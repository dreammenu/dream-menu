/* trend-charts.js: the "menu over time" charts, drawn with the dmviz.js kit.
   Used by /analysis: course-level data in trend-public.js and bench-public.js for everyone; the full data in
   partner/trend-data.js and partner/bench-data.js (behind sign-in) adds partner charts in place. This file holds no data of its own. Built for
   tools/build_trends.py output; every value is a share of answers within a course. */
(function () {
  'use strict';
  var V = window.DMV; if (!V) return;
  var el = V.el, h = V.h, esc = V.esc, lin = V.lin, fmt = V.fmt, pp = V.pp;
  var STAGE_COL = { 'Rising': '--v-up', 'Steady staple': '--v-s3', 'Recovering': '--v-s5', 'Peaked': '--v-s2', 'No clear pattern': '--v-ns', 'Fading': '--v-down' };
  var STAGE_ORDER = ['Rising', 'Steady staple', 'Recovering', 'Peaked', 'No clear pattern', 'Fading'];
  var STAGE_NOTE = {
    'Rising': 'Recent share clearly above the earlier quarters',
    'Steady staple': 'Above-median dish whose share holds in every full quarter',
    'Recovering': 'Dipped clearly in a middle quarter, now back up',
    'Peaked': 'Rose to a high in a middle quarter, then fell back clearly',
    'No clear pattern': 'Moves are within what sampling alone gives',
    'Fading': 'Recent share clearly below the earlier quarters'
  };
  var MIX_COL = ['--v-s1', '--v-s2', '--v-s3', '--v-s4', '--v-s5', '--v-ns'];
  function ql(q) { return q.replace(/^20(\d\d)-Q(\d)$/, 'Q$2 $1'); }
  function pv(p) { return p === null || p === undefined ? '' : p < 0.001 ? 'p < 0.001' : 'p = ' + (+p).toFixed(3); }
  function src(D) {
    return 'Source: Dream Menu interviews, ' + fmt(D.meta.n) + ' answering the dish questions, to ' + (window.DM_FRESH ? window.DM_FRESH.fmt(D.meta.last) : D.meta.last) +
      '. Shares of answers within each course. Earlier = ' + D.meta.early.map(ql).join(' and ') + '; recent = ' + D.meta.late.map(ql).join(', ') +
      '. Quarters under ' + D.meta.min_n + ' answers shown hollow.';
  }
  function courseChips(card, D, cur, draw) {
    V.chips(card.filters, D.meta.courses.map(function (c) { return [c[0], c[1] + 's']; }), cur, draw);
  }
  function wrapText(s, n) { var w = String(s).split(' '), out = [], line = ''; w.forEach(function (x) { if ((line + ' ' + x).trim().length > n && line) { out.push(line); line = x; } else line = (line + ' ' + x).trim(); }); if (line) out.push(line); return out; }

  // ------------------------------------------------------------------ findings list
  function findings(host, D) {
    var o = h('ol', 'tr-find');
    D.find.forEach(function (f) { o.appendChild(h('li', '', esc(f))); });
    host.appendChild(o);
  }

  // ------------------------------------------------------------------ churn: observed against chance
  function churn(host, D) {
    var c = V.card(host, { id: 'tr-churn', title: 'Share of each course’s answers that moved to a different food group', sub: 'Recent quarters against the earlier ones. The grey band is where 95% of results fall if nothing had really changed and only sampling varied; a dot beyond it is real change.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-course-churn',
      legend: [['Moved beyond chance', '--v-up'], ['Within chance', '--v-ns'], ['95% range from sampling alone', '--v-grid']] });
    var rows = D.churn;
    V.responsive(c.plot, function (W) {
      var rowH = 46, m = { t: 22, b: 30, l: 104, r: 64 }, H = m.t + m.b + rows.length * rowH;
      var s = V.svg(c.plot, W, H, 'Course churn against chance');
      var top = Math.max(20, Math.ceil(Math.max.apply(null, rows.map(function (r) { return Math.max(r.obs, r.p95); })) / 5) * 5);
      var x = lin(0, top, m.l, W - m.r);
      var g = el('g', { class: 'dmv-grid' }, s);
      for (var t = 0; t <= top; t += 5) { el('line', { x1: x(t), x2: x(t), y1: m.t - 6, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle' }, s, t + '%'); }
      rows.forEach(function (r, i) {
        var y = m.t + i * rowH + rowH / 2;
        el('text', { x: m.l - 12, y: y + 4, 'text-anchor': 'end', fill: 'var(--v-ink)', 'font-weight': 600 }, s, r.cl + 's');
        el('rect', { x: x(0), y: y - 9, width: x(r.p95) - x(0), height: 18, rx: 4, fill: 'var(--v-grid)' }, s);
        el('line', { x1: x(r.chance), x2: x(r.chance), y1: y - 9, y2: y + 9, stroke: 'var(--v-muted)', 'stroke-width': 2 }, s);
        var real = r.p < 0.05, col = real ? 'var(--v-up)' : 'var(--v-ns)';
        el('line', { x1: x(r.chance), x2: x(r.obs), y1: y, y2: y, stroke: col, 'stroke-width': 2 }, s);
        var dot = el('circle', { cx: x(r.obs), cy: y, r: 7, fill: col, stroke: 'var(--v-ring)', 'stroke-width': 2 }, s);
        el('text', { x: x(r.obs) + 13, y: y + 4, fill: 'var(--v-ink)', 'font-weight': 700 }, s, r.obs.toFixed(1) + '%');
        var hit = el('rect', { x: m.l, y: y - rowH / 2, width: W - m.l - m.r, height: rowH, fill: 'transparent' }, s);
        V.tip.bind(hit, '<b>' + esc(r.cl) + 's</b><div class="row"><span class="k">Moved group</span><span>' + r.obs.toFixed(1) + '% of answers</span></div><div class="row"><span class="k">Expected from sampling</span><span>' + r.chance.toFixed(1) + '% (95% up to ' + r.p95.toFixed(1) + '%)</span></div><div class="row"><span class="k">Beyond chance</span><span>' + pp(r.beyond) + '</span></div><div class="row"><span class="k">Chance of this much or more</span><span>' + pv(r.p) + '</span></div><div class="row"><span class="k">Answers</span><span>' + fmt(r.n1) + ' earlier, ' + fmt(r.n2) + ' recent</span></div>');
        void dot;
      });
    });
    c.setTable([{ l: 'Course', f: function (r) { return r.cl; } }, { l: 'Moved food group %', k: 'obs', n: 1 }, { l: 'Expected from sampling %', k: 'chance', n: 1 }, { l: '95% of chance results below %', k: 'p95', n: 1 }, { l: 'Beyond chance, pts', k: 'beyond', n: 1 }, { l: 'p', k: 'p', n: 1 }, { l: 'Moved dish (all tracked dishes) %', k: 'dish', n: 1 }, { l: 'Dish, expected from sampling %', k: 'dish_chance', n: 1 }], rows);
  }

  // ------------------------------------------------------------------ concentration small multiples
  function conc(host, D) {
    var c = V.card(host, { id: 'tr-conc', title: 'Share of answers taken by each course’s five favourite dishes, by quarter', sub: 'A rising line means guests are converging on the same few dishes; a falling one means the course is opening up. Bands are 95% ranges for each quarter.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-top-five-share' });
    var grid = h('div', 'tr-sm'); c.plot.appendChild(grid);
    D.conc.forEach(function (r) {
      var cell = h('div', 'tr-cell'); grid.appendChild(cell);
      cell.appendChild(h('p', 'tr-ct', '<b>' + esc(r.cl) + 's</b> <span class="tr-tag ' + (r.sig ? (r.move > 0 ? 'up' : 'dn') : 'ns') + '">' + esc(r.verdict) + '</span>'));
      cell.appendChild(h('p', 'tr-cs', esc(r.early.toFixed(1)) + '% earlier → ' + esc(r.late.toFixed(1)) + '% recent · ' + esc(r.dishes.join(', '))));
      var plot = h('div'); cell.appendChild(plot);
      V.responsive(plot, function (W) {
        var H = 150, m = { t: 10, b: 22, l: 30, r: 8 }, s = V.svg(plot, W, H, r.cl + ' top five share');
        var top = Math.max(10, Math.ceil(Math.max.apply(null, r.q.map(function (x) { return x.hi || 0; })) / 10) * 10);
        var x = lin(0, r.q.length - 1, m.l + 6, W - m.r - 6), y = lin(0, top, H - m.b, m.t);
        var g = el('g', { class: 'dmv-grid' }, s);
        [0, top / 2, top].forEach(function (t) { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); el('text', { x: m.l - 5, y: y(t) + 4, 'text-anchor': 'end' }, s, t + '%'); });
        var band = '', bandB = '';
        r.q.forEach(function (p, i) { if (p.lo === null) return; band += (band ? 'L' : 'M') + x(i) + ' ' + y(p.hi); });
        r.q.slice().reverse().forEach(function (p, j) { var i = r.q.length - 1 - j; if (p.lo === null) return; bandB += 'L' + x(i) + ' ' + y(p.lo); });
        el('path', { d: band + bandB + 'Z', fill: 'var(--v-wash)' }, s);
        var d = '';
        r.q.forEach(function (p, i) { if (p.share === null) return; d += (d ? 'L' : 'M') + x(i) + ' ' + y(p.share); });
        el('path', { d: d, fill: 'none', stroke: 'var(--v-s1)', 'stroke-width': 2, 'stroke-linejoin': 'round' }, s);
        r.q.forEach(function (p, i) {
          if (p.share === null) return;
          var dot = el('circle', { cx: x(i), cy: y(p.share), r: 4, fill: p.low ? 'var(--v-surface)' : 'var(--v-s1)', stroke: 'var(--v-s1)', 'stroke-width': 2 }, s);
          el('text', { x: x(i), y: H - 6, 'text-anchor': 'middle' }, s, ql(p.q).replace(' ', ' '));
          var hit = el('rect', { x: x(i) - 16, y: m.t, width: 32, height: H - m.t - m.b, fill: 'transparent' }, s);
          V.tip.bind(hit, '<b>' + esc(r.cl) + 's, ' + ql(p.q) + '</b><div class="row"><span class="k">Top five share</span><span>' + p.share.toFixed(1) + '%</span></div><div class="row"><span class="k">95% range</span><span>' + p.lo + '% to ' + p.hi + '%</span></div><div class="row"><span class="k">Answers</span><span>' + fmt(p.n) + (p.low ? ' (low base)' : '') + '</span></div>');
          void dot;
        });
      });
    });
    var rows = [];
    D.conc.forEach(function (r) { r.q.forEach(function (p) { rows.push({ cl: r.cl, q: ql(p.q), share: p.share, lo: p.lo, hi: p.hi, n: p.n, low: p.low ? 'yes' : '' }); }); });
    c.setTable([{ l: 'Course', k: 'cl' }, { l: 'Quarter', k: 'q' }, { l: 'Top five share %', k: 'share', n: 1 }, { l: '95% low', k: 'lo', n: 1 }, { l: '95% high', k: 'hi', n: 1 }, { l: 'Answers', k: 'n', n: 1 }, { l: 'Low base', k: 'low' }], rows);
  }

  // ------------------------------------------------------------------ lifecycle mix per course
  function stageBar(host, D) {
    var c = V.card(host, { id: 'tr-stages', title: 'Where each course’s tracked dishes sit in their life cycle', sub: 'The fourteen most-named dishes in each course, sorted by the shape of their share over six quarters. Only moves that pass a significance test count as rising, fading, peaked or recovering.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-lifecycle-mix',
      legend: STAGE_ORDER.map(function (s) { return [s, STAGE_COL[s]]; }) });
    var rows = D.stages;
    V.responsive(c.plot, function (W) {
      var rowH = 40, m = { t: 6, b: 6, l: 104, r: 10 }, H = m.t + m.b + rows.length * rowH;
      var s = V.svg(c.plot, W, H, 'Life-cycle mix by course');
      rows.forEach(function (r, i) {
        var y = m.t + i * rowH + 8, tot = 0; STAGE_ORDER.forEach(function (k) { tot += r.c[k] || 0; });
        el('text', { x: m.l - 12, y: y + 17, 'text-anchor': 'end', fill: 'var(--v-ink)', 'font-weight': 600 }, s, r.cl + 's');
        var x = lin(0, tot, m.l, W - m.r), acc = 0;
        STAGE_ORDER.forEach(function (k) {
          var n = r.c[k] || 0; if (!n) return;
          var x0 = x(acc), x1 = x(acc + n); acc += n;
          var seg = el('rect', { x: x0 + 1, y: y, width: Math.max(0, x1 - x0 - 2), height: 24, rx: 4, fill: 'var(' + STAGE_COL[k] + ')' }, s);
          if (x1 - x0 > 22) el('text', { x: (x0 + x1) / 2, y: y + 16, 'text-anchor': 'middle', fill: k === 'No clear pattern' ? 'var(--v-ink)' : '#fff', 'font-weight': 700 }, s, String(n));
          V.tip.bind(seg, '<b>' + esc(r.cl) + 's: ' + esc(k) + '</b><div class="row"><span class="k">Dishes</span><span>' + n + ' of ' + tot + ' (' + Math.round(100 * n / tot) + '%)</span></div><div class="row"><span class="k">Means</span><span>' + esc(STAGE_NOTE[k]) + '</span></div>');
        });
      });
    });
    c.setTable([{ l: 'Course', f: function (r) { return r.cl; } }].concat(STAGE_ORDER.map(function (k) { return { l: k, f: function (r) { return r.c[k] || 0; }, n: 1 }; })), rows);
  }

  // ------------------------------------------------------------------ steady staples: range bars
  function staples(host, D) {
    var list = D.staples || [];
    if (!list.length) return;
    var c = V.card(host, { id: 'tr-staples', title: 'The steady staples: dishes whose share never really moves', sub: 'Lowest to highest share in any full quarter, with the dot at the share across all answers. Safe ground for a core range.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-steady-staples' });
    var order = D.meta.courses.map(function (x) { return x[1]; });
    var rows = list.slice().sort(function (a, b) { return a.cl === b.cl ? b.pct - a.pct : order.indexOf(a.cl) - order.indexOf(b.cl); });
    V.responsive(c.plot, function (W) {
      var rowH = 26, m = { t: 8, b: 28, l: Math.min(250, W * 0.42), r: 46 }, H = m.t + m.b + rows.length * rowH;
      var s = V.svg(c.plot, W, H, 'Steady staples range');
      var top = Math.ceil(Math.max.apply(null, rows.map(function (r) { return r.hi; })) / 5) * 5;
      var x = lin(0, top, m.l, W - m.r), g = el('g', { class: 'dmv-grid' }, s);
      for (var t = 0; t <= top; t += 5) { el('line', { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle' }, s, t + '%'); }
      rows.forEach(function (r, i) {
        var y = m.t + i * rowH + rowH / 2;
        el('text', { x: m.l - 10, y: y + 4, 'text-anchor': 'end', fill: 'var(--v-ink)' }, s, r.l);
        el('text', { x: 4, y: y + 4, fill: 'var(--v-muted)' }, s, (i === 0 || rows[i - 1].cl !== r.cl) ? r.cl + 's' : '');
        el('line', { x1: x(r.lo), x2: x(r.hi), y1: y, y2: y, stroke: 'var(--v-s3)', 'stroke-width': 6, 'stroke-linecap': 'round', opacity: 0.45 }, s);
        el('circle', { cx: x(r.pct), cy: y, r: 5, fill: 'var(--v-s3)', stroke: 'var(--v-ring)', 'stroke-width': 2 }, s);
        el('text', { x: x(r.hi) + 8, y: y + 4, fill: 'var(--v-ink2)' }, s, r.pct.toFixed(1) + '%');
        var hit = el('rect', { x: 0, y: y - rowH / 2, width: W, height: rowH, fill: 'transparent' }, s);
        V.tip.bind(hit, '<b>' + esc(r.l) + '</b> <span class="k">' + esc(r.cl) + '</span><div class="row"><span class="k">Share of all answers</span><span>' + r.pct.toFixed(1) + '%</span></div><div class="row"><span class="k">Range in full quarters</span><span>' + r.lo + '% to ' + r.hi + '%</span></div>');
      });
    });
    c.setTable([{ l: 'Dish', k: 'l' }, { l: 'Course', k: 'cl' }, { l: 'Share %', k: 'pct', n: 1 }, { l: 'Lowest full quarter %', k: 'lo', n: 1 }, { l: 'Highest full quarter %', k: 'hi', n: 1 }], rows);
  }

  // ------------------------------------------------------------------ where the share went (partner)
  function flows(host, D) {
    var cur = D.flows.slice().sort(function (a, b) { return b.lost - a.lost; })[0].course;
    var c = V.card(host, { id: 'tr-flows', title: 'Where the share went: food-group gains and losses, earlier to recent', sub: 'Losses on the left add up to gains on the right. These are net shifts between two sets of guests, not individual people switching. Solid bars are clear moves.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-share-flows', filters: true,
      legend: [['Clear gain', '--v-up'], ['Clear loss', '--v-down'], ['Not a clear move', '--v-ns']] });
    function draw(k) {
      cur = k; var F = D.flows.filter(function (f) { return f.course === k; })[0];
      var rows = F.groups.slice().sort(function (a, b) { return a.move - b.move; });
      V.responsive(c.plot, function (W) {
        var rowH = 30, m = { t: 30, b: 26, l: Math.min(210, W * 0.36), r: 20 }, H = m.t + m.b + rows.length * rowH;
        var s = V.svg(c.plot, W, H, 'Share flows');
        var mx = Math.max(4, Math.ceil(Math.max.apply(null, rows.map(function (r) { return Math.abs(r.move); }))));
        var x = lin(-mx, mx, m.l, W - m.r), g = el('g', { class: 'dmv-grid' }, s);
        [-mx, -mx / 2, 0, mx / 2, mx].forEach(function (t) { el('line', { x1: x(t), x2: x(t), y1: m.t - 4, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle' }, s, (t > 0 ? '+' : '') + (Math.round(t * 10) / 10)); });
        el('text', { x: x(0) - 8, y: 16, 'text-anchor': 'end', fill: 'var(--v-ink2)', 'font-weight': 600 }, s, F.lost.toFixed(1) + ' pts lost');
        el('text', { x: x(0) + 8, y: 16, fill: 'var(--v-ink2)', 'font-weight': 600 }, s, F.won.toFixed(1) + ' pts gained');
        el('line', { x1: x(0), x2: x(0), y1: m.t - 6, y2: H - m.b, class: 'dmv-axis' }, s);
        rows.forEach(function (r, i) {
          var y = m.t + i * rowH + 5, col = r.sig ? (r.move > 0 ? 'var(--v-up)' : 'var(--v-down)') : 'var(--v-ns)';
          el('text', { x: m.l - 10, y: y + 14, 'text-anchor': 'end', fill: 'var(--v-ink)' }, s, r.l);
          var x0 = x(Math.min(0, r.move)), x1 = x(Math.max(0, r.move));
          var bar = el('rect', { x: x0, y: y, width: Math.max(1, x1 - x0), height: 20, rx: 4, fill: col }, s);
          var inside = r.move < 0 ? x0 - m.l < 64 : W - m.r - x1 < 64;
          el('text', { x: inside ? (r.move < 0 ? x0 + 8 : x1 - 8) : (r.move >= 0 ? x1 + 6 : x0 - 6), y: y + 14, 'text-anchor': (r.move >= 0) !== inside ? 'start' : 'end', fill: inside ? '#fff' : 'var(--v-ink2)', 'font-weight': 600 }, s, pp(r.move));
          V.tip.bind(bar, '<b>' + esc(r.l) + '</b><div class="row"><span class="k">Earlier</span><span>' + r.early + '%</span></div><div class="row"><span class="k">Recent</span><span>' + r.late + '%</span></div><div class="row"><span class="k">Change</span><span>' + pp(r.move) + '</span></div>' + (r.p !== null ? '<div class="row"><span class="k">Test</span><span>' + pv(r.p) + (r.sig ? ', clear' : ', not clear') + '</span></div>' : ''));
        });
      });
      c.setTable([{ l: 'Food group', k: 'l' }, { l: 'Earlier %', k: 'early', n: 1 }, { l: 'Recent %', k: 'late', n: 1 }, { l: 'Change, pts', k: 'move', n: 1 }, { l: 'p', k: 'p', n: 1 }, { l: 'Clear', f: function (r) { return r.sig ? 'yes' : ''; } }], rows, 'dream-menu-share-flows-' + k);
    }
    courseChips(c, D, cur, draw); draw(cur);
  }

  // ------------------------------------------------------------------ then vs now slope (partner)
  function slope(host, D) {
    var cur = 'd';
    var c = V.card(host, { id: 'tr-slope', title: 'Then and now: every tracked dish, earlier share against recent share', sub: 'Each line joins a dish’s pooled share in the earlier quarters to the recent ones. Coloured lines are clear moves; grey lines are within noise.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-then-and-now', filters: true,
      legend: [['Clearly rising', '--v-up'], ['Clearly falling', '--v-down'], ['Not a clear move', '--v-ns']] });
    function draw(k) {
      cur = k; var rows = D.life.filter(function (r) { return r.course === k; });
      V.responsive(c.plot, function (W) {
        var H = 420, lab = Math.min(200, W * 0.3), m = { t: 30, b: 16, l: lab, r: lab }, s = V.svg(c.plot, W, H, 'Then and now');
        var top = Math.ceil(Math.max.apply(null, rows.map(function (r) { return Math.max(r.early, r.late); })) + 1);
        var y = lin(0, top, H - m.b, m.t), x0 = m.l, x1 = W - m.r;
        el('text', { x: x0, y: 16, 'text-anchor': 'middle', fill: 'var(--v-ink2)', 'font-weight': 700 }, s, 'Earlier');
        el('text', { x: x1, y: 16, 'text-anchor': 'middle', fill: 'var(--v-ink2)', 'font-weight': 700 }, s, 'Recent');
        el('line', { x1: x0, x2: x0, y1: m.t, y2: H - m.b, class: 'dmv-axis' }, s); el('line', { x1: x1, x2: x1, y1: m.t, y2: H - m.b, class: 'dmv-axis' }, s);
        function place(list, key) {   // spread labels so they never overlap
          var ys = list.map(function (r) { return { r: r, y: y(r[key]) }; }).sort(function (a, b) { return a.y - b.y; });
          for (var i = 1; i < ys.length; i++) if (ys[i].y - ys[i - 1].y < 14) ys[i].y = ys[i - 1].y + 14;
          var over = ys.length ? ys[ys.length - 1].y - (H - m.b) : 0; if (over > 0) ys.forEach(function (o) { o.y -= over; });
          return ys;
        }
        var ordered = rows.slice().sort(function (a, b) { return (a.sig ? 1 : 0) - (b.sig ? 1 : 0); });
        ordered.forEach(function (r) {
          var col = r.sig ? (r.move > 0 ? 'var(--v-up)' : 'var(--v-down)') : 'var(--v-ns)';
          var ln = el('line', { x1: x0, x2: x1, y1: y(r.early), y2: y(r.late), stroke: col, 'stroke-width': r.sig ? 3 : 1.5, 'stroke-linecap': 'round' }, s);
          el('circle', { cx: x0, cy: y(r.early), r: r.sig ? 4.5 : 3, fill: col }, s); el('circle', { cx: x1, cy: y(r.late), r: r.sig ? 4.5 : 3, fill: col }, s);
          var hit = el('line', { x1: x0, x2: x1, y1: y(r.early), y2: y(r.late), stroke: 'transparent', 'stroke-width': 12 }, s);
          V.tip.bind(hit, '<b>' + esc(r.l) + '</b><div class="row"><span class="k">Earlier</span><span>' + r.early + '%</span></div><div class="row"><span class="k">Recent</span><span>' + r.late + '%</span></div><div class="row"><span class="k">Change</span><span>' + pp(r.move) + ', ' + pv(r.p) + '</span></div><div class="row"><span class="k">Stage</span><span>' + esc(r.stage) + '</span></div>');
          void ln;
        });
        place(rows, 'early').forEach(function (o) { el('text', { x: x0 - 10, y: o.y + 4, 'text-anchor': 'end', fill: o.r.sig ? 'var(--v-ink)' : 'var(--v-muted)', 'font-weight': o.r.sig ? 700 : 400 }, s, o.r.l + ' ' + o.r.early.toFixed(1)); });
        place(rows, 'late').forEach(function (o) { el('text', { x: x1 + 10, y: o.y + 4, fill: o.r.sig ? 'var(--v-ink)' : 'var(--v-muted)', 'font-weight': o.r.sig ? 700 : 400 }, s, o.r.late.toFixed(1) + ' ' + o.r.l); });
      });
      c.setTable([{ l: 'Dish', k: 'l' }, { l: 'Earlier %', k: 'early', n: 1 }, { l: 'Recent %', k: 'late', n: 1 }, { l: 'Change, pts', k: 'move', n: 1 }, { l: 'p', k: 'p', n: 1 }, { l: 'Stage', k: 'stage' }], rows, 'dream-menu-then-and-now-' + k);
    }
    courseChips(c, D, cur, draw); draw(cur);
  }

  // ------------------------------------------------------------------ menu mix by quarter (partner)
  function mix(host, D) {
    var cur = 'd';
    var c = V.card(host, { id: 'tr-mix', title: 'The shape of each course, quarter by quarter', sub: 'Each bar is one quarter’s answers split across the five biggest food groups (100% = every coded answer). Faded bars rest on fewer than ' + D.meta.min_n + ' answers.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-menu-mix', filters: true });
    function draw(k) {
      cur = k; var M = D.mix.filter(function (x) { return x.course === k; })[0];
      V.legend(c.legend, M.rows.map(function (r, i) { return [r.l, MIX_COL[i]]; }));
      V.responsive(c.plot, function (W) {
        var H = 330, m = { t: 10, b: 40, l: 36, r: Math.min(190, W * 0.26) }, s = V.svg(c.plot, W, H, 'Menu mix by quarter');
        var n = M.q.length, bw = Math.min(70, (W - m.l - m.r) / n * 0.62), step = (W - m.l - m.r) / n;
        var y = lin(0, 100, H - m.b, m.t), g = el('g', { class: 'dmv-grid' }, s);
        [0, 25, 50, 75, 100].forEach(function (t) { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); el('text', { x: m.l - 6, y: y(t) + 4, 'text-anchor': 'end' }, s, t + '%'); });
        var lastSolid = -1; M.q.forEach(function (q, i) { if (!M.low[i]) lastSolid = i; });
        M.q.forEach(function (q, i) {
          if (!M.n_q[i]) return;
          var cx = m.l + step * (i + 0.5), acc = 0;
          M.rows.forEach(function (r, j) {
            var v = r.share[i] || 0; if (v <= 0) return;
            var yt = y(acc + v), yb = y(acc); acc += v;
            var seg = el('rect', { x: cx - bw / 2, y: yt + 1, width: bw, height: Math.max(0, yb - yt - 2), rx: 3, fill: 'var(' + MIX_COL[j] + ')', opacity: M.low[i] ? 0.4 : 1 }, s);
            V.tip.bind(seg, '<b>' + esc(r.l) + '</b> <span class="k">' + ql(q) + '</span><div class="row"><span class="k">Share of answers</span><span>' + v.toFixed(1) + '%</span></div><div class="row"><span class="k">Answers that quarter</span><span>' + fmt(M.n_q[i]) + (M.low[i] ? ' (low base)' : '') + '</span></div>');
            if (i === lastSolid && v >= 6) el('text', { x: W - m.r + 10, y: (yt + yb) / 2 + 4, fill: 'var(--v-ink2)' }, s, r.l.length > 24 ? r.l.slice(0, 23) + '…' : r.l);
          });
          el('text', { x: cx, y: H - m.b + 16, 'text-anchor': 'middle' }, s, ql(q));
          el('text', { x: cx, y: H - m.b + 30, 'text-anchor': 'middle', fill: 'var(--v-muted)' }, s, fmt(M.n_q[i]) + ' ans.');
        });
      });
      var rows = M.rows.map(function (r) { var o = { l: r.l }; M.q.forEach(function (q, i) { o[q] = r.share[i]; }); return o; });
      c.setTable([{ l: 'Food group', k: 'l' }].concat(M.q.map(function (q) { return { l: ql(q) + ' %', k: q, n: 1 }; })), rows, 'dream-menu-menu-mix-' + k);
    }
    courseChips(c, D, cur, draw); draw(cur);
  }

  // ------------------------------------------------------------------ lifecycle board (partner)
  function board(host, D) {
    var cur = 'all';
    var c = V.card(host, { id: 'tr-board', title: 'The life-cycle board: every tracked dish, sorted by the shape of its share', sub: 'Six stages, each with the tests behind it. A small sparkline shows the share in each quarter (hollow = low base). Use it to separate what is growing from what is mature or tiring.', src: src(D), fresh: ['interviews'], csv: 'dream-menu-lifecycle-board', filters: true });
    function draw(k) {
      cur = k; var list = D.life.filter(function (r) { return k === 'all' || r.course === k; });
      var wrap = h('div', 'tr-board'); c.plot.innerHTML = ''; c.plot.appendChild(wrap);
      STAGE_ORDER.forEach(function (st) {
        var items = list.filter(function (r) { return r.stage === st; }).sort(function (a, b) { return b.pct - a.pct; });
        var col = h('div', 'tr-col'); wrap.appendChild(col);
        col.appendChild(h('div', 'tr-colh', '<i style="background:var(' + STAGE_COL[st] + ')"></i><b>' + esc(st) + '</b><span>' + items.length + '</span><p>' + esc(STAGE_NOTE[st]) + '</p>'));
        if (st === 'No clear pattern') {
          col.appendChild(h('p', 'tr-quiet', items.map(function (r) { return esc(r.l) + (k === 'all' ? ' <small>' + esc(r.cl.toLowerCase()) + '</small>' : ''); }).join(' · ') || '–'));
          return;
        }
        if (!items.length) col.appendChild(h('p', 'tr-quiet', 'None this read.'));
        items.forEach(function (r) {
          var it = h('div', 'tr-item');
          it.appendChild(h('div', 'tr-ih', '<b>' + esc(r.l) + '</b><span>' + r.pct.toFixed(1) + '%</span>'));
          it.appendChild(h('div', 'tr-im', esc(r.cl) + ' · ' + (r.move >= 0 ? '+' : '−') + Math.abs(r.move).toFixed(1) + ' pts'));
          var sp = h('div', 'tr-sp'); it.appendChild(sp);
          V.spark(sp, r.share, { color: 'var(' + STAGE_COL[st] + ')', w: 150, h: 30, low: (D.mix.filter(function (m) { return m.course === r.course; })[0] || { low: [] }).low, min: 0 });
          it.appendChild(h('div', 'tr-iw', esc(r.why)));
          col.appendChild(it);
          V.tip.bind(it, '<b>' + esc(r.l) + '</b> <span class="k">' + esc(r.cl) + '</span><div class="row"><span class="k">Earlier → recent</span><span>' + r.early + '% → ' + r.late + '%</span></div><div class="row"><span class="k">Test</span><span>' + pv(r.p) + '</span></div><div class="row"><span class="k">Why</span><span>' + esc(r.why) + '</span></div>');
        });
      });
      c.setTable([{ l: 'Dish', k: 'l' }, { l: 'Course', k: 'cl' }, { l: 'Stage', k: 'stage' }, { l: 'Share %', k: 'pct', n: 1 }, { l: 'Earlier %', k: 'early', n: 1 }, { l: 'Recent %', k: 'late', n: 1 }, { l: 'Change, pts', k: 'move', n: 1 }, { l: 'p', k: 'p', n: 1 }, { l: 'Why', k: 'why' }], list, 'dream-menu-lifecycle-' + k);
    }
    V.chips(c.filters, [['all', 'All courses']].concat(D.meta.courses.map(function (x) { return [x[0], x[1] + 's']; })), cur, draw);
    draw(cur);
  }

  // ------------------------------------------------------------------ forecast fans (partner)
  function fans(host, D) {
    var list = D.fc.slice(0, 8);
    if (!list.length) return;
    var c = V.card(host, { id: 'tr-fan', title: 'Where the clear movers are heading: three quarters on recent trend', sub: 'Solid line = share so far (hollow = low base); dashed line and band = a damped projection with a planning range. A planning range, not a forecast guarantee: use it to size orders, not to promise.', src: src(D) + ' Projection: recency-weighted trend, damped 0.7 per quarter (as in the Insight Series).', fresh: ['interviews'], csv: 'dream-menu-mover-projections',
      legend: [['Clearly rising', '--v-up'], ['Clearly falling', '--v-down']] });
    var grid = h('div', 'tr-sm'); c.plot.appendChild(grid);
    list.forEach(function (r) {
      var cell = h('div', 'tr-cell'); grid.appendChild(cell);
      var col = r.move > 0 ? 'var(--v-up)' : 'var(--v-down)';
      cell.appendChild(h('p', 'tr-ct', '<b>' + esc(r.l) + '</b> <span class="tr-tag ' + (r.move > 0 ? 'up' : 'dn') + '">' + pp(r.move) + '</span>'));
      cell.appendChild(h('p', 'tr-cs', esc(r.cl) + (r.level === 'Group' ? ' · food group' : ' · dish') + ' · ' + pv(r.p)));
      var plot = h('div'); cell.appendChild(plot);
      V.responsive(plot, function (W) {
        var H = 160, m = { t: 10, b: 22, l: 30, r: 8 }, s = V.svg(plot, W, H, r.l + ' projection');
        var labs = r.q.concat(r.fq), N = labs.length;
        var vmax = Math.max.apply(null, r.share.filter(function (v) { return v !== null; }).concat(r.f.map(function (f) { return f[2]; })));
        var top = vmax * 1.1 > 10 ? Math.ceil(vmax * 1.1 / 10) * 10 : 10;
        var x = lin(0, N - 1, m.l + 4, W - m.r - 4), y = lin(0, top, H - m.b, m.t), g = el('g', { class: 'dmv-grid' }, s);
        [0, top / 2, top].forEach(function (t) { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); el('text', { x: m.l - 5, y: y(t) + 4, 'text-anchor': 'end' }, s, Math.round(t) + '%'); });
        el('rect', { x: x(r.anchor), y: m.t, width: x(N - 1) - x(r.anchor), height: H - m.t - m.b, fill: 'var(--v-plane)' }, s);
        var a = r.share[r.anchor], up = 'M' + x(r.anchor) + ' ' + y(a), dn = '';
        r.f.forEach(function (f, j) { up += 'L' + x(r.anchor + j + 1) + ' ' + y(f[2]); });
        for (var j = r.f.length - 1; j >= 0; j--) dn += 'L' + x(r.anchor + j + 1) + ' ' + y(r.f[j][1]);
        el('path', { d: up + dn + 'L' + x(r.anchor) + ' ' + y(a) + 'Z', fill: col, opacity: 0.14 }, s);
        var d = ''; r.share.forEach(function (v, i) { if (v === null || r.low[i] && i > r.anchor) return; d += (d ? 'L' : 'M') + x(i) + ' ' + y(v); });
        el('path', { d: d, fill: 'none', stroke: col, 'stroke-width': 2, 'stroke-linejoin': 'round' }, s);
        var fd = 'M' + x(r.anchor) + ' ' + y(a); r.f.forEach(function (f, j) { fd += 'L' + x(r.anchor + j + 1) + ' ' + y(f[0]); });
        el('path', { d: fd, fill: 'none', stroke: col, 'stroke-width': 2, 'stroke-dasharray': '5 4' }, s);
        r.share.forEach(function (v, i) { if (v === null) return; el('circle', { cx: x(i), cy: y(v), r: 3.5, fill: r.low[i] ? 'var(--v-surface)' : col, stroke: col, 'stroke-width': 1.8 }, s); });
        [0, r.anchor, N - 1].forEach(function (i) { el('text', { x: x(i), y: H - 6, 'text-anchor': i === 0 ? 'start' : i === N - 1 ? 'end' : 'middle' }, s, ql(labs[i])); });
        var last = r.f[r.f.length - 1];
        var hit = el('rect', { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent' }, s);
        V.tip.bind(hit, '<b>' + esc(r.l) + '</b><div class="row"><span class="k">Latest full quarter</span><span>' + a + '% (' + ql(r.q[r.anchor]) + ')</span></div>' + r.f.map(function (f, j) { return '<div class="row"><span class="k">' + ql(r.fq[j]) + '</span><span>' + f[0] + '% (' + f[1] + '–' + f[2] + ')</span></div>'; }).join('') + '<div class="row"><span class="k">Earlier → recent</span><span>' + pp(r.move) + '</span></div>');
        void last;
      });
    });
    var rows = list.map(function (r) { var o = { l: r.l, cl: r.cl, level: r.level, move: r.move, p: r.p, last: r.share[r.anchor], lq: ql(r.q[r.anchor]) }; r.fq.forEach(function (q, j) { o[q] = r.f[j][0]; o[q + 'lo'] = r.f[j][1]; o[q + 'hi'] = r.f[j][2]; }); return o; });
    var cols = [{ l: 'Dish or group', k: 'l' }, { l: 'Course', k: 'cl' }, { l: 'Level', k: 'level' }, { l: 'Change, pts', k: 'move', n: 1 }, { l: 'Latest full quarter', k: 'lq' }, { l: 'Share then %', k: 'last', n: 1 }];
    list[0].fq.forEach(function (q) { cols.push({ l: ql(q) + ' %', k: q, n: 1 }, { l: ql(q) + ' low', k: q + 'lo', n: 1 }, { l: ql(q) + ' high', k: q + 'hi', n: 1 }); });
    c.setTable(cols, rows);
  }


  // ------------------------------------------------------------------ how Dream Menu compares (benchmarks)
  var VERD = { agrees: ['Agrees', '--v-s3', '<path d="M4.5 8.3 7 10.8l4.6-5.1" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'],
    differs: ['Challenges', '--v-s2', '<path d="M4 6.2h8M4 9.8h8M10.2 3.8 5.8 12.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'],
    context: ['Context', '--v-ns', '<circle cx="8" cy="4.6" r="1.1" fill="currentColor"/><path d="M8 7.2v5" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>'] };
  function vchip(v) { var x = VERD[v]; return '<span class="bm-v bm-' + v + '"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">' + x[2] + '</svg>' + x[0] + '</span>'; }
  var ARR = { up: '<svg viewBox="0 0 16 16" width="16" height="16" aria-label="rising" role="img"><path d="M8 13V3M3.8 7.2 8 3l4.2 4.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    down: '<svg viewBox="0 0 16 16" width="16" height="16" aria-label="falling" role="img"><path d="M8 3v10M3.8 8.8 8 13l4.2-4.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    flat: '<svg viewBox="0 0 16 16" width="16" height="16" aria-label="steady" role="img"><path d="M3 8h10M9.5 4.5 13 8l-3.5 3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' };
  function bench(host, D, partner) {
    var items = D.items;
    var c = V.card(host, { id: 'bm-board', title: 'Where outside sources agree with Dream Menu, and where they challenge it', sub: esc(D.meta.note), src: 'Outside sources as linked on each comparison. Dream Menu: ' + fmt(D.meta.n_all) + ' interviews to ' + (window.DM_FRESH ? window.DM_FRESH.fmt(D.meta.last) : D.meta.last) + '.', fresh: ['interviews'], csv: 'dream-menu-benchmarks', filters: true });
    var themes = ['All'].concat(items.map(function (b) { return b.theme; }).filter(function (t, i, a) { return a.indexOf(t) === i; }));
    function draw(th) {
      var list = items.filter(function (b) { return th === 'All' || b.theme === th; });
      var o = '<div class="bm-sum">';
      ['agrees', 'differs', 'context'].forEach(function (v) {
        var xs = list.filter(function (b) { return b.verdict === v; });
        o += '<div class="bm-col"><div class="bm-colh">' + vchip(v) + '<b>' + xs.length + '</b></div>' + (xs.length ? xs.map(function (b) {
          var dir = b.kind === 'direction' ? '<span class="bm-dirs"><span title="Dream Menu" class="bm-dm">' + ARR[b.dm.dir] + '</span><span title="Outside source" class="bm-ex">' + ARR[b.ext.dir] + '</span></span>' : b.kind === 'level' ? '<span class="bm-lv">' + b.dm.v + '% · ' + b.ext.v + '%</span>' : '';
          return '<a class="bm-pill" href="#bm-' + b.id + '">' + esc(b.topic) + dir + '</a>';
        }).join('') : '<p class="tr-quiet">None in this theme.</p>') + '</div>';
      });
      o += '</div><p class="bm-key"><span class="bm-dm">' + ARR.up + '</span> Dream Menu &nbsp; <span class="bm-ex">' + ARR.up + '</span> outside source &nbsp; · &nbsp; level comparisons show Dream Menu first</p><div class="bm-grid">';
      list.forEach(function (b) {
        o += '<article class="bm-card" id="bm-' + b.id + '"><header><h4>' + esc(b.topic) + '</h4>' + vchip(b.verdict) + '</header>';
        if (b.kind === 'level') {
          o += '<div class="bm-bars"><div><span>Dream Menu</span><i style="width:' + b.dm.v + '%" class="bm-dmbar"></i><b>' + b.dm.v + '%</b></div><div><span>Outside</span><i style="width:' + b.ext.v + '%" class="bm-exbar"></i><b>' + b.ext.v + '%</b></div></div>';
        }
        o += '<dl><dt><span class="bm-dm">' + (b.dm.dir ? ARR[b.dm.dir] : '●') + '</span>Dream Menu</dt><dd>' + esc(b.dm.text) + ' <small>' + esc(b.dm.base) + '</small></dd>' +
          '<dt><span class="bm-ex">' + (b.ext.dir ? ARR[b.ext.dir] : '●') + '</span>Outside</dt><dd>' + esc(b.ext.text) + ' <small><a href="' + esc(b.ext.url) + '" rel="noopener" target="_blank">' + esc(b.ext.who) + ', ' + esc(b.ext.date) + '</a></small>' + (b.extra ? '<br><small>' + esc(b.extra) + '</small>' : '') + '</dd></dl>' +
          '<p class="bm-read"><b>What it means</b>' + esc(b.read) + '</p></article>';
      });
      c.plot.innerHTML = o + '</div>';
      c.setTable([{ l: 'Topic', k: 'topic' }, { l: 'Theme', k: 'theme' }, { l: 'Verdict', f: function (b) { return VERD[b.verdict][0]; } }, { l: 'Dream Menu', f: function (b) { return b.dm.text; } }, { l: 'Outside source figure', f: function (b) { return b.ext.text; } }, { l: 'Source', f: function (b) { return b.ext.who + ', ' + b.ext.date; } }, { l: 'Link', f: function (b) { return b.ext.url; } }, { l: 'What it means', k: 'read' }], list, 'dream-menu-benchmarks');
    }
    V.chips(c.filters, themes.map(function (t) { return [t, t]; }), 'All', draw); draw('All');
  }

  function start() {
    var P = window.DM_TRENDP, X = window.DM_TRENDX, g = function (id) { return document.getElementById(id); };
    if (X || window.DM_INTEL) document.documentElement.classList.add('dm-partner');
    var F = X || P;
    if (F && g('th-find')) findings(g('th-find'), F);
    if (P && g('th-churn')) { churn(g('th-churn'), P); if (X) flows(g('th-churn'), X); }
    if (P && g('th-conc')) { conc(g('th-conc'), P); if (X) mix(g('th-conc'), X); }
    if (P && g('th-life')) { stageBar(g('th-life'), P); staples(g('th-life'), P); if (X) { board(g('th-life'), X); slope(g('th-life'), X); } }
    if (X && g('th-fan')) fans(g('th-fan'), X);
    var BX = window.DM_BENCHX, BP = window.DM_BENCHP;
    if ((BX || BP) && g('th-bench')) bench(g('th-bench'), BX || BP, !!BX);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();

  window.DMT = { bench: bench, findings: findings, churn: churn, conc: conc, stageBar: stageBar, staples: staples, flows: flows, slope: slope, mix: mix, board: board, fans: fans, wrapText: wrapText };
})();
