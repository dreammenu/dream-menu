#!/usr/bin/env python3
"""Writes /reports: one library page for every dated publication (the 2026 report, the Insight Series,
State of the Menu), kept apart from the live analysis at /analysis.

Run from the repository root after build_case_studies.py and build_quarterly.py, before build_nav.py:
    python3 tools/build_reports.py

The page shell (head, header, footer) is copied from explore.html; build_nav.py then refreshes the
header and footer. Dates are read from the pages themselves, so they stay true after a rebuild.
"""
import glob, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
E = lambda x: html.escape(x, quote=True)


def text(fn):
    s = open(fn, encoding='utf-8').read()
    return s


def data_to(fn):
    m = re.search(r'[Dd]ata to (\d{1,2} [A-Z][a-z]+ 20\d\d)', text(fn))
    return m.group(1) if m else ''


T = text('explore.html')
head = T[:T.index('</head>')]
head = re.sub(r'<title>.*?</title>', '<title>Reports | Dream Menu</title>', head)
DESC = 'Every Dream Menu publication in one place, each fixed at its data date: the Hospitality Intelligence Report 2026, the Insight Series and State of the Menu.'
head = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + DESC, head)
head = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + DESC, head)
head = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>Reports | Dream Menu', head)
head = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>https://www.dream-menu.com/reports', head)
head = re.sub(r'<link rel="stylesheet" href="/explore[^"]*">\n?', '', head)
if '/pages.css' not in head:
    head += '<link rel="stylesheet" href="/pages.css">\n'
HEADER = T[T.index('<body'):T.index('<main')]
FOOTER = T[T.index('</main>') + len('</main>'):]

# ---- the three collections
rep_date = data_to('report.html') or '9 October 2026'
REPORT = [('/report', 'Overview and seven key findings', 'Open to everyone', False),
          ('/report/operator-pulse', 'Operator pulse: what 54 operators said about costs and confidence', '', True),
          ('/report/glasgow', "Glasgow's dining landscape: neighbourhoods, corridors and case studies", '', True),
          ('/report/whats-on-the-menu', "What's on the menu: demand course by course, and trend fatigue", '', True),
          ('/report/opportunities', 'Opportunities: concept gaps, occasions, investable theses', '', True)]

cs = text('case-studies.html')
cs_date = data_to('case-studies.html')
cs_items = []
for m in re.finditer(r'<a[^>]+href="(/case-studies/[a-z0-9-]+)"[^>]*>(.*?)</a>', cs, re.S):
    u, inner = m.group(1), m.group(2)
    h = re.search(r'<h3[^>]*>(.*?)</h3>', inner, re.S)
    if not h or any(u == x[0] for x in cs_items):
        continue
    t = re.sub(r'<[^>]+>', '', h.group(1)).strip()
    num = re.search(r'No\. (\d+)', inner)
    cs_items.append((u, html.unescape(t).strip(), num.group(1) if num else ''))
cs_items.sort(key=lambda x: x[2])

qs = sorted(glob.glob('quarterly/20*.html'), reverse=True)
q_items = []
for fn in qs:
    k = os.path.basename(fn)[:-5]
    y, q = k.split('-')
    q_items.append((f'/quarterly/{k}', f'{q.upper()} {y}', data_to(fn)))

LOCK = '<svg class="rp-lock" viewBox="0 0 16 16" width="12" height="12" aria-label="Partners" role="img"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'
FREE = '/case-studies/guests-and-critics'


def row(u, t, note='', lock=False):
    return f'<li><a href="{u}"><span>{E(t)}{" " + LOCK if lock else ""}</span>{f"<em>{E(note)}</em>" if note else ""}</a></li>'


body = f'''<main class="pg rp">
<section class="pg-hero"><div class="wrap">
<div class="eyebrow">Reports</div>
<h1>Dream Menu publications</h1>
<p class="lede">Each report is fixed at the date its data was drawn, so the figures inside will not match the live numbers. For what the data says today, read <a href="/analysis">the analysis</a>, which is refreshed every week.</p>
</div></section>
<section class="rp-sec"><div class="wrap">
<article class="rp-col">
<p class="rp-kick">Annual report · Edition 6 · Data to {E(rep_date)}</p>
<h2><a href="/report">Hospitality Intelligence Report 2026</a></h2>
<p>The community view, a survey of 54 operators and five quarters of tracked demand, produced in partnership with Dunns Food &amp; Drinks. The overview is open; the four chapters need the partner password.</p>
<ul class="rp-list">{''.join(row(u, t, n, l) for u, t, n, l in REPORT)}</ul>
</article>
<article class="rp-col">
<p class="rp-kick">Quarterly · Public</p>
<h2><a href="/quarterly">State of the Menu</a></h2>
<p>The public headlines each quarter: the dream menu right now, the debates, what guests want gone and the most-named venues.</p>
<ul class="rp-list">{''.join(row(u, t, f'Data to {d}' if d else '') for u, t, d in q_items)}</ul>
</article>
<article class="rp-col rp-wide">
<p class="rp-kick">Commissioned reports · {len(cs_items)} reports · Built from data to {E(cs_date)}</p>
<h2><a href="/case-studies">Insight Series</a></h2>
<p>Reports that answer one commercial question each, for suppliers, operators, investors and the public sector. Most are provisional samples showing what a commissioned report looks like. One is free to read; the rest need the partner password. <a href="/for-business">Commission a report</a>.</p>
<ul class="rp-list rp-grid">{''.join(row(u, (f"No. {n} · " if n else "") + t, 'Free to read' if u == FREE else '', u != FREE) for u, t, n in cs_items)}</ul>
</article>
</div></section>
</main>
'''

CSS = '''<style>
.rp-sec .wrap{display:grid;grid-template-columns:1fr 1fr;gap:28px 36px;padding-top:32px;padding-bottom:48px}
.rp-col{border-top:3px solid var(--ink);padding-top:14px;min-width:0}
.rp-col.rp-wide{grid-column:1/-1}
.rp-kick{font:700 12px/1.3 var(--body);letter-spacing:.05em;text-transform:uppercase;color:var(--muted,#666);margin:0 0 6px}
.rp-col h2{margin:0 0 8px;font-size:26px}
.rp-col h2 a{color:inherit;text-decoration:none;box-shadow:inset 0 -3px 0 var(--gold)}
.rp-col>p{max-width:68ch;margin:0 0 14px}
.rp-list{list-style:none;margin:0;padding:0}
.rp-list li{border-top:1px solid var(--rule)}
.rp-list a{display:flex;justify-content:space-between;gap:12px;padding:11px 0;color:var(--ink);text-decoration:none;font-weight:600}
.rp-list a:hover span{text-decoration:underline;text-decoration-color:var(--gold);text-decoration-thickness:2px}
.rp-list em{font-style:normal;font-weight:500;color:var(--muted,#666);white-space:nowrap;font-size:14px}
.rp-grid{display:grid;grid-template-columns:1fr 1fr;column-gap:36px}
.rp-lock{vertical-align:-1px;opacity:.6}
@media (max-width:760px){.rp-sec .wrap,.rp-grid{grid-template-columns:1fr}.rp-list a{flex-direction:column;gap:2px}}
</style>
'''
open('reports.html', 'w', encoding='utf-8').write(head + CSS + '</head>\n' + HEADER + body + FOOTER)
print('wrote reports.html |', len(REPORT), 'report pages,', len(q_items), 'quarterly editions,', len(cs_items), 'Insight Series reports')
