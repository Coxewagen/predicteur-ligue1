import json, math, sys
sys.path.insert(0,'/home/claude/work')
from model import gmult, lambdas, probs
from scipy.stats import poisson
exec(open('ucl_model.py').read().split("res=[l")[0])
res=[l.strip().split(';') for l in open('ucl_res.csv') if l.strip()]
# pre-match d replay
R=dict(start); rows=[]
for d_,h,a,hs,as_,neu in res:
    hs,as_=int(hs),int(as_); d=R[h]-R[a]+H; rows.append((d,hs,as_))
    E=1/(1+10**(-d/400)); S=1 if hs>as_ else (.5 if hs==as_ else 0)
    for t,sg in ((h,1),(a,-1)): R[t]+=sg*(40 if t in EST else K)*gmult(hs-as_)*(S-E)
best=None
for c in [x/100 for x in range(0,61,2)]:
    ll=0
    for d,hs,as_ in rows:
        lh,la=lambdas(d,P); lh*=math.exp(c); la*=math.exp(c)
        ll-=math.log(poisson.pmf(hs,lh)*poisson.pmf(as_,la))
    if best is None or ll<best[0]: best=(ll,c)
print(best)
