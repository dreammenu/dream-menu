/* render.js: fills the partner pages from partner-data.js (24 Oct 2026) */
(function(){
var P=window.DM_PARTNER;if(!P||!P.trends)return;
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function $(id){return document.getElementById(id)}
function f1(v){return (Math.round(v*10)/10).toFixed(1)}
function sg(v){return (v>0?'+':'')+f1(v)}
function pct(v){return f1(v)+'%'}
function bars(items,fmt){var top=items.length?items[0][1]:1;return '<ul class="bars">'+items.map(function(x){return '<li><span class="bl">'+esc(x[0])+'</span><span class="bt"><i style="width:'+f1(100*x[1]/top)+'%"></i></span><span class="bv">'+fmt(x[1])+'</span></li>'}).join('')+'</ul>'}
var ORDER=P.order||Object.keys(P.trends),QS=P.trends[ORDER[0]].q,MIN=P.min_n||100;
function spark(share,low){
  var vals=share.filter(function(v){return v!=null}),mx=Math.max.apply(null,vals.concat([0]))||1,d='',pen=false,dots='';
  share.forEach(function(v,i){if(v==null){pen=false;return}var x=f1(4+30.4*i),y=f1(36-32*v/mx);d+=(pen?' L':' M')+x+' '+y;pen=true;
    dots+=low[i]?'<circle cx="'+x+'" cy="'+y+'" r="2.6" fill="none" stroke="currentColor" stroke-width="1.4" opacity=".55"/>':'<circle cx="'+x+'" cy="'+y+'" r="2.6" fill="currentColor"/>'});
  var lab='Share by quarter '+share.map(function(v,i){return QS[i]+' '+(v==null?'no comparable answers':pct(v)+(low[i]?' (few answers)':''))}).join(', ');
  return '<svg class="spark" viewBox="0 0 160 40" role="img" aria-label="'+esc(lab)+'"><path d="'+d.trim()+'" fill="none" stroke="currentColor" stroke-width="2" opacity=".85"/>'+dots+'</svg>'}
function row(x,name,sub,low){return '<tr><td>'+esc(name)+(sub?'<small>'+esc(sub)+'</small>':'')+'</td><td class="sp">'+spark(x.share,low)+'</td><td class="num">'+pct(x.early)+'</td><td class="num">'+pct(x.late)+'</td><td class="num '+(x.sig?(x.move>0?'up':'down'):'')+'">'+sg(x.move)+'</td><td class="num">'+(x.sig?'yes':'no')+'</td></tr>'}
var HEAD='<thead><tr><th>%s</th><th>By quarter</th><th class="num">Earlier</th><th class="num">Recent</th><th class="num">Move (pts)</th><th class="num">Clear?</th></tr></thead>';
function note(T){var lows=QS.filter(function(q,i){return T.low[i]});
  return '<p class="note">'+T.n.toLocaleString('en-GB')+' answers. Answers per quarter in the trend line: '+QS.map(function(q,i){return q+' '+T.n_q[i]}).join(', ')+'.'+(lows.length?' Hollow points mark quarters with fewer than '+MIN+' answers: read them with care.':'')+(T.note?' '+esc(T.note):'')+'</p>'}
function thin(course){for(var k in P.trends){var T=P.trends[k];if(T.label===course)return T.n_q[0]+T.n_q[1]<MIN||T.n_q[3]+T.n_q[4]+T.n_q[5]<MIN}return false}

// briefing
if($('bf-movers')){
  $('bf-movers').innerHTML='<div class="tablewrap"><table><thead><tr><th>Level</th><th>Course</th><th>Category</th><th class="num">Move (pts)</th><th class="num">p</th></tr></thead><tbody>'+
    P.movers.map(function(m){return '<tr><td>'+esc(m.level)+'</td><td>'+esc(m.course)+(thin(m.course)?'<small>few answers</small>':'')+'</td><td>'+esc(m.l)+'</td><td class="num '+(m.move>0?'up':'down')+'">'+sg(m.move)+'</td><td class="num">'+m.p.toFixed(3)+'</td></tr>'}).join('')+'</tbody></table></div>';
}
if($('bf-courses')){
  $('bf-courses').innerHTML='<div class="grid wide">'+ORDER.map(function(k){var T=P.trends[k];
    return '<div class="card"><h3>'+esc(T.label)+'</h3><div class="tablewrap" style="border:0"><table>'+HEAD.replace('%s','Group')+'<tbody>'+
      T.groups.slice(0,6).map(function(x){return row(x,x.c,'',T.low)}).join('')+'</tbody></table></div>'+
      '<div class="tablewrap" style="border:0;margin-top:10px"><table>'+HEAD.replace('%s','Dish')+'<tbody>'+
      T.cats.slice(0,10).map(function(x){return row(x,x.l,x.g,T.low)}).join('')+'</tbody></table></div>'+note(T)+'</div>'}).join('')+'</div>';
}
if($('bf-groups')){
  $('bf-groups').innerHTML='<div class="grid">'+P.groups.map(function(G){return '<div class="card"><div class="eyebrow">'+esc(G.g)+' · '+G.n+' guests</div><h3 style="margin-top:6px">Top groups</h3>'+bars(G.top_groups,pct)+'<h3 style="margin-top:12px">Top dishes</h3>'+bars(G.top,pct)+'</div>'}).join('')+'</div>';
}
// insights
if($('in-courses')){
  $('in-courses').innerHTML='<div class="grid">'+ORDER.map(function(k){var T=P.trends[k];
    return '<div class="card"><div class="eyebrow">'+esc(T.label)+' · '+T.n.toLocaleString('en-GB')+' answers</div><h3 style="margin-top:6px">By group</h3>'+
      bars(T.groups.slice(0,5).map(function(x){return [x.c,x.pct]}),pct)+'<h3 style="margin-top:12px">Top dishes</h3>'+
      bars(T.cats.slice(0,6).map(function(x){return [x.l,x.pct]}),pct)+'</div>'}).join('')+'</div>';
}
if($('in-guilty'))$('in-guilty').innerHTML=bars(P.extra.guilty,String);
if($('in-bin'))$('in-bin').innerHTML=bars(P.extra.bin,String);
// one-pager
function mv(list){return '<ul class="plain">'+list.map(function(m){return '<li>'+esc(m.l)+' ('+esc(m.course.toLowerCase())+(m.level==='Group'?', group':'')+') <b>'+sg(m.move)+' pts</b></li>'}).join('')+'</ul>'}
if($('op-rising'))$('op-rising').innerHTML=mv(P.movers.filter(function(m){return m.move>0}).slice(0,5));
if($('op-falling'))$('op-falling').innerHTML=mv(P.movers.filter(function(m){return m.move<0}).sort(function(a,b){return a.move-b.move}).slice(0,5));
if($('op-scot'))$('op-scot').innerHTML=bars(P.scotland,pct);
})();
