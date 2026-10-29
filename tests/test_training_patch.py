"""BOUWER-V1 — de PATCH-route van een training, zonder database: een
nagemaakte Supabase-client registreert wat de route zou wegschrijven.
Draaien: python lokaal-start.py tests/test_training_patch.py"""
import base64, os, secrets, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class Q:
    def __init__(self, log, tabel): self.log, self.tabel, self.op = log, tabel, None
    def update(self, d): self.op = ("update", d); return self
    def select(self, *a, **k): self.op = ("select", a); return self
    def eq(self, *a): self.log.append((self.tabel, "eq", a)); return self
    def execute(self):
        self.log.append((self.tabel, self.op))
        class R: data = [{"id": "t1"}]
        return R()


class FakeSB:
    def __init__(self): self.log = []
    def table(self, naam): return Q(self.log, naam)


class U: id = "user-1"


sb = FakeSB()
main.app.dependency_overrides[main.get_current_user] = lambda: U()
main.app.dependency_overrides[main.get_supabase] = lambda: sb
c = TestClient(main.app)

# precies wat de bouwer stuurt bij "Wijzigen"
payload = {"datum": "2026-11-02", "sport": "Fietsen", "starttijd": "07:00", "notitie": "", "naam": "5 x 4 drempel",
           "duur_min": 75, "kcal_verbranding": 640, "afstand_km": 0,
           "zone_verdeling": json.dumps([{"naam": "Opwarming", "duur_min": 15, "zone": "Z1"}])}
r = c.patch("/api/fuelc/trainingen/t1", json=payload)
print("status", r.status_code, r.text[:120])
assert r.status_code == 200, r.text
upd = [x for x in sb.log if x[0] == "fuelc_trainingen" and x[1] and x[1][0] == "update"][0][1][1]
assert set(upd) == set(payload), upd
print("velden doorgegeven:", sorted(upd))

# datum ontbreekt (alleen naam): mag ook
r = c.patch("/api/fuelc/trainingen/t1", json={"naam": "x"})
assert r.status_code == 200, r.text
# verboden velden worden genegeerd, lege wijziging is 400
r = c.patch("/api/fuelc/trainingen/t1", json={"user_id": "ander", "bron": "coach"})
assert r.status_code == 400, r.text
print("ALLES OK")
