#!/usr/bin/env python3
"""Brings the figures written into the static pages in line with the data files.

Run from the repository root after any data update (after add_interviews.py / add_venues.py):
  python3 tools/refresh_static.py && python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py

Reads partner-data.js, dm-data.js, dm-cat.js, dm-labels.js and tools/data/static-counts.json and
rewrites, in place:
  index.html      hero and stats counts, the voted dream menu, course cards, the four market tabs
                  (dishes and most-named venues), the debates, guilty pleasures and bin it, map card,
                  source line
  insights.html   lede, debates, interviews by quarter, quote attributions
  every page      the "Data to ..." date in the footer
  dm-fresh.js     the data status table (interviews, venues, analysis)
  for-business, how-it-works, onepager, briefing, partner, operators, map: counts and dates
The 2026 report pages keep their own edition figures (data to 9 October 2026) on purpose.
"""
import datetime as dt, glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TODAY = dt.date.today().isoformat()


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
D = load('dm-data.js', 'DM')
C = load('dm-cat.js', 'DMC')
L = load('dm-labels.js', 'DML')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
M = D['meta']
V = {v['i']: v for v in D['venues']}
MK = {m['id']: m for m in D['markets']}
LAST = dt.date.fromisoformat(P['last'])
LAST_H = LAST.strftime('%-d %B %Y')          # 27 October 2026
LAST_S = LAST.strftime('%-d %b')              # 27 Oct
N_ALL = f"{P['n_all']:,}"
lab = lambda c: (L.get(c) or [c])[0]
fmt = lambda n: f'{n:,}'
pc0 = lambda x: f'{round(x):d}%'
w1 = lambda a, b: f'{100 * a / b:.1f}%' if b else '0%'
changed = []


def edit(fn, pairs, required=True):
    s = open(fn, encoding='utf-8').read()
    o = s
    for pat, rep in pairs:
        s2 = re.sub(pat, rep, s, flags=re.S)
        if s2 == s and required and not re.search(pat, s, flags=re.S):
            raise SystemExit(f'{fn}: pattern not found: {pat[:80]}')
        s = s2
    if s != o:
        open(fn, 'w', encoding='utf-8').write(s)
        changed.append(fn)


# ---------------------------------------------------------------- shared pieces
def debates_home():
    out = []
    spec = [('coke', 'Irn-Bru or Coca-Cola?', ['Irn Bru', 'Coca Cola', 'Neither']),
            ('tea', 'Coffee or tea?', ['Coffee', 'Tea', 'Neither']),
            ('pineapple', 'Pineapple on pizza?', ['Yes', 'No']),
            ('water', 'Still, sparkling or tap?', ['Still', 'Tap', 'Sparkling', 'Scottish tap water'])]
    for key, title, opts in spec:
        d = SC['debates'][key]
        n = d['n']
        sh = [(o, 100 * d['c'][o] / n) for o in opts]
        win = max(sh, key=lambda x: x[1])
        label = ', '.join(f'{o} {pc0(p)}' for o, p in sh)
        bars = ''.join(f'<i class="s{i}" style="width:{p:.1f}%" title="{o} {pc0(p)}"></i>' for i, (o, p) in enumerate(sh))
        keys = ''.join(f'<li><i class="s{i}"></i>{o} <b>{pc0(p)}</b></li>' for i, (o, p) in enumerate(sh))
        out.append(f'<article class="deb"><h3>{title}</h3><p class="win">{win[0]} <b>{pc0(win[1])}</b></p>'
                   f'<div class="stack" role="img" aria-label="{label}">{bars}</div><ul class="sk">{keys}</ul>'
                   f'<p class="n">{fmt(n)} answers</p></article>')
    return '<div class="dgrid">' + ''.join(out) + '</div>'


def debates_insights():
    out = []
    spec = [('coke', 'Irn Bru or Coke?', ['Irn Bru', 'Coca Cola', 'Neither']),
            ('tea', 'Tea or coffee?', ['Coffee', 'Tea', 'Neither']),
            ('pineapple', 'Pineapple on pizza?', ['Yes', 'No']),
            ('water', 'Still, tap or sparkling?', ['Still', 'Tap', 'Sparkling', 'Scottish tap water'])]
    for key, title, opts in spec:
        d = SC['debates'][key]
        n = d['n']
        sh = [(o, 100 * d['c'][o] / n) for o in opts]
        label = ', '.join(f'{o} {p:.1f}%' for o, p in sh)
        bars = ''.join(f'<i class="s{i + 1}" style="width:{p:.2f}%" title="{o}: {p:.1f}%"></i>' for i, (o, p) in enumerate(sh))
        keys = ''.join(f'<span><b class="s{i + 1}"></b>{o} <em>{p:.1f}%</em></span>' for i, (o, p) in enumerate(sh))
        out.append(f'    <div class="card"><h3>{title}</h3><div class="split" role="img" aria-label="{label}">{bars}</div>'
                   f'<div class="splitkey">{keys}</div><p class="note">{fmt(n)} answers</p></div>')
    return '<div class="grid">\n' + '\n'.join(out) + '\n  </div>'


def hb(items):
    """items: [(label, count, pct)] -> the home page horizontal bars"""
    top = items[0][1] if items else 1
    return '<ol class="hb">' + ''.join(
        f'<li><span class="hb-l">{html.escape(l)}</span><span class="hb-t"><i style="width:{100 * c / top:.1f}%"></i></span>'
        f'<span class="hb-v">{pc0(p)}</span></li>' for l, c, p in items) + '</ol>'


def course_card(k, eyebrow):
    t = P['trends'][k]
    base = SC['course_card_answers'][k]
    items = [(it.get('l') or lab(it['c']), it['n'], 100 * it['n'] / base) for it in t['cats'][:5]]
    return (f'<article class="ccard"><header><span class="eyebrow">{eyebrow}</span><span class="n">{fmt(base)} answers</span></header>'
            + hb(items) + '</article>')


def drink_card():
    dc = SC['drink_card']
    items = [(l, c, 100 * c / dc['n']) for l, c in dc['c'][:5]]
    return (f'<article class="ccard"><header><span class="eyebrow">Drink</span><span class="n">{fmt(dc["n"])} answers</span></header>'
            + hb(items) + '</article>')


def market_pane(i, mid, title, more_href, more_text, hidden):
    m = MK[mid]
    cats = [(lab(C['c'][ci]), n, sh) for ci, n, sh in C['m'][mid][:8]]
    vl = ''.join(
        f'<li><a href="/map#venue-{v["i"]}"><span class="r">{r}</span><span class="vn">{html.escape(v["n"])}'
        f'<small>{html.escape(v["tw"] or v["c"])}</small></span><span class="vm">{v["m"]}</span></a></li>'
        for r, v in enumerate((V[x] for x in m['top'][:6]), 1))
    return (f'<div class="mpane" role="tabpanel" id="p{i}" aria-labelledby="t{i}"{" hidden" if hidden else ""}>\n'
            f'  <div class="mcol"><h3>What guests name in {title}</h3><p class="sub">Share of dishes named, all courses · '
            f'{fmt(m["mn"])} mentions from {fmt(m["g"])} guests</p>\n  {hb(cats)}</div>\n'
            f'  <div class="mcol"><h3>Most-named venues</h3><p class="sub">Times named by guests</p><ol class="vlist">{vl}</ol>\n'
            f'  <a class="more" href="{more_href}">{more_text}</a></div>\n</div>')


def rank_list(lst):
    return '<ol class="rk">' + ''.join(f'<li><span class="r">{i}</span><span class="t">{html.escape(t)}</span><span class="v">{n}</span></li>'
                                     for i, (t, n) in enumerate(lst[:6], 1)) + '</ol>'


# ---------------------------------------------------------------- index.html
menu = []
for k, c in (('s', 'Starter'), ('m', 'Main'), ('d', 'Side'), ('p', 'Dessert')):
    it = P['trends'][k]['cats'][0]
    menu.append((c, it.get('l') or lab(it['c']), 100 * it['n'] / SC['course_card_answers'][k]))
dl, dn = SC['drink_card']['c'][0]
menu.append(('Drink', dl, 100 * dn / SC['drink_card']['n']))
menu_html = '<ol>' + ''.join(f'<li><span class="c">{c}</span><span class="d">{html.escape(d)}</span><span class="dots"></span><span class="p">{pc0(p)}</span></li>' for c, d, p in menu) + '</ol>'
panes = '\n'.join([
    market_pane(0, 'city:Glasgow|United Kingdom', 'Glasgow', '/map#city-glasgow-united-kingdom', 'See Glasgow on the map →', False),
    market_pane(1, 'city:Edinburgh|United Kingdom', 'Edinburgh', '/map#city-edinburgh-united-kingdom', 'See Edinburgh on the map →', True),
    market_pane(2, 'nation:Scotland', 'Scotland', '/map#nation-scotland', 'See Scotland on the map →', True),
    market_pane(3, 'world:World', 'every market', '/map#world', 'See the world on the map →', True)])
edit('index.html', [
    (r'(food trends and insights from )[\d,]+( Dream Menu interviews)', rf'\g<1>{N_ALL}\g<2>'),
    (r'from places you actually go\. [\d,]+ interviews later', f'from places you actually go. {N_ALL} interviews later'),
    (r'(<div class="ms">as voted by )[\d,]+( guests</div>)', rf'\g<1>{N_ALL}\g<2>'),
    (r'(<div class="ms">as voted by [\d,]+ guests</div>\s*)<ol>.*?</ol>', lambda m: m.group(1) + menu_html),
    (r'<section class="h-stats" aria-label="In numbers"><div class="wrap">.*?</div></section>',
     '<section class="h-stats" aria-label="In numbers"><div class="wrap">\n'
     f'  <div><b>{N_ALL}</b><span>interviews</span></div>\n  <div><b>{fmt(M["mentions"])}</b><span>venue mentions</span></div>\n'
     f'  <div><b>{fmt(M["venues"])}</b><span>venues named</span></div>\n  <div><b>{M["cities"]}</b><span>cities</span></div>\n'
     f'  <div><b>{M["countries"]}</b><span>countries</span></div>\n</div></section>'),
    (r'<div class="cgrid">.*?</article></div>\n',
     lambda m: '<div class="cgrid">' + course_card('s', 'Starter') + course_card('m', 'Main') + course_card('d', 'Side')
     + course_card('p', 'Dessert') + drink_card() + '</div>\n'),
    (r'<div class="mpane" role="tabpanel" id="p0".*?See the world on the map →</a></div>\n</div>', lambda m: panes),
    (r'<div class="dgrid">.*?</article></div>', lambda m: debates_home()),
    (r'(<h3>Guilty pleasures</h3><p class="sub">[^<]*</p>)<ol class="rk">.*?</ol>', lambda m: m.group(1) + rank_list(P['extra']['guilty'])),
    (r'(<h3>Bin it</h3><p class="sub">[^<]*</p>)<ol class="rk">.*?</ol>', lambda m: m.group(1) + rank_list(P['extra']['bin'])),
    (r'<h2>[\d,]+ venues, <em>pinned</em></h2>', f'<h2>{fmt(M["pinned"])} venues, <em>pinned</em></h2>'),
    (r'Source: [\d,]+ Dream Menu interviews, 1 September 2025 to [^.]+\.', f'Source: {N_ALL} Dream Menu interviews, 1 September 2025 to {LAST_H}.'),
])

# ---------------------------------------------------------------- insights.html
iq = P['extra']['interviews_q']
qmax = max(iq)
qbars = ''.join(f'<div><span class="qv">{n}</span><i style="height:{round(100 * n / qmax)}%"></i><span class="ql">{q.replace("-", " ")}</span></div>'
                for q, n in zip(P['trends']['s']['q'], iq))
edit('insights.html', [
    (r'Every number here comes from [\d,]+ Dream Menu interviews, September 2025 to [^.]+\. Dish shares use the [\d,]+ interviews',
     f'Every number here comes from {N_ALL} Dream Menu interviews, September 2025 to {LAST_H}. Dish shares use the {fmt(P["n"])} interviews'),
    (r'(<h2 id="debates">The big debates</h2>\s*)<div class="grid">.*?(\n</div></section>)',
     lambda m: m.group(1) + debates_insights() + m.group(2)),
    (r'(<div class="qchart" role="img" aria-label="Interviews by quarter">).*?(</div>\s*<p class="note">)', lambda m: m.group(1) + qbars + m.group(2)),
    (r'<blockquote class="quote">([^<]*?)\., ([^<]+)</blockquote>', r'<blockquote class="quote">\1.<small>\2</small></blockquote>'),
], required=False)

# ---------------------------------------------------------------- other pages
edit('for-business.html', [
    (r'and where would you eat it\? [\d,]+ interviews later', f'and where would you eat it? {N_ALL} interviews later'),
    (r'<div class="facts"><div><b>[\d,]+</b> <span>interviews</span></div><div><b>[\d,]+</b> <span>venues named</span></div><div><b>[\d,]+</b> <span>venue mentions</span></div><div><b>\d+</b> <span>countries</span></div></div>',
     f'<div class="facts"><div><b>{N_ALL}</b> <span>interviews</span></div><div><b>{fmt(M["venues"])}</b> <span>venues named</span></div><div><b>{fmt(M["mentions"])}</b> <span>venue mentions</span></div><div><b>{M["countries"]}</b> <span>countries</span></div></div>'),
])
edit('how-it-works.html', [
    (r'[\d,]+ interviews are included, up to [^.]+\. Venues on the map come from (?:the same [\d,]+ interviews\.|the [\d,]+ interviews up to [^;]+; newer answers join the map at the next update\.) The dish figures on the Insights page use the [\d,]+ interviews',
     f'{N_ALL} interviews are included, up to {LAST_H}. Venues on the map come from the same {fmt(M["interviews_mapped"])} interviews. The dish figures on the Insights page use the {fmt(P["n"])} interviews'),
    (r'Of [\d,]+ venues named, [\d,]+ have a confirmed address and [\d,]+ an approximate one\.',
     f'Of {fmt(M["venues"])} venues named, {fmt(M["located"])} have a confirmed address and {fmt(M["approximate"])} an approximate one.'),
])
edit('onepager.html', [
    (r'(Dream Menu · partner summary · )[^<]+', rf'\g<1>{LAST_H}'),
    (r'<div class="facts"><div><b>[\d,]+</b> <span>interviews</span></div><div><b>[\d,]+</b> <span>venues named</span></div>',
     f'<div class="facts"><div><b>{N_ALL}</b> <span>interviews</span></div><div><b>{fmt(M["venues"])}</b> <span>venues named</span></div>'),
])
edit('briefing.html', [
    (r'(Partner briefing · data to )[^<]+', rf'\g<1>{LAST_H}'),
    (r'<p class="lede">[\d,]+ interviews with dish answers\.', f'<p class="lede">{fmt(P["n"])} interviews with dish answers.'),
])
edit('partner.html', [
    (r'Market intelligence from [\d,]+ interviews', f'Market intelligence from {N_ALL} interviews'),
    (r'<b>[\d,]+</b><span>interviews to [^<]+</span>', f'<b>{N_ALL}</b><span>interviews to {LAST_H}</span>'),
    (r'(respondent groups and the full operator survey\. Data to )[^.]+\.', rf'\g<1>{LAST_H}.'),
    (r'(guide awards\.</td><td class="num">)[\d,]+', rf'\g<1>{fmt(M["venues"])}'),
    (r'(plus counts and shares\.</td><td class="num">)[\d,]+', rf'\g<1>{fmt(sum(len(v) for v in C["m"].values()))}'),
    (r'(which cities and neighbourhoods are gaining momentum\.</td><td class="num">)[\d,]+',
     rf'\g<1>{fmt(open("partner/data/market_activity_by_quarter.csv", encoding="utf-8-sig").read().count(chr(10)) - 1)}'),
])
edit('operators.html', [(r'(figures are from the live interviews to )[^,]+(, as shown)', rf'\g<1>{LAST_H}\g<2>')])
edit('map.html', [(r"(dream-menu interviews to )[^.]+\. Venues mapped from (?:every )?interviews? to [^,]+,",
                   rf"\g<1>{LAST_H}. Venues mapped from every interview to {LAST_H},")])
for fn in glob.glob('*.html') + glob.glob('report/*.html'):
    edit(fn, [(r'(<span>Dream Menu, Glasgow\. Data to )[^.]+(\.</span>)', rf'\g<1>{LAST_H}\g<2>')], required=False)

# ---------------------------------------------------------------- dm-fresh.js
edit('dm-fresh.js', [
    (r"interviews: \{ label: 'Dream Menu interviews', size: '[^']*', from: '2025-09-01', to: '[^']*', updated: '[^']*',\s*note: '[^']*' \}",
     f"interviews: {{ label: 'Dream Menu interviews', size: '{N_ALL} interviews', from: '2025-09-01', to: '{P['last']}', updated: '{TODAY}',\n"
     f"      note: 'Dish categories refined 24 Oct 2026. Interviews to {LAST_S} added {dt.date.fromisoformat(TODAY).strftime('%-d %b')}.' }}"),
    (r"venues: \{ label: 'Venues named by guests', size: '[^']*', from: '2025-09-01', to: '[^']*', updated: '[^']*',\s*note: '[^']*' \}",
     f"venues: {{ label: 'Venues named by guests', size: '{fmt(M['venues'])} venues, {fmt(M['pinned'])} pinned', from: '2025-09-01', to: '{M['interviews_to']}', updated: '{TODAY}',\n"
     f"      note: 'Addresses researched 22 Oct 2026; new venues added {dt.date.fromisoformat(TODAY).strftime('%-d %b')}.' }}"),
    (r"analysis: \{ label: 'Dream Menu analysis', size: '([^']*)', to: '[^']*', updated: '[^']*' \}",
     rf"analysis: {{ label: 'Dream Menu analysis', size: '\1', to: '{P['last']}', updated: '{TODAY}' }}"),
])
# ---------------------------------------------------------------- awards (from awards.js meta)
_s = open('awards.js', encoding='utf-8').read()
_m = re.search(r'window\.DM_AWARDS\s*=\s*', _s)
AWD = json.JSONDecoder().raw_decode(_s[_m.end():])[0]
AWM, _G, _PL = AWD['meta'], AWD['groups'], AWD['places']
_star = lambda p: any(_G[a[0]] == 'star' for a in p[10])
AW_FACTS = (f'<div class="facts"><div><b>{fmt(sum(1 for p in _PL if _star(p)))}</b> <span>MICHELIN Starred</span></div>'
            f'<div><b>{fmt(sum(1 for p in _PL if any(_G[a[0]] == "fifty" for a in p[10])))}</b> <span>on a 50 Best list</span></div>'
            f'<div><b>{fmt(sum(1 for p in _PL if p[15]))}</b> <span>also named by guests</span></div>'
            f'<div><b>{fmt(sum(1 for p in _PL if p[6] == "Scotland" and _star(p)))}</b> <span>starred in Scotland</span></div></div>')
AW_PLACES, AW_N, AW_BUILT = fmt(AWM['places']), fmt(AWM['awards']), AWM['built']
AW_H = dt.date.fromisoformat(AW_BUILT).strftime('%-d %b %Y')
edit('tools/build_nav.py', [(r"'[\d,]+ MICHELIN, 50 Best and guide winners in one searchable list'",
                             f"'{AW_PLACES} MICHELIN, 50 Best and guide winners in one searchable list'")])
edit('index.html', [(r'<h3>[\d,]+ award winners</h3>', f'<h3>{AW_PLACES} award winners</h3>'),
                    (r'(<span class="eyebrow">Awards</span> )[\d,]+( award winners)', rf'\g<1>{AW_PLACES}\g<2>')], required=False)
edit('awards.html', [(r'<h1>[\d,]+ recognised <em>venues</em></h1>', f'<h1>{AW_PLACES} recognised <em>venues</em></h1>'),
                     (r'[\d,]+ awards across \d+ countries\.', f"{AW_N} awards across {AWM['countries']} countries."),
                     (r'<div class="facts"><div><b>[\d,]+</b> <span>MICHELIN Starred</span>.*?</div></div>', AW_FACTS)])
edit('how-it-works.html', [(r'[\d,]+ recognised venues and [\d,]+ awards\.', f'{AW_PLACES} recognised venues and {AW_N} awards.')])
edit('analysis.js', [(r'Awards as listed on [^.]+\.', f'Awards as listed on {AW_H}.')])
edit('onepager.html', [(r'<b>[\d,]+</b> <span>award venues mapped</span>', f'<b>{AW_PLACES}</b> <span>award venues mapped</span>')])
edit('dm-fresh.js', [(r"awards: \{ label: 'Awards and guides', size: '[^']*', to: '[^']*', updated: '[^']*',",
                      f"awards: {{ label: 'Awards and guides', size: '{AW_PLACES} award winners', to: '{AW_BUILT}', updated: '{AW_BUILT}',")])

print('updated:', ', '.join(sorted(set(changed))))
