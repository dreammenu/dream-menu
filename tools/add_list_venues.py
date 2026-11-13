#!/usr/bin/env python3
"""Puts every venue from Gordon's Google Maps list "Dream Menu 2025/26" on the map (13 Nov 2026).

Run from the repository root:
  python3 tools/add_list_venues.py            # writes the spec, then runs add_venues.py with it

Reads tools/data/gmaps/dream-menu-2025-26-list.txt (the list as copied from Google Maps) and
tools/data/gmaps/placements.py (where each new venue goes). List venues have no guest mentions, so
they show on the map as places but do not change any counts in the analysis.
Writes tools/data/gmaps/needs-location.md: open venues that could not be placed with confidence.
"""
import importlib.util, json, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
spec_ = importlib.util.spec_from_file_location('placements', 'tools/data/gmaps/placements.py')
PL = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(PL)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


def norm(x):
    x = unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    x = re.sub(r"[’'`]", '', x); x = re.sub(r'[^a-z0-9]+', ' ', x)
    x = re.sub(r'\b(the|restaurant|ristorante|bar|kitchen|and|cafe|glasgow|edinburgh|ltd|co)\b', ' ', x)
    return re.sub(r'\s+', ' ', x).strip()


def slug(x):
    x = unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', x).strip('-')


ADDR = {204: ('Tudor Hotel', '39 Alexander St, Airdrie ML6 0BA'), 923: ('3 Theberton St', '3 Theberton St, London N1 0QY'),
        1143: ('51 Bell St', '51 Bell St, Glasgow G1 1PA'), 1149: ('7-8 Cadzow Pl', '7-8 Cadzow Pl, Edinburgh'),
        1203: ('87 Brewer St', '87 Brewer St, London W1F 9UX'), 261: ('Malletsheugh', 'Auchenback, Newton Mearns'),
        658: ('Marina del Cantone', 'Marina del Cantone, Massa Lubrense, Naples')}

rows = []
L = open('tools/data/gmaps/dream-menu-2025-26-list.txt', encoding='utf-8').read().splitlines()
for i, l in enumerate(L):
    m = re.match(r'^\s*(\d+)\.\s*(.+)$', l)
    if not m:
        continue
    k, rest = int(m.group(1)), m.group(2).strip()
    mm = re.match(r'^(.*?)(\d\.\d)\(([\d,]+)\)(.*)$', rest)
    name, meta = (mm.group(1).strip(), mm.group(4).strip()) if mm else (rest, '')
    nxt = L[i + 1].strip() if i + 1 < len(L) else ''
    st = 'gone' if 'no longer exists' in nxt else 'closed' if 'Permanently closed' in meta else 'temp' if 'Temporarily closed' in meta else ''
    name = re.sub(r'\s*\|\s*Edinburgh$', ' Edinburgh', name).replace('LtdWholesaler', 'Ltd')
    if k in ADDR:
        name = ADDR[k][0]
    rows.append(dict(k=k, n=name, st=st, meta=re.sub(r'^[^\w£$€]+', '', meta)))

D = load('dm-data.js', 'DM')
byid = {v['i']: v for v in D['venues']}
idx = {}
for v in D['venues']:
    idx.setdefault(norm(v['n']), []).append(v['i'])

out, already, skipped, unplaced = [], [], [], []
for r in rows:
    if r['st'] in ('closed', 'gone'):
        skipped.append(r); continue
    if norm(r['n']) in idx:
        already.append(r); continue
    if r['k'] in PL.SAME:
        already.append(r); continue
    if r['k'] not in PL.PLACE:
        unplaced.append(r); continue
    key, prec = PL.PLACE[r['k']]
    la, lo, city, co, na, area = PL.P[key]
    where = ', '.join(x for x in (area, city) if x)
    vid = slug(r['n']) + '-' + slug(city)
    if vid in byid or any(v['i'] == vid for v in out):
        vid += f"-{r['k']}"
    guess = r['k'] in getattr(PL, 'GUESS', set())
    note = ('From the Dream Menu 2025/26 list. ' + (f'Best guess: placed in {where}; location to be confirmed.' if guess else '') +
            ('' if guess else f'Placed on the street; exact door not checked.' if prec == 'street' else f'Placed in {where}; exact spot not known.'))
    out.append(dict(i=vid, n=r['n'], c=city, tw=area, co=co, na=na, p=prec, la=la, lo=lo,
                    ad=ADDR.get(r['k'], ('', ''))[1], no=note + (' Temporarily closed when saved.' if r['st'] == 'temp' else '')))

os.makedirs('tools/data/gmaps', exist_ok=True)
json.dump(dict(new_venues=out, fix_venues={}, mentions=[]), open('tools/data/gmaps/new-venues-2026-11-13-list.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(dict(rows=[]), open('tools/data/gmaps/no-interviews.json', 'w'), indent=1)
with open('tools/data/gmaps/needs-location.md', 'w', encoding='utf-8') as f:
    f.write('# Dream Menu 2025/26 list: venues still to place\n\nOpen venues from the Google Maps list that could not be placed on the map with confidence from their name or list position. '
            'Add a town (or address) for each to tools/data/gmaps/placements.py and rerun tools/add_list_venues.py.\n\n')
    for r in unplaced:
        f.write(f"- {r['k']}. {r['n']}" + (f" ({r['meta']})" if r['meta'] else '') + '\n')
print(f"list {len(rows)} | already on the map {len(already)} | closed or gone {len(skipped)} | new {len(out)} | still to place {len(unplaced)}")
if '--dry' not in sys.argv:
    subprocess.run([sys.executable, 'tools/add_venues.py', 'tools/data/gmaps/new-venues-2026-11-13-list.json', 'tools/data/gmaps/no-interviews.json'], check=True)
