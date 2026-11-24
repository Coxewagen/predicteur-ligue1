"""Journal des pronos LdC.
python3 journal.py add [J]   -> enregistre les pronos actuels (preds.json, ou preds_jJ.json pour J5 à J8) avec et sans absences
python3 journal.py res FILE  -> ajoute les résultats depuis un scoreboard ESPN (fichier brut Firecrawl)
python3 journal.py bilan     -> bilan : réussite par tranche, effet des absences
"""
import json, math, sys, os
sys.path.insert(0,'/home/claude/work')
from model import probs
J='journal.json'
jr=json.load(open(J)) if os.path.exists(J) else {}
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]
def model(h,a,R,HT,ABS,use_abs=True):
    x=(0.84*(R[h]+(ABS.get(h,0) if use_abs else 0)-R[a]-(ABS.get(a,0) if use_abs else 0))+HT.get(h,56))/100
    lh,la=math.exp(P[0]+.12+P[1]*x), math.exp(P[2]+.12-P[3]*x); return [round(v,4) for v in probs(lh,la,0.05)[:3]]
cmd=sys.argv[1]
if cmd=='add':
    R=json.load(open('ratings2.json'))['R']; HT=json.load(open('hfa_team.json')); ABS=json.load(open('abs.json')); OD=json.load(open('odds.json')) if len(sys.argv)<3 else {}
    for x in json.load(open('preds.json' if len(sys.argv)<3 else f'preds_j{sys.argv[2]}.json')):
        k=x['date'][:10]+' '+x['h']+' - '+x['a']; e=jr.get(k,{})
        e.update(date=x['date'],h=x['h'],a=x['a'],p=x['mod'],p_sans_abs=model(x['h'],x['a'],R,HT,ABS,False),abs_h=ABS.get(x['h'],0),abs_a=ABS.get(x['a'],0),
                 prono=x['label'],prob=round(x['prob'],4),type=x['reco'],cotes=OD.get(x['h']),enregistre=__import__('datetime').datetime.now().isoformat(timespec='minutes'))
        jr[k]=e
elif cmd=='res':
    j=json.loads(json.loads(open(sys.argv[2]).read())['rawHtml'])
    for ev in j['events']:
        if ev['status']['type']['state']!='post': continue
        c=ev['competitions'][0]; h=[t for t in c['competitors'] if t['homeAway']=='home'][0]; a=[t for t in c['competitors'] if t['homeAway']=='away'][0]
        for k,e in jr.items():
            if e['h']==h['team']['displayName'] and e['a']==a['team']['displayName'] and k[:10]==ev['date'][:10]:
                e['score']=[int(h['score']),int(a['score'])]
elif cmd=='bilan':
    done=[e for e in jr.values() if 'score' in e]
    def ok(e):
        hs,as_=e['score']; o=0 if hs>as_ else (1 if hs==as_ else 2); fav=0 if e['p'][0]>=e['p'][2] else 2
        return o==fav if e['type']=='win' else o!=(2 if fav==0 else 0)
    def ll(e,key):
        hs,as_=e['score']; o=0 if hs>as_ else (1 if hs==as_ else 2); return -math.log(e[key][o])
    print(f"{len(done)} matchs joués · pronos réussis {sum(ok(e) for e in done)}/{len(done)}")
    for lo,hi in ((.5,.65),(.65,.75),(.75,1)):
        s=[e for e in done if lo<=e['prob']<hi]
        if s: print(f"  annoncé {lo:.0%}-{hi:.0%} : {sum(ok(e) for e in s)}/{len(s)} (annoncé en moyenne {sum(e['prob'] for e in s)/len(s):.0%})")
    if done:
        print(f"  erreur avec absences {sum(ll(e,'p') for e in done)/len(done):.4f} · sans absences {sum(ll(e,'p_sans_abs') for e in done)/len(done):.4f}")
json.dump(jr,open(J,'w'),ensure_ascii=False,indent=1)
