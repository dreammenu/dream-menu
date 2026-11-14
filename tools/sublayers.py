"""Sub layers inside a food group: one source for every page that shows them.

Seafood is the first group with sub layers. Counts for dishes the site tracks come from
partner-data.js (so they match dish pages and the scorecard exactly); the rest come from
tools/data/seafood-sub-layers.json (the Responses sheet pivot). If the two sources still
differ from the group total, the gap is shown as its own line rather than hidden.

    from sublayers import sub_layers
    S = sub_layers(P)   # {'Seafood': {'s': {'n': 439, 'base': 1225, 'items': [{'l','n','p','slug'}...]}, ...}}
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {'Seafood': os.path.join(ROOT, 'tools', 'data', 'seafood-sub-layers.json')}


def _slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', 'and')).strip('-')


def sub_layers(P, dish_slugs=None):
    if dish_slugs is None:
        d = os.path.join(ROOT, 'trends')
        dish_slugs = {f[:-5] for f in os.listdir(d) if f.endswith('.html')} if os.path.isdir(d) else set()
    out = {}
    for group, fn in FILES.items():
        if not os.path.exists(fn):
            continue
        raw = json.load(open(fn, encoding='utf-8'))
        out[group] = {}
        for k, T in P['trends'].items():
            g = next((x for x in T['groups'] if x['c'] == group), None)
            if not g or not raw.get(k):
                continue
            tracked = {(c.get('l') or c['c']): c['n'] for c in T['cats'] if c.get('g') == group}
            counts = dict(raw[k])
            counts.update(tracked)
            gap = g['n'] - sum(counts.values())
            items = [dict(l=l, n=n) for l, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])) if n > 0]
            if gap > 0:
                items.append(dict(l=f'Other {group.lower()}', n=gap))
            for it in items:
                it['p'] = round(100 * it['n'] / T['n'], 1)
                s = _slug(it['l'])
                if s in dish_slugs:
                    it['slug'] = s
            out[group][k] = dict(n=g['n'], base=T['n'], p=g['pct'], label=T['label'], read=raw.get('read'), items=items)
    return out
