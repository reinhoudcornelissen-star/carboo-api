// patch-api-voornaam.js
// De bevoorradingsroute geeft nu ook de voornaam terug, zodat het
// rapport persoonlijk kan openen.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-voornaam.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('VOORNAAM-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}
if (!f.includes('BEVOORRADING-V1')) {
  console.error('FOUT: draai eerst patch-api-bevoorrading.js.');
  process.exit(1);
}

const stappen = [];
function vervang(naam, zoek, nieuw) {
  const n = f.split(zoek).length - 1;
  if (n !== 1) { console.error('FOUT bij "' + naam + '": anker komt ' + n + 'x voor (verwacht 1).'); process.exit(1); }
  f = f.replace(zoek, nieuw);
  stappen.push(naam);
}

fs.writeFileSync(pad + '.bak-voornaam', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-voornaam');

// ─── 1. de naam mee ophalen ────────────────────────────────────────────────
vervang(
  'naam bij het profiel opgehaald',
  '.select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg")',
  '.select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,voornaam,achternaam")   # VOORNAAM-V1'
);

// ─── 2. en meesturen ───────────────────────────────────────────────────────
vervang(
  'naam meegestuurd',
  '        "gewicht_kg": gewicht, "gewogen_op": gewogen_op,',
  '        "voornaam": (profiel.get("voornaam") or "").strip() or None,\n' +
  '        "gewicht_kg": gewicht, "gewogen_op": gewogen_op,'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - ' + stappen.length + ' wijzigingen toegepast:');
stappen.forEach(s => console.log('  - ' + s));
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Voornaam bij de bevoorrading" && git push origin HEAD:main');
