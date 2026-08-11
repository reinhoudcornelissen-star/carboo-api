// patch-voornaam-fix.js
// De vorige patch zette "# VOORNAAM-V1" achter een regel die met een
// backslash doorliep. Daardoor viel de voortzetting weg en struikelde
// Python over de inspringing.
//
// Draaien vanuit de root van carboo-api:
//    node patch-voornaam-fix.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

const zoek = '.select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,voornaam,achternaam")   # VOORNAAM-V1';

if (!f.includes(zoek)) {
  console.log('Die regel staat er niet (meer). Niets gedaan.');
  console.log('Controleer met:');
  console.log('  Select-String -Path main.py -Pattern "VOORNAAM-V1" -Context 1,2');
  process.exit(0);
}

fs.writeFileSync(pad + '.bak-voornaamfix', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-voornaamfix');

f = f.replace(zoek, '.select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,voornaam,achternaam")');

fs.writeFileSync(pad, f, 'utf8');

console.log('OK - het commentaar is weg, de voortzetting werkt weer.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Voortzetting hersteld" && git push origin HEAD:main');
