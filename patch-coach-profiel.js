// patch-coach-profiel.js
// De coachroute /api/coach/klant/{id}/data haalde maar zes profielvelden op
// en berekende vvm_kg en eiwit_doel_g niet. Daardoor viel bij de coach de
// regel "Energy availability" weg en klopten de macrodoelen niet.
//
// Nu worden dezelfde berekende velden meegestuurd als bij de klant zelf.
// De Strava-tokens blijven bewust buiten de selectie.
//
// Draaien vanuit de root van carboo-api:
//    node patch-coach-profiel.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('COACH-PROFIEL-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const zoek =
  '    prof = supabase.table("fuelc_profiel").select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,lengte_cm").eq("user_id", klant_id).execute()';

const aantal = f.split(zoek).length - 1;
if (aantal !== 1) {
  console.error('FOUT: anker komt ' + aantal + 'x voor (verwacht 1).');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-coachprofiel', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-coachprofiel');

const nieuw =
  '    # COACH-PROFIEL-V1 — dezelfde velden en berekeningen als bij de klant zelf,\n' +
  '    # zodat vetvrije massa, eiwitdoel en energy availability ook hier kloppen.\n' +
  '    prof = supabase.table("fuelc_profiel").select(\n' +
  '        "energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,lengte_cm,"\n' +
  '        "leeftijd,geslacht,doelstelling,activiteit,doel_tempo,bmr,tdee,tdee_basis,"\n' +
  '        "vet_meting_pct,vet_meting_gewicht_kg,vet_meting_datum,momenten_tijden,eet_patroon"\n' +
  '    ).eq("user_id", klant_id).execute()';

f = f.replace(zoek, nieuw);

// De toewijzing eronder krijgt de berekende velden mee.
const zoek2 = '    result["profiel"] = prof.data[0] if prof.data else {}';
if (f.split(zoek2).length - 1 !== 1) {
  console.error('FOUT: tweede anker komt niet exact 1x voor.');
  process.exit(1);
}

f = f.replace(zoek2,
  '    _profRij = prof.data[0] if prof.data else {}\n' +
  '    if _profRij:\n' +
  '        _profRij["vvm_kg"] = bereken_vvm(_profRij)\n' +
  '        _profRij["eiwit_doel_g"] = bereken_eiwit_doel(_profRij)\n' +
  '    result["profiel"] = _profRij'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('OK - de coach krijgt nu het volledige profiel met de berekende velden.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Coach krijgt vetvrije massa en eiwitdoel van zijn klant" && git push origin HEAD:main');
