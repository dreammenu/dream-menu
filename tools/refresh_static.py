#!/usr/bin/env python3
"""Brings the figures written into the static pages in line with the data files.

Run from the repository root after any data update (after add_interviews.py / add_venues.py):
  python3 tools/refresh_static.py && python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py

Reads partner-data.js, dm-data.js, dm-cat.js, dm-labels.js and tools/data/static-counts.json and
rewrites, in place:
  index.html      hero and stats counts, the voted dream menu, course cards, the four market tabs
                  (dishes and most-named venues), the debates, guilty pleasures and bin it, map card,
                  source line
  insights.html   lede, debates, interviews by quarter, quote attributions
  every page      the "Data to ..." date in the footer
  dm-fresh.js     the data status table (interviews, venues, analysis)
  for-business, how-it-works, onepager, briefing, partner, operators, map: counts and dates
The 2026 report pages keep their own edition figures (data to 9 October 2026) on purpose.
"""
import datetime as dt, glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TODAY = dt.date.today().isoformat()


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
D = load('dm-data.js', 'DM')


def fix_place_labels():
    """The reverse geocoder labels some Leith and Portobello venues 'Seafield'. Relabel them from the
    postcode district in the address, and write dm-data.js back only if something changed."""
    DISTRICT = {'EH6': 'Leith', 'EH15': 'Portobello'}
    n = 0
    for v in D['venues']:
        if v.get('tw') in ('Seafield',):
            pc = re.search(r'\b(EH\d+)\s*\d[A-Z]{2}\b', v.get('ad') or '')
            new = DISTRICT.get(pc.group(1) if pc else '', v['c'])
            if new != v['tw']:
                v['tw'] = new
                n += 1
    if n:
        src = open('dm-data.js', encoding='utf-8').read()
        m = re.search(r'window\.DM\s*=\s*', src)
        obj, used = json.JSONDecoder().raw_decode(src[m.end():])
        src = src[:m.end()] + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + src[m.end() + used:]
        open('dm-data.js', 'w', encoding='utf-8').write(src)
        changed.append('dm-data.js')


changed = []
fix_place_labels()
C = load('dm-cat.js', 'DMC')
L = load('dm-labels.js', 'DML')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
M = D['meta']
V = {v['i']: v for v in D['venues']}
MK = {m['id']: m for m in D['markets']}
# awards (from awards.js meta)
_s = open('awards.js', encoding='utf-8').read()
_m = re.search(r'window\.DM_AWARDS\s*=\s*', _s)
AWD = json.JSONDecoder().raw_decode(_s[_m.end():])[0]
AWM, _G, _PL = AWD['meta'], AWD['groups'], AWD['places']
_star = lambda p: any(_G[a[0]] == 'star' for a in p[10])
LAST = dt.date.fromisoformat(P['last'])
LAST_H = LAST.strftime('%-d %B %Y')          # 27 October 2026
LAST_S = LAST.strftime('%-d %b')              # 27 Oct
N_ALL = f"{P['n_all']:,}"
lab = lambda c: (L.get(c) or [c])[0]
fmt = lambda n: f'{n:,}'
pc0 = lambda x: f'{round(x):d}%'
w1 = lambda a, b: f'{100 * a / b:.1f}%' if b else '0%'


# Home sections that may have been retired by tools/build_home.py (the market tabs left the home page on
# 13 Nov 2026; the city guides and the analysis carry that view). Their patterns are applied only if present.
OPTIONAL = {r'<div class="mpane" role="tabpanel" id="p0".*?See the world on the map →</a></div>\n</div>',
            r'<div class="mtabs" role="tablist" aria-label="Market">.*?</div>',
            r'<p class="lede">What guests name in each market[^<]*</p>'}


def edit(fn, pairs, required=True):
    s = open(fn, encoding='utf-8').read()
    o = s
    s = re.sub(r'<details class="vinfo">.*?</details>', '', s, flags=re.S)  # chart notes are re-added by build_info.py
    for pat, rep in pairs:
        s2 = re.sub(pat, rep, s, flags=re.S)
        if s2 == s and required and pat not in OPTIONAL and not re.search(pat, s, flags=re.S):
            raise SystemExit(f'{fn}: pattern not found: {pat[:80]}')
        s = s2
    if s != o:
        open(fn, 'w', encoding='utf-8').write(s)
        changed.append(fn)


# ---------------------------------------------------------------- shared pieces
def dcount(d, o):
    """Debate count; 'Scottish tap water' answers are tap water, so they count as Tap."""
    return d['c'].get(o, 0) + (d['c'].get('Scottish tap water', 0) if o == 'Tap' else 0)


def debates_home():
    out = []
    spec = [('coke', 'Irn-Bru or Coca-Cola?', ['Irn Bru', 'Coca Cola', 'Neither']),
            ('tea', 'Coffee or tea?', ['Coffee', 'Tea', 'Neither']),
            ('pineapple', 'Pineapple on pizza?', ['Yes', 'No']),
            ('water', 'Still, sparkling or tap?', ['Still', 'Tap', 'Sparkling'])]
    for key, title, opts in spec:
        d = SC['debates'][key]
        n = d['n']
        sh = [(o, 100 * dcount(d, o) / n) for o in opts]
        win = max(sh, key=lambda x: x[1])
        label = ', '.join(f'{o} {pc0(p)}' for o, p in sh)
        bars = ''.join(f'<i class="s{i}" style="width:{p:.1f}%" title="{o} {pc0(p)}"></i>' for i, (o, p) in enumerate(sh))
        keys = ''.join(f'<li><i class="s{i}"></i>{o} <b>{pc0(p)}</b></li>' for i, (o, p) in enumerate(sh))
        out.append(f'<article class="deb"><h3>{title}</h3><p class="win">{win[0]} <b>{pc0(win[1])}</b></p>'
                   f'<div class="stack" role="img" aria-label="{label}">{bars}</div><ul class="sk">{keys}</ul>'
                   f'<p class="n">{fmt(n)} answers</p></article>')
    return '<div class="dgrid">' + ''.join(out) + '</div>'


def debates_insights():
    out = []
    spec = [('coke', 'Irn Bru or Coke?', ['Irn Bru', 'Coca Cola', 'Neither']),
            ('tea', 'Tea or coffee?', ['Coffee', 'Tea', 'Neither']),
            ('pineapple', 'Pineapple on pizza?', ['Yes', 'No']),
            ('water', 'Still, tap or sparkling?', ['Still', 'Tap', 'Sparkling'])]
    for key, title, opts in spec:
        d = SC['debates'][key]
        n = d['n']
        sh = [(o, 100 * dcount(d, o) / n) for o in opts]
        label = ', '.join(f'{o} {p:.1f}%' for o, p in sh)
        bars = ''.join(f'<i class="s{i + 1}" style="width:{p:.2f}%" title="{o}: {p:.1f}%"></i>' for i, (o, p) in enumerate(sh))
        keys = ''.join(f'<span><b class="s{i + 1}"></b>{o} <em>{p:.1f}%</em></span>' for i, (o, p) in enumerate(sh))
        out.append(f'    <div class="card"><h3>{title}</h3><div class="split" role="img" aria-label="{label}">{bars}</div>'
                   f'<div class="splitkey">{keys}</div><p class="note">{fmt(n)} answers</p></div>')
    return '<div class="grid">\n' + '\n'.join(out) + '\n  </div>'


def hb(items):
    """items: [(label, count, pct)] -> the home page horizontal bars"""
    top = items[0][1] if items else 1
    return '<ol class="hb">' + ''.join(
        f'<li><span class="hb-l">{html.escape(l)}</span><span class="hb-t"><i style="width:{100 * c / top:.1f}%"></i></span>'
        f'<span class="hb-v">{pc0(p)}</span></li>' for l, c, p in items) + '</ol>'


def course_card(k, eyebrow):
    t = P['trends'][k]
    base = SC['course_card_answers'][k]
    items = [(it.get('l') or lab(it['c']), it['n'], 100 * it['n'] / base) for it in t['cats'][:5]]
    return (f'<article class="ccard"><header><span class="eyebrow">{eyebrow}</span><span class="n">{fmt(base)} answers</span></header>'
            + hb(items) + '</article>')


def drink_card():
    dc = SC['drink_card']
    items = [(l, c, 100 * c / dc['n']) for l, c in dc['c'][:5]]
    return (f'<article class="ccard"><header><span class="eyebrow">Drink</span><span class="n">{fmt(dc["n"])} answers</span></header>'
            + hb(items) + '</article>')


# Market tabs on the home page. Glasgow holds most of the evidence, so the tabs are Glasgow, Edinburgh,
# the rest of Scotland, the rest of the UK and outside the UK: no tab repeats another. Each dish shows its share of the dish
# mentions at that market's venues and how far that is above or below the all-market share (the index).
GLA, EDI = ('Glasgow', 'United Kingdom'), ('Edinburgh', 'United Kingdom')
MARKET_SETS = [
    ('Glasgow', lambda v: (v['c'], v['co']) == GLA, '/map#city-glasgow-united-kingdom', 'See Glasgow on the map →', 'city:Glasgow|United Kingdom'),
    ('Edinburgh', lambda v: (v['c'], v['co']) == EDI, '/map#city-edinburgh-united-kingdom', 'See Edinburgh on the map →', 'city:Edinburgh|United Kingdom'),
    ('the rest of Scotland', lambda v: v['na'] == 'Scotland' and (v['c'], v['co']) not in (GLA, EDI), '/map#nation-scotland', 'See Scotland on the map →', None),
    ('the rest of the UK', lambda v: bool(v['c']) and v['co'] == 'United Kingdom' and v['na'] in ('England', 'Wales', 'Northern Ireland'), '/map#nation-england', 'See England on the map →', None),
    ('outside the UK', lambda v: bool(v['c'] and v['co']) and v['co'] != 'United Kingdom', '/map#world', 'See the world on the map →', None),
]
DEEP_MENTIONS = 300   # a market is deep with 30+ guests (the site-wide rule) and 300+ venue mentions
TAB_NAMES = ['Glasgow', 'Edinburgh', 'Rest of Scotland', 'Rest of UK', 'Outside the UK']


def cat_counts(pred):
    """Dish counts, the number of venues each dish is named at, venue mentions and the venues, for one market."""
    cnt, spread, mentions, venues = {}, {}, 0, []
    for i, v in enumerate(D['venues']):
        if not pred(v) or not v.get('m'):
            continue
        mentions += v['m']
        venues.append(v)
        for ci, n in C['v'].get(str(i)) or []:
            cnt[ci] = cnt.get(ci, 0) + n
            spread[ci] = spread.get(ci, 0) + 1
    return cnt, spread, mentions, venues


WORLD_CNT, _, _, _ = cat_counts(lambda v: True)
WORLD_T = sum(WORLD_CNT.values())


def market_pane(i, title, pred, more_href, more_text, mid, hidden):
    cnt, spread, mentions, venues = cat_counts(pred)
    tot = sum(cnt.values()) or 1
    deep = (bool(MK[mid].get('so')) if mid else True) and mentions >= DEEP_MENTIONS
    floor = 5 if deep else 8
    solid = lambda ci: cnt[ci] >= floor and spread[ci] >= 3   # an index needs 5 mentions (8 in a thin market) at 3+ venues
    idx = lambda ci: 100 * (cnt[ci] / tot) / (WORLD_CNT[ci] / WORLD_T)
    top = sorted(cnt, key=lambda ci: (-cnt[ci], C['c'][ci]))[:8]
    hi = top and cnt[top[0]] or 1
    rows = ''
    for ci in top:
        x = idx(ci)
        here, allp = 100 * cnt[ci] / tot, 100 * WORLD_CNT[ci] / WORLD_T
        chip = (f'<span class="hb-x up" title="{here:.1f}% of mentions here, {allp:.1f}% across all markets">vs {allp:.1f}%</span>' if x >= 125 and solid(ci) else
                f'<span class="hb-x dn" title="{here:.1f}% of mentions here, {allp:.1f}% across all markets">vs {allp:.1f}%</span>' if x <= 75 and solid(ci) else '')
        rows += (f'<li><span class="hb-l">{html.escape(lab(C["c"][ci]))}{chip}</span><span class="hb-t"><i style="width:{100 * cnt[ci] / hi:.1f}%"></i></span>'
                 f'<span class="hb-v">{100 * cnt[ci] / tot:.1f}%</span></li>')
    sig = sorted((ci for ci in cnt if solid(ci) and idx(ci) >= 125), key=lambda ci: -idx(ci))[:3]
    sig_html = ('<p class="sig"><b>A bigger share of mentions here than across all markets:</b> ' + ', '.join(
        f'{html.escape(lab(C["c"][ci]))} ({100 * cnt[ci] / tot:.1f}% here vs {100 * WORLD_CNT[ci] / WORLD_T:.1f}%)' for ci in sig) + '</p>') if sig else ''
    if mid:
        m = MK[mid]
        base = f'{fmt(m["mn"])} venue mentions from {fmt(m["g"])} guests'
    else:
        base = f'{fmt(mentions)} venue mentions at {fmt(len(venues))} venues'
    tag = 'Deep market' if deep else 'Early signal'
    tag_html = f'<span class="mk-tag{"" if tag == "Deep market" else " early"}" title="{"30 or more guests" if tag == "Deep market" else "Fewer answers: read with care"}">{tag}</span>'
    vs = sorted((v for v in venues if v.get('y') != 'area'), key=lambda v: (-(v.get('m') or 0), v['n']))[:6]
    vl = ''.join(
        f'<li><a href="/map#venue-{v["i"]}"><span class="r">{r}</span><span class="vn">{html.escape(v["n"])}'
        f'<small>{html.escape(v["tw"] or v["c"])}{", " + html.escape(v["co"]) if v["co"] != "United Kingdom" else ""}</small></span><span class="vm" title="Named {v['m']} times">{100 * v["m"] / (mentions or 1):.1f}%</span></a></li>'
        for r, v in enumerate(vs, 1))
    return (f'<div class="mpane" role="tabpanel" id="p{i}" aria-labelledby="t{i}"{" hidden" if hidden else ""}>\n'
            f'  <div class="mcol"><h3>What guests name in {title} {tag_html}</h3><p class="sub">Share of the {fmt(tot)} dishes named at venues here · {base}. '
            f'"vs" marks a dish whose share here differs clearly from its share across all markets (shown where a dish is named at least {floor} times at three or more venues).</p>\n'
            f'  <ol class="hb">{rows}</ol>{sig_html}</div>\n'
            f'  <div class="mcol"><h3>Most-named venues</h3><p class="sub">Share of all venue mentions in this market</p><ol class="vlist">{vl}</ol>\n'
            f'  <a class="more" href="{more_href}">{more_text}</a></div>\n</div>')


def rank_list(lst, base=None):
    # shares of all interviews, not raw counts: the base grows every quarter
    base = base or int(str(N_ALL).replace(',', ''))
    return '<ol class="rk">' + ''.join(f'<li><span class="r">{i}</span><span class="t">{html.escape(t)}</span><span class="v">{100 * n / base:.1f}%</span></li>'
                                     for i, (t, n) in enumerate(lst[:6], 1)) + '</ol>'


# ---------------------------------------------------------------- index.html
menu = []
for k, c in (('s', 'Starter'), ('m', 'Main'), ('d', 'Side'), ('p', 'Dessert')):
    it = P['trends'][k]['cats'][0]
    menu.append((c, it.get('l') or lab(it['c']), 100 * it['n'] / SC['course_card_answers'][k]))
dl, dn = SC['drink_card']['c'][0]
menu.append(('Drink', dl, 100 * dn / SC['drink_card']['n']))
menu_html = '<ol>' + ''.join(f'<li><span class="c">{c}</span><span class="d">{html.escape(d)}</span><span class="dots"></span><span class="p">{pc0(p)}</span></li>' for c, d, p in menu) + '</ol>'
panes = '\n'.join(market_pane(i, t, pr, h, ht, mid, i > 0) for i, (t, pr, h, ht, mid) in enumerate(MARKET_SETS))
tabs = ('<div class="mtabs" role="tablist" aria-label="Market">' + ''.join(
    f'<button type="button" role="tab" id="t{i}" aria-controls="p{i}" aria-selected="{"true" if i == 0 else "false"}">{n}</button>'
    for i, n in enumerate(TAB_NAMES)) + '</div>')
edit('index.html', [
    (r'(speaking for themselves: trends from )[\d,]+( Dream Menu interviews)', rf'\g<1>{N_ALL}\g<2>'),
    (r'from places you actually go\. [\d,]+ interviews later', f'from places you actually go. {N_ALL} interviews later'),
    (r'(<div class="ms">as voted by )[\d,]+( guests</div>)', rf'\g<1>{N_ALL}\g<2>'),
    (r'(<div class="ms">as voted by [\d,]+ guests</div>\s*)<ol>.*?</ol>', lambda m: m.group(1) + menu_html),
    (r'<section class="h-stats" aria-label="In numbers"><div class="wrap">.*?</div></section>',
     '<section class="h-stats" aria-label="In numbers"><div class="wrap">\n'
     f'  <div><b>{N_ALL}</b><span>interviews</span></div>\n  <div><b>{fmt(M["mentions"])}</b><span>venue mentions</span></div>\n'
     f'  <div><b>{fmt(M["venues"])}</b><span>venues named</span></div>\n  <div><b>{M["cities"]}</b><span>cities</span></div>\n'
     f'  <div><b>{M["countries"]}</b><span>countries</span></div>\n</div></section>'),
    (r'<div class="cgrid">.*?</article></div>\n',
     lambda m: '<div class="cgrid">' + course_card('s', 'Starter') + course_card('m', 'Main') + course_card('d', 'Side')
     + course_card('p', 'Dessert') + drink_card() + '</div>\n'),
    (r'<div class="mpane" role="tabpanel" id="p0".*?See the world on the map →</a></div>\n</div>', lambda m: panes),
    (r'<div class="mtabs" role="tablist" aria-label="Market">.*?</div>', lambda m: tabs),
    (r'<p class="lede">What guests name in each market[^<]*</p>',
     '<p class="lede">What guests name in each market, the dishes each one names more than the rest, and the venues behind it. '
     'Glasgow, where the series started and most guests are based, is kept apart so it does not drown out everywhere else.</p>'),
    (r'<div class="dgrid">.*?</article></div>', lambda m: debates_home()),
    (r'(<h3>Guilty pleasures</h3><p class="sub">[^<]*</p>)<ol class="rk">.*?</ol>', lambda m: m.group(1) + rank_list(P['extra']['guilty'])),
    (r'(<h3>Bin it</h3><p class="sub">[^<]*</p>)<ol class="rk">.*?</ol>', lambda m: m.group(1) + rank_list(P['extra']['bin'])),
])

# ---------------------------------------------------------------- for-business.html: evidence cards and contact
CONTACT = 'contact.dreammenu@gmail.com'
INSTAGRAM = 'https://www.instagram.com/dream.menu/'
SAMPLE = '/case-studies/guests-and-critics'
_si = open('partner/intel-data.js', encoding='utf-8').read()
_mi = re.search(r'window\.DM_INTEL\s*=\s*', _si)
KPI = json.JSONDecoder().raw_decode(_si[_mi.end():])[0]['kpi']


def fb_cards():
    rows = ''.join(f'<li><span class="dish">{c}: {html.escape(d)}</span><span class="dots"></span><span class="price">{pc0(p)}</span></li>' for c, d, p in menu)
    top, rest, unplaced, cities, deep = city_cover()
    by_mk = [(m['n'] + (' (deep)' if deep(m) else ''), m['mn']) for m in top[:6]]
    by_mk.append((f'{len(cities) - 6} more cities and towns', sum(m['mn'] for m in cities[6:])))
    by_mk.append(('Chains and unplaced venues', unplaced))
    mk_rows = ''.join(f'<li><span class="dish">{n}</span><span class="dots"></span><span class="price">{fmt(c)}</span></li>' for n, c in by_mk)
    guest_award = sum(1 for p in _PL if p[15])
    guest_star_uk = sum(1 for p in _PL if p[15] and _star(p) and p[5] == 'GB')
    return (
        '<!--fb-cards--><section><div class="wrap">\n  <h2 id="evidence">The evidence, in brief</h2>\n  <div class="grid">\n'
        f'    <div class="card"><div class="eyebrow">The dream menu</div><h3 style="margin-top:6px">The top dish on every course</h3><ol class="menu">{rows}</ol>'
        f'<p class="note" style="margin-top:8px">Share of each course&rsquo;s answers, {N_ALL} interviews to {LAST_H}. <a href="/#courses">Every course in full</a></p></div>\n'
        f'    <div class="card"><div class="eyebrow">Where the evidence comes from</div><h3 style="margin-top:6px">Venue mentions by city</h3><ol class="menu">{mk_rows}</ol>'
        f'<p class="note" style="margin-top:8px">{len(cities)} cities and towns so far; Glasgow and Edinburgh are each deep enough to read on their own. <a href="/cities">Every city</a></p></div>\n'
        f'    <div class="card stat"><div class="eyebrow">What is moving</div><h3 style="margin-top:6px">{KPI["sig"]} clear movers</h3><p>Of {KPI["tests"]} dishes and groups tested, {KPI["sig"]} moved clearly between 2025 and 2026: {KPI["up"]} up and {KPI["down"]} down. '
        f'Partners see which ones, by course, market and guest type, with a score out of 10 for every trend.</p><a class="go" href="/login?next=/briefing">Partner briefing</a></div>\n'
        f'    <div class="card stat"><div class="eyebrow">Recognition</div><h3 style="margin-top:6px">Guests and guides</h3><p>{guest_award} venues guests name also hold a guide award; {guest_star_uk} of them are MICHELIN Starred venues in the UK. '
        f'The rest is the part of the market the guides do not see.</p><a class="go" href="{SAMPLE}">Read the free sample report</a></div>\n'
        '  </div>\n</div></section><!--/fb-cards-->')


def fb_proof():
    q = json.load(open('tools/data/testimonials.json', encoding='utf-8'))['quotes']
    if not q:
        return '<!--fb-proof--><!--/fb-proof-->'
    return ('<!--fb-proof--><section><div class="wrap"><h2 id="proof">What people say</h2><div class="grid">' + ''.join(
        f'<div class="card quote"><p>&ldquo;{html.escape(x["quote"])}&rdquo;</p><p class="note" style="margin-top:8px"><b>{html.escape(x["name"])}</b>, '
        f'{html.escape(x["role"])}, {html.escape(x["organisation"])}</p></div>' for x in q) + '</div></div></section><!--/fb-proof-->')


def fb_contact():
    return (
        '<!--fb-contact--><section><div class="wrap">\n  <h2 id="work">Work with us</h2>\n'
        '  <div class="grid fb-contact">\n'
        '    <div class="card"><h3>Start with the free sample</h3><p>No. 08 in the Insight Series, <b>Guests and critics</b>, is open to everyone: how far the venues guests love overlap with the guide award winners, with the data under every exhibit.</p>'
        f'<a class="go" href="{SAMPLE}">Read the sample report</a></div>\n'
        f'    <div class="card"><h3>Talk to us</h3><p>Partnerships, commissioned reports, the Restaurant MOT, data licences and press enquiries.</p>'
        f'<p style="margin-top:10px"><a href="mailto:{CONTACT}">{CONTACT}</a><br><a href="{INSTAGRAM}" rel="noopener" target="_blank">@dream.menu on Instagram</a></p></div>\n'
        '  </div>\n'
        f'  <form class="fb-form" id="enquiry" action="mailto:{CONTACT}" method="post" enctype="text/plain">\n'
        '    <h3>Send an enquiry</h3>\n'
        '    <div class="fb-row"><label>Your name<input name="name" autocomplete="name" required></label><label>Organisation<input name="organisation" autocomplete="organization"></label></div>\n'
        '    <div class="fb-row"><label>Email<input name="email" type="email" autocomplete="email" required></label>'
        '<label>Interested in<select name="topic"><option>A partnership</option><option>A commissioned report</option><option>The Restaurant MOT</option><option>A data licence</option><option>Press or research</option><option>Something else</option></select></label></div>\n'
        '    <label>What would you like to know?<textarea name="message" rows="4"></textarea></label>\n'
        '    <p><button class="cta" type="submit">Write the email</button></p>\n'
        f'    <p class="note">This opens an email to {CONTACT} in your own mail app, ready to send. Nothing is stored on this site. See the <a href="/privacy">privacy notice</a>.</p>\n'
        '  </form>\n'
        '<script>(function(){var f=document.getElementById("enquiry");if(!f)return;f.addEventListener("submit",function(e){e.preventDefault();var d=new FormData(f),g=function(k){return (d.get(k)||"").toString().trim()};'
        f'var sub="Dream Menu enquiry: "+g("topic")+(g("organisation")?" ("+g("organisation")+")":"");var body=g("message")+"\\n\\n"+g("name")+(g("organisation")?"\\n"+g("organisation"):"")+"\\n"+g("email");'
        f'location.href="mailto:{CONTACT}?subject="+encodeURIComponent(sub)+"&body="+encodeURIComponent(body)}})}})();</script>\n'
        '</div></section><!--/fb-contact-->')



# ---------------------------------------------------------------- home: where the evidence comes from, by city (Gordon, 31 Oct)
CITY_TOP = 10


def city_cover():
    """Venue mentions by city (where the venue is). Returns the top cities, the rest, and counts."""
    cities = sorted((m for m in D['markets'] if m['k'] == 'city'), key=lambda m: (-m['mn'], m['n']))
    deep = lambda m: m['g'] >= 30 and m['mn'] >= DEEP_MENTIONS
    top = cities[:CITY_TOP]
    rest = cities[CITY_TOP:]
    unplaced = M['mentions'] - sum(m['mn'] for m in cities)
    return top, rest, unplaced, cities, deep


def coverage_html():
    top, rest, unplaced, cities, deep = city_cover()
    n_deep = sum(1 for m in cities if deep(m))
    uk = sum(1 for m in cities if m['co'] == 'United Kingdom')
    abroad = len(cities) - uk
    place = lambda m: m['n'] if m['co'] == 'United Kingdom' else f"{m['n']}, {m['co']}"
    tiles = ''.join(
        f'<li class="{"deep" if deep(m) else ""}"><b>{html.escape(place(m))}</b><span class="cv-n">{fmt(m["mn"])}</span>'
        f'<span class="cv-s">venue mentions · {fmt(m["g"])} guests</span>'
        f'<span class="mk-tag{"" if deep(m) else " early"}">{"Deep" if deep(m) else "Early signal"}</span></li>'
        for m in top)
    tiles += (f'<li class="more"><b>{len(rest)} more cities and towns</b><span class="cv-n">{fmt(sum(m["mn"] for m in rest))}</span>'
              f'<span class="cv-s">venue mentions, including {html.escape(next((m["n"] for m in rest if m["co"] == "United Kingdom"), ""))} and {html.escape(next((m["n"] for m in rest if m["co"] != "United Kingdom"), ""))}</span></li>')
    deep_names = ' and '.join(html.escape(m['n']) for m in cities if deep(m))
    return ('<section class="h-cover" id="coverage"><div class="wrap"><div class="cv-head"><div><div class="eyebrow">Coverage</div>'
            '<h2>Where the evidence <em>comes from</em></h2>'
            f'<p class="lede">Guests have named venues in <b>{len(cities)} cities and towns</b>: {uk} in the UK and {abroad} abroad. '
            f'{deep_names} are each <b>deep</b> markets in their own right, so every finding can be read city by city. '
            'A city is deep once 30 or more guests have made 300 or more venue mentions there; below that it is an <b>early signal</b>, worth reading with care.</p></div>'
            '<a class="btn gold" href="/take-part">Add your city</a></div>'
            f'<ol class="cv-cities">{tiles}</ol><p class="note">Venue mentions by the city the venue is in, {N_ALL} interviews to {LAST_H}. '
            f'{fmt(unplaced)} further mentions are of chains or places guests did not tie to a city. Every figure on this site says which market it covers.</p></div></section>')


_ix = open('index.html', encoding='utf-8').read()
if 'class="h-cover"' in _ix:
    _ix2 = re.sub(r'<section class="h-cover".*?</section>', lambda m: coverage_html(), _ix, count=1, flags=re.S)
else:
    _ix2 = _ix.replace('<section class="audband"', coverage_html() + '\n<section class="audband"', 1)
if _ix2 != _ix:
    open('index.html', 'w', encoding='utf-8').write(_ix2)
    changed.append('index.html')

# ---------------------------------------------------------------- insights.html
iq = P['extra']['interviews_q']
qmax = max(iq)
qbars = ''.join(f'<div><span class="qv">{n}</span><i style="height:{round(100 * n / qmax)}%"></i><span class="ql">{q.replace("-", " ")}</span></div>'
                for q, n in zip(P['trends']['s']['q'], iq))
edit('insights.html', [
    (r'Every number here comes from [\d,]+ Dream Menu interviews, September 2025 to [^.]+\. Dish shares use the [\d,]+ interviews',
     f'Every number here comes from {N_ALL} Dream Menu interviews, September 2025 to {LAST_H}. Dish shares use the {fmt(P["n"])} interviews'),
    (r'(<h2 id="debates">The big debates</h2>\s*)<div class="grid">.*?(\n</div></section>)',
     lambda m: m.group(1) + debates_insights() + m.group(2)),
    (r'(<div class="qchart" role="img" aria-label="Interviews by quarter">).*?(</div>\s*<p class="note">)', lambda m: m.group(1) + qbars + m.group(2)),
    (r'<blockquote class="quote">([^<]*?)\., ([^<]+)</blockquote>', r'<blockquote class="quote">\1.<small>\2</small></blockquote>'),
], required=False)

# ---------------------------------------------------------------- other pages
edit('for-business.html', [
    (r'and where would you eat it\? [\d,]+ interviews later', f'and where would you eat it? {N_ALL} interviews later'),
    (r'<div class="facts"><div><b>[\d,]+</b> <span>interviews</span></div><div><b>[\d,]+</b> <span>venues named</span></div><div><b>[\d,]+</b> <span>venue mentions</span></div><div><b>\d+</b> <span>countries</span></div></div>',
     f'<div class="facts"><div><b>{N_ALL}</b> <span>interviews</span></div><div><b>{fmt(M["venues"])}</b> <span>venues named</span></div><div><b>{fmt(M["mentions"])}</b> <span>venue mentions</span></div><div><b>{M["countries"]}</b> <span>countries</span></div></div>'),
])
_fb = open('for-business.html', encoding='utf-8').read()
if '<!--fb-cards-->' not in _fb:      # first run: swap the old hand-made sections for generated ones
    _fb = re.sub(r'<section><div class="wrap">\s*<div class="grid">\s*<div class="card"><div class="eyebrow">Scotland, dish categories</div>.*?</div></section>', '<!--fb-cards--><!--/fb-cards-->', _fb, count=1, flags=re.S)
    _fb = re.sub(r'<section><div class="wrap prose">\s*<h2 id="work">Work with us</h2>.*?</div></section>', '<!--fb-contact--><!--/fb-contact-->', _fb, count=1, flags=re.S)
    open('for-business.html', 'w', encoding='utf-8').write(_fb)
if '<!--fb-proof-->' not in _fb:
    _fb = _fb.replace('<!--fb-contact-->', '<!--fb-proof--><!--/fb-proof-->\n<!--fb-contact-->', 1)
    open('for-business.html', 'w', encoding='utf-8').write(_fb)
edit('for-business.html', [(r'<!--fb-proof-->.*?<!--/fb-proof-->', lambda m: fb_proof()),
                           (r'<!--fb-cards-->.*?<!--/fb-cards-->', lambda m: fb_cards()),
                           (r'<!--fb-contact-->.*?<!--/fb-contact-->', lambda m: fb_contact())])
edit('how-it-works.html', [
    (r'[\d,]+ interviews are included, up to [^.]+\. Venues on the map come from (?:the same [\d,]+ interviews\.|the [\d,]+ interviews up to [^;]+; newer answers join the map at the next update\.) The dish figures in the analysis use the [\d,]+ interviews',
     f'{N_ALL} interviews are included, up to {LAST_H}. Venues on the map come from the same {fmt(M["interviews_mapped"])} interviews. The dish figures in the analysis use the {fmt(P["n"])} interviews'),
    (r'Of [\d,]+ venues named, [\d,]+ have a confirmed address and [\d,]+ an approximate one\.',
     f'Of {fmt(M["venues"])} venues named, {fmt(M["located"])} have a confirmed address and {fmt(M["approximate"])} an approximate one.'),
])
edit('onepager.html', [
    (r'(Dream Menu · partner summary · )[^<]+', rf'\g<1>{LAST_H}'),
    (r'<div class="facts"><div><b>[\d,]+</b> <span>interviews</span></div><div><b>[\d,]+</b> <span>venues named</span></div>',
     f'<div class="facts"><div><b>{N_ALL}</b> <span>interviews</span></div><div><b>{fmt(M["venues"])}</b> <span>venues named</span></div>'),
])
# briefing.html retired 13 Nov 2026: the partner briefing is the signed-in view of /analysis
# partner.html is written by tools/build_partner.py
edit('operators.html', [(r'(figures are from the live interviews to )[^,]+(, as shown)', rf'\g<1>{LAST_H}\g<2>')])
edit('map.html', [(r"(dream-menu interviews to )[^.]+\. Venues mapped from (?:every )?interviews? to [^,]+,",
                   rf"\g<1>{LAST_H}. Venues mapped from every interview to {LAST_H},")])
for fn in glob.glob('*.html') + glob.glob('report/*.html'):
    edit(fn, [(r'(<span>Dream Menu, Glasgow\. Data to )[^.]+(\.</span>)', rf'\g<1>{LAST_H}\g<2>')], required=False)

# ---------------------------------------------------------------- dm-fresh.js
edit('dm-fresh.js', [
    (r"interviews: \{ label: 'Dream Menu interviews', size: '[^']*', from: '2025-09-01', to: '[^']*', updated: '[^']*',\s*note: '[^']*' \}",
     f"interviews: {{ label: 'Dream Menu interviews', size: '{N_ALL} interviews', from: '2025-09-01', to: '{P['last']}', updated: '{TODAY}',\n"
     f"      note: 'Dish categories refined 24 Oct 2026. Interviews to {LAST_S} added {dt.date.fromisoformat(TODAY).strftime('%-d %b')}.' }}"),
    (r"venues: \{ label: 'Venues named by guests', size: '[^']*', from: '2025-09-01', to: '[^']*', updated: '[^']*',\s*note: '[^']*' \}",
     f"venues: {{ label: 'Venues named by guests', size: '{fmt(M['venues'])} venues, {fmt(M['pinned'])} pinned', from: '2025-09-01', to: '{M['interviews_to']}', updated: '{TODAY}',\n"
     f"      note: 'Addresses researched 22 Oct 2026; new venues added {dt.date.fromisoformat(TODAY).strftime('%-d %b')}.' }}"),
    (r"analysis: \{ label: 'Dream Menu analysis', size: '([^']*)', to: '[^']*', updated: '[^']*' \}",
     rf"analysis: {{ label: 'Dream Menu analysis', size: '\1', to: '{P['last']}', updated: '{TODAY}' }}"),
])
# ---------------------------------------------------------------- awards (from awards.js meta)
AW_FACTS = (f'<div class="facts"><div><b>{fmt(sum(1 for p in _PL if _star(p)))}</b> <span>MICHELIN Starred</span></div>'
            f'<div><b>{fmt(sum(1 for p in _PL if any(_G[a[0]] == "fifty" for a in p[10])))}</b> <span>on a 50 Best list</span></div>'
            f'<div><b>{fmt(sum(1 for p in _PL if p[15]))}</b> <span>also named by guests</span></div>'
            f'<div><b>{fmt(sum(1 for p in _PL if p[6] == "Scotland" and _star(p)))}</b> <span>starred in Scotland</span></div></div>')
AW_PLACES, AW_N, AW_BUILT = fmt(AWM['places']), fmt(AWM['awards']), AWM['built']
AW_H = dt.date.fromisoformat(AW_BUILT).strftime('%-d %b %Y')
# (the awards list page and its menu entry were retired 13 Nov 2026)
edit('index.html', [(r'<h3>[\d,]+ award winners</h3>', f'<h3>{AW_PLACES} award winners</h3>'),
                    (r'(<span class="eyebrow">Awards</span> )[\d,]+( award winners)', rf'\g<1>{AW_PLACES}\g<2>')], required=False)
# awards.html retired 13 Nov 2026: award winners are a layer on /map
edit('how-it-works.html', [(r'[\d,]+ recognised venues and [\d,]+ awards\.', f'{AW_PLACES} recognised venues and {AW_N} awards.')])
edit('analysis.js', [(r'Awards as listed on [^.]+\.', f'Awards as listed on {AW_H}.')])
edit('onepager.html', [(r'<b>[\d,]+</b> <span>award venues mapped</span>', f'<b>{AW_PLACES}</b> <span>award venues mapped</span>')])
edit('dm-fresh.js', [(r"awards: \{ label: 'Awards and guides', size: '[^']*', to: '[^']*', updated: '[^']*',",
                      f"awards: {{ label: 'Awards and guides', size: '{AW_PLACES} award winners', to: '{AW_BUILT}', updated: '{AW_BUILT}',")])

print('updated:', ', '.join(sorted(set(changed))))
