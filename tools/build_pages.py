#!/usr/bin/env python3
"""Writes the two analysis pages, /analysis (public) and /intelligence (partner), around the
site's shared head, header and footer (taken from insights.html). Run from the repository root:

    python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py

The charts are drawn in the browser by analysis.js and partner/intel.js from the data files
that build_intel.py writes. Section titles are filled from the data, so they stay true after a refresh.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
T = open('insights.html', encoding='utf-8').read()
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


# ------------------------------------------------------------------ /intelligence (partner)
TOC = [('1', 'Executive read', 'read'), ('2', 'Momentum matrix', 'matrix-sec'), ('3', 'How sure we are', 'confidence-sec'),
       ('4', 'Trend wall', 'wall-sec'), ('5', 'Dish heat', 'heat-sec'), ('6', 'Who wants what', 'segments-sec'),
       ('7', 'Opportunity score', 'opportunity-sec'), ('8', 'Operator pulse', 'operators-sec')]
toc = '<ul class="iv-toc">' + ''.join(f'<li><a href="#{a}"><b>{n}</b>{t}</a></li>' for n, t, a in TOC) + '</ul>'
intel_main = f'''<main class="iv-page">
<section class="iv-hero navy"><div class="iv-wrap">
<span class="iv-kick">Partner intelligence</span>
<h1>The market read, in ten minutes</h1>
<p class="lede">Eight views of what Scotland’s food people want, how sure we can be, and where it points: from a one-screen executive read to an opportunity score for every tracked dish and drink. Every chart has a table view and a CSV download.</p>
</div></section>
{sec(1, 'Executive read', 't1', 'The three things to take into this quarter’s planning, then the numbers behind them.', '<div class="kpis" id="x-kpis"></div><div class="sowhat" id="x-sowhat"></div><div class="iv-callout"><svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 4.6V8l2.3 1.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span><b>Next refresh.</b> 11 interviews have come in since the data was cut on 19 October (the latest on 27 October). They join every chart at the next refresh, along with the rest of the fourth quarter.</span></div><div data-fresh="interviews look"></div>', 'read')}
{sec(2, 'Momentum matrix', 't2', 'Each dish placed by how big it is (across) and how fast its share is moving (up or down). Pick a course. Top right is where volume and momentum meet; top left is where the next staples come from.', '<div id="c-matrix"></div>', 'matrix-sec')}
{sec(3, 'How sure we are', 't3', '', '<div id="c-forest"></div>', 'confidence-sec')}
{sec(4, 'Trend wall', 't4', 'Thirty-six small charts on one scale per cell, so the shape of each course reads at a glance. Hover any cell for the quarter-by-quarter numbers.', '<div id="c-wall"></div>', 'wall-sec')}
{sec(5, 'Dish heat', 't5', 'Ten leading dishes per course, coloured against their own average so a small dish that spikes stands out as clearly as a big one.', '<div id="c-heat"></div>', 'heat-sec')}
{sec(6, 'Who wants what', 't6', 'Industry (chefs, operators, front of house), creators (food pages and writers) and enthusiasts answer differently. Plan the range for the customer you are selling to.', '<div id="c-seg"></div>', 'segments-sec')}
{sec(7, 'Opportunity score', 't7', 'One ranking that weighs size, momentum, strength of evidence and how open the field is. <b>Back</b> = rising clearly or scoring 60 and over. <b>Watch</b> = promising, not proven. <b>Review</b> = falling clearly or scoring low and drifting down.', '<div id="c-opp"></div>', 'opportunity-sec')}
{sec(8, 'Operator pulse', 't8', 'What the people buying from suppliers are feeling, and where their response falls short of the pressure. This is where a supplier can help.', '<div id="c-ops"></div>', 'operators-sec')}
<section class="iv-sec" id="method"><div class="iv-wrap prose">
<p class="iv-eyebrow">Method</p>
<h2 class="iv-title" data-short="Method">How these numbers are made</h2>
<ul class="iv-sub" style="max-width:80ch">
<li><b>Shares</b> are of answers coded to a category within each course. Answers coded as Other are left out.</li>
<li><b>Change</b> compares pooled earlier quarters (2025-Q3 and Q4) with pooled recent quarters (2026-Q2 to Q4), in percentage points. A move is <b>clear</b> when a two-proportion z-test gives p &lt; 0.05. With 131 tests, six or seven clear results would be expected by chance alone, so 21 is a real signal, and any single borderline result deserves care.</li>
<li><b>95% ranges</b> use the standard error behind each test, so a range clears zero exactly when the move is clear.</li>
<li><b>Opportunity score</b>: demand (share percentile, 30), momentum (change percentile, 35), evidence (1 − p, 15), room to enter (share of the dish’s venue mentions that go to one venue, doubled and capped, 20), minus 10 where guests also name it in “Bin it”. Weights are a judgement; the table view shows every component so you can re-weight in the CSV.</li>
<li><b>Segments</b> come from each guest’s own description: industry 449, creators 407, enthusiasts 359.</li>
<li>Qualitative fieldwork, not a statistically representative survey of the population.</li>
</ul>
</div></section>
</main>
'''
intel = (head('Partner intelligence | Dream Menu', 'The quarterly market read for Dream Menu partners: momentum, confidence, segments, opportunity scores and the operator pulse.', '/intelligence', robots=True)
         + HEADER + CONF + '\n' + intel_main + FOOTER
         + '<script src="/dmviz.js"></script>\n<script src="/partner/intel-data.js"></script>\n<script src="/partner/intel.js"></script>\n</body>\n</html>\n')
open('intelligence.html', 'w', encoding='utf-8').write(intel)

# ------------------------------------------------------------------ /analysis (public)
an_main = f'''<main class="iv-page">
<section class="iv-hero"><div class="iv-wrap">
<span class="iv-kick">The analysis</span>
<h1>Scotland’s appetite, analysed</h1>
<p class="lede">Three questions the raw counts can’t answer on their own: does each city eat differently, do guests agree with the critics, and how settled is each course? Built from {'{'}interviews{'}'} interviews and the venues guests name.</p>
</div></section>
<section class="iv-sec" id="cities"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">A</span>Every city’s appetite</p><h2 class="iv-title" id="ta" data-short="Every city’s appetite">&nbsp;</h2><p class="iv-sub">An index strips out size, so a city with fewer interviews is compared fairly with Glasgow. Above 100 means a market names the dish more than everyone else does.</p><div class="kpis" id="city-sig"></div><div id="c-cities"></div></div></section>
<section class="iv-sec" id="critics"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">B</span>Guests and critics</p><h2 class="iv-title" id="tb" data-short="Guests and critics">&nbsp;</h2><p class="iv-sub" id="sb"></p><div id="c-critics"></div></div></section>
<section class="iv-sec" id="settled-sec"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">C</span>How settled each course is</p><h2 class="iv-title" id="tc" data-short="How settled each course is">&nbsp;</h2><p class="iv-sub">A settled course is safe ground for a menu; an open one is where a distinctive dish can stand out.</p><div id="c-conc"></div>
<div class="iv-lock"><svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg><span>Partners also see which dishes are rising and falling, how sure each move is, and an opportunity score for every dish. <a href="/intelligence">Partner intelligence</a> · <a href="/for-business">Work with us</a></span></div>
</div></section>
</main>
'''
an_main = an_main.replace('{interviews}', '1,221')
an = (head('The analysis: Scotland’s appetite | Dream Menu', 'How each city eats differently, where guests and critics agree, and how settled each course is: analysis from 1,221 Dream Menu interviews.', '/analysis')
      + HEADER + an_main + FOOTER
      + '<script src="/dmviz.js"></script>\n<script src="/analysis-data.js"></script>\n<script src="/analysis.js"></script>\n</body>\n</html>\n')
open('analysis.html', 'w', encoding='utf-8').write(an)
print('wrote intelligence.html', len(intel), 'analysis.html', len(an))
