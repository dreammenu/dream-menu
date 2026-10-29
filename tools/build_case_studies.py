#!/usr/bin/env python3
"""Builds the Dream Menu Insight Series: /case-studies and /case-studies/<slug>.

Run from the repository root after a data refresh:
  python3 tools/build_case_studies.py && python3 tools/build_nav.py

Every figure is read from the live data files (partner-data.js, analysis-data.js, dm-data.js,
awards.js, tools/data/static-counts.json, tools/data/look-ahead-2026-scores.json), so the reports
follow each refresh. Report 01 is Gordon's drafted night-out briefing (28 Oct 2026); its market
benchmarks are fixed published figures with sources. Charts and layout come from tools/cs_kit.py,
case.css and case.js; the page shell (head, header, footer) is copied from restaurant-mot.html.
"""
import datetime as dt, json, math, os, re, sys
from collections import Counter, defaultdict
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from cs_kit import (Ex, esc, num, pts, hbar, dumbbell, diverge, stack, cols, heat, matrix, small_multiples,
                    strip, waterfall, glasgow_map, sowhat, pull, quotes, table,
                    project, fan_multiples, lanes, roadmap, ledger, scenarios, forces)

CONTACT = 'contact.dreammenu@gmail.com'


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
AN = load('analysis-data.js', 'DM_ANALYSIS')
DM = load('dm-data.js', 'DM')
AW = load('awards.js', 'DM_AWARDS')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
LOOK = json.load(open('tools/data/look-ahead-2026-scores.json', encoding='utf-8'))['rows']
MK = {m['n']: m for m in DM['markets']}
VEN = {v['i']: v for v in DM['venues']}
LAST = dt.date.fromisoformat(P['last'])
LAST_H = f'{LAST.day} {LAST:%B %Y}'
TODAY = dt.date.today()
TODAY_H = f'{TODAY.day} {TODAY:%B %Y}'
N_ALL = P['n_all']
f0 = lambda x: f'{x:,.0f}'
f1 = lambda x: f'{x:.1f}'
pc = lambda a, b: round(100 * a / b) if b else 0
DM_SRC = f'Dream Menu interviews, {f0(N_ALL)} to {LAST_H}'
EARLY, RECENT = 'Jul to Dec 2025', 'Apr 2026 onward'


def trend(c):
    return P['trends'][c]


def item(c, name, level='cats'):
    for it in trend(c)[level]:
        if it.get('l') == name or it['c'] == name:
            return it
    raise KeyError(f'{c}: {name}')


def sig_set(c):
    t = trend(c)
    return {it.get('l') or it['c'] for it in t['groups'] + t['cats'] if it['sig']}


def qlab(q):
    y, n = q.split('-Q')
    return f'Q{n} {y[2:]}'


def faded(c):
    return {i for i, lo in enumerate(trend(c)['low']) if lo}


def city_row(label):
    for r in AN['cities']['rows']:
        if r['l'] == label:
            return r
    raise KeyError(label)


def vname(i):
    return VEN[i]['n']


def vloc(v):
    return v.get('c') or v.get('tw') or ''


def cat_count(v, cat):
    return dict(v.get('k', [])).get(cat, 0)


def link(h, t):
    return f'<a href="{esc(h)}" rel="noopener" target="_blank">{esc(t)}</a>'


def nice(a):
    """'Debt / cashflow / financing' -> 'Debt, cashflow and financing'."""
    parts = [x.strip() for x in a.replace('(', '').replace(')', '').split('/') if x.strip()]
    if len(parts) < 2:
        return a
    return ', '.join(parts[:-1]) + ' and ' + parts[-1]


# ------------------------------------------------------------------ page shell
TPL = open('restaurant-mot.html', encoding='utf-8').read()
HEAD, FOOT = TPL[:TPL.find('<main>')], TPL[TPL.find('</main>') + len('</main>'):]
HEAD = HEAD.replace('<link rel="stylesheet" href="/brand.css">', '<link rel="stylesheet" href="/brand.css">\n<link rel="stylesheet" href="/case.css"><script src="/case.js" defer></script>')


def shell(path, title, desc):
    h = HEAD
    h = re.sub(r'<title>[^<]*</title>', f'<title>{esc(title)} | Dream Menu</title>', h)
    h = re.sub(r'(<meta name="description" content=")[^"]*', rf'\g<1>{esc(desc)}', h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', rf'\g<1>{esc(desc)}', h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', rf'\g<1>{esc(title)} | Dream Menu', h)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*', rf'\g<1>https://www.dream-menu.com{path}', h)
    return h


def write(path, title, desc, body):
    fn = path.strip('/') + '.html'
    os.makedirs(os.path.dirname(fn) or '.', exist_ok=True)
    open(fn, 'w', encoding='utf-8').write(shell(path, title, desc) + '<main>\n' + body + '\n</main>' + FOOT)
    return fn


AUD = {'supplier': 'Suppliers and brands', 'venue': 'Operators', 'investor': 'Investors and property', 'public': 'Public sector, tourism and press', 'forecast': 'Trends and forecasts'}
ORDER = ['night-out', 'glasgow-edinburgh', 'seafood', 'dessert', 'drinks', 'trend-fatigue',
         'neighbourhoods', 'guests-and-critics', 'steak', 'italian', 'operator-confidence',
         'glasgow-2030', 'edinburgh-2030', 'ten-forces', 'edge-of-the-menu']
META = {
    'night-out': dict(no=1, kind='Price and cost briefing', plain='The cost of a night out in Glasgow'),
    'glasgow-edinburgh': dict(no=2, kind='Market-entry read', plain='Two cities, two appetites'),
    'seafood': dict(no=3, kind='Category deep-dive', plain="Scotland's seafood appetite"),
    'dessert': dict(no=4, kind='Category deep-dive', plain='The last spend: dessert'),
    'drinks': dict(no=5, kind='Category deep-dive', plain='What Scotland drinks with dinner'),
    'trend-fatigue': dict(no=6, kind='Trend tracker', plain='Trend fatigue'),
    'neighbourhoods': dict(no=7, kind='Location read', plain='Where Glasgow eats'),
    'guests-and-critics': dict(no=8, kind='Reputation study', plain='Guests and critics'),
    'steak': dict(no=9, kind='Category deep-dive', plain='The steak economy'),
    'italian': dict(no=10, kind='Cuisine deep-dive', plain="Glasgow's Italian table"),
    'operator-confidence': dict(no=11, kind='Sector pulse', plain='The confidence gap'),
    'glasgow-2030': dict(no=12, kind='City forecast', plain='Glasgow to 2030'),
    'edinburgh-2030': dict(no=13, kind='City forecast, directional', plain='Edinburgh and Scotland to 2030'),
    'ten-forces': dict(no=14, kind='Long-term forces', plain='Ten forces to 2031'),
    'edge-of-the-menu': dict(no=15, kind='Niche watchlist', plain='The edge of the menu'),
}
REPORTS = []


def render(r):
    strip_txt = {
        'draft': '<b>Draft briefing.</b> Written by Dream Menu for a named partner. Market figures are published benchmarks; venue prices are modelled. <a href="/case-studies">All reports</a>',
        'sample': f'<b>Provisional sample.</b> Real figures from live Dream Menu data to {LAST_H}, written to an illustrative brief to show the work Dream Menu does on request. Not yet reviewed with a client. <a href="/case-studies">All reports</a>',
    }[r['status']]
    status_lbl = 'Draft briefing' if r['status'] == 'draft' else 'Provisional sample'
    kp = ''.join(f'<div class="cs-kpi"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in r['kpis'])
    subj = ('Commission%20a%20report%20like%20' + esc(r['plain']).replace(' ', '%20'))
    cover = f'''<div class="cs-strip"><div class="wrap">{strip_txt}</div></div>
<section class="cs-cover"><div class="wrap">
  <div class="cs-series"><span class="no">No. {r["no"]:02d}</span><span>Dream Menu Insight Series · {esc(r["kind"])}</span></div>
  <h1>{r["title"]}</h1>
  <p class="cs-stand">{r["stand"]}</p>
  <dl class="cs-meta"><div><dt>Written for</dt><dd>{esc(r["client"])}</dd></div><div><dt>The question</dt><dd>{esc(r["question"])}</dd></div>
  <div><dt>Status</dt><dd>{status_lbl}, {esc(r.get("dated", TODAY_H))}</dd></div><div><dt>Evidence</dt><dd>{esc(r["evidence"])}</dd></div></dl>
  <div class="cs-kpis">{kp}</div>
  <div class="cs-actions"><button class="cs-btn" type="button" data-print>Save as PDF</button><a class="cs-btn" href="mailto:{CONTACT}?subject={subj}">Commission a report like this</a></div>
</div></section>'''
    secs = [('summary', 'Executive summary')] + [(c[0], c[1]) for c in r['chapters']] + [('recommendations', 'What to do'), ('watch', 'What to watch'), ('method', 'Method and sources')]
    toc = '<nav class="cs-toc" aria-label="Contents"><b>Contents</b><ol>' + ''.join(f'<li><a href="#{i}"><span>{n + 1:02d}</span>{esc(t)}</a></li>' for n, (i, t) in enumerate(secs)) + '</ol></nav>'
    msgs = ''.join(f'<li><span class="n">{esc(n)}<small>{esc(u)}</small></span><h3>{h}</h3><p>{t}</p></li>' for n, u, h, t in r['msgs'])
    todo = ''.join(f'<li data-n="{i + 1}">{esc(rc[0])}</li>' for i, rc in enumerate(r['recs']))
    summ = f'''<section id="summary"><p class="cs-kicker">01 · Executive summary</p><h2>The answer</h2>
<div class="cs-answer"><small>In one sentence</small><p>{r["answer"]}</p></div>
<ul class="cs-msgs">{msgs}</ul>
<h3 style="margin:26px 0 4px;font-size:17px">What we recommend</h3><ol class="cs-todo">{todo}</ol></section>'''
    chap = ''
    for k, (cid, kick, h2, lede, body) in enumerate(r['chapters']):
        chap += f'<section id="{cid}"><p class="cs-kicker">{k + 2:02d} · {esc(kick)}</p><h2>{h2}</h2><p class="cs-lede">{lede}</p>{body}</section>'
    n0 = len(r['chapters']) + 2
    imp = {'High': .85, 'Medium': .55, 'Low': .25}
    eff = {'Low': .14, 'Medium': .56, 'High': .9}
    short = lambda t: t
    mx = matrix([(i + 1, short(rc[0]), imp[rc[2]], eff[rc[3]]) for i, rc in enumerate(r['recs'])])
    mx_fig = r['ex']('Where to start: impact against effort', 'Each recommendation placed by expected impact for the client and the effort to deliver it.', mx, 'Dream Menu assessment of the recommendations in this report')
    recl = ''.join(f'<li><span class="rn">{i + 1:02d}</span><div><h3>{esc(rc[0])}</h3><p>{rc[1]}</p><div class="tags"><span class="tg{" hi" if rc[2] == "High" else ""}">Impact: {rc[2]}</span><span class="tg">Effort: {rc[3]}</span><span class="tg">{esc(rc[4])}</span></div></div></li>' for i, rc in enumerate(r['recs']))
    recs = f'<section id="recommendations"><p class="cs-kicker">{n0:02d} · Recommendations</p><h2>What to do</h2><p class="cs-lede">{r.get("recs_lede", "Ranked by impact. The matrix shows where to start; the list says why.")}</p>{mx_fig}<ol class="recs">{recl}</ol></section>'
    watch = ''.join(f'<div><h4>{esc(h)}</h4><p>{t}</p></div>' for h, t in r['watch'])
    watch = f'<section id="watch"><p class="cs-kicker">{n0 + 1:02d} · Risks and signals</p><h2>What would change our view</h2><p class="cs-lede">The signals to track over the next two quarters, and what each would mean for the recommendations.</p><div class="watch">{watch}</div></section>'
    ms = ''.join(f'<div><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in r['method_stats'])
    method = f'''<section id="method"><p class="cs-kicker">{n0 + 2:02d} · Appendix</p><h2>Method and sources</h2><div class="method-grid">{ms}</div>
<div class="prose">{r["method"]}<p>Dish categories were made more specific on 24 October 2026; each answer is coded to the dish itself with a parent group. A <b>clear move</b> means a two-proportion test between July to December 2025 and April 2026 onward came out at p &lt; 0.05. Dream Menu is qualitative fieldwork with food-literate guests, chefs and hospitality staff, not a statistically representative survey of the population. <a href="/how-it-works">How Dream Menu works</a>.</p>{r.get("sources", "")}</div></section>'''
    k = ORDER.index(r['slug'])
    pick = [ORDER[(k + j) % len(ORDER)] for j in (1, 2, 3)]
    more = ''.join(f'<a href="/case-studies/{s}"><small>No. {META[s]["no"]:02d} · {esc(META[s]["kind"])}</small><b>{esc(META[s]["plain"])}</b></a>' for s in pick)
    nxt = f'''<section id="next"><div class="cs-next"><h2>Want this for your business?</h2><p>Every report in the series can be commissioned for your category, market or venue, with fresh fieldwork on top of the archive and quarterly tracking after.</p><a class="cs-btn" href="mailto:{CONTACT}?subject=Commissioned%20report">Talk to Dream Menu</a></div>
<h3 style="margin:26px 0 0;font-size:17px">More from the Insight Series</h3><div class="cs-more">{more}</div></section>'''
    body = cover + f'<div class="wrap cs-body">{toc}<article class="cs-art">{summ}{chap}{recs}{watch}{method}{nxt}</article></div>'
    REPORTS.append(r)
    return write(f'/case-studies/{r["slug"]}', r['plain'], r['desc'], body)


# ================================================================== shared figures
s_t, m_t, d_t, p_t, a_t, k_t = (trend(c) for c in 'smdpak')
Q = [qlab(q) for q in s_t['q']]
CM = AN['cities']
GI, EI = CM['markets'].index('Glasgow'), CM['markets'].index('Edinburgh')
GL, ED = MK['Glasgow'], MK['Edinburgh']
BIN, GUILTY = P['extra']['bin'], P['extra']['guilty']
DEB = SC['debates']
CONC = {c['course']: c for c in AN['conc']}
GROUPS = {g['g']: g for g in P['groups']}


# ================================================================== 01 night out (Gordon's draft)
def r_night_out():
    ex = Ex()
    NIQ = 'https://nielseniq.com/global/en/insights/analysis/2026/why-value-matters-more-than-ever-for-restaurants/'
    L = link
    grid_rows = [('Pint of standard lager', [4.60, 5.40, 6.50, 6.80]), ('Pint of premium lager or craft', [5.30, 6.20, 7.20, 7.50]),
                 ('Pint of Guinness', [4.90, 5.60, 6.60, 6.80]), ('Glass of house wine (175ml)', [6.00, 7.50, 9.50, 8.50]),
                 ('Spirit and mixer (single)', [4.80, 6.00, 8.00, 7.00]), ('Cocktail', [None, 10.50, 13.50, 11.00]),
                 ('Soft drink or alcohol-free pint', [2.80, 3.80, 4.50, 4.50])]
    tiers = ['Local or suburban pub', 'City-centre bar', 'Cocktail or hotel bar', 'Club or live venue']
    gbp = lambda v: f'£{v:.2f}'
    pressures = [('Food input costs', 63), ('Energy and utilities', 61), ('Labour costs', 57), ('Rent, rates and property', 52), ('Consumer demand and footfall', 44), ('Debt and cashflow', 33), ('Drink input costs', 26)]
    ch1 = (ex('A typical Glasgow night costs £74 a head, and drink is the biggest line', 'Modelled per-head spend on a typical Saturday, October 2026.',
              waterfall([('Food', 30), ('Drink', 34), ('Transport', 10)], 'Typical night'),
              'Dream Menu model built from the Glasgow price grids in this report', (['Line', 'Per head', 'Share'], [['Food', '£30', '41%'], ['Drink', '£34', '46%'], ['Transport', '£10', '13%'], ['Total', '£74', '100%']]))
           + ex('A celebration costs nearly four times a catch-up, and most people should add a fifth', 'Modelled per-head budget by type of night, with the 20% overspend buffer.',
                hbar([('The catch-up', 40, 'Plan £48 with the buffer'), ('The classic Saturday', 75, 'Plan £90 with the buffer'), ('The big night', 150, 'Plan £180 with the buffer')], on={'The classic Saturday'}, pre='£'),
                f'Dream Menu model; overspend from {L("https://confidentials.com/body/boozy-brits-spend-6500-a-year-on-nights-out", "Confidentials")} (78% of 18 to 35s go over budget)',
                (['Night', 'Plan for', 'With 20% buffer'], [['The catch-up', '£40', '£48'], ['The classic Saturday', '£75', '£90'], ['The big night', '£150', '£180']]))
           + '<div class="prose"><p><b>What each night includes.</b> The catch-up: two cans at home, four pints at about £5.20, a chippy, bus in and night bus home. The classic Saturday: two courses with service, five drinks mixing pints, wine and a cocktail, bus in and half a £16 to £20 taxi. The big night: a pre-dinner cocktail, dinner with shared wine, four drinks across a cocktail bar and club, £10 entry, a late bite and a solo taxi.</p></div>'
           + sowhat('Dunns', 'Drink and the optional extras decide the bill. That is where venues are losing spend, and where a supplier can help them keep it.'))
    ch2 = ('<div class="prose"><p>A night out costs around a third more than it did in 2022. Glasgow remains one of the better-value big cities in the UK, which is a selling point for its venues but also caps how much of the cost stack they can pass on before losing their value reputation.</p></div>'
           + ex('Glasgow pours one of the cheapest pints of Guinness in the UK', 'Average price of a pint of Guinness, March 2026.',
                hbar([('Glasgow', 4.93), ('UK average', 5.41), ('London', 6.87)], on={'Glasgow'}, dec=2, pre='£'),
                L('https://www.thedrinksbusiness.com/2026/03/guinness-prices-rise-across-the-uk/', 'The Drinks Business, March 2026'), (['City', 'Pint of Guinness'], [['Glasgow', '£4.93'], ['UK average', '£5.41'], ['London', '£6.87']]))
           + table(['Signal', 'What it means'], [
               ['<b>Hospitality prices are up about 30% in four years</b>', f'Average restaurant spend per head has risen from £25.35 to £30.08 ({L(NIQ, "NielsenIQ, 2026")}).'],
               ['<b>Scottish pubs face a rates shock</b>', f'Average pub business rates forecast to rise 77% in 2026/27, to £26,385 ({L("https://cater.affino.com/news/scottish-pubs-to-be-hit-with-staggering-increases-to-business-rates", "UKHospitality Scotland via Cater")}). Expect some of it in menu and bar prices within a year.'],
               ['<b>Consumers are price-aware</b>', f'UK adults spend £3,776 a year on nights out ({L("https://www.thedrinksbusiness.com/2025/10/brits-spend-nearly-4k-per-year-on-nights-out-study-reveals/", "Aqua via The Drinks Business")}), yet price is the top worry for 44% planning one ({L("https://www.thespiritsbusiness.com/2023/12/young-adults-avoid-booze-on-nights-out/", "Rekom via The Spirits Business")}).'],
               ['<b>Getting home has got cheaper</b>', 'Bus singles capped at £2 across the SPT area from 7 September 2026; ScotRail peak fares scrapped permanently in September 2025.'],
           ]))
    ch3 = (ex('The venue tier moves a drink by up to £3, and the cocktail decides the bill', 'Modelled Glasgow prices by drink and venue tier, October 2026 (indicative).',
              heat(['Drink'] + tiers, grid_rows, fmt=gbp, key=('Cheaper', 'Dearer')),
              f'Dream Menu model from national and Glasgow benchmarks ({L("https://www.morningadvertiser.co.uk/Article/2026/05/21/average-pint-price-rises-33-to-534-the-morning-advertiser-finds/", "Morning Advertiser")}, {L("https://www.finder.com/uk/drinking-statistics", "Finder")}), with Scottish venue-tier mark-ups. A planning model, not a price list.',
              (['Drink'] + tiers, [[d] + [gbp(v) if v else 'n/a' for v in vs] for d, vs in grid_rows]))
           + '<div class="prose"><p>A city-centre pint sits at £5.20 to £6.20, below Edinburgh (about £6) and London (about £6.75). The UK average pint was £5.34 in April 2026, up 3.3% on the year, and brewers raised wholesale prices again in 2026. Food is the most controllable line: dinner runs £18 to £45 a head, a meal at an inexpensive Glasgow restaurant averages £17.20, and a set or pre-theatre menu saves £10 or more.</p></div>'
           + '<div class="sowhat" style="background:var(--panel)"><b>Scottish factor</b><p>Minimum unit pricing (65p a unit in shops) lifts the cost of drinking at home, so the gap between pre-drinks and drinking out is narrower in Scotland than in England.</p></div>')
    ch4 = (table(['Mode', 'Cost per trip, Oct 2026', 'Night-out notes'], [
        ['First Glasgow or Stagecoach bus, including night buses', '£2 single, capped', f'£2 cap across the SPT area from 7 Sept 2026 ({L("https://www.firstbus.co.uk/greater-glasgow/tickets/ps2-fare-cap", "First Bus")}). Night routes such as N2, N18, N240 and N267 run Friday and Saturday.'],
        ['First 6pm Plus ticket', '£4.75 (city, app)', f'Unlimited travel after 6pm, including night buses ({L("https://www.firstbus.co.uk/greater-glasgow/plan-journey/forthcoming-fare-changes", "First Bus")})'],
        ['Glasgow Subway', '£1.80 smartcard', f'Last trains around 23:40 Monday to Saturday and about 18:12 on Sundays ({L("https://www.scottishdailyexpress.co.uk/news/scottish-news/blow-rangers-fans-spt-confirms-36429818", "Scottish Daily Express")})'],
        ['Black cab, centre to West End or Southside', 'Modelled £10 to £18', f'Flag fall £4.50 after the 2025 review; night tariff from 11pm ({L("https://prod.news.stv.tv/west-central/glasgow-taxi-fares-increase-proposed-as-drivers-call-for-higher-night-charges", "STV")})'],
        ['Black cab, centre to outer suburbs', 'Modelled £20 to £30', 'Long queues at Gordon Street and Hope Street ranks after 2am'],
        ['Uber or private hire', 'Modelled £12 to £35', 'Surge pricing at closing time can add 50% to 100%'],
        ['ScotRail late train', 'About £16.80 Glasgow to Edinburgh return', f'Peak fares scrapped from 1 Sept 2025 ({L("https://www.timeout.com/uk/news/the-major-british-rail-operator-that-has-axed-all-peak-time-fares-090225", "Time Out")}); last departures around midnight'],
    ]) + sowhat('venues', 'The cheapest way home is now cheaper than one soft drink. The constraint is timing: the Subway closes early and the last trains leave around midnight, so late spend from suburban and Edinburgh visitors competes with the timetable.'))
    ch5 = ('<div class="prose"><p>Two datasets sit behind this section: 962 community interviews and the operator survey from April 2026, as published in the Dream Menu Hospitality Intelligence Report 2026. All mentions are unprompted.</p></div>'
           + '<div class="ex-pair"><div>' + ex('Soft drinks are the most-named dream drink, and classic cocktails rival beer', 'Dream-drink mentions in 962 interviews.',
                hbar([('Soft and diet drinks', 143), ('Beer', 116), ('Margarita', 66), ('Martini', 64)], on={'Soft and diet drinks'}),
                'Dream Menu Hospitality Intelligence Report 2026', (['Drink', 'Mentions'], [['Soft and diet drinks', 143], ['Beer', 116], ['Margarita', 66], ['Martini', 64]])) + '</div><div>'
           + ex('Food costs top the pressures; drink costs trail', 'Share of operators naming each pressure, April 2026.',
                hbar(pressures, on={'Food input costs'}, alt={'Drink input costs'}, unit='%'),
                'Dream Menu 2026 operator survey, as published in the 2026 report', (['Pressure', 'Share'], [[a, f'{b}%'] for a, b in pressures])) + '</div></div>'
           + '<ul class="prose">' + ''.join(f'<li style="margin-bottom:8px">{x}</li>' for x in [
               '<b>Classic cocktails carry the premium end of the bill.</b> Margaritas (66) and martinis (64) together outrank beer (116), and these are the £10 to £13.50 drinks in the price grid.',
               '<b>No and low is no longer the cheap option.</b> Irn Bru beats Coca-Cola 435 to 307, and at £3.80 a time in town a soft round costs real money.',
               '<b>Diners spend on classics, not gimmicks.</b> Steak (251), seafood starters (303, scallops alone 99) and chips (240) lead; Dubai chocolate (124) and matcha (90) top the trends people want gone.',
               '<b>The extras are what get cut.</b> 72% of operators report spend per head flat or falling; guests skip the starter, the second cocktail or the dessert.',
               '<b>The late-night end is comfort food.</b> Pizza (141), kebab (36) and the chippy (23) dominate guilty pleasures; late-night dessert is a documented concept gap.',
           ]) + '</ul>')
    recs = [
        ('Lead sales calls with a "save the last spend" range', 'Ready-to-plate desserts in the most-named formats (ice cream 221, sticky toffee pudding 122, tiramisu 120) and batch-friendly cocktail serves: the two lines guests cut first.', 'High', 'Low', 'Quarter 1'),
        ('Launch a "Glasgow classics" bar pack', 'Tequila, gin, vermouth, citrus and premium mixers with a costed menu at a £10 to £11 sell price. Margarita 66 and martini 64 against beer 116.', 'High', 'Low', 'Quarter 1'),
        ('Co-publish a quarterly Glasgow Night Out Index', 'A fixed basket (pint, wine, cocktail, soft drink, casual main, late bite, taxi home) in the Dunns-sponsored quarterly report: a repeatable headline for the press and the sales team.', 'High', 'Medium', 'Quarter 1'),
        ('Price soft drinks and no/low as margin lines', 'Premium soft drinks, Scottish mixers and alcohol-free pints with a menu template at £3.50 to £4.50. Soft drinks are the most-named dream drink.', 'Medium', 'Low', 'Quarter 1'),
        ('Build costed £22 and £30 set-menu kits', 'Around the most-named dishes (steak 251, seafood starters 303, chips 240). Set price points are what operators say convert cautious diners.', 'High', 'Medium', 'Quarter 2'),
        ('Offer one-quarter price holds on core lines', '87% of operators report supplier prices rising and 46% have changed or renegotiated suppliers in six months: a retention risk and an opening.', 'Medium', 'High', 'Quarter 2'),
        ('Target new accounts in emerging districts', 'The Barras draws 50 mentions and the Southside has the widest gap between guest advocacy and press attention (see No. 07).', 'Medium', 'Medium', 'Quarter 2'),
    ]
    return render(dict(slug='night-out', ex=ex, status='draft', dated='28 October 2026', aud='supplier venue public', **META['night-out'],
        title='The cost of a <em>night out</em> in Glasgow',
        desc='What food, drink and transport cost on a Glasgow night out in 2026, how to budget for one, and what it means for a food and drink distributor.',
        stand='What food, drink and transport cost on a Glasgow night out in 2026, how to budget for one, and where a food and drink distributor can help venues keep the spend that guests are cutting.',
        client='Dunns Food & Drinks', question='What does a night out cost, and where is the spend being lost?', evidence='Published price benchmarks, Dream Menu 2026 report, operator survey',
        kpis=[('£74', 'a typical night out, per head'), ('£34', 'of it on drink, the most elastic line'), ('£2', 'the cheapest way home, under one soft drink'), ('72%', 'of operators see spend per head flat or falling')],
        answer='Glasgow is still good value at about £74 a head, but guests are trading down inside the bill, so the prize for a distributor is helping venues keep the dessert, the last drink and the soft round.',
        msgs=[('£74', 'a head', 'A typical night, split three ways', 'About £30 food, £34 drink and £10 transport. A low-key night is £40 and a celebration £150 or more; add 20% because most people overspend.'),
              ('10%', 'cheaper', 'Good value caps pricing', 'Drink runs about 10% below Edinburgh and 20% below London. The price advantage sells the city but limits what venues can pass on.'),
              ('72%', 'of operators', 'The extras are what get cut', 'Spend per head is flat or falling as guests skip dessert and the extra drink. Classics still win the spend that remains.')],
        chapters=[('budget', 'The bill', 'A typical night costs £74 a head, and the extras decide it', 'Three modelled nights out, built from Glasgow prices: the catch-up, the classic Saturday and the big night.', ch1),
                  ('market', 'Market context', 'A night out costs a third more than in 2022', 'Prices, rates and consumer worry are rising together; transport is the one line that has got cheaper.', ch2),
                  ('drink', 'Food and drink', 'Drink is the biggest and most elastic line', 'Where the money goes behind the bar and on the plate.', ch3),
                  ('transport', 'Transport', 'Getting home is cheap; getting home late is hard', 'A £2 night bus and a £20 solo taxi can sit either side of the same evening.', ch4),
                  ('dream-menu', 'What Dream Menu adds', 'Guests are trading down inside the bill, not staying in', 'What 962 interviews and the operator survey say about where the money still goes.', ch5)],
        recs=recs, recs_lede='Seven ideas for Dunns, each linking a cost-of-night-out finding to a product, a sales conversation or joint content. Start with the four quick wins in the first quarter.',
        watch=[('Rates and wage costs', 'If the 2026/27 rates rise reaches bar prices faster than expected, the night-out total moves above £80 and the set-menu kits become more urgent.'),
               ('The £2 bus cap', 'The cap is why transport got cheaper. If it ends or narrows, the taxi line grows again and late spend suffers.'),
               ('Spend per head', 'A second operator survey showing spend per head recovering would shift the focus from protecting spend to growing it.'),
               ('Cocktail share', 'Cocktails are losing share of dream drinks (see No. 05). If that continues, weight the bar pack towards whisky and lager.')],
        method_stats=[('962', 'interviews in the 2026 report'), ('54', 'operators in the 2026 report'), ('20+', 'published price sources'), ('3', 'modelled nights out')],
        method='<p>Glasgow price grids and personas are modelled, indicative figures, not a venue price survey. They start from published national and city benchmarks and apply typical Scottish venue-tier mark-ups. Dream Menu figures are exact counts from the 2026 report; the live archive now holds ' + f0(N_ALL) + ' interviews, which the other reports in the series use.</p>',
        sources='<p><b>Sources:</b> ' + ', '.join([L(NIQ, 'NielsenIQ'), L('https://www.morningadvertiser.co.uk/Article/2026/05/21/average-pint-price-rises-33-to-534-the-morning-advertiser-finds/', 'Morning Advertiser'), L('https://www.thedrinksbusiness.com/2026/03/guinness-prices-rise-across-the-uk/', 'The Drinks Business'), L('https://www.finder.com/uk/drinking-statistics', 'Finder'), L('https://www.thinkmoney.co.uk/blog/pints-up-33percent-to-pound534-as-pound10-pints-arrive-in-london-what-it-means-fo/', 'thinkmoney'), L('https://www.expatica.com/uk/cost-of-living/glasgow/', 'Expatica (Numbeo)'), L('https://expatistan.com/cost-of-living/comparison/sofia/glasgow', 'Expatistan'), L('https://cater.affino.com/news/scottish-pubs-to-be-hit-with-staggering-increases-to-business-rates', 'UKHospitality Scotland via Cater'), L('https://www.thespiritsbusiness.com/2023/12/young-adults-avoid-booze-on-nights-out/', 'The Spirits Business'), L('https://thinkmoney.co.uk/blog/a-night-in-numbers-how-to-budget-on-nights-out', 'thinkmoney budgeting'), L('https://confidentials.com/body/boozy-brits-spend-6500-a-year-on-nights-out', 'Confidentials'), L('https://www.firstbus.co.uk/greater-glasgow/tickets/ps2-fare-cap', 'First Bus'), L('https://prod.news.stv.tv/west-central/glasgow-taxi-fares-increase-proposed-as-drivers-call-for-higher-night-charges', 'STV'), L('https://www.timeout.com/uk/news/the-major-british-rail-operator-that-has-axed-all-peak-time-fares-090225', 'Time Out')]) + '.</p>',
        card=('£74', 'a typical Glasgow night out, per head'),
        blurb='What food, drink and transport cost on a Glasgow night out, how to budget for one, and where a distributor can help venues keep the spend.'))


# ================================================================== 02 Glasgow and Edinburgh
def r_two_cities():
    ex = Ex()
    rows = [r for r in CM['rows'] if not r['cells'][GI]['thin'] and not r['cells'][EI]['thin']]
    gap = sorted(rows, key=lambda r: r['cells'][EI]['idx'] - r['cells'][GI]['idx'], reverse=True)
    neg, mar, marg, scal, stp, tira = (city_row(x) for x in ('Negroni', 'Martini', 'Margarita', 'Scallops', 'Sticky toffee pudding', 'Tiramisu'))
    top10 = lambda m: sum(VEN[i]['m'] for i in m['top'][:10])
    gt, et = top10(GL), top10(ED)
    gsea, esea = dict((c[0], c[2]) for c in GL['cat']).get('Seafood', 0), dict((c[0], c[2]) for c in ED['cat']).get('Seafood', 0)
    ch1 = (ex('Edinburgh leans to stirred drinks and pudding; Glasgow to shellfish, tiramisu and margaritas', 'Edinburgh index minus Glasgow index for each dish (index: 100 = the all-market average). Right of the line: Edinburgh names it more.',
              diverge([(r['l'], r['cells'][EI]['idx'] - r['cells'][GI]['idx']) for r in gap], left='Glasgow leans', right='Edinburgh leans', show=lambda v: f'{v:+.0f}'),
              f'{DM_SRC}; dish mentions tied to a venue ({f0(CM["totals"][GI])} Glasgow, {f0(CM["totals"][EI])} Edinburgh)',
              (['Dish', 'Glasgow share', 'Glasgow index', 'Edinburgh share', 'Edinburgh index'], [[r['l'], f'{r["cells"][GI]["share"]}%', r['cells'][GI]['idx'], f'{r["cells"][EI]["share"]}%', r['cells'][EI]['idx']] for r in gap]))
           + sowhat('a second site', f'The bar list is the biggest change: Edinburgh names the negroni at {neg["cells"][EI]["idx"]} and the martini at {mar["cells"][EI]["idx"]} on the index; Glasgow at {neg["cells"][GI]["idx"]} and {mar["cells"][GI]["idx"]}. A margarita-led list needs a stirred section to travel east.'))
    ch2 = ('<div class="ex-pair"><div>' + ex('Glasgow\'s favourites are spread across many venues', f'Times each venue is named, Glasgow top 10 ({f0(GL["mn"])} mentions in all).',
              hbar([(vname(i), VEN[i]['m']) for i in GL['top'][:10]], on={vname(GL['top'][0])}), DM_SRC, (['Venue', 'Mentions'], [[vname(i), VEN[i]['m']] for i in GL['top'][:10]])) + '</div><div>'
           + ex('Edinburgh\'s sit with fewer names', f'Times each venue is named, Edinburgh top 10 ({f0(ED["mn"])} mentions in all).',
              hbar([(vname(i), VEN[i]['m']) for i in ED['top'][:10]], on={vname(ED['top'][0])}), DM_SRC, (['Venue', 'Mentions'], [[vname(i), VEN[i]['m']] for i in ED['top'][:10]])) + '</div></div>'
           + ex(f'The top ten take {pc(et, ED["mn"])}% of Edinburgh\'s attention and {pc(gt, GL["mn"])}% of Glasgow\'s', 'Share of each city\'s venue mentions going to its ten most-named venues.',
                stack([('Edinburgh', f'{f0(ED["mn"])} mentions', [('Top 10 venues', et, 'k1'), ('Every other venue', ED['mn'] - et, 'k0')]),
                       ('Glasgow', f'{f0(GL["mn"])} mentions', [('Top 10 venues', gt, 'k1'), ('Every other venue', GL['mn'] - gt, 'k0')])],
                      [('Top 10 venues', 'k1'), ('Every other venue', 'k0')]), DM_SRC,
                (['City', 'Top 10 mentions', 'All mentions', 'Share'], [['Edinburgh', et, ED['mn'], f'{pc(et, ED["mn"])}%'], ['Glasgow', gt, GL['mn'], f'{pc(gt, GL["mn"])}%']]))
           + sowhat('a newcomer', f'In Edinburgh you are competing with a short list of strong favourites led by {vname(ED["top"][0])}. Aim to be talked about alongside them, not instead of them.'))
    three = ('Scallops', 'Tiramisu', 'Sticky toffee pudding', 'Cod, hake and white fish')
    ch3 = (ex('The dessert that sells in one city is second choice in the other', 'Index by city for four signature dishes (100 = the all-market average).',
              '<div class="ex-pair">' + ''.join(f'<div><h4>{esc(lbl)}</h4>' + hbar([(m, city_row(lbl)['cells'][i]['idx']) for i, m in ((GI, 'Glasgow'), (EI, 'Edinburgh'))], on={'Glasgow' if city_row(lbl)['cells'][GI]['idx'] > city_row(lbl)['cells'][EI]['idx'] else 'Edinburgh'}, mx=200) + '</div>' for lbl in three) + '</div>',
              DM_SRC, (['Dish', 'Glasgow index', 'Edinburgh index'], [[lbl, city_row(lbl)['cells'][GI]['idx'], city_row(lbl)['cells'][EI]['idx']] for lbl in three]))
           + f'<div class="prose"><p>Edinburgh still loves seafood: it is {f1(esea)}% of the city\'s venue mentions against {f1(gsea)}% in Glasgow. But where Glasgow names scallops ({scal["cells"][GI]["share"]}% of dish mentions, index {scal["cells"][GI]["idx"]}), Edinburgh names white fish and Leith\'s fish specialists. On dessert the cities swap: sticky toffee pudding indexes {stp["cells"][EI]["idx"]} in Edinburgh, tiramisu {tira["cells"][GI]["idx"]} in Glasgow.</p></div>')
    recs = [('Rewrite the bar list for Edinburgh', f'Keep two margaritas and add a stirred section (negroni, martini, a freezer martini). Negroni index {neg["cells"][EI]["idx"]} in Edinburgh against {neg["cells"][GI]["idx"]} in Glasgow.', 'High', 'Low', 'Before opening'),
            ('Plan launch PR around the favourites', f'Ten venues take {pc(et, ED["mn"])}% of Edinburgh mentions. Collaborations or guest nights with them earn word of mouth faster than paid launch media.', 'High', 'Medium', 'Launch quarter'),
            ('Test the format before signing', 'Twenty interviews with Edinburgh guests on your format and dishes before committing to a site: cheap insurance on a six-figure fit-out.', 'High', 'Medium', 'Site search'),
            ('Swap the dessert anchor', f'Sticky toffee pudding indexes {stp["cells"][EI]["idx"]} in Edinburgh; tiramisu {tira["cells"][GI]["idx"]} in Glasgow. Lead with the local favourite.', 'Medium', 'Low', 'Before opening'),
            ('Lead starters with named Scottish fish', 'Keep one shellfish signature, but Edinburgh guests reward white fish and Leith-style fish cookery more than scallops.', 'Medium', 'Medium', 'Menu build')]
    return render(dict(slug='glasgow-edinburgh', ex=ex, status='sample', aud='investor venue', **META['glasgow-edinburgh'],
        title='Two cities, <em>two appetites</em>', desc='How Glasgow and Edinburgh guests differ on drinks, seafood and dessert, and what a restaurant group needs to change to open a second site.',
        stand='A Glasgow format that works is not guaranteed to work 45 miles east. This read compares what guests in each city name, which venues set the bar, and how concentrated each market is.',
        client='A restaurant group with a Glasgow venue, weighing an Edinburgh opening', question='What would a second site need to change?', evidence=f'{f0(CM["totals"][GI] + CM["totals"][EI])} dish mentions, {f0(GL["mn"] + ED["mn"])} venue mentions',
        kpis=[(str(neg['cells'][EI]['idx']), 'Edinburgh negroni index (100 = average)'), (str(marg['cells'][GI]['idx']), 'Glasgow margarita index'), (f'{pc(et, ED["mn"])}%', 'of Edinburgh mentions go to its top 10 venues'), (f'{pc(gt, GL["mn"])}%', 'the same figure for Glasgow')],
        answer='The format can travel, but the bar list, the dessert and the launch plan should not: Edinburgh drinks stirred, prefers pudding and concentrates its loyalty on fewer venues.',
        msgs=[(str(neg['cells'][EI]['idx']), 'index', 'Edinburgh drinks stirred, Glasgow shaken', f'Negroni {neg["cells"][EI]["idx"]} and martini {mar["cells"][EI]["idx"]} in Edinburgh; the margarita indexes {marg["cells"][GI]["idx"]} in Glasgow.'),
              (str(scal['cells'][GI]['idx']), 'index', 'Glasgow is the scallop city', f'Scallops index {scal["cells"][GI]["idx"]} in Glasgow and {scal["cells"][EI]["idx"]} in Edinburgh, where white fish leads instead.'),
              (f'{pc(et, ED["mn"])}%', 'top-10 share', 'Edinburgh is more concentrated', f'Its ten favourites take {pc(et, ED["mn"])}% of mentions against {pc(gt, GL["mn"])}% in Glasgow.')],
        chapters=[('dishes', 'Dish by dish', 'Edinburgh drinks stirred; Glasgow shakes and orders shellfish', 'Each city\'s share of dish mentions against the all-market average, and where the two differ most.', ch1),
                  ('venues', 'Who sets the bar', 'Edinburgh\'s loyalty sits with fewer venues', 'The venues each city names most, and how much of the conversation they hold.', ch2),
                  ('signatures', 'Signature dishes', 'The dessert that sells in one city is second choice in the other', 'Four dishes that change between the cities.', ch3)],
        recs=recs,
        watch=[('Edinburgh sample size', f'Edinburgh has {f0(CM["totals"][EI])} dish mentions against {f0(CM["totals"][GI])} in Glasgow. A commission would add targeted Edinburgh interviews to firm up single-dish reads.'),
               ('Festival distortion', 'August interviews include Fringe visitors. Excluding August would show whether the stirred-drinks lean is local or visitor-led.'),
               ('Cocktail fatigue', 'Cocktails are losing share across the archive (No. 05). Stirred classics are holding up better than house cocktails.'),
               ('New favourites', 'A new Edinburgh opening entering the top ten would show the market is less closed than it looks.')],
        method_stats=[(f0(CM['totals'][GI]), 'Glasgow dish mentions'), (f0(CM['totals'][EI]), 'Edinburgh dish mentions'), (f0(GL['v']), 'Glasgow venues named'), (f0(ED['v']), 'Edinburgh venues named')],
        method=f'<p>Built from venue mentions in {f0(N_ALL)} interviews to {LAST_H}. The index compares a city\'s share of dish mentions with the share across all markets (100 = average). Only dishes with enough mentions in both cities are shown; single-dish figures for Edinburgh rest on 5 to 10 mentions each and are directional.</p>',
        card=(str(neg['cells'][EI]['idx']), f'Edinburgh negroni index, against {neg["cells"][GI]["idx"]} in Glasgow'),
        blurb='What Glasgow and Edinburgh guests name more than everyone else, and what a restaurant group would change for a second site.'))


# ================================================================== 03 seafood
def r_seafood():
    ex = Ex()
    s_sea, m_sea = item('s', 'Seafood', 'groups'), item('m', 'Seafood', 'groups')
    cats = [it for it in s_t['cats'] if it.get('g') == 'Seafood'][:7]
    cod, scal_i = item('m', 'Cod, hake and white fish'), item('s', 'Scallops')
    others = [g for g in s_t['groups'] if g['c'] != 'Seafood'][:4]
    sea_v = sorted(DM['venues'], key=lambda v: -cat_count(v, 'Seafood'))[:10]
    grp = {g: dict(GROUPS[g]['top_groups']).get('Seafood', 0) for g in GROUPS}
    top3 = sum(it['pct'] for it in cats[:3])
    db_rows = [('Seafood mains (group)', m_sea['early'], m_sea['late']), ('Cod, hake and white fish (main)', cod['early'], cod['late']), ('Seafood starters (group)', s_sea['early'], s_sea['late'])] + [(it['l'], it['early'], it['late']) for it in cats[:5]]
    ch1 = (ex('Seafood takes over a third of all dream starters, more than the next four groups combined', 'Share of dream starters by food group.',
              hbar([(s_sea['c'], s_sea['pct'])] + [(g['c'], g['pct']) for g in others], on={'Seafood'}, unit='%', dec=1),
              f'{DM_SRC}; {f0(s_t["n"])} starters', (['Group', 'Share', 'Answers'], [[g['c'], f'{g["pct"]}%', g['n']] for g in [s_sea] + others]))
           + ex(f'Scallops lead, and the shellfish top three cover {top3:.0f}% of all starters', 'Dream seafood starters, number of mentions.',
                hbar([(it['l'], it['n']) for it in cats], on={it['l'] for it in cats[:3]}),
                DM_SRC, (['Dish', 'Mentions', 'Share of starters'], [[it['l'], it['n'], f'{it["pct"]}%'] for it in cats])))
    ch2 = (ex('White fish is the clear riser on the main course', 'Share of dream mains and starters, early against recent.',
              dumbbell(db_rows, sig={'Cod, hake and white fish (main)'}),
              f'{DM_SRC}. Clear move: two-proportion test, p < 0.05', (['Item', EARLY, RECENT, 'Change'], [[a, f'{b}%', f'{c}%', pts(c - b)] for a, b, c in db_rows]))
           + ex('Seafood mains, white fish and scallops by quarter', 'Share of answers each quarter, on one scale. Faded points have fewer than 100 answers.',
                small_multiples([('Seafood mains', m_sea['share'], 'k1'), ('White fish mains', cod['share'], 'k1'), ('Scallop starters', scal_i['share'], 'k0'), ('Seafood starters', s_sea['share'], 'k0')], Q, faded=faded('m')),
                DM_SRC, (['Quarter'] + Q, [[n] + [f'{v}%' for v in it['share']] for n, it in (('Seafood mains', m_sea), ('White fish mains', cod), ('Scallop starters', scal_i), ('Seafood starters', s_sea))]))
           + sowhat('a seafood supplier', f'The volume is in starters; the growth is in mains. White fish rose from {f1(cod["early"])}% to {f1(cod["late"])}% of dream mains, a clear move, while starters hold steady around a third.'))
    ch3 = ('<div class="ex-pair"><div>' + ex('One venue owns seafood; Leith and the coast share the rest', 'Seafood mentions by venue.',
              hbar([(v['n'], cat_count(v, 'Seafood'), vloc(v)) for v in sea_v], on={sea_v[0]['n']}), DM_SRC, (['Venue', 'Place', 'Seafood mentions'], [[v['n'], vloc(v), cat_count(v, 'Seafood')] for v in sea_v])) + '</div><div>'
           + ex('The trade names seafood most', 'Seafood as a share of everything each group names.',
                hbar([(g, grp[g]) for g in ('Industry', 'Enthusiasts', 'Creators')], on={'Industry'}, unit='%', dec=1), DM_SRC,
                (['Group', 'Seafood share'], [[g, f'{grp[g]}%'] for g in grp])) + '</div></div>'
           + quotes([('Hand dived Orkney scallops with chipotle, mussel, squash and pata negra from Heron in Leith.', 'Dream Menu guest'),
                     ('Scallops in anchovy butter, Crabshakk. The butter has to be soaked up with a side of skinny fries and a basket of bread!', 'Dream Menu guest'),
                     ('Fish pastrami from Barry Fish in Leith. It\'s sensational.', 'Dream Menu guest')])
           + sowhat('a supplier', f'Guests repeat provenance back word for word: hand-dived, Orkney, Leith. Named origin is the selling point, and outside {sea_v[0]["n"]} no venue has yet claimed a seafood dish as its own.'))
    recs = [('Make named-origin scallops the hero line', f'Scallops are {f1(scal_i["pct"])}% of all starters, the single most-named starter. Sell hand-dived and named-harbour scallops with the story attached.', 'High', 'Low', 'Next quarter'),
            ('Build a white fish range for mains', f'Cod, hake and white fish mains rose from {f1(cod["early"])}% to {f1(cod["late"])}%: the clearest seafood riser. Portioned, with one sauce idea per cut.', 'High', 'Medium', 'Next two quarters'),
            ('Sell to chefs first', f'The trade names seafood at {f1(grp["Industry"])}% of everything it names, ahead of enthusiasts ({f1(grp["Enthusiasts"])}%). Sampling and kitchen visits beat consumer marketing.', 'Medium', 'Low', 'Ongoing'),
            ('Help one venue per district own a seafood dish', 'Demand outside the top venue is thin and spread. Co-develop a signature with venues guests already name for one seafood dish.', 'Medium', 'Medium', 'Six months'),
            ('Track the starter share quarterly', 'Seafood starters are steady around a third. A fall below 30% would be the first sign of fatigue.', 'Low', 'Low', 'Quarterly')]
    return render(dict(slug='seafood', ex=ex, status='sample', aud='supplier venue', **META['seafood'],
        title="Scotland's <em>seafood</em> appetite", desc='Where seafood sits on the dream menu, which dishes lead, what is rising and which venues own it.',
        stand='Seafood is the single biggest idea on Scotland\'s dream menu. This report reads it across starters and mains, tracks it quarter by quarter, and names the venues guests associate with it.',
        client='A Scottish seafood supplier planning its foodservice range', question='Which seafood products should we push next year, and to whom?', evidence=f'{f0(s_t["n"])} starters, {f0(m_t["n"])} mains, venue mentions',
        kpis=[(f'{f1(s_sea["pct"])}%', 'of dream starters are seafood'), (f'{f1(scal_i["pct"])}%', 'name scallops, the top starter'), (f'{f1(m_sea["pct"])}%', 'of dream mains are seafood'), (f'{pts(cod["move"])} pts', 'white fish mains, a clear rise')],
        answer='Seafood owns the starter and is growing on the main course, so the range should pair a named-origin scallop hero with a white fish line for mains, sold to chefs first.',
        msgs=[(f'{f1(s_sea["pct"])}%', 'of starters', 'Seafood owns the starter', f'{f0(s_t["n"])} dream starters; seafood takes {f1(s_sea["pct"])}%, and scallops alone {f1(scal_i["pct"])}%.'),
              (pts(cod['move']), 'pts', 'White fish is the riser', f'Cod, hake and white fish mains rose from {f1(cod["early"])}% to {f1(cod["late"])}%, a clear move.'),
              (f'{f1(grp["Industry"])}%', 'of trade picks', 'Chefs are the advocates', 'Hospitality professionals name seafood more than any other group.')],
        chapters=[('starter', 'The starter', 'Seafood takes a third of all dream starters', 'Where seafood sits against every other food group, and which dishes lead.', ch1),
                  ('trend', 'The trend', 'The growth is moving to the main course', 'Early against recent, and quarter by quarter.', ch2),
                  ('where', 'Where and who', 'One venue owns it; the trade champions it', 'The venues guests name for seafood, and which guests name it most.', ch3)],
        recs=recs,
        watch=[('Scallop prices', 'Hand-dived scallop supply is weather and season dependent. A price spike would test how far the hero line can carry a menu price.'),
               ('Prawns and langoustines', 'Prawns started high in the first quarter of fieldwork and have settled. A further fall would suggest fatigue with prawn starters.'),
               ('White fish confirmation', 'Two more quarters at or above the recent share would turn the white fish move from clear to established.'),
               ('Seafood outside Glasgow', 'The rest of Scotland indexes highly for scallops on few mentions. Targeted fieldwork on the coast would show whether that is real.')],
        method_stats=[(f0(s_t['n']), 'dream starters'), (f0(m_t['n']), 'dream mains'), (f0(sum(cat_count(v, 'Seafood') for v in DM['venues'])), 'seafood venue mentions'), ('6', 'quarters tracked')],
        method='<p>Starter and main shares use interviews with a codable answer for that course. Venue figures use mentions tied to a named venue. Quarters with fewer than 100 answers are shown faded.</p>',
        card=(f'{f1(s_sea["pct"])}%', 'of dream starters are seafood'),
        blurb='Where seafood sits on the dream menu, which dishes lead, what is rising and which venues own it.'))


# ================================================================== 04 dessert
def r_dessert():
    ex = Ex()
    tir, stp_i, chs = item('p', 'Tiramisu'), item('p', 'Sticky toffee pudding'), item('p', 'Baked cheesecake')
    frm, choc = item('p', 'Fruit and meringue', 'groups'), item('p', 'Chocolate desserts', 'groups')
    look = P['look']
    spend = Counter(r['spend'] for r in LOOK if r['spend'])
    lower = spend['Down']
    des_v = sorted(DM['venues'], key=lambda v: -v.get('cs', {}).get('p', 0))[:10]
    binx = dict(BIN)
    conc_lbl = lambda c: f'{CONC[c]["cl"]}: {CONC[c]["top1"].lower()}'
    ch1 = (ex('Two desserts take almost a quarter of answers; after that, nobody owns the course', 'Share of dream desserts, top 12 dishes.',
              hbar([(it['l'], it['pct']) for it in p_t['cats'][:12]], on={'Tiramisu', 'Sticky toffee pudding'}, unit='%', dec=1),
              f'{DM_SRC}; {f0(p_t["n"])} desserts', (['Dessert', 'Share', 'Answers'], [[it['l'], f'{it["pct"]}%', it['n']] for it in p_t['cats'][:12]]))
           + ex('Dessert is the most open course on the menu', 'Share taken by the leading food group in each course.',
                hbar([(conc_lbl(c), CONC[c]['top1v']) for c in ('d', 's', 'm', 'p')], on={conc_lbl('p')}, unit='%', dec=1),
                DM_SRC, (['Course', 'Leading group', 'Share'], [[CONC[c]['cl'], CONC[c]['top1'], f'{CONC[c]["top1v"]}%'] for c in 'smdp']))
           + sowhat('a dessert range', f'The volume is in two classics; the opportunity is the open space after them. No other dessert has more than {max(it["pct"] for it in p_t["cats"][2:]):.0f}% of answers, so a venue can still make one its own.'))
    gl = [(g['c'], g['early'], g['late']) for g in p_t['groups'][:8]] + [('Baked cheesecake (dish)', chs['early'], chs['late'])]
    ch2 = (ex('Fruit is clearly up and baked cheesecake clearly down', 'Share of dream desserts by group and dish, early against recent.',
              dumbbell(gl, sig={'Fruit and meringue', 'Baked cheesecake (dish)'}),
              f'{DM_SRC}. Clear move: p < 0.05', (['Group', EARLY, RECENT, 'Change'], [[a, f'{b}%', f'{c}%', pts(c - b)] for a, b, c in gl]))
           + ex('Guests want the novelty chocolate gone', 'Unprompted "bin it" mentions: trends guests would happily see disappear.',
                hbar([(n, v) for n, v in BIN[:10]], on={'Dubai chocolate', 'Pistachio (everything)'}),
                f'{DM_SRC}; "bin it" question', (['Trend', 'Mentions'], [[n, v] for n, v in BIN[:10]])))
    ch3 = (ex('Operators say guests are holding back on spend', 'Average spend per head over the last four weeks, operator survey.',
              stack([('Spend per head', f'{sum(spend.values())} operators', [('Up', spend['Up'], 'k1'), ('Flat', spend['Flat'], 'k0'), ('Down', spend['Down'], 'k2'), ('Unsure', spend['Unsure'], 'k0')])],
                    [('Up', 'k1'), ('Down', 'k2'), ('Flat or unsure', 'k0')]),
              f'2026 Look Ahead operator survey, {len(LOOK)} operators, April to May 2026', (['Answer', 'Operators'], [[k, v] for k, v in spend.most_common()]))
           + ex('Guests walk on for dessert: gelato shops sit beside restaurants', 'Venues named most for dessert.',
                hbar([(v['n'], v['cs'].get('p', 0), vloc(v)) for v in des_v], on={v['n'] for v in des_v if 'Gela' in v['n'] or 'Scoop' in v['n']}),
                DM_SRC, (['Venue', 'Place', 'Dessert mentions'], [[v['n'], vloc(v), v['cs'].get('p', 0)] for v in des_v]))
           + sowhat('restaurants', f'Only {spend["Up"]} of {sum(spend.values())} operators see spend per head rising. When a venue\'s own dessert is forgettable, guests take the last spend to the gelato shop next door.'))
    recs = [('Make tiramisu and sticky toffee pudding the volume lines', f'Together {f1(tir["pct"] + stp_i["pct"])}% of {f0(p_t["n"])} dream desserts, both steady. Ready-to-plate at a quality guests notice.', 'High', 'Low', 'Next quarter'),
            ('Offer a smaller dessert at a lower price', 'Guests skip dessert to save money. A smaller format keeps the course on the bill and the spend in the venue.', 'High', 'Low', 'Next quarter'),
            ('Add a seasonal fruit and meringue line', f'Fruit and meringue rose from {f1(frm["early"])}% to {f1(frm["late"])}%, a clear move. Pavlova and Eton mess that change each quarter.', 'High', 'Medium', 'Next quarter'),
            ('Reduce baked cheesecake; test a Basque style', f'Baked cheesecake fell from {f1(chs["early"])}% to {f1(chs["late"])}%, a clear move.', 'Medium', 'Low', 'Six months'),
            ('Do not build a range on viral flavours', f'Dubai chocolate draws {binx.get("Dubai chocolate", 0)} "bin it" mentions and pistachio-everything {binx.get("Pistachio (everything)", 0)}.', 'Medium', 'Low', 'Now')]
    return render(dict(slug='dessert', ex=ex, status='sample', aud='supplier venue', **META['dessert'],
        title='The last spend: <em>dessert</em>', desc='Which desserts guests still choose, what is rising and falling, and what a dessert range should look like.',
        stand='Dessert is the course guests cut first when money is tight. This report asks which desserts still earn their place, what is moving, and what to stop making.',
        client='A dessert maker or foodservice supplier', question='Which desserts still earn their place on the bill?', evidence=f'{f0(p_t["n"])} dream desserts, operator survey, "bin it" answers',
        kpis=[(f'{f1(tir["pct"])}%', 'name tiramisu, the top dessert'), (f'{f1(stp_i["pct"])}%', 'name sticky toffee pudding'), (f'{f1(CONC["p"]["top1v"])}%', 'leading group share, the lowest of any course'), (f'{spend["Up"]} of {sum(spend.values())}', 'operators see spend per head rising')],
        answer='Two classics carry the volume and fruit is the clear riser, so a dessert range should lead with tiramisu and sticky toffee pudding, add a seasonal fruit line, and offer a smaller format so the course stays on the bill.',
        msgs=[(f'{f1(tir["pct"] + stp_i["pct"])}%', 'of desserts', 'Two classics carry the course', 'Tiramisu and sticky toffee pudding, both steady over six quarters.'),
              (pts(frm['move']), 'pts', 'Fruit is the clear riser', f'Fruit and meringue rose from {f1(frm["early"])}% to {f1(frm["late"])}%; baked cheesecake fell {abs(chs["move"]):.1f} points.'),
              (str(binx.get('Dubai chocolate', 0)), 'mentions', 'Novelty chocolate is tired', 'Dubai chocolate is the second most-named trend guests want gone.')],
        chapters=[('course', 'The course', 'Two classics, then an open field', 'What guests choose for dessert, and how fragmented the course is against the others.', ch1),
                  ('moves', 'What is moving', 'Fruit is up, cheesecake down, novelty chocolate tired', 'Early against recent, and what guests want gone.', ch2),
                  ('spend', 'The spend', 'The last spend walks next door', 'What operators see, and where guests go instead.', ch3)],
        recs=recs,
        watch=[('Spend per head', 'If the next operator survey shows spend per head recovering, the smaller-format dessert matters less and premium lines matter more.'),
               ('Fruit and meringue', 'Fruit is seasonal. Two more quarters including winter will show whether the rise holds outside summer.'),
               ('Chocolate desserts', f'Chocolate desserts are drifting down ({f1(choc["early"])}% to {f1(choc["late"])}%) without a clear move yet.'),
               ('Late-night dessert', 'A documented concept gap in Glasgow. A late-night dessert venue gaining mentions would confirm demand.')],
        method_stats=[(f0(p_t['n']), 'dream desserts'), (str(len(LOOK)), 'operators surveyed'), (f0(sum(v for _, v in BIN)), '"bin it" mentions (top 10)'), ('6', 'quarters tracked')],
        method='<p>Dessert shares use interviews with a codable dessert answer. The operator survey ran 2 April to 3 May 2026. "Bin it" answers are unprompted and grouped into published labels.</p>',
        card=(f'{f1(tir["pct"])}%', 'of dream desserts are tiramisu'),
        blurb='The most open course on the menu: what guests choose, what is moving and where a supplier can protect the last spend.'))


# ================================================================== 05 drinks
def r_drinks():
    ex = Ex()
    ck, sp, bc = (item('a', n, 'groups') for n in ('Cocktails', 'Spirits', 'Beer and cider'))
    wh, lg_ = item('a', 'Whisky'), item('a', 'Lager')
    sig = sig_set('a')
    coke, tea, water, pine = DEB['coke'], DEB['tea'], DEB['water'], DEB['pineapple']
    db_rows = [(g['c'], g['early'], g['late']) for g in a_t['groups']] + [(it['l'], it['early'], it['late']) for it in a_t['cats'][:12] if abs(it['move']) >= 1.5]
    q5 = Q[:5]
    deb = lambda d, order: [(k.replace('Coca Cola', 'Coca-Cola'), d['c'][k], kk) for k, kk in order if k in d['c']]
    ch1 = (ex(f'Cocktails have lost {abs(ck["move"]):.0f} points of share; spirits, beer and whisky took it', 'Share of dream alcoholic drinks, early against recent.',
              dumbbell(db_rows, sig=sig),
              f'{DM_SRC}. Trend tests use the original single drink question, before it split on 23 August 2026', (['Drink', EARLY, RECENT, 'Change', 'Clear?'], [[a, f'{b}%', f'{c}%', pts(c - b), 'Yes' if a in sig else 'No'] for a, b, c in db_rows]))
           + ex('Cocktails, spirits, beer and whisky by quarter', 'Share of dream alcoholic drinks each quarter, on one scale. Faded points have fewer than 100 answers.',
                small_multiples([('Cocktails', ck['share'][:5], 'k2'), ('Spirits', sp['share'][:5], 'k1'), ('Beer and cider', bc['share'][:5], 'k1'), ('Whisky', wh['share'][:5], 'k1')], q5, faded={i for i in faded('a') if i < 5}),
                DM_SRC, (['Quarter'] + q5, [[n] + [f'{v}%' for v in it['share'][:5]] for n, it in (('Cocktails', ck), ('Spirits', sp), ('Beer and cider', bc), ('Whisky', wh))]))
           + sowhat('a drinks range', f'Cocktails are still the biggest group ({f1(ck["late"])}% recently) but the long house list is the casualty. Whisky ({f1(wh["early"])}% to {f1(wh["late"])}%) and lager ({f1(lg_["early"])}% to {f1(lg_["late"])}%) are the clear gainers.'))
    ch2 = (ex('Irn Bru wins the round; coffee beats tea more than two to one', 'The debates every interview ends with. Hover a segment for the count.',
              stack([('Irn Bru or Coca-Cola?', f'{f0(coke["n"])} answering', deb(coke, [('Irn Bru', 'k1'), ('Coca Cola', 'k2'), ('Neither', 'k0')])),
                     ('Coffee or tea?', f'{f0(tea["n"])} answering', deb(tea, [('Coffee', 'k1'), ('Tea', 'k2'), ('Neither', 'k0')])),
                     ('Still, sparkling or tap?', f'{f0(water["n"])} answering', deb(water, [('Still', 'k1'), ('Sparkling', 'k2'), ('Tap', 'k3'), ('Scottish tap water', 'k0')])),
                     ('Pineapple on pizza?', f'{f0(pine["n"])} answering', deb(pine, [('Yes', 'k1'), ('No', 'k2')]))],
                    [], named=True),
              DM_SRC, (['Question', 'Answer', 'Count'], [[q, k, v] for q, d in (('Irn Bru or Coke', coke), ('Coffee or tea', tea), ('Water', water), ('Pineapple', pine)) for k, v in d['c'].items()]))
           + ex('Soft drinks lead the soft round; no and low is an eighth of it', 'Dream soft drinks by group, share.',
                hbar([(g['c'], g['pct']) for g in k_t['groups']], on={'No and low alcohol'}, unit='%', dec=1), f'{DM_SRC}; {f0(k_t["n"])} soft drink answers',
                (['Group', 'Share'], [[g['c'], f'{g["pct"]}%'] for g in k_t['groups']])))
    recs = [('Cut the house cocktail list; keep the classics', f'Cocktails fell from {f1(ck["early"])}% to {f1(ck["late"])}%, the largest clear move in the archive. Spicy margarita and martini still lead.', 'High', 'Low', 'Next menu change'),
            ('Sell whisky by the dram and the highball', f'Whisky rose from {f1(wh["early"])}% to {f1(wh["late"])}%, a clear move. A short Scottish list staff can talk about.', 'High', 'Low', 'Next quarter'),
            ('Put a premium or local lager on draught', f'Lager rose from {f1(lg_["early"])}% to {f1(lg_["late"])}%, clear. Beer and cider overall up {pts(bc["move"])} points.', 'Medium', 'Medium', 'Next quarter'),
            ('List Irn Bru and price soft drinks as margin', f'{pc(coke["c"]["Irn Bru"], coke["n"])}% choose Irn Bru over Coca-Cola. The soft round is real spend.', 'Medium', 'Low', 'Now'),
            ('Build three named alcohol-free serves', 'Guests who choose no and low name a specific drink and venue. One token mocktail undersells it.', 'Medium', 'Medium', 'Six months')]
    return render(dict(slug='drinks', ex=ex, status='sample', aud='supplier venue', **META['drinks'],
        title='What Scotland <em>drinks</em> with dinner', desc='Cocktails losing share to whisky and lager, Irn Bru against Coke, and the no and low list.',
        stand='Is the cocktail boom over? This report reads the dream alcoholic drink over time, the soft drinks guests choose, and the debates every interview ends with.',
        client='A drinks brand or wholesaler planning its on-trade range', question='Where is the on-trade drink heading in Scotland?', evidence=f'{f0(a_t["n"])} alcoholic and {f0(k_t["n"])} soft drink answers, four debates',
        kpis=[(f'{pts(ck["move"])} pts', 'cocktails, share of dream drinks'), (f'{pts(wh["move"])} pts', 'whisky, a clear rise'), (f'{pc(coke["c"]["Irn Bru"], coke["n"])}%', 'choose Irn Bru over Coca-Cola'), (f'{pc(tea["c"]["Coffee"], tea["n"])}%', 'choose coffee over tea')],
        answer='The cocktail boom is cooling, not over: guests are trading the long house list for whisky, lager and the classics, and the soft round in Scotland starts with Irn Bru.',
        msgs=[(pts(ck['move']), 'pts', 'Cocktails are losing share', f'From {f1(ck["early"])}% to {f1(ck["late"])}% of dream alcoholic drinks: the biggest clear move in the archive.'),
              (pts(sp['move']), 'pts', 'Spirits and beer are taking it', f'Spirits {f1(sp["early"])}% to {f1(sp["late"])}%, led by whisky; lager clearly up too.'),
              (f'{pc(coke["c"]["Irn Bru"], coke["n"])}%', 'Irn Bru', 'Irn Bru wins the round', f'{f0(coke["c"]["Irn Bru"])} choose Irn Bru, {f0(coke["c"]["Coca Cola"])} Coca-Cola, {f0(coke["c"]["Neither"])} neither.')],
        chapters=[('alcohol', 'The alcoholic drink', 'Cocktails are giving ground to whisky and lager', 'Early against recent, and quarter by quarter.', ch1),
                  ('round', 'The soft round', 'Irn Bru, coffee and still water win the debates', 'What guests choose when the drink is not alcoholic.', ch2)],
        recs=recs,
        watch=[('Drink question split', 'Since 23 August 2026 soft and alcoholic drinks are asked separately. Two quarters on the new questions will confirm the trend on a cleaner base.'),
               ('Negroni and martini', 'Stirred classics are rising without a clear move yet (see No. 02 for the Edinburgh lean).'),
               ('Guinness', 'Guinness and stout drifted down. A recovery in winter quarters would be seasonal, not structural.'),
               ('No and low', 'No and low fell as a share of soft drinks. Watch whether that is fatigue or an effect of the new question.')],
        method_stats=[(f0(a_t['n']), 'alcoholic drink answers'), (f0(k_t['n']), 'soft drink answers'), (f0(coke['n']), 'Irn Bru or Coke answers'), ('5', 'quarters tested')],
        method='<p>Alcoholic and soft drink shares pool the original single drink question and the two questions that replaced it on 23 August 2026; trend tests use the original question only, so the latest quarter is left out of the trend charts.</p>',
        card=(f'{pts(ck["move"])} pts', 'cocktails, share of dream alcoholic drinks'),
        blurb='The shift from cocktails to whisky and lager, the soft-drink round and the no and low question.'))


# ================================================================== 06 trend fatigue
def r_fatigue():
    ex = Ex()
    pot, veg, med = (item('d', n, 'groups') for n in ('Potatoes and fries', 'Vegetables and salad', 'Mediterranean and Middle Eastern'))
    lf, sk, mc, gr = (item('d', n) for n in ('Loaded fries', 'Skinny fries', 'Mac and cheese', 'Greens and creamed spinach'))
    sig = sig_set('d')
    hype = {'Matcha', 'Dubai chocolate', 'Filming food and mukbang', 'Viral TikTok food', 'Hot honey', 'Pistachio (everything)', 'Deconstructed and gimmick plating'}
    hype_n = sum(v for n, v in BIN if n in hype); all_n = sum(v for _, v in BIN)
    ch1 = (ex('Guests are tired of food made for the camera', 'Unprompted "bin it" mentions: the trends guests would happily see disappear. Highlighted: hype-led trends.',
              hbar([(n, v) for n, v in BIN[:10]], on=hype), f'{DM_SRC}; "bin it" question', (['Trend', 'Mentions', 'Hype-led?'], [[n, v, 'Yes' if n in hype else 'No'] for n, v in BIN[:10]]))
           + sowhat('a menu team', f'{pc(hype_n, all_n)}% of the top ten "bin it" mentions are about hype: viral flavours, filming food and gimmick plating. The fatigue is with the performance, not with any one ingredient.'))
    sides = [(g['c'], g['early'], g['late']) for g in d_t['groups'][:8]] + [(it['l'], it['early'], it['late']) for it in (sk, lf, mc, gr)]
    ch2 = (ex('The side order is moving from chips to greens', 'Share of dream sides, early against recent.',
              dumbbell(sides, sig=sig), f'{DM_SRC}. Clear move: p < 0.05', (['Side', EARLY, RECENT, 'Change', 'Clear?'], [[a, f'{b}%', f'{c}%', pts(c - b), 'Yes' if a in sig else 'No'] for a, b, c in sides]))
           + ex('Potato sides by quarter, against vegetables and Mediterranean sides', 'Share of dream sides each quarter, on one scale. Faded points have fewer than 100 answers.',
                small_multiples([('Potatoes and fries', pot['share'], 'k2'), ('Vegetables and salad', veg['share'], 'k1'), ('Mediterranean sides', med['share'], 'k1')], Q, faded=faded('d')),
                DM_SRC, (['Quarter'] + Q, [[n] + [f'{v}%' for v in it['share']] for n, it in (('Potatoes and fries', pot), ('Vegetables and salad', veg), ('Mediterranean sides', med))]))
           + sowhat('a menu team', f'Loaded fries fell from {f1(lf["early"])}% to {f1(lf["late"])}% and potato sides lost {abs(pot["move"]):.1f} points overall. Greens, salads and mezze-style sides took the space.'))
    ch3 = (ex('Comfort food is not going anywhere', 'Guilty pleasures guests admit to, mentions.',
              hbar([(n, v) for n, v in GUILTY[:10]], on={GUILTY[0][0]}), f'{DM_SRC}; guilty pleasure question', (['Guilty pleasure', 'Mentions'], [[n, v] for n, v in GUILTY[:10]]))
           + pull('Loaded fries are stupid unless you\'ve made them yourself at 3am.', 'Dream Menu guest, October 2026')
           + sowhat('venues', 'Guests want honest comfort, not comfort dressed up for the camera. A well-made classic does not need a twist.'))
    recs = [('Drop the viral special', 'Put the effort into a dish people come back for. Hype-led trends dominate the "bin it" list.', 'High', 'Low', 'Next menu change'),
            ('Make greens and salads as considered as the chips', f'Vegetable and salad sides rose from {f1(veg["early"])}% to {f1(veg["late"])}%; greens and creamed spinach clearly up.', 'High', 'Low', 'Next menu change'),
            ('Add a Mediterranean or mezze-style side', f'From {f1(med["early"])}% to {f1(med["late"])}% of dream sides, a clear move.', 'Medium', 'Low', 'Next quarter'),
            ('Keep one loaded item at most', f'Loaded fries fell from {f1(lf["early"])}% to {f1(lf["late"])}%; loaded and dirty food draws {dict(BIN).get("Loaded and dirty food", 0)} "bin it" mentions.', 'Medium', 'Low', 'Now'),
            ('Explain small plates clearly', f'Small plates appear in the "bin it" list ({dict(BIN).get("Small plates", 0)}). If that is the format, be clear on portions and price.', 'Low', 'Low', 'Now')]
    return render(dict(slug='trend-fatigue', ex=ex, status='sample', aud='venue public supplier', **META['trend-fatigue'],
        title='Trend <em>fatigue</em>', desc='The trends guests want gone, the sides they are leaving behind and what replaces them.',
        stand='Every interview asks which food trend should quietly disappear. Set against what guests actually choose, the answers show which trends are tiring and what is replacing them.',
        client='A menu development team or food editor', question='What are guests tired of, and what replaces it?', evidence=f'"Bin it" answers, {f0(d_t["n"])} dream sides, guilty pleasures',
        kpis=[(str(BIN[0][1]), f'want {BIN[0][0].lower()} gone'), (str(BIN[1][1]), f'want {BIN[1][0].lower()} gone'), (f'{pts(pot["move"])} pts', 'potato sides on dream menus'), (f'{pts(veg["move"])} pts', 'vegetable and salad sides')],
        answer='Guests are tired of food made to be posted, not of comfort: hype-led trends top the "bin it" list while chips give way to greens and mezze, and the honest classics hold.',
        msgs=[(f'{pc(hype_n, all_n)}%', 'of top-10 "bin it"', 'The fatigue is with the hype', 'Matcha, Dubai chocolate and filming food lead, with viral TikTok food close behind.'),
              (pts(pot['move']), 'pts', 'Chips are giving way', f'Potato sides fell from {f1(pot["early"])}% to {f1(pot["late"])}% of dream sides, a clear move.'),
              (str(GUILTY[0][1]), 'mentions', 'Comfort holds', f'{GUILTY[0][0]} tops the guilty pleasures, with pasta and noodles close behind.')],
        chapters=[('bin', 'What guests want gone', 'Guests are tired of food made for the camera', 'Unprompted answers to "Do you have a food trend you wish would quietly disappear?"', ch1),
                  ('sides', 'What replaces it', 'The side order is moving from chips to greens', 'What guests actually choose, early against recent.', ch2),
                  ('comfort', 'What stays', 'Comfort food is not going anywhere', 'The guilty pleasures guests admit to.', ch3)],
        recs=recs,
        watch=[('The next viral flavour', 'Hype cycles are short. A new entry climbing the "bin it" list within two quarters of peaking would confirm the pattern.'),
               ('Chips recovery', 'Potato sides fell sharply. A winter rebound would suggest seasonality rather than fatigue.'),
               ('Small plates', 'If small plates keep rising in the "bin it" list, it becomes a format risk, not just a pricing one.'),
               ('Matcha', 'Matcha leads the list. Watch whether it fades from menus or settles as a drink rather than a flavour.')],
        method_stats=[(f0(sum(v for _, v in BIN)), '"bin it" mentions (top 10)'), (f0(d_t['n']), 'dream sides'), (f0(sum(v for _, v in GUILTY)), 'guilty pleasure mentions (top 10)'), ('6', 'quarters tracked')],
        method='<p>"Bin it" and guilty pleasure answers are unprompted and grouped into published labels; one answer can name more than one trend. Side shares use interviews with a codable side answer.</p>',
        card=(str(BIN[0][1]), f'guests want {BIN[0][0].lower()} gone'),
        blurb='The trends guests want gone, the sides they are leaving behind and what replaces them.'))


# ================================================================== 07 neighbourhoods
def r_neighbourhoods():
    ex = Ex()
    AREAS = [('City centre', 55.8615, -4.2560), ('Merchant City', 55.8590, -4.2440), ('Finnieston', 55.8650, -4.2860), ('West End', 55.8750, -4.2930),
             ('Partick', 55.8700, -4.3090), ('Woodlands', 55.8680, -4.2700), ('Southside', 55.8370, -4.2680), ('Shawlands', 55.8300, -4.2830),
             ('East End', 55.8550, -4.2330), ('Dennistoun', 55.8610, -4.2130), ('Kinning Park and Govan', 55.8530, -4.3020)]
    MERGE = {'Shawlands': 'Southside', 'Dennistoun': 'East End', 'Kinning Park and Govan': 'Elsewhere in the city'}
    kmd = lambda a, b: math.hypot((a[0] - b[0]) * 111, (a[1] - b[1]) * 111 * math.cos(math.radians(55.86)))
    g = [v for v in DM['venues'] if v.get('c') == 'Glasgow' and not v.get('tw') and v['p'] in ('exact', 'street', 'neighbourhood') and v.get('la') and 55.80 < v['la'] < 55.90 and -4.37 < v['lo'] < -4.17]
    gid = {v['i'] for v in g}
    unplaced = [v for v in DM['venues'] if v.get('c') == 'Glasgow' and not v.get('tw') and v['i'] not in gid]
    agg = defaultdict(lambda: dict(v=0, m=0, h=0, names=[], k=Counter()))
    pts_ = []
    for v in g:
        d, n = min((kmd((v['la'], v['lo']), (la, lo)), n) for n, la, lo in AREAS)
        n = MERGE.get(n, n) if d < 1.6 else 'Elsewhere in the city'
        a = agg[n]; a['v'] += 1; a['m'] += v['m']; a['h'] += v.get('cs', {}).get('h', 0); a['names'].append((v['m'], v['n']))
        for kk, c in v.get('k', []):
            a['k'][kk] += c
        pts_.append((v['la'], v['lo'], v['m'], v['n'], n, n in ('Finnieston', 'Southside')))
    tot_m, tot_v = sum(a['m'] for a in agg.values()), sum(a['v'] for a in agg.values())
    areas = [n for n in sorted(agg, key=lambda n: -agg[n]['m']) if n != 'Elsewhere in the city']
    ppv = {n: agg[n]['m'] / agg[n]['v'] for n in areas}
    top3 = sum(agg[n]['m'] for n in areas[:3])
    anchor = {n: sorted(agg[n]['names'], reverse=True)[0] for n in areas}
    # label each district at the mention-weighted centre of its venues, nudged above the cluster
    cen = {}
    for la, lo, mm, nm, ar, on in pts_:
        c = cen.setdefault(ar, [0, 0, 0]); c[0] += la * (mm + 1); c[1] += lo * (mm + 1); c[2] += mm + 1
    nudge = {'City centre': (0.0040, -0.004), 'Merchant City': (-0.0045, 0.006), 'Finnieston': (0.0042, 0.0), 'West End': (0.0042, 0.0), 'Partick': (0.0035, -0.004),
             'Woodlands': (0.0040, 0.006), 'Southside': (-0.0062, 0.0), 'East End': (-0.0042, 0.008)}
    zones = [(n, cen[n][0] / cen[n][2] + nudge.get(n, (0.004, 0))[0], cen[n][1] / cen[n][2] + nudge.get(n, (0.004, 0))[1]) for n in areas]
    hid = {n: 100 * agg[n]['h'] / agg[n]['m'] for n in areas if agg[n]['m'] >= 40}
    big = [n for n in areas if agg[n]['v'] >= 15]
    ch1 = (ex('Glasgow\'s food conversation runs along one line, from the Merchant City to Finnieston', f'Every Glasgow venue guests have named with a known address ({f0(tot_v)}), sized by mentions. Highlighted: Finnieston and the Southside. Hover for names.',
              glasgow_map(pts_, zones), f'{DM_SRC}; venue locations from guest answers and address research. River line approximate; a few outlying venues fall outside the frame.',
              (['Neighbourhood', 'Venues', 'Mentions'], [[n, agg[n]['v'], agg[n]['m']] for n in areas]))
           + ex(f'Three districts hold {pc(top3, tot_m)}% of mentions', 'Share of venue mentions by neighbourhood; the note shows its share of venues.',
                hbar([(n, 100 * agg[n]['m'] / tot_m, f'{agg[n]["v"]} venues, {pc(agg[n]["v"], tot_v)}% of all') for n in areas], on=set(areas[:3]), unit='%', dec=1),
                DM_SRC, (['Neighbourhood', 'Share of mentions', 'Share of venues'], [[n, f'{100 * agg[n]["m"] / tot_m:.1f}%', f'{100 * agg[n]["v"] / tot_v:.1f}%'] for n in areas])))
    ch2 = (ex('Finnieston and the Southside draw the most mentions per venue', 'Average guest mentions per named venue, by neighbourhood (15 or more venues).',
              hbar([(n, ppv[n]) for n in sorted(big, key=lambda n: -ppv[n])], on={'Finnieston', 'Southside'}, dec=1),
              DM_SRC, (['Neighbourhood', 'Mentions per venue', 'Venues'], [[n, f'{ppv[n]:.1f}', agg[n]['v']] for n in sorted(areas, key=lambda n: -ppv[n])]))
           + ex('Destination venues make districts', 'Share of each neighbourhood\'s mentions held by its most-named venue.',
                hbar([(n, 100 * anchor[n][0] / agg[n]['m'], anchor[n][1]) for n in sorted(big, key=lambda n: -anchor[n][0] / agg[n]['m'])], on={'Southside', 'West End'}, unit='%', dec=0),
                DM_SRC, (['Neighbourhood', 'Anchor venue', 'Anchor mentions', 'Share'], [[n, anchor[n][1], anchor[n][0], f'{pc(anchor[n][0], agg[n]["m"])}%'] for n in areas]))
           + sowhat('a landlord or developer', f'High mentions per venue with a single strong anchor is the signature of a district on the way up. The Southside has both: {ppv["Southside"]:.1f} mentions per venue and {anchor["Southside"][1]} holding {pc(anchor["Southside"][0], agg["Southside"]["m"])}% of them.'))
    ch3 = (ex('The insider districts: where guests name their hidden gems', 'Hidden-gem and next-stop answers as a share of each area\'s mentions (40 or more mentions).',
              hbar(sorted(hid.items(), key=lambda x: -x[1]), on={n for n, v in hid.items() if v >= 30}, unit='%', dec=0),
              f'{DM_SRC}; "favourite hidden gem" and "next stop" questions', (['Neighbourhood', 'Hidden-gem share'], [[n, f'{v:.0f}%'] for n, v in sorted(hid.items(), key=lambda x: -x[1])]))
           + table(['Neighbourhood', 'Venues', 'Mentions', 'Most-named venues', 'What guests name there'],
                   [[f'<b>{esc(n)}</b>', agg[n]['v'], agg[n]['m'], esc(', '.join(x[1] for x in sorted(agg[n]['names'], reverse=True)[:3])), esc(', '.join(k for k, _ in agg[n]['k'].most_common(3)))] for n in areas], num_cols=(1, 2)))
    recs = [('Prioritise Southside units for food-led tenants', f'{ppv["Southside"]:.1f} mentions per venue, one of the two highest in the city, with a high hidden-gem share: demand ahead of supply.', 'High', 'Medium', 'Next 12 months'),
            ('Lead with one destination tenant per street', f'Anchors carry a large share of their districts ({anchor["Southside"][1]}, {anchor["West End"][1]}). A destination venue lifts the units around it.', 'High', 'High', 'Leasing strategy'),
            ('Take early positions in the East End', 'The Barras area has a high share of hidden-gem answers. Pair units with the market and events while rents allow.', 'Medium', 'Medium', '12 to 24 months'),
            ('Use the city centre for brand-led concepts', f'The centre has the most venues and mentions but fewer per venue ({ppv["City centre"]:.1f}): volume, diluted. It suits known brands.', 'Medium', 'Low', 'Ongoing'),
            ('Track district momentum quarterly', 'Mentions per venue and hidden-gem share by area, every quarter, so the next district shows before rents move.', 'Medium', 'Low', 'Quarterly')]
    return render(dict(slug='neighbourhoods', ex=ex, status='sample', aud='investor venue public', **META['neighbourhoods'],
        title='Where <em>Glasgow</em> eats', desc='A neighbourhood read of Glasgow\'s food scene: where guest attention sits, which districts punch above their weight and where the next one is.',
        stand='Which Glasgow districts do guests talk about, which punch above their weight, and where is the next Finnieston? A location read built from every venue guests have named.',
        client='A property developer or landlord with food and drink units', question='Which neighbourhoods should we lease to food and drink operators next?', evidence=f'{f0(tot_v)} mapped Glasgow venues, {f0(tot_m)} mentions',
        kpis=[(f'{pc(top3, tot_m)}%', 'of mentions in three districts'), (f'{ppv["Finnieston"]:.1f}', 'mentions per venue in Finnieston'), (f'{ppv["Southside"]:.1f}', 'mentions per venue in the Southside'), (f'{ppv["City centre"]:.1f}', 'in the city centre, for comparison')],
        answer='Guest attention is concentrated between the Merchant City and Finnieston, but the Southside matches Finnieston on mentions per venue and has more of the hidden-gem answers: it is the district to lease into next.',
        msgs=[(f'{pc(top3, tot_m)}%', 'of mentions', 'One line holds the conversation', f'{areas[0]}, {areas[1]} and {areas[2]} hold {pc(top3, tot_m)}% of mentions of mapped Glasgow venues.'),
              (f'{ppv["Southside"]:.1f}', 'per venue', 'The Southside punches above its weight', f'Against {ppv["City centre"]:.1f} in the city centre; only Finnieston is comparable.'),
              (f'{pc(anchor["Southside"][0], agg["Southside"]["m"])}%', 'anchor share', 'Destinations make districts', f'{anchor["Southside"][1]} alone holds {pc(anchor["Southside"][0], agg["Southside"]["m"])}% of Southside mentions.')],
        chapters=[('map', 'The map', 'Glasgow\'s food conversation runs along one line', 'Where every named venue sits, and how attention splits by district.', ch1),
                  ('value', 'Value per venue', 'Finnieston and the Southside punch above their weight', 'Mentions per venue, and how much each district depends on one destination.', ch2),
                  ('districts', 'District profiles', 'The insider districts are where the next Finnieston comes from', 'Where guests name their hidden gems, and what each area is known for.', ch3)],
        recs=recs,
        watch=[('Rents and vacancy', 'Dream Menu measures demand, not rent. A commission would pair this read with agent data on rents and vacant units by street.'),
               ('Anchor risk', 'Districts that depend on one venue are exposed if it closes or moves. Watch anchor share alongside mentions.'),
               ('New openings', 'A new venue entering an area\'s top three within two quarters is the earliest sign of momentum.'),
               (f'{len(unplaced)} venues without an address', f'Some guests name a venue without enough detail to place it ({f0(sum(v["m"] for v in unplaced))} mentions). Address research would sharpen the read.')],
        method_stats=[(f0(tot_v), 'Glasgow venues mapped'), (f0(tot_m), 'mentions'), (str(len(areas)), 'districts'), (f0(len(unplaced)), 'venues not placed')],
        method='<p>Venues are those guests named in Glasgow with an exact address or a named street or neighbourhood, inside the city. Each is assigned to the nearest of eleven district centre points within 1.6 km (the Southside includes Govanhill, Strathbungo and Shawlands; the East End includes the Barras and Dennistoun; Woodlands includes Charing Cross); the rest are "elsewhere". Boundaries are indicative. Hidden-gem share counts mentions from the "favourite hidden gem" and "next stop" questions.</p>',
        card=(f'{ppv["Southside"]:.1f}', 'mentions per venue in the Southside'),
        blurb='Where guest attention sits in Glasgow, which districts punch above their weight, and where the next Finnieston is.'))


# ================================================================== 08 guests and critics
def r_critics():
    ex = Ex()
    c = AN['critics']; T = c['tops']
    allk = str(c['venues'])
    bands = [('Top 10', T['10']), ('Top 25', T['25']), ('Top 50', T['50']), ('Top 100', T['100']), ('All named venues', T[allk])]

    def tier_of(p):
        if p['tier'] in ('AA Rosettes', 'Other guides'):
            return 'Other guides'
        return {'One star': 'MICHELIN Star'}.get(p['tier'], p['tier'])
    tiers = [('MICHELIN Star', 'k1'), ('Bib Gourmand', 'k1'), ('MICHELIN selected', 'k3'), ('Other guides', 'k3'), ('No guide award', 'k2')]
    rows = [(lbl, k, [(p['m'], f'<b>{esc(p["n"])}</b><br>{esc(p["c"])}<br>{p["m"]} mentions, rank {p["rank"]}<br>{esc(", ".join(p["aw"]) or "No guide award")}') for p in c['points'] if tier_of(p) == lbl]) for lbl, k in tiers]
    un = [p for p in c['points'] if not p['aw']][:12]
    stars = [p for p in c['points'] if any('Star' in a for a in p['aw'])]
    bib_top = [p for p in c['points'][:25] if p['tier'] == 'Bib Gourmand']
    scot_star = sum(1 for p in AW['places'] if p[6] == 'Scotland' and any(AW['groups'][a[0]] == 'star' for a in p[10]))
    aw_named = sum(1 for p in AW['places'] if p[15])
    allshare = 100 * T[allk]['award'] / T[allk]['n']
    ch1 = (ex(f'Guest favourites are far likelier to hold a guide award, yet most do not', 'Share of venues holding any guide award (MICHELIN, 50 Best, AA, Good Food Guide), by guest popularity.',
              hbar([(b, 100 * v['award'] / v['n'], f'{v["award"]} of {v["n"]}') for b, v in bands], on={'Top 25'}, unit='%', dec=0),
              f'{DM_SRC}; awards from the Dream Menu awards list', (['Band', 'With an award', 'Venues', 'Share'], [[b, v['award'], v['n'], f'{100 * v["award"] / v["n"]:.0f}%'] for b, v in bands]))
           + sowhat('a tourism body', f'The guides and the guests agree more than chance would suggest ({pc(T["25"]["award"], 25)}% of the top 25 against {allshare:.0f}% overall), but {100 - T["100"]["award"]} of the hundred venues guests name most hold no guide award at all. A visitor following only the guides misses most of what locals love.'))
    ch2 = (ex('Bib Gourmand is where guests and inspectors meet; stars sit further down the list', f'The {len(c["points"])} venues guests name most, by guide status. Across: guest mentions (square-root scale). Hover for each venue.',
              strip(rows, max(p['m'] for p in c['points']), 'Guest mentions'),
              DM_SRC, (['Status', 'Venues in the top ' + str(len(c['points'])), 'Highest-ranked'], [[lbl, len(px), next((p['n'] for p in c['points'] if tier_of(p) == lbl), '')] for lbl, _, px in rows]))
           + f'<div class="prose"><p>{len(bib_top)} of the 25 most-named venues hold a Bib Gourmand ({esc(", ".join(p["n"] for p in bib_top))}). The starred venues guests name ({esc(", ".join(p["n"] for p in stars))}) sit between ranks {min(p["rank"] for p in stars)} and {max(p["rank"] for p in stars)}: admired, but named less often than the city\'s casual favourites.</p></div>')
    ch3 = (ex('The unrecognised favourites', 'The most-named venues with no guide award.',
              hbar([(p['n'], p['m'], p['c']) for p in un], on={un[0]['n']}), DM_SRC, (['Venue', 'City', 'Mentions', 'Rank'], [[p['n'], p['c'], p['m'], p['rank']] for p in un]))
           + sowhat('press and city marketing', f'{un[0]["n"]} is the most-named venue in the archive and holds no guide award. A guest favourites list alongside the guides gives visitors and press the local view.'))
    recs = [('Publish a guest favourites trail beside the guides', f'{100 - T["100"]["award"]} of the top 100 named venues hold no guide award. A trail built from guest mentions fills the gap the guides leave.', 'High', 'Medium', 'Next season'),
            ('Use Bib Gourmand as the bridge', f'{len(bib_top)} of the top 25 hold a Bib Gourmand: the award guests and inspectors agree on most. Lead visitor food campaigns with it.', 'High', 'Low', 'Now'),
            ('Pitch the unrecognised favourites to press', f'Start with {", ".join(p["n"] for p in un[:3])}: high guest advocacy, no guide coverage.', 'Medium', 'Low', 'Now'),
            ('Tell venues awards are not the only route', 'Most guest favourites built their reputation without a guide award. Operator support should value word of mouth as much as inspection.', 'Medium', 'Low', 'Ongoing'),
            ('Re-run the overlap each year', 'When the 2027 guides publish, measure it again: a rising share means the guides are catching up with guests.', 'Low', 'Low', 'Annually')]
    return render(dict(slug='guests-and-critics', ex=ex, status='sample', aud='public venue investor', **META['guests-and-critics'],
        title='Guests and <em>critics</em>', desc='How far guest favourites and guide award winners overlap, where they meet and the favourites the guides miss.',
        stand='Do the guides and the guests agree? This study sets the venues Dream Menu guests name most against MICHELIN, 50 Best, AA and Good Food Guide awards.',
        client='A city marketing or tourism body', question='Should we promote guide winners, guest favourites, or both?', evidence=f'{f0(c["venues"])} named venues, {f0(AW["meta"]["places"])} award winners',
        kpis=[(f'{pc(T["25"]["award"], 25)}%', 'of the top 25 named venues hold a guide award'), (f'{allshare:.0f}%', 'of all named venues do'), (str(100 - T['100']['award']), 'of the top 100 have no award at all'), (str(scot_star), 'MICHELIN-starred venues in Scotland')],
        answer='Guests and critics agree more than chance would suggest, especially on Bib Gourmand, but most guest favourites hold no guide award, so a visitor offer built only on the guides misses most of what locals love.',
        msgs=[(f'{pc(T["25"]["award"], 25)}%', 'of top 25', 'Favourites are likelier to be recognised', f'Against {allshare:.0f}% of all named venues.'),
              (str(len(bib_top)), 'of top 25', 'Bib Gourmand is the bridge', 'Casual, good-value cooking is where inspectors and guests agree.'),
              (str(100 - T['100']['award']), 'of top 100', 'Most favourites are unrecognised', f'Led by {un[0]["n"]}, the most-named venue in the archive.')],
        chapters=[('overlap', 'The overlap', 'Favourites are likelier to be recognised, but most are not', 'Guide awards by guest popularity band.', ch1),
                  ('tiers', 'Where they meet', 'Bib Gourmand is where guests and inspectors agree', 'The most-named venues, laid out by guide status.', ch2),
                  ('unrecognised', 'The gap', 'The favourites the guides miss', 'High guest advocacy, no guide award.', ch3)],
        recs=recs,
        watch=[('2027 guide editions', 'MICHELIN Great Britain and Ireland 2027 publishes early in 2027. New Scottish stars or Bibs among guest favourites would narrow the gap.'),
               ('Visit frequency', 'Guests name places they go often; tasting-menu venues are visited less. A commission could weight by visit frequency.'),
               ('Beyond Glasgow', 'Most named venues are in Glasgow. Targeted fieldwork elsewhere would test whether the pattern holds.'),
               ('Award inflation', 'If guide selections expand, overlap rises without guests changing their minds. Track awards and mentions together.')],
        method_stats=[(f0(c['venues']), 'named venues compared'), (f0(AW['meta']['places']), 'award winners on the list'), (str(aw_named), 'award venues guests name'), (str(len(c['points'])), 'top venues plotted')],
        method='<p>Each venue guests name is matched to the Dream Menu awards list (MICHELIN 2026 editions, the 50 Best lists, AA Rosettes, the Good Food Guide and others; see the <a href="/awards">award winners</a> page). "Any guide award" includes MICHELIN selected. Bands are by number of guest mentions.</p>',
        card=(str(100 - T['100']['award']), 'of the top 100 guest favourites have no guide award'),
        blurb='How far guest favourites and guide award winners overlap, where they meet and the favourites the guides miss.'))


# ================================================================== 09 steak
def r_steak():
    ex = Ex()
    sb = item('m', 'Steak and beef', 'groups')
    cuts = [it for it in m_t['cats'] if it.get('g') == 'Steak and beef']
    sr, rb, fl, pie = item('m', 'Short rib and braised beef'), item('m', 'Ribeye steak'), item('m', 'Fillet steak'), item('m', 'Steak pie')
    tart = item('s', 'Steak tartare and carpaccio')
    gr, tc, sk, tf = item('d', 'Greens and creamed spinach'), item('d', 'Triple-cooked chips'), item('d', 'Skinny fries'), item('d', 'Truffle fries')
    sig = sig_set('m') | sig_set('d')
    others = [g for g in m_t['groups'] if g['c'] != 'Steak and beef'][:4]
    sv = sorted(DM['venues'], key=lambda v: -cat_count(v, 'Steak / beef'))[:10]
    db_rows = [(sb['c'] + ' (group)', sb['early'], sb['late'])] + [(it['l'], it['early'], it['late']) for it in cuts]
    sides = [(it['l'], it['early'], it['late']) for it in (gr, tc, sk, tf)]
    ch1 = (ex('A quarter of all dream mains are steak or beef, the largest main course group', 'Share of dream mains by food group.',
              hbar([(sb['c'], sb['pct'])] + [(g['c'], g['pct']) for g in others], on={'Steak and beef'}, unit='%', dec=1),
              f'{DM_SRC}; {f0(m_t["n"])} mains', (['Group', 'Share', 'Answers'], [[g['c'], f'{g["pct"]}%', g['n']] for g in [sb] + others]))
           + ex('Guests name the cut, and the braise is catching the fillet', 'Dream beef mains by cut, mentions. Highlighted: the risers.',
                hbar([(it['l'], it['n']) for it in cuts], on={'Short rib and braised beef', 'Ribeye steak', 'Steak pie'}),
                DM_SRC, (['Cut', 'Mentions', 'Share of mains'], [[it['l'], it['n'], f'{it["pct"]}%'] for it in cuts])))
    ch2 = (ex('Flavour cuts and the steak pie are rising; fillet is slipping', 'Share of dream mains, early against recent.',
              dumbbell(db_rows, sig=sig),
              f'{DM_SRC}. Clear move: p < 0.05', (['Cut', EARLY, RECENT, 'Change', 'Clear?'], [[a, f'{b}%', f'{c}%', pts(c - b), 'Yes' if a in sig else 'No'] for a, b, c in db_rows]))
           + ex('Beef mains by quarter: the group, short rib, ribeye and steak pie', 'Share of dream mains each quarter, on one scale. Faded points have fewer than 100 answers.',
                small_multiples([('Steak and beef', sb['share'], 'k1'), ('Short rib', sr['share'], 'k1'), ('Ribeye', rb['share'], 'k1'), ('Steak pie', pie['share'], 'k1')], Q, faded=faded('m')),
                DM_SRC, (['Quarter'] + Q, [[n] + [f'{v}%' for v in it['share']] for n, it in (('Steak and beef', sb), ('Short rib', sr), ('Ribeye', rb), ('Steak pie', pie))]))
           + sowhat('a beef supplier', f'Guests are trading towards flavour: short rib ({f1(sr["early"])}% to {f1(sr["late"])}%), ribeye ({f1(rb["early"])}% to {f1(rb["late"])}%) and steak pie ({f1(pie["early"])}% to {f1(pie["late"])}%, a clear move) are rising while fillet slips ({f1(fl["early"])}% to {f1(fl["late"])}%). Those are typically the cuts with the better margin per plate.'))
    ch3 = ('<div class="ex-pair"><div>' + ex('The steakhouse venues guests name', 'Beef and steak mentions by venue.',
              hbar([(v['n'], cat_count(v, 'Steak / beef'), vloc(v)) for v in sv], on={sv[0]['n'], sv[1]['n']}), DM_SRC,
              (['Venue', 'Place', 'Beef mentions'], [[v['n'], vloc(v), cat_count(v, 'Steak / beef')] for v in sv])) + '</div><div>'
           + ex('Greens are rising as the steak side; chips hold', 'Share of dream sides, early against recent.',
                dumbbell(sides, sig=sig), DM_SRC, (['Side', EARLY, RECENT], [[a, f'{b}%', f'{c}%'] for a, b, c in sides])) + '</div></div>'
           + sowhat('venues', f'The steak plate is changing around the meat: greens and creamed spinach rose from {f1(gr["early"])}% to {f1(gr["late"])}% of dream sides, a clear move. Steak tartare and carpaccio hold {f1(tart["pct"])}% of starters.'))
    recs = [('Lead the range with flavour cuts', 'Short rib and ribeye are rising; fillet is slipping. Flavour cuts deliver the experience guests name at a better cost per plate.', 'High', 'Low', 'Next quarter'),
            ('Supply a premium steak pie', f'Steak pie rose from {f1(pie["early"])}% to {f1(pie["late"])}% of dream mains, a clear move. A named-beef pie for pubs and bistros.', 'High', 'Medium', 'Next quarter'),
            ('Package braises for small kitchens', 'Short rib is a braise: pre-cooked, portioned short rib lets small kitchens put it on without the labour.', 'Medium', 'Medium', 'Six months'),
            ('Sell the plate, not just the cut', 'Pair beef with greens and creamed spinach, the clear riser among sides. A costed steak-plate card for chefs.', 'Medium', 'Low', 'Next quarter'),
            ('Target the venues guests already name', f'Start with {sv[0]["n"]}, {sv[1]["n"]} and {sv[2]["n"]}, and the steakhouses that follow them.', 'Medium', 'Low', 'Now')]
    return render(dict(slug='steak', ex=ex, status='sample', aud='supplier venue', **META['steak'],
        title='The <em>steak</em> economy', desc='Steak and beef on the dream menu: the cuts guests name, what is rising, the sides that go with them and the venues that own them.',
        stand='Steak is the largest single idea on the main course. This report reads the cuts guests name, the quiet shift from fillet to flavour, and the plate around the meat.',
        client='A beef supplier or butcher selling to restaurants', question='Which cuts and products should we push to restaurants next?', evidence=f'{f0(m_t["n"])} mains, {f0(d_t["n"])} sides, venue mentions',
        kpis=[(f'{f1(sb["pct"])}%', 'of dream mains are steak or beef'), (f'{pts(sb["move"])} pts', 'beef mains, early against recent'), (f'{pts(pie["move"])} pts', 'steak pie, a clear rise'), (f'{pts(fl["move"])} pts', 'fillet, slipping')],
        answer='Steak is the biggest main course idea and still growing, but guests are moving from fillet to flavour cuts, braises and the steak pie, so the range should follow the flavour.',
        msgs=[(f'{f1(sb["pct"])}%', 'of mains', 'Beef leads the main course', f'{f0(sb["n"])} of {f0(m_t["n"])} dream mains, rising from {f1(sb["early"])}% to {f1(sb["late"])}% (not yet a clear move).'),
              (pts(pie['move']), 'pts', 'The steak pie is back', f'From {f1(pie["early"])}% to {f1(pie["late"])}% of mains: a clear move.'),
              (pts(fl['move']), 'pts', 'Fillet is slipping', 'Short rib and ribeye rise as fillet falls: guests are trading to flavour.')],
        chapters=[('main', 'The main course', 'A quarter of dream mains are steak or beef', 'Where beef sits against every other main course group, and the cuts guests name.', ch1),
                  ('cuts', 'The cuts', 'Guests are trading from fillet to flavour', 'Early against recent, and quarter by quarter.', ch2),
                  ('plate', 'The plate and the venues', 'Greens are the new steak side', 'The venues guests name for beef, and what goes beside it.', ch3)],
        recs=recs,
        watch=[('Beef prices', 'If wholesale beef prices rise, the shift to braises and pies may speed up; a commission would pair this read with price data.'),
               ('The beef group', f'Beef mains are up {pts(sb["move"])} points without a clear move yet (p = {sb["p"]}). One more strong quarter would confirm it.'),
               ('Fillet', 'A continued fall would make fillet a special-occasion cut rather than a menu staple.'),
               ('Plant-based mains', 'Vegetable sides are rising. Watch whether that reaches the main course and takes share from beef.')],
        method_stats=[(f0(m_t['n']), 'dream mains'), (f0(sb['n']), 'beef and steak mains'), (f0(sum(cat_count(v, 'Steak / beef') for v in DM['venues'])), 'beef venue mentions'), ('6', 'quarters tracked')],
        method='<p>Main and side shares use interviews with a codable answer for that course. "Steak (cut not named)" covers answers naming steak without a cut.</p>',
        card=(f'{f1(sb["pct"])}%', 'of dream mains are steak or beef'),
        blurb='The cuts guests name, the shift from fillet to flavour, the steak plate and the venues that own it.'))


# ================================================================== 10 Italian
def r_italian():
    ex = Ex()
    si, mi = item('s', 'Pasta and Italian', 'groups'), item('m', 'Pasta and Italian', 'groups')
    tir = item('p', 'Tiramisu'); br = item('s', 'Bruschetta')
    it_cats = [it for it in s_t['cats'] + m_t['cats'] if it.get('g') in ('Pasta and Italian', 'Pizza')]
    tg = city_row('Tiramisu')
    G = dict(GUILTY)
    ital = ['Sugo Pasta', 'Margo', 'Malocchio', "Celino's Partick", 'Santa Lucia Merchant City Glasgow', 'Paesano Pizza West End', 'Eleven Fifty Five', 'Grosso', 'La Lanterna', "Celentano's", 'Casa Italian Kitchen', 'Sannio Italian Restaurant & Bar']
    byn = {v['n']: v for v in DM['venues']}
    iv = sorted([byn[n] for n in ital if n in byn], key=lambda v: -v['m'])
    top30 = AN['critics']['points'][:30]
    it_top = [p for p in top30 if p['n'] in ital]
    touch = [('Dream starters: pasta and Italian', si['pct']), ('Dream mains: pasta and Italian', mi['pct']), ('Dream desserts: tiramisu alone', tir['pct'])]
    db_rows = [(it['l'], it['early'], it['late']) for it in it_cats] + [('Pasta and Italian starters (group)', si['early'], si['late']), ('Pasta and Italian mains (group)', mi['early'], mi['late'])]
    ch1 = (ex('Italian appears on every course, and wins dessert outright', 'Share of each course that is Italian.',
              hbar(touch, on={'Dream desserts: tiramisu alone'}, unit='%', dec=1), DM_SRC, (['Course', 'Share'], [[a, f'{b}%'] for a, b in touch]))
           + ex('Italian is also Scotland\'s comfort food', 'Guilty pleasures guests admit to. Highlighted: Italian.',
                hbar([(n, v) for n, v in GUILTY[:8]], on={'Takeaway pizza', 'Spag bol and tomato pasta', "Domino's"}), f'{DM_SRC}; guilty pleasure question',
                (['Guilty pleasure', 'Mentions'], [[n, v] for n, v in GUILTY[:8]])))
    ch2 = (ex(f'{len(it_top)} of the 30 most-named venues in the archive are Italian', 'Guest mentions of Italian venues.',
              hbar([(v['n'].replace(' Merchant City Glasgow', ''), v['m'], vloc(v)) for v in iv[:10]], on={iv[0]['n'], iv[1]['n']}), DM_SRC,
              (['Venue', 'Place', 'Mentions'], [[v['n'], vloc(v), v['m']] for v in iv]))
           + ex('Tiramisu is a Glasgow habit', 'Tiramisu index by market (100 = average), markets with enough mentions to read.',
                hbar([(m, tg['cells'][i]['idx']) for i, m in enumerate(CM['markets']) if not tg['cells'][i]['thin']], on={'Glasgow'}),
                DM_SRC, (['Market', 'Share', 'Index'], [[m, f'{tg["cells"][i]["share"]}%', tg['cells'][i]['idx']] for i, m in enumerate(CM['markets'])]))
           + quotes([('Tiramisu from Celino\'s in Partick. Honourable mention goes to the chocolate cheesecake my fiancée made.', 'Dream Menu guest'), ('Classic Tiramisu from Celino\'s in Partick!', 'Dream Menu guest'), ('Tiramisu from Paesano.', 'Dream Menu guest')]))
    ch3 = (ex('Inside Italian: pasta leads, pizza is comfort, bruschetta is rising', 'Italian and pizza dishes on dream starters and mains, early against recent.',
              dumbbell(db_rows, sig=sig_set('s') | sig_set('m')),
              DM_SRC, (['Dish', EARLY, RECENT, 'Change'], [[a, f'{b}%', f'{c}%', pts(c - b)] for a, b, c in db_rows]))
           + sowhat('an Italian operator', f'The Italian share is steady rather than growing ({f1(mi["early"])}% to {f1(mi["late"])}% of mains), so growth comes from taking share within it. The venues that win are specialists: fresh pasta (Sugo), one great tiramisu (Celino\'s), a clear point of view (Margo).'))
    recs = [('Specialise: one thing done best', f'The Italian winners are specialists. {iv[0]["n"]} ({iv[0]["m"]} mentions) does fresh pasta; Celino\'s is named for tiramisu.', 'High', 'Medium', 'Concept stage'),
            ('Make the tiramisu famous', f'Tiramisu is {f1(tir["pct"])}% of all dream desserts and indexes {tg["cells"][GI]["idx"]} in Glasgow. A named signature tiramisu is the cheapest reputation an Italian venue can buy.', 'High', 'Low', 'Now'),
            ('Lift the cheque with small Italian starters', f'Bruschetta rose from {f1(br["early"])}% to {f1(br["late"])}% of starters.', 'Medium', 'Low', 'Next menu change'),
            ('Treat pizza as comfort, priced as such', f'Takeaway pizza is the top guilty pleasure ({G.get("Takeaway pizza", 0)}). Pizza wins on comfort and value, not on gourmet pricing.', 'Medium', 'Low', 'Now'),
            ('For importers: sell to the specialists', 'Supply named-origin pasta flour, guanciale and mascarpone to the venues guests already name for Italian.', 'Medium', 'Medium', 'Next quarter')]
    return render(dict(slug='italian', ex=ex, status='sample', aud='venue supplier investor', **META['italian'],
        title="Glasgow's <em>Italian</em> table", desc='Italian food on the dream menu: every course, the comfort end, the venues guests name and how specialists win.',
        stand='Glasgow has loved Italian food for a century. This report shows where it sits on the dream menu today, from the tiramisu to the takeaway pizza, and how the venues that win are doing it.',
        client='An Italian restaurant group or Italian food importer', question='How does an Italian venue win in Glasgow now?', evidence=f'{f0(s_t["n"])} starters, {f0(m_t["n"])} mains, {f0(p_t["n"])} desserts, venue mentions',
        kpis=[(f'{f1(tir["pct"])}%', 'of dream desserts are tiramisu'), (str(tg['cells'][GI]['idx']), 'Glasgow tiramisu index'), (f'{len(it_top)} of 30', 'most-named venues are Italian'), (str(G.get('Takeaway pizza', 0)), 'name takeaway pizza as a guilty pleasure')],
        answer='Italian is on every course and owns dessert, but the share is steady, not growing, so the venues that win are specialists with one thing done better than anyone: fresh pasta, a famous tiramisu, a clear point of view.',
        msgs=[(f'{f1(tir["pct"])}%', 'of desserts', 'Tiramisu owns dessert', f'The top dessert in the archive, indexing {tg["cells"][GI]["idx"]} in Glasgow.'),
              (f'{len(it_top)} of 30', 'top venues', 'Specialists lead', f'{iv[0]["n"]}, {iv[1]["n"]} and {iv[2]["n"]} are among the most-named venues in the city.'),
              (str(G.get('Takeaway pizza', 0)), 'mentions', 'Italian is comfort too', 'Takeaway pizza and spag bol are two of the top three guilty pleasures.')],
        chapters=[('courses', 'Every course', 'Italian appears on every course, and wins dessert', 'Italian share by course, and its place in comfort food.', ch1),
                  ('venues', 'The venues', 'Specialists are among the city\'s most-named venues', 'Who guests name for Italian, and how Glasgow\'s tiramisu habit compares.', ch2),
                  ('inside', 'Inside Italian', 'Pasta leads, pizza is comfort, bruschetta is rising', 'The dishes within Italian, early against recent.', ch3)],
        recs=recs,
        watch=[('Pasta share', f'Pasta and Italian mains are steady at {f1(mi["pct"])}%. A fall would suggest saturation in the city centre.'),
               ('Tiramisu fatigue', 'Tiramisu is so dominant it could tire. Watch the "bin it" list for it.'),
               ('Pizza', 'Pizza on dream mains is small and steady; its strength is comfort and takeaway.'),
               ('Edinburgh', 'Tiramisu indexes lower in Edinburgh, where sticky toffee pudding leads (see No. 02).')],
        method_stats=[(f0(si['n'] + mi['n']), 'Italian starters and mains'), (f0(tir['n']), 'tiramisu answers'), (str(len(iv)), 'Italian venues profiled'), ('6', 'quarters tracked')],
        method='<p>Italian dishes are those in the "Pasta and Italian" and "Pizza" groups, plus tiramisu. Italian venues are a hand-picked list of venues guests name whose offer is Italian.</p>',
        card=(f'{f1(tir["pct"])}%', 'of dream desserts are tiramisu'),
        blurb='Italian on every course, the comfort end, the venues guests name and how the specialists win.'))


# ================================================================== 11 operator confidence
def r_confidence():
    ex = Ex()
    L = LOOK; n = len(L)
    f = lambda k: [r[k] for r in L if r[k] is not None]
    tr, pr, c3, c12 = f('trading'), f('predictable'), f('conf3'), f('conf12')
    call = Counter(f('call')); sup = Counter(f('supplier')); staff = Counter(f('staffing')); spend = Counter(f('spend')); foot = Counter(f('footfall'))
    look = P['look']
    acts = []
    for a, v in look['actions']:
        if a == 'rota changes)':
            continue
        acts.append(('Staffing model changes' if a.startswith('Staffing model') else nice(a), v))
    sizes = ['Micro (1–10 staff)', 'Small (11–50)']
    bysize = {s: [r for r in L if r['size'] == s] for s in sizes}
    m = lambda rs, k: mean([r[k] for r in rs if r[k] is not None])
    down12 = sum(1 for r in L if r['conf3'] is not None and r['conf12'] < r['conf3'])
    neg_call = call['Mixed'] + call['Deteriorating']
    hist = lambda vals, lo, hi: [(str(i), vals.count(i)) for i in range(lo, hi + 1)]
    ch1 = ('<div class="ex-pair"><div>' + ex(f'Trading scores cluster below the midpoint: average {mean(tr):.1f} of 10', 'How would you rate the current trading environment? (1 to 10), number of operators.',
              cols(hist(tr, 1, 10), on={'1', '2', '3', '4'}, note=f'{sum(1 for v in tr if v <= 4)} of {len(tr)} score 4 or below.'),
              f'2026 Look Ahead survey, {n} operators', (['Score', 'Operators'], hist(tr, 1, 10))) + '</div><div>'
           + ex(f'Nobody can see beyond a quarter: predictability averages {mean(pr):.1f}', 'How predictable are your next three months? (1 to 10), number of operators.',
                cols(hist(pr, 1, 10), on={'1', '2', '3'}, note=f'{sum(1 for v in pr if v <= 3)} of {len(pr)} score 3 or below; nobody scores above {max(pr)}.'),
                f'2026 Look Ahead survey, {n} operators', (['Score', 'Operators'], hist(pr, 1, 10))) + '</div></div>'
           + ex(f'{pc(sum(1 for v in c3 if v >= 6), len(c3))}% back their own next quarter; {pc(call["Improving"] + call["Stable"], sum(call.values()))}% say the same of the sector', 'Confidence in your own business (6 or above of 10 counts as positive) against the call on the sector in your area.',
                stack([('Your business, next 3 months', f'average {mean(c3):.1f} of 10', [('6 or above', sum(1 for v in c3 if v >= 6), 'k1'), ('5', c3.count(5), 'k0'), ('4 or below', sum(1 for v in c3 if v <= 4), 'k2')]),
                       ('Your business, next 12 months', f'average {mean(c12):.1f} of 10', [('6 or above', sum(1 for v in c12 if v >= 6), 'k1'), ('5', c12.count(5), 'k0'), ('4 or below', sum(1 for v in c12 if v <= 4), 'k2')]),
                       ('The sector in your area', f'{sum(call.values())} answering', [('Improving or stable', call['Improving'] + call['Stable'], 'k1'), ('Mixed', call['Mixed'], 'k0'), ('Deteriorating', call['Deteriorating'], 'k2')])],
                      [('Positive', 'k1'), ('Middle', 'k0'), ('Negative', 'k2')]),
                f'2026 Look Ahead survey, {n} operators, 2 April to 3 May 2026', (['Question', 'Positive', 'Middle', 'Negative'], [['Your business, 3 months', sum(1 for v in c3 if v >= 6), c3.count(5), sum(1 for v in c3 if v <= 4)], ['Your business, 12 months', sum(1 for v in c12 if v >= 6), c12.count(5), sum(1 for v in c12 if v <= 4)], ['Sector in your area', call['Improving'] + call['Stable'], call['Mixed'], call['Deteriorating']]]))
           + sowhat('a lender or council', f'This is the confidence gap: operators average {mean(c3):.1f} for their own next quarter, yet {neg_call} of {sum(call.values())} call their local sector mixed or deteriorating, and {down12} of {len(c3)} are less confident about the year than the quarter.'))
    press = [(nice(a), v) for a, v in look['pressures'][:9]]
    ch2 = (ex('Costs, not demand, are the pressure: energy, food and labour lead', 'Which pressures are most significant today? Number of operators naming each.',
              hbar(press, on={press[0][0], press[1][0], press[2][0]}), f'2026 Look Ahead survey, {n} operators', (['Pressure', 'Operators'], press))
           + ex('Supplier prices are rising for almost everyone; spend per head is flat at best', 'Four-week trends reported by operators.',
                stack([('Supplier pricing', f'{sum(sup.values())} answering; {sup["Rising fast"]} say rising fast', [('Stable', sup['Stable'], 'k1'), ('Unsure', sup['Unsure'], 'k0'), (f'Rising ({sup["Rising fast"]} fast, {sup["Rising slowly"]} slowly)', sup['Rising fast'] + sup['Rising slowly'], 'k2')]),
                       ('Spend per head', f'{sum(spend.values())} answering', [('Up', spend['Up'], 'k1'), ('Flat', spend['Flat'], 'k0'), ('Down', spend['Down'], 'k2'), ('Unsure', spend['Unsure'], 'k0')]),
                       ('Bookings and footfall', f'{sum(foot.values())} answering', [('Up', foot['Up'], 'k1'), ('Flat', foot['Flat'], 'k0'), ('Down', foot['Down'], 'k2'), ('Not applicable', foot['N/A'], 'k0')]),
                       ('Staffing pressure', f'{sum(staff.values())} answering', [('No issue', staff['No issue'], 'k1'), ('Issue', staff['Issue'], 'k0'), ('Major issue', staff['Major issue'], 'k2')])],
                      [('Good for the business', 'k1'), ('Neutral or unsure', 'k0'), ('Bad for the business', 'k2')]),
                f'2026 Look Ahead survey, {n} operators', (['Trend', 'Answer', 'Operators'], [[t, k, v] for t, cc in (('Supplier pricing', sup), ('Spend per head', spend), ('Footfall', foot), ('Staffing', staff)) for k, v in cc.most_common()])))
    sup_ = [(nice(a), v) for a, v in look['support'] if v > 2]
    ch3 = ('<div class="ex-pair"><div>' + ex('Operators are acting: price changes lead', 'Actions taken in the last three to six months.',
              hbar(acts[:9], on={acts[0][0]}), f'2026 Look Ahead survey, {n} operators', (['Action', 'Operators'], acts[:9])) + '</div><div>'
           + ex('Rates relief is the one ask that unites them', 'Support that would make the biggest difference.',
                hbar(sup_, on={sup_[0][0]}), f'2026 Look Ahead survey, {n} operators', (['Support', 'Operators'], sup_)) + '</div></div>'
           + ex('Small businesses are feeling it more than micro ones', 'Average scores by business size (1 to 10).',
                heat(['Business size', 'Trading', 'Predictability', 'Confidence, 3 months', 'Confidence, 12 months'],
                     [(f'{s.split(" (")[0]} ({len(bysize[s])})', [round(m(bysize[s], k), 1) for k in ('trading', 'predictable', 'conf3', 'conf12')]) for s in sizes],
                     fmt=lambda v: f'{v:.1f}', key=('Lower', 'Higher')),
                '2026 Look Ahead survey; medium and large businesses (7) too few to show', (['Size', 'Trading', 'Predictability', '3 months', '12 months'], [[s] + [f'{m(bysize[s], k):.1f}' for k in ('trading', 'predictable', 'conf3', 'conf12')] for s in sizes]))
           + sowhat('policy makers', f'Small businesses (11 to 50 staff) rate trading at {m(bysize[sizes[1]], "trading"):.1f} against {m(bysize[sizes[0]], "trading"):.1f} for micro businesses: big enough to carry a full wage bill and rates, too small to absorb shocks. {look["support"][0][1]} of {n} name rates relief as the support that would help most.'))
    recs = [('Target support at small businesses (11 to 50 staff)', f'Their trading score ({m(bysize[sizes[1]], "trading"):.1f}) is the lowest of any size band with enough answers.', 'High', 'Medium', 'Next budget round'),
            ('Offer bridging, not growth, finance', f'Predictability averages {mean(pr):.1f} of 10. Products that smooth a bad quarter fit better than expansion loans.', 'High', 'Medium', 'Next quarter'),
            ('Make rates relief the headline ask', f'{look["support"][0][1]} of {n} operators name it: the one measure that unites the sector.', 'High', 'High', 'Next budget round'),
            ('Fund footfall initiatives with events', 'Tourism and footfall initiatives are among the top three asks; events are named as a performance factor.', 'Medium', 'Medium', 'Six months'),
            ('Run the pulse every quarter', 'One survey is a snapshot. A quarterly pulse turns it into an early-warning system for lenders and councils.', 'Medium', 'Low', 'Quarterly')]
    return render(dict(slug='operator-confidence', ex=ex, status='sample', aud='public investor supplier', **META['operator-confidence'],
        title='The confidence <em>gap</em>', desc='A pulse of Scottish hospitality operators: trading, predictability, confidence, the pressures they face and the support they want.',
        stand='Scottish operators back their own businesses but not the sector around them, and almost none can see beyond the next quarter. A sector pulse from the 2026 Look Ahead survey.',
        client='A lender, local authority or trade body', question='How are operators really doing, and what support would help most?', evidence=f'{n} Scottish operators, 2 April to 3 May 2026',
        kpis=[(f'{mean(c3):.1f}', 'confidence in own business, next 3 months (of 10)'), (f'{neg_call} of {sum(call.values())}', 'call the local sector mixed or deteriorating'), (f'{mean(pr):.1f}', 'predictability of the next 3 months (of 10)'), (f'{look["support"][0][1]} of {n}', 'want rates relief')],
        answer='Operators are confident in themselves but not in the sector, and almost none can see beyond a quarter, so the most useful support smooths a bad quarter: rates relief, bridging finance and footfall, aimed first at small businesses.',
        msgs=[(f'{mean(c3):.1f}', 'of 10', 'They back themselves', f'Average confidence in their own next three months; {sum(1 for v in c3 if v >= 6)} of {len(c3)} score 6 or more.'),
              (f'{neg_call}', f'of {sum(call.values())}', 'They doubt the sector', f'Call their local sector mixed or deteriorating; only {call["Improving"]} say improving.'),
              (f'{mean(pr):.1f}', 'of 10', 'Nobody can see ahead', f'Predictability of the next quarter; nobody scores above {max(pr)}.')],
        chapters=[('gap', 'The confidence gap', 'Operators back their own business but not the sector', 'Trading, predictability and confidence, in full distribution.', ch1),
                  ('pressure', 'The pressure', 'Costs, not demand, are what hurts', 'The pressures operators name and the four-week trends they see.', ch2),
                  ('response', 'The response', 'Operators are acting; rates relief is the shared ask', 'What they have done, what would help, and who is feeling it most.', ch3)],
        recs=recs,
        watch=[('A second survey', 'A second pulse would show whether the gap is closing or widening. One survey is a snapshot.'),
               ('Energy prices', 'Energy and food costs lead the pressures. A fall in energy prices would ease the biggest single cost line.'),
               ('Closures', f'"More closures nearby" is the most-seen warning signal ({dict(look["signals"]).get("More closures nearby", 0)} of {n}). Track closures by area.'),
               ('Sample mix', f'Micro and small businesses are {len(bysize[sizes[0]]) + len(bysize[sizes[1]])} of {n} answers: a fair picture of Scottish hospitality, thin for larger operators.')],
        method_stats=[(str(n), 'operators'), (str(len(bysize[sizes[0]])), 'micro businesses'), (str(len(bysize[sizes[1]])), 'small businesses'), ('5', 'weeks of fieldwork')],
        method='<p>The 2026 Look Ahead survey ran 2 April to 3 May 2026. Respondents were owners, chefs, managers and suppliers across cafés, restaurants, hotels, bars, street food and catering. Scores are 1 to 10. Several questions allowed more than one answer. Figures here are recomputed from the anonymised scores, so they can differ by one or two from the 2026 report, which used an earlier extract.</p>',
        card=(f'{neg_call} of {sum(call.values())}', 'operators call their local sector mixed or deteriorating'),
        blurb='Trading, predictability and confidence from Scottish operators, the pressures they face and the support they want.'))


# ================================================================== forecast series (Nos. 12 to 15)
L = link
XL = Q + ['Q1 27', 'Q2 27', 'Q3 27', 'Q4 27']
POS = json.load(open('tools/data/positive-trends-2026.json', encoding='utf-8'))
PT = POS['tags']
OMK = "Omakase and chef's counters"
SRC = {
    'savills': ('https://www.savills.co.uk/insight-and-opinion/savills-news/388121/record-year-for-glasgow-fandb-operators-with-38-new-openings-in-2025', 'Savills, February 2026'),
    'glevy': ('https://www.scotsman.com/news/glasgow-tourist-tax-given-go-ahead-by-councillors-with-hopes-visitor-levy-will-generate-ps16m-5185874', 'The Scotsman'),
    'glevy2': ('https://www.glasgow.gov.uk/article/14799/Glasgow-s-Visitor-Levy', 'Glasgow City Council'),
    'elevy': ('https://www.edinburgh.gov.uk/business/visitor-levy-edinburgh', 'City of Edinburgh Council'),
    'elevy50': ('https://edinburghmagazine.com/transforming-tourism-edinburghs-visitor-levy-to-raise-50m-annually', 'Edinburgh Magazine, August 2026'),
    'eindie': ('https://www.scotsman.com/business/the-independent-restaurant-resurgence-driving-edinburghs-buoyant-food-and-beverage-sector-8931275', 'The Scotsman, August 2026'),
    'glp1': ('https://www.restaurantonline.co.uk/Article/2026/07/03/use-of-weight-loss-medication-to-reduce-out-of-home-food-and-drink-spend-by-1bn/', 'IGD via Restaurant Online, July 2026'),
    'drink': ('https://theboar.org/2026/10/new-data-shows-young-people-drinking-less-than-ever/', 'The Boar, October 2026'),
    'niq': ('https://nielseniq.com/global/en/news-center/2026/hospitality-closures-accelerate-in-fourth-quarter-as-costs-rise-again/', 'NielsenIQ, January 2026'),
    'rates': ('https://cater.affino.com/news/scottish-pubs-to-be-hit-with-staggering-increases-to-business-rates', 'UKHospitality Scotland via Cater'),
    'bidfood': ('https://www.thegrocer.co.uk/news/weight-loss-drugs-to-fuel-rise-of-smaller-plates-in-2027-says-bidfood/724308.article', 'Bidfood via The Grocer'),
    'wfm': ('https://press.aboutamazon.com/2026/10/whole-foods-market-reveals-its-top-food-and-beverage-trend-predictions-for-2027', 'Whole Foods Market, October 2026'),
    'datassential': ('https://www.foodmanufacture.co.uk/Article/2026/10/15/2027-flavours-from-buldak-to-koji-milk/', 'Datassential via Food Manufacture, October 2026'),
    'hojicha': ('https://www.foodmanufacture.co.uk/Article/2026/08/28/what-is-hojicha-and-can-it-overtake-matchas-popularity/', 'Food Manufacture, August 2026'),
    'pandan': ('https://www.foodnavigator.com/Article/2026/10/27/a-flavour-to-watch-the-rise-of-pandan/', 'FoodNavigator, October 2026'),
    'sesame': ('https://www.timeout.com/usa/news/is-black-sesame-going-to-be-the-it-flavor-of-2026-112025', 'Time Out'),
    'westaf': ('https://www.euronews.com/culture/2025/02/18/londons-african-fine-dining-boom-how-restaurants-like-akoko-and-chishuru-are-redefining-th', 'Euronews, February 2025'),
    'seaweed': ('https://www.scotsman.com/food/scottish-seaweed-set-to-be-next-global-food-trend', 'The Scotsman'),
    'kelp': ('https://ww1.sruc.ac.uk/media/tfnmad5h/food-and-footprint-kelpcrofting-case-study.pdf', 'SRUC kelpcrofting case study'),
    'tinned': ('https://www.thecaterer.com/sector/chef/tinned-fish-trend-table', 'The Caterer'),
}
S = lambda k: L(*SRC[k])
SRC_LIST = lambda keys: '<p><b>Sources:</b> ' + ', '.join(S(k) for k in keys) + '.</p>'
FC_METHOD = ('<p><b>How the projections work.</b> Each line is a recency-weighted straight line through the quarters with enough answers, '
             'started from the latest solid quarter and damped by 30% each quarter so that no trend runs on for ever. The shaded band is a '
             'planning range that widens with the horizon and with the steepness of the trend, because a steep trend is the one most likely to stall. It shows how far the line could reasonably wander, not a statistical confidence interval. '
             'These are projections of the recent trend, not predictions: they say where things go if nothing changes, which is useful precisely '
             'because something usually does. Calls beyond 2027 are Dream Menu judgement, combining the projections with the published research cited.</p>')


MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ym = lambda x: f'{MON[min(11, int(round((x % 1) * 12)))]} {int(x)}'


def fanp(title, c, name, level='groups', k='k1'):
    it = item(c, name, level)
    vals, fd = it['share'], faded(c)
    ai, _ = project(vals, fd, 1)
    ai, pr = project(vals, fd, len(XL) - 1 - ai)
    return (title, vals, k, fd, ai, pr)


def fan_data(panels):
    return (['Measure', 'Latest solid quarter', 'Q4 27 on trend', 'Planning range'],
            [[t, f'{vs[ai]:.1f}% ({XL[ai]})', f'{pr[-1][0]:.1f}%', f'{pr[-1][1]:.1f}% to {pr[-1][2]:.1f}%'] for t, vs, k, fd, ai, pr in panels])


def big3(cols_):
    cls = {'In': '', 'Holding': 'hold', 'Out': 'out'}
    return '<div class="cs-big3">' + ''.join(f'<div class="{cls[h]}"><h4>{h}</h4><ul>' + ''.join(f'<li>{x}</li>' for x in xs) + '</ul></div>' for h, xs in cols_) + '</div>'


def areas_of(city, centres, radius, bbox):
    kmd = lambda a, b: math.hypot((a[0] - b[0]) * 111, (a[1] - b[1]) * 111 * math.cos(math.radians(a[0])))
    la0, la1, lo0, lo1 = bbox
    vs = [v for v in DM['venues'] if v.get('c') == city and not v.get('tw') and v['p'] in ('exact', 'street', 'neighbourhood') and v.get('la') and la0 < v['la'] < la1 and lo0 < v['lo'] < lo1]
    agg = defaultdict(lambda: dict(v=0, m=0, h=0, names=[], k=Counter()))
    for v in vs:
        d, n = min((kmd((v['la'], v['lo']), c), n) for n, c in centres.items())
        n = n if d < radius else 'Elsewhere'
        a = agg[n]; a['v'] += 1; a['m'] += v['m']; a['h'] += v.get('cs', {}).get('h', 0); a['names'].append((v['m'], v['n']))
        for kk, c in v.get('k', []):
            a['k'][kk] += c
    return agg


def cat_label(c):
    return c.replace(' / ', ', ').replace('Tartare, carpaccio', 'Tartare and carpaccio')


# ------------------------------------------------------------------ 12 Glasgow to 2030
def r_glasgow_2030():
    ex = Ex()
    tot_g = CM['totals'][GI]
    rows = [r for r in CM['rows'] if not r['cells'][GI]['thin']]
    gi = sorted(((r['l'], r['cells'][GI]['idx']) for r in rows), key=lambda x: -x[1])
    ch1 = (ex('Glasgow over-orders margaritas, scallops and tiramisu, and under-orders the Negroni', 'Glasgow\'s index against all Dream Menu answers for the most-named dishes and drinks (100 = average). Bars show the gap from average.',
              diverge([(n, v - 100) for n, v in gi], unit='', show=lambda v: str(round(v + 100)), left='Less than average', right='More than average'),
              f'{DM_SRC}; {f0(CM["totals"][GI])} Glasgow answers. Only dishes with enough Glasgow answers shown.',
              (['Dish or drink', 'Glasgow index', 'Glasgow share'], [[r['l'], r['cells'][GI]['idx'], f'{r["cells"][GI]["share"]}%'] for r in sorted(rows, key=lambda r: -r['cells'][GI]['idx'])]))
           + '<div class="prose"><p>Glasgow\'s table is generous, loud and familiar. The city indexes high on the margarita (the city\'s signature drink in the archive), scallops, tiramisu, fillet steak and chicken tenders, and low on the Negroni and the martini that define Edinburgh. That profile is a strength for the next five years: the forces below mostly reward classics done well, and they punish novelty that is only there to be photographed.</p></div>'
           + table(['Market signal', 'What it says about 2030'], [
               ['<b>38 city-centre food and drink openings in 2025</b>', f'The most since 2018 and about 10% up on 2024, across 87,000 sq ft ({S("savills")}). Demand for space is real.'],
               ['<b>Prime rents up about 15% to £50 per sq ft</b>', 'Space is getting dearer where footfall is highest. Independents will look to the Southside and the East End.'],
               ['<b>Larger operators took about a quarter of deals</b>', 'Dishoom and Sticks\'n\'Sushi signal that national brands now see Glasgow as a must-have city. Expect more by 2028.'],
               ['<b>Rates rises of up to 900% for some bars</b>', f'Scottish pub rates are forecast to rise 77% on average in 2026/27 ({S("rates")}). Wet-led bars are most exposed.'],
               ['<b>More than four licensed sites closing a day across Britain</b>', f'98,914 sites at the end of 2025, down 382 in the quarter; casual dining down 1.8% ({S("niq")}). Growth and closure are happening at once.'],
           ]))
    events = [
        ('National Living Wage rises to £12.71', 'k0', 2026.25, None, 'April 2026: the third big wage step in three years'),
        ('Commonwealth Games in Glasgow', 'k3', 2026.56, None, 'July to August 2026: a one-off spike in visitors'),
        ('£2 bus fare cap across the SPT area', 'k1', 2026.68, None, 'From September 2026: a cheaper way home'),
        ('Glasgow visitor levy starts at 5%', 'k1', 2027.07, 2031, 'From 25 January 2027, about £16m a year for the visitor economy'),
        ('Scottish pub and bar rates shock', 'k2', 2026.25, 2029.25, '2026/27 revaluation; average pub bill up 77%'),
        ('Weight-loss drugs reduce eating-out spend', 'k2', 2026.5, 2031, 'IGD expects almost £1bn less out-of-home spend by 2031'),
        ('Younger guests drinking less', 'k2', 2026, 2031, 'A steady shift from volume to quality at the bar'),
        ('National brands enter the city centre', 'k1', 2025.5, 2028.5, 'Dishoom, Sticks\'n\'Sushi and followers'),
    ]
    ch2 = (ex('Eight dated forces will shape Glasgow\'s tables to 2031', 'Diamonds are one-off events; bars show when a force builds and lasts. The dotted line is today.',
              roadmap(events, 2025, 2031, now=2026.83),
              f'{S("glevy")}; {S("glevy2")}; {S("glp1")}; {S("rates")}; {S("drink")}; {S("savills")}',
              (['Force', 'Starts', 'Runs to', 'Note'], [[a, ym(s), ym(e) if e else 'One-off', n] for a, _, s, e, n in events]))
           + sowhat('Glasgow venues', 'The visitor levy is the one force on this list that adds money rather than taking it away. From 2027 about £16m a year will be spent on the visitor economy. Venues that get into the events and marketing plans early will be the ones that benefit.'))
    panels = [fanp('Spirits (of dream drinks)', 'a', 'Spirits'), fanp('Cocktails (of dream drinks)', 'a', 'Cocktails', k='k2'),
              fanp('Vegetables and salad (of sides)', 'd', 'Vegetables and salad'), fanp('Potatoes and fries (of sides)', 'd', 'Potatoes and fries', k='k2'),
              fanp('Seafood (of mains)', 'm', 'Seafood'), fanp('Steak and beef (of mains)', 'm', 'Steak and beef'),
              fanp('Ice cream and frozen (of desserts)', 'p', 'Ice cream and frozen'), fanp('Chocolate desserts (of desserts)', 'p', 'Chocolate desserts', k='k2')]
    sp = panels[0]
    pp = panels[3]
    ch3 = (ex(f'If recent trends hold, spirits reach about {sp[5][-1][0]:.0f}% of dream drinks and potato sides fall to about {pp[5][-1][0]:.0f}% by the end of 2027', 'Share of dream choices each quarter, with a projection on the recent trend to Q4 2027. Indigo: rising; amber: falling. Each panel has its own scale.',
              fan_multiples(panels, XL), f'{DM_SRC}. About 57% of answers with a known home market are from Glasgow. Projection method in the appendix.', fan_data(panels))
           + '<div class="prose"><p>The archive covers the whole of Scotland, but Glasgow supplies most of it, so these lines are the closest thing to a Glasgow demand curve that exists. Three things stand out. The bar is moving from cocktails to spirits and whisky, quickly. Vegetables are taking space from chips on the side order. And seafood keeps climbing as a main course while steak holds its ground. None of this is a fad: each has run for at least four quarters. Treat the chips line with care, though: the first weeks of Q4 2026 point back up, and potatoes are seasonal, which is why its planning range is the widest on the page.</p></div>'
           + big3([('In', ['Whisky and spirits served simply, by the dram or in a highball', 'Vegetable sides treated as a dish, not a garnish', 'White fish, crab and shellfish mains', 'Ice cream and gelato as the default dessert']),
                   ('Holding', ['Steak, especially named cuts and sharing steaks', 'Tiramisu, the city\'s favourite dessert', 'Pasta and Italian', 'The margarita, even as the cocktail list shrinks']),
                   ('Out', ['Long novelty cocktail lists', 'Loaded and dirty fries', 'Chocolate-heavy desserts', 'Anything built for the camera first'])]))
    agg = areas_of('Glasgow', {'City centre': (55.8615, -4.2560), 'Merchant City': (55.8590, -4.2440), 'Finnieston': (55.8650, -4.2860), 'West End': (55.8750, -4.2930),
                               'Partick': (55.8700, -4.3090), 'Woodlands': (55.8680, -4.2700), 'Southside': (55.8370, -4.2680), 'Shawlands': (55.8300, -4.2830),
                               'East End': (55.8550, -4.2330), 'Dennistoun': (55.8610, -4.2130)}, 1.6, (55.80, 55.90, -4.37, -4.17))
    for a, b in (('Shawlands', 'Southside'), ('Dennistoun', 'East End')):
        if a in agg:
            x, y = agg.pop(a), agg[b]
            for kk in ('v', 'm', 'h'):
                y[kk] += x[kk]
            y['names'] += x['names']
    outlook = {'Southside': ('Rising', 'High mentions per venue and a high hidden-gem share: demand ahead of supply.'),
               'East End': ('Rising', 'The Barras and Dennistoun have insider buzz and lower rents. The likeliest new district by 2030.'),
               'Finnieston': ('Maturing', 'Still the destination strip, but rents and saturation slow it. Expect churn, not growth.'),
               'West End': ('Steady', 'Deep, loyal and residential. Holds its share.'),
               'City centre': ('Brand-led', 'Most venues and the most national brands. Volume, diluted per venue.'),
               'Merchant City': ('Steady', 'Evening economy core; exposed to bar rates.'),
               'Partick': ('Rising', 'Small base, growing interest next to Finnieston.'),
               'Woodlands': ('Steady', 'Neighbourhood dining around Charing Cross.')}
    ar = [n for n in sorted(agg, key=lambda n: -agg[n]['m']) if n != 'Elsewhere' and agg[n]['v'] >= 8]
    ppv = {n: agg[n]['m'] / agg[n]['v'] for n in ar}
    hid = {n: 100 * agg[n]['h'] / agg[n]['m'] for n in ar}
    ch4 = (ex('The Southside and the East End combine high mentions per venue with insider buzz: the next five years are theirs', 'Mentions per named venue, by district (8 or more venues). The note shows the share of mentions that are hidden gems or next stops.',
              hbar([(n, ppv[n], f'{hid[n]:.0f}% hidden gems') for n in sorted(ar, key=lambda n: -ppv[n])], on={n for n in ar if outlook.get(n, ('',))[0] == 'Rising'}, dec=1),
              f'{DM_SRC}; venue locations from guest answers and address research', (['District', 'Venues', 'Mentions', 'Per venue', 'Hidden-gem share'], [[n, agg[n]['v'], agg[n]['m'], f'{ppv[n]:.1f}', f'{hid[n]:.0f}%'] for n in ar]))
           + table(['District', 'Outlook to 2030', 'Why'], [[f'<b>{esc(n)}</b>', outlook.get(n, ('Steady', ''))[0], esc(outlook.get(n, ('', 'Small base.'))[1])] for n in ar])
           + sowhat('investors and landlords', 'Leasing follows attention with a lag of a few years. Finnieston\'s numbers today are what the Southside\'s will look like around 2028, if the pattern of the last decade repeats. The East End is the outside bet.'))
    sc = [('Classics, done better', 50, 'The base case: steady demand, tighter margins, a better bar.', 'Guests keep eating out but order fewer extras. Spirits, seafood and vegetables grow; cocktail lists shrink. The levy funds a few big events a year. The independent scene moves south and east as rents climb in the centre.', 'spirits share keeps rising; set menus spread; new openings on Victoria Road and in Dennistoun.'),
          ('The events city', 25, 'The upside: the levy and big events lift the whole year.', 'Levy money goes into a year-round events calendar. Hotel occupancy rises and visitors fill midweek tables. National brands keep arriving, and the city-centre vacancy rate falls.', 'a published levy spending plan with events beyond the summer; hotel occupancy up two years running.'),
          ('The squeeze', 25, 'The downside: costs outrun prices and the middle closes.', 'Rates, wages and weaker appetite (weight-loss drugs, less drinking) close mid-market casual dining and wet-led bars. The scene polarises between cheap and special.', 'more than one closure a week in the city centre; spend per head falling for two surveys in a row.')]
    ch5 = scenarios(sc) + '<div class="prose" style="margin-top:18px"><p>The likelihoods are Dream Menu\'s judgement, not a model output. They exist to force a plan for each case: an operator who has a plan only for the base case is betting the business on a coin that lands heads half the time.</p></div>'
    recs = [('Rebuild the bar around spirits, whisky and a short classic list', f'Spirits rose from {f1(item("a", "Spirits", "groups")["early"])}% to {f1(item("a", "Spirits", "groups")["late"])}% of dream drinks, a clear move, while cocktails fell {abs(item("a", "Cocktails", "groups")["move"]):.0f} points. Fewer, better drinks also suit guests who are drinking less.', 'High', 'Low', 'Next menu change'),
            ('Make a vegetable side the menu\'s talking point', f'Vegetable and salad sides rose {pts(item("d", "Vegetables and salad", "groups")["move"])} points; potato sides fell {abs(item("d", "Potatoes and fries", "groups")["move"]):.0f}. Both moves are clear.', 'High', 'Low', 'Next menu change'),
            ('Get into the levy plan before January 2027', 'Venues and suppliers that help shape the events calendar will capture the £16m a year. Approach the council and Glasgow Life now.', 'High', 'Medium', 'Before January 2027'),
            ('Lease or open on the Southside and in the East End', 'Both districts pair high mentions per venue with insider buzz, at lower rents than Finnieston.', 'High', 'High', '12 to 24 months'),
            ('Design smaller-portion and protein-led options', f'Weight-loss drugs could take almost £1bn out of eating-out spend by 2031 ({S("glp1")}). Half portions and protein-forward dishes keep those guests coming.', 'Medium', 'Medium', 'During 2027'),
            ('Re-run this forecast every quarter', 'Each new quarter tightens the planning range and shows which scenario is winning.', 'Medium', 'Low', 'Quarterly')]
    return render(dict(slug='glasgow-2030', ex=ex, status='sample', aud='forecast venue supplier investor public', **META['glasgow-2030'],
        title='Glasgow <em>to 2030</em>', desc='A city forecast for Glasgow: what guests will order, which districts rise, the forces that bite, and three scenarios to 2030.',
        stand='What will Glasgow order in 2027, which districts will lead by 2030, and which forces will decide it? A city forecast built from six quarters of Dream Menu demand data and the latest market research.',
        client='A supplier, operator group or investor planning for Glasgow', question='How will Glasgow\'s food and drink scene change by 2030, and how should we prepare?', evidence=f'Six quarters of demand data, {f0(CM["totals"][GI])} Glasgow answers, market research',
        kpis=[('38', 'city-centre food and drink openings in 2025, the most since 2018'), ('£16m', 'a year from the visitor levy, from January 2027'), (f'{pts(item("a", "Spirits", "groups")["move"])} pts', 'spirits as a share of dream drinks, a clear move'), ('50%', 'our likelihood for the base case, "Classics, done better"')],
        answer='Glasgow is heading for fewer, better drinks, more fish and vegetables, and a scene that moves south and east, with the visitor levy as the one new source of money and rising costs as the main threat.',
        msgs=[(f'{sp[5][-1][0]:.0f}%', 'by Q4 27', 'The bar turns to spirits', f'On the recent trend, spirits reach about {sp[5][-1][0]:.0f}% of dream drinks by the end of 2027, up from {sp[1][sp[4]]:.0f}%. Cocktails keep losing share.'),
              ('£16m', 'a year', 'The levy is the upside', 'From January 2027, 5% on overnight stays, spent on the visitor economy. The only force on the list that adds money.'),
              (f'{ppv.get("Southside", 0):.1f}', 'per venue', 'The scene moves south and east', f'Second only to Finnieston ({ppv.get("Finnieston", 0):.1f}) on mentions per venue; the East End has the highest hidden-gem share ({hid.get("East End", 0):.0f}%).')],
        chapters=[('today', 'Glasgow today', 'Glasgow orders generous, loud and familiar', 'What the city over-orders against the rest of the archive, and what the property market is saying.', ch1),
                  ('forces', 'The forces', 'Eight dated forces will shape the next five years', 'Wages, rates, the levy, weight-loss drugs and a generation drinking less, on one timeline.', ch2),
                  ('menu', 'The menu forecast', 'What Glasgow will order in 2027', 'Six quarters of demand, projected on the recent trend, with a planning range.', ch3),
                  ('districts', 'The map forecast', 'The Southside and the East End are next', 'Which districts have momentum, and what each is likely to look like by 2030.', ch4),
                  ('scenarios', 'Scenarios', 'Three ways the city could go', 'A base case and two alternatives, with the early signs of each.', ch5)],
        recs=recs, recs_lede='Six moves that work in the base case and protect against the downside.',
        watch=[('Spirits share', 'If spirits stall below a quarter of dream drinks in 2027, the bar shift is slower than projected.'),
               ('The levy spending plan', 'A plan weighted to year-round events moves the odds towards "The events city".'),
               ('City-centre closures', 'More than one a week for a quarter would move the odds towards "The squeeze".'),
               ('Southside rents', 'Rents rising faster than footfall would mean the district is pricing itself out, as Finnieston did.')],
        method_stats=[('6', 'quarters of demand data'), (f0(tot_g), 'Glasgow answers'), ('8', 'measures projected'), ('3', 'scenarios')],
        method=FC_METHOD + '<p>City index: Glasgow\'s share of answers for each dish against the share across all answers, times 100. District figures use venues guests named in Glasgow with a known address, assigned to the nearest district centre within 1.6 km (Shawlands joins the Southside, Dennistoun the East End).</p>',
        sources=SRC_LIST(['savills', 'glevy', 'glevy2', 'rates', 'niq', 'glp1', 'drink']),
        card=('£16m', 'a year from Glasgow\'s visitor levy from 2027'),
        blurb='What Glasgow will order in 2027, which districts rise, the forces that bite and three scenarios to 2030.'))


# ------------------------------------------------------------------ 13 Edinburgh and Scotland to 2030
def r_edinburgh_2030():
    ex = Ex()
    rows = [r for r in CM['rows'] if not r['cells'][EI]['thin']]
    ei = sorted(((r['l'], r['cells'][EI]['idx']) for r in rows), key=lambda x: -x[1])
    neg = city_row('Negroni')['cells'][EI]['idx']
    tot_e = CM['totals'][EI]
    ch1 = (ex('Edinburgh drinks like a capital: the Negroni and the martini over-index more than three times', 'Edinburgh\'s index against all Dream Menu answers (100 = average), for dishes with enough Edinburgh answers.',
              diverge([(n, v - 100) for n, v in ei], show=lambda v: str(round(v + 100)), left='Less than average', right='More than average'),
              f'{DM_SRC}; {f0(tot_e)} Edinburgh answers', (['Dish or drink', 'Edinburgh index', 'Glasgow index'], [[r['l'], r['cells'][EI]['idx'], r['cells'][GI]['idx']] for r in sorted(rows, key=lambda r: -r['cells'][EI]['idx'])]))
           + '<div class="prose"><p>Where Glasgow over-orders the margarita, Edinburgh over-orders the Negroni (index ' + str(neg) + ') and the martini. It also leans to sticky toffee pudding, white fish and steak. It is a stirred-drink, white-tablecloth, visitor-shaped appetite, and the next five years will be shaped by the one policy that is already live here and not yet in Glasgow: the visitor levy.</p></div>'
           + sowhat('a supplier', 'Two cities fifty minutes apart need two bar strategies. In Edinburgh, lead with vermouth, bitters, gin and the stirred classics; in Glasgow, with tequila, whisky and a short sour-led list.'))
    agg = areas_of('Edinburgh', {'Leith': (55.9750, -3.1720), 'Old Town': (55.9495, -3.1890), 'New Town': (55.9545, -3.1990), 'West End': (55.9485, -3.2110), 'Stockbridge': (55.9590, -3.2085),
                                 'Southside': (55.9410, -3.1820), 'Bruntsfield': (55.9375, -3.2060), 'Leith Walk': (55.9640, -3.1770)}, 1.3, (55.90, 56.0, -3.35, -3.05))
    ar = [n for n in sorted(agg, key=lambda n: -agg[n]['m']) if n != 'Elsewhere' and agg[n]['v'] >= 10]
    ppv = {n: agg[n]['m'] / agg[n]['v'] for n in ar}
    hid = {n: 100 * agg[n]['h'] / agg[n]['m'] for n in ar}
    anc = {n: sorted(agg[n]['names'], reverse=True)[0][1] for n in ar}
    out = {'Leith': 'Rising', 'Leith Walk': 'Rising', 'Stockbridge': 'Steady', 'New Town': 'Brand-led', 'West End': 'Steady', 'Old Town': 'Visitor-led', 'Bruntsfield': 'Steady', 'Southside': 'Rising'}
    ch2 = (ex('Leith is Edinburgh\'s insider district: the highest share of hidden-gem answers in the city', 'Share of each district\'s mentions that are hidden gems or next stops (10 or more named venues).',
              hbar([(n, hid[n], f'{agg[n]["v"]} venues, most named: {anc[n]}') for n in sorted(ar, key=lambda n: -hid[n])], on={'Leith', 'Leith Walk'}, unit='%'),
              f'{DM_SRC}; venue locations from guest answers and address research', (['District', 'Venues', 'Mentions', 'Per venue', 'Hidden-gem share', 'Most named'], [[n, agg[n]['v'], agg[n]['m'], f'{ppv[n]:.1f}', f'{hid[n]:.0f}%', anc[n]] for n in ar]))
           + ex('The New Town draws the most per venue; the Old Town, full of visitors, the least', 'Mentions per named venue, by district.',
                hbar([(n, ppv[n]) for n in sorted(ar, key=lambda n: -ppv[n])], on={'New Town'}, alt={'Old Town'}, dec=1), DM_SRC,
                (['District', 'Per venue', 'Outlook to 2030'], [[n, f'{ppv[n]:.1f}', out.get(n, 'Steady')] for n in ar]))
           + sowhat('investors and landlords', f'The Old Town has the most named venues ({agg["Old Town"]["v"]}) but the fewest mentions each ({ppv["Old Town"]:.1f}): footfall without loyalty. Leith and Leith Walk are the reverse, and the levy\'s neighbourhood spending could speed them up. Edinburgh\'s Leith is what Glasgow\'s Southside is.'))
    events = [('Edinburgh visitor levy at 5%', 'k1', 2026.56, 2031, 'From 24 July 2026; up to £50m a year, capped at five nights'),
              ('Festival season', 'k3', 2026.58, None, 'Every August: the city\'s biggest month, now levy-funded'),
              ('First full levy year reported', 'k0', 2027.6, None, 'Expected mid-2027: the first evidence of what the money buys'),
              ('Glasgow levy starts', 'k0', 2027.07, None, 'January 2027: two levy cities, competing for the same visitors'),
              ('£5m for Leith Theatre and £90m+ of levy programmes', 'k1', 2026.6, 2029.6, 'Three years of projects, including culture in Leith'),
              ('Chain retreat, independent advance', 'k2', 2026, 2029, 'Pizza Express shut two Leith sites; Las Iguanas left George Street; about 60% of take-up is local independents')]
    ch3 = (ex('The levy turns Edinburgh into a test case for the rest of Scotland', 'Diamonds are one-off events; bars show programmes that run. The dotted line is today.',
              roadmap(events, 2026, 2031, now=2026.83), f'{S("elevy")}; {S("elevy50")}; {S("eindie")}', (['Event', 'Starts', 'Note'], [[a, ym(s), n] for a, _, s, e, n in events]))
           + table(['Signal', 'What it means by 2030'], [
               ['<b>Up to £50m a year from the levy</b>', f'The UK\'s first city-wide visitor levy went live on 24 July 2026 ({S("elevy")}). By 2030 it will have funded around £200m of visitor-economy spending: events, cleaning, culture and housing.'],
               ['<b>About 60% of leasing take-up by local independents</b>', f'Footfall up 2% and the highest hotel occupancy of Europe\'s major gateway cities ({S("eindie")}). Independents are winning the space chains are leaving.'],
               ['<b>Ottolenghi is coming to the west end</b>', 'A London name choosing Edinburgh says the city is now on the national-brand map for food, not just for retail.'],
               ['<b>Chains leaving</b>', 'Pizza Express closed two Leith sites; Las Iguanas left George Street. Casual-dining chains are the losers of the decade.'],
           ]))
    scot = sorted([(m['n'], m['mn']) for m in DM['markets'] if m['k'] == 'city' and m.get('na') == 'Scotland' and m['n'] not in ('Glasgow', 'Edinburgh') and m['mn'] >= 4], key=lambda x: -x[1])[:12]
    ros = [r for r in CM['rows'] if not r['cells'][2]['thin']]
    coast = {'Ullapool', 'Portree', 'Tarbert', 'Oban', 'Isle Of Mull', 'Isle of Skye', 'North Berwick', 'Cullen', 'Ardrishaig', 'Largs', 'Isle of Lewis', 'Isle of Arran'}
    ch4 = (ex('Outside the two cities, guests name coastal and destination venues', 'Venue mentions by town, outside Glasgow and Edinburgh (4 or more). Highlighted: coastal and island towns.',
              hbar(scot, on={n for n, _ in scot if n in coast}), f'{DM_SRC}; venue locations', (['Town', 'Mentions'], [[n, v] for n, v in scot]))
           + '<div class="prose"><p>Away from the cities, guests name destinations rather than locals: seafood at Ullapool, Portree and Tarbert, hotel dining at Auchterarder and Crieff, and Aberdeen as the third city. Answers from the rest of Scotland over-index on ' + nice(' / '.join(r['l'].lower() for r in sorted(ros, key=lambda r: -r['cells'][2]['idx'])[:3])) + '. ' + f'Scottish seaweed is being tipped as the next global food trend ({S("seaweed")}), and kelp crofting is turning it into a coastal crop ({S("kelp")}). If it happens, it will start on these coasts, on these menus.</p></div>'
           + sowhat('tourism bodies', 'The rest of Scotland\'s food story is a journey, not a high street. A seafood and destination-dining trail, funded as levies spread, is the obvious product.'))
    ch5 = (table(['Theme', 'Direction to 2030', 'Confidence', 'Why'], [
        ['<b>Stirred classics and aperitivo</b>', 'Growing', 'Medium', 'Edinburgh over-indexes on the Negroni and martini; Whole Foods names "bitter done better" for 2027.'],
        ['<b>Independent restaurants</b>', 'Growing', 'High', 'About 60% of take-up, as chains retreat from George Street and Leith.'],
        ['<b>Leith and Leith Walk</b>', 'Growing', 'Medium', 'The highest hidden-gem shares in the city and levy-funded culture in Leith.'],
        ['<b>Old Town visitor dining</b>', 'Holding', 'Medium', 'Lots of venues, few mentions each. The levy adds visitors, not loyalty.'],
        ['<b>Casual-dining chains</b>', 'Shrinking', 'High', 'Closures in Leith and George Street mirror the national figures.'],
        ['<b>Coastal and island seafood destinations</b>', 'Growing', 'Medium', 'Already the most-named venues outside the cities; seaweed could add a second act.'],
    ]) + '<div class="prose" style="margin-top:12px"><p><b>Why "directional".</b> Edinburgh supplies ' + f0(tot_e) + ' answers to Glasgow\'s ' + f0(CM['totals'][GI]) + ', and the rest of Scotland ' + f0(CM['totals'][2]) + '. That is enough to see the shape of the city\'s appetite, not enough to project it quarter by quarter. Edinburgh\'s growing share of venue mentions since late 2025 mostly reflects where Dream Menu interviews have reached, not a change in demand. A commission would add about 150 Edinburgh interviews to put the city on the same footing as Glasgow.</p></div>')
    recs = [('Run a separate Edinburgh bar programme', f'Negroni index {neg} and martini {city_row("Martini")["cells"][EI]["idx"]}: vermouth, bitters and gin-led serves, not the Glasgow margarita list.', 'High', 'Low', 'Next quarter'),
            ('Back independents in Leith and Leith Walk', 'The insider districts, with levy-funded culture arriving. Lease to food-led independents before rents follow.', 'High', 'Medium', '12 to 24 months'),
            ('Use levy money for food beyond August', 'Fund food events in the shoulder months so that the levy fills tables in March, not only during the festivals.', 'High', 'Medium', 'Next levy round'),
            ('Build a coastal seafood trail', 'The most-named venues outside the cities are coastal. A trail turns scattered destinations into one product.', 'Medium', 'Medium', '2027'),
            ('Commission 150 more Edinburgh interviews', 'Moves this read from directional to forecast-grade, with quarterly projections like Glasgow\'s.', 'Medium', 'Low', 'Next quarter')]
    return render(dict(slug='edinburgh-2030', ex=ex, status='sample', aud='forecast public investor supplier', **META['edinburgh-2030'],
        title='Edinburgh <em>and Scotland</em> to 2030', desc='A directional forecast for Edinburgh and the rest of Scotland: the capital\'s appetite, Leith\'s rise, the visitor levy test and coastal destinations.',
        stand='Edinburgh is the UK\'s first levy city and orders like a capital. A directional forecast for the capital and the rest of Scotland, from Dream Menu data and the latest market research.',
        client='A tourism body, investor or supplier with Scottish ambitions', question='How will Edinburgh and the rest of Scotland change by 2030, and where are the openings?', evidence=f'{f0(tot_e)} Edinburgh answers, {f0(MK["Edinburgh"]["v"])} Edinburgh venues, market research',
        kpis=[('£50m', 'a year expected from Edinburgh\'s visitor levy'), (str(neg), 'Edinburgh\'s Negroni index (100 = average)'), (f'{hid["Leith"]:.0f}%', 'of Leith mentions are hidden gems'), ('60%', 'of Edinburgh leasing take-up by local independents')],
        answer='Edinburgh is a stirred-drink, independent-led capital whose next five years will be shaped by the levy and by Leith, while the rest of Scotland\'s food story is coastal destinations; read this as direction, not a forecast, until the sample grows.',
        msgs=[(str(neg), 'index', 'A capital\'s appetite', 'Edinburgh over-orders the Negroni and martini more than three times; Glasgow the margarita.'),
              (f'{hid["Leith"]:.0f}%', 'hidden gems', 'Leith is the insider district', f'The highest hidden-gem share in the city; the Old Town has the most venues but just {ppv["Old Town"]:.1f} mentions each.'),
              ('£50m', 'a year', 'The levy test', 'Live since 24 July 2026. What it buys will decide whether other Scottish cities follow.')],
        chapters=[('appetite', 'The appetite', 'Edinburgh drinks like a capital', 'What the city orders more and less of than the rest of the archive.', ch1),
                  ('districts', 'The districts', 'Leith is Edinburgh\'s Southside', 'Where guests name their hidden gems, and where the visitors are.', ch2),
                  ('levy', 'The levy', 'The UK\'s first levy city is the test case', 'What is already live, what is coming and what the market is saying.', ch3),
                  ('scotland', 'The rest of Scotland', 'Outside the cities, the story is the coast', 'The towns guests name and the ingredient that could come next.', ch4),
                  ('outlook', 'Outlook', 'Direction to 2030', 'Six themes, with direction and confidence.', ch5)],
        recs=recs,
        watch=[('Levy spending', 'If the first report shows levy money in events beyond August, raise the odds on Leith and the shoulder months.'),
               ('Independent take-up', 'If the 60% share holds through 2027, the chain retreat is structural.'),
               ('Negroni and martini share', 'A fall would suggest the stirred-drinks profile is a 2026 fashion rather than the city\'s character.'),
               ('Other levies', 'Highland and other councils adopting levies would fund the coastal trail.')],
        method_stats=[(f0(tot_e), 'Edinburgh answers'), (f0(MK['Edinburgh']['v']), 'Edinburgh venues named'), (f0(sum(agg[n]['v'] for n in ar)), 'venues mapped to districts'), (f0(CM['totals'][2]), 'rest-of-Scotland answers')],
        method='<p>City index as in No. 12. Edinburgh districts use venues with a known address, assigned to the nearest of eight district centres within 1.3 km. Town mentions use venue locations from guest answers. This report is directional: no quarterly projections are made for Edinburgh because the quarterly samples are too small.</p>',
        sources=SRC_LIST(['elevy', 'elevy50', 'eindie', 'seaweed', 'kelp', 'wfm']),
        card=(str(neg), 'Edinburgh\'s Negroni index: a capital\'s appetite'),
        blurb='The capital\'s appetite, Leith\'s rise, the levy test and the coastal story, read as direction to 2030.'))


# ------------------------------------------------------------------ 14 Ten forces to 2031
def r_forces():
    ex = Ex()
    sp, ck = item('a', 'Spirits', 'groups'), item('a', 'Cocktails', 'groups')
    veg, pot = item('d', 'Vegetables and salad', 'groups'), item('d', 'Potatoes and fries', 'groups')
    fish = item('m', 'Cod, hake and white fish')
    asd = item('d', 'Asian', 'groups')
    F = [
        (1, 'The appetite shrinks', '£1bn', 'less out-of-home spend by 2031 from weight-loss drugs', f'IGD expects GLP-1 medicines to take almost £1bn out of eating-out spend by 2031 ({S("glp1")}). Users eat less and drink less; they still go out. Portions, protein and price per plate all change.', '2027 onward', 'down'),
        (2, 'A generation drinks less', '24%', 'of adults did not drink in 2024, up from 19% in 2022', f'Fewer than 2% of people in their 20s drink daily, against 14% in their 60s ({S("drink")}). The bar has to make money from fewer, better drinks and a serious alcohol-free list.', 'Now', 'down'),
        (3, 'Drink less, drink better', f'{pts(sp["move"])} pts', 'spirits as a share of dream drinks, a clear move', f'Spirits rose from {f1(sp["early"])}% to {f1(sp["late"])}% of dream drinks and cocktails fell {abs(ck["move"]):.0f} points. Whisky and lager lead. Guests are moving from novelty to the classic pour.', 'Now', 'mixed'),
        (4, 'The cost stack keeps rising', '4+', 'licensed sites closing a day in Britain at the end of 2025', f'Wages (£12.71 from April 2026), rates (Scottish pubs up 77%) and energy keep rising; 382 sites closed in one quarter ({S("niq")}). The middle of the market is the most exposed.', 'Now to 2029', 'down'),
        (5, 'Cities tax visitors to fund themselves', '£66m', 'a year from the Edinburgh and Glasgow levies combined', f'Edinburgh\'s 5% levy went live in July 2026 (up to £50m a year); Glasgow\'s starts in January 2027 (about £16m) ({S("elevy")}, {S("glevy")}). Events and visitor spending will be planned around the money.', '2026 onward', 'up'),
        (6, 'Vegetables move to the middle', f'{pts(veg["move"])} pts', 'vegetable and salad sides, a clear move', f'Vegetable sides rose and potato sides fell {abs(pot["move"]):.0f} points. Mediterranean sides are up too. This is guests choosing vegetables, not being told to.', 'Now', 'up'),
        (7, 'Provenance becomes the point', f'{PT["Local, seasonal and Scottish produce"]}', f'of {POS["answers"]} guests want more local and seasonal food, the top answer', f'Asked which trend they want more of, guests name local, seasonal and Scottish produce more than anything else. White fish mains rose from {f1(fish["early"])}% to {f1(fish["late"])}%, a clear move.', 'Now to 2031', 'up'),
        (8, 'Hype burns out faster', '113', 'guests want matcha gone; 105 want Dubai chocolate gone', 'Viral trends now reach the "bin it" list within a year of peaking. Novelty still sells for a season, but it no longer builds a reputation.', 'Now', 'mixed'),
        (9, 'Asia keeps arriving', f'{pts(asd["move"])} pts', 'Asian sides, a clear move', f'Korean, Japanese and South-East Asian flavours move from specialists to mainstream menus: hojicha, pandan, buldak and koji are all on 2027 trend lists ({S("datassential")}).', '2027 to 2030', 'up'),
        (10, 'The format gets rethought', f'{PT["Small plates and sharing"]}', f'guests want more small plates, while 35 want them gone', 'Small plates are the only trend that is both loved and loathed. Set menus, solo-friendly portions, chef\'s counters and short menus are the formats that follow.', '2026 to 2029', 'mixed'),
    ]
    imp = {1: .82, 2: .78, 3: .68, 4: .92, 5: .6, 6: .42, 7: .68, 8: .28, 9: .38, 10: .58}
    unc = {1: .66, 2: .2, 3: .56, 4: .1, 5: .3, 6: .26, 7: .14, 8: .36, 9: .74, 10: .84}
    ch1 = forces(F)
    mx_ = matrix([(n, t, imp[n], unc[n]) for n, t, *_ in F], xl=('More certain', 'Less certain'), yl=('Lower impact', 'Higher impact'),
                 q=('Prepare scenarios', 'Plan for it', 'Track it', 'Wildcards'))
    when = [(f'{n:02d}. {t}', 'k1' if d == 'up' else 'k2' if d == 'down' else 'k3', a, b, hz) for (n, t, s, sl, body, hz, d), (a, b) in zip(F, [(2027, 2031), (2025, 2031), (2025.5, 2028.5), (2025, 2029.5), (2026.56, 2031), (2025.75, 2029), (2026, 2031), (2025.5, 2027.5), (2026.5, 2030.5), (2026, 2029.5)])]
    ch2 = (ex('Four forces are both big and near-certain: plan for them now', 'Each force placed by our view of its impact on Scottish hospitality and how certain it is.', mx_,
              'Dream Menu assessment', (['Force', 'Impact (0 to 1)', 'Uncertainty (0 to 1)'], [[t, imp[n], unc[n]] for n, t, *_ in F]))
           + ex('When each force bites', 'Bars show when each force is strongest. Indigo: growing; amber: shrinking demand or margin; teal: reshaping. The dotted line is today.',
                roadmap(when, 2025, 2031, now=2026.83), 'Dream Menu assessment from the sources cited on each force', (['Force', 'From', 'To'], [[a, ym(s), ym(e)] for a, _, s, e, _ in when])))
    panels = [fanp('Spirits (of dream drinks)', 'a', 'Spirits'), fanp('Cocktails (of dream drinks)', 'a', 'Cocktails', k='k2'),
              fanp('Vegetables and salad (of sides)', 'd', 'Vegetables and salad'), fanp('Potatoes and fries (of sides)', 'd', 'Potatoes and fries', k='k2'),
              fanp('White fish (of mains)', 'm', 'Cod, hake and white fish', level='cats'), fanp('Asian (of sides)', 'd', 'Asian')]
    tags = sorted(PT.items(), key=lambda x: -x[1])[:12]
    ch3 = (ex('Forces 3, 6, 7 and 9 already show in what guests choose', 'Share of dream choices each quarter, with a projection on the recent trend to Q4 2027. Each panel has its own scale.', fan_multiples(panels, XL), f'{DM_SRC}. Projection method in the appendix.', fan_data(panels))
           + ex('What guests want more of: local and seasonal food comes first', f'"Is there a trend you\'d like to see more of?" {POS["answers"]} answers, 13 August to 29 October 2026, coded by Dream Menu. One answer can name more than one.',
                hbar(tags, on={tags[0][0]}), 'Dream Menu interviews; hand-coded, counts approximate', (['Theme', 'Answers'], [[a, b] for a, b in tags])))
    imp_rows = [
        ['<b>01 The appetite shrinks</b>', 'Half portions, protein-led plates, price per plate not per head', 'Smaller pack formats, protein lines', 'Fewer covers needed per site; value formats win'],
        ['<b>02 A generation drinks less</b>', 'A real alcohol-free list, priced for margin', 'Premium soft drinks and alcohol-free', 'Wet-led bars are the riskiest assets'],
        ['<b>03 Drink less, drink better</b>', 'Shorter cocktail lists; a whisky and spirits offer', 'Spirits and whisky ranging and training', 'Bars with a food or experience angle'],
        ['<b>04 The cost stack</b>', 'Set menus, fewer dishes, less waste', 'Price holds and cost-engineered recipes', 'Distress sales and better entry prices'],
        ['<b>05 Visitor levies</b>', 'Join the events calendar', 'Event packs and pop-up bars', 'Hotel-adjacent and event-district units'],
        ['<b>06 Vegetables move to the middle</b>', 'A hero vegetable side', 'Premium vegetables and dressings', 'Lower food cost per plate'],
        ['<b>07 Provenance</b>', 'Name farms, boats and makers', 'Scottish-sourced ranges with stories', 'Destination dining outside the cities'],
        ['<b>08 Hype burns out</b>', 'One special at a time, retired fast', 'Short-run limited editions', 'Avoid concept bets built on one trend'],
        ['<b>09 Asia keeps arriving</b>', 'One Asian-led dish per course', 'Pastes, ferments and flavours', 'Asian concepts outside the centre'],
        ['<b>10 Format rethink</b>', 'Clear portions; counters and set menus', 'Portion-controlled formats', 'Smaller, more flexible units'],
    ]
    ch4 = table(['Force', 'For operators', 'For suppliers', 'For investors and property'], imp_rows)
    recs = [('Plan for the four certain forces this year', 'Costs, less drinking, provenance and visitor levies are high-impact and near-certain. Put each into the 2027 plan with an owner.', 'High', 'Low', 'Now'),
            ('Write a smaller-appetite menu', 'Half portions, protein-led dishes and price per plate protect covers as weight-loss drugs spread.', 'High', 'Medium', 'During 2027'),
            ('Rebuild the drinks list for fewer, better drinks', 'Spirits up, cocktails down and young guests drinking less all point the same way.', 'High', 'Low', 'Next menu change'),
            ('Make provenance specific', 'Local and seasonal is the most-wanted trend. Name the farm, the boat and the maker.', 'Medium', 'Low', 'Now'),
            ('Retire one hype item a season', 'Hype burns out within a year. Keep novelty to a single, time-limited special.', 'Medium', 'Low', 'Every season'),
            ('Track the wildcards quarterly', 'Weight-loss drug uptake and new formats are the least certain. Quarterly data shows which way they break.', 'Medium', 'Low', 'Quarterly')]
    return render(dict(slug='ten-forces', ex=ex, status='sample', aud='forecast venue supplier investor public', **META['ten-forces'],
        title='Ten forces <em>to 2031</em>', desc='The ten long-term forces that will reshape eating out in Scotland to 2031, with evidence, timing, impact and what to do about each.',
        stand='Weight-loss drugs, a generation drinking less, visitor levies and a menu turning to vegetables and fish: the ten forces that will reshape eating out in Scotland over the next five years, and what to do about each.',
        client='Any business planning beyond next quarter', question='What will reshape eating out in Scotland over the next five years?', evidence=f'Six quarters of Dream Menu data, {POS["answers"]} trend answers, published research',
        kpis=[('£1bn', 'less out-of-home spend by 2031 from weight-loss drugs'), ('24%', 'of adults did not drink in 2024'), (f'{pts(sp["move"])} pts', 'spirits as a share of dream drinks'), ('£66m', 'a year from Scotland\'s two city levies')],
        answer='The next five years will reward businesses that sell less but better: smaller portions, fewer and better drinks, vegetables, fish and named provenance, paid for in part by visitors through the new levies.',
        msgs=[('4', 'forces', 'Plan for these now', 'Rising costs, a generation drinking less, provenance and visitor levies are both high-impact and near-certain.'),
              ('3', 'to prepare for', 'Prepare scenarios', 'How far weight-loss drugs spread, how durable the drinks shift is and how formats change are all big but uncertain.'),
              ('4', 'already visible', 'The data is ahead of the headlines', 'Spirits, vegetables, white fish and Asian sides are already moving in Dream Menu answers.')],
        chapters=[('forces', 'The ten forces', 'Ten forces will reshape eating out by 2031', 'Each with the number that matters, the evidence and when it bites.', ch1),
                  ('priority', 'Priority', 'Four forces are big and near-certain', 'Impact against certainty, and the timeline.', ch2),
                  ('evidence', 'The evidence', 'Four forces already show in what guests choose', 'Dream Menu demand data, projected on the recent trend.', ch3),
                  ('implications', 'Implications', 'What each force means for you', 'By audience: operators, suppliers, investors and property.', ch4)],
        recs=recs,
        watch=[('Weight-loss drug uptake', 'Faster uptake than IGD expects would move force 1 into "plan for it".'),
               ('Alcohol-free share', 'If alcohol-free starts to gain share of dream drinks, force 2 has reached the menu.'),
               ('Levy spending', 'Where the money goes decides whether force 5 lifts the whole year or only August.'),
               ('Small plates', 'A clear rise in the "bin it" count would confirm the format shift in force 10.')],
        method_stats=[('10', 'forces'), ('6', 'quarters of demand data'), (str(POS['answers']), 'trend answers coded'), (str(len(SRC)), 'published sources')],
        method=FC_METHOD + '<p>Impact and certainty scores are Dream Menu judgement, made before reading the demand data so that the data could confirm or contradict them. Trend answers come from the question added on 13 August 2026 and are coded by hand.</p>',
        sources=SRC_LIST(['glp1', 'drink', 'niq', 'rates', 'elevy', 'glevy', 'datassential', 'bidfood', 'wfm']),
        card=('10', 'forces reshaping Scottish eating out to 2031'),
        blurb='Weight-loss drugs, less drinking, visitor levies and the turn to vegetables and fish: ten forces to 2031.'))


# ------------------------------------------------------------------ 15 The edge of the menu
def r_niche():
    ex = Ex()
    STG = [('Fringe', 'A handful of venues'), ('Early adopters', 'Chefs and specialists'), ('Crossing over', 'Independents take it up'), ('Mainstream', 'On chain menus'), ('Past the peak', 'Fatigue sets in')]
    BN = dict(BIN)
    # name, stage, confidence, when (label), start, end, what, signal, who
    W = [
        ('Dirty soda', 0, 'Low', 'Maybe never', 2027, 2030, 'Cola or soda with cream, syrups and lime, from Utah', '1 guest asked for it; big US coverage. Sugar and Scotland\'s Irn Bru loyalty make it a hard sell.', 'Soft drinks brands'),
        ('West African fine dining', 0, 'Low', '2030+', 2028, 2031, 'Suya, jollof and fermented flavours at the top end', f'Michelin stars for Chishuru and Akoko in London ({S("westaf")}); not yet in Scotland.', 'Investors, chefs'),
        ('Phone-free dining', 0, 'Low', '2029', 2027, 2029.5, 'Pouches for phones, no filming at the table', f'1 guest asked for it; 45 want filming food gone. A reaction to the camera.', 'Operators'),
        ('Koji and koji milk', 0, 'Low', '2029', 2027.5, 2029.5, 'Japanese mould ferment used for umami, now in oat milk', f'On the 2027 Datassential list ({S("datassential")}). Chef-led for now.', 'Chefs, dairy-free brands'),
        ('Hojicha', 1, 'Medium', '2028', 2026.5, 2028.3, 'Roasted green tea: nutty, lower caffeine, less bitter than matcha', f'1 guest named it; trade press asks if it is matcha\'s successor ({S("hojicha")}). Matcha tops the "bin it" list ({BN.get("Matcha", 0)}).', 'Cafés, drinks brands'),
        ('Pandan', 1, 'Medium', '2028', 2026.5, 2028.5, 'South-East Asian leaf: grassy vanilla, bright green', f'Part of {PT["Asian dessert flavours (ube, pandan, black sesame, kinako)"]} guests asking for Asian dessert flavours; Black Sheep Coffee launched pandan drinks in the UK in April 2026 ({S("pandan")}).', 'Dessert and bakery'),
        ('Black sesame', 1, 'Medium', '2028', 2026.5, 2028.5, 'Toasted, nutty, grey-black: ice cream, buns, lattes', f'Tipped as an "it" flavour ({S("sesame")}); named by Glasgow guests alongside ube and kinako.', 'Ice cream, bakery'),
        ('Scottish seaweed', 1, 'Medium', '2029', 2027, 2029.5, 'Kelp, dulse and sugar kelp as seasoning, butter and side', f'Tipped as the next global food trend ({S("seaweed")}); kelp crofting is scaling ({S("kelp")}).', 'Suppliers, coastal venues'),
        ('Gildas and conservas', 1, 'Medium', '2028', 2026.5, 2028.3, 'Basque pintxo on a stick; premium tinned fish', f'1 guest named gildas; tinned fish is "the latest trend on the table" ({S("tinned")}).', 'Bars, wine bars'),
        ('Omakase and chef\'s counters', 1, 'Medium', '2028', 2026, 2028.5, 'Chef chooses; guests sit at the pass', f'{PT[OMK]} guests asked for it. Small units, high spend per head.', 'Operators, landlords'),
        ('Nose to tail cuts', 1, 'Low', '2029', 2026.5, 2029.5, 'Tongue, cheek, offal, treated as the main event', f'{PT["Nose to tail (beef tongue)"]} guests asked for beef tongue and similar; fits the cost-cutting and provenance forces.', 'Butchers, chefs'),
        ('Crispy rice', 1, 'Low', '2028', 2026.75, 2028.3, 'Pressed, fried rice squares topped with tuna or salmon', '1 guest named it; widespread in US Japanese-fusion menus.', 'Asian concepts'),
        ('Luxury bites', 1, 'Low', '2028', 2026.5, 2028.5, 'A caviar bump, one piece of bluefin: luxury by the bite', f'{PT["Luxury made accessible (caviar, bluefin)"]} guests asked for luxury made accessible.', 'Cocktail bars, seafood'),
        ('Ferments and pickles', 2, 'High', '2027', 2025.5, 2027.5, 'Kimchi, miso, house pickles, wild beer and natural wine', f'{PT["Ferments, pickles and miso"]} guests asked for more; "Function and Ferment" is a Bidfood 2027 trend ({S("bidfood")}).', 'Suppliers, all menus'),
        ('Korean, beyond fried chicken', 2, 'Medium', '2027', 2025.75, 2027.75, 'Buldak heat, makgeolli, Korean barbecue', f'{PT["Korean"]} guests asked for Korean; buldak and makgeolli are on 2027 lists ({S("datassential")}). Asian sides are a clear riser.', 'Operators, suppliers'),
        ('Retro revival', 2, 'High', '2027', 2025.75, 2027.5, 'Prawn cocktail, Black Forest gâteau, school-dinner puddings', f'{PT["Retro and nostalgia dishes"]} guests asked for it, the third-biggest theme.', 'Pubs, dessert suppliers'),
        ('Single-dessert specialists', 2, 'Medium', '2027', 2025.75, 2027.5, 'Shops that do one thing: tiramisu, cheesecake, gelato', f'{PT["Tiramisu and single-dessert specialists"]} guests named them; tiramisu is Glasgow\'s favourite dessert.', 'Landlords, dessert brands'),
        ('Smaller portions and protein', 2, 'High', '2027', 2026.25, 2027.75, 'Half portions, protein-led plates, calorie clarity', f'{PT["Health, protein and lighter options"]} guests asked for it; weight-loss drugs will cut spend by almost £1bn ({S("glp1")}).', 'All'),
        ('Regional Mexican', 2, 'Medium', '2028', 2026, 2028.3, 'Al pastor, Mexico City street food, salsa negra', f'1 guest asked for al pastor; Mexico City cuisine is on the 2027 lists ({S("datassential")}).', 'Operators'),
        ('Small plates', 3, 'High', 'Now', 2023, 2026, 'Sharing plates across the table', f'{PT["Small plates and sharing"]} guests want more; {BN.get("Small plates", 0)} want them gone. Loved and loathed.', 'Operators'),
        ('Tiramisu', 3, 'High', 'Now', 2024, 2026, 'The default dessert of the decade', 'The most-named dessert in Glasgow, holding its share. A classic now, not a trend.', 'Dessert suppliers'),
        ('Matcha', 4, 'High', 'Fading by 2027', 2024, 2027, 'Green tea in everything', f'Top of the "bin it" list ({BN.get("Matcha", 0)}). Settling as a drink, leaving desserts.', 'Cafés'),
        ('Dubai chocolate', 4, 'High', 'Fading now', 2025, 2026.75, 'Pistachio, kataifi and chocolate', f'{BN.get("Dubai chocolate", 0)} want it gone; nobody asked for more.', 'Dessert suppliers'),
        ('Hot honey', 4, 'High', 'Fading by 2027', 2024, 2027.25, 'Chilli honey on pizza, chicken and halloumi', f'{BN.get("Hot honey", 0)} want it gone; {PT["Hot honey and flavoured honey"]} still want more.', 'Pizza, chicken concepts'),
        ('Pistachio everything', 4, 'Medium', 'Fading by 2027', 2024.5, 2027.25, 'Pistachio cream in croissants, lattes, desserts', f'{BN.get("Pistachio (everything)", 0)} want it gone; {PT["Pistachio"]} want more. Expect it to settle in gelato.', 'Bakery, coffee'),
        ('Loaded fries', 4, 'High', 'Fading now', 2023, 2026.5, 'Fries buried under toppings', f'Down from {f1(item("d", "Loaded fries")["early"])}% to {f1(item("d", "Loaded fries")["late"])}% of dream sides, a clear fall; {BN.get("Loaded and dirty food", 0)} want loaded food gone.', 'Operators'),
    ]
    nW = len(W)
    up = [w for w in W if w[1] <= 2]
    ch1 = (ex(f'{nW} items on one curve: most of what is coming is still with chefs and specialists', 'Each item placed at its current stage of adoption in Scotland. Hover a chip for the evidence.',
              lanes(STG, [(w[0], w[1], w[2], w[3], w[7]) for w in W]),
              f'Dream Menu assessment from {DM_SRC}, {POS["answers"]} coded trend answers, the "bin it" question and the published sources in each profile',
              (['Item', 'Stage', 'Confidence', 'Mainstream in Glasgow'], [[w[0], STG[w[1]][0], w[2], w[3]] for w in W]))
           + sowhat('menu developers', 'The useful part of the curve is the middle. Fringe items are too early to bet on and items past the peak are already costing goodwill. The six items crossing over now are where a menu or a range can lead without gambling.'))
    led = [('Matcha', 0, BN.get('Matcha', 0)), ('Dubai chocolate', 0, BN.get('Dubai chocolate', 0)), ('Filming food', PT['Phone-free dining and dress codes'], BN.get('Filming food and mukbang', 0)),
           ('Loaded and dirty food', 0, BN.get('Loaded and dirty food', 0)), ('Small plates', PT['Small plates and sharing'], BN.get('Small plates', 0)),
           ('Hot honey', PT['Hot honey and flavoured honey'], BN.get('Hot honey', 0)), ('Pistachio', PT['Pistachio'], BN.get('Pistachio (everything)', 0)),
           ('Local and seasonal', PT['Local, seasonal and Scottish produce'], 0), ('Retro and nostalgia', PT['Retro and nostalgia dishes'], 0), ('Ferments and pickles', PT['Ferments, pickles and miso'], 0)]
    ch2 = (ex('The hype ledger: what guests want gone outweighs what they want more of, except for small plates', 'Mentions of each theme in the "bin it" question (left) and the "more of" question (right). The two questions have different sample sizes, so compare shapes, not totals.',
              ledger([(a, p, n) for a, p, n in led]), f'{DM_SRC}; "bin it" answers since July 2025; "more of" answers since 13 August 2026', (['Theme', 'Want it gone', 'Want more'], [[a, n, p] for a, p, n in led]))
           + '<div class="prose"><p>Two patterns repeat. First, a trend reaches the "bin it" list within about a year of its peak: matcha and Dubai chocolate went from novelty to irritation inside 2025 and 2026. Second, what guests ask for instead is rarely another novelty. Local and seasonal food, retro classics and ferments all point the same way: real food with a story, made properly. The exception is small plates, the one trend that is both loved and loathed, which means the format is right and the execution (portion, price, pacing) is what guests are judging.</p></div>')
    rm = [(w[0], 'k1' if w[2] == 'High' else 'k3' if w[2] == 'Medium' else 'k0', w[4], w[5], f'{STG[w[1]][0]}; {w[3]}') for w in sorted(up, key=lambda w: (w[5], w[4]))]
    ch3 = (ex('When the arrivals reach mainstream Glasgow menus', 'Bars run from first sightings in Scotland to the point we expect the item on mainstream Glasgow menus (the dot). Indigo: high confidence; teal: medium; grey: speculative. The dotted line is today.',
              roadmap(rm, 2025, 2031, now=2026.83), 'Dream Menu judgement from the evidence in each profile', (['Item', 'First sightings', 'Mainstream', 'Confidence'], [[w[0], ym(w[4]), w[3], w[2]] for w in sorted(up, key=lambda w: (w[5], w[4]))]))
           + sowhat('suppliers', 'Most arrivals take two to three years from first sightings to mainstream in Glasgow, usually by way of London and then Edinburgh. That gap is the window to develop, test and range a product before demand peaks.'))
    prof = table(['Item', 'What it is', 'The signal', 'Stage', 'Mainstream in Glasgow', 'Confidence', 'Who should act'],
                 [[f'<b>{esc(w[0])}</b>', esc(w[6]), w[7], STG[w[1]][0], esc(w[3]), w[2], esc(w[8])] for w in sorted(W, key=lambda w: (w[1], w[0]))])
    tells = ('<ul class="cs-msgs" style="margin-top:18px">'
             '<li><span class="n">01</span><h3>A chef names it before a guest does</h3><p>Items start in chef and staff answers. When guests start naming them unprompted, the item is crossing over.</p></li>'
             '<li><span class="n">02</span><h3>It arrives as a flavour, then a dish</h3><p>Pandan and black sesame arrive in lattes and ice cream first. A dedicated dish is the sign of the next stage.</p></li>'
             '<li><span class="n">03</span><h3>Edinburgh first, Glasgow a year later</h3><p>Stirred drinks and specialist formats tend to land in Edinburgh first; Glasgow adopts and scales.</p></li>'
             '<li><span class="n">04</span><h3>The "bin it" list is the peak</h3><p>When an item first appears in "bin it" answers, it has peaked. Retire it within two seasons.</p></li></ul>')
    ch4 = prof + tells
    recs = [('Range ferments and pickles now', f'Crossing over with high confidence: {PT["Ferments, pickles and miso"]} guests asked for more, and it fits the provenance and vegetable forces.', 'High', 'Low', 'Now'),
            ('Retire Dubai chocolate, and limit pistachio and hot honey to one dish each', f'{BN.get("Dubai chocolate", 0)}, {BN.get("Pistachio (everything)", 0)} and {BN.get("Hot honey", 0)} guests want them gone. Each is costing goodwill.', 'Medium', 'Low', 'Now'),
            ('Swap matcha for hojicha on the drinks list', 'Keeps the green-tea guest and leaves the most-binned trend behind.', 'Medium', 'Low', 'Next menu change'),
            ('Build a winter retro menu', f'{PT["Retro and nostalgia dishes"]} guests asked for retro classics: prawn cocktail, Black Forest gâteau, school puddings. Low cost, high affection.', 'High', 'Low', 'Winter 2026'),
            ('Develop smaller-portion and protein lines', 'High confidence and growing, driven by weight-loss drugs. Suppliers who are ready in 2027 set the standard.', 'High', 'Medium', 'During 2027'),
            ('Trial one Asian dessert flavour in summer 2027', 'Pandan or black sesame in ice cream or a bun, as a limited run. Cheap to test and early on the curve.', 'Medium', 'Low', 'Spring 2027'),
            ('Partner a Scottish seaweed producer', 'Early, but uniquely Scottish. A supplier who develops it now owns the story if it crosses over.', 'Low', 'Medium', '2028')]
    return render(dict(slug='edge-of-the-menu', ex=ex, status='sample', aud='forecast supplier venue', **META['edge-of-the-menu'],
        title='The edge <em>of the menu</em>', desc=f'A watchlist of {nW} niche foods, drinks and formats that could reach Scottish menus, placed on an adoption curve with timing and confidence.',
        stand=f'Hojicha, pandan, seaweed, gildas and the retro revival: {nW} niche items on one adoption curve, with when we expect each on mainstream Glasgow menus, how sure we are, and which trends are already burning out.',
        client='A food supplier or menu development team', question='Which niche items will reach Scottish menus next, and when?', evidence=f'{POS["answers"]} trend answers, "bin it" answers, six quarters of data, trade research',
        kpis=[(str(nW), 'items on the watchlist'), (str(sum(1 for w in W if w[1] == 2)), 'crossing over now'), (str(BN.get('Matcha', 0)), 'guests want matcha gone, the top of the list'), ('2 to 3', 'years from first sighting to mainstream Glasgow')],
        answer='The next wave is real food with a story (ferments, retro classics, smaller protein-led plates, Asian dessert flavours) rather than another viral novelty, and it reaches mainstream Glasgow menus two to three years after it first appears.',
        msgs=[(str(sum(1 for w in W if w[1] == 2)), 'crossing over', 'Where to lead', 'Ferments, Korean, retro, single-dessert shops, smaller portions and regional Mexican are moving from specialists to independents now.'),
              (str(BN.get('Matcha', 0) + BN.get('Dubai chocolate', 0)), '"bin it" votes', 'Hype burns out in a year', 'Matcha and Dubai chocolate went from novelty to irritation inside two years.'),
              ('2 to 3', 'years', 'The window', 'From first sighting to mainstream Glasgow menus, usually by way of London and Edinburgh.')],
        chapters=[('curve', 'The curve', f'{nW} items on one adoption curve', 'Where each item sits today, and how sure we are.', ch1),
                  ('hype', 'The hype ledger', 'What guests want gone outweighs what they want more of', 'Set side by side, the two questions show what is burning out and what replaces it.', ch2),
                  ('arrivals', 'Arrivals', 'When the arrivals reach Glasgow', 'Expected timing for the items on the way up.', ch3),
                  ('profiles', 'Profiles', f'All {nW} items, and how to spot the next one', 'What each is, the signal behind it, timing, confidence and who should act.', ch4)],
        recs=recs,
        watch=[('New "bin it" entries', 'The first "bin it" mention of an item on the way up means it has peaked faster than expected.'),
               ('Guest-named arrivals', 'An item named by three or more guests in a quarter moves up a stage.'),
               ('Hojicha against matcha', 'If matcha leaves the "bin it" list without hojicha rising, green tea fatigue is general, not matcha-specific.'),
               ('Seaweed supply', 'Kelp crofting volumes and price decide whether seaweed can reach chain menus.')],
        method_stats=[(str(nW), 'items assessed'), (str(POS['answers']), 'trend answers coded'), (f0(sum(v for _, v in BIN)), '"bin it" mentions (top 10)'), ('5', 'adoption stages')],
        method='<p>Stage, timing and confidence are Dream Menu judgement, combining what guests say (the "more of" and "bin it" questions), what they choose (six quarters of dream dishes and drinks) and published trade research. "Mainstream in Glasgow" means we would expect to find the item on menus in several chains or on most independent menus in a district. Confidence is high where guest data and outside research agree, medium where one leads, and low where the item is speculative. The "more of" question began on 13 August 2026; answers were coded by hand and counts are approximate.</p>',
        sources=SRC_LIST(['hojicha', 'pandan', 'sesame', 'seaweed', 'kelp', 'tinned', 'westaf', 'datassential', 'bidfood', 'wfm', 'glp1']),
        card=(str(nW), 'niche items on one adoption curve, with timing'),
        blurb=f'Hojicha, pandan, seaweed, gildas and the retro revival: {nW} niche items placed on an adoption curve, with timing and confidence.'))


written = [fn() for fn in (r_night_out, r_two_cities, r_seafood, r_dessert, r_drinks, r_fatigue, r_neighbourhoods, r_critics, r_steak, r_italian, r_confidence,
                            r_glasgow_2030, r_edinburgh_2030, r_forces, r_niche)]

# ================================================================== library index
by = {r['slug']: r for r in REPORTS}
cards = ''
for s in ORDER:
    r = by[s]
    st = 'Draft briefing' if r['status'] == 'draft' else 'Provisional sample'
    who = r['client'] if r['client'].startswith('Dunns') else r['client'][0].lower() + r['client'][1:]
    cards += (f'<a href="/case-studies/{s}" data-for="{r["aud"]}"><div class="lc"><small>No. {r["no"]:02d} · {esc(r["kind"])}</small><h3>{esc(r["plain"])}</h3></div>'
              f'<div class="lb"><p>{esc(r["blurb"])}</p><span class="who">For {esc(who)} · {st}</span>'
              f'<div class="big"><b>{esc(r["card"][0])}</b><span>{esc(r["card"][1])}</span></div></div></a>')
filt = '<div class="lib-filter" role="group" aria-label="Filter reports"><button type="button" data-f="all" aria-pressed="true">All reports</button>' + ''.join(f'<button type="button" data-f="{k}" aria-pressed="false">{esc(v)}</button>' for k, v in AUD.items()) + '</div>'
idx = f'''<div class="cs-strip"><div class="wrap"><b>Dream Menu Insight Series.</b> {len(ORDER)} example reports: one draft briefing for a partner, ten provisional samples and four trend and forecast reports, built from live data to {LAST_H}.</div></div>
<section class="cs-cover"><div class="wrap">
  <div class="cs-series"><span class="no">{len(ORDER)} reports</span><span>Dream Menu Insight Series</span></div>
  <h1>Reports on <em>request</em></h1>
  <p class="cs-stand">Dream Menu turns {f0(N_ALL)} interviews, {f0(DM["meta"]["venues"])} named venues, {f0(AW["meta"]["places"])} award winners and a Scottish operator survey into reports that answer one commercial question, with the evidence on the page. These {len(ORDER)} show the range, from category deep-dives to city forecasts and a niche watchlist.</p>
  <div class="cs-kpis"><div class="cs-kpi"><b>{f0(N_ALL)}</b><span>interviews with chefs, staff and food lovers</span></div><div class="cs-kpi"><b>{f0(DM["meta"]["venues"])}</b><span>venues named, in {DM["meta"]["countries"]} countries</span></div><div class="cs-kpi"><b>{len(LOOK)}</b><span>operators in the 2026 pulse</span></div><div class="cs-kpi"><b>6</b><span>quarters of tracked demand</span></div></div>
  <div class="cs-actions"><a class="cs-btn" href="mailto:{CONTACT}?subject=Commissioned%20report">Commission a report</a></div>
</div></section>
<div class="wrap" style="padding-top:34px;padding-bottom:20px">
  <p class="cs-kicker">The library</p><h2 style="font:800 clamp(24px,3.2vw,34px)/1.1 var(--display);margin:0 0 16px">Choose a report</h2>
  {filt}<div class="lib">{cards}</div>
</div>
<div class="wrap" style="padding-top:28px;padding-bottom:40px">
  <p class="cs-kicker">How it works</p><h2 style="font:800 clamp(24px,3.2vw,34px)/1.1 var(--display);margin:0 0 16px">What every report includes</h2>
  <ul class="cs-msgs">
    <li><span class="n">01</span><h3>The answer first</h3><p>A one-sentence answer to the client's question, three findings with the number behind each, and a ranked list of what to do.</p></li>
    <li><span class="n">02</span><h3>Evidence you can check</h3><p>Numbered exhibits with the data table under each, named venues and dishes, and the method in an appendix.</p></li>
    <li><span class="n">03</span><h3>Recommendations by impact</h3><p>Each action placed by impact and effort, with timing, and the signals that would change the view.</p></li>
    <li><span class="n">04</span><h3>Quarterly follow-up</h3><p>Optional tracking each quarter, so the next report shows what moved and whether it was a clear move.</p></li>
  </ul>
  <div class="cs-next" style="margin-top:26px"><h2>Commission a report</h2><p>Category deep-dives, market-entry reads, price briefings, location reads and sector pulses, with fresh fieldwork on top of the archive where needed.</p><a class="cs-btn" href="mailto:{CONTACT}?subject=Commissioned%20report">Talk to Dream Menu</a></div>
</div>'''
written.insert(0, write('/case-studies', 'Insight Series: reports on request',
                        'Fifteen Dream Menu reports on request: night-out costs, Glasgow against Edinburgh, seafood, dessert, drinks, trend fatigue, neighbourhoods, guests and critics, steak, Italian food, operator confidence, city forecasts for Glasgow and Edinburgh to 2030, ten forces to 2031 and a niche trend watchlist.', idx))
print('wrote', len(written), 'pages')
