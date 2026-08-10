// patch-api-inzichten.js
// De bevoorrading geeft nu ook inzichten terug in plaats van alleen
// cijfers: een kop, een inleidende regel over het loggen, en per
// sectie drie tot vier vaststellingen met een ernstkleur.
//
// De cijfers blijven meekomen — het rapport toont ze niet meer los,
// maar ze zitten wel in de zinnen verwerkt.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-inzichten.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('INZICHTEN-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}
if (!f.includes('BEVOORRADING-V1')) {
  console.error('FOUT: draai eerst patch-api-bevoorrading.js.');
  process.exit(1);
}

const stappen = [];
function vervang(naam, zoek, nieuw) {
  const n = f.split(zoek).length - 1;
  if (n !== 1) { console.error('FOUT bij "' + naam + '": anker komt ' + n + 'x voor (verwacht 1).'); process.exit(1); }
  f = f.replace(zoek, nieuw);
  stappen.push(naam);
}

fs.writeFileSync(pad + '.bak-inzichten', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-inzichten');

// ─── 1. het profiel ophalen, want de doelen zitten daarin ──────────────────
vervang(
  'profiel opgehaald',
  '    gewicht = None\n    gewogen_op = None',
  '    # INZICHTEN-V1 — de doelen komen uit het profiel\n' +
  '    profiel = {}\n' +
  '    try:\n' +
  '        pr = supabase.table("fuelc_profiel") \\\n' +
  '            .select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg") \\\n' +
  '            .eq("user_id", user_id).limit(1).execute().data or []\n' +
  '        profiel = pr[0] if pr else {}\n' +
  '    except Exception:\n' +
  '        profiel = {}\n' +
  '\n' +
  '    gewicht = None\n    gewogen_op = None'
);

// ─── 2. de inzichtenbouwer ─────────────────────────────────────────────────
vervang(
  'inzichtenbouwer toegevoegd',
  '@app.get("/api/fuelc/bevoorrading")',
  `# ── INZICHTEN-V1 — van cijfers naar vaststellingen ────────────────────

DAGNAAM = ["maandag", "dinsdag", "woensdag", "donderdag",
           "vrijdag", "zaterdag", "zondag"]


def _dagnaam(datum: str) -> str:
    try:
        from datetime import date
        d = date.fromisoformat(str(datum)[:10])
        return DAGNAAM[d.weekday()]
    except Exception:
        return str(datum)


def _standfirst(dagen_gelogd: int, laagste_dag: str) -> str:
    """De inleidende regel. Goed loggen wordt bekrachtigd; slecht loggen
    krijgt een eerlijke waarschuwing in plaats van een compliment."""
    if dagen_gelogd >= 7:
        return ("Zeven dagen op zeven gelogd — daar is dit rapport op gebouwd. "
                "De meeste dagen zaten dicht bij je doel; " + laagste_dag +
                " week af, en daar begint het verhaal.")
    if dagen_gelogd >= 5:
        return (str(dagen_gelogd) + " van de zeven dagen gelogd. Genoeg om een lijn te zien, "
                "maar de ontbrekende dagen tellen niet mee in wat hieronder staat.")
    return (str(dagen_gelogd) + " van de zeven dagen gelogd. Dit rapport steunt dus op een deel "
            "van je week — lees het met die beperking in gedachten.")


def _bouw_inzichten(res: dict, dagen: dict, profiel: dict, trainingen: list) -> dict:
    d = res["per_dag"]
    kwaliteit = []
    macros = []

    def voeg(lijst, ernst, kop, tekst):
        lijst.append({"ernst": ernst, "kop": kop, "tekst": tekst})

    # ── kwaliteit ───────────────────────────────────────────────────
    lage_groentedagen = len([v for v in dagen.values() if v["groenten"] < 200])
    if d["groenten"] < 250:
        voeg(kwaliteit, "geel", "Je groenten blijven achter",
             ("Op " + str(lage_groentedagen) + " van de " + str(len(dagen)) +
              " dagen bleef je onder de 200 gram. Eén extra portie per dag tilt meteen ook je "
              "vezels en kalium mee omhoog — die twee volgen je groenten."))
    elif d["groenten"] >= 300:
        voeg(kwaliteit, "groen", "Je groenten zitten op peil",
             "Gemiddeld boven de 300 gram per dag. Dat is waar je vezels en kalium vandaan komen.")

    kcal = max(d["kcal"], 1)
    pct_toeg = (d["suikers_toegevoegd"] * 4 / kcal) * 100
    if pct_toeg > 10:
        voeg(kwaliteit, "rood", "Te veel toegevoegde suiker",
             ("Toegevoegde suikers leverden " + str(round(pct_toeg)) + "% van je energie. "
              "De WHO houdt 10% aan als bovengrens, en onder de 5% als streefwaarde."))
    else:
        voeg(kwaliteit, "groen", "Je suikers zitten goed",
             ("Toegevoegde suikers bleven op " + str(round(pct_toeg)) + "% van je energie, "
              "onder de bovengrens van de WHO. Het grootste deel van je koolhydraten is zetmeel, "
              "en dat is precies wat je wil."))

    vet_tot = max(d["verzadigd"] + d["onverzadigd"], 1)
    pct_verz = (d["verzadigd"] / vet_tot) * 100
    if pct_verz > 33:
        voeg(kwaliteit, "rood", "Een derde van je vet is verzadigd",
             ("Onder de 30% is het streven. Verzadigd vet komt meestal uit kaas, boter en vet vlees; "
              "één van die bronnen vervangen brengt je er meestal onder."))
    elif pct_verz < 28:
        voeg(kwaliteit, "groen", "Je vetverdeling is in orde",
             ("Ruim twee derde van je vet is onverzadigd. Dat is de verhouding waar je naartoe wil."))

    if d["omega3"] < 1.5:
        voeg(kwaliteit, "geel", "Weinig omega 3",
             ("Je komt op " + str(d["omega3"]) + " gram per dag, tegenover een richtlijn van 1,5. "
              "Twee porties vette vis per week brengt je daar meestal."))

    if d["vezels"] < 30 and d["groenten"] >= 250:
        voeg(kwaliteit, "geel", "Je vezels blijven onder de richtlijn",
             (str(d["vezels"]) + " gram per dag tegenover 30 als richtlijn. Volkoren in plaats van wit "
              "brood of pasta is de snelste weg."))

    # ── macro's ─────────────────────────────────────────────────────
    e_doel = float(profiel.get("energie_doel") or 0)
    kh_pct = float(profiel.get("kh_doel_pct") or 50)

    tr_per_dag = {}
    for t in trainingen:
        tr_per_dag[str(t.get("datum"))] = tr_per_dag.get(str(t.get("datum")), 0) + (t.get("kcal_verbranding") or 0)

    dagpct = []
    for datum, v in dagen.items():
        if e_doel <= 0:
            continue
        doel_kh = (e_doel * kh_pct / 100 + tr_per_dag.get(datum, 0)) / 4
        if doel_kh > 0:
            dagpct.append((datum, v["kh"] / doel_kh))

    laagste_dag = ""
    if dagpct:
        dagpct.sort(key=lambda x: x[1])
        slechtste, pct_slecht = dagpct[0]
        binnen10 = len([p for _, p in dagpct if 0.9 <= p <= 1.1])
        laagste_dag = _dagnaam(slechtste)

        if pct_slecht < 0.6:
            voeg(macros, "geel", _dagnaam(slechtste).capitalize() + " valt uit de rij",
                 ("Op die dag haalde je " + str(round(pct_slecht * 100)) + "% van je koolhydraatdoel, "
                  "terwijl de rest van de week er dicht bij zat."))
        if binnen10 >= len(dagpct) - 1 and len(dagpct) >= 5:
            voeg(macros, "groen", "Je koolhydraten volgen je training",
                 ("Op " + str(binnen10) + " van de " + str(len(dagpct)) + " dagen zat je binnen tien procent "
                  "van je doel — ook op je trainingsdagen, en dat is het lastigste stuk."))

    dagdelen = res.get("dagdelen") or []
    if dagdelen:
        zwaarste = max(dagdelen, key=lambda m: m["eiwit"])
        lichtste = min([m for m in dagdelen if m["moment"] in (0, 2, 4)] or dagdelen,
                       key=lambda m: m["eiwit"])
        if zwaarste["eiwit"] > 40:
            voeg(macros, "rood", "Je eiwit staat scheef verdeeld",
                 (str(zwaarste["eiwit"]) + " gram in je " + zwaarste["naam"].lower() +
                  " tegenover " + str(lichtste["eiwit"]) + " in je " + lichtste["naam"].lower() +
                  ". Meer dan veertig gram in één maaltijd benut je niet volledig; verschuiven kost je niets extra."))

    # ── de kop ──────────────────────────────────────────────────────
    rood = [i for i in (macros + kwaliteit) if i["ernst"] == "rood"]
    geel = [i for i in (macros + kwaliteit) if i["ernst"] == "geel"]

    if laagste_dag and any("valt uit de rij" in i["kop"] for i in macros):
        kop = laagste_dag.capitalize() + " is de dag die eruit springt."
    elif rood:
        kop = rood[0]["kop"] + "."
    elif geel:
        kop = geel[0]["kop"] + "."
    else:
        kop = "Een week zonder uitschieters."

    return {
        "kop": kop,
        "standfirst": _standfirst(res["dagen_gelogd"], laagste_dag or "één dag"),
        "inzichten_kwaliteit": kwaliteit[:4],
        "inzichten_macros": macros[:3],
    }


@app.get("/api/fuelc/bevoorrading")`
);

// ─── 3. de inzichten meesturen ─────────────────────────────────────────────
vervang(
  'inzichten aan het antwoord toegevoegd',
  '    return {\n        "van": van, "tot": tot,',
  '    res = {\n        "van": van, "tot": tot,'
);

vervang(
  'antwoord afgerond',
  '        "trainingen": trainingen,\n    }\n\n\n# ── INZICHTEN-V1',
  '        "trainingen": trainingen,\n' +
  '    }\n' +
  '    try:\n' +
  '        res.update(_bouw_inzichten(res, dagen, profiel, tr))\n' +
  '    except Exception as e:\n' +
  '        res.update({"kop": "", "standfirst": "", "inzichten_kwaliteit": [],\n' +
  '                    "inzichten_macros": [], "inzichten_fout": str(e)})\n' +
  '    return res\n\n\n# ── INZICHTEN-V1'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - ' + stappen.length + ' wijzigingen toegepast:');
stappen.forEach(s => console.log('  - ' + s));
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Bevoorrading geeft inzichten" && git push origin HEAD:main');
