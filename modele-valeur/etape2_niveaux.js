// Étape 2 du nouveau modèle : valeur d'équipe -> niveau (points Elo).
// niveau = 1500 + C * (ln(valeur du XI) - moyenne des ln), C calibré par maximum de vraisemblance sur les 91 matchs J1->J11
// (avantage domicile 50 Elo et conversion Elo -> buts d'elo.html). Intervalle plausible à 90 % : 78 à 132.
// Usage : node modele-valeur/etape2_niveaux.js   (lit valeurs_equipes.json, écrit niveaux_equipes.json)
const fs = require('fs'), path = require('path');
const C = 106, H = 50;
const V = JSON.parse(fs.readFileSync(path.join(__dirname, 'valeurs_equipes.json'), 'utf8')).equipes;
const teams = Object.keys(V), m = teams.reduce(function(s, t){ return s + Math.log(V[t].valeurXI); }, 0) / teams.length;
const out = {};
teams.forEach(function(t){ out[t] = Math.round((1500 + C * (Math.log(V[t].valeurXI) - m)) * 10) / 10; });
fs.writeFileSync(path.join(__dirname, 'niveaux_equipes.json'), JSON.stringify({etape: 2, C: C, avantageDomicile: H, source: 'valeurs_equipes.json (valeur du XI type)', niveaux: out}, null, 1));
console.log(JSON.stringify(out, null, 1));
