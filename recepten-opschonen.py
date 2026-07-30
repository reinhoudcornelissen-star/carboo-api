"""
recepten-opschonen.py — twee dingen, zodat elk recept-ingredient teruggevonden wordt:

  A. namen in de recepten gelijktrekken met bestaande producten (geen nieuwe producten)
  B. de zeven producten toevoegen die echt ontbreken

    python recepten-opschonen.py              # alleen tonen, wijzigt niets
    python recepten-opschonen.py --toepassen  # voert het uit
"""
import os
import sys
from supabase import create_client

TOEPASSEN = "--toepassen" in sys.argv
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
ADMIN = "24605703-c6eb-4194-af80-7a22edec0581"

# ─── A. hernoemingen ───────────────────────────────────────────────
HERNOEM = {
    "Wortel rauw": "Wortel",
    "Tomaat rauw": "Tomaat",
    "Tomaat (groot)": "Tomaat",
    "Paprika": "Paprika rood",
    "Paprika rauw": "Paprika rood",
    "Broccoli": "Broccoli gestoomd",
    "Champignons gemengd": "Champignons",
    "Stokbrood": "Stokbrood (wit)",
    "Pasta volkoren gekookt": "Pasta volkoren (gek.)",
    "Zoete aardappel gekookt": "Zoete aardappel gek.",
    "Aardappel (gekookt)": "Aardappel gekookt",
    "Tonijn (in water)": "Tonijn blik in water",
    "Edamame gekookt": "Edamame gek.",
    "Sla": "Gemengde sla",
}

# ─── B. ontbrekende producten, waarden per 100 g ───────────────────
# naam, categorie, portie_g, portie_label, kcal, kh, suikers, vezels, eiwit, vet,
# verzadigd, natrium, kalium, calcium, ijzer, magnesium, vitc, vitd, vitb12, omega3, gi
NIEUW = [
    ("Ei",                 "Eieren",          50,  "1 ei",       143, 0.7, 0.4, 0,   12.6, 9.5, 3.1,  142, 138, 56,  1.8, 12, 0,   2.0, 1.1, 0.1, 0),
    ("Witloof",            "Groenten",        150, "1 stronk",   17,  2.0, 1.0, 1.3, 1.0,  0.1, 0,    5,   211, 19,  0.2, 10, 3,   0,   0,   0,   15),
    ("Zalm rauw",          "Vlees & vis",     100, "1 moot",     208, 0,   0,   0,   20.0, 13.4, 3.1, 59,  363, 12,  0.3, 27, 0,   11,  3.2, 2.3, 0),
    ("Tonijn rauw",        "Vlees & vis",     100, "1 portie",   144, 0,   0,   0,   23.3, 4.9,  1.3, 39,  252, 8,   1.0, 50, 0,   1.7, 9.4, 1.3, 0),
    ("Wokolie",            "Vetten & oliën",  10,  "1 el",       900, 0,   0,   0,   0,    100,  9.0, 0,   0,   0,   0,   0,  0,   0,   0,   1.5, 0),
    ("Yoghurt Griekse 0%", "Zuivel",          150, "1 portie",   57,  4.0, 4.0, 0,   10.0, 0.4,  0.2, 36,  141, 110, 0.1, 11, 0,   0,   0.7, 0,   11),
    ("Zwarte olijven",     "Groenten",        25,  "handvol",    115, 6.0, 0,   3.2, 0.8,  10.9, 1.4, 735, 8,   88,  3.3, 4,  1,   0,   0,   0.1, 15),
]

# ─── uitvoeren ─────────────────────────────────────────────────────
print("=" * 76)
print("A. NAMEN GELIJKTREKKEN IN DE RECEPTEN")
print("=" * 76)

r = sb.table("fuelc_recepten_eigen").select("id,naam,ingredienten").execute()
wijzig = []
for x in (r.data or []):
    ing = x.get("ingredienten")
    if not isinstance(ing, list):
        continue
    nieuw_ing, geraakt = [], []
    for i in ing:
        if isinstance(i, dict):
            n = (i.get("naam") or "").strip()
            if n in HERNOEM:
                geraakt.append(f"{n} -> {HERNOEM[n]}")
                i = dict(i, naam=HERNOEM[n])
        nieuw_ing.append(i)
    if geraakt:
        wijzig.append((x.get("id"), x.get("naam"), nieuw_ing, geraakt))

print(f"{len(wijzig)} recepten krijgen een of meer hernoemingen\n")
for _id, naam, _ing, geraakt in wijzig:
    print(f"  {naam}")
    for g in geraakt:
        print(f"      {g}")

print()
print("=" * 76)
print("B. ONTBREKENDE PRODUCTEN TOEVOEGEN")
print("=" * 76)
best = sb.table("fuelc_bibliotheek").select("naam").execute()
bestaand = set((b.get("naam") or "").strip().lower() for b in (best.data or []))
toe = [p for p in NIEUW if p[0].lower() not in bestaand]
al = [p[0] for p in NIEUW if p[0].lower() in bestaand]
print(f"{len(toe)} toe te voegen" + (f", {len(al)} bestaan al: {', '.join(al)}" if al else ""))
print()
print(f"  {'product':22} {'categorie':16} {'kcal':>5} {'kh':>5} {'eiw':>5} {'vet':>5} {'gi':>4}")
for p in toe:
    print(f"  {p[0][:22]:22} {p[1][:16]:16} {p[4]:5} {p[5]:5} {p[8]:5} {p[9]:5} {p[20]:4}")

print()
if not TOEPASSEN:
    print("Niets gewijzigd. Draai met --toepassen om het uit te voeren.")
    sys.exit(0)

import uuid
n_prod = 0
for p in toe:
    (naam, cat, pg, pl, kcal, kh, suik, vez, eiw, vet, verz,
     natr, kal, calc, ijz, mag, vitc, vitd, vitb12, om3, gi) = p
    sb.table("fuelc_bibliotheek").insert({
        "id": str(uuid.uuid4()), "user_id": ADMIN, "is_globaal": True, "bron": "eigen",
        "naam": naam, "categorie": cat, "portie_g": pg, "portie_label": pl,
        "kcal_100g": kcal, "kh_100g": kh, "suikers_100g": suik, "vezels_100g": vez,
        "eiwit_100g": eiw, "vet_100g": vet, "verzadigd_100g": verz,
        "natrium_100g": natr, "kalium_100g": kal, "calcium_100g": calc,
        "ijzer_100g": ijz, "magnesium_100g": mag, "vitc_100g": vitc,
        "vitd_100g": vitd, "vitb12_100g": vitb12, "omega3_100g": om3, "gi": gi,
    }).execute()
    n_prod += 1

n_rec = 0
for _id, naam, nieuw_ing, _g in wijzig:
    if not _id:
        continue
    sb.table("fuelc_recepten_eigen").update({"ingredienten": nieuw_ing}).eq("id", _id).execute()
    n_rec += 1

print(f"{n_prod} producten toegevoegd, {n_rec} recepten hernoemd.")
print("Draai daarna opnieuw: python recept-diagnose.py")
