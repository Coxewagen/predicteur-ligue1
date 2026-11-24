import json, csv, bisect, math, sys
from collections import defaultdict
sys.path.insert(0,'/home/claude/work')
from model import probs
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
R=json.load(open('cl_hist_raw.json')); M=json.load(open('cl_names.json'))
snaps=defaultdict(list)
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')): snaps[r['club']].append((r['date'],float(r['elo'])))
for k in snaps: snaps[k].sort()
def elo(c,d):
    s=snaps.get(c); 
    if not s: return None
    i=bisect.bisect_right([x[0] for x in s],d)-1
    return s[i][1] if i>=0 and s[i][0]>=str(int(d[:4])-1) else None
last={}
for r in R: last[r['season']]=r
G=[]
for r in R:
    h,a=M.get(r['h']),M.get(r['a'])
    if not h or not a: continue
    eh,ea=elo(h,r['date']),elo(a,r['date'])
    if eh is None or ea is None: continue
    G.append(dict(s=r['season'],d=eh-ea,hg=r['hg'],ag=r['ag'],neu=r is last[r['season']],ko=not r['stage'].startswith(('League','Group'))))
print('matchs utilisables',len(G))
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]; RHO=-0.0433
def lam(g,H,C,S):
    x=(g['d']*S+(0 if g['neu'] else H))/100
    return math.exp(P[0]+C+P[1]*x), math.exp(P[2]+C-P[3]*x)
def nll(th,gs):
    H,C,S=th; t=0
    for g in gs:
        lh,la=lam(g,H,C,S); t-=poisson.logpmf(g['hg'],lh)+poisson.logpmf(g['ag'],la)
    return t
train=[g for g in G if int(g['s'][:4])%2==0]; test=[g for g in G if int(g['s'][:4])%2==1]
for name,gs in (('pair',train),('impair',test),('tout',G)):
    r=minimize(nll,[50,0,1],args=(gs,),method='Nelder-Mead'); print(name,'H=%.0f C=%.2f S=%.2f'%tuple(r.x))
json.dump(G,open('bt_games.json','w'))
