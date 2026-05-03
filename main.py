from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os
from supabase import create_client, Client

app = FastAPI(title="Carboo API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://carboo-next.vercel.app",
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
                        "text": 'Analyseer dit voedseletiket. Geef ALLEEN een JSON object terug, geen uitleg. Gebruik dit formaat: {"naam":"","categorie":"Granen en brood","portie_g":100,"portie_label":"100g","kcal":0,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,"natrium":0,"kalium":0,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0,"gi":0}'
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
