from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx
from supabase import create_client, Client

app = FastAPI(title="Carboo API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://carboo-next.vercel.app",
        "https://carboo.app",
        "https://www.carboo.app",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise HTTPException(500, "Supabase niet geconfigureerd")
    return create_client(url, key)

async def get_current_user(request: Request, supabase: Client = Depends(get_supabase)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Niet ingelogd")
    try:
        user = supabase.auth.get_user(token)
        return user.user
    except Exception:
        raise HTTPException(401, "Ongeldige token")

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ═══ MODULE 1 — RACE NUTRITION COACH ═════════════════════════════════════════

class CoachData(BaseModel):
    atleet_naam: str
    wedstrijd_naam: str
    gewicht: float
    sport: str
    niveau: str
    ervaring: str
    wedstrijd_datum: str
    start_time: str
    eind_time: str
    totale_min: int
    temp: int
    vochtigheid: int
    hoogte: int
    min_kh: int
    max_kh: int
    dag_target: Optional[int] = None
    factor: Optional[int] = None
    cl_waarden: Optional[dict] = None
    cl_eigen: Optional[dict] = None
    carboloading: Optional[dict] = None
    cl_status: Optional[dict] = None
    ontbijt_kh: Optional[int] = None
    ontbijt_timing: Optional[str] = None
    ontbijt_tijd: Optional[str] = None
    maaltijd_moment: Optional[str] = None
    rd_waarden: Optional[dict] = None
    rd_eigen: Optional[list] = None
    pool: Optional[dict] = None
    preview_uren: Optional[dict] = None
    preview_comments: Optional[dict] = None
    logo_b64: Optional[str] = None
    logo_mime: Optional[str] = "image/png"

class CoachRapportRequest(BaseModel):
    coach_data: CoachData
    gebruiker_naam: str

@app.post("/api/coach/bereken-kh")
def bereken_kh(sport: str, minuten: int):
    from coach_logic import get_kh_range
    mn, mx = get_kh_range(sport, minuten)
    return {"min_kh": mn, "max_kh": mx}

@app.post("/api/coach/genereer-rapport")
async def genereer_rapport(req: CoachRapportRequest, user=Depends(get_current_user)):
    from coach_logic import genereer_html
    try:
        html = genereer_html(req.coach_data.dict(), req.gebruiker_naam)
        return {"html": html}
    except Exception as e:
        raise HTTPException(500, f"Rapport generatie mislukt: {e}")

@app.post("/api/coach/genereer-pdf")
async def genereer_pdf(req: CoachRapportRequest, user=Depends(get_current_user)):
    from coach_logic import genereer_pdf
    try:
        pdf_bytes = genereer_pdf(req.coach_data.dict(), req.gebruiker_naam)
        atleet = req.coach_data.atleet_naam.replace(" ", "_")
        wedstrijd = req.coach_data.wedstrijd_naam.replace(" ", "_")
        filename = f"Carboo_RacePlan_{atleet}_{wedstrijd}.pdf"
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(500, f"PDF generatie mislukt: {e}")

@app.post("/api/coach/sla-plan-op")
async def sla_plan_op(req: CoachRapportRequest, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_plannen").upsert({
        "user_id": user.id,
        "coach_data": req.coach_data.dict(),
    }, on_conflict="user_id").execute()
    return {"status": "opgeslagen"}

@app.get("/api/coach/haal-plan-op")
async def haal_plan_op(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_plannen").select("coach_data").eq("user_id", user.id).limit(1).execute()
    return {"plan": r.data[0]["coach_data"] if r.data else None}


# ═══ MODULE 2 — FUELC ════════════════════════════════════════════════════════

class FuelcProfiel(BaseModel):
    geslacht: str
    leeftijd: int
    gewicht_kg: float
    lengte_cm: int
    activiteit: str
    doelstelling: str
    bmr: Optional[int] = None
    tdee_basis: Optional[int] = None
    energie_doel: Optional[int] = None
    kh_doel_pct: Optional[int] = 50
    eiwit_doel_pct: Optional[int] = 25
    vet_doel_pct: Optional[int] = 25
    eet_patroon: Optional[str] = "Klassiek (3 maaltijden)"
    momenten_tijden: Optional[str] = None
    td_0: Optional[bool] = False
    td_1: Optional[bool] = False
    td_2: Optional[bool] = False

class TrainingData(BaseModel):
    datum: str
    sport: str
    duur_min: int
    afstand_km: Optional[float] = 0
    kcal_verbranding: Optional[int] = 0
    zone_verdeling: Optional[str] = None
    notitie: Optional[str] = None
    starttijd: Optional[str] = "07:00"

class DagboekItem(BaseModel):
    datum: str
    moment: int
    naam: str
    hoeveelheid_g: float
    kcal: float
    kh_g: float
    eiwit_g: float
    vet_g: float
    vezels_g: Optional[float] = 0
    suikers_g: Optional[float] = 0
    verz_g: Optional[float] = 0
    natrium_mg: Optional[float] = 0
    kalium_mg: Optional[float] = 0
    calcium_mg: Optional[float] = 0
    ijzer_mg: Optional[float] = 0
    vitd_mcg: Optional[float] = 0
    vitb12_mcg: Optional[float] = 0
    omega3_g: Optional[float] = 0
    gi: Optional[int] = None
    categorie: Optional[str] = None
    product_id: Optional[str] = None

class WelzijnData(BaseModel):
    datum: str
    energie_score: Optional[int] = None
    stemming: Optional[int] = None
    stress: Optional[int] = None
    slaap_uur: Optional[float] = None
    slaap_kwaliteit: Optional[int] = None
    spierpijn: Optional[int] = None
    hf_rust: Optional[int] = None
    hrv: Optional[int] = None
    honger: Optional[int] = None
    gi_klachten: Optional[bool] = False
    gehydrateerd: Optional[bool] = True
    rpe: Optional[int] = None
    energiek_training: Optional[bool] = None
    gewicht_kg: Optional[float] = None

@app.get("/api/fuelc/profiel")
async def get_fuelc_profiel(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_profiel").select("*").eq("user_id", user.id).execute()
    return {"profiel": r.data[0] if r.data else None}

@app.post("/api/fuelc/profiel")
async def sla_fuelc_profiel(profiel: FuelcProfiel, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = profiel.dict()
    data["user_id"] = user.id
    bestaand = supabase.table("fuelc_profiel").select("id").eq("user_id", user.id).execute()
    if bestaand.data:
        supabase.table("fuelc_profiel").update(data).eq("user_id", user.id).execute()
    else:
        supabase.table("fuelc_profiel").insert(data).execute()
    return {"status": "opgeslagen"}

@app.get("/api/fuelc/trainingen")
async def get_trainingen(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_trainingen").select("*").eq("user_id", user.id).order("datum", desc=True).limit(60).execute()
    return {"trainingen": r.data or []}

@app.post("/api/fuelc/trainingen")
async def voeg_training_toe(training: TrainingData, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = training.dict()
    data["user_id"] = user.id
    data["bron"] = "manueel"
    supabase.table("fuelc_trainingen").insert(data).execute()
    return {"status": "opgeslagen"}

@app.delete("/api/fuelc/trainingen/{training_id}")
async def verwijder_training(training_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_trainingen").delete().eq("id", training_id).eq("user_id", user.id).execute()
    return {"status": "verwijderd"}


# ─── COACH ZONE ───────────────────────────────────────────────────────────────

import secrets

class CoachProfiel(BaseModel):
    naam: str
    bio: Optional[str] = ""
    specialisatie: Optional[str] = ""
    email: str

class PrivacyInstellingen(BaseModel):
    relatie_id: str
    fuelc_dagschema: bool = True
    fuelc_analyses: bool = False
    macros: bool = False
    gewicht: bool = False
    race_plannen: bool = True
    train_gut: bool = False
    dossier: bool = False

class CoachOpmerking(BaseModel):
    relatie_id: str
    klant_id: str
    tekst: str
    item_type: Optional[str] = "algemeen"
    item_id: Optional[str] = None
    item_label: Optional[str] = None

class CoachReactie(BaseModel):
    opmerking_id: str
    tekst: str

class CoachNotitie(BaseModel):
    klant_id: str
    tekst: str


# ─── ADMIN + COACH AANVRAGEN ─────────────────────────────────────────────────

class CoachAanvraag(BaseModel):
    naam: str
    email: str
    bio: Optional[str] = ""
    specialisatie: Optional[str] = ""

async def is_admin(user, supabase: Client) -> bool:
    r = supabase.table("carboo_admins").select("user_id").eq("user_id", user.id).execute()
    return bool(r.data)

@app.get("/api/admin/check")
async def check_admin(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    return {"is_admin": await is_admin(user, supabase)}

@app.get("/api/admin/aanvragen")
async def get_aanvragen(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    r = supabase.table("carboo_coach_aanvragen").select("*").order("aangemaakt", desc=True).execute()
    return {"aanvragen": r.data or []}

@app.post("/api/admin/aanvragen/{aanvraag_id}/keur-goed")
async def keur_goed(aanvraag_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    from datetime import datetime
    aanvraag = supabase.table("carboo_coach_aanvragen").select("*").eq("id", aanvraag_id).execute()
    if not aanvraag.data:
        raise HTTPException(404, "Aanvraag niet gevonden")
    a = aanvraag.data[0]
    # Maak coach profiel aan of update verified
    bestaand = supabase.table("carboo_coaches").select("id").eq("user_id", a["user_id"]).execute()
    if bestaand.data:
        supabase.table("carboo_coaches").update({"verified": True}).eq("user_id", a["user_id"]).execute()
    else:
        supabase.table("carboo_coaches").insert({
            "user_id": a["user_id"], "naam": a["naam"], "email": a["email"],
            "bio": a["bio"] or "", "specialisatie": a["specialisatie"] or "", "verified": True
        }).execute()
    supabase.table("carboo_coach_aanvragen").update({
        "status": "goedgekeurd", "behandeld": datetime.now().isoformat()
    }).eq("id", aanvraag_id).execute()
    return {"ok": True}

@app.post("/api/admin/aanvragen/{aanvraag_id}/weiger")
async def weiger_aanvraag(aanvraag_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    from datetime import datetime
    supabase.table("carboo_coach_aanvragen").update({
        "status": "geweigerd", "behandeld": datetime.now().isoformat()
    }).eq("id", aanvraag_id).execute()
    return {"ok": True}

@app.get("/api/coach/aanvraag")
async def get_mijn_aanvraag(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coach_aanvragen").select("*").eq("user_id", user.id).execute()
    return {"aanvraag": r.data[0] if r.data else None}

@app.post("/api/coach/aanvraag")
async def dien_aanvraag_in(item: CoachAanvraag, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    bestaand = supabase.table("carboo_coach_aanvragen").select("id,status").eq("user_id", user.id).execute()
    if bestaand.data:
        bestaand_status = bestaand.data[0]["status"]
        if bestaand_status == "goedgekeurd":
            raise HTTPException(400, "Aanvraag al goedgekeurd")
        if bestaand_status == "pending":
            raise HTTPException(400, "Aanvraag al ingediend — wacht op goedkeuring")
        # Geweigerd — laat opnieuw indienen
        supabase.table("carboo_coach_aanvragen").update({
            "naam": item.naam, "email": item.email,
            "bio": item.bio or "", "specialisatie": item.specialisatie or "",
            "status": "pending", "behandeld": None
        }).eq("user_id", user.id).execute()
    else:
        supabase.table("carboo_coach_aanvragen").insert({
            "user_id": user.id, "naam": item.naam, "email": item.email,
            "bio": item.bio or "", "specialisatie": item.specialisatie or ""
        }).execute()
    return {"ok": True}

# ── Coach profiel ──────────────────────────────────────────────────────────────

@app.post("/api/admin/coach-aanmaken")
async def admin_maak_coach(item: CoachProfiel, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    # Zoek user op basis van email
    gebruiker = supabase.auth.admin.list_users()
    klant_id = None
    for u in (gebruiker or []):
        if hasattr(u, 'email') and u.email == item.email:
            klant_id = u.id
            break
    if not klant_id:
        raise HTTPException(404, f"Geen Carboo account gevonden voor {item.email}")
    bestaand = supabase.table("carboo_coaches").select("id").eq("user_id", klant_id).execute()
    if bestaand.data:
        supabase.table("carboo_coaches").update({"verified": True, "naam": item.naam, "email": item.email}).eq("user_id", klant_id).execute()
    else:
        supabase.table("carboo_coaches").insert({"user_id": klant_id, "naam": item.naam, "email": item.email, "bio": item.bio or "", "specialisatie": item.specialisatie or "", "verified": True}).execute()
    return {"ok": True}

@app.delete("/api/admin/coach/{coach_id}")
async def admin_verwijder_coach(coach_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    supabase.table("carboo_coaches").update({"verified": False}).eq("id", coach_id).execute()
    return {"ok": True}

@app.get("/api/coach/profiel")
async def get_coach_profiel(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coaches").select("*").eq("user_id", user.id).execute()
    return {"profiel": r.data[0] if r.data else None}

@app.post("/api/coach/profiel")
async def sla_coach_profiel(item: CoachProfiel, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = {"user_id": user.id, "naam": item.naam, "bio": item.bio or "", "specialisatie": item.specialisatie or "", "email": item.email}
    bestaand = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if bestaand.data:
        supabase.table("carboo_coaches").update(data).eq("user_id", user.id).execute()
    else:
        supabase.table("carboo_coaches").insert(data).execute()
    profiel = supabase.table("carboo_coaches").select("*").eq("user_id", user.id).execute()
    return {"ok": True, "profiel": profiel.data[0] if profiel.data else None}

# ── Invite systeem ──────────────────────────────────────────────────────────────

@app.post("/api/coach/invite/genereer")
async def genereer_invite(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id,verified").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(400, "Maak eerst een coach profiel aan")
    if not coach.data[0].get("verified"):
        raise HTTPException(403, "Coach account nog niet goedgekeurd door admin")
    coach_id = coach.data[0]["id"]
    from datetime import datetime, timedelta
    # Verwijder alle bestaande pending invites van deze coach
    supabase.table("carboo_coach_klanten").delete().eq("coach_id", coach_id).eq("status", "pending").execute()
    token = secrets.token_urlsafe(24)
    expires = (datetime.now() + timedelta(days=7)).isoformat()
    supabase.table("carboo_coach_klanten").insert({
        "coach_id": coach_id,
        "klant_id": None,
        "status": "pending",
        "invite_token": token,
        "invite_expires": expires
    }).execute()
    return {"token": token, "expires": expires, "link": f"/app/coach-zone/invite/{token}"}

@app.get("/api/coach/invite/{token}")
async def get_invite_info(token: str, supabase: Client = Depends(get_supabase)):
    from datetime import datetime
    r = supabase.table("carboo_coach_klanten").select("*, carboo_coaches(naam,bio,specialisatie,email)").eq("invite_token", token).eq("status", "pending").execute()
    if not r.data:
        raise HTTPException(404, "Uitnodiging niet gevonden of verlopen")
    relatie = r.data[0]
    if relatie.get("invite_expires") and relatie["invite_expires"] < datetime.now().isoformat():
        raise HTTPException(410, "Uitnodiging verlopen")
    return {"relatie": relatie}

@app.post("/api/coach/invite/{token}/accepteer")
async def accepteer_invite(token: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    from datetime import datetime
    r = supabase.table("carboo_coach_klanten").select("*").eq("invite_token", token).eq("status", "pending").execute()
    if not r.data:
        raise HTTPException(404, "Uitnodiging niet gevonden")
    relatie = r.data[0]
    if relatie["invite_expires"] < datetime.now().isoformat():
        raise HTTPException(410, "Uitnodiging verlopen")
    # Update relatie
    supabase.table("carboo_coach_klanten").update({
        "klant_id": user.id, "status": "actief", "bijgewerkt": "now()"
    }).eq("id", relatie["id"]).execute()
    # Maak standaard privacy instellingen aan
    supabase.table("carboo_coach_privacy").insert({
        "relatie_id": relatie["id"], "klant_id": user.id,
        "fuelc_dagschema": True, "fuelc_analyses": False,
        "race_plannen": True, "train_gut": False, "dossier": False
    }).execute()
    return {"ok": True, "relatie_id": relatie["id"]}

@app.post("/api/coach/invite/{token}/weiger")
async def weiger_invite(token: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_coach_klanten").update({"status": "geweigerd", "bijgewerkt": "now()"}).eq("invite_token", token).execute()
    return {"ok": True}

# ── Klant: coaches beheren ─────────────────────────────────────────────────────

@app.get("/api/coach/mijn-coaches")
async def get_mijn_coaches(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coach_klanten").select("*, carboo_coaches(naam,bio,specialisatie,email)").eq("klant_id", user.id).eq("status", "actief").execute()
    return {"coaches": r.data or []}

@app.delete("/api/coach/mijn-coaches/{relatie_id}")
async def verwijder_coach(relatie_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_coach_klanten").update({"status": "ingetrokken", "bijgewerkt": "now()"}).eq("id", relatie_id).eq("klant_id", user.id).execute()
    return {"ok": True}

# ── Privacy instellingen ────────────────────────────────────────────────────────

@app.get("/api/coach/privacy/{relatie_id}")
async def get_privacy(relatie_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coach_privacy").select("*").eq("relatie_id", relatie_id).eq("klant_id", user.id).execute()
    return {"privacy": r.data[0] if r.data else None}

@app.put("/api/coach/privacy/{relatie_id}")
async def update_privacy(relatie_id: str, item: PrivacyInstellingen, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_coach_privacy").update({
        "fuelc_dagschema": item.fuelc_dagschema, "fuelc_analyses": item.fuelc_analyses,
        "macros": item.macros, "gewicht": item.gewicht,
        "race_plannen": item.race_plannen, "train_gut": item.train_gut,
        "dossier": item.dossier, "bijgewerkt": "now()"
    }).eq("relatie_id", relatie_id).eq("klant_id", user.id).execute()
    return {"ok": True}

# ── Coach: klanten overzicht ────────────────────────────────────────────────────

@app.get("/api/coach/mijn-klanten")
async def get_mijn_klanten(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        return {"klanten": []}
    coach_id = coach.data[0]["id"]
    r = supabase.table("carboo_coach_klanten").select("*, carboo_coach_privacy(*)").eq("coach_id", coach_id).eq("status", "actief").execute()
    return {"klanten": r.data or []}

@app.get("/api/coach/klant/{klant_id}/data")
async def get_klant_data(klant_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Coach leest klantdata — enkel wat privacy toelaat."""
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(403, "Geen coach account")
    coach_id = coach.data[0]["id"]
    relatie = supabase.table("carboo_coach_klanten").select("*, carboo_coach_privacy(*)").eq("coach_id", coach_id).eq("klant_id", klant_id).eq("status", "actief").execute()
    if not relatie.data:
        raise HTTPException(403, "Geen toegang tot deze klant")
    privacy = relatie.data[0].get("carboo_coach_privacy") or {}
    if isinstance(privacy, list) and privacy:
        privacy = privacy[0]
    result: dict = {"relatie_id": relatie.data[0]["id"], "privacy": privacy}
    # Laad data op basis van privacy
    if privacy.get("fuelc_dagschema"):
        dag = supabase.table("fuelc_dagboek").select("datum,naam,kcal,kh_g,eiwit_g,vet_g").eq("user_id", klant_id).order("datum", desc=True).limit(30).execute()
        result["dagschema"] = dag.data or []
    if privacy.get("race_plannen"):
        rap = supabase.table("carboo_rapporten").select("id,naam,type,meta,datum").eq("user_id", klant_id).order("datum", desc=True).limit(10).execute()
        result["race_plannen"] = rap.data or []
    if privacy.get("train_gut"):
        gut = supabase.table("carboo_gut_sessies").select("*").eq("user_id", klant_id).order("datum", desc=True).limit(20).execute()
        result["gut_sessies"] = gut.data or []
        wm = supabase.table("carboo_gut_winkelmandje").select("*").eq("user_id", klant_id).execute()
        result["gut_winkelmandje"] = wm.data or []
    if privacy.get("dossier"):
        dos = supabase.table("carboo_rapporten").select("id,naam,type,meta,datum").eq("user_id", klant_id).order("datum", desc=True).limit(10).execute()
        result["dossier"] = dos.data or []
    if privacy.get("fuelc_analyses"):
        if "dagschema" not in result:
            dag = supabase.table("fuelc_dagboek").select("datum,naam,kcal,kh_g,eiwit_g,vet_g,vezels_g").eq("user_id", klant_id).order("datum", desc=True).limit(30).execute()
            result["dagschema"] = dag.data or []

    if privacy.get("macros"):
        dag = supabase.table("fuelc_dagboek").select("datum,kcal,kh_g,eiwit_g,vet_g").eq("user_id", klant_id).order("datum", desc=True).limit(70).execute()
        items = dag.data or []
        # Groepeer per dag
        per_dag: dict = {}
        for item in items:
            d = item.get("datum", "")
            if d not in per_dag:
                per_dag[d] = {"kcal": 0, "kh": 0, "eiwit": 0, "vet": 0}
            per_dag[d]["kcal"] += item.get("kcal", 0) or 0
            per_dag[d]["kh"] += item.get("kh_g", 0) or 0
            per_dag[d]["eiwit"] += item.get("eiwit_g", 0) or 0
            per_dag[d]["vet"] += item.get("vet_g", 0) or 0
        if per_dag:
            n = len(per_dag)
            result["macros_data"] = {
                "gem_kcal": round(sum(d["kcal"] for d in per_dag.values()) / n),
                "gem_kh": round(sum(d["kh"] for d in per_dag.values()) / n),
                "gem_eiwit": round(sum(d["eiwit"] for d in per_dag.values()) / n),
                "gem_vet": round(sum(d["vet"] for d in per_dag.values()) / n),
                "dagen": n,
            }

    if privacy.get("gewicht"):
        gew = supabase.table("fuelc_dagboek_welzijn").select("datum,gewicht_kg").eq("user_id", klant_id).not_.is_("gewicht_kg", "null").order("datum", desc=True).limit(20).execute()
        result["gewicht_data"] = gew.data or []

    return result

# ── Opmerkingen ─────────────────────────────────────────────────────────────────

@app.post("/api/coach/opmerkingen")
async def plaats_opmerking(item: CoachOpmerking, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(403, "Geen coach account")
    coach_id = coach.data[0]["id"]
    # Verifieer relatie
    relatie = supabase.table("carboo_coach_klanten").select("id").eq("id", item.relatie_id).eq("coach_id", coach_id).eq("status", "actief").execute()
    if not relatie.data:
        raise HTTPException(403, "Geen actieve relatie met deze klant")
    r = supabase.table("carboo_coach_opmerkingen").insert({
        "relatie_id": item.relatie_id, "coach_id": coach_id,
        "klant_id": item.klant_id, "tekst": item.tekst,
        "item_type": item.item_type or "algemeen",
        "item_id": item.item_id, "item_label": item.item_label,
    }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.get("/api/coach/opmerkingen/coach")
async def get_opmerkingen_coach(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        return {"opmerkingen": []}
    coach_id = coach.data[0]["id"]
    r = supabase.table("carboo_coach_opmerkingen").select("*, carboo_coach_reacties(*)").eq("coach_id", coach_id).order("aangemaakt", desc=True).limit(50).execute()
    return {"opmerkingen": r.data or []}

@app.get("/api/coach/opmerkingen/klant")
async def get_opmerkingen_klant(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_coach_opmerkingen").select("*, carboo_coaches(naam), carboo_coach_reacties(*)").eq("klant_id", user.id).order("aangemaakt", desc=True).limit(50).execute()
    # Tel ongelezen
    ongelezen = sum(1 for o in (r.data or []) if not o.get("gelezen"))
    return {"opmerkingen": r.data or [], "ongelezen": ongelezen}

@app.put("/api/coach/opmerkingen/{opmerking_id}/gelezen")
async def markeer_gelezen(opmerking_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_coach_opmerkingen").update({"gelezen": True}).eq("id", opmerking_id).eq("klant_id", user.id).execute()
    return {"ok": True}

@app.delete("/api/coach/opmerkingen/{opmerking_id}")
async def verwijder_opmerking(opmerking_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        supabase.table("carboo_coach_opmerkingen").delete().eq("id", opmerking_id).eq("coach_id", coach.data[0]["id"]).execute()
    return {"ok": True}

@app.post("/api/coach/reacties")
async def plaats_reactie(item: CoachReactie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    # Verifieer dat klant eigenaar is van de opmerking
    opm = supabase.table("carboo_coach_opmerkingen").select("id").eq("id", item.opmerking_id).eq("klant_id", user.id).execute()
    if not opm.data:
        raise HTTPException(403, "Geen toegang")
    supabase.table("carboo_coach_reacties").insert({"opmerking_id": item.opmerking_id, "klant_id": user.id, "tekst": item.tekst}).execute()
    supabase.table("carboo_coach_opmerkingen").update({"gelezen": True}).eq("id", item.opmerking_id).execute()
    return {"ok": True}

# ── Privé notities ─────────────────────────────────────────────────────────────

@app.get("/api/coach/notities/{klant_id}")
async def get_notities(klant_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        return {"notities": []}
    r = supabase.table("carboo_coach_notities").select("*").eq("coach_id", coach.data[0]["id"]).eq("klant_id", klant_id).order("bijgewerkt", desc=True).execute()
    return {"notities": r.data or []}

@app.post("/api/coach/notities")
async def sla_notitie(item: CoachNotitie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(403, "Geen coach account")
    supabase.table("carboo_coach_notities").insert({"coach_id": coach.data[0]["id"], "klant_id": item.klant_id, "tekst": item.tekst}).execute()
    return {"ok": True}

@app.delete("/api/coach/notities/{notitie_id}")
async def verwijder_notitie(notitie_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        supabase.table("carboo_coach_notities").delete().eq("id", notitie_id).eq("coach_id", coach.data[0]["id"]).execute()
    return {"ok": True}


# ─── DOSSIER / RAPPORTEN ──────────────────────────────────────────────────────

class RapportItem(BaseModel):
    naam: str
    type: str  # "race_plan" | "gut_log" | "analyse"
    html: str
    meta: Optional[dict] = {}

# ─── TRAIN THE GUT ───────────────────────────────────────────────────────────

class GutProtocol(BaseModel):
    sport: str
    wedstrijd: Optional[str] = ""
    niveau: str
    ervaring: str
    wedstrijd_datum: Optional[str] = None
    trainingen_per_week: int = 1

class GutSessie(BaseModel):
    datum: Optional[str] = None
    sport: Optional[str] = ""
    duur_min: int
    intensiteit: str
    week_nummer: int
    temp_c: Optional[int] = None
    vochtigheid_pct: Optional[int] = None
    notitie: Optional[str] = ""
    energie_score: Optional[int] = None
    prestatie_score: Optional[int] = None
    wil_doorgaan: Optional[bool] = None
    dosis_aanpassen: Optional[str] = "Zelfde"
    producten: Optional[list] = []

class WinkelmandjeItem(BaseModel):
    naam: str
    categorie: Optional[str] = ""
    kh_gram: int
    max_kh_uur: Optional[int] = None
    gem_gi_score: Optional[float] = None
    aantal_sessies: Optional[int] = 1
    sport: Optional[str] = ""

def bereken_startdosis(niveau: str, ervaring: str, sport: str) -> dict:
    """Bereken start- en maxdosis op basis van niveau, ervaring en sport."""
    # Basisdosis per ervaringsniveau
    basis = {"Beginner": 20, "Gevorderd": 40, "Ervaren": 60}.get(ervaring, 20)
    # Niveau-multiplier
    mult = {"Recreant": 1.0, "Competitief": 1.3, "Professioneel": 1.6}.get(niveau, 1.0)
    # Sport-correctie: lopen GI-gevoeliger
    sport_factor = 0.8 if sport in ["Lopen"] else 1.0
    startdosis = max(20, round(basis * sport_factor / 5) * 5)
    # Max dosis per niveau
    max_map = {"Recreant": 60, "Competitief": 90, "Professioneel": 120}
    max_dosis = max_map.get(niveau, 60)
    if sport == "Lopen":
        max_dosis = round(max_dosis * 0.85 / 5) * 5
    # Ratio aanbeveling
    if startdosis < 60:
        ratio = "Geen vereiste — glucose/maltodextrine volstaat"
    elif startdosis < 90:
        ratio = "2:1 glucose:fructose"
    else:
        ratio = "1:0.8 glucose:fructose"
    return {
        "startdosis": startdosis,
        "max_dosis": max_dosis,
        "ratio_advies": ratio,
        "wk12_dosis": startdosis,
        "wk34_dosis": min(startdosis + 15, max_dosis),
        "wk56_dosis": min(startdosis + 30, max_dosis),
    }

@app.get("/api/gut/protocol")
async def get_protocol(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_gut_protocol").select("*").eq("user_id", user.id).execute()
    return {"protocol": r.data[0] if r.data else None}

@app.post("/api/gut/protocol")
async def sla_protocol_op(item: GutProtocol, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    dosis = bereken_startdosis(item.niveau, item.ervaring, item.sport)
    data = {
        "user_id": user.id,
        "sport": item.sport,
        "wedstrijd": item.wedstrijd or "",
        "niveau": item.niveau,
        "ervaring": item.ervaring,
        "wedstrijd_datum": item.wedstrijd_datum,
        "trainingen_per_week": item.trainingen_per_week,
        "startdosis_g_uur": dosis["startdosis"],
        "max_dosis_g_uur": dosis["max_dosis"],
        "week_huidig": 1,
        "bijgewerkt": "now()",
    }
    # Upsert op user_id
    bestaand = supabase.table("carboo_gut_protocol").select("id").eq("user_id", user.id).execute()
    if bestaand.data:
        supabase.table("carboo_gut_protocol").update(data).eq("user_id", user.id).execute()
    else:
        supabase.table("carboo_gut_protocol").insert(data).execute()
    return {"ok": True, "dosis": dosis}

@app.get("/api/gut/sessies")
async def get_sessies(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    sessies = supabase.table("carboo_gut_sessies").select("*").eq("user_id", user.id).order("datum", desc=True).execute()
    sessie_ids = [s["id"] for s in (sessies.data or [])]
    producten = []
    if sessie_ids:
        producten = supabase.table("carboo_gut_producten").select("*").in_("sessie_id", sessie_ids).execute().data or []
    prod_map: dict = {}
    for p in producten:
        prod_map.setdefault(p["sessie_id"], []).append(p)
    result = []
    for s in (sessies.data or []):
        s["producten"] = prod_map.get(s["id"], [])
        result.append(s)
    return {"sessies": result}

@app.post("/api/gut/sessies")
async def sla_sessie_op(item: GutSessie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    from datetime import date
    sessie_data = {
        "user_id": user.id,
        "datum": item.datum or str(date.today()),
        "sport": item.sport or "",
        "duur_min": item.duur_min,
        "intensiteit": item.intensiteit,
        "week_nummer": item.week_nummer,
        "temp_c": item.temp_c,
        "vochtigheid_pct": item.vochtigheid_pct,
        "notitie": item.notitie or "",
        "energie_score": item.energie_score,
        "prestatie_score": item.prestatie_score,
        "wil_doorgaan": item.wil_doorgaan,
        "dosis_aanpassen": item.dosis_aanpassen or "Zelfde",
    }
    r = supabase.table("carboo_gut_sessies").insert(sessie_data).execute()
    sessie_id = r.data[0]["id"] if r.data else None
    if sessie_id and item.producten:
        for p in item.producten:
            supabase.table("carboo_gut_producten").insert({
                "sessie_id": sessie_id,
                "user_id": user.id,
                "naam": p.get("naam", ""),
                "categorie": p.get("categorie", ""),
                "kh_gram": p.get("kh_gram", 0),
                "hoeveelheid_ml_g": p.get("hoeveelheid_ml_g"),
                "tijdstip_min": p.get("tijdstip_min"),
                "gi_totaal": p.get("gi_totaal"),
                "gi_misselijkheid": p.get("gi_misselijkheid"),
                "gi_krampen": p.get("gi_krampen"),
                "gi_opgeblazen": p.get("gi_opgeblazen"),
                "gi_diarree": p.get("gi_diarree"),
            }).execute()
    # Update week_huidig in protocol
    supabase.table("carboo_gut_protocol").update({
        "week_huidig": item.week_nummer,
        "bijgewerkt": "now()"
    }).eq("user_id", user.id).execute()
    return {"ok": True, "sessie_id": sessie_id}

@app.delete("/api/gut/sessies/{sessie_id}")
async def verwijder_sessie(sessie_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_gut_sessies").delete().eq("user_id", user.id).eq("id", sessie_id).execute()
    return {"ok": True}

@app.get("/api/gut/winkelmandje")
async def get_winkelmandje(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_gut_winkelmandje").select("*").eq("user_id", user.id).order("goedgekeurd_op", desc=True).execute()
    return {"items": r.data or []}

@app.post("/api/gut/winkelmandje")
async def voeg_toe_winkelmandje(item: WinkelmandjeItem, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = {
        "user_id": user.id,
        "naam": item.naam,
        "categorie": item.categorie or "",
        "kh_gram": item.kh_gram,
        "max_kh_uur": item.max_kh_uur,
        "gem_gi_score": item.gem_gi_score,
        "aantal_sessies": item.aantal_sessies,
        "sport": item.sport or "",
        "goedgekeurd_op": "now()",
    }
    # Upsert op naam
    bestaand = supabase.table("carboo_gut_winkelmandje").select("id,aantal_sessies").eq("user_id", user.id).eq("naam", item.naam).execute()
    if bestaand.data:
        data["aantal_sessies"] = (bestaand.data[0].get("aantal_sessies") or 1) + 1
        supabase.table("carboo_gut_winkelmandje").update(data).eq("user_id", user.id).eq("naam", item.naam).execute()
    else:
        supabase.table("carboo_gut_winkelmandje").insert(data).execute()
    return {"ok": True}

@app.delete("/api/gut/winkelmandje/{item_id}")
async def verwijder_winkelmandje(item_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_gut_winkelmandje").delete().eq("user_id", user.id).eq("id", item_id).execute()
    return {"ok": True}

@app.get("/api/gut/advies")
async def get_advies(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Genereer wetenschappelijk advies op basis van sessiehistoriek."""
    protocol = supabase.table("carboo_gut_protocol").select("*").eq("user_id", user.id).execute()
    if not protocol.data:
        return {"advies": None}
    p = protocol.data[0]
    sessies = supabase.table("carboo_gut_sessies").select("*").eq("user_id", user.id).order("datum", desc=True).limit(10).execute()
    sessie_ids = [s["id"] for s in (sessies.data or [])]
    producten = []
    if sessie_ids:
        producten = supabase.table("carboo_gut_producten").select("*").in_("sessie_id", sessie_ids).execute().data or []
    # Analyseer GI scores per product
    product_stats: dict = {}
    for prod in producten:
        naam = prod["naam"]
        gi = prod.get("gi_totaal") or 0
        if naam not in product_stats:
            product_stats[naam] = {"gi_scores": [], "kh": prod["kh_gram"], "cat": prod.get("categorie", "")}
        product_stats[naam]["gi_scores"].append(gi)
    adviezen = []
    for naam, stats in product_stats.items():
        gem_gi = sum(stats["gi_scores"]) / len(stats["gi_scores"]) if stats["gi_scores"] else 0
        n = len(stats["gi_scores"])
        if gem_gi <= 2 and n >= 2:
            adviezen.append({"product": naam, "type": "positief", "bericht": f"{naam} scoort uitstekend (gem GI {gem_gi:.1f}/10). Klaar voor het winkelmandje?", "gem_gi": round(gem_gi, 1), "n": n})
        elif gem_gi >= 5:
            adviezen.append({"product": naam, "type": "waarschuwing", "bericht": f"{naam} geeft GI klachten (gem {gem_gi:.1f}/10). Overweeg lagere dosis of ander product.", "gem_gi": round(gem_gi, 1), "n": n})
        elif n >= 1:
            adviezen.append({"product": naam, "type": "neutraal", "bericht": f"{naam}: {n} sessie(s), gem GI {gem_gi:.1f}/10. Nog meer testen aanbevolen.", "gem_gi": round(gem_gi, 1), "n": n})
    # Week advies
    week = p.get("week_huidig", 1)
    startdosis = p.get("startdosis_g_uur", 30)
    wk_dosis = startdosis if week <= 2 else (startdosis + 15 if week <= 4 else min(startdosis + 30, p.get("max_dosis_g_uur", 90)))
    ratio = "geen vereiste" if wk_dosis < 60 else ("2:1 glucose:fructose" if wk_dosis < 90 else "1:0.8 glucose:fructose")
    return {
        "week": week,
        "dosis_huidig": wk_dosis,
        "ratio_advies": ratio,
        "product_adviezen": adviezen,
        "protocol": p,
    }


@app.get("/api/dossier/rapporten")
async def get_rapporten(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_rapporten").select("id,naam,type,meta,datum").eq("user_id", user.id).order("datum", desc=True).execute()
    return {"rapporten": r.data or []}

@app.get("/api/dossier/rapporten/{rapport_id}")
async def get_rapport(rapport_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_rapporten").select("*").eq("user_id", user.id).eq("id", rapport_id).execute()
    if not r.data:
        raise HTTPException(404, "Rapport niet gevonden")
    return r.data[0]

@app.post("/api/dossier/rapporten")
async def sla_rapport_op(item: RapportItem, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    from datetime import datetime
    # Max 20 rapporten per gebruiker
    bestaand = supabase.table("carboo_rapporten").select("id").eq("user_id", user.id).execute()
    if len(bestaand.data or []) >= 20:
        # Verwijder oudste
        oudste = supabase.table("carboo_rapporten").select("id").eq("user_id", user.id).order("datum").limit(1).execute()
        if oudste.data:
            supabase.table("carboo_rapporten").delete().eq("id", oudste.data[0]["id"]).execute()
    r = supabase.table("carboo_rapporten").insert({
        "user_id": user.id,
        "naam": item.naam,
        "type": item.type,
        "html": item.html,
        "meta": item.meta or {},
        "datum": datetime.now().isoformat(),
    }).execute()
    return {"id": r.data[0]["id"] if r.data else None, "ok": True}

@app.delete("/api/dossier/rapporten/{rapport_id}")
async def verwijder_rapport(rapport_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_rapporten").delete().eq("user_id", user.id).eq("id", rapport_id).execute()
    return {"ok": True}

@app.get("/api/fuelc/off-zoek")
async def off_zoek(q: str):
    """Proxy naar Open Food Facts om CORS te omzeilen."""
    if not q or len(q) < 2:
        return {"products": []}
    url = (
        "https://world.openfoodfacts.org/cgi/search.pl"
        f"?search_terms={q}&search_simple=1&action=process&json=1&page_size=20"
        "&fields=id,product_name,product_name_nl,product_name_fr,nutriments,serving_size,serving_quantity"
        "&lc=nl,fr,en"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, headers={"User-Agent": "Carboo/2.0 (sports nutrition app)"})
            return r.json()
    except Exception as e:
        raise HTTPException(502, f"Open Food Facts niet bereikbaar: {e}")

@app.get("/api/fuelc/dagboek/bereik")
async def get_dagboek_bereik(van: str, tot: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Haal alle dagboek items op voor een datumbereik in één call."""
    r = supabase.table("fuelc_dagboek").select("*").eq("user_id", user.id).gte("datum", van).lte("datum", tot).execute()
    # Groepeer per datum
    per_dag: dict = {}
    for item in (r.data or []):
        d = item.get("datum", "")
        if d not in per_dag:
            per_dag[d] = []
        per_dag[d].append(item)
    return {"per_dag": per_dag}

@app.get("/api/fuelc/dagboek/{datum}")
async def get_dagboek(datum: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_dagboek").select("*").eq("user_id", user.id).eq("datum", datum).execute()
    return {"items": r.data or []}

@app.post("/api/fuelc/dagboek")
async def voeg_dagboek_toe(item: DagboekItem, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = item.dict()
    data["user_id"] = user.id
    supabase.table("fuelc_dagboek").insert(data).execute()
    return {"status": "opgeslagen"}

@app.delete("/api/fuelc/dagboek/{item_id}")
async def verwijder_dagboek_item(item_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_dagboek").delete().eq("id", item_id).eq("user_id", user.id).execute()
    return {"status": "verwijderd"}

@app.put("/api/fuelc/dagboek/{item_id}")
async def update_dagboek_item(item_id: str, update: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_dagboek").update(update).eq("id", item_id).eq("user_id", user.id).execute()
    return {"status": "bijgewerkt"}

@app.get("/api/fuelc/welzijn")
async def get_welzijn(van: str, tot: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_dagboek_welzijn").select("*").eq("user_id", user.id).gte("datum", van).lte("datum", tot).execute()
    return {"welzijn": r.data or []}

@app.post("/api/fuelc/welzijn")
async def sla_welzijn_op(welzijn: WelzijnData, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = welzijn.dict()
    data["user_id"] = user.id
    supabase.table("fuelc_dagboek_welzijn").upsert(data, on_conflict="user_id,datum").execute()
    return {"status": "opgeslagen"}

@app.get("/api/fuelc/bibliotheek")
async def get_bibliotheek(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_bibliotheek").select("*").eq("user_id", user.id).order("naam").execute()
    return {"producten": r.data or []}

@app.post("/api/fuelc/bibliotheek")
async def voeg_product_toe(product: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    product["user_id"] = user.id
    supabase.table("fuelc_bibliotheek").insert(product).execute()
    return {"status": "opgeslagen"}

@app.patch("/api/fuelc/bibliotheek/{product_id}")
async def update_product(product_id: str, update: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_bibliotheek").update(update).eq("id", product_id).eq("user_id", user.id).execute()
    return {"status": "bijgewerkt"}

@app.delete("/api/fuelc/bibliotheek/{product_id}")
async def verwijder_product(product_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_dagboek").update({"product_id": None}).eq("product_id", product_id).execute()
    supabase.table("fuelc_bibliotheek").delete().eq("id", product_id).eq("user_id", user.id).execute()
    return {"status": "verwijderd"}

@app.get("/api/fuelc/recepten")
async def get_recepten(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_recepten_eigen").select("*").or_(f"user_id.eq.{user.id},is_globaal.eq.true").order("naam").execute()
    return {"recepten": r.data or []}

@app.post("/api/fuelc/recepten")
async def voeg_recept_toe(recept: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    recept["user_id"] = user.id
    supabase.table("fuelc_recepten_eigen").insert(recept).execute()
    return {"status": "opgeslagen"}

@app.delete("/api/fuelc/recepten/{recept_id}")
async def verwijder_recept(recept_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_recepten_eigen").delete().eq("id", recept_id).eq("user_id", user.id).execute()
    return {"status": "verwijderd"}

@app.get("/api/fuelc/dagmenu")
async def get_dagmenu(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_dagmenu").select("*").or_(f"user_id.eq.{user.id},is_globaal.eq.true").order("naam").execute()
    return {"menus": r.data or []}

@app.post("/api/fuelc/dagmenu")
async def sla_dagmenu_op(menu: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    menu["user_id"] = user.id
    supabase.table("fuelc_dagmenu").insert(menu).execute()
    return {"status": "opgeslagen"}

@app.delete("/api/fuelc/dagmenu/{menu_id}")
async def verwijder_dagmenu(menu_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("fuelc_dagmenu").delete().eq("id", menu_id).eq("user_id", user.id).execute()
    return {"status": "verwijderd"}

@app.get("/api/fuelc/zones/{sport}")
async def get_zones(sport: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("fuelc_zones").select("*").eq("user_id", user.id).eq("sport", sport).execute()
    return {"zones": r.data[0] if r.data else {}}

@app.post("/api/fuelc/zones")
async def sla_zones_op(data: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data["user_id"] = user.id
    sport = data.get("sport", "")
    bestaand = supabase.table("fuelc_zones").select("id").eq("user_id", user.id).eq("sport", sport).execute()
    if bestaand.data:
        supabase.table("fuelc_zones").update(data).eq("user_id", user.id).eq("sport", sport).execute()
    else:
        supabase.table("fuelc_zones").insert(data).execute()
    return {"status": "opgeslagen"}


# ═══ MODULE 3 — TRAIN THE GUT ════════════════════════════════════════════════

class GutLog(BaseModel):
    week_nr: int
    score: int
    symptoom: str
    int_uitg: str
    temp: int
    timing_ok: str
    notitie: Optional[str] = ""
    fase: str
    product: str
    kh_pp: int
    porties: int
    kh_doel: int
    progressie: Optional[str] = ""
    intensiteit: Optional[str] = ""

@app.get("/api/gut/data")
async def get_gut_data(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_gut_data").select("*").eq("user_id", user.id).execute()
    return {"data": r.data[0] if r.data else None}

@app.post("/api/gut/data")
async def sla_gut_data(gut: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    gut["user_id"] = user.id
    bestaand = supabase.table("carboo_gut_data").select("id").eq("user_id", user.id).execute()
    if bestaand.data:
        supabase.table("carboo_gut_data").update(gut).eq("user_id", user.id).execute()
    else:
        supabase.table("carboo_gut_data").insert(gut).execute()
    return {"status": "opgeslagen"}

@app.get("/api/gut/logs")
async def get_gut_logs(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_gut_logs").select("*").eq("user_id", user.id).order("week_nr").execute()
    return {"logs": r.data or []}

@app.post("/api/gut/logs")
async def sla_gut_log(log: GutLog, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    data = log.dict()
    data["user_id"] = user.id
    data["ingevuld"] = True
    bestaand = supabase.table("carboo_gut_logs").select("id").eq("user_id", user.id).eq("week_nr", log.week_nr).execute()
    if bestaand.data:
        supabase.table("carboo_gut_logs").update(data).eq("user_id", user.id).eq("week_nr", log.week_nr).execute()
    else:
        supabase.table("carboo_gut_logs").insert(data).execute()
    return {"status": "opgeslagen"}

@app.post("/api/gut/schema")
async def genereer_gut_schema(body: dict, user=Depends(get_current_user)):
    from gut_logic import genereer_schema
    try:
        schema = genereer_schema(body.get("data", {}), body.get("logs", {}), body.get("actieve_fase", ""))
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(500, f"Schema generatie mislukt: {e}")


# ═══ CREDITS ════════════════════════════════════════════════════════════════

@app.get("/api/credits")
async def get_credits(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_gebruikers").select("credits").eq("id", user.id).single().execute()
    return {"credits": r.data.get("credits", 0) if r.data else 0}

@app.post("/api/credits/gebruik")
async def gebruik_credit(omschrijving: str = "Rapport", user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_gebruikers").select("credits").eq("id", user.id).single().execute()
    credits = r.data.get("credits", 0) if r.data else 0
    if credits <= 0:
        raise HTTPException(402, "Geen credits meer")
    supabase.table("carboo_gebruikers").update({"credits": credits - 1}).eq("id", user.id).execute()
    supabase.table("carboo_credit_log").insert({"user_id": user.id, "omschrijving": omschrijving, "bedrag": -1}).execute()
    return {"credits": credits - 1}


# ═══ ETIKETSCAN ══════════════════════════════════════════════════════════════

@app.post("/api/fuelc/scan-etiket")
async def scan_etiket(request: Request, user=Depends(get_current_user)):
    import json, re
    try:
        import anthropic
    except ImportError:
        raise HTTPException(500, "anthropic pakket niet geinstalleerd")

    body = await request.json()
    image_data = body.get("image_data", "")
    media_type = body.get("media_type", "image/jpeg")

    if not image_data:
        raise HTTPException(400, "Geen afbeelding ontvangen")

    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        media_type = "image/jpeg"

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY niet ingesteld op Render")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data}
                    },
                    {
                        "type": "text",
                        "text": 'Analyseer dit voedseletiket. Geef ALLEEN een JSON object terug, geen uitleg. BELANGRIJK: alle voedingswaarden (kcal, kh, suikers, vezels, eiwit, vet, verz, natrium, kalium, calcium, ijzer, magnesium, vitc, vitd, vitb12, omega3) moeten PER 100G zijn, niet per portie. De portie_g en portie_label zijn informatief. Gebruik dit formaat: {"naam":"","categorie":"Granen en brood","portie_g":100,"portie_label":"100g","kcal":0,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,"natrium":0,"kalium":0,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0,"gi":0}'
                    }
                ]
            }]
        )
        tekst = msg.content[0].text.strip()
        match = re.search(r'\{[\s\S]*\}', tekst)
        if not match:
            raise HTTPException(422, f"Claude antwoord: {tekst[:200]}")
        return json.loads(match.group())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Claude fout: {type(e).__name__}: {str(e)[:200]}")

# ─── COACH ZONE SOCIAAL ───────────────────────────────────────────────────────

class CoachBericht(BaseModel):
    tekst: str
    type: Optional[str] = "bericht"

class PrikbordPost(BaseModel):
    titel: str
    tekst: str
    type: Optional[str] = "post"

class PrikbordReactie(BaseModel):
    post_id: str
    tekst: str
    anoniem: Optional[bool] = False

# ── Groepsberichten ────────────────────────────────────────────────────────────

@app.get("/api/coach/berichten")
async def get_berichten_coach(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Coach haalt eigen berichten op."""
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        return {"berichten": []}
    coach_id = coach.data[0]["id"]
    r = supabase.table("carboo_coach_berichten").select("*, carboo_bericht_gelezen(klant_id)").eq("coach_id", coach_id).order("aangemaakt", desc=True).limit(50).execute()
    return {"berichten": r.data or []}

@app.get("/api/coach/berichten/inbox")
async def get_berichten_klant(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Klant haalt berichten van al zijn coaches op."""
    coaches = supabase.table("carboo_coach_klanten").select("coach_id").eq("klant_id", user.id).eq("status", "actief").execute()
    if not coaches.data:
        return {"berichten": [], "ongelezen": 0}
    coach_ids = [c["coach_id"] for c in coaches.data]
    r = supabase.table("carboo_coach_berichten").select("*, carboo_coaches(naam), carboo_bericht_gelezen(klant_id)").in_("coach_id", coach_ids).order("aangemaakt", desc=True).limit(50).execute()
    gelezen_ids = set()
    for b in (r.data or []):
        for g in (b.get("carboo_bericht_gelezen") or []):
            if g.get("klant_id") == user.id:
                gelezen_ids.add(b["id"])
    ongelezen = sum(1 for b in (r.data or []) if b["id"] not in gelezen_ids)
    return {"berichten": r.data or [], "ongelezen": ongelezen, "gelezen_ids": list(gelezen_ids)}

@app.post("/api/coach/berichten")
async def stuur_bericht(item: CoachBericht, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(403, "Geen coach account")
    r = supabase.table("carboo_coach_berichten").insert({
        "coach_id": coach.data[0]["id"],
        "tekst": item.tekst,
        "type": item.type or "bericht",
    }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.post("/api/coach/berichten/{bericht_id}/gelezen")
async def markeer_bericht_gelezen(bericht_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        supabase.table("carboo_bericht_gelezen").insert({"bericht_id": bericht_id, "klant_id": user.id}).execute()
    except Exception:
        pass
    return {"ok": True}

@app.delete("/api/coach/berichten/{bericht_id}")
async def verwijder_bericht(bericht_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        supabase.table("carboo_coach_berichten").delete().eq("id", bericht_id).eq("coach_id", coach.data[0]["id"]).execute()
    return {"ok": True}

# ── Prikbord ───────────────────────────────────────────────────────────────────

@app.get("/api/coach/prikbord")
async def get_prikbord(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Haalt prikbord op — werkt voor coach én klant."""
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        coach_id = coach.data[0]["id"]
        r = supabase.table("carboo_coach_prikbord").select("*, carboo_prikbord_reacties(*)").eq("coach_id", coach_id).order("aangemaakt", desc=True).limit(30).execute()
    else:
        coaches = supabase.table("carboo_coach_klanten").select("coach_id").eq("klant_id", user.id).eq("status", "actief").execute()
        if not coaches.data:
            return {"posts": []}
        coach_ids = [c["coach_id"] for c in coaches.data]
        r = supabase.table("carboo_coach_prikbord").select("*, carboo_coaches(naam), carboo_prikbord_reacties(id,tekst,anoniem,aangemaakt,klant_id)").in_("coach_id", coach_ids).order("aangemaakt", desc=True).limit(30).execute()
    return {"posts": r.data or []}

@app.post("/api/coach/prikbord")
async def maak_post(item: PrikbordPost, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(403, "Geen coach account")
    r = supabase.table("carboo_coach_prikbord").insert({
        "coach_id": coach.data[0]["id"],
        "titel": item.titel,
        "tekst": item.tekst,
        "type": item.type or "post",
    }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.delete("/api/coach/prikbord/{post_id}")
async def verwijder_post(post_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        supabase.table("carboo_coach_prikbord").delete().eq("id", post_id).eq("coach_id", coach.data[0]["id"]).execute()
    return {"ok": True}

@app.post("/api/coach/prikbord/reactie")
async def plaats_prikbord_reactie(item: PrikbordReactie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_prikbord_reacties").insert({
        "post_id": item.post_id,
        "klant_id": user.id,
        "tekst": item.tekst,
        "anoniem": item.anoniem or False,
    }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.delete("/api/coach/prikbord/reactie/{reactie_id}")
async def verwijder_prikbord_reactie(reactie_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_prikbord_reacties").delete().eq("id", reactie_id).eq("klant_id", user.id).execute()
    return {"ok": True}
