"""VOEDINGSGROEP-SPIEGEL-V1 - dezelfde vraag wordt in TWEE talen beantwoord.

  !!  DEZELFDE REGELS STAAN IN main.py EN IN analyses.tsx  !!

"Tot welke voedingsgroep hoort dit?" wordt op twee plekken beslist:

  - herkenCategorie in app/app/fueling/analyse-utils.ts (TypeScript). Daar
    staat sinds oktober 2026 de ENIGE frontendkopie: analyses.tsx (het scherm
    van de sporter) en de coachzone importeren hem allebei;
  - _voedingsgroep in main.py (Python), voor De Bevoorrading.

Die tweede moet er zijn: het weekrapport wordt op de server gemaakt, want er
hangt een coachroute aan (/api/coach/klant/{id}/bevoorrading) en die draait
buiten de browser om. Zolang dat zo is, bestaat het antwoord twee keer.

WAT ER GEBEURDE. herken_categorie had geen vangnet op de NAAM. Een logregel
zonder bruikbare categorie kwam als "Overige" terug, en _gf_gram telt
"Overige" bij groente noch fruit. Analyses heeft dat vangnet wel. Een
gebruiker die elke dag ruim 120 g fruit logde, zag 139 g in Analyses en 54 g
in zijn Bevoorrading. Hij merkte het; de app meldde niets.

Deze test leest analyse-utils.ts in en legt de vijf lijsten die de
voedingsgroepen scheiden woord voor woord naast de Python-kant. Wijzigt iemand daar
een woord, dan wordt dit script rood.

WAT DEZE TEST NIET DOET. Hij bewijst dat de twee NU gelijk lopen, niet dat
wie er een wijzigt de andere aanpast. En hij vergelijkt de lijsten, niet elk
pad: de naamcorrecties en de MAP-tabellen worden alleen via gedrag getoetst.
Twee verschillen zijn bovendien bekend en bewust (zie het commentaar bij
VOEDINGSGROEP-SPIEGEL-V1 in main.py): het weekrapport pakt gelogde RECEPTEN
uit in ingredienten en Analyses niet, en de twee delen door een ander aantal
dagen.

Draaien:  python tests/test_voedingsgroep.py

Geen database, geen netwerk. main.py wordt via ast gelezen en alleen de
betrokken functies worden uitgevoerd, dus dit draait tegen de ECHTE code.
Ligt carboo-next-v2 er niet naast, dan zegt het script dat en slaat de
vergelijking over; dan bewaakt het alleen de Python-kant.
"""
import ast
import io
import json
import re
import sys
import time
from pathlib import Path

MAIN = Path(__file__).resolve().parent.parent / "main.py"
TS = (Path(__file__).resolve().parent.parent.parent
      / "carboo-next-v2" / "app" / "app" / "fueling" / "analyse-utils.ts")

NODIG_FUNC = {"_bevat_woord", "_haal_catwoorden",
              "_vg_heel_woord", "_vg_normaliseer", "_vg_basis",
              "_voedingsgroep", "_gf_gram", "_bordrol_uit_groep"}
NODIG_VAR = {"_catwoorden_cache", "_VG_STANDAARD", "_VG_NORM", "_VG_MAP",
             "_G_DIER", "_G_PLANT",
             "_BORDROL_UIT_GROEP",
             "_VG_CAT_KNOL",
             "_VG_CAT_GROENTE", "_VG_CAT_FRUIT", "_VG_GROENTE_NAMEN",
             "_VG_FRUIT_NAMEN", "_VG_VANGNET"}


def laad_main():
    bron = io.open(MAIN, encoding="utf-8-sig").read()
    stukken = []
    for knoop in ast.parse(bron).body:
        if isinstance(knoop, ast.FunctionDef) and knoop.name in NODIG_FUNC:
            knoop.decorator_list = []
            stukken.append(knoop)
        elif isinstance(knoop, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in NODIG_VAR for t in knoop.targets):
            stukken.append(knoop)
    ruimte = {"_re": re, "_time": time, "json": json, "Client": object,
              "print": lambda *a, **k: None}
    exec(compile(ast.Module(stukken, []), "<main>", "exec"), ruimte)
    mist = (NODIG_FUNC | NODIG_VAR) - set(ruimte)
    if mist:
        print(f"main.py mist: {sorted(mist)}")
        sys.exit(1)
    return ruimte


M = laad_main()
fouten = []


def ok(wat, gekregen, verwacht):
    goed = gekregen == verwacht
    if not goed:
        fouten.append(f"{wat}: kreeg {gekregen!r}, verwacht {verwacht!r}")
    kort = repr(gekregen)
    if len(kort) > 58:
        kort = kort[:55] + "..."
    print(f"  {'ok ' if goed else 'FOUT'} {wat:<48} {kort}")


class NepSupabase:
    """Staat er alleen omdat herken_categorie een client verwacht."""

    def table(self, _n):
        return self

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        class R:
            data = []
        return R()


SB = NepSupabase()

print("\nDE VIJF LIJSTEN DIE DE VOEDINGSGROEPEN SCHEIDEN")
if not TS.exists():
    print(f"  OVERGESLAGEN - analyse-utils.ts niet gevonden op {TS}")
    print("  (het gedrag hieronder wordt nog wel bewaakt)")
else:
    ts = io.open(TS, encoding="utf-8").read()
    for ts_naam, py_naam in (("CAT_GROENTE", "_VG_CAT_GROENTE"),
                             ("CAT_FRUIT", "_VG_CAT_FRUIT"),
                             ("CAT_KNOL", "_VG_CAT_KNOL"),
                             ("GROENTE_NAMEN", "_VG_GROENTE_NAMEN"),
                             ("FRUIT_NAMEN", "_VG_FRUIT_NAMEN")):
        m = re.search(r"const\s+" + ts_naam + r"\s*=\s*\[([^\]]*)\]", ts)
        if not m:
            fouten.append(f"{ts_naam} niet gevonden in analyse-utils.ts")
            print(f"  FOUT {ts_naam} niet gevonden in analyse-utils.ts")
            continue
        uit_ts = list(re.findall(r'"([^"]*)"', m.group(1)))
        ok(f"{ts_naam} == {py_naam}", list(M[py_naam]), uit_ts)

    # CATEGORIE-KAAS-V1 — ook de categorievertaling vergelijken. Die stond
    # buiten deze test, en daardoor glipte er een gat doorheen: "Kaas",
    # "Melk", "Yoghurt en verse zuivel" en "Gevogelte" ontbraken in BEIDE
    # talen. Burrata en Cheddar kwamen als "Overige" uit de classificatie en
    # telden in het weekrapport bij dierlijk noch plantaardig eiwit.
    m = re.search(r"const CAT_NORM[^=]*=\s*{(.*?)\n}", ts, re.S)
    if not m:
        fouten.append("CAT_NORM niet gevonden in analyse-utils.ts")
        print("  FOUT CAT_NORM niet gevonden")
    else:
        kaal = re.sub(r"/[*].*?[*]/", "", m.group(1), flags=re.S)
        uit_ts = dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', kaal))
        ok("CAT_NORM == _VG_NORM (aantal)", len(M["_VG_NORM"]), len(uit_ts))
        ok("CAT_NORM == _VG_NORM (inhoud)", M["_VG_NORM"] == uit_ts, True)
        if M["_VG_NORM"] != uit_ts:
            alleen_py = set(M["_VG_NORM"]) - set(uit_ts)
            alleen_ts = set(uit_ts) - set(M["_VG_NORM"])
            if alleen_py:
                print(f"       alleen in Python: {sorted(alleen_py)}")
            if alleen_ts:
                print(f"       alleen in TS    : {sorted(alleen_ts)}")

    groepen = []
    for regel in ts.splitlines():
        if ".some(w => n.includes(w))" not in regel or '["' not in regel:
            continue
        g = re.search(r'return "([^"]+)"', regel)
        if g:
            groepen.append(g.group(1))
    verwacht = (["Snacks"] + [g for g, _ in M["_VG_VANGNET"]] +
                ["Sportvoeding", "Vetten & oliën"])
    ok("groepen en volgorde van het vangnet", groepen, verwacht)

print("\nHET GAT: EEN LOGREGEL ZONDER CATEGORIE")
ok("banaan zonder categorie", M["_voedingsgroep"]("Banaan", ""), "Fruit")
ok("banaan met categorie Overige", M["_voedingsgroep"]("Banaan", "Overige"), "Fruit")
ok("blauwe bes zonder categorie", M["_voedingsgroep"]("Blauwe bes", ""), "Fruit")
ok("kipfilet zonder categorie", M["_voedingsgroep"]("Kipfilet", ""), "Vlees & vis")
ok("volkorenbrood (substring!)", M["_voedingsgroep"]("Volkorenbrood", ""), "Granen & brood")
ok("onbekend blijft Overige", M["_voedingsgroep"]("Zzzz", ""), "Overige")

print("\nDE NAAMCORRECTIES VAN analyse-utils.ts")
ok("zoete aardappel is groente", M["_voedingsgroep"]("Zoete aardappel gek.", ""), "Groenten")
ok("gewone aardappel is graan", M["_voedingsgroep"]("Aardappel gekookt", ""), "Granen & brood")
ok("groentesoep is groente", M["_voedingsgroep"]("Groentesoep", ""), "Groenten")
ok("tropifruit is snoep", M["_voedingsgroep"]("Tropifruit", ""), "Snacks")
ok("skyr is zuivel", M["_voedingsgroep"]("Skyr naturel", ""), "Zuivel")

print()
print("CATEGORIEEN DIE DE NAAM NIET VERRAADT (CATEGORIE-KAAS-V1)")
# Burrata en Cheddar bevatten het woord "kaas" niet. Zonder de categorie
# "Kaas" in de vertaaltabel kwamen ze als "Overige" uit de classificatie en
# telden ze bij dierlijk noch plantaardig eiwit.
ok("burrata", M["_voedingsgroep"]("Burrata", "Kaas"), "Zuivel")
ok("cheddar", M["_voedingsgroep"]("Cheddar", "Kaas"), "Zuivel")
ok("brie", M["_voedingsgroep"]("Brie", "Kaas"), "Zuivel")
ok("eendenborst", M["_voedingsgroep"]("Eendenborst", "Gevogelte"), "Vlees & vis")
ok("griekse yoghurt", M["_voedingsgroep"]("Griekse yoghurt", "Yoghurt en verse zuivel"), "Zuivel")
ok("halfvolle melk", M["_voedingsgroep"]("Halfvolle melk", "Melk"), "Zuivel")

print()
print("KORTE WOORDEN BINNEN 'GROENTEN EN FRUIT' (KORT-WOORD-V1)")
# "ui" staat in CAT_GROENTE en zit in "fr-ui-t": alles met fruit in de naam
# kwam er als GROENTE uit. "sla" deed hetzelfde met "slagroom". Korte woorden
# worden hier nu op heel woord getoetst; langere blijven substring, want
# "tomat" moet kerstomaten blijven vangen.
GF = "Groenten en fruit"
ok("grapefruit", M["_voedingsgroep"]("Grapefruit", GF), "Fruit")
ok("druiven", M["_voedingsgroep"]("Druiven", GF), "Fruit")
ok("fruitsalade", M["_voedingsgroep"]("Fruitsalade", GF), "Fruit")
ok("vers fruit", M["_voedingsgroep"]("Vers fruit", GF), "Fruit")
ok("ui blijft groente", M["_voedingsgroep"]("Ui", GF), "Groenten")
ok("gemengde sla blijft groente", M["_voedingsgroep"]("Gemengde sla", GF), "Groenten")
ok("cherrytomaten (substring blijft)", M["_voedingsgroep"]("Cherrytomaten", GF), "Groenten")
ok("kerstomaatjes (substring blijft)", M["_voedingsgroep"]("Kerstomaatjes", GF), "Groenten")

print("\nDE HEEL-WOORDGEVALLEN")
ok("sla is groente", M["_voedingsgroep"]("Sla", ""), "Groenten")
ok("slagroom is dat niet", M["_voedingsgroep"]("Slagroom", ""), "Zuivel")
ok("peer is fruit", M["_voedingsgroep"]("Peer", ""), "Fruit")

print("\nWAT AL WERKTE, WERKT NOG")
ok("appel in Groenten en fruit", M["_voedingsgroep"]("Appel", "Groenten en fruit"), "Fruit")
ok("tomaat in Groenten en fruit", M["_voedingsgroep"]("Tomaat", "Groenten en fruit"), "Groenten")
ok("onbekende vrucht valt op Groenten", M["_voedingsgroep"]("Kaki", "Groenten en fruit"), "Groenten")

print("\nKNOL-FIX-V3: AARDAPPEL IS GEEN APPEL")
# NEVO zet "Aardappel gekookt" in de categorie "Groenten en fruit", en
# CAT_FRUIT matcht op substring: "appel" zit in "aardappel". Zonder de
# knollijst kwamen aardappelen bij het FRUIT terecht -- ook de zoete, waarvan
# de naamcorrectie nooit bereikt werd.
ok("aardappel is graan", M["_voedingsgroep"]("Aardappel gekookt", "Groenten en fruit"), "Granen & brood")
ok("puree ook", M["_voedingsgroep"]("Aardappelpuree", "Groenten en fruit"), "Granen & brood")
ok("friet ook", M["_voedingsgroep"]("Friet", "Groenten en fruit"), "Granen & brood")
ok("zoete aardappel blijft groente", M["_voedingsgroep"]("Zoete aardappel gek.", "Groenten en fruit"), "Groenten")
ok("en een echte appel blijft fruit", M["_voedingsgroep"]("Appel", "Groenten en fruit"), "Fruit")
# herken_categorie bestaat niet meer: hij was de laatste gebruiker van de
# oude weg en werd dood toen _voedingsgroep ook de eiwit-as overnam.

print("\nDE GRAMMEN VAN EEN LOGREGEL")
g, fr = M["_gf_gram"]({"naam": "Banaan", "categorie": "", "hoeveelheid_g": 120}, {}, SB)
ok("120 g banaan zonder categorie -> fruit", round(fr), 120)
ok("en niet bij groente", round(g), 0)
g, fr = M["_gf_gram"]({"naam": "Tomatensoep", "categorie": "Groenten en fruit",
                       "hoeveelheid_g": 200}, {}, SB)
ok("200 g soep telt VOL mee, zoals Analyses", round(g), 200)

print("\nEEN GELOGD RECEPT")
recept = {"id": "r1", "aantal_porties": 2, "ingredienten": [
    {"naam": "Gehakt", "gram": 300},
    {"naam": "Tomaat", "gram": 200},
    {"naam": "Spaghetti", "gram": 200},
]}
bib = {"gehakt": {"categorie": "Vlees"},
       "tomaat": {"categorie": "Groenten en fruit"},
       "spaghetti": {"categorie": "Granen en brood"}}
g, fr = M["_gf_gram"]({"naam": "Spaghetti bolognese", "recept_id": "r1",
                       "hoeveelheid_g": 100}, {"r1": recept}, SB, bib)
ok("alleen de tomaat telt als groente", round(g), 100)
ok("het gehakt niet meer", round(g) < 150, True)

print()
print("HET MAANDBORD GEBRUIKT DEZELFDE VERTALER (BORD-FRUIT-V2)")
# rol_van zit genest in get_bord en is niet los te laden; de brug ertussen
# wel. Voorheen besliste herken_categorie hier, en die heeft geen vangnet op
# de naam: een product zonder bruikbare categorie kreeg GEEN bordrol en viel
# als niet_ingedeeld van het bord. Dezelfde fout als bij het fruit.
def bordrol(naam, cat):
    return M["_bordrol_uit_groep"](M["_voedingsgroep"](naam, cat))

ok("banaan zonder categorie", bordrol("Banaan", ""), "fruit")
ok("kipfilet zonder categorie", bordrol("Kipfilet", ""), "eiwit")
ok("volkorenbrood zonder categorie", bordrol("Volkorenbrood", ""), "zetmeel")
ok("aardappel in Groenten en fruit", bordrol("Aardappel gekookt", "Groenten en fruit"), "zetmeel")
ok("zoete aardappel blijft groente", bordrol("Zoete aardappel gek.", "Groenten en fruit"), "groente")
ok("amandelen", bordrol("Amandelen", ""), "noten")
ok("olijfolie", bordrol("Olijfolie", ""), "vetstof")
# een gerecht heeft niet EEN rol, en onbekend blijft onbekend: allebei None,
# zodat ze als niet_ingedeeld zichtbaar blijven in plaats van stil bij een
# willekeurige rol te landen
ok("een gerecht krijgt geen rol", bordrol("Stoofpotje", "Maaltijden"), None)
ok("onbekend krijgt geen rol", bordrol("Zzzz", ""), None)

print()
print("DIERLIJK TEGENOVER PLANTAARDIG EIWIT")
# Deze as had een VIERDE classificeerder: _eiwit_categorie met een eigen
# lijst _RAAD_CATEGORIE, een kopie van de OUDE cascade uit analyse-utils.ts.
# Die vergeleek op woordbegin, dus "Volkorenbrood" kwam er als "Overige" uit
# en telde bij geen van beide. Nu loopt het via _voedingsgroep.
def as_eiwit(naam, cat):
    g = M["_voedingsgroep"](naam, cat)
    if g in M["_G_DIER"]:
        return "dierlijk"
    if g in M["_G_PLANT"]:
        return "plantaardig"
    return "geen van beide"

ok("kipfilet", as_eiwit("Kipfilet", ""), "dierlijk")
ok("griekse yoghurt", as_eiwit("Griekse yoghurt", ""), "dierlijk")
ok("tofu", as_eiwit("Tofu naturel", ""), "plantaardig")
ok("linzen", as_eiwit("Linzen gekookt", ""), "plantaardig")
ok("volkorenbrood (was Overige)", as_eiwit("Volkorenbrood", ""), "plantaardig")
ok("olijfolie telt niet mee", as_eiwit("Olijfolie", ""), "geen van beide")

print("\nKAN DEZE TEST ZELF FALEN?")
_echt = M["_vg_basis"]
M["_vg_basis"] = lambda naam, cat: "Overige"
_betrapt = M["_voedingsgroep"]("Banaan", "") != "Fruit"
M["_vg_basis"] = _echt
ok("een vertaler die niets herkent, wordt betrapt", _betrapt, True)

print()
if fouten:
    print(f"{len(fouten)} FOUT(EN):")
    for f in fouten:
        print(f"  - {f}")
    sys.exit(1)
print("alles klopt")
