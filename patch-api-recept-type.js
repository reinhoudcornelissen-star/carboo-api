// patch-api-recept-type.js
// Voegt een route toe om het type van een recept te wijzigen:
//   PATCH /api/fuelc/recepten/{recept_id}/type
//
// Alleen de eigenaar van het recept kan dit.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-recept-type.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('RECEPT-TYPE-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '@app.delete("/api/fuelc/recepten/{recept_id}")';
if (f.split(anker).length - 1 !== 1) {
  console.error('FOUT: anker komt niet exact 1x voor.');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-recepttype', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-recepttype');

const blok = `# RECEPT-TYPE-V1
RECEPT_TYPES = ["Ontbijt", "Lunch", "Avondmaal", "Snack", "Sportvoeding", "Herstel"]


@app.patch("/api/fuelc/recepten/{recept_id}/type")
async def recept_type(recept_id: str, body: dict, user=Depends(get_current_user),
                      supabase: Client = Depends(get_supabase)):
    """Wijzigt het type van een recept. Alleen de eigenaar."""
    t = (body.get("type") or "").strip()
    if t not in RECEPT_TYPES:
        raise HTTPException(400, "Onbekend type")
    r = supabase.table("fuelc_recepten_eigen").update({"type": t}) \\
        .eq("id", recept_id).eq("user_id", user.id).execute()
    if not r.data:
        raise HTTPException(404, "Recept niet gevonden")
    return {"ok": True, "type": t}


`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('OK - de route staat er.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Recepttype wijzigen" && git push origin HEAD:main');
