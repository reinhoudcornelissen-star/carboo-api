import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''@app.post("/api/coach/reacties")
async def plaats_reactie(item: CoachReactie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    opm = supabase.table("carboo_coach_opmerkingen").select("id").eq("id", item.opmerking_id).eq("klant_id", user.id).execute()
    if not opm.data:
        raise HTTPException(403, "Geen toegang")
    supabase.table("carboo_coach_reacties").insert({"opmerking_id": item.opmerking_id, "klant_id": user.id, "tekst": item.tekst}).execute()
    supabase.table("carboo_coach_opmerkingen").update({"gelezen": True}).eq("id", item.opmerking_id).execute()
    return {"ok": True}'''

new = '''@app.post("/api/coach/reacties")
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
    return {"ok": True}'''

if old in content:
    content = content.replace(old, new)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("OK - patch applied")
else:
    print("MISS - old block not found")
