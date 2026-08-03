// patch-api-suikers.js
// Voegt suikers_toegevoegd_g toe aan het DagboekItem-model in main.py.
// Zonder dit veld filtert Pydantic het weg en blijft de kolom leeg.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-suikers.js

const fs = require('fs');

const pad = 'main.py';

if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('suikers_toegevoegd_g')) {
  console.log('Het veld bestaat al in main.py. Niets gedaan.');
  process.exit(0);
}

const anker = '    suikers_g: Optional[float] = 0';
const aantal = f.split(anker).length - 1;

if (aantal !== 1) {
  console.error('FOUT: anker komt ' + aantal + 'x voor (verwacht 1).');
  console.error('Anker: ' + anker);
  process.exit(1);
}

const bak = pad + '.bak-suikersplitsing';
fs.writeFileSync(bak, f, 'utf8');
console.log('Back-up geschreven: ' + bak);

f = f.replace(
  anker,
  anker + '\n    suikers_toegevoegd_g: Optional[float] = None'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - suikers_toegevoegd_g toegevoegd aan DagboekItem.');
console.log('');
console.log('Volgende stappen:');
console.log('  git add main.py');
console.log('  git commit -m "Dagboek accepteert toegevoegde suikers"');
console.log('  git push origin HEAD:main');
console.log('');
console.log('Render bouwt daarna automatisch opnieuw (duurt een minuut of twee).');
