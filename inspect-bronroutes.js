// inspect-bronroutes.js — LEEST ALLEEN, verandert niets.
// Toont de vier routes waar een pushmelding aan gehangen moet worden.
//
// Draaien vanuit de root van carboo-api:
//    node inspect-bronroutes.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

const uit = [];
const log = (s = '') => { uit.push(s); console.log(s); };
const regels = fs.readFileSync(pad, 'utf8').split(/\r?\n/);

// Zoek de route op naam en toon hem tot de volgende @app-decorator
function toonRoute(titel, zoek) {
  log('');
  log('='.repeat(70));
  log(titel);
  log('='.repeat(70));

  const start = regels.findIndex(r => r.includes(zoek));
  if (start === -1) { log('  (niet gevonden: ' + zoek + ')'); return; }

  let eind = start + 1;
  while (eind < regels.length && eind < start + 90) {
    if (regels[eind].startsWith('@app.')) break;
    eind++;
  }

  for (let i = start; i < eind; i++) {
    log(String(i + 1).padStart(5) + ' | ' + regels[i]);
  }
}

log('CARBOO — bronroutes voor pushmeldingen');

toonRoute('1) COACH STUURT EEN BERICHT',        '@app.post("/api/coach/berichten")');
toonRoute('2) COACH PLAATST EEN OPMERKING',     '@app.post("/api/coach/opmerkingen")');
toonRoute('3) COACH PLANT EEN TRAINING',        '@app.post("/api/coach/klant/{klant_id}/training")');
toonRoute('4) COACH MAAKT EEN RACEPLAN-CONCEPT','@app.post("/api/coach/klant/{klant_id}/raceplan-concept")');

fs.writeFileSync('inspect-bronroutes.txt', uit.join('\n'), 'utf8');
log('');
log('Klaar. Alles staat ook in inspect-bronroutes.txt');
