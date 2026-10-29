#!/usr/bin/env python3
"""Applies new award editions to awards.js without the full awards build.

Run from the repository root:
  python3 tools/update_awards.py tools/data/awards-update-2026-10-29.json

The full awards build (MICHELIN extract, list matching, gazetteer) lives outside this repository.
This script takes a small JSON file of changes and applies them in place:

  rank      add a ranked edition of a list to places already on the map
            {"code": "fwx", "year": 2026, "rows": [[rank, place_id], ...]}
  replace   swap one award record for another on an existing place
            {"place": id, "from": [code, year], "to": [code, year]}
  add       a new place with its awards (same field order as awards.js places)
  sources   replacement notes for the source list
  built     build date written to meta

Counts per award code, totals and each place's tier (its top award in meta.order) are recomputed.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def main(fn):
    U = json.load(open(fn, encoding='utf-8'))
    s = open('awards.js', encoding='utf-8').read()
    m = re.search(r'window\.DM_AWARDS\s*=\s*', s)
    A, end = json.JSONDecoder().raw_decode(s[m.end():])
    head, tail = s[:m.start()], s[m.end() + end:]
    P = {p[0]: p for p in A['places']}
    order = A['meta']['order']
    changed = 0

    for r in U.get('rank', []):
        for rank, pid in r['rows']:
            p = P[pid]  # KeyError means the list entry has no place on the map yet
            p[10] = [a for a in p[10] if not (a[0] in r.get('replaces', [r['code']]) and a[1] == r['year'])]
            p[10].append([r['code'], r['year'], rank])
            changed += 1
    for r in U.get('replace', []):
        p = P[r['place']]
        hit = [a for a in p[10] if a[0] == r['from'][0] and a[1] == r['from'][1]]
        if not hit:
            raise SystemExit(f"{r['place']}: no {r['from']} record")
        p[10] = [a for a in p[10] if a not in hit] + [list(r['to'])]
        changed += 1
    for p in U.get('add', []):
        if p[0] in P:
            raise SystemExit(f'{p[0]} already exists')
        A['places'].append(p)
        P[p[0]] = p
        changed += 1

    # tiers, counts, totals
    for p in A['places']:
        p[9] = min(order.index(a[0]) for a in p[10])
    codes = {}
    for p in A['places']:
        for a in p[10]:
            codes[a[0]] = codes.get(a[0], 0) + 1
    A['meta']['codes'] = codes
    A['meta']['places'] = len(A['places'])
    A['meta']['awards'] = sum(codes.values())
    A['meta']['countries'] = len({p[5] for p in A['places']})
    A['meta']['built'] = U['built']
    for k, note in U.get('sources', {}).items():
        A['sources'][k]['note'] = note

    open('awards.js', 'w', encoding='utf-8').write(head + 'window.DM_AWARDS=' + json.dumps(A, ensure_ascii=False, separators=(',', ':')) + tail)
    print('changes', changed, 'places', A['meta']['places'], 'awards', A['meta']['awards'], 'countries', A['meta']['countries'])


if __name__ == '__main__':
    main(sys.argv[1])
