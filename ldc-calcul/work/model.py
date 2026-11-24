import math, numpy as np
from data import seasons
from scipy.stats import poisson
from scipy.optimize import minimize
MAXG=10
def gmult(gd):
    gd=abs(gd); return 1 if gd<=1 else (1.5 if gd==2 else (11+gd)/8)
def run_elo(S, K=20, H=60, carry=0.75, promo=-30, record=None):
    """parcourt les saisons dans l'ordre ; record(season, md, h, a, d, hg, ag) appelé AVANT la mise à jour.
       d = Rh + H - Ra (avantage domicile inclus)."""
    R={}; prev_teams=set()
    for si,(y,ms) in enumerate(S):
        teams={m[1] for m in ms}|{m[2] for m in ms}
        if R:
            mean=np.mean([R[t] for t in prev_teams])
            relegated=[t for t in prev_teams if t not in teams]
            rel=np.mean([R[t] for t in relegated]) if relegated else mean-100
            newR={}
            for t in teams:
                if t in prev_teams: newR[t]=mean+(R[t]-mean)*carry
                else: newR[t]=rel+promo
            # recentrage à 1500
            m2=np.mean(list(newR.values())); R={t:v-m2+1500 for t,v in newR.items()}
        else: R={t:1500 for t in teams}
        for m in ms:
            md,h,a,hg,ag=m[:5]
            if len(m)>5 and not m[5]: continue
            d=R[h]+H-R[a]
            if record: record(y,md,h,a,d,hg,ag)
            E=1/(1+10**(-d/400)); Sres=1 if hg>ag else (0.5 if hg==ag else 0)
            delta=K*gmult(hg-ag)*(Sres-E); R[h]+=delta; R[a]-=delta
        prev_teams=teams
    return R
def lambdas(d,p):
    a0,a1,b0,b1=p; x=d/100
    return math.exp(a0+a1*x), math.exp(b0-b1*x)
def probs(lh,la,rho=0.0):
    i=np.arange(MAXG+1); M=np.outer(poisson.pmf(i,lh),poisson.pmf(i,la))
    if rho:
        M[0,0]*=1-lh*la*rho; M[0,1]*=1+lh*rho; M[1,0]*=1+la*rho; M[1,1]*=1-rho
    M=np.clip(M,0,None); M/=M.sum()
    return np.tril(M,-1).sum(), np.trace(M), np.triu(M,1).sum(), M
def fit_goals(rows):
    d=np.array([r[0] for r in rows])/100; hg=np.array([r[1] for r in rows]); ag=np.array([r[2] for r in rows])
    def nll(p):
        lh=np.exp(p[0]+p[1]*d); la=np.exp(p[2]-p[3]*d)
        return -(hg*np.log(lh)-lh + ag*np.log(la)-la).sum()
    return minimize(nll,[0.3,0.2,0.1,0.2]).x
def fit_rho(rows,p):
    def nll(r):
        s=0
        for d,hg,ag in rows:
            lh,la=lambdas(d,p); M=probs(lh,la,r[0])[3]; s-=math.log(max(M[min(hg,MAXG),min(ag,MAXG)],1e-12))
        return s
    return minimize(nll,[-0.05],bounds=[(-0.3,0.3)]).x[0]
