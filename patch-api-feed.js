// patch-api-feed.js
// Zet klaar wat de gecombineerde feedpagina nodig heeft:
//   GET /api/publiek/artikels          — de Carboo-posts (als die nog ontbreken)
//   GET /api/publiek/artikel/{id}      — één post
//   GET /api/publiek/racemaps-recent   — de laatste racemaps over alle wedstrijden
//
// Alles zonder login. Alleen posts met is_admin_post = true komen naar buiten.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-feed.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

const anker = '@app.get("/api/publiek/wedstrijden")';
if (f.split(anker).length - 1 !== 1) {
  console.error('FOUT: anker niet gevonden. Draai eerst patch-api-racemaps.js.');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-feed', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-feed');

let blok = '';

if (!f.includes('ARTIKELS-PUBLIEK-V1')) {
  blok += `# ── ARTIKELS-PUBLIEK-V1 — de Carboo-posts op het open web ──────────────

def _artikel_veilig(p: dict, kort: bool = True) -> dict:
    tekst = p.get("tekst") or ""
    return {
        "id": p["id"],
        "titel": p.get("titel") or "",
        "tekst": (tekst[:240] + "…") if (kort and len(tekst) > 240) else tekst,
        "type": p.get("type"),
        "foto_url": p.get("foto_url"),
        "aangemaakt": p.get("aangemaakt"),
    }


@app.get("/api/publiek/artikels")
async def publieke_artikels(supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coach_prikbord") \\
        .select("id,titel,tekst,type,foto_url,aangemaakt") \\
        .eq("is_admin_post", True) \\
        .order("aangemaakt", desc=True).limit(60).execute()
    return {"artikels": [_artikel_veilig(p) for p in (r.data or [])]}


@app.get("/api/publiek/artikel/{artikel_id}")
async def publiek_artikel(artikel_id: str, supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coach_prikbord") \\
        .select("id,titel,tekst,type,foto_url,aangemaakt") \\
        .eq("id", artikel_id).eq("is_admin_post", True).execute()
    if not r.data:
        raise HTTPException(404, "Artikel niet gevonden")
    return _artikel_veilig(r.data[0], kort=False)


`;
  console.log('  - artikelroutes toegevoegd');
} else {
  console.log('  - artikelroutes stonden er al');
}

if (!f.includes('FEED-RECENT-V1')) {
  blok += `# ── FEED-RECENT-V1 — de laatste racemaps over alle wedstrijden ─────────

@app.get("/api/publiek/racemaps-recent")
async def publieke_racemaps_recent(supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_racemaps_publiek").select("*") \\
        .is_("verwijderd_op", "null") \\
        .order("gepubliceerd", desc=True).limit(40).execute()
    rijen = r.data or []
    if not rijen:
        return {"racemaps": []}

    ids = [x["rapport_id"] for x in rijen]
    rap = supabase.table("carboo_rapporten").select("id,meta").in_("id", ids).execute()
    per_id = {x["id"]: x for x in (rap.data or [])}

    uit = []
    for x in rijen:
        if x["rapport_id"] not in per_id:
            continue
        veilig = _publiek_veilig(x, per_id[x["rapport_id"]])
        veilig["slug"] = x["wedstrijd_slug"]
        uit.append(veilig)
    return {"racemaps": uit}


`;
  console.log('  - racemaps-recent toegevoegd');
} else {
  console.log('  - racemaps-recent stond er al');
}

if (!blok) {
  console.log('');
  console.log('Alles stond er al. Niets gewijzigd.');
  process.exit(0);
}

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Publieke feedroutes" && git push origin HEAD:main');
