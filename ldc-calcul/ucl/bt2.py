import json, math, sys
sys.path.insert(0,'/home/claude/work')
from model import probs
G=json.load(open('bt_games.json'))
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]; RHO=-0.0433
def pr(g,H,C,S):
    x=(g['d']*S+(0 if g['neu'] else H))/100
    lh,la=math.exp(P[0]+C+P[1]*x), math.exp(P[2]+C-P[3]*x)
    ph,pd,pa,_=probs(lh,la,RHO); return ph,pd,pa
def evalset(gs,th):
    rows=[]
    for g in gs:
        ph,pd,pa=pr(g,*th); fav=0 if ph>=pa else 2; pf=ph if fav==0 else pa
        o=0 if g['hg']>g['ag'] else (1 if g['hg']==g['ag'] else 2)
        rows.append((pf,pf+pd,o==fav,o!=(2 if fav==0 else 0)))
    return rows
for lab,th,gs in (('test impair (réglé sur pair)',(50,0.08,0.84),[g for g in G if int(g['s'][:4])%2]),('test pair (réglé sur impair)',(61,0.15,0.83),[g for g in G if int(g['s'][:4])%2==0])):
    rows=evalset(gs,th); print(lab,len(rows))
    for lo,hi in ((0.5,0.6),(0.6,0.7),(0.7,0.8),(0.8,1)):
        s=[r for r in rows if lo<=r[0]<hi]; 
        if s: print(f"  victoire prévue {lo:.0%}-{hi:.0%}: n={len(s)} réussite {sum(r[2] for r in s)/len(s):.0%} (prévu {sum(r[0] for r in s)/len(s):.0%})")
    for lo,hi in ((0.6,0.7),(0.7,0.75),(0.75,0.8),(0.8,0.9),(0.9,1)):
        s=[r for r in rows if lo<=r[1]<hi and r[0]<0.6]
        if s: print(f"  ou nul (favori<60%) {lo:.0%}-{hi:.0%}: n={len(s)} réussite {sum(r[3] for r in s)/len(s):.0%} (prévu {sum(r[1] for r in s)/len(s):.0%})")
# ancien réglage (H=50,C=0.17,S=1) pour comparaison
rows=evalset(G,(50,0.17,1.0)); s=[r for r in rows if r[0]>=0.6]; print('ancien réglage, victoires >=60%:',len(s), f"{sum(r[2] for r in s)/len(s):.0%} prévu {sum(r[0] for r in s)/len(s):.0%}")
rows=evalset(G,(56,0.12,0.84)); s=[r for r in rows if r[0]>=0.6]; print('nouveau réglage, victoires >=60%:',len(s), f"{sum(r[2] for r in s)/len(s):.0%} prévu {sum(r[0] for r in s)/len(s):.0%}")
