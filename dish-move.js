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
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ql = function (q) { var p = String(q).split('-'); return p[1] + ' ' + p[0].slice(2); };
  var pts = function (v) { return (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(1) + ' pts'; };
  var span = function (a) { return a && a.length ? (a.length > 1 ? ql(a[0]) + ' to ' + ql(a[a.length - 1]) : ql(a[0])) : ''; };

  function spark(r) {
    var s = r.share || [], W = 300, H = 90, pad = 8, n = s.length;
    var vals = s.filter(function (v) { return v != null; });
    if (vals.length < 2) return '';
    var top = Math.max.apply(null, vals.concat([1])) * 1.15;
    var x = function (i) { return pad + i * (W - 2 * pad) / (n - 1); };
    var y = function (v) { return H - pad - v / top * (H - 2 * pad); };
    var path = '', dots = '';
    s.forEach(function (v, i) {
      if (v == null) return;
      path += (path ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1);
      var faint = r.low && r.low[i];
      dots += '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="3.5" class="' + (faint ? 'lo' : '') + '"><title>' + ql(r.q[i]) + ': ' + v.toFixed(1) + '% (' + (r.n_q ? r.n_q[i] : '') + ' answers)</title></circle>';
    });
    return '<svg class="mv-spark" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Share by quarter">' +
      '<path d="' + path + '"/>' + dots + '</svg>';
  }

  function block(r) {
    var dir = r.move > 0 ? 'up' : r.move < 0 ? 'down' : 'flat';
    var verdict = r.sig ? (r.move > 0 ? 'Clear riser' : 'Clear faller') : 'No clear move yet';
    var head = '<div class="mv-head"><b>' + esc(r.course) + '</b><span class="mv-tag ' + (r.sig ? dir : 'flat') + '">' + verdict + '</span>' +
      (r.score != null ? '<span class="mv-score">Trend score <b>' + r.score.toFixed(1) + '</b>/10' + (r.tier ? ' · ' + esc(r.tier) : '') + '</span>' : '') + '</div>';
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
    var table = '<div class="tablewrap" style="border:0"><table class="mv-tab"><thead><tr><th></th>' + th + '</tr></thead><tbody><tr><td>Share</td>' + td + '</tr><tr><td class="pg-mut">Answers</td>' + tn + '</tr></tbody></table></div>';
    return '<div class="mv-row">' + head + spark(r) + line + table + (r.note ? '<p class="pg-mut">' + esc(r.note) + '</p>' : '') + '</div>';
  }

  box.classList.remove('pg-lock');
  box.classList.add('mv');
  box.innerHTML = '<h2>Is it rising? <span class="mv-badge">Partner</span></h2>' + '<div class="mv-rows">' + rows.map(block).join('') + '</div>' +
    '<p class="pg-mut">Share of the guests answering that course, by quarter. Movement compares the pooled share in ' + span(M.early) + ' with ' + span(M.late) +
    ' (' + esc(M.test || 'two-proportion z-test, p < 0.05') + '). Faded quarters have fewer than ' + (M.min_n || 100) + ' answers. Trend score from the opportunity score on <a href="/intelligence">Intelligence</a>. Data to ' + esc(M.last ? new Date(M.last + 'T12:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '') + '. Licensed to Dream Menu partners; please do not share.</p>';
})();
