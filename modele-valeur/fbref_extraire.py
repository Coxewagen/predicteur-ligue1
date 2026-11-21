# Extrait les stats joueurs de Ligue 1 2026/27 depuis les pages FBref (standard, tirs, divers) copiées en markdown, + la table des gardiens.
# Usage : python3 -I modele-valeur/fbref_extraire.py <dossier avec fb_std.md fb_shoot.md fb_misc.md gardiens.txt> <date>
# Écrit modele-valeur/stats_joueurs_<date>.json
import json, re, sys, os
d, date = sys.argv[1], sys.argv[2]
def cell(c):
    c = c.strip(); m = re.match(r'^\[([^\]]*)\]\([^)]*\)$', c)
    return m.group(1) if m else c
def table(fn):
    rows, hdr = [], None
    for l in open(os.path.join(d, fn), encoding='utf-8').read().split('\n'):
        if not l.startswith('|'): continue
        c = [cell(x) for x in l.strip().strip('|').split('|')]
        if c[0] == 'Rk' and 'Player' in c: hdr = c; continue
        if hdr and re.match(r'^\d+$', c[0]) and len(c) == len(hdr): 
            r = {}
            for h, v in zip(hdr, c):
                if h not in r: r[h] = v   # colonnes en double (totaux puis par 90 min) : on garde la première
            rows.append(r)
    return rows
def num(x):
    try: return float(x)
    except: return 0.0
P = {}
for r in table('fb_std.md'):
    k = (r['Player'], r['Squad'])
    P[k] = {'nom': r['Player'], 'equipe': r['Squad'], 'poste': r['Pos'], 'matchs': int(num(r['MP'])), 'titularisations': int(num(r['Starts'])), 'min': int(num(r['Min'])), 'n90': num(r['90s']), 'buts': int(num(r['Gls'])), 'passes': int(num(r['Ast'])), 'butsHorsPen': int(num(r['G-PK'])), 'jaunes': int(num(r['CrdY'])), 'rouges': int(num(r['CrdR']))}
for r in table('fb_shoot.md'):
    k = (r['Player'], r['Squad'])
    if k in P: P[k]['tirs'] = int(num(r['Sh'])); P[k]['cadres'] = int(num(r['SoT']))
for r in table('fb_misc.md'):
    k = (r['Player'], r['Squad'])
    if k in P: P[k]['tacles'] = int(num(r['TklW'])); P[k]['interceptions'] = int(num(r['Int']))
G = []
for l in open(os.path.join(d, 'gardiens.txt'), encoding='utf-8'):
    n, e, m, s, sv = l.strip().split('|'); G.append({'nom': n, 'equipe': e, 'min': int(m), 'n90': int(m) / 90, 'tirsCadresSubis': int(s), 'arrets': int(sv)})
out = {'date': date, 'source': 'fbref.com Ligue 1 2026-2027 (standard, shooting, misc, goalkeeping), mise à jour FBref 21-nov 06h25', 'joueurs': list(P.values()), 'gardiens': G}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats_joueurs_' + date + '.json'), 'w'), ensure_ascii=False, indent=0)
print(len(P), 'joueurs,', len(G), 'gardiens ; sans tirs:', sum(1 for v in P.values() if 'tirs' not in v), 'sans misc:', sum(1 for v in P.values() if 'tacles' not in v))
