import json, csv, bisect, math, sys, datetime as dt
from collections import defaultdict
sys.path.insert(0,'/home/claude/work')
from model import probs
G=json.load(open('bt_games.json')); R=json.load(open('cl_hist_raw.json')); M=json.load(open('cl_names.json'))
# dates de tous les matchs (championnat + LdC) par club ClubElo
D=defaultdict(set)
for r in csv.DictReader(open('data/cf/data/Matches.csv')):
    D[r['HomeTeam']].add(r['MatchDate']); D[r['AwayTeam']].add(r['MatchDate'])
for r in R:
    for n in (r['h'],r['a']):
        if M.get(n): D[M[n]].add(r['date'])
DS={k:sorted(v) for k,v in D.items()}
def rest(c,d):
    s=DS.get(c,[]); i=bisect.bisect_left(s,d)-1
    if i<0: return None
    return (dt.date.fromisoformat(d)-dt.date.fromisoformat(s[i])).days
P=[0.2435271896000928, 0.22999410049139296, 0.2329922253720047, 0.22124428438233315]
# rejoue les matchs utilisables dans le même ordre que bt.py
import bisect as b2
snaps=defaultdict(list)
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')): snaps[r['club']].append((r['date'],float(r['elo'])))
rows=[]
last={}
for r in R: last[r['season']]=r
for r in R:
    h,a=M.get(r['h']),M.get(r['a'])
    if not h or not a: continue
    def elo(c):
        s=sorted(snaps.get(c,[])); ds=[x[0] for x in s]; i=b2.bisect_right(ds,r['date'])-1
        return s[i][1] if i>=0 and s[i][0]>=str(int(r['date'][:4])-1) else None
    eh,ea=elo(h),elo(a)
    if eh is None or ea is None: continue
    rh,ra=rest(h,r['date']),rest(a,r['date'])
    if rh is None or ra is None or rh>14 or ra>14: continue
    x=(0.84*(eh-ea)+(0 if r is last[r['season']] else 56))/100
    lh,la=math.exp(P[0]+.12+P[1]*x), math.exp(P[2]+.12-P[3]*x)
    exp_gd=lh-la
    rows.append((rh-ra, r['hg']-r['ag']-exp_gd, rh, ra))
import statistics as st
print('n',len(rows))
for lo,hi in ((-99,-2),(-1,1),(2,99)):
    s=[x[1] for x in rows if lo<=x[0]<=hi]; print(f"écart de repos {lo}..{hi} j : n={len(s)} buts au-dessus du prévu pour l'équipe à domicile {st.mean(s):+.2f} ±{st.pstdev(s)/math.sqrt(len(s)):.2f}")
for k in (2,3):
    s=[x[1] for x in rows if x[2]<=k]; t=[-x[1] for x in rows if x[3]<=k]
    print(f"équipe avec <= {k} j de repos : n={len(s)+len(t)} écart {st.mean(s+t):+.2f} ±{st.pstdev(s+t)/math.sqrt(len(s+t)):.2f}")
