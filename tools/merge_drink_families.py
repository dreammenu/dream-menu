"""Fold drink variants into one drink (26 Nov 2026), on the published soft and alcoholic drink lists in partner-data.js.
Shares on one base add up, so the family's share, quarterly series and early/recent pools are sums; the trend test is rerun.
Run after rebuild_food_trends.py (which leaves drinks alone)."""
import json, math, re, sys
sys.path.insert(0, 'tools/data')
from category_recodes_2026_11_26 import DRINK_FAMILY, LABEL2
def load(fn, var):
    s = open(fn, encoding='utf-8').read(); m = re.search(r'window\.' + var + r'\s*=\s*', s)
    obj, end = json.JSONDecoder().raw_decode(s[m.end():]); return s[:m.end()], obj, s[m.end() + end:]
def ztest(c1, n1, c2, n2):
    if not n1 or not n2: return 1.0
    pp = (c1 + c2) / (n1 + n2); se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    return 1.0 if se == 0 else math.erfc(abs((c2 / n2 - c1 / n1) / se) / math.sqrt(2))
h, P, t_ = load('partner-data.js', 'DM_PARTNER')
early, late = P['method']['early'], P['method']['late']
for k, fam in DRINK_FAMILY.items():
    t = P['trends'][k]; q, nq = t['q'], t['n_q']
    n1 = sum(n for x, n in zip(q, nq) if x in early); n2 = sum(n for x, n in zip(q, nq) if x in late)
    by = {it['c']: it for it in t['cats']}
    t.setdefault('parts', {})
    for tgt in sorted(set(fam.values())):
        members = [c for c in [tgt] + [s for s, d in fam.items() if d == tgt] if c in by]
        if len(members) < 2 or tgt not in by:
            continue
        its = [by[c] for c in members]
        t['parts'][tgt] = sorted([dict(x) for x in its], key=lambda x: -x['n'])
        new = dict(by[tgt])
        new['n'] = sum(x['n'] for x in its); new['pct'] = round(sum(x['pct'] for x in its), 1)
        new['share'] = [None if all(x['share'][i] is None for x in its) else round(sum(x['share'][i] or 0 for x in its), 1) for i in range(len(q))]
        new['early'] = round(sum(x['early'] for x in its), 1); new['late'] = round(sum(x['late'] for x in its), 1)
        new['move'] = round(new['late'] - new['early'], 1)
        new['p'] = round(ztest(round(new['early'] * n1 / 100), n1, round(new['late'] * n2 / 100), n2), 3); new['sig'] = new['p'] < 0.05
        new['l'] = LABEL2.get(tgt, new.get('l'))
        t['cats'] = [x for x in t['cats'] if x['c'] not in members] + [new]
        by = {it['c']: it for it in t['cats']}
    for it in t['cats']:
        if it['c'] in LABEL2: it['l'] = LABEL2[it['c']]
    t['cats'].sort(key=lambda x: -x['n'])
    print(k, [(x['l'], x['n'], x['pct']) for x in t['cats']])
mv = []
for k in P['order']:
    tt = P['trends'][k]
    for level, lst in (('Group', tt['groups']), ('Dish', tt['cats'])):
        for it in lst:
            if it['sig']: mv.append(dict(level=level, course=tt['label'], c=it['c'], l=it.get('l') or it['c'], move=it['move'], p=it['p']))
P['movers'] = sorted(mv, key=lambda x: -x['move'])
open('partner-data.js', 'w', encoding='utf-8').write(h + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + t_)
