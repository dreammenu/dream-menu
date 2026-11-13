#!/usr/bin/env python3
"""Builds the public venue and dish pages from the site's data files.

  /venue/<slug>      one page per venue guests have named at least twice (venue/<slug>.html)
  /trends            the dish index, course by course (trends.html)
  /trends/<slug>     one page per tracked dish (trends/<slug>.html)
  /badge             the "Named on Dream Menu" badge for venues (badge.html, badge.svg)

Public pages carry headline figures only (shares, counts, ranks, where each market over-indexes).
Quarterly movement and trend scores stay in the partner area (Heads of Terms 3.3 and 3.4): the figures are
written to partner/dish-moves.js (behind sign-in) and /dish-move.js fills the "Is it rising?" card on each
dish page only when that file loads, i.e. for signed-in partners.
Also rewrites the venue, trend and badge entries in sitemap.xml.

Run after refresh_static.py:  python3 tools/build_venue_pages.py && python3 tools/build_nav.py
"""
import datetime as dt, glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P, D, C, L = load('partner-data.js', 'DM_PARTNER'), load('dm-data.js', 'DM'), load('dm-cat.js', 'DMC'), load('dm-labels.js', 'DML')
SITE = 'https://www.dream-menu.com'
E = lambda x: html.escape(str(x), quote=True)
fmt = lambda n: f'{n:,}'
lab = lambda c: (L.get(c) or [c])[0]
grp = lambda c: (L.get(c) or [c, ''])[1] if len(L.get(c) or []) > 1 else ''
LAST = dt.date.fromisoformat(P['last'])
LAST_H = LAST.strftime('%-d %B %Y')
MIN_MENTIONS = D['meta']['thresholds'].get('min_public_mentions', 2)
COURSE = {'s': 'Starter', 'm': 'Main', 'd': 'Side', 'p': 'Dessert', 'k': 'Soft drink', 'a': 'Alcoholic drink', 'h': 'Hidden gem or next stop'}


def slugify(s):
    s = re.sub(r'[̀-ͯ]', '', __import__('unicodedata').normalize('NFKD', str(s)).lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


VENUES = D['venues']
VIDX = {v['i']: n for n, v in enumerate(VENUES)}
vslug = lambda v: re.sub(r'-x$', '', v['i'])
PUBLIC_V = [v for v in VENUES if (v.get('m') or 0) >= MIN_MENTIONS and v['c'] and v.get('y') != 'area']
HAS_PAGE = {v['i'] for v in PUBLIC_V}
place = lambda v: ', '.join(x for x in [v.get('tw') or v['c'], v['c'] if v.get('tw') and v['tw'] != v['c'] else '', '' if v['co'] == 'United Kingdom' else v['co']] if x)

# market sets shared with the home page
GLA, EDI = ('Glasgow', 'United Kingdom'), ('Edinburgh', 'United Kingdom')
MARKETS = [
    ('Glasgow', lambda v: (v['c'], v['co']) == GLA),
    ('Edinburgh', lambda v: (v['c'], v['co']) == EDI),
    ('Rest of Scotland', lambda v: v['na'] == 'Scotland' and (v['c'], v['co']) not in (GLA, EDI)),
    ('Rest of UK', lambda v: bool(v['c']) and v['co'] == 'United Kingdom' and v['na'] in ('England', 'Wales', 'Northern Ireland')),
    ('Outside the UK', lambda v: bool(v['c'] and v['co']) and v['co'] != 'United Kingdom'),
]
MK_CNT, MK_TOT = {}, {}
for name, pred in MARKETS:
    cnt = {}
    for n, v in enumerate(VENUES):
        if pred(v):
            for ci, k in C['v'].get(str(n)) or []:
                cnt[ci] = cnt.get(ci, 0) + k
    MK_CNT[name], MK_TOT[name] = cnt, sum(cnt.values()) or 1
W_CNT = {}
for n in range(len(VENUES)):
    for ci, k in C['v'].get(str(n)) or []:
        W_CNT[ci] = W_CNT.get(ci, 0) + k
W_TOT = sum(W_CNT.values())
CI = {c: i for i, c in enumerate(C['c'])}

# ---------------------------------------------------------------- page shell (restaurant-mot.html header and footer)
TPL = open('restaurant-mot.html', encoding='utf-8').read()
HEAD, FOOT = TPL[:TPL.find('<main>')], TPL[TPL.find('</main>') + len('</main>'):]
HEAD = HEAD.replace('<link rel="stylesheet" href="/brand.css">', '<link rel="stylesheet" href="/brand.css">\n<link rel="stylesheet" href="/pages.css">', 1)


def page(path, title, desc, body, ld=None):
    h = re.sub(r'<title>[^<]*</title>', f'<title>{E(title)}</title>', HEAD)
    for prop in ('name="description"', 'property="og:description"'):
        h = re.sub(r'(<meta ' + prop + r' content=")[^"]*', lambda m: m.group(1) + E(desc), h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(title), h)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + SITE + path, h)
    if ld:
        h = h.replace('</head>', '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>\n</head>', 1)
    fn = path.strip('/') + '.html'
    os.makedirs(os.path.dirname(fn) or '.', exist_ok=True)
    open(fn, 'w', encoding='utf-8').write(h + '<main class="pg">\n' + body + '\n</main>' + FOOT)
    return fn


def bars(items, total=None, fmtv=None):
    top = max([c for _, c, *_ in items] or [1])
    return '<ol class="pg-bars">' + ''.join(
        f'<li><span class="l">{l}</span><span class="t"><i style="width:{100 * c / top:.1f}%"></i></span><span class="v">{fmtv(c) if fmtv else c}</span></li>'
        for l, c, *_ in items) + '</ol>'


SRC = f'<p class="pg-src">Source: Dream Menu, {fmt(P["n_all"])} interviews to {LAST_H}. Qualitative fieldwork with a large base, not a representative survey. <a href="/how-it-works">How it works</a></p>'

# ---------------------------------------------------------------- dish pages
DISHES = {}   # slug -> dict(label, group, rows per course)
for k in P['order']:
    T = P['trends'][k]
    for rank, it in enumerate(T['cats'], 1):
        label = it.get('l') or lab(it['c'])
        s = slugify(label)
        d = DISHES.setdefault(s, dict(l=label, g=it.get('g') or grp(it['c']), c=it['c'], rows=[]))
        d['rows'].append(dict(course=T['label'], k=k, pct=it['pct'], n=it['n'], base=T['n'], rank=rank, of=len(T['cats'])))
        d.setdefault('mv', []).append(dict(course=T['label'], k=k, q=T['q'], n_q=T['n_q'], low=T['low'], share=it.get('share'),
                                           early=it.get('early'), late=it.get('late'), move=it.get('move'), p=it.get('p'), sig=it.get('sig'), note=T.get('note')))
DISH_OF_CAT = {d['c']: s for s, d in DISHES.items()}


def venues_for(cat, limit=8):
    ci = CI.get(cat)
    if ci is None:
        return []
    out = []
    for n, v in enumerate(VENUES):
        for c2, k in C['v'].get(str(n)) or []:
            if c2 == ci:
                out.append((k, v))
    out.sort(key=lambda x: (-x[0], -(x[1].get('m') or 0), x[1]['n']))
    return out[:limit]


def vlink(v):
    return f'<a href="/venue/{vslug(v)}">{E(v["n"])}</a>' if v['i'] in HAS_PAGE else f'<a href="/map#venue-{v["i"]}">{E(v["n"])}</a>'


# ---------------------------------------------------------------- "Worth knowing" side box
# Public insights: only headline facts (shares, ranks, markets, venues, awards). No movement (Heads of Terms 3.3/3.4).
# Each rule fires only when the pattern is strong enough to be worth saying.
BIN_N = dict(P['extra']['bin'])
FATIGUE_MAP = {'Loaded / dirty fries': 'Loaded and dirty food', 'Truffle fries': 'Loaded and dirty food'}   # as tools/build_intel.py
AWD = D.get('aw') or {}
ORD = {1: 'most-chosen', 2: 'second most-chosen', 3: 'third most-chosen'}


def public_insights(d):
    out = []
    ci = CI.get(d['c'])
    best = max(d['rows'], key=lambda r: r['pct'])
    c = best['course'].lower()
    T = P['trends'][best['k']]
    me = next(x for x in T['cats'] if (x.get('l') or lab(x['c'])) == d['l'])
    fam = d['g']
    G = next((g for g in T.get('groups') or [] if g['c'] == fam), None)
    sibs = [x for x in T['cats'] if (x.get('g') or grp(x['c'])) == fam]
    if G and len(sibs) >= 2 and G['n'] >= 30:
        sh = 100 * me['n'] / G['n']
        if sh >= 40:
            out.append(('family', f'Takes <b>{round(sh)}%</b> of all {E(fam.lower())} picks in the {E(c)} course ({me["n"]} of {G["n"]}).'))
    if len(d['rows']) > 1:
        cs = ' and '.join(E(r['course'].lower()) for r in d['rows'])
        out.append(('courses', f'Guests put it on the menu as both a {cs}: {fmt(sum(r["n"] for r in d["rows"]))} picks in all.'))
    if ci is not None and W_TOT:
        wsh = W_CNT.get(ci, 0) / W_TOT
        best_mk = None
        for name, _ in MARKETS:
            n = MK_CNT[name].get(ci, 0)
            if wsh and MK_TOT[name] >= 50 and n >= 5:
                x = (n / MK_TOT[name]) / wsh
                if x >= 1.5 and (not best_mk or x > best_mk[1]):
                    best_mk = (name, x, n)
        if best_mk:
            out.append(('market', f'{E(best_mk[0])} names it <b>{best_mk[1]:.1f}×</b> as often as all markets do ({best_mk[2]} venue mentions).'))
    allv = venues_for(d['c'], 10 ** 6)
    tot = sum(k for k, _ in allv)
    if tot >= 6 and allv:
        k, v = allv[0]
        if k / tot >= 0.25 and k >= 3:
            out.append(('venue', f'One address leads: <b>{E(v["n"])}</b> gets {k} of the {tot} venue mentions for it ({round(100 * k / tot)}%).'))
    if tot >= 10 and allv and allv[0][0] / tot < 0.15 and len(allv) >= 10:
        out.append(('spread', f'No single home: guests tie it to <b>{len(allv)}</b> different venues, none with more than {allv[0][0]} mentions.'))
    if len(allv) >= 5:
        aw = [v for _, v in allv if v['i'] in AWD]
        if len(aw) / len(allv) >= 0.4:
            out.append(('awards', f'Critics agree: {len(aw)} of the {len(allv)} venues guests name for it hold a guide award.'))
    b = FATIGUE_MAP.get(d['c'])
    if b and BIN_N.get(b):
        out.append(('bin', f'Divisive: {BIN_N[b]} guests named &ldquo;{E(b.lower())}&rdquo; as a trend they want to bin.'))
    return out[:4]


def insight_box(d):
    items = public_insights(d)
    lis = ''.join(f'<li data-k="{k}">{t}</li>' for k, t in items)
    return (f'<aside class="dm-ins" id="dm-ins"{"" if items else " hidden"}><h2>Worth knowing</h2>'
            f'<ul class="ins-list">{lis}</ul></aside>')


written = []
for s, d in DISHES.items():
    ci = CI.get(d['c'])
    rows = ''.join(f'<tr><td>{E(r["course"])}</td><td class="num"><b>{r["pct"]:.1f}%</b></td><td class="num">{fmt(r["n"])} of {fmt(r["base"])}</td><td class="num">{r["rank"]}</td></tr>' for r in d['rows'])
    best = max(d['rows'], key=lambda r: r['pct'])
    mk = []
    if ci is not None:
        wsh = W_CNT.get(ci, 0) / W_TOT if W_TOT else 0
        for name, _ in MARKETS:
            c = MK_CNT[name].get(ci, 0)
            if wsh and MK_TOT[name] >= 50:
                mk.append((name, c, 100 * c / MK_TOT[name], MK_TOT[name]))
    mk_rows = ''.join(
        f'<tr><td>{E(n)}</td><td class="num" title="{c} of {fmt(t)} mentions"><b>{sh:.1f}%</b></td><td class="num">{100 * wsh:.1f}%</td></tr>' if c >= 3 else
        f'<tr><td>{E(n)}</td><td class="num">–</td><td class="num">{100 * wsh:.1f}%</td></tr>' for n, c, sh, t in mk)
    vs = venues_for(d['c'])
    vl = ''.join(f'<li>{vlink(v)} <span class="pg-mut">{E(place(v))}</span> <b>{k}</b></li>' for k, v in vs)
    same = sorted((x for x in DISHES.values() if x['g'] == d['g'] and x is not d), key=lambda x: -max(r['pct'] for r in x['rows']))[:8]
    rel = ''.join(f'<a class="pg-chip" href="/trends/{slugify(x["l"])}">{E(x["l"])}</a>' for x in same)
    lede = (f'{best["pct"]:.1f}% of guests who answered the {best["course"].lower()} question chose {E(d["l"])}, '
            f'number {best["rank"]} of the {best["of"]} {best["course"].lower()} dishes we track.')
    ibox = insight_box(d)
    body = f'''<section class="pg-hero"><div class="wrap pg-hero-ins{" has-ins" if "hidden" not in ibox.split(">")[0] else ""}"><div class="pg-hero-main">
  <p class="eyebrow"><a href="/trends">Dish trends</a>{(" · " + E(d["g"])) if d["g"] else ""}</p>
  <h1>{E(d["l"])}</h1>
  <p class="lede">{lede}</p>
  <div class="pg-facts"><div><b>{best["pct"]:.1f}%</b><span>of {E(best["course"].lower())} answers</span></div><div><b>#{best["rank"]}</b><span>{E(best["course"].lower())} dish</span></div><div><b>{fmt(sum(r["n"] for r in d["rows"]))}</b><span>guests chose it</span></div><div><b>{len(vs) and fmt(sum(k for k, _ in venues_for(d["c"], 10**6)))}</b><span>venue mentions for it</span></div></div>
</div>{ibox}</div></section>
<section><div class="wrap pg-grid">
  <div class="card"><h2>On the dream menu</h2><div class="tablewrap" style="border:0"><table><thead><tr><th>Course</th><th class="num">Share</th><th class="num">Guests</th><th class="num">Rank</th></tr></thead><tbody>{rows}</tbody></table></div>
  <p class="pg-mut">Share of the guests who answered that course, all interviews.</p></div>
  <div class="card"><h2>By market</h2>{('<div class="tablewrap" style="border:0"><table><thead><tr><th>Market</th><th class="num">Share here</th><th class="num">All markets</th></tr></thead><tbody>' + mk_rows + '</tbody></table></div><p class="pg-mut">Share of each market&#39;s venue-linked dish mentions, so markets with fewer answers compare fairly; shown from three mentions. Markets outside Scotland are early signals.</p>') if mk_rows else '<p class="pg-mut">Not enough venue mentions to compare markets yet.</p>'}</div>
  <div class="card"><h2>Where guests go for it</h2>{('<ol class="pg-list">' + vl + '</ol>') if vl else '<p class="pg-mut">No venue named for this dish more than once yet.</p>'}</div>
  <div class="card pg-lock" id="dm-move" data-slug="{s}"><h2>Is it rising?</h2><p>Quarter-by-quarter movement, a clear-move test and a trend score out of 10 for {E(d["l"])} are for Dream Menu partners.</p><p><a class="go" href="/login?next=/trends/{s}">Partner sign-in</a> · <a class="go" href="/for-business#work">Become a partner</a></p></div>
</div></section>
{('<section><div class="wrap"><h2 class="pg-h2">Also in ' + E(d["g"].lower()) + '</h2><div class="pg-chips">' + rel + '</div></div></section>') if rel else ''}
<section><div class="wrap">{SRC}</div></section>
<script src="/partner/dish-moves.js" defer></script><script src="/dish-move.js" defer></script>'''
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': f'{d["l"]}: how often guests choose it', 'dateModified': P['last'],
          'publisher': {'@type': 'Organization', 'name': 'Dream Menu', 'url': SITE}, 'about': d['l'], 'url': f'{SITE}/trends/{s}'}
    written.append(page(f'/trends/{s}', f'{d["l"]}: dish trend | Dream Menu',
                        f'{d["l"]} on the dream menu: {best["pct"]:.1f}% of {best["course"].lower()} answers from {fmt(P["n_all"])} Dream Menu interviews, where guests go for it and which markets name it most.', body, ld))

# share-shift theories: which dishes in the same course moved the other way (likely substitutes)
def _corr(a, b, low):
    pr = [(x, y) for x, y, l in zip(a or [], b or [], low or [False] * 9) if x is not None and y is not None and not l]
    if len(pr) < 3:
        return 0.0
    mx, my = sum(x for x, _ in pr) / len(pr), sum(y for _, y in pr) / len(pr)
    sxy = sum((x - mx) * (y - my) for x, y in pr)
    sx = sum((x - mx) ** 2 for x, _ in pr) ** .5
    sy = sum((y - my) ** 2 for _, y in pr) ** .5
    return sxy / (sx * sy) if sx and sy else 0.0


def shifts(k, it):
    T = P['trends'][k]
    m = it.get('move') or 0
    out = []
    for o in T['cats']:
        if o is it or o.get('move') is None:
            continue
        om = o['move']
        if abs(m) >= 0.5 and (om * m >= 0 or abs(om) < 0.5):
            continue                      # need an opposite move
        if abs(m) < 0.5 and abs(om) < 1.0:
            continue                      # steady dish: show only real movers it competes with
        same = (o.get('g') or grp(o['c'])) == (it.get('g') or grp(it['c']))
        r = _corr(it.get('share'), o.get('share'), T['low'])
        w = abs(om) * (1.6 if same else 1.0) * (1 + max(0.0, -r)) * (1.3 if o.get('sig') else 1.0)
        out.append(dict(l=o.get('l') or lab(o['c']), s=slugify(o.get('l') or lab(o['c'])), move=om, sig=bool(o.get('sig')),
                        same=same, r=round(r, 2), w=w))
    out.sort(key=lambda x: -x['w'])
    for x in out:
        x.pop('w')
    g = it.get('g') or grp(it['c'])
    G = {x['c']: x for x in T.get('groups') or []}
    grp_row = G.get(g)
    other = sorted((x for x in T.get('groups') or [] if x['c'] != g and x.get('move') is not None
                    and (abs(m) < 0.5 or x['move'] * m < 0)), key=lambda x: -abs(x['move']))[:2]
    return dict(sub=out[:3], grp=dict(l=g, move=grp_row['move'], sig=bool(grp_row.get('sig'))) if grp_row and g else None,
                og=[dict(l=x['c'], move=x['move'], sig=bool(x.get('sig'))) for x in other])


# partner-only movement data for the dish pages (served behind sign-in by middleware.js: /partner/:path*)
I = load('partner/intel-data.js', 'DM_INTEL')
CIX = {(c['course'], c['l']): c for c in I['ci'] if c.get('level') == 'Dish'}
OPP = {(o['course'], o['l']): o for o in I['opp']}
MOVES = {}
SCORED = sorted(I['opp'], key=lambda o: -o['score'])


def partner_insights(k, it, m):
    """Movement insights for signed-in partners. Returned as plain text; each fires only when notable."""
    T = P['trends'][k]
    out = []
    sh, low, q = it['share'], T['low'], T['q']
    solid = [(i, v) for i, v in enumerate(sh) if v is not None and not low[i]]
    ql = lambda x: x.split('-')[1] + ' ' + x.split('-')[0]
    if len(solid) >= 3:
        li, lv = solid[-1]
        if lv == max(v for _, v in solid) and lv > solid[0][1]:
            out.append(f'Its highest share in any quarter with {P["min_n"]}+ answers came in {ql(q[li])} ({lv:.1f}%), the latest such quarter.')
        elif lv == min(v for _, v in solid) and lv < solid[0][1]:
            out.append(f'Its lowest share in any quarter with {P["min_n"]}+ answers came in {ql(q[li])} ({lv:.1f}%), the latest such quarter.')
    mv = sorted(T['cats'], key=lambda c: -c['move'])
    if mv[0] is it and it['move'] >= 1:
        out.append(f'The fastest-rising {T["label"].lower()} we track ({it["move"]:+.1f} pts{", a clear move" if it["sig"] else ""}).')
    elif mv[-1] is it and it['move'] <= -1:
        out.append(f'The fastest-falling {T["label"].lower()} we track ({it["move"]:+.1f} pts{", a clear move" if it["sig"] else ""}).'.replace('+-', '-'))
    if it['early'] >= 1 and it['late'] >= 2 * it['early']:
        out.append(f'More than doubled: {it["early"]:.1f}% earlier to {it["late"]:.1f}% recently.')
    elif it['early'] >= 2 and it['late'] <= 0.5 * it['early']:
        out.append(f'Share has halved or worse: {it["early"]:.1f}% earlier to {it["late"]:.1f}% recently.')
    lab = it.get('l') or lab_(it['c'])
    pos = next((n for n, o in enumerate(SCORED, 1) if o['course'] == k and o['l'] == lab), None)
    if pos and pos <= 5:
        out.append(f'Number {pos} of the {len(SCORED)} dishes and drinks with a trend score.')
    rank = lambda x: 0 if x.startswith('Number') else 1 if 'fastest' in x else 2 if ('doubled' in x or 'halved' in x) else 3
    return [x.replace('+-', '−').replace('(-', '(−') for x in sorted(out, key=rank)]


lab_ = lab


def split_parts(o):
    """Score parts on the 0-10 scale, rounded so they add up exactly to the published score (+ any Bin it penalty)."""
    parts = o.get('parts') or {}
    total = round(o['score'] + (o.get('fat') or 0))          # in tenths of a point on the 0-10 scale
    raw = {k: v for k, v in parts.items()}
    scale = total / sum(raw.values()) if sum(raw.values()) else 0
    exact = {k: v * scale for k, v in raw.items()}
    fl = {k: int(v) for k, v in exact.items()}
    for k in sorted(exact, key=lambda k: -(exact[k] - fl[k]))[:total - sum(fl.values())]:
        fl[k] += 1
    return {k: fl[k] / 10 for k in parts}

for s, d in DISHES.items():
    rows = []
    for m in d['mv']:
        c, o = CIX.get((m['k'], d['l'])) or {}, OPP.get((m['k'], d['l']))
        m = dict(m, lo=c.get('lo'), hi=c.get('hi'))
        if o:
            m.update(score=round(o['score'] / 10, 1), tier=o['tier'], parts=split_parts(o), fat=round((o.get('fat') or 0) / 10, 1))
        it = next((x for x in P['trends'][m['k']]['cats'] if (x.get('l') or lab(x['c'])) == d['l']), None)
        if it is not None:
            m['shift'] = shifts(m['k'], it)
        if it is not None:
            m['ins'] = partner_insights(m['k'], it, m)
        rows.append({k: v for k, v in m.items() if v is not None and k != 'k'})
    MOVES[s] = rows
MOVE_META = dict(last=P['last'], early=P['method']['early'], late=P['method']['late'], test=P['method']['test'], min_n=P.get('min_n') or 100)
with open('partner/dish-moves.js', 'w', encoding='utf-8') as f:
    f.write('/* Generated by tools/build_venue_pages.py. Partner only (behind sign-in). */\nwindow.DM_DISHMOVES='
            + json.dumps(dict(meta=MOVE_META, d=MOVES), ensure_ascii=False, separators=(',', ':')) + ';\n')

# dish index
idx_cols = ''
for k in P['order']:
    T = P['trends'][k]
    lis = ''.join(f'<li><a href="/trends/{slugify(it.get("l") or lab(it["c"]))}">{E(it.get("l") or lab(it["c"]))}</a><span>{it["pct"]:.1f}%</span></li>' for it in T['cats'])
    idx_cols += f'<div class="card"><h2>{E(T["label"])}</h2><p class="pg-mut">{fmt(T["n"])} answers</p><ol class="pg-idx">{lis}</ol></div>'
body = f'''<section class="pg-hero"><div class="wrap"><p class="eyebrow">Dish trends</p><h1>Every dish we <em>track</em></h1>
<p class="lede">{len(DISHES)} dishes and drinks across six courses, each with its share of guests, where people go for it and which markets name it most. Pick one to open its page.</p></div></section>
<section><div class="wrap pg-grid">{idx_cols}</div></section>
<section><div class="wrap">{SRC}</div></section>'''
written.append(page('/trends', 'Dish trends: every dish we track | Dream Menu', f'{len(DISHES)} dishes and drinks from {fmt(P["n_all"])} Dream Menu interviews, course by course, with a page for each.', body))

# ---------------------------------------------------------------- venue pages
by_city = {}
for v in PUBLIC_V:
    by_city.setdefault((v['c'], v['co']), []).append(v)
for lst in by_city.values():
    lst.sort(key=lambda v: (-(v.get('m') or 0), v['n']))
AW = D.get('aw') or {}
OA = load('other-awards.js', 'DM_OA')['v']   # tools/build_other_awards.py
STOP = {'the', 'restaurant', 'kitchen', 'house', 'cafe', 'glasgow', 'edinburgh', 'london', 'grill', 'and', 'with', 'street', 'road'}
for v in PUBLIC_V:
    s = vslug(v)
    n = VIDX[v['i']]
    city = by_city[(v['c'], v['co'])]
    rank = city.index(v) + 1
    cats = sorted(C['v'].get(str(n)) or [], key=lambda x: -x[1])[:10]
    cat_items = [(f'<a href="/trends/{DISH_OF_CAT[C["c"][ci]]}">{E(lab(C["c"][ci]))}</a>' if C['c'][ci] in DISH_OF_CAT else E(lab(C['c'][ci])), k) for ci, k in cats]
    courses = sorted(((COURSE.get(c, c), k) for c, k in (v.get('cs') or {}).items()), key=lambda x: -x[1])
    words = ''.join(f'<span class="pg-chip">{E(w)}</span>' for w in (v.get('d') or [])[:8])
    # only quotes that name the venue: the matching that attached them can pick up answers about another place
    keys = [w for w in re.findall(r"[a-z0-9']+", slugify(v['n']).replace('-', ' ')) if len(w) >= 4 and w not in STOP]
    own = [(c, t) for c, t in (v.get('q') or []) if keys and any(k in slugify(t).replace('-', ' ') for k in keys)]
    quotes = ''.join(f'<blockquote class="quote">{E(t)}<small>Guest answer, {E(COURSE.get(c, c).lower())}</small></blockquote>' for c, t in own[:4])
    aw = AW.get(v['i'])
    other = OA.get(v['i'], [])
    lis = [f'<li>{E(a)}</li>' for a in (aw['a'] if aw else [])]
    lis += [f'<li>{E(t)}' + (f' <a class="pg-src-l" href="{E(u)}" rel="nofollow noopener" target="_blank">source</a>' if u.startswith('http') else '') + '</li>' for t, _, _, u in other]
    aw_html = ('<div class="card"><h2>Awards and guides</h2><ul class="pg-list">' + ''.join(lis) +
               '</ul><p class="pg-mut"><a href="/awards">All award winners</a>' + (' · Includes Scottish, UK and bar awards matched by hand. Spotted something missing? <a href="mailto:contact.dreammenu@gmail.com">Tell us</a>' if other else '') + '</p></div>') if lis else ''
    near = [x for x in city if x is not v][:6]
    near_html = ''.join(f'<li>{vlink(x)} <b>{x["m"]}</b></li>' for x in near)
    addr = E(v['ad']) if v.get('ad') and v.get('p') == 'exact' else E(place(v))
    closed = ' <span class="mk-tag early">Closed</span>' if v.get('s') == 'closed' else ''
    lede = (f'Named {v["m"]} times by {v.get("g") or v["m"]} Dream Menu guests: number {rank} of {len(city)} venues named in {E(v["c"])}.')
    body = f'''<section class="pg-hero"><div class="wrap">
  <p class="eyebrow"><a href="/rankings">Venues</a> · {E(place(v))}</p>
  <h1>{E(v["n"])}{closed}</h1>
  <p class="lede">{lede}</p>
  <p class="pg-mut">{addr} · <a href="/map#venue-{v["i"]}">See it on the map</a></p>
  <div class="pg-facts"><div><b>{v["m"]}</b><span>times named</span></div><div><b>{v.get("g") or v["m"]}</b><span>guests</span></div><div><b>#{rank}</b><span>in {E(v["c"])}</span></div><div><b>{sum((v.get("cs") or {}).values())}</b><span>dishes logged</span></div></div>
</div></section>
<section><div class="wrap pg-grid">
  <div class="card"><h2>What guests name here</h2>{bars(cat_items) if cat_items else '<p class="pg-mut">No dish coded yet.</p>'}{('<div class="pg-chips" style="margin-top:12px">' + words + '</div>') if words else ''}</div>
  <div class="card"><h2>For which course</h2>{bars([(E(c), k) for c, k in courses]) if courses else '<p class="pg-mut">No course recorded.</p>'}</div>
  {aw_html}
  <div class="card"><h2>Also named in {E(v["c"])}</h2><ol class="pg-list">{near_html}</ol><p class="pg-mut"><a href="/rankings">Full rankings</a></p></div>
</div></section>
{('<section><div class="wrap"><h2 class="pg-h2">In guests&rsquo; words</h2><div class="pg-quotes">' + quotes + '</div></div></section>') if quotes else ''}
<section><div class="wrap"><div class="card pg-badge"><div><h2>Run {E(v["n"])}?</h2><p>Show guests you made the list. Add the free &ldquo;Named on Dream Menu&rdquo; badge to your website; it links back to this page.</p>
<p><a class="go" href="/badge?v={s}">Get the badge</a> · <a class="go" href="/restaurant-mot">Restaurant MOT</a></p></div>
<a href="/badge?v={s}"><img src="/badge.svg" alt="Named on Dream Menu" width="180" height="60"></a></div>{SRC}</div></section>'''
    ld = {'@context': 'https://schema.org', '@type': 'Restaurant', 'name': v['n'], 'url': f'{SITE}/venue/{s}'}
    if v.get('ad') and v.get('p') == 'exact':
        ld['address'] = v['ad']
    if v.get('la') is not None and v.get('t') == 'L':
        ld['geo'] = {'@type': 'GeoCoordinates', 'latitude': v['la'], 'longitude': v['lo']}
    written.append(page(f'/venue/{s}', f'{v["n"]}, {place(v)} | Dream Menu',
                        f'{v["n"]} in {place(v)}: named {v["m"]} times by Dream Menu guests, number {rank} in {v["c"]}. What guests order there and why.', body, ld))

# remove pages for venues that dropped below the threshold
for fn in glob.glob('venue/*.html'):
    if fn not in written:
        os.remove(fn)

# ---------------------------------------------------------------- badge
open('badge.svg', 'w', encoding='utf-8').write(
    '<svg xmlns="http://www.w3.org/2000/svg" width="180" height="60" viewBox="0 0 180 60" role="img" aria-label="Named on Dream Menu">'
    '<rect x="1" y="1" width="178" height="58" rx="29" fill="#0b0b0b" stroke="#debd1a" stroke-width="2"/>'
    '<circle cx="30" cy="30" r="19" fill="#fff"/><path d="M19 34h22M21 33a9 9 0 0 1 18 0M30 22v2" stroke="#1c2152" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    '<text x="58" y="26" font-family="Arial,Helvetica,sans-serif" font-size="10" font-weight="700" fill="#debd1a" letter-spacing="1.2">NAMED ON</text>'
    '<text x="58" y="42" font-family="Arial,Helvetica,sans-serif" font-size="15" font-weight="800" fill="#fff">DREAM MENU</text></svg>\n')
body = f'''<section class="pg-hero"><div class="wrap"><p class="eyebrow">For venues</p><h1>Named on <em>Dream Menu</em></h1>
<p class="lede">If guests have named your venue on Dream Menu, you can show it. The badge is free and links to your venue page, where guests can see what people order and why.</p></div></section>
<section><div class="wrap pg-grid">
  <div class="card"><h2>1. Find your venue</h2><p>Every venue named at least twice has a page. Search the <a href="/rankings">rankings</a> or the <a href="/map">map</a>, or type your venue below.</p>
  <label class="pg-field">Venue<input id="bq" list="bl" placeholder="Start typing a venue name" autocomplete="off"></label><datalist id="bl"></datalist></div>
  <div class="card"><h2>2. Copy the code</h2><p>Paste this into your website where the badge should appear.</p><textarea id="bc" rows="4" readonly></textarea><p><button type="button" class="pr-copy" id="bcopy">Copy the code</button></p></div>
  <div class="card"><h2>Preview</h2><p id="bp"><img src="/badge.svg" alt="Named on Dream Menu" width="180" height="60"></p><p class="pg-mut">The badge stays the same size on any background. On print, use the Dream Menu Popular Venue sticker instead (ask us).</p></div>
</div></section>
<script>(function(){{var V={json.dumps({vslug(v): v['n'] + ', ' + place(v) for v in PUBLIC_V}, ensure_ascii=False)};
var q=document.getElementById('bq'),c=document.getElementById('bc'),l=document.getElementById('bl'),p=document.getElementById('bp');
l.innerHTML=Object.keys(V).map(function(k){{return '<option value="'+V[k].replace(/"/g,'&quot;')+'">'}}).join('');
function code(s){{var u='{SITE}/venue/'+s;return '<a href="'+u+'" title="Named on Dream Menu"><img src="{SITE}/badge.svg" alt="Named on Dream Menu" width="180" height="60"></a>'}}
function set(s){{if(!s||!V[s])return;c.value=code(s);p.innerHTML=code(s);q.value=V[s]}}
q.addEventListener('change',function(){{for(var k in V)if(V[k]===q.value)set(k)}});
set(new URLSearchParams(location.search).get('v'));if(!c.value)c.value=code('your-venue');
document.getElementById('bcopy').onclick=function(){{c.select();(navigator.clipboard?navigator.clipboard.writeText(c.value):Promise.reject()).then(function(){{document.getElementById('bcopy').textContent='Copied'}},function(){{document.execCommand('copy')}})}};}})();</script>'''
written.append(page('/badge', 'Named on Dream Menu: badge for venues | Dream Menu', 'A free badge for venues Dream Menu guests have named, linking to the venue page.', body))

# ---------------------------------------------------------------- rankings data: only the fields /rankings uses (dm-data.js is ~830 KB)
KEEP_V = ('i', 'n', 'c', 'co', 'r', 'na', 'tw', 'y', 's', 'm', 'g', 'cs', 'd')
KEEP_M = ('id', 'k', 'n', 'co', 'v', 'g', 'so')
rk = dict(markets=[{k: m[k] for k in KEEP_M if k in m} for m in D['markets']],
          venues=[dict({k: v[k] for k in KEEP_V if k in v and v[k] not in (None, '', [])}, **({'pg': 1} if v['i'] in HAS_PAGE else {}))
                  for v in VENUES if v.get('m')],
          aw={i: {'a': a['a'][:1]} for i, a in AW.items()})
open('rank-data.js', 'w', encoding='utf-8').write('/* Generated by tools/build_venue_pages.py for /rankings. */\nwindow.DM=' + json.dumps(rk, ensure_ascii=False, separators=(',', ':')) + ';\n')

# ---------------------------------------------------------------- city guides
# One page per city with enough venues named. Shares are of the city's own mentions, so cities compare fairly.
from vinfo import vinfo as _vi
CITY_MIN_V, DEEP_G = 5, 30
_cm = {(m['n'], m['co']): m for m in D['markets'] if m['k'] == 'city'}
_allk = {}
for v in VENUES:
    for k, n in v.get('k') or []:
        _allk[k] = _allk.get(k, 0) + n
_allt = sum(_allk.values()) or 1
_bc = {}
for v in sorted(VENUES, key=lambda v: -(v.get('m') or 0)):
    if v.get('c') and v.get('m'):
        _bc.setdefault((v['c'], v['co']), []).append(v)
cslug = lambda c, co: slugify(c if co == 'United Kingdom' else f'{c} {co}')
CITIES = sorted([(c, co) for (c, co), lst in _bc.items() if c and (c, co) in _cm and len([v for v in lst if v.get('y') != 'area']) >= CITY_MIN_V],
                key=lambda k: -_cm[k]['g'])
CPICK = [('s', 'Starter'), ('m', 'Main'), ('d', 'Side'), ('p', 'Dessert'), ('k', 'Soft drink'), ('a', 'Drink')]


def city_page(c, co):
    M, vs = _cm[(c, co)], [v for v in _bc[(c, co)] if v.get('y') != 'area' and v.get('s') != 'closed']
    deep, tot = M['g'] >= DEEP_G, sum(v['m'] for v in vs) or 1
    pc = lambda n: f'{100 * n / tot:.1f}%'
    name = c if co == 'United Kingdom' else f'{c}, {co}'
    aw_n = sum(1 for v in vs if v['i'] in AW)
    # the city's dream menu: the venue most named for each course
    picks = []
    for k, lab in CPICK:
        best = max(vs, key=lambda v: ((v.get('cs') or {}).get(k, 0), v['m']))
        n = (best.get('cs') or {}).get(k, 0)
        if n >= (2 if deep else 1):
            picks.append(f'<article><span>{lab}</span><h3>{vlink(best)}</h3><p>Known for {E((best.get("k") or [["its cooking"]])[0][0].lower())}</p><small>named {n} time{"s" if n != 1 else ""} for this course</small></article>')
    top = vs[:15 if deep else 10]
    top_html = bars([(vlink(v) + (' <span class="mk-tag">Award</span>' if v['i'] in AW else ''), v['m']) for v in top], fmtv=pc)
    gems = sorted([v for v in vs if v not in vs[:10] and (v.get('cs') or {}).get('h', 0) >= 2], key=lambda v: -(v['cs']['h']))[:8]
    gems_html = ''.join(f'<li>{vlink(v)} <span class="pg-mut">{E((v.get("k") or [[""]])[0][0])}</span></li>' for v in gems)
    # what this city names more than everywhere else (points of share), deep markets only
    over = ''
    if deep:
        ck = {}
        for v in vs:
            for k, n in v.get('k') or []:
                ck[k] = ck.get(k, 0) + n
        ct = sum(ck.values()) or 1
        rows = sorted(((100 * n / ct - 100 * (_allk[k] - n) / max(1, _allt - ct), k, 100 * n / ct) for k, n in ck.items() if n >= 8 and k != 'Other'), reverse=True)
        up, dn = [r for r in rows if r[0] > 0][:5], [r for r in rows[::-1] if r[0] < 0][:3]
        if up:
            over = ('<div class="card"><h2>What ' + E(c) + ' names more than everywhere else</h2>'
                    + _vi(f'Each figure is the gap, in percentage points, between a food’s share of {c}’s venue mentions and its share everywhere else. Plus means {c} names it more.\nShares keep a big city and a small one comparable. Gaps under a point or two are not worth acting on.')
                    + '<ol class="pg-idx">' + ''.join(f'<li>{E(k)}<span>+{d:.1f} pts ({s:.1f}% here)</span></li>' for d, k, s in up) + '</ol>'
                    + ('<p class="pg-mut">Named less here: ' + ', '.join(f'{E(k).lower()} ({d:.1f} pts)' for d, k, s in dn) + '.</p>' if dn else '') + '</div>')
    awv = [v for v in vs if v['i'] in AW][:6]
    aw_html = ('<div class="card"><h2>Where guests and guides agree</h2><ol class="pg-list">' + ''.join(f'<li>{vlink(v)} <span class="pg-mut">{E(AW[v["i"]]["a"][0])}</span></li>' for v in awv)
               + '</ol><p class="pg-mut"><a href="/awards">All award winners</a></p></div>') if awv else ''
    qs = []
    for v in vs[:12]:
        keys = [w for w in re.findall(r"[a-z0-9']+", slugify(v['n']).replace('-', ' ')) if len(w) >= 4 and w not in STOP]
        for cc, t in v.get('q') or []:
            if keys and any(k in slugify(t).replace('-', ' ') for k in keys) and 40 < len(t) < 240:
                qs.append(f'<blockquote class="quote">{E(t)}<small>Guest answer, {E(COURSE.get(cc, cc).lower())}</small></blockquote>')
                break
    others = ''.join(f'<a class="pg-chip" href="/city/{cslug(*k)}">{E(k[0])}</a>' for k in CITIES if k != (c, co))
    early = '' if deep else f'<p class="pg-early"><b>Early signal.</b> {M["g"]} guests have named venues in {E(c)} so far. Read this as a list of pointers, not a ranking. <a href="/take-part">Add your dream menu</a>.</p>'
    lede = (f'{fmt(M["g"])} food-led guests have named {fmt(len(vs))} places in {E(c)} as part of their dream menu. These are the ones they name most, the hidden gems, and what sets the city’s taste apart.'
            if deep else f'The places in {E(c)} that Dream Menu guests name when asked for their dream menu.')
    body = f'''<section class="pg-hero"><div class="wrap">
  <p class="eyebrow"><a href="/cities">City guides</a> · {E(co if co != "United Kingdom" else (M.get("na") or co))}</p>
  <h1>Where {E(c)}&rsquo;s foodies <em>eat</em></h1>
  <p class="lede">{lede}</p>{early}
  <div class="pg-facts"><div><b>{fmt(M["g"])}</b><span>guests</span></div><div><b>{fmt(len(vs))}</b><span>venues named</span></div><div><b>{100 * tot / max(1, D["meta"]["mentions"]):.1f}%</b><span>of all mentions</span></div><div><b>{aw_n}</b><span>hold a guide award</span></div></div>
  <p class="pg-mut"><a href="/map">Open {E(c)} on the map</a> · <a href="/rankings">Rankings by course</a></p>
</div></section>
{('<section><div class="wrap"><h2 class="pg-h2">The ' + E(c) + ' dream menu</h2><p class="pg-mut" style="margin:-6px 0 12px">The venue guests name most for each course.</p><div class="ct-menu">' + ''.join(picks) + '</div></div></section>') if len(picks) >= 3 else ''}
<section><div class="wrap pg-grid">
  <div class="card ct-wide"><h2>Most named in {E(c)}</h2>{_vi(f'Each bar is a venue’s share of all venue mentions in {c}. One guest can name several venues, so this measures how often a place comes to mind, not how good it is.' + ('' if deep else chr(10) + 'With few guests so far, the order can change with a handful of interviews.'))}{top_html}</div>
  {('<div class="card"><h2>Hidden gems and next stops</h2><p class="pg-mut" style="margin-top:-4px">Outside the top ten, named by guests as a gem or the place they want to try next.</p><ol class="pg-list">' + gems_html + '</ol></div>') if gems else ''}
  {over}
  {aw_html}
</div></section>
{('<section><div class="wrap"><h2 class="pg-h2">In guests&rsquo; words</h2><div class="pg-quotes">' + ''.join(qs[:4]) + '</div></div></section>') if qs else ''}
<section><div class="wrap pg-grid">
  <div class="card"><h2>Run a venue in {E(c)}?</h2><p>See how {E(c)}&rsquo;s taste differs from other cities, check whether your venue has a page, and get the free badge.</p><p><a class="go" href="/analysis#cities">Every city&rsquo;s appetite</a> · <a class="go" href="/badge">Get the badge</a> · <a class="go" href="/operators">Operator toolkit</a></p></div>
  {('<div class="card"><h2>By neighbourhood</h2><div class="pg-chips">' + AREA_CHIPS[(c, co)] + '</div></div>') if AREA_CHIPS.get((c, co)) else ''}
  <div class="card"><h2>Other city guides</h2><div class="pg-chips">{others}</div></div>
</div>{SRC}</section>'''
    ld = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': f'Where {c}’s foodies eat', 'numberOfItems': len(top),
          'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': v['n'], 'url': f'{SITE}/venue/{vslug(v)}' if v['i'] in HAS_PAGE else f'{SITE}/map#venue-{v["i"]}'} for i, v in enumerate(top, 1)]}
    return page(f'/city/{cslug(c, co)}', f'Where {c}’s foodies eat: {len(vs)} places named | Dream Menu',
                f'The restaurants, bars and cafes in {name} that {M["g"]} Dream Menu guests name most: the city’s dream menu course by course, hidden gems and award holders.', body, ld)


# neighbourhoods: postcode districts grouped into the areas people actually use. Only venues with a confirmed address count.
AREAS = {('Glasgow', 'United Kingdom'): [('City Centre and Merchant City', ['G1', 'G2']), ('Finnieston and Charing Cross', ['G3']), ('West End', ['G11', 'G12', 'G20']),
                                         ('Woodlands and St George’s Cross', ['G4']), ('Southside', ['G41', 'G42', 'G43', 'G44', 'G46']), ('East End and Dennistoun', ['G31', 'G40'])],
         ('Edinburgh', 'United Kingdom'): [('Old Town', ['EH1']), ('New Town', ['EH2']), ('Stockbridge and the West End', ['EH3']), ('Leith and Leith Walk', ['EH6', 'EH7']),
                                           ('Southside, Bruntsfield and Morningside', ['EH8', 'EH9', 'EH10'])]}
_pcd = lambda v: (re.search(r'\b((?:G|EH)\d{1,2})\s?\d[A-Z]{2}\b', v.get('ad') or '') or [None, None])[1]
aslug = lambda c, a: slugify(f'{c} {a}')
AREA_V = {}
for _ck, _lst in AREAS.items():
    for _an, _ds in _lst:
        _vs = [v for v in _bc.get(_ck, []) if v.get('y') != 'area' and v.get('s') != 'closed' and v.get('p') == 'exact' and _pcd(v) in _ds]
        if len(_vs) >= 8:
            AREA_V[(_ck, _an)] = _vs
AREA_CHIPS = {ck: ''.join(f'<a class="pg-chip" href="/area/{aslug(ck[0], an)}">{E(an)}</a>' for (c2, an) in AREA_V if c2 == ck) for ck in AREAS}


def area_page(ck, an):
    c, vs = ck[0], AREA_V[(ck, an)]
    tot, ctot = sum(v['m'] for v in vs) or 1, sum(v['m'] for v in _bc[ck]) or 1
    pc = lambda n: f'{100 * n / tot:.1f}%'
    picks = []
    for k, lab in CPICK[:4]:
        best = max(vs, key=lambda v: ((v.get('cs') or {}).get(k, 0), v['m']))
        n = (best.get('cs') or {}).get(k, 0)
        if n >= 2:
            picks.append(f'<article><span>{lab}</span><h3>{vlink(best)}</h3><p>Known for {E((best.get("k") or [["its cooking"]])[0][0].lower())}</p><small>named {n} times for this course</small></article>')
    gems = sorted([v for v in vs[6:] if (v.get('cs') or {}).get('h', 0) >= 2], key=lambda v: -(v['cs']['h']))[:6]
    kk = {}
    for v in vs:
        for k, n in v.get('k') or []:
            kk[k] = kk.get(k, 0) + n
    kt = sum(kk.values()) or 1
    known = ', '.join(f'{E(k).lower()} ({100 * n / kt:.0f}%)' for k, n in sorted(kk.items(), key=lambda x: -x[1])[:4] if k != 'Other')
    others = ''.join(f'<a class="pg-chip" href="/area/{aslug(c, a2)}">{E(a2)}</a>' for (c2, a2) in AREA_V if c2 == ck and a2 != an)
    body = f"""<section class="pg-hero"><div class="wrap">
  <p class="eyebrow"><a href="/city/{cslug(*ck)}">{E(c)}</a> · Neighbourhood guide</p>
  <h1>{E(an)}: <em>where foodies eat</em></h1>
  <p class="lede">The {len(vs)} places in {E(an)} that Dream Menu guests name most. What they name here: {known}.</p>
  <div class="pg-facts"><div><b>{len(vs)}</b><span>venues named</span></div><div><b>{100 * tot / ctot:.1f}%</b><span>of {E(c)} mentions</span></div><div><b>{sum(1 for v in vs if v["i"] in AW)}</b><span>hold a guide award</span></div></div>
  <p class="pg-mut">Areas follow postcode districts, so edges are approximate, and only venues with a confirmed address are counted.</p>
</div></section>
{('<section><div class="wrap"><h2 class="pg-h2">The ' + E(an) + ' dream menu</h2><div class="ct-menu">' + ''.join(picks) + '</div></div></section>') if len(picks) >= 2 else ''}
<section><div class="wrap pg-grid">
  <div class="card ct-wide"><h2>Most named in {E(an)}</h2>{_vi(f'Each bar is a venue’s share of all venue mentions in {an}. It measures how often a place comes to mind, not how good it is.')}{bars([(vlink(v) + (' <span class="mk-tag">Award</span>' if v['i'] in AW else ''), v['m']) for v in vs[:12]], fmtv=pc)}</div>
  {('<div class="card"><h2>Hidden gems and next stops</h2><ol class="pg-list">' + ''.join(f'<li>{vlink(v)} <span class="pg-mut">{E((v.get("k") or [[""]])[0][0])}</span></li>' for v in gems) + '</ol></div>') if gems else ''}
  <div class="card"><h2>More of {E(c)}</h2><div class="pg-chips">{others}</div><p style="margin-top:12px"><a class="go" href="/city/{cslug(*ck)}">The full {E(c)} guide</a> · <a class="go" href="/map">Map</a></p></div>
</div>{SRC}</section>"""
    return page(f'/area/{aslug(c, an)}', f'{an}, {c}: where foodies eat | Dream Menu',
                f'The {len(vs)} restaurants, bars and cafes in {an}, {c} that Dream Menu guests name most, with the area’s dream menu and hidden gems.', body,
                {'@context': 'https://schema.org', '@type': 'ItemList', 'name': f'Where foodies eat in {an}, {c}',
                 'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': v['n']} for i, v in enumerate(vs[:12], 1)]})


cwritten = [city_page(*k) for k in CITIES]
cwritten += [area_page(ck, an) for (ck, an) in AREA_V]
for fn in glob.glob('area/*.html'):
    if fn not in cwritten:
        os.remove(fn)
for fn in glob.glob('city/*.html'):
    if fn not in cwritten:
        os.remove(fn)
_cards = ''.join(
    f'<a class="ct-card" href="/city/{cslug(*k)}"><b>{E(k[0])}</b><span>{E(k[1] if k[1] != "United Kingdom" else (_cm[k].get("na") or ""))}</span>'
    f'<em>{fmt(len([v for v in _bc[k] if v.get("y") != "area"]))} venues · {fmt(_cm[k]["g"])} guests</em>'
    f'<small>{E(_bc[k][0]["n"])} leads</small>{"" if _cm[k]["g"] >= DEEP_G else "<i>Early signal</i>"}</a>' for k in CITIES)
cwritten.append(page('/cities', 'City guides: where foodies eat, city by city | Dream Menu',
    f'{len(CITIES)} city guides built from Dream Menu interviews: the venues food-led guests name most, hidden gems and what sets each city apart.',
    f'''<section class="pg-hero"><div class="wrap"><p class="eyebrow">Where to eat</p><h1>City guides, <em>by the people who eat there</em></h1>
<p class="lede">No critics and no paid placements. Each guide is built from the venues guests name when asked for their dream menu. Cities appear once guests have named at least {CITY_MIN_V} places there.</p></div></section>
<section><div class="wrap"><div class="ct-grid">{_cards}</div>
<p class="pg-mut">Your city missing or thin? <a href="/take-part">Add your dream menu</a>, or explore every venue on the <a href="/map">map</a>.</p>{SRC}</div></section>''',
    {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Dream Menu city guides', 'url': f'{SITE}/cities'}))
written += cwritten
_css = open('pages.css', encoding='utf-8').read()
_blk = """/* city */
.ct-menu{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:0 22px}
.ct-menu article{border-top:1px solid var(--ink);padding:12px 0 14px;position:relative}
.ct-menu article::before{content:"";position:absolute;top:-1px;left:0;width:40px;height:5px;background:var(--gold)}
.ct-menu span{font:800 11px/1 var(--display);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.ct-menu h3{font-size:19px;line-height:1.2;margin:8px 0 4px}.ct-menu p{margin:0;font-size:14.5px}.ct-menu small{color:var(--muted);font-size:12.5px}
.ct-wide{grid-column:1/-1}.ct-wide .pg-bars li{grid-template-columns:minmax(0,1fr) 38% 52px}
.pg-early{border-left:3px solid var(--gold);padding:2px 0 2px 12px;font-size:14.5px;max-width:720px}
.ct-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:0 22px;margin-bottom:18px}
.ct-card{display:grid;gap:3px;border-top:1px solid var(--ink);padding:12px 0 16px;text-decoration:none;color:var(--ink);position:relative}
.ct-card b{font:700 21px/1.15 var(--display)}.ct-card span,.ct-card em,.ct-card small{font-style:normal;font-size:13.5px;color:var(--muted)}
.ct-card i{font-style:normal;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.ct-card:hover b{text-decoration:underline}
/* /city */
"""
open('pages.css', 'w', encoding='utf-8').write(re.sub(r'/\* city \*/.*?/\* /city \*/\n', '', _css, flags=re.S) + _blk)

# ---------------------------------------------------------------- interactive tools: /menu-check and /my-dream-menu
# Public data only: each tracked dish's overall share of its course, the steady staples, and the city index.
def _jsload(fn):
    t = open(fn, encoding='utf-8').read()
    return json.JSONDecoder().raw_decode(t[t.index('{'):])[0]


_TPUB, _AD = _jsload('trend-public.js'), _jsload('analysis-data.js')
_stap = {(x['course'], x['l']) for x in _TPUB['staples']}
_crow = {r['l']: [c['idx'] if not c['thin'] else None for c in r['cells']] for r in _AD['cities']['rows']}
PICK = dict(n=P['n_all'], last=P['last'], markets=_AD['cities']['markets'], courses=[
    dict(k=k, label=P['trends'][k]['label'], base=P['trends'][k]['n'],
         items=[dict(s=slugify(it.get('l') or lab(it['c'])), l=it.get('l') or lab(it['c']), g=it.get('g') or grp(it['c']), p=it['pct'],
                     st=1 if (k, it.get('l') or lab(it['c'])) in _stap else 0, ci=_crow.get(it.get('l') or lab(it['c'])))
                for it in P['trends'][k]['cats'] if (it.get('l') or lab(it['c'])) != 'Other'])
    for k in P['order']])
open('pick-data.js', 'w', encoding='utf-8').write('/* Generated by tools/build_venue_pages.py for /menu-check and /my-dream-menu. Public shares only. */\nwindow.DM_PICK='
                                                  + json.dumps(PICK, ensure_ascii=False, separators=(',', ':')) + ';\n')
_TS = '<script src="/pick-data.js"></script>\n<script src="/tools.js" defer></script>'
written.append(page('/menu-check', 'Check my menu against what guests want | Dream Menu',
    f'A free tool for venues: tick the dishes on your menu and see how much of what {fmt(P["n_all"])} food-led guests ask for you already cover, which staples are missing and where the gaps are.',
    f'''<section class="pg-hero"><div class="wrap"><p class="eyebrow">For venues · Free tool</p><h1>Check my menu <em>against what guests want</em></h1>
<p class="lede">Tick what is on your menu. You will see how much of what guests name for each course you already cover, which steady staples are missing, and the biggest gaps. Nothing you tick leaves your browser.</p></div></section>
<section><div class="wrap"><div id="mc" class="tl" data-tool="check"><noscript>This tool needs JavaScript.</noscript></div>{SRC}</div></section>
{_TS}'''))
written.append(page('/my-dream-menu', 'Build your dream menu and see who agrees | Dream Menu',
    f'Pick your dream starter, main, side, dessert and drinks, then see what share of {fmt(P["n_all"])} guests chose the same, which city you eat like, and share your menu.',
    f'''<section class="pg-hero"><div class="wrap"><p class="eyebrow">Food trends · Play</p><h1>Build your <em>dream menu</em></h1>
<p class="lede">Six choices, no wrong answers. Pick one for each course and see how your taste compares with {fmt(P["n_all"])} guests who have answered the same question.</p></div></section>
<section><div class="wrap"><div id="dm" class="tl" data-tool="dream"><noscript>This tool needs JavaScript.</noscript></div>{SRC}</div></section>
{_TS}'''))
_css = open('pages.css', encoding='utf-8').read()
_blk = """/* tools */
.tl{margin:26px 0 18px}
.tl-grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(300px,1fr);gap:34px;align-items:start}
@media (max-width:900px){.tl-grid{grid-template-columns:1fr}}
.tl-course{border-top:1px solid var(--ink);padding:12px 0 18px;position:relative}
.tl-course::before{content:"";position:absolute;top:-1px;left:0;width:40px;height:5px;background:var(--gold)}
.tl-course h2{font-size:19px;margin:6px 0 2px}.tl-course p{margin:0 0 10px;font-size:13.5px;color:var(--muted)}
.tl-opts{display:flex;flex-wrap:wrap;gap:8px}
.tl-opt{font:500 14.5px/1.2 var(--body);border:1.5px solid var(--rule-strong);background:var(--card);color:var(--ink);border-radius:4px;padding:9px 12px;cursor:pointer;display:inline-flex;gap:8px;align-items:baseline}
.tl-opt small{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
.tl-opt:hover{border-color:var(--ink)}
.tl-opt[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}.tl-opt[aria-pressed="true"] small{color:inherit;opacity:.7}
.tl-opt:focus-visible{outline:2px solid var(--navy);outline-offset:2px}
.tl-out{position:sticky;top:calc(var(--hh,62px) + 14px);border-top:1px solid var(--ink);padding-top:14px}
.tl-out h2{font-size:22px;line-height:1.2;margin:4px 0 6px}.tl-out h3{font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:18px 0 6px}
.tl-big{font:800 54px/1 var(--display);margin:6px 0 2px}.tl-big small{font-size:18px;color:var(--muted);font-weight:600}
.tl-rows{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:7px}
.tl-rows li{display:grid;grid-template-columns:78px minmax(0,1fr) 48px;gap:10px;align-items:center;font-size:14px}
.tl-rows .t{height:9px;background:var(--rule);overflow:hidden}.tl-rows .t i{display:block;height:100%;background:var(--navy)}
.tl-rows .v{text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
.tl-list{margin:0;padding-left:18px;font-size:14.5px;display:grid;gap:4px}
.tl-mut{color:var(--muted);font-size:13.5px}
.tl-acts{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.tl-btn{font:700 14px/1 var(--body);border:1.5px solid var(--ink);background:var(--ink);color:var(--paper);border-radius:99px;padding:11px 16px;cursor:pointer;text-decoration:none}
.tl-btn.alt{background:none;color:var(--ink)}
.tl-lock{border-left:3px solid var(--gold);padding:2px 0 2px 12px;font-size:14px;margin-top:14px}
.tl-picks{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:0}
.tl-picks li{display:grid;grid-template-columns:86px minmax(0,1fr) auto;gap:10px;padding:9px 0;border-bottom:1px solid var(--rule);font-size:15px;align-items:baseline}
.tl-picks span{font:800 11px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}.tl-picks b{font-weight:600}.tl-picks em{font-style:normal;font-variant-numeric:tabular-nums;color:var(--muted);font-size:13.5px}
/* /tools */
"""
open('pages.css', 'w', encoding='utf-8').write(re.sub(r'/\* tools \*/.*?/\* /tools \*/\n', '', _css, flags=re.S) + _blk)

# ---------------------------------------------------------------- sitemap
sm = open('sitemap.xml', encoding='utf-8').read()
sm = re.sub(r'\s*<url><loc>https://www\.dream-menu\.com/(?:venue|trends|badge|city|cities|area|menu-check|my-dream-menu)[^<]*</loc>[^\n]*</url>', '', sm)
add = ''.join(f'\n  <url><loc>{SITE}/{fn[:-5]}</loc><lastmod>{P["last"]}</lastmod></url>' for fn in sorted(written))
sm = sm.replace('\n</urlset>', add + '\n</urlset>')
open('sitemap.xml', 'w', encoding='utf-8').write(sm)
print(f'wrote {len(written)} pages: {len(PUBLIC_V)} venues, {len(DISHES)} dishes, trends index, badge')
