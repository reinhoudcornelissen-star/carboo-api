"""COACH-TRAINING-V1 — de coach in de module Training van zijn klant, zonder
database: een nagemaakte Supabase-client met de tabellen in het geheugen.
Draaien: python lokaal-start.py tests/test_coach_training.py"""
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
    def or_(self, *a, **k): return self
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


class U: id = "coach-user"


db = {
    "carboo_coaches": [{"id": "co1", "user_id": "coach-user"}],
    "carboo_coach_klanten": [
        {"id": "rel1", "coach_id": "co1", "klant_id": "k1", "status": "actief", "carboo_coach_privacy": {"training": False}},
        {"id": "rel2", "coach_id": "co1", "klant_id": "k2", "status": "actief", "carboo_coach_privacy": [{"training": True}]},
    ],
    "fuelc_trainingen": [
        {"id": "t-gedaan", "user_id": "k2", "datum": "2026-10-01", "sport": "Lopen", "bron": "manueel", "gedaan_op": "2026-10-01T10:00:00"},
        {"id": "t-garmin", "user_id": "k2", "datum": "2026-10-02", "sport": "Fietsen", "bron": "garmin", "gedaan_op": None},
        {"id": "t-eigen", "user_id": "k2", "datum": "2099-01-05", "sport": "Lopen", "naam": "Duurloop", "bron": "manueel", "gedaan_op": None},
        {"id": "t-ander", "user_id": "k9", "datum": "2099-01-05", "sport": "Lopen", "bron": "manueel", "gedaan_op": None},
    ],
    "fuelc_profiel": [{"id": "pr1", "user_id": "k2", "gewicht_kg": 72}],
    "fuelc_zones": [{"id": "z1", "user_id": "k2", "sport": "Lopen", "z2_tempo_van": 5.5}],
    "carboo_wedstrijden": [{"id": "w-ander", "user_id": "k9", "naam": "niet van k2", "datum": "2099-06-01"}],
}
sb = FakeSB(db)
main.supabase_admin = sb
main.app.dependency_overrides[main.get_supabase] = lambda: sb
main.app.dependency_overrides[main.get_current_user] = lambda: U()
pushes = []
main.stuur_push_async = lambda *a, **k: pushes.append((a, k))
c = TestClient(main.app)
P = "/api/coach/klant/k2/training"

# ── toegang ──────────────────────────────────────────────────────────────
assert c.get("/api/coach/klant/k1/training/trainingen").status_code == 403, "vinkje uit → 403"
assert c.get("/api/coach/klant/k9/training/trainingen").status_code == 403, "geen relatie → 403"
assert c.get("/api/coach/klant/k2/training/trainingen").status_code == 200, "vinkje aan (als lijst uit de join) → ok"
print("toegang ok")

# ── profiel, zones, oefeningen van de klant ──────────────────────────────
assert c.get(P + "/profiel").json()["profiel"]["gewicht_kg"] == 72
assert c.get(P + "/zones/Lopen").json()["zones"]["z2_tempo_van"] == 5.5
assert c.get(P + "/zones/Zwemmen").json()["zones"] == {}
r = c.post(P + "/zones", json={"sport": "Fietsen", "z2_hs_van": 120, "bijgewerkt_door": "coach"})
assert r.status_code == 200 and [z for z in db["fuelc_zones"] if z["sport"] == "Fietsen"][0]["user_id"] == "k2"
assert c.get(P + "/oefeningen").status_code == 200
print("profiel/zones ok")

# ── trainingen ───────────────────────────────────────────────────────────
lijst = c.get(P + "/trainingen").json()["trainingen"]
assert {t["id"] for t in lijst} == {"t-gedaan", "t-garmin", "t-eigen"}, "alleen van k2"
r = c.post(P + "/trainingen", json={"datum": "2099-01-06", "sport": "Fietsen", "duur_min": 90, "naam": "Duurrit", "gedaan": True})
assert r.status_code == 200, r.text
nieuw = [t for t in db["fuelc_trainingen"] if t.get("naam") == "Duurrit"][0]
assert nieuw["user_id"] == "k2" and nieuw["bron"] == "coach" and nieuw["coach_id"] == "co1" and nieuw["gedaan_op"] is None, "bron coach, en gedaan telt niet voor de coach"
assert len(pushes) == 1 and pushes[0][0][0] == "k2", pushes
# wijzigen: gedane of Garmin-training niet, eigen geplande wel; afvinken mag niet
assert c.patch(P + "/trainingen/t-gedaan", json={"datum": "2099-01-07"}).status_code == 403
assert c.patch(P + "/trainingen/t-garmin", json={"datum": "2099-01-07"}).status_code == 403
assert c.patch(P + "/trainingen/t-ander", json={"datum": "2099-01-07"}).status_code == 404, "van iemand anders → niet gevonden"
r = c.patch(P + "/trainingen/t-eigen", json={"datum": "2099-01-08", "gedaan": True, "user_id": "hacker"})
assert r.status_code == 200 and r.json()["gewijzigd"] == ["datum"], r.text
eigen = [t for t in db["fuelc_trainingen"] if t["id"] == "t-eigen"][0]
assert eigen["datum"] == "2099-01-08" and eigen["gedaan_op"] is None and eigen["user_id"] == "k2"
# verwijderen
assert c.delete(P + "/trainingen/t-gedaan").status_code == 403
assert c.delete(P + "/trainingen/t-eigen").status_code == 200
assert not [t for t in db["fuelc_trainingen"] if t["id"] == "t-eigen"]
assert [t for t in db["fuelc_trainingen"] if t["id"] == "t-ander"], "van iemand anders blijft"
print("trainingen ok")

# ── signalen: hoogstens één open per dag, soort training ─────────────────
sig = db.get("carboo_coach_signalen") or []
assert len(sig) == 1 and sig[0]["klant_id"] == "k2" and sig[0]["soort"] == "training" and sig[0]["coach_id"] == "co1", sig
assert "haalde een training weg" in sig[0]["titel"], "de laatste tekst wint"
print("signaal ok")

# ── schema ───────────────────────────────────────────────────────────────
plan = {"invoer": {"start": "2099-01-05", "dagen": 4, "uren": 6},
        "weken": [{"nummer": 1, "blok": 1, "blokNaam": "Basis", "dagen": []}]}
r = c.post(P + "/plannen", json={"titel": "Van de coach", "startdatum": "2099-01-05", "invoer": plan["invoer"], "plan": plan})
assert r.status_code == 200, r.text
p = r.json()["plan"]
assert p["user_id"] == "k2" and p["coach_id"] == "co1" and p["titel"] == "Van de coach", p
assert len(pushes) == 2
assert [x["id"] for x in c.get(P + "/plannen").json()["plannen"]] == [p["id"]]
assert c.get("/api/coach/klant/k1/training/plannen").status_code == 403
r = c.put(P + f"/plannen/{p['id']}", json={"titel": "Aangepast", "user_id": "hacker"})
assert r.status_code == 200 and r.json()["plan"]["titel"] == "Aangepast" and r.json()["plan"]["user_id"] == "k2"
# week naar kalender: de rijen zijn van de coach, de gedane van de sporter blijft
db["fuelc_trainingen"].append({"id": "t-plan-gedaan", "user_id": "k2", "datum": "2099-01-05", "sport": "Lopen", "bron": "manueel",
                               "gedaan_op": "2099-01-05T09:00:00", "plan_id": p["id"]})
r = c.post(P + f"/plannen/{p['id']}/kalender", json={"van": "2099-01-05", "tot": "2099-01-11", "trainingen": [
    {"datum": "2099-01-05", "sport": "Lopen", "duur_min": 60, "naam": "op de gedane dag"},
    {"datum": "2099-01-06", "sport": "Fietsen", "duur_min": 90, "naam": "Duurrit", "afstand_km": 0},
    {"datum": "2099-01-08", "sport": "Lopen", "duur_min": 45, "naam": "Tempo"},
]})
assert r.status_code == 200, r.text
assert r.json()["gezet"] == 2 and r.json()["overgeslagen"] == 1, r.json()
gezet = [t for t in db["fuelc_trainingen"] if t.get("plan_id") == p["id"] and not t.get("gedaan_op")]
assert len(gezet) == 2 and all(t["bron"] == "coach" and t["coach_id"] == "co1" and t["user_id"] == "k2" for t in gezet), gezet
gedaan = [t for t in db["fuelc_trainingen"] if t["id"] == "t-plan-gedaan"][0]
assert gedaan["bron"] == "manueel" and "coach_id" not in gedaan, "de gedane blijft van de sporter"
assert len(pushes) == 3
wk = c.get(P + f"/plannen/{p['id']}/kalender?van=2099-01-05&tot=2099-01-11").json()
assert len(wk["trainingen"]) == 4 and sum(1 for t in wk["trainingen"] if t["van_plan"]) == 3, wk   # + de losse coachtraining van 6 januari
assert c.delete(P + f"/plannen/{p['id']}").status_code == 200
assert c.get(P + "/plannen").json()["plannen"] == []
print("schema ok")

# ── wedstrijden ──────────────────────────────────────────────────────────
r = c.post(P + "/wedstrijden", json={"datum": "2099-05-01", "naam": "Marathon", "prioriteit": "A"})
assert r.status_code == 200 and r.json()["wedstrijd"]["user_id"] == "k2", r.text
w = r.json()["wedstrijd"]
assert [x["id"] for x in c.get(P + "/wedstrijden").json()["wedstrijden"]] == [w["id"]], "alleen van k2"
assert c.put(P + f"/wedstrijden/{w['id']}", json={"naam": "Marathon Rotterdam"}).json()["wedstrijd"]["naam"] == "Marathon Rotterdam"
assert c.put(P + "/wedstrijden/w-ander", json={"naam": "x"}).status_code == 404
assert c.delete(P + f"/wedstrijden/{w['id']}").status_code == 200
assert c.get(P + "/wedstrijden").json()["wedstrijden"] == []
assert [x for x in db["carboo_wedstrijden"] if x["id"] == "w-ander"], "van iemand anders blijft"
assert len(pushes) == 3, "wedstrijden geven geen push, wel een signaal"
print("wedstrijden ok")

# ── privacy: het vinkje komt binnen via PUT /api/coach/privacy ───────────
class K: id = "k2"
main.app.dependency_overrides[main.get_current_user] = lambda: K()
db["carboo_coach_privacy"] = [{"id": "pv2", "relatie_id": "rel2", "klant_id": "k2", "training": False}]
r = c.put("/api/coach/privacy/rel2", json={"relatie_id": "rel2", "training": True})
assert r.status_code == 200 and db["carboo_coach_privacy"][0]["training"] is True, r.text
r = c.put("/api/coach/privacy/rel2", json={"relatie_id": "rel2"})
assert r.status_code == 200 and db["carboo_coach_privacy"][0]["training"] is True, "niet meegestuurd (oudere app) → ongemoeid"
print("privacy ok")
print("ALLES OK")
