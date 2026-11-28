#!/usr/bin/env python3
"""Public views of the partner pages: text open to everyone, charts and data tables for partners.

The full pages stay where they are (report chapters, operator toolkit, tested ideas, Insight Series)
and are only ever served to signed-in partners. This script writes a public copy of each one under
/open/ with every chart, exhibit and numeric data table swapped for a grey placeholder that carries a
sign-in link. middleware.js sends signed-out visitors to the /open/ copy at the same address, so the
chart figures never reach a browser that has not signed in.

Run it last, after tools/build_nav.py, so the copies carry the current header and footer.
Usage: python3 tools/build_gate.py
"""
import glob, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 'open'
SITE = 'https://www.dream-menu.com'
FREE = {'case-studies/guests-and-critics.html'}          # the free sample stays fully open as before

def pages():
    ps = ['operators.html', 'tested-ideas.html', 'case-studies.html']
    ps += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, 'report', '*.html')))
    ps += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, 'case-studies', '*.html')))
    return [p for p in ps if p not in FREE]

# Public pages whose charts are for partners too (28 Nov 2026): the home page, every dish page, State of the
# Menu and Specials. Their words stay open; middleware.js serves the /open/ copy to signed-out visitors.
def chart_pages():
    ps = ['index.html', 'quarterly.html', 'specials.html']
    for d in ('quarterly', 'trends'):
        ps += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, d, '*.html')))
    return ps

def url_of(path):
    u = '/' + re.sub(r'\.html$', '', path)
    return '/' if u == '/index' else u

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>')

def cls(attrs):
    m = re.search(r'\bclass\s*=\s*"([^"]*)"', attrs)
    return m.group(1).split() if m else []

def attr(attrs, name):
    m = re.search(r'\b' + name + r'\s*=\s*"([^"]*)"', attrs)
    return m.group(1) if m else ''

def close_of(s, name, start):
    """End index of the element whose start tag ends at `start`, counting nested tags of the same name."""
    depth = 1
    for m in TAG.finditer(s, start):
        if m.group(2).lower() != name:
            continue
        if m.group(1):
            depth -= 1
            if depth == 0:
                return m.end()
        elif not m.group(3).rstrip().endswith('/'):
            depth += 1
    return len(s)

def numeric(table_html):
    cells = re.findall(r'<td\b[^>]*>(.*?)</td>', table_html, re.S)
    if not cells:
        return False
    nums = sum(1 for c in cells if re.search(r'\d', re.sub(r'<[^>]+>', '', c)))
    return nums / len(cells) >= 0.4

TOOLS = {'operators.html'}   # the toolkit's tables are worked guidance, not panel data, so they stay open

def wanted(name, c, body, inside_fig, path=''):
    """Is this element a chart or a data table that partners keep?"""
    if name == 'figure':
        return 'hq' not in c   # a guest quote on the home page is words, not a chart
    if inside_fig:
        return False
    if name in ('ul', 'ol') and ({'bars', 'hb'} & set(c)):
        return True
    if name == 'div' and ({'cgrid', 'dgrid', 'stack'} & set(c)):   # home page: course cards and the great debates
        return True
    if name == 'svg' and 'svgc' in c:
        return True
    if name == 'div' and ({'tablewrap', 'cs-table-wrap'} & set(c)):
        return path not in TOOLS and numeric(body)
    return False

LOCKSVG = '<svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>'
BARS = (92, 74, 66, 51, 38)

def placeholder(kind, nxt):
    label = 'Partner chart' if kind == 'chart' else 'Partner data'
    ghost = ''.join(f'<i style="width:{w}%"></i>' for w in BARS)
    return (f'<div class="pgate pgate-{kind}"><a class="pgate-bar" href="/login?next={html.escape(nxt, quote=True)}">'
            f'{LOCKSVG}<span>{label}</span><b>Sign in to see it</b></a>'
            f'<div class="pgate-ghost" aria-hidden="true">{ghost}</div></div>')

def keep_in_figure(body):
    """From a figure, keep the caption (the finding, in words), the source line, and empty script targets."""
    keep = []
    for m in TAG.finditer(body):
        if m.group(1):
            continue
        name, c = m.group(2).lower(), cls(m.group(3))
        if name == 'figcaption' or (name == 'footer' and 'ex-src' in c):
            keep.append(body[m.start():close_of(body, name, m.end())])
        elif name == 'svg' and attr(m.group(3), 'id'):
            end = close_of(body, name, m.end())
            inner = body[m.end():end]
            if not re.sub(r'</svg>\s*$', '', inner).strip():   # empty canvas a page script draws into
                keep.append('<div hidden>' + body[m.start():end] + '</div>')
    return keep

def gate(s, path):
    url = url_of(path)
    out, i, n = [], 0, 0
    for m in TAG.finditer(s):
        if m.start() < i or m.group(1):
            continue
        name = m.group(2).lower()
        if name in VOID:
            continue
        end = close_of(s, name, m.end())
        body = s[m.start():end]
        if not wanted(name, cls(m.group(3)), body, False, path):
            continue
        fid = attr(m.group(3), 'id')
        nxt = url + ('#' + fid if fid else '')
        if name == 'figure':
            kept = keep_in_figure(body)
            cap = [k for k in kept if k.startswith('<figcaption')]
            rest = [k for k in kept if not k.startswith('<figcaption')]
            repl = s[m.start():m.end()] + ''.join(cap) + placeholder('chart', nxt) + ''.join(rest) + '</figure>'
        else:
            repl = placeholder('data' if name == 'div' and {'tablewrap', 'cs-table-wrap'} & set(cls(m.group(3))) else 'chart', nxt)
        out.append(s[i:m.start()]); out.append(repl)
        i, n = end, n + 1
    out.append(s[i:])
    s = ''.join(out)
    # an open page: indexable, pointing search engines at the real address, without the licensed-content banner
    s = re.sub(r'<meta name="robots"[^>]*>\s*', '', s)
    s = re.sub(r'<link rel="canonical"[^>]*>\s*', '', s)
    s = s.replace('Partner access only.', 'Free to read; the charts and data tables are for partners.')
    s = s.replace('<head>', f'<head>\n<meta name="dm-view" content="open">\n<link rel="canonical" href="{SITE}{url}">', 1)
    return s, n

def sitemap(urls):
    p = os.path.join(ROOT, 'sitemap.xml')
    sm = open(p, encoding='utf-8').read()
    add = ''.join(f'<url><loc>{SITE}{u}</loc></url>\n' for u in urls if f'<loc>{SITE}{u}</loc>' not in sm)
    if add:
        open(p, 'w', encoding='utf-8').write(sm.replace('</urlset>', add + '</urlset>'))
    return add.count('<url>')

def main():
    total = 0
    for p in pages() + chart_pages():
        src = os.path.join(ROOT, p)
        s = open(src, encoding='utf-8').read()
        g, n = gate(s, p)
        dst = os.path.join(ROOT, OUT, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'w', encoding='utf-8').write(g)
        total += n
        print(f'{p}: {n} charts and tables kept for partners')
    print(f'{len(pages()) + len(chart_pages())} open pages written to /{OUT}/, {total} visuals gated')
    print(f'{sitemap("/" + re.sub(r"\.html$", "", p) for p in pages())} pages added to sitemap.xml')

if __name__ == '__main__':
    main()
