#!/usr/bin/env python3
"""Writes the public email digest from the home page's "This quarter" cards:
tools/data/digest/<data date>.txt and .html. Public figures only, so it is safe for the sign-up list.
The weekly refresh puts it into Gmail as a draft with no recipients, for Gordon to check and send.

Run after build_home.py:  python3 tools/build_digest.py
"""
import datetime as dt, html, json, os, re

s = open('index.html', encoding='utf-8').read()
t = open('trend-public.js', encoding='utf-8').read()
M = json.JSONDecoder().raw_decode(t[t.index('{'):])[0]['meta']
sec = re.search(r'<section class="h-sec" id="now">.*?</section>', s, re.S).group(0)
txt = lambda x: html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x))).strip()
cards = []
for m in re.finditer(r'<article class="hf-card([^"]*)">.*?<h3>(.*?)</h3><p>(.*?)</p><p class="hf-do"><b>What to do</b>(.*?)</p><a class="hf-more" href="([^"]+)"', sec, re.S):
    cards.append(dict(ext='hf-ext' in m.group(1), h=txt(m.group(2)), p=txt(m.group(3)), do=txt(m.group(4)), u='https://www.dream-menu.com' + m.group(5)))
if len(cards) < 3:
    raise SystemExit('digest: fewer than three findings found on the home page')
d = dt.date.fromisoformat(M['last'])
when = f'{d.day} {d.strftime("%B %Y")}'
subject = f'Dream Menu: {cards[0]["h"][0].lower() + cards[0]["h"][1:]}, and two more findings'
intro = f'What {M["n_all"]:,} food-led guests are telling us, to {when}. Three findings and what to do about each.'
more = [('Check my menu', 'Tick your dishes and see how much of what guests want you cover.', '/menu-check'),
        ('City and neighbourhood guides', 'Where foodies eat, from Finnieston to Leith.', '/cities'),
        ('Build your dream menu', 'Pick six courses and see who agrees.', '/my-dream-menu')]
lines = [subject, '', intro, '']
for i, c in enumerate(cards, 1):
    lines += [('Outside check: ' if c['ext'] else f'{i}. ') + c['h'], c['p'], 'What to do: ' + c['do'], c['u'], '']
lines += ['Also on the site'] + [f'- {a}: {b} https://www.dream-menu.com{u}' for a, b, u in more]
lines += ['', 'Qualitative fieldwork with a large base, not a representative survey. Reply to this email to stop receiving it.']
E = html.escape
h = (f'<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;color:#0b0b0b;line-height:1.5">'
     f'<div style="border-top:1px solid #0b0b0b"><div style="width:46px;height:5px;background:#debd1a"></div></div>'
     f'<p style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#5b5b5f;margin:14px 0 4px">Dream Menu · {when}</p>'
     f'<h1 style="font-size:24px;line-height:1.2;margin:0 0 10px">Foodies, speaking for themselves</h1><p style="margin:0 0 18px">{E(intro)}</p>'
     + ''.join(f'<div style="border-top:1px solid #d9d9d6;padding:14px 0"><p style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#5b5b5f;margin:0 0 4px">{"Outside check" if c["ext"] else "Finding " + str(i)}</p>'
               f'<h2 style="font-size:18px;line-height:1.25;margin:0 0 6px">{E(c["h"])}</h2><p style="margin:0 0 8px">{E(c["p"])}</p>'
               f'<p style="margin:0 0 8px;border-left:3px solid #debd1a;padding-left:10px"><b>What to do:</b> {E(c["do"])}</p><a href="{c["u"]}" style="color:#1c2152;font-weight:bold">See the evidence</a></div>'
               for i, c in enumerate(cards, 1))
     + '<div style="border-top:1px solid #0b0b0b;padding:14px 0"><p style="font-weight:bold;margin:0 0 6px">Also on the site</p>'
     + ''.join(f'<p style="margin:0 0 6px"><a href="https://www.dream-menu.com{u}" style="color:#1c2152;font-weight:bold">{a}</a>: {b}</p>' for a, b, u in more)
     + '</div><p style="font-size:12px;color:#5b5b5f">Qualitative fieldwork with a large base, not a representative survey. Reply to this email to stop receiving it.</p></div>')
os.makedirs('tools/data/digest', exist_ok=True)
base = f'tools/data/digest/{M["last"]}'
open(base + '.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
open(base + '.html', 'w', encoding='utf-8').write(h + '\n')
print(f'digest: {base}.txt and .html | subject: {subject}')
