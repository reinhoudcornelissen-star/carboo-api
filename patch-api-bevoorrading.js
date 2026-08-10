// patch-api-bevoorrading.js
// De rekenroute voor het weekrapport:
//   GET /api/fuelc/bevoorrading?van=2026-08-03&tot=2026-08-09
//   GET /api/coach/klant/{klant_id}/bevoorrading?van=...&tot=...
//
// Wat ze doet:
//   - de week aan logregels ophalen en per dag optellen
//   - gelogde gerechten uitpakken in hun ingredienten, alleen voor de
//     groente- en fruittelling (de macro's staan al op de logregel zelf)
//   - categorieen herkennen met herken_categorie uit CATWOORDEN-V1
//   - de nutrientdensiteit berekenen met dezelfde formule als de app
//   - per training het dagdeel ervoor en erna
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-bevoorrading.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('BEVOORRADING-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}
if (!f.includes('CATWOORDEN-V1')) {
  console.error('FOUT: draai eerst patch-api-categoriewoorden.js.');
  process.exit(1);
}

const anker = '@app.get("/api/publiek/wedstrijden")';
if (f.split(anker).length - 1 !== 1) {
  console.error('FOUT: anker niet gevonden.');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-bevoorrading', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-bevoorrading');

const blok = `# ── BEVOORRADING-V1 — de cijfers voor het weekrapport ──────────────────

MOMENT_NAMEN = {0: "Ontbijt", 1: "Voormiddag", 2: "Lunch",
                3: "Namiddag", 4: "Avondmaal", 5: "Avondtussendoortje"}


def _gf_gram(rij: dict, recepten: dict, supabase: Client):
    """Hoeveel gram groente en fruit zit er in deze logregel?

    Een gewoon product telt met zijn eigen gewicht. Een gelogd gerecht
    wordt uitgepakt in zijn ingredienten en geschaald naar het aantal
    porties, want daar zitten de groenten in verstopt."""
    groente = 0.0
    fruit = 0.0

    rid = rij.get("recept_id")
    rc = recepten.get(str(rid)) if rid else None

    if rc and rc.get("ingredienten"):
        ingr = rc["ingredienten"]
        if isinstance(ingr, str):
            try:
                ingr = json.loads(ingr)
            except Exception:
                ingr = []
        porties_gelogd = (rij.get("hoeveelheid_g") or 100) / 100.0
        schaal = porties_gelogd / max(float(rc.get("aantal_porties") or 1), 1)
        for i in (ingr or []):
            gram = (i.get("gram") or i.get("hoeveelheid_g") or 0) * schaal
            cat = herken_categorie(i.get("naam") or "", "Groenten en fruit", supabase)
            if cat == "Groenten":
                groente += gram
            elif cat == "Fruit":
                fruit += gram
        return groente, fruit

    cat = herken_categorie(rij.get("naam") or "", rij.get("categorie") or "", supabase)
    gram = rij.get("hoeveelheid_g") or 0
    if cat == "Groenten":
        groente += gram
    elif cat == "Fruit":
        fruit += gram
    return groente, fruit


def _nd_score(v: dict) -> float:
    """Nutrientdensiteit /10 — zelfde formule als analyse-utils.ts."""
    if not v.get("kcal"):
        return 0.0
    s = 0.0
    if v["vezels"] >= 25: s += 2
    elif v["vezels"] >= 15: s += 1
    if v["kalium"] >= 2800: s += 1
    elif v["kalium"] >= 1500: s += 0.5
    if v["calcium"] >= 800: s += 1
    elif v["calcium"] >= 400: s += 0.5
    if v["ijzer"] >= 10: s += 1
    elif v["ijzer"] >= 5: s += 0.5
    if v["vitd"] >= 10: s += 0.5
    elif v["vitd"] >= 5: s += 0.25
    if v["vitb12"] >= 1.5: s += 1
    elif v["vitb12"] >= 0.8: s += 0.5
    if v["omega3"] >= 1.0: s += 0.5
    elif v["omega3"] >= 0.5: s += 0.25
    gf = v["groenten"] + v["fruit"]
    if gf >= 500: s += 3
    elif gf >= 350: s += 2
    elif gf >= 200: s += 1
    elif gf >= 100: s += 0.5
    groepen = len([c for c, k in v["cat_kcal"].items() if k > 50])
    if groepen >= 5: s += 1
    elif groepen >= 3: s += 0.5
    return round(min(10.0, s), 1)


def _bereken_bevoorrading(user_id: str, van: str, tot: str, supabase: Client) -> dict:
    # alles in een paar bevragingen, niet een per dag
    dg = supabase.table("fuelc_dagboek").select("*") \\
        .eq("user_id", user_id).gte("datum", van).lte("datum", tot).execute().data or []
    tr = supabase.table("fuelc_trainingen").select("*") \\
        .eq("user_id", user_id).gte("datum", van).lte("datum", tot) \\
        .order("datum").execute().data or []

    recept_ids = list({str(r["recept_id"]) for r in dg if r.get("recept_id")})
    recepten = {}
    if recept_ids:
        rr = supabase.table("fuelc_recepten_eigen") \\
            .select("id,naam,aantal_porties,ingredienten") \\
            .in_("id", recept_ids).execute().data or []
        recepten = {str(x["id"]): x for x in rr}

    gewicht = None
    gewogen_op = None
    try:
        w = supabase.table("fuelc_dagboek_welzijn").select("datum,gewicht_kg") \\
            .eq("user_id", user_id).gte("datum", van).lte("datum", tot) \\
            .not_.is_("gewicht_kg", "null").order("datum", desc=True).limit(1).execute().data or []
        if w:
            gewicht = w[0].get("gewicht_kg")
            gewogen_op = w[0].get("datum")
    except Exception:
        pass

    # ── per dag optellen ────────────────────────────────────────────
    def leeg():
        return {"kcal": 0.0, "kh": 0.0, "eiwit": 0.0, "vet": 0.0, "vezels": 0.0,
                "suikers": 0.0, "suikers_toegevoegd": 0.0, "verzadigd": 0.0,
                "omega3": 0.0, "natrium": 0.0, "kalium": 0.0, "calcium": 0.0,
                "ijzer": 0.0, "vitd": 0.0, "vitb12": 0.0,
                "groenten": 0.0, "fruit": 0.0, "cat_kcal": {}}

    dagen: dict = {}
    per_moment: dict = {}

    for r in dg:
        d = str(r.get("datum"))
        v = dagen.setdefault(d, leeg())
        v["kcal"] += r.get("kcal") or 0
        v["kh"] += r.get("kh_g") or 0
        v["eiwit"] += r.get("eiwit_g") or 0
        v["vet"] += r.get("vet_g") or 0
        v["vezels"] += r.get("vezels_g") or 0
        v["suikers"] += r.get("suikers_g") or 0
        v["suikers_toegevoegd"] += r.get("suikers_toegevoegd_g") or 0
        v["verzadigd"] += r.get("verz_g") or 0
        v["omega3"] += r.get("omega3_g") or 0
        v["natrium"] += r.get("natrium_mg") or 0
        v["kalium"] += r.get("kalium_mg") or 0
        v["calcium"] += r.get("calcium_mg") or 0
        v["ijzer"] += r.get("ijzer_mg") or 0
        v["vitd"] += r.get("vitd_mcg") or 0
        v["vitb12"] += r.get("vitb12_mcg") or 0

        g, fr = _gf_gram(r, recepten, supabase)
        v["groenten"] += g
        v["fruit"] += fr

        cat = herken_categorie(r.get("naam") or "", r.get("categorie") or "", supabase)
        v["cat_kcal"][cat] = v["cat_kcal"].get(cat, 0) + (r.get("kcal") or 0)

        m = r.get("moment")
        if m is not None and m < 90:
            pm = per_moment.setdefault(int(m), {"kh": 0.0, "eiwit": 0.0, "vet": 0.0})
            pm["kh"] += r.get("kh_g") or 0
            pm["eiwit"] += r.get("eiwit_g") or 0
            pm["vet"] += r.get("vet_g") or 0

    n_dagen = max(len(dagen), 1)

    def gem(sleutel):
        return round(sum(v[sleutel] for v in dagen.values()) / n_dagen, 1)

    # ── per training ────────────────────────────────────────────────
    def moment_voor(start) -> int:
        s = str(start or "")[:5]
        if not s:
            return 2
        if s < "10:00": return 0
        if s < "12:00": return 1
        if s < "15:00": return 2
        if s < "18:00": return 3
        return 4

    def som(datum, moment, veld):
        return round(sum((r.get(veld) or 0) for r in dg
                         if str(r.get("datum")) == str(datum) and r.get("moment") == moment))

    trainingen = []
    for t in tr:
        mv = moment_voor(t.get("starttijd"))
        duur = t.get("duur_min") or 0
        tijdens = round(sum((r.get("kh_g") or 0) for r in dg
                            if str(r.get("datum")) == str(t.get("datum"))
                            and (r.get("moment") or 0) >= 90))
        trainingen.append({
            "datum": t.get("datum"),
            "sport": t.get("sport"),
            "duur_min": duur,
            "starttijd": t.get("starttijd"),
            "verbrand": round(t.get("kcal_verbranding") or 0),
            "dagdeel_voor": MOMENT_NAMEN.get(mv, ""),
            "kh_voor": som(t.get("datum"), mv, "kh_g"),
            "kh_tijdens": tijdens,
            "kh_per_uur": round(tijdens / (duur / 60.0)) if duur >= 60 else None,
            "dagdeel_na": MOMENT_NAMEN.get(mv + 1, ""),
            "kh_na": som(t.get("datum"), mv + 1, "kh_g"),
            "eiwit_na": som(t.get("datum"), mv + 1, "eiwit_g"),
        })

    # ── de nutrientdensiteit per dag, dan gemiddeld ─────────────────
    nd = [_nd_score(v) for v in dagen.values() if v["kcal"] > 0]
    nd_gem = round(sum(nd) / len(nd), 1) if nd else 0.0

    return {
        "van": van, "tot": tot,
        "gewicht_kg": gewicht, "gewogen_op": gewogen_op,
        "dagen_gelogd": len(dagen),
        "trainingen_aantal": len(tr),
        "trainingsminuten": sum((t.get("duur_min") or 0) for t in tr),
        "verbrand_kcal": round(sum((t.get("kcal_verbranding") or 0) for t in tr)),

        "nutrientdensiteit": nd_gem,
        "per_dag": {
            "kcal": gem("kcal"), "kh": gem("kh"), "eiwit": gem("eiwit"), "vet": gem("vet"),
            "vezels": gem("vezels"),
            "zetmeel": round(gem("kh") - gem("suikers"), 1),
            "suikers_natuurlijk": round(gem("suikers") - gem("suikers_toegevoegd"), 1),
            "suikers_toegevoegd": gem("suikers_toegevoegd"),
            "verzadigd": gem("verzadigd"),
            "onverzadigd": round(gem("vet") - gem("verzadigd"), 1),
            "omega3": gem("omega3"),
            "groenten": round(gem("groenten")),
            "fruit": round(gem("fruit")),
            "natrium": round(gem("natrium")), "kalium": round(gem("kalium")),
            "calcium": round(gem("calcium")), "ijzer": gem("ijzer"),
            "vitd": gem("vitd"), "vitb12": gem("vitb12"),
        },
        "dagen": [
            {"datum": d,
             "kcal": round(v["kcal"]), "kh": round(v["kh"]),
             "eiwit": round(v["eiwit"]), "vet": round(v["vet"]),
             "groenten": round(v["groenten"]), "fruit": round(v["fruit"]),
             "nd": _nd_score(v)}
            for d, v in sorted(dagen.items())
        ],
        "dagdelen": [
            {"moment": m, "naam": MOMENT_NAMEN.get(m, "Moment " + str(m)),
             "kh": round(p["kh"] / n_dagen), "eiwit": round(p["eiwit"] / n_dagen),
             "vet": round(p["vet"] / n_dagen)}
            for m, p in sorted(per_moment.items())
        ],
        "trainingen": trainingen,
    }


@app.get("/api/fuelc/bevoorrading")
async def bevoorrading(van: str, tot: str, user=Depends(get_current_user),
                       supabase: Client = Depends(get_supabase)):
    return _bereken_bevoorrading(user.id, van, tot, supabase)


@app.get("/api/coach/klant/{klant_id}/bevoorrading")
async def bevoorrading_coach(klant_id: str, van: str, tot: str,
                             user=Depends(get_current_user),
                             supabase: Client = Depends(get_supabase)):
    _verifieer_coach_klant(user.id, klant_id, supabase)
    return _bereken_bevoorrading(klant_id, van, tot, supabase)


`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - de rekenroute staat er.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Bevoorrading rekenroute" && git push origin HEAD:main');
