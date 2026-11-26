"""Sub layers: one source for every page that opens a food group or a dish (26 Nov 2026).

Three levels, each counted once: a food group (seafood), the dishes inside it (scallops, oysters...), and for
family dishes the kinds inside the dish (steak by cut, chips and fries by kind). Rankings show the group or the
dish; the next level opens under it rather than being split out as rows of its own.

Every figure comes from partner-data.js (the audited categories, rebuilt from the answers), so a sub layer always
matches the dish pages. Dishes with fewer than ten answers, leftovers ("other seafood") and anything else in the
group that is not ranked as a dish are shown together as one "Other" line, so the layers add up to the group.

    from sublayers import sub_layers
    S = sub_layers(P)   # {'Seafood': {'s': {'n', 'base', 'p', 'label', 'items': [{'l','n','p','slug', 'parts'?}]}}}
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', 'and')).strip('-')


def parts_of(T, code):
    parts = (T.get('parts') or {}).get(code)
    if not parts:
        return None
    return [dict(l=x['l'], n=x['n'], p=round(100 * x['n'] / T['n'], 1)) for x in parts]


def sub_layers(P, dish_slugs=None):
    if dish_slugs is None:
        d = os.path.join(ROOT, 'trends')
        dish_slugs = {f[:-5] for f in os.listdir(d) if f.endswith('.html')} if os.path.isdir(d) else set()
    out = {}
    for k, T in P['trends'].items():
        dishes = T.get('all') or T['cats']
        for g in T['groups']:
            mine = [it for it in dishes if it.get('g') == g['c']]
            items = []
            for it in sorted(mine, key=lambda x: (-x['n'], x.get('l') or x['c'])):
                row = dict(l=it.get('l') or it['c'], n=it['n'], p=round(100 * it['n'] / T['n'], 1))
                s = _slug(row['l'])
                if s in dish_slugs:
                    row['slug'] = s
                pr = parts_of(T, it['c'])
                if pr:
                    row['parts'] = pr
                items.append(row)
            gap = g['n'] - sum(r['n'] for r in items)
            if gap > 0:
                items.append(dict(l=f'Other {g["c"].lower()}', n=gap, p=round(100 * gap / T['n'], 1), other=1))
            if len(items) < 2:
                continue
            out.setdefault(g['c'], {})[k] = dict(n=g['n'], base=T['n'], p=g['pct'], label=T['label'], items=items)
    return out
