import json, csv, bisect, math, statistics as st
from collections import defaultdict
LH=json.load(open('hfa.json'))['LH']; E=lambda d:1/(1+10**(-d/400)); S={'H':1,'D':.5,'A':0}
R=json.load(open('cl_hist_raw.json')); M=json.load(open('cl_names.json'))
res=defaultdict(list)  # club -> [(date, win?)]
dom=[]
for r in csv.DictReader(open('data/cf/data/Matches.csv')):
    if not r['FTResult']: continue
    res[r['HomeTeam']].append((r['MatchDate'],r['FTResult']=='H')); res[r['AwayTeam']].append((r['MatchDate'],r['FTResult']=='A'))
    if r['HomeElo'] and r['AwayElo'] and r['Division'] in ('E0','SP1','D1','I1','F1','P1','N1','T1') and r['MatchDate']>='2010-07-01':
        dom.append(r)
for r in R:
    for n,w in ((r['h'],r['hg']>r['ag']),(r['a'],r['ag']>r['hg'])):
        if M.get(n): res[M[n]].append((r['date'],w))
for k in res: res[k].sort()
def streak(c,d):
    h=res.get(c,[]); i=bisect.bisect_left(h,(d,))-1; n=0
    while i>=0 and not h[i][1]: n+=1; i-=1
    return n
def b(n): return '0-2' if n<3 else ('3-5' if n<6 else ('6-8' if n<9 else '9+'))
# championnats : résultat (points/3 façon Elo) vs attendu, du point de vue de chaque équipe
D=defaultdict(list)
for r in dom:
    d=float(r['HomeElo'])-float(r['AwayElo'])+LH[r['Division']]; s=S[r['FTResult']]
    D[b(streak(r['HomeTeam'],r['MatchDate']))].append(s-E(d)); D[b(streak(r['AwayTeam'],r['MatchDate']))].append((1-s)-E(-d))
print('CHAMPIONNATS (résultat réel - attendu, en part de victoire)')
for k in ('0-2','3-5','6-8','9+'):
    v=D[k]; print(f"  {k} matchs sans victoire : n={len(v)}  {st.mean(v):+.3f} ±{st.pstdev(v)/math.sqrt(len(v)):.3f}")
# LdC
snaps=defaultdict(list)
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')): snaps[r['club']].append((r['date'],float(r['elo'])))
for k in snaps: snaps[k].sort()
def elo(c,d):
    s=snaps.get(c); 
    if not s: return None
    ds=[x[0] for x in s]; i=bisect.bisect_right(ds,d)-1
    return s[i][1] if i>=0 and s[i][0]>=str(int(d[:4])-1) else None
last={r['season']:r for r in R}; C=defaultdict(list)
for r in R:
    h,a=M.get(r['h']),M.get(r['a'])
    if not h or not a: continue
    eh,ea=elo(h,r['date']),elo(a,r['date'])
    if eh is None or ea is None: continue
    d=0.84*(eh-ea)+(0 if r is last[r['season']] else 56); s=1 if r['hg']>r['ag'] else (.5 if r['hg']==r['ag'] else 0)
    C[b(streak(h,r['date']))].append(s-E(d)); C[b(streak(a,r['date']))].append((1-s)-E(-d))
print('LIGUE DES CHAMPIONS')
for k in ('0-2','3-5','6-8','9+'):
    v=C[k]
    if v: print(f"  {k} matchs sans victoire : n={len(v)}  {st.mean(v):+.3f} ±{st.pstdev(v)/math.sqrt(len(v)):.3f}")
