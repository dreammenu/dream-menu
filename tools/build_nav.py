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

LOCKED = ('/briefing', '/onepager', '/review', '/geocoder', '/partner', '/report/', '/operators', '/tested-ideas', '/insights', '/intelligence')

AUD = [  # key, label, plural heading, blurb, curated picks (item ids, best first)
 ('food', 'Food lover', 'food lovers', 'What Scotland wants to eat, where to go, and the debates that never end.', ['f4', 'f6', 'f5', 'f8', 'f9', 'f14']),
 ('venue', 'Running a venue', 'people running a venue', 'Tools, benchmarks and tested ideas to lift every cover.', ['o3', 'o8', 'r9', 'r14', 'o6', 'o12']),
 ('new', 'Opening a venue', 'people opening a venue', 'Gaps in the market, neighbourhoods and the numbers to model before you sign.', ['r16', 'r8', 'r3', 'o3', 'r10', 'o12']),
 ('chef', 'Chef or kitchen lead', 'chefs and kitchen leads', 'What guests order, what is moving and what they are tired of.', ['r14', 'o4', 'r13', 'f5', 'f14', 'r10']),
 ('supplier', 'Supplier or brand', 'suppliers and brands', 'Demand signals, quarterly briefings and data to plan your range.', ['b8', 'b3', 'r13', 'r2', 'b5', 'f16']),
 ('investor', 'Investor or developer', 'investors and developers', 'Where the evidence points for capital, concepts and sites.', ['r18', 'r16', 'f16', 'r2', 'r8', 'f6']),
 ('press', 'Press or researcher', 'press and researchers', 'The findings, the method and the numbers worth quoting.', ['r2', 'f16', 'f4', 'o10', 'f8', 'r6']),
]
AUD_SHORT = {'food': 'food lovers', 'venue': 'operators', 'new': 'new venues', 'chef': 'chefs', 'supplier': 'suppliers', 'investor': 'investors', 'press': 'press'}
# extra search words, so people find things by the words they use
KEYWORDS = {
 'f1': 'dishes trends starters mains desserts drinks sides course', 'f4': 'irn-bru coke coffee tea pineapple pizza water', 'f5': 'comfort food matcha dubai chocolate tired',
 'f16': 'analysis index city glasgow edinburgh critics michelin awards concentration data', 'b8': 'dashboard analysis momentum matrix opportunity score confidence segments consultant',
 'f6': 'map restaurants bars cafes venues near me city country', 'f7': 'best restaurants top venues most named', 'f8': 'michelin stars 50 best bib gourmand guides',
 'f9': 'fringe cocktail sandwich edinburgh festival', 'f11': 'cocktails drinks bar bartender', 'f15': 'interview submit share my menu',
 'r2': 'headline summary key findings opportunities risks', 'r4': 'survey operators costs confidence trading energy labour', 'r8': 'finnieston southside shawlands barras west end rents sites location',
 'r9': 'advocacy recommend word of mouth signature dish', 'r13': 'rising falling demand quarter trends movers', 'r14': 'stop trends fatigue tired avoid', 'r16': 'gaps white space concept new venue idea brunch dessert late night',
 'r17': 'occasions brunch breakfast date celebration work lunch', 'r18': 'investment capital groups invest', 'r19': 'forecast predict next trends',
 'o3': 'revpash gross profit gp margin vat pricing price rise no-shows no shows deposits waste delivery apps regulars session costs labour food cost', 'o4': 'menu engineering stars dogs puzzles workhorses dish profitability',
 'o5': 'behavioural psychology nudges bread decoy wait', 'o6': 'checklist bathroom sunday festive christmas january quiet season price rise supplier solo diners celebration',
 'o7': 'instagram tiktok reviews google tripadvisor reply', 'o8': 'research evidence studies nudges menu psychology pricing no-shows reminder texts loyalty cards buffet plates music cutlery wine glass', 'o10': 'myths choice overload mints wansink',
 'o11': 'test trial experiment a/b sample size', 'o12': 'audit review consultancy diagnostic mystery', 'b3': 'quarterly briefing sales team movers', 'b5': 'csv download data export spreadsheet',
 'b1': 'partnership sponsor commission research data', 'b7': 'contact commission sponsor partner', 'a1': 'method methodology data sources interviews geocoding', 'a2': 'gdpr data protection cookies',
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

GROUPS = [  # key, label, landing page, one-line summary
 ('food', 'Food & places', '/', 'What guests dream of eating and where they go'),
 ('report', 'Report 2026', '/report', 'The Hospitality Intelligence Report 2026'),
 ('ops', 'Operators', '/operators', 'Tools, benchmarks and tested ideas for venues'),
 ('biz', 'For business', '/for-business', 'Partnerships, briefings and data'),
 ('about', 'About', '/how-it-works', 'How Dream Menu works'),
]

# id, title, url, description, group, audiences, star (featured), parent id
ITEMS = [
 ('f1', 'Food trends', '/', f'What {N_ALL} guests dream of eating, course by course and city by city', 'food', 'food chef supplier press', 1, None),
 ('f16', 'The analysis', '/analysis', 'Every city\'s appetite indexed, guests against the critics, and how settled each course is', 'food', 'food investor press supplier', 1, None),
 ('f17', "Every city's appetite, indexed", '/analysis#cities', 'Which dishes each market names more than everyone else', 'food', 'investor new supplier', 0, 'f16'),
 ('f18', 'Guests and critics', '/analysis#critics', 'How far guest favourites and guide award winners overlap', 'food', 'food press', 0, 'f16'),
 ('f2', 'The dishes people choose', '/#courses', 'The top dishes for every course and their share of guests', 'food', 'food chef supplier', 0, 'f1'),
 ('f3', "Every city's appetite", '/#places', 'What Glasgow, Edinburgh and every market names, and the venues behind it', 'food', 'food investor supplier', 0, 'f1'),
 ('f4', 'The great debates', '/#debates', 'Irn-Bru or Coke, coffee or tea, pineapple on pizza, tap or sparkling', 'food', 'food press', 1, 'f1'),
 ('f5', 'Guilty pleasures and Bin it', '/#mood', 'The comfort food guests admit to, and the trends they want gone', 'food', 'food chef venue', 1, 'f1'),
 ('f6', 'Venue map', '/map', f'{N_PINNED} venues guests have named in {N_COUNTRIES} countries, with award winners', 'food', 'food investor new supplier', 1, None),
 ('f7', 'Rankings', '/rankings', 'The venues guests name most, by market and by course', 'food', 'food venue press', 0, None),
 ('f8', 'Award winners', '/awards', '21,008 MICHELIN, 50 Best and guide winners in one searchable list', 'food', 'food press investor', 0, None),
 ('f9', 'Specials', '/specials', 'Themed editions: Dream Fringe, Dream Cocktail and Dream Sandwich', 'food', 'food chef', 0, None),
 ('f10', 'Dream Fringe', '/specials#fringe', 'Late-night food after the shows and the best Fringe venues', 'food', 'food', 0, 'f9'),
 ('f11', 'Dream Cocktail', '/specials#cocktail', 'The drinks guests and bartenders would order', 'food', 'food chef', 0, 'f9'),
 ('f12', 'Dream Sandwich', '/specials#sandwich', 'The sandwiches Scotland dreams of', 'food', 'food', 0, 'f9'),
 ('f13', 'From the kitchen', '/from-the-kitchen', 'Cafés, restaurants and bars describe their menus in three words', 'food', 'food chef', 0, None),
 ('f14', 'Advice for anyone who cooks', '/from-the-kitchen#advice', 'Tips from the people who cook for a living', 'food', 'food chef', 0, 'f13'),
 ('f15', 'Take part', '/take-part', 'Share your own dream menu: five courses and the venue that does it best', 'food', 'food', 0, None),

 ('r1', 'Report overview', '/report', 'Where Glasgow and Scotland actually eat: the community view, the operator view and tracked demand', 'report', 'venue new investor supplier press chef', 0, None),
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

 ('o1', 'Operator toolkit', '/operators', 'The top 20 actions, calculators, a menu matrix and checklists', 'ops', 'venue new chef', 0, None),
 ('o2', 'The top 20 actions', '/operators#actions', 'What to do first, from identity to strategy', 'ops', 'venue new', 0, 'o1'),
 ('o3', 'Calculators', '/operators#numbers', 'RevPASH, dish pricing, price rises, no-shows, waste, delivery and more', 'ops', 'venue new', 1, 'o1'),
 ('o4', 'Menu matrix', '/operators#matrix', 'Paste your dishes and see which earn their place', 'ops', 'chef venue', 1, 'o1'),
 ('o5', 'Odd ideas that work', '/operators#odd', 'Ten behavioural ideas, each with a test to run this week', 'ops', 'venue chef', 0, 'o1'),
 ('o6', 'Checklists', '/operators#checklists', 'Thirteen tickable lists, from the first 90 seconds to the festive season', 'ops', 'venue', 0, 'o1'),
 ('o7', 'Social media and reviews', '/operators#digital', 'The three-post week and how to reply to every kind of review', 'ops', 'venue', 0, 'o1'),
 ('o8', 'Tested ideas', '/tested-ideas', '20 ideas scored against the research, with a trial for each', 'ops', 'venue chef supplier press', 1, None),
 ('o9', 'The evidence map', '/tested-ideas#matrix', 'Every idea placed by impact and strength of evidence', 'ops', 'venue press', 0, 'o8'),
 ('o10', 'Myths busted', '/tested-ideas#myths', "Five things operators are told that don't stand up", 'ops', 'venue press', 0, 'o8'),
 ('o11', 'Trial planner', '/tested-ideas#trial', 'How long a test needs, and why pooling venues helps', 'ops', 'venue supplier', 0, 'o8'),
 ('o12', 'Restaurant MOT', '/restaurant-mot', 'An independent four-week diagnostic of one venue', 'ops', 'venue new', 0, None),

 ('b1', 'For business', '/for-business', 'Market intelligence from over a thousand conversations with Scotland\'s food people', 'biz', 'supplier investor venue', 0, None),
 ('b7', 'Work with us', '/for-business#work', 'Partnerships, commissioned research and sponsorship', 'biz', 'supplier investor', 0, 'b1'),
 ('b2', 'Partner area', '/partner', 'Everything included in the partnership, in one place', 'biz', 'supplier', 0, None),
 ('b8', 'Partner intelligence', '/intelligence', 'Momentum matrix, confidence ranges, segments, opportunity scores and the operator pulse', 'biz', 'supplier investor', 1, 'b2'),
 ('b3', 'Partner briefing', '/briefing', 'The quarterly market read: clear movers and what operators say', 'biz', 'supplier', 1, 'b2'),
 ('b4', 'Insights', '/insights', 'Debates, dishes by group and how the trade feels, in full', 'biz', 'supplier chef press', 0, 'b2'),
 ('b5', 'Data extracts', '/partner#data', 'Structured CSV downloads for your own analysis', 'biz', 'supplier press', 0, 'b2'),
 ('b6', 'Partner one-pager', '/onepager', 'One page to share with your team', 'biz', 'supplier', 0, 'b2'),

 ('a1', 'How it works', '/how-it-works', 'Where the data comes from, how venues are placed and which guides count', 'about', 'press', 0, None),
 ('a2', 'Privacy', '/privacy', 'How interview answers and site visits are used', 'about', 'press', 0, None),
]

IT = {}
for row in ITEMS:
    i, t, u, d, g, a, s, p = row
    IT[i] = dict(id=i, t=t, u=u, d=d, g=g, a=a.split(), s=bool(s), p=p, lock=u.startswith(LOCKED), k=KEYWORDS.get(i, ''))

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
    # audience menu
    out.append('<li class="mnav-item mnav-aud" data-g="start"><a class="mnav-top" href="/explore" aria-expanded="false" aria-controls="mp-start"><span>I&rsquo;m a&hellip;</span>' + CHEV + '</a>')
    out.append('<div class="mpanel mp-aud" id="mp-start"><div class="mp-inner">')
    out.append('<div class="aud-tabs" role="tablist" aria-label="Choose who you are">')
    for n, (k, lab, pl, bl, picks) in enumerate(AUD):
        out.append(f'<button type="button" role="tab" id="at-{k}" data-aud="{k}" aria-controls="ap-{k}" aria-selected="{"true" if n == 0 else "false"}" tabindex="{0 if n == 0 else -1}">{aicon(k)}<span>{E(lab)}</span></button>')
    out.append('</div><div class="aud-panes">')
    for n, (k, lab, pl, bl, picks) in enumerate(AUD):
        out.append(f'<div class="aud-pane" role="tabpanel" id="ap-{k}" aria-labelledby="at-{k}"{"" if n == 0 else " hidden"}>')
        out.append(f'<p class="aud-blurb"><b>Start here</b>{E(bl)}</p><ul class="picks">')
        for pid in picks:
            it = IT[pid]
            out.append(f'<li><a href="{it["u"]}"><b>{E(it["t"])}{lk(it)}</b><span>{E(it["d"])}</span></a></li>')
        out.append(f'</ul><a class="aud-all" href="/explore?for={k}">Everything for {E(pl)} ({aud_count(k)}) {ARROW}</a></div>')
    out.append('</div></div></div></li>')
    # content menus
    for g, lab, land, summ in GROUPS:
        if g == 'about':
            continue
        cur = ' aria-current="true"' if g == cur_group else ''
        out.append(f'<li class="mnav-item" data-g="{g}"><a class="mnav-top" href="{land}" aria-expanded="false" aria-controls="mp-{g}"{cur}><span>{E(lab)}</span>{CHEV}</a>')
        out.append(f'<div class="mpanel" id="mp-{g}"><div class="mp-inner mp-cols"><div class="mp-links">')
        for it in pages(g):
            out.append(f'<div class="mp-page"><a class="mp-p" href="{it["u"]}"><b>{E(it["t"])}{lk(it)}</b><span>{E(it["d"])}</span></a>')
            ch = children(it['id'])
            if ch:
                out.append('<ul class="mp-sub">' + ''.join(f'<li><a href="{c["u"]}">{E(c["t"])}</a></li>' for c in ch) + '</ul>')
            out.append('</div>')
        out.append('</div><aside class="mp-feature"><p class="mp-eyebrow">Don&rsquo;t miss</p>')
        stars = [x for x in IT.values() if x['g'] == g and x['s']][:3]
        for it in stars:
            out.append(f'<a class="mp-star" href="{it["u"]}"><b>{E(it["t"])}{lk(it)}</b><span>{E(it["d"])}</span>{ARROW}</a>')
        out.append(f'<a class="mp-land" href="{land}">Go to {E(lab)} {ARROW}</a></aside></div></div></li>')
    out.append('</ul><a class="mnav-all" href="/explore">See everything on Dream Menu ' + ARROW + '</a></nav>')
    out.append('<button type="button" class="msearch" data-search aria-label="Search the site">' + SEARCH + '<span>Search</span><kbd>/</kbd></button>')
    out.append('<a class="takepart" href="/take-part">Take part</a>')
    out.append('<button type="button" class="mburger" aria-expanded="false" aria-controls="mnav"><span class="bars" aria-hidden="true"><i></i><i></i><i></i></span><span class="sr">Menu</span></button>')
    out.append('</div></header>')
    return ''.join(out)

def footer_links():
    out = ['<nav class="footlinks footcols" aria-label="All pages">']
    for g, lab, land, summ in GROUPS:
        out.append(f'<div><b>{E(lab)}</b>')
        for it in pages(g):
            out.append(f'<a href="{it["u"]}">{E(it["t"])}{lk(it)}</a>')
        if g == 'about':
            out.append('<a href="/explore">Explore everything</a><a href="/login">Partner sign-in</a>')
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
    for it in IT.values():
        if it['u'] == path:
            return it['g']
    return {'/explore': 'start'}.get(path)

HEAD_TAGS = '<script>document.documentElement.classList.add("js")</script><script src="/nav-data.js" defer></script><script src="/nav.js" defer></script><script src="/dm-fresh.js" defer></script>'

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    data = dict(aud=[dict(k=k, l=l, p=p, sh=AUD_SHORT[k], b=b, picks=picks) for k, l, p, b, picks in AUD],
                groups=[dict(k=g, l=l, u=u, d=d) for g, l, u, d in GROUPS],
                items=[dict(id=x['id'], t=x['t'], u=x['u'], d=x['d'], g=x['g'], a=x['a'], s=x['s'], p=x['p'], lock=x['lock'], k=x['k']) for x in IT.values()])
    with open('nav-data.js', 'w') as f:
        f.write('/* Generated by tools/build_nav.py: edit the list there, not this file. */\nwindow.DM_NAV=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    foot = footer_links()
    changed = 0
    for fn in sorted(glob.glob('*.html') + glob.glob('report/*.html')):
        s = open(fn).read()
        o = s
        path = '/' + fn[:-5]
        path = '/' if path == '/index' else path
        s = re.sub(r'<header class="top">.*?</header>', lambda m: header(page_group(path)), s, count=1, flags=re.S)
        s = re.sub(r'<nav class="footlinks[^"]*" aria-label="All pages">.*?</nav>', lambda m: foot, s, count=1, flags=re.S)
        if 'src="/nav.js"' in s and 'src="/dm-fresh.js"' not in s:
            s = s.replace('<script src="/nav.js" defer></script>', '<script src="/nav.js" defer></script><script src="/dm-fresh.js" defer></script>', 1)
        if 'src="/nav.js"' not in s:
            s = s.replace('<link rel="stylesheet" href="/brand.css">', HEAD_TAGS + '\n<link rel="stylesheet" href="/brand.css">', 1)
        if fn == 'index.html' and 'class="audband"' not in s:
            m = re.search(r'(<section class="h-stats".*?</section>)', s, re.S)
            s = s[:m.end()] + '\n' + aud_band() + s[m.end():]
        if fn == 'explore.html':
            s = re.sub(r'<!--cards-->.*?<!--/cards-->', lambda m: '<!--cards-->' + explore_cards() + '<!--/cards-->', s, flags=re.S)
        if s != o:
            open(fn, 'w').write(s)
            changed += 1
    print('pages updated:', changed, '| items:', len(IT))

if __name__ == '__main__':
    main()
