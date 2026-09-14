"""GUT-COACH-MOMENT-V1 - de vaststeller en de beslisboom moeten het eens zijn.

  !!  DEZELFDE REGEL STAAT OP TWEE PLEKKEN IN main.py  !!

  _gut_coach_fasedoorbraak zegt VOORAF of een dosis het protocol door de
  opbouw heen duwt. Het coachscherm maakt daar zijn bevestiging van.

  beoordeel_testmoment besluit ACHTERAF dat het gebeurt:

      plafond_sport = GUT_PLAFOND.get(sport, 115)
      grens = doel_wedstrijd["grens"] or plafond_sport
      nieuw = _gut_stap_omhoog(doel, grens)
      if nieuw <= doel:  ->  fase_bevestiging

  Lopen die twee uit de pas, dan gebeurt er een van twee dingen:

    - het scherm waarschuwt voor een doorbraak die niet komt, of
    - een coach kort het protocol af zonder dat iemand het zei.

  Het tweede is het ergste. Een sporter die van 60 naar 120 springt en
  slaagt, staat in een klap in de bevestigingsfase met zijn hele opbouw
  overgeslagen -- en een darmtrainingsprotocol bestaat juist om die opbouw
  af te dwingen. Dat merkt niemand tot het gebeurd is.

  Daarom controleert dit script de twee niet apart, maar of ze op ELK pad
  hetzelfde zeggen. Wijzigt iemand er een, dan hoort dit script rood te
  worden.

  Dat is ook de grens van deze test: hij bewijst dat ze nu gelijk lopen. Hij
  dwingt niet af dat wie er een wijzigt de andere aanpast - hij maakt alleen
  zichtbaar DAT het misging.

Draaien:  python tests/test_fasedoorbraak.py   (vanuit de wortel van de repo)
          python test_fasedoorbraak.py         (vanuit deze map)

Geen database, geen netwerk. Het script leest main.py via een pad relatief
aan zichzelf en voert daaruit alles met de _gut_-prefix uit.
"""
import ast
import io
from pathlib import Path

MAIN = Path(__file__).resolve().parent.parent / "main.py"


def laad_main():
    bron = io.open(MAIN, encoding="utf-8-sig").read()
    stukken = []
    for knoop in ast.parse(bron).body:
        if isinstance(knoop, ast.FunctionDef) and knoop.name.startswith("_gut_"):
            knoop.decorator_list = []
            stukken.append(knoop)
        elif isinstance(knoop, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id.startswith("GUT_")
                for t in knoop.targets):
            stukken.append(knoop)
    ruimte = {"print": lambda *a, **k: None}
    exec(compile(ast.Module(stukken, []), "<main>", "exec"), ruimte)
    return ruimte


R = laad_main()


class Query:
    def __init__(self, db, tabel):
        self.db = db
        self.tabel = tabel

    def __getattr__(self, naam):
        return lambda *a, **k: self

    def execute(self):
        class Resultaat:
            pass
        r = Resultaat()
        if self.tabel == "carboo_gut_protocol":
            r.data = [dict(self.db["protocol"])] if self.db.get("protocol") else []
        else:
            r.data = []
        return r


class NepSupabase:
    def __init__(self, db):
        self.db = db

    def table(self, tabel):
        return Query(self.db, tabel)


def beslisboom_breekt_door(protocol, dosis):
    """Wat beoordeel_testmoment zou besluiten, met zijn eigen drie regels.

    Letterlijk overgenomen uit die route. Wijkt dit af, dan is dit script
    waardeloos: het zou de vaststeller met zichzelf vergelijken in plaats
    van met de beslisboom."""
    doel_wedstrijd = R["_gut_protocol_doel"](NepSupabase({"protocol": protocol}), "u1")
    if not doel_wedstrijd["nodig"]:
        return False
    plafond_sport = R["GUT_PLAFOND"].get(doel_wedstrijd["sport"], 115)
    grens = doel_wedstrijd["grens"] or plafond_sport
    return R["_gut_stap_omhoog"](dosis, grens) <= dosis


fouten = []


def check(naam, gekregen, verwacht):
    ok = gekregen == verwacht
    if not ok:
        fouten.append(naam)
    print(f"  {'ok ' if ok else 'FOUT'} {naam:54} {gekregen}"
          + ("" if ok else f"\n        verwacht {verwacht}"))


def eens(naam, protocol, dosis, verwacht, fase="opbouw"):
    """De kern: zeggen de vaststeller en de beslisboom hetzelfde?"""
    sup = NepSupabase({"protocol": protocol})
    zei = R["_gut_coach_fasedoorbraak"](sup, "u1", dosis, fase) is not None
    doet = beslisboom_breekt_door(protocol, dosis) if fase == "opbouw" else False

    check(f"{naam}: vaststeller", zei, verwacht)
    check(f"{naam}: beslisboom", doet, verwacht)
    if zei != doet:
        fouten.append(f"{naam}: DE TWEE ZIJN HET ONEENS")
        print(f"  FOUT {naam}: vaststeller zegt {zei}, beslisboom doet {doet}")


# Fietsen/Competitief geeft plafond 90; 3 uur wedstrijd geeft doel 90.
COMP = {"sport": "Fietsen", "niveau": "Competitief", "wedstrijd_duur_uur": 3}
# Professioneel fietsen: plafond 120, wedstrijd van 5 uur -> sportplafond.
PRO = {"sport": "Fietsen", "niveau": "Professioneel", "wedstrijd_duur_uur": 5}
# Onder het uur valt er niets te trainen.
KORT = {"sport": "Fietsen", "niveau": "Competitief", "wedstrijd_duur_uur": 0.75}

print("ONDER, OP EN BOVEN DE GRENS")
eens("60 bij een grens van 90", COMP, 60, False)
eens("75 bij een grens van 90", COMP, 75, False)
eens("90 is de grens zelf", COMP, 90, True)
eens("120 ligt er ver boven", COMP, 120, True)

print("\nEEN HOGERE GRENS SCHUIFT DE DREMPEL MEE")
eens("90 bij een grens van 120", PRO, 90, False)
eens("120 is daar de grens", PRO, 120, True)

print("\nBUITEN DE OPBOUW STUURT DE DOSIS DE FASE NIET")
eens("120 in de bevestiging", COMP, 120, False, fase="bevestiging")
eens("120 in de wedstrijdsimulatie", COMP, 120, False, fase="wedstrijd")

print("\nGEEN PROTOCOL, GEEN DOORBRAAK")
eens("wedstrijd onder het uur", KORT, 120, False)

print("\nWAT DE VASTSTELLER TERUGGEEFT")
uit = R["_gut_coach_fasedoorbraak"](NepSupabase({"protocol": COMP}), "u1", 120)
check("de dosis staat in de melding", uit and uit["dosis"], 120)
check("en de grens erbij", uit and uit["grens"], 90)
check("een dosis van nul telt niet",
      R["_gut_coach_fasedoorbraak"](NepSupabase({"protocol": COMP}), "u1", 0), None)

print("\nKAN DEZE TEST ZELF FALEN?")
# Alles hierboven staat op ok, en een test die nooit rood geweest is kan een
# stille passagier zijn. Daarom saboteren we de vaststeller: hij zegt "geen
# doorbraak" waar de beslisboom er wel een doet. Slaat de oneens-melding dan
# niet aan, dan bewaakt dit script niets en moet je het niet vertrouwen.
echte = R["_gut_coach_fasedoorbraak"]
try:
    R["_gut_coach_fasedoorbraak"] = lambda *a, **k: None
    sup = NepSupabase({"protocol": COMP})
    zei = R["_gut_coach_fasedoorbraak"](sup, "u1", 120) is not None
    betrapt = zei != beslisboom_breekt_door(COMP, 120)
finally:
    R["_gut_coach_fasedoorbraak"] = echte
check("een vaststeller die ten onrechte nee zegt, wordt betrapt", betrapt, True)

print()
if fouten:
    raise SystemExit(f"{len(fouten)} FOUTEN: {fouten}")
print("alles klopt")
