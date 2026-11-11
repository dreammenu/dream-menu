#!/usr/bin/env python3
"""Drinks, restarted: a clean series from the soft and alcoholic drink questions asked since 23 Aug 2026.

Run from the repository root (after add_interviews.py, before build_pages.py):  python3 tools/build_drinks.py

The old single drink question stopped on 23 Aug 2026, so the tested drink trends in partner-data.js end there.
This script starts again from the two new questions. It reads tools/data/drinks-new-series.json (the base rows)
plus any tools/data/new-interviews-*.json row dated after the base file's 'to' date, and writes drinks-new.js
(window.DM_DRINKS): share of answers by drink group and the most-named drinks, overall and per quarter, with
95% ranges. Answers that belong to the other question (a wine given as a soft drink) are left out and counted.
Movement is not tested until two quarters each hold 100 answers.
"""
import glob, json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
Z = 1.959964
MIN_Q = 100

SOFT = {
    'Colas': ['Coca-Cola', 'Diet Coke / Coke Zero', 'Cherry / vanilla cola', 'Dr Pepper'],
    'Irn-Bru': ['Irn Bru'],
    'Lemonade and craft sodas': ['Lemonade / limonata', 'Italian / craft soda', 'Orange soda (Fanta, Orangina, Tango)', 'Cream soda / root beer',
                                 'Ginger beer / ginger ale', 'Cordial / squash (elderflower, Ribena)'],
    'Tea and coffee': ['Coffee (other)', 'Iced tea', 'Tea / chai', 'Iced coffee / iced latte', 'Bubble tea / milk tea', 'Latte / flat white / cappuccino', 'Matcha'],
    'Juice, milk and shakes': ['Juice (orange, apple, fresh)', 'Lassi / smoothie', 'Milkshake', 'Milk'],
    'Water': ['Sparkling / still water'],
    'Energy drinks': ['Energy drink'],
    'Mocktails': ['Mocktail / alcohol-free'],
    'Other soft drinks': ['Soft drink (other)', 'Other'],
}
ALC = {
    'Cocktails': ['Negroni', 'Paloma', 'Hugo / limoncello / other spritz', 'Dirty / classic martini', 'Margarita (classic / frozen)', 'Spicy margarita',
                  "Tommy's margarita", 'Espresso martini', 'Cocktail (other / named house cocktail)', 'Daiquiri', 'Pina colada', 'Old Fashioned',
                  'French martini', 'Aperol spritz', 'Whisky sour / sours', 'Mojito', 'Bloody Mary', 'Long Island iced tea'],
    'Wine and fizz': ['Red wine', 'White wine', 'Rose wine', 'Wine (other)', 'Champagne', 'Prosecco / cava / sparkling', 'Port / sherry / dessert wine'],
    'Beer and cider': ['Lager / pilsner', 'Beer (other)', 'Guinness / stout', 'IPA / craft beer', 'Cider'],
    'Spirits': ['Whisky / dram', 'Tequila / mezcal', 'Vodka drinks', 'Gin and tonic', 'Dark and stormy / rum drinks', 'Sake / soju'],
    'Alcohol-free instead': ['Mocktail / alcohol-free'],
    'Other': ['Other'],
}
NICE = {'Diet Coke / Coke Zero': 'Diet Coke and Coke Zero', 'Irn Bru': 'Irn-Bru', 'Lemonade / limonata': 'Lemonade', 'Italian / craft soda': 'Craft sodas',
        'Orange soda (Fanta, Orangina, Tango)': 'Orange soda', 'Cream soda / root beer': 'Cream soda', 'Ginger beer / ginger ale': 'Ginger beer',
        'Cocktail (other / named house cocktail)': 'House cocktails', 'Dirty / classic martini': 'Martini', 'Whisky / dram': 'Whisky',
        'Lager / pilsner': 'Lager', 'Margarita (classic / frozen)': 'Margarita', 'Mocktail / alcohol-free': 'Alcohol-free', 'Guinness / stout': 'Guinness and stout',
        'Juice (orange, apple, fresh)': 'Juice', 'Sparkling / still water': 'Water', 'Tea / chai': 'Tea', 'Soft drink (other)': 'Other soft drinks',
        'Beer (other)': 'Beer', 'Wine (other)': 'Wine (type not named)', 'Tequila / mezcal': 'Tequila and mezcal', 'Coffee (other)': 'Coffee',
        'Prosecco / cava / sparkling': 'Prosecco and sparkling', 'Dark and stormy / rum drinks': 'Rum drinks'}


def quarter(d):
    return f'{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}'


def wilson(c, n):
    if not n:
        return None, None
    p = c / n
    d = 1 + Z * Z / n
    mid = (p + Z * Z / (2 * n)) / d
    hw = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return round(100 * max(0, mid - hw), 1), round(100 * (mid + hw), 1)


base = json.load(open('tools/data/drinks-new-series.json', encoding='utf-8'))
rows = [dict(q=r['period'], k=r['k'], a=r['a']) for r in base['rows']]
last = base['to']
for fn in sorted(glob.glob('tools/data/new-interviews-*.json')):
    for r in json.load(open(fn, encoding='utf-8'))['rows']:
        if r['date'] > base['to']:
            rows.append(dict(q=quarter(r['date']), k=r.get('k'), a=r.get('a')))
            last = max(last, r['date'])
QS = sorted({r['q'] for r in rows})


def series(key, groups, label):
    of = {c: g for g, cs in groups.items() for c in cs}
    ans = [(r['q'], r[key]) for r in rows if r[key]]
    ok = [(q, c) for q, c in ans if c in of]
    n = len(ok)
    nq = {q: sum(1 for x, _ in ok if x == q) for q in QS}
    out_g = []
    for g in groups:
        c = sum(1 for _, x in ok if of[x] == g)
        if not c:
            continue
        lo, hi = wilson(c, n)
        out_g.append(dict(l=g, n=c, pct=round(100 * c / n, 1), lo=lo, hi=hi,
                          q=[round(100 * sum(1 for qq, x in ok if qq == q and of[x] == g) / nq[q], 1) if nq[q] else None for q in QS]))
    out_g.sort(key=lambda x: -x['n'])
    cnt = {}
    for _, x in ok:
        cnt[x] = cnt.get(x, 0) + 1
    top = [dict(l=NICE.get(c, c), g=of[c], n=k, pct=round(100 * k / n, 1)) for c, k in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
    return dict(label=label, n=n, answered=len(ans), left_out=len(ans) - n, n_q=[nq[q] for q in QS], groups=out_g, top=top)


soft = series('k', SOFT, 'Soft drink')
alc = series('a', ALC, 'Alcoholic drink')
af = next((g for g in alc['groups'] if g['l'] == 'Alcohol-free instead'), None)
ready = sum(1 for n in alc['n_q'] if n >= MIN_Q) >= 2
find = [
    f"{soft['groups'][0]['l']} lead the soft drink round with {soft['groups'][0]['pct']}% of answers; {soft['top'][0]['l']} is the single most-named soft drink ({soft['top'][0]['pct']}%).",
    f"{alc['groups'][0]['l']} take {alc['groups'][0]['pct']}% of alcoholic drink answers, ahead of {alc['groups'][1]['l'].lower()} ({alc['groups'][1]['pct']}%) and {alc['groups'][2]['l'].lower()} ({alc['groups'][2]['pct']}%).",
]
if af:
    find.append(f"{af['pct']}% answer the alcoholic drink question with something alcohol-free: a built-in read on how many guests don’t drink.")
D = dict(meta=dict(start='2026-08-23', last=last, q=QS, min_q=MIN_Q, ready=ready,
                   note='A new series from the soft and alcoholic drink questions asked since 23 August 2026. It is a baseline: movement will be tested once two quarters each hold 100 answers.'),
         find=find, soft=soft, alc=alc)
open('drinks-new.js', 'w', encoding='utf-8').write('/* Generated by tools/build_drinks.py. Public: shares of answers only. */\nwindow.DM_DRINKS=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('soft', soft['n'], soft['n_q'], 'left out', soft['left_out'], [(g['l'], g['pct']) for g in soft['groups'][:4]])
print('alc', alc['n'], alc['n_q'], 'left out', alc['left_out'], [(g['l'], g['pct']) for g in alc['groups']])
for f in find:
    print(' -', f)
