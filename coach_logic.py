# coach_logic.py
# Dunne wrapper die de kernlogica uit carboo_coach.py beschikbaar stelt
# voor de FastAPI backend. Zo hergebruiken we alle bestaande Python code.

# KH_TARGETS direct overgenomen uit carboo_coach.py
KH_TARGETS = {
    "Fietsen":       {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":         {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":       {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":      {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon": {(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
    "Crossduatlon":  {(0,90):(0,0),(90,150):(30,60),(150,9999):(60,90)},
}


def get_kh_range(sport: str, minuten: int) -> tuple[int, int]:
    """Geeft (min_kh, max_kh) terug op basis van sport en wedstrijdduur."""
    ranges = KH_TARGETS.get(sport, KH_TARGETS["Fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= minuten < hi:
            return mn, mx
    return 60, 90


def genereer_html(data: dict, gebruiker_naam: str) -> str:
    """
    Genereer het volledige HTML rapport.
    Roept _genereer_html() aan uit carboo_coach.py.
    """
    try:
        # Importeer de originele functie uit carboo_coach
        from carboo_coach import _genereer_html
        return _genereer_html(data, gebruiker_naam)
    except ImportError:
        # Fallback als carboo_coach nog niet beschikbaar is
        return _genereer_html_fallback(data, gebruiker_naam)


def genereer_pdf(data: dict, gebruiker_naam: str) -> bytes:
    """
    Genereer het PDF rapport.
    Roept _genereer_pdf() aan uit carboo_coach.py.
    """
    try:
        from carboo_coach import _genereer_pdf
        return _genereer_pdf(data, gebruiker_naam)
    except ImportError:
        raise RuntimeError("carboo_coach.py niet gevonden — kopieer het naar de api map")


def bereken_raceplan(data: dict):
    """
    Bereken het uur-per-uur raceplan.
    Roept _bereken_raceplan() aan uit carboo_coach.py.
    """
    try:
        from carboo_coach import _bereken_raceplan
        return _bereken_raceplan(data)
    except ImportError:
        raise RuntimeError("carboo_coach.py niet gevonden")


def _genereer_html_fallback(data: dict, gebruiker_naam: str) -> str:
    """
    Minimale fallback HTML als carboo_coach.py niet beschikbaar is.
    Alleen voor development/testing.
    """
    atleet = data.get("atleet_naam", gebruiker_naam)
    sport = data.get("sport", "—")
    return f"""<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"><title>Carboo Plan — {atleet}</title></head>
<body style="font-family:sans-serif;padding:20px">
  <h1>Race Nutrition Plan</h1>
  <p><strong>Atleet:</strong> {atleet}</p>
  <p><strong>Sport:</strong> {sport}</p>
  <p style="color:red">⚠️ carboo_coach.py niet gevonden — kopieer het bestand naar de api map.</p>
</body>
</html>"""
