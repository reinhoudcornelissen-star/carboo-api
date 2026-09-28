"""
lokaal-start.py — draait een Python-script met de certificaten van Windows.

Waarom: Norton 360 scant HTTPS-verkeer en zet er een eigen certificaat op.
Windows vertrouwt dat, Python standaard niet, en dan faalt elke verbinding
met Supabase of de pushdiensten met CERTIFICATE_VERIFY_FAILED.
truststore laat Python de certificatenlijst van Windows gebruiken.

Alleen nodig op een pc met zo'n scanner; op Render niet.

Gebruik (vanuit carboo-api):
    python lokaal-start.py push-diagnose.py --droog
    python lokaal-start.py -m uvicorn main:app --reload

Eenmalig nodig:  pip install truststore
"""

import sys
import runpy

try:
    import truststore
except ImportError:
    sys.exit("Ontbreekt: truststore.  Installeer met:  pip install truststore")

truststore.inject_into_ssl()

if len(sys.argv) < 2:
    sys.exit(__doc__)

if sys.argv[1] == "-m":
    if len(sys.argv) < 3:
        sys.exit("Na -m hoort een modulenaam, bv. uvicorn.")
    module = sys.argv[2]
    sys.argv = [module] + sys.argv[3:]
    runpy.run_module(module, run_name="__main__", alter_sys=True)
else:
    script = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_path(script, run_name="__main__")
