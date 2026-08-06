// patch-api-scores.js
// Sluit de sterrenbeoordeling aan:
//   POST /api/fuelc/recepten/{id}/score   — stemmen (één stem per klant)
//   De receptenlijst krijgt gemiddelde, aantal_scores en mijn_score mee.
//   De publieke feed neemt voortaan ook recepten op die goed scoren.
//
// Drempel voor de feed: gemiddeld 4 sterren of meer, met minstens
// 3 stemmen. Je eigen handmatige vlag blijft daarnaast bestaan.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-scores.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('SCORES-V1')) {
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

fs.writeFileSync(pad + '.bak-scores', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-scores');

// ─── 1. hulpfunctie en stemroute ───────────────────────────────────────────
vervang(
  'stemroute toegevoegd',
  '@app.delete("/api/fuelc/recepten/{recept_id}")',
  `# SCORES-V1 — beoordelingen van recepten
SCORE_MIN_STEMMEN = 3      # minder dan dit telt niet mee voor de feed
SCORE_MIN_GEMIDDELDE = 4.0


def _scores_per_recept(supabase: Client, eigen_user_id: str = None) -> dict:
    """Geeft per recept het gemiddelde, het aantal stemmen en eventueel
    de eigen stem. Faalt stil: zonder scores werkt de app gewoon door."""
    uit: dict = {}
    try:
        r = supabase.table("fuelc_recept_scores").select("recept_id,user_id,score").limit(5000).execute()
        per: dict = {}
        for x in (r.data or []):
            rid = str(x.get("recept_id"))
            per.setdefault(rid, []).append(x)
        for rid, rijen in per.items():
            punten = [float(y.get("score") or 0) for y in rijen if y.get("score")]
            if not punten:
                continue
            eigen = None
            if eigen_user_id:
                for y in rijen:
                    if str(y.get("user_id")) == str(eigen_user_id):
                        eigen = y.get("score")
                        break
            uit[rid] = {
                "gemiddelde": round(sum(punten) / len(punten), 1),
                "aantal_scores": len(punten),
                "mijn_score": eigen,
            }
    except Exception:
        pass
    return uit


class ReceptScore(BaseModel):
    score: int


@app.post("/api/fuelc/recepten/{recept_id}/score")
async def recept_score(recept_id: str, item: ReceptScore, user=Depends(get_current_user),
                       supabase: Client = Depends(get_supabase)):
    """Eén stem per klant per recept. Opnieuw stemmen overschrijft de vorige."""
    if not 1 <= int(item.score) <= 5:
        raise HTTPException(400, "Score moet tussen 1 en 5 liggen")
    supabase.table("fuelc_recept_scores").upsert({
        "recept_id": recept_id,
        "user_id": user.id,
        "score": int(item.score),
    }, on_conflict="recept_id,user_id").execute()

    scores = _scores_per_recept(supabase, user.id).get(str(recept_id), {})
    return {"ok": True, **scores}


@app.delete("/api/fuelc/recepten/{recept_id}")`
);

// ─── 2. de lijst krijgt de scores mee ──────────────────────────────────────
vervang(
  'scores in de receptenlijst',
  '    for _x in rijen:\n        _x["van_mij"] = str(_x.get("user_id")) == str(user.id)\n    return {"recepten": rijen}',
  '    _sc = _scores_per_recept(supabase, user.id)\n' +
  '    for _x in rijen:\n' +
  '        _x["van_mij"] = str(_x.get("user_id")) == str(user.id)\n' +
  '        _x.update(_sc.get(str(_x.get("id")), {"gemiddelde": None, "aantal_scores": 0, "mijn_score": None}))\n' +
  '    return {"recepten": rijen}'
);

// ─── 3. goede scores komen op de feed ──────────────────────────────────────
vervang(
  'goede scores komen op de feed',
  '    r = supabase.table("fuelc_recepten_eigen").select("*") \\\n        .eq("is_globaal", True).eq("publiek", True).order("naam").limit(200).execute()\n    return {"recepten": [_recept_veilig(x) for x in (r.data or [])]}',
  '    # SCORES-V1 — op de feed staat wat bewust gedeeld is, plus wat goed scoort\n' +
  '    r = supabase.table("fuelc_recepten_eigen").select("*") \\\n' +
  '        .eq("is_globaal", True).order("naam").limit(400).execute()\n' +
  '    sc = _scores_per_recept(supabase)\n' +
  '    uit = []\n' +
  '    for x in (r.data or []):\n' +
  '        s = sc.get(str(x.get("id")), {})\n' +
  '        verdient = (s.get("aantal_scores", 0) >= SCORE_MIN_STEMMEN\n' +
  '                    and (s.get("gemiddelde") or 0) >= SCORE_MIN_GEMIDDELDE)\n' +
  '        if x.get("publiek") or verdient:\n' +
  '            veilig = _recept_veilig(x)\n' +
  '            veilig["gemiddelde"] = s.get("gemiddelde")\n' +
  '            veilig["aantal_scores"] = s.get("aantal_scores", 0)\n' +
  '            uit.append(veilig)\n' +
  '    return {"recepten": uit}'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - ' + stappen.length + ' wijzigingen toegepast:');
stappen.forEach(s => console.log('  - ' + s));
console.log('');
console.log('Vergeet de unieke sleutel op fuelc_recept_scores niet.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Receptbeoordelingen" && git push origin HEAD:main');
