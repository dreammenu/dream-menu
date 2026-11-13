/* Dream Menu interactive tools: /menu-check (venues) and /my-dream-menu (food lovers).
   Data: pick-data.js (public shares only). Choices stay in the browser and in the page link. */
(function () {
  'use strict';
  var D = window.DM_PICK, host = document.querySelector('.tl');
  if (!D || !host) return;
  var mode = host.getAttribute('data-tool');
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function pc(v) { return (Math.round(v * 10) / 10).toFixed(1) + '%'; }
  function when() { var d = new Date(D.last + 'T00:00:00'); return d.getDate() + ' ' + ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][d.getMonth()] + ' ' + d.getFullYear(); }
  function info(t) { return '<details class="vinfo"><summary><span class="vi-i" aria-hidden="true">i</span>How to read this</summary><div class="vi-b">' + t.split('\n').map(function (p) { return '<p>' + p + '</p>'; }).join('') + '</div></details>'; }
  var FOOD = { s: 1, m: 1, d: 1, p: 1 };
  // state: course key -> array of slugs. Kept in the hash so a result can be shared or bookmarked.
  var st = {};
  D.courses.forEach(function (c) { st[c.k] = []; });
  (location.hash || '').replace(/^#/, '').split('&').forEach(function (kv) {
    var p = kv.split('='), c = D.courses.filter(function (x) { return x.k === p[0]; })[0];
    if (c && p[1]) st[c.k] = p[1].split('.').filter(function (s) { return c.items.some(function (i) { return i.s === s; }); });
  });
  function save() {
    var h = D.courses.filter(function (c) { return st[c.k].length; }).map(function (c) { return c.k + '=' + st[c.k].join('.'); }).join('&');
    try { history.replaceState(null, '', h ? '#' + h : location.pathname); } catch (e) { }
  }
  function opts(c, single) {
    return '<div class="tl-opts" role="group" aria-label="' + esc(c.label) + '">' + c.items.map(function (i) {
      return '<button type="button" class="tl-opt" data-c="' + c.k + '" data-s="' + i.s + '" aria-pressed="' + (st[c.k].indexOf(i.s) >= 0) + '">' + esc(i.l) + '<small>' + pc(i.p) + '</small></button>';
    }).join('') + '</div>';
  }
  function layout(intro) {
    host.innerHTML = '<div class="tl-grid"><div>' + D.courses.map(function (c) {
      return '<div class="tl-course"><h2>' + esc(c.label) + '</h2><p>' + intro(c) + '</p>' + opts(c) + '</div>';
    }).join('') + '</div><aside class="tl-out" id="tl-out" aria-live="polite"></aside></div>';
    host.addEventListener('click', function (e) {
      var b = e.target.closest('.tl-opt'); if (!b) return;
      var k = b.getAttribute('data-c'), s = b.getAttribute('data-s'), a = st[k], i = a.indexOf(s);
      if (mode === 'dream') st[k] = i >= 0 ? [] : [s]; else if (i >= 0) a.splice(i, 1); else a.push(s);
      [].forEach.call(host.querySelectorAll('.tl-opt[data-c="' + k + '"]'), function (x) { x.setAttribute('aria-pressed', st[k].indexOf(x.getAttribute('data-s')) >= 0); });
      save(); render();
    });
  }
  function copyLink(btn) {
    var done = function () { var t = btn.textContent; btn.textContent = 'Link copied'; setTimeout(function () { btn.textContent = t; }, 1600); };
    if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(done, function () { }); else prompt('Copy this link', location.href);
  }

  /* ---------------- Check my menu ---------------- */
  var MOVES = null;
  function renderCheck() {
    var out = document.getElementById('tl-out'), any = D.courses.some(function (c) { return st[c.k].length; });
    if (!any) { out.innerHTML = '<h2>Tick a few dishes to start</h2><p class="tl-mut">The figure beside each dish is its share of that course’s answers from ' + D.n.toLocaleString('en-GB') + ' interviews to ' + when() + '.</p>'; return; }
    var rows = '', cov = [], missSt = [], hasSt = [], gaps = [];
    D.courses.forEach(function (c) {
      var got = 0;
      c.items.forEach(function (i) {
        var on = st[c.k].indexOf(i.s) >= 0;
        if (on) got += i.p;
        if (i.st) (on ? hasSt : missSt).push(i.l + ' (' + c.label.toLowerCase() + ')');
        if (!on && FOOD[c.k] && st[c.k].length) gaps.push({ l: i.l, p: i.p, c: c.label.toLowerCase() });
      });
      if (st[c.k].length) { rows += '<li><span>' + esc(c.label) + '</span><span class="t"><i style="width:' + Math.min(100, got) + '%"></i></span><span class="v">' + Math.round(got) + '%</span></li>'; if (FOOD[c.k]) cov.push(got); }
    });
    var avg = cov.length ? cov.reduce(function (a, b) { return a + b; }, 0) / cov.length : 0;
    gaps.sort(function (a, b) { return b.p - a.p; });
    var verdict = !cov.length ? 'Drinks only so far' : avg >= 45 ? 'A crowd-pleasing menu' : avg >= 25 ? 'A balanced menu' : 'A specialist menu';
    var why = !cov.length ? 'Tick some food to get a read on the menu as a whole.' : avg >= 45 ? 'You cover most of what guests name. Your edge has to come from how well the favourites are made.' : avg >= 25 ? 'You cover the main favourites and leave room for your own dishes.' : 'You are choosing to stand apart from the favourites. That works when the concept is clear and the cooking earns it.';
    var h = '<h2>' + verdict + '</h2><p class="tl-mut">' + why + '</p>' +
      (cov.length ? '<div class="tl-big">' + Math.round(avg) + '%<small> of what guests name, across your food courses</small></div>' : '') +
      info('For each course, the bar adds up the shares of the dishes you ticked: it is the share of guests whose dream answer for that course is on your menu.\nA low figure is not a fault. It means the menu is specialised. Use the gaps list to decide whether any favourite is worth adding.') +
      '<ul class="tl-rows">' + rows + '</ul>';
    if (hasSt.length || missSt.length) h += '<h3>Steady staples</h3><p class="tl-mut">Dishes that hold their share in every quarter.</p>' +
      (hasSt.length ? '<p><b>On your menu:</b> ' + esc(hasSt.join(', ')) + '.</p>' : '') + (missSt.length ? '<p><b>Not ticked:</b> ' + esc(missSt.slice(0, 8).join(', ')) + '.</p>' : '');
    if (gaps.length) h += '<h3>Biggest gaps</h3><ol class="tl-list">' + gaps.slice(0, 5).map(function (g) { return '<li>' + esc(g.l) + ' <span class="tl-mut">' + pc(g.p) + ' of ' + g.c + ' answers</span></li>'; }).join('') + '</ol>';
    if (MOVES) {
      var up = [], dn = [];
      D.courses.forEach(function (c) { c.items.forEach(function (i) {
        if (!FOOD[c.k]) return;   // the drinks series restarted in August 2026: no movement to report yet
        var m = (MOVES.d[i.s] || []).filter(function (r) { return r.course === c.label && r.sig; })[0]; if (!m) return;
        var on = st[c.k].indexOf(i.s) >= 0;
        if (m.move > 0 && !on && st[c.k].length) up.push(i.l + ' (' + c.label.toLowerCase() + ', +' + m.move.toFixed(1) + ' pts)');
        if (m.move < 0 && on) dn.push(i.l + ' (' + c.label.toLowerCase() + ', ' + m.move.toFixed(1) + ' pts)');
      }); });
      h += '<h3>Partner view: movement</h3>' + (up.length ? '<p><b>Clearly rising, not on your menu:</b> ' + esc(up.join(', ')) + '.</p>' : '<p class="tl-mut">No clearly rising dish is missing from the courses you ticked.</p>') +
        (dn.length ? '<p><b>On your menu and clearly fading:</b> ' + esc(dn.join(', ')) + '.</p>' : '');
    } else h += '<p class="tl-lock"><b>Partners also see movement:</b> which missing dishes are clearly rising and which of yours are fading. <a href="/login?next=/menu-check">Partner sign-in</a></p>';
    h += '<div class="tl-acts"><button type="button" class="tl-btn" id="tl-copy">Copy link to this check</button><button type="button" class="tl-btn alt" onclick="window.print()">Print</button><a class="tl-btn alt" href="/operators">Operator toolkit</a></div>';
    out.innerHTML = h;
    document.getElementById('tl-copy').onclick = function () { copyLink(this); };
  }

  /* ---------------- Build your dream menu ---------------- */
  function pickOf(c) { return c.items.filter(function (i) { return i.s === st[c.k][0]; })[0]; }
  function twin() {
    var sc = D.markets.map(function () { return 0; }), n = 0;
    D.courses.forEach(function (c) { var p = pickOf(c); if (p && p.ci) { n++; p.ci.forEach(function (x, j) { if (x) sc[j] += Math.log(x / 100); }); } });
    if (n < 2) return null;
    var best = 0; sc.forEach(function (v, j) { if (v > sc[best]) best = j; });
    return sc[best] > 0.15 ? D.markets[best] : null;
  }
  function card(picks, title) {
    var W = 1080, H = 1350, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    var x = cv.getContext('2d');
    x.fillStyle = '#1c2152'; x.fillRect(0, 0, W, H);
    x.fillStyle = '#debd1a'; x.fillRect(80, 90, 120, 14);
    x.fillStyle = '#fff'; x.font = '800 40px Arial, Helvetica, sans-serif'; x.fillText('MY DREAM MENU', 80, 170);
    x.font = '800 78px Arial, Helvetica, sans-serif'; x.fillText(title, 80, 270);
    var y = 380;
    picks.forEach(function (p) {
      x.fillStyle = '#debd1a'; x.font = '700 26px Arial, Helvetica, sans-serif'; x.fillText(p.c.toUpperCase(), 80, y);
      x.fillStyle = '#fff'; x.font = '700 46px Arial, Helvetica, sans-serif';
      var t = p.l; while (x.measureText(t).width > W - 160 && t.length > 4) t = t.slice(0, -2); x.fillText(t === p.l ? t : t + '…', 80, y + 54);
      x.fillStyle = 'rgba(255,255,255,.7)'; x.font = '400 28px Arial, Helvetica, sans-serif'; x.fillText(pc(p.p) + ' of guests agree', 80, y + 94);
      y += 150;
    });
    x.fillStyle = 'rgba(255,255,255,.75)'; x.font = '400 28px Arial, Helvetica, sans-serif'; x.fillText('Build yours at dream-menu.com/my-dream-menu', 80, H - 80);
    return cv;
  }
  function renderDream() {
    var out = document.getElementById('tl-out'), picks = [];
    D.courses.forEach(function (c) { var p = pickOf(c); if (p) picks.push({ c: c.label, l: p.l, p: p.p, st: p.st, rank: c.items.indexOf(p) + 1 }); });
    if (!picks.length) { out.innerHTML = '<h2>Pick your first course</h2><p class="tl-mut">Choose one dish or drink for each course. Your result builds as you go.</p>'; return; }
    var avgRank = picks.reduce(function (a, p) { return a + p.rank; }, 0) / picks.length, done = picks.length === D.courses.length;
    var title = avgRank <= 3 ? 'The Crowd-Pleaser' : avgRank <= 6 ? 'Classic with a Twist' : avgRank <= 9 ? 'The Explorer' : 'The Trailblazer';
    var why = avgRank <= 3 ? 'You pick what most guests pick. You would get on with almost any table.' : avgRank <= 6 ? 'Mostly favourites, with a choice or two of your own.' : avgRank <= 9 ? 'You look past the obvious order more often than not.' : 'Few guests share your choices. You are ahead of the menu, or happily off it.';
    var tw = done ? twin() : null, stn = picks.filter(function (p) { return p.st; }).length;
    var h = '<p class="tl-mut">' + (done ? 'Your dream menu makes you' : picks.length + ' of ' + D.courses.length + ' chosen. So far you are') + '</p><h2>' + title + '</h2><p>' + why + '</p>' +
      '<ul class="tl-picks">' + picks.map(function (p) { return '<li><span>' + esc(p.c) + '</span><b>' + esc(p.l) + '</b><em>' + pc(p.p) + ' agree</em></li>'; }).join('') + '</ul>' +
      info('The figure beside each choice is the share of guests who named the same thing for that course. The title comes from how high your choices rank on average among the tracked dishes.\nIt is a bit of fun built on real answers, not a personality test.') +
      (stn ? '<p class="tl-mut">' + stn + ' of your choices ' + (stn === 1 ? 'is a steady staple' : 'are steady staples') + ': dishes that never go out of fashion.</p>' : '') +
      (tw ? '<p><b>You eat like ' + esc(tw) + '.</b> <span class="tl-mut">Your choices are named more there than elsewhere.</span></p>' : '');
    if (done) h += '<div class="tl-acts"><button type="button" class="tl-btn" id="tl-share">Share my menu</button><button type="button" class="tl-btn alt" id="tl-copy">Copy link</button><a class="tl-btn alt" href="/take-part">Make it count: take part</a></div><p class="tl-mut">This is for fun and is not saved. To add your answers to the research, take part.</p>';
    out.innerHTML = h;
    if (!done) return;
    document.getElementById('tl-copy').onclick = function () { copyLink(this); };
    document.getElementById('tl-share').onclick = function () {
      var cv = card(picks, title);
      cv.toBlob(function (b) {
        var f = new File([b], 'my-dream-menu.png', { type: 'image/png' });
        if (navigator.canShare && navigator.canShare({ files: [f] })) navigator.share({ files: [f], title: 'My dream menu', text: 'My dream menu: ' + title + '. Build yours at dream-menu.com/my-dream-menu' }).catch(function () { });
        else { var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'my-dream-menu.png'; a.click(); }
      });
    };
  }

  var render = mode === 'dream' ? renderDream : renderCheck;
  layout(mode === 'dream'
    ? function (c) { return 'Pick one. The figure is the share of guests who chose it.'; }
    : function (c) { return 'Tick everything you serve. ' + c.base.toLocaleString('en-GB') + ' answers for this course.'; });
  render();
  if (mode === 'check') {   // partner movement, only served after sign-in
    var s = document.createElement('script'); s.src = '/partner/dish-moves.js';
    s.onload = function () { if (window.DM_DISHMOVES) { MOVES = window.DM_DISHMOVES; render(); } };
    document.head.appendChild(s);
  }
})();
