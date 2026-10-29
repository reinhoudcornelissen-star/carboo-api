"""GARMIN-WORKOUT-V1 — de workout-JSON voor de Training API, zonder Garmin
en zonder database. Draaien: python lokaal-start.py tests/test_garmin_workout.py"""
import base64, json, os, secrets, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
os.environ.setdefault("MOLLIE_API_KEY", "test_" + "x" * 30)
os.environ.setdefault("GARMIN_TOKEN_KEY", base64.b64encode(secrets.token_bytes(32)).decode())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

segs = [
    {"naam": "Opwarming", "duur_min": 15, "zone": "Z1"},
    {"herhaling": {"reps": 5, "blokken": [{"naam": "Work", "duur_min": 4, "zone": "Z4"}, {"naam": "Recovery", "duur_min": 3, "zone": "Z1"}]}, "naam": "5x Work/Recovery", "duur_min": 35, "zone": "Z4"},
    {"naam": "Cooldown", "duur_min": 10, "zone": "Z1", "notitie": "rustig uitbollen"},
]
fiets = {"naam": "5 x 4 drempel", "sport": "Fietsen", "datum": "2026-11-02", "zone_verdeling": json.dumps(segs), "notitie": ""}
zones_fiets = {"z1_tempo_van": "100", "z1_tempo_tot": "150", "z4_tempo_van": "250", "z4_tempo_tot": "270", "z4_hs_van": "160", "z4_hs_tot": "170"}

w = main._garmin_workout_json(fiets, zones_fiets)
assert w["sport"] == "CYCLING" and w["workoutProvider"] == "Carboo" and w["workoutName"] == "5 x 4 drempel"
st = w["segments"][0]["steps"]
assert [s["type"] for s in st] == ["WorkoutStep", "WorkoutRepeatStep", "WorkoutStep"]
assert st[0]["intensity"] == "WARMUP" and st[0]["durationType"] == "TIME" and st[0]["durationValue"] == 900
assert st[0]["targetType"] == "POWER" and st[0]["targetValueLow"] == 100 and st[0]["targetValueHigh"] == 150
assert st[1]["repeatType"] == "REPEAT_UNTIL_STEPS_CMPLT" and st[1]["repeatValue"] == 5
w1, r1 = st[1]["steps"]
assert w1["intensity"] == "INTERVAL" and w1["durationValue"] == 240 and w1["targetType"] == "POWER" and w1["targetValueLow"] == 250
assert r1["intensity"] == "RECOVERY" and r1["durationValue"] == 180
assert st[2]["intensity"] == "COOLDOWN" and "rustig uitbollen" in st[2]["description"]
# volgorde van stepOrder loopt door, ook in de herhaling
assert [st[0]["stepOrder"], st[1]["stepOrder"], w1["stepOrder"], r1["stepOrder"], st[2]["stepOrder"]] == [1, 2, 3, 4, 5]
print("fietsen ok")

# lopen: tempo als m/s (traag = low, snel = high), afstand in meter
loop = {"naam": "Tempoloop", "sport": "Lopen", "datum": "2026-11-03",
        "zone_verdeling": json.dumps([{"naam": "Duurblok", "duur_min": 25, "zone": "Z3", "afstand_tekst": "5 km", "tempo_tekst": "5:00 /km"}])}
zones_loop = {"z3_tempo_van": "5.00", "z3_tempo_tot": "4.30"}
w = main._garmin_workout_json(loop, zones_loop)
s = w["segments"][0]["steps"][0]
assert w["sport"] == "RUNNING" and s["durationType"] == "DISTANCE" and s["durationValue"] == 5000 and s["durationValueType"] == "METER"
assert s["targetType"] == "PACE" and abs(s["targetValueLow"] - 1000 / 300) < 0.001 and abs(s["targetValueHigh"] - 1000 / 270) < 0.001
print("lopen ok")

# zonder zones: OPEN; hartslag als enige: HEART_RATE
w = main._garmin_workout_json(loop, {})
assert w["segments"][0]["steps"][0]["targetType"] == "OPEN"
w = main._garmin_workout_json(loop, {"z3_hs_van": "150", "z3_hs_tot": "160"})
assert w["segments"][0]["steps"][0]["targetType"] == "HEART_RATE" and w["segments"][0]["steps"][0]["targetValueHigh"] == 160
print("doelen ok")

# fouten: sport en lege opbouw
for slecht in ({"sport": "Zwemmen", "zone_verdeling": json.dumps(segs)}, {"sport": "Fietsen", "zone_verdeling": None}):
    try:
        main._garmin_workout_json(slecht, {}); raise SystemExit("had moeten falen")
    except ValueError as e:
        print("geweigerd:", str(e)[:60])
print("ALLES OK")
