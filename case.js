/* case.js: tooltips, contents highlighting, print button and library filters for /case-studies. */
(function () {
  'use strict';
  var tip = document.createElement('div');
  tip.className = 'cs-tip'; tip.setAttribute('role', 'status');
  document.addEventListener('DOMContentLoaded', function () { document.body.appendChild(tip); });
  function show(el, x, y) {
    tip.innerHTML = el.getAttribute('data-tip');
    tip.classList.add('on');
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var left = Math.min(Math.max(8, x + 14), window.innerWidth - w - 8);
    var top = y - h - 12 < 8 ? y + 18 : y - h - 12;
    tip.style.left = left + 'px'; tip.style.top = top + 'px';
  }
  function hide() { tip.classList.remove('on'); }
  document.addEventListener('mousemove', function (e) {
    var el = e.target.closest && e.target.closest('[data-tip]');
    if (el) show(el, e.clientX, e.clientY); else hide();
  });
  document.addEventListener('focusin', function (e) {
    var el = e.target.closest && e.target.closest('[data-tip]');
    if (!el) return hide();
    var r = el.getBoundingClientRect(); show(el, r.left + r.width / 2, r.top);
  });
  document.addEventListener('focusout', hide);
  window.addEventListener('scroll', hide, { passive: true });

  document.addEventListener('DOMContentLoaded', function () {
    // print / save as PDF
    document.querySelectorAll('[data-print]').forEach(function (b) {
      b.addEventListener('click', function () {
        document.querySelectorAll('.ex-data').forEach(function (d) { d.setAttribute('open', ''); });
        window.print();
      });
    });
    // contents: highlight the section in view
    var links = document.querySelectorAll('.cs-toc a');
    if (links.length && 'IntersectionObserver' in window) {
      var map = {};
      links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting) {
            links.forEach(function (a) { a.removeAttribute('aria-current'); });
            var a = map[e.target.id]; if (a) a.setAttribute('aria-current', 'true');
          }
        });
      }, { rootMargin: '-30% 0px -60% 0px' });
      Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
    }
    // library filter
    var bar = document.querySelector('.lib-filter');
    if (bar) bar.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      bar.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      var f = b.getAttribute('data-f');
      document.querySelectorAll('.lib a').forEach(function (a) {
        a.hidden = f !== 'all' && (' ' + a.getAttribute('data-for') + ' ').indexOf(' ' + f + ' ') < 0;
      });
    });
  });
})();
