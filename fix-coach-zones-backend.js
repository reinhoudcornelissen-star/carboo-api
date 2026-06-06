const fs = require('fs');
const pad = 'C:/Users/reinhoud/Documents/Carbs/carboo-api/main.py';
let f = fs.readFileSync(pad, 'utf8');

if (f.includes('/api/coach/klant/{klant_id}/zones')) {
  console.log('AL AANWEZIG');
  process.exit(0);
}

const anker = `    return {"ok": True}\r\n\r\n\r\n# ─── DOSSIER / RAPPORTEN`;

const L = [
  '    return {"ok": True}',
  '',
  '',
  '# ─── COACH: ZONES PER KLANT ───────────────────────────────────────────────────',
  '',
  'async def _verifieer_coach_klant(user, klant_id, supabase):',
  '    """Check dat de ingelogde gebruiker een coach is die aan deze klant gekoppeld is."""',
  '    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()',
  '    if not coach.data:',
  '        raise HTTPException(403, "Geen coach account")',
  '    coach_id = coach.data[0]["id"]',
  '    relatie = supabase.table("carboo_coach_klanten").select("id").eq("coach_id", coach_id).eq("klant_id", klant_id).eq("status", "actief").execute()',
  '    if not relatie.data:',
  '        raise HTTPException(403, "Geen actieve relatie met deze klant")',
  '    return coach_id',
  '',
  '@app.get("/api/coach/klant/{klant_id}/zones")',
  'async def get_klant_zones(klant_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):',
  '    """Haal alle zones (per sport) van een klant op. Alleen voor gekoppelde coach."""',
  '    await _verifieer_coach_klant(user, klant_id, supabase)',
  '    r = supabase.table("fuelc_zones").select("*").eq("user_id", klant_id).execute()',
  '    return {"zones": r.data or []}',
  '',
  '@app.post("/api/coach/klant/{klant_id}/zones")',
  'async def sla_klant_zones_op(klant_id: str, data: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):',
  '    """Sla zones voor een sport van een klant op. Alleen voor gekoppelde coach."""',
  '    await _verifieer_coach_klant(user, klant_id, supabase)',
  '    sport = (data.get("sport") or "").strip()',
  '    if not sport:',
  '        raise HTTPException(400, "Sport is verplicht")',
  '    toegestaan = {"sport", "eenheid"}',
  '    for z in ["z1","z2","z3","z4","z5"]:',
  '        for suf in ["_hs_van","_hs_tot","_tempo_van","_tempo_tot"]:',
  '            toegestaan.add(z + suf)',
  '    payload = {k: v for k, v in data.items() if k in toegestaan}',
  '    payload["user_id"] = klant_id',
  '    payload["sport"] = sport',
  '    payload["updated_at"] = "now()"',
  '    bestaand = supabase.table("fuelc_zones").select("id").eq("user_id", klant_id).eq("sport", sport).execute()',
  '    if bestaand.data:',
  '        supabase.table("fuelc_zones").update(payload).eq("user_id", klant_id).eq("sport", sport).execute()',
  '    else:',
  '        supabase.table("fuelc_zones").insert(payload).execute()',
  '    return {"ok": True}',
  '',
  '',
  '# ─── DOSSIER / RAPPORTEN',
];
const nieuw = L.join('\r\n');

if (!f.includes(anker)) {
  console.log('ANKER NIET GEVONDEN');
  process.exit(0);
}
f = f.replace(anker, nieuw);
fs.writeFileSync(pad, f, 'utf8');
console.log('OK - zones-endpoints toegevoegd (schoon)');
