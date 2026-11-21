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
const variants={
 'Hasard (1/3 – 1/3 – 1/3)':(m)=>[1/3,1/3,1/3],
 'Fréquences ligue (45/26/29)':(m)=>[.45,.26,.29],
 'Modèle de base (buts + domicile)':(m)=>model(TT(m.md),m.md,m.home,m.away,{}),
 '+ forme sur 5 matchs':(m)=>model(TT(m.md),m.md,m.home,m.away,{form:1}),
 '+ forme + série (≈ appli sans absences/fatigue)':(m)=>model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1}),
};
function report(D0,D1,title,withMarket){
  console.log('\n=== '+title+' ===');
  let base=mk(D0,D1,variants['Hasard (1/3 – 1/3 – 1/3)']);
  if(withMarket){const keep=new Set(Object.keys(ODDS));base=base.filter(r=>keep.has(r.m.home+'|'+r.m.away));}
  const keys=new Set(base.map(r=>r.m.home+'|'+r.m.away));
  const res=[];
  Object.keys(variants).forEach(k=>{const rows=mk(D0,D1,variants[k]).filter(r=>keys.has(r.m.home+'|'+r.m.away));res.push(evalSet(rows,k));});
  if(withMarket){
    const mkt=base.map(r=>({m:r.m,o:r.o,p:vig(ODDS[r.m.home+'|'+r.m.away].o)}));res.push(evalSet(mkt,'MARCHÉ (cotes moyennes sans marge)'));
    const full=variants['+ forme + série (≈ appli sans absences/fatigue)'];
    const bl=base.map(r=>{const pm=full(r.m),pk=vig(ODDS[r.m.home+'|'+r.m.away].o);return {m:r.m,o:r.o,p:pm.map((x,i)=>.5*x+.5*pk[i])};});res.push(evalSet(bl,'Mélange 50 % modèle + 50 % marché'));
  }
  const u=res[0];
  console.log('n =',u.n,'matchs');
  console.log('Variante'.padEnd(52),'Brier'.padEnd(8),'LogLoss'.padEnd(9),'RPS'.padEnd(8),'1er choix OK','  écart Brier vs hasard (± erreur-type)');
  res.forEach(r=>{const p=pairSE(r.Bs,u.Bs);console.log(r.name.padEnd(52),r.B.toFixed(3).padEnd(8),r.L.toFixed(3).padEnd(9),r.R.toFixed(3).padEnd(8),(Math.round(r.acc*100)+' %').padEnd(12),(p.m>=0?'+':'')+p.m.toFixed(3)+' ± '+p.se.toFixed(3));});
  return res;}
report(2,11,'TOUTES LES JOURNÉES J2 → J11 (matchs joués)',false);
report(6,11,'J6 → J11, mêmes matchs que ceux avec cotes',true);
// sensibilité du lissage et de l'avantage domicile (modèle complet reconstructible), J2–J11
console.log('\n=== Sensibilité (Brier, J2→J11, modèle + forme + série) ===');
const sens=(label,o)=>{const r=evalSet(mk(2,11,m=>model(TT(m.md),m.md,m.home,m.away,Object.assign({form:1,streak:1},o))),label);return label.padEnd(44)+r.B.toFixed(4);};
[['Lissage de l\'appli (k=8→3,5)',{}],['k=3',{k:3}],['k=6',{k:6}],['k=10',{k:10}],['k=15',{k:15}],['k=25',{k:25}]].forEach(([l,o])=>console.log(sens(l,o)));
[['Avantage dom. 1,15/0,92 (appli)',{}],['1,05/1,00',{HA:1.05,AW:1.0}],['1,25/0,85',{HA:1.25,AW:.85}],['1,30/0,88',{HA:1.3,AW:.88}]].forEach(([l,o])=>console.log(sens(l,o)));
[['Moy. ligue 1,41 (appli)',{}],['Moy. ligue 1,50',{LA:1.5}],['Moy. ligue 1,60',{LA:1.6}]].forEach(([l,o])=>console.log(sens(l,o)));
[['Sans correction Dixon-Coles (ρ=0)',{rho:0}],['ρ=−0,15',{rho:-.15}]].forEach(([l,o])=>console.log(sens(l,o)));
// calibration (modèle complet), J2–J11, toutes issues confondues
console.log('\n=== Calibration (modèle complet, J2→J11) : proba annoncée vs fréquence réelle ===');
const rowsC=mk(2,11,m=>model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1}));
const bins=[[0,.2],[.2,.3],[.3,.4],[.4,.5],[.5,.6],[.6,.7],[.7,1.01]];
bins.forEach(([lo,hi])=>{let n=0,sp=0,so=0;rowsC.forEach(r=>r.p.forEach((x,i)=>{if(x>=lo&&x<hi){n++;sp+=x;so+=(r.o===i?1:0);}}));console.log(('['+Math.round(lo*100)+'–'+Math.round(Math.min(hi,1)*100)+' %[').padEnd(12),('n='+n).padEnd(7),'annoncé',n?(100*sp/n).toFixed(0)+' %':'-','| réel',n?(100*so/n).toFixed(0)+' %':'-');});
// règles de pari de l'appli
console.log('\n=== Règles de pari de l\'appli (favori ≥ 60 % → sec ; sinon favori+nul ≥ 70 % → ou nul), J2→J11 ===');
let W={n:0,hit:0,sp:0},DC={n:0,hit:0,sp:0},NO={n:0};
rowsC.forEach(r=>{const fav=r.p[0]>=r.p[2]?0:2,pw=r.p[fav],pdc=pw+r.p[1];const res=r.o===fav,nl=r.o!==(fav===0?2:0);
  if(pw>=.6){W.n++;W.hit+=res?1:0;W.sp+=pw;}else if(pdc>=.7){DC.n++;DC.hit+=nl?1:0;DC.sp+=pdc;}else NO.n++;});
console.log('Victoire sèche :',W.n,'matchs | réussite réelle',Math.round(100*W.hit/W.n)+' %','| annoncée en moyenne',Math.round(100*W.sp/W.n)+' %');
console.log('« Ou nul »      :',DC.n,'matchs | réussite réelle',Math.round(100*DC.hit/DC.n)+' %','| annoncée en moyenne',Math.round(100*DC.sp/DC.n)+' %');
console.log('« Trop serré »  :',NO.n,'matchs');
// avec cotes : rendement des paris « victoire sèche » aux cotes moyennes (mise 1 € à plat), J6→J11
console.log('\n=== Rendement fictif aux cotes moyennes du marché (J6→J11, 45 matchs) ===');
let S={n:0,gain:0,hit:0},Dd={n:0,gain:0,hit:0},E={n:0,gain:0,hit:0};
mk(6,11,m=>model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1})).forEach(r=>{const od=ODDS[r.m.home+'|'+r.m.away];if(!od)return;const o=od.o,fav=r.p[0]>=r.p[2]?0:2,pw=r.p[fav],pdc=pw+r.p[1],oFav=o[fav===0?0:2];
  if(pw>=.6){S.n++;S.hit+=r.o===fav?1:0;S.gain+=(r.o===fav?oFav:0)-1;}
  else if(pdc>=.7){const oDC=1.035/(1/oFav+1/o[1]);Dd.n++;Dd.hit+=r.o!==(fav===0?2:0)?1:0;Dd.gain+=(r.o!==(fav===0?2:0)?oDC:0)-1;}
  // « valeur » : paris sur le résultat où modèle × cote > 1,10
  [0,1,2].forEach(i=>{if(r.p[i]*o[i]>1.10){E.n++;E.hit+=r.o===i?1:0;E.gain+=(r.o===i?o[i]:0)-1;}});});
const f=x=>(x.gain>=0?'+':'')+x.gain.toFixed(2)+' € pour '+x.n+' paris de 1 € ('+x.hit+' gagnés)';
console.log('Victoire sèche (favori ≥ 60 %) :',f(S));
console.log('« Ou nul » (cote estimée) :',f(Dd));
console.log('Paris « de valeur » (modèle × cote > 1,10, toutes issues) :',f(E));
// écart modèle vs marché (même 45 matchs)
{const keys=new Set(Object.keys(ODDS));
 const rows=mk(6,11,m=>model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1})).filter(r=>keys.has(r.m.home+'|'+r.m.away));
 const bm=rows.map(r=>brier(r.p,r.o)),bk=rows.map(r=>brier(vig(ODDS[r.m.home+'|'+r.m.away].o),r.o));
 const p=pairSE(bm,bk);console.log('\nModèle − marché (Brier, 45 matchs) :',p.m.toFixed(3),'±',p.se.toFixed(3));
 // désaccord : écart moyen |p modèle − p marché| et résultat quand le modèle voit « plus haut » que le marché
 let big=0,bigHit=0,bigMk=0;rows.forEach(r=>{const pk=vig(ODDS[r.m.home+'|'+r.m.away].o);r.p.forEach((x,i)=>{if(x-pk[i]>0.10){big++;bigHit+=r.o===i?1:0;bigMk+=pk[i];}});});
 console.log('Issues que le modèle voit ≥10 pts au-dessus du marché :',big,'| réalisées',bigHit,'('+Math.round(100*bigHit/big)+' %) | probabilité du marché en moyenne',Math.round(100*bigMk/big)+' %');}
