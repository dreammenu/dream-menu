/* Sub layers (26 Nov 2026): a food group opens into its dishes, and a family dish (steak, chips and fries,
   curry...) opens into the kinds guests named. Each answer is counted once, at every level. Data:
   window.DM_MIX.sub from /mix-public.js, built by tools/sublayers.py, so every page shows the same figures. */
(function () {
  var COURSE = { Starter: 's', Main: 'm', Side: 'd', Dessert: 'p', 'Soft drink': 'k', 'Alcoholic drink': 'a' };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function data() { return (window.DM_MIX && window.DM_MIX.sub) || {}; }
  function get(group, course) {
    var G = data()[group]; if (!G) return null;
    var k = COURSE[course] || course; return G[k] && G[k].items && G[k].items.length ? G[k] : null;
  }
  function name(it) { return it.slug ? '<a href="/trends/' + it.slug + '">' + esc(it.l) + '</a>' : esc(it.l); }
  function bar(l, p, max, title, cls) {
    return '<div class="dx-row dx-srow' + (cls || '') + '" title="' + esc(title) + '"><span>' + l + '</span><i><b style="width:' + (100 * p / (max || 1)).toFixed(1) + '%"></b></i><em>' + p.toFixed(1) + '%</em></div>';
  }
  // the kinds inside one family dish, as an expandable block under its row
  function parts(it, S, max) {
    var tot = it.n || 1;
    return '<details class="dx-sub dx-partd"><summary>' + bar(name(it), it.p, max, it.l + ': ' + it.p + '% of ' + S.label.toLowerCase() + ' answers') + '</summary><div class="dx-parts">' +
      it.parts.map(function (x) { return bar(esc(x.l), x.p, max, x.l + ': ' + Math.round(100 * x.n / tot) + '% of ' + it.l.toLowerCase(), ' dx-part'); }).join('') +
      '<p class="dx-note">Inside ' + esc(it.l.toLowerCase()) + ': ' + it.parts.length + ' kinds, counted once in the dish above.</p></div></details>';
  }
  // the dishes inside one food group, with bars as share of the course's answers
  function list(S) {
    var max = S.items[0].p || 1;
    return '<div class="dx-subs">' + S.items.map(function (s) {
      if (s.parts && s.parts.length > 1) return parts(s, S, max);
      return bar(name(s), s.p, max, s.l + ': ' + s.p + '% of ' + S.label.toLowerCase() + ' answers, ' + Math.round(100 * s.n / S.n) + '% of the group', s.other ? ' dx-other' : '');
    }).join('') + '<p class="dx-note">Share of all ' + S.label.toLowerCase() + ' answers; ' + S.n + ' answers in the group in all. Dishes named by fewer than ten guests sit in the Other line.</p></div>';
  }
  // one line: "scallops 7.8%, prawns and langoustines 6.3%, ... and 14 more"
  function line(S, top) {
    top = top || 4;
    var named = S.items.filter(function (s) { return !s.other; });
    var a = named.slice(0, top).map(function (s) { return name(s) + ' ' + s.p.toFixed(1) + '%'; });
    var rest = named.length - top;
    return a.join(', ') + (rest > 0 ? ' and ' + rest + ' more' : '');
  }
  // expandable block for tables and cards
  function details(S, label, open) {
    var nd = S.items.filter(function (s) { return !s.other; }).length;
    return '<details class="dx-sub dx-subd"' + (open ? ' open' : '') + '><summary>' + esc(label || ('Open: ' + nd + ' dishes')) + '</summary>' + list(S) + '</details>';
  }
  // CSV rows: [course label, group, dish, kind, answers, share of course answers, course answers]
  function rows() {
    var out = [], D = data();
    Object.keys(D).forEach(function (g) { Object.keys(D[g]).forEach(function (k) { var S = D[g][k]; S.items.forEach(function (s) {
      out.push([S.label, g, s.l, '', s.n, s.p.toFixed(1), S.base]);
      (s.parts || []).forEach(function (x) { out.push([S.label, g, s.l, x.l, x.n, x.p.toFixed(1), S.base]); });
    }); }); });
    return out;
  }
  window.DMSub = { get: get, list: list, line: line, details: details, rows: rows };
})();
