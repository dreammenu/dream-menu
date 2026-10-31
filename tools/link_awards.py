#!/usr/bin/env python3
"""Links guest venues to award places already in awards.js, where the automatic match missed them
(different spelling, e.g. "Andrew Fairlies" for Restaurant Andrew Fairlie).

Run from the repository root:
  python3 tools/link_awards.py tools/data/award-links-2026-10-31.json

Writes the award record into dm-data.js (DM.aw[venue]) in the same form as the existing links,
adds the venue id to the place's guest-venue list in awards.js and updates meta.dm_matched.
Safe to rerun: links that already exist are skipped.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def read(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    obj, end = json.JSONDecoder().raw_decode(s[m.end():])
    return s[:m.start()], obj, s[m.end() + end:]


def write(fn, var, head, obj, tail):
    open(fn, 'w', encoding='utf-8').write(head + f'window.{var}=' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + tail)


def main(fn):
    links = json.load(open(fn, encoding='utf-8'))['links']
    ha, A, ta = read('awards.js', 'DM_AWARDS')
    hd, D, td = read('dm-data.js', 'DM')
    P = {p[0]: p for p in A['places']}
    V = {v['i'] for v in D['venues']}
    order = A['meta']['order']
    added = 0
    for L in links:
        vid, pid = L['venue'], L['place']
        if vid not in V or pid not in P:
            raise SystemExit(f'unknown id: {vid} or {pid}')
        if vid in D['aw']:
            continue
        p = P[pid]
        recs = sorted(p[10], key=lambda a: (order.index(a[0]), -a[1]))
        labels = [(f'#{a[2]} ' if len(a) > 2 else '') + A['legend'][a[0]][0] + f' {a[1]}' for a in recs]
        D['aw'][vid] = {'id': pid, 'g': A['groups'][recs[0][0]], 'a': labels}
        if vid not in p[-1]:
            p[-1].append(vid)
        added += 1
    A['meta']['dm_matched'] = len(D['aw'])
    write('awards.js', 'DM_AWARDS', ha, A, ta)
    write('dm-data.js', 'DM', hd, D, td)
    print('linked', added, 'guest venues with awards', len(D['aw']))


if __name__ == '__main__':
    main(sys.argv[1])
