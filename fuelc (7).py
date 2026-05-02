import streamlit as st
from datetime import date, timedelta
from supabase import create_client


# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE CONNECTIE — zelfde aanpak als login.py
# ═══════════════════════════════════════════════════════════════════════════════

def _get_secrets(key: str, default: str = "") -> str:
    import os
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        return st.secrets[key]
    except:
        return default


@st.cache_resource
def _get_supabase_client():
    """Gecachede Supabase client — één connectie per server instantie."""
    url = _get_secrets("SUPABASE_URL")
    key = _get_secrets("SUPABASE_KEY")
    return create_client(url, key)

def _get_supabase():
    return _get_supabase_client()


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTEN
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVITEIT_FACTOR = {
    "Zittend (kantoorwerk, weinig beweging)":  1.2,
    "Licht actief (wandelen, staand werk)":    1.375,
    "Matig actief (lichamelijk werk)":         1.55,
}

DOELSTELLING_OPTIES = [
    "Gewicht houden",
    "Gewicht verliezen — 0.25 kg/week",
    "Gewicht verliezen — 0.5 kg/week",
    "Gewicht verliezen — 0.75 kg/week",
    "Gewicht aankomen — 0.25 kg/week",
    "Gewicht aankomen — 0.5 kg/week",
    "Prestatie (geen gewichtsdoel)",
]

DOELSTELLING_KCAL = {
    "Gewicht houden":                      0,
    "Gewicht verliezen — 0.25 kg/week": -275,
    "Gewicht verliezen — 0.5 kg/week":  -550,
    "Gewicht verliezen — 0.75 kg/week": -825,
    "Gewicht aankomen — 0.25 kg/week":  +275,
    "Gewicht aankomen — 0.5 kg/week":   +550,
    "Prestatie (geen gewichtsdoel)":        0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# BEREKENINGEN
# ═══════════════════════════════════════════════════════════════════════════════

def _bereken_bmr(geslacht: str, gewicht: float, lengte: int, leeftijd: int) -> int:
    """Mifflin-St Jeor formule."""
    if geslacht == "Man":
        bmr = 10 * gewicht + 6.25 * lengte - 5 * leeftijd + 5
    else:
        bmr = 10 * gewicht + 6.25 * lengte - 5 * leeftijd - 161
    return round(bmr)


def _bereken_tdee(bmr: int, activiteit: str) -> int:
    factor = ACTIVITEIT_FACTOR.get(activiteit, 1.2)
    return round(bmr * factor)


def _bereken_energie_doel(tdee: int, doelstelling: str) -> int:
    delta = DOELSTELLING_KCAL.get(doelstelling, 0)
    return tdee + delta


def _bereken_macros(energie_doel: int, kh_pct: int, eiwit_pct: int, vet_pct: int) -> dict:
    """Bereken macros in gram op basis van percentages."""
    return {
        "kh_g":    round(energie_doel * kh_pct    / 100 / 4),  # 4 kcal/g
        "eiwit_g": round(energie_doel * eiwit_pct / 100 / 4),  # 4 kcal/g
        "vet_g":   round(energie_doel * vet_pct   / 100 / 9),  # 9 kcal/g
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE — PROFIEL OPSLAAN / LADEN
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def _laad_profiel(user_id: str) -> dict:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_profiel").select("*").eq("user_id", user_id).execute()
        return r.data[0] if r.data else {}
    except Exception as e:
        print(f"Fout bij laden profiel: {e}")
        return {}


def _sla_profiel_op(user_id: str, profiel: dict) -> bool:
    try:
        sb       = _get_supabase()
        bestaand = sb.table("fuelc_profiel").select("id").eq("user_id", user_id).execute()
        if bestaand.data:
            sb.table("fuelc_profiel").update(profiel).eq("user_id", user_id).execute()
        else:
            profiel["user_id"] = user_id
            sb.table("fuelc_profiel").insert(profiel).execute()
        _laad_profiel.clear()
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan profiel: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# HULPFUNCTIES UI
# ═══════════════════════════════════════════════════════════════════════════════

def _sectie(titel: str, kleur: str = "#22c55e"):
    st.markdown(
        f'<div style="font-size:0.72rem;font-weight:700;color:{kleur};'
        f'letter-spacing:2px;margin:18px 0 8px;padding-bottom:4px;'
        f'border-bottom:1px solid #1e293b;">{titel}</div>',
        unsafe_allow_html=True)


def _metric_card(label: str, waarde: str, eenheid: str = "",
                 kleur: str = "#f97316", sub: str = ""):
    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;'
        f'padding:14px;text-align:center;">'
        f'<div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:6px;">'
        f'{label}</div>'
        f'<div style="font-size:1.8rem;font-weight:800;color:{kleur};">{waarde}</div>'
        f'<div style="font-size:0.75rem;color:#64748b;">{eenheid}</div>'
        f'{"<div style=\'font-size:0.7rem;color:#475569;margin-top:4px;\'>" + sub + "</div>" if sub else ""}'
        f'</div>',
        unsafe_allow_html=True)


def _macro_balk(label: str, gram: int, pct: int, kleur: str):
    st.markdown(
        f'<div style="margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:0.78rem;margin-bottom:4px;">'
        f'<span style="color:#f8fafc;font-weight:600;">{label}</span>'
        f'<span style="color:{kleur};font-weight:700;">{gram}g &nbsp;·&nbsp; {pct}%</span>'
        f'</div>'
        f'<div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;background:{kleur};border-radius:4px;"></div>'
        f'</div></div>',
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STAP — PROFIEL & TDEE
# ═══════════════════════════════════════════════════════════════════════════════

def _stap_profiel(user: dict):
    user_id = user.get("id","")

    # Laad bestaand profiel uit Supabase of session state
    if "fc_profiel" not in st.session_state:
        st.session_state.fc_profiel = _laad_profiel(user_id)
    p = st.session_state.fc_profiel

    # ── BLOK 1: Basisgegevens ─────────────────────────────────────────────────
    _sectie("BASISGEGEVENS")
    c1, c2, c3 = st.columns(3)
    with c1:
        geslacht = st.radio("Geslacht", ["Man","Vrouw"],
                             index=["Man","Vrouw"].index(p.get("geslacht","Man")),
                             key="fc_geslacht", horizontal=True)
    with c2:
        leeftijd = st.number_input("Leeftijd", 16, 80,
                                    int(p.get("leeftijd", 30)), 1, key="fc_leeftijd")
    with c3:
        gewicht = st.number_input("Gewicht (kg)", 30.0, 200.0,
                                   float(p.get("gewicht_kg", 70.0)), 0.5,
                                   key="fc_gewicht")

    c4, c5 = st.columns(2)
    with c4:
        lengte = st.number_input("Lengte (cm)", 140, 220,
                                  int(p.get("lengte_cm", 175)), 1, key="fc_lengte")
    with c5:
        activiteit = st.selectbox(
            "Activiteitsniveau buiten sport",
            list(ACTIVITEIT_FACTOR.keys()),
            index=list(ACTIVITEIT_FACTOR.keys()).index(
                p.get("activiteit", list(ACTIVITEIT_FACTOR.keys())[0]))
            if p.get("activiteit") in ACTIVITEIT_FACTOR else 0,
            key="fc_activiteit")

    # ── BLOK 2: Doelstelling ──────────────────────────────────────────────────
    _sectie("DOELSTELLING")
    doelstelling = st.radio(
        "Wat is je voedingsdoel?",
        DOELSTELLING_OPTIES,
        index=DOELSTELLING_OPTIES.index(p.get("doelstelling", "Gewicht houden"))
        if p.get("doelstelling") in DOELSTELLING_OPTIES else 0,
        key="fc_doelstelling")

    # ── BLOK 3: Macro verdeling ───────────────────────────────────────────────
    _sectie("MACRO VERDELING")
    st.markdown(
        '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:10px;">'
        'Standaard verdeling voor sporters — pas aan naar voorkeur. '
        'Totaal moet 100% zijn.</div>',
        unsafe_allow_html=True)

    c6, c7, c8 = st.columns(3)
    with c6:
        kh_pct = st.number_input("Koolhydraten %", 20, 70,
                                   int(p.get("kh_doel_pct", 50)), 5, key="fc_kh_pct")
    with c7:
        eiwit_pct = st.number_input("Eiwit %", 10, 40,
                                     int(p.get("eiwit_doel_pct", 25)), 5, key="fc_eiwit_pct")
    with c8:
        vet_pct = st.number_input("Vet %", 10, 40,
                                   int(p.get("vet_doel_pct", 25)), 5, key="fc_vet_pct")

    totaal_pct = kh_pct + eiwit_pct + vet_pct
    if totaal_pct != 100:
        st.markdown(
            f'<div style="background:#1a0a0a;border-left:3px solid #ef4444;'
            f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#ef4444;">'
            f'⚠️ Totaal is {totaal_pct}% — moet 100% zijn.</div>',
            unsafe_allow_html=True)

    # ── Live berekening ───────────────────────────────────────────────────────
    bmr          = _bereken_bmr(geslacht, gewicht, lengte, leeftijd)
    tdee         = _bereken_tdee(bmr, activiteit)
    energie_doel = _bereken_energie_doel(tdee, doelstelling)
    macros       = _bereken_macros(energie_doel, kh_pct, eiwit_pct, vet_pct)

    _sectie("JOUW ENERGIEPROFIEL", "#22c55e")

    c9, c10, c11 = st.columns(3)
    with c9:
        _metric_card("BASISMETABOLISME", str(bmr), "kcal/dag",
                     "#4ade80", "BMR — Mifflin-St Jeor")
    with c10:
        _metric_card("TDEE BASIS", str(tdee), "kcal/dag",
                     "#22c55e", "Zonder sport")
    with c11:
        delta      = DOELSTELLING_KCAL.get(doelstelling, 0)
        delta_txt  = (f"+{delta}" if delta > 0 else str(delta)) if delta != 0 else "±0"
        doel_kleur = "#22c55e" if delta >= 0 else "#ef4444"
        _metric_card("ENERGIE DOEL", str(energie_doel), "kcal/dag",
                     doel_kleur, f"TDEE {delta_txt} kcal")

    # Macro balken
    st.markdown("<br>", unsafe_allow_html=True)
    _sectie("MACRO DOELEN PER DAG")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        _macro_balk("Koolhydraten", macros["kh_g"],    kh_pct,    "#22c55e")
        _macro_balk("Eiwit",        macros["eiwit_g"], eiwit_pct, "#16a34a")
    with col_m2:
        _macro_balk("Vet",          macros["vet_g"],   vet_pct,   "#86efac")
        st.markdown(
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;'
            f'padding:10px 14px;font-size:0.8rem;color:#94a3b8;margin-top:4px;">'
            f'💡 Sport verhoogt je dagelijkse behoefte. '
            f'FuelC past dit automatisch aan op basis van je trainingen.</div>',
            unsafe_allow_html=True)

    # ── Maaltijdmomenten instelling ──────────────────────────────────────────
    _sectie("EETPATROON & MAALTIJDMOMENTEN")
    st.markdown(
        '<div style="font-size:0.78rem;color:#64748b;margin-bottom:12px;">' +
        'Stel je eetpatroon in en pas de tijdstippen aan. Wordt toegepast op het weekschema.</div>',
        unsafe_allow_html=True)

    ep1, ep2 = st.columns(2)
    with ep1:
        patroon_keuze = st.selectbox("Eetpatroon",
            ["Klassiek (3 maaltijden)","Intermittent 16:8","Intermittent 18:6"],
            index=["Klassiek (3 maaltijden)","Intermittent 16:8","Intermittent 18:6"].index(
                p.get("eet_patroon","Klassiek (3 maaltijden)"))
            if p.get("eet_patroon") in ["Klassiek (3 maaltijden)","Intermittent 16:8","Intermittent 18:6"] else 0,
            key="prof_patroon")

    MAALTIJD_DEFAULTS = {
        "Klassiek (3 maaltijden)": [
            {"naam":"Ontbijt","tijdstip":"07:30","type":"ontbijt"},
            {"naam":"Lunch","tijdstip":"12:30","type":"lunch"},
            {"naam":"Avondmaal","tijdstip":"18:30","type":"avond"},
        ],
        "Intermittent 16:8": [
            {"naam":"Eerste maaltijd","tijdstip":"12:00","type":"ontbijt"},
            {"naam":"Tweede maaltijd","tijdstip":"16:00","type":"lunch"},
            {"naam":"Derde maaltijd","tijdstip":"19:30","type":"avond"},
        ],
        "Intermittent 18:6": [
            {"naam":"Eerste maaltijd","tijdstip":"13:00","type":"ontbijt"},
            {"naam":"Tweede maaltijd","tijdstip":"18:30","type":"avond"},
        ],
    }

    with ep2:
        if patroon_keuze == "Klassiek (3 maaltijden)":
            st.markdown('<div style="font-size:0.72rem;color:#64748b;padding-top:28px;">Tussendoor momenten:</div>', unsafe_allow_html=True)

    # Tussendoor (enkel bij klassiek)
    tussendoor_aan = []
    if patroon_keuze == "Klassiek (3 maaltijden)":
        td_cols = st.columns(3)
        td_namen = ["Tussendoor voormiddag","Tussendoor namiddag","Avondsnack"]
        td_tijden = ["10:00","15:00","21:00"]
        for ti in range(3):
            with td_cols[ti]:
                if st.checkbox(td_namen[ti], key=f"prof_td_{ti}",
                    value=bool(p.get(f"td_{ti}", False))):
                    tussendoor_aan.append(ti)

    # Tijdstippen aanpassen
    import json as _json_prof
    momenten_prof = MAALTIJD_DEFAULTS.get(patroon_keuze, MAALTIJD_DEFAULTS["Klassiek (3 maaltijden)"])
    opgeslagen_mom = p.get("momenten_tijden")
    if opgeslagen_mom:
        try: opgeslagen_mom = _json_prof.loads(opgeslagen_mom) if isinstance(opgeslagen_mom, str) else opgeslagen_mom
        except: opgeslagen_mom = None

    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin:10px 0 6px;">Tijdstippen aanpassen:</div>', unsafe_allow_html=True)
    tijd_cols = st.columns(len(momenten_prof))
    nieuwe_tijden = {}
    for i, m in enumerate(momenten_prof):
        with tijd_cols[i]:
            huidig = (opgeslagen_mom or {}).get(str(i), m["tijdstip"]) if opgeslagen_mom else m["tijdstip"]
            nieuwe_tijden[str(i)] = st.text_input(
                m["naam"], value=huidig,
                key=f"prof_tijd_{i}", placeholder="HH:MM")

    if patroon_keuze == "Klassiek (3 maaltijden)":
        td_cols2 = st.columns(3)
        for ti in tussendoor_aan:
            with td_cols2[ti]:
                huidig_td = (opgeslagen_mom or {}).get(f"td_{ti}", td_tijden[ti])
                nieuwe_tijden[f"td_{ti}"] = st.text_input(
                    td_namen[ti], value=huidig_td,
                    key=f"prof_tdtijd_{ti}", placeholder="HH:MM")

    # ── Opslaan ───────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<style>[data-testid="stButton"] button[kind="primary"],'
        '.fc-groen button{background:#22c55e!important;color:#0a0f1e!important;'
        'font-weight:800!important;}</style>',
        unsafe_allow_html=True)
    if totaal_pct != 100:
        st.markdown(
            f'<div style="background:#1a0a0a;border-left:3px solid #fbbf24;border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#fbbf24;margin-bottom:8px;">' +
            f'⚠️ Macro verdeling is {totaal_pct}% — aanbeveling is 100%. Je kan toch opslaan.</div>',
            unsafe_allow_html=True)

    c_ops, c_vol = st.columns(2)
    with c_ops:
        opslaan_klik = st.button("💾 Opslaan", key="fc_prof_opslaan",
                     use_container_width=True)
    with c_vol:
        if st.session_state.fc_profiel.get("bmr"):
            if st.button("Volgende →", key="fc_prof_volgende",
                         use_container_width=True):
                st.session_state.fc_stap = 2
                st.rerun()
    if opslaan_klik:
            import json as _json_save
            profiel_data = {
                "geslacht":       geslacht,
                "leeftijd":       leeftijd,
                "gewicht_kg":     gewicht,
                "lengte_cm":      lengte,
                "activiteit":     activiteit,
                "doelstelling":   doelstelling,
                "doel_tempo":     abs(DOELSTELLING_KCAL.get(doelstelling, 0)) / 1100,
                "bmr":            bmr,
                "tdee_basis":     tdee,
                "energie_doel":   energie_doel,
                "kh_doel_pct":    kh_pct,
                "eiwit_doel_pct": eiwit_pct,
                "vet_doel_pct":   vet_pct,
                "eet_patroon":    st.session_state.get("prof_patroon","Klassiek (3 maaltijden)"),
                "momenten_tijden":_json_save.dumps({
                    str(i): st.session_state.get(f"prof_tijd_{i}", "") for i in range(6)
                }),
                "td_0": 0 in [ti for ti in range(3) if st.session_state.get(f"prof_td_{ti}")],
                "td_1": 1 in [ti for ti in range(3) if st.session_state.get(f"prof_td_{ti}")],
                "td_2": 2 in [ti for ti in range(3) if st.session_state.get(f"prof_td_{ti}")],
            }
            if _sla_profiel_op(user_id, profiel_data):
                st.session_state.fc_profiel = profiel_data
                st.success("✅ Profiel opgeslagen!")
                st.rerun()



# ═══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDERS ANDERE BLOKKEN
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 2 — TRAININGEN (MANUELE INVOER)
# ═══════════════════════════════════════════════════════════════════════════════

SPORT_OPTIES = ["Lopen", "Fietsen", "Zwemmen", "Roeien", "Crosstrainer", "Indoor lopen", "Kracht", "Andere"]

ZONE_LABELS = [
    "Z1 — Herstel",
    "Z2 — Duurzaam",
    "Z3 — Tempo",
    "Z4 — Drempel",
    "Z5 — VO2max",
]

ZONE_MET = {
    "Z1 — Herstel":    4.0,
    "Z2 — Duurzaam":   6.0,
    "Z3 — Tempo":      8.5,
    "Z4 — Drempel":   10.5,
    "Z5 — VO2max":    13.0,
}

# MET per sport voor nauwkeurigere kcal berekening
SPORT_MET_FACTOR = {
    "Lopen":          {"Z1":6.0,"Z2":8.5,"Z3":11.0,"Z4":13.0,"Z5":16.0},
    "Fietsen":        {"Z1":4.0,"Z2":6.0,"Z3":8.0,"Z4":10.0,"Z5":12.0},
    "Zwemmen":        {"Z1":5.0,"Z2":7.0,"Z3":9.0,"Z4":11.0,"Z5":13.0},
    "Roeien":         {"Z1":4.5,"Z2":7.0,"Z3":9.5,"Z4":11.5,"Z5":14.0},
    "Crosstrainer":   {"Z1":4.0,"Z2":6.0,"Z3":8.0,"Z4":10.0,"Z5":12.0},
    "Indoor lopen":   {"Z1":6.0,"Z2":8.5,"Z3":11.0,"Z4":13.0,"Z5":16.0},
    "Kracht":         {"Z1":3.5,"Z2":5.0,"Z3":6.0,"Z4":7.0,"Z5":8.0},
    "Andere":         {"Z1":4.0,"Z2":6.0,"Z3":8.5,"Z4":10.5,"Z5":13.0},
}

def _bereken_kcal(gewicht_kg: float, minuten: float, zone: str, sport: str = "") -> int:
    """MET-gebaseerde kcalberekening per sport."""
    z_key = zone[:2].upper() if zone else "Z2"
    sport_mets = SPORT_MET_FACTOR.get(sport, SPORT_MET_FACTOR["Andere"])
    met = sport_mets.get(z_key, 6.0)
    return round((met * gewicht_kg * 3.5 / 200) * minuten)

def _dominante_zone(blokken: list) -> str:
    """Blokken = lijst van (zone_label, minuten)."""
    zones = {}
    for z, m in blokken:
        key = next((k for k in ZONE_MET if z.startswith(k[:2])), z)
        zones[key] = zones.get(key, 0) + m
    return max(zones, key=zones.get) if zones else "Z2 — Duurzaam"

@st.cache_data(ttl=120)
def _laad_zones(user_id: str, sport: str) -> dict:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_zones").select("*").eq("user_id", user_id).eq("sport", sport).execute()
        return r.data[0] if r.data else {}
    except:
        return {}

def _sla_zones_op(user_id: str, sport: str, zones: dict) -> bool:
    try:
        sb = _get_supabase()
        bestaand = sb.table("fuelc_zones").select("id").eq("user_id", user_id).eq("sport", sport).execute()
        zones["user_id"] = user_id
        zones["sport"]   = sport
        if bestaand.data:
            sb.table("fuelc_zones").update(zones).eq("user_id", user_id).eq("sport", sport).execute()
        else:
            sb.table("fuelc_zones").insert(zones).execute()
        _laad_zones.clear()
        return True
    except Exception as e:
        st.error(f"Fout opslaan zones: {e}")
        return False

@st.cache_data(ttl=60)
def _laad_trainingen(user_id: str) -> list:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_trainingen").select("*").eq("user_id", user_id).order("datum", desc=True).limit(30).execute()
        return r.data or []
    except:
        return []

def _sla_training_op(user_id: str, training: dict) -> bool:
    # Toegestane kolommen in fuelc_trainingen
    KOLOMMEN = {"datum","sport","duur_min","afstand_km",
                "kcal_verbranding","zone_verdeling","notitie","bron","user_id","starttijd"}
    try:
        sb = _get_supabase()
        data = {k: v for k, v in training.items() if k in KOLOMMEN}
        # Omschrijving niet als apart veld maar als prefix in notitie
        if "omschrijving" in training and training["omschrijving"]:
            notitie_huidig = data.get("notitie","") or ""
            if training["omschrijving"] not in notitie_huidig:
                data["notitie"] = f"{training['omschrijving']} | {notitie_huidig}".strip(" | ")
        data["user_id"] = user_id
        data["bron"]    = "manueel"
        sb.table("fuelc_trainingen").insert(data).execute()
        _laad_trainingen.clear()
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan training: {e}")
        return False

def _verwijder_training(training_id: str) -> bool:
    try:
        sb = _get_supabase()
        sb.table("fuelc_trainingen").delete().eq("id", training_id).execute()
        _laad_trainingen.clear()
        return True
    except Exception as e:
        st.error(f"Fout bij verwijderen: {e}")
        return False

def _format_tempo(val: float) -> str:
    """Zet decimaal tempo om naar min:sec formaat."""
    if not val: return ""
    minuten = int(val)
    seconden = round((val - minuten) * 60)
    return f"{minuten}:{seconden:02d}"

def _zone_info(zones: dict, zone_label: str, eenheid: str, sport: str) -> str:
    """Geef tempo/hs bereik info voor een zone."""
    z_key = zone_label[:2].lower()
    if eenheid == "tempo" and sport == "Lopen":
        van = zones.get(f"{z_key}_tempo_van")
        tot = zones.get(f"{z_key}_tempo_tot")
        if van and tot:
            return f"{_format_tempo(van)} — {_format_tempo(tot)} min/km"
        elif van:
            return f"vanaf {_format_tempo(van)} min/km"
    elif eenheid == "watt":
        van = zones.get(f"{z_key}_tempo_van")
        tot = zones.get(f"{z_key}_tempo_tot")
        if van and tot: return f"{int(van)}—{int(tot)}W"
        elif van: return f"vanaf {int(van)}W"
    if eenheid in ("hartslag", None, ""):
        van = zones.get(f"{z_key}_hs_van")
        tot = zones.get(f"{z_key}_hs_tot")
        if van and tot: return f"{int(van)}—{int(tot)} bpm"
        elif van: return f"vanaf {int(van)} bpm"
    return ""

def _parse_tempo(s: str):
    """Converteer tempo string (5:30 of 5.5) naar decimaal getal."""
    if not s: return None
    s = s.strip()
    if ":" in s:
        parts = s.split(":")
        try: return int(parts[0]) + int(parts[1])/60
        except: return None
    try: return float(s)
    except: return None


def _stap_trainingen(user: dict):
    user_id = user.get("id", "")
    profiel = st.session_state.get("fc_profiel", {})
    gewicht = float(profiel.get("gewicht_kg", 70) or 70)

    _sectie("TRAININGEN", "#22c55e")

    tab_add, tab_zones, tab_lijst = st.tabs([
        "➕  Training toevoegen",
        "⚙️  Zone kalibratie",
        "📋  Mijn trainingen",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — TRAINING TOEVOEGEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_add:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ALGEMEEN", "#22c55e")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sport = st.selectbox("Sport", SPORT_OPTIES, key="tr_sport")
        with c2:
            datum = st.date_input("Datum", key="tr_datum")
        with c3:
            starttijd = st.text_input("Starttijd (HH:MM)",
                value="07:00", placeholder="07:00", key="tr_starttijd")
        with c4:
            omschrijving = st.text_input("Naam / omschrijving",
                placeholder="bijv. Lange duurloop", key="tr_naam")

        zones_data = _laad_zones(user_id, sport)
        eenheid    = zones_data.get("eenheid", "hartslag")

        # ── Invoer stijl keuze ────────────────────────────────────────────────
        invoer_stijl = st.radio("Invoer stijl",
            ["⚡ Snel (intensiteit)", "⚙️ Gedetailleerd (zones)"],
            horizontal=True, key="tr_invoer_stijl")

        # ══════════════════════════════════════════════════════════════════════
        # SNELLE INVOER
        # ══════════════════════════════════════════════════════════════════════
        if invoer_stijl == "⚡ Snel (intensiteit)":
            st.markdown("<br>", unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                if sport == "Lopen":
                    snel_km  = st.number_input("Afstand (km)", 0.0, 200.0, 10.0, 0.5, key="tr_snel_km")
                    snel_min = 0
                else:
                    snel_min = st.number_input("Duur (min)", 0, 300, 60, key="tr_snel_min")
                    snel_km  = 0.0
            with sc2:
                snel_int = st.select_slider("Intensiteit",
                    options=["Licht", "Matig", "Intensief"],
                    key="tr_snel_int")
            with sc3:
                INT_ZONE = {"Licht": "Z1 Herstel", "Matig": "Z2 Duurzaam", "Intensief": "Z4 Drempel"}
                snel_zone = INT_ZONE[snel_int]
                if sport == "Lopen" and snel_km > 0:
                    tempo = zones_data.get("z2_tempo", 6.0) if snel_int == "Matig" else \
                            zones_data.get("z1_tempo", 7.0) if snel_int == "Licht" else \
                            zones_data.get("z4_tempo", 4.5)
                    snel_min = round(snel_km * (tempo or 6.0))
                snel_kcal = _bereken_kcal(gewicht, snel_min, snel_zone, sport) if snel_min > 0 else 0
                if snel_min > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    _metric_card("KCAL", str(snel_kcal), "kcal", "#22c55e")

            snel_notitie = f"{snel_int} — {snel_zone}"
            if st.button("💾  Training opslaan", key="tr_snel_save", use_container_width=True, type="primary"):
                if snel_min > 0:
                    import json as _jsn
                    _zone_verd = {snel_zone[:2].lower(): snel_min}
                    _ok = _sla_training_op(user_id, {
                        "datum":           str(datum),
                        "sport":           sport,
                        "omschrijving":    omschrijving or snel_notitie,
                        "duur_min":        snel_min,
                        "afstand_km":      round(snel_km, 2),
                        "kcal_verbranding":snel_kcal,
                        "zone_verdeling":  _jsn.dumps(_zone_verd),
                        "notitie":         snel_notitie,
                        "starttijd":       starttijd or "07:00",
                    })
                    if not _ok:
                        st.stop()
                    st.success(f"✅ Training opgeslagen — {snel_min} min · {snel_kcal} kcal")
                    st.rerun()
                else:
                    st.error("Vul duur of afstand in.")

        # ══════════════════════════════════════════════════════════════════════
        # GEDETAILLEERDE INVOER
        # ══════════════════════════════════════════════════════════════════════
        else:
            if sport == "Lopen":
                invoer_modus = st.radio("Invoer op basis van",
                    ["Tijd (minuten)", "Afstand (km)"],
                    horizontal=True, key="tr_invoer_modus")
            else:
                invoer_modus = "Tijd (minuten)"

            def _zone_selectbox(label, key, default_idx=1):
                zone = st.selectbox(label, ZONE_LABELS, index=default_idx, key=key)
                info = _zone_info(zones_data, zone, eenheid, sport)
                if info:
                    st.markdown(
                        f'<div style="font-size:0.7rem;color:#86efac;margin-top:-8px;margin-bottom:4px;">→ {info}</div>',
                        unsafe_allow_html=True)
                return zone

            def _invoer_blok(prefix, label_min, label_km, default_min, default_km, zone_idx):
                if invoer_modus == "Afstand (km)" and sport == "Lopen":
                    km   = st.number_input(label_km, 0.0, 200.0, default_km, 0.1, key=f"{prefix}_km")
                    zone = _zone_selectbox("Intensiteitszone", f"{prefix}_zone", zone_idx)
                    tempo = zones_data.get(f"{zone[:2].lower()}_tempo")
                    minuten = round(km * tempo) if tempo and tempo > 0 and km > 0 else round(km * 6) if km > 0 else 0
                    return minuten, km, zone
                else:
                    minuten = st.number_input(label_min, 0, 300, default_min, key=f"{prefix}_min")
                    zone    = _zone_selectbox("Intensiteitszone", f"{prefix}_zone", zone_idx)
                    return minuten, 0.0, zone

            _sectie("OPWARMING", "#22c55e")
            ow1, ow2 = st.columns(2)
            with ow1:
                opw_min, opw_km, opw_zone = _invoer_blok("tr_opw","Duur (min)","Afstand (km)",10,2.0,0)
            with ow2:
                opw_kcal = _bereken_kcal(gewicht, opw_min, opw_zone, sport) if opw_min > 0 else 0
                if opw_min > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    _metric_card("KCAL", str(opw_kcal), "kcal", "#22c55e")

            _sectie("KERN", "#22c55e")
            kern_type = st.radio("Type kern",
                ["Doorlopend","Intervalblokken","Ramp up","Ramp down"],
                horizontal=True, key="tr_kern_type")

            kern_min=0; kern_km=0.0; kern_zone=ZONE_LABELS[1]; kern_notitie=""

            if kern_type == "Doorlopend":
                k1, k2 = st.columns(2)
                with k1:
                    kern_min, kern_km, kern_zone = _invoer_blok("tr_kern","Duur (min)","Afstand (km)",40,8.0,1)
                with k2:
                    kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone, sport) if kern_min > 0 else 0
                    if kern_min > 0:
                        st.markdown("<br>", unsafe_allow_html=True)
                        _metric_card("KCAL", str(kern_kcal), "kcal", "#22c55e")
            elif kern_type == "Intervalblokken":
                ic1, ic2, ic3 = st.columns(3)
                with ic1:
                    int_herh    = st.number_input("Herhalingen", 1, 30, 5, key="tr_int_herh")
                    int_zone_w  = _zone_selectbox("Zone werk", "tr_int_zone_w", 3)
                with ic2:
                    int_zone_r  = _zone_selectbox("Zone rust", "tr_int_zone_r", 0)
                    if invoer_modus == "Afstand (km)" and sport == "Lopen":
                        int_werk_km = st.number_input("Werkblok (km)", 0.1, 10.0, 1.0, 0.1, key="tr_int_werk_km")
                        int_rust_km = st.number_input("Rustblok (km)", 0.1, 5.0, 0.4, 0.1, key="tr_int_rust_km")
                        tempo_w = zones_data.get("z4_tempo", 4.5) or 4.5
                        tempo_r = zones_data.get("z1_tempo", 7.0) or 7.0
                        int_werk = round(int_werk_km * tempo_w)
                        int_rust  = round(int_rust_km * tempo_r)
                        kern_km   = int_herh * (int_werk_km + int_rust_km)
                        kern_notitie = f"{int_herh}× {int_werk_km}km {int_zone_w[:2]} + {int_rust_km}km {int_zone_r[:2]}"
                    else:
                        int_werk = st.number_input("Werkblok (min)", 1, 60, 4, key="tr_int_werk")
                        int_rust  = st.number_input("Rustblok (min)", 1, 30, 2, key="tr_int_rust")
                        kern_notitie = f"{int_herh}× {int_werk}min {int_zone_w[:2]} + {int_rust}min {int_zone_r[:2]}"
                kern_min  = int_herh * (int_werk + int_rust)
                kern_zone = int_zone_w
                with ic3:
                    st.markdown(f'<div style="font-size:0.8rem;color:#22c55e;padding-top:28px;">{kern_notitie}</div>', unsafe_allow_html=True)
            elif kern_type == "Ramp up":
                ru1, ru2, ru3 = st.columns(3)
                with ru1: ramp_min = st.number_input("Duur (min)", 5, 120, 20, key="tr_ramp_min")
                with ru2: ramp_van  = _zone_selectbox("Van zone", "tr_ramp_van", 1)
                with ru3: ramp_naar = _zone_selectbox("Naar zone", "tr_ramp_naar", 3)
                kern_min = ramp_min; kern_zone = ramp_naar
                kern_notitie = f"Ramp: {ramp_van[:2]} → {ramp_naar[:2]}"
            elif kern_type == "Ramp down":
                rd1, rd2, rd3 = st.columns(3)
                with rd1: ramp_min = st.number_input("Duur (min)", 5, 120, 20, key="tr_rampd_min")
                with rd2: ramp_van  = _zone_selectbox("Van zone", "tr_rampd_van", 3)
                with rd3: ramp_naar = _zone_selectbox("Naar zone", "tr_rampd_naar", 1)
                kern_min = ramp_min; kern_zone = ramp_van
                kern_notitie = f"Ramp: {ramp_van[:2]} → {ramp_naar[:2]}"

            kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone, sport) if kern_min > 0 else 0

            _sectie("COOLING DOWN", "#22c55e")
            cd1, cd2 = st.columns(2)
            with cd1:
                cool_min, cool_km, cool_zone = _invoer_blok("tr_cool","Duur (min)","Afstand (km)",10,2.0,0)
            with cd2:
                cool_kcal = _bereken_kcal(gewicht, cool_min, cool_zone, sport) if cool_min > 0 else 0
                if cool_min > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    _metric_card("KCAL", str(cool_kcal), "kcal", "#22c55e")

            totaal_min  = opw_min + kern_min + cool_min
            totaal_kcal = opw_kcal + kern_kcal + cool_kcal
            blokken     = [(opw_zone, opw_min), (kern_zone, kern_min), (cool_zone, cool_min)]
            dom_zone    = _dominante_zone(blokken) if totaal_min > 0 else "—"

            if totaal_min > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                _sectie("SAMENVATTING", "#22c55e")
                m1, m2, m3 = st.columns(3)
                with m1: _metric_card("TOTALE DUUR", f"{totaal_min//60}u{totaal_min%60:02d}", "min", "#22c55e")
                with m2: _metric_card("KCAL", str(totaal_kcal), "kcal", "#4ade80")
                with m3: _metric_card("DOM. ZONE", dom_zone[:2], dom_zone[4:], "#16a34a")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Training opslaan", key="tr_opslaan", use_container_width=True, type="primary"):
                    zone_verdeling = {}
                    for z, m in blokken:
                        zk = z[:2].lower()
                        zone_verdeling[zk] = zone_verdeling.get(zk, 0) + m
                    notitie_vol = (
                        f"{omschrijving + ' | ' if omschrijving else ''}"
                        f"OPW: {opw_min}min {opw_zone[:2]} | KERN: {kern_min}min {kern_zone[:2]}"
                        f"{chr(32)+kern_notitie if kern_notitie else ''} | COOL: {cool_min}min {cool_zone[:2]}"
                    ).strip(" | ")
                    import json as _jtr
                    training_data = {
                        "datum":           str(datum),
                        "sport":           sport,
                        "omschrijving":    omschrijving or "",
                        "duur_min":        totaal_min,
                        "afstand_km":      round(opw_km + kern_km + cool_km, 2),
                        "kcal_verbranding":totaal_kcal,
                        "zone_verdeling":  _jtr.dumps(zone_verdeling),
                        "notitie":         notitie_vol,
                        "starttijd":       starttijd or "07:00",
                    }
                    if _sla_training_op(user_id, training_data):
                        _laad_trainingen.clear()
                        st.session_state["tr_saved"] = True
                        for k in [k for k in st.session_state
                                  if k.startswith(("tr_opw","tr_kern","tr_cool",
                                                   "tr_naam","tr_int","tr_ramp"))]:
                            st.session_state.pop(k, None)
                        st.rerun()

                if st.session_state.pop("tr_saved", False):
                    st.success("✅ Training opgeslagen! Ga naar 📋 Mijn trainingen.")
            else:
                st.button("💾 Training opslaan", key="tr_opslaan", use_container_width=True, disabled=True)
                st.caption("Vul minstens één blok in.")


    with tab_zones:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ZONE KALIBRATIE PER SPORT", "#22c55e")
        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:16px;">' +
            'Koppel je intensiteitszones aan tempo of hartslag. ' +
            'Voer tempo in als decimale minuten: 5.30 = 5min30sec/km.</div>',
            unsafe_allow_html=True)

        kal_sport = st.selectbox("Sport", SPORT_OPTIES, key="kal_sport")
        kal_zones = _laad_zones(user_id, kal_sport)

        # Toon status per sport
        sport_status = []
        for sp in SPORT_OPTIES:
            z = _laad_zones(user_id, sp)
            if z:
                sport_status.append(f'<span style="background:#22c55e22;color:#22c55e;border:1px solid #22c55e44;border-radius:4px;padding:2px 8px;font-size:0.7rem;margin:2px;">{sp} ✓</span>')
            else:
                sport_status.append(f'<span style="background:#1e293b;color:#475569;border:1px solid #334155;border-radius:4px;padding:2px 8px;font-size:0.7rem;margin:2px;">{sp}</span>')
        st.markdown(
            '<div style="margin-bottom:12px;">' + " ".join(sport_status) + '</div>',
            unsafe_allow_html=True)

        if kal_sport == "Lopen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/km)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Indoor lopen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/km)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Fietsen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Watt", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Roeien":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/500m)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Crosstrainer":
            kal_eenheid = st.radio("Koppelen aan",
                ["Watt", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        else:
            kal_eenheid = "Hartslag (bpm)"

        toon_tempo = kal_eenheid in ["Tempo (min/km)", "Tempo (min/500m)", "Watt", "Beide"]
        toon_hs    = kal_eenheid in ["Hartslag (bpm)", "Beide"]
        if kal_sport in ("Lopen", "Indoor lopen"):
            tempo_label = "Tempo (min/km)"
        elif kal_sport == "Roeien":
            tempo_label = "Tempo (min/500m)"
        else:
            tempo_label = "Watt"

        nieuwe_zones = {"eenheid": "tempo" if toon_tempo and not toon_hs else "hartslag"}

        for z in ZONE_LABELS:
            z_key = z[:2].lower()
            st.markdown(
                f'<div style="font-size:0.75rem;font-weight:700;color:#22c55e;margin:14px 0 4px;' +
                f'padding:4px 8px;background:#0f172a;border-left:3px solid #22c55e;border-radius:0 4px 4px 0;">' +
                f'{z}</div>', unsafe_allow_html=True)

            if toon_tempo:
                t1, t2 = st.columns(2)
                with t1:
                    # Gebruik text_input voor tempo om automatisch aanpassen te voorkomen
                    huidig_van_raw = kal_zones.get(f"{z_key}_tempo_van") or 0
                    huidig_van_str = _format_tempo(float(huidig_van_raw)) if huidig_van_raw else ""
                    tempo_van_str = st.text_input(
                        f"{tempo_label} — van (langzamer)",
                        value=huidig_van_str,
                        key=f"kal_{z_key}_tempo_van_str",
                        placeholder="bijv. 5:30",
                        help="Formaat: min:sec bijv. 5:30 of 5.5")
                    # Converteer terug naar decimaal
                    nieuwe_zones[f"{z_key}_tempo_van"] = _parse_tempo(tempo_van_str)

                with t2:
                    huidig_tot_raw = kal_zones.get(f"{z_key}_tempo_tot") or 0
                    huidig_tot_str = _format_tempo(float(huidig_tot_raw)) if huidig_tot_raw else ""
                    tempo_tot_str = st.text_input(
                        f"{tempo_label} — tot (sneller)",
                        value=huidig_tot_str,
                        key=f"kal_{z_key}_tempo_tot_str",
                        placeholder="bijv. 5:00",
                        help="Formaat: min:sec bijv. 5:00 of 5.0")
                    nieuwe_zones[f"{z_key}_tempo_tot"] = _parse_tempo(tempo_tot_str)

                van_val = nieuwe_zones.get(f"{z_key}_tempo_van")
                tot_val = nieuwe_zones.get(f"{z_key}_tempo_tot")
                if van_val and tot_val:
                    if kal_sport == "Lopen":
                        preview = f"{_format_tempo(van_val)} — {_format_tempo(tot_val)} min/km"
                    else:
                        preview = f"{int(van_val)}—{int(tot_val)}W"
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#86efac;margin-top:-6px;margin-bottom:4px;">' +
                        f'→ {preview}</div>', unsafe_allow_html=True)

            if toon_hs:
                h1, h2 = st.columns(2)
                with h1:
                    hs_van = st.number_input("Hartslag — van (bpm)", 0, 220,
                        int(kal_zones.get(f"{z_key}_hs_van") or 0), 1,
                        key=f"kal_{z_key}_hs_van")
                    nieuwe_zones[f"{z_key}_hs_van"] = hs_van if hs_van > 0 else None
                with h2:
                    hs_tot = st.number_input("Hartslag — tot (bpm)", 0, 220,
                        int(kal_zones.get(f"{z_key}_hs_tot") or 0), 1,
                        key=f"kal_{z_key}_hs_tot")
                    nieuwe_zones[f"{z_key}_hs_tot"] = hs_tot if hs_tot > 0 else None
                if hs_van and hs_tot:
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#86efac;margin-top:-6px;margin-bottom:4px;">' +
                        f'→ {int(hs_van)}—{int(hs_tot)} bpm</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"💾 Zones opslaan voor {kal_sport}", key=f"kal_ops_{kal_sport}", use_container_width=True):
            if _sla_zones_op(user_id, kal_sport, nieuwe_zones):
                _laad_zones.clear()
                st.success(f"✅ Zones opgeslagen voor {kal_sport}!")
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — MIJN TRAININGEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        trainingen = _laad_trainingen(user_id)

        if not trainingen:
            st.markdown(
                '<div style="text-align:center;color:#64748b;padding:30px;">' +
                'Nog geen trainingen toegevoegd.</div>',
                unsafe_allow_html=True)
        else:
            from datetime import date as _dt2, timedelta as _td2
            vandaag    = _dt2.today()
            week_start = vandaag - _td2(days=vandaag.weekday())
            week_kcal  = sum(t.get("kcal_verbranding",0) or 0 for t in trainingen if t.get("datum","") >= str(week_start))
            week_min   = sum(t.get("duur_min",0) or 0 for t in trainingen if t.get("datum","") >= str(week_start))
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #22c55e;border-radius:10px;' +
                f'padding:12px 16px;margin-bottom:16px;display:flex;gap:24px;">' +
                f'<div><div style="font-size:0.65rem;color:#64748b;">DEZE WEEK</div>' +
                f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">{week_min//60}u{week_min%60:02d} · {week_kcal} kcal</div></div>' +
                f'<div><div style="font-size:0.65rem;color:#64748b;">TRAININGEN</div>' +
                f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">' +
                f'{len([t for t in trainingen if t.get("datum","") >= str(week_start)])}</div></div></div>',
                unsafe_allow_html=True)

            SPORT_EMOJI = {"Lopen":"🏃","Fietsen":"🚴","Zwemmen":"🏊","Kracht":"💪","Andere":"⚡"}
            ZONE_KLEUR  = {"z1":"#64748b","z2":"#22c55e","z3":"#fbbf24","z4":"#f97316","z5":"#ef4444"}

            for t in trainingen:
                import json as _jt
                sport_em = SPORT_EMOJI.get(t.get("sport",""),"⚡")
                duur_min = t.get("duur_min",0) or 0
                kcal     = t.get("kcal_verbranding",0) or 0
                notitie  = t.get("notitie","") or ""
                zv = t.get("zone_verdeling") or {}
                if isinstance(zv,str):
                    try: zv = _jt.loads(zv)
                    except: zv = {}
                totaal_zv = sum(zv.values()) if zv else max(duur_min,1)
                zone_balken = "".join([
                    f'<div style="display:inline-block;width:{round(zv.get(z,0)/totaal_zv*100)}%;' +
                    f'height:6px;background:{kleur};"></div>'
                    for z,kleur in ZONE_KLEUR.items() if zv.get(z,0) > 0
                ])

                with st.expander(
                    f"{sport_em} {t.get('sport','')} — {t.get('datum','')[:10]} — "
                    f"{duur_min//60}u{duur_min%60:02d} — {kcal}kcal",
                    expanded=False):
                    if notitie:
                        st.markdown(f'<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">{notitie[:100]}</div>', unsafe_allow_html=True)
                    if zone_balken:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;margin-bottom:6px;">{zone_balken}</div>',
                            unsafe_allow_html=True)

                    # Bevestiging verwijder
                    confirm_key = f"confirm_del_{t['id']}"
                    if not st.session_state.get(confirm_key, False):
                        if st.button("🗑 Verwijderen", key=f"tr_del_{t['id']}"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("Ben je zeker dat je deze training wilt verwijderen?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Ja, verwijderen", key=f"tr_del_ja_{t['id']}", use_container_width=True):
                                if _verwijder_training(t["id"]):
                                    _laad_trainingen.clear()
                                    st.session_state.pop(confirm_key, None)
                                    st.rerun()
                        with c2:
                            if st.button("❌ Annuleren", key=f"tr_del_nee_{t['id']}", use_container_width=True):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()



# ═══════════════════════════════════════════════════════════════════════════════
# VOEDSEL_DB — NEVO-GEBASEERD, 120+ PRODUCTEN MET HUISHOUDMATEN
# ═══════════════════════════════════════════════════════════════════════════════

SPORT_EMOJI = {
    "zwemmen": "🏊", "swim": "🏊", "zwem": "🏊",
    "fietsen": "🚴", "wielrennen": "🚴", "mtb": "🚴", "cycling": "🚴",
    "lopen": "🏃", "hardlopen": "🏃", "running": "🏃", "run": "🏃",
    "wandelen": "🚶", "hiken": "🥾", "hiking": "🥾", "trail": "🏔️",
    "kracht": "🏋️", "fitness": "🏋️", "gym": "🏋️", "gewichten": "🏋️",
    "yoga": "🧘", "pilates": "🧘", "stretching": "🧘",
    "triathlon": "🏊", "duathlon": "🚴",
    "voetbal": "⚽", "tennis": "🎾", "padel": "🎾",
    "roeien": "🚣", "kayak": "🚣", "sup": "🚣",
    "crossfit": "🏋️", "hiit": "⚡", "interval": "⚡",
    "herstel": "💆", "recovery": "💆",
}

def _sport_emoji(sport_naam: str) -> str:
    """Geeft het juiste emoji voor een sporttype terug."""
    if not sport_naam:
        return "⚡"
    nl = sport_naam.lower().strip()
    for sleutel, emoji in SPORT_EMOJI.items():
        if sleutel in nl:
            return emoji
    return "⚡"


VOEDSEL_DB = [
    # ── GRANEN & BROOD ────────────────────────────────────────────────────────
    {"naam":"Volkorenbrood","cat":"Granen & brood","moment":["ontbijt","lunch"],
     "portie":35,"portie_label":"1 snede","gi":50,
     "kcal":224,"kh":40,"suikers":3,"toegev_suikers":0,"vezels":7,"eiwit":9,"vet":3,"verz":0.5,
     "natrium":400,"kalium":230,"calcium":25,"ijzer":2.0,"magnesium":45,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Wit brood","cat":"Granen & brood","moment":["ontbijt","lunch"],
     "portie":35,"portie_label":"1 snede","gi":70,
     "kcal":265,"kh":49,"suikers":4,"toegev_suikers":0,"vezels":2,"eiwit":8,"vet":3,"verz":0.6,
     "natrium":500,"kalium":100,"calcium":40,"ijzer":1.5,"magnesium":20,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Havermout","cat":"Granen & brood","moment":["ontbijt"],
     "portie":45,"portie_label":"6 el droog","gi":55,
     "kcal":370,"kh":60,"suikers":1,"toegev_suikers":0,"vezels":10,"eiwit":13,"vet":7,"verz":1.2,
     "natrium":5,"kalium":360,"calcium":50,"ijzer":3.9,"magnesium":130,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Rijst wit gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":64,
     "kcal":130,"kh":28,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":3,"vet":0,"verz":0,
     "natrium":0,"kalium":35,"calcium":10,"ijzer":0.2,"magnesium":12,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Rijst volkoren gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":50,
     "kcal":110,"kh":23,"suikers":0,"vezels":2,"eiwit":3,"vet":1,"verz":0.1,
     "natrium":0,"kalium":84,"calcium":10,"ijzer":0.5,"magnesium":44,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Pasta volkoren gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":42,
     "kcal":150,"kh":28,"suikers":1,"toegev_suikers":0,"vezels":4,"eiwit":6,"vet":1,"verz":0.1,
     "natrium":0,"kalium":90,"calcium":20,"ijzer":1.5,"magnesium":47,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Aardappel gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":175,"portie_label":"2 middelgrote","gi":72,
     "kcal":87,"kh":20,"suikers":1,"toegev_suikers":0,"vezels":2,"eiwit":2,"vet":0,"verz":0,
     "natrium":5,"kalium":410,"calcium":6,"ijzer":0.3,"magnesium":20,"vitc":12,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Zoete aardappel gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 middelgrote","gi":61,
     "kcal":90,"kh":21,"suikers":4,"vezels":3,"eiwit":2,"vet":0,"verz":0,
     "natrium":36,"kalium":337,"calcium":30,"ijzer":0.7,"magnesium":25,"vitc":20,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Quinoa gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":185,"portie_label":"3 opscheplepels","gi":53,
     "kcal":120,"kh":21,"suikers":1,"toegev_suikers":0,"vezels":3,"eiwit":4,"vet":2,"verz":0.2,
     "natrium":5,"kalium":172,"calcium":17,"ijzer":1.5,"magnesium":64,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Rijstwafel naturel","cat":"Granen & brood","moment":["tussendoor","ontbijt"],
     "portie":9,"portie_label":"1 wafel","gi":82,
     "kcal":385,"kh":81,"suikers":1,"vezels":2,"eiwit":8,"vet":3,"verz":0.5,
     "natrium":10,"kalium":95,"calcium":5,"ijzer":0.5,"magnesium":35,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    # ── ZUIVEL & ALTERNATIEVEN ────────────────────────────────────────────────
    {"naam":"Volle melk","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":27,
     "kcal":64,"kh":5,"suikers":5,"vezels":0,"eiwit":3,"vet":4,"verz":2.4,
     "natrium":43,"kalium":150,"calcium":120,"ijzer":0.1,"magnesium":11,"vitc":1,"vitd":0.1,"vitb12":0.5,"omega3":0.1},
    {"naam":"Halfvolle melk","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":27,
     "kcal":46,"kh":5,"suikers":5,"toegev_suikers":0,"vezels":0,"eiwit":3,"vet":2,"verz":1.1,
     "natrium":43,"kalium":150,"calcium":120,"ijzer":0.1,"magnesium":11,"vitc":1,"vitd":0.1,"vitb12":0.5,"omega3":0},
    {"naam":"Griekse yoghurt vol","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"1 kommetje","gi":11,
     "kcal":130,"kh":4,"suikers":4,"vezels":0,"eiwit":9,"vet":8,"verz":5.0,
     "natrium":40,"kalium":170,"calcium":110,"ijzer":0.1,"magnesium":11,"vitc":0,"vitd":0.1,"vitb12":0.8,"omega3":0.1},
    {"naam":"Kwark mager","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":100,"portie_label":"3 el","gi":15,
     "kcal":57,"kh":4,"suikers":4,"toegev_suikers":0,"vezels":0,"eiwit":9,"vet":0,"verz":0,
     "natrium":40,"kalium":130,"calcium":95,"ijzer":0.1,"magnesium":9,"vitc":0,"vitd":0,"vitb12":0.5,"omega3":0},
    {"naam":"Skyr","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"1 kommetje","gi":14,
     "kcal":63,"kh":4,"suikers":4,"vezels":0,"eiwit":11,"vet":0,"verz":0,
     "natrium":50,"kalium":160,"calcium":130,"ijzer":0.1,"magnesium":12,"vitc":0,"vitd":0.1,"vitb12":1.0,"omega3":0},
    {"naam":"Edammer 30+","cat":"Zuivel","moment":["ontbijt","lunch"],
     "portie":20,"portie_label":"1 plakje","gi":0,
     "kcal":270,"kh":0,"suikers":0,"vezels":0,"eiwit":27,"vet":18,"verz":11.0,
     "natrium":800,"kalium":100,"calcium":770,"ijzer":0.2,"magnesium":30,"vitc":0,"vitd":0.2,"vitb12":1.5,"omega3":0.2},
    {"naam":"Mozzarella","cat":"Zuivel","moment":["lunch","avond"],
     "portie":50,"portie_label":"halve bol","gi":0,
     "kcal":280,"kh":2,"suikers":1,"toegev_suikers":0,"vezels":0,"eiwit":19,"vet":22,"verz":13.0,
     "natrium":600,"kalium":76,"calcium":505,"ijzer":0.3,"magnesium":20,"vitc":0,"vitd":0.2,"vitb12":1.3,"omega3":0.2},
    {"naam":"Haverdrank","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":49,
     "kcal":45,"kh":7,"suikers":4,"vezels":1,"eiwit":1,"vet":1,"verz":0.2,
     "natrium":60,"kalium":60,"calcium":120,"ijzer":0.2,"magnesium":10,"vitc":0,"vitd":1.0,"vitb12":0,"omega3":0},
    {"naam":"Sojadrank","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":30,
     "kcal":40,"kh":3,"suikers":2,"vezels":0,"eiwit":3,"vet":2,"verz":0.3,
     "natrium":50,"kalium":130,"calcium":120,"ijzer":0.4,"magnesium":19,"vitc":0,"vitd":1.0,"vitb12":0.4,"omega3":0.3},
    {"naam":"Plattekaas","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":100,"portie_label":"3 el","gi":10,
     "kcal":72,"kh":3,"suikers":3,"vezels":0,"eiwit":8,"vet":3,"verz":2.0,
     "natrium":55,"kalium":120,"calcium":85,"ijzer":0.1,"magnesium":8,"vitc":0,"vitd":0,"vitb12":0.5,"omega3":0},

    # ── VLEES & VIS ───────────────────────────────────────────────────────────
    {"naam":"Kipfilet gebakken","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":120,"portie_label":"1 filet","gi":0,
     "kcal":165,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":31,"vet":4,"verz":1.0,
     "natrium":74,"kalium":370,"calcium":12,"ijzer":1.0,"magnesium":28,"vitc":0,"vitd":0.1,"vitb12":0.3,"omega3":0.1},
    {"naam":"Zalm gebakken","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":0,
     "kcal":208,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":20,"vet":13,"verz":3.0,
     "natrium":59,"kalium":440,"calcium":15,"ijzer":0.5,"magnesium":27,"vitc":0,"vitd":9.0,"vitb12":3.0,"omega3":2.3},
    {"naam":"Tonijn in water","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 blikje uitgelekt","gi":0,
     "kcal":108,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":25,"vet":1,"verz":0.2,
     "natrium":320,"kalium":280,"calcium":10,"ijzer":1.3,"magnesium":30,"vitc":0,"vitd":3.0,"vitb12":2.0,"omega3":0.3},
    {"naam":"Rundergehakt mager","cat":"Vlees & vis","moment":["avond"],
     "portie":120,"portie_label":"1 portie","gi":0,
     "kcal":200,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":20,"vet":13,"verz":5.0,
     "natrium":75,"kalium":300,"calcium":10,"ijzer":2.5,"magnesium":20,"vitc":0,"vitd":0,"vitb12":2.0,"omega3":0.1},
    {"naam":"Kabeljauw","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":0,
     "kcal":82,"kh":0,"suikers":0,"vezels":0,"eiwit":18,"vet":1,"verz":0.1,
     "natrium":54,"kalium":340,"calcium":15,"ijzer":0.3,"magnesium":30,"vitc":0,"vitd":1.0,"vitb12":1.5,"omega3":0.3},
    {"naam":"Makreel gerookt","cat":"Vlees & vis","moment":["lunch"],
     "portie":100,"portie_label":"1 filet","gi":0,
     "kcal":205,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":19,"vet":14,"verz":3.0,
     "natrium":700,"kalium":330,"calcium":12,"ijzer":1.0,"magnesium":30,"vitc":0,"vitd":5.0,"vitb12":7.0,"omega3":2.2},
    {"naam":"Garnalen","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 portie","gi":0,
     "kcal":99,"kh":0,"suikers":0,"vezels":0,"eiwit":21,"vet":1,"verz":0.3,
     "natrium":111,"kalium":220,"calcium":60,"ijzer":1.5,"magnesium":30,"vitc":0,"vitd":0,"vitb12":1.0,"omega3":0.6},
    {"naam":"Kippenham","cat":"Vlees & vis","moment":["ontbijt","lunch"],
     "portie":30,"portie_label":"2 plakjes","gi":0,
     "kcal":105,"kh":2,"suikers":1,"vezels":0,"eiwit":18,"vet":3,"verz":1.0,
     "natrium":900,"kalium":200,"calcium":10,"ijzer":0.5,"magnesium":15,"vitc":0,"vitd":0,"vitb12":0.2,"omega3":0},
    {"naam":"Biefstuk","cat":"Vlees & vis","moment":["avond"],
     "portie":150,"portie_label":"1 stuk","gi":0,
     "kcal":217,"kh":0,"suikers":0,"vezels":0,"eiwit":26,"vet":12,"verz":4.0,
     "natrium":66,"kalium":380,"calcium":10,"ijzer":2.8,"magnesium":24,"vitc":0,"vitd":0,"vitb12":2.5,"omega3":0.1},
    {"naam":"Sardines in blik","cat":"Vlees & vis","moment":["lunch"],
     "portie":100,"portie_label":"1 blikje","gi":0,
     "kcal":208,"kh":0,"suikers":0,"vezels":0,"eiwit":25,"vet":11,"verz":1.5,
     "natrium":505,"kalium":300,"calcium":380,"ijzer":2.9,"magnesium":39,"vitc":0,"vitd":4.0,"vitb12":8.0,"omega3":1.5},

    # ── EIEREN ────────────────────────────────────────────────────────────────
    {"naam":"Ei gekookt","cat":"Eieren","moment":["ontbijt","lunch"],
     "portie":60,"portie_label":"1 ei (M)","gi":0,
     "kcal":155,"kh":1,"suikers":1,"vezels":0,"eiwit":13,"vet":11,"verz":3.0,
     "natrium":124,"kalium":130,"calcium":50,"ijzer":1.8,"magnesium":12,"vitc":0,"vitd":2.0,"vitb12":0.9,"omega3":0.1},
    {"naam":"Ei gebakken","cat":"Eieren","moment":["ontbijt","lunch"],
     "portie":60,"portie_label":"1 ei (M)","gi":0,
     "kcal":185,"kh":1,"suikers":0,"vezels":0,"eiwit":13,"vet":14,"verz":3.5,
     "natrium":130,"kalium":130,"calcium":50,"ijzer":1.8,"magnesium":12,"vitc":0,"vitd":2.0,"vitb12":0.9,"omega3":0.1},

    # ── GROENTEN ──────────────────────────────────────────────────────────────
    {"naam":"Broccoli gekookt","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":10,
     "kcal":34,"kh":7,"suikers":2,"vezels":3,"eiwit":3,"vet":0,"verz":0,
     "natrium":33,"kalium":316,"calcium":47,"ijzer":0.7,"magnesium":21,"vitc":65,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Spinazie gekookt","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":15,
     "kcal":23,"kh":4,"suikers":0,"vezels":2,"eiwit":3,"vet":0,"verz":0,
     "natrium":79,"kalium":466,"calcium":99,"ijzer":2.7,"magnesium":87,"vitc":28,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Wortel rauw","cat":"Groenten","moment":["lunch","tussendoor"],
     "portie":80,"portie_label":"1 middelgrote","gi":35,
     "kcal":41,"kh":10,"suikers":5,"vezels":3,"eiwit":1,"vet":0,"verz":0,
     "natrium":69,"kalium":320,"calcium":33,"ijzer":0.3,"magnesium":12,"vitc":6,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Tomaat","cat":"Groenten","moment":["lunch","avond"],
     "portie":120,"portie_label":"1 tomaat","gi":15,
     "kcal":18,"kh":4,"suikers":3,"toegev_suikers":0,"vezels":1,"eiwit":1,"vet":0,"verz":0,
     "natrium":5,"kalium":237,"calcium":10,"ijzer":0.3,"magnesium":11,"vitc":14,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Paprika rood","cat":"Groenten","moment":["lunch","avond","tussendoor"],
     "portie":120,"portie_label":"1 paprika","gi":15,
     "kcal":31,"kh":7,"suikers":5,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":4,"kalium":212,"calcium":7,"ijzer":0.4,"magnesium":10,"vitc":128,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Courgette","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":15,
     "kcal":17,"kh":3,"suikers":2,"toegev_suikers":0,"vezels":1,"eiwit":1,"vet":0,"verz":0,
     "natrium":8,"kalium":261,"calcium":16,"ijzer":0.4,"magnesium":18,"vitc":17,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Champignon","cat":"Groenten","moment":["ontbijt","lunch","avond"],
     "portie":100,"portie_label":"handjevol","gi":10,
     "kcal":22,"kh":3,"suikers":2,"vezels":1,"eiwit":3,"vet":0,"verz":0,
     "natrium":5,"kalium":318,"calcium":3,"ijzer":0.5,"magnesium":9,"vitc":3,"vitd":1.0,"vitb12":0,"omega3":0},
    {"naam":"Avocado","cat":"Groenten","moment":["ontbijt","lunch"],
     "portie":80,"portie_label":"halve avocado","gi":10,
     "kcal":160,"kh":9,"suikers":1,"toegev_suikers":0,"vezels":7,"eiwit":2,"vet":15,"verz":2.0,
     "natrium":7,"kalium":485,"calcium":12,"ijzer":0.6,"magnesium":29,"vitc":10,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Linzen gekookt","cat":"Peulvruchten","moment":["lunch","avond"],
     "portie":150,"portie_label":"3 opscheplepels","gi":32,
     "kcal":116,"kh":20,"suikers":2,"toegev_suikers":0,"vezels":8,"eiwit":9,"vet":0,"verz":0,
     "natrium":238,"kalium":365,"calcium":19,"ijzer":3.3,"magnesium":36,"vitc":3,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Kikkererwten gekookt","cat":"Peulvruchten","moment":["lunch","avond"],
     "portie":150,"portie_label":"3 opscheplepels","gi":28,
     "kcal":164,"kh":27,"suikers":5,"vezels":8,"eiwit":9,"vet":3,"verz":0.3,
     "natrium":24,"kalium":291,"calcium":49,"ijzer":2.9,"magnesium":48,"vitc":2,"vitd":0,"vitb12":0,"omega3":0.1},

    # ── FRUIT ─────────────────────────────────────────────────────────────────
    {"naam":"Banaan","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":120,"portie_label":"1 banaan (M)","gi":51,
     "kcal":89,"kh":23,"suikers":12,"toegev_suikers":0,"vezels":3,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":358,"calcium":5,"ijzer":0.3,"magnesium":27,"vitc":9,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Appel","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":150,"portie_label":"1 appel (M)","gi":38,
     "kcal":52,"kh":14,"suikers":10,"toegev_suikers":0,"vezels":2,"eiwit":0,"vet":0,"verz":0,
     "natrium":1,"kalium":107,"calcium":6,"ijzer":0.1,"magnesium":5,"vitc":5,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Sinaasappel","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":150,"portie_label":"1 sinaasappel","gi":43,
     "kcal":47,"kh":12,"suikers":9,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":0,"kalium":181,"calcium":40,"ijzer":0.1,"magnesium":10,"vitc":53,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Bosbes","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":100,"portie_label":"handjevol","gi":25,
     "kcal":57,"kh":14,"suikers":10,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":77,"calcium":6,"ijzer":0.3,"magnesium":6,"vitc":10,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Aardbei","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"handjevol","gi":40,
     "kcal":32,"kh":8,"suikers":5,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":153,"calcium":16,"ijzer":0.4,"magnesium":13,"vitc":59,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Mango","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":150,"portie_label":"1 kopje blokjes","gi":51,
     "kcal":60,"kh":15,"suikers":14,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":168,"calcium":11,"ijzer":0.2,"magnesium":10,"vitc":28,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Kiwi","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":80,"portie_label":"1 kiwi","gi":39,
     "kcal":61,"kh":15,"suikers":9,"toegev_suikers":0,"vezels":3,"eiwit":1,"vet":1,"verz":0,
     "natrium":3,"kalium":312,"calcium":34,"ijzer":0.3,"magnesium":17,"vitc":93,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Dadel gedroogd","cat":"Fruit","moment":["tussendoor"],
     "portie":30,"portie_label":"3 dadels","gi":42,
     "kcal":277,"kh":75,"suikers":66,"toegev_suikers":0,"vezels":7,"eiwit":2,"vet":0,"verz":0,
     "natrium":1,"kalium":696,"calcium":64,"ijzer":0.9,"magnesium":54,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Rozijnen","cat":"Fruit","moment":["tussendoor"],
     "portie":30,"portie_label":"2 el","gi":64,
     "kcal":299,"kh":79,"suikers":59,"toegev_suikers":0,"vezels":4,"eiwit":3,"vet":0,"verz":0,
     "natrium":11,"kalium":749,"calcium":50,"ijzer":1.9,"magnesium":32,"vitc":4,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Peer","cat":"Fruit","moment":["tussendoor"],
     "portie":150,"portie_label":"1 peer (M)","gi":38,
     "kcal":57,"kh":15,"suikers":10,"toegev_suikers":0,"vezels":3,"eiwit":0,"vet":0,"verz":0,
     "natrium":1,"kalium":119,"calcium":9,"ijzer":0.2,"magnesium":7,"vitc":4,"vitd":0,"vitb12":0,"omega3":0},

    # ── NOTEN & ZADEN ─────────────────────────────────────────────────────────
    {"naam":"Amandelen","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"handjevol (~20st)","gi":0,
     "kcal":579,"kh":22,"suikers":4,"toegev_suikers":0,"vezels":13,"eiwit":21,"vet":50,"verz":4.0,
     "natrium":1,"kalium":705,"calcium":264,"ijzer":3.7,"magnesium":270,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Walnoten","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"handjevol (~7 halve)","gi":0,
     "kcal":654,"kh":14,"suikers":3,"toegev_suikers":0,"vezels":7,"eiwit":15,"vet":65,"verz":6.0,
     "natrium":2,"kalium":441,"calcium":98,"ijzer":2.9,"magnesium":158,"vitc":1,"vitd":0,"vitb12":0,"omega3":2.6},
    {"naam":"Cashewnoten","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"handjevol (~20st)","gi":25,
     "kcal":553,"kh":33,"suikers":6,"toegev_suikers":0,"vezels":3,"eiwit":18,"vet":44,"verz":9.0,
     "natrium":12,"kalium":660,"calcium":37,"ijzer":6.7,"magnesium":292,"vitc":1,"vitd":0,"vitb12":0,"omega3":0.2},
    {"naam":"Chiazaad","cat":"Noten & zaden","moment":["ontbijt","tussendoor"],
     "portie":15,"portie_label":"1 el","gi":1,
     "kcal":486,"kh":42,"suikers":0,"toegev_suikers":0,"vezels":34,"eiwit":17,"vet":31,"verz":3.0,
     "natrium":16,"kalium":407,"calcium":631,"ijzer":7.7,"magnesium":335,"vitc":2,"vitd":0,"vitb12":0,"omega3":5.1},
    {"naam":"Lijnzaad","cat":"Noten & zaden","moment":["ontbijt"],
     "portie":10,"portie_label":"1 el","gi":35,
     "kcal":534,"kh":29,"suikers":2,"toegev_suikers":0,"vezels":27,"eiwit":18,"vet":42,"verz":4.0,
     "natrium":30,"kalium":813,"calcium":255,"ijzer":5.7,"magnesium":392,"vitc":0,"vitd":0,"vitb12":0,"omega3":6.4},
    {"naam":"Pompoenpitten","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"2 el","gi":25,
     "kcal":559,"kh":11,"suikers":1,"toegev_suikers":0,"vezels":6,"eiwit":30,"vet":49,"verz":9.0,
     "natrium":7,"kalium":809,"calcium":46,"ijzer":8.8,"magnesium":592,"vitc":2,"vitd":0,"vitb12":0,"omega3":0.1},

    # ── VETTEN & OLIËN ────────────────────────────────────────────────────────
    {"naam":"Olijfolie extra vierge","cat":"Vetten & oliën","moment":["lunch","avond"],
     "portie":10,"portie_label":"1 el","gi":0,
     "kcal":884,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":100,"verz":14.0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0.1,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.8},
    {"naam":"Boter","cat":"Vetten & oliën","moment":["ontbijt","lunch"],
     "portie":10,"portie_label":"1 kl","gi":0,
     "kcal":717,"kh":1,"suikers":0,"vezels":0,"eiwit":1,"vet":81,"verz":51.0,
     "natrium":700,"kalium":24,"calcium":24,"ijzer":0.1,"magnesium":2,"vitc":0,"vitd":0.1,"vitb12":0,"omega3":0.3},
    {"naam":"Kokosolie","cat":"Vetten & oliën","moment":["ontbijt","avond"],
     "portie":10,"portie_label":"1 el","gi":0,
     "kcal":862,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":0,"vet":100,"verz":87.0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    # ── SAUZEN & SPREADS ──────────────────────────────────────────────────────
    {"naam":"Pindakaas naturel","cat":"Sauzen & spreads","moment":["ontbijt","tussendoor"],
     "portie":20,"portie_label":"1 el","gi":14,
     "kcal":594,"kh":20,"suikers":9,"toegev_suikers":0,"vezels":6,"eiwit":25,"vet":50,"verz":10.0,
     "natrium":410,"kalium":705,"calcium":49,"ijzer":1.9,"magnesium":154,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Amandelboter","cat":"Sauzen & spreads","moment":["ontbijt","tussendoor"],
     "portie":20,"portie_label":"1 el","gi":0,
     "kcal":614,"kh":19,"suikers":5,"toegev_suikers":0,"vezels":10,"eiwit":21,"vet":56,"verz":4.0,
     "natrium":5,"kalium":740,"calcium":264,"ijzer":3.7,"magnesium":270,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Hummus","cat":"Peulvruchten","moment":["lunch","tussendoor"],
     "portie":50,"portie_label":"2 el","gi":6,
     "kcal":177,"kh":14,"suikers":1,"toegev_suikers":0,"vezels":6,"eiwit":8,"vet":10,"verz":1.0,
     "natrium":421,"kalium":228,"calcium":38,"ijzer":2.4,"magnesium":35,"vitc":3,"vitd":0,"vitb12":0,"omega3":0.3},
    {"naam":"Honing","cat":"Sauzen & spreads","moment":["ontbijt"],
     "portie":15,"portie_label":"1 el","gi":58,
     "kcal":304,"kh":82,"suikers":82,"toegev_suikers":82,"toegev_suikers":82,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":4,"kalium":52,"calcium":6,"ijzer":0.4,"magnesium":2,"vitc":1,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Tomatensaus","cat":"Sauzen & spreads","moment":["lunch","avond"],
     "portie":100,"portie_label":"3 el","gi":35,
     "kcal":72,"kh":12,"suikers":9,"toegev_suikers":8,"toegev_suikers":8,"vezels":2,"eiwit":2,"vet":2,"verz":0.3,
     "natrium":590,"kalium":400,"calcium":20,"ijzer":0.7,"magnesium":20,"vitc":15,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Pesto groen","cat":"Sauzen & spreads","moment":["lunch","avond"],
     "portie":20,"portie_label":"1 el","gi":0,
     "kcal":490,"kh":5,"suikers":2,"vezels":2,"eiwit":8,"vet":49,"verz":9.0,
     "natrium":700,"kalium":200,"calcium":200,"ijzer":2.0,"magnesium":50,"vitc":5,"vitd":0,"vitb12":0,"omega3":0.4},

    # ── DRANKEN ───────────────────────────────────────────────────────────────
    {"naam":"Water","cat":"Dranken","moment":["ontbijt","lunch","avond","tussendoor"],
     "portie":250,"portie_label":"1 glas","gi":0,
     "kcal":0,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Koffie zwart","cat":"Dranken","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"1 kopje","gi":0,
     "kcal":2,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":2,"kalium":92,"calcium":2,"ijzer":0.1,"magnesium":6,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Groene thee","cat":"Dranken","moment":["tussendoor","ontbijt"],
     "portie":200,"portie_label":"1 glas","gi":0,
     "kcal":1,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":0,"kalium":21,"calcium":2,"ijzer":0.1,"magnesium":3,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Sinaasappelsap vers","cat":"Dranken","moment":["ontbijt"],
     "portie":150,"portie_label":"1 glas","gi":50,
     "kcal":45,"kh":10,"suikers":9,"toegev_suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":200,"calcium":11,"ijzer":0.2,"magnesium":11,"vitc":50,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Kokoswater","cat":"Dranken","moment":["tussendoor"],
     "portie":250,"portie_label":"1 glas","gi":54,
     "kcal":19,"kh":4,"suikers":4,"toegev_suikers":0,"vezels":0,"eiwit":1,"vet":0,"verz":0,
     "natrium":105,"kalium":250,"calcium":24,"ijzer":0.3,"magnesium":25,"vitc":2,"vitd":0,"vitb12":0,"omega3":0},

    # ── SPORTVOEDING ──────────────────────────────────────────────────────────
    {"naam":"Energiegel standaard","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":40,"portie_label":"1 gel","gi":80,
     "kcal":100,"kh":25,"suikers":17,"toegev_suikers":15,"toegev_suikers":15,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":55,"kalium":30,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Sportdrank isotoon","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":500,"portie_label":"1 bidon","gi":70,
     "kcal":140,"kh":35,"suikers":30,"toegev_suikers":6,"toegev_suikers":6,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":230,"kalium":80,"calcium":0,"ijzer":0,"magnesium":10,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Whey proteïne","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":30,"portie_label":"1 schep","gi":20,
     "kcal":380,"kh":6,"suikers":4,"vezels":0,"eiwit":80,"vet":4,"verz":1.0,
     "natrium":200,"kalium":200,"calcium":200,"ijzer":0.5,"magnesium":50,"vitc":0,"vitd":0,"vitb12":1.0,"omega3":0.2},
    {"naam":"Recovery shake","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":80,"portie_label":"1 portie","gi":55,
     "kcal":350,"kh":50,"suikers":20,"toegev_suikers":18,"toegev_suikers":18,"vezels":2,"eiwit":25,"vet":5,"verz":1.0,
     "natrium":300,"kalium":300,"calcium":300,"ijzer":3.0,"magnesium":80,"vitc":20,"vitd":1.0,"vitb12":1.5,"omega3":0.3},
    {"naam":"Energiereep","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":65,"portie_label":"1 reep","gi":65,
     "kcal":380,"kh":60,"suikers":30,"toegev_suikers":25,"vezels":3,"eiwit":10,"vet":10,"verz":3.0,
     "natrium":200,"kalium":200,"calcium":100,"ijzer":2.0,"magnesium":40,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    # ── NIEUWE PRODUCTEN ─────────────────────────────────────────────────────
    {"naam":"Goudse kaas 48+","cat":"Zuivel","moment":["lunch","avond"],
     "portie":30,"portie_label":"1 plak","gi":None,
     "kcal":356,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":26,"vet":28,"verz":18,
     "natrium":810,"kalium":100,"calcium":820,"ijzer":0.2,"magnesium":11,"vitc":0,"vitd":0.2,"vitb12":1.5,"omega3":0.3},

    {"naam":"Bruin brood","cat":"Granen & brood","moment":["ontbijt","lunch"],
     "portie":35,"portie_label":"1 snede","gi":65,
     "kcal":233,"kh":42,"suikers":3,"toegev_suikers":1,"vezels":5,"eiwit":8,"vet":2,"verz":0.4,
     "natrium":430,"kalium":220,"calcium":80,"ijzer":2.0,"magnesium":40,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Pasta wit gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":200,"portie_label":"1 portie","gi":50,
     "kcal":131,"kh":26,"suikers":0.5,"toegev_suikers":0,"vezels":1.8,"eiwit":5,"vet":1,"verz":0.2,
     "natrium":1,"kalium":45,"calcium":7,"ijzer":0.5,"magnesium":18,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Cracker volkoren","cat":"Granen & brood","moment":["snack","lunch"],
     "portie":11,"portie_label":"1 cracker","gi":45,
     "kcal":409,"kh":65,"suikers":2,"toegev_suikers":0,"vezels":8,"eiwit":10,"vet":11,"verz":1.5,
     "natrium":600,"kalium":280,"calcium":40,"ijzer":3.0,"magnesium":70,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.2},

    {"naam":"Couscous rauw","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":75,"portie_label":"1 droge portie","gi":65,
     "kcal":357,"kh":72,"suikers":0.3,"toegev_suikers":0,"vezels":5,"eiwit":13,"vet":2,"verz":0.3,
     "natrium":10,"kalium":180,"calcium":24,"ijzer":1.4,"magnesium":44,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Muesli naturel","cat":"Granen & brood","moment":["ontbijt"],
     "portie":60,"portie_label":"1 portie","gi":55,
     "kcal":364,"kh":59,"suikers":12,"toegev_suikers":2,"vezels":8,"eiwit":10,"vet":7,"verz":1.2,
     "natrium":50,"kalium":350,"calcium":50,"ijzer":3.5,"magnesium":90,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.2},

    {"naam":"Cruesli","cat":"Granen & brood","moment":["ontbijt"],
     "portie":60,"portie_label":"1 portie","gi":60,
     "kcal":430,"kh":65,"suikers":22,"toegev_suikers":18,"vezels":6,"eiwit":8,"vet":14,"verz":2,
     "natrium":80,"kalium":280,"calcium":40,"ijzer":3.0,"magnesium":70,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.3},

    {"naam":"Pangasius gebakken","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":None,
     "kcal":105,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":19,"vet":3,"verz":0.8,
     "natrium":90,"kalium":340,"calcium":18,"ijzer":0.4,"magnesium":25,"vitc":0,"vitd":1.5,"vitb12":1.8,"omega3":0.4},

    {"naam":"Kalkoenfilet gebakken","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 stuk","gi":None,
     "kcal":157,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":30,"vet":3,"verz":0.9,
     "natrium":65,"kalium":340,"calcium":20,"ijzer":1.0,"magnesium":28,"vitc":0,"vitd":0.2,"vitb12":0.8,"omega3":0.1},

    {"naam":"Rundergehakt normaal","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":125,"portie_label":"1 portie","gi":None,
     "kcal":213,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":19,"vet":15,"verz":6,
     "natrium":75,"kalium":320,"calcium":12,"ijzer":2.2,"magnesium":20,"vitc":0,"vitd":0.1,"vitb12":2.0,"omega3":0.2},

    {"naam":"Groentenmix rauw","cat":"Groenten","moment":["lunch","avond","snack"],
     "portie":100,"portie_label":"1 portie","gi":15,
     "kcal":35,"kh":5,"suikers":3,"toegev_suikers":0,"vezels":3,"eiwit":2,"vet":0.3,"verz":0,
     "natrium":40,"kalium":350,"calcium":45,"ijzer":1.2,"magnesium":22,"vitc":40,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Groentenmix warm","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 portie","gi":15,
     "kcal":45,"kh":6,"suikers":4,"toegev_suikers":0,"vezels":4,"eiwit":3,"vet":0.5,"verz":0.1,
     "natrium":30,"kalium":380,"calcium":55,"ijzer":1.5,"magnesium":25,"vitc":25,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Witloof","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 stronkjes","gi":15,
     "kcal":17,"kh":3,"suikers":2,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":10,"kalium":270,"calcium":25,"ijzer":0.5,"magnesium":10,"vitc":5,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Ui","cat":"Groenten","moment":["lunch","avond"],
     "portie":80,"portie_label":"1 ui","gi":10,
     "kcal":40,"kh":9,"suikers":4,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":4,"kalium":157,"calcium":23,"ijzer":0.2,"magnesium":10,"vitc":7,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Prei","cat":"Groenten","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 stuk","gi":15,
     "kcal":29,"kh":6,"suikers":2,"toegev_suikers":0,"vezels":2,"eiwit":2,"vet":0,"verz":0,
     "natrium":20,"kalium":180,"calcium":59,"ijzer":1.0,"magnesium":14,"vitc":12,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Bloem","cat":"Granen & brood","moment":["avond"],
     "portie":20,"portie_label":"2 el","gi":70,
     "kcal":364,"kh":76,"suikers":0,"toegev_suikers":0,"vezels":3,"eiwit":10,"vet":1,"verz":0.2,
     "natrium":2,"kalium":107,"calcium":15,"ijzer":1.0,"magnesium":22,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Mosselen","cat":"Vlees & vis","moment":["avond"],
     "portie":300,"portie_label":"1 portie","gi":None,
     "kcal":86,"kh":4,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":12,"vet":2,"verz":0.4,
     "natrium":286,"kalium":320,"calcium":26,"ijzer":4.0,"magnesium":34,"vitc":0,"vitd":0,"vitb12":12.0,"omega3":0.5},

    {"naam":"Braadworst","cat":"Vlees & vis","moment":["avond"],
     "portie":150,"portie_label":"1 worst","gi":None,
     "kcal":285,"kh":2,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":14,"vet":25,"verz":10,
     "natrium":800,"kalium":200,"calcium":10,"ijzer":1.2,"magnesium":15,"vitc":0,"vitd":0.1,"vitb12":1.0,"omega3":0.2},

    {"naam":"Groentensoep","cat":"Groenten","moment":["lunch","avond"],
     "portie":300,"portie_label":"1 kom","gi":30,
     "kcal":35,"kh":5,"suikers":3,"toegev_suikers":0,"vezels":2,"eiwit":2,"vet":1,"verz":0.1,
     "natrium":480,"kalium":320,"calcium":25,"ijzer":0.6,"magnesium":18,"vitc":8,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Chocolade puur 72%","cat":"Overige","moment":["snack"],
     "portie":25,"portie_label":"2 blokjes","gi":25,
     "kcal":546,"kh":46,"suikers":25,"toegev_suikers":23,"vezels":11,"eiwit":5,"vet":35,"verz":21,
     "natrium":8,"kalium":500,"calcium":60,"ijzer":4.5,"magnesium":140,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Snoepmix","cat":"Overige","moment":["snack"],
     "portie":40,"portie_label":"1 zakje","gi":80,
     "kcal":350,"kh":85,"suikers":70,"toegev_suikers":68,"vezels":0,"eiwit":5,"vet":1,"verz":0.5,
     "natrium":50,"kalium":10,"calcium":5,"ijzer":0.1,"magnesium":2,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Pils bier","cat":"Dranken","moment":["avond"],
     "portie":250,"portie_label":"1 glas","gi":None,
     "kcal":43,"kh":3.6,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":0.5,"vet":0,"verz":0,
     "natrium":10,"kalium":30,"calcium":4,"ijzer":0,"magnesium":6,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Wijn rood","cat":"Dranken","moment":["avond"],
     "portie":150,"portie_label":"1 glas","gi":None,
     "kcal":85,"kh":2.6,"suikers":0.6,"toegev_suikers":0,"vezels":0,"eiwit":0.1,"vet":0,"verz":0,
     "natrium":5,"kalium":115,"calcium":8,"ijzer":0.5,"magnesium":12,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Rode bonen gekookt","cat":"Peulvruchten","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 opscheplepel","gi":24,
     "kcal":127,"kh":22,"suikers":0.3,"toegev_suikers":0,"vezels":7,"eiwit":9,"vet":0.5,"verz":0.1,
     "natrium":2,"kalium":405,"calcium":40,"ijzer":2.9,"magnesium":45,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Zwarte bonen gekookt","cat":"Peulvruchten","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 opscheplepel","gi":30,
     "kcal":132,"kh":24,"suikers":0.3,"toegev_suikers":0,"vezels":8,"eiwit":9,"vet":0.5,"verz":0.1,
     "natrium":1,"kalium":355,"calcium":27,"ijzer":2.1,"magnesium":60,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.2},

    {"naam":"Edamame","cat":"Peulvruchten","moment":["snack","lunch"],
     "portie":100,"portie_label":"1 portie","gi":18,
     "kcal":122,"kh":10,"suikers":2,"toegev_suikers":0,"vezels":5,"eiwit":11,"vet":5,"verz":0.7,
     "natrium":6,"kalium":436,"calcium":60,"ijzer":2.3,"magnesium":64,"vitc":9,"vitd":0,"vitb12":0,"omega3":0.3},

    {"naam":"Spliterwten gekookt","cat":"Peulvruchten","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 opscheplepel","gi":22,
     "kcal":118,"kh":21,"suikers":2.8,"toegev_suikers":0,"vezels":8,"eiwit":8,"vet":0.4,"verz":0.1,
     "natrium":2,"kalium":362,"calcium":27,"ijzer":1.3,"magnesium":36,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Tofu naturel","cat":"Sojaproducten","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 portie","gi":15,
     "kcal":76,"kh":1.9,"suikers":0.7,"toegev_suikers":0,"vezels":0.3,"eiwit":8,"vet":4.8,"verz":0.7,
     "natrium":7,"kalium":150,"calcium":350,"ijzer":1.6,"magnesium":30,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.3},

    {"naam":"Tempeh","cat":"Sojaproducten","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 portie","gi":15,
     "kcal":193,"kh":9,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":19,"vet":11,"verz":2.2,
     "natrium":9,"kalium":412,"calcium":111,"ijzer":2.7,"magnesium":81,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.2},

    {"naam":"Sojayoghurt","cat":"Sojaproducten","moment":["ontbijt","snack"],
     "portie":150,"portie_label":"1 portie","gi":18,
     "kcal":62,"kh":3.8,"suikers":3.5,"toegev_suikers":0,"vezels":0,"eiwit":3.9,"vet":3.4,"verz":0.5,
     "natrium":40,"kalium":138,"calcium":120,"ijzer":0.5,"magnesium":15,"vitc":0,"vitd":1.0,"vitb12":0.4,"omega3":0.1},

    {"naam":"Sojamelk ongezoet","cat":"Sojaproducten","moment":["ontbijt","snack"],
     "portie":250,"portie_label":"1 glas","gi":30,
     "kcal":33,"kh":1.3,"suikers":0.5,"toegev_suikers":0,"vezels":0,"eiwit":3.3,"vet":1.8,"verz":0.3,
     "natrium":45,"kalium":118,"calcium":120,"ijzer":0.5,"magnesium":19,"vitc":0,"vitd":1.0,"vitb12":0.4,"omega3":0.4},
    # ── ONTBREKENDE PRODUCTEN ─────────────────────────────────────────────────
    {"naam":"Ei groot","cat":"Eieren","moment":["ontbijt","lunch"],
     "portie":60,"portie_label":"1 ei (L)","gi":0,
     "kcal":155,"kh":1,"suikers":1,"toegev_suikers":0,"vezels":0,"eiwit":13,"vet":11,"verz":3.0,
     "natrium":124,"kalium":130,"calcium":50,"ijzer":1.8,"magnesium":12,"vitc":0,"vitd":2.0,"vitb12":0.9,"omega3":0.1},

    {"naam":"Granola","cat":"Granen & brood","moment":["ontbijt"],
     "portie":45,"portie_label":"3 el","gi":55,
     "kcal":450,"kh":65,"suikers":20,"toegev_suikers":15,"vezels":5,"eiwit":9,"vet":16,"verz":2.5,
     "natrium":50,"kalium":280,"calcium":40,"ijzer":3.0,"magnesium":65,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.2},

    {"naam":"Pannenkoek","cat":"Granen & brood","moment":["ontbijt"],
     "portie":80,"portie_label":"1 pannenkoek","gi":67,
     "kcal":227,"kh":32,"suikers":4,"toegev_suikers":2,"vezels":1,"eiwit":7,"vet":8,"verz":2.0,
     "natrium":250,"kalium":120,"calcium":80,"ijzer":1.0,"magnesium":12,"vitc":0,"vitd":0.3,"vitb12":0.4,"omega3":0.1},

    {"naam":"Appelmoes","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":120,"portie_label":"3 el","gi":40,
     "kcal":68,"kh":17,"suikers":14,"toegev_suikers":5,"vezels":1,"eiwit":0,"vet":0,"verz":0,
     "natrium":2,"kalium":90,"calcium":5,"ijzer":0.1,"magnesium":4,"vitc":3,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Pindakaas","cat":"Noten & zaden","moment":["ontbijt","tussendoor"],
     "portie":20,"portie_label":"1 el","gi":14,
     "kcal":594,"kh":20,"suikers":9,"toegev_suikers":3,"vezels":6,"eiwit":25,"vet":50,"verz":10.0,
     "natrium":410,"kalium":705,"calcium":49,"ijzer":1.9,"magnesium":154,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Komkommer","cat":"Groenten","moment":["lunch","tussendoor"],
     "portie":100,"portie_label":"5 schijfjes","gi":15,
     "kcal":15,"kh":3,"suikers":2,"toegev_suikers":0,"vezels":1,"eiwit":1,"vet":0,"verz":0,
     "natrium":2,"kalium":147,"calcium":16,"ijzer":0.3,"magnesium":13,"vitc":3,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Kipfilet","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":120,"portie_label":"1 filet","gi":0,
     "kcal":165,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":31,"vet":4,"verz":1.0,
     "natrium":74,"kalium":370,"calcium":12,"ijzer":1.0,"magnesium":28,"vitc":0,"vitd":0.1,"vitb12":0.3,"omega3":0.1},

    {"naam":"Sla gemengd","cat":"Groenten","moment":["lunch","avond"],
     "portie":50,"portie_label":"1 handjevol","gi":10,
     "kcal":15,"kh":2,"suikers":1,"toegev_suikers":0,"vezels":1,"eiwit":1,"vet":0,"verz":0,
     "natrium":10,"kalium":200,"calcium":30,"ijzer":0.8,"magnesium":10,"vitc":10,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Mayonaise","cat":"Sauzen & spreads","moment":["lunch","avond"],
     "portie":15,"portie_label":"1 el","gi":0,
     "kcal":680,"kh":2,"suikers":1,"toegev_suikers":1,"vezels":0,"eiwit":1,"vet":75,"verz":6.0,
     "natrium":500,"kalium":20,"calcium":5,"ijzer":0.1,"magnesium":2,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.5},

    {"naam":"Broccoli","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":10,
     "kcal":34,"kh":7,"suikers":2,"toegev_suikers":0,"vezels":3,"eiwit":3,"vet":0,"verz":0,
     "natrium":33,"kalium":316,"calcium":47,"ijzer":0.7,"magnesium":21,"vitc":65,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Wortel","cat":"Groenten","moment":["lunch","avond"],
     "portie":80,"portie_label":"1 wortel","gi":35,
     "kcal":41,"kh":10,"suikers":5,"toegev_suikers":0,"vezels":3,"eiwit":1,"vet":0,"verz":0,
     "natrium":69,"kalium":320,"calcium":33,"ijzer":0.3,"magnesium":12,"vitc":6,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Sojasaus","cat":"Sauzen & spreads","moment":["lunch","avond"],
     "portie":15,"portie_label":"1 el","gi":0,
     "kcal":60,"kh":6,"suikers":2,"toegev_suikers":1,"vezels":0,"eiwit":6,"vet":0,"verz":0,
     "natrium":4000,"kalium":200,"calcium":10,"ijzer":0.5,"magnesium":20,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Olijfolie","cat":"Vetten & oliën","moment":["lunch","avond"],
     "portie":10,"portie_label":"1 el","gi":0,
     "kcal":884,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":0,"vet":100,"verz":14.0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0.1,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.8},

    {"naam":"Wrap","cat":"Granen & brood","moment":["lunch"],
     "portie":60,"portie_label":"1 wrap","gi":65,
     "kcal":306,"kh":52,"suikers":3,"toegev_suikers":1,"vezels":3,"eiwit":8,"vet":7,"verz":1.5,
     "natrium":450,"kalium":120,"calcium":80,"ijzer":2.0,"magnesium":20,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Kalkoenfilet","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":120,"portie_label":"1 stuk","gi":0,
     "kcal":157,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":30,"vet":3,"verz":0.9,
     "natrium":65,"kalium":340,"calcium":20,"ijzer":1.0,"magnesium":28,"vitc":0,"vitd":0.2,"vitb12":0.8,"omega3":0.1},

    {"naam":"Haring","cat":"Vlees & vis","moment":["lunch"],
     "portie":100,"portie_label":"1 haring","gi":0,
     "kcal":158,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":18,"vet":9,"verz":2.0,
     "natrium":430,"kalium":330,"calcium":35,"ijzer":1.1,"magnesium":30,"vitc":0,"vitd":4.5,"vitb12":6.0,"omega3":1.6},

    {"naam":"Stokbrood","cat":"Granen & brood","moment":["lunch"],
     "portie":60,"portie_label":"2 sneden","gi":72,
     "kcal":270,"kh":53,"suikers":3,"toegev_suikers":1,"vezels":2,"eiwit":9,"vet":2,"verz":0.4,
     "natrium":520,"kalium":100,"calcium":20,"ijzer":1.5,"magnesium":15,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Zalm","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":0,
     "kcal":208,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":20,"vet":13,"verz":3.0,
     "natrium":59,"kalium":440,"calcium":15,"ijzer":0.5,"magnesium":27,"vitc":0,"vitd":9.0,"vitb12":3.0,"omega3":2.3},

    {"naam":"Couscous gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":65,
     "kcal":112,"kh":23,"suikers":0,"toegev_suikers":0,"vezels":1,"eiwit":4,"vet":0,"verz":0,
     "natrium":5,"kalium":58,"calcium":8,"ijzer":0.4,"magnesium":13,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Citroen","cat":"Fruit","moment":["lunch","avond"],
     "portie":30,"portie_label":"1/2 citroen sap","gi":20,
     "kcal":29,"kh":9,"suikers":3,"toegev_suikers":0,"vezels":3,"eiwit":1,"vet":0,"verz":0,
     "natrium":2,"kalium":138,"calcium":26,"ijzer":0.6,"magnesium":8,"vitc":53,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Spinazie","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":15,
     "kcal":23,"kh":4,"suikers":0,"toegev_suikers":0,"vezels":2,"eiwit":3,"vet":0,"verz":0,
     "natrium":79,"kalium":466,"calcium":99,"ijzer":2.7,"magnesium":87,"vitc":28,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Spek","cat":"Vlees & vis","moment":["ontbijt","avond"],
     "portie":30,"portie_label":"2 reepjes","gi":0,
     "kcal":541,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":37,"vet":43,"verz":16.0,
     "natrium":1700,"kalium":420,"calcium":10,"ijzer":1.0,"magnesium":20,"vitc":0,"vitd":0,"vitb12":1.0,"omega3":0.2},

    {"naam":"Varkenshaas","cat":"Vlees & vis","moment":["avond"],
     "portie":150,"portie_label":"1 stuk","gi":0,
     "kcal":143,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":22,"vet":6,"verz":2.0,
     "natrium":54,"kalium":380,"calcium":6,"ijzer":1.0,"magnesium":25,"vitc":0,"vitd":0.1,"vitb12":0.8,"omega3":0.1},

    {"naam":"Erwten","cat":"Groenten","moment":["avond"],
     "portie":100,"portie_label":"3 el","gi":48,
     "kcal":81,"kh":14,"suikers":6,"toegev_suikers":0,"vezels":5,"eiwit":5,"vet":0,"verz":0,
     "natrium":5,"kalium":244,"calcium":25,"ijzer":1.5,"magnesium":33,"vitc":14,"vitd":0,"vitb12":0,"omega3":0.1},

    {"naam":"Makreel","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":0,
     "kcal":205,"kh":0,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":19,"vet":14,"verz":3.0,
     "natrium":700,"kalium":330,"calcium":12,"ijzer":1.0,"magnesium":30,"vitc":0,"vitd":5.0,"vitb12":7.0,"omega3":2.2},

    {"naam":"Selder","cat":"Groenten","moment":["lunch","avond"],
     "portie":80,"portie_label":"2 stengels","gi":15,
     "kcal":16,"kh":3,"suikers":2,"toegev_suikers":0,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":80,"kalium":260,"calcium":40,"ijzer":0.2,"magnesium":11,"vitc":3,"vitd":0,"vitb12":0,"omega3":0},

    {"naam":"Worst","cat":"Vlees & vis","moment":["avond"],
     "portie":120,"portie_label":"1 worst","gi":0,
     "kcal":285,"kh":2,"suikers":0,"toegev_suikers":0,"vezels":0,"eiwit":14,"vet":25,"verz":10.0,
     "natrium":800,"kalium":200,"calcium":10,"ijzer":1.2,"magnesium":15,"vitc":0,"vitd":0.1,"vitb12":1.0,"omega3":0.2},

    {"naam":"Muesli","cat":"Granen & brood","moment":["ontbijt"],
     "portie":60,"portie_label":"1 portie","gi":55,
     "kcal":364,"kh":59,"suikers":12,"toegev_suikers":2,"vezels":8,"eiwit":10,"vet":7,"verz":1.2,
     "natrium":50,"kalium":350,"calcium":50,"ijzer":3.5,"magnesium":90,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.2},

]

CATEGORIE_OPTIES = [
    "Granen & brood","Zuivel","Eieren","Vlees & vis","Groenten","Fruit",
    "Peulvruchten","Sojaproducten","Noten & zaden","Vetten & oliën","Sauzen & spreads","Dranken","Sportvoeding","Overige"
]


# ── UITGEBREID PRODUCT FORMULIER (manueel + scan) ────────────────────────────

EENHEID_OPTIES = [
    ("gram (g)", 1.0),
    ("stuk", None),      # gebruiker geeft gram per stuk op
    ("snede", None),
    ("plakje", None),
    ("eetlepel (15ml)", 15.0),
    ("koffielepel (5ml)", 5.0),
    ("kopje (150ml)", 150.0),
    ("glas (200ml)", 200.0),
    ("bidon (500ml)", 500.0),
    ("opscheplepel (75g)", 75.0),
    ("handjevol (25g)", 25.0),
    ("portie", None),
    ("ml", 1.0),
]


def _product_formulier(prefix: str, defaults: dict = None) -> dict:
    """Universeel product invoerformulier — zelfde voor manueel en scan."""
    d = defaults or {}

    _sectie("PRODUCTINFO", "#22c55e")
    p1, p2 = st.columns(2)
    with p1:
        naam = st.text_input("Productnaam *",
            value=d.get("naam",""), key=f"{prefix}_naam",
            placeholder="bijv. Havermout Quaker")
    with p2:
        cat_idx = CATEGORIE_OPTIES.index(d.get("categorie","Overige")) \
            if d.get("categorie") in CATEGORIE_OPTIES else len(CATEGORIE_OPTIES)-1
        categorie = st.selectbox("Categorie *", CATEGORIE_OPTIES,
            index=cat_idx, key=f"{prefix}_cat")

    # Portie instelling
    _sectie("PORTIE & EENHEID", "#22c55e")
    eu1, eu2, eu3 = st.columns(3)
    with eu1:
        eenheid_namen = [e[0] for e in EENHEID_OPTIES]
        eenheid = st.selectbox("Eenheid",
            eenheid_namen, key=f"{prefix}_eenheid")
        gram_factor = dict(EENHEID_OPTIES).get(eenheid)
    with eu2:
        portie_hoev = st.number_input(
            "Hoeveelheid per portie",
            0.1, 2000.0,
            float(d.get("portie_g", 100)),
            0.5, key=f"{prefix}_portie_hoev")
    with eu3:
        if gram_factor:
            portie_g = round(portie_hoev * gram_factor, 1)
            st.markdown(
                f'<div style="font-size:0.75rem;color:#22c55e;padding-top:28px;">'
                f'= {portie_g}g</div>', unsafe_allow_html=True)
        else:
            portie_g = portie_hoev
            st.markdown(
                f'<div style="font-size:0.75rem;color:#64748b;padding-top:28px;">'
                f'{portie_g}g per stuk/portie</div>', unsafe_allow_html=True)
    portie_label = f"{portie_hoev} {eenheid}"

    # Macros per 100g
    _sectie("ENERGIE & MACROS per 100g", "#22c55e")
    m1, m2, m3 = st.columns(3)
    with m1:
        kcal = st.number_input("Energie (kcal)", 0.0, 900.0,
            float(d.get("kcal_100g",0) or 0), 1.0, key=f"{prefix}_kcal")
    with m2:
        kh = st.number_input("Koolhydraten (g)", 0.0, 100.0,
            float(d.get("kh_100g",0) or 0), 0.1, key=f"{prefix}_kh")
    with m3:
        suikers = st.number_input("waarvan toegevoegde suikers (g)", 0.0, 100.0,
            float(d.get("suikers_100g",0) or 0), 0.1, key=f"{prefix}_suikers")

    m4, m5, m6 = st.columns(3)
    with m4:
        vezels = st.number_input("Vezels (g)", 0.0, 100.0,
            float(d.get("vezels_100g",0) or 0), 0.1, key=f"{prefix}_vezels")
    with m5:
        eiwit = st.number_input("Eiwit (g)", 0.0, 100.0,
            float(d.get("eiwit_100g",0) or 0), 0.1, key=f"{prefix}_eiwit")
    with m6:
        vet = st.number_input("Vetten totaal (g)", 0.0, 100.0,
            float(d.get("vet_100g",0) or 0), 0.1, key=f"{prefix}_vet")

    m7, m8 = st.columns(2)
    with m7:
        verz = st.number_input("waarvan verzadigd (g)", 0.0, 100.0,
            float(d.get("verzadigd_100g",0) or 0), 0.1, key=f"{prefix}_verz")
    with m8:
        natrium = st.number_input("Natrium (mg)", 0.0, 5000.0,
            float(d.get("natrium_100g",0) or 0), 1.0, key=f"{prefix}_natrium")

    # Extra voedingsstoffen
    _sectie("MINERALEN & VITAMINEN per 100g", "#22c55e")
    st.markdown(
        '<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">'
        'Optioneel — vul in wat op het etiket staat.</div>',
        unsafe_allow_html=True)

    v1, v2, v3, v4 = st.columns(4)
    with v1:
        kalium = st.number_input("Kalium (mg)", 0.0, 5000.0,
            float(d.get("kalium_100g",0) or 0), 1.0, key=f"{prefix}_kalium")
        vitc = st.number_input("Vit C (mg)", 0.0, 1000.0,
            float(d.get("vitc_100g",0) or 0), 0.1, key=f"{prefix}_vitc")
    with v2:
        calcium = st.number_input("Calcium (mg)", 0.0, 2000.0,
            float(d.get("calcium_100g",0) or 0), 1.0, key=f"{prefix}_calcium")
        vitd = st.number_input("Vit D (µg)", 0.0, 100.0,
            float(d.get("vitd_100g",0) or 0), 0.1, key=f"{prefix}_vitd")
    with v3:
        ijzer = st.number_input("IJzer (mg)", 0.0, 50.0,
            float(d.get("ijzer_100g",0) or 0), 0.1, key=f"{prefix}_ijzer")
        vitb12 = st.number_input("Vit B12 (µg)", 0.0, 100.0,
            float(d.get("vitb12_100g",0) or 0), 0.1, key=f"{prefix}_vitb12")
    with v4:
        magnesium = st.number_input("Magnesium (mg)", 0.0, 1000.0,
            float(d.get("magnesium_100g",0) or 0), 1.0, key=f"{prefix}_magnesium")
        omega3 = st.number_input("Omega-3 (g)", 0.0, 20.0,
            float(d.get("omega3_100g",0) or 0), 0.1, key=f"{prefix}_omega3")

    # GI
    gi_col, notitie_col = st.columns(2)
    with gi_col:
        gi = st.number_input("Glycemische index (GI)", 0, 100,
            int(d.get("gi",0) or 0), 1, key=f"{prefix}_gi",
            help="0 = onbekend | <55 laag | 55-69 matig | ≥70 hoog")
    with notitie_col:
        notitie = st.text_input("Notitie (optioneel)",
            value=d.get("notitie","") or "",
            key=f"{prefix}_notitie",
            placeholder="bijv. biologisch, glutenvrij...")

    # Live preview per portie
    if kcal > 0 or kh > 0 or eiwit > 0:
        f = portie_g / 100
        st.markdown(
            f'<div style="background:#1e293b;border-radius:8px;padding:10px 14px;margin-top:8px;">'
            f'<div style="font-size:0.65rem;color:#64748b;margin-bottom:6px;">PREVIEW PER PORTIE ({portie_label})</div>'
            f'<div style="display:flex;gap:16px;flex-wrap:wrap;">'
            f'<span style="font-size:0.85rem;font-weight:700;color:#f97316;">{round(kcal*f)}kcal</span>'
            f'<span style="font-size:0.8rem;color:#22c55e;">{round(kh*f,1)}g KH</span>'
            f'<span style="font-size:0.8rem;color:#3b82f6;">{round(eiwit*f,1)}g eiwit</span>'
            f'<span style="font-size:0.8rem;color:#8b5cf6;">{round(vet*f,1)}g vet</span>'
            f'<span style="font-size:0.8rem;color:#64748b;">{round(vezels*f,1)}g vezels</span>'
            f'{"<span style=\"font-size:0.75rem;color:#fbbf24;\">GI " + str(gi) + "</span>" if gi > 0 else ""}'
            f'</div></div>',
            unsafe_allow_html=True)

    favoriet = st.checkbox("⭐ Toevoegen aan favorieten", key=f"{prefix}_fav",
        value=bool(d.get("favoriet",False)))

    return {
        "naam":           naam.strip() if naam else "",
        "categorie":      categorie,
        "portie_g":       portie_g,
        "portie_label":   portie_label,
        "kcal_100g":      kcal or None,
        "kh_100g":        kh or None,
        "suikers_100g":   suikers or None,
        "vezels_100g":    vezels or None,
        "eiwit_100g":     eiwit or None,
        "vet_100g":       vet or None,
        "verzadigd_100g": verz or None,
        "natrium_100g":   natrium or None,
        "kalium_100g":    kalium or None,
        "calcium_100g":   calcium or None,
        "ijzer_100g":     ijzer or None,
        "magnesium_100g": magnesium or None,
        "vitc_100g":      vitc or None,
        "vitd_100g":      vitd or None,
        "vitb12_100g":    vitb12 or None,
        "omega3_100g":    omega3 or None,
        "gi":             gi or None,
        "notitie":        notitie.strip() if notitie else None,
        "favoriet":       favoriet,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BIBLIOTHEEK SUPABASE FUNCTIES
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30)
def _laad_bibliotheek_raw(user_id: str) -> list:
    try:
        r = _get_supabase().table("fuelc_bibliotheek").select("*")            .eq("user_id", user_id).order("naam").execute()
        return r.data or []
    except Exception as e:
        print(f"Fout bibliotheek: {e}")
        return []

def _laad_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    data = _laad_bibliotheek_raw(user_id)
    if zoek:
        zoek_l = zoek.lower()
        data = [p for p in data if zoek_l in (p.get("naam") or "").lower()]
    if categorie and categorie != "Alle":
        data = [p for p in data if p.get("categorie","") == categorie]
    return data

@st.cache_data(ttl=30)
def _laad_gecombineerde_bibliotheek_raw(user_id: str) -> list:
    eigen = _laad_bibliotheek_raw(user_id)
    eigen_namen = {p["naam"].lower() for p in eigen}
    databank = []
    for p in VOEDSEL_DB:
        if p["naam"].lower() not in eigen_namen:
            databank.append({
                "id": f"db_{p['naam']}", "naam": p["naam"],
                "categorie": p["cat"], "bron": "databank",
                "portie_g": p["portie"], "portie_label": p.get("portie_label", f"{p['portie']}g"),
                "kcal_100g": p["kcal"], "kh_100g": p["kh"],
                "suikers_100g": p.get("toegev_suikers", 0), "eiwit_100g": p["eiwit"],
                "vet_100g": p["vet"], "verzadigd_100g": p["verz"],
                "vezels_100g": p["vezels"], "natrium_100g": p["natrium"],
                "kalium_100g": p.get("kalium"), "calcium_100g": p.get("calcium"),
                "ijzer_100g": p.get("ijzer"), "magnesium_100g": p.get("magnesium"),
                "vitc_100g": p.get("vitc"), "vitd_100g": p.get("vitd"),
                "vitb12_100g": p.get("vitb12"), "omega3_100g": p.get("omega3"),
                "gi": p.get("gi"), "favoriet": False,
            })
    return eigen + databank

def _laad_gecombineerde_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    data = _laad_gecombineerde_bibliotheek_raw(user_id)
    if zoek:
        zoek_l = zoek.lower()
        data = [p for p in data if zoek_l in p["naam"].lower()]
    if categorie and categorie != "Alle":
        data = [p for p in data if p.get("categorie","") == categorie]
    return data

def _sla_product_op(user_id: str, product: dict) -> bool:
    try:
        product["user_id"] = user_id
        if "bron" not in product:
            product["bron"] = "manueel"
        _get_supabase().table("fuelc_bibliotheek").insert(product).execute()
        _laad_bibliotheek_raw.clear()
        _laad_gecombineerde_bibliotheek_raw.clear()
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False

def _update_product(product_id: str, data: dict) -> bool:
    try:
        _get_supabase().table("fuelc_bibliotheek").update(data).eq("id", product_id).execute()
        _laad_bibliotheek_raw.clear()
        _laad_gecombineerde_bibliotheek_raw.clear()
        return True
    except Exception as e:
        st.error(f"Fout updaten: {e}")
        return False

def _verwijder_product(product_id: str) -> bool:
    try:
        sb = _get_supabase()
        # Ontkoppel eerst dagboek items die naar dit product verwijzen
        sb.table("fuelc_dagboek").update({"product_id": None})\
          .eq("product_id", product_id).execute()
        # Dan verwijder het product
        sb.table("fuelc_bibliotheek").delete().eq("id", product_id).execute()
        _laad_bibliotheek_raw.clear()
        _laad_gecombineerde_bibliotheek_raw.clear()
        return True
    except Exception as e:
        st.error(f"Fout verwijderen: {e}")
        return False

# ─── COMMUNITY FUNCTIES ───────────────────────────────────────────────────────


def _laad_community_recepten() -> list:
    """Laad alle gedeelde recepten met scores en reacties."""
    try:
        r = _get_supabase().table("fuelc_recepten_eigen").select("*")\
            .eq("is_globaal", True).order("naam").execute()
        recepten = r.data or []

        # Laad scores
        if recepten:
            rec_ids = [r["id"] for r in recepten]
            scores_r = _get_supabase().table("fuelc_recept_scores").select("*")\
                .in_("recept_id", rec_ids).execute()
            scores = scores_r.data or []

            reacties_r = _get_supabase().table("fuelc_recept_reacties").select("*")\
                .in_("recept_id", rec_ids).order("created_at", desc=True).execute()
            reacties = reacties_r.data or []

            for rec in recepten:
                rec_scores = [s["score"] for s in scores if s["recept_id"] == rec["id"]]
                rec["gem_score"]   = round(sum(rec_scores)/len(rec_scores), 1) if rec_scores else 0
                rec["n_scores"]    = len(rec_scores)
                rec["reacties"]    = [rt for rt in reacties if rt["recept_id"] == rec["id"]]
                rec["n_reacties"]  = len(rec["reacties"])

        return recepten
    except Exception as e:
        print(f"Fout laden community: {e}")
        return []

def _sla_score_op(recept_id: str, user_id: str, score: int) -> bool:
    try:
        _get_supabase().table("fuelc_recept_scores").upsert({
            "recept_id": recept_id,
            "user_id":   user_id,
            "score":     score,
        }, on_conflict="recept_id,user_id").execute()
        return True
    except Exception as e:
        st.error(f"Fout score: {e}")
        return False

def _sla_reactie_op(recept_id: str, user_id: str, naam: str, bericht: str) -> bool:
    try:
        if not bericht.strip(): return False
        _get_supabase().table("fuelc_recept_reacties").insert({
            "recept_id": recept_id,
            "user_id":   user_id,
            "naam":      naam,
            "bericht":   bericht[:200],
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout reactie: {e}")
        return False

def _verwijder_reactie(reactie_id: str) -> bool:
    try:
        _get_supabase().table("fuelc_recept_reacties").delete().eq("id", reactie_id).execute()
        return True
    except: return False

def _render_community_tab(user: dict):
    """Community tab in bibliotheek."""
    import json as _j
    user_id  = user.get("id","")
    user_naam = user.get("name","Gebruiker")
    is_admin  = user_id == "22019eac-30b9-471e-88f3-58c7e80a4876"

    st.markdown("<br>", unsafe_allow_html=True)
    _sectie("COMMUNITY RECEPTEN", "#22c55e")
    st.markdown(
        '<div style="font-size:0.8rem;color:#64748b;margin-bottom:16px;">'
        'Gedeelde recepten van de community — scoor en laat een reactie achter.</div>',
        unsafe_allow_html=True)

    recepten = _laad_community_recepten()

    if not recepten:
        st.markdown(
            '<div style="text-align:center;color:#64748b;padding:40px;">'
            '🌍 Nog geen gedeelde recepten. Deel jouw eerste recept via de tab "📋 Mijn recepten"!</div>',
            unsafe_allow_html=True)
        return

    # Sorteer op score
    recepten = sorted(recepten, key=lambda r: r.get("gem_score",0), reverse=True)

    TYPE_EMOJI = {"ontbijt":"🌅","tussendoor":"🍎","lunch":"🥗","avond":"🍽️"}

    for rec in recepten:
        gem   = rec.get("gem_score", 0)
        n_sc  = rec.get("n_scores", 0)
        n_rt  = rec.get("n_reacties", 0)
        sterren = "⭐" * round(gem) + "☆" * (5 - round(gem)) if gem > 0 else "☆☆☆☆☆"
        emoji = TYPE_EMOJI.get(rec.get("type",""), "🍴")

        with st.expander(
            f"{emoji} {rec['naam']}  {sterren}  "
            f"({gem}/5 · {n_sc} scores · {n_rt} reacties)",
            expanded=False):

            # Macro info
            mc1,mc2,mc3,mc4 = st.columns(4)
            for col, label, val, kleur in [
                (mc1,"KCAL",rec.get("kcal",0),"#f97316"),
                (mc2,"KH g",rec.get("kh",0),"#22c55e"),
                (mc3,"EIWIT g",rec.get("eiwit",0),"#3b82f6"),
                (mc4,"VET g",rec.get("vet",0),"#8b5cf6"),
            ]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">{label}</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:{kleur};">{val}</div>'
                        f'</div>', unsafe_allow_html=True)

            # Ingrediënten
            ing = rec.get("ingredienten") or []
            if isinstance(ing, str):
                try: ing = _j.loads(ing)
                except: ing = []
            if ing:
                ing_txt = " · ".join([f"{i.get('naam','')} {i.get('gram',0)}g" for i in ing])
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#94a3b8;margin:8px 0 4px;">🥗 {ing_txt}</div>',
                    unsafe_allow_html=True)
            if rec.get("bereiding"):
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:8px;">'
                    f'👨‍🍳 {rec["bereiding"]}</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border-color:#1e293b;margin:8px 0;">', unsafe_allow_html=True)

            # Score geven
            sc1, sc2 = st.columns([3,2])
            with sc1:
                st.markdown(
                    '<div style="font-size:0.72rem;font-weight:700;color:#f8fafc;margin-bottom:4px;">'
                    '⭐ Jouw score</div>', unsafe_allow_html=True)
                mijn_score = st.select_slider(
                    "Score", options=[1,2,3,4,5],
                    key=f"score_{rec['id']}", label_visibility="collapsed")
            with sc2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Score opslaan", key=f"score_ops_{rec['id']}",
                             use_container_width=True):
                    if _sla_score_op(rec["id"], user_id, mijn_score):
                        st.success(f"✅ Score {mijn_score}/5 opgeslagen!")
                        st.rerun()

            # Reacties tonen
            reacties = rec.get("reacties", [])
            if reacties:
                st.markdown(
                    f'<div style="font-size:0.72rem;font-weight:700;color:#f8fafc;margin:8px 0 6px;">'
                    f'💬 Reacties ({len(reacties)})</div>', unsafe_allow_html=True)
                for rt in reacties[-5:]:  # max 5 tonen
                    datum = rt.get("created_at","")[:10]
                    rt_naam = rt.get("naam","Gebruiker")
                    can_del = is_admin or rt.get("user_id") == user_id
                    rd1, rd2 = st.columns([5,0.5]) if can_del else st.columns([5,0.1])
                    with rd1:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:8px 12px;margin-bottom:4px;">'
                            f'<div style="font-size:0.65rem;color:#64748b;">{rt_naam} · {datum}</div>'
                            f'<div style="font-size:0.8rem;color:#f1f5f9;">{rt.get("bericht","")}</div>'
                            f'</div>', unsafe_allow_html=True)
                    if can_del:
                        with rd2:
                            if st.button("✕", key=f"del_rt_{rt['id']}"):
                                _verwijder_reactie(rt["id"])
                                st.rerun()

            # Reactie toevoegen
            st.markdown(
                '<div style="font-size:0.72rem;font-weight:700;color:#f8fafc;margin:8px 0 4px;">'
                '✍️ Reactie achterlaten</div>', unsafe_allow_html=True)
            ra1, ra2 = st.columns([4,1])
            with ra1:
                bericht = st.text_input("Bericht", max_chars=200,
                    placeholder="Wat vind je van dit recept? (max 200 tekens)",
                    key=f"bericht_{rec['id']}", label_visibility="collapsed")
            with ra2:
                if st.button("Stuur", key=f"reactie_ops_{rec['id']}",
                             use_container_width=True):
                    if bericht.strip():
                        if _sla_reactie_op(rec["id"], user_id, user_naam, bericht):
                            st.success("✅ Reactie geplaatst!")
                            st.session_state.pop(f"bericht_{rec['id']}", None)
                            st.rerun()
                    else:
                        st.warning("Typ een bericht.")

            # Admin: verwijder recept
            if is_admin:
                if st.button("🗑 Recept verwijderen (admin)", key=f"del_rec_{rec['id']}"):
                    _verwijder_eigen_recept(rec["id"])
                    st.rerun()






def _render_receptenbeheer(user_id: str):
    """Receptenbeheer — ingredienten opbouwen via universeel formulier."""
    import json as _j

    tab_nieuw, tab_lijst = st.tabs(["➕ Recept toevoegen", "📋 Mijn recepten"])

    with tab_nieuw:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("NIEUW RECEPT", "#22c55e")
        ri1, ri2 = st.columns(2)
        with ri1:
            r_naam = st.text_input("Naam recept *", key="r_naam",
                placeholder="bijv. Havermout met fruit en noten")
        with ri2:
            r_type = st.selectbox("Type *",
                ["ontbijt","tussendoor","lunch","avond"], key="r_type",
                format_func=lambda x: {"ontbijt":"🌅 Ontbijt","tussendoor":"🍎 Tussendoor",
                    "lunch":"🥗 Lunch","avond":"🍽️ Avond"}[x])
        r_globaal = st.checkbox("🌍 Deel met community", key="r_globaal")

        _sectie("INGREDIËNTEN", "#22c55e")

        # Ingrediënten in session state bewaren
        if "r_ingredienten" not in st.session_state:
            st.session_state["r_ingredienten"] = []
        ingredienten_data = st.session_state["r_ingredienten"]

        # Bereken totalen
        def _som(veld):
            def _gram(i): return float(i.get("gram") or i.get("g") or i.get("hoeveelheid_g") or 100)
            return sum((i.get(veld,0) or 0)*(_gram(i)/100) for i in ingredienten_data)
        totaal_kcal  = _som("kcal_100g")
        totaal_kh    = _som("kh_100g")
        totaal_eiwit = _som("eiwit_100g")
        totaal_vet   = _som("vet_100g")
        totaal_vezels= _som("vezels_100g")
        totaal_natrium=_som("natrium_100g")

        # Toon toegevoegde ingrediënten
        # Toon toegevoegde ingrediënten
        for ii, ing in enumerate(ingredienten_data):
            gram_val = float(ing.get("gram") or ing.get("g") or ing.get("hoeveelheid_g") or 100)
            naam_val = ing.get("naam") or ing.get("name") or "?"
            ic1, ic2, ic3, ic4 = st.columns([4, 1.5, 2, 0.5])
            with ic1:
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#f1f5f9;padding:5px 0;">' +
                    f'<b>{naam_val}</b></div>',
                    unsafe_allow_html=True)
            with ic2:
                nieuwe_gram = st.number_input("g", 1.0, 2000.0, gram_val, 5.0,
                    key=f"r_gram_{ii}", label_visibility="collapsed")
                if nieuwe_gram != gram_val:
                    st.session_state["r_ingredienten"][ii]["gram"] = nieuwe_gram
                    st.rerun()
            with ic3:
                kcal_ing = round((ing.get("kcal_100g",0) or 0)*gram_val/100)
                kh_ing   = round((ing.get("kh_100g",0) or 0)*gram_val/100,1)
                ei_ing   = round((ing.get("eiwit_100g",0) or 0)*gram_val/100,1)
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#22c55e;padding-top:6px;">' +
                    f'{kcal_ing}kcal · {kh_ing}g KH · {ei_ing}g ei</div>',
                    unsafe_allow_html=True)
            with ic4:
                if st.button("✕", key=f"r_del_{ii}"):
                    st.session_state["r_ingredienten"].pop(ii)
                    st.rerun()

        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

        # ── Ingrediënt toevoegen ──────────────────────────────────────────────
        _sectie("INGREDIËNT TOEVOEGEN", "#22c55e")

        bron = st.radio("Bron kiezen",
            ["🔍 Voedselbank", "📋 Mijn bibliotheek", "✏️ Manueel"],
            horizontal=True, key="r_bron")

        if bron == "🔍 Voedselbank":
            db_c1, db_c2 = st.columns([2, 3])
            with db_c1:
                db_cat = st.selectbox("Categorie",
                    ["Alle"] + CATEGORIE_OPTIES,
                    key="r_db_cat", label_visibility="collapsed")
            resultaten = [p for p in VOEDSEL_DB
                         if db_cat == "Alle" or p["cat"] == db_cat]
            with db_c2:
                keuze_db = st.selectbox("Product kiezen",
                    ["— kies product —"] + [p["naam"] for p in resultaten],
                    key="r_db_keuze", label_visibility="collapsed")
            if keuze_db != "— kies product —":
                prod_sel = next((p for p in resultaten if p["naam"]==keuze_db), None)
                if prod_sel:
                    ga1, ga2 = st.columns([3,1])
                    with ga1:
                        portie_std = float(prod_sel["portie"])
                        pc1, pc2 = st.columns([1,1])
                        with pc1:
                            n_porties = st.number_input("Porties", 0.5, 20.0, 1.0, 0.5,
                                key="r_db_porties")
                        with pc2:
                            gram_db = st.number_input("Gram totaal",
                                1.0, 5000.0, round(portie_std * n_porties, 1), 5.0,
                                key="r_db_gram")
                        st.markdown(
                            f'<div style="font-size:0.7rem;color:#22c55e;">' +
                            f'{round(prod_sel["kcal"]*gram_db/100)}kcal · ' +
                            f'{round(prod_sel["kh"]*gram_db/100,1)}g KH · ' +
                            f'{round(prod_sel["eiwit"]*gram_db/100,1)}g eiwit</div>',
                            unsafe_allow_html=True)
                    with ga2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("➕ Toevoegen", key="r_db_add", use_container_width=True):
                            st.session_state["r_ingredienten"].append({
                                "naam":prod_sel["naam"],"gram":gram_db,"label":f"{gram_db}g",
                                "kcal_100g":prod_sel["kcal"],"kh_100g":prod_sel["kh"],
                                "suikers_100g":prod_sel.get("toegev_suikers", 0),"eiwit_100g":prod_sel["eiwit"],
                                "vet_100g":prod_sel["vet"],"verzadigd_100g":prod_sel.get("verz",0),
                                "vezels_100g":prod_sel["vezels"],"natrium_100g":prod_sel["natrium"],
                                "kalium_100g":prod_sel.get("kalium",0),"calcium_100g":prod_sel.get("calcium",0),
                                "ijzer_100g":prod_sel.get("ijzer",0),"magnesium_100g":prod_sel.get("magnesium",0),
                                "vitc_100g":prod_sel.get("vitc",0),"vitd_100g":prod_sel.get("vitd",0),
                                "vitb12_100g":prod_sel.get("vitb12",0),"omega3_100g":prod_sel.get("omega3",0),
                                "gi":prod_sel.get("gi",0),
                            })
                            for k in ["r_db_keuze","r_db_zoek"]:
                                st.session_state.pop(k,None)
                            st.rerun()

        elif bron == "📋 Mijn bibliotheek":
            # Laad enkel eigen bibliotheek (niet databank)
            eigen_bib = _laad_bibliotheek_raw(user_id)

            bib_c1, bib_c2 = st.columns([2, 3])
            with bib_c1:
                bib_cat = st.selectbox("Categorie",
                    ["Alle"] + CATEGORIE_OPTIES,
                    key="r_bib_cat", label_visibility="collapsed")
            bib_res = [p for p in eigen_bib
                      if bib_cat == "Alle" or p.get("categorie","") == bib_cat]
            with bib_c2:
                keuze_bib = st.selectbox("Product kiezen",
                    ["— kies product —"] + [p["naam"] for p in bib_res],
                    key="r_bib_keuze", label_visibility="collapsed")

            if keuze_bib != "— kies product —":
                prod_bib = next((p for p in bib_res if p["naam"]==keuze_bib), None)
                if prod_bib:
                    portie_bib = float(prod_bib.get("portie_g",100) or 100)
                    gb1, gb2 = st.columns([3,1])
                    with gb1:
                        portie_label_str = prod_bib.get("portie_label","") or f"{portie_bib}g"
                        bc1, bc2 = st.columns([1,1])
                        with bc1:
                            n_porties_b = st.number_input(f"Porties ({portie_label_str})",
                                0.5, 20.0, 1.0, 0.5, key="r_bib_porties")
                        with bc2:
                            gram_bib = st.number_input("Gram totaal",
                                1.0, 5000.0, round(portie_bib * n_porties_b, 1), 5.0,
                                key="r_bib_gram")
                        kcal_p = round((prod_bib.get("kcal_100g",0) or 0)*gram_bib/100)
                        kh_p   = round((prod_bib.get("kh_100g",0) or 0)*gram_bib/100,1)
                        ei_p   = round((prod_bib.get("eiwit_100g",0) or 0)*gram_bib/100,1)
                        st.markdown(
                            f'<div style="font-size:0.7rem;color:#22c55e;">' +
                            f'{kcal_p}kcal · {kh_p}g KH · {ei_p}g eiwit</div>',
                            unsafe_allow_html=True)
                    with gb2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("➕ Toevoegen", key="r_bib_add", use_container_width=True):
                            st.session_state["r_ingredienten"].append({
                                "naam":prod_bib["naam"],"gram":gram_bib,
                                "label":prod_bib.get("portie_label","") or f"{gram_bib}g",
                                **{k: prod_bib.get(k) or 0
                                   for k in ["kcal_100g","kh_100g","suikers_100g","eiwit_100g",
                                             "vet_100g","verzadigd_100g","vezels_100g","natrium_100g",
                                             "kalium_100g","calcium_100g","ijzer_100g","magnesium_100g",
                                             "vitc_100g","vitd_100g","vitb12_100g","omega3_100g","gi"]}
                            })
                            for k in ["r_bib_keuze"]:
                                st.session_state.pop(k,None)
                            st.rerun()

        else:  # ✏️ Manueel
            st.markdown(
                '<div style="font-size:0.75rem;color:#64748b;margin-bottom:8px;">' +
                'Voer het product manueel in. Je kan meerdere manuele ingrediënten toevoegen.</div>',
                unsafe_allow_html=True)
            # Gebruik unieke key per teller zodat je meerdere kunt toevoegen
            man_teller = st.session_state.get("r_man_teller", 0)
            ing_man = _product_formulier(f"r_man_{man_teller}")
            if ing_man["naam"]:
                if st.button("➕ Toevoegen", key=f"r_man_add_{man_teller}", use_container_width=True):
                    st.session_state["r_ingredienten"].append(ing_man)
                    st.session_state["r_man_teller"] = man_teller + 1
                    # Wis manueel formulier
                    for k in [k for k in st.session_state if k.startswith(f"r_man_{man_teller}")]:
                        st.session_state.pop(k, None)
                    st.rerun()
            else:
                st.button("➕ Toevoegen", key=f"r_man_add_{man_teller}",
                          use_container_width=True, disabled=True)
                st.caption("Vul minstens een naam in.")


        _sectie("BEREIDING", "#22c55e")
        r_bereiding = st.text_area("Bereidingswijze", key="r_bereiding", height=80,
            placeholder="1. Kook 3 min. 2. Voeg fruit toe. 3. Serveer.")

        if ingredienten_data and totaal_kcal > 0:
            def _som2(veld):
                def _g(i): return float(i.get("gram") or i.get("g") or 100)
                return round(sum((i.get(veld,0) or 0)*(_g(i)/100) for i in ingredienten_data),1)
            extra_v = []
            if _som2("vezels_100g"):    extra_v.append(f'Vezels: {_som2("vezels_100g")}g')
            if _som2("natrium_100g"):   extra_v.append(f'Natrium: {round(_som2("natrium_100g"))}mg')
            if _som2("kalium_100g"):    extra_v.append(f'Kalium: {round(_som2("kalium_100g"))}mg')
            if _som2("calcium_100g"):   extra_v.append(f'Calcium: {round(_som2("calcium_100g"))}mg')
            if _som2("ijzer_100g"):     extra_v.append(f'IJzer: {_som2("ijzer_100g")}mg')
            if _som2("magnesium_100g"): extra_v.append(f'Magnesium: {round(_som2("magnesium_100g"))}mg')
            if _som2("vitc_100g"):      extra_v.append(f'Vit C: {_som2("vitc_100g")}mg')
            if _som2("vitd_100g"):      extra_v.append(f'Vit D: {_som2("vitd_100g")}µg')
            if _som2("vitb12_100g"):    extra_v.append(f'Vit B12: {_som2("vitb12_100g")}µg')
            if _som2("omega3_100g"):    extra_v.append(f'Omega-3: {_som2("omega3_100g")}g')
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px;padding:14px;margin:10px 0;">' +
                f'<div style="font-size:0.7rem;font-weight:700;color:#22c55e;margin-bottom:10px;">TOTAAL RECEPT</div>' +
                f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px;">' +
                f'<div><div style="font-size:0.6rem;color:#94a3b8;">KCAL</div><div style="font-size:1.1rem;font-weight:800;color:#f97316;">{round(totaal_kcal)}</div></div>' +
                f'<div><div style="font-size:0.6rem;color:#94a3b8;">KH</div><div style="font-size:1.1rem;font-weight:800;color:#22c55e;">{round(totaal_kh,1)}g</div></div>' +
                f'<div><div style="font-size:0.6rem;color:#94a3b8;">EIWIT</div><div style="font-size:1.1rem;font-weight:800;color:#3b82f6;">{round(totaal_eiwit,1)}g</div></div>' +
                f'<div><div style="font-size:0.6rem;color:#94a3b8;">VET</div><div style="font-size:1.1rem;font-weight:800;color:#8b5cf6;">{round(totaal_vet,1)}g</div></div>' +
                f'</div>' +
                (f'<div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;">' + ' · '.join(extra_v) + '</div>' if extra_v else '') +
                f'</div>',
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if r_naam and ingredienten_data:
            if st.button("💾 Recept opslaan", key="r_opslaan", use_container_width=True):
                def _tot(veld):
                    def _g(i): return float(i.get("gram") or i.get("g") or i.get("hoeveelheid_g") or 100)
                    return round(sum((i.get(veld,0) or 0)*(_g(i)/100) for i in ingredienten_data), 1)
                # Sla enkel naam/gram/label op als ingrediëntenlijst
                ing_lijst = [{"naam":i["naam"],"gram":i["gram"],"label":i.get("label","")}
                             for i in ingredienten_data]
                recept = {
                    "naam":r_naam.strip(),"type":r_type,
                    "kcal":round(_tot("kcal_100g")),"kh":_tot("kh_100g"),
                    "eiwit":_tot("eiwit_100g"),"vet":_tot("vet_100g"),
                    "vezels":_tot("vezels_100g"),"natrium":round(_tot("natrium_100g")),
                    "ingredienten":_j.dumps(ing_lijst),
                    "bereiding":r_bereiding.strip() if r_bereiding else "",
                    "is_globaal":st.session_state.get("r_globaal",False),
                    "user_id":user_id,
                }
                try:
                    _get_supabase().table("fuelc_recepten_eigen").insert(recept).execute()
                    st.success(f"✅ '{r_naam}' opgeslagen!")
                    for k in [k for k in st.session_state if k.startswith(("r_","ing_"))]:
                        st.session_state.pop(k,None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Fout: {e}")
        else:
            st.button("💾 Recept opslaan", key="r_opslaan", use_container_width=True, disabled=True)
            st.caption("Voeg minstens één ingrediënt toe.")

    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            r = _get_supabase().table("fuelc_recepten_eigen").select("*")                .or_(f"user_id.eq.{user_id},is_globaal.eq.true").order("naam").execute()
            eigen_recepten = r.data or []
        except: eigen_recepten = []
        TYPE_LABEL = {"ontbijt":"🌅","tussendoor":"🍎","lunch":"🥗","avond":"🍽️"}
        for rec in eigen_recepten:
            ing = rec.get("ingredienten") or []
            if isinstance(ing,str):
                try: ing = _j.loads(ing)
                except: ing = []
            globaal_badge = " 🌍" if rec.get("is_globaal") else ""
            with st.expander(
                f"{TYPE_LABEL.get(rec.get('type',''),'🍴')}  "
                f"{rec.get('naam','')}{globaal_badge}  ·  "
                f"{rec.get('kcal',0)} kcal  ·  {rec.get('kh',0)}g KH  ·  {rec.get('eiwit',0)}g eiwit",
                expanded=False):
                rm1,rm2,rm3,rm4 = st.columns(4)
                for col,lbl,val,kl in [
                    (rm1,"KCAL",rec.get("kcal",0),"#f97316"),
                    (rm2,"KH g",rec.get("kh",0),"#22c55e"),
                    (rm3,"EIWIT g",rec.get("eiwit",0),"#3b82f6"),
                    (rm4,"VET g",rec.get("vet",0),"#8b5cf6"),
                ]:
                    with col:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;margin-bottom:6px;">' +
                            f'<div style="font-size:0.65rem;font-weight:600;color:#94a3b8;margin-bottom:2px;">{lbl}</div>' +
                            f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>' +
                            f'</div>', unsafe_allow_html=True)

                # Extra voedingsstoffen uit recept kolommen
                extra_rec = []
                if rec.get("vezels"):    extra_rec.append(f'Vezels: {rec["vezels"]}g')
                if rec.get("natrium"):   extra_rec.append(f'Natrium: {rec["natrium"]}mg')
                if extra_rec:
                    st.markdown(
                        f'<div style="font-size:0.75rem;color:#94a3b8;margin-bottom:8px;">' +
                        ' · '.join(extra_rec) + '</div>',
                        unsafe_allow_html=True)

                if ing:
                    st.markdown(
                        '<div style="font-size:0.72rem;font-weight:700;color:#64748b;margin:6px 0 4px;">INGREDIËNTEN</div>',
                        unsafe_allow_html=True)
                    for item in ing:
                        naam_i  = item.get("naam","") if isinstance(item,dict) else ""
                        gram_i  = float(item.get("gram") or item.get("g") or 0) if isinstance(item,dict) else 0
                        label_i = item.get("label","") if isinstance(item,dict) else ""
                        # Toon voedingswaarden per ingrediënt indien beschikbaar
                        kcal_i  = round((item.get("kcal_100g",0) or 0)*gram_i/100) if gram_i else 0
                        detail_i = f' ({kcal_i}kcal)' if kcal_i > 0 else ''
                        st.markdown(
                            f'<div style="font-size:0.8rem;color:#f1f5f9;padding:2px 0;">' +
                            f'· <b>{naam_i}</b> — {label_i or str(gram_i)+"g"}{detail_i}</div>',
                            unsafe_allow_html=True)

                if rec.get("bereiding"):
                    st.markdown(
                        f'<div style="font-size:0.78rem;color:#94a3b8;margin-top:6px;">' +
                        f'👨\u200d🍳 {rec["bereiding"]}</div>', unsafe_allow_html=True)
                if rec.get("user_id") == user_id or user_id == "22019eac-30b9-471e-88f3-58c7e80a4876":
                    if st.button("🗑 Verwijderen", key=f"r_del_{rec['id']}"):
                        try:
                            _get_supabase().table("fuelc_recepten_eigen").delete().eq("id",rec["id"]).execute()
                            st.rerun()
                        except Exception as e: st.error(str(e))




@st.cache_data(ttl=60)
def _laad_alle_recepten(user_id: str) -> list:
    """Laad eigen + gedeelde recepten."""
    try:
        r = _get_supabase().table("fuelc_recepten_eigen").select("*")            .or_(f"user_id.eq.{user_id},is_globaal.eq.true")            .order("naam").execute()
        return r.data or []
    except Exception as e:
        print(f"Fout laden recepten: {e}")
        return []



def _render_product_rij(p: dict, user_id: str):
    """Render één product rij in de bibliotheek."""
    portie = p.get("portie_g") or 0
    kcal   = p.get("kcal_100g") or 0
    kh     = p.get("kh_100g") or 0
    eiwit  = p.get("eiwit_100g") or 0
    vet    = p.get("vet_100g") or 0
    with st.expander(
            f"{'⭐ ' if p.get('favoriet') else '🥦 '}{p.get('naam','')}  ·  {kcal} kcal/100g  ·  {p.get('categorie','')}",
            expanded=False):
        mc1,mc2,mc3,mc4 = st.columns(4)
        for col,lbl,val,kl in [(mc1,"KCAL",kcal,"#f97316"),(mc2,"KH g",kh,"#22c55e"),(mc3,"EIWIT g",eiwit,"#3b82f6"),(mc4,"VET g",vet,"#8b5cf6")]:
            with col:
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;margin-bottom:4px;">' +
                    f'<div style="font-size:0.65rem;font-weight:600;color:#94a3b8;margin-bottom:2px;">{lbl}</div>' +
                    f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>' +
                    f'</div>', unsafe_allow_html=True)
        if portie > 0:
            st.markdown(
                f'<div style="font-size:0.72rem;color:#64748b;margin-top:6px;">' +
                f'Per portie ({p.get("portie_label") or str(portie)+"g"}): ' +
                f'{round(kcal*portie/100)}kcal · {round(kh*portie/100,1)}g KH · ' +
                f'{round(eiwit*portie/100,1)}g eiwit · {round(vet*portie/100,1)}g vet</div>',
                unsafe_allow_html=True)

        # Extra voedingsstoffen
        extra = []
        if p.get("vezels_100g"):    extra.append(f'Vezels: {p["vezels_100g"]}g')
        if p.get("natrium_100g"):   extra.append(f'Natrium: {round(p["natrium_100g"])}mg')
        if p.get("kalium_100g"):    extra.append(f'Kalium: {round(p["kalium_100g"])}mg')
        if p.get("calcium_100g"):   extra.append(f'Calcium: {round(p["calcium_100g"])}mg')
        if p.get("ijzer_100g"):     extra.append(f'IJzer: {p["ijzer_100g"]}mg')
        if p.get("magnesium_100g"): extra.append(f'Magnesium: {round(p["magnesium_100g"])}mg')
        if p.get("vitc_100g"):      extra.append(f'Vit C: {p["vitc_100g"]}mg')
        if p.get("vitd_100g"):      extra.append(f'Vit D: {p["vitd_100g"]}µg')
        if p.get("vitb12_100g"):    extra.append(f'Vit B12: {p["vitb12_100g"]}µg')
        if p.get("omega3_100g"):    extra.append(f'Omega-3: {p["omega3_100g"]}g')
        if p.get("gi"):             extra.append(f'GI: {p["gi"]}')
        if extra:
            st.markdown(
                f'<div style="font-size:0.7rem;color:#64748b;margin-top:4px;">' +
                ' · '.join(extra) + '</div>',
                unsafe_allow_html=True)
        ba1, ba2 = st.columns(2)
        with ba1:
            fav_lbl = "★ Verwijder favoriet" if p.get("favoriet") else "☆ Favoriet"
            if st.button(fav_lbl, key=f"bib_fav_{p['id']}", use_container_width=True):
                if _update_product(p["id"], {"favoriet": not p.get("favoriet")}):
                    _laad_bibliotheek_raw.clear()
                    _laad_gecombineerde_bibliotheek_raw.clear()
                    st.rerun()
        with ba2:
            if st.button("🗑 Verwijderen", key=f"bib_del_{p['id']}", use_container_width=True):
                if _verwijder_product(p["id"]):
                    st.success("Verwijderd.")
                    st.rerun()


def _stap_bibliotheek(user: dict):
    user_id = user.get("id", "")
    _sectie("VOEDSELBIBLIOTHEEK", "#22c55e")

    tab_add, tab_db, tab_scan, tab_lijst, tab_recepten, tab_community = st.tabs([
        "➕  Manueel toevoegen",
        "🔍  Voedselbank zoeken",
        "📷  Etiketscan",
        "📋  Mijn bibliotheek",
        "🍴  Recepten",
        "🌍  Community",
    ])

    with tab_add:
        st.markdown("<br>", unsafe_allow_html=True)
        product_data = _product_formulier("bib")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.pop("bib_saved", False):
            st.success("✅ Product opgeslagen in je bibliotheek!")

        if product_data["naam"]:
            if st.button("💾 Product opslaan", key="bib_opslaan", use_container_width=True):
                product_data["bron"] = "manueel"
                if _sla_product_op(user_id, product_data):
                    st.session_state["bib_saved"] = True
                    for k in [k for k in st.session_state if k.startswith("bib_") and k != "bib_saved"]:
                        st.session_state.pop(k, None)
                    st.rerun()
        else:
            st.button("💾 Product opslaan", key="bib_opslaan", use_container_width=True, disabled=True)

    with tab_db:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ZOEKEN IN VOEDSELBANK", "#22c55e")
        db_zoek = st.text_input("Zoeken", placeholder="bijv. havermout, banaan...",
            key="db_zoek", label_visibility="collapsed")
        db_cat  = st.selectbox("Categorie", ["Alle"]+CATEGORIE_OPTIES,
            key="db_cat_filter", label_visibility="collapsed")
        zoek_l  = db_zoek.lower().strip() if db_zoek else ""
        db_res  = [p for p in VOEDSEL_DB
                   if (not zoek_l or zoek_l in p["naam"].lower())
                   and (db_cat=="Alle" or p["cat"]==db_cat)]
        st.markdown(f'<div style="font-size:0.72rem;color:#64748b;margin:6px 0;">{len(db_res)} product(en)</div>', unsafe_allow_html=True)

        for i, p in enumerate(db_res[:50]):
            with st.expander(f"🥦 {p['naam']}  ·  {p['kcal']} kcal/100g  ·  {p['portie_label']}", expanded=False):
                mc1,mc2,mc3,mc4 = st.columns(4)
                for col,lbl,val,kl in [(mc1,"KCAL",p["kcal"],"#f97316"),(mc2,"KH g",p["kh"],"#22c55e"),(mc3,"EIWIT g",p["eiwit"],"#3b82f6"),(mc4,"VET g",p["vet"],"#8b5cf6")]:
                    with col:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;margin-bottom:4px;">' +
                            f'<div style="font-size:0.65rem;font-weight:600;color:#94a3b8;margin-bottom:2px;">{lbl}</div>' +
                            f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>' +
                            f'</div>', unsafe_allow_html=True)
                extra_db = [
                    f'Vezels: {p["vezels"]}g',
                    f'Natrium: {p["natrium"]}mg',
                ]
                if p.get("kalium"):    extra_db.append(f'Kalium: {p["kalium"]}mg')
                if p.get("calcium"):   extra_db.append(f'Calcium: {p["calcium"]}mg')
                if p.get("ijzer"):     extra_db.append(f'IJzer: {p["ijzer"]}mg')
                if p.get("magnesium"): extra_db.append(f'Magnesium: {p["magnesium"]}mg')
                if p.get("vitc"):      extra_db.append(f'Vit C: {p["vitc"]}mg')
                if p.get("vitd"):      extra_db.append(f'Vit D: {p["vitd"]}µg')
                if p.get("vitb12"):    extra_db.append(f'Vit B12: {p["vitb12"]}µg')
                if p.get("omega3"):    extra_db.append(f'Omega-3: {p["omega3"]}g')
                if p.get("gi"):        extra_db.append(f'GI: {p["gi"]}')
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#64748b;margin:6px 0;">' +
                    ' · '.join(extra_db) + '</div>',
                    unsafe_allow_html=True)
                eenheid_db = st.selectbox("Eenheid", ["gram (g)","stuk","snede","eetlepel (15ml)","kopje (150ml)","glas (200ml)","portie","ml"], key=f"db_e_{i}")
                EG = {"gram (g)":1.0,"stuk":1.0,"snede":1.0,"eetlepel (15ml)":15.0,"kopje (150ml)":150.0,"glas (200ml)":200.0,"portie":float(p["portie"]),"ml":1.0}
                hoev_db = st.number_input("Hoeveelheid", 0.1, 500.0, 1.0 if eenheid_db not in ("gram (g)","ml") else float(p["portie"]), 0.5, key=f"db_h_{i}")
                portie_g_db = round(hoev_db * EG.get(eenheid_db,1.0), 1)
                st.markdown(f'<div style="font-size:0.75rem;color:#22c55e;">= {portie_g_db}g · {round(p["kcal"]*portie_g_db/100)}kcal per portie</div>', unsafe_allow_html=True)
                if st.button("📥 Toevoegen aan bibliotheek", key=f"db_import_{i}", use_container_width=True):
                    prod = {
                        "naam":p["naam"],"categorie":p["cat"],"bron":"databank",
                        "portie_g":portie_g_db,"portie_label":f"{hoev_db} {eenheid_db}",
                        "kcal_100g":p["kcal"],"kh_100g":p["kh"],"suikers_100g":p.get("toegev_suikers", 0),
                        "eiwit_100g":p["eiwit"],"vet_100g":p["vet"],"verzadigd_100g":p["verz"],
                        "vezels_100g":p["vezels"],"natrium_100g":p["natrium"],
                        "kalium_100g":p.get("kalium"),"calcium_100g":p.get("calcium"),
                        "ijzer_100g":p.get("ijzer"),"magnesium_100g":p.get("magnesium"),
                        "vitc_100g":p.get("vitc"),"vitd_100g":p.get("vitd"),
                        "vitb12_100g":p.get("vitb12"),"omega3_100g":p.get("omega3"),
                        "gi":p.get("gi"),"favoriet":False,"user_id":user_id,
                    }
                    if _sla_product_op(user_id, prod):
                        st.success(f"✅ '{p['naam']}' toegevoegd!")
                        st.rerun()

    with tab_scan:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ETIKETSCAN VIA AI", "#22c55e")
        scan_foto = st.file_uploader("Foto van etiket (JPG/PNG)", type=["jpg","jpeg","png"], key="scan_foto")
        if scan_foto:
            import base64, requests as _req2, json as _json_s, os as _os
            foto_bytes = scan_foto.read()
            foto_b64   = base64.b64encode(foto_bytes).decode()
            foto_mime  = "image/jpeg" if scan_foto.name.lower().endswith((".jpg",".jpeg")) else "image/png"
            st.image(scan_foto, width=300)
            if st.button("🤖 Scan etiket", key="scan_btn", use_container_width=True):
                with st.spinner("AI leest het etiket..."):
                    try:
                        resp = _req2.post("https://api.anthropic.com/v1/messages",
                            json={"model":"claude-sonnet-4-5","max_tokens":1000,"messages":[{"role":"user","content":[
                                {"type":"image","source":{"type":"base64","media_type":foto_mime,"data":foto_b64}},
                                {"type":"text","text":"Lees de voedingswaarden per 100g uit dit etiket. Geef ENKEL JSON: {naam,kcal_100g,kh_100g,suikers_100g,vezels_100g,eiwit_100g,vet_100g,verzadigd_100g,natrium_100g,portie_g,gi}. Geen uitleg."}
                            ]}]},
                            headers={"x-api-key":_os.environ.get("ANTHROPIC_API_KEY",""),
                                     "anthropic-version":"2023-06-01","content-type":"application/json"},
                            timeout=30).json()
                        tekst = resp["content"][0]["text"].strip().strip("```json").strip("```").strip()
                        st.session_state["scan_result"] = _json_s.loads(tekst)
                        st.success("✅ Etiket uitgelezen!")
                    except Exception as e:
                        st.error(f"Scan mislukt: {e}")

        scan_result = st.session_state.get("scan_result",{})
        if scan_result:
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("GESCANDE WAARDEN — controleer en pas aan", "#86efac")
            # Snelle categorie keuze bovenaan
            sc1, sc2 = st.columns([2,3])
            with sc1:
                scan_cat_snel = st.selectbox(
                    "📂 Categorie",
                    CATEGORIE_OPTIES,
                    key="scan_cat_snel",
                    index=CATEGORIE_OPTIES.index(scan_result.get("categorie","Overige"))
                    if scan_result.get("categorie") in CATEGORIE_OPTIES else len(CATEGORIE_OPTIES)-1
                )
                scan_result["categorie"] = scan_cat_snel
            with sc2:
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b;padding-top:28px;">' +
                    f'Kies de categorie zodat je het product snel terugvindt.</div>',
                    unsafe_allow_html=True)
            scan_product = _product_formulier("scan", defaults=scan_result)
            if scan_product["naam"]:
                if st.button("💾 Opslaan", key="scan_opslaan", use_container_width=True):
                    scan_product["bron"] = "etiketscan"
                    if _sla_product_op(user_id, scan_product):
                        st.success(f"✅ Opgeslagen!")
                        for k in [k for k in st.session_state if k.startswith("scan_")]:
                            st.session_state.pop(k,None)
                        st.rerun()

    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns([3,2,1])
        with f1: zoek = st.text_input("Zoeken", placeholder="bijv. havermout", key="bib_zoek", label_visibility="collapsed")
        with f2: filter_cat = st.selectbox("Categorie", ["Alle"]+CATEGORIE_OPTIES, key="bib_filter_cat", label_visibility="collapsed")
        with f3: fav_f = st.selectbox("Filter", ["Alle","⭐ Fav"], key="bib_fav_f", label_visibility="collapsed")
        producten = _laad_bibliotheek(user_id, zoek, filter_cat)
        if fav_f == "⭐ Fav": producten = [p for p in producten if p.get("favoriet")]
        st.markdown(f'<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">{len(producten)} product(en)</div>', unsafe_allow_html=True)

        # Groepeer favorieten per categorie
        if fav_f == "⭐ Fav" and filter_cat == "Alle":
            from collections import defaultdict as _dd
            per_cat = _dd(list)
            for p in producten:
                per_cat[p.get("categorie","Overige")].append(p)
            for cat_naam in sorted(per_cat.keys()):
                st.markdown(
                    f'<div style="font-size:0.7rem;font-weight:700;color:#f97316;'
                    f'letter-spacing:1px;text-transform:uppercase;'
                    f'margin:16px 0 6px;border-left:3px solid #f97316;padding-left:8px;">'
                    f'{cat_naam} ({len(per_cat[cat_naam])})</div>',
                    unsafe_allow_html=True)
                for p in per_cat[cat_naam]:
                    _render_product_rij(p, user_id)
        else:
            for p in producten:
                portie  = p.get("portie_g") or 0
                kcal    = p.get("kcal_100g") or 0
                kh      = p.get("kh_100g") or 0
                eiwit   = p.get("eiwit_100g") or 0
                vet     = p.get("vet_100g") or 0
                fav_ster = "⭐ " if p.get("favoriet") else ""
                with st.expander(
                        f"{'⭐ ' if p.get('favoriet') else '🥦 '}{p.get('naam','')}  ·  {kcal} kcal/100g  ·  {p.get('categorie','')}",
                        expanded=False):
                    mc1,mc2,mc3,mc4 = st.columns(4)
                    for col,lbl,val,kl in [(mc1,"KCAL",kcal,"#f97316"),(mc2,"KH g",kh,"#22c55e"),(mc3,"EIWIT g",eiwit,"#3b82f6"),(mc4,"VET g",vet,"#8b5cf6")]:
                        with col:
                            st.markdown(
                                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;margin-bottom:4px;">' +
                                f'<div style="font-size:0.65rem;font-weight:600;color:#94a3b8;margin-bottom:2px;">{lbl}</div>' +
                                f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>' +
                                f'</div>', unsafe_allow_html=True)
                    if portie > 0:
                        st.markdown(
                            f'<div style="font-size:0.72rem;color:#64748b;margin-top:6px;">' +
                            f'Per portie ({p.get("portie_label") or str(portie)+"g"}): ' +
                            f'{round(kcal*portie/100)}kcal · {round(kh*portie/100,1)}g KH · ' +
                            f'{round(eiwit*portie/100,1)}g eiwit · {round(vet*portie/100,1)}g vet</div>',
                            unsafe_allow_html=True)

                    # Extra voedingsstoffen
                    extra = []
                    if p.get("vezels_100g"):    extra.append(f'Vezels: {p["vezels_100g"]}g')
                    if p.get("natrium_100g"):   extra.append(f'Natrium: {round(p["natrium_100g"])}mg')
                    if p.get("kalium_100g"):    extra.append(f'Kalium: {round(p["kalium_100g"])}mg')
                    if p.get("calcium_100g"):   extra.append(f'Calcium: {round(p["calcium_100g"])}mg')
                    if p.get("ijzer_100g"):     extra.append(f'IJzer: {p["ijzer_100g"]}mg')
                    if p.get("magnesium_100g"): extra.append(f'Magnesium: {round(p["magnesium_100g"])}mg')
                    if p.get("vitc_100g"):      extra.append(f'Vit C: {p["vitc_100g"]}mg')
                    if p.get("vitd_100g"):      extra.append(f'Vit D: {p["vitd_100g"]}µg')
                    if p.get("vitb12_100g"):    extra.append(f'Vit B12: {p["vitb12_100g"]}µg')
                    if p.get("omega3_100g"):    extra.append(f'Omega-3: {p["omega3_100g"]}g')
                    if p.get("gi"):             extra.append(f'GI: {p["gi"]}')
                    if extra:
                        st.markdown(
                            f'<div style="font-size:0.7rem;color:#64748b;margin-top:4px;">' +
                            ' · '.join(extra) + '</div>',
                            unsafe_allow_html=True)
                    ba1, ba2 = st.columns(2)
                    with ba1:
                        fav_lbl = "★ Verwijder favoriet" if p.get("favoriet") else "☆ Favoriet"
                        if st.button(fav_lbl, key=f"bib_fav_{p['id']}", use_container_width=True):
                            if _update_product(p["id"], {"favoriet": not p.get("favoriet")}):
                                _laad_bibliotheek_raw.clear()
                                _laad_gecombineerde_bibliotheek_raw.clear()
                                st.rerun()
                    with ba2:
                        if st.button("🗑 Verwijderen", key=f"bib_del_{p['id']}", use_container_width=True):
                            if _verwijder_product(p["id"]):
                                st.success("Verwijderd.")
                                st.rerun()

    with tab_recepten:
        st.markdown("<br>", unsafe_allow_html=True)
        _render_receptenbeheer(user_id)

    with tab_community:
        _render_community_tab(user)



RECEPT_DB = [
    # ── ONTBIJT ───────────────────────────────────────────────────────────────
    {
        "naam": "Havermout met banaan en honing",
        "type": "ontbijt",
        "kcal": 420, "kh": 72, "eiwit": 14, "vet": 8,
        "ingredienten": [
            ("Havermout", 80), ("Volle melk", 200), ("Banaan", 120), ("Honing", 15)
        ],
        "bereiding": "1. Kook de havermout 3 min in de melk. 2. Snijd de banaan in schijfjes. 3. Leg op de pap en druppel honing erover."
    },
    {
        "naam": "Volkoren boterhammen met ei en tomaat",
        "type": "ontbijt",
        "kcal": 390, "kh": 48, "eiwit": 22, "vet": 12,
        "ingredienten": [
            ("Volkorenbrood", 105), ("Ei groot", 120), ("Tomaat", 100), ("Boter", 10)
        ],
        "bereiding": "1. Bak de eieren in boter. 2. Snijd tomaat in schijfjes. 3. Beleg de boterhammen."
    },
    {
        "naam": "Griekse yoghurt met bosbes en granola",
        "type": "ontbijt",
        "kcal": 380, "kh": 52, "eiwit": 18, "vet": 10,
        "ingredienten": [
            ("Griekse yoghurt vol", 200), ("Bosbes", 100), ("Granola", 45)
        ],
        "bereiding": "1. Schep yoghurt in een kom. 2. Verdeel bosbessen erover. 3. Strooi granola erbovenop."
    },
    {
        "naam": "Roerei met champignons op brood",
        "type": "ontbijt",
        "kcal": 450, "kh": 44, "eiwit": 26, "vet": 18,
        "ingredienten": [
            ("Ei groot", 180), ("Champignon", 100), ("Bruin brood", 70), ("Boter", 10)
        ],
        "bereiding": "1. Bak champignons 3 min in boter. 2. Klop eieren los en roer door de pan. 3. Serveer op geroosterd brood."
    },
    {
        "naam": "Smoothie met havermout en fruit",
        "type": "ontbijt",
        "kcal": 400, "kh": 68, "eiwit": 12, "vet": 7,
        "ingredienten": [
            ("Havermout", 50), ("Banaan", 120), ("Aardbei", 100), ("Halfvolle melk", 200)
        ],
        "bereiding": "1. Doe alle ingrediënten in de blender. 2. Mix tot glad. 3. Direct serveren."
    },
    {
        "naam": "Kwark met rozijnen en appel",
        "type": "ontbijt",
        "kcal": 310, "kh": 48, "eiwit": 20, "vet": 2,
        "ingredienten": [
            ("Kwark mager", 200), ("Appel", 150), ("Rozijnen", 30)
        ],
        "bereiding": "1. Snijd appel in kleine stukjes. 2. Meng met kwark. 3. Voeg rozijnen toe en roer goed."
    },
    {
        "naam": "Pannenkoeken met appelmoes",
        "type": "ontbijt",
        "kcal": 480, "kh": 78, "eiwit": 14, "vet": 12,
        "ingredienten": [
            ("Pannenkoek", 240), ("Appelmoes", 120), ("Honing", 15)
        ],
        "bereiding": "1. Bak pannenkoeken goudbruin. 2. Serveer met appelmoes. 3. Druppel honing erover."
    },
    {
        "naam": "Muesli met halfvolle melk en banaan",
        "type": "ontbijt",
        "kcal": 430, "kh": 70, "eiwit": 12, "vet": 9,
        "ingredienten": [
            ("Muesli", 80), ("Halfvolle melk", 200), ("Banaan", 120)
        ],
        "bereiding": "1. Doe muesli in een kom. 2. Giet melk erover. 3. Snijd banaan in schijfjes en voeg toe."
    },
    {
        "naam": "Volkoren toast met pindakaas en banaan",
        "type": "ontbijt",
        "kcal": 460, "kh": 62, "eiwit": 16, "vet": 16,
        "ingredienten": [
            ("Volkorenbrood", 105), ("Pindakaas", 40), ("Banaan", 120)
        ],
        "bereiding": "1. Rooster de boterhammen. 2. Smeer pindakaas erop. 3. Beleg met schijfjes banaan."
    },
    {
        "naam": "Skyr met kiwi en noten",
        "type": "ontbijt",
        "kcal": 340, "kh": 38, "eiwit": 24, "vet": 9,
        "ingredienten": [
            ("Skyr", 200), ("Kiwi", 100), ("Walnoten", 20), ("Honing", 10)
        ],
        "bereiding": "1. Schep skyr in een kom. 2. Snijd kiwi en leg bovenop. 3. Strooi gehakte walnoten en honing erover."
    },

    # ── TUSSENDOOR ────────────────────────────────────────────────────────────
    {
        "naam": "Appel met amandelboter",
        "type": "tussendoor",
        "kcal": 220, "kh": 28, "eiwit": 4, "vet": 11,
        "ingredienten": [
            ("Appel", 150), ("Amandelboter", 20)
        ],
        "bereiding": "1. Snijd appel in partjes. 2. Serveer met amandelboter als dip."
    },
    {
        "naam": "Rijstwafels met hummus",
        "type": "tussendoor",
        "kcal": 200, "kh": 32, "eiwit": 6, "vet": 6,
        "ingredienten": [
            ("Rijstwafel naturel", 36), ("Hummus", 50)
        ],
        "bereiding": "1. Smeer hummus op de rijstwafels. 2. Eventueel bestrooien met paprikapoeder."
    },
    {
        "naam": "Banaan met walnoten",
        "type": "tussendoor",
        "kcal": 250, "kh": 32, "eiwit": 4, "vet": 12,
        "ingredienten": [
            ("Banaan", 120), ("Walnoten", 25)
        ],
        "bereiding": "1. Pel de banaan. 2. Eet samen met een handjevol walnoten."
    },
    {
        "naam": "Volkoren cracker met plattekaas en tomaat",
        "type": "tussendoor",
        "kcal": 190, "kh": 22, "eiwit": 9, "vet": 7,
        "ingredienten": [
            ("Cracker volkoren", 30), ("Plattekaas", 60), ("Tomaat", 80)
        ],
        "bereiding": "1. Smeer plattekaas op crackers. 2. Beleg met schijfjes tomaat."
    },
    {
        "naam": "Griekse yoghurt met honing",
        "type": "tussendoor",
        "kcal": 210, "kh": 22, "eiwit": 14, "vet": 7,
        "ingredienten": [
            ("Griekse yoghurt vol", 150), ("Honing", 15)
        ],
        "bereiding": "1. Schep yoghurt in een kommetje. 2. Druppel honing erover."
    },
    {
        "naam": "Dadels met cashewnoten",
        "type": "tussendoor",
        "kcal": 240, "kh": 38, "eiwit": 4, "vet": 9,
        "ingredienten": [
            ("Dadel gedroogd", 40), ("Cashewnoten", 20)
        ],
        "bereiding": "1. Combineer dadels en cashewnoten in een bakje. 2. Direct serveren."
    },
    {
        "naam": "Kwark met aardbei",
        "type": "tussendoor",
        "kcal": 170, "kh": 20, "eiwit": 16, "vet": 1,
        "ingredienten": [
            ("Kwark mager", 150), ("Aardbei", 100), ("Honing", 10)
        ],
        "bereiding": "1. Snijd aardbeien in stukjes. 2. Meng met kwark en honing."
    },
    {
        "naam": "Boterham met kippenham en komkommer",
        "type": "tussendoor",
        "kcal": 220, "kh": 28, "eiwit": 14, "vet": 5,
        "ingredienten": [
            ("Bruin brood", 70), ("Kippenham", 60), ("Komkommer", 60)
        ],
        "bereiding": "1. Beleg boterham met kippenham. 2. Voeg schijfjes komkommer toe."
    },

    # ── LUNCH ─────────────────────────────────────────────────────────────────
    {
        "naam": "Volkoren boterhammen met kipfilet en sla",
        "type": "lunch",
        "kcal": 480, "kh": 52, "eiwit": 36, "vet": 12,
        "ingredienten": [
            ("Volkorenbrood", 140), ("Kipfilet", 100), ("Sla gemengd", 50),
            ("Tomaat", 80), ("Mayonaise", 15)
        ],
        "bereiding": "1. Snijd kipfilet in reepjes en kruid. 2. Bak 6 min in pan. 3. Beleg brood met sla, tomaat en kip."
    },
    {
        "naam": "Pasta met tonijn en tomaat",
        "type": "lunch",
        "kcal": 520, "kh": 68, "eiwit": 32, "vet": 9,
        "ingredienten": [
            ("Pasta wit gekookt", 250), ("Tonijn in water", 120),
            ("Tomatensaus", 100), ("Paprika rood", 80)
        ],
        "bereiding": "1. Kook pasta al dente. 2. Verwarm tomatensaus met paprika. 3. Meng met tonijn en pasta."
    },
    {
        "naam": "Rijst met kipfilet en groenten",
        "type": "lunch",
        "kcal": 540, "kh": 65, "eiwit": 38, "vet": 8,
        "ingredienten": [
            ("Rijst wit gekookt", 200), ("Kipfilet", 120),
            ("Broccoli", 150), ("Wortel rauw", 80), ("Sojasaus", 15)
        ],
        "bereiding": "1. Kook rijst. 2. Bak kipfilet 8 min en snijd in stukjes. 3. Stoom groenten 5 min en serveer met sojasaus."
    },
    {
        "naam": "Soep met brood",
        "type": "lunch",
        "kcal": 380, "kh": 52, "eiwit": 16, "vet": 10,
        "ingredienten": [
            ("Wortel", 100), ("Ui", 80), ("Aardappel gekookt", 175),
            ("Kipfilet", 60), ("Volkorenbrood", 70)
        ],
        "bereiding": "1. Kook groenten en kip 20 min in bouillon. 2. Mix tot soep. 3. Serveer met volkorenbrood."
    },
    {
        "naam": "Quinoa salade met ei en groenten",
        "type": "lunch",
        "kcal": 490, "kh": 52, "eiwit": 24, "vet": 18,
        "ingredienten": [
            ("Quinoa gekookt", 185), ("Ei groot", 120),
            ("Komkommer", 100), ("Tomaat", 100), ("Olijfolie", 10)
        ],
        "bereiding": "1. Kook eieren 8 min. 2. Snijd groenten fijn. 3. Meng met quinoa en besprenkel met olijfolie."
    },
    {
        "naam": "Wraps met kalkoen en avocado",
        "type": "lunch",
        "kcal": 560, "kh": 55, "eiwit": 34, "vet": 22,
        "ingredienten": [
            ("Wrap", 120), ("Kalkoenfilet", 100),
            ("Avocado", 80), ("Sla gemengd", 50), ("Tomaat", 80)
        ],
        "bereiding": "1. Bak kalkoen 6 min en snijd in reepjes. 2. Prak avocado grof. 3. Vul wraps met alle ingrediënten."
    },
    {
        "naam": "Aardappelsalade met haring",
        "type": "lunch",
        "kcal": 500, "kh": 50, "eiwit": 24, "vet": 20,
        "ingredienten": [
            ("Aardappel gekookt", 300), ("Haring", 100),
            ("Ui", 60), ("Mayonaise", 30), ("Sla gemengd", 50)
        ],
        "bereiding": "1. Snijd aardappelen in blokjes. 2. Meng met mayonaise en ui. 3. Serveer met haring op sla."
    },
    {
        "naam": "Broodje zalm met komkommer",
        "type": "lunch",
        "kcal": 460, "kh": 44, "eiwit": 28, "vet": 18,
        "ingredienten": [
            ("Stokbrood", 100), ("Zalm", 100),
            ("Plattekaas", 50), ("Komkommer", 80)
        ],
        "bereiding": "1. Snijd stokbrood open. 2. Smeer plattekaas erop. 3. Beleg met zalm en komkommer."
    },
    {
        "naam": "Couscous met kip en paprika",
        "type": "lunch",
        "kcal": 510, "kh": 62, "eiwit": 34, "vet": 10,
        "ingredienten": [
            ("Couscous gekookt", 200), ("Kipfilet", 100),
            ("Paprika rood", 100), ("Wortel rauw", 80), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bereid couscous per verpakking. 2. Bak kip en groenten 8 min. 3. Meng alles en besprenkel met olijfolie."
    },
    {
        "naam": "Linzensoep met brood",
        "type": "lunch",
        "kcal": 430, "kh": 62, "eiwit": 22, "vet": 7,
        "ingredienten": [
            ("Linzen gekookt", 200), ("Wortel", 100),
            ("Ui", 80), ("Tomatensaus", 80), ("Volkorenbrood", 70)
        ],
        "bereiding": "1. Fruit ui aan. 2. Voeg linzen, wortel en tomatensaus toe, kook 15 min. 3. Serveer met brood."
    },
    {
        "naam": "Rijstwafel met kippenham en kaas",
        "type": "lunch",
        "kcal": 350, "kh": 40, "eiwit": 20, "vet": 11,
        "ingredienten": [
            ("Rijstwafel naturel", 36), ("Kippenham", 90),
            ("Edammer 30+", 30), ("Tomaat", 80)
        ],
        "bereiding": "1. Beleg rijstwafels met ham. 2. Voeg kaas en tomaat toe. 3. Direct serveren."
    },

    # ── AVOND ─────────────────────────────────────────────────────────────────
    {
        "naam": "Spaghetti bolognese",
        "type": "avond",
        "kcal": 620, "kh": 72, "eiwit": 36, "vet": 18,
        "ingredienten": [
            ("Pasta wit gekookt", 300), ("Rundergehakt mager", 120),
            ("Tomatensaus", 150), ("Ui", 80), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak ui en gehakt 8 min. 2. Voeg tomatensaus toe, sudder 10 min. 3. Serveer over pasta."
    },
    {
        "naam": "Kipfilet met aardappelen en broccoli",
        "type": "avond",
        "kcal": 580, "kh": 52, "eiwit": 48, "vet": 14,
        "ingredienten": [
            ("Kipfilet", 180), ("Aardappel gekookt", 300),
            ("Broccoli", 150), ("Boter", 10), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak kip 10 min in olie. 2. Kook aardappelen 20 min. 3. Stoom broccoli 5 min en serveer met beetje boter."
    },
    {
        "naam": "Zalm met rijst en courgette",
        "type": "avond",
        "kcal": 610, "kh": 56, "eiwit": 42, "vet": 20,
        "ingredienten": [
            ("Zalm", 180), ("Rijst wit gekookt", 200),
            ("Courgette", 150), ("Olijfolie", 10), ("Citroen", 30)
        ],
        "bereiding": "1. Kruid zalm en bak 4 min per kant. 2. Gril courgette in olie. 3. Serveer met rijst en citroensap."
    },
    {
        "naam": "Stoemp met worst en spek",
        "type": "avond",
        "kcal": 640, "kh": 58, "eiwit": 28, "vet": 28,
        "ingredienten": [
            ("Aardappel gekookt", 350), ("Wortel rauw", 150),
            ("Spek", 40), ("Boter", 15), ("Halfvolle melk", 50)
        ],
        "bereiding": "1. Kook aardappelen en wortels gaar. 2. Stamp met boter en melk. 3. Bak spek krokant en meng erdoor."
    },
    {
        "naam": "Pasta pesto met kip en spinazie",
        "type": "avond",
        "kcal": 630, "kh": 64, "eiwit": 40, "vet": 22,
        "ingredienten": [
            ("Pasta volkoren gekookt", 280), ("Kipfilet", 150),
            ("Spinazie", 100), ("Pesto groen", 30)
        ],
        "bereiding": "1. Kook pasta. 2. Bak kip in reepjes 8 min. 3. Meng pasta met spinazie, kip en pesto."
    },
    {
        "naam": "Gebakken kabeljauw met aardappelpuree",
        "type": "avond",
        "kcal": 520, "kh": 48, "eiwit": 40, "vet": 14,
        "ingredienten": [
            ("Kabeljauw", 200), ("Aardappel gekookt", 300),
            ("Boter", 15), ("Halfvolle melk", 60), ("Broccoli", 150)
        ],
        "bereiding": "1. Stamp aardappelen met boter en melk. 2. Bak kabeljauw 4 min per kant. 3. Serveer met gestoomde broccoli."
    },
    {
        "naam": "Rijst met gehakt en paprika",
        "type": "avond",
        "kcal": 600, "kh": 66, "eiwit": 34, "vet": 18,
        "ingredienten": [
            ("Rijst wit gekookt", 220), ("Rundergehakt mager", 120),
            ("Paprika rood", 150), ("Ui", 80), ("Tomatensaus", 100)
        ],
        "bereiding": "1. Bak gehakt en ui 8 min. 2. Voeg paprika en saus toe, 10 min sudderen. 3. Serveer over rijst."
    },
    {
        "naam": "Linzen met zoete aardappel en spinazie",
        "type": "avond",
        "kcal": 560, "kh": 78, "eiwit": 24, "vet": 10,
        "ingredienten": [
            ("Linzen gekookt", 200), ("Zoete aardappel gekookt", 250),
            ("Spinazie", 100), ("Ui", 80), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak ui aan in olie. 2. Voeg linzen en zoete aardappel toe, 10 min verwarmen. 3. Roer spinazie erdoor."
    },
    {
        "naam": "Kip met groentewok en noedels",
        "type": "avond",
        "kcal": 570, "kh": 62, "eiwit": 38, "vet": 14,
        "ingredienten": [
            ("Kipfilet", 150), ("Pasta wit gekookt", 200),
            ("Broccoli", 120), ("Wortel rauw", 100), ("Sojasaus", 20)
        ],
        "bereiding": "1. Bak kip 6 min. 2. Voeg groenten toe en roerbak 4 min. 3. Meng met noedels en sojasaus."
    },
    {
        "naam": "Biefstuk met frietjes en salade",
        "type": "avond",
        "kcal": 680, "kh": 58, "eiwit": 38, "vet": 28,
        "ingredienten": [
            ("Biefstuk", 150), ("Aardappel gekookt", 300),
            ("Sla gemengd", 80), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak biefstuk 3 min per kant. 2. Bak aardappelen als blokjes in oven 25 min. 3. Serveer met salade."
    },
    {
        "naam": "Ovenschotel met kip en groenten",
        "type": "avond",
        "kcal": 540, "kh": 44, "eiwit": 42, "vet": 18,
        "ingredienten": [
            ("Kipfilet", 180), ("Aardappel gekookt", 250),
            ("Courgette", 150), ("Paprika rood", 100), ("Olijfolie", 10)
        ],
        "bereiding": "1. Snijd alles in stukken en kruid. 2. Besprenkel met olijfolie. 3. Oven 200°C, 30 min bakken."
    },
    {
        "naam": "Varkenshaas met appel en aardappelen",
        "type": "avond",
        "kcal": 590, "kh": 54, "eiwit": 40, "vet": 18,
        "ingredienten": [
            ("Varkenshaas", 160), ("Aardappel gekookt", 280),
            ("Appel", 150), ("Boter", 15), ("Ui", 60)
        ],
        "bereiding": "1. Bak varkenshaas 10 min. 2. Fruit appel en ui in boter. 3. Serveer met gekookte aardappelen."
    },
    {
        "naam": "Tonijnpasta met olijven en tomaat",
        "type": "avond",
        "kcal": 550, "kh": 66, "eiwit": 34, "vet": 12,
        "ingredienten": [
            ("Pasta volkoren gekookt", 280), ("Tonijn in water", 150),
            ("Tomatensaus", 120), ("Olijfolie", 10)
        ],
        "bereiding": "1. Kook pasta al dente. 2. Verwarm tomatensaus. 3. Meng met tonijn en pasta, besprenkel met olijfolie."
    },
    {
        "naam": "Gehaktballen met aardappelpuree en erwtjes",
        "type": "avond",
        "kcal": 640, "kh": 60, "eiwit": 36, "vet": 24,
        "ingredienten": [
            ("Rundergehakt mager", 150), ("Aardappel gekookt", 300),
            ("Erwten", 100), ("Boter", 15), ("Halfvolle melk", 60)
        ],
        "bereiding": "1. Vorm gehaktballen en bak 12 min. 2. Stamp aardappelen met boter en melk. 3. Serveer met erwtjes."
    },
    {
        "naam": "Makreel met rijst en groene salade",
        "type": "avond",
        "kcal": 580, "kh": 52, "eiwit": 36, "vet": 22,
        "ingredienten": [
            ("Makreel", 150), ("Rijst volkoren gekookt", 200),
            ("Sla gemengd", 80), ("Citroen", 30), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak makreel 4 min per kant. 2. Kook rijst. 3. Serveer met salade en citroensap."
    },

    # ── BELGISCHE KLASSIEKERS ─────────────────────────────────────────────────
    {
        "naam": "Witloof met ham en kaas uit de oven",
        "type": "avond",
        "kcal": 580, "kh": 22, "eiwit": 38, "vet": 36,
        "vezels": 4, "natrium": 1100,
        "ingredienten": [
            ("Witloof", 400), ("Kippenham", 120), ("Edammer 30+", 80),
            ("Halfvolle melk", 200), ("Boter", 20), ("Bloem", 20)
        ],
        "bereiding": "1. Blancheer witloof 10 min in gezouten water. 2. Maak bechamelsaus: smelt boter, roer bloem erdoor, voeg melk toe en roer glad. 3. Wikkel witloof in ham, leg in ovenschaal. 4. Giet bechamel erover en bestrooi met geraspte kaas. 5. Oven 200°C, 20 min gratineren."
    },
    {
        "naam": "Macaroni met kaas en ham",
        "type": "avond",
        "kcal": 640, "kh": 72, "eiwit": 34, "vet": 22,
        "vezels": 3, "natrium": 950,
        "ingredienten": [
            ("Pasta wit gekookt", 300), ("Kippenham", 100), ("Edammer 30+", 80),
            ("Halfvolle melk", 200), ("Boter", 20), ("Bloem", 20)
        ],
        "bereiding": "1. Kook macaroni al dente. 2. Maak kaassaus: smelt boter, voeg bloem toe, roer melk erdoor en laat indikken. 3. Voeg helft van de kaas toe aan de saus. 4. Meng pasta en ham met saus, doe in ovenschaal. 5. Bestrooi met resterende kaas, 15 min gratineren op 200°C."
    },
    {
        "naam": "Balletjes in tomatensaus met puree",
        "type": "avond",
        "kcal": 620, "kh": 52, "eiwit": 34, "vet": 26,
        "vezels": 5, "natrium": 780,
        "ingredienten": [
            ("Rundergehakt normaal", 200), ("Aardappel gekookt", 300),
            ("Tomatensaus", 200), ("Ui", 80), ("Halfvolle melk", 60), ("Boter", 15)
        ],
        "bereiding": "1. Vorm kleine balletjes van gehakt en kruid met peper, zout en nootmuskaat. 2. Bak balletjes rondom bruin. 3. Voeg ui en tomatensaus toe, sudder 20 min. 4. Stamp aardappelen met boter en melk tot puree. 5. Serveer balletjes op puree."
    },
    {
        "naam": "Spaghetti Bolognese",
        "type": "avond",
        "kcal": 620, "kh": 72, "eiwit": 36, "vet": 18,
        "vezels": 6, "natrium": 620,
        "ingredienten": [
            ("Pasta volkoren gekookt", 300), ("Rundergehakt mager", 150),
            ("Tomatensaus", 200), ("Ui", 80), ("Wortel", 80),
            ("Olijfolie", 10), ("Edammer 30+", 30)
        ],
        "bereiding": "1. Fruit ui en wortel aan in olijfolie. 2. Voeg gehakt toe en bak rul, 8 min. 3. Voeg tomatensaus toe en sudder 20 min op laag vuur. 4. Kook spaghetti al dente. 5. Serveer met bolognesesaus en geraspte kaas."
    },
    {
        "naam": "Lasagne",
        "type": "avond",
        "kcal": 650, "kh": 58, "eiwit": 38, "vet": 28,
        "vezels": 5, "natrium": 820,
        "ingredienten": [
            ("Pasta wit gekookt", 200), ("Rundergehakt mager", 150),
            ("Tomatensaus", 200), ("Halfvolle melk", 250), ("Boter", 25),
            ("Bloem", 25), ("Edammer 30+", 60), ("Ui", 60)
        ],
        "bereiding": "1. Maak vleessaus: bak ui en gehakt, voeg tomatensaus toe, sudder 15 min. 2. Maak bechamelsaus: boter smelten, bloem toevoegen, melk erdoor roeren. 3. Leg laagjes: lasagnevellen, vleessaus, bechamel. 4. Eindig met bechamel en kaas. 5. Oven 180°C, 35 min."
    },
    {
        "naam": "Vol-au-vent",
        "type": "avond",
        "kcal": 590, "kh": 38, "eiwit": 36, "vet": 30,
        "vezels": 2, "natrium": 780,
        "ingredienten": [
            ("Kipfilet", 150), ("Rundergehakt mager", 80),
            ("Champignon", 100), ("Halfvolle melk", 250), ("Boter", 25),
            ("Bloem", 25), ("Rijst wit gekookt", 150)
        ],
        "bereiding": "1. Kook kip en maak balletjes van gehakt. 2. Bak champignons in boter. 3. Maak witte saus: boter, bloem, melk — laat indikken. 4. Voeg kip, balletjes en champignons toe aan saus. 5. Serveer in bladerdeegbakje of op rijst."
    },
    {
        "naam": "Mosselen met friet",
        "type": "avond",
        "kcal": 610, "kh": 62, "eiwit": 32, "vet": 22,
        "vezels": 4, "natrium": 920,
        "ingredienten": [
            ("Mosselen", 400), ("Aardappel gekookt", 300),
            ("Ui", 80), ("Selder", 60), ("Boter", 20), ("Olijfolie", 10)
        ],
        "bereiding": "1. Stoof ui en selder aan in boter. 2. Voeg mosselen toe, dek af en kook 8-10 min tot mosselen open zijn. 3. Snijd aardappelen in frieten en bak krokant in olie. 4. Serveer mosselen in kookpot met friet apart. 5. Eventueel met mayonaise."
    },
    {
        "naam": "Stoemp met braadworst",
        "type": "avond",
        "kcal": 620, "kh": 54, "eiwit": 26, "vet": 30,
        "vezels": 7, "natrium": 860,
        "ingredienten": [
            ("Aardappel gekookt", 350), ("Wortel rauw", 150),
            ("Prei", 100), ("Worst", 150), ("Boter", 20), ("Halfvolle melk", 60)
        ],
        "bereiding": "1. Kook aardappelen en wortels gaar in gezouten water. 2. Snijd prei fijn en stoof zacht in boter. 3. Stamp aardappelen en wortels grof met boter en melk. 4. Roer gestoofde prei door de stoemp. 5. Bak braadworst 10 min en serveer naast de stoemp."
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 4 — WEEKSCHEMA v8
# ═══════════════════════════════════════════════════════════════════════════════

DAGEN_NL = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

MAALTIJD_TEMPLATES = {
    "Klassiek (3 maaltijden)": [
        {"naam":"Ontbijt",   "tijdstip":"07:30","type":"ontbijt"},
        {"naam":"Lunch",     "tijdstip":"12:30","type":"lunch"},
        {"naam":"Avondmaal", "tijdstip":"18:30","type":"avond"},
    ],
    "Intermittent 16:8": [
        {"naam":"Eerste maaltijd","tijdstip":"12:00","type":"ontbijt"},
        {"naam":"Tweede maaltijd","tijdstip":"16:00","type":"lunch"},
        {"naam":"Derde maaltijd", "tijdstip":"19:30","type":"avond"},
    ],
    "Intermittent 18:6": [
        {"naam":"Eerste maaltijd","tijdstip":"13:00","type":"ontbijt"},
        {"naam":"Tweede maaltijd","tijdstip":"18:30","type":"avond"},
    ],
}

TUSSENDOOR_OPTIES = [
    {"naam":"Tussendoor voormiddag","tijdstip":"10:00","type":"tussendoor"},
    {"naam":"Tussendoor namiddag",  "tijdstip":"15:00","type":"tussendoor"},
    {"naam":"Avondsnack",           "tijdstip":"21:00","type":"tussendoor"},
]

HERSTEL_MACROS = {"kh_pct":52,"eiwit_pct":33,"vet_pct":15}


def _kies_recept(moment_type, energie_doel, alle_recepten=None, gebruikte_ids=None):
    """Kies recept — vermijd al gebruikte recepten voor variatie."""
    pool = alle_recepten if alle_recepten else RECEPT_DB
    kandidaten = [r for r in pool if r.get("type") == moment_type]
    if not kandidaten: kandidaten = pool
    # Filter gebruikte recepten voor variatie
    if gebruikte_ids:
        vers = [r for r in kandidaten if r.get("id","") not in gebruikte_ids and r.get("naam","") not in gebruikte_ids]
        if vers: kandidaten = vers
    return min(kandidaten, key=lambda r: abs((r.get("kcal") or 0) - energie_doel))


def _bereken_moment_doelen(energie_basis, momenten, training_timing, profiel, training_kcal=0, verdeling_pct=None):
    """Bereken energie per moment met custom verdeling."""
    energie_dag = energie_basis + int(training_kcal or 0)
    kh_pct    = profiel.get("kh_doel_pct", 50) or 50
    eiwit_pct = profiel.get("eiwit_doel_pct", 25) or 25
    vet_pct   = profiel.get("vet_doel_pct", 25) or 25

    # Gebruik custom verdeling als opgegeven, anders standaard
    if verdeling_pct and len(verdeling_pct) == len(momenten):
        # Normaliseer naar 100%
        totaal = sum(verdeling_pct.values()) or 100
        pcts_per_moment = {i: round(v/totaal*100) for i,v in verdeling_pct.items()}
    else:
        # Standaard verdeling
        vaste   = [m for m in momenten if m["type"] != "tussendoor"]
        n_td    = len([m for m in momenten if m["type"] == "tussendoor"])
        pct_td  = 8  # per tussendoor
        rest    = 100 - n_td * pct_td
        if len(vaste) == 3:   base = {"ontbijt":30,"lunch":35,"avond":35}
        elif len(vaste) == 2:
            types = [m["type"] for m in vaste]
            base  = {"ontbijt":45,"avond":55} if "lunch" not in types else {"ontbijt":40,"lunch":60}
        else: base = {"ontbijt":100}
        # Schaal naar rest%
        factor = rest/100
        base   = {k: round(v*factor) for k,v in base.items()}
        pcts_per_moment = {}
        for i, m in enumerate(momenten):
            if m["type"] == "tussendoor":
                pcts_per_moment[i] = pct_td
            else:
                pcts_per_moment[i] = base.get(m["type"], 20)

    # Herstelmoment na training
    herstel_idx = None
    if training_timing and training_timing != "Geen training":
        uur = {"Ochtend (voor 11u)":"10:30","Middag (11u-15u)":"14:00","Avond (na 15u)":"18:00"}.get(training_timing)
        if uur:
            for i, m in enumerate(momenten):
                if m.get("tijdstip","00:00") > uur:
                    herstel_idx = i
                    break

    result = []
    for i, m in enumerate(momenten):
        e = round(energie_dag * pcts_per_moment.get(i, 20) / 100)
        if i == herstel_idx:
            kh_m  = round(e * HERSTEL_MACROS["kh_pct"] / 100 / 4)
            ei_m  = round(e * HERSTEL_MACROS["eiwit_pct"] / 100 / 4)
            vt_m  = round(e * HERSTEL_MACROS["vet_pct"] / 100 / 9)
        else:
            kh_m  = round(e * kh_pct / 100 / 4)
            ei_m  = round(e * eiwit_pct / 100 / 4)
            vt_m  = round(e * vet_pct / 100 / 9)
        result.append({**m, "energie_doel":e, "kh_doel_g":kh_m, "eiwit_doel_g":ei_m, "vet_doel_g":vt_m, "pct":pcts_per_moment.get(i,20)})
    return result


def _laad_dagschema(user_id, datum):
    try:
        r = _get_supabase().table("fuelc_dagschema").select("*").eq("user_id",user_id).eq("datum",datum).execute()
        return r.data[0] if r.data else {}
    except: return {}


def _sla_dag_als_menu(user_id: str, datum: str, momenten: list, naam: str = "") -> bool:
    """Sla alle items van een dag op als herbruikbaar dagmenu."""
    import json as _j
    try:
        if not naam:
            from datetime import datetime as _dt
            naam = f"Dagmenu {_dt.now().strftime('%d/%m %H:%M')}"
        items_per_moment = {}
        heeft_items = False
        for mi, m in enumerate(momenten):
            items = _laad_dagboek_items(user_id, datum, mi)
            if items:
                heeft_items = True
                items_per_moment[str(mi)] = {
                    "naam": m.get("naam",""),
                    "type": m.get("type",""),
                    "items": [
                        {"naam": i["naam"],
                         "hoeveelheid_g": i.get("hoeveelheid_g",100),
                         "kcal": i.get("kcal",0),
                         "kh_g": i.get("kh_g",0),
                         "eiwit_g": i.get("eiwit_g",0),
                         "vet_g": i.get("vet_g",0)}
                        for i in items
                    ]
                }
        if not heeft_items:
            st.warning("Voeg eerst voeding toe aan deze dag voor je het schema opslaat.")
            return False
        _get_supabase().table("fuelc_dagmenu").insert({
            "user_id":    user_id,
            "naam":       naam,
            "momenten":   _j.dumps(items_per_moment),
            "is_globaal": False,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False


def _laad_dagmenu_lijst(user_id: str) -> list:
    try:
        r = _get_supabase().table("fuelc_dagmenu").select("*")            .or_(f"user_id.eq.{user_id},is_globaal.eq.true")            .order("naam").execute()
        return r.data or []
    except: return []


def _sla_dagmenu(user_id: str, datum: str, momenten: list, bibliotheek: list, naam: str = "") -> bool:
    import json as _j
    try:
        if not naam:
            from datetime import datetime as _dt
            naam = f"Dagmenu {_dt.now().strftime('%d/%m %H:%M')}"
        items_per_moment = {}
        for mi, m in enumerate(momenten):
            items = _laad_dagboek_items(user_id, datum, mi)
            if items:
                items_per_moment[mi] = {
                    "naam": m.get("naam",""), "type": m.get("type",""),
                    "items": [{"naam":i["naam"],"hoeveelheid_g":i.get("hoeveelheid_g",100),
                               "kcal":i.get("kcal",0),"kh_g":i.get("kh_g",0),
                               "eiwit_g":i.get("eiwit_g",0),"vet_g":i.get("vet_g",0)} for i in items]
                }
        if not items_per_moment:
            st.warning("Geen items om op te slaan.")
            return False
        _get_supabase().table("fuelc_dagmenu").insert({
            "user_id": user_id, "naam": naam,
            "momenten": _j.dumps(items_per_moment), "is_globaal": False,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan dagmenu: {e}")
        return False


def _laad_dagmenu_op_dag(user_id: str, datum: str, dagmenu: dict, bibliotheek: list) -> bool:
    import json as _j
    try:
        momenten_data = dagmenu.get("momenten") or "{}"
        if isinstance(momenten_data, str):
            momenten_data = _j.loads(momenten_data)
        for mi_str, moment_info in momenten_data.items():
            mi = int(mi_str)
            for item in moment_info.get("items", []):
                prod = next((p for p in bibliotheek if p["naam"].lower()==item["naam"].lower()), None)
                hg = float(item.get("hoeveelheid_g",100))
                if prod is None:
                    prod = {
                        "naam": item["naam"], "id": f"db_{item['naam']}",
                        "kcal_100g": round(item.get("kcal",0)*100/max(hg,1), 1),
                        "kh_100g":   round(item.get("kh_g",0)*100/max(hg,1), 1),
                        "eiwit_100g":round(item.get("eiwit_g",0)*100/max(hg,1), 1),
                        "vet_100g":  round(item.get("vet_g",0)*100/max(hg,1), 1),
                        "vezels_100g":0,
                    }
                _sla_dagboek_item(user_id, datum, mi, prod, hg)
        return True
    except Exception as e:
        st.error(f"Fout laden dagmenu: {e}")
        return False


def _sla_dagschema_op(user_id, datum, schema):
    try:
        sb = _get_supabase()
        schema["user_id"] = user_id
        schema["datum"]   = datum
        bestaand = sb.table("fuelc_dagschema").select("id").eq("user_id",user_id).eq("datum",datum).execute()
        if bestaand.data:
            sb.table("fuelc_dagschema").update(schema).eq("user_id",user_id).eq("datum",datum).execute()
            return bestaand.data[0]["id"]
        r = sb.table("fuelc_dagschema").insert(schema).execute()
        return r.data[0]["id"] if r.data else None
    except Exception as e:
        st.error(f"Fout schema: {e}")
        return None


def _laad_dagboek_items(user_id, datum, moment):
    try:
        cache_key = f"dagboek_cache_{datum}"
        if cache_key not in st.session_state:
            r = _get_supabase().table("fuelc_dagboek")\
                .select("id,datum,moment,naam,hoeveelheid_g,kcal,kh_g,eiwit_g,vet_g,vezels_g,suikers_g,verz_g,natrium_mg,kalium_mg,calcium_mg,ijzer_mg,vitd_mcg,vitb12_mcg,omega3_g,gi,categorie,product_id")\
                .eq("user_id",user_id).eq("datum",datum).execute()
            st.session_state[cache_key] = r.data or []
        return [i for i in st.session_state[cache_key] if i.get("moment") == moment]
    except: return []


def _invalideer_dagboek_cache(datum):
    st.session_state.pop(f"dagboek_cache_{datum}", None)


def _verwijder_dagboek_item(item_id, datum=None):
    try:
        _get_supabase().table("fuelc_dagboek").delete().eq("id",item_id).execute()
        if datum: _invalideer_dagboek_cache(datum)
        return True
    except: return False


def _verwijder_alle_items_moment(user_id, datum, moment_idx):
    try:
        items = _laad_dagboek_items(user_id, datum, moment_idx)
        for item in items:
            _get_supabase().table("fuelc_dagboek").delete().eq("id",item["id"]).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except: return False


def _sla_dagboek_item(user_id, datum, moment, product, hoeveelheid):
    try:
        f = hoeveelheid / 100
        prod_id = product.get("id","")
        if not prod_id or str(prod_id).startswith("db_"):
            prod_id = None
        _get_supabase().table("fuelc_dagboek").insert({
            "user_id":user_id,"datum":datum,"moment":moment,
            "product_id":prod_id,"naam":product["naam"],
            "hoeveelheid_g":hoeveelheid,
            "kcal":      round((product.get("kcal_100g") or 0)*f, 1),
            "kh_g":      round((product.get("kh_100g") or 0)*f, 1),
            "eiwit_g":   round((product.get("eiwit_100g") or 0)*f, 1),
            "vet_g":     round((product.get("vet_100g") or 0)*f, 1),
            "vezels_g":  round((product.get("vezels_100g") or 0)*f, 1),
            "suikers_g": round((product.get("suikers_100g") or 0)*f, 2),
            "verz_g":    round((product.get("verzadigd_100g") or 0)*f, 2),
            "natrium_mg":round((product.get("natrium_100g") or 0)*f, 1),
            "kalium_mg": round((product.get("kalium_100g") or 0)*f, 1),
            "calcium_mg":round((product.get("calcium_100g") or 0)*f, 1),
            "ijzer_mg":  round((product.get("ijzer_100g") or 0)*f, 3),
            "vitd_mcg":  round((product.get("vitd_100g") or 0)*f, 3),
            "vitb12_mcg":round((product.get("vitb12_100g") or 0)*f, 3),
            "omega3_g":  round((product.get("omega3_100g") or 0)*f, 3),
            "gi":        product.get("gi") or None,
            "categorie": product.get("categorie") or product.get("cat") or None,
        }).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False


def _update_dagboek_item(item_id, datum, hoeveelheid, kcal_100, kh_100, ei_100, vt_100,
                         su_100=0, verz_100=0, na_100=0, ka_100=0, ca_100=0,
                         ij_100=0, vd_100=0, b12_100=0, om3_100=0):
    try:
        f = hoeveelheid / 100
        _get_supabase().table("fuelc_dagboek").update({
            "hoeveelheid_g":hoeveelheid,
            "kcal":      round((kcal_100 or 0)*f, 1),
            "kh_g":      round((kh_100 or 0)*f, 1),
            "eiwit_g":   round((ei_100 or 0)*f, 1),
            "vet_g":     round((vt_100 or 0)*f, 1),
            "suikers_g": round((su_100 or 0)*f, 2),
            "verz_g":    round((verz_100 or 0)*f, 2),
            "natrium_mg":round((na_100 or 0)*f, 1),
            "kalium_mg": round((ka_100 or 0)*f, 1),
            "calcium_mg":round((ca_100 or 0)*f, 1),
            "ijzer_mg":  round((ij_100 or 0)*f, 3),
            "vitd_mcg":  round((vd_100 or 0)*f, 3),
            "vitb12_mcg":round((b12_100 or 0)*f, 3),
            "omega3_g":  round((om3_100 or 0)*f, 3),
        }).eq("id", item_id).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except: return False


def _sla_recept_items(user_id, datum, moment_idx, recept, bibliotheek):
    """Sla ingrediënten van recept op als dagboek items."""
    import json as _jr
    ing_raw = recept.get("ingredienten", [])
    if isinstance(ing_raw, str):
        try: ing_raw = _jr.loads(ing_raw)
        except: ing_raw = []
    # Normaliseer naar lijst van (naam, gram)
    ing_list = []
    for item in ing_raw:
        if isinstance(item, dict):
            ing_list.append((item.get("naam",""), float(item.get("gram") or item.get("g") or 100)))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            ing_list.append((item[0], float(item[1])))
    n = max(len(ing_list), 1)
    for naam, gram in ing_list:
        prod = next((p for p in bibliotheek if p["naam"].lower() == naam.lower()), None)
        if prod is None:
            prod = {
                "naam":naam,"id":f"db_{naam}",
                "kcal_100g": round((recept.get("kcal",0)/n)/(gram/100)) if gram>0 else 0,
                "kh_100g":   round((recept.get("kh",0)/n)/(gram/100)) if gram>0 else 0,
                "eiwit_100g":round((recept.get("eiwit",0)/n)/(gram/100)) if gram>0 else 0,
                "vet_100g":  round((recept.get("vet",0)/n)/(gram/100)) if gram>0 else 0,
                "vezels_100g":0,
            }
        _sla_dagboek_item(user_id, datum, moment_idx, prod, float(gram))


def _stap_dagschema(user: dict):
    import json as _json
    from datetime import date as _date, timedelta as _td

    user_id     = user.get("id","")
    profiel     = st.session_state.get("fc_profiel", {})
    energie_dag = int(profiel.get("energie_doel", 2000) or 2000)

    _sectie("DAGSCHEMA", "#22c55e")

    # Datum
    if "ds_datum" not in st.session_state:
        st.session_state["ds_datum"] = _date.today()
    datum      = st.session_state["ds_datum"]
    dag_str    = str(datum)
    dag_naam   = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"][datum.weekday()]
    is_vandaag = datum == _date.today()

    # Navigator
    n1, n2, n3, n4 = st.columns([0.7, 4, 0.7, 2])
    with n1:
        if st.button("◀", key="ds_vorige", use_container_width=True):
            st.session_state["ds_datum"] = datum - _td(days=1); st.rerun()
    with n2:
        vd = ' <span style="background:#f97316;color:white;border-radius:4px;font-size:0.6rem;padding:1px 6px;">VANDAAG</span>' if is_vandaag else ""
        st.markdown(f'<div style="text-align:center;padding:5px 0;"><div style="font-size:1rem;font-weight:800;color:#f8fafc;">{dag_naam} {datum.strftime("%d/%m/%Y")}{vd}</div></div>', unsafe_allow_html=True)
    with n3:
        if st.button("▶", key="ds_volgende", use_container_width=True):
            st.session_state["ds_datum"] = datum + _td(days=1); st.rerun()
    with n4:
        dag_menu_open_key = f"dagmenu_open_{dag_str}"
        if st.button("💾 Opgeslagen schema's", key=f"dm_open_{dag_str}", use_container_width=True):
            st.session_state[dag_menu_open_key] = not st.session_state.get(dag_menu_open_key, False); st.rerun()

    # Eetpatroon
    patroon = profiel.get("eet_patroon", "Klassiek (3 maaltijden)")
    if patroon not in MAALTIJD_TEMPLATES: patroon = "Klassiek (3 maaltijden)"
    td_aan = [ti for ti in range(3) if profiel.get(f"td_{ti}", False)] if patroon == "Klassiek (3 maaltijden)" else []

    def _bds(pn, td):
        b = [m.copy() for m in MAALTIJD_TEMPLATES.get(pn, MAALTIJD_TEMPLATES["Klassiek (3 maaltijden)"])]
        if pn == "Klassiek (3 maaltijden)":
            for ti in td: b.append(TUSSENDOOR_OPTIES[ti].copy())
        return sorted(b, key=lambda x: x.get("tijdstip","00:00"))

    momenten_basis = _bds(patroon, td_aan)
    n_h = len([m for m in momenten_basis if m["type"] != "tussendoor"])
    def _pds(t):
        if t == "tussendoor": return 8
        return {"ontbijt":25,"lunch":35,"avond":32}.get(t,25) if n_h==3 else 48
    verdeling_pct = {i: _pds(m["type"]) for i,m in enumerate(momenten_basis)}

    # Training
    alle_trainingen   = _laad_trainingen(user_id)
    training_kcal_dag = sum(t.get("kcal_verbranding",0) or 0 for t in alle_trainingen if t.get("datum","")[:10]==dag_str)
    energie_totaal    = energie_dag + training_kcal_dag

    # Data
    bibliotheek   = _laad_gecombineerde_bibliotheek(user_id)
    alle_recepten = _laad_alle_recepten(user_id)

    # Momenten
    momenten = _bereken_moment_doelen(energie_dag, momenten_basis, "Geen training", profiel, training_kcal_dag, verdeling_pct)

    # Dagmenu panel
    # Toon verwijder melding indien aanwezig
    if f"dm_del_ok_{dag_str}" in st.session_state:
        st.success(f"✅ '{st.session_state.pop(f'dm_del_ok_{dag_str}')}' verwijderd")

    if st.session_state.get(dag_menu_open_key, False):
        with st.container():
            dm1, dm2 = st.columns(2)
            with dm1:
                st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#22c55e;margin-bottom:6px;">💾 DIT SCHEMA OPSLAAN</div>', unsafe_allow_html=True)
                dagmenu_lijst_check = _laad_dagmenu_lijst(user_id)
                eigen_schemas = [d for d in dagmenu_lijst_check if d.get("user_id") == user_id]
                if len(eigen_schemas) >= 10:
                    st.warning("⚠️ Maximum van 10 schema's bereikt. Verwijder een schema om een nieuw op te slaan.")
                else:
                    dm_naam = st.text_input("Naam", placeholder="bijv. Rustdag, Trainingsdag...", key=f"dm_naam_{dag_str}", label_visibility="collapsed")
                    if st.button("Opslaan", key=f"dm_ops_{dag_str}", use_container_width=True):
                        if _sla_dag_als_menu(user_id, dag_str, momenten, dm_naam):
                            st.success("✅ Schema opgeslagen!")
                            st.session_state.pop(dag_menu_open_key, None); st.rerun()
            with dm2:
                st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#22c55e;margin-bottom:6px;">📂 Laden &amp; verwijderen</div>', unsafe_allow_html=True)
                dagmenu_lijst = _laad_dagmenu_lijst(user_id)
                if dagmenu_lijst:
                    dm_keuze = st.selectbox("Kies schema", ["— kies —"]+[d["naam"] for d in dagmenu_lijst], key=f"dm_keuze_{dag_str}", label_visibility="collapsed")
                    if dm_keuze != "— kies —":
                        gek = next((d for d in dagmenu_lijst if d["naam"]==dm_keuze), None)
                        col_l, col_v = st.columns(2)
                        with col_l:
                            if st.button("📂 Laden", key=f"dm_laad_{dag_str}", use_container_width=True):
                                _laad_dagmenu_op_dag(user_id, dag_str, gek, bibliotheek)
                                st.session_state.pop(dag_menu_open_key, None); st.rerun()
                        with col_v:
                            if gek and gek.get("user_id") == user_id:  # enkel eigen schemas
                                if st.button("🗑 Verwijder", key=f"dm_del_{dag_str}", use_container_width=True, type="secondary"):
                                    try:
                                        _get_supabase().table("fuelc_dagmenu").delete().eq("id", gek["id"]).execute()
                                        st.session_state[f"dm_del_ok_{dag_str}"] = dm_keuze
                                        st.rerun()
                                    except Exception as del_e:
                                        st.error(f"Verwijderen mislukt: {del_e}")
                else:
                    st.caption("Nog geen schema's opgeslagen.")


    # Dagdoel balk
    alle_items_dag = []
    for mi in range(len(momenten)):
        alle_items_dag += _laad_dagboek_items(user_id, dag_str, mi)
    tot_kcal = sum(i.get("kcal",0) or 0 for i in alle_items_dag)
    pct_dag  = min(100, round(tot_kcal/energie_totaal*100)) if energie_totaal > 0 else 0
    k_dag    = "#22c55e" if pct_dag>=80 else ("#fbbf24" if pct_dag>=40 else "#334155")
    sport_nm  = next((t.get("sport","") for t in alle_trainingen if (t.get("datum","") or "")[:10]==dag_str), "")
    tr_emoji  = _sport_emoji(sport_nm)
    tr_info   = f" · {tr_emoji} +{training_kcal_dag} kcal" if training_kcal_dag > 0 else ""
    st.markdown(
        f'<div style="background:#1e293b;border-radius:8px;padding:10px 14px;margin:8px 0 12px;">' +
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">' +
        f'<span style="font-size:0.75rem;color:#64748b;">Dagdoel{tr_info}</span>' +
        f'<span style="font-size:0.9rem;font-weight:800;color:{k_dag};">{round(tot_kcal)} / {energie_totaal} kcal — {pct_dag}%</span>' +
        f'</div><div style="background:#0f172a;border-radius:6px;height:10px;">' +
        f'<div style="width:{pct_dag}%;height:100%;background:{k_dag};border-radius:6px;"></div></div></div>',
        unsafe_allow_html=True)

    # Maaltijdmomenten
    for mi, moment in enumerate(momenten):
        m_naam  = moment.get("naam","")
        m_tijd  = moment.get("tijdstip","")
        e_doel  = moment.get("energie_doel", 0)
        kh_doel = moment.get("kh_doel_g", 0)
        ei_doel = moment.get("eiwit_doel_g", 0)
        vt_doel = moment.get("vet_doel_g", 0)
        m_pct   = moment.get("pct", 0)
        m_type  = moment.get("type","")

        items   = _laad_dagboek_items(user_id, dag_str, mi)
        m_kcal  = sum(i.get("kcal",0) or 0 for i in items)
        m_kh    = sum(i.get("kh_g",0) or 0 for i in items)
        m_eiwit = sum(i.get("eiwit_g",0) or 0 for i in items)
        m_vet   = sum(i.get("vet_g",0) or 0 for i in items)
        pct_m   = min(100, round(m_kcal/e_doel*100)) if e_doel > 0 else 0
        k_m     = "#22c55e" if pct_m>=80 else ("#fbbf24" if pct_m>=40 else "#475569")
        if m_kcal > e_doel*1.1 and e_doel > 0: k_m = "#ef4444"

        open_key = f"moment_open_{dag_str}_{mi}"
        h1, h2, h3 = st.columns([0.4, 5, 1.5])
        with h1:
            lbl = "▲" if st.session_state.get(open_key) else "▼"
            if st.button(lbl, key=f"mom_tog_{dag_str}_{mi}", use_container_width=True):
                st.session_state[open_key] = not st.session_state.get(open_key, False); st.rerun()
        with h2:
            items_preview = f" · {', '.join(i.get('naam','') for i in items[:2])}{'...' if len(items)>2 else ''}" if items else ""
            st.markdown(
                f'<div style="padding:4px 0;"><span style="font-size:0.7rem;color:#64748b;">{m_tijd}</span>' +
                f'<span style="font-size:0.9rem;font-weight:700;color:#f8fafc;margin-left:8px;">{m_naam}</span>' +
                f'<span style="font-size:0.65rem;color:#475569;margin-left:6px;">{m_pct}%</span>' +
                f'<span style="font-size:0.72rem;color:#64748b;">{items_preview}</span></div>',
                unsafe_allow_html=True)
        with h3:
            st.markdown(
                f'<div style="text-align:right;padding:4px 0;"><span style="font-size:0.85rem;font-weight:800;color:{k_m};">' +
                f'{round(m_kcal)}<span style="font-size:0.65rem;color:#64748b;">/{e_doel} kcal</span></span></div>',
                unsafe_allow_html=True)
        st.markdown(f'<div style="background:#1e293b;border-radius:3px;height:4px;margin-bottom:6px;"><div style="width:{pct_m}%;height:100%;background:{k_m};border-radius:3px;"></div></div>', unsafe_allow_html=True)

        if st.session_state.get(open_key, False):
            # Zone 1: macro 2x2
            ba1, ba2 = st.columns(2)
            for col, lbl2, huidig, doel, kleur in [(ba1,"KCAL",round(m_kcal),e_doel,"#f97316"),(ba2,"KH",f"{round(m_kh)}g",f"{kh_doel}g","#22c55e")]:
                with col:
                    st.markdown(f'<div style="background:#0f172a;border-radius:8px;padding:10px 12px;margin-bottom:6px;"><div style="font-size:0.6rem;color:#64748b;">{lbl2}</div><div style="font-size:1.1rem;font-weight:800;color:{kleur};">{huidig}</div><div style="font-size:0.65rem;color:#475569;">/ {doel}</div></div>', unsafe_allow_html=True)
            ba3, ba4 = st.columns(2)
            for col, lbl2, huidig, doel, kleur in [(ba3,"EIWIT",f"{round(m_eiwit)}g",f"{ei_doel}g","#3b82f6"),(ba4,"VET",f"{round(m_vet)}g",f"{vt_doel}g","#8b5cf6")]:
                with col:
                    st.markdown(f'<div style="background:#0f172a;border-radius:8px;padding:10px 12px;margin-bottom:8px;"><div style="font-size:0.6rem;color:#64748b;">{lbl2}</div><div style="font-size:1.1rem;font-weight:800;color:{kleur};">{huidig}</div><div style="font-size:0.65rem;color:#475569;">/ {doel}</div></div>', unsafe_allow_html=True)

            # Zone 2: items
            if items:
                for item in items:
                    hg       = float(item.get("hoeveelheid_g",100) or 100)
                    f100     = 100/max(hg,1)
                    kcal_100 = round((item.get("kcal",0) or 0)*f100, 1)
                    kh_100   = round((item.get("kh_g",0) or 0)*f100, 1)
                    ei_100   = round((item.get("eiwit_g",0) or 0)*f100, 1)
                    vt_100   = round((item.get("vet_g",0) or 0)*f100, 1)
                    su_100   = round((item.get("suikers_g",0) or 0)*f100, 2)
                    verz_100 = round((item.get("verz_g",0) or 0)*f100, 2)
                    na_100   = round((item.get("natrium_mg",0) or 0)*f100, 1)
                    ka_100   = round((item.get("kalium_mg",0) or 0)*f100, 1)
                    ca_100   = round((item.get("calcium_mg",0) or 0)*f100, 1)
                    ij_100   = round((item.get("ijzer_mg",0) or 0)*f100, 3)
                    vd_100   = round((item.get("vitd_mcg",0) or 0)*f100, 3)
                    b12_100  = round((item.get("vitb12_mcg",0) or 0)*f100, 3)
                    om3_100  = round((item.get("omega3_g",0) or 0)*f100, 3)
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:10px 12px;margin-bottom:4px;">' +
                        f'<div style="font-size:0.88rem;font-weight:700;color:#f1f5f9;">{item.get("naam","")}</div>' +
                        f'<div style="font-size:0.72rem;color:#64748b;margin-top:2px;">{round(item.get("kcal",0))}kcal · {round(item.get("kh_g",0),1)}g KH · {round(item.get("eiwit_g",0),1)}g eiwit</div></div>',
                        unsafe_allow_html=True)
                    gi1, gi2, gi3 = st.columns([3,1,1])
                    with gi1:
                        nieuwe_g = st.number_input("g",1.0,2000.0,hg,5.0,key=f"g_{item['id']}",label_visibility="collapsed")
                    with gi2:
                        if st.button("💾 Sla op",key=f"upd_{item['id']}",use_container_width=True):
                            _update_dagboek_item(
                                item["id"],dag_str,nieuwe_g,
                                kcal_100,kh_100,ei_100,vt_100,
                                su_100,verz_100,na_100,ka_100,ca_100,
                                ij_100,vd_100,b12_100,om3_100)
                            _invalideer_dagboek_cache(dag_str); st.rerun()
                    with gi3:
                        if st.button("🗑 Wis",key=f"del_{item['id']}",use_container_width=True):
                            _verwijder_dagboek_item(item["id"],dag_str); st.rerun()
                st.markdown(
                    f'<div style="background:#0f172a;border-radius:6px;padding:8px 12px;margin:4px 0 8px;">' +
                    f'<span style="font-size:0.78rem;font-weight:700;color:#f97316;">▸ {round(m_kcal)} kcal</span>' +
                    f'<span style="font-size:0.72rem;color:#64748b;"> · {round(m_kh)}g KH · {round(m_eiwit)}g eiwit · {round(m_vet)}g vet</span></div>',
                    unsafe_allow_html=True)
                # Dagdeel opslaan/laden knoppen
                dm_col1, dm_col2, dm_col3 = st.columns(3)
                with dm_col1:
                    if st.button(f"🗑 Wissen",key=f"wis_{dag_str}_{mi}",use_container_width=True):
                        _verwijder_alle_items_moment(user_id,dag_str,mi); st.rerun()
                with dm_col2:
                    if st.button(f"💾 Sla dagdeel op",key=f"ddl_save_{dag_str}_{mi}",use_container_width=True):
                        st.session_state[f"ddl_save_open_{dag_str}_{mi}"] = True
                        st.rerun()
                with dm_col3:
                    if st.button(f"📂 Laad dagdeel",key=f"ddl_load_{dag_str}_{mi}",use_container_width=True):
                        st.session_state[f"ddl_load_open_{dag_str}_{mi}"] = not st.session_state.get(f"ddl_load_open_{dag_str}_{mi}", False)
                        st.rerun()

                # Dagdeel opslaan popup
                if st.session_state.get(f"ddl_save_open_{dag_str}_{mi}"):
                    ddl_naam = st.text_input("Naam dagdeel", placeholder=f"bijv. {m_naam} proteïnerijk", key=f"ddl_naam_{dag_str}_{mi}")
                    if st.button("✓ Opslaan", key=f"ddl_save_ok_{dag_str}_{mi}", type="primary"):
                        if _sla_dag_als_menu(user_id, dag_str, [momenten[mi]], ddl_naam or m_naam):
                            st.success(f"✅ '{ddl_naam or m_naam}' opgeslagen!")
                            st.session_state.pop(f"ddl_save_open_{dag_str}_{mi}", None)
                            st.rerun()
                    if st.button("✗ Annuleer", key=f"ddl_save_cancel_{dag_str}_{mi}"):
                        st.session_state.pop(f"ddl_save_open_{dag_str}_{mi}", None)
                        st.rerun()

                # Dagdeel laden
                if st.session_state.get(f"ddl_load_open_{dag_str}_{mi}"):
                    dagmenu_lijst_ddl = _laad_dagmenu_lijst(user_id)
                    if dagmenu_lijst_ddl:
                        ddl_keuze = st.selectbox("Kies dagdeel", ["— kies —"]+[d["naam"] for d in dagmenu_lijst_ddl], key=f"ddl_load_keuze_{dag_str}_{mi}", label_visibility="collapsed")
                        if ddl_keuze != "— kies —":
                            gek_ddl = next((d for d in dagmenu_lijst_ddl if d["naam"]==ddl_keuze), None)
                            if st.button(f"📂 Laden in {m_naam}", key=f"ddl_load_ok_{dag_str}_{mi}", type="primary", use_container_width=True):
                                _laad_dagmenu_op_dag(user_id, dag_str, gek_ddl, bibliotheek)
                                st.session_state.pop(f"ddl_load_open_{dag_str}_{mi}", None)
                                st.rerun()
                    else:
                        st.caption("Nog geen dagdelen opgeslagen.")

            # Zone 3: toevoegen
            st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#475569;margin:8px 0 4px;">TOEVOEGEN</div>', unsafe_allow_html=True)
            add_key = f"add_mode_{dag_str}_{mi}"
            if add_key not in st.session_state: st.session_state[add_key] = "recept"
            tm1, tm2 = st.columns(2)
            with tm1:
                if st.button("🍴 Recept",key=f"mode_rec_{dag_str}_{mi}",type="primary" if st.session_state[add_key]=="recept" else "secondary",use_container_width=True):
                    st.session_state[add_key]="recept"; st.rerun()
            with tm2:
                if st.button("🥦 Product",key=f"mode_prod_{dag_str}_{mi}",type="primary" if st.session_state[add_key]=="product" else "secondary",use_container_width=True):
                    st.session_state[add_key]="product"; st.rerun()

            if st.session_state[add_key] == "recept":
                rec_filter = st.selectbox("Filter",["Alle recepten","Eigen recepten","Favorieten","Gedeelde recepten"],key=f"rf_{dag_str}_{mi}",label_visibility="collapsed")
                if rec_filter=="Eigen recepten": rec_pool=[r for r in alle_recepten if r.get("user_id")==user_id]
                elif rec_filter=="Favorieten":   rec_pool=[r for r in alle_recepten if r.get("favoriet")]
                elif rec_filter=="Gedeelde recepten": rec_pool=[r for r in alle_recepten if r.get("is_globaal")]
                else: rec_pool=alle_recepten
                if not rec_pool: rec_pool=alle_recepten
                rec_namen=[f"{r['naam']} ({r.get('kcal',0)}kcal)" for r in rec_pool]
                rec_keuze=st.selectbox("Recept kiezen",["— kies recept —"]+rec_namen,key=f"rk_{dag_str}_{mi}",label_visibility="collapsed")
                if rec_keuze != "— kies recept —":
                    gekozen_rec=rec_pool[rec_namen.index(rec_keuze)] if rec_keuze in rec_namen else None
                    if gekozen_rec:
                        import json as _jj
                        ing=gekozen_rec.get("ingredienten","")
                        if isinstance(ing,str):
                            try: ing=_jj.loads(ing)
                            except: ing=[]
                        if ing:
                            ing_txt=" · ".join([f"{i.get('naam','')} {i.get('gram',0)}g" for i in ing[:3]])
                            st.markdown(f'<div style="font-size:0.72rem;color:#64748b;margin:4px 0;">🥗 {ing_txt}{"..." if len(ing)>3 else ""}</div>',unsafe_allow_html=True)
                        if st.button(f"➕ {gekozen_rec['naam']} toevoegen",key=f"radd_{dag_str}_{mi}",use_container_width=True):
                            _sla_recept_items(user_id,dag_str,mi,gekozen_rec,bibliotheek)
                            st.session_state.pop(f"rk_{dag_str}_{mi}",None); st.rerun()
            else:
                pc1, pc2, pc3 = st.columns([2,1,3])
                with pc1:
                    cat_f=st.selectbox("cat",["Alle"]+CATEGORIE_OPTIES,key=f"c_{dag_str}_{mi}",label_visibility="collapsed")
                with pc2:
                    fav_f=st.selectbox("fav",["Alle","⭐"],key=f"f_{dag_str}_{mi}",label_visibility="collapsed")
                gefilterd=[p for p in bibliotheek if (cat_f=="Alle" or p.get("categorie","")==cat_f) and (fav_f=="Alle" or p.get("favoriet",False))]
                with pc3:
                    keuze=st.selectbox("product",["— kies product —"]+[p["naam"] for p in gefilterd],key=f"pk_{dag_str}_{mi}",label_visibility="collapsed")
                if keuze != "— kies product —":
                    gekozen=next((p for p in gefilterd if p["naam"]==keuze),None)
                    if gekozen:
                        portie=float(gekozen.get("portie_g") or 100)
                        portie_lbl=gekozen.get("portie_label","") or f"{portie}g"
                        kcal_p=round((gekozen.get("kcal_100g",0) or 0)*portie/100)
                        kh_p=round((gekozen.get("kh_100g",0) or 0)*portie/100,1)
                        ei_p=round((gekozen.get("eiwit_100g",0) or 0)*portie/100,1)
                        st.markdown(
                            f'<div style="background:#0f172a;border-radius:6px;padding:8px 12px;margin:4px 0;">' +
                            f'<div style="font-size:0.75rem;font-weight:700;color:#f1f5f9;">{gekozen["naam"]}</div>' +
                            f'<div style="font-size:0.7rem;color:#64748b;">{portie_lbl} · {kcal_p}kcal · {kh_p}g KH · {ei_p}g eiwit</div></div>',
                            unsafe_allow_html=True)
                        ha1, ha2, ha3 = st.columns([2,1.5,1])
                        with ha1:
                            hoev=st.number_input("g",1.0,2000.0,portie,5.0,key=f"h_{dag_str}_{mi}",label_visibility="collapsed")
                        with ha2:
                            n_port=st.number_input("porties",0.5,20.0,1.0,0.5,key=f"np_{dag_str}_{mi}",label_visibility="collapsed")
                            st.markdown(f'<div style="font-size:0.68rem;color:#22c55e;">= {round(portie*n_port,1)}g</div>',unsafe_allow_html=True)
                        with ha3:
                            if st.button("➕",key=f"add_{dag_str}_{mi}",use_container_width=True):
                                gram_fin=round(portie*n_port,1) if n_port!=1.0 else hoev
                                _sla_dagboek_item(user_id,dag_str,mi,gekozen,gram_fin)
                                st.session_state.pop(f"pk_{dag_str}_{mi}",None); st.rerun()

        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)





def _safe_int(val, default=1, min_val=1, max_val=10):
    """Converteer veilig naar int, ook als val een string is."""
    try:
        v = int(float(str(val))) if val else default
        return max(min_val, min(max_val, v))
    except: return default


def _render_voedingsdagboek(user: dict):
    from datetime import date as _ddb, timedelta as _tddb
    user_id = user.get("id","")
    profiel = st.session_state.get("fc_profiel",{})
    energie_doel = int(profiel.get("energie_doel",2000) or 2000)

    _sectie("WEEKDAGBOEK", "#22c55e")

    # Week navigator
    if "db_week_offset" not in st.session_state:
        st.session_state["db_week_offset"] = 0
    offset = st.session_state["db_week_offset"]
    vandaag = _ddb.today()
    maandag = vandaag - _tddb(days=vandaag.weekday()) + _tddb(weeks=offset)

    wn1, wn2, wn3 = st.columns([0.7, 4, 0.7])
    with wn1:
        if st.button("◀", key="db_vorige_week", use_container_width=True):
            st.session_state["db_week_offset"] -= 1; st.rerun()
    with wn2:
        zondag = maandag + _tddb(days=6)
        st.markdown(
            f'<div style="text-align:center;padding:5px 0;">' +
            f'<div style="font-size:0.9rem;font-weight:800;color:#f8fafc;">' +
            f'Week van {maandag.strftime("%d/%m")} tot {zondag.strftime("%d/%m/%Y")}</div>' +
            f'</div>', unsafe_allow_html=True)
    with wn3:
        if st.button("▶", key="db_volgende_week", use_container_width=True):
            st.session_state["db_week_offset"] += 1; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    DAGEN = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

    # Laad alle welzijn data voor de week in 1 query
    @st.cache_data(ttl=60)
    def _laad_week_welzijn(uid, ma, zo):
        try:
            r = _get_supabase().table("fuelc_dagboek_welzijn").select("*")                .eq("user_id",uid).gte("datum",str(ma)).lte("datum",str(zo)).execute()
            return {row["datum"][:10]: row for row in (r.data or [])}
        except: return {}

    week_welzijn = _laad_week_welzijn(user_id, maandag, maandag+_tddb(days=6))

    # 7 dagen
    for dag_idx in range(7):
        dag_datum  = maandag + _tddb(days=dag_idx)
        dag_str    = str(dag_datum)
        dag_naam   = DAGEN[dag_idx]
        is_vandaag = dag_datum == vandaag
        is_toekomst = dag_datum > vandaag

        # Voeding data
        alle_items = []
        for mi in range(6):
            alle_items += _laad_dagboek_items(user_id, dag_str, mi)
        tot_kcal = sum(i.get("kcal",0) or 0 for i in alle_items)
        tot_kcal = sum(i.get("kcal",0) or 0 for i in alle_items)
        # Voeg training kcal toe aan dagdoel
        training_kcal_db = sum(t.get("kcal_verbranding",0) or 0
            for t in _laad_trainingen(user_id) if (t.get("datum","") or "")[:10]==dag_str)
        energie_doel_dag = energie_doel + training_kcal_db
        pct = min(100, round(tot_kcal/energie_doel_dag*100)) if energie_doel_dag > 0 else 0
        pct = min(100, round(tot_kcal/energie_doel_dag*100)) if energie_doel_dag > 0 else 0
        k   = "#22c55e" if pct>=80 else ("#fbbf24" if pct>=40 else "#334155")
        # Welzijn data
        w = week_welzijn.get(dag_str, {})
        heeft_welzijn = bool(w.get("energie_score") or w.get("slaap_uur"))

        open_key = f"db_dag_open_{dag_str}"

        # ── Dag header ────────────────────────────────────────────────────────
        dh1, dh2, dh3, dh4 = st.columns([0.5, 3, 2.5, 0.6])
        with dh1:
            lbl = "▲" if st.session_state.get(open_key) else "▼"
            if st.button(lbl, key=f"db_tog_{dag_str}", use_container_width=True):
                st.session_state[open_key] = not st.session_state.get(open_key, False)
                st.rerun()
        with dh2:
            vd_badge = ' <span style="background:#f97316;color:white;border-radius:3px;font-size:0.55rem;padding:1px 5px;">VANDAAG</span>' if is_vandaag else ""
            st.markdown(
                f'<div style="padding:4px 0;">' +
                f'<span style="font-size:0.9rem;font-weight:800;color:#f8fafc;">{dag_naam} {dag_datum.strftime("%d/%m")}{vd_badge}</span>' +
                (f'<span style="font-size:0.68rem;color:#22c55e;margin-left:8px;">✓ welzijn</span>' if heeft_welzijn else '') +
                f'</div>', unsafe_allow_html=True)
        with dh3:
            # Mini kcal balk
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">' +
                f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px;">' +
                f'<div style="width:{pct}%;height:100%;background:{k};border-radius:3px;"></div></div>' +
                f'<div style="font-size:0.75rem;color:{k};min-width:70px;text-align:right;">'
                f'{round(tot_kcal)} / {energie_doel_dag} kcal'
                + (f" · {_sport_emoji(next((t.get("sport","") for t in _laad_trainingen(user_id) if (t.get("datum","") or "")[:10]==dag_str), ""))}+{training_kcal_db}" if training_kcal_db > 0 else "") + '</div>' +
                f'</div>', unsafe_allow_html=True)
        with dh4:
            # Welzijn score dot
            en = w.get("energie_score",0) or 0
            dot_k = "#22c55e" if en>=7 else ("#fbbf24" if en>=4 else ("#ef4444" if en>0 else "#334155"))
            st.markdown(
                f'<div style="text-align:center;padding:4px 0;">' +
                f'<div style="width:12px;height:12px;border-radius:50%;background:{dot_k};margin:0 auto;" title="Energie {en}/10"></div>' +
                f'</div>', unsafe_allow_html=True)

        # ── Uitklapbare detail ────────────────────────────────────────────────
        if st.session_state.get(open_key, False):
            with st.container():
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:0 0 10px 10px;padding:16px;margin-bottom:4px;">',
                    unsafe_allow_html=True)

                # ── WELZIJN invullen ──────────────────────────────────────────
                st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#22c55e;margin-bottom:12px;letter-spacing:1px;">WELZIJN</div>', unsafe_allow_html=True)

                # Energieniveau + Stemming + Stress
                wc1, wc2, wc3 = st.columns(3)
                with wc1:
                    en_val = st.select_slider("⚡ Energieniveau",
                        options=list(range(1,11)),
                        value=_safe_int(w.get("energie_score"), 5, 1, 10),
                        key=f"db_en_{dag_str}")
                with wc2:
                    stem_val = st.select_slider("😊 Stemming",
                        options=[1,2,3,4,5],
                        value=_safe_int(w.get("stemming"), 3, 1, 5),
                        key=f"db_stem_{dag_str}")
                with wc3:
                    stress_val = st.select_slider("😤 Stress",
                        options=[1,2,3,4,5],
                        value=_safe_int(w.get("stress"), 2, 1, 5),
                        key=f"db_stress_{dag_str}")

                # Slaap
                st.markdown('<div style="font-size:0.7rem;font-weight:600;color:#64748b;margin:10px 0 6px;">SLAAP</div>', unsafe_allow_html=True)
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    slaap_uur_val = st.number_input("🌙 Uren slaap",
                        0.0, 12.0, float(w.get("slaap_uur") or 7.5), 0.5,
                        key=f"db_sl_{dag_str}")
                with sc2:
                    slaap_kwal_val = st.select_slider("💤 Slaapkwaliteit",
                        options=list(range(1,11)),
                        value=_safe_int(w.get("slaap_kwaliteit"), 5, 1, 10),
                        key=f"db_slk_{dag_str}")
                with sc3:
                    sp_val = st.select_slider("🦵 Spierpijn/vermoeidheid",
                        options=list(range(1,11)),
                        value=_safe_int(w.get("spierpijn"), 1, 1, 10),
                        key=f"db_sp_{dag_str}")

                # HF + HRV
                st.markdown('<div style="font-size:0.7rem;font-weight:600;color:#64748b;margin:10px 0 6px;">HARTSLAG & HRV (optioneel)</div>', unsafe_allow_html=True)
                hc1, hc2 = st.columns(2)
                with hc1:
                    hf_val = st.number_input("❤️ HF rust (bpm)",
                        0, 120, _safe_int(w.get("hf_rust"), 0, 0, 120), 1,
                        key=f"db_hf_{dag_str}")
                with hc2:
                    hrv_val = st.number_input("📡 HRV (ms)",
                        0, 200, _safe_int(w.get("hrv"), 0, 0, 200), 1,
                        key=f"db_hrv_{dag_str}")

                # ── VOEDING & TRAINING ────────────────────────────────────────
                st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#22c55e;margin:14px 0 10px;letter-spacing:1px;">VOEDING & TRAINING</div>', unsafe_allow_html=True)
                vc1, vc2, vc3 = st.columns(3)
                with vc1:
                    honger_val = st.select_slider("🍽️ Hongergevoel",
                        options=[1,2,3,4,5],
                        value=_safe_int(w.get("honger"), 3, 1, 5),
                        key=f"db_hg_{dag_str}",
                        help="1=geen honger, 5=constant honger")
                with vc2:
                    gi_val = st.checkbox("🫀 GI klachten tijdens training",
                        value=bool(w.get("gi_klachten", False)),
                        key=f"db_gi_{dag_str}")
                with vc3:
                    hydr_val = st.checkbox("💧 Voldoende gehydrateerd",
                        value=bool(w.get("gehydrateerd", True)),
                        key=f"db_hydr_{dag_str}")

                # Training RPE
                has_training = any(
                    t.get("datum","")[:10] == dag_str
                    for t in _laad_trainingen(user_id))
                if has_training:
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        rpe_val = st.select_slider("💪 RPE training",
                            options=list(range(1,11)),
                            value=_safe_int(w.get("rpe"), 5, 1, 10),
                            key=f"db_rpe_{dag_str}",
                            help="1=heel licht, 10=maximaal")
                    with tc2:
                        energiek_val = st.checkbox("⚡ Energiek tijdens training",
                            value=bool(w.get("energiek_training", True)),
                            key=f"db_entr_{dag_str}")
                else:
                    rpe_val = None; energiek_val = None


                # Opslaan
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Opslaan", key=f"db_ops_{dag_str}", use_container_width=True):
                    data = {
                        "user_id":          user_id,
                        "datum":            dag_str,
                        "energie_score":    en_val,
                        "stemming":         stem_val,
                        "stress":           stress_val,
                        "slaap_uur":        slaap_uur_val,
                        "slaap_kwaliteit":  slaap_kwal_val,
                        "spierpijn":        sp_val,
                        "hf_rust":          hf_val if hf_val > 0 else None,
                        "hrv":              hrv_val if hrv_val > 0 else None,
                        "honger":           honger_val,
                        "gi_klachten":      gi_val,
                        "gehydrateerd":     hydr_val,
                        "rpe":              rpe_val,
                        "energiek_training":energiek_val,
                        "gewicht_kg":       None,
                    }
                    try:
                        _get_supabase().table("fuelc_dagboek_welzijn")\
                            .upsert(data, on_conflict="user_id,datum").execute()
                        st.success("✅ Opgeslagen!")
                        _laad_week_welzijn.clear()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fout: {e}")

                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)



def _herken_categorie(naam: str, bib_cat: str = "") -> str:
    """Herken categorie op basis van productnaam als bibliotheek categorie ontbreekt."""
    cat = bib_cat or ""
    if cat and cat != "Overige":
        return cat
    n = (naam or "").lower()
    # Sojaproducten eerst (voor zuivel/vlees checks)
    if any(w in n for w in ["tofu","tempeh","sojayoghurt","sojamelk","soja drink","soja-","edamame"]):
        return "Sojaproducten"
    # Peulvruchten
    if any(w in n for w in ["boon","linze","kikker","hummus","spliterwt","lentil","chickpea",
           "kidneyboon","bruine boon","witte boon","zwarte boon","rode boon",
           "rode bonen","witte bonen","bruine bonen","zwarte bonen","kidney",
           "peulvrucht","erwt","doperwt","tuinboon"]):
        return "Peulvruchten"
    # Noten & zaden
    if any(w in n for w in ["noot","amandel","cashew","walnoot","pinda","pistache","hazelnoot",
           "macadamia","pecan","paranoot","chiazaad","lijnzaad","pompoenpit","zonnebloempit",
           "sesamzaad","hennepzaad","zaad","notenmix","noten","pindakaas","amandelboter",
           "notenboter","tahin","tahini"]):
        return "Noten & zaden"
    # Vlees & vis
    if any(w in n for w in ["garnaal","krab","kreeft","mossel","oester","scampi",
           "inktvis","zeevruchten","vis","zalm","tonijn","kabeljauw","tilapia",
           "forel","sardine","makreel","haring","pangasius","zeebaars","dorade",
           "kip","vlees","gehakt","varken","rund","lam","steak","bacon",
           "ham","worst","salami","filet","pulled","kalkoen","kipfilet",
           "biefstuk","entrecote","ossenhaas","varkenshaas","ribstuk"]):
        return "Vlees & vis"
    # Zuivel
    if any(w in n for w in ["melk","yoghurt","kwark","kaas","room","boter","skyr",
           "cottage","plattekaas","ricotta","mozzarella","cheddar","gouda","brie",
           "camembert","feta","parmezan","gruyere","mascarpone","creme fraiche"]):
        return "Zuivel"
    # Eieren
    if any(w in n for w in ["ei ","ei,","eieren","omelet","roerei","gekookt ei","gebakken ei"]):
        return "Eieren"
    # Granen & brood
    if any(w in n for w in ["brood","pasta","rijst","havermout","graan","wrap","pita",
           "tortilla","cracker","muesli","granola","cornflakes","couscous","bulgur",
           "spelt","rogge","gerst","quinoa","aardappel","zoete aardappel","friet",
           "pannenkoek","wafel","rijstwafel","cracotte"]):
        return "Granen & brood"
    # Groenten
    if any(w in n for w in ["broccoli","spinazie","wortel","tomaat","paprika","courgette",
           "sla","komkommer","champignon","avocado","ui","knoflook","prei","witloof",
           "bloemkool","spruitje","rode kool","witte kool","savooikool","knolselder",
           "venkel","asperge","biet","aubergine","pompoen","erwt","mais","groente"]):
        return "Groenten"
    # Fruit
    if any(w in n for w in ["appel","peer","banaan","aardbei","bosbes","mango","kiwi",
           "sinaas","druif","meloen","ananas","perzik","abrikoos","pruim","kers",
           "framboos","braambes","vijg","dadel","rozijn","gedroogd fruit","fruit"]):
        return "Fruit"
    # Sportvoeding
    if any(w in n for w in ["shake","proteine","whey","bcaa","gel ","energiegel",
           "energiereep","sportdrank","recovery","creatine","pre-workout","isotoon"]):
        return "Sportvoeding"
    # Vetten & oliën
    if any(w in n for w in ["olijfolie","zonnebloemolie","kokosolie","lijnzaadolie",
           "olie","margarine","frituurvet"]):
        return "Vetten & oliën"
    return "Overige"

def _bereken_performance_score(dag_data: dict, profiel: dict, welzijn: dict,
                                items_detail: list = None,
                                training_kcal: int = 0,
                                is_trainingsdag: bool = False) -> dict:
    """
    Performance score 0-100 op basis van sportvoedingswetenschap.
    6 pijlers, elk wetenschappelijk gewogen.
    """
    score = 0
    breakdown = {}

    energie_doel_basis = int(profiel.get("energie_doel", 2000) or 2000)
    energie_doel = energie_doel_basis + int(training_kcal or 0)
    kh_doel_pct  = float(profiel.get("kh_doel_pct", 50) or 50)
    ei_doel_pct  = float(profiel.get("eiwit_doel_pct", 25) or 25)
    vt_doel_pct  = float(profiel.get("vet_doel_pct", 25) or 25)

    kcal   = dag_data.get("kcal", 0) or 0
    kh     = dag_data.get("kh", 0) or 0
    eiwit  = dag_data.get("eiwit", 0) or 0
    vet    = dag_data.get("vet", 0) or 0
    vezels = dag_data.get("vezels", 0) or 0
    natrium= dag_data.get("natrium", 0) or 0
    omega3 = dag_data.get("omega3", 0) or 0
    vitd   = dag_data.get("vitd", 0) or 0
    vitb12 = dag_data.get("vitb12", 0) or 0
    n_mom_gevuld = dag_data.get("n_momenten_ingevuld", 0) or 0
    n_mom_totaal = dag_data.get("n_momenten", 3) or 3
    heeft_training = dag_data.get("heeft_training", False)
    cat_kcal = dag_data.get("cat_kcal", {})

    # ── PIJLER 1: ENERGIEBALANS (20pt) ────────────────────────────────────────
    # Gaussian curve: max bij 100% doel, daalt proportioneel
    if energie_doel > 0 and kcal > 0:
        import math as _m
        pct_e = kcal / energie_doel
        # Gaussian: sigma=0.15 → 1 SD = 15% afwijking = 60% score
        e_score = round(20 * _m.exp(-((pct_e - 1.0) ** 2) / (2 * 0.18 ** 2)))
        e_score = max(2, min(20, e_score))
    else:
        e_score = 0
    score += e_score
    breakdown["energiebalans"] = {"score": e_score, "max": 20,
        "detail": f"{round(kcal)} / {energie_doel} kcal ({round(kcal/max(energie_doel,1)*100)}%)"}

    # ── PIJLER 2: MACROKWALITEIT (25pt) ───────────────────────────────────────
    macro_score = 0

    # KH: goed gespreide inname, op trainingsdag hoger gewogen
    if kcal > 0:
        kh_act_pct = kh * 4 / kcal * 100
        kh_diff = abs(kh_act_pct - kh_doel_pct)
        kh_pts = 10 if kh_diff <= 5 else (8 if kh_diff <= 10 else (5 if kh_diff <= 20 else 2))
        macro_score += kh_pts

        # Eiwit: beoordeel spreiding over momenten
        ei_act_pct = eiwit * 4 / kcal * 100
        ei_diff = abs(ei_act_pct - ei_doel_pct)
        # Spreiding: hoeveel momenten hebben eiwit (via items_detail)
        if items_detail:
            momenten_met_eiwit = len(set(
                i.get("moment", 0) for i in items_detail
                if (i.get("eiwit_g", 0) or 0) >= 5  # min 5g eiwit per moment telt mee
            ))
            n_mom_eiwit = min(5, n_mom_totaal)
            spread_pct = momenten_met_eiwit / max(n_mom_eiwit, 1)
            ei_spread_pts = round(5 * spread_pct)  # 5pt voor goede spreiding
        else:
            ei_spread_pts = 3  # onbekend → neutraal
        ei_pts = (5 if ei_diff <= 5 else (3 if ei_diff <= 15 else 1)) + ei_spread_pts
        macro_score += min(10, ei_pts)

        # Vet: niet te laag (hormonaal), niet te hoog
        vt_act_pct = vet * 9 / kcal * 100
        if 20 <= vt_act_pct <= 35: vt_pts = 5
        elif 15 <= vt_act_pct <= 40: vt_pts = 3
        elif vt_act_pct < 15: vt_pts = 1  # te laag = hormonaal risico
        else: vt_pts = 2
        macro_score += vt_pts

    score += macro_score
    breakdown["macrokwaliteit"] = {"score": macro_score, "max": 25,
        "detail": f"KH {round(kh_act_pct if kcal>0 else 0)}% · Eiwit {round(ei_act_pct if kcal>0 else 0)}% · Vet {round(vt_act_pct if kcal>0 else 0)}%"}

    # ── PIJLER 3: MICRONUTRIËNTENDICHTHEID (20pt) ─────────────────────────────
    micro_score = 0

    # Vezels: ADH 30g, lineair
    if vezels >= 30: micro_score += 6
    elif vezels >= 20: micro_score += 4
    elif vezels >= 10: micro_score += 2

    # Omega-3: belangrijk voor herstel en inflammatie
    if omega3 >= 1.5: micro_score += 5
    elif omega3 >= 0.8: micro_score += 3
    elif omega3 >= 0.3: micro_score += 1

    # Vitamine D: crucaal voor sporters
    if vitd >= 10: micro_score += 4
    elif vitd >= 5:  micro_score += 2
    elif vitd > 0:   micro_score += 1

    # Vitamine B12: risico bij plant-based
    if vitb12 >= 2.4: micro_score += 3
    elif vitb12 >= 1:  micro_score += 2
    elif vitb12 > 0:   micro_score += 1

    # Natrium: sporters mogen meer (verlies via zweet)
    na_max = 3500 if heeft_training else 2300
    if natrium > 0:
        if natrium <= na_max: micro_score += 2
        else: micro_score += 0
    else:
        micro_score += 1  # onbekend = neutraal

    score += micro_score
    breakdown["micronutriënten"] = {"score": micro_score, "max": 20,
        "detail": f"Vezels {round(vezels)}g · Omega-3 {round(omega3,1)}g · VitD {round(vitd,1)}µg"}

    # ── PIJLER 4: MAALTIJDTIMING (15pt) ─────────────────────────────────────
    timing_score = 0
    timing_details = []

    # -- Deelpijler A: Eiwitverdeling per maaltijdtype (6pt) --
    # Haal eiwit per moment op uit items_detail
    eiwit_per_moment = {}
    moment_types = {}  # moment_idx -> type (ontbijt/lunch/avond/tussendoor)
    if items_detail:
        for it in items_detail:
            mi = int(it.get("moment", 0) or 0)
            eg = float(it.get("eiwit_g", 0) or 0)
            eiwit_per_moment[mi] = eiwit_per_moment.get(mi, 0) + eg

    # Drempelwaarden per maaltijdtype
    EI_DREMPEL = {"ontbijt": 15, "lunch": 25, "avond": 30, "tussendoor": 10}
    # Gebruik n_mom_gevuld als proxy — zonder maaltijdtype info gaan we op totaal
    hoofd_momenten = [mi for mi, eg in eiwit_per_moment.items() if eg > 0]
    n_goed_eiwit = sum(1 for mi, eg in eiwit_per_moment.items() if eg >= 20)
    n_tussen_eiwit = sum(1 for mi, eg in eiwit_per_moment.items()
                         if 0 < eg < 20 and eg >= 10)
    ei_pts = min(6, n_goed_eiwit * 2 + n_tussen_eiwit * 1)
    timing_score += ei_pts
    timing_details.append(f"{n_goed_eiwit} momenten ≥20g eiwit")

    # -- Deelpijler B: KH op trainingsdag vs rustdag (5pt) --
    kh_dag = kh
    kh_doel_basis = energie_doel * (kh_doel_pct / 100) / 4 if energie_doel > 0 else kh_doel_g
    training_kcal_dag = int(training_kcal or 0)
    is_trainingsdag = training_kcal_dag > 0

    if is_trainingsdag:
        # Op trainingsdag: KH mogen en moeten hoger zijn
        kh_doel_training = kh_doel_basis + round(training_kcal_dag * 0.5 / 4)  # 50% extra kcal als KH
        kh_pct_van_doel = kh_dag / max(kh_doel_training, 1) * 100
        if kh_pct_van_doel >= 90:
            timing_score += 5
            timing_details.append("KH goed op trainingsdag")
        elif kh_pct_van_doel >= 70:
            timing_score += 3
            timing_details.append("KH matig op trainingsdag")
        elif kh_pct_van_doel >= 50:
            timing_score += 1
            timing_details.append("KH te laag op trainingsdag")
        else:
            timing_details.append("⚠️ KH sterk te laag op trainingsdag")

        # Bonus: pre/post training KH — gebruik starttijd indien beschikbaar
        # Starttijd zit in training_kcal maar niet rechtstreeks hier beschikbaar
        # Proxy: als er KH gegeten zijn (kh_dag > kh_doel_basis * 0.8) = pre/post ok
    else:
        # Rustdag: KH binnen normale range
        kh_pct_van_doel = kh_dag / max(kh_doel_basis, 1) * 100
        if 85 <= kh_pct_van_doel <= 115:
            timing_score += 5
            timing_details.append("KH perfect op rustdag")
        elif 70 <= kh_pct_van_doel <= 130:
            timing_score += 3
            timing_details.append("KH goed op rustdag")
        else:
            timing_score += 1
            timing_details.append("KH buiten bereik op rustdag")

    # -- Deelpijler C: Maaltijdpatroon dekking (4pt) --
    if n_mom_totaal > 0:
        dekking = n_mom_gevuld / n_mom_totaal
        patroon_pts = round(4 * dekking)
        timing_score += patroon_pts
        timing_details.append(f"{n_mom_gevuld}/{n_mom_totaal} momenten gevuld")

    score += timing_score
    breakdown["maaltijdregelmaat"] = {"score": timing_score, "max": 15,
        "detail": " · ".join(timing_details)}

    # ── PIJLER 5: VOEDINGSKWALITEIT INDEX (15pt) ──────────────────────────────
    kwal_score = 0

    # Variatie voedingsgroepen
    n_groepen = len([c for c, k in cat_kcal.items() if k > 50])  # min 50kcal bijdrage
    if n_groepen >= 5:   kwal_score += 5
    elif n_groepen >= 3: kwal_score += 3
    elif n_groepen >= 2: kwal_score += 1

    # Plantaardig/dierlijk balans
    PLANTAARDIG = {"Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten","Sojaproducten"}
    DIERLIJK    = {"Vlees & vis","Zuivel","Eieren"}
    # Sportvoeding = neutraal, niet meegewogen in bewerkingsgraad
    kcal_plant = sum(k for c,k in cat_kcal.items() if c in PLANTAARDIG)
    kcal_dier  = sum(k for c,k in cat_kcal.items() if c in DIERLIJK)
    kcal_voeding = kcal_plant + kcal_dier
    if kcal_voeding > 0:
        plant_pct = kcal_plant / kcal_voeding * 100
        if 30 <= plant_pct <= 70: kwal_score += 5  # goede mix
        elif plant_pct >= 20:     kwal_score += 3
        else:                     kwal_score += 1

    # Groenten & fruit aanwezig
    groente_kcal = cat_kcal.get("Groenten", 0) + cat_kcal.get("Fruit", 0)
    if groente_kcal >= 150:   kwal_score += 5
    elif groente_kcal >= 75:  kwal_score += 3
    elif groente_kcal > 0:    kwal_score += 1

    score += kwal_score
    breakdown["voedingskwaliteit"] = {"score": kwal_score, "max": 15,
        "detail": f"{n_groepen} voedingsgroepen · {round(plant_pct if kcal_voeding>0 else 0)}% plantaardig"}

    # ── PIJLER 6: HYDRATATIE (5pt) ───────────────────────────────────────────
    # Bereken vocht uit dagschema items (gram ≈ ml voor dranken)
    ml_dag = 0
    for it in (items_detail or []):
        naam_h = (it.get("naam","") or "").lower()
        hg_h   = float(it.get("hoeveelheid_g", 0) or 0)
        cat_h  = (it.get("categorie","") or "").lower()
        is_drank = (cat_h == "dranken" or
                    any(w in naam_h for w in ["water","thee","sap","kokos","sportdrank","isotoon","bidon"]))
        is_alcohol = any(w in naam_h for w in ["bier","wijn","alcohol","cola","frisdrank"])
        if is_drank and not is_alcohol:
            ml_dag += hg_h

    # Vochtdoel: 2000ml basis + extra op basis van trainingsintensiteit en duur (ACSM)
    # Zweetverlies per uur: Z1=500ml, Z2=500ml, Z3=700ml, Z4=1000ml, Z5=1000ml
    ZWEET_ML_UUR = {"z1": 500, "z2": 500, "z3": 700, "z4": 1000, "z5": 1000}
    extra_ml_training = 0
    if heeft_training and training_kcal > 0:
        # Haal zone_verdeling en duur_min op uit dag_data indien beschikbaar
        dag_trainingen_h = dag_data.get("dag_trainingen", []) if isinstance(dag_data, dict) else []
        # Fallback: schat op basis van kcal en intensiteit
        # Gem MET ~8 = matig intensief → ~700ml/uur
        # training_kcal / gewicht_kg / MET * 60 ≈ minuten — benadering via kcal
        gewicht_h = float(profiel.get("gewicht_kg", 70) or 70)
        # Schat dominante zone op basis van MET (kcal/min/gewicht)
        # Gemiddelde MET = kcal / (gewicht * min/60)
        # Zonder duur gebruiken we kcal als proxy:
        if training_kcal < 300:
            zweet_factor = 500   # licht
        elif training_kcal < 500:
            zweet_factor = 600   # matig licht
        elif training_kcal < 700:
            zweet_factor = 700   # matig
        elif training_kcal < 900:
            zweet_factor = 850   # matig intensief
        else:
            zweet_factor = 1000  # intensief

        # Schat duur: kcal / (MET * gewicht / 60) — gebruik gem MET 8
        duur_geschat_uur = training_kcal / max(8 * gewicht_h / 60, 1) / 60
        duur_geschat_uur = min(duur_geschat_uur, 4)  # max 4u cap
        extra_ml_training = round(zweet_factor * duur_geschat_uur)
        # +500ml herstelhydratatie na training (ACSM richtlijn)
        extra_ml_training += 500

    ml_doel = 2000 + extra_ml_training
    pct_hydr = ml_dag / max(ml_doel, 1) * 100

    if pct_hydr >= 90:
        hydr_score = 5
        hydr_detail = f"{round(ml_dag)}ml — voldoende (doel: {ml_doel}ml)"
    elif pct_hydr >= 65:
        hydr_score = 3
        hydr_detail = f"{round(ml_dag)}ml — matig (doel: {ml_doel}ml)"
    elif pct_hydr >= 40:
        hydr_score = 1
        hydr_detail = f"{round(ml_dag)}ml — te weinig (doel: {ml_doel}ml)"
    else:
        hydr_score = 0
        hydr_detail = f"Geen dranken geregistreerd (doel: {ml_doel}ml)"

    score += hydr_score
    breakdown["hydratatie"] = {"score": hydr_score, "max": 5, "detail": hydr_detail}

    return {
        "score": max(0, min(100, score)),
        "breakdown": breakdown
    }


def _render_analyses(user: dict):
    from datetime import date as _da, timedelta as _ta
    import json as _json
    import math as _m

    user_id      = user.get("id","")
    profiel      = st.session_state.get("fc_profiel",{})
    energie_doel = int(profiel.get("energie_doel",2000) or 2000)
    kh_doel_pct  = float(profiel.get("kh_doel_pct",50) or 50)
    ei_doel_pct  = float(profiel.get("eiwit_doel_pct",25) or 25)
    vt_doel_pct  = float(profiel.get("vet_doel_pct",25) or 25)
    lengte_prof  = float(profiel.get("lengte_cm",175) or 175)
    kh_doel_g    = round(energie_doel * kh_doel_pct / 100 / 4)
    ei_doel_g    = round(energie_doel * ei_doel_pct / 100 / 4)
    vt_doel_g    = round(energie_doel * vt_doel_pct / 100 / 9)

    _sectie("ANALYSES", "#22c55e")

    periode = st.radio("Periode",
        ["Laatste 7 dagen","Laatste 30 dagen","Laatste 90 dagen"],
        horizontal=True, key="an_periode")
    n_dagen = {"Laatste 7 dagen":7,"Laatste 30 dagen":30,"Laatste 90 dagen":90}[periode]
    einde = _da.today()
    start = einde - _ta(days=n_dagen-1)

    # Data laden
    @st.cache_data(ttl=300)
    def _laad_gewicht_all(uid):
        try:
            r = _get_supabase().table("fuelc_dagboek_welzijn")\
                .select("datum,gewicht_kg").eq("user_id",uid)\
                .order("datum").execute()
            return [(row["datum"][:10], float(row["gewicht_kg"]))
                    for row in (r.data or []) if row.get("gewicht_kg")]
        except: return []

    @st.cache_data(ttl=120)
    def _laad_welzijn_week(uid, s, e):
        try:
            r = _get_supabase().table("fuelc_dagboek_welzijn").select("*")\
                .eq("user_id",uid).gte("datum",str(s)).lte("datum",str(e))\
                .order("datum").execute()
            return {row["datum"][:10]: row for row in (r.data or [])}
        except: return {}

    gewicht_punten = _laad_gewicht_all(user_id)
    welzijn_data   = _laad_welzijn_week(user_id, start, einde)
    gewicht_punten = _laad_gewicht_all(user_id)



    PLANTAARDIG = {"Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten","Sojaproducten"}
    DIERLIJK    = {"Vlees & vis","Zuivel","Eieren"}

    # Laad categorie lookup voor cat_kcal
    @st.cache_data(ttl=300)
    def _laad_bib_cat(uid):
        try:
            r1 = _get_supabase().table("fuelc_bibliotheek")                .select("id,categorie").eq("user_id",uid).execute()
            r2 = _get_supabase().table("fuelc_bibliotheek")                .select("id,categorie").is_("user_id","null").execute()
            return {row["id"]: row for row in (r1.data or [])+(r2.data or [])}
        except: return {}
    bib_cat_lookup = _laad_bib_cat(user_id)

    # Laad trainingen voor de periode
    alle_trainingen_raw = _laad_trainingen(user_id)
    # Maak lookup per datum
    training_per_dag = {}
    for t in alle_trainingen_raw:
        d = (t.get("datum") or "")[:10]
        if d:
            if d not in training_per_dag:
                training_per_dag[d] = []
            training_per_dag[d].append(t)

    # Voedingsdata per dag
    dagen_data = []
    for i in range(n_dagen):
        dag     = start + _ta(days=i)
        dag_str = str(dag)
        items   = []
        for mi in range(6):
            for it in _laad_dagboek_items(user_id, dag_str, mi):
                items.append({**it, "moment": mi})
        kcal    = sum(it.get("kcal",0)       or 0 for it in items)
        kh      = sum(it.get("kh_g",0)       or 0 for it in items)
        eiwit   = sum(it.get("eiwit_g",0)    or 0 for it in items)
        vet     = sum(it.get("vet_g",0)      or 0 for it in items)
        vezels  = sum(it.get("vezels_g",0)   or 0 for it in items)
        suikers = sum(it.get("suikers_g",0)  or 0 for it in items)
        verz    = sum(it.get("verz_g",0)     or 0 for it in items)
        natrium = sum(it.get("natrium_mg",0) or 0 for it in items)
        kalium  = sum(it.get("kalium_mg",0)  or 0 for it in items)
        calcium = sum(it.get("calcium_mg",0) or 0 for it in items)
        ijzer   = sum(it.get("ijzer_mg",0)   or 0 for it in items)
        vitd    = sum(it.get("vitd_mcg",0)   or 0 for it in items)
        vitb12  = sum(it.get("vitb12_mcg",0) or 0 for it in items)
        omega3  = sum(it.get("omega3_g",0)   or 0 for it in items)
        n_mom   = len(set(it.get("moment",0) for it in items)) if items else 0
        cat_kcal = {}
        for it in items:
            pid      = it.get("product_id","") or ""
            prod_bib = bib_cat_lookup.get(pid, {})
            _cat_raw = (it.get("categorie","") or prod_bib.get("categorie","") or "")
            if not _cat_raw or _cat_raw == "Overige":
                cat = _herken_categorie(it.get("naam",""), "")
            else:
                cat = _cat_raw
            cat_kcal[cat] = cat_kcal.get(cat,0) + (it.get("kcal",0) or 0)
        # Training data voor deze dag
        dag_trainingen = training_per_dag.get(dag_str, [])
        training_kcal  = sum(t.get("kcal_verbranding",0) or 0 for t in dag_trainingen)
        training_min   = sum(t.get("duur_min",0) or 0 for t in dag_trainingen)
        sporten        = list(set(t.get("sport","") for t in dag_trainingen if t.get("sport")))
        is_trainingsdag = len(dag_trainingen) > 0

        dagen_data.append({
            "datum":dag_str, "kcal":kcal,   "kh":kh,      "eiwit":eiwit,
            "vet":vet,       "vezels":vezels,"suikers":suikers,"verz":verz,
            "natrium":natrium,"kalium":kalium,"calcium":calcium,
            "ijzer":ijzer,   "vitd":vitd,   "vitb12":vitb12, "omega3":omega3,
            "n_mom":n_mom,   "cat_kcal":cat_kcal, "items":items,
            "training_kcal":training_kcal, "training_min":training_min,
            "sporten":sporten, "is_trainingsdag":is_trainingsdag,
        })

    dagen_met = [d for d in dagen_data if d["kcal"] > 0]

    # Bereken gemiddelde training kcal over de periode
    _train_dagen = [d for d in dagen_data if d.get("training_kcal",0) > 0]
    _gem_train   = round(sum(d.get("training_kcal",0) for d in _train_dagen) / max(len(_train_dagen),1)) if _train_dagen else 0
    energie_doel_incl = energie_doel + _gem_train
    # Update macro doelen op basis van energie incl. training
    kh_doel_g = round(energie_doel_incl * kh_doel_pct / 100 / 4)
    ei_doel_g = round(energie_doel_incl * ei_doel_pct / 100 / 4)
    vt_doel_g = round(energie_doel_incl * vt_doel_pct / 100 / 9)


    def _chart(html_body: str, height: int = 320):
        h_inner = height - 20
        html_full = (
            '<!DOCTYPE html><html><head>'
            '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'
            f'<style>'
            f'*{{box-sizing:border-box;margin:0;padding:0;}}'
            f'html,body{{width:100%;height:{height}px;overflow:hidden;background:#0f172a;}}'
            f'</style></head>'
            f'<body style="padding:4px 8px;">'
            f'<div style="position:relative;width:100%;height:{h_inner}px;">{html_body}</div>'
            f'</body></html>'
        )
        st.components.v1.html(html_full, height=height, scrolling=False)

    def _lijn_chart(labels, datasets, doel_lijn=None, y_label="", title="", y_max=None, y_min=None, doel_lijnen=None):
        ds_js = []
        for ds in datasets:
            ds_js.append(f'''{{
                label: '{ds["label"]}',
                data: {_json.dumps(ds["data"])},
                borderColor: '{ds["color"]}',
                backgroundColor: '{ds["color"]}22',
                borderWidth: 2.5,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: {str(ds.get("fill",False)).lower()},
                tension: 0.3,
            }}''')
        if doel_lijn is not None:
            ds_js.append(f'''{{
                label: 'Doel ({doel_lijn})',
                data: {_json.dumps([doel_lijn]*len(labels))},
                borderColor: '#f97316',
                borderWidth: 1.5,
                borderDash: [6,4],
                pointRadius: 0,
                fill: false,
                tension: 0,
            }}''')
        # Meerdere stippellijnen
        if doel_lijnen:
            for dl in doel_lijnen:
                ds_js.append(f'''{{
                    label: '{dl["label"]}',
                    data: {_json.dumps([dl["waarde"]]*len(labels))},
                    borderColor: '{dl["color"]}',
                    borderWidth: 1.5,
                    borderDash: [6,4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                }}''')
        return f'''
        <canvas id="chart__lijn_chart"></canvas>
        <script>
        new Chart(document.getElementById('chart__lijn_chart'), {{
            type: 'line',
            data: {{
                labels: {_json.dumps(labels)},
                datasets: [{",".join(ds_js)}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                animation: {{duration:0}},
                plugins: {{
                    legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }},
                    title: {{ display: {'true' if title else 'false'}, text: '{title}', color: '#f8fafc', font: {{ size: 13, weight: 'bold' }} }}
                }},
                scales: {{
                    x: {{ ticks: {{ color: '#64748b', maxTicksLimit: 10 }}, grid: {{ color: '#1e293b' }} }},
                    y: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e293b' }},
                          {('min: ' + str(y_min) + ',') if y_min is not None else 'min: 0,'}
                          {('max: ' + str(y_max) + ',') if y_max else ''}
                          title: {{ display: {'true' if y_label else 'false'}, text: '{y_label}', color: '#64748b' }} }}
                }}
            }}
        }});
        </script>'''

    def _bar_chart(labels, datasets, y_label="", y_max=None, y_min=None):
        ds_js = []
        for ds in datasets:
            ds_js.append(f'''{{
                label: '{ds["label"]}',
                data: {_json.dumps(ds["data"])},
                backgroundColor: '{ds["color"]}cc',
                borderColor: '{ds["color"]}',
                borderWidth: 1,
                borderRadius: 4,
            }}''')
        return f'''
        <canvas id="chart__bar_chart"></canvas>
        <script>
        new Chart(document.getElementById('chart__bar_chart'), {{
            type: 'bar',
            data: {{
                labels: {_json.dumps(labels)},
                datasets: [{",".join(ds_js)}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                animation: {{duration:0}},
                plugins: {{
                    legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
                }},
                scales: {{
                    x: {{ ticks: {{ color: '#64748b', maxTicksLimit: 12 }}, grid: {{ color: '#1e293b' }} }},
                    y: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e293b' }},
                          {('min: ' + str(y_min) + ',') if y_min is not None else 'min: 0,'}
                          {('max: ' + str(y_max) + ',') if y_max else ''}
                          title: {{ display: {'true' if y_label else 'false'}, text: '{y_label}', color: '#64748b' }} }}
                }}
            }}
        }});
        </script>'''

    def _donut_chart(labels, values, colors):
        return f'''
        <canvas id="chart__donut_chart"></canvas>
        <script>
        new Chart(document.getElementById('chart__donut_chart'), {{
            type: 'doughnut',
            data: {{
                labels: {_json.dumps(labels)},
                datasets: [{{ data: {_json.dumps(values)},
                    backgroundColor: {_json.dumps(colors)},
                    borderColor: '#0a0f1e', borderWidth: 2 }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false, animation: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 12 }}, padding: 16, boxWidth: 14 }} }}
                }}
            }}
        }});
        </script>'''

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Gewicht","Voedingskwaliteit","Koolhydraten","Eiwit","Vetten","Performance"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — GEWICHT
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)

        if not gewicht_punten:
            st.warning("⚖️ Je hebt nog geen gewicht ingevoerd. Vul hieronder je gewicht in om de grafiek en BMI te zien.")
        else:
            laatste = gewicht_punten[-1][1]
            eerste  = gewicht_punten[0][1]
            bmi     = round(laatste/((lengte_prof/100)**2),1) if lengte_prof > 0 else 0
            bmi_cat = "Ondergewicht" if bmi<18.5 else ("Normaal" if bmi<25 else ("Overgewicht" if bmi<30 else "Obesitas"))
            bmi_k   = "#22c55e" if bmi<25 else ("#fbbf24" if bmi<30 else "#ef4444")
            trend_g = laatste - eerste if len(gewicht_punten)>1 else 0
            trend_t = "→ Stabiel" if abs(trend_g)<0.1 else (f"▲ +{round(trend_g,1)} kg" if trend_g>0 else f"▼ {round(trend_g,1)} kg")
            trend_k = "#64748b" if abs(trend_g)<0.1 else ("#ef4444" if trend_g>0.3 else ("#22c55e" if trend_g<-0.3 else "#fbbf24"))

            # KPI badges
            k1,k2,k3,k4 = st.columns(4)
            for col,lbl,val,kl in [
                (k1,"HUIDIG",f"{round(laatste,1)} kg","#f8fafc"),
                (k2,"START",f"{round(eerste,1)} kg","#64748b"),
                (k3,"BMI",f"{bmi} — {bmi_cat}",bmi_k),
                (k4,"TREND",trend_t,trend_k)]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;">' +
                        f'<div style="font-size:0.6rem;color:#64748b;margin-bottom:3px;">{lbl}</div>' +
                        f'<div style="font-size:0.9rem;font-weight:800;color:{kl};">{val}</div>' +
                        f'</div>', unsafe_allow_html=True)

            # Grafiek
            from datetime import datetime as _dtt
            labels_g = [_dtt.strptime(p[0],"%Y-%m-%d").strftime("%d %b") for p in gewicht_punten[-60:]]
            vals_g   = [p[1] for p in gewicht_punten[-60:]]
            _chart(_lijn_chart(
                labels_g,
                [{"label":"Gewicht (kg)","data":vals_g,"color":"#22c55e","fill":True}],
                y_label="kg",
                y_min=max(0, round(min(vals_g)-10)),
                y_max=round(max(vals_g)+10)), height=420)

            # Statistieken
            if len(vals_g) >= 2:
                gem_gew = round(sum(vals_g)/len(vals_g),1)
                min_gew = round(min(vals_g),1)
                max_gew = round(max(vals_g),1)
                st.markdown(
                    f'<div style="display:flex;gap:12px;margin-top:8px;">' +
                    f'<div style="flex:1;background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">GEMIDDELD</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#f8fafc;">{gem_gew} kg</div></div>' +
                    f'<div style="flex:1;background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">LAAGST</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#22c55e;">{min_gew} kg</div></div>' +
                    f'<div style="flex:1;background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">HOOGST</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#f97316;">{max_gew} kg</div></div>' +
                    f'<div style="flex:1;background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">METINGEN</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#f8fafc;">{len(vals_g)}</div></div>' +
                    f'</div>', unsafe_allow_html=True)


            # ── Kcal inname vs doel (incl. training) ────────────────────────────
            if dagen_met:
                labels_kcal = [d["datum"][5:] for d in dagen_data if d["kcal"]>0]
                kcal_inname = [round(d["kcal"]) for d in dagen_data if d["kcal"]>0]
                kcal_doel_p = [energie_doel + round(d.get("training_kcal",0)) for d in dagen_data if d["kcal"]>0]
                if kcal_inname:
                    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 6px;">Kcal inname vs doel (incl. training)</div>', unsafe_allow_html=True)
                    _chart(_bar_chart(labels_kcal,[
                        {"label":"Inname (kcal)","data":kcal_inname,"color":"#22c55e"},
                        {"label":"Doel incl. training (kcal)","data":kcal_doel_p,"color":"#f97316"},
                    ], y_label="kcal"), height=280)


        # ── Gewicht melding na opslaan ───────────────────────────────────────
        if "_gew_diff_data" in st.session_state:
            _gd = st.session_state["_gew_diff_data"]
            st.warning(f"⚖️ Je bent {_gd['diff']} kg {_gd['richting']}. Wil je je energiebehoefte updaten naar {_gd['tdee']} kcal? (BMR: {_gd['bmr']} kcal)")
            if st.button(f"✓ Ja, update energiebehoefte naar {_gd['tdee']} kcal", key="an_gew_update_tdee", type="primary", use_container_width=True):
                try:
                    _get_supabase().table("fuelc_profiel").update({
                        "gewicht_kg": _gd["nieuw_gew"],
                        "bmr":        _gd["bmr"],
                        "tdee_basis": _gd["tdee"],
                        "energie_doel": _gd["tdee"],
                    }).eq("user_id", user_id).execute()
                    st.session_state.fc_profiel.update({
                        "gewicht_kg": _gd["nieuw_gew"],
                        "bmr":        _gd["bmr"],
                        "tdee_basis": _gd["tdee"],
                        "energie_doel": _gd["tdee"],
                    })
                    st.session_state.pop("_gew_diff_data", None)
                    st.success(f"✅ Profiel bijgewerkt — nieuw energiedoel: {_gd['tdee']} kcal")
                    st.cache_data.clear(); st.rerun()
                except Exception as _e:
                    st.error(f"Fout: {_e}")
            if st.button("✗ Nee, behoud huidige berekening", key="an_gew_geen_update"):
                st.session_state.pop("_gew_diff_data", None)
                st.rerun()

        # ── Gewicht invoer ────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("GEWICHT INVOEREN", "#22c55e")

        # Laad laatste gewichtsmeting
        try:
            _gew_r = _get_supabase().table("fuelc_dagboek_welzijn")\
                .select("datum,gewicht_kg").eq("user_id",user_id)\
                .not_.is_("gewicht_kg","null").order("datum",desc=True).limit(1).execute()
            _laatste_gew_row = _gew_r.data[0] if _gew_r.data else None
        except: _laatste_gew_row = None

        _huidig_gew = float(_laatste_gew_row["gewicht_kg"]) if _laatste_gew_row else float(profiel.get("gewicht_kg") or 70)
        _laatste_gew_datum = _laatste_gew_row["datum"] if _laatste_gew_row else None

        # Check of al gewogen deze week
        from datetime import date as _gd, timedelta as _gt
        _vandaag = _gd.today()
        _week_start = _vandaag - _gt(days=_vandaag.weekday())
        _al_gewogen = _laatste_gew_datum and _laatste_gew_datum >= str(_week_start)

        if _al_gewogen:
            st.markdown(
                f'<div style="background:#0f2d1a;border-left:3px solid #22c55e;border-radius:0 8px 8px 0;padding:10px 14px;">'
                f'<div style="font-size:0.8rem;color:#22c55e;">✓ Al gewogen deze week: <b>{_huidig_gew} kg</b> op {_laatste_gew_datum}</div>'
                f'</div>', unsafe_allow_html=True)
        
        gew_cols = st.columns([2,1])
        with gew_cols[0]:
            nieuw_gew = st.number_input(
                "Gewicht (kg)" + (" — al ingegeven deze week" if _al_gewogen else ""),
                30.0, 250.0, _huidig_gew, 0.1, key="an_gew_invoer")
        with gew_cols[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Opslaan", key="an_gew_opslaan", use_container_width=True, type="primary"):
                try:
                    from datetime import date as _gdd
                    _today_str = str(_gdd.today())
                    _get_supabase().table("fuelc_dagboek_welzijn").upsert({
                        "user_id": user_id, "datum": _today_str,
                        "gewicht_kg": nieuw_gew,
                    }, on_conflict="user_id,datum").execute()
                    st.cache_data.clear()
                    # Melding bij significante wijziging
                    _diff = round(nieuw_gew - _huidig_gew, 1)
                    if abs(_diff) >= 0.5:
                        _richting = "gedaald" if _diff < 0 else "gestegen"
                        geslacht_p = profiel.get("geslacht","man")
                        leeftijd_p = int(profiel.get("leeftijd",30) or 30)
                        lengte_p   = float(profiel.get("lengte_cm",175) or 175)
                        activiteit_p = profiel.get("activiteit", "Zittend (kantoorwerk, weinig beweging)")
                        pal_p = ACTIVITEIT_FACTOR.get(activiteit_p, 1.2)
                        bmr_nieuw  = round(10*nieuw_gew + 6.25*lengte_p - 5*leeftijd_p + (5 if geslacht_p=="man" else -161))
                        tdee_nieuw = round(bmr_nieuw * pal_p)
                        st.session_state["_gew_diff_data"] = {
                            "richting": _richting, "diff": abs(_diff),
                            "nieuw_gew": nieuw_gew, "bmr": bmr_nieuw, "tdee": tdee_nieuw
                        }
                        st.rerun()
                    else:
                        st.success(f"✅ Gewicht opgeslagen: {nieuw_gew} kg")
                        st.rerun()
                except Exception as e:
                    st.error(f"Fout: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — VOEDINGSKWALITEIT
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        if not dagen_met:
            st.info("Vul je dagschema in om voedingskwaliteit te analyseren.")
        else:
            @st.cache_data(ttl=300)
            def _laad_micro_bibliotheek(uid):
                try:
                    r1 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,categorie,vezels_100g,kalium_100g,calcium_100g,ijzer_100g,vitd_100g,vitb12_100g,omega3_100g")\
                        .eq("user_id",uid).execute()
                    r2 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,categorie,vezels_100g,kalium_100g,calcium_100g,ijzer_100g,vitd_100g,vitb12_100g,omega3_100g")\
                        .is_("user_id","null").execute()
                    return {row["id"]: row for row in (r1.data or [])+(r2.data or [])}
                except: return {}

            micro_bib = _laad_micro_bibliotheek(user_id)
            PLANTAARDIG_K = {"Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten","Sojaproducten"}
            DIERLIJK_K    = {"Vlees & vis","Zuivel","Eieren"}
            RESTGROEP_K   = {"Sauzen & spreads","Dranken","Zoetwaren & snacks"}

            kwal_dagen = []
            for dd in dagen_met:
                kcal_dag = dd["kcal"] or 1
                # Haal micronutriënten direct uit dd (al geaggregeerd)
                vezels = dd.get("vezels",0) or 0
                kalium = dd.get("kalium",0) or 0
                calcium = dd.get("calcium",0) or 0
                ijzer  = dd.get("ijzer",0) or 0
                vitd   = dd.get("vitd",0) or 0
                vitb12 = dd.get("vitb12",0) or 0
                omega3 = dd.get("omega3",0) or 0
                n_micro = 1 if (vezels or kalium or calcium or ijzer or vitd or vitb12 or omega3) else 0
                kcal_plant=0; kcal_dier=0; kcal_rest=0
                cats_dag=set()
                for it in dd.get("items",[]):
                    kc  = float(it.get("kcal",0) or 0)
                    cat = it.get("categorie","Overige") or "Overige"
                    cats_dag.add(cat)
                    # Gebruik waarden direct uit dagboek (opgeslagen bij invoer)
                    vz  = float(it.get("vezels_g",0) or 0)
                    ka  = float(it.get("kalium_mg",0) or 0)
                    ca  = float(it.get("calcium_mg",0) or 0)
                    ij  = float(it.get("ijzer_mg",0) or 0)
                    vd  = float(it.get("vitd_mcg",0) or 0)
                    b12 = float(it.get("vitb12_mcg",0) or 0)
                    om3 = float(it.get("omega3_g",0) or 0)
                    if vz or ka or ca or ij or vd or b12 or om3:
                        n_micro += 1
                    vezels  += vz
                    kalium  += ka
                    calcium += ca
                    ijzer   += ij
                    vitd    += vd
                    vitb12  += b12
                    omega3  += om3
                    if cat in PLANTAARDIG_K: kcal_plant += kc
                    elif cat in DIERLIJK_K:  kcal_dier  += kc
                    else:                    kcal_rest  += kc
                # GF bonus
                kcal_gf = (dd.get("cat_kcal",{}).get("Groenten",0) + dd.get("cat_kcal",{}).get("Fruit",0))
                gf_pct  = kcal_gf/kcal_dag*100
                # Nutriëntdensiteit score
                nd = 0
                if kcal_dag > 0:
                    v100=vezels/kcal_dag*100; k100=kalium/kcal_dag*100
                    c100=calcium/kcal_dag*100; i100=ijzer/kcal_dag*100
                    vd100=vitd/kcal_dag*100; b100=vitb12/kcal_dag*100; o100=omega3/kcal_dag*100
                    if v100>=3: nd+=2
                    elif v100>=1.5: nd+=1
                    if k100>=300: nd+=2
                    elif k100>=150: nd+=1
                    if c100>=100: nd+=1
                    if i100>=1: nd+=1
                    if vd100>=1: nd+=1
                    if b100>=0.5: nd+=1
                    if o100>=0.2: nd+=2
                    elif o100>=0.1: nd+=1
                    if gf_pct>=15: nd+=2
                    elif gf_pct>=8: nd+=1
                    nd = min(10,nd)
                rest_pct = round(kcal_rest/kcal_dag*100) if kcal_dag>0 else 0
                kwal_dagen.append({
                    "datum":dd["datum"],"nd_score":nd,"rest_pct":rest_pct,
                    "vezels":round(vezels,1),"kalium":round(kalium),
                    "calcium":round(calcium),"ijzer":round(ijzer,1),
                    "vitd":round(vitd,1),"vitb12":round(vitb12,2),"omega3":round(omega3,2),
                    "kcal_plant":kcal_plant,"kcal_dier":kcal_dier,"kcal_dag":kcal_dag,
                     "n_cats":len(cats_dag),"cats":cats_dag,"heeft_micro":n_micro>0,
                     "cat_kcal":dd.get("cat_kcal",{}),
                 })
            kwal_met  = [d for d in kwal_dagen if d["kcal_dag"]>0]
            n_met     = max(len(kwal_met),1)
            gem_nd   = round(sum(d["nd_score"] for d in kwal_met)/n_met,1) if kwal_met else 0
            gem_rest = round(sum(d["rest_pct"] for d in kwal_met)/n_met) if kwal_met else 0
            gem_cats = round(sum(d["n_cats"] for d in kwal_met)/n_met,1) if kwal_met else 0
            heeft_micro = any(d["heeft_micro"] for d in kwal_dagen)
            alle_cats_w = set()
            for d in kwal_dagen: alle_cats_w |= d["cats"]
            ontbrekend = [c for c in ["Groenten","Fruit","Vlees & vis","Peulvruchten","Noten & zaden","Zuivel"] if c not in alle_cats_w]

            k_nd  = "#22c55e" if gem_nd>=7 else ("#fbbf24" if gem_nd>=4 else "#ef4444")
            k_rst = "#22c55e" if gem_rest<=20 else ("#fbbf24" if gem_rest<=40 else "#ef4444")
            k_cat = "#22c55e" if gem_cats>=5 else ("#fbbf24" if gem_cats>=3 else "#ef4444")

            # Info expander


            # KPI badges
            q1,q3 = st.columns(2)
            with q1:
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:14px;text-align:center;margin-bottom:14px;height:110px;display:flex;flex-direction:column;justify-content:center;">'
                    f'<div style="font-size:0.6rem;color:#64748b;margin-bottom:6px;">NUTRIËNTDENSITEIT</div>'
                    f'<div style="font-size:1.4rem;font-weight:900;color:{k_nd};">{gem_nd}/10</div>'
                    f'<div style="font-size:0.65rem;color:#475569;margin-top:4px;">gem per dag</div>'
                    f'</div>', unsafe_allow_html=True)

            with q3:
                ALLE_GROEPEN_V = [
                    ("Groenten","#22c55e"),("Fruit","#a78bfa"),
                    ("Granen & brood","#f97316"),("Vlees & vis","#ef4444"),
                    ("Zuivel","#3b82f6"),("Eieren","#fbbf24"),
                    ("Peulvruchten","#4ade80"),("Noten & zaden","#f59e0b"),
                ]
                blokjes = "".join(
                    f'<div title="{g}" style="width:18px;height:18px;border-radius:4px;'
                    f'background:{"" + kl if g in alle_cats_w else "#1e293b"};'
                    f'border:1px solid {"" + kl if g in alle_cats_w else "#334155"};'
                    f'display:inline-block;margin:2px;"></div>'
                    for g, kl in ALLE_GROEPEN_V)
                adv_var = "Veel variatie" if gem_cats>=4 else ("Matige variatie" if gem_cats>=2 else "Weinig variatie")
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:14px;text-align:center;margin-bottom:14px;height:110px;display:flex;flex-direction:column;justify-content:center;">'
                    f'<div style="font-size:0.6rem;color:#64748b;margin-bottom:4px;">VARIATIE VOEDINGSGROEPEN</div>'
                    f'<div style="font-size:0.62rem;color:#94a3b8;margin-bottom:5px;">{len(alle_cats_w & {g for g,_ in ALLE_GROEPEN_V})}/8 groepen gegeten · gekleurd = aanwezig</div>'
                    f'<div style="margin-bottom:5px;line-height:1;">{blokjes}</div>'
                    f'<div style="font-size:0.72rem;font-weight:700;color:{k_cat};">{adv_var} per dag</div>'
                    f'</div>', unsafe_allow_html=True)
                if ontbrekend:
                    st.markdown(
                        f'<div style="background:#1a1200;border-left:3px solid #fbbf24;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;">'
                        f'<div style="font-size:0.72rem;font-weight:700;color:#fbbf24;margin-bottom:4px;">⚠️ ONTBREKENDE GROEPEN DEZE PERIODE</div>'
                        f'<div style="font-size:0.78rem;color:#94a3b8;">{' + '" · "' + '.join(ontbrekend)}</div>'
                        f'</div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<div style="background:#0f2d1a;border-left:3px solid #22c55e;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;">'
                        '<div style="font-size:0.72rem;font-weight:700;color:#22c55e;">✓ Alle voedingsgroepen aanwezig deze periode</div>'
                        '</div>', unsafe_allow_html=True)

            if not heeft_micro:
                st.markdown(
                    '<div style="background:#1e293b;border-radius:8px;padding:10px 14px;margin-bottom:14px;">'
                    '<div style="font-size:0.78rem;color:#64748b;">ℹ️ Micronutriënten niet beschikbaar voor alle producten. '
                    'Voeg waarden toe in de bibliotheek voor een vollediger beeld.</div>'
                    '</div>', unsafe_allow_html=True)

            nd_labels = [d["datum"][5:] for d in kwal_dagen]

            # Grafiek 1a: Nutriëntdensiteit per dag (schaal 0-10)
            nd_col1, nd_col2 = st.columns([8,1])
            with nd_col1:
                st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:2px;">Nutriëntdensiteit per dag (/10)</div>', unsafe_allow_html=True)
            with nd_col2:
                with st.expander("ℹ️"):
                    st.markdown(
                        '<div style="font-size:0.78rem;color:#94a3b8;line-height:1.7;">'
                        '<b style="color:#f8fafc;">Wat is nutriëntdensiteit?</b><br><br>'
                        'Niet alle calorieën zijn gelijk. 100 kcal uit broccoli levert veel meer vitaminen, '
                        'mineralen en vezels dan 100 kcal uit koekjes. '
                        'De nutriëntdensiteit score meet hoe <b style="color:#22c55e;">voedingsrijk</b> je eten is per calorie.<br><br>'
                        'Score 8-10 = rijke voeding vol micronutriënten<br>'
                        'Score 4-7 = redelijk, ruimte voor verbetering<br>'
                        'Score 0-3 = veel lege calorieën<br><br>'
                        'Tip: meer groenten, fruit, peulvruchten en volkoren verhogen je score.'
                        '</div>', unsafe_allow_html=True)
            nd_vals   = [d["nd_score"] if d["kcal_dag"]>0 else None for d in kwal_dagen]
            _chart(_lijn_chart(nd_labels, [
                {"label":"Nutriëntdensiteit /10","data":nd_vals,"color":"#22c55e","fill":True},
            ], doel_lijn=7, y_label="Score /10", y_max=10), height=380)

            # Grafiek 1b: % Restgroep - enkel echte restgroep (snoep, frisdrank, alcohol)
            RESTGROEP_NAMEN = {"Sauzen & spreads","Dranken","Zoetwaren & snacks"}
            rest_vals = []
            for d in kwal_dagen:
                if d["kcal_dag"] <= 0:
                    rest_vals.append(None)
                else:
                    kcal_rest = sum(v for k,v in d.get("cat_kcal",{}).items() if k in RESTGROEP_NAMEN)
                    rest_vals.append(round(kcal_rest / d["kcal_dag"] * 100))
            heeft_restgroep = any(v is not None and v > 0 for v in rest_vals)
            if heeft_restgroep:
                st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 6px;">% Restgroep per dag (snoep · frisdrank · alcohol · koek)</div>', unsafe_allow_html=True)
                _chart(_bar_chart(nd_labels, [
                    {"label":"% Restgroep","data":[v if v is not None else 0 for v in rest_vals],"color":"#ef4444"},
                ], y_label="%", y_max=100), height=300)

            # Grafiek 2: Plantaardig vs dierlijk
            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 6px;">Plantaardige vs dierlijke voeding (% kcal per dag)</div>', unsafe_allow_html=True)
            plant_pct = []
            dier_pct  = []
            for d in kwal_dagen:
                tot = d["kcal_plant"]+d["kcal_dier"]
                if tot>0:
                    plant_pct.append(round(d["kcal_plant"]/tot*100))
                    dier_pct.append(round(d["kcal_dier"]/tot*100))
                else:
                    plant_pct.append(0); dier_pct.append(0)
            plant_met = [p for p, d in zip(plant_pct, kwal_dagen) if d["kcal_plant"]+d["kcal_dier"] > 0]
            gem_plant = round(sum(plant_met)/max(len(plant_met),1)) if plant_met else 0
            plant_met = [p for p, d in zip(plant_pct, kwal_dagen) if d["kcal_plant"]+d["kcal_dier"] > 0]
            gem_plant = round(sum(plant_met)/max(len(plant_met),1)) if plant_met else 0

            pa1, pa2 = st.columns([3,1])
            with pa1:
                _chart(_bar_chart(nd_labels, [
                    {"label":"Plantaardig %","data":plant_pct,"color":"#22c55e"},
                    {"label":"Dierlijk %","data":dier_pct,"color":"#3b82f6"},
                ], y_label="%", y_max=100), height=360)
            with pa2:
                k_pl = "#22c55e" if gem_plant>=50 else ("#fbbf24" if gem_plant>=30 else "#ef4444")
                adv_pl = "Goed" if gem_plant>=50 else ("Matig" if gem_plant>=30 else "Te laag")
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:10px;padding:16px;text-align:center;height:360px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;">'
                    f'<div style="font-size:0.62rem;color:#64748b;margin-bottom:8px;">GEM PLANTAARDIG</div>'
                    f'<div style="font-size:2.2rem;font-weight:900;color:{k_pl};">{gem_plant}%</div>'
                    f'<div style="font-size:0.72rem;color:{k_pl};margin-top:4px;">{adv_pl}</div>'
                    f'<div style="font-size:0.65rem;color:#475569;margin-top:10px;line-height:1.5;">Doel: min 50% plantaardig</div>'
                    f'</div>', unsafe_allow_html=True)
            # Grafiek 3: Vezels
            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 6px;">Vezelinname per dag (ADH = 30g)</div>', unsafe_allow_html=True)
            vez_vals = [d["vezels"] for d in kwal_dagen]
            gem_vez  = round(sum(vez_vals)/max(len(vez_vals),1),1)
            k_vez = "#22c55e" if gem_vez>=25 else ("#fbbf24" if gem_vez>=15 else "#ef4444")
            _chart(_lijn_chart(nd_labels,
                [{"label":"Vezels (g)","data":vez_vals,"color":"#22c55e","fill":True}],
                doel_lijn=30, y_label="gram"), height=360)
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px 14px;margin-top:4px;">'
                f'<span style="font-size:0.8rem;color:{k_vez};">Gem {gem_vez}g/dag — '
                f'{"✓ voldoende" if gem_vez>=25 else ("⚠️ net onder ADH" if gem_vez>=15 else "⚠️ te laag — voeg meer groenten, volkoren en peulvruchten toe")}'
                f'</span></div>', unsafe_allow_html=True)

            # Micronutriënten vs ADH
            if heeft_micro:
                mi1, mi2 = st.columns([4,1])
                with mi1:
                    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 8px;">Micronutriënten</div>', unsafe_allow_html=True)
                with mi2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("ℹ️"):
                        st.markdown('<div style="font-size:0.75rem;color:#94a3b8;line-height:1.6;">Gebaseerd op producten in de NEVO-databank of waarvoor je micronutriënten hebt ingevuld in de bibliotheek.</div>', unsafe_allow_html=True)
                gem_kal = round(sum(d["kalium"] for d in kwal_met)/n_met)
                gem_cal = round(sum(d["calcium"] for d in kwal_met)/n_met)
                gem_ij  = round(sum(d["ijzer"] for d in kwal_met)/n_met,1)
                gem_vd  = round(sum(d["vitd"] for d in kwal_met)/n_met,1)
                gem_b12 = round(sum(d["vitb12"] for d in kwal_met)/n_met,2)
                gem_om3 = round(sum(d["omega3"] for d in kwal_met)/n_met,2)
                MICROS = [
                    ("🥬 Kalium",gem_kal,3500,"mg"),
                    ("🦴 Calcium",gem_cal,1000,"mg"),
                    ("🩸 IJzer",gem_ij,15,"mg"),
                    ("☀️ Vitamine D",gem_vd,15,"µg"),
                    ("🧬 Vitamine B12",gem_b12,2.4,"µg"),
                    ("🐟 Omega-3",gem_om3,1.5,"g"),
                ]
                MICRO_TIPS = {
                    "🥬 Kalium":       "Rijke bronnen: banaan, aardappel, avocado, spinazie, witte bonen, zalm",
                    "🦴 Calcium":      "Rijke bronnen: melk, yoghurt, kaas, broccoli, amandelen, sardines",
                    "🩸 IJzer":        "Rijke bronnen: rood vlees, linzen, spinazie, tofu, pompoenpitten — combineer met vitamine C",
                    "☀️ Vitamine D":   "Rijke bronnen: vette vis (zalm, makreel), eieren, verrijkte zuivel — zon is essentieel",
                    "🧬 Vitamine B12": "Rijke bronnen: vlees, vis, eieren, melk — bij plantaardig dieet: supplement aanbevolen",
                    "🐟 Omega-3":      "Rijke bronnen: zalm, makreel, haring, walnoten, lijnzaad, chiazaad",
                }
                for lbl_m,waarde_m,adh_m,eenh_m in MICROS:
                    if waarde_m==0: continue
                    pct_m = min(150,round(waarde_m/max(adh_m,0.001)*100))
                    kl_m = "#22c55e" if pct_m>=80 else ("#fbbf24" if pct_m>=50 else "#ef4444")
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:7px;">'
                        f'<div style="min-width:130px;font-size:0.78rem;color:#94a3b8;">{lbl_m}</div>'
                        f'<div style="flex:1;background:#1e293b;border-radius:3px;height:7px;">'
                        f'<div style="width:{min(100,pct_m)}%;height:100%;background:{kl_m};border-radius:3px;"></div></div>'
                        f'<div style="min-width:80px;font-size:0.75rem;color:{kl_m};text-align:right;">{waarde_m}{eenh_m}/{adh_m}{eenh_m}</div>'
                        f'</div>', unsafe_allow_html=True)
                    if pct_m < 80 and lbl_m in MICRO_TIPS:
                        kleur_tip = "#ef4444" if pct_m < 50 else "#fbbf24"
                        st.markdown(
                            f'<div style="margin-left:140px;margin-bottom:10px;'
                            f'padding:6px 10px;background:#1e293b;'
                            f'border-left:2px solid {kleur_tip};border-radius:0 6px 6px 0;">'
                            f'<div style="font-size:0.7rem;color:{kleur_tip};font-weight:600;margin-bottom:2px;">'  
                            f'{"🔴 Te laag" if pct_m<50 else "🟡 Net onder ADH"}</div>'
                            f'<div style="font-size:0.7rem;color:#64748b;">{MICRO_TIPS[lbl_m]}</div>'
                            f'</div>', unsafe_allow_html=True)

            # ── Groenten & fruit overzicht ──────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("GROENTEN & FRUIT", "#22c55e")

            # Bereken groenten en fruit gram per dag
            groenten_per_dag = []
            fruit_per_dag    = []
            for dd in dagen_data:
                gr_g = 0; fr_g = 0
                for it in dd.get("items", []):
                    hg  = float(it.get("hoeveelheid_g", 0) or 0)
                    pid = it.get("product_id", "") or ""
                    _cat_raw = (it.get("categorie", "") or
                               bib_cat_lookup.get(pid, {}).get("categorie", "") or "")
                    if not _cat_raw or _cat_raw == "Overige":
                        cat_gf = _herken_categorie(it.get("naam", ""), "")
                    else:
                        cat_gf = _cat_raw
                    if cat_gf == "Groenten": gr_g += hg
                    elif cat_gf == "Fruit":  fr_g += hg
                groenten_per_dag.append(round(gr_g))
                fruit_per_dag.append(round(fr_g))

            dagen_met_gf = [i for i, d in enumerate(dagen_data) if d["kcal"] > 0]
            n_gf = max(len(dagen_met_gf), 1)
            gem_groenten = round(sum(groenten_per_dag[i] for i in dagen_met_gf) / n_gf)
            gem_fruit    = round(sum(fruit_per_dag[i] for i in dagen_met_gf) / n_gf)
            gem_totaal   = gem_groenten + gem_fruit
            DOEL_GROENTEN = 300
            DOEL_FRUIT    = 250
            DOEL_TOTAAL   = DOEL_GROENTEN + DOEL_FRUIT  # 550g
            pct_gr   = min(150, round(gem_groenten / DOEL_GROENTEN * 100))
            pct_fr   = min(150, round(gem_fruit    / DOEL_FRUIT    * 100))
            pct_doel_gf = min(150, round(gem_totaal / DOEL_TOTAAL * 100))
            k_gf  = "#22c55e" if gem_totaal >= DOEL_TOTAAL else ("#fbbf24" if gem_totaal >= DOEL_TOTAAL*0.65 else "#ef4444")
            k_gr  = "#22c55e" if gem_groenten >= DOEL_GROENTEN else ("#fbbf24" if gem_groenten >= DOEL_GROENTEN*0.65 else "#ef4444")
            k_fr  = "#22c55e" if gem_fruit >= DOEL_FRUIT else ("#fbbf24" if gem_fruit >= DOEL_FRUIT*0.65 else "#ef4444")
            adv_gf = ("✓ Voldoende groenten en fruit (doel: 300g groenten + 250g fruit)" if gem_totaal >= DOEL_TOTAAL
                      else ("⚠️ Matig — probeer meer te variëren" if gem_totaal >= DOEL_TOTAAL * 0.65
                      else "⚠️ Te weinig — verhoog je inname van groenten en fruit"))

            # KPI rij
            gf1, gf2, gf3, gf4 = st.columns(4)
            for col, lbl, val, kl in [
                (gf1, "GEM GROENTEN/DAG", f"{gem_groenten}g / {DOEL_GROENTEN}g", k_gr),
                (gf2, "GEM FRUIT/DAG",    f"{gem_fruit}g / {DOEL_FRUIT}g",       k_fr),
                (gf3, "TOTAAL/DAG",       f"{gem_totaal}g / {DOEL_TOTAAL}g",     k_gf),
                (gf4, "% VAN DOEL",       f"{pct_doel_gf}%",                     k_gf),
            ]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;">' +
                        f'<div style="font-size:0.6rem;color:#64748b;">{lbl}</div>' +
                        f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>' +
                        f'</div>', unsafe_allow_html=True)

            # Grafiek
            gf_labels = [d["datum"][5:] for d in dagen_data]
            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">Groenten & fruit per dag (g)</div>', unsafe_allow_html=True)
            _chart(_lijn_chart(gf_labels, [
                {"label": "Groenten (g)", "data": groenten_per_dag, "color": "#22c55e", "fill": False},
                {"label": "Fruit (g)",    "data": fruit_per_dag,    "color": "#a78bfa", "fill": False},
            ], doel_lijnen=[
                {"label": "Doel groenten (300g)", "waarde": 300, "color": "#22c55e"},
                {"label": "Doel fruit (250g)",    "waarde": 250, "color": "#a78bfa"},
            ], y_label="gram"), height=300)

            # Advies tekst
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:12px 14px;margin-top:6px;">' +
                f'<span style="font-size:0.82rem;color:{k_gf};">{adv_gf}</span>' +
                f'<span style="font-size:0.75rem;color:#64748b;"> · Aanbeveling: min. 300g groenten + 250g fruit per dag</span>' +
                f'</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — KOOLHYDRATEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        if not dagen_met:
            st.info("Nog geen voedingsdata.")
        else:
            labels_d = [d["datum"][5:] for d in dagen_data]

            @st.cache_data(ttl=300)
            def _laad_suikers_bib(uid):
                try:
                    r1 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,naam,suikers_100g").eq("user_id",uid).execute()
                    r2 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,naam,suikers_100g").is_("user_id","null").execute()
                    return {row["id"]: row for row in (r1.data or [])+(r2.data or [])}
                except: return {}

            su_bib = _laad_suikers_bib(user_id)

            # Suikers per dag + top producten
            suikers_per_dag = []
            suiker_producten = {}  # naam -> {"su": gram, "gi": waarde}
            # Laad suikers + GI uit bibliotheek als fallback voor oude items
            @st.cache_data(ttl=300)
            def _laad_su_gi_bib(uid):
                try:
                    r1 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,naam,suikers_100g,gi").eq("user_id",uid).execute()
                    r2 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,naam,suikers_100g,gi").is_("user_id","null").execute()
                    return {row["id"]: row for row in (r1.data or [])+(r2.data or [])}
                except: return {}
            su_gi_bib = _laad_su_gi_bib(user_id)

            for dd in dagen_data:
                dag_su = dd.get("suikers", 0) or 0
                for it in dd.get("items",[]):
                    hg  = float(it.get("hoeveelheid_g",100) or 100)
                    su  = float(it.get("suikers_g",0) or 0)
                    gi  = it.get("gi") or None
                    # Fallback via bibliotheek voor oude items zonder suikers_g
                    if su == 0:
                        pid  = it.get("product_id","") or ""
                        prod = su_gi_bib.get(pid, {})
                        su   = float(prod.get("suikers_100g") or 0) * hg / 100
                        if not gi: gi = prod.get("gi") or None
                    if su > 0:
                        naam = it.get("naam","Onbekend") or "Onbekend"
                        if naam not in suiker_producten:
                            suiker_producten[naam] = {"su": 0, "gi": gi}
                        suiker_producten[naam]["su"] += su
                        if gi and not suiker_producten[naam]["gi"]:
                            suiker_producten[naam]["gi"] = gi
                suikers_per_dag.append(round(dag_su if dag_su > 0 else sum(
                    float(it.get("suikers_g",0) or 0) for it in dd.get("items",[])), 1))
            gem_kh = round(sum(d["kh"] for d in dagen_met)/len(dagen_met),1)
            gem_su = round(sum(s for s,d in zip(suikers_per_dag,dagen_data) if d["kcal"]>0)/max(len(dagen_met),1),1)
            pct_kh = round(gem_kh/max(kh_doel_g,1)*100)
            su_pct = round(gem_su/max(gem_kh,1)*100)
            k_kh = "#22c55e" if 85<=pct_kh<=115 else ("#fbbf24" if 70<=pct_kh<=130 else "#ef4444")
            k_su = "#22c55e" if su_pct<=10 else ("#fbbf24" if su_pct<=20 else "#ef4444")

            m1,m2,m3,m4 = st.columns(4)
            for col,lbl,val,kl in [
                (m1,"GEM KH/DAG",f"{gem_kh}g",k_kh),
                (m2,"KH DOEL",f"{kh_doel_g}g","#64748b"),
                (m3,"TOEGEV. SUIKERS/DAG",f"{gem_su}g",k_su),
                (m4,"SUIKERS % VAN KH",f"{su_pct}%",k_su)]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">{lbl}</div>'
                        f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>'
                        f'</div>', unsafe_allow_html=True)

            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">KH per dag vs doel</div>', unsafe_allow_html=True)
            kh_vals = [round(d["kh"],1) for d in dagen_data]
            _chart(_lijn_chart(labels_d,
                [{"label":"KH (g)","data":kh_vals,"color":"#22c55e","fill":True}],
                doel_lijn=kh_doel_g, y_label="gram"), height=260)

            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 6px;">Toegevoegde suikers vs totale KH per dag</div>', unsafe_allow_html=True)
            _chart(_bar_chart(labels_d, [
                {"label":"Totale KH (g)","data":kh_vals,"color":"#22c55e"},
                {"label":"Toegevoegde suikers (g)","data":suikers_per_dag,"color":"#f97316"},
            ], y_label="gram"), height=280)

            # Meldingen >10%
            meldingen_su = [(d["datum"][5:], s, round(s/d["kh"]*100))
                            for d,s in zip(dagen_data,suikers_per_dag)
                            if d["kh"]>0 and s/d["kh"]*100>10]
            if meldingen_su:
                st.markdown(
                    '<div style="background:#1a0a0a;border-left:3px solid #f97316;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:8px;">'
                    '<div style="font-size:0.72rem;font-weight:700;color:#f97316;margin-bottom:6px;">⚠️ DAGEN MET SUIKERS &gt;10% VAN KH</div>',
                    unsafe_allow_html=True)
                for datum_m,su_m,pct_m in meldingen_su:
                    st.markdown(f'<div style="font-size:0.78rem;color:#94a3b8;padding:2px 0;">· {datum_m}: {su_m}g = {pct_m}%</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Top suikerproducten met GI
            if suiker_producten:
                st.markdown(
                    '<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:20px 0 4px;">🍬 Voedingsmiddelen met toegevoegde suikers — top deze periode</div>',
                    unsafe_allow_html=True)
                st.markdown(
                    '<div style="font-size:0.7rem;color:#64748b;margin-bottom:10px;">GI: laag &lt;55 · matig 55-70 · hoog &gt;70 · — = niet bekend</div>',
                    unsafe_allow_html=True)
                top_su = sorted(suiker_producten.items(), key=lambda x: -x[1]["su"] if isinstance(x[1], dict) else -x[1])[:8]
                max_su_val = top_su[0][1]["su"] if isinstance(top_su[0][1], dict) else top_su[0][1] if top_su else 1
                for naam_su, data_su in top_su:
                    gram_su = data_su["su"] if isinstance(data_su, dict) else data_su
                    gi_su   = data_su.get("gi") if isinstance(data_su, dict) else None
                    pct_bar = round(gram_su/max(max_su_val,1)*100)
                    if gi_su:
                        gi_int = int(gi_su)
                        gi_lbl = str(gi_int)
                        gi_kl  = "#22c55e" if gi_int<55 else ("#fbbf24" if gi_int<=70 else "#ef4444")
                    else:
                        gi_lbl = "—"; gi_kl = "#475569"
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:9px 12px;margin-bottom:5px;">'
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                        f'<div style="flex:1;font-size:0.78rem;color:#f1f5f9;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{naam_su}</div>'
                        f'<div style="font-size:0.72rem;color:#f97316;font-weight:700;min-width:40px;text-align:right;">{round(gram_su,1)}g</div>'
                        f'<div style="font-size:0.72rem;font-weight:700;color:{gi_kl};min-width:52px;text-align:right;">GI {gi_lbl}</div>'
                        f'</div>'
                        f'<div style="background:#0f172a;border-radius:3px;height:5px;">'
                        f'<div style="width:{pct_bar}%;height:100%;background:#f97316;border-radius:3px;"></div>'
                        f'</div></div>', unsafe_allow_html=True)

            # ── GI overzicht ─────────────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("GLYCEMISCHE INDEX OVERZICHT", "#22c55e")
            st.markdown(
                '<div style="font-size:0.7rem;color:#64748b;margin-bottom:12px;">' +
                'GI laag &lt;55 · matig 55-70 · hoog &gt;70 · gewogen GI = gemiddelde gewogen naar kcal bijdrage</div>',
                unsafe_allow_html=True)

            # Verzamel alle producten met GI uit de periode
            gi_producten = {}  # naam -> {gi, kcal_totaal}
            for dd in dagen_met:
                for it in dd.get("items", []):
                    gi_val = it.get("gi") or None
                    if not gi_val:
                        # Fallback: zoek GI in VOEDSEL_DB op naam
                        naam_gi = it.get("naam", "")
                        for p in VOEDSEL_DB:
                            if p["naam"].lower() == naam_gi.lower() and p.get("gi"):
                                gi_val = p["gi"]
                                break
                    if gi_val and int(gi_val) > 0:
                        naam_gi = it.get("naam", "Onbekend")
                        kcal_gi = float(it.get("kcal", 0) or 0)
                        if naam_gi not in gi_producten:
                            gi_producten[naam_gi] = {"gi": int(gi_val), "kcal": 0, "gram": 0}
                        gi_producten[naam_gi]["kcal"] += kcal_gi
                        gi_producten[naam_gi]["gram"] += float(it.get("hoeveelheid_g", 0) or 0)

            if gi_producten:
                # Gewogen GI berekenen
                totaal_kcal_gi = sum(v["kcal"] for v in gi_producten.values())
                gewogen_gi = round(sum(v["gi"] * v["kcal"] for v in gi_producten.values()) / max(totaal_kcal_gi, 1))
                k_wgi = "#22c55e" if gewogen_gi < 55 else ("#fbbf24" if gewogen_gi <= 70 else "#ef4444")
                cat_wgi = "Laag" if gewogen_gi < 55 else ("Matig" if gewogen_gi <= 70 else "Hoog")

                # KPI gewogen GI
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:20px;">' +
                    f'<div><div style="font-size:0.6rem;color:#64748b;">GEWOGEN GI DEZE PERIODE</div>' +
                    f'<div style="font-size:2rem;font-weight:900;color:{k_wgi};">{gewogen_gi}</div>' +
                    f'<div style="font-size:0.72rem;color:{k_wgi};">{cat_wgi} GI</div></div>' +
                    f'<div style="font-size:0.78rem;color:#94a3b8;line-height:1.6;">' +
                    f'{"✓ Goede GI score — overwegend trage koolhydraten." if gewogen_gi < 55 else ("⚠️ Matige GI — probeer meer volkoren en groenten." if gewogen_gi <= 70 else "⚠️ Hoge GI — vervang witte rijst, wit brood en suikerrijke producten.")}' +
                    f'</div></div>', unsafe_allow_html=True)

                # Drie kolommen: laag / matig / hoog
                laag  = {k:v for k,v in gi_producten.items() if v["gi"] < 55}
                matig = {k:v for k,v in gi_producten.items() if 55 <= v["gi"] <= 70}
                hoog  = {k:v for k,v in gi_producten.items() if v["gi"] > 70}

                gc1, gc2, gc3 = st.columns(3)
                for col, titel, prod_dict, kleur in [
                    (gc1, "🟢 Laag GI (<55)",   laag,  "#22c55e"),
                    (gc2, "🟡 Matig GI (55-70)", matig, "#fbbf24"),
                    (gc3, "🔴 Hoog GI (>70)",    hoog,  "#ef4444"),
                ]:
                    with col:
                        st.markdown(
                            f'<div style="font-size:0.72rem;font-weight:700;color:{kleur};margin-bottom:8px;">{titel} ({len(prod_dict)})</div>',
                            unsafe_allow_html=True)
                        if prod_dict:
                            gesorteerd = sorted(prod_dict.items(), key=lambda x: -x[1]["kcal"])
                            for naam_p, data_p in gesorteerd[:8]:
                                gem_gram = round(data_p["gram"] / max(len(dagen_met), 1))
                                st.markdown(
                                    f'<div style="background:#1e293b;border-radius:6px;padding:7px 10px;margin-bottom:4px;">' +
                                    f'<div style="display:flex;justify-content:space-between;">' +
                                    f'<span style="font-size:0.75rem;color:#f1f5f9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:65%;">{naam_p}</span>' +
                                    f'<span style="font-size:0.72rem;color:{kleur};font-weight:700;">GI {data_p["gi"]}</span>' +
                                    f'</div>' +
                                    f'<div style="font-size:0.68rem;color:#64748b;">{gem_gram}g/dag gem.</div>' +
                                    f'</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f'<div style="font-size:0.75rem;color:#475569;padding:8px;">Geen producten</div>',
                                unsafe_allow_html=True)
            else:
                st.info("Voeg GI-waarden toe aan je producten in de bibliotheek voor dit overzicht.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — EIWIT
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("<br>", unsafe_allow_html=True)
        if not dagen_met:
            st.info("Nog geen voedingsdata.")
        else:
            labels_d = [d["datum"][5:] for d in dagen_data]
            gem_ei  = round(sum(d["eiwit"] for d in dagen_met)/len(dagen_met),1)
            pct_ei  = round(gem_ei/max(ei_doel_g,1)*100)
            k_ei    = "#22c55e" if 85<=pct_ei<=115 else ("#fbbf24" if 70<=pct_ei<=130 else "#ef4444")
            gew_kg  = float(profiel.get("gewicht_kg",70) or 70)
            ei_per_kg = round(gem_ei/max(gew_kg,1),2)
            ei_per_kg_k = "#22c55e" if ei_per_kg>=1.4 else ("#fbbf24" if ei_per_kg>=1.2 else "#ef4444")

            m1,m2,m3,m4 = st.columns(4)
            for col,lbl,val,kl in [
                (m1,"GEM EIWIT/DAG",f"{gem_ei}g",k_ei),
                (m2,"DOEL",f"{ei_doel_g}g","#64748b"),
                (m3,"% VAN DOEL",f"{pct_ei}%",k_ei),
                (m4,"G/KG LICHAAMSGEWICHT",f"{ei_per_kg}g/kg",ei_per_kg_k)]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">{lbl}</div>'
                        f'<div style="font-size:0.9rem;font-weight:800;color:{kl};">{val}</div>'
                        f'</div>', unsafe_allow_html=True)

            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">Eiwitinname per dag vs doel</div>', unsafe_allow_html=True)
            ei_vals = [round(d["eiwit"],1) for d in dagen_data]
            _chart(_lijn_chart(labels_d,
                [{"label":"Eiwit (g)","data":ei_vals,"color":"#3b82f6","fill":True}],
                doel_lijn=ei_doel_g, y_label="gram"), height=260)

            # Eiwitverdeling over maaltijdmomenten
            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 4px;">Eiwitverdeling over maaltijdmomenten</div>', unsafe_allow_html=True)
            MOMENT_NAMEN = ["Ontbijt","Tussend. vm","Lunch","Tussend. nm","Avondmaal","Avondsnack"]
            MOMENT_TYPES = ["hoofd","tussen","hoofd","tussen","hoofd","tussen"]
            ei_per_mom = [0.0]*6
            for dd in dagen_met:
                for it in dd.get("items",[]):
                    mi = int(it.get("moment",0) or 0)
                    if 0<=mi<6:
                        ei_per_mom[mi] += float(it.get("eiwit_g",0) or 0)
            ei_gem_mom = [round(ei_per_mom[i]/max(len(dagen_met),1),1) for i in range(6)]
            # Doel per moment: hoofdmaaltijd = ei_doel_g/3, tussendoor = 12g
            ei_doel_mom = [ei_doel_g/3 if MOMENT_TYPES[i]=="hoofd" else 12.0 for i in range(6)]
            _chart(_bar_chart(MOMENT_NAMEN, [
                {"label":"Gem eiwit (g)","data":ei_gem_mom,"color":"#3b82f6"},
                {"label":"Aanbevolen (g)","data":[round(x,1) for x in ei_doel_mom],"color":"#f97316"},
            ], y_label="gram"), height=260)

            # Analyse spreiding hoofdmaaltijden
            hoofd_ei = [ei_gem_mom[i] for i in [0,2,4]]
            hoofd_ok = all(e>=20 for e in hoofd_ei if e>0)
            tussen_ei = [ei_gem_mom[i] for i in [1,3,5]]
            tussen_ok = all(e>=8 for e in tussen_ei if e>0)
            if hoofd_ok:
                adv_ei = "✓ Goede eiwitverdeling over hoofdmaaltijden (≥20g per maaltijd). Optimale MPS-stimulatie."
                adv_k = "#22c55e"
            else:
                lage = [MOMENT_NAMEN[i] for i in [0,2,4] if 0<ei_gem_mom[i]<20]
                adv_ei = f"⚠️ Te weinig eiwit bij: {', '.join(lage)}. Streef naar min. 20g per hoofdmaaltijd voor optimale spiereiwitsynthese."
                adv_k = "#fbbf24"
            st.markdown(f'<div style="background:#1e293b;border-radius:8px;padding:12px;margin-top:6px;font-size:0.82rem;color:{adv_k};">{adv_ei}</div>', unsafe_allow_html=True)

            # Plantaardig vs dierlijk
            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 6px;">Herkomst eiwit (plantaardig vs dierlijk)</div>', unsafe_allow_html=True)
            ei_pl=0; ei_di=0
            EIWIT_PCT = {"Vlees & vis":22,"Zuivel":8,"Eieren":13,"Granen & brood":10,
                         "Groenten":3,"Peulvruchten":9,"Noten & zaden":18,
                         "Fruit":1,"Sauzen & spreads":5,"Sportvoeding":20,"Overige":8}
            PLANTAARDIG = {"Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten","Sojaproducten"}
            DIERLIJK = {"Vlees & vis","Zuivel","Eieren"}
            for dd in dagen_met:
                for it in dd.get("items",[]):
                    # Haal categorie op: eerst uit item, dan uit bibliotheek
                    pid = it.get("product_id","") or ""
                    cat = _herken_categorie(
                        it.get("naam",""),
                        it.get("categorie") or bib_cat_lookup.get(pid,{}).get("categorie",""))

                    ei_g = float(it.get("eiwit_g",0) or 0)
                    if cat in PLANTAARDIG: ei_pl += ei_g
                    elif cat in DIERLIJK:  ei_di += ei_g
            ei_tot = ei_pl + ei_di
            if ei_tot > 0:
                pct_pl = round(ei_pl/ei_tot*100)
                pct_di = 100-pct_pl
                ep1, ep2 = st.columns([1,2])
                with ep1:
                    _chart(_donut_chart(
                        [f"Plantaardig {pct_pl}%",f"Dierlijk {pct_di}%"],
                        [pct_pl, pct_di], ["#22c55e","#3b82f6"]), height=300)
                with ep2:
                    kl_pl = "#22c55e" if 30<=pct_pl<=70 else "#3b82f6" if pct_di>70 else "#fbbf24"
                    # Bouw overzicht per categorie
                    cat_ei_detail = {}
                    for dd in dagen_met:
                        for it in dd.get("items",[]):
                            pid_d = it.get("product_id","") or ""
                            # Altijd herkenning op naam — ook als categorie al opgeslagen is
                            # want oude items kunnen verkeerde/lege categorie hebben
                            _cat_raw = (it.get("categorie") or 
                                       bib_cat_lookup.get(pid_d,{}).get("categorie","") or "")
                            # Forceer naam-herkenning als categorie Overige of leeg is
                            if not _cat_raw or _cat_raw == "Overige":
                                cat_d = _herken_categorie(it.get("naam",""), "")
                            else:
                                cat_d = _cat_raw
                            eg = float(it.get("eiwit_g",0) or 0)
                            if eg > 0:
                                cat_ei_detail[cat_d] = cat_ei_detail.get(cat_d,0) + eg
                    top_cats = sorted(cat_ei_detail.items(), key=lambda x:-x[1])[:6]
                    max_ei_cat = top_cats[0][1] if top_cats else 1
                    CAT_KL = {"Vlees & vis":"#ef4444","Zuivel":"#3b82f6","Eieren":"#fbbf24",
                              "Granen & brood":"#f97316","Groenten":"#22c55e","Peulvruchten":"#22c55e",
                              "Noten & zaden":"#f59e0b","Fruit":"#a78bfa","Sportvoeding":"#14b8a6","Overige":"#64748b"}
                    html_detail = (
                        f'<div style="background:#1e293b;border-radius:10px;padding:16px;height:300px;box-sizing:border-box;overflow-y:auto;">'
                        f'<div style="font-size:0.7rem;font-weight:700;color:#64748b;margin-bottom:10px;">EIWITBRONNEN (gem/dag)</div>'
                    )
                    for cat_n, ei_g in top_cats:
                        ei_gem_dag = round(ei_g/len(dagen_met),1)
                        pct_b = round(ei_g/max_ei_cat*100)
                        kl_c = CAT_KL.get(cat_n,"#64748b")
                        is_plant = cat_n in {"Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten","Sojaproducten"}
                        is_dier  = cat_n in {"Vlees & vis","Zuivel","Eieren"}
                        html_detail += (
                            f'<div style="margin-bottom:7px;">'
                            f'<div style="display:flex;justify-content:space-between;font-size:0.72rem;margin-bottom:3px;">'
                            f'<span style="color:#f1f5f9;">{cat_n}</span>'
                            f'<span style="color:{kl_c};font-weight:700;">{ei_gem_dag}g/dag</span>'
                            f'</div>'
                            f'<div style="background:#0f172a;border-radius:3px;height:5px;">'
                            f'<div style="width:{pct_b}%;height:100%;background:{kl_c};border-radius:3px;"></div>'
                            f'</div></div>'
                        )
                    html_detail += (
                        f'<div style="border-top:1px solid #334155;margin-top:10px;padding-top:10px;">'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
                        f'<span style="font-size:0.75rem;color:#22c55e;">Plantaardig</span>'
                        f'<span style="font-size:0.75rem;font-weight:700;color:#22c55e;">{pct_pl}%</span></div>'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
                        f'<span style="font-size:0.75rem;color:#3b82f6;">Dierlijk</span>'
                        f'<span style="font-size:0.75rem;font-weight:700;color:#3b82f6;">{pct_di}%</span></div>'
                        f'<div style="font-size:0.72rem;color:#64748b;">Gem eiwit: <b style="color:#3b82f6">{ei_per_kg}g/kg/dag</b> — '
                        f'{"✓ voldoende (doel ≥1.4g/kg)" if ei_per_kg>=1.4 else "⚠️ onder aanbeveling (doel 1.4–1.7g/kg)"}'
                        f'</div></div></div>'
                    )
                    st.markdown(html_detail, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — VETTEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown("<br>", unsafe_allow_html=True)
        if not dagen_met:
            st.info("Nog geen voedingsdata.")
        else:
            labels_d = [d["datum"][5:] for d in dagen_data]
            gem_vet = round(sum(d["vet"] for d in dagen_met)/len(dagen_met),1)
            pct_vet = round(gem_vet/max(vt_doel_g,1)*100)
            k_vet   = "#22c55e" if 85<=pct_vet<=115 else ("#fbbf24" if 70<=pct_vet<=130 else "#ef4444")
            # Vet als % van kcal
            gem_kcal_v = round(sum(d["kcal"] for d in dagen_met)/len(dagen_met))
            vet_pct_kcal = round(gem_vet*9/max(gem_kcal_v,1)*100)

            v1,v2,v3 = st.columns(3)
            for col,lbl,val,kl in [
                (v1,"GEM VET/DAG",f"{gem_vet}g",k_vet),
                (v2,"DOEL",f"{vt_doel_g}g","#64748b"),
                (v3,"% VAN KCAL",f"{vet_pct_kcal}%",k_vet)]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">{lbl}</div>'
                        f'<div style="font-size:1rem;font-weight:800;color:{kl};">{val}</div>'
                        f'</div>', unsafe_allow_html=True)

            st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">Vetinname per dag vs doel</div>', unsafe_allow_html=True)
            vet_vals = [round(d["vet"],1) for d in dagen_data]
            _chart(_lijn_chart(labels_d,
                [{"label":"Vet (g)","data":vet_vals,"color":"#8b5cf6","fill":True}],
                doel_lijn=vt_doel_g, y_label="gram"), height=260)

            # Verzadigde vs onverzadigde vetten
            @st.cache_data(ttl=300)
            def _laad_vet_bib(uid):
                try:
                    r1 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,verzadigd_100g").eq("user_id",uid).execute()
                    r2 = _get_supabase().table("fuelc_bibliotheek")\
                        .select("id,verzadigd_100g").is_("user_id","null").execute()
                    return {row["id"]: float(row.get("verzadigd_100g") or 0) for row in (r1.data or [])+(r2.data or [])}
                except: return {}

            verz_per_dag = []
            onverz_per_dag = []
            heeft_verz_data = False
            for dd in dagen_data:
                # Lees verz_g direct uit dagboek items — wordt opgeslagen bij invoer
                dag_verz = sum(float(it.get("verz_g", 0) or 0) for it in dd.get("items", []))
                dag_vet  = dd["vet"]
                if dag_verz > 0: heeft_verz_data = True
                verz_per_dag.append(round(dag_verz, 1))
                onverz_per_dag.append(round(max(0, dag_vet - dag_verz), 1))

            if heeft_verz_data:
                _chart(_bar_chart(labels_d, [
                    {"label":"Onverzadigd (g)","data":onverz_per_dag,"color":"#22c55e"},
                    {"label":"Verzadigd (g)","data":verz_per_dag,"color":"#ef4444"},
                ], y_label="gram"), height=260)

                gem_verz = round(sum(verz_per_dag)/max(len([x for x in verz_per_dag if x>0]),1),1)
                verz_pct_kcal = round(gem_verz*9/max(gem_kcal_v,1)*100)
                k_verz = "#22c55e" if verz_pct_kcal<=10 else "#ef4444"

                # Donut verz/onverz gemiddelde
                vd1, vd2 = st.columns([1,2])
                with vd1:
                    gem_onverz = round(gem_vet - gem_verz, 1)
                    _chart(_donut_chart(
                        [f"Onverzadigd {round(gem_onverz,1)}g",f"Verzadigd {gem_verz}g"],
                        [max(0,round(gem_onverz,1)), gem_verz],
                        ["#22c55e","#ef4444"]), height=260)
                with vd2:
                    # Energie doel inclusief gemiddelde training
                    _gem_train_kcal = round(sum(d.get("training_kcal",0) for d in dagen_data if d.get("training_kcal",0)>0) / max(len([d for d in dagen_data if d.get("training_kcal",0)>0]),1)) if any(d.get("training_kcal",0)>0 for d in dagen_data) else 0
                    energie_doel_incl = energie_doel + _gem_train_kcal
                    adv_verz = (f"✓ Verzadigde vetten ({verz_pct_kcal}% van kcal) binnen aanbeveling (max 10%)." if verz_pct_kcal<=10
                                else f"⚠️ Verzadigde vetten ({verz_pct_kcal}% van kcal) overschrijden de WHO-aanbeveling (max 10%). Vervang boter/room/vet vlees door olijfolie, noten en vis.")
                    k_adv_v = "#22c55e" if verz_pct_kcal<=10 else "#fbbf24"
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:10px;padding:16px;height:260px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;">'
                        f'<div style="font-size:0.7rem;font-weight:700;color:#64748b;margin-bottom:8px;">ANALYSE</div>'
                        f'<div style="font-size:0.85rem;color:{k_adv_v};line-height:1.6;margin-bottom:12px;">{adv_verz}</div>'
                        f'<div style="font-size:0.75rem;color:#64748b;line-height:1.7;">'
                        f'Gem verzadigd: <b style="color:#ef4444">{gem_verz}g/dag</b> = {verz_pct_kcal}% van kcal<br>'
                        f'WHO max: 10% = <b style="color:#94a3b8">{round(energie_doel_incl*0.10/9)}g/dag</b> bij {energie_doel_incl} kcal (basis {energie_doel} + gem. training {_gem_train_kcal})'
                        f'</div></div>', unsafe_allow_html=True)
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6 — PERFORMANCE
    # ══════════════════════════════════════════════════════════════════════════
    with tab6:
        st.markdown("<br>", unsafe_allow_html=True)
        if not dagen_met:
            st.info("Vul je dagschema in om je performance score te berekenen.")
        else:
            scores_per_dag = []
            for dd in dagen_data:
                if dd["kcal"] > 0:
                    w = welzijn_data.get(dd["datum"], {})
                    result = _bereken_performance_score(
                        dd, profiel, w, dd.get("items",[]),
                        training_kcal=dd.get("training_kcal",0),
                        is_trainingsdag=dd.get("is_trainingsdag",False))
                    scores_per_dag.append({
                        "datum": dd["datum"],
                        "score": result["score"],
                        "breakdown": result["breakdown"]})

            if scores_per_dag:
                gem_score = round(sum(s["score"] for s in scores_per_dag)/len(scores_per_dag))
                beste     = max(scores_per_dag, key=lambda s:s["score"])
                slechtste = min(scores_per_dag, key=lambda s:s["score"])
                n_goed    = sum(1 for s in scores_per_dag if s["score"]>=75)
                k_gem     = "#22c55e" if gem_score>=75 else ("#fbbf24" if gem_score>=50 else "#ef4444")

                p1,p2,p3,p4 = st.columns(4)
                for col,lbl,val,kl in [
                    (p1,"GEM SCORE",f"{gem_score}/100",k_gem),
                    (p2,"BESTE DAG",f"{beste['score']} ({beste['datum'][5:]})", "#22c55e"),
                    (p3,"SLECHTSTE",f"{slechtste['score']} ({slechtste['datum'][5:]})", "#ef4444"),
                    (p4,"GOEDE DAGEN",f"{n_goed}/{len(scores_per_dag)}","#22c55e")]:
                    with col:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;margin-bottom:12px;">'
                            f'<div style="font-size:0.6rem;color:#64748b;">{lbl}</div>'
                            f'<div style="font-size:0.9rem;font-weight:800;color:{kl};">{val}</div>'
                            f'</div>', unsafe_allow_html=True)

                st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">Performance score per dag</div>', unsafe_allow_html=True)
                perf_labels = [s["datum"][5:] for s in scores_per_dag]
                perf_vals   = [s["score"] for s in scores_per_dag]
                _chart(_lijn_chart(perf_labels,
                    [{"label":"Score","data":perf_vals,"color":"#22c55e","fill":True}],
                    doel_lijn=75, y_label="Score /100"), height=260)

                # Breakdown laatste dag
                bd = scores_per_dag[-1]
                st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin:16px 0 8px;">Breakdown laatste dag</div>', unsafe_allow_html=True)
                PIJLERS = {
                    "energiebalans":    ("⚡ Energiebalans",20),
                    "macrokwaliteit":   ("🥗 Macrokwaliteit",25),
                    "micronutriënten":  ("💊 Micronutriënten",20),
                    "maaltijdregelmaat":("📅 Maaltijdtiming",15),
                    "voedingskwaliteit":("🌿 Voedingskwaliteit",15),
                    "hydratatie":       ("💧 Hydratatie",5),
                }
                for k,(lbl,maxp) in PIJLERS.items():
                    pts = bd["breakdown"].get(k,{})
                    if isinstance(pts,dict): pts = pts.get("score",0)
                    pct_p = round(pts/maxp*100)
                    kl_p = "#22c55e" if pct_p>=80 else ("#fbbf24" if pct_p>=50 else "#ef4444")
                    detail = ""
                    if isinstance(bd["breakdown"].get(k),dict):
                        detail = bd["breakdown"][k].get("detail","")
                    detail_html = f'<div style="font-size:0.68rem;color:#64748b;margin-top:3px;">{detail}</div>' if detail else ""
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:8px;padding:10px 12px;margin-bottom:6px;">'
                        f'<div style="margin-bottom:5px;">'
                        f'<span style="font-size:0.82rem;color:#f8fafc;">{lbl}</span></div>'
                        f'<div style="background:#0f172a;border-radius:3px;height:5px;margin-bottom:4px;">'
                        f'<div style="width:{pct_p}%;height:100%;background:{kl_p};border-radius:3px;"></div></div>'
                        + detail_html + '</div>',
                        unsafe_allow_html=True)


def _stap_dashboard(user: dict):
    tab_db, tab_an = st.tabs(["📓 Dagboek", "📊 Analyses"])
    with tab_db:
        _render_voedingsdagboek(user)
    with tab_an:
        _render_analyses(user)


def render_fuelc(user: dict):
    """Publieke entry point voor de FuelC module."""
    if "fc_stap" not in st.session_state:
        st.session_state.fc_stap = 0

    stap = st.session_state.fc_stap

    # ── Terug knop + Navigatiebalk ───────────────────────────────────────────
    top1, top2 = st.columns([1, 4])
    with top1:
        if st.button("← Modules", key="fc_terug_modules", use_container_width=True):
            st.session_state.module = "menu"
            st.rerun()

    NAV = [
        (0, "👤 Profiel"),
        (1, "🏃 Trainingen"),
        (2, "📚 Bibliotheek"),
        (3, "📅 Dagschema"),
        (4, "📊 Analyses"),
    ]
    cols = st.columns(len(NAV))
    for col, (s, label) in zip(cols, NAV):
        with col:
            actief = stap == s
            if st.button(
                label,
                key=f"fc_nav_{s}",
                use_container_width=True,
                type="primary" if actief else "secondary",
            ):
                st.session_state.fc_stap = s
                st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Module routing ────────────────────────────────────────────────────────
    if stap == 0: _stap_profiel(user)
    elif stap == 1: _stap_trainingen(user)
    elif stap == 2: _stap_bibliotheek(user)
    elif stap == 3: _stap_dagschema(user)
    elif stap == 4: _render_analyses(user)
