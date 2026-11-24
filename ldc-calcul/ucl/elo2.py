import json,csv,sys
sys.path.insert(0,'/home/claude/work')
from model import gmult
snap={}
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')):
    if r['date']=='2026-09-01': snap[r['club']]=float(r['elo'])
exec(open('ucl_model.py').read().split('snap={}')[0].split('H=50; K=20')[1])  # MAP, EST
M=dict(json.load(open('automap.json'))); M.update(MAP)
M.update({"AEK Athens":"AEK","Atlético Madrid":"Ath Madrid","Bodo/Glimt":"Bodoe Glimt","Borussia Mönchengladbach":"MGladbach","Deportivo":"La Coruna","Eintracht Frankfurt":"Ein Frankfurt","Espanyol":"Espanol","FC Cologne":"FC Koln","Fortuna Sittard":"For Sittard","Manchester City":"Man City","Manchester United":"Man United","Nottingham Forest":"Nott'm Forest","Paris Saint-Germain":"Paris SG","Rapid Vienna":"Rapid Wien","Sint-Truidense":"St Truiden","Sporting CP":"Sp Lisbon","WSG Swarovski Tirol":"Wattens","Athletic Club":"Ath Bilbao","Hamarkameratene":"Ham-Kam","Istanbul Basaksehir":"Buyuksehyr"})
G=[tuple(x) for x in json.load(open('allgames.json'))]
# ajouter les matchs LdC manquants
have={(g[0][:10],g[2],g[3]) for g in G}
for l in open('ucl_res.csv'):
    d,h,a,hs,as_,n=l.strip().split(';')
    if (d,h,a) not in have: G.append((d+'T20:00','League Phase',h,a,int(hs),int(as_),int(n)))
G.sort()
R={}; unk=set()
def rating(n):
    if n in R: return R[n]
    if n in EST: R[n]=EST[n]
    elif n in M and M[n] in snap: R[n]=snap[M[n]]
    else: R[n]=1400; unk.add(n)
    return R[n]
H=50; nG=0
for dt,comp,h,a,hs,as_,neu in G:
    rh,ra=rating(h),rating(a); d=rh-ra+(0 if neu else H)
    E=1/(1+10**(-d/400)); S=1 if hs>as_ else (.5 if hs==as_ else 0)
    for t,sg in ((h,1),(a,-1)):
        k=40 if t in EST else 20
        R[t]+=sg*k*gmult(hs-as_)*(S-E)
    nG+=1
print(nG,'matchs; inconnus:',sorted(unk))
old=json.load(open('ratings.json'))
FX=json.load(open('fixtures.json'))
for t in sorted({f['h'] for f in FX}|{f['a'] for f in FX}, key=lambda t:-R[t]):
    print(f"{t:22s} {old['start'][t]:.0f} -> LdC seule {old['R'][t]:.0f} -> avec champ. {R[t]:.0f}")
json.dump({'R':R,'start':old['start']},open('ratings2.json','w'),ensure_ascii=False)
