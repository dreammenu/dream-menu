#!/usr/bin/env python3
"""Places the "What the evidence says for you" boxes on the pages each reader already uses (24 Nov 2026).

tools/build_pages.py writes the four reader cards (rewritten from the live numbers at every refresh) to
tools/data/evidence-roles.json and puts two of them on its own pages (opening or investing on /analysis/cities,
suppliers on /analysis/partner). This script puts the other two on static pages:
  role 0, running a venue or a kitchen  -> /operators (the operator toolkit)
  role 3, marketing, press and guides   -> /press (the press kit)
Run it after build_pages.py, build_press.py and refresh_static.py, before build_info.py and build_nav.py.
Usage: python3 tools/build_evidence.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
R = json.load(open('tools/data/evidence-roles.json', encoding='utf-8'))['roles']
PLACES = [(0, 'operators.html'), (3, 'press.html')]
CSS = ('<style>.ev-card{border-left:4px solid var(--gold);background:var(--panel);padding:18px 20px;margin:26px 0 6px;border-radius:0 8px 8px 0}'
       '.ev-card h2{margin:6px 0 8px;font-size:clamp(20px,2.4vw,26px)}.ev-card p{max-width:80ch;margin:0 0 10px}</style>')

def box(r):
    return (f'<!--evidence--><section id="evidence"><div class="wrap">{CSS}<div class="ev-card"><div class="eyebrow">What the evidence says for you</div>'
            f'<h2>{r["h"]}</h2><p>{r["t"]}</p><a href="/analysis/demand">See the findings behind it &rarr;</a></div></div></section><!--/evidence-->\n')

for i, fn in PLACES:
    if i >= len(R) or not os.path.exists(fn):
        continue
    s = open(fn, encoding='utf-8').read()
    s = re.sub(r'<!--evidence-->.*?<!--/evidence-->\n?', '', s, flags=re.S)
    m = re.search(r'<main[^>]*>.*?</section>\s*', s, re.S)        # straight after the page's opening section
    if not m:
        raise SystemExit(f'{fn}: no opening section found')
    s = s[:m.end()] + box(R[i]) + s[m.end():]
    open(fn, 'w', encoding='utf-8').write(s)
    print(f'{fn}: evidence box for "{R[i]["h"]}"')
