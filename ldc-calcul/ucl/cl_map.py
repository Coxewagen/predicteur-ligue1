import json, csv, unicodedata, re
from collections import defaultdict
R=json.load(open('cl_hist_raw.json'))
clubs=defaultdict(set)
for r in csv.DictReader(open('data/cf/data/EloRatings.csv')): clubs[r['country']].add(r['club'])
CC={'MCO':'FRA','WAL':'ENG'}
STOP=set('fc cf ac as sc afc ssc club de calcio sv vfb vfl fk sk cd rc ud bk if tsg kv krc sl cp bc 1 04 1909 1899 1907 1913 sad cfc ogc olympique stade sporting real atletico athletic borussia royal pfc sfp gnk hnk nk rsc lille losc ksc'.split())
def toks(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9 ]',' ',s); return [t for t in s.split() if t]
MAN={"FC Bayern München":"Bayern Munich","FC Internazionale Milano":"Inter","Sporting Clube de Portugal":"Sp Lisbon","Sport Lisboa e Benfica":"Benfica","Club Atlético de Madrid":"Ath Madrid","Paris Saint-Germain FC":"Paris SG","Manchester City FC":"Man City","Manchester United FC":"Man United","Athletic Club":"Ath Bilbao","Borussia Mönchengladbach":"MGladbach","Eintracht Frankfurt":"Ein Frankfurt","Sporting Clube de Braga":"Sp Braga","Real Sociedad de Fútbol":"Sociedad","Real Betis Balompié":"Betis","SSC Napoli":"Napoli","AC Milan":"Milan","AS Roma":"Roma","Juventus FC":"Juventus","Olympique de Marseille":"Marseille","Olympique Lyonnais":"Lyon","Stade Rennais FC 1901":"Rennes","Bayer 04 Leverkusen":"Leverkusen","FC Red Bull Salzburg":"Salzburg","RB Leipzig":"RB Leipzig","FC Porto":"Porto","PSV":"PSV Eindhoven","AFC Ajax":"Ajax","Tottenham Hotspur FC":"Tottenham","Newcastle United FC":"Newcastle","Club Brugge KV":"Club Brugge","Valencia CF":"Valencia","Sevilla FC":"Sevilla","Villarreal CF":"Villarreal","Bodø/Glimt":"Bodoe Glimt","FK Bodø/Glimt":"Bodoe Glimt","Royale Union Saint-Gilloise":"Union SG","Stade Brestois 29":"Brest","Galatasaray AŞ":"Galatasaray","Fenerbahçe SK":"Fenerbahce","Beşiktaş JK":"Besiktas","Olympiacos FC":"Olympiakos","Olympiakos CFP":"Olympiakos","Celtic FC":"Celtic","Rangers FC":"Rangers","FC København":"FC Kobenhavn","FC Kobenhavn":"FC Kobenhavn","Paris FC":"Paris FC","LOSC Lille":"Lille","Lille OSC":"Lille","Girona FC":"Girona","Atalanta BC":"Atalanta","Bologna FC 1909":"Bologna","Liverpool FC":"Liverpool","Arsenal FC":"Arsenal","Chelsea FC":"Chelsea","Aston Villa FC":"Aston Villa","SL Benfica":"Benfica","Sporting CP":"Sp Lisbon","Feyenoord Rotterdam":"Feyenoord","Feyenoord":"Feyenoord","AS Monaco FC":"Monaco","Racing Club de Lens":"Lens","RC Lens":"Lens","SK Sturm Graz":"Sturm Graz","VfB Stuttgart":"Stuttgart","Borussia Dortmund":"Dortmund","FC Barcelona":"Barcelona","Real Madrid CF":"Real Madrid","Villarreal":"Villarreal","FC Schalke 04":"Schalke 04","VfL Wolfsburg":"Wolfsburg","TSG 1899 Hoffenheim":"Hoffenheim","1. FC Union Berlin":"Union Berlin","SV Werder Bremen":"Werder Bremen","Hamburger SV":"Hamburg","FC Basel 1893":"Basel"}
def find(name,cc):
    if name in MAN: return MAN[name]
    c=CC.get(cc,cc); pool=clubs.get(c)
    if not pool: return None
    t=[x for x in toks(name) if x not in STOP]
    best=(0,None)
    for p in pool:
        pt=[x for x in toks(p) if x not in STOP]
        if not pt: continue
        sc=sum(1 for x in t if any(x==y or (len(x)>3 and (x.startswith(y) or y.startswith(x))) for y in pt))
        if sc>best[0]: best=(sc,p)
    return best[1]
M={}; miss=set()
for r in R:
    for n,c in ((r['h'],r['hc']),(r['a'],r['ac'])):
        if n not in M:
            M[n]=find(n,c)
            if not M[n]: miss.add((n,c))
json.dump(M,open('cl_names.json','w'),ensure_ascii=False,indent=0)
ok=sum(1 for r in R if M[r['h']] and M[r['a']]); print('matchs mappés',ok,'/',len(R))
print(sorted(miss)[:60])
