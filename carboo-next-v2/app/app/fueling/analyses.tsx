"use client"
import { useState, useEffect, useMemo } from "react"

const API = "https://carboo-api.onrender.com"

function r1(n: number) { return Math.round(n * 10) / 10 }
function rnd(n: number) { return Math.round(n) }

// ── MINI CHART COMPONENTEN ─────────────────────────────────────────────────
function BalkChart({ labels, waarden, doel, hoogte = 120 }: any) {
  const max = Math.max(...waarden.filter((v: number) => v > 0), doel * 1.2, 1)
  const barHoogte = hoogte - 24
  const doelY = barHoogte - Math.round(doel / max * barHoogte)
  return (
    <div style={{ position: "relative", height: hoogte }}>
      {/* SVG stippellijn */}
      <svg style={{ position: "absolute", top: 0, left: 0, width: "100%", height: barHoogte, pointerEvents: "none", zIndex: 2 }}>
        <line x1="0" y1={doelY} x2="100%" y2={doelY} stroke="#f97316" strokeWidth="1.5" strokeDasharray="6,4" />
      </svg>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: barHoogte }}>
        {waarden.map((v: number, i: number) => {
          const h = v > 0 ? Math.max(2, Math.round(v / max * barHoogte)) : 0
          const k = v > doel * 1.1 ? "#ef4444" : v >= doel * 0.85 ? "#22c55e" : v >= doel * 0.5 ? "#f97316" : "#3b82f6"
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%" }}>
              <div title={`${labels[i]}: ${rnd(v)}`} style={{ width: "100%", height: h, background: h > 0 ? k : "transparent", borderRadius: "3px 3px 0 0" }} />
            </div>
          )
        })}
      </div>
      {/* X-as labels */}
      <div style={{ display: "flex", gap: 2, height: 20 }}>
        {labels.map((l: string, i: number) => (
          <div key={i} style={{ flex: 1, fontSize: "0.45rem", color: "#475569", textAlign: "center", overflow: "hidden", paddingTop: 2 }}>
            {labels.length <= 14 ? l : (i % Math.ceil(labels.length / 10) === 0 ? l : "")}
          </div>
        ))}
      </div>
    </div>
  )
}

function LijnChart({ labels, datasets, hoogte = 120 }: any) {
  const allVals = datasets.flatMap((d: any) => d.waarden).filter((v: any) => v !== null)
  const max = Math.max(...allVals, 1)
  const min = 0
  const range = max - min || 1
  const w = 100 / Math.max(labels.length - 1, 1)

  return (
    <svg viewBox={`0 0 300 ${hoogte}`} style={{ width: "100%", height: hoogte }}>
      {datasets.map((ds: any, di: number) => {
        const points = ds.waarden.map((v: number | null, i: number) =>
          v !== null ? `${i * w * 3},${hoogte - 10 - ((v - min) / range * (hoogte - 20))}` : null
        ).filter(Boolean)
        const d = points.reduce((acc: string, p: string, i: number) => acc + (i === 0 ? `M${p}` : `L${p}`), "")
        return (
          <g key={di}>
            <path d={d} fill="none" stroke={ds.kleur} strokeWidth="2" strokeLinejoin="round" />
            {ds.doel && (
              <line x1="0" y1={hoogte - 10 - ((ds.doel - min) / range * (hoogte - 20))} x2="300" y2={hoogte - 10 - ((ds.doel - min) / range * (hoogte - 20))}
                stroke="#f97316" strokeWidth="1" strokeDasharray="5,3" />
            )}
          </g>
        )
      })}
    </svg>
  )
}

function MetricCard({ label, waarde, sub, kleur = "#f97316" }: any) {
  return (
    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "14px 16px", textAlign: "center" }}>
      <div style={{ fontSize: "0.6rem", color: "#64748b", letterSpacing: 2, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 800, color: kleur }}>{waarde}</div>
      {sub && <div style={{ fontSize: "0.65rem", color: "#64748b", marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function ProgressBalk({ waarde, doel, kleur, hoogte = 8 }: any) {
  const pct = Math.min(100, Math.round(waarde / Math.max(doel, 1) * 100))
  const k = waarde > doel * 1.1 ? "#ef4444" : waarde >= doel * 0.85 ? "#22c55e" : waarde >= doel * 0.5 ? "#f97316" : "#3b82f6"
  return (
    <div style={{ background: "#1e293b", borderRadius: hoogte / 2, height: hoogte }}>
      <div style={{ width: `${pct}%`, height: "100%", background: kleur || k, borderRadius: hoogte / 2, transition: "width 0.3s" }} />
    </div>
  )
}

// ── VOEDSEL DB voor GI lookup ──────────────────────────────────────────────
const GI_DB: Record<string, number> = {
  "Volkorenbrood":50,"Wit brood":70,"Havermout":55,"Rijst wit gekookt":64,
  "Rijst volkoren gekookt":50,"Pasta volkoren gekookt":42,"Aardappel gekookt":72,
  "Zoete aardappel gekookt":61,"Quinoa gekookt":53,"Rijstwafel naturel":82,
  "Banaan":51,"Appel":38,"Sinaasappel":43,"Bosbes":25,"Aardbei":40,
  "Mango":51,"Kiwi":39,"Dadel gedroogd":42,"Rozijnen":64,"Peer":38,
  "Linzen gekookt":32,"Kikkererwten gekookt":28,"Sportdrank isotoon":70,
  "Energiegel standaard":80,"Energiereep":65,"Honing":58,"Tomatensaus":35,
}

// NEVO micronutriënten lookup per 100g
const NEVO_MICRO: Record<string, { verz: number, kalium: number, calcium: number, ijzer: number, vitd: number, vitb12: number, omega3: number }> = {
  "Volkorenbrood":     { verz:0.5, kalium:230, calcium:25,  ijzer:2.0, vitd:0,   vitb12:0,   omega3:0.1 },
  "Havermout":         { verz:1.2, kalium:360, calcium:50,  ijzer:3.9, vitd:0,   vitb12:0,   omega3:0.1 },
  "Rijst wit gekookt": { verz:0,   kalium:35,  calcium:10,  ijzer:0.2, vitd:0,   vitb12:0,   omega3:0   },
  "Pasta volkoren gekookt": { verz:0.1, kalium:90, calcium:20, ijzer:1.5, vitd:0, vitb12:0,  omega3:0.1 },
  "Aardappel gekookt": { verz:0,   kalium:410, calcium:6,   ijzer:0.3, vitd:0,   vitb12:0,   omega3:0   },
  "Zoete aardappel gekookt": { verz:0, kalium:337, calcium:30, ijzer:0.7, vitd:0, vitb12:0,  omega3:0 },
  "Quinoa gekookt":    { verz:0.2, kalium:172, calcium:17,  ijzer:1.5, vitd:0,   vitb12:0,   omega3:0.1 },
  "Banaan":            { verz:0,   kalium:358, calcium:5,   ijzer:0.3, vitd:0,   vitb12:0,   omega3:0   },
  "Appel":             { verz:0,   kalium:107, calcium:6,   ijzer:0.1, vitd:0,   vitb12:0,   omega3:0   },
  "Halfvolle melk":    { verz:1.1, kalium:150, calcium:120, ijzer:0.1, vitd:0.1, vitb12:0.5, omega3:0   },
  "Volle melk":        { verz:2.4, kalium:150, calcium:120, ijzer:0.1, vitd:0.1, vitb12:0.5, omega3:0.1 },
  "Griekse yoghurt":   { verz:5.0, kalium:170, calcium:110, ijzer:0.1, vitd:0.1, vitb12:0.8, omega3:0.1 },
  "Kwark (mager)":     { verz:0,   kalium:130, calcium:95,  ijzer:0.1, vitd:0,   vitb12:0.5, omega3:0   },
  "Skyr":              { verz:0,   kalium:160, calcium:130, ijzer:0.1, vitd:0.1, vitb12:1.0, omega3:0   },
  "Ei (gekookt)":      { verz:3.0, kalium:130, calcium:50,  ijzer:1.8, vitd:2.0, vitb12:0.9, omega3:0.1 },
  "Kipfilet":          { verz:1.0, kalium:370, calcium:12,  ijzer:1.0, vitd:0.1, vitb12:0.3, omega3:0.1 },
  "Zalm":              { verz:3.0, kalium:440, calcium:15,  ijzer:0.5, vitd:9.0, vitb12:3.0, omega3:2.3 },
  "Tonijn (blik)":     { verz:0.2, kalium:280, calcium:10,  ijzer:1.3, vitd:3.0, vitb12:2.0, omega3:0.3 },
  "Rundvlees (mager)": { verz:5.0, kalium:300, calcium:10,  ijzer:2.5, vitd:0,   vitb12:2.0, omega3:0.1 },
  "Amandelen":         { verz:4.0, kalium:705, calcium:264, ijzer:3.7, vitd:0,   vitb12:0,   omega3:0.1 },
  "Walnoten":          { verz:6.0, kalium:441, calcium:98,  ijzer:2.9, vitd:0,   vitb12:0,   omega3:2.6 },
  "Pindakaas":         { verz:10.0,kalium:705, calcium:49,  ijzer:1.9, vitd:0,   vitb12:0,   omega3:0.1 },
  "Broccoli":          { verz:0,   kalium:316, calcium:47,  ijzer:0.7, vitd:0,   vitb12:0,   omega3:0.1 },
  "Spinazie":          { verz:0,   kalium:466, calcium:99,  ijzer:2.7, vitd:0,   vitb12:0,   omega3:0.1 },
  "Avocado":           { verz:2.0, kalium:485, calcium:12,  ijzer:0.6, vitd:0,   vitb12:0,   omega3:0.1 },
  "Linzen":            { verz:0,   kalium:365, calcium:19,  ijzer:3.3, vitd:0,   vitb12:0,   omega3:0.1 },
  "Kikkererwten":      { verz:0.3, kalium:291, calcium:49,  ijzer:2.9, vitd:0,   vitb12:0,   omega3:0.1 },
  "Olijfolie":         { verz:14.0,kalium:0,   calcium:0,   ijzer:0.1, vitd:0,   vitb12:0,   omega3:0.8 },
  "Weiprotein":        { verz:1.0, kalium:200, calcium:200, ijzer:0.5, vitd:0,   vitb12:1.0, omega3:0.2 },
  "Sportdrank":        { verz:0,   kalium:80,  calcium:0,   ijzer:0,   vitd:0,   vitb12:0,   omega3:0   },
}

const PLANTAARDIG = new Set(["Granen & brood","Groenten","Fruit","Noten & zaden","Peulvruchten","Sojaproducten"])
const DIERLIJK = new Set(["Vlees & vis","Zuivel","Eieren"])

function herkenCategorie(naam: string, cat: string): string {
  if (cat && cat !== "Overige") return cat
  const n = naam.toLowerCase()
  if (["tofu","tempeh","sojayoghurt","sojamelk","edamame"].some(w => n.includes(w))) return "Sojaproducten"
  if (["boon","linze","kikker","hummus","spliterwt","erwt"].some(w => n.includes(w))) return "Peulvruchten"
  if (["noot","amandel","cashew","walnoot","pinda","chiazaad","lijnzaad","pompoenpit"].some(w => n.includes(w))) return "Noten & zaden"
  if (["garnaal","zalm","tonijn","kabeljauw","makreel","haring","kip","vlees","gehakt","varken","rund","lam","steak","ham","worst","filet","kalkoen","biefstuk","vis"].some(w => n.includes(w))) return "Vlees & vis"
  if (["melk","yoghurt","kwark","kaas","room","boter","skyr","plattekaas","mozzarella"].some(w => n.includes(w))) return "Zuivel"
  if (["ei ","ei,","eieren","omelet","roerei"].some(w => n.includes(w)) || naam.toLowerCase().startsWith("ei")) return "Eieren"
  if (["brood","pasta","rijst","havermout","wrap","cracker","muesli","granola","couscous","quinoa","aardappel","pannenkoek","wafel"].some(w => n.includes(w))) return "Granen & brood"
  if (["broccoli","spinazie","wortel","tomaat","paprika","courgette","sla","komkommer","champignon","avocado","ui","prei","witloof","groente"].some(w => n.includes(w))) return "Groenten"
  if (["appel","peer","banaan","aardbei","bosbes","mango","kiwi","sinaas","druif","dadel","rozijn","fruit"].some(w => n.includes(w))) return "Fruit"
  if (["shake","proteine","whey","energiegel","sportdrank","recovery","isotoon"].some(w => n.includes(w))) return "Sportvoeding"
  if (["olijfolie","zonnebloemolie","kokosolie","olie"].some(w => n.includes(w))) return "Vetten & oliën"
  return "Overige"
}

// ── HOOFDCOMPONENT ─────────────────────────────────────────────────────────
export default function Analyses({ profiel, token, setProfiel }: { profiel: any; token: string | null; setProfiel?: (p: any) => void }) {
  const [periode, setPeriode] = useState<7 | 30 | 90>(7)
  const [actieveTab, setActieveTab] = useState(0)
  const [dagData, setDagData] = useState<any[]>([])
  const [trainingen, setTrainingen] = useState<any[]>([])
  const [gewichtPunten, setGewichtPunten] = useState<[string, number][]>([])
  const [laden, setLaden] = useState(false)
  const [gewicht, setGewicht] = useState(profiel?.gewicht_kg || 70)
  const [gewichtOpgeslagen, setGewichtOpgeslagen] = useState(false)

  // Sync gewicht als profiel binnenkomt/verandert
  useEffect(() => {
    if (profiel?.gewicht_kg) setGewicht(profiel.gewicht_kg)
  }, [profiel?.gewicht_kg])

  const energieDoel = profiel?.energie_doel || 2000
  const khPct = profiel?.kh_doel_pct || 50
  const eiPct = profiel?.eiwit_doel_pct || 25
  const vtPct = profiel?.vet_doel_pct || 25
  const gewichtKg = profiel?.gewicht_kg || 70
  const lengteCm = profiel?.lengte_cm || 175

  // Basis doelen
  const khDoel = Math.round(energieDoel * khPct / 100 / 4)
  const eiDoel = Math.round(energieDoel * eiPct / 100 / 4)
  const vtDoel = Math.round(energieDoel * vtPct / 100 / 9)

  // Laad data — gebatcht om geheugen te sparen (max 7 calls tegelijk)
  useEffect(() => {
    if (!token) return
    setLaden(true)
    setDagData([])

    const dagenArray = Array.from({ length: periode }, (_, i) => {
      const d = new Date(Date.now() - (periode - 1 - i) * 86400000)
      return d.toISOString().split("T")[0]
    })
    const startStr = dagenArray[0]
    const eindeStr = dagenArray[dagenArray.length - 1]

    async function laadAlles() {
      // Trainingen + welzijn parallel (kleine calls)
      const [trData, welzData] = await Promise.all([
        fetch(`${API}/api/fuelc/trainingen`, { headers: { Authorization: `Bearer ${token}` } })
          .then(r => r.json()).then(d => d.trainingen || []).catch(() => []),
        fetch(`${API}/api/fuelc/welzijn?van=${startStr}&tot=${eindeStr}`, { headers: { Authorization: `Bearer ${token}` } })
          .then(r => r.json()).then(d => d.welzijn || []).catch(() => []),
      ])

      setTrainingen(trData.filter((t: any) => t.datum >= startStr && t.datum <= eindeStr))
      const gp: [string, number][] = welzData
        .filter((w: any) => w.gewicht_kg)
        .map((w: any) => [w.datum.slice(0, 10), parseFloat(w.gewicht_kg)])
      setGewichtPunten(gp)

      // Dagboek in 1 call voor het hele bereik
      const bereikData = await fetch(
        `${API}/api/fuelc/dagboek/bereik?van=${startStr}&tot=${eindeStr}`,
        { headers: { Authorization: `Bearer ${token}` } }
      ).then(r => r.json()).catch(() => ({ per_dag: {} }))

      const perDag = bereikData.per_dag || {}
      const alleDagen = dagenArray.map(d => ({ datum: d, items: perDag[d] || [] }))
      setDagData(alleDagen)
    }

    laadAlles().finally(() => setLaden(false))
  }, [token, periode])

  // Bereken stats per dag
  const dagStats = useMemo(() => {
    return dagData.map(d => {
      const items = d.items || []
      const kcal = items.reduce((a: number, i: any) => a + (i.kcal || 0), 0)
      const kh = items.reduce((a: number, i: any) => a + (i.kh_g || 0), 0)
      const eiwit = items.reduce((a: number, i: any) => a + (i.eiwit_g || 0), 0)
      const vet = items.reduce((a: number, i: any) => a + (i.vet_g || 0), 0)
      const vezels = items.reduce((a: number, i: any) => a + (i.vezels_g || 0), 0)
      // TOEGEVOEGDE suikers: enkel suikers uit bewerkte producten
      // Natuurlijke suikers (fruit, groenten, zuivel, noten) worden NIET meegeteld
      const NATUURLIJKE_CATS = ["groenten en fruit", "fruit", "groenten", "noten en zaden", "peulvruchten"]
      const NATUURLIJKE_PRODUCTEN = new Set([
        "banaan","appel","peer","sinaasappel","mandarijn","kiwi","mango","druiven","ananas",
        "kers","framboos","blauwe bessen","aardbeien","pruim","grapefruit","watermeloen",
        "abrikoos","dadels gedroogd","vijgen gedroogd","gedroogd fruit mix","rozijnen",
        "broccoli","spinazie","wortel","tomaat","paprika","courgette","sla","komkommer",
        "halfvolle melk","volle melk","griekse yoghurt","kwark","skyr","kefir","slagroom",
        "amandelen","walnoten","pindakaas","cashewnoten","hazelnoten","pistachenoten",
        "linzen","kikkererwten","edamame","zwarte bonen","spliterwten",
        "avocado","zoete aardappel","aardappel",
      ])
      const suikers = items.reduce((a: number, i: any) => {
        const naam = (i.naam || "").toLowerCase()
        const cat = (i.categorie || "").toLowerCase()
        const f = (i.hoeveelheid_g || 100) / 100
        // Sla over als het een product met enkel natuurlijke suikers is
        const isNatuurlijk = NATUURLIJKE_CATS.some(c => cat.includes(c)) ||
          Array.from(NATUURLIJKE_PRODUCTEN).some(n => naam.includes(n))
        if (isNatuurlijk) return a
        // Gebruik opgeslagen suikers_g als beschikbaar
        if (i.suikers_g > 0) return a + i.suikers_g
        // Schatting voor bewerkte producten: sportvoeding hoog, rest laag
        const khG = i.kh_g || 0
        if (cat.includes("sport")) return a + khG * 0.6
        if (naam.includes("gel") || naam.includes("sportdrank") || naam.includes("reep")) return a + khG * 0.7
        if (cat.includes("snack") || cat.includes("gebak") || cat.includes("koek")) return a + khG * 0.4
        if (cat.includes("drank") && !cat.includes("sport")) return a + khG * 0.5
        // Granen (brood, pasta, rijst, havermout, quinoa) → geen toegevoegde suikers
        if (cat.includes("granen") || naam.includes("brood") || naam.includes("pasta") ||
            naam.includes("rijst") || naam.includes("havermout") || naam.includes("quinoa") ||
            naam.includes("couscous") || naam.includes("crackers") || naam.includes("wrap"))
          return a
        return a + khG * 0.05
      }, 0)
      // Micronutriënten: gebruik opgeslagen waarde of NEVO lookup als fallback
      let verz = 0, natrium = 0, omega3 = 0, vitd = 0, vitb12 = 0, kalium = 0, calcium = 0, ijzer = 0
      items.forEach((i: any) => {
        const f = (i.hoeveelheid_g || 100) / 100
        const naam = (i.naam || "").toLowerCase()
        // Exact match eerst, dan gedeeltelijk op eerste woord
        let nevo: any = NEVO_MICRO[i.naam]
        if (!nevo) {
          const eersteWoord = naam.split(" ")[0]
          const key = Object.keys(NEVO_MICRO).find(k =>
            naam.includes(k.toLowerCase()) || k.toLowerCase().includes(eersteWoord)
          )
          nevo = key ? NEVO_MICRO[key] : {}
        }
        // > 0 check zodat expliciete 0 uit DB ook NEVO fallback triggert
        verz    += (i.verz_g    > 0 ? i.verz_g    : (nevo.verz    || 0) * f)
        natrium += (i.natrium_mg > 0 ? i.natrium_mg : 0)
        omega3  += (i.omega3_g  > 0 ? i.omega3_g  : (nevo.omega3  || 0) * f)
        vitd    += (i.vitd_mcg  > 0 ? i.vitd_mcg  : (nevo.vitd    || 0) * f)
        vitb12  += (i.vitb12_mcg > 0 ? i.vitb12_mcg : (nevo.vitb12 || 0) * f)
        kalium  += (i.kalium_mg > 0 ? i.kalium_mg : (nevo.kalium  || 0) * f)
        calcium += (i.calcium_mg > 0 ? i.calcium_mg : (nevo.calcium || 0) * f)
        ijzer   += (i.ijzer_mg  > 0 ? i.ijzer_mg  : (nevo.ijzer   || 0) * f)
      })

      // Trainingskcal voor deze dag
      const dagTrain = trainingen
        .filter((t: any) => (t.datum || "").slice(0, 10) === d.datum)
        .reduce((a: number, t: any) => a + (t.kcal_verbranding || 0), 0)
      const eDoel = energieDoel + dagTrain

      // Categorie kcal
      const catKcal: Record<string, number> = {}
      items.forEach((it: any) => {
        const cat = herkenCategorie(it.naam || "", it.categorie || "")
        catKcal[cat] = (catKcal[cat] || 0) + (it.kcal || 0)
      })

      // Performance score (0-100)
      let score = 0
      if (kcal > 0) {
        // Energiebalans (25pt) - Gaussian
        if (eDoel > 0) {
          const pctE = kcal / eDoel
          const eScore = Math.min(25, Math.round(25 * Math.exp(-Math.pow(pctE - 1, 2) / (2 * 0.18 * 0.18))))
          score += Math.max(2, eScore)
        }
        // KH (20pt) — gram vs doel
        const khDoeD = Math.round(energieDoel * khPct / 100 / 4)
        const khPctVanDoel = khDoeD > 0 ? kh / khDoeD : 0
        score += khPctVanDoel >= 0.95 ? 20 : khPctVanDoel >= 0.80 ? 14 : khPctVanDoel >= 0.60 ? 8 : khPctVanDoel >= 0.40 ? 4 : 2
        // Eiwit (20pt) — gram vs doel
        const eiDoeD = Math.round(energieDoel * eiPct / 100 / 4)
        const eiPctVanDoel = eiDoeD > 0 ? eiwit / eiDoeD : 0
        score += eiPctVanDoel >= 0.95 ? 20 : eiPctVanDoel >= 0.80 ? 14 : eiPctVanDoel >= 0.60 ? 8 : eiPctVanDoel >= 0.40 ? 4 : 2
        // Vezels (15pt)
        score += vezels >= 30 ? 15 : vezels >= 20 ? 10 : vezels >= 10 ? 5 : 0
        // Maaltijdspreiding (10pt)
        const momenten = new Set(items.map((i: any) => i.moment)).size
        score += Math.min(10, momenten * 2)
        // Vochtbalans: schat uit dagboek items
        const VOCHT_MAP: Record<string, number> = {
          "water":100,"melk":100,"yoghurt":85,"kefir":100,"koffie":100,"thee":100,
          "sap":100,"sportdrank":100,"sojamelk":100,"kokoswater":100,"smoothie":90,
          "cola":100,"fanta":100,"sprite":100,"ijsthee":100,"bouillon":100,"soep":85,
        }
        const dagVocht = items.reduce((acc: number, item: any) => {
          const n = (item.naam||"").toLowerCase()
          const c = (item.categorie||"").toLowerCase()
          const g = item.hoeveelheid_g || 0
          const match = Object.keys(VOCHT_MAP).find(k => n.includes(k))
          if (match) return acc + g * VOCHT_MAP[match] / 100
          if (["dranken","zuivel"].some(x => c.includes(x))) return acc + g * 0.9
          return acc
        }, 0)
        score += dagVocht >= 2000 ? 10 : dagVocht >= 1500 ? 7 : dagVocht >= 1000 ? 4 : dagVocht >= 500 ? 2 : 0
      }

      // Groenten & fruit in gram
      const gfGram = items.reduce((acc: number, it: any) => {
        const cat = herkenCategorie(it.naam || "", it.categorie || "")
        if (cat === "Groenten" || cat === "Fruit") return acc + (it.hoeveelheid_g || 0)
        return acc
      }, 0)

      return { ...d, kcal, kh, eiwit, vet, vezels, suikers, verz, natrium, omega3,
        vitd, vitb12, kalium, calcium, ijzer, dagTrain, eDoel, catKcal, gfGram,
        score: Math.min(100, score), heeftData: kcal > 0 }
    })
  }, [dagData, trainingen, energieDoel, khPct, eiPct, vtPct])

  const metData = dagStats.filter(d => d.heeftData)
  const n = Math.max(metData.length, 1)

  // Gemiddelden
  const gem = {
    kcal: rnd(metData.reduce((a, d) => a + d.kcal, 0) / n),
    kh: r1(metData.reduce((a, d) => a + d.kh, 0) / n),
    eiwit: r1(metData.reduce((a, d) => a + d.eiwit, 0) / n),
    vet: r1(metData.reduce((a, d) => a + d.vet, 0) / n),
    vezels: r1(metData.reduce((a, d) => a + d.vezels, 0) / n),
    suikers: r1(metData.reduce((a, d) => a + d.suikers, 0) / n),
    verz: r1(metData.reduce((a, d) => a + d.verz, 0) / n),
    omega3: r1(metData.reduce((a, d) => a + d.omega3, 0) / n),
    vitd: r1(metData.reduce((a, d) => a + d.vitd, 0) / n),
    vitb12: r1(metData.reduce((a, d) => a + d.vitb12, 0) / n),
    kalium: rnd(metData.reduce((a, d) => a + d.kalium, 0) / n),
    calcium: rnd(metData.reduce((a, d) => a + d.calcium, 0) / n),
    ijzer: r1(metData.reduce((a, d) => a + d.ijzer, 0) / n),
    score: rnd(metData.reduce((a, d) => a + d.score, 0) / n),
  }

  // Training totalen
  const trainKcal = trainingen.reduce((a, t) => a + (t.kcal_verbranding || 0), 0)
  const trainMin = trainingen.reduce((a, t) => a + (t.duur_min || 0), 0)

  // Gem trainingskcal (voor aangepaste doelen)
  const trainDagen = dagStats.filter(d => d.dagTrain > 0)
  const gemTrainKcal = trainDagen.length > 0 ? rnd(trainDagen.reduce((a, d) => a + d.dagTrain, 0) / trainDagen.length) : 0
  const energieDoelingcl = energieDoel + gemTrainKcal
  const khDoeIncl = Math.round(energieDoelingcl * khPct / 100 / 4)
  const eiDoeIncl = Math.round(energieDoelingcl * eiPct / 100 / 4)
  const vtDoeIncl = Math.round(energieDoelingcl * vtPct / 100 / 9)

  const labels = dagStats.map(d => d.datum.slice(5))

  async function slaGewichtOp() {
    if (!token) return
    try {
      const today = new Date().toISOString().split("T")[0]
      await fetch(`${API}/api/fuelc/welzijn`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ datum: today, gewicht_kg: gewicht })
      })
      // Herbereken BMR/TDEE/energiedoel op basis van nieuw gewicht en sla op in profiel
      if (profiel) {
        const g = gewicht
        const l = profiel.lengte_cm || 175
        const a = profiel.leeftijd || 30
        const gs = profiel.geslacht || "Man"
        const bmrNieuw = Math.round(10 * g + 6.25 * l - 5 * a + (gs === "Man" ? 5 : -161))
        const ACTIVITEIT_FACTOR: Record<string, number> = {
          "Weinig actief (zittend werk)": 1.2,
          "Licht actief (1-3x/week buiten)": 1.375,
          "Matig actief (3-5x/week buiten)": 1.55,
          "Zeer actief (6-7x/week buiten)": 1.725,
          "Extreem actief (2x/dag trainen)": 1.9,
        }
        const factor = ACTIVITEIT_FACTOR[profiel.activiteit] || 1.55
        const tdeeNieuw = Math.round(bmrNieuw * factor)
        const nieuwProfiel = { ...profiel, gewicht_kg: g, bmr: bmrNieuw, tdee_basis: tdeeNieuw, energie_doel: tdeeNieuw }
        // Sla op in API
        await fetch(`${API}/api/fuelc/profiel`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify(nieuwProfiel)
        }).catch(() => {})
        // Update localStorage cache
        try { localStorage.setItem("carboo_profiel", JSON.stringify(nieuwProfiel)) } catch (_) {}
        // Update parent state zodat alle tabs direct het nieuwe gewicht zien
        if (setProfiel) setProfiel(nieuwProfiel)
      }
      setGewichtOpgeslagen(true)
      setTimeout(() => setGewichtOpgeslagen(false), 2500)
    } catch {}
  }

  const TABS = ["📊 Gewicht", "🌿 Voedingskwaliteit", "🌾 Koolhydraten", "💪 Eiwit", "🧈 Vetten", "⚡ Performance"]

  if (!profiel) return (
    <div style={{ textAlign: "center", padding: "60px 20px" }}>
      <div style={{ fontSize: "2rem", marginBottom: 12 }}>📊</div>
      <div style={{ color: "#555" }}>Vul eerst je profiel in om analyses te zien.</div>
    </div>
  )

  return (
    <div>
      {/* Header + periode */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div style={{ fontSize: "0.65rem", color: "#f97316", letterSpacing: 3 }}>ANALYSES</div>
        <div style={{ display: "flex", gap: 4, background: "#0f172a", borderRadius: 8, padding: 4 }}>
          {([7, 30, 90] as const).map(p => (
            <button key={p} onClick={() => setPeriode(p)} style={{ padding: "5px 14px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: "0.78rem", fontWeight: 600, background: periode === p ? "#f97316" : "transparent", color: periode === p ? "#0c0c0c" : "#555" }}>{p}d</button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 3, marginBottom: 20, flexWrap: "wrap", borderBottom: "1px solid #1e293b", paddingBottom: 10 }}>
        {TABS.map((t, i) => (
          <button key={i} onClick={() => setActieveTab(i)} style={{ padding: "6px 12px", borderRadius: 7, border: "none", cursor: "pointer", fontSize: "0.78rem", fontWeight: 600, background: actieveTab === i ? "rgba(249,115,22,0.15)" : "transparent", color: actieveTab === i ? "#f97316" : "#555" }}>{t}</button>
        ))}
      </div>

      {laden && <div style={{ textAlign: "center", padding: 40, color: "#475569" }}>Laden...</div>}

      {!laden && metData.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px 20px", color: "#475569" }}>
          <div style={{ fontSize: "1.5rem", marginBottom: 10 }}>📋</div>
          Nog geen voedingsdata voor de laatste {periode} dagen. Vul je dagschema in.
        </div>
      )}

      {!laden && (
        <>
          {/* ── TAB 0: GEWICHT ── */}
          {actieveTab === 0 && (
            <div>
              {/* Gewicht KPIs */}
              {gewichtPunten.length > 0 ? (() => {
                const laatste = gewichtPunten[gewichtPunten.length - 1][1]
                const eerste = gewichtPunten[0][1]
                const bmi = r1(laatste / Math.pow(lengteCm / 100, 2))
                const bmiCat = bmi < 18.5 ? "Ondergewicht" : bmi < 25 ? "Normaal" : bmi < 30 ? "Overgewicht" : "Obesitas"
                const bmiK = bmi < 25 ? "#22c55e" : bmi < 30 ? "#fbbf24" : "#ef4444"
                const trend = r1(laatste - eerste)
                return (
                  <>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
                      <MetricCard label="HUIDIG GEWICHT" waarde={`${laatste} kg`} kleur="#f5f3ef" />
                      <MetricCard label="START" waarde={`${eerste} kg`} kleur="#64748b" />
                      <MetricCard label="BMI" waarde={`${bmi}`} sub={bmiCat} kleur={bmiK} />
                      <MetricCard label="TREND" waarde={Math.abs(trend) < 0.1 ? "→ Stabiel" : trend > 0 ? `▲ +${trend} kg` : `▼ ${trend} kg`}
                        kleur={Math.abs(trend) < 0.1 ? "#64748b" : trend < -0.3 ? "#22c55e" : "#f97316"} />
                    </div>
                    {/* Gewicht grafiek */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>GEWICHTSVERLOOP</div>
                      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 100 }}>
                        {gewichtPunten.slice(-30).map(([d, v], i) => {
                          const min = Math.min(...gewichtPunten.map(p => p[1])) - 2
                          const max = Math.max(...gewichtPunten.map(p => p[1])) + 2
                          const h = Math.round((v - min) / (max - min) * 80) + 10
                          return <div key={i} title={`${d}: ${v}kg`} style={{ flex: 1, height: h, background: "#22c55e", borderRadius: 2, minWidth: 4 }} />
                        })}
                      </div>
                    </div>
                  </>
                )
              })() : (
                <div style={{ background: "#1e293b", borderRadius: 10, padding: 16, marginBottom: 16, color: "#64748b", fontSize: "0.82rem" }}>
                  ⚖️ Nog geen gewicht geregistreerd. Voer hieronder je gewicht in.
                </div>
              )}

              {/* Kcal per dag vs doel */}
              {metData.length > 0 && (
                <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>KCAL PER DAG VS DOEL (incl. training)</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {dagStats.filter(d => d.heeftData).slice(-14).map(d => {
                      const pct = Math.min(130, rnd(d.kcal / Math.max(d.eDoel, 1) * 100))
                      const k = pct > 110 ? "#ef4444" : pct >= 85 ? "#22c55e" : pct >= 60 ? "#f97316" : "#3b82f6"
                      const dagLabel = new Date(d.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric" })
                      return (
                        <div key={d.datum}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", marginBottom: 2 }}>
                            <span style={{ color: "#64748b" }}>{dagLabel}{d.dagTrain > 0 ? ` 🏃+${d.dagTrain}` : ""}</span>
                            <span style={{ color: k, fontWeight: 700 }}>{rnd(d.kcal)} / {d.eDoel} kcal ({pct}%)</span>
                          </div>
                          <ProgressBalk waarde={d.kcal} doel={d.eDoel} hoogte={6} />
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Training samenvatting */}
              {trainingen.length > 0 && (
                <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 12 }}>TRAINING — LAATSTE {periode} DAGEN</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                    <MetricCard label="TOTAAL KCAL" waarde={`${trainKcal}`} sub="verbrand" kleur="#22c55e" />
                    <MetricCard label="TOTAAL DUUR" waarde={`${Math.floor(trainMin/60)}u${trainMin%60}min`} kleur="#3b82f6" />
                    <MetricCard label="# TRAININGEN" waarde={`${trainingen.length}`} sub={`gem ${rnd(trainMin / Math.max(trainingen.length, 1))} min`} kleur="#8b5cf6" />
                  </div>
                </div>
              )}

              {/* Gewicht invoer */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2 }}>GEWICHT BIJWERKEN</div>
                  <div style={{ fontSize: "0.68rem", color: "#475569", display: "flex", alignItems: "center", gap: 5 }}>
                    <span>⚖️</span>
                    <span>Weeg jezelf <b style={{ color: "#94a3b8" }}>1× per week</b>, steeds op hetzelfde moment</span>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <input type="number" value={gewicht} onChange={e => setGewicht(Number(e.target.value))} step={0.1} min={30} max={250}
                    style={{ width: 90, padding: "10px 12px", background: "#1e293b", border: "1px solid #f97316", borderRadius: 8, color: "#f97316", fontSize: "1.1rem", fontWeight: 800, textAlign: "center", outline: "none" }} />
                  <span style={{ color: "#64748b" }}>kg</span>
                  <button onClick={slaGewichtOp} style={{ padding: "10px 20px", background: gewichtOpgeslagen ? "#22c55e" : "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 700 }}>
                    {gewichtOpgeslagen ? "✓ Opgeslagen!" : "Opslaan"}
                  </button>
                  {profiel?.gewicht_kg && gewicht !== profiel.gewicht_kg && (
                    <span style={{ fontSize: "0.75rem", color: gewicht < profiel.gewicht_kg ? "#22c55e" : "#f97316", fontWeight: 700 }}>
                      {gewicht < profiel.gewicht_kg ? "▼" : "▲"} {Math.abs(r1(gewicht - profiel.gewicht_kg))} kg
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ── TAB 1: VOEDINGSKWALITEIT ── */}
          {actieveTab === 1 && metData.length > 0 && (
            <div>
              {/* Nutriëntdensiteit score */}
              {(() => {
                const ndScores = metData.map(d => {
                  let nd = 0
                  // Vezels: ADH 30g (2pt = bereikt, 1pt = half)
                  if (d.vezels >= 25) nd += 2; else if (d.vezels >= 15) nd += 1
                  // Kalium: ADH 3500mg
                  if (d.kalium >= 2800) nd += 1; else if (d.kalium >= 1500) nd += 0.5
                  // Calcium: ADH 1000mg
                  if (d.calcium >= 800) nd += 1; else if (d.calcium >= 400) nd += 0.5
                  // IJzer: ADH 15mg
                  if (d.ijzer >= 10) nd += 1; else if (d.ijzer >= 5) nd += 0.5
                  // Vit D: ADH 15µg (half punt max)
                  if (d.vitd >= 10) nd += 0.5; else if (d.vitd >= 5) nd += 0.25
                  // Vit B12: ADH 2.4µg
                  if (d.vitb12 >= 1.5) nd += 1; else if (d.vitb12 >= 0.8) nd += 0.5
                  // Omega-3: ADH 1.5g (half punt max)
                  if (d.omega3 >= 1.0) nd += 0.5; else if (d.omega3 >= 0.5) nd += 0.25
                  // Groenten & fruit: gewicht in gram (verhoogd doel)
                  const gfGram = (d.gfGram || 0)
                  if (gfGram >= 500) nd += 3; else if (gfGram >= 350) nd += 2; else if (gfGram >= 200) nd += 1; else if (gfGram >= 100) nd += 0.5
                  // Diversiteit: aantal voedingsgroepen
                  const aantalGroepen = Object.keys(d.catKcal).filter(c => d.catKcal[c] > 50).length
                  if (aantalGroepen >= 5) nd += 1; else if (aantalGroepen >= 3) nd += 0.5
                  return Math.min(10, nd)
                })
                const gemNd = r1(ndScores.reduce((a, v) => a + v, 0) / ndScores.length)
                const ndK = gemNd >= 7 ? "#22c55e" : gemNd >= 4 ? "#fbbf24" : "#ef4444"

                // Unieke categorieën aanwezig
                const alleCats = new Set(metData.flatMap(d => Object.keys(d.catKcal).filter(c => d.catKcal[c] > 50)))
                const hoofdGroepen = ["Groenten","Fruit","Granen & brood","Vlees & vis","Zuivel","Eieren","Peulvruchten","Noten & zaden"]
                const ontbrekend = hoofdGroepen.filter(g => !alleCats.has(g))

                return (
                  <>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, textAlign: "center" }}>
                        <div style={{ fontSize: "0.6rem", color: "#64748b", marginBottom: 6 }}>NUTRIËNTDENSITEIT GEM</div>
                        <div style={{ fontSize: "2rem", fontWeight: 800, color: ndK }}>{gemNd}/10</div>
                        <div style={{ fontSize: "0.68rem", color: "#475569" }}>{gemNd >= 7 ? "Uitstekend" : gemNd >= 4 ? "Redelijk" : "Verbetering nodig"}</div>
                      </div>
                      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                        <div style={{ fontSize: "0.6rem", color: "#64748b", marginBottom: 8 }}>VOEDINGSGROEPEN ({alleCats.size}/8)</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                          {hoofdGroepen.map(g => (
                            <div key={g} style={{ fontSize: "0.6rem", padding: "2px 6px", borderRadius: 4, background: alleCats.has(g) ? "rgba(34,197,94,0.15)" : "#1e293b", color: alleCats.has(g) ? "#22c55e" : "#475569", border: `1px solid ${alleCats.has(g) ? "#22c55e44" : "#2a2a2a"}` }}>
                              {g.split(" ")[0]}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {ontbrekend.length > 0 && (
                      <div style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.3)", borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontSize: "0.78rem", color: "#fbbf24" }}>
                        ⚠️ Ontbrekende groepen: {ontbrekend.join(" · ")}
                      </div>
                    )}

                    {/* ND per dag */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>NUTRIËNTDENSITEIT PER DAG (/10) — stippel = doel (7)</div>
                      <BalkChart labels={labels} waarden={dagStats.map((_, i) => ndScores[metData.indexOf(dagStats[i])] ?? 0)} doel={7} hoogte={100} />
                    </div>

                    {/* Plantaardig vs dierlijk */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>PLANTAARDIG VS DIERLIJK (% kcal per dag)</div>
                      {metData.map(d => {
                        const plantKcal = Object.entries(d.catKcal).filter(([c]) => PLANTAARDIG.has(c)).reduce((a, [, v]) => a + v, 0)
                        const dierKcal = Object.entries(d.catKcal).filter(([c]) => DIERLIJK.has(c)).reduce((a, [, v]) => a + v, 0)
                        const tot = plantKcal + dierKcal || 1
                        const plantPct = rnd(plantKcal / tot * 100)
                        const dagLabel = new Date(d.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric" })
                        return (
                          <div key={d.datum} style={{ marginBottom: 6 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.68rem", marginBottom: 2 }}>
                              <span style={{ color: "#64748b" }}>{dagLabel}</span>
                              <span style={{ color: "#94a3b8" }}>🌿 {plantPct}% plant · 🥩 {100 - plantPct}% dier</span>
                            </div>
                            <div style={{ height: 7, background: "#1e293b", borderRadius: 4, overflow: "hidden", display: "flex" }}>
                              <div style={{ width: `${plantPct}%`, background: "#22c55e", borderRadius: "4px 0 0 4px" }} />
                              <div style={{ flex: 1, background: "#3b82f6" }} />
                            </div>
                          </div>
                        )
                      })}
                      {(() => {
                        const gemPlant = rnd(metData.reduce((a, d) => {
                          const pl = Object.entries(d.catKcal).filter(([c]) => PLANTAARDIG.has(c)).reduce((s, [, v]) => s + v, 0)
                          const di = Object.entries(d.catKcal).filter(([c]) => DIERLIJK.has(c)).reduce((s, [, v]) => s + v, 0)
                          return a + pl / (pl + di || 1) * 100
                        }, 0) / n)
                        const k = gemPlant >= 50 ? "#22c55e" : gemPlant >= 30 ? "#fbbf24" : "#ef4444"
                        return (
                          <div style={{ marginTop: 10, padding: "8px 12px", background: "#1e293b", borderRadius: 8, fontSize: "0.78rem", color: k }}>
                            Gem {gemPlant}% plantaardig — {gemPlant >= 50 ? "✓ Goed" : "⚠️ Doel: min 50%"}
                          </div>
                        )
                      })()}
                    </div>

                    {/* Vezels */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 6 }}>VEZELS PER DAG — ADH = 30g</div>
                      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 12 }}>
                        <div style={{ fontSize: "2rem", fontWeight: 800, color: gem.vezels >= 25 ? "#22c55e" : gem.vezels >= 15 ? "#f97316" : "#ef4444" }}>{gem.vezels}g</div>
                        <div style={{ fontSize: "0.78rem", color: "#64748b" }}>
                          gemiddeld per dag<br />
                          {gem.vezels < 20 ? "💡 Meer groenten, volkoren en peulvruchten" : ""}
                        </div>
                      </div>
                      <BalkChart labels={labels} waarden={dagStats.map(d => d.vezels)} doel={30} hoogte={80} />
                    </div>

                    {/* Micronutriënten */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>MICRONUTRIËNTEN GEM vs ADH</div>
                      <div style={{ fontSize: "0.7rem", color: "#475569", marginBottom: 10 }}>
                        ℹ️ Gebaseerd op NEVO-databank producten. Producten zonder micronutriëntdata tellen als 0.
                      </div>
                      {[
                        { l: "🥬 Kalium", v: gem.kalium, doel: 3500, e: "mg", tip: "Banaan, aardappel, avocado, spinazie, zalm" },
                        { l: "🦴 Calcium", v: gem.calcium, doel: 1000, e: "mg", tip: "Melk, yoghurt, kaas, broccoli, sardines" },
                        { l: "🩸 IJzer", v: gem.ijzer, doel: 15, e: "mg", tip: "Rood vlees, linzen, spinazie, pompoenpitten" },
                        { l: "☀️ Vitamine D", v: gem.vitd, doel: 15, e: "µg", tip: "Zalm, makreel, eieren, verrijkte zuivel" },
                        { l: "🧬 Vitamine B12", v: gem.vitb12, doel: 2.4, e: "µg", tip: "Vlees, vis, eieren, melk" },
                        { l: "🐟 Omega-3", v: gem.omega3, doel: 1.5, e: "g", tip: "Zalm, makreel, haring, walnoten, lijnzaad" },
                      ].map(m => {
                        const pct = Math.min(150, rnd(m.v / Math.max(m.doel, 0.001) * 100))
                        const k = pct >= 80 ? "#22c55e" : pct >= 50 ? "#fbbf24" : "#ef4444"
                        return (
                          <div key={m.l} style={{ marginBottom: 12 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", marginBottom: 4 }}>
                              <span style={{ color: "#94a3b8" }}>{m.l}</span>
                              <span style={{ color: k, fontWeight: 700 }}>{m.v}{m.e} / {m.doel}{m.e} ({pct}%)</span>
                            </div>
                            <ProgressBalk waarde={m.v} doel={m.doel} kleur={k} hoogte={6} />
                            {pct < 80 && <div style={{ fontSize: "0.68rem", color: pct < 50 ? "#ef4444" : "#fbbf24", marginTop: 3 }}>💡 {m.tip}</div>}
                          </div>
                        )
                      })}
                    </div>

                    {/* Groenten & fruit */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginTop: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 12 }}>GROENTEN & FRUIT (gram per dag)</div>
                      {(() => {
                        const gfData = dagStats.map(d => {
                          let gr = 0, fr = 0
                          d.items.forEach((it: any) => {
                            const cat = herkenCategorie(it.naam || "", it.categorie || "")
                            if (cat === "Groenten") gr += it.hoeveelheid_g || 0
                            else if (cat === "Fruit") fr += it.hoeveelheid_g || 0
                          })
                          return { datum: d.datum, gr: rnd(gr), fr: rnd(fr) }
                        })
                        const metGf = gfData.filter((_, i) => dagStats[i].heeftData)
                        const gemGr = rnd(metGf.reduce((a, d) => a + d.gr, 0) / Math.max(metGf.length, 1))
                        const gemFr = rnd(metGf.reduce((a, d) => a + d.fr, 0) / Math.max(metGf.length, 1))
                        return (
                          <>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8, marginBottom: 12 }}>
                              {[
                                { l: "GEM GROENTEN", v: `${gemGr}g`, doel: "300g", k: gemGr >= 300 ? "#22c55e" : gemGr >= 200 ? "#f97316" : "#ef4444" },
                                { l: "GEM FRUIT", v: `${gemFr}g`, doel: "250g", k: gemFr >= 250 ? "#22c55e" : gemFr >= 150 ? "#f97316" : "#ef4444" },
                                { l: "TOTAAL", v: `${gemGr + gemFr}g`, doel: "550g", k: gemGr + gemFr >= 550 ? "#22c55e" : "#f97316" },
                                { l: "% VAN DOEL", v: `${rnd((gemGr + gemFr) / 5.5)}%`, doel: "100%", k: gemGr + gemFr >= 550 ? "#22c55e" : "#f97316" },
                              ].map(k => (
                                <div key={k.l} style={{ background: "#1e293b", borderRadius: 8, padding: "10px", textAlign: "center" }}>
                                  <div style={{ fontSize: "0.58rem", color: "#64748b" }}>{k.l}</div>
                                  <div style={{ fontSize: "0.95rem", fontWeight: 800, color: k.k }}>{k.v}</div>
                                  <div style={{ fontSize: "0.58rem", color: "#475569" }}>doel {k.doel}</div>
                                </div>
                              ))}
                            </div>
                            {metGf.slice(-14).map(d => (
                              <div key={d.datum} style={{ marginBottom: 5 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.68rem", marginBottom: 2 }}>
                                  <span style={{ color: "#64748b" }}>{new Date(d.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric" })}</span>
                                  <span style={{ color: "#94a3b8" }}>🥦 {d.gr}g · 🍎 {d.fr}g</span>
                                </div>
                                <div style={{ height: 6, background: "#1e293b", borderRadius: 3, display: "flex", gap: 2 }}>
                                  <div style={{ width: `${Math.min(100, d.gr / 5.5)}%`, background: "#22c55e", borderRadius: 3 }} />
                                  <div style={{ width: `${Math.min(100, d.fr / 5.5)}%`, background: "#a78bfa", borderRadius: 3 }} />
                                </div>
                              </div>
                            ))}
                            <div style={{ display: "flex", gap: 12, marginTop: 6, fontSize: "0.68rem" }}>
                              <span><span style={{ color: "#22c55e" }}>■</span> Groenten (doel 300g)</span>
                              <span><span style={{ color: "#a78bfa" }}>■</span> Fruit (doel 250g)</span>
                            </div>
                          </>
                        )
                      })()}
                    </div>
                  </>
                )
              })()}
            </div>
          )}

          {/* ── TAB 2: KOOLHYDRATEN ── */}
          {actieveTab === 2 && metData.length > 0 && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
                {[
                  { l: "GEM KH/DAG", v: `${gem.kh}g`, k: Math.abs(gem.kh - khDoeIncl) < khDoeIncl * 0.15 ? "#22c55e" : "#f97316" },
                  { l: "KH DOEL", v: `${khDoeIncl}g`, k: "#64748b" },
                  { l: "TOEGEVOEGde SUIKERS/DAG", v: `${gem.suikers}g`, k: gem.suikers / Math.max(gem.kh, 1) <= 0.1 ? "#22c55e" : "#f97316" },
                  { l: "TOEGEVOEGD % KH", v: `${rnd(gem.suikers / Math.max(gem.kh, 1) * 100)}%`, k: gem.suikers / Math.max(gem.kh, 1) <= 0.1 ? "#22c55e" : "#ef4444" },
                ].map(m => <MetricCard key={m.l} label={m.l} waarde={m.v} kleur={m.k} />)}
              </div>

              {/* KH per dag */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>KH PER DAG vs DOEL ({khDoeIncl}g)</div>
                <BalkChart labels={labels} waarden={dagStats.map(d => d.kh)} doel={khDoeIncl} hoogte={120} />
              </div>

              {/* KH + Suikers gecombineerd */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>TOEGEVOEGDE SUIKERS vs KH (excl. natuurlijke suikers)</div>
                {dagStats.filter(d => d.heeftData).slice(-14).map(d => {
                  const suPct = rnd(d.suikers / Math.max(d.kh, 1) * 100)
                  const k = suPct <= 10 ? "#22c55e" : suPct <= 20 ? "#fbbf24" : "#ef4444"
                  const dagLabel = new Date(d.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric" })
                  return (
                    <div key={d.datum} style={{ marginBottom: 6 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", marginBottom: 2 }}>
                        <span style={{ color: "#64748b" }}>{dagLabel}</span>
                        <span style={{ color: k }}>{rnd(d.kh)}g KH · {r1(d.suikers)}g suikers ({suPct}%)</span>
                      </div>
                      <div style={{ height: 7, background: "#1e293b", borderRadius: 4, display: "flex" }}>
                        <div style={{ width: `${Math.min(100, rnd(d.kh / Math.max(khDoeIncl, 1) * 100))}%`, background: "#22c55e", borderRadius: 4 }} />
                      </div>
                      {suPct > 10 && (
                        <div style={{ height: 4, marginTop: 1 }}>
                          <div style={{ width: `${Math.min(100, suPct)}%`, height: "100%", background: "#ef4444", borderRadius: 2 }} />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* GI overzicht */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>GLYCEMISCHE INDEX OVERZICHT</div>
                {(() => {
                  const giProducten: Record<string, { gi: number, kcal: number, gram: number }> = {}
                  metData.forEach(d => {
                    d.items.forEach((it: any) => {
                      const gi = it.gi || GI_DB[it.naam] || 0
                      if (gi > 0) {
                        const n = it.naam || "Onbekend"
                        if (!giProducten[n]) giProducten[n] = { gi, kcal: 0, gram: 0 }
                        giProducten[n].kcal += it.kcal || 0
                        giProducten[n].gram += it.hoeveelheid_g || 0
                      }
                    })
                  })
                  const totKcalGi = Object.values(giProducten).reduce((a, v) => a + v.kcal, 0)
                  const gewogenGi = totKcalGi > 0 ? rnd(Object.values(giProducten).reduce((a, v) => a + v.gi * v.kcal, 0) / totKcalGi) : 0
                  const giK = gewogenGi < 55 ? "#22c55e" : gewogenGi <= 70 ? "#fbbf24" : "#ef4444"
                  const laag = Object.entries(giProducten).filter(([, v]) => v.gi < 55)
                  const matig = Object.entries(giProducten).filter(([, v]) => v.gi >= 55 && v.gi <= 70)
                  const hoog = Object.entries(giProducten).filter(([, v]) => v.gi > 70)
                  return (
                    <>
                      {gewogenGi > 0 && (
                        <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "10px 14px", background: "#1e293b", borderRadius: 8, marginBottom: 14 }}>
                          <div>
                            <div style={{ fontSize: "0.6rem", color: "#64748b" }}>GEWOGEN GI</div>
                            <div style={{ fontSize: "1.8rem", fontWeight: 800, color: giK }}>{gewogenGi}</div>
                            <div style={{ fontSize: "0.7rem", color: giK }}>{gewogenGi < 55 ? "Laag GI" : gewogenGi <= 70 ? "Matig GI" : "Hoog GI"}</div>
                          </div>
                          <div style={{ fontSize: "0.78rem", color: "#94a3b8", lineHeight: 1.6 }}>
                            {gewogenGi < 55 ? "✓ Overwegend trage koolhydraten." : gewogenGi <= 70 ? "⚠️ Matige GI — meer volkoren en groenten." : "⚠️ Hoge GI — minder witte rijst en suiker."}
                          </div>
                        </div>
                      )}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                        {[
                          { titel: "🟢 Laag (<55)", items: laag, k: "#22c55e" },
                          { titel: "🟡 Matig (55-70)", items: matig, k: "#fbbf24" },
                          { titel: "🔴 Hoog (>70)", items: hoog, k: "#ef4444" },
                        ].map(col => (
                          <div key={col.titel}>
                            <div style={{ fontSize: "0.68rem", fontWeight: 700, color: col.k, marginBottom: 8 }}>{col.titel} ({col.items.length})</div>
                            {col.items.sort((a, b) => b[1].kcal - a[1].kcal).slice(0, 5).map(([naam, data]) => (
                              <div key={naam} style={{ background: "#1e293b", borderRadius: 6, padding: "6px 8px", marginBottom: 4 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem" }}>
                                  <span style={{ color: "#f1f5f9", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "70%" }}>{naam}</span>
                                  <span style={{ color: col.k, fontWeight: 700 }}>GI {data.gi}</span>
                                </div>
                                <div style={{ fontSize: "0.62rem", color: "#475569" }}>{rnd(data.gram / n)}g/dag gem</div>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    </>
                  )
                })()}
              </div>
            </div>
          )}

          {/* ── TAB 3: EIWIT ── */}
          {actieveTab === 3 && metData.length > 0 && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
                {[
                  { l: "GEM EIWIT/DAG", v: `${gem.eiwit}g`, k: Math.abs(gem.eiwit - eiDoeIncl) < eiDoeIncl * 0.15 ? "#22c55e" : "#f97316" },
                  { l: "DOEL", v: `${eiDoeIncl}g`, k: "#64748b" },
                  { l: "% VAN DOEL", v: `${rnd(gem.eiwit / Math.max(eiDoeIncl, 1) * 100)}%`, k: gem.eiwit >= eiDoeIncl * 0.85 ? "#22c55e" : "#f97316" },
                  { l: "G/KG LICHAAM", v: `${r1(gem.eiwit / Math.max(gewichtKg, 1))}g/kg`, k: gem.eiwit / gewichtKg >= 1.4 ? "#22c55e" : "#f97316" },
                ].map(m => <MetricCard key={m.l} label={m.l} waarde={m.v} kleur={m.k} />)}
              </div>

              {/* Eiwit per dag */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>EIWITINNAME PER DAG vs DOEL ({eiDoeIncl}g)</div>
                <BalkChart labels={labels} waarden={dagStats.map(d => d.eiwit)} doel={eiDoeIncl} hoogte={120} />
              </div>

              {/* Eiwit per maaltijdmoment */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>EIWIT PER MAALTIJDMOMENT (gemiddeld)</div>
                {(() => {
                  const eiPerMom = [0, 0, 0, 0, 0, 0]
                  const nPerMom = [0, 0, 0, 0, 0, 0]
                  metData.forEach(d => {
                    d.items.forEach((it: any) => {
                      const mi = Math.min(5, it.moment || 0)
                      eiPerMom[mi] += it.eiwit_g || 0
                      nPerMom[mi]++
                    })
                  })
                  const momNamen = ["Ontbijt", "Voormiddag", "Lunch", "Namiddag", "Avondmaal", "Na training"]
                  const eiDoelMom = eiDoeIncl / 3
                  return momNamen.map((naam, i) => {
                    if (nPerMom[i] === 0) return null
                    const gem = r1(eiPerMom[i] / n)
                    const k = gem >= 20 ? "#22c55e" : gem >= 10 ? "#f97316" : "#ef4444"
                    return (
                      <div key={naam} style={{ marginBottom: 10 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", marginBottom: 4 }}>
                          <span style={{ color: "#94a3b8" }}>{naam}</span>
                          <span style={{ color: k, fontWeight: 700 }}>{gem}g {gem >= 20 ? "✓" : gem >= 10 ? "" : "⚠️"}</span>
                        </div>
                        <ProgressBalk waarde={gem} doel={40} kleur={k} hoogte={6} />
                      </div>
                    )
                  })
                })()}
                <div style={{ fontSize: "0.7rem", color: "#475569", marginTop: 8 }}>Aanbeveling: min. 20g eiwit per hoofdmaaltijd voor optimale spiereiwitsynthese</div>
              </div>

              {/* Eiwitbronnen */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>HERKOMST EIWIT</div>
                {(() => {
                  const catEi: Record<string, number> = {}
                  metData.forEach(d => {
                    d.items.forEach((it: any) => {
                      const cat = herkenCategorie(it.naam || "", it.categorie || "")
                      catEi[cat] = (catEi[cat] || 0) + (it.eiwit_g || 0)
                    })
                  })
                  const totEi = Object.values(catEi).reduce((a, v) => a + v, 0)
                  const plantEi = Object.entries(catEi).filter(([c]) => PLANTAARDIG.has(c)).reduce((a, [, v]) => a + v, 0)
                  const dierEi = Object.entries(catEi).filter(([c]) => DIERLIJK.has(c)).reduce((a, [, v]) => a + v, 0)
                  const pctPl = rnd(plantEi / Math.max(totEi, 1) * 100)
                  const CAT_KL: Record<string, string> = { "Vlees & vis": "#ef4444", "Zuivel": "#3b82f6", "Eieren": "#fbbf24", "Granen & brood": "#f97316", "Groenten": "#22c55e", "Peulvruchten": "#4ade80", "Noten & zaden": "#f59e0b", "Sportvoeding": "#14b8a6" }
                  const top = Object.entries(catEi).sort((a, b) => b[1] - a[1]).slice(0, 6)
                  const maxEi = top[0]?.[1] || 1
                  return (
                    <>
                      <div style={{ display: "flex", gap: 12, marginBottom: 14 }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ height: 12, background: "#1e293b", borderRadius: 6, overflow: "hidden", display: "flex" }}>
                            <div style={{ width: `${pctPl}%`, background: "#22c55e" }} />
                            <div style={{ flex: 1, background: "#3b82f6" }} />
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", marginTop: 4 }}>
                            <span style={{ color: "#22c55e" }}>🌿 Plantaardig {pctPl}%</span>
                            <span style={{ color: "#3b82f6" }}>🥩 Dierlijk {100 - pctPl}%</span>
                          </div>
                        </div>
                      </div>
                      {top.map(([cat, ei]) => {
                        const gemDag = r1(ei / n)
                        const pct = rnd(ei / maxEi * 100)
                        const k = CAT_KL[cat] || "#64748b"
                        return (
                          <div key={cat} style={{ marginBottom: 8 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: 3 }}>
                              <span style={{ color: "#f1f5f9" }}>{cat}</span>
                              <span style={{ color: k, fontWeight: 700 }}>{gemDag}g/dag</span>
                            </div>
                            <ProgressBalk waarde={pct} doel={100} kleur={k} hoogte={5} />
                          </div>
                        )
                      })}
                      <div style={{ marginTop: 10, fontSize: "0.72rem", color: gem.eiwit / gewichtKg >= 1.4 ? "#22c55e" : "#fbbf24" }}>
                        {r1(gem.eiwit / gewichtKg)}g/kg/dag — {gem.eiwit / gewichtKg >= 1.4 ? "✓ voldoende" : "⚠️ doel 1.4-1.7g/kg/dag"}
                      </div>
                    </>
                  )
                })()}
              </div>
            </div>
          )}

          {/* ── TAB 4: VETTEN ── */}
          {actieveTab === 4 && metData.length > 0 && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10, marginBottom: 16 }}>
                {[
                  { l: "GEM VET/DAG", v: `${gem.vet}g`, k: Math.abs(gem.vet - vtDoeIncl) < vtDoeIncl * 0.15 ? "#22c55e" : "#f97316" },
                  { l: "DOEL", v: `${vtDoeIncl}g`, k: "#64748b" },
                  { l: "% VAN KCAL", v: `${rnd(gem.vet * 9 / Math.max(gem.kcal, 1) * 100)}%`, k: "#8b5cf6" },
                ].map(m => <MetricCard key={m.l} label={m.l} waarde={m.v} kleur={m.k} />)}
              </div>

              {/* Vet per dag */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>VETINNAME PER DAG vs DOEL ({vtDoeIncl}g)</div>
                <BalkChart labels={labels} waarden={dagStats.map(d => d.vet)} doel={vtDoeIncl} hoogte={120} />
              </div>

              {/* Verzadigd vs onverzadigd */}
              <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>VERZADIGD vs ONVERZADIGD VET</div>
                {(() => {
                  const gemVerz = r1(metData.reduce((a, d) => a + d.verz, 0) / n)
                  const gemOnverz = r1(gem.vet - gemVerz)
                  const verzPctKcal = rnd(gemVerz * 9 / Math.max(gem.kcal, 1) * 100)
                  const whoDoel = rnd(energieDoelingcl * 0.10 / 9)
                  const k = verzPctKcal <= 10 ? "#22c55e" : "#ef4444"

                  return (
                    <>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
                        <div style={{ background: "#1e293b", borderRadius: 10, padding: 14, textAlign: "center" }}>
                          <div style={{ fontSize: "0.6rem", color: "#64748b" }}>GEM VERZADIGD</div>
                          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: k }}>{gemVerz}g</div>
                          <div style={{ fontSize: "0.68rem", color: k }}>{verzPctKcal}% van kcal</div>
                        </div>
                        <div style={{ background: "#1e293b", borderRadius: 10, padding: 14, textAlign: "center" }}>
                          <div style={{ fontSize: "0.6rem", color: "#64748b" }}>GEM ONVERZADIGD</div>
                          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#22c55e" }}>{gemOnverz}g</div>
                          <div style={{ fontSize: "0.68rem", color: "#475569" }}>WHO max: {whoDoel}g/dag</div>
                        </div>
                      </div>

                      <div style={{ padding: "10px 14px", background: `rgba(${verzPctKcal <= 10 ? "34,197,94" : "239,68,68"},0.08)`, border: `1px solid rgba(${verzPctKcal <= 10 ? "34,197,94" : "239,68,68"},0.3)`, borderRadius: 8, fontSize: "0.78rem", color: k, marginBottom: 14 }}>
                        {verzPctKcal <= 10 ? `✓ Verzadigde vetten (${verzPctKcal}%) binnen WHO-aanbeveling (max 10%).` : `⚠️ Verzadigde vetten (${verzPctKcal}%) overschrijden de WHO-aanbeveling. Vervang boter/vet vlees door olijfolie en noten.`}
                      </div>

                      {/* Verz per dag */}
                      {dagStats.filter(d => d.heeftData && d.verz > 0).slice(-14).map(d => {
                        const vPct = rnd(d.verz * 9 / Math.max(d.kcal, 1) * 100)
                        const k2 = vPct <= 10 ? "#22c55e" : "#ef4444"
                        const dagLabel = new Date(d.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric" })
                        return (
                          <div key={d.datum} style={{ marginBottom: 6 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", marginBottom: 2 }}>
                              <span style={{ color: "#64748b" }}>{dagLabel}</span>
                              <span style={{ color: k2 }}>{r1(d.verz)}g verz ({vPct}% kcal)</span>
                            </div>
                            <div style={{ height: 6, background: "#1e293b", borderRadius: 3, display: "flex" }}>
                              <div style={{ width: `${Math.min(100, rnd(d.verz / Math.max(whoDoel, 1) * 100))}%`, background: k2, borderRadius: 3 }} />
                            </div>
                          </div>
                        )
                      })}
                    </>
                  )
                })()}
              </div>
            </div>
          )}

          {/* ── TAB 5: PERFORMANCE ── */}
          {actieveTab === 5 && metData.length > 0 && (
            <div>
              {(() => {
                const scores = metData.map(d => d.score)
                const beste = metData.reduce((b, d) => d.score > b.score ? d : b, metData[0])
                const nGoed = scores.filter(s => s >= 75).length
                return (
                  <>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
                      <MetricCard label="GEM SCORE" waarde={`${gem.score}/100`}
                        sub={gem.score >= 75 ? "🏆 Uitstekend" : gem.score >= 60 ? "👍 Goed" : gem.score >= 45 ? "📈 In ontwikkeling" : "💪 Potentieel"}
                        kleur={gem.score >= 75 ? "#22c55e" : gem.score >= 60 ? "#f97316" : "#ef4444"} />
                      <MetricCard label="BESTE DAG" waarde={`${beste.score}/100`} sub={beste.datum.slice(5).replace("-", "/")} kleur="#22c55e" />
                      <MetricCard label="GOEDE DAGEN" waarde={`${nGoed}/${metData.length}`} sub="score ≥75" kleur="#22c55e" />
                      <MetricCard label="BIJGEHOUDEN" waarde={`${metData.length}/${periode}`} sub="dagen" kleur="#3b82f6" />
                    </div>

                    {/* Score per dag */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>PERFORMANCE SCORE PER DAG — stippel = doel (75)</div>
                      {metData.slice(-14).map(d => {
                        const k = d.score >= 75 ? "#22c55e" : d.score >= 55 ? "#f97316" : "#ef4444"
                        const dagLabel = new Date(d.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric" })
                        return (
                          <div key={d.datum} style={{ marginBottom: 10 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: 4 }}>
                              <span style={{ color: "#64748b" }}>{dagLabel}</span>
                              <span style={{ color: k, fontWeight: 800 }}>{d.score}/100</span>
                            </div>
                            <ProgressBalk waarde={d.score} doel={100} kleur={k} hoogte={10} />
                          </div>
                        )
                      })}
                    </div>

                    {/* Score opbouw uitleg */}
                    <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16 }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 14 }}>HOE WERKT DE PERFORMANCE SCORE?</div>
                      {[
                        { l: "⚡ Energiebalans", uitleg: "Kcal inname vs energiedoel (incl. training)" },
                        { l: "🥗 Koolhydraten", uitleg: "KH inname vs KH doel" },
                        { l: "💪 Eiwit", uitleg: "Eiwitinname vs eiwitdoel" },
                        { l: "🌿 Vezels", uitleg: "Min. 30g/dag voor optimale spijsvertering en herstel" },
                        { l: "📅 Maaltijdspreiding", uitleg: "Aantal ingevulde maaltijdmomenten" },
                        { l: "💧 Vochtbalans", uitleg: "Min. 2L water per dag" },
                      ].map(item => (
                        <div key={item.l} style={{ display: "flex", alignItems: "center", padding: "8px 0", borderBottom: "1px solid #1e293b" }}>
                          <div>
                            <div style={{ fontSize: "0.82rem", color: "#f5f3ef" }}>{item.l}</div>
                            <div style={{ fontSize: "0.68rem", color: "#475569" }}>{item.uitleg}</div>
                          </div>
                        </div>
                      ))}

                      {/* Breakdown laatste dag */}
                      {metData.length > 0 && (() => {
                        const last = metData[metData.length - 1]
                        const scores6 = (() => {
                          const kcal = last.kcal
                          const eDoel = last.eDoel
                          let e = 0, kh = 0, ei = 0, vz = 0, sp = 0, vt = 0
                          if (kcal > 0 && eDoel > 0) {
                            const pctE = kcal / eDoel
                            e = Math.max(2, Math.min(25, rnd(25 * Math.exp(-Math.pow(pctE - 1, 2) / (2 * 0.18 * 0.18)))))
                          }
                          // KH en eiwit score op basis van gram vs doel (niet % van kcal)
                          if (khDoeIncl > 0) {
                            const khPctVanDoel = last.kh / khDoeIncl
                            kh = khPctVanDoel >= 0.95 ? 20 : khPctVanDoel >= 0.80 ? 14 : khPctVanDoel >= 0.60 ? 8 : khPctVanDoel >= 0.40 ? 4 : 2
                          }
                          if (eiDoeIncl > 0) {
                            const eiPctVanDoel = last.eiwit / eiDoeIncl
                            ei = eiPctVanDoel >= 0.95 ? 20 : eiPctVanDoel >= 0.80 ? 14 : eiPctVanDoel >= 0.60 ? 8 : eiPctVanDoel >= 0.40 ? 4 : 2
                          }
                          // Vochtbalans: schat ml vocht uit dagboek items
                          const VOCHT_PER_100G: Record<string, number> = {
                            "water": 100, "melk": 100, "yoghurt": 85, "kefir": 100,
                            "koffie": 100, "thee": 100, "sap": 100, "smoothie": 90,
                            "sportdrank": 100, "sojamelk": 100, "kokoswater": 100,
                            "cola": 100, "fanta": 100, "sprite": 100, "bier": 100,
                            "ijsthee": 100, "bouillon": 100, "soep": 85,
                          }
                          const VOCHT_CATS = ["dranken", "zuivel"]
                          const totaalVocht = last.items.reduce((acc: number, item: any) => {
                            const naam = (item.naam || "").toLowerCase()
                            const cat = (item.categorie || "").toLowerCase()
                            const g = item.hoeveelheid_g || 0
                            // Check op naam
                            const match = Object.keys(VOCHT_PER_100G).find(k => naam.includes(k))
                            if (match) return acc + g * VOCHT_PER_100G[match] / 100
                            // Check op categorie
                            if (VOCHT_CATS.some(c => cat.includes(c))) return acc + g * 0.9
                            return acc
                          }, 0)
                          const vochtMl = Math.round(totaalVocht)
                          vt = vochtMl >= 2000 ? 10 : vochtMl >= 1500 ? 7 : vochtMl >= 1000 ? 4 : vochtMl >= 500 ? 2 : 0
                          vz = last.vezels >= 30 ? 15 : last.vezels >= 20 ? 10 : last.vezels >= 10 ? 5 : 0
                          sp = Math.min(10, new Set(last.items.map((i: any) => i.moment)).size * 2)
                          return [
                            { l: "Energiebalans", pts: e, max: 25, detail: `${rnd(kcal)} / ${eDoel} kcal` },
                            { l: "Koolhydraten", pts: kh, max: 20, detail: `${r1(last.kh)}g vs doel ${khDoeIncl}g` },
                            { l: "Eiwit", pts: ei, max: 20, detail: `${r1(last.eiwit)}g vs doel ${eiDoeIncl}g` },
                            { l: "Vezels", pts: vz, max: 15, detail: `${r1(last.vezels)}g (doel 30g)` },
                            { l: "Maaltijdspreiding", pts: sp, max: 10, detail: `${new Set(last.items.map((i: any) => i.moment)).size} momenten ingevuld` },
                            { l: "💧 Vochtbalans", pts: vt, max: 10, detail: `${vochtMl}ml / doel 2000ml` },
                          ]
                        })()
                        return (
                          <div style={{ marginTop: 16 }}>
                            <div style={{ fontSize: "0.65rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>BREAKDOWN LAATSTE DAG ({last.datum.slice(5).replace("-", "/")})</div>
                            {scores6.map(s => {
                              const pct = rnd(s.pts / s.max * 100)
                              // Groen enkel als volledige score behaald, oranje bij gedeeltelijk
                              const k = s.pts >= s.max ? "#22c55e" : s.pts >= s.max * 0.5 ? "#f97316" : "#ef4444"
                              return (
                                <div key={s.l} style={{ background: "#1e293b", borderRadius: 8, padding: "10px 12px", marginBottom: 6 }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                    <span style={{ fontSize: "0.82rem", color: "#f5f3ef" }}>{s.l}</span>
                                    <span style={{ fontSize: "0.82rem", color: k, fontWeight: 700 }}>{s.detail}</span>
                                  </div>
                                  <div style={{ background: "#0f172a", borderRadius: 3, height: 5, marginTop: 4 }}>
                                    <div style={{ width: `${pct}%`, height: "100%", background: k, borderRadius: 3 }} />
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )
                      })()}
                    </div>
                  </>
                )
              })()}
            </div>
          )}
        </>
      )}
    </div>
  )
}
