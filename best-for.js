/* best-for.js: the "Best for" tabs on city and neighbourhood guides (21 Nov 2026).
   Without JavaScript every panel shows; with it, one panel shows at a time. ?dish=seafood or #bf-seafood opens that panel. */
(function(){
var box=document.querySelector('#best-for .bf');if(!box)return;
var tabs=[].slice.call(box.querySelectorAll('.bf-tabs [data-bf]')),panels=[].slice.call(box.querySelectorAll('.bf-p'));
if(!tabs.length)return;
function show(g,push){
  if(!panels.some(function(p){return p.dataset.bf===g}))g=tabs[0].dataset.bf;
  panels.forEach(function(p){p.classList.toggle('on',p.dataset.bf===g)});
  tabs.forEach(function(t){t.setAttribute('aria-pressed',t.dataset.bf===g?'true':'false')});
  if(push){try{var q=new URLSearchParams(location.search);q.set('dish',g);history.replaceState(null,'',location.pathname+'?'+q.toString()+'#best-for')}catch(e){}}
}
tabs.forEach(function(t){t.addEventListener('click',function(){show(t.dataset.bf,true)})});
var start='';
try{start=new URLSearchParams(location.search).get('dish')||''}catch(e){}
var h=(location.hash||'').match(/^#bf-(.+)$/);if(h)start=h[1];
show(start,false);
if(start&&!h&&location.hash!=='#best-for'){var s=document.getElementById('best-for');if(s)s.scrollIntoView()}
})();
