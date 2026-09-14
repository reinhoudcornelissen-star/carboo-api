"""GUT-HERSTART-V1 - _gut_herstart_nodig en _gut_t1_verzeker moeten het eens zijn.

  !!  DEZELFDE VOORWAARDEN STAAN OP TWEE PLEKKEN IN main.py  !!

  _gut_herstart_nodig stelt vast of er een herstart komt en schrijft niets.
  _gut_t1_verzeker voert hem uit. Beide beslissen op dezelfde reeks controles:
  protocol_aan, doel nodig, momenten aanwezig, reeks-kolom aanwezig, lopende
  reeks niet leeg, ander getal dan waar de reeks mee begon, en al iets
  beoordeeld.

  Lopen die twee uit de pas, dan gebeurt er een van twee dingen, en allebei
  zijn erger dan een storing:

    - het scherm vraagt bevestiging voor een herstart die niet komt, of
    - de reeks wordt herstart zonder dat er iets gevraagd is.

  Het tweede merkt een sporter pas als zijn opbouw weg is. Daarom controleert
  dit script niet de twee functies apart, maar of ze op ELK pad hetzelfde
  zeggen. Wijzigt iemand er een, dan hoort dit script rood te worden.

  Dat is ook de grens van deze test: hij bewijst dat ze nu gelijk lopen. Hij
  dwingt niet af dat wie er een wijzigt de andere aanpast - hij maakt alleen
  zichtbaar DAT het misging.

Draaien:  python tests/test_herstart.py      (vanuit de wortel van de repo)
          python test_herstart.py            (vanuit deze map)

Het script leest main.py via een pad relatief aan zichzelf en laadt daaruit
alles met de _gut_-prefix plus de GUT_-constanten. Geen database, geen
netwerk, geen andere bestanden: wat hier draait is de echte code uit main.py.

Let op bij het lezen: een insert is niet hetzelfde als een herstart. Bij een
lege database maakt _gut_t1_verzeker ook een rij aan (T1). Alleen een insert
met een hoger reeksnummer telt als herstart.
"""
import ast
import io
from pathlib import Path

MAIN = Path(__file__).resolve().parent.parent / "main.py"


def laad_main():
    """Voert de _gut_-functies en GUT_-constanten uit main.py uit in een
    eigen namespace. Zo loopt dit script niet achter zodra er een functie
    bijkomt, en draait het tegen de echte code in plaats van een kopie."""
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
HANDELINGEN = []


class Query:
    """Legt vast wat er naar de database zou gaan, zonder het te doen.

    Filters worden genegeerd: er is maar een gebruiker, dus alle rijen uit de
    nepdatabase komen binnen. Dat is precies wat _gut_momenten verwacht."""

    def __init__(self, db, tabel):
        self.db = db
        self.tabel = tabel

    def __getattr__(self, naam):
        def doe(*a, **k):
            if naam in ("insert", "update") and a and isinstance(a[0], dict):
                HANDELINGEN.append((naam, self.tabel, a[0]))
            return self
        return doe

    def execute(self):
        class Resultaat:
            pass
        r = Resultaat()
        if self.tabel == "carboo_gut_testmomenten":
            r.data = self.db["momenten"]
        elif self.tabel == "carboo_gut_protocol":
            r.data = [dict(self.db["protocol"])]
        else:
            r.data = []
        return r


class NepSupabase:
    def __init__(self, db):
        self.db = db

    def table(self, tabel):
        return Query(self.db, tabel)


# _gut_protocol_doel leest sport, niveau en wedstrijd_duur_uur. Zonder een
# wedstrijdduur boven het uur besluit _gut_doel dat er niets te trainen valt,
# stoppen beide functies meteen, en meet dit script overal "geen herstart":
# groen, en volstrekt leeg.
PROTOCOL = {"sport": "Fietsen", "niveau": "Competitief", "wedstrijd_duur_uur": 3}


def moment(nummer, dosis, reeks=1, status="open", advies=None):
    """Een testmoment zoals de database het teruggeeft.

    De sleutel reeks staat er expliciet in: _gut_momenten leidt heeft_kolom af
    uit "reeks" in rijen[0]. Zonder die sleutel zou elke controle hieronder
    "geen herstart" meten om de verkeerde reden."""
    return {"id": f"m{reeks}-{nummer}", "nummer": nummer, "doel_kh_uur": dosis,
            "reeks": reeks, "status": status, "advies_soort": advies,
            "fase": "opbouw", "bron": "protocol"}


def meet(momenten, startdosis, protocol_aan=True, mag_herstarten=True):
    """Draait beide functies op dezelfde rijen en geeft terug wat ze deden."""
    HANDELINGEN.clear()
    db1 = {"momenten": [dict(m) for m in momenten], "protocol": PROTOCOL}
    nodig = R["_gut_herstart_nodig"](NepSupabase(db1), "u1", startdosis, protocol_aan)
    bij_vaststellen = list(HANDELINGEN)

    HANDELINGEN.clear()
    db2 = {"momenten": [dict(m) for m in momenten], "protocol": PROTOCOL}
    R["_gut_t1_verzeker"](NepSupabase(db2), "u1", startdosis, protocol_aan,
                          mag_herstarten)
    return nodig, bij_vaststellen, list(HANDELINGEN)


def herstart_gebeurd(handelingen, reeks_nu):
    return any(soort == "insert" and tabel == "carboo_gut_testmomenten"
               and int(rij.get("reeks") or 1) > reeks_nu
               for soort, tabel, rij in handelingen)


fouten = []


def check(naam, gekregen, verwacht):
    ok = gekregen == verwacht
    if not ok:
        fouten.append(naam)
    print(f"  {'ok ' if ok else 'FOUT'} {naam:52} {gekregen}"
          + ("" if ok else f"\n        verwacht {verwacht}"))


def eens(naam, momenten, startdosis, verwacht_herstart, reeks_nu=1,
         protocol_aan=True):
    """De kern: zeggen beide functies hetzelfde?"""
    nodig, bij_vaststellen, deed = meet(momenten, startdosis, protocol_aan)
    zei = nodig is not None
    deed_het = herstart_gebeurd(deed, reeks_nu)

    check(f"{naam}: vaststellen", zei, verwacht_herstart)
    check(f"{naam}: uitvoeren", deed_het, verwacht_herstart)
    if zei != deed_het:
        fouten.append(f"{naam}: DE TWEE ZIJN HET ONEENS")
        print(f"  FOUT {naam}: vaststellen zegt {zei}, uitvoeren doet {deed_het}")
    if bij_vaststellen:
        fouten.append(f"{naam}: vaststellen schreef naar de database")
        print(f"  FOUT {naam}: _gut_herstart_nodig schreef {bij_vaststellen}")
    return nodig


REEKS = [moment(1, 90, advies="omhoog", status="geslaagd"),
         moment(2, 105, advies="omhoog", status="geslaagd")]
ONBEOORDEELD = [moment(1, 90)]

print("DE VIER PADEN")
eens("lege database", [], 90, False)
eens("reeks zonder beoordeling, ander getal", ONBEOORDEELD, 70, False)
eens("reeks met beoordeling, gelijk getal", REEKS, 90, False)
eens("reeks met beoordeling, hoger getal", REEKS, 120, True)

print("\nDE VERLAGING")
nodig = eens("reeks met beoordeling, lager getal", REEKS, 70, True)
check("de nieuwe dosis staat in de melding", nodig and nodig["dosis"], 70)
check("en het aantal momenten van de lopende reeks", nodig and nodig["momenten"], 2)

print("\nEEN VERLAGING VAN VIJF GRAM TELT NET ZO GOED")
klein = eens("105 wordt 100", REEKS, 100, True)
check("ook dan wordt er bevestiging gevraagd", klein is not None, True)

print("\nWAT DE VASTSTELLING NIET DOET")
_, _, deed = meet(REEKS, 70, mag_herstarten=False)
check("zonder goedkeuring geen herstart", herstart_gebeurd(deed, 1), False)
check("en ook verder geen enkele schrijfactie", deed, [])

print("\nHET PROTOCOL STUURT NIET")
eens("protocol uit: de sporter is zelf de baas", REEKS, 70, False, protocol_aan=False)

print("\nEEN TWEEDE REEKS")
REEKS2 = REEKS + [moment(1, 70, reeks=2, advies="omhoog", status="geslaagd")]
eens("herstart vanuit reeks 2", REEKS2, 120, True, reeks_nu=2)
eens("gelijk aan waar reeks 2 mee begon", REEKS2, 70, False, reeks_nu=2)

print("\nKAN DEZE TEST ZELF FALEN?")
# Alles hierboven staat op ok, en een test die nooit rood geweest is kan een
# stille passagier zijn. Ving Query de inserts niet op, dan zou overal False
# staan en overal ok. Daarom saboteren we de vaststeller: hij zegt "geen
# herstart" terwijl de uitvoerder er wel een doet. Slaat de oneens-melding dan
# niet aan, dan bewaakt dit script niets en moet je het niet vertrouwen.
echte_vaststeller = R["_gut_herstart_nodig"]
try:
    R["_gut_herstart_nodig"] = lambda *a, **k: None
    nodig_nep, _, deed_nep = meet(REEKS, 70)
    betrapt = (nodig_nep is not None) != herstart_gebeurd(deed_nep, 1)
finally:
    R["_gut_herstart_nodig"] = echte_vaststeller
check("een vaststeller die ten onrechte nee zegt, wordt betrapt", betrapt, True)

print()
if fouten:
    raise SystemExit(f"{len(fouten)} FOUTEN: {fouten}")
print("alles klopt")
