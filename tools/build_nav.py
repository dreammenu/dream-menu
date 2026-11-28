#!/usr/bin/env python3
"""Builds the Dream Menu site navigation from one list.

Run from the repository root:  python3 tools/build_nav.py

It rewrites, on every page:
  - the header (the "I'm a..." audience menu, four content menus, search, mobile menu)
  - the grouped footer links
  - the two tags in <head> that load the menu script
and regenerates nav-data.js (used by search and the Explore page) and the cards on explore.html.

To add a page or section: add one row to ITEMS below and run the script again.
"""
import glob, html, json, os, re

def _load(fn):
    t = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), fn), encoding='utf-8').read()
    return json.JSONDecoder().raw_decode(t[t.index('=') + 1:])[0]
_P, _M = _load('partner-data.js'), _load('dm-data.js')['meta']
N_ALL, N_PINNED, N_COUNTRIES = f"{_P['n_all']:,}", f"{_M['pinned']:,}", _M['countries']
N_VENUES = f"{_M['venues']:,}"   # same figure as the home page and the map ("venues named"), 28 Nov 2026

PUBLIC = ('/case-studies/guests-and-critics',)   # the free sample report
LOCKED = ('/briefing', '/onepager', '/review', '/geocoder', '/partner', '/insights')   # report chapters, toolkit, tested ideas and Insight Series are open text with partner-only charts (tools/build_gate.py)

AUD = [  # key, label, plural heading, blurb, curated picks (item ids, best first)
 ('food', 'Food lover', 'food lovers', 'What people want to eat, where to go, and the debates that never end.', ['f4', 'f6', 'f5', 'f8', 'f9', 'f14']),
 ('venue', 'Running a venue', 'people running a venue', 'Tools, benchmarks and tested ideas to lift every cover.', ['o3', 'o8', 'r9', 'r14', 'o6', 'o12']),
 ('new', 'Opening a venue', 'people opening a venue', 'Gaps in the market, neighbourhoods and the numbers to model before you sign.', ['r16', 'r8', 'r3', 'o3', 'r10', 'o12']),
 ('chef', 'Chef or kitchen lead', 'chefs and kitchen leads', 'What guests order, what is moving and what they are tired of.', ['r14', 'o4', 'r13', 'f5', 'f14', 'r10']),
 ('supplier', 'Supplier or brand', 'suppliers and brands', 'Demand signals, quarterly briefings and data to plan your range.', ['f16', 'b3', 'r13', 'r2', 'f22']),
 ('investor', 'Investor or developer', 'investors and developers', 'Where the evidence points for capital, concepts and sites.', ['r18', 'r16', 'f16', 'r2', 'r8', 'f6']),
 ('press', 'Press or researcher', 'press and researchers', 'The findings, the method and the numbers worth quoting.', ['a3', 'r2', 'f16', 'f4', 'f8', 'b17']),
]
INTERESTS = [  # key, label, one line, item ids best first. Drives the "I'm interested in" filter on the home page and /analysis (interest.js)
 ('food', 'Food', 'What guests want on every course, and how it is moving', ['f24', 'f19', 'f21', 'o30', 'b13', 'b12', 'b18', 'f13']),
 ('drinks', 'Drinks', 'Cocktails, alcohol-free, soft drinks and the debates', ['f25', 'b14', 'f11', 'f4', 'f28', 'f19']),
 ('sales', 'Growing sales', 'What brings guests in and gets venues recommended', ['f26', 'o8', 'o4', 'r9', 'o7', 'f28', 'r16', 'o13']),
 ('costs', 'Cutting costs', 'Margins, prices, waste and what operators are feeling', ['o3', 'f29', 'o6', 'o5', 'b10', 'b20', 'o12', 'o8']),
 ('menu', 'Planning a menu or range', 'What to add, protect and drop', ['f24', 'o30', 'f27', 'f21', 'r14', 'o4', 'b24', 'f19']),
 ('places', 'Places and locations', 'Where guests go, by city and neighbourhood, and where to open', ['f6', 'f30', 'f17', 'f7', 'b16', 'r8', 'b11', 'f18']),
 ('about', 'About and working with us', 'Who we are, partnerships, commissioned reports, press and how the data is made', ['a0', 'b1', 'b2', 'r0', 'a3', 'a1', 'f15', 'o12']),
]
# Every page and section carries at least one interest, so the filter reaches the whole site.
# build_nav.py stops with an error if an item has no interest, or if a page on disk is missing from ITEMS.
ITAGS = {
 'f1': 'food drinks', 'f16': 'food drinks sales costs menu places', 'f17': 'places food', 'f18': 'places', 'f21': 'food drinks menu',
 'f22': 'food drinks', 'f24': 'food menu sales', 'f25': 'drinks', 'f26': 'sales costs menu', 'f27': 'menu food costs',
 'f28': 'sales menu drinks food', 'f29': 'costs sales', 'f2': 'food menu', 'f4': 'drinks food', 'f5': 'food menu',
 'f6': 'places', 'f20': 'food drinks', 'f19': 'food drinks menu', 'f30': 'places', 'f7': 'places sales',
 'f9': 'drinks food', 'f10': 'places food', 'f11': 'drinks', 'f12': 'food', 'f31': 'food drinks', 'f13': 'food menu',
 'f14': 'food menu costs', 'f32': 'food drinks sales costs menu places', 'f15': 'about', 'r0': 'about',
 'r1': 'sales places costs', 'r2': 'sales places', 'r3': 'places sales', 'r4': 'costs', 'r5': 'costs', 'r6': 'costs',
 'r7': 'places', 'r8': 'places', 'r9': 'sales', 'r10': 'sales places', 'r11': 'places', 'r12': 'food menu drinks',
 'r13': 'menu food', 'r14': 'menu food', 'r15': 'sales places', 'r16': 'sales places menu', 'r17': 'sales menu',
 'r18': 'places sales', 'r19': 'menu food drinks',
 'o1': 'costs sales menu', 'o2': 'sales costs', 'o3': 'costs', 'o4': 'menu sales costs', 'o5': 'sales', 'o6': 'costs sales',
 'o7': 'sales', 'o30': 'menu food', 'o8': 'sales costs', 'o9': 'sales', 'o10': 'sales', 'o11': 'sales costs',
 'o13': 'sales', 'o12': 'sales costs menu about',
 'b1': 'about', 'b9': 'about sales', 'b10': 'costs drinks', 'b11': 'places', 'b12': 'food menu', 'b13': 'food menu',
 'b14': 'drinks', 'b15': 'menu food', 'b16': 'places', 'b17': 'places', 'b18': 'food menu', 'b19': 'food places',
 'b20': 'costs', 'b21': 'places sales', 'b22': 'places', 'b23': 'menu costs sales', 'b24': 'menu food drinks',
 'b2': 'about menu sales', 'b6': 'about sales', 'b7': 'sales places about', 'a0': 'about', 'a1': 'about', 'a3': 'about', 'a2': 'about', 'a4': 'about',
}
# Pages that are not destinations (sign-in, errors, internal tools, redirects); everything else on disk must be in ITEMS.
NOT_PAGES = {'/analysis', '/index', '/404', '/login', '/geocoder', '/review', '/insights', '/intelligence', '/partner', '/briefing', '/explore', '/awards', '/', '/offline'}
AUD_SHORT = {'food': 'food lovers', 'venue': 'operators', 'new': 'new venues', 'chef': 'chefs', 'supplier': 'suppliers', 'investor': 'investors', 'press': 'press'}
# extra search words, so people find things by the words they use
KEYWORDS = {
 'f1': 'dishes trends starters mains desserts drinks sides course', 'f4': 'irn-bru coke coffee tea pineapple pizza water', 'f5': 'comfort food matcha dubai chocolate tired',
 'f20': 'quarterly edition newsletter email state of the menu headlines', 'o13': 'badge sticker website embed named venue',
 'f19': 'dish trends tiramisu scallops steak negroni margarita dessert starter page',
 'f16': 'analysis index city glasgow edinburgh critics michelin awards concentration data', 'f23': 'partner intelligence dashboard momentum matrix opportunity score confidence segments forecast projection operator pulse', 'f22': 'benchmark compare yougov poll market data sources challenge',
 'f6': 'map restaurants bars cafes venues near me city country', 'f7': 'best restaurants top venues most named', 'f30': 'city guide glasgow edinburgh london best restaurants where to eat', 'f8': 'michelin stars 50 best bib gourmand guides',
 'f9': 'fringe cocktail sandwich edinburgh festival', 'f11': 'cocktails drinks bar bartender', 'f15': 'interview submit share my menu',
 'r2': 'headline summary key findings opportunities risks', 'r4': 'survey operators costs confidence trading energy labour', 'r8': 'finnieston southside shawlands barras west end rents sites location',
 'r9': 'advocacy recommend word of mouth signature dish', 'r13': 'rising falling demand quarter trends movers', 'r14': 'stop trends fatigue tired avoid', 'r16': 'gaps white space concept new venue idea brunch dessert late night',
 'r17': 'occasions brunch breakfast date celebration work lunch', 'r18': 'investment capital groups invest', 'r19': 'forecast predict next trends',
 'o3': 'revpash gross profit gp margin vat pricing price rise no-shows no shows deposits waste delivery apps regulars session costs labour food cost', 'o4': 'menu engineering stars dogs puzzles workhorses dish profitability',
 'o5': 'behavioural psychology nudges bread decoy wait', 'o6': 'checklist bathroom sunday festive christmas january quiet season price rise supplier solo diners celebration',
 'o7': 'instagram tiktok reviews google tripadvisor reply', 'o8': 'research evidence studies nudges menu psychology pricing no-shows reminder texts loyalty cards buffet plates music cutlery wine glass', 'o10': 'myths choice overload mints wansink',
 'o11': 'test trial experiment a/b sample size', 'o12': 'audit review consultancy diagnostic mystery', 'b3': 'quarterly briefing sales team movers', 
 'a0': 'about us mission why who founder gordon best story contact podcast napkin pitch youtube spotify', 'b1': 'partnership sponsor commission research data', 'b7': 'contact commission sponsor partner', 'a1': 'method methodology data sources interviews geocoding', 'a2': 'gdpr data protection cookies', 'a4': 'app install phone mobile home screen offline iphone android download', 'a3': 'press media journalist quote statistics logo credit',
}
AUD_ICON = {
 'food': '<path d="M7 3v7a2 2 0 0 0 4 0V3M9 3v18M17 3c-2 2-2.5 4-2.5 7H17v11"/>',
 'venue': '<path d="M3 9 4.5 4h15L21 9M3 9v11h18V9M3 9h18"/><path d="M9 20v-6h6v6"/>',
 'new': '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11Z"/><path d="M12 7v6M9 10h6"/>',
 'chef': '<path d="M6 14a4 4 0 1 1 1.5-7.7 4.5 4.5 0 0 1 9 0A4 4 0 1 1 18 14v6H6Z"/><path d="M6 17h12"/>',
 'supplier': '<path d="M2 6h12v10H2zM14 10h4l3 3v3h-7"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
 'investor': '<path d="M3 20h18M5 16l5-5 3 3 6-7"/><path d="M15 7h4v4"/>',
 'press': '<path d="M4 5h13v14H6a2 2 0 0 1-2-2Z"/><path d="M17 9h3v8a2 2 0 0 1-2 2M7 9h7M7 12h7M7 15h4"/>',
}

GROUPS = [  # key, label, landing page, one-line summary. Grouped by reader (24 Nov 2026 audit)
 ('analysis', 'Findings', '/analysis/demand', 'What foodies want and what is changing, the partner briefing and the dated reports'),
 ('venues', 'For venues', '/menu-check', 'Tools and a diagnostic for people running a venue'),
 ('trends', 'For foodies', '/map', 'Where to eat, the dream menu and ways to join in'),
 ('about', 'About', '/about', 'Who we are, how the data works, and how to work with us'),
]
# Header: six items. A group with one entry is a plain link (no dropdown); Reports has four entries, the rest three.
# For foodies (the home page) is reached from the logo and the footer. About is a plain link to /about (22 Nov 2026).
# SEC: the pages of each section, in order. The footer column and the tab bar at the top of each of these pages
# use exactly this list, with the same names, so the menus, the footer and the pages tell one story (22 Nov 2026).
# One structure, used three times (24 Nov 2026): the header dropdowns, the footer columns and the tab bar on short
# pages all list the same pages, with the same names, in the same order. Five sections.
# Four sections (24 Nov 2026): no separate partner menu. The briefing sits with the findings, working with us and
# the press kit with About; the rep sheet (venues to call) is reached from the briefing.
SEC = {'analysis': ['f24', 'f21', 'f17', 'f19', 'b2', 'r1', 'f20', 'b9'],
       'venues': ['o30', 'o1', 'o8', 'o12', 'o13'],
       'trends': ['f6', 'f30', 'f7', 'f1', 'f31', 'f9', 'f13', 'f15'],
       'about': ['a0', 'a1', 'f22', 'a4', 'a2', 'b1', 'a3']}
# Each section is split into short labelled groups (25 Nov 2026): the dropdown shows them as titled columns, a
# short page's tab bar shows only its own group, and the footer uses the same titles.
SUB = {'analysis': [('The findings', ['f24', 'f21', 'f17', 'f19']), ('Reports and briefings', ['b2', 'r1', 'f20', 'b9'])],
       'venues': [('Tools for your venue', ['o30', 'o1', 'o8']), ('Get a review or a badge', ['o12', 'o13'])],
       'trends': [('Where to eat', ['f6', 'f30', 'f7']), ('Join in', ['f1', 'f31', 'f9', 'f13', 'f15'])],
       'about': [('About Dream Menu', ['a0', 'a1', 'f22', 'a4', 'a2']), ('Work with us', ['b1', 'a3'])]}
assert all(sum((ids for _, ids in SUB[g]), []) == SEC[g] for g in SUB), 'SUB must list SEC in order'
# Header dropdowns = the section lists. The analysis page's own parts are in its "On this page" bar.
HMENU = {g: SEC[g] for g in SEC}
FOOT = [(lab, SEC[g]) for g, lab, *_ in GROUPS if g in SEC]
NO_SECNAV = {'/', '/map'}   # the home page and the full-screen map carry no tab bar
# Page labels (the small line above each headline) use the same name as the page's tab
EYEBROW = {'/report': 'Reports · Report 2026, edition 6', '/cities': 'City guides',
           '/rankings': 'Rankings', '/my-dream-menu': 'Build your dream menu', '/menu-check': 'Check my menu · Free tool',
           '/operators': 'Operator toolkit', '/badge': 'Venue badge', '/for-business': 'Ways to work with us', '/press': 'Press kit',
           '/privacy': 'Privacy'}
# Where each top-level page sits (children follow their parent). MENU = the pages listed in the footer;
# everything else is one click away on /explore and in search.
PLACE = {'f1': 'trends', 'f19': 'analysis', 'f9': 'trends', 'f31': 'trends', 'f13': 'trends',
         'f6': 'trends', 'f30': 'trends', 'f7': 'trends',
         'f16': 'analysis', 'r0': 'analysis', 'f20': 'analysis', 'r1': 'analysis', 'r4': 'analysis', 'r7': 'analysis', 'r12': 'analysis', 'r15': 'analysis', 'b9': 'analysis',
         'o1': 'venues', 'o30': 'venues', 'o8': 'venues', 'o13': 'venues', 'o12': 'venues',
         'b1': 'about', 'b2': 'analysis',
         'a0': 'about', 'a1': 'about', 'a3': 'about', 'a2': 'about', 'a4': 'about', 'f15': 'trends'}
MENU = [i for g in SEC.values() for i in g]
RETITLE = {'f22': 'Can we trust it?', 'b7': 'Venues to call', 'f24': 'What guests want', 'f21': 'What is changing', 'f17': 'Where it differs',
           'o13': 'Venue badge', 'r0': 'All reports', 'f1': 'The dream menu', 'r1': 'Report 2026', 'b2': 'Partner briefing', 'b1': 'Ways to work with us', 'f16': 'The analysis', 'b9': 'Insight Series'}

# id, title, url, description, group, audiences, star (featured), parent id
ITEMS = [
 ('f1', 'Food trends', '/', f'What {N_ALL} guests dream of eating, course by course and city by city', 'food', 'food chef supplier press', 1, None),
 ('f16', 'The findings', '/analysis/demand', 'What guests want, what is changing, how cities differ, how it compares, and what to do', 'food', 'food investor press supplier', 1, None),
 ('f32', 'The short version', '/#now', 'What the data says this quarter, in a few lines', 'food', 'food venue new chef supplier investor press', 0, 'f16'),
 ('f17', "Every city's appetite", '/analysis/cities', 'Which dishes take a bigger share in each market than everywhere else', 'food', 'investor new supplier', 0, 'f16'),
 ('f18', 'Guests and critics', '/analysis/cities#critics', 'How far guest favourites and guide award winners overlap', 'food', 'food press', 0, 'f16'),
 ('f21', 'What changed', '/analysis/change', 'How much each course moved, against chance, and the steady staples', 'food', 'food chef supplier press', 0, 'f16'),
 ('f22', 'How we compare', '/analysis/trust', 'Dream Menu against national polls, eating-out data, menu trackers and sales', 'food', 'food press investor supplier', 1, 'f16'),
 ('f24', 'What guests want', '/analysis/demand', 'Each course ranked by food group with seafood dish by dish, the dish life cycle, the staples, and demand against what menus list', 'food', 'food chef supplier venue', 0, 'f16'),
 ('f25', 'Drinks baseline', '/analysis/change#drinks', 'Soft and alcoholic drinks since August 2026, including the alcohol-free share', 'food', 'venue supplier', 0, 'f16'),
 ('f26', 'What should I do?', '/operators#evidence', 'The evidence read for venues, investors, suppliers and press', 'food', 'venue new supplier investor press', 0, 'f16'),
 ('f27', 'Category scorecard', '/analysis/partner#category-sec', 'Partners: a grow, defend, trim, core or niche call for every food group', 'food', 'supplier', 0, 'f16'),
 ('f28', 'Dish and drink scores', '/analysis/partner#opportunity-sec', 'Partners: back, watch or review, with a score out of 10 for every dish and drink', 'food', 'supplier', 0, 'f16'),
 ('f29', 'Operator pulse', '/analysis/partner#segments-sec', 'Partners: what operators say about costs, prices and confidence', 'food', 'supplier investor', 0, 'f16'),
 ('f2', 'The dishes people choose', '/#courses', 'The top dishes for every course and their share of guests', 'food', 'food chef supplier', 0, 'f1'),
 ('f4', 'The great debates', '/#debates', 'Irn-Bru or Coke, coffee or tea, pineapple on pizza, tap or sparkling', 'food', 'food press', 1, 'f1'),
 ('f5', 'Guilty pleasures and Bin it', '/#mood', 'The comfort food guests admit to, and the trends they want gone', 'food', 'food chef venue', 1, 'f1'),
 ('f6', 'Venue map', '/map', f'{N_VENUES} venues guests have named in {N_COUNTRIES} countries, plus Dream Menu’s own list and award winners', 'food', 'food investor new supplier', 1, None),
 ('f20', 'State of the Menu', '/quarterly', 'The quarter in food, with an email edition', 'food', 'food press supplier chef', 1, None),
 ('f19', 'Dish trends', '/trends', 'A page for every dish and drink we track', 'food', 'food chef supplier press', 1, None),
 ('f30', 'City guides', '/cities', 'Where foodies eat in each city: most named, hidden gems, award holders', 'food', 'food venue press new', 0, None),
 ('f7', 'Rankings', '/rankings', 'The venues guests name most, by market, course, dish and drink', 'food', 'food venue press', 0, None),
 ('f9', 'Specials', '/specials', 'Themed editions: Dream Fringe, Dream Cocktail and Dream Sandwich', 'food', 'food chef', 0, None),
 ('f10', 'Dream Fringe', '/specials#fringe', 'Late-night food after the shows and the best Fringe venues', 'food', 'food', 0, 'f9'),
 ('f11', 'Dream Cocktail', '/specials#cocktail', 'The drinks guests and bartenders would order', 'food', 'food chef', 0, 'f9'),
 ('f12', 'Dream Sandwich', '/specials#sandwich', 'The sandwiches Scotland dreams of', 'food', 'food', 0, 'f9'),
 ('f31', 'Build your dream menu', '/my-dream-menu', 'Pick six courses, see who agrees and which city you eat like', 'food', 'food', 0, None),
 ('f13', 'From the kitchen', '/from-the-kitchen', 'Cafés, restaurants and bars describe their menus in three words', 'food', 'food chef', 0, None),
 ('f14', 'Advice for anyone who cooks', '/from-the-kitchen#advice', 'Tips from the people who cook for a living', 'food', 'food chef', 0, 'f13'),
 ('f15', 'Take part', '/take-part', 'Share your own dream menu: five courses and the venue that does it best', 'food', 'food', 0, None),

 ('r0', 'All reports', '/report#library', 'Every dated publication in one place: the 2026 report, fifteen Insight Series reports and State of the Menu', 'report', 'venue new investor supplier press chef', 1, 'r1'),
 ('r1', 'Report overview', '/report', 'Report 2026 and every other publication: findings, operators, Glasgow, opportunities', 'report', 'venue new investor supplier press chef', 0, None),
 ('r2', 'Seven key findings', '/report#findings', 'The headline findings, with the top five opportunities and risks', 'report', 'investor press supplier venue', 1, 'r1'),
 ('r3', 'Five questions before you invest', '/report#questions', 'A quick test for any concept, site or menu', 'report', 'new investor', 0, 'r1'),
 ('r4', 'Operator pulse', '/report/operator-pulse', 'What 54 operators said about trading, costs and confidence', 'report', 'venue supplier investor press', 0, None),
 ('r5', 'Early-warning signals', '/report/operator-pulse#warning', 'The signs operators watch before trading turns', 'report', 'venue investor', 0, 'r4'),
 ('r6', 'What would help most', '/report/operator-pulse#help', 'The support operators say they need', 'report', 'press supplier', 0, 'r4'),
 ('r7', "Glasgow's dining landscape", '/report/glasgow', 'Neighbourhoods, food corridors, case studies and the Michelin picture', 'report', 'new investor venue press', 0, None),
 ('r8', 'Neighbourhoods and food corridors', '/report/glasgow#neighbourhoods', 'Six corridors from Finnieston to the Barras, and where rents still make sense', 'report', 'new investor', 0, 'r7'),
 ('r9', 'What high-advocacy venues share', '/report/glasgow#characteristics', 'Seven traits of the venues guests recommend most', 'report', 'venue new chef', 1, 'r7'),
 ('r10', 'Five case studies', '/report/glasgow#case-studies', "Crabshakk, Margo, Gloriosa, Sebb's and Trust by Modou", 'report', 'venue new chef', 0, 'r7'),
 ('r11', 'The Michelin landscape', '/report/glasgow#michelin', 'Where Glasgow sits in the guides', 'report', 'press food', 0, 'r7'),
 ('r12', "What's on the menu", '/report/whats-on-the-menu', 'What Scotland dreams of eating, course by course, and what is moving', 'report', 'chef supplier venue', 0, None),
 ('r13', 'Demand tracker', '/report/whats-on-the-menu#tracker', 'Dishes rising and falling across five quarters', 'report', 'supplier chef', 1, 'r12'),
 ('r14', 'Trend fatigue', '/report/whats-on-the-menu#fatigue', 'What to stop doing: the trends guests are tired of', 'report', 'chef venue', 1, 'r12'),
 ('r15', 'Opportunities', '/report/opportunities', 'Concept gaps, dining occasions, investable theses and forecasts', 'report', 'new investor', 0, None),
 ('r16', 'Concept gaps', '/report/opportunities#gaps', "What Glasgow wants and can't easily find", 'report', 'new investor', 1, 'r15'),
 ('r17', 'The seven dining occasions', '/report/opportunities#occasions', 'From brunch to late-night dessert: what each occasion needs', 'report', 'venue new', 0, 'r15'),
 ('r18', 'Five investable theses', '/report/opportunities#theses', 'Where the evidence points for capital', 'report', 'investor', 1, 'r15'),
 ('r19', 'Trend forecasts', '/report/opportunities#forecasts', 'What is likely to move next', 'report', 'supplier chef investor', 0, 'r15'),

 ('o1', 'Operator toolkit', '/operators', 'Actions, calculators, a menu matrix and checklists', 'ops', 'venue new chef', 0, None),
 ('o2', 'The top 20 actions', '/operators#actions', 'What to do first, from identity to strategy', 'ops', 'venue new', 0, 'o1'),
 ('o3', 'Calculators', '/operators#numbers', 'RevPASH, dish pricing, price rises, no-shows, waste, delivery and more', 'ops', 'venue new', 1, 'o1'),
 ('o4', 'Menu matrix', '/operators#matrix', 'Paste your dishes and see which earn their place', 'ops', 'chef venue', 1, 'o1'),
 ('o5', 'Odd ideas that work', '/operators#odd', 'Ten behavioural ideas, each with a test to run this week', 'ops', 'venue chef', 0, 'o1'),
 ('o6', 'Checklists', '/operators#checklists', 'Thirteen tickable lists, from the first 90 seconds to the festive season', 'ops', 'venue', 0, 'o1'),
 ('o7', 'Social media and reviews', '/operators#digital', 'The three-post week and how to reply to every kind of review', 'ops', 'venue', 0, 'o1'),
 ('o30', 'Check my menu', '/menu-check', 'Tick your dishes and see how much of what guests want you cover', 'ops', 'venue chef new', 0, None),
 ('o8', 'Tested ideas', '/tested-ideas', '20 ideas scored against the research, with a trial for each', 'ops', 'venue chef supplier press', 1, None),
 ('o9', 'The evidence map', '/tested-ideas#matrix', 'Every idea placed by impact and strength of evidence', 'ops', 'venue press', 0, 'o8'),
 ('o10', 'Myths busted', '/tested-ideas#myths', "Five things operators are told that don't stand up", 'ops', 'venue press', 0, 'o8'),
 ('o11', 'Trial planner', '/tested-ideas#trial', 'How long a test needs, and why pooling venues helps', 'ops', 'venue supplier', 0, 'o8'),
 ('o13', 'Named on Dream Menu badge', '/badge', 'A free badge for venues guests have named, linking to the venue page', 'ops', 'venue', 0, None),
 ('o12', 'Restaurant MOT', '/restaurant-mot', 'An independent four-week diagnostic of one venue', 'ops', 'venue new', 0, None),

 ('b1', 'For business', '/for-business', 'Partnerships, commissioned reports, the Restaurant MOT and data licences', 'biz', 'supplier investor venue', 0, None),
 ('b9', 'Insight Series', '/case-studies', 'Fifteen deep-dive reports, free to read; partners see the charts', 'biz', 'supplier investor venue new press chef', 1, None),
 ('b10', 'The cost of a night out', '/case-studies/night-out', 'Food, drink and transport on a Glasgow night out, and what it means for a supplier', 'biz', 'supplier venue press food', 0, 'b9'),
 ('b11', 'Two cities, two appetites', '/case-studies/glasgow-edinburgh', 'How Glasgow and Edinburgh guests differ, for a group opening a second site', 'biz', 'new investor venue', 0, 'b9'),
 ('b12', "Scotland's seafood appetite", '/case-studies/seafood', 'Where seafood sits on the dream menu and what is rising', 'biz', 'supplier chef', 0, 'b9'),
 ('b13', 'The last spend: dessert', '/case-studies/dessert', 'Which desserts guests still choose and what a range should look like', 'biz', 'supplier chef venue', 0, 'b9'),
 ('b14', 'What Scotland drinks with dinner', '/case-studies/drinks', 'Cocktails losing share to whisky and lager, and the soft-drink round', 'biz', 'supplier venue', 0, 'b9'),
 ('b15', 'Trend fatigue', '/case-studies/trend-fatigue', 'The trends guests want gone and what replaces them', 'biz', 'chef venue press', 0, 'b9'),
 ('b16', 'Where Glasgow eats', '/case-studies/neighbourhoods', 'Which districts punch above their weight, and where the next Finnieston is', 'biz', 'investor new venue', 0, 'b9'),
 ('b17', 'Guests and critics', '/case-studies/guests-and-critics', 'Free sample report: how far guest favourites and guide award winners overlap', 'biz', 'press investor food', 0, 'b9'),
 ('b18', 'The steak economy', '/case-studies/steak', 'The cuts guests name and the shift from fillet to flavour', 'biz', 'supplier chef venue', 0, 'b9'),
 ('b19', "Glasgow's Italian table", '/case-studies/italian', 'Italian on every course and how the specialists win', 'biz', 'venue supplier new', 0, 'b9'),
 ('b20', 'The confidence gap', '/case-studies/operator-confidence', 'Scottish operators back themselves but not the sector', 'biz', 'investor press supplier', 0, 'b9'),
 ('b21', 'Glasgow to 2030', '/case-studies/glasgow-2030', 'City forecast: what Glasgow orders next, rising districts, three scenarios', 'biz', 'venue supplier investor press new', 0, 'b9'),
 ('b22', 'Edinburgh and Scotland to 2030', '/case-studies/edinburgh-2030', 'The capital\'s appetite, Leith, the levy test and the coast', 'biz', 'investor press supplier new', 0, 'b9'),
 ('b23', 'Ten forces to 2031', '/case-studies/ten-forces', 'Weight-loss drugs, less drinking, levies and the turn to fish and vegetables', 'biz', 'venue supplier investor press new', 0, 'b9'),
 ('b24', 'The edge of the menu', '/case-studies/edge-of-the-menu', '26 niche items on an adoption curve, with timing and confidence', 'biz', 'venue supplier press new', 0, 'b9'),
 ('b2', 'Partner briefing', '/analysis/partner', 'Clear movers, buying calls, dish scores and partnership dates, read on the site. Charts unlock at sign-in', 'biz', 'supplier', 0, None),
 ('b6', 'Partner one-pager', '/onepager', 'One page to share with your team', 'biz', 'supplier', 0, 'b2'),
 ('b7', 'Rep sheet: venues to call', '/partner/accounts', 'Scottish venues guests name for rising dishes, by range, with the dish to lead with', 'biz', 'supplier', 0, 'b2'),

 ('a0', 'About Dream Menu', '/about', 'Why we do it, what we do and who is behind it, including the Napkin Pitch podcast', 'about', 'food venue new chef supplier investor press', 1, None),
 ('a1', 'How it works', '/how-it-works', 'Where the data comes from, how venues are placed and which guides count', 'about', 'press', 0, None),
 ('a3', 'Press kit', '/press', 'Figures to quote, how to credit them and logos', 'about', 'press', 0, None),
 ('a4', 'Get the app', '/app', 'Dream Menu on your phone: add it to your home screen, free, no app store', 'about', 'food venue chef supplier investor press', 0, None),
 ('a2', 'Privacy', '/privacy', 'How interview answers and site visits are used', 'about', 'press', 0, None),
]

IT = {}
_parent = {row[0]: row[7] for row in ITEMS}
for row in ITEMS:
    i, t, u, d, g, a, s, p = row
    g = PLACE[p or i] if (p or i) in PLACE else PLACE[_parent[p]]
    t = RETITLE.get(i, t)
    IT[i] = dict(id=i, t=t, u=u, d=d, g=g, a=a.split(), s=bool(s), p=p, n=ITAGS.get(i, '').split(), lock=(u.startswith(LOCKED) and u not in PUBLIC) or i in ('f23', 'b2', 'f27', 'f28', 'f29'), k=KEYWORDS.get(i, ''))

E = lambda x: html.escape(x, quote=True)
LOCK = '<svg class="lock" viewBox="0 0 16 16" width="12" height="12" aria-label="Sign in needed" role="img"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'
CHEV = '<svg class="chev" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
SEARCH = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
ARROW = '<span class="arr" aria-hidden="true">→</span>'

def aicon(k, cls='aico'):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{AUD_ICON[k]}</svg>'

def lk(it):
    return (' ' + LOCK) if it['lock'] else ''

def children(pid):
    return [x for x in IT.values() if x['p'] == pid]

def pages(g):
    return [x for x in IT.values() if x['g'] == g and not x['p']]

def aud_count(k):
    return sum(1 for x in IT.values() if k in x['a'])

def header(cur_group):
    out = ['<header class="top"><div class="wrap">',
           '<a class="mark" href="/"><img src="/logo-128.png" alt="" width="40" height="40">Dream Menu</a>',
           '<nav class="mnav" id="mnav" aria-label="Site"><ul class="mnav-list">']
    for g, lab, land, summ in GROUPS:
        if g not in HMENU:
            continue
        cur = ' aria-current="true"' if g == cur_group else ''
        ids = HMENU[g]
        if len(ids) == 1:
            out.append(f'<li class="mnav-solo" data-g="{g}"><a class="mnav-top" href="{IT[ids[0]]["u"]}"{cur}><span>{E(lab)}</span></a></li>')
            continue
        out.append(f'<li class="mnav-item" data-g="{g}"><a class="mnav-top" href="{land}" aria-expanded="false" aria-controls="mp-{g}"{cur}><span>{E(lab)}</span>{CHEV}</a>')
        out.append(f'<div class="mpanel mp-simple mp-grouped" id="mp-{g}"><div class="mp-inner"><p class="mp-sum">{E(summ)}</p><div class="mp-groups">')
        for sub, sids in SUB.get(g, [(None, ids)]):
            out.append(f'<div class="mp-group">' + (f'<p class="mp-gh">{E(sub)}</p>' if sub else '') + '<div class="mp-links">')
            for it in [IT[i] for i in sids]:
                out.append(f'<div class="mp-page"><a class="mp-p" href="{it["u"]}"><b>{E(it["t"])}{lk(it)}</b><span>{E(it["d"])}</span></a></div>')
            out.append('</div></div>')
        out.append('</div></div></div></li>')
    out.append('</ul><a class="mnav-all" href="/login?next=/analysis/partner">Partner sign-in ' + ARROW + '</a></nav>')   # shown in the phone menu only
    out.append('<button type="button" class="msearch" data-search aria-label="Search the site">' + SEARCH + '<span>Search</span><kbd>/</kbd></button>')
    out.append('<a class="signin" href="/login?next=/analysis/partner">Partner sign-in</a>')
    out.append('<button type="button" class="mburger" aria-expanded="false" aria-controls="mnav"><span class="bars" aria-hidden="true"><i></i><i></i><i></i></span><span class="sr">Menu</span></button>')
    out.append('</div></header>')
    return ''.join(out)

def is_long(s):
    """Same test nav.js uses to build an "On this page" bar: 3+ h2 headings that can be jumped to."""
    m = s[s.find('<main'):s.find('</main>')]
    n = len(re.findall(r'<h2[^>]*\bid="', m))
    for sec in re.finditer(r'<section[^>]*\bid="[^"]+"[^>]*>(.*?)</section>', m, re.S):
        h = re.search(r'<h2([^>]*)>', sec.group(1))
        if h and 'id="' not in h.group(1):
            n += 1
    return n >= 3 or 'class="cs-toc"' in m

def secnav(path, s=''):
    if path in NO_SECNAV or (s and is_long(s)):
        return ''
    for g, lab, land, summ in GROUPS:
        for sub, sids in SUB.get(g, [(lab, SEC.get(g, []))]):
            its = [IT[i] for i in sids]
            if any(it['u'] == path for it in its):   # the tab bar shows only the page's own small group
                links = ''.join(f'<a href="{it["u"]}"' + (' aria-current="page"' if it['u'] == path else '') + f'>{E(it["t"])}{lk(it)}</a>' for it in its)
                return f'<!--secnav--><nav class="subnav secnav" aria-label="{E(sub)} pages"><div class="wrap"><span class="secnav-l">{E(sub)}</span>{links}</div></nav><!--/secnav-->'
    return ''

def footer_links():
    out = ['<nav class="footlinks footcols" aria-label="All pages">']
    for g, lab, land, summ in GROUPS:
        if g not in SEC:
            continue
        out.append(f'<div><b>{E(lab)}</b>')
        for sub, sids in SUB.get(g, [(None, SEC[g])]):
            if sub:
                out.append(f'<i class="fsub">{E(sub)}</i>')
            for it in [IT[i] for i in sids]:
                out.append(f'<a href="{it["u"]}">{E(it["t"])}{lk(it)}</a>')
        out.append('</div>')
    out.append('</nav>')
    return ''.join(out)

def explore_cards():
    out = []
    for g, lab, land, summ in GROUPS:
        out.append(f'<section class="ex-group" id="g-{g}" data-g="{g}"><div class="wrap"><h2>{E(lab)}</h2><p class="lede">{E(summ)}</p><div class="ex-grid">')
        for it in pages(g):
            ch = children(it['id'])
            aud = ' '.join(sorted(set(it['a'] + sum((c['a'] for c in ch), []))))
            out.append(f'<article class="ex-card" data-aud="{aud}" data-self="{" ".join(it["a"])}" data-text="{E((it["t"] + " " + it["d"] + " " + it["k"]).lower())}">')
            out.append(f'<a class="ex-main" href="{it["u"]}"><b>{E(it["t"])}{lk(it)}</b><span>{E(it["d"])}</span></a>')
            if ch:
                out.append('<ul class="ex-sub">' + ''.join(
                    f'<li data-aud="{" ".join(c["a"])}" data-text="{E((c["t"] + " " + c["d"] + " " + c["k"]).lower())}"><a href="{c["u"]}"><b>{E(c["t"])}</b><span>{E(c["d"])}</span></a></li>' for c in ch) + '</ul>')
            out.append('<p class="ex-tags">' + ''.join(f'<span data-a="{k}">{E(l)}</span>' for k, l, *_ in AUD if k in it['a']) + '</p></article>')
        out.append('</div></div></section>')
    return ''.join(out)

def aud_band():
    out = ['<section class="audband" id="start"><div class="wrap"><div class="eyebrow">Start here</div><h2>Where do you want to start?</h2>',
           '<p class="lede">Pick who you are and we&rsquo;ll point you to the best of Dream Menu for you.</p><div class="audgrid">']
    for k, lab, pl, bl, picks in AUD:
        top = IT[picks[0]]
        out.append(f'<a class="audtile" href="/explore?for={k}" data-aud="{k}">{aicon(k)}<b>{E(lab)}</b><span>{E(bl)}</span><em>Start with: {E(top["t"])}</em></a>')
    out.append('</div><p class="audmore"><a href="/explore">Or browse everything on the site ' + ARROW + '</a></p></div></section>')
    return ''.join(out)

def page_group(path):
    if path in ('/', '/index'):
        return None   # the home page belongs to no one section
    for it in IT.values():
        if it['u'] == path:
            return it['g']
    # child pages light up their section in the header too
    if path == '/analysis/trust':
        return 'about'
    for pre, g in (('/analysis/', 'analysis'), ('/partner/', 'analysis'), ('/city/', 'trends'), ('/area/', 'trends'), ('/venue/', 'trends'), ('/trends/', 'analysis'),
                   ('/case-studies/', 'analysis'), ('/report/', 'analysis'), ('/quarterly/', 'analysis')):
        if path.startswith(pre):
            return g
    return {'/explore': 'start'}.get(path)

APP_TAGS = ('<link rel="manifest" href="/manifest.webmanifest"><meta name="mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Dream Menu">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
            '<link rel="stylesheet" href="/app.css"><script src="/app.js" defer></script>')
HEAD_TAGS = '<script>document.documentElement.classList.add("js")</script><script src="/nav-data.js" defer></script><script src="/nav.js" defer></script><script src="/dm-fresh.js" defer></script>'

def check_coverage():
    keys = {k for k, *_ in INTERESTS}
    bad = [i for i, x in IT.items() if not x['n'] or set(x['n']) - keys]
    if bad:
        raise SystemExit(f'items with no interest (or an unknown one) in ITAGS: {bad}')
    urls = {x['u'].split('#')[0] for x in IT.values()}
    pages = {'/' + f[:-5] for f in glob.glob('*.html')} | {'/' + f[:-5] for f in glob.glob('report/*.html') + glob.glob('case-studies/*.html')}
    missing = sorted(pages - urls - NOT_PAGES)
    if missing:
        raise SystemExit(f'pages not reachable from the interest filter (add them to ITEMS and ITAGS): {missing}')


COURSE_WORDS = {'starter': 'Starter', 'main': 'Main', 'side': 'Side', 'dessert': 'Dessert', 'soft drink': 'Soft drink',
                'alcoholic drink': 'Drink', 'drink': 'Drink'}

def dish_index():
    """Every dish page (trends/<slug>.html) for the site search (24 Nov 2026): name, course and one line."""
    out = []
    for fn in sorted(glob.glob('trends/*.html')):
        h = open(fn, encoding='utf-8').read()
        t = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
        dsc = re.search(r'<meta name="description" content="([^"]*)"', h)
        if not t:
            continue
        name = html.unescape(re.sub(r'<[^>]+>', '', t.group(1))).strip()
        d = html.unescape(dsc.group(1)) if dsc else ''
        m = re.search(r'([\d.]+%) of (starter|main|side|dessert|soft drink|alcoholic drink|drink) answers', d)
        course = COURSE_WORDS.get(m.group(2), '') if m else ''
        line = f'{m.group(1)} of {m.group(2)} answers. Where guests go for it and which markets name it most.' if m else d[:120]
        out.append(dict(t=name, u='/' + fn[:-5], c=course, d=line))
    return out

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    check_coverage()
    data = dict(aud=[dict(k=k, l=l, p=p, sh=AUD_SHORT[k], b=b, picks=picks) for k, l, p, b, picks in AUD],
                groups=[dict(k=g, l=l, u=u, d=d) for g, l, u, d in GROUPS],
                ints=[dict(k=k, l=l, d=d, ids=ids) for k, l, d, ids in INTERESTS],
                items=[dict(id=x['id'], t=x['t'], u=x['u'], d=x['d'], g=x['g'], a=x['a'], s=x['s'], p=x['p'], lock=x['lock'], k=x['k'], n=x['n']) for x in IT.values()])
    data['dishes'] = dish_index()
    with open('nav-data.js', 'w') as f:
        f.write('/* Generated by tools/build_nav.py: edit the list there, not this file. */\nwindow.DM_NAV=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    foot = footer_links()
    changed = 0
    for fn in sorted([f for f in glob.glob('*.html') if open(f, encoding='utf-8').read().find('<header class="top">') >= 0] + glob.glob('report/*.html') + glob.glob('case-studies/*.html') + glob.glob('venue/*.html') + glob.glob('city/*.html') + glob.glob('area/*.html') + glob.glob('trends/*.html') + glob.glob('quarterly/*.html') + glob.glob('analysis/*.html')):
        s = open(fn).read()
        o = s
        path = '/' + fn[:-5]
        path = '/' if path == '/index' else path
        s = re.sub(r'<header class="top">.*?</header>', lambda m: header(page_group(path)), s, count=1, flags=re.S)
        s = re.sub(r'<nav class="footlinks[^"]*" aria-label="All pages">.*?</nav>', lambda m: foot, s, count=1, flags=re.S)
        # section tab bar, first thing in <main>
        s = re.sub(r'<!--secnav-->.*?<!--/secnav-->', '', s, flags=re.S)
        sn = secnav(path, s)
        if sn:
            s = re.sub(r'(<main[^>]*>)', lambda m: m.group(1) + sn, s, count=1)
        # the 2026 report's own chapter bar lists its chapters only; the venue tools live under For venues
        if '<nav class="subnav" aria-label="Report sections">' in s:
            if fn in ('operators.html', 'tested-ideas.html', 'restaurant-mot.html'):
                s = re.sub(r'<nav class="subnav" aria-label="Report sections">.*?</nav>\s*', '', s, count=1, flags=re.S)
            else:
                s = re.sub(r'<a href="/(operators|tested-ideas|restaurant-mot)"[^>]*>.*?</a>', '', s, flags=re.S)
                s = s.replace('<nav class="subnav" aria-label="Report sections">', '<nav class="subnav" aria-label="Report 2026 chapters">')
        if is_long(s):   # one bar per page: a long page keeps only its "On this page" bar
            s = re.sub(r'<nav class="subnav" aria-label="Report 2026 chapters">.*?</nav>\s*', '', s, count=1, flags=re.S)
        s = s.replace('<nav class="subnav" aria-label="Report 2026 chapters"><div class="wrap"><a href="/report"', '<nav class="subnav" aria-label="Report 2026 chapters"><div class="wrap"><span class="secnav-l">Report 2026</span><a href="/report"', 1) if 'secnav-l">Report 2026<' not in s else s
        if path in EYEBROW:
            i = s.find('<main')
            s = s[:i] + re.sub(r'(class="eyebrow">)[^<]*(<)', lambda m: m.group(1) + E(EYEBROW[path]) + m.group(2), s[i:], count=1)
        # footer logo sits beside the words "Dream Menu", so it is decorative (screen readers would read the name twice)
        s = s.replace('<div class="footband"><img src="/logo-128.png" alt="Dream Menu"', '<div class="footband"><img src="/logo-128.png" alt=""')
        # bottom line: no repeats of links already in the columns above (audit, 16 Nov 2026)
        s = s.replace('<a href="/privacy">Privacy</a> · <a href="/login?next=/analysis/partner">Partner sign-in</a> · <a href="/how-it-works">How it works</a> · <a href="https://www.instagram.com/dream.menu/"',
                      '<a href="mailto:contact.dreammenu@gmail.com">contact.dreammenu@gmail.com</a> · <a href="https://www.instagram.com/dream.menu/"')
        if 'src="/nav.js"' in s and 'src="/dm-fresh.js"' not in s:
            s = s.replace('<script src="/nav.js" defer></script>', '<script src="/nav.js" defer></script><script src="/dm-fresh.js" defer></script>', 1)
        if 'src="/nav.js"' not in s:
            s = s.replace('<link rel="stylesheet" href="/brand.css">', HEAD_TAGS + '\n<link rel="stylesheet" href="/brand.css">', 1)
        if 'rel="manifest"' not in s:   # the installable app (28 Nov 2026): manifest, home-screen settings, app.js and app.css
            s = s.replace('</head>', APP_TAGS + '\n</head>', 1)
        if '/_vercel/insights/script.js' not in s:   # Vercel Web Analytics (cookie-free); switch it on in the Vercel dashboard
            s = s.replace('</head>', '<script defer src="/_vercel/insights/script.js"></script>\n</head>', 1)
        if False and fn == 'index.html' and 'class="audband"' not in s:   # the home page no longer carries the audience band (tools/build_home.py)
            m = re.search(r'(<section class="h-stats".*?</section>)', s, re.S)
            s = s[:m.end()] + '\n' + aud_band() + s[m.end():]
        if False and fn == 'explore.html':   # /explore retired 13 Nov 2026: the interest filter on the home page does its job
            s = re.sub(r'<!--cards-->.*?<!--/cards-->', lambda m: '<!--cards-->' + explore_cards() + '<!--/cards-->', s, flags=re.S)
        if s != o:
            open(fn, 'w').write(s)
            changed += 1
    print('pages updated:', changed, '| items:', len(IT))

if __name__ == '__main__':
    main()
