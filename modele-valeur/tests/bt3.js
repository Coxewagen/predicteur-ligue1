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
const SL={G:1,DC:2,DL:2,MI:3,AT:2,BU:1};
function xi(sq){const out=[];Object.keys(SL).forEach(g=>{const grp=sq.filter(p=>p[1]===g).slice();
  if(g==='G')grp.sort((a,b)=>(b[3]-a[3])||(b[2]-a[2]));else grp.sort((a,b)=>((b[3]>=E.IMP.MINREG)-(a[3]>=E.IMP.MINREG))||(b[2]-a[2]));out.push(...grp.slice(0,SL[g]));});return out;}
const sum=a=>a.reduce((s,p)=>s+p[2],0);
const AGG={
 'Total de l\'effectif':sq=>sum(sq),
 'XI type (titulaires habituels)':sq=>sum(xi(sq)),
 '11 joueurs les plus chers':sq=>sum(sq.slice().sort((a,b)=>b[2]-a[2]).slice(0,11)),
 '16 joueurs les plus chers':sq=>sum(sq.slice().sort((a,b)=>b[2]-a[2]).slice(0,16)),
 'XI type + 35 % du banc':sq=>{const x=xi(sq),s=new Set(x);return sum(x)+.35*sum(sq.filter(p=>!s.has(p)).sort((a,b)=>b[2]-a[2]).slice(0,7));},
};
// performances réelles J1→J11
const perf={};teams.forEach(t=>perf[t]={g:0,gd:0,pts:0});
MD.forEach(m=>{const a=perf[m.home],b=perf[m.away];a.g++;b.g++;a.gd+=m.hs-m.as;b.gd+=m.as-m.hs;a.pts+=m.hs>m.as?3:m.hs===m.as?1:0;b.pts+=m.as>m.hs?3:m.hs===m.as?1:0;});
const gd=teams.map(t=>perf[t].gd/perf[t].g),pp=teams.map(t=>perf[t].pts/perf[t].g);
const cor=(x,y)=>{const mx=mean(x),my=mean(y);return x.reduce((s,v,i)=>s+(v-mx)*(y[i]-my),0)/Math.sqrt(x.reduce((s,v)=>s+(v-mx)**2,0)*y.reduce((s,v)=>s+(v-my)**2,0));};
const rows2=MD.filter(m=>m.md>=2&&m.md<=11);
const polyBase=(()=>{const Tc={};const TT=D=>Tc[D]||(Tc[D]=stats(D));const B=rows2.map(m=>brier(model(TT(m.md),m.md,m.home,m.away,{form:1,streak:1}),outc(m)));return {B:mean(B),Bs:B};})();
console.log('Corrélation avec les résultats réels J1→J11 (1 = parfait) et Brier J2→J11 d\'un Elo qui part de cette valeur (meilleur réglage testé)\n');
console.log('Calcul de la valeur d\'équipe'.padEnd(36),'échelle'.padEnd(10),'corr. diff. buts','corr. points','meilleur Brier (K=25, c)');
const best={};
Object.keys(AGG).forEach(k=>{const v=teams.map(t=>AGG[k](E.SQUADS[t]));
  [['brute',x=>x],['racine',Math.sqrt],['ln',Math.log]].forEach(([sc,f])=>{const z=v.map(f);
    let bb=9,bc=0;[10,20,30,40,60,80,100,130,160,200,260].forEach(c=>{const zs={};teams.forEach((t,i)=>zs[t]=z[i]);const mz=mean(z),sd=Math.sqrt(mean(z.map(x=>(x-mz)**2)));
      const init={};teams.forEach((t,i)=>init[t]=1500+c*(z[i]-mz)/sd);const o=runElo(init,25,E.H);const B=mean(rows2.map(m=>brier(o[m.home+'|'+m.away],outc(m))));if(B<bb){bb=B;bc=c;}});
    console.log(k.padEnd(36),sc.padEnd(10),cor(z,gd).toFixed(2).padEnd(17),cor(z,pp).toFixed(2).padEnd(13),bb.toFixed(4)+'  (c='+bc+')');});});
