#!/usr/bin/env python3
"""The partner part of /analysis and the "ways to work with us" block on /for-business.

Run from the repository root after build_intel.py (it reads partner-data.js and partner/intel-data.js):
  python3 tools/build_partner.py

Since 13 Nov 2026 there is no separate partner area: the analysis IS the partner product. Partners sign in
and the same page grows a partner briefing. This script writes partner/hub.js (behind sign-in), which
fills two slots on /analysis:
  top:    confidential line and This quarter (clear movers, scores to back, operator mood)
  bottom: data downloads, the partnership this term, terms of use and sponsorship (folded)
The scorecard, scores, confidence and segments in between are drawn by partner/intel.js and trend-charts.js.
Source blocks (download table, terms, confidential line) live in tools/data/partner-static.html.
partner.html is a redirect to /analysis#partner.
/for-business gets one block that routes each kind of visitor to the offer that fits them.
"""
import datetime as dt, html, json, os, re
import benchlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
E = html.escape


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
I = load('partner/intel-data.js', 'DM_INTEL')
M = load('dm-data.js', 'DM')['meta']
C = load('dm-cat.js', 'DMC')
TODAY = dt.date.today()
N_ALL = f"{P['n_all']:,}"


def hdate(d):
    return d.strftime('%-d %B %Y')


LAST = hdate(dt.date.fromisoformat(P['last']))
START, END = dt.date(2026, 10, 1), dt.date(2027, 3, 31)
CONTACT = 'contact.dreammenu@gmail.com'
ASK = ('mailto:' + CONTACT + '?subject=Dunns%20commissioned%20questions&amp;body=Question%201:%0D%0A%0D%0AWhich%20department%20is%20asking:'
       '%0D%0A%0D%0AQuestion%202:%0D%0A%0D%0AWhich%20department%20is%20asking:%0D%0A')
ARROW = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def pts(x):
    return ('+' if x > 0 else '−') + f'{abs(x):.1f} pts'


# ---------------------------------------------------------------- 1. this quarter
mv = P['movers']
up = sorted([m for m in mv if m['move'] > 0], key=lambda m: -m['move'])
dn = sorted([m for m in mv if m['move'] < 0], key=lambda m: m['move'])
back = [o for o in I['opp'] if o['tier'] == 'Back'][:3]
ops = I['ops']


def mlist(rows):
    return ''.join(f'<li><b>{E(r["l"])}</b> <span>{E(r["course"].lower())}</span><em>{pts(r["move"])}</em></li>' for r in rows[:4])


QUARTER = f'''<section class="ph-sec"><div class="wrap">
  <div class="ph-head"><h2>This quarter</h2><p>Written from the data to {LAST}. Only moves that pass a significance test are listed.</p></div>
  <div class="ph-q">
    <div class="ph-tile up"><h3>Rising clearly <small>{len(up)}</small></h3><ul>{mlist(up)}</ul></div>
    <div class="ph-tile dn"><h3>Falling clearly <small>{len(dn)}</small></h3><ul>{mlist(dn)}</ul></div>
    <div class="ph-tile"><h3>Top scores to back</h3><ul>{''.join(f'<li><b>{E(o["l"])}</b> <span>{E(o["cl"].lower())}</span><em>{o["score"] / 10:.1f}/10</em></li>' for o in back)}</ul></div>
    <div class="ph-tile"><h3>How operators feel</h3><ul><li><b>Confidence, next 12 months</b><em>{ops["conf12"]:.1f}/10</em></li>
      <li><b>See supplier prices rising</b><em>{ops["rising"]}%</em></li>
      <li><b>Biggest pressure</b><em>{E(ops["pressures"][0][0].split("/")[0].lower())}</em></li></ul></div>
  </div>
  <p class="ph-actions"><a class="cta" href="/onepager">Print the one-pager for a sales meeting</a> <a class="ph-ghost" href="#data">Download the data</a></p>
</div></section>
'''

# ---------------------------------------------------------------- 3. the term, from today's date
qn = (TODAY.month - 1) // 3
q_start = dt.date(TODAY.year, qn * 3 + 1, 1)
q_end = (dt.date(TODAY.year + (qn == 3), (qn * 3 + 3) % 12 + 1, 1) - dt.timedelta(days=1))
nq_start = q_end + dt.timedelta(days=1)
qlab = lambda d: f'Q{(d.month - 1) // 3 + 1} {d.year}'
steps = [
    (START, 'Partnership started', 'Partner briefing, map trend lines and data downloads opened.', 'done'),
    (TODAY, f'Now: {qlab(TODAY)} fieldwork', f'Interviews to {LAST} are already in every page. The site refreshes every Monday.', 'now'),
    (q_end + dt.timedelta(days=1), f'{qlab(q_start)} review and presentation', 'The written Quarterly Industry Insight Review and a presentation to management and sales teams, after the quarter closes.', 'next'),
    (nq_start + dt.timedelta(days=13), f'Questions for {qlab(nq_start)}', 'Send up to two commissioned questions from any department. Without them, Dream Menu sets the scope from the previous quarter.', 'next'),
    (END, 'Initial term ends', 'The review of the final quarter follows. Reviews already delivered can be kept for internal reference.', 'next'),
]
when = {0: lambda d: hdate(d), 1: lambda d: 'Today', 2: lambda d: 'After ' + hdate(q_end), 3: lambda d: 'By ' + hdate(d), 4: lambda d: hdate(d)}
TERM = ('<section class="ph-sec"><div class="wrap ph-term"><div><div class="ph-head"><h2>Your partnership this term</h2>'
        f'<p>{hdate(START)} to {hdate(END)}. What has happened and what is due next.</p></div><ol class="ph-time">'
        + ''.join(f'<li class="{c}"><span class="ph-when">{when[i](d)}</span><b>{E(t)}</b><span>{E(x)}</span></li>' for i, (d, t, x, c) in enumerate(steps))
        + f'</ol></div><aside class="ph-ask"><h3>Ask the panel a question</h3><p>Up to two questions a quarter, placed into live interviews and reported in the next review.</p>'
        f'<a class="cta" href="{ASK}">Send your questions</a><p class="ph-small">Or a new themed round, or an extra cut of the data: Gordon Best, '
        f'<a href="mailto:{CONTACT}">{CONTACT}</a>.</p></aside></div></section>\n')

# ---------------------------------------------------------------- 4. downloads (keep the table the download script binds to)
SRC = open('tools/data/partner-static.html', encoding='utf-8').read()
blk = lambda k: re.search(rf'<!--{k}-->(.*?)<!--/{k}-->', SRC, re.S).group(1)
table = blk('table')
mkt_rows = open('partner/data/market_activity_by_quarter.csv', encoding='utf-8-sig').read().count('\n') - 1
table = re.sub(r'(guide awards\.</td><td class="num">)[\d,]+', rf'\g<1>{M.get("on_map", M["venues"]):,}', table)   # the extract holds every place on the map
table = re.sub(r'(plus counts and shares\.</td><td class="num">)[\d,]+', rf'\g<1>{sum(len(v) for v in C["m"].values()):,}', table)
table = re.sub(r'(which cities and neighbourhoods are gaining momentum\.</td><td class="num">)[\d,]+', rf'\g<1>{mkt_rows:,}', table)
DATA = (f'<section class="ph-sec ph-alt" id="data"><div class="wrap"><div class="ph-head"><h2>Data downloads</h2>'
        f'<p>CSV files for Excel or any data tool, built from the live data each time you download: interviews to {LAST}. '
        'Aggregated and anonymised: no names, contact details or quotes from individual guests.</p></div>' + table +
        '<p class="note">Shares exclude answers coded as Other. Locations: "address confirmed" is a verified address or postcode; "approximate" is placed on the right street, '
        'neighbourhood or town; "not yet pinned" is counted in its city or country.</p></div></section>\n')

# ---------------------------------------------------------------- 5. terms, folded
t_terms, t_spon = blk('terms'), blk('spon')
FOLD = ('<section class="ph-sec"><div class="wrap"><details class="ph-fold"><summary>Terms of use and sponsorship</summary><div class="grid">'
        f'<div class="card"><h3>Terms of use</h3><!--terms-->{t_terms}<!--/terms--></div>'
        f'<div class="card"><h3>Sponsorship on Dream Menu output</h3><!--spon-->{t_spon}<!--/spon--></div></div></details></div></section>\n')

conf = blk('conf')
TOP = conf + '\n' + QUARTER.replace('<section class="ph-sec">', '<section class="ph-sec" id="p-quarter">', 1).replace('<h2>This quarter</h2>', '<h2 data-short="This quarter">This quarter, for partners</h2>', 1)
# formerly on /briefing (retired 13 Nov 2026): drawn by partner/render.js from partner/briefing-extra.js
TOP += ('<section class="ph-sec ph-alt" id="changed-since"><div class="wrap"><div class="ph-head"><h2 data-short="Since last time">What changed since the last update</h2>'
        '<p>Movers that are new, no longer clear, or still clear against the last saved snapshot.</p></div><div id="bf-changes"><p class="note">Loading.</p></div></div></section>\n'
        '<section class="ph-sec" id="ranges"><div class="wrap"><div class="ph-head"><h2 data-short="By Dunns range">By Dunns range</h2>'
        '<p>Food groups rolled up into supplier ranges, so each trend reads as a range call. The grouping is Dream Menu&rsquo;s and will be matched to Dunns&rsquo; own category list.</p></div>'
        '<div id="bf-ranges"><p class="note">Loading.</p></div></div></section>\n')
BOTTOM = (DATA + TERM.replace('<section class="ph-sec">', '<section class="ph-sec" id="term">', 1)
          + FOLD.replace('<section class="ph-sec">', '<section class="ph-sec" id="terms">', 1))
HUB = ('/* Generated by tools/build_partner.py. Partner only (behind sign-in): fills the partner slots on /analysis. */\n'
       'window.DM_HUB=' + json.dumps(dict(top=TOP, bottom=BOTTOM), ensure_ascii=False) + ';\n'
       '(function(){var H=window.DM_HUB;[["p-hub-top",H.top],["p-hub-bottom",H.bottom]].forEach(function(x){var el=document.getElementById(x[0]);if(el)el.innerHTML=x[1]});})();\n')
open('partner/hub.js', 'w', encoding='utf-8').write(HUB)

# retired pages: each is a redirect, so old links and bookmarks still work
def _stub(fn, title, to, msg):
    open(fn, 'w', encoding='utf-8').write(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title} | Dream Menu</title>'
        f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={to}"><script>location.replace("{to}")</script></head>'
        f'<body><p>{msg} <a href="{to}">Continue</a>.</p></body></html>\n')
_stub('briefing.html', 'Partner briefing', '/analysis#partner', 'The partner briefing is now part of the analysis.')
_stub('explore.html', 'Find your way', '/#pick', 'Pick what you are interested in on the home page.')
_stub('awards.html', 'Award winners', '/map', 'Award winners are a layer on the venue map.')
# the old partner area now lives inside /analysis
open('partner.html', 'w', encoding='utf-8').write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Partner briefing | Dream Menu</title>'
    '<meta name="robots" content="noindex"><link rel="canonical" href="https://www.dream-menu.com/analysis">'
    '<meta http-equiv="refresh" content="0; url=/analysis#partner"><script>location.replace("/analysis"+(location.hash||"#partner"))</script></head>'
    '<body><p>The partner area is now part of <a href="/analysis#partner">the analysis</a>.</p></body></html>\n')

# ---------------------------------------------------------------- /for-business: route each visitor to the right offer
ROUTES = [
    ('Suppliers, distributors and brands', 'A partnership', 'What is rising and falling each quarter, a briefing for your sales team, the map with trend lines and the data behind it, plus questions you put to the panel.',
     [('/analysis', 'See the open analysis'), ('#work', 'Talk about a partnership')]),
    ('Investors, developers and consultants', 'Commissioned reports', 'Fifteen Insight Series reports on demand, sites, neighbourhoods and concepts, or a report built around your own question.',
     [('/case-studies/guests-and-critics', 'Read the free sample'), ('/case-studies', 'See the reports')]),
    ('Restaurants, bars and cafés', 'Tools and a check-up', 'The free operator toolkit and badge, and the Restaurant MOT: a four-week independent check of one venue against what its guests say.',
     [('/operators', 'Open the toolkit'), ('/restaurant-mot', 'How the MOT works')]),
    ('Press and researchers', 'Figures to quote', 'Headline numbers, the method and how to credit Dream Menu, all free to use with a credit.',
     [('/press', 'Open the press kit'), ('/how-it-works', 'How it works')]),
]
FB = ('<!--fb-routes--><section><div class="wrap">\n  <h2 id="get">Ways to work with us</h2>\n  <p class="lede" style="margin-bottom:16px">Pick the line that describes you.</p>\n  <div class="fb-routes">'
      + ''.join(f'<div class="card fb-route"><div class="eyebrow">{E(w)}</div><h3>{E(o)}</h3><p>{E(d)}</p><p class="fb-links">'
                + ' '.join(f'<a class="go" href="{u}">{E(t)}</a>' for u, t in links) + '</p></div>' for w, o, d, links in ROUTES)
      + '</div>\n</div></section><!--/fb-routes-->')
fb = open('for-business.html', encoding='utf-8').read()
if '<!--fb-routes-->' in fb:
    fb = re.sub(r'<!--fb-routes-->.*?<!--/fb-routes-->', lambda m: FB, fb, count=1, flags=re.S)
else:
    fb = re.sub(r'<section><div class="wrap">\s*<h2 id="get">What partners get</h2>.*?</div></section>', lambda m: FB, fb, count=1, flags=re.S)
fb = fb.replace('<div class="eyebrow">For suppliers, distributors and venues</div>', '<div class="eyebrow">For business</div>')
BENCH = ('<!--fb-bench--><section><div class="wrap">\n  <h2 id="checked">Checked against the wider market</h2>\n'
         f'  <p class="lede" style="margin-bottom:14px">{benchlib.headline()}. Some of the findings that agree with national research:</p>\n'
         + benchlib.agree_list(6) + '\n  <p class="note"><a href="/analysis#compare">Every comparison, with sources and the local insights</a></p>\n</div></section><!--/fb-bench-->')
if '<!--fb-bench-->' in fb:
    fb = re.sub(r'<!--fb-bench-->.*?<!--/fb-bench-->', lambda m: BENCH, fb, count=1, flags=re.S)
else:
    fb = fb.replace('<!--/fb-routes-->', '<!--/fb-routes-->\n' + BENCH, 1)
open('for-business.html', 'w', encoding='utf-8').write(fb)
print('partner/hub.js, partner.html (redirect) and for-business.html written;', len(up), 'up,', len(dn), 'down; next review after', q_end)
