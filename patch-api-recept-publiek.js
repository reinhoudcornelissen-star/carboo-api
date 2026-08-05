// patch-api-recept-publiek.js
// 1. De publieke receptenlijst toont alleen nog recepten met publiek = true.
// 2. Nieuwe route om die vlag om te zetten vanuit de app:
//      PATCH /api/fuelc/recepten/{recept_id}/publiek
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-recept-publiek.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('RECEPT-PUBLIEK-V2')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

if (!f.includes('RECEPTEN-PUBLIEK-V1')) {
  console.error('FOUT: draai eerst patch-api-recepten.js.');
  process.exit(1);
}

const stappen = [];
function vervang(naam, zoek, nieuw) {
  const n = f.split(zoek).length - 1;
  if (n !== 1) { console.error('FOUT bij "' + naam + '": anker komt ' + n + 'x voor (verwacht 1).'); process.exit(1); }
  f = f.replace(zoek, nieuw);
  stappen.push(naam);
}

fs.writeFileSync(pad + '.bak-receptpubliek', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-receptpubliek');

// ─── 1. de lijst filteren ──────────────────────────────────────────────────
vervang(
  'lijst filtert op de publieke vlag',
  '    r = supabase.table("fuelc_recepten_eigen").select("*") \\\n        .eq("is_globaal", True).order("naam").limit(200).execute()',
  '    # RECEPT-PUBLIEK-V2 — alleen wat bewust online gezet is\n' +
  '    r = supabase.table("fuelc_recepten_eigen").select("*") \\\n' +
  '        .eq("is_globaal", True).eq("publiek", True).order("naam").limit(200).execute()'
);

// ─── 2. het detail ook ─────────────────────────────────────────────────────
vervang(
  'detailpagina filtert mee',
  '    r = supabase.table("fuelc_recepten_eigen").select("*") \\\n        .eq("is_globaal", True).limit(400).execute()',
  '    r = supabase.table("fuelc_recepten_eigen").select("*") \\\n' +
  '        .eq("is_globaal", True).eq("publiek", True).limit(400).execute()'
);

// ─── 3. route om de vlag om te zetten ──────────────────────────────────────
vervang(
  'schakelroute toegevoegd',
  '@app.delete("/api/fuelc/recepten/{recept_id}")',
  '@app.patch("/api/fuelc/recepten/{recept_id}/publiek")\n' +
  'async def recept_publiek(recept_id: str, body: dict, user=Depends(get_current_user),\n' +
  '                         supabase: Client = Depends(get_supabase)):\n' +
  '    """Zet een globaal recept op of van de publieke feed.\n' +
  '    Alleen de eigenaar van het recept kan dit."""\n' +
  '    aan = bool(body.get("publiek"))\n' +
  '    r = supabase.table("fuelc_recepten_eigen").update({"publiek": aan}) \\\n' +
  '        .eq("id", recept_id).eq("user_id", user.id).execute()\n' +
  '    if not r.data:\n' +
  '        raise HTTPException(404, "Recept niet gevonden")\n' +
  '    return {"ok": True, "publiek": aan}\n' +
  '\n' +
  '\n' +
  '@app.delete("/api/fuelc/recepten/{recept_id}")'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - ' + stappen.length + ' wijzigingen toegepast:');
stappen.forEach(s => console.log('  - ' + s));
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Recepten alleen publiek na eigen keuze" && git push origin HEAD:main');
