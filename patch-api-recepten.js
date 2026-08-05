// patch-api-recepten.js
// Voegt twee publieke routes toe aan main.py:
//   GET /api/publiek/recepten        — de globale Carboo-recepten
//   GET /api/publiek/recept/{slug}   — één recept, met ingrediënten en bereiding
//
// Alleen recepten met is_globaal = true. Eigen recepten van klanten
// blijven privé.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-recepten.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('RECEPTEN-PUBLIEK-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '@app.get("/api/publiek/wedstrijden")';
if (f.split(anker).length - 1 !== 1) {
  console.error('FOUT: anker niet gevonden. Draai eerst patch-api-racemaps.js.');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-recepten', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-recepten');

const blok = `# ── RECEPTEN-PUBLIEK-V1 — de globale recepten op het open web ──────────

def _recept_slug(naam: str, rid: str) -> str:
    """Leesbare URL met de eerste acht tekens van het id erachter,
    zodat twee recepten met dezelfde naam elkaar niet in de weg zitten."""
    return _slug(naam) + "-" + str(rid).replace("-", "")[:8]


def _recept_veilig(r: dict, kort: bool = True) -> dict:
    import json as _json
    ingr = r.get("ingredienten")
    if isinstance(ingr, str):
        try:
            ingr = _json.loads(ingr)
        except Exception:
            ingr = []
    uit = {
        "id": r["id"],
        "slug": _recept_slug(r.get("naam") or "recept", r["id"]),
        "naam": r.get("naam") or "",
        "type": r.get("type"),
        "porties": r.get("aantal_porties") or 1,
        "kcal": r.get("kcal"), "kh": r.get("kh"),
        "eiwit": r.get("eiwit"), "vet": r.get("vet"),
        "vezels": r.get("vezels"), "gi": r.get("gi"),
        "ingredienten": ingr or [],
    }
    if not kort:
        uit["bereiding"] = r.get("bereiding") or ""
        uit["suikers"] = r.get("suikers")
        uit["natrium"] = r.get("natrium")
    return uit


@app.get("/api/publiek/recepten")
async def publieke_recepten(supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_recepten_eigen").select("*") \\
        .eq("is_globaal", True).order("naam").limit(200).execute()
    return {"recepten": [_recept_veilig(x) for x in (r.data or [])]}


@app.get("/api/publiek/recept/{slug}")
async def publiek_recept(slug: str, supabase: Client = Depends(get_supabase)):
    staart = slug.rsplit("-", 1)[-1]
    if len(staart) != 8:
        raise HTTPException(404, "Recept niet gevonden")
    r = supabase.table("fuelc_recepten_eigen").select("*") \\
        .eq("is_globaal", True).limit(400).execute()
    for x in (r.data or []):
        if str(x["id"]).replace("-", "")[:8] == staart:
            return _recept_veilig(x, kort=False)
    raise HTTPException(404, "Recept niet gevonden")


`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - twee publieke routes toegevoegd.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Recepten publiek" && git push origin HEAD:main');
console.log('');
console.log('Testen na de deploy, zonder inloggen:');
console.log('  https://carboo-api-fra.onrender.com/api/publiek/recepten');
