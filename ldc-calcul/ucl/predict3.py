import json, math, sys
sys.path.insert(0,'/home/claude/work')
import numpy as np
from model import probs
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]; RHO=0.05
S=0.84; C=0.12; W=1.0   # réglages validés sur 1544 matchs de LdC 2011-2026 ; W = part du modèle
R=json.load(open('ratings2.json'))['R']; FX=json.load(open('fixtures.json')); OD=json.load(open('odds.json'))
HT=json.load(open('hfa_team.json')); ABS=json.load(open('abs.json'))
out=[]
for f in FX:
    h,a=f['h'],f['a']
    x=(S*(R[h]+ABS.get(h,0)-R[a]-ABS.get(a,0))+HT.get(h,56))/100
    lh,la=math.exp(P[0]+C+P[1]*x), math.exp(P[2]+C-P[3]*x)
    mh,md,ma,M=probs(lh,la,RHO)
    o=OD.get(h)
    if o:
        iv=[1/v for v in o]; s=sum(iv); kh,kd,ka=[v/s for v in iv]
        ph,pd,pa=W*mh+(1-W)*kh, W*md+(1-W)*kd, W*ma+(1-W)*ka
    else: ph,pd,pa=mh,md,ma
    oc=int(np.argmax([ph,pd,pa])); best=(-1,0,0)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            k=0 if i>j else (1 if i==j else 2)
            if k==oc and M[i,j]>best[0]: best=(M[i,j],i,j)
    fav=0 if ph>=pa else 2; pf=ph if fav==0 else pa; dc=pf+pd; team=h if fav==0 else a
    if pf>=0.60: r=('win','Victoire '+team,pf)
    else: r=('dc',team+' ou nul',dc)
    w=None
    if o: w=(o[0] if fav==0 else o[2]) if r[0]=='win' else 1/(1/(o[0] if fav==0 else o[2])+1/o[1])
    out.append(dict(date=f['date'],h=h,a=a,hid=f['hid'],aid=f['aid'],eh=round(R[h]),ea=round(R[a]),ph=ph,pd=pd,pa=pa,mod=[mh,md,ma],score=f"{best[1]}-{best[2]}",reco=r[0],label=r[1],prob=r[2],mini=1/r[2],odds=o,wo=w))
json.dump(out,open('preds.json','w'),ensure_ascii=False,indent=1)
for x in out: print(f"{x['h'][:14]:14s}-{x['a'][:14]:14s} mod {x['mod'][0]:.0%}/{x['mod'][1]:.0%}/{x['mod'][2]:.0%} -> {x['ph']:.0%}/{x['pd']:.0%}/{x['pa']:.0%} {x['label'][:28]:28s} {x['prob']:.0%} mini {x['mini']:.2f} wmx {x['wo']:.2f} {'OK' if x['wo']>=x['mini'] else ''}")
