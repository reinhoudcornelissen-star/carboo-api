"""COACHZONE-V2 — het coachdashboard geeft per klant de ongelezen reacties en de
volgende wedstrijd mee (voor het rode bolletje en het vlagje in de klantenlijst).
Zonder database: een nagemaakte Supabase-client.
Draaien: python lokaal-start.py tests/test_coach_dashboard.py"""
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
    def is_(self, k, v): self.f.append(lambda r: r.get(k) is None if v == "null" else r.get(k) == v); return self
    def or_(self, *a, **k): return self
    def order(self, k=None, desc=False, **kw):
        if k: self.f.append(("order", k, desc))
        return self
    def limit(self, *a, **k): return self
    def execute(self):
        fns = [x for x in self.f if callable(x)]
        rows = [r for r in self.db.setdefault(self.tabel, []) if all(fn(r) for fn in fns)]
        for x in self.f:
            if isinstance(x, tuple): rows.sort(key=lambda r: str(r.get(x[1]) or ""), reverse=x[2])
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
    "carboo_coaches": [{"id": "co1", "user_id": "coach-user", "naam": "Coach", "verified": True}],
    "carboo_coach_klanten": [
        {"id": "rel1", "coach_id": "co1", "klant_id": "k1", "klant_email": "k1@x.be", "status": "actief", "carboo_coach_privacy": {"training": True}},
        {"id": "rel2", "coach_id": "co1", "klant_id": "k2", "klant_email": "k2@x.be", "status": "actief", "carboo_coach_privacy": {}},
    ],
    "fuelc_profiel": [{"user_id": "k1", "voornaam": "Ann", "achternaam": "Peeters"}],
    "carboo_coach_opmerkingen": [
        {"id": "o1", "coach_id": "co1", "klant_id": "k1", "tekst": "x", "aangemaakt": "2026-11-01", "carboo_coach_reacties": [
            {"id": "r1", "auteur_type": "klant"}, {"id": "r2", "auteur_type": "klant"}, {"id": "r3", "auteur_type": "coach"}]},
        {"id": "o2", "coach_id": "co1", "klant_id": "k2", "tekst": "y", "aangemaakt": "2026-11-01", "carboo_coach_reacties": [{"id": "r4", "auteur_type": "klant"}]},
    ],
    "carboo_coach_reactie_gelezen": [{"coach_id": "co1", "reactie_id": "r1"}],
    "carboo_wedstrijden": [
        {"id": "w1", "user_id": "k1", "naam": "Oud", "datum": "2020-01-01", "prioriteit": "A"},
        {"id": "w2", "user_id": "k1", "naam": "Later", "datum": "2099-06-01", "prioriteit": "B"},
        {"id": "w3", "user_id": "k1", "naam": "Eerst", "datum": "2099-03-01", "prioriteit": "A"},
    ],
}
sb = FakeSB(db)
main.supabase_admin = sb
main.app.dependency_overrides[main.get_supabase] = lambda: sb
main.app.dependency_overrides[main.get_current_user] = lambda: U()
async def _geen_admin(user, supabase): return False
main.is_admin = _geen_admin
c = TestClient(main.app)

r = c.get("/api/coach/dashboard")
assert r.status_code == 200, r.text
d = r.json()
assert d["ongelezen_coach"] == 2, d["ongelezen_coach"]   # r2 en r4; r1 gelezen, r3 van de coach zelf
kl = {k["klant_id"]: k for k in d["klanten"]}
assert kl["k1"]["ongelezen"] == 1 and kl["k2"]["ongelezen"] == 1, kl
assert kl["k1"]["voornaam"] == "Ann"
assert kl["k1"]["volgende_wedstrijd"] == {"naam": "Eerst", "datum": "2099-03-01", "prioriteit": "A"}, kl["k1"]["volgende_wedstrijd"]
assert kl["k2"]["volgende_wedstrijd"] is None
print("ALLES OK")
