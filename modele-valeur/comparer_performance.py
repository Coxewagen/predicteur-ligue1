# Compare deux équipes poste par poste avec le score de performance (points) de chaque joueur.
# Usage : python3 -I modele-valeur/comparer_performance.py comparaison_OGC_Nice__Paris_Saint_Germain.json Nice "Paris SG"
# (lit la composition de comparaison_*.json faite par comparer_equipes.js et performance_joueurs_<date>.json ; écrit performance_<dom>_<ext>.json)
import json, os, re, sys, unicodedata, glob
D = os.path.dirname(os.path.abspath(__file__))
cmp_f, fb_dom, fb_ext = sys.argv[1], sys.argv[2], sys.argv[3]
C = json.load(open(os.path.join(D, cmp_f), encoding='utf-8'))
P = json.load(open(sorted(glob.glob(os.path.join(D, 'performance_joueurs_*.json')))[-1], encoding='utf-8'))
M = P['methode']; dist = M['distribution']
def norm(s): return re.sub(r"[^a-z ]", '', unicodedata.normalize('NFD', s.lower().replace('-', ' ').replace("'", '')).encode('ascii', 'ignore').decode()).strip()
GROUP = {'G': 'GK', 'DC': 'DC', 'DL': 'DL', 'MI': 'MI', 'AT': 'FW', 'BU': 'FW'}
LIBELLE = {'G': 'Gardien', 'DC': 'Défenseur central', 'DL': 'Latéral', 'MI': 'Milieu', 'AT': 'Attaquant', 'BU': 'Avant-centre'}
def find(nom, equipe, gk):
    pool = [x for x in (P['gardiens'] if gk else P['joueurs']) if x['equipe'] == equipe]
    n = norm(nom); t = set(n.split())
    for x in pool:
        if norm(x['nom']) == n: return x
    best, sc = None, 0
    for x in pool:
        u = set(norm(x['nom']).split()); inter = len(t & u)
        if inter and inter / min(len(t), len(u)) > sc: best, sc = x, inter / min(len(t), len(u))
    return best if sc >= 0.5 else None
def pts(x, g):
    m, s = dist[g]['moyenne'], dist[g]['ecartType']; k = M['K_gardien'] if g == 'GK' else M['K_outfield']
    return round(50 + 15 * (x['raw90'] - m) / s * x['n90'] / (x['n90'] + k), 1)
def equipe(side, fb):
    out = []
    for l in C['lignes']:
        p = l[side]; poste = l['poste']; x = find(p['nom'], fb, poste == 'G')
        out.append({'poste': poste, 'nom': p['nom'], 'fbref': x['nom'] if x else None, 'minutes': x['min'] if x else 0, 'points': pts(x, GROUP[poste]) if x else None, 'remplace': p.get('absentRemplace')})
    return out
A, B = equipe('dom', fb_dom), equipe('ext', fb_ext)
for L in (A, B): print([ (r['nom'], r['fbref']) for r in L if r['fbref'] is None or norm(r['nom']) != norm(r['fbref'] or '')])
# appariement : à chaque poste, du meilleur au moins bon
rows = []
for g in ('G', 'DC', 'DL', 'MI', 'AT', 'BU'):
    a = sorted([r for r in A if r['poste'] == g], key=lambda r: -(r['points'] or 0)); b = sorted([r for r in B if r['poste'] == g], key=lambda r: -(r['points'] or 0))
    for x, y in zip(a, b): rows.append({'poste': LIBELLE[g], 'dom': x, 'ext': y})
for r in rows:
    f = lambda z: '%s%s = %s pts (%d min)' % (z['nom'], '*' if z['remplace'] else '', z['points'], z['minutes'])
    print(r['poste'].ljust(18), f(r['dom']).ljust(52), '|', f(r['ext']))
ma = sum(r['dom']['points'] for r in rows) / len(rows); mb = sum(r['ext']['points'] for r in rows) / len(rows)
print('Moyenne XI :', round(ma, 1), '|', round(mb, 1))
json.dump({'dom': C['dom'], 'ext': C['ext'], 'lignes': rows, 'moyenneDom': round(ma, 1), 'moyenneExt': round(mb, 1)}, open(os.path.join(D, 'performance_' + re.sub(r'\W+', '_', C['dom']) + '__' + re.sub(r'\W+', '_', C['ext']) + '.json'), 'w'), ensure_ascii=False, indent=1)
