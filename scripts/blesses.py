"""Récupère la liste des joueurs blessés de Ligue 1 sur Transfermarkt et l'écrit dans blesses.json.
En cas d'échec (site bloqué, page vide), le fichier existant est conservé tel quel."""
import json, re, sys, time, unicodedata, datetime
import requests
from bs4 import BeautifulSoup

URL = "https://www.transfermarkt.fr/ligue-1/verletztespieler/wettbewerb/FR1"
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9"}
CLUBS = [('saint-germain','Paris Saint-Germain'),('paris fc','Paris FC'),('auxerre','AJ Auxerre'),('monaco','AS Monaco'),
         ('angers','Angers SCO'),('troyes','ES Troyes AC'),('lorient','FC Lorient'),('havre','Le Havre AC'),('le mans','Le Mans FC'),
         ('lens','RC Lens'),('lille','LOSC Lille'),('nice','OGC Nice'),('lyon','Olympique Lyonnais'),('marseille','Olympique de Marseille'),
         ('strasbourg','RC Strasbourg'),('rennes','Stade Rennais'),('rennais','Stade Rennais'),('brest','Stade Brestois'),('toulouse','Toulouse FC')]
DATE = re.compile(r'\d{1,2}\s+\S+\.?\s+\d{4}|\d{2}/\d{2}/\d{4}')

def canon(n):
    s = unicodedata.normalize('NFD', n).encode('ascii', 'ignore').decode().lower()
    for k, v in CLUBS:
        if k in s: return v
    return None

def page(n):
    url = URL + ("" if n == 1 else f"/page/{n}")
    r = requests.get(url, headers=HEAD, timeout=30)
    print(f"page {n}: HTTP {r.status_code}, {len(r.text)} octets")
    if r.status_code != 200: return None
    soup = BeautifulSoup(r.text, "html.parser")
    tab = soup.select_one("table.items")
    if not tab: return []
    out = []
    for tr in tab.select("tbody > tr"):
        if not (set(tr.get("class") or []) & {"odd", "even"}): continue
        a = tr.select_one("td.hauptlink a")
        if not a: continue
        name = a.get_text(strip=True)
        club = None
        for img in tr.select("img"):
            t = img.get("title") or img.get("alt") or ""
            if "wappen" in (img.get("src") or img.get("data-src") or "") and t:
                club = canon(t)
                if club: break
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td", recursive=False)]
        dates = [d for t in tds for d in DATE.findall(t)]
        injury = next((t for t in tds[1:] if t and t != name and not DATE.search(t) and not re.search(r'\d', t) and len(t) > 3 and canon(t) is None), "")
        out.append({"name": name, "club": club, "injury": injury, "dates": dates})
    return out

def main():
    rows, n = [], 1
    while n <= 8:
        p = page(n)
        if p is None: break
        if not p: break
        new = [x for x in p if (x["name"], x["club"]) not in {(y["name"], y["club"]) for y in rows}]
        if not new: break
        rows += new; n += 1; time.sleep(2)
    print(f"{len(rows)} blessés lus")
    if len(rows) < 10:
        print("Trop peu de lignes : on garde l'ancien fichier."); return 0
    teams = {}
    for x in rows:
        if not x["club"]: print("club inconnu :", x); continue
        teams.setdefault(x["club"], []).append({"name": x["name"], "injury": x["injury"],
                                                 "return": x["dates"][-1] if len(x["dates"]) > 1 else ""})
    data = {"updatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": URL, "count": len(rows), "teams": teams}
    try:
        old = json.load(open("blesses.json", encoding="utf-8"))
        if old.get("teams") == teams: print("Aucun changement."); return 0
    except Exception: pass
    json.dump(data, open("blesses.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for t, l in sorted(teams.items()): print(f"{t}: {', '.join(p['name'] for p in l)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
