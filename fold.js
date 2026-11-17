/* Dream Menu: shortens the analysis page (17 Nov 2026). Secondary charts and long lists are shown at a set height
   with a "Show all" button; the first chart in each question stays open. The content is drawn at full width first
   and only clipped, so charts keep their size. A link to anything inside a folded block opens it.
   Which blocks fold: FOLD (every screen) and PHONE (phones only, under 720px). */
(function () {
  var FOLD = ['th-life', 'th-drinks', 'c-critics', 'ranges', 'c-matrix', 'th-fan', 'c-ops', 'term', 'method-list'];
  var PHONE = ['th-cats', 'c-opp', 'th-bench', 'th-audit'];
  var phone = window.matchMedia && matchMedia('(max-width:720px)').matches;
  var css = document.createElement('style');
  css.textContent = '.dm-fold{position:relative;max-height:var(--fh,440px);overflow:hidden}'
    + '.dm-fold::after{content:"";position:absolute;left:0;right:0;bottom:0;height:90px;background:linear-gradient(rgba(255,255,255,0),var(--bg,#fff));pointer-events:none}'
    + '.dm-fold-b{display:inline-flex;align-items:center;gap:8px;margin:12px 0 4px;padding:9px 16px;border:1px solid currentColor;border-radius:999px;background:none;font:700 14px/1.2 var(--body,inherit);color:inherit;cursor:pointer}'
    + '.dm-fold-b:focus-visible{outline:3px solid #debd1a;outline-offset:2px}';
  document.head.appendChild(css);

  function fold(el) {
    if (el && el.tagName === 'SECTION') el = el.querySelector('.wrap') || el;
    if (!el || el.dataset.folded || el.offsetHeight < (phone ? 560 : 700)) return;
    el.dataset.folded = '1';
    el.style.setProperty('--fh', (phone ? 380 : 460) + 'px');
    var bg = getComputedStyle(el.closest('section') || document.body).backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)') el.style.setProperty('--bg', bg);
    el.classList.add('dm-fold');
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'dm-fold-b'; b.setAttribute('aria-expanded', 'false');
    var label = el.getAttribute('data-fold') || 'Show all';
    b.textContent = label;
    b.addEventListener('click', function () {
      var open = el.classList.toggle('dm-fold');
      b.setAttribute('aria-expanded', open ? 'false' : 'true');
      b.textContent = open ? label : 'Show less';
      if (open) el.scrollIntoView({ block: 'nearest' });
    });
    el.parentNode.insertBefore(b, el.nextSibling);
  }
  function openFor(t) {
    for (var e = t; e; e = e.parentElement) if (e.classList && e.classList.contains('dm-fold')) {
      e.classList.remove('dm-fold');
      var b = e.nextSibling; if (b && b.className === 'dm-fold-b') { b.textContent = 'Show less'; b.setAttribute('aria-expanded', 'true'); }
    }
  }
  function run() {
    FOLD.concat(phone ? PHONE : []).forEach(function (id) { fold(document.getElementById(id)); });
    var t = location.hash && document.getElementById(location.hash.slice(1));
    if (t) { openFor(t); var n = document.getElementById(location.hash.slice(1)); if (n) n.scrollIntoView(); }
  }
  addEventListener('hashchange', function () { var t = document.getElementById(location.hash.slice(1)); if (t) { openFor(t); t.scrollIntoView(); } });
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a) return;
    var t = document.getElementById(a.getAttribute('href').slice(1)); if (t) openFor(t);
  });
  // charts are drawn after load, and partner sections after sign-in data arrives: fold once each settles
  addEventListener('load', function () { setTimeout(run, 900); setTimeout(run, 2500); });
})();
