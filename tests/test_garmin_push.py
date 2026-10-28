"""GARMIN-PUSH-V1 — lokale test zonder Garmin en zonder database: sportnamen,
lokale datum/uur, de trainingsrij en de dubbelcontrole.
Draaien: python lokaal-start.py tests/test_garmin_push.py"""
import base64, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_CLIENT_ID", "test-client")
os.environ.setdefault("GARMIN_CLIENT_SECRET", "test-secret")
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
os.environ.setdefault("GARMIN_PUSH_SECRET", "geheim-test")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

# sportnamen
assert main._garmin_sport_nl("CYCLING") == "Fietsen"
assert main._garmin_sport_nl("indoor_cycling") == "Indoor fietsen"
assert main._garmin_sport_nl("TRAIL_RUNNING") == "Trail"
assert main._garmin_sport_nl("LAP_SWIMMING") == "Zwemmen"
assert main._garmin_sport_nl("BMX") == "Fietsen" or main._garmin_sport_nl("BMX") is None
assert main._garmin_sport_nl("GOLF") is None and main._garmin_sport_nl(None) is None
print("sportnamen ok")

# lokale tijd: 2026-10-28 06:30 in Brussel (UTC+1) = 05:30 UTC
import datetime as dt
utc = int(dt.datetime(2026, 10, 28, 5, 30, tzinfo=dt.timezone.utc).timestamp())
act = {"activityId": 123, "activityType": "RUNNING", "startTimeInSeconds": utc,
       "startTimeOffsetInSeconds": 3600, "durationInSeconds": 3725, "distanceInMeters": 10400,
       "activeKilocalories": 640, "activityName": "Ochtendloop"}
assert main._garmin_lokaal(act) == ("2026-10-28", "06:30")
assert main._garmin_datum({"calendarDate": "2026-10-27"}) == "2026-10-27"
assert main._garmin_datum(act) == "2026-10-28"
print("lokale tijd ok")

# trainingsrij
rij = main._garmin_training_payload("u1", act)
assert rij["sport"] == "Lopen" and rij["duur_min"] == 62 and rij["kcal_verbranding"] == 640
assert rij["afstand_km"] == 10.4 and rij["garmin_activity_id"] == "123" and rij["bron"] == "garmin"
zonder = main._garmin_training_payload("u1", {**act, "activeKilocalories": None})
assert zonder["kcal_verbranding"] == 62 * 8, "zonder kcal valt hij terug op 8 kcal/min"
assert main._garmin_training_payload("u1", {**act, "activityType": "GOLF"}) is None
print("trainingsrij ok")

# dubbelcontrole tegenover Strava en manueel
bestaande = [
    {"id": "s1", "bron": "strava", "starttijd": "06:33", "duur_min": 60},
    {"id": "m1", "bron": "manueel", "starttijd": "18:00", "duur_min": 60},
]
assert main._garmin_zelfde_training(rij, bestaande)["id"] == "s1"
assert main._garmin_zelfde_training({**rij, "starttijd": "06:40"}, bestaande) is None, "7 min verschil = andere sessie"
assert main._garmin_zelfde_training({**rij, "duur_min": 100}, bestaande) is None, "duur te verschillend"
assert main._garmin_zelfde_training(rij, [{"id": "g1", "bron": "garmin", "starttijd": "06:30", "duur_min": 62}]) is None
print("dubbelcontrole ok")

# gezondheidsvelden: alleen de gekozen velden, score uit dict
w = main._garmin_gezondheid_waarden("sleeps", {"durationInSeconds": 27000, "overallSleepScore": {"value": 81, "qualifier": "GOOD"},
                                               "sleepLevelsMap": {"deep": [1, 2]}, "userId": "x"})
assert w == {"durationInSeconds": 27000, "overallSleepScore": 81}, w
w = main._garmin_gezondheid_waarden("dailies", {"restingHeartRateInBeatsPerMinute": 48, "averageStressLevel": 22,
                                                "bodyBatteryHighestValue": 90, "timeOffsetHeartRateSamples": {"0": 50}})
assert "timeOffsetHeartRateSamples" not in w and w["restingHeartRateInBeatsPerMinute"] == 48
print("gezondheid ok")
print("ALLES OK")
