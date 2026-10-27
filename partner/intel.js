/* partner/intel.js: draws /intelligence from partner/intel-data.js (both behind partner sign-in). */
(function () {
  'use strict';
  function start() {
  var I = window.DM_INTEL, V = window.DMV;
  if (!I || !V || !window.DM_FRESH) return;
  var el = V.el, h = V.h, esc = V.esc, lin = V.lin, fmt = V.fmt, pp = V.pp;
  var COURSES = [['s', 'Starter'], ['m', 'Main'], ['d', 'Side'], ['p', 'Dessert'], ['a', 'Alcoholic drink'], ['k', 'Soft drink']];
  var CL = {}; COURSES.forEach(function (c) { CL[c[0]] = c[1]; });
  var SRC = 'Source: Dream Menu interviews, ' + fmt(I.kpi.n) + ' answering the dish questions, 1 Sep 2025 to ' + window.DM_FRESH.fmt(I.kpi.last) + '. Earlier = ' + I.method.early.join(' and ') + '; recent = ' + I.method.late.join(', ') + '. Clear = two-proportion z-test, p < 0.05.';
  var $ = function (s) { return document.querySelector(s); };
  var setT = function (id, html) { var n = document.getElementById(id); if (n) n.innerHTML = html; };
  function colOf(r) { return r.sig ? (r.move > 0 ? 'var(--v-up)' : 'var(--v-down)') : 'var(--v-ns)'; }
  var PROPER = /\b(mediterranean|middle eastern|scottish|british|asian|indian|italian|mexican|latin|japanese|sunday|new york|irn bru|coke|aperol|guinness)\b/gi;
  function lc(s) { return String(s).toLowerCase().replace(PROPER, function (w) { return w.replace(/\b\w/g, function (c) { return c.toUpperCase(); }); }).replace(/\bnew York\b/, 'New York'); }
  function pv(p) { return p < 0.001 ? 'p < 0.001' : 'p = ' + p.toFixed(3); }

  // =================================================================== 1. executive read
  (function exec() {
    var k = I.kpi, o = I.ops;
    var host = $('#x-kpis'); if (!host) return;
    var iq = k.interviews_q;
    host.innerHTML =
      '<div class="kpi hero"><span class="lab">Clear movers this read</span><span class="val">' + k.sig + '<small>of ' + k.tests + ' tested</small></span><span class="del">' + k.up + ' rising, ' + k.down + ' falling, each passing p &lt; 0.05</span></div>' +
      '<div class="kpi"><span class="lab">Interviews by quarter</span><span class="val">' + fmt(k.n_all) + '</span><span class="del">' + iq[iq.length - 2] + ' in ' + k.quarters[k.quarters.length - 2] + '; ' + iq[iq.length - 1] + ' so far in ' + k.quarters[k.quarters.length - 1] + '</span><div class="kspark"></div></div>' +
      '<div class="kpi"><span class="lab">Operator confidence, next 3 months</span><span class="val">' + o.conf3.toFixed(1) + '<small>/10</small></span><span class="del down">' + o.conf12.toFixed(1) + ' looking 12 months out</span></div>' +
      '<div class="kpi"><span class="lab">Operators seeing supplier prices rise</span><span class="val">' + o.rising + '<small>%</small></span><span class="del">of ' + o.n + ' surveyed in the 2026 Look Ahead</span></div>';
    V.spark(host.querySelector('.kspark'), iq, { color: 'var(--v-brand)', area: true, low: iq.map(function (n) { return n < 100; }) });
    var up = I.ci.filter(function (r) { return r.sig && r.move > 0; }).sort(function (a, b) { return b.move - a.move; });
    var dn = I.ci.filter(function (r) { return r.sig && r.move < 0; }).sort(function (a, b) { return a.move - b.move; });
    var side = I.ci.filter(function (r) { return r.course === 'd' && r.sig; });
    var upD = up.filter(function (r) { return r.level === 'Dish'; }), dnD = dn.filter(function (r) { return r.level === 'Dish'; });
    var best = I.opp[0];
    $('#x-sowhat').innerHTML =
      '<div><b>Back</b><p><strong>' + esc(up[0].l) + '</strong> is the strongest riser (' + pp(up[0].move) + ' in ' + up[0].cl.toLowerCase() + 's, ' + pv(up[0].p) + '), led by <strong>' + esc(lc(upD[0].l)) + '</strong> (' + pp(upD[0].move) + '). Top of the opportunity score: <strong>' + esc(lc(best.l)) + '</strong>.</p></div>' +
      '<div><b>Rethink</b><p><strong>' + esc(dn[0].l) + '</strong> lost the most ground (' + pp(dn[0].move) + ' of ' + dn[0].cl.toLowerCase() + ' answers), the largest clear move in the data. Still the biggest group, but no longer a default.</p></div>' +
      '<div><b>Watch</b><p>Sides are the most fluid course: <strong>' + side.length + ' clear moves</strong>. ' + esc(dn[1].l) + ' fell ' + pp(dn[1].move).replace('−', '') .replace(' pts', ' points') + ' while greens and Mediterranean sides took the space.</p></div>';
    var byC = {}; I.ci.forEach(function (r) { if (r.sig) byC[r.cl] = (byC[r.cl] || 0) + 1; });
    var hot = Object.keys(byC).sort(function (a, b) { return byC[b] - byC[a]; });
    setT('t1', hot[0] + 's and ' + hot[1].toLowerCase() + 's are where demand is moving; ' + esc(lc(dn[0].l)) + ' and ' + esc(lc(dn[1].l)) + ' are giving up the most ground');
  })();

  // =================================================================== 2. momentum matrix
  (function matrix() {
    var host = $('#c-matrix'); if (!host) return;
    var cur = 'd';
    var c = V.card(host, { id: 'matrix', title: 'Share of answers against change in share, every tracked dish', sub: 'Bubble size = answers. Lines split each course at its median share and at no change.', src: SRC, fresh: ['interviews'], csv: 'dream-menu-momentum-matrix',
      legend: [['Clear rise', '--v-up'], ['Clear fall', '--v-down'], ['Not a clear move', '--v-ns']] });
    V.chips(c.filters, [['all', 'All courses']].concat(COURSES), cur, function (v) { cur = v; redraw(); });
    var redraw = V.responsive(c.plot, draw);
    function draw(W) {
      var pts = I.momentum.filter(function (r) { return cur === 'all' || r.course === cur; });
      var mob = W < 560, H = mob ? 370 : 450, m = { l: 44, r: 16, t: 34, b: 40 };
      var s = V.svg(c.plot, W, H, 'Momentum matrix');
      var xmax = Math.max.apply(null, pts.map(function (p) { return p.pct; })) * 1.12;
      var ym = Math.max.apply(null, pts.map(function (p) { return Math.abs(p.move); })) * 1.15;
      var xn = V.nice(0, xmax, mob ? 4 : 6), yn = V.nice(-ym, ym, 6);
      var x = lin(0, xn.hi, m.l, W - m.r), y = lin(yn.lo, yn.hi, H - m.b, m.t);
      var g = el('g', { class: 'dmv-grid' }, s);
      yn.ticks.forEach(function (t) { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); el('text', { x: m.l - 8, y: y(t) + 4, 'text-anchor': 'end', class: 't-num' }, s, (t > 0 ? '+' : '') + t); });
      xn.ticks.forEach(function (t) { el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle', class: 't-num' }, s, t + '%'); });
      el('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: 'dmv-axis' }, s);
      var med = cur === 'all' ? median(pts.map(function (p) { return p.pct; })) : pts[0].med;
      el('line', { x1: x(med), x2: x(med), y1: m.t, y2: H - m.b, class: 'dmv-axis' }, s);
      el('text', { x: m.l, y: H - 6, class: 't-ink2' }, s, 'Share of the course’s answers →');
      el('text', { x: 0, y: 12, class: 't-ink2' }, s, '↑ Change in share, points');
      var q = [[W - m.r - 6, m.t + 14, 'end', 'CORE AND GROWING'], [m.l + 6, m.t + 14, 'start', 'EMERGING'], [W - m.r - 6, H - m.b - 8, 'end', 'CORE BUT SOFTENING'], [m.l + 6, H - m.b - 8, 'start', 'FADING']];
      q.forEach(function (a) { el('text', { x: a[0], y: a[1], 'text-anchor': a[2], class: 't-b', 'letter-spacing': mob ? '.03em' : '.08em', 'font-size': mob ? '9' : '10.5', opacity: .7 }, s, a[3]); });
      var rmax = Math.max.apply(null, pts.map(function (p) { return p.n; }));
      var r = function (n) { return 4 + Math.sqrt(n / rmax) * (mob ? 12 : 17); };
      pts.sort(function (a, b) { return b.n - a.n; });
      var placed = [];
      pts.forEach(function (p) {
        var gg = el('g', {}, s);
        el('circle', { cx: x(p.pct), cy: y(p.move), r: r(p.n), fill: colOf(p), 'fill-opacity': p.sig ? .85 : .45, stroke: 'var(--v-ring)', 'stroke-width': 2, class: 'dmv-mark' }, gg);
        V.tip.bind(gg, '<b>' + esc(p.l) + '</b> <span class="k">' + esc(p.cl) + '</span><div class="row"><span class="k">Share</span><span>' + p.pct.toFixed(1) + '% (' + p.n + ' answers)</span></div><div class="row"><span class="k">Change</span><span>' + pp(p.move) + '</span></div><div class="row"><span class="k">Test</span><span>' + pv(p.p) + (p.sig ? ', clear' : ', not clear') + '</span></div>');
      });
      // selective labels: clear movers, then the biggest dishes, avoiding overlaps
      var want = pts.filter(function (p) { return p.sig; }).concat(pts.slice(0, mob ? 3 : 6));
      var seen = {};
      want.forEach(function (p) {
        if (seen[p.l + p.course]) return; seen[p.l + p.course] = 1;
        var txt = p.l.length > 28 ? p.l.slice(0, 27) + '…' : p.l;
        var tw = txt.length * 6.1, cx = x(p.pct), cy = y(p.move), rr = r(p.n);
        var right = cx + rr + 4 + tw < W - m.r;
        var bx = right ? cx + rr + 4 : cx - rr - 4 - tw, by = cy - 6;
        var box = [bx, by, bx + tw, by + 13];
        for (var i = 0; i < placed.length; i++) { var b = placed[i]; if (box[0] < b[2] && box[2] > b[0] && box[1] < b[3] && box[3] > b[1]) return; }
        placed.push(box);
        el('text', { x: right ? bx : bx + tw, y: cy + 4, 'text-anchor': right ? 'start' : 'end', class: 't-ink', 'font-weight': p.sig ? 700 : 500 }, s, txt);
      });
      c.setTable([{ l: 'Dish', k: 'l' }, { l: 'Course', k: 'cl' }, { l: 'Share %', k: 'pct', n: 1 }, { l: 'Change, pts', f: function (r) { return (r.move > 0 ? '+' : '') + r.move.toFixed(1); }, n: 1 }, { l: 'p', f: function (r) { return r.p.toFixed(3); }, n: 1 }, { l: 'Clear move', f: function (r) { return r.sig ? 'Yes' : 'No'; } }, { l: 'Quadrant', f: function (r) { return { 'core-up': 'Core and growing', 'core-down': 'Core but softening', emerging: 'Emerging', fading: 'Fading' }[r.quad]; } }], pts.slice().sort(function (a, b) { return b.move - a.move; }));
    }
    var em = I.momentum.filter(function (r) { return r.quad === 'emerging' && r.sig; });
    var ems = em.map(function (r) { return esc(lc(r.l)); }).slice(0, 3);
    setT('t2', ems.length ? 'Growth is coming from the edges: ' + (ems.length > 1 ? ems.slice(0, -1).join(', ') + ' and ' + ems[ems.length - 1] : ems[0]) + (ems.length > 1 ? ' are' : ' is') + ' still small, but rising clearly' : 'Where each dish sits on size and momentum');
  })();
  function median(a) { a = a.slice().sort(function (x, y) { return x - y; }); var n = a.length; return n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2; }

  // =================================================================== 3. forest plot
  (function forest() {
    var host = $('#c-forest'); if (!host) return;
    var mode = 'sig';
    var c = V.card(host, { id: 'confidence', title: 'Change in share with its 95% range: a line that crosses zero is not a clear move', sub: 'Dot = best estimate of the change from earlier to recent quarters. Line = the range the true change very likely sits in.', src: SRC + ' Ranges use the standard error behind each test.', fresh: ['interviews'], csv: 'dream-menu-movers-with-ranges',
      legend: [['Clear rise', '--v-up'], ['Clear fall', '--v-down'], ['Not a clear move', '--v-ns']] });
    V.chips(c.filters, [['sig', 'Clear movers'], ['big', 'Largest 30 dishes and groups'], ['near', 'Near misses']], mode, function (v) { mode = v; redraw(); });
    var redraw = V.responsive(c.plot, draw);
    function rows() {
      var all = I.ci.slice();
      if (mode === 'sig') return all.filter(function (r) { return r.sig; }).sort(function (a, b) { return b.move - a.move; });
      if (mode === 'near') return all.filter(function (r) { return !r.sig && r.p < 0.2; }).sort(function (a, b) { return b.move - a.move; });
      return all.sort(function (a, b) { return b.n - a.n; }).slice(0, 30).sort(function (a, b) { return b.move - a.move; });
    }
    function draw(W) {
      var R = rows(), mob = W < 560, lw = mob ? 132 : 300, rh = 26, m = { t: 26, b: 30, r: mob ? 12 : 70 };
      var H = m.t + R.length * rh + m.b;
      var s = V.svg(c.plot, W, H, 'Change in share with 95% ranges');
      var lo = Math.min.apply(null, R.map(function (r) { return r.lo; })), hi = Math.max.apply(null, R.map(function (r) { return r.hi; }));
      var n = V.nice(Math.min(lo, -1), Math.max(hi, 1), mob ? 4 : 7);
      var x = lin(n.lo, n.hi, lw, W - m.r);
      var g = el('g', { class: 'dmv-grid' }, s);
      n.ticks.forEach(function (t) { el('line', { x1: x(t), x2: x(t), y1: m.t - 6, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle', class: 't-num' }, s, (t > 0 ? '+' : '') + t); });
      el('line', { x1: x(0), x2: x(0), y1: m.t - 10, y2: H - m.b, stroke: 'var(--v-ink2)', 'stroke-width': 1.5 }, s);
      el('text', { x: x(0), y: m.t - 14, 'text-anchor': 'middle', class: 't-ink2', 'font-size': 11 }, s, 'no change');
      R.forEach(function (r, i) {
        var yy = m.t + i * rh + rh / 2, gg = el('g', {}, s), col = colOf(r);
        if (i % 2 === 0) el('rect', { x: 0, y: yy - rh / 2, width: W, height: rh, fill: 'var(--v-plane)', opacity: .55 }, gg);
        var cw = mob ? 0 : (r.cl + (r.level === 'Group' ? ' · group' : '')).length * 5.9 + 18;
        var maxc = Math.floor((lw - 8 - cw) / 6.6);
        var lab = r.l.length > maxc ? r.l.slice(0, maxc - 1) + '…' : r.l;
        el('text', { x: 0, y: yy - (mob ? 1 : 0) + 4, class: 't-ink', 'font-weight': 600 }, gg, lab);
        if (!mob) el('text', { x: lw - 12, y: yy + 4, 'text-anchor': 'end', 'font-size': 11 }, gg, r.cl + (r.level === 'Group' ? ' · group' : ''));
        el('line', { x1: x(r.lo), x2: x(r.hi), y1: yy, y2: yy, stroke: col, 'stroke-width': 2, 'stroke-linecap': 'round' }, gg);
        el('circle', { cx: x(r.move), cy: yy, r: 5, fill: col, stroke: 'var(--v-ring)', 'stroke-width': 2, class: 'dmv-mark' }, gg);
        if (!mob) el('text', { x: W - m.r + 8, y: yy + 4, class: 't-ink t-num', 'font-weight': 700 }, gg, (r.move > 0 ? '+' : '') + r.move.toFixed(1));
        V.tip.bind(gg, '<b>' + esc(r.l) + '</b> <span class="k">' + esc(r.cl) + ' · ' + r.level.toLowerCase() + '</span><div class="row"><span class="k">Earlier</span><span>' + r.early.toFixed(1) + '% of ' + fmt(r.n1) + '</span></div><div class="row"><span class="k">Recent</span><span>' + r.late.toFixed(1) + '% of ' + fmt(r.n2) + '</span></div><div class="row"><span class="k">Change</span><span>' + pp(r.move) + '</span></div><div class="row"><span class="k">95% range</span><span>' + (r.lo > 0 ? '+' : '') + r.lo.toFixed(1) + ' to ' + (r.hi > 0 ? '+' : '') + r.hi.toFixed(1) + '</span></div><div class="row"><span class="k">Test</span><span>' + pv(r.p) + '</span></div>');
      });
      c.setTable([{ l: 'Dish or group', k: 'l' }, { l: 'Course', k: 'cl' }, { l: 'Level', k: 'level' }, { l: 'Earlier %', k: 'early', n: 1 }, { l: 'Recent %', k: 'late', n: 1 }, { l: 'Change, pts', f: function (r) { return r.move.toFixed(1); }, n: 1 }, { l: 'Range low', f: function (r) { return r.lo.toFixed(1); }, n: 1 }, { l: 'Range high', f: function (r) { return r.hi.toFixed(1); }, n: 1 }, { l: 'p', f: function (r) { return r.p.toFixed(3); }, n: 1 }], R);
    }
    var widest = I.ci.filter(function (r) { return r.sig; }).sort(function (a, b) { return (a.hi - a.lo) - (b.hi - b.lo); });
    var tight = widest[0];
    setT('t3', I.kpi.sig + ' of ' + I.kpi.tests + ' moves clear the bar. The rest are noise until the sample grows, so do not plan around them');
    setT('s3', 'Most charts of “trends” show every wiggle. This one shows how sure we are. The tightest clear result is <b>' + esc(lc(tight.l)) + '</b> (' + pp(tight.move) + ', range ' + tight.lo.toFixed(1) + ' to ' + tight.hi.toFixed(1) + '). Use the <b>Near misses</b> view as the watch list for next quarter.');
  })();

  // =================================================================== 4. trend wall
  (function wallChart() {
    var host = $('#c-wall'); if (!host) return;
    var c = V.card(host, { id: 'trend-wall', title: 'The top six groups in every course, six quarters each', sub: 'Shaded = the recent quarters used for the test. Open dots = quarters with fewer than ' + I.method.min_n + ' answers. A coloured frame marks a clear move.', src: SRC, fresh: ['interviews'], csv: 'dream-menu-trend-wall',
      legend: [['Clear rise', '--v-up', 'sq'], ['Clear fall', '--v-down', 'sq']] });
    var out = '', rows = [];
    I.wall.forEach(function (w) {
      out += '<div class="wall-row"><h4>' + esc(w.cl) + '<small>' + fmt(w.n_q.reduce(function (a, b) { return a + b; }, 0)) + ' answers</small></h4><div class="wall">';
      w.items.forEach(function (it, i) {
        var cls = it.sig ? (it.move > 0 ? 'sig-up' : 'sig-down') : '';
        out += '<div class="cell ' + cls + '" data-w="' + w.course + '" data-i="' + i + '"><div class="cl">' + esc(it.l) + '</div><div class="cv">' + it.pct.toFixed(1) + '%<span class="' + (it.sig ? (it.move > 0 ? 'up' : 'down') : '') + '">' + (it.move > 0 ? '▲ ' : it.move < 0 ? '▼ ' : '') + Math.abs(it.move).toFixed(1) + '</span></div><div class="sp"></div></div>';
        rows.push({ c: w.cl, l: it.l, pct: it.pct, early: it.early, late: it.late, move: it.move, p: it.p, share: it.share, q: w.q });
      });
      out += '</div></div>';
    });
    c.plot.innerHTML = out;
    c.plot.querySelectorAll('.cell').forEach(function (cell) {
      var w = I.wall.filter(function (x) { return x.course === cell.getAttribute('data-w'); })[0], it = w.items[+cell.getAttribute('data-i')];
      var lateStart = w.q.indexOf(I.method.late[0]);
      var col = it.sig ? (it.move > 0 ? 'var(--v-up)' : 'var(--v-down)') : 'var(--v-ink2)';
      V.spark(cell.querySelector('.sp'), it.share, { color: col, band: [lateStart - 0.5, w.q.length - 0.5], low: w.low, w: 160, h: 46 });
      V.tip.bind(cell, function () { return '<b>' + esc(it.l) + '</b> <span class="k">' + esc(w.cl) + '</span>' + w.q.map(function (q, i) { return '<div class="row"><span class="k">' + q + (w.low[i] ? ' (small)' : '') + '</span><span>' + (it.share[i] === null ? '–' : it.share[i].toFixed(1) + '%') + '</span></div>'; }).join('') + '<div class="row"><span class="k">Change</span><span>' + pp(it.move) + ', ' + pv(it.p) + '</span></div>'; });
    });
    var q = I.wall[0].q;
    c.setTable([{ l: 'Group', k: 'l' }, { l: 'Course', k: 'c' }].concat(q.map(function (qq, i) { return { l: qq + ' %', f: function (r) { return r.share[i] === null ? '' : r.share[i].toFixed(1); }, n: 1 }; })).concat([{ l: 'Change, pts', f: function (r) { return r.move.toFixed(1); }, n: 1 }, { l: 'p', f: function (r) { return r.p.toFixed(3); }, n: 1 }]), rows);
    var dr = I.wall.slice().sort(function (p, q) { return q.items.filter(function (i) { return i.sig; }).length - p.items.filter(function (i) { return i.sig; }).length; })[0];
    var ups = dr.items.filter(function (i) { return i.sig && i.move > 0; }).sort(function (p, q) { return q.move - p.move; }).slice(0, 1).map(function (i) { return lc(i.l); });
    var dns = dr.items.filter(function (i) { return i.sig && i.move < 0; }).sort(function (p, q) { return p.move - q.move; }).slice(0, 1).map(function (i) { return lc(i.l); });
    setT('t4', dr.cl + 's have reshaped the most' + (dns.length ? ': out of ' + esc(dns[0]) : '') + (ups.length ? ', into ' + esc(ups[0]) : ''));
  })();

  // =================================================================== 5. dish heat
  (function heatChart() {
    var host = $('#c-heat'); if (!host) return;
    var cur = 'd';
    var c = V.card(host, { id: 'dish-heat', title: 'Each dish’s share by quarter, against its own average', sub: 'Blue = above the dish’s own average that quarter, red = below. The number is the share of answers. Hatched columns have fewer than ' + I.method.min_n + ' answers.', src: SRC, fresh: ['interviews'], csv: 'dream-menu-dish-heat' });
    V.chips(c.filters, COURSES, cur, function (v) { cur = v; draw(); });
    var sc = h('div', 'scale', 'Below average <i style="background:var(--v-r3)"></i><i style="background:var(--v-r2)"></i><i style="background:var(--v-r1)"></i><i style="background:var(--v-d0)"></i><i style="background:var(--v-d1)"></i><i style="background:var(--v-d2)"></i><i style="background:var(--v-d3)"></i> Above average');
    c.el.insertBefore(sc, c.plot);
    function bucket(v) {
      if (v === null) return ['transparent', ''];
      if (v < 70) return ['var(--v-r3)', 'b-r3']; if (v < 85) return ['var(--v-r2)', 'b-r2']; if (v < 95) return ['var(--v-r1)', 'b-r1'];
      if (v <= 105) return ['var(--v-d0)', 'b-d0']; if (v <= 125) return ['var(--v-d1)', 'b-d1']; if (v <= 150) return ['var(--v-d2)', 'b-d2']; return ['var(--v-d3)', 'b-d3'];
    }
    function draw() {
      var hd = I.heat.filter(function (x) { return x.course === cur; })[0];
      var cols = 'minmax(120px,1.6fr) ' + hd.q.map(function () { return 'minmax(52px,1fr)'; }).join(' ');
      var o = '<div class="heat-scroll"><div class="heat" style="grid-template-columns:' + cols + '"><div></div>' + hd.q.map(function (q, i) { return '<div class="hh' + (hd.low[i] ? ' low' : '') + '">' + q.replace('20', '’') + '<br><span style="font-weight:400">n=' + hd.n_q[i] + '</span></div>'; }).join('');
      hd.rows.forEach(function (r, ri) {
        o += '<div class="hl" title="' + esc(r.l) + '">' + esc(r.l) + '</div>';
        r.share.forEach(function (v, i) {
          var b = bucket(r.idx[i]);
          o += '<div class="hc ' + b[1] + (hd.low[i] ? ' low' : '') + '" style="background-color:' + b[0] + '" data-r="' + ri + '" data-i="' + i + '">' + (v === null ? '–' : v.toFixed(1)) + '</div>';
        });
      });
      c.plot.innerHTML = o + '</div></div>';
      c.plot.querySelectorAll('.hc').forEach(function (cell) {
        var r = hd.rows[+cell.getAttribute('data-r')], i = +cell.getAttribute('data-i');
        V.tip.bind(cell, '<b>' + esc(r.l) + '</b> <span class="k">' + hd.q[i] + '</span><div class="row"><span class="k">Share</span><span>' + (r.share[i] === null ? '–' : r.share[i].toFixed(1) + '%') + '</span></div><div class="row"><span class="k">Index vs own average</span><span>' + (r.idx[i] === null ? '–' : r.idx[i]) + '</span></div><div class="row"><span class="k">Answers that quarter</span><span>' + hd.n_q[i] + (hd.low[i] ? ' (small)' : '') + '</span></div>');
      });
      c.setTable([{ l: 'Dish', k: 'l' }].concat(hd.q.map(function (q, i) { return { l: q + ' %', f: function (r) { return r.share[i] === null ? '' : r.share[i].toFixed(1); }, n: 1 }; })).concat([{ l: 'Average %', k: 'avg', n: 1 }]), hd.rows, 'dream-menu-dish-heat-' + hd.cl.toLowerCase().replace(/ /g, '-'));
    }
    draw();
    var lead = I.heat.map(function (hd) { return hd.rows[0]; }).filter(function (r) { return !r.sig; }).length;
    setT('t5', 'At dish level the leaders hold: the top dish in ' + lead + ' of ' + I.heat.length + ' courses shows no clear move. The change happens in the second tier');
  })();

  // =================================================================== 6. segments
  (function segChart() {
    var host = $('#c-seg'); if (!host) return;
    var S = I.seg, mode = 'groups';
    var COL = ['--v-s1', '--v-s2', '--v-s3'], SHAPE = ['circle', 'square', 'diamond'];
    var c = V.card(host, { id: 'segments', title: 'Share of all dish and drink answers, by who is answering', sub: 'Each group’s top six. An open marker means the item is outside that group’s top six, so its share is below the value shown.', src: 'Source: Dream Menu interviews, ' + S.segs.map(function (s) { return s.g + ' ' + fmt(s.n); }).join(', ') + '. Respondent group from the guest’s own description of their page.', fresh: ['interviews'], csv: 'dream-menu-segments',
      legend: S.segs.map(function (s, i) { return [s.g + ' (' + s.share + '%)', COL[i], i === 1 ? 'sq' : '']; }) });
    V.chips(c.filters, [['groups', 'Food groups'], ['dishes', 'Dishes']], mode, function (v) { mode = v; redraw(); });
    var redraw = V.responsive(c.plot, draw);
    function mark(g, shape, cx, cy, col, open) {
      var a = { fill: open ? 'var(--v-surface)' : 'var(' + col + ')', stroke: open ? 'var(' + col + ')' : 'var(--v-ring)', 'stroke-width': 2, class: 'dmv-mark' };
      if (shape === 'circle') { a.cx = cx; a.cy = cy; a.r = 6; return el('circle', a, g); }
      if (shape === 'square') { a.x = cx - 5.5; a.y = cy - 5.5; a.width = 11; a.height = 11; a.rx = 2; return el('rect', a, g); }
      a.points = [cx, cy - 7, cx + 7, cy, cx, cy + 7, cx - 7, cy].join(' '); return el('polygon', a, g);
    }
    function draw(W) {
      var R = S[mode], mob = W < 560, lw = mob ? 120 : 210, rh = 34, m = { t: 10, b: 30, r: 20 };
      var H = m.t + R.length * rh + m.b, s = V.svg(c.plot, W, H, 'Segment comparison');
      var all = []; R.forEach(function (r) { S.segs.forEach(function (sg) { all.push(r.v[sg.g] !== null && r.v[sg.g] !== undefined ? r.v[sg.g] : r.floor[sg.g]); }); });
      var n = V.nice(Math.max(0, Math.min.apply(null, all) - 1), Math.max.apply(null, all) * 1.06, mob ? 4 : 6), x = lin(n.lo, n.hi, lw, W - m.r);
      var g = el('g', { class: 'dmv-grid' }, s);
      n.ticks.forEach(function (t) { el('line', { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 18, 'text-anchor': 'middle', class: 't-num' }, s, t + '%'); });
      R.forEach(function (r, i) {
        var yy = m.t + i * rh + rh / 2, gg = el('g', {}, s);
        el('text', { x: 0, y: yy + 4, class: 't-ink', 'font-weight': 600 }, gg, r.g.length > (mob ? 17 : 30) ? r.g.slice(0, mob ? 16 : 29) + '…' : r.g);
        var xs = S.segs.map(function (sg) { var v = r.v[sg.g]; return x(v !== null && v !== undefined ? v : r.floor[sg.g]); });
        el('line', { x1: Math.min.apply(null, xs), x2: Math.max.apply(null, xs), y1: yy, y2: yy, stroke: 'var(--v-axis)', 'stroke-width': 2 }, gg);
        S.segs.forEach(function (sg, k) { var v = r.v[sg.g]; mark(gg, SHAPE[k], xs[k], yy, COL[k], v === null || v === undefined); });
        V.tip.bind(gg, '<b>' + esc(r.g) + '</b>' + S.segs.map(function (sg) { var v = r.v[sg.g]; return '<div class="row"><span class="k">' + sg.g + '</span><span>' + (v === null || v === undefined ? 'below ' + r.floor[sg.g] + '% (not top six)' : v.toFixed(1) + '%') + '</span></div>'; }).join(''));
      });
      c.setTable([{ l: mode === 'groups' ? 'Food group' : 'Dish', k: 'g' }].concat(S.segs.map(function (sg) { return { l: sg.g + ' %', f: function (r) { var v = r.v[sg.g]; return v === null || v === undefined ? '<' + r.floor[sg.g] : v.toFixed(1); }, n: 1 }; })), R);
    }
    var pf = S.groups.filter(function (g) { return g.g === 'Potatoes and fries'; })[0], sf = S.groups.filter(function (g) { return g.g === 'Seafood'; })[0];
    setT('t6', 'The trade orders seafood, creators order chips: ' + sf.v.Industry + '% of industry answers are seafood, and ' + pf.v.Creators + '% of creator answers are potatoes and fries');
  })();

  // =================================================================== 7. opportunity scorecard
  (function opp() {
    var host = $('#c-opp'); if (!host) return;
    var filt = 'all', course = 'all';
    var PARTS = [['demand', 'Demand', '--v-brand'], ['momentum', 'Momentum', '--v-s1'], ['evidence', 'Evidence', '--v-d2'], ['room', 'Room to enter', '--v-gold']];
    var c = V.card(host, { id: 'opportunity', title: 'Opportunity score for every tracked dish and drink, out of 100', sub: 'Demand 30, momentum 35, evidence 15, room to enter 20, minus 10 if guests also want it binned. Soft drinks are left out (too few answers per quarter).', src: SRC + ' Room to enter = how much of the dish’s venue mentions go to one venue.', fresh: ['interviews', 'venues'], csv: 'dream-menu-opportunity-scores',
      legend: PARTS.map(function (p) { return [p[1], p[2], 'sq']; }) });
    var crs = [['all', 'All courses']].concat(COURSES.filter(function (x) { return x[0] !== 'k'; }));
    var f1 = h('div', 'dmv-filters'), f2 = c.filters;
    c.el.insertBefore(f1, c.filters.nextSibling);
    V.chips(f2, [['all', 'All tiers'], ['Back', 'Back'], ['Watch', 'Watch'], ['Review', 'Review']], filt, function (v) { filt = v; draw(); });
    V.chips(f1, crs, course, function (v) { course = v; draw(); });
    function draw() {
      var R = I.opp.filter(function (o) { return (filt === 'all' || o.tier === filt) && (course === 'all' || o.course === course); });
      var show = R.slice(0, 20);
      var o = '<div class="opp-scroll"><table class="opp"><thead><tr><th>#</th><th>Dish</th><th>Verdict</th><th>Score</th><th class="hide-s" style="text-align:right">Share</th><th style="text-align:right">Change</th><th class="hide-s">Where guests go for it</th></tr></thead><tbody>';
      show.forEach(function (r, i) {
        var tot = PARTS.reduce(function (a, p) { return a + r.parts[p[0]]; }, 0);
        o += '<tr data-i="' + i + '"><td class="n">' + (I.opp.indexOf(r) + 1) + '</td><td class="dish"><b>' + esc(r.l) + '</b><span>' + esc(r.cl) + (r.fatigue ? ' · also in “Bin it”' : '') + '</span></td><td>' + V.tier(r.tier) + '</td>' +
          '<td><div style="display:flex;gap:10px;align-items:center"><div class="stack" style="max-width:' + Math.max(40, tot / 100 * 240) + 'px">' + PARTS.map(function (p) { return '<i style="flex:' + r.parts[p[0]] + ';background:var(' + p[2] + ')"></i>'; }).join('') + '</div><b class="n" style="font-variant-numeric:tabular-nums">' + r.score + '</b></div></td>' +
          '<td class="n hide-s">' + r.pct.toFixed(1) + '%</td><td class="n" style="color:' + (r.sig ? (r.move > 0 ? 'var(--v-good-ink)' : 'var(--v-crit)') : 'var(--v-ink2)') + '">' + pp(r.move) + '</td><td class="hide-s">' + (r.venues ? r.venues + ' venues; ' + esc(r.topv) + ' ' + r.top + '%' : '–') + '</td></tr>';
      });
      o += '</tbody></table></div>' + (R.length > 20 ? '<p class="dmv-src" style="margin-top:8px">Showing 20 of ' + R.length + '. The table view and CSV hold every row.</p>' : '');
      c.plot.innerHTML = o;
      c.plot.querySelectorAll('tbody tr').forEach(function (tr) {
        var r = show[+tr.getAttribute('data-i')];
        V.tip.bind(tr.querySelector('.stack'), '<b>' + esc(r.l) + ': ' + r.score + '/100</b>' + PARTS.map(function (p) { return '<div class="row"><span class="k">' + p[1] + '</span><span>' + r.parts[p[0]].toFixed(1) + '</span></div>'; }).join('') + (r.fat ? '<div class="row"><span class="k">Bin it penalty</span><span>−' + r.fat + '</span></div>' : '') + '<div class="row"><span class="k">Test</span><span>' + pv(r.p) + '</span></div>');
      });
      c.setTable([{ l: 'Dish', k: 'l' }, { l: 'Course', k: 'cl' }, { l: 'Verdict', k: 'tier' }, { l: 'Score', k: 'score', n: 1 }, { l: 'Demand', f: function (r) { return r.parts.demand; }, n: 1 }, { l: 'Momentum', f: function (r) { return r.parts.momentum; }, n: 1 }, { l: 'Evidence', f: function (r) { return r.parts.evidence; }, n: 1 }, { l: 'Room to enter', f: function (r) { return r.parts.room; }, n: 1 }, { l: 'Share %', k: 'pct', n: 1 }, { l: 'Change, pts', k: 'move', n: 1 }, { l: 'p', k: 'p', n: 1 }, { l: 'Venues named', k: 'venues', n: 1 }, { l: 'Top venue', k: 'topv' }, { l: 'Top venue share %', k: 'top', n: 1 }], R);
    }
    draw();
    var back = I.opp.filter(function (o) { return o.tier === 'Back'; });
    setT('t7', back.length + ' dishes and drinks earn a “Back” verdict. ' + esc(back[0].l) + ', ' + esc(lc(back[1].l)) + ' and ' + esc(lc(back[2].l)) + ' lead the list');
  })();

  // =================================================================== 8. operators
  (function ops() {
    var o = I.ops, host = $('#c-ops'); if (!host) return;
    var SRC8 = 'Source: Dream Menu 2026 Look Ahead survey, ' + o.n + ' operators, 2 April to 3 May 2026. Respondents could pick several options, so shares add to more than 100%.';
    var wrap = h('div', 'iv-grid2'); host.appendChild(wrap);
    var a = h('div'), b = h('div'); wrap.appendChild(a); wrap.appendChild(b);
    var c1 = V.card(a, { id: 'pressure-gap', title: 'Pressure felt against the matching action taken', sub: 'Share of operators naming each pressure, beside the share who took the action that answers it most directly.', src: SRC8, fresh: ['look'], csv: 'dream-menu-pressure-vs-action',
      legend: [['Name it as a pressure', '--v-s2', 'sq'], ['Took the matching action', '--v-s1', 'sq']] });
    V.responsive(c1.plot, function (W) {
      var R = o.gap, mob = W < 520, rh = 64, m = { t: 6, b: 26, l: 0, r: 40 };
      var H = m.t + R.length * rh + m.b, s = V.svg(c1.plot, W, H, 'Pressure against action');
      var x = lin(0, 100, m.l, W - m.r);
      var g = el('g', { class: 'dmv-grid' }, s);
      [0, 25, 50, 75, 100].forEach(function (t) { el('line', { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b }, g); el('text', { x: x(t), y: H - m.b + 16, 'text-anchor': t === 0 ? 'start' : t === 100 ? 'end' : 'middle', class: 't-num' }, s, t + '%'); });
      R.forEach(function (r, i) {
        var y0 = m.t + i * rh, gg = el('g', {}, s);
        el('text', { x: 0, y: y0 + 13, class: 't-ink', 'font-weight': 700 }, gg, ({ 'Energy/utilities': 'Energy and utilities', 'Rent/rates/property costs': 'Rent, rates and property', 'Consumer demand / footfall': 'Footfall and demand' })[r.pressure] || r.pressure);
        el('path', { d: bar(x(0), y0 + 19, x(r.pv) - x(0), 12), fill: 'var(--v-s2)' }, gg);
        el('text', { x: x(r.pv) + 6, y: y0 + 29, class: 't-ink t-num', 'font-weight': 700 }, gg, r.pv + '%');
        el('path', { d: bar(x(0), y0 + 33, x(r.av) - x(0), 12), fill: 'var(--v-s1)' }, gg);
        el('text', { x: x(r.av) + 6, y: y0 + 43, class: 't-ink2 t-num' }, gg, r.av + '%');
        el('text', { x: 0, y: y0 + 58, 'font-size': 11 }, gg, '→ ' + r.action.replace(/\s*\(.*\)/, ''));
        V.tip.bind(gg, '<b>' + esc(r.pressure) + '</b><div class="row"><span class="k">Name it as a pressure</span><span>' + r.pv + '%</span></div><div class="row"><span class="k">' + esc(r.action) + '</span><span>' + r.av + '%</span></div><div class="row"><span class="k">Gap</span><span>' + (r.gap > 0 ? r.gap + ' pts unanswered' : 'action ahead of pressure') + '</span></div>');
      });
      c1.setTable([{ l: 'Pressure', k: 'pressure' }, { l: 'Name it %', k: 'pv', n: 1 }, { l: 'Matching action', k: 'action' }, { l: 'Took it %', k: 'av', n: 1 }, { l: 'Gap, pts', k: 'gap', n: 1 }], R);
    });
    function bar(x0, y0, w, hh) { w = Math.max(w, 2); var r = Math.min(4, w); return 'M' + x0 + ' ' + y0 + 'H' + (x0 + w - r) + 'Q' + (x0 + w) + ' ' + y0 + ' ' + (x0 + w) + ' ' + (y0 + r) + 'V' + (y0 + hh - r) + 'Q' + (x0 + w) + ' ' + (y0 + hh) + ' ' + (x0 + w - r) + ' ' + (y0 + hh) + 'H' + x0 + 'Z'; }

    var c2 = V.card(b, { id: 'trade-call', title: 'How operators call the next few months, and how this year compares', sub: 'Each bar is all answers. Worse to the left of the line, better to the right.', src: SRC8.replace(' Respondents could pick several options, so shares add to more than 100%.', ' “Unsure” answers left out.'), fresh: ['look'], csv: 'dream-menu-trade-call',
      legend: [['Worse', '--v-down', 'sq'], ['Neutral', '--v-ns', 'sq'], ['Better', '--v-up', 'sq']] });
    V.responsive(c2.plot, function (W) {
      var rows = [
        { l: 'Their call on trade', parts: [['Deteriorating', o.call[0][2], '--v-down'], ['Mixed', o.call[1][2], '--v-ns'], ['Stable', o.call[2][2], '--v-d1'], ['Improving', o.call[3][2], '--v-up']], neg: o.call[0][2] + o.call[1][2] / 2 },
        { l: 'Trading against last year', parts: [['Worse', o.vs[0][2], '--v-down'], ['About the same', o.vs[1][2], '--v-ns'], ['Better', o.vs[2][2], '--v-d1'], ['Much better', o.vs[3][2], '--v-up']], neg: o.vs[0][2] + o.vs[1][2] / 2 }];
      var H = 220, s = V.svg(c2.plot, W, H, 'Trade call'), m = { l: 0, r: 0 };
      var lo = -Math.max(rows[0].neg, rows[1].neg), hi = Math.max(100 - rows[0].neg, 100 - rows[1].neg), x = lin(lo, hi, 2, W - 2);
      rows.forEach(function (r, i) {
        var y0 = 24 + i * 92, gg = el('g', {}, s), cx = x(-r.neg);
        el('text', { x: 0, y: y0, class: 't-ink', 'font-weight': 700 }, gg, r.l);
        r.parts.forEach(function (p) {
          var w = (x(100) - x(0)) * p[1] / 100;
          var seg = el('rect', { x: cx, y: y0 + 10, width: Math.max(0, w - 2), height: 26, fill: 'var(' + p[2] + ')', rx: 0 }, gg);
          if (w > 34) el('text', { x: cx + w / 2 - 1, y: y0 + 27, 'text-anchor': 'middle', fill: p[2] === '--v-ns' || p[2] === '--v-d1' ? 'var(--v-ink)' : '#fff', 'font-weight': 700, 'font-size': 12 }, gg, p[1] + '%');
          V.tip.bind(seg, '<b>' + esc(p[0]) + '</b><div class="row"><span class="k">' + esc(r.l) + '</span><span>' + p[1] + '%</span></div>');
          el('text', { x: cx + 2, y: y0 + 52, 'font-size': 10.5 }, gg, w > 60 ? p[0] : '');
          cx += w;
        });
      });
      el('line', { x1: x(0), x2: x(0), y1: 26, y2: H - 30, stroke: 'var(--v-ink2)', 'stroke-width': 1.5 }, s);
      c2.setTable([{ l: 'Question', k: 'q' }, { l: 'Answer', k: 'a' }, { l: 'Operators', k: 'n', n: 1 }, { l: 'Share %', k: 'p', n: 1 }],
        o.call.map(function (x) { return { q: 'Call on trade', a: x[0], n: x[1], p: x[2] }; }).concat(o.vs.map(function (x) { return { q: 'Against last year', a: x[0], n: x[1], p: x[2] }; })));
    });
    var k = h('div', 'kpis'); k.style.gridTemplateColumns = 'repeat(2,minmax(0,1fr))';
    k.innerHTML = '<div class="kpi"><span class="lab">Trading environment</span><span class="val">' + o.trading.toFixed(1) + '<small>/10</small></span><span class="del">How easy trading feels right now</span></div><div class="kpi"><span class="lab">Predictability, next 3 months</span><span class="val">' + o.predictable.toFixed(1) + '<small>/10</small></span><span class="del down">Planning horizon is short</span></div>';
    b.appendChild(k);
    var big = o.gap.filter(function (g) { return g.pressure === 'Energy/utilities'; })[0];
    var price = (o.actions.filter(function (x) { return x[0] === 'Price changes'; })[0] || [0, 0])[1];
    setT('t8', 'Operators are answering costs with prices, not efficiency: ' + price + '% have changed prices, but while ' + big.pv + '% name ' + esc(big.pressure.split('/')[0].toLowerCase()) + ' as a pressure, only ' + big.av + '% have invested to cut it');
  })();
  }
  // dm-fresh.js loads deferred, so draw once the page is parsed and it has run
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
