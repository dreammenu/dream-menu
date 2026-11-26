"""Rebuild the four food-course trend blocks in partner-data.js from the recoded answers (sheet rows to 1280,
plus interview 1340 from the 24 Nov batch, which the sheet has not coded). Every category gets a series; the
published top 14 dishes and top 10 groups keep their role, and 'all' holds every dish with MIN_N+ answers.
Needs a fresh export of the Responses sheet (answers, categories and timestamps for the four food columns) as rows.json, ts.json and catlist.json in /tmp/audit; see tools/data/category-audit-2026-11-26.json for the recodes it applies."""
import json, math, re, sys, datetime, collections
sys.path.insert(0, 'tools/data'); sys.path.insert(0, '/tmp/audit')
from category_recodes_2026_11_26 import R, MERGE, NEW, LABEL, GROUP, STEAK_CUTS
ROOT = '/home/claude/dream-menu/'
MIN_N = 10
def load(fn, var):
    s = open(ROOT + fn, encoding='utf-8').read(); m = re.search(r'window\.' + var + r'\s*=\s*', s)
    obj, end = json.JSONDecoder().raw_decode(s[m.end():]); return s[:m.end()], obj, s[m.end() + end:]
def ztest(c1, n1, c2, n2):
    if not n1 or not n2: return 1.0
    pp = (c1 + c2) / (n1 + n2); se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    return 1.0 if se == 0 else math.erfc(abs((c2 / n2 - c1 / n1) / se) / math.sqrt(2))
def qof(d): return f'{d.year}-Q{(d.month - 1) // 3 + 1}'
rows = json.load(open('/tmp/audit/rows.json')); ts = json.load(open('/tmp/audit/ts.json'))
hP, P, tP = load('partner-data.js', 'DM_PARTNER'); _, L, _ = load('dm-labels.js', 'DML')
CL = {}
for r in json.load(open('/tmp/audit/catlist.json'))[1:]:
    kk = {'Starter': 's', 'Main': 'm', 'Side': 'd', 'Dessert': 'p'}.get(r[1])
    if kk: CL[(kk, r[2])] = (r[3], r[4])
rec = {(k, r): n for k, r, n in R}; merged = {o: n for (k, o), n in MERGE.items()}
def par(k, c):
    if c in NEW: return NEW[c][1]
    if c in GROUP: return GROUP[c]
    return CL.get((k, c), (None, (L.get(c) or [None, 'Other answers'])[1]))[1]
OLDL = {(k, it['c']): it.get('l') for k in 'smdp' for it in P['trends'][k]['cats']}
def lab(k, c):
    if c == 'Creamed spinach / greens': return 'Green vegetables'
    if c in LABEL: return LABEL[c]
    if c in NEW: return NEW[c][0]
    return OLDL.get((k, c)) or (L.get(c) or [None])[0] or CL.get((k, c), (c,))[0]
b1281 = next(x for x in json.load(open(ROOT + 'tools/data/new-interviews-2026-11-24.json'))['rows'] if x['row'] == '1281')
early, late = P['method']['early'], P['method']['late']
for k in 'smdp':
    t = P['trends'][k]; q = t['q']; qi = {x: i for i, x in enumerate(q)}
    ans = []
    for r in rows:
        if r['course'] == k and r['cat'] and r['row'] <= 1280:
            c0 = rec.get((k, r['row']), r['cat']); c = merged.get(c0, c0)
            d = datetime.datetime.strptime(ts[str(r['row'])][:10], '%d/%m/%Y')
            ans.append((qof(d), c, c0))
    if b1281.get(k): ans.append((qof(datetime.date.fromisoformat(b1281['date'])), merged.get(b1281[k], b1281[k]), b1281[k]))
    ans = [(qq, c, c0) for qq, c, c0 in ans if c != 'Other' and qq in qi]
    nq = [0] * len(q); cats = collections.defaultdict(lambda: [0] * len(q)); groups = collections.defaultdict(lambda: [0] * len(q))
    cuts = collections.defaultdict(lambda: [0] * len(q))
    for qq, c, c0 in ans:
        nq[qi[qq]] += 1; cats[c][qi[qq]] += 1; groups[par(k, c)][qi[qq]] += 1
        if c == 'Steak (unspecified cut)': cuts[c0][qi[qq]] += 1
    N = sum(nq); ei = [i for i, x in enumerate(q) if x in early]; li = [i for i, x in enumerate(q) if x in late]
    n1, n2 = sum(nq[i] for i in ei), sum(nq[i] for i in li)
    def item(c, cnt, is_cat):
        c1, c2 = sum(cnt[i] for i in ei), sum(cnt[i] for i in li)
        it = dict(c=c, n=sum(cnt), pct=round(100 * sum(cnt) / N, 1), share=[round(100 * a / b, 1) if b else None for a, b in zip(cnt, nq)],
                  early=round(100 * c1 / n1, 1), late=round(100 * c2 / n2, 1))
        it['move'] = round(it['late'] - it['early'], 1); it['p'] = round(ztest(c1, n1, c2, n2), 3); it['sig'] = it['p'] < 0.05
        if is_cat: it['l'] = lab(k, c); it['g'] = par(k, c)
        return it
    allc = sorted((item(c, v, True) for c, v in cats.items()), key=lambda x: (-x['n'], x['l']))
    t['n_q'], t['n'] = nq, N; t['low'] = [n < P['min_n'] for n in nq]
    t['cats'] = allc[:14]
    t['all'] = [x for x in allc if x['n'] >= MIN_N]
    if cuts:   # the cut split inside the one Steak dish, for the steak page and the steak report
        CUTL = {'Steak (unspecified cut)': 'Cut not named', 'Chateaubriand / cote de boeuf / T-bone': 'Sharing steaks (chateaubriand, côte de boeuf)',
                'Bavette / flat iron / hanger / picanha': 'Bavette, rump and other cuts', 'Steak frites / steak and chips': 'Steak frites'}
        t['cuts'] = sorted((dict(item(c, v, False), l=CUTL.get(c) or (L.get(c) or [c])[0] or c) for c, v in cuts.items()), key=lambda x: (-x['n'], x['l']))
    t['groups'] = sorted((item(g, v, False) for g, v in groups.items() if g != 'Other answers'), key=lambda x: (-x['n'], x['c']))[:10]
    print(k, N, nq, 'published', [x['l'] for x in t['cats']][-3:], 'all', len(t['all']))
mv = []
for k in P['order']:
    tt = P['trends'][k]
    for level, lst in (('Group', tt['groups']), ('Dish', tt['cats'])):
        for it in lst:
            if it['sig']: mv.append(dict(level=level, course=tt['label'], c=it['c'], l=it.get('l') or it['c'], move=it['move'], p=it['p']))
P['movers'] = sorted(mv, key=lambda x: -x['move'])
P['n'] = P['n']  # interviews count unchanged
open(ROOT + 'partner-data.js', 'w', encoding='utf-8').write(hP + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + tP)
print('movers', len(mv))
