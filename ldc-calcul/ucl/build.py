import json, html
from datetime import datetime, timedelta
P=json.load(open('preds.json'))
FR={"Atlético Madrid":"Atlético","Internazionale":"Inter","Paris Saint-Germain":"PSG","Manchester City":"Man City","Manchester United":"Man United","Borussia Dortmund":"Dortmund","Feyenoord Rotterdam":"Feyenoord","Bodo/Glimt":"Bodø/Glimt","Slavia Prague":"Slavia Prague","Sporting CP":"Sporting","Real Betis":"Betis","VfB Stuttgart":"Stuttgart","Bayern Munich":"Bayern","Shakhtar Donetsk":"Shakhtar","Slovan Bratislava":"Slovan","LASK Linz":"LASK","AEK Athens":"AEK","FC Porto":"Porto","PSV Eindhoven":"PSV","Club Brugge":"Bruges","RB Leipzig":"Leipzig","Viking FK":"Viking","Sabah FK":"Sabah","AS Roma":"Roma","Fenerbahce":"Fenerbahçe"}
n=lambda t: html.escape(FR.get(t,t))
f2=lambda x: f"{x:.2f}".replace('.',',')
pc=lambda x: f"{x*100:.0f} %"
logo=lambda i,t: f'<img src="https://a.espncdn.com/i/teamlogos/soccer/500/{i}.png" alt="" onerror="this.style.visibility=\'hidden\'">'
JOURS=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
MOIS=["","janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
rows=[]; cur=None
G2=json.load(open('allgames2.json'));
for _l in open('ucl_res.csv',encoding='utf-8'):
    _p=_l.strip().split(';')
    if len(_p)==6 and _p[0]>='2026-11-02': G2.append([_p[0]+'T20:00','League Phase',_p[1],_p[2],int(_p[3]),int(_p[4]),0])
ABL=json.load(open('absl.json')); AE=json.load(open('abs.json')); HT=json.load(open('hfa_team.json'))
def form(t,before):
    L=[g for g in G2 if t in (g[2],g[3]) and g[0][:10]<before[:10]][-6:][::-1]; out=[]
    for g in L:
        home=g[2]==t; gf,ga=(g[4],g[5]) if home else (g[5],g[4]); r='V' if gf>ga else ('N' if gf==ga else 'D')
        comp='LdC' if g[1].startswith('League') else ('Coupe' if 'Round' in g[1] else 'Champ.')
        out.append([g[0][8:10]+'/'+g[0][5:7],FR.get(g[3] if home else g[2],g[3] if home else g[2]),('dom.' if home else 'ext.'),f"{gf}-{ga}",r,comp])
    allg=[g for g in G2 if t in (g[2],g[3]) and g[0][:10]<before[:10]][::-1]
    def res(g):
        home=g[2]==t; gf,ga=(g[4],g[5]) if home else (g[5],g[4]); return 'V' if gf>ga else ('N' if gf==ga else 'D')
    rs=[res(g) for g in allg]; st=''
    if rs:
        if rs[0]=='V':
            n=next((i for i,x in enumerate(rs) if x!='V'),len(rs)); st=f"{n} victoire{'s' if n>1 else ''} de suite"
        else:
            n=next((i for i,x in enumerate(rs) if x=='V'),len(rs)); st=f"{n} match{'s' if n>1 else ''} sans victoire"
            if rs[0]=='D':
                m=next((i for i,x in enumerate(rs) if x!='D'),len(rs))
                if m>1: st=f"{m} défaites de suite · "+st
    return out,st
MD={}
ORD=list(json.load(open('odds.json')).keys())
def mkcards(P,jn):
    rows=[]; cur=None
    for x in sorted(P,key=lambda x:(x['date'][:10],ORD.index(x['h']) if x['h'] in ORD else 99)):
        dt=datetime.strptime(x['date'][:16],"%Y-%m-%dT%H:%M")+timedelta(hours=1)
        day=f"{JOURS[dt.weekday()]} {dt.day} {MOIS[dt.month]}"
        if day!=cur:
            if cur is not None: rows.append('</div>')
            cur=day; rows.append(f'<h2 class="day" data-d="{dt:%d}">{day}</h2><div class="grid" data-d="{dt:%d}">')
        fav=0 if x['ph']>=x['pa'] else 2
        cls=lambda k: ' class="fav"' if k==fav else ''
        lab=x['label'].replace(x['h'],FR.get(x['h'],x['h'])).replace(x['a'],FR.get(x['a'],x['a']))
        if x['reco']=='none':
            t=x['h'] if x['ph']>=x['pa'] else x['a']; lab=FR.get(t,t)+' ou nul'; x['reco']='dc'
        o=x['odds']; contra = o and ((0 if o[0]<=o[2] else 2)!=(0 if x['mod'][0]>=x['mod'][2] else 2))
        pill=f'<span class="pill {x["reco"]}">{html.escape(lab)}</span>'
        mh,md,ma=x['mod']; pw=mh if fav==0 else ma; pdc=pw+md
        ow=odc=None; w='—'
        if x['odds']:
            oo=x['odds']; ow=oo[0] if fav==0 else oo[2]; odc=1.035/(1/ow+1/oo[1])
            def chip(lbl,od,p,ap):
                g=od>=1/p; return f'<div class="wl"><span class="wn">{lbl}</span><span class="w {"good" if g else "bad"}" data-k="{lbl}" data-p="{p:.4f}">{ap}{f2(od)} {"✓" if g else "✗"}</span></div>'
            w=chip('Ou nul',odc,pdc,'≈')+chip('Sec',ow,pw,'')
        else:
            w=''.join(f'<div class="wl"><span class="wn">{l_}</span><span class="w" data-k="{l_}" data-p="{p_:.4f}">—</span></div>' for l_,p_ in (('Ou nul',pdc),('Sec',pw)))
        o=x['odds']
        od=f'<span class="o">{f2(o[0])} · {f2(o[1])} · {f2(o[2])}</span>' if o else '<span class="o"></span>'
        gid=f"{x['hid']}-{x['aid']}"
        fh,sh=form(x['h'],x['date']); fa,sa=form(x['a'],x['date'])
        MD[gid]=dict(h=FR.get(x['h'],x['h']),a=FR.get(x['a'],x['a']),hid=x['hid'],aid=x['aid'],p=[round(v*100) for v in x['mod']],sc=x['score'],eh=x['eh'],ea=x['ea'],hfa=HT.get(x['h'],56),
          ah=ABL.get(x['h'],{'o':[],'d':[]}),aa=ABL.get(x['a'],{'o':[],'d':[]}),xh=AE.get(x['h'],0),xa=AE.get(x['a'],0),fh=fh,fa=fa,sh=sh,sa=sa,lab=x['label'],pr=round(x['prob']*100))
        pr=[x["ph"],x["pd"],x["pa"]]
        rows.append(f'''<div class="card" data-g="{gid}" data-h="{x['hid']}" data-a="{x['aid']}" data-fav="{fav}" data-t="{x['reco']}" data-j="{jn}" data-date="{dt:%Y-%m-%d}" data-day="{dt:%d}" data-en="{html.escape(x['h'])}|{html.escape(x['a'])}" data-pw="{pw:.4f}" data-pdc="{pdc:.4f}" data-ow="{ow or 0:.3f}" data-odc="{odc or 0:.3f}">
<div class="ctop"><span class="t">{dt:%H:%M}</span><span class="res"></span></div>
<div class="teams"><div class="tm">{logo(x["hid"],x["h"])}<b>{n(x["h"])}</b></div><div class="mid"><span class="live"></span><span class="pv">{x["score"]}</span></div><div class="tm">{logo(x["aid"],x["a"])}<b>{n(x["a"])}</b></div></div>
<div class="bar"><i class="bh{' f' if fav==0 else ''}" style="width:{pr[0]*100:.1f}%"></i><i class="bd" style="width:{pr[1]*100:.1f}%"></i><i class="ba{' f' if fav==2 else ''}" style="width:{pr[2]*100:.1f}%"></i></div>
<div class="pcts"><span{cls(0)}>{pc(pr[0])}</span><span>{pc(pr[1])}</span><span{cls(2)}>{pc(pr[2])}</span></div>
<div class="cbot"><div>{pill}<div class="sub">{pc(x["prob"])} · mini {f2(x["mini"])}</div></div><div class="wx">{w}{od}</div></div>
<div class="betz"><label class="bet"><input type="checkbox"><span>J’ai parié</span></label><div class="ch"><button type="button" data-c="p">Ou nul</button><button type="button" data-c="w">Victoire sèche</button></div></div>
</div>''')
    if cur is not None: rows.append('</div>')
    return rows

PJ={'4':P}
for _j in '5678': PJ[_j]=json.load(open(f'preds_j{_j}.json'))
JC={}; JL={}; DAYS={}; ALLFX={}
for _j,_P in PJ.items():
    JC[_j]=mkcards(_P,_j)
    _ds=sorted({x['date'][:10] for x in _P}); JL[_j]=(datetime.strptime(_ds[-1]+'T'+max(x['date'][11:16] for x in _P if x['date'][:10]==_ds[-1]),"%Y-%m-%dT%H:%M")+timedelta(hours=1)).strftime('%Y-%m-%d')
    DAYS[_j]=[]
    for _d in _ds:
        _dd=datetime.strptime(_d,'%Y-%m-%d'); DAYS[_j].append([f"{_dd:%d}",JOURS[_dd.weekday()]])
    for x in _P: ALLFX[(x['h'],x['a'])]=f"{x['hid']}-{x['aid']}"
FIN={}
for _l in open('ucl_res.csv',encoding='utf-8'):
    _p=_l.strip().split(';')
    if len(_p)==6 and _p[0]>='2026-11-02' and (_p[1],_p[2]) in ALLFX: FIN[ALLFX[(_p[1],_p[2])]]={'h':int(_p[3]),'a':int(_p[4]),'state':'post','txt':'Terminé'}
import csv
from collections import OrderedDict
OLD=OrderedDict([('1',('08','09','10')),('2',('13','14')),('3',('20','21'))])
_res=[r for r in csv.reader(open('ucl_res.csv',encoding='utf-8'),delimiter=';') if r]
def _dl(d):
    dd=datetime.strptime(d,'%Y-%m-%d'); return f"{JOURS[dd.weekday()]} {dd.day} {MOIS[dd.month]}"
OLDH=''; BTN={}
for j,days in OLD.items():
    h=''; bs=['<button type="button" data-j="'+j+'" data-d="all" class="on">Tout</button>']
    for k,dy in enumerate(days):
        rr=[r for r in _res if r[0][8:10]==dy and r[0][5:7] in ('09','10')]
        if not rr: continue
        h+=f'<h2 class="day" data-j="{j}" data-d="{dy}">{_dl(rr[0][0])}</h2><div class="olist" data-j="{j}" data-d="{dy}">'+''.join(f'<div class="orow"><b>{n(r[1])}</b><span class="osc">{r[3]}-{r[4]}</span><b>{n(r[2])}</b></div>' for r in rr)+'</div>'
        bs.append(f'<button type="button" data-j="{j}" data-d="{dy}">{_dl(rr[0][0]).split()[0]} {int(dy)}</button>')
    OLDH+=h; BTN[j]=''.join(bs)
j4=sorted({r for r in []})
for _j in '45678':
    BTN[_j]='<button type="button" data-j="'+_j+'" data-d="all" class="on">Tout</button>'+(''.join(f'<button type="button" data-j="{_j}" data-d="{dd}">{lb} {int(dd)}</button>' for dd,lb in DAYS[_j]) if len(DAYS[_j])>1 else '')+f'<button type="button" data-j="{_j}" data-d="live">● En direct</button>'
NAV='<div class="nav" id="nj">'+''.join(f'<button type="button" data-j="{j}" class="">J{j}</button>' for j in '12345678')+'</div><div class="nav sub" id="nd">'+''.join(f'<span class="ds" data-j="{j}" hidden>{b}</span>' for j,b in BTN.items())+'</div>'
NAVJS="""<script>(function(){var J=window.CJ||'4',D='all';function ap(){var isNew=+J>=4,LV=D==='live';window.CJ=J;document.getElementById('ttl').textContent='Ligue des champions \u00b7 Journ\u00e9e '+J;document.querySelectorAll('#nj button').forEach(function(b){b.classList.toggle('on',b.dataset.j===J)});document.querySelectorAll('#nd .ds').forEach(function(s){s.hidden=s.dataset.j!==J});document.querySelectorAll('#nd .ds[data-j="'+J+'"] button').forEach(function(b){b.classList.toggle('on',b.dataset.d===D)});var cur=document.getElementById('cur');cur.hidden=!isNew;document.getElementById('old').hidden=isNew;['combo','recap','lmsg'].forEach(function(i){var e=document.getElementById(i);if(e)e.style.display=isNew?'':'none'});document.querySelectorAll('#cur .jc').forEach(function(e){e.hidden=e.dataset.j!==J});document.querySelectorAll('#cur .jc[data-j="'+J+'"] [data-d]').forEach(function(e){e.hidden=!(D==='all'||e.dataset.d===D)});cur.style.display=LV?'none':'';var lb=document.getElementById('livebox'),nm=document.getElementById('nolive'),H='';if(LV){document.querySelectorAll('#cur .card').forEach(function(c){var l=(window.LIVE||{})[c.dataset.h+'-'+c.dataset.a];if(!(l&&l.state==='in'))return;var n=(c.dataset.en||'|').split('|'),r=c.querySelector('.res');H+='<div class="lrow"><span class="ln">'+n[0]+'</span><b class="ls">'+l.h+' - '+l.a+'</b><span class="ln">'+n[1]+'</span><span class="lm">'+(l.txt||'')+'</span>'+(r&&r.textContent?'<span class="'+r.className+'">'+r.textContent+'</span>':'')+'</div>'})}lb.hidden=!LV;lb.innerHTML=LV?H:'';nm.hidden=!(LV&&!H);document.querySelectorAll('#old [data-j]').forEach(function(e){e.hidden=!(e.dataset.j===J&&(D==='all'||e.dataset.d===D))});}
document.addEventListener('click',function(e){var b=e.target.closest('#nj button');if(b){J=b.dataset.j;D='all';ap();if(window.__paint)window.__paint();return;}b=e.target.closest('#nd button');if(b){D=b.dataset.d;ap();}});window.__ap=ap;ap();setInterval(function(){if(D==='live')ap()},3000);})();</script><style>[hidden]{display:none!important}#nj{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}#nj button{padding:9px 0;font-size:21px;text-align:center}@media(min-width:700px){#nj{grid-template-columns:repeat(8,84px)}}#livebox .lrow{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr) 44px;align-items:center;gap:2px 8px;padding:7px 2px;border-bottom:1px solid #1d3a2a;font-size:16px;font-weight:800}#livebox .ln{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#livebox .ln:first-child{text-align:right}#livebox .ls{font-size:24px;color:#ffc83d;text-align:center;white-space:nowrap}#livebox .lm{font-size:14px;color:#9fd3b0;text-align:right}#livebox .res{grid-column:1/5;justify-self:center;font-size:13px;padding:1px 10px}</style>"""
JS=r'''<script>
(function(){
var K='ldc_j4_bets',B={};try{B=JSON.parse(localStorage.getItem(K)||'{}')||{}}catch(e){}
var L={};
function pD(){var p=new Intl.DateTimeFormat('en-US',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()),o={};p.forEach(function(x){o[x.type]=x.value});return o.year+'-'+o.month+'-'+o.day}
function AD(){var t=Date.parse(pD()),s={};document.querySelectorAll('.card[data-date]').forEach(function(c){var d=c.dataset.date,k=(Date.parse(d)-t)/864e5;if(k>=-2&&k<=1)s[d]=1});return Object.keys(s).sort()}
function defJ(){var t=pD(),r='8';['4','5','6','7','8'].some(function(j){if(JL[j]>=t){r=j;return true}return false});return r}
window.CJ=defJ();
function KPf(){return window.CJ==='4'?'ldc_j4':'ldc_j'+window.CJ}
function save(){try{localStorage.setItem(K,JSON.stringify(B))}catch(e){}}
function paint(){
  var n=0,w=0,wait=0,items=[];
  document.querySelectorAll('[data-g]').forEach(function(tr){
    var g=tr.dataset.g,cb=tr.querySelector('.bet input'),on=!!B[g];cb.checked=on;tr.classList.toggle('betted',on);var typ=(B[g]==='w'||(B[g]===1&&tr.dataset.t==='win'))?'win':'dc';tr.querySelectorAll('.ch button').forEach(function(x){x.classList.toggle('on',(B[g]==='w')===(x.dataset.c==='w'))});
    var l=L[g],lv=tr.querySelector('.live'),rs=tr.querySelector('.res');
    lv.innerHTML=l&&l.state!=='pre'?l.h+'-'+l.a+'<span class="st'+(l.state==='post'?' ft':'')+'">'+l.txt+'</span>':'';
    var res=null;
    if(l&&l.state==='post'){var o=l.h>l.a?0:(l.h===l.a?1:2),f=+tr.dataset.fav;res=typ==='win'?o===f:o!==(f===0?2:0);}
    rs.className='res'+(res===null?'':(res?' ok':' ko'));rs.textContent=on&&res!==null?(res?'✓ Gagné':'✗ Perdu'):'';
    if(on&&l&&l.state==='in'){var o3=l.h>l.a?0:(l.h===l.a?1:2),f3=+tr.dataset.fav,c3=typ==='win'?o3===f3:o3!==(f3===0?2:0);rs.className='res '+(c3?'lok':'lko');rs.textContent=c3?'● En bonne voie':'● Mal parti';}
    if(on&&tr.dataset.j===window.CJ){n++;if(res===null)wait++;else if(res)w++;
      var nm=tr.querySelectorAll('.tm b'),st,cl;
      if(res===true){st='✓ Gagné';cl='ok';}else if(res===false){st='✗ Perdu';cl='ko';}
      else if(l&&l.state==='in'){var o2=l.h>l.a?0:(l.h===l.a?1:2),f2=+tr.dataset.fav,cur=typ==='win'?o2===f2:o2!==(f2===0?2:0);st=l.h+'-'+l.a+' · '+(cur?'en bonne voie':'mal parti');cl='lv';}
      else{st='À venir · '+tr.querySelector('.t').textContent;cl='wt';}
      items.push('<div class="rl"><span><b>'+nm[0].textContent+' – '+nm[1].textContent+'</b> · '+(function(){var nm2=tr.querySelectorAll('.tm b'),fv=nm2[+tr.dataset.fav===0?0:1].textContent;return typ==='win'?'Victoire '+fv:fv+' ou nul'})()+'</span><span class="s '+cl+'">'+st+'</span></div>');}
  });
  var lost=n-w-wait;
  document.getElementById('recap').innerHTML=n?('<h2>Récap de mes paris</h2><div class="tiles"><div class="tile"><b>'+n+'</b><span>Pariés</span></div><div class="tile g"><b>'+w+'</b><span>Gagnés</span></div><div class="tile r"><b>'+lost+'</b><span>Perdus</span></div><div class="tile y"><b>'+wait+'</b><span>À venir</span></div></div>'+items.join('')):'';

  var OD={};try{OD=JSON.parse(localStorage.getItem('ldc_j4_odds')||'{}')||{}}catch(e){}
  var KP=KPf(),DL=DAYS[window.CJ]||[],CM='all';try{CM=localStorage.getItem(KP+'_cm')||'all'}catch(e){}if(DL.length<2||!DL.some(function(x){return x[0]===CM}))CM='all';
  var FZ={},fzd=false;try{FZ=JSON.parse(localStorage.getItem('ldc_j4_frz')||'{}')||{}}catch(e){}
  Object.keys(FZ).forEach(function(k){if(!B[k]){delete FZ[k];fzd=true}});
  var C=[];document.querySelectorAll('[data-g]').forEach(function(tr){var g=tr.dataset.g;if(!B[g])return;if(tr.dataset.j!==window.CJ)return;if(CM!=='all'&&tr.dataset.day!==CM)return;var sec=(B[g]==='w')||(B[g]===1&&tr.dataset.t==='win');
    var p=+(sec?tr.dataset.pw:tr.dataset.pdc),od=+(sec?tr.dataset.ow:tr.dataset.odc),ok2=g+(sec?'w':'p'),l=L[g],r=null;if(!FZ[g]&&+tr.dataset.ow>0){FZ[g]={ow:tr.dataset.ow,odc:tr.dataset.odc};fzd=true;}if(FZ[g])od=+(sec?FZ[g].ow:FZ[g].odc);if(OD[ok2])od=OD[ok2];
    if(l&&l.state==='post'){var o=l.h>l.a?0:(l.h===l.a?1:2),f=+tr.dataset.fav;r=sec?o===f:o!==(f===0?2:0);}
    var nm=tr.querySelectorAll('.tm b'),fv=nm[+tr.dataset.fav===0?0:1].textContent;C.push({k:ok2,man:!!OD[ok2],lab:(sec?'Victoire '+fv:fv+' ou nul'),p:p,od:od,r:r,m:nm[0].textContent+' – '+nm[1].textContent});});
  if(fzd){try{localStorage.setItem('ldc_j4_frz',JSON.stringify(FZ))}catch(x){}}
  var cb=document.getElementById('combo');
  var seg=DL.length<2?'':'<div class="seg">'+DL.concat([['all','Les deux jours']]).map(function(x){return '<button type="button" data-cm="'+x[0]+'" class="'+(CM===x[0]?'on':'')+'">'+x[1]+'</button>'}).join('')+'</div>';
  if(document.activeElement&&(document.activeElement.id==='mise'||document.activeElement.id==='boost'||document.activeElement.classList.contains('cod'))){}else if(!n){cb.innerHTML='';}else if(C.length<2){cb.innerHTML='<h2>Combiné</h2>'+seg+'<div style="color:var(--mut);font-size:17px">Coche au moins 2 matchs</div>';}else{
    var P=1,O=1,ok=true,lost=false,done=0;C.forEach(function(c){P*=c.p;if(c.od)O*=c.od;else ok=false;if(c.r===false)lost=true;if(c.r!==null)done++;});
    var f2=function(v){return v.toFixed(2).replace('.',',')},pc=function(v){return Math.round(v*100)+' %'};
    var rows=C.map(function(c){return '<tr><td><b>'+c.lab+'</b><br><span style="color:var(--mut);font-size:15px">'+c.m+'</span></td><td class="n">'+pc(c.p)+'</td><td class="n"><input class="cod" data-k="'+c.k+'" type="text" inputmode="decimal" value="'+(c.od?f2(c.od):'')+'"></td><td class="n">'+(c.r===null?'':(c.r?'✓':'✗'))+'</td></tr>'}).join('');
    var st=lost?'<span class="res ko">✗ Perdu</span>':(done===C.length?'<span class="res ok">✓ Gagné</span>':'');
    var sv='';try{sv=localStorage.getItem(KP+'_mise_'+CM)||''}catch(e){}
    var prev=document.getElementById('mise');if(prev&&prev.dataset.cm===CM)sv=prev.value;var bv='';try{bv=localStorage.getItem(KP+'_boost_'+CM)||''}catch(e){}var pb=document.getElementById('boost');if(pb&&prev&&prev.dataset.cm===CM)bv=pb.value;
    cb.innerHTML='<h2>Combiné · '+C.length+' matchs '+st+'</h2>'+seg+'<table><tr><th>Pari</th><th class="n">Réussite</th><th class="n">Cote</th><th></th></tr>'+rows
      +'<tr class="tot"><td>Total</td><td class="n">'+pc(P)+'</td><td class="n">'+(ok?f2(O):'—')+'</td><td></td></tr></table>'
      +'<div style="margin-top:8px;font-size:17px;color:var(--mut)">Cote mini <b style="color:var(--ink)">'+f2(1/P)+'</b></div>'
      +'<div class="stk"><label for="mise">Mise</label><input id="mise" data-cm="'+CM+'" type="number" inputmode="decimal" min="0" step="0.5" value="'+sv+'"><span>€</span><label for="boost" style="margin-left:14px">Booster</label><input id="boost" class="bst" type="number" inputmode="decimal" min="0" step="1" value="'+bv+'"><span>%</span></div><div class="gain" id="gain"></div>';
    var gain=function(){var v=parseFloat(String(document.getElementById('mise').value).replace(',','.'))||0,el=document.getElementById('gain');try{localStorage.setItem(KP+'_mise_'+CM,document.getElementById('mise').value)}catch(e){}
      if(!v||!ok){el.innerHTML='';return;}var g=v*O,fm=function(x){return f2(x)+' €'};
      var bo=parseFloat(String(document.getElementById('boost').value).replace(',','.'))||0;try{localStorage.setItem(KP+'_boost_'+CM,document.getElementById('boost').value)}catch(e){}
      var net=(g-v)*(1+bo/100),tot=v+net;
      el.innerHTML=lost?'<span>Perdu <b class="no">−'+fm(v)+'</b></span>':'<span>Gain <b>'+fm(tot)+'</b></span><span>Bénéfice <b class="yes">+'+fm(net)+'</b></span>'+(bo?'<span>dont booster <b class="yes">+'+fm(net-(g-v))+'</b></span>':'');};
    document.getElementById('mise').oninput=gain;document.getElementById('boost').oninput=gain;gain();
  }
}
document.addEventListener('click',function(e){var sg=e.target.closest('.seg button');if(sg){try{localStorage.setItem(KPf()+'_cm',sg.dataset.cm)}catch(x){}paint();return;}var bt=e.target.closest('.ch button');if(!bt)return;var tr=bt.closest('[data-g]');B[tr.dataset.g]=bt.dataset.c;save();paint();});
document.addEventListener('change',function(e){if(!e.target.classList.contains('cod'))return;var v=parseFloat(String(e.target.value).replace(',','.'));var OD={};try{OD=JSON.parse(localStorage.getItem('ldc_j4_odds')||'{}')||{}}catch(x){}if(v>1)OD[e.target.dataset.k]=v;else delete OD[e.target.dataset.k];try{localStorage.setItem('ldc_j4_odds',JSON.stringify(OD))}catch(x){}e.target.blur();paint();});
document.addEventListener('change',function(e){var tr=e.target.closest('[data-g]');if(!tr)return;if(e.target.checked)B[tr.dataset.g]=(tr.dataset.t==='win'?'w':'p');else delete B[tr.dataset.g];save();paint();});
function lab(st){var n=(st.type&&st.type.name)||'';if(n==='STATUS_HALFTIME')return 'Mi-temps';if(st.type&&st.type.state==='post')return 'Terminé';return st.displayClock||'';}
var UM={'52319':'510','2609356':'21922','52277':'175','79946':'2572','52498':'494','52280':'359','2603790':'11420','52919':'382','50062':'148','50043':'570','50064':'437','50136':'114','52758':'124','52265':'244','50129':'887','50051':'86','52692':'436','7889':'364','63405':'4411','52797':'521','70691':'102','52747':'160','59333':'2980','75797':'166','52749':'142','50138':'110','52682':'360','50137':'104','50124':'1068','50037':'132','50080':'83','52683':'362','50067':'432','50107':'134','52707':'493','50149':'2250'};
async function uefa(){
  var ds=AD();if(!ds.length)return null;var u='https://match.uefa.com/v5/matches?competitionId=1&fromDate='+ds[0]+'&toDate='+ds[ds.length-1]+'&limit=40&offset=0&_='+Date.now(),j=null;
  var CH=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.CapacitorHttp;
  try{if(CH){var rr=await CH.get({url:u});j=(typeof rr.data==='string')?JSON.parse(rr.data):rr.data;}else{var r=await fetch(u,{cache:'no-store'});if(!r.ok)return null;j=await r.json();}}catch(e){return null}
  if(!Array.isArray(j)||!j.length)return null;
  var out={};j.forEach(function(m){var h=UM[m.homeTeam&&m.homeTeam.id],a=UM[m.awayTeam&&m.awayTeam.id];if(!h||!a)return;var t=(m.score&&m.score.total)||{home:0,away:0},st=m.status==='LIVE'?'in':(m.status==='FINISHED'?'post':'pre');
    var tx='';if(st==='in'){tx=(m.phase==='HALF_TIME'||m.phase==='HALF_TIME_BREAK')?'Mi-temps':((m.minute&&m.minute.normal!=null?m.minute.normal:'')+(m.minute&&m.minute.injuryTime?'+'+m.minute.injuryTime:'')+"'");}else if(st==='post')tx='Terminé';
    out[h+'-'+a]={h:+t.home||0,a:+t.away||0,state:st,txt:tx};});
  return out;
}
function notif(t,b){var LN=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.LocalNotifications;if(LN){try{LN.schedule({notifications:[{id:Math.floor(Math.random()*2000000000),title:t,body:b,schedule:{at:new Date(Date.now()+300)}}]}).catch(function(){})}catch(e){}}else if(window.Notification&&Notification.permission==='granted'){try{new Notification(t,{body:b})}catch(e){}}}
(function(){var LN=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.LocalNotifications;if(LN){try{LN.requestPermissions().catch(function(){})}catch(e){}}else if(window.Notification&&Notification.permission==='default'){document.addEventListener('click',function f(){document.removeEventListener('click',f);try{Notification.requestPermission()}catch(e){}})}})();
var NS='';
async function nstat(){var LN=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.LocalNotifications;if(!LN){NS=(window.Notification?(Notification.permission==='granted'?'\uD83D\uDD14 ok':'\uD83D\uDD15 non'):'\uD83D\uDD15 module absent');return}try{var r=await LN.checkPermissions();NS=r.display==='granted'?'\uD83D\uDD14 ok':'\uD83D\uDD15 '+(r.display==='denied'?'refus\u00e9':'\u00e0 autoriser');}catch(e){NS='\uD83D\uDD15 erreur'}}
document.addEventListener('click',async function(e){if(!e.target.closest('#lmsg'))return;var LN=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.LocalNotifications;if(LN){try{await LN.requestPermissions()}catch(x){}}else if(window.Notification&&Notification.permission==='default'){try{await Notification.requestPermission()}catch(x){}}await nstat();notif('\u26BD Test','Notification de test');var m=document.getElementById('lmsg');if(m)m.textContent=m.textContent.replace(/ \u00b7 \uD83D.*$/,'')+' \u00b7 '+NS;});
nstat();setInterval(nstat,20000);
function nrm(x){return String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ø/g,'o').replace(/[^a-z ]/g,'').trim()}
function nmt(a,b){a=nrm(a);b=nrm(b);return !!a&&!!b&&(a===b||a.indexOf(b)===0||b.indexOf(a)===0)}
async function lscore(){
  var out={},any=false,CH=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.CapacitorHttp;
  var cards=[].slice.call(document.querySelectorAll('.card[data-en]'));
  for(const d of AD().map(function(x){return x.replace(/-/g,'')})){
    try{var u='https://prod-cdn-public-api.livescore.com/v1/api/app/date/soccer/'+d+'/1?locale=en&countryCode=FR&_='+Date.now(),j=null;
      if(CH){try{var rr=await CH.get({url:u});j=(typeof rr.data==='string')?JSON.parse(rr.data):rr.data;}catch(x){j=null}}
      if(!j){var r=await fetch(u,{cache:'no-store'});if(!r.ok)continue;j=await r.json();}
      any=true;
      (j.Stages||[]).forEach(function(s){if(s.CompN!=='Champions League'||s.CompD!=='UEFA')return;(s.Events||[]).forEach(function(e){var h=e.T1&&e.T1[0]&&e.T1[0].Nm,a=e.T2&&e.T2[0]&&e.T2[0].Nm;if(!h||!a)return;
        var c=cards.filter(function(c){var p=c.dataset.en.split('|');return nmt(p[0],h)&&nmt(p[1],a)})[0];if(!c)return;
        var ep=String(e.Eps||''),st=ep==='FT'||ep==='AET'||ep==='AP'?'post':(ep==='NS'||ep===''||/^\d{1,2}:\d{2}/.test(ep)?'pre':'in');
        out[c.dataset.h+'-'+c.dataset.a]={h:+e.Tr1||0,a:+e.Tr2||0,state:st,txt:st==='in'?(ep==='HT'?'Mi-temps':ep):(st==='post'?'Terminé':'')};});});
    }catch(e){}
  }
  return any?out:null;
}
async function fotmob(){
  var out={},any=false,CH=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.CapacitorHttp;
  var cards=[].slice.call(document.querySelectorAll('.card[data-en]'));
  for(const d of AD().map(function(x){return x.replace(/-/g,'')})){
    try{var u='https://www.fotmob.com/api/data/matches?date='+d+'&timezone=Europe/Paris&_='+Date.now(),j=null;
      if(CH){try{var rr=await CH.get({url:u});j=(typeof rr.data==='string')?JSON.parse(rr.data):rr.data;}catch(x){j=null}}
      if(!j){var r=await fetch(u,{cache:'no-store'});if(!r.ok)continue;j=await r.json();}
      any=true;
      (j.leagues||[]).forEach(function(l){if(l.primaryId!==42&&l.name!=='Champions League')return;(l.matches||[]).forEach(function(m){var h=m.home&&m.home.name,a=m.away&&m.away.name,st=m.status||{};if(!h||!a)return;
        var c=cards.filter(function(c){var p=c.dataset.en.split('|');return nmt(p[0],h)&&nmt(p[1],a)})[0];if(!c)return;
        var s2=st.finished?'post':(st.started&&!st.cancelled?'in':'pre'),lt=(st.liveTime&&st.liveTime.short)||'';
        out[c.dataset.h+'-'+c.dataset.a]={h:+m.home.score||0,a:+m.away.score||0,state:s2,txt:s2==='in'?(lt==='HT'?'Mi-temps':lt):(s2==='post'?'Terminé':'')};});});
    }catch(e){}
  }
  return any?out:null;
}
async function tick(){
  var out={},ok=false,src='',eo={};
  if(!AD().length){var m0=document.getElementById('lmsg');if(m0)m0.textContent=NS||'';paint();return;}
  var pr=await Promise.all([uefa(),lscore(),fotmob()]);var uo=pr[0],lo=pr[1],fo=pr[2];
  for(const d of AD().map(function(x){return x.replace(/-/g,'')})){
    try{var u='https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard?dates='+d+'&_='+Date.now(),j=null;var CH=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.CapacitorHttp;if(CH){try{var rr=await CH.get({url:u});j=(typeof rr.data==='string')?JSON.parse(rr.data):rr.data;}catch(x){j=null}}if(!j){var r=await fetch(u,{cache:'no-store'});if(!r.ok)continue;j=await r.json();}ok=true;
      (j.events||[]).forEach(function(e){var c=e.competitions[0],h=c.competitors.find(x=>x.homeAway==='home'),a=c.competitors.find(x=>x.homeAway==='away');
        eo[h.team.id+'-'+a.team.id]={h:+h.score||0,a:+a.score||0,state:e.status.type.state,txt:lab(e.status)};});
    }catch(e){}
  }
  var SR=[['UEFA',uo],['LiveScore',lo],['FotMob',fo],['ESPN',Object.keys(eo).length?eo:null]].filter(function(x){return x[1]}),RK={pre:0,in:1,post:2};
  SR.forEach(function(x,i){Object.keys(x[1]).forEach(function(k){var n=x[1][k],o=out[k];if(!o||(n.h+n.a>o.h+o.a)||(n.h+n.a===o.h+o.a&&RK[n.state]>RK[o.state]))out[k]=n;});});
  ok=SR.length>0;src=SR.map(function(x){return x[0]}).join('+');
  if(ok){if(window.__pl){Object.keys(out).forEach(function(k){var n=out[k],o=window.__pl[k];if(!o||o.state!=='in'||n.state!=='in')return;if(n.h+n.a<=o.h+o.a)return;var c=document.querySelector('[data-g][data-h="'+k.split('-')[0]+'"][data-a="'+k.split('-')[1]+'"]');var nm=c?(c.dataset.en||'|').split('|'):['',''];var sc=n.h>o.h?nm[0]:nm[1];notif('\u26BD BUT ! '+nm[0]+' '+n.h+' - '+n.a+' '+nm[1],sc+' marque'+(n.txt?' \u00b7 '+n.txt:''));});}window.__pl=JSON.parse(JSON.stringify(out));}
  if(ok){Object.assign(L,out);window.LIVE=L;try{localStorage.setItem('ldc_j4_live',JSON.stringify(L))}catch(e){}}
  var t=new Date().toLocaleTimeString('fr-FR',{timeZone:'Europe/Paris',hour:'2-digit',minute:'2-digit'});
  document.getElementById('lmsg').textContent=(ok?'Scores '+src+' · '+t:'Scores indisponibles')+(NS?' · '+NS:'');
  paint();
}

function esc(x){return String(x).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function side(nm,ab,xe,fo,stk){
  var h='<div class="mc"><h4>'+esc(nm)+'</h4>';
  h+=(ab.o.length||ab.d.length)?'':'<div class="ab">Aucun absent</div>';
  ab.o.forEach(function(p){h+='<div class="ab">🩹 '+esc(p)+'</div>'});
  ab.d.forEach(function(p){h+='<div class="ab d">❔ '+esc(p)+'</div>'});
  if(xe) h+='<div class="ab el">'+xe+' Elo</div>';
  h+='<div class="stk">'+esc(stk)+'</div>';
  fo.forEach(function(f){h+='<div class="fr"><span>'+f[0]+' · '+esc(f[1])+' ('+f[2]+')</span><span>'+f[5]+' '+f[3]+' <b class="'+f[4]+'">'+f[4]+'</b></span></div>'});
  return h+'</div>';
}
function openM(g){
  var m=MD[g];if(!m)return;
  var lg=function(id){return '<img src="https://a.espncdn.com/i/teamlogos/soccer/500/'+id+'.png" onerror="this.style.visibility=\'hidden\'">'};
  document.getElementById('mpan').innerHTML='<button class="mx" id="mx">✕</button>'
   +'<div class="mh"><div class="t">'+lg(m.hid)+esc(m.h)+'<div style="font-size:15px;color:var(--mut)">Elo '+m.eh+' · domicile +'+m.hfa+'</div></div><div class="t" style="font-size:26px">'+m.sc+'</div><div class="t">'+lg(m.aid)+esc(m.a)+'<div style="font-size:15px;color:var(--mut)">Elo '+m.ea+'</div></div></div>'
   +'<div class="mp"><span>1 · '+m.p[0]+' %</span><span>N · '+m.p[1]+' %</span><span>2 · '+m.p[2]+' %</span></div>'
   +'<div class="mg">'+side(m.h,m.ah,m.xh,m.fh,m.sh)+side(m.a,m.aa,m.xa,m.fa,m.sa)+'</div>';
  document.getElementById('mov').classList.add('open');
}
document.addEventListener('click',function(e){
  if(e.target.id==='mx'||e.target.id==='mov'){document.getElementById('mov').classList.remove('open');return;}
  if(e.target.closest('input,button,label,.mpan'))return;
  var tr=e.target.closest('[data-g]');if(tr)openM(tr.dataset.g);
});

var OKEY='CLE_ODDS_API',NM={'Sporting CP':'Sporting Lisbon','Bodo/Glimt':'Bodø/Glimt','Feyenoord Rotterdam':'Feyenoord','Internazionale':'Inter Milan','LASK Linz':'LASK','Slovan Bratislava':'ŠK Slovan Bratislava','Paris Saint-Germain':'Paris Saint Germain','Slavia Prague':'Slavia Praha','Lens':'RC Lens','FC Porto':'Porto','Borussia Dortmund':'Borussia Dortmund'};
function nm(x){return NM[x]||x}
async function odds(){
  if(!OKEY)return;
  try{var r=await fetch('https://api.the-odds-api.com/v4/sports/soccer_uefa_champs_league/odds/?regions=fr&markets=h2h&oddsFormat=decimal&bookmakers=winamax_fr&apiKey='+OKEY,{cache:'no-store'});if(!r.ok)return;var j=await r.json();
    var by={};j.forEach(function(e){var b=(e.bookmakers||[]).find(function(x){return x.key==='winamax_fr'});if(!b)return;var m=b.markets.find(function(x){return x.key==='h2h'});if(!m)return;var o={};m.outcomes.forEach(function(x){o[x.name]=x.price});by[e.home_team+'|'+e.away_team]=[o[e.home_team],o.Draw,o[e.away_team]];});
    var FZ0={};try{FZ0=JSON.parse(localStorage.getItem('ldc_j4_frz')||'{}')||{}}catch(x){}
    document.querySelectorAll('[data-en]').forEach(function(c){if(c.dataset.g&&FZ0[c.dataset.g])return;var p=c.dataset.en.split('|'),k=nm(p[0])+'|'+nm(p[1]),o=by[k];if(!o||!o[0])return;
      var f=+c.dataset.fav,ow=f===0?o[0]:o[2],odc=1.035/(1/ow+1/o[1]);c.dataset.ow=ow.toFixed(3);c.dataset.odc=odc.toFixed(3);
      c.querySelectorAll('.w[data-k]').forEach(function(w){var v=w.dataset.k==='Sec'?ow:odc,g=v>=1/(+w.dataset.p);w.className='w '+(g?'good':'bad');w.textContent=(w.dataset.k==='Sec'?'':'≈')+v.toFixed(2).replace('.',',')+' '+(g?'✓':'✗');});
      var oe=c.querySelector('.o');if(oe)oe.textContent=o.map(function(v){return v.toFixed(2).replace('.',',')}).join(' · ');});
    paint();
  }catch(e){}
}
odds();setInterval(odds,600000);
try{L=Object.assign({},JSON.parse(localStorage.getItem('ldc_j4_live')||'{}')||{},FIN);window.LIVE=L}catch(e){}
window.__paint=paint;
paint();tick();setInterval(tick,15000);document.addEventListener('visibilitychange',function(){if(!document.hidden)tick()});
})();
</script>'''
from datetime import datetime
from zoneinfo import ZoneInfo
_n=datetime.now(ZoneInfo('Europe/Paris'))
MAJ=f"{JOURS[_n.weekday()].lower()} {_n.day} {MOIS[_n.month]} à {_n:%H:%M}"
CURH=''.join(f'<div class="jc" data-j="{j}" hidden>'+''.join(JC[j])+'</div>' for j in JC)
page=f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ligue des champions</title><style>
:root{{color-scheme:dark;--bg:#07120d;--sur:#10231a;--sur2:#0c1c14;--line:#244634;--ink:#fff;--mut:#c6d6cb;--gold:#ffc83d;--green:#3ddc84;--red:#ff6b61}}
*{{box-sizing:border-box}}
body{{margin:0;color:var(--ink);font:18px/1.35 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:radial-gradient(1200px 600px at 50% -200px,#1a3d8a 0%,rgba(26,61,138,.25) 35%,transparent 70%),var(--bg);min-height:100vh}}
.wrap{{max-width:1180px;margin:0 auto;padding:22px 14px 40px}}
h1{{margin:0;font-size:32px;font-weight:900;letter-spacing:.01em;background:linear-gradient(90deg,#fff,#ffc83d);-webkit-background-clip:text;background-clip:text;color:transparent}}
#lmsg{{margin:6px 0 4px!important}}.upd{{margin:6px 0 0;font-size:17px;font-weight:800;color:#ffc83d}}
h2.day{{margin:26px 0 12px;font-size:22px;color:var(--gold);display:flex;align-items:center;gap:12px}}h2.day:after{{content:"";flex:1;height:2px;background:linear-gradient(90deg,var(--gold),transparent)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}}
.card{{background:linear-gradient(180deg,var(--sur),var(--sur2));border:1px solid var(--line);border-radius:18px;padding:14px 16px;box-shadow:0 8px 24px rgba(0,0,0,.35);cursor:pointer;transition:transform .12s,border-color .12s}}
.card:hover{{transform:translateY(-2px);border-color:#3c6b51}}.card.betted{{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold),0 8px 24px rgba(0,0,0,.35)}}
.ctop{{display:flex;justify-content:space-between;align-items:center;min-height:30px}}.t{{font-weight:800;color:var(--mut);background:rgba(255,255,255,.06);padding:3px 10px;border-radius:999px;font-size:16px}}
.teams{{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin:8px 0 10px}}
.tm{{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center}}.tm img{{width:52px;height:52px;object-fit:contain;filter:drop-shadow(0 2px 4px rgba(0,0,0,.5))}}.tm b{{font-size:18px;line-height:1.2}}
.mid{{text-align:center;min-width:80px}}.pv{{font-size:28px;font-weight:900;letter-spacing:.04em}}
.live{{display:block;font-size:30px;font-weight:900}}.live:not(:empty){{background:linear-gradient(180deg,#2a0f0f,#160808);border:2px solid #ff6b61;border-radius:14px;padding:6px 14px 4px;box-shadow:0 0 14px rgba(255,107,97,.35);margin-bottom:4px}}.live:not(:empty):has(.ft){{border-color:#6b7b72;background:#0c1c14;box-shadow:none}}.live .st{{display:block;font-size:14px;font-weight:800;color:var(--red)}}.live .st.ft{{color:var(--mut)}}
.live:not(:empty)+.pv{{font-size:15px;color:var(--mut);font-weight:700}}
.bar{{display:flex;height:10px;border-radius:999px;overflow:hidden;background:#000;gap:2px}}.bar i{{display:block;height:100%}}
.bh,.ba{{background:#3a5a49}}.bd{{background:#6b7b72}}.bar i.f{{background:linear-gradient(90deg,#ffc83d,#ffdf7f)}}
.pcts{{display:flex;justify-content:space-between;margin:6px 2px 10px;font-size:17px;color:var(--mut);font-variant-numeric:tabular-nums}}.pcts .fav{{color:var(--gold);font-weight:900;font-size:19px}}
.cbot{{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-start;gap:10px;padding-top:10px;border-top:1px solid var(--line)}}.wx{{text-align:right;margin-left:auto}}
.pill{{display:inline-block;padding:7px 14px;border-radius:999px;font-weight:900;font-size:17px;white-space:nowrap}}
.pill.win{{background:var(--green);color:#062312}}.pill.dc{{background:#ffc83d;color:#241a02}}.pill.none{{background:#55606b;color:#fff}}
.sub{{font-size:15px;color:var(--mut);margin-top:6px;white-space:nowrap}}
.w{{display:inline-block;font-weight:900;padding:5px 11px;border-radius:999px;font-size:18px}}.w.good{{background:#0b3d1f;color:#7dffb0}}.w.bad{{background:#4a1010;color:#ffb3ad}}
.wl{{display:flex;justify-content:flex-end;align-items:center;gap:8px;margin-bottom:5px}}.wn{{font-size:15px;color:var(--mut);font-weight:700;white-space:nowrap}}.w{{white-space:nowrap}}
#combo{{margin-top:22px;background:linear-gradient(180deg,var(--sur),var(--sur2));border:1px solid var(--line);border-radius:18px;padding:16px}}#combo:empty{{display:none}}
.cod{{width:78px;font:inherit;font-size:18px;font-weight:800;text-align:right;padding:5px 8px;border-radius:8px;border:2px solid var(--line);background:#0c1c14;color:var(--ink)}}.cod:focus{{border-color:var(--gold);outline:0}}
.nav{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}}.nav button{{font:inherit;font-size:18px;font-weight:800;padding:9px 16px;border-radius:999px;border:2px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}}.nav button.on{{background:#ffc83d;border-color:#ffc83d;color:#111}}.nav .ds{{display:flex;gap:8px;flex-wrap:wrap}}[hidden]{{display:none!important}}.orow{{display:flex;align-items:center;gap:12px;padding:12px 14px;border:2px solid var(--line);border-radius:14px;margin:0 0 8px;font-size:19px}}.orow b:first-child{{flex:1;text-align:right}}.orow b:last-child{{flex:1}}.osc{{font-size:24px;font-weight:900;background:#ffc83d;color:#111;border-radius:10px;padding:2px 12px}}
.seg{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}}.seg button{{font:inherit;font-size:16px;font-weight:800;padding:7px 14px;border-radius:999px;border:2px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}}.seg button.on{{background:#ffc83d;border-color:#ffc83d;color:#241a02}}
#combo h2{{margin:0 0 10px;color:var(--gold);font-size:24px}}#combo table{{width:100%;border-collapse:collapse;font-size:17px}}#combo td,#combo th{{padding:8px 4px;border-bottom:1px solid var(--line);text-align:left}}#combo th{{color:var(--mut);font-size:14px;text-transform:uppercase}}#combo .n{{text-align:right}}#combo tr.tot td{{border-top:2px solid var(--gold);font-weight:900}}
.stk{{display:flex;align-items:center;gap:10px;margin:12px 0 6px;font-size:19px;font-weight:800}}.stk .bst{{width:90px!important}}.stk{{flex-wrap:wrap}}.stk input{{width:120px;font:inherit;font-size:21px;padding:8px 12px;border-radius:10px;border:2px solid var(--gold);background:#0c1c14;color:var(--ink)}}
.gain{{display:flex;gap:10px 22px;flex-wrap:wrap;font-size:19px}}.gain b{{font-size:24px}}.gain .yes{{color:#7dffb0}}.gain .no{{color:#ffb3ad}}
.o{{display:block;font-size:15px;color:var(--mut);margin-top:6px;white-space:nowrap}}
.betz{{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:10px}}
.bet{{display:flex;align-items:center;gap:8px;font-size:17px;font-weight:800;cursor:pointer}}.bet input{{width:24px;height:24px;accent-color:#ffc83d}}
.ch{{display:none;gap:8px}}.card.betted .ch{{display:flex}}.ch:empty{{display:none!important}}
.ch button{{font:inherit;font-size:15px;font-weight:800;padding:6px 12px;border-radius:999px;border:2px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}}.ch button.on{{background:#ffc83d;border-color:#ffc83d;color:#241a02}}
.res{{font-weight:900;font-size:16px;padding:4px 12px;border-radius:999px}}.res.ok{{background:#0b3d1f;color:#7dffb0}}.res.ko{{background:#4a1010;color:#ffb3ad}}.res:empty{{display:none}}.res.lok{{background:#2e2a0b;color:#ffc83d}}.res.lko{{background:#4a1010;color:#ffb3ad}}
#recap{{margin-top:22px;background:var(--sur);border:1px solid var(--line);border-radius:14px;padding:16px}}#recap:empty{{display:none}}
#recap h2{{margin:0 0 12px;color:var(--gold);font-size:24px}}.tiles{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}}
.tile{{background:#0f2218;border-radius:12px;padding:12px;text-align:center}}.tile b{{display:block;font-size:34px}}.tile span{{font-size:16px;color:var(--mut)}}
.tile.g b{{color:#7dffb0}}.tile.r b{{color:#ffb3ad}}.tile.y b{{color:var(--gold)}}
.rl{{display:flex;justify-content:space-between;gap:10px;padding:9px 4px;border-top:1px solid var(--line);font-size:18px}}.rl b{{font-weight:800}}.rl .s{{font-weight:900;white-space:nowrap}}.s.ok{{color:#7dffb0}}.s.ko{{color:#ffb3ad}}.s.wt{{color:var(--mut)}}.s.lv{{color:var(--gold)}}
.mov{{position:fixed;inset:0;background:rgba(0,0,0,.65);display:none;align-items:flex-start;justify-content:center;z-index:50;overflow:auto;padding:20px 10px}}.mov.open{{display:flex}}
.mpan{{background:#13281c;border:1px solid var(--line);border-radius:16px;max-width:760px;width:100%;padding:18px;position:relative}}
.mx{{position:absolute;right:12px;top:10px;font-size:26px;background:none;border:0;color:var(--ink);cursor:pointer}}
.mh{{display:flex;align-items:center;justify-content:space-around;gap:10px;margin:6px 0 12px}}.mh .t{{text-align:center;font-weight:900;font-size:21px}}.mh img{{width:56px;height:56px;object-fit:contain;display:block;margin:0 auto 6px}}
.mp{{text-align:center;font-size:20px;font-weight:800;margin-bottom:10px}}.mp span{{display:inline-block;margin:0 8px}}
.mg{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.mc{{background:#0f2218;border-radius:12px;padding:12px}}.mc h4{{margin:0 0 8px;color:var(--gold);font-size:18px}}
.mc .ab{{font-size:17px;margin:3px 0}}.mc .ab.d{{color:var(--mut)}}.mc .el{{font-weight:900;color:#ffb3ad}}
.fr{{display:flex;justify-content:space-between;gap:6px;font-size:16px;padding:4px 0;border-top:1px solid var(--line)}}.fr b{{display:inline-block;width:26px;text-align:center;border-radius:6px;color:#062312}}
.fr b.V{{background:#3ddc84}}.fr b.N{{background:#c9d8cd}}.fr b.D{{background:#ff6b61}}.stk{{font-weight:800;margin:4px 0 8px;font-size:17px}}
@media(max-width:600px){{.mg{{grid-template-columns:1fr}}}}

.o{{display:block;font-size:15px;color:var(--mut);margin-top:5px;white-space:nowrap}}
</style></head><body><div class="wrap"><h1 id="ttl">Ligue des champions</h1><p class="upd">Mis à jour le {MAJ}</p>
{NAV}<p id="lmsg" style="margin:0 0 10px;color:var(--mut);font-size:16px"></p><div id="livebox" hidden></div><div id="nolive" hidden style="font-size:26px;font-weight:800;padding:30px 0;text-align:center">Aucun match en cours</div><div id="cur">{CURH}</div><div id="old" hidden>{OLDH}</div></div>
<div id="combo"></div><div id="recap"></div></div><div class="mov" id="mov"><div class="mpan" id="mpan"></div></div>'''+'<script>var MD='+json.dumps(MD,ensure_ascii=False)+';var FIN='+json.dumps(FIN)+';var DAYS='+json.dumps(DAYS,ensure_ascii=False)+';var JL='+json.dumps(JL)+';</script>'+JS+NAVJS+'''</body></html>'''
open('/home/claude/ucl/pronos-ldc-j4.html','w').write(page)
# version appli (sans la clé de cotes) publiée sur GitHub : l'appli la charge à chaque ouverture
import subprocess, os
app=page.replace("var OKEY='CLE_ODDS_API'","var OKEY=''")
REPO='/home/claude/predicteur-ligue1'
if os.path.isdir(REPO) and os.environ.get('NO_PUSH')!='1':
    open(REPO+'/ldc.html','w').write(app)
    def g(*a): return subprocess.run(['git','-C',REPO]+list(a),capture_output=True,text=True)
    g('pull','-q','--rebase'); g('add','ldc.html')
    if g('diff','--cached','--quiet').returncode:
        g('commit','-q','-m','LdC : mise à jour des pronos ('+MAJ+')\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_016pn6rCzxVWaM9ZHMe9PhSv')
        r=g('push','-q'); print('publié' if r.returncode==0 else 'push KO: '+r.stderr[-200:])
