// patch-api-meldingen.js
// Hangt pushmeldingen aan de vier bronroutes:
//   1. coach stuurt een bericht        -> alle actieve klanten van die coach
//   2. coach plaatst een opmerking     -> de betrokken klant
//   3. coach plant een training        -> de klant (alleen bij een nieuwe)
//   4. coach maakt een raceplan-concept-> de klant
//
// Het versturen gebeurt op een achtergrondthread, zodat een coach met
// vijftig klanten niet staat te wachten op vijftig HTTP-verzoeken.
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-meldingen.js

const fs = require('fs');

const pad = 'main.py';
if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('PUSHKOPPEL-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}
if (!f.includes('def stuur_push(')) {
  console.error('FOUT: stuur_push bestaat niet. Draai eerst patch-api-push.js.');
  process.exit(1);
}

const stappen = [];

function vervangRegex(naam, regex, nieuw) {
  const alle = f.match(new RegExp(regex.source, 'g'));
  if (!alle) { console.error('FOUT bij "' + naam + '": anker niet gevonden.'); process.exit(1); }
  if (alle.length > 1) { console.error('FOUT bij "' + naam + '": anker komt ' + alle.length + 'x voor.'); process.exit(1); }
  f = f.replace(regex, nieuw);
  stappen.push(naam);
}

fs.writeFileSync(pad + '.bak-pushkoppel', f, 'utf8');
console.log('Back-up geschreven: ' + pad + '.bak-pushkoppel');

// ─── 0. hulpfunctie voor achtergrondverzending ─────────────────────────────
vervangRegex(
  'achtergrondverzending toegevoegd',
  /@app\.get\("\/api\/push\/sleutel"\)/,
  'def stuur_push_async(*args, **kwargs):\n' +
  '    """PUSHKOPPEL-V1 — verstuurt op een aparte thread zodat het verzoek\n' +
  '    niet hoeft te wachten. Faalt stil, net als stuur_push zelf."""\n' +
  '    import threading\n' +
  '    try:\n' +
  '        threading.Thread(target=stuur_push, args=args, kwargs=kwargs, daemon=True).start()\n' +
  '    except Exception:\n' +
  '        pass\n' +
  '\n' +
  '\n' +
  '@app.get("/api/push/sleutel")'
);

// ─── 1. coach stuurt een bericht ───────────────────────────────────────────
vervangRegex(
  'coachbericht',
  /( *"type": item\.type or "bericht",\r?\n *\}\)\.execute\(\)\r?\n)( *return \{"ok": True, "id": r\.data\[0\]\["id"\] if r\.data else None\})/,
  '$1' +
  '    # PUSHKOPPEL-V1 — naar alle actieve klanten van deze coach\n' +
  '    try:\n' +
  '        _kl = supabase.table("carboo_coach_klanten").select("klant_id") \\\n' +
  '            .eq("coach_id", coach.data[0]["id"]).eq("status", "actief").limit(500).execute()\n' +
  '        for _k in (_kl.data or []):\n' +
  '            if _k.get("klant_id"):\n' +
  '                stuur_push_async(_k["klant_id"], "Bericht van je coach",\n' +
  '                                 (item.tekst or "")[:120], url="/app/coach-zone",\n' +
  '                                 tag="coachbericht", soort="coachbericht", supabase=supabase)\n' +
  '    except Exception:\n' +
  '        pass\n' +
  '$2'
);

// ─── 2. coach plaatst een opmerking ────────────────────────────────────────
vervangRegex(
  'coachopmerking',
  /( *"item_id": item\.item_id, "item_label": item\.item_label,\r?\n *\}\)\.execute\(\)\r?\n)( *return \{"ok": True, "id": r\.data\[0\]\["id"\] if r\.data else None\})/,
  '$1' +
  '    # PUSHKOPPEL-V1\n' +
  '    stuur_push_async(item.klant_id, "Opmerking van je coach",\n' +
  '                     (item.tekst or "")[:120], url="/app/coach-zone",\n' +
  '                     tag="coachopmerking", soort="coachopmerking", supabase=supabase)\n' +
  '$2'
);

// ─── 3. coach plant een training ───────────────────────────────────────────
// Alleen bij een nieuwe training. Een wijziging achteraf mag niet opnieuw trillen.
vervangRegex(
  'geplande training',
  /( *ins = supabase\.table\("fuelc_trainingen"\)\.insert\(payload\)\.execute\(\)\r?\n)( *return \{"ok": True, "id": ins\.data\[0\]\["id"\] if ins\.data else None\})/,
  '$1' +
  '    # PUSHKOPPEL-V1 — alleen bij een nieuwe training, niet bij een wijziging\n' +
  '    stuur_push_async(klant_id, "Nieuwe training gepland",\n' +
  '                     f"{payload[\'naam\']} op {datum}", url="/app/fueling",\n' +
  '                     tag="training", soort="training", supabase=supabase)\n' +
  '$2'
);

// ─── 4. raceplan-concept ───────────────────────────────────────────────────
vervangRegex(
  'raceplan-concept',
  /( *"door_coach": coach_id,\r?\n *\}\)\.execute\(\)\r?\n)( *return \{"ok": True, "id": r\.data\[0\]\["id"\] if r\.data else None\})/,
  '$1' +
  '    # PUSHKOPPEL-V1\n' +
  '    stuur_push_async(klant_id, "Je raceplan staat klaar",\n' +
  '                     naam, url="/app/race",\n' +
  '                     tag="raceplan", soort="raceplan", supabase=supabase)\n' +
  '$2'
);

fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - ' + stappen.length + ' wijzigingen toegepast:');
stappen.forEach(s => console.log('  - ' + s));
console.log('');
console.log('Volgende stappen:');
console.log('  git add -A && git commit -m "Pushmeldingen bij coachberichten, opmerkingen, trainingen en raceplannen"');
console.log('  git push origin HEAD:main');
console.log('');
console.log('Daarna in Render controleren of de deploy start.');
