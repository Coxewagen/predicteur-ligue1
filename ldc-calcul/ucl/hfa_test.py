import json, csv, math, bisect
from collections import defaultdict
from scipy.optimize import brentq
import sys; sys.path.insert(0,'/home/claude/work')
from model import probs
E=lambda d:1/(1+10**(-d/400)); S={'H':1,'D':.5,'A':0}
rows=[r for r in csv.DictReader(open('data/cf/data/Matches.csv')) if r['HomeElo'] and r['AwayElo'] and r['FTResult']]
def season(d): y=int(d[:4]); return y if int(d[5:7])>=7 else y-1
byL=defaultdict(list)
for r in rows: byL[(r['Division'],season(r['MatchDate']))].append(r)
LH={}
for k,rs in byL.items():
    try: LH[k]=brentq(lambda H: sum(E(float(r['HomeElo'])-float(r['AwayElo'])+H)-S[r['FTResult']] for r in rs),-300,400)
    except: LH[k]=50
team=defaultdict(lambda:defaultdict(lambda:{'h':[],'a':[]}))
for r in rows:
    sn=season(r['MatchDate']); d=float(r['HomeElo'])-float(r['AwayElo'])+LH[(r['Division'],sn)]; s=S[r['FTResult']]
    team[r['HomeTeam']][sn]['h'].append((d,s)); team[r['AwayTeam']][sn]['a'].append((-d,1-s))
def delta(g):
    if len(g)<5: return 0
    try: return brentq(lambda x: sum(E(d+x)-s for d,s in g),-600,600)
    except: return 0
def spec(t,sn,shrink):
    h=[];a=[]
    for y in (sn-3,sn-2,sn-1):
        v=team.get(t,{}).get(y)
        if v: h+=v['h']; a+=v['a']
    n=min(len(h),len(a))
    if n<15: return 0
    return n/(n+shrink)*(delta(h)-delta(a))
R=json.load(open('cl_hist_raw.json')); M=json.load(open('cl_names.json'))
snaps=defaultdict(list)
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')): snaps[r['club']].append((r['date'],float(r['elo'])))
for k in snaps: snaps[k].sort()
def elo(c,d):
    s=snaps.get(c)
    if not s: return None
    ds=[x[0] for x in s]; i=bisect.bisect_right(ds,d)-1
    return s[i][1] if i>=0 and s[i][0]>=str(int(d[:4])-1) else None
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]
last={r['season']:r for r in R}
G=[]
for r in R:
    h,a=M.get(r['h']),M.get(r['a'])
    if not h or not a or r is last[r['season']]: continue
    eh,ea=elo(h,r['date']),elo(a,r['date'])
    if eh is None or ea is None: continue
    G.append((h,int(r['season'][:4]),eh-ea,r['hg'],r['ag']))
def ll(fn):
    t=0
    for h,sn,d,hg,ag in G:
        x=(0.84*d+56+fn(h,sn))/100
        lh,la=math.exp(P[0]+.12+P[1]*x), math.exp(P[2]+.12-P[3]*x)
        ph,pd,pa,_=probs(lh,la,-0.0433); o=0 if hg>ag else (1 if hg==ag else 2)
        t-=math.log([ph,pd,pa][o])
    return t/len(G)
print('matchs',len(G))
print('avantage fixe 56          ',round(ll(lambda h,sn:0),4))
for sh,k in ((60,1.0),(60,0.5),(150,1.0),(60,0.25)):
    print(f'par équipe (rétréci {sh}, x{k})',round(ll(lambda h,sn:k*spec(h,sn,sh)),4))
lg={}
for r in rows: lg[(r['HomeTeam'],season(r['MatchDate']))]=r['Division']
allLH=[v for k,v in LH.items() if k[0] in ('E0','SP1','D1','I1','F1','P1','N1','T1','B1','G1','SC0')]
mean=sum(allLH)/len(allLH)
def lgh(h,sn):
    for y in (sn,sn-1):
        L=lg.get((h,y))
        if L: return sum(LH.get((L,yy),mean) for yy in (y-2,y-1,y))/3-mean
    return 0
for k in (1.0,0.5):
    print(f'par championnat x{k}',round(ll(lambda h,sn:k*lgh(h,sn)),4))
lg={}
for r in rows: lg[(r['HomeTeam'],season(r['MatchDate']))]=r['Division']
def lgh(h,sn):
    for y in (sn-1,sn-2):
        L=lg.get((h,y))
        if L and (L,y) in LH: return LH[(L,y)]-56
    return 0
print('avantage du championnat   ',round(ll(lgh),4))
print('moitié championnat        ',round(ll(lambda h,sn:0.5*lgh(h,sn)),4))
