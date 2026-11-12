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
_alc = {g['l']: g for g in DRK['alc']['groups']}
_af = _alc.get('Alcohol-free instead', {}).get('pct', 0)
_stap3 = ', '.join(x['l'].lower() for x in TP['staples'][:2]) + ' and ' + TP['staples'][2]['l'].lower()
_bagree = sum(1 for i in BEN['items'] if i['verdict'] == 'agrees')
_bdiff = sum(1 for i in BEN['items'] if i['verdict'] == 'differs')

DO = {  # one direct use per section, shown under its introduction
    'read': 'brief a team in two minutes. Every line is rechecked at each refresh, so quote it with its date.',
    'settled-sec': 'decide where to be different. Keep a settled course short and well made, and put your signature dish in the most open one.',
    'life': 'manage the range: protect the staples, trial rising dishes as specials, and retire fading ones on your own schedule.',
    'changed': (f'set priorities for the next menu change. Review {_most["cl"].lower()}s first; change {_oth} for cost or quality, not to chase a trend.'
                if _moved else 'set priorities. No course has moved beyond chance, so test new ideas as specials first.'),
    'drinks': 'set a baseline. Price alcohol-free properly now, and wait for two full quarters before acting on movement.',
    'cities': 'fit a menu to its market. Lean into dishes that sit above average in your city, and think twice before importing a favourite that sits below it.',
    'critics': 'decide what to promote. Where guests and critics agree, shout about it; where guests lead, you are ahead of the guides.',
    'compare': 'calibrate confidence. Where outside data agrees, act; where it differs, test first, because foodies tend to lead the wider public.',
    'opportunity-sec': 'start range conversations from the Back list, then use the matrix to see whether a dish is big, growing or both.',
    'confidence-sec': 'separate signal from noise. Act on a move only when its whole range sits clear of zero.',
    'next': 'plan stock and ranges from the shaded range, not the single line.',
    'segments-sec': 'match the range to the customer: trade buyers, creators and diners want different things.',
    'operators-sec': 'lead sales conversations with the pressures operators name most, and the gaps in their response.',
}


def chap(n, kicker, title, sub, body, sid, partner=False, preview='', tid='', sub_id='', part=''):
    """One section of the story. Partner sections show a short preview with a sign-in link until partner data loads."""
    t = f'<h2 class="iv-title"{f" id={chr(34)}{tid}{chr(34)}" if tid else ""} data-short="{kicker}">{title}</h2>'
    sp = f'<p class="iv-sub"{f" id={chr(34)}{sub_id}{chr(34)}" if sub_id else ""}>{sub}</p>'
    if sid in DO:
        sp += f'<p class="iv-do"><b>Use it to</b>{DO[sid]}</p>'
    tag = '<span class="pv-tag">Partners</span>' if partner else ''
    inner = body
    if partner:
        inner = (f'<div class="pv-lock">{LOCKSVG}<p><b>For Dream Menu partners.</b> {preview}</p>'
                 f'<a href="/login?next=/analysis">Partner sign-in</a></div><div class="pv-body">{body}</div>')
    ph = f'<div class="iv-part"><div class="iv-wrap"><span>{part}</span></div></div>' if part else ''
    return (f'{ph}<section class="iv-sec" id="{sid}"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">{n}</span>{kicker}{tag}</p>'
            f'{t}{sp}{inner}</div></section>\n')


PARTS = [  # the story in order: label, anchor, lock
    ('The short version', 'read', False), ('What guests want', 'settled-sec', False), ('What is changing', 'changed', False),
    ('Where it differs', 'cities', False), ('The reality check', 'compare', False), ('What to do', 'actions', False),
    ('Partner briefing', 'opportunity-sec', True), ('Reference charts', 'reference', False)]
toc = '<ol class="iv-story">' + ''.join(f'<li><a href="#{a}"><b>{i}</b><span>{t}{" " + LK if lock else ""}</span></a></li>' for i, (t, a, lock) in enumerate(PARTS, 1)) + '</ol>'

_ROLES = [
    ('Running a venue or a kitchen',
     (f'Review the {_most["cl"].lower()} list first: it is the only course that has moved beyond chance. ' if _moved else 'No course has moved beyond chance, so trial new ideas as specials. ')
     + f'Protect the staples ({_stap3}). Give alcohol-free its own priced section: {_af:.1f}% of guests choose it when asked for an alcoholic drink.',
     '/operators', 'Operator toolkit'),
    ('Opening a venue or investing',
     f'Guests broadly agree on what {_set["cl"].lower()}s should be, so compete there on quality, not novelty. {_open["cl"]}s are the most open course: that is where a signature dish can stand out. '
     f'Recommendation is concentrated (the top 10% of venues take {_K["marks"]["10"]:.0f}% of mentions), so plan for word of mouth from day one.',
     '/map', 'Venue map and rankings'),
    ('Supplying venues or building a range',
     f'Build the core range around the {_n_stap} steady staples and follow the shift within {_most["cl"].lower()}s. '
     'Partners see which food groups gained and lost, a score for every dish and a three-quarter planning range.',
     '/for-business', 'Ways to work with us'),
    ('Marketing, press and guides',
     f'{_t25}% of the 25 most-named venues hold a guide award, against {_tall}% of all venues named: guests and critics agree at the very top and part ways below it. '
     'The favourites beyond the guides are the stories nobody else has.',
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
_GL = {'Industry': 'Industry (chefs, operators, front of house)', 'Creators': 'Creators (food pages and writers)', 'Enthusiasts': 'Enthusiasts (people who love eating out)'}


def _bars(rows):
    return '<div class="bm-bars who-bars">' + ''.join(f'<div><span>{l}</span><i style="width:{v:.1f}%" class="bm-dmbar"></i><b>{'&lt;1' if 0 < v < 0.5 else format(v, '.0f')}%</b></div>' for l, v in rows) + '</div>'


WHO = (f'<div class="who"><div class="dmv-card"><h3>Who answers</h3><p class="who-s">Share of the {_gt:,} guests who answered the dish questions, by how they describe themselves.</p>' + vinfo('Each bar is one group’s share of the panel. Groups come from how guests introduce themselves, so they are a guide, not a strict job title.\nThe panel leans towards people who work in or write about food, which is why it tends to spot trends before the wider public.')
       + _bars([(_GL.get(g['g'], g['g']), 100 * g['n'] / _gt) for g in P['groups']])
       + f'</div><div class="dmv-card"><h3>Where their venues are</h3><p class="who-s">Share of the {_uk:,} UK venue mentions, by nation. {100 * (_all - _uk) / _all:.0f}% of all {_all:,} mentions are outside the UK or not placed in a nation.</p>' + vinfo('Each bar is a nation’s share of the venues guests named in the UK. It shows where the evidence is strongest: findings lean towards Scotland because most venues named are there.')
       + _bars([(n, 100 * c / _uk) for n, c in sorted(_nat, key=lambda x: -x[1])])
       + '</div></div><p class="iv-sub" style="max-width:80ch"><b>Read it as:</b> a large panel of food-led people, most of them in Scotland and many working in the trade. It leads the wider public on trends more than it mirrors it, which is why chapter 9 sets the findings against national sources. Age, home city and how often guests eat out are not collected yet.</p>')
main = f"""<main class="iv-page">
<section class="iv-hero navy"><div class="iv-wrap">
<span class="iv-kick">The analysis</span>
<h1>What the UK’s foodies want, and where it’s heading</h1>
<p class="lede">{N_ALL} interviews, read as one story: what guests want, what is changing, where cities and critics differ, how it compares with outside data, and what to do about it. Parts 1 to 6 are open to all. Partners also get the briefing in part 7. Every chart has a short guide, a table view and a download.</p>
{toc}
</div></section>
{chap(1, 'The short version', 'What the data says this quarter', 'If you read one section, read this. Each line is written from the numbers and rechecked at every refresh; the sections below show the evidence behind it. Partners also see the executive read: clear movers, operator confidence and the three things to plan around.', '<div id="th-find"></div><div class="pv-body"><div class="kpis" id="x-kpis"></div><div class="sowhat" id="x-sowhat"></div><h3 class="iv-h3" id="t1"></h3></div>' + CALLOUT + '<div data-fresh="interviews look"></div>', 'read', part='Part one · The short version')}
{chap(2, 'How settled the menu is', '&nbsp;', 'Start with the shape of demand. Where guests agree on what a course should be, a menu has to deliver the favourite well. Where they do not, there is room to be different.', '<div id="c-conc"></div>', 'settled-sec', tid='tc', part='Part two · What guests want')}
{chap(3, 'The dishes that hold', f"{_n_stap} dishes hold their share in every quarter: the core of any menu", 'Most dishes drift up and down with the sample. A few never do. These are the staples guests keep choosing whatever else is in fashion, and beside them is how many of each course’s dishes are rising, steady or fading. Partners can open every dish by name in the reference charts.', '<div id="th-life"></div>', 'life')}
{chap(4, 'What changed', ('Sides are being rewritten; the rest of the menu is holding' if _most['course'] == 'd' else f"{_most['cl']}s changed most") if _moved else 'No course has changed beyond chance', f'So much for what holds. Now for what moves. Comparing late 2025 with the recent quarters, {_most["obs"]}% of {_most["cl"].lower()} answers sit in a different food group, against about {_most["chance"]}% that sampling alone would produce. No other course clears that bar. Do guests pile onto fewer favourites as a result? No: the five favourite dishes in each course hold the share they did a year ago (reference charts). Partners also see where the share went, food group by food group.', '<div id="th-churn"></div>', 'changed', part='Part three · What is changing')}
{chap(5, 'Drinks, restarted', 'What guests drink, on a clean new series', 'Drinks need their own telling. The question was split into soft and alcoholic on 23 August 2026, so the old drink trends stopped there. This is the new baseline, built only from the new questions; movement will be tested once two quarters each hold 100 answers.', '<div id="th-drinks"></div>', 'drinks')}
{chap(6, 'Every city’s appetite', '&nbsp;', 'The national picture hides real differences. Shares, not counts, are used throughout, so a city with fewer interviews is compared fairly with Glasgow.', '<div class="kpis" id="city-sig"></div><div id="c-cities"></div>', 'cities', tid='ta', part='Part four · Where it differs')}
{chap(7, 'Guests and critics', '&nbsp;', '', '<div id="c-critics"></div>', 'critics', tid='tb', sub_id='sb')}
{chap(8, 'How we compare', f'Outside data agrees with Dream Menu on {_bagree} topics and challenges it on {_bdiff}', 'A panel of food-led people is not the general public, so every finding deserves a check. Here national polls, eating-out data, menu trackers and sales figures sit beside Dream Menu’s own numbers. Outside figures are never mixed into Dream Menu data: they stand alongside it, with their source and date, as a check and a challenge. Partners also see dish, drink and operator comparisons.', '<div id="th-bench"></div>', 'compare', part='Part five · The reality check')}
<div class="iv-part"><div class="iv-wrap"><span>Part six · What to do</span></div></div>
<section class="iv-sec" id="actions"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">9</span>What to do about it</p>
<h2 class="iv-title" data-short="What to do">The same evidence, read for four kinds of reader</h2>
<p class="iv-sub">Each recommendation follows from the sections above and is rewritten when the numbers change.</p>
{ACTIONS}
</div></section>
{chap(10, 'What to back', 'A score for every dish and drink', 'The briefing starts with the answer: one ranking that weighs size, momentum, strength of evidence and how open the field is. <b>Back</b> = rising clearly or scoring 60 and over. <b>Watch</b> = promising, not proven. <b>Review</b> = falling clearly or scoring low and drifting down. The matrix below it shows why a dish scores as it does: how big it is against how fast it is moving.', '<div id="c-opp"></div><h3 class="iv-h3 iv-h3b" id="t2"></h3><div id="c-matrix"></div><span id="matrix-sec"></span>', 'opportunity-sec', True, 'A score out of 10 for every tracked dish and drink (back it, watch it or review it), with each one placed by size and momentum.', tid='t7', part='Part seven · Partner briefing')}
{chap(11, 'How sure we are', 'Which moves are real', '', '<div id="c-forest"></div>', 'confidence-sec', True, 'Every change with its 95% range, so you can tell a real move from noise before acting on it.', tid='t3', sub_id='s3')}
{chap(12, 'Next three quarters', 'Where the clear movers are heading', 'Once a move is clear, the question is how far it goes. A damped projection gives each clear mover a planning range for range reviews and stock; it weighs recent quarters more and flattens over time.', '<div id="th-fan"></div>', 'next', True, 'A three-quarter planning range for every dish and food group that is clearly rising or falling.')}
{chap(13, 'Who wants what', 'How each group of guests differs', 'A score is an average. Industry (chefs, operators, front of house), creators (food pages and writers) and enthusiasts answer differently, so plan the range for the customer you are selling to.', '<div id="c-seg"></div>', 'segments-sec', True, 'How industry, creators and enthusiasts differ on every course.', tid='t6')}
{chap(14, 'Operator pulse', 'How operators feel, and where they need help', 'Last, the people who buy. What operators are feeling, and where their response falls short of the pressure: this is where a supplier can help.', '<div id="c-ops"></div>', 'operators-sec', True, 'What 55 operators say about costs, confidence and the gaps a supplier can fill.', tid='t8')}
<div class="iv-part"><div class="iv-wrap"><span>Reference</span></div></div>
<section class="iv-sec" id="reference"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">15</span>Reference charts</p>
<h2 class="iv-title" data-short="Reference">The detail behind the story</h2>
<p class="iv-sub">Charts that support a point made above without needing a section of their own. Open the ones you need.</p>
<details class="iv-ref" id="converging"><summary>Are guests converging on the same favourites? <small>Top-five share by quarter</small></summary><div id="th-conc"></div></details>
<details class="iv-ref" id="ref-concentration"><summary>How concentrated are recommendations? <small>Share of mentions held by the most-named venues</small></summary><div data-card="concentration"></div></details>
<div class="pv-body">
<details class="iv-ref" id="ref-board"><summary>Every tracked dish by life-cycle stage <small>Partners</small></summary><div data-card="tr-board"></div></details>
<details class="iv-ref" id="ref-slope"><summary>Then and now: every dish, earlier share against recent <small>Partners</small></summary><div data-card="tr-slope"></div></details>
<details class="iv-ref" id="wall-sec"><summary>Trend wall: the top six groups in every course <small>Partners</small></summary><h3 class="iv-h3" id="t4"></h3><div id="c-wall"></div></details>
<details class="iv-ref" id="heat-sec"><summary>Dish heat: each dish against its own average <small>Partners</small></summary><h3 class="iv-h3" id="t5"></h3><div id="c-heat"></div></details>
</div>
</div></section>
<section class="iv-sec" id="method"><div class="iv-wrap prose">
<p class="iv-eyebrow">Method</p>
<h2 class="iv-title" data-short="Method">Who answers, and how these numbers are made</h2>
{WHO}
{METHOD}
</div></section>
</main>
"""
an = (head('The analysis | Dream Menu', 'How each city eats, how guests compare with the critics, how the menu is changing and how Dream Menu compares with outside sources: analysis from ' + N_ALL + ' Dream Menu interviews.', '/analysis')
      + HEADER + main + FOOTER
      + '<script src="/dmviz.js"></script>\n<script src="/analysis-data.js"></script>\n<script src="/analysis.js"></script>\n'
      '<script src="/trend-public.js"></script>\n<script src="/drinks-new.js"></script>\n<script src="/bench-public.js"></script>\n'
      '<script src="/partner/intel-data.js"></script>\n<script src="/partner/intel.js"></script>\n'
      '<script src="/partner/trend-data.js"></script>\n<script src="/partner/bench-data.js"></script>\n'
      '<script src="/trend-charts.js"></script>\n'
      '<script>(function(){function o(){var t=location.hash&&document.getElementById(location.hash.slice(1));for(var e=t;e;e=e.parentElement)if(e.tagName==="DETAILS")e.open=true;if(t&&t.closest&&t.closest("details"))t.scrollIntoView();}addEventListener("hashchange",o);setTimeout(o,600);})();</script>\n</body>\n</html>\n')
open('analysis.html', 'w', encoding='utf-8').write(an)

# the old partner page now lives inside /analysis
open('intelligence.html', 'w', encoding='utf-8').write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The analysis | Dream Menu</title>'
    '<meta name="robots" content="noindex"><link rel="canonical" href="https://www.dream-menu.com/analysis">'
    '<meta http-equiv="refresh" content="0; url=/analysis#matrix-sec"></head><body><p>Partner intelligence is now part of <a href="/analysis">the analysis</a>.</p></body></html>\n')
print('wrote analysis.html', len(an), '(intelligence.html is a redirect)')
