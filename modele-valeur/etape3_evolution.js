// Étape 3 du nouveau modèle : le niveau de chaque équipe évolue avec les résultats.
// niveau(équipe) = niveau valeur (étape 2) + ajustement ; ajustement = somme des écarts (différence de buts réelle - prévue par la valeur seule,
// convertie en Elo, plafonnée à ±4 buts) / (nombre de matchs + LAMBDA). LAMBDA = poids de la valeur, en nombre de matchs.
// Usage : node modele-valeur/etape3_evolution.js [LAMBDA]   (écrit niveaux_actuels.json)
const fs = require('fs'), path = require('path');
const LAMBDA = Number(process.argv[2]) || 50, H = 50;
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'elo.html'), 'utf8');
const i = html.indexOf('const EMBED = '), E = JSON.parse(html.slice(i + 14, html.indexOf('\n', i)).replace(/;\s*$/, ''));
const R0 = JSON.parse(fs.readFileSync(path.join(__dirname, 'niveaux_equipes.json'), 'utf8')).niveaux;
const idx = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const a0 = idx.indexOf('let MATCHDAY_HISTORY = {');
let d = 0, k = idx.indexOf('{', a0); const st = k;
for(; k < idx.length; k++){ if(idx[k] === '{') d++; else if(idx[k] === '}'){ d--; if(!d) break; } }
const HIST = eval('(' + idx.slice(st, k + 1) + ')');
const P = E.P, lamOf = function(dd){ const x = dd / 100; return [Math.exp(P[0] + P[1] * x), Math.exp(P[2] - P[3] * x)]; };
const per100 = (function(){ const a = lamOf(100), b = lamOf(0); return (a[0] - a[1]) - (b[0] - b[1]); })();
const G2E = 100 / per100;
const A = {}; Object.keys(R0).forEach(function(t){ A[t] = {s: 0, n: 0}; });
let nm = 0;
Object.keys(HIST).map(Number).sort(function(a, b){ return a - b; }).forEach(function(md){
  HIST[md].forEach(function(m){
    if(!m.played) return;
    const l = lamOf(R0[m.home] + H - R0[m.away]);
    const res = Math.max(-4, Math.min(4, (m.homeScore - m.awayScore) - (l[0] - l[1]))) * G2E;
    A[m.home].s += res; A[m.home].n++; A[m.away].s -= res; A[m.away].n++; nm++;
  });
});
const out = {};
Object.keys(R0).forEach(function(t){ out[t] = {depart: R0[t], ajustement: Math.round(A[t].s / (A[t].n + LAMBDA) * 10) / 10, niveau: Math.round((R0[t] + A[t].s / (A[t].n + LAMBDA)) * 10) / 10, matchs: A[t].n}; });
fs.writeFileSync(path.join(__dirname, 'niveaux_actuels.json'), JSON.stringify({etape: 3, lambda: LAMBDA, matchsJoues: nm, niveaux: out}, null, 1));
Object.keys(out).sort(function(a, b){ return out[b].niveau - out[a].niveau; }).forEach(function(t){ console.log(t.padEnd(26), String(Math.round(out[t].depart)).padStart(5), '->', String(Math.round(out[t].niveau)).padStart(5), '(' + (out[t].ajustement >= 0 ? '+' : '') + Math.round(out[t].ajustement) + ')'); });
