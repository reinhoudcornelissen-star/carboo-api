#!/usr/bin/env python3
"""
push-diagnose.py — stuurt een testmelding naar pushabonnementen in Carboo
en schrijft per rij weg wat de pushdienst antwoordde.

Gebruik (vanuit C:\\Users\\reinhoud\\Documents\\Carbs\\carboo-api):

    python push-diagnose.py --droog        # niets versturen, alleen tonen
    python push-diagnose.py                # alleen JOUW eigen toestellen
    python push-diagnose.py --iedereen     # alle actieve toestellen, ook van klanten

LET OP: zonder --droog krijgen mensen een echte melding op hun telefoon.
Begin met --droog, dan zonder vlag, en pas daarna met --iedereen.

Terugdraaien is niet nodig: het script verstuurt en noteert, het verwijdert niets.
Enige wijziging aan de data is actief = false bij een 404/410, wat de
bestaande opruimlogica sowieso al doet.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone

REINHOUD = "24605703-c6eb-4194-af80-7a22edec0581"

# ---------------------------------------------------------------- afhankelijkheden

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env is optioneel als de variabelen al in de omgeving staan

try:
    from supabase import create_client
except ImportError:
    sys.exit("Ontbreekt: supabase.  Installeer met:  pip install supabase")

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    sys.exit("Ontbreekt: pywebpush.  Installeer met:  pip install pywebpush")

# ---------------------------------------------------------------- omgeving

def env(*namen):
    """Eerste variabele die gevuld is, want de naamgeving verschilt per omgeving."""
    for n in namen:
        w = os.environ.get(n)
        if w:
            return w
    return None

SUPABASE_URL = env("SUPABASE_URL")
SUPABASE_KEY = env("SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY")
VAPID_PRIVATE = env("VAPID_PRIVATE_KEY")
VAPID_CONTACT = env("VAPID_CONTACT")

ontbreekt = [n for n, w in [
    ("SUPABASE_URL", SUPABASE_URL),
    ("SUPABASE_SERVICE_KEY", SUPABASE_KEY),
    ("VAPID_PRIVATE_KEY", VAPID_PRIVATE),
    ("VAPID_CONTACT", VAPID_CONTACT),
] if not w]

if ontbreekt:
    print("Deze omgevingsvariabelen ontbreken:", ", ".join(ontbreekt))
    print("Zet ze in een .env naast dit script, of haal ze uit Render >")
    print("service carboo-api > Environment.  Het script stopt hier.")
    sys.exit(1)

if VAPID_CONTACT and not VAPID_CONTACT.startswith("mailto:"):
    VAPID_CONTACT = "mailto:" + VAPID_CONTACT

# ---------------------------------------------------------------- argumenten

p = argparse.ArgumentParser()
p.add_argument("--iedereen", action="store_true",
               help="ook de toestellen van klanten, niet alleen die van jezelf")
p.add_argument("--droog", action="store_true",
               help="niets versturen, alleen tonen welke rijen aan de beurt zijn")
p.add_argument("--ook-inactief", action="store_true",
               help="ook rijen met actief = false meenemen (om te zien of ze echt dood zijn)")
args = p.parse_args()

# ---------------------------------------------------------------- ophalen

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

vraag = sb.table("fuelc_push_abonnementen").select(
    "id, user_id, endpoint, p256dh, auth, actief, user_agent"
)
if not args.ook_inactief:
    vraag = vraag.eq("actief", True)
if not args.iedereen:
    vraag = vraag.eq("user_id", REINHOUD)

rijen = vraag.execute().data or []

if not rijen:
    print("Geen abonnementen gevonden met deze filters.")
    sys.exit(0)

bereik = "alle klanten" if args.iedereen else "alleen jouw eigen toestellen"
print(f"\n{len(rijen)} abonnement(en) gevonden — bereik: {bereik}")
if args.droog:
    print("DROGE LOOP: er wordt niets verstuurd en niets weggeschreven.\n")
else:
    print("Er wordt nu een echte melding verstuurd.\n")

# ---------------------------------------------------------------- versturen

# Zelfde vorm als stuur_push() in main.py; sw.js leest titel/tekst/url/tag.
LADING = json.dumps({
    "titel": "Carboo",
    "tekst": "Je meldingen werken. Je krijgt voortaan bericht van je coach.",
    "url": "/app/fueling",
    "tag": "diagnose",
})

def kort(s, n=46):
    s = s or ""
    return s if len(s) <= n else s[:n - 1] + "\u2026"

def dienst(endpoint):
    if "fcm.googleapis.com" in endpoint:
        return "FCM (Android/Chrome)"
    if "notify.windows.com" in endpoint:
        return "WNS (Edge/Windows)"
    if "push.apple.com" in endpoint:
        return "Apple"
    if "mozilla.com" in endpoint:
        return "Mozilla"
    return "onbekend"

nu = datetime.now(timezone.utc).isoformat()
telling = {"gelukt": 0, "dood": 0, "fout": 0, "overgeslagen": 0}
verslag = []

for r in rijen:
    label = f"{r['user_id'][:8]}  {dienst(r['endpoint']):<20}"

    if args.droog:
        verslag.append((label, "zou versturen", kort(r.get("user_agent"))))
        telling["overgeslagen"] += 1
        continue

    if not r.get("p256dh") or not r.get("auth"):
        verslag.append((label, "GEEN SLEUTELS", "rij onbruikbaar"))
        telling["fout"] += 1
        continue

    try:
        webpush(
            subscription_info={
                "endpoint": r["endpoint"],
                "keys": {"p256dh": r["p256dh"], "auth": r["auth"]},
            },
            data=LADING,
            vapid_private_key=VAPID_PRIVATE,
            vapid_claims={"sub": VAPID_CONTACT},
            ttl=60,
        )
        # actief bewust niet aanraken: met --ook-inactief zou een toestel dat
        # de klant zelf uitzette anders weer meldingen krijgen van de backend.
        sb.table("fuelc_push_abonnementen").update({
            "laatste_succes_op": nu,
            "laatste_fout": None,
        }).eq("id", r["id"]).execute()

        verslag.append((label, "GELUKT", kort(r.get("user_agent"))))
        telling["gelukt"] += 1

    except WebPushException as e:
        code = getattr(e.response, "status_code", None)
        wijziging = {"laatste_fout": str(code or "fout"), "laatste_fout_op": nu}

        if code in (404, 410):
            wijziging["actief"] = False
            uitkomst = f"DOOD ({code}) — op inactief gezet"
            telling["dood"] += 1
        else:
            uitkomst = f"FOUT ({code or type(e).__name__})"
            telling["fout"] += 1

        sb.table("fuelc_push_abonnementen").update(wijziging).eq("id", r["id"]).execute()
        verslag.append((label, uitkomst, kort(str(e), 60)))

    except Exception as e:
        sb.table("fuelc_push_abonnementen").update({
            "laatste_fout": type(e).__name__,
            "laatste_fout_op": nu,
        }).eq("id", r["id"]).execute()
        verslag.append((label, f"FOUT ({type(e).__name__})", kort(str(e), 60)))
        telling["fout"] += 1

# ---------------------------------------------------------------- verslag

print("-" * 100)
for label, uitkomst, extra in verslag:
    print(f"{label}  {uitkomst:<28}  {extra}")
print("-" * 100)

if args.droog:
    print(f"{telling['overgeslagen']} rijen zouden een melding krijgen.")
else:
    print(f"gelukt {telling['gelukt']}   dood {telling['dood']}   fout {telling['fout']}")
    print("\nDe kolommen laatste_succes_op, laatste_fout en laatste_fout_op zijn bijgewerkt.")
    print("Controleer in Supabase:")
    print("  select user_id, actief, laatste_succes_op, laatste_fout, laatste_fout_op")
    print("  from fuelc_push_abonnementen order by laatste_succes_op desc nulls last;")
