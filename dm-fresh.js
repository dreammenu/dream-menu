/* dm-fresh.js: when each dataset behind the site was last collected and updated.
   Loaded on every page (added by tools/build_nav.py). It adds a "Data to ... · Updated ..." line under
   every visual or block of figures, a short status chip under the page title, and a data status panel
   in the footer. To record a refresh, change the dates in SETS below (set 'checked' when a source was checked and had nothing new). Nothing else needs editing. */
(function () {
  'use strict';
  var SETS = {
    interviews: { label: 'Dream Menu interviews', size: '1,256 interviews', from: '2025-09-01', to: '2026-11-10', updated: '2026-11-11',
      note: 'Dish categories refined 24 Oct 2026. Interviews to 10 Nov added 11 Nov.' },
    venues: { label: 'Venues named by guests', size: '1,935 venues, 1,722 pinned', from: '2025-09-01', to: '2026-11-10', updated: '2026-11-11',
      note: 'Addresses researched 22 Oct 2026; new venues added 11 Nov.' },
    awards: { label: 'Awards and guides', size: '21,046 award winners', to: '2026-11-11', updated: '2026-11-11',
      note: 'MICHELIN extract of 11 Oct 2026 plus later editions: Philippines 2027 (29 Oct), South Australia 2027 (14 Oct), Beijing & Tianjin 2027 (28 Oct), Kuala Lumpur & Penang 2027 (4 Nov), Chengdu 2027; World 50 Best Restaurants 2026 in full (1-50 announced 4 Nov); SLTN Awards 2026 (5 Nov); AA, Good Food Guide, OAD, La Liste, Tabelog and Gault&Millau lists.' },
    look: { label: '2026 Look Ahead operator survey', size: '55 operators', from: '2026-04-02', to: '2026-05-03', updated: '2026-10-24', checked: '2026-11-11' },
    report: { label: 'Hospitality Intelligence Report 2026', size: 'Edition 6', to: '2026-10-09', updated: '2026-10-21' },
    fringe: { label: 'Dream Fringe interviews', size: '52 interviews', from: '2026-07-24', to: '2026-08-28', updated: '2026-10-21', checked: '2026-11-11' },
    cocktail: { label: 'Dream Cocktail entries', size: '16 creations', to: '2026-06-08', updated: '2026-10-21', checked: '2026-11-11' },
    sandwich: { label: 'Dream Sandwich entries', size: '20 creations', to: '2026-05-14', updated: '2026-10-21', checked: '2026-11-11' },
    kitchen: { label: 'Venue interviews', size: '64 venues', from: '2025-09-03', to: '2026-07-31', updated: '2026-10-21', checked: '2026-11-11' },
    research: { label: 'Published research reviewed', size: '20 ideas scored', updated: '2026-10-26' },
    toolkit: { label: 'Operator toolkit', size: 'Benchmarks from the 2026 report', to: '2026-10-09', updated: '2026-10-26' },
    analysis: { label: 'Dream Menu analysis', size: 'Built from interviews and venues', to: '2026-11-10', updated: '2026-11-11' }
  };
  var M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmt(d) { if (!d) return ''; var p = d.split('-'); return (+p[2]) + ' ' + M[+p[1] - 1] + ' ' + p[0]; }
  function seen(s) { return s.checked && s.checked > s.updated ? s.checked : s.updated; }
  function days(d) { return Math.floor((Date.now() - new Date(d + 'T12:00:00Z').getTime()) / 864e5); }
  function line(k, opts) {
    var s = SETS[k]; if (!s) return '';
    var parts = [];
    if (s.to) parts.push((s.from ? 'Data ' + fmt(s.from) + ' to ' : 'Data to ') + fmt(s.to));
    if (seen(s) !== s.updated) parts.push('No new responses · checked ' + fmt(s.checked));
    else parts.push('Updated ' + fmt(s.updated));
    return (opts && opts.label === false ? '' : s.label + ' · ') + parts.join(' · ');
  }
  var CLOCK = '<svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 4.6V8l2.3 1.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';
  function stamp(keys, extra) {
    keys = [].concat(keys);
    var p = document.createElement('p');
    p.className = 'dm-fresh';
    p.setAttribute('data-fresh-stamp', keys.join(' '));
    var age = days(SETS[keys[0]] ? seen(SETS[keys[0]]) : '2026-10-27');
    p.innerHTML = CLOCK + '<span>' + keys.map(function (k) { return line(k); }).join('<br>') + (extra ? '<br>' + extra : '') + '</span>' +
      (age > 120 ? '<em class="dm-fresh-old">Over four months old</em>' : '');
    p.title = keys.map(function (k) { return SETS[k] && SETS[k].note ? SETS[k].note : ''; }).filter(Boolean).join(' ');
    return p;
  }

  // Which dataset each page draws on. 'def' is the page default; 'rules' match a section by id or heading text.
  var PAGES = {
    '/': { def: 'interviews', all: true, chip: ['interviews', 'venues'], rules: [['places', ['venues', 'interviews']], ['map', 'venues'], [/award/i, 'awards'], ['more', null], ['start', null], ['h-stats', null]] },
    '/insights': { def: 'interviews', all: true, chip: ['interviews'], rules: [[/trade feels|hospitality/i, 'look']] },
    '/briefing': { def: 'interviews', all: true, chip: ['interviews', 'look'], rules: [[/Look Ahead|operators/i, 'look']] },
    '/onepager': { def: 'interviews', chip: ['interviews'] },
    '/partner': { def: 'interviews', chip: ['interviews', 'venues'], rules: [[/Terms of use|partnership includes/i, null]] },
    '/rankings': { def: 'venues', chip: ['venues'] },
    '/awards': { def: 'awards', chip: ['awards'] },
    '/map': { def: 'venues', chip: ['venues', 'awards'] },
    '/specials': { def: 'fringe', all: true, chip: ['fringe', 'cocktail', 'sandwich'], rules: [['fringe', 'fringe'], ['cocktail', 'cocktail'], ['sandwich', 'sandwich']] },
    '/from-the-kitchen': { def: 'kitchen', all: true, chip: ['kitchen'] },
    '/report': { def: 'report', all: true, chip: ['report'], rules: [['sponsor', null], [/About the report/i, null]] },
    '/report/operator-pulse': { def: 'report', all: true, chip: ['report', 'look'] },
    '/report/glasgow': { def: 'report', all: true, chip: ['report', 'venues'] },
    '/report/whats-on-the-menu': { def: 'report', all: true, chip: ['report'] },
    '/report/opportunities': { def: 'report', all: true, chip: ['report'] },
    '/operators': { def: 'toolkit', chip: ['toolkit'], rules: [['actions', 'report'], [/outside view/i, null]] },
    '/tested-ideas': { def: 'research', all: true, chip: ['research'] },
    '/for-business': { def: 'interviews', chip: ['interviews'], rules: [[/sponsor|Work with us/i, null]] },
    '/how-it-works': { def: null, chip: ['interviews', 'venues', 'awards'] },
    '/restaurant-mot': { def: null, chip: null },
    '/case-studies': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/night-out': { def: null, chip: null },
    '/case-studies/glasgow-edinburgh': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/seafood': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/dessert': { def: null, chip: ['interviews', 'look'] },
    '/case-studies/drinks': { def: null, chip: ['interviews'] },
    '/case-studies/trend-fatigue': { def: null, chip: ['interviews'] },
    '/case-studies/neighbourhoods': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/guests-and-critics': { def: null, chip: ['venues', 'awards'] },
    '/case-studies/steak': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/italian': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/operator-confidence': { def: null, chip: ['look'] },
    '/case-studies/glasgow-2030': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/edinburgh-2030': { def: null, chip: ['interviews', 'venues'] },
    '/case-studies/ten-forces': { def: null, chip: ['interviews'] },
    '/case-studies/edge-of-the-menu': { def: null, chip: ['interviews'] },
    '/analysis': { def: null, chip: ['analysis', 'interviews', 'venues', 'awards', 'look'] }
  };
  var DATA_SEL = '.bars, table, .facts, canvas, figure, .chart, [class*="chart"], [class*="spark"], .stat, .stats, .h-stats, .kpis, .debate, .tile-num, svg[viewBox]:not([viewBox="0 0 24 24"]):not([viewBox="0 0 16 16"]):not([viewBox="0 0 12 12"]):not(.aico)';

  function path() { var p = location.pathname.replace(/\.html$/, '').replace(/\/$/, '').replace(/^\/index$/, ''); return p || '/'; }

  function pick(cfg, sec) {
    var id = sec.id || '', text = (sec.querySelector('h2, h3') || {}).textContent || '';
    var rules = cfg.rules || [];
    for (var i = 0; i < rules.length; i++) {
      var r = rules[i][0];
      if ((typeof r === 'string' && r === id) || (r instanceof RegExp && r.test(text))) return rules[i][1];
    }
    return cfg.def;
  }

  function run() {
    var cfg = PAGES[path()] || { def: undefined, chip: null };
    var main = document.querySelector('main') || document.body;
    // status chip under the page title
    if (cfg.chip) {
      var hero = main.querySelector('.iv-hero .iv-wrap, .hero .wrap, .navyband .wrap, .h-hero .wrap, .ex-hero .wrap, .cs-cover .wrap');
      var host = hero || main.querySelector('h1') && main.querySelector('h1').parentNode;
      if (host && !host.querySelector('.dm-chip')) {
        var c = document.createElement('p');
        c.className = 'dm-chip';
        var latest = cfg.chip.map(function (k) { return SETS[k].updated; }).sort().pop();
        var check = cfg.chip.map(function (k) { return seen(SETS[k]); }).sort().pop();
        c.innerHTML = CLOCK + '<span>' + (check > latest ? 'Checked for new responses <b>' + fmt(check) + '</b> · last change ' + fmt(latest) : 'Last updated <b>' + fmt(latest) + '</b>') + '</span>' +
          cfg.chip.map(function (k) { var s = SETS[k]; return '<span class="dm-chip-set">' + s.label + (s.to ? ': data to ' + fmt(s.to) : '') + '</span>'; }).join('');
        host.appendChild(c);
      }
    }
    // a stamp under every block that shows data
    if (cfg.def !== undefined) {
      main.querySelectorAll('section').forEach(function (sec) {
        if (sec.matches('.hero, .navyband, .h-hero, .h-stats, .audband, .ex-hero, .iv-hero, .iv-sec') || sec.querySelector('[data-fresh-stamp]') || sec.hasAttribute('data-no-fresh')) return;
        if (!cfg.all && !sec.querySelector(DATA_SEL)) return;
        var ds = pick(cfg, sec);
        if (!ds) return;
        var wrap = sec.querySelector(':scope > .wrap') || sec;
        wrap.appendChild(stamp(ds));
      });
    }
    // explicit markers: <div data-fresh="interviews look"></div>
    main.querySelectorAll('[data-fresh]').forEach(function (el) {
      if (el.querySelector('[data-fresh-stamp]')) return;
      el.appendChild(stamp(el.getAttribute('data-fresh').split(/\s+/)));
    });
    // data status panel in the footer
    var foot = document.querySelector('footer.foot');
    if (foot && !foot.querySelector('.dm-status')) {
      var d = document.createElement('details');
      d.className = 'dm-status';
      var rows = Object.keys(SETS).map(function (k) {
        var s = SETS[k];
        return '<tr><th scope="row">' + s.label + '</th><td>' + s.size + '</td><td>' + (s.to ? (s.from ? fmt(s.from) + ' to ' : 'to ') + fmt(s.to) : '') + '</td><td>' + fmt(s.updated) + (s.checked && s.checked > s.updated ? '<br><small>checked ' + fmt(s.checked) + ', nothing new</small>' : '') + '</td></tr>';
      }).join('');
      var newest = Object.keys(SETS).map(function (k) { return SETS[k].updated; }).sort().pop();
      d.innerHTML = '<summary>' + CLOCK + ' Data status: last updated ' + fmt(newest) + '</summary><div class="dm-status-in"><table><thead><tr><th>Dataset</th><th>Size</th><th>Collected</th><th>Updated</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
      var band = foot.querySelector('.footband');
      if (band && band.nextSibling) foot.insertBefore(d, band.nextSibling); else foot.appendChild(d);
    }
  }

  window.DM_FRESH = { sets: SETS, fmt: fmt, line: line, stamp: stamp };
  var css = document.createElement('style');
  css.textContent =
    '.dm-fresh{display:flex;gap:7px;align-items:flex-start;margin:14px 0 0;font:500 12.5px/1.45 var(--body,system-ui);color:var(--muted,#5b5b5f);letter-spacing:.01em}' +
    '.dm-fresh svg{flex:0 0 auto;margin-top:2px;opacity:.85}.dm-fresh-old{font-style:normal;margin-left:8px;padding:0 6px;border-radius:999px;background:var(--panel,#f3f3f1);color:var(--ink,#0b0b0b)}' +
    '.dm-chip{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;margin:16px 0 0;font:500 13px/1.4 var(--body,system-ui);opacity:.92}' +
    '.dm-chip svg{flex:0 0 auto}.dm-chip b{font-weight:700}.dm-chip-set{opacity:.8;padding-left:14px;border-left:1px solid currentColor;line-height:1.1}' +
    '.dm-status{margin:0 auto;max-width:1180px;padding:6px 20px 14px;font:500 13px/1.5 var(--body,system-ui)}' +
    '.dm-status summary{cursor:pointer;display:inline-flex;gap:7px;align-items:center;opacity:.85}.dm-status summary:hover{opacity:1}' +
    '.dm-status-in{overflow-x:auto;margin-top:10px}.dm-status table{border-collapse:collapse;width:100%;min-width:560px;font-size:12.5px}' +
    '.dm-status th,.dm-status td{text-align:left;padding:6px 10px 6px 0;border-bottom:1px solid rgba(127,127,127,.25);font-variant-numeric:tabular-nums;vertical-align:top}' +
    '.dm-status thead th{font-weight:700;opacity:.8}.dm-status tbody th{font-weight:600}' +
    '@media print{.dm-status{display:none}}';
  document.head.appendChild(css);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(run, 0); });
  else setTimeout(run, 0);
  window.addEventListener('load', function () { setTimeout(run, 50); });
})();
