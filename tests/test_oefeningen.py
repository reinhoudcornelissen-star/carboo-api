"""OEFENINGEN-V2 — historiek en 'laatste waarden' van krachtoefeningen,
zonder database: een nagemaakte Supabase-client met trainingen in het
geheugen. Alleen gedane trainingen tellen (GEDAAN-V1).
Draaien: python lokaal-start.py tests/test_oefeningen.py"""
import base64, json, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def seg(oid, naam, **k):
    return {"naam": naam, "zone": "Z2", "duur_min": 5, "kracht": {"oefening_id": oid, "naam": naam, **k}}


# ── de parser: tekst of lijst, vreemde dingen genegeerd ─────────────
segs = [{"naam": "Kracht", "duur_min": 45, "zone": "Z2", "kracht_sessie": {"focus": ["benen"], "intensiteit": "matig"}},
        seg("squat", "Squat", sets=4, reps=8, gewicht_kg=60, rust_s=90),
        "rommel", {"naam": "zonder kracht"}]
assert [k["oefening_id"] for k in main._kracht_oefeningen_van({"zone_verdeling": json.dumps(segs)})] == ["squat"]
assert [k["oefening_id"] for k in main._kracht_oefeningen_van({"zone_verdeling": segs})] == ["squat"]
assert main._kracht_oefeningen_van({"zone_verdeling": "{kapot"}) == []
assert main._kracht_oefeningen_van({"zone_verdeling": None}) == []
w = main._kracht_waarden({"sets": "3", "reps": 12, "gewicht": 20, "rust_s": 60}, "2026-10-20")
assert w["sets"] == 3 and w["reps"] == 12 and w["gewicht_kg"] == 20 and w["volume"] == 720 and w["seconden"] is None, w
w = main._kracht_waarden({"sets": 3, "seconden": 40, "per_kant": True}, "2026-10-20")
assert w["seconden"] == 40 and w["per_kant"] is True and w["gewicht_kg"] is None and w["volume"] == 0, w
print("parser ok")


# ── nagemaakte Supabase ─────────────────────────────────────────────
class Q:
    def __init__(self, db, tabel): self.db, self.tabel, self.f = db, tabel, []
    def select(self, *a, **k): return self
    def eq(self, k, v): self.f.append(lambda r: str(r.get(k)) == str(v)); return self
    def order(self, k, desc=False): self.sort = (k, desc); return self
    def limit(self, n): self.n = n; return self
    def execute(self):
        rows = [r for r in self.db.get(self.tabel, []) if all(fn(r) for fn in self.f)]
        k, desc = getattr(self, "sort", ("datum", True))
        rows = sorted(rows, key=lambda r: str(r.get(k)), reverse=desc)[:getattr(self, "n", 999)]
        class R: data = rows
        return R()


class FakeSB:
    def __init__(self, db): self.db = db
    def table(self, naam): return Q(self.db, naam)


class U: id = "u1"


db = {"fuelc_trainingen": [
    # gepland voor morgen, nog niet gedaan: telt niet
    {"id": "t4", "user_id": "u1", "datum": "2026-11-01", "bron": "manueel", "gedaan_op": None,
     "zone_verdeling": json.dumps([seg("squat", "Squat", sets=5, reps=5, gewicht_kg=80, rust_s=120)])},
    # gisteren afgevinkt
    {"id": "t3", "user_id": "u1", "datum": "2026-10-29", "bron": "manueel", "gedaan_op": "2026-10-29T19:00:00",
     "zone_verdeling": json.dumps([seg("squat", "Squat", sets=4, reps=8, gewicht_kg=60, rust_s=90),
                                   seg("plank", "Plank", sets=3, seconden=45, rust_s=30)])},
    # vorige week via Garmin (plan overgenomen, oefeningen blijven staan)
    {"id": "t2", "user_id": "u1", "datum": "2026-10-22", "bron": "garmin", "gedaan_op": None,
     "zone_verdeling": json.dumps([seg("squat", "Squat", sets=3, reps=10, gewicht=50, rust_s=90),
                                   seg("rdl", "Romanian deadlift", sets=3, reps=10, gewicht_kg=40)])},
    # van iemand anders
    {"id": "t9", "user_id": "u2", "datum": "2026-10-30", "bron": "manueel", "gedaan_op": "2026-10-30T10:00:00",
     "zone_verdeling": json.dumps([seg("squat", "Squat", sets=10, reps=10, gewicht_kg=100)])},
    # duurtraining zonder oefeningen
    {"id": "t1", "user_id": "u1", "datum": "2026-10-28", "bron": "strava", "gedaan_op": None,
     "zone_verdeling": json.dumps([{"naam": "Z2", "duur_min": 60, "zone": "Z2"}])},
]}
main.app.dependency_overrides[main.get_current_user] = lambda: U()
main.app.dependency_overrides[main.get_supabase] = lambda: FakeSB(db)
c = TestClient(main.app)

# ── laatste waarden per oefening ────────────────────────────────────
r = c.get("/api/fuelc/oefeningen/laatste")
assert r.status_code == 200, r.text
la = r.json()["laatste"]
assert set(la) == {"squat", "plank", "rdl"}, la
assert la["squat"]["datum"] == "2026-10-29" and la["squat"]["sets"] == 4 and la["squat"]["gewicht_kg"] == 60, "geplande van morgen telt niet, gisteren wel"
assert la["plank"]["seconden"] == 45 and la["plank"]["reps"] is None
assert la["rdl"]["datum"] == "2026-10-22" and la["rdl"]["gewicht_kg"] == 40
print("laatste ok")

# ── historiek van één oefening ──────────────────────────────────────
r = c.get("/api/fuelc/oefeningen/squat/historiek")
assert r.status_code == 200, r.text
h = r.json()["historiek"]
assert [x["datum"] for x in h] == ["2026-10-29", "2026-10-22"], h
assert h[1]["gewicht_kg"] == 50, "oud veld 'gewicht' wordt ook gelezen"
assert h[0]["volume"] == 4 * 8 * 60
assert c.get("/api/fuelc/oefeningen/bestaat-niet/historiek").json()["historiek"] == []
print("historiek ok")

# ── databank valt uit: lege lijst, geen 500 ─────────────────────────
class Kapot:
    def table(self, naam): raise RuntimeError("geen verbinding")
main.app.dependency_overrides[main.get_supabase] = lambda: Kapot()
assert c.get("/api/fuelc/oefeningen/laatste").json() == {"laatste": {}}
assert c.get("/api/fuelc/oefeningen/squat/historiek").json() == {"historiek": []}
print("uitval ok")
print("ALLES OK")
