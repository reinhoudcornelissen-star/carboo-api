// patch-push-synchroon.js
// De push draaide op een losse daemon-thread. Op Render kan zo'n thread
// stilvallen zodra het verzoek klaar is en de dienst niets meer te doen
// heeft — dan blijft de melding hangen tot het volgende verkeer de
// dienst weer wakker maakt. Vandaar de vertraging van uren.
//
// Oplossing: de push synchroon versturen. Het duurt een fractie van een
// seconde per toestel en je hebt een handvol toestellen, dus de klant
// merkt er niets van — en de melding is gegarandeerd verstuurd voordat
// het verzoek terugkeert.
//
// De naam en handtekening van stuur_push_async blijven gelijk, dus de
// vier aanroepers hoeven niet aangeraakt te worden.
//
// Draaien vanuit de root van carboo-api:
//    node patch-push-synchroon.js
//
// DAARNA EERST:  python -m py_compile main.py

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('PUSHKOPPEL-V2')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const oud =
`def stuur_push_async(*args, **kwargs):
    """PUSHKOPPEL-V1 — verstuurt op een aparte thread zodat het verzoek
    niet hoeft te wachten. Faalt stil, net als stuur_push zelf."""
    import threading
    try:
        threading.Thread(target=stuur_push, args=args, kwargs=kwargs, daemon=True).start()
    except Exception:
        pass`;

if (f.split(oud).length - 1 !== 1) {
  console.error('FOUT: de functie stuur_push_async is niet herkend (mogelijk andere regeleindes).');
  console.error('  Controleer met: Select-String -Path main.py -Pattern "PUSHKOPPEL-V1"');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-pushsync', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-pushsync');

const nieuw =
`def stuur_push_async(*args, **kwargs):
    """PUSHKOPPEL-V2 — verstuurt synchroon. Een losse daemon-thread bleef
    op Render soms uren hangen tot de dienst weer opgepord werd; een push
    duurt maar een fractie van een seconde, dus we wachten er gewoon op.
    Faalt stil, net als stuur_push zelf."""
    try:
        return stuur_push(*args, **kwargs)
    except Exception:
        return 0`;

f = f.replace(oud, nieuw);
fs.writeFileSync(pad, f, 'utf8');

// controle op commentaar achter een doorlopende regel
const verdacht = [];
f.split(/\r?\n/).forEach((r, i) => {
  if (/\\\s*$/.test(r) && r.includes('#')) verdacht.push(i + 1);
});

console.log('OK - de push wordt nu synchroon verstuurd.');
console.log(verdacht.length
  ? 'WAARSCHUWING: commentaar achter een doorlopende regel op: ' + verdacht.join(', ')
  : 'Controle: geen commentaar achter een doorlopende regel.');

console.log('');
console.log('EERST DIT, en pas pushen als het zwijgt:');
console.log('  python -m py_compile main.py');
console.log('');
console.log('  git add -A && git commit -m "Push synchroon versturen" && git push origin HEAD:main');
