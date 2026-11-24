import json, csv, bisect, math, statistics as st
from collections import defaultdict
LH=json.load(open('hfa.json'))['LH']
E=lambda d:1/(1+10**(-d/400)); S={'H':1,'D':.5,'A':0}
hist=defaultdict(list)   # club -> [(date, résidu)]
for r in csv.DictReader(open('data/cf/data/Matches.csv')):
    if not r['HomeElo'] or not r['AwayElo'] or not r['FTResult'] or r['Division'] not in LH: continue
    d=float(r['HomeElo'])-float(r['AwayElo'])+LH[r['Division']]; s=S[r['FTResult']]
    hist[r['HomeTeam']].append((r['MatchDate'],s-E(d))); hist[r['AwayTeam']].append((r['MatchDate'],(1-s)-E(-d)))
for k in hist: hist[k].sort()
def form(c,date,n=5):
    h=hist.get(c,[]); i=bisect.bisect_left(h,(date,))
    xs=[x[1] for x in h[max(0,i-n):i]]
    return sum(xs) if len(xs)==n else None
R=json.load(open('cl_hist_raw.json')); M=json.load(open('cl_names.json')); G=json.load(open('bt_games.json'))
# reconstituer l'ordre utilisé dans bt.py pour relier G et R
import csv as c2
snaps=defaultdict(list)
for r in c2.DictReader(open('data/cf/data/EloRatings.csv')): snaps[r['club']].append((r['date'],float(r['elo'])))
for k in snaps: snaps[k].sort()
def elo(cl,d):
    s=snaps.get(cl); 
    if not s: return None
    ds=[x[0] for x in s]; i=bisect.bisect_right(ds,d)-1
    return s[i][1] if i>=0 and s[i][0]>=str(int(d[:4])-1) else None
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]
last={r['season']:r for r in R}
rows=[]
for r in R:
    h,a=M.get(r['h']),M.get(r['a'])
    if not h or not a: continue
    eh,ea=elo(h,r['date']),elo(a,r['date'])
    if eh is None or ea is None: continue
    fh,fa=form(h,r['date']),form(a,r['date'])
    if fh is None or fa is None: continue
    x=(0.84*(eh-ea)+(0 if r is last[r['season']] else 56))/100
    lh,la=math.exp(P[0]+.12+P[1]*x), math.exp(P[2]+.12-P[3]*x)
    rows.append((fh-fa, (r['hg']-r['ag'])-(lh-la)))
print('LdC n=',len(rows))
xs=[r[0] for r in rows]; ys=[r[1] for r in rows]
mx,my=st.mean(xs),st.mean(ys); b=sum((x-mx)*(y-my) for x,y in rows)/sum((x-mx)**2 for x in xs)
res=[y-my-b*(x-mx) for x,y in rows]; se=math.sqrt(sum(e*e for e in res)/(len(rows)-2)/sum((x-mx)**2 for x in xs))
print(f"LdC : +1 point de forme (sur 5 matchs) = {b:+.3f} but d'écart (±{se:.3f})")
for lo,hi in ((-9,-1),(-1,1),(1,9)):
    s=[y for x,y in rows if lo<=x<hi]; print(f"  écart de forme {lo}..{hi}: n={len(s)} résidu {st.mean(s):+.2f}")
# même test en championnat (forme -> match suivant)
dom=[]
for r in csv.DictReader(open('data/cf/data/Matches.csv')):
    if r['MatchDate']<'2015-07-01' or not r['HomeElo'] or not r['AwayElo'] or r['Division'] not in ('E0','SP1','D1','I1','F1','P1','N1','T1') or not r['FTHome']: continue
    fh,fa=form(r['HomeTeam'],r['MatchDate']),form(r['AwayTeam'],r['MatchDate'])
    if fh is None or fa is None: continue
    d=float(r['HomeElo'])-float(r['AwayElo'])+LH[r['Division']]
    dom.append((fh-fa, S[r['FTResult']]-E(d)))
xs=[r[0] for r in dom]; mx=st.mean(xs); my=st.mean([r[1] for r in dom])
b=sum((x-mx)*(y-my) for x,y in dom)/sum((x-mx)**2 for x in xs)
res=[y-my-b*(x-mx) for x,y in dom]; se=math.sqrt(sum(e*e for e in res)/(len(dom)-2)/sum((x-mx)**2 for x in xs))
print(f"Championnats n={len(dom)} : +1 point de forme = {b:+.4f} de résultat (±{se:.4f})")
