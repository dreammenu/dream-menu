#!/usr/bin/env python3
"""Builds partner/briefing-extra.js (behind the partner sign-in) for three briefing sections:

  1. What changed since the last briefing: clear movers gained, lost and still clear, against the newest
     snapshot in tools/data/briefing-snapshots/ dated before this data. A snapshot of today's movers is saved
     there too, so the next quarter compares against this one.
  2. Trend scorecard: every scored dish and drink with a score out of 10 (the opportunity score from
     tools/build_intel.py divided by 10), its verdict and a plain signal (rising, clear / rising / steady / easing / falling, clear).
  3. By Dunns range: the parent groups rolled up into indicative supplier ranges, course by course.
     The range list is Dream Menu's grouping; align it with Dunns' own category list when Dunns shares it.

Run after build_intel.py:  python3 tools/build_briefing_extras.py
"""
import datetime as dt, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
I = load('partner/intel-data.js', 'DM_INTEL')
SNAPS = 'tools/data/briefing-snapshots'

# ---------------------------------------------------------------- 1. changes since the last snapshot
key = lambda m: (m['course'], m['level'], m['l'])
now = {key(m): m for m in P['movers']}
older = sorted(f for f in glob.glob(f'{SNAPS}/*.json') if os.path.basename(f)[:-5] < P['last'])
changes = None
if older:
    base = json.load(open(older[-1], encoding='utf-8'))
    was = {key(m): m for m in base['movers']}
    row = lambda m, b=None: dict(course=m['course'], level=m['level'], l=m['l'], move=m['move'], was=(b or {}).get('move'))
    changes = dict(
        since=base['last'], n_then=base['n'], n_now=P['n'],
        new=[row(m) for k, m in now.items() if k not in was],
        gone=[dict(course=m['course'], level=m['level'], l=m['l'], was=m['move']) for k, m in was.items() if k not in now],
        kept=[row(m, was[k]) for k, m in now.items() if k in was])
    for lst in changes.values():
        if isinstance(lst, list):
            lst.sort(key=lambda r: -abs(r.get('move') if r.get('move') is not None else r.get('was') or 0))
json.dump(dict(last=P['last'], built=P['built'], n=P['n'], source='tools/build_briefing_extras.py',
               movers=[dict(course=m['course'], level=m['level'], l=m['l'], move=m['move'], p=m['p']) for m in P['movers']]),
          open(f'{SNAPS}/{P["last"]}.json', 'w', encoding='utf-8'), indent=1)

# ---------------------------------------------------------------- 2. trend scorecard
def signal(o):
    if o['sig']:
        return 'Rising, clear' if o['move'] > 0 else 'Falling, clear'
    return 'Rising' if o['move'] >= 1 else 'Easing' if o['move'] <= -1 else 'Steady'


score = [dict(l=o['l'], cl=o['cl'], s10=round(o['score'] / 10, 1), tier=o['tier'], sig=signal(o), pct=o['pct'], move=o['move'],
              where=o.get('topv') or '', bin=bool(o.get('fatigue'))) for o in I['opp']]

# ---------------------------------------------------------------- 3. by Dunns range
RANGES = [
    ('Fish and seafood', ['Seafood']),
    ('Meat and poultry', ['Steak and beef', 'Chicken', 'Pork', 'Game and duck', 'Lamb']),
    ('Potatoes, vegetables and salad', ['Potatoes and fries', 'Vegetables and salad']),
    ('World foods, pasta and rice', ['Pasta and Italian', 'Asian', 'Indian', 'Mexican and Latin', 'Mediterranean and Middle Eastern']),
    ('Bakery, desserts and puddings', ['Bread', 'Tiramisu and creamy desserts', 'Cakes and bakes', 'Puddings', 'Chocolate desserts',
                                       'Cheesecake', 'Tarts and pies', 'Fruit and meringue']),
    ('Dairy, cheese and frozen', ['Ice cream and frozen', 'Cheese']),
    ('Soft drinks and low/no', ['Soft drinks', 'No and low alcohol']),
    ('Coffee and tea', ['Coffee and tea']),
    ('Beer, wine and spirits', ['Cocktails', 'Wine and fizz', 'Beer and cider', 'Spirits']),
    ('Pub classics, burgers and sharing', ['Burgers and fried food', 'Scottish and British classics', 'Sharing and tasting']),
]
mapped = {g for _, gs in RANGES for g in gs}
ranges = []
for name, groups in RANGES:
    cells = []
    for k in P['order']:
        T = P['trends'][k]
        gs = [g for g in T['groups'] if g['c'] in groups]
        if not gs:
            continue
        cells.append(dict(course=T['label'], late=round(sum(g['late'] for g in gs), 1), move=round(sum(g['move'] for g in gs), 1),
                          clear=[f"{g['c']} {'+' if g['move'] > 0 else ''}{g['move']:.1f}" for g in gs if g['sig']],
                          groups=[g['c'] for g in gs]))
    ranges.append(dict(r=name, cells=cells))
other = sorted({g['c'] for k in P['order'] for g in P['trends'][k]['groups'] if g['c'] not in mapped})

out = dict(built=dt.date.today().isoformat(), last=P['last'], changes=changes, score=score, ranges=ranges, other=other,
           early=I['method']['early'], late=I['method']['late'])
open('partner/briefing-extra.js', 'w', encoding='utf-8').write(
    '/* Generated by tools/build_briefing_extras.py. Partner-only (served from /partner/, behind sign-in). */\n'
    'window.DM_BRIEF_X=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('changes since', changes and changes['since'], '| new', changes and len(changes['new']), '| gone', changes and len(changes['gone']),
      '| scored', len(score), '| unmapped groups', other)
