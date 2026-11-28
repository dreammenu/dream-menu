#!/usr/bin/env python3
"""Where to sell it: Scottish venues guests name for dishes that are rising, by supplier range (partners only).

The account finder the trade intelligence firms charge most for, built from data Dream Menu already holds:
which venues guests name (dm-data.js), for which dishes (dm-cat.js, dm-labels.js), and which of those dishes
are worth backing (partner/dish-moves.js: Back / Watch / Review tiers and trend scores; partner/category-data.js:
food groups with a Grow call). Ranges come from tools/ranges.py. Cost flags and the market watch board come from
tools/data/market-watch.json (outside sources, kept beside Dream Menu figures, never mixed in).

Writes partner/sell-data.js (window.DM_SELL, behind sign-in). partner/sell.js draws it twice:
  /analysis "Where to sell it" chapter (top venues per range) and the market watch board in the partner briefing,
  /partner/accounts  the full rep sheet: filter by range and market, mark your own customers, print.

Run after build_venue_pages.py (it writes partner/dish-moves.js) and build_pages.py (partner/category-data.js):
  python3 tools/build_accounts.py
"""
import datetime as dt, json, os, re, unicodedata
from ranges import RANGES, RANGE_OF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


def slugify(s):
    s = re.sub(r'[̀-ͯ]', '', unicodedata.normalize('NFKD', str(s)).lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


D, C, L = load('dm-data.js', 'DM'), load('dm-cat.js', 'DMC'), load('dm-labels.js', 'DML')
MV = load('partner/dish-moves.js', 'DM_DISHMOVES')
CATS = load('partner/category-data.js', 'DM_CATS')
P = load('partner-data.js', 'DM_PARTNER')
W = json.load(open('tools/data/market-watch.json', encoding='utf-8'))
ST = json.load(open('tools/data/venue-status.json', encoding='utf-8')) if os.path.exists('tools/data/venue-status.json') else None
OA = load('other-awards.js', 'DM_OA')['v']
MIN_M = D['meta']['thresholds'].get('min_public_mentions', 2)

# weights: a Back dish counts in full, a Watch dish half, a dish in a Grow food group (not itself scored) a third,
# each scaled by its trend score where it has one. Review dishes are listed as "watch out", not scored.
WT = {'Back': 1.0, 'Watch': 0.5}
GROW = {r['l'] for r in CATS['rows'] if r['call'] == 'Grow'}
FALL = {r['l'] for r in CATS['rows'] if r['call'] in ('Trim', 'Defend')}


def best(slug):
    """The strongest course entry for a dish: Back before Watch before Review, then score."""
    es = [e for e in MV['d'].get(slug) or [] if e.get('tier')]
    order = {'Back': 0, 'Watch': 1, 'Review': 2}
    return sorted(es, key=lambda e: (order[e['tier']], -e['score']))[0] if es else None


def market(v):
    if v['c'] == 'Glasgow':
        return 'Glasgow'
    if v['c'] == 'Edinburgh':
        return 'Edinburgh'
    return 'Rest of Scotland'


rows = []
for n, v in enumerate(D['venues']):
    if v.get('na') != 'Scotland' or (v.get('m') or 0) < MIN_M or not v.get('c') or v.get('y') == 'area':
        continue
    sell, risk = {}, []
    for ci, k in C['v'].get(str(n)) or []:
        ent = L.get(C['c'][ci]) or [C['c'][ci]]
        lab, grp = ent[0], (ent[1] if len(ent) > 1 else '')
        rng = RANGE_OF.get(grp)
        if not rng:
            continue
        slug = slugify(lab)
        e = best(slug)
        if e and e['tier'] in WT:
            w = WT[e['tier']] * e['score'] / 10
            sig = dict(d=lab, s=slug, k=k, t=e['tier'], sc=e['score'], mv=e['move'], cl=bool(e['sig']), co=e['course'])
        elif grp in GROW and not (e and e['tier'] == 'Review'):
            w = 0.33 * 0.6
            sig = dict(d=lab, s=slug if slug in MV['d'] else '', k=k, t='Grow', g=grp)
        else:
            if (e and e['tier'] == 'Review' and e['sig'] and e['move'] < 0) or (grp in FALL and not e):
                risk.append(dict(d=lab, k=k, mv=e['move'] if e else None, g=grp, r=rng))
            continue
        b = sell.setdefault(rng, dict(x=0.0, s=[]))
        b['x'] += k * w
        b['s'].append(sig)
    if not sell:
        continue
    for b in sell.values():
        b['x'] = round(b['x'], 2)
        b['s'].sort(key=lambda s: (-(s['k'] * (WT.get(s['t'], 0.2) * (s.get('sc') or 6) / 10)), s['d']))
    aw = D['aw'].get(v['i'])
    o = (ST or {}).get('v', {}).get(v['i']) or {}
    lic = o.get('lic') or {}
    st = {k: x for k, x in dict(s=o.get('s'), r=o.get('r'), d=o.get('d'), cap=lic.get('cap'), lg=lic.get('g'), ch=lic.get('ch')).items() if x}
    rows.append(dict(n=v['n'], p=re.sub(r'-x$', '', v['i']), mk=market(v), c=v.get('tw') or v['c'], ad=v.get('ad') or '',
                     m=v['m'], g=v.get('g') or v['m'], aw=(aw['a'][0] if aw and aw.get('a') else (OA[v['i']][0][0] if OA.get(v['i']) else '')), st=st, ch=v.get('y') == 'chain',
                     r=sell, w=sorted(risk, key=lambda r: -r['k'])[:2]))
rows.sort(key=lambda r: -sum(b['x'] for b in r['r'].values()))

# ---------------------------------------------------------------- market watch: outside finding, Dream Menu reading, what to do
TR = P['trends']
gp = lambda k, l: next(g for g in TR[k]['groups'] if g['c'] == l)
sc_v = [v for v in D['venues'] if v.get('na') == 'Scotland']
sc_m = sum(v.get('m') or 0 for v in sc_v) or 1
city_m = sum(v.get('m') or 0 for v in sc_v if v['c'] in ('Glasgow', 'Edinburgh'))
AU = load('menu-audit-public.js', 'DM_AUDIT')
main_p = next((x for x in AU.get('prices') or [] if x['course'] == 'Main'), None)
DR = load('drinks-new.js', 'DM_DRINKS')
nolo = re.search(r'([\d.]+)% answer the alcoholic drink question with something alcohol-free', ' '.join(DR.get('find') or []))
binned = dict(P['extra']['bin']).get('Small plates', 0)
aw_n = sum(1 for r in rows if r['aw'])
vs, fm, ck, bc = gp('d', 'Vegetables and salad'), gp('p', 'Fruit and meringue'), gp('a', 'Cocktails'), gp('a', 'Beer and cider')
sea_s, sea_m, pot = gp('s', 'Seafood'), gp('m', 'Seafood'), gp('d', 'Potatoes and fries')
pc = lambda x: f'{x:.1f}%'
DMR = {
    'churn': (f"Guests name {sum(1 for v in sc_v if (v.get('m') or 0) >= MIN_M):,} Scottish venues two or more times; {len(rows)} are named for dishes worth backing and make up the rep sheet."
              + (f" On the food hygiene register, {ST['n_new']} named venues registered in the last year and {ST['n_check']} of the {ST['n_exact']} with a full address could not be found: some have closed, others trade under another name. "
                 f"{len(ST['leads'])} restaurants, cafés and bars in Glasgow and Edinburgh registered in the last 12 months and are not yet inspected." if ST else '')),
    'cities': f"Glasgow and Edinburgh hold {100 * city_m / sc_m:.0f}% of Scottish venue mentions: the two places Dream Menu can read in depth.",
    'costs': f"Seafood is {pc(sea_s['pct'])} of dream starters and {pc(sea_m['pct'])} of mains; potatoes and fries are {pc(pot['pct'])} of sides.",
    'value': (f"The median main on the menus of the {AU['n']} most-named venues is £{main_p['median']:.2f} (middle half £{main_p['lo']:.2f} to £{main_p['hi']:.2f})."
              if main_p else 'The menu audit has too few priced mains to compare yet.'),
    'lighter': f"Vegetable and salad sides moved from {pc(vs['early'])} to {pc(vs['late'])} of answers and fruit desserts from {pc(fm['early'])} to {pc(fm['late'])}; {100 * binned / P.get('n_sheet', P['n_all']):.1f}% of guests want small plates binned.",
    'drinks': (f"On the original drinks question, cocktails fell from {pc(ck['early'])} to {pc(ck['late'])} of alcoholic picks{', a clear move' if ck['sig'] else ''}; beer and cider rose from {pc(bc['early'])} to {pc(bc['late'])}."
               + (f" {nolo.group(1)}% now answer the alcoholic drink question with something alcohol-free." if nolo else '')),
}
watch = [dict(w, dm=DMR[w['id']]) for w in W['watch']]

out = dict(built=dt.date.today().isoformat(), last=P['last'], n=P['n_all'], outside=W['updated'],
           ranges=[dict(r=r, cost=sorted({f"{g}: {W['cost'][g]['level'].lower()}" for g in gs if g in W['cost']})) for r, gs in RANGES],
           cost=W['cost'], watch=watch, v=rows,
           status=(dict(extract=ST['extract'], lic=ST.get('lic'), n_new=ST['n_new'], n_check=ST['n_check'], ir_named=ST['ir_named'], ir_all=ST['ir_all']) if ST else None),
           leads=(ST['leads'] if ST else []),
           how=('A venue\'s score in a range adds up the times guests name it for dishes in that range, '
                'weighted by each dish\'s call: Back counts in full and Watch half, scaled by the trend score; a dish in a food group to grow counts a fifth. '
                'It shows proven demand at the venue, not who supplies it today.'))
open('partner/sell-data.js', 'w', encoding='utf-8').write(
    '/* Generated by tools/build_accounts.py. Partner only (behind sign-in). */\nwindow.DM_SELL='
    + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
by_mk = {m: sum(1 for r in rows if r['mk'] == m) for m in ('Glasgow', 'Edinburgh', 'Rest of Scotland')}
print('partner/sell-data.js:', len(rows), 'venues', by_mk, '| watch', len(watch), '| top', [r['n'] for r in rows[:5]])

# ---------------------------------------------------------------- /partner/accounts: the full rep sheet (behind sign-in)
import html as _html
E_ = lambda x: _html.escape(str(x), quote=True)
TPL = open('restaurant-mot.html', encoding='utf-8').read()
HEAD, FOOT = TPL[:TPL.find('<main>')], TPL[TPL.find('</main>') + len('</main>'):]
T = 'Rep sheet: venues to call | Dream Menu'
DESC = 'Partner rep sheet: Scottish venues guests name for rising dishes, by supplier range.'
h = re.sub(r'<title>[^<]*</title>', f'<title>{E_(T)}</title>', HEAD).replace(' aria-current="true"', '')
for prop in ('name="description"', 'property="og:description"'):
    h = re.sub(r'(<meta ' + prop + r' content=")[^"]*', lambda m: m.group(1) + E_(DESC), h)
h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E_(T), h)
h = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + 'https://www.dream-menu.com/partner/accounts', h)
h = h.replace('<link rel="stylesheet" href="/brand.css">', '<link rel="stylesheet" href="/brand.css">\n<link rel="stylesheet" href="/pages.css">\n<link rel="stylesheet" href="/dmviz.css">', 1)
h = h.replace('</head>', '<meta name="robots" content="noindex, nofollow">\n</head>', 1)
LAST_H = dt.date.fromisoformat(P['last']).strftime('%-d %B %Y')
BODY = f'''<main class="pg">
<section class="pg-hero"><div class="wrap">
<p class="eyebrow">Partners · Where to sell it</p>
<h1>Venues to call, range by range</h1>
<p class="lede">Every Scottish venue guests have named at least twice, scored for each supplier range by the dishes guests name there and whether those dishes are worth backing. Lead with the first dish; check the &ldquo;watch out&rdquo; column before you go.</p>
<p class="acct-noprint"><button class="cta" type="button" onclick="window.print()">Print this list</button> <a class="go" href="/analysis/partner#sell-sec">Back to the briefing</a></p>
</div></section>
<section><div class="wrap">
<p class="pg-src" id="acct-print-h"></p>
<div id="acct-sheet"></div>
<div class="acct-noprint">
<h2 id="new-openings">New openings to call</h2>
<div id="acct-leads"></div>
<h2>How to use it</h2>
<ul>
<li><b>Pick a range and a market</b>, then work down the list. The first dish in each row is the one to open with; &ldquo;also&rdquo; lists the next two.</li>
<li><b>Tick the venues that already buy from you.</b> &ldquo;Not yet ours&rdquo; then shows the prospects. The ticks stay in this browser only; nothing is sent to Dream Menu.</li>
<li><b>Read it as proven demand at the venue</b>, not as who supplies it today. A venue named for scallops sells scallops guests remember; whether it buys them from you is your list, not ours.</li>
<li><b>Check the status line</b> under each venue: the latest food hygiene result, &ldquo;new&rdquo; for a venue registered in the last year, a licence that changed hands, and for Glasgow the licensed capacity, a rough guide to account size. &ldquo;Not found on the hygiene register&rdquo; usually means closed or renamed, but sometimes a venue is registered under a company or sister name, so check before you strike it off.</li>
<li><b>Mind the cost watch</b> line above the table: where input costs are rising, pitch the spec that protects the operator&rsquo;s margin.</li>
</ul>
<p class="pg-src">Source: Dream Menu, {P["n_all"]:,} interviews to {LAST_H}; {len(rows)} Scottish venues. Calls (Back, Watch, Grow) come from the partner briefing and are rechecked at every Monday refresh. Status: Food Standards Agency food hygiene register and Glasgow City Council licensed premises data, both Open Government Licence; venues are matched by postcode and name, and any match we were not sure of is left blank. Partner only: please do not share outside your organisation.</p>
</div>
</div></section>
</main>'''
open('partner/accounts.html', 'w', encoding='utf-8').write(h + BODY + FOOT.replace('</body>', '<script src="/dmviz.js"></script><script src="/partner/sell-data.js"></script><script src="/partner/sell.js"></script>\n</body>', 1))
print('partner/accounts.html written')
