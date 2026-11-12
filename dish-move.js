/* Fills the "Is it rising?" card on /trends/<slug> for signed-in partners.
   The figures live in /partner/dish-moves.js, which middleware.js only serves after sign-in.
   Without sign-in that file returns 401, window.DM_DISHMOVES stays undefined and the locked card stays as it is. */
(function () {
  var box = document.getElementById('dm-move');
  var D = window.DM_DISHMOVES;
  if (!box || !D || !D.d) return;
  var rows = D.d[box.getAttribute('data-slug')];
  if (!rows || !rows.length) return;
  var M = D.meta || {};
  var MIN = M.min_n || 100;
  var LABEL = (document.querySelector('.pg-hero h1') || {}).textContent || 'this dish';
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ql = function (q) { var p = String(q).split('-'); return p[1] + ' ' + p[0].slice(2); };
  var pts = function (v) { return (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(1) + ' pts'; };
  var span = function (a) { return a && a.length ? (a.length > 1 ? ql(a[0]) + ' to ' + ql(a[a.length - 1]) : ql(a[0])) : ''; };

  /* Least-squares line through the quarters with enough answers (all quarters if fewer than three qualify). */
  function fit(r) {
    var s = r.share || [], idx = [];
    s.forEach(function (v, i) { if (v != null && !(r.low && r.low[i])) idx.push(i); });
    if (idx.length < 3) { idx = []; s.forEach(function (v, i) { if (v != null) idx.push(i); }); }
    if (idx.length < 2) return null;
    var n = idx.length, mx = 0, my = 0, sxx = 0, sxy = 0;
    idx.forEach(function (i) { mx += i / n; my += s[i] / n; });
    idx.forEach(function (i) { sxx += (i - mx) * (i - mx); sxy += (i - mx) * (s[i] - my); });
    var b = sxx ? sxy / sxx : 0;
    return { a: my - b * mx, b: b, i0: idx[0], i1: idx[idx.length - 1] };
  }

  /* Indicative direction for moves that have not passed the clear-move test yet. */
  function indicative(r, f) {
    var m = r.move || 0, p = r.p == null ? 1 : r.p;
    if (Math.abs(m) < 0.5) return { cls: 'flat', label: 'Holding steady', why: 'recent share within half a point of the earlier share' };
    var dir = m > 0 ? 'up' : 'down';
    var strength = p < 0.10 ? 'strong hint' : p < 0.30 ? 'early hint' : 'weak hint';
    var mixed = f && Math.abs(f.b) >= 0.1 && (f.b > 0) !== (m > 0);
    return {
      cls: 'ind-' + dir,
      label: 'Leaning ' + dir + ' (' + strength + ')',
      why: (mixed ? 'the latest quarters run the other way, so treat with care; ' : '') +
        (p < 0.10 ? 'close to the clear-move bar' : p < 0.30 ? 'moving, but more interviews needed to confirm' : 'too close to call on current numbers')
    };
  }

  function spark(r, f) {
    var s = r.share || [], W = 300, H = 90, pad = 8, n = s.length;
    var vals = s.filter(function (v) { return v != null; });
    if (vals.length < 2) return '';
    var top = Math.max.apply(null, vals.concat([1])) * 1.15;
    var x = function (i) { return pad + i * (W - 2 * pad) / (n - 1); };
    var y = function (v) { return H - pad - Math.max(0, Math.min(top, v)) / top * (H - 2 * pad); };
    var path = '', dots = '', tl = '';
    s.forEach(function (v, i) {
      if (v == null) return;
      path += (path ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1);
      var faint = r.low && r.low[i];
      dots += '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="3.5" class="' + (faint ? 'lo' : '') + '"><title>' + ql(r.q[i]) + ': ' + v.toFixed(1) + '% (' + (r.n_q ? r.n_q[i] : '') + ' answers)</title></circle>';
    });
    if (f) tl = '<line class="tl" x1="' + x(f.i0).toFixed(1) + '" y1="' + y(f.a + f.b * f.i0).toFixed(1) + '" x2="' + x(f.i1).toFixed(1) + '" y2="' + y(f.a + f.b * f.i1).toFixed(1) + '"><title>Trend line through the quarters with ' + MIN + '+ answers</title></line>';
    return '<svg class="mv-spark" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Share by quarter">' + tl + '<path d="' + path + '"/>' + dots + '</svg>';
  }

  function scoreBar(r) {
    if (r.score == null) return '<p class="pg-mut mv-noscore">No trend score: soft drinks are not scored because the question changed in August 2026.</p>';
    var P = r.parts || {}, seg = [['demand', 'Demand', 3], ['momentum', 'Momentum', 3.5], ['evidence', 'Evidence', 1.5], ['room', 'Room to enter', 2]];
    var bar = seg.map(function (s) { return '<i class="sb-' + s[0] + '" style="width:' + (10 * (P[s[0]] || 0)).toFixed(1) + '%" title="' + s[1] + ' ' + (P[s[0]] || 0).toFixed(1) + ' of ' + s[2] + '"></i>'; }).join('');
    var keys = seg.map(function (s) { return '<span><i class="sw sb-' + s[0] + '"></i>' + s[1] + ' <b>' + (P[s[0]] || 0).toFixed(1) + '</b>/' + s[2] + '</span>'; }).join('');
    return '<div class="mv-sb"><div class="mv-sbar" aria-hidden="true">' + bar + '</div><div class="mv-skeys">' + keys +
      (r.fat ? '<span class="mv-fat">Bin it penalty <b>−' + r.fat.toFixed(1) + '</b></span>' : '') + '</div></div>';
  }

  function theories(r, label) {
    var S = r.shift;
    if (!S) return '';
    var m = r.move || 0, up = m >= 0.5, down = m <= -0.5;
    var lead = up ? 'Possibly taking share from' : down ? 'Possibly losing share to' : 'Holding its own against these movers';
    var items = (S.sub || []).map(function (x) {
      var tags = [];
      if (x.same) tags.push('same family');
      if (x.r <= -0.5) tags.push('opposite quarterly pattern');
      if (x.sig) tags.push('clear move');
      return '<li><a href="/trends/' + esc(x.s) + '">' + esc(x.l) + '</a> <b class="' + (x.sig ? (x.move > 0 ? 'up' : 'down') : '') + '">' + pts(x.move) + '</b>' +
        (tags.length ? ' <span class="pg-mut">' + tags.join(' · ') + '</span>' : '') + '</li>';
    }).join('');
    var ctx = [];
    var G = S.grp;
    if (G && Math.abs(G.move) >= 0.5 && (up || down)) {
      if ((G.move > 0) === up) ctx.push('Part of a wider shift: the ' + esc(G.l) + ' family as a whole is ' + pts(G.move) + (G.sig ? ' (clear)' : '') + ', so this may be the category moving rather than the dish.');
      else ctx.push((up ? 'Winning inside a shrinking family' : 'Losing ground inside a growing family') + ': ' + esc(G.l) + ' overall is ' + pts(G.move) + (G.sig ? ' (clear)' : '') + ', so the swing looks specific to ' + esc(label) + '.');
    }
    if (S.og && S.og.length) ctx.push('Across the ' + esc(r.course.toLowerCase()) + ' course, the bigger swing is ' + (up ? 'away from ' : down ? 'towards ' : 'between ') +
      S.og.map(function (o) { return esc(o.l) + ' (' + pts(o.move) + (o.sig ? ', clear' : '') + ')'; }).join(' and ') + '.');
    if (!items && !ctx.length) return '';
    return '<div class="mv-th"><b>Who&rsquo;s taking share? <span class="mv-theory">Theory</span></b>' +
      (items ? '<p>' + lead + ':</p><ol>' + items + '</ol>' : '') +
      ctx.map(function (c) { return '<p>' + c + '</p>'; }).join('') + '</div>';
  }

  function block(r) {
    var f = fit(r);
    var dir = r.move > 0 ? 'up' : r.move < 0 ? 'down' : 'flat';
    var tag, note = '';
    if (r.sig) {
      tag = '<span class="mv-tag ' + dir + '">' + (r.move > 0 ? 'Clear riser' : 'Clear faller') + '</span>';
    } else {
      var ind = indicative(r, f);
      tag = '<span class="mv-tag flat">No clear move yet</span><span class="mv-tag ' + ind.cls + '">Indicative: ' + ind.label + '</span>';
      note = '<p class="mv-ind">Indicative trend: ' + esc(ind.why) + '. Not yet a clear move at p &lt; 0.05.</p>';
    }
    var head = '<div class="mv-head"><b>' + esc(r.course) + '</b>' + tag +
      (r.score != null ? '<span class="mv-score">Trend score <b>' + r.score.toFixed(1) + '</b>/10' + (r.tier ? ' · <span class="mv-tier t-' + esc(r.tier.toLowerCase()) + '">' + esc(r.tier) + '</span>' : '') + '</span>' : '') + '</div>';
    var line = r.early != null && r.late != null
      ? '<p class="mv-line">' + r.early.toFixed(1) + '% (' + span(M.early) + ') → <b>' + r.late.toFixed(1) + '%</b> (' + span(M.late) + '), <b class="' + (r.sig ? dir : '') + '">' + pts(r.move) + '</b>' +
        (r.lo != null && r.hi != null ? ', 95% range ' + pts(r.lo) + ' to ' + pts(r.hi) : '') + (r.p != null ? ', p = ' + (r.p < 0.001 ? '<0.001' : r.p.toFixed(3)) : '') + '</p>'
      : '';
    var th = '', td = '', tn = '';
    (r.q || []).forEach(function (q, i) {
      var faint = r.low && r.low[i] ? ' class="lo"' : '';
      th += '<th class="num"' + faint + '>' + ql(q) + '</th>';
      td += '<td class="num"' + faint + '>' + (r.share && r.share[i] != null ? r.share[i].toFixed(1) + '%' : '–') + '</td>';
      tn += '<td class="num"' + faint + '>' + (r.n_q ? r.n_q[i] : '') + '</td>';
    });
    var table = '<div class="mv-tabwrap"><table class="mv-tab"><colgroup><col class="lab"></colgroup><thead><tr><th>Quarter</th>' + th + '</tr></thead><tbody><tr><td>Share</td>' + td + '</tr><tr><td>Answers</td>' + tn + '</tr></tbody></table></div>';
    return '<div class="mv-row">' + head + spark(r, f) + line + note + theories(r, LABEL) + scoreBar(r) + table + (r.note ? '<p class="pg-mut">' + esc(r.note) + '</p>' : '') + '</div>';
  }

  var key = '<details class="mv-key" open><summary>Key</summary><div class="mv-kgrid">' +
    '<div><b>Chart</b>' +
      '<p><svg width="34" height="10" aria-hidden="true"><line x1="2" y1="5" x2="32" y2="5" class="kl"/><circle cx="17" cy="5" r="3.5" class="kd"/></svg> Share of guests answering that course, by quarter</p>' +
      '<p><svg width="34" height="10" aria-hidden="true"><circle cx="17" cy="5" r="3.5" class="kd lo"/></svg> Fewer than ' + MIN + ' answers that quarter: read with care</p>' +
      '<p><svg width="34" height="10" aria-hidden="true"><line x1="2" y1="5" x2="32" y2="5" class="ktl"/></svg> Trend line through the quarters with ' + MIN + '+ answers</p></div>' +
    '<div><b>Trend score out of 10</b>' +
      '<p><i class="sw sb-demand"></i>Demand (up to 3): how often it is chosen in its course</p>' +
      '<p><i class="sw sb-momentum"></i>Momentum (up to 3.5): change from earlier to recent share</p>' +
      '<p><i class="sw sb-evidence"></i>Evidence (up to 1.5): how sure the change is</p>' +
      '<p><i class="sw sb-room"></i>Room to enter (up to 2): how tied it is to one venue</p>' +
      '<p class="pg-mut">Less 1 point if guests also name it in Bin it.</p></div>' +
    '<div><b>Tier</b>' +
      '<p><span class="mv-tier t-back">Back</span> clear riser, or score 6.0+</p>' +
      '<p><span class="mv-tier t-watch">Watch</span> score 4.5 to 5.9, or lower and not falling</p>' +
      '<p><span class="mv-tier t-review">Review</span> clear faller, or under 4.5 and falling</p></div>' +
    '<div><b>Movement</b>' +
      '<p><span class="mv-tag up">Clear riser</span> <span class="mv-tag down">Clear faller</span> passed the test (p &lt; 0.05)</p>' +
      '<p><span class="mv-tag ind-up">Leaning up</span> <span class="mv-tag ind-down">Leaning down</span> indicative only: strong hint p &lt; 0.10, early hint p &lt; 0.30, weak hint above</p>' +
      '<p><span class="mv-tag flat">Holding steady</span> within half a point</p></div>' +
    '<div><b>Who&rsquo;s taking share? (theory)</b>' +
      '<p>Dishes in the same course that moved the other way, ranked by size of move, more weight for the same family, a clear move, or quarters that rise as this one falls (opposite quarterly pattern).</p>' +
      '<p class="pg-mut">A pointer for where to look, not proof one dish replaced another: guests choose one dish per course, so shares always trade off.</p></div>' +
    '</div></details>';

  var ib = document.getElementById('dm-ins');
  var pins = [];
  rows.forEach(function (r) { (r.ins || []).forEach(function (t) { pins.push((rows.length > 1 ? r.course + ': ' : '') + t); }); });
  if (ib && pins.length) {
    var ul = ib.querySelector('.ins-list');
    ul.insertAdjacentHTML('beforeend', pins.slice(0, 3).map(function (t) { return '<li class="ins-p"><span class="ins-tag">Partner</span>' + esc(t) + '</li>'; }).join(''));
    ib.hidden = false;
    if (ib.parentNode) ib.parentNode.classList.add('has-ins');
  }
  box.classList.remove('pg-lock');
  box.classList.add('mv');
  box.innerHTML = '<h2>Is it rising? <span class="mv-badge">Partner</span></h2>' + '<details class="vinfo"><summary><span class="vi-i" aria-hidden="true">i</span>How to read this</summary><div class="vi-b"><p>Each small chart is this dish’s share of a course’s answers, quarter by quarter. Faint dots are quarters with few answers; the straight line is the trend through the firmer quarters.</p><p>The badge only says rising or falling when the change passes a statistical test. Otherwise treat the movement as noise.</p></div></details>' + '<div class="mv-rows">' + rows.map(block).join('') + '</div>' + key +
    '<p class="pg-mut">Movement compares the pooled share in ' + span(M.early) + ' with ' + span(M.late) +
    ' (' + esc(M.test || 'two-proportion z-test, p < 0.05') + '). Trend scores match <a href="/analysis#opportunity-sec">the analysis</a>. Data to ' +
    esc(M.last ? new Date(M.last + 'T12:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '') + '. Licensed to Dream Menu partners; please do not share.</p>';
})();
