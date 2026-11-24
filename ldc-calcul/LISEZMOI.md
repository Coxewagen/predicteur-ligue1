# Pronos LdC — reprise du projet (état au 24/11/2026, 00h30)

Hans (VTC, francophone) : prédicteur Ligue des champions, fichier `pronos-ldc-j4.html` + appli Android « Pronos LdC ».
Toutes les réponses en français. Règles de Hans : ne rien décider à sa place (lui demander avant), envoyer seulement les fichiers modifiés, .html en simple fichier téléchargeable (pas d'artefact), aucune légende/note/texte explicatif dans les pages (chiffres et noms seulement), grandes polices et fort contraste, cotes et boosts toujours modifiables à la main.

## Installation dans une nouvelle session
1. Dézipper dans `/home/claude/` : on obtient `/home/claude/ucl/` (scripts + données) et `/home/claude/work/` (model.py, data.py, parse.py : `from model import probs, gmult`).
2. Cloner `https://github.com/Coxewagen/predicteur-ligue1` dans `/home/claude/predicteur-ligue1` (`build.py` y publie `ldc.html`).
3. Installer numpy et scipy si absents (`pip install --break-system-packages numpy scipy`).
4. Testé : `python3 predict_j.py 5` et `python3 elo2.py` redonnent exactement les mêmes fichiers.
La clé The Odds API n'est PAS dans la copie GitHub (dépôt public) : elle est dans l'archive zip, `build.py`, variable `OKEY`.

## Modèle
- Elo (ClubElo 2026-09-01, mis à jour match par match, K=20 ; K=40 Shakhtar, Slavia, Slovan, Sabah) + Poisson/Dixon-Coles.
- λ_dom=exp(0.2435+C+0.2300·x), λ_ext=exp(0.2330+C−0.2212·x), x=(S·ΔElo+terrain)/100, S=0.84, C=0.12, RHO=+0.05. Avantage du terrain +56 pour tous (Shakhtar 15). Winamax exclu du calcul (W=1.0), cotes affichées pour info.
- Malus d'absences : ΔElo = max(−40, 97.6·ln(valeur_onze_avec_absents / valeur_onze_type)), valeurs Transfermarkt (`abs.json`, listes dans `absl.json`).
- Prono : « Victoire X » si le favori ≥ 60 %, sinon « X ou nul ». Cote minimale = 1/probabilité. Cote « Ou nul » estimée = 1.035/(1/cote_fav + 1/cote_nul).

## Fichiers clés (`/home/claude/ucl/`)
- `build.py` : génère `pronos-ldc-j4.html` (J1–J8) ET `/home/claude/predicteur-ligue1/ldc.html` (version appli, OKEY vidé), puis git pull --rebase / commit / push (`NO_PUSH=1` pour ne pas pousser). Les messages de commit finissent par les lignes d'attribution demandées par la session.
- `predict3.py` = J4 uniquement (NE PAS relancer : changerait les probas de J4). `predict_j.py N` = J5–J8 (lit `fixtures_jN.json`, écrit `preds_jN.json`).
- `fixtures_j5..j8.json` (18 matchs chacun), `ratings2.json` (Elo après J4), `ucl_res.csv` (résultats J1–J4, format `date;home;away;hs;as;0`), `elo2.py` (recalcule ratings2.json depuis ucl_res.csv), `allgames.json`/`allgames2.json` (matchs de championnat jusqu'au 01/11 seulement), `abs.json`, `absl.json`, `abs_tm.json`, `hfa_team.json`, `odds.json` (cotes J4 seulement, ne pas utiliser pour J5+), `tmvals.py`, `lineup.py` (lit les compos ESPN).
- `journal.py` + `journal.json` : `add [N]`, `res <fichier ESPN>`, `bilan`. Bilan J4 : 16/18 (9/9 mardi, 7/9 mercredi).
- Appli : `predicteur-ligue1/ldc-app.html` (coque Capacitor qui charge `ldc.html` depuis raw.githubusercontent à chaque ouverture, cache jusqu'à 5 min), workflow `.github/workflows/build-apk-ldc.yml`, icônes `android-icons-ldc/` (ballon bleu sur fond vert). Nouvelle page = pas de nouvelle APK ; APK seulement si icône/plugin changent. APK : https://github.com/Coxewagen/predicteur-ligue1/releases/download/apk-ldc-latest/pronos-ldc.apk
- Calendrier : J5 24–25/11, J6 8–9/12, J7 19–20/01/2027, J8 27/01/2027 (18 matchs à 21h00).

## Scores en direct (dans la page)
4 sources fusionnées, score le plus avancé gardé : UEFA `match.uefa.com/v5/matches?competitionId=1&fromDate=..&toDate=..`, LiveScore `prod-cdn-public-api.livescore.com/v1/api/app/date/soccer/YYYYMMDD/1`, FotMob `www.fotmob.com/api/data/matches?date=YYYYMMDD&timezone=Europe/Paris`, ESPN `site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard?dates=`. Rafraîchi toutes les 15 s. Sur PC (page ouverte depuis un fichier) UEFA et LiveScore sont bloqués par CORS : seuls ESPN et FotMob passent ; sur le téléphone tout passe. Retard d'environ 1 minute dû aux sources gratuites. Cliquer sur la ligne « Scores… » en haut envoie une notification test.

## Routine avant chaque journée (N = 5, 6, 7, 8)
1. Mettre à jour `abs.json` / `absl.json` avec les compos officielles (ESPN, rosters + `lineup.py`).
2. `cd /home/claude/ucl && python3 predict_j.py N && python3 build.py` (republie `ldc.html`).
3. Envoyer `pronos-ldc-j4.html` à Hans avec 2–3 lignes sur ce qui a changé.

## Routine après chaque journée
1. `python3 journal.py add N`, récupérer le scoreboard ESPN brut, `python3 journal.py res <fichier>`, `python3 journal.py bilan`, envoyer le bilan (court, en français : résultat par tranche, effet des absences).
2. Ajouter les résultats dans `ucl_res.csv`, relancer `python3 elo2.py` avant la journée suivante.

## À savoir / en suspens
- Les absences de J5–J8 sont encore celles de J4 (soir) : à refaire avec les compos.
- L'Elo ignore les championnats après le 01/11.
- Cotes Winamax de J5+ : « — » tant qu'elles ne sont pas saisies à la main ou fournies par The Odds API.
- Notifications seulement quand l'appli est ouverte (Hans n'en recevait aucune : le test via la ligne « Scores… » devait dire pourquoi, non vérifié).
- « En bonne voie » absent sur Liverpool : non élucidé, abandonné à sa demande.
- Possibles tests « enjeu » pour J7–J8 (janvier) ; valeurs Transfermarkt manquantes (Bodø, LASK, Slovan…).
- Question restée sans réponse : reprogrammer la vérification des compos pour la J5 ? NE PAS programmer sans son accord.
- GitHub : l'API GraphQL est indisponible dans la session ; utiliser `gh api repos/...` (REST) ou l'URL directe de la release.
