// Étape 4 bis du nouveau modèle : bonus / malus propre à chaque équipe quand elle reçoit.
// Avantage domicile commun H = 50 Elo (≈ 0,29 but). Bonus propre = (moyenne des résidus à domicile - moyenne des résidus à l'extérieur) / 2,
// où résidu = différence de buts réelle - prévue par la valeur seule (plafonnée à ±4 buts, convertie en Elo).
// Ce bonus est ramené vers 0 avec un poids LAMH en matchs : bonus = brut * n / (n + LAMH), n = 2*nDom*nExt/(nDom+nExt).
// Il ne s'applique qu'aux matchs que l'équipe joue à domicile.
// Usage : node modele-valeur/etape4b_domicile.js [LAMH]   (lit niveaux_equipes.json, absences_actuelles.json ; écrit domicile_equipes.json et matchs_J11.json)
const fs = require('fs'), path = require('path');
const LAMH = Number(process.argv[2]) || 40, H = 50;
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
const per100 = (function(){ const a = lamOf(100), b = lamOf(0); return (a[0] - a[1]) - (b[0] - b[1]); })(), G2E = 100 / per100;
const S = {}; Object.keys(R0).forEach(function(t){ S[t] = {sh: 0, nh: 0, sa: 0, na: 0}; });
Object.keys(HIST).map(Number).sort(function(a, b){ return a - b; }).forEach(function(md){
  HIST[md].forEach(function(m){
    if(!m.played) return;
    const l = lamOf(R0[m.home] + H - R0[m.away]);
    const g = Math.max(-4, Math.min(4, (m.homeScore - m.awayScore) - (l[0] - l[1]))) * G2E;
    S[m.home].sh += g; S[m.home].nh++; S[m.away].sa -= g; S[m.away].na++;
  });
});
const out = {};
Object.keys(S).forEach(function(t){
  const x = S[t], ne = x.nh && x.na ? 2 * x.nh * x.na / (x.nh + x.na) : 0, brut = ne ? (x.sh / x.nh - x.sa / x.na) / 2 : 0;
  out[t] = {matchsDomicile: x.nh, matchsExterieur: x.na, brut: Math.round(brut * 10) / 10, bonus: Math.round(brut * ne / (ne + LAMH) * 10) / 10};
});
fs.writeFileSync(path.join(__dirname, 'domicile_equipes.json'), JSON.stringify({etape: '4bis', LAMH: LAMH, H: H, equipes: out}, null, 1));
// combinaison avec niveaux + absences sur les matchs restants de la J11
const AB = JSON.parse(fs.readFileSync(path.join(__dirname, 'absences_actuelles.json'), 'utf8'));
const rows = AB.matchsJ11.map(function(r){
  const hm = r.match.split(' - ')[0], bonus = out[hm].bonus;
  return Object.assign({}, r, {bonusDomicile: bonus, ecartFinal: Math.round((r.ecartApres + bonus) * 10) / 10});
});
fs.writeFileSync(path.join(__dirname, 'matchs_J11.json'), JSON.stringify({etape: '4bis', LAMH: LAMH, matchs: rows}, null, 1));
console.log('équipe'.padEnd(26), 'dom/ext', ' brut', ' bonus retenu');
Object.keys(out).sort(function(a, b){ return out[b].bonus - out[a].bonus; }).forEach(function(t){ console.log(t.padEnd(26), (out[t].matchsDomicile + '/' + out[t].matchsExterieur).padEnd(7), String(out[t].brut).padStart(6), String(out[t].bonus).padStart(7)); });
console.log('\nmatch'.padEnd(40), 'bonus dom', 'écart avant absences → après absences → final');
rows.forEach(function(r){ console.log(r.match.padEnd(40), String(r.bonusDomicile).padStart(7), '  ', String(r.ecartAvant).padStart(7), '→', String(r.ecartApres).padStart(7), '→', String(r.ecartFinal).padStart(7)); });
