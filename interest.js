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
    if (m && INT[m[1]]) return m[1];
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

  function list(k, mode) {
    var I = INT[k];
    var ids = I.ids.filter(function (id) { return IT[id] && !(mode === 'analysis' && IT[id].u.indexOf('/analysis#') === 0); });
    var cards = ids.map(function (id) {
      var x = IT[id];
      return '<li><a href="' + esc(x.u) + '"><b>' + esc(x.t) + (x.lock ? ' ' + LOCK : '') + '</b><span>' + esc(x.d) + '</span></a></li>';
    }).join('');
    var head = mode === 'analysis'
      ? '<p class="int-note">Showing the sections of this page about <b>' + esc(I.l.toLowerCase()) + '</b>. <button type="button" class="int-all">Show the whole page</button></p><p class="int-h">More on ' + esc(I.l.toLowerCase()) + ' across Dream Menu</p>'
      : '<p class="int-h">' + esc(I.d) + '. Start here:</p>';
    var foot = mode === 'home' ? '<p class="int-go"><a href="/analysis?for=' + k + '">Read the analysis for ' + esc(I.l.toLowerCase()) + ' &rarr;</a></p>' : '';
    return head + '<ul class="int-list">' + cards + '</ul>' + foot;
  }

  function filterPage(k) {
    var secs = document.querySelectorAll('main [data-i]');
    var shown = 0;
    Array.prototype.forEach.call(secs, function (s) {
      var tags = (s.getAttribute('data-i') || '').split(' ');
      var on = !k || tags.indexOf('all') > -1 || tags.indexOf(k) > -1;
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
      if (mode === 'analysis') filterPage(k);
    });
  }

  boxes.forEach(function (box) {
    var mode = box.getAttribute('data-interest');
    var lab = mode === 'analysis' ? 'Show me' : 'I&rsquo;m interested in';
    box.classList.add('int-box', 'int-' + mode);
    box.innerHTML = '<div class="int-chips" role="group" aria-label="Interested in"><span class="int-l">' + lab + '</span>'
      + (mode === 'analysis' ? '<button type="button" data-k="">Everything</button>' : '')
      + D.ints.map(function (i) { return '<button type="button" data-k="' + i.k + '">' + esc(i.l) + '</button>'; }).join('')
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
