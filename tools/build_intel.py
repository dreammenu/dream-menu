#!/usr/bin/env python3
"""Builds the analysis data behind /analysis (public) and /partner/intelligence (partner only).

Run from the repository root:  python3 tools/build_intel.py

Reads the site's own data files (partner-data.js, dm-data.js, dm-cat.js, dm-labels.js) and
writes two files:
  analysis-data.js            public: city appetite index, guests vs critics, concentration
  partner/intel-data.js       partner only (behind sign-in): confidence intervals, momentum,
                              trend wall, dish heat, segments, opportunity scores, operators

Every figure is derived from those inputs, so re-running after a data refresh updates the pages.
Headlines public, depth locked: nothing about quarterly movement goes into the public file.
"""
import json, math, os, re, statistics
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    obj, _ = json.JSONDecoder().raw_decode(s[m.end():].lstrip())
    return obj


P = load('partner-data.js', 'DM_PARTNER')
D = load('dm-data.js', 'DM')
C = load('dm-cat.js', 'DMC')
L = load('dm-labels.js', 'DML')

COURSE = {k: P['trends'][k]['label'] for k in P['order']}
EARLY, LATE = P['method']['early'], P['method']['late']
Z = 1.959964


def label(c):
    return (L.get(c) or [c])[0]


def parent(c):
    return (L.get(c) or [c, ''])[1]


def r1(x):
    return None if x is None else round(x, 1)


# ---------------------------------------------------------------- partner analyses
def pool_n(t, quarters):
    return sum(n for q, n in zip(t['q'], t['n_q']) if q in quarters and n)


def ci_rows():
    """Difference in share, late minus early, with a 95% interval on the pooled standard error."""
    rows = []
    for k in P['order']:
        t = P['trends'][k]
        n1, n2 = pool_n(t, EARLY), pool_n(t, LATE)
        for level, items in (('Group', t['groups']), ('Dish', t['cats'])):
            for it in items:
                p1, p2 = it['early'] / 100, it['late'] / 100
                if not n1 or not n2:
                    continue
                pp = (p1 * n1 + p2 * n2) / (n1 + n2)  # pooled, so the interval agrees with the z-test flag
                se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
                # back out the standard error from the published p so the interval always agrees with
                # the significance flag (shares are rounded to 0.1, which can tip borderline cases)
                if 0.0005 < it['p'] < 0.9995 and abs(it['move']) >= 0.1:
                    zp = statistics.NormalDist().inv_cdf(1 - it['p'] / 2)
                    se = abs(it['move']) / 100 / zp
                rows.append(dict(course=k, cl=t['label'], level=level, c=it['c'],
                                 l=it.get('l') or it['c'], g=it.get('g', ''), n=it['n'], pct=it['pct'],
                                 early=it['early'], late=it['late'], move=it['move'],
                                 lo=round(it['move'] - Z * se * 100, 2), hi=round(it['move'] + Z * se * 100, 2),
                                 p=it['p'], sig=it['sig'], n1=n1, n2=n2, share=it['share']))
    return rows


ROWS = ci_rows()


def quadrant(r, med):
    hi = r['pct'] >= med
    up = r['move'] > 0
    return ('core-up' if up else 'core-down') if hi else ('emerging' if up else 'fading')


def momentum():
    out = []
    for k in P['order']:
        cats = [r for r in ROWS if r['course'] == k and r['level'] == 'Dish']
        med = statistics.median([r['pct'] for r in cats])
        for r in cats:
            out.append(dict(course=k, cl=r['cl'], l=r['l'], g=r['g'], n=r['n'], pct=r['pct'],
                            move=r['move'], p=r['p'], sig=r['sig'], quad=quadrant(r, med), med=med))
    return out


def heat():
    """Dish-level share by quarter, indexed to the dish's own average share (100 = average)."""
    out = []
    for k in P['order']:
        t = P['trends'][k]
        rows = []
        for it in t['cats'][:10]:
            vals = [v for v, nq in zip(it['share'], t['n_q']) if v is not None and nq]
            w = [nq for v, nq in zip(it['share'], t['n_q']) if v is not None and nq]
            avg = sum(v * n for v, n in zip(vals, w)) / sum(w) if w else 0
            idx = [None if (v is None or not nq) else (round(v / avg * 100) if avg else None)
                   for v, nq in zip(it['share'], t['n_q'])]
            rows.append(dict(l=it.get('l') or it['c'], share=it['share'], idx=idx, avg=r1(avg), sig=it['sig'], move=it['move']))
        out.append(dict(course=k, cl=t['label'], q=t['q'], n_q=t['n_q'], low=[n < P['min_n'] for n in t['n_q']], rows=rows))
    return out


def wall():
    out = []
    for k in P['order']:
        t = P['trends'][k]
        out.append(dict(course=k, cl=t['label'], q=t['q'], n_q=t['n_q'], n=t['n'],
                        low=[n < P['min_n'] for n in t['n_q']],
                        items=[dict(l=g['c'], share=g['share'], early=g['early'], late=g['late'], move=g['move'],
                                    p=g['p'], sig=g['sig'], pct=g['pct'], n=g['n']) for g in t['groups'][:6]],
                        note=t.get('note', '')))
    return out


def segments():
    segs = P['groups']
    tot = sum(s['n'] for s in segs)
    names = []
    for s in segs:
        for g, _ in s['top_groups']:
            if g not in names:
                names.append(g)
    rows = []
    for g in names:
        vals = {s['g']: dict(s['top_groups']).get(g) for s in segs}
        known = [(vals[s['g']], s['n']) for s in segs if vals[s['g']] is not None]
        floor = {s['g']: min(v for _, v in s['top_groups']) for s in segs}
        rows.append(dict(g=g, v=vals, floor=floor, complete=len(known) == len(segs)))
    # dish-level: the top six dishes per segment
    dnames = []
    for s in segs:
        for d, _ in s['top']:
            if d not in dnames:
                dnames.append(d)
    drows = [dict(g=d, v={s['g']: dict(s['top']).get(d) for s in segs},
                  floor={s['g']: min(v for _, v in s['top']) for s in segs}) for d in dnames]
    return dict(segs=[dict(g=s['g'], n=s['n'], share=round(s['n'] / tot * 100, 1)) for s in segs], groups=rows, dishes=drows)


FATIGUE = {  # dish category -> the "Bin it" answer it overlaps with
    'Loaded / dirty fries': 'Loaded and dirty food',
    'Truffle fries': 'Loaded and dirty food',
}
BIN = dict(P['extra']['bin'])


def venue_spread():
    """For each dish category: how many venues guests tie it to, and the top venue's share."""
    names = C['c']
    per = defaultdict(list)
    for vi, pairs in C['v'].items():
        for ci, cnt in pairs:
            per[names[ci]].append((cnt, int(vi)))
    out = {}
    for c, lst in per.items():
        lst.sort(reverse=True)
        tot = sum(x for x, _ in lst)
        out[c] = dict(venues=len(lst), mentions=tot, top=round(lst[0][0] / tot * 100) if tot else 0,
                      topv=D['venues'][lst[0][1]]['n'] if lst else '')
    return out


SPREAD = venue_spread()


def pct_rank(vals, x):
    s = sorted(vals)
    below = sum(1 for v in s if v < x)
    eq = sum(1 for v in s if v == x)
    return (below + 0.5 * eq) / len(s) * 100


def opportunity():
    """Composite score per dish (all six courses).
    Demand 30%: share within its course (percentile across all dishes).
    Momentum 35%: late minus early share (percentile).
    Evidence 15%: 1 - p, so a clearer test result counts for more.
    Room to enter 20%: how concentrated guest mentions are on one venue (a dish guests tie to
    one place is easier to win with a second good version).
    Fatigue penalty: 10 points if guests also name it in 'Bin it'."""
    dish = [r for r in ROWS if r['level'] == 'Dish' and r['course'] not in ('k',)]
    pcts = [r['pct'] for r in dish]
    moves = [r['move'] for r in dish]
    out = []
    for r in dish:
        sp = SPREAD.get(r['c'], dict(venues=0, mentions=0, top=0, topv=''))
        demand = pct_rank(pcts, r['pct'])
        mom = pct_rank(moves, r['move'])
        evid = (1 - r['p']) * 100
        room = min(100, sp['top'] * 2) if sp['mentions'] >= 5 else 30
        fat = 10 if r['c'] in FATIGUE else 0
        score = 0.30 * demand + 0.35 * mom + 0.15 * evid + 0.20 * room - fat
        if r['sig'] and r['move'] > 0:
            tier = 'Back'
        elif r['sig'] and r['move'] < 0:
            tier = 'Review'
        elif score >= 60:
            tier = 'Back'
        elif score >= 45:
            tier = 'Watch'
        else:
            tier = 'Review' if r['move'] < 0 else 'Watch'
        out.append(dict(l=r['l'], cl=r['cl'], course=r['course'], pct=r['pct'], move=r['move'], p=r['p'], sig=r['sig'],
                        venues=sp['venues'], top=sp['top'], topv=sp['topv'],
                        parts=dict(demand=round(0.30 * demand, 1), momentum=round(0.35 * mom, 1),
                                   evidence=round(0.15 * evid, 1), room=round(0.20 * room, 1)),
                        fatigue=FATIGUE.get(r['c'], ''), fat=fat, score=round(score), tier=tier))
    out.sort(key=lambda x: -x['score'])
    return out


def merge_counts(pairs):
    """The survey export split one option at its comma: 'Staffing model changes (cross-training' + 'rota changes)'."""
    out, skip = [], False
    for i, (k, v) in enumerate(pairs):
        if skip:
            skip = False
            continue
        if k.count('(') > k.count(')') and i + 1 < len(pairs) and pairs[i + 1][0].endswith(')'):
            out.append([k + ', ' + pairs[i + 1][0], v])
            skip = True
        else:
            out.append([k, v])
    return out


def operators():
    lk = P['look']
    n = lk['n']
    pct = lambda v, base=n: round(v / base * 100)
    actions = merge_counts(lk['actions'])
    links = [  # pressure -> the action that answers it most directly
        ('Food input costs', 'Supplier changes / renegotiation'),
        ('Energy/utilities', 'Investment in equipment/efficiency'),
        ('Labour costs', 'Staffing model changes (cross‑training, rota changes)'),
        ('Consumer demand / footfall', 'Marketing / partnerships / events'),
        ('Rent/rates/property costs', 'Reduced opening hours'),
        ('Drink input costs', 'Menu engineering / reduced SKUs'),
    ]
    P_ = dict(lk['pressures'])
    A_ = dict(actions)
    gap = [dict(pressure=p, pv=pct(P_.get(p, 0)), action=a, av=pct(A_.get(a, 0)), gap=pct(P_.get(p, 0)) - pct(A_.get(a, 0))) for p, a in links]
    sup_base = sum(v for k, v in lk['supplier'] if k != 'Unsure')
    rising = sum(v for k, v in lk['supplier'] if k.startswith('Rising'))
    order_call = ['Deteriorating ⬇️', 'Mixed', 'Stable', 'Improving ⬆️']
    call = dict(lk['call'])
    calln = sum(call.values())
    vs = dict(lk['vs_last_year'])
    vsn = sum(v for k, v in vs.items() if k != 'Unsure')
    return dict(n=n, trading=lk['trading'], predictable=lk['predictable'], conf3=lk['conf3'], conf12=lk['conf12'],
                rising=pct(rising, lk and sum(v for _, v in lk['supplier'])), sup_base=sup_base,
                pressures=[[k, pct(v)] for k, v in lk['pressures'][:8]],
                actions=[[k, pct(v)] for k, v in actions[:8]],
                support=[[k, pct(v)] for k, v in lk['support'][:6]],
                signals=[[k, pct(v)] for k, v in lk['signals'] if v > 1][:6],
                gap=gap,
                call=[[k.replace(' ⬇️', '').replace(' ⬆️', ''), call.get(k, 0), round(call.get(k, 0) / calln * 100)] for k in order_call],
                vs=[[k, vs.get(k, 0), round(vs.get(k, 0) / vsn * 100)] for k in ['Worse', 'About the same', 'Better', 'Much better']],
                staffing=lk['staffing'], size=lk['size'])


def headline_kpis():
    sig = [r for r in ROWS if r['sig']]
    up = [r for r in sig if r['move'] > 0]
    dn = [r for r in sig if r['move'] < 0]
    iq = P['extra']['interviews_q']
    return dict(n=P['n'], n_all=P['n_all'], last=P['last'], built=P['built'], interviews_q=iq,
                quarters=P['trends']['s']['q'], sig=len(sig), up=len(up), down=len(dn),
                tests=len(ROWS),
                biggest_up=max(up, key=lambda r: r['move']) if up else None,
                biggest_down=min(dn, key=lambda r: r['move']) if dn else None)


# ---------------------------------------------------------------- public analyses
def market_of(v):
    if v['c'] == 'Glasgow':
        return 'Glasgow'
    if v['c'] == 'Edinburgh':
        return 'Edinburgh'
    if v['na'] == 'Scotland':
        return 'Rest of Scotland'
    if v['co'] == 'United Kingdom':
        return 'Rest of UK'
    return 'Outside the UK'


MARKETS = ['Glasgow', 'Edinburgh', 'Rest of Scotland', 'Rest of UK', 'Outside the UK']


def city_index():
    names = C['c']
    tot = Counter()
    by = defaultdict(Counter)
    for vi, pairs in C['v'].items():
        v = D['venues'][int(vi)]
        mk = market_of(v)
        for ci, cnt in pairs:
            tot[names[ci]] += cnt
            by[mk][names[ci]] += cnt
    T = sum(tot.values())
    mt = {m: sum(by[m].values()) for m in MARKETS}
    top = [c for c, _ in tot.most_common(18)]
    rows = []
    sig = signature(by, tot, mt, T)
    for s_ in sig:  # make sure each market's signature dish is on the grid
        if s_['raw'] and s_['raw'] not in top:
            top.append(s_['raw'])
    for c in top:
        base = tot[c] / T
        cells = []
        for m in MARKETS:
            k = by[m][c]
            share = k / mt[m] if mt[m] else 0
            cells.append(dict(n=k, share=round(share * 100, 1), idx=round(share / base * 100) if base else None,
                              thin=k < 5))
        rows.append(dict(c=c, l=label(c), g=parent(c), n=tot[c], share=round(base * 100, 1), cells=cells))
    return dict(markets=MARKETS, totals=[mt[m] for m in MARKETS], total=T, rows=rows,
                signature=[{k: v for k, v in s_.items() if k != 'raw'} for s_ in sig])


def signature(by, tot, mt, T):
    """Signature dish per market: the highest index among dishes with 8+ mentions there."""
    sig = []
    for m in MARKETS:
        best = None
        for c, k in by[m].items():
            if k < 8 or tot[c] < 15:
                continue
            idx = (k / mt[m]) / (tot[c] / T) * 100
            if best is None or (round(idx), k) > (round(best[1]), best[2]):
                best = (c, idx, k)
        sig.append(dict(m=m, c=label(best[0]) if best else '', raw=best[0] if best else '', pin=round(best[2] / tot[best[0]] * 100) if best else 0, base=round(mt[m] / T * 100), idx=round(best[1]) if best else None, n=best[2] if best else 0, total=mt[m]))
    return sig


TIER = [  # order matters: the highest recognition a venue holds
    ('Three MICHELIN Stars', 'Three stars'), ('Two MICHELIN Stars', 'Two stars'), ('One MICHELIN Star', 'One star'),
    ("World's 50 Best", "World's 50 Best"), ('50 Best', '50 Best (regional)'), ('Bib Gourmand', 'Bib Gourmand'),
    ('Green Star', 'Green Star'), ('Rosette', 'AA Rosettes'), ('MICHELIN Guide', 'MICHELIN selected'), ('', 'Other guides')]


def tier_of(awards):
    for key, name in TIER:
        if any(key in a for a in awards):
            return name
    return 'Other guides'


def critics():
    vs = sorted([v for v in D['venues'] if v['m'] > 0], key=lambda v: -v['m'])
    aw = D['aw']
    tops = {}
    for k in (10, 25, 50, 100, len(vs)):
        sub = vs[:k]
        tops[k] = dict(n=len(sub), award=sum(1 for v in sub if v['i'] in aw))
    pts = []
    for rank, v in enumerate(vs[:150], 1):
        a = aw.get(v['i'])
        pts.append(dict(n=v['n'], c=v['c'], m=v['m'], g=v['g'], rank=rank, tier=tier_of(a['a']) if a else 'No guide award',
                        aw=(a['a'][:2] if a else [])))
    champions = [dict(n=v['n'], c=v['c'], m=v['m'], g=v['g']) for v in vs if v['i'] not in aw][:10]
    starred = [dict(n=v['n'], c=v['c'], m=v['m'], tier=tier_of(aw[v['i']]['a']), aw=aw[v['i']]['a'][0]) for v in vs if v['i'] in aw][:10]
    # Pareto: cumulative share of mentions held by the top x% of venues
    tot = sum(v['m'] for v in vs)
    cum, curve = 0, []
    marks = {}
    for i, v in enumerate(vs, 1):
        cum += v['m']
        x = i / len(vs) * 100
        if i % max(1, len(vs) // 100) == 0 or i == len(vs):
            curve.append([round(x, 1), round(cum / tot * 100, 1)])
        for p in (1, 5, 10, 20, 50):
            if p not in marks and x >= p:
                marks[p] = round(cum / tot * 100, 1)
    once = sum(1 for v in vs if v['m'] == 1)
    tier_counts = Counter(tier_of(aw[v['i']]['a']) for v in vs if v['i'] in aw)
    return dict(venues=len(vs), mentions=tot, tops=tops, points=pts, champions=champions, starred=starred,
                curve=curve, marks=marks, once=once, once_pct=round(once / len(vs) * 100),
                linked=sum(1 for v in vs if v['i'] in aw), tiers=tier_counts.most_common())


def concentration():
    out = []
    for k in ('s', 'm', 'd', 'p'):  # food courses; the drink questions have only three or four groups
        t = P['trends'][k]
        gs = sorted(t['groups'], key=lambda g: -g['pct'])
        top3 = sum(g['pct'] for g in gs[:3])
        cats = sorted(t['cats'], key=lambda c: -c['pct'])
        out.append(dict(course=k, cl=t['label'], n=t['n'], top1=gs[0]['c'], top1v=gs[0]['pct'],
                        top3=round(top3, 1), dish=cats[0].get('l') or cats[0]['c'], dishv=cats[0]['pct'],
                        groups=[[g['c'], g['pct']] for g in gs[:3]]))
    return out


FRESH = dict(interviews_to=P['last'], built=P['built'], venues_built=D['meta']['built'],
             interviews=P['n_all'], dish_n=P['n'], venues=D['meta']['venues'])

public = dict(fresh=FRESH, cities=city_index(), critics=critics(), conc=concentration())
partner = dict(fresh=FRESH, kpi=headline_kpis(), ci=[r for r in ROWS], momentum=momentum(), heat=heat(),
               wall=wall(), seg=segments(), opp=opportunity(), ops=operators(),
               method=dict(early=EARLY, late=LATE, test=P['method']['test'], min_n=P['min_n']))

hdr = '/* Generated by tools/build_intel.py from the site data files. Do not edit by hand. */\n'
with open('analysis-data.js', 'w', encoding='utf-8') as f:
    f.write(hdr + 'window.DM_ANALYSIS=' + json.dumps(public, ensure_ascii=False, separators=(',', ':')) + ';\n')
with open('partner/intel-data.js', 'w', encoding='utf-8') as f:
    f.write(hdr + 'window.DM_INTEL=' + json.dumps(partner, ensure_ascii=False, separators=(',', ':')) + ';\n')

k = partner['kpi']
print('tests', k['tests'], 'significant', k['sig'], '(up', k['up'], 'down', k['down'], ')')
print('critics', public['critics']['tops'], 'marks', public['critics']['marks'])
print('signature', public['cities']['signature'])
print('opp top', [(o['l'], o['cl'], o['score'], o['tier']) for o in partner['opp'][:8]])
print('sizes', os.path.getsize('analysis-data.js'), os.path.getsize('partner/intel-data.js'))
