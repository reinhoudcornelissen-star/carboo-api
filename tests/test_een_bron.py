"""EEN-BRON-V1 — Garmin en Strava leveren dezelfde rit; er blijft één rij
met de Garmin-waarden. Zonder database en zonder Strava: een nagemaakte
Supabase-client en een nagemaakt Strava-antwoord.
Draaien: python lokaal-start.py tests/test_een_bron.py"""
import asyncio, base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


# ── de vergelijking zelf ─────────────────────────────────────────────
garmin_rij = {"id": "g1", "bron": "garmin", "starttijd": "10:12", "duur_min": 75}
strava_rij = {"starttijd": "10:12", "duur_min": 69}           # Strava: bewegende tijd
assert main._strava_zelfde_garmin(strava_rij, [garmin_rij])["id"] == "g1"
assert main._strava_zelfde_garmin(strava_rij, [{**garmin_rij, "bron": "manueel"}]) is None, "alleen Garmin-rijen tellen"
assert main._strava_zelfde_garmin({**strava_rij, "starttijd": "10:20"}, [garmin_rij]) is None
assert main._garmin_zelfde_training({"starttijd": "10:12", "duur_min": 75}, [{"id": "s1", "bron": "strava", "starttijd": "10:12", "duur_min": 69}])["id"] == "s1"
print("vergelijking ok")

# ── dagtelling: Garmin telt als werkelijk ────────────────────────────
per_dag = main._trainingskcal_per_dag([
    {"datum": "2026-10-29", "sport": "Fietsen", "bron": "manueel", "kcal_verbranding": 500},
    {"datum": "2026-10-29", "sport": "Fietsen", "bron": "garmin", "kcal_verbranding": 428},
])
assert per_dag["2026-10-29"] == 428, per_dag
print("dagtelling ok")


# ── nagemaakte Supabase: tabellen in het geheugen ────────────────────
class Q:
    def __init__(self, db, tabel): self.db, self.tabel, self.f, self.op = db, tabel, [], None
    def select(self, *a): self.op = ("select",); return self
    def update(self, d): self.op = ("update", d); return self
    def insert(self, d): self.op = ("insert", d); return self
    def delete(self): self.op = ("delete",); return self
    def upsert(self, d, **k): self.op = ("insert", d); return self
    def eq(self, k, v): self.f.append(lambda r: str(r.get(k)) == str(v)); return self
    def is_(self, k, v): self.f.append(lambda r: r.get(k) is None); return self
    @property
    def not_(self):
        q = self
        class N:
            def is_(self2, k, v): q.f.append(lambda r: r.get(k) is not None); return q
        return N()
    def execute(self):
        rows = [r for r in self.db.setdefault(self.tabel, []) if all(fn(r) for fn in self.f)]
        if self.op[0] == "update":
            for r in rows: r.update(self.op[1])
        elif self.op[0] == "insert":
            r = {"id": f"n{len(self.db[self.tabel]) + 1}", **self.op[1]}; self.db[self.tabel].append(r); rows = [r]
        elif self.op[0] == "delete":
            self.db[self.tabel] = [r for r in self.db[self.tabel] if r not in rows]
        class R: data = rows
        return R()


class FakeSB:
    def __init__(self, db): self.db = db
    def table(self, naam): return Q(self.db, naam)


class FakeHTTP:
    """Het Strava-antwoord voor GET /activities/{id}."""
    antwoord = {}
    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def get(self, url, **k):
        class R: status_code = 200
        R.json = lambda self2: FakeHTTP.antwoord
        return R()


async def niets(k, sb): return "token"
main._refresh_token_indien_nodig = niets
main.httpx.AsyncClient = FakeHTTP

# ── 1. Garmin eerst, dan het Strava-bericht: geen tweede rij ─────────
db = {"carboo_strava_koppelingen": [{"user_id": "u1", "strava_athlete_id": "77"}],
      "fuelc_trainingen": [{"id": "g1", "user_id": "u1", "datum": "2026-10-29", "starttijd": "10:12", "duur_min": 75,
                            "kcal_verbranding": 428, "sport": "E-bike", "bron": "garmin", "garmin_activity_id": "555"}]}
main.supabase_admin = FakeSB(db)
FakeHTTP.antwoord = {"id": 9001, "sport_type": "EBikeRide", "start_date_local": "2026-10-29T10:12:00",
                     "moving_time": 69 * 60, "calories": 428, "name": "Ochtendrit"}
asyncio.run(main._strava_webhook_verwerk({"object_type": "activity", "aspect_type": "create", "object_id": 9001, "owner_id": 77}))
tr = db["fuelc_trainingen"]
assert len(tr) == 1 and tr[0]["bron"] == "garmin" and tr[0]["kcal_verbranding"] == 428 and tr[0]["duur_min"] == 75, tr
assert str(tr[0]["strava_activity_id"]) == "9001", "Strava-id hangt aan de Garmin-rij"
print("garmin eerst ok")

# ── 2. Strava-update daarna: Garmin-waarden blijven staan ────────────
FakeHTTP.antwoord = {**FakeHTTP.antwoord, "name": "Andere naam", "calories": 999}
asyncio.run(main._strava_webhook_verwerk({"object_type": "activity", "aspect_type": "update", "object_id": 9001, "owner_id": 77}))
assert len(tr) == 1 and tr[0]["kcal_verbranding"] == 428 and tr[0]["bron"] == "garmin", tr
print("strava-update genegeerd ok")

# ── 3. Strava-delete: Garmin-rij blijft, alleen de koppeling eraf ───
asyncio.run(main._strava_webhook_verwerk({"object_type": "activity", "aspect_type": "delete", "object_id": 9001, "owner_id": 77}))
tr = db["fuelc_trainingen"]
assert len(tr) == 1 and tr[0]["bron"] == "garmin" and tr[0].get("strava_activity_id") is None, tr
print("strava-delete ok")

# ── 4. Andere sessie van Strava (later op de dag): wél toevoegen ────
FakeHTTP.antwoord = {"id": 9002, "sport_type": "Ride", "start_date_local": "2026-10-29T14:14:00",
                     "moving_time": 32 * 60, "calories": 176, "name": "Middagrit"}
asyncio.run(main._strava_webhook_verwerk({"object_type": "activity", "aspect_type": "create", "object_id": 9002, "owner_id": 77}))
tr = db["fuelc_trainingen"]
assert len(tr) == 2 and tr[1]["bron"] == "strava" and tr[1]["kcal_verbranding"] == 176, tr
print("andere sessie ok")

# ── 5. Strava eerst, dan Garmin: Garmin-waarden nemen de rij over ───
db["fuelc_trainingen"] = [{"id": "s1", "user_id": "u1", "datum": "2026-10-29", "starttijd": "10:12", "duur_min": 69,
                           "kcal_verbranding": 400, "sport": "E-bike", "bron": "strava", "strava_activity_id": "9001"}]
db["carboo_garmin_activiteiten"] = []
import datetime as dt
utc = int(dt.datetime(2026, 10, 29, 9, 12, tzinfo=dt.timezone.utc).timestamp())
act = {"activityId": 555, "activityType": "CYCLING", "startTimeInSeconds": utc, "startTimeOffsetInSeconds": 3600,
       "durationInSeconds": 75 * 60, "activeKilocalories": 428, "activityName": "Ochtendrit"}
asyncio.run(main._garmin_activiteit_verwerk(act, {"user_id": "u1"}))
tr = db["fuelc_trainingen"]
assert len(tr) == 1 and tr[0]["bron"] == "garmin" and tr[0]["kcal_verbranding"] == 428 and tr[0]["duur_min"] == 75, tr
assert tr[0]["garmin_activity_id"] == "555" and tr[0]["strava_activity_id"] == "9001", tr
print("strava eerst ok")
print("ALLES OK")
