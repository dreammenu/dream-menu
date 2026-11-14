/* Sub layers inside a food group (seafood today). Data: window.DM_MIX.sub from /mix-public.js,
   built by tools/sublayers.py. Every page that shows a food group uses these helpers, so the
   breakdown, its order and its figures are the same everywhere. */
(function () {
  var COURSE = { Starter: 's', Main: 'm', Side: 'd', Dessert: 'p' };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function data() { return (window.DM_MIX && window.DM_MIX.sub) || {}; }
  function get(group, course) {
    var G = data()[group]; if (!G) return null;
    var k = COURSE[course] || course; return G[k] && G[k].items && G[k].items.length ? G[k] : null;
  }
  function name(it) { return it.slug ? '<a href="/trends/' + it.slug + '">' + esc(it.l) + '</a>' : esc(it.l); }
  // full list with bars, as share of the course's answers
  function list(S) {
    var max = S.items[0].p || 1;
    return '<div class="dx-subs">' + S.items.map(function (s) {
      return '<div class="dx-row dx-srow" title="' + esc(s.l) + ': ' + s.p + '% of ' + S.label.toLowerCase() + ' answers, ' + Math.round(100 * s.n / S.n) + '% of ' + S.n + ' seafood picks"><span>' + name(s) + '</span><i><b style="width:' + (100 * s.p / max).toFixed(1) + '%"></b></i><em>' + s.p.toFixed(1) + '%</em></div>';
    }).join('') + '<p class="dx-note">Share of all ' + S.label.toLowerCase() + ' answers. Every seafood dish guests named: ' + S.n + ' picks.</p></div>';
  }
  // one line: "scallops 7.8%, prawns and langoustines 6.3%, ... and 14 more"
  function line(S, top) {
    top = top || 4;
    var a = S.items.slice(0, top).map(function (s) { return name(s) + ' ' + s.p.toFixed(1) + '%'; });
    var rest = S.items.length - top;
    return a.join(', ') + (rest > 0 ? ' and ' + rest + ' more' : '');
  }
  // expandable block for tables and cards
  function details(S, label) {
    return '<details class="dx-sub dx-subd"><summary>' + esc(label || ('Inside seafood: ' + S.items.length + ' sub layers')) + '</summary>' + list(S) + '</details>';
  }
  // CSV rows: [course label, group, sub layer, picks, share of course answers, course answers]
  function rows() {
    var out = [], D = data();
    Object.keys(D).forEach(function (g) { Object.keys(D[g]).forEach(function (k) { var S = D[g][k]; S.items.forEach(function (s) { out.push([S.label, g, s.l, s.n, s.p.toFixed(1), S.base]); }); }); });
    return out;
  }
  window.DMSub = { get: get, list: list, line: line, details: details, rows: rows };
})();
