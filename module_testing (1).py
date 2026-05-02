"""
Train the Gut — Carboo module voor systematische maagtraining
Claude API-gebaseerd schema | Fase-systeem multisport | Productwaarschuwingen
"""
import streamlit as st
import anthropic
import json
from datetime import date, timedelta

SPORTEN       = ["Fietsen", "Lopen", "Triatlon", "Duatlon", "Crosstriatlon"]
MULTISPORT    = ["Triatlon", "Duatlon", "Crosstriatlon"]
PRODUCT_TYPES = ["Gel", "Sportdrank", "Vast voedsel", "Cafeïnegel", "Supplement"]
SYMPTOMEN     = [
    "Geen klachten", "Lichte maagkramp", "Misselijkheid",
    "Opgeblazen gevoel", "Reflux / brandend maagzuur",
    "Diarree", "Braken", "Hoofdpijn", "Steken in de zij",
]
INTENSITEITEN = [
    "Z1 — Actief herstel", "Z2 — Duurtraining", "Z3 — Tempo",
    "Z4 — Drempeltraining", "Z5 — Wedstrijdintensiteit",
]

# ── KH targets ────────────────────────────────────────────────────────────────
KH_TARGETS = {
    "Fietsen":      {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":        {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":      {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":     {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon":{(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}

def _get_richtlijn(sport, duur_min):
    ranges = KH_TARGETS.get(sport, KH_TARGETS["Fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= duur_min < hi:
            return mn, mx
    return 0, 0

# ── Fases per sport ───────────────────────────────────────────────────────────
SPORT_FASES = {
    "Fietsen":      [{"naam":"Fietsen",      "icon":"🚴"}],
    "Lopen":        [{"naam":"Lopen",        "icon":"🏃"}],
    "Triatlon":     [{"naam":"Fietsgedeelte","icon":"🚴"},
                     {"naam":"Loopgedeelte", "icon":"🏃"},
                     {"naam":"Combinatie",   "icon":"🏊🚴🏃"}],
    "Duatlon":      [{"naam":"Fietsgedeelte","icon":"🚴"},
                     {"naam":"Eerste loop",  "icon":"🏃"},
                     {"naam":"Tweede loop",  "icon":"🏃"},
                     {"naam":"Combinatie",   "icon":"🏃🚴"}],
    "Crosstriatlon":[{"naam":"Fietsgedeelte","icon":"🚵"},
                     {"naam":"Loopgedeelte", "icon":"🏃"},
                     {"naam":"Combinatie",   "icon":"🚵🏃"}],
}

# ── Productwaarschuwingen ──────────────────────────────────────────────────────
SPORT_PRODUCT_WAARSCHUWINGEN = {
    "Lopen":        {"Vast voedsel": ("⚠️","#ef4444","Vast voedsel sterk afgeraden bij lopen.")},
    "Crosstriatlon":{"Vast voedsel": ("⚠️","#ef4444","Offroad verhoogt schokbelasting — vast voedsel risicovol.")},
    "Triatlon":     {"Vast voedsel": ("💡","#fbbf24","Vast voedsel enkel op de fiets, nooit op de loop.")},
    "Duatlon":      {"Vast voedsel": ("💡","#fbbf24","Vast voedsel enkel op de fiets.")},
}

# ── Sport-specifieke producttips ──────────────────────────────────────────────
SPORT_PRODUCT_TIPS = {
    "Fietsen":{"icon":"🚴","intro":"Op de fiets de meeste vrijheid — geen loopimpact op de maag.","tips":[
        ("✅","Vast voedsel werkt goed","Rijstwafels, repen en bananen zijn ideaal."),
        ("✅","Sportdrank als basis","Vul bidons met sportdrank voor constante KH-inname."),
        ("✅","Gels als aanvulling","Bij hogere intensiteit of als vast voedsel moeilijk gaat."),
        ("💡","Grote variatie mogelijk","Zittend verdraagt de maag meer verschillende producten."),
    ]},
    "Lopen":{"icon":"🏃","intro":"Schokbelasting bij lopen — kies eenvoudig en bewezen.","tips":[
        ("⚠️","Vermijd vast voedsel","Loopbeweging verhoogt kans op maagklachten sterk."),
        ("✅","Gels + water is gouden combinatie","Elke gel altijd met minstens 150ml water — nooit met sportdrank."),
        ("⚠️","Gel en sportdrank niet combineren","Neem óf een gel met water, óf sportdrank — nooit gel wegspoelen met sportdrank. Dit geeft een te hoge suikerconcentratie in de darm."),

        ("💡","Kleine frequente porties","Liever 3x klein dan 1x groot per uur."),
    ]},
    "Triatlon":{"icon":"🏊🚴🏃","intro":"Stem voeding af per segment.","tips":[
        ("ℹ️","Zwemmen: geen voeding","Start vroeg op de fiets — maag is nog fris."),
        ("✅","Fiets: maximale inname","Vast voedsel, sportdrank én gels mogelijk."),
        ("⚠️","Loop: enkel vloeibaar","Geen vast voedsel na T2."),
        ("💡","Overgang fiets→loop","Laatste inname minstens 10 min voor T2."),
    ]},
    "Duatlon":{"icon":"🏃🚴","intro":"Begin en eindig met lopen — plan per segment.","tips":[
        ("⚠️","Eerste loop: licht houden","Enkel gels/sportdrank — maag is nog koud."),
        ("✅","Fiets: ideaal moment","Beste kans voor hogere KH-inname."),
        ("⚠️","Tweede loop: enkel vloeibaar","Maag is al vermoeid."),
        ("💡","Timing","Laatste vaste voeding 15 min voor einde fiets."),
    ]},
    "Crosstriatlon":{"icon":"🚵","intro":"Offroad verhoogt schokbelasting — extra voorzichtig.","tips":[
        ("⚠️","Vermijd vast voedsel","Oneven ondergrond maakt vast voedsel risicovol."),
        ("✅","Enkel vloeibaar en isotone gels","Goed verteerbare, isotone producten."),
        ("⚠️","Geen nieuwe producten op offroad","Test eerst op de weg."),
        ("💡","Hydratatie prioriteit","Regelmatig drinken moeilijker — train dit bewust."),
    ]},
}

# ── Diagnose tabel ─────────────────────────────────────────────────────────────
DIAGNOSE_TABEL = [
    ({"Misselijkheid"},              "Laat",  True,  True,  "Hypertone gel met te weinig water bij hoge intensiteit",  "Isotone gel of verdunnen met 200ml water"),
    ({"Misselijkheid"},              "Laat",  True,  False, "Maag overbelast door hoge intensiteit laat in wedstrijd", "Minder zoete variant of neutrale gel"),
    ({"Misselijkheid"},              "Begin", False, False, "Mogelijk te hoge glucose:fructose verhouding",            "Product met 2:1 glucose:fructose verhouding"),
    ({"Krampen"},                    "Begin", False, True,  "Hypertoon product met te weinig water",                   "Altijd 150-200ml water per portie"),
    ({"Krampen"},                    "Midden",True,  False, "Hoge osmolariteit bij hogere intensiteit",                "Hypotone sportdrank of isotone gel"),
    ({"Opgeblazen gevoel"},          "Begin", False, False, "Mogelijk polyolen of teveel natrium",                     "Check ingrediënten op sorbitol/maltitol"),
    ({"Opgeblazen gevoel"},          "Midden",False, False, "Mogelijke fructose-intolerantie bij hogere dosering",     "Product met enkel glucose"),
    ({"Reflux / brandend maagzuur"}, "Laat",  True,  False, "Cafeïne of hoge zuurtegraad bij hoge intensiteit",       "Cafeïnevrije gel, vermijd citroensmaak"),
    ({"Diarree"},                    "Begin", True,  False, "Hypertoon product bij hoge intensiteit",                  "Hypotone sportdrank"),
    ({"Diarree"},                    "Midden",False, False, "Hoge fructosedosis",                                      "Max 60g glucose/uur of 2:1 verhouding"),
    ({"Lichte maagkramp"},           "Begin", False, True,  "Te weinig water bij inname",                              "Minimaal 150ml water per portie"),
]

def _genereer_diagnose(klachten, moment, intensiteit, water):
    intensiteit_hoog = intensiteit in ["Z4 — Drempeltraining","Z5 — Wedstrijdintensiteit"]
    water_weinig     = water == "< 100ml"
    klachten_set     = set(klachten)
    for r_kl, r_mom, r_int, r_wat, diag, alt in DIAGNOSE_TABEL:
        if (r_kl & klachten_set and r_mom == moment and
                r_int == intensiteit_hoog and r_wat == water_weinig):
            return diag, alt
    if "Misselijkheid" in klachten_set:
        return "Mogelijke overbelasting maag", "Verlaag concentratie, spreid innamen"
    if "Krampen" in klachten_set:
        return "Osmotische kramp", "Meer water (min 150ml) per portie"
    if "Diarree" in klachten_set:
        return "Hoge osmolariteit of fructose", "Hypotone sportdrank als alternatief"
    return "Onvoldoende data", "Overweeg alternatief product"


# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE API — SCHEMA GENERATIE
# ═══════════════════════════════════════════════════════════════════════════════

def _get_claude_client():
    """Maak Anthropic client aan via environment variable (Render) of Streamlit secrets."""
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
    if not api_key:
        st.warning("⚠️ ANTHROPIC_API_KEY niet gevonden — fallback schema wordt gebruikt.")
        return None
    return anthropic.Anthropic(api_key=api_key)



# ═══════════════════════════════════════════════════════════════════════════════
# WATERVALSTRATEGIE — SCHEMA GENERATIE
# ═══════════════════════════════════════════════════════════════════════════════

KLACHT_ALTERNATIEF = {
    "Lichte maagkramp": "Meer water bij inname (min. 200ml), of isotone gel proberen",
    "Krampen":          "Meer water bij inname (min. 200ml), of isotone gel proberen",
    "Misselijkheid":    "Minder zoete variant of lagere concentratie sportdrank",
    "Opgeblazen gevoel":"Check fructose/polyolen in ingredienten, kies ander type",
    "Reflux / brandend maagzuur": "Caffeinevrije variant, neutrale smaak",
    "Diarree":          "Hypotone variant of lagere osmolariteit",
    "Braken":           "Stop testtraining, drastisch verlagen naar 0.5 portie",
    "Hoofdpijn":        "Hydratatie verhogen, natrium controleren",
    "Steken in de zij": "Timing aanpassen — later innemen, kleinere slokken",
}


def _sorteer_producten_lopen(producten: list) -> list:
    PRIORITEIT = {"Gel": 0, "Cafeinegel": 1, "Sportdrank": 2,
                  "Supplement": 3, "Vast voedsel": 4}
    def sort_key(p):
        prio  = PRIORITEIT.get(p.get("type","Supplement"), 5)
        kh    = p.get("kh", 99)
        klacht= 1 if p.get("status") == "klachten" else 0
        return (klacht, prio, kh)
    return sorted(producten, key=sort_key)


def _bereken_start_porties_lopen(ervaring, target_kh, huidige_inname, kh_pp):
    if kh_pp <= 0:
        return 1
    if ervaring == "Nog nooit":
        return 1
    elif ervaring == "2-4 wedstrijden":
        start = round(target_kh * 0.55)
    elif ervaring == "5-10 wedstrijden":
        start = min(huidige_inname, round(target_kh * 0.80))
    else:
        start = min(huidige_inname, round(target_kh * 0.90))
    return max(1, round(start / max(kh_pp, 1)))


def _bepaal_intensiteit_lopen(week_nr, fase_logs):
    if week_nr <= 2:
        return "Z2 - Duurtraining"
    gesorteerd = sorted([(int(k),v) for k,v in fase_logs.items()], key=lambda x:x[0])
    if week_nr <= 4:
        if len(gesorteerd) >= 2:
            laatste2 = [v for _,v in gesorteerd[-2:]]
            if all(l.get("score",0) >= 4 for l in laatste2):
                return "Z3 - Tempo"
        return "Z2 - Duurtraining"
    if len(gesorteerd) >= 2:
        laatste2 = [v for _,v in gesorteerd[-2:]]
        if all(l.get("score",0) >= 4 and
               l.get("symptoom","") in ["","Geen klachten"] for l in laatste2):
            return "Z4 - Drempeltraining"
    return "Z3 - Tempo"


def _volgende_product_lopen(gesorteerde_prods, logs_fase):
    if not gesorteerde_prods:
        return {"naam":"---","kh":22,"type":"Gel","status":""}
    if not logs_fase:
        zonder_klachten = [p for p in gesorteerde_prods if p.get("status") != "klachten"]
        return zonder_klachten[0] if zonder_klachten else gesorteerde_prods[0]
    gesorteerd_logs = sorted([(int(k),v) for k,v in logs_fase.items()], key=lambda x:x[0])
    prev_log        = gesorteerd_logs[-1][1]
    prev_prod_naam  = prev_log.get("product","")
    prev_score      = prev_log.get("score", 3)
    prev_klacht     = prev_log.get("symptoom","Geen klachten") not in ["","Geen klachten"]
    prod_namen = [p["naam"] for p in gesorteerde_prods]
    try:
        huidig_idx = prod_namen.index(prev_prod_naam)
    except ValueError:
        huidig_idx = 0
    if prev_klacht or prev_score <= 2:
        volgende_idx = huidig_idx + 1
        if volgende_idx < len(gesorteerde_prods):
            return gesorteerde_prods[volgende_idx]
        else:
            return gesorteerde_prods[0]
    else:
        return gesorteerde_prods[huidig_idx]


def _alle_producten_klachten(gesorteerde_prods, logs_fase):
    prod_namen_klacht = set()
    for v in logs_fase.values():
        if v.get("symptoom","Geen klachten") not in ["","Geen klachten"]:
            prod_namen_klacht.add(v.get("product",""))
    alle_namen = set(p["naam"] for p in gesorteerde_prods)
    return alle_namen.issubset(prod_namen_klacht) and len(alle_namen) > 0


def _bereken_volgende_porties_lopen(prev_porties, score, heeft_klachten,
                                     max_porties, product_gewisseld):
    if product_gewisseld:
        return 1
    if score >= 4 and not heeft_klachten:
        delta = 1
    elif score == 3 and not heeft_klachten:
        delta = 0
    else:
        delta = -1
    return max(1, min(prev_porties + delta, max_porties))


def _genereer_schema_lopen(data, logs, actieve_fase):
    producten      = [p for p in data.get("producten",[]) if p.get("naam")]
    ervaring       = data.get("ervaring","Nog nooit")
    target_kh      = int(data.get("target_kh", 60))
    huidige_inname = int(data.get("huidige_inname", 0))
    eetmom         = int(data.get("eetmomenten", 2))
    fase_logs      = {k:v for k,v in logs.items()
                      if v.get("fase")==actieve_fase and v.get("ingevuld")}
    week_nr        = len([v for v in logs.values() if v.get("ingevuld")]) + 1
    gesorteerd     = _sorteer_producten_lopen(producten)
    huidig_prod    = _volgende_product_lopen(gesorteerd, fase_logs)
    kh_pp          = huidig_prod.get("kh", 22)

    prev_prod_naam    = ""
    product_gewisseld = False
    if fase_logs:
        prev_log       = sorted([(int(k),v) for k,v in fase_logs.items()])[-1][1]
        prev_prod_naam = prev_log.get("product","")
        product_gewisseld = bool(prev_prod_naam) and huidig_prod["naam"] != prev_prod_naam

    if not fase_logs:
        porties = _bereken_start_porties_lopen(
            ervaring, target_kh, huidige_inname, kh_pp)
    else:
        prev_log       = sorted([(int(k),v) for k,v in fase_logs.items()])[-1][1]
        prev_porties   = prev_log.get("porties", 1)
        prev_score     = prev_log.get("score", 3)
        heeft_klachten = prev_log.get("symptoom","Geen klachten") not in ["","Geen klachten"]
        max_porties    = max(1, round(target_kh / max(kh_pp,1)))
        porties = _bereken_volgende_porties_lopen(
            prev_porties, prev_score, heeft_klachten, max_porties, product_gewisseld)

    kh_totaal = porties * kh_pp
    interval  = max(10, round(60 / max(eetmom, porties) / 5) * 5)
    zone      = _bepaal_intensiteit_lopen(week_nr, fase_logs)

    if product_gewisseld:
        progressie = "product gewisseld"
    elif not fase_logs:
        progressie = "start"
    else:
        prev_p = sorted(fase_logs.items())[-1][1].get("porties",1)
        if porties > prev_p:   progressie = "omhoog"
        elif porties < prev_p: progressie = "omlaag"
        else:                  progressie = "herhalen"

    alternatief_voorstel = ""
    if fase_logs:
        prev_log       = sorted([(int(k),v) for k,v in fase_logs.items()])[-1][1]
        heeft_klachten = prev_log.get("symptoom","Geen klachten") not in ["","Geen klachten"]
        if heeft_klachten and _alle_producten_klachten(gesorteerd, fase_logs):
            klacht = prev_log.get("symptoom","")
            alternatief_voorstel = KLACHT_ALTERNATIEF.get(
                klacht, "Overweeg een ander producttype te testen")

    if product_gewisseld:
        tip = "Nieuw product - start opnieuw met 1 portie en observeer goed."
    elif porties == 1:
        tip = "Neem de gel altijd met 150-200ml water - nooit met sportdrank."
    else:
        tip = f"Spreid {porties} porties gelijkmatig - elke {interval} minuten, altijd met 150-200ml water."

    return {
        "week": week_nr, "fase": actieve_fase,
        "product": huidig_prod["naam"], "kh_pp": kh_pp,
        "porties": porties, "kh_totaal": kh_totaal,
        "interval_min": interval, "intensiteit": zone,
        "progressie": progressie, "tip": tip,
        "alternatief": alternatief_voorstel, "duur_min": "90-120",
    }


def _genereer_schema(data, logs, actieve_fase):
    sport = data.get("sport","Fietsen")
    if sport == "Lopen":
        return _genereer_schema_lopen(data, logs, actieve_fase)
    return _genereer_schema_lopen(data, logs, actieve_fase)



# ═══════════════════════════════════════════════════════════════════════════════
# HULPFUNCTIES
# ═══════════════════════════════════════════════════════════════════════════════

def _sectie(titel, kleur="#f97316"):
    st.markdown(
        f'<div style="font-size:0.72rem;font-weight:700;color:{kleur};'
        f'letter-spacing:2px;margin:18px 0 8px;padding-bottom:4px;'
        f'border-bottom:1px solid #1e293b;">{titel}</div>',
        unsafe_allow_html=True)


def _score_kleur(score):
    if score >= 4.5: return "#22c55e"
    if score >= 3.5: return "#84cc16"
    if score >= 2.5: return "#fbbf24"
    if score >= 1.5: return "#f97316"
    return "#ef4444"


def _score_label(score):
    return {1:"Zeer slecht ❌",2:"Slecht ⚠️",3:"Matig 🟡",
            4:"Goed ✅",5:"Uitstekend 🌟"}.get(score,"—")


def _is_fase_stabiel(logs: dict, fase_naam: str, target_kh: int = 0) -> bool:
    fase_logs = {k:v for k,v in logs.items()
                 if v.get("fase")==fase_naam and v.get("ingevuld")}
    if len(fase_logs) < 2:
        return False
    laatste2 = [v for _,v in sorted(fase_logs.items(), key=lambda x:int(x[0]))[-2:]]
    scores_ok = all(l.get("score",0) >= 4 and
                    l.get("symptoom","") in ["","Geen klachten"] for l in laatste2)
    if not scores_ok:
        return False
    # Afgerond enkel als laatste 2 weken op Z4/Z5 waren EN target bereikt
    z4_ok = all("Z4" in l.get("intensiteit","") or "Z5" in l.get("intensiteit","")
                for l in laatste2)
    if target_kh > 0:
        target_ok = any(l.get("kh_doel",0) >= target_kh for l in laatste2)
        return z4_ok and target_ok
    return z4_ok

def _bereken_startpunt(data: dict) -> int:
    maag     = data.get("maag_gevoelig","Af en toe")
    ervaring = data.get("ervaring","Nog nooit")
    sport    = data.get("sport","Fietsen")
    inname   = int(data.get("huidige_inname",0))
    target   = int(data.get("target_kh",60))
    temp     = data.get("temp",16)
    hoogte   = data.get("hoogte",0)

    if maag == "Altijd met sportvoeding":
        start = 10
    elif maag == "Nooit":
        if ervaring == "Nog nooit":          start = round(target*0.40)
        elif ervaring == "2-4 wedstrijden":  start = round(target*0.55)
        elif ervaring == "5-10 wedstrijden": start = min(inname, round(target*0.80))
        else:                                start = min(inname, round(target*0.90))
    else:
        if ervaring == "Nog nooit":          start = round(target*0.30)
        elif ervaring == "2-4 wedstrijden":  start = round(target*0.45)
        elif ervaring == "5-10 wedstrijden": start = min(round(inname*0.60), round(target*0.70))
        else:                                start = min(round(inname*0.70), round(target*0.80))

    if sport in ["Lopen","Crosstriatlon"]: start = max(10, start-5)
    if temp > 28:    start = max(10, start-5)
    if hoogte > 2000: start = max(10, start-5)
    return round(start/5)*5


def _volgende_week_nr(logs: dict) -> int:
    if not logs:
        return 1
    ingevulde = [int(k) for k,v in logs.items() if v.get("ingevuld")]
    return max(ingevulde)+1 if ingevulde else 1


def _actieve_fase(sport: str, logs: dict) -> str:
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])
    for fase in fases:
        if not _is_fase_stabiel(logs, fase["naam"]):
            return fase["naam"]
    return fases[-1]["naam"]


# ═══════════════════════════════════════════════════════════════════════════════
# STAPPEN
# ═══════════════════════════════════════════════════════════════════════════════

def _stap_intro():
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;
                padding:24px;margin-bottom:20px;">
        <div style="font-size:1rem;font-weight:800;color:#f8fafc;margin-bottom:10px;">
            Waarom maagtraining?</div>
        <div style="font-size:0.85rem;color:#94a3b8;line-height:1.8;">
            Tijdens intensieve inspanning vermindert de bloedtoevoer naar je maag.
            Door systematisch te trainen went je maag aan grotere hoeveelheden koolhydraten.
            <br><br>
            Carboo begeleidt je stap voor stap — op basis van jouw wekelijkse scores
            en symptomen wordt je schema progressief opgebouwd.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _sectie("HOE WERKT HET?")
    for nr, naam, uitleg in [
        ("1","Profiel","Sport, duur, ervaring en productgeschiedenis"),
        ("2","Producten","Producten bevestigen of aanvullen"),
        ("3","Schema","Carboo stelt jouw persoonlijk weekplan op"),
        ("4","Dagboek","Score en symptomen invullen na training"),
        ("5","Rapport","Welke producten werken op racedag"),
    ]:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;'
            f'border-bottom:1px solid #1e293b;">'
            f'<div style="width:24px;height:24px;border-radius:50%;background:#f97316;'
            f'display:flex;align-items:center;justify-content:center;font-size:11px;'
            f'font-weight:700;color:white;flex-shrink:0;">{nr}</div>'
            f'<div><span style="font-weight:600;color:#f8fafc;">{naam}</span> '
            f'<span style="color:#64748b;font-size:0.82rem;">— {uitleg}</span></div>'
            f'</div>', unsafe_allow_html=True)


def _stap_profiel():
    _sectie("JOUW TRAININGSPROFIEL")
    data       = st.session_state.get("tg_data", {})
    ERV_OPTIES = ["Nog nooit","2-4 wedstrijden","5-10 wedstrijden","Meer dan 10 wedstrijden"]

    # ── Sport & Niveau ────────────────────────────────────────────────────────
    _sectie("SPORT & NIVEAU")
    c1, c2 = st.columns(2)
    with c1:
        sport = st.selectbox("Sport", SPORTEN,
                              index=SPORTEN.index(data.get("sport","Fietsen")),
                              key="tg_sport")
    with c2:
        niveau = st.selectbox("Niveau", ["Recreatief","Competitief","Elite"],
                               index=["Recreatief","Competitief","Elite"].index(
                                   data.get("niveau","Recreatief")), key="tg_niveau")
    test_discipline = data.get("test_discipline","Beide")

    # ── Ervaring ─────────────────────────────────────────────────────────────
    _sectie("ERVARING MET WEDSTRIJDVOEDING")
    ervaring = st.radio("Hoeveel wedstrijden heb je al voeding gebruikt?",
                         ERV_OPTIES,
                         index=ERV_OPTIES.index(data.get("ervaring","Nog nooit")),
                         key="tg_ervaring", horizontal=True)

        # ── Opslaan ───────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Volgende →", key="tg_prof_next", use_container_width=True):
        st.session_state.tg_data = {
            "sport":    sport,
            "niveau":   niveau,
            "ervaring": ervaring,
            "test_discipline": test_discipline,
        }
        st.session_state.tg_stap = 3
        st.rerun()


def _stap_producten():
    _sectie("TE TESTEN PRODUCTEN")
    data  = st.session_state.get("tg_data",{})
    sport = data.get("sport","Fietsen")
    opgeslagen = data.get("producten",[{"naam":"","type":"Gel","kh":22,"rol":"Test"}])
    n = st.session_state.get("tg_n_prod", len(opgeslagen))

    # Sport tips in 1 venster
    sport_tips = SPORT_PRODUCT_TIPS.get(sport)
    if sport_tips:
        tips_html = (
            f'<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;'
            f'padding:16px;margin-bottom:20px;">'
            f'<div style="font-size:0.72rem;font-weight:700;color:#f97316;letter-spacing:2px;'
            f'margin-bottom:8px;">{sport_tips["icon"]} PRODUCTTIPS VOOR {sport.upper()}</div>'
            f'<div style="font-size:0.82rem;color:#94a3b8;margin-bottom:12px;font-style:italic;">'
            f'{sport_tips["intro"]}</div>'
        )
        kleur_map = {"✅":"#22c55e","⚠️":"#fbbf24","💡":"#3b82f6","ℹ️":"#64748b"}
        for icoon, titel, uitleg in sport_tips["tips"]:
            kleur = kleur_map.get(icoon,"#94a3b8")
            tips_html += (
                f'<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #1e293b;">'
                f'<div style="font-size:1rem;flex-shrink:0;">{icoon}</div>'
                f'<div><span style="font-weight:700;color:{kleur};font-size:0.82rem;">{titel}</span>'
                f'<span style="color:#64748b;font-size:0.8rem;"> — {uitleg}</span></div>'
                f'</div>'
            )
        tips_html += '</div>'
        st.markdown(tips_html, unsafe_allow_html=True)

    # Diagnoses uit profiel
    gekende = data.get("gekende_producten",[])
    if any(p.get("diagnose") for p in gekende):
        _sectie("DIAGNOSE UIT PROFIEL","#3b82f6")
        for p in gekende:
            if p.get("diagnose"):
                verd  = p.get("verdraagbaarheid","")
                kl    = "#fbbf24" if verd=="Soms klachten" else "#ef4444"
                pn    = p["naam"]
                pd    = p["diagnose"]
                pa    = p["alternatief"]
                st.markdown(
                    f'<div style="background:#0f172a;border:1px solid {kl};'
                    f'border-radius:8px;padding:10px;margin-bottom:6px;">'
                    f'<div style="font-size:0.82rem;font-weight:700;color:{kl};">{pn}</div>'
                    f'<div style="font-size:0.78rem;color:#94a3b8;">Oorzaak: {pd}</div>'
                    f'<div style="font-size:0.78rem;color:#22c55e;">✅ Alternatief: {pa}</div>'
                    f'</div>', unsafe_allow_html=True)



    st.markdown(
        '<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;'
        'padding:16px;margin-bottom:16px;">',
        unsafe_allow_html=True)

    _sectie("TE TESTEN PRODUCTEN")

    h1,h2,h3,h4 = st.columns([3,2,1,1])
    for col, lbl in [(h1,"Product"),(h2,"Type"),(h3,"KH/portie"),(h4,"")]:
        col.markdown(f'<div style="font-size:10px;color:#64748b;">{lbl}</div>',
                     unsafe_allow_html=True)

    producten      = []
    waarschuwingen = SPORT_PRODUCT_WAARSCHUWINGEN.get(sport,{})

    for i in range(n):
        p = opgeslagen[i] if i < len(opgeslagen) else {"naam":"","type":"Gel","kh":22,"rol":"Test"}
        c1,c2,c3,c4 = st.columns([3,2,1,1])
        with c1:
            naam = st.text_input(f"n{i}", value=p.get("naam",""),
                                  placeholder="Productnaam",
                                  key=f"tg_pnaam_{i}", label_visibility="collapsed")
        with c2:
            idx_t = PRODUCT_TYPES.index(p.get("type","Gel")) \
                    if p.get("type") in PRODUCT_TYPES else 0
            ptype = st.selectbox(f"t{i}", PRODUCT_TYPES, index=idx_t,
                                  key=f"tg_ptype_{i}", label_visibility="collapsed")
        with c3:
            kh = st.number_input(f"k{i}", 0, 120, int(p.get("kh",22)),
                                   key=f"tg_pkh_{i}", label_visibility="collapsed")
        with c4:
            if n > 1 and st.button("✕", key=f"tg_pdel_{i}"):
                st.session_state["tg_n_prod"] = n-1
                st.rerun()
        producten.append({"naam":naam,"type":ptype,"kh":kh,"rol":"Test",
                           "status":p.get("status","")})

        # Waarschuwing als product overeenkomt met een gekend klachtenproduct uit profiel
        if naam:
            gekende_klachten = [
                g for g in data.get("gekende_producten",[])
                if g.get("verdraagbaarheid") == "Klachten"
                and g.get("naam","").strip().lower() == naam.strip().lower()
            ]
            if gekende_klachten:
                gk = gekende_klachten[0]
                diag_txt = f" | Oorzaak: {gk['diagnose']}" if gk.get("diagnose") else ""
                alt_txt  = f" | Alternatief: {gk['alternatief']}" if gk.get("alternatief") else ""
                st.markdown(
                    f'<div style="background:#1a0a0a;border-left:3px solid #ef4444;'
                    f'border-radius:0 8px 8px 0;padding:8px 14px;margin:2px 0 8px 0;'
                    f'font-size:0.8rem;color:#ef4444;">'
                    f'⚠️ <b>Je had al klachten met {naam}</b>{diag_txt}'
                    f'{"<br><span style=\'color:#22c55e;\'>✅ " + gk["alternatief"] + "</span>" if gk.get("alternatief") else ""}'
                    f'</div>',
                    unsafe_allow_html=True)

        if ptype in waarschuwingen:
            ic, kl, tx = waarschuwingen[ptype]
            st.markdown(
                f'<div style="background:#0f172a;border-left:3px solid {kl};'
                f'border-radius:0 6px 6px 0;padding:6px 12px;'
                f'margin:-4px 0 8px 0;font-size:0.78rem;color:{kl};">'
                f'{ic} {tx}</div>', unsafe_allow_html=True)

    col_add, _ = st.columns([2,3])
    with col_add:
        if st.button("＋ Product toevoegen", key="tg_padd", use_container_width=True):
            st.session_state["tg_n_prod"] = n+1
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    gevulde = [p for p in producten if p["naam"]]

    # ── Carboo Coach chatbot ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💬 Stel een vraag aan Carboo Coach", expanded=False):
        st.markdown(
            '<div style="font-size:0.78rem;color:#64748b;margin-bottom:10px;">'+
            'Carboo Coach geeft neutrale, wetenschappelijk onderbouwde informatie. '+
            'Geen merkaanbevelingen — enkel feiten en richtlijnen.</div>',
            unsafe_allow_html=True)

        if "tg_chat_history" not in st.session_state:
            st.session_state.tg_chat_history = []

        for msg in st.session_state.tg_chat_history:
            if msg["rol"] == "coach":
                rol_kleur = "#f97316"
                rol_naam  = "Carboo Coach"
                bg_kleur  = "#1e293b"
                tekst_kleur = "#f8fafc"
            else:
                rol_kleur = "#3b82f6"
                rol_naam  = "Jij"
                bg_kleur  = "#0f172a"
                tekst_kleur = "#e2e8f0"
            tekst_veilig = msg["tekst"]
            st.markdown(
                f'<div style="background:{bg_kleur};border-left:3px solid {rol_kleur};'+
                f'border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:10px;">'+
                f'<div style="font-size:11px;color:{rol_kleur};font-weight:800;'+
                f'letter-spacing:1px;margin-bottom:6px;">{rol_naam}</div>'+
                f'<div style="font-size:0.88rem;color:{tekst_kleur};line-height:1.6;">{tekst_veilig}</div>'+
                f'</div>', unsafe_allow_html=True)

        vraag = st.text_input("Jouw vraag...",
                               placeholder="bijv. Wat is osmolariteit bij sportgels?",
                               key="tg_chat_input")

        col_send, col_clear = st.columns([3,1])
        with col_send:
            stuur = st.button("Stuur →", key="tg_chat_stuur", use_container_width=True)
        with col_clear:
            if st.button("Wis", key="tg_chat_wis", use_container_width=True):
                st.session_state.tg_chat_history = []
                st.rerun()

        if stuur and vraag.strip():
            client = _get_claude_client()
            if client:
                sport_ctx  = data.get("sport","Fietsen")
                erv_ctx    = data.get("ervaring","Nog nooit")
                duur_ctx   = data.get("wedstrijd_duur",120)
                prod_ctx   = ", ".join(p["naam"] for p in data.get("producten",[]) if p.get("naam")) or "nog niet ingevuld"
                gekend_ctx = ", ".join(
                    p["naam"] + (" (klachten)" if p.get("verdraagbaarheid")=="Klachten" else " (OK)")
                    for p in data.get("gekende_producten",[]) if p.get("naam")
                ) or "geen"

                # Haal KH richtlijn op voor deze atleet
                kh_min_c, kh_max_c = _get_richtlijn(sport_ctx, duur_ctx)
                kh_richtlijn_txt = (f"{kh_min_c}–{kh_max_c}g KH/uur"
                                    if kh_max_c > 0 else "geen extra KH nodig")

                systeem = (
                    "Je bent Carboo Coach, een neutrale sportvoedingsadviseur. "
                    "Je geeft wetenschappelijk onderbouwde informatie over sportvoeding tijdens inspanning. "
                    "REGELS: geen merkaanbevelingen of commerciele uitspraken, geen specifieke producten aanraden op naam, "
                    "wel uitleg over producttypen, ingredienten, osmolariteit, verhoudingen, timing, wetenschappelijke richtlijnen. "
                    "Antwoord altijd in het Nederlands. Beknopt: max 4-5 zinnen tenzij uitgebreide uitleg nodig is. "
                    f"CONTEXT ATLEET: Sport: {sport_ctx} | Duur: {duur_ctx} min | Ervaring: {erv_ctx} | "
                    f"KH-richtlijn voor deze atleet: {kh_richtlijn_txt} | "
                    f"Te testen producten: {prod_ctx} | Gekende producten: {gekend_ctx}. "
                    f"Gebruik ALTIJD de KH-richtlijn van {kh_richtlijn_txt} als je spreekt over aanbevolen hoeveelheden voor deze atleet, "
                    f"niet de algemene 60-90g/uur waarde tenzij die overeenkomt."
                )

                berichten = []
                for m in st.session_state.tg_chat_history[-6:]:
                    rol = "assistant" if m["rol"] == "coach" else "user"
                    berichten.append({"role": rol, "content": m["tekst"]})
                berichten.append({"role": "user", "content": vraag.strip()})

                with st.spinner("Carboo Coach denkt na..."):
                    try:
                        antwoord_msg = client.messages.create(
                            model="claude-opus-4-5",
                            max_tokens=400,
                            system=systeem,
                            messages=berichten,
                        )
                        antwoord = antwoord_msg.content[0].text.strip()
                    except Exception as e:
                        antwoord = f"Even geen verbinding. Probeer opnieuw. ({e})"

                st.session_state.tg_chat_history.append({"rol":"user",  "tekst": vraag.strip()})
                st.session_state.tg_chat_history.append({"rol":"coach", "tekst": antwoord})
                st.rerun()
            else:
                st.warning("Coach niet beschikbaar — API key ontbreekt.")

    # ── Navigatie ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c_terug, c_next = st.columns([1,2])
    with c_terug:
        if st.button("← Terug", key="tg_prod_back", use_container_width=True):
            st.session_state.tg_stap = 2
            st.rerun()
    with c_next:
        if st.button("🚀 Start met testen →", key="tg_prod_next", use_container_width=True):
            gevulde = [p for p in producten if p["naam"]]
            if not gevulde:
                st.error("Voeg minstens 1 product toe.")
            else:
                st.session_state.tg_data["producten"] = gevulde
                st.session_state.tg_stap = 4
                st.rerun()


def _stap_schema():
    """Schema — Claude API genereert het weekplan."""
    _sectie("TESTSCHEMA")
    data  = st.session_state.get("tg_data",{})
    logs  = st.session_state.get("tg_logs",{})
    sport = data.get("sport","Fietsen")
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])

    producten  = [p for p in data.get("producten",[]) if p.get("naam")]
    basis_prod = next((p for p in producten if p.get("rol")=="Basis"), None)
    test_prods = [p for p in producten if p.get("rol")=="Test"]
    basis_kh   = basis_prod["kh"] if basis_prod else 0
    target_kh  = int(data.get("target_kh",60))

    # Bepaal actieve fase
    actieve_fase_naam = _actieve_fase(sport, logs)
    data["actieve_fase"] = actieve_fase_naam
    st.session_state.tg_data = data

    # ── Fase voortgang ────────────────────────────────────────────────────────
    _sectie("VOORTGANG PER FASE")
    fase_kleuren = ["#3b82f6","#f97316","#8b5cf6","#22c55e"]
    for fi, fase in enumerate(fases):
        fn     = fase["naam"]
        fi_ic  = fase["icon"]
        fkl    = fase_kleuren[fi % len(fase_kleuren)]
        stab   = _is_fase_stabiel(logs, fn, target_kh)
        actief = fn == actieve_fase_naam
        gelockt= not stab and not actief and fi > 0
        # Controleer of vorige fase stabiel is
        if fi > 0:
            prev_stab = _is_fase_stabiel(logs, fases[fi-1]["naam"], target_kh)
            gelockt   = not prev_stab and not actief

        status = "✅ Afgerond" if stab else ("📝 Actief" if actief else "🔒 Wacht")
        sk     = "#22c55e" if stab else (fkl if actief else "#334155")

        n_weken = len([v for v in logs.values()
                       if v.get("fase")==fn and v.get("ingevuld")])
        st.markdown(
            f'<div style="background:#0f172a;border:2px solid {sk};border-radius:10px;'
            f'padding:12px 14px;margin-bottom:8px;{"opacity:0.4;" if gelockt else ""}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span>{fi_ic}</span>'
            f'<span style="font-weight:800;color:#f8fafc;">{fn}</span>'
            f'{"<span style=\\'font-size:11px;color:#64748b;\\'>" + str(n_weken) + " weken gelogd</span>" if n_weken > 0 else ""}'
            f'</div>'
            f'<span style="font-size:0.75rem;font-weight:700;color:{sk};">{status}</span>'
            f'</div></div>',
            unsafe_allow_html=True)

    # ── Weken van actieve fase ────────────────────────────────────────────────
    _sectie(f"SCHEMA — {actieve_fase_naam.upper()}", "#3b82f6")

    fase_logs = {k:v for k,v in logs.items()
                 if v.get("fase")==actieve_fase_naam and v.get("ingevuld")}

    for wn in sorted(fase_logs.keys(), key=int):
        lw      = logs[wn]
        porties = lw.get("porties",1)
        pnaam   = lw.get("product","—")
        kh_pp   = lw.get("kh_pp",0)
        kh_tot  = basis_kh + porties*kh_pp
        pct     = round((kh_tot/max(target_kh,1))*100)
        s       = lw.get("score",0)
        sym     = lw.get("symptoom","")
        prog    = lw.get("progressie","")
        prog_kl = "#22c55e" if prog=="omhoog" else ("#ef4444" if prog=="omlaag" else "#fbbf24")

        score_html = f"<div>Score: <b style='color:{_score_kleur(s)};'>{s}/5</b></div>" if s else ""
        sym_html   = (f"<div>{sym if sym and sym!='Geen klachten' else '✅ Geen klachten'}</div>"
                      if s else "")
        prog_html  = (f'<div style="color:{prog_kl};font-size:10px;">▶ {prog}</div>'
                      if prog else "")

        st.markdown(
            f'<div style="background:#0a0f1e;border:1px solid #22c55e;'
            f'border-radius:8px;padding:12px;margin-bottom:6px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            f'<span style="font-weight:700;color:#f8fafc;">Week {wn}</span>'
            f'<span style="font-weight:800;color:#22c55e;">{kh_tot}g/uur</span>'
            f'</div>'
            f'<div style="background:#1e293b;border-radius:3px;height:4px;overflow:hidden;margin-bottom:8px;">'
            f'<div style="width:{min(pct,100)}%;height:100%;background:#22c55e;border-radius:3px;"></div>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:0.75rem;color:#94a3b8;">'
            f'<div>🧪 <b style="color:#f8fafc;">{pnaam}</b> — {porties}x {kh_pp}g</div>'
            f'{prog_html}'
            f'{score_html}{sym_html}'
            f'</div></div>',
            unsafe_allow_html=True)

    # ── Volgende week genereren ───────────────────────────────────────────────
    volgende_wn = _volgende_week_nr(logs)
    stabiel     = _is_fase_stabiel(logs, actieve_fase_naam, target_kh)

    if stabiel:
        st.markdown(
            f'<div style="background:#0a1a0a;border:1px solid #22c55e;border-radius:8px;'
            f'padding:12px;margin-bottom:12px;font-size:0.82rem;color:#22c55e;">'
            f'✅ <b>{actieve_fase_naam} afgerond!</b> 2 weken stabiel met score ≥ 4.</div>',
            unsafe_allow_html=True)
        # Controleer of er nog fases zijn
        fase_namen = [f["naam"] for f in fases]
        huidige_idx = fase_namen.index(actieve_fase_naam) if actieve_fase_naam in fase_namen else 0
        if huidige_idx < len(fases)-1:
            volgende_fase = fases[huidige_idx+1]["naam"]
            if st.button(f"▶ Start {volgende_fase}", key="tg_start_fase",
                          use_container_width=True):
                st.session_state.tg_data["actieve_fase"] = volgende_fase
                st.rerun()
        else:
            st.success("🏁 Alle fases afgerond! Bekijk je rapport.")
    else:
        # Genereer schema via watervalstrategie
        cache_key = f"tg_schema_week_{volgende_wn}"
        if cache_key not in st.session_state:
            schema = _genereer_schema(data, logs, actieve_fase_naam)
            st.session_state[cache_key] = schema
        else:
            schema = st.session_state[cache_key]

        # Toon gepland schema
        pnaam    = schema.get("product","—")
        porties  = schema.get("porties",1)
        kh_test  = schema.get("kh_test",0)
        kh_basis = schema.get("kh_basis",0)
        kh_tot   = schema.get("kh_totaal", kh_basis+kh_test)
        interval = schema.get("interval_min",30)
        zone     = schema.get("intensiteit","Z2 — Duurtraining")
        reden      = schema.get("reden","")
        tip        = schema.get("tip","")
        alternatief= schema.get("alternatief","")
        duur_min   = schema.get("duur_min","90-120")
        pct      = round((kh_tot/max(target_kh,1))*100)
        prog     = schema.get("progressie","")
        prog_kl  = "#22c55e" if prog=="omhoog" else ("#ef4444" if prog=="omlaag" else "#fbbf24")

        if porties > 1:
            tijden = " → ".join([f"+{interval*i}min" for i in range(1,porties+1)])
            interval_txt = f"Elke {interval} min — altijd met 150-200ml water"
        else:
            tijden = f"+{interval}min na start"
            interval_txt = "Altijd innemen met 150-200ml water"

        basis_html = ""
        if basis_prod:
            bp = basis_prod["naam"]
            basis_html = (f'<div style="font-size:0.75rem;color:#3b82f6;margin-bottom:6px;">'
                          f'🔵 Basis: {bp} — {kh_basis}g/uur (vast)</div>')

        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0f172a,#1e1a2e);'
            f'border:2px solid #8b5cf6;border-radius:14px;padding:20px;margin-bottom:16px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
            f'<div style="font-size:0.65rem;font-weight:700;color:#8b5cf6;letter-spacing:2px;">'
            f'📋 WEEKPLAN — WEEK {volgende_wn}</div>'
            f'<div style="font-size:0.72rem;font-weight:700;color:{prog_kl};">▶ {prog}</div>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;">'
            f'<div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">'
            f'<div style="font-size:1.5rem;font-weight:800;color:#8b5cf6;">{kh_tot}g</div>'
            f'<div style="font-size:11px;color:#64748b;">KH/uur totaal</div>'
            f'<div style="font-size:10px;color:#475569;">{pct}% van target</div></div>'
            f'<div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">'
            f'<div style="font-size:1.5rem;font-weight:800;color:#f97316;">{porties}x</div>'
            f'<div style="font-size:11px;color:#64748b;">{pnaam}</div>'
            f'<div style="font-size:10px;color:#475569;">{kh_test}g KH test</div></div>'
            f'<div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">'
            f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">{zone.split(" — ")[0]}</div>'
            f'<div style="font-size:11px;color:#64748b;">{zone.split(" — ")[1] if " — " in zone else zone}</div>'
            f'</div></div>'
            f'{basis_html}'
            f'<div style="background:#0f172a;border-radius:8px;padding:10px;margin-bottom:10px;">'
            f'<div style="font-size:10px;color:#64748b;margin-bottom:4px;">INNAMETIJDSTIPPEN</div>'
            f'<div style="font-size:0.85rem;font-weight:700;color:#f8fafc;">📍 {tijden}</div>'
            f'<div style="font-size:0.72rem;color:#64748b;margin-top:2px;">{interval_txt}</div>'
            f'</div>'
            f'{"<div style=\\'background:#1a0a0a;border-left:3px solid #ef4444;border-radius:0 6px 6px 0;padding:8px 12px;margin-top:6px;font-size:0.78rem;color:#ef4444;\\'><b style=\\'color:#f8fafc;\\'>⚠️ Alternatief:</b> " + alternatief + "</div>" if alternatief else ""}'
            f'</div>',
            unsafe_allow_html=True)

        if st.button(f"📝 Week {volgende_wn} invullen →",
                      key="goto_logboek", use_container_width=True):
                st.session_state["tg_actieve_week"] = volgende_wn
                st.session_state["tg_actieve_fase"] = actieve_fase_naam
                st.session_state["tg_huidig_schema"] = schema
                st.session_state.tg_stap = 5
                st.rerun()

    c_terug, c_rapport = st.columns(2)
    with c_terug:
        if st.button("← Terug", key="tg_schema_back"):
            st.session_state.tg_stap = 3
            st.rerun()
    with c_rapport:
        if st.button("📊 Rapport →", key="tg_schema_rapport", use_container_width=True):
            st.session_state.tg_stap = 6
            st.rerun()


def _stap_logboek():
    """Dagboek — toont het AI-gegenereerde schema en vraagt om score."""
    _sectie("DAGBOEK")
    data  = st.session_state.get("tg_data",{})
    logs  = st.session_state.get("tg_logs",{})

    actieve_week  = st.session_state.get("tg_actieve_week", _volgende_week_nr(logs))
    actieve_fase  = st.session_state.get("tg_actieve_fase","")
    schema        = st.session_state.get("tg_huidig_schema",{})
    log           = logs.get(str(actieve_week),{})

    producten  = [p for p in data.get("producten",[]) if p.get("naam")]
    basis_prod = next((p for p in producten if p.get("rol")=="Basis"), None)
    basis_kh   = basis_prod["kh"] if basis_prod else 0
    target_kh  = int(data.get("target_kh",60))

    pnaam   = schema.get("product","—")
    porties = schema.get("porties",1)
    kh_pp   = next((p["kh"] for p in producten if p["naam"]==pnaam), 0)
    kh_tot  = schema.get("kh_totaal", basis_kh + porties*kh_pp)
    interval= schema.get("interval_min",30)
    zone    = schema.get("intensiteit","Z2 — Duurtraining")
    pct     = round((kh_tot/max(target_kh,1))*100)

    basis_naam_h = basis_prod["naam"] if basis_prod else ""
    basis_extra  = f"+ {basis_naam_h} {basis_kh}g basis" if basis_prod else ""

    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #8b5cf6;border-radius:10px;'
        f'padding:14px;margin-bottom:16px;">'
        f'<div style="font-size:0.65rem;color:#8b5cf6;letter-spacing:2px;margin-bottom:6px;">'
        f'📋 SCHEMA — WEEK {actieve_week} — {actieve_fase.upper()}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div>'
        f'<div style="font-weight:800;color:#f8fafc;font-size:1rem;">{pnaam}</div>'
        f'<div style="font-size:0.78rem;color:#64748b;">'
        f'{porties}x {kh_pp}g {basis_extra} = {kh_tot}g/uur | {zone}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:1.4rem;font-weight:800;color:#f97316;">{kh_tot}g/uur</div>'
        f'<div style="font-size:10px;color:#64748b;">{pct}% van target</div>'
        f'</div></div></div>',
        unsafe_allow_html=True)

    if schema.get("tip"):
        st.markdown(
            f'<div style="background:#0a1628;border-left:3px solid #f97316;'
            f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:8px;'
            f'font-size:0.8rem;color:#94a3b8;">'
            f'💡 <b style="color:#f8fafc;">Tip:</b> {schema["tip"]}</div>',
            unsafe_allow_html=True)
    if schema.get("alternatief"):
        st.markdown(
            f'<div style="background:#1a0a0a;border-left:3px solid #ef4444;'
            f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:14px;'
            f'font-size:0.8rem;color:#ef4444;">'
            f'⚠️ <b style="color:#f8fafc;">Alternatief voorstel:</b> {schema["alternatief"]}</div>',
            unsafe_allow_html=True)

    duur_schema = schema.get("duur_min","90-120")
    st.markdown(
        f'<div style="font-size:0.82rem;color:#94a3b8;margin-bottom:14px;">'
        f'Voer deze training uit van <b style="color:#f8fafc;">{duur_schema} minuten</b> '
        f'op <b style="color:#f8fafc;">{schema.get("intensiteit","Z2")}</b>. '
        f'Vul daarna hieronder in hoe het verliep.</div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        score = st.slider("Verdraagbaarheid (1=slecht — 5=uitstekend)",
                           1, 5, int(log.get("score",3)), key=f"tg_score_{actieve_week}")
        st.markdown(
            f'<div style="font-size:0.8rem;color:{_score_kleur(score)};font-weight:700;">'
            f'{_score_label(score)}</div>', unsafe_allow_html=True)
    with c2:
        symptoom = st.selectbox("Symptomen", SYMPTOMEN,
                                 index=SYMPTOMEN.index(log.get("symptoom","Geen klachten")),
                                 key=f"tg_symp_{actieve_week}")

    int_uitg = st.selectbox("Werkelijk uitgevoerde intensiteit", INTENSITEITEN,
                             index=INTENSITEITEN.index(log.get("int_uitg","Z2 — Duurtraining"))
                             if log.get("int_uitg") in INTENSITEITEN else 1,
                             key=f"tg_int_{actieve_week}")

    c3, c4 = st.columns(2)
    with c3:
        temp_log = st.number_input("Temperatuur (°C)", -5, 45,
                                    int(log.get("temp",18)), 1, key=f"tg_temp_{actieve_week}")
    with c4:
        timing_ok = st.radio("Innamen op geplande tijdstip?",
                              ["Ja","Gedeeltelijk","Neen"],
                              index=["Ja","Gedeeltelijk","Neen"].index(log.get("timing_ok","Ja")),
                              key=f"tg_timing_{actieve_week}", horizontal=True)

    notitie = st.text_area("Notities", value=log.get("notitie",""),
                            key=f"tg_notitie_{actieve_week}", height=80,
                            placeholder="Hoe smaakte het? Klachten op welk moment?")

    if st.button(f"✅ Opslaan week {actieve_week}", key=f"tg_save_{actieve_week}",
                  use_container_width=True):
        if "tg_logs" not in st.session_state:
            st.session_state.tg_logs = {}
        st.session_state.tg_logs[str(actieve_week)] = {
            "score":score,"symptoom":symptoom,"int_uitg":int_uitg,
            "temp":temp_log,"timing_ok":timing_ok,"notitie":notitie,
            "fase":actieve_fase,
            "product":pnaam,"kh_pp":kh_pp,"porties":porties,"kh_doel":kh_tot,
            "progressie":schema.get("progressie",""),
            "intensiteit":schema.get("intensiteit","Z2 - Duurtraining"),
            "ingevuld":True,
        }
        # Wis cache zodat schema volgende week herberekend wordt
        volgende_wn = actieve_week+1
        cache_key = f"tg_schema_week_{volgende_wn}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]

        st.success(f"✅ Week {actieve_week} opgeslagen!")
        st.session_state["tg_actieve_week"] = volgende_wn
        st.session_state.tg_stap = 4
        st.rerun()

    c_terug, c_rapport = st.columns(2)
    with c_terug:
        if st.button("← Schema", key="tg_log_back"):
            st.session_state.tg_stap = 4
            st.rerun()
    with c_rapport:
        if st.button("📊 Rapport →", key="tg_log_rapport", use_container_width=True):
            st.session_state.tg_stap = 6
            st.rerun()


def _stap_rapport():
    _sectie("TESTRAPPORT — TRAIN THE GUT")
    data  = st.session_state.get("tg_data",{})
    logs  = st.session_state.get("tg_logs",{})
    sport = data.get("sport","Fietsen")
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])

    ingevuld = [v for v in logs.values() if v.get("ingevuld")]
    if not ingevuld:
        st.warning("Nog geen trainingen gelogd.")
        if st.button("← Naar schema", key="tg_rep_back2"):
            st.session_state.tg_stap = 4
            st.rerun()
        return

    gem_score = sum(v["score"] for v in ingevuld)/len(ingevuld)
    max_kh    = max(v.get("kh_doel",0) for v in ingevuld)
    n_klacht  = sum(1 for v in ingevuld if v.get("symptoom","Geen klachten")!="Geen klachten")

    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;'
        f'padding:18px;margin-bottom:18px;">'
        f'<div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:12px;">'
        f'SAMENVATTING — {sport.upper()}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">'
        f'<div style="text-align:center;">'
        f'<div style="font-size:1.6rem;font-weight:800;color:#f97316;">{len(ingevuld)}</div>'
        f'<div style="font-size:11px;color:#64748b;">trainingen</div></div>'
        f'<div style="text-align:center;">'
        f'<div style="font-size:1.6rem;font-weight:800;color:{_score_kleur(gem_score)};">'
        f'{gem_score:.1f}/5</div>'
        f'<div style="font-size:11px;color:#64748b;">gem. score</div></div>'
        f'<div style="text-align:center;">'
        f'<div style="font-size:1.6rem;font-weight:800;color:#22c55e;">{max_kh}g</div>'
        f'<div style="font-size:11px;color:#64748b;">max KH/uur</div></div>'
        f'<div style="text-align:center;">'
        f'<div style="font-size:1.6rem;font-weight:800;'
        f'color:{"#22c55e" if n_klacht==0 else "#fbbf24"}">{n_klacht}</div>'
        f'<div style="font-size:11px;color:#64748b;">weken klachten</div></div>'
        f'</div></div>',
        unsafe_allow_html=True)

    for fase in fases:
        fn        = fase["naam"]
        fase_logs = [v for v in ingevuld if v.get("fase")==fn]
        if not fase_logs: continue
        stabiel   = _is_fase_stabiel(logs, fn, int(data.get("target_kh",0)))
        _sectie(f"{fase['icon']} {fn.upper()}", "#22c55e" if stabiel else "#f97316")

        prod_data = {}
        for v in fase_logs:
            prod = v.get("product","—")
            if prod not in prod_data:
                prod_data[prod] = {"scores":[],"symptomen":[],"kh_max":0,"porties_max":0}
            prod_data[prod]["scores"].append(v["score"])
            prod_data[prod]["symptomen"].append(v.get("symptoom","Geen klachten"))
            prod_data[prod]["kh_max"]      = max(prod_data[prod]["kh_max"],v.get("kh_doel",0))
            prod_data[prod]["porties_max"] = max(prod_data[prod]["porties_max"],v.get("porties",0))

        aanbevolen = []
        for prod, pd in prod_data.items():
            gem  = sum(pd["scores"])/len(pd["scores"])
            ok   = gem >= 4.0
            kl   = _score_kleur(gem)
            symp = max(set(pd["symptomen"]),key=pd["symptomen"].count)
            if ok: aanbevolen.append(prod)

            st.markdown(
                f'<div style="background:#0f172a;border:2px solid {"#22c55e" if ok else "#ef4444"};'
                f'border-radius:10px;padding:12px;margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<div><div style="font-weight:800;color:#f8fafc;">{prod}</div>'
                f'<div style="font-size:11px;color:#64748b;">'
                f'max {pd["porties_max"]}x · {pd["kh_max"]}g/uur</div></div>'
                f'<div style="text-align:right;">'
                f'<div style="font-size:1.2rem;font-weight:800;color:{kl};">{gem:.1f}/5</div>'
                f'<div style="font-size:10px;color:{"#22c55e" if ok else "#ef4444"};">'
                f'{"✅ Aanbevolen" if ok else "❌ Vermijden"}</div></div></div>'
                f'<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">'
                f'Symptoom: {symp}</div></div>',
                unsafe_allow_html=True)

        if stabiel and aanbevolen:
            st.markdown(
                f'<div style="background:#0a1a0a;border:1px solid #22c55e;border-radius:8px;'
                f'padding:10px;margin-bottom:8px;font-size:0.8rem;color:#22c55e;">'
                f'✅ <b>{fn} stabiel</b> — aanbevolen: <b>{", ".join(aanbevolen)}</b></div>',
                unsafe_allow_html=True)

    _sectie("AANBEVELING VOOR RACEDAG","#22c55e")
    alle_ok = list({v.get("product") for v in ingevuld
                    if (sum(x["score"] for x in ingevuld if x.get("product")==v.get("product"))/
                        max(sum(1 for x in ingevuld if x.get("product")==v.get("product")),1))>=4.0})
    if alle_ok:
        st.success(f"✅ Goedgekeurde producten: **{', '.join(alle_ok)}**")
        st.markdown(
            f'<div style="background:#0f172a;border:1px solid #22c55e;border-radius:8px;'
            f'padding:14px;font-size:0.82rem;color:#94a3b8;line-height:1.7;margin-top:8px;">'
            f'Maag verdraagt <b style="color:#22c55e;">{max_kh}g KH/uur</b>.<br>'
            f'Gebruik <b style="color:#f8fafc;">enkel geteste producten</b> op racedag.<br><br>'
            f'🏁 Integreer in <b style="color:#f97316;">Race Nutrition Coach</b>.</div>',
            unsafe_allow_html=True)
    else:
        st.warning("Nog geen producten met score ≥ 4. Ga verder met testen.")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Terug", key="tg_rep_back"):
            st.session_state.tg_stap = 4
            st.rerun()
    with c2:
        if st.button("🔄 Nieuw schema", key="tg_nieuw", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("tg_"):
                    del st.session_state[k]
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# HOOFDFUNCTIE
# ═══════════════════════════════════════════════════════════════════════════════

def render_testing(user: dict):
    st.markdown(
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">'
        '<div style="font-size:2rem;font-weight:900;letter-spacing:3px;color:#f8fafc;">'
        'CAR<span style="color:#f97316;">BOO</span></div>'
        '<div style="font-size:0.85rem;font-weight:700;color:#8b5cf6;letter-spacing:2px;'
        'border:1px solid #8b5cf6;border-radius:6px;padding:3px 10px;">TRAIN THE GUT</div>'
        '</div>',
        unsafe_allow_html=True)



    stap  = st.session_state.get("tg_stap",1)
    namen = ["← Modules","Intro","Profiel","Producten","Schema","Dagboek","Rapport"]
    cols  = st.columns(len(namen))
    for i, (col, naam) in enumerate(zip(cols, namen)):
        actief = (i) == stap and i > 0
        gedaan = i > 0 and i < stap
        with col:
            if st.button(
                f'{"✓ " if gedaan else ""}{naam}',
                key=f"tg_nav_{i}",
                use_container_width=True,
                type="primary" if actief else "secondary"
            ):
                if i == 0:
                    st.session_state.module = "menu"
                else:
                    st.session_state["tg_stap"] = i
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if   stap==1: _stap_intro(); st.markdown("<br>",unsafe_allow_html=True); \
        st.button("Start Train the Gut →",key="tg_start",use_container_width=True) and \
        (st.session_state.update({"tg_stap":2}) or st.rerun())
    elif stap==2: _stap_profiel()
    elif stap==3: _stap_producten()
    elif stap==4: _stap_schema()
    elif stap==5: _stap_logboek()
    elif stap==6: _stap_rapport()
