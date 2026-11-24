import csv, json, math, sys
sys.path.insert(0,'/home/claude/work')
import numpy as np
from model import gmult, lambdas, probs
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]; RHO=-0.043258059130917466
H=50; K=20
MAP={"Galatasaray":"Galatasaray","VfB Stuttgart":"Stuttgart","Sporting CP":"Sp Lisbon","Atlético Madrid":"Ath Madrid","Bayern Munich":"Bayern Munich","Barcelona":"Barcelona","Aston Villa":"Aston Villa","Bodo/Glimt":"Bodoe Glimt","Lille":"Lille","Feyenoord Rotterdam":"Feyenoord","Internazionale":"Inter","LASK Linz":"LASK","Manchester United":"Man United","AS Roma":"Roma","Villarreal":"Villarreal","Paris Saint-Germain":"Paris SG","AEK Athens":"AEK","Real Madrid":"Real Madrid","Fenerbahce":"Fenerbahce","Liverpool":"Liverpool","Borussia Dortmund":"Dortmund","Real Betis":"Betis","FC Porto":"Porto","Napoli":"Napoli","Lens":"Lens","Como":"Como","PSV Eindhoven":"PSV Eindhoven","Club Brugge":"Club Brugge","RB Leipzig":"RB Leipzig","Manchester City":"Man City","Arsenal":"Arsenal","Viking FK":"Viking"}
EST={"Shakhtar Donetsk":1650,"Slavia Prague":1690,"Slovan Bratislava":1520,"Sabah FK":1450}
snap={}
for r in csv.DictReader(open('/home/claude/ucl/data/cf/data/EloRatings.csv')):
    if r['date']=='2026-09-01': snap[r['club']]=float(r['elo'])
R={}
for e,c in MAP.items(): R[e]=snap[c]
R.update(EST)
start=dict(R)
res=[l.strip().split(';') for l in open('ucl_res.csv') if l.strip()]
ok=n=0; ll=0; goals=0
for d_,h,a,hs,as_,neu in res:
    hs,as_=int(hs),int(as_); d=R[h]-R[a]+(0 if neu=='1' else H)
    ph,pd,pa,_=probs(*lambdas(d,P),RHO)
    o=0 if hs>as_ else (1 if hs==as_ else 2); fav=int(np.argmax([ph,pd,pa]))
    n+=1; ok+= (fav==o); ll+=-math.log([ph,pd,pa][o]); goals+=hs+as_
    E=1/(1+10**(-d/400)); S=1 if hs>as_ else (.5 if hs==as_ else 0)
    for t,sg in ((h,1),(a,-1)):
        k=40 if t in EST else K
        R[t]+=sg*k*gmult(hs-as_)*(S-E)
print("matchs",n,"favori juste",ok,"logloss",round(ll/n,3),"buts/match",round(goals/n,2))
json.dump({'R':R,'start':start},open('ratings.json','w'),ensure_ascii=False,indent=0)
