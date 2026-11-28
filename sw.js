/* Dream Menu app: service worker (28 Nov 2026).
   - Public pages: network first, so visitors always get the newest figures; the last copy is kept for offline use.
   - Scripts, styles, fonts and images: served from the cache straight away and refreshed in the background.
   - Partner and locked pages, sign-in, and partner data are never stored on the device.
   Bump VERSION when this file changes so old caches are cleared. */
var VERSION = 'dm-app-v1';
var PAGES = VERSION + '-pages', ASSETS = VERSION + '-assets';
var CORE = ['/', '/offline', '/site.css', '/brand.css', '/home.css', '/pages.css', '/app.css',
  '/nav-data.js', '/nav.js', '/dm-fresh.js', '/app.js', '/logo-128.png', '/app-icon-192.png',
  '/fonts/league-spartan-latin-800-normal.woff2', '/fonts/public-sans-latin-400-normal.woff2', '/fonts/public-sans-latin-700-normal.woff2'];
// Same list as middleware.js and the private headers in vercel.json: nothing here is ever cached
var PRIVATE = /^\/(briefing|onepager|review|geocoder|partner|report\/|operators|tested-ideas|insights|intelligence|case-studies|login|logout|open\/|_vercel)/;
var MAX_PAGES = 80;

self.addEventListener('install', function (e) {
  e.waitUntil(Promise.all([caches.open(PAGES), caches.open(ASSETS)]).then(function (cs) {
    return Promise.all(CORE.map(function (u) {
      var c = /\.[a-z0-9]+$/.test(u) ? cs[1] : cs[0];
      return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
    }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf(VERSION) !== 0; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

function storable(res) {
  if (!res || res.status !== 200 || res.type !== 'basic' || res.redirected) return false;
  var cc = res.headers.get('Cache-Control') || '';
  return !/private|no-store/.test(cc);
}
function trim(name, max) {
  caches.open(name).then(function (c) {
    c.keys().then(function (k) { if (k.length > max) c.delete(k[0]).then(function () { trim(name, max); }); });
  });
}
function cleanKey(url) { var u = new URL(url); u.search = ''; u.hash = ''; return u.toString(); }

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;
  var path = url.pathname.replace(/\.html$/, '');
  if (PRIVATE.test(path) || path === '/partner-data.js' || path === '/sw.js') return;

  if (req.mode === 'navigate') {
    var key = cleanKey(req.url);
    e.respondWith(fetch(req).then(function (res) {
      if (storable(res)) { var copy = res.clone(); caches.open(PAGES).then(function (c) { c.put(key, copy); trim(PAGES, MAX_PAGES); }); }
      return res;
    }).catch(function () {
      return caches.match(key).then(function (hit) { return hit || caches.match('/offline'); });
    }));
    return;
  }

  if (/\.(js|css|woff2|png|webp|jpe?g|svg|ico|webmanifest|json)$/.test(path)) {
    e.respondWith(caches.open(ASSETS).then(function (c) {
      return c.match(req).then(function (hit) {
        var net = fetch(req).then(function (res) { if (storable(res)) c.put(req, res.clone()); return res; });
        if (hit) { e.waitUntil(net.catch(function () {})); return hit; }
        return net;
      });
    }));
  }
});
