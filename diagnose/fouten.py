"""
diagnose/fouten.py — telt (alleen lezen) de combinaties actief / laatste_fout
in fuelc_push_abonnementen.

Gebruik (vanuit carboo-api):   python lokaal-start.py diagnose/fouten.py
"""
from collections import Counter
from datetime import date
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client
v = dotenv_values(Path(__file__).resolve().parent.parent / ".env")
sb = create_client(v["SUPABASE_URL"], v["SUPABASE_SERVICE_KEY"])
r = sb.table("fuelc_push_abonnementen").select("actief, laatste_fout").execute().data
print(date.today())
print(Counter((x["actief"], repr(x["laatste_fout"])) for x in r))
