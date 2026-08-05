// patch-api-recept-vanmij.js
// De receptenlijst geeft nu per recept aan of het van de ingelogde
// gebruiker is. Zonder dat kan de app niet weten wie een globaal recept
// op de publieke feed mag zetten.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-recept-vanmij.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('VAN-MIJ-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const zoek =
  '@app.get("/api/fuelc/recepten")\n' +
  'async def get_recepten(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):\n' +
  '    r = supabase.table("fuelc_recepten_eigen").select("*").or_(f"user_id.eq.{user.id},is_globaal.eq.true").order("naam").execute()\n' +
  '    return {"recepten": r.data or []}';

if (f.split(zoek).length - 1 !== 1) {
  // Regeleindes kunnen afwijken; probeer het met een regex.
  const regex = /@app\.get\("\/api\/fuelc\/recepten"\)\r?\nasync def get_recepten\(user=Depends\(get_current_user\), supabase: Client = Depends\(get_supabase\)\):\r?\n( *)r = supabase\.table\("fuelc_recepten_eigen"\)\.select\("\*"\)\.or_\(f"user_id\.eq\.\{user\.id\},is_globaal\.eq\.true"\)\.order\("naam"\)\.execute\(\)\r?\n *return \{"recepten": r\.data or \[\]\}/;
  if (!regex.test(f)) {
    console.error('FOUT: de route /api/fuelc/recepten is niet herkend.');
    console.error('Toon me hem met:');
    console.error('  Select-String -Path main.py -Pattern \'api/fuelc/recepten"\' -Context 0,4');
    process.exit(1);
  }
  fs.writeFileSync(pad + '.bak-vanmij', f, 'utf8');
  f = f.replace(regex,
    '@app.get("/api/fuelc/recepten")\n' +
    'async def get_recepten(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):\n' +
    '$1r = supabase.table("fuelc_recepten_eigen").select("*").or_(f"user_id.eq.{user.id},is_globaal.eq.true").order("naam").execute()\n' +
    '$1# VAN-MIJ-V1 — de app moet weten welke globale recepten van deze gebruiker zijn\n' +
    '$1rijen = r.data or []\n' +
    '$1for _x in rijen:\n' +
    '$1    _x["van_mij"] = str(_x.get("user_id")) == str(user.id)\n' +
    '$1return {"recepten": rijen}'
  );
} else {
  fs.writeFileSync(pad + '.bak-vanmij', f, 'utf8');
  f = f.replace(zoek,
    '@app.get("/api/fuelc/recepten")\n' +
    'async def get_recepten(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):\n' +
    '    r = supabase.table("fuelc_recepten_eigen").select("*").or_(f"user_id.eq.{user.id},is_globaal.eq.true").order("naam").execute()\n' +
    '    # VAN-MIJ-V1 — de app moet weten welke globale recepten van deze gebruiker zijn\n' +
    '    rijen = r.data or []\n' +
    '    for _x in rijen:\n' +
    '        _x["van_mij"] = str(_x.get("user_id")) == str(user.id)\n' +
    '    return {"recepten": rijen}'
  );
}

console.log('Back-up geschreven: ' + pad + '.bak-vanmij');
fs.writeFileSync(pad, f, 'utf8');

console.log('OK - van_mij toegevoegd aan de receptenlijst.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Recepten weten van wie ze zijn" && git push origin HEAD:main');
