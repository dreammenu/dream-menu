/* Dream Menu app (28 Nov 2026): makes the site installable and app-like on phones.
   1. Registers the service worker (sw.js) for offline use.
   2. When opened from the home screen: an app tab bar at the bottom of the screen.
   3. In a phone browser: a small "Add Dream Menu to your home screen" banner (Android install button, iPhone instructions).
   4. A note when the connection drops. */
(function(){
'use strict';
var doc=document, root=doc.documentElement, w=window;
function store(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}}
function sess(k,v){try{if(v===undefined)return sessionStorage.getItem(k);sessionStorage.setItem(k,v)}catch(e){return null}}
var path=location.pathname.replace(/\.html$/,'').replace(/\/index$/,'').replace(/\/$/,'')||'/';
var standalone=(w.matchMedia&&w.matchMedia('(display-mode: standalone)').matches)||w.navigator.standalone===true;
var ua=navigator.userAgent||'';
var ios=/iPhone|iPad|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
var iosSafari=ios&&/Safari/.test(ua)&&!/CriOS|FxiOS|EdgiOS|OPiOS|GSA|Instagram|FBAN|FBAV/.test(ua);
var phone=w.matchMedia&&w.matchMedia('(max-width: 900px)').matches;
var track=function(n,p){try{if(w.va)w.va('event',{name:n,data:p||{}})}catch(e){}};

/* 1. offline support */
if('serviceWorker' in navigator&&w.isSecureContext){
  w.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){})});
}

/* 2. app tab bar */
var TABS=[
  {t:'Home',u:'/',on:/^\/$/,i:'<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/>'},
  {t:'Findings',u:'/analysis/demand',on:/^\/(analysis|quarterly|report|case-studies|briefing|partner)/,i:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'},
  {t:'Dishes',u:'/trends',on:/^\/(trends|my-dream-menu|specials|menu-check)/,i:'<path d="M4 15a8 8 0 0 1 16 0"/><path d="M2 15h20M12 7V5M10 5h4M3 19h18"/>'},
  {t:'Map',u:'/map',on:/^\/(map|cities|city|venue|rankings|area)/,i:'<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/>'},
  {t:'Search',u:'#search',search:1,i:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>'}
];
function tabBar(){
  if(doc.querySelector('.apptabs'))return;
  var n=doc.createElement('nav'); n.className='apptabs'; n.setAttribute('aria-label','App');
  n.innerHTML=TABS.map(function(t){
    var cur=t.on&&t.on.test(path);
    return '<a href="'+t.u+'"'+(t.search?' data-app-search':'')+(cur?' aria-current="page" class="on"':'')+'><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+t.i+'</svg><span>'+t.t+'</span></a>';
  }).join('');
  doc.body.appendChild(n);
  var s=n.querySelector('[data-app-search]');
  s.addEventListener('click',function(e){
    e.preventDefault();
    var b=doc.querySelector('[data-search]');
    if(b)b.click(); else location.href='/trends';
  });
}
if(standalone){
  root.classList.add('is-app');
  if(/[?&]source=app/.test(location.search))track('App opened');
}

/* 3. install banner, phones in a browser only */
var deferred=null, SNOOZE='dm_app_snooze';
function snoozed(){var t=+store(SNOOZE)||0;return Date.now()-t<30*864e5}
function banner(mode){
  if(standalone||snoozed()||doc.querySelector('.appbanner')||/^\/(login|logout|offline|app)$/.test(path))return;
  var b=doc.createElement('div'); b.className='appbanner'; b.setAttribute('role','dialog'); b.setAttribute('aria-label','Get the Dream Menu app');
  var how=mode==='ios'
    ?'<p>Tap <b>Share</b> <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M8 7l4-4 4 4"/><path d="M5 11v9h14v-9"/></svg> then <b>Add to Home Screen</b>.</p>'
    :'<p>Findings, dish trends and the venue map, one tap away. Free, no app store.</p>';
  b.innerHTML='<img src="/app-icon-192.png" alt="" width="44" height="44"><div class="ab-txt"><b>Get the Dream Menu app</b>'+how+'</div>'
    +(mode==='ios'?'':'<button type="button" class="ab-go">Install</button>')
    +'<button type="button" class="ab-x" aria-label="Not now">&times;</button>';
  doc.body.appendChild(b);
  requestAnimationFrame(function(){b.classList.add('in')});
  track('App banner shown',{mode:mode});
  b.querySelector('.ab-x').onclick=function(){store(SNOOZE,String(Date.now()));b.remove()};
  var go=b.querySelector('.ab-go');
  if(go)go.onclick=function(){
    if(!deferred)return;
    deferred.prompt();
    deferred.userChoice.then(function(r){track('App install choice',{outcome:r.outcome});if(r.outcome!=='accepted')store(SNOOZE,String(Date.now()))});
    deferred=null; b.remove();
  };
}
// show it on the second page of a visit, or after 20 seconds on the first, so it never greets a first-time reader
var views=(+sess('dm_views')||0)+1; sess('dm_views',String(views));
function when(fn){ if(views>=2)setTimeout(fn,1500); else setTimeout(fn,20000); }
w.addEventListener('beforeinstallprompt',function(e){
  e.preventDefault(); deferred=e; w.DM_INSTALL=e;
  doc.dispatchEvent(new Event('dm-installable'));
  if(phone)when(function(){banner('android')});
});
if(iosSafari&&!standalone&&phone)when(function(){banner('ios')});
w.addEventListener('appinstalled',function(){track('App installed');var b=doc.querySelector('.appbanner');if(b)b.remove()});

/* 4. connection note */
function note(on){
  var n=doc.querySelector('.appnet');
  if(!n){n=doc.createElement('div');n.className='appnet';n.setAttribute('role','status');doc.body.appendChild(n)}
  n.textContent=on?'Back online':'You are offline. Pages you have opened before still work.';
  n.classList.toggle('ok',on); n.classList.add('in');
  clearTimeout(n._t); if(on)n._t=setTimeout(function(){n.classList.remove('in')},2500);
}
w.addEventListener('offline',function(){note(false)});
w.addEventListener('online',function(){note(true)});

function ready(){ if(standalone)tabBar(); if(!navigator.onLine)note(false); }
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',ready); else ready();
})();
