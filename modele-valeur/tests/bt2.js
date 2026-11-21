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

// ===== Valeur d'effectif (Transfermarkt, fichier elo.html) =====
const E=(()=>{const t=fs.readFileSync('/home/claude/predicteur-ligue1/elo.html','utf8');const i=t.indexOf('const EMBED = ');const j=t.indexOf('\n',i);return JSON.parse(t.slice(i+14,j).replace(/;\s*$/,''));})();
const V={};Object.keys(E.SQUADS).forEach(t=>V[t]=E.SQUADS[t].reduce((a,p)=>a+p[2],0));
const lnV={};Object.keys(V).forEach(t=>lnV[t]=Math.log(V[t]));const lnMean=mean(Object.values(lnV));
function mean(a){return a.reduce((x,y)=>x+y,0)/a.length;}
// predict(d) d'elo.html
function eloPredict(d){const P=E.P,x=d/100;const lh=Math.exp(P[0]+P[1]*x),la=Math.exp(P[2]-P[3]*x),rho=E.RHO;let ph=0,pd=0,pa=0,tot=0;const M=[];
  for(let i=0;i<=10;i++){M[i]=[];for(let j=0;j<=10;j++){let p=pois(lh,i)*pois(la,j);if(i===0&&j===0)p*=1-lh*la*rho;else if(i===0&&j===1)p*=1+lh*rho;else if(i===1&&j===0)p*=1+la*rho;else if(i===1&&j===1)p*=1-rho;p=Math.max(p,0);M[i][j]=p;tot+=p;}}
  for(let i=0;i<=10;i++)for(let j=0;j<=10;j++){const p=M[i][j]/tot;if(i>j)ph+=p;else if(i===j)pd+=p;else pa+=p;}return [ph,pd,pa];}
const gmult=gd=>{gd=Math.abs(gd);return gd<=1?1:(gd===2?1.5:(11+gd)/8);};
function runElo(init,K,H){const R=Object.assign({},init);const out={};
  MD.forEach(m=>{const d=R[m.home]+H-R[m.away];out[m.home+'|'+m.away]=eloPredict(d);const Ex=1/(1+Math.pow(10,-d/400)),S=m.hs>m.as?1:(m.hs===m.as?.5:0);const delta=K*gmult(m.hs-m.as)*(S-Ex);R[m.home]+=delta;R[m.away]-=delta;});return out;}
const teams=Object.keys(V);
const rows=MD.filter(m=>m.md>=2&&m.md<=11);
const cmp=(pf,label,ref)=>{const B=rows.map(m=>brier(pf(m),outc(m)));const r=ref?pairSE(B,ref):null;return {label,B:mean(B),Bs:B,r};};
const Tc2={};const TT2=D=>Tc2[D]||(Tc2[D]=stats(D));
const poisBase=cmp(m=>model(TT2(m.md),m.md,m.home,m.away,{form:1,streak:1}),'Poisson actuel (index.html, reconstruit)');
const pr=(r)=>r.label.padEnd(58)+r.B.toFixed(4)+(r.r?'   vs Poisson actuel '+(r.r.m>=0?'+':'')+r.r.m.toFixed(4)+' ± '+r.r.se.toFixed(4):'');
console.log('\n=== Modèle Elo, journées 2→11 (82 matchs), K=15 et avantage domicile 50 comme dans elo.html ===');
console.log(pr(poisBase));
const startFlat={};teams.forEach(t=>startFlat[t]=1500);
const eloStart=runElo(E.START,E.K,E.H);console.log(pr(cmp(m=>eloStart[m.home+'|'+m.away],'Elo avec les niveaux de départ actuels (elo.html)',poisBase.Bs)));
const eloFlat=runElo(startFlat,E.K,E.H);console.log(pr(cmp(m=>eloFlat[m.home+'|'+m.away],'Elo « parti de zéro » (tout le monde à 1500)',poisBase.Bs)));
console.log('\n--- Elo parti de la VALEUR DE L\'EFFECTIF : Elo départ = 1500 + c × (ln valeur − moyenne) ---');
for(const K of [15,25,40]) for(const c of [0,30,50,70,90,120]){
  const init={};teams.forEach(t=>init[t]=1500+c*(lnV[t]-lnMean));const o=runElo(init,K,E.H);
  console.log(pr(cmp(m=>o[m.home+'|'+m.away],'K='+K+'  c='+c+(c===0?' (zéro)':''),poisBase.Bs)));}
// corrélation valeur ↔ niveau de départ de elo.html
const xs=teams.map(t=>lnV[t]),ys=teams.map(t=>E.START[t]);const mx=mean(xs),my=mean(ys);const corr=xs.reduce((s,x,i)=>s+(x-mx)*(ys[i]-my),0)/Math.sqrt(xs.reduce((s,x)=>s+(x-mx)**2,0)*ys.reduce((s,y)=>s+(y-my)**2,0));
console.log('\nCorrélation entre ln(valeur d\'effectif) et le niveau de départ actuel d\'elo.html :',corr.toFixed(2));
// pente de régression réelle : points/match vs ln valeur (J1–J11) pour info
const ppg={};teams.forEach(t=>ppg[t]={p:0,g:0,gd:0});MD.forEach(m=>{const a=ppg[m.home],b=ppg[m.away];a.g++;b.g++;a.gd+=m.hs-m.as;b.gd+=m.as-m.hs;a.p+=m.hs>m.as?3:m.hs===m.as?1:0;b.p+=m.as>m.hs?3:m.hs===m.as?1:0;});
const gdp=teams.map(t=>ppg[t].gd/ppg[t].g);const mg=mean(gdp);const corr2=xs.reduce((s,x,i)=>s+(x-mx)*(gdp[i]-mg),0)/Math.sqrt(xs.reduce((s,x)=>s+(x-mx)**2,0)*gdp.reduce((s,y)=>s+(y-mg)**2,0));
console.log('Corrélation entre ln(valeur d\'effectif) et la différence de buts par match réelle (J1→J11) :',corr2.toFixed(2),'(1 = parfait)');
// Poisson avec niveau de départ propre à chaque équipe (valeur d'effectif)
function modelV(T,D,h,a,o){o=o||{};const LA=1.41,k0=Math.max(3,8-((D-1)-1)*0.5),k=k0*(o.kmult||1),beta=o.beta||0;
  const th=T[h],ta=T[a];if(!th||!ta)return null;
  const tgt=(t,sign)=>LA*Math.exp(sign*beta*(lnV[t]-lnMean));
  const sh=(x,p,tg)=>(x+tg*k)/(p+k);
  let hS=sh(th.gf,th.p,tgt(h,1)),hC=sh(th.ga,th.p,tgt(h,-1)),aS=sh(ta.gf,ta.p,tgt(a,1)),aC=sh(ta.ga,ta.p,tgt(a,-1));
  const mh=streakAdj(th.res),ma=streakAdj(ta.res);hS*=1+mh;hC*=Math.max(.1,1-mh*.5);aS*=1+ma;aC*=Math.max(.1,1-ma*.5);
  const w=r=>r.slice(-5).filter(x=>x==='W').length;const fh=.9+w(th.res)/5*.2,fa=.9+w(ta.res)/5*.2;
  const lh=Math.max(.05,hS*aC/LA*1.15*fh),la=Math.max(.05,aS*hC/LA*.92*fa);
  let pH=0,pD=0,pA=0,tot=0;for(let i=0;i<=6;i++)for(let j=0;j<=6;j++){let p=pois(lh,i)*pois(la,j)*tau(i,j,lh,la,-.08);if(p<0)p=0;tot+=p;if(i>j)pH+=p;else if(i===j)pD+=p;else pA+=p;}return [pH/tot,pD/tot,pA/tot];}
console.log('\n=== Poisson (modèle d\'index.html) avec un niveau de départ propre à chaque équipe, tiré de la valeur d\'effectif ===');
console.log(pr(poisBase));
for(const km of [1,2,3]) for(const beta of [0,.05,.10,.15,.20]){
  const r=cmp(m=>modelV(TT2(m.md),m.md,m.home,m.away,{beta,kmult:km}),'poids du départ ×'+km+'  β='+beta+(beta===0?' (moyenne ligue, = actuel)':''),poisBase.Bs);console.log(pr(r));}
// comparaison avec le marché sur les 45 matchs
const keys=new Set(Object.keys(ODDS));const r45=rows.filter(m=>keys.has(m.home+'|'+m.away));
const B45=f=>mean(r45.map(m=>brier(f(m),outc(m))));
const iV={};teams.forEach(t=>iV[t]=1500+70*(lnV[t]-lnMean));const eV=runElo(iV,25,E.H);
console.log('\n=== Sur les 45 matchs avec cotes (J6→J11) ===');
console.log('Poisson actuel                      ',B45(m=>model(TT2(m.md),m.md,m.home,m.away,{form:1,streak:1})).toFixed(4));
console.log('Poisson + départ valeur (β=.10, ×2)  ',B45(m=>modelV(TT2(m.md),m.md,m.home,m.away,{beta:.10,kmult:2})).toFixed(4));
console.log('Elo départ valeur (c=70, K=25)       ',B45(m=>eV[m.home+'|'+m.away]).toFixed(4));
console.log('Elo actuel d\'elo.html                ',B45(m=>eloStart[m.home+'|'+m.away]).toFixed(4));
console.log('Marché                              ',B45(m=>vig(ODDS[m.home+'|'+m.away].o)).toFixed(4));
