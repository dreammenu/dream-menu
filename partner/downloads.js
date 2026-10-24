/* downloads.js: builds the partner CSV extracts from the live data files (24 Oct 2026) */
(function(){
var CR=String.fromCharCode(13),LF=String.fromCharCode(10),NEEDQ=new RegExp('[",'+CR+LF+']');
function parse(t){var rows=[],row=[],f='',q=false,i=0,c;for(;i<t.length;i++){c=t[i];if(q){if(c==='"'){if(t[i+1]==='"'){f+='"';i++}else q=false}else f+=c}else if(c==='"')q=true;else if(c===','){row.push(f);f=''}else if(c===CR){}else if(c===LF){row.push(f);rows.push(row);row=[];f=''}else f+=c}if(f!==''||row.length){row.push(f);rows.push(row)}return rows}
function cell(s){s=String(s==null?'':s);return NEEDQ.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function csv(rows){return '﻿'+rows.map(function(x){return x.map(cell).join(',')}).join(LF)+LF}
function get(u){return fetch(u,{credentials:'same-origin'}).then(function(r){if(!r.ok)throw new Error(u+' '+r.status);return r.text()})}
function f1(v){return (Math.round(v*10)/10).toFixed(1)}
function dm(){return Promise.all([get('/dm-data.js'),get('/dm-cat.js'),get('/dm-labels.js')]).then(function(a){var w={};
  new Function('window',a[0])(w);var codes=JSON.parse(JSON.stringify(w.DM));new Function('window',a[1])(w);var C=w.DMC;new Function('window','DML_ONLY',a[2].slice(0,a[2].indexOf('(function(){var D=window.DM')))(w);return {DM:codes,C:C,L:w.DML}})}
var B={
 venues:function(){return Promise.all([get('/partner/data/venues-base.csv'),dm()]).then(function(a){var D=a[1],top={};
   D.DM.venues.forEach(function(v,i){var k=D.C.v[i],o=[],ix={};(k||[]).forEach(function(x){var n=D.C.c[x[0]],l=D.L[n]?D.L[n][0]:n;if(ix.hasOwnProperty(l))o[ix[l]][1]+=x[1];else{ix[l]=o.length;o.push([l,x[1]])}});top[v.i]=o.slice(0,3).map(function(x){return x[0]+' ('+x[1]+')'}).join('; ')});
   var rows=parse(a[0].replace(/^﻿/,'')),ti=rows[0].indexOf('top_dish_categories');
   for(var r=1;r<rows.length;r++)rows[r][ti]=top.hasOwnProperty(rows[r][0])?top[rows[r][0]]:'';return csv(rows)})},
 market:function(){return dm().then(function(D){var rows=[['market_id','market','level','country','guests','venues','mentions','dish_category','label','parent_group','category_mentions','share_pct']];
   D.DM.markets.forEach(function(m){var c=D.C.m[m.id];if(!c)return;var co=m.co||(m.k==='country'?m.n:'');
     c.forEach(function(x){var n=D.C.c[x[0]],l=D.L[n]||[n,''];rows.push([m.id,m.n,m.k,co,m.g,m.v,m.mn,n,l[0],l[1],x[1],f1(x[2])])})});return csv(rows)})},
 trends:function(){var P=window.DM_PARTNER,rows=[['course','level','category','label','parent_group','quarter','share_pct','answers_in_quarter','low_sample','earlier_share_pct','recent_share_pct','move_pts','p_value','clear_move']];
   P.order.forEach(function(k){var T=P.trends[k];[['group',T.groups],['dish',T.cats]].forEach(function(L){L[1].forEach(function(x){T.q.forEach(function(q,i){
     rows.push([T.label,L[0],x.c,x.l||x.c,x.g||'',q,x.share[i]==null?'':f1(x.share[i]),T.n_q[i],T.low[i]?'yes':'no',f1(x.early),f1(x.late),f1(x.move),x.p,x.sig?'yes':'no'])})})})});return Promise.resolve(csv(rows))},
 course:function(){var P=window.DM_PARTNER,rows=[['course','level','category','label','parent_group','answers','share_pct','answers_in_course']];
   P.order.forEach(function(k){var T=P.trends[k];T.groups.forEach(function(x){rows.push([T.label,'group',x.c,x.c,'',x.n,f1(x.pct),T.n])});
     T.cats.slice(0,10).forEach(function(x){rows.push([T.label,'dish',x.c,x.l,x.g,x.n,f1(x.pct),T.n])})});return Promise.resolve(csv(rows))}
};
window.DMPartnerCSV=B;
document.addEventListener('click',function(e){var a=e.target.closest('a[data-csv]');if(!a||!B[a.dataset.csv])return;e.preventDefault();
  var t=a.querySelector('b'),o=t?t.textContent:'',name=(a.getAttribute('href')||'').split('/').pop()||'data.csv';if(t)t.textContent='Preparing...';
  B[a.dataset.csv]().then(function(s){var u=URL.createObjectURL(new Blob([s],{type:'text/csv;charset=utf-8'})),l=document.createElement('a');l.href=u;l.download=name;document.body.appendChild(l);l.click();l.remove();setTimeout(function(){URL.revokeObjectURL(u)},4000);if(t)t.textContent=o})
  .catch(function(){if(t)t.textContent=o;alert('The file could not be prepared. Please refresh and try again.')})});
})();
