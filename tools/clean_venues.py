"""Merge duplicate venues and tidy display names (rules in tools/data/venue-cleanup.json).

Run from the repository root, before the page builds:
  python3 tools/clean_venues.py

What it changes:
  dm-data.js       duplicates folded into the kept venue (mentions, guests, courses, dish groups, dishes, quotes,
                   best location, awards); renamed venues; market counts and top-10 lists; headline totals
  dm-cat.js        refined dish counts per venue, re-keyed because the venue list is indexed by position
  partner/data/venues-base.csv   rows for kept and renamed venues rewritten, duplicate rows dropped
  awards.js, tools/data/other-awards-links.json, tools/data/award-links-*.json, tools/data/gmaps/placements.py,
  tools/data/home-quotes.json    duplicate ids pointed at the kept venue
  vercel.json      a permanent redirect from each duplicate's old venue page to the kept venue's page

Guests: a guest who named both spellings is counted once in neither file, so the merged guest count is the sum,
capped at the merged mention count. Safe to rerun: pairs whose duplicate is gone are skipped.
"""
import csv
import glob
import io
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import add_venues as av  # noqa: E402  (load, save, member, COURSE_COL)

RULES = json.load(open('tools/data/venue-cleanup.json', encoding='utf-8'))
PREC = {'exact': 0, 'street': 1, 'neighbourhood': 2, 'city': 3, '': 4}
TRUST = {'L': 0, 'A': 1, 'U': 2}


def slug(vid):
    return re.sub(r'-x$', '', vid)


def main():
    dparts = av.load('dm-data.js', 'DM')
    cparts = av.load('dm-cat.js', 'DMC')
    D, C = dparts[1], cparts[1]
    V = D['venues']
    byid = {v['i']: v for v in V}
    old_idx = {v['i']: i for i, v in enumerate(V)}
    merged = []

    for keep, dup in RULES['merge']:
        if dup not in byid or keep not in byid:
            continue
        k, d = byid[keep], byid[dup]
        k['m'] = k.get('m', 0) + d.get('m', 0)
        k['g'] = min(k.get('g', 0) + d.get('g', 0), k['m']) if k['m'] else 0
        cs = Counter(k.get('cs', {})); cs.update(d.get('cs', {}))
        if cs:
            k['cs'] = dict(cs)
        kk = Counter(dict((a, b) for a, b in k.get('k', []))); kk.update(dict((a, b) for a, b in d.get('k', [])))
        if kk:
            k['k'] = [[a, b] for a, b in sorted(kk.items(), key=lambda x: -x[1])[:3]]
        dishes = list(k.get('d') or [])
        for x in d.get('d') or []:
            if x.lower() not in {y.lower() for y in dishes} and len(dishes) < 5:
                dishes.append(x)
        if dishes:
            k['d'] = dishes
        if d.get('q'):
            k['q'] = (k.get('q') or []) + [q for q in d['q'] if q not in (k.get('q') or [])]
        # keep the better location
        better = (TRUST.get(d.get('t'), 3), PREC.get(d.get('p', ''), 4)) < (TRUST.get(k.get('t'), 3), PREC.get(k.get('p', ''), 4))
        if better:
            for f in ('t', 'p', 'la', 'lo'):
                if f in d:
                    k[f] = d[f]
                elif f in k:
                    del k[f]
        if not k.get('ad') and d.get('ad'):
            k['ad'] = d['ad']
        for f in ('tw', 'na', 'co', 'cc', 'r'):
            if not k.get(f) and d.get(f):
                k[f] = d[f]
        aw = D.get('aw', {})
        if dup in aw and keep not in aw:
            aw[keep] = aw.pop(dup)
        else:
            aw.pop(dup, None)
        # refined dish counts (dm-cat.js is keyed by list position)
        a = Counter(dict((x, y) for x, y in C['v'].get(str(old_idx[keep]), [])))
        a.update(dict((x, y) for x, y in C['v'].get(str(old_idx[dup]), [])))
        if a:
            C['v'][str(old_idx[keep])] = [[x, y] for x, y in sorted(a.items(), key=lambda t: -t[1])]
        merged.append((keep, dup))

    gone = {dup for _, dup in merged}
    for vid, name in RULES['rename'].items():
        if vid in byid and vid not in gone:
            byid[vid]['n'] = name

    if merged:
        newV = [v for v in V if v['i'] not in gone]
        C['v'] = {str(i): C['v'][str(old_idx[v['i']])] for i, v in enumerate(newV) if str(old_idx[v['i']]) in C['v']}
        D['venues'] = V = newV
        C['n'] = len(V)

    # markets: venue counts, pins, mentions, courses and top 10 (dish shares are unchanged: no mention was added or lost)
    for mk in D['markets']:
        vs = [v for v in V if av.member(mk, v)]
        mk['v'] = len(vs)
        mk['pn'] = sum(1 for v in vs if 'la' in v)
        mk['mn'] = sum(v['m'] for v in vs)
        cs = Counter()
        for v in vs:
            cs.update(v.get('cs', {}))
        mk['cs'] = dict(cs)
        prior = {vid: i for i, vid in enumerate(mk.get('top', []))}
        mk['top'] = [v['i'] for v in sorted((v for v in vs if v['m'] > 0),
                                            key=lambda v: (-v['m'], -v.get('g', 0), prior.get(v['i'], 10 ** 6)))[:10]]
    meta = D['meta']
    named = [v for v in V if v['m'] > 0]
    meta.update(on_map=len(V), on_map_pinned=sum(1 for v in V if 'la' in v), listed=len(V) - len(named),
                venues=len(named), pinned=sum(1 for v in named if 'la' in v),
                located=sum(1 for v in V if v['t'] == 'L'), approximate=sum(1 for v in V if v['t'] == 'A'),
                unpinned=sum(1 for v in V if v['t'] == 'U'), mentions=sum(v['m'] for v in V),
                countries=len({v['co'] for v in named if v['co']}),
                cities=sum(1 for mk in D['markets'] if mk['k'] == 'city' and mk['mn'] > 0))
    av.save('dm-data.js', 'DM', dparts, D)
    av.save('dm-cat.js', 'DMC', cparts, C)

    # partner venue extract
    fn = 'partner/data/venues-base.csv'
    rows = list(csv.DictReader(io.StringIO(open(fn, encoding='utf-8-sig').read())))
    cols = list(rows[0].keys())
    byid = {v['i']: v for v in V}
    touched = {k for k, _ in merged} | set(RULES['rename'])
    status = {'L': 'address confirmed', 'A': 'approximate', 'U': 'not yet pinned'}
    out_rows = []
    for r in rows:
        vid = r['venue_id']
        if vid in gone:
            continue
        if vid in touched and vid in byid:
            v = byid[vid]
            r.update(venue=v['n'], latitude=v.get('la', ''), longitude=v.get('lo', ''), location_status=status[v['t']],
                     location_precision=v.get('p', ''), mentions=v['m'], guests_naming=v.get('g', 0),
                     top_dish_categories='; '.join(f'{a} ({b})' for a, b in v.get('k', [])),
                     dishes_named='; '.join((v.get('d') or [])[:4]) or r.get('dishes_named', ''), address=v.get('ad', ''))
            for c, col in av.COURSE_COL.items():
                r[col] = v.get('cs', {}).get(c, 0)
        out_rows.append(r)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=cols, lineterminator='\r\n')
    w.writeheader(); w.writerows(out_rows)
    open(fn, 'w', encoding='utf-8-sig').write(out.getvalue())

    # other files that name venue ids
    files = ['awards.js', 'tools/data/other-awards-links.json', 'tools/data/gmaps/placements.py', 'tools/data/home-quotes.json'] \
        + glob.glob('tools/data/award-links-*.json')
    for f in files:
        if not os.path.exists(f):
            continue
        s = s0 = open(f, encoding='utf-8').read()
        for keep, dup in merged:
            s = re.sub(r'(?<![\w-])' + re.escape(dup) + r'(?![\w-])', keep, s)
            s = s.replace(f'"{keep}","{keep}"', f'"{keep}"')
        if s != s0:
            open(f, 'w', encoding='utf-8').write(s)

    # redirects from old venue pages
    vj = json.load(open('vercel.json', encoding='utf-8'))
    have = {r['source'] for r in vj.get('redirects', [])}
    for keep, dup in merged:
        src = f'/venue/{slug(dup)}'
        if src not in have:
            vj.setdefault('redirects', []).append({'source': src, 'destination': f'/venue/{slug(keep)}', 'permanent': True})
    open('vercel.json', 'w', encoding='utf-8').write(json.dumps(vj, indent=2, ensure_ascii=False) + '\n')

    print(f'merged {len(merged)} duplicate venues; venues named {meta["venues"]}, on the map {meta["on_map"]}, '
          f'mentions {meta["mentions"]}')
    for k, d in merged:
        print(f'  {byid[k]["n"]}  <-  {d}  (now {byid[k]["m"]} mentions)')


if __name__ == '__main__':
    main()
