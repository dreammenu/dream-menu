/* dm.js: loads venue data, the refined category layer and plain labels (24 Oct 2026) */
(function(){var s=document.currentScript,u=['/dm-data.js','/dm-cat.js','/dm-labels.js'];
if(document.readyState==='loading'&&s&&!s.async&&!s.defer){document.write(u.map(function(p){return '<script src="'+p+'"></scr'+'ipt>'}).join(''));}
else{u.forEach(function(p){try{var x=new XMLHttpRequest();x.open('GET',p,false);x.send();if(x.status===200)(0,eval)(x.responseText);}catch(e){}});}
})();
