// patch-namen-backend.js
// Twee wijzigingen in main.py:
//   1. De bevoorradingsroute geeft de voornaam terug.
//   2. De klantenlijst van de coach krijgt voornaam en achternaam mee.
//
// LET OP — wat er de vorige keer misging: ik zette een commentaar achter
// een regel die met een backslash doorliep naar de volgende. Dat
// commentaar slikt de backslash op, en dan valt de volgende regel los.
// Er staat nu geen enkel commentaar achter zo'n regel.
//
// Draaien vanuit de root van carboo-api:
//    node patch-namen-backend.js
//
// DAARNA EERST:  python -m py_compile main.py
// Pas pushen als dat commando zwijgt.

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('NAMEN-V2')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}
if (!f.includes('BEVOORRADING-V1')) {
  console.error('FOUT: de bevoorradingsroute ontbreekt. Draai eerst patch-api-bevoorrading.js.');
  process.exit(1);
}

const stappen = [];
function vervang(naam, zoek, nieuw) {
  const n = f.split(zoek).length - 1;
  if (n !== 1) { console.error('FOUT bij "' + naam + '": anker komt ' + n + 'x voor (verwacht 1).'); process.exit(1); }
  f = f.replace(zoek, nieuw);
  stappen.push(naam);
}

fs.writeFileSync(pad + '.bak-namen2', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-namen2');

// ─── 1. de naam mee ophalen (geen commentaar op deze regel!) ───────────────
vervang(
  'naam bij het profiel opgehaald',
  '.select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg")',
  '.select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,voornaam,achternaam")'
);

// ─── 2. de naam meesturen met het rapport ──────────────────────────────────
vervang(
  'naam meegestuurd met het rapport',
  '        "gewicht_kg": gewicht, "gewogen_op": gewogen_op,',
  '        "voornaam": (profiel.get("voornaam") or "").strip() or None,\n' +
  '        "gewicht_kg": gewicht, "gewogen_op": gewogen_op,'
);

// ─── 3. namen bij de klantenlijst ──────────────────────────────────────────
vervang(
  'namen bij de klantenlijst',
  '        klant_reactie_ids = []',
  '        # NAMEN-V2 — namen erbij zodat het klantenoverzicht leesbaar wordt.\n' +
  '        # Faalt stil: zonder naam valt het scherm terug op het e-mailadres.\n' +
  '        try:\n' +
  '            _ids = [k.get("klant_id") for k in mijn_klanten if k.get("klant_id")]\n' +
  '            if _ids:\n' +
  '                _pr = supabase.table("fuelc_profiel").select("user_id,voornaam,achternaam").in_("user_id", _ids).execute().data or []\n' +
  '                _namen = {str(p["user_id"]): p for p in _pr}\n' +
  '                for _k in mijn_klanten:\n' +
  '                    _p = _namen.get(str(_k.get("klant_id"))) or {}\n' +
  '                    _k["voornaam"] = (_p.get("voornaam") or "").strip() or None\n' +
  '                    _k["achternaam"] = (_p.get("achternaam") or "").strip() or None\n' +
  '        except Exception:\n' +
  '            pass\n' +
  '\n' +
  '        klant_reactie_ids = []'
);

fs.writeFileSync(pad, f, 'utf8');

// ─── controle: staat er ergens commentaar achter een doorlopende regel? ────
const regels = f.split(/\r?\n/);
const verdacht = [];
regels.forEach((r, i) => {
  if (/\\\s*$/.test(r) && r.includes('#')) verdacht.push(i + 1);
});

console.log('');
console.log('OK - ' + stappen.length + ' wijzigingen toegepast:');
stappen.forEach(s => console.log('  - ' + s));

if (verdacht.length) {
  console.log('');
  console.log('WAARSCHUWING: commentaar achter een doorlopende regel op: ' + verdacht.join(', '));
} else {
  console.log('');
  console.log('Controle: geen commentaar achter een doorlopende regel.');
}

console.log('');
console.log('EERST DIT, en pas pushen als het zwijgt:');
console.log('  python -m py_compile main.py');
console.log('');
console.log('  git add -A && git commit -m "Namen in rapport en klantenlijst" && git push origin HEAD:main');
