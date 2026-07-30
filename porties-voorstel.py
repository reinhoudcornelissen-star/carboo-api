"""
porties-voorstel.py — stelt per recept een aantal porties voor, zodat de ingredienten
overeenkomen met de opgeslagen kcal per portie. Toont het resulterende portiegewicht,
zodat je kunt zien of het plausibel is. Leest alleen tenzij je --toepassen meegeeft.

    python porties-voorstel.py              # alleen tonen
    python porties-voorstel.py --toepassen  # zet porties en herberekent de macro's
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

r = sb.table("fuelc_recepten_eigen").select(
    "id,naam,aantal_porties,kcal,ingredienten").execute()

rijen = []
for x in (r.data or []):
    tot = {"kcal": 0.0, "kh": 0.0, "eiwit": 0.0, "vet": 0.0, "vezels": 0.0}
    gram = 0.0
    mist = 0
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
    op = float(x.get("kcal") or 0)
    huidig = max(int(x.get("aantal_porties") or 1), 1)
    if mist or tot["kcal"] <= 0 or op <= 0:
        rijen.append((x.get("naam"), x.get("id"), huidig, gram, tot, op, None, mist))
        continue
    # het portieaantal dat het dichtst bij de opgeslagen kcal per portie uitkomt
    voorstel = max(1, round(tot["kcal"] / op))
    rijen.append((x.get("naam"), x.get("id"), huidig, gram, tot, op, voorstel, 0))

print(f"{'recept':38} {'nu':>3} {'voor':>4} {'g/port':>7} {'kcal/port':>10} {'opgesl':>7}")
print("-" * 76)
wijzig = []
for naam, _id, huidig, gram, tot, op, voorstel, mist in sorted(
        rijen, key=lambda t: -(t[6] or 0)):
    if voorstel is None:
        print(f"{(naam or '?')[:38]:38} {huidig:3} {'?':>4}  ({mist} ingredient niet gevonden)")
        continue
    gp = gram / voorstel
    kp = tot["kcal"] / voorstel
    merk = "" if voorstel == huidig else "  <= wijzigt"
    print(f"{(naam or '?')[:38]:38} {huidig:3} {voorstel:4} {gp:7.0f} {kp:10.0f} {op:7.0f}{merk}")
    if voorstel != huidig or abs(kp - op) / max(op, 1) > 0.05:
        wijzig.append((naam, _id, voorstel, tot))

print()
print(f"{len(wijzig)} recepten zouden wijzigen.")
if not TOEPASSEN:
    print("Niets gewijzigd. Draai met --toepassen om porties en macro's bij te werken.")
    sys.exit(0)

n = 0
for naam, _id, voorstel, tot in wijzig:
    if not _id:
        continue
    sb.table("fuelc_recepten_eigen").update({
        "aantal_porties": voorstel,
        "kcal": round(tot["kcal"] / voorstel),
        "kh": round(tot["kh"] / voorstel, 1),
        "eiwit": round(tot["eiwit"] / voorstel, 1),
        "vet": round(tot["vet"] / voorstel, 1),
        "vezels": round(tot["vezels"] / voorstel, 1),
    }).eq("id", _id).execute()
    n += 1
print(f"{n} recepten bijgewerkt: porties gezet en macro's herberekend uit de ingredienten.")
