import streamlit as st
import math
from datetime import datetime, timedelta

# ─── MASCOT AVATAR ────────────────────────────────────────────────────────────
from carboo_assets import MASCOT_B64


# ─── COACH STAPPEN ────────────────────────────────────────────────────────────
STAPPEN = [
    "welkom",
    "atleet_profiel",
    "wedstrijd_info",
    "carboloading",
    "racedag_voeding",
    "raceplan",
    "samenvatting",
]

SPORT_ICONS = {
    "Fietsen":      "🚴",
    "Lopen":        "🏃",
    "Duatlon":      "🏃🚴",
    "Crossduatlon": "🚵🏃",
    "Triatlon":     "🏊🚴🏃",
    "Crosstriatlon":"🚵🏊",
}

KH_TARGETS = {
    "Fietsen":      {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":        {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":      {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":     {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon":{(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}


def _get_kh_range(sport, minuten):
    ranges = KH_TARGETS.get(sport, KH_TARGETS["Fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= minuten < hi:
            return mn, mx
    return 60, 90


def _progress_bar(stap_idx: int):
    total = len(STAPPEN) - 1
    pct = int((stap_idx / total) * 100)
    labels = ["👋 Welkom", "🏃 Profiel", "🏁 Wedstrijd", "🍝 Carboloading", "🥗 Racedag", "📋 Raceplan", "✅ Samenvatting"]
    
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#94a3b8; font-size:0.72rem; font-weight:700; letter-spacing:1px;">STAP {stap_idx + 1} VAN {total + 1}</span>
            <span style="color:#f97316; font-size:0.72rem; font-weight:700;">{pct}% VOLTOOID</span>
        </div>
        <div style="background:#1e293b; border-radius:8px; height:8px; overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:linear-gradient(90deg,#f97316,#fb923c); border-radius:8px; transition:width 0.3s;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:8px; flex-wrap:wrap; gap:4px;">
            {"".join(f'<span style="font-size:0.62rem; color:{"#f97316" if i == stap_idx else "#334155" if i > stap_idx else "#22c55e"}; font-weight:700;">{lbl}</span>' for i, lbl in enumerate(labels))}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _coach_bubble(tekst: str, icon: str = "🤖"):
    html = (
        '<div style="display:flex;gap:14px;margin-bottom:20px;align-items:flex-end;">' +
        '<div style="flex-shrink:0;width:70px;height:70px;display:flex;align-items:flex-end;justify-content:center;">' +
        '<img src="' + MASCOT_B64 + '" style="height:70px;width:auto;object-fit:contain;filter:drop-shadow(0 2px 8px rgba(249,115,22,0.5));" alt="Carboo">' +
        '</div>' +
        '<div style="background:#1e293b;border:1px solid #334155;border-radius:0 14px 14px 14px;padding:14px 18px;color:#f8fafc;font-size:0.9rem;line-height:1.6;max-width:680px;">' +
        tekst +
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _info_card(titel: str, waarde: str, kleur: str = "#f97316", icon: str = ""):
    st.markdown(f"""
    <div style="background:#1e293b; border-left:4px solid {kleur}; border-radius:10px; 
         padding:14px 16px; margin-bottom:10px;">
        <div style="font-size:0.68rem; color:#64748b; font-weight:700; letter-spacing:1px; margin-bottom:2px;">{icon} {titel.upper()}</div>
        <div style="font-size:1.05rem; font-weight:800; color:#f8fafc;">{waarde}</div>
    </div>
    """, unsafe_allow_html=True)


def _stap_welkom(naam: str):
    _coach_bubble(f"""
    Hoi <b>{naam}</b>! 👋 Ik ben <b>Carboo</b>, jouw persoonlijke race nutrition coach.<br><br>
    Ik ga je stap voor stap begeleiden om jouw voeding optimaal af te stemmen op je komende wedstrijd. 
    We bouwen samen een <b>volledig voedingsplan</b> op dat bestaat uit:<br><br>
    🍝 <b>Carbohydrate loading</b> — de 2 dagen vóór de race<br>
    🏁 <b>Racedag voeding</b> — ontbijt en pre-race strategie<br>
    ⏱️ <b>Slim raceplan</b> — uur per uur wat je eet en drinkt<br><br>
    Dit duurt slechts <b>5-7 minuten</b>. Ben je er klaar voor?
    """, "🤖")

    st.markdown("""
    <div style="font-size:0.72rem;color:#64748b;text-align:center;margin-top:4px;
                padding:8px 16px;border-top:1px solid #1e293b;">
        Carboo is een hulpmiddel voor recreatieve en competitieve sporters. 
        Bij medische aandoeningen, klinische voedingsproblemen, eetstoornissen 
        of specifieke gezondheidsvragen raadpleeg je best een erkend diëtist of arts.
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀  JA, LET'S GO!", key="welkom_ja", use_container_width=True):
        st.session_state.coach_stap = 1
        st.rerun()


def _stap_profiel(naam: str):
    _coach_bubble(f"""
    Laten we starten met jouw <b>profiel als atleet</b>. Dit helpt me om je koolhydraatbehoeften 
    nauwkeurig te berekenen. Vul de gegevens zo nauwkeurig mogelijk in.
    """)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            atleet_naam = st.text_input("👤 Naam atleet",
                value=st.session_state.get("coach_data", {}).get("atleet_naam", ""),
                key="p_atleet_naam", placeholder="Voornaam en naam atleet")
        with col2:
            wedstrijd_naam = st.text_input("🏆 Naam wedstrijd",
                value=st.session_state.get("coach_data", {}).get("wedstrijd_naam", ""),
                key="p_wedstrijd_naam", placeholder="bv. Ironman Frankfurt")

        col3, col4 = st.columns(2)
        with col3:
            gewicht = st.number_input("⚖️ Lichaamsgewicht (kg)", 30.0, 150.0,
                st.session_state.get("coach_data", {}).get("gewicht", 70.0), 0.5, key="p_gewicht")
        with col4:
            sport_list = list(SPORT_ICONS.keys())
            sport_default = st.session_state.get("coach_data", {}).get("sport", "Fietsen")
            sport_idx = sport_list.index(sport_default) if sport_default in sport_list else 0
            sport = st.selectbox("🏅 Discipline",
                [f"{SPORT_ICONS[s]} {s}" for s in sport_list],
                index=sport_idx, key="p_sport")
            sport_clean = sport.split(" ", 1)[1] if " " in sport else sport

        niveau_list = ["Recreatief", "Competitief", "Elite / Semi-pro"]
        niveau_default = st.session_state.get("coach_data", {}).get("niveau", "Recreatief")
        niveau_idx = niveau_list.index(niveau_default) if niveau_default in niveau_list else 0
        nc1, nc2 = st.columns([11, 1])
        with nc1:
            niveau = st.selectbox("📊 Sportniveau", niveau_list, index=niveau_idx, key="p_niveau")
        with nc2:
            st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
            with st.popover("ℹ️"):
                st.markdown("""
**Sportniveau — legende**

🟢 **Recreatief**
Meedoen is belangrijker dan winnen. Je sport voor plezier en gezondheid.

🟡 **Competitief**
Je hebt een (tijds)doel. Je traint gericht.

🔴 **Elite / Semi-pro**
Je verdient (geld)prijzen met je sport. Prestatie staat centraal.
""")

        erv_list = ["Eerste wedstrijd", "1-3 wedstrijden", "4-10 wedstrijden", "10+ wedstrijden"]
        erv_default = st.session_state.get("coach_data", {}).get("ervaring", "Eerste wedstrijd")
        erv_idx = erv_list.index(erv_default) if erv_default in erv_list else 0
        ervaring = st.selectbox("🎯 Ervaring met wedstrijdvoeding", erv_list, index=erv_idx, key="p_erv")

    # ── Logo upload ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#64748b;'
        'letter-spacing:2px;margin:18px 0 6px;">🖼️ LOGO OP RAPPORT (optioneel)</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.78rem;color:#64748b;margin-bottom:8px;">'
        'Upload je club- of teamlogo. Dit verschijnt professioneel op de PDF rapporten.</div>',
        unsafe_allow_html=True)

    logo_col1, logo_col2 = st.columns([2,1])
    with logo_col1:
        logo_file = st.file_uploader(
            "Logo uploaden (PNG of JPG, max 2MB)",
            type=["png","jpg","jpeg"],
            key="p_logo_upload",
            label_visibility="collapsed")

        if logo_file:
            import base64
            logo_bytes = logo_file.read()
            logo_b64 = base64.b64encode(logo_bytes).decode()
            logo_mime = "image/png" if logo_file.name.lower().endswith(".png") else "image/jpeg"
            st.session_state["coach_logo_b64"] = logo_b64
            st.session_state["coach_logo_mime"] = logo_mime
            st.success("✅ Logo opgeladen!")

    with logo_col2:
        if st.session_state.get("coach_logo_b64"):
            logo_b64_prev = st.session_state["coach_logo_b64"]
            logo_mime_prev = st.session_state.get("coach_logo_mime","image/png")
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;' +
                f'padding:8px;text-align:center;">' +
                f'<img src="data:{logo_mime_prev};base64,{logo_b64_prev}" ' +
                f'style="max-height:60px;max-width:100%;object-fit:contain;">' +
                f'<div style="font-size:10px;color:#64748b;margin-top:4px;">Voorbeeld</div></div>',
                unsafe_allow_html=True)
            if st.button("🗑 Logo verwijderen", key="p_logo_del"):
                del st.session_state["coach_logo_b64"]
                del st.session_state["coach_logo_mime"]
                st.rerun()
        else:
            st.markdown(
                '<div style="background:#0f172a;border:1px dashed #334155;border-radius:8px;' +
                'padding:16px;text-align:center;color:#64748b;font-size:0.75rem;">Nog geen logo</div>',
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="prof_prev"):
            st.session_state.coach_stap = 0
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="prof_next", use_container_width=True):
            if "coach_data" not in st.session_state:
                st.session_state.coach_data = {}
            st.session_state.coach_data.update({
                "atleet_naam":    atleet_naam,
                "wedstrijd_naam": wedstrijd_naam,
                "gewicht":        gewicht,
                "sport":          sport_clean,
                "niveau":         niveau,
                "ervaring":       ervaring,
            })
            st.session_state.coach_stap = 2
            st.rerun()


def _stap_wedstrijd():
    data = st.session_state.get("coach_data", {})
    _coach_bubble(f"""
    Nu de <b>wedstrijddetails</b>. Op basis van de duur en het type wedstrijd bereken ik hoeveel 
    koolhydraten je nodig hebt en stel ik een tijdlijn op.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        wedstrijd_datum = st.date_input("📅 Wedstrijddatum",
            value=datetime.now().date() + timedelta(days=14), key="w_datum")
    _tijden_start = ['04:00', '04:15', '04:30', '04:45', '05:00', '05:15', '05:30', '05:45', '06:00', '06:15', '06:30', '06:45', '07:00', '07:15', '07:30', '07:45', '08:00', '08:15', '08:30', '08:45', '09:00', '09:15', '09:30', '09:45', '10:00', '10:15', '10:30', '10:45', '11:00', '11:15', '11:30', '11:45', '12:00', '12:15', '12:30', '12:45', '13:00', '13:15', '13:30', '13:45', '14:00', '14:15', '14:30', '14:45', '15:00', '15:15', '15:30', '15:45', '16:00', '16:15', '16:30', '16:45', '17:00', '17:15', '17:30', '17:45', '18:00', '18:15', '18:30', '18:45', '19:00', '19:15', '19:30', '19:45', '20:00', '20:15', '20:30', '20:45', '21:00', '21:15', '21:30', '21:45', '22:00', '22:15', '22:30', '22:45', '23:00', '23:15', '23:30', '23:45']
    _tijden_eind  = ['04:00', '04:01', '04:02', '04:03', '04:04', '04:05', '04:06', '04:07', '04:08', '04:09', '04:10', '04:11', '04:12', '04:13', '04:14', '04:15', '04:16', '04:17', '04:18', '04:19', '04:20', '04:21', '04:22', '04:23', '04:24', '04:25', '04:26', '04:27', '04:28', '04:29', '04:30', '04:31', '04:32', '04:33', '04:34', '04:35', '04:36', '04:37', '04:38', '04:39', '04:40', '04:41', '04:42', '04:43', '04:44', '04:45', '04:46', '04:47', '04:48', '04:49', '04:50', '04:51', '04:52', '04:53', '04:54', '04:55', '04:56', '04:57', '04:58', '04:59', '05:00', '05:01', '05:02', '05:03', '05:04', '05:05', '05:06', '05:07', '05:08', '05:09', '05:10', '05:11', '05:12', '05:13', '05:14', '05:15', '05:16', '05:17', '05:18', '05:19', '05:20', '05:21', '05:22', '05:23', '05:24', '05:25', '05:26', '05:27', '05:28', '05:29', '05:30', '05:31', '05:32', '05:33', '05:34', '05:35', '05:36', '05:37', '05:38', '05:39', '05:40', '05:41', '05:42', '05:43', '05:44', '05:45', '05:46', '05:47', '05:48', '05:49', '05:50', '05:51', '05:52', '05:53', '05:54', '05:55', '05:56', '05:57', '05:58', '05:59', '06:00', '06:01', '06:02', '06:03', '06:04', '06:05', '06:06', '06:07', '06:08', '06:09', '06:10', '06:11', '06:12', '06:13', '06:14', '06:15', '06:16', '06:17', '06:18', '06:19', '06:20', '06:21', '06:22', '06:23', '06:24', '06:25', '06:26', '06:27', '06:28', '06:29', '06:30', '06:31', '06:32', '06:33', '06:34', '06:35', '06:36', '06:37', '06:38', '06:39', '06:40', '06:41', '06:42', '06:43', '06:44', '06:45', '06:46', '06:47', '06:48', '06:49', '06:50', '06:51', '06:52', '06:53', '06:54', '06:55', '06:56', '06:57', '06:58', '06:59', '07:00', '07:01', '07:02', '07:03', '07:04', '07:05', '07:06', '07:07', '07:08', '07:09', '07:10', '07:11', '07:12', '07:13', '07:14', '07:15', '07:16', '07:17', '07:18', '07:19', '07:20', '07:21', '07:22', '07:23', '07:24', '07:25', '07:26', '07:27', '07:28', '07:29', '07:30', '07:31', '07:32', '07:33', '07:34', '07:35', '07:36', '07:37', '07:38', '07:39', '07:40', '07:41', '07:42', '07:43', '07:44', '07:45', '07:46', '07:47', '07:48', '07:49', '07:50', '07:51', '07:52', '07:53', '07:54', '07:55', '07:56', '07:57', '07:58', '07:59', '08:00', '08:01', '08:02', '08:03', '08:04', '08:05', '08:06', '08:07', '08:08', '08:09', '08:10', '08:11', '08:12', '08:13', '08:14', '08:15', '08:16', '08:17', '08:18', '08:19', '08:20', '08:21', '08:22', '08:23', '08:24', '08:25', '08:26', '08:27', '08:28', '08:29', '08:30', '08:31', '08:32', '08:33', '08:34', '08:35', '08:36', '08:37', '08:38', '08:39', '08:40', '08:41', '08:42', '08:43', '08:44', '08:45', '08:46', '08:47', '08:48', '08:49', '08:50', '08:51', '08:52', '08:53', '08:54', '08:55', '08:56', '08:57', '08:58', '08:59', '09:00', '09:01', '09:02', '09:03', '09:04', '09:05', '09:06', '09:07', '09:08', '09:09', '09:10', '09:11', '09:12', '09:13', '09:14', '09:15', '09:16', '09:17', '09:18', '09:19', '09:20', '09:21', '09:22', '09:23', '09:24', '09:25', '09:26', '09:27', '09:28', '09:29', '09:30', '09:31', '09:32', '09:33', '09:34', '09:35', '09:36', '09:37', '09:38', '09:39', '09:40', '09:41', '09:42', '09:43', '09:44', '09:45', '09:46', '09:47', '09:48', '09:49', '09:50', '09:51', '09:52', '09:53', '09:54', '09:55', '09:56', '09:57', '09:58', '09:59', '10:00', '10:01', '10:02', '10:03', '10:04', '10:05', '10:06', '10:07', '10:08', '10:09', '10:10', '10:11', '10:12', '10:13', '10:14', '10:15', '10:16', '10:17', '10:18', '10:19', '10:20', '10:21', '10:22', '10:23', '10:24', '10:25', '10:26', '10:27', '10:28', '10:29', '10:30', '10:31', '10:32', '10:33', '10:34', '10:35', '10:36', '10:37', '10:38', '10:39', '10:40', '10:41', '10:42', '10:43', '10:44', '10:45', '10:46', '10:47', '10:48', '10:49', '10:50', '10:51', '10:52', '10:53', '10:54', '10:55', '10:56', '10:57', '10:58', '10:59', '11:00', '11:01', '11:02', '11:03', '11:04', '11:05', '11:06', '11:07', '11:08', '11:09', '11:10', '11:11', '11:12', '11:13', '11:14', '11:15', '11:16', '11:17', '11:18', '11:19', '11:20', '11:21', '11:22', '11:23', '11:24', '11:25', '11:26', '11:27', '11:28', '11:29', '11:30', '11:31', '11:32', '11:33', '11:34', '11:35', '11:36', '11:37', '11:38', '11:39', '11:40', '11:41', '11:42', '11:43', '11:44', '11:45', '11:46', '11:47', '11:48', '11:49', '11:50', '11:51', '11:52', '11:53', '11:54', '11:55', '11:56', '11:57', '11:58', '11:59', '12:00', '12:01', '12:02', '12:03', '12:04', '12:05', '12:06', '12:07', '12:08', '12:09', '12:10', '12:11', '12:12', '12:13', '12:14', '12:15', '12:16', '12:17', '12:18', '12:19', '12:20', '12:21', '12:22', '12:23', '12:24', '12:25', '12:26', '12:27', '12:28', '12:29', '12:30', '12:31', '12:32', '12:33', '12:34', '12:35', '12:36', '12:37', '12:38', '12:39', '12:40', '12:41', '12:42', '12:43', '12:44', '12:45', '12:46', '12:47', '12:48', '12:49', '12:50', '12:51', '12:52', '12:53', '12:54', '12:55', '12:56', '12:57', '12:58', '12:59', '13:00', '13:01', '13:02', '13:03', '13:04', '13:05', '13:06', '13:07', '13:08', '13:09', '13:10', '13:11', '13:12', '13:13', '13:14', '13:15', '13:16', '13:17', '13:18', '13:19', '13:20', '13:21', '13:22', '13:23', '13:24', '13:25', '13:26', '13:27', '13:28', '13:29', '13:30', '13:31', '13:32', '13:33', '13:34', '13:35', '13:36', '13:37', '13:38', '13:39', '13:40', '13:41', '13:42', '13:43', '13:44', '13:45', '13:46', '13:47', '13:48', '13:49', '13:50', '13:51', '13:52', '13:53', '13:54', '13:55', '13:56', '13:57', '13:58', '13:59', '14:00', '14:01', '14:02', '14:03', '14:04', '14:05', '14:06', '14:07', '14:08', '14:09', '14:10', '14:11', '14:12', '14:13', '14:14', '14:15', '14:16', '14:17', '14:18', '14:19', '14:20', '14:21', '14:22', '14:23', '14:24', '14:25', '14:26', '14:27', '14:28', '14:29', '14:30', '14:31', '14:32', '14:33', '14:34', '14:35', '14:36', '14:37', '14:38', '14:39', '14:40', '14:41', '14:42', '14:43', '14:44', '14:45', '14:46', '14:47', '14:48', '14:49', '14:50', '14:51', '14:52', '14:53', '14:54', '14:55', '14:56', '14:57', '14:58', '14:59', '15:00', '15:01', '15:02', '15:03', '15:04', '15:05', '15:06', '15:07', '15:08', '15:09', '15:10', '15:11', '15:12', '15:13', '15:14', '15:15', '15:16', '15:17', '15:18', '15:19', '15:20', '15:21', '15:22', '15:23', '15:24', '15:25', '15:26', '15:27', '15:28', '15:29', '15:30', '15:31', '15:32', '15:33', '15:34', '15:35', '15:36', '15:37', '15:38', '15:39', '15:40', '15:41', '15:42', '15:43', '15:44', '15:45', '15:46', '15:47', '15:48', '15:49', '15:50', '15:51', '15:52', '15:53', '15:54', '15:55', '15:56', '15:57', '15:58', '15:59', '16:00', '16:01', '16:02', '16:03', '16:04', '16:05', '16:06', '16:07', '16:08', '16:09', '16:10', '16:11', '16:12', '16:13', '16:14', '16:15', '16:16', '16:17', '16:18', '16:19', '16:20', '16:21', '16:22', '16:23', '16:24', '16:25', '16:26', '16:27', '16:28', '16:29', '16:30', '16:31', '16:32', '16:33', '16:34', '16:35', '16:36', '16:37', '16:38', '16:39', '16:40', '16:41', '16:42', '16:43', '16:44', '16:45', '16:46', '16:47', '16:48', '16:49', '16:50', '16:51', '16:52', '16:53', '16:54', '16:55', '16:56', '16:57', '16:58', '16:59', '17:00', '17:01', '17:02', '17:03', '17:04', '17:05', '17:06', '17:07', '17:08', '17:09', '17:10', '17:11', '17:12', '17:13', '17:14', '17:15', '17:16', '17:17', '17:18', '17:19', '17:20', '17:21', '17:22', '17:23', '17:24', '17:25', '17:26', '17:27', '17:28', '17:29', '17:30', '17:31', '17:32', '17:33', '17:34', '17:35', '17:36', '17:37', '17:38', '17:39', '17:40', '17:41', '17:42', '17:43', '17:44', '17:45', '17:46', '17:47', '17:48', '17:49', '17:50', '17:51', '17:52', '17:53', '17:54', '17:55', '17:56', '17:57', '17:58', '17:59', '18:00', '18:01', '18:02', '18:03', '18:04', '18:05', '18:06', '18:07', '18:08', '18:09', '18:10', '18:11', '18:12', '18:13', '18:14', '18:15', '18:16', '18:17', '18:18', '18:19', '18:20', '18:21', '18:22', '18:23', '18:24', '18:25', '18:26', '18:27', '18:28', '18:29', '18:30', '18:31', '18:32', '18:33', '18:34', '18:35', '18:36', '18:37', '18:38', '18:39', '18:40', '18:41', '18:42', '18:43', '18:44', '18:45', '18:46', '18:47', '18:48', '18:49', '18:50', '18:51', '18:52', '18:53', '18:54', '18:55', '18:56', '18:57', '18:58', '18:59', '19:00', '19:01', '19:02', '19:03', '19:04', '19:05', '19:06', '19:07', '19:08', '19:09', '19:10', '19:11', '19:12', '19:13', '19:14', '19:15', '19:16', '19:17', '19:18', '19:19', '19:20', '19:21', '19:22', '19:23', '19:24', '19:25', '19:26', '19:27', '19:28', '19:29', '19:30', '19:31', '19:32', '19:33', '19:34', '19:35', '19:36', '19:37', '19:38', '19:39', '19:40', '19:41', '19:42', '19:43', '19:44', '19:45', '19:46', '19:47', '19:48', '19:49', '19:50', '19:51', '19:52', '19:53', '19:54', '19:55', '19:56', '19:57', '19:58', '19:59', '20:00', '20:01', '20:02', '20:03', '20:04', '20:05', '20:06', '20:07', '20:08', '20:09', '20:10', '20:11', '20:12', '20:13', '20:14', '20:15', '20:16', '20:17', '20:18', '20:19', '20:20', '20:21', '20:22', '20:23', '20:24', '20:25', '20:26', '20:27', '20:28', '20:29', '20:30', '20:31', '20:32', '20:33', '20:34', '20:35', '20:36', '20:37', '20:38', '20:39', '20:40', '20:41', '20:42', '20:43', '20:44', '20:45', '20:46', '20:47', '20:48', '20:49', '20:50', '20:51', '20:52', '20:53', '20:54', '20:55', '20:56', '20:57', '20:58', '20:59', '21:00', '21:01', '21:02', '21:03', '21:04', '21:05', '21:06', '21:07', '21:08', '21:09', '21:10', '21:11', '21:12', '21:13', '21:14', '21:15', '21:16', '21:17', '21:18', '21:19', '21:20', '21:21', '21:22', '21:23', '21:24', '21:25', '21:26', '21:27', '21:28', '21:29', '21:30', '21:31', '21:32', '21:33', '21:34', '21:35', '21:36', '21:37', '21:38', '21:39', '21:40', '21:41', '21:42', '21:43', '21:44', '21:45', '21:46', '21:47', '21:48', '21:49', '21:50', '21:51', '21:52', '21:53', '21:54', '21:55', '21:56', '21:57', '21:58', '21:59', '22:00', '22:01', '22:02', '22:03', '22:04', '22:05', '22:06', '22:07', '22:08', '22:09', '22:10', '22:11', '22:12', '22:13', '22:14', '22:15', '22:16', '22:17', '22:18', '22:19', '22:20', '22:21', '22:22', '22:23', '22:24', '22:25', '22:26', '22:27', '22:28', '22:29', '22:30', '22:31', '22:32', '22:33', '22:34', '22:35', '22:36', '22:37', '22:38', '22:39', '22:40', '22:41', '22:42', '22:43', '22:44', '22:45', '22:46', '22:47', '22:48', '22:49', '22:50', '22:51', '22:52', '22:53', '22:54', '22:55', '22:56', '22:57', '22:58', '22:59', '23:00', '23:01', '23:02', '23:03', '23:04', '23:05', '23:06', '23:07', '23:08', '23:09', '23:10', '23:11', '23:12', '23:13', '23:14', '23:15', '23:16', '23:17', '23:18', '23:19', '23:20', '23:21', '23:22', '23:23', '23:24', '23:25', '23:26', '23:27', '23:28', '23:29', '23:30', '23:31', '23:32', '23:33', '23:34', '23:35', '23:36', '23:37', '23:38', '23:39', '23:40', '23:41', '23:42', '23:43', '23:44', '23:45', '23:46', '23:47', '23:48', '23:49', '23:50', '23:51', '23:52', '23:53', '23:54', '23:55', '23:56', '23:57', '23:58', '23:59']
    with col2:
        _start_def = data.get("start_time", "09:00")
        _start_idx = _tijden_start.index(_start_def) if _start_def in _tijden_start else 20
        _start_str = st.selectbox("Starttijd", _tijden_start, index=_start_idx, key="w_start")
        start_time = datetime.strptime(_start_str, "%H:%M").time()
    with col3:
        _eind_def = data.get("eind_time", "12:00")
        _eind_idx = _tijden_eind.index(_eind_def) if _eind_def in _tijden_eind else 96
        _eind_str = st.selectbox("🏁 Geschatte eindtijd", _tijden_eind, index=_eind_idx, key="w_eind")
        eind_time = datetime.strptime(_eind_str, "%H:%M").time()

    col4, col5 = st.columns(2)
    with col4:
        temp = st.number_input("🌡️ Verwachte temperatuur (°C)", -10, 50,
            int(data.get("temp", 18) or 18), key="w_temp")
    with col5:
        vochtigheid = st.number_input("💧 Vochtigheid (%)", 0, 100,
            int(data.get("vochtigheid", 50) or 50), key="w_vocht")

    hoogte = st.number_input("⛰️ Hoogte boven zeeniveau (m)", 0, 5000,
        int(data.get("hoogte", 0) or 0), key="w_hoogte")

    start_dt = datetime.combine(datetime.today(), start_time)
    eind_dt = datetime.combine(datetime.today(), eind_time)
    if eind_dt <= start_dt:
        eind_dt += timedelta(days=1)
    totale_min = int((eind_dt - start_dt).total_seconds() / 60)
    sport = data.get("sport", "Fietsen")
    min_kh, max_kh = _get_kh_range(sport, totale_min)

    st.markdown(f"""
    <div style="background:rgba(59,130,246,0.1); border:1px solid #3b82f6; padding:14px; 
         border-radius:10px; margin:16px 0; text-align:center; color:#93c5fd; font-weight:700;">
        ⏱️ Duur: {totale_min // 60}u{int(totale_min or 0) % 60:02d}m &nbsp;|&nbsp;
        📊 {math.ceil(int(totale_min or 0) / 60)} uur te plannen
    </div>
    """, unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="wed_prev"):
            st.session_state.coach_stap = 1
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="wed_next", use_container_width=True):
            st.session_state.coach_data.update({
                "wedstrijd_datum": str(wedstrijd_datum),
                "start_time": start_time.strftime("%H:%M"),
                "eind_time": eind_time.strftime("%H:%M"),
                "totale_min": totale_min,
                "temp": temp,
                "vochtigheid": vochtigheid,
                "hoogte": hoogte,
                "min_kh": min_kh,
                "max_kh": max_kh,
            })
            st.session_state.coach_stap = 3
            st.rerun()


def _stap_carboloading():
    data       = st.session_state.get("coach_data", {})
    gewicht    = int(data.get("gewicht", 70) or 70)
    totale_min = int(data.get("totale_min", 180) or 180)

    # Herstel groene status bij terugkeren
    for k, v in data.get("cl_status", {}).items():
        if k not in st.session_state:
            st.session_state[k] = v

    if totale_min > 300:   factor = 12
    elif totale_min > 180: factor = 10
    elif totale_min > 90:  factor = 8
    else:                  factor = 6

    dag_target = round(gewicht * factor)

    _coach_bubble(f"""
    Vul per maaltijd in wat je plant te eten. Ik bereken automatisch of je je doel haalt.<br><br>
    Wanneer het balkje onderaan groen kleurt, bevestig je met <b>Dagdeel opslaan</b>. Er zal een groen bolletje verschijnen. Eigen producten kunnen onderaan worden toegevoegd.
    """)

    st.markdown("""
    <style>
    div[data-testid="stNumberInput"] input { background-color:#1e293b !important; color:#f8fafc !important; border:1px solid #334155 !important; }
    div[data-testid="stNumberInput"] button { background-color:#334155 !important; color:#f8fafc !important; border:none !important; }
    div[data-testid="stTextInput"] input { background-color:#1e293b !important; color:#f8fafc !important; border:1px solid #334155 !important; }
    /* Expander header: lichtgrijze achtergrond + donkere tekst — altijd leesbaar */
    div[data-testid="stExpander"] > details > summary {
        background-color: #1e293b !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        color: #f1f5f9 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary p {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover p {
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary svg {
        fill: #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    MOMENT_FOODS = {
        "Ontbijt": [
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",          "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",          "kh_portie": 14},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Ontbijtgranen",       "portie": "1 kom (30g)",            "kh_portie": 25},
            {"naam": "Muesli",              "portie": "1 kom (40g)",            "kh_portie": 30},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Melk (dierlijk)",     "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Plantaardige melk",   "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Peer",                "portie": "1 stuk middel (135g)",   "kh_portie": 19},
            {"naam": "Kiwi",                "portie": "1 stuk middel (75g)",    "kh_portie": 11},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",   "kh_portie": 4},
            {"naam": "Chocopasta",          "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Koffie met suiker",   "portie": "1 tas + 1 klontje",      "kh_portie": 5},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
        ],
        "Tussendoor VM": [
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Peer",                "portie": "1 stuk middel (135g)",   "kh_portie": 19},
            {"naam": "Dadels gedroogd",     "portie": "1 stuk (9g netto)",      "kh_portie": 6},
            {"naam": "Rozijnen",            "portie": "1 handje (20g)",         "kh_portie": 15},
            {"naam": "Muesli/granenreep",   "portie": "1 reep (40g)",           "kh_portie": 26},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Speculoos",           "portie": "1 stuk (7g)",            "kh_portie": 5},
            {"naam": "Snoep/winegums",      "portie": "1 zakje (30g)",          "kh_portie": 26},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
            {"naam": "Pannenkoek",          "portie": "1 stuk (60g)",           "kh_portie": 27},
        ],
        "Lunch": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar","kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",   "kh_portie": 30},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",         "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",         "kh_portie": 8},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",         "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",         "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",         "kh_portie": 14},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",  "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",  "kh_portie": 15},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",        "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",       "kh_portie": 35},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",  "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",  "kh_portie": 4},
            {"naam": "Chocopasta",          "portie": "1 koffielepel (4.5g)",  "kh_portie": 3},
        ],
        "Tussendoor NM": [
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Peer",                "portie": "1 stuk middel (135g)",   "kh_portie": 19},
            {"naam": "Dadels gedroogd",     "portie": "1 stuk (9g netto)",      "kh_portie": 6},
            {"naam": "Rozijnen",            "portie": "1 handje (20g)",         "kh_portie": 15},
            {"naam": "Muesli/granenreep",   "portie": "1 reep (40g)",           "kh_portie": 26},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Speculoos",           "portie": "1 stuk (7g)",            "kh_portie": 5},
            {"naam": "Snoep/winegums",      "portie": "1 zakje (30g)",          "kh_portie": 26},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
            {"naam": "Pannenkoek",          "portie": "1 stuk (60g)",           "kh_portie": 27},
        ],
        "Avondmaal": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar","kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",   "kh_portie": 30},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",         "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",         "kh_portie": 8},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",         "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",         "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",         "kh_portie": 14},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",  "kh_portie": 30},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",        "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",       "kh_portie": 35},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",    "kh_portie": 27},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",  "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",  "kh_portie": 4},
        ],
        "Avond snack": [
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Dadels gedroogd",     "portie": "1 stuk (9g netto)",      "kh_portie": 6},
            {"naam": "Rozijnen",            "portie": "1 handje (20g)",         "kh_portie": 15},
            {"naam": "Muesli/granenreep",   "portie": "1 reep (40g)",           "kh_portie": 26},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Speculoos",           "portie": "1 stuk (7g)",            "kh_portie": 5},
            {"naam": "Snoep/winegums",      "portie": "1 zakje (30g)",          "kh_portie": 26},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
            {"naam": "Pannenkoek",          "portie": "1 stuk (60g)",           "kh_portie": 27},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",   "kh_portie": 4},
        ],
    }

    MAALTIJD_CONFIG = {
        "Ontbijt":       {"pct": 0.25,  "icon": ""},
        "Tussendoor VM": {"pct": 0.083, "icon": ""},
        "Lunch":         {"pct": 0.25,  "icon": ""},
        "Tussendoor NM": {"pct": 0.083, "icon": ""},
        "Avondmaal":     {"pct": 0.25,  "icon": ""},
        "Avond snack":   {"pct": 0.083, "icon": ""},
    }

    tab1, tab2 = st.tabs(["  DAG 1 (2 dagen voor race)", "  DAG 2 (1 dag voor race)"])
    dag_totalen = {}

    for dag_idx, tab in enumerate([tab1, tab2], start=1):
        with tab:
            dag_kh = 0
            left_col, right_col = st.columns([1, 1])
            maaltijd_list = list(MAALTIJD_CONFIG.items())

            for col_obj, moment_slice in [
                (left_col,  maaltijd_list[:3]),
                (right_col, maaltijd_list[3:]),
            ]:
                with col_obj:
                    for m_name, m_cfg in moment_slice:
                        m_target  = round(dag_target * m_cfg["pct"])
                        status_key = f"cl_status_d{dag_idx}_{m_name}"
                        is_groen  = st.session_state.get(status_key, False)

                        # Bereken preview KH (huidige waarden uit session_state)
                        # Standaard producten
                        preview_kh = sum(
                            st.session_state.get(f"cl_d{dag_idx}_{m_name}_{p['naam']}", 0.0)
                            * p["kh_portie"]
                            for p in MOMENT_FOODS.get(m_name, [])
                        )
                        # Eigen producten meetellen
                        # Lees zowel base keys als _inp keys (widget waarden)
                        _eigen_base_prev = f"eigen_d{dag_idx}_{m_name}"
                        _n_eigen_prev = st.session_state.get(f"{_eigen_base_prev}_n", 0)
                        for _ei in range(_n_eigen_prev):
                            # Gebruik _inp key als die beschikbaar is (live widget waarde)
                            _ekh = st.session_state.get(
                                f"{_eigen_base_prev}_{_ei}_kh_inp",
                                st.session_state.get(f"{_eigen_base_prev}_{_ei}_kh", 0.0)
                            )
                            _eport = st.session_state.get(
                                f"{_eigen_base_prev}_{_ei}_port_inp",
                                st.session_state.get(f"{_eigen_base_prev}_{_ei}_port", 0.0)
                            )
                            preview_kh += float(_ekh) * float(_eport)
                        over_limiet = preview_kh > m_target

                        # Groene dot verdwijnt automatisch bij overschrijding
                        if over_limiet and is_groen:
                            st.session_state[status_key] = False
                            is_groen = False

                        # Label met groene dot
                        dot       = "🟢 " if is_groen else ""
                        exp_label = f"{dot}**{m_name}**"

                        with st.expander(exp_label, expanded=False):

                            # Producten header
                            st.markdown(
                                '<div style="font-size:0.7rem;color:#64748b;font-weight:700;'
                                'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">'
                                'Voedingsmiddel · portiegrootte · KH/portie · aantal porties</div>',
                                unsafe_allow_html=True
                            )

                            moment_kh = 0.0

                            # Standaard producten
                            for product in MOMENT_FOODS.get(m_name, []):
                                ss_key = f"cl_d{dag_idx}_{m_name}_{product['naam']}"
                                if ss_key not in st.session_state:
                                    saved = data.get("cl_waarden", {})
                                    st.session_state[ss_key] = float(saved.get(ss_key, 0.0))
                                if not isinstance(st.session_state.get(ss_key), (int, float)):
                                    st.session_state[ss_key] = 0.0

                                pc1, pc2 = st.columns([5, 1])
                                with pc1:
                                    st.markdown(
                                        f'<div style="padding:6px 0 2px;color:#f1f5f9;font-size:0.88rem;font-weight:600;line-height:1.4;">'
                                        f'{product["naam"]} '
                                        f'<span style="color:#64748b;font-size:0.78rem;font-weight:400;">'
                                        f'— {product["portie"]} · {product["kh_portie"]}g KH/portie</span></div>',
                                        unsafe_allow_html=True
                                    )
                                with pc2:
                                    val = st.number_input("p", min_value=0.0, max_value=20.0,
                                                          step=0.5, key=ss_key,
                                                          label_visibility="collapsed")
                                kh = val * product["kh_portie"]
                                moment_kh += kh
                                if val > 0:
                                    val_str = str(int(val)) if val == int(val) else str(val)
                                    st.markdown(
                                        f'<div style="font-size:0.72rem;color:#f97316;'
                                        f'margin:-4px 0 6px 0;text-align:right;">→ {val_str}× {product["kh_portie"]}g = <b>{round(kh)}g KH</b></div>',
                                        unsafe_allow_html=True
                                    )

                            # Eigen producten
                            eigen_key_base = f"eigen_d{dag_idx}_{m_name}"
                            n_eigen = st.session_state.get(f"{eigen_key_base}_n", 0)

                            st.markdown('<hr style="border-color:#1e293b;margin:8px 0 10px 0;">', unsafe_allow_html=True)
                            st.caption("Noteer bij eigen producten het aantal koolhydraten per portie (zie verpakking)")

                            for i in range(n_eigen):
                                e_naam = st.session_state.get(f"{eigen_key_base}_{i}_naam", "")
                                e_kh   = st.session_state.get(f"{eigen_key_base}_{i}_kh",   0.0)
                                e_port = st.session_state.get(f"{eigen_key_base}_{i}_port", 0.0)

                                if i == 0:
                                    lc1, lc2, lc3, lc4 = st.columns([4, 2, 2, 0.6])
                                    with lc1: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PRODUCTNAAM</div>', unsafe_allow_html=True)
                                    with lc2: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KH/PORTIE (g)</div>', unsafe_allow_html=True)
                                    with lc3: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PORTIES</div>', unsafe_allow_html=True)

                                ec1, ec2, ec3, ec4 = st.columns([4, 2, 2, 0.6])
                                with ec1:
                                    new_naam = st.text_input("Naam", value=e_naam,
                                        key=f"{eigen_key_base}_{i}_naam_inp",
                                        placeholder="bv. Cruesli extra", label_visibility="collapsed")
                                    st.session_state[f"{eigen_key_base}_{i}_naam"] = new_naam
                                with ec2:
                                    new_kh = st.number_input("KH/portie", value=float(e_kh),
                                        min_value=0.0, step=1.0,
                                        key=f"{eigen_key_base}_{i}_kh_inp",
                                        label_visibility="collapsed", help="KH per portie — zie verpakking")
                                    st.session_state[f"{eigen_key_base}_{i}_kh"] = new_kh
                                with ec3:
                                    new_port = st.number_input("Porties", value=float(e_port),
                                        min_value=0.0, step=1.0,
                                        key=f"{eigen_key_base}_{i}_port_inp",
                                        label_visibility="collapsed")
                                    st.session_state[f"{eigen_key_base}_{i}_port"] = new_port
                                with ec4:
                                    if st.button("🗑", key=f"{eigen_key_base}_{i}_del",
                                                 help="Verwijder", use_container_width=True):
                                        for j in range(i, n_eigen - 1):
                                            for field in ["naam", "kh", "port"]:
                                                st.session_state[f"{eigen_key_base}_{j}_{field}"] = \
                                                    st.session_state.get(f"{eigen_key_base}_{j+1}_{field}", 0 if field != "naam" else "")
                                        for field in ["naam", "kh", "port"]:
                                            st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}", None)
                                            st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}_inp", None)
                                        st.session_state[f"{eigen_key_base}_n"] = n_eigen - 1
                                        st.rerun()

                                eigen_kh_i = float(new_kh) * float(new_port)
                                moment_kh += eigen_kh_i
                                if new_port > 0 and new_kh > 0:
                                    st.markdown(
                                        f'<div style="font-size:0.72rem;color:#3b82f6;'
                                        f'margin:-4px 0 4px 0;text-align:right;">'
                                        f'→ {new_port:.0f}× {new_kh:.0f}g = <b>{round(eigen_kh_i)}g KH</b></div>',
                                        unsafe_allow_html=True
                                    )

                            if st.button("➕  Voeg eigen product toe", key=f"{eigen_key_base}_add",
                                         use_container_width=True):
                                st.session_state[f"{eigen_key_base}_n"] = n_eigen + 1
                                st.rerun()

                            # Progressiebalk op basis van werkelijke moment_kh (na alle widgets)
                            pct_nu = min(100, round((moment_kh / m_target) * 100)) if m_target > 0 else 0
                            over_nu = moment_kh > m_target
                            if over_nu:          balk_kleur = "#ef4444"
                            elif pct_nu >= 80:   balk_kleur = "#22c55e"
                            elif pct_nu >= 50:   balk_kleur = "#fbbf24"
                            else:                balk_kleur = "#f97316"

                            if over_nu:
                                st.markdown(
                                    '<div style="display:flex;gap:10px;align-items:center;'
                                    'margin-bottom:6px;background:rgba(239,68,68,0.1);'
                                    'border:1px solid #ef4444;border-radius:10px;padding:8px 12px;">' +
                                    '<img src="' + MASCOT_B64 + '" style="height:36px;width:auto;flex-shrink:0;">' +
                                    '<span style="color:#fca5a5;font-size:0.80rem;">'
                                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet!</span>'
                                    '</div>',
                                    unsafe_allow_html=True
                                )

                            st.markdown(
                                f'<div style="background:#1e293b;border-radius:6px;height:8px;margin:6px 0 8px 0;">' +
                                f'<div style="width:{pct_nu}%;height:100%;background:{balk_kleur};border-radius:6px;"></div>' +
                                f'</div>',
                                unsafe_allow_html=True
                            )

                            # Toggle knop: opslaan ↔ aanpassen
                            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                            reeds_groen = st.session_state.get(status_key, False)
                            if reeds_groen:
                                btn_lbl  = "🔓  Wijzigen"
                                btn_type = "secondary"
                            else:
                                btn_lbl  = "Dagdeel opslaan"
                                btn_type = "primary"
                            if st.button(btn_lbl, key=f"save_{dag_idx}_{m_name}",
                                         use_container_width=True, type=btn_type):
                                if reeds_groen:
                                    st.session_state[status_key] = False
                                else:
                                    st.session_state[status_key] = (pct_nu >= 80 and moment_kh <= m_target)
                                st.rerun()

                        # Gebruik session_state rechtstreeks voor dag_kh
                        # (moment_kh is 0 als expander gesloten is)
                        for _p in MOMENT_FOODS.get(m_name, []):
                            _ss = f"cl_d{dag_idx}_{m_name}_{_p['naam']}"
                            _val = float(st.session_state.get(_ss, 0.0))
                            dag_kh += _val * _p["kh_portie"]
                        # Eigen producten via _inp keys
                        _eigen_base_dag = f"eigen_d{dag_idx}_{m_name}"
                        _n_eigen_dag = st.session_state.get(f"{_eigen_base_dag}_n", 0)
                        for _ei in range(_n_eigen_dag):
                            _ekh   = st.session_state.get(f"{_eigen_base_dag}_{_ei}_kh_inp",
                                     st.session_state.get(f"{_eigen_base_dag}_{_ei}_kh", 0.0))
                            _eport = st.session_state.get(f"{_eigen_base_dag}_{_ei}_port_inp",
                                     st.session_state.get(f"{_eigen_base_dag}_{_ei}_port", 0.0))
                            dag_kh += float(_ekh) * float(_eport)

            # Dag totaal balk
            dag_pct   = round((dag_kh / dag_target) * 100) if dag_target > 0 else 0
            dag_over  = dag_kh > dag_target
            if dag_over:        bar_color = "#ef4444"
            elif dag_pct >= 80: bar_color = "#22c55e"
            elif dag_pct >= 50: bar_color = "#fbbf24"
            else:               bar_color = "#f97316"

            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;'
                f'padding:16px;text-align:center;margin-top:12px;">'
                f'<div style="font-weight:900;font-size:1rem;color:#f8fafc;margin-bottom:10px;">TOTAAL DAG {dag_idx}</div>'
                f'<div style="background:#1e293b;border-radius:8px;height:14px;overflow:hidden;">'
                f'<div style="width:{min(dag_pct,100)}%;height:100%;background:{bar_color};border-radius:8px;"></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

            if dag_over:
                st.markdown(
                    '<div style="display:flex;gap:10px;align-items:center;margin-top:8px;'
                    'background:rgba(239,68,68,0.1);border:1px solid #ef4444;'
                    'border-radius:10px;padding:12px 16px;">' +
                    '<img src="' + MASCOT_B64 + '" style="height:48px;width:auto;flex-shrink:0;">' +
                    '<span style="color:#fca5a5;font-size:0.88rem;">'
                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van deze dag!</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

            dag_totalen[f"dag{dag_idx}"] = {"totaal": round(dag_kh), "target": dag_target, "pct": dag_pct}

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)

    def _save_cl():
        cl_waarden = {}
        for d in [1, 2]:
            for m_name in MAALTIJD_CONFIG:
                for product in MOMENT_FOODS.get(m_name, []):
                    k = f"cl_d{d}_{m_name}_{product['naam']}"
                    cl_waarden[k] = st.session_state.get(k, 0)
        if "coach_data" not in st.session_state:
            st.session_state.coach_data = {}
        cl_status = {k: v for k, v in st.session_state.items() if k.startswith("cl_status_")}
        # Bewaar eigen producten carboloading
        eigen_cl = {}
        for d in [1, 2]:
            for m_name in MAALTIJD_CONFIG:
                base = f"eigen_d{d}_{m_name}"
                n = st.session_state.get(f"{base}_n", 0)
                items = []
                for i in range(n):
                    naam  = st.session_state.get(f"{base}_{i}_naam", "")
                    kh    = st.session_state.get(f"{base}_{i}_kh", 0.0)
                    port  = st.session_state.get(f"{base}_{i}_port", 0.0)
                    if naam and port > 0:
                        items.append({"naam": naam, "kh": kh, "port": port})
                if items:
                    eigen_cl[f"d{d}_{m_name}"] = items
        st.session_state.coach_data.update({
            "cl_waarden":  cl_waarden,
            "cl_eigen":    eigen_cl,
            "carboloading": dag_totalen,
            "dag_target":  dag_target,
            "factor":      factor,
            "cl_status":   cl_status,
        })

    with col_prev:
        if st.button("← Vorige", key="cl_prev"):
            _save_cl()
            st.session_state.coach_stap = 2
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="cl_next", use_container_width=True):
            _save_cl()
            st.session_state.coach_stap = 4
            st.rerun()



def _stap_racedag():
    data           = st.session_state.get("coach_data", {})
    start_time_str = data.get("start_time", "09:00")
    gewicht        = int(data.get("gewicht", 70) or 70)
    # KH richtlijn afhankelijk van timing (wetenschappelijk: g/kg/uur voor de start)
    # Wordt pas correct berekend na timing keuze — hier als fallback
    kh_min = round(gewicht * 1)
    kh_max = round(gewicht * 4)

    # Herstel status en waarden bij terugkeren
    if "rd_status_bevestigd" not in st.session_state:
        st.session_state["rd_status_bevestigd"] = data.get("rd_status", False)
    # Herstel rd_ waarden
    saved_rd_waarden = data.get("rd_waarden", {})
    for k, v in saved_rd_waarden.items():
        if k not in st.session_state:
            st.session_state[k] = v

    start_dt  = datetime.strptime(start_time_str, "%H:%M")
    start_uur = start_dt.hour

    # Automatisch maaltijdmoment bepalen op basis van starttijdstip
    if start_uur < 13:
        maaltijd_naam = "Ontbijt"
        maaltijd_icon = "🍳"
    elif start_uur < 17:
        maaltijd_naam = "Lunch"
        maaltijd_icon = "🥗"
    else:
        maaltijd_naam = "Avondmaal"
        maaltijd_icon = "🍽️"

    _coach_bubble(f"""
    Perfect! Nu plannen we jouw <b>laatste maaltijd voor de wedstrijd</b>!<br><br>
    Het doel is om met volle glycogeenvoorraden aan de start te staan, maar zonder een volle of zwaar gevoel in de maag.<br><br>
    ✅ Kies <b>licht verteerbare</b> producten: laag in vezels en vetten.<br>
    🎯 Kies producten die je maag goed verdraagt en die je al kent uit training.<br><br>
    Wanneer het balkje onderaan groen kleurt, bevestig je met <b>Dagdeel opslaan</b>. Er zal een groen bolletje verschijnen. Eigen producten kunnen onderaan worden toegevoegd.
    """)

    # Expander CSS voor leesbaarheid
    st.markdown("""
    <style>
    div[data-testid="stExpander"] > details > summary {
        background-color: #1e293b !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        color: #f1f5f9 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary p {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover p {
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary svg {
        fill: #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Timing dropdown
    onbijt_tips = {
        "3-4 uur voor start (aanbevolen)": -210,
        "2-3 uur voor start": -150,
        "1-2 uur voor start (licht)": -90,
    }
    ontbijt_keuze = st.selectbox("Wanneer eet je jouw laatste maaltijd?",
                                  list(onbijt_tips.keys()), key="rd_ontbijt_timing")
    offset       = onbijt_tips[ontbijt_keuze]
    ontbijt_tijd = (start_dt + timedelta(minutes=offset)).strftime("%H:%M")

    # KH richtlijn: 1-4g per kg lichaamsgewicht voor alle tijden
    kh_min = round(gewicht * 1)
    kh_max = round(gewicht * 4)









    # Productenlijsten per maaltijdmoment
    RACEDAG_FOODS = {
        "Ontbijt": [
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",          "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",          "kh_portie": 14},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Ontbijtgranen",       "portie": "1 kom (30g)",            "kh_portie": 25},
            {"naam": "Muesli",              "portie": "1 kom (40g)",            "kh_portie": 30},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Melk (dierlijk)",     "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Plantaardige melk",   "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",   "kh_portie": 4},
            {"naam": "Chocopasta",          "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",        "kh_portie": 35},
        ],
        "Lunch": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar", "kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",    "kh_portie": 30},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",          "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",          "kh_portie": 8},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",        "kh_portie": 35},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
        ],
        "Avondmaal": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar", "kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",    "kh_portie": 30},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",          "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",          "kh_portie": 8},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",        "kh_portie": 35},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
        ],
    }

    # Alle producten tonen als keuze
    seen = set()
    producten = []
    for foods in RACEDAG_FOODS.values():
        for p in foods:
            if p["naam"] not in seen:
                seen.add(p["naam"])
                producten.append(p)
    saved_rd  = data.get("rd_waarden", {})

    # ── Voortgangsbalk + avatar bij overschrijding ──────────────────────────
        # Expander met label + groen bolletje
    rd_is_groen = st.session_state.get("rd_status_bevestigd", False)
    rd_dot      = "🟢 " if rd_is_groen else ""
    rd_exp_label = f"{rd_dot}**Voedingsmiddelen laatste maaltijd voor de race**"

    with st.expander(rd_exp_label, expanded=False):
        # Header
        st.markdown(
            f'<div style="font-size:0.7rem;color:#64748b;font-weight:700;letter-spacing:0.1em;'
            f'text-transform:uppercase;margin-bottom:8px;">'
            f'Voedingsmiddel · portiegrootte · KH/portie · aantal porties</div>',
            unsafe_allow_html=True
        )

        ontbijt_kh = 0

        # Standaard producten
        for product in producten:
            ss_key = f"rd_{maaltijd_naam}_{product['naam']}"
            if ss_key not in st.session_state:
                st.session_state[ss_key] = int(saved_rd.get(ss_key, 0))
            if not isinstance(st.session_state.get(ss_key), int):
                st.session_state[ss_key] = 0

            pc1, pc2 = st.columns([5, 1])
            with pc1:
                st.markdown(
                    f'<div style="padding:6px 0 2px;color:#f1f5f9;font-size:0.88rem;font-weight:600;line-height:1.4;">'
                    f'{product["naam"]} '
                    f'<span style="color:#64748b;font-size:0.78rem;font-weight:400;">'
                    f'— {product["portie"]} · {product["kh_portie"]}g KH/portie</span></div>',
                    unsafe_allow_html=True
                )
            with pc2:
                val = st.number_input("p", min_value=0, max_value=20, step=1,
                                      key=ss_key, label_visibility="collapsed")
            kh = val * product["kh_portie"]
            ontbijt_kh += kh
            if val > 0:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#f97316;margin:-4px 0 6px 0;text-align:right;">'
                    f'→ {val}× {product["kh_portie"]}g = <b>{round(kh)}g KH</b></div>',
                    unsafe_allow_html=True
                )

        # Eigen producten
        st.markdown('<hr style="border-color:#1e293b;margin:10px 0;">', unsafe_allow_html=True)
        eigen_key_base = f"rd_eigen_{maaltijd_naam}"
        n_eigen = st.session_state.get(f"{eigen_key_base}_n", 0)

        eigen_kh_total = 0
        for i in range(n_eigen):
            e_naam = st.session_state.get(f"{eigen_key_base}_{i}_naam", "")
            # Gebruik _inp keys voor live widget waarden
            e_kh   = st.session_state.get(f"{eigen_key_base}_{i}_kh_inp",
                     st.session_state.get(f"{eigen_key_base}_{i}_kh",   0.0))
            e_port = st.session_state.get(f"{eigen_key_base}_{i}_port_inp",
                     st.session_state.get(f"{eigen_key_base}_{i}_port", 0.0))

            if i == 0:
                lc1, lc2, lc3, lc4 = st.columns([4, 2, 2, 0.6])
                with lc1: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PRODUCTNAAM</div>', unsafe_allow_html=True)
                with lc2: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KH/PORTIE (g)</div>', unsafe_allow_html=True)
                with lc3: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PORTIES</div>', unsafe_allow_html=True)

            ec1, ec2, ec3, ec4 = st.columns([4, 2, 2, 0.6])
            with ec1:
                new_naam = st.text_input("Naam", value=e_naam, key=f"{eigen_key_base}_{i}_naam_inp",
                                         placeholder="bv. Rijstwafel", label_visibility="collapsed")
                st.session_state[f"{eigen_key_base}_{i}_naam"] = new_naam
            with ec2:
                new_kh = st.number_input("KH/portie", value=float(e_kh), min_value=0.0, step=1.0,
                                         key=f"{eigen_key_base}_{i}_kh_inp",
                                         label_visibility="collapsed", help="KH per portie — zie verpakking")
                st.session_state[f"{eigen_key_base}_{i}_kh"] = new_kh
            with ec3:
                new_port = st.number_input("Porties", value=float(e_port), min_value=0.0, step=1.0,
                                           key=f"{eigen_key_base}_{i}_port_inp",
                                           label_visibility="collapsed")
                st.session_state[f"{eigen_key_base}_{i}_port"] = new_port
            with ec4:
                if st.button("🗑", key=f"{eigen_key_base}_{i}_del", help="Verwijder", use_container_width=True):
                    for j in range(i, n_eigen - 1):
                        for field in ["naam", "kh", "port"]:
                            st.session_state[f"{eigen_key_base}_{j}_{field}"] = \
                                st.session_state.get(f"{eigen_key_base}_{j+1}_{field}", 0 if field != "naam" else "")
                    for field in ["naam", "kh", "port"]:
                        st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}", None)
                        st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}_inp", None)
                    st.session_state[f"{eigen_key_base}_n"] = n_eigen - 1
                    st.rerun()

            eigen_kh_i = new_kh * new_port
            eigen_kh_total += eigen_kh_i
            if new_port > 0 and new_kh > 0:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#3b82f6;margin:-4px 0 4px 0;text-align:right;">'
                    f'→ {new_port:.0f}× {new_kh:.0f}g = <b>{round(eigen_kh_i)}g KH</b></div>',
                    unsafe_allow_html=True
                )

        st.caption("Noteer bij eigen producten het aantal koolhydraten per portie (zie verpakking)")
        if st.button("➕  Voeg eigen product toe", key=f"{eigen_key_base}_add", use_container_width=True):
            st.session_state[f"{eigen_key_base}_n"] = n_eigen + 1
            st.rerun()

        ontbijt_kh = round(ontbijt_kh + eigen_kh_total)

        # Progressiebalk — gebruik opgeslagen waarde als ontbijt_kh nog 0 is
        _ontbijt_kh_balk = ontbijt_kh
        if _ontbijt_kh_balk == 0:
            # Bereken uit session_state rechtstreeks
            _ontbijt_kh_balk = sum(
                st.session_state.get(f"rd_{maaltijd_naam}_{p['naam']}", 0) * p["kh_portie"]
                for p in producten
            )
            # Eigen producten via _inp keys
            _eigen_rd_n2 = st.session_state.get(f"rd_eigen_{maaltijd_naam}_n", 0)
            for _ei2 in range(_eigen_rd_n2):
                _ekh2   = st.session_state.get(f"rd_eigen_{maaltijd_naam}_{_ei2}_kh_inp",
                          st.session_state.get(f"rd_eigen_{maaltijd_naam}_{_ei2}_kh", 0.0))
                _eport2 = st.session_state.get(f"rd_eigen_{maaltijd_naam}_{_ei2}_port_inp",
                          st.session_state.get(f"rd_eigen_{maaltijd_naam}_{_ei2}_port", 0.0))
                _ontbijt_kh_balk += float(_ekh2) * float(_eport2)
            _ontbijt_kh_balk = round(_ontbijt_kh_balk)
        _pct_knop  = min(100, round((_ontbijt_kh_balk / kh_max) * 100)) if kh_max > 0 else 0
        _over_knop = _ontbijt_kh_balk > kh_max
        if _over_knop:          _balk_kleur = "#ef4444"
        elif _pct_knop >= 25:   _balk_kleur = "#22c55e"
        elif _pct_knop >= 15:   _balk_kleur = "#fbbf24"
        else:                   _balk_kleur = "#f97316"

        if _over_knop:
            st.markdown(
                '<div style="display:flex;gap:10px;align-items:center;margin-bottom:8px;'
                'background:rgba(239,68,68,0.1);border:1px solid #ef4444;'
                'border-radius:10px;padding:8px 12px;">' +
                '<img src="' + MASCOT_B64 + '" style="height:36px;width:auto;flex-shrink:0;">' +
                '<span style="color:#fca5a5;font-size:0.80rem;">'
                '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet!</span>'
                '</div>',
                unsafe_allow_html=True
            )
        st.markdown(
            f'<div style="background:#1e293b;border-radius:6px;height:8px;margin:6px 0 8px 0;">' +
            f'<div style="width:{_pct_knop}%;height:100%;background:{_balk_kleur};border-radius:6px;"></div>' +
            f'</div>',
            unsafe_allow_html=True
        )

        # Toggle knop: opslaan ↔ aanpassen
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        _over_knop   = ontbijt_kh > kh_max
        _reeds_groen = st.session_state.get("rd_status_bevestigd", False)
        if _reeds_groen:
            _btn_lbl  = "🔓  Wijzigen"
            _btn_type = "secondary"
        else:
            _btn_lbl  = "Dagdeel opslaan"
            _btn_type = "primary"
        if st.button(_btn_lbl, key="rd_save", use_container_width=True, type=_btn_type):
            if _reeds_groen:
                st.session_state["rd_status_bevestigd"] = False
            else:
                # Groen als >= 25% van target en niet over limiet
                st.session_state["rd_status_bevestigd"] = (_pct_knop >= 25 and not _over_knop)
                if not st.session_state["rd_status_bevestigd"] and _pct_knop > 0:
                    st.warning("Vul minstens 25% van je KH target in om op te slaan.")
            # Bewaar rd_waarden bij klikken zodat ze behouden blijven bij navigatie
            _rd_waarden_save = {
                f"rd_{maaltijd_naam}_{p['naam']}": st.session_state.get(f"rd_{maaltijd_naam}_{p['naam']}", 0)
                for p in producten
            }
            if "coach_data" not in st.session_state:
                st.session_state.coach_data = {}
            st.session_state.coach_data["rd_waarden"]    = _rd_waarden_save
            st.session_state.coach_data["rd_status"]     = st.session_state.get("rd_status_bevestigd", False)
            st.session_state.coach_data["ontbijt_kh"]    = ontbijt_kh
            st.session_state.coach_data["ontbijt_timing"] = ontbijt_keuze
            st.session_state.coach_data["ontbijt_tijd"]  = ontbijt_tijd
            st.session_state.coach_data["maaltijd_moment"] = maaltijd_naam
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="rd_prev"):
            st.session_state.coach_stap = 3
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="rd_next", use_container_width=True):
            rd_waarden = {f"rd_{maaltijd_naam}_{p['naam']}": st.session_state.get(f"rd_{maaltijd_naam}_{p['naam']}", 0)
                          for p in producten}
            # Bewaar eigen producten racedag
            eigen_rd_base = f"rd_eigen_{maaltijd_naam}"
            n_eigen_rd = st.session_state.get(f"{eigen_rd_base}_n", 0)
            eigen_rd = []
            for i in range(n_eigen_rd):
                naam  = st.session_state.get(f"{eigen_rd_base}_{i}_naam", "")
                kh    = st.session_state.get(f"{eigen_rd_base}_{i}_kh", 0.0)
                port  = st.session_state.get(f"{eigen_rd_base}_{i}_port", 0.0)
                if naam and port > 0:
                    eigen_rd.append({"naam": naam, "kh": kh, "port": port})
            st.session_state.coach_data.update({
                "ontbijt_kh":      ontbijt_kh,
                "ontbijt_timing":  ontbijt_keuze,
                "ontbijt_tijd":    ontbijt_tijd,
                "maaltijd_moment": maaltijd_naam,
                "pre_totaal_kh":   ontbijt_kh,
                "rd_waarden":      rd_waarden,
                "rd_eigen":        eigen_rd,
                "rd_status":       st.session_state.get("rd_status_bevestigd", False),
            })
            st.session_state.coach_stap = 5
            st.rerun()



def _stap_raceplan():
    data = st.session_state.get("coach_data", {})
    # Sport + duur balk + wetenschappelijke adviezen (geen KH grammen)
    _sport     = data.get("sport", "")
    _tot_min   = int(data.get("totale_min", 0) or 0)
    _sport_icon = SPORT_ICONS.get(_sport, "🏅")

    # Adviezen per sport per tijdsduur
    RACE_ADVIEZEN = {
        "Fietsen": {
            (0,   75):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (75,  120):  ["Kies voor een mix van vloeibare en vaste koolhydraatbronnen",
                          "Sportdrank + rijstwafel of reep: combineer gel met vast voedsel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (120, 181):  ["Kies voor een mix van gels, vaste voeding en sportdrank",
                          "Wissel regelmatig af tussen vloeibaar en vast",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (181, 9999): ["Kies voor een mix van gels, vaste voeding en sportdrank",
                          "Kies producten die je al gebruikt hebt tijdens training",
                          "Geen nieuwe producten op racedag - alleen vertrouwde keuzes"],
        },
        "Lopen": {
            (0,   60):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (60,  120):  ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (120, 181):  ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (181, 9999): ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
        "Triatlon": {
            (0,   60):   ["Zwemmen: niet mogelijk om in te nemen — start optimaal gevoed",
                          "Fiets: vloeibare koolhydraatbronnen (sportdrank)",
                          "Loop: water of sportdrank volstaat bij sprint",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (60,  120):  ["Fiets is het hoofdtankmoment — start onmiddellijk na T1",
                          "Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank + gel",
                          "Loop: gel of sportdrank, kies voor vloeibare bronnen",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (120, 240):  ["Fiets: kies voor een mix van gels, vaste voeding en sportdrank",
                          "Loop: bij voorkeur vloeibaar (gel + water), GI-gevoeliger na fietsen",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (240, 9999): ["Fiets: mix van gels, repen, sportdrank en vast voedsel",
                          "Loop: vloeibaar + cola in het laatste deel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
        "Duatlon": {
            (0,   75):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (75,  150):  ["Fiets = hoofdtankmoment: kies bij voorkeur vloeibare koolhydraatbronnen",
                          "Gel aan start 2e loop is essentieel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (150, 210):  ["Kies voor een mix van gels, vaste voeding en sportdrank op de fiets",
                          "2e loop: gel + water, kies voor vloeibare bronnen",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (210, 9999): ["Kies voor een mix van gels, vaste voeding en sportdrank",
                          "Meer GI-stress dan triatlon — plan innametiming op rustige segmenten",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
        "Crossduatlon": {
            (0,   90):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (90,  150):  ["MTB: kies bij voorkeur vloeibare koolhydraatbronnen — trillingen verhogen GI-stress",
                          "Neem in op vlakke/rechte stukken, nooit op technisch terrein",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (150, 9999): ["Kies voor een mix van gels en sportdrank",
                          "MTB: enkel vloeibaar, geen vast voedsel op technisch terrein",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
    }

    # Zoek de juiste adviezen op basis van sport en duur
    sport_key = _sport if _sport in RACE_ADVIEZEN else "Fietsen"
    tips = []
    for (dmin, dmax), advies in RACE_ADVIEZEN[sport_key].items():
        if dmin <= _tot_min < dmax:
            tips = advies
            break
    if not tips and _tot_min >= 240:
        tips = list(RACE_ADVIEZEN[sport_key].values())[-1]

    # Balk: sport + duur
    sport_html = (
        '<div style="background:rgba(59,130,246,0.08);border:1px solid #3b82f6;'
        'border-radius:12px;padding:14px 18px;margin-bottom:16px;">' +
        f'<div style="color:#60a5fa;font-weight:800;font-size:0.85rem;margin-bottom:10px;">' +
        f'{_sport_icon} {_sport} &nbsp;·&nbsp; ⏱️ {_tot_min//60}u{_tot_min%60:02d}m</div>' +
        '<div style="color:#94a3b8;font-size:0.78rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.1em;margin-bottom:8px;">💡 Advies voor jouw race</div>'
    )
    for tip in tips:
        sport_html += (
            f'<div style="display:flex;gap:8px;margin-bottom:6px;align-items:flex-start;">' +
            f'<span style="color:#f97316;flex-shrink:0;">→</span>' +
            f'<span style="color:#e2e8f0;font-size:0.85rem;">{tip}</span></div>'
        )
    # Voeg oproep toe onderaan, behalve bij protocollen zonder KH inname
    geen_kh = any("Geen extra koolhydraten nodig" in tip for tip in tips)
    if not geen_kh:
        sport_html += (
            '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #1e3a5f;">' +
            '<span style="color:#60a5fa;font-size:0.95rem;font-weight:600;">'
            '📝 Kies hieronder je producten en druk op <b>Preview schema</b>. ' +
            'Ik maak een voorstel dat je daarna zelf kan aanpassen.</span></div>'
        )

    # ORS / hitte melding in adviesbalk
    _temp_val  = int(data.get("temp", 18) or 18)
    _vocht_val = int(data.get("vochtigheid", 50) or 50)
    _pool_data = data.get("pool", {})
    _supp_data = _pool_data.get("supplementen", {})
    _ors_naam  = _supp_data.get("ors_naam", "") if isinstance(_supp_data, dict) else ""
    _tot_min_adv = int(data.get("totale_min", 0) or 0)
    if _tot_min_adv >= 120 and _temp_val >= 25:
        if _temp_val >= 28:
            # Extreme hitte
            sport_html += (
                '<div style="margin-top:8px;background:rgba(239,68,68,0.15);border:1px solid #ef4444;' +
                'border-radius:8px;padding:8px 12px;">' +
                '<span style="color:#fca5a5;font-size:0.82rem;">🔴 <b>Extreme hitte</b> — verhoog vochtinname. ' +
                'Voeg ORS toe aan je voeding tijdens de laatste 48u voor de wedstrijd en opteer voor een sportdrank tijdens de wedstrijd.</span></div>'
            )
        else:
            # Warm (25-28°C)
            sport_html += (
                '<div style="margin-top:8px;background:rgba(249,115,22,0.12);border:1px solid #f97316;' +
                'border-radius:8px;padding:8px 12px;">' +
                '<span style="color:#fed7aa;font-size:0.82rem;">🌡️ <b>Warm weer & lange inspanning</b> — ' +
                'Voeg ORS toe aan je voeding tijdens de laatste 48u voor de wedstrijd en opteer voor een sportdrank tijdens de wedstrijd.</span></div>'
            )

    sport_html += '</div>'
    # Avatar naast de blauwe kader
    avatar_html = (
        '<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px;">' +
        f'<img src="{MASCOT_B64}" style="height:80px;width:auto;flex-shrink:0;margin-top:4px;">' +
        '<div style="flex:1;">' + sport_html + '</div>' +
        '</div>'
    )
    st.markdown(avatar_html, unsafe_allow_html=True)

    def _prod_blok(label, kleur, emoji, key_n, key_naam, key_kh,
                       default_n, placeholder, default_kh, eenheid="KH/stuk"):
        n = st.number_input(f"Aantal {label.lower()}", 0, 8, default_n,
                            key=key_n, label_visibility="collapsed")
        pool_items = []
        for i in range(int(n)):
            c1, c2, c3 = st.columns([3, 1.5, 0.8])
            with c1:
                naam = st.text_input("naam", key=f"{key_naam}_{i}",
                                     placeholder=placeholder, label_visibility="collapsed")
            with c2:
                kh = st.number_input(eenheid, key=f"{key_kh}_{i}",
                                     min_value=0, value=default_kh, label_visibility="collapsed")
            with c3:
                st.markdown(
                    f'<div style="padding:8px 4px;font-size:0.85rem;font-weight:700;' +
                    f'color:#f97316;text-align:center;">{kh}g</div>',
                    unsafe_allow_html=True)
            if naam:
                pool_items.append({"naam": naam, "kh": kh})
        return pool_items

    def _sectie_header(label, kleur, emoji):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:14px 0 6px 0;">' +
            f'<span style="font-size:1.1rem;">{emoji}</span>' +
            f'<span style="color:{kleur};font-weight:800;font-size:0.88rem;'
            f'letter-spacing:0.08em;">{label}</span></div>',
            unsafe_allow_html=True)

    # ── 1. Sportdrank ────────────────────────────────────────────────────────
    _sectie_header("SPORTDRANK", "#3b82f6", "🥤")
    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Naam &nbsp;·&nbsp; KH per 500ml &nbsp;·&nbsp; Totaal</div>', unsafe_allow_html=True)
    drank_pool = _prod_blok("Sportdrank", "#3b82f6", "🥤",
                            "rp_n_drank", "rp_drank", "rp_dkh",
                            1, "bijv. Maurten 320", 70, "KH/500ml")

    # ── 2. Energy gels ───────────────────────────────────────────────────────
    _sectie_header("ENERGY GELS", "#60a5fa", "⚡")
    gel_col1, gel_col2 = st.columns(2)
    with gel_col1:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Gewone gels &nbsp;·&nbsp; KH/gel</div>', unsafe_allow_html=True)
        gels_pool = _prod_blok("Gel", "#60a5fa", "⚡",
                               "rp_n_gels", "rp_gel", "rp_gkh",
                               1, "bijv. SIS Go Gel", 22, "KH/gel")
    with gel_col2:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Gels met cafeïne &nbsp;·&nbsp; KH/gel</div>', unsafe_allow_html=True)
        cafe_pool = _prod_blok("Cafeïne gel", "#8b5cf6", "⚡",
                               "rp_n_cafe", "rp_cafe", "rp_ckh",
                               0, "bijv. SIS Caffeine Gel", 22, "KH/gel")

    # ── 3. Vaste voeding ─────────────────────────────────────────────────────
    _sectie_header("VASTE VOEDING", "#10b981", "🍌")
    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Naam &nbsp;·&nbsp; KH per portie &nbsp;·&nbsp; Totaal</div>', unsafe_allow_html=True)
    vast_pool = _prod_blok("Vast voedsel", "#10b981", "🍌",
                           "rp_n_vast", "rp_vast", "rp_vkh",
                           0, "bijv. Rijstwafel, banaan", 25, "KH/portie")

    # ── 4. Supplementen ───────────────────────────────────────────────────────
    # ── Supplementen header met info tooltip direct naast titel ──────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span style="font-size:0.72rem;font-weight:700;color:#8b5cf6;letter-spacing:1px;">💊 SUPPLEMENTEN</span>
        <span style="display:inline-flex;align-items:center;justify-content:center;
                     width:16px;height:16px;border-radius:50%;
                     background:rgba(139,92,246,0.2);border:1px solid #8b5cf6;
                     color:#8b5cf6;font-size:10px;font-weight:700;cursor:help;flex-shrink:0;"
              title="Zorg ervoor dat je juist suppleert tijdens je wedstrijd!">i</span>
    </div>
    """, unsafe_allow_html=True)

    ors_naam = ""
    ors_mg   = 0
    gum_mg   = 0

    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Supplementen (cafeïnegum, ORS, ...)</div>', unsafe_allow_html=True)

    # Dynamische supplement invoer — elk supplement apart
    n_supp = st.session_state.get("rp_n_supp", 1)
    supp_namen = []
    for _si in range(n_supp):
        _sc1, _sc2, _sc3 = st.columns([5, 1, 1])
        with _sc1:
            _sn = st.text_input(f"Supplement {_si+1}",
                                placeholder="bijv. Run Gum, SIS Hydro...",
                                key=f"rp_supp_naam_{_si}",
                                label_visibility="collapsed")
            supp_namen.append(_sn.strip() if _sn else "")
        with _sc2:
            if _si == n_supp - 1 and st.button("＋", key=f"rp_supp_add_{_si}", help="Toevoegen"):
                st.session_state["rp_n_supp"] = n_supp + 1
                st.rerun()
        with _sc3:
            if n_supp > 1 and st.button("✕", key=f"rp_supp_del_{_si}", help="Verwijderen"):
                for _j in range(_si, n_supp - 1):
                    st.session_state[f"rp_supp_naam_{_j}"] = st.session_state.get(f"rp_supp_naam_{_j+1}", "")
                st.session_state["rp_n_supp"] = n_supp - 1
                st.rerun()

    # Lijst van ingevulde supplementen (zonder lege)
    supp_lijst = [s for s in supp_namen if s]
    gum_naam = supp_lijst[0] if supp_lijst else ""  # eerste voor backward compat
    supp_alle = supp_lijst  # volledige lijst voor rapport

    st.markdown("<br>", unsafe_allow_html=True)

    pool = {
        "drank": drank_pool,
        "gels":  gels_pool,
        "cafe":  cafe_pool,
        "vast":  vast_pool,
        "supplementen": {
            "ors_naam":  ors_naam,
            "ors_mg":    ors_mg,
            "gum_naam":  gum_naam,     # eerste supplement (compat)
            "supp_lijst": supp_alle,   # volledige lijst
        },
    }
    # Pool altijd opslaan zodat preview er toegang toe heeft
    if "coach_data" not in st.session_state:
        st.session_state.coach_data = {}
    st.session_state.coach_data["pool"] = pool

    # ── Knoppen: Vorige boven Preview, breedte = vaste voeding sectie ─────────
    if st.button("← Vorige", key="rp_prev"):
        st.session_state.coach_stap = 4
        st.rerun()
    if st.button("👁  Preview schema", key="rp_preview", use_container_width=True):
        # Wis n_items keys zodat defaults opnieuw berekend worden
        for k in list(st.session_state.keys()):
            if k.startswith("prev_n_items_") or k.startswith("prev_t_") or k.startswith("prev_p_") or k.startswith("prev_a_") or k.startswith("prev_w_"):
                del st.session_state[k]
        st.session_state.pop("rp_preview_leeg", None)
        st.session_state["rp_show_preview"] = True
        st.rerun()

    # ── Preview schema ─────────────────────────────────────────────────────────
    if st.session_state.get("rp_show_preview", False):
        import math
        from datetime import datetime, timedelta

        data       = st.session_state.get("coach_data", {})
        sport      = data.get("sport", "Fietsen")
        totale_min = int(data.get("totale_min", 180) or 180)
        temp       = int(data.get("temp", 18) or 18)
        vochtigheid = int(int(data.get("vochtigheid", 50) or 50) or 50)
        hoogte     = int(data.get("hoogte", 0) or 0)
        start_str  = data.get("start_time", "09:00")
        gewicht    = int(data.get("gewicht", 70) or 70)
        niveau     = data.get("niveau", "Recreatief")
        ervaring   = data.get("ervaring", "Eerste wedstrijd")
        min_kh     = data.get("min_kh", 60)
        max_kh     = data.get("max_kh", 90)
        start_dt   = datetime.strptime(start_str, "%H:%M")
        aantal_uren = math.ceil(int(totale_min or 0) / 60)

        # ── Sport-fase labels ──────────────────────────────────────────────────
        FASE_LABELS = {
            "Triatlon": {
                1: ("🏊", "Zwemmen", "Geen inname mogelijk — start gevoed"),
                2: ("🚴", "Fietsen", "Hoofdtankmoment — start direct bij T1"),
                3: ("🚴", "Fietsen", ""),
                4: ("🚴", "Fietsen", ""),
                5: ("🏃", "Lopen", "Vloeibaar only, GI-gevoeliger na fietsen"),
                6: ("🏃", "Lopen", ""),
                7: ("🏃", "Lopen", ""),
            },
            "Duatlon": {
                1: ("🏃", "Loop 1", "Hoge intensiteit — geen inname mogelijk"),
                2: ("🚴", "Fietsen", "Hoofdtankmoment — start direct"),
                3: ("🚴", "Fietsen", ""),
                4: ("🏃", "Loop 2", "Gel mee vanuit T2"),
                5: ("🏃", "Loop 2", ""),
            },
            "Crossduatlon": {
                1: ("🏃", "Trail 1", "Technisch terrein — geen inname"),
                2: ("🚵", "MTB", "Neem in op vlakke stukken, vloeibaar only"),
                3: ("🚵", "MTB", ""),
                4: ("🏃", "Trail 2", "Gel mee vanuit T2"),
            },
        }

        def get_fase(sport, uur_num, totale_min):
            if sport not in FASE_LABELS:
                return None
            fasen = FASE_LABELS[sport]
            # Schaal uren naar fases op basis van totale duur
            if sport == "Triatlon":
                zwem_uren = 1
                loop_start = max(3, aantal_uren - max(1, aantal_uren // 3))
                if uur_num <= zwem_uren:
                    return fasen.get(1)
                elif uur_num < loop_start:
                    return fasen.get(2)
                else:
                    return fasen.get(5)
            return fasen.get(uur_num)

        # ── Geen KH drempel ───────────────────────────────────────────────────
        geen_kh_drempel = {"Fietsen": 75, "Lopen": 60, "Duatlon": 75, "Crossduatlon": 90}
        geen_kh = int(totale_min or 0) < geen_kh_drempel.get(sport, 75)

        # ── Globale instellingen ──────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        # CSS voor uitlijning preview met rest van pagina
        st.markdown("""
        <style>
        div[data-testid="stExpander"] > details { background-color: #0f172a !important; }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(
            '<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:12px;">' +
            f'<img src="{MASCOT_B64}" style="height:72px;width:auto;flex-shrink:0;margin-top:4px;">' +
            '<div style="flex:1;background:#0f172a;border:2px solid #3b82f6;border-radius:14px;padding:14px 18px;">' +
            '<div style="color:#60a5fa;font-weight:800;font-size:0.9rem;margin-bottom:4px;">PREVIEW RACEPLAN — aanpasbaar</div>' +
            '<div style="color:#94a3b8;font-size:0.82rem;">Wijzig het plan indien gewenst! Je kan zelf puzzelen met de tijd, voedingsmiddelen (tot op halve portie) en vocht per wedstrijduur. Indien gewenst kan je per uur ook notities toevoegen. Probeer zowel de koolhydraten als het vocht aan te vullen tot de balk groen is!</div>' +
            '</div></div>',
            unsafe_allow_html=True
        )

        # Vocht berekening
        basis_vocht = 800 if int(temp or 18) > 25 else (600 if int(temp or 18) > 15 else 400)
        f_factor    = (int(hoogte or 0) / 1000) * 0.15 + (0.15 if int(vochtigheid or 0) > 70 else 0)
        # Sportniveau-correctie: enkel Elite/Semi-pro +5%
        niveau_factor = 1.05 if niveau == "Elite / Semi-pro" else 1.0

        vocht_uur = round(basis_vocht * (1 + f_factor) * niveau_factor / 10) * 10
        vocht_pm  = round(vocht_uur / 3 / 10) * 10  # per innamemoment
        gel_interval = 40   # minuten tussen gels
        vast_vanaf   = 1    # vast voedsel vanaf uur 1
        cafe_vanaf   = 2    # cafeïne vanaf uur 2

                # ── Bouw lijst van alle producten ─────────────────────────────────────
        alle_opties = []
        kh_map      = {}
        emoji_map   = {}

        if pool.get("drank"):
            for p in pool["drank"]:
                naam  = p.get("naam", p.get("name", "Sportdrank"))
                kh_pm = round((p["kh"] / 500) * vocht_pm)
                lbl   = f"🥤 {naam} ({vocht_pm}ml)"
                alle_opties.append(lbl)
                kh_map[lbl]    = kh_pm
                emoji_map[lbl] = "🥤"

        if pool.get("gels"):
            for p in pool["gels"]:
                naam = p.get("naam", p.get("name", "Gel"))
                lbl  = f"⚡ {naam}"
                alle_opties.append(lbl)
                kh_map[lbl]    = p["kh"]
                emoji_map[lbl] = "⚡"

        if pool.get("vast"):
            for p in pool["vast"]:
                naam = p.get("naam", p.get("name", "Vast"))
                # Kies emoji op basis van productnaam
                naam_l = naam.lower()
                if any(w in naam_l for w in ["reep", "bar", "energiereep"]):
                    em = "🍫"
                elif any(w in naam_l for w in ["koek", "wafel", "speculoos", "pannenkoek", "granola", "muesli", "biscuit"]):
                    em = "🍪"
                elif any(w in naam_l for w in ["rijstwafel", "rijst"]):
                    em = "🌾"
                elif any(w in naam_l for w in ["banaan"]):
                    em = "🍌"
                elif any(w in naam_l for w in ["appel", "peer", "fruit", "kiwi", "appelmoes"]):
                    em = "🍎"
                elif any(w in naam_l for w in ["dadel", "rozijn", "noot"]):
                    em = "🌰"
                else:
                    em = "🍱"
                lbl  = f"{em} {naam}"
                alle_opties.append(lbl)
                kh_map[lbl]    = p["kh"]
                emoji_map[lbl] = em

        if pool.get("cafe"):
            for p in pool["cafe"]:
                naam = p.get("naam", p.get("name", "Cafeïne gel"))
                lbl  = f"⚡ {naam} (CAF)"
                alle_opties.append(lbl)
                kh_map[lbl]    = p["kh"]
                emoji_map[lbl] = "☕"

        # Supplementen toevoegen
        supp = pool.get("supplementen", {})
        if supp.get("ors_naam"):
            lbl = f"💊 {supp['ors_naam']} (ORS)"
            alle_opties.append(lbl)
            kh_map[lbl]    = 0
            emoji_map[lbl] = "💊"
        # Elk supplement apart als selecteerbare optie
        _supp_lijst = supp.get("supp_lijst", [])
        if not _supp_lijst and supp.get("gum_naam"):
            _supp_lijst = [supp["gum_naam"]]
        for _sn in _supp_lijst:
            if _sn:
                lbl = f"🍬 {_sn}"
                if lbl not in alle_opties:
                    alle_opties.append(lbl)
                    kh_map[lbl]    = 0
                    emoji_map[lbl] = "🍬"

        alle_opties += ["— leeg —"]
        kh_map["— leeg —"] = 0

        # Drank label (eerste optie indien beschikbaar)
        drank_lbl = next((l for l in alle_opties if l.startswith("🥤")), "— leeg —")
        gel_lbl   = next((l for l in alle_opties if l.startswith("⚡")), None)
        vast_lbl  = next((l for l in alle_opties if l.startswith("🍌")), None)
        # cafe_lbl = eerste cafeïne gel optie
        _cafe_namen = [p.get("naam", p.get("name","")) for p in pool.get("cafe", [])]
        cafe_lbl = next((l for l in alle_opties if any(n in l for n in _cafe_namen)), None)

        # ── Per uur schema ────────────────────────────────────────────────────
        totaal_kh_race    = 0
        totaal_vocht_race = 0


        # Sport-specifieke tips per uur
        UUR_TIPS = {
            "Fietsen":      "Kies per intervalmoment één product: sportdrank, gel of vast voedsel. Voeg water toe bij gels.",
            "Lopen":        "Kies per intervalmoment één product: gel of sportdrank. Neem altijd water bij een gel.",
            "Triatlon":     "Fietsgedeelte = hoofdtankmoment. Loopgedeelte: kies gels met water, vermijd vast voedsel.",
            "Duatlon":      "Fiets = hoofdtankmoment. Neem bij T2 een gel mee voor de tweede loopfase.",
            "Crossduatlon": "Neem in op vlakke MTB-stukken. Kies gels met water, geen vast voedsel op technisch terrein.",
        }
        uur_tip = UUR_TIPS.get(sport, "")

        # Kolomtitels
        t1, t2, t3, tplus, t4, t5, t6 = st.columns([1.1, 2.2, 0.8, 0.25, 1.8, 0.7, 0.35])
        with t1: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">TIJDSTIP</div>', unsafe_allow_html=True)
        with t2: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KOOLHYDRAATBRON</div>', unsafe_allow_html=True)
        with t3: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">AANTAL</div>', unsafe_allow_html=True)
        with t4: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">WATER</div>', unsafe_allow_html=True)
        with t5: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KH</div>', unsafe_allow_html=True)

        for u in range(aantal_uren):
            u_num    = u + 1
            is_last  = (u == aantal_uren - 1)
            # rest_min altijd beschikbaar — ook voor niet-laatste uren
            rest_min = int(totale_min or 0) % 60 if int(totale_min or 0) % 60 != 0 else 60
            uur_start = start_dt + timedelta(hours=u)
            cur_min  = round(min_kh * 0.6) if is_last else min_kh
            cur_max  = round(max_kh * 0.6) if is_last else max_kh
            fase     = get_fase(sport, u_num, totale_min)

            # Fase label
            fase_html = ""
            if fase:
                fase_icon, fase_naam, fase_tip = fase
                fase_html = f' &nbsp;<span style="color:#cbd5e1;font-size:0.75rem;">{fase_icon} {fase_naam}'
                if fase_tip:
                    fase_html += f' — {fase_tip}'
                fase_html += '</span>'

            # Tip per uur
            if geen_kh or (fase and "Geen inname" in fase[2]):
                _uur_tip = "💧 Enkel water of mondspoeling"
            elif is_last:
                _rest_tip = int(totale_min or 0) % 60 if int(totale_min or 0) % 60 != 0 else 60
                _vocht_tip = round(vocht_uur * (_rest_tip / 60))
                if _rest_tip < 15:
                    _kh_tip = "geen KH meer"
                elif _rest_tip < 31:
                    _kh_tip = "15–20g KH"
                elif _rest_tip < 46:
                    _kh_tip = "30–40g KH"
                else:
                    _kh_tip = f"{round(min_kh*0.6)}–{round(max_kh*0.6)}g KH"
                _uur_tip = f"🏁 Laatste uur — {_kh_tip} · {_vocht_tip}ml vocht · kleine slokjes · geen vast voedsel"
            elif u_num == 1:
                _uur_tip = "⚡ Start vroeg met innemen — wacht niet op honger of dorst"
            elif fase and "Zwemmen" in fase[1]:
                _uur_tip = "🏊 Geen inname mogelijk — start gevoed aan het fietsen"
            elif fase and "Loop" in fase[1]:
                _uur_tip = "Kies per rij één product. Neem bij een gel altijd water via de waterkolom."
            elif sport == "Lopen":
                _uur_tip = "Kies vloeibare bronnen. Voeg water toe via de waterkolom bij elke gel."
            else:
                _uur_tip = "Kies per rij één product. Voeg water toe bij gels via de waterkolom."

            rest_label = f" &nbsp;<span style='color:#f97316;font-size:0.75rem;'>⏱ nog {rest_min} min</span>" if is_last and rest_min < 60 else ""
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px 10px 0 0;padding:9px 14px;margin-top:12px;">'
                f'<span style="color:#f8fafc;font-weight:800;font-size:0.9rem;">'
                f'UUR {u_num} — {uur_start.strftime("%H:%M")}{rest_label}</span>'
                + (fase_html if fase_html else '')
                + (f'<div style="color:#94a3b8;font-size:0.72rem;margin-top:4px;">{uur_tip}</div>' if uur_tip and not geen_kh else "")
                + f'<div style="color:#93c5fd;font-size:0.73rem;margin-top:5px;">{_uur_tip}</div>' +
                f'</div>',
                unsafe_allow_html=True
            )

            # Notitie veld per uur
            notitie = st.text_input("Notitie", value="",
                placeholder="Notitie (bv. T2 — wisseling, cola station, ...)",
                key=f"prev_notitie_{u_num}",
                label_visibility="collapsed"
            )

            # KH target laatste uur schalen naar resterende tijd
            if is_last:
                if rest_min < 15:
                    cur_min = 0
                    cur_max = 0
                elif rest_min < 31:
                    cur_min = 15
                    cur_max = 20
                elif rest_min < 46:
                    cur_min = 30
                    cur_max = 40
                else:
                    # > 45 min resterend → 60% van normaal target
                    cur_min = round(min_kh * 0.6)
                    cur_max = round(max_kh * 0.6)

            # Standaard items op basis van rest_min
            default_items = []
            if is_last:
                if geen_kh or rest_min < 15:
                    # Geen KH meer — enkel water/spoelen
                    default_items = [
                        ("10min", "— leeg —"),
                    ]
                elif rest_min < 31:
                    # 15–30 min: 1 moment vloeibaar
                    default_items = [
                        ("15min", drank_lbl),
                    ]
                elif rest_min < 46:
                    # 31–45 min: 2 momenten vloeibaar
                    default_items = [
                        ("20min", drank_lbl),
                        ("35min", "— leeg —"),
                    ]
                else:
                    # > 45 min: 2 momenten normaal
                    default_items = [
                        ("20min", drank_lbl),
                        ("40min", drank_lbl),
                    ]
            else:
                default_items = [
                    ("20min", drank_lbl if not geen_kh else "— leeg —"),
                    ("40min", drank_lbl if not geen_kh else "— leeg —"),
                    ("60min", "— leeg —"),
                ]

            # ── ORS automatisch inplannen bij hitte ──────────────────────────
            ors_naam  = supp.get("ors_naam", "") if isinstance(supp, dict) else ""
            n_items_key = f"prev_n_items_{u_num}"
            if n_items_key not in st.session_state:
                # Na reset: lege rijen, anders defaults
                if st.session_state.get("rp_preview_leeg", False):
                    st.session_state[n_items_key] = 0
                else:
                    st.session_state[n_items_key] = len(default_items)

            n_items = st.session_state[n_items_key]

            uur_kh    = 0
            uur_vocht = 0
            # Leeg-flag blijft actief tijdens hele preview render
            timing_opties = ["5min", "10min", "15min", "20min", "25min", "30min", "35min", "40min", "45min", "50min", "55min", "60min"]

            for i_idx in range(n_items):
                def_timing = default_items[i_idx][0] if i_idx < len(default_items) else "20min"
                def_prod   = default_items[i_idx][1] if i_idx < len(default_items) else "— leeg —"
                if def_prod not in alle_opties:
                    def_prod = "— leeg —"

                t_key = f"prev_t_{u_num}_{i_idx}"
                p_key = f"prev_p_{u_num}_{i_idx}"

                if t_key not in st.session_state:
                    st.session_state[t_key] = def_timing
                if p_key not in st.session_state:
                    st.session_state[p_key] = def_prod

                w_key = f"prev_w_{u_num}_{i_idx}"
                if w_key not in st.session_state:
                    # Standaard water bij gel/cafeïne
                    st.session_state[w_key] = "💧 water 150ml" if ("⚡" in st.session_state.get(p_key,"")) else "—"

                water_opties = ["—", "💧 water 100ml", "💧 water 150ml", "💧 water 200ml", "💧 water 250ml", "💧 water 500ml"]

                # Aantal key
                a_key = f"prev_a_{u_num}_{i_idx}"
                if a_key not in st.session_state:
                    st.session_state[a_key] = 1.0

                # Kolommen: timing | product | aantal | + | water | KH | 🗑
                c1, c2, c3, cplus, c4, c5, c6 = st.columns([1.1, 2.2, 0.8, 0.25, 1.8, 0.7, 0.35])
                with c1:
                    t_idx = timing_opties.index(st.session_state[t_key]) if st.session_state[t_key] in timing_opties else 0
                    gekozen_t = st.selectbox("", timing_opties, index=t_idx,
                        key=t_key, label_visibility="collapsed")
                with c2:
                    p_idx = alle_opties.index(st.session_state[p_key]) if st.session_state[p_key] in alle_opties else len(alle_opties)-1
                    gekozen_p = st.selectbox("", alle_opties, index=p_idx,
                        key=p_key, label_visibility="collapsed")
                with c3:
                    gekozen_a = st.number_input("", min_value=0.5, max_value=10.0,
                        value=float(st.session_state[a_key]),
                        step=0.5, key=a_key, label_visibility="collapsed")
                with cplus:
                    st.markdown('<div style="padding:8px 2px;text-align:center;color:#64748b;font-size:0.9rem;">+</div>', unsafe_allow_html=True)
                with c4:
                    w_idx = water_opties.index(st.session_state[w_key]) if st.session_state[w_key] in water_opties else 0
                    gekozen_w = st.selectbox("", water_opties, index=w_idx,
                        key=w_key, label_visibility="collapsed")
                with c5:
                    kh_val = round(kh_map.get(gekozen_p, 0) * gekozen_a)
                    st.markdown(
                        f'<div style="padding:8px 4px;font-size:0.82rem;font-weight:700;' +
                        f'color:{"#f97316" if kh_val > 0 else "#475569"};text-align:center;">' +
                        f'{kh_val}g KH</div>',
                        unsafe_allow_html=True
                    )
                with c6:
                    if st.button("🗑", key=f"prev_del_{u_num}_{i_idx}", help="Verwijder rij"):
                        for j in range(i_idx, n_items - 1):
                            st.session_state[f"prev_t_{u_num}_{j}"] = st.session_state.get(f"prev_t_{u_num}_{j+1}", "20min")
                            st.session_state[f"prev_p_{u_num}_{j}"] = st.session_state.get(f"prev_p_{u_num}_{j+1}", "— leeg —")
                            st.session_state[f"prev_a_{u_num}_{j}"] = st.session_state.get(f"prev_a_{u_num}_{j+1}", 1.0)
                            st.session_state[f"prev_w_{u_num}_{j}"] = st.session_state.get(f"prev_w_{u_num}_{j+1}", "—")
                        st.session_state[n_items_key] = max(0, n_items - 1)
                        st.rerun()
                # Vocht berekening
                vocht_water = 0
                if gekozen_w and gekozen_w != "—":
                    try:
                        vocht_water = int(gekozen_w.split()[-1].replace("ml","")) * gekozen_a
                    except: pass
                vocht_drank = 0
                if "🥤" in gekozen_p:
                    # Lees ml rechtstreeks uit het label: "🥤 Maurten 320 (200ml)"
                    try:
                        import re
                        ml_match = re.search(r'\((\d+)ml\)', gekozen_p)
                        vocht_drank = int(ml_match.group(1)) * gekozen_a if ml_match else 0
                    except: pass
                uur_vocht += round(vocht_water + vocht_drank)
                uur_kh += kh_val

            # Rij toevoegen knop
            ca1, ca2 = st.columns([4, 1])
            with ca2:
                if st.button("➕ Rij", key=f"prev_add_{u_num}", help="Voeg rij toe"):
                    st.session_state[n_items_key] = n_items + 1
                    st.rerun()

            # Avatar bij overschrijding

            # Totaal per uur
            if geen_kh:
                totaal_kleur = "#3b82f6"
                totaal_label = "Geen KH nodig"
            else:
                if uur_kh > cur_max:
                    totaal_kleur = "#ef4444"
                elif uur_kh >= cur_min:
                    totaal_kleur = "#22c55e"
                elif uur_kh >= cur_min * 0.7:
                    totaal_kleur = "#fbbf24"
                else:
                    totaal_kleur = "#ef4444"
                totaal_label = f"{uur_kh}g KH  {'✅' if cur_min <= uur_kh <= cur_max else ('⚠️' if uur_kh > cur_max else '❌')}"

            totaal_kh_race    += uur_kh
            totaal_vocht_race += uur_vocht

            # ── KH balk kleur ─────────────────────────────────────────────────
            if geen_kh:
                kh_pct   = 100
                kh_kleur = "#3b82f6"
            else:
                kh_pct   = min(100, round((uur_kh / cur_max) * 100)) if cur_max > 0 else 0
                kh_over  = uur_kh > cur_max
                if kh_over:              kh_kleur = "#ef4444"
                elif uur_kh >= cur_min:  kh_kleur = "#22c55e"
                elif kh_pct >= 50:       kh_kleur = "#fbbf24"
                elif kh_pct >= 30:       kh_kleur = "#f97316"
                else:                    kh_kleur = "#334155"

            # ── Vocht balk kleur ──────────────────────────────────────────────
            # Laatste uur: vochttarget op basis van resterende minuten
            if is_last:
                _rest = int(totale_min or 0) % 60 if int(totale_min or 0) % 60 != 0 else 60
                vocht_target_uur = round(vocht_uur * (_rest / 60))
            else:
                vocht_target_uur = vocht_uur
            vocht_pct   = min(100, round((uur_vocht / vocht_target_uur) * 100)) if vocht_target_uur > 0 else 0
            vocht_over  = uur_vocht > vocht_target_uur * 1.3
            if vocht_over:          vocht_kleur = "#ef4444"
            elif vocht_pct >= 80:   vocht_kleur = "#22c55e"
            elif vocht_pct >= 50:   vocht_kleur = "#fbbf24"
            else:                   vocht_kleur = "#f97316"

            # Avatar bij KH overschrijding
            if not geen_kh and uur_kh > cur_max:
                st.markdown(
                    '<div style="display:flex;gap:10px;align-items:center;margin:6px 0;' +
                    'background:rgba(239,68,68,0.1);border:1px solid #ef4444;' +
                    'border-radius:10px;padding:8px 12px;">' +
                    f'<img src="{MASCOT_B64}" style="height:36px;width:auto;flex-shrink:0;">' +
                    '<span style="color:#fca5a5;font-size:0.80rem;">' +
                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van dit uur!</span>' +
                    '</div>',
                    unsafe_allow_html=True
                )

            notitie_html = (
                f'<div style="color:#64748b;font-size:0.72rem;font-style:italic;'
                f'padding:4px 0 6px 0;">{notitie}</div>'
            ) if notitie else ""

            st.markdown(
                f'<div style="background:#0f172a;border-radius:0 0 10px 10px;padding:10px 14px 10px 14px;">' +
                notitie_html +
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">' +
                f'<span style="color:#94a3b8;font-size:0.7rem;font-weight:700;width:44px;flex-shrink:0;">KH</span>' +
                f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;">' +
                f'<div style="width:{kh_pct}%;height:100%;background:{kh_kleur};border-radius:4px;"></div></div>' +
                '</div>' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                f'<span style="color:#94a3b8;font-size:0.7rem;font-weight:700;width:44px;flex-shrink:0;">💧</span>' +
                f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;">' +
                f'<div style="width:{vocht_pct}%;height:100%;background:{vocht_kleur};border-radius:4px;"></div></div>' +
                '</div>' +
                f'</div>',
                unsafe_allow_html=True
            )

        # ── Race totaal ───────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:#1e293b;border-radius:12px;padding:14px 18px;'
            f'display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="color:#94a3b8;font-size:0.85rem;font-weight:700;">TOTAAL RACE</span>'
            f'<div style="display:flex;gap:20px;align-items:center;">'
            f'<span style="color:#3b82f6;font-size:0.9rem;font-weight:700;">💧 {totaal_vocht_race}ml vocht</span>'
            f'<span style="color:#f8fafc;font-size:1rem;font-weight:900;">{totaal_kh_race}g KH</span>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Preview resetten", key="rp_reset_preview", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("prev_"):
                    del st.session_state[k]
            st.session_state.pop("rp_preview_leeg", None)
            st.session_state["rp_show_preview"] = False
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="display:flex;gap:14px;align-items:center;' +
            'background:rgba(249,115,22,0.08);border:1px solid #f97316;' +
            'border-radius:12px;padding:14px 16px;margin-bottom:12px;">' +
            f'<img src="{MASCOT_B64}" style="height:60px;width:auto;flex-shrink:0;">' +
            '<span style="color:#f1f5f9;font-size:0.88rem;">' +
            '<b style="font-size:1rem;">Tevreden met je plan?</b> Klik hieronder om je race nutrition rapport te genereren en te downloaden.<br>' +
            '<span style="color:#f97316;font-weight:700;">Let op! Indien je klikt op Genereer rapport kan je niet meer terug en zal je een credit inzetten!</span>' +
            '</span></div>',
            unsafe_allow_html=True
        )
        # ── Credit check ──────────────────────────────────────────────────────
        user_id  = st.session_state.get("current_user", {}).get("id", "")
        from login import get_credits
        credits_actueel = get_credits(user_id) if user_id else 0
        if "current_user" in st.session_state:
            st.session_state.current_user["credits"] = credits_actueel

        # Credits teller tonen
        if credits_actueel > 0:
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #334155;border-radius:8px;
                        padding:8px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
                <span style="color:#94a3b8;font-size:0.82rem;">Beschikbare credits</span>
                <span style="color:#f97316;font-weight:900;font-size:1.1rem;">{credits_actueel}</span>
            </div>
            """, unsafe_allow_html=True)

        # Knop altijd zichtbaar
        if st.button("📄  GENEREER RAPPORT", key="rp_gen", use_container_width=True):
            st.session_state.coach_data["pool"] = pool

            # ── Bewaar preview comments per uur ──────────────────────────────
            _comments = {}
            for _u in range(1, 25):
                _c = st.session_state.get(f"prev_notitie_{_u}", "")
                if _c:
                    _comments[str(_u)] = _c
            st.session_state.coach_data["preview_comments"] = _comments

            # ── Lees de aangepaste preview rijen uit session_state ────────────
            # Zet prev_t_, prev_p_, prev_a_, prev_w_ om naar preview_uren structuur
            _preview_uren = {}
            for _u in range(1, aantal_uren + 1):
                _n = st.session_state.get(f"prev_n_items_{_u}", 0)
                _items = []
                for _i in range(_n):
                    _prod  = st.session_state.get(f"prev_p_{_u}_{_i}", "— leeg —")
                    _tijd  = st.session_state.get(f"prev_t_{_u}_{_i}", "20min")
                    _antal = st.session_state.get(f"prev_a_{_u}_{_i}", 1.0)
                    _water = st.session_state.get(f"prev_w_{_u}_{_i}", "—")
                    _kh    = round(kh_map.get(_prod, 0) * _antal)
                    _emoji = emoji_map.get(_prod, "💧")
                    # Haal productnaam op uit label (zonder emoji prefix)
                    _naam = _prod.split(" ", 1)[1] if " " in _prod and _prod != "— leeg —" else _prod
                    import re as _re
                    _water_ml = 0
                    if _water and _water != "—":
                        _m = _re.search(r'(\d+)ml', _water)
                        if _m:
                            _water_ml = int(_m.group(1)) * _antal
                    elif _emoji == "🥤":
                        _m2 = _re.search(r'\((\d+)ml\)', _prod)
                        if _m2:
                            _water_ml = int(_m2.group(1)) * _antal

                    if _prod != "— leeg —":
                        # Normaal product item
                        _items.append({
                            "min":      _tijd,
                            "emoji":    _emoji,
                            "naam":     _naam,
                            "kh":       _kh,
                            "water_ml": round(_water_ml),
                            "antal":    _antal,
                        })
                    elif _water_ml > 0:
                        # Leeg product maar wel water gekozen → sla op als water item
                        _items.append({
                            "min":      _tijd,
                            "emoji":    "💧",
                            "naam":     "Water",
                            "kh":       0,
                            "water_ml": round(_water_ml),
                        })
                _preview_uren[str(_u)] = _items
            st.session_state.coach_data["preview_uren"] = _preview_uren

            with st.spinner("Rapport wordt gegenereerd..."):
                try:
                    gebruiker_naam = st.session_state.get("current_user", {}).get("name", "Atleet")
                    data_voor_html = dict(st.session_state.coach_data)
                    data_voor_html["logo_b64"]  = st.session_state.get("coach_logo_b64", "")
                    data_voor_html["logo_mime"] = st.session_state.get("coach_logo_mime", "image/png")
                    html_str = _genereer_html(data_voor_html, gebruiker_naam)
                    # Sla rapport op — credit aftrek gebeurt in rapport module
                    st.session_state["rapport_html"] = html_str
                    st.session_state.pop("rapport_pdf", None)
                    st.session_state["module"] = "rapport"
                    st.rerun()
                except Exception as e:
                    st.error(f"Fout bij genereren rapport: {e}")




def _portie_omschrijving(naam: str, portie: str, aantal: int) -> str:
    """Maak een leesbare portie omschrijving: '3 sneden wit brood'"""
    p = portie.lower()
    # Bepaal de maat-eenheid
    if "snede" in p:
        eenheid = "snede" if aantal == 1 else "sneden"
    elif "stuk" in p:
        eenheid = "stuk" if aantal == 1 else "stuks"
    elif "kom" in p:
        eenheid = "kom" if aantal == 1 else "kommen"
    elif "glas" in p:
        eenheid = "glas" if aantal == 1 else "glazen"
    elif "potje" in p:
        eenheid = "potje" if aantal == 1 else "potjes"
    elif "eetlpl" in p or "eetlepel" in p:
        eenheid = "eetlepel" if aantal == 1 else "eetlepels"
    elif "koffielepel" in p:
        eenheid = "koffielepel" if aantal == 1 else "koffielepels"
    elif "schaaltje" in p:
        eenheid = "schaaltje" if aantal == 1 else "schaaltjes"
    elif "reep" in p:
        eenheid = "reep" if aantal == 1 else "repen"
    elif "tas" in p:
        eenheid = "tas" if aantal == 1 else "tassen"
    elif "bidon" in p or "500ml" in p or "ml" in p:
        eenheid = "bidon" if aantal == 1 else "bidons"
    elif "bord" in p:
        eenheid = "bord" if aantal == 1 else "borden"
    else:
        eenheid = "portie" if aantal == 1 else "porties"
    return f"{aantal} {eenheid} {naam.lower()}"


def _bereken_raceplan(data: dict) -> list:
    """Bereken het uur-per-uur raceplan."""
    import math
    from datetime import datetime, timedelta

    pool        = data.get("pool", {})

    def _pool_item(key):
        """Haal eerste item uit pool — werkt voor zowel dict als lijst."""
        val = pool.get(key, {})
        if isinstance(val, list) and val:
            return val[0]
        if isinstance(val, dict) and val:
            return val
        return {}
    totale_min  = int(int(data.get("totale_min", 180) or 180) or 180)
    min_kh      = data.get("min_kh", 60)
    max_kh      = data.get("max_kh", 90)
    temp        = int(int(data.get("temp", 18) or 18) or 18)
    hoogte      = int(int(data.get("hoogte", 0) or 0) or 0)
    vochtigheid = int(int(data.get("vochtigheid", 50) or 50) or 50)
    start_str   = data.get("start_time", "09:00")
    sport       = data.get("sport", "Fietsen")
    start_dt    = datetime.strptime(start_str, "%H:%M")
    aantal_uren = math.ceil(int(totale_min or 0) / 60)

    geen_kh_drempel = {"Fietsen": 75, "Lopen": 60, "Duatlon": 75, "Crossduatlon": 90}
    geen_kh = int(totale_min or 0) < geen_kh_drempel.get(sport, 75)

    basis_vocht = 800 if int(temp or 18) > 25 else (600 if int(temp or 18) > 15 else 500)
    f_factor    = (int(hoogte or 0) / 1000) * 0.15 + (0.15 if int(vochtigheid or 0) > 70 else 0)
    vocht_per_m = round(((basis_vocht * (1 + f_factor)) / 3) / 10) * 10

    uren = []
    vast_idx   = 0
    cafe_strat = data.get("cafeine_strategie", "")

    for u in range(aantal_uren):
        is_last  = (u == aantal_uren - 1)
        if is_last:
            # Schaal KH target op basis van resterende minuten
            rest_min = int(totale_min or 0) % 60 if int(totale_min or 0) % 60 != 0 else 60
            if rest_min < 15:
                cur_min, cur_max = 0, 0
            elif rest_min < 31:
                cur_min, cur_max = 15, 20
            elif rest_min < 46:
                cur_min, cur_max = 30, 40
            else:
                # > 45 min resterend → 60% van normaal target
                cur_min = round(min_kh * 0.6)
                cur_max = round(max_kh * 0.6)
        else:
            cur_min = min_kh
            cur_max = max_kh
        uur_kh   = 0
        uur_start = start_dt + timedelta(hours=u)
        items    = []

        if geen_kh:
            items.append({"min": "20min", "emoji": "💧", "naam": "Water / mondspoeling", "kh": 0, "water_ml": vocht_per_m})
            items.append({"min": "40min", "emoji": "💧", "naam": "Water / mondspoeling", "kh": 0, "water_ml": vocht_per_m})
        else:
            if pool.get("drank"):
                d = _pool_item("drank")
                naam_d = d.get("naam", d.get("name", "Sportdrank"))
                kh_per_m = round((d["kh"] / 500) * vocht_per_m)
                for label in ["20min", "40min", "60min"]:
                    items.append({"min": label, "emoji": "🥤",
                                  "naam": f"{naam_d} ({vocht_per_m}ml)",
                                  "kh": kh_per_m, "water_ml": vocht_per_m})
                    uur_kh += kh_per_m

            if u == 1 and not is_last and pool.get("cafe") and "uur 2" in cafe_strat:
                c = _pool_item("cafe")
                naam_c = c.get("naam", c.get("name", "Cafeïne gel"))
                items.append({"min": "20min", "emoji": "⚡", "naam": naam_c, "kh": c["kh"]})
                uur_kh += c["kh"]

            if "verspreid" in cafe_strat and not is_last and pool.get("cafe") and u % 2 == 1:
                c = _pool_item("cafe")
                naam_c = c.get("naam", c.get("name", "Cafeïne gel"))
                items.append({"min": "40min", "emoji": "⚡", "naam": naam_c, "kh": c["kh"]})
                uur_kh += c["kh"]

            if pool.get("vast") and uur_kh < cur_min:
                item = pool["vast"][vast_idx % len(pool["vast"])]
                naam_v = item.get("naam", item.get("name", "Vast voedsel"))
                items.append({"min": "30min", "emoji": "🍌", "naam": naam_v, "kh": item["kh"]})
                uur_kh += item["kh"]
                vast_idx += 1

            if pool.get("gels") and uur_kh < cur_min:
                g = _pool_item("gels")
                naam_g = g.get("naam", g.get("name", "Gel"))
                items.append({"min": "45min", "emoji": "⚡", "naam": naam_g, "kh": g["kh"]})
                uur_kh += g["kh"]

            if is_last:
                rest_min_vocht = int(totale_min or 0) % 60 if int(totale_min or 0) % 60 != 0 else 60
                vocht_last = max(round(vocht_per_m * (rest_min_vocht / 60) / 10) * 10, 100)
                if geen_kh or rest_min_vocht < 15:
                    # Geen KH, enkel water
                    items = [{"min": "10min", "emoji": "💧", "naam": "Water / spoelen",
                              "kh": 0, "water_ml": vocht_last}]
                elif rest_min_vocht < 31:
                    # 15-30 min: 1 moment vloeibaar
                    items = [{"min": "15min", "emoji": items[0]["emoji"] if items else "💧",
                              "naam": items[0]["naam"] if items else "Water",
                              "kh": items[0]["kh"] if items else 0,
                              "water_ml": vocht_last}]
                elif rest_min_vocht < 46:
                    # 31-45 min: 2 momenten vloeibaar
                    items = [i for i in items if i["min"] == "20min"]
                    items = [{**i, "water_ml": vocht_last} for i in items]
                    items.append({"min": "35min", "emoji": "💧", "naam": "Water / spoelen",
                                  "kh": 0, "water_ml": vocht_last})
                else:
                    # >45 min: houd 20min item, voeg water toe op 40min
                    items = [i for i in items if i["min"] == "20min"]
                    items = [{**i, "water_ml": vocht_last} for i in items]
                    items.append({"min": "40min", "emoji": "💧", "naam": "Water / spoelen",
                                  "kh": 0, "water_ml": vocht_last})

        uren.append({
            "uur": u + 1, "uur_start": uur_start.strftime("%H:%M"),
            "items": items, "uur_kh": round(uur_kh),
            "min_kh": cur_min, "max_kh": cur_max,
            "is_last": is_last, "geen_kh": geen_kh,
        })

    return uren, vocht_per_m










# ── Dynamische recepten (gedeeld door HTML en PDF) ─────────────────────────
RECEPTEN = {
    # Pasta
    "Pasta (hoofdmaaltijd)": [
        ("Pasta bolognese light",
         "300g witte pasta · 150g mager rundergehakt · 200ml passata · ui · weinig olijfolie.<br>"
         "Kook pasta al dente. Fruit ui, voeg gehakt en passata toe, 15 min sudderen. Laag in vezels en vetten."),
        ("Pasta met tonijn en tomaat",
         "300g witte pasta · 1 blik tonijn op water · 200ml passata · knoflook · peterselie.<br>"
         "Kook pasta al dente. Meng met tonijn en passata. Laag in vetten, hoog in KH en eiwitten."),
        ("Pasta met kipfilet en lichte roomsaus",
         "300g witte pasta · 150g kipfilet · 100ml magere room · knoflook · bieslook.<br>"
         "Bak kip 8 min, blus met room. Serveer over pasta. Licht en verteerbaar."),
    ],
    "Pasta (bijgerecht)": [
        ("Pasta als bijgerecht met kip",
         "150g witte pasta · 150g kipfilet · 100g gestoofde groenten · scheutje olijfolie.<br>"
         "Kook pasta, combineer met kip en groenten. Licht en verteerbaar."),
    ],
    # Rijst
    "Rijst (hoofdmaaltijd)": [
        ("Rijst met zalm en gestoomde wortels",
         "250g witte rijst · 150g zalm · 150g wortels.<br>"
         "Stoom wortels 12 min. Bak zalm 4 min per kant. Licht verteerbaar, hoog in KH en eiwitten."),
        ("Rijst met kip en courgette",
         "250g witte rijst · 150g kipfilet · 100g courgette · knoflook · beetje olijfolie.<br>"
         "Bak kip 8 min, stoom courgette 5 min. Serveer op rijst. Ideaal pre-race avondmaal."),
        ("Rijst met garnalen en lichte saus",
         "250g witte rijst · 150g garnalen · 100ml magere room · ui · peterselie.<br>"
         "Fruit ui, voeg garnalen 3 min, blus met room. Serveer op rijst. Laag in vetten."),
    ],
    "Rijst (bijgerecht)": [
        ("Rijst als bijgerecht met vis",
         "150g witte rijst · 150g magere vis (kabeljauw, tilapia) · gestoofde groenten.<br>"
         "Stoom vis 10 min, combineer met rijst en groenten. Laag in vetten, hoog in eiwitten."),
    ],
    # Aardappelen
    "Aardappelen gekookt": [
        ("Gekookte aardappelen met kipfilet",
         "250g gekookte aardappelen · 150g kipfilet · 100g gestoofde wortels · beetje olijfolie.<br>"
         "Kook aardappelen 20 min. Bak kip 8 min. Vermijd boter of zware sauzen."),
        ("Aardappelpuree light met vis",
         "250g aardappelen · 150g kabeljauw · scheut magere melk · peterselie.<br>"
         "Stamp aardappelen met melk, geen boter. Stoom vis 10 min. Licht en verteerbaar."),
    ],
    # Brood — avondmaal is ongebruikelijk maar sommige atleten kiezen hiervoor
    "Wit brood": [
        ("Uitgebreide boterham met eiwitrijke beleg",
         "4-6 sneden wit brood · 100g kalkoenfilet of kipfilet · 2 eieren hardgekookt · tomaat · komkommer.<br>"
         "Leg beleg royaal op. Eet rustig en kauw goed. Drink 1-2 glazen water erbij. "
         "Voeg eventueel wat rijstwafels toe voor extra KH."),
    ],
    "Bruin brood": [
        ("Bruine boterham avondmaal",
         "4 sneden bruin brood · magere kaas of kalkoen · tomaat · komkommer.<br>"
         "Licht en verteerbaar. Let op: bruin brood bevat meer vezels — eet liever wit brood de dag voor de race."),
    ],
    "Volkorenbrood": [
        ("Volkorenbrood — tip voor de dag voor de race",
         "3-4 sneden volkorenbrood · magere kaas of kipfilet · groenten naar keuze.<br>"
         "⚠️ Volkorenbrood bevat veel vezels. Overweeg te wisselen naar wit brood op de dag voor de race."),
    ],
    # Ontbijtproducten als avondmaal (sommige atleten doen dit)
    "Havermout": [
        ("Overnight oats als avondmaal",
         "80g havermout · 200ml magere melk of plantaardige melk · 1 banaan · 1 eetlepel honing.<br>"
         "Meng havermout met melk, laat 30 min staan. Voeg banaan en honing toe. "
         "Verrassend goed als licht avondmaal — laag in vetten, hoog in KH."),
        ("Warme havermoutpap met fruit",
         "80g havermout · 250ml melk · 1 banaan · rozijnen · snufje kaneel.<br>"
         "Kook havermout 5 min in melk. Voeg fruit toe. Licht, verteerbaar en hoog in KH."),
    ],
    "Ontbijtgranen": [
        ("Ontbijtgranen met melk en fruit",
         "60g cornflakes of ontbijtgranen · 200ml melk · 1 banaan · handvol rozijnen.<br>"
         "Meng en serveer koud. Snel klaar, licht verteerbaar en hoog in snelle KH. "
         "Kies voor cornflakes of gewone ontbijtgranen — vermijd muesli of granola voor slaapgaan."),
    ],
    "Muesli": [
        ("Muesli met yoghurt en honing",
         "60g muesli · 150g magere yoghurt · 1 banaan · 1 eetlepel honing.<br>"
         "Meng muesli met yoghurt. ⚠️ Muesli bevat meer vezels dan cornflakes — "
         "eet dit liever 2 dagen voor de race, niet de dag ervoor."),
    ],
    "Granola (krokant)": [
        ("Granola met melk en banaan",
         "50g granola · 200ml melk · 1 banaan · 1 koffielepel honing.<br>"
         "⚠️ Granola is vetrijker dan andere ontbijtgranen. Beperk de portie en "
         "kies dit liever 2 dagen voor de race."),
    ],
}
TUSSENDOORTJE_DAG1 = [
    ("Rijstwafels met honing en banaan",
     "3-4 rijstwafels · 2 koffielepels honing · 1 banaan in plakjes.<br>"
     "Beleg rijstwafels met honing en banaan. Snel klaar, licht verteerbaar en hoog in snelle KH. "
     "Ideaal als extra tussendoortje de dag voor de race."),
    ("Energieballetjes van dadels en havermout",
     "10 dadels · 50g havermout · 1 eetlepel pindakaas · 1 eetlepel honing · snufje kaneel.<br>"
     "Mix dadels fijn, meng met havermout, pindakaas en honing. Rol tot balletjes. "
     "30 min in koelkast. Hoog in KH en gemakkelijk mee te nemen."),
]
TUSSENDOORTJE_DAG2 = [
    ("Banaan met honing en granola",
     "2 bananen · 1 eetlepel honing · 2 eetlepels granola.<br>"
     "Snijd bananen, druppel honing erover, bestrooi met granola. "
     "Snelle KH voor de laatste avond voor de race. Eet 2-3 uur voor slaapgaan."),
    ("Appelmoes met rijstwafels",
     "1 schaaltje appelmoes (150g) · 4 rijstwafels · 1 koffielepel honing.<br>"
     "Serveer appelmoes als dip bij rijstwafels. Licht, verteerbaar en aangenaam zoet. "
     "Geen vezels, geen vetten — perfect als avondsnack de dag voor de race."),
]

STANDAARD_RECEPT_DAG1 = ("Pasta bolognese light",
    "300g witte pasta · 150g mager rundergehakt · 200ml passata · ui · weinig olijfolie.<br>"
    "Kook pasta al dente. Fruit ui, voeg gehakt en passata toe, 15 min sudderen. Laag in vezels en vetten.")
STANDAARD_RECEPT_DAG2 = ("Rijst met zalm en gestoomde wortels",
    "250g witte rijst · 150g zalm · 150g wortels.<br>"
    "Stoom wortels 12 min. Bak zalm 4 min per kant. Licht verteerbaar, hoog in KH en eiwitten.")

CL_KH_GEWICHT = {
    "Pasta (hoofdmaaltijd)":75,"Pasta (bijgerecht)":37,
    "Rijst (hoofdmaaltijd)":81,"Rijst (bijgerecht)":42,
    "Aardappelen gekookt":30,"Wit brood":17,"Bruin brood":16,
    "Volkorenbrood":14,"Havermout":27,"Ontbijtgranen":25,
    "Muesli":30,"Granola (krokant)":26,
}

def zoek_hoofd_product(dag_num, waarden, maaltijdmomenten):
    """Zoek het dominante KH-product over een lijst van maaltijdmomenten.
    Enkel producten die in RECEPTEN staan tellen mee (standaard producten).
    Eigen producten worden genegeerd — die triggeren de cascade naar volgend moment.
    Geeft (product, maaltijdmoment) terug of (None, None) als niets gevonden."""
    for moment in maaltijdmomenten:
        moment_kh = {}
        for prod in RECEPTEN.keys():
            val = waarden.get(f"cl_d{dag_num}_{moment}_{prod}", 0)
            if val and val > 0:
                moment_kh[prod] = val * CL_KH_GEWICHT.get(prod, 10)
        if moment_kh:
            hoofd = max(moment_kh, key=moment_kh.get)
            return hoofd, moment
    return None, None

def detecteer_recept(dag_num, waarden, standaard):
    """Cascade: Avondmaal → Lunch → Ontbijt → Standaard recept.
    Eigen producten worden genegeerd en triggeren de cascade naar het volgende moment."""
    cascade = ["Avondmaal", "Lunch", "Ontbijt"]
    hoofd, gevonden_moment = zoek_hoofd_product(dag_num, waarden, cascade)

    if hoofd is None:
        # Alles leeg of enkel eigen producten → standaard
        return standaard, None

    recepten = RECEPTEN.get(hoofd, [])
    if not recepten:
        return standaard, None

    # Kies recept op basis van dag_num (dag 1 → recept 0, dag 2 → recept 1, etc.)
    recept = recepten[dag_num % len(recepten)]

    return recept, gevonden_moment

def _genereer_pdf(data: dict, gebruiker_naam: str) -> bytes:
    """Volledig PDF rapport: info + carboloading + racedag + uur-per-uur + snelkaart."""
    import io, math, base64
    from datetime import datetime, timedelta
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    KeepTogether, PageBreak, Image)
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=1.6*cm, leftMargin=1.6*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm)

    ORANJE  = colors.HexColor("#f97316")
    DONKER  = colors.HexColor("#0f172a")
    MIDDEL  = colors.HexColor("#1e293b")
    BLAUW   = colors.HexColor("#3b82f6")
    GRIJS   = colors.HexColor("#64748b")
    WIT     = colors.white
    LGRIJS  = colors.HexColor("#f1f5f9")
    GROEN   = colors.HexColor("#22c55e")
    GEEL    = colors.HexColor("#fbbf24")
    ROOD    = colors.HexColor("#ef4444")
    LORANJE = colors.HexColor("#fff7ed")

    W, H  = A4
    breed = W - 3.2*cm

    def S(naam, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=DONKER, leading=13)
        base.update(kw)
        return ParagraphStyle(naam, **base)

    s_titel  = S("TT", fontSize=18, fontName="Helvetica-Bold", textColor=WIT,
                 alignment=TA_CENTER, leading=24)
    s_sub    = S("ST", fontSize=9.5, textColor=colors.HexColor("#fb923c"), alignment=TA_CENTER)
    s_sectie = S("SE", fontSize=11, fontName="Helvetica-Bold", textColor=ORANJE,
                 leading=16, spaceBefore=8, spaceAfter=3)
    s_label  = S("LA", fontSize=7.5, fontName="Helvetica-Bold", textColor=GRIJS, leading=11)
    s_waarde = S("WA", fontSize=10, fontName="Helvetica-Bold", textColor=DONKER, leading=14)
    s_kop    = S("KW", fontSize=8.5, fontName="Helvetica-Bold", textColor=WIT, leading=12)
    s_body   = S("BO", fontSize=8.5, textColor=colors.HexColor("#334155"), leading=12)
    s_tip    = S("TI", fontSize=8, textColor=DONKER, leading=12, leftIndent=6)
    s_footer = S("FO", fontSize=7, textColor=GRIJS, alignment=TA_CENTER, leading=10)
    s_uur_kop = S("UK", fontSize=9, fontName="Helvetica-Bold", textColor=WIT, leading=13)

    story = []

    # ── Logo laden ──────────────────────────────────────────────────────────
    import base64
    from io import BytesIO
    logo_b64   = data.get("logo_b64", "")
    logo_mime  = data.get("logo_mime", "image/png")
    logo_img   = None
    if logo_b64:
        try:
            from reportlab.lib.utils import ImageReader
            logo_bytes = base64.b64decode(logo_b64)
            logo_img   = ImageReader(BytesIO(logo_bytes))
        except Exception:
            logo_img = None

    def maak_header(titel_tekst, subtitel_tekst=""):
        """Witte professionele header — logo altijd zichtbaar."""
        WIT      = colors.HexColor("#ffffff")
        DONKER_T = colors.HexColor("#0f172a")
        GRIJS_T  = colors.HexColor("#64748b")
        ORANJE_L = colors.HexColor("#f97316")
        LOGO_B   = 2.5 * cm
        TEXT_B   = breed - LOGO_B - 0.3*cm if logo_img else breed

        # Oranje accentlijn + titel in donkere tekst
        hdr_tekst = (
            f'<font color="#0f172a"><b>{titel_tekst}</b></font>'
            + (f'<br/><font size="8" color="#64748b">{subtitel_tekst}</font>'
               if subtitel_tekst else "")
        )
        tekst_p = Paragraph(hdr_tekst, S("HDR_WIT", fontSize=13,
                                          fontName="Helvetica-Bold",
                                          textColor=DONKER_T, leading=16))

        if logo_img:
            from reportlab.platypus import Image as RLImage
            try:
                logo_p = RLImage(BytesIO(base64.b64decode(logo_b64)),
                                 width=LOGO_B, height=1.4*cm, kind="proportional")
            except Exception:
                logo_p = Paragraph("", S("E", fontSize=8))
            hdr_data = [[tekst_p, logo_p]]
            col_w    = [TEXT_B, LOGO_B]
        else:
            hdr_data = [[tekst_p]]
            col_w    = [breed]

        hdr_t = Table(hdr_data, colWidths=col_w, rowHeights=[1.8*cm])
        hdr_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), WIT),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING",   (0,0), (0,0),   12),
            ("RIGHTPADDING",  (0,0), (0,0),   8),
            ("LEFTPADDING",   (1,0), (1,0),   4),
            ("RIGHTPADDING",  (1,0), (1,0),   8),
        ]))

        # Oranje accentlijn onderaan header
        accent = Table([[""]],
                       colWidths=[breed],
                       rowHeights=[3])
        accent.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), ORANJE_L),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ]))
        return [hdr_t, accent, Spacer(1, 8)]


    atleet         = data.get("atleet_naam", gebruiker_naam)
    wedstrijd_naam = data.get("wedstrijd_naam", "")
    sport          = data.get("sport", "Fietsen")
    niveau         = data.get("niveau", "—")
    gewicht        = int(data.get("gewicht", 70) or 70)
    datum          = data.get("wedstrijd_datum", "—")
    start          = data.get("start_time", "—")
    eind           = data.get("eind_time", "—")

    for blok in maak_header("RACE NUTRITION PLAN", wedstrijd_naam.upper()):
        story.append(blok)
    story.append(Spacer(1, 10))

    # Atleet & wedstrijd
    story.append(Paragraph("ATLEET & WEDSTRIJD", s_sectie))
    story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))
    totmin   = int(int(data.get("totale_min", 0) or 0) or 0)
    duur_str = f"{int(totmin or 0) // 60}u{int(totmin or 0) % 60:02d}m" if totmin else "—"
    temp     = data.get("temp", "—")
    vocht    = data.get("vochtigheid", "—")
    hoogte   = data.get("hoogte", "—")
    ervaring = data.get("ervaring", "—")

    info_rows = [
        [Paragraph("NAAM ATLEET",  s_label), Paragraph(atleet,  s_waarde),
         Paragraph("DISCIPLINE",   s_label), Paragraph(sport,   s_waarde)],
        [Paragraph("GEWICHT",      s_label), Paragraph(f"{gewicht} kg", s_waarde),
         Paragraph("SPORTNIVEAU",  s_label), Paragraph(niveau,  s_waarde)],
        [Paragraph("DATUM",        s_label), Paragraph(str(datum), s_waarde),
         Paragraph("START / EIND", s_label), Paragraph(f"{start} — {eind}", s_waarde)],
        [Paragraph("DUUR",         s_label), Paragraph(duur_str, s_waarde),
         Paragraph("TEMP / VOCHTIGHEID", s_label), Paragraph(f"{temp}°C  |  {vocht}%", s_waarde)],
        [Paragraph("HOOGTE",       s_label), Paragraph(f"{hoogte} m", s_waarde),
         Paragraph("ERVARING WEDSTRIJDVOEDING", s_label), Paragraph(ervaring, s_waarde)],
    ]
    it = Table(info_rows, colWidths=[breed*0.18, breed*0.32, breed*0.22, breed*0.28])
    it.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LGRIJS,WIT,LGRIJS,WIT,LGRIJS]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
    ]))
    story.append(it)
    story.append(Spacer(1, 10))

    # ── Carboloading ──────────────────────────────────────────────────────────
    dag_target = data.get("dag_target", 0)
    cl_data    = data.get("carboloading", {})
    cl_waarden = data.get("cl_waarden", {})

    story.append(Paragraph("CARBOLOADING — LAATSTE 48 UUR", s_sectie))
    story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))

    CL_KH_MAP = {
        "Wit brood":17,"Bruin brood":16,"Volkorenbrood":14,"Havermout":27,
        "Ontbijtgranen":25,"Muesli":30,"Granola (krokant)":26,
        "Melk (dierlijk)":9,"Plantaardige melk":9,"Banaan":30,"Appel":15,
        "Peer":19,"Kiwi":11,"Yoghurt natuur":6,"Plattekaas":4,
        "Confituur":3,"Honing":4,"Chocopasta":3,"Koffie met suiker":5,
        "Vruchtensap sinaas":20,"Sportdrank":35,"Rijstwafels":7,
        "Energiereep":40,"Rozijnen":15,"Dadels gedroogd":6,
        "Muesli/granenreep":26,"Speculoos":5,"Snoep/winegums":26,
        "Appelmoes":27,"Pannenkoek":27,
        "Pasta (hoofdmaaltijd)":75,"Pasta (bijgerecht)":37,
        "Rijst (hoofdmaaltijd)":81,"Rijst (bijgerecht)":42,
        "Aardappelen gekookt":30,"Groentenmix rauw":5,"Groentenmix warm":8,
    }
    CL_PORTIE_MAP = {
        "Wit brood":"snede","Bruin brood":"snede","Volkorenbrood":"snede",
        "Havermout":"kom","Ontbijtgranen":"kom","Muesli":"kom",
        "Granola (krokant)":"kom","Melk (dierlijk)":"glas",
        "Plantaardige melk":"glas","Banaan":"stuk","Appel":"stuk",
        "Peer":"stuk","Kiwi":"stuk","Yoghurt natuur":"potje",
        "Plattekaas":"eetlepel","Confituur":"koffielepel","Honing":"koffielepel",
        "Chocopasta":"koffielepel","Koffie met suiker":"tas","Vruchtensap sinaas":"glas",
        "Sportdrank":"bidon","Rijstwafels":"stuk","Energiereep":"reep",
        "Rozijnen":"handje","Dadels gedroogd":"stuk","Muesli/granenreep":"reep",
        "Speculoos":"stuk","Snoep/winegums":"zakje","Appelmoes":"schaaltje",
        "Pannenkoek":"stuk",
        "Pasta (hoofdmaaltijd)":"bord","Pasta (bijgerecht)":"bord",
        "Rijst (hoofdmaaltijd)":"bord","Rijst (bijgerecht)":"bord",
        "Aardappelen gekookt":"bord","Groentenmix rauw":"bord","Groentenmix warm":"bord",
    }
    MAALTIJDEN = ["Ontbijt","Tussendoor VM","Lunch","Tussendoor NM","Avondmaal","Avond snack"]
    MAALTIJD_PCT = {"Ontbijt":0.25,"Tussendoor VM":0.083,"Lunch":0.25,
                    "Tussendoor NM":0.083,"Avondmaal":0.25,"Avond snack":0.083}

    for dag_num in [1, 2]:
        dag_label = f"DAG {dag_num} — {'2 dagen voor race' if dag_num==1 else '1 dag voor race'}"
        dag_vals  = cl_data.get(f"dag{dag_num}", {})
        totaal    = dag_vals.get("totaal", 0)
        target    = dag_vals.get("target", dag_target)
        pct       = dag_vals.get("pct", 0)
        bar_c     = GROEN if pct >= 90 else (GEEL if pct >= 70 else ROOD)

        dag_hdr = Table([[
            Paragraph(dag_label, S("DH", fontSize=9, fontName="Helvetica-Bold",
                                   textColor=WIT, leading=13)),
        ]], colWidths=[breed])
        dag_hdr.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),MIDDEL),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ]))
        story.append(dag_hdr)

        # Per maaltijdmoment
        ml_rows = [[Paragraph("MAALTIJDMOMENT", s_kop),
                    Paragraph("GEKOZEN VOEDINGSMIDDELEN", s_kop),
                    Paragraph("KH", s_kop)]]
        for m_naam in MAALTIJDEN:
            items_txt = []
            m_kh_tot  = 0
            for prod_naam, kh_pp in CL_KH_MAP.items():
                key = f"cl_d{dag_num}_{m_naam}_{prod_naam}"
                val = cl_waarden.get(key, 0)
                if val and val > 0:
                    eenheid = CL_PORTIE_MAP.get(prod_naam, "portie")
                    n = int(val) if val == int(val) else val
                    mv = "meervoud" if n > 1 else "enkelvoud"
                    _MV = {"snede":"sneden","kom":"kommen","glas":"glazen","stuk":"stuks",
                           "potje":"potjes","eetlepel":"eetlepels","koffielepel":"koffielepels",
                           "zakje":"zakjes","bord":"borden","portie":"porties",
                           "schaaltje":"schaaltjes","reep":"repen","tas":"tassen"}
                    e_mv = _MV.get(eenheid, eenheid + "s") if n > 1 else eenheid
                    items_txt.append(f"{n} {e_mv} {prod_naam.lower()}")
                    m_kh_tot += val * kh_pp
            if items_txt:
                m_target = round(dag_target * MAALTIJD_PCT.get(m_naam, 0.15))
                ml_rows.append([
                    Paragraph(m_naam, s_body),
                    Paragraph(", ".join(items_txt), s_body),
                    Paragraph(f"{round(m_kh_tot)}g", S("MK", fontSize=8,
                        fontName="Helvetica-Bold", textColor=ORANJE, leading=12)),
                ])
        if len(ml_rows) > 1:
            ml_t = Table(ml_rows, colWidths=[breed*0.22, breed*0.63, breed*0.15])
            ml_t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),DONKER),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
                ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ]))
            story.append(ml_t)

        # Progressiebalk per dag
        pct_balk  = min(100, round((totaal / target) * 100)) if target > 0 else 0
        over_balk = totaal > target
        if over_balk:            balk_c = ROOD
        elif pct_balk >= 80:     balk_c = GROEN
        elif pct_balk >= 50:     balk_c = GEEL
        else:                    balk_c = ORANJE

        vul  = max(0, min(pct_balk, 100)) / 100
        rest = 1 - vul
        balk = Table([["", ""]], colWidths=[
            breed * vul  if vul  > 0.01 else 0.5,
            breed * rest if rest > 0.01 else 0.5,
        ])
        balk.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,0), balk_c),
            ("BACKGROUND", (1,0), (1,0), colors.HexColor("#1e293b")),
            ("ROWHEIGHT",  (0,0), (-1,-1), 0.22*cm),
            ("TOPPADDING",    (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ]))
        story.append(balk)
        story.append(Spacer(1, 5))

    # Tips + avondmaal suggestie
    cl_tips = [
        "Kies licht verteerbare producten: pasta, rijst, wit brood, banaan.",
        "Beperk vezels & vetten en rauwe groenten in de 24u voor de race.",
        "Drink voldoende — kleine slokjes gespreid over de dag.",
        "Verdeel je koolhydraten over 5–6 momenten per dag.",
    ]
    tip_rows = [[Paragraph("TIPS CARBOLOADING", s_kop)]]
    for tip in cl_tips:
        tip_rows.append([Paragraph(f"  →  {tip}", s_tip)])
    tip_t = Table(tip_rows, colWidths=[breed])
    tip_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),MIDDEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e2e8f0")),
    ]))
    story.append(tip_t)
    story.append(Spacer(1, 5))

    # Detecteer dynamische recepten per dag
    (rec1_titel, rec1_tekst), moment1 = detecteer_recept(1, cl_waarden, STANDAARD_RECEPT_DAG1)
    (rec2_titel, rec2_tekst), moment2 = detecteer_recept(2, cl_waarden, STANDAARD_RECEPT_DAG2)

    def _maak_rec_label(dag_num, moment):
        if moment is None:
            return f"Suggestie Tussendoortjes — Dag {dag_num}"
        return f"DAG {dag_num} — {moment} Suggestie + Recept"

    def _maak_rec_items(dag_num, titel, tekst, moment):
        if moment is None:
            return TUSSENDOORTJE_DAG1 if dag_num == 1 else TUSSENDOORTJE_DAG2
        return [(f"{titel} (dag {dag_num} voor race)", tekst)]

    rec_rows = []
    for dag_num, rec_titel, rec_tekst, moment in [
        (1, rec1_titel, rec1_tekst, moment1),
        (2, rec2_titel, rec2_tekst, moment2),
    ]:
        sectie_lbl = _maak_rec_label(dag_num, moment)
        rec_rows.append([Paragraph(sectie_lbl.upper(), s_kop)])
        for t, r in _maak_rec_items(dag_num, rec_titel, rec_tekst, moment):
            # Verwijder HTML tags voor ReportLab
            r_pdf = r.replace("<br>", " ").replace("<br/>", " ").replace("&", "&amp;")
            rec_rows.append([Paragraph(f"  ✦  {t}", S("RT", fontSize=8, fontName="Helvetica-Bold",
                                                         textColor=colors.HexColor("#1e40af"), leading=11))])
            rec_rows.append([Paragraph(f"      {r_pdf}", S("RB", fontSize=7.5,
                                                          textColor=colors.HexColor("#334155"),
                                                          leading=11, leftIndent=12))])
    rec_t = Table(rec_rows, colWidths=[breed])
    rec_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),colors.HexColor("#1e3a5f")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#eff6ff"),WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#bfdbfe")),
        ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#dbeafe")),
    ]))
    story.append(rec_t)
    story.append(Spacer(1, 10))

    # ── Laatste maaltijd ──────────────────────────────────────────────────────
    maaltijd_mom = data.get("maaltijd_moment", "Ontbijt")
    ont_timing   = data.get("ontbijt_timing", "—")
    ont_tijd     = data.get("ontbijt_tijd", "—")
    ont_kh       = data.get("ontbijt_kh", 0)
    rd_waarden   = data.get("rd_waarden", {})
    temp_val     = int(data.get("temp", 18) or 18)

    if temp_val > 25:   vocht_advies = "600–800ml in de 2–3u voor de start (warm weer)"
    elif temp_val > 15: vocht_advies = "400–600ml in de 2–3u voor de start"
    else:               vocht_advies = "300–500ml in de 2–3u voor de start (koel weer)"

    story.append(Paragraph(f"LAATSTE MAALTIJD — {maaltijd_mom.upper()}", s_sectie))
    story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))

    rd_info = Table([
        [Paragraph("TIMING", s_label), Paragraph(ont_timing, s_waarde),
         Paragraph("MAALTIJD OM", s_label), Paragraph(ont_tijd, s_waarde)],
        [Paragraph("TOTAAL KH", s_label), Paragraph(f"{ont_kh}g", s_waarde),
         Paragraph("AANBEVOLEN VOCHT", s_label), Paragraph(vocht_advies, s_body)],
    ], colWidths=[breed*0.18, breed*0.32, breed*0.22, breed*0.28])
    rd_info.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LGRIJS,WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),7),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
    ]))
    story.append(rd_info)

    # Voedingsmiddelen racedag — balk zonder grammen
    rd_items = []
    for k, val in rd_waarden.items():
        if val and val > 0:
            parts = k.split("_", 2)
            prod_naam = parts[2] if len(parts) > 2 else k
            kh_pp    = CL_KH_MAP.get(prod_naam, 0)
            eenheid  = CL_PORTIE_MAP.get(prod_naam, "portie")
            n = int(val) if val == int(val) else val
            _MV2 = {"snede":"sneden","kom":"kommen","glas":"glazen","stuk":"stuks",
                    "potje":"potjes","eetlepel":"eetlepels","koffielepel":"koffielepels",
                    "zakje":"zakjes","bord":"borden","portie":"porties",
                    "schaaltje":"schaaltjes","reep":"repen","tas":"tassen"}
            e_mv = _MV2.get(eenheid, eenheid + "s") if n > 1 else eenheid
            rd_items.append((f"{n} {e_mv} {prod_naam.lower()}", round(val * kh_pp)))

    if rd_items:
        story.append(Spacer(1, 5))
        rd_rows = [[Paragraph("VOEDINGSMIDDEL — HOEVEELHEID", s_kop), Paragraph("KH", s_kop)]]
        rd_kh_tot = 0
        for omschr, kh in rd_items:
            rd_rows.append([Paragraph(omschr, s_body), Paragraph(f"{kh}g", s_body)])
            rd_kh_tot += kh
        rd_food_t = Table(rd_rows, colWidths=[breed*0.78, breed*0.22])
        rd_food_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),DONKER),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),7),
            ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ]))
        story.append(rd_food_t)
        # Kleurenbalk — geen grammen
        kh_max_rd = round(int(data.get("gewicht", 70) or 70) * 4)
        rd_pct    = min(100, round((rd_kh_tot / kh_max_rd)*100)) if kh_max_rd > 0 else 0
        rd_over   = rd_kh_tot > kh_max_rd
        if rd_over:            balk_c = ROOD
        elif rd_pct >= 25:     balk_c = GROEN
        elif rd_pct >= 15:     balk_c = GEEL
        else:                  balk_c = ORANJE
        vul = max(0, min(rd_pct, 100)) / 100
        balk = Table([["", ""]], colWidths=[breed*vul if vul > 0 else 0.01, breed*(1-vul) if vul < 1 else 0.01])
        balk.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,0),balk_c),
            ("BACKGROUND",(1,0),(1,0),colors.HexColor("#1e293b")),
            ("ROWHEIGHT",(0,0),(-1,-1),0.25*cm),
            ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ]))
        story.append(balk)

    # Receptsuggesties verwijderd — niet nodig bij laatste maaltijd

    rd_tips = [
        "Kies producten die je al getest hebt in training — geen nieuw voedsel op racedag.",
        "Kies licht verteerbaar: laag in vezels en vetten.",
        "Drink geen grote hoeveelheden vocht vlak voor de start — kleine slokjes.",
    ]
    story.append(Spacer(1,4))
    rd_tip_rows = [[Paragraph("TIPS LAATSTE MAALTIJD", s_kop)]]
    for tip in rd_tips:
        rd_tip_rows.append([Paragraph(f"  →  {tip}", s_tip)])
    rd_tip_t = Table(rd_tip_rows, colWidths=[breed])
    rd_tip_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),MIDDEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e2e8f0")),
    ]))
    story.append(rd_tip_t)

    # ── PAGINA 2 — RACEPLAN ────────────────────────────────────────────────────
    story.append(PageBreak())
    for blok in maak_header("RACEPLAN", f"{sport}  ·  {duur_str}  ·  Start {start}  ·  {atleet}"):
        story.append(blok)
    story.append(Spacer(1, 8))

    min_kh = data.get("min_kh", 0)
    max_kh = data.get("max_kh", 0)
    pool   = data.get("pool", {})
    supp   = pool.get("supplementen", {})

    # Lees preview comments
    preview_comments = data.get("preview_comments") or data.get("notities") or {}

    uren_berekend, vocht_per_m = _bereken_raceplan(data)
    preview_uren = data.get("preview_uren", {})

    # Logo voor HTML rapport
    logo_b64_html  = data.get("logo_b64", "")
    logo_mime_html = data.get("logo_mime", "image/png")
    logo_html_tag  = (
        f'<img src="data:{logo_mime_html};base64,{logo_b64_html}" ' +
        'style="max-height:48px;max-width:120px;object-fit:contain;">' 
        if logo_b64_html else ""
    )
    # Supplementen HTML blok
    _supp = data.get("pool", {}).get("supplementen", {})
    _supp_lijst_html = _supp.get("supp_lijst", []) if _supp else []
    if not _supp_lijst_html and _supp and _supp.get("gum_naam"):
        _supp_lijst_html = [_supp["gum_naam"]]
    _supp_lijst_html = [s for s in _supp_lijst_html if s]
    if _supp_lijst_html:
        _supp_items = "".join([
            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b;">' +
            f'<span style="font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;' +
            f'background:rgba(6,182,212,0.15);color:#67e8f9;border:1px solid #06b6d4;">SUP</span>' +
            f'<span style="font-size:13px;color:#f1f5f9;">{s}</span></div>'
            for s in _supp_lijst_html
        ])
        supp_html_blok = f'''
        <div style="background:#0f172a;border-radius:12px;padding:20px;margin:16px 0;">
          <div style="font-size:0.7rem;font-weight:700;color:#06b6d4;letter-spacing:2px;margin-bottom:12px;">💊 SUPPLEMENTEN</div>
          {_supp_items}
          <div style="font-size:11px;color:#64748b;margin-top:10px;font-style:italic;">
            ℹ️ Zorg ervoor dat je juist suppleert tijdens je wedstrijd.
          </div>
        </div>'''
    else:
        supp_html_blok = ""

    # Pas items aan op basis van preview_uren (gebruiker aangepast plan)
    uren = []
    for uur_data in uren_berekend:
        u_num = uur_data["uur"]
        if str(u_num) in preview_uren:
            items = preview_uren[str(u_num)]
            u_kh  = sum(i["kh"] for i in items)
            uur_data = dict(uur_data)
            uur_data["items"] = items
            uur_data["uur_kh"] = u_kh
        uren.append(uur_data)

    story.append(Spacer(1, 4))

    for uur_data in uren:
        u_num   = uur_data["uur"]
        u_start = uur_data["uur_start"]
        u_kh    = uur_data["uur_kh"]
        u_min   = uur_data["min_kh"]
        u_max   = uur_data["max_kh"]
        items   = uur_data["items"]
        geen_kh = uur_data["geen_kh"]
        is_last = uur_data["is_last"]
        comment = preview_comments.get(str(u_num), "")

        bar_c = GROEN if u_kh >= u_min else (GEEL if u_kh >= u_min*0.8 else ROOD)
        if geen_kh: bar_c = BLAUW

        kh_info = ("Geen extra KH nodig" if geen_kh else
                   f"Berekend: {u_kh}g  |  Target: {u_min}–{u_max}g")

        uur_kop = Table([[
            Paragraph(f"UUR {u_num}   {u_start}", s_uur_kop),
        ]], colWidths=[breed])
        uur_kop.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),DONKER),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ]))

        VAST_EMOJIS = {"🍌","🍫","🍪","🌾","🍎","🌰","🍱"}
        item_rows = []
        for item in items:
            EMOJI_BADGE = {
                "🥤": ("SD",   "#3b82f6"), "⚡": ("GEL", "#f97316"),
                "🍌": ("VAST", "#22c55e"), "🍫": ("VAST", "#22c55e"),
                "🍪": ("VAST", "#22c55e"), "🌾": ("VAST", "#22c55e"),
                "🍎": ("VAST", "#22c55e"), "🌰": ("VAST", "#22c55e"),
                "💊": ("SUP",  "#06b6d4"), "🍬": ("SUP",  "#06b6d4"),
                "🍱": ("VAST", "#22c55e"), "☕": ("CAF",  "#8b5cf6"),
                "💧": ("H2O",  "#64748b"), "🧃": ("SD",   "#3b82f6"),
            }
            bd, bd_hex = EMOJI_BADGE.get(item["emoji"], ("VAST", "#22c55e"))
            _water_ml_item = item.get("water_ml", 0)
            if item["emoji"] == "💧":
                naam_kort = f"{_water_ml_item}ml" if _water_ml_item > 0 else "Water"
            else:
                naam_kort = item["naam"].split("(")[0].strip()
            _pdf_antal = item.get("antal", 1.0)
            if _pdf_antal == 0.5:         _pdf_lbl = "½ "
            elif _pdf_antal != 1.0:       _pdf_lbl = f"{str(_pdf_antal).replace('.', ',')}x "
            else:                         _pdf_lbl = ""
            water_ml  = item.get("water_ml", 0)
            _slok_ml_pdf = 25 if sport in ["Lopen","Duatlon","Triatlon","Crosstriatlon"] else 40
            if water_ml > 0 and item["emoji"] in VAST_EMOJIS | {"⚡", "☕", "💊", "🍬"}:
                # Gel/vast/supplement: toon +Xml H2O
                water_str = f'  <font color="#64748b" size="7">+{water_ml}ml H2O</font>'
            elif item["emoji"] == "🥤" and water_ml > 0:
                # Sportdrank: toon slokken
                _slk = max(1, int(water_ml / _slok_ml_pdf + 0.5))
                water_str = f'  <font color="#64748b" size="7">≈{_slk} slokjes</font>'
            else:
                water_str = ""
            item_rows.append([
                Paragraph(item["min"], S("MIN", fontSize=8, fontName="Helvetica-Bold",
                                          textColor=BLAUW, leading=12)),
                Paragraph(
                    f'<font color="{bd_hex}"><b>[{bd}]</b></font>  {_pdf_lbl}{naam_kort}{water_str}',
                    s_body),
                Paragraph(f"{item['kh']}g" if item["kh"] > 0 else "—",
                          S("KHI", fontSize=8, textColor=ORANJE if item["kh"] > 0 else GRIJS,
                            fontName="Helvetica-Bold", leading=12, alignment=TA_RIGHT)),
            ])
        if not item_rows:
            # Geen items ingegeven — enkel notitie tonen indien aanwezig
            if comment:
                item_rows.append([
                    Paragraph("»", S("IC", fontSize=9, fontName="Helvetica-Bold",
                                      textColor=GEEL, leading=12)),
                    Paragraph(comment, S("CM", fontSize=7.5, textColor=colors.HexColor("#f59e0b"),
                                          fontName="Helvetica-Oblique", leading=11)),
                    Paragraph("", s_body),
                ])
            else:
                # Volledig leeg uur — sla over, voeg lege rij toe zonder H2O
                item_rows.append([Paragraph("", s_body),
                                  Paragraph('<font color="#64748b">—</font>', s_body),
                                  Paragraph("", s_body)])
        elif comment:
            item_rows.append([
                Paragraph("»", S("IC", fontSize=9, fontName="Helvetica-Bold",
                                  textColor=GEEL, leading=12)),
                Paragraph(comment, S("CM", fontSize=7.5, textColor=colors.HexColor("#f59e0b"),
                                      fontName="Helvetica-Oblique", leading=11)),
                Paragraph("", s_body),
            ])

        items_t = Table(item_rows, colWidths=[breed*0.15, breed*0.67, breed*0.18])
        items_t.setStyle(TableStyle([
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WIT,LGRIJS]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("BOX",(0,0),(-1,-1),0.3,colors.HexColor("#cbd5e1")),
            ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e2e8f0")),
        ]))
        # Progressiebalken KH + vocht per uur
        kh_pct  = min(100, round((u_kh / u_max) * 100)) if u_max > 0 else 0
        kh_over = u_kh > u_max
        toon_kh_balk_pdf = not (geen_kh or (is_last and u_max == 0))
        if geen_kh:          kh_c = BLAUW
        elif kh_over:        kh_c = ROOD
        elif u_kh >= u_min:  kh_c = GROEN
        elif kh_pct >= 50:   kh_c = GEEL
        else:                kh_c = ROOD

        # Vocht berekening uit items
        u_vocht = sum(
            i.get("water_ml", 0)
            for i in items
        )
        # Vocht target: consistent met preview (vocht_per_m × 3 innamen)
        _rest_pdf = int(totmin or 0) % 60 if int(totmin or 0) % 60 != 0 else 60
        _vocht_schaal_pdf = (_rest_pdf / 60) if is_last else 1.0
        vocht_uur_pdf = round(vocht_per_m * 3 * _vocht_schaal_pdf)
        v_pct  = min(100, round((u_vocht / vocht_uur_pdf) * 100)) if (vocht_uur_pdf > 0 and u_vocht > 0) else 0
        vocht_over_pdf = u_vocht > vocht_uur_pdf * 1.3
        if vocht_over_pdf:    v_c = ROOD
        elif v_pct >= 80:     v_c = GROEN
        elif v_pct >= 50:     v_c = GEEL
        else:                 v_c = ORANJE

        # Progressiebalken als één tabel onder de items
        balk_breed = breed - 1.2*cm  # zelfde breedte als items tabel
        lbl_breed  = 0.8*cm

        def _balk(pct, kleur):
            vul  = max(0, min(pct,100)) / 100
            rest = 1 - vul
            t = Table([["",""]], colWidths=[
                balk_breed*vul  if vul  > 0.01 else 0.5,
                balk_breed*rest if rest > 0.01 else 0.5,
            ])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,0),kleur),
                ("BACKGROUND",(1,0),(1,0),colors.HexColor("#1e293b")),
                ("ROWHEIGHT",(0,0),(-1,-1),0.17*cm),
                ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
            ]))
            return t

        # Progressiebalken met label links
        s_balk_lbl = S("BL", fontSize=7, fontName="Helvetica-Bold",
                        textColor=GRIJS, leading=10)
        LBL_B = 0.9*cm  # breedte label kolom
        BAR_B = breed - LBL_B  # breedte balk kolom

        def _balk_rij(label, pct, kleur):
            vul  = max(0, min(pct, 100)) / 100
            rest = 1.0 - vul
            balk = Table([["", ""]], colWidths=[
                BAR_B * vul  if vul  > 0 else 0.01,
                BAR_B * rest if rest > 0 else 0.01,
            ])
            balk.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(0,0), kleur),
                ("BACKGROUND", (1,0),(1,0), colors.HexColor("#1e293b")),
                ("ROWHEIGHT",  (0,0),(-1,-1), 0.22*cm),
                ("TOPPADDING",    (0,0),(-1,-1), 0),
                ("BOTTOMPADDING", (0,0),(-1,-1), 0),
                ("LEFTPADDING",   (0,0),(-1,-1), 0),
                ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ]))
            rij = Table([[Paragraph(label, s_balk_lbl), balk]],
                        colWidths=[LBL_B, BAR_B])
            rij.setStyle(TableStyle([
                ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
                ("LEFTPADDING",  (0,0),(0,0),   8),
                ("RIGHTPADDING", (0,0),(0,0),   4),
                ("LEFTPADDING",  (1,0),(1,0),   0),
                ("RIGHTPADDING", (1,0),(1,0),   0),
                ("TOPPADDING",   (0,0),(-1,-1), 2),
                ("BOTTOMPADDING",(0,0),(-1,-1), 2),
                ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#0f172a")),
            ]))
            return rij

        balken_lijst = [uur_kop, items_t]
        if toon_kh_balk_pdf:
            balken_lijst.append(_balk_rij("KH", kh_pct, kh_c))
        balken_lijst.append(_balk_rij("Vocht", v_pct, v_c))
        balken_lijst.append(Spacer(1, 4))
        story.append(KeepTogether(balken_lijst))

    # Legende onder raceplan
    leg_items_rp = [["[H2O]","Water / mondspoeling"],["[SD]","Sportdrank"],
                    ["[GEL]","Energy gel"],["[VAST]","Vast voedsel"],["[CAF]","Gel + cafeïne"],["[SUP]","Supplement"]]
    leg_row_rp = [[Paragraph(f"{s}  {l}", S("LGR", fontSize=7.5, textColor=GRIJS, leading=11))
                   for s, l in leg_items_rp]]
    leg_t_rp = Table(leg_row_rp, colWidths=[breed/6]*6)
    leg_t_rp.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("BACKGROUND",    (0,0),(-1,-1), LGRIJS),
        ("BOX",           (0,0),(-1,-1), 0.3, GRIJS),
    ]))
    story.append(Spacer(1, 6))
    story.append(leg_t_rp)

    # Supplementen
    _heeft_supp = (supp and (supp.get("ors_naam") or supp.get("gum_naam") or
                             any(s for s in supp.get("supp_lijst", []))))
    if _heeft_supp:
        story.append(Spacer(1, 4))
        story.append(Paragraph("SUPPLEMENTEN", s_sectie))
        story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))
        supp_rows = []
        if supp.get("ors_naam"):
            supp_rows.append([Paragraph("ORS tabletten", s_body),
                               Paragraph(f"{supp.get('ors_naam','')}", s_waarde)])
        # Alle supplementen tonen
        _supp_lijst_pdf = supp.get("supp_lijst", [])
        if not _supp_lijst_pdf and supp.get("gum_naam"):
            _supp_lijst_pdf = [supp["gum_naam"]]
        for _sn_pdf in [s for s in _supp_lijst_pdf if s]:
            supp_rows.append([Paragraph("Supplement", s_body),
                               Paragraph(f"{_sn_pdf}", s_waarde)])
        if supp_rows:
            st_t = Table(supp_rows, colWidths=[breed*0.3, breed*0.7])
            st_t.setStyle(TableStyle([
                ("ROWBACKGROUNDS",(0,0),(-1,-1),[LGRIJS,WIT]),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),8),
                ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ]))
            story.append(st_t)

    # ── PAGINA 3 — RACEMAP ────────────────────────────────────────────────────
    story.append(PageBreak())

    for blok in maak_header("CARBOO RACEMAP",
                             f"{sport}  ·  {duur_str}  ·  Start {start}  ·  {atleet}"):
        story.append(blok)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Knip de strip uit (±4.5cm breed) voor stuurbuis of bovenbuis.",
        S("INS", fontSize=8, textColor=GRIJS, leading=11)
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width=breed, thickness=0.5, color=ORANJE, spaceAfter=8))

    # Strip breedte
    STRIP_B   = 4.0 * cm
    COL_TIJD  = 1.0 * cm
    COL_LIJN  = 0.5 * cm
    COL_BADGE = STRIP_B - COL_TIJD - COL_LIJN

    from datetime import datetime as DT3, timedelta as TD3
    from collections import defaultdict as dd3

    BADGE_MAP3 = {
        "🥤":("SD","#3b82f6"),"⚡":("GEL","#f97316"),
        "🍌":("VAST","#22c55e"),"🍫":("VAST","#22c55e"),
        "🍪":("VAST","#22c55e"),"🌾":("VAST","#22c55e"),
        "🍎":("VAST","#22c55e"),"🌰":("VAST","#22c55e"),
        "🍱":("VAST","#22c55e"),"☕":("CAF","#8b5cf6"),
        "💊":("SUP","#06b6d4"),"🍬":("SUP","#06b6d4"),
        "💧":("H2O","#64748b"),"🧃":("SD","#3b82f6"),
    }
    _slok3 = 25 if sport in ["Lopen","Duatlon","Triatlon","Crosstriatlon"] else 40

    tl3_data   = []
    tl3_styles = []
    r3 = 0

    s_tc = S("TC3", fontSize=8, fontName="Helvetica-Bold",
               textColor=ORANJE, leading=10, alignment=TA_RIGHT)
    s_tc2 = S("TC4", fontSize=7, textColor=GRIJS, leading=9, alignment=TA_RIGHT)
    s_dot = S("DC3", fontSize=8, textColor=ORANJE, alignment=TA_CENTER, leading=10)
    s_dot2 = S("DC4", fontSize=6, textColor=GRIJS, alignment=TA_CENTER, leading=8)
    s_badge = S("BC3", fontSize=7, fontName="Helvetica",
                 textColor=colors.HexColor("#1e293b"), leading=9)

    for uur_data in uren:
        u_num3   = uur_data["uur"]
        u_start3 = uur_data["uur_start"]
        is_last3 = uur_data["is_last"]
        # Gebruik preview_uren (wat gebruiker ingesteld heeft) net als raceplan
        if str(u_num3) in preview_uren and preview_uren[str(u_num3)]:
            items3 = preview_uren[str(u_num3)]
        else:
            items3 = uur_data["items"]

        ipm3 = dd3(list)
        for item in items3:
            ipm3[item["min"]].append(item)

        mo3 = ["+20min","+30min","+40min","+45min","+60min"]
        gs3 = [(m, ipm3[m]) for m in mo3 if m in ipm3]
        for m, its in ipm3.items():
            if m not in mo3:
                gs3.append((m, its))

        if not gs3:
            continue

        uur_dt3 = DT3.strptime(u_start3, "%H:%M")

        for i3, (ml3, mitems3) in enumerate(gs3):
            off3 = int(ml3.replace("+","").replace("min","")) if ml3 != "+60min" else 60
            tijd3 = (uur_dt3 + TD3(minutes=off3)).strftime("%H:%M")

            t_cel = Paragraph(f"<b>{tijd3}</b>" if i3==0 else tijd3,
                               s_tc if i3==0 else s_tc2)
            d_cel = Paragraph("●", s_dot if i3==0 else s_dot2)

            # Badge tekst — kort houden
            parts3 = []
            for item in mitems3:
                bd3, bh3 = BADGE_MAP3.get(item["emoji"], ("?","#888"))
                nm3 = item["naam"].split("(")[0].strip()[:12]
                kh3 = f"({item['kh']}g)" if item["kh"] > 0 else ""
                wml3 = item.get("water_ml", 0)
                if wml3 > 0 and item["emoji"] not in ["🥤","💧"]:
                    w3 = f'<font color="#64748b">[H2O] +{wml3}ml</font>'
                elif item["emoji"] == "🥤" and wml3 > 0:
                    w3 = f'<font color="#64748b">≈{max(1,int(wml3/_slok3+0.5))} slokjes</font>'
                else:
                    w3 = ""
                line3 = f'<font color="{bh3}"><b>[{bd3}]</b></font> {nm3}{kh3}'
                if w3:
                    line3 += f"<br/>{w3}"
                parts3.append(line3)

            b_cel = Paragraph("<br/>".join(parts3), s_badge)
            tl3_data.append([t_cel, d_cel, b_cel])

            tp3 = 4 if i3 == 0 else 2
            tl3_styles += [
                ("TOPPADDING",    (0,r3),(-1,r3), tp3),
                ("BOTTOMPADDING", (0,r3),(-1,r3), 1),
                ("LEFTPADDING",   (0,r3),(0,r3),  1),
                ("RIGHTPADDING",  (0,r3),(0,r3),  1),
                ("LEFTPADDING",   (1,r3),(1,r3),  0),
                ("RIGHTPADDING",  (1,r3),(1,r3),  0),
                ("LEFTPADDING",   (2,r3),(2,r3),  2),
                ("RIGHTPADDING",  (2,r3),(2,r3),  1),
                ("VALIGN",        (0,r3),(-1,r3),  "TOP"),
            ]
            if i3 == 0:
                tl3_styles.append(("BACKGROUND",(0,r3),(0,r3),colors.HexColor("#fff7ed")))
            r3 += 1

        if not is_last3:
            tl3_data.append([
                Paragraph(" ", S(f"sp{r3}", fontSize=3, leading=4)),
                Paragraph("-", S(f"sep{r3}", fontSize=4, textColor=GRIJS,
                                  alignment=TA_CENTER, leading=4)),
                Paragraph(" ", S(f"sp2{r3}", fontSize=3, leading=4)),
            ])
            tl3_styles += [
                ("TOPPADDING",    (0,r3),(-1,r3), 0),
                ("BOTTOMPADDING", (0,r3),(-1,r3), 0),
                ("ROWHEIGHT",     (0,r3),(-1,r3), 5),
            ]
            r3 += 1

    if tl3_data:
        tl3_styles += [
            ("BOX",          (0,0),(-1,-1), 0.5, ORANJE),
            ("LINEAFTER",    (0,0),(0,-1),  0.3, colors.HexColor("#334155")),
            ("LINEAFTER",    (1,0),(1,-1),  0.3, colors.HexColor("#334155")),
            ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#f8fafc")),
            ("BACKGROUND",   (1,0),(1,-1),  colors.HexColor("#1e293b")),
            # Dot kolom: GEEN padding — kolom is te smal
            ("LEFTPADDING",  (1,0),(1,-1),  0),
            ("RIGHTPADDING", (1,0),(1,-1),  0),
            ("TOPPADDING",   (1,0),(1,-1),  0),
            ("BOTTOMPADDING",(1,0),(1,-1),  0),
        ]
        tl3_t = Table(tl3_data,
                      colWidths=[COL_TIJD, COL_LIJN, COL_BADGE],
                      repeatRows=0, hAlign="LEFT")
        tl3_t.setStyle(TableStyle(tl3_styles))
        story.append(tl3_t)

    # Legende — volledige breedte
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width=breed, thickness=0.5, color=GRIJS, spaceAfter=5))
    leg_rm = [("[H2O]","Water"),("[SD]","Sportdrank"),("[GEL]","Energy gel"),
              ("[VAST]","Vast voedsel"),("[CAF]","Cafeïne"),("[SUP]","Supplement")]
    leg_rm_row = [[Paragraph(
        f'<font color="#64748b"><b>{s}</b></font>  {l}',
        S("LR", fontSize=7.5, textColor=DONKER, leading=11))
        for s, l in leg_rm]]
    leg_rm_t = Table(leg_rm_row, colWidths=[breed/6]*6)
    leg_rm_t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("BOX",           (0,0),(-1,-1), 0.5, GRIJS),
        ("INNERGRID",     (0,0),(-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND",    (0,0),(-1,-1), LGRIJS),
    ]))
    story.append(leg_rm_t)


    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=STRIP_B, thickness=0.5, color=GRIJS, spaceAfter=3))
    leg_items_strip = [
        ("[SD]","Sportdrank"), ("[GEL]","Gel"),
        ("[VAST]","Vast"), ("[CAF]","Cafeïne"),
        ("[H2O]","Water"), ("[SUP]","Suppl."),
    ]
    for s, l in leg_items_strip:
        story.append(Paragraph(
            f'<font color="#64748b"><b>{s}</b></font>  <font size="6" color="#64748b">{l}</font>',
            S("LGS", fontSize=6, fontName="Helvetica", leading=9)
        ))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width=STRIP_B, thickness=0.5, color=GRIJS))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Gegenereerd door Carboo Race Nutrition. Dit plan is een richtlijn — gemaakt door sportdiëtisten.",
        s_footer
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()




def _genereer_html(data: dict, gebruiker_naam: str) -> str:
    """Genereer volledig HTML rapport van het race nutrition plan."""
    from datetime import datetime, timedelta, datetime as DT
    from collections import defaultdict
    import math

    atleet        = data.get("atleet_naam", gebruiker_naam)
    wedstrijd_naam = data.get("wedstrijd_naam", "")
    sport         = data.get("sport", "—")
    niveau        = data.get("niveau", "—")
    gewicht       = (data.get("gewicht", "—") or "—")
    datum         = data.get("wedstrijd_datum", "—")
    start         = data.get("start_time", "—")
    eind          = data.get("eind_time", "—")
    totmin   = int(int(data.get("totale_min", 0) or 0) or 0)
    duur_str = f"{int(totmin or 0) // 60}u{int(totmin or 0) % 60:02d}m" if totmin else "—"
    temp     = data.get("temp", "—")
    vocht    = data.get("vochtigheid", "—")
    hoogte   = data.get("hoogte", "—")
    ervaring = data.get("ervaring", "—")
    dag_target = data.get("dag_target", 0)
    cl_data    = data.get("carboloading", {})
    cl_waarden = data.get("cl_waarden", {})
    rd_waarden = data.get("rd_waarden", {})
    ont_kh     = data.get("ontbijt_kh", 0)
    ont_timing = data.get("ontbijt_timing", "—")
    ont_tijd   = data.get("ontbijt_tijd", "—")
    maaltijd_mom = data.get("maaltijd_moment", "Ontbijt")
    min_kh     = data.get("min_kh", 0)
    max_kh     = data.get("max_kh", 0)
    temp_val   = int(data.get("temp", 18) or 18)
    pool       = data.get("pool", {})
    preview_comments = data.get("preview_comments", {})

    if temp_val > 25:   vocht_advies = "600–800ml (2–3u voor start, warm)"
    elif temp_val > 15: vocht_advies = "400–600ml (2–3u voor start)"
    else:               vocht_advies = "300–500ml (2–3u voor start, koel)"

    CL_KH_MAP = {
        "Wit brood":17,"Bruin brood":16,"Volkorenbrood":14,"Havermout":27,
        "Ontbijtgranen":25,"Muesli":30,"Granola (krokant)":26,
        "Melk (dierlijk)":9,"Plantaardige melk":9,"Banaan":30,"Appel":15,
        "Peer":19,"Kiwi":11,"Yoghurt natuur":6,"Plattekaas":4,
        "Confituur":3,"Honing":4,"Chocopasta":3,"Koffie met suiker":5,
        "Vruchtensap sinaas":20,"Sportdrank":35,"Rijstwafels":7,
        "Energiereep":40,"Rozijnen":15,"Dadels gedroogd":6,
        "Muesli/granenreep":26,"Speculoos":5,"Snoep/winegums":26,
        "Appelmoes":27,"Pannenkoek":27,
        "Pasta (hoofdmaaltijd)":75,"Pasta (bijgerecht)":37,
        "Rijst (hoofdmaaltijd)":81,"Rijst (bijgerecht)":42,
        "Aardappelen gekookt":30,"Groentenmix rauw":5,"Groentenmix warm":8,
    }
    CL_PORTIE_MAP = {
        "Wit brood":"sneden","Bruin brood":"sneden","Volkorenbrood":"sneden",
        "Havermout":"kom","Ontbijtgranen":"kom","Muesli":"kom","Granola (krokant)":"kom",
        "Melk (dierlijk)":"glas","Plantaardige melk":"glas","Banaan":"stuk","Appel":"stuk",
        "Peer":"stuk","Kiwi":"stuk","Yoghurt natuur":"potje","Plattekaas":"eetlepels",
        "Confituur":"koffielepel","Honing":"koffielepel","Chocopasta":"koffielepel",
        "Koffie met suiker":"tas","Vruchtensap sinaas":"glas","Sportdrank":"bidon",
        "Pasta (hoofdmaaltijd)":"bord","Pasta (bijgerecht)":"bord",
        "Rijst (hoofdmaaltijd)":"bord","Rijst (bijgerecht)":"bord",
        "Aardappelen gekookt":"bord","Groentenmix rauw":"bord","Groentenmix warm":"bord",
        "Rijstwafels":"stuk","Energiereep":"reep","Rozijnen":"handje",
        "Appelmoes":"schaaltje","Pannenkoek":"stuk",
    }
    MAALTIJDEN = ["Ontbijt","Tussendoor VM","Lunch","Tussendoor NM","Avondmaal","Avond snack"]
    BADGE = {"🥤":("SD","#3b82f6"),"⚡":("GEL","#f97316"),
             "🍌":("VAST","#22c55e"),"🍫":("VAST","#22c55e"),"🍪":("VAST","#22c55e"),
             "🌾":("VAST","#22c55e"),"🍎":("VAST","#22c55e"),"🌰":("VAST","#22c55e"),
             "🍱":("VAST","#22c55e"),
             "☕":("CAF","#8b5cf6"),
             "💊":("SUP","#06b6d4"),"🍬":("SUP","#06b6d4"),
             "💧":("H2O","#64748b")}

    def kh_col(pct, grens_groen=90, grens_geel=70):
        if pct >= grens_groen: return "#22c55e"
        if pct >= grens_geel:  return "#fbbf24"
        return "#ef4444"

    def prog_bar(val, target, grens_groen=90, grens_geel=70, over_rood=True):
        if target == 0:
            return ""
        pct = min(round(val/target*100), 100)
        over = val > target
        if over and over_rood:
            col = "#ef4444"
        else:
            col = kh_col(pct, grens_groen, grens_geel)
        return (f'<div style="background:#0f172a;border-radius:3px;height:7px;margin:5px 0 2px;overflow:hidden">' +
                f'<div style="width:{pct}%;height:100%;background:{col};border-radius:3px"></div></div>')

    # ── Carboloading HTML ─────────────────────────────────────────────────────
    cl_html = ""
    for dag_num in [1, 2]:
        dag_vals = cl_data.get(f"dag{dag_num}", {})
        totaal   = dag_vals.get("totaal", 0)
        target   = dag_vals.get("target", dag_target)
        pct      = dag_vals.get("pct", 0)
        col      = kh_col(pct)
        lbl      = "2 dagen voor race" if dag_num == 1 else "1 dag voor race"

        rows = ""
        for m in MAALTIJDEN:
            items_txt = []
            for prod, kh_pp in CL_KH_MAP.items():
                val = cl_waarden.get(f"cl_d{dag_num}_{m}_{prod}", 0)
                if val and val > 0:
                    n = int(val) if val == int(val) else val
                    eenh = CL_PORTIE_MAP.get(prod, "portie")
                    items_txt.append(f"{n} {eenh} {prod.lower()}")
            if items_txt:
                rows += (f'<tr><td class="ml-name">{m}</td>' +
                         f'<td class="ml-items">{", ".join(items_txt)}</td></tr>')

        # Eigen producten carboloading
        eigen_cl = data.get("cl_eigen", {})
        for m in MAALTIJDEN:
            eigen_items = eigen_cl.get(f"d{dag_num}_{m}", [])
            if eigen_items:
                items_txt = [f"{int(it['port'])} portie {it['naam'].lower()} ({round(it['kh']*it['port'])}g KH)"
                             for it in eigen_items]
                rows += (f'<tr><td class="ml-name">{m} (eigen)</td>' +
                         f'<td class="ml-items" style="color:#f97316">{", ".join(items_txt)}</td></tr>')

        cl_html += (
            f'<div style="margin-bottom:10px">' +
            f'<div style="background:#0f172a;border-radius:5px;padding:5px 10px;font-size:12px;' +
            f'font-weight:bold;color:#94a3b8;display:flex;justify-content:space-between;margin-bottom:4px">' +
            f'<span>DAG {dag_num} — {lbl}</span></div>' +
            f'<table class="ml-table"><tbody>{rows}</tbody></table>' +
            prog_bar(totaal, target, grens_groen=80, grens_geel=50) +
            '</div>'
        )

    # ── Laatste maaltijd HTML ─────────────────────────────────────────────────
    rd_items = []
    rd_kh_tot = 0
    for k, val in rd_waarden.items():
        if val and val > 0:
            parts = k.split("_", 2)
            prod  = parts[2] if len(parts) > 2 else k
            kh_pp = CL_KH_MAP.get(prod, 0)
            n     = int(val) if val == int(val) else val
            eenh  = CL_PORTIE_MAP.get(prod, "portie")
            rd_items.append((f"{n} {eenh} {prod.lower()}", round(val*kh_pp)))
            rd_kh_tot += round(val*kh_pp)
    # Eigen producten racedag
    for it in data.get("rd_eigen", []):
        kh_tot_it = round(it["kh"] * it["port"])
        rd_items.append((f"{int(it['port'])} portie {it['naam'].lower()}", kh_tot_it))
        rd_kh_tot += kh_tot_it

    rd_rows = "".join(
        f'<tr><td style="padding:4px 8px;font-size:12px">{omschr}</td>' +
        f'<td style="text-align:right;padding:4px 8px;font-size:12px;color:#f97316;font-weight:bold">{kh}g</td></tr>'
        for omschr, kh in rd_items
    )
    # Laatste maaltijd balk: grens = kh_max (gewicht*4), groen bij ≥25% (zelfde als in wizard)
    kh_max_rd = round(gewicht * 4) if isinstance(gewicht, (int, float)) else 288
    lm_pct    = round(rd_kh_tot / kh_max_rd * 100) if kh_max_rd > 0 else 0
    lm_over   = rd_kh_tot > kh_max_rd
    if lm_over:          lm_col = "#ef4444"
    elif lm_pct >= 25:   lm_col = "#22c55e"
    elif lm_pct >= 15:   lm_col = "#fbbf24"
    else:                lm_col = "#f97316"
    lm_prog = (f'<div style="background:#0f172a;border-radius:3px;height:7px;margin:5px 0 2px;overflow:hidden">' +
               f'<div style="width:{min(lm_pct,100)}%;height:100%;background:{lm_col};border-radius:3px"></div></div>')

    # ── Raceplan HTML ─────────────────────────────────────────────────────────
    # Gebruik preview_uren (door gebruiker aangepast) indien beschikbaar
    # Anders terugvallen op _bereken_raceplan
    uren_berekend, vocht_per_m = _bereken_raceplan(data)
    preview_uren = data.get("preview_uren", {})

    # Logo voor HTML rapport
    logo_b64_html  = data.get("logo_b64", "")
    logo_mime_html = data.get("logo_mime", "image/png")
    logo_html_tag  = (
        f'<img src="data:{logo_mime_html};base64,{logo_b64_html}" ' +
        'style="max-height:48px;max-width:120px;object-fit:contain;">' 
        if logo_b64_html else ""
    )
    # Supplementen HTML blok
    _supp = data.get("pool", {}).get("supplementen", {})
    _supp_lijst_html = _supp.get("supp_lijst", []) if _supp else []
    if not _supp_lijst_html and _supp and _supp.get("gum_naam"):
        _supp_lijst_html = [_supp["gum_naam"]]
    _supp_lijst_html = [s for s in _supp_lijst_html if s]
    if _supp_lijst_html:
        _supp_items = "".join([
            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b;">' +
            f'<span style="font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;' +
            f'background:rgba(6,182,212,0.15);color:#67e8f9;border:1px solid #06b6d4;">SUP</span>' +
            f'<span style="font-size:13px;color:#f1f5f9;">{s}</span></div>'
            for s in _supp_lijst_html
        ])
        supp_html_blok = f'''
        <div style="background:#0f172a;border-radius:12px;padding:20px;margin:16px 0;">
          <div style="font-size:0.7rem;font-weight:700;color:#06b6d4;letter-spacing:2px;margin-bottom:12px;">💊 SUPPLEMENTEN</div>
          {_supp_items}
          <div style="font-size:11px;color:#64748b;margin-top:10px;font-style:italic;">
            ℹ️ Zorg ervoor dat je juist suppleert tijdens je wedstrijd.
          </div>
        </div>'''
    else:
        supp_html_blok = ""

    raceplan_html = ""
    for uur_data in uren_berekend:
        u_num   = uur_data["uur"]
        u_start = uur_data["uur_start"]
        u_min   = uur_data["min_kh"]
        u_max   = uur_data["max_kh"]
        geen_kh = uur_data["geen_kh"]
        is_last = uur_data["is_last"]
        comment = preview_comments.get(str(u_num), "")

        # Gebruik preview_uren als key bestaat (ook als leeg)
        if str(u_num) in preview_uren:
            items = preview_uren[str(u_num)]
        else:
            items = uur_data["items"]

        u_kh    = sum(i["kh"] for i in items)
        bar_col = "#22c55e" if u_kh >= u_min else ("#fbbf24" if u_kh >= u_min*0.8 else "#ef4444")
        if geen_kh: bar_col = "#3b82f6"
        kh_info = "Geen extra KH nodig" if geen_kh else f"KH: {u_kh}g | target {u_min}–{u_max}g"

        item_rows = ""
        for item in items:
            bd, col = BADGE.get(item["emoji"], ("?","#888"))
            kh_txt = f'<span style="color:#f97316;font-weight:bold;margin-left:auto">{item["kh"]}g</span>' if item["kh"] > 0 else ""
            naam_kort = item["naam"].split("(")[0].strip()
            # Formatteer aantal
            _antal = item.get("antal", 1.0)
            if _antal == 0.5:       _antal_lbl = "½ "
            elif _antal == int(_antal) and _antal != 1: _antal_lbl = f"{int(_antal)}× "
            elif _antal != 1:       _antal_lbl = f"{str(_antal).replace('.', ',')}× "
            else:                   _antal_lbl = ""
            # Water badge + ml: gebruik gekozen hoeveelheid uit plan
            _item_water_ml = item.get("water_ml", 0)
            if item["emoji"] in ["⚡", "🍌", "☕", "🍫","🍪","🌾","🍎","🌰","🍱","💊","🍬"]:
                # Enkel tonen als gebruiker water heeft gekozen
                if _item_water_ml > 0:
                    water_txt = (
                        f' <span style="color:#64748b;border:1px solid #64748b;border-radius:2px;' +
                        f'font-size:8px;font-weight:bold;padding:0 2px;line-height:11px;display:inline-block;' +
                        f'margin-left:3px">H2O {_item_water_ml}ml</span>'
                    )
                else:
                    water_txt = ""
            elif item["emoji"] == "💧":
                # Water item: toon ml direct in naam, geen aparte water_txt
                naam_kort = f"{_item_water_ml}ml" if _item_water_ml > 0 else "Water"
                water_txt = ""
            elif item["emoji"] == "🥤":
                # Sportdrank: toon slokken op basis van sport
                _slok_ml  = 25 if sport in ["Lopen","Duatlon","Triatlon","Crosstriatlon"] else 40
                _slokken  = max(1, int(_item_water_ml / _slok_ml + 0.5)) if _item_water_ml > 0 else ""
                water_txt = (
                    f' <span style="color:#64748b;font-size:9px;margin-left:3px">≈ {_slokken} slokjes</span>'
                ) if _slokken else ""
            else:
                water_txt = ""
            item_rows += (
                f'<div class="item-row">' +
                f'<span class="item-min">{item["min"]}</span>' +
                f'<span class="item-badge" style="color:{col};border-color:{col}">{bd}</span>' +
                f'<span class="item-naam">{_antal_lbl}{naam_kort}{water_txt}</span>' +
                f'{kh_txt}</div>'
            )
        if comment:
            item_rows += f'<div class="item-comment">◂ {comment}</div>'

        # Vocht berekening per uur
        u_vocht = sum(item.get("water_ml", 0) for item in items)
        # KH balk
        kh_pct   = min(100, round((u_kh / u_max) * 100)) if u_max > 0 else 0
        kh_over  = u_kh > u_max
        toon_kh_balk = not (geen_kh or (is_last and u_max == 0))  # verberg bij geen KH
        if geen_kh:           kh_balk_col = "#3b82f6"
        elif kh_over:         kh_balk_col = "#ef4444"
        elif u_kh >= u_min:   kh_balk_col = "#22c55e"
        elif kh_pct >= 50:    kh_balk_col = "#fbbf24"
        else:                 kh_balk_col = "#ef4444"

        # Vocht balk — target = vocht_per_m × aantal innamen
        # Vocht target: consistent met preview (vocht_per_m × 3 innamen = vocht per uur)
        _rest_min_html = int(totmin or 0) % 60 if int(totmin or 0) % 60 != 0 else 60
        _vocht_schaal  = (_rest_min_html / 60) if is_last else 1.0
        vocht_uur_html = round(vocht_per_m * 3 * _vocht_schaal)  # zelfde als preview
        # Als geen vocht ingegeven: balk op 0%
        vocht_pct      = min(100, round((u_vocht / vocht_uur_html) * 100)) if (vocht_uur_html > 0 and u_vocht > 0) else 0
        vocht_over = u_vocht > vocht_uur_html * 1.3
        if vocht_over:        v_balk_col = "#ef4444"
        elif vocht_pct >= 80: v_balk_col = "#22c55e"
        elif vocht_pct >= 50: v_balk_col = "#fbbf24"
        else:                 v_balk_col = "#f97316"

        kh_balk_str = (
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">' +
            f'<span style="font-size:9px;color:#64748b;width:20px;flex-shrink:0">KH</span>' +
            f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px">' +
            f'<div style="width:{kh_pct}%;height:100%;background:{kh_balk_col};border-radius:3px"></div></div></div>'
        ) if toon_kh_balk else ""
        balken_html = (
            f'<div style="padding:4px 5px 3px 5px;background:#0a0f1e;border-radius:0 0 5px 5px">' +
            kh_balk_str +
            f'<div style="display:flex;align-items:center;gap:6px">' +
            f'<span style="font-size:9px;color:#64748b;width:20px;flex-shrink:0">💧</span>' +
            f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px">' +
            f'<div style="width:{vocht_pct}%;height:100%;background:{v_balk_col};border-radius:3px"></div></div></div>' +
            f'</div>'
        )

        raceplan_html += (
            f'<div style="margin-bottom:6px">' +
            f'<div style="background:#0f172a;border-radius:5px 5px 0 0;padding:5px 10px;font-size:12px;' +
            f'font-weight:bold;color:#93c5fd;margin-bottom:0">' +
            f'<span>UUR {u_num} {u_start}</span></div>' +
            f'<div style="padding:0 4px">{item_rows}</div>' +
            balken_html +
            f'</div>'
        )

    # ── Carboo Racemap HTML ───────────────────────────────────────────────────
    racemap_rows = ""
    for uur_data in uren_berekend:
        u_start = uur_data["uur_start"]
        u_num_rm = uur_data["uur"]
        # Gebruik preview items voor racemap ook
        if str(u_num_rm) in preview_uren and preview_uren[str(u_num_rm)]:
            items = preview_uren[str(u_num_rm)]
        else:
            items   = uur_data["items"]
        comment = preview_comments.get(str(u_num_rm), "")
        uur_dt  = DT.strptime(u_start, "%H:%M")
        per_min = defaultdict(list)
        for item in items:
            per_min[item["min"]].append(item)
        def get_offset(m):
            return int(m.replace("+","").replace("min",""))
        gesorteerd = sorted(per_min.items(), key=lambda x: get_offset(x[0]))
        for i, (ml, min_items) in enumerate(gesorteerd):
            offset = get_offset(ml)
            exact  = (uur_dt + timedelta(minutes=offset)).strftime("%H:%M")
            t_s = "color:#f97316;font-weight:bold" if i == 0 else "color:#475569"
            d_s = "background:#f97316;width:5px;height:5px" if i == 0 else "background:#334155;width:3px;height:3px;border:1px solid #475569"
            badges_parts = []
            for item in min_items:
                bd, col = BADGE.get(item["emoji"], ("?","#888"))
                # Toon productnaam bij gel, vast en cafeïne
                naam_kort = item["naam"].split("(")[0].strip()[:14]
                _rm_antal = item.get("antal", 1.0)
                if _rm_antal == 0.5:      _rm_lbl = "½ "
                elif _rm_antal != 1.0:    _rm_lbl = f"{str(_rm_antal).replace('.', ',')}× "
                else:                     _rm_lbl = ""
                if item["emoji"] in ["⚡", "☕","🍌","🍫","🍪","🌾","🍎","🌰","🍱"]:
                    lbl = f"{bd} {_rm_lbl}{naam_kort}"
                else:
                    lbl = f"{bd} {_rm_lbl}" if _rm_lbl else bd
                badge = f'<b style="color:{col};border:1px solid {col};border-radius:2px;padding:0 2px;font-size:9px;line-height:10px;display:inline-block;margin-right:1px">{lbl}</b>'
                # H2O badge enkel als gebruiker water heeft gekozen (water_ml > 0)
                _rm_wml = item.get("water_ml", 0)
                if item["emoji"] in ["⚡","☕","🍌","🍫","🍪","🌾","🍎","🌰","🍱","💊","🍬"] and _rm_wml > 0:
                    h2o = f'<b style="color:#64748b;border:1px solid #64748b;border-radius:2px;padding:0 2px;font-size:9px;line-height:10px;display:inline-block;margin-left:1px;margin-right:2px">H2O</b>'
                    badges_parts.append(badge + h2o)
                else:
                    badges_parts.append(badge)
            badges_html = "".join(badges_parts)
            racemap_rows += (
                f'<tr>' +
                f'<td style="text-align:right;padding:0 2px 0 0;font-size:9px;width:30px;white-space:nowrap;{t_s}">{exact}</td>' +
                f'<td style="width:10px;text-align:center;padding:0;position:relative">' +
                f'<div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:#334155;transform:translateX(-50%)"></div>' +
                f'<span style="{d_s};border-radius:50%;display:inline-block;position:relative;vertical-align:middle"></span>' +
                f'</td>' +
                f'<td style="padding:0 0 0 3px;font-size:9px;line-height:10px">{badges_html}</td>' +
                f'</tr>'
            )

    # ── Dynamische recepten op basis van avondmaal keuze ─────────────────────
    # Recepten en detecteer_recept zijn globaal gedefinieerd boven _genereer_pdf

    (rec1_titel, rec1_tekst), moment1 = detecteer_recept(1, cl_waarden, STANDAARD_RECEPT_DAG1)
    (rec2_titel, rec2_tekst), moment2 = detecteer_recept(2, cl_waarden, STANDAARD_RECEPT_DAG2)

    def maak_recept_html(dag_num, titel, tekst, moment, tussendoortjes):
        if moment is None:
            sectie_titel = "Suggestie Tussendoortjes"
            html_blokken = ""
            for td_titel, td_tekst in tussendoortjes:
                html_blokken += (
                    f'<div class="recept-blok">' +
                    f'<div class="recept-titel">✦ {td_titel}</div>' +
                    f'<div class="recept-tekst">{td_tekst}</div></div>'
                )
            return sectie_titel, html_blokken
        else:
            sectie_titel = f"{moment} Suggestie + Recept"
            html_blok = (
                f'<div class="recept-blok">' +
                f'<div class="recept-titel">✦ {titel} (dag {dag_num} voor race)</div>' +
                f'<div class="recept-tekst">{tekst}</div></div>'
            )
            return sectie_titel, html_blok



    sec1_titel, recept_dag1_html = maak_recept_html(1, rec1_titel, rec1_tekst, moment1, TUSSENDOORTJE_DAG1)
    sec2_titel, recept_dag2_html = maak_recept_html(2, rec2_titel, rec2_tekst, moment2, TUSSENDOORTJE_DAG2)

    # ── Volledige HTML ────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="nl"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Carboo Race Nutrition Plan — {atleet}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:20px}}
.page{{max-width:760px;margin:0 auto;display:flex;flex-direction:column;gap:14px}}
.header{{background:#1e293b;border-radius:10px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:21px;font-weight:900;color:#f97316;letter-spacing:2px}}
.header p{{font-size:14px;color:#64748b;margin-top:2px}}
.header-right{{text-align:right;font-size:14px;color:#64748b;line-height:1.6}}
.header-right b{{color:#f1f5f9;font-size:16px}}
.info-grid{{background:#1e293b;border-radius:10px;padding:12px 16px;display:grid;grid-template-columns:repeat(3,1fr);gap:7px}}
.info-item .lbl{{font-size:12px;font-weight:bold;color:#64748b;text-transform:uppercase;letter-spacing:.5px}}
.info-item .val{{font-size:15px;font-weight:bold;color:#f1f5f9;margin-top:1px}}
.sectie{{background:#1e293b;border-radius:10px;padding:14px 16px}}
.stitel{{font-size:14px;font-weight:bold;color:#f97316;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #334155}}
.ml-table{{width:100%;border-collapse:collapse;font-size:14px;margin-bottom:2px}}
.ml-table tr:nth-child(odd){{background:rgba(255,255,255,0.02)}}
.ml-name{{width:110px;padding:3px 8px;color:#64748b;font-size:13px;font-weight:bold;vertical-align:top}}
.ml-items{{padding:3px 8px;color:#cbd5e1;font-size:13.5px}}
.recept-blok{{background:rgba(30,58,138,0.25);border:1px solid #1e3a8a;border-radius:5px;padding:7px 10px;margin-top:6px}}
.recept-titel{{font-size:13px;font-weight:bold;color:#93c5fd;margin-bottom:2px}}
.recept-tekst{{font-size:12.5px;color:#94a3b8;line-height:1.5}}
.lm-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}}
.lm-item .lbl{{font-size:12px;color:#64748b;font-weight:bold;text-transform:uppercase}}
.lm-item .val{{font-size:15px;font-weight:bold;color:#f1f5f9}}
.voeding-table{{width:100%;border-collapse:collapse;margin-bottom:4px}}
.voeding-table tr:nth-child(even){{background:rgba(255,255,255,0.02)}}
.voeding-table th{{text-align:left;padding:5px 8px;font-size:12.5px;color:#64748b;background:#0f172a;font-weight:bold;text-transform:uppercase;letter-spacing:.5px}}
.item-row{{display:flex;align-items:center;gap:5px;padding:3px 5px;font-size:13px;border-bottom:1px solid rgba(255,255,255,0.03)}}
.item-min{{width:34px;color:#3b82f6;font-weight:bold;font-size:12px;flex-shrink:0}}
.item-badge{{font-size:11px;font-weight:bold;border:1px solid;border-radius:2px;padding:0 2px;line-height:12px;flex-shrink:0}}
.item-naam{{flex:1;color:#cbd5e1}}
.item-comment{{font-size:12px;color:#fbbf24;padding:2px 5px;font-style:italic}}
.raceplan-wrap{{display:grid;grid-template-columns:1fr 160px;gap:10px}}
.racemap-kaart{{background:#0f172a;border-radius:6px;padding:7px 9px}}
.racemap-kaart h3{{font-size:13px;font-weight:bold;color:#f97316;letter-spacing:1px;margin-bottom:1px}}
.racemap-kaart .sub{{font-size:10px;color:#475569;margin-bottom:4px}}
.racemap-kaart table{{width:100%;border-collapse:collapse;line-height:1;border-spacing:0}}
.racemap-leg{{font-size:10px;color:#64748b;margin-top:4px;border-top:1px solid #1e293b;padding-top:3px;display:flex;flex-wrap:wrap;gap:4px}}
.footer{{font-size:12px;color:#334155;text-align:center;padding:6px}}
</style>
</head>
<body>
<div class="page">

<div class="header">
  <div style="display:flex;align-items:center;gap:14px;">
    {logo_html_tag}
    <div>
      <h1>CARBOO RACE NUTRITION PLAN</h1>
      <p>{data.get("wedstrijd_naam","").upper()}</p>
    </div>
  </div>
  <div class="header-right">
    <b>{atleet}</b><br>
    {sport} · {duur_str}<br>
    {datum} · Start {start}
  </div>
</div>

<div class="info-grid">
  <div class="info-item"><div class="lbl">Naam atleet</div><div class="val">{atleet}</div></div>
  <div class="info-item"><div class="lbl">Discipline</div><div class="val">{sport}</div></div>
  <div class="info-item"><div class="lbl">Sportniveau</div><div class="val">{niveau}</div></div>
  <div class="info-item"><div class="lbl">Gewicht</div><div class="val">{gewicht} kg</div></div>
  <div class="info-item"><div class="lbl">Duur</div><div class="val">{duur_str}</div></div>
  <div class="info-item"><div class="lbl">Start / Eind</div><div class="val">{start} — {eind}</div></div>
  <div class="info-item"><div class="lbl">Temp / Vochtigheid</div><div class="val">{temp}°C | {vocht}%</div></div>
  <div class="info-item"><div class="lbl">Hoogte</div><div class="val">{hoogte} m</div></div>
  <div class="info-item"><div class="lbl">Ervaring wedstrijdvoeding</div><div class="val">{ervaring}</div></div>
</div>

<div class="sectie">
  <div class="stitel">Carboloading — Laatste 48 uur</div>
  {cl_html}
  <div style="margin-top:10px">
    <div class="stitel" style="font-size:11.5px;margin-bottom:6px">DAG 1 — {sec1_titel}</div>
    {recept_dag1_html}
    <div class="stitel" style="font-size:11.5px;margin-bottom:6px;margin-top:8px">DAG 2 — {sec2_titel}</div>
    {recept_dag2_html}
  </div>
</div>

<div class="sectie">
  <div class="stitel">Laatste Maaltijd voor de Wedstrijd</div>
  <div class="lm-grid">
    <div class="lm-item"><div class="lbl">Timing laatste maaltijd</div><div class="val">{ont_timing}</div></div>
    <div class="lm-item"><div class="lbl">Maaltijd om</div><div class="val">{ont_tijd}</div></div>
    <div class="lm-item"><div class="lbl">Totaal KH</div><div class="val" style="color:#f97316">{ont_kh}g</div></div>
    <div class="lm-item"><div class="lbl">Aanbevolen vocht</div><div class="val" style="font-size:12px">{vocht_advies}</div></div>
  </div>
  <table class="voeding-table">
    <tr><th>Voedingsmiddel</th><th style="text-align:right">KH</th></tr>
    {rd_rows}
  </table>
  {lm_prog}
</div>

<div class="sectie">
  <div class="stitel">Raceplan</div>
  <div class="raceplan-wrap">
    <div>{raceplan_html}</div>
    <div>
      <div class="racemap-kaart">
        <h3>CARBOO RACEMAP</h3>
        <div class="sub">{sport} · {duur_str} · {start}</div>
        <table>{racemap_rows}</table>
        <div class="racemap-leg">
          <span><b style="color:#3b82f6">SD</b> Drank</span>
          <span><b style="color:#f97316">GEL</b> Gel</span>
          <span><b style="color:#22c55e">VAST</b> Vast</span>
          <span><b style="color:#8b5cf6">CAF</b> Cafeïne</span>
          <span><b style="color:#64748b">H2O</b> Water</span>
        </div>
      </div>
    </div>
  </div>
</div>

{supp_html_blok}
<div class="footer">Gegenereerd door Carboo Race Nutrition.  Dit plan is een richtlijn — gemaakt door sportdiëtisten.</div>
</div>
</body></html>"""
    return html


def _stap_samenvatting():
    data = st.session_state.get("coach_data", {})
    naam = st.session_state.get("current_user", {}).get("name", "Atleet")

    _coach_bubble(f"""
    🎉 <b>Super gedaan, {naam}!</b> Hier is jouw <b>volledig gepersonaliseerd race nutrition plan</b>. 
    Bewaar dit goed en volg het stap voor stap!
    """, "🏆")

    st.markdown("""
    <div style="background:#1e293b; border-radius:16px; padding:20px; margin-bottom:20px; border-top:4px solid #f97316;">
        <div style="font-weight:900; color:#f97316; font-size:0.85rem; letter-spacing:2px; margin-bottom:14px;">📋 JOUW PLAN OVERZICHT</div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    info_items = [
        (c1, "Atleet", naam, "#f97316"),
        (c2, "Sport", f"{SPORT_ICONS.get(data.get('sport',''), '🏅')} {data.get('sport','—')}", "#3b82f6"),
        (c3, "Wedstrijd", data.get("wedstrijd_datum","—"), "#22c55e"),
        (c4, "Duur", f"{data.get('totale_min',0)//60}u{data.get('totale_min',0)%60:02d}m", "#8b5cf6"),
    ]
    for col, lbl, val, color in info_items:
        with col:
            st.markdown(f"""
            <div style="text-align:center; padding:10px; background:#0f172a; border-radius:10px; border-top:3px solid {color};">
                <div style="font-size:0.62rem; color:#64748b; font-weight:700; letter-spacing:1px;">{lbl.upper()}</div>
                <div style="font-size:0.95rem; font-weight:800; color:#f8fafc; margin-top:4px;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    tab_cl, tab_race, tab_plan = st.tabs(["🍝  CARBOLOADING", "🌅  RACEDAG", "⏱️  RACEPLAN"])

    with tab_cl:
        factor = data.get("factor", 8)
        dag_target = data.get("dag_target", 0)
        cl_data = data.get("carboloading", {})

        st.markdown(f"""
        <div style="background:rgba(249,115,22,0.1); border:1px solid #f97316; padding:14px; 
             border-radius:10px; margin-bottom:16px; text-align:center; color:#fb923c; font-weight:700;">
            📊 Protocol: {factor}g KH/kg/dag &nbsp;|&nbsp; 
            🎯 Dagdoel: {dag_target}g KH &nbsp;|&nbsp;
            ⚖️ Gewicht: {int(data.get("gewicht", 70) or 70)}kg
        </div>
        """, unsafe_allow_html=True)

        for dag_key in ["dag1", "dag2"]:
            dag_info = cl_data.get(dag_key, {})
            totaal = dag_info.get("totaal", 0)
            pct = dag_info.get("pct", 0)
            bar_c = "#22c55e" if pct >= 90 else ("#fbbf24" if pct >= 70 else "#ef4444")
            dag_num = dag_key[-1]
            dag_label = "2 dagen voor race" if dag_num == "1" else "1 dag voor race"

            st.markdown(f"""
            <div style="background:#0f172a; border-radius:12px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="font-weight:800; color:#f8fafc;">DAG {dag_num} — {dag_label}</div>
                    <div style="font-weight:700; color:{bar_c};">{totaal}g / {dag_target}g</div>
                </div>
                <div style="background:#334155; border-radius:6px; height:8px;">
                    <div style="width:{min(pct,100)}%; height:100%; background:{bar_c}; border-radius:6px;"></div>
                </div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">{pct}% van dagtarget</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:16px;">
            <div style="font-weight:800; color:#f97316; margin-bottom:10px; font-size:0.85rem;">💡 CARBOLOADING TIPS</div>
        """, unsafe_allow_html=True)
        tips_cl = [
            "🍚 Kies witte pasta, rijst en wit brood — minder vezels = minder maagklachten",
            "🍌 Bananen, dadelstroop en sportdranken zijn snelle koolhydraatbronnen",
            "🥩 Beperk eiwitten en vetten de laatste dag niet, maar geef koolhydraten prioriteit",
            "💧 Drink voldoende water — koolhydraten binden vocht (3g water per 1g KH)",
            "🚫 Vermijd nieuwe, onbekende voedingsmiddelen de dag voor de race",
        ]
        for tip in tips_cl:
            st.markdown(f'<div style="background:#1e293b; border-radius:8px; padding:10px 14px; margin-bottom:6px; font-size:0.82rem; color:#f8fafc;">{tip}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_race:
        ontbijt_tijd = data.get("ontbijt_tijd", "—")
        start_time = data.get("start_time", "—")
        ontbijt_kh = data.get("ontbijt_kh", 0)
        pre_totaal = data.get("pre_totaal_kh", 0)

        st.markdown(f"""
        <div style="background:#0f172a; border-radius:14px; padding:20px; margin-bottom:16px;">
            <div style="font-weight:900; color:#22c55e; margin-bottom:14px; font-size:0.85rem; letter-spacing:1px;">RACEDAGTIJDLIJN</div>
        """, unsafe_allow_html=True)

        tijdlijn = [
            (ontbijt_tijd, "🍳 ONTBIJT", f"{ontbijt_kh}g KH — licht verteerbaar, geen nieuwe producten", "#f97316"),
            ("30-60 min voor", "⚡ PRE-RACE", f"{'Gel + ' if data.get('pre_gel') else ''}{'Sportdrank + ' if data.get('sportdrank_ont') else ''}{'Koffie' if data.get('koffie') else 'Alleen water'}", "#3b82f6"),
            (start_time, "🏁 START", f"Totaal {pre_totaal}g KH geconsumeerd voor de start", "#22c55e"),
        ]
        for tijd, event, beschr, color in tijdlijn:
            st.markdown(f"""
            <div style="display:flex; gap:14px; margin-bottom:12px; align-items:flex-start;">
                <div style="background:{color}22; color:{color}; padding:4px 10px; border-radius:6px; 
                     font-size:0.7rem; font-weight:800; white-space:nowrap; min-width:80px; text-align:center; margin-top:2px;">{tijd}</div>
                <div>
                    <div style="font-weight:800; color:#f8fafc; font-size:0.85rem;">{event}</div>
                    <div style="color:#94a3b8; font-size:0.8rem; margin-top:2px;">{beschr}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        cafe_strat = data.get("cafeine_strategie", "—")
        st.markdown(f"""
        <div style="background:#fef3c7; border-left:4px solid #f59e0b; padding:12px 16px; 
             border-radius:8px; color:#92400e; font-size:0.85rem;">
            ⚡ <b>Cafeïne strategie:</b> {cafe_strat}
        </div>
        """, unsafe_allow_html=True)

    with tab_plan:
        pool = data.get("pool", {})
        totale_min = int(data.get("totale_min", 180) or 180)
        min_kh = data.get("min_kh", 60)
        max_kh = data.get("max_kh", 90)
        temp = int(data.get("temp", 18) or 18)
        hoogte = int(data.get("hoogte", 0) or 0)
        vochtigheid = int(int(data.get("vochtigheid", 50) or 50) or 50)
        start_dt = datetime.strptime(data.get("start_time", "09:00"), "%H:%M")
        aantal_uren = math.ceil(int(totale_min or 0) / 60)

        if not any(len(pool.get(k, [])) > 0 for k in ["drank", "gels", "vast", "cafe"]):
            st.markdown("""
            <div style="background:#fef2f2; border-left:4px solid #ef4444; padding:14px; 
                 border-radius:8px; color:#991b1b;">
                ⚠️ Geen producten ingevoerd. Ga terug naar stap 5 om je race-producten toe te voegen.
            </div>
            """, unsafe_allow_html=True)
        else:
            basis_vocht = 800 if int(temp or 18) > 25 else (600 if int(temp or 18) > 15 else 500)
            f_factor = (int(hoogte or 0) / 1000) * 0.15 + (0.15 if int(vochtigheid or 0) > 70 else 0)
            vocht_per_m = round(((basis_vocht * (1 + f_factor)) / 3) / 10) * 10

            if int(temp or 0) > 28 or (int(temp or 0) > 24 and int(vochtigheid or 0) > 75):
                st.markdown('<div class="alert-red">⚠️ <b>ORS NODIG:</b> Hitte + vochtigheid. Gebruik ORS voor zoutbalans.</div>', unsafe_allow_html=True)

            vast_idx = 0
            cafeine_gebruikt = False

            for u in range(aantal_uren):
                is_last = (u == aantal_uren - 1)
                cur_min_kh = round(min_kh * 0.6) if is_last else min_kh
                cur_max_kh = round(max_kh * 0.6) if is_last else max_kh
                uur_kh = 0
                moment_items = {1: [], 2: [], 3: []}
                uur_start = start_dt + timedelta(hours=u)
                uur_label = uur_start.strftime("%H:%M")

                if pool.get("drank"):
                    d = _pool_item("drank")
                    _d_naam = d.get("naam", d.get("name", "Sportdrank"))
                    kh_per_m = round((d["kh"] / 500) * vocht_per_m)
                    for m in [1, 2, 3]:
                        moment_items[m].append({"label": f"🥤 {vocht_per_m}ml <b>{_d_naam}</b> ({kh_per_m}g)", "kh": kh_per_m})
                        uur_kh += kh_per_m

                cafe_strat = data.get("cafeine_strategie", "")
                if u == 1 and not is_last and pool.get("cafe") and "uur 2" in cafe_strat:
                    c = _pool_item("cafe")
                    _c_naam = c.get("naam", c.get("name", "Cafeïne gel"))
                    moment_items[1].append({"label": f"⚡ <b>{_c_naam}</b> ({c['kh']}g)", "kh": c["kh"]})
                    uur_kh += c["kh"]
                    cafeine_gebruikt = True

                if "verspreid" in cafe_strat and not is_last and pool.get("cafe") and u % 2 == 1:
                    c = _pool_item("cafe")
                    moment_items[2].append({"label": f"⚡ <b>{c.get('naam', c.get('name','Cafeïne gel'))}</b> ({c['kh']}g)", "kh": c["kh"]})
                    uur_kh += c["kh"]

                if pool.get("vast") and uur_kh < cur_min_kh:
                    item = pool["vast"][vast_idx % len(pool["vast"])]
                    moment_items[2].append({"label": f"🍱 <b>{item.get('naam', item.get('name','Vast'))}</b> ({item['kh']}g)", "kh": item["kh"]})
                    uur_kh += item["kh"]
                    vast_idx += 1

                if pool.get("gels") and uur_kh < cur_min_kh:
                    g = _pool_item("gels")
                    moment_items[3].append({"label": f"🧪 <b>{g.get('naam', g.get('name','Gel'))}</b> ({g['kh']}g)", "kh": g["kh"]})
                    uur_kh += g["kh"]

                status_color = "#22c55e" if uur_kh >= cur_min_kh else "#f59e0b"
                rows_html = ""
                for m_num in [1, 2, 3]:
                    min_label = f"+{m_num * 20}min"
                    if is_last and m_num > 1:
                        item_text = '<span style="color:#94a3b8;">Enkel spoelen / water.</span>'
                    elif moment_items[m_num]:
                        item_text = " + ".join(i["label"] for i in moment_items[m_num])
                    else:
                        item_text = f"🥤 {vocht_per_m}ml water"

                    rows_html += f"""
                    <div style="display:flex; gap:10px; margin-bottom:8px; font-size:0.83rem;">
                        <span style="color:#3b82f6; font-weight:700; min-width:55px;">{min_label}</span>
                        <span style="color:#1e293b;">{item_text}</span>
                    </div>"""

                st.markdown(f"""
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:14px; padding:16px; margin-bottom:14px; color:#1e293b;">
                    <div style="display:flex; justify-content:space-between; font-weight:900; font-size:0.92rem; 
                         border-bottom:2px solid #3b82f6; padding-bottom:6px; margin-bottom:10px;">
                        <span>UUR {u+1} — {uur_label}</span>
                        <span style="font-size:0.72rem; color:#64748b;">Doel: {cur_min_kh}–{cur_max_kh}g KH</span>
                    </div>
                    {rows_html}
                    <div style="text-align:right; font-weight:700; color:{status_color}; font-size:0.8rem; 
                         padding-top:8px; border-top:1px dashed #cbd5e1; margin-top:4px;">
                        TOTAAL: {round(uur_kh)}g KH &nbsp;|&nbsp; DOEL: {cur_min_kh}–{cur_max_kh}g
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:14px; text-align:center;">
                <div style="color:#94a3b8; font-size:0.82rem;">
                    💧 Vocht/moment: <b style="color:white;">{vocht_per_m}ml</b> &nbsp;|&nbsp;
                    🌡️ {temp}°C &nbsp;|&nbsp;
                    💦 {vochtigheid}% vochtigheid &nbsp;|&nbsp;
                    ⛰️ {hoogte}m
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # ── PDF Download knop ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('''
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid #334155;
         border-radius:16px;padding:20px 24px;text-align:center;margin-bottom:16px;">
        <div style="font-size:1.5rem;margin-bottom:8px;">📄</div>
        <div style="font-weight:900;color:#f8fafc;font-size:1rem;margin-bottom:6px;">
            Genereer jouw Race Nutrition Rapport
        </div>
        <div style="color:#64748b;font-size:0.82rem;">
            Alle keuzes, richtlijnen en wetenschappelijke adviezen in één overzichtelijk rapport.
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if st.button("📄  GENEREER PLAN", key="sum_pdf", use_container_width=True):
        with st.spinner("Rapport wordt gegenereerd..."):
            try:
                gebruiker_naam = st.session_state.get("current_user", {}).get("name", "Atleet")
                data_met_logo = dict(data)
                data_met_logo["logo_b64"]  = st.session_state.get("coach_logo_b64", "")
                data_met_logo["logo_mime"] = st.session_state.get("coach_logo_mime", "image/png")
                html_str     = _genereer_html(data_met_logo, gebruiker_naam)
                atleet       = data.get("atleet_naam", gebruiker_naam).replace(" ", "_")
                wedstrijd    = data.get("wedstrijd_naam", "race").replace(" ", "_")
                bestandsnaam = f"Carboo_RacePlan_{atleet}_{wedstrijd}.html"
                st.success("✅ Rapport klaar!")
            except Exception as e:
                st.error(f"Fout bij genereren rapport: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Terug naar raceplan", key="sum_prev"):
            st.session_state.coach_stap = 5
            st.rerun()
    with col2:
        if st.button("🔄 Nieuw plan starten", key="sum_new"):
            for k in list(st.session_state.keys()):
                if k.startswith("cl_") or k.startswith("rp_") or k.startswith("rd_") or k.startswith("p_") or k.startswith("w_"):
                    del st.session_state[k]
            st.session_state.coach_stap = 0
            st.session_state.coach_data = {}
            st.rerun()
    with col3:
        if st.button("🏠 Terug naar menu", key="sum_menu"):
            st.session_state.module = "menu"
            st.rerun()


# ─── MAIN RENDER ─────────────────────────────────────────────────────────────

def render_coach(user: dict):
    naam = user.get("name", "Atleet")

    if "coach_stap" not in st.session_state:
        st.session_state.coach_stap = 0
    if "coach_data" not in st.session_state:
        st.session_state.coach_data = {}

    stap = st.session_state.coach_stap
    stap_idx = min(stap, len(STAPPEN) - 1)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:16px; padding:18px 22px; 
         margin-bottom:20px; border-left:5px solid #f97316; display:flex; justify-content:space-between;">
        <div>
            <div style="font-size:0.68rem; color:#f97316; font-weight:800; letter-spacing:2px;">CARBOO COACH</div>
            <div style="font-size:1.1rem; font-weight:900; color:#f8fafc; margin-top:2px;">
                {STAPPEN[stap_idx].replace("_"," ").upper()}
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.68rem; color:#64748b;">Gebruiker</div>
            <div style="font-size:0.9rem; font-weight:700; color:#f8fafc;">{naam}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _progress_bar(stap_idx)

    if stap == 0:
        _stap_welkom(naam)
    elif stap == 1:
        _stap_profiel(naam)
    elif stap == 2:
        _stap_wedstrijd()
    elif stap == 3:
        _stap_carboloading()
    elif stap == 4:
        _stap_racedag()
    elif stap == 5:
        _stap_raceplan()
    elif stap == 6:
        _stap_samenvatting()
