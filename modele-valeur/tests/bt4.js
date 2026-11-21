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
// valeur d'équipe = XI type, échelle ln (étape 1)
const SL={G:1,DC:2,DL:2,MI:3,AT:2,BU:1};
function xi(sq){const out=[];Object.keys(SL).forEach(g=>{const grp=sq.filter(p=>p[1]===g).slice();
  if(g==='G')grp.sort((a,b)=>(b[3]-a[3])||(b[2]-a[2]));else grp.sort((a,b)=>((b[3]>=E.IMP.MINREG)-(a[3]>=E.IMP.MINREG))||(b[2]-a[2]));out.push(...grp.slice(0,SL[g]));});return out;}
const XI={};teams.forEach(t=>XI[t]=xi(E.SQUADS[t]).reduce((s,p)=>s+p[2],0));
const L={};teams.forEach(t=>L[t]=Math.log(XI[t]));const Lm=mean(teams.map(t=>L[t]));
const P=E.P;
const lamOf=d=>{const x=d/100;return [Math.exp(P[0]+P[1]*x),Math.exp(P[2]-P[3]*x)];};
const lpois=(y,l)=>-l+y*Math.log(l)-Math.log(fact(y));
const ALL=MD; // J1→J11
function ll(c,ms,H){return ms.reduce((s,m)=>{const d=H+c*(L[m.home]-L[m.away]);const [lh,la]=lamOf(d);return s+lpois(m.hs,lh)+lpois(m.as,la);},0);}
function fitC(ms,H){let best=-1e9,bc=0;for(let c=0;c<=300;c+=1){const v=ll(c,ms,H);if(v>best){best=v;bc=c;}}return bc;}
const H0=E.H;
const cAll=fitC(ALL,H0);
console.log('Conversion valeur → niveau, calibrée sur les 91 matchs J1→J11 (avantage domicile',H0,'Elo, comme elo.html) :');
console.log('  ≈',cAll,'points Elo par unité de ln(valeur du XI)  →  valeur du XI ×2 = +'+Math.round(cAll*Math.log(2))+' Elo ; ×1,5 = +'+Math.round(cAll*Math.log(1.5)));
// incertitude : rééchantillonnage des journées (bootstrap par journée)
const mds=[...new Set(ALL.map(m=>m.md))];let seed=7;const rnd=()=>{seed=(seed*1664525+1013904223)%4294967296;return seed/4294967296;};
const cs=[];for(let b=0;b<200;b++){const pick=[];for(let k=0;k<mds.length;k++)pick.push(mds[Math.floor(rnd()*mds.length)]);const ms=[];pick.forEach(md=>ALL.filter(m=>m.md===md).forEach(m=>ms.push(m)));cs.push(fitC(ms,H0));}
cs.sort((a,b)=>a-b);console.log('  intervalle plausible (90 %) :',cs[10],'à',cs[189],'Elo par unité de ln');
// valeur SEULE, sans aucune mise à jour par les résultats : test « une journée à la fois » (la journée testée n'a pas servi à calibrer)
const rows=MD.filter(m=>m.md>=2&&m.md<=11);const Bs=[];const cL=[];
mds.forEach(md=>{const train=ALL.filter(m=>m.md!==md),test=ALL.filter(m=>m.md===md&&m.md>=2);if(!test.length)return;const c=fitC(train,H0);cL.push(c);test.forEach(m=>{const p=eloPredict(H0+c*(L[m.home]-L[m.away]));Bs.push(brier(p,outc(m)));});});
const poisB=(()=>{const Tc={};const TT=D=>Tc[D]||(Tc[D]=stats(D));return rows.map(m=>brier(model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1}),outc(m)));})();
const eloS=runElo(E.START,E.K,E.H);const eloSB=rows.map(m=>brier(eloS[m.home+'|'+m.away],outc(m)));
console.log('\nValeur SEULE (aucune mise à jour par les résultats), Brier J2→J11, calibration sans la journée testée :',mean(Bs).toFixed(4));
console.log('  pour comparaison : Poisson actuel de l\'appli',mean(poisB).toFixed(4),'| Elo actuel',mean(eloSB).toFixed(4),'| hasard 0.6667');
const pse=pairSE(Bs,poisB);console.log('  valeur seule − Poisson actuel :',pse.m.toFixed(4),'±',pse.se.toFixed(4));
// niveau de chaque équipe + écart « prévu / réel »
const perf={};teams.forEach(t=>perf[t]={g:0,gd:0});MD.forEach(m=>{perf[m.home].g++;perf[m.away].g++;perf[m.home].gd+=m.hs-m.as;perf[m.away].gd+=m.as-m.hs;});
const per100=(()=>{const [a,b]=lamOf(100),[c0,d0]=lamOf(0);return ((a-b)-(c0-d0));})(); // buts de différence par 100 Elo
console.log('\n100 points Elo ≈',per100.toFixed(2),'but de différence par match (d\'après la conversion Elo→buts d\'elo.html)');
const rating={};teams.forEach(t=>rating[t]=1500+cAll*(L[t]-Lm));
console.log('\nÉquipe'.padEnd(27),'Niveau (Elo)','avance prévue vs équipe moyenne (buts/match)','diff. de buts réelle (buts/match)');
teams.sort((a,b)=>rating[b]-rating[a]).forEach(t=>{const exp=(rating[t]-1500)/100*per100,act=perf[t].gd/perf[t].g;console.log(t.padEnd(26),String(Math.round(rating[t])).padStart(8),(exp>=0?'+':'')+exp.toFixed(2).padStart(12),'                    ',(act>=0?'+':'')+act.toFixed(2));});
// bruit : dispersion des résidus
const res=teams.map(t=>perf[t].gd/perf[t].g-(rating[t]-1500)/100*per100);const rsd=Math.sqrt(mean(res.map(x=>x*x)));
console.log('\nÉcart-type des écarts prévu/réel entre équipes :',rsd.toFixed(2),'but/match (dont ≈0,52 dû au simple hasard sur ~10 matchs)');
const trueSd=Math.sqrt(Math.max(0,rsd*rsd-0.52*0.52));console.log('  → écart « vrai » de niveau non expliqué par la valeur :',trueSd.toFixed(2),'but/match ≈',Math.round(trueSd/per100*100),'points Elo');
fs.writeFileSync('/tmp/claude-0/-home-claude/25613fe4-9ffa-5a5d-ba32-5a9a4f4c2081/scratchpad/bt/etape2.json',JSON.stringify({c:cAll,H:H0,per100,rating,trueSdElo:Math.round(trueSd/per100*100)}));
