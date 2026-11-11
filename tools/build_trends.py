#!/usr/bin/env python3
"""Menu trends over time: extra analyses for /analysis (course level for all, full detail for signed-in partners).

Run from the repository root after the data refresh, after build_intel.py:
  python3 tools/build_trends.py

Reads partner-data.js (quarterly shares per course) and writes:
  trend-public.js          window.DM_TRENDP  course-level only: how much each course changed, how
                           concentrated it is, how many dishes sit in each lifecycle stage, and the
                           steady staples (no dish-level movement, which stays with partners)
  partner/trend-data.js    window.DM_TRENDX  everything: churn, concentration, lifecycle board, where
                           the share went, then vs now, menu mix by quarter, forecasts, conclusions

Everything is a share of answers within a course, so quarters and markets of different sizes compare
fairly. Food courses only: the drink questions changed on 23 Aug 2026, so drink trends are not tested.
Counts are recovered from the published shares (share x answers / 100, rounded), as add_interviews.py does.
"""
import json, math, os, random, re, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from cs_kit import project  # noqa: E402  damped-trend projection used by the trend reports


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


P = load('partner-data.js', 'DM_PARTNER')
EARLY, LATE, MIN_N = P['method']['early'], P['method']['late'], P['min_n']
FOOD = ['s', 'm', 'd', 'p']
Z = 1.959964
NORM = statistics.NormalDist()
random.seed(20261111)   # fixed, so the chance baselines are the same on every run


def r1(x):
    return None if x is None else round(x + 0.0, 1)


def ztest(c1, n1, c2, n2):
    if not n1 or not n2:
        return 1.0
    pp = (c1 + c2) / (n1 + n2)
    se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    return 1.0 if se == 0 else math.erfc(abs(c2 / n2 - c1 / n1) / se / math.sqrt(2))


def counts(it, nq):
    return [round((s or 0) * n / 100) if n else 0 for s, n in zip(it['share'], nq)]


def wilson(c, n):
    if not n:
        return None, None
    p = c / n
    d = 1 + Z * Z / n
    mid = (p + Z * Z / (2 * n)) / d
    hw = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return r1(100 * (mid - hw)), r1(100 * (mid + hw))


def qn(x):
    return f'Q{x[-1]} {x[:4]}'


def course(k):
    t = P['trends'][k]
    q, nq = t['q'], t['n_q']
    ei = [i for i, x in enumerate(q) if x in EARLY]
    li = [i for i, x in enumerate(q) if x in LATE]
    solid = [i for i, n in enumerate(nq) if n >= MIN_N]
    return t, q, nq, ei, li, solid


def label(it):
    return it.get('l') or it['c']


# ------------------------------------------------------------------ 1. churn: how much of each course moved
def tvd(a, b):
    return 0.5 * sum(abs(x - y) for x, y in zip(a, b))


def churn(k, level):
    t, q, nq, ei, li, _ = course(k)
    items = t['groups'] if level == 'group' else t['cats']
    n1, n2 = sum(nq[i] for i in ei), sum(nq[i] for i in li)
    c1 = [sum(counts(it, nq)[i] for i in ei) for it in items]
    c2 = [sum(counts(it, nq)[i] for i in li) for it in items]
    c1.append(max(0, n1 - sum(c1)))   # everything outside the published list, so shares add to 100
    c2.append(max(0, n2 - sum(c2)))
    e = [c / n1 for c in c1]
    l_ = [c / n2 for c in c2]
    obs = 100 * tvd(e, l_)
    pooled = [(a + b) / (n1 + n2) for a, b in zip(c1, c2)]
    cum = []
    acc = 0
    for p_ in pooled:
        acc += p_
        cum.append(acc)

    def draw(n):
        out = [0] * len(pooled)
        for _ in range(n):
            u = random.random()
            for j, cv in enumerate(cum):
                if u <= cv:
                    out[j] += 1
                    break
            else:
                out[-1] += 1
        return [x / n for x in out]

    sims = [100 * tvd(draw(n1), draw(n2)) for _ in range(1500)]
    exp = statistics.mean(sims)
    p = (1 + sum(1 for s in sims if s >= obs)) / (len(sims) + 1)
    return dict(obs=r1(obs), chance=r1(exp), beyond=r1(obs - exp), p=round(p, 3), n1=n1, n2=n2,
                p95=r1(sorted(sims)[int(0.95 * len(sims))]))


# ------------------------------------------------------------------ 2. concentration over time
def concentration(k):
    t, q, nq, ei, li, solid = course(k)
    top = t['cats'][:5]
    cs = [counts(it, nq) for it in top]
    by_q = []
    for i in range(len(q)):
        c = sum(x[i] for x in cs)
        lo, hi = wilson(c, nq[i])
        by_q.append(dict(q=q[i], n=nq[i], share=r1(100 * c / nq[i]) if nq[i] else None, lo=lo, hi=hi, low=nq[i] < MIN_N))
    c1, c2 = sum(sum(x[i] for x in cs) for i in ei), sum(sum(x[i] for x in cs) for i in li)
    n1, n2 = sum(nq[i] for i in ei), sum(nq[i] for i in li)
    pv = ztest(c1, n1, c2, n2)
    move = 100 * (c2 / n2 - c1 / n1)
    return dict(dishes=[label(it) for it in top], q=by_q, early=r1(100 * c1 / n1), late=r1(100 * c2 / n2),
                move=r1(move), p=round(pv, 3), sig=pv < 0.05,
                verdict=('converging' if move > 0 else 'spreading out') if pv < 0.05 else 'holding steady')


# ------------------------------------------------------------------ 3. lifecycle stage for every dish
STAGES = ['Rising', 'Peaked', 'Steady staple', 'Recovering', 'Fading', 'No clear pattern']


def lifecycle(k):
    t, q, nq, ei, li, solid = course(k)
    med = statistics.median(it['pct'] for it in t['cats'])
    out = []
    for it in t['cats']:
        c = counts(it, nq)
        s = [it['share'][i] for i in solid]
        cs = [c[i] for i in solid]
        ns = [nq[i] for i in solid]
        ipk = max(range(len(s)), key=lambda j: s[j])
        imn = min(range(len(s)), key=lambda j: s[j])
        last = len(s) - 1
        p_peak = ztest(cs[ipk], ns[ipk], cs[last], ns[last])
        p_rise = ztest(cs[0], ns[0], cs[ipk], ns[ipk])
        p_dip = ztest(cs[imn], ns[imn], cs[last], ns[last])
        p_fall = ztest(cs[0], ns[0], cs[imn], ns[imn])
        mean = sum(cs) / sum(ns) * 100 if sum(ns) else 0
        # spread beyond sampling noise: chi-square test of the solid quarters against one shared share
        chi = sum((cs[j] - ns[j] * mean / 100) ** 2 / (ns[j] * mean / 100) for j in range(len(s))) if mean else 0
        p_flat = 1 - chi2_cdf(chi, len(s) - 1)
        why = ''
        if it['sig'] and it['move'] > 0:
            st, why = 'Rising', f"Recent share {it['late']}% against {it['early']}% earlier, a clear move"
        elif it['sig'] and it['move'] < 0:
            st, why = 'Fading', f"Recent share {it['late']}% against {it['early']}% earlier, a clear move"
        elif 0 < ipk < last and p_peak < 0.05 and p_rise < 0.1:
            st, why = 'Peaked', f"Rose to {s[ipk]}% in {qn(q[solid[ipk]])}, then fell back to {s[last]}% by {qn(q[solid[last]])}"
        elif 0 < imn < last and p_dip < 0.05 and p_fall < 0.1:
            st, why = 'Recovering', f"Dipped to {s[imn]}% in {qn(q[solid[imn]])}, back to {s[last]}% by {qn(q[solid[last]])}"
        elif p_flat > 0.5 and it['pct'] >= med:
            st, why = 'Steady staple', f"Between {min(s)}% and {max(s)}% in every full quarter"
        else:
            st, why = 'No clear pattern', 'Quarter-to-quarter changes are within what sampling alone would give'
        out.append(dict(course=k, cl=t['label'], l=label(it), g=it.get('g', ''), pct=it['pct'], n=it['n'],
                        early=it['early'], late=it['late'], move=it['move'], p=it['p'], sig=it['sig'],
                        share=it['share'], stage=st, why=why, p_flat=round(p_flat, 3)))
    return out


def chi2_cdf(x, k):
    """Regularised lower incomplete gamma P(k/2, x/2), by series (k is small here)."""
    if x <= 0:
        return 0.0
    a, z = k / 2, x / 2
    term = 1 / a
    total = term
    n = 1
    while n < 500:
        term *= z / (a + n)
        total += term
        if term < 1e-12 * total:
            break
        n += 1
    return min(1.0, total * math.exp(-z + a * math.log(z) - math.lgamma(a)))


# ------------------------------------------------------------------ 4. where the share went (groups)
def flows(k):
    t, *_ = course(k)
    gs = [dict(l=g['c'], early=g['early'], late=g['late'], move=g['move'], p=g['p'], sig=g['sig'])
          for g in t['groups']]
    other_e = r1(100 - sum(g['early'] for g in gs))
    other_l = r1(100 - sum(g['late'] for g in gs))
    gs.append(dict(l='Everything else', early=other_e, late=other_l, move=r1(other_l - other_e), p=None, sig=False))
    lost = sum(-g['move'] for g in gs if g['move'] < 0)
    won = sum(g['move'] for g in gs if g['move'] > 0)
    return dict(groups=sorted(gs, key=lambda g: g['move']), lost=r1(lost), won=r1(won))


# ------------------------------------------------------------------ 5. menu mix by quarter (groups)
def mix(k):
    t, q, nq, *_ = course(k)
    top = t['groups'][:5]
    rows = [dict(l=g['c'], share=g['share']) for g in top]
    rest = [None if not n else r1(100 - sum((g['share'][i] or 0) for g in top)) for i, n in enumerate(nq)]
    rows.append(dict(l='Everything else', share=rest))
    return dict(q=q, n_q=nq, low=[n < MIN_N for n in nq], rows=rows)


# ------------------------------------------------------------------ 6. forecasts for the clear movers
def forecasts():
    out = []
    for k in FOOD:
        t, q, nq, ei, li, solid = course(k)
        faded = {i for i, n in enumerate(nq) if n < MIN_N}
        for it in t['cats'] + t['groups']:
            if not it['sig']:
                continue
            ai, proj = project(it['share'], faded=faded, steps=3)
            labs = next_quarters(q[ai], 3)
            out.append(dict(course=k, cl=t['label'], l=label(it), level='Dish' if 'g' in it else 'Group',
                            move=it['move'], p=it['p'], q=q, share=it['share'], low=[i in faded for i in range(len(q))],
                            anchor=ai, fq=labs, f=[[r1(m), r1(lo), r1(hi)] for m, lo, hi in proj]))
    out.sort(key=lambda r: -abs(r['move']))
    return out


def next_quarters(qs, n):
    y, k = int(qs[:4]), int(qs[-1])
    out = []
    for _ in range(n):
        k += 1
        if k == 5:
            y, k = y + 1, 1
        out.append(f'{y}-Q{k}')
    return out


# ------------------------------------------------------------------ build
CH = {k: dict(group=churn(k, 'group'), dish=churn(k, 'dish')) for k in FOOD}
CO = {k: concentration(k) for k in FOOD}
LC = [r for k in FOOD for r in lifecycle(k)]
FL = {k: flows(k) for k in FOOD}
MX = {k: mix(k) for k in FOOD}
FC = forecasts()
LABEL = {k: P['trends'][k]['label'] for k in FOOD}


def stage_counts(k):
    return {s: sum(1 for r in LC if r['course'] == k and r['stage'] == s) for s in STAGES}


PROPER = re.compile(r'^(Sunday|Scottish|British|Asian|Indian|Italian|Mexican|Mediterranean|Middle|Japanese|New York|Irn|Biscoff|Basque|Victoria)')


def lc_(s):
    return s if PROPER.match(s) else s[0].lower() + s[1:]


# conclusions, written from the numbers so they stay true after each refresh
most = max(FOOD, key=lambda k: CH[k]['group']['beyond'])
least = min(FOOD, key=lambda k: CH[k]['group']['beyond'])
real = [k for k in FOOD if CH[k]['group']['p'] < 0.05]
conv = [k for k in FOOD if CO[k]['sig'] and CO[k]['move'] > 0]
spread = [k for k in FOOD if CO[k]['sig'] and CO[k]['move'] < 0]
staples = sorted((r for r in LC if r['stage'] == 'Steady staple'), key=lambda r: -r['pct'])
peaked = sorted((r for r in LC if r['stage'] == 'Peaked'), key=lambda r: -r['pct'])
rising = sorted((r for r in LC if r['stage'] == 'Rising'), key=lambda r: -r['move'])
fading = sorted((r for r in LC if r['stage'] == 'Fading'), key=lambda r: r['move'])


def names(rows, n=3):
    xs = [f"{lc_(r['l'])} ({r['cl'].lower()})" for r in rows[:n]]
    return ', '.join(xs[:-1]) + (' and ' + xs[-1] if len(xs) > 1 else xs[0] if xs else '')


def jn(xs):
    xs = list(xs)
    return ', '.join(xs[:-1]) + ' and ' + xs[-1] if len(xs) > 1 else (xs[0] if xs else '')


public_find = [
    f"{LABEL[most]}s changed most: {CH[most]['group']['obs']}% of answers sit in a different food group than in late 2025, "
    f"against {CH[most]['group']['chance']}% that sampling alone would produce.",
    (f"{jn(LABEL[k] + 's' for k in real)} have moved beyond chance; "
     f"{jn(LABEL[k].lower() + 's' for k in FOOD if k not in real)} are broadly where they were, which makes them safe ground for a range.")
    if real else "No course has moved beyond what sampling alone would give.",
    (f"Guests are converging on favourites in {jn(LABEL[k].lower() for k in conv)}" + (f" and spreading out in {jn(LABEL[k].lower() for k in spread)}." if spread else '.'))
    if conv else (f"Guests are spreading out in {jn(LABEL[k].lower() for k in spread)}: the top five dishes there take a smaller share than they did." if spread
                  else 'The five favourite dishes in each course hold the same share they did a year ago.'),
    f"{len(staples)} dishes are steady staples, holding their share in every full quarter, led by {names(staples)}." if staples else '',
]
partner_find = public_find[:2] + [
    f"Clearly rising: {names(rising, 4)}." if rising else '',
    f"Clearly fading: {names(fading, 4)}." if fading else '',
    f"Past their peak: {names(peaked, 3)} rose to a high in a middle quarter and have since fallen back clearly. Treat them as mature, not growing." if peaked else '',
    f"In {LABEL[most].lower()}s, {FL[most]['lost']} points of share left the falling groups, led by {lc_(FL[most]['groups'][0]['l'])} ({FL[most]['groups'][0]['move']:+.1f} pts); "
    f"{lc_(FL[most]['groups'][-1]['l'])} gained most ({FL[most]['groups'][-1]['move']:+.1f} pts).",
    public_find[2],
]
public_find = [x for x in public_find if x]
partner_find = [x for x in partner_find if x]

meta = dict(last=P['last'], early=EARLY, late=LATE, min_n=MIN_N, n=P['n'], n_all=P['n_all'],
            stages=STAGES, courses=[[k, LABEL[k]] for k in FOOD])

public = dict(meta=meta, find=public_find,
              churn=[dict(course=k, cl=LABEL[k], **{kk: CH[k]['group'][kk] for kk in ('obs', 'chance', 'beyond', 'p', 'p95', 'n1', 'n2')},
                          dish=CH[k]['dish']['obs'], dish_chance=CH[k]['dish']['chance']) for k in FOOD],
              conc=[dict(course=k, cl=LABEL[k], **CO[k]) for k in FOOD],
              stages=[dict(course=k, cl=LABEL[k], c=stage_counts(k)) for k in FOOD],
              staples=[dict(course=r['course'], cl=r['cl'], l=r['l'], pct=r['pct'],
                            lo=min(v for v, n in zip(r['share'], P['trends'][r['course']]['n_q']) if n >= MIN_N),
                            hi=max(v for v, n in zip(r['share'], P['trends'][r['course']]['n_q']) if n >= MIN_N)) for r in staples])
partner = dict(meta=meta, find=partner_find, churn=public['churn'], conc=public['conc'], stages=public['stages'], staples=public['staples'],
               life=LC, flows=[dict(course=k, cl=LABEL[k], **FL[k]) for k in FOOD],
               mix=[dict(course=k, cl=LABEL[k], **MX[k]) for k in FOOD], fc=FC)

hdr = '/* Generated by tools/build_trends.py on ' + P['built'] + '. '
with open('trend-public.js', 'w', encoding='utf-8') as f:
    f.write(hdr + 'Public: course-level trend analysis only. */\nwindow.DM_TRENDP=' + json.dumps(public, ensure_ascii=False, separators=(',', ':')) + ';\n')
with open('partner/trend-data.js', 'w', encoding='utf-8') as f:
    f.write(hdr + 'Partner only (behind sign-in). */\nwindow.DM_TRENDX=' + json.dumps(partner, ensure_ascii=False, separators=(',', ':')) + ';\n')

print('churn', {k: (CH[k]['group']['obs'], CH[k]['group']['chance'], CH[k]['group']['p']) for k in FOOD})
print('conc', {k: (CO[k]['early'], CO[k]['late'], CO[k]['p']) for k in FOOD})
print('stages', {k: stage_counts(k) for k in FOOD})
print('forecasts', len(FC))
for x in partner_find:
    print(' -', x)
