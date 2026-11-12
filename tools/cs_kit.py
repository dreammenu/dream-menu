"""cs_kit: chart and layout helpers for the Dream Menu Insight Series (/case-studies).

Charts follow the site's dataviz rules: one validated palette (case.css --c1 indigo, --c2 amber,
--c3 teal, --cm muted), emphasis by highlighting rather than rainbow colour, values on the bar
ends, a hover tooltip on every mark (case.js reads data-tip) and a data table under every exhibit.
"""
import html, math, random
from vinfo import vinfo

esc = lambda s: html.escape(str(s), quote=True)


def num(v, dec=0, unit=''):
    if v is None:
        return 'n/a'
    s = f'{v:,.{dec}f}'
    return s + unit


def pts(v, dec=1):
    return ('+' if v > 0 else '\u2212' if v < 0 else '') + f'{abs(v):.{dec}f}'


# ------------------------------------------------------------------ exhibits
# "How to read this" notes by chart kind, matched on the chart's own markup (first match wins)
KIND_INFO = [
    ('svgc fan', 'The solid line is the recorded share; the dashed line is where the recent trend points; the shaded band is a sensible planning range around it. The band widens because the further ahead you look, the less certain the path.\nUse the band for planning, not the single line. Faded dots are quarters with few answers.'),
    ('aria-label="Map', 'Each circle is a venue at its approximate address; bigger circles are named by more guests. Strong circles are the ones the text discusses.\nHover or tap a circle for the venue and its figures.'),
    ('svgc strip', 'Each dot is one item, spread vertically so dots do not hide each other; further right means a higher value. The scale is square-root, which keeps small values readable beside large ones.\nHover or tap a dot for its name and figure.'),
    ('wf-svg', 'Each step adds its cost to the running total, ending in the total bar on the right.\nThe figures are modelled from published prices and typical orders, not receipts from real nights out.'),
    ('class="svgc"', 'One small chart per item, all on the same scale, so heights compare fairly across panels. The line is the share each quarter and the figure top right is the latest value.\nFaded points are quarters with fewer than 100 answers: read them as an early signal, not a result.'),
    ('class="db"', 'Each row compares two periods. The ring is the earlier share and the dot the recent one, so the line between them is the size of the change; the key shows which colour means rising or falling.\n"Clear" marks a change too big to be explained by sampling alone. The rest could be noise.'),
    ('dv2 ledger', 'Each row sets two counts of guests against each other on one scale: bars to the left for the first answer named in the key, bars to the right for the second. The figures at the end give both.\nA long bar on both sides means a divisive item: loved by some, tired of by others.'),
    ('class="dv2"', 'Bars grow left or right from the centre line: to the right means above the reference point, to the left below it, and a longer bar is a bigger gap.\nFaded rows are less certain, usually because they rest on few answers.'),
    ('class="hb"', 'Each bar is one item on a common scale, with its value at the end. Strong bars are the ones the text is about; pale bars are there for comparison.\nHover or tap a bar for the exact figure.'),
    ('class="sb"', 'Each bar adds up to 100% and splits one group\u2019s answers into parts. Compare the size of the same colour from row to row rather than the overall bar length.\nHover or tap a segment for its share and the number behind it.'),
    ('class="cols"', 'Each column is one period or group on a common scale, with its value on top. Highlighted columns are the ones the text discusses.'),
    ('class="heat"', 'Each cell is shaded by how its value ranks against every other cell in the table: darker means higher. Read across a row to compare places, down a column to compare items.'),
    ('class="mx"', 'Each numbered point is a recommendation, placed by likely impact (up) and the effort it needs (right). Top left are quick wins; top right are bigger bets worth planning.\nPositions are informed judgement, not measured values.'),
    ('lanes-svg', 'The curve is the usual life of a food trend, from early adopters through the mainstream to fade. Each circle counts the items we place at that stage, and the columns below list them, shaded by how confident we are.\nRead it as a watchlist, not a forecast.'),
    ('class="rm"', 'Each bar runs from when we expect an idea to first appear to when it reaches the mainstream, marked by the dot. The vertical line is today.\nThese timings are judgement drawn from the data and trade sources, not modelled forecasts.'),
    ('class="scens"', 'Each card is one possible future with our estimate of how likely it is. The likelihoods are judgement calls, not modelled probabilities; the early signs show what to watch to know which way things are going.'),
    ('class="forces"', 'Each card is one force acting on the market: the headline figure, which way it pushes and how soon it bites.'),
]


def kind_info(chart):
    for key, text in KIND_INFO:
        if key in chart:
            return text
    return ''


class Ex:
    """Numbers exhibits within one report."""

    def __init__(self):
        self.n = 0

    def __call__(self, title, sub, chart, src, data=None, legend=None, info=None):
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
                f'<h3>{title}</h3><p class="exh-sub">{sub}</p>{vinfo(kind_info(chart) if info is None else info)}</figcaption>{lg}{chart}'
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
    out, boxes = [], []
    for n, lab, imp, eff in sorted(items, key=lambda t: (-t[2], t[3])):
        x, y0 = 8 + 84 * eff, 8 + 84 * imp
        pref = ' r' if x > 66 else ''
        other = '' if pref else ' r'
        # try the preferred side, then the other side, then small nudges up and down, so labels never collide
        for dy, side in [(0, pref), (0, other), (-7, pref), (-7, other), (7, pref), (7, other), (-14, pref), (-14, other)]:
            y = min(86, max(5, y0 + dy))
            if side == ' r' and x < 34 or side == '' and x > 70:
                continue
            x0, x1 = (x - 31, x + 2) if side else (x - 2, x + 31)
            if not any(abs(y - by) < 8 and x0 < bx1 and bx0 < x1 for bx0, bx1, by in boxes):
                break
        boxes.append((x0, x1, y))
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
    return (f'<svg class="svgc strip" viewBox="0 0 {w} {h:.0f}" role="img" aria-label="{esc(xlabel)}">{g}{body}'
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
    return f'<svg class="svgc wf-svg" viewBox="0 0 {w} {h}" role="img" aria-label="Budget build-up">{out}</svg>'


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


# ------------------------------------------------------------------ forecast helpers (Nos. 12 to 15)
def project(vals, faded=(), steps=5, phi=0.7):
    """Damped-trend projection. Fits a recency-weighted line to the solid quarters, starts from a blend
    of the last solid value and the fitted line, and damps the slope by phi each quarter.
    Returns (anchor index, [(mid, lo, hi)] for each step). The band is a planning range, not a confidence interval."""
    P = [(i, v) for i, v in enumerate(vals) if v is not None and i not in faded]
    n = len(P)
    w = [1 + k for k in range(n)]
    sw = sum(w); mx = sum(wi * x for wi, (x, _) in zip(w, P)) / sw; my = sum(wi * y for wi, (_, y) in zip(w, P)) / sw
    sxx = sum(wi * (x - mx) ** 2 for wi, (x, _) in zip(w, P)) or 1
    b = sum(wi * (x - mx) * (y - my) for wi, (x, y) in zip(w, P)) / sxx
    a = my - b * mx
    s = max(1.5, math.sqrt(sum(wi * (y - (a + b * x)) ** 2 for wi, (x, y) in zip(w, P)) / sw))
    ai, av = P[-1]
    start = 0.5 * av + 0.5 * (a + b * ai)
    out, cum = [], 0
    for j in range(1, steps + 1):
        cum += phi ** j
        mid = start + b * cum
        hw = s * math.sqrt(1 + 0.6 * j) + 0.5 * abs(b) * cum  # sampling noise plus doubt about the slope itself
        out.append((max(0, mid), max(0, mid - hw), min(100, mid + hw)))
    return ai, out


def fan_multiples(panels, xlabels, unit='%', ymax=None, w=300, h=190, cols_min=260):
    """panels: (title, values, k, faded, anchor, proj). values cover the history; proj continues from the anchor
    index to the end of xlabels. Solid line = history, dashed line + band = projection on recent trend."""
    pl, pr, pt, pb = 34, 14, 46, 26
    iw, ih = w - pl - pr, h - pt - pb
    N = len(xlabels)
    X = lambda i: pl + iw * i / (N - 1)
    out = []
    for title, vs, k, fd, ai, proj in panels:
        # each panel has its own scale (the measures have different bases); the axis always starts at zero
        top = ymax or 5 * math.ceil(max([v for v in vs if v is not None] + [hi for _, _, hi in proj]) * 1.1 / 5)
        y = lambda v: pt + ih * (1 - v / top)
        fz = f'<rect class="fz" x="{X(ai):.1f}" y="{pt}" width="{X(N - 1) - X(ai):.1f}" height="{ih}"/><text class="fzl" x="{X(N - 1) - 3:.1f}" y="{pt + 12}" text-anchor="end">Projection</text>'
        ticks = [0, top / 2, top]
        g = ''.join(f'<line class="grid" x1="{pl}" x2="{w - pr}" y1="{y(t):.1f}" y2="{y(t):.1f}"/><text x="{pl - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.0f}</text>' for t in ticks)
        solid = [(X(i), v) for i, v in enumerate(vs) if v is not None and i not in fd]
        path = 'M' + ' L'.join(f'{x:.1f},{y(v):.1f}' for x, v in solid)
        pts_ = [(X(ai), vs[ai], vs[ai], vs[ai])] + [(X(ai + j + 1), m, lo, hi) for j, (m, lo, hi) in enumerate(proj)]
        band = 'M' + ' L'.join(f'{x:.1f},{y(hi):.1f}' for x, _, _, hi in pts_) + ' L' + ' L'.join(f'{x:.1f},{y(lo):.1f}' for x, _, lo, _ in reversed(pts_)) + ' Z'
        pline = 'M' + ' L'.join(f'{x:.1f},{y(m):.1f}' for x, m, _, _ in pts_)
        dots = ''
        for i, v in enumerate(vs):
            if v is None:
                continue
            op = ' opacity=".35"' if i in fd else ''
            dots += f'<circle class="{k} ring" cx="{X(i):.1f}" cy="{y(v):.1f}" r="{4.5 if i == ai else 3.2}"{op} tabindex="0" data-tip="{esc("<b>" + esc(title) + "</b><br>" + esc(xlabels[i]) + ": " + num(v, 1, unit) + (" (few answers)" if i in fd else ""))}"/>'
        em, elo, ehi = proj[-1]
        dots += f'<circle class="{k} pend" cx="{X(N - 1):.1f}" cy="{y(em):.1f}" r="4.5" tabindex="0" data-tip="{esc("<b>" + esc(title) + "</b><br>" + esc(xlabels[-1]) + " on recent trend: " + num(em, 1, unit) + "<br>Planning range " + num(elo, 1) + " to " + num(ehi, 1, unit))}"/>'
        xt = ''.join(f'<text x="{X(i):.1f}" y="{h - 8}" text-anchor="{a}">{esc(xlabels[i])}</text>' for i, a in ((0, 'start'), (ai, 'middle'), (N - 1, 'end')))
        out.append(f'<svg class="svgc fan" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}"><text class="tb" x="{pl}" y="15">{esc(title)}</text>'
                   f'<text class="tv" x="{pl}" y="33">{num(vs[ai], 1, unit)} in {esc(xlabels[ai])} → <tspan class="tb">{num(em, 1, unit)}</tspan> by {esc(xlabels[-1])}</text>{fz}{g}'
                   f'<path class="band {k}" d="{band}"/><path class="ln {k}" d="{path}"/><path class="ln proj {k}" d="{pline}"/>{dots}{xt}</svg>')
    legend = ('<div class="ex-legend"><span><i style="background:var(--c1)"></i>Recorded share</span><span><i class="dash"></i>Projection on the recent trend</span>'
              '<span><i style="background:var(--c1);opacity:.22"></i>Planning range</span><span><i class="dot" style="background:var(--c1);opacity:.35"></i>Quarter with few answers</span></div>')
    return legend + f'<div class="ex-pair" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,{cols_min}px),1fr));gap:18px 24px">' + ''.join(f'<div>{s}</div>' for s in out) + '</div>'


def _curve(x):
    """Adoption curve: an S-shaped rise to a peak at x = .8, then a gentle fade."""
    if x <= .8:
        return 1 / (1 + math.exp(-11 * (x - .44)))
    p = 1 / (1 + math.exp(-11 * (.8 - .44)))
    return p - 1.3 * (x - .8) ** 1.4


def lanes(stages, items, w=680, h=180):
    """stages: (name, note). items: (name, stage index, confidence High/Medium/Low, when, tip).
    Draws the adoption curve with a count per stage, then the items as chips in stage columns."""
    n = len(stages)
    pl, pr, pt, pb = 8, 8, 18, 48
    iw, ih = w - pl - pr, h - pt - pb
    X = lambda t: pl + iw * t
    Y = lambda v: pt + ih * (1 - v)
    path = 'M' + ' L'.join(f'{X(t / 100):.1f},{Y(_curve(t / 100)):.1f}' for t in range(0, 101))
    area = path + f' L{X(1):.1f},{Y(0):.1f} L{X(0):.1f},{Y(0):.1f} Z'
    svg = f'<path class="area" d="{area}"/><path class="ln k1" d="{path}"/>'
    cnt = [sum(1 for it in items if it[1] == i) for i in range(n)]
    for i, (nm, _) in enumerate(stages):
        if i:
            svg += f'<line class="grid" x1="{X(i / n):.1f}" x2="{X(i / n):.1f}" y1="{pt - 6}" y2="{Y(0):.1f}" stroke-dasharray="3 4"/>'
        cx = (i + .5) / n
        cy = Y(_curve(cx))
        r = 7 + 3.2 * math.sqrt(cnt[i])
        svg += f'<circle class="k1 ring" cx="{X(cx):.1f}" cy="{cy:.1f}" r="{r:.1f}" tabindex="0" data-tip="{esc("<b>" + esc(nm) + "</b><br>" + str(cnt[i]) + " items on the watchlist")}"/>'
        svg += f'<text class="cnum" x="{X(cx):.1f}" y="{cy + 4.5:.1f}" text-anchor="middle">{cnt[i]}</text>'
        svg += f'<text class="tb" x="{X(cx):.1f}" y="{h - 10}" text-anchor="middle">{esc(nm)}</text>'
    svg += f'<line class="axis" x1="{pl}" x2="{w - pr}" y1="{Y(0):.1f}" y2="{Y(0):.1f}"/>'
    head = f'<svg class="svgc lanes-svg" viewBox="0 0 {w} {h}" role="img" aria-label="Adoption curve with the number of items at each stage">{svg}</svg>'
    colsh = ''
    for i, (nm, note) in enumerate(stages):
        chips = ''.join(f'<li class="chip c-{c.lower()}" tabindex="0" data-tip="{esc("<b>" + esc(t) + "</b><br>" + tip + "<br>Confidence: " + c)}"><span>{esc(t)}</span><small>{esc(wh)}</small></li>'
                        for t, s, c, wh, tip in items if s == i)
        colsh += f'<div class="lane"><h4>{esc(nm)}<small>{esc(note)}</small></h4><ul>{chips}</ul></div>'
    legend = ('<div class="ex-legend"><span><i class="chipk c-high"></i>High confidence</span><span><i class="chipk c-medium"></i>Medium</span>'
              '<span><i class="chipk c-low"></i>Low (speculative)</span><span>Small text: when we expect it on mainstream Glasgow menus</span></div>')
    return head + legend + f'<div class="lanes" style="--n:{n}">{colsh}</div>'


def roadmap(rows, y0=2026, y1=2031, now=None):
    """rows: (label, k, start, end, note). Years as decimals; end None draws a single event marker.
    A bar runs from first arrival to the mainstream point; the dot marks the mainstream point."""
    span = y1 - y0
    P = lambda t: 100 * (min(max(t, y0), y1) - y0) / span
    yrs = ''.join(f'<span style="left:{P(y):.2f}%">{y}</span>' for y in range(y0, y1 + 1))
    nl = f'<i class="rm-now" style="left:{P(now):.2f}%"></i>' if now else ''
    out = []
    for lab, k, a, b, note in rows:
        tip = f'<b>{esc(lab)}</b><br>{esc(note)}'
        if b is None:
            mark = f'<b class="ev {k}" style="left:{P(a):.2f}%"></b>'
        else:
            mark = f'<i class="bar {k}" style="left:{P(a):.2f}%;width:{max(1, P(b) - P(a)):.2f}%"></i><b class="end {k}" style="left:{P(b):.2f}%"></b>'
        out.append(f'<li tabindex="0" data-tip="{esc(tip)}"><span class="l">{esc(lab)}<small>{esc(note)}</small></span><span class="t">{nl}{mark}</span></li>')
    return f'<div class="rm" style="--n:{span}"><div class="rm-h"><span></span><span class="yrs">{yrs}</span></div><ul>{"".join(out)}</ul></div>'


def ledger(rows, left='Want it gone', right='Named as a positive trend'):
    """rows: (label, positive, negative). Bars either side of a centre line, on one shared scale."""
    top = max(max(p, n) for _, p, n in rows) or 1
    out = []
    for lab, p, n in rows:
        tip = f'<b>{esc(lab)}</b><br>{esc(right)}: {p}<br>{esc(left)}: {n}'
        out.append(f'<li tabindex="0" data-tip="{esc(tip)}"><span class="l">{esc(lab)}</span><span class="t">'
                   f'<i class="n" style="left:{50 - 50 * n / top:.1f}%;width:{50 * n / top:.1f}%"></i><i class="p" style="left:50%;width:{50 * p / top:.1f}%"></i></span>'
                   f'<span class="v"><em>{n}</em> / {p}</span></li>')
    axis = f'<div class="dv2-axis"><span></span><span><span>← {esc(left)}</span><span>{esc(right)} →</span></span><span></span></div>'
    return axis + '<ul class="dv2 ledger">' + ''.join(out) + '</ul>'


def scenarios(items):
    """items: (name, probability %, tagline, body, signals). Cards with a probability bar."""
    out = ''
    for nm, pr, tag, body, sig in items:
        out += (f'<div class="scen"><div class="sp"><b>{pr}%</b><span>likelihood</span><i style="width:{pr}%"></i></div>'
                f'<h4>{esc(nm)}</h4><p class="stag">{tag}</p><p>{body}</p><p class="sig"><b>Early signs:</b> {sig}</p></div>')
    return f'<div class="scens">{out}</div>'


def forces(items):
    """items: (n, title, stat, stat label, body, horizon, direction up/down/mixed)."""
    out = ''
    for n, t, s, sl, body, hz, d in items:
        out += (f'<div class="force" id="force-{n}"><span class="fn">{n:02d}</span><h4>{t}</h4>'
                f'<div class="fs"><b>{esc(s)}</b><span>{sl}</span></div><p>{body}</p>'
                f'<div class="ft"><span class="tg">Bites: {esc(hz)}</span><span class="tg d-{d}">{ {"up": "Growing", "down": "Shrinking", "mixed": "Reshaping"}[d] }</span></div></div>')
    return f'<div class="forces">{out}</div>'
