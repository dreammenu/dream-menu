#!/usr/bin/env python3
"""Venue status from the Food Standards Scotland hygiene register (FHIS), for partners.

Downloads the FSA open data file for every Scottish council (Open Government Licence v3.0, no key), matches each
Scottish venue guests have named to its register entry by postcode, distance and name, and records:
  status   listed (on the register), new (registered, awaiting first inspection),
           check (full address known but not found on the register: may have closed or renamed)
  rating   Pass, Pass and Eat Safe, Improvement Required, Awaiting Inspection, Exempt, with the date
  type     the register's business type (restaurant/cafe, pub/bar, takeaway, hotel ...)
It also lists new leads: restaurants, cafés and bars in Glasgow and Edinburgh registered in the last 12 months and
not yet inspected, so not yet on any guide or in Dream Menu.

Writes tools/data/venue-status.json (read by build_accounts.py; nothing from it is public).
If the download fails (no network), the existing file is kept and the build carries on.
Matching is conservative: a venue with no confident match is left without a status rather than guessed.

Run before build_accounts.py (build_venue_pages.py calls both):  python3 tools/build_status.py
"""
import datetime as dt, difflib, glob, json, math, os, re, subprocess, sys, unicodedata
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
OUT = 'tools/data/venue-status.json'
CACHE = os.environ.get('DM_FHIS_CACHE', '/tmp/dm-fhis')
API = 'https://api.ratings.food.gov.uk/Authorities'
FOOD = {'Restaurant/Cafe/Canteen', 'Pub/bar/nightclub', 'Takeaway/sandwich shop', 'Hotel/bed & breakfast/guest house',
        'Other catering premises', 'Mobile caterer', 'Retailers - other', 'Manufacturers/packers'}
LEAD_TYPES = {'Restaurant/Cafe/Canteen', 'Pub/bar/nightclub'}
SERVE = LEAD_TYPES | {'Takeaway/sandwich shop', 'Hotel/bed & breakfast/guest house', 'Other catering premises', 'Mobile caterer'}
LEAD_LA = {'Glasgow City': 'Glasgow', 'Edinburgh (City of)': 'Edinburgh'}
TODAY = dt.date.today()
NOT_LEAD = re.compile(r'school|nursery|after ?school|childcare|care home|\bcare\b|hospital|universit|college|church|academy|council|hospice|playgroup|out of school|childmind|creche|crèche|breakfast club', re.I)


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


def fetch():
    """Download the Scottish council files into CACHE. Returns the list of XML paths, or [] if offline."""
    os.makedirs(CACHE, exist_ok=True)
    aj = os.path.join(CACHE, 'authorities.json')
    r = subprocess.run(['curl', '-sfL', '-m', '60', '-H', 'x-api-version: 2', '-H', 'Accept: application/json', '-o', aj, API])
    if r.returncode:
        return []
    files = []
    for a in json.load(open(aj))['authorities']:
        if a.get('RegionName') != 'Scotland':
            continue
        fn = os.path.join(CACHE, f"la{a['LocalAuthorityId']}.xml")
        if subprocess.run(['curl', '-sfL', '-m', '300', '-o', fn, a['FileName']]).returncode == 0:
            files.append(fn)
    return files


def parse(files):
    rows, extract = [], ''
    for f in files:
        root = ET.parse(f).getroot()
        extract = max(extract, root.findtext('Header/ExtractDate') or '')
        for e in root.iter('EstablishmentDetail'):
            t = e.findtext('BusinessType') or ''
            if t not in FOOD:
                continue
            la, lo = e.findtext('Geocode/Latitude'), e.findtext('Geocode/Longitude')
            rows.append(dict(id=e.findtext('FHRSID'), n=re.sub(r'(?<=[a-z])Ú', 'é', e.findtext('BusinessName') or ''), t=t, r=e.findtext('RatingValue') or '',
                             d=e.findtext('RatingDate') or '', pc=(e.findtext('PostCode') or '').upper().replace(' ', ''),
                             a=', '.join(x for x in (e.findtext(f'AddressLine{i}') for i in (1, 2, 3, 4)) if x),
                             la=e.findtext('LocalAuthorityName') or '',
                             lat=float(la) if la else None, lon=float(lo) if lo else None))
    return rows, extract


STOP = {'the', 'ltd', 'limited', 'and', 'co', 'uk', 'llp', 'plc', 't/a', 'ta', 'glasgow', 'edinburgh', 'scotland', 'at', 'st', 'street', 'road', 'lane', 'cic'}
COMMON = {'curry', 'pizza', 'pizzeria', 'sushi', 'burger', 'chicken', 'pakora', 'kebab', 'thai', 'indian', 'italian', 'chinese', 'tandoori', 'noodle',
          'white', 'black', 'golden', 'little', 'royal', 'grand', 'city', 'central', 'station', 'garden', 'corner', 'village', 'harbour', 'market'}
GENERIC = {'restaurant', 'bar', 'cafe', 'kitchen', 'bistro', 'grill', 'pub', 'hotel', 'house', 'eatery', 'coffee', 'shop', 'deli', 'bakery', 'diner'}


import functools


@functools.lru_cache(maxsize=None)
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('&', ' and ').replace("'", '')
    return tuple(dict.fromkeys(w for w in re.split(r'[^a-z0-9]+', s) if w and w not in STOP))


def _close(x, y):
    if x == y:
        return True
    if min(len(x), len(y)) >= 4 and (x.startswith(y) or y.startswith(x)) and abs(len(x) - len(y)) <= 2:
        return True     # chip / chips, hajar / hajars
    return min(len(x), len(y)) >= 5 and difflib.SequenceMatcher(None, x, y).ratio() >= 0.88


@functools.lru_cache(maxsize=None)
def sim(a, b):
    """1.0 when every distinctive word of both names matches; 0.9 to 1.0 when one name's words are all in the other
    and at least half the other's are matched (Delhi Darbar / Namaste by Delhi Darbar); otherwise 0.
    Word-level, so short look-alikes (Bolt Burger / Bob the Burger, Thunder / Thunderdog) do not match."""
    ta, tb = norm(a), norm(b)
    ca, cb = [w for w in ta if w not in GENERIC] or list(ta), [w for w in tb if w not in GENERIC] or list(tb)
    if not ca or not cb:
        return 0.0
    cov = lambda xs, ys: sum(1 for x in xs if any(_close(x, y) for y in ys)) / len(xs)
    ab, ba = cov(ca, cb), cov(cb, ca)
    if ab == 1 and ba == 1:
        return 1.0
    for full, other, part in ((ca, cb, ba), (cb, ca, ab)):
        if part < 0.5 or min(cov(full, other), 1) < 1:
            continue
        if len(full) >= 2:
            return round(0.9 + 0.1 * part, 3)
        # a one-word name (Crabshakk, Colpi) must be the first word of the other, spelt the same, and not a common word
        if full[0] == other[0] and full[0] not in COMMON and (len(full[0]) >= 5 or (len(full[0]) >= 3 and len(other) <= 2)):
            return 0.9
    return 0.0


def dist(a, b):
    if None in (a[0], a[1], b[0], b[1]):
        return 9e9
    k = math.cos(math.radians(a[0]))
    return 111320 * math.hypot(a[0] - b[0], (a[1] - b[1]) * k)


PC = re.compile(r'\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b')


def match(v, by_pc, rows_grid):
    m = PC.search((v.get('ad') or '').upper())
    pc = (m.group(1) + m.group(2)) if m else ''
    here = (v.get('la'), v.get('lo'))
    exact = v.get('p') in ('exact', 'street')
    cands = []
    for r in by_pc.get(pc, []):
        cands.append((sim(v['n'], r['n']), 0, r, 'postcode'))
    if exact:
        gx, gy = round(here[0] * 100), round(here[1] * 60)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for r in rows_grid.get((gx + dx, gy + dy), []):
                    d = dist(here, (r['lat'], r['lon']))
                    if d <= 1500:
                        sc = sim(v['n'], r['n'])
                        if sc >= 0.9:
                            cands.append((sc, d, r, 'near'))
    cands = [c for c in cands if c[0] >= 1.0 or c[2]['t'] in SERVE]
    ok = [c for c in cands if (c[3] == 'postcode' and c[0] >= 0.9) or (c[1] <= 150 and c[0] >= 0.9) or (c[1] <= 1500 and c[0] >= 1.0)]
    if not ok:
        # a shared registration: every word of the venue's name appears, spelt the same, in one entry at its postcode (Margo and Sebb's)
        mine = [w for w in norm(v['n']) if w not in GENERIC]
        for r in by_pc.get(pc, []):
            if mine and r['t'] in SERVE and all(w in norm(r['n']) for w in mine):
                return (0.9, 0, r, 'shared'), pc
        return None, pc
    # food-service types first, then the best name, then the nearest; a live rating beats an awaiting one
    ok.sort(key=lambda c: (-round(c[0], 2), c[2]['t'] not in LEAD_TYPES, c[1], c[2]['r'] == 'Awaiting Inspection'))
    return ok[0], pc


GLA_URL = 'https://hub.arcgis.com/api/download/v1/items/0b5b75d511f7400483d7275881897215/geojson?redirect=true&layers=0'


def glasgow():
    """Glasgow City Council licensed premises (open data): on-sales licences with capacity and grant date."""
    fn = os.path.join(CACHE, 'glasgow-licensed.geojson')
    if not os.environ.get('DM_FHIS_OFFLINE') and subprocess.run(['curl', '-sfL', '-m', '300', '-o', fn, GLA_URL]).returncode:
        return []
    try:
        feats = json.load(open(fn))['features']
    except Exception:
        return []
    out = []
    for f in feats:
        p, g = f['properties'], (f.get('geometry') or {}).get('coordinates') or [None, None]
        if 'On' not in (p.get('ALCOHOL_SALES') or ''):
            continue
        ref = re.sub(r'\s+', ' ', p.get('PREMISES_REF') or '').strip()
        m = re.search(r'\b\d', ref)
        name = ref[:m.start()].strip(' ,') if m else ''
        pc = PC.search((p.get('ADDRESS') or ref).upper())
        out.append(dict(no=p.get('LICENCE_NO'), n=name, a=(p.get('ADDRESS') or '').strip(), pc=(pc.group(1) + pc.group(2)) if pc else '',
                        cap=p.get('CAPACITY_ON'), g=(p.get('GRANTDATE') or '')[:10],
                        h=__import__('hashlib').sha1((p.get('LICENCE_HOLDER') or '').strip().lower().encode()).hexdigest()[:10],
                        lat=g[1], lon=g[0]))
    return out


def match_lic(v, lics):
    m = PC.search((v.get('ad') or '').upper())
    pc = (m.group(1) + m.group(2)) if m else ''
    best = None
    for L in lics:
        if not L['n']:
            continue
        same = pc and L['pc'] == pc
        d = dist((v.get('la'), v.get('lo')), (L['lat'], L['lon']))
        if not same and d > 150:
            continue
        sc = sim(v['n'], L['n'])
        if sc >= 0.9:
            if not best or (sc, -d) > (best[0], -best[1]):
                best = (sc, d, L)
    return best


def main():
    files = fetch() if not os.environ.get('DM_FHIS_OFFLINE') else sorted(glob.glob(os.path.join(CACHE, 'la*.xml')))
    if not files:
        print('build_status: FSA register not reachable; keeping', OUT if os.path.exists(OUT) else 'no status file')
        return
    rows, extract = parse(files)
    by_pc, grid = {}, {}
    for r in rows:
        by_pc.setdefault(r['pc'], []).append(r)
        if r['lat'] is not None:
            grid.setdefault((round(r['lat'] * 100), round(r['lon'] * 60)), []).append(r)
    D = load('dm-data.js', 'DM')
    out, n_ex, n_check = {}, 0, 0
    for v in D['venues']:
        if v.get('na') != 'Scotland' or v.get('y') == 'area':
            continue
        best, pc = match(v, by_pc, grid)
        exact = v.get('p') in ('exact', 'street') and bool(pc)
        n_ex += exact
        if best:
            r = best[2]
            out[v['i']] = dict(s='new' if r['r'] == 'Awaiting Inspection' and r['d'] >= (TODAY - dt.timedelta(days=365)).isoformat() else 'listed', r=r['r'], d=r['d'], t=r['t'], f=r['id'],
                               q=best[3], c=round(best[0], 2), rn=r['n'])
        elif exact:
            out[v['i']] = dict(s='check')
            n_check += 1
    # Glasgow licences: capacity, grant date, and a change of licence holder since the last run
    lics = glasgow()
    prev = json.load(open(OUT, encoding='utf-8')).get('v', {}) if os.path.exists(OUT) else {}
    lic_used = set()
    if lics:
        for v in D['venues']:
            if v.get('c') != 'Glasgow' or v.get('p') not in ('exact', 'street') or v.get('y') == 'area':
                continue
            b = match_lic(v, lics)
            if not b:
                continue
            L = b[2]
            lic_used.add(L['no'])
            o = out.setdefault(v['i'], dict(s='listed'))
            if o['s'] == 'check':
                o['s'] = 'listed'
            was = (prev.get(v['i']) or {}).get('lic') or {}
            ch = was.get('ch', '')
            if was.get('no') == L['no'] and was.get('h') and was['h'] != L['h']:
                ch = TODAY.isoformat()
            o['lic'] = dict(no=L['no'], cap=L['cap'], g=L['g'], h=L['h'], **({'ch': ch} if ch else {}))
            if L['g'] >= (TODAY - dt.timedelta(days=365)).isoformat() and o['s'] == 'listed':
                o['s'] = 'new'
    n_check = sum(1 for o in out.values() if o['s'] == 'check')
    # new leads: registered in the last 12 months, awaiting first inspection, restaurants and bars in the two cities
    cut = (TODAY - dt.timedelta(days=365)).isoformat()
    named = {o['f'] for o in out.values() if o.get('f')}
    leads = sorted([dict(n=r['n'], t='Restaurant or café' if r['t'].startswith('Restaurant') else 'Pub or bar', a=r['a'],
                         pc=PC.sub(lambda m: m.group(1) + ' ' + m.group(2), r['pc']), mk=LEAD_LA[r['la']], d=r['d'], f=r['id'], dm=r['id'] in named)
                    for r in rows if r['la'] in LEAD_LA and r['t'] in LEAD_TYPES and r['r'] == 'Awaiting Inspection' and r['d'] >= cut
                    and not re.search(r'\bflat\b|\d+/\d+', r['a'], re.I) and not NOT_LEAD.search(r['n']) and r['id'] not in named],
                   key=lambda x: x['d'], reverse=True)
    # plus Glasgow on-sales licences granted in the last 12 months that no guest has named yet
    for L in lics:
        if L['no'] in lic_used or not L['n'] or L['g'] < cut:
            continue
        dup = next((x for x in leads if x['mk'] == 'Glasgow' and x['pc'].replace(' ', '') == L['pc'] and sim(x['n'], L['n']) >= 0.9), None)
        if dup:
            dup.update(cap=L['cap'], lic=L['g'])
        else:
            leads.append(dict(n=L['n'], t='Licensed premises', a=L['a'], pc=PC.sub(lambda m: m.group(1) + ' ' + m.group(2), L['pc']), mk='Glasgow',
                              d=L['g'], cap=L['cap'], lic=L['g'], dm=False))
    leads.sort(key=lambda x: x['d'], reverse=True)
    # how the named venues compare with every restaurant and bar on the register in the same councils
    las = {r['la'] for r in rows if r['id'] in named}
    pool = [r for r in rows if r['la'] in las and r['t'] in LEAD_TYPES and r['r'] in ('Pass', 'Pass and Eat Safe', 'Improvement Required')]
    mine = [r for r in rows if r['id'] in named and r['r'] in ('Pass', 'Pass and Eat Safe', 'Improvement Required')]
    ir = lambda xs: round(100 * sum(1 for r in xs if r['r'] == 'Improvement Required') / (len(xs) or 1), 1)
    res = dict(extract=extract, built=TODAY.isoformat(), source='Food Standards Agency, Food Hygiene Information Scheme open data (Open Government Licence v3.0)',
               n_scot=sum(1 for v in D['venues'] if v.get('na') == 'Scotland' and v.get('y') != 'area'), n_exact=n_ex,
               n_listed=sum(1 for o in out.values() if o['s'] == 'listed'), n_new=sum(1 for o in out.values() if o['s'] == 'new'), n_check=n_check,
               ir_named=ir(mine), ir_all=ir(pool), lic=dict(n=len(lics), matched=len(lic_used), latest=max((L['g'] for L in lics), default='')), n_rated=len(mine), n_pool=len(pool), v=out, leads=leads)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f"venue-status.json: register {extract}, {len(rows):,} food premises | named venues listed {res['n_listed']}, new {res['n_new']}, "
          f"check {n_check} of {n_ex} with a full address | improvement required {res['ir_named']}% named vs {res['ir_all']}% all | Glasgow licences {len(lics)}, matched {len(lic_used)} | leads {len(leads)}")


if __name__ == '__main__':
    main()
