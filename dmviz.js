/* dmviz.js: small chart toolkit for Dream Menu analysis pages. No dependencies.
   Every chart sits in a card with: an action title, optional filters, a table view, CSV download,
   a source line and a "Data to ... · Updated ..." stamp (from dm-fresh.js). */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var ICON = {
    table: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 3h12v10H2zM2 6.5h12M2 10h12M6.5 3v10" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    csv: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v8m0 0-3-3m3 3 3-3M3 12.5h10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    link: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.5 9.5l3-3M7 4.5l1-1a2.5 2.5 0 0 1 3.5 3.5l-1 1M9 11.5l-1 1A2.5 2.5 0 0 1 4.5 9l1-1" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
  };

  function el(tag, attrs, parent, text) {
    var n = document.createElementNS(NS, tag);
    if (attrs) for (var k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) n.setAttribute(k, attrs[k]);
    if (text !== undefined) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  }
  function h(tag, cls, html) { var n = document.createElement(tag); if (cls) n.className = cls; if (html !== undefined) n.innerHTML = html; return n; }
  function esc(s) { return String(s === undefined || s === null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function lin(d0, d1, r0, r1) { var k = (r1 - r0) / ((d1 - d0) || 1); var f = function (v) { return r0 + (v - d0) * k; }; f.inv = function (p) { return d0 + (p - r0) / k; }; return f; }
  function nice(lo, hi, n) {
    var span = hi - lo || 1, step = Math.pow(10, Math.floor(Math.log10(span / (n || 5)))), err = (n || 5) / span * step;
    if (err <= 0.15) step *= 10; else if (err <= 0.35) step *= 5; else if (err <= 0.75) step *= 2;
    var a = Math.floor(lo / step) * step, b = Math.ceil(hi / step) * step, t = [];
    for (var v = a; v <= b + step / 2; v += step) t.push(+v.toFixed(10));
    return { lo: a, hi: b, ticks: t, step: step };
  }
  function fmt(v, d) { if (v === null || v === undefined || isNaN(v)) return '–'; return (+v).toLocaleString('en-GB', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function pp(v, d) { if (v === null || v === undefined) return '–'; d = d === undefined ? 1 : d; return (v > 0 ? '+' : v < 0 ? '−' : '±') + Math.abs(v).toFixed(d) + ' pts'; }
  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  // ---------- tooltip
  var tipEl;
  function tip() { if (!tipEl) { tipEl = h('div', 'dmv-tip'); tipEl.setAttribute('role', 'status'); document.body.appendChild(tipEl); } return tipEl; }
  function showTip(evt, html) {
    var t = tip(); t.innerHTML = html; t.classList.add('on');
    var x, y;
    if (evt && evt.clientX !== undefined && (evt.clientX || evt.clientY)) { x = evt.clientX; y = evt.clientY; }
    else if (evt && evt.target && evt.target.getBoundingClientRect) { var r = evt.target.getBoundingClientRect(); x = r.left + r.width / 2; y = r.top; }
    var w = t.offsetWidth, hh = t.offsetHeight, vw = window.innerWidth;
    var left = Math.min(Math.max(8, x + 14), vw - w - 8), top = y - hh - 12;
    if (top < 8) top = y + 18;
    t.style.left = left + 'px'; t.style.top = top + 'px';
  }
  function hideTip() { if (tipEl) tipEl.classList.remove('on'); }
  function bindTip(node, html) {
    node.classList.add('dmv-hit');
    node.setAttribute('tabindex', '0');
    var f = typeof html === 'function' ? html : function () { return html; };
    node.addEventListener('mousemove', function (e) { showTip(e, f()); });
    node.addEventListener('mouseleave', hideTip);
    node.addEventListener('focus', function (e) { showTip(e, f()); });
    node.addEventListener('blur', hideTip);
    node.addEventListener('touchstart', function (e) { var t = e.touches[0]; showTip({ clientX: t.clientX, clientY: t.clientY }, f()); }, { passive: true });
  }
  document.addEventListener('scroll', hideTip, { passive: true });
  document.addEventListener('touchstart', function (e) { if (!e.target.closest || !e.target.closest('.dmv-hit')) hideTip(); }, { passive: true });

  // ---------- CSV
  function csv(name, cols, rows) {
    var q = function (v) { v = v === null || v === undefined ? '' : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var body = [cols.map(function (c) { return q(c.l || c); }).join(',')].concat(rows.map(function (r) { return cols.map(function (c) { return q(typeof c === 'string' ? r[c] : (c.csv ? c.csv(r) : r[c.k])); }).join(','); })).join('\n');
    var blob = new Blob(['﻿' + body], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name + '.csv';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }


  // ---------- "How to read this" notes, one per chart id (kept short: what it shows, how to read, one caution)
  var INFO = {
    'city-index': 'Pick a dish and read across. Use the key above the table: cells towards the "bigger share" end mean that city names the dish more than the panel as a whole does, cells towards the other end less, and neutral cells are about average. Because every cell is a share of that city’s own mentions, a city with 40 interviews compares fairly with one that has 600.\nCaution: greyed cells rest on fewer than five mentions. Treat them as a hint, not a finding.',
    'agreement': 'Each bar takes the venues guests name most, from the top 10 out to every venue, and shows the share holding at least one guide award. Bars that fall from left to right mean guests and critics agree most about the very top places.\nCaution: "no award" means no award in the guides we track, not a judgement on quality.',
    'concentration': 'Read along the curve: at any point across, it tells you what share of all mentions goes to that top slice of venues. The steeper the early rise, the more guests pile onto the same few places.\nUse it to judge how hard it is for a new venue to be noticed.',
    'champions': 'These are the places guests name most that the big guides leave out. The bar is the number of times guests named each venue.\nUse it to find word-of-mouth favourites before the guides do. Small counts are normal here: two or three mentions is already notable.',
    'award-favourites': 'Award-holding venues, ranked by how often guests name them. The bar is the number of mentions.\nRead it as the places where public opinion and critical opinion meet.',
    'settled': 'Each bar is one course. The taller the bar, the more of its answers go to just three food groups, so the more guests agree on what that course should be.\nUse it to see where a menu must play safe (tall bars) and where there is room to stand out (short bars).',
    'demand-mix': 'One panel per course. Each bar is a food group’s share of that course’s answers, so the panels compare fairly even though courses get different numbers of answers. The top bar in each panel is the group to lead with.\nGroups outside the top six are not shown, so the bars do not add up to 100%.',
    'menu-gap': 'Two different measures side by side. "Guests naming it" is the share of guests whose dream answer for that course is this dish. "On menus" is the share of audited venues that list it. A Gap is a dish guests name often that few menus offer; Over-supplied is the reverse; Table stakes are wanted and widely listed.\nThe audit covers the venues guests name most, not the whole market, and menus change: check the date in the source line.',
    'menu-price': 'The median is the middle printed price for the course across the audited menus; the middle half is the range that half of all prices fall inside.\nThese are the venues guests name most, which skew above the market average.',
    'cat-score': 'One row per food group in each course. Share is how much of the course’s demand it holds; change is how that share has moved since late 2025. A call is only Grow, Defend or Trim when the move passes a significance test; otherwise the group is Core (large) or Niche (small).\nUse the filter to see one call at a time. This is guest demand, not sales: read it beside your own sell-out data.',
    'tr-churn': 'Each dot is how much of a course has changed food group since late 2025. The grey band is how much change you would see from chance alone if nothing had really moved. A dot inside the band is noise; a dot clearly to its right is a real shift.\nThe further right, the more that course is being rewritten.',
    'tr-conc': 'Each line follows the share taken by a course’s five favourite dishes, quarter by quarter. Rising means tastes are narrowing onto the same favourites; falling means guests are spreading out to other dishes.\nCaution: where the shaded bands of two quarters overlap, the difference between them could be chance.',
    'tr-stages': 'Each bar splits a course’s 14 most-named dishes into life-cycle stages, from rising to fading. A dish only counts as rising or fading if its move passes a statistical test; otherwise it sits in "no clear pattern".\nA course with many staples is stable; one with many risers and faders is in flux.',
    'tr-staples': 'Each line runs from a dish’s lowest to its highest quarterly share, and the dot is its share overall. A short line means the dish barely moves from quarter to quarter.\nThese are the dishes to keep on a menu while other courses change.',
    'tr-flows': 'Pick a course. Bars to the left are food groups that lost share; bars to the right gained it. Losses and gains always balance.\nCaution: these are shifts between two sets of interviews, not individual guests changing their minds. Only solid bars are clear moves.',
    'tr-slope': 'Each line joins a dish’s share in the earlier quarters (left) to the recent ones (right). Steeper means bigger change. Coloured lines passed a significance test; grey lines did not.\nStart with the coloured lines: they are the moves worth acting on.',
    'tr-mix': 'Each bar is one quarter, split into the five biggest food groups, so every bar adds to 100%. Watch how the size of one colour changes from bar to bar.\nCaution: faded bars have few answers and can swing on a handful of interviews.',
    'tr-board': 'Every tracked dish, filed under the stage its share pattern fits best. The tiny chart beside each dish shows its share each quarter.\nRead it as a portfolio: protect staples, trial risers, and plan an exit for faders.',
    'tr-fan': 'The solid line is what has happened; the dashed line is where the recent trend points; the shaded fan is a sensible planning range around it. The fan widens because the further ahead you look, the less certain the path.\nUse the range for stock and range decisions, never the single line.',
    'bm-board': 'Each card sets a Dream Menu figure beside a published outside figure on the same topic. "Agrees" and "differs" compare direction and rough level only.\nOutside figures measure different people and things (all adults, delivery orders, menus), so a difference is a finding, not an error. They are never mixed into Dream Menu data.',
    'dr-soft': 'Each bar is the share of soft drink answers in that group; the thin line is the range the true share very likely sits in. Narrow lines mean a firm figure.\nCaution: this series only started in late August 2026, so it shows levels, not trends yet.',
    'dr-alc': 'Each bar is the share of alcoholic drink answers in that group; the thin line is the range the true share very likely sits in. "Alcohol-free instead" counts guests who chose not to drink.\nCaution: this series only started in late August 2026, so it shows levels, not trends yet.',
    'matrix': 'Across = how big a dish is (its share of answers). Up = how fast that share is growing. Bigger bubbles have more answers behind them.\nTop right: big and growing, back it. Top left: small but rising, the next staples. Bottom right: big but slipping, review it.',
    'confidence': 'Each dot is the best estimate of how much a dish’s share changed. The line around it is the range the true change very likely sits in.\nThe rule is simple: if the line crosses zero, the change could be chance. Act only on lines that sit wholly to one side.',
    'trend-wall': 'One small chart per food group, all on the same scale within a cell, so shapes compare at a glance. The shaded area marks the recent quarters used in the test; a coloured frame means the move is clear.\nScan for frames first, then check the detail in the other partner chapters.',
    'dish-heat': 'Each row is a dish and each column a quarter. Colour compares the dish only with its own average, so a small dish having a strong quarter shows up as clearly as a big one.\nUse it to spot specials worth trying. Caution: hatched columns have few answers.',
    'segments': 'Each column is one group of guests, with its six most-named items as a share of that group’s answers. Compare the same item across columns to see who wants it most.\nUse it to plan a range for the customer you sell to rather than the average guest.',
    'opportunity': 'One score out of 10 per dish or drink, combining how big it is, how fast it is moving, how firm the evidence is and how crowded the field is. Back = act now, Watch = promising, Review = losing ground.\nThe score is a way to rank a shortlist, not a forecast of sales.',
    'pressure-gap': 'For each pressure, the first bar is the share of operators feeling it and the second the share taking the action that answers it. A big gap between the two is unmet need.\nThat gap is where a supplier can offer help.',
    'trade-call': 'Each bar is all operator answers, split from "much worse" on the left to "much better" on the right. More of the bar to the right of the line means more optimism.\nCompare the rows to see whether the mood has improved on last year.'
  };

  function info(t) {
    if (!t) return '';
    return '<details class="vinfo"><summary><span class="vi-i" aria-hidden="true">i</span>How to read this</summary><div class="vi-b">' +
      t.split('\n').map(function (p) { return '<p>' + p + '</p>'; }).join('') + '</div></details>';
  }
  // ---------- card
  function card(host, o) {
    var c = h('div', 'dmv-card');
    if (o.id) { c.id = o.id; var slot = document.querySelector('[data-card="' + o.id + '"]'); if (slot) host = slot; }   // a page can place any chart by id
    var head = h('div', 'dmv-head');
    // Editorial order: the finding as the headline, what is measured as the line beneath, reading notes folded away.
    var note = o.info || INFO[o.id] || '';
    var tt = o.claim
      ? h('div', '', '<h3>' + o.claim + '</h3>' + (o.title ? '<p>' + o.title + '</p>' : '') + info((o.sub ? o.sub + '\n' : '') + note))
      : h('div', '', (o.title ? '<h3>' + o.title + '</h3>' : '') + (o.sub ? '<p>' + o.sub + '</p>' : '') + info(note));
    head.appendChild(tt);
    var tools = h('div', 'dmv-tools');
    c.appendChild(head);
    var filters = h('div', 'dmv-filters'); c.appendChild(filters);
    if (!o.filters) filters.style.display = 'none';
    var legend = h('ul', 'dmv-legend'); c.appendChild(legend);
    if (!o.legend) legend.style.display = 'none'; else setLegend(legend, o.legend);
    var plot = h('div', 'dmv-plot'); c.appendChild(plot);
    var tbl = h('div', 'dmv-table'); c.appendChild(tbl);
    var foot = h('div', 'dmv-foot');
    foot.appendChild(h('p', 'dmv-src', o.src || ''));
    c.appendChild(foot);
    if (o.fresh && window.DM_FRESH) foot.appendChild(window.DM_FRESH.stamp(o.fresh));
    foot.appendChild(tools);
    host.appendChild(c);
    var api = { el: c, plot: plot, filters: filters, legend: legend, data: null };
    api.setTable = function (cols, rows, name) {
      api.data = { cols: cols, rows: rows, name: name || o.csv || 'dream-menu-data' };
      var t = '<table><thead><tr>' + cols.map(function (cl) { return '<th' + (cl.n ? ' class="n"' : '') + ' scope="col">' + esc(cl.l) + '</th>'; }).join('') + '</tr></thead><tbody>' +
        rows.map(function (r) { return '<tr>' + cols.map(function (cl, i) { var v = cl.f ? cl.f(r) : r[cl.k]; return (i === 0 ? '<th scope="row">' : '<td' + (cl.n ? ' class="n"' : '') + '>') + esc(v) + (i === 0 ? '</th>' : '</td>'); }).join('') + '</tr>'; }).join('') + '</tbody></table>';
      tbl.innerHTML = t;
    };
    var bt = h('button', 'dmv-btn', ICON.table + 'Table'); bt.type = 'button'; bt.setAttribute('aria-pressed', 'false');
    bt.onclick = function () { var on = c.classList.toggle('show-table'); bt.setAttribute('aria-pressed', on ? 'true' : 'false'); };
    var bc = h('button', 'dmv-btn', ICON.csv + 'CSV'); bc.type = 'button';
    bc.onclick = function () { if (api.data) csv(api.data.name, api.data.cols.map(function (cl) { return { l: cl.l, csv: function (r) { return cl.csv ? cl.csv(r) : cl.f ? cl.f(r) : r[cl.k]; } }; }), api.data.rows); };
    tools.appendChild(bt); tools.appendChild(bc);
    if (o.id) {
      var bl = h('button', 'dmv-btn', ICON.link + 'Link'); bl.type = 'button'; bl.title = 'Copy a link to this chart';
      bl.onclick = function () { var u = location.origin + location.pathname + '#' + o.id; (navigator.clipboard ? navigator.clipboard.writeText(u) : Promise.reject()).then(function () { bl.innerHTML = ICON.link + 'Copied'; setTimeout(function () { bl.innerHTML = ICON.link + 'Link'; }, 1600); }, function () { location.hash = o.id; }); };
      tools.appendChild(bl);
    }
    return api;
  }
  function setLegend(ul, items) {
    ul.innerHTML = items.map(function (it) { return '<li><i class="dmv-sw' + (it[2] ? ' ' + it[2] : '') + '" style="background:var(' + it[1] + ')"></i>' + esc(it[0]) + '</li>'; }).join('');
    ul.style.display = '';
  }
  function chips(host, opts, cur, onPick) {
    host.style.display = '';
    host.innerHTML = '';
    opts.forEach(function (op) {
      var b = h('button', 'dmv-btn', esc(op[1])); b.type = 'button';
      b.setAttribute('aria-pressed', op[0] === cur ? 'true' : 'false');
      b.onclick = function () { host.querySelectorAll('.dmv-btn').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); }); b.setAttribute('aria-pressed', 'true'); onPick(op[0]); };
      host.appendChild(b);
    });
  }
  // re-draw on width change
  function responsive(node, draw) {
    var last = 0, t;
    function go() { var w = Math.round(node.clientWidth); if (w && w !== last) { last = w; draw(w); } }
    go();
    if (window.ResizeObserver) new ResizeObserver(function () { clearTimeout(t); t = setTimeout(go, 80); }).observe(node);
    else window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(go, 120); });
    return function () { last = 0; go(); };
  }
  function svg(parent, w, hgt, label) {
    parent.innerHTML = '';
    var s = el('svg', { viewBox: '0 0 ' + w + ' ' + hgt, width: w, height: hgt, role: 'img', 'aria-label': label || '' }, parent);
    return s;
  }
  // a short spark line, for KPI tiles and small multiples
  function spark(parent, vals, o) {
    o = o || {};
    var w = o.w || 160, hh = o.h || 34, pad = 4;
    var v = vals.map(function (x) { return x === null ? null : +x; });
    var ok = v.filter(function (x) { return x !== null; });
    var lo = o.min !== undefined ? o.min : Math.min.apply(null, ok), hi = o.max !== undefined ? o.max : Math.max.apply(null, ok);
    if (hi === lo) { hi += 1; lo -= 1; }
    var x = lin(0, v.length - 1, pad, w - pad), y = lin(lo, hi, hh - pad, pad);
    var s = el('svg', { viewBox: '0 0 ' + w + ' ' + hh, preserveAspectRatio: 'none', 'aria-hidden': 'true' }, parent);
    if (o.band) el('rect', { x: x(o.band[0]), y: 0, width: x(o.band[1]) - x(o.band[0]), height: hh, fill: 'var(--v-wash)' }, s);
    var d = '', area = '', started = false, first = null, lastx = null;
    v.forEach(function (val, i) {
      if (val === null) return;
      d += (started ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(val).toFixed(1);
      if (!started) first = x(i);
      lastx = x(i); started = true;
    });
    if (o.area) { el('path', { d: d + 'L' + lastx + ' ' + hh + 'L' + first + ' ' + hh + 'Z', fill: o.color || 'var(--v-brand)', opacity: .1 }, s); }
    el('path', { d: d, fill: 'none', stroke: o.color || 'var(--v-brand)', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', 'vector-effect': 'non-scaling-stroke' }, s);
    if (o.low) v.forEach(function (val, i) { if (val !== null && o.low[i]) el('circle', { cx: x(i), cy: y(val), r: 2.2, fill: 'var(--v-surface)', stroke: o.color || 'var(--v-brand)', 'stroke-width': 1.4, 'vector-effect': 'non-scaling-stroke' }, s); });
    var li = v.length - 1; while (li > 0 && v[li] === null) li--;
    if (o.dot !== false) el('circle', { cx: x(li), cy: y(v[li]), r: 3, fill: o.color || 'var(--v-brand)' }, s);
    return s;
  }
  var TIER = {
    Back: '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="currentColor"/><path d="M4.8 8.2 7 10.4l4.2-4.6" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    Watch: '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="currentColor"/><circle cx="8" cy="8" r="2.2" fill="#0b0b0b"/></svg>',
    Review: '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="currentColor"/><path d="M5.2 5.2l5.6 5.6M10.8 5.2l-5.6 5.6" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/></svg>'
  };
  function tier(t) { return '<span class="tier ' + t.toLowerCase() + '">' + TIER[t] + t + '</span>'; }

  window.DMV = { el: el, h: h, esc: esc, lin: lin, nice: nice, fmt: fmt, pp: pp, css: css, card: card, chips: chips, legend: setLegend,
    responsive: responsive, svg: svg, spark: spark, tip: { show: showTip, hide: hideTip, bind: bindTip }, csv: csv, tier: tier };
})();
