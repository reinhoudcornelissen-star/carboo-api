"""
diagnose/broer.py — leest (alleen lezen) per gebruiker hoeveel pushtoestellen
actief, dood (404/410) of inactief zonder foutcode zijn, en of elke rij zonder
foutcode een actieve "broer" heeft op hetzelfde soort toestel.

Gebruik (vanuit carboo-api):   python lokaal-start.py diagnose/broer.py
Let op: op Android meldt Chrome voor elk toestel "Android 10; K"; de
user_agent is daar dus een zwakke vingerafdruk.
"""
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client

v = dotenv_values(Path(__file__).resolve().parent.parent / ".env")
sb = create_client(v["SUPABASE_URL"], v["SUPABASE_SERVICE_KEY"])
rijen = sb.table("fuelc_push_abonnementen") \
    .select("id, user_id, actief, user_agent, laatste_fout").execute().data or []
IK = "24605703-c6eb-4194-af80-7a22edec0581"

def toestel(ua):
    ua = ua or ""
    plat = "Android" if "Android" in ua else "Windows" if "Windows" in ua else "Mac" if "Macintosh" in ua else "iPhone" if "iPhone" in ua else "?"
    m = re.search(r"Edg/(\d+)", ua) or re.search(r"Chrome/(\d+)", ua) or re.search(r"Version/(\d+).*Safari", ua)
    br = ("Edge" if "Edg/" in ua else "Chrome" if "Chrome/" in ua else "Safari" if "Safari" in ua else "?")
    return f"{plat} {br} {m.group(1) if m else '?'}"

def soort(r):
    if r["actief"]: return "actief"
    return "dood" if (r.get("laatste_fout") or "") in ("404", "410") else "zonder code"

per = defaultdict(list)
for r in rijen: per[r["user_id"]].append(r)

print(f"{date.today()}  —  {len(rijen)} rijen, {len(per)} gebruikers\n")
print(f"{'klant':<14}{'actief':>7}{'404/410':>9}{'zonder code':>13}   oordeel")
print("-" * 70)
klanten_ok = klanten_weg = 0
for uid, rs in sorted(per.items(), key=lambda kv: (kv[0] != IK, kv[0])):
    t = defaultdict(int)
    for r in rs: t[soort(r)] += 1
    naam = uid[:8] + (" (jij)" if uid == IK else "")
    if t["actief"]:
        oordeel = "minstens 1 actieve rij"
        if uid != IK: klanten_ok += 1
    else:
        oordeel = "ALLEEN INACTIEVE RIJEN -> zelf aanspreken"
        if uid != IK: klanten_weg += 1
    print(f"{naam:<14}{t['actief']:>7}{t['dood']:>9}{t['zonder code']:>13}   {oordeel}")
print("-" * 70)
print(f"Klanten (zonder jou): {klanten_ok} met actieve rij, {klanten_weg} met alleen inactieve rijen\n")

print("Raadselrijen (inactief, geen foutcode):")
print(f"{'klant':<14}{'toestel':<22}broer")
print("-" * 70)
for uid, rs in sorted(per.items(), key=lambda kv: (kv[0] != IK, kv[0])):
    actieve = [toestel(r["user_agent"]) for r in rs if r["actief"]]
    for r in rs:
        if soort(r) != "zonder code": continue
        tt = toestel(r["user_agent"])
        if tt in actieve: b = "ja, zelfde toestel+versie actief"
        elif any(a.rsplit(" ", 1)[0] == tt.rsplit(" ", 1)[0] for a in actieve): b = "ja, zelfde soort toestel, andere versie (update?)"
        elif actieve: b = "alleen een ANDER soort toestel actief: " + ", ".join(sorted(set(actieve)))
        else: b = "GEEN BROER"
        print(f"{uid[:8] + (' (jij)' if uid == IK else ''):<14}{tt:<22}{b}")

print("\nActieve rijen per gebruiker (toestel):")
for uid, rs in sorted(per.items(), key=lambda kv: (kv[0] != IK, kv[0])):
    a = [toestel(r["user_agent"]) for r in rs if r["actief"]]
    if a: print(f"  {uid[:8] + (' (jij)' if uid == IK else ''):<14}" + ", ".join(a))
