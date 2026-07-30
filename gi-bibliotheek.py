"""
gi-bibliotheek.py — vult de ontbrekende GI-waarden in fuelc_bibliotheek aan.

    python gi-bibliotheek.py              # tonen
    python gi-bibliotheek.py --toepassen  # uitvoeren

Herkomst van de waarden staat per product in de derde kolom:
  tabel  = internationale GI-tabellen (Atkinson e.a.)
  afgel. = afgeleid uit de productsamenstelling, geen gemeten waarde
"""
import os
import sys
from supabase import create_client

TOEPASSEN = "--toepassen" in sys.argv
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# naam: (gi, herkomst, toelichting)
GI = {
    "Haribo tropifruit":                                (75, "tabel",  "gomsnoep, glucosestroop"),
    "Wellness Flakes cocolade":                         (70, "tabel",  "ontbijtgraan met suiker"),
    "Milka Choco caramel":                              (45, "tabel",  "melkchocolade, vet remt"),
    "Ps toast":                                         (72, "tabel",  "wit geroosterd brood"),
    "X-Oats":                                           (55, "tabel",  "haverbasis"),
    "Eiwit Pita Brood":                                 (55, "afgel.", "eiwitrijk brood, trager"),
    "Ps crackers":                                      (70, "tabel",  "tarwecracker"),
    "Alcoholvrij bruin bier":                           (65, "tabel",  "maltose"),
    "Aldi proteïnereep met cranberries":                (50, "afgel.", "eiwit en vet remmen"),
    "Crispy protein bar decathlon":                     (50, "afgel.", "idem"),
    "Proteine reep kruidvat":                           (50, "afgel.", "idem"),
    "Proteïnereep kruidvat":                            (50, "afgel.", "idem"),
    "Protein Bar":                                      (50, "afgel.", "idem"),
    "HiPRO Peanut Butter Banana Protein Bar":           (45, "afgel.", "pinda vertraagt extra"),
    "MyProtein Whey Protein Isolate Lemon & Raspberry": (25, "tabel",  "wei-eiwit"),
    "Proteïne supplement":                              (25, "tabel",  "idem"),
    "Griekse yoghurt 2% aldi":                          (35, "tabel",  "zuivel, lactose"),
    "Griekse yoghurt aldi framboos":                    (35, "tabel",  "idem, gezoet"),
    "Skyr aldi":                                        (30, "tabel",  "magere zuivel"),
    "Skyr yoghurtdrink":                                (30, "tabel",  "idem"),
    "Ricotta":                                          (30, "tabel",  "idem"),
    "Philadelphia light":                               (30, "tabel",  "idem"),
    "Kaasschnitzel vegetarisch":                        (50, "afgel.", "paneerlaag"),
    "Vissticks":                                        (55, "afgel.", "paneerlaag"),
    "Mayonaise light":                                  (55, "afgel.", "suiker in kleine hoeveelheid"),
    "Pesto aldi":                                       (30, "afgel.", "weinig koolhydraat, veel vet"),
    "Nori":                                             (15, "tabel",  "zeewier, vezelrijk"),
}

b = sb.table("fuelc_bibliotheek").select("id,naam,categorie,kh_100g,gi").execute()
prod = b.data or []
te_doen, niet_gevonden = [], list(GI.keys())

for p in prod:
    n = (p.get("naam") or "").strip()
    if n in GI:
        if n in niet_gevonden:
            niet_gevonden.remove(n)
        huidig = p.get("gi")
        if huidig and float(huidig) > 0:
            continue
        te_doen.append((p.get("id"), n, p.get("categorie"), float(p.get("kh_100g") or 0), GI[n]))

print(f"{len(te_doen)} producten krijgen een GI\n")
print(f"{'product':44} {'kh':>6} {'gi':>4}  {'herkomst':8} toelichting")
print("-" * 96)
for _id, n, cat, kh, (gi, bron, uitleg) in sorted(te_doen, key=lambda t: -t[3]):
    print(f"{n[:44]:44} {kh:6.1f} {gi:4}  {bron:8} {uitleg}")

if niet_gevonden:
    print(f"\nNiet in de bibliotheek gevonden ({len(niet_gevonden)}): {', '.join(niet_gevonden)}")

rest = [p for p in prod if not (p.get("gi") and float(p.get("gi")) > 0)
        and (p.get("naam") or "").strip() not in GI and float(p.get("kh_100g") or 0) >= 5]
if rest:
    print(f"\nNog zonder GI en wel koolhydraatrijk ({len(rest)}):")
    for p in rest:
        print(f"  {float(p.get('kh_100g') or 0):6.1f}g KH  {p.get('naam')}")

print()
if not TOEPASSEN:
    print("Niets gewijzigd. Draai met --toepassen.")
    sys.exit(0)

n = 0
for _id, naam, cat, kh, (gi, bron, uitleg) in te_doen:
    if not _id:
        continue
    sb.table("fuelc_bibliotheek").update({"gi": gi}).eq("id", _id).execute()
    n += 1
print(f"{n} producten bijgewerkt.")
