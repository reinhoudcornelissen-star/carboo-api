"""DOELTIJD-V1 — een wedstrijd bewaart haar doeltijden (seconden, totaal en per onderdeel),
geschoond: alleen getallen tussen 1 s en 48 u, hoogstens zes.
Draaien: python lokaal-start.py tests/test_doeltijden.py"""
import base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

s = main._wedstrijd_schoon
assert s({"doeltijden": {"totaal": 19800, "Zwemmen": "2400", "Fietsen": 10200.4, "Lopen": "6900"}})["doeltijden"] == \
    {"totaal": 19800, "Zwemmen": 2400, "Fietsen": 10200, "Lopen": 6900}
assert s({"doeltijden": {"totaal": 0, "Lopen": -5, "Fietsen": "abc", "x": 48 * 3600 + 1}})["doeltijden"] is None
assert s({"doeltijden": None})["doeltijden"] is None
assert s({"doeltijden": "5:30"})["doeltijden"] is None
assert len(s({"doeltijden": {str(i): 60 for i in range(10)}})["doeltijden"]) == 6
assert "doeltijden" not in s({"naam": "x"})   # niet meegegeven: niet aanraken bij een PUT
m = main.WedstrijdData(datum="2027-09-05", naam="Halve", doeltijden={"totaal": 19800})
assert s(m.dict())["doeltijden"] == {"totaal": 19800}
print("ALLES OK")
