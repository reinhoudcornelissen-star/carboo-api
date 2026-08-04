// inspect-meldingen.js — LEEST ALLEEN, verandert niets.
// Draaien vanuit de root van carboo-api:
//    node inspect-meldingen.js
// Output ook in inspect-meldingen.txt

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

const uit = [];
const log = (s = '') => { uit.push(s); console.log(s); };
const regels = fs.readFileSync(pad, 'utf8').split(/\r?\n/);

function toon(titel, patronen, context) {
  log('');
  log('='.repeat(70));
  log(titel);
  log('='.repeat(70));

  const houden = new Set();
  regels.forEach((r, i) => {
    if (patronen.some(p => p.test(r))) {
      for (let j = Math.max(0, i - 1); j <= Math.min(regels.length - 1, i + context); j++) houden.add(j);
    }
  });

  if (houden.size === 0) { log('  (geen treffers)'); return; }

  const lijst = [...houden].sort((a, b) => a - b);
  let vorige = -99;
  for (const i of lijst) {
    if (i > vorige + 1) log('  ...');
    log(String(i + 1).padStart(5) + ' | ' + regels[i]);
    vorige = i;
  }
}

log('CARBOO — waar ontstaan de meldingen?');
log('bestand: main.py (' + regels.length + ' regels)');

// 1. Hoe worden meldingen opgehaald?
toon(
  '1) DE MELDINGEN ZELF',
  [/api\/notificaties/],
  26
);

// 2. Alle POST- en PUT-routes: daar gebeurt iets dat een melding waard kan zijn
log('');
log('='.repeat(70));
log('2) ALLE ROUTES DIE IETS AANMAKEN OF WIJZIGEN');
log('='.repeat(70));
regels.forEach((r, i) => {
  const m = r.match(/@app\.(post|put|patch)\("([^"]+)"\)/);
  if (m) {
    const volgende = regels[i + 1] || '';
    const naam = (volgende.match(/async def (\w+)/) || [])[1] || '?';
    log('  ' + String(i + 1).padStart(5) + '  ' + m[1].toUpperCase().padEnd(6) + m[2].padEnd(48) + naam);
  }
});

// 3. Bestaat er al een meldingentabel?
toon(
  '3) TABELLEN DIE MET MELDINGEN TE MAKEN HEBBEN',
  [/notificatie/i, /melding/i, /_gelezen/],
  3
);

fs.writeFileSync('inspect-meldingen.txt', uit.join('\n'), 'utf8');
log('');
log('Klaar. Alles staat ook in inspect-meldingen.txt');
