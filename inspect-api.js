// inspect-api.js — LEEST ALLEEN, verandert niets.
// Draaien vanuit de map van je API-repo (waar main.py staat):
//    node inspect-api.js
// Staat main.py ergens anders, geef het pad mee:
//    node inspect-api.js C:\Users\reinhoud\Documents\Carbs\carboo-api

const fs = require('fs');
const path = require('path');

const CONTEXT = 14;
const uit = [];
const log = (s = '') => { uit.push(s); console.log(s); };

const startMap = process.argv[2] || '.';

// main.py zoeken
function zoek(naam, start) {
  const res = [];
  (function loop(dir, diep) {
    if (diep > 6) return;
    let items;
    try { items = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const it of items) {
      if (['node_modules', '.git', '.next', 'venv', '__pycache__', 'env'].includes(it.name)) continue;
      const p = path.join(dir, it.name);
      if (it.isDirectory()) loop(p, diep + 1);
      else if (it.name === naam) res.push(p);
    }
  })(start, 0);
  return res;
}

const paden = zoek('main.py', startMap);

if (paden.length === 0) {
  log('main.py niet gevonden vanaf: ' + path.resolve(startMap));
  log('');
  log('Geef het pad van je API-repo mee, bijvoorbeeld:');
  log('  node inspect-api.js ..\\carboo-api');
  process.exit(0);
}

for (const p of paden) {
  const regels = fs.readFileSync(p, 'utf8').split(/\r?\n/);
  log('');
  log('='.repeat(70));
  log('bestand: ' + p + '   (' + regels.length + ' regels)');
  log('='.repeat(70));

  const patronen = [
    /fuelc\/bibliotheek/,
    /fuelc_bibliotheek/,
    /is_globaal/,
  ];

  const houden = new Set();
  regels.forEach((r, i) => {
    if (patronen.some(pat => pat.test(r))) {
      for (let j = Math.max(0, i - CONTEXT); j <= Math.min(regels.length - 1, i + CONTEXT); j++) houden.add(j);
    }
  });

  if (houden.size === 0) { log('  (geen treffers)'); continue; }

  const lijst = [...houden].sort((a, b) => a - b);
  let vorige = -99;
  for (const i of lijst) {
    if (i > vorige + 1) log('  ...');
    log(String(i + 1).padStart(5) + ' | ' + regels[i]);
    vorige = i;
  }
}

fs.writeFileSync('inspect-api-output.txt', uit.join('\n'), 'utf8');
log('');
log('Klaar. Alles staat ook in inspect-api-output.txt');
