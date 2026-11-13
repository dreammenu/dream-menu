"""Build the home page structure and its "This quarter" findings band.

Run after refresh_static.py, build_trends.py, build_drinks.py and build_benchmarks.py,
and before build_nav.py. Safe to rerun.

  * writes the #now section: three findings from Dream Menu data, each with a
    plain recommendation, plus one outside check kept visibly separate
  * puts the sections in a fixed order and drops the old "Go deeper" block
  * points the hero buttons at the findings and the map
  * labels the comfort lists as shares of all interviews
Only public, course-level figures are used here.
"""
import html, json, re

ROOT = '.'


def load(fn):
    s = open(fn, encoding='utf-8').read()
    return json.loads(s[s.index('{'):s.rstrip().rstrip(';').rindex('}') + 1])


T = load('trend-public.js')
DR = load('drinks-new.js')
B = load('bench-public.js')
N_ALL = T['meta']['n_all']
e = html.escape


def pct(v):
    return f'{v:.1f}%'


def card(n, tag, title, body, do, link, label, kind=''):
    return (f'<article class="hf-card{kind}"><div class="hf-n">{n}</div><div class="hf-tag">{tag}</div>'
            f'<h3>{title}</h3><p>{body}</p><p class="hf-do"><b>What to do</b>{do}</p>'
            f'<a class="hf-more" href="{link}">{label} &rarr;</a></article>')


cards = []

# 1. Where the menu is moving: course churn beyond chance
ch = sorted(T['churn'], key=lambda c: -c['beyond'])
moved = [c for c in ch if c['p'] < 0.05]
if moved:
    c = moved[0]
    steady = [x['cl'].lower() + 's' for x in T['churn'] if x not in moved]
    rest = ', '.join(steady[:-1]) + ' and ' + steady[-1] if len(steady) > 1 else (steady[0] if steady else '')
    cards.append(card(1, 'Movement', f'{c["cl"]}s are where the menu is moving',
        f'{pct(c["obs"])} of {c["cl"].lower()} answers now sit in a different food group than in late 2025. '
        f'Sampling alone would move about {pct(c["chance"])}.' + (f' {rest.capitalize()} are within chance.' if rest else ''),
        f'Review the {c["cl"].lower()} list first. ' + (f'Change {rest} for cost or quality, not to chase a trend.' if rest else ''),
        '/analysis#changed', 'What changed, course by course'))
else:
    cards.append(card(1, 'Movement', 'No course has moved beyond chance',
        'Every course holds roughly the mix it had in late 2025 once sampling noise is allowed for.',
        'Keep core lines and test new ideas as specials before they earn a permanent place.',
        '/analysis#changed', 'What changed, course by course'))

# 2. Demand against supply, from the menu audit (tools/build_menu_audit.py). Replaced the staples card on 13 Nov 2026:
#    the staples are still on /analysis#life; this is the finding a venue can act on tonight. Falls back to staples without an audit.
import os
AU = None
if os.path.exists('menu-audit-public.js'):
    AU = json.loads(open('menu-audit-public.js', encoding='utf-8').read().split('window.DM_AUDIT=', 1)[1].strip().rstrip(';'))
_gaps = sorted([r for r in (AU or {}).get('rows', []) if r['read'] == 'Gap'], key=lambda r: -r['demand'])
st = T['staples']
if _gaps:
    g = _gaps[0]
    gc = g['course'].lower()
    same = [r for r in _gaps if r['course'] == g['course']]
    over = sorted([r for r in AU['rows'] if r['read'] == 'Over-supplied' and r['course'] == g['course']], key=lambda r: -r['menus'])
    cn = AU.get('cn', {}).get(g['course'], AU['n'])
    cards.append(card(2, 'Menus', f'{g["l"]}: {pct(g["demand"])} of guests, {g["menus"]:.0f}% of menus',
        f'We read the published menus of {AU["n"]} of the venues guests name most. {g["l"]} is the most-named {gc}, yet it is on {g["menus"]:.0f}% of the {cn} menus that print {gc}s.'
        + (f' {over[0]["l"]} are on {over[0]["menus"]:.0f}%, for {pct(over[0]["demand"])} of guests.' if over else ''),
        (f'Check your {gc} list against the {len(same)} most-named ({", ".join(r["l"].lower() for r in same)}) before adding anything new.' if len(same) > 1
         else f'If {g["l"].lower()} is not on your menu, trial it as a special.'),
        '/analysis#menu-gap', 'What guests ask for against what menus list'))
elif st:
    top = st[:3]
    names = ', '.join(s['l'].lower() for s in top[:-1]) + ' and ' + top[-1]['l'].lower()
    cards.append(card(2, 'Staples', f'{len(st)} dishes hold their share every quarter',
        f'Led by {names}. Tiramisu alone takes {pct(top[0]["pct"])} of dessert answers.' if top[0]['l'] == 'Tiramisu'
        else f'Led by {names}, each holding its share in every full quarter.',
        'Protect these lines. Spend effort on how well they are made and priced, not on replacing them.',
        '/analysis#life', 'The life cycle of every dish'))

# 3. Drinks: cocktails and alcohol-free
alc = {g['l']: g for g in DR['alc']['groups']}
ck, af = alc.get('Cocktails'), alc.get('Alcohol-free instead')
if ck and af:
    cards.append(card(3, 'Drinks', f'Cocktails lead; {pct(af["pct"])} choose alcohol-free',
        f'Cocktails take {pct(ck["pct"])} of alcoholic drink answers. {pct(af["pct"])} answer the question with something alcohol-free. '
        f'An early baseline from {DR["alc"]["n"]} answers since August 2026.',
        'Give alcohol-free its own priced section, not a footnote, and lead the drinks list with house cocktails.',
        '/analysis#drinks', 'The new drinks series'))

# 4. Outside check: one place where foodies and the market disagree
dif = [i for i in B['items'] if i['verdict'] == 'differs' and i.get('kind') == 'direction']
if dif:
    i = dif[0]
    cards.append(card('', 'Outside check', f'{e(i["topic"])}: growth and backlash at once' if i['id'] == 'matcha' else e(i['topic']),
        f'{e(i["dm"]["text"])}. {e(i["ext"]["who"])} ({e(i["ext"]["date"])}) reports the opposite: {e(i["ext"]["text"][0].lower() + i["ext"]["text"][1:])}.',
        e(i['read'].split('. ', 1)[1] if '. ' in i['read'] else i['read']),
        '/analysis#compare', 'Every outside benchmark', ' hf-ext'))

last = T['meta']['last']
from datetime import date
d = date.fromisoformat(last)
when = f'{d.day} {d.strftime("%B %Y")}'
section = (
    '<section class="h-sec" id="now"><div class="wrap">\n'
    '  <div class="h-head"><div class="eyebrow">This quarter</div><h2>Three findings, and <em>what to do about them</em></h2>\n'
    f'  <p class="lede">Tested against chance, not just counted. Figures are shares of answers from {N_ALL:,} interviews to {when}. '
    + (f'The menus card sets those answers beside {AU["n"]} published menus read on {date.fromisoformat(AU["collected"]).day} {date.fromisoformat(AU["collected"]).strftime("%B %Y")}. ' if _gaps else '')
    + 'The fourth card is an outside source, kept separate as a challenge to our own data.</p></div>\n'
    f'  <div class="hf-grid">{"".join(cards)}</div>\n'
    '  <p class="hf-foot"><a class="btn gold" href="/analysis">Read the full analysis</a> <a class="hf-link" href="/report">Report 2026</a></p>\n'
    '</div></section>\n')
METHOD_NOTE = (f'<p class="method">Source: {N_ALL:,} Dream Menu interviews, 1 September 2025 to {when}. Dish categories were made more specific on 24 October 2026: '
               'each answer is now coded to the dish itself (scallops, tiramisu, skinny fries) rather than a broad group such as seafood or ice cream. '
               'Shares are of answers coded to a category; answers coded as Other are left out. Qualitative fieldwork, not a statistically representative survey. '
               '<a href="/how-it-works">How it works</a>.</p>')

fn = 'index.html'
s = open(fn, encoding='utf-8').read()
head, rest = s.split('<section class="h-hero">', 1)
rest = '<section class="h-hero">' + rest
# split off sections up to the signup block
end = rest.index('<!--signup-->') if '<!--signup-->' in rest else rest.index('<section class="su">')
body, tail = rest[:end], rest[end:]
secs = {}
for m in re.finditer(r'<section class="([^"]+)"(?: id="([^"]+)")?[^>]*>.*?</section>\n*', body, re.S):
    key = m.group(2) or m.group(1)
    secs[key] = m.group(0).rstrip('\n') + '\n\n'
gap = re.sub(r'<section class="[^"]+".*?</section>\n*', '', body, flags=re.S).strip()
if gap:
    raise SystemExit(f'unexpected content between home sections: {gap[:200]}')
secs['now'] = section + '\n'
secs['try'] = ('<section class="h-sec alt" id="try"><div class="wrap">\n'
    '  <div class="h-head"><div class="eyebrow">Try it yourself</div><h2>Put the data <em>to work</em></h2></div>\n'
    '  <div class="hf-grid hf-three">'
    '<article class="hf-card"><div class="hf-tag">For food lovers</div><h3>Build your dream menu</h3><p>Pick six courses, see what share of guests agree and which city you eat like. Share the result.</p><a class="hf-more" href="/my-dream-menu">Build mine &rarr;</a></article>'
    '<article class="hf-card"><div class="hf-tag">For a night out</div><h3>City and neighbourhood guides</h3><p>Where foodies eat in Glasgow, Edinburgh, London and beyond, down to Finnieston and Leith. No critics, no paid placements.</p><a class="hf-more" href="/cities">Find a guide &rarr;</a></article>'
    '<article class="hf-card"><div class="hf-tag">For venues</div><h3>Check my menu</h3><p>Tick the dishes you serve and see how much of what guests want you cover, the staples you are missing and the biggest gaps.</p><a class="hf-more" href="/menu-check">Check mine &rarr;</a></article>'
    '</div>\n</div></section>\n\n')
secs.pop('more', None)
for _k in ('start', 'coverage', 'map'):   # trimmed 13 Nov 2026: the menu, the tools band and the places section already do these jobs
    secs.pop(_k, None)

order = ['h-hero', 'h-stats', 'now', 'try', 'start', 'courses', 'places', 'debates', 'mood', 'map', 'coverage', 'rising']
missing = [k for k in secs if k not in order]
if missing:
    raise SystemExit(f'home sections not in the order list: {missing}')
if 'mood' in secs and 'class="method">Source:' not in secs['mood']:
    secs['mood'] = re.sub(r'(</div></section>\n*)$', lambda m: METHOD_NOTE + '\n' + m.group(1), secs['mood'].rstrip('\n') + '\n', count=1) + '\n'
body = ''.join(secs[k] for k in order if k in secs)
s = head + body + tail

# hero buttons
s = re.sub(r'<div class="h-ctas"><a class="btn gold" href="#[^"]+">[^<]+</a><a class="btn ghost" href="/map">[^<]+</a></div>',
           '<div class="h-ctas"><a class="btn gold" href="#now">This quarter&rsquo;s findings</a><a class="btn ghost" href="/map">Find a place to eat</a></div>', s)
s = s.replace('href="#map"', 'href="/map"').replace('href="#start"', 'href="#try"').replace('href="#coverage"', 'href="/cities"')
# comfort lists are shares of all interviews
s = s.replace('<p class="sub">The comfort food guests admit to</p>', f'<p class="sub">Comfort food guests admit to, as a share of all interviews</p>')
s = s.replace('<p class="sub">Food trends guests would happily see disappear</p>', f'<p class="sub">Trends guests would happily see go, as a share of all interviews</p>')
open(fn, 'w', encoding='utf-8').write(s)

# styles, kept in one marked block so reruns replace it
css_fn = 'brand.css'
css = open(css_fn, encoding='utf-8').read()
block = """/* home-find */
.hf-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:22px}
.hf-card{background:var(--card);border:1px solid var(--rule);border-top:4px solid var(--navy);border-radius:10px;padding:18px 18px 16px;display:flex;flex-direction:column}
.hf-card.hf-ext{border-top-color:var(--rule-strong);background:var(--panel)}
.hf-n{font:700 13px/1 inherit;color:var(--muted)}
.hf-n:empty{display:none}
.hf-tag{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:6px 0 8px}
.hf-card h3{font-size:19px;line-height:1.25;margin:0 0 8px}
.hf-card p{font-size:15px;line-height:1.5;margin:0 0 10px;color:var(--ink)}
.hf-do{border-left:3px solid var(--gold);padding-left:10px}
.hf-do b{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:2px}
.hf-more{margin-top:auto;font-size:14px;font-weight:600}
.hf-three{grid-template-columns:repeat(3,1fr)}
@media (max-width:1000px){.hf-three{grid-template-columns:1fr}}
.hf-foot{margin-top:20px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}
@media (max-width:1000px){.hf-grid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:620px){.hf-grid{grid-template-columns:1fr}}
/* /home-find */
"""
css = re.sub(r'/\* home-find \*/.*?/\* /home-find \*/\n', '', css, flags=re.S) + block
open(css_fn, 'w', encoding='utf-8').write(css)
print('home: ' + ', '.join(k for k in order if k in secs), f'| {len(cards)} finding cards')
