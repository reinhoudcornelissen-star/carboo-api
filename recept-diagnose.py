"""
recept-diagnose.py — laat per recept zien hoeveel gram er in zit en welk product er bij elk
ingredient gevonden werd. Zo zien we of de afwijkingen komen door porties of door foute
matches. Leest alleen, wijzigt niets.

    python recept-diagnose.py            # overzicht van alle recepten
    python recept-diagnose.py Lasagne    # detail van één recept (deel van de naam volstaat)
"""
import os
import sys
from supabase import create_client

try:
    from nevo_data import NEVO
except ImportError:
    print("nevo_data.py ontbreekt.")
    sys.exit(1)

filter_naam = " ".join(a for a in sys.argv[1:] if not a.startswith("--")).lower()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

bib_r = sb.table("fuelc_bibliotheek").select(
    "naam,kcal_100g,kh_100g,eiwit_100g,vet_100g,vezels_100g").execute()
BIB = {}
for b in (bib_r.data or []):
    n = (b.get("naam") or "").strip()
    if n:
        BIB[n.lower()] = ("bib", n, {
            "kcal": float(b.get("kcal_100g") or 0), "kh": float(b.get("kh_100g") or 0),
            "eiwit": float(b.get("eiwit_100g") or 0), "vet": float(b.get("vet_100g") or 0),
            "vezels": float(b.get("vezels_100g") or 0)})
NEVO_L = {k.lower(): ("nevo", k, v) for k, v in NEVO.items()}


def zoek(naam):
    """Alleen exacte match. Losse matches zijn te riskant gebleken."""
    n = (naam or "").strip().lower()
    if not n:
        return None
    if n in BIB:
        return BIB[n]
    if n in NEVO_L:
        return NEVO_L[n]
    return None


r = sb.table("fuelc_recepten_eigen").select(
    "naam,aantal_porties,kcal,kh,eiwit,vet,ingredienten").execute()
recepten = r.data or []

if filter_naam:
    for x in recepten:
        if filter_naam not in (x.get("naam") or "").lower():
            continue
        por = max(int(x.get("aantal_porties") or 1), 1)
        print(f"\n{x.get('naam')}   ({por} portie(s), opgeslagen {x.get('kcal')} kcal)")
        print("-" * 74)
        tot = 0.0
        gram_tot = 0.0
        for i in (x.get("ingredienten") or []):
            inaam = i.get("naam") or "?"
            gram = float(i.get("gram") or i.get("hoeveelheid_g") or 0)
            gram_tot += gram
            v = zoek(inaam)
            if v is None:
                print(f"  {gram:6.0f}g  {inaam[:34]:34}  NIET GEVONDEN")
                continue
            bron, echte_naam, w = v
            kc = w["kcal"] * gram / 100
            tot += kc
            merk = "" if echte_naam.lower() == inaam.strip().lower() else f"  -> {echte_naam}"
            print(f"  {gram:6.0f}g  {inaam[:34]:34}  {kc:6.0f} kcal  [{bron}]{merk}")
        print("-" * 74)
        print(f"  {gram_tot:6.0f}g totaal            berekend {tot:6.0f} kcal voor het hele recept")
        print(f"          per portie ({por}x)         {tot/por:6.0f} kcal   opgeslagen: {x.get('kcal')}")
    sys.exit(0)

print(f"{'recept':40} {'por':>3} {'gram':>6} {'g/por':>6} {'opgesl':>7} {'berek':>6} {'ratio':>6}")
print("-" * 82)
rijen = []
for x in recepten:
    por = max(int(x.get("aantal_porties") or 1), 1)
    tot = 0.0
    gram_tot = 0.0
    mist = 0
    for i in (x.get("ingredienten") or []):
        gram = float(i.get("gram") or i.get("hoeveelheid_g") or 0)
        gram_tot += gram
        v = zoek(i.get("naam"))
        if v is None:
            mist += 1
            continue
        tot += v[2]["kcal"] * gram / 100
    op = float(x.get("kcal") or 0)
    per = tot / por
    ratio = per / op if op else 0
    rijen.append((ratio, x.get("naam") or "?", por, gram_tot, gram_tot / por, op, per, mist))

for ratio, naam, por, gram, gpor, op, per, mist in sorted(rijen, key=lambda t: -t[0]):
    ster = f"  ({mist} ontbreekt)" if mist else ""
    print(f"{naam[:40]:40} {por:3} {gram:6.0f} {gpor:6.0f} {op:7.0f} {per:6.0f} {ratio:6.2f}{ster}")
