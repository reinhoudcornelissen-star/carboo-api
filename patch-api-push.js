// patch-api-push.js
// Voegt web push toe aan main.py:
//   POST /api/push/abonneren     — toestel opslaan
//   POST /api/push/afmelden      — toestel uitzetten
//   POST /api/push/vernieuwen    — abonnement vervangen (door de service worker)
//   POST /api/push/test          — testmelding naar jezelf
//   stuur_push(user_id, ...)     — hulpfunctie om vanuit de rest van main.py te gebruiken
//
// Vereist: pywebpush in requirements.txt en drie omgevingsvariabelen
// in Render: VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CONTACT
//
// Draaien vanuit de root van carboo-api:
//    node patch-api-push.js

const fs = require('fs');

const pad = 'main.py';

if (!fs.existsSync(pad)) {
  console.error('FOUT: main.py niet gevonden. Draai dit vanuit de map carboo-api.');
  process.exit(1);
}

let f = fs.readFileSync(pad, 'utf8');

if (f.includes('WEBPUSH-V1')) {
  console.log('Deze patch is al toegepast. Niets gedaan.');
  process.exit(0);
}

const anker = '@app.get("/api/fuelc/welzijn")';
const aantal = f.split(anker).length - 1;
if (aantal !== 1) {
  console.error('FOUT: anker komt ' + aantal + 'x voor (verwacht 1).');
  process.exit(1);
}

const bak = pad + '.bak-webpush';
fs.writeFileSync(bak, f, 'utf8');
console.log('Back-up geschreven: ' + bak);

const blok = `# ============================================================
# WEBPUSH-V1 — meldingen naar de telefoon
# ============================================================

class PushAbonnement(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


def _vapid():
    """Sleutels uit de omgeving. Ontbreken ze, dan doet push niets
    en blijft de rest van de app gewoon werken."""
    prive = os.environ.get("VAPID_PRIVATE_KEY")
    contact = os.environ.get("VAPID_CONTACT", "mailto:info@carboo.app")
    return prive, contact


def stuur_push(user_id: str, titel: str, tekst: str,
               url: str = "/app/fueling", tag: str = "carboo",
               soort: str = "algemeen", supabase: Client = None):
    """Stuurt een melding naar alle actieve toestellen van een gebruiker.
    Faalt stil: een melding die niet aankomt mag nooit een verzoek breken."""
    prive, contact = _vapid()
    if not prive or supabase is None:
        return 0

    # voorkeur van de klant respecteren
    try:
        v = supabase.table("fuelc_push_voorkeuren").select("aan") \\
            .eq("user_id", user_id).eq("soort", soort).execute()
        if v.data and v.data[0].get("aan") is False:
            return 0
    except Exception:
        pass

    try:
        r = supabase.table("fuelc_push_abonnementen").select("*") \\
            .eq("user_id", user_id).eq("actief", True).execute()
        abos = r.data or []
    except Exception:
        return 0

    lading = json.dumps({"titel": titel, "tekst": tekst, "url": url, "tag": tag})
    verzonden = 0

    for a in abos:
        try:
            webpush(
                subscription_info={
                    "endpoint": a["endpoint"],
                    "keys": {"p256dh": a["p256dh"], "auth": a["auth"]},
                },
                data=lading,
                vapid_private_key=prive,
                vapid_claims={"sub": contact},
                ttl=86400,
            )
            verzonden += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            # 404 en 410 betekenen: dit toestel bestaat niet meer
            if code in (404, 410):
                try:
                    supabase.table("fuelc_push_abonnementen") \\
                        .update({"actief": False, "laatste_fout": str(code)}) \\
                        .eq("endpoint", a["endpoint"]).execute()
                except Exception:
                    pass
        except Exception:
            pass

    return verzonden


@app.get("/api/push/sleutel")
async def push_sleutel():
    return {"publiek": os.environ.get("VAPID_PUBLIC_KEY", "")}


@app.post("/api/push/abonneren")
async def push_abonneren(abo: PushAbonnement, user=Depends(get_current_user),
                         supabase: Client = Depends(get_supabase)):
    data = abo.dict()
    data["user_id"] = user.id
    data["actief"] = True
    data["laatste_fout"] = None
    supabase.table("fuelc_push_abonnementen").upsert(data, on_conflict="endpoint").execute()
    return {"status": "geabonneerd"}


@app.post("/api/push/afmelden")
async def push_afmelden(body: dict, user=Depends(get_current_user),
                        supabase: Client = Depends(get_supabase)):
    ep = body.get("endpoint")
    q = supabase.table("fuelc_push_abonnementen").update({"actief": False}).eq("user_id", user.id)
    if ep:
        q = q.eq("endpoint", ep)
    q.execute()
    return {"status": "afgemeld"}


@app.post("/api/push/vernieuwen")
async def push_vernieuwen(body: dict, supabase: Client = Depends(get_supabase)):
    """Wordt door de service worker aangeroepen, zonder token."""
    oud = body.get("oud_endpoint")
    nieuw = body.get("nieuw") or {}
    if not oud or not nieuw.get("endpoint"):
        return {"status": "genegeerd"}
    r = supabase.table("fuelc_push_abonnementen").select("user_id").eq("endpoint", oud).execute()
    if not r.data:
        return {"status": "onbekend"}
    keys = nieuw.get("keys") or {}
    supabase.table("fuelc_push_abonnementen").upsert({
        "user_id": r.data[0]["user_id"],
        "endpoint": nieuw["endpoint"],
        "p256dh": keys.get("p256dh", ""),
        "auth": keys.get("auth", ""),
        "actief": True,
    }, on_conflict="endpoint").execute()
    supabase.table("fuelc_push_abonnementen").update({"actief": False}).eq("endpoint", oud).execute()
    return {"status": "vernieuwd"}


@app.post("/api/push/test")
async def push_test(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    n = stuur_push(user.id, "Carboo", "Meldingen staan aan. Zo ziet het eruit.",
                   supabase=supabase)
    return {"verzonden": n}


`;

// importregels toevoegen bovenaan
const importAnker = 'from pydantic import BaseModel';
if (f.split(importAnker).length - 1 !== 1) {
  console.error('FOUT: import-anker "' + importAnker + '" is niet uniek of niet gevonden.');
  console.error('Voeg de imports dan handmatig toe:');
  console.error('  import os, json');
  console.error('  from pywebpush import webpush, WebPushException');
  process.exit(1);
}
f = f.replace(importAnker, importAnker + '\nfrom pywebpush import webpush, WebPushException');

f = f.replace(anker, blok + anker);
fs.writeFileSync(pad, f, 'utf8');

console.log('');
console.log('OK - push-routes toegevoegd aan main.py.');
console.log('');
console.log('Nog te doen:');
console.log('  1. pywebpush toevoegen aan requirements.txt');
console.log('  2. In Render drie omgevingsvariabelen zetten:');
console.log('     VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CONTACT');
console.log('  3. git add -A && git commit -m "Web push" && git push origin HEAD:main');
console.log('');
console.log('Controleer bovenaan main.py of "import os" en "import json" er staan.');
