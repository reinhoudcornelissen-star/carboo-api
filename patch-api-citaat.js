// patch-api-citaat.js
// Voegt toe aan main.py:
//   GET /api/publiek/citaat?week=32
//
// Geen login nodig; het is geen persoonsgegeven.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-citaat.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('CITAAT-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '@app.get("/api/publiek/wedstrijden")';
if (f.split(anker).length - 1 !== 1) {
  console.error('FOUT: anker niet gevonden.');
  process.exit(1);
}

fs.writeFileSync(pad + '.bak-citaat', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-citaat');

const blok = `# ── CITAAT-V1 — het citaat van de week ────────────────────────────────

@app.get("/api/publiek/citaat")
async def publiek_citaat(week: int = 1, supabase: Client = Depends(get_supabase)):
    """Het citaat dat bij dit weeknummer hoort. Bestaat het niet,
    dan komt er niets terug en toont de app gewoon geen blok."""
    nr = ((int(week) - 1) % 52) + 1
    try:
        r = supabase.table("fuelc_citaten").select("week_nr,tekst,auteur,context") \\
            .eq("week_nr", nr).eq("actief", True).limit(1).execute()
        return (r.data or [{}])[0]
    except Exception:
        return {}


`;

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('OK - de route staat er.');
console.log('');
console.log('  python -m py_compile main.py');
console.log('  git add -A && git commit -m "Citaat van de week" && git push origin HEAD:main');
console.log('');
console.log('Testen na de deploy:');
console.log('  https://carboo-api-fra.onrender.com/api/publiek/citaat?week=32');
