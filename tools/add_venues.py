#!/usr/bin/env python3
"""Adds venue mentions from newly coded interviews to the venue map data.

Run from the repository root:
  python3 tools/add_venues.py tools/data/new-venues-2026-10-28.json tools/data/new-interviews-2026-10-28.json [ukpostcodes.csv]

The JSON lists new venues (with an address, or the place the guest named) and every venue
mention from the new interviews (venue id, course, dish named, refined dish category, a short
quote). The script updates, in place:
  dm-data.js       venues (counts, course split, quotes, dishes, coarse categories), every market
                   that contains a touched venue (venues, pins, mentions, guests, course split,
                   leading categories, top venues) and the headline totals in meta
  dm-cat.js        refined dish counts per venue and per market
  partner/map-trends.js                    venue mentions per market per quarter
  partner/data/venues-base.csv             the venue extract (touched rows rewritten, new rows added)
  partner/data/market_activity_by_quarter.csv

Exact addresses are located by UK postcode centroid (dwyl UK postcode file, optional third
argument). Places without an address are pinned in the city, town, street or area the guest
named, with a small fixed offset so pins in one place fan out (same offset on every run).
"""
import csv, hashlib, io, json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

COURSE_COL = dict(s='mentions_starter', m='mentions_main', d='mentions_side', p='mentions_dessert',
                  k='mentions_soft_drink', a='mentions_alcoholic_drink', h='mentions_hidden_gem_or_next_stop')

# refined dish category -> the coarse venue-level category used in dm-data.js
COARSE = {
    'Burger (other)': 'Burger', 'Loaded / dirty fries': 'Chips / fries', 'Fried potatoes / chips': 'Chips / fries',
    'Ice cream (other)': 'Ice cream / gelato', 'Gelato': 'Ice cream / gelato',
    'Oysters': 'Seafood', 'Crab': 'Seafood', 'Scallops': 'Seafood', 'Cod / hake / white fish': 'Seafood',
    'Fish (other)': 'Seafood', 'Calamari / squid': 'Seafood', 'Mussels / clams': 'Seafood',
    'Carbonara': 'Pasta', 'Pasta starter (cacio e pepe, small pasta)': 'Pasta',
    'Fried chicken': 'Fried chicken / wings / tenders', 'Roast chicken': 'Chicken',
    'Hummus / dips / falafel': 'Dips (hummus, taramasalata, tahini)', 'Tacos': 'Tacos / Mexican',
    'Tenderstem / broccoli': 'Vegetable sides (greens, broccoli, cabbage)', 'Brownie': 'Brownie',
    'Fried Italian bites (suppli, fritti)': 'Fried Italian bites', 'Donburi / teriyaki / Japanese': 'Sushi / Japanese',
    'Korean (bibimbap, bulgogi, KFC)': 'Asian', 'Crispy / smashed potatoes': 'Potatoes (non-fries)',
    'Mash / pomme puree': 'Potatoes (non-fries)', 'Ribeye steak': 'Steak / beef', 'Steak pie / pies': 'Pie',
    'Sticky toffee pudding': 'Sticky toffee pudding', 'Croissants / pastries / cinnamon buns': 'Café / Bakery / Dessert',
    'Tiramisu': 'Tiramisu', 'Laksa': 'Asian noodles / hotpot', 'Chaat / Indian street food': 'Pakora / Indian starters',
    'Scotch egg': 'Pork', 'Chicken tikka masala': 'Curry / Indian', 'Croquettes / croquetas': 'Arancini / croquette',
    'Lemon cake / drizzle': 'Cake (general)', 'Custard tart / pastel de nata': 'Tart (any)',
    'Steak tartare / carpaccio': 'Tartare / carpaccio', 'Dumplings / gyoza / dim sum': 'Asian small plates (rolls, dumplings, dim sum)',
    'Cheese board': 'Cheese (as dessert)', 'Margarita (classic / frozen)': 'Margarita', 'Spicy margarita': 'Margarita',
    'Negroni': 'Negroni', 'Red wine': 'White/Red/Rose wine', 'Cocktail (other / named house cocktail)': 'Cocktail (general)',
    'Whisky / dram': 'Whisky / dram', 'Dirty / classic martini': 'Martini (non-espresso)',
    'Mocktail / alcohol-free': 'Mocktail (non-alcoholic specialty)', 'Guinness / stout': 'Guinness',
    'Black pudding': 'British / Scottish / Pub', 'Haggis bon bons / haggis': 'Haggis bon bons',
    'Mushrooms': 'Vegetable sides (greens, broccoli, cabbage)', 'Ramen': 'Asian noodles / hotpot',
    'Bao buns': 'Bread-based sides (naan, focaccia, bao, sourdough)', 'Basque cheesecake': 'Cheesecake',
    'Mozzarella sticks / fried cheese': 'Cheese-based sides (mozzarella, halloumi, burrata)',
    'Tapas / small plates': 'Small plates / sharing', 'Risotto': 'Pasta', 'Rendang / Malaysian curry': 'Curry / Indian',
    'Traybakes / slices / Scottish bakes': 'Café / Bakery / Dessert', 'Jelly / custard / childhood puddings': 'Café / Bakery / Dessert',
    'Gin and tonic': 'Gin & tonic', 'IPA / craft beer': 'Beer / lager / ale',
}
CC = {'United Kingdom': 'GB', 'Ireland': 'IE', 'Netherlands': 'NL', 'Mexico': 'MX', 'Italy': 'IT', 'Australia': 'AU',
      'United States': 'US', 'France': 'FR', 'Spain': 'ES', 'Greece': 'GR', 'Barbados': 'BB', 'New Zealand': 'NZ',
      'Czech Republic': 'CZ', 'Iceland': 'IS', 'Denmark': 'DK', 'Jamaica': 'JM', 'Thailand': 'TH', 'Japan': 'JP',
      'India': 'IN', 'Portugal': 'PT', 'Singapore': 'SG', 'Germany': 'DE'}


def load(fn, var):
    s = open(fn, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    obj, end = json.JSONDecoder().raw_decode(s[m.end():])
    return s[:m.start()], obj, s[m.end() + end:]


def save(fn, var, parts, obj):
    head, _, tail = parts
    open(fn, 'w', encoding='utf-8').write(head + 'window.' + var + '=' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + tail)


def quarter(d):
    return f'{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}'


def offset(vid, prec):
    """Fixed fan-out for guessed pins: up to ~1 km for city pins, less for streets and areas."""
    if prec == 'exact':
        return 0.0, 0.0
    h = hashlib.md5(vid.encode()).digest()
    reach = {'street': 0.0012, 'neighbourhood': 0.003}.get(prec, 0.008)
    return (h[0] / 255 - .5) * 2 * reach, (h[1] / 255 - .5) * 2 * reach * 1.7


def member(mk, v):
    k = mk['k']
    return (k == 'world' or (k == 'region' and v['r'] and v['r'] == mk['r'])
            or (k == 'country' and v['co'] and v['co'] == mk['co'])
            or (k == 'nation' and v['na'] and v['na'] == mk['na'] and v['co'] == mk['co'])
            or (k == 'city' and v['c'] and v['c'] == mk['n'] and v['co'] == mk['co']))


def main(vfn, ifn, pcfn=None):
    spec = json.load(open(vfn, encoding='utf-8'))
    irows = json.load(open(ifn, encoding='utf-8'))['rows']
    dates = {r['row']: r['date'] for r in irows}
    already = sum(1 for r in irows if r.get('counted'))   # in the interview totals already, only new to the map
    dparts = load('dm-data.js', 'DM'); D = dparts[1]
    cparts = load('dm-cat.js', 'DMC'); C = cparts[1]
    tparts = load('partner/map-trends.js', 'DM_TRENDS'); T = tparts[1]
    V = D['venues']
    byid = {v['i']: v for v in V}
    vidx = {v['i']: i for i, v in enumerate(V)}
    region_of = {}
    for v in V:
        if v['co'] and v['r']:
            region_of.setdefault(v['co'], v['r'])
    region_of.setdefault('Netherlands', 'Europe')
    for _co, _r in (('Czech Republic', 'Europe'), ('Iceland', 'Europe'), ('Jamaica', 'North America')):
        region_of.setdefault(_co, _r)

    # postcodes for exact addresses
    pcs = {}
    if pcfn:
        want = {re.search(r'([A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2})$', n['ad']).group(1)
                for n in spec['new_venues'] if n['p'] == 'exact' and n['co'] == 'United Kingdom'}
        for row in csv.reader(open(pcfn, encoding='utf-8')):
            if row[1] in want:
                pcs[row[1]] = (float(row[2]), float(row[3]))

    added = []
    for n in spec['new_venues']:
        if n['i'] in byid:
            continue
        la, lo = n['la'], n['lo']
        if la is None:
            pc = re.search(r'([A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2})$', n['ad']).group(1)
            la, lo = pcs[pc]
        dla, dlo = offset(n['i'], n['p'])
        v = dict(i=n['i'], n=n['n'], t='L' if n['p'] == 'exact' else 'A', p=n['p'], c=n['c'], cc=CC.get(n['co'], ''),
                 co=n['co'], r=region_of.get(n['co'], ''), na=n['na'], tw=n['tw'], m=0, g=0,
                 la=round(la + dla, 6), lo=round(lo + dlo, 6), cs={})
        if n['ad']:
            v['ad'] = n['ad']
        if n['no']:
            v['no'] = n['no']
        V.append(v); byid[v['i']] = v; vidx[v['i']] = len(V) - 1
        added.append(v['i'])

    for vid, fix in spec.get('fix_venues', {}).items():
        v = byid[vid]
        for key, val in fix.items():
            if key == 'drop_k':
                v.pop('k', None)
            else:
                v[key] = val
        v['t'] = 'L' if v['p'] == 'exact' else 'A'
        v.pop('u', None); v.pop('s', None)
        if 'cc' not in v or not v['cc']:
            v['cc'] = CC.get(v['co'], '')
        if not v.get('r'):
            v['r'] = region_of.get(v['co'], '')

    # apply mentions
    cat_list = C['c']
    touched, guests = set(added), defaultdict(set)   # new venues count as touched so their markets exist and are counted
    market_new = defaultdict(lambda: dict(coarse=Counter(), fine=Counter(), guests=set(), q=Counter()))
    for mt in spec['mentions']:
        v = byid[mt['v']]
        touched.add(v['i'])
        v['m'] += 1
        cs = v.setdefault('cs', {})
        cs[mt['course']] = cs.get(mt['course'], 0) + 1
        if mt['row'] not in guests[v['i']]:
            guests[v['i']].add(mt['row'])
            v['g'] += 1
        if mt['q']:
            q = v.setdefault('q', [])
            if len(q) < 2:
                txt = mt['q'] if len(mt['q']) <= 150 else mt['q'][:149].rsplit(' ', 1)[0] + '…'
                q.append([mt['course'], txt])
        if mt['dish']:
            d = v.setdefault('d', [])
            if mt['dish'] not in d and len(d) < 5:
                d.append(mt['dish'])
        coarse = COARSE.get(mt['cat']) if mt['cat'] else None
        if coarse:
            kk = Counter(dict((a, b) for a, b in v.get('k', [])))
            kk[coarse] += 1
            v['k'] = [[a, b] for a, b in sorted(kk.items(), key=lambda x: -x[1])[:3]]
        if mt['cat']:
            if mt['cat'] not in cat_list:
                cat_list.append(mt['cat'])
            ci = cat_list.index(mt['cat'])
            vv = Counter(dict((a, b) for a, b in C['v'].get(str(vidx[v['i']]), [])))
            vv[ci] += 1
            C['v'][str(vidx[v['i']])] = [[a, b] for a, b in sorted(vv.items(), key=lambda x: -x[1])]
        for mk in D['markets']:
            if member(mk, v):
                mn = market_new[mk['id']]
                mn['guests'].add(mt['row'])
                mn['q'][quarter(dates[mt['row']])] += 1
                if coarse:
                    mn['coarse'][coarse] += 1
                if mt['cat']:
                    mn['fine'][cat_list.index(mt['cat'])] += 1

    # new markets for places that have none yet
    have = {mk['id'] for mk in D['markets']}
    for v in V:
        if v['i'] not in touched:
            continue
        for k, mid, name in (('country', f"country:{v['co']}", v['co']), ('city', f"city:{v['c']}|{v['co']}", v['c'])):
            if name and mid not in have:
                mk = dict(id=mid, k=k, n=name, co=v['co'], r=v['r'], na=v['na'] if k == 'city' else '', v=0, pn=0, mn=0,
                          g=0, hg=0, so=False, to=False, cat=[], cs={}, top=[])
                last = max(i for i, x in enumerate(D['markets']) if x['k'] == k)
                D['markets'].insert(last + 1, mk); have.add(mid)
                C['m'][mid] = []
                mn = market_new[mid]
                for mt in spec['mentions']:
                    if member(mk, byid[mt['v']]):
                        mn['guests'].add(mt['row']); mn['q'][quarter(dates[mt['row']])] += 1
                        c2 = COARSE.get(mt['cat']) if mt['cat'] else None
                        if c2:
                            mn['coarse'][c2] += 1
                        if mt['cat']:
                            mn['fine'][cat_list.index(mt['cat'])] += 1

    # recompute market aggregates
    for mk in D['markets']:
        vs = [v for v in V if member(mk, v)]
        if mk['id'] not in market_new and not any(v['i'] in touched for v in vs):
            continue
        mn = market_new[mk['id']]
        mk['v'] = len(vs)
        mk['pn'] = sum(1 for v in vs if 'la' in v)
        mk['mn'] = sum(v['m'] for v in vs)
        cs = Counter()
        for v in vs:
            cs.update(v.get('cs', {}))
        mk['cs'] = dict(cs)
        mk['g'] += len(mn['guests'])
        prior = {vid: i for i, vid in enumerate(mk['top'])}
        mk['top'] = [v['i'] for v in sorted((v for v in vs if v['m'] > 0),
                                            key=lambda v: (-v['m'], -v['g'], prior.get(v['i'], 10 ** 6 + vidx[v['i']])))[:10]]
        for key, store, new in (('cat', mk, mn['coarse']), ('fine', C['m'], mn['fine'])):
            lst = store['cat'] if key == 'cat' else C['m'].setdefault(mk['id'], [])
            den = round(lst[0][1] / lst[0][2] * 100) if lst and lst[0][2] else 0
            cnt = Counter({a: b for a, b, _ in lst})
            for a, b in new.items():
                if a in cnt or not lst or len(lst) < 8:
                    cnt[a] += b
            den += sum(new.values())
            top = sorted(cnt.items(), key=lambda x: -x[1])[:8]
            out = [[a, b, round(100 * b / den, 1) if den else 0] for a, b in top]
            if key == 'cat':
                mk['cat'] = out
            else:
                C['m'][mk['id']] = out
        tr = T.setdefault(mk['id'], {})
        for q, n in mn['q'].items():
            tr[q] = tr.get(q, 0) + n

    meta = D['meta']
    batch_n = len(dates)
    meta['interviews'] += batch_n - already
    meta['interviews_mapped'] += batch_n
    if dates:
        meta['interviews_to'] = max(meta['interviews_to'], max(dates.values()))
    meta['built'] = '2026-10-28'
    meta['venues'] = len(V)
    meta['pinned'] = sum(1 for v in V if 'la' in v)
    meta['located'] = sum(1 for v in V if v['t'] == 'L')
    meta['approximate'] = sum(1 for v in V if v['t'] == 'A')
    meta['unpinned'] = sum(1 for v in V if v['t'] == 'U')
    meta['mentions'] = sum(v['m'] for v in V)
    meta['countries'] = sum(1 for mk in D['markets'] if mk['k'] == 'country')
    meta['cities'] = sum(1 for mk in D['markets'] if mk['k'] == 'city')
    # Headline totals count venues guests have named. Places on the map only because they are on
    # Dream Menu's own Google Maps list (m == 0) are counted separately as 'listed'.
    named = [v for v in V if v['m'] > 0]
    meta['on_map'] = len(V)
    meta['on_map_pinned'] = meta['pinned']
    meta['listed'] = len(V) - len(named)
    meta['venues'] = len(named)
    meta['pinned'] = sum(1 for v in named if 'la' in v)
    meta['countries'] = len({v['co'] for v in named if v['co']})
    meta['cities'] = sum(1 for mk in D['markets'] if mk['k'] == 'city' and mk['mn'] > 0)
    for mt in spec['mentions']:
        q = quarter(dates[mt['row']])
        meta['qtot'][q] = meta['qtot'].get(q, 0) + 1
    C['n'] = len(V)
    C['b'] = '2026-10-28'
    save('dm-data.js', 'DM', dparts, D)
    save('dm-cat.js', 'DMC', cparts, C)
    save('partner/map-trends.js', 'DM_TRENDS', tparts, T)

    # partner extracts
    fn = 'partner/data/venues-base.csv'
    raw = open(fn, encoding='utf-8-sig').read()
    rows = list(csv.DictReader(io.StringIO(raw)))
    cols = list(rows[0].keys())
    aw = {k: '; '.join(x.get('a', [])) for k, x in D.get('aw', {}).items()}

    def vrow(v, old=None):
        r = dict(old) if old else {c: '' for c in cols}
        status = {'L': 'address confirmed', 'A': 'approximate', 'U': 'not yet pinned'}[v['t']]
        r.update(venue_id=v['i'], venue=v['n'], city=v['c'], town=v['tw'], country=v['co'], nation=v['na'], region=v['r'],
                 latitude=v.get('la', ''), longitude=v.get('lo', ''), location_status=status, location_precision=v['p'],
                 mentions=v['m'], guests_naming=v['g'],
                 top_dish_categories='; '.join(f'{a} ({b})' for a, b in v.get('k', [])),
                 dishes_named='; '.join(v.get('d', [])[:4]) if v.get('d') else (old or {}).get('dishes_named', ''),
                 address=v.get('ad', ''))
        for c, col in COURSE_COL.items():
            r[col] = v.get('cs', {}).get(c, 0)
        if not old:
            r['awards'] = aw.get(v['i'], '')
        return r

    have_rows = {r['venue_id'] for r in rows}
    rows = [vrow(byid[r['venue_id']], r) if r['venue_id'] in touched or r['venue_id'] in spec.get('fix_venues', {}) else r for r in rows]
    rows += [vrow(v) for v in V if v['i'] not in have_rows]
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=cols, lineterminator='\r\n')
    w.writeheader(); w.writerows(rows)
    open(fn, 'w', encoding='utf-8-sig').write(out.getvalue())

    fn = 'partner/data/market_activity_by_quarter.csv'
    rows = list(csv.DictReader(open(fn, encoding='utf-8-sig')))
    cols = list(rows[0].keys())
    names = {mk['id']: (mk['n'], mk['k']) for mk in D['markets']}
    seen = set()
    for r in rows:
        key = (r['market_id'], r['quarter'])
        seen.add(key)
        if r['market_id'] in T and r['quarter'] in T[r['market_id']]:
            r['venue_mentions'] = T[r['market_id']][r['quarter']]
    for mid, qs in T.items():
        for q, n in qs.items():
            if (mid, q) not in seen and mid in names:
                rows.append(dict(market_id=mid, market=names[mid][0], level=names[mid][1], quarter=q, venue_mentions=n))
    order = {mk['id']: i for i, mk in enumerate(D['markets'])}
    rows.sort(key=lambda r: (order.get(r['market_id'], 10 ** 6), r['quarter']))
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=cols, lineterminator='\r\n')
    w.writeheader(); w.writerows(rows)
    open(fn, 'w', encoding='utf-8-sig').write(out.getvalue())
    print('venues', meta['venues'], 'pinned', meta['pinned'], 'mentions', meta['mentions'], 'cities', meta['cities'],
          'countries', meta['countries'], 'touched', len(touched))


if __name__ == '__main__':
    main(*sys.argv[1:])
