// patch-api-categoriewoorden.js
// Voegt twee dingen toe aan main.py:
//   GET /api/categorie-woorden      — de lijst, voor de app
//   herken_categorie(naam, cat)     — dezelfde herkenning in Python,
//                                     voor het weekrapport
//
// De lijst wordt vijf minuten in het geheugen gehouden, zodat een
// wijziging in de database snel doorkomt zonder elke keer te bevragen.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-categoriewoorden.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('CATWOORDEN-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '@app.get("/api/publiek/wedstrijden")';
if (f.split(anker).length - 1 !== 1) {
  console.error('FOUT: anker niet gevonden.');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-catwoorden', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-catwoorden');

const blok = `# ── CATWOORDEN-V1 — categorieherkenning op basis van de database ──────

import re as _re
import time as _time

_catwoorden_cache = {"tijd": 0.0, "data": None}


def _haal_catwoorden(supabase: Client) -> list:
    """De woordenlijst, vijf minuten vastgehouden."""
    nu = _time.time()
    if _catwoorden_cache["data"] is not None and nu - _catwoorden_cache["tijd"] < 300:
        return _catwoorden_cache["data"]
    try:
        r = supabase.table("fuelc_categorie_woorden") \\
            .select("woord,categorie").eq("actief", True).limit(2000).execute()
        rijen = r.data or []
    except Exception:
        rijen = _catwoorden_cache["data"] or []
    _catwoorden_cache["tijd"] = nu
    _catwoorden_cache["data"] = rijen
    return rijen


def _bevat_woord(naam: str, woord: str) -> bool:
    """Het woord moet aan het BEGIN van een woord staan.
    Zo matcht "uien" wel op "ui", maar "bruisend" niet."""
    return bool(_re.search(r"(^|[^a-z0-9])" + _re.escape(woord), naam))


def herken_categorie(naam: str, cat: str, supabase: Client) -> str:
    """Zelfde uitkomst als normaliseerCategorie in de app.
    Alleen "Groenten en fruit" wordt gesplitst; de rest blijft zoals ze is."""
    c = (cat or "").lower().strip()
    n = (naam or "").lower().strip()

    if c in ("groenten en fruit", "groenten & fruit"):
        woorden = _haal_catwoorden(supabase)
        # eerst de knollen, die horen niet bij groenten of fruit
        for w in woorden:
            if w["categorie"] == "Granen & brood" and _bevat_woord(n, w["woord"]):
                return "Granen & brood"
        for w in woorden:
            if w["categorie"] == "Groenten" and _bevat_woord(n, w["woord"]):
                return "Groenten"
        for w in woorden:
            if w["categorie"] == "Fruit" and _bevat_woord(n, w["woord"]):
                return "Fruit"
        return "Groenten"

    return cat or "Overige"


@app.get("/api/categorie-woorden")
async def categorie_woorden(supabase: Client = Depends(get_supabase)):
    """De woordenlijst voor de app. Geen persoonsgegevens, dus geen login nodig."""
    return {"woorden": _haal_catwoorden(supabase)}


`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - route en herkenning toegevoegd.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Categoriewoorden uit de database" && git push origin HEAD:main');
console.log('');
console.log('Testen na de deploy:');
console.log('  https://carboo-api-fra.onrender.com/api/categorie-woorden');
