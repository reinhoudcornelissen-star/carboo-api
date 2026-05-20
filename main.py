cd C:\Users\reinhoud\Documents\Carbs\carboo-api

Write-Host "`n=== Laatste 5 commits ===" -ForegroundColor Cyan
git log --oneline -5

Write-Host "`n=== Singleton in laatste commit? ===" -ForegroundColor Cyan
git show HEAD:main.py | Select-String "_supabase_singleton" | Select-Object -First 3from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx
from supabase import create_client, Client
from mollie.api.client import Client as MollieClient

mollie_client = MollieClient()
mollie_client.set_api_key(os.getenv("MOLLIE_API_KEY", ""))
APP_URL = os.getenv("APP_URL", "https://carboo.app")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://carboo-api.onrender.com/api/mollie/webhook")

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

# Globale Supabase client - 1x aangemaakt, hergebruikt voor alle requests
_supabase_singleton: Optional[Client] = None

def get_supabase() -> Client:
    global _supabase_singleton
    if _supabase_singleton is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise HTTPException(500, "Supabase niet geconfigureerd")
        _supabase_singleton = create_client(url, key)
    return _supabase_singleton

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
    geboortedatum: Optional[date] = None
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
    # Als geboortedatum is ingevuld, bereken leeftijd serverside (single source of truth)
    if data.get("geboortedatum"):
        from datetime import date as _date
        gd = data["geboortedatum"]
        if isinstance(gd, _date):
            today = _date.today()
            data["leeftijd"] = today.year - gd.year - ((today.month, today.day) < (gd.month, gd.day))
            data["geboortedatum"] = gd.isoformat()
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
    dagschema: bool = False
    gewicht: bool = False
    macros: bool = False
    voedingskwaliteit: bool = False
    performance: bool = False
    race_plannen: bool = False
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

@app.get("/api/admin/coaches")
async def admin_lijst_coaches(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Alle coaches (geverifieerd + gedeactiveerd) met aantal klanten."""
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    coaches = supabase.table("carboo_coaches").select("*").order("naam").execute()
    result = []
    for c in (coaches.data or []):
        kl = supabase.table("carboo_coach_klanten").select("id", count="exact").eq("coach_id", c["id"]).eq("status", "actief").execute()
        result.append({**c, "aantal_klanten": kl.count or 0})
    return {"coaches": result}

@app.post("/api/admin/coach/{coach_id}/activeer")
async def admin_activeer_coach(coach_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Coach licentie heractiveren (verified=true)."""
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    supabase.table("carboo_coaches").update({"verified": True}).eq("id", coach_id).execute()
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
# NIEUW: koppeling op klant email, betere validatie

@app.post("/api/coach/invite/genereer")
async def genereer_invite(data: dict, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    klant_email = (data.get("email") or "").strip().lower()
    if not klant_email:
        raise HTTPException(400, "Email van de klant is verplicht")

    coach = supabase.table("carboo_coaches").select("id,verified").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(400, "Maak eerst een coach profiel aan")
    if not coach.data[0].get("verified"):
        raise HTTPException(403, "Coach account nog niet goedgekeurd door admin")
    coach_id = coach.data[0]["id"]

    # Zoek klant in auth.users via Supabase admin API
    klant_id = None
    try:
        all_users = supabase.auth.admin.list_users()
        for u in (all_users or []):
            user_email = getattr(u, 'email', None) or (u.get('email') if isinstance(u, dict) else None)
            user_uid = getattr(u, 'id', None) or (u.get('id') if isinstance(u, dict) else None)
            if user_email and user_email.lower() == klant_email:
                klant_id = str(user_uid)
                break
    except Exception as e:
        raise HTTPException(500, f"Fout bij zoeken gebruiker: {e}")
    if not klant_id:
        raise HTTPException(404, f"Geen Carboo-gebruiker gevonden met email {klant_email}. De klant moet eerst een account aanmaken in de app.")

    if klant_id == user.id:
        raise HTTPException(400, "Je kan jezelf niet als klant uitnodigen")

    # Check bestaande relatie
    bestaand = supabase.table("carboo_coach_klanten").select("id,status").eq("coach_id", coach_id).eq("klant_id", klant_id).execute()
    if bestaand.data:
        rel = bestaand.data[0]
        if rel["status"] == "actief":
            raise HTTPException(400, "Deze klant is al gekoppeld aan jou")
        # Verwijder pending/geweigerd voor nieuwe poging
        supabase.table("carboo_coach_klanten").delete().eq("id", rel["id"]).execute()

    from datetime import datetime, timedelta
    token = secrets.token_urlsafe(24)
    expires = (datetime.now() + timedelta(days=7)).isoformat()

    supabase.table("carboo_coach_klanten").insert({
        "coach_id": coach_id,
        "klant_id": klant_id,
        "klant_email": klant_email,
        "status": "pending",
        "invite_token": token,
        "invite_expires": expires
    }).execute()

    return {"token": token, "expires": expires, "link": f"/app/coach-zone/invite/{token}", "klant_email": klant_email}

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
    if relatie.get("invite_expires") and relatie["invite_expires"] < datetime.now().isoformat():
        raise HTTPException(410, "Uitnodiging verlopen")

    # Check: ingelogde gebruiker MOET de juiste klant zijn
    if relatie.get("klant_id") and relatie["klant_id"] != user.id:
        raise HTTPException(403, "Deze uitnodiging is voor een andere gebruiker")

    supabase.table("carboo_coach_klanten").update({
        "klant_id": user.id, "status": "actief", "bijgewerkt": "now()"
    }).eq("id", relatie["id"]).execute()

    # Privacy instellingen
    bestaande_privacy = supabase.table("carboo_coach_privacy").select("id").eq("relatie_id", relatie["id"]).execute()
    if not bestaande_privacy.data:
        supabase.table("carboo_coach_privacy").insert({
            "relatie_id": relatie["id"], "klant_id": user.id,
            "dagschema": False, "gewicht": False, "macros": False,
            "voedingskwaliteit": False, "performance": False,
            "race_plannen": False, "train_gut": False, "dossier": False
        }).execute()
    return {"ok": True, "relatie_id": relatie["id"]}

@app.post("/api/coach/invite/{token}/weiger")
async def weiger_invite(token: str, supabase: Client = Depends(get_supabase)):
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
        "dagschema": item.dagschema,
        "gewicht": item.gewicht,
        "macros": item.macros,
        "voedingskwaliteit": item.voedingskwaliteit,
        "performance": item.performance,
        "race_plannen": item.race_plannen,
        "train_gut": item.train_gut,
        "dossier": item.dossier,
        "bijgewerkt": "now()"
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
    prof = supabase.table("fuelc_profiel").select("energie_doel,kh_doel_pct,eiwit_doel_pct,vet_doel_pct,gewicht_kg,lengte_cm").eq("user_id", klant_id).execute()
    result["profiel"] = prof.data[0] if prof.data else {}
    if privacy.get("dagschema"):
        dag = supabase.table("fuelc_dagboek").select("datum,moment,naam,kcal,kh_g,eiwit_g,vet_g,vezels_g,hoeveelheid_g,suikers_g,natrium_mg,vitd_mcg,vitb12_mcg,omega3_g,calcium_mg,ijzer_mg,gi").eq("user_id", klant_id).order("datum", desc=True).limit(100).execute()
        result["dagschema"] = dag.data or []
        tr = supabase.table("fuelc_trainingen").select("datum,sport,duur_min,kcal_verbranding").eq("user_id", klant_id).order("datum", desc=True).limit(30).execute()
        result["trainingen"] = tr.data or []
        wz = supabase.table("fuelc_dagboek_welzijn").select("datum,energie_score,stemming,stress,slaap_uur,gewicht_kg,hf_rust,rpe").eq("user_id", klant_id).order("datum", desc=True).limit(30).execute()
        result["welzijn"] = wz.data or []
    if privacy.get("race_plannen"):
        rap = supabase.table("carboo_rapporten").select("id,naam,type,meta,datum").eq("user_id", klant_id).order("datum", desc=True).limit(10).execute()
        result["race_plannen"] = rap.data or []
    if privacy.get("train_gut"):
        gut = supabase.table("carboo_gut_sessies").select("*").eq("user_id", klant_id).order("datum", desc=True).limit(30).execute()
        sessie_list = gut.data or []
        # Producten per sessie nested
        if sessie_list:
            sessie_ids = [s["id"] for s in sessie_list]
            prod = supabase.table("carboo_gut_producten").select("*").in_("sessie_id", sessie_ids).order("tijdstip_min").execute()
            prod_map: dict = {}
            for p in (prod.data or []):
                sid = p["sessie_id"]
                if sid not in prod_map: prod_map[sid] = []
                prod_map[sid].append(p)
            for s in sessie_list:
                s["producten"] = prod_map.get(s["id"], [])
        result["gut_sessies"] = sessie_list
        wm = supabase.table("carboo_gut_winkelmandje").select("*").eq("user_id", klant_id).order("aantal_sessies", desc=True).execute()
        result["gut_winkelmandje"] = wm.data or []
        prot = supabase.table("carboo_gut_protocol").select("*").eq("user_id", klant_id).eq("actief", True).execute()
        result["gut_protocol"] = prot.data[0] if prot.data else None
    if privacy.get("dossier"):
        dos = supabase.table("carboo_rapporten").select("id,naam,type,meta,datum").eq("user_id", klant_id).order("datum", desc=True).limit(10).execute()
        result["dossier"] = dos.data or []
    if privacy.get("voedingskwaliteit") or privacy.get("performance") or privacy.get("macros"):
        if "dagschema" not in result:
            # Voor coach analyses: volledige velden inclusief micronutrienten
            dag = supabase.table("fuelc_dagboek").select("datum,moment,naam,categorie,kcal,kh_g,eiwit_g,vet_g,vezels_g,hoeveelheid_g,suikers_g,natrium_mg,kalium_mg,calcium_mg,ijzer_mg,vitd_mcg,vitb12_mcg,omega3_g,verz_g,gi").eq("user_id", klant_id).order("datum", desc=True).limit(200).execute()
            dag_items = dag.data or []
            # Stuur ook mee in result voor frontend berekening
            result["dagschema_full"] = dag_items
            # Trainingen ook nodig voor de berekening
            tr_full = supabase.table("fuelc_trainingen").select("datum,sport,duur_min,kcal_verbranding").eq("user_id", klant_id).order("datum", desc=True).limit(60).execute()
            result["trainingen_full"] = tr_full.data or []
        else:
            dag_items = result["dagschema"]
            result["dagschema_full"] = dag_items
            tr_full = supabase.table("fuelc_trainingen").select("datum,sport,duur_min,kcal_verbranding").eq("user_id", klant_id).order("datum", desc=True).limit(60).execute()
            result["trainingen_full"] = tr_full.data or []

    if privacy.get("macros"):
        items = dag_items if "dag_items" in dir() else []
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
        gew = supabase.table("fuelc_dagboek_welzijn").select("datum,gewicht_kg,energie_score,stemming,stress,slaap_uur,slaap_kwaliteit,hf_rust,hrv").eq("user_id", klant_id).not_.is_("gewicht_kg", "null").order("datum", desc=True).limit(30).execute()
        result["gewicht_data"] = gew.data or []

    if privacy.get("voedingskwaliteit") or privacy.get("performance"):
        vq_items = dag_items if "dag_items" in dir() and dag_items else []
        if not vq_items:
            dag_vq = supabase.table("fuelc_dagboek").select("datum,kcal,kh_g,eiwit_g,vet_g,vezels_g").eq("user_id", klant_id).order("datum", desc=True).limit(70).execute()
            vq_items = dag_vq.data or []

    if privacy.get("voedingskwaliteit") and vq_items:
        vq_dag: dict = {}
        for item in vq_items:
            d = item.get("datum", "")
            if d not in vq_dag:
                vq_dag[d] = {"vezels": 0, "kcal": 0, "kh": 0, "eiwit": 0}
            vq_dag[d]["vezels"] += item.get("vezels_g", 0) or 0
            vq_dag[d]["kcal"] += item.get("kcal", 0) or 0
            vq_dag[d]["kh"] += item.get("kh_g", 0) or 0
            vq_dag[d]["eiwit"] += item.get("eiwit_g", 0) or 0
        if vq_dag:
            n = len(vq_dag)
            gem_vezels = round(sum(d["vezels"] for d in vq_dag.values()) / n, 1)
            gem_kcal = round(sum(d["kcal"] for d in vq_dag.values()) / n)
            gem_kh = round(sum(d["kh"] for d in vq_dag.values()) / n)
            gem_eiwit = round(sum(d["eiwit"] for d in vq_dag.values()) / n)
            vezels_score = min(10, round(gem_vezels / 2.5))
            result["voedingskwaliteit"] = {
                "gem_vezels_dag": gem_vezels,
                "gem_kcal_dag": gem_kcal,
                "aantal_dagen": n,
                "scores": [
                    {"label": "Vezels", "score": vezels_score},
                    {"label": "Energie gemiddeld", "score": min(10, round(gem_kcal / 200))},
                    {"label": "Koolhydraten", "score": min(10, round(gem_kh / 30))},
                    {"label": "Eiwit", "score": min(10, round(gem_eiwit / 15))},
                ]
            }

    if privacy.get("performance") and vq_items:
        vq_dag2: dict = {}
        for item in vq_items:
            d = item.get("datum", "")
            if d not in vq_dag2:
                vq_dag2[d] = {"kcal": 0, "kh": 0, "eiwit": 0, "vezels": 0}
            vq_dag2[d]["kcal"] += item.get("kcal", 0) or 0
            vq_dag2[d]["kh"] += item.get("kh_g", 0) or 0
            vq_dag2[d]["eiwit"] += item.get("eiwit_g", 0) or 0
            vq_dag2[d]["vezels"] += item.get("vezels_g", 0) or 0
        trainingen = supabase.table("fuelc_trainingen").select("datum,kcal_verbranding").eq("user_id", klant_id).order("datum", desc=True).limit(14).execute()
        tr_kcal = {t["datum"][:10]: (t.get("kcal_verbranding") or 0) for t in (trainingen.data or [])}
        dag_scores = []
        for d, vals in list(vq_dag2.items())[:14]:
            extra = tr_kcal.get(d, 0)
            doel = 1914 + extra
            kcal_score = min(10, round(vals["kcal"] / max(doel, 1) * 10))
            kh_score = min(10, round(vals["kh"] / 265 * 10))
            ei_score = min(10, round(vals["eiwit"] / 120 * 10))
            vez_score = min(10, round(vals["vezels"] / 25 * 10))
            dag_score = round((kcal_score + kh_score + ei_score + vez_score) / 4, 1)
            dag_scores.append(dag_score)
        gem_score = round(sum(dag_scores) / max(len(dag_scores), 1), 1) if dag_scores else 0
        result["performance"] = {
            "score": gem_score,
            "details": [
                {"label": "Energiebalans", "score": min(10, round(gem_score))},
                {"label": "Koolhydraten", "score": min(10, round(gem_score * 0.9))},
                {"label": "Eiwit", "score": min(10, round(gem_score * 1.1))},
                {"label": "Vezels", "score": min(10, round(gem_score * 0.8))},
            ]
        }
    return result

# ── Opmerkingen ─────────────────────────────────────────────────────────────────

@app.post("/api/coach/opmerkingen")
async def plaats_opmerking(item: CoachOpmerking, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        raise HTTPException(403, "Geen coach account")
    coach_id = coach.data[0]["id"]
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
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        coach_id = coach.data[0]["id"]
        opm = supabase.table("carboo_coach_opmerkingen").select("id").eq("id", item.opmerking_id).eq("coach_id", coach_id).execute()
        if opm.data:
            supabase.table("carboo_coach_reacties").insert({"opmerking_id": item.opmerking_id, "coach_id": coach_id, "tekst": item.tekst, "auteur_type": "coach"}).execute()
            return {"ok": True}
    opm = supabase.table("carboo_coach_opmerkingen").select("id").eq("id", item.opmerking_id).eq("klant_id", user.id).execute()
    if not opm.data:
        raise HTTPException(403, "Geen toegang")
    supabase.table("carboo_coach_reacties").insert({"opmerking_id": item.opmerking_id, "klant_id": user.id, "tekst": item.tekst, "auteur_type": "klant"}).execute()
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
    type: str
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
    basis = {"Beginner": 20, "Gevorderd": 40, "Ervaren": 60}.get(ervaring, 20)
    mult = {"Recreant": 1.0, "Competitief": 1.3, "Professioneel": 1.6}.get(niveau, 1.0)
    sport_factor = 0.8 if sport in ["Lopen"] else 1.0
    startdosis = max(20, round(basis * sport_factor / 5) * 5)
    max_map = {"Recreant": 60, "Competitief": 90, "Professioneel": 120}
    max_dosis = max_map.get(niveau, 60)
    if sport == "Lopen":
        max_dosis = round(max_dosis * 0.85 / 5) * 5
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
    protocol = supabase.table("carboo_gut_protocol").select("*").eq("user_id", user.id).execute()
    if not protocol.data:
        return {"advies": None}
    p = protocol.data[0]
    sessies = supabase.table("carboo_gut_sessies").select("*").eq("user_id", user.id).order("datum", desc=True).limit(10).execute()
    sessie_ids = [s["id"] for s in (sessies.data or [])]
    producten = []
    if sessie_ids:
        producten = supabase.table("carboo_gut_producten").select("*").in_("sessie_id", sessie_ids).execute().data or []
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
    bestaand = supabase.table("carboo_rapporten").select("id").eq("user_id", user.id).execute()
    if len(bestaand.data or []) >= 20:
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
    r = supabase.table("fuelc_dagboek").select("*").eq("user_id", user.id).gte("datum", van).lte("datum", tot).execute()
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
    foto_url: Optional[str] = None

class PrikbordReactie(BaseModel):
    post_id: str
    tekst: str
    anoniem: Optional[bool] = False

# ── Groepsberichten ────────────────────────────────────────────────────────────

@app.get("/api/coach/berichten")
async def get_berichten_coach(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if not coach.data:
        return {"berichten": []}
    coach_id = coach.data[0]["id"]
    r = supabase.table("carboo_coach_berichten").select("*, carboo_bericht_gelezen(klant_id)").eq("coach_id", coach_id).order("aangemaakt", desc=True).limit(50).execute()
    return {"berichten": r.data or []}

@app.get("/api/coach/berichten/inbox")
async def get_berichten_klant(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
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
    """Haalt prikbord op:
    - Iedereen ziet admin posts (is_admin_post=true)
    - Klant ziet ook posts van zijn eigen coaches
    - Coach ziet ook zijn eigen posts
    """
    posts = []
    # Admin posts (voor iedereen)
    admin_r = supabase.table("carboo_coach_prikbord").select("*, carboo_prikbord_reacties(id,tekst,anoniem,aangemaakt,klant_id)").eq("is_admin_post", True).order("aangemaakt", desc=True).limit(30).execute()
    posts.extend(admin_r.data or [])

    # Coach? Voeg eigen posts toe
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        coach_id = coach.data[0]["id"]
        c_r = supabase.table("carboo_coach_prikbord").select("*, carboo_prikbord_reacties(*)").eq("coach_id", coach_id).eq("is_admin_post", False).order("aangemaakt", desc=True).limit(30).execute()
        posts.extend(c_r.data or [])

    # Klant van een coach? Voeg posts van eigen coaches toe
    klant_coaches = supabase.table("carboo_coach_klanten").select("coach_id").eq("klant_id", user.id).eq("status", "actief").execute()
    if klant_coaches.data:
        coach_ids = [c["coach_id"] for c in klant_coaches.data]
        k_r = supabase.table("carboo_coach_prikbord").select("*, carboo_coaches(naam), carboo_prikbord_reacties(id,tekst,anoniem,aangemaakt,klant_id)").in_("coach_id", coach_ids).eq("is_admin_post", False).order("aangemaakt", desc=True).limit(30).execute()
        posts.extend(k_r.data or [])

    # Sorteer alles op datum
    posts.sort(key=lambda p: p.get("aangemaakt", ""), reverse=True)
    return {"posts": posts}

@app.post("/api/coach/prikbord")
async def maak_post(item: PrikbordPost, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Coach maakt post voor klanten, admin maakt post voor iedereen."""
    is_adm = await is_admin(user, supabase)
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()

    if is_adm:
        # Admin post — zichtbaar voor iedereen
        r = supabase.table("carboo_coach_prikbord").insert({
            "coach_id": coach.data[0]["id"] if coach.data else None,
            "is_admin_post": True,
            "titel": item.titel,
            "tekst": item.tekst,
            "type": item.type or "post",
            "foto_url": item.foto_url,
        }).execute()
    else:
        if not coach.data:
            raise HTTPException(403, "Geen coach of admin account")
        r = supabase.table("carboo_coach_prikbord").insert({
            "coach_id": coach.data[0]["id"],
            "is_admin_post": False,
            "titel": item.titel,
            "tekst": item.tekst,
            "type": item.type or "post",
            "foto_url": item.foto_url,
        }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.delete("/api/coach/prikbord/{post_id}")
async def verwijder_post(post_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    is_adm = await is_admin(user, supabase)
    if is_adm:
        # Admin mag elke post verwijderen
        supabase.table("carboo_coach_prikbord").delete().eq("id", post_id).execute()
    else:
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


# ─── FORUM ─────────────────────────────────────────────────────────────────────

class ForumPost(BaseModel):
    titel: str
    tekst: str
    categorie: Optional[str] = "algemeen"
    foto_url: Optional[str] = None

class ForumReactie(BaseModel):
    post_id: str
    tekst: str

@app.get("/api/forum/posts")
async def get_forum_posts(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Alle zichtbare forum posts."""
    r = supabase.table("carboo_forum").select("*").eq("verborgen", False).order("aangemaakt", desc=True).limit(50).execute()
    posts = r.data or []
    # Voor elke post de reacties halen
    for p in posts:
        reacties = supabase.table("carboo_forum_reacties").select("*").eq("post_id", p["id"]).eq("verborgen", False).order("aangemaakt").execute()
        p["reacties"] = reacties.data or []
    return {"posts": posts}

@app.post("/api/forum/posts")
async def maak_forum_post(item: ForumPost, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Iedereen kan posten."""
    # Haal naam op (uit auth metadata of email)
    auteur_naam = getattr(user, "email", "").split("@")[0] if hasattr(user, "email") else "Gebruiker"
    r = supabase.table("carboo_forum").insert({
        "auteur_id": user.id,
        "auteur_naam": auteur_naam,
        "titel": item.titel,
        "tekst": item.tekst,
        "foto_url": item.foto_url,
        "categorie": item.categorie or "algemeen",
    }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.post("/api/forum/reacties")
async def plaats_forum_reactie(item: ForumReactie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    auteur_naam = getattr(user, "email", "").split("@")[0] if hasattr(user, "email") else "Gebruiker"
    r = supabase.table("carboo_forum_reacties").insert({
        "post_id": item.post_id,
        "auteur_id": user.id,
        "auteur_naam": auteur_naam,
        "tekst": item.tekst,
    }).execute()
    return {"ok": True, "id": r.data[0]["id"] if r.data else None}

@app.delete("/api/forum/posts/{post_id}")
async def verwijder_forum_post(post_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Eigen post verwijderen of admin verwijdert (zet verborgen=true)."""
    is_adm = await is_admin(user, supabase)
    if is_adm:
        # Admin verbergt (zachte delete voor audit)
        supabase.table("carboo_forum").update({"verborgen": True}).eq("id", post_id).execute()
    else:
        # Eigen post hard verwijderen
        supabase.table("carboo_forum").delete().eq("id", post_id).eq("auteur_id", user.id).execute()
    return {"ok": True}

@app.delete("/api/forum/reacties/{reactie_id}")
async def verwijder_forum_reactie(reactie_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    is_adm = await is_admin(user, supabase)
    if is_adm:
        supabase.table("carboo_forum_reacties").update({"verborgen": True}).eq("id", reactie_id).execute()
    else:
        supabase.table("carboo_forum_reacties").delete().eq("id", reactie_id).eq("auteur_id", user.id).execute()
    return {"ok": True}

@app.post("/api/admin/forum/posts/{post_id}/herstel")
async def admin_herstel_post(post_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Admin maakt verborgen post terug zichtbaar."""
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    supabase.table("carboo_forum").update({"verborgen": False}).eq("id", post_id).execute()
    return {"ok": True}



# ─── CHALLENGES + LEADERBOARD ──────────────────────────────────────────────────

class ChallengeMaak(BaseModel):
    titel: str
    omschrijving: Optional[str] = None
    type: str  # plantaardig|performance|vocht|wedstrijd_tijd|afstand|vrije_score
    hoger_beter: bool = True
    doel_waarde: Optional[float] = None
    eenheid: Optional[str] = None
    start_datum: str
    eind_datum: str

class ChallengeScore(BaseModel):
    manuele_score: float

def _bereken_auto_score(supabase: Client, user_id: str, ctype: str, start: str, eind: str) -> Optional[float]:
    """Bereken auto score voor een challenge type tussen start en eind."""
    dag = supabase.table("fuelc_dagboek").select("*").eq("user_id", user_id).gte("datum", start).lte("datum", eind).execute()
    items = dag.data or []
    if not items:
        return None
    # Groepeer per dag
    per_dag: dict = {}
    for it in items:
        d = (it.get("datum") or "")[:10]
        per_dag.setdefault(d, []).append(it)
    dagen = list(per_dag.values())
    if not dagen:
        return None

    if ctype == "plantaardig":
        PLANT = {"Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten"}
        DIER = {"Vlees & vis","Zuivel","Eieren"}
        pcts = []
        for dag_items in dagen:
            pl, di = 0.0, 0.0
            for it in dag_items:
                cat = it.get("categorie", "")
                k = it.get("kcal") or 0
                if cat in PLANT: pl += k
                elif cat in DIER: di += k
            tot = pl + di
            if tot > 0: pcts.append(pl / tot * 100)
        return sum(pcts) / len(pcts) if pcts else None

    if ctype == "vocht":
        VOCHT = {"water":100,"melk":100,"yoghurt":85,"koffie":100,"thee":100,"sap":100,"sportdrank":100,"smoothie":90,"cola":100,"soep":85,"bouillon":100}
        dag_vocht = []
        for dag_items in dagen:
            v = 0
            for it in dag_items:
                n = (it.get("naam") or "").lower()
                g = it.get("hoeveelheid_g") or 0
                for k, pct in VOCHT.items():
                    if k in n:
                        v += g * pct / 100
                        break
            dag_vocht.append(v)
        return sum(dag_vocht) / len(dag_vocht) if dag_vocht else None

    if ctype == "performance":
        prof = supabase.table("fuelc_profiel").select("energie_doel,kh_doel_pct,eiwit_doel_pct").eq("user_id", user_id).execute()
        p = prof.data[0] if prof.data else {}
        eDoel = p.get("energie_doel") or 2200
        khPct = p.get("kh_doel_pct") or 50
        eiPct = p.get("eiwit_doel_pct") or 20
        scores = []
        for dag_items in dagen:
            kcal = sum((it.get("kcal") or 0) for it in dag_items)
            kh = sum((it.get("kh_g") or 0) for it in dag_items)
            ei = sum((it.get("eiwit_g") or 0) for it in dag_items)
            vez = sum((it.get("vezels_g") or 0) for it in dag_items)
            if kcal <= 0: continue
            import math
            score = 0
            pctE = kcal / eDoel if eDoel > 0 else 0
            score += max(2, min(25, round(25 * math.exp(-((pctE - 1) ** 2) / (2 * 0.18 * 0.18)))))
            khD = round(eDoel * khPct / 100 / 4)
            khPctD = kh / khD if khD > 0 else 0
            score += 20 if khPctD >= 0.95 else 14 if khPctD >= 0.80 else 8 if khPctD >= 0.60 else 4 if khPctD >= 0.40 else 2
            eiD = round(eDoel * eiPct / 100 / 4)
            eiPctD = ei / eiD if eiD > 0 else 0
            score += 20 if eiPctD >= 0.95 else 14 if eiPctD >= 0.80 else 8 if eiPctD >= 0.60 else 4 if eiPctD >= 0.40 else 2
            score += 15 if vez >= 30 else 10 if vez >= 20 else 5 if vez >= 10 else 0
            momenten = len(set(it.get("moment") for it in dag_items if it.get("moment")))
            score += min(10, momenten * 2)
            VOCHT_MAP = {"water":100,"melk":100,"yoghurt":85,"koffie":100,"thee":100,"sap":100,"sportdrank":100,"smoothie":90,"cola":100,"soep":85}
            v = 0
            for it in dag_items:
                n = (it.get("naam") or "").lower()
                g = it.get("hoeveelheid_g") or 0
                for k, pct in VOCHT_MAP.items():
                    if k in n: v += g * pct / 100; break
            score += 10 if v >= 2000 else 7 if v >= 1500 else 4 if v >= 1000 else 2 if v >= 500 else 0
            scores.append(min(100, score))
        return sum(scores) / len(scores) if scores else None
    return None

@app.get("/api/challenges")
async def lijst_challenges(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Geef actieve challenges terug die de user kan zien:
    - Alle admin challenges
    - Coach challenges van zijn eigen coaches (voor klanten)
    - Eigen challenges (voor coach)
    """
    is_adm = await is_admin(user, supabase)
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    coach_id = coach.data[0]["id"] if coach.data else None
    klant_coaches = supabase.table("carboo_coach_klanten").select("coach_id").eq("klant_id", user.id).eq("status", "actief").execute()
    klant_coach_ids = [c["coach_id"] for c in (klant_coaches.data or [])]

    alle = supabase.table("carboo_challenges").select("*").eq("actief", True).order("eind_datum", desc=True).execute()
    zichtbaar = []
    for ch in (alle.data or []):
        if ch["maker_type"] == "admin":
            zichtbaar.append(ch)
        elif coach_id and ch["coach_id"] == coach_id:
            zichtbaar.append(ch)
        elif klant_coach_ids and ch["coach_id"] in klant_coach_ids:
            zichtbaar.append(ch)
    return {"challenges": zichtbaar}

@app.post("/api/challenges")
async def maak_challenge(item: ChallengeMaak, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    is_adm = await is_admin(user, supabase)
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).eq("verified", True).execute()
    coach_id = coach.data[0]["id"] if coach.data else None
    if not (is_adm or coach_id):
        raise HTTPException(403, "Alleen admin of coach kan challenges aanmaken")
    if item.type not in ["plantaardig", "performance", "vocht", "wedstrijd_tijd", "afstand", "vrije_score"]:
        raise HTTPException(400, "Ongeldig type")
    data = {
        "maker_id": user.id, "maker_type": "admin" if is_adm else "coach",
        "coach_id": coach_id if not is_adm else None,
        "titel": item.titel, "omschrijving": item.omschrijving, "type": item.type,
        "hoger_beter": item.hoger_beter, "doel_waarde": item.doel_waarde, "eenheid": item.eenheid,
        "start_datum": item.start_datum, "eind_datum": item.eind_datum,
    }
    r = supabase.table("carboo_challenges").insert(data).execute()
    new_id = r.data[0]["id"] if r.data else None
    # Auto-toevoeg eigen klanten als coach
    if coach_id and new_id:
        klanten = supabase.table("carboo_coach_klanten").select("klant_id").eq("coach_id", coach_id).eq("status", "actief").execute()
        for k in (klanten.data or []):
            try:
                supabase.table("carboo_challenge_deelnemers").insert({"challenge_id": new_id, "user_id": k["klant_id"]}).execute()
            except: pass
    return {"ok": True, "id": new_id}

@app.delete("/api/challenges/{ch_id}")
async def verwijder_challenge(ch_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    is_adm = await is_admin(user, supabase)
    if is_adm:
        supabase.table("carboo_challenges").update({"actief": False}).eq("id", ch_id).execute()
    else:
        supabase.table("carboo_challenges").update({"actief": False}).eq("id", ch_id).eq("maker_id", user.id).execute()
    return {"ok": True}

@app.post("/api/challenges/{ch_id}/deelnemen")
async def deelnemen(ch_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    naam = getattr(user, "email", "").split("@")[0]
    try:
        supabase.table("carboo_challenge_deelnemers").insert({"challenge_id": ch_id, "user_id": user.id, "user_naam": naam}).execute()
    except Exception as e:
        if "duplicate" not in str(e).lower():
            raise HTTPException(500, str(e))
    return {"ok": True}

@app.post("/api/challenges/{ch_id}/score")
async def update_score(ch_id: str, item: ChallengeScore, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Update eigen manuele score."""
    supabase.table("carboo_challenge_deelnemers").update({"manuele_score": item.manuele_score}).eq("challenge_id", ch_id).eq("user_id", user.id).execute()
    return {"ok": True}

@app.get("/api/challenges/{ch_id}/leaderboard")
async def leaderboard(ch_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    ch = supabase.table("carboo_challenges").select("*").eq("id", ch_id).single().execute()
    if not ch.data:
        raise HTTPException(404, "Challenge niet gevonden")
    ch_data = ch.data
    deeln = supabase.table("carboo_challenge_deelnemers").select("*").eq("challenge_id", ch_id).execute()
    deelnemers = deeln.data or []
    auto_types = {"plantaardig", "performance", "vocht"}
    results = []
    for d in deelnemers:
        if ch_data["type"] in auto_types:
            score = _bereken_auto_score(supabase, d["user_id"], ch_data["type"], ch_data["start_datum"], ch_data["eind_datum"])
        else:
            score = d.get("manuele_score")
        results.append({
            "user_id": d["user_id"], "user_naam": d.get("user_naam") or "Deelnemer",
            "score": float(score) if score is not None else None,
            "is_mij": d["user_id"] == user.id,
        })
    # Sorteer
    met_score = [r for r in results if r["score"] is not None]
    zonder = [r for r in results if r["score"] is None]
    hoger_beter = ch_data.get("hoger_beter", True)
    met_score.sort(key=lambda x: x["score"], reverse=hoger_beter)
    for i, r in enumerate(met_score): r["rang"] = i + 1
    # Badges berekenen
    totaal = len(met_score)
    if totaal > 0:
        for r in met_score:
            if r["rang"] == 1: r["badge"] = "diamond"
            elif r["rang"] <= max(1, round(totaal * 0.1)): r["badge"] = "goud"
            elif r["rang"] <= max(1, round(totaal * 0.5)): r["badge"] = "zilver"
            else: r["badge"] = "brons"
    for r in zonder: r["rang"] = None; r["badge"] = None
    return {"challenge": ch_data, "leaderboard": met_score + zonder}

@app.get("/api/badges")
async def mijn_badges(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Haal opgeslagen badges van user op."""
    r = supabase.table("carboo_badges").select("*, carboo_challenges(titel, type, eind_datum)").eq("user_id", user.id).order("toegekend_op", desc=True).execute()
    return {"badges": r.data or []}

@app.post("/api/challenges/{ch_id}/badges-toekennen")
async def toekennen_badges(ch_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Admin/coach kent definitieve badges toe aan einde challenge."""
    is_adm = await is_admin(user, supabase)
    ch = supabase.table("carboo_challenges").select("*").eq("id", ch_id).single().execute()
    if not ch.data: raise HTTPException(404, "Niet gevonden")
    if not is_adm and ch.data["maker_id"] != user.id:
        raise HTTPException(403, "Geen rechten")
    # Recompute leaderboard
    lb = await leaderboard(ch_id, user, supabase)
    for r in lb["leaderboard"]:
        if r.get("badge"):
            try:
                supabase.table("carboo_badges").upsert({"user_id": r["user_id"], "challenge_id": ch_id, "niveau": r["badge"]}, on_conflict="user_id,challenge_id").execute()
            except: pass
    return {"ok": True, "toegekend": sum(1 for r in lb["leaderboard"] if r.get("badge"))}



# ─── NOTIFICATIES ──────────────────────────────────────────────────────────────

@app.get("/api/notificaties")
async def get_notificaties(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Bereken alle actieve notificaties voor de huidige user."""
    from datetime import date, datetime, timedelta, timezone
    notifs = []
    today = date.today()

    # Welke notif_keys zijn al gelezen?
    gelezen_r = supabase.table("carboo_notificatie_gelezen").select("notificatie_key").eq("user_id", user.id).execute()
    gelezen_keys = set(g["notificatie_key"] for g in (gelezen_r.data or []))

    def add(key: str, icon: str, titel: str, tekst: str, link: str = None, niveau: str = "info"):
        if key in gelezen_keys: return
        notifs.append({"key": key, "icon": icon, "titel": titel, "tekst": tekst, "link": link, "niveau": niveau, "aangemaakt": datetime.now(timezone.utc).isoformat()})

    # 1. Dagschema 2 dagen niet ingevuld
    try:
        recent = supabase.table("fuelc_dagboek").select("datum").eq("user_id", user.id).gte("datum", (today - timedelta(days=3)).isoformat()).execute()
        dagen_ingevuld = set((it["datum"] or "")[:10] for it in (recent.data or []))
        gemiste = []
        for d in range(1, 3):
            checkdag = (today - timedelta(days=d)).isoformat()
            if checkdag not in dagen_ingevuld:
                gemiste.append(checkdag)
        if len(gemiste) >= 2:
            add(f"dagschema_inactief_{today.isoformat()}", "📋", "Dagschema bijhouden",
                f"Je hebt je dagschema {len(gemiste)} dagen niet ingevuld. Houd je voeding bij voor betere inzichten!",
                "/app/fueling", "warning")
    except Exception as e: print(f"notif dagboek fout: {e}")

    # 2. Gewicht 7 dagen niet — alleen bij doel = gewichtsverlies
    try:
        prof = supabase.table("fuelc_profiel").select("doel,energie_doel").eq("user_id", user.id).execute()
        if prof.data:
            doel = (prof.data[0].get("doel") or "").lower()
            if "afval" in doel or "verlies" in doel or "gewichtsverlies" in doel:
                gewicht = supabase.table("fuelc_gewicht").select("datum").eq("user_id", user.id).gte("datum", (today - timedelta(days=8)).isoformat()).execute()
                if not gewicht.data:
                    add(f"gewicht_inactief_{today.isoformat()}", "⚖️", "Gewicht bijhouden",
                        "Je hebt je gewicht 7+ dagen niet ingegeven. Wekelijks wegen helpt bij gewichtsverlies!",
                        "/app/fueling", "warning")
    except Exception as e: print(f"notif gewicht fout: {e}")

    # 3 + 4. Nieuwe feed posts (admin + coach posts laatste 7 dagen)
    try:
        sinds = (today - timedelta(days=7)).isoformat()
        # Admin posts voor iedereen
        adm_posts = supabase.table("carboo_coach_prikbord").select("id,titel,aangemaakt,is_admin_post").eq("is_admin_post", True).gte("aangemaakt", sinds).order("aangemaakt", desc=True).limit(5).execute()
        for p in (adm_posts.data or []):
            add(f"feed_post_{p['id']}", "📣", "Nieuwe Carboo post", p["titel"], "/app/coach-zone", "info")
        # Posts van eigen coaches
        klant_coaches = supabase.table("carboo_coach_klanten").select("coach_id").eq("klant_id", user.id).eq("status", "actief").execute()
        coach_ids = [k["coach_id"] for k in (klant_coaches.data or [])]
        if coach_ids:
            coach_posts = supabase.table("carboo_coach_prikbord").select("id,titel,aangemaakt").in_("coach_id", coach_ids).eq("is_admin_post", False).gte("aangemaakt", sinds).order("aangemaakt", desc=True).limit(5).execute()
            for p in (coach_posts.data or []):
                add(f"feed_post_{p['id']}", "💬", "Nieuwe post van je coach", p["titel"], "/app/coach-zone", "info")
    except Exception as e: print(f"notif feed fout: {e}")

    # 5. Coach feedback (ongelezen opmerkingen)
    try:
        opm = supabase.table("carboo_coach_opmerkingen").select("id,tekst,aangemaakt").eq("klant_id", user.id).eq("gelezen", False).order("aangemaakt", desc=True).limit(5).execute()
        for o in (opm.data or []):
            preview = (o["tekst"] or "")[:60] + ("..." if len(o.get("tekst") or "") > 60 else "")
            add(f"coach_feedback_{o['id']}", "💬", "Feedback van je coach", preview, "/app/coach-zone", "info")
    except Exception as e: print(f"notif feedback fout: {e}")

    # 6. Forum reactie op eigen post
    try:
        sinds = (today - timedelta(days=7)).isoformat()
        # Eigen posts ophalen
        eigen = supabase.table("carboo_forum").select("id,titel").eq("auteur_id", user.id).execute()
        if eigen.data:
            post_ids = [p["id"] for p in eigen.data]
            reacties = supabase.table("carboo_forum_reacties").select("id,tekst,auteur_naam,post_id,aangemaakt").in_("post_id", post_ids).neq("auteur_id", user.id).gte("aangemaakt", sinds).order("aangemaakt", desc=True).limit(5).execute()
            post_titels = {p["id"]: p["titel"] for p in eigen.data}
            for r in (reacties.data or []):
                add(f"forum_reactie_{r['id']}", "💬", f"Nieuwe reactie van {r.get('auteur_naam', 'iemand')}",
                    f"Op '{post_titels.get(r['post_id'], 'je post')}'", "/app/coach-zone", "info")
    except Exception as e: print(f"notif forum fout: {e}")

    # 7. Nieuwe challenge beschikbaar
    try:
        sinds = (today - timedelta(days=7)).isoformat()
        # Globale + relevante coach challenges van laatste 7 dagen
        is_adm = await is_admin(user, supabase)
        coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
        coach_id = coach.data[0]["id"] if coach.data else None
        klant_coaches_r = supabase.table("carboo_coach_klanten").select("coach_id").eq("klant_id", user.id).eq("status", "actief").execute()
        klant_coach_ids = [c["coach_id"] for c in (klant_coaches_r.data or [])]
        alle = supabase.table("carboo_challenges").select("id,titel,maker_type,coach_id,aangemaakt").eq("actief", True).gte("aangemaakt", sinds).execute()
        for ch in (alle.data or []):
            relevant = False
            if ch["maker_type"] == "admin": relevant = True
            elif coach_id and ch["coach_id"] == coach_id: relevant = False  # eigen challenge
            elif ch["coach_id"] in klant_coach_ids: relevant = True
            if relevant:
                add(f"challenge_nieuw_{ch['id']}", "🏆", "Nieuwe challenge", ch["titel"], "/app/coach-zone", "info")
    except Exception as e: print(f"notif challenge nieuw fout: {e}")

    # 8. Challenge eindigt over 3 dagen (waar je in deelneemt)
    try:
        eind3 = (today + timedelta(days=3)).isoformat()
        eind1 = (today + timedelta(days=1)).isoformat()
        mijn_deeln = supabase.table("carboo_challenge_deelnemers").select("challenge_id").eq("user_id", user.id).execute()
        ch_ids = [d["challenge_id"] for d in (mijn_deeln.data or [])]
        if ch_ids:
            eindigend = supabase.table("carboo_challenges").select("id,titel,eind_datum").in_("id", ch_ids).eq("actief", True).gte("eind_datum", eind1).lte("eind_datum", eind3).execute()
            for ch in (eindigend.data or []):
                dagen = (date.fromisoformat(ch["eind_datum"]) - today).days
                add(f"challenge_eind_{ch['id']}_{today.isoformat()}", "⏰", "Challenge bijna afgelopen",
                    f"'{ch['titel']}' eindigt over {dagen} dag{'en' if dagen != 1 else ''}!", "/app/coach-zone", "warning")
    except Exception as e: print(f"notif challenge eind fout: {e}")

    # 9. Abonnement vervalt over 7 dagen
    try:
        vervalt = (today + timedelta(days=7)).isoformat()
        abo = supabase.table("carboo_abonnementen").select("id,pakket,verval_datum").eq("user_id", user.id).eq("status", "actief").lte("verval_datum", vervalt).gte("verval_datum", today.isoformat()).execute()
        for a in (abo.data or []):
            dagen = (date.fromisoformat(a["verval_datum"]) - today).days
            add(f"abo_vervalt_{a['id']}_{today.isoformat()}", "⚠️", "Abonnement verloopt",
                f"Je '{a['pakket']}' abonnement vervalt over {dagen} dag{'en' if dagen != 1 else ''}",
                "/app/account", "warning")
    except Exception as e: print(f"notif abo fout: {e}")

    # Sorteer op niveau dan datum
    niveau_orde = {"warning": 0, "info": 1}
    notifs.sort(key=lambda n: (niveau_orde.get(n["niveau"], 2), n["aangemaakt"]), reverse=False)
    return {"notificaties": notifs, "ongelezen": len(notifs)}

class NotifGelezen(BaseModel):
    key: str

@app.post("/api/notificaties/gelezen")
async def markeer_notif_gelezen(item: NotifGelezen, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        supabase.table("carboo_notificatie_gelezen").insert({"user_id": user.id, "notificatie_key": item.key}).execute()
    except Exception as e:
        if "duplicate" not in str(e).lower():
            raise HTTPException(500, str(e))
    return {"ok": True}

@app.post("/api/notificaties/alles-gelezen")
async def markeer_alles_gelezen(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Markeer ALLE huidige notificaties als gelezen."""
    huidige = await get_notificaties(user, supabase)
    for n in huidige["notificaties"]:
        try:
            supabase.table("carboo_notificatie_gelezen").insert({"user_id": user.id, "notificatie_key": n["key"]}).execute()
        except: pass
    return {"ok": True, "aantal": huidige["ongelezen"]}



@app.post("/api/auth/trial-starten")
async def start_trial(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Geeft een 7-daags 'alles' trial abo aan een nieuwe user. Eénmalig per user_id."""
    from datetime import date, timedelta
    # Check of user al ooit een abo had
    bestaand = supabase.table("carboo_abonnementen").select("id").eq("user_id", user.id).execute()
    if bestaand.data:
        return {"ok": False, "reden": "Al abonnement gehad"}
    verval = date.today() + timedelta(days=7)
    supabase.table("carboo_abonnementen").insert({
        "user_id": user.id,
        "pakket": "alles",
        "status": "actief",
        "prijs": 0,
        "start_datum": date.today().isoformat(),
        "verval_datum": verval.isoformat(),
        "mollie_payment_id": "trial_auto_7d",
    }).execute()
    return {"ok": True, "verval_datum": verval.isoformat()}



# ─── MOLLIE BETALINGEN ────────────────────────────────────────────────────────

# Extra credits pakketten
EXTRA_CREDITS = {
    "raceplan_1": {"label": "1 extra raceplan", "credits": 1, "prijs": "2.99"},
    "raceplan_5": {"label": "5 extra raceplannen", "credits": 5, "prijs": "9.99"},
}

class BetalingAanmaken(BaseModel):
    pakket_id: str  # 'fueling', 'race', 'gut', 'alles', 'coach', 'raceplan_1', 'raceplan_5'

@app.get("/api/mollie/mijn-abonnement")
async def mijn_abonnement(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Haal actieve abonnementen + prijzen op voor de gebruiker."""
    abos = supabase.table("carboo_abonnementen").select("*").eq("user_id", user.id).eq("status", "actief").gte("verval_datum", "today").execute()
    prijzen_r = supabase.table("carboo_prijzen").select("*").eq("actief", True).execute()
    prijzen_map = {}
    for p in (prijzen_r.data or []):
        prijzen_map[p["id"]] = {"prijs": str(p["prijs"]), "label": p["label"]}
    # Credits ophalen
    geb = supabase.table("carboo_gebruikers").select("credits").eq("id", user.id).single().execute()
    credits = (geb.data or {}).get("credits", 0)
    return {"abonnementen": abos.data or [], "prijzen": prijzen_map, "credits": credits, "extra_credits_pakketten": EXTRA_CREDITS}

@app.post("/api/mollie/betaling-aanmaken")
async def betaling_aanmaken(item: BetalingAanmaken, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Maak een Mollie payment aan. Werkt voor abos én extra credits."""
    pakket_id = item.pakket_id
    is_credits = pakket_id in EXTRA_CREDITS

    if is_credits:
        pakket_info = EXTRA_CREDITS[pakket_id]
        bedrag = pakket_info["prijs"]
        omschrijving = f"Carboo - {pakket_info['label']}"
    else:
        prijs_r = supabase.table("carboo_prijzen").select("*").eq("id", pakket_id).single().execute()
        if not prijs_r.data:
            raise HTTPException(404, f"Pakket '{pakket_id}' niet gevonden")
        bedrag = f"{float(prijs_r.data['prijs']):.2f}"
        omschrijving = f"Carboo - {prijs_r.data['label']} (1 maand)"

    # Email opvragen
    try:
        users = supabase.auth.admin.list_users()
        email = next((u.email for u in users if str(u.id) == str(user.id)), None)
    except: email = None

    try:
        payment = mollie_client.payments.create({
            "amount": {"currency": "EUR", "value": bedrag},
            "description": omschrijving,
            "redirectUrl": f"{APP_URL}/app/abonnement?betaling=ok&pakket={pakket_id}",
            "webhookUrl": WEBHOOK_URL,
            "metadata": {
                "user_id": str(user.id),
                "pakket_id": pakket_id,
                "is_credits": is_credits,
                "email": email or "",
            }
        })
        return {"checkout_url": payment.checkout_url, "payment_id": payment.id}
    except Exception as e:
        raise HTTPException(500, f"Mollie fout: {str(e)}")

@app.post("/api/mollie/webhook")
async def mollie_webhook(request: Request, supabase: Client = Depends(get_supabase)):
    """Mollie roept dit aan na elke status verandering."""
    try:
        form = await request.form()
        payment_id = form.get("id")
        if not payment_id:
            return {"ok": False, "reden": "Geen id"}

        # Probeer met SDK, fallback naar directe HTTP call bij SSL/connectie problemen
        payment = None
        last_err = None
        for poging in range(3):
            try:
                payment = mollie_client.payments.get(payment_id)
                break
            except Exception as err:
                last_err = err
                print(f"Mollie SDK poging {poging+1} faalde: {err}")
                import time
                time.sleep(0.5 * (poging + 1))
        if payment is None:
            # Fallback: direct HTTP call met httpx
            try:
                import asyncio
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(
                        f"https://api.mollie.com/v2/payments/{payment_id}",
                        headers={"Authorization": f"Bearer {os.getenv('MOLLIE_API_KEY')}"}
                    )
                    if resp.status_code != 200:
                        raise Exception(f"Mollie HTTP {resp.status_code}: {resp.text}")
                    pd = resp.json()
                    class P:
                        pass
                    payment = P()
                    payment.id = pd.get("id")
                    payment.status = pd.get("status")
                    payment.metadata = pd.get("metadata") or {}
                    payment.amount = pd.get("amount") or {"value": "0", "currency": "EUR"}
                    payment.is_paid = lambda: pd.get("status") == "paid"
            except Exception as fallback_err:
                print(f"Mollie fallback faalde: {fallback_err}")
                raise Exception(f"Kan Mollie payment niet ophalen: {last_err or fallback_err}")

        if not payment.is_paid():
            return {"ok": True, "status": str(payment.status)}

        metadata = payment.metadata or {}
        user_id = metadata.get("user_id")
        pakket_id = metadata.get("pakket_id")
        is_credits = metadata.get("is_credits", False)

        if not user_id or not pakket_id:
            return {"ok": False, "reden": "Geen user_id of pakket_id in metadata"}

        # Check of we deze payment al verwerkt hebben (idempotentie)
        bestaand = supabase.table("carboo_abonnementen").select("id").eq("mollie_payment_id", payment_id).execute()
        if bestaand.data:
            return {"ok": True, "reden": "Al verwerkt"}

        from datetime import date, timedelta
        if is_credits:
            # Extra credits toevoegen
            pakket_info = EXTRA_CREDITS.get(pakket_id, {})
            credits_toe = pakket_info.get("credits", 0)
            huidig = supabase.table("carboo_gebruikers").select("credits").eq("id", user_id).single().execute()
            nieuwe_credits = (huidig.data.get("credits", 0) if huidig.data else 0) + credits_toe
            supabase.table("carboo_gebruikers").update({"credits": nieuwe_credits}).eq("id", user_id).execute()
            # Log transactie
            try:
                supabase.table("carboo_transacties").insert({
                    "user_id": user_id, "credits": credits_toe,
                    "omschrijving": pakket_info.get("label", "Extra credits"),
                    "mollie_payment_id": payment_id,
                    "bedrag": float(payment.amount["value"]),
                }).execute()
            except: pass
        else:
            # Abonnement aanmaken/verlengen — 30 dagen vanaf vandaag
            verval = date.today() + timedelta(days=30)
            # Check of er al een actief abo is van dit pakket → verleng vanaf vervaldatum
            bestaand_abo = supabase.table("carboo_abonnementen").select("verval_datum").eq("user_id", user_id).eq("pakket", pakket_id).eq("status", "actief").execute()
            if bestaand_abo.data:
                huidig_verval = date.fromisoformat(bestaand_abo.data[0]["verval_datum"])
                if huidig_verval > date.today():
                    verval = huidig_verval + timedelta(days=30)

            supabase.table("carboo_abonnementen").insert({
                "user_id": user_id, "pakket": pakket_id, "status": "actief",
                "prijs": float(payment.amount["value"]),
                "start_datum": date.today().isoformat(),
                "verval_datum": verval.isoformat(),
                "mollie_payment_id": payment_id,
            }).execute()

            # Race of Alles abo → credits OVERRIDE naar 5
            if pakket_id in ("race", "alles"):
                supabase.table("carboo_gebruikers").update({"credits": 5}).eq("id", user_id).execute()

        return {"ok": True}
    except Exception as e:
        print(f"Mollie webhook fout: {e}")
        # Belangrijk: 500 returnen zodat Mollie het opnieuw probeert (max 14 dagen retry)
        raise HTTPException(500, f"Webhook verwerking faalde: {str(e)}")

@app.delete("/api/mollie/abonnement/{pakket_id}")
async def annuleer_abonnement(pakket_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Markeer abonnement als 'niet automatisch verlengen' — blijft actief tot vervaldatum."""
    supabase.table("carboo_abonnementen").update({"auto_verleng": False}).eq("user_id", user.id).eq("pakket", pakket_id).eq("status", "actief").execute()
    return {"ok": True, "bericht": "Automatische verlenging gestopt. Je abonnement blijft actief tot vervaldatum."}



# ─── SJABLONEN ─────────────────────────────────────────────────────────────────

class SjabloonMaak(BaseModel):
    naam: str
    items: List[dict] = []

@app.get("/api/fuelc/sjablonen")
async def lijst_sjablonen(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_sjablonen").select("*").eq("user_id", user.id).order("aangemaakt", desc=True).execute()
    return {"sjablonen": r.data or []}

@app.post("/api/fuelc/sjablonen")
async def maak_sjabloon(item: SjabloonMaak, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    if not item.naam.strip():
        raise HTTPException(400, "Naam verplicht")
    data = {"user_id": user.id, "naam": item.naam.strip(), "items": item.items}
    r = supabase.table("carboo_sjablonen").insert(data).execute()
    return {"ok": True, "sjabloon": r.data[0] if r.data else None}

@app.delete("/api/fuelc/sjablonen/{sjabloon_id}")
async def verwijder_sjabloon(sjabloon_id: str, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_sjablonen").delete().eq("id", sjabloon_id).eq("user_id", user.id).execute()
    return {"ok": True}



# ─── STRAVA INTEGRATIE ─────────────────────────────────────────────────────────

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_OAUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"

SPORT_ACTIVITY_TYPES = {
    "Ride", "VirtualRide", "EBikeRide", "MountainBikeRide", "GravelRide",
    "Run", "VirtualRun", "TrailRun",
    "Swim",
    "Workout", "WeightTraining", "Crossfit", "Elliptical", "Rowing", "StairStepper",
    "Hike",
}

SPORT_TYPE_NL = {
    "Ride": "Fietsen", "VirtualRide": "Indoor fietsen", "EBikeRide": "E-bike",
    "MountainBikeRide": "Mountainbiken", "GravelRide": "Gravel",
    "Run": "Lopen", "VirtualRun": "Indoor lopen", "TrailRun": "Trail",
    "Swim": "Zwemmen",
    "Workout": "Workout", "WeightTraining": "Krachttraining",
    "Crossfit": "Crossfit", "Elliptical": "Crosstrainer",
    "Rowing": "Roeien", "StairStepper": "Stairs",
    "Hike": "Wandeling",
}

@app.get("/api/strava/auth-url")
async def strava_auth_url(user=Depends(get_current_user)):
    """Geef de Strava OAuth URL terug om naartoe te redirecten."""
    if not STRAVA_CLIENT_ID:
        raise HTTPException(500, "Strava niet geconfigureerd")
    redirect_uri = f"{APP_URL}/app/fueling"
    scope = "read,activity:read_all"
    state = str(user.id)  # zodat we user kunnen identificeren in callback
    url = (
        f"{STRAVA_OAUTH_URL}?client_id={STRAVA_CLIENT_ID}"
        f"&response_type=code&redirect_uri={redirect_uri}"
        f"&approval_prompt=auto&scope={scope}&state={state}"
    )
    return {"auth_url": url}

class StravaCallback(BaseModel):
    code: str

@app.post("/api/strava/callback")
async def strava_callback(item: StravaCallback, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Wissel de OAuth code uit voor een access token en bewaar."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(STRAVA_TOKEN_URL, data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": item.code,
            "grant_type": "authorization_code",
        })
    if r.status_code != 200:
        raise HTTPException(400, f"Strava OAuth fout: {r.text}")
    data = r.json()
    athlete = data.get("athlete", {})
    from datetime import datetime, timezone
    expires_at = datetime.fromtimestamp(data["expires_at"], tz=timezone.utc).isoformat()
    record = {
        "user_id": user.id,
        "strava_athlete_id": athlete.get("id"),
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "token_expires_at": expires_at,
        "atleet_naam": f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
    }
    # Upsert
    try:
        supabase.table("carboo_strava_koppelingen").upsert(record, on_conflict="user_id").execute()
    except Exception as e:
        raise HTTPException(500, f"Opslaan fout: {str(e)}")
    return {"ok": True, "atleet_naam": record["atleet_naam"]}

@app.get("/api/strava/status")
async def strava_status(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    r = supabase.table("carboo_strava_koppelingen").select("atleet_naam,laatste_sync,gekoppeld_op").eq("user_id", user.id).execute()
    if not r.data:
        return {"gekoppeld": False}
    d = r.data[0]
    return {
        "gekoppeld": True,
        "atleet_naam": d.get("atleet_naam"),
        "laatste_sync": d.get("laatste_sync"),
        "gekoppeld_op": d.get("gekoppeld_op"),
    }

@app.delete("/api/strava/koppel")
async def strava_ontkoppel(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    supabase.table("carboo_strava_koppelingen").delete().eq("user_id", user.id).execute()
    return {"ok": True}

async def _refresh_token_indien_nodig(koppeling: dict, supabase: Client):
    """Refresh access token als die is verlopen."""
    from datetime import datetime, timezone
    exp = datetime.fromisoformat(koppeling["token_expires_at"].replace("Z", "+00:00"))
    if exp > datetime.now(timezone.utc):
        return koppeling["access_token"]
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(STRAVA_TOKEN_URL, data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": koppeling["refresh_token"],
        })
    if r.status_code != 200:
        raise HTTPException(401, "Strava refresh faalde - opnieuw koppelen vereist")
    d = r.json()
    expires_at = datetime.fromtimestamp(d["expires_at"], tz=timezone.utc).isoformat()
    supabase.table("carboo_strava_koppelingen").update({
        "access_token": d["access_token"],
        "refresh_token": d["refresh_token"],
        "token_expires_at": expires_at,
    }).eq("user_id", koppeling["user_id"]).execute()
    return d["access_token"]

@app.post("/api/strava/sync")
async def strava_sync(historie: bool = False, dagen: int = 7, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Haal nieuwe Strava activiteiten op. Met ?historie=true&dagen=N: laatste N dagen."""
    from datetime import datetime, timezone, timedelta
    k_r = supabase.table("carboo_strava_koppelingen").select("*").eq("user_id", user.id).execute()
    if not k_r.data:
        raise HTTPException(404, "Strava niet gekoppeld")
    k = k_r.data[0]
    token = await _refresh_token_indien_nodig(k, supabase)
    # Bepaal vanaf wanneer
    if historie:
        sinds = datetime.now(timezone.utc) - timedelta(days=max(1, min(dagen, 90)))
    elif k.get("laatste_sync"):
        sinds = datetime.fromisoformat(k["laatste_sync"].replace("Z", "+00:00"))
    else:
        sinds = datetime.fromisoformat(k["gekoppeld_op"].replace("Z", "+00:00"))
    after_ts = int(sinds.timestamp())
    print(f"[strava] sync voor user {user.id} sinds {sinds.isoformat()} (historie={historie})")
    # Strava activities ophalen
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{STRAVA_API_BASE}/athlete/activities",
            headers={"Authorization": f"Bearer {token}"},
            params={"after": after_ts, "per_page": 50},
        )
    if r.status_code != 200:
        raise HTTPException(500, f"Strava API fout: {r.text}")
    activities = r.json()
    print(f"[strava] {len(activities)} activiteiten ontvangen van Strava")
    for a in activities[:5]:
        print(f"[strava]   - {a.get('start_date_local')} {a.get('type')} / {a.get('sport_type')} '{a.get('name')}'")
    # Filter alleen sport types
    sport_activities = [a for a in activities if a.get("sport_type") in SPORT_ACTIVITY_TYPES or a.get("type") in SPORT_ACTIVITY_TYPES]
    print(f"[strava] {len(sport_activities)} sport activiteiten na filter")

    nieuwe_imports = []
    conflicten = []

    for a in sport_activities:
        sport_type = a.get("sport_type") or a.get("type")
        sport_nl = SPORT_TYPE_NL.get(sport_type, sport_type)
        datum = a["start_date_local"][:10]
        duur_min = round(a.get("moving_time", 0) / 60)
        kcal = round(a.get("calories", 0)) if a.get("calories") else round(duur_min * 8)  # fallback schatting
        naam = a.get("name", sport_nl)
        strava_id = a["id"]
        # Check of we deze al hebben (idempotentie)
        bestaand = supabase.table("fuelc_trainingen").select("id").eq("user_id", user.id).eq("strava_activity_id", strava_id).execute()
        if bestaand.data:
            continue
        # Check voor conflict op dezelfde datum
        zelfde_dag = supabase.table("fuelc_trainingen").select("id,sport,duur_min,kcal_verbranding,bron").eq("user_id", user.id).eq("datum", datum).execute()
        if zelfde_dag.data and any(t.get("bron", "manueel") == "manueel" for t in zelfde_dag.data):
            # Conflict! Vraag aan user
            conflicten.append({
                "strava_activity_id": strava_id,
                "datum": datum,
                "strava": {"naam": naam, "sport": sport_nl, "duur_min": duur_min, "kcal": kcal},
                "bestaand": [{"id": t["id"], "sport": t.get("sport"), "duur_min": t.get("duur_min"), "kcal_verbranding": t.get("kcal_verbranding")} for t in zelfde_dag.data if t.get("bron", "manueel") == "manueel"],
            })
        else:
            # Geen conflict, gewoon importeren
            try:
                supabase.table("fuelc_trainingen").insert({
                    "user_id": user.id, "datum": datum,
                    "sport": sport_nl, "duur_min": duur_min,
                    "kcal_verbranding": kcal, "bron": "strava",
                    "strava_activity_id": strava_id,
                    "naam": naam,
                }).execute()
                nieuwe_imports.append({"datum": datum, "naam": naam, "duur_min": duur_min, "kcal": kcal})
            except Exception as e:
                print(f"Strava import fout: {e}")

    # Update laatste_sync
    supabase.table("carboo_strava_koppelingen").update({
        "laatste_sync": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", user.id).execute()

    return {
        "ok": True,
        "geimporteerd": len(nieuwe_imports),
        "imports": nieuwe_imports,
        "conflicten": conflicten,
    }

class StravaConflictResolve(BaseModel):
    strava_activity_id: int
    datum: str
    naam: str
    sport: str
    duur_min: int
    kcal: int
    keuze: str  # 'strava' = vervang bestaande, 'behoud' = negeer strava, 'beide' = beide laten staan
    bestaand_id: Optional[str] = None

@app.post("/api/strava/conflict-oplos")
async def strava_conflict_oplos(item: StravaConflictResolve, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """User koos hoe conflict op te lossen."""
    if item.keuze == "behoud":
        # Strava negeren, niets doen (markeer dat we deze gezien hebben - voeg een geblokkeerd record toe is overkill)
        return {"ok": True, "actie": "Strava genegeerd"}

    if item.keuze == "strava":
        # Verwijder de bestaande manuele training en importeer Strava
        if item.bestaand_id:
            supabase.table("fuelc_trainingen").delete().eq("id", item.bestaand_id).eq("user_id", user.id).execute()

    # Voor 'strava' en 'beide': importeer Strava
    try:
        supabase.table("fuelc_trainingen").insert({
            "user_id": user.id, "datum": item.datum,
            "sport": item.sport, "duur_min": item.duur_min,
            "kcal_verbranding": item.kcal, "bron": "strava",
            "strava_activity_id": item.strava_activity_id,
            "naam": item.naam,
        }).execute()
        return {"ok": True, "actie": "Strava geïmporteerd"}
    except Exception as e:
        raise HTTPException(500, f"Import fout: {str(e)}")


# ─── GARMIN INTEGRATIE ─────────────────────────────────────────────────────────

import random

def _gen_pairing_code() -> str:
    """Genereer 6-cijferige pairing code."""
    return str(random.randint(100000, 999999))

@app.get("/api/garmin/pairing-code")
async def garmin_pairing_code(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Genereer of haal bestaande pairing code op voor user."""
    r = supabase.table("carboo_garmin_pairing").select("*").eq("user_id", user.id).execute()
    if r.data:
        d = r.data[0]
        return {
            "code": d["pairing_code"],
            "gekoppeld": d.get("gekoppeld", False),
            "gekoppeld_op": d.get("gekoppeld_op"),
        }
    # Genereer nieuwe code (uniek)
    for _ in range(20):
        code = _gen_pairing_code()
        bestaand = supabase.table("carboo_garmin_pairing").select("id").eq("pairing_code", code).execute()
        if not bestaand.data:
            supabase.table("carboo_garmin_pairing").insert({
                "user_id": user.id,
                "pairing_code": code,
            }).execute()
            return {"code": code, "gekoppeld": False, "gekoppeld_op": None}
    raise HTTPException(500, "Kon geen unieke code genereren")

@app.post("/api/garmin/reset-code")
async def garmin_reset_code(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Reset pairing code (bv. als verloren of nieuwe Garmin)."""
    supabase.table("carboo_garmin_pairing").delete().eq("user_id", user.id).execute()
    return await garmin_pairing_code(user, supabase)

class GarminActiefPlan(BaseModel):
    rapport_id: str

@app.post("/api/garmin/zet-actief")
async def garmin_zet_actief(item: GarminActiefPlan, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Markeer een rapport als 'actief voor Garmin'. Zet alle andere op false."""
    supabase.table("carboo_rapporten").update({"actief_voor_garmin": False}).eq("user_id", user.id).execute()
    r = supabase.table("carboo_rapporten").update({"actief_voor_garmin": True}).eq("id", item.rapport_id).eq("user_id", user.id).execute()
    if not r.data:
        raise HTTPException(404, "Rapport niet gevonden")
    return {"ok": True}

@app.get("/api/garmin/actief-plan/{pairing_code}")
async def garmin_actief_plan(pairing_code: str, supabase: Client = Depends(get_supabase)):
    """
    Public endpoint - geen auth nodig. Garmin device roept dit aan met de pairing code.
    Returns compact JSON met het actieve raceplan voor Garmin display.
    """
    # Vind user via pairing code
    p_r = supabase.table("carboo_garmin_pairing").select("user_id,gekoppeld").eq("pairing_code", pairing_code).execute()
    if not p_r.data:
        raise HTTPException(404, "Ongeldige pairing code")
    user_id = p_r.data[0]["user_id"]
    # Markeer als gekoppeld bij eerste call
    if not p_r.data[0].get("gekoppeld"):
        from datetime import datetime, timezone
        supabase.table("carboo_garmin_pairing").update({
            "gekoppeld": True,
            "gekoppeld_op": datetime.now(timezone.utc).isoformat(),
        }).eq("pairing_code", pairing_code).execute()
    # Haal actief raceplan op
    r_r = supabase.table("carboo_rapporten").select("id,naam,meta,html").eq("user_id", user_id).eq("actief_voor_garmin", True).eq("type", "race_html").order("datum", desc=True).limit(1).execute()
    if not r_r.data:
        return {"ok": False, "fout": "Geen actief raceplan gekozen"}
    rapport = r_r.data[0]
    # Parse plan uit meta (race_data zit daar)
    meta = rapport.get("meta", {}) or {}
    # Probeer plan items op te halen uit de HTML of meta
    # Voor nu: gebruik dummy items uit meta indien beschikbaar
    plan_items_raw = meta.get("plan_items", [])
    # plan_items kan een dict zijn (per uur), normaliseer naar list
    items_list = []
    if isinstance(plan_items_raw, dict):
        # Per uur dict: {0: [{...}, ...], 1: [{...}, ...]}
        for uur_key in sorted(plan_items_raw.keys(), key=lambda k: int(k) if str(k).isdigit() else 0):
            uur_items = plan_items_raw[uur_key]
            if not isinstance(uur_items, list):
                continue
            try:
                uur_int = int(uur_key)
            except:
                uur_int = 0
            for it in uur_items:
                if not isinstance(it, dict):
                    continue
                try:
                    # min binnen het uur
                    min_offset = int(str(it.get("min", "0")).replace("min", "").strip())
                    tijd_sec = (uur_int * 60 + min_offset) * 60
                    emoji_to_type = {"⚡": "GEL", "🥤": "SD", "🍌": "VAST", "☕": "CAF", "🍫": "VAST", "🍪": "VAST", "🌾": "VAST"}
                    type_short = emoji_to_type.get(it.get("emoji", ""), "GEL")
                    items_list.append({
                        "tijd": tijd_sec,
                        "type": type_short,
                        "label": str(it.get("naam", ""))[:30],
                    })
                except Exception as ex:
                    print(f"[garmin] item parse fout: {ex}")
                    continue
    elif isinstance(plan_items_raw, list):
        items_list = plan_items_raw
    # Fallback: parse uit HTML als nog steeds leeg
    if not items_list:
        items_list = _parse_plan_uit_html(rapport.get("html", ""))
    print(f"[garmin] returned {len(items_list)} items voor pairing {pairing_code}")
    return {
        "ok": True,
        "naam": rapport.get("naam", "Raceplan"),
        "sport": meta.get("sport", "Fietsen"),
        "totale_min": meta.get("totale_min", 180),
        "items": items_list[:30],
    }

def _parse_plan_uit_html(html: str) -> list:
    """Eenvoudige parser - zoekt voedingsmomenten in racemap HTML."""
    import re
    items = []
    # Match patroon: tijd (XX:YY) + type (GEL/SD/VAST/CAF) + label
    # Voorbeeld: "09:20 GEL 6D groot +200ml"
    # Parse vanuit racemap rows in HTML
    pattern = r'(\d{1,3}):(\d{2})\s*</[^>]+>\s*<[^>]+>\s*(SD|GEL|VAST|CAF|H2O)\s*</[^>]+>\s*([^<]+)'
    matches = re.findall(pattern, html)
    for m in matches:
        try:
            uren, mins, type_, label = m
            tijd_sec = (int(uren) * 60 + int(mins)) * 60
            items.append({
                "tijd": tijd_sec,
                "type": type_,
                "label": label.strip()[:30],
            })
        except:
            continue
    return items


@app.get("/api/admin/forum/verborgen")
async def admin_verborgen_posts(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Admin: lijst verborgen posts om eventueel te herstellen."""
    if not await is_admin(user, supabase):
        raise HTTPException(403, "Geen toegang")
    r = supabase.table("carboo_forum").select("*").eq("verborgen", True).order("aangemaakt", desc=True).limit(50).execute()
    return {"posts": r.data or []}



# ═══════════════════════════════════════════════════════
# MOLLIE BETALINGEN
# ═══════════════════════════════════════════════════════

import hmac
import hashlib

MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "")
APP_URL = os.environ.get("APP_URL", "https://carboo.app")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://carboo-api.onrender.com/api/mollie/webhook")

# Service-role client voor admin operaties
def _get_admin_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase_admin = _get_admin_client()

PAKKETTEN = {
    "fueling": {"label": "Fueling",            "module": "fueling"},
    "race":    {"label": "Race Nutrition Plan", "module": "race"},
    "gut":     {"label": "Train the Gut",       "module": "gut"},
    "alles":   {"label": "Alles-in-één",        "module": "alles"},
    "coach":   {"label": "Coach Zone",          "module": "coach"},
}

def get_prijs(pakket_id: str) -> float:
    try:
        r = supabase_admin.table("carboo_prijzen").select("prijs").eq("id", pakket_id).single().execute()
        return float(r.data["prijs"])
    except:
        fallback = {"fueling": 5.99, "race": 4.99, "gut": 3.99, "alles": 9.99, "coach": 14.99}
        return fallback.get(pakket_id, 9.99)


class BetalingRequest(BaseModel):
    pakket_id: str


async def _get_of_maak_mollie_klant(user_id: str, email: str, naam: str) -> str:
    bestaand = supabase_admin.table("carboo_mollie_klanten").select("mollie_customer_id").eq("user_id", user_id).execute()
    if bestaand.data:
        return bestaand.data[0]["mollie_customer_id"]
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.mollie.com/v2/customers",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}", "Content-Type": "application/json"},
            json={"name": naam or email, "email": email, "locale": "nl_BE"},
            timeout=10
        )
        data = resp.json()
        if resp.status_code != 201:
            raise HTTPException(500, f"Mollie customer fout: {data.get('detail')}")
        customer_id = data["id"]
        supabase_admin.table("carboo_mollie_klanten").insert({
            "user_id": user_id, "mollie_customer_id": customer_id
        }).execute()
        return customer_id


@app.post("/api/mollie/betaling-aanmaken")
async def maak_betaling(item: BetalingRequest, user=Depends(get_current_user)):
    if item.pakket_id not in PAKKETTEN:
        raise HTTPException(400, "Ongeldig pakket")
    if not MOLLIE_API_KEY:
        raise HTTPException(500, "Mollie niet geconfigureerd")

    pakket = PAKKETTEN[item.pakket_id]
    prijs = get_prijs(item.pakket_id)
    customer_id = await _get_of_maak_mollie_klant(user.id, user.email, user.email)
    payload = {
        "amount": {"currency": "EUR", "value": f"{prijs:.2f}"},
        "description": f"Carboo — {pakket['label']} (maandelijks)",
        "sequenceType": "first",
        "customerId": customer_id,
        "redirectUrl": f"{APP_URL}/app/abonnement?betaling=ok&pakket={item.pakket_id}&user_id={user.id}",
        "webhookUrl": WEBHOOK_URL,
        "metadata": {
            "user_id": user.id,
            "user_email": user.email,
            "pakket": item.pakket_id,
            "type": "abonnement_eerste"
        },
        "locale": "nl_BE",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.mollie.com/v2/payments",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}", "Content-Type": "application/json"},
            json=payload, timeout=10
        )
        data = resp.json()
        if resp.status_code == 201:
            return {"checkout_url": data["_links"]["checkout"]["href"], "payment_id": data["id"]}
        raise HTTPException(500, f"Mollie fout: {data.get('detail', 'Onbekende fout')}")


@app.post("/api/mollie/webhook")
async def mollie_webhook(request: Request):
    body = await request.form()
    payment_id = body.get("id", "")
    if not payment_id:
        return {"status": "ok"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.mollie.com/v2/payments/{payment_id}",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"}, timeout=10
        )
        if resp.status_code != 200:
            return {"status": "ok"}
        betaling = resp.json()
    if betaling.get("status") != "paid":
        return {"status": "ok"}
    metadata = betaling.get("metadata", {})
    user_id = metadata.get("user_id", "")
    pakket = metadata.get("pakket", "")
    if not user_id or not pakket:
        return {"status": "ok"}
    from datetime import date, timedelta
    verval = (date.today().replace(day=1) + timedelta(days=32)).replace(day=date.today().day)
    bestaand = supabase_admin.table("carboo_abonnementen").select("id").eq("user_id", user_id).eq("pakket", pakket).execute()
    betaling_type = metadata.get("type", "abonnement")
    prijs = get_prijs(pakket)
    if bestaand.data:
        supabase_admin.table("carboo_abonnementen").update({
            "status": "actief",
            "verval_datum": verval.isoformat(),
            "mollie_payment_id": payment_id,
            "bijgewerkt": "now()"
        }).eq("user_id", user_id).eq("pakket", pakket).execute()
    else:
        supabase_admin.table("carboo_abonnementen").insert({
            "user_id": user_id, "pakket": pakket, "status": "actief",
            "prijs": prijs, "start_datum": date.today().isoformat(),
            "verval_datum": verval.isoformat(), "mollie_payment_id": payment_id,
        }).execute()
    if betaling_type == "abonnement_eerste":
        klant_rec = supabase_admin.table("carboo_mollie_klanten").select("mollie_customer_id").eq("user_id", user_id).execute()
        if klant_rec.data:
            customer_id = klant_rec.data[0]["mollie_customer_id"]
            async with httpx.AsyncClient() as client:
                import asyncio
                await asyncio.sleep(2)
                sub_resp = await client.post(
                    f"https://api.mollie.com/v2/customers/{customer_id}/subscriptions",
                    headers={"Authorization": f"Bearer {MOLLIE_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "amount": {"currency": "EUR", "value": f"{prijs:.2f}"},
                        "interval": "1 month",
                        "description": f"Carboo — {PAKKETTEN.get(pakket, {}).get('label', pakket)} (maandelijks)",
                        "webhookUrl": WEBHOOK_URL,
                        "metadata": {"user_id": user_id, "pakket": pakket, "type": "abonnement_verlenging"},
                    },
                    timeout=15
                )
                if sub_resp.status_code == 201:
                    sub_data = sub_resp.json()
                    supabase_admin.table("carboo_abonnementen").update({
                        "mollie_subscription_id": sub_data["id"]
                    }).eq("user_id", user_id).eq("pakket", pakket).execute()
                    supabase_admin.table("carboo_mollie_klanten").update({
                        "mollie_mandate_id": sub_data.get("mandateId", "")
                    }).eq("user_id", user_id).execute()
    return {"status": "ok"}


@app.get("/api/mollie/mijn-abonnement")
async def mijn_abonnement(user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    abos = supabase.table("carboo_abonnementen").select("*").eq("user_id", user.id).eq("status", "actief").execute()
    prijzen = supabase.table("carboo_prijzen").select("*").execute()
    return {
        "abonnementen": abos.data or [],
        "prijzen": {p["id"]: p for p in (prijzen.data or [])}
    }


@app.get("/api/mollie/prijzen")
async def get_prijzen(supabase: Client = Depends(get_supabase)):
    prijzen = supabase.table("carboo_prijzen").select("*").eq("actief", True).execute()
    return {"prijzen": prijzen.data or []}


class PrijsUpdate(BaseModel):
    prijs: float

@app.put("/api/admin/prijzen/{pakket_id}")
async def update_prijs(pakket_id: str, item: PrijsUpdate, user=Depends(get_current_user)):
    admin = supabase_admin.table("carboo_admins").select("user_id").eq("user_id", user.id).execute()
    if not admin.data:
        raise HTTPException(403, "Geen toegang")
    supabase_admin.table("carboo_prijzen").update({
        "prijs": item.prijs, "bijgewerkt": "now()"
    }).eq("id", pakket_id).execute()
    return {"ok": True, "pakket": pakket_id, "nieuwe_prijs": item.prijs}


@app.get("/api/admin/abonnementen")
async def admin_abonnementen(user=Depends(get_current_user)):
    admin = supabase_admin.table("carboo_admins").select("user_id").eq("user_id", user.id).execute()
    if not admin.data:
        raise HTTPException(403, "Geen toegang")
    abos = supabase_admin.table("carboo_abonnementen").select("*").order("aangemaakt", desc=True).execute()
    return {"abonnementen": abos.data or []}


@app.post("/api/admin/abonnement-toewijzen")
async def abonnement_toewijzen(item: dict, user=Depends(get_current_user)):
    """Admin wijst abonnement toe. Als gebruiker niet bestaat + wachtwoord opgegeven → maakt account aan."""
    admin = supabase_admin.table("carboo_admins").select("user_id").eq("user_id", user.id).execute()
    if not admin.data:
        raise HTTPException(403, "Geen toegang")

    email = (item.get("email") or "").strip().lower()
    wachtwoord = (item.get("wachtwoord") or "").strip()
    user_id = item.get("user_id", "")
    nieuwe_gebruiker = False

    if email and not user_id:
        # Zoek of gebruiker al bestaat
        try:
            users = supabase_admin.auth.admin.list_users()
            match = next((u for u in users if getattr(u, 'email', None) == email), None)
            if match:
                user_id = str(match.id)
            elif wachtwoord:
                # Maak nieuwe gebruiker aan
                if len(wachtwoord) < 6:
                    raise HTTPException(400, "Wachtwoord moet minstens 6 karakters lang zijn")
                created = supabase_admin.auth.admin.create_user({
                    "email": email,
                    "password": wachtwoord,
                    "email_confirm": True
                })
                if created and created.user:
                    user_id = str(created.user.id)
                    nieuwe_gebruiker = True
                else:
                    raise HTTPException(500, "Kon gebruiker niet aanmaken")
            else:
                raise HTTPException(404, f"Gebruiker '{email}' bestaat niet. Geef ook een wachtwoord op om een nieuw account aan te maken.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Fout: {e}")

    if not user_id:
        raise HTTPException(400, "Geef email op")

    from datetime import date, timedelta
    duur = int(item.get("duur_maanden", 1))
    verval = date.today() + timedelta(days=30 * duur)
    supabase_admin.table("carboo_abonnementen").upsert({
        "user_id": user_id,
        "pakket": item.get("pakket", "alles"),
        "status": "actief",
        "prijs": float(item.get("prijs", 0)),
        "start_datum": date.today().isoformat(),
        "verval_datum": verval.isoformat(),
        "mollie_payment_id": f"admin_manueel_{user.id}",
    }).execute()

    return {"ok": True, "user_id": user_id, "nieuwe_gebruiker": nieuwe_gebruiker, "email": email}

@app.delete("/api/mollie/abonnement/{pakket_id}")
async def annuleer_abonnement(pakket_id: str, user=Depends(get_current_user)):
    abo = supabase_admin.table("carboo_abonnementen").select("mollie_subscription_id").eq("user_id", user.id).eq("pakket", pakket_id).execute()
    if not abo.data or not abo.data[0].get("mollie_subscription_id"):
        raise HTTPException(404, "Geen actief abonnement gevonden")
    sub_id = abo.data[0]["mollie_subscription_id"]
    klant = supabase_admin.table("carboo_mollie_klanten").select("mollie_customer_id").eq("user_id", user.id).execute()
    if not klant.data:
        raise HTTPException(404, "Geen Mollie klant gevonden")
    customer_id = klant.data[0]["mollie_customer_id"]
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"https://api.mollie.com/v2/customers/{customer_id}/subscriptions/{sub_id}",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"}, timeout=10
        )
    supabase_admin.table("carboo_abonnementen").update({
        "mollie_subscription_id": None, "bijgewerkt": "now()"
    }).eq("user_id", user.id).eq("pakket", pakket_id).execute()
    return {"ok": True, "bericht": "Automatische verlenging geannuleerd. Abonnement loopt door tot vervaldatum."}
