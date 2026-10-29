"""Kerncijfers uit een .fit-bestand van Garmin (FIT-CIJFERS-V1).

Overgenomen van test2perform (activiteit_cijfers.py), zonder numpy: een
activiteit telt hoogstens enkele tienduizenden seconden, dat rekent gewoon
Python vlot. Hier staat alleen wat uit het bestand zelf volgt; de drempel van
de sporter (FTP, drempelhartslag) komt er pas in het dashboard bij, zodat een
nieuwe drempel geen nieuwe berekening van het bestand vraagt.

Wat er bewaard wordt (carboo_garmin_activiteiten.kerncijfers):

  duur_s, afstand_m, sport
  vermogen   gem_vermogen, max_vermogen, np (genormaliseerd vermogen) en mmp:
             de beste gemiddelden over vaste duren (power-duration curve)
  hartslag   gem_hartslag, max_hartslag en som_hr2: de som van de hartslag in
             het kwadraat per seconde, waarmee hrTSS met elke drempelhartslag
             exact na te rekenen is
  hist_w, hist_hr
             seconden per vak van 10 W en 5 slagen, voor de tijd per zone

HERKOMST: genormaliseerd vermogen volgens Coggan (Allen & Coggan, "Training
and Racing with a Power Meter"): het voortschrijdend gemiddelde over 30 s,
tot de vierde macht, gemiddeld, de vierdemachtswortel.
"""

from __future__ import annotations

from typing import Any

#: Duren (s) voor de power-duration curve, van sprint tot uren.
MMP_DUREN = (1, 5, 10, 15, 30, 60, 120, 180, 300, 600, 1200, 1800, 2700, 3600, 5400, 7200)
NP_VENSTER_S = 30     # Coggan
MAX_GAT_S = 10        # gat tot zoveel seconden vullen we met de vorige waarde
BIN_W = 10
BIN_HR = 5
VERSIE = 1


class FitFout(Exception):
    pass


def _per_seconde(records: list[dict[str, Any]], veld: str) -> list[float | None]:
    """De waarden van één veld, per seconde (gaten tot MAX_GAT_S gevuld, None zonder meting)."""
    uit: list[float | None] = []
    for i, r in enumerate(records):
        waarde = r.get(veld)
        v = float(waarde) if isinstance(waarde, (int, float)) else None
        if i + 1 < len(records):
            dt = int((records[i + 1]["timestamp"] - r["timestamp"]).total_seconds())
            herhaal = dt if 1 <= dt <= MAX_GAT_S else 1
        else:
            herhaal = 1
        uit.extend([v] * herhaal)
    return uit


def _beste(reeks: list[float], duur: int) -> float | None:
    """Het hoogste gemiddelde over `duur` opeenvolgende seconden."""
    if len(reeks) < duur:
        return None
    som = 0.0
    cum = [0.0]
    for v in reeks:
        som += v
        cum.append(som)
    beste = max(cum[i + duur] - cum[i] for i in range(len(reeks) - duur + 1))
    return beste / duur


def _histogram(reeks: list[float], breedte: int) -> dict[str, int]:
    vakken: dict[int, int] = {}
    for v in reeks:
        k = int(v // breedte * breedte)
        vakken[k] = vakken.get(k, 0) + 1
    return {str(k): n for k, n in sorted(vakken.items())}


def kerncijfers(inhoud: bytes) -> dict[str, Any]:
    """De kerncijfers van een activiteit; FitFout als het bestand niet te lezen is."""
    from garmin_fit_sdk import Decoder, Stream
    try:
        berichten, fouten = Decoder(Stream.from_byte_array(bytearray(inhoud))).read()
    except Exception as exc:
        raise FitFout(f"geen leesbaar .fit-bestand: {exc}") from exc
    records = [r for r in berichten.get("record_mesgs", []) if r.get("timestamp")]
    if not records:
        raise FitFout("geen metingen in het bestand" + (f" ({fouten[0]})" if fouten else ""))
    records.sort(key=lambda r: r["timestamp"])
    sessie = (berichten.get("session_mesgs") or [{}])[0]

    uit: dict[str, Any] = {"versie": VERSIE, "sport": str(sessie.get("sport")) if sessie.get("sport") is not None else None}
    vermogen = _per_seconde(records, "power")
    hartslag = _per_seconde(records, "heart_rate")
    snelheid = _per_seconde(records, "enhanced_speed")
    if all(v is None for v in snelheid):
        snelheid = _per_seconde(records, "speed")

    uit["duur_s"] = int(round(sessie.get("total_timer_time") or len(vermogen)))
    afstand = sessie.get("total_distance") or records[-1].get("distance")
    uit["afstand_m"] = round(float(afstand), 1) if afstand else None

    met_w = [v for v in vermogen if v is not None]
    if len(met_w) >= NP_VENSTER_S:
        w = [v if v is not None else 0.0 for v in vermogen]
        # voortschrijdend gemiddelde over 30 s
        som = sum(w[:NP_VENSTER_S])
        rollend = [som / NP_VENSTER_S]
        for i in range(NP_VENSTER_S, len(w)):
            som += w[i] - w[i - NP_VENSTER_S]
            rollend.append(som / NP_VENSTER_S)
        np_ = (sum(r ** 4 for r in rollend) / len(rollend)) ** 0.25
        uit.update({
            "s_vermogen": len(met_w),
            "gem_vermogen": round(sum(met_w) / len(met_w), 1),
            "max_vermogen": int(max(met_w)),
            "np": round(np_, 1),
            "mmp": {str(d): round(b, 1) for d in MMP_DUREN if (b := _beste(w, d)) is not None},
            "hist_w": _histogram(met_w, BIN_W),
        })

    hr = [v for v in hartslag if v is not None and v > 0]
    if hr:
        uit.update({
            "s_hartslag": len(hr),
            "gem_hartslag": round(sum(hr) / len(hr), 1),
            "max_hartslag": int(max(hr)),
            "som_hr2": int(sum(v * v for v in hr)),
            "hist_hr": _histogram(hr, BIN_HR),
        })

    met_v = [v for v in snelheid if v is not None]
    if met_v:
        uit["gem_snelheid_kmh"] = round(sum(met_v) / len(met_v) * 3.6, 2)
    return uit


def tss_van(k: dict[str, Any], ftp: float | None, drempel_hs: float | None) -> tuple[int | None, str]:
    """TSS uit de kerncijfers, zoals test2perform: eerst vermogen (Coggan),
    anders hartslag (hrTSS), anders None. Geeft (tss, bron)."""
    duur = float(k.get("duur_s") or 0)
    if ftp and k.get("np") and (k.get("s_vermogen") or 0) >= 0.5 * max(1.0, duur):
        np_ = float(k["np"])
        return int(round(duur * np_ * (np_ / ftp) / (ftp * 3600) * 100)), "vermogen"
    if drempel_hs and k.get("som_hr2"):
        return int(round(float(k["som_hr2"]) / (float(drempel_hs) ** 2) / 3600 * 100)), "hartslag"
    return None, "geen"
