"""KOPPEL-OPRUIM-V1 — Garmin- en Strava-koppelingen van wie niet (meer) betaalt, komen
vrij: alleen proef gehad → de dag na het verlopen; ooit betaald → na 14 dagen gratie.
Zonder database of Garmin/Strava: nagemaakte client, losmaken gemonkeypatcht.
Draaien: python lokaal-start.py tests/test_koppel_opruim.py"""
import base64, os, secrets, sys
from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
os.environ["CRON_SLEUTEL"] = "test-sleutel"
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
    def lt(self, k, v): self.f.append(lambda r: str(r.get(k)) < str(v)); return self
    def in_(self, k, vs): self.f.append(lambda r: str(r.get(k)) in {str(x) for x in vs}); return self
    def is_(self, k, v): self.f.append(lambda r: r.get(k) is None if v == "null" else r.get(k) == v); return self
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


vandaag = date.today()
d = lambda n: (vandaag + timedelta(days=n)).isoformat()   # noqa: E731
PROEF = "trial_auto_7d"


def abo(uid, pakket, verval, mpid="tr_betaald", status="actief", bonus=False):
    return {"user_id": uid, "pakket": pakket, "verval_datum": verval, "mollie_payment_id": mpid, "status": status, "bonus_training": bonus}


# ── de beslisregel los ───────────────────────────────────────────────────────
B = main._opruim_beslissing
V = vandaag.isoformat()
assert B([abo("u", "alles", d(1), PROEF)], V) is None, "proef loopt nog"
assert B([abo("u", "alles", d(0), PROEF)], V) is None, "op de vervaldag zelf nog niet"
assert B([abo("u", "alles", d(-1), PROEF)], V) == "proef", "dag na het verlopen"
assert B([abo("u", "alles", d(-1), PROEF, status="verlopen")], V) == "proef", "status al op verlopen gezet"
assert B([abo("u", "training", d(-3))], V) is None, "betaald, binnen de gratie"
assert B([abo("u", "training", d(-14))], V) is None, "precies 14 dagen: nog gratie"
assert B([abo("u", "training", d(-15))], V) == "verlopen", "gratie voorbij"
assert B([abo("u", "alles", d(-20), PROEF), abo("u", "fueling", d(30))], V) == "proef", "fueling zonder bonus geeft geen training"
assert B([abo("u", "fueling", d(30), bonus=True)], V) is None, "fueling met bonus_training geeft training"
assert B([abo("u", "fueling_training", d(5))], V) is None
assert B([abo("u", "coach", None)], V) is None, "zonder vervaldatum: loopt"
assert B([], V) == "proef", "nooit een abonnement: vrijmaken"
assert B([abo("u", "alles", d(-20), PROEF), abo("u", "training", d(-3))], V) is None, "proef verlopen maar betaald en in gratie"

# ── de route ─────────────────────────────────────────────────────────────────
db = {
    "carboo_garmin_koppelingen": [{"user_id": "u1"}, {"user_id": "u3"}, {"user_id": "u5"}],
    "carboo_garmin_koppelpogingen": [{"user_id": "u1"}],
    "carboo_strava_koppelingen": [{"user_id": "u2", "access_token": "x"}, {"user_id": "u3", "access_token": "x"}, {"user_id": "u4", "access_token": "x"}],
    "carboo_abonnementen": [
        abo("u1", "alles", d(-1), PROEF),            # proef verlopen → los (garmin)
        abo("u2", "alles", d(1), PROEF),             # proef loopt → blijft
        abo("u3", "training", d(-3)),                # betaald, gratie → blijft
        abo("u4", "alles", d(-20)),                  # betaald, gratie voorbij → los (strava)
        abo("u5", "alles", d(-5), PROEF), abo("u5", "fueling", d(40)),   # fueling zonder training → los
    ],
}
sb = FakeSB(db)
main.supabase_admin = sb
main.app.dependency_overrides[main.get_supabase] = lambda: sb
garmin_af, strava_af, pushes = [], [], []
async def _garmin_toegang_nep(uid):
    rij = [r for r in db["carboo_garmin_koppelingen"] if r["user_id"] == uid]
    return (rij[0], "token") if rij else (None, None)
main._garmin_toegang = _garmin_toegang_nep
class _Resp: status_code = 204
class _Client:
    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def delete(self, url, **k): garmin_af.append(url); return _Resp()
    async def post(self, url, **k): strava_af.append(url); return _Resp()
main.httpx.AsyncClient = _Client
async def _refresh_nep(k, sb): return k["access_token"]
main._refresh_token_indien_nodig = _refresh_nep
main.stuur_push = lambda uid, titel, tekst, **k: pushes.append((uid, titel)) or 1
c = TestClient(main.app)

r = c.post("/api/cron/koppelingen-opruimen")
assert r.status_code == 403, r.text
H = {"x-cron-sleutel": "test-sleutel"}

r = c.post("/api/cron/koppelingen-opruimen?droog=true", headers=H)
assert r.status_code == 200, r.text
j = r.json()
assert j["droog"] and j["gecontroleerd"] == 5, j
assert {(x["user_id"], x["reden"]) for x in j["losgemaakt"]} == {("u1", "proef"), ("u4", "verlopen"), ("u5", "proef")}, j
assert len(db["carboo_garmin_koppelingen"]) == 3 and len(db["carboo_strava_koppelingen"]) == 3, "droog wist niets"
assert not garmin_af and not strava_af and not pushes

r = c.post("/api/cron/koppelingen-opruimen", headers=H)
assert r.status_code == 200, r.text
j = r.json()
los = {x["user_id"]: x for x in j["losgemaakt"]}
assert set(los) == {"u1", "u4", "u5"}, j
assert los["u1"]["garmin"] and not los["u1"]["strava"]
assert los["u4"]["strava"] and not los["u4"]["garmin"]
assert [r["user_id"] for r in db["carboo_garmin_koppelingen"]] == ["u3"], db["carboo_garmin_koppelingen"]
assert db["carboo_garmin_koppelpogingen"] == []
assert sorted(r["user_id"] for r in db["carboo_strava_koppelingen"]) == ["u2", "u3"]
assert len(garmin_af) == 2 and all(u.endswith("/user/registration") for u in garmin_af), garmin_af
assert strava_af == ["https://www.strava.com/oauth/deauthorize"], strava_af
assert sorted(p[0] for p in pushes) == ["u1", "u4", "u5"], pushes
assert "Garmin" in dict(pushes)["u1"] and "Strava" in dict(pushes)["u4"]

# ── de camera-cron neemt de opruiming mee (geen aparte Render Cron Job) ───────
db["carboo_strava_koppelingen"].append({"user_id": "u6", "access_token": "x"})
db["carboo_abonnementen"].append(abo("u6", "alles", d(-2), PROEF))
r = c.post("/api/cron/camera", headers=H)
assert r.status_code == 200, r.text
assert r.json() == {"verwerkt": 0, "koppelingen_losgemaakt": 1}, r.json()
assert sorted(r["user_id"] for r in db["carboo_strava_koppelingen"]) == ["u2", "u3"]
r = c.post("/api/cron/camera", headers=H)
assert r.json()["koppelingen_losgemaakt"] == 0, "tweede beurt: niets meer te doen"

# ── de gewone Strava-ontkoppelknop meldt nu ook af bij Strava ────────────────
class U: id = "u2"
main.app.dependency_overrides[main.get_current_user] = lambda: U()
strava_af.clear()
r = c.delete("/api/strava/koppel")
assert r.status_code == 200 and strava_af == ["https://www.strava.com/oauth/deauthorize"], (r.text, strava_af)
assert sorted(r["user_id"] for r in db["carboo_strava_koppelingen"]) == ["u3"]
print("ALLES OK")
