#!/usr/bin/env python3
"""Adds newly coded Dream Menu interviews to the site's data without a full rebuild.

Run from the repository root:
  python3 tools/add_interviews.py tools/data/new-interviews-2026-10-28.json

The full build pipeline (sheet export, machine coding, venue matching) lives outside this
repository. This script takes a small batch of interviews that have already been coded by hand
into the refined dish categories (see the JSON file) and folds them into partner-data.js:

  * food trend lines (starter, main, side, dessert): per-quarter counts are recovered exactly from
    the published shares and answer counts, the new answers are added to their quarter, and shares,
    early/recent pools, the two-proportion z-test, the clear-mover flag and the movers list are
    recomputed. Drinks trend tests use the original drink question only (retired 23 Aug 2026), so new
    interviews do not change them.
  * guilty pleasures and "bin it" counts, interviews per quarter, respondent group sizes, totals.

Only the categories already published (top groups and top dishes per course) can move; a category
outside the published list stays outside it until the next full rebuild.
Venue mentions are added separately by tools/add_venues.py.
"""
import json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    obj, end = json.JSONDecoder().raw_decode(s[m.end():])
    return s[:m.start()], obj, s[m.end() + end:]


def quarter(d):
    y, mth = int(d[:4]), int(d[5:7])
    return f'{y}-Q{(mth - 1) // 3 + 1}'


def ztest(c1, n1, c2, n2):
    if not n1 or not n2:
        return 1.0
    pp = (c1 + c2) / (n1 + n2)
    se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    return math.erfc(abs((c2 / n2 - c1 / n1) / se) / math.sqrt(2))


def main(batch_fn):
    batch = json.load(open(batch_fn, encoding='utf-8'))['rows']
    head, P, tail = load('partner-data.js', 'DM_PARTNER')
    _, L, _ = load('dm-labels.js', 'DML')
    early, late = P['method']['early'], P['method']['late']
    parent = lambda c: (L.get(c) or [c, ''])[1]

    for k in ('s', 'm', 'd', 'p'):   # food courses only (see docstring)
        t = P['trends'][k]
        q, nq = t['q'], list(t['n_q'])
        items = t['groups'] + t['cats']
        counts = {id(it): [round((s or 0) * n / 100) if n else 0 for s, n in zip(it['share'], nq)] for it in items}
        for r in batch:
            c = r.get(k)
            if not c:
                continue
            qi = q.index(quarter(r['date']))
            nq[qi] += 1
            for it in t['groups']:
                if it['c'] == parent(c):
                    counts[id(it)][qi] += 1
            for it in t['cats']:
                if it['c'] == c:
                    counts[id(it)][qi] += 1
        t['n_q'] = nq
        t['n'] = sum(nq)
        t['low'] = [n < P['min_n'] for n in nq]
        ei = [i for i, x in enumerate(q) if x in early]
        li = [i for i, x in enumerate(q) if x in late]
        n1, n2 = sum(nq[i] for i in ei), sum(nq[i] for i in li)
        for it in items:
            cnt = counts[id(it)]
            c1, c2 = sum(cnt[i] for i in ei), sum(cnt[i] for i in li)
            it['n'] = sum(cnt)
            it['pct'] = round(100 * it['n'] / t['n'], 1)
            it['share'] = [round(100 * c / n, 1) if n else None for c, n in zip(cnt, nq)]
            it['early'] = round(100 * c1 / n1, 1)
            it['late'] = round(100 * c2 / n2, 1)
            it['move'] = round(it['late'] - it['early'], 1)
            it['p'] = round(ztest(c1, n1, c2, n2), 3)
            it['sig'] = it['p'] < 0.05
        t['groups'].sort(key=lambda x: -x['n'])
        t['cats'].sort(key=lambda x: -x['n'])

    # movers: every clear move across all courses, largest rise first
    mv = []
    for k in P['order']:
        t = P['trends'][k]
        for level, lst in (('Group', t['groups']), ('Dish', t['cats'])):
            for it in lst:
                if it['sig']:
                    mv.append(dict(level=level, course=t['label'], c=it['c'], l=it.get('l') or it['c'],
                                   move=it['move'], p=it['p']))
    P['movers'] = sorted(mv, key=lambda x: -x['move'])

    # guilty pleasures and bin it (published top tens)
    for key in ('guilty', 'bin'):
        lst = P['extra'][key]
        for r in batch:
            lab = r.get(key)
            for row in lst:
                if lab and row[0] == lab:
                    row[1] += 1
        lst.sort(key=lambda x: -x[1])
    iq = P['extra']['interviews_q']
    for r in batch:
        iq[P['trends']['s']['q'].index(quarter(r['date']))] += 1
    for g in P['groups']:
        g['n'] += sum(1 for r in batch if r['group'] == g['g'])

    # counts behind the static home and insights figures (debates, course cards, drink card)
    sc_fn = 'tools/data/static-counts.json'
    SC = json.load(open(sc_fn, encoding='utf-8'))
    if batch_fn not in SC['applied']:
        for key in ('coke', 'tea', 'pineapple', 'water'):
            d = SC['debates'][key]
            for r in batch:
                if r.get(key) in d['c']:
                    d['c'][r[key]] += 1
                    d['n'] += 1
        for k in ('s', 'm', 'd', 'p'):
            SC['course_card_answers'][k] += sum(1 for r in batch if r.get(k))
        dc = SC['drink_card']
        dc['n'] += sum(1 for r in batch if r.get('k') or r.get('a'))
        for r in batch:
            for k in ('k', 'a'):
                lab = dc['map'].get(r.get(k) or '')
                for row in dc['c']:
                    if row[0] == lab:
                        row[1] += 1
        dc['c'].sort(key=lambda x: -x[1])
        SC['applied'].append(batch_fn)
        json.dump(SC, open(sc_fn, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    answered = sum(1 for r in batch if any(r.get(k) for k in 'smdpka'))
    P['n'] += answered
    P['n_all'] += len(batch)
    P['last'] = max(r['date'] for r in batch)
    P['built'] = '2026-10-28'
    open('partner-data.js', 'w', encoding='utf-8').write(head + 'window.DM_PARTNER=' + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + tail)
    print('partner-data.js: n', P['n'], 'n_all', P['n_all'], 'last', P['last'], 'movers', len(P['movers']))


if __name__ == '__main__':
    main(sys.argv[1])
