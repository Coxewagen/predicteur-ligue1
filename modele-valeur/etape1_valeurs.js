// Étape 1 du nouveau modèle : valeur de chaque équipe d'après ses joueurs.
// Données : valeurs Transfermarkt (M€) et minutes jouées de chaque joueur, relevées le 2026-11-01 (extraites de elo.html).
// Valeur d'équipe = somme des valeurs du XI type (1 G, 2 DC, 2 DL, 3 MI, 2 AT, 1 BU : titulaires habituels, à défaut les plus chers).
// Usage : node modele-valeur/etape1_valeurs.js   (écrit joueurs_2026-11-01.json et valeurs_equipes.json)
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'elo.html'), 'utf8');
const i = html.indexOf('const EMBED = '), j = html.indexOf('\n', i);
const E = JSON.parse(html.slice(i + 14, j).replace(/;\s*$/, ''));
const SLOTS = {G:1, DC:2, DL:2, MI:3, AT:2, BU:1};
function xi(sq){
  const out = [];
  Object.keys(SLOTS).forEach(function(g){
    const grp = sq.filter(function(p){ return p[1] === g; }).slice();
    if(g === 'G') grp.sort(function(a, b){ return (b[3] - a[3]) || (b[2] - a[2]); });
    else grp.sort(function(a, b){ return ((b[3] >= E.IMP.MINREG) - (a[3] >= E.IMP.MINREG)) || (b[2] - a[2]); });
    out.push.apply(out, grp.slice(0, SLOTS[g]));
  });
  return out;
}
const sum = function(a){ return a.reduce(function(s, p){ return s + p[2]; }, 0); };
const res = {};
Object.keys(E.SQUADS).forEach(function(t){
  const sq = E.SQUADS[t], x = xi(sq);
  res[t] = {valeurXI: Math.round(sum(x) * 10) / 10, valeurEffectif: Math.round(sum(sq) * 10) / 10, nbJoueurs: sq.length, xi: x.map(function(p){ return p[0] + ' (' + p[1] + ', ' + p[2] + ' M€)'; })};
});
const lnv = Object.keys(res).map(function(t){ return Math.log(res[t].valeurXI); });
const m = lnv.reduce(function(a, b){ return a + b; }, 0) / lnv.length;
Object.keys(res).forEach(function(t){ res[t].indexLn = Math.round((Math.log(res[t].valeurXI) - m) * 1000) / 1000; });
fs.writeFileSync(path.join(__dirname, 'joueurs_2026-11-01.json'), JSON.stringify(E.SQUADS));
fs.writeFileSync(path.join(__dirname, 'valeurs_equipes.json'), JSON.stringify({date: '2026-11-01', source: 'Transfermarkt (via elo.html)', equipes: res}, null, 1));
console.log(Object.keys(res).sort(function(a, b){ return res[b].valeurXI - res[a].valeurXI; }).map(function(t){ return t.padEnd(26) + String(res[t].valeurXI).padStart(7) + '  ' + String(res[t].valeurEffectif).padStart(7) + '  ' + res[t].indexLn; }).join('\n'));
