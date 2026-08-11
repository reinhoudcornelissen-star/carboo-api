// patch-api-klantnaam.js
// De klantenlijst van de coach krijgt de voornaam en achternaam mee
// uit fuelc_profiel, zodat het overzicht namen kan tonen in plaats
// van e-mailadressen.
//
// Eén extra bevraging voor de hele lijst, niet één per klant.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-klantnaam.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('KLANTNAAM-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '        klant_reactie_ids = []';
const n = f.split(anker).length - 1;
if (n !== 1) {
  console.error('FOUT: anker komt ' + n + 'x voor (verwacht 1).');
  console.error('  Select-String -Path main.py -Pattern "klant_reactie_ids = \\[\\]"');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-klantnaam', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-klantnaam');

const blok = `        # KLANTNAAM-V1 — namen erbij, zodat het overzicht leesbaar wordt.
        # Faalt stil: zonder naam valt het scherm terug op het e-mailadres.
        try:
            _ids = [k.get("klant_id") for k in mijn_klanten if k.get("klant_id")]
            if _ids:
                _pr = supabase.table("fuelc_profiel") \\
                    .select("user_id,voornaam,achternaam") \\
                    .in_("user_id", _ids).execute().data or []
                _namen = {str(p["user_id"]): p for p in _pr}
                for _k in mijn_klanten:
                    _p = _namen.get(str(_k.get("klant_id"))) or {}
                    _k["voornaam"] = (_p.get("voornaam") or "").strip() or None
                    _k["achternaam"] = (_p.get("achternaam") or "").strip() or None
        except Exception:
            pass

`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('OK - de namen komen mee met de klantenlijst.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Namen bij de klantenlijst" && git push origin HEAD:main');
