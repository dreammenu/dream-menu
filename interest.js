/* interest.js: the "I'm interested in" filter (13 Nov 2026).
   Fills every <div data-interest="home|analysis">. Interests and their best pages come from
   INTERESTS in tools/build_nav.py (window.DM_NAV.ints). The choice lives in the link (?for=costs)
   and, as a convenience, in this browser. On /analysis it also shows only the sections tagged
   with that interest (data-i on each section; "all" always shows; untagged sections always show). */
(function () {
  var D = window.DM_NAV;
  if (!D || !D.ints) return;
  var IT = {}, INT = {};
  D.items.forEach(function (x) { IT[x.id] = x; });
  D.ints.forEach(function (i) { INT[i.k] = i; });
  var KEY = 'dm_interest';
  var LOCK = '<svg class="lock" viewBox="0 0 16 16" width="11" height="11" aria-label="Partners" role="img"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function read() {
    var m = location.search.match(/[?&]for=([a-z]+)/);
    if (m && (INT[m[1]] || m[1] === 'all')) return m[1];
    try { var v = localStorage.getItem(KEY); return INT[v] ? v : ''; } catch (e) { return ''; }
  }
  function save(k) {
    try { if (k) localStorage.setItem(KEY, k); else localStorage.removeItem(KEY); } catch (e) {}
    try {
      var u = new URL(location.href);
      if (k) u.searchParams.set('for', k); else u.searchParams.delete('for');
      history.replaceState(null, '', u.pathname + u.search + u.hash);
    } catch (e) {}
  }
  var boxes = Array.prototype.slice.call(document.querySelectorAll('[data-interest]'));
  if (!boxes.length) return;

  function card(x) {
    return '<li><a href="' + esc(x.u) + '"><b>' + esc(x.t) + (x.lock ? ' ' + LOCK : '') + '</b><span>' + esc(x.d) + '</span></a></li>';
  }
  var GL = {}; (D.groups || []).forEach(function (g, i) { GL[g.k] = { l: g.l, i: i }; });
  function grouped(items) {   // items sorted into the site's sections, in menu order
    var by = {};
    items.forEach(function (x) { (by[x.g] = by[x.g] || []).push(x); });
    return Object.keys(by).sort(function (a, b) { return (GL[a] || { i: 99 }).i - (GL[b] || { i: 99 }).i; }).map(function (g) {
      return '<div class="int-grp"><p class="int-gl">' + esc((GL[g] || { l: g }).l) + '</p><ul class="int-mini">' + by[g].map(function (x) {
        return '<li><a href="' + esc(x.u) + '">' + esc(x.t) + (x.lock ? ' ' + LOCK : '') + '</a></li>';
      }).join('') + '</ul></div>';
    }).join('');
  }
  function list(k, mode) {
    if (k === 'all') {   // the whole site, by section: every page is here
      var pages = D.items.filter(function (x) { return !x.p && x.u !== '/'; });
      return '<p class="int-h">Every page on Dream Menu, by section.</p><div class="int-grps">' + grouped(pages) + '</div>';
    }
    var I = INT[k];
    var here = function (x) { return !(mode === 'analysis' && x.u.indexOf('/analysis#') === 0) && x.u !== '/'; };
    var start = I.ids.map(function (id) { return IT[id]; }).filter(function (x) { return x && here(x); });
    var seen = {}; start.forEach(function (x) { seen[x.id] = 1; });
    var rest = D.items.filter(function (x) { return !seen[x.id] && here(x) && (x.n || []).indexOf(k) > -1; });
    var head = mode === 'analysis'
      ? '<p class="int-note">Showing the sections of this page about <b>' + esc(I.l.toLowerCase()) + '</b>. <button type="button" class="int-all">Show the whole page</button></p><p class="int-h">More on ' + esc(I.l.toLowerCase()) + ' across Dream Menu</p>'
      : '<p class="int-h">' + esc(I.d) + '. Start here:</p>';
    var more = rest.length ? '<details class="int-more"><summary>Everything on ' + esc(I.l.toLowerCase()) + ' <small>' + rest.length + ' more</small></summary><div class="int-grps">' + grouped(rest) + '</div></details>' : '';
    var foot = mode === 'home' && k !== 'about' ? '<p class="int-go"><a href="/analysis?for=' + k + '">Read the analysis for ' + esc(I.l.toLowerCase()) + ' &rarr;</a></p>' : '';
    return head + '<ul class="int-list">' + start.map(card).join('') + '</ul>' + more + foot;
  }

  function filterPage(k) {
    var secs = document.querySelectorAll('main [data-i]');
    var shown = 0;
    Array.prototype.forEach.call(secs, function (s) {
      var tags = (s.getAttribute('data-i') || '').split(' ');
      var on = !k || k === 'about' || tags.indexOf('all') > -1 || tags.indexOf(k) > -1;
      s.hidden = !on;
      if (on) shown++;
      if (s.id) Array.prototype.forEach.call(document.querySelectorAll('.onpage a[href="#' + s.id + '"]'), function (a) { a.style.display = on ? '' : 'none'; });
    });
    Array.prototype.forEach.call(document.querySelectorAll('main .iv-part'), function (p) { p.hidden = !!k; });
    return shown;
  }

  function apply(k) {
    boxes.forEach(function (box) {
      var mode = box.getAttribute('data-interest');
      Array.prototype.forEach.call(box.querySelectorAll('.int-chips button'), function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-k') === k ? 'true' : 'false'); });
      var out = box.querySelector('.int-out');
      out.innerHTML = k ? list(k, mode) : (mode === 'home' ? '<p class="int-h">Pick one and we&rsquo;ll point you to the findings, tools and reports that matter for it.</p>' : '');
      var all = out.querySelector('.int-all');
      if (all) all.onclick = function () { save(''); apply(''); };
      if (mode === 'analysis') filterPage(k === 'all' || k === 'about' ? '' : k);
    });
  }

  boxes.forEach(function (box) {
    var mode = box.getAttribute('data-interest');
    var lab = mode === 'analysis' ? 'Show me' : 'I&rsquo;m interested in';
    box.classList.add('int-box', 'int-' + mode);
    box.innerHTML = '<div class="int-chips" role="group" aria-label="Interested in"><span class="int-l">' + lab + '</span>'
      + (mode === 'analysis' ? '<button type="button" data-k="">Everything</button>' : '')
      + D.ints.filter(function (i) { return !(mode === 'analysis' && i.k === 'about'); }).map(function (i) { return '<button type="button" data-k="' + i.k + '">' + esc(i.l) + '</button>'; }).join('')
      + (mode === 'home' ? '<button type="button" data-k="all" class="int-every">Every page</button>' : '')
      + '</div><div class="int-out" aria-live="polite"></div>';
    box.addEventListener('click', function (e) {
      var b = e.target.closest('.int-chips button');
      if (!b) return;
      var k = b.getAttribute('data-k');
      if (mode === 'home' && b.getAttribute('aria-pressed') === 'true') k = '';
      save(k); apply(k);
    });
  });
  apply(read());
})();
