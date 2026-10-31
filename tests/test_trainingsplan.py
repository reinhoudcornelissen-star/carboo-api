"""TRAININGSPLAN-V1 — de routes voor het trainingsplan, zonder database:
een nagemaakte Supabase-client met de tabel in het geheugen.
Draaien: python lokaal-start.py tests/test_trainingsplan.py"""
import base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class Q:
    def __init__(self, db, tabel): self.db, self.tabel, self.f, self.op = db, tabel, [], ("select",)
    def select(self, *a, **k): return self
    def insert(self, d): self.op = ("insert", d); return self
    def update(self, d): self.op = ("update", d); return self
    def delete(self): self.op = ("delete",); return self
    def eq(self, k, v): self.f.append(lambda r: str(r.get(k)) == str(v)); return self
    def order(self, *a, **k): return self
    def execute(self):
        rows = [r for r in self.db.setdefault(self.tabel, []) if all(fn(r) for fn in self.f)]
        if self.op[0] == "insert":
            r = {"id": f"p{len(self.db[self.tabel]) + 1}", **self.op[1]}; self.db[self.tabel].append(r); rows = [r]
        elif self.op[0] == "update":
            for r in rows: r.update(self.op[1])
        elif self.op[0] == "delete":
            self.db[self.tabel] = [r for r in self.db[self.tabel] if r not in rows]
        class R: data = rows
        return R()


class FakeSB:
    def __init__(self, db): self.db = db
    def table(self, naam): return Q(self.db, naam)


class U: id = "u1"


db = {}
main.supabase_admin = FakeSB(db)
main.app.dependency_overrides[main.get_current_user] = lambda: U()
c = TestClient(main.app)

plan = {"invoer": {"start": "2026-11-02", "dagen": 4, "uren": 6}, "weken": [{"nummer": 1, "blok": 1, "blokNaam": "Basis", "dagen": []}]}

# aanmaken
r = c.post("/api/trainingsplannen", json={"titel": "  Mijn plan  ", "startdatum": "2026-11-02", "invoer": plan["invoer"], "plan": plan, "eenheid": "watt"})
assert r.status_code == 200, r.text
p1 = r.json()["plan"]; assert p1["titel"] == "Mijn plan" and p1["user_id"] == "u1" and p1["plan"]["weken"], p1
# zonder weken: 400
assert c.post("/api/trainingsplannen", json={"titel": "x", "startdatum": "2026-11-02", "invoer": {}, "plan": {"weken": []}}).status_code == 400
assert c.post("/api/trainingsplannen", json={"titel": "x", "startdatum": "2 nov", "invoer": {}, "plan": plan}).status_code == 400
print("aanmaken ok")

# lijst, alleen van deze sporter
db["carboo_trainingsplannen"].append({"id": "ander", "user_id": "u2", "titel": "van iemand anders", "plan": plan})
lijst = c.get("/api/trainingsplannen").json()["plannen"]
assert [p["id"] for p in lijst] == [p1["id"]], lijst
print("lijst ok")

# wijzigen: alleen toegelaten velden, plan gecontroleerd
r = c.put(f"/api/trainingsplannen/{p1['id']}", json={"titel": "Nieuw", "user_id": "hacker", "plan": {**plan, "opmerkingen": ["x"]}})
assert r.status_code == 200 and r.json()["plan"]["titel"] == "Nieuw" and r.json()["plan"]["user_id"] == "u1" and r.json()["plan"]["updated_at"], r.text
assert c.put(f"/api/trainingsplannen/{p1['id']}", json={"plan": {"weken": []}}).status_code == 400
assert c.put(f"/api/trainingsplannen/{p1['id']}", json={}).status_code == 400
assert c.put("/api/trainingsplannen/ander", json={"titel": "gekaapt"}).status_code == 404
print("wijzigen ok")

# verwijderen, niet van een ander
assert c.delete("/api/trainingsplannen/ander").json() == {"ok": True}
assert any(p["id"] == "ander" for p in db["carboo_trainingsplannen"]), "plan van een ander blijft"
assert c.delete(f"/api/trainingsplannen/{p1['id']}").json() == {"ok": True}
assert c.get("/api/trainingsplannen").json()["plannen"] == []
print("verwijderen ok")
print("ALLES OK")
