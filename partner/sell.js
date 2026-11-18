/* Where to sell it and the market watch board (partners). Data: partner/sell-data.js, built by tools/build_accounts.py.
   On /analysis: #th-sell (top venues per range) and #p-watch (market watch, filled once partner/hub.js has drawn).
   On /partner/accounts: #acct-sheet, the full rep sheet with search, own-customer marks, print and CSV. */
(function () {
  var S = window.DM_SELL, V = window.DMV;
  if (!S || !V) return;
  var esc = V.esc, MK = ['Glasgow', 'Edinburgh', 'Rest of Scotland'];
  var KEY = 'dm-own-customers';
  function own() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function setOwn(o) { try { localStorage.setItem(KEY, JSON.stringify(o)); } catch (e) {} }
  var pts = function (x) { return (x > 0 ? '+' : '−') + Math.abs(x).toFixed(1) + ' pts'; };
  var times = function (k) { return k === 1 ? 'once' : k === 2 ? 'twice' : k + ' times'; };
  var low = function (s) { return s.charAt(0).toLowerCase() + s.slice(1); };

  function why(s) {
    var d = s.s ? '<a href="/trends/' + s.s + '">' + esc(s.d) + '</a>' : esc(s.d);
    if (s.t === 'Back') return d + ' named here ' + times(s.k) + ': a dish to back (' + s.sc.toFixed(1) + '/10' + (s.cl ? ', ' + pts(s.mv) + ' and rising clearly' : '') + ')';
    if (s.t === 'Watch') return d + ' named here ' + times(s.k) + ': one to watch (' + s.sc.toFixed(1) + '/10)';
    return d + ' named here ' + times(s.k) + ': part of ' + esc(low(s.g)) + ', a food group to grow';
  }
  function tier(t) { return '<span class="sc-call ' + (t === 'Watch' ? 'sc-core' : 'sc-grow') + '">' + t + '</span>'; }
  function costOf(r) { var R = S.ranges.filter(function (x) { return x.r === r; })[0]; return R && R.cost.length ? R.cost.join('; ') : ''; }

  function sheet(host, o) {
    var ranges = S.ranges.filter(function (R) { return S.v.some(function (v) { return v.r[R.r]; }); }).map(function (R) { return R.r; });
    var cur = { r: o.range || ranges[0], m: 'All', q: '', mine: 'all' }, mine = own();
    var c = V.card(host, { id: o.id, claim: o.claim, title: o.title, filters: true,
      src: 'Source: Dream Menu interviews to ' + S.last.split('-').reverse().join('/') + ', Scottish venues named at least twice. ' + S.how });
    var f2 = document.createElement('div'); f2.className = 'dmv-filters sell-f2'; c.filters.parentNode.insertBefore(f2, c.filters.nextSibling);
    function list() {
      return S.v.filter(function (v) { return v.r[cur.r] && (cur.m === 'All' || v.mk === cur.m); })
        .filter(function (v) { return !cur.q || (v.n + ' ' + v.c + ' ' + v.ad).toLowerCase().indexOf(cur.q) >= 0; })
        .filter(function (v) { return cur.mine === 'all' || (cur.mine === 'new' ? !mine[v.p] : !!mine[v.p]); })
        .sort(function (a, b) { return b.r[cur.r].x - a.r[cur.r].x || b.m - a.m; });
    }
    function draw() {
      var all = list(), rows = o.limit ? all.slice(0, o.limit) : all, cost = costOf(cur.r);
      c.plot.innerHTML = (cost ? '<p class="sell-cost"><b>Cost watch for this range:</b> ' + esc(cost) + '. Pair the pitch with a spec that protects margin.</p>' : '') +
        '<div class="sc-wrap"><table class="sc sell"><thead><tr>' + (o.full ? '<th class="sell-own">Ours</th>' : '') + '<th>Venue</th><th>Where</th><th class="num sell-g">Guests</th><th>Why it is worth a call</th><th class="sell-w">Watch out</th></tr></thead><tbody>' +
        (rows.length ? rows.map(function (v) {
          var b = v.r[cur.r], lead = b.s[0], more = b.s.slice(1, 3);
          return '<tr>' + (o.full ? '<td class="sell-own"><input type="checkbox" aria-label="' + esc(v.n) + ' is already our customer" data-p="' + v.p + '"' + (mine[v.p] ? ' checked' : '') + '></td>' : '') +
            '<td><b><a href="/venue/' + v.p + '">' + esc(v.n) + '</a></b>' + (v.aw ? '<small class="sell-aw">' + esc(v.aw) + '</small>' : '') + (v.ch ? '<small class="sell-aw">Chain</small>' : '') + '</td>' +
            '<td>' + esc(v.c) + (o.full && v.ad ? '<small>' + esc(v.ad) + '</small>' : '') + '</td><td class="num sell-g">' + v.g + '</td>' +
            '<td>' + tier(lead.t) + ' ' + why(lead) + (more.length ? '<small>Also: ' + more.map(function (s) { return (s.s ? '<a href="/trends/' + s.s + '">' + esc(s.d) + '</a>' : esc(s.d)) + ' (' + s.t.toLowerCase() + ')'; }).join(', ') + '</small>' : '') + '</td>' +
            '<td class="sell-w">' + (v.w.length ? v.w.map(function (w) { return esc(w.d) + (w.mv != null ? ' ' + pts(w.mv) : '') + ' <small>' + esc(w.g) + ' falling</small>'; }).join('<br>') : '<small>Nothing falling</small>') + '</td></tr>';
        }).join('') : '<tr><td colspan="6"><small>No venues match.</small></td></tr>') + '</tbody></table></div>' +
        (o.limit && all.length > rows.length ? '<p class="sell-more">Top ' + rows.length + ' of ' + all.length + ' venues. <a href="/partner/accounts?range=' + encodeURIComponent(cur.r) + '">Open the full rep sheet</a>: every venue, mark your own customers, print or download.</p>' : '');
      c.setTable([{ l: 'Venue', k: 'n' }, { l: 'Market', k: 'mk' }, { l: 'Town or city', k: 'c' }, { l: 'Address', k: 'ad' }, { l: 'Guests naming it', n: 1, k: 'g' },
        { l: 'Range', f: function () { return cur.r; } }, { l: 'Range score', n: 1, f: function (v) { return v.r[cur.r].x; } },
        { l: 'Lead dish', f: function (v) { return v.r[cur.r].s[0].d; } }, { l: 'Call', f: function (v) { return v.r[cur.r].s[0].t; } },
        { l: 'Times named here', n: 1, f: function (v) { return v.r[cur.r].s[0].k; } },
        { l: 'Other dishes', f: function (v) { return v.r[cur.r].s.slice(1).map(function (s) { return s.d + ' (' + s.t + ')'; }).join('; '); } },
        { l: 'Watch out', f: function (v) { return v.w.map(function (w) { return w.d; }).join('; '); } },
        { l: 'Guide award', k: 'aw' }, { l: 'Our customer', f: function (v) { return mine[v.p] ? 'yes' : ''; } }], all, 'dream-menu-where-to-sell-' + cur.r.toLowerCase().replace(/[^a-z]+/g, '-'));
      var hd = c.el.querySelector('.dmv-head h3'); if (hd && rows.length) hd.textContent = o.full ? 'Where to sell it: ' + cur.r.toLowerCase() + ', ' + (cur.m === 'All' ? 'all Scotland' : cur.m) : all[0].n + ' leads for ' + cur.r.toLowerCase() + (cur.m === 'All' ? '' : ' in ' + cur.m);
      if (o.full) c.plot.querySelectorAll('input[data-p]').forEach(function (i) { i.onchange = function () { if (i.checked) mine[i.dataset.p] = 1; else delete mine[i.dataset.p]; setOwn(mine); }; });
      if (o.onDraw) o.onDraw(cur, all.length);
    }
    V.chips(c.filters, ranges.map(function (r) { return [r, r]; }), cur.r, function (k) { cur.r = k; draw(); });
    V.chips(f2, [['All', 'All Scotland']].concat(MK.map(function (m) { return [m, m]; })), cur.m, function (k) { cur.m = k; draw(); });
    if (o.full) {
      var s = document.createElement('input'); s.type = 'search'; s.placeholder = 'Find a venue, street or town'; s.className = 'sell-q'; s.setAttribute('aria-label', 'Find a venue');
      s.oninput = function () { cur.q = s.value.trim().toLowerCase(); draw(); }; f2.appendChild(s);
      var m = document.createElement('div'); m.className = 'sell-mine'; f2.appendChild(m);
      V.chips(m, [['all', 'Every venue'], ['new', 'Not yet ours'], ['ours', 'Ours']], 'all', function (k) { cur.mine = k; draw(); });
    }
    draw();
  }

  function watch(host) {
    host.innerHTML = '<div class="mw">' + S.watch.map(function (w) {
      return '<div class="mw-tile"><h3>' + esc(w.title) + '</h3><p class="mw-ext">' + esc(w.ext) + ' <a href="' + esc(w.url) + '" rel="noopener">' + esc(w.who) + ', ' + esc(w.date) + '</a></p>' +
        '<p class="mw-dm"><b>Dream Menu:</b> ' + esc(w.dm) + '</p><p class="mw-do"><b>What to do:</b> ' + esc(w.do) + '</p></div>';
    }).join('') + '</div><p class="note">Outside figures as reported by their publishers, gathered ' + S.outside.split('-').reverse().join('/') + '; Dream Menu figures are live. The two are never mixed.</p>';
  }

  function start() {
    var g = function (id) { return document.getElementById(id); };
    if (g('th-sell')) sheet(g('th-sell'), { id: 'sell', limit: 12, claim: 'The venues to call first, range by range', title: 'Scottish venues guests name for dishes worth backing, with the reason for each call' });
    if (g('acct-sheet')) {
      var q = new URLSearchParams(location.search).get('range');
      sheet(g('acct-sheet'), { id: 'rep-sheet', full: true, range: S.ranges.some(function (R) { return R.r === q; }) ? q : null, claim: 'Where to sell it: the full rep sheet',
        title: S.v.length + ' Scottish venues guests name for dishes worth backing. Tick your own customers to see who is not yet one (kept in this browser only).',
        onDraw: function (cur, n) { var t = g('acct-print-h'); if (t) t.textContent = cur.r + ' · ' + (cur.m === 'All' ? 'All Scotland' : cur.m) + ' · ' + n + ' venues'; } });
    }
    var tries = 0;
    (function w() { var el = g('p-watch'); if (el) watch(el); else if (tries++ < 40) setTimeout(w, 150); })();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
