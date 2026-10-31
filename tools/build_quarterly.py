#!/usr/bin/env python3
"""Builds the public quarterly edition, the guest menus and the email sign-up boxes.

  /quarterly                 State of the Menu: the public headlines for the current quarter (quarterly.html),
                             plus a dated copy in quarterly/<yyyy-qn>.html for the archive
  /menus                     published guest menus, from tools/data/guest-menus.json (opt-in guests only)
  <!--signup-->...<!--/signup-->   the quarterly email sign-up box on every page that carries the markers,
                             wired to the Google Form in tools/data/signup.json (email fallback until it is set)

Public headlines only: no quarterly risers or fallers (Heads of Terms 3.3 and 3.4).
Run after refresh_static.py:  python3 tools/build_quarterly.py && python3 tools/build_nav.py
"""
import datetime as dt, glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P, D, L = load('partner-data.js', 'DM_PARTNER'), load('dm-data.js', 'DM'), load('dm-labels.js', 'DML')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
SIGN = json.load(open('tools/data/signup.json', encoding='utf-8'))
MENUS = json.load(open('tools/data/guest-menus.json', encoding='utf-8'))['menus']
E = lambda x: html.escape(str(x), quote=True)
fmt = lambda n: f'{n:,}'
lab = lambda c: (L.get(c) or [c])[0]
slugify = lambda s: re.sub(r'[^a-z0-9]+', '-', __import__('unicodedata').normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()).strip('-')
SITE, CONTACT = 'https://www.dream-menu.com', 'contact.dreammenu@gmail.com'
LAST = dt.date.fromisoformat(P['last'])
LAST_H = LAST.strftime('%-d %B %Y')
Q = f'{LAST.year}-Q{(LAST.month - 1) // 3 + 1}'
Q_H = f'Q{(LAST.month - 1) // 3 + 1} {LAST.year}'

# ---------------------------------------------------------------- sign-up box
def signup(where):
    fid, entry = SIGN.get('form_id'), SIGN.get('email_entry')
    if fid and entry:
        form = (f'<form class="su-form" action="https://docs.google.com/forms/d/e/{E(fid)}/formResponse" method="post" target="su-{where}">'
                f'<label class="sr" for="su-e-{where}">Email</label><input id="su-e-{where}" type="email" name="{E(entry)}" placeholder="you@example.com" required autocomplete="email">'
                f'<button class="cta" type="submit">Sign up</button></form><iframe name="su-{where}" title="Sign-up" hidden></iframe>'
                '<p class="su-done" hidden>Thanks: you are on the list for the next edition.</p>')
        js = ('<script>document.querySelectorAll(".su-form").forEach(function(f){f.addEventListener("submit",function(){setTimeout(function(){'
              'f.hidden=true;f.parentNode.querySelector(".su-done").hidden=false},400)})})</script>')
    else:
        form = (f'<p><a class="cta" href="mailto:{CONTACT}?subject=Subscribe%20to%20State%20of%20the%20Menu&body=Please%20add%20me%20to%20the%20quarterly%20edition.">Sign up by email</a></p>')
        js = ''
    return (f'<!--signup--><section class="su"><div class="wrap su-in"><div><div class="eyebrow">Quarterly email</div><h2>State of the Menu, <em>every quarter</em></h2>'
            '<p>The public headlines four times a year: what guests choose, the debates, the venues they name and where the evidence is growing. No spam; unsubscribe any time.</p></div>'
            f'<div class="su-box">{form}<p class="su-note">We keep your email only to send the edition. See the <a href="/privacy">privacy notice</a>.</p></div></div></section>{js}<!--/signup-->')


# ---------------------------------------------------------------- page shell
TPL = open('restaurant-mot.html', encoding='utf-8').read()
HEAD, FOOT = TPL[:TPL.find('<main>')], TPL[TPL.find('</main>') + len('</main>'):]
HEAD = HEAD.replace('<link rel="stylesheet" href="/brand.css">', '<link rel="stylesheet" href="/brand.css">\n<link rel="stylesheet" href="/pages.css">', 1)


def page(path, title, desc, body):
    h = re.sub(r'<title>[^<]*</title>', f'<title>{E(title)}</title>', HEAD)
    for prop in ('name="description"', 'property="og:description"'):
        h = re.sub(r'(<meta ' + prop + r' content=")[^"]*', lambda m: m.group(1) + E(desc), h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(title), h)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + SITE + path, h)
    fn = path.strip('/') + '.html'
    os.makedirs(os.path.dirname(fn) or '.', exist_ok=True)
    open(fn, 'w', encoding='utf-8').write(h + '<main class="pg">\n' + body + '\n</main>' + FOOT)
    return fn


# ---------------------------------------------------------------- State of the Menu
qi = P['trends']['s']['q'].index(Q) if Q in P['trends']['s']['q'] else -1
n_q = P['extra']['interviews_q'][qi] if qi >= 0 else 0
menu = []
for k, c in (('s', 'Starter'), ('m', 'Main'), ('d', 'Side'), ('p', 'Dessert')):
    T = P['trends'][k]
    a, b = T['cats'][0], T['cats'][1]
    menu.append((c, a.get('l') or lab(a['c']), 100 * a['n'] / SC['course_card_answers'][k], b.get('l') or lab(b['c']), 100 * b['n'] / SC['course_card_answers'][k]))
dc = SC['drink_card']
menu.append(('Drink', dc['c'][0][0], 100 * dc['c'][0][1] / dc['n'], dc['c'][1][0], 100 * dc['c'][1][1] / dc['n']))
deb = SC['debates']
tap = deb['water']['c']['Tap'] + deb['water']['c'].get('Scottish tap water', 0)
pc = lambda a, b: f'{round(100 * a / b)}%'
MK = {m['id']: m for m in D['markets']}
_cities = sorted((m for m in D['markets'] if m['k'] == 'city'), key=lambda m: (-m['mn'], m['n']))
cov = [(m['n'] + (' (deep)' if m['g'] >= 30 and m['mn'] >= 300 else ''), m['mn']) for m in _cities[:5]] + [(f'{len(_cities) - 5} more cities and towns', sum(m['mn'] for m in _cities[5:]))]
dish_link = lambda l: f'<a href="/trends/{slugify(l)}">{E(l)}</a>' if os.path.exists(f'trends/{slugify(l)}.html') else E(l)
rows = ''.join(f'<tr><td>{c}</td><td><b>{dish_link(a)}</b> {pa:.0f}%</td><td>{dish_link(b)} {pb:.0f}%</td></tr>' for c, a, pa, b, pb in menu)
gla = MK.get('city:Glasgow|United Kingdom')
top_v = [v for v in D['venues'] if gla and v['i'] in gla['top'][:5]]
top_v.sort(key=lambda v: -v['m'])
vlink = lambda v: f'<a href="/venue/{re.sub(r"-x$", "", v["i"])}">{E(v["n"])}</a>' if os.path.exists(f'venue/{re.sub(r"-x$", "", v["i"])}.html') else E(v['n'])
body = f'''<section class="pg-hero"><div class="wrap"><p class="eyebrow">State of the Menu · {Q_H}</p><h1>The quarter <em>in food</em></h1>
<p class="lede">The public headlines from {fmt(P["n_all"])} Dream Menu interviews, with {fmt(n_q)} new ones this quarter so far (data to {LAST_H}). Partners get the movement behind them in the quarterly briefing.</p>
<div class="pg-facts"><div><b>{fmt(P["n_all"])}</b><span>interviews</span></div><div><b>{fmt(n_q)}</b><span>this quarter so far</span></div><div><b>{fmt(D["meta"]["venues"])}</b><span>venues named</span></div><div><b>{D["meta"]["countries"]}</b><span>countries</span></div></div></div></section>
<section><div class="wrap pg-grid">
  <div class="card"><h2>The dream menu right now</h2><div class="tablewrap" style="border:0"><table><thead><tr><th>Course</th><th>Leads</th><th>Runner-up</th></tr></thead><tbody>{rows}</tbody></table></div><p class="pg-mut">Share of each course&rsquo;s answers, all interviews. <a href="/trends">Every dish</a></p></div>
  <div class="card"><h2>The debates</h2><ul class="pg-list"><li>Irn-Bru beats Coca-Cola, {pc(deb["coke"]["c"]["Irn Bru"], deb["coke"]["n"])} to {pc(deb["coke"]["c"]["Coca Cola"], deb["coke"]["n"])}</li><li>Coffee over tea, {pc(deb["tea"]["c"]["Coffee"], deb["tea"]["n"])} to {pc(deb["tea"]["c"]["Tea"], deb["tea"]["n"])}</li><li>Pineapple on pizza: {pc(deb["pineapple"]["c"]["No"], deb["pineapple"]["n"])} say no</li><li>Water: still {pc(deb["water"]["c"]["Still"], deb["water"]["n"])}, tap {pc(tap, deb["water"]["n"])}</li></ul><p class="pg-mut"><a href="/#debates">All four debates</a></p></div>
  <div class="card"><h2>What guests want gone</h2><ol class="pg-list">{"".join(f"<li>{E(t)} <b>{n}</b></li>" for t, n in P["extra"]["bin"][:5])}</ol><p class="pg-mut">Answers to &ldquo;which trend would you bin?&rdquo;</p></div>
  <div class="card"><h2>Most-named venues</h2><ol class="pg-list">{"".join(f"<li>{vlink(v)} <b>{v['m']}</b></li>" for v in top_v)}</ol><p class="pg-mut"><a href="/rankings">Rankings by market and course</a></p></div>
  <div class="card"><h2>Where the evidence is growing</h2><ul class="pg-list">{"".join(f"<li>{n}: {fmt(c)} venue mentions</li>" for n, c in cov)}</ul><p class="pg-mut">Glasgow and Edinburgh are each deep markets; the other cities are early signals. <a href="/#coverage">Every city</a> · <a href="/take-part">Add your city</a></p></div>
  <div class="card pg-lock"><h2>What is moving</h2><p>Which dishes are clearly rising or falling, by course and market, with a trend score out of 10, is in the partner briefing.</p><p><a class="go" href="/login?next=/briefing">Partner briefing</a> · <a class="go" href="/for-business#work">Become a partner</a></p></div>
</div></section>
<section><div class="wrap"><p class="pg-src">Source: Dream Menu, {fmt(P["n_all"])} interviews, September 2025 to {LAST_H}. Qualitative fieldwork with a large base, not a representative survey. Credit: Dream Menu (dream-menu.com). <a href="/press">Press kit</a></p>
<p class="pg-mut">Editions: {" · ".join(f'<a href="/quarterly/{os.path.basename(f)[:-5]}">{os.path.basename(f)[:-5].upper().replace("-", " ")}</a>' for f in sorted(set(glob.glob("quarterly/*.html")) | {f"quarterly/{Q.lower()}.html"}))}</p></div></section>
<!--signup--><!--/signup-->'''
written = [page('/quarterly', f'State of the Menu, {Q_H} | Dream Menu', f'The quarter in food from {fmt(P["n_all"])} Dream Menu interviews: the dream menu, the debates, the trends guests want gone and the venues they name.', body),
           page(f'/quarterly/{Q.lower()}', f'State of the Menu, {Q_H} | Dream Menu', f'Dream Menu quarterly edition, {Q_H}.', body)]

# ---------------------------------------------------------------- guest menus (opt-in only)
if MENUS:
    cards = ''.join(
        f'<article class="card gm"><p class="eyebrow">{E(m.get("role", ""))} · {E(m.get("city", ""))}</p><h2>{E(m["name"])}&rsquo;s dream menu</h2>'
        '<ol class="gm-list">' + ''.join(f'<li><span>{E(c)}</span><b>{dish_link(d)}</b><em>{E(v)}</em></li>' for c, d, v in m['menu']) + '</ol>'
        + (f'<p class="pg-mut"><a href="https://www.instagram.com/{E(m["handle"])}/" rel="noopener" target="_blank">@{E(m["handle"])}</a></p>' if m.get('handle') else '') + '</article>'
        for m in sorted(MENUS, key=lambda m: m.get('date', ''), reverse=True))
    body = (f'<section class="pg-hero"><div class="wrap"><p class="eyebrow">Guest menus</p><h1>Dream menus, <em>in full</em></h1>'
            f'<p class="lede">Menus from guests who chose to be named. {len(MENUS)} so far; every other answer is counted anonymously in the trends.</p></div></section>'
            f'<section><div class="wrap pg-grid">{cards}</div></section><section><div class="wrap"><p><a class="cta" href="/take-part">Add your dream menu</a></p></div></section>')
    written.append(page('/menus', 'Guest dream menus | Dream Menu', 'Dream menus from named guests: five courses and the venue that does each best.', body))
elif os.path.exists('menus.html'):
    os.remove('menus.html')

# ---------------------------------------------------------------- sign-up boxes on every page with markers
n = 0
for fn in glob.glob('*.html') + glob.glob('quarterly/*.html'):
    s = open(fn, encoding='utf-8').read()
    if '<!--signup-->' in s:
        s2 = re.sub(r'<!--signup-->.*?<!--/signup-->', lambda m: signup(slugify(fn)), s, flags=re.S)
        if s2 != s:
            open(fn, 'w', encoding='utf-8').write(s2)
            n += 1

sm = open('sitemap.xml', encoding='utf-8').read()
sm = re.sub(r'\s*<url><loc>https://www\.dream-menu\.com/(?:quarterly|menus)[^<]*</loc>[^\n]*</url>', '', sm)
sm = sm.replace('\n</urlset>', ''.join(f'\n  <url><loc>{SITE}/{f[:-5]}</loc><lastmod>{P["last"]}</lastmod></url>' for f in written) + '\n</urlset>')
open('sitemap.xml', 'w', encoding='utf-8').write(sm)
print('wrote', written, '| sign-up boxes', n, '| guest menus', len(MENUS), '| sign-up form', 'set' if SIGN.get('form_id') else 'not set (email fallback)')
