/* analysis.js: draws /analysis from analysis-data.js. Public headline analysis only:
   no quarter-by-quarter movement (that stays in the partner area). */
(function () {
  'use strict';
  function start() {
  var A = window.DM_ANALYSIS, V = window.DMV;
  if (!A || !V || !window.DM_FRESH) return;
  var el = V.el, h = V.h, esc = V.esc, lin = V.lin, fmt = V.fmt;
  var F = window.DM_FRESH;
  var $ = function (s) { return document.querySelector(s); };
  var setT = function (id, html) { var n = document.getElementById(id); if (n) n.innerHTML = html; };
  var SRC_V = 'Source: venues and dishes named in ' + fmt(A.fresh.interviews) + ' Dream Menu interviews to ' + F.fmt(A.fresh.interviews_to) + '. Counts are dish mentions tied to a named venue.';

  // =================================================================== A. city appetite index
  (function cities() {
    var C = A.cities, host = $('#c-cities'); if (!host) return;
    var sigs = C.signature.filter(function (s) { return s.c; });
    var sc = $('#city-sig');
    if (sc) sc.innerHTML = sigs.map(function (s) { return '<div class="kpi"><span class="lab">' + esc(s.m) + '’s signature order</span><span class="val" style="font-size:28px">' + esc(s.c) + '</span><span class="del">' + (s.pin === 100 ? 'All ' + s.n : s.pin + '% of its ' + Math.round(s.n * 100 / s.pin)) + ' venue-linked mentions are in ' + esc(s.m) + ', which holds ' + s.base + '% of all mentions. Index ' + s.idx + '.</span></div>'; }).join('') +
      '<div class="kpi"><span class="lab">Venue-linked dish mentions</span><span class="val">' + fmt(C.total) + '</span><span class="del">' + C.markets.map(function (m, i) { return esc(m) + ' ' + fmt(C.totals[i]); }).slice(0, 2).join(', ') + '</span></div>';
    var c = V.card(host, { id: 'city-index', title: 'How often each market names a dish, against all markets (100 = the same)', sub: 'Index = the dish’s share of a market’s mentions ÷ its share everywhere × 100. Greyed cells rest on fewer than five mentions, so read them as a hint.', src: SRC_V, fresh: ['venues', 'interviews'], csv: 'dream-menu-city-appetite-index' });
    var scale = h('div', 'scale', 'Named less <i style="background:var(--v-r2)"></i><i style="background:var(--v-r1)"></i><i style="background:var(--v-d0)"></i><i style="background:var(--v-d1)"></i><i style="background:var(--v-d2)"></i><i style="background:var(--v-d3)"></i> Named more');
    c.el.insertBefore(scale, c.plot);
    function bucket(v) {
      if (v === null) return ['transparent', ''];
      if (v < 60) return ['var(--v-r2)', 'b-r2']; if (v < 85) return ['var(--v-r1)', 'b-r1']; if (v <= 115) return ['var(--v-d0)', 'b-d0'];
      if (v <= 150) return ['var(--v-d1)', 'b-d1']; if (v <= 220) return ['var(--v-d2)', 'b-d2']; return ['var(--v-d3)', 'b-d3'];
    }
    var cols = 'minmax(140px,1.7fr) ' + C.markets.map(function () { return 'minmax(64px,1fr)'; }).join(' ');
    var o = '<div class="heat-scroll"><div class="heat" style="grid-template-columns:' + cols + '"><div class="hh" style="text-align:left">Dish · share of all</div>' + C.markets.map(function (m, i) { return '<div class="hh">' + esc(m) + '<br><span style="font-weight:400">' + fmt(C.totals[i]) + '</span></div>'; }).join('');
    C.rows.forEach(function (r, ri) {
      o += '<div class="hl" title="' + esc(r.l) + '"><span style="overflow:hidden;text-overflow:ellipsis">' + esc(r.l) + '</span><span style="flex:none;font-weight:400;color:var(--v-muted);margin-left:6px">' + r.share + '%</span></div>';
      r.cells.forEach(function (cell, i) {
        var b = cell.thin ? ['var(--v-plane)', ''] : bucket(cell.idx);
        o += '<div class="hc ' + b[1] + '" style="background-color:' + b[0] + (cell.thin ? ';color:var(--v-muted)' : '') + '" data-r="' + ri + '" data-i="' + i + '">' + (cell.n ? cell.idx : '–') + '</div>';
      });
    });
    c.plot.innerHTML = o + '</div></div>';
    c.plot.querySelectorAll('.hc').forEach(function (cell) {
      var r = C.rows[+cell.getAttribute('data-r')], i = +cell.getAttribute('data-i'), x = r.cells[i];
      V.tip.bind(cell, '<b>' + esc(r.l) + '</b> <span class="k">' + esc(C.markets[i]) + '</span><div class="row"><span class="k">Mentions</span><span>' + x.n + '</span></div><div class="row"><span class="k">Share of market</span><span>' + x.share + '%</span></div><div class="row"><span class="k">Share everywhere</span><span>' + r.share + '%</span></div><div class="row"><span class="k">Index</span><span>' + (x.n ? x.idx : '–') + (x.thin ? ' (thin)' : '') + '</span></div>');
    });
    c.setTable([{ l: 'Dish', k: 'l' }, { l: 'Group', k: 'g' }, { l: 'Mentions', k: 'n', n: 1 }, { l: 'Share of all %', k: 'share', n: 1 }].concat(C.markets.map(function (m, i) { return { l: m + ' index', f: function (r) { return r.cells[i].n ? r.cells[i].idx : ''; }, n: 1 }; })).concat(C.markets.map(function (m, i) { return { l: m + ' mentions', f: function (r) { return r.cells[i].n; }, n: 1 }; })), C.rows);
    var g = sigs[0], e = sigs[1];
    setT('ta', g && e ? 'Glasgow orders the ' + esc(g.c.toLowerCase()) + ', Edinburgh the ' + esc(e.c.toLowerCase()) + ': each city has a drink it names far more than anywhere else' : 'Every market has its own appetite');
  })();

  // =================================================================== B. guests vs critics
  (function critics() {
    var K = A.critics, host = $('#c-critics'); if (!host) return;
    var grid = h('div', 'iv-grid2 even'); host.appendChild(grid);
    var a = h('div'), b = h('div'); grid.appendChild(a); grid.appendChild(b);
    var steps = [['10', 'Top 10'], ['25', 'Top 25'], ['50', 'Top 50'], ['100', 'Top 100'], [String(K.venues), 'All ' + fmt(K.venues)]];
    var c1 = V.card(a, { id: 'agreement', title: 'Share of guests’ most-named venues that hold a guide award', sub: 'Venues ranked by how many times guests name them. Award = any MICHELIN, 50 Best, AA, Good Food Guide, OAD, La Liste or other listed guide.', src: SRC_V.replace(' Counts are dish mentions tied to a named venue.', '') + ' Awards as listed on 29 Oct 2026.', fresh: ['venues', 'awards'], csv: 'dream-menu-guests-vs-critics' });
    V.responsive(c1.plot, function (W) {
      var H = 250, m = { t: 26, b: 34, l: 6, r: 6 }, s = V.svg(c1.plot, W, H, 'Award share by rank band');
      var rows = steps.map(function (st) { var t = K.tops[st[0]]; return { l: st[1], v: t.award / t.n * 100, a: t.award, n: t.n }; });
      var bw = Math.min(64, (W - m.l - m.r) / rows.length * 0.56), band = (W - m.l - m.r) / rows.length;
      var y = lin(0, 50, H - m.b, m.t);
      var g = el('g', { class: 'dmv-grid' }, s);
      [0, 10, 20, 30, 40, 50].forEach(function (t) { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); });
      rows.forEach(function (r, i) {
        var cx = m.l + band * i + band / 2, top = y(r.v), gg = el('g', {}, s);
        var w = bw, x0 = cx - w / 2, rr = 4;
        el('path', { d: 'M' + x0 + ' ' + y(0) + 'V' + (top + rr) + 'Q' + x0 + ' ' + top + ' ' + (x0 + rr) + ' ' + top + 'H' + (x0 + w - rr) + 'Q' + (x0 + w) + ' ' + top + ' ' + (x0 + w) + ' ' + (top + rr) + 'V' + y(0) + 'Z', fill: i === rows.length - 1 ? 'var(--v-ns)' : 'var(--v-brand)', class: 'dmv-mark' }, gg);
        el('text', { x: cx, y: top - 8, 'text-anchor': 'middle', class: 't-ink t-b t-num', 'font-size': 14 }, gg, Math.round(r.v) + '%');
        el('text', { x: cx, y: H - m.b + 18, 'text-anchor': 'middle', class: 't-ink2' }, gg, r.l);
        V.tip.bind(gg, '<b>' + esc(r.l) + ' named venues</b><div class="row"><span class="k">Hold a guide award</span><span>' + r.a + ' of ' + r.n + '</span></div>');
      });
      el('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: 'dmv-axis' }, s);
      c1.setTable([{ l: 'Venues', k: 'l' }, { l: 'With a guide award', k: 'a', n: 1 }, { l: 'Venues', k: 'n', n: 1 }, { l: 'Share %', f: function (r) { return r.v.toFixed(1); }, n: 1 }], rows);
    });
    var c2 = V.card(b, { id: 'concentration', title: 'How concentrated guest recommendations are', sub: 'Venues ranked by mentions; the line shows the share of all mentions held by the top x% of venues.', src: SRC_V.replace('Counts are dish mentions tied to a named venue.', fmt(K.mentions) + ' venue mentions across ' + fmt(K.venues) + ' venues.'), fresh: ['venues'], csv: 'dream-menu-mention-concentration' });
    V.responsive(c2.plot, function (W) {
      var H = 250, m = { t: 14, b: 34, l: 40, r: 14 }, s = V.svg(c2.plot, W, H, 'Concentration curve');
      var x = lin(0, 100, m.l, W - m.r), y = lin(0, 100, H - m.b, m.t);
      var g = el('g', { class: 'dmv-grid' }, s);
      [0, 25, 50, 75, 100].forEach(function (t) { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); el('text', { x: m.l - 8, y: y(t) + 4, 'text-anchor': 'end', class: 't-num' }, s, t + '%'); el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle', class: 't-num' }, s, t + '%'); });
      el('line', { x1: x(0), y1: y(0), x2: x(100), y2: y(100), stroke: 'var(--v-axis)', 'stroke-width': 1 }, s);
      el('text', { x: x(62), y: y(56), 'font-size': 11, transform: 'rotate(' + (-Math.atan((y(0) - y(100)) / (x(100) - x(0))) * 180 / Math.PI) + ' ' + x(62) + ' ' + y(56) + ')' }, s, 'if every venue were named equally');
      var pts = [[0, 0]].concat(K.curve);
      var d = pts.map(function (p, i) { return (i ? 'L' : 'M') + x(p[0]).toFixed(1) + ' ' + y(p[1]).toFixed(1); }).join('');
      el('path', { d: d + 'L' + x(100) + ' ' + y(0) + 'Z', fill: 'var(--v-brand)', opacity: .08 }, s);
      el('path', { d: d, fill: 'none', stroke: 'var(--v-brand)', 'stroke-width': 2, 'stroke-linejoin': 'round' }, s);
      [[10, K.marks[10]], [20, K.marks[20]]].forEach(function (mk) {
        var gg = el('g', {}, s);
        el('circle', { cx: x(mk[0]), cy: y(mk[1]), r: 5, fill: 'var(--v-brand)', stroke: 'var(--v-ring)', 'stroke-width': 2, class: 'dmv-mark' }, gg);
        el('text', { x: x(mk[0]) + 9, y: y(mk[1]) + 14, class: 't-ink t-b' }, gg, 'Top ' + mk[0] + '%: ' + Math.round(mk[1]) + '%');
        V.tip.bind(gg, '<b>Top ' + mk[0] + '% of venues</b><div class="row"><span class="k">Share of all mentions</span><span>' + mk[1] + '%</span></div>');
      });
      el('text', { x: m.l, y: H - 4, class: 't-ink2' }, s, 'Share of venues, most named first →');
      c2.setTable([{ l: 'Top share of venues %', f: function (r) { return r[0]; }, n: 1 }, { l: 'Share of mentions %', f: function (r) { return r[1]; }, n: 1 }], K.curve);
    });
    var lists = h('div', 'iv-grid2 even'); host.appendChild(lists);
    var l1 = h('div'), l2 = h('div'); lists.appendChild(l1); lists.appendChild(l2);
    var c3 = V.card(l1, { id: 'champions', title: 'Guests’ champions beyond the big guides', sub: 'The most-named venues not in the guides we track (MICHELIN, 50 Best, AA three Rosettes and above, Good Food Guide 100 Best Local, OAD, La Liste). Many hold other awards; this is about guide coverage, not quality.', src: SRC_V.replace(' Counts are dish mentions tied to a named venue.', ''), fresh: ['venues', 'awards'], csv: 'dream-menu-guest-champions' });
    c3.plot.innerHTML = '<ol class="rank-list">' + K.champions.map(function (v) { return '<li><div>' + esc(v.n) + '<span>' + esc(v.c) + (v.o ? ' · Also recognised: ' + esc(v.o) : '') + '</span></div><em>' + v.m + '</em></li>'; }).join('') + '</ol><p class="dmv-src" style="margin-top:8px">Number = times named by guests. Being outside the big guides says nothing about quality. "Also recognised" shows the Scottish, UK and bar awards we match by hand; a venue with none listed may still hold awards we have not found.</p>';
    c3.setTable([{ l: 'Venue', k: 'n' }, { l: 'City', k: 'c' }, { l: 'Mentions', k: 'm', n: 1 }, { l: 'Guests naming', k: 'g', n: 1 }, { l: 'Also recognised (examples)', k: 'o' }], K.champions);
    var c4 = V.card(l2, { id: 'award-favourites', title: 'Award holders guests name most', sub: 'Where guests and critics agree.', src: SRC_V.replace(' Counts are dish mentions tied to a named venue.', '') + ' Highest recognition shown.', fresh: ['venues', 'awards'], csv: 'dream-menu-award-favourites' });
    c4.plot.innerHTML = '<ol class="rank-list">' + K.starred.map(function (v) { return '<li><div>' + esc(v.n) + '<span>' + esc(v.c) + ' · ' + esc(v.aw) + '</span></div><em>' + v.m + '</em></li>'; }).join('') + '</ol><p class="dmv-src" style="margin-top:8px">Number = times named by guests.</p>';
    c4.setTable([{ l: 'Venue', k: 'n' }, { l: 'City', k: 'c' }, { l: 'Recognition', k: 'aw' }, { l: 'Mentions', k: 'm', n: 1 }], K.starred);
    var t25 = K.tops['25'], all = K.tops[String(K.venues)];
    setT('tb', 'The more guests name a venue, the likelier the critics agree: ' + Math.round(t25.award / t25.n * 100) + '% of the 25 most-named venues hold a guide award, against ' + Math.round(all.award / all.n * 100) + '% of all venues named');
    setT('sb', 'Recommendation is concentrated: the top 10% of venues collect <b>' + Math.round(K.marks[10]) + '%</b> of every mention, while <b>' + K.once_pct + '%</b> of venues are named only once. The venues guests love most are mostly not the ones the guides list. That gap is where a guest-led index earns its place.');
  })();

  // =================================================================== C. course concentration
  (function conc() {
    var host = $('#c-conc'); if (!host) return;
    var R = A.conc;
    var c = V.card(host, { id: 'settled', title: 'Share of each course’s answers taken by its three biggest food groups', sub: 'The higher the bar, the more settled the course: guests agree on what it should be.', src: 'Source: Dream Menu interviews, ' + fmt(A.fresh.dish_n) + ' answering the dish questions, 1 Sep 2025 to ' + F.fmt(A.fresh.interviews_to) + '. Shares of answers coded to a food group.', fresh: ['interviews'], csv: 'dream-menu-course-concentration',
      legend: [['Biggest group', '--v-brand', 'sq'], ['Second', '--v-d2', 'sq'], ['Third', '--v-d1', 'sq']] });
    V.responsive(c.plot, function (W) {
      var mob = W < 560, lw = mob ? 96 : 150, rh = 46, m = { t: 6, b: 26, r: 46 };
      var rows = R.slice().sort(function (a, b) { return b.top3 - a.top3; });
      var H = m.t + rows.length * rh + m.b, s = V.svg(c.plot, W, H, 'Course concentration');
      var x = lin(0, 100, lw, W - m.r);
      var g = el('g', { class: 'dmv-grid' }, s);
      [0, 25, 50, 75, 100].forEach(function (t) { el('line', { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 16, 'text-anchor': 'middle', class: 't-num' }, s, t + '%'); });
      var COL = ['--v-brand', '--v-d2', '--v-d1'];
      rows.forEach(function (r, i) {
        var y0 = m.t + i * rh + 8, gg = el('g', {}, s), cx = x(0);
        el('text', { x: 0, y: y0 + 13, class: 't-ink', 'font-weight': 700 }, gg, r.cl);
        r.groups.forEach(function (gp, k) {
          var w = x(gp[1]) - x(0);
          var seg = el('rect', { x: cx, y: y0, width: Math.max(0, w - 2), height: 18, fill: 'var(' + COL[k] + ')', rx: k === 2 ? 3 : 0 }, gg);
          if (w > 70 && !mob) el('text', { x: cx + 6, y: y0 + 13, fill: k === 2 ? 'var(--v-ink)' : '#fff', 'font-size': 11, 'font-weight': 600 }, gg, gp[0].length > w / 6.5 ? gp[0].slice(0, Math.floor(w / 6.5) - 1) + '…' : gp[0]);
          V.tip.bind(seg, '<b>' + esc(gp[0]) + '</b> <span class="k">' + esc(r.cl) + '</span><div class="row"><span class="k">Share of answers</span><span>' + gp[1].toFixed(1) + '%</span></div>');
          cx += w;
        });
        el('text', { x: cx + 6, y: y0 + 13, class: 't-ink t-b t-num' }, gg, Math.round(r.top3) + '%');
        el('text', { x: lw, y: y0 + 32, 'font-size': 11 }, gg, 'Top dish: ' + r.dish + ' ' + r.dishv.toFixed(1) + '%');
      });
      c.setTable([{ l: 'Course', k: 'cl' }, { l: 'Answers', k: 'n', n: 1 }, { l: 'Top three groups %', k: 'top3', n: 1 }, { l: 'Biggest group', k: 'top1' }, { l: 'Its share %', k: 'top1v', n: 1 }, { l: 'Top dish', k: 'dish' }, { l: 'Its share %', k: 'dishv', n: 1 }], rows);
    });
    var food = R.slice().sort(function (a, b) { return b.top3 - a.top3; });
    var low = food[food.length - 1], open = food.filter(function (r) { return r.top3 - low.top3 < 1; });
    var openTxt = open.map(function (r) { return r.cl.toLowerCase() + 's'; }).join(' and ');
    setT('tc', food[0].cl + 's are the most settled course, ' + openTxt + ' the most open: the three biggest groups take ' + Math.round(food[0].top3) + '% of ' + food[0].cl.toLowerCase() + ' answers, against ' + Math.round(low.top3) + '% for ' + openTxt);
  })();
  }
  // dm-fresh.js loads deferred, so draw once the page is parsed and it has run
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
