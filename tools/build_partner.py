#!/usr/bin/env python3
"""The partner area (/partner) and the "ways to work with us" block on /for-business.

Run from the repository root after build_intel.py (it reads partner-data.js and partner/intel-data.js):
  python3 tools/build_partner.py

/partner is organised around what partner teams do, not the contract:
  1. This quarter: the headlines written from the data (clear movers, scores to back, operator mood)
  2. Pick the tool for the job: sales, buying and range, marketing, strategy
  3. Your partnership this term: dates and what is due, worked out from today's date
  4. Data downloads (built live in the browser by partner/downloads.js)
  5. Terms of use and sponsorship, folded away
/for-business gets one block that routes each kind of visitor to the offer that fits them.
"""
import datetime as dt, html, json, os, re

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
  <p class="ph-actions"><a class="cta" href="/briefing">Open the full briefing</a> <a class="ph-ghost" href="/onepager">Print the one-pager for a sales meeting</a></p>
</div></section>
'''

# ---------------------------------------------------------------- 2. tools by job
JOBS = [
    ('Sales', 'Conversations with kitchens', [
        ('/onepager', 'One-pager', 'The quarter on one printable page'),
        ('/map', 'Venue map with trend lines', 'Which venues guests name in a patch, and where demand is moving'),
        ('/briefing#courses', 'Course by course', 'What to talk about with each kind of kitchen'),
    ]),
    ('Buying and range', 'What to stock next', [
        ('/analysis#opportunity-sec', 'Opportunity score', 'Back, watch or review: a score for every dish and drink'),
        ('/analysis#next', 'Next three quarters', 'A planning range for every clear mover'),
        ('/analysis#category-sec', 'Category scorecard', 'Every food group with a call: grow, defend, trim, core or niche'),
        ('/analysis#life', 'Life cycle', 'What is growing, mature or tiring'),
        ('/analysis#drinks', 'Drinks', 'The new drinks baseline since August'),
    ]),
    ('Marketing', 'Stories and campaigns', [
        ('/#debates', 'Debates and guilty pleasures', 'Irn-Bru or Coke, trends to bin, comfort food'),
        ('/analysis#compare', 'How we compare', 'Dream Menu against national polls and market data'),
        ('/specials', 'Themed rounds', 'Dream Cocktail, Sandwich and Fringe'),
    ]),
    ('Strategy', 'Management and planning', [
        ('/analysis#segments-sec', 'Who wants what', 'Industry, creators and enthusiasts compared'),
        ('/analysis#operators-sec', 'Operator pulse', 'Costs, confidence and the gaps a supplier can fill'),
        ('/report', 'Report 2026', 'The Hospitality Intelligence Report'),
        ('/case-studies', 'Insight Series', 'Fifteen deep-dive reports'),
    ]),
]
TOOLS = ('<section class="ph-sec ph-alt"><div class="wrap"><div class="ph-head"><h2>Pick the tool for the job</h2>'
         '<p>Everything in the partnership, sorted by what you are trying to do. Every chart downloads as CSV.</p></div><div class="ph-jobs">'
         + ''.join(f'<div class="ph-job"><h3>{E(t)}</h3><p class="ph-sub">{E(s)}</p><ul>'
                   + ''.join(f'<li><a href="{u}"><b>{E(a)}</b><span>{E(d)}</span>{ARROW}</a></li>' for u, a, d in items) + '</ul></div>' for t, s, items in JOBS)
         + '</div></div></section>\n')

# ---------------------------------------------------------------- 3. the term, from today's date
qn = (TODAY.month - 1) // 3
q_start = dt.date(TODAY.year, qn * 3 + 1, 1)
q_end = (dt.date(TODAY.year + (qn == 3), (qn * 3 + 3) % 12 + 1, 1) - dt.timedelta(days=1))
nq_start = q_end + dt.timedelta(days=1)
qlab = lambda d: f'Q{(d.month - 1) // 3 + 1} {d.year}'
steps = [
    (START, 'Partnership started', 'Partner area, map trend lines and data downloads opened.', 'done'),
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
old = open('partner.html', encoding='utf-8').read()
table = re.search(r'<div class="tablewrap"><table>.*?</table></div>', old, re.S).group(0)
mkt_rows = open('partner/data/market_activity_by_quarter.csv', encoding='utf-8-sig').read().count('\n') - 1
table = re.sub(r'(guide awards\.</td><td class="num">)[\d,]+', rf'\g<1>{M["venues"]:,}', table)
table = re.sub(r'(plus counts and shares\.</td><td class="num">)[\d,]+', rf'\g<1>{sum(len(v) for v in C["m"].values()):,}', table)
table = re.sub(r'(which cities and neighbourhoods are gaining momentum\.</td><td class="num">)[\d,]+', rf'\g<1>{mkt_rows:,}', table)
DATA = (f'<section class="ph-sec ph-alt" id="data"><div class="wrap"><div class="ph-head"><h2>Data downloads</h2>'
        f'<p>CSV files for Excel or any data tool, built from the live data each time you download: interviews to {LAST}. '
        'Aggregated and anonymised: no names, contact details or quotes from individual guests.</p></div>' + table +
        '<p class="note">Shares exclude answers coded as Other. Locations: "address confirmed" is a verified address or postcode; "approximate" is placed on the right street, '
        'neighbourhood or town; "not yet pinned" is counted in its city or country.</p></div></section>\n')

# ---------------------------------------------------------------- 5. terms, folded
terms = re.search(r'<div class="card"><h3>Terms of use</h3>(.*?)</div>\s*<div class="card"><h3>Sponsorship on Dream Menu output</h3>(.*?)</div>\s*</div></div></section>', old, re.S)
if terms:
    t_terms, t_spon = terms.group(1), terms.group(2)
else:   # already rebuilt: read back from the folded block
    t_terms = re.search(r'<!--terms-->(.*?)<!--/terms-->', old, re.S).group(1)
    t_spon = re.search(r'<!--spon-->(.*?)<!--/spon-->', old, re.S).group(1)
FOLD = ('<section class="ph-sec"><div class="wrap"><details class="ph-fold"><summary>Terms of use and sponsorship</summary><div class="grid">'
        f'<div class="card"><h3>Terms of use</h3><!--terms-->{t_terms}<!--/terms--></div>'
        f'<div class="card"><h3>Sponsorship on Dream Menu output</h3><!--spon-->{t_spon}<!--/spon--></div></div></details></div></section>\n')

conf = re.search(r'<div class="confidential">.*?</div></div>', old, re.S).group(0)
HERO = f'''<section class="navyband"><div class="wrap">
  <div class="eyebrow">Dunns Food &amp; Drinks · Partner area</div>
  <h1>What is moving, and <em>what to do about it</em></h1>
  <p class="lede">Market intelligence from {N_ALL} interviews with chefs, operators, suppliers and food lovers, to {LAST}. Start with this quarter, then pick the tool for the job.</p>
</div></section>
'''
main = ('<main>\n' + conf + '\n' + HERO + QUARTER.replace('<section class="ph-sec">', '<section class="ph-sec" id="q">', 1)
        + TOOLS.replace('<section class="ph-sec ph-alt">', '<section class="ph-sec ph-alt" id="tools">', 1)
        + TERM.replace('<section class="ph-sec">', '<section class="ph-sec" id="term">', 1) + DATA + FOLD + '</main>')
new = re.sub(r'<main>.*?</main>', lambda m: main, old, count=1, flags=re.S)
new = new.replace('<title>Partner area | Dream Menu</title>', '<title>Partner area | Dream Menu</title>')
open('partner.html', 'w', encoding='utf-8').write(new)

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
open('for-business.html', 'w', encoding='utf-8').write(fb)
print('partner.html and for-business.html written;', len(up), 'up,', len(dn), 'down; next review after', q_end)
