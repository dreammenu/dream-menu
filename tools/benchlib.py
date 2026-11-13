"""Shared helpers for showing the outside benchmarks (bench-public.js) on other pages.

Public comparisons only: partner comparisons (partner/bench-data.js) never appear outside the sign-in.
Used by build_venue_pages.py (dish pages), build_press.py (press kit), build_home.py (home) and
build_partner.py (/for-business). Run build_benchmarks.py first so the figures are current.
"""
import html, json, os, re

E = html.escape
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    p = os.path.join(ROOT, 'bench-public.js')
    if not os.path.exists(p):
        return dict(meta={}, items=[])
    s = open(p, encoding='utf-8').read()
    m = re.search(r'window\.DM_BENCHP\s*=\s*', s)
    return json.JSONDecoder().raw_decode(s[m.end():])[0]


B = _load()


def _partner_n():
    p = os.path.join(ROOT, 'partner', 'bench-data.js')
    if not os.path.exists(p):
        return 0
    t = open(p, encoding='utf-8').read()
    m = re.search(r'window\.DM_BENCHX\s*=\s*', t)
    return len(json.JSONDecoder().raw_decode(t[m.end():])[0]['items'])


N_PARTNER = _partner_n()
ITEMS = {b['id']: b for b in B['items']}
N_AGREE = sum(1 for b in B['items'] if b['verdict'] == 'agrees')
N_LOCAL = sum(1 for b in B['items'] if b['verdict'] == 'differs')
N_ALL = len(B['items'])
LABEL = {'agrees': 'Agrees', 'differs': 'Local insight', 'context': 'Context'}

# dish page slug -> the public comparisons that are about that dish
DISH = {
    'tiramisu': ['tiramisu'], 'sticky-toffee-pudding': ['stp'], 'scallops': ['scallops'],
    'margarita': ['margarita'], 'spicy-margarita': ['margarita'], 'martini': ['martini'],
    'diet-coke-and-coke-zero': ['diet'], 'coca-cola': ['diet', 'irnbru'], 'irn-bru': ['irnbru'],
    'coffee': ['tea'], 'tea': ['tea'], 'latte-and-flat-white': ['tea'], 'water': ['water'],
    'pizza': ['pizza'], 'mocktails-and-alcohol-free': ['nolo'], 'loaded-fries': ['loaded'],
    'fillet-steak': ['steakchicken'], 'ribeye-steak': ['steakchicken'], 'steak-cut-not-named': ['steakchicken'],
    'sharing-steaks-chateaubriand-cote-de-boeuf': ['steakchicken'], 'short-rib-and-braised-beef': ['steakchicken'],
    'other-pasta': ['italian'], 'bruschetta': ['italian'],
}


def chip(v):
    return f'<span class="bx-v bx-{v}">{LABEL[v]}</span>'


def card(b):
    src = f'<a href="{E(b["ext"]["url"])}" rel="noopener" target="_blank">{E(b["ext"]["who"])}, {E(b["ext"]["date"])}</a>'
    return (f'<div class="bx-item"><p class="bx-top">{chip(b["verdict"])} <b>{E(b["topic"])}</b></p>'
            f'<p><span class="bx-l">Dream Menu</span>{E(b["dm"]["text"])}</p>'
            f'<p><span class="bx-l">Outside</span>{E(b["ext"]["text"])} <small>{src}</small></p>'
            f'<p class="bx-read">{E(b["read"])}</p></div>')


def dish_card(slug):
    ids = [i for i in DISH.get(slug, []) if i in ITEMS]
    if not ids:
        return ''
    return ('<div class="card bx"><h2>How it compares</h2>' + ''.join(card(ITEMS[i]) for i in ids)
            + f'<p class="pg-mut"><a href="/analysis#compare">All {N_ALL} comparisons with outside research</a></p></div>')


def agree_list(limit=None, cls='bx-list'):
    """The comparisons that agree, one line each: what Dream Menu found, and who backs it."""
    xs = [b for b in B['items'] if b['verdict'] == 'agrees'][:limit]
    return (f'<ul class="{cls}">' + ''.join(
        f'<li><b>{E(b["topic"])}.</b> {E(b["dm"]["text"])}. <span class="bx-by">Backed by {E(b["ext"]["who"])} ({E(b["ext"]["date"])}): '
        f'{E(b["ext"]["text"])}.</span> <a href="{E(b["ext"]["url"])}" rel="noopener" target="_blank">Source</a></li>'
        for b in xs) + '</ul>')


def headline():
    """One wording everywhere, and the same counts the signed-out analysis page shows."""
    return f'Published research backs Dream Menu on {N_AGREE} of {N_ALL} topics; {N_LOCAL} more are local insights'


def partner_note():
    extra = N_PARTNER - N_ALL
    return f'Partners see {extra} more comparisons, on dish and drink movement and trading conditions.' if extra > 0 else ''
