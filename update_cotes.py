#!/usr/bin/env python3
"""Cotes Winamax 1 / N / 2 de la Ligue 1 -> cotes.json (affichage seulement).

Lit la page publique winamax.fr (« PRELOADED_STATE ») et écrit, pour chaque match à venir,
les cotes domicile / nul / extérieur. Ces cotes ne servent JAMAIS au calcul du modèle.
Ne casse rien : si la page est illisible, le fichier existant est laissé tel quel.

Usage :  python update_cotes.py [cotes.json] [--depuis-fichier page.html]
(Winamax refuse les adresses hors de France : à lancer depuis un PC en France, pas depuis GitHub Actions.
 L’appli Android lit Winamax elle-même ; cotes.json sert de relevé de secours pour le navigateur.)
"""
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    PARIS_TZ = ZoneInfo("Europe/Paris")
except Exception:  # pragma: no cover
    PARIS_TZ = None

URL = "https://www.winamax.fr/paris-sportifs/sports/1/7/4"   # Football > France > Ligue 1
LIGUE1_TOURNAMENT_ID = 4

# noms Winamax -> noms utilisés dans l'appli
NAMES = {
    "AJ Auxerre": "AJ Auxerre", "Auxerre": "AJ Auxerre",
    "AS Monaco": "AS Monaco", "Monaco": "AS Monaco",
    "Angers": "Angers SCO", "Angers SCO": "Angers SCO",
    "Brest": "Stade Brestois", "Stade Brestois": "Stade Brestois",
    "Le Havre": "Le Havre AC", "Le Havre AC": "Le Havre AC",
    "Le Mans": "Le Mans FC", "Le Mans FC": "Le Mans FC",
    "Lens": "RC Lens", "RC Lens": "RC Lens",
    "Lille": "LOSC Lille", "LOSC Lille": "LOSC Lille",
    "Lorient": "FC Lorient", "FC Lorient": "FC Lorient",
    "Lyon": "Olympique Lyonnais", "Olympique Lyonnais": "Olympique Lyonnais",
    "Marseille": "Olympique de Marseille", "Olympique de Marseille": "Olympique de Marseille",
    "Nice": "OGC Nice", "OGC Nice": "OGC Nice",
    "Paris FC": "Paris FC",
    "PSG": "Paris Saint-Germain", "Paris SG": "Paris Saint-Germain", "Paris Saint-Germain": "Paris Saint-Germain",
    "Rennes": "Stade Rennais", "Stade Rennais": "Stade Rennais",
    "Strasbourg": "RC Strasbourg", "RC Strasbourg": "RC Strasbourg",
    "Toulouse": "Toulouse FC", "Toulouse FC": "Toulouse FC",
    "Troyes": "ES Troyes AC", "ES Troyes AC": "ES Troyes AC",
}


def now_paris_iso():
    now = datetime.now(PARIS_TZ) if PARIS_TZ else datetime.now()
    return now.replace(tzinfo=None).isoformat(timespec="seconds")


def fetch_page():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "fr-FR,fr;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_odds(html):
    """-> {"Domicile|Extérieur": [cote1, coteN, cote2]} avec les noms de l'appli, et la liste des noms inconnus."""
    m = re.search(r"PRELOADED_STATE\s*=\s*", html)
    if not m:
        raise ValueError("PRELOADED_STATE introuvable (page changée ou bloquée ?)")
    state, _ = json.JSONDecoder().raw_decode(html[m.end():])
    matches, bets, outcomes, odds = state["matches"], state["bets"], state["outcomes"], state["odds"]
    out, unknown = {}, set()
    for mt in matches.values():
        if mt.get("tournamentId") != LIGUE1_TOURNAMENT_ID or not mt.get("mainBetId"):
            continue
        bet = bets.get(str(mt["mainBetId"]))
        if not bet or not bet.get("available", True):
            continue
        home_w, away_w = mt.get("competitor1Name"), mt.get("competitor2Name")
        if not home_w or not away_w:          # pari « vainqueur du championnat », etc.
            continue
        home, away = NAMES.get(home_w), NAMES.get(away_w)
        if not home or not away:
            unknown.update(n for n in (home_w, away_w) if n not in NAMES)
            continue
        cotes = [None, None, None]
        for oid in bet["outcomes"]:
            o = outcomes.get(str(oid)) or {}
            v = odds.get(str(oid))
            label = o.get("label")
            if label == "Match nul":
                cotes[1] = v
            elif label == home_w or NAMES.get(label) == home:      # « Paris SG » / « PSG » : même club
                cotes[0] = v
            elif label == away_w or NAMES.get(label) == away:
                cotes[2] = v
        if all(isinstance(c, (int, float)) and c > 1 for c in cotes):
            out[f"{home}|{away}"] = [round(float(c), 2) for c in cotes]
    return out, sorted(unknown)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    path = Path(args[0]) if args else Path("cotes.json")
    try:
        if "--depuis-fichier" in argv:
            html = Path(argv[argv.index("--depuis-fichier") + 1]).read_text(encoding="utf-8")
        else:
            html = fetch_page()
        odds, unknown = parse_odds(html)
    except Exception as e:  # jamais bloquant : on garde le fichier existant
        print(f"⚠️  Cotes Winamax : mise à jour ignorée ({type(e).__name__}: {e})")
        return 0
    if unknown:
        print("⚠️  Noms d'équipes Winamax inconnus (à ajouter dans NAMES) :", ", ".join(unknown))
    if not odds:
        print("⚠️  Cotes Winamax : aucun match lu, fichier inchangé.")
        return 0
    data = {"updatedAt": now_paris_iso(), "source": "winamax.fr", "odds": odds}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✅ Cotes Winamax : {len(odds)} match(s) écrits dans {path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
