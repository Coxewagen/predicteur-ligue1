// Étape 4 du nouveau modèle : les absences.
// Principe : le niveau d'une équipe le jour du match = niveau de l'étape 3 + malus d'absences.
//   malus = C * ln((V - perte) / V)        V = valeur du XI type, perte = valeur des titulaires absents - valeur de leurs remplaçants
// Même logique de remplacement qu'elo.html : meilleur remplaçant du même poste (valeur x1), sinon poste voisin (x0,8), sinon rien.
// Garde-fous repris d'elo.html (non testés ici, faute d'historique d'absences) : gardien titulaire absent sans vrai remplaçant -> au moins -15 ; plafond -40.
// Sources d'absences : texte absenceReason de index.html (vérifié J11) + liste des blessés Transfermarkt (blesses.json).
// Usage : node modele-valeur/etape4_absences.js   (écrit absences_actuelles.json)
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const C = JSON.parse(fs.readFileSync(path.join(__dirname, 'niveaux_equipes.json'), 'utf8')).C;   // 106
const GKFLOOR = 15, CAP = 40, MINREG = 150;
const SQ = JSON.parse(fs.readFileSync(path.join(__dirname, 'joueurs_2026-11-01.json'), 'utf8'));
const NIV = JSON.parse(fs.readFileSync(path.join(__dirname, 'niveaux_actuels.json'), 'utf8')).niveaux;
const BL = JSON.parse(fs.readFileSync(path.join(ROOT, 'blesses.json'), 'utf8'));
// texte d'absences de index.html
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
let a = html.indexOf('let TEAMS = ['), d = 0, i = html.indexOf('[', a), st = i;
for (; i < html.length; i++) { if (html[i] === '[') d++; else if (html[i] === ']') { d--; if (!d) break; } }
const TEAMS = eval('(' + html.slice(st, i + 1) + ')');
const ABS = {}; TEAMS.forEach(function(t){ ABS[t.name] = t.absenceReason || ''; });

const SLOTS = {G: 1, DC: 2, DL: 2, MI: 3, AT: 2, BU: 1}, ADJ = {G: [], DC: ['DL'], DL: ['DC'], MI: ['AT'], AT: ['MI', 'BU'], BU: ['AT']};
// classes de segments du texte : retour (apte, de retour, disponible...), incertain, sinon absent
function classe(ns){
  if (/\b(de retour|apte|aptes|disponibles?|n est plus signale|mais sur le banc|reporte)\b/.test(ns.replace(/'/g, ' '))) return 'ret';
  if (/\bincertains?\b/.test(ns)) return 'inc';
  if (/aucun absent/.test(ns)) return 'rien';
  return 'abs';
}
function nrm(s){ return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/-/g, ' '); }
function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function sameName(x, y){
  const p = nrm(x).split(' ').filter(Boolean), q = nrm(y).split(' ').filter(Boolean);
  if (p.join(' ') === q.join(' ')) return true;
  const lp = p[p.length - 1], lq = q[q.length - 1];
  if (lp === lq && (p.length === 1 || q.length === 1 || p[0][0] === q[0][0])) return true;
  return p.some(function(w){ return w.length >= 5 && q.includes(w); });
}
function absentsOf(team){
  const text = ABS[team] || '', sq = SQ[team] || [], cls = {abs: new Set(), ret: new Set(), inc: new Set()};
  text.split(';').forEach(function(seg){
    const ns = nrm(seg), c = classe(ns); if (c === 'rien') return;
    sq.forEach(function(p){
      const parts = nrm(p[0]).split(' ').filter(Boolean);
      const cands = (parts.length > 1 ? parts.slice(1).map(function(_, k){ return parts.slice(k + 1).join(' '); }).concat(parts.slice(1).filter(function(w){ return w.length >= 5; })) : [parts[0]]).concat([nrm(p[0])]);
      for (const sur of cands) {
        const m = ns.match(new RegExp('(?:\\b([a-z]{1,2})\\. )?\\b' + esc(sur) + '\\b'));
        if (m) { if (m[1] && !parts[0].startsWith(m[1])) continue; cls[c].add(p[0]); break; }
      }
    });
  });
  const out = new Set(cls.abs), src = {}; cls.abs.forEach(function(n){ src[n] = 'texte'; });
  // le texte vérifié du jour l'emporte sur Transfermarkt : un joueur « de retour » ou « incertain » dans le texte n'est pas compté absent
  ((BL.teams || {})[team] || []).forEach(function(n){
    const p = sq.find(function(q){ return q[0] === n; }) || sq.find(function(q){ return sameName(q[0], n); });
    if (!p || cls.ret.has(p[0]) || cls.inc.has(p[0])) return;
    out.add(p[0]); src[p[0]] = src[p[0]] ? 'texte+TM' : 'TM';
  });
  return {noms: [...out], src: src, incertains: [...cls.inc], retours: [...cls.ret]};
}
function xiOf(sq){
  const XI = [];
  Object.keys(SLOTS).forEach(function(g){
    const grp = sq.filter(function(p){ return p[1] === g; }).slice();
    if (g === 'G') grp.sort(function(x, y){ return (y[3] - x[3]) || (y[2] - x[2]); });
    else grp.sort(function(x, y){ return ((y[3] >= MINREG) - (x[3] >= MINREG)) || (y[2] - x[2]); });
    XI.push.apply(XI, grp.slice(0, SLOTS[g]));
  });
  return XI;
}
function impact(team){
  const sq = SQ[team], ab = absentsOf(team), absent = new Set(ab.noms), full = xiOf(sq), V = full.reduce(function(s, p){ return s + p[2]; }, 0);
  const fullN = new Set(full.map(function(p){ return p[0]; }));
  const bench = sq.filter(function(p){ return !fullN.has(p[0]) && !absent.has(p[0]); }).sort(function(x, y){ return y[2] - x[2]; });
  let loss = 0, gk = false; const list = [];
  full.filter(function(p){ return absent.has(p[0]); }).sort(function(x, y){ return y[2] - x[2]; }).forEach(function(p){
    let best = null, bv = -1;
    bench.filter(function(q){ return q[1] === p[1]; }).forEach(function(q){ if (q[2] > bv) { bv = q[2]; best = q; } });
    bench.filter(function(q){ return ADJ[p[1]].includes(q[1]); }).forEach(function(q){ if (q[2] * 0.8 > bv) { bv = q[2] * 0.8; best = q; } });
    if (!best) bv = 0; else bench.splice(bench.indexOf(best), 1);
    const l = Math.max(0, p[2] - bv); loss += l; if (p[1] === 'G' && bv < 0.5 * p[2]) gk = true;
    list.push({joueur: p[0], poste: p[1], valeur: p[2], source: ab.src[p[0]], remplacant: best ? best[0] : null, valeurRemplacant: best ? Math.round(bv * 10) / 10 : 0, perte: Math.round(l * 10) / 10});
  });
  let malus = C * Math.log(Math.max(V - loss, 0.1) / V), brut = malus;
  if (gk) malus = Math.min(malus, -GKFLOOR);
  malus = Math.max(malus, -CAP);
  // absents repérés mais hors XI type (info seulement)
  const horsXI = ab.noms.filter(function(n){ return !fullN.has(n); });
  return {valeurXI: V, perteTotale: Math.round(loss * 10) / 10, malusBrut: Math.round(brut * 10) / 10, malus: Math.round(malus * 10) / 10, gardienSansRemplacant: gk, absentsXI: list, absentsHorsXI: horsXI, incertains: ab.incertains};
}
const out = {};
Object.keys(SQ).forEach(function(t){ out[t] = impact(t); out[t].niveauSansAbsence = NIV[t] ? NIV[t].niveau : null; out[t].niveauAvecAbsences = NIV[t] ? Math.round((NIV[t].niveau + out[t].malus) * 10) / 10 : null; });
fs.writeFileSync(path.join(__dirname, 'absences_actuelles.json'), JSON.stringify({etape: 4, C: C, GKFLOOR: GKFLOOR, CAP: CAP, blessesTM: BL.updatedAt, equipes: out}, null, 1));
Object.keys(out).sort(function(x, y){ return out[x].malus - out[y].malus; }).forEach(function(t){
  const o = out[t];
  console.log(t.padEnd(24), String(o.malus).padStart(6), ' perte', String(o.perteTotale).padStart(6), '/', String(o.valeurXI).padStart(5), ' ', o.absentsXI.map(function(x){ return x.joueur + ' (' + x.poste + ' ' + x.valeur + '→' + (x.remplacant || 'aucun') + ' ' + x.valeurRemplacant + ', ' + x.source + ')'; }).join(' ; '), o.gardienSansRemplacant ? '[GK]' : '', o.absentsHorsXI.length ? ' | hors XI: ' + o.absentsHorsXI.join(', ') : '');
});

// Effet sur les matchs restants de la J11 (écart de niveau domicile - extérieur, avantage domicile inclus)
const J11 = [['OGC Nice', 'Paris Saint-Germain', 'sam. 17h15'], ['AS Monaco', 'AJ Auxerre', 'sam. 20h45'], ['LOSC Lille', 'Olympique Lyonnais', 'sam. 20h45'], ['RC Lens', 'Toulouse FC', 'sam. 20h45'], ['RC Strasbourg', 'Stade Brestois', 'sam. 20h45'], ['Paris FC', 'Angers SCO', 'dim. 15h00'], ['FC Lorient', 'Stade Rennais', 'dim. 17h15'], ['Olympique de Marseille', 'Le Mans FC', 'dim. 20h45']];
const H = 50, rows = J11.map(function(m){
  const h = out[m[0]], a = out[m[1]];
  const avant = h.niveauSansAbsence + H - a.niveauSansAbsence, apres = h.niveauAvecAbsences + H - a.niveauAvecAbsences;
  return {match: m[0] + ' - ' + m[1], heure: m[2], malusDom: h.malus, malusExt: a.malus, ecartAvant: Math.round(avant * 10) / 10, ecartApres: Math.round(apres * 10) / 10, variation: Math.round((apres - avant) * 10) / 10};
});
const f = JSON.parse(fs.readFileSync(path.join(__dirname, 'absences_actuelles.json'), 'utf8')); f.matchsJ11 = rows;
fs.writeFileSync(path.join(__dirname, 'absences_actuelles.json'), JSON.stringify(f, null, 1));
console.log('\nmatch'.padEnd(40), 'malus dom/ext', ' écart avant → après (Elo)', ' variation');
rows.forEach(function(r){ console.log(r.match.padEnd(40), (r.malusDom + ' / ' + r.malusExt).padEnd(14), String(r.ecartAvant).padStart(7), '→', String(r.ecartApres).padStart(7), ' ', (r.variation > 0 ? '+' : '') + r.variation); });
