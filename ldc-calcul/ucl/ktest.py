import json, csv, math, sys, bisect
from collections import defaultdict
sys.path.insert(0,'/home/claude/work')
from model import probs, gmult
E=lambda d:1/(1+10**(-d/400))
LH=json.load(open('hfa.json'))['LH']
snap={}
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')):
    snap.setdefault(r['date'],{})[r['club']]=float(r['elo'])
dom=[]
for r in csv.DictReader(open('data/cf/data/Matches.csv')):
    if r['FTHome']=='' or r['MatchDate']<'2024-08-01': continue
    dom.append((r['MatchDate'],'D',r['HomeTeam'],r['AwayTeam'],int(float(r['FTHome'])),int(float(r['FTAway'])),LH.get(r['Division'],50)))
R=json.load(open('cl_hist_raw.json')); M=json.load(open('cl_names.json'))
last={r['season']:r for r in R}
cl=[]
for r in R:
    if r['season'] not in ('2024-25','2025-26'): continue
    h,a=M.get(r['h']),M.get(r['a'])
    if h and a: cl.append((r['date'],'C',h,a,r['hg'],r['ag'],0 if r is last[r['season']] else 56))
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]
def run(Kd,Kc,start_key,S=0.84,C=0.12):
    tot=0;n=0
    for season,(d0,d1) in (('2024-25',('2024-09-01','2025-07-01')),('2025-26',('2025-09-01','2026-07-01'))):
        Rt=dict(snap[d0 if d0 in snap else sorted(snap)[0]])
        ev=sorted([g for g in dom+cl if d0<=g[0]<d1])
        for d,k,h,a,hg,ag,H in ev:
            if h not in Rt or a not in Rt: continue
            diff=Rt[h]-Rt[a]
            if k=='C':
                x=(S*diff+H)/100; lh,la=math.exp(P[0]+C+P[1]*x), math.exp(P[2]+C-P[3]*x)
                ph,pd,pa,_=probs(lh,la,-0.0433); o=0 if hg>ag else (1 if hg==ag else 2); tot-=math.log([ph,pd,pa][o]); n+=1
            K=Kd if k=='D' else Kc
            if K:
                e=E(diff+H); s=1 if hg>ag else (.5 if hg==ag else 0); dl=K*gmult(hg-ag)*(s-e); Rt[h]+=dl; Rt[a]-=dl
    return tot/n,n
# référence : notes ClubElo (prolongées) à la date du match
def ref(S=0.84,C=0.12):
    ds=sorted(snap); tot=0;n=0
    for d,k,h,a,hg,ag,H in cl:
        i=bisect.bisect_right(ds,d)-1; sn=snap[ds[i]]
        if h not in sn or a not in sn: continue
        x=(S*(sn[h]-sn[a])+H)/100; lh,la=math.exp(P[0]+C+P[1]*x), math.exp(P[2]+C-P[3]*x)
        ph,pd,pa,_=probs(lh,la,-0.0433); o=0 if hg>ag else (1 if hg==ag else 2); tot-=math.log([ph,pd,pa][o]); n+=1
    return tot/n,n
print('notes ClubElo du jour (référence)',ref())
print('notes figées au 1er sept',run(0,0,None))
for Kd,Kc in ((10,10),(20,20),(30,30),(20,30),(20,40),(10,30),(30,20),(40,40)):
    print(f'K champ.={Kd} K LdC={Kc}',run(Kd,Kc,None))
print('---')
for Kd,Kc in ((15,15),(15,25),(25,20)):
    print(f'K champ.={Kd} K LdC={Kc}',run(Kd,Kc,None))
# rapprochement des notes de départ vers 1600 de x %
orig=run
def run_reg(f,Kd=20,Kc=20):
    global snap
    sv={k:dict(v) for k,v in snap.items()}
    for k in ('2024-09-01','2025-09-01'):
        if k in snap: snap[k]={c:1600+(e-1600)*(1-f) for c,e in snap[k].items()}
    r=run(Kd,Kc,None); snap.clear(); snap.update(sv); return r
for f in (0.05,0.1,0.2):
    print('départ rapproché de',f,run_reg(f))
