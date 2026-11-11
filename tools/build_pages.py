#!/usr/bin/env python3
"""Writes the two analysis pages, /analysis (public) and /intelligence (partner), around the
site's shared head, header and footer (taken from insights.html). Run from the repository root:

    python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py

The charts are drawn in the browser by analysis.js and partner/intel.js from the data files
that build_intel.py writes. Section titles are filled from the data, so they stay true after a refresh.
"""
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

# ------------------------------------------------------------------ /intelligence (partner)
TOC = [('1', 'Executive read', 'read'), ('2', 'Momentum matrix', 'matrix-sec'), ('3', 'How sure we are', 'confidence-sec'),
       ('4', 'Trend wall', 'wall-sec'), ('5', 'Dish heat', 'heat-sec'), ('6', 'Who wants what', 'segments-sec'),
       ('7', 'Opportunity score', 'opportunity-sec'), ('8', 'Operator pulse', 'operators-sec'),
       ('9', 'What changed', 'tr-changed'), ('10', 'Life cycle', 'tr-life'), ('11', 'Menu shape', 'tr-shape'), ('12', 'Next three quarters', 'tr-next'), ('13', 'Staples', 'tr-stap')]
toc = '<ul class="iv-toc">' + ''.join(f'<li><a href="#{a}"><b>{n}</b>{t}</a></li>' for n, t, a in TOC) + '</ul>'
intel_main = f'''<main class="iv-page">
<section class="iv-hero navy"><div class="iv-wrap">
<span class="iv-kick">Partner intelligence</span>
<h1>The market read, in ten minutes</h1>
<p class="lede">Thirteen views of what the UK’s foodies want, how sure we can be, and where it points: from a one-screen executive read to an opportunity score for every tracked dish and drink. Every chart has a table view and a CSV download.</p>
</div></section>
{sec(1, 'Executive read', 't1', 'The three things to take into this quarter’s planning, then the numbers behind them.', '<div class="kpis" id="x-kpis"></div><div class="sowhat" id="x-sowhat"></div><div class="iv-callout"><svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 4.6V8l2.3 1.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span><b>Data to ' + LAST_H + '.</b> Every chart includes all ' + N_ALL + ' interviews received to that date. Quarters with fewer than ' + str(P['min_n']) + ' answers, including the fourth quarter so far, are shown faded: read them as an early signal.</span></div><div data-fresh="interviews look"></div>', 'read')}
{sec(2, 'Momentum matrix', 't2', 'Each dish placed by how big it is (across) and how fast its share is moving (up or down). Pick a course. Top right is where volume and momentum meet; top left is where the next staples come from.', '<div id="c-matrix"></div>', 'matrix-sec')}
{sec(3, 'How sure we are', 't3', '', '<div id="c-forest"></div>', 'confidence-sec')}
{sec(4, 'Trend wall', 't4', 'Thirty-six small charts on one scale per cell, so the shape of each course reads at a glance. Hover any cell for the quarter-by-quarter numbers.', '<div id="c-wall"></div>', 'wall-sec')}
{sec(5, 'Dish heat', 't5', 'Ten leading dishes per course, coloured against their own average so a small dish that spikes stands out as clearly as a big one.', '<div id="c-heat"></div>', 'heat-sec')}
{sec(6, 'Who wants what', 't6', 'Industry (chefs, operators, front of house), creators (food pages and writers) and enthusiasts answer differently. Plan the range for the customer you are selling to.', '<div id="c-seg"></div>', 'segments-sec')}
{sec(7, 'Opportunity score', 't7', 'One ranking that weighs size, momentum, strength of evidence and how open the field is. <b>Back</b> = rising clearly or scoring 60 and over. <b>Watch</b> = promising, not proven. <b>Review</b> = falling clearly or scoring low and drifting down.', '<div id="c-opp"></div>', 'opportunity-sec')}
{sec(8, 'Operator pulse', 't8', 'What the people buying from suppliers are feeling, and where their response falls short of the pressure. This is where a supplier can help.', '<div id="c-ops"></div>', 'operators-sec')}
{sect(9, 'What changed', f"{_most['cl']}s moved most: {_most['obs']}% of answers changed food group, against {_most['chance']}% from chance", 'The menu over time, course by course. Each finding below is written from the numbers and rechecked at every refresh; the charts underneath show how much each course really moved and where the share went.', '<div id="trx-find"></div><div id="trx-churn"></div>', 'tr-changed')}
{sect(10, 'Life cycle', 'What is growing, what is mature and what is tiring', 'Every tracked dish placed in one of six stages from the shape of its share over six quarters. Rising and fading need a clear earlier-to-recent move; peaked and recovering need a clear swing between quarters.', '<div id="trx-life"></div>', 'tr-life')}
{sect(11, 'Menu shape', 'How each course is made up, quarter by quarter', 'The five biggest food groups in each course as a share of every coded answer, and whether guests are converging on a few favourites or spreading out.', '<div id="trx-mix"></div>', 'tr-shape')}
{sect(12, 'Next three quarters', 'Where the clear movers are heading', 'A damped projection for each clear mover, so a planning range is on the table for range reviews and stock. Projections weigh recent quarters more and flatten over time.', '<div id="trx-fan"></div>', 'tr-next')}
{sect(13, 'Staples', 'The dishes that hold their share, every quarter', 'The quiet strength of the menu: dishes big enough to matter whose share stays inside sampling noise from one full quarter to the next.', '<div id="trx-staples"></div>', 'tr-stap')}
<section class="iv-sec" id="method"><div class="iv-wrap prose">
<p class="iv-eyebrow">Method</p>
<h2 class="iv-title" data-short="Method">How these numbers are made</h2>
<ul class="iv-sub" style="max-width:80ch">
<li><b>Shares</b> are of answers coded to a category within each course. Answers coded as Other are left out.</li>
<li><b>Change</b> compares pooled earlier quarters (2025-Q3 and Q4) with pooled recent quarters (2026-Q2 to Q4), in percentage points. A move is <b>clear</b> when a two-proportion z-test gives p &lt; 0.05. With 131 tests, six or seven clear results would be expected by chance alone, so 21 is a real signal, and any single borderline result deserves care.</li>
<li><b>95% ranges</b> use the standard error behind each test, so a range clears zero exactly when the move is clear.</li>
<li><b>Opportunity score</b>: demand (share percentile, 30), momentum (change percentile, 35), evidence (1 − p, 15), room to enter (share of the dish’s venue mentions that go to one venue, doubled and capped, 20), minus 10 where guests also name it in “Bin it”. Weights are a judgement; the table view shows every component so you can re-weight in the CSV.</li>
<li><b>Segments</b> come from each guest’s own description: industry 449, creators 407, enthusiasts 359.</li>
<li><b>Menu over time</b> (sections 9 to 13, food courses only): churn is half the sum of absolute changes in food-group share, earlier to recent, compared with 1,500 simulated reruns in which nothing changed and only sampling varied. Life-cycle stages use z-tests between quarters with 100+ answers (peaked: high in a middle quarter, clearly above the latest; recovering: the reverse) and a chi-square test for steadiness (p &gt; 0.5, dish above the course median). Projections are a recency-weighted, damped trend with a planning range. Drink questions changed on 23 August 2026, so drinks are left out.</li>
<li>Qualitative fieldwork, not a statistically representative survey of the population.</li>
</ul>
</div></section>
</main>
'''
intel = (head('Partner intelligence | Dream Menu', 'The quarterly market read for Dream Menu partners: momentum, confidence, segments, opportunity scores and the operator pulse.', '/intelligence', robots=True)
         + HEADER + CONF + '\n' + intel_main + FOOTER
         + '<script src="/dmviz.js"></script>\n<script src="/partner/intel-data.js"></script>\n<script src="/partner/intel.js"></script>\n<script src="/partner/trend-data.js"></script>\n<script src="/trend-charts.js"></script>\n</body>\n</html>\n')
open('intelligence.html', 'w', encoding='utf-8').write(intel)

# ------------------------------------------------------------------ /analysis (public)
LOCK = '''<div class="iv-lock"><svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg><span>Partners also see which dishes are rising, fading or past their peak, where the share went, the shape of each course by quarter, projections for every clear mover, how sure each move is, and an opportunity score for every dish. <a href="/intelligence">Partner intelligence</a> · <a href="/for-business">Work with us</a></span></div>
'''
an_main = f'''<main class="iv-page">
<section class="iv-hero"><div class="iv-wrap">
<span class="iv-kick">The analysis</span>
<h1>Every market’s appetite, analysed</h1>
<p class="lede">Six questions the raw counts can’t answer on their own: does each city eat differently, do guests agree with the critics, how settled is each course, how much has each course changed, are guests converging on favourites, and which dishes are the steady staples? Built from {'{'}interviews{'}'} interviews and the venues guests name.</p>
</div></section>
<section class="iv-sec" id="cities"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">A</span>Every city’s appetite</p><h2 class="iv-title" id="ta" data-short="Every city’s appetite">&nbsp;</h2><p class="iv-sub">Shares, not counts, so a city with fewer interviews is compared fairly with Glasgow. Each cell is the dish’s share of that market’s mentions, coloured by how far it sits above or below its share everywhere.</p><div class="kpis" id="city-sig"></div><div id="c-cities"></div></div></section>
<section class="iv-sec" id="critics"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">B</span>Guests and critics</p><h2 class="iv-title" id="tb" data-short="Guests and critics">&nbsp;</h2><p class="iv-sub" id="sb"></p><div id="c-critics"></div></div></section>
<section class="iv-sec" id="settled-sec"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">C</span>How settled each course is</p><h2 class="iv-title" id="tc" data-short="How settled each course is">&nbsp;</h2><p class="iv-sub">A settled course is safe ground for a menu; an open one is where a distinctive dish can stand out.</p><div id="c-conc"></div>
</div></section>
{sect('D', 'How much each course changed', 'Sides are being rewritten; the rest of the menu is holding' if _most['course'] == 'd' else f"{_most['cl']}s changed most", 'How much of each course’s answers moved to a different food group between late 2025 and the recent quarters, set against what sampling alone would produce. Course level only.', '<div id="trp-find"></div><div id="trp-churn"></div>', 'trp-changed-sec')}
{sect('E', 'Converging or spreading out', 'Do guests pile onto the same few favourites?', 'The share of each course’s answers taken by its five most-named dishes, quarter by quarter, with 95% ranges.', '<div id="trp-conc"></div>', 'trp-conc-sec')}
{sect('F', 'Life cycle and staples', f"{_n_stap} steady staples, and how every course’s dishes are moving", 'How many of each course’s tracked dishes are rising, steady, peaked, recovering or fading, and the staples whose share never really moves.', '<div id="trp-life"></div>' + LOCK, 'trp-life-sec')}
</main>
'''
an_main = an_main.replace('{interviews}', N_ALL)
an = (head('The analysis: every market’s appetite | Dream Menu', 'How each city eats differently, where guests and critics agree, and how settled each course is: analysis from ' + N_ALL + ' Dream Menu interviews.', '/analysis')
      + HEADER + an_main + FOOTER
      + '<script src="/dmviz.js"></script>\n<script src="/analysis-data.js"></script>\n<script src="/analysis.js"></script>\n<script src="/trend-public.js"></script>\n<script src="/trend-charts.js"></script>\n</body>\n</html>\n')
open('analysis.html', 'w', encoding='utf-8').write(an)
print('wrote intelligence.html', len(intel), 'analysis.html', len(an))
