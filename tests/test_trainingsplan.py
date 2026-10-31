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
    def gte(self, k, v): self.f.append(lambda r: str(r.get(k)) >= str(v)); return self
    def lte(self, k, v): self.f.append(lambda r: str(r.get(k)) <= str(v)); return self
    def in_(self, k, vs): self.f.append(lambda r: str(r.get(k)) in {str(x) for x in vs}); return self
    def order(self, *a, **k): return self
    def limit(self, *a, **k): return self
    def execute(self):
        rows = [r for r in self.db.setdefault(self.tabel, []) if all(fn(r) for fn in self.f)]
        if self.op[0] == "insert":
            lijst = self.op[1] if isinstance(self.op[1], list) else [self.op[1]]
            rows = []
            for d in lijst:
                r = {"id": f"{self.tabel[:1]}{len(self.db[self.tabel]) + 1}", **d}; self.db[self.tabel].append(r); rows.append(r)
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

# PLAN-KALENDER-V1 — een week naar de kalender
main._vandaag_brussel = lambda: "2026-11-04"   # woensdag; maandag en dinsdag liggen in het verleden
db["fuelc_trainingen"] = [
    {"id": "t1", "user_id": "u1", "datum": "2026-11-03", "sport": "Fietsen", "duur_min": 60, "bron": "manueel", "gedaan_op": None, "plan_id": p1["id"]},   # oud plan, gepland → weg
    {"id": "t2", "user_id": "u1", "datum": "2026-11-04", "sport": "Fietsen", "duur_min": 90, "bron": "garmin", "gedaan_op": None, "plan_id": p1["id"]},     # oud plan, gedaan → blijft, dag bezet
    {"id": "t3", "user_id": "u1", "datum": "2026-11-05", "sport": "Lopen", "duur_min": 40, "bron": "manueel", "gedaan_op": None, "plan_id": None},         # eigen training → kiest de sporter
    {"id": "t4", "user_id": "u1", "datum": "2026-11-06", "sport": "Zwemmen", "duur_min": 45, "bron": "manueel", "gedaan_op": None, "plan_id": None},       # eigen training, blijft
    {"id": "t5", "user_id": "u2", "datum": "2026-11-05", "sport": "Lopen", "duur_min": 40, "bron": "manueel", "gedaan_op": None, "plan_id": None},         # van een ander
]
w = c.get(f"/api/trainingsplannen/{p1['id']}/kalender", params={"van": "2026-11-02", "tot": "2026-11-08"}).json()
assert [x["id"] for x in w["trainingen"]] == ["t1", "t2", "t3", "t4"], w
assert [x["gedaan"] for x in w["trainingen"]] == [False, True, False, False] and [x["van_plan"] for x in w["trainingen"]] == [True, True, False, False], w
assert c.get("/api/trainingsplannen/ander/kalender", params={"van": "2026-11-02", "tot": "2026-11-08"}).status_code == 404
assert c.get(f"/api/trainingsplannen/{p1['id']}/kalender", params={"van": "2 nov", "tot": "2026-11-08"}).status_code == 400
sessies = [
    {"datum": "2026-11-02", "sport": "Fietsen", "duur_min": 60, "naam": "Duur", "starttijd": "18:00"},                       # maandag: verleden → overgeslagen
    {"datum": "2026-11-04", "sport": "Fietsen", "duur_min": 70, "naam": "Drempel", "starttijd": "18:00"},                    # woensdag: gedane plansessie → overgeslagen
    {"datum": "2026-11-05", "sport": "Fietsen", "duur_min": 75, "naam": "Duur", "zone_verdeling": [{"naam": "Duurblok", "duur_min": 75, "zone": "Z2"}], "kcal_verbranding": 600.4, "notitie": "Rustig", "starttijd": "18:00"},
    {"datum": "2026-11-06", "sport": "Krachttraining", "duur_min": 45, "naam": "Kracht", "starttijd": "18:00"},
    {"datum": "2026-11-08", "sport": "Fietsen", "duur_min": 180, "naam": "Lange rit", "starttijd": "09:00", "user_id": "hacker", "bron": "garmin"},
]
r = c.post(f"/api/trainingsplannen/{p1['id']}/kalender", json={"van": "2026-11-02", "tot": "2026-11-08", "trainingen": sessies, "vervang_ids": ["t3", "t4", "t5", "t2"]})
assert r.status_code == 200, r.text
assert r.json() == {"ok": True, "gezet": 3, "verwijderd": 3, "overgeslagen": 2}, r.json()   # weg: t1 (oud plan), t3 en t4 (gekozen); t2 gedaan blijft, t5 niet van u1
ids = {x["id"] for x in db["fuelc_trainingen"]}
assert "t1" not in ids and "t3" not in ids and "t4" not in ids and "t2" in ids and "t5" in ids, ids
nieuwe = [x for x in db["fuelc_trainingen"] if x.get("plan_id") == p1["id"] and x["id"] not in ("t2",)]
assert sorted(x["datum"] for x in nieuwe) == ["2026-11-05", "2026-11-06", "2026-11-08"], nieuwe
for x in nieuwe:
    assert x["user_id"] == "u1" and x["bron"] == "manueel" and x["gedaan_op"] is None and x["plan_id"] == p1["id"], x
zondag = next(x for x in nieuwe if x["datum"] == "2026-11-08"); assert zondag["starttijd"] == "09:00" and zondag["duur_min"] == 180
donderdag = next(x for x in nieuwe if x["datum"] == "2026-11-05"); assert donderdag["zone_verdeling"] == '[{"naam": "Duurblok", "duur_min": 75, "zone": "Z2"}]' and donderdag["kcal_verbranding"] == 600 and donderdag["notitie"] == "Rustig"
assert c.post(f"/api/trainingsplannen/{p1['id']}/kalender", json={"van": "2026-11-02", "tot": "2026-11-20", "trainingen": []}).status_code == 400
assert c.post("/api/trainingsplannen/ander/kalender", json={"van": "2026-11-02", "tot": "2026-11-08", "trainingen": []}).status_code == 404
# nog eens dezelfde week: de drie nieuwe plansessies worden vervangen, niets dubbel
r = c.post(f"/api/trainingsplannen/{p1['id']}/kalender", json={"van": "2026-11-02", "tot": "2026-11-08", "trainingen": sessies}).json()
assert r == {"ok": True, "gezet": 3, "verwijderd": 3, "overgeslagen": 2}, r
assert len([x for x in db["fuelc_trainingen"] if x.get("plan_id") == p1["id"]]) == 4, db["fuelc_trainingen"]
print("kalender ok")

# verwijderen, niet van een ander
assert c.delete("/api/trainingsplannen/ander").json() == {"ok": True}
assert any(p["id"] == "ander" for p in db["carboo_trainingsplannen"]), "plan van een ander blijft"
assert c.delete(f"/api/trainingsplannen/{p1['id']}").json() == {"ok": True}
assert c.get("/api/trainingsplannen").json()["plannen"] == []
print("verwijderen ok")
print("ALLES OK")
