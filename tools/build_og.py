"""Share images (17 Nov 2026): the picture a link shows on WhatsApp, LinkedIn, iMessage and so on.

  og.png                     the site-wide card (headline and current totals), used by every page without its own
  og/<kind>/<slug>.png       one card per venue, city guide, neighbourhood guide and dish trend page

Then sets og:image (and twitter:image) on those pages. Run after the page builders, before build_nav.py:
  python3 tools/build_og.py

Cards carry no percentages, so a venue's card only changes when its name, place or named dishes change; an image is
rewritten only when its text changes (tools/data/og-manifest.json), which keeps the repository small.
"""
import glob
import hashlib
import html
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
INK, NAVY, GOLD, WHITE, MUTED = (11, 11, 11), (28, 33, 82), (222, 189, 26), (255, 255, 255), (90, 94, 110)
F = 'tools/fonts/'
def font(name, size): return ImageFont.truetype(F + name + '.ttf', size)
HEAD = 'league-spartan-latin-800-normal'
BODY = 'public-sans-latin-400-normal'
BOLD = 'public-sans-latin-700-normal'
LOGO = Image.open('logo-256.png').convert('RGBA')
SITE = 'https://www.dream-menu.com'
MANI = 'tools/data/og-manifest.json'


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def card(path, eyebrow, title, sub, foot):
    im = Image.new('RGB', (W, H), WHITE)
    d = ImageDraw.Draw(im)
    x, maxw = 64, 820
    d.rectangle([x, 70, x + 30, 74], fill=GOLD)
    d.text((x + 44, 59), eyebrow.upper(), font=font(BOLD, 22), fill=INK)
    # title and subline: the largest title that fits in three lines and leaves room above the black band
    fs = font(BODY, 30)
    sub_lines = wrap(d, sub, fs, maxw)[:2] if sub else []
    for size in (104, 92, 80, 70, 60, 52, 46):
        f = font(HEAD, size)
        lines = wrap(d, title.upper(), f, maxw)
        fits = len(lines) <= 3 and all(d.textlength(l, font=f) <= maxw for l in lines)
        if fits and 112 + len(lines) * int(size * 0.98) + len(sub_lines) * 44 + 20 <= 490:
            break
    lines = lines[:3]
    y = 112
    for i, l in enumerate(lines):
        d.text((x, y), l, font=f, fill=NAVY if i == len(lines) - 1 and len(lines) > 1 else INK)
        y += int(size * 0.98)
    y += 14
    for l in sub_lines:
        d.text((x, y), l, font=fs, fill=MUTED)
        y += 44
    lg = LOGO.resize((210, 210))
    im.paste(lg, (W - 64 - 210, 150), lg)
    d.rectangle([0, 510, W, H], fill=INK)
    d.text((x, 552), foot, font=font(BODY, 27), fill=WHITE)
    fr = font(BOLD, 27)
    d.text((W - 64 - d.textlength('dream-menu.com', font=fr), 552), 'dream-menu.com', font=fr, fill=WHITE)
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    # a fixed palette keeps the brand colours exact and the files small
    pal = Image.new('P', (1, 1))
    ramp = []
    for c in (INK, NAVY, GOLD, MUTED):
        for t in range(16):
            ramp += [round(c[k] + (255 - c[k]) * t / 15) for k in range(3)]
    pal.putpalette(ramp + [0] * (768 - len(ramp)))
    body = im.crop((0, 0, W, H))
    logo_box = (W - 64 - 210, 150, W - 64, 360)
    q = body.quantize(palette=pal, dither=Image.Dither.NONE).convert('RGB')
    q.paste(im.crop(logo_box), logo_box[:2])
    q.quantize(colors=128, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(path, optimize=True)


def set_meta(fn, url):
    s = open(fn, encoding='utf-8').read()
    s2 = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{url}">', s)
    if '<meta name="twitter:image"' in s2:
        s2 = re.sub(r'<meta name="twitter:image" content="[^"]*">', f'<meta name="twitter:image" content="{url}">', s2)
    else:
        s2 = s2.replace('<meta name="twitter:card"', f'<meta name="twitter:image" content="{url}">\n<meta name="twitter:card"', 1)
    if s2 != s:
        open(fn, 'w', encoding='utf-8').write(s2)


def h1(fn):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', open(fn, encoding='utf-8').read(), re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''


def main():
    mani = json.load(open(MANI)) if os.path.exists(MANI) else {}
    new = {}
    D = load('dm-data.js', 'DM')
    meta = D['meta']
    VS = {re.sub(r'-x$', '', v['i']): v for v in D['venues']}

    jobs = [('og.png', 'Dream Menu', 'Foodies, speaking for themselves',
             'UK food trends from the people who cook, serve and eat out',
             f'{meta["interviews"]:,} interviews · {meta["venues"]:,} venues named · {meta["cities"]} cities', None)]
    for fn in sorted(glob.glob('venue/*.html')):
        s = os.path.basename(fn)[:-5]
        v = VS.get(s)
        if not v:
            continue
        dishes = [x for x in (v.get('d') or []) if len(x) < 40][:2]
        jobs.append((f'og/venue/{s}.png', f'Venue · {v["c"] or v["co"]}', v['n'],
                     ('Guests name: ' + ', '.join(dishes)) if dishes else 'What Dream Menu guests order there, and why',
                     'Foodies, speaking for themselves', fn))
    for fn in sorted(glob.glob('city/*.html')):
        t = h1(fn)
        jobs.append((f'og/city/{os.path.basename(fn)[:-5]}.png', 'City guide', t,
                     'The places foodies name most, hidden gems and award holders', 'Foodies, speaking for themselves', fn))
    for fn in sorted(glob.glob('area/*.html')):
        t = h1(fn)
        jobs.append((f'og/area/{os.path.basename(fn)[:-5]}.png', 'Neighbourhood guide', t,
                     'Where foodies eat, from Dream Menu interviews', 'Foodies, speaking for themselves', fn))
    for fn in sorted(glob.glob('trends/*.html')):
        t = h1(fn)
        jobs.append((f'og/trends/{os.path.basename(fn)[:-5]}.png', 'Dish trend', t,
                     'How often guests choose it, quarter by quarter, and where', 'Foodies, speaking for themselves', fn))

    made = 0
    for path, eb, title, sub, foot, page in jobs:
        key = hashlib.md5('|'.join([eb, title, sub, foot, 'v2']).encode()).hexdigest()[:12]
        new[path] = key
        if mani.get(path) != key or not os.path.exists(path):
            card(path, eb, title, sub, foot)
            made += 1
        if page:
            set_meta(page, f'{SITE}/{path}')
    # remove cards for pages that no longer exist
    for p in set(mani) - set(new):
        if p.startswith('og/') and os.path.exists(p):
            os.remove(p)
    json.dump(new, open(MANI, 'w'), indent=0, sort_keys=True)
    print(f'share images: {len(jobs)} cards, {made} redrawn')


if __name__ == '__main__':
    main()
