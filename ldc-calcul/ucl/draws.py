import json, math, sys
sys.path.insert(0,'/home/claude/work')
from model import probs
G=json.load(open('bt_games.json'))
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]
def pr(g,rho,C=.12):
    x=(0.84*g['d']+(0 if g['neu'] else 56))/100
    lh,la=math.exp(P[0]+C+P[1]*x), math.exp(P[2]+C-P[3]*x); return probs(lh,la,rho)[:3]
def ev(rho,show=False):
    bins={}; ll=0
    for g in G:
        ph,pd,pa=pr(g,rho); o=0 if g['hg']>g['ag'] else (1 if g['hg']==g['ag'] else 2); ll-=math.log([ph,pd,pa][o])
        gap=abs(ph-pa); k='serré (<15 pts)' if gap<.15 else ('moyen (15-35)' if gap<.35 else 'déséquilibré (>35)')
        b=bins.setdefault(k,[0,0,0]); b[0]+=1; b[1]+=pd; b[2]+=(o==1)
        # « ou nul » réussite
    if show:
        for k,(n,pdx,dr) in bins.items(): print(f"  {k:20s} n={n:4d} nul prévu {pdx/n:.1%} réel {dr/n:.1%}")
    return ll/len(G)
print('rho actuel -0.043'); print(' erreur',round(ev(-0.0433,True),4))
for rho in (-0.15,-0.1,0,0.05,0.1):
    print('rho',rho,'erreur',round(ev(rho),4))
# réussite des « ou nul » prévus vs annoncés, par tranche
rows=[]
for g in G:
    ph,pd,pa=pr(g,-0.0433); fav=0 if ph>=pa else 2; pf=ph if fav==0 else pa
    o=0 if g['hg']>g['ag'] else (1 if g['hg']==g['ag'] else 2)
    rows.append((pf+pd, o!=(2 if fav==0 else 0), pf, o==fav))
for lo,hi in ((.6,.65),(.65,.7),(.7,.75),(.75,.8),(.8,.85),(.85,1)):
    s=[r for r in rows if lo<=r[0]<hi]
    if s: print(f"  « ou nul » annoncé {lo:.0%}-{hi:.0%}: n={len(s)} réussite {sum(r[1] for r in s)/len(s):.0%} (annoncé {sum(r[0] for r in s)/len(s):.0%})")
print('--- validation croisée')
full=G
for name,tr,te in (('pair->impair',[g for g in full if int(g['s'][:4])%2==0],[g for g in full if int(g['s'][:4])%2]),('impair->pair',[g for g in full if int(g['s'][:4])%2],[g for g in full if int(g['s'][:4])%2==0])):
    G=tr; best=min((ev(r),r) for r in (-0.0433,0,0.03,0.05,0.08,0.1,0.15))
    G=te; print(name,'meilleur rho',best[1],'test',round(ev(best[1]),4),'vs actuel',round(ev(-0.0433),4))
G=full
for rho in (0.05,):
    rows=[]
    for g in G:
        ph,pd,pa=pr(g,rho); fav=0 if ph>=pa else 2; pf=ph if fav==0 else pa
        o=0 if g['hg']>g['ag'] else (1 if g['hg']==g['ag'] else 2); rows.append((pf+pd, o!=(2 if fav==0 else 0)))
    for lo,hi in ((.6,.65),(.65,.7),(.7,.75),(.75,.8)):
        s=[r for r in rows if lo<=r[0]<hi]; print(f"  rho {rho} « ou nul » {lo:.0%}-{hi:.0%}: n={len(s)} réussite {sum(r[1] for r in s)/len(s):.0%} annoncé {sum(r[0] for r in s)/len(s):.0%}")
