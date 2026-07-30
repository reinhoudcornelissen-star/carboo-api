"""
zoek-product.py — zoekt een term in de bibliotheek en in NEVO en toont de voedingswaarden.

    python zoek-product.py havermout          # alleen jouw eigen producten
    python zoek-product.py havermout --alles  # ook die van klanten
"""
import os
import sys
from supabase import create_client

try:
    from nevo_data import NEVO
except ImportError:
    NEVO = {}

ALLES = "--alles" in sys.argv
ADMIN = "24605703-c6eb-4194-af80-7a22edec0581"
term = " ".join(a for a in sys.argv[1:] if not a.startswith("--")).strip().lower()
if not term:
    print("Geef een zoekterm mee, bijvoorbeeld: python zoek-product.py havermout")
    sys.exit(1)

sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

kop = f"{'naam':42} {'kcal':>5} {'kh':>6} {'suik':>5} {'vez':>5} {'eiw':>5} {'vet':>5} {'gi':>4}"

b = sb.table("fuelc_bibliotheek").select(
    "naam,categorie,portie_g,kcal_100g,kh_100g,suikers_100g,vezels_100g,"
    "eiwit_100g,vet_100g,gi,user_id,bron").execute()
alle = [x for x in (b.data or []) if term in (x.get("naam") or "").lower()]
treffers = alle if ALLES else [x for x in alle if x.get("user_id") == ADMIN]
van_klanten = len(alle) - len(treffers)

bron_tekst = "alle producten" if ALLES else "alleen jouw eigen producten"
print(f"=== BIBLIOTHEEK — {len(treffers)} treffer(s) op '{term}'  ({bron_tekst}) ===")
if treffers:
    print(kop)
    print("-" * 84)
    for x in sorted(treffers, key=lambda y: -(float(y.get("kcal_100g") or 0))):
        print(f"{(x.get('naam') or '?')[:42]:42} "
              f"{float(x.get('kcal_100g') or 0):5.0f} "
              f"{float(x.get('kh_100g') or 0):6.1f} "
              f"{float(x.get('suikers_100g') or 0):5.1f} "
              f"{float(x.get('vezels_100g') or 0):5.1f} "
              f"{float(x.get('eiwit_100g') or 0):5.1f} "
              f"{float(x.get('vet_100g') or 0):5.1f} "
              f"{int(x.get('gi') or 0):4}")
        print(f"{'':42} categorie {x.get('categorie')}, portie {x.get('portie_g')}g")
else:
    print("  (niets gevonden)")
if van_klanten:
    print(f"\n  ({van_klanten} treffer(s) van klanten verborgen — gebruik --alles om ze te tonen)")

nev = [(k, v) for k, v in NEVO.items() if term in k.lower()]
print(f"\n=== NEVO — {len(nev)} treffer(s) ===")
if nev:
    print(kop)
    print("-" * 84)
    for k, v in sorted(nev, key=lambda t: -t[1].get("kcal", 0)):
        print(f"{k[:42]:42} {v.get('kcal', 0):5.0f} {v.get('kh', 0):6.1f} "
              f"{'':>5} {v.get('vezels', 0):5.1f} {v.get('eiwit', 0):5.1f} "
              f"{v.get('vet', 0):5.1f}")
    print("\n(NEVO toont geen suikers en GI in dit overzicht — die staan in nevo-data.ts)")
else:
    print("  (niets gevonden, of nevo_data.py ontbreekt)")
