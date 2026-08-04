// herstel-tekens2.js
// Herstelt tekens die door PowerShell dubbel gecodeerd zijn.
// Symptoom: emoji werden "ðŸ" en het punt-teken werd "Â·".
//
// Zonder argumenten kijkt hij naar de twee bestanden waar het misging.
// Je kunt ook een pad meegeven:
//    node herstel-tekens2.js main.py
//    node herstel-tekens2.js app\app\coach-zone\page.tsx

const fs = require('fs');
const path = require('path');

const standaard = [
  path.join('app', 'app', 'coach-zone', 'page.tsx'),
  'main.py',
];

const doelen = process.argv.length > 2 ? process.argv.slice(2) : standaard;

// Windows-1252 wijkt op één plek af van Latin-1: de bytes 0x80 tot 0x9F.
const cp1252 = {
  0x20AC: 0x80, 0x201A: 0x82, 0x0192: 0x83, 0x201E: 0x84, 0x2026: 0x85,
  0x2020: 0x86, 0x2021: 0x87, 0x02C6: 0x88, 0x2030: 0x89, 0x0160: 0x8A,
  0x2039: 0x8B, 0x0152: 0x8C, 0x017D: 0x8E, 0x2018: 0x91, 0x2019: 0x92,
  0x201C: 0x93, 0x201D: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97,
  0x02DC: 0x98, 0x2122: 0x99, 0x0161: 0x9A, 0x203A: 0x9B, 0x0153: 0x9C,
  0x017E: 0x9E, 0x0178: 0x9F,
};

let iets = false;

for (const pad of doelen) {
  if (!fs.existsSync(pad)) {
    console.log('overgeslagen (bestaat niet): ' + pad);
    continue;
  }

  const tekst = fs.readFileSync(pad, 'utf8');

  // "Ã" of "Â" gevolgd door een leesteken, of de klassieke emoji-verminking
  if (!/ðŸ|Ã.|Â[ ·»½¡]/.test(tekst)) {
    console.log('in orde: ' + pad);
    continue;
  }

  fs.writeFileSync(pad + '.bak-tekens', tekst, 'utf8');

  const bytes = [];
  for (const ch of tekst) {
    const c = ch.codePointAt(0);
    if (c < 0x100) bytes.push(c);
    else if (cp1252[c] !== undefined) bytes.push(cp1252[c]);
    else for (const b of Buffer.from(ch, 'utf8')) bytes.push(b);
  }

  fs.writeFileSync(pad, Buffer.from(bytes));

  const na = fs.readFileSync(pad, 'utf8');
  const nogFout = /ðŸ|Ã.|Â[ ·»½¡]/.test(na);

  if (nogFout) {
    console.log('LET OP, nog niet goed: ' + pad);
    console.log('  zet terug met: Copy-Item "' + pad + '.bak-tekens" "' + pad + '" -Force');
  } else {
    console.log('hersteld: ' + pad + '   (back-up: ' + path.basename(pad) + '.bak-tekens)');
    iets = true;
  }
}

console.log('');
if (iets) {
  console.log('Klaar. Vergeet niet te bouwen en te pushen in beide mappen.');
} else {
  console.log('Er is niets gewijzigd.');
}
