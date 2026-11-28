/* Dream Menu visuals (28 Nov 2026): one set of line icons across the site, and figures that count up when they
   come into view. Decorates the pages after they load, so every generated page picks it up without a rebuild.
   Icons are drawn for Dream Menu (24px grid, 1.8 stroke, currentColor), so they follow light and dark mode. */
(function(){
'use strict';
var doc=document;
var P={
  talk:'<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>',
  pin:'<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/>',
  shop:'<path d="M4 9h16l-1.5-5h-13z"/><path d="M5 9v11h14V9"/><path d="M10 20v-6h4v6"/><path d="M4 9c0 1.5 1.3 2.5 2.7 2.5S9.3 10.5 9.3 9c0 1.5 1.3 2.5 2.7 2.5s2.7-1 2.7-2.5c0 1.5 1.2 2.5 2.6 2.5S20 10.5 20 9"/>',
  city:'<path d="M3 21h18"/><path d="M5 21V8l5-3v16"/><path d="M10 21V10h9v11"/><path d="M13 13.5h3M13 17h3M7 10v.01M7 13v.01M7 16v.01"/>',
  globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.6 3.8 5.6 3.8 9S14.6 18.4 12 21c-2.6-2.6-3.8-5.6-3.8-9S9.4 5.6 12 3Z"/>',
  starter:'<path d="M3 12h18a9 9 0 0 1-18 0Z"/><path d="M9 4c-1 1 1 2 0 3.5M13 4c-1 1 1 2 0 3.5"/>',
  main:'<path d="M3 17h18"/><path d="M5 17a7 7 0 0 1 14 0"/><path d="M12 8V6.5M10.5 6.5h3M2 20h20"/>',
  side:'<path d="M6 10h12l-1.5 10h-9z"/><path d="M8 10 7 4M11 10V3.5M14 10l.5-6M16.5 10l1.5-5"/>',
  dessert:'<path d="M3 13 18 6l3 7z"/><path d="M3 13v6h18v-6"/><path d="M3 16h18"/><circle cx="17.5" cy="4" r="1.3"/>',
  drink:'<path d="M5 4h14l-7 8z"/><path d="M12 12v8M8 20h8"/><path d="M16 4l2-2"/>',
  list:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
  people:'<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 14.3c3 .2 5.5 2.4 5.5 5.7"/>',
  scale:'<path d="M12 3v18M7 21h10M5 6h14"/><path d="M5 6 2 13a3 3 0 0 0 6 0Z"/><path d="M19 6l-3 7a3 3 0 0 0 6 0Z"/>',
  shield:'<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  bulb:'<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3Z"/>',
  target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  trend:'<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
  map:'<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
  pie:'<path d="M12 3a9 9 0 1 0 9 9h-9z"/><path d="M15 2.5A8 8 0 0 1 21.5 9H15z"/>',
  trophy:'<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H4.5c0 3 1.5 4.5 3.7 4.8M16 6h3.5c0 3-1.5 4.5-3.7 4.8"/><path d="M12 13v4M8.5 21h7M9.5 17h5v4h-5z"/>',
  briefcase:'<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5h6v2M3 12.5h18"/>',
  calendar:'<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>'
};
function svg(k,cls){return '<svg class="dmi '+(cls||'')+'" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+P[k]+'</svg>'}
window.DM_ICON=svg;
function $$(s,c){return Array.prototype.slice.call((c||doc).querySelectorAll(s))}
function pick(t,map){t=(t||'').toLowerCase();for(var i=0;i<map.length;i++)if(map[i][0].test(t))return map[i][1];return null}

var COURSE=[[/starter/,'starter'],[/main/,'main'],[/side/,'side'],[/dessert/,'dessert'],[/drink|cocktail|soft|alcohol/,'drink']];
var STAT=[[/interview|guest/,'talk'],[/mention/,'pin'],[/venue|place/,'shop'],[/cit/,'city'],[/countr/,'globe'],[/answer|share|%/,'pie'],[/#|rank|dish$/,'trophy'],[/quarter|updated|data to/,'calendar']];
var TAG=[[/drink/,'drink'],[/menu/,'list'],[/venue/,'shop'],[/who|orders/,'people'],[/debate/,'scale'],[/outside|check|benchmark/,'shield'],[/supplier|sponsor|business/,'briefcase'],[/foodie|eat/,'pin']];
var PAGE={'/analysis/demand':'target','/analysis/change':'trend','/analysis/cities':'map','/analysis/trust':'shield','/analysis/partner':'briefcase'};

function decorate(){
  // home: the figures band and the dream menu card
  $$('.h-stats .wrap>div').forEach(function(d){var k=pick(d.textContent,STAT);if(k&&!d.querySelector('.dmi'))d.insertAdjacentHTML('afterbegin',svg(k,'dmi-stat'))});
  $$('.h-menu li .c, .ccard header .eyebrow').forEach(function(c){var k=pick(c.textContent,COURSE);if(k&&!c.querySelector('.dmi'))c.insertAdjacentHTML('afterbegin',svg(k,'dmi-inline'))});
  // finding cards and "pick your way in"
  $$('.hf-card .hf-tag').forEach(function(t){var k=pick(t.textContent,TAG);if(k&&!t.parentNode.querySelector('.dmi-badge')){var n=t.parentNode.querySelector('.hf-n');(n||t).insertAdjacentHTML('beforebegin','<span class="dmi-badge">'+svg(k)+'</span>')}});
  // dish, city and venue pages: the fact tiles
  $$('.pg-facts>div').forEach(function(d){var k=pick((d.querySelector('span')||d).textContent+' '+((d.querySelector('b')||{}).textContent||''),STAT);if(k&&!d.querySelector('.dmi'))d.insertAdjacentHTML('afterbegin',svg(k,'dmi-fact'))});
  $$('.pg-hero .eyebrow').forEach(function(e){var k=pick(e.textContent,COURSE);if(k&&!e.querySelector('.dmi'))e.insertAdjacentHTML('afterbegin',svg(k,'dmi-inline'))});
  // findings pages: a mark on the page title and on every "Use it to"
  var path=location.pathname.replace(/\.html$/,''), pk=PAGE[path];
  if(pk)$$('.iv-hero .iv-kick').forEach(function(k){if(!k.querySelector('.dmi'))k.insertAdjacentHTML('afterbegin',svg(pk,'dmi-inline'))});
  $$('.iv-do').forEach(function(d){if(!d.querySelector('.dmi'))d.insertAdjacentHTML('afterbegin',svg('bulb','dmi-do'))});
  $$('.hf-do').forEach(function(d){var b=d.querySelector('b');if(b&&!b.querySelector('.dmi'))b.insertAdjacentHTML('afterbegin',svg('bulb','dmi-inline'))});
}

/* figures count up once, when they first come into view (not for people who ask for reduced motion) */
function countUp(){
  if(!('IntersectionObserver' in window)||(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches))return;
  var els=$$('.h-stats b, .pg-facts b, .kpis b');
  var io=new IntersectionObserver(function(es){es.forEach(function(e){
    if(!e.isIntersecting)return; io.unobserve(e.target);
    var el=e.target, txt=el.textContent, m=txt.match(/^([^0-9]*)([0-9][0-9,]*\.?[0-9]*)(.*)$/);
    if(!m)return;
    var end=parseFloat(m[2].replace(/,/g,'')), dec=(m[2].split('.')[1]||'').length, comma=m[2].indexOf(',')>-1, t0=null, dur=900;
    if(!isFinite(end)||end===0)return;
    function f(v){var s=v.toFixed(dec);if(comma)s=s.replace(/\B(?=(\d{3})+(?!\d))/g,',');return m[1]+s+m[3]}
    function step(t){if(!t0)t0=t;var p=Math.min(1,(t-t0)/dur),q=1-Math.pow(1-p,3);el.textContent=f(end*q);if(p<1)requestAnimationFrame(step);else el.textContent=txt}
    requestAnimationFrame(step);
  })},{threshold:.6});
  els.forEach(function(e){io.observe(e)});
}
function run(){decorate();countUp()}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',run);else run();
})();
