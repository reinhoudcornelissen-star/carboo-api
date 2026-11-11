"""KRANT-TOON-V1 en WEEKBORD-V1 (11 november 2026).

De vaststellingen onder "Kwaliteit van je voeding" kennen drie trappen:
wie minstens 85 procent van een richtlijn haalt, krijgt "bijna" in plaats van
een tekort. Op het blad staat eerst wat goed zit, dan wat bijna rond is, dan
de werkpunten; een werkpunt valt nooit weg achter groene.

Draaien:  python tests/test_krant_toon.py
Geen database, geen netwerk.
"""
import base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


class Nul(dict):
    """Wat het rapport verder nog opvraagt en hier niet toe doet, is 0."""
    def __missing__(self, k):
        return 0


def rapport(**per_dag):
    basis = dict(kcal=2500, kcal_voeding=2500, groenten=350, fruit=250, suikers_toegevoegd=20, zetmeel=200, kh=350,
                 verzadigd=20, vocht=1800, drankdagen=6, omega3=2.0, vezels=35)
    basis.update(per_dag)
    dagen = {f"2026-11-0{i}": Nul(groenten=basis["groenten"]) for i in range(2, 9)}
    res = Nul(per_dag=Nul(basis), normen=[], dagen_gelogd=7, alleen_volledig=True)
    return main._bouw_inzichten(res, dagen, {}, [])


def koppen(r):
    return [(i["ernst"], i["kop"]) for i in r["inzichten_kwaliteit"]]


# 1. de cijfers van de schermafbeelding: fruit 148/200 is een werkpunt, de drie andere zijn bijna rond
r = rapport(fruit=148, vocht=1400, omega3=1.4, vezels=26)
k = koppen(r)
assert ("geel", "Fruit is je makkelijkste winst") in k, k
assert ("bijna", "Nog één glas en je drinkt genoeg") in k, k
assert ("bijna", "Je omega 3 zit er bijna") in k, k
assert ("bijna", "Je vezels zitten er bijna") in k, k
# eerst wat goed zit, dan bijna, dan het werkpunt
ernst = [e for e, _ in k]
assert ernst == sorted(ernst, key=["groen", "bijna", "geel", "rood"].index), ernst
assert ernst[0] == "groen" and ernst.count("groen") >= 2, ernst
tekst = next(i["tekst"] for i in r["inzichten_kwaliteit"] if i["kop"] == "Je omega 3 zit er bijna")
assert "1,4 gram per dag, de richtlijn is 1,5" in tekst, tekst
print("bijna ok")

# 2. ver onder de richtlijn: de kop benoemt de stap, de oude woorden zijn weg
r = rapport(groenten=100, fruit=50, vocht=800, omega3=0.3, vezels=12)
k = koppen(r)
for kop in ("Een portie groenten erbij", "Fruit is je makkelijkste winst", "Meer drinken loont", "Omega 3 kan omhoog"):
    assert ("geel", kop) in k, (kop, k)
alles = " ".join(i["kop"] + " " + i["tekst"] for i in r["inzichten_kwaliteit"]) + " " + r["kop"]
for oud in ("blijft achter", "blijven achter", "te weinig", "Weinig omega"):
    assert oud not in alles, (oud, alles)
# vijf werkpunten: er is plaats voor vier, plus twee die goed zitten
assert [e for e, _ in k].count("geel") == 4 and [e for e, _ in k].count("groen") == 2, k
print("werkpunten ok")

# 3. een overschrijding blijft rood en valt nooit weg
r = rapport(suikers_toegevoegd=120, verzadigd=60, groenten=100, fruit=50, vocht=800, omega3=0.3, vezels=12)
k = koppen(r)
assert ("rood", "Toegevoegde suiker mag wat lager") in k and ("rood", "Je verzadigd vet mag wat lager") in k, k
assert len(k) <= 6, k
print("rood ok")

# 4. alles goed: alleen groen
r = rapport()
assert {e for e, _ in koppen(r)} == {"groen"}, koppen(r)
print("ALLES OK")
