# gut_logic.py
# Wrapper die de Train the Gut schema logica exporteert voor de FastAPI backend.
# Hergebruikt de watervalstrategie uit module_testing.py

KH_TARGETS = {
    "Fietsen":       {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":         {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":       {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":      {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon": {(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}

SPORT_FASES = {
    "Fietsen":      [{"naam":"Fietsen","icon":"🚴"}],
    "Lopen":        [{"naam":"Lopen","icon":"🏃"}],
    "Triatlon":     [{"naam":"Fietsgedeelte","icon":"🚴"},{"naam":"Loopgedeelte","icon":"🏃"},{"naam":"Combinatie","icon":"🏊🚴🏃"}],
    "Duatlon":      [{"naam":"Fietsgedeelte","icon":"🚴"},{"naam":"Eerste loop","icon":"🏃"},{"naam":"Tweede loop","icon":"🏃"},{"naam":"Combinatie","icon":"🏃🚴"}],
    "Crosstriatlon":[{"naam":"Fietsgedeelte","icon":"🚵"},{"naam":"Loopgedeelte","icon":"🏃"},{"naam":"Combinatie","icon":"🚵🏃"}],
}

KLACHT_ALTERNATIEF = {
    "Lichte maagkramp": "Meer water bij inname (min. 200ml), of isotone gel proberen",
    "Krampen":          "Meer water bij inname (min. 200ml), of isotone gel proberen",
    "Misselijkheid":    "Minder zoete variant of lagere concentratie sportdrank",
    "Opgeblazen gevoel":"Check fructose/polyolen in ingredienten, kies ander type",
    "Reflux / brandend maagzuur": "Caffeinevrije variant, neutrale smaak",
    "Diarree":          "Hypotone variant of lagere osmolariteit",
    "Braken":           "Stop testtraining, drastisch verlagen naar 0.5 portie",
}

PRIORITEIT_LOPEN = {"Gel": 0, "Cafeinegel": 1, "Sportdrank": 2, "Supplement": 3, "Vast voedsel": 4}


def _is_fase_stabiel(logs: dict, fase_naam: str, target_kh: int = 0) -> bool:
    fase_logs = {k:v for k,v in logs.items() if v.get("fase")==fase_naam and v.get("ingevuld")}
    if len(fase_logs) < 2:
        return False
    laatste2 = [v for _,v in sorted(fase_logs.items(), key=lambda x:int(x[0]))[-2:]]
    scores_ok = all(l.get("score",0)>=4 and l.get("symptoom","") in ["","Geen klachten"] for l in laatste2)
    if not scores_ok:
        return False
    z4_ok = all("Z4" in l.get("intensiteit","") or "Z5" in l.get("intensiteit","") for l in laatste2)
    if target_kh > 0:
        target_ok = any(l.get("kh_doel",0) >= target_kh for l in laatste2)
        return z4_ok and target_ok
    return z4_ok


def _actieve_fase(sport: str, logs: dict) -> str:
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])
    for fase in fases:
        if not _is_fase_stabiel(logs, fase["naam"]):
            return fase["naam"]
    return fases[-1]["naam"]


def _volgende_week_nr(logs: dict) -> int:
    ingevulde = [int(k) for k,v in logs.items() if v.get("ingevuld")]
    return max(ingevulde)+1 if ingevulde else 1


def _sorteer_producten(producten: list) -> list:
    def sort_key(p):
        prio   = PRIORITEIT_LOPEN.get(p.get("type","Supplement"), 5)
        kh     = p.get("kh", 99)
        klacht = 1 if p.get("status") == "klachten" else 0
        return (klacht, prio, kh)
    return sorted(producten, key=sort_key)


def _bepaal_intensiteit(week_nr: int, fase_logs: dict) -> str:
    if week_nr <= 2:
        return "Z2 — Duurtraining"
    gesorteerd = sorted([(int(k),v) for k,v in fase_logs.items()], key=lambda x:x[0])
    if week_nr <= 4:
        if len(gesorteerd) >= 2:
            laatste2 = [v for _,v in gesorteerd[-2:]]
            if all(l.get("score",0) >= 4 for l in laatste2):
                return "Z3 — Tempo"
        return "Z2 — Duurtraining"
    if len(gesorteerd) >= 2:
        laatste2 = [v for _,v in gesorteerd[-2:]]
        if all(l.get("score",0)>=4 and l.get("symptoom","") in ["","Geen klachten"] for l in laatste2):
            return "Z4 — Drempeltraining"
    return "Z3 — Tempo"


def genereer_schema(data: dict, logs: dict, actieve_fase: str) -> dict:
    """
    Genereer het Train the Gut schema voor de volgende week.
    Watervalstrategie: progressief opbouwen op basis van vorige scores.
    """
    try:
        from module_testing import _genereer_schema as _orig
        return _orig(data, logs, actieve_fase)
    except ImportError:
        pass

    # Fallback: eigen implementatie
    producten  = [p for p in data.get("producten",[]) if p.get("naam")]
    ervaring   = data.get("ervaring","Nog nooit")
    target_kh  = int(data.get("target_kh", 60))
    eetmom     = int(data.get("eetmomenten", 2))

    fase_logs  = {k:v for k,v in logs.items() if v.get("fase")==actieve_fase and v.get("ingevuld")}
    week_nr    = _volgende_week_nr(logs)
    gesorteerd = _sorteer_producten(producten)

    if not gesorteerd:
        return {"week": week_nr, "fase": actieve_fase, "product": "—", "kh_pp": 0, "porties": 0, "kh_totaal": 0, "interval_min": 30, "intensiteit": "Z2 — Duurtraining", "progressie": "start", "tip": "Voeg eerst producten toe.", "alternatief": "", "duur_min": "90-120"}

    huidig_prod = gesorteerd[0]
    kh_pp = huidig_prod.get("kh", 22)

    if not fase_logs:
        if ervaring == "Nog nooit":
            porties = 1
        elif ervaring == "2-4 wedstrijden":
            porties = max(1, round(target_kh * 0.55 / max(kh_pp,1)))
        else:
            porties = max(1, round(target_kh * 0.75 / max(kh_pp,1)))
        progressie = "start"
    else:
        prev_log   = sorted([(int(k),v) for k,v in fase_logs.items()])[-1][1]
        prev_port  = prev_log.get("porties", 1)
        prev_score = prev_log.get("score", 3)
        heeft_klachten = prev_log.get("symptoom","Geen klachten") not in ["","Geen klachten"]
        max_porties = max(1, round(target_kh / max(kh_pp,1)))

        if prev_score >= 4 and not heeft_klachten:
            porties = min(prev_port + 1, max_porties)
            progressie = "omhoog"
        elif prev_score == 3 and not heeft_klachten:
            porties = prev_port
            progressie = "herhalen"
        else:
            porties = max(1, prev_port - 1)
            progressie = "omlaag"

    kh_totaal = porties * kh_pp
    interval  = max(10, round(60 / max(eetmom, porties) / 5) * 5)
    zone      = _bepaal_intensiteit(week_nr, fase_logs)

    alternatief = ""
    if fase_logs:
        prev_log = sorted([(int(k),v) for k,v in fase_logs.items()])[-1][1]
        klacht = prev_log.get("symptoom","")
        if klacht and klacht != "Geen klachten":
            alternatief = KLACHT_ALTERNATIEF.get(klacht, "Overweeg een ander producttype")

    if porties == 1:
        tip = "Neem de gel altijd met 150-200ml water — nooit met sportdrank."
    else:
        tip = f"Spreid {porties} porties gelijkmatig — elke {interval} minuten, altijd met 150-200ml water."

    return {
        "week": week_nr,
        "fase": actieve_fase,
        "product": huidig_prod["naam"],
        "kh_pp": kh_pp,
        "porties": porties,
        "kh_totaal": kh_totaal,
        "interval_min": interval,
        "intensiteit": zone,
        "progressie": progressie,
        "tip": tip,
        "alternatief": alternatief,
        "duur_min": "90-120",
    }
