# Étape 1 bis du nouveau modèle : un score de PERFORMANCE (points) par joueur, à la place de la valeur marchande.
# Principe : impact par 90 min en « buts créés ou évités » (attaque + défense), comparé aux autres joueurs du même poste en Ligue 1 (écart-type),
# ramené vers la moyenne du poste quand le joueur a peu de minutes (poids n90 / (n90 + K)), puis converti : points = 50 + 15 x écart.
#   50 = joueur moyen de Ligue 1 à son poste ; 65 = un écart-type au-dessus ; 35 = un écart-type en dessous.
# Outfield : attaque = 0,5 x buts hors penalty + 0,5 x tirs pondérés (0,07 par tir non cadré, 0,30 par tir cadré) + 0,45 x passes décisives ; défense = 0,03 x (tacles gagnés + interceptions)
# Gardien : arrêts - taux d'arrêt moyen des gardiens x tirs cadrés subis, par 90 min.
# Usage : python3 -I modele-valeur/etape1b_performance.py   (lit stats_joueurs_<date>.json ; écrit performance_joueurs_<date>.json)
import json, os, re, unicodedata, statistics as st, glob
D = os.path.dirname(os.path.abspath(__file__))
f = sorted(glob.glob(os.path.join(D, 'stats_joueurs_*.json')))[-1]
S = json.load(open(f, encoding='utf-8')); date = S['date']
K_OUT, K_GK, MIN90_REF = 4.0, 5.0, 2.5
def norm(s): return re.sub(r"[^a-z ]", '', unicodedata.normalize('NFD', s.lower().replace('-', ' ').replace("'", '')).encode('ascii', 'ignore').decode()).strip()
def attaque(j): return 0.5 * j['butsHorsPen'] + 0.5 * (0.07 * (j['tirs'] - j['cadres']) + 0.30 * j['cadres']) + 0.45 * j['passes']
def defense(j): return 0.03 * (j['tacles'] + j['interceptions'])
TEAMS = {'Nice': 'OGC Nice', 'Paris SG': 'Paris Saint-Germain', 'Angers': 'Angers SCO', 'Auxerre': 'AJ Auxerre', 'Brest': 'Stade Brestois', 'Le Havre': 'Le Havre AC', 'Le Mans': 'Le Mans FC', 'Lens': 'RC Lens', 'Lille': 'LOSC Lille', 'Lorient': 'FC Lorient', 'Lyon': 'Olympique Lyonnais', 'Marseille': 'Olympique de Marseille', 'Monaco': 'AS Monaco', 'Paris FC': 'Paris FC', 'Rennes': 'Stade Rennais', 'Strasbourg': 'RC Strasbourg', 'Toulouse': 'Toulouse FC', 'Troyes': 'ES Troyes AC'}
_h = open(os.path.join(D, '..', 'elo.html'), encoding='utf-8').read(); _i = _h.index('const EMBED = ')
SQ = json.loads(_h[_i + 14:_h.index('\n', _i)].rstrip().rstrip(';'))['SQUADS']
SLOT = {'G': 'GK', 'DC': 'DC', 'DL': 'DL', 'MI': 'MI', 'AT': 'FW', 'BU': 'FW'}
def slot(j):
    t = set(norm(j['nom']).split()); best, sc = None, 0
    for q in SQ.get(TEAMS[j['equipe']], []):
        u = set(norm(q[0]).split()); inter = len(t & u)
        if inter and inter / min(len(t), len(u)) > sc: best, sc = q, inter / min(len(t), len(u))
    if best and sc >= 0.5: return SLOT[best[1]], True
    return {'DF': 'DC', 'MF': 'MI', 'FW': 'FW'}.get(j['poste'].split(',')[0], 'MI'), False
def grp(j): return j['groupe']
for j in S['joueurs']: j['groupe'], j['pAppar'] = slot(j)
for j in S['joueurs']: j['raw90'] = (attaque(j) + defense(j)) / j['n90'] if j['n90'] > 0 else 0.0
dist = {}
for g in ('DC', 'DL', 'MI', 'FW'):
    v = [j['raw90'] for j in S['joueurs'] if grp(j) == g and j['n90'] >= MIN90_REF]; dist[g] = (st.mean(v), st.pstdev(v), len(v))
tot_sv = sum(x['arrets'] for x in S['gardiens']) / sum(x['tirsCadresSubis'] for x in S['gardiens'])
for x in S['gardiens']: x['raw90'] = (x['arrets'] - tot_sv * x['tirsCadresSubis']) / x['n90']
vg = [x['raw90'] for x in S['gardiens'] if x['n90'] >= 3]; dist['GK'] = (st.mean(vg), st.pstdev(vg), len(vg))
def points(raw90, n90, g):
    m, s, _ = dist[g]; z = (raw90 - m) / s; k = K_GK if g == 'GK' else K_OUT
    return 50 + 15 * z * n90 / (n90 + k)
for j in S['joueurs']: j['points'] = round(points(j['raw90'], j['n90'], grp(j)), 1)
for x in S['gardiens']: x['points'] = round(points(x['raw90'], x['n90'], 'GK'), 1)
json.dump({'date': date, 'source': S['source'], 'methode': {'K_outfield': K_OUT, 'K_gardien': K_GK, 'echelle': '50 + 15 x ecart-type', 'tauxArretMoyen': round(tot_sv, 3), 'distribution': {g: {'moyenne': round(v[0], 4), 'ecartType': round(v[1], 4), 'n': v[2]} for g, v in dist.items()}}, 'joueurs': S['joueurs'], 'gardiens': S['gardiens']}, open(os.path.join(D, 'performance_joueurs_' + date + '.json'), 'w'), ensure_ascii=False, indent=0)
print(sum(1 for j in S['joueurs'] if j['pAppar']), 'joueurs sur', len(S['joueurs']), 'rattachés à un poste elo.html')
print('distribution par poste (moyenne, écart-type, effectif) :', {g: (round(v[0], 3), round(v[1], 3), v[2]) for g, v in dist.items()}, '| taux d\'arrêt moyen', round(tot_sv, 3))
for g in ('FW', 'MI', 'DC', 'DL'):
    L = sorted([j for j in S['joueurs'] if grp(j) == g and j['n90'] >= MIN90_REF], key=lambda j: -j['points'])
    print('\n', g, 'meilleurs :', ' | '.join('%s (%s) %.0f' % (j['nom'], j['equipe'], j['points']) for j in L[:6]))
    print('   ', g, 'moins bons :', ' | '.join('%s (%s) %.0f' % (j['nom'], j['equipe'], j['points']) for j in L[-4:]))
L = sorted([x for x in S['gardiens'] if x['n90'] >= 3], key=lambda x: -x['points']); print('\n GK :', ' | '.join('%s (%s) %.0f' % (x['nom'], x['equipe'], x['points']) for x in L))
