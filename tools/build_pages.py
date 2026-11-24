#!/usr/bin/env python3
"""Writes the analysis page /analysis (partner chapters unlock in place after sign-in) around the
site's shared head, header and footer (taken from insights.html). Run from the repository root:

    python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py

The charts are drawn in the browser by analysis.js and partner/intel.js from the data files
that build_intel.py writes. Section titles are filled from the data, so they stay true after a refresh.
"""
from vinfo import vinfo
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
T = open('insights.html', encoding='utf-8').read()
_ps = open('partner-data.js', encoding='utf-8').read()
P = json.JSONDecoder().raw_decode(_ps[_ps.index('=') + 1:])[0]
N_ALL = f"{P['n_all']:,}"   # interviews in the data, e.g. 1,234
import datetime as _dt
LAST_H = _dt.date.fromisoformat(P['last']).strftime('%-d %B %Y')   # e.g. 27 October 2026
HEAD_END = T.index('</head>')
BODY = T.index('<body')
HEADER = T[BODY:T.index('<main')]
HEADER = re.sub(r'<div class="confidential">.*?</div></div>\s*', '', HEADER, flags=re.S)
CONF = re.search(r'<div class="confidential">.*?</div></div>', T, re.S).group(0)
FOOTER = T[T.index('</main>') + len('</main>'):T.index('<script src="/partner-data.js">')]


def head(title, desc, url, robots=False):
    h = T[:HEAD_END]
    h = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', h)
    h = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + desc, h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + desc, h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + title, h)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>https://www.dream-menu.com' + url, h)
    h = re.sub(r'<style>.*?</style>\n?', '', h, flags=re.S)
    if robots:
        h += '<meta name="robots" content="noindex,nofollow">\n'
    h += '<link rel="stylesheet" href="/dmviz.css">\n'
    return h + '</head>\n'


def sec(n, kicker, tid, sub, body, sid=''):
    return (f'<section class="iv-sec" id="{sid}"><div class="iv-wrap">'
            f'<p class="iv-eyebrow"><span class="iv-num">{n}</span>{kicker}</p>'
            f'<h2 class="iv-title" id="{tid}" data-short="{kicker}">&nbsp;</h2>'
            f'<p class="iv-sub" id="s{tid[1:]}">{sub}</p>{body}</div></section>\n')


def sect(n, kicker, title, sub, body, sid):
    return (f'<section class="iv-sec" id="{sid}"><div class="iv-wrap">'
            f'<p class="iv-eyebrow"><span class="iv-num">{n}</span>{kicker}</p>'
            f'<h2 class="iv-title" data-short="{kicker}">{title}</h2>'
            f'<p class="iv-sub">{sub}</p>{body}</div></section>\n')


_tp = open('partner/trend-data.js', encoding='utf-8').read()
TX = json.JSONDecoder().raw_decode(_tp[_tp.index('window.DM_TRENDX=') + len('window.DM_TRENDX='):])[0]
_pp = open('trend-public.js', encoding='utf-8').read()
TP = json.JSONDecoder().raw_decode(_pp[_pp.index('window.DM_TRENDP=') + len('window.DM_TRENDP='):])[0]
_most = max(TX['churn'], key=lambda r: r['beyond'])
_n_stap = len(TP['staples'])

# ------------------------------------------------------------------ /analysis: one page, partner chapters unlock in place
LOCKSVG = '<svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'
LK = '<svg class="lk" viewBox="0 0 16 16" width="11" height="11" aria-label="Partners" role="img"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'


_others = [r['cl'].lower() + 's' for r in TX['churn'] if r is not _most]
_oth = ', '.join(_others[:-1]) + ' and ' + _others[-1]
_moved = _most['p'] < 0.05


def _js(fn):
    t = open(fn, encoding='utf-8').read()
    return json.JSONDecoder().raw_decode(t[t.index('{'):])[0]


AD, DRK, BEN = _js('analysis-data.js'), _js('drinks-new.js'), _js('bench-public.js')
_food = sorted([c for c in AD['conc'] if c['course'] in 'smdp'], key=lambda c: -c['top3'])
_open = _food[-1]
_set = next(c for c in _food if not (_moved and c['course'] == _most['course']))   # a course in flux is not one to call settled
_K = AD['critics']
_t25 = round(100 * _K['tops']['25']['award'] / _K['tops']['25']['n'])
_tall = round(100 * _K['tops'][str(_K['venues'])]['award'] / _K['venues'])
_a25 = round(100 * _K['tops']['25']['any'] / _K['tops']['25']['n'])
_aall = round(100 * _K['tops'][str(_K['venues'])]['any'] / _K['venues'])
_alc = {g['l']: g for g in DRK['alc']['groups']}
_af = _alc.get('Alcohol-free instead', {}).get('pct', 0)
_stap3 = ', '.join(x['l'].lower() for x in TP['staples'][:2]) + ' and ' + TP['staples'][2]['l'].lower()
_bagree = sum(1 for i in BEN['items'] if i['verdict'] == 'agrees')
_bdiff = sum(1 for i in BEN['items'] if i['verdict'] == 'differs')
_ball = len(BEN['items'])
import benchlib as _bl
# the counts below are spans that trend-charts.js rewrites from the comparisons the reader actually sees
# (21 signed out, every comparison once a partner signs in), so the title, intro and board always agree
BN = lambda k, v: f'<span data-bn="{k}">{v}</span>'

# ---- menu audit (tools/build_menu_audit.py): every figure below is read from menu-audit-public.js
def _audit():
    t = open('menu-audit-public.js', encoding='utf-8').read().split('window.DM_AUDIT=', 1)[1].strip().rstrip(';')
    return json.loads(t)


AU = _audit() if os.path.exists('menu-audit-public.js') else None
AU_SUB = AU_V = AU_I = AU_S = AU_M = ''
if AU and AU.get('rows'):
    _gaps = sorted([r for r in AU['rows'] if r['read'] == 'Gap'], key=lambda r: -r['demand'])
    _over = sorted([r for r in AU['rows'] if r['read'] == 'Over-supplied'], key=lambda r: -r['menus'])
    _apr = {x['course']: x for x in AU.get('prices', [])}
    _acn = AU.get('cn', {})
    if _gaps:
        _g = _gaps[0]
        _gc = _g['course'].lower()
        _same = [r for r in _gaps if r['course'] == _g['course']]
        _o = next((r for r in _over if r['course'] == _g['course']), _over[0] if _over else None)
        AU_SUB = (f' Then supply: we read the published menus of {AU["n"]} of the venues guests name most. {_g["l"]} is the {_gc} answer of {_g["demand"]:.1f}% of guests '
                  f'but is listed on {_g["menus"]:.0f}% of the {_acn.get(_g["course"], AU["n"])} menus that print {_gc}s'
                  + (f', against {_o["menus"]:.0f}% for {_o["l"].lower()}, which {_o["demand"]:.1f}% name' if _o else '') + '.')
        AU_V = (f' On the {_gc} list, check the {len(_same)} most-named {_gc}s first ({", ".join(r["l"].lower() for r in _same)}): '
                f'together they are {sum(r["demand"] for r in _same):.1f}% of {_gc} answers, and each is on {max(r["menus"] for r in _same):.0f}% or fewer of the menus we read.'
                if len(_same) > 1 else f' Check {_g["l"].lower()} first: {_g["demand"]:.1f}% of guests name it and {_g["menus"]:.0f}% of the menus we read list it.')
        AU_S = (' The menu audit shows where listings trail demand: ' + '; '.join(f'{r["l"].lower()} ({r["demand"]:.1f}% of guests, {r["menus"]:.0f}% of menus)' for r in _gaps[:3]) + '.')
        AU_M = (f' A fresh line from the menu audit: {_g["l"].lower()} is the most-named {_gc}, at {_g["demand"]:.1f}% of answers, yet {100 - _g["menus"]:.0f}% of the {_gc} menus we read leave it off.')
    if 'Main' in _apr and 'Starter' in _apr:
        _m, _s = _apr['Main'], _apr['Starter']
        AU_I = (f' For pricing, the middle printed price at the {AU["n"]} audited venues is £{_s["median"]:.2f} for a starter and £{_m["median"]:.2f} for a main '
                f'(half of all mains fall between £{_m["lo"]:.2f} and £{_m["hi"]:.2f}).')

DO = {  # one direct use per section, shown under its introduction
    'read': 'brief a team in two minutes. Every line is rechecked at each refresh, so quote it with its date.',
    'demand': 'set the shape of a menu or a range: lead each course with its biggest food group, protect the staples, and trial rising dishes as specials.',
    'category-sec': 'run a range review. Start with Grow and Defend: those are the lines where a decision is due.',
    'changed': (f'set priorities for the next menu change. Review {_most["cl"].lower()}s first; change {_oth} for cost or quality, not to chase a trend.'
                if _moved else 'set priorities. No course has moved beyond chance, so test new ideas as specials first.'),
    'drinks': 'set a baseline. Price alcohol-free properly now, and wait for two full quarters before acting on movement.',
    'cities': 'fit a menu to its market. Lean into dishes that sit above average in your city, and think twice before importing a favourite that sits below it.',
    'compare': 'calibrate confidence. Where outside data agrees, act; where it differs, test first, because foodies tend to lead the wider public.',
    'sell-sec': 'plan a call list. Pick a range and a market, then work down the list: each venue comes with the dish to lead with and what is falling there.',
    'opportunity-sec': 'start range conversations from the Back list, then use the matrix to see whether a dish is big, growing or both.',
    'confidence-sec': 'separate signal from noise, then plan stock from the shaded range, not the single line.',
    'segments-sec': 'match the range to the customer, and lead sales conversations with the pressures operators name most.',
}


def chap(n, kicker, title, sub, body, sid, partner=False, preview='', tid='', sub_id='', part=''):
    """One section of the story. Partner sections sit in .iv-pzone, which stays hidden until partner data loads."""
    t = f'<h2 class="iv-title"{f" id={chr(34)}{tid}{chr(34)}" if tid else ""} data-short="{kicker}">{title}</h2>'
    sp = f'<p class="iv-sub"{f" id={chr(34)}{sub_id}{chr(34)}" if sub_id else ""}>{sub}</p>'
    if sid in DO:
        sp += f'<p class="iv-do"><b>Use it to</b>{DO[sid]}</p>'
    tag = '<span class="pv-tag">Partners</span>' if partner else ''
    inner = body
    ph = f'<div class="iv-part"><div class="iv-wrap"><span>{part}</span></div></div>' if part else ''
    return (f'{ph}<section class="iv-sec" id="{sid}"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">{n}</span>{kicker}{tag}</p>'
            f'{t}{sp}{inner}</div></section>\n')


# demand mix (public): each food course's answers by food group. Category scorecard (partners): the same groups with their movement and a call.
_FOODC = [k for k in P['order'] if k in 'smdp']
MIX = dict(last=P['last'], n=P['n_all'], courses=[dict(k=k, label=P['trends'][k]['label'], base=P['trends'][k]['n'],
           groups=[dict(l=g['c'], p=g['pct']) for g in P['trends'][k]['groups'][:6]]) for k in _FOODC])
# sub layers inside a food group (seafood today): one shared source, see tools/sublayers.py
import sys as _sys; _sys.path.insert(0, os.path.join(ROOT, 'tools'))
from sublayers import sub_layers
MIX['sub'] = sub_layers(P)
# the ranking lists seafood as its dishes, not as one group: each seafood dish takes its own place among the food groups
for _co in MIX['courses']:
    _T = P['trends'][_co['k']]
    _S = MIX['sub'].get('Seafood', {}).get(_co['k'])
    _rows = [dict(l=g['c'], p=g['pct']) for g in _T['groups'] if not (_S and g['c'] == 'Seafood')]
    if _S:
        _rows += [dict(l=it['l'], p=it['p'], dish='Seafood', **({'slug': it['slug']} if it.get('slug') else {})) for it in _S['items'] if not it['l'].startswith('Other seafood')]
        _co['split'] = dict(g='Seafood', p=_S['p'])
    _co['groups'] = sorted(_rows, key=lambda r: -r['p'])[:8]
open('mix-public.js', 'w', encoding='utf-8').write('/* Generated by tools/build_pages.py. Public shares only. */\nwindow.DM_MIX=' + json.dumps(MIX, ensure_ascii=False, separators=(',', ':')) + ';\n')


def _call(g):
    if g['sig'] and g['move'] > 0:
        return 'Grow', 'Demand is clearly rising. Widen the range and lead specials with it.'
    if g['sig'] and g['pct'] >= 10:
        return 'Defend', 'Still large but clearly losing share. Hold the best sellers and cut the tail.'
    if g['sig']:
        return 'Trim', 'Small and clearly falling. Reduce lines as they sell through.'
    if g['pct'] >= 10:
        return 'Core', 'Large and steady. Compete on quality, price and availability.'
    return 'Niche', 'Small and steady. Stock to order.'


_COST = json.load(open('tools/data/market-watch.json', encoding='utf-8'))['cost']   # outside cost flags, shown beside the call
CATS = dict(last=P['last'], rows=[dict(course=P['trends'][k]['label'], l=g['c'], p=g['pct'], move=g['move'], sig=bool(g['sig']), call=_call(g)[0], do=_call(g)[1],
                                       **({'cost': {x: _COST[g['c']][x] for x in ('level', 'text', 'who', 'date')}} if g['c'] in _COST else {}))
                                  for k in _FOODC for g in P['trends'][k]['groups']])
open('partner/category-data.js', 'w', encoding='utf-8').write('/* Generated by tools/build_pages.py. Partner only (behind sign-in). */\nwindow.DM_CATS=' + json.dumps(CATS, ensure_ascii=False, separators=(',', ':')) + ';\n')
_ngrow = sum(1 for r in CATS['rows'] if r['call'] == 'Grow')
_ncut = sum(1 for r in CATS['rows'] if r['call'] in ('Defend', 'Trim'))
_lead = {c['k']: c['groups'][0] for c in MIX['courses']}
# headline: a course where the split seafood dishes together outweigh the top entry is still a seafood course
for _c in MIX['courses']:
    if _c.get('split') and _c['split']['p'] > _c['groups'][0]['p']:
        _d = next(g for g in _c['groups'] if g.get('dish'))
        _lead[_c['k']] = dict(l=f"Seafood, led by {_d['l'].lower()},", p=_c['split']['p'])

PARTS = [  # the questions the page answers, in order: label, anchor, lock
    ('The short version', 'read', False), ('What do guests want?', 'demand', False), ('What is changing?', 'changed', False),
    ('Where does it differ?', 'cities', False), ('Can we trust it?', 'compare', False), ('What should I do?', 'actions', False),
    ('Partner briefing', 'partner', True)]
toc = '<ol class="iv-story">' + ''.join(f'<li{" class=" + chr(34) + "iv-story-p" + chr(34) if lock else ""}><a href="#{a}"><b>{i}</b><span>{t}{" " + LK if lock else ""}</span></a></li>' for i, (t, a, lock) in enumerate(PARTS, 1)) + '</ol>'

_ROLES = [
    ('Running a venue or a kitchen',
     (f'Review the {_most["cl"].lower()} list first: it is the only course that has moved beyond chance. ' if _moved else 'No course has moved beyond chance, so trial new ideas as specials. ')
     + f'Protect the staples ({_stap3}). Give alcohol-free its own priced section: {_af:.1f}% of guests choose it when asked for an alcoholic drink.' + AU_V,
     '/operators', 'Operator toolkit'),
    ('Opening a venue or investing',
     f'Guests broadly agree on what {_set["cl"].lower()}s should be, so compete there on quality, not novelty. {_open["cl"]}s are the most open course: that is where a signature dish can stand out. '
     f'Recommendation is concentrated (the top 10% of venues take {_K["marks"]["10"]:.0f}% of mentions), so plan for word of mouth from day one.' + AU_I,
     '/map', 'Venue map and rankings'),
    ('Supplying venues or building a range',
     f'Build the core range around the {_n_stap} steady staples and follow the shift within {_most["cl"].lower()}s. '
     'Partners see which food groups gained and lost, a score for every dish and a three-quarter planning range.' + AU_S,
     '/for-business', 'Ways to work with us'),
    ('Marketing, press and guides',
     f'{_t25}% of the 25 most-named venues hold a current guide award ({_a25}% counting trade awards and other lists), against {_tall}% of all venues named ({_aall}%): guests and critics agree at the very top and part ways below it. '
     'The favourites beyond the guides are the stories nobody else has.' + AU_M,
     '/press', 'Press kit'),
]
ACTIONS = ('<div class="iv-roles">' + ''.join(
    f'<article><h3>{r}</h3><p>{t}</p><a href="{u}">{l} &rarr;</a></article>' for r, t, u, l in _ROLES) + '</div>')

CALLOUT = ('<div class="iv-callout"><svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 4.6V8l2.3 1.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span><b>Data to '
           + LAST_H + '.</b> Every chart includes all ' + N_ALL + ' interviews received to that date. Quarters with fewer than ' + str(P['min_n'])
           + ' answers, including the fourth quarter so far, are shown faded: read them as an early signal.</span></div>')
METHOD = open('tools/data/analysis-method.html', encoding='utf-8').read()
_ds = open('dm-data.js', encoding='utf-8').read()
DMD = json.JSONDecoder().raw_decode(_ds[_ds.index('window.DM=') + len('window.DM='):])[0]
_gt = sum(g['n'] for g in P['groups'])
_nat = [(m['n'], m['mn']) for m in DMD['markets'] if m['k'] == 'nation']
_uk = sum(n for _, n in _nat) or 1
_all = DMD['meta']['mentions']
_GL = {'Industry': 'Industry (chefs, operators, front of house)', 'Creators': 'Creators (food pages and writers)', 'Enthusiasts': 'Enthusiasts (foodies outside the trade)'}


def _bars(rows):
    return '<div class="bm-bars who-bars">' + ''.join(f'<div><span>{l}</span><i style="width:{v:.1f}%" class="bm-dmbar"></i><b>{'&lt;1' if 0 < v < 0.5 else format(v, '.0f')}%</b></div>' for l, v in rows) + '</div>'


WHO = (f'<div class="who"><div class="dmv-card"><h3>Who answers</h3><p class="who-s">Share of the {_gt:,} guests who answered the dish questions, by how they describe themselves.</p>' + vinfo('Each bar is one group’s share of the panel. Groups come from how guests introduce themselves, so they are a guide, not a strict job title.\nThe panel leans towards people who work in or write about food, which is why it tends to spot trends before the wider public.')
       + _bars([(_GL.get(g['g'], g['g']), 100 * g['n'] / _gt) for g in P['groups']])
       + f'</div><div class="dmv-card"><h3>Where their venues are</h3><p class="who-s">Share of the {_uk:,} UK venue mentions, by nation. {100 * (_all - _uk) / _all:.0f}% of all {_all:,} mentions are outside the UK or not placed in a nation.</p>' + vinfo('Each bar is a nation’s share of the venues guests named in the UK. It shows where the evidence is strongest: findings lean towards Scotland because most venues named are there.')
       + _bars([(n, 100 * c / _uk) for n, c in sorted(_nat, key=lambda x: -x[1])])
       + '</div></div><p class="iv-sub" style="max-width:80ch"><b>Read it as:</b> a large panel of food-led people, most of them in Scotland and many working in the trade. It leads the wider public on trends more than it mirrors it, which is why the &ldquo;Can we trust it?&rdquo; section sets the findings against national sources. Age, home city and how often guests eat out are not collected yet.</p>')
main = f"""<main class="iv-page">
<section class="iv-hero navy"><div class="iv-wrap">
<span class="iv-kick">The analysis</span>
<h1>What the UK’s foodies want, and where it’s heading</h1>
<p class="lede">{N_ALL} interviews, read the way a trade analyst would: demand, change, place, a check against outside data, then what to do. Five questions, one answer each, refreshed every week. Each question has its own page; partners who sign in see every chart.</p>
<p class="iv-also">Looking up one dish? <a href="/trends">Dish trends</a>. Need a dated publication? <a href="/report#library">Reports</a>.</p>
<!-- the numbered story list was dropped (24 Nov 2026): the "On this page" bar below the hero does that job -->
<div data-interest="analysis"></div>
</div></section>
{chap(1, 'The short version', 'What the data says this quarter', 'Each line is written from the numbers and rechecked at every refresh. The pages below show the evidence.', '<div id="th-find"></div><div class="pv-body"><div class="kpis" id="x-kpis"></div><div class="sowhat" id="x-sowhat"></div><h3 class="iv-h3" id="t1"></h3></div><div data-fresh="interviews look"></div>', 'read')}
{chap(2, 'What do guests want?', f"{_lead['s']['l']} to start, {_lead['m']['l'].lower()} for main, {_lead['d']['l'].lower()} on the side", f'Demand first. The chart ranks what guests name on each course: food groups, with seafood broken out into its dishes so scallops, prawns and white fish each take their own place. Below it is the life cycle that menu analysts use: a dish emerges, grows, becomes established and fades. {_n_stap} dishes are established staples that hold their share every quarter.{AU_SUB}', '<div id="th-demand"></div><div id="th-audit"></div><span id="life"></span><span id="settled-sec"></span><div id="th-life"></div>', 'demand', part='Question one')}
{chap(3, 'What is changing?', ('Sides are being rewritten; the rest of the menu is holding' if _most['course'] == 'd' else f"{_most['cl']}s changed most") if _moved else 'No course has changed beyond chance', f'{_most["obs"]}% of {_most["cl"].lower()} answers have moved to a different food group since late 2025, against about {_most["chance"]}% you would expect from the luck of who was asked. No other course has moved more than chance would explain.', '<div id="th-churn"></div><h3 class="iv-h3 iv-h3b" id="drinks">Drinks: a new baseline since August 2026</h3><p class="iv-sub">The drinks question was split into soft and alcoholic on 23 August 2026, so this series starts there. Levels only for now; movement will be tested once two quarters each hold 100 answers.</p><div id="th-drinks"></div>', 'changed', part='Question two')}
{chap(4, 'Where does it differ?', '&nbsp;', 'The national picture hides real differences between cities, and between what guests name and what guides reward. Shares, not counts, are used throughout, so a smaller city is compared fairly with Glasgow.', '<div id="c-cities"></div><span id="critics"></span><h3 class="iv-h3 iv-h3b" id="tb"></h3><p class="iv-sub" id="sb"></p><div id="c-critics"></div>', 'cities', tid='ta', part='Question three')}
{chap(5, 'Can we trust it?', f'Published research backs Dream Menu on {BN("agree", _bagree)} of {BN("all", _ball)} topics; {BN("local", _bdiff)} more are local insights', f'Every finding is checked against wider hospitality research: YouGov and Drinkaware polling, trade bodies such as the SLTA and the British Soft Drinks Association, wholesaler studies from Bidfood and CGA by NIQ, Seafish and Seafood Scotland, and sales data. On {BN("agree", _bagree)} of {BN("all", _ball)} topics they point the same way. Where they differ, the reason is local: Scottish foodies and the trade see a shift before the national average does. Outside figures sit beside Dream Menu data with their source and date, never inside it. <span class="bn-pnote">{_bl.partner_note()}</span>', '<div id="th-bench"></div>', 'compare', part='Question four')}
<div class="iv-part"><div class="iv-wrap"><span>Question five</span></div></div>
<section class="iv-sec" id="actions"><div class="iv-wrap"><p class="iv-eyebrow">What should I do?</p>
<h2 class="iv-title" data-short="What should I do?">The same evidence, read for four kinds of reader</h2>
<p class="iv-sub">Each recommendation follows from the sections above and is rewritten when the numbers change.</p>
{ACTIONS}
</div></section>
<div id="partner">
<section class="iv-pteaser"><div class="iv-wrap"><p><b>The partner briefing.</b> Below is everything partners get each quarter: the clear movers, a buying call for every category, the venues to call, a score for every dish, confidence ranges, who buys and partnership dates. The charts and figures unlock when you sign in. <a href="/for-business">Become a partner</a>.</p><a href="/login?next=/analysis%23partner">Partner sign-in</a></div></section>
<div class="iv-pzone">
<div class="iv-part"><div class="iv-wrap"><span>Partner briefing</span></div></div>
<div id="p-hub-top"></div>
{chap(6, 'Category scorecard', f'{_ngrow} categories to grow, {_ncut} to defend or trim', 'The buying view. Every food group in every course, with its share of demand, how that share has moved, and a call: Grow, Defend, Trim, Core or Niche. A move only earns a call when it passes a significance test.', '<div id="th-cats"></div>', 'category-sec', True, 'Every food group in every course with its share, its movement and a buying call: grow, defend, trim, core or niche.')}
{chap(7, 'Where to sell it', 'The venues to call, range by range', 'From categories to accounts. Every Scottish venue guests name at least twice, scored for each supplier range by the dishes guests name there and whether those dishes are worth backing. Each row gives the dish to lead with and anything falling at that venue. The <a href="/partner/accounts">full rep sheet</a> adds every venue, addresses, your own customer marks and print.', '<div id="th-sell"></div>', 'sell-sec', True, 'Scottish venues guests name for rising dishes, by supplier range, with the dish to lead with at each one.')}
{chap(8, 'What to back', 'A score for every dish and drink', 'From categories to single dishes. One ranking weighs size, momentum, strength of evidence and how open the field is: <b>Back</b>, <b>Watch</b> or <b>Review</b>. The matrix shows why a dish scores as it does.', '<div id="c-opp"></div><h3 class="iv-h3 iv-h3b" id="t2"></h3><div id="c-matrix"></div><span id="matrix-sec"></span>', 'opportunity-sec', True, 'A score out of 10 for every tracked dish and drink, with each one placed by size and momentum.', tid='t7')}
{chap(9, 'How sure, and where next', 'Which moves are real, and how far they go', '', '<div id="c-forest"></div><span id="next"></span><div id="th-fan"></div>', 'confidence-sec', True, 'Every change with its 95% range, and a three-quarter planning range for the clear movers.', tid='t3', sub_id='s3')}
{chap(10, 'Who buys', 'How guests differ, and how operators feel', 'Plan the range for the customer you sell to: trade, creators and enthusiasts answer differently. Then the people who buy: what operators feel, and where their response falls short of the pressure.', '<div id="c-seg"></div><span id="operators-sec"></span><h3 class="iv-h3 iv-h3b" id="t8"></h3><div id="c-ops"></div>', 'segments-sec', True, 'How industry, creators and enthusiasts differ on every course, and what 55 operators say about costs and confidence.', tid='t6')}
<div id="p-hub-bottom"></div>
<section class="iv-sec" id="reference"><div class="iv-wrap"><p class="iv-eyebrow">Partner reference</p>
<h2 class="iv-title" data-short="Partner reference">Every dish, in detail</h2>
<p class="iv-sub">The full tables behind the briefing. Open the ones you need.</p>
<details class="iv-ref" id="ref-board"><summary>Every tracked dish by life-cycle stage</summary><div data-card="tr-board"></div></details>
<details class="iv-ref" id="ref-slope"><summary>Then and now: every dish, earlier share against recent</summary><div data-card="tr-slope"></div></details>
<details class="iv-ref" id="wall-sec"><summary>Trend wall: the top six groups in every course</summary><h3 class="iv-h3" id="t4"></h3><div id="c-wall"></div></details>
<details class="iv-ref" id="heat-sec"><summary>Dish heat: each dish against its own average</summary><h3 class="iv-h3" id="t5"></h3><div id="c-heat"></div></details>
</div></section>
</div>
</div>
<section class="iv-sec" id="method"><div class="iv-wrap prose">
<p class="iv-eyebrow">Method</p>
<h2 class="iv-title" data-short="Method">Who answers, and how these numbers are made</h2>
{WHO}
<h3 class="iv-h3 iv-h3b">Supporting charts</h3>
<details class="iv-ref" id="ref-settled"><summary>How settled is each course? <small>Share of answers in the top three food groups</small></summary><h3 class="iv-h3" id="tc"></h3><div id="c-conc"></div></details>
<details class="iv-ref" id="converging"><summary>Are guests converging on the same favourites? <small>Top-five share by quarter</small></summary><div id="th-conc"></div></details>
<details class="iv-ref" id="ref-concentration"><summary>How concentrated are recommendations? <small>Share of mentions held by the most-named venues</small></summary><div data-card="concentration"></div></details>
{METHOD}
</div></section>
</main>
"""
an = (head('The analysis | Dream Menu', 'How each city eats, how guests compare with the critics, how the menu is changing and how Dream Menu compares with outside sources: analysis from ' + N_ALL + ' Dream Menu interviews.', '/analysis')
      + HEADER + main + FOOTER
      + '<script src="/dmviz.js"></script>\n<script src="/analysis-data.js"></script>\n<script src="/analysis.js"></script>\n'
      '<script src="/mix-public.js"></script><script src="/sublayers.js"></script><script src="/menu-audit-public.js"></script><script src="/trend-public.js"></script>\n<script src="/drinks-new.js"></script>\n<script src="/bench-public.js"></script>\n'
      '<script src="/partner/intel-data.js"></script>\n<script src="/partner/intel.js"></script>\n'
      '<script src="/partner/trend-data.js"></script><script src="/partner/category-data.js"></script>\n<script src="/partner/bench-data.js"></script>\n'
      '<script src="/trend-charts.js"></script>\n'
      '<script src="/partner-data.js"></script><script src="/partner/hub.js"></script><script src="/partner/sell-data.js"></script><script src="/partner/sell.js"></script><script src="/partner/briefing-extra.js"></script><script src="/partner/render.js"></script>\n'
      '<script src="/interest.js" defer></script>\n<script src="/fold.js" defer></script>\n'
      '<script>(function(){function o(){var t=location.hash&&document.getElementById(location.hash.slice(1));for(var e=t;e;e=e.parentElement)if(e.tagName==="DETAILS")e.open=true;if(t&&t.closest&&t.closest("details"))t.scrollIntoView();}addEventListener("hashchange",o);setTimeout(o,600);})();</script>\n</body>\n</html>\n')
# interest tags (interest.js): which sections show when a reader picks an interest. "all" always shows.
SECI = {'read': 'all', 'demand': 'food menu sales', 'changed': 'food drinks menu', 'cities': 'places food sales', 'compare': 'food drinks places sales costs',
        'actions': 'all', 'category-sec': 'menu food costs', 'sell-sec': 'sales places', 'opportunity-sec': 'sales menu food drinks', 'confidence-sec': 'menu food drinks',
        'segments-sec': 'costs sales', 'reference': 'food drinks menu', 'method': 'all'}
for _sid, _tags in SECI.items():
    an = an.replace(f'<section class="iv-sec" id="{_sid}">', f'<section class="iv-sec" id="{_sid}" data-i="{_tags}">', 1)
open('analysis.html', 'w', encoding='utf-8').write(an)

# the old partner page now lives inside /analysis
open('intelligence.html', 'w', encoding='utf-8').write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The analysis | Dream Menu</title>'
    '<meta name="robots" content="noindex"><link rel="canonical" href="https://www.dream-menu.com/analysis">'
    '<meta http-equiv="refresh" content="0; url=/analysis#matrix-sec"></head><body><p>Partner intelligence is now part of <a href="/analysis">the analysis</a>.</p></body></html>\n')
print('wrote analysis.html', len(an), '(intelligence.html is a redirect)')

# ---------------------------------------------------------------- the analysis, spread across the site (24 Nov 2026)
# Gordon: no single analysis page. Each part lives with the readers it serves:
#   Findings      /analysis/demand, /analysis/change, /analysis/cities
#   Findings      /analysis/partner (the briefing; charts greyed until sign-in)
#   About         /analysis/trust (Can we trust it?, with the method)
# "What should I do?" is split by reader (tools/data/evidence-roles.json, placed by tools/build_evidence.py):
# venues on the operator toolkit, opening and investing on Where it differs, suppliers on the partner briefing,
# press on the press kit. /analysis itself is a stub that forwards old /analysis#<id> links.
PARTS = [  # slug, section key (for the hero kicker), page title, section ids, one line under the title
    ('demand', 'Findings', 'What do guests want?', ['demand'], 'Each course ranked by food group, the dish life cycle, the staples, and demand against what menus list'),
    ('change', 'Findings', 'What is changing?', ['changed'], 'How much each course has moved against chance, the steady staples, and drinks'),
    ('cities', 'Findings', 'Where does it differ?', ['cities'], 'How each city eats, and where guests and the critics part ways'),
    ('partner', 'Findings', 'The partner briefing', ['partner'], 'Clear movers, a call for every category, the venues to call and a score for every dish. Charts unlock at sign-in'),
    ('trust', 'About', 'Can we trust it?', ['compare', 'method'], 'Dream Menu against national polls, eating-out data and menu trackers, and how the numbers are made'),
]

def _block(s, sid):
    if sid == 'partner':
        return s[s.index('<div id="partner">'):s.index('<section class="iv-sec" id="method"')]
    m = re.search(r'(<div class="iv-part"><div class="iv-wrap"><span>[^<]*</span></div></div>\s*)?<section class="iv-sec" id="' + sid + r'"', s)
    k = m.start(0) + (len(m.group(1)) if m.group(1) else 0)
    depth, j = 0, None
    for t in re.finditer(r'<(/?)section\b', s[k:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            j = k + t.end() + s[k + t.end():].index('>') + 1
            break
    return s[k:j]

_full = an
_mstart, _mend = _full.index('<main class="iv-page">'), _full.index('</main>')
_body = _full[_mstart:_mend]
_pre, _post = _full[:_mstart], _full[_mend:]
_url = lambda slug: '/analysis/' + slug

# the four reader cards from "What should I do?", for build_evidence.py
_roles = re.findall(r'<article><h3>(.*?)</h3><p>(.*?)</p><a href="([^"]*)">(.*?) &rarr;</a></article>', ACTIONS, re.S)
json.dump({'built': P['last'], 'n': N_ALL, 'roles': [dict(h=h, t=t, u=u, l=l) for h, t, u, l in _roles]},
          open('tools/data/evidence-roles.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def _role_box(i, sid='evidence'):
    h, t, u, l = _roles[i]
    return (f'<section class="iv-sec ev-box" id="{sid}"><div class="iv-wrap"><p class="iv-eyebrow">What the evidence says for you</p>'
            f'<h2 class="iv-title" data-short="What to do">{h}</h2><p class="iv-sub">{t}</p></div></section>\n')

_where = {'read': '/#now', 'actions': '/operators#evidence', 'parts': '/analysis/demand'}
for sl, kick, title, ids, line in PARTS:
    for sid in ids:
        for x in re.findall(r'\bid="([^"]+)"', _block(_body, sid)):
            _where.setdefault(x, _url(sl))
        _where[sid] = _url(sl)
_where.update({'matrix-sec': '/analysis/partner', 'data': '/analysis/partner', 'term': '/analysis/partner', 'partner': '/analysis/partner'})

_CSS = ('<style id="an-split">.iv-hero.an-sub{padding-top:28px;padding-bottom:26px}.iv-hero.an-sub h1{font-size:clamp(28px,4vw,44px)}'
        '.ev-box .iv-wrap{border-left:4px solid var(--gold);padding-left:18px}.ev-box .iv-sub{max-width:80ch;color:var(--ink)}</style>\n')
os.makedirs('analysis', exist_ok=True)
written = []
for sl, kick, title, ids, line in PARTS:
    content = ''.join(_block(_body, sid) + '\n' for sid in ids)
    if sl == 'cities' and len(_roles) > 1:
        content += _role_box(1)                                   # opening a venue or investing
    if sl == 'partner' and len(_roles) > 2:
        content = content.replace('<div class="iv-pzone">', _role_box(2) + '<div class="iv-pzone">', 1)   # suppliers
    hero = (f'<section class="iv-hero navy an-sub"><div class="iv-wrap"><span class="iv-kick">{kick}</span><h1>{title}</h1>'
            f'<p class="lede">{line}. From {N_ALL} Dream Menu interviews, refreshed every week.</p></div></section>')
    pre = _pre.replace('</head>', _CSS + '</head>', 1)
    if sl != 'partner':
        pre = pre.replace('<body', '<body class="no-onpage"', 1)   # short pages: the section tab bar is the one bar
    pre = re.sub(r'<title>[^<]*</title>', f'<title>{title} | Dream Menu</title>', pre, count=1)
    pre = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>https://www.dream-menu.com' + _url(sl), pre, count=1)
    pre = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + title + ' | Dream Menu', pre, count=1)
    pre = re.sub(r'(<meta (?:name|property)="(?:og:)?description" content=")[^"]*', lambda m: m.group(1) + line + '.', pre)
    open(f'analysis/{sl}.html', 'w', encoding='utf-8').write(pre + f'<main class="iv-page">\n{hero}\n{content}' + _post)
    written.append(f'analysis/{sl}.html')

# /analysis: a stub that sends old links to where each part now lives
_stub = ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>Findings | Dream Menu</title>'
         '<meta name="robots" content="noindex"><link rel="canonical" href="https://www.dream-menu.com/analysis/demand">'
         '<script>(function(){var W=' + json.dumps(_where, separators=(',', ':')) + ';var h=location.hash.slice(1);'
         'location.replace(W[h]?(W[h].indexOf("#")>0?W[h]:W[h]+"#"+h):"/analysis/demand");})();</script></head>'
         '<body><p>The analysis now lives across the site: <a href="/analysis/demand">What guests want</a>, <a href="/analysis/change">What is changing</a>, '
         '<a href="/analysis/cities">Where it differs</a>, <a href="/analysis/partner">the partner briefing</a> and <a href="/analysis/trust">Can we trust it?</a></p></body></html>\n')
open('analysis.html', 'w', encoding='utf-8').write(_stub)
_sm = open('sitemap.xml', encoding='utf-8').read()
_sm = _sm.replace('<url><loc>https://www.dream-menu.com/analysis</loc>', '<url><loc>https://www.dream-menu.com/analysis/demand</loc>') if '<loc>https://www.dream-menu.com/analysis/demand</loc>' not in _sm else re.sub(r'<url><loc>https://www\.dream-menu\.com/analysis</loc>.*?</url>\n?', '', _sm)
_add = ''.join(f'<url><loc>https://www.dream-menu.com{_url(sl)}</loc></url>\n' for sl, *_ in PARTS if f'<loc>https://www.dream-menu.com{_url(sl)}</loc>' not in _sm)
open('sitemap.xml', 'w', encoding='utf-8').write(_sm.replace('</urlset>', _add + '</urlset>'))
print('analysis spread:', ', '.join(written), '| /analysis forwards |', len(_roles), 'reader cards saved')
