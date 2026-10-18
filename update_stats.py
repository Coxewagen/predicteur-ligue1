#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Met à jour automatiquement les statistiques Ligue 1 dans predicteur-foot.html,
via l'API football-data.org (Ligue 1 incluse gratuitement, pour toujours).

CE QU'IL FAIT
--------------
1. Interroge l'API football-data.org pour récupérer le classement Ligue 1 à jour
   (matchs joués, buts marqués, buts encaissés, victoires), y compris les stats
   séparées à domicile / à l'extérieur quand elles sont disponibles.
2. Récupère les 5 derniers matchs de chaque club pour calculer une forme récente
   pondérée et détecter une série en cours (victoires, invincibilité, défaites).
3. Remplace le tableau `TEAMS` dans predicteur-foot.html, avec sauvegarde (.bak).

AVANT DE LANCER LE SCRIPT
--------------------------
1. pip install requests
2. Compte gratuit sur https://www.football-data.org/client/register
3. Colle ta clé API dans la variable API_KEY ci-dessous.

UTILISATION
-----------
    python update_stats.py                             # mise à jour complète (~2 min)
    python update_stats.py chemin/vers/fichier.html     # cible un fichier précis
    python update_stats.py --rapide                     # classement seulement, sans forme récente
    python update_stats.py --h2h "Equipe A" "Equipe B"  # confrontations directes de la saison
    python update_stats.py --forcer-journee 2           # écrase une journée 2 saisie manuellement avec les vraies données API

Une journée saisie manuellement dans l'appli (bouton "Copier le code") est
protégée automatiquement : une mise à jour normale ne l'écrasera jamais toute
seule. Utilise --forcer-journee si l'API a maintenant les bonnes données et
que tu veux remplacer ta saisie manuelle par celles-ci.

Tu peux relancer ce script chaque semaine, après une journée de Ligue 1.
"""

import os
import re
import sys
import json
import time
import shutil
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

try:
    import requests
except ImportError:
    print("La librairie 'requests' n'est pas installée.")
    print("Installe-la avec : pip install requests")
    sys.exit(1)

# ============================================================
# CONFIGURATION
# ============================================================

# Clé lue en priorité depuis la variable d'env FOOTBALL_DATA_API_KEY (c'est comme
# ça que le workflow GitHub Actions la fournit, via un secret du repo) ; la valeur
# codée en dur ci-dessous ne sert que de secours pour un lancement en local.
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "c86d040c5dc0496ebde91f82527c36e3")
COMPETITION_CODE = "FL1"  # FL1 = Ligue 1 (France)
DEFAULT_HTML_FILENAME = "predicteur-foot.html"

NAME_MAP = {
    "paris saint-germain": "Paris Saint-Germain",
    "lens":                "RC Lens",
    "lille":                "LOSC Lille",
    "lyonnais":             "Olympique Lyonnais",
    "marseille":            "Olympique de Marseille",
    "rennais":              "Stade Rennais",
    "monaco":               "AS Monaco",
    "strasbourg":           "RC Strasbourg",
    "lorient":              "FC Lorient",
    "toulouse":             "Toulouse FC",
    "paris fc":             "Paris FC",
    "brestois":             "Stade Brestois",
    "angers":               "Angers SCO",
    "havre":                "Le Havre AC",
    "auxerre":              "AJ Auxerre",
    "nice":                 "OGC Nice",
    "le mans":              "Le Mans FC",
    "troyes":               "ES Troyes AC",
}

# Clé de tri par ville (pas par nom officiel du club), pour un ordre alphabétique
# stable qui ne change jamais, quel que soit le classement du moment.
CITY_SORT_KEY = {
    "Angers SCO":             "Angers",
    "AJ Auxerre":             "Auxerre",
    "Stade Brestois":         "Brest",
    "Le Havre AC":            "Le Havre",
    "Le Mans FC":             "Le Mans",
    "RC Lens":                "Lens",
    "LOSC Lille":             "Lille",
    "FC Lorient":             "Lorient",
    "Olympique Lyonnais":     "Lyon",
    "Olympique de Marseille": "Marseille",
    "AS Monaco":              "Monaco",
    "OGC Nice":               "Nice",
    "Paris FC":               "Paris FC",
    "Paris Saint-Germain":    "Paris Saint-Germain",
    "Stade Rennais":          "Rennes",
    "RC Strasbourg":          "Strasbourg",
    "Toulouse FC":            "Toulouse",
    "ES Troyes AC":           "Troyes",
}


def sort_by_city(teams):
    return sorted(teams, key=lambda t: CITY_SORT_KEY.get(t["name"], t["name"]))


def resolve_team_name(api_name: str) -> str:
    lowered = api_name.lower()
    for key, nice_name in NAME_MAP.items():
        if key in lowered:
            return nice_name
    print(f"  ⚠️  Pas de correspondance pour '{api_name}' — ajoute-le à NAME_MAP si besoin.")
    return api_name


# ============================================================
# CLASSEMENT (TOTAL / HOME / AWAY)
# ============================================================

def fetch_standings():
    url = f"https://api.football-data.org/v4/competitions/{COMPETITION_CODE}/standings"
    headers = {"X-Auth-Token": API_KEY}

    print("Interrogation de football-data.org ...")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        sys.exit(1)

    if resp.status_code == 403:
        print("❌ Clé API refusée (403). Vérifie qu'elle est correcte et active.")
        sys.exit(1)
    if resp.status_code == 429:
        print("❌ Trop de requêtes envoyées (429). Attends une minute et réessaie.")
        sys.exit(1)
    if resp.status_code != 200:
        print(f"❌ Erreur API ({resp.status_code}) : {resp.text[:300]}")
        sys.exit(1)

    data = resp.json()
    try:
        standings_list = data["standings"]
    except KeyError:
        print("❌ Format de réponse inattendu de l'API.")
        print(json.dumps(data, indent=2)[:500])
        sys.exit(1)

    return standings_list, data


def build_teams(standings_list):
    by_type = {s["type"]: s["table"] for s in standings_list}
    total_table = by_type.get("TOTAL", [])
    home_table = by_type.get("HOME", [])
    away_table = by_type.get("AWAY", [])

    home_by_id = {row["team"]["id"]: row for row in home_table}
    away_by_id = {row["team"]["id"]: row for row in away_table}

    teams = []
    for row in total_table:
        api_name = row["team"]["name"]
        team_id = row["team"]["id"]
        played = row["playedGames"] or 0
        if played == 0:
            continue
        goals_for = row["goalsFor"]
        goals_against = row["goalsAgainst"]
        wins = row["won"]
        draws = row["draw"]

        entry = {
            "id": team_id,
            "name": resolve_team_name(api_name),
            "scored": round(goals_for / played, 3),
            "conceded": round(goals_against / played, 3),
            "form": round((wins / played) * 5, 2),
            "played": played,
            "wins": wins,
            "draws": draws,
            "goalsFor": goals_for,
            "goalsAgainst": goals_against,
        }

        hrow = home_by_id.get(team_id)
        if hrow and (hrow.get("playedGames") or 0) > 0:
            entry["homeScored"] = round(hrow["goalsFor"] / hrow["playedGames"], 3)
            entry["homeConceded"] = round(hrow["goalsAgainst"] / hrow["playedGames"], 3)

        arow = away_by_id.get(team_id)
        if arow and (arow.get("playedGames") or 0) > 0:
            entry["awayScored"] = round(arow["goalsFor"] / arow["playedGames"], 3)
            entry["awayConceded"] = round(arow["goalsAgainst"] / arow["playedGames"], 3)

        teams.append(entry)
    return teams


# ============================================================
# FORME RÉCENTE (5 DERNIERS MATCHS) + SÉRIE
# ============================================================

def fetch_team_recent_matches(team_id: int):
    """Récupère les matchs terminés d'une équipe, TOUTES compétitions confondues
    (championnat + coupes + Europe). Ça permet de calculer à la fois la forme
    domestique (filtrée sur Ligue 1 ensuite) et le repos/fatigue (qui doit lui
    tenir compte de TOUTES les compétitions) à partir d'un seul appel API."""
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
    params = {"status": "FINISHED"}
    headers = {"X-Auth-Token": API_KEY}
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    if resp.status_code != 200:
        return []
    matches = resp.json().get("matches", [])
    matches.sort(key=lambda m: m.get("utcDate", ""), reverse=True)
    return matches


def is_domestic_league_match(match: dict) -> bool:
    comp = match.get("competition", {}) or {}
    return comp.get("code") == COMPETITION_CODE


def match_result_for(match: dict, team_id: int):
    home = match.get("homeTeam", {}) or {}
    away = match.get("awayTeam", {}) or {}
    score = match.get("score", {}) or {}
    ft = score.get("fullTime") or score.get("regularTime") or {}
    gh, ga = ft.get("home"), ft.get("away")
    if gh is None or ga is None:
        return None
    is_home = home.get("id") == team_id
    team_goals = gh if is_home else ga
    opp_goals = ga if is_home else gh
    if team_goals > opp_goals:
        return "W"
    if team_goals == opp_goals:
        return "D"
    return "L"


def opponent_id(match: dict, team_id: int):
    home = match.get("homeTeam", {}) or {}
    away = match.get("awayTeam", {}) or {}
    return away.get("id") if home.get("id") == team_id else home.get("id")


def compute_recent_form_and_streak(matches, team_id: int):
    domestic_matches = [m for m in matches if is_domestic_league_match(m)]
    results = [r for r in (match_result_for(m, team_id) for m in domestic_matches) if r]
    if not results:
        return None

    last5 = results[:5]
    recent_form = last5.count("W")

    first = results[0]
    streak_len = 0
    if first == "W":
        streak_type = "win"
        for r in results:
            if r == "W":
                streak_len += 1
            else:
                break
    elif first == "L":
        streak_type = "lose"
        for r in results:
            if r == "L":
                streak_len += 1
            else:
                break
    else:
        streak_type = "unbeaten"
        for r in results:
            if r != "L":
                streak_len += 1
            else:
                break

    return {
        "recentForm": round(recent_form, 1),
        "streakType": streak_type,
        "streakLen": min(streak_len, 10),
    }


CL_CODES = {"CL", "UCL"}
EL_CODES = {"EL", "UEL"}
UECL_CODES = {"UECL"}
CL_KEYWORDS = ("champions league",)
EL_KEYWORDS = ("europa league",)
UECL_KEYWORDS = ("conference league",)


def compute_fatigue(matches, updated_at: datetime):
    """Repos et fatigue basés sur le tout dernier match joué, TOUTES compétitions
    confondues (le championnat seul ne suffit pas : une équipe peut être fatiguée
    par un match européen même si son dernier match de Ligue 1 remonte à une semaine).
    Le niveau de la compétition européenne (C1 > EL > Conference) est distingué,
    la C1 étant généralement plus exigeante (adversaires, trajets, enjeu)."""
    if not matches:
        return None
    last = matches[0]  # déjà trié du plus récent au plus ancien
    last_date_str = last.get("utcDate")
    if not last_date_str:
        return None
    try:
        last_date = datetime.fromisoformat(last_date_str.replace("Z", "+00:00"))
    except ValueError:
        return None

    now = updated_at
    if last_date.tzinfo and now.tzinfo is None:
        now = now.astimezone()
    rest_days = max((now - last_date).days, 0)

    comp = last.get("competition", {}) or {}
    comp_code = (comp.get("code") or "").upper()
    comp_name = (comp.get("name") or "").lower()

    europe_level = None
    if comp_code in CL_CODES or any(k in comp_name for k in CL_KEYWORDS):
        europe_level = "CL"
    elif comp_code in EL_CODES or any(k in comp_name for k in EL_KEYWORDS):
        europe_level = "EL"
    elif comp_code in UECL_CODES or any(k in comp_name for k in UECL_KEYWORDS):
        europe_level = "UECL"

    return {"restDays": rest_days, "playedEurope": europe_level is not None, "europeLevel": europe_level}


def add_recent_form(teams):
    print("\nRécupération de la forme récente (5 derniers matchs) et du repos pour chaque club...")
    print("(respecte la limite de requêtes de l'API gratuite, ~2 minutes au total)")
    now = datetime.now().astimezone()
    for idx, t in enumerate(teams):
        matches = fetch_team_recent_matches(t["id"])

        info = compute_recent_form_and_streak(matches, t["id"])
        if info:
            t.update(info)
            print(f"  [{idx+1}/{len(teams)}] {t['name']:<28} forme récente: {info['recentForm']}/5  "
                  f"série: {info['streakType']} ({info['streakLen']})")
        else:
            print(f"  [{idx+1}/{len(teams)}] {t['name']:<28} pas assez de matchs pour la forme récente")

        fatigue = compute_fatigue(matches, now)
        if fatigue:
            t.update(fatigue)
            europe_note = " [a joué en Coupe d'Europe]" if fatigue["playedEurope"] else ""
            print(f"      repos : {fatigue['restDays']} jour(s){europe_note}")

        if idx < len(teams) - 1:
            time.sleep(7)  # marge de sécurité sous la limite de 10 requêtes/minute
    return teams


# ============================================================
# CONFRONTATIONS DIRECTES
# ============================================================

def find_team_by_name(teams, name: str):
    name_l = name.lower().strip()
    for t in teams:
        if t["name"].lower() == name_l:
            return t
    for t in teams:
        if name_l in t["name"].lower() or t["name"].lower() in name_l:
            return t
    return None


def run_h2h_report(teams, name1: str, name2: str):
    t1 = find_team_by_name(teams, name1)
    t2 = find_team_by_name(teams, name2)
    if not t1 or not t2:
        missing = name1 if not t1 else name2
        print(f"❌ Équipe introuvable dans le classement actuel : '{missing}'")
        print("   Vérifie l'orthographe, ou lance une mise à jour complète d'abord.")
        return

    print(f"\nRecherche des confrontations {t1['name']} vs {t2['name']} cette saison...")
    matches = fetch_team_recent_matches(t1["id"])
    h2h = [m for m in matches if opponent_id(m, t1["id"]) == t2["id"]]

    if not h2h:
        print(f"Aucune confrontation trouvée cette saison entre {t1['name']} et {t2['name']} (pour l'instant).")
        return

    wins = draws = losses = 0
    for m in h2h:
        r = match_result_for(m, t1["id"])
        if r == "W":
            wins += 1
        elif r == "D":
            draws += 1
        elif r == "L":
            losses += 1

    print(f"\nConfrontations cette saison ({len(h2h)}) : "
          f"{wins}V {draws}N {losses}D pour {t1['name']} (face à {t2['name']})")
    for m in h2h:
        date = (m.get("utcDate") or "")[:10]
        ft = (m.get("score", {}) or {}).get("fullTime", {}) or {}
        home_name = (m.get("homeTeam") or {}).get("name", "?")
        away_name = (m.get("awayTeam") or {}).get("name", "?")
        print(f"  - {date} : {home_name} {ft.get('home','?')} - {ft.get('away','?')} {away_name}")


# ============================================================
# ÉCRITURE DANS LE FICHIER HTML
# ============================================================

# Champs saisis/corrigés à la main (absences, Coupe du Monde, bonus nouveau coach)
# qui ne viennent PAS de l'API football-data.org : une mise à jour automatique des
# stats ne doit jamais les écraser. On les relit dans le fichier existant avant de
# régénérer TEAMS, et on les recolle sur l'équipe correspondante (par nom).
PRESERVE_KEYS_STR = ["absenceReason", "absenceUpdatedAt"]
PRESERVE_KEYS_RAW = ["absentAttackers", "absentDefenders", "gkOut", "keyPlayerOut",
                     "worldCupPlayers", "newCoachBoostFrom"]


def parse_preserved_fields(html_path: Path) -> dict:
    """Relit le TEAMS actuel du fichier et renvoie, par nom d'équipe, les champs
    manuels à préserver. Les objets TEAMS sont plats (pas d'accolades imbriquées),
    donc un découpage par { ... } top-level suffit."""
    try:
        content = html_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.search(r"let TEAMS = \[(.*?)\];", content, re.DOTALL)
    if not m:
        return {}
    out = {}
    for obj in re.findall(r"\{([^{}]*)\}", m.group(1)):
        name_m = re.search(r'name:"((?:[^"\\]|\\.)*)"', obj)
        if not name_m:
            continue
        extra = {}
        for key in PRESERVE_KEYS_STR:
            vm = re.search(rf'{key}:"((?:[^"\\]|\\.)*)"', obj)
            if vm:
                extra[key] = vm.group(1).replace('\\"', '"').replace("\\\\", "\\")
        for key in PRESERVE_KEYS_RAW:
            vm = re.search(rf'{key}:\s*([A-Za-z0-9_.+-]+)', obj)
            if not vm:
                continue
            v = vm.group(1)
            if v == "true": extra[key] = True
            elif v == "false": extra[key] = False
            else:
                try: extra[key] = int(v)
                except ValueError:
                    try: extra[key] = float(v)
                    except ValueError: pass
        out[name_m.group(1)] = extra
    return out


def teams_to_js(teams, preserved=None):
    preserved = preserved or {}
    lines = ["let TEAMS = ["]
    for t in teams:
        parts = [
            f'id:{t["id"]}',
            f'name:"{t["name"]}"',
            f'scored:{t["scored"]}',
            f'conceded:{t["conceded"]}',
            f'form:{t["form"]}',
            f'played:{t["played"]}',
            f'wins:{t["wins"]}',
            f'draws:{t.get("draws", 0)}',
            f'goalsFor:{t["goalsFor"]}',
            f'goalsAgainst:{t["goalsAgainst"]}',
        ]
        if "homeScored" in t:
            parts.append(f'homeScored:{t["homeScored"]}')
            parts.append(f'homeConceded:{t["homeConceded"]}')
        if "awayScored" in t:
            parts.append(f'awayScored:{t["awayScored"]}')
            parts.append(f'awayConceded:{t["awayConceded"]}')
        if "recentForm" in t:
            parts.append(f'recentForm:{t["recentForm"]}')
            parts.append(f'streakType:"{t["streakType"]}"')
            parts.append(f'streakLen:{t["streakLen"]}')
        if "restDays" in t:
            parts.append(f'restDays:{t["restDays"]}')
            parts.append('playedEurope:' + ("true" if t.get("playedEurope") else "false"))
            europe_level = t.get("europeLevel")
            parts.append('europeLevel:' + (f'"{europe_level}"' if europe_level else 'null'))

        extra = preserved.get(t["name"], {})
        if "worldCupPlayers" in extra:
            parts.append(f'worldCupPlayers:{extra["worldCupPlayers"]}')
        if any(k in extra for k in ("absentAttackers", "absentDefenders", "gkOut", "keyPlayerOut")):
            parts.append(f'absentAttackers:{extra.get("absentAttackers", 0)}')
            parts.append(f'absentDefenders:{extra.get("absentDefenders", 0)}')
            parts.append('gkOut:' + ("true" if extra.get("gkOut") else "false"))
            parts.append('keyPlayerOut:' + ("true" if extra.get("keyPlayerOut") else "false"))
            parts.append(f'absenceReason:{json.dumps(extra.get("absenceReason", ""), ensure_ascii=False)}')
            if "absenceUpdatedAt" in extra:
                parts.append(f'absenceUpdatedAt:{json.dumps(extra["absenceUpdatedAt"], ensure_ascii=False)}')
        if "newCoachBoostFrom" in extra:
            parts.append(f'newCoachBoostFrom:{extra["newCoachBoostFrom"]}')

        lines.append("  { " + ", ".join(parts) + " },")
    lines.append("];")
    return "\n".join(lines)


def fetch_matchday_results(matchday):
    """Récupère les matchs (joués ou à venir) de la journée en cours."""
    url = f"https://api.football-data.org/v4/competitions/{COMPETITION_CODE}/matches"
    params = {"matchday": matchday}
    headers = {"X-Auth-Token": API_KEY}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.RequestException:
        return [], None
    if resp.status_code != 200:
        return [], None
    raw = resp.json()
    matches = raw.get("matches", [])

    results = []
    for m in matches:
        home_name = resolve_team_name(m.get("homeTeam", {}).get("name", "?"))
        away_name = resolve_team_name(m.get("awayTeam", {}).get("name", "?"))
        ft = (m.get("score", {}) or {}).get("fullTime", {}) or {}
        # on se fie à la présence d'un score plutôt qu'au champ 'status', qui peut
        # rester en retard par rapport au classement sur certaines réponses de l'API
        played = ft.get("home") is not None and ft.get("away") is not None
        results.append({
            "home": home_name,
            "away": away_name,
            "homeScore": ft.get("home") if played else None,
            "awayScore": ft.get("away") if played else None,
            "played": played,
        })
    return results, raw


def read_matchday_history(html_path: Path) -> dict:
    """Lit l'historique déjà présent dans le fichier HTML (MATCHDAY_HISTORY),
    pour y ajouter la nouvelle journée sans écraser les précédentes."""
    try:
        content = html_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.search(r"let MATCHDAY_HISTORY = (\{.*?\});", content, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def history_to_js(history: dict) -> str:
    return "let MATCHDAY_HISTORY = " + json.dumps(history, indent=2, ensure_ascii=False) + ";"


def last_update_to_js(matchday, updated_at_iso, note=""):
    note_js = json.dumps(note, ensure_ascii=False) if note else '""'
    return (f'let LAST_UPDATE = {{ matchday: {matchday}, '
            f'updatedAt: "{updated_at_iso}", note: {note_js} }};')


def update_history_only(html_path: Path, matchday, results):
    """Écrit uniquement les résultats connus dans MATCHDAY_HISTORY, SANS toucher
    TEAMS ni LAST_UPDATE. Utilisé quand la journée n'est pas encore terminée,
    pour afficher les scores des matchs déjà joués sans fausser le classement/
    la forme (qui, eux, attendent la fin complète de la journée)."""
    content = html_path.read_text(encoding="utf-8")
    history_pattern = re.compile(r"let MATCHDAY_HISTORY = \{.*?\};", re.DOTALL)

    history = read_matchday_history(html_path)
    existing = history.get(str(matchday))
    existing_is_manual = bool(existing) and any(r.get("source") == "manual" for r in existing)
    if existing_is_manual:
        print(f"⚠️  Journée {matchday} avait été saisie manuellement — résultats partiels NON écrasés.")
        return

    history[str(matchday)] = results
    new_history_block = history_to_js(history)
    if history_pattern.search(content):
        new_content = history_pattern.sub(new_history_block, content, count=1)
    else:
        new_content = content.replace("let TEAMS = [", new_history_block + "\n\nlet TEAMS = [", 1)

    backup_path = html_path.with_suffix(html_path.suffix + ".bak")
    shutil.copy2(html_path, backup_path)
    html_path.write_text(new_content, encoding="utf-8")
    played_count = sum(1 for r in results if r["played"])
    print(f"✅ Résultats partiels de la journée {matchday} enregistrés "
          f"({played_count}/{len(results)} joués) — classement/forme pas encore "
          f"recalculés (journée pas terminée).")


def update_html_file(html_path: Path, teams, matchday, updated_at_iso, note="", results=None, force=False):
    content = html_path.read_text(encoding="utf-8")

    teams_pattern = re.compile(r"let TEAMS = \[.*?\];", re.DOTALL)
    if not teams_pattern.search(content):
        print(f"❌ Impossible de trouver le tableau 'TEAMS' dans {html_path}.")
        sys.exit(1)

    update_pattern = re.compile(r"let LAST_UPDATE = \{.*?\};", re.DOTALL)
    history_pattern = re.compile(r"let MATCHDAY_HISTORY = \{.*?\};", re.DOTALL)

    preserved = parse_preserved_fields(html_path)
    if preserved:
        n_abs = sum(1 for v in preserved.values()
                    if any(k in v for k in ("absentAttackers", "absentDefenders", "gkOut", "keyPlayerOut")))
        print(f"   Champs manuels préservés (absences/WC/nouveau coach) pour {len(preserved)} équipe(s), "
              f"dont {n_abs} avec une absence enregistrée.")
    new_content = teams_pattern.sub(teams_to_js(teams, preserved), content, count=1)

    new_update_block = last_update_to_js(matchday, updated_at_iso, note)
    if update_pattern.search(new_content):
        new_content = update_pattern.sub(new_update_block, new_content, count=1)
    else:
        new_content = new_content.replace("let TEAMS = [", new_update_block + "\n\nlet TEAMS = [", 1)

    if results:
        history = read_matchday_history(html_path)
        existing = history.get(str(matchday))
        existing_is_manual = bool(existing) and any(r.get("source") == "manual" for r in existing)

        if existing_is_manual and not force:
            print(f"⚠️  Journée {matchday} avait été saisie manuellement — NON écrasée automatiquement,")
            print(f"   pour ne pas perdre ta saisie. Si l'API a maintenant raison et que tu veux la")
            print(f"   remplacer, relance avec : python update_stats.py --forcer-journee {matchday}")
        else:
            history[str(matchday)] = results  # écrase seulement l'entrée de CETTE journée, garde les autres
            new_history_block = history_to_js(history)
            if history_pattern.search(new_content):
                new_content = history_pattern.sub(new_history_block, new_content, count=1)
            else:
                new_content = new_content.replace(
                    "let TEAMS = [", new_history_block + "\n\nlet TEAMS = [", 1
                )
            print(f"   Historique : {len(history)} journée(s) au total ({', '.join(sorted(history, key=int))}).")

    backup_path = html_path.with_suffix(html_path.suffix + ".bak")
    shutil.copy2(html_path, backup_path)

    html_path.write_text(new_content, encoding="utf-8")
    print(f"✅ Fichier mis à jour : {html_path}")
    print(f"   (sauvegarde de l'ancienne version : {backup_path})")


# ============================================================
# ============================================================
# MISE À JOUR COMPLÈTE (réutilisée par le mode normal et --si-pret)
# ============================================================

def run_full_update(html_path: Path, quick: bool, prefetched=None, force_matchday=None):
    """prefetched (optionnel) = (standings_list, raw_data, matchday, results, raw_matches),
    déjà récupérés par run_if_ready — évite de rappeler l'API pour rien.
    force_matchday : si renseigné et égal à la journée en cours, écrase même une
    entrée saisie manuellement (protection normalement active par défaut)."""
    if prefetched:
        standings_list, raw_data, matchday, results, raw_matches = prefetched
    else:
        standings_list, raw_data = fetch_standings()
        matchday = (raw_data.get("season") or {}).get("currentMatchday", "?")
        results, raw_matches = fetch_matchday_results(matchday) if isinstance(matchday, int) else ([], None)

    teams = build_teams(standings_list)
    teams = sort_by_city(teams)

    if len(teams) < 10:
        debug_path = html_path.parent / "debug_reponse_api.json"
        debug_path.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"❌ Seulement {len(teams)} équipes récupérées, mise à jour annulée par sécurité.")
        print(f"   Détail de la réponse de l'API enregistré dans : {debug_path}")
        print("   Ouvre ce fichier (ou envoie-le) pour comprendre pourquoi.")
        sys.exit(1)

    has_split = sum(1 for t in teams if "homeScored" in t)
    print(f"\n{len(teams)} équipes récupérées ({has_split} avec stats domicile/extérieur séparées) :")
    for t in teams:
        split_note = " [dom/ext OK]" if "homeScored" in t else ""
        print(f"  - {t['name']:<28} buts marqués/m: {t['scored']:.2f}  "
              f"encaissés/m: {t['conceded']:.2f}  forme: {t['form']:.1f}/5{split_note}")

    if quick:
        print("\n(Mode --rapide : forme récente sur 5 matchs non recalculée cette fois.)")
    else:
        teams = add_recent_form(teams)

    note = ""
    if len(teams) < 18:
        note = f"{len(teams)}/18 clubs ont des données (les autres n'ont pas encore joué)"

    if raw_matches is not None:
        debug_matches_path = html_path.parent / "debug_matches_api.json"
        debug_matches_path.write_text(json.dumps(raw_matches, indent=2, ensure_ascii=False), encoding="utf-8")

    played_count = sum(1 for r in results if r["played"])
    print(f"\n{played_count}/{len(results)} match(s) de la journée {matchday} marqués comme joués par l'API.")

    force = (force_matchday is not None and force_matchday == matchday)
    update_html_file(html_path, teams, matchday, datetime.now().isoformat(timespec="seconds"), note, results, force=force)
    print(f"\nTerminé — {datetime.now().strftime('%d/%m/%Y à %H:%M')}")


def read_current_matchday(html_path: Path):
    """Lit le numéro de journée déjà enregistré dans le fichier HTML (LAST_UPDATE),
    pour éviter de refaire une mise à jour complète si c'est déjà à jour."""
    try:
        content = html_path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"let LAST_UPDATE = \{\s*matchday:\s*(\d+)", content)
    return int(m.group(1)) if m else None


def run_if_ready(html_path: Path, quick: bool, force_matchday=None):
    """Ne met à jour que si la journée en cours est terminée côté API (tous les
    matchs ont un score). Sinon, ne fait rien et se termine silencieusement —
    pensé pour être lancé plusieurs fois par jour par une tâche planifiée, sans
    dépendre d'une heure fixe devinée à l'avance.
    Coût : 2 requêtes API par vérification (peu importe le résultat)."""
    print("Vérification de l'état de la journée en cours...")
    standings_list, raw_data = fetch_standings()
    matchday = (raw_data.get("season") or {}).get("currentMatchday", None)

    if not isinstance(matchday, int):
        print("Impossible de déterminer la journée en cours — abandon (rien modifié).")
        return

    results, raw_matches = fetch_matchday_results(matchday)
    if not results:
        print(f"Aucun match trouvé pour la journée {matchday} — abandon (rien modifié).")
        return

    played_count = sum(1 for r in results if r["played"])
    total = len(results)
    print(f"Journée {matchday} : {played_count}/{total} match(s) joués côté API.")

    if played_count < total:
        print("La journée n'est pas encore terminée — mise à jour des résultats connus "
              "uniquement (classement/forme pas recalculés avant la fin de la journée).")
        update_history_only(html_path, matchday, results)
        return

    forcing_this_matchday = (force_matchday is not None and force_matchday == matchday)
    already_done = read_current_matchday(html_path)
    if already_done == matchday and not forcing_this_matchday:
        print(f"Journée {matchday} déjà enregistrée dans le fichier.")
        # L'API peut garder "journée en cours = N" alors que la journée N+1 a déjà
        # commencé (matchs du vendredi/samedi) : on regarde si elle a déjà des scores
        # pour ne pas rater ses résultats (1 requête de plus, seulement dans ce cas).
        nxt = matchday + 1
        if nxt <= 34:
            next_results, next_raw = fetch_matchday_results(nxt)
            next_played = sum(1 for r in next_results if r["played"])
            if next_played == 0:
                print("Journée suivante pas encore commencée — rien à refaire, on économise des requêtes.")
            elif next_played < len(next_results):
                print(f"Journée {nxt} déjà commencée côté API ({next_played}/{len(next_results)} joués, "
                      f"alors que 'journée en cours' = {matchday}) — enregistrement des résultats connus.")
                update_history_only(html_path, nxt, next_results)
            else:
                print(f"Journée {nxt} complète côté API (alors que 'journée en cours' = {matchday}) — mise à jour complète.")
                run_full_update(html_path, quick, prefetched=(standings_list, raw_data, nxt, next_results, next_raw))
        return

    print("Journée complète ✅ — lancement de la mise à jour (sans rappeler l'API pour le classement/matchs)...")
    run_full_update(html_path, quick, prefetched=(standings_list, raw_data, matchday, results, raw_matches), force_matchday=force_matchday)


# ============================================================
# MAIN
# ============================================================

def main():
    args = sys.argv[1:]

    if "--h2h" in args:
        idx = args.index("--h2h")
        try:
            name1, name2 = args[idx + 1], args[idx + 2]
        except IndexError:
            print('Usage : python update_stats.py --h2h "Equipe 1" "Equipe 2"')
            sys.exit(1)
        standings_list, _ = fetch_standings()
        teams = build_teams(standings_list)
        run_h2h_report(teams, name1, name2)
        return

    force_matchday = None
    if "--forcer-journee" in args:
        idx = args.index("--forcer-journee")
        try:
            force_matchday = int(args[idx + 1])
        except (IndexError, ValueError):
            print('Usage : python update_stats.py --forcer-journee 2')
            sys.exit(1)

    quick = "--rapide" in args
    # on retire les flags (et leur valeur) avant de chercher le nom de fichier positionnel
    skip_next = False
    positional = []
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a == "--forcer-journee":
            skip_next = True
            continue
        if not a.startswith("--"):
            positional.append(a)
    html_arg = positional[0] if positional else DEFAULT_HTML_FILENAME
    html_path = Path(html_arg)

    if not html_path.exists():
        print(f"❌ Fichier introuvable : {html_path}")
        print("   Lance le script depuis le dossier contenant predicteur-foot.html,")
        print("   ou passe le chemin en argument : python update_stats.py chemin/fichier.html")
        sys.exit(1)

    if "--si-pret" in args:
        run_if_ready(html_path, quick, force_matchday=force_matchday)
        return

    run_full_update(html_path, quick, force_matchday=force_matchday)


if __name__ == "__main__":
    main()
