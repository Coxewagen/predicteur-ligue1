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
G2=json.load(open('allgames2.json')); ABL=json.load(open('absl.json')); AE=json.load(open('abs.json')); HT=json.load(open('hfa_team.json'))
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
for x in sorted(P,key=lambda x:(x['date'][:10],ORD.index(x['h']) if x['h'] in ORD else 99)):
    dt=datetime.strptime(x['date'][:16],"%Y-%m-%dT%H:%M")+timedelta(hours=1)
    day=f"{JOURS[dt.weekday()]} {dt.day} {MOIS[dt.month]}"
    if day!=cur:
        cur=day; rows.append(f'<tr class="day"><td colspan="8">{day}</td></tr>')
    fav=0 if x['ph']>=x['pa'] else 2
    cls=lambda k: ' class="fav"' if k==fav else ''
    lab=x['label'].replace(x['h'],FR.get(x['h'],x['h'])).replace(x['a'],FR.get(x['a'],x['a']))
    if x['reco']=='none':
        t=x['h'] if x['ph']>=x['pa'] else x['a']; lab=FR.get(t,t)+' ou nul'; x['reco']='dc'
    o=x['odds']; contra = o and ((0 if o[0]<=o[2] else 2)!=(0 if x['mod'][0]>=x['mod'][2] else 2))
    pill=f'<span class="pill {x["reco"]}">{html.escape(lab)}</span>'
    if x['wo']:
        good=x['wo']>=x['mini']
        w=f'<span class="w {"good" if good else "bad"}">{"≈" if x["reco"]!="win" else ""}{f2(x["wo"])} {"✓" if good else "✗"}</span>'
    else: w='—'
    o=x['odds']
    od=f'<span class="o">{f2(o[0])} · {f2(o[1])} · {f2(o[2])}</span>' if o else ''
    gid=f"{x['hid']}-{x['aid']}"
    fh,sh=form(x['h'],x['date']); fa,sa=form(x['a'],x['date'])
    MD[gid]=dict(h=FR.get(x['h'],x['h']),a=FR.get(x['a'],x['a']),hid=x['hid'],aid=x['aid'],p=[round(v*100) for v in x['mod']],sc=x['score'],eh=x['eh'],ea=x['ea'],hfa=HT.get(x['h'],56),
      ah=ABL.get(x['h'],{'o':[],'d':[]}),aa=ABL.get(x['a'],{'o':[],'d':[]}),xh=AE.get(x['h'],0),xa=AE.get(x['a'],0),fh=fh,fa=fa,sh=sh,sa=sa,lab=x['label'],pr=round(x['prob']*100))
    rows.append(f'''<tr data-g="{gid}" data-h="{x['hid']}" data-a="{x['aid']}" data-fav="{fav}" data-t="{x['reco']}"><td class="t">{dt:%H:%M}</td>
<td class="m"><div class="tm">{logo(x["hid"],x["h"])}<b>{n(x["h"])}</b></div><div class="tm">{logo(x["aid"],x["a"])}<b>{n(x["a"])}</b></div></td>
<td{cls(0)}>{pc(x["ph"])}</td><td>{pc(x["pd"])}</td><td{cls(2)}>{pc(x["pa"])}</td>
<td class="sc"><span class="live"></span><span class="pv">{x["score"]}</span></td><td>{pill}<div class="sub">{pc(x["prob"])} · mini {f2(x["mini"])}</div><label class="bet"><input type="checkbox"><span>J’ai parié</span></label><div class="ch">{'<button type="button" data-c="p">Ou nul</button><button type="button" data-c="w">Victoire sèche</button>' if x['reco']=='dc' else ''}</div><span class="res"></span></td><td class="wx">{w}{od}</td></tr>''')
JS=r'''<script>
(function(){
var K='ldc_j4_bets',B={};try{B=JSON.parse(localStorage.getItem(K)||'{}')||{}}catch(e){}
var L={};
function save(){try{localStorage.setItem(K,JSON.stringify(B))}catch(e){}}
function paint(){
  var n=0,w=0,wait=0,items=[];
  document.querySelectorAll('tr[data-g]').forEach(function(tr){
    var g=tr.dataset.g,cb=tr.querySelector('.bet input'),on=!!B[g];cb.checked=on;tr.classList.toggle('betted',on);var typ=(B[g]==='w')?'win':tr.dataset.t;tr.querySelectorAll('.ch button').forEach(function(x){x.classList.toggle('on',(B[g]==='w')===(x.dataset.c==='w'))});
    var l=L[g],lv=tr.querySelector('.live'),rs=tr.querySelector('.res');
    lv.innerHTML=l&&l.state!=='pre'?l.h+'-'+l.a+'<span class="st'+(l.state==='post'?' ft':'')+'">'+l.txt+'</span>':'';
    var res=null;
    if(l&&l.state==='post'){var o=l.h>l.a?0:(l.h===l.a?1:2),f=+tr.dataset.fav;res=typ==='win'?o===f:o!==(f===0?2:0);}
    rs.className='res'+(res===null?'':(res?' ok':' ko'));rs.textContent=on&&res!==null?(res?'✓ Gagné':'✗ Perdu'):'';
    if(on){n++;if(res===null)wait++;else if(res)w++;
      var nm=tr.querySelectorAll('.tm b'),st,cl;
      if(res===true){st='✓ Gagné';cl='ok';}else if(res===false){st='✗ Perdu';cl='ko';}
      else if(l&&l.state==='in'){var o2=l.h>l.a?0:(l.h===l.a?1:2),f2=+tr.dataset.fav,cur=typ==='win'?o2===f2:o2!==(f2===0?2:0);st=l.h+'-'+l.a+' · '+(cur?'en bonne voie':'mal parti');cl='lv';}
      else{st='À venir · '+tr.querySelector('.t').textContent;cl='wt';}
      items.push('<div class="rl"><span><b>'+nm[0].textContent+' – '+nm[1].textContent+'</b> · '+(B[g]==='w'?'Victoire '+tr.querySelector('.pill').textContent.replace(' ou nul',''):tr.querySelector('.pill').textContent)+'</span><span class="s '+cl+'">'+st+'</span></div>');}
  });
  var lost=n-w-wait;
  document.getElementById('recap').innerHTML=n?('<h2>Récap de mes paris</h2><div class="tiles"><div class="tile"><b>'+n+'</b><span>Pariés</span></div><div class="tile g"><b>'+w+'</b><span>Gagnés</span></div><div class="tile r"><b>'+lost+'</b><span>Perdus</span></div><div class="tile y"><b>'+wait+'</b><span>À venir</span></div></div>'+items.join('')):'';
}
document.addEventListener('click',function(e){var bt=e.target.closest('.ch button');if(!bt)return;var tr=bt.closest('tr[data-g]');B[tr.dataset.g]=bt.dataset.c;save();paint();});
document.addEventListener('change',function(e){var tr=e.target.closest('tr[data-g]');if(!tr)return;if(e.target.checked)B[tr.dataset.g]='p';else delete B[tr.dataset.g];save();paint();});
function lab(st){var n=(st.type&&st.type.name)||'';if(n==='STATUS_HALFTIME')return 'Mi-temps';if(st.type&&st.type.state==='post')return 'Terminé';return st.displayClock||'';}
async function tick(){
  var out={},ok=false;
  for(const d of ['20261103','20261104']){
    try{var r=await fetch('https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard?dates='+d,{cache:'no-store'});if(!r.ok)continue;var j=await r.json();ok=true;
      (j.events||[]).forEach(function(e){var c=e.competitions[0],h=c.competitors.find(x=>x.homeAway==='home'),a=c.competitors.find(x=>x.homeAway==='away');
        out[h.team.id+'-'+a.team.id]={h:+h.score||0,a:+a.score||0,state:e.status.type.state,txt:lab(e.status)};});
    }catch(e){}
  }
  if(ok){L=out;try{localStorage.setItem('ldc_j4_live',JSON.stringify(L))}catch(e){}}
  var t=new Date().toLocaleTimeString('fr-FR',{timeZone:'Europe/Paris',hour:'2-digit',minute:'2-digit'});
  document.getElementById('lmsg').textContent=ok?'Scores ESPN · '+t:'Scores indisponibles';
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
  var tr=e.target.closest('tr[data-g]');if(tr)openM(tr.dataset.g);
});
try{L=JSON.parse(localStorage.getItem('ldc_j4_live')||'{}')||{}}catch(e){}
paint();tick();setInterval(tick,30000);
})();
</script>'''
page=f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ligue des champions · J4</title><style>
:root{{color-scheme:dark;--bg:#0b1a12;--sur:#13281c;--line:#2a4a36;--ink:#fff;--mut:#c9d8cd;--gold:#ffc83d;--green:#3ddc84;--red:#ff6b61;--navy:#1f3b8a}}
body{{margin:0;background:var(--bg);color:var(--ink);font:18px/1.35 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1150px;margin:0 auto;padding:18px 12px}}
h1{{margin:0 0 14px;font-size:30px;color:var(--gold)}}
.tbl{{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--sur)}}
table{{border-collapse:collapse;width:100%;min-width:900px}}
th{{text-align:left;font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);padding:12px 10px;border-bottom:2px solid var(--navy)}}
td{{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:middle;font-variant-numeric:tabular-nums;font-size:19px}}
tr.day td{{background:#0f2218;color:var(--gold);font-weight:800;font-size:20px;padding:10px}}
.t{{font-weight:700;color:var(--mut)}}
.tm{{display:flex;align-items:center;gap:10px;margin:3px 0}}.tm img{{width:30px;height:30px;object-fit:contain}}.tm b{{font-size:19px}}
td.fav{{color:var(--gold);font-weight:900;font-size:21px}}
.sc{{font-weight:900;font-size:22px;white-space:nowrap}}
.pill{{display:inline-block;padding:6px 12px;border-radius:999px;font-weight:800;font-size:17px;white-space:nowrap}}
.pill.win{{background:var(--green);color:#062312}}.pill.dc{{background:#ffc83d;color:#241a02}}.pill.none{{background:#55606b;color:#fff}}
.sub{{font-size:15px;color:var(--mut);margin-top:5px;white-space:nowrap}}
.w{{display:inline-block;font-weight:900;padding:4px 10px;border-radius:999px;font-size:18px}}.w.good{{background:#0b3d1f;color:#7dffb0}}.w.bad{{background:#4a1010;color:#ffb3ad}}
.warn{{color:var(--gold);font-size:24px;font-weight:900;vertical-align:middle}}
.bet{{display:flex;align-items:center;gap:8px;margin-top:8px;font-size:17px;font-weight:700;cursor:pointer}}.ch{{display:none;gap:8px;margin-top:8px}}tr.betted .ch{{display:flex}}.ch:empty{{display:none!important}}
.ch button{{font:inherit;font-size:16px;font-weight:800;padding:6px 12px;border-radius:999px;border:2px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}}.ch button.on{{background:#ffc83d;border-color:#ffc83d;color:#241a02}}
.bet input{{width:24px;height:24px;accent-color:#ffc83d}}
tr.betted td{{background:rgba(255,200,61,.07)}}
.live{{display:block;font-size:24px;font-weight:900}}.live .st{{display:block;font-size:14px;font-weight:700;color:#ff6b61}}.live .st.ft{{color:var(--mut)}}
.live:not(:empty)+.pv{{font-size:15px;color:var(--mut);font-weight:700}}
.res{{display:inline-block;margin-top:6px;font-weight:900;font-size:17px;padding:3px 10px;border-radius:999px}}.res.ok{{background:#0b3d1f;color:#7dffb0}}.res.ko{{background:#4a1010;color:#ffb3ad}}.res:empty{{display:none}}
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
tr[data-g] td.m{{cursor:pointer}}
.o{{display:block;font-size:15px;color:var(--mut);margin-top:5px;white-space:nowrap}}
</style></head><body><div class="wrap"><h1>Ligue des champions · Journée 4</h1>
<p id="lmsg" style="margin:0 0 10px;color:var(--mut);font-size:16px"></p><div class="tbl"><table><thead><tr><th>Heure</th><th>Match</th><th>1</th><th>N</th><th>2</th><th>Score</th><th>Prono</th><th>Winamax</th></tr></thead><tbody>
{"".join(rows)}
</tbody></table></div><div id="recap"></div></div><div class="mov" id="mov"><div class="mpan" id="mpan"></div></div>'''+'<script>var MD='+json.dumps(MD,ensure_ascii=False)+';</script>'+JS+'''</body></html>'''
open('/home/claude/ucl/pronos-ldc-j4.html','w').write(page)
