// herstel-emoji.js
// Herstelt ALLEEN de reeksen die aantoonbaar dubbel gecodeerd zijn.
//
// Werkwijze: zoek groepjes tekens uit het Windows-1252 bereik, zet die
// terug naar bytes, en kijk of die bytes een geldig UTF-8 teken vormen.
// Zo ja, vervangen. Zo nee, met rust laten.
//
// Daardoor blijven "Cafeïne", "—" en andere al correcte tekens ongemoeid.
//
// Draaien vanuit de map van het bestand:
//    node herstel-emoji.js main.py
//    node herstel-emoji.js app\app\coach-zone\page.tsx

const fs = require('fs');

const pad = process.argv[2] || 'main.py';

if (!fs.existsSync(pad)) {
  console.error('FOUT: ' + pad + ' niet gevonden.');
  process.exit(1);
}

const tekst = fs.readFileSync(pad, 'utf8');

if (tekst.includes('\uFFFD')) {
  console.error('FOUT: dit bestand bevat al ongeldige bytes.');
  console.error('Zet eerst een goede versie terug voor je dit draait.');
  process.exit(1);
}

// Windows-1252: de bytes 0x80 tot 0x9F wijken af van Latin-1.
const naarByte = {
  0x20AC: 0x80, 0x201A: 0x82, 0x0192: 0x83, 0x201E: 0x84, 0x2026: 0x85,
  0x2020: 0x86, 0x2021: 0x87, 0x02C6: 0x88, 0x2030: 0x89, 0x0160: 0x8A,
  0x2039: 0x8B, 0x0152: 0x8C, 0x017D: 0x8E, 0x2018: 0x91, 0x2019: 0x92,
  0x201C: 0x93, 0x201D: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97,
  0x02DC: 0x98, 0x2122: 0x99, 0x0161: 0x9A, 0x203A: 0x9B, 0x0153: 0x9C,
  0x017E: 0x9E, 0x0178: 0x9F,
};

function alsByte(ch) {
  const c = ch.codePointAt(0);
  if (c >= 0xA0 && c <= 0xFF) return c;
  if (naarByte[c] !== undefined) return naarByte[c];
  return null;
}

// Reeksen van minstens twee omzetbare tekens: korter kan geen
// meerbyte-teken vormen.
const kandidaat = /[\u00A0-\u00FF\u0152\u0153\u0160\u0161\u0178\u017D\u017E\u0192\u02C6\u02DC\u2013\u2014\u2018\u2019\u201A\u201C\u201D\u201E\u2020\u2021\u2022\u2026\u2030\u2039\u203A\u20AC\u2122]{2,}/g;

let hersteld = 0;
let overgeslagen = 0;

const nieuw = tekst.replace(kandidaat, reeks => {
  const bytes = [];
  for (const ch of reeks) {
    const b = alsByte(ch);
    if (b === null) return reeks;
    bytes.push(b);
  }
  const buf = Buffer.from(bytes);
  const uit = buf.toString('utf8');

  // Alleen aanvaarden als het echt geldige UTF-8 was: geen vervangtekens,
  // en heen en weer omzetten geeft precies dezelfde bytes terug.
  if (uit.includes('\uFFFD') || !Buffer.from(uit, 'utf8').equals(buf)) {
    overgeslagen++;
    return reeks;
  }

  hersteld++;
  return uit;
});

if (hersteld === 0) {
  console.log('Niets te herstellen in ' + pad + '.');
  if (overgeslagen) console.log('(' + overgeslagen + ' reeksen bekeken en met rust gelaten)');
  process.exit(0);
}

fs.writeFileSync(pad + '.bak-emoji', tekst, 'utf8');
fs.writeFileSync(pad, nieuw, 'utf8');

console.log('Back-up: ' + pad + '.bak-emoji');
console.log('');
console.log('Hersteld: ' + hersteld + ' reeks(en)');
console.log('Met rust gelaten: ' + overgeslagen + ' reeks(en)');
console.log('');

// Laat zien wat er veranderd is, zodat je het kunt nakijken.
const oudR = tekst.split(/\r?\n/);
const nieuwR = nieuw.split(/\r?\n/);
let getoond = 0;
for (let i = 0; i < oudR.length && getoond < 8; i++) {
  if (oudR[i] !== nieuwR[i]) {
    console.log('  regel ' + (i + 1) + ':');
    console.log('    was: ' + oudR[i].trim().slice(0, 70));
    console.log('    nu:  ' + nieuwR[i].trim().slice(0, 70));
    getoond++;
  }
}

console.log('');
console.log('Controleer nu of het nog compileert:');
console.log('  python -m py_compile ' + pad + '        (voor main.py)');
console.log('  npm run build                            (voor de frontend)');
