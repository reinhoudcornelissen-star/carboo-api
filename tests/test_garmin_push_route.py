"""GARMIN-PUSH-V1 — de route zelf: verkeerd geheim is 404, rommel is 400,
een geldig bericht voor een onbekende Garmin-gebruiker is 200 en schrijft
niets (alleen een leesopdracht naar de koppelingen).
Draaien: python lokaal-start.py tests/test_garmin_push_route.py"""
import base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_CLIENT_ID", "test-client")
os.environ.setdefault("GARMIN_CLIENT_SECRET", "test-secret")
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
os.environ["GARMIN_PUSH_SECRET"] = "geheim-" + secrets.token_urlsafe(16)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

c = TestClient(main.app)
goed = os.environ["GARMIN_PUSH_SECRET"]
assert c.post("/api/garmin/push/verkeerd", json={"dailies": []}).status_code == 404
assert c.post(f"/api/garmin/push/{goed}", content=b"geen json", headers={"content-type": "application/json"}).status_code == 400
assert c.post(f"/api/garmin/push/{goed}", json=[1, 2]).status_code == 400
r = c.post(f"/api/garmin/push/{goed}", json={"dailies": [{"userId": "bestaat-niet-" + secrets.token_hex(4), "calendarDate": "2026-10-28", "steps": 1}]})
assert r.status_code == 200 and r.json() == {"ok": True}, r.text
print("route ok (404 / 400 / 200)")
print("ALLES OK")
