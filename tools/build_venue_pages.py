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
                mk.append((name, c, 100 * (c / MK_TOT[name]) / wsh))
    mk_rows = ''.join(
        f'<tr><td>{E(n)}</td><td class="num">{c}</td><td class="num">{"×%.1f" % (x / 100) if c >= 3 else "–"}</td></tr>' for n, c, x in mk)
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
  <div class="card"><h2>By market</h2>{('<div class="tablewrap" style="border:0"><table><thead><tr><th>Market</th><th class="num">Mentions</th><th class="num">Index</th></tr></thead><tbody>' + mk_rows + '</tbody></table></div><p class="pg-mut">Mentions at venues in each market. ×1.5 = named one and a half times as often as across all markets; shown from three mentions. Markets outside Scotland are early signals.</p>') if mk_rows else '<p class="pg-mut">Not enough venue mentions to compare markets yet.</p>'}</div>
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

# ---------------------------------------------------------------- sitemap
sm = open('sitemap.xml', encoding='utf-8').read()
sm = re.sub(r'\s*<url><loc>https://www\.dream-menu\.com/(?:venue|trends|badge)[^<]*</loc>[^\n]*</url>', '', sm)
add = ''.join(f'\n  <url><loc>{SITE}/{fn[:-5]}</loc><lastmod>{P["last"]}</lastmod></url>' for fn in sorted(written))
sm = sm.replace('\n</urlset>', add + '\n</urlset>')
open('sitemap.xml', 'w', encoding='utf-8').write(sm)
print(f'wrote {len(written)} pages: {len(PUBLIC_V)} venues, {len(DISHES)} dishes, trends index, badge')
