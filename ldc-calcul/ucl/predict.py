import json, math, sys
sys.path.insert(0,'/home/claude/work')
import numpy as np
from model import lambdas, probs
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]; RHO=-0.043258059130917466; H=50; C=0.17
R=json.load(open('ratings2.json'))['R']; FX=json.load(open('fixtures.json')); OD=json.load(open('odds.json')); HT=json.load(open('hfa_team.json')); ABS=json.load(open('abs.json'))
out=[]
for f in FX:
    h,a=f['h'],f['a']; d=R[h]+ABS.get(h,0)-R[a]-ABS.get(a,0)+HT.get(h,H)
    lh,la=lambdas(d,P); lh*=math.exp(C); la*=math.exp(C)
    ph,pd,pa,M=probs(lh,la,RHO)
    oc=int(np.argmax([ph,pd,pa])); best=(-1,0,0)
    for ii in range(M.shape[0]):
        for jj in range(M.shape[1]):
            k=0 if ii>jj else (1 if ii==jj else 2)
            if k==oc and M[ii,jj]>best[0]: best=(M[ii,jj],ii,jj)
    i,j=best[1],best[2]
    fav=0 if ph>=pa else 2; pf=ph if fav==0 else pa; dc=pf+pd
    team=h if fav==0 else a
    if pf>=0.60: r=('win','Victoire '+team,pf,1/min(pf,0.72))
    elif dc>=0.70: r=('dc',team+' ou nul',dc,1/(min(dc,0.71) if dc<0.75 else min(dc,0.77)))
    else: r=('none','Trop serré · '+team+' ou nul',dc,1/dc)
    o=OD.get(h); w=None
    if o:
        w=(o[0] if fav==0 else o[2]) if r[0]=='win' else 1/(1/(o[0] if fav==0 else o[2])+1/o[1])
    out.append(dict(date=f['date'],h=h,a=a,hid=f['hid'],aid=f['aid'],eh=round(R[h]),ea=round(R[a]),ph=ph,pd=pd,pa=pa,score=f"{i}-{j}",xg=[round(lh,2),round(la,2)],reco=r[0],label=r[1],prob=r[2],mini=r[3],odds=o,wo=w))
json.dump(out,open('preds.json','w'),ensure_ascii=False,indent=1)
for x in out: print(f"{x['date'][5:16]} {x['h'][:16]:16s} {x['eh']} - {x['a'][:16]:16s} {x['ea']}  {x['ph']:.0%} {x['pd']:.0%} {x['pa']:.0%}  {x['score']}  {x['label'][:34]:34s} {x['prob']:.0%} mini {x['mini']:.2f} wmx {x['wo'] and round(x['wo'],2)}")
