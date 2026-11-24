import csv, math, json, collections
from scipy.optimize import brentq
rows=[r for r in csv.DictReader(open('data/cf/data/Matches.csv')) if r['MatchDate']>='2023-07-01' and r['HomeElo'] and r['AwayElo'] and r['FTResult']]
E=lambda d:1/(1+10**(-d/400))
S={'H':1,'D':.5,'A':0}
byL=collections.defaultdict(list)
for r in rows: byL[r['Division']].append(r)
LH={}
for L,rs in byL.items():
    f=lambda H: sum(E(float(r['HomeElo'])-float(r['AwayElo'])+H)-S[r['FTResult']] for r in rs)
    LH[L]=brentq(f,-300,400)
meanH=sum(LH.values())/len(LH)
team=collections.defaultdict(lambda:{'h':[],'a':[]})
for r in rows:
    d=float(r['HomeElo'])-float(r['AwayElo']); H=LH[r['Division']]; s=S[r['FTResult']]
    team[r['HomeTeam']]['h'].append((d+H,s)); team[r['AwayTeam']]['a'].append((-(d+H),1-s))
def delta(g):
    if not g: return 0
    f=lambda x: sum(E(d+x)-s for d,s in g)
    return brentq(f,-600,600)
out={}
for t,v in team.items():
    n=min(len(v['h']),len(v['a']))
    if n<15: continue
    raw=delta(v['h'])-delta(v['a'])
    k=n/(n+60)   # rétrécissement
    out[t]=dict(n=n,raw=round(raw),spec=round(k*raw))
json.dump({'LH':LH,'meanH':meanH,'team':out},open('hfa.json','w'),indent=0)
print('HFA moyen',round(meanH), {k:round(v) for k,v in sorted(LH.items())})
