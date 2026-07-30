"""
porties-standaard.py — zet het aantal porties op basis van standaard portiegroottes en
herberekent de macro's uit de ingredienten.

  hoofdgerecht 400 g | soep 300 g | ontbijt en smoothie 300 g | broodje of croque 200 g

    python porties-standaard.py              # tonen
    python porties-standaard.py --toepassen  # uitvoeren
"""
import os
import sys
from supabase import create_client

try:
    from nevo_data import NEVO
except ImportError:
    print("nevo_data.py ontbreekt.")
    sys.exit(1)

TOEPASSEN = "--toepassen" in sys.argv
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

bib_r = sb.table("fuelc_bibliotheek").select(
    "naam,kcal_100g,kh_100g,eiwit_100g,vet_100g,vezels_100g").execute()
BRON = {}
for b in (bib_r.data or []):
    n = (b.get("naam") or "").strip().lower()
    if n:
        BRON[n] = {"kcal": float(b.get("kcal_100g") or 0), "kh": float(b.get("kh_100g") or 0),
                   "eiwit": float(b.get("eiwit_100g") or 0), "vet": float(b.get("vet_100g") or 0),
                   "vezels": float(b.get("vezels_100g") or 0)}
for k, v in NEVO.items():
    BRON.setdefault(k.strip().lower(), v)


def norm(naam, typ):
    n = (naam or "").lower()
    if "balletjes" in n or "bar" in n:
        return None                      # aantal stuks laten staan
    if "soep" in n:
        return 300
    if "smoothie" in n:
        return 300
    for w in ("croque", "smos", "wrap", "durum", "toast", "broodje", "sandwich"):
        if w in n:
            return 200
    if (typ or "").lower() == "ontbijt":
        return 300
    if "havermout" in n or "yoghurt" in n:
        return 300
    return 400                            # hoofdgerecht


r = sb.table("fuelc_recepten_eigen").select(
    "id,naam,type,aantal_porties,kcal,ingredienten").execute()

print(f"{'recept':40} {'nu':>3} {'nieuw':>5} {'g/port':>7} {'kcal/port':>10}")
print("-" * 70)
wijzig = []
for x in sorted((r.data or []), key=lambda y: (y.get("naam") or "")):
    tot = {"kcal": 0.0, "kh": 0.0, "eiwit": 0.0, "vet": 0.0, "vezels": 0.0}
    gram, mist = 0.0, 0
    for i in (x.get("ingredienten") or []):
        if not isinstance(i, dict):
            continue
        g = float(i.get("gram") or i.get("hoeveelheid_g") or 0)
        gram += g
        v = BRON.get((i.get("naam") or "").strip().lower())
        if v is None:
            mist += 1
            continue
        for k in tot:
            tot[k] += v.get(k, 0.0) * g / 100.0
    huidig = max(int(x.get("aantal_porties") or 1), 1)
    if mist or gram <= 0 or tot["kcal"] <= 0:
        print(f"{(x.get('naam') or '?')[:40]:40} {huidig:3}   --   (overgeslagen)")
        continue
    doel = norm(x.get("naam"), x.get("type"))
    nieuw = huidig if doel is None else max(1, round(gram / doel))
    merk = "" if nieuw == huidig else "  <="
    print(f"{(x.get('naam') or '?')[:40]:40} {huidig:3} {nieuw:5} "
          f"{gram/nieuw:7.0f} {tot['kcal']/nieuw:10.0f}{merk}")
    wijzig.append((x.get("id"), nieuw, tot))

print()
if not TOEPASSEN:
    print(f"{len(wijzig)} recepten worden bijgewerkt. Draai met --toepassen.")
    sys.exit(0)

n = 0
for _id, nieuw, tot in wijzig:
    if not _id:
        continue
    sb.table("fuelc_recepten_eigen").update({
        "aantal_porties": nieuw,
        "kcal": round(tot["kcal"] / nieuw),
        "kh": round(tot["kh"] / nieuw, 1),
        "eiwit": round(tot["eiwit"] / nieuw, 1),
        "vet": round(tot["vet"] / nieuw, 1),
        "vezels": round(tot["vezels"] / nieuw, 1),
    }).eq("id", _id).execute()
    n += 1
print(f"{n} recepten bijgewerkt.")
