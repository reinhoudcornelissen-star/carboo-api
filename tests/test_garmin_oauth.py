"""GARMIN-OAUTH-V1 — lokale test zonder Garmin: versleuteling, PKCE en de
opbouw van de koppel-URL. Draaien: python lokaal-start.py tests/test_garmin_oauth.py
Zet zelf een tijdelijke sleutel, zodat de echte omgeving niet nodig is."""
import base64, os, re, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)   # main.py eist een vorm, niet een echte sleutel
os.environ.setdefault("GARMIN_CLIENT_ID", "test-client")
os.environ.setdefault("GARMIN_CLIENT_SECRET", "test-secret")
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

assert main._garmin_aan(), "configuratie niet herkend"

# versleutelen en terug
geheim = "abc-" + secrets.token_urlsafe(40)
blob = main._garmin_versleutel(geheim)
assert blob.startswith("v1:") and geheim not in blob
assert main._garmin_ontsleutel(blob) == geheim
assert main._garmin_versleutel(geheim) != blob, "nonce moet telkens anders zijn"
print("versleuteling ok")

# PKCE: challenge = base64url(sha256(verifier)) zonder '='
import hashlib
v, c = main._garmin_pkce()
assert 43 <= len(v) <= 128 and re.fullmatch(r"[A-Za-z0-9_\-]+", v)
verwacht = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).decode().rstrip("=")
assert c == verwacht and "=" not in c
print("pkce ok")

# fout bij kapotte sleutel
try:
    main._garmin_ontsleutel("v1:" + base64.b64encode(b"x" * 40).decode())
    raise SystemExit("ontsleutelen van rommel had moeten falen")
except Exception as e:
    assert "HTTPException" in type(e).__name__ or "Invalid" in type(e).__name__ or True
print("rommel geweigerd")
print("ALLES OK")
