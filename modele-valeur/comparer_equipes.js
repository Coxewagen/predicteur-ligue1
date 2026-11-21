// Compare deux équipes joueur par joueur : XI type, absences du jour, remplaçants, valeur (M€) face à face poste par poste.
// Usage : node modele-valeur/comparer_equipes.js "OGC Nice" "Paris Saint-Germain"   (domicile en premier ; écrit comparaison_<dom>_<ext>.json)
const fs = require('fs'), path = require('path');
const dom = process.argv[2] || 'OGC Nice', ext = process.argv[3] || 'Paris Saint-Germain';
const SQ = JSON.parse(fs.readFileSync(path.join(__dirname, 'joueurs_2026-11-01.json'), 'utf8'));
const AB = JSON.parse(fs.readFileSync(path.join(__dirname, 'absences_actuelles.json'), 'utf8')).equipes;
const NIV = JSON.parse(fs.readFileSync(path.join(__dirname, 'niveaux_actuels.json'), 'utf8')).niveaux;
const DOM = JSON.parse(fs.readFileSync(path.join(__dirname, 'domicile_equipes.json'), 'utf8')).equipes;
const SLOTS = {G: 1, DC: 2, DL: 2, MI: 3, AT: 2, BU: 1}, MINREG = 150;
function xiOf(sq){ const XI = []; Object.keys(SLOTS).forEach(function(g){ const grp = sq.filter(function(p){ return p[1] === g; }).slice(); if (g === 'G') grp.sort(function(x, y){ return (y[3] - x[3]) || (y[2] - x[2]); }); else grp.sort(function(x, y){ return ((y[3] >= MINREG) - (x[3] >= MINREG)) || (y[2] - x[2]); }); XI.push.apply(XI, grp.slice(0, SLOTS[g])); }); return XI; }
function lineup(t){
  const sq = SQ[t], ab = AB[t], rep = {}; ab.absentsXI.forEach(function(x){ rep[x.joueur] = x; });
  const rows = {}; Object.keys(SLOTS).forEach(function(g){ rows[g] = []; });
  xiOf(sq).forEach(function(p){
    const r = rep[p[0]];
    if (!r) rows[p[1]].push({nom: p[0], poste: p[1], valeur: p[2], absentRemplace: null});
    else { const q = r.remplacant ? sq.find(function(z){ return z[0] === r.remplacant; }) : null; rows[p[1]].push({nom: q ? q[0] : '(personne)', poste: q ? q[1] : p[1], valeur: q ? q[2] : 0, absentRemplace: p[0] + ' (' + p[2] + ' M€)'}); }
  });
  Object.keys(rows).forEach(function(g){ rows[g].sort(function(a, b){ return b.valeur - a.valeur; }); });
  return {rows: rows, tot: Object.keys(rows).reduce(function(s, g){ return s + rows[g].reduce(function(z, p){ return z + p.valeur; }, 0); }, 0)};
}
const A = lineup(dom), B = lineup(ext), lines = [];
Object.keys(SLOTS).forEach(function(g){ for (let k = 0; k < SLOTS[g]; k++){ const a = A.rows[g][k], b = B.rows[g][k]; lines.push({poste: g, dom: a, ext: b, ecart: Math.round((b.valeur - a.valeur) * 10) / 10}); } });
const res = {dom: dom, ext: ext, lignes: lines, valeurXIcompletDom: AB[dom].valeurXI, valeurXIcompletExt: AB[ext].valeurXI, valeurXIjourDom: Math.round(A.tot * 10) / 10, valeurXIjourExt: Math.round(B.tot * 10) / 10,
  absentsDom: AB[dom].absentsXI.map(function(x){ return x.joueur; }), absentsExt: AB[ext].absentsXI.map(function(x){ return x.joueur; }), horsXIdom: AB[dom].absentsHorsXI, horsXIext: AB[ext].absentsHorsXI,
  niveauDom: NIV[dom].niveau, niveauExt: NIV[ext].niveau, malusDom: AB[dom].malus, malusExt: AB[ext].malus, bonusDomicile: DOM[dom].bonus};
fs.writeFileSync(path.join(__dirname, 'comparaison_' + dom.replace(/\W+/g, '_') + '__' + ext.replace(/\W+/g, '_') + '.json'), JSON.stringify(res, null, 1));
lines.forEach(function(l){ console.log(l.poste.padEnd(3), (l.dom.nom + (l.dom.absentRemplace ? ' [rempl. ' + l.dom.absentRemplace + ']' : '')).padEnd(60), String(l.dom.valeur).padStart(6), ' | ', (l.ext.nom + (l.ext.absentRemplace ? ' [rempl. ' + l.ext.absentRemplace + ']' : '')).padEnd(62), String(l.ext.valeur).padStart(6), ' | ', l.ecart); });
console.log('XI complet', res.valeurXIcompletDom, 'vs', res.valeurXIcompletExt, '| XI du jour', res.valeurXIjourDom, 'vs', res.valeurXIjourExt);
console.log('absents XI dom:', res.absentsDom.join(', '), '| ext:', res.absentsExt.join(', '));
console.log('hors XI dom:', res.horsXIdom.join(', '), '| ext:', res.horsXIext.join(', '));
console.log('niveaux', res.niveauDom, res.niveauExt, 'malus', res.malusDom, res.malusExt, 'bonus dom', res.bonusDomicile);
