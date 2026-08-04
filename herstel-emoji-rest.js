// herstel-emoji-rest.js
// Zet de laatste vijf emoji terug die het vorige script niet kon herstellen.
//
// Waarom niet automatisch: die emoji bevatten de byte 0x8D of 0x8F, en
// daar bestaat in Windows-1252 geen teken voor. Die byte is bij de
// oorspronkelijke verminking weggevallen en valt niet terug te rekenen.
// Uit wat er overblijft plus de context is wel af te leiden welke het was.
//
// Draaien vanuit de map carboo-api:
//    node herstel-emoji-rest.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (!f.includes('\u00F0\u0178')) {
  console.log('Geen resten meer gevonden. Niets gedaan.');
  process.exit(0);
}

fs.writeFileSync(pad + '.bak-emojirest', f, 'utf8');
console.log('Back-up: ' + pad + '.bak-emojirest');
console.log('');

// Volgorde is van belang: de langste eerst. "ðŸ" op zichzelf is het
// begin van alle andere, dus die moet als laatste.
const vervangingen = [
  ['\u00F0\u0178\u00BD\u00EF\u00B8', '\u{1F37D}\u{FE0F}', 'bord (gut-protocol)'],
  ['\u00F0\u0178\u2026',             '\u{1F3C5}',         'medaille (mijlpaal)'],
  ['\u00F0\u0178\u2020',             '\u{1F3C6}',         'beker (challenge)'],
  ['\u00F0\u0178\u0152',             '\u{1F34C}',         'banaan (producttype)'],
  ['\u00F0\u0178\u00AB',             '\u{1F36B}',         'chocolade (producttype)'],
  ['\u00F0\u0178\u00AA',             '\u{1F36A}',         'koekje (producttype)'],
  ['\u00F0\u0178',                   '\u{1F3C1}',         'vlag (raceplan)'],
];

let totaal = 0;
for (const [zoek, nieuw, wat] of vervangingen) {
  const n = f.split(zoek).length - 1;
  if (n === 0) continue;
  f = f.split(zoek).join(nieuw);
  console.log('  ' + n + 'x  ' + wat);
  totaal += n;
}

if (totaal === 0) {
  console.log('Niets vervangen.');
  process.exit(0);
}

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('Totaal ' + totaal + ' vervangen.');
console.log('');
console.log('Controleer:');
console.log('  python -m py_compile main.py');
console.log('  Select-String -Path main.py -Pattern "ðŸ"      (hoort leeg te zijn)');
