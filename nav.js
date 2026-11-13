/* Dream Menu site navigation: menus, "I'm a..." audience picker, search, on-page jump bars, Explore page.
   Menu content comes from nav-data.js, which tools/build_nav.py generates. */
(function(){
'use strict';
var D=window.DM_NAV||{aud:[],groups:[],items:[]};
var doc=document, root=doc.documentElement;
var desk=window.matchMedia('(min-width: 1081px)');
var hoverable=window.matchMedia('(hover: hover) and (pointer: fine)');
function $(s,c){return (c||doc).querySelector(s)}
function $$(s,c){return Array.prototype.slice.call((c||doc).querySelectorAll(s))}
function esc(t){return String(t).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function store(k,v){try{if(v===undefined)return localStorage.getItem(k);if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(e){return null}}
var AUD={};D.aud.forEach(function(a){AUD[a.k]=a});
var ITEM={};D.items.forEach(function(i){ITEM[i.id]=i});
var GROUP={};D.groups.forEach(function(g){GROUP[g.k]=g});
var LOCK='<svg class="lock" viewBox="0 0 16 16" width="12" height="12" aria-label="Sign in needed" role="img"><path fill="currentColor" d="M4 7V5a4 4 0 1 1 8 0v2h1v8H3V7h1Zm2 0h4V5a2 2 0 1 0-4 0v2Z"/></svg>';

/* ---------- header menus ---------- */
var nav=$('#mnav'), burger=$('.mburger'), items=$$('.mnav-item'), openItem=null, hoverT=null;
function setOpen(li,on){
  if(!li)return;
  var a=$('.mnav-top',li);
  li.classList.toggle('open',on); a.setAttribute('aria-expanded',on?'true':'false');
  if(on){ if(openItem&&openItem!==li&&desk.matches)setOpen(openItem,false); openItem=li; }
  else if(openItem===li){ openItem=null; }
  root.classList.toggle('menu-open',!!(openItem&&desk.matches));
}
function closeAll(){items.forEach(function(li){setOpen(li,false)})}
items.forEach(function(li){
  var a=$('.mnav-top',li);
  a.addEventListener('click',function(e){
    e.preventDefault();
    setOpen(li,!li.classList.contains('open'));
  });
  a.addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'&&desk.matches){e.preventDefault();setOpen(li,true);var f=$('.mpanel a, .mpanel button[aria-selected="true"]',li);if(f)f.focus();}
  });
  li.addEventListener('mouseenter',function(){if(!desk.matches||!hoverable.matches)return;clearTimeout(hoverT);hoverT=setTimeout(function(){setOpen(li,true)},openItem?0:110)});
  li.addEventListener('mouseleave',function(){if(!desk.matches||!hoverable.matches)return;clearTimeout(hoverT);hoverT=setTimeout(function(){setOpen(li,false)},220)});
});
doc.addEventListener('click',function(e){if(desk.matches&&openItem&&!openItem.contains(e.target))closeAll()});
doc.addEventListener('keydown',function(e){
  if(e.key!=='Escape')return;
  if(openItem){var a=$('.mnav-top',openItem);setOpen(openItem,false);a.focus();}
  else if(nav&&nav.classList.contains('open')){toggleDrawer(false);burger.focus();}
});
doc.addEventListener('focusin',function(e){if(desk.matches&&openItem&&!openItem.contains(e.target))setOpen(openItem,false)});

/* mobile drawer */
function toggleDrawer(on){
  if(!nav)return;
  if(on&&!$('.mdrawer-head',nav)){
    var h=doc.createElement('div');h.className='mdrawer-head';
    h.innerHTML='<b>Menu</b><div><button type="button" class="md-search" aria-label="Search the site"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Search</button><button type="button" class="md-close">Close <span aria-hidden="true">&times;</span></button></div>';
    nav.insertBefore(h,nav.firstChild);
    $('.md-close',h).addEventListener('click',function(){toggleDrawer(false);burger.focus()});
    $('.md-search',h).addEventListener('click',function(){openSearch()});
  }
  nav.classList.toggle('open',on); burger.setAttribute('aria-expanded',on?'true':'false');
  root.classList.toggle('drawer-open',on);
  if(!on)closeAll(); else {var c=$('.md-close',nav); if(c)c.focus();}
}
if(burger)burger.addEventListener('click',function(){toggleDrawer(!nav.classList.contains('open'))});
desk.addEventListener&&desk.addEventListener('change',function(){toggleDrawer(false);closeAll()});

/* audience tabs */
var tabs=$$('.aud-tabs [role="tab"]');
function pickAud(k,save){
  if(!AUD[k])return;
  tabs.forEach(function(t){var on=t.dataset.aud===k;t.setAttribute('aria-selected',on?'true':'false');t.tabIndex=on?0:-1;var p=doc.getElementById(t.getAttribute('aria-controls'));if(p)p.hidden=!on;});
  if(save){store('dm-aud',k);markAud(k);}
}
function markAud(k){
  var top=$('.mnav-aud .mnav-top span');
  if(top)top.innerHTML=k&&AUD[k]?'For <i>'+esc(AUD[k].sh)+'</i>':'I&rsquo;m a&hellip;';
  $$('.audtile').forEach(function(t){t.classList.toggle('mine',t.dataset.aud===k)});
}
tabs.forEach(function(t,n){
  t.addEventListener('click',function(){pickAud(t.dataset.aud,true)});
  t.addEventListener('mouseenter',function(){if(desk.matches&&hoverable.matches)pickAud(t.dataset.aud,false)});
  t.addEventListener('keydown',function(e){
    var d={ArrowDown:1,ArrowRight:1,ArrowUp:-1,ArrowLeft:-1}[e.key];if(!d)return;e.preventDefault();
    var nx=tabs[(n+d+tabs.length)%tabs.length];nx.focus();pickAud(nx.dataset.aud,false);
  });
});
var saved=store('dm-aud');
if(saved&&AUD[saved]){pickAud(saved,false);markAud(saved);}
$$('.audtile').forEach(function(t){t.addEventListener('click',function(){store('dm-aud',t.dataset.aud)})});

/* ---------- search ---------- */
var dlg=null, results=[], sel=0;
function itemAud(i){return i.a||[]}
function score(i,toks,aud){
  if(!toks.length)return 0;
  var t=norm(i.t), d=norm(i.d), kw=norm(i.k||''), par=i.p&&ITEM[i.p]?ITEM[i.p].t.toLowerCase():'', g=((GROUP[i.g]||{}).l||'').toLowerCase(), s=0;
  for(var n=0;n<toks.length;n++){
    var w=toks[n], hit=0;
    if(t.indexOf(w)===0)hit=6;else if(t.indexOf(w)>=0)hit=4;
    else if(kw.indexOf(w)>=0)hit=3;else if(d.indexOf(w)>=0)hit=2;else if(par.indexOf(w)>=0||g.indexOf(w)>=0)hit=1;
    if(!hit)return 0; s+=hit;
  }
  if(aud&&itemAud(i).indexOf(aud)>=0)s+=3;   /* who you are sorts results, it never hides them */
  return s+(i.s?1:0);
}
function norm(q){return q.toLowerCase().replace(/[\u2018\u2019']/g,'').replace(/-/g,' ')}
function rowHtml(i,n){
  var par=i.p&&ITEM[i.p]?ITEM[i.p].t:(GROUP[i.g]||{}).l;
  return '<li role="option" id="sr-'+n+'" aria-selected="'+(n===sel)+'"><a href="'+i.u+'" tabindex="-1"><span class="sr-where">'+esc(par||'')+'</span><b>'+esc(i.t)+(i.lock?' '+LOCK:'')+'</b><span>'+esc(i.d)+'</span></a></li>';
}
function runSearch(){
  var q=norm($('#srQ').value.trim()), aud=$('#srAud').value, list=$('#srList'), head=$('#srHead');
  var toks=q.split(/\s+/).filter(Boolean);
  if(!toks.length){
    var ids=aud&&AUD[aud]?AUD[aud].picks:D.items.filter(function(i){return i.s}).slice(0,8).map(function(i){return i.id});
    results=ids.map(function(id){return ITEM[id]});
    head.textContent=aud&&AUD[aud]?'Start here for '+AUD[aud].p:'Popular on Dream Menu';
  }else{
    results=D.items.map(function(i){return [score(i,toks,aud),i]}).filter(function(x){return x[0]>0}).sort(function(a,b){return b[0]-a[0]}).slice(0,12).map(function(x){return x[1]});
    head.textContent=results.length?results.length+(results.length===1?' result':' results')+(aud&&AUD[aud]?', most useful for '+AUD[aud].p+' first':''):'No matches. Try another word, or browse everything below.';
  }
  sel=0; list.innerHTML=results.map(rowHtml).join('');
  $('#srQ').setAttribute('aria-activedescendant',results.length?'sr-0':'');
}
function moveSel(d){
  if(!results.length)return; sel=(sel+d+results.length)%results.length;
  $$('#srList li').forEach(function(li,n){li.setAttribute('aria-selected',n===sel?'true':'false')});
  var li=doc.getElementById('sr-'+sel); if(li){li.scrollIntoView({block:'nearest'});$('#srQ').setAttribute('aria-activedescendant','sr-'+sel);}
}
function buildDialog(){
  dlg=doc.createElement('dialog'); dlg.className='srdlg'; dlg.setAttribute('aria-label','Search Dream Menu');
  var opts='<option value="">Anyone</option>'+D.aud.map(function(a){return '<option value="'+a.k+'">'+esc(a.l)+'</option>'}).join('');
  dlg.innerHTML='<div class="sr-box"><div class="sr-top"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'+
    '<input id="srQ" type="search" placeholder="Search dishes, tools, report sections&hellip;" autocomplete="off" role="combobox" aria-expanded="true" aria-controls="srList" aria-label="Search Dream Menu">'+
    '<button type="button" class="sr-close" aria-label="Close search">Esc</button></div>'+
    '<div class="sr-filter"><label for="srAud">Sort for: I&rsquo;m a&hellip;</label><select id="srAud">'+opts+'</select></div>'+
    '<p class="sr-head" id="srHead" aria-live="polite"></p><ul class="sr-list" id="srList" role="listbox" aria-label="Results"></ul>'+
    '<p class="sr-foot"><a href="/explore">Browse everything, sorted by who you are &rarr;</a><span><kbd>&uarr;</kbd><kbd>&darr;</kbd> to move, <kbd>Enter</kbd> to open</span></p></div>';
  doc.body.appendChild(dlg);
  $('#srQ').addEventListener('input',runSearch);
  $('#srAud').addEventListener('change',function(){store('dm-aud',this.value||null);markAud(this.value);if(this.value)pickAud(this.value,false);runSearch();$('#srQ').focus();});
  $('#srQ').addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'){e.preventDefault();moveSel(1)}
    else if(e.key==='ArrowUp'){e.preventDefault();moveSel(-1)}
    else if(e.key==='Enter'&&results[sel]){e.preventDefault();go(results[sel].u)}
    else if(e.key==='Escape'){e.preventDefault();dlg.close()}
  });
  $('.sr-close',dlg).addEventListener('click',function(){dlg.close()});
  dlg.addEventListener('click',function(e){if(e.target===dlg)dlg.close()});
  dlg.addEventListener('close',function(){root.classList.remove('search-open')});
  $('#srList').addEventListener('click',function(e){var a=e.target.closest('a');if(a){e.preventDefault();go(a.getAttribute('href'))}});
}
function go(u){if(dlg&&dlg.open)dlg.close();var here=location.pathname.replace(/\.html$/,'')||'/';var p=u.split('#');if((p[0]||'/')===here&&p[1]){location.hash=p[1];}else location.href=u;}
function openSearch(){
  if(!dlg)buildDialog();
  closeAll();toggleDrawer(false);
  var a=store('dm-aud');$('#srAud').value=a&&AUD[a]?a:'';
  if(typeof dlg.showModal==='function')dlg.showModal();else dlg.setAttribute('open','');
  root.classList.add('search-open');$('#srQ').value='';runSearch();$('#srQ').focus();
}
$$('[data-search]').forEach(function(b){b.addEventListener('click',openSearch)});
doc.addEventListener('keydown',function(e){
  var t=e.target, typing=t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.tagName==='SELECT'||t.isContentEditable);
  if((e.key==='/'&&!typing)||((e.metaKey||e.ctrlKey)&&(e.key==='k'||e.key==='K'))){e.preventDefault();openSearch();}
});

/* ---------- "On this page" jump bars ---------- */
(function(){
  var main=$('main'); if(!main||$('.jump',main)||doc.body.classList.contains('no-onpage'))return;
  function label(h){return (h.getAttribute('data-short')||h.textContent).replace(/\s+/g,' ').trim()}
  var hs=$$('h2',main).filter(function(h){return h.id||(h.closest('section')&&h.closest('section').id&&$('h2',h.closest('section'))===h)});
  if(hs.length<3)hs=$$('h3[id]',main);
  if(hs.length<3)return;
  var links=hs.slice(0,18).map(function(h){var id=h.id||h.closest('section').id;return '<a href="#'+id+'">'+esc(label(h))+'</a>'}).join('');
  var bar=doc.createElement('nav'); bar.className='jump onpage'; bar.setAttribute('aria-label','On this page');
  bar.innerHTML='<div class="wrap"><span class="onpage-l">On this page</span>'+links+'</div>';
  var sub=$('.subnav',main), first=main.firstElementChild;
  var after=sub||(first&&first.tagName==='SECTION'?first:null);
  if(!after&&first&&first.classList.contains('confidential')){var nx=first.nextElementSibling;after=nx&&nx.tagName==='SECTION'?nx:first;}
  if(after&&after.nextElementSibling&&after.nextElementSibling.classList.contains('h-stats'))after=after.nextElementSibling;
  if(after)after.insertAdjacentElement('afterend',bar);
})();

/* ---------- Explore page ---------- */
(function(){
  var q=$('#exQ'); if(!q)return;
  var selA=$('#exAud'), cards=$$('.ex-card'), groups=$$('.ex-group'), chips=$('#exChips');
  D.aud.forEach(function(a){var o=doc.createElement('option');o.value=a.k;o.textContent=a.l;selA.appendChild(o)});
  chips.innerHTML=groups.map(function(g){var k=g.dataset.g;return '<a href="#g-'+k+'">'+esc(GROUP[k].l)+' <b data-c="'+k+'"></b></a>'}).join('');
  var prm=new URLSearchParams(location.search);
  var a0=prm.get('for')||store('dm-aud')||''; if(AUD[a0])selA.value=a0;
  q.value=prm.get('q')||'';
  function picks(a){
    var w=$('#exPicksWrap');
    if(!a||!AUD[a]){w.hidden=true;return}
    w.hidden=false; $('#exPicksH').textContent='Start here: the best for '+AUD[a].p;
    $('#exPicks').innerHTML=AUD[a].picks.map(function(id,n){var i=ITEM[id];return '<a class="ex-pick" href="'+i.u+'"><span class="n">'+(n+1)+'</span><b>'+esc(i.t)+(i.lock?' '+LOCK:'')+'</b><span>'+esc(i.d)+'</span><em>'+esc((GROUP[i.g]||{}).l||'')+'</em></a>'}).join('');
  }
  function apply(push){
    var a=selA.value, toks=norm(q.value.trim()).split(/\s+/).filter(Boolean), total=0;
    function ok(el,useSelf){var au=(useSelf?el.dataset.self:el.dataset.aud)||'';var txt=el.dataset.text||'';
      if(a&&(' '+au+' ').indexOf(' '+a+' ')<0)return false;
      for(var i=0;i<toks.length;i++)if(txt.indexOf(toks[i])<0)return false;return true;}
    var filtered=!!(a||toks.length);
    cards.forEach(function(c){
      var any=0;
      $$('.ex-sub li',c).forEach(function(li){var s=!filtered||ok(li,false);li.hidden=!s;if(s)any++;});
      var show=!filtered||ok(c,true)||any>0; c.hidden=!show; if(show)total++;
      $$('.ex-tags span',c).forEach(function(s){s.classList.toggle('on',s.dataset.a===a)});
    });
    groups.forEach(function(g){var n=$$('.ex-card',g).filter(function(c){return !c.hidden}).length;g.hidden=!n;var b=$('[data-c="'+g.dataset.g+'"]',chips);if(b)b.textContent=n;b&&b.parentNode.classList.toggle('none',!n)});
    var em=$('#exEmpty'); em.hidden=total>0;
    if(!total&&a){var other=cards.filter(function(c){var txt=norm(c.textContent);return toks.every(function(w){return txt.indexOf(w)>=0})}).length;
      em.innerHTML='Nothing for '+esc(AUD[a].p)+' matches that. '+(other?'<button type="button" class="linkbtn" id="exAny">Show '+other+' match'+(other>1?'es':'')+' for anyone</button>':'Try a broader word.');
      var b=$('#exAny');if(b)b.addEventListener('click',function(){selA.value='';store('dm-aud',null);markAud('');apply()});}
    else if(!total){em.innerHTML='Nothing matches that yet. Try a broader word, or <a href="mailto:contact.dreammenu@gmail.com">ask us</a>: the answer may be in the data.';}
    $('#exCount').textContent=(a||toks.length)?'Showing '+total+' of '+cards.length+' pages'+(a?' for '+AUD[a].p:'')+(toks.length?' matching “'+q.value.trim()+'”':'')+'.':'All '+cards.length+' pages and their sections.';
    picks(toks.length?'':a);
    if(push!==false){var u=new URLSearchParams();if(a)u.set('for',a);if(q.value.trim())u.set('q',q.value.trim());history.replaceState(null,'',location.pathname+(u.toString()?'?'+u:'')+location.hash);}
  }
  selA.addEventListener('change',function(){store('dm-aud',selA.value||null);markAud(selA.value);if(selA.value)pickAud(selA.value,false);apply()});
  q.addEventListener('input',function(){apply()});
  apply(false);
})();
/* ---------- wayfinding: sticky header, section tracking, breadcrumbs, next step, back to top ---------- */
(function(){
  var path=location.pathname.replace(/\.html$/,'').replace(/\/index$/,'').replace(/\/$/,'')||'/', top=$('header.top'), main=$('main'), isMap=path==='/map';
  if(!top||!main)return;
  // 1. header stays within reach: slides away going down, returns on the way up
  if(!isMap){
    root.classList.add('nav-sticky');
    var setH=function(){root.style.setProperty('--hh',top.offsetHeight+'px')}; setH(); window.addEventListener('resize',setH);
    var ly=window.scrollY, tick=false;
    window.addEventListener('scroll',function(){
      if(tick)return; tick=true;
      requestAnimationFrame(function(){
        var y=window.scrollY, open=$('.mnav-top[aria-expanded="true"]')||root.classList.contains('mnav-open')||doc.body.classList.contains('mnav-open');
        if(y>ly+6&&y>320&&!open)root.classList.add('nav-away'); else if(y<ly-6||y<=320)root.classList.remove('nav-away');
        root.classList.toggle('nav-deep',y>1400);
        ly=y; tick=false;
      });
    },{passive:true});
  }
  // 2. "On this page" follows the reader and marks the current section
  var bar=$('.jump.onpage');
  if(bar&&'IntersectionObserver' in window){
    var links=$$('a[href^="#"]',bar), map={}, cur=null;
    links.forEach(function(a){var t=doc.getElementById(a.getAttribute('href').slice(1)); if(t){var sec=t.tagName==='SECTION'?t:(t.closest('section')||t); map[sec.id||t.id]=a;}});
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ var a=map[e.target.id]; if(a&&a!==cur){ if(cur)cur.removeAttribute('aria-current'); cur=a; a.setAttribute('aria-current','true');
        var w=a.parentNode; if(w.scrollWidth>w.clientWidth)w.scrollTo({left:a.offsetLeft-w.clientWidth/2+a.offsetWidth/2,behavior:'smooth'}); } } });
    },{rootMargin:'-20% 0px -70% 0px'});
    Object.keys(map).forEach(function(id){var t=doc.getElementById(id); if(t)io.observe(t)});
  }
  // 3. breadcrumbs: where this page sits, taken from the menu itself
  var PARENT={area:['Where to eat','/map','City guides','/cities'],city:['Where to eat','/map','City guides','/cities'],venue:['Where to eat','/map','Venue map','/map'],trends:['Food trends','/','Dish trends','/trends'],'case-studies':['Analysis & reports','/analysis','Insight Series reports','/case-studies'],report:['Analysis & reports','/analysis','Report 2026','/report'],quarterly:['Analysis & reports','/analysis','State of the Menu','/quarterly']};
  var seg=path.split('/').filter(Boolean), trail=[], here=null, nextUp=null;
  var title=function(){var h=$('h1',main); return h?h.textContent.replace(/\s+/g,' ').trim():doc.title.split('|')[0].trim()};
  if(seg.length===2&&PARENT[seg[0]]){
    var P=PARENT[seg[0]]; trail=[[P[0],P[1]],[P[2],P[3]]]; here=title(); nextUp={k:'Back to',t:P[2],h:P[3],d:''};
  } else if(seg.length===1){
    var a=$('.mp-p[href="'+path+'"]',top);
    if(a){
      var item=a.closest('.mnav-item'), g=$('.mnav-top',item), all=$$('.mp-p',top), i=all.indexOf(a), n=all[i+1]||all[0];
      if(g.getAttribute('href')!==path)trail=[[g.textContent.trim(),g.getAttribute('href')]];
      else trail=[[g.textContent.trim(),null]];
      here=$('b',a).textContent;
      if(n&&n.getAttribute('href')!==path&&n.getAttribute('href')!=='/')nextUp={k:n.closest('.mnav-item')===item?'Next':'Next: '+$('.mnav-top',n.closest('.mnav-item')).textContent.trim(),t:$('b',n).textContent,h:n.getAttribute('href'),d:($('span',n)||{}).textContent||''};
    } else if(!/^\/(login|logout|404)$/.test(path)) here=title();
  }
  if(here&&path!=='/'&&!isMap&&!$('.crumbs')){
    var c=doc.createElement('nav'); c.className='crumbs'; c.setAttribute('aria-label','Breadcrumb');
    c.innerHTML='<div class="wrap"><a href="/">Home</a>'+trail.map(function(t){return '<i aria-hidden="true">/</i>'+(t[1]?'<a href="'+t[1]+'">'+esc(t[0])+'</a>':'<span>'+esc(t[0])+'</span>')}).join('')+'<i aria-hidden="true">/</i><b aria-current="page">'+esc(here.length>48?here.slice(0,46)+'…':here)+'</b></div>';
    top.insertAdjacentElement('afterend',c);
  }
  // 4. one clear next step at the foot of the page
  var foot=$('footer.foot');
  if(nextUp&&foot&&path!=='/'&&!isMap&&!$('.nextup,.cs-next,.ph-next',main)){
    var nx=doc.createElement('a'); nx.className='nextstep'; nx.href=nextUp.h;
    nx.innerHTML='<div class="wrap"><span>'+esc(nextUp.k)+'</span><b>'+esc(nextUp.t)+'</b>'+(nextUp.d?'<em>'+esc(nextUp.d)+'</em>':'')+'<i aria-hidden="true">&rarr;</i></div>';
    foot.insertAdjacentElement('beforebegin',nx);
  }
  // 5. back to top on long pages
  if(!isMap){
    var up=doc.createElement('button'); up.type='button'; up.className='totop'; up.setAttribute('aria-label','Back to top');
    up.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M8 13V3M3.5 7.5 8 3l4.5 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    up.onclick=function(){window.scrollTo({top:0,behavior:'smooth'})}; doc.body.appendChild(up);
  }
})();
/* ---------- partner visits: one extra, labelled page view on partner pages, so usage can be reported per partner ---------- */
(function(){
  var m=doc.cookie.match(/(?:^|; )dm_who=([a-z0-9-]+)/); if(!m)return;
  var p=location.pathname.replace(/\.html$/,'');
  if(!/^\/(partner|briefing|insights|analysis|operators|tested-ideas|menu-check|case-studies|quarterly|onepager)/.test(p))return;
  window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments)};
  try{window.va('pageview',{path:'/_partner/'+m[1]+p,route:'/_partner/'+m[1]})}catch(e){}
})();
})();
