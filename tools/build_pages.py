#!/usr/bin/env python3
"""Writes the analysis page /analysis (partner chapters unlock in place after sign-in) around the
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

# ------------------------------------------------------------------ /analysis: one page, partner chapters unlock in place
LOCKSVG = '<svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'
LK = '<svg class="lk" viewBox="0 0 16 16" width="11" height="11" aria-label="Partners" role="img"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'


def chap(n, kicker, title, sub, body, sid, partner=False, preview='', tid='', sub_id=''):
    """One chapter. Partner chapters show a short preview with a sign-in link until partner data loads."""
    t = f'<h2 class="iv-title"{f" id={chr(34)}{tid}{chr(34)}" if tid else ""} data-short="{kicker}">{title}</h2>'
    sp = f'<p class="iv-sub"{f" id={chr(34)}{sub_id}{chr(34)}" if sub_id else ""}>{sub}</p>'
    tag = '<span class="pv-tag">Partners</span>' if partner else ''
    inner = body
    if partner:
        inner = (f'<div class="pv-lock">{LOCKSVG}<p><b>For Dream Menu partners.</b> {preview}</p>'
                 f'<a href="/login?next=/analysis">Partner sign-in</a></div><div class="pv-body">{body}</div>')
    return (f'<section class="iv-sec" id="{sid}"><div class="iv-wrap"><p class="iv-eyebrow"><span class="iv-num">{n}</span>{kicker}{tag}</p>'
            f'{t}{sp}{inner}</div></section>\n')


CH = [  # number, label, anchor, partner
    ('1', 'Headlines', 'read', False), ('2', 'Every city', 'cities', False), ('3', 'Guests and critics', 'critics', False),
    ('4', 'How settled', 'settled-sec', False), ('5', 'What changed', 'changed', False), ('6', 'Converging?', 'converging', False),
    ('7', 'Life cycle', 'life', False), ('8', 'Drinks', 'drinks', False), ('9', 'How we compare', 'compare', False),
    ('10', 'Momentum', 'matrix-sec', True), ('11', 'How sure we are', 'confidence-sec', True), ('12', 'Trend wall', 'wall-sec', True),
    ('13', 'Dish heat', 'heat-sec', True), ('14', 'Next three quarters', 'next', True), ('15', 'Who wants what', 'segments-sec', True),
    ('16', 'Opportunity score', 'opportunity-sec', True), ('17', 'Operator pulse', 'operators-sec', True)]
toc = ('<div class="iv-toc-g"><span>Open to all</span>' + ''.join(f'<a href="#{a}"><b>{n}</b>{t}</a>' for n, t, a, p in CH if not p) + '</div>'
       '<div class="iv-toc-g"><span>Partners</span>' + ''.join(f'<a href="#{a}"><b>{n}</b>{t} {LK}</a>' for n, t, a, p in CH if p) + '</div>')
toc = toc.replace('<div class="iv-toc-g">', '<div class="iv-toc iv-toc-g">')
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


WHO = (f'<div class="who"><div class="dmv-card"><h3>Who answers</h3><p class="who-s">Share of the {_gt:,} guests who answered the dish questions, by how they describe themselves.</p>'
       + _bars([(_GL.get(g['g'], g['g']), 100 * g['n'] / _gt) for g in P['groups']])
       + f'</div><div class="dmv-card"><h3>Where their venues are</h3><p class="who-s">Share of the {_uk:,} UK venue mentions, by nation. {100 * (_all - _uk) / _all:.0f}% of all {_all:,} mentions are outside the UK or not placed in a nation.</p>'
       + _bars([(n, 100 * c / _uk) for n, c in sorted(_nat, key=lambda x: -x[1])])
       + '</div></div><p class="iv-sub" style="max-width:80ch"><b>Read it as:</b> a large panel of food-led people, most of them in Scotland and many working in the trade. It leads the wider public on trends more than it mirrors it, which is why chapter 9 sets the findings against national sources. Age, home city and how often guests eat out are not collected yet.</p>')
main = f"""<main class="iv-page">
<section class="iv-hero navy"><div class="iv-wrap">
<span class="iv-kick">The analysis</span>
<h1>What the UK’s foodies want, and where it’s heading</h1>
<p class="lede">One place for every analysis of {N_ALL} interviews: how each city eats, how guests compare with the critics, how the menu is changing, and how Dream Menu compares with outside sources. Chapters 1 to 9 are open to all. Partners also see chapters 10 to 17, plus extra charts inside chapters 1, 5 to 7 and 9, after signing in. Every chart has a table view and a CSV download.</p>
{toc}
</div></section>
{chap(1, 'Headlines', 'What the data says this quarter', 'Each finding is written from the numbers and rechecked at every refresh. Partners also see the executive read: clear movers, operator confidence and the three things to plan around.', '<div id="th-find"></div><div class="pv-body"><div class="kpis" id="x-kpis"></div><div class="sowhat" id="x-sowhat"></div><h3 class="iv-h3" id="t1"></h3></div>' + CALLOUT + '<div data-fresh="interviews look"></div>', 'read')}
{chap(2, 'Every city’s appetite', '&nbsp;', 'Shares, not counts, so a city with fewer interviews is compared fairly with Glasgow. Each cell is the dish’s share of that market’s mentions, coloured by how far it sits above or below its share everywhere.', '<div class="kpis" id="city-sig"></div><div id="c-cities"></div>', 'cities', tid='ta')}
{chap(3, 'Guests and critics', '&nbsp;', '', '<div id="c-critics"></div>', 'critics', tid='tb', sub_id='sb')}
{chap(4, 'How settled each course is', '&nbsp;', 'A settled course is safe ground for a menu; an open one is where a distinctive dish can stand out.', '<div id="c-conc"></div>', 'settled-sec', tid='tc')}
{chap(5, 'What changed', 'Sides are being rewritten; the rest of the menu is holding' if _most['course'] == 'd' else f"{_most['cl']}s changed most", 'How much of each course’s answers moved to a different food group between late 2025 and the recent quarters, set against what sampling alone would produce. Partners also see where the share went, food group by food group.', '<div id="th-churn"></div>', 'changed')}
{chap(6, 'Converging or spreading out', 'Do guests pile onto the same few favourites?', 'The share of each course’s answers taken by its five most-named dishes, quarter by quarter, with 95% ranges. Partners also see the shape of every course, quarter by quarter.', '<div id="th-conc"></div>', 'converging')}
{chap(7, 'Life cycle and staples', f"{_n_stap} steady staples, and how every course’s dishes are moving", 'How many of each course’s tracked dishes are rising, steady, peaked, recovering or fading, and the staples whose share never really moves. Partners also see every dish named on the life-cycle board and a then-and-now chart.', '<div id="th-life"></div>', 'life')}
{chap(8, 'Drinks, restarted', 'What guests drink, on a clean new series', 'The drink question was split into soft and alcoholic on 23 August 2026, so the old drink trends stopped there. This is the new baseline, built only from the new questions. Movement will be tested once two quarters each hold 100 answers.', '<div id="th-drinks"></div>', 'drinks')}
{chap(9, 'How we compare', 'Dream Menu against outside sources', 'National polls, eating-out data, menu trackers and sales figures, set beside Dream Menu’s own numbers. Outside figures are never mixed into Dream Menu data: they sit alongside it, with their source and date, as a check and a challenge. Partners also see dish and drink comparisons and the operator benchmarks.', '<div id="th-bench"></div>', 'compare')}
{chap(10, 'Momentum matrix', 'Where size and momentum meet', 'Each dish placed by how big it is (across) and how fast its share is moving (up or down). Pick a course. Top right is where volume and momentum meet; top left is where the next staples come from.', '<div id="c-matrix"></div>', 'matrix-sec', True, 'Every tracked dish placed by size and momentum, course by course, so you can see where volume and growth meet.', tid='t2')}
{chap(11, 'How sure we are', 'Which moves are real', '', '<div id="c-forest"></div>', 'confidence-sec', True, 'Every change with its 95% range, so you can tell a real move from noise before acting on it.', tid='t3', sub_id='s3')}
{chap(12, 'Trend wall', 'Every course on one wall', 'Thirty-six small charts on one scale per cell, so the shape of each course reads at a glance. Hover any cell for the quarter-by-quarter numbers.', '<div id="c-wall"></div>', 'wall-sec', True, 'The six biggest food groups in every course, quarter by quarter, on one wall.', tid='t4')}
{chap(13, 'Dish heat', 'Spikes against each dish’s own average', 'Ten leading dishes per course, coloured against their own average so a small dish that spikes stands out as clearly as a big one.', '<div id="c-heat"></div>', 'heat-sec', True, 'Ten leading dishes per course, coloured against their own average so spikes stand out.', tid='t5')}
{chap(14, 'Next three quarters', 'Where the clear movers are heading', 'A damped projection for each clear mover, so a planning range is on the table for range reviews and stock. Projections weigh recent quarters more and flatten over time.', '<div id="th-fan"></div>', 'next', True, 'A three-quarter planning range for every dish and food group that is clearly rising or falling.')}
{chap(15, 'Who wants what', 'How each group of guests differs', 'Industry (chefs, operators, front of house), creators (food pages and writers) and enthusiasts answer differently. Plan the range for the customer you are selling to.', '<div id="c-seg"></div>', 'segments-sec', True, 'How industry, creators and enthusiasts differ on every course.', tid='t6')}
{chap(16, 'Opportunity score', 'A score for every dish and drink', 'One ranking that weighs size, momentum, strength of evidence and how open the field is. <b>Back</b> = rising clearly or scoring 60 and over. <b>Watch</b> = promising, not proven. <b>Review</b> = falling clearly or scoring low and drifting down.', '<div id="c-opp"></div>', 'opportunity-sec', True, 'A score out of 10 for every tracked dish and drink: back it, watch it or review it.', tid='t7')}
{chap(17, 'Operator pulse', 'How operators feel, and where they need help', 'What the people buying from suppliers are feeling, and where their response falls short of the pressure. This is where a supplier can help.', '<div id="c-ops"></div>', 'operators-sec', True, 'What 55 operators say about costs, confidence and the gaps a supplier can fill.', tid='t8')}
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
      '<script src="/trend-charts.js"></script>\n</body>\n</html>\n')
open('analysis.html', 'w', encoding='utf-8').write(an)

# the old partner page now lives inside /analysis
open('intelligence.html', 'w', encoding='utf-8').write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The analysis | Dream Menu</title>'
    '<meta name="robots" content="noindex"><link rel="canonical" href="https://www.dream-menu.com/analysis">'
    '<meta http-equiv="refresh" content="0; url=/analysis#matrix-sec"></head><body><p>Partner intelligence is now part of <a href="/analysis">the analysis</a>.</p></body></html>\n')
print('wrote analysis.html', len(an), '(intelligence.html is a redirect)')
