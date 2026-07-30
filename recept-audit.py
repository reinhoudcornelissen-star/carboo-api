"""
recept-audit.py — rekent elk recept na uit zijn ingredienten en vergelijkt dat met de
opgeslagen waarden. Ingredientwaarden komen uit fuelc_bibliotheek en uit nevo_data.py.

Let op: de opgeslagen receptwaarden zijn PER PORTIE. De ingredienten gelden voor het hele
recept, dus die som wordt gedeeld door het aantal porties.

Gebruik (Render Web Shell van carboo-api-fra):
    python recept-audit.py              # alleen tonen, wijzigt niets
    python recept-audit.py --toepassen  # corrigeert de recepten die volledig narekenbaar zijn
"""
import os
import sys
from supabase import create_client

try:
    from nevo_data import NEVO
except ImportError:
    print("nevo_data.py ontbreekt. Draai eerst nevo-naar-python.js en kopieer het bestand hierheen.")
    sys.exit(1)

TOEPASSEN = "--toepassen" in sys.argv
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# ─── bronnen inlezen ───────────────────────────────────────────────
bib_r = sb.table("fuelc_bibliotheek").select(
    "naam,kcal_100g,kh_100g,eiwit_100g,vet_100g,vezels_100g"
).execute()
BIB = {}
for b in (bib_r.data or []):
    n = (b.get("naam") or "").strip()
    if not n:
        continue
    BIB[n.lower()] = {
        "kcal": float(b.get("kcal_100g") or 0),
        "kh": float(b.get("kh_100g") or 0),
        "eiwit": float(b.get("eiwit_100g") or 0),
        "vet": float(b.get("vet_100g") or 0),
        "vezels": float(b.get("vezels_100g") or 0),
    }
NEVO_L = {k.lower(): v for k, v in NEVO.items()}

print(f"bibliotheek: {len(BIB)} producten   NEVO: {len(NEVO_L)} producten\n")


def zoek(naam):
    """Zoek een ingredient. Bibliotheek gaat voor op NEVO."""
    n = (naam or "").strip().lower()
    if not n:
        return None
    if n in BIB:
        return BIB[n]
    if n in NEVO_L:
        return NEVO_L[n]
    # losser: begint met, of bevat
    for bron in (BIB, NEVO_L):
        for k, v in bron.items():
            if k == n or k.startswith(n) or n.startswith(k):
                return v
    return None


# ─── recepten narekenen ────────────────────────────────────────────
r = sb.table("fuelc_recepten_eigen").select(
    "id,naam,aantal_porties,kcal,kh,eiwit,vet,vezels,ingredienten"
).execute()
recepten = r.data or []

volledig, onvolledig = [], []
for x in recepten:
    naam = x.get("naam") or "?"
    por = max(int(x.get("aantal_porties") or 1), 1)
    ing = x.get("ingredienten")
    if not isinstance(ing, list) or not ing:
        onvolledig.append((naam, ["geen ingredienten"], None))
        continue

    tot = {"kcal": 0.0, "kh": 0.0, "eiwit": 0.0, "vet": 0.0, "vezels": 0.0}
    mist, gram_tot = [], 0.0
    for i in ing:
        if not isinstance(i, dict):
            continue
        inaam = i.get("naam") or ""
        try:
            gram = float(i.get("gram") or i.get("hoeveelheid_g") or i.get("hoeveelheid") or 0)
        except (TypeError, ValueError):
            gram = 0.0
        gram_tot += gram
        v = zoek(inaam)
        if v is None:
            mist.append(f"{inaam} ({gram:.0f}g)")
            continue
        f = gram / 100.0
        for k in tot:
            tot[k] += v.get(k, 0.0) * f

    per = {k: v / por for k, v in tot.items()}
    opgeslagen = {
        "kcal": float(x.get("kcal") or 0), "kh": float(x.get("kh") or 0),
        "eiwit": float(x.get("eiwit") or 0), "vet": float(x.get("vet") or 0),
        "vezels": float(x.get("vezels") or 0),
    }
    rij = (naam, x.get("id"), por, gram_tot, opgeslagen, per, mist)
    (onvolledig if mist else volledig).append(rij)

# ─── uitvoer ───────────────────────────────────────────────────────
print("=" * 78)
print(f"VOLLEDIG NAREKENBAAR: {len(volledig)}   INGREDIENT NIET GEVONDEN: {len(onvolledig)}")
print("=" * 78)

groot, klein = [], []
for rij in volledig:
    naam, _id, por, gram, op, per, _ = rij
    afw = abs(op["kcal"] - per["kcal"]) / max(op["kcal"], 1) * 100
    (groot if afw > 10 else klein).append((afw, rij))

groot.sort(key=lambda t: -t[0])
print(f"\n--- meer dan 10% verschil met de ingredienten: {len(groot)} ---")
print(f"{'recept':40} {'opgesl':>7} {'berekend':>9} {'versch':>7} {'%':>5}")
for afw, (naam, _id, por, gram, op, per, _) in groot:
    print(f"{naam[:40]:40} {op['kcal']:7.0f} {per['kcal']:9.0f} "
          f"{op['kcal']-per['kcal']:7.0f} {afw:4.0f}%")

print(f"\n--- binnen 10%: {len(klein)} ---")
for afw, (naam, _id, por, gram, op, per, _) in sorted(klein, key=lambda t: -t[0])[:12]:
    print(f"  {naam[:40]:40} {op['kcal']:6.0f} vs {per['kcal']:6.0f}  ({afw:.0f}%)")
if len(klein) > 12:
    print(f"  ... en {len(klein)-12} andere")

if onvolledig:
    print(f"\n--- niet narekenbaar, ingredient ontbreekt in bibliotheek en NEVO: {len(onvolledig)} ---")
    for rij in onvolledig:
        naam = rij[0]
        mist = rij[-1] if len(rij) > 2 else rij[1]
        print(f"  {naam}")
        for m in (mist or [])[:6]:
            print(f"      ontbreekt: {m}")

# ─── eventueel corrigeren ──────────────────────────────────────────
print()
if not TOEPASSEN:
    print("Niets gewijzigd. Draai met --toepassen om de volledig narekenbare recepten te corrigeren.")
else:
    n = 0
    for rij in volledig:
        naam, _id, por, gram, op, per, _ = rij
        if not _id:
            continue
        sb.table("fuelc_recepten_eigen").update({
            "kcal": round(per["kcal"]),
            "kh": round(per["kh"], 1),
            "eiwit": round(per["eiwit"], 1),
            "vet": round(per["vet"], 1),
            "vezels": round(per["vezels"], 1),
        }).eq("id", _id).execute()
        n += 1
    print(f"{n} recepten bijgewerkt naar de berekende waarden.")
    print("De recepten met ontbrekende ingredienten zijn NIET aangeraakt.")
