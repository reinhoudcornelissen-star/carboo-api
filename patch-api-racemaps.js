// patch-api-racemaps.js
// Voegt toe aan main.py:
//   POST /api/racemap/publiceer      — een raceplan openbaar maken
//   POST /api/racemap/depubliceer    — weer offline halen
//   GET  /api/racemap/status         — wat heb ik gepubliceerd
//   GET  /api/publiek/wedstrijden    — GEEN login: lijst wedstrijden
//   GET  /api/publiek/racemaps/{slug}— GEEN login: de plannen van een wedstrijd
//
// De publieke routes geven alleen gepubliceerde plannen terug, en alleen
// de velden die openbaar mogen zijn. Nooit het volledige rapport.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-racemaps.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('RACEMAPS-PUBLIEK-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '@app.get("/api/fuelc/welzijn")';
const aantal = f.split(anker).length - 1;
if (aantal !== 1) {
  console.error('FOUT: anker komt ' + aantal + 'x voor (verwacht 1).');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-racemaps', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-racemaps');

const blok = `# ============================================================
# RACEMAPS-PUBLIEK-V1 — raceplannen delen op het open web
# ============================================================

class RacemapPubliceer(BaseModel):
    rapport_id: str
    wedstrijd: str
    toon_naam: bool = False
    voornaam: Optional[str] = None


def _slug(tekst: str) -> str:
    """Nette URL-vorm: 'Ironman Maastricht' wordt 'ironman-maastricht'.
    Accenten eruit, alles klein, spaties en leestekens naar streepjes."""
    import unicodedata, re as _re
    t = unicodedata.normalize("NFKD", tekst or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "onbekend"


def _publiek_veilig(rij: dict, rapport: dict) -> dict:
    """Bouwt wat naar buiten mag. Alles wat hier niet in staat,
    verlaat de server niet."""
    meta = rapport.get("meta") or {}
    return {
        "id": rij["id"],
        "wedstrijd": rij["wedstrijd"],
        "sport": rij.get("sport") or meta.get("sport"),
        "duur_min": rij.get("duur_min") or meta.get("totale_min"),
        "voornaam": rij.get("voornaam") if rij.get("toon_naam") else None,
        "gepubliceerd": rij.get("gepubliceerd"),
        "plan_items": meta.get("plan_items") or {},
    }


@app.post("/api/racemap/publiceer")
async def racemap_publiceer(item: RacemapPubliceer, user=Depends(get_current_user),
                            supabase: Client = Depends(get_supabase)):
    # Alleen je eigen rapport mag je publiceren
    r = supabase.table("carboo_rapporten").select("id,meta,user_id") \\
        .eq("id", item.rapport_id).eq("user_id", user.id).execute()
    if not r.data:
        raise HTTPException(404, "Raceplan niet gevonden")

    meta = r.data[0].get("meta") or {}
    if not (meta.get("plan_items")):
        raise HTTPException(400, "Dit raceplan bevat nog geen plan om te delen")

    wedstrijd = (item.wedstrijd or "").strip()
    if len(wedstrijd) < 3:
        raise HTTPException(400, "Geef een wedstrijdnaam op")

    supabase.table("carboo_racemaps_publiek").upsert({
        "rapport_id": item.rapport_id,
        "user_id": user.id,
        "wedstrijd": wedstrijd,
        "wedstrijd_slug": _slug(wedstrijd),
        "sport": meta.get("sport"),
        "duur_min": meta.get("totale_min"),
        "toon_naam": bool(item.toon_naam),
        "voornaam": (item.voornaam or "").strip()[:40] if item.toon_naam else None,
        "verwijderd_op": None,
    }, on_conflict="rapport_id").execute()

    return {"ok": True, "slug": _slug(wedstrijd)}


@app.post("/api/racemap/depubliceer")
async def racemap_depubliceer(body: dict, user=Depends(get_current_user),
                              supabase: Client = Depends(get_supabase)):
    from datetime import datetime, timezone
    rid = body.get("rapport_id")
    if not rid:
        raise HTTPException(400, "rapport_id ontbreekt")
    supabase.table("carboo_racemaps_publiek") \\
        .update({"verwijderd_op": datetime.now(timezone.utc).isoformat()}) \\
        .eq("rapport_id", rid).eq("user_id", user.id).execute()
    return {"ok": True}


@app.get("/api/racemap/status")
async def racemap_status(user=Depends(get_current_user),
                         supabase: Client = Depends(get_supabase)):
    """Welke van mijn raceplannen staan openbaar?"""
    r = supabase.table("carboo_racemaps_publiek") \\
        .select("rapport_id,wedstrijd,wedstrijd_slug,toon_naam,gepubliceerd") \\
        .eq("user_id", user.id).is_("verwijderd_op", "null").execute()
    return {"gepubliceerd": r.data or []}


# ─── Publiek, zonder login ──────────────────────────────────────────────

@app.get("/api/publiek/wedstrijden")
async def publieke_wedstrijden(supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_racemaps_publiek") \\
        .select("wedstrijd,wedstrijd_slug,sport") \\
        .is_("verwijderd_op", "null").limit(2000).execute()

    per = {}
    for x in (r.data or []):
        s = x["wedstrijd_slug"]
        if s not in per:
            per[s] = {"slug": s, "wedstrijd": x["wedstrijd"], "sporten": set(), "aantal": 0}
        per[s]["aantal"] += 1
        if x.get("sport"):
            per[s]["sporten"].add(x["sport"])

    lijst = [{"slug": v["slug"], "wedstrijd": v["wedstrijd"],
              "sporten": sorted(v["sporten"]), "aantal": v["aantal"]}
             for v in per.values()]
    lijst.sort(key=lambda v: (-v["aantal"], v["wedstrijd"]))
    return {"wedstrijden": lijst}


@app.get("/api/publiek/racemaps/{slug}")
async def publieke_racemaps(slug: str, supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_racemaps_publiek").select("*") \\
        .eq("wedstrijd_slug", slug).is_("verwijderd_op", "null") \\
        .order("gepubliceerd", desc=True).limit(60).execute()
    rijen = r.data or []
    if not rijen:
        return {"wedstrijd": None, "plannen": []}

    ids = [x["rapport_id"] for x in rijen]
    rap = supabase.table("carboo_rapporten").select("id,meta").in_("id", ids).execute()
    per_id = {x["id"]: x for x in (rap.data or [])}

    plannen = [_publiek_veilig(x, per_id.get(x["rapport_id"], {}))
               for x in rijen if x["rapport_id"] in per_id]

    return {"wedstrijd": rijen[0]["wedstrijd"], "plannen": plannen}


`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - vijf routes toegevoegd.');
console.log('');
console.log('Volgende stappen:');
console.log('  git add -A && git commit -m "Raceplannen publiek delen" && git push origin HEAD:main');
console.log('');
console.log('Testen zodra Render gebouwd heeft:');
console.log('  https://carboo-api-fra.onrender.com/api/publiek/wedstrijden');
console.log('  Dat hoort een lege lijst te geven, zonder inloggen.');
