"""cs_kit: chart and layout helpers for the Dream Menu Insight Series (/case-studies).

Charts follow the site's dataviz rules: one validated palette (case.css --c1 indigo, --c2 amber,
--c3 teal, --cm muted), emphasis by highlighting rather than rainbow colour, values on the bar
ends, a hover tooltip on every mark (case.js reads data-tip) and a data table under every exhibit.
"""
import html, math, random

esc = lambda s: html.escape(str(s), quote=True)


def num(v, dec=0, unit=''):
    if v is None:
        return 'n/a'
    s = f'{v:,.{dec}f}'
    return s + unit


def pts(v, dec=1):
    return ('+' if v > 0 else '\u2212' if v < 0 else '') + f'{abs(v):.{dec}f}'


# ------------------------------------------------------------------ exhibits
class Ex:
    """Numbers exhibits within one report."""

    def __init__(self):
        self.n = 0

    def __call__(self, title, sub, chart, src, data=None, legend=None):
        self.n += 1
        lg = ''
        if legend:
            lg = '' if not legend else '<div class="ex-legend">' + ''.join(f'<span><i class="{c}" style="{s}"></i>{esc(t)}</span>' for t, c, s in legend) + '</div>'
        tb = ''
        if data:
            head, rows = data
            th = ''.join(f'<th>{esc(h)}</th>' for h in head)
            tr = ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>' for r in rows)
            tb = f'<details class="ex-data"><summary>Show the data</summary><div class="cs-table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></details>'
        return (f'<figure class="ex" id="exhibit-{self.n}"><figcaption class="ex-cap"><span class="ex-n">Exhibit {self.n}</span>'
                f'<h3>{title}</h3><p class="exh-sub">{sub}</p></figcaption>{lg}{chart}'
                f'<footer class="ex-src">Source: {src}</footer>{tb}</figure>')


LEG_C1 = ('', '', 'background:var(--c1)')
def leg(label, var='c1', shape=''):
    return (label, shape, f'background:var(--{var})')


# ------------------------------------------------------------------ HTML charts
def hbar(rows, on=None, alt=None, unit='', dec=0, mx=None, tip_unit=None, pre=''):
    """rows: (label, value) or (label, value, note). on: labels to emphasise (None = all)."""
    top = mx or max(r[1] for r in rows) or 1
    out = []
    for r in rows:
        lab, v = r[0], r[1]
        note = r[2] if len(r) > 2 else ''
        cls = 'on' if on is None or lab in on else 'off'
        if alt and lab in alt:
            cls = 'alt'
        tip = f'<b>{esc(lab)}</b><br>{pre}{num(v, dec, tip_unit if tip_unit is not None else unit)}' + (f'<br>{esc(note)}' if note else '')
        sm = f'<small>{esc(note)}</small>' if note else ''
        out.append(f'<li class="{cls}" tabindex="0" data-tip="{esc(tip)}"><span class="l">{esc(lab)}{sm}</span>'
                   f'<span class="t"><i style="width:{max(0.4, 100 * v / top):.1f}%"></i></span><span class="v">{pre}{num(v, dec, unit)}</span></li>')
    return '<ul class="hb">' + ''.join(out) + '</ul>'


def dumbbell(rows, unit='%', dec=1, mx=None, sig=(), flat=0.6, a_lab='Jul to Dec 2025', b_lab='Apr 2026 onward'):
    """rows: (label, early, recent). Ring = early, dot = recent; colour by direction."""
    top = mx or max(max(a, b) for _, a, b in rows) * 1.08 or 1
    out = []
    for lab, a, b in rows:
        d = b - a
        cls = 'up' if d > flat else 'down' if d < -flat else 'flat'
        x1, x2 = 100 * min(a, b) / top, 100 * max(a, b) / top
        clear = ' · clear move' if lab in sig else ''
        tip = f'<b>{esc(lab)}</b><br>{esc(a_lab)}: {num(a, dec, unit)}<br>{esc(b_lab)}: {num(b, dec, unit)}<br>Change: {pts(d, dec)} pts{clear}'
        out.append(f'<li class="{cls}" tabindex="0" data-tip="{esc(tip)}"><span class="l">{esc(lab)}</span><span class="t">'
                   f'<span class="seg" style="left:{x1:.1f}%;width:{max(0.3, x2 - x1):.1f}%"></span>'
                   f'<span class="a" style="left:{100 * a / top:.1f}%"></span><span class="b" style="left:{100 * b / top:.1f}%"></span></span>'
                   f'<span class="v">{pts(d, dec)}<small>{"clear" if lab in sig else "pts"}</small></span></li>')
    legend = (f'<div class="ex-legend"><span><i class="ring"></i>{esc(a_lab)}</span><span><i class="dot" style="background:var(--c1)"></i>{esc(b_lab)}, rising</span>'
              f'<span><i class="dot" style="background:var(--c2)"></i>{esc(b_lab)}, falling</span></div>')
    return legend + '<ul class="db">' + ''.join(out) + '</ul>'


def diverge(rows, center=0, unit='', dec=1, mx=None, dim=(), left='', right='', show=None):
    """rows: (label, value). Bars grow from the centre line; indigo above centre, amber below."""
    top = mx or max(abs(v - center) for _, v in rows) or 1
    out = []
    for lab, v in rows:
        d = v - center
        w = 50 * abs(d) / top
        bar = (f'<i class="p" style="left:50%;width:{w:.1f}%"></i>' if d >= 0 else f'<i class="n" style="left:{50 - w:.1f}%;width:{w:.1f}%"></i>')
        val = show(v) if show else (pts(v, dec) if center == 0 else num(v, dec, unit))
        cls = 'dim' if lab in dim else ''
        out.append(f'<li class="{cls}" tabindex="0" data-tip="{esc("<b>" + esc(lab) + "</b><br>" + val)}"><span class="l">{esc(lab)}</span><span class="t">{bar}</span><span class="v">{val}</span></li>')
    axis = f'<div class="dv2-axis"><span></span><span><span>{esc(left)}</span><span>{esc(right)}</span></span><span></span></div>' if left or right else ''
    return axis + '<ul class="dv2">' + ''.join(out) + '</ul>'


def stack(rows, legend, named=False):
    """rows: (label, note, [(segment, value, k)]) with k in k1/k2/k3/k0; values are shares or counts."""
    out = []
    for lab, note, segs in rows:
        tot = sum(v for _, v, _ in segs) or 1
        sp = []
        for name, v, k in segs:
            p = 100 * v / tot
            txt = (f'{esc(name)} {p:.0f}%' if named and p >= 20 else f'{p:.0f}%') if p >= 9 else ''
            sp.append(f'<span class="{k}" style="flex:{v} 1 0" tabindex="0" data-tip="{esc("<b>" + esc(name) + "</b><br>" + f"{p:.0f}% ({v:,})")}">{txt}</span>')
        out.append(f'<li><div class="l"><span>{esc(lab)}</span><small>{esc(note)}</small></div><div class="bar">{"".join(sp)}</div></li>')
    lg = '' if not legend else '<div class="ex-legend">' + ''.join(f'<span><i style="background:var(--{k.replace("k", "c") if k != "k0" else "cm"})"></i>{esc(t)}</span>' for t, k in legend) + '</div>'
    return lg + '<ul class="sb">' + ''.join(out) + '</ul>'


def cols(items, on=(), alt=(), unit='', note=''):
    top = max(v for _, v in items) or 1
    c = []
    for x, v in items:
        cls = 'on' if x in on else 'alt' if x in alt else ''
        c.append(f'<div class="{cls}" tabindex="0" data-tip="{esc("<b>" + esc(x) + "</b><br>" + num(v, 0, unit))}"><b>{num(v, 0, unit)}</b><i style="height:{max(1.5, 82 * v / top):.1f}%"></i></div>')
    xs = ''.join(f'<span>{esc(x)}</span>' for x, _ in items)
    nt = f'<p class="cols-note">{note}</p>' if note else ''
    return f'<div class="cols">{"".join(c)}</div><div class="cols-x">{xs}</div>{nt}'


def heat(head, rows, fmt=lambda v: str(v), key=('Lower', 'Higher')):
    vals = sorted(v for _, vs in rows for v in vs if v is not None)
    def cls(v):
        if v is None:
            return 'h0'
        r = vals.index(v) / max(1, len(vals) - 1)
        return 'h' + str(min(5, 1 + int(r * 5)))
    th = ''.join(f'<th>{esc(h)}</th>' for h in head)
    tr = ''.join('<tr><td>' + esc(lab) + '</td>' + ''.join(
        f'<td class="{cls(v)}" tabindex="0" data-tip="{esc("<b>" + esc(lab) + "</b><br>" + esc(head[i + 1]) + ": " + (fmt(v) if v is not None else "n/a"))}">{fmt(v) if v is not None else "n/a"}</td>' for i, v in enumerate(vs)) + '</tr>' for lab, vs in rows)
    k = ''.join(f'<i style="background:var(--s{i})"></i>' for i in range(1, 6))
    return f'<div class="heat-wrap"><table class="heat"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div><div class="heat-key">{esc(key[0])} {k} {esc(key[1])}</div>'


def matrix(items, xl=('Lower effort', 'Higher effort'), yl=('Lower impact', 'Higher impact'),
           q=('Big bets', 'Quick wins', 'Fill-ins', 'Hard yards')):
    """items: (n, label, impact 0-1, effort 0-1). Quick wins top left."""
    seen = {}
    out = []
    for n, lab, imp, eff in items:
        key = (round(imp, 1), round(eff, 1))
        k = seen.get(key, 0); seen[key] = k + 1
        x = 8 + 84 * eff + (k * 4)
        y = 8 + 84 * imp - (k * 12)
        side = ' r' if x > 66 else ''
        out.append(f'<div class="pt{side}" style="left:{x:.1f}%;bottom:{y:.1f}%" tabindex="0" data-tip="{esc("<b>" + str(n) + ". " + esc(lab) + "</b>")}"><b>{n}</b><span>{esc(lab)}</span></div>')
    return (f'<div class="mx" role="img" aria-label="Recommendations by impact and effort">'
            f'<span class="q q1">{q[0]}</span><span class="q q2">{q[1]}</span><span class="q q3">{q[2]}</span><span class="q q4">{q[3]}</span>'
            + ''.join(out) +
            f'<div class="ax x"><span>{xl[0]}</span><span>{xl[1]}</span></div><div class="ax y"><span>{yl[0]}</span><span>{yl[1]}</span></div></div>')


# ------------------------------------------------------------------ SVG charts
def small_multiples(panels, xlabels, unit='%', ymax=None, faded=(), w=300, h=170):
    """panels: (title, values, k). One shared y-scale so panels compare honestly."""
    top = ymax or max(v for _, vs, _ in panels for v in vs if v is not None) * 1.15
    pl, pr, pt, pb = 34, 14, 26, 26
    iw, ih = w - pl - pr, h - pt - pb
    out = []
    for title, vs, k in panels:
        xs = [pl + iw * i / (len(vs) - 1) for i in range(len(vs))]
        y = lambda v: pt + ih * (1 - v / top)
        ticks = [0, top / 2, top]
        g = ''.join(f'<line class="grid" x1="{pl}" x2="{w - pr}" y1="{y(t):.1f}" y2="{y(t):.1f}"/><text x="{pl - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.0f}</text>' for t in ticks)
        solid = [(x, v) for i, (x, v) in enumerate(zip(xs, vs)) if v is not None and i not in faded]
        path = 'M' + ' L'.join(f'{x:.1f},{y(v):.1f}' for x, v in solid)
        area = path + f' L{solid[-1][0]:.1f},{pt + ih} L{solid[0][0]:.1f},{pt + ih} Z'
        dots = ''
        for i, (x, v) in enumerate(zip(xs, vs)):
            if v is None:
                continue
            op = ' opacity=".35"' if i in faded else ''
            r = 5 if i == len(solid) - 1 or i in faded else 3.5
            dots += f'<circle class="{k} ring" cx="{x:.1f}" cy="{y(v):.1f}" r="{r}"{op} tabindex="0" data-tip="{esc("<b>" + esc(title) + "</b><br>" + esc(xlabels[i]) + ": " + num(v, 1, unit) + (" (few answers)" if i in faded else ""))}"/>'
        last = solid[-1]
        xt = ''.join(f'<text x="{x:.1f}" y="{h - 8}" text-anchor="middle">{esc(xlabels[i])}</text>' for i, x in enumerate(xs) if i % 2 == 0 or len(xs) <= 4)
        out.append(f'<svg class="svgc" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}"><text class="tb" x="{pl}" y="15">{esc(title)}</text>'
                   f'<text class="tx" x="{w - pr}" y="15" text-anchor="end">{num(last[1], 1, unit)}</text>{g}'
                   f'<path class="area" d="{area}"/><path class="ln {k}" d="{path}"/>{dots}{xt}</svg>')
    return '<div class="ex-pair" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:18px 24px">' + ''.join(f'<div>{s}</div>' for s in out) + '</div>'


def strip(rows, xmax, xlabel, w=680, seed=7):
    """Dot strip: rows (label, k, [(x, tip)]). Square-root x from the smallest value; row height grows with its count."""
    rnd = random.Random(seed)
    pl, pr, pt, pb = 150, 20, 8, 42
    iw = w - pl - pr
    xs = [x for _, _, px in rows for x, _ in px]
    xmin = max(1, min(xs) - 0.5)
    X = lambda v: pl + iw * (math.sqrt(v) - math.sqrt(xmin)) / (math.sqrt(xmax) - math.sqrt(xmin))
    hs = [max(40, min(130, 26 + 0.85 * len(px))) for _, _, px in rows]
    h = pt + sum(hs) + pb
    ticks = [t for t in (5, 10, 15, 20, 30, 45) if xmin <= t <= xmax]
    g = ''.join(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{pt}" y2="{h - pb}"/><text x="{X(t):.1f}" y="{h - pb + 18}" text-anchor="middle">{t}</text>' for t in ticks)
    body, y0 = '', pt
    for (lab, k, ptsx), rh in zip(rows, hs):
        cy = y0 + rh / 2
        body += f'<line class="grid" x1="{pl}" x2="{w - pr}" y1="{y0 + rh:.1f}" y2="{y0 + rh:.1f}" opacity=".5"/>'
        body += f'<text class="tx" x="{pl - 12}" y="{cy + 4:.1f}" text-anchor="end">{esc(lab)} ({len(ptsx)})</text>'
        for x, tip in ptsx:
            jy = cy + rnd.uniform(-rh * .36, rh * .36)
            body += f'<circle class="{k} ring" cx="{X(x) + rnd.uniform(-2.5, 2.5):.1f}" cy="{jy:.1f}" r="5" tabindex="0" data-tip="{esc(tip)}"/>'
        y0 += rh
    return (f'<svg class="svgc" viewBox="0 0 {w} {h:.0f}" role="img" aria-label="{esc(xlabel)}">{g}{body}'
            f'<text x="{pl + iw / 2:.1f}" y="{h - 4:.0f}" text-anchor="middle">{esc(xlabel)}</text></svg>')


def waterfall(steps, total_label, unit='£', w=640, h=300):
    """steps: (label, value). Bars float from the running total; the last bar is the total."""
    pl, pr, pt, pb = 40, 16, 20, 44
    tot = sum(v for _, v in steps)
    n = len(steps) + 1
    iw, ih = w - pl - pr, h - pt - pb
    bw = min(64, iw / n * .55)
    y = lambda v: pt + ih * (1 - v / (tot * 1.12))
    out, run = '', 0
    ticks = [0, 20, 40, 60, 80] if tot < 90 else [0, 50, 100, 150]
    out += ''.join(f'<line class="grid" x1="{pl}" x2="{w - pr}" y1="{y(t):.1f}" y2="{y(t):.1f}"/><text x="{pl - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{unit}{t}</text>' for t in ticks if t <= tot * 1.12)
    for i, (lab, v) in enumerate(steps + [(total_label, None)]):
        cx = pl + iw * (i + .5) / n
        if v is None:
            y0, y1, k, val = y(tot), y(0), 'k1', tot
        else:
            y0, y1, k, val = y(run + v), y(run), 'k0', v
        out += f'<rect class="{k} wf" x="{cx - bw / 2:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(1, y1 - y0):.1f}" rx="3" tabindex="0" data-tip="{esc("<b>" + esc(lab) + "</b><br>" + unit + str(val))}"/>'
        out += f'<text class="tb" x="{cx:.1f}" y="{y0 - 7:.1f}" text-anchor="middle">{unit}{val}</text>'
        out += f'<text class="tx" x="{cx:.1f}" y="{h - pb + 18}" text-anchor="middle">{esc(lab)}</text>'
        if v is not None and i < len(steps):
            nx = pl + iw * (i + 1.5) / n
            out += f'<line class="wfc" x1="{cx + bw / 2:.1f}" x2="{nx - bw / 2:.1f}" y1="{y(run + v):.1f}" y2="{y(run + v):.1f}"/>'
            run += v
    out += f'<line class="axis" x1="{pl}" x2="{w - pr}" y1="{y(0):.1f}" y2="{y(0):.1f}"/>'
    return f'<svg class="svgc" viewBox="0 0 {w} {h}" role="img" aria-label="Budget build-up">{out}</svg>'


def glasgow_map(points, labels, w=680, bbox=(55.822, 55.882, -4.330, -4.195)):
    """points: (lat, lon, mentions, name, area, on). labels: (name, lat, lon). Clipped to the bbox."""
    la0, la1, lo0, lo1 = bbox
    k = math.cos(math.radians((la0 + la1) / 2))
    s = w / ((lo1 - lo0) * k)
    X = lambda lo: (lo - lo0) * k * s
    Y = lambda la: (la1 - la) * s
    vw, vh = w, Y(la0)
    clyde = [(55.8660, -4.3500), (55.8615, -4.3200), (55.8585, -4.3000), (55.8590, -4.2870), (55.8578, -4.2720),
             (55.8568, -4.2600), (55.8555, -4.2500), (55.8520, -4.2420), (55.8480, -4.2340), (55.8470, -4.2250),
             (55.8430, -4.2150), (55.8390, -4.2000), (55.8350, -4.1850)]
    river = 'M' + ' L'.join(f'{X(lo):.1f},{Y(la):.1f}' for la, lo in clyde)
    out = f'<defs><clipPath id="gmclip"><rect x="0" y="0" width="{vw:.0f}" height="{vh:.0f}" rx="8"/></clipPath></defs><g clip-path="url(#gmclip)">'
    out += f'<rect x="0" y="0" width="{vw:.0f}" height="{vh:.0f}" fill="var(--panel)"/>'
    out += f'<path class="river" d="{river}"/><text class="lbl2" x="{X(-4.312):.1f}" y="{Y(55.8565):.1f}">River Clyde</text>'
    inside = [p for p in points if la0 < p[0] < la1 and lo0 < p[1] < lo1]
    for la, lo, m, name, area, on in sorted(inside, key=lambda p: -p[2]):
        r = 2.6 + 1.9 * math.sqrt(m)
        out += f'<circle class="{"k1" if on else "k0"} ring" cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="{r:.1f}" fill-opacity="{.9 if on else .75}" tabindex="0" data-tip="{esc("<b>" + esc(name) + "</b><br>" + esc(area) + "<br>" + str(m) + " mentions")}"/>'
    for name, la, lo in labels:
        out += f'<text class="lbl" x="{X(lo):.1f}" y="{Y(la):.1f}" text-anchor="middle">{esc(name)}</text>'
    out += '</g>'
    return f'<svg class="svgc" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="Map of Glasgow venues named by guests" style="overflow:hidden;border-radius:8px">{out}</svg>'


# ------------------------------------------------------------------ text blocks
def sowhat(who, text):
    return f'<div class="sowhat"><b>So what for {esc(who)}</b><p>{text}</p></div>'


def pull(text, who):
    return f'<blockquote class="pull"><p>{text}</p><small>{esc(who)}</small></blockquote>'


def quotes(items):
    return '<div class="quotes">' + ''.join(f'<figure><blockquote>{esc(q)}</blockquote><figcaption>{esc(w)}</figcaption></figure>' for q, w in items) + '</div>'


def table(head, rows, num_cols=()):
    th = ''.join(f'<th>{esc(h)}</th>' for h in head)
    tr = ''.join('<tr>' + ''.join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<div class="cs-table-wrap"><table class="cs-table"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
