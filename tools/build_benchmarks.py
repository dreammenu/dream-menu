#!/usr/bin/env python3
"""How Dream Menu compares: published outside sources set against Dream Menu's own figures.

Run from the repository root after build_trends.py:  python3 tools/build_benchmarks.py

Outside figures are kept in this file (BENCH) with their source, date, link and what they measure; Dream Menu
figures are read live from the site's data files, so every comparison stays current after a refresh.
Nothing from outside sources is ever merged into Dream Menu's own counts or charts.

Writes:
  bench-public.js          window.DM_BENCHP  comparisons that use only figures already public on the site
  partner/bench-data.js    window.DM_BENCHX  every comparison, including dish and drink movement (sign-in)

Verdicts: 'agrees' (same direction or a similar level), 'differs' (opposite direction or a clearly different level),
'context' (a different measure that frames the Dream Menu figure rather than testing it).
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
I = load('partner/intel-data.js', 'DM_INTEL')
TP = load('trend-public.js', 'DM_TRENDP')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
N_ALL = P['n_all']


def item(course, label):
    t = P['trends'][course]
    for it in t['groups'] + t['cats']:
        if (it.get('l') or it['c']) == label:
            return it
    raise KeyError(label)


def deb(key, *answers):
    d = SC['debates'][key]
    c = sum(d['c'].get(a, 0) for a in answers)
    return round(100 * c / d['n'], 1), d['n']


def binned(label):
    for lab, n in P['extra']['bin']:
        if lab == label:
            return n
    return 0


def mv(course, label):
    it = item(course, label)
    return dict(early=it['early'], late=it['late'], move=it['move'], p=it['p'], sig=it['sig'], pct=it['pct'])


def staple(label):
    for s in TP['staples']:
        if s['l'] == label:
            return s
    return None


def fmt_move(m):
    return f"{m['early']}% earlier, {m['late']}% recent ({'+' if m['move'] > 0 else '−'}{abs(m['move']):.1f} pts{', a clear move' if m['sig'] else ', within noise'})"


B = []


def add(**kw):
    B.append(kw)


# ---------------------------------------------------------------- debates (public)
pine, pine_n = deb('pineapple', 'Yes')
add(id='pineapple', topic='Pineapple on pizza', theme='Debates', tier='public', verdict='agrees', kind='level',
    dm=dict(v=pine, unit='%', text=f'{pine}% say yes', base=f'{pine_n:,} guests'),
    ext=dict(v=53, unit='%', text='53% of Britons like pineapple on pizza', who='YouGov, GB adults', date='2017',
             url='https://yougov.co.uk/news/2017/03/06/does-pineapple-belong-pizza'),
    read='Foodies split almost exactly like the general public. Pineapple is a genuine 50:50 call, so it belongs on a pizza menu as an option, not a statement.')
cof, tea_n = deb('tea', 'Coffee')
tea, _ = deb('tea', 'Tea')
add(id='tea', topic='Tea or coffee', theme='Debates', tier='public', verdict='differs', kind='level',
    dm=dict(v=cof, unit='%', text=f'{cof}% pick coffee ({tea}% tea)', base=f'{tea_n:,} guests'),
    ext=dict(v=35, unit='%', text='Just over a third of Britons prefer coffee; 52% prefer tea', who='YouGov, GB adults', date='2012',
             url='https://yougov.co.uk/news/2012/03/27/tea-vs-coffee'),
    read='Dream Menu guests are far more coffee-led than Britain as a whole. That reflects who answers (younger, urban, many in the trade), so read coffee demand here as the leading edge, not the national average. YouGov Profiles data from 2025 shows daily coffee and tea drinking now close to level across age groups.')
irn, coke_n = deb('coke', 'Irn Bru')
coke, _ = deb('coke', 'Coca Cola')
add(id='irnbru', topic='Irn-Bru or Coke', theme='Debates', tier='public', verdict='differs', kind='level',
    dm=dict(v=irn, unit='%', text=f'{irn}% pick Irn-Bru ({coke}% Coke)', base=f'{coke_n:,} guests'),
    ext=dict(v=21, unit='%', text='Irn-Bru was 21% of 330ml cans sold with Scottish takeaways, against 36% for Coke', who='Scoffable takeaway orders, Scotland', date='2022',
             url='https://www.scoffable.com/article/irnbru-vs-coke-ten-years-of-takeaway-data'),
    extra='AG Barr says Irn-Bru accounts for one in every two flavoured fizzy drink cans in Scotland and grew ahead of the soft-drinks market (Circana, 12 weeks to 18 July 2026).',
    read='Irn-Bru wins the loyalty question; Coke wins the order that comes with a takeaway meal. Both are true: one is identity, the other is habit. A range in Scotland needs both, with Irn-Bru as the local signal.')
tap, w_n = deb('water', 'Tap', 'Scottish tap water')
add(id='water', topic='Tap water with dinner', theme='Debates', tier='public', verdict='agrees', kind='level',
    dm=dict(v=tap, unit='%', text=f'{tap}% ask for tap water', base=f'{w_n:,} guests'),
    ext=dict(v=33, unit='%', text='About a third of people drink tap water when eating out in restaurants', who='Local Government Association survey, 3,000 people', date='2016',
             url='https://www.yorkshirepost.co.uk/health/tap-water-should-be-offered-families-eating-out-1799806'),
    read='Roughly one diner in three takes tap water in both sources. The rest split between still and sparkling, so a bottled water offer still matters to two tables in three.')

# ---------------------------------------------------------------- trends guests want gone vs market growth (public)
mat = binned('Matcha')
add(id='matcha', topic='Matcha', theme='Trends', tier='public', verdict='differs', kind='direction',
    dm=dict(dir='down', text=f'The trend guests most want binned: {mat} guests ({100 * mat / N_ALL:.0f}% of all interviews)', base=f'{N_ALL:,} interviews'),
    ext=dict(dir='up', text='Consumers choosing matcha lattes 33.5% more than a year earlier; matcha dishes on UK menus doubled', who='Tastewise, UK consumer and menu data', date='June 2026',
             url='https://tastewise.io/blog/uk-menu-trends'),
    extra='A matcha iced latte was one of the UK’s top trending Deliveroo orders of 2025.',
    read='Growth and backlash at once: the classic sign of a polarising trend near its peak. Serve it well for the fans who want it, but don’t build a menu identity around it.')
dub = binned('Dubai chocolate')
add(id='pistachio', topic='Dubai chocolate and pistachio', theme='Trends', tier='public', verdict='differs', kind='direction',
    dm=dict(dir='down', text=f'Second most-named trend to bin: {dub} guests ({100 * dub / N_ALL:.0f}% of interviews)', base=f'{N_ALL:,} interviews'),
    ext=dict(dir='up', text='Pistachio reaching consumers 44% faster than a year earlier; pistachio with chocolate up 28%', who='Tastewise, UK consumer data', date='June 2026',
             url='https://tastewise.io/blog/uk-menu-trends'),
    read='The same pattern as matcha. Pistachio as a flavour still has room; the viral Dubai bar format is what foodies are tired of.')
ld = binned('Loaded and dirty food')
add(id='loaded', topic='Loaded and dirty food', theme='Trends', tier='public', verdict='differs', kind='direction',
    dm=dict(dir='down', text=f'{ld} guests name loaded and dirty food as a trend to bin', base=f'{N_ALL:,} interviews'),
    ext=dict(dir='up', text='Loaded fries and shareable potato platters recommended as plant-forward wins for pubs and bars', who='UKHospitality trend report', date='2026',
             url='https://www.ukhospitality.org.uk/?p=10357'),
    read='A gap between what the trade is advised to add and what foodies say they are tired of. Worth testing before adding loaded formats to a menu.')
tir = staple('Tiramisu')
if tir:
    add(id='tiramisu', topic='Tiramisu', theme='Dishes', tier='public', verdict='agrees', kind='direction',
        dm=dict(dir='flat', text=f"Steady staple: {tir['pct']}% of dessert answers, between {tir['lo']}% and {tir['hi']}% in every full quarter", base='dessert answers'),
        ext=dict(dir='up', text='Tiramisu up nearly 15% in consumer demand', who='Tastewise, UK consumer data', date='June 2026',
                 url='https://tastewise.io/blog/uk-menu-trends'),
        read='The biggest single dessert on the Dream Menu, and still growing in the wider market. As safe as dessert gets.')

# ---------------------------------------------------------------- market context (public)
add(id='ooh', topic='How often Scotland eats out', theme='Market', tier='public', verdict='context', kind='context',
    dm=dict(text='Dream Menu asks what people would choose, not how often they buy', base=f'{N_ALL:,} interviews'),
    ext=dict(text='Out-of-home transactions in Scotland fell 7% in 2025, to 809 million; delivery transactions fell 30%', who='Food Standards Scotland, Worldpanel by Numerator', date='2026',
             url='https://www.foodstandards.gov.scot/science-and-evidence/monitoring-out-of-home-food-and-drink-purchases-in-scotland-and-great-britain-2024-2025'),
    read='Fewer trips make each visit count for more. Dream Menu shows what people want from the visits they still make: the dishes worth leaving the house for.')
add(id='sites', topic='Venues trading', theme='Market', tier='public', verdict='context', kind='context',
    dm=dict(text=f"Guests have named {load('dm-data.js', 'DM')['meta'].get('venues', 0) or len(load('dm-data.js', 'DM')['venues']):,} venues", base='venue mentions'),
    ext=dict(text='Britain had 98,319 licensed venues in September 2026, 977 fewer than a year earlier (−1.0%)', who='NIQ Hospitality Market Monitor (CGA data)', date='October 2026',
             url='https://www.vinetur.com/en/20261030110108/britain-lost-977-licensed-hospitality-venues-in-the-year-to-september.html'),
    read='A shrinking market concentrates demand. The venues guests name repeatedly are the ones with a reason to visit that survives a squeeze.')

# ---------------------------------------------------------------- partner: dish and drink movement against the market
sun = mv('m', 'Sunday roast')
add(id='roast', topic='Sunday roast', theme='Dishes', tier='partner', verdict='differs', kind='direction',
    dm=dict(dir='down' if sun['sig'] and sun['move'] < 0 else 'flat', text='Share of main answers: ' + fmt_move(sun), base='main answers'),
    ext=dict(dir='up', text='Consumer demand for Sunday roast up 11.6% in a year', who='Tastewise, UK consumer data', date='June 2026',
             url='https://tastewise.io/blog/uk-menu-trends'),
    read='People still eat roasts, but fewer name one as their dream main. A habit, not an aspiration: keep it on for Sunday trade, and don’t expect it to drive a new opening.')
veg = mv('d', 'Vegetables and salad')
fry = mv('d', 'Potatoes and fries')
add(id='sides', topic='Sides: fries against greens', theme='Dishes', tier='partner', verdict='differs', kind='direction',
    dm=dict(dir='down', text=f"Potatoes and fries {fry['early']}% → {fry['late']}% of side answers; vegetables and salad {veg['early']}% → {veg['late']}% (both clear moves)", base='side answers'),
    ext=dict(dir='up', text='Operators growing the number and price of sides to lift spend; vegetable dishes present but not leading menu growth', who='Lumina Intelligence Menu Tracker, 80 UK chains', date='2025 to May 2026',
             url='https://www.lumina-intelligence.com/?p=41434'),
    read='Menus are adding sides; guests are switching which sides they want. The opportunity for a supplier is greens, seasonal veg and salads priced as an upsell, not more fries.')
ck = mv('a', 'Cocktails')
add(id='cocktails', topic='Cocktails', theme='Drinks', tier='partner', verdict='agrees', kind='direction',
    dm=dict(dir='down', text='Share of alcoholic drink answers: ' + fmt_move(ck), base='drink answers, original question'),
    ext=dict(dir='down', text='Espresso martini down 15%, Aperol spritz down 14%, mojito down 13% in consumer demand', who='Tastewise, UK consumer data', date='June 2026',
             url='https://tastewise.io/blog/uk-menu-trends'),
    read='Both sources show cocktails cooling. Guests are moving to whisky, lager and beer.')
wh = mv('a', 'Whisky')
add(id='whisky', topic='Whisky', theme='Drinks', tier='partner', verdict='differs', kind='direction',
    dm=dict(dir='up', text='Share of alcoholic drink answers: ' + fmt_move(wh), base='drink answers, original question'),
    ext=dict(dir='down', text='Diageo’s Great Britain spirits sales fell by a mid-single-digit percentage in early 2026', who='Diageo trading update via Morning Advertiser', date='May 2026',
             url='https://www.morningadvertiser.co.uk/Article/2026/05/06/demand-for-guinness-contributes-to-diageo-sales-growth/'),
    extra='Scotland is different: whisky’s on-trade sales value in Scotland grew 18.2% in 2023, giving Scotland 15.4% of UK on-trade whisky sales (CGA by NIQ).',
    read='A Scottish story running against the national spirits market. Whisky is rising on Dream Menu because the panel is mostly Scottish, where whisky has been gaining on-trade share. Treat it as a Scotland range priority, not a UK one.')
gs = mv('a', 'Guinness and stout')
add(id='guinness', topic='Guinness', theme='Drinks', tier='partner', verdict='differs', kind='direction',
    dm=dict(dir='flat', text='Guinness and stout, share of alcoholic drink answers: ' + fmt_move(gs), base='drink answers, original question'),
    ext=dict(dir='up', text='One in nine pints poured in the UK is a Guinness; the UK’s number-one on-trade beer with double-digit growth', who='CGA by NIQ via Marketing Week; Diageo', date='2025 to 2026',
             url='https://www.marketingweek.com/guinness-women-younger-drinkers/'),
    read='The market’s biggest beer story barely registers as a dream drink. Guinness is what people order, not what they dream of; beer as a whole is rising on Dream Menu, led by lager.')
bc = mv('p', 'Baked cheesecake')
add(id='cake', topic='Cheesecake and big cakes', theme='Dishes', tier='partner', verdict='agrees', kind='direction',
    dm=dict(dir='down', text='Baked cheesecake, share of dessert answers: ' + fmt_move(bc), base='dessert answers'),
    ext=dict(dir='down', text='Chocolate cake down 24%, cupcakes down 38%, birthday cake down 41% in consumer demand', who='Tastewise, UK consumer data', date='June 2026',
             url='https://tastewise.io/blog/uk-menu-trends'),
    read='Cake fatigue shows in both. The desserts holding up are tiramisu, sticky toffee pudding and lighter, fruit-led plates.')
o = I['ops']
add(id='confidence', topic='Operator confidence', theme='Market', tier='partner', verdict='context', kind='context',
    dm=dict(text=f"Look Ahead operators rate the next 12 months {o['conf12']:.1f} out of 10", base=f"{o['n']} operators, mostly micro and small"),
    ext=dict(text='51% of hospitality leaders confident about the next 12 months; only 16% of independents', who='NIQ and Zonal Business Confidence Survey, leaders of 16,000+ sites', date='Feb to Mar 2026',
             url='https://www.morningadvertiser.co.uk/Article/2026/04/01/hospitality-confidence-rebounds-but-costs-hit-small-pubs-and-operators'),
    read='Dream Menu’s operators are small independents, the group NIQ finds least confident. Their middling score is in line with that: cautious, not collapsing.')
add(id='prices', topic='Prices', theme='Market', tier='partner', verdict='agrees', kind='context',
    dm=dict(text=f"{o['rising']}% of operators see supplier prices rising", base=f"{o['sup_base']} operators"),
    ext=dict(text='Restaurant and hotel prices up 3.8% in the year to September 2026, against 3.5% for all prices', who='Office for National Statistics, CPI', date='October 2026',
             url='https://www.babypips.com/news/headline-uk-inflation-september-2026-cpi-fuel-prices-boe-rate-hike'),
    read='Costs are still rising faster than prices overall, which is why operators are reaching for supplier renegotiation and menu engineering first.')

ORDER = {'agrees': 0, 'differs': 1, 'context': 2}
meta = dict(last=P['last'], n_all=N_ALL, built=P['built'],
            note='Outside figures are quoted from their publishers and kept apart from Dream Menu data. They measure different things (polls of all adults, delivery orders, menus, sales), so a difference is a finding, not an error.')
pub = [b for b in B if b['tier'] == 'public']
hdr = '/* Generated by tools/build_benchmarks.py on ' + P['built'] + '. '
open('bench-public.js', 'w', encoding='utf-8').write(hdr + 'Public comparisons only. */\nwindow.DM_BENCHP=' + json.dumps(dict(meta=meta, items=pub), ensure_ascii=False, separators=(',', ':')) + ';\n')
open('partner/bench-data.js', 'w', encoding='utf-8').write(hdr + 'Partner only (behind sign-in). */\nwindow.DM_BENCHX=' + json.dumps(dict(meta=meta, items=B), ensure_ascii=False, separators=(',', ':')) + ';\n')
print('benchmarks', len(B), 'public', len(pub), {v: sum(1 for b in B if b['verdict'] == v) for v in ORDER})
