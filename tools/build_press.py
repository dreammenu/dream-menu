#!/usr/bin/env python3
"""Builds /press (press.html): quotable figures from the live data, how to credit Dream Menu, the method in brief,
logo downloads and the contact. Every figure is read from the site's data files, so rerun after each refresh:

  python3 tools/build_press.py && python3 tools/build_nav.py

Only public headline figures appear here (Heads of Terms: headlines public, depth locked). No quarterly movers.
"""
import datetime as dt, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P, D, C, L = load('partner-data.js', 'DM_PARTNER'), load('dm-data.js', 'DM'), load('dm-cat.js', 'DMC'), load('dm-labels.js', 'DML')
A = load('awards.js', 'DM_AWARDS')
SC = json.load(open('tools/data/static-counts.json', encoding='utf-8'))
M = D['meta']
E = lambda x: html.escape(str(x), quote=True)
fmt = lambda n: f'{n:,}'
pc = lambda a, b: f'{round(100 * a / b)}%'
lab = lambda c: (L.get(c) or [c])[0]
LAST = dt.date.fromisoformat(P['last'])
LAST_H = LAST.strftime('%-d %B %Y')
CONTACT = 'contact.dreammenu@gmail.com'

# ---------------------------------------------------------------- figures
deb = SC['debates']
tap = deb['water']['c']['Tap'] + deb['water']['c'].get('Scottish tap water', 0)
top = {}
for k in ('s', 'm', 'd', 'p'):
    it = P['trends'][k]['cats'][0]
    top[k] = (it.get('l') or lab(it['c']), pc(it['n'], SC['course_card_answers'][k]))
dl, dn = SC['drink_card']['c'][0]
guest_award = sum(1 for p in A['places'] if p[15])
MK = {m['id']: m for m in D['markets']}


def city_index(mid, name):
    """The dish a city names most above the all-market share (five or more mentions)."""
    w = {ci: n for ci, n, _ in C['m']['world:World']}
    cnt, wt = {}, {}
    for i, v in enumerate(D['venues']):
        for ci, n in C['v'].get(str(i)) or []:
            wt[ci] = wt.get(ci, 0) + n
            if (v['c'], v['co']) == (name, 'United Kingdom'):
                cnt[ci] = cnt.get(ci, 0) + n
    T, WT = sum(cnt.values()), sum(wt.values())
    best = max((ci for ci in cnt if cnt[ci] >= 5), key=lambda ci: (cnt[ci] / T) / (wt[ci] / WT))
    return lab(C['c'][best]), (cnt[best] / T) / (wt[best] / WT)


edi_dish, edi_x = city_index('city:Edinburgh|United Kingdom', 'Edinburgh')
gla_dish, gla_x = city_index('city:Glasgow|United Kingdom', 'Glasgow')
top_v = [v for v in D['venues'] if v['i'] == MK['city:Glasgow|United Kingdom']['top'][0]][0]

FACTS = [
    (pc(deb['coke']['c']['Irn Bru'], deb['coke']['n']), f'choose Irn-Bru over Coca-Cola ({fmt(deb["coke"]["n"])} answers)'),
    (pc(deb['pineapple']['c']['No'], deb['pineapple']['n']), f'say no to pineapple on pizza: the closest debate on the menu'),
    (pc(deb['tea']['c']['Coffee'], deb['tea']['n']), f'pick coffee over tea ({fmt(deb["tea"]["n"])} answers)'),
    (pc(tap, deb['water']['n']), 'ask for tap water with dinner, close behind still at ' + pc(deb['water']['c']['Still'], deb['water']['n'])),
    (top['p'][1], f'name {top["p"][0].lower()} as their dream dessert, the most-named single dish on any course'),
    (top['s'][1], f'choose {top["s"][0].lower()} to start'),
    (f'×{edi_x:.1f}', f'Edinburgh names the {edi_dish.lower()} {edi_x:.1f} times as often as guests overall'),
    (f'{P["extra"]["bin"][0][1]}', f'guests want {P["extra"]["bin"][0][0].lower()} binned: the trend they are most tired of'),
    (f'{P["extra"]["guilty"][0][1]}', f'name {P["extra"]["guilty"][0][0].lower()} as their guilty pleasure, the top answer'),
    (fmt(guest_award), 'venues guests name also hold a MICHELIN, 50 Best or guide award'),
]
cards = ''.join(f'<div class="card stat"><b>{E(v)}</b><span>{E(t)}</span>'
                f'<button type="button" class="pr-copy" data-q="{E(v + " " + t + ". Source: Dream Menu, " + str(fmt(P["n_all"])) + " interviews to " + LAST_H + ".")}">Copy with source</button></div>'
                for v, t in FACTS)

body = f'''<section class="navyband"><div class="wrap">
  <div class="eyebrow">Press and researchers</div>
  <h1>Press <em>kit</em></h1>
  <p class="lede">Dream Menu asks chefs, creators and people who love eating out one question: build your dream menu, one dish per course, from places you actually go. {fmt(P["n_all"])} interviews later, these are the figures most worth quoting, how to credit them and who to call.</p>
</div></section>
<section><div class="wrap">
  <h2 id="figures">Figures worth quoting</h2>
  <p class="lede" style="margin-bottom:14px">From {fmt(P["n_all"])} Dream Menu interviews, September 2025 to {LAST_H}. Each card copies the figure with its source line.</p>
  <div class="grid pr-grid">{cards}</div>
  <p class="note" style="margin-top:12px">Glasgow&rsquo;s most-named venue is {E(top_v["n"])} ({top_v["m"]} mentions). Glasgow over-indexes on {E(gla_dish.lower())} (×{gla_x:.1f}). More on the <a href="/">food trends page</a>, the <a href="/analysis">analysis</a> and the <a href="/rankings">rankings</a>.</p>
</div></section>
<section><div class="wrap prose">
  <h2 id="credit">How to credit</h2>
  <p>Please credit <b>Dream Menu (dream-menu.com)</b> and give the base and date, for example: <em>Source: Dream Menu, {fmt(P["n_all"])} interviews to {LAST_H}.</em> Link to the page the figure came from where you can.</p>
  <h2 id="method">The method in brief</h2>
  <p>Guests answer the same questions through Instagram: a starter, main, side, dessert and drinks, and the venue that does each best, plus a hidden gem and four debates. Answers are coded by hand to {len(C["c"])} dish categories. Venues are matched and placed on the map ({fmt(M["pinned"])} of {fmt(M["venues"])} pinned). It is qualitative fieldwork with a large base, not a statistically representative survey: guests are weighted towards Glasgow and towards people who work in or write about food. Movement over time is only called when it passes a two-proportion test. <a href="/how-it-works">Full method</a>.</p>
  <h2 id="assets">Logo and images</h2>
  <p><a href="/logo-256.png" download>Dream Menu badge (PNG, 256 px)</a> · <a href="/og.png" download>Share image (PNG)</a> · <a href="/map-preview.png" download>Venue map preview (PNG)</a></p>
  <h2 id="contact">Contact</h2>
  <p>Gordon Best, founder. <a href="mailto:{CONTACT}?subject=Press%20enquiry">{CONTACT}</a> · <a href="https://www.instagram.com/dream.menu/" rel="noopener" target="_blank">@dream.menu</a>. Interviews, custom cuts of the data and comment on Scottish hospitality on request.</p>
</div></section>
<script>document.querySelectorAll('.pr-copy').forEach(function(b){{b.addEventListener('click',function(){{var t=b.getAttribute('data-q');
(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){{b.textContent='Copied'}},function(){{prompt('Copy this line',t)}});setTimeout(function(){{b.textContent='Copy with source'}},2000)}})}})</script>'''

TPL = open('restaurant-mot.html', encoding='utf-8').read()
head, foot = TPL[:TPL.find('<main>')], TPL[TPL.find('</main>') + len('</main>'):]
title, desc = 'Press kit | Dream Menu', f'Quotable figures from {fmt(P["n_all"])} Dream Menu interviews, how to credit them, the method in brief, logos and the press contact.'
head = re.sub(r'<title>[^<]*</title>', f'<title>{E(title)}</title>', head)
for prop in ('name="description"', 'property="og:description"'):
    head = re.sub(r'(<meta ' + prop + r' content=")[^"]*', lambda m: m.group(1) + E(desc), head)
head = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(title), head)
head = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>https://www.dream-menu.com/press', head)
open('press.html', 'w', encoding='utf-8').write(head + '<main>\n' + body + '\n</main>' + foot)
print('wrote press.html:', [f for f, _ in FACTS])
