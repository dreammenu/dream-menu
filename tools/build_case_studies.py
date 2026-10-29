#!/usr/bin/env python3
"""Builds the public case-study pages: /case-studies and /case-studies/<slug>.

Run from the repository root after a data refresh:
  python3 tools/build_case_studies.py && python3 tools/build_nav.py

The night-out report is Gordon's drafted briefing (28 Oct 2026), set as a page. The five provisional
reports are samples of commissioned work, built from the live data files (partner-data.js,
analysis-data.js, dm-data.js, tools/data/static-counts.json), so their figures follow each refresh.
The page shell (head, header, footer) is copied from restaurant-mot.html.
"""
import datetime as dt, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CONTACT = 'contact.dreammenu@gmail.com'


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
AN = load('analysis-data.js', 'DM_ANALYSIS')
DM = load('dm-data.js', 'DM')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
MK = {m['n']: m for m in DM['markets']}
VEN = {v['i']: v for v in DM['venues']}
LAST = dt.date.fromisoformat(P['last'])
LAST_H = f'{LAST.day} {LAST:%B %Y}'
N_ALL = P['n_all']

esc = lambda s: html.escape(str(s), quote=True)
f0 = lambda x: f'{x:,.0f}'
f1 = lambda x: f'{x:.1f}'
pct = lambda a, b: round(100 * a / b) if b else 0


def trend(course):
    return P['trends'][course]


def item(course, name, level='cats'):
    for it in trend(course)[level]:
        if it.get('l') == name or it['c'] == name:
            return it
    raise KeyError(f'{course} {name}')


def city_row(label):
    for r in AN['cities']['rows']:
        if r['l'] == label:
            return r
    raise KeyError(label)


# ------------------------------------------------------------------ page shell
TPL = open('restaurant-mot.html', encoding='utf-8').read()
HEAD, FOOT = TPL[:TPL.find('<main>')], TPL[TPL.find('</main>') + len('</main>'):]


def shell(path, title, desc):
    h = HEAD
    h = re.sub(r'<title>[^<]*</title>', f'<title>{esc(title)} | Dream Menu</title>', h)
    h = re.sub(r'(<meta name="description" content=")[^"]*', rf'\g<1>{esc(desc)}', h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', rf'\g<1>{esc(desc)}', h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', rf'\g<1>{esc(title)} | Dream Menu', h)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*', rf'\g<1>https://www.dream-menu.com{path}', h)
    return h


PAGES = [  # slug, short title, client, status
    ('night-out', 'The cost of a night out', 'A food and drink distributor', 'Draft briefing'),
    ('glasgow-edinburgh', 'Two cities, two appetites', 'A restaurant group weighing a second city', 'Provisional sample'),
    ('seafood', "Scotland's seafood appetite", 'A seafood supplier', 'Provisional sample'),
    ('dessert', 'The last spend: dessert', 'A dessert maker or foodservice supplier', 'Provisional sample'),
    ('drinks', 'What Scotland drinks with dinner', 'A drinks brand or wholesaler', 'Provisional sample'),
    ('trend-fatigue', 'Trend fatigue', 'A menu development team or food editor', 'Provisional sample'),
]


def subnav(cur):
    a = ['<a href="/case-studies"' + (' aria-current=page' if cur == '' else '') + '>All case studies</a>']
    for slug, t, _, _ in PAGES:
        a.append(f'<a href="/case-studies/{slug}"' + (' aria-current=page' if cur == slug else '') + f'>{esc(t)}</a>')
    return f'<nav class="subnav" aria-label="Case studies"><div class="wrap">{"".join(a)}</div></nav>'


def banner(text):
    return f'<div class="confidential"><div class="wrap">{text}</div></div>'


def hero(eyebrow, h1, lede, facts=None):
    fx = ''
    if facts:
        fx = '<div class="facts">' + ''.join(f'<div><b>{esc(v)}</b> <span>{esc(k)}</span></div>' for v, k in facts) + '</div>'
    return f'<section class="navyband"><div class="wrap">\n  <div class="eyebrow">{eyebrow}</div>\n  <h1>{h1}</h1>\n  <p class="lede">{lede}</p>\n  {fx}\n</div></section>'


def sec(sid, h2, body, lede=None):
    ld = f'<p class="lede" style="margin-bottom:14px">{lede}</p>' if lede else ''
    return f'<section id="{sid}"><div class="wrap">\n  <h2>{h2}</h2>\n  {ld}{body}\n</div></section>'


def bars(rows, unit='', scale=None, dec=0):
    """rows: [(label, value)]; bar widths relative to scale or the largest value."""
    top = scale or max(v for _, v in rows) or 1
    out = []
    for lab, v in rows:
        val = (f'{v:,.{dec}f}' if isinstance(v, (int, float)) else esc(v)) + unit
        out.append(f'<li><span class="bl">{esc(lab)}</span><span class="bt"><i style="width:{100 * v / top:.1f}%"></i></span><span class="bv">{val}</span></li>')
    return '<ul class="bars">' + ''.join(out) + '</ul>'


def diverge(rows, scale=None):
    top = scale or max(abs(v) for _, v in rows) or 1
    out = []
    for lab, v in rows:
        w = 50 * abs(v) / top
        i = (f'<i class="pos" style="left:50%;width:{w:.1f}%"></i>' if v >= 0
             else f'<i class="neg" style="left:{50 - w:.1f}%;width:{w:.1f}%"></i>')
        out.append(f'<li><span class="bl">{esc(lab)}</span><span class="dv">{i}</span><span class="bv">{v:+.1f}</span></li>')
    return '<ul class="bars diverge">' + ''.join(out) + '</ul>'


def table(head, rows):
    th = ''.join(f'<th>{esc(h)}</th>' for h in head)
    tr = ''.join('<tr>' + ''.join(f'<td data-label="{esc(head[i])}">{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<div class="tablewrap"><table class="stack"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def cards(items):
    return '<div class="grid">' + ''.join(f'<div class="card"><h3>{h}</h3><p>{p}</p></div>' for h, p in items) + '</div>'


def card(h, body):
    return f'<div class="card"><h3>{h}</h3>{body}</div>'


def grid(*cs):
    return '<div class="grid">' + ''.join(cs) + '</div>'


def callout(b, text):
    return f'<div class="callout"><b>{b}</b> {text}</div>'


def ul(items):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'


def source(text):
    return f'<p class="source">{text}</p>'


def quote(text, who):
    return f'<blockquote class="quote"><p>&ldquo;{esc(text)}&rdquo;</p><small>{esc(who)}</small></blockquote>'


def link(href, text):
    return f'<a href="{esc(href)}" rel="noopener" target="_blank">{esc(text)}</a>'


def fresh(keys='interviews'):
    return f'<div data-fresh="{keys}"></div>'


PROVISIONAL = (f'<b>Provisional sample.</b> Built from live Dream Menu data to {LAST_H} to show the kind of report '
               f'Dream Menu writes on request. The figures are real; the client brief is illustrative and the findings '
               f'have not yet been reviewed with a client. <a href="/case-studies">About case studies</a>')


def full_commission(extra):
    base = [
        'A brief agreed with you: the questions, the markets and the decisions the report needs to support',
        'Fresh fieldwork on top of the archive: targeted interviews with guests, chefs or buyers in your category',
        'Venue-level detail: the named venues, dishes and quotes behind every figure, as a data extract',
        'Quarterly tracking, so the next report shows what moved and whether it was a clear move',
    ]
    return sec('commission', 'What a full commission adds', ul(extra + base) +
               f'<p><a class="cta" href="mailto:{CONTACT}?subject=Commissioned%20report">Ask about a report like this</a></p>')


def method(text):
    return sec('method', 'Method and limits', f'<div class="prose"><p>{text}</p><p>Dish categories were made more specific on 24 October 2026; each answer is coded to the dish itself with a parent group. A clear move means a two-proportion test between July to December 2025 and April 2026 onward came out at p &lt; 0.05. Dream Menu is qualitative fieldwork with food-literate guests, not a statistically representative survey. <a href="/how-it-works">How Dream Menu works</a>.</p></div>')


def write(path, title, desc, body):
    fn = path.strip('/') + '.html'
    os.makedirs(os.path.dirname(fn) or '.', exist_ok=True)
    open(fn, 'w', encoding='utf-8').write(shell(path, title, desc) + '<main>\n' + body + '\n</main>' + FOOT)
    return fn


written = []

# ================================================================== index
cards_html = []
for slug, t, client, status in PAGES:
    blurb = {
        'night-out': 'What food, drink and transport cost on a Glasgow night out, how to budget for one, and what it means for a supplier.',
        'glasgow-edinburgh': 'What Glasgow and Edinburgh guests name more than everyone else, and what that means for a group opening in the other city.',
        'seafood': 'Where seafood sits on the dream menu, which dishes lead, what is rising and which venues own it.',
        'dessert': 'The most open course on the menu: what guests choose, what is moving and where a supplier can protect the last spend.',
        'drinks': 'The shift from cocktails to whisky and lager, the soft-drink round and the no and low question.',
        'trend-fatigue': 'The trends guests want gone, the sides they are leaving behind and what replaces them.',
    }[slug]
    cards_html.append(f'<a class="card" href="/case-studies/{slug}" style="text-decoration:none;color:inherit"><span class="eyebrow">{esc(status)}</span><h3>{esc(t)}</h3><p>{blurb}</p><p style="font-size:13px;color:var(--muted)">Written for: {esc(client)}</p></a>')
idx = '\n'.join([
    hero('Case studies', 'Reports on <em>request</em>',
         f'Dream Menu turns {f0(N_ALL)} interviews, {f0(DM["meta"]["venues"])} named venues and a Scottish operator survey into reports that answer one commercial question. These six show the range: a cost briefing, a market-entry read, three category deep-dives and a trend piece.',
         [(f0(N_ALL), 'interviews'), (f0(DM['meta']['venues']), 'venues named'), ('55', 'operators surveyed'), ('6', 'example reports')]),
    subnav(''),
    sec('reports', 'The reports', '<div class="grid">' + ''.join(cards_html) + '</div>' + fresh('interviews venues'),
        'The night-out briefing is a working draft. The other five are provisional samples: real figures from the live data, written to an illustrative brief.'),
    sec('what', 'What you can commission', cards([
        ('Category deep-dive', 'One course, ingredient or drink: share of guests, what is rising and falling, who names it, and the venues and dishes behind it.'),
        ('Market-entry read', 'How a city or neighbourhood eats compared with everywhere else, which venues set the bar, and where the gaps are.'),
        ('Price and cost briefing', 'What a night out, a dish or a round costs, built from published benchmarks and set against what guests choose.'),
        ('Trend and fatigue tracker', 'What guests say they are tired of, what is replacing it and what that means for menus and ranges.'),
        ('Restaurant MOT', 'An independent four-week check of one venue. <a href="/restaurant-mot">See how it works</a>.'),
        ('Commissioned questions', 'Add your own questions to the interview series and get the answers back each quarter.'),
    ])),
    sec('how', 'How a commission works', '<ol class="steps">'
        '<li><span class="eyebrow">Step 1</span><h3>The question</h3><p>We agree the decision the report should support and the markets it covers.</p></li>'
        '<li><span class="eyebrow">Step 2</span><h3>The data</h3><p>The interview archive, the venue map and the operator survey, plus new fieldwork where needed.</p></li>'
        '<li><span class="eyebrow">Step 3</span><h3>The report</h3><p>A written report with charts, named venues and recommendations, and the data behind it.</p></li>'
        '<li><span class="eyebrow">Step 4</span><h3>The follow-up</h3><p>Optional quarterly tracking, so you can see what moved.</p></li></ol>'
        f'<p><a class="cta" href="mailto:{CONTACT}?subject=Commissioned%20report">Talk to us about a report</a></p>'),
])
written.append(write('/case-studies', 'Case studies: reports on request',
                     'Example Dream Menu reports: the cost of a night out in Glasgow, Glasgow against Edinburgh, seafood, dessert, drinks and trend fatigue.', idx))

# ================================================================== 1. night out (Gordon's draft)
S = lambda h, t: link(h, t)
NIQ = 'https://nielseniq.com/global/en/insights/analysis/2026/why-value-matters-more-than-ever-for-restaurants/'
no_body = '\n'.join([
    banner('<b>Draft briefing, 28 October 2026.</b> Written for Dunns Food &amp; Drinks as a Dream Menu hospitality intelligence briefing. Price grids and budgets are modelled, indicative figures, not a venue price survey. <a href="/case-studies">About case studies</a>'),
    hero('Case study · Price and cost briefing', 'The cost of a <em>night out</em> in Glasgow, 2026',
         'What food, drink and transport cost on a Glasgow night out, how to budget for one, and what it means for Dunns Food &amp; Drinks.',
         [('£74', 'a typical night, per head'), ('£34', 'on drink'), ('£30', 'on food'), ('£10', 'getting there and back')]),
    subnav('night-out'),
    sec('summary', 'Summary',
        '<div class="prose"><p>A typical night out in Glasgow costs about £74 a head in October 2026: around £30 on food, £34 on drink and £10 getting there and back. Plan £40 for a low-key pub night and £150 or more for a celebration, and add 20% because most people overspend.</p></div>'
        + cards([
            ('Drink is the biggest and most elastic line', 'A city-centre pint is £5.20 to £6.20 and a cocktail £10.50 to £13.50, so the number of cocktails decides the bill. Glasgow drink prices run about 10% below Edinburgh.'),
            ('Food is the most controllable line', 'Two courses in a mid-range Glasgow restaurant cost £30 to £40 a head; a set or pre-theatre menu saves £10 or more.'),
            ('Transport has got cheaper', "Scotland's £2 bus cap and night buses make getting home as cheap as £2, while a solo taxi is £10 to £30. The real constraint is timing, not cost."),
            ('Diners are trading down, not staying in', "Dream Menu's 2026 data shows 72% of operators with flat or falling spend per head, as guests skip dessert and the extra drink. Classics such as steak, seafood, margaritas and martinis still win the spend that remains."),
            ('For Dunns', 'The commercial prize is helping venues protect spend per head: dessert, cocktail and premium soft drink ranges, costed set-menu kits, and a quarterly Glasgow Night Out Index co-published with Dream Menu.'),
        ])),
    sec('market', 'Market context',
        '<div class="prose"><p>A night out costs around a third more than it did in 2022, and the pressure on Scottish venues is still building. Glasgow remains one of the better-value big cities in the UK, which matters for anyone pitching to, or marketing for, the city\'s hospitality trade.</p></div>'
        + ul([
            f'<b>Hospitality prices are up about 30% in four years.</b> Compound food and drink inflation for the sector has topped 30% since mid-2022, and average restaurant spend per head has risen from £25.35 to £30.08 ({S(NIQ, "NielsenIQ, 2026")}).',
            f'<b>Scottish pubs face a rates shock.</b> UKHospitality Scotland forecasts the average Scottish pub\'s business rates rising 77% in 2026/27, to £26,385 ({S("https://cater.affino.com/news/scottish-pubs-to-be-hit-with-staggering-increases-to-business-rates", "UKHospitality Scotland via Cater")}). Expect some of this to reach menu and bar prices over the next 12 months.',
            f'<b>Consumers are price-aware.</b> UK adults spend an average of £3,776 a year on nights out in pubs, bars and clubs ({S("https://www.thedrinksbusiness.com/2025/10/brits-spend-nearly-4k-per-year-on-nights-out-study-reveals/", "Aqua via The Drinks Business, Oct 2025")}), yet price is the top worry for 44% of people planning a night out ({S("https://www.thespiritsbusiness.com/2023/12/young-adults-avoid-booze-on-nights-out/", "Rekom via The Spirits Business")}).',
            '<b>Public policy is cutting the cost of getting home.</b> Scotland has capped bus singles at £2 across the SPT area from 7 September 2026 and permanently scrapped ScotRail peak fares in September 2025. Transport is the one line of the budget that has got cheaper.',
        ])
        + card('A pint of Guinness, 2026', bars([('Glasgow', 4.93), ('UK average', 5.41), ('London', 6.87)], dec=2).replace('<span class="bv">', '<span class="bv">£'))
        + source(f'Guinness prices from {S("https://www.thedrinksbusiness.com/2026/03/guinness-prices-rise-across-the-uk/", "The Drinks Business, March 2026")}. Drink in Glasgow runs roughly 10% below Edinburgh and 20% below London; food and taxis are broadly in line with the UK average outside London.')
        + '<div class="prose"><p>Glasgow\'s price advantage is a selling point for the city\'s venues, but it also caps how much of the cost stack they can pass on before losing their value reputation.</p></div>'),
    sec('food', 'Food',
        '<div class="prose"><p>Dinner on a Glasgow night out costs £18 to £45 a head for most people, with a late-night bite adding £8 to £12. Food is the most controllable line: it can be skipped, swapped for a set menu, or upgraded for a special occasion.</p></div>'
        + ul([
            f'A meal at an inexpensive Glasgow restaurant averages £17.20, and a three-course meal for two at a mid-range place £60.71 ({S("https://www.expatica.com/uk/cost-of-living/glasgow/", "Numbeo via Expatica, June 2026")}).',
            f'A dinner for two at an Italian restaurant with wine and dessert comes in around £59 ({S("https://expatistan.com/cost-of-living/comparison/sofia/glasgow", "Expatistan, Oct 2026")}).',
            f'Across the UK, the average restaurant main has risen from about £11 in 2022 to just under £12.50 ({S(NIQ, "NielsenIQ, 2026")}).',
        ])
        + table(['Food', 'Modelled cost per person (indicative)'], [
            ['Late-night bite (chippy, pizza slice, kebab)', '£8 to £12'],
            ['Casual meal (inexpensive restaurant)', '£15 to £20'],
            ['Two courses, mid-range restaurant', '£30 to £40'],
            ['Set or pre-theatre menu', '£20 to £30'],
            ['Special occasion, three courses with service', '£45 and up'],
        ])
        + source('Modelled from the Glasgow benchmarks above.')
        + '<div class="prose"><p>Glasgow\'s value strength is the middle of the market: independent bistros, small-plates spots and curry houses where two courses still come in under £35. Fine dining is priced closer to Edinburgh.</p></div>'),
    sec('drink', 'Drink',
        '<div class="prose"><p>A city-centre pint in Glasgow now sits at roughly £5.20 to £6.20, still below Edinburgh (about £6) and London (about £6.75). Drink is the single biggest and most variable line in any night-out budget, typically 40% to 65% of total spend.</p></div>'
        + ul([
            f'UK average pint: £5.34 in April 2026, up 3.3% year on year, with premium lager at £5.94 and stout at £5.74 ({S("https://www.morningadvertiser.co.uk/Article/2026/05/21/average-pint-price-rises-33-to-534-the-morning-advertiser-finds/", "Morning Advertiser, May 2026")}).',
            f'Glasgow is the second-cheapest UK city for Guinness at £4.93 a pint, against a UK average of £5.41 and £6.87 in London ({S("https://www.thedrinksbusiness.com/2026/03/guinness-prices-rise-across-the-uk/", "The Drinks Business, March 2026")}).',
            f'Edinburgh averages around £6 a pint, level with Bath and Bristol ({S("https://www.finder.com/uk/drinking-statistics", "Finder, 2026")}).',
            f'Upward pressure continues: Heineken raised wholesale prices 2.7% from February 2026 and Diageo raised draught Guinness 5.2% from April 2026 ({S("https://www.thinkmoney.co.uk/blog/pints-up-33percent-to-pound534-as-pound10-pints-arrive-in-london-what-it-means-fo/", "thinkmoney")}).',
        ])
        + '<h3>Modelled Glasgow price grid, October 2026 (indicative)</h3>'
        + table(['Drink', 'Local or suburban pub', 'City-centre bar', 'Cocktail or hotel bar', 'Club or live venue'], [
            ['Pint of standard lager', '£4.60', '£5.40', '£6.50', '£6.80'],
            ['Pint of premium lager or craft', '£5.30', '£6.20', '£7.20', '£7.50'],
            ['Pint of Guinness', '£4.90', '£5.60', '£6.60', '£6.80'],
            ['Glass of house wine (175ml)', '£6.00', '£7.50', '£9.50', '£8.50'],
            ['Spirit and mixer (single)', '£4.80', '£6.00', '£8.00', '£7.00'],
            ['Cocktail', 'n/a', '£10.50', '£13.50', '£11.00'],
            ['Soft drink or alcohol-free pint', '£2.80', '£3.80', '£4.50', '£4.50'],
        ])
        + source('City-centre bar means Merchant City and the West End. Grid built from the national and Glasgow benchmarks above, with venue-tier mark-ups typical of Scottish licensed trade pricing. Treat it as a planning model, not a price list.')
        + callout('Scottish factor: minimum unit pricing.', 'Scotland sets a floor of 65p per unit of alcohol in shops. It mostly lifts the cost of pre-drinks at home rather than bar prices, so the gap between drinking at home and drinking out is narrower in Scotland than in England.')),
    sec('transport', 'Transport',
        '<div class="prose"><p>Getting out and home costs £4 to £25 a head in Glasgow, and the choice of how to get home is the biggest swing factor. A £2 night bus and a solo £20 taxi can sit either side of the same evening.</p></div>'
        + table(['Mode', 'Cost per trip (Oct 2026)', 'Night-out notes'], [
            ['First Glasgow or Stagecoach bus, including night buses', '£2 single, capped', f'Scottish Government £2 cap across the SPT area from 7 Sept 2026 ({S("https://www.firstbus.co.uk/greater-glasgow/tickets/ps2-fare-cap", "First Bus")}). Night routes such as N2, N18, N240 and N267 run on Friday and Saturday ({S("https://www.firstbus.co.uk/greater-glasgow/plan-journey/timetables?day=sa&service=128", "First Bus")})'],
            ['First 6pm Plus ticket', '£4.75 (city, app)', f'Unlimited travel after 6pm, including night buses ({S("https://www.firstbus.co.uk/greater-glasgow/plan-journey/forthcoming-fare-changes", "First Bus fare changes")})'],
            ['Glasgow Subway', '£1.80 smartcard, £1.85 paper single', f'Last trains around 23:40 Monday to Saturday and about 18:12 on Sundays, so useful for getting in, rarely for getting home ({S("https://www.scottishdailyexpress.co.uk/news/scottish-news/blow-rangers-fans-spt-confirms-36429818", "Scottish Daily Express")}, {S("https://appsavvytraveller.com/glasgow-public-transport/", "App Savvy Traveller")})'],
            ['Black cab, city centre to West End or Southside', 'Modelled £10 to £18 at night', f'Flag fall rose to £4.50 after the 2025 review; night tariff applies from 11pm ({S("https://prod.news.stv.tv/west-central/glasgow-taxi-fares-increase-proposed-as-drivers-call-for-higher-night-charges", "STV")})'],
            ['Black cab, city centre to outer suburbs', 'Modelled £20 to £30 at night', 'Long queues at Gordon Street and Hope Street ranks after 2am'],
            ['Uber or private hire', 'Modelled £12 to £35', 'Surge pricing at closing time can add 50% to 100%'],
            ['ScotRail late train (commuter belt, Edinburgh)', 'Glasgow to Edinburgh anytime day return about £16.80', f'Peak fares permanently scrapped from 1 Sept 2025 ({S("https://www.timeout.com/uk/news/the-major-british-rail-operator-that-has-axed-all-peak-time-fares-090225", "Time Out")}). Last departures are around midnight, which cuts nights short for visitors'],
        ])
        + callout('The insight for operators:', 'the cheapest way home in Glasgow is now cheaper than one soft drink. The real constraint is not cost but timing: the Subway closes early and the last trains leave around midnight, so venues that want late spend from suburban and Edinburgh visitors are competing with the train timetable.')),
    sec('budgets', 'Modelled budgets',
        '<div class="prose"><p>A typical Saturday night out in Glasgow costs about £75 a head, a low-key night about £40, and a celebration £150 or more. The three personas below are built from the price grids above.</p></div>'
        + grid(card('Per head, by type of night', bars([('The catch-up', 40), ('The classic Saturday', 75), ('The big night', 150)]).replace('<span class="bv">', '<span class="bv">£')),
               card('How the typical night splits', bars([('Drink', 34), ('Food', 30), ('Transport', 10)]).replace('<span class="bv">', '<span class="bv">£')
                    + '<p style="font-size:13px">Drink 46%, food 41%, transport 13%. The biggest swing factors are the number of cocktails and whether the taxi home is shared.</p>'))
        + ul([
            '<b>The catch-up:</b> two cans at home, four pints at about £5.20, a chippy, bus in and night bus home',
            '<b>The classic Saturday:</b> two courses with service, five drinks mixing pints, wine and a cocktail, bus in and half a £16 to £20 taxi home',
            '<b>The big night:</b> a pre-dinner cocktail, mid-range dinner with shared wine, four drinks across a cocktail bar and club, £10 entry, a late bite and a solo taxi',
        ])
        + f'<div class="prose"><p><b>Benchmarks:</b> UK survey work has put the average night out at £45 to £73 a head over recent years, depending on the definition and who was asked ({S("https://thinkmoney.co.uk/blog/a-night-in-numbers-how-to-budget-on-nights-out", "thinkmoney")}, {S("https://www.thespiritsbusiness.com/2023/12/young-adults-avoid-booze-on-nights-out/", "Rekom via The Spirits Business")}). Allowing for roughly 30% hospitality inflation since 2022, the £74 Glasgow model sits in the middle of that range.</p></div>'),
    sec('budget', 'How to budget for a night out',
        f'<div class="prose"><p>Budget £75 a head for a standard Glasgow night out, then add a 20% buffer: most people overspend once the night gets going. In one UK survey, 78% of 18 to 35 year olds said they routinely go over their planned budget ({S("https://confidentials.com/body/boozy-brits-spend-6500-a-year-on-nights-out", "Confidentials")}).</p></div>'
        + table(['Type of night', 'Plan for', 'With 20% buffer'], [['Low-key pub night', '£40', '£48'], ['Dinner and drinks', '£75', '£90'], ['Celebration or club night', '£150', '£180']])
        + grid(card('Costs people forget', ul(['Service charge of 10% to 12.5% on restaurant bills', 'Club entry of £5 to £15 and cloakroom of £2 to £3', 'Rounds: in a group of five, buying a round of cocktails costs £50 to £65 in one go', 'Surge pricing on Uber and private hire after 2am, often 1.5 to 2 times the normal fare', 'The Sunday trap: the Subway stops around 6pm, so Sunday nights default to taxis'])),
               card('Ways to spend less without missing out', ul(['Use the £2 bus cap both ways, or the £4.75 First 6pm Plus ticket for unlimited travel after 6pm', 'Eat early: pre-theatre and set menus save £10 to £15 a head against à la carte', 'Swap one cocktail for a pint or a premium soft drink and save £5 to £8', 'Split the taxi home; a shared £18 fare is £6 each between three', 'Drink in the Southside or a local pub rather than a city-centre cocktail bar, saving up to £2 a drink'])))),
    sec('dream-menu', 'What Dream Menu data adds',
        '<div class="prose"><p>Glasgow\'s food-literate diners still go out, but they are trading down inside the bill: 72% of operators in the Dream Menu 2026 survey report spend per head flat or falling, while 87% report supplier prices rising. The interview data shows where the money still goes, and it lines up with the most expensive lines in this budget. Two datasets sit behind this section: 962 community interviews with chefs, hospitality staff, food writers and diners, and a 55-operator field survey from April 2026 (Dream Menu Hospitality Intelligence Report 2026). All mentions are unprompted.</p></div>'
        + grid(card('Dream-drink mentions, 962 interviews', bars([('Soft and diet drinks', 143), ('Beer', 116), ('Margarita', 66), ('Martini', 64)])),
               card('What pushes prices up: share of operators naming each pressure', bars([('Food input costs', 63), ('Energy and utilities', 61), ('Labour costs', 57), ('Rent, rates and property', 52), ('Consumer demand and footfall', 44), ('Debt and cashflow', 33), ('Drink input costs', 26)], unit='%')))
        + ul([
            '<b>Classic cocktails carry the premium end of the bill.</b> Margaritas (66) and martinis (64) together outrank beer (116), and these are the £10 to £13.50 drinks in the price grid. A night built on two cocktails costs roughly double a night built on two pints.',
            '<b>Soft drinks are a real part of the round.</b> Soft and diet drinks are the single most-named dream drink (143). Irn Bru beats Coca-Cola 435 to 307, and 21% chose neither. At £3.80 a time in town, no and low choices are no longer the cheap option.',
            '<b>Diners spend on classics, not gimmicks.</b> Steak is the most-named main (251), seafood leads starters (303, with scallops alone at 99) and chips lead sides (240). Dubai chocolate (124 mentions) and matcha (90) top the list of trends people want gone, so premium pricing on novelty items is resisted.',
            '<b>The extras are what get cut.</b> 42% of operators see lower spend per head locally, and operators describe guests skipping the starter, the second cocktail or the dessert. That is why the modelled budgets treat dessert and a final drink as optional lines.',
            "<b>Value price points work.</b> One operator's £30 three-course lunch has taken off, and lunch vouchers kept another fully booked through January and February. A clear, honest set price is what converts a cautious diner.",
            "<b>The late-night end is comfort food.</b> Pizza (141), kebab (36) and the chippy (23) dominate guilty pleasures, which is the £8 to £12 late-night bite line. A late-night dessert offer is one of the report's documented concept gaps.",
            '<b>Where the night happens is shifting.</b> The Barras draws 50 mentions, more than any single venue, and the Southside has the widest gap between community advocacy and press attention, with rents well below Finnieston.',
        ])
        + '<div class="prose"><p>Food input costs top the stack, and drink input costs are named by only 26%. That gap is why menu prices are rising faster than bar prices, and it is the line a food distributor can most directly help with.</p></div>'
        + source('Figures in this section are from the Dream Menu Hospitality Intelligence Report 2026 (962 interviews and the April 2026 operator survey). The live site now holds ' + f0(N_ALL) + ' interviews; the report counts are kept as published.')),
    sec('dunns', 'What this means for Dunns',
        '<div class="prose"><p>The opportunity for Dunns is to help venues protect spend per head, because that is the line customers are cutting while volume holds. Each idea below links a cost-of-night-out finding to a product, a sales conversation or a piece of joint content.</p></div>'
        + table(['Finding', 'Evidence', 'Idea for Dunns'], [
            ['Guests skip dessert and the last drink', '72% of operators report flat or falling spend per head; dessert and second cocktail are the first cuts', 'Lead sales calls with a "save the last spend" range: ready-to-plate desserts in the most-named formats (ice cream 221, sticky toffee pudding 122, tiramisu 120) and batch-friendly cocktail serves'],
            ['Classic cocktails outrank beer', 'Margarita 66 and martini 64 vs beer 116', 'Bundle tequila, gin, vermouth, citrus and premium mixers as a "Glasgow classics" bar pack, with a costed menu showing a £10 to £11 sell price at healthy margin'],
            ['Soft drinks and no/low are a large share of the round', 'Soft drinks most-named drink (143); Irn Bru 435 vs Coke 307', 'Push premium soft drinks, Scottish mixers and alcohol-free pints as margin lines, not afterthoughts; supply a menu template that prices them at £3.50 to £4.50'],
            ['Set price points convert cautious diners', '£30 three-course lunch and January vouchers cited as operator wins', 'Build costed "£22 / £30 set menu" kits from Dunns lines around the most-named dishes (steak 251, seafood starters 303, chips 240)'],
            ['Supplier prices are the top cost worry', '87% report supplier prices rising; 46% have changed or renegotiated suppliers in six months', 'A retention risk and an opening: offer price-holds on core night-out lines for one quarter, and target operators actively shopping around'],
            ['Growth is in emerging districts', 'The Barras 50 mentions; Southside has the widest advocacy-to-press gap', 'Use the Dream Menu venue map to prioritise new-account visits in the Southside, the Barras and the East End'],
            ['Late-night food is comfort food', 'Pizza 141, kebab 36, chippy 23; late-night dessert is a documented concept gap', 'Target late-opening takeaways and venues with frozen and ambient lines for the 11pm to 3am trade'],
            ['Getting home is cheaper than ever', '£2 bus cap, night buses, ScotRail peak fares scrapped', 'Help venues sell early-evening and weeknight occasions to customers who no longer need a taxi budget'],
        ])
        + callout('Suggested sequence:', 'launch the four quick wins in the first quarter, since they use existing Dunns ranges and the existing quarterly report. Build the set-menu kits and price-hold offer in the second quarter, once the Night Out Index shows which price points matter most.')
        + callout('Joint content idea: the Glasgow Night Out Index.', 'A quarterly price check of a fixed basket (pint, glass of wine, cocktail, soft drink, casual main, late-night bite, taxi home), published in the Dunns-sponsored quarterly report alongside Dream Menu demand data. It fits the existing quarterly summary and sales-team presentation, gives the press a repeatable headline number, and positions Dunns as the distributor that understands what a night out costs the customer, not only the venue.')),
    sec('sources', 'Methodology and sources',
        '<div class="prose"><p>Glasgow price grids and personas are modelled, indicative figures, not a venue price survey. They start from published national and city benchmarks below and apply typical Scottish venue-tier mark-ups. Dream Menu figures are exact counts from the 2026 report; the community sample skews food-literate and the operator survey is directional.</p></div>'
        + grid(card('Drink', ul([S("https://www.morningadvertiser.co.uk/Article/2026/05/21/average-pint-price-rises-33-to-534-the-morning-advertiser-finds/", "Morning Advertiser: average pint price rises 3.3% to £5.34"), S("https://www.thedrinksbusiness.com/2026/03/guinness-prices-rise-across-the-uk/", "The Drinks Business: Guinness prices rise across the UK"), S("https://www.finder.com/uk/drinking-statistics", "Finder: UK drinking statistics"), S("https://www.thinkmoney.co.uk/blog/pints-up-33percent-to-pound534-as-pound10-pints-arrive-in-london-what-it-means-fo/", "thinkmoney: pint prices up 3.3%")])),
               card('Food and market', ul([S(NIQ, "NielsenIQ: why value matters more than ever for restaurants"), S("https://www.expatica.com/uk/cost-of-living/glasgow/", "Expatica: cost of living in Glasgow (Numbeo data)"), S("https://expatistan.com/cost-of-living/comparison/sofia/glasgow", "Expatistan: Glasgow prices"), S("https://cater.affino.com/news/scottish-pubs-to-be-hit-with-staggering-increases-to-business-rates", "UKHospitality Scotland via Cater: Scottish pub business rates"), S("https://www.thedrinksbusiness.com/2025/10/brits-spend-nearly-4k-per-year-on-nights-out-study-reveals/", "The Drinks Business: Brits spend nearly £4k a year on nights out"), S("https://www.thespiritsbusiness.com/2023/12/young-adults-avoid-booze-on-nights-out/", "The Spirits Business: Rekom night-out spend"), S("https://thinkmoney.co.uk/blog/a-night-in-numbers-how-to-budget-on-nights-out", "thinkmoney: how to budget on nights out"), S("https://confidentials.com/body/boozy-brits-spend-6500-a-year-on-nights-out", "Confidentials: 18 to 35s and night-out budgets")])),
               card('Transport', ul([S("https://www.firstbus.co.uk/greater-glasgow/tickets/ps2-fare-cap", "First Bus: £2 fare cap"), S("https://www.firstbus.co.uk/greater-glasgow/plan-journey/forthcoming-fare-changes", "First Bus: fare changes and 6pm Plus"), S("https://www.firstbus.co.uk/greater-glasgow/plan-journey/timetables?day=sa&service=128", "First Bus: night services"), S("https://www.scottishdailyexpress.co.uk/news/scottish-news/blow-rangers-fans-spt-confirms-36429818", "Scottish Daily Express: Subway fares 2026"), S("https://appsavvytraveller.com/glasgow-public-transport/", "App Savvy Traveller: Glasgow public transport"), S("https://prod.news.stv.tv/west-central/glasgow-taxi-fares-increase-proposed-as-drivers-call-for-higher-night-charges", "STV: Glasgow taxi fare review"), S("https://www.timeout.com/uk/news/the-major-british-rail-operator-that-has-axed-all-peak-time-fares-090225", "Time Out: ScotRail scraps peak fares")])))),
])
written.append(write('/case-studies/night-out', 'The cost of a night out in Glasgow, 2026',
                     'What food, drink and transport cost on a Glasgow night out in 2026, how to budget for one, and what it means for a food and drink distributor.', no_body))

# ================================================================== 2. Glasgow and Edinburgh
CM = AN['cities']
gi, ei = CM['markets'].index('Glasgow'), CM['markets'].index('Edinburgh')
G, E = MK['Glasgow'], MK['Edinburgh']
rows = [r for r in CM['rows'] if not r['cells'][gi]['thin'] and not r['cells'][ei]['thin']]
g_hi = sorted(rows, key=lambda r: -r['cells'][gi]['idx'])
e_hi = sorted(rows, key=lambda r: -r['cells'][ei]['idx'])
top10 = lambda m: sum(VEN[i]['m'] for i in m['top'][:10])
g_top, e_top = top10(G), top10(E)
neg, mar = city_row('Negroni'), city_row('Martini')
scal, stp, tira = city_row('Scallops'), city_row('Sticky toffee pudding'), city_row('Tiramisu')
marg = city_row('Margarita')
ge_body = '\n'.join([
    banner(PROVISIONAL),
    hero('Case study · Market-entry read', 'Two cities, <em>two appetites</em>',
         f'Written for a restaurant group with a Glasgow site, weighing a first opening in Edinburgh (or the reverse). The question: how differently do the two cities eat and drink, and what would a second site need to change?',
         [(f'{neg["cells"][ei]["idx"]}', 'Edinburgh negroni index'), (f'{marg["cells"][gi]["idx"]}', 'Glasgow margarita index'),
          (f'{pct(e_top, E["mn"])}%', 'Edinburgh mentions in its top 10 venues'), (f'{pct(g_top, G["mn"])}%', 'same for Glasgow')]),
    subnav('glasgow-edinburgh'),
    sec('brief', 'The brief', '<div class="prose"><p>A group running a successful Glasgow venue wants to know whether the format travels 45 miles east. Menus, drinks lists and launch marketing all depend on how far Edinburgh guests differ, so the report compares what guests in each city name, which venues set the bar, and how concentrated each market is.</p></div>'),
    sec('findings', 'What we found', cards([
        ('Edinburgh drinks stirred, Glasgow drinks shaken',
         f'Edinburgh guests name the negroni at {neg["cells"][ei]["idx"]} and the martini at {mar["cells"][ei]["idx"]} on the index (100 = the all-market average). In Glasgow they index at {neg["cells"][gi]["idx"]} and {mar["cells"][gi]["idx"]}, while the margarita indexes at {marg["cells"][gi]["idx"]}. A Glasgow bar list built on margaritas would need a stirred, spirit-forward section in Edinburgh.'),
        ('Glasgow is the scallop city',
         f'Scallops are {f1(scal["cells"][gi]["share"])}% of Glasgow dish mentions (index {scal["cells"][gi]["idx"]}) against {f1(scal["cells"][ei]["share"])}% in Edinburgh (index {scal["cells"][ei]["idx"]}). Edinburgh still loves seafood ({f1(dict((c[0], c[2]) for c in E["cat"]).get("Seafood", 0))}% of its venue mentions against {f1(dict((c[0], c[2]) for c in G["cat"]).get("Seafood", 0))}% in Glasgow), but it is led by Leith fish venues rather than one shellfish dish.'),
        ('Pudding beats tiramisu in Edinburgh',
         f'Sticky toffee pudding indexes at {stp["cells"][ei]["idx"]} in Edinburgh and {stp["cells"][gi]["idx"]} in Glasgow; tiramisu runs the other way ({tira["cells"][gi]["idx"]} in Glasgow, {tira["cells"][ei]["idx"]} in Edinburgh). The dessert that sells in one city is not the safe bet in the other.'),
        ('Edinburgh is more concentrated',
         f'Edinburgh\'s ten most-named venues take {pct(e_top, E["mn"])}% of the city\'s {f0(E["mn"])} venue mentions; Glasgow\'s top ten take {pct(g_top, G["mn"])}% of {f0(G["mn"])}. A newcomer in Edinburgh is competing with a shorter list of strong favourites, led by {esc(VEN[E["top"][0]]["n"])}.'),
    ])),
    sec('index', 'Dish by dish', table(['Dish', 'Glasgow share', 'Glasgow index', 'Edinburgh share', 'Edinburgh index'],
        [[esc(r['l']), f'{f1(r["cells"][gi]["share"])}%', str(r['cells'][gi]['idx']), f'{f1(r["cells"][ei]["share"])}%', str(r['cells'][ei]['idx'])] for r in sorted(rows, key=lambda r: -(r['cells'][ei]['idx'] - r['cells'][gi]['idx']))])
        + source(f'Share of dish mentions tied to a venue in each market ({f0(CM["totals"][gi])} in Glasgow, {f0(CM["totals"][ei])} in Edinburgh). Index: the market\'s share against the all-market share, where 100 is average. Dishes are shown where both cities have enough mentions to read; sorted from most Edinburgh-leaning to most Glasgow-leaning.') + fresh('interviews venues'),
        'Index above 100 means the city names the dish more than guests everywhere else do.'),
    sec('venues', 'Who sets the bar', grid(
        card('Glasgow: most-named venues', bars([(VEN[i]['n'], VEN[i]['m']) for i in G['top'][:8]])),
        card('Edinburgh: most-named venues', bars([(VEN[i]['n'], VEN[i]['m']) for i in E['top'][:8]])))
        + source('Times each venue is named by guests, across every course and the hidden-gem question.')),
    sec('means', 'What it means for a second site', table(['Area', 'Glasgow format', 'Edinburgh adjustment'], [
        ['Bar list', 'Margaritas and house cocktails lead', 'Add a stirred section: negroni, martini and a freezer martini serve'],
        ['Starters', 'Scallops and shellfish carry the menu', 'Lean on white fish and named Scottish fish; keep one shellfish signature'],
        ['Dessert', 'Tiramisu is the safe choice', 'Sticky toffee pudding earns its place'],
        ['Launch', 'Many favourites, spread thin', 'Fewer, stronger favourites: aim to be talked about next to them, not instead of them'],
    ])),
    full_commission(['Neighbourhood-level reads for shortlisted sites, from Leith to Stockbridge or Finnieston to the Southside', 'Guest interviews in the target city about your existing venue and format']),
    method(f'Built from venue mentions in {f0(N_ALL)} Dream Menu interviews to {LAST_H}. Edinburgh has far fewer mentions than Glasgow ({f0(CM["totals"][ei])} against {f0(CM["totals"][gi])} dish mentions), so single-dish figures there rest on 5 to 10 mentions each and are directional.'),
])
written.append(write('/case-studies/glasgow-edinburgh', 'Two cities, two appetites: Glasgow and Edinburgh',
                     'A provisional Dream Menu case study: how Glasgow and Edinburgh guests differ on drinks, seafood and dessert, and what a second site needs to change.', ge_body))

# ================================================================== 3. Seafood
s_t, m_t = trend('s'), trend('m')
s_sea, m_sea = item('s', 'Seafood', 'groups'), item('m', 'Seafood', 'groups')
sea_cats = [it for it in s_t['cats'] if it.get('g') == 'Seafood'][:7]
cod = item('m', 'Cod, hake and white fish')
sc_s = item('s', 'Scallops')
grp = {g['g']: dict(g['top_groups']).get('Seafood') for g in P['groups']}
sea_v = sorted(DM['venues'], key=lambda v: -dict(v.get('k', [])).get('Seafood', 0))[:8]
rs = CM['markets'].index('Rest of Scotland')
sea_body = '\n'.join([
    banner(PROVISIONAL),
    hero('Case study · Category deep-dive', "Scotland's <em>seafood</em> appetite",
         'Written for a Scottish seafood supplier planning its foodservice range. The question: where does seafood sit on the dream menu, which dishes lead, what is rising and who owns it?',
         [(f'{f1(s_sea["pct"])}%', 'of dream starters are seafood'), (f'{f1(sc_s["pct"])}%', 'name scallops, the top starter'),
          (f'{f1(m_sea["pct"])}%', 'of dream mains are seafood'), (f'+{f1(cod["move"])} pts', 'white fish mains, a clear rise')]),
    subnav('seafood'),
    sec('brief', 'The brief', '<div class="prose"><p>A supplier of Scottish fish and shellfish wants to know which products to push to restaurants next year and where to find the venues that will take them. The report reads seafood across starters and mains, tracks it quarter by quarter, and names the venues guests associate with it.</p></div>'),
    sec('findings', 'What we found', cards([
        ('Seafood owns the starter',
         f'{f0(s_sea["n"])} of {f0(s_t["n"])} dream starters ({f1(s_sea["pct"])}%) are seafood, more than the next four groups combined. Scallops alone are {f1(sc_s["pct"])}%, the single most-named starter in the archive.'),
        ('White fish is the riser',
         f'Cod, hake and white fish mains rose from {f1(cod["early"])}% to {f1(cod["late"])}% of dream mains, a clear move. Seafood mains overall rose from {f1(m_sea["early"])}% to {f1(m_sea["late"])}%, not yet a clear move but heading the same way.'),
        ('The trade names it most',
         f'Seafood is {f1(grp.get("Industry", 0))}% of everything hospitality professionals name, against {f1(grp.get("Enthusiasts", 0))}% for food enthusiasts and {f1(grp.get("Creators", 0))}% for content creators. Chefs and front of house are the strongest advocates.'),
        ('A few venues carry it',
         f'{esc(sea_v[0]["n"])} alone gathers {dict(sea_v[0]["k"]).get("Seafood")} seafood mentions. Outside it, demand is spread across Leith, the West End and the coast, which leaves room for more venues to own a seafood dish.'),
    ])),
    sec('dishes', 'Which seafood leads', grid(
        card('Seafood starters, mentions', bars([(it['l'], it['n']) for it in sea_cats])),
        card('Scallops, share of dream starters by quarter', bars([(q.replace('-', ' '), v or 0) for q, v in zip(s_t['q'], sc_s['share'])], unit='%', dec=1)
             + '<p style="font-size:13px">The latest quarter is part-way through and has fewer answers, so it is shown for completeness only.</p>'))
        + fresh('interviews')),
    sec('where', 'Where guests eat it', grid(
        card('Venues with the most seafood mentions', bars([(v['n'], dict(v['k']).get('Seafood', 0)) for v in sea_v])),
        card('Scallops by market (index, 100 = average)', bars([(m, scal['cells'][i]['idx']) for i, m in enumerate(CM['markets']) if not scal['cells'][i]['thin']])))
        + quote('Hand dived Orkney scallops with chipotle, mussel, squash and pata negra from Heron in Leith.', 'Dream Menu guest')
        + quote('Scallops in anchovy butter, Crabshakk. The butter has to be soaked up with a side of skinny fries and a basket of bread!', 'Dream Menu guest')),
    sec('means', 'What it means for a seafood supplier', table(['Finding', 'Action'], [
        ['Scallops lead the starter course', 'Make hand-dived and named-origin scallops the hero line; guests repeat the provenance back word for word'],
        ['White fish mains are a clear riser', 'Build a hake and cod range for mains, portioned and sold with a simple sauce idea'],
        ['The trade is the strongest advocate', 'Lead with chef sampling and kitchen visits rather than consumer marketing'],
        ['Demand outside the top venue is spread thin', 'Target venues that guests already name for one seafood dish and help them make it a signature'],
    ])),
    full_commission(['Price and margin checks on the hero lines with operators who already list them', 'A seafood-specific question set added to the interview series for two quarters']),
    method(f'Built from {f0(N_ALL)} Dream Menu interviews to {LAST_H}. Starter and main shares use the interviews with a codable answer for that course ({f0(s_t["n"])} starters, {f0(m_t["n"])} mains). Venue figures use the mentions tied to a named venue.'),
])
written.append(write('/case-studies/seafood', "Scotland's seafood appetite",
                     'A provisional Dream Menu case study: where seafood sits on the dream menu, which dishes lead, what is rising and which venues own it.', sea_body))

# ================================================================== 4. Dessert
p_t = trend('p')
conc = {c['course']: c for c in AN['conc']}
tir, stp_i, chs = item('p', 'Tiramisu'), item('p', 'Sticky toffee pudding'), item('p', 'Baked cheesecake')
frm, ice = item('p', 'Fruit and meringue', 'groups'), item('p', 'Ice cream and frozen', 'groups')
choc = item('p', 'Chocolate desserts', 'groups')
binx = dict(P['extra']['bin'])
look = P['look']
lower = dict(look['signals']).get('Lower spend per head', 0)
des_v = sorted(DM['venues'], key=lambda v: -v.get('cs', {}).get('p', 0))[:8]
moves = [(it['c'] + ' (group)', it['move']) for it in p_t['groups']] + [(it['l'], it['move']) for it in p_t['cats'][:12]]
moves = sorted([m for m in moves if abs(m[1]) >= 1.5], key=lambda x: -x[1])
des_body = '\n'.join([
    banner(PROVISIONAL),
    hero('Case study · Category deep-dive', 'The last spend: <em>dessert</em>',
         'Written for a dessert maker or foodservice supplier. The question: dessert is the course guests cut first when money is tight, so which desserts still earn their place, and what should a range look like?',
         [(f'{f1(tir["pct"])}%', 'name tiramisu, the top dessert'), (f'{f1(stp_i["pct"])}%', 'sticky toffee pudding'),
          (f'{f1(conc["p"]["top1v"])}%', 'top dessert group share, the lowest of any course'), (f'{lower} of {look["n"]}', 'operators see lower spend per head')]),
    subnav('dessert'),
    sec('brief', 'The brief', f'<div class="prose"><p>Operators tell Dream Menu that guests are skipping the extras: {lower} of {look["n"]} in the operator survey see lower spend per head locally. A supplier wants to know which desserts guests still want enough to order, what is moving, and what to stop making.</p></div>'),
    sec('findings', 'What we found', cards([
        ('Two desserts cover almost a quarter of answers',
         f'Tiramisu ({f1(tir["pct"])}%) and sticky toffee pudding ({f1(stp_i["pct"])}%) together are {f1(tir["pct"] + stp_i["pct"])}% of {f0(p_t["n"])} dream desserts. Both are steady, with no clear move up or down.'),
        ('The most open course',
         f'The leading dessert group takes only {f1(conc["p"]["top1v"])}% of answers, against {f1(conc["s"]["top1v"])}% for seafood starters and {f1(conc["d"]["top1v"])}% for potato sides. Beyond the two favourites, there is no default dessert, which leaves room for a venue to make one its own.'),
        ('Fruit is up, baked cheesecake is down',
         f'Fruit and meringue desserts rose from {f1(frm["early"])}% to {f1(frm["late"])}%, a clear move. Baked cheesecake fell from {f1(chs["early"])}% to {f1(chs["late"])}%, also clear. Chocolate desserts are drifting down ({f1(choc["early"])}% to {f1(choc["late"])}%), not yet a clear move.'),
        ('Novelty chocolate is on the way out',
         f'Dubai chocolate is the second most-named trend guests want gone ({binx.get("Dubai chocolate", 0)} mentions) and pistachio-everything appears {binx.get("Pistachio (everything)", 0)} times. A range built on the last viral flavour is a risk.'),
    ])),
    sec('moves', 'What is moving', grid(
        card('Top dream desserts, share of answers', bars([(it['l'], it['pct']) for it in p_t['cats'][:10]], unit='%', dec=1)),
        card('Change in share, early against recent (points)', diverge(moves)))
        + source('Early: July to December 2025. Recent: April 2026 onward. Clear moves are fruit and meringue (up) and baked cheesecake (down); the rest are within normal variation.') + fresh('interviews')),
    sec('venues', 'Where guests go for dessert', card('Venues named most for dessert', bars([(v['n'], v['cs'].get('p', 0)) for v in des_v]))
        + quote('Dream dessert is the whiskey and amaro cherry ice cream from Loop and Scoop, in a tub cause cones are icky', 'Dream Menu guest')
        + source('Gelato and scoop shops appear next to restaurants: guests will walk on for dessert, which is spend a restaurant loses if its own dessert is forgettable.')),
    sec('means', 'What it means for a dessert range', table(['Finding', 'Action'], [
        ['Tiramisu and sticky toffee pudding cover almost a quarter of answers', 'Make both ready-to-plate at a quality guests notice; these are the volume lines'],
        ['Fruit and meringue is a clear riser', 'Add a seasonal fruit and meringue line (pavlova, Eton mess) that changes each quarter'],
        ['Baked cheesecake is falling', 'Hold or reduce baked cheesecake; test a lighter or Basque style instead'],
        ['Novelty flavours are fatigued', 'Avoid committing a range to Dubai chocolate or pistachio-everything'],
        ['Guests skip dessert to save money', 'Offer a smaller-format dessert at a lower price point so the course stays on the bill'],
    ])),
    full_commission(['Menu price and attachment-rate checks with operators who stock your lines', 'Late-night dessert: a concept test in Glasgow, where it is a documented gap']),
    method(f'Built from {f0(p_t["n"])} codable dessert answers in {f0(N_ALL)} Dream Menu interviews to {LAST_H}, plus the 2026 Look Ahead operator survey ({look["n"]} operators, April to May 2026) and the "bin it" question on trends guests want gone.'),
])
written.append(write('/case-studies/dessert', 'The last spend: dessert',
                     'A provisional Dream Menu case study: which desserts guests still choose, what is rising and falling, and what a dessert range should look like.', des_body))

# ================================================================== 5. Drinks
a_t, k_t = trend('a'), trend('k')
ck, sp, bc = item('a', 'Cocktails', 'groups'), item('a', 'Spirits', 'groups'), item('a', 'Beer and cider', 'groups')
wh, lg = item('a', 'Whisky'), item('a', 'Lager')
deb = SC['debates']
coke, tea, water = deb['coke'], deb['tea'], deb['water']
nolo = item('k', 'No and low alcohol', 'groups')
dmoves = sorted([(it['c'] + ' (group)', it['move']) for it in a_t['groups']] + [(it['l'], it['move']) for it in a_t['cats'][:14] if abs(it['move']) >= 1.5], key=lambda x: -x[1])
drk_body = '\n'.join([
    banner(PROVISIONAL),
    hero('Case study · Category deep-dive', 'What Scotland <em>drinks</em> with dinner',
         'Written for a drinks brand or wholesaler planning its on-trade range. The question: is the cocktail boom over, what is replacing it, and what goes in the soft-drink round?',
         [(f'{f1(ck["move"])} pts', 'cocktails, share of dream drinks'), (f'+{f1(wh["move"])} pts', 'whisky, a clear rise'),
          (f'{pct(coke["c"]["Irn Bru"], coke["n"])}%', 'choose Irn Bru over Coke'), (f'{pct(tea["c"]["Coffee"], tea["n"])}%', 'choose coffee over tea')]),
    subnav('drinks'),
    sec('brief', 'The brief', '<div class="prose"><p>A drinks business wants to know where the on-trade is heading in Scotland. The report reads the dream alcoholic drink over time, the soft drinks guests choose, and the debates that every interview ends with.</p></div>'),
    sec('findings', 'What we found', cards([
        ('Cocktails are losing share',
         f'Cocktails fell from {f1(ck["early"])}% to {f1(ck["late"])}% of dream alcoholic drinks, the largest clear move in the archive. They are still the biggest group, but the gap is closing.'),
        ('Whisky, lager and spirits are taking it',
         f'Spirits rose from {f1(sp["early"])}% to {f1(sp["late"])}%, led by whisky ({f1(wh["early"])}% to {f1(wh["late"])}%). Beer and cider rose from {f1(bc["early"])}% to {f1(bc["late"])}%, with lager clearly up. All three are clear moves.'),
        ('Irn Bru wins the round',
         f'{f0(coke["c"]["Irn Bru"])} guests choose Irn Bru, {f0(coke["c"]["Coca Cola"])} Coca-Cola and {f0(coke["c"]["Neither"])} neither ({f0(coke["n"])} answering). In Scotland, a soft-drinks list without Irn Bru is missing the favourite.'),
        ('No and low is a list, not a line',
         f'{f1(nolo["pct"])}% of dream soft drinks are mocktails or alcohol-free, and mocktails sit in the top five dream drinks overall. Guests who choose them name a specific drink and venue, so one token option undersells it.'),
    ])),
    sec('moves', 'What is moving', grid(
        card('Change in share of dream alcoholic drinks, early against recent (points)', diverge(dmoves)),
        card('Top dream alcoholic drinks, share', bars([(it['l'], it['pct']) for it in a_t['cats'][:10]], unit='%', dec=1)))
        + source('Trend tests use answers to the original single drink question, before it was split into soft and alcoholic on 23 August 2026. Early: July to December 2025. Recent: April 2026 onward.') + fresh('interviews')),
    sec('round', 'The soft-drink round and the debates', grid(
        card(f'Irn Bru or Coca-Cola? ({f0(coke["n"])} answering)', bars(sorted(coke['c'].items(), key=lambda x: -x[1]))),
        card(f'Coffee or tea? ({f0(tea["n"])} answering)', bars(sorted(tea['c'].items(), key=lambda x: -x[1]))),
        card(f'Still, sparkling or tap? ({f0(water["n"])} answering)', bars(sorted(water['c'].items(), key=lambda x: -x[1]))),
        card('Dream soft drinks by group, share', bars([(it['c'], it['pct']) for it in k_t['groups']], unit='%', dec=1))) + fresh('interviews')),
    sec('means', 'What it means for a drinks range', table(['Finding', 'Action'], [
        ['Cocktails are losing share', 'Keep the classics that still lead (spicy margarita, martini) and cut the long house list'],
        ['Whisky is a clear riser', 'Sell whisky by the dram and in highballs, with a short Scottish list staff can talk about'],
        ['Lager is up', 'A premium or local lager on draught earns its tap'],
        ['Irn Bru leads the soft round', 'List it, and price premium soft drinks as a margin line'],
        ['No and low is specific', 'Build three or four named alcohol-free serves rather than one mocktail'],
    ])),
    full_commission(['A drinks-only question set for two quarters to firm up the whisky and lager trend', 'Bartender interviews in Glasgow and Edinburgh on what guests order versus what they dream of']),
    method(f'Built from {f0(a_t["n"])} codable alcoholic drink answers and {f0(k_t["n"])} soft drink answers in {f0(N_ALL)} Dream Menu interviews to {LAST_H}, plus the debate questions every interview ends with.'),
])
written.append(write('/case-studies/drinks', 'What Scotland drinks with dinner',
                     'A provisional Dream Menu case study: cocktails losing share to whisky and lager, Irn Bru against Coke, and the no and low list.', drk_body))

# ================================================================== 6. Trend fatigue
d_t = trend('d')
pot, veg, med, bfr = (item('d', n, 'groups') for n in ('Potatoes and fries', 'Vegetables and salad', 'Mediterranean and Middle Eastern', 'Burgers and fried food'))
lf, sk, mc, gr = item('d', 'Loaded fries'), item('d', 'Skinny fries'), item('d', 'Mac and cheese'), item('d', 'Greens and creamed spinach')
bin_l, guilty = P['extra']['bin'], P['extra']['guilty']
side_moves = sorted([(it['c'] + ' (group)', it['move']) for it in d_t['groups'][:8]] + [(it['l'], it['move']) for it in d_t['cats'][:12] if abs(it['move']) >= 1.8], key=lambda x: -x[1])
tf_body = '\n'.join([
    banner(PROVISIONAL),
    hero('Case study · Trend and fatigue tracker', 'Trend <em>fatigue</em>',
         'Written for a menu development team or a food editor. The question: what are guests tired of, and is the fatigue about the food or about the hype?',
         [(f'{bin_l[0][1]}', f'want {bin_l[0][0].lower()} gone'), (f'{bin_l[1][1]}', f'want {bin_l[1][0].lower()} gone'),
          (f'{f1(pot["move"])} pts', 'potato sides on dream menus'), (f'+{f1(veg["move"])} pts', 'vegetable and salad sides')]),
    subnav('trend-fatigue'),
    sec('brief', 'The brief', '<div class="prose"><p>Every Dream Menu interview asks: do you have a food trend you wish would quietly disappear? The answers are unprompted. Set against what guests actually choose for their dream menu, they show which trends are tiring and what is replacing them.</p></div>'),
    sec('findings', 'What we found', cards([
        ('The fatigue is with the hype',
         f'The top answers are {bin_l[0][0].lower()} ({bin_l[0][1]}), {bin_l[1][0].lower()} ({bin_l[1][1]}), filming food ({dict(bin_l).get("Filming food and mukbang", 0)}) and viral TikTok food ({dict(bin_l).get("Viral TikTok food", 0)}). Guests are tired of food made to be posted, more than of any one ingredient.'),
        ('Loaded food is tiring on the plate too',
         f'Loaded and dirty food draws {dict(bin_l).get("Loaded and dirty food", 0)} "bin it" mentions, and loaded fries fell from {f1(lf["early"])}% to {f1(lf["late"])}% of dream sides, a clear move. Burgers and fried sides fell from {f1(bfr["early"])}% to {f1(bfr["late"])}%.'),
        ('The side order is changing',
         f'Potato and fries sides fell from {f1(pot["early"])}% to {f1(pot["late"])}% of dream sides. Vegetables and salad rose from {f1(veg["early"])}% to {f1(veg["late"])}%, and Mediterranean and Middle Eastern sides from {f1(med["early"])}% to {f1(med["late"])}%. All clear moves.'),
        ('Comfort food is not going anywhere',
         f'Guilty pleasures are as loved as ever: {guilty[0][0].lower()} ({guilty[0][1]}), {guilty[1][0].lower()} ({guilty[1][1]}) and {guilty[2][0].lower()} ({guilty[2][1]}). Guests want honest comfort, not comfort dressed up for the camera.'),
    ])),
    sec('bin', 'What guests want gone', grid(
        card('"Bin it": trends guests want to disappear, mentions', bars([(n, v) for n, v in bin_l[:10]])),
        card('Guilty pleasures, mentions', bars([(n, v) for n, v in guilty[:8]]))) + fresh('interviews')),
    sec('sides', 'What replaces it', card('Change in share of dream sides, early against recent (points)', diverge(side_moves))
        + source('Early: July to December 2025. Recent: April 2026 onward. Clear moves include potatoes and fries, skinny fries, loaded fries and mac and cheese (down) and vegetables and salad, Mediterranean sides and greens (up).') + fresh('interviews')),
    sec('means', 'What it means for a menu', table(['Finding', 'Action'], [
        ['Guests are tired of food made for the camera', 'Drop the viral special; put the effort into a dish people come back for'],
        ['Loaded food is fading on dream menus', 'Keep one loaded item at most, and make it good enough to justify itself'],
        ['Vegetable and Mediterranean sides are rising', 'Make greens, salads and a mezze-style side as considered as the chips'],
        ['Comfort food is safe', 'A well-made classic (pizza, pasta, fried chicken) does not need a twist'],
        [f'Small plates appear in the "bin it" list ({dict(bin_l).get("Small plates", 0)})', 'If the format is small plates, explain portions and pricing clearly'],
    ])),
    full_commission(['A quarterly fatigue tracker, so you see a trend tiring before it shows in sales', 'Chef and food writer interviews on what they expect to tire next']),
    method(f'Built from unprompted answers to the "bin it" question and {f0(d_t["n"])} codable side answers in {f0(N_ALL)} Dream Menu interviews to {LAST_H}. "Bin it" answers are grouped into published labels; one answer can name more than one trend.'),
])
written.append(write('/case-studies/trend-fatigue', 'Trend fatigue: what guests want gone',
                     'A provisional Dream Menu case study: the trends guests want gone, the sides they are leaving behind and what replaces them.', tf_body))

print('wrote', ', '.join(written))
