const fs=require('fs');
const s=fs.readFileSync('/home/claude/predicteur-ligue1/index.html','utf8');
const a0=s.indexOf('let MATCHDAY_HISTORY = {');let d=0,i=s.indexOf('{',a0),st=i;for(;i<s.length;i++){if(s[i]=='{')d++;else if(s[i]=='}'){d--;if(!d)break;}}
const H=eval('('+s.slice(st,i+1)+')');
const NM={'Troyes':'ES Troyes AC','Le Havre':'Le Havre AC','Lens':'RC Lens','Marseille':'Olympique de Marseille','Angers':'Angers SCO','Nice':'OGC Nice','Brest':'Stade Brestois','Lyon':'Olympique Lyonnais','Lorient':'FC Lorient','Le Mans':'Le Mans FC','Monaco':'AS Monaco','Rennes':'Stade Rennais','Lille':'LOSC Lille','PSG':'Paris Saint-Germain','Auxerre':'AJ Auxerre','Paris FC':'Paris FC','Toulouse':'Toulouse FC','Strasbourg':'RC Strasbourg'};
// cotes
const ODDS={};let bad=0;
fs.readFileSync('odds.txt','utf8').trim().split('\n').forEach(l=>{const [h,a,hs,as,o1,ox,o2]=l.split('|');ODDS[NM[h]+'|'+NM[a]]={hs:+hs,as:+as,o:[+o1,+ox,+o2]};});
// matchs joués par journée
const MD=[];Object.keys(H).map(Number).sort((a,b)=>a-b).forEach(md=>H[md].forEach(m=>{if(m.played)MD.push({md,home:m.home,away:m.away,hs:+m.homeScore,as:+m.awayScore});}));
// vérification des scores de la table de cotes
let okS=0,missS=[];Object.keys(ODDS).forEach(k=>{const [h,a]=k.split('|');const m=MD.find(x=>x.home===h&&x.away===a);if(!m)missS.push(k+' (absent)');else if(m.hs!==ODDS[k].hs||m.as!==ODDS[k].as)missS.push(k+' score '+m.hs+'-'+m.as+' vs '+ODDS[k].hs+'-'+ODDS[k].as);else okS++;});
console.log('cotes/scores concordants:',okS,'/',Object.keys(ODDS).length,missS.length?'| ÉCARTS: '+missS.join('; '):'');
const LA0=1.41,HA=1.15,AW=0.92,RHO=-0.08,MAXG=6;
const fact=n=>{let f=1;for(let i=2;i<=n;i++)f*=i;return f;};
const pois=(l,k)=>Math.exp(-l)*Math.pow(l,k)/fact(k);
const tau=(x,y,l,m,r)=>x===0&&y===0?1-l*m*r:x===0&&y===1?1+l*r:x===1&&y===0?1+m*r:x===1&&y===1?1-r:1;
function stats(D){ // stats de chaque équipe avec les matchs des journées < D
  const T={};const g=t=>T[t]||(T[t]={p:0,gf:0,ga:0,res:[]});
  MD.filter(m=>m.md<D).forEach(m=>{const h=g(m.home),a=g(m.away);h.p++;a.p++;h.gf+=m.hs;h.ga+=m.as;a.gf+=m.as;a.ga+=m.hs;
    h.res.push(m.hs>m.as?'W':m.hs===m.as?'D':'L');a.res.push(m.as>m.hs?'W':m.hs===m.as?'D':'L');});
  return T;}
function streakAdj(res){ // série en cours (le plus récent d'abord)
  const r=res.slice().reverse();if(!r.length)return 0;let n=0;
  if(r[0]==='W'){for(const x of r){if(x==='W')n++;else break;}return Math.min(.10,n*.02);}
  if(r[0]==='L'){for(const x of r){if(x==='L')n++;else break;}return -Math.min(.10,n*.02);}
  for(const x of r){if(x!=='L')n++;else break;}return Math.min(.06,n*.012);}
function model(T,D,h,a,o){
  o=o||{};const LA=o.LA||LA0,k=o.k!=null?o.k:Math.max(3,8-((D-1)-1)*0.5),ha=o.HA||HA,aw=o.AW||AW,rho=o.rho!=null?o.rho:RHO;
  const th=T[h],ta=T[a];if(!th||!ta||!th.p||!ta.p)return null;
  const sh=(x,p)=>(x+LA*k)/(p+k);
  let hS=sh(th.gf,th.p),hC=sh(th.ga,th.p),aS=sh(ta.gf,ta.p),aC=sh(ta.ga,ta.p);
  if(o.streak){const mh=streakAdj(th.res),ma=streakAdj(ta.res);hS*=1+mh;hC*=Math.max(.1,1-mh*.5);aS*=1+ma;aC*=Math.max(.1,1-ma*.5);}
  let fh=1,fa=1;if(o.form){const w=r=>r.slice(-5).filter(x=>x==='W').length;fh=.9+w(th.res)/5*.2;fa=.9+w(ta.res)/5*.2;}
  const lh=Math.max(.05,hS*aC/LA*ha*fh),la=Math.max(.05,aS*hC/LA*aw*fa);
  let pH=0,pD=0,pA=0,tot=0,best={p:-1};
  for(let i=0;i<=MAXG;i++)for(let j=0;j<=MAXG;j++){let p=pois(lh,i)*pois(la,j)*tau(i,j,lh,la,rho);if(p<0)p=0;tot+=p;if(i>j)pH+=p;else if(i===j)pD+=p;else pA+=p;if(p>best.p)best={i,j,p};}
  return [pH/tot,pD/tot,pA/tot];}
// ---- jeu d'évaluation ----
const outc=m=>m.hs>m.as?0:m.hs===m.as?1:2;
const brier=(p,o)=>p.reduce((s,x,i)=>s+(x-(i===o?1:0))**2,0);
const logl=(p,o)=>-Math.log(Math.max(1e-9,p[o]));
const rps=(p,o)=>{const c1=p[0],c2=p[0]+p[1];const o1=o===0?1:0,o2=o<=1?1:0;return ((c1-o1)**2+(c2-o2)**2)/2;};
function evalSet(rows,name){ // rows: {m,p,o}
  const n=rows.length;const B=rows.map(r=>brier(r.p,r.o)),L=rows.map(r=>logl(r.p,r.o)),R=rows.map(r=>rps(r.p,r.o));
  const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
  const acc=mean(rows.map(r=>r.p.indexOf(Math.max(...r.p))===r.o?1:0));
  return {name,n,B:mean(B),L:mean(L),R:mean(R),acc,Bs:B};}
function pairSE(a,b){const d=a.map((x,i)=>x-b[i]);const m=d.reduce((x,y)=>x+y,0)/d.length;const v=d.reduce((x,y)=>x+(y-m)**2,0)/(d.length-1);return {m,se:Math.sqrt(v/d.length)};}
const mk=(D0,D1,fn)=>MD.filter(m=>m.md>=D0&&m.md<=D1).map(m=>({m,o:outc(m),p:fn(m)})).filter(r=>r.p);
const Tc={};const TT=D=>Tc[D]||(Tc[D]=stats(D));
// réalité de la saison : moyenne de buts / équipe / match (informatif)
const totG=MD.reduce((x,m)=>x+m.hs+m.as,0),nM=MD.length;
console.log('matchs joués:',nM,'| buts/équipe/match saison 2026-27 :',(totG/(2*nM)).toFixed(3),'(le modèle utilise 1,41) | % victoires dom/nul/ext :',[0,1,2].map(k=>Math.round(100*MD.filter(m=>outc(m)===k).length/nM)).join('/'));
const vig=o=>{const q=o.map(x=>1/x),s=q.reduce((a,b)=>a+b,0);return q.map(x=>x/s);};

// ---- Modèle « force attaque/défense » ajusté à l'adversaire (régression de Poisson pénalisée) ----
function fitRidge(D,gamma,half,opt){
  opt=opt||{};
  const ms=MD.filter(m=>m.md<D);const teams=[...new Set(ms.flatMap(m=>[m.home,m.away]))];
  const idx={};teams.forEach((t,i)=>idx[t]=i);const n=teams.length;
  const att=new Array(n).fill(0),def=new Array(n).fill(0);
  let mu=Math.log(1.45),eta=Math.log(1.2);
  const data=ms.map(m=>({h:idx[m.home],a:idx[m.away],yh:m.hs,ya:m.as,w:half?Math.pow(.5,(D-1-m.md)/half):1}));
  for(let it=0;it<150;it++){
    // mu
    {let g=0,h=0;data.forEach(r=>{const lh=Math.exp(mu+eta+att[r.h]-def[r.a]),la=Math.exp(mu+att[r.a]-def[r.h]);g+=r.w*(r.yh-lh+r.ya-la);h+=r.w*(lh+la);});mu+=g/h;}
    // eta (avantage domicile), faible pénalité vers log(1.2)
    if(!opt.noEta){let g=0,h=0;data.forEach(r=>{const lh=Math.exp(mu+eta+att[r.h]-def[r.a]);g+=r.w*(r.yh-lh);h+=r.w*lh;});const pen=3;g-=pen*(eta-Math.log(1.2));h+=pen;eta+=g/h;}
    for(let t=0;t<n;t++){
      {let g=0,h=0;data.forEach(r=>{if(r.h===t){const lh=Math.exp(mu+eta+att[t]-def[r.a]);g+=r.w*(r.yh-lh);h+=r.w*lh;}if(r.a===t){const la=Math.exp(mu+att[t]-def[r.h]);g+=r.w*(r.ya-la);h+=r.w*la;}});g-=gamma*att[t];h+=gamma;att[t]+=g/h;}
      {let g=0,h=0;data.forEach(r=>{if(r.a===t){const lh=Math.exp(mu+eta+att[r.h]-def[t]);g+=-r.w*(r.yh-lh);h+=r.w*lh;}if(r.h===t){const la=Math.exp(mu+att[r.a]-def[t]);g+=-r.w*(r.ya-la);h+=r.w*la;}});g-=gamma*def[t];h+=gamma;def[t]+=g/h;}
    }
  }
  return {idx,att,def,mu,eta};}
function probsFromLam(lh,la,rho){let pH=0,pD=0,pA=0,tot=0;for(let i=0;i<=MAXG;i++)for(let j=0;j<=MAXG;j++){let p=pois(lh,i)*pois(la,j)*tau(i,j,lh,la,rho);if(p<0)p=0;tot+=p;if(i>j)pH+=p;else if(i===j)pD+=p;else pA+=p;}return [pH/tot,pD/tot,pA/tot];}
const cache={};
function ridgeP(m,gamma,half,rho){const key=m.md+'|'+gamma+'|'+half;const F=cache[key]||(cache[key]=fitRidge(m.md,gamma,half));
  const h=F.idx[m.home],a=F.idx[m.away];if(h==null||a==null)return null;
  const lh=Math.exp(F.mu+F.eta+F.att[h]-F.def[a]),la=Math.exp(F.mu+F.att[a]-F.def[h]);return probsFromLam(lh,la,rho!=null?rho:-.08);}
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
const cur=m=>model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1});
const rowsAll=MD.filter(m=>m.md>=2&&m.md<=11);
const evalFn=(fn,rows)=>{const B=rows.map(m=>{const p=fn(m);return p?brier(p,outc(m)):null;});return B;};
const B0=evalFn(cur,rowsAll);
console.log('Référence : modèle actuel reconstruit (J2→J11, 82 matchs) Brier =',mean(B0).toFixed(4));
console.log('\nModèle « forces attaque/défense ajustées à l\'adversaire » (régression de Poisson pénalisée) :');
console.log('pénalité γ'.padEnd(12),'mémoire (demi-vie)'.padEnd(20),'Brier'.padEnd(8),'écart vs actuel');
for(const half of [0,10,6,4]) for(const gamma of [3,6,10,20]){
  const B=evalFn(m=>ridgeP(m,gamma,half),rowsAll);const ok=B.every(x=>x!=null);if(!ok){console.log('données manquantes');continue;}
  const p=pairSE(B,B0);console.log(String(gamma).padEnd(12),(half?half+' journées':'aucune').padEnd(20),mean(B).toFixed(4).padEnd(8),(p.m>=0?'+':'')+p.m.toFixed(4)+' ± '+p.se.toFixed(4));}
// mélange actuel + ajusté
for(const [g,h] of [[6,0],[10,0],[10,6]]){const B=evalFn(m=>{const a=cur(m),b=ridgeP(m,g,h);return a.map((x,i)=>.5*x+.5*b[i]);},rowsAll);console.log('Mélange 50/50 actuel + ajusté (γ='+g+', mémoire '+(h||'aucune')+') :',mean(B).toFixed(4));}
// poids du marché : sur les 45 matchs avec cotes
const rows45=MD.filter(m=>ODDS[m.home+'|'+m.away]&&m.md>=6);
console.log('\nPoids du marché dans un mélange marché + modèle actuel (45 matchs avec cotes) :');
[0,.2,.4,.5,.6,.8,.9,1].forEach(w=>{const B=rows45.map(m=>{const a=cur(m),k=vig(ODDS[m.home+'|'+m.away].o);return brier(a.map((x,i)=>(1-w)*x+w*k[i]),outc(m));});console.log('  poids marché',String(w).padEnd(4),'Brier',mean(B).toFixed(4));});
// idem avec le modèle ajusté
console.log('Avec le modèle ajusté (γ=10, mémoire 6) à la place :');
[0,.5,.8,1].forEach(w=>{const B=rows45.map(m=>{const a=ridgeP(m,10,6),k=vig(ODDS[m.home+'|'+m.away].o);return brier(a.map((x,i)=>(1-w)*x+w*k[i]),outc(m));});console.log('  poids marché',String(w).padEnd(4),'Brier',mean(B).toFixed(4));});
console.log('\nModèle actuel « tempéré » vers les fréquences de la ligue (J2→J11) :');
[0,.1,.2,.3,.4].forEach(a=>{const B=rowsAll.map(m=>{const p=cur(m),f=[.47,.22,.31];return brier(p.map((x,i)=>(1-a)*x+a*f[i]),outc(m));});console.log('  part des fréquences',String(a).padEnd(4),'Brier',mean(B).toFixed(4));});
const avg=[0,0,0];rowsAll.forEach(m=>cur(m).forEach((x,i)=>avg[i]+=x/rowsAll.length));console.log('Moyenne des probabilités annoncées (dom/nul/ext) :',avg.map(x=>Math.round(100*x)).join('/'),'| réel',[0,1,2].map(k=>Math.round(100*rowsAll.filter(m=>outc(m)===k).length/rowsAll.length)).join('/'));
