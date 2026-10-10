# Prédicteur Ligue 1

Site : https://coxewagen.github.io/predicteur-ligue1/

## Mise à jour automatique

`update_stats.py` tourne tout seul toutes les 3h via GitHub Actions
(`.github/workflows/update.yml`) : classement, forme récente, repos/fatigue —
uniquement via l'API football-data.org, et seulement quand la journée en
cours est terminée (`--si-pret`, pas d'appel inutile sinon).

**Ce qu'il ne touche JAMAIS automatiquement** (pas de source API fiable pour
ça) : les absences (`absentAttackers`, `absentDefenders`, `gkOut`,
`keyPlayerOut`, `absenceReason`), `worldCupPlayers`, `newCoachBoostFrom`. Ces
champs sont relus et recollés tels quels à chaque mise à jour auto — mais
une correction d'absence reste toujours à faire à la main (via le chat, ou
en éditant `index.html` directement sur GitHub).

## Clé API

`FOOTBALL_DATA_API_KEY` doit être ajoutée en secret du repo (Settings →
Secrets and variables → Actions → New repository secret) pour que le
workflow tourne sans exposer la clé en clair. Sans ce secret, le script
retombe sur une clé codée en dur dans le fichier — à éviter sur un repo
public si tu peux l'ajouter en secret.
