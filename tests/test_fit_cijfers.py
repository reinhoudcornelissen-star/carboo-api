"""FIT-CIJFERS-V1 — kerncijfers en TSS uit een synthetisch .fit-bestand
(1 u fietsen: 20' 200 W / 20' 300 W / 20' 150 W, hartslag 130/165/120).
Draaien: python lokaal-start.py tests/test_fit_cijfers.py <pad naar test.fit>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fit_cijfers import kerncijfers, tss_van  # noqa: E402

pad = sys.argv[1]
k = kerncijfers(open(pad, "rb").read())
print({x: k[x] for x in ("sport", "duur_s", "afstand_m", "gem_vermogen", "max_vermogen", "np", "gem_hartslag", "max_hartslag", "som_hr2", "gem_snelheid_kmh") if x in k})
assert k["duur_s"] == 3600 and abs(k["afstand_m"] - 32400) < 1
assert abs(k["gem_vermogen"] - 216.7) < 0.2 and k["max_vermogen"] == 300
# NP: gemiddelde van de vierde machten van 200/300/150 (de 30 s-overgangen wegen amper): (200^4+300^4+150^4)/3 ^ 0.25
verwacht_np = ((200 ** 4 + 300 ** 4 + 150 ** 4) / 3) ** 0.25
assert abs(k["np"] - verwacht_np) < 1.5, (k["np"], verwacht_np)
assert k["mmp"]["1200"] == 300.0 and 240 < k["mmp"]["3600"] < 220 + 10 or abs(k["mmp"]["3600"] - 216.7) < 0.2
assert abs(k["gem_hartslag"] - 138.3) < 0.2 and k["max_hartslag"] == 165
assert k["som_hr2"] == 1200 * (130 ** 2 + 165 ** 2 + 120 ** 2)
assert k["hist_w"]["300"] == 1200 and k["hist_hr"]["165"] == 1200
print("kerncijfers ok")

# TSS: met FTP 250 → duur*np*IF/(ftp*3600)*100 ; hrTSS met drempel 160
tss_w, bron = tss_van(k, 250, 160)
verwacht = 3600 * k["np"] * (k["np"] / 250) / (250 * 3600) * 100
assert bron == "vermogen" and abs(tss_w - verwacht) < 1, (tss_w, verwacht)
tss_hr, bron = tss_van(k, None, 160)
assert bron == "hartslag" and tss_hr == round(k["som_hr2"] / 160 ** 2 / 3600 * 100)
assert tss_van(k, None, None) == (None, "geen")
print("tss ok:", tss_w, "(vermogen)", tss_hr, "(hartslag)")
print("ALLES OK")
