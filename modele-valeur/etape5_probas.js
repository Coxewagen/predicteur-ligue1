// Étape 5 du nouveau modèle : du niveau de match aux probabilités 1 / N / 2 (Poisson + Dixon-Coles, conversion Elo -> buts d'elo.html).
// écart de match d = niveau(dom) + malus absences(dom) + bonus domicile(dom) + H - (niveau(ext) + malus absences(ext))
// Usage : node modele-valeur/etape5_probas.js   (lit niveaux_actuels.json, absences_actuelles.json, domicile_equipes.json, cotes.json ; écrit probas_J11.json)
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), H = 50;
const html = fs.readFileSync(path.join(root, 'elo.html'), 'utf8');
const i = html.indexOf('const EMBED = '), E = JSON.parse(html.slice(i + 14, html.indexOf('\n', i)).replace(/;\s*$/, ''));
const NIV = JSON.parse(fs.readFileSync(path.join(__dirname, 'niveaux_actuels.json'), 'utf8')).niveaux;
const AB = JSON.parse(fs.readFileSync(path.join(__dirname, 'absences_actuelles.json'), 'utf8')).equipes;
const DOM = JSON.parse(fs.readFileSync(path.join(__dirname, 'domicile_equipes.json'), 'utf8')).equipes;
const COTES = JSON.parse(fs.readFileSync(path.join(root, 'cotes.json'), 'utf8'));
const fact = function(n){ let f = 1; for(let k = 2; k <= n; k++) f *= k; return f; };
const pois = function(l, k){ return Math.exp(-l) * Math.pow(l, k) / fact(k); };
function predict(d){
  const x = d / 100, lh = Math.exp(E.P[0] + E.P[1] * x), la = Math.exp(E.P[2] - E.P[3] * x), rho = E.RHO, M = [];
  let tot = 0, ph = 0, pd = 0, pa = 0, best = {p: -1};
  for(let a = 0; a <= 10; a++){ M[a] = []; for(let b = 0; b <= 10; b++){ let p = pois(lh, a) * pois(la, b); if(a === 0 && b === 0) p *= 1 - lh * la * rho; else if(a === 0 && b === 1) p *= 1 + lh * rho; else if(a === 1 && b === 0) p *= 1 + la * rho; else if(a === 1 && b === 1) p *= 1 - rho; p = Math.max(p, 0); M[a][b] = p; tot += p; } }
  for(let a = 0; a <= 10; a++) for(let b = 0; b <= 10; b++){ const p = M[a][b] / tot; if(a > b) ph += p; else if(a === b) pd += p; else pa += p; if(p > best.p) best = {i: a, j: b, p: p}; }
  return {p1: ph, pN: pd, p2: pa, lh: lh, la: la, score: best};
}
const J11 = [['OGC Nice', 'Paris Saint-Germain', 'sam. 17h15'], ['AS Monaco', 'AJ Auxerre', 'sam. 20h45'], ['LOSC Lille', 'Olympique Lyonnais', 'sam. 20h45'], ['RC Lens', 'Toulouse FC', 'sam. 20h45'], ['RC Strasbourg', 'Stade Brestois', 'sam. 20h45'], ['Paris FC', 'Angers SCO', 'dim. 15h00'], ['FC Lorient', 'Stade Rennais', 'dim. 17h15'], ['Olympique de Marseille', 'Le Mans FC', 'dim. 20h45']];
const r1 = function(x){ return Math.round(x * 1000) / 10; };
const rows = J11.map(function(m){
  const h = m[0], a = m[1], dd = NIV[h].niveau + AB[h].malus + DOM[h].bonus + H - (NIV[a].niveau + AB[a].malus), pr = predict(dd);
  const o = COTES.odds[h + '|' + a], q = o ? o.map(function(x){ return 1 / x; }) : null, s = q ? q[0] + q[1] + q[2] : 1;
  const mk = q ? q.map(function(x){ return x / s; }) : null;
  return {match: h + ' - ' + a, heure: m[2], ecart: Math.round(dd * 10) / 10, p1: r1(pr.p1), pN: r1(pr.pN), p2: r1(pr.p2), butsAttendus: [Math.round(pr.lh * 100) / 100, Math.round(pr.la * 100) / 100], scoreProbable: pr.score.i + '-' + pr.score.j,
    cotesJustes: [pr.p1, pr.pN, pr.p2].map(function(x){ return Math.round(100 / x) / 100; }), cotesWinamax: o || null, marche: mk ? mk.map(r1) : null, ecartMarche: mk ? [r1(pr.p1 - mk[0]), r1(pr.pN - mk[1]), r1(pr.p2 - mk[2])] : null};
});
fs.writeFileSync(path.join(__dirname, 'probas_J11.json'), JSON.stringify({etape: 5, cotesDu: COTES.updatedAt, matchs: rows}, null, 1));
rows.forEach(function(r){ console.log(r.match.padEnd(38), String(r.ecart).padStart(7), ' 1/N/2 ', [r.p1, r.pN, r.p2].join(' / ').padEnd(18), ' marché ', (r.marche || []).join(' / ').padEnd(18), ' écart ', (r.ecartMarche || []).join(' / '), ' score', r.scoreProbable, ' buts', r.butsAttendus.join('-')); });
