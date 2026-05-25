"""
Daily cron job: markeer verlopen abonnementen als status=verlopen.
Wordt elke nacht om 03:00 UTC uitgevoerd via Render Cron Job.
"""
import os
import sys
from datetime import date
from supabase import create_client

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("[CRON] FOUT: SUPABASE_URL of SUPABASE_SERVICE_KEY ontbreekt", file=sys.stderr)
        sys.exit(1)
    
    supabase = create_client(url, key)
    vandaag = date.today().isoformat()
    
    try:
        rijen = supabase.table("carboo_abonnementen").select("id,user_id,pakket,verval_datum").eq("status", "actief").lt("verval_datum", vandaag).execute()
        aantal = len(rijen.data or [])
        
        if aantal == 0:
            print(f"[CRON {vandaag}] Geen verlopen abonnementen om op te kuisen")
            return
        
        result = supabase.table("carboo_abonnementen").update({
            "status": "verlopen",
            "bijgewerkt": "now()"
        }).eq("status", "actief").lt("verval_datum", vandaag).execute()
        
        print(f"[CRON {vandaag}] {aantal} abonnementen gemarkeerd als verlopen:")
        for r in (rijen.data or []):
            print(f"  - user={r['user_id']} pakket={r['pakket']} verval={r['verval_datum']}")
    
    except Exception as e:
        print(f"[CRON] FOUT: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()