import io

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''@app.post("/api/coach/reacties")
async def plaats_reactie(item: CoachReactie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    if coach.data:
        coach_id = coach.data[0]["id"]
        opm = supabase.table("carboo_coach_opmerkingen").select("id").eq("id", item.opmerking_id).eq("coach_id", coach_id).execute()
        if opm.data:
            supabase.table("carboo_coach_reacties").insert({"opmerking_id": item.opmerking_id, "coach_id": coach_id, "tekst": item.tekst, "auteur_type": "coach"}).execute()
            return {"ok": True}'''

new = '''@app.post("/api/coach/reacties")
async def plaats_reactie(item: CoachReactie, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    print(f"[REACTIE DEBUG] user.id={user.id} opmerking_id={item.opmerking_id}")
    coach = supabase.table("carboo_coaches").select("id").eq("user_id", user.id).execute()
    print(f"[REACTIE DEBUG] coach.data={coach.data}")
    if coach.data:
        coach_id = coach.data[0]["id"]
        opm = supabase.table("carboo_coach_opmerkingen").select("id").eq("id", item.opmerking_id).eq("coach_id", coach_id).execute()
        print(f"[REACTIE DEBUG] opm.data={opm.data} coach_id={coach_id}")
        if opm.data:
            r = supabase.table("carboo_coach_reacties").insert({"opmerking_id": item.opmerking_id, "coach_id": coach_id, "tekst": item.tekst, "auteur_type": "coach"}).execute()
            print(f"[REACTIE DEBUG] insert resultaat: {r.data}")
            return {"ok": True}'''

if old in content:
    content = content.replace(old, new)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("OK - debug toegevoegd")
else:
    print("MISS")
