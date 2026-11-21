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
const C=106;
const R0={};teams.forEach(t=>R0[t]=1500+C*(L[t]-Lm));
const per100=(()=>{const [a,b]=lamOf(100),[c0,d0]=lamOf(0);return (a-b)-(c0-d0);})();
const G2E=100/per100; // buts de différence -> points Elo
const rows=MD.filter(m=>m.md>=2&&m.md<=11);
const byMd=md=>MD.filter(m=>m.md===md);
// (A) dérive Elo : départ = niveau valeur, mise à jour après chaque match
function evalDrift(K,useG){const R=Object.assign({},R0);const out=[];
  const ordered=MD.slice();
  ordered.forEach(m=>{const d=R[m.home]+H0-R[m.away];if(m.md>=2)out.push(brier(eloPredict(d),outc(m)));
    const Ex=1/(1+Math.pow(10,-d/400)),S=m.hs>m.as?1:(m.hs===m.as?.5:0);const delta=K*(useG?gmult(m.hs-m.as):1)*(S-Ex);R[m.home]+=delta;R[m.away]-=delta;});
  return {B:out,R};}
// (B) ajustement d'équipe appris : niveau = valeur + A, A = somme des écarts (réel - prévu par la valeur seule) / (n + lambda)
function evalAdj(lambda,wInitial){const out=[];const A={};teams.forEach(t=>A[t]={s:0,n:0});
  const cur=t=>R0[t]+(A[t].s/(A[t].n+lambda));
  MD.forEach(m=>{const d=cur(m.home)+H0-cur(m.away);if(m.md>=2)out.push(brier(eloPredict(d),outc(m)));
    const d0=R0[m.home]+H0-R0[m.away];const [lh,la]=lamOf(d0);const res=(m.hs-m.as)-(lh-la); // en buts, point de vue du domicile
    const g=Math.max(-4,Math.min(4,res))*G2E;A[m.home].s+=g;A[m.home].n++;A[m.away].s-=g;A[m.away].n++;});
  const R={};teams.forEach(t=>R[t]=cur(t));return {B:out,R};}
// ===== (C) avantage domicile propre à chaque équipe =====
// résidu d'un match (en buts, point de vue du domicile) = réel - prévu ; converti en Elo ; plafonné à ±4 buts
// effet domicile h(t) = (moyenne des résidus à domicile - moyenne des résidus à l'extérieur) / 2, ramené vers 0 avec un poids lamH (en matchs)
// niveau du jour : d = niv(dom) + h(dom) + H + h(ext) - niv(ext)   (variante 'sym') ; ou sans h(ext) (variante 'dom')
function evalHome(lamA,lamH,H,variant){const out=[];const A={},S={};teams.forEach(t=>{A[t]={s:0,n:0};S[t]={sh:0,nh:0,sa:0,na:0};});
  const cur=t=>R0[t]+(A[t].s/(A[t].n+lamA));
  const hEff=t=>{const x=S[t];if(!x.nh||!x.na||lamH>=1e8)return 0;const ne=2*x.nh*x.na/(x.nh+x.na);return ((x.sh/x.nh-x.sa/x.na)/2)*ne/(ne+lamH);};
  MD.forEach(m=>{const d=cur(m.home)+hEff(m.home)+(variant==='sym'?hEff(m.away):0)+H-cur(m.away);
    if(m.md>=2)out.push(brier(eloPredict(d),outc(m)));
    const d0=R0[m.home]+H-R0[m.away];const [lh,la]=lamOf(d0);const res=(m.hs-m.as)-(lh-la);
    const g=Math.max(-4,Math.min(4,res))*G2E;
    A[m.home].s+=g;A[m.home].n++;A[m.away].s-=g;A[m.away].n++;
    S[m.home].sh+=g;S[m.home].nh++;S[m.away].sa+=-g;S[m.away].na++;});
  const hs={};teams.forEach(t=>hs[t]=hEff(t));return {B:out,h:hs,S};}
// ===== Étape 5 : probabilités et test complet =====
function evalP(lamA,lamH,H,scale){const out=[];const A={},S={};teams.forEach(t=>{A[t]={s:0,n:0};S[t]={sh:0,nh:0,sa:0,na:0};});
  const cur=t=>R0[t]+(A[t].s/(A[t].n+lamA));
  const hEff=t=>{const x=S[t];if(!x.nh||!x.na||lamH>=1e8)return 0;const ne=2*x.nh*x.na/(x.nh+x.na);return ((x.sh/x.nh-x.sa/x.na)/2)*ne/(ne+lamH);};
  MD.forEach(m=>{const d=(cur(m.home)+hEff(m.home)+H-cur(m.away))*(scale||1);
    if(m.md>=2)out.push(eloPredict(d));
    const d0=R0[m.home]+H-R0[m.away];const [lh,la]=lamOf(d0);const res=(m.hs-m.as)-(lh-la);
    const g=Math.max(-4,Math.min(4,res))*G2E;
    A[m.home].s+=g;A[m.home].n++;A[m.away].s-=g;A[m.away].n++;
    S[m.home].sh+=g;S[m.home].nh++;S[m.away].sa+=-g;S[m.away].na++;});
  return out;}
const R2=MD.filter(m=>m.md>=2);
const sc=(P,idx)=>{const ii=idx||R2.map((_,i)=>i);const B=ii.map(i=>brier(P[i],outc(R2[i]))),Lg=ii.map(i=>logl(P[i],outc(R2[i]))),Rp=ii.map(i=>rps(P[i],outc(R2[i])));
  const acc=mean(ii.map(i=>P[i].indexOf(Math.max(...P[i]))===outc(R2[i])?1:0));return {B,L:mean(Lg),R:mean(Rp),acc};};
const eloS=runElo(E.START,E.K,E.H);
const M={
 'Poisson actuel de l\'appli (reconstitué)':R2.map(m=>model(TT(m.md),m.md,m.home,m.away,{form:true,streak:true})),
 'Elo actuel (elo.html)':R2.map(m=>eloS[m.home+'|'+m.away]),
 'Nouveau : valeur seule':evalP(1e9,1e9,H0),
 'Nouveau : valeur + résultats (λ=50)':evalP(50,1e9,H0),
 'Nouveau : + bonus domicile (λH=40)':evalP(50,40,H0),
 'Hasard (1/3 chacun)':R2.map(()=>[1/3,1/3,1/3])};
const FULL=M['Nouveau : + bonus domicile (λH=40)'];
const ref=sc(M['Poisson actuel de l\'appli (reconstitué)']).B, ref2=sc(FULL).B;
console.log('Test complet, journées 2 à 11 (82 matchs, chaque match prédit avec les seules données d\'avant) — sans absences, faute d\'historique\n');
console.log('Modèle'.padEnd(44),'Brier ','Log-loss','RPS   ','Bon résultat','vs Poisson actuel');
Object.keys(M).forEach(k=>{const s=sc(M[k]);const p=pairSE(s.B,ref);console.log(k.padEnd(44),mean(s.B).toFixed(4),' ',s.L.toFixed(4),'  ',s.R.toFixed(4),' ',(s.acc*100).toFixed(0)+' %'.padEnd(6),'  ',(p.m>=0?'+':'')+p.m.toFixed(4)+' ± '+p.se.toFixed(4));});
// calibration globale
const fr=[0,0,0],pm=[0,0,0];R2.forEach((m,i)=>{fr[outc(m)]++;FULL[i].forEach((x,k)=>pm[k]+=x);});
console.log('\nCalibration du modèle complet : prévu / réel  — victoire dom. '+(pm[0]/82*100).toFixed(1)+' % / '+(fr[0]/82*100).toFixed(1)+' %   nul '+(pm[1]/82*100).toFixed(1)+' % / '+(fr[1]/82*100).toFixed(1)+' %   victoire ext. '+(pm[2]/82*100).toFixed(1)+' % / '+(fr[2]/82*100).toFixed(1)+' %');
const bins=[[0,.15],[.15,.30],[.30,.45],[.45,.60],[.60,.75],[.75,1.01]];console.log('Fiabilité (toutes issues confondues) : proba prévue → fréquence réelle');
bins.forEach(([a,b])=>{let n=0,sp=0,sh=0;R2.forEach((m,i)=>FULL[i].forEach((x,k)=>{if(x>=a&&x<b){n++;sp+=x;sh+=(outc(m)===k?1:0);}}));console.log('   '+(a*100).toFixed(0).padStart(3)+'-'+Math.min(100,b*100).toFixed(0).padEnd(3)+' %  n='+String(n).padStart(3)+'  prévu '+(sp/n*100).toFixed(1)+' %  réel '+(sh/n*100).toFixed(1)+' %');});
console.log('\nSensibilité à l\'écart de niveau (1 = tel quel) :');
[0.6,0.8,1,1.2,1.4].forEach(s=>{const P=evalP(50,40,H0,s);console.log('   échelle',s,' Brier',mean(sc(P).B).toFixed(4));});
// ---- face au marché (45 matchs avec cotes) ----
const ii=[];R2.forEach((m,i)=>{if(ODDS[m.home+'|'+m.away])ii.push(i);});
const MKT=R2.map(m=>{const o=ODDS[m.home+'|'+m.away];return o?vig(o.o):null;});
console.log('\nFace au marché — '+ii.length+' matchs avec cotes moyennes (J6 à J11)');
const mk45=ii.map(i=>brier(MKT[i],outc(R2[i])));
console.log('   '+'Marché (cotes sans marge)'.padEnd(42),mean(mk45).toFixed(4));
Object.keys(M).filter(k=>k!=='Hasard (1/3 chacun)').forEach(k=>{const s=sc(M[k],ii);const p=pairSE(s.B,mk45);console.log('   '+k.padEnd(42),mean(s.B).toFixed(4),'  vs marché +'+p.m.toFixed(4)+' ± '+p.se.toFixed(4));});
console.log('\nMélange marché + nouveau modèle (poids du modèle) :');
[0,0.1,0.2,0.3,0.5,1].forEach(w=>{const B=ii.map(i=>brier(MKT[i].map((x,k)=>(1-w)*x+w*FULL[i][k]),outc(R2[i])));const p=pairSE(B,mk45);console.log('   poids '+w.toFixed(1)+'  Brier '+mean(B).toFixed(4)+'  vs marché '+(p.m>=0?'+':'')+p.m.toFixed(4)+' ± '+p.se.toFixed(4));});
// désaccords
console.log('\nQuand le nouveau modèle s\'écarte du marché (issue où il est le plus au-dessus du marché) :');
[0.05,0.08,0.10,0.15].forEach(th=>{let n=0,hit=0,sm=0,sM=0;ii.forEach(i=>{const dif=FULL[i].map((x,k)=>x-MKT[i][k]);const k=dif.indexOf(Math.max(...dif));if(dif[k]>=th){n++;sm+=FULL[i][k];sM+=MKT[i][k];if(outc(R2[i])===k)hit++;}});console.log('   écart ≥ '+(th*100).toFixed(0)+' pts : '+n+' matchs, réalisé '+hit+' ('+(n?(hit/n*100).toFixed(0):'-')+' %), prévu par le modèle '+(n?(sm/n*100).toFixed(0):'-')+' %, par le marché '+(n?(sM/n*100).toFixed(0):'-')+' %');});
