"""
ontbrekende-ingredienten.py — geeft alle ingredientnamen uit de recepten die niet exact
voorkomen in de bibliotheek of in NEVO, met het aantal recepten waarin ze staan en een
suggestie voor de dichtstbijzijnde bestaande naam. Leest alleen.

    python ontbrekende-ingredienten.py
"""
import os
import sys
import difflib
from supabase import create_client

try:
    from nevo_data import NEVO
except ImportError:
    print("nevo_data.py ontbreekt.")
    sys.exit(1)

sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

bib_r = sb.table("fuelc_bibliotheek").select("naam").execute()
bib_namen = [(b.get("naam") or "").strip() for b in (bib_r.data or []) if b.get("naam")]
alle = {n.lower(): ("bib", n) for n in bib_namen}
for n in NEVO:
    alle.setdefault(n.strip().lower(), ("nevo", n))

r = sb.table("fuelc_recepten_eigen").select("naam,ingredienten").execute()
ontbreekt = {}
totaal_ing = 0
for x in (r.data or []):
    for i in (x.get("ingredienten") or []):
        if not isinstance(i, dict):
            continue
        inaam = (i.get("naam") or "").strip()
        if not inaam:
            continue
        totaal_ing += 1
        if inaam.lower() in alle:
            continue
        e = ontbreekt.setdefault(inaam, [])
        e.append(x.get("naam") or "?")

print(f"{totaal_ing} ingredientvermeldingen in {len(r.data or [])} recepten")
print(f"{len(ontbreekt)} unieke namen worden NIET exact teruggevonden\n")
print(f"{'ontbrekende naam':32} {'in':>3}  dichtstbijzijnde bestaande naam")
print("-" * 86)
sleutels = list(alle.keys())
for naam in sorted(ontbreekt, key=lambda n: -len(ontbreekt[n])):
    recs = ontbreekt[naam]
    dicht = difflib.get_close_matches(naam.lower(), sleutels, n=1, cutoff=0.6)
    sug = ""
    if dicht:
        bron, echt = alle[dicht[0]]
        sug = f"{echt}  [{bron}]"
    else:
        sug = "-- geen gelijkende naam --"
    print(f"{naam[:32]:32} {len(recs):3}  {sug}")

print()
print("Recepten per ontbrekende naam:")
for naam in sorted(ontbreekt, key=lambda n: -len(ontbreekt[n])):
    print(f"  {naam}: {', '.join(ontbreekt[naam][:5])}"
          + (" ..." if len(ontbreekt[naam]) > 5 else ""))
