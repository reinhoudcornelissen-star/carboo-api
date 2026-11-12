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

# SCHEDULE-ANTWOORD-V1 — Garmin geeft bij het inplannen een kaal nummer terug
assert main._garmin_id_uit(123456, "scheduleId") == 123456
assert main._garmin_id_uit("123456", "scheduleId") == 123456
assert main._garmin_id_uit({"workoutId": 77, "sport": "RUNNING"}, "workoutId") == 77
assert main._garmin_id_uit({}, "workoutId") is None and main._garmin_id_uit(None, "x") is None
print("id-antwoord ok")

# GARMIN-SCHEMA-V1 — het schema-tempo van het trainingsplan gaat voor op de eigen zones
def stap1(sport, seg, zones=None):
    return main._garmin_workout_json({"naam": "x", "sport": sport, "datum": "2026-11-11", "zone_verdeling": json.dumps([seg])}, zones or {})["segments"][0]["steps"][0]

s = stap1("Lopen", {"naam": "Duurblok", "duur_min": 30, "zone": "Z3", "doel": "5:10–4:50 /km · 150–160 bpm", "doel_zone": "Z3", "doel_sport": "Lopen"}, zones_loop)
assert s["targetType"] == "PACE" and abs(s["targetValueLow"] - 1000 / 310) < 0.001 and abs(s["targetValueHigh"] - 1000 / 290) < 0.001, s
# ook zonder eigen zones, en binnen een herhaling
w = main._garmin_workout_json({"naam": "x", "sport": "Lopen", "datum": "2026-11-11", "zone_verdeling": json.dumps([
    {"herhaling": {"reps": 4, "blokken": [{"naam": "Work", "duur_min": 4, "zone": "Z4", "afstand_tekst": "1 km", "doel": "4:20–4:05 /km", "doel_zone": "Z4", "doel_sport": "Lopen"},
                                          {"naam": "Recovery", "duur_min": 2, "zone": "Z1", "doel": "tot 6:00 /km", "doel_zone": "Z1", "doel_sport": "Lopen"}]}, "naam": "4x", "duur_min": 24, "zone": "Z4"}])}, {})
a, b = w["segments"][0]["steps"][0]["steps"]
assert a["targetType"] == "PACE" and a["durationType"] == "DISTANCE" and abs(a["targetValueHigh"] - 1000 / 245) < 0.001, a
assert b["targetType"] == "PACE" and abs(b["targetValueHigh"] - 1000 / 360) < 0.001 and b["targetValueLow"] < b["targetValueHigh"], b
# de zone van de stap is nadien gewijzigd: het schema-doel geldt niet meer, de eigen zones wel
s = stap1("Lopen", {"naam": "Duurblok", "duur_min": 30, "zone": "Z3", "doel": "6:00–5:30 /km", "doel_zone": "Z2", "doel_sport": "Lopen"}, zones_loop)
assert s["targetType"] == "PACE" and abs(s["targetValueLow"] - 1000 / 300) < 0.001, s
# een gevoel in plaats van getallen: terugval op de eigen zones (hier geen: OPEN)
s = stap1("Lopen", {"naam": "Duurblok", "duur_min": 30, "zone": "Z2", "doel": "rustig, je kunt nog vlot praten", "doel_zone": "Z2", "doel_sport": "Lopen"})
assert s["targetType"] == "OPEN", s
# fietsen: watt uit het schema; alleen hartslag in het schema: hartslag
s = stap1("Fietsen", {"naam": "Duurblok", "duur_min": 60, "zone": "Z2", "doel": "180–220 W · 130–145 bpm", "doel_zone": "Z2", "doel_sport": "Fietsen"}, zones_fiets)
assert s["targetType"] == "POWER" and (s["targetValueLow"], s["targetValueHigh"]) == (180, 220), s
s = stap1("Fietsen", {"naam": "Duurblok", "duur_min": 60, "zone": "Z2", "doel": "130–145 bpm", "doel_zone": "Z2", "doel_sport": "Fietsen"})
assert s["targetType"] == "HEART_RATE" and (s["targetValueLow"], s["targetValueHigh"]) == (130, 145), s
# GARMIN-SCHEMA-V2 — na een zonewissel volgt het horloge het schema-tempo van de nieuwe zone
D = {"Z2": "6:00–5:30 /km", "Z3": "5:10–4:50 /km"}
s = stap1("Lopen", {"naam": "Duurblok", "duur_min": 30, "zone": "Z3", "doel": "6:00–5:30 /km", "doel_zone": "Z2", "doel_sport": "Lopen", "doelen": D}, zones_loop)
assert s["targetType"] == "PACE" and abs(s["targetValueLow"] - 1000 / 310) < 0.001 and abs(s["targetValueHigh"] - 1000 / 290) < 0.001, s
# een stap die er in de kalender bij kwam (zonder doel) neemt de schema-tempo's van een andere stap
w = main._garmin_workout_json({"naam": "x", "sport": "Lopen", "datum": "2026-11-12", "zone_verdeling": json.dumps([
    {"naam": "Duurblok", "duur_min": 30, "zone": "Z2", "doel": "6:00–5:30 /km", "doel_zone": "Z2", "doel_sport": "Lopen", "doelen": D},
    {"naam": "Tempowerk", "duur_min": 10, "zone": "Z3"}])}, zones_loop)
n = w["segments"][0]["steps"][1]
assert n["targetType"] == "PACE" and abs(n["targetValueHigh"] - 1000 / 290) < 0.001, n
# de sport is gewijzigd: de schema-tempo's gelden niet meer
s = stap1("Fietsen", {"naam": "Duurblok", "duur_min": 30, "zone": "Z3", "doel": "6:00–5:30 /km", "doel_zone": "Z2", "doel_sport": "Lopen", "doelen": D})
assert s["targetType"] == "OPEN", s
print("SCHEMA OK")
