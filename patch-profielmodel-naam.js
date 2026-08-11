// patch-profielmodel-naam.js
// voornaam en achternaam toevoegen aan FuelcProfiel. Zonder deze twee
// regels gooit de opslagroute ze weg, want het model bepaalt wat er
// bewaard wordt.
//
// De velden komen achteraan de klasse te staan, zodat de bestaande
// volgorde ongemoeid blijft.
//
// Draaien vanuit de root van carboo-api:
//    node patch-profielmodel-naam.js
//
// DAARNA EERST:  python -m py_compile main.py

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (/class FuelcProfiel[\s\S]{0,1200}?voornaam: Optional\[str\]/.test(f)) {
  console.log('De naamvelden staan er al in. Niets gedaan.');
  process.exit(0);
}

const zoek = '    td_2: Optional[bool] = False';
const n = f.split(zoek).length - 1;
if (n !== 1) {
  console.error('FOUT: anker komt ' + n + 'x voor (verwacht 1).');
  console.error('  Select-String -Path main.py -Pattern "td_2: Optional" -Context 2,2');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-profielnaam', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-profielnaam');

f = f.replace(zoek,
  '    td_2: Optional[bool] = False\n' +
  '    voornaam: Optional[str] = None\n' +
  '    achternaam: Optional[str] = None'
);

fs.writeFileSync(pad, f, 'utf8');

// controle: geen commentaar achter een doorlopende regel
const verdacht = [];
f.split(/\r?\n/).forEach((r, i) => {
  if (/\\\s*$/.test(r) && r.includes('#')) verdacht.push(i + 1);
});

console.log('OK - voornaam en achternaam staan in het model.');
console.log(verdacht.length
  ? 'WAARSCHUWING: commentaar achter een doorlopende regel op: ' + verdacht.join(', ')
  : 'Controle: geen commentaar achter een doorlopende regel.');

console.log('');
console.log('EERST DIT, en pas pushen als het zwijgt:');
console.log('  python -m py_compile main.py');
console.log('');
console.log('  git add -A && git commit -m "Naamvelden in het profielmodel" && git push origin HEAD:main');
