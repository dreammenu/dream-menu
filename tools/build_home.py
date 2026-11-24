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
import benchlib
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


def times(r):
    """Plain words for a ratio: 2.3 -> 'more than twice', 3.1 -> 'three times'."""
    words = {2: 'twice', 3: 'three times', 4: 'four times', 5: 'five times'}
    w = int(r)
    if w < 2:
        return f'{r:.1f} times'
    if w in words:
        return ('more than ' if r - w >= 0.2 else 'about ') + words[w]
    return f'about {round(r)} times'


def card(n, tag, title, body, do, link, label, kind=''):
    return (f'<article class="hf-card{kind}"><div class="hf-n">{n}</div><div class="hf-tag">{tag}</div>'
            f'<h3>{title}</h3><p>{body}</p><p class="hf-do"><b>What to do</b>{do}</p>'
            f'<a class="hf-more" href="{link}">{label} &rarr;</a></article>')


cards = []
# Home findings rewritten 24 Nov 2026 (Gordon: make them insights an audience would be impressed by). Six cards, each a
# surprising, quotable fact first, then what to do. All figures are computed here at every build, so they stay current.
import os
def jsdata(fn):
    s_ = open(fn, encoding='utf-8').read()
    m_ = re.search(r'window\.\w+\s*=\s*', s_)
    return json.JSONDecoder().raw_decode(s_[m_.end():])[0]
PD = jsdata('partner-data.js')
AD = jsdata('analysis-data.js')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
AU = None
if os.path.exists('menu-audit-public.js'):
    AU = json.loads(open('menu-audit-public.js', encoding='utf-8').read().split('window.DM_AUDIT=', 1)[1].strip().rstrip(';'))
_gaps = sorted([r for r in (AU or {}).get('rows', []) if r['read'] == 'Gap'], key=lambda r: -r['demand'])
def one_in(p):
    return f'1 in {round(100 / p)}' if p else ''

# 1. Drinks: the cocktail's grip is slipping, spirits and whisky rising (like-for-like trend test on the drink question)
ag = {g['c']: g for g in PD['trends']['a']['groups']}
ac = {g['c']: g for g in PD['trends']['a'].get('cats', [])}
ck, sp, wh = ag.get('Cocktails'), ag.get('Spirits'), ac.get('Whisky / dram')
alc = {g['l']: g for g in DR['alc']['groups']}
af = alc.get('Alcohol-free instead')
if ck and ck.get('sig') and ck['move'] < 0:
    extra = ''
    if wh and wh.get('p', 1) < 0.05 and wh['late'] > wh['early']:
        extra = f' Whisky went from {pct(wh["early"])} to {pct(wh["late"])}, {times(wh["late"] / wh["early"])} as many picks.'
    elif sp and sp.get('sig'):
        extra = f' Spirits went from {pct(sp["early"])} to {pct(sp["late"])}.'
    cards.append(card(1, 'Drinks', 'The cocktail&rsquo;s grip is slipping',
        f'Cocktails fell from {pct(ck["early"])} to {pct(ck["late"])} of drink picks since late 2025, a move far beyond chance.{extra}'
        + (f' And {one_in(af["pct"])} now answer &ldquo;your dream alcoholic drink&rdquo; with something alcohol-free.' if af else ''),
        'Keep a tight house cocktail list, give a proper whisky and beer offer room, and price alcohol-free as a section, not a footnote.',
        '/analysis/change#drinks', 'How drinks are moving'))

# 2. Menus: the favourite dessert that most menus leave off (menu audit)
if _gaps:
    g = _gaps[0]
    gc = g['course'].lower()
    cn = AU.get('cn', {}).get(g['course'], AU['n'])
    off = 100 - g['menus']
    lead = 'Foodies&rsquo; favourite'
    cards.append(card(2, 'Menus', f'{lead} {gc} is missing from {round(off / 25) and ["", "1 in 4", "half of", "3 in 4", "almost all"][min(4, round(off / 25))] or pct(off)} menus',
        f'{g["l"]} is the {gc} guests name most ({pct(g["demand"])} of answers). We read {cn} {gc} menus from the venues guests rate highest: {pct(off)} leave it off.',
        f'If {g["l"].lower()} is not on your list, trial it as a special this month.',
        '/analysis/demand#th-audit', 'What guests want against what menus list'))

# 3. Guests and the guides: agree at the top, then part ways
cr = AD.get('critics', {})
t10, all_ = cr.get('tops', {}).get('10'), cr.get('tops', {}).get(str(cr.get('venues')))
if t10 and all_:
    none_pct = 100 * (all_['n'] - all_['any']) / all_['n']
    cards.append(card(3, 'Venues', f'The guides know the top 10. Foodies know the other {all_["n"] - all_["any"]:,}',
        f'Foodies and critics agree on the very best: {t10["any"]} of the 10 most-named venues hold a guide award or a place on a respected list. '
        f'Below that, they part ways: {pct(none_pct)} of the {cr["venues"]:,} places guests name are in no guide, award or list at all. That is where the next big names are.',
        'Guides tell you who has arrived. Our venue map shows who guests rate before the guides catch up.',
        '/analysis/cities#critics', 'Guests and the guides'))

# 4. Who you ask changes the menu: chefs and industry against creators
grp = {x['g']: dict(x['top_groups']) for x in PD.get('groups', [])}
ind, cre = grp.get('Industry', {}), grp.get('Creators', {})
if ind.get('Seafood') and cre.get('Potatoes and fries'):
    cards.append(card(4, 'Who orders what', 'Chefs dream of seafood. Creators dream of chips',
        f'Seafood is {pct(ind["Seafood"])} of what hospitality professionals choose, against {pct(cre.get("Seafood", 0))} for food creators, '
        f'who rate potatoes and fries ({pct(cre["Potatoes and fries"])}) as highly as seafood. The people who cook and the people who post want different plates.',
        'Write the menu for your guests, and the specials board for the people who will photograph it.',
        '/analysis/demand', 'What guests want, by who they are'))

# 5. The great debates
db = SC.get('debates', {})
cc, pn = db.get('coke'), db.get('pineapple')
if cc and pn:
    ib, co = 100 * cc['c']['Irn Bru'] / cc['n'], 100 * cc['c']['Coca Cola'] / cc['n']
    yes = 100 * pn['c']['Yes'] / pn['n']
    tie = abs(yes - 50) < 2
    cards.append(card(5, 'The debates', f'Irn Bru beats Coke. Pineapple on pizza is {"a dead heat" if tie else ("a yes" if yes > 50 else "a no")}',
        f'Asked to choose, {pct(ib)} pick Irn Bru and {pct(co)} Coca-Cola. Pineapple on pizza splits the room: {pct(yes)} yes, {pct(100 - yes)} no, from {pn["n"]:,} answers.',
        'Stock Irn Bru beside Coke. On pineapple, let the guest decide.',
        '/#debates', 'Every debate'))

# 6. Outside check: one place where foodies and the market disagree
dif = [i for i in B['items'] if i['verdict'] == 'differs' and i.get('kind') == 'direction']
if dif:
    i = dif[0]
    cards.append(card('', 'Outside check', 'The trend foodies most want gone is still growing' if i['id'] == 'matcha' else e(i['topic']),
        f'{e(i["dm"]["text"])}. {e(i["ext"]["who"])} ({e(i["ext"]["date"])}) reports the opposite: {e(i["ext"]["text"][0].lower() + i["ext"]["text"][1:])}.',
        e(i['read'].split('. ', 1)[1] if '. ' in i['read'] else i['read']),
        '/analysis/trust', 'Every outside benchmark', ' hf-ext'))

last = T['meta']['last']
from datetime import date
d = date.fromisoformat(last)
when = f'{d.day} {d.strftime("%B %Y")}'
section = (
    '<section class="h-sec" id="now"><div class="wrap">\n'
    '  <div class="h-head"><div class="eyebrow">This quarter</div><h2>What <em>{:,} foodies</em> just told us</h2>\n'.format(N_ALL) +
    f'  <p class="lede">Six things the data says right now, from {N_ALL:,} interviews to {when}. Changes are tested against chance, not just counted; '
    'the grey card is an outside source, kept apart as a challenge to our own data. Each ends with what to do about it.</p></div>\n'
    f'  <div class="hf-grid hf-three">{"".join(cards)}</div>\n'
    f'  <p class="hf-bench"><span aria-hidden="true">&#10003;</span> {benchlib.headline()}. <a href="/analysis#compare">See every comparison</a></p>\n'
    '  <p class="hf-foot"><a class="btn gold" href="/analysis/demand">See all the findings</a> <a class="hf-link" href="/report#library">All reports</a></p>\n'
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
_DM = load('dm-data.js')
secs['try'] = ('<section class="h-sec alt" id="try"><div class="wrap">\n'
    '  <div class="h-head"><div class="eyebrow">Try it yourself</div><h2>Put the data <em>to work</em></h2></div>\n'
    '  <div class="hf-grid hf-three">'
    '<article class="hf-card"><div class="hf-tag">For food lovers</div><h3>Build your dream menu</h3><p>Pick six courses, see what share of guests agree and which city you eat like. Share the result.</p><a class="hf-more" href="/my-dream-menu">Build mine &rarr;</a></article>'
    f'<article class="hf-card hf-map"><a class="hf-pic" href="/map" tabindex="-1" aria-hidden="true"><img src="/map-card.webp" alt="" width="640" height="431" loading="lazy"></a><div class="hf-tag">For a night out</div><h3>The venue map</h3><p>{_DM["meta"]["pinned"]:,} places guests have named, plus award winners, with city and neighbourhood guides from Glasgow to London. No critics, no paid placements.</p><a class="hf-more" href="/map">Open the map &rarr;</a> <a class="hf-more hf-2" href="/cities">City guides &rarr;</a></article>'
    '<article class="hf-card"><div class="hf-tag">For venues</div><h3>Check my menu</h3><p>Tick the dishes you serve and see how much of what guests want you cover, the staples you are missing and the biggest gaps.</p><a class="hf-more" href="/menu-check">Check mine &rarr;</a></article>'
    '</div>\n</div></section>\n\n')
secs['pick'] = ('<section class="h-sec" id="pick"><div class="wrap">\n'
    '  <div class="h-head"><div class="eyebrow">Find what matters to you</div><h2>What are you <em>interested in?</em></h2></div>\n'
    '  <div data-interest="home"></div>\n</div></section>\n\n')
# In their own words: three guest answers, anonymous (tools/data/home-quotes.json). Added 16 Nov 2026 (audit):
# the headline promises foodies speaking for themselves, so the page should let them.
_VI = {v['i']: v for v in _DM['venues']}
_CN = {'s': 'starter', 'm': 'main', 'd': 'side', 'p': 'dessert', 'k': 'soft drink', 'a': 'drink'}
_qs = []
for q in json.load(open('tools/data/home-quotes.json', encoding='utf-8'))['quotes']:
    v = _VI.get(q['venue'])
    if not v:
        continue
    own = sorted([t for c, t in v.get('q') or [] if c == q['course']], key=len)
    if not own:
        continue
    slug = re.sub(r'-x$', '', v['i'])
    where = f'<a href="/venue/{slug}">{e(v["n"])}</a>' if os.path.exists(f'venue/{slug}.html') else e(v['n'])
    _qs.append(f'<figure class="hq"><blockquote>&ldquo;{e(own[-1])}&rdquo;</blockquote>'
               f'<figcaption>A guest&rsquo;s dream {_CN.get(q["course"], "dish")} &middot; {where}, {e(v["c"])}</figcaption></figure>')
if _qs:
    secs['voices'] = ('<section class="h-sec" id="voices"><div class="wrap">\n'
        '  <div class="h-head"><div class="eyebrow">In their own words</div><h2>What the answers <em>sound like</em></h2>\n'
        '  <p class="lede">Every figure on this site starts as an answer like these. Guests are not named unless they asked to be.</p></div>\n'
        f'  <div class="hq-grid">{"".join(_qs)}</div>\n</div></section>\n\n')

secs.pop('more', None)
for _k in ('start', 'coverage', 'map', 'places'):   # trimmed 13 Nov 2026: the menu, the tools band, the city guides and the analysis already do these jobs
    secs.pop(_k, None)

# Home (24 Nov 2026 audit): findings first, then one door per reader, then the dream menu itself.
# The interest filter, the tools band, the crave/over lists and the risers left the home page: the header
# menus, the three doors and the analysis already do those jobs.
secs['doors'] = ('<section class="h-sec alt" id="doors"><div class="wrap">\n'
    '  <div class="h-head"><div class="eyebrow">Where next</div><h2>Pick your <em>way in</em></h2></div>\n'
    '  <div class="hf-grid hf-three">'
    '<article class="hf-card"><div class="hf-tag">For suppliers and sponsors</div><h3>Work with us</h3><p>A quarterly partner briefing for your sales team, commissioned reports on your own question, or a sponsorship. Pick the route that fits.</p><a class="hf-more" href="/for-business">Ways to work with us &rarr;</a></article>'
    '<article class="hf-card"><div class="hf-tag">For venues</div><h3>Check your menu</h3><p>Tick the dishes you serve and see how much of what guests want you cover, then the toolkit, tested ideas and the Restaurant MOT.</p><a class="hf-more" href="/menu-check">Check my menu &rarr;</a></article>'
    '<article class="hf-card hf-map"><a class="hf-pic" href="/map" tabindex="-1" aria-hidden="true"><img src="/map-card.webp" alt="" width="640" height="431" loading="lazy"></a><div class="hf-tag">For foodies</div><h3>Where to eat</h3><p>The venues guests name, mapped and ranked, with city guides and your own dream menu to build.</p><a class="hf-more" href="/map">Open the map &rarr;</a></article>'
    '</div>\n</div></section>\n\n')
for _k in ('pick', 'try', 'mood', 'rising'):
    secs.pop(_k, None)
order = ['h-hero', 'h-stats', 'now', 'doors', 'courses', 'voices', 'debates']
missing = [k for k in secs if k not in order]
if missing:
    raise SystemExit(f'home sections not in the order list: {missing}')
if 'mood' in secs:
    secs['mood'] = re.sub(r'<p class="method">Source:.*?</p>\n?', '', secs['mood'], flags=re.S)
    secs['mood'] = re.sub(r'(</div></section>\n*)$', lambda m: METHOD_NOTE + '\n' + m.group(1), secs['mood'].rstrip('\n') + '\n', count=1) + '\n'
body = ''.join(secs[k] for k in order if k in secs)
s = head + body + tail
if '/interest.js' not in s:
    s = s.replace('</body>', '<script src="/interest.js" defer></script>\n</body>', 1)

# hero card: a teaser for the course section, not a second copy of it
s = re.sub(r'\s*<a class="mlink"[^>]*>.*?</a>', '', s)
s = s.replace('<div class="mf">Share of answers for each course</div>',
              '<div class="mf">Share of answers for each course</div><a class="mlink" href="#courses">The top five in every course &rarr;</a>', 1)
# report sponsor, under the hero buttons (Dunns is named as sponsor on /report; independence terms there)
s = re.sub(r'\s*<p class="h-sponsor">.*?</p>', '', s)
s = s.replace('</div>\n  </div>\n  <aside class="h-menu"',
              '</div>\n    <p class="h-sponsor"><img src="/dunns.png" alt="" width="28" height="28"><span>Report 2026 produced in partnership with <a href="/report#sponsor">Dunns Food &amp; Drinks</a>. The findings are independent.</span></p>\n  </div>\n  <aside class="h-menu"', 1)
if 'class="h-sponsor"' not in s:
    raise SystemExit('hero sponsor line: insertion point not found')

# hero buttons
s = re.sub(r'<div class="h-ctas"><a class="btn gold" href="#[^"]+">[^<]+</a><a class="btn ghost" href="/map">[^<]+</a></div>',
           '<div class="h-ctas"><a class="btn gold" href="#now">This quarter&rsquo;s findings</a><a class="btn ghost" href="/map">Find a place to eat</a></div>', s)
# a dish search in the hero (24 Nov 2026): typing opens the site search with dishes first (nav.js data-search-input)
s = re.sub(r'\s*<form class="h-search".*?</form>', '', s, flags=re.S)
s = s.replace('<a class="btn ghost" href="/map">Find a place to eat</a></div>',
              '<a class="btn ghost" href="/map">Find a place to eat</a></div>'
              '<form class="h-search" role="search" action="/trends"><label for="hSearch">Look up any dish</label>'
              '<div><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
              '<input id="hSearch" type="search" data-search-input placeholder="Scallops, tiramisu, whisky&hellip;" autocomplete="off"></div></form>', 1)
s = s.replace('href="#map"', 'href="/map"').replace('href="#start"', 'href="#doors"').replace('href="#try"', 'href="#doors"').replace('href="#pick"', 'href="#doors"').replace('href="#coverage"', 'href="/cities"')
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
