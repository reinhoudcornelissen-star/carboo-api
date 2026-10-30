"""TOKEN-VERNIEUW-V1 — na 24 uur vernieuwt Carboo de Garmin-token; de nieuwe
tokens moeten in de bestaande koppeling komen zonder dat de databank over de
verplichte kolommen (toestemming_op) valt.
Draaien: python lokaal-start.py tests/test_garmin_token_vernieuw.py"""
import asyncio, base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

VERPLICHT = ("user_id", "toestemming_op", "access_token", "refresh_token")


class Q:
    def __init__(self, db): self.db, self.f, self.op = db, [], None
    def select(self, *a): self.op = ("select",); return self
    def update(self, d): self.op = ("update", d); return self
    def upsert(self, d, **k): self.op = ("upsert", d); return self
    def eq(self, k, v): self.f.append(lambda r: str(r.get(k)) == str(v)); return self
    def execute(self):
        rows = [r for r in self.db if all(fn(r) for fn in self.f)]
        if self.op[0] == "update":
            for r in rows: r.update(self.op[1])
        elif self.op[0] == "upsert":
            # zoals Postgres: eerst de verplichte kolommen van de nieuwe rij nakijken
            for kol in VERPLICHT:
                if self.op[1].get(kol) is None:
                    raise Exception(f'null value in column "{kol}" violates not-null constraint')
            bestaand = [r for r in self.db if r["user_id"] == self.op[1]["user_id"]]
            if bestaand: bestaand[0].update(self.op[1])
            else: self.db.append(dict(self.op[1]))
        class R: data = rows
        return R()


class FakeSB:
    def __init__(self, db): self.db = db
    def table(self, naam): assert naam == "carboo_garmin_koppelingen"; return Q(self.db)


db = [{"user_id": "u1", "garmin_user_id": "g9", "rechten": ["WORKOUT_IMPORT"], "toestemming_op": "2026-10-29T06:00:00+00:00",
       "access_token": main._garmin_versleutel("oud-access"), "refresh_token": main._garmin_versleutel("oud-refresh"),
       "access_verloopt_op": "2026-10-30T05:00:00+00:00"}]  # verlopen
main.supabase_admin = FakeSB(db)

async def nep_token_post(data):
    assert data["grant_type"] == "refresh_token" and data["refresh_token"] == "oud-refresh"
    return {"access_token": "nieuw-access", "refresh_token": "nieuw-refresh", "expires_in": 86400, "refresh_token_expires_in": 7776000}
main._garmin_token_post = nep_token_post

k, token = asyncio.run(main._garmin_toegang("u1"))
assert token == "nieuw-access", token
assert len(db) == 1, db
rij = db[0]
assert main._garmin_ontsleutel(rij["access_token"]) == "nieuw-access"
assert main._garmin_ontsleutel(rij["refresh_token"]) == "nieuw-refresh"
assert rij["toestemming_op"] == "2026-10-29T06:00:00+00:00" and rij["garmin_user_id"] == "g9" and rij["rechten"] == ["WORKOUT_IMPORT"], "koppelgegevens blijven staan"
assert rij["access_verloopt_op"] > "2026-10-30T05:00:00", rij["access_verloopt_op"]
print("vernieuwing ok")

# geldige token: niets vernieuwen
db[0]["access_verloopt_op"] = "2099-01-01T00:00:00+00:00"
async def mag_niet(data): raise AssertionError("token werd onnodig vernieuwd")
main._garmin_token_post = mag_niet
k, token = asyncio.run(main._garmin_toegang("u1"))
assert token == "nieuw-access"
print("geldige token ok")
print("ALLES OK")
