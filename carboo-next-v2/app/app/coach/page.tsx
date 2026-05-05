"use client"
import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@/lib/auth-context"

const API = "https://carboo-api.onrender.com"

// ─── CONSTANTEN ──────────────────────────────────────────────────────────────
const SPORT_ICONS: Record<string, string> = {
  "Fietsen": "🚴", "Lopen": "🏃", "Duatlon": "🏃🚴",
  "Crossduatlon": "🚵🏃", "Triatlon": "🏊🚴🏃", "Crosstriatlon": "🚵🏊",
}

const KH_TARGETS: Record<string, Record<string, [number, number]>> = {
  "Fietsen":      { "0-75": [0,0], "75-120": [30,60], "120-180": [60,90], "180+": [85,110] },
  "Lopen":        { "0-60": [0,0], "60-90": [30,60], "90-180": [60,90], "180+": [75,90] },
  "Duatlon":      { "0-60": [0,0], "60-120": [30,60], "120+": [60,90] },
  "Triatlon":     { "0-90": [0,0], "90-180": [60,90], "180+": [80,110] },
  "Crosstriatlon":{ "0-90": [0,0], "90-180": [60,90], "180+": [75,100] },
  "Crossduatlon": { "0-90": [0,0], "90-180": [60,90], "180+": [75,100] },
}

function getKhRange(sport: string, minuten: number): [number, number] {
  const ranges = KH_TARGETS[sport] || KH_TARGETS["Fietsen"]
  for (const [range, vals] of Object.entries(ranges)) {
    const [lo, hi] = range.includes("+")
      ? [parseInt(range), 99999]
      : range.split("-").map(Number)
    if (minuten >= lo && minuten < hi) return vals
  }
  return [60, 90]
}

const RACE_ADVIEZEN: Record<string, Record<string, string[]>> = {
  "Fietsen": {
    "0-75": ["Water of mondspoeling met sportdrank volstaat", "Geen extra koolhydraten nodig", "Druk door naar rapport opmaken!"],
    "75-120": ["Kies voor een mix van vloeibare en vaste koolhydraatbronnen", "Sportdrank + rijstwafel of reep: combineer gel met vast voedsel", "Kies producten die je al gebruikt hebt tijdens training"],
    "120-181": ["Kies voor een mix van gels, vaste voeding en sportdrank", "Wissel regelmatig af tussen vloeibaar en vast", "Kies producten die je al gebruikt hebt tijdens training"],
    "181+": ["Kies voor een mix van gels, vaste voeding en sportdrank", "Kies producten die je al gebruikt hebt tijdens training", "Geen nieuwe producten op racedag - alleen vertrouwde keuzes"],
  },
  "Lopen": {
    "0-60": ["Water of mondspoeling met sportdrank volstaat", "Geen extra koolhydraten nodig", "Druk door naar rapport opmaken!"],
    "60-120": ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel", "Kies producten die je al gebruikt hebt tijdens training"],
    "120-181": ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel", "Kies producten die je al gebruikt hebt tijdens training"],
    "181+": ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel", "Kies producten die je al gebruikt hebt tijdens training"],
  },
  "Triatlon": {
    "0-60": ["Zwemmen: niet mogelijk om in te nemen — start optimaal gevoed", "Fiets: vloeibare koolhydraatbronnen (sportdrank)", "Loop: water of sportdrank volstaat bij sprint", "Kies producten die je al gebruikt hebt tijdens training"],
    "60-120": ["Fiets is het hoofdtankmoment — start onmiddellijk na T1", "Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank + gel", "Loop: gel of sportdrank, kies voor vloeibare bronnen", "Kies producten die je al gebruikt hebt tijdens training"],
    "120-240": ["Fiets: kies voor een mix van gels, vaste voeding en sportdrank", "Loop: bij voorkeur vloeibaar (gel + water), GI-gevoeliger na fietsen", "Kies producten die je al gebruikt hebt tijdens training"],
    "240+": ["Fiets: mix van gels, repen, sportdrank en vast voedsel", "Loop: vloeibaar + cola in het laatste deel", "Kies producten die je al gebruikt hebt tijdens training"],
  },
  "Duatlon": {
    "0-75": ["Water of mondspoeling met sportdrank volstaat", "Geen extra koolhydraten nodig", "Druk door naar rapport opmaken!"],
    "75-150": ["Fiets = hoofdtankmoment: kies bij voorkeur vloeibare koolhydraatbronnen", "Gel aan start 2e loop is essentieel", "Kies producten die je al gebruikt hebt tijdens training"],
    "150-210": ["Kies voor een mix van gels, vaste voeding en sportdrank op de fiets", "2e loop: gel + water, kies voor vloeibare bronnen", "Kies producten die je al gebruikt hebt tijdens training"],
    "210+": ["Kies voor een mix van gels, vaste voeding en sportdrank", "Meer GI-stress dan triatlon — plan innametiming op rustige segmenten", "Kies producten die je al gebruikt hebt tijdens training"],
  },
  "Crossduatlon": {
    "0-90": ["Water of mondspoeling met sportdrank volstaat", "Geen extra koolhydraten nodig", "Druk door naar rapport opmaken!"],
    "90-150": ["MTB: kies bij voorkeur vloeibare koolhydraatbronnen — trillingen verhogen GI-stress", "Neem in op vlakke/rechte stukken, nooit op technisch terrein", "Kies producten die je al gebruikt hebt tijdens training"],
    "150+": ["Kies voor een mix van gels en sportdrank", "MTB: enkel vloeibaar, geen vast voedsel op technisch terrein", "Kies producten die je al gebruikt hebt tijdens training"],
  },
}

function getRaceAdviezen(sport: string, minuten: number): string[] {
  const adv = RACE_ADVIEZEN[sport] || RACE_ADVIEZEN["Fietsen"]
  for (const [range, tips] of Object.entries(adv)) {
    const [lo, hi] = range.includes("+") ? [parseInt(range), 99999] : range.split("-").map(Number)
    if (minuten >= lo && minuten < hi) return tips
  }
  return Object.values(adv)[Object.values(adv).length - 1]
}

const STAP_LABELS = ["👋 Welkom", "🏃 Profiel", "🏁 Wedstrijd", "🍝 Carboloading", "🥗 Racedag", "📋 Raceplan", "✅ Klaar"]
const SPORTEN = Object.keys(SPORT_ICONS)
const NIVEAUS = ["Recreatief", "Competitief", "Elite / Semi-pro"]
const ERVARING_LIJST = ["Eerste wedstrijd", "1-3 wedstrijden", "4-10 wedstrijden", "10+ wedstrijden"]

// Carboloading voedingslijsten
const CL_MAALTIJDEN = {
  "Ontbijt": [
    { naam: "Wit brood", portie: "1 snede (35g)", kh: 17 },
    { naam: "Volkorenbrood", portie: "1 snede (35g)", kh: 14 },
    { naam: "Havermout", portie: "1 kom (45g droog)", kh: 27 },
    { naam: "Ontbijtgranen", portie: "1 kom (30g)", kh: 25 },
    { naam: "Muesli", portie: "1 kom (40g)", kh: 30 },
    { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
    { naam: "Melk", portie: "1 glas (200ml)", kh: 9 },
    { naam: "Yoghurt natuur", portie: "1 potje (125g)", kh: 6 },
    { naam: "Honing", portie: "1 koffielepel", kh: 4 },
    { naam: "Vruchtensap", portie: "1 glas (200ml)", kh: 20 },
  ],
  "Tussendoor VM": [
    { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
    { naam: "Appel", portie: "1 stuk (125g)", kh: 15 },
    { naam: "Rozijnen", portie: "1 handje (20g)", kh: 15 },
    { naam: "Muesli/granenreep", portie: "1 reep (40g)", kh: 26 },
    { naam: "Havermout", portie: "1 kom (45g droog)", kh: 27 },
    { naam: "Appelmoes", portie: "1 schaaltje (150g)", kh: 27 },
    { naam: "Speculoos", portie: "1 stuk (7g)", kh: 5 },
  ],
  "Lunch": [
    { naam: "Pasta (hoofdmaaltijd)", portie: "120g rauw / 300g gaar", kh: 75 },
    { naam: "Pasta (bijgerecht)", portie: "60g rauw / 150g gaar", kh: 37 },
    { naam: "Rijst (hoofdmaaltijd)", portie: "115g rauw / 290g gaar", kh: 81 },
    { naam: "Rijst (bijgerecht)", portie: "60g rauw / 150g gaar", kh: 42 },
    { naam: "Aardappelen gekookt", portie: "1 bord (175g)", kh: 30 },
    { naam: "Wit brood", portie: "1 snede (35g)", kh: 17 },
    { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
    { naam: "Sportdrank", portie: "1 bidon (500ml)", kh: 35 },
    { naam: "Honing", portie: "1 koffielepel", kh: 4 },
  ],
  "Tussendoor NM": [
    { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
    { naam: "Appel", portie: "1 stuk (125g)", kh: 15 },
    { naam: "Rozijnen", portie: "1 handje (20g)", kh: 15 },
    { naam: "Muesli/granenreep", portie: "1 reep (40g)", kh: 26 },
    { naam: "Appelmoes", portie: "1 schaaltje (150g)", kh: 27 },
    { naam: "Speculoos", portie: "1 stuk (7g)", kh: 5 },
  ],
  "Avondmaal": [
    { naam: "Pasta (hoofdmaaltijd)", portie: "120g rauw / 300g gaar", kh: 75 },
    { naam: "Pasta (bijgerecht)", portie: "60g rauw / 150g gaar", kh: 37 },
    { naam: "Rijst (hoofdmaaltijd)", portie: "115g rauw / 290g gaar", kh: 81 },
    { naam: "Rijst (bijgerecht)", portie: "60g rauw / 150g gaar", kh: 42 },
    { naam: "Aardappelen gekookt", portie: "1 bord (175g)", kh: 30 },
    { naam: "Groentenmix", portie: "1 bord (150g)", kh: 6 },
    { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
    { naam: "Sportdrank", portie: "1 bidon (500ml)", kh: 35 },
    { naam: "Honing", portie: "1 koffielepel", kh: 4 },
  ],
  "Avond snack": [
    { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
    { naam: "Appel", portie: "1 stuk (125g)", kh: 15 },
    { naam: "Rozijnen", portie: "1 handje (20g)", kh: 15 },
    { naam: "Appelmoes", portie: "1 schaaltje (150g)", kh: 27 },
    { naam: "Honing", portie: "1 koffielepel", kh: 4 },
    { naam: "Havermout", portie: "1 kom (45g droog)", kh: 27 },
  ],
}

const CL_MAALTIJD_PCT: Record<string, number> = {
  "Ontbijt": 0.25, "Tussendoor VM": 0.083, "Lunch": 0.25,
  "Tussendoor NM": 0.083, "Avondmaal": 0.25, "Avond snack": 0.083,
}

const RACEDAG_VOEDING = [
  { naam: "Wit brood", portie: "1 snede (35g)", kh: 17 },
  { naam: "Havermout", portie: "1 kom (45g droog)", kh: 27 },
  { naam: "Ontbijtgranen", portie: "1 kom (30g)", kh: 25 },
  { naam: "Banaan", portie: "1 stuk (130g)", kh: 30 },
  { naam: "Melk", portie: "1 glas (200ml)", kh: 9 },
  { naam: "Yoghurt natuur", portie: "1 potje (125g)", kh: 6 },
  { naam: "Honing", portie: "1 koffielepel", kh: 4 },
  { naam: "Vruchtensap", portie: "1 glas (200ml)", kh: 20 },
  { naam: "Sportdrank", portie: "1 bidon (500ml)", kh: 35 },
  { naam: "Pasta (hoofdmaaltijd)", portie: "120g rauw / 300g gaar", kh: 75 },
  { naam: "Rijst (hoofdmaaltijd)", portie: "115g rauw / 290g gaar", kh: 81 },
  { naam: "Aardappelen gekookt", portie: "1 bord (175g)", kh: 30 },
  { naam: "Appelmoes", portie: "1 schaaltje (150g)", kh: 27 },
]

// ─── TYPES ────────────────────────────────────────────────────────────────────
interface CoachData {
  atleet_naam?: string
  wedstrijd_naam?: string
  gewicht?: number
  sport?: string
  niveau?: string
  ervaring?: string
  wedstrijd_datum?: string
  start_time?: string
  eind_time?: string
  totale_min?: number
  temp?: number
  vochtigheid?: number
  hoogte?: number
  min_kh?: number
  max_kh?: number
  dag_target?: number
  factor?: number
  cl_waarden?: Record<string, number>
  ontbijt_kh?: number
  ontbijt_timing?: string
  ontbijt_tijd?: string
  maaltijd_moment?: string
  pool?: {
    drank: { naam: string; kh: number }[]
    gels: { naam: string; kh: number }[]
    cafe: { naam: string; kh: number }[]
    vast: { naam: string; kh: number }[]
    supplementen: string[]
  }
}

// ─── HELPER COMPONENTEN ───────────────────────────────────────────────────────
function ProgressBar({ stap }: { stap: number }) {
  const total = 6
  const pct = Math.round((stap / total) * 100)
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ color: "#94a3b8", fontSize: "0.72rem", fontWeight: 700, letterSpacing: 1 }}>STAP {stap + 1} VAN {total + 1}</span>
        <span style={{ color: "#f97316", fontSize: "0.72rem", fontWeight: 700 }}>{pct}% VOLTOOID</span>
      </div>
      <div style={{ background: "#1e293b", borderRadius: 8, height: 8, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg,#f97316,#fb923c)", borderRadius: 8, transition: "width 0.3s" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, flexWrap: "wrap", gap: 4 }}>
        {STAP_LABELS.map((lbl, i) => (
          <span key={i} style={{ fontSize: "0.62rem", color: i === stap ? "#f97316" : i > stap ? "#334155" : "#22c55e", fontWeight: 700 }}>{lbl}</span>
        ))}
      </div>
    </div>
  )
}

function CoachBubble({ tekst }: { tekst: string }) {
  return (
    <div style={{ display: "flex", gap: 14, marginBottom: 20, alignItems: "flex-end" }}>
      <div style={{ flexShrink: 0, width: 52, height: 52, background: "rgba(249,115,22,0.15)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.8rem", border: "2px solid rgba(249,115,22,0.3)" }}>
        🤖
      </div>
      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "0 14px 14px 14px", padding: "14px 18px", color: "#f8fafc", fontSize: "0.9rem", lineHeight: 1.6, maxWidth: 680 }}
        dangerouslySetInnerHTML={{ __html: tekst }} />
    </div>
  )
}

function NavKnoppen({ onVorige, onVolgende, vorigeLabel = "← Vorige", volgendeLabel = "Volgende →" }: {
  onVorige?: () => void; onVolgende?: () => void; vorigeLabel?: string; volgendeLabel?: string
}) {
  const btn = (onClick: (() => void) | undefined, label: string, primary: boolean) => (
    <button onClick={onClick} style={{ flex: 1, padding: "12px 0", background: primary ? "#f97316" : "#1e293b", color: primary ? "#0c0c0c" : "#94a3b8", border: `1px solid ${primary ? "#f97316" : "#334155"}`, borderRadius: 10, fontSize: "0.88rem", fontWeight: 700, cursor: "pointer" }}>
      {label}
    </button>
  )
  return (
    <div style={{ display: "flex", gap: 10, marginTop: 24 }}>
      {onVorige && btn(onVorige, vorigeLabel, false)}
      {onVolgende && btn(onVolgende, volgendeLabel, true)}
    </div>
  )
}

// ─── HOOFDCOMPONENT ───────────────────────────────────────────────────────────
export default function CoachPage() {
  const { user, token } = useAuth()
  const [stap, setStap] = useState(0)
  const [data, setData] = useState<CoachData>({})
  const [fout, setFout] = useState("")

  // Profiel state
  const [atleetNaam, setAtleetNaam] = useState("")
  const [wedstrijdNaam, setWedstrijdNaam] = useState("")
  const [gewicht, setGewicht] = useState(70)
  const [sport, setSport] = useState("Fietsen")
  const [niveau, setNiveau] = useState("Recreatief")
  const [ervaring, setErvaring] = useState("Eerste wedstrijd")

  // Wedstrijd state
  const [datum, setDatum] = useState("")
  const [startTijd, setStartTijd] = useState("09:00")
  const [eindTijd, setEindTijd] = useState("12:00")
  const [temp, setTemp] = useState(18)
  const [vochtigheid, setVochtigheid] = useState(50)
  const [hoogte, setHoogte] = useState(0)

  // Carboloading state: { "d1_Ontbijt_Havermout": 2, ... }
  const [clWaarden, setClWaarden] = useState<Record<string, number>>({})

  // Racedag state
  const [rdWaarden, setRdWaarden] = useState<Record<string, number>>({})
  const [ontbijtTiming, setOntbijtTiming] = useState("3-4 uur voor start (aanbevolen)")

  // Raceplan state
  const [poolDrank, setPoolDrank] = useState([{ naam: "", kh: 70 }])
  const [poolGels, setPoolGels] = useState([{ naam: "", kh: 22 }])
  const [poolCafe, setPoolCafe] = useState<{ naam: string; kh: number }[]>([])
  const [poolVast, setPoolVast] = useState<{ naam: string; kh: number }[]>([])
  const [supplementen, setSupplementen] = useState([""])
  const [rapport, setRapport] = useState("")
  const [rapportLaden, setRapportLaden] = useState(false)
  // Preview raceplan states
  const [previewActief, setPreviewActief] = useState(false)
  const [urenData, setUrenData] = useState<Record<number, {timing: string; prod: string; aantal: number; water: string}[]>>({})
  const [notities, setNotities] = useState<Record<number, string>>({})

  const s = { background: "#141414", minHeight: "100vh", padding: "20px 16px", fontFamily: "system-ui, sans-serif", color: "#f5f3ef" }
  const card = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 12 }
  // Voor number inputs: onChange (direct feedback)
  // Voor text inputs: onBlur (geen re-render bij elke toets)
  const inp = (value: string | number, onChange: (v: any) => void, type = "text", placeholder = "") => {
    if (type === "number") {
      return {
        defaultValue: value,
        onBlur: (e: any) => { const v = parseFloat(e.target.value) || 0; if (v !== value) onChange(v) },
        type, placeholder,
        style: { width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }
      }
    }
    return {
      defaultValue: value,
      onBlur: (e: any) => { if (e.target.value !== value) onChange(e.target.value) },
      type, placeholder,
      style: { width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }
    }
  }

  // ── Berekeningen ───────────────────────────────────────────────────────────
  function berekenDuur() {
    const [sh, sm] = startTijd.split(":").map(Number)
    const [eh, em] = eindTijd.split(":").map(Number)
    let min = (eh * 60 + em) - (sh * 60 + sm)
    if (min <= 0) min += 24 * 60
    return min
  }

  function clDagTarget() {
    const min = data.totale_min || berekenDuur()
    const factor = min > 300 ? 12 : min > 180 ? 10 : min > 90 ? 8 : 6
    return { target: Math.round(gewicht * factor), factor }
  }

  function clMomentTarget(moment: string) {
    const { target } = clDagTarget()
    return Math.round(target * (CL_MAALTIJD_PCT[moment] || 0.15))
  }

  function clMomentKh(dag: number, moment: string) {
    return (CL_MAALTIJDEN[moment as keyof typeof CL_MAALTIJDEN] || []).reduce((acc, p) => {
      return acc + (clWaarden[`d${dag}_${moment}_${p.naam}`] || 0) * p.kh
    }, 0)
  }

  function clDagKh(dag: number) {
    return Object.keys(CL_MAALTIJDEN).reduce((acc, m) => acc + clMomentKh(dag, m), 0)
  }

  function rdKhTotaal() {
    return RACEDAG_VOEDING.reduce((acc, p) => acc + (rdWaarden[`rd_${p.naam}`] || 0) * p.kh, 0)
  }

  function ontbijtTijd() {
    const [h, m] = startTijd.split(":").map(Number)
    const offsets: Record<string, number> = {
      "3-4 uur voor start (aanbevolen)": -210, "2-3 uur voor start": -150, "1-2 uur voor start (licht)": -90
    }
    const offset = offsets[ontbijtTiming] || -210
    const total = h * 60 + m + offset
    const th = Math.floor(((total % 1440) + 1440) % 1440 / 60)
    const tm = ((total % 1440) + 1440) % 1440 % 60
    return `${th.toString().padStart(2, "0")}:${tm.toString().padStart(2, "0")}`
  }

  function vochPerUur() {
    const basis = temp > 25 ? 800 : temp > 15 ? 600 : 400
    const factor = (hoogte / 1000) * 0.15 + (vochtigheid > 70 ? 0.15 : 0)
    return Math.round(basis * (1 + factor) / 10) * 10
  }

  // ── Rapport genereren ──────────────────────────────────────────────────────
  async function genereerRapport(
    urenData: Record<number, {timing: string; prod: string; aantal: number; water: string}[]>,
    notities: Record<number, string>
  ) {
    setRapportLaden(true)
    const totMin = data.totale_min || berekenDuur()
    const aantalUren = Math.ceil(totMin / 60)
    const [minKh, maxKh] = getKhRange(sport, totMin)
    const vpm = vochPerUur()
    const adviezen = getRaceAdviezen(sport, totMin)
    const geenKhDrempel: Record<string,number> = { "Fietsen":75,"Lopen":60,"Duatlon":75,"Crossduatlon":90 }
    const geenKh = totMin < (geenKhDrempel[sport] || 75)
    const { target: dagTarget } = clDagTarget()

    // Bouw product lookup
    function waterMl(w: string) { const m = w.match(/(\d+)ml/); return m ? parseInt(m[1]) : 0 }
    const alleProducten: { lbl: string; kh: number; emoji: string; water: number }[] = []
    poolDrank.filter(p => p.naam).forEach(p => {
      const khPm = Math.round(p.kh / 500 * Math.round(vpm/3))
      alleProducten.push({ lbl: `🥤 ${p.naam} (${Math.round(vpm/3)}ml)`, kh: khPm, emoji: "🥤", water: Math.round(vpm/3) })
    })
    poolGels.filter(p => p.naam).forEach(p => alleProducten.push({ lbl: `⚡ ${p.naam}`, kh: p.kh, emoji: "⚡", water: 150 }))
    poolCafe.filter(p => p.naam).forEach(p => alleProducten.push({ lbl: `☕ ${p.naam} (CAF)`, kh: p.kh, emoji: "☕", water: 150 }))
    poolVast.filter(p => p.naam).forEach(p => alleProducten.push({ lbl: `🍌 ${p.naam}`, kh: p.kh, emoji: "🍌", water: 0 }))

    function getProd(lbl: string) { return alleProducten.find(p => p.lbl === lbl) }

    // Bouw uren array
    const uren = Array.from({length: aantalUren}, (_, u) => {
      const isLast = u === aantalUren - 1
      const restMin = isLast ? (totMin % 60 || 60) : 60
      const [curMin, curMax] = (() => {
        if (!isLast) return [minKh, maxKh]
        if (restMin < 15) return [0, 0]
        if (restMin < 31) return [15, 20]
        if (restMin < 46) return [30, 40]
        return [Math.round(minKh*0.6), Math.round(maxKh*0.6)]
      })()
      const [sh, sm] = startTijd.split(":").map(Number)
      const tot = sh*60 + sm + u*60
      const uurStart = `${Math.floor(tot/60%24).toString().padStart(2,"0")}:${(tot%60).toString().padStart(2,"0")}`

      const rijen = urenData[u] || []
      const items = rijen.filter(r => r.prod !== "— leeg —" || waterMl(r.water) > 0).map(r => {
        const prod = getProd(r.prod)
        const kh = Math.round((prod?.kh || 0) * r.aantal)
        const wml = waterMl(r.water) * r.aantal + (prod?.emoji === "🥤" ? prod.water * r.aantal : 0)
        const badge = prod?.emoji === "🥤" ? "SD" : prod?.emoji === "⚡" ? "GEL" : prod?.emoji === "☕" ? "CAF" : prod?.emoji === "🍌" ? "VAST" : prod?.emoji === "💊" ? "SUP" : "H2O"
        const badgeKleur = { SD:"#3b82f6",GEL:"#f97316",CAF:"#8b5cf6",VAST:"#22c55e",SUP:"#06b6d4",H2O:"#64748b" }[badge] || "#64748b"
        const naam = r.prod === "— leeg —" ? `Water (${waterMl(r.water)}ml)` : r.prod.replace(/^[🥤⚡☕🍌💊💧] /,"")
        const _aantal = r.aantal
        const aantalLbl = _aantal === 0.5 ? "½ " : _aantal !== 1 ? `${_aantal}× ` : ""
        return { timing: r.timing, badge, badgeKleur, naam, kh, wml, aantalLbl }
      })

      const uurKh = items.reduce((a,i) => a+i.kh, 0)
      const uurVocht = items.reduce((a,i) => a+i.wml, 0)
      const vTarget = Math.round(vpm * (restMin/60))
      const khPct = curMax > 0 ? Math.min(100, Math.round(uurKh/curMax*100)) : 0
      const vPct = vTarget > 0 ? Math.min(100, Math.round(uurVocht/vTarget*100)) : 0
      const khKleur = uurKh > curMax ? "#ef4444" : uurKh >= curMin ? "#22c55e" : khPct >= 50 ? "#fbbf24" : "#ef4444"
      const vKleur = uurVocht > vTarget*1.3 ? "#ef4444" : vPct >= 80 ? "#22c55e" : vPct >= 50 ? "#fbbf24" : "#f97316"

      return { uur: u+1, start: uurStart, items, uurKh, uurVocht, curMin, curMax, khPct, vPct, khKleur, vKleur, geenKh, isLast, notitie: notities[u]||"", restMin }
    })

    const totaalKh = uren.reduce((a,u) => a+u.uurKh, 0)
    const totaalVocht = uren.reduce((a,u) => a+u.uurVocht, 0)

    // CL data voor rapport
    const CLkh: Record<string,number> = {
      "Wit brood":17,"Volkorenbrood":14,"Havermout":27,"Ontbijtgranen":25,"Muesli":30,"Banaan":30,
      "Melk":9,"Yoghurt natuur":6,"Honing":4,"Vruchtensap":20,"Sportdrank":35,
      "Pasta (hoofdmaaltijd)":75,"Pasta (bijgerecht)":37,"Rijst (hoofdmaaltijd)":81,"Rijst (bijgerecht)":42,
      "Aardappelen gekookt":30,"Groentenmix":6,"Rozijnen":15,"Muesli/granenreep":26,"Appelmoes":27,"Speculoos":5
    }

    const rdKh = Math.round(rdKhTotaal())
    const vochAdvies = temp > 25 ? "600–800ml (warm weer)" : temp > 15 ? "400–600ml" : "300–500ml (koel)"

    const html = `<!DOCTYPE html>
<html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Carboo Race Nutrition Plan — ${atleetNaam}</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:16px}
.page{max-width:780px;margin:0 auto;display:flex;flex-direction:column;gap:12px}
.header{background:#1e293b;border-radius:10px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;border-left:5px solid #f97316}
.header h1{font-size:18px;font-weight:900;color:#f97316;letter-spacing:2px}
.header p{font-size:12px;color:#64748b;margin-top:2px}
.header-r{text-align:right;font-size:12px;color:#64748b;line-height:1.5}
.header-r b{color:#f1f5f9;font-size:14px;display:block}
.info-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;background:#1e293b;border-radius:10px;padding:12px 14px}
.info-item .lbl{font-size:10px;font-weight:bold;color:#64748b;text-transform:uppercase}
.info-item .val{font-size:13px;font-weight:bold;color:#f1f5f9;margin-top:1px}
.sectie{background:#1e293b;border-radius:10px;padding:12px 14px}
.stitel{font-size:12px;font-weight:bold;color:#f97316;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #334155}
.raceplan-wrap{display:grid;grid-template-columns:1fr 150px;gap:10px}
.uur-blok{margin-bottom:6px}
.uur-kop{background:#0f172a;border-radius:5px 5px 0 0;padding:5px 10px;font-size:11px;font-weight:bold;color:#93c5fd}
.item-row{display:flex;align-items:center;gap:6px;padding:3px 8px;font-size:11px;border-bottom:1px solid rgba(255,255,255,0.03)}
.item-min{width:36px;color:#3b82f6;font-weight:bold;font-size:10px;flex-shrink:0}
.item-badge{font-size:9px;font-weight:bold;border:1px solid;border-radius:2px;padding:0 3px;flex-shrink:0}
.item-naam{flex:1;color:#cbd5e1}
.item-kh{color:#f97316;font-weight:bold;font-size:11px}
.prog-wrap{background:#0a0f1e;border-radius:0 0 5px 5px;padding:4px 8px 5px}
.prog-row{display:flex;align-items:center;gap:5px;margin-bottom:2px}
.prog-lbl{font-size:9px;color:#64748b;width:20px;flex-shrink:0}
.prog-bar{flex:1;background:#1e293b;border-radius:3px;height:5px}
.prog-fill{height:100%;border-radius:3px}
.prog-val{font-size:9px;width:40px;text-align:right}
.notitie{font-size:10px;color:#fbbf24;padding:2px 8px;font-style:italic}
.racemap{background:#0f172a;border-radius:6px;padding:8px}
.rm-titel{font-size:11px;font-weight:bold;color:#f97316;letter-spacing:1px;margin-bottom:2px}
.rm-sub{font-size:9px;color:#475569;margin-bottom:6px}
.rm-tbl{width:100%;border-collapse:collapse;line-height:1}
.rm-tbl td{padding:1px 0}
.rm-dot{width:9px;text-align:center;position:relative}
.rm-lijn{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#334155;transform:translateX(-50%)}
.rm-badges{font-size:9px;line-height:12px}
.badge-sd{color:#3b82f6;border:1px solid #3b82f6;border-radius:2px;padding:0 2px;font-size:8px;font-weight:bold}
.badge-gel{color:#f97316;border:1px solid #f97316;border-radius:2px;padding:0 2px;font-size:8px;font-weight:bold}
.badge-caf{color:#8b5cf6;border:1px solid #8b5cf6;border-radius:2px;padding:0 2px;font-size:8px;font-weight:bold}
.badge-vast{color:#22c55e;border:1px solid #22c55e;border-radius:2px;padding:0 2px;font-size:8px;font-weight:bold}
.badge-h2o{color:#64748b;border:1px solid #64748b;border-radius:2px;padding:0 2px;font-size:8px;font-weight:bold}
.badge-sup{color:#06b6d4;border:1px solid #06b6d4;border-radius:2px;padding:0 2px;font-size:8px;font-weight:bold}
.legende{display:flex;flex-wrap:wrap;gap:6px;font-size:9px;color:#64748b;margin-top:6px;padding-top:4px;border-top:1px solid #1e293b}
.adv-blok{background:rgba(59,130,246,0.08);border:1px solid #3b82f6;border-radius:8px;padding:10px 14px}
.adv-item{display:flex;gap:6px;margin-bottom:4px;font-size:12px;color:#e2e8f0}
.footer{font-size:10px;color:#334155;text-align:center;padding:6px}
</style></head><body>
<div class="page">

<div class="header">
  <div>
    <h1>🏁 CARBOO RACE NUTRITION PLAN</h1>
    <p>${wedstrijdNaam}${wedstrijdNaam ? " — " : ""}${datum} — Start ${startTijd}</p>
  </div>
  <div class="header-r"><b>${atleetNaam}</b>${sport} · ${Math.floor(totMin/60)}u${(totMin%60).toString().padStart(2,"0")}m<br>${SPORT_ICONS[sport]||""} ${niveau}</div>
</div>

<div class="info-grid">
  <div class="info-item"><div class="lbl">Gewicht</div><div class="val">${gewicht} kg</div></div>
  <div class="info-item"><div class="lbl">Start / Eind</div><div class="val">${startTijd} — ${eindTijd}</div></div>
  <div class="info-item"><div class="lbl">KH target/uur</div><div class="val" style="color:#f97316">${geenKh ? "— (<75min)" : minKh+"–"+maxKh+"g"}</div></div>
  <div class="info-item"><div class="lbl">Temp / Vochtigheid</div><div class="val">${temp}°C | ${vochtigheid}%</div></div>
  <div class="info-item"><div class="lbl">Hoogte</div><div class="val">${hoogte} m</div></div>
  <div class="info-item"><div class="lbl">Niveau / Ervaring</div><div class="val">${niveau}</div></div>
</div>

<div class="sectie">
  <div class="stitel">Race Advies — ${sport}</div>
  <div class="adv-blok">
    ${adviezen.map(a => `<div class="adv-item"><span style="color:#f97316">→</span><span>${a}</span></div>`).join("")}
  </div>
</div>

<div class="sectie">
  <div class="stitel">Carboloading — Laatste 48 uur</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
    ${[1,2].map(dag => {
      const dagKh = Math.round(clDagKh(dag))
      const pct = Math.min(100,Math.round(dagKh/dagTarget*100))
      const kleur = pct>=80?"#22c55e":pct>=50?"#fbbf24":"#ef4444"
      const details = Object.keys(CL_MAALTIJDEN).map(m => {
        const items = (CL_MAALTIJDEN[m as keyof typeof CL_MAALTIJDEN]||[]).filter(p => (clWaarden[`d${dag}_${m}_${p.naam}`]||0)>0)
        if (!items.length) return ""
        return `<div style="font-size:10px;color:#94a3b8;margin:1px 0"><b style="color:#64748b">${m}:</b> ${items.map(p => `${clWaarden[`d${dag}_${m}_${p.naam}`]}× ${p.naam}`).join(", ")}</div>`
      }).join("")
      return `<div style="background:#0f172a;border-radius:8px;padding:10px">
        <div style="font-weight:bold;color:#f8fafc;font-size:12px;margin-bottom:4px">Dag ${dag} — ${dag===1?"2 dagen voor race":"1 dag voor race"}</div>
        ${details || '<div style="font-size:10px;color:#334155">Geen data ingevuld</div>'}
        <div style="font-size:11px;color:${kleur};margin-top:6px">${dagKh}g / ${dagTarget}g KH (${pct}%)</div>
        <div style="background:#1e293b;border-radius:3px;height:6px;margin-top:4px"><div style="width:${Math.min(pct,100)}%;height:100%;background:${kleur};border-radius:3px"></div></div>
      </div>`
    }).join("")}
  </div>
</div>

<div class="sectie">
  <div class="stitel">Laatste Maaltijd — ${data.maaltijd_moment || "Ontbijt"}</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:8px">
    <div class="info-item"><div class="lbl">Timing</div><div class="val">${ontbijtTiming.split(" ").slice(0,2).join(" ")}</div></div>
    <div class="info-item"><div class="lbl">Maaltijd om</div><div class="val">${ontbijtTijd()}</div></div>
    <div class="info-item"><div class="lbl">Totaal KH</div><div class="val" style="color:#f97316">${rdKh}g</div></div>
  </div>
  ${RACEDAG_VOEDING.filter(p => (rdWaarden[`rd_${p.naam}`]||0)>0).map(p => {
    const val = rdWaarden[`rd_${p.naam}`]||0
    return `<div style="font-size:11px;color:#cbd5e1;padding:2px 0">${val}× ${p.naam} = ${Math.round(val*p.kh)}g KH</div>`
  }).join("")||'<div style="font-size:11px;color:#334155">Geen data ingevuld</div>'}
  <div style="font-size:11px;color:#64748b;margin-top:6px">💧 Aanbevolen vocht voor start: ${vochAdvies}</div>
</div>

<div class="sectie">
  <div class="stitel">Raceplan</div>
  <div class="raceplan-wrap">
    <div>
      ${uren.map(u => {
        const itemRows = u.items.map(item => {
          const badgeClass = {SD:"badge-sd",GEL:"badge-gel",CAF:"badge-caf",VAST:"badge-vast",H2O:"badge-h2o",SUP:"badge-sup"}[item.badge]||"badge-h2o"
          const waterStr = item.wml > 0 && !["SD"].includes(item.badge) ? ` <span class="badge-h2o">+${Math.round(item.wml)}ml</span>` : ""
          return `<div class="item-row">
            <span class="item-min">${item.timing}</span>
            <span class="${badgeClass} item-badge">${item.badge}</span>
            <span class="item-naam">${item.aantalLbl}${item.naam}${waterStr}</span>
            ${item.kh>0?`<span class="item-kh">${item.kh}g</span>`:""}
          </div>`
        }).join("")
        const notitieHtml = u.notitie ? `<div class="notitie">◂ ${u.notitie}</div>` : ""
        const khBalkHtml = !u.geenKh && u.curMax > 0 ? `<div class="prog-row"><span class="prog-lbl">KH</span><div class="prog-bar"><div class="prog-fill" style="width:${u.khPct}%;background:${u.khKleur}"></div></div><span class="prog-val" style="color:${u.khKleur}">${u.uurKh}g</span></div>` : ""
        return `<div class="uur-blok">
          <div class="uur-kop">UUR ${u.uur} — ${u.start}${u.isLast && u.restMin<60?` ⏱ nog ${u.restMin}min`:""}</div>
          ${u.items.length>0?itemRows:"<div class='item-row' style='color:#334155;font-size:10px'>Geen items</div>"}
          ${notitieHtml}
          <div class="prog-wrap">
            ${khBalkHtml}
            <div class="prog-row"><span class="prog-lbl">💧</span><div class="prog-bar"><div class="prog-fill" style="width:${u.vPct}%;background:${u.vKleur}"></div></div><span class="prog-val" style="color:${u.vKleur}">${u.uurVocht}ml</span></div>
          </div>
        </div>`
      }).join("")}
      <div style="background:#1e293b;border-radius:8px;padding:10px;display:flex;justify-content:space-between;margin-top:6px">
        <span style="color:#94a3b8;font-weight:bold;font-size:12px">TOTAAL RACE</span>
        <div><span style="color:#3b82f6;font-weight:bold;font-size:12px">💧 ${totaalVocht}ml</span>&nbsp;&nbsp;<span style="color:#f8fafc;font-weight:900;font-size:13px">${totaalKh}g KH</span></div>
      </div>
    </div>

    <div class="racemap">
      <div class="rm-titel">📋 RACEMAP</div>
      <div class="rm-sub">${sport} · ${Math.floor(totMin/60)}u${(totMin%60).toString().padStart(2,"0")}m</div>
      <table class="rm-tbl">
        ${uren.flatMap(u => {
          const [sh,sm] = u.start.split(":").map(Number)
          return u.items.map((item, idx) => {
            const offMin = parseInt(item.timing.replace("+","").replace("min","")) || 20
            const exact = `${Math.floor((sh*60+sm+offMin)/60%24).toString().padStart(2,"0")}:${((sh*60+sm+offMin)%60).toString().padStart(2,"0")}`
            const badgeClass = {SD:"badge-sd",GEL:"badge-gel",CAF:"badge-caf",VAST:"badge-vast",H2O:"badge-h2o",SUP:"badge-sup"}[item.badge]||"badge-h2o"
            const isFirst = idx===0
            return `<tr>
              <td style="text-align:right;padding-right:3px;font-size:9px;width:32px;${isFirst?"color:#f97316;font-weight:bold":"color:#475569"}">${exact}</td>
              <td class="rm-dot"><div class="rm-lijn"></div><span style="${isFirst?"background:#f97316":"background:#334155"};width:${isFirst?5:3}px;height:${isFirst?5:3}px;border-radius:50%;display:inline-block;position:relative"></span></td>
              <td class="rm-badges"><span class="${badgeClass}">${item.badge}</span> ${item.aantalLbl}${item.naam.split("(")[0].trim().slice(0,12)}${item.kh>0?` <span style="color:#f97316">${item.kh}g</span>`:""}${item.wml>0&&item.badge!=="SD"?` <span style="color:#64748b;font-size:8px">+${item.wml}ml</span>`:item.badge==="SD"?` <span style="color:#64748b;font-size:8px">${item.wml}ml</span>`:""}</td>
            </tr>`
          })
        }).join("")}
      </table>
      <div class="legende">
        <span><b class="badge-sd">SD</b> Drank</span>
        <span><b class="badge-gel">GEL</b> Gel</span>
        <span><b class="badge-caf">CAF</b> Cafeïne</span>
        <span><b class="badge-vast">VAST</b> Vast</span>
        <span><b class="badge-h2o">H2O</b> Water</span>
      </div>
    </div>
  </div>
</div>

${supplementen.filter(s=>s).length > 0 ? `
<div class="sectie">
  <div class="stitel">💊 Supplementen</div>
  ${supplementen.filter(s=>s).map(s => `<div style="font-size:12px;color:#cbd5e1;padding:3px 0">→ ${s}</div>`).join("")}
</div>` : ""}

<div class="footer">Gegenereerd door Carboo Race Nutrition · Versie Next.js · Dit plan is een richtlijn voor sporters.</div>
</div></body></html>`

    setRapport(html)

    // Automatisch opslaan in dossier
    if (token) {
      const totMin = data.totale_min || berekenDuur()
      try {
        await fetch(`${API}/api/dossier/rapporten`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            naam: `${wedstrijdNaam || "Race"} — ${datum || new Date().toLocaleDateString("nl-BE")}`,
            type: "race_plan",
            html,
            meta: {
              sport,
              duur: `${Math.floor(totMin/60)}u${(totMin%60).toString().padStart(2,"0")}m`,
              datum,
              atleet: atleetNaam,
            }
          })
        })
      } catch {}
    }

    setRapportLaden(false)
  }



  // ─── STAP RENDERERS ─────────────────────────────────────────────────────────

  function renderWelkom() {
    const naam = user?.email?.split("@")[0] || "Atleet"
    return (
      <div>
        <CoachBubble tekst={`Hoi <b>${naam}</b>! 👋 Ik ben <b>Carboo</b>, jouw persoonlijke race nutrition coach.<br><br>Ik ga je stap voor stap begeleiden om jouw voeding optimaal af te stemmen op je komende wedstrijd. We bouwen samen een <b>volledig voedingsplan</b> op:<br><br>🍝 <b>Carbohydrate loading</b> — de 2 dagen vóór de race<br>🏁 <b>Racedag voeding</b> — ontbijt en pre-race strategie<br>⏱️ <b>Slim raceplan</b> — uur per uur wat je eet en drinkt<br><br>Dit duurt slechts <b>5-7 minuten</b>. Ben je er klaar voor?`} />
        <div style={{ fontSize: "0.72rem", color: "#64748b", textAlign: "center", marginTop: 4, padding: "8px 16px", borderTop: "1px solid #1e293b" }}>
          Carboo is een hulpmiddel voor recreatieve en competitieve sporters. Bij medische aandoeningen raadpleeg je best een erkend diëtist of arts.
        </div>
        <button onClick={() => setStap(1)} style={{ width: "100%", padding: "14px 0", marginTop: 20, background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 10, fontSize: "0.95rem", fontWeight: 900, cursor: "pointer", letterSpacing: 1 }}>
          🚀 JA, LET'S GO!
        </button>
      </div>
    )
  }

  function renderProfiel() {
    const Label = ({ children }: { children: string }) => (
      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 }}>{children}</div>
    )
    const Veld = ({ children }: { children: any }) => (
      <div style={{ marginBottom: 12 }}>{children}</div>
    )
    const sel = (value: string, onChange: (v: string) => void, opties: string[]) => (
      <select value={value} onChange={e => onChange(e.target.value)}
        style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }}>
        {opties.map(o => <option key={o}>{o}</option>)}
      </select>
    )
    return (
      <div>
        <CoachBubble tekst="Laten we starten met jouw <b>profiel als atleet</b>. Dit helpt me om je koolhydraatbehoeften nauwkeurig te berekenen." />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <Veld><Label>Naam atleet</Label><input {...inp(atleetNaam, setAtleetNaam, "text", "Voornaam en naam")} /></Veld>
          <Veld><Label>Naam wedstrijd</Label><input {...inp(wedstrijdNaam, setWedstrijdNaam, "text", "bv. Ironman Frankfurt")} /></Veld>
          <Veld><Label>Gewicht (kg)</Label><input {...inp(gewicht, setGewicht, "number")} step={0.5} min={30} max={150} /></Veld>
          <Veld><Label>Discipline</Label>{sel(sport, setSport, SPORTEN)}</Veld>
        </div>
        <Veld><Label>Sportniveau</Label>{sel(niveau, setNiveau, NIVEAUS)}</Veld>
        <Veld><Label>Ervaring met wedstrijdvoeding</Label>{sel(ervaring, setErvaring, ERVARING_LIJST)}</Veld>
        <NavKnoppen onVorige={() => setStap(0)} onVolgende={() => { if (!atleetNaam) { setFout("Naam atleet is verplicht"); return } setData(d => ({ ...d, atleet_naam: atleetNaam, wedstrijd_naam: wedstrijdNaam, gewicht, sport, niveau, ervaring })); setFout(""); setStap(2) }} />
        {fout && <div style={{ color: "#ef4444", fontSize: "0.8rem", marginTop: 8 }}>{fout}</div>}
      </div>
    )
  }

  function renderWedstrijd() {
    const totMin = berekenDuur()
    const [minKh, maxKh] = getKhRange(sport, totMin)
    const Label = ({ children }: { children: string }) => (
      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700, textTransform: "uppercase" }}>{children}</div>
    )
    return (
      <div>
        <CoachBubble tekst="Nu de <b>wedstrijddetails</b>. Op basis van de duur en het type wedstrijd bereken ik hoeveel koolhydraten je nodig hebt." />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 12 }}>
          <div><Label>Wedstrijddatum</Label><input {...inp(datum, setDatum, "date")} /></div>
          <div><Label>Starttijd</Label><input {...inp(startTijd, setStartTijd, "time")} /></div>
          <div><Label>Geschatte eindtijd</Label><input {...inp(eindTijd, setEindTijd, "time")} /></div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 12 }}>
          <div><Label>Temperatuur (°C)</Label><input {...inp(temp, setTemp, "number")} min={-10} max={50} /></div>
          <div><Label>Vochtigheid (%)</Label><input {...inp(vochtigheid, setVochtigheid, "number")} min={0} max={100} /></div>
          <div><Label>Hoogte boven zee (m)</Label><input {...inp(hoogte, setHoogte, "number")} min={0} max={5000} /></div>
        </div>
        <div style={{ background: "rgba(59,130,246,0.1)", border: "1px solid #3b82f6", padding: 14, borderRadius: 10, textAlign: "center", color: "#93c5fd", fontWeight: 700, marginBottom: 16 }}>
          ⏱️ Duur: {Math.floor(totMin / 60)}u{(totMin % 60).toString().padStart(2, "0")}m &nbsp;|&nbsp; 📊 KH target: {minKh}–{maxKh}g/uur
        </div>
        <NavKnoppen onVorige={() => setStap(1)} onVolgende={() => { setData(d => ({ ...d, wedstrijd_datum: datum, start_time: startTijd, eind_time: eindTijd, totale_min: totMin, temp, vochtigheid, hoogte, min_kh: minKh, max_kh: maxKh })); setStap(3) }} />
      </div>
    )
  }

  function renderCarboloading() {
    const { target, factor } = clDagTarget()
    return (
      <div>
        <CoachBubble tekst={`Vul per maaltijd in wat je plant te eten. Ik bereken automatisch of je je doel haalt.<br><br>🎯 <b>Jouw dagdoel: ${target}g KH/dag</b> (${factor}g KH/kg · ${gewicht}kg)`} />
        {[1, 2].map(dag => {
          const dagKh = Math.round(clDagKh(dag))
          const pct = Math.min(100, Math.round(dagKh / target * 100))
          const kleur = dagKh > target ? "#ef4444" : pct >= 80 ? "#22c55e" : pct >= 50 ? "#fbbf24" : "#f97316"
          return (
            <div key={dag} style={{ ...card, marginBottom: 16 }}>
              <div style={{ fontSize: "0.75rem", color: "#f97316", fontWeight: 700, letterSpacing: 2, marginBottom: 12 }}>
                DAG {dag} — {dag === 1 ? "2 DAGEN VOOR RACE" : "1 DAG VOOR RACE"}
              </div>
              {Object.keys(CL_MAALTIJDEN).map(moment => {
                const mKh = Math.round(clMomentKh(dag, moment))
                const mTarget = clMomentTarget(moment)
                const mPct = Math.min(100, Math.round(mKh / mTarget * 100))
                const mKleur = mKh > mTarget ? "#ef4444" : mPct >= 80 ? "#22c55e" : mPct >= 50 ? "#fbbf24" : "#f97316"
                return (
                  <details key={moment} style={{ marginBottom: 8 }}>
                    <summary style={{ background: "#1e293b", padding: "10px 14px", borderRadius: 8, cursor: "pointer", color: "#f1f5f9", fontWeight: 600, listStyle: "none", display: "flex", justifyContent: "space-between" }}>
                      <span>{moment}</span>
                      <span style={{ color: mKleur, fontSize: "0.8rem" }}>{mKh}g / {mTarget}g KH</span>
                    </summary>
                    <div style={{ padding: "10px 4px" }}>
                      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 8, fontWeight: 700 }}>Voedingsmiddel · portie · KH/portie · aantal porties</div>
                      {(CL_MAALTIJDEN[moment as keyof typeof CL_MAALTIJDEN] || []).map(p => {
                        const key = `d${dag}_${moment}_${p.naam}`
                        const val = clWaarden[key] || 0
                        return (
                          <div key={p.naam} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                            <div style={{ flex: 1, fontSize: "0.82rem", color: "#f5f3ef" }}>
                              {p.naam} <span style={{ color: "#64748b", fontSize: "0.72rem" }}>— {p.portie} · {p.kh}g KH/portie</span>
                            </div>
                            <input type="number" min={0} max={20} step={0.5} defaultValue={val}
                              onBlur={e => { const v = parseFloat(e.target.value) || 0; setClWaarden(prev => ({ ...prev, [key]: v })) }}
                              style={{ width: 60, padding: "6px 8px", background: "#0f172a", border: "1px solid #334155", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem", textAlign: "center", outline: "none" }} />
                            {val > 0 && <span style={{ fontSize: "0.72rem", color: "#f97316", minWidth: 45 }}>= {Math.round(val * p.kh)}g</span>}
                          </div>
                        )
                      })}
                      <div style={{ height: 6, background: "#1e293b", borderRadius: 3, marginTop: 8 }}>
                        <div style={{ height: "100%", width: `${mPct}%`, background: mKleur, borderRadius: 3 }} />
                      </div>
                    </div>
                  </details>
                )
              })}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8, padding: "10px 14px", background: "#0f172a", borderRadius: 8 }}>
                <span style={{ color: "#94a3b8", fontSize: "0.82rem", fontWeight: 700 }}>TOTAAL DAG {dag}</span>
                <span style={{ color: kleur, fontWeight: 700 }}>{dagKh}g / {target}g KH ({pct}%)</span>
              </div>
              <div style={{ height: 8, background: "#1e293b", borderRadius: 4, marginTop: 6 }}>
                <div style={{ height: "100%", width: `${Math.min(pct, 100)}%`, background: kleur, borderRadius: 4 }} />
              </div>
            </div>
          )
        })}
        <NavKnoppen onVorige={() => setStap(2)} onVolgende={() => { setData(d => ({ ...d, cl_waarden: clWaarden, dag_target: clDagTarget().target, factor: clDagTarget().factor })); setStap(4) }} />
      </div>
    )
  }

  function renderRacedag() {
    const totMin = data.totale_min || berekenDuur()
    const khMin = Math.round(gewicht * 1)
    const khMax = Math.round(gewicht * 4)
    const rdKh = Math.round(rdKhTotaal())
    const pct = Math.min(100, Math.round(rdKh / khMax * 100))
    const kleur = rdKh > khMax ? "#ef4444" : pct >= 25 ? "#22c55e" : pct >= 15 ? "#fbbf24" : "#f97316"
    const [sh] = startTijd.split(":").map(Number)
    const maaltijdMom = sh < 13 ? "Ontbijt" : sh < 17 ? "Lunch" : "Avondmaal"

    return (
      <div>
        <CoachBubble tekst={`Perfect! Nu plannen we jouw <b>laatste maaltijd voor de wedstrijd</b>!<br><br>Het doel is om met volle glycogeenvoorraden aan de start te staan, maar zonder zwaar gevoel.<br><br>✅ Kies <b>licht verteerbare</b> producten: laag in vezels en vetten.<br>🎯 Alleen producten die je al kent uit training!`} />
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>WANNEER EET JE JOUW LAATSTE MAALTIJD?</div>
          <select value={ontbijtTiming} onChange={e => setOntbijtTiming(e.target.value)}
            style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }}>
            {["3-4 uur voor start (aanbevolen)", "2-3 uur voor start", "1-2 uur voor start (licht)"].map(o => <option key={o}>{o}</option>)}
          </select>
          <div style={{ fontSize: "0.75rem", color: "#60a5fa", marginTop: 6 }}>
            → Maaltijd om <b>{ontbijtTijd()}</b> ({maaltijdMom})
          </div>
        </div>
        <details>
          <summary style={{ background: "#1e293b", padding: "12px 16px", borderRadius: 8, cursor: "pointer", color: "#f1f5f9", fontWeight: 600, listStyle: "none", marginBottom: 8 }}>
            {maaltijdMom} — Voedingsmiddelen ({rdKh}g KH)
          </summary>
          <div style={{ padding: "10px 4px" }}>
            <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 8, fontWeight: 700 }}>Voedingsmiddel · portie · KH/portie · aantal</div>
            {RACEDAG_VOEDING.map(p => {
              const key = `rd_${p.naam}`
              const val = rdWaarden[key] || 0
              return (
                <div key={p.naam} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <div style={{ flex: 1, fontSize: "0.82rem", color: "#f5f3ef" }}>
                    {p.naam} <span style={{ color: "#64748b", fontSize: "0.72rem" }}>— {p.portie} · {p.kh}g KH</span>
                  </div>
                  <input type="number" min={0} max={20} step={1} defaultValue={val}
                    onBlur={e => { const v = parseInt(e.target.value) || 0; setRdWaarden(prev => ({ ...prev, [key]: v })) }}
                    style={{ width: 60, padding: "6px 8px", background: "#0f172a", border: "1px solid #334155", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem", textAlign: "center", outline: "none" }} />
                  {val > 0 && <span style={{ fontSize: "0.72rem", color: "#f97316", minWidth: 45 }}>= {Math.round(val * p.kh)}g</span>}
                </div>
              )
            })}
            <div style={{ height: 8, background: "#1e293b", borderRadius: 4, marginTop: 10 }}>
              <div style={{ height: "100%", width: `${pct}%`, background: kleur, borderRadius: 4 }} />
            </div>
            <div style={{ fontSize: "0.75rem", color: kleur, marginTop: 4, textAlign: "right" }}>{rdKh}g KH · doel {khMin}–{khMax}g</div>
          </div>
        </details>
        <NavKnoppen onVorige={() => setStap(3)} onVolgende={() => { setData(d => ({ ...d, rd_waarden: rdWaarden, ontbijt_kh: Math.round(rdKhTotaal()), ontbijt_timing: ontbijtTiming, ontbijt_tijd: ontbijtTijd(), maaltijd_moment: maaltijdMom })); setStap(5) }} />
      </div>
    )
  }

  function renderRaceplan() {
    const totMin = data.totale_min || berekenDuur()
    const [minKh, maxKh] = getKhRange(sport, totMin)
    const adviezen = getRaceAdviezen(sport, totMin)
    const geenKhDrempel: Record<string,number> = { "Fietsen":75,"Lopen":60,"Duatlon":75,"Crossduatlon":90 }
    const geenKh = totMin < (geenKhDrempel[sport] || 75)
    const vpm = vochPerUur()
    const aantalUren = Math.ceil(totMin / 60)

    // Bouw lijst van beschikbare producten voor dropdown
    const alleProducten: { lbl: string; kh: number; emoji: string; water: number }[] = []
    poolDrank.filter(p => p.naam).forEach(p => {
      const khPm = Math.round(p.kh / 500 * Math.round(vpm / 3))
      alleProducten.push({ lbl: `🥤 ${p.naam} (${Math.round(vpm/3)}ml)`, kh: khPm, emoji: "🥤", water: Math.round(vpm/3) })
    })
    poolGels.filter(p => p.naam).forEach(p => alleProducten.push({ lbl: `⚡ ${p.naam}`, kh: p.kh, emoji: "⚡", water: 150 }))
    poolCafe.filter(p => p.naam).forEach(p => alleProducten.push({ lbl: `☕ ${p.naam} (CAF)`, kh: p.kh, emoji: "☕", water: 150 }))
    poolVast.filter(p => p.naam).forEach(p => alleProducten.push({ lbl: `🍌 ${p.naam}`, kh: p.kh, emoji: "🍌", water: 0 }))
    supplementen.filter(s => s).forEach(s => alleProducten.push({ lbl: `💊 ${s}`, kh: 0, emoji: "💊", water: 0 }))
    alleProducten.push({ lbl: "— leeg —", kh: 0, emoji: "💧", water: 0 })

    const TIMING_OPTIES = ["+5min","+10min","+15min","+20min","+25min","+30min","+35min","+40min","+45min","+50min","+55min","+60min"]
    const WATER_OPTIES = ["—","💧 100ml","💧 150ml","💧 200ml","💧 250ml","💧 500ml"]

    function waterMl(w: string) { const m = w.match(/(\d+)ml/); return m ? parseInt(m[1]) : 0 }

    // Preview state (staat in hoofdcomponent)
    type RijType = { timing: string; prod: string; aantal: number; water: string }
    const initUren = (): Record<number, RijType[]> => {
      const result: Record<number, RijType[]> = {}
      for (let u = 0; u < aantalUren; u++) {
        const isLast = u === aantalUren - 1
        const drankLbl = alleProducten.find(p => p.emoji === "🥤")?.lbl || "— leeg —"
        if (isLast) {
          const restMin = totMin % 60 || 60
          result[u] = restMin < 30
            ? [{ timing: "+15min", prod: drankLbl, aantal: 1, water: "—" }]
            : [{ timing: "+20min", prod: drankLbl, aantal: 1, water: "—" },
               { timing: "+40min", prod: drankLbl, aantal: 1, water: "—" }]
        } else {
          result[u] = geenKh
            ? [{ timing: "+20min", prod: "— leeg —", aantal: 1, water: "💧 200ml" },
               { timing: "+40min", prod: "— leeg —", aantal: 1, water: "💧 200ml" }]
            : [{ timing: "+20min", prod: drankLbl, aantal: 1, water: "—" },
               { timing: "+40min", prod: drankLbl, aantal: 1, water: "—" }]
        }
      }
      return result
    }

    function getUur(u: number): RijType[] {
      return urenData[u] !== undefined ? urenData[u] : (initUren()[u] || [])
    }

    function setRij(u: number, i: number, veld: keyof RijType, val: any) {
      const huidig = getUur(u)
      const nieuw = huidig.map((r, j) => j === i ? { ...r, [veld]: val } : r)
      setUrenData(prev => ({ ...prev, [u]: nieuw }))
    }

    function voegRijToe(u: number) {
      const huidig = getUur(u)
      setUrenData(prev => ({ ...prev, [u]: [...huidig, { timing: "+20min", prod: "— leeg —", aantal: 1, water: "—" }] }))
    }

    function verwijderRij(u: number, i: number) {
      const huidig = getUur(u)
      setUrenData(prev => ({ ...prev, [u]: huidig.filter((_, j) => j !== i) }))
    }

    function uurKh(u: number) {
      return getUur(u).reduce((acc, rij) => {
        const prod = alleProducten.find(p => p.lbl === rij.prod)
        return acc + (prod?.kh || 0) * rij.aantal
      }, 0)
    }

    function uurVocht(u: number) {
      return getUur(u).reduce((acc, rij) => {
        const prod = alleProducten.find(p => p.lbl === rij.prod)
        const wml = waterMl(rij.water)
        const drankMl = prod?.emoji === "🥤" ? prod.water * rij.aantal : 0
        return acc + wml * rij.aantal + drankMl
      }, 0)
    }

    function vochTarget(u: number) {
      const isLast = u === aantalUren - 1
      const restMin = isLast ? (totMin % 60 || 60) : 60
      return Math.round(vpm * (restMin / 60))
    }

    function uurKhTarget(u: number): [number, number] {
      const isLast = u === aantalUren - 1
      if (!isLast) return [minKh, maxKh]
      const restMin = totMin % 60 || 60
      if (restMin < 15) return [0, 0]
      if (restMin < 31) return [15, 20]
      if (restMin < 46) return [30, 40]
      return [Math.round(minKh * 0.6), Math.round(maxKh * 0.6)]
    }

    function uurStartTijd(u: number) {
      const [sh, sm] = startTijd.split(":").map(Number)
      const tot = sh * 60 + sm + u * 60
      return `${Math.floor(tot/60%24).toString().padStart(2,"0")}:${(tot%60).toString().padStart(2,"0")}`
    }

    const totaalKh = Array.from({length: aantalUren}, (_,u) => uurKh(u)).reduce((a,b) => a+b, 0)
    const totaalVocht = Array.from({length: aantalUren}, (_,u) => uurVocht(u)).reduce((a,b) => a+b, 0)

    const PoolInvoer = ({ label, items, setItems, defaultKh }: {
      label: string; items: { naam: string; kh: number }[];
      setItems: (v: { naam: string; kh: number }[]) => void; defaultKh: number
    }) => (
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 6, fontWeight: 700, textTransform: "uppercase" as const }}>{label}</div>
        {items.map((item, i) => (
          <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
            <input defaultValue={item.naam}
              onBlur={e => { if (e.target.value !== item.naam) setItems(items.map((x,j) => j===i ? {...x,naam:e.target.value} : x)) }}
              placeholder="Naam product"
              style={{ flex: 1, padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none" }} />
            <input type="number" defaultValue={item.kh} min={0} max={200}
              onBlur={e => { const v = parseFloat(e.target.value)||0; if(v!==item.kh) setItems(items.map((x,j) => j===i ? {...x,kh:v} : x)) }}
              style={{ width: 65, padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f97316", fontSize: "0.82rem", outline: "none", textAlign: "center" as const }} />
            <span style={{ color: "#64748b", fontSize: "0.7rem", alignSelf: "center", minWidth: 28 }}>g KH</span>
            {items.length > 1 && <button onClick={() => setItems(items.filter((_,j) => j!==i))} style={{ background: "none", border: "none", color: "#475569", cursor: "pointer" }}>✕</button>}
          </div>
        ))}
        <button onClick={() => setItems([...items, {naam:"",kh:defaultKh}])} style={{ fontSize: "0.72rem", color: "#f97316", background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: 6, padding: "4px 10px", cursor: "pointer" }}>➕ Toevoegen</button>
      </div>
    )

    const sel = (val: string, onChange: (v:string)=>void, opties: string[]) => (
      <select value={val} onChange={e => onChange(e.target.value)}
        style={{ padding: "6px 4px", background: "#0f172a", border: "1px solid #1e293b", borderRadius: 5, color: "#f5f3ef", fontSize: "0.75rem", outline: "none", width: "100%" }}>
        {opties.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    )

    return (
      <div>
        <CoachBubble tekst="Vul jouw race producten in en klik op <b>👁 Preview schema</b> om het uur-per-uur plan aan te passen." />

        {/* Advies balk */}
        <div style={{ background: "rgba(59,130,246,0.08)", border: "1px solid #3b82f6", borderRadius: 10, padding: "12px 16px", marginBottom: 16 }}>
          <div style={{ color: "#60a5fa", fontWeight: 800, fontSize: "0.85rem", marginBottom: 8 }}>
            {SPORT_ICONS[sport]||""} {sport} · ⏱️ {Math.floor(totMin/60)}u{(totMin%60).toString().padStart(2,"0")}m
          </div>
          {adviezen.map((tip, i) => (
            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 4, color: "#e2e8f0", fontSize: "0.83rem" }}>
              <span style={{ color: "#f97316" }}>→</span><span>{tip}</span>
            </div>
          ))}
          {temp >= 28 && <div style={{ marginTop: 8, background: "rgba(239,68,68,0.15)", border: "1px solid #ef4444", borderRadius: 8, padding: "8px 12px", color: "#fca5a5", fontSize: "0.8rem" }}>🔴 <b>Extreme hitte</b> — verhoog vochtinname en gebruik ORS tabletten.</div>}
        </div>

        {/* Pool invoer */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 14 }}>
          <PoolInvoer label="🥤 Sportdrank — KH per 500ml" items={poolDrank} setItems={setPoolDrank} defaultKh={70} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <PoolInvoer label="⚡ Energy gels — KH/gel" items={poolGels} setItems={setPoolGels} defaultKh={22} />
            <PoolInvoer label="☕ Cafeïne gels — KH/gel" items={poolCafe} setItems={setPoolCafe} defaultKh={22} />
          </div>
          <PoolInvoer label="🍌 Vaste voeding — KH/portie" items={poolVast} setItems={setPoolVast} defaultKh={25} />
          <div>
            <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 6, fontWeight: 700, textTransform: "uppercase" as const }}>💊 Supplementen</div>
            {supplementen.map((s, i) => (
              <input key={i} defaultValue={s}
                onBlur={e => { if (e.target.value !== s) setSupplementen(supplementen.map((x,j) => j===i ? e.target.value : x)) }}
                placeholder="bv. Run Gum, SIS Hydro..."
                style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none", marginBottom: 6 }} />
            ))}
          </div>
        </div>

        {/* Knoppen */}
        <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
          <button onClick={() => setStap(4)} style={{ padding: "12px 20px", background: "#1e293b", color: "#94a3b8", border: "1px solid #334155", borderRadius: 10, fontSize: "0.85rem", fontWeight: 700, cursor: "pointer" }}>← Vorige</button>
          <button onClick={() => { setUrenData(initUren()); setPreviewActief(true) }}
            style={{ flex: 1, padding: "12px 0", background: "#3b82f6", color: "#fff", border: "none", borderRadius: 10, fontSize: "0.88rem", fontWeight: 700, cursor: "pointer" }}>
            👁 Preview schema
          </button>
        </div>

        {/* Preview schema */}
        {previewActief && (
          <div>
            <div style={{ display: "flex", gap: 14, alignItems: "flex-start", marginBottom: 14 }}>
              <div style={{ fontSize: "2rem", flexShrink: 0, marginTop: 4 }}>🤖</div>
              <div style={{ flex: 1, background: "#0f172a", border: "2px solid #3b82f6", borderRadius: 14, padding: "12px 16px" }}>
                <div style={{ color: "#60a5fa", fontWeight: 800, marginBottom: 4 }}>PREVIEW RACEPLAN — aanpasbaar</div>
                <div style={{ color: "#94a3b8", fontSize: "0.82rem" }}>Wijzig het plan indien gewenst! Pas tijdstip, product, aantal en water aan. Probeer KH én vocht balkjes groen te krijgen.</div>
              </div>
            </div>

            {/* Kolomtitels */}
            <div style={{ display: "grid", gridTemplateColumns: "70px 1fr 55px 90px 55px 28px", gap: 4, padding: "0 4px", marginBottom: 4 }}>
              {["TIJDSTIP","PRODUCT","AANTAL","WATER","KH",""].map((t,i) => (
                <div key={i} style={{ fontSize: "0.6rem", color: "#475569", fontWeight: 700 }}>{t}</div>
              ))}
            </div>

            {Array.from({length: aantalUren}, (_, u) => {
              const [curMin, curMax] = uurKhTarget(u)
              const uKh = Math.round(uurKh(u))
              const uVocht = uurVocht(u)
              const vTarget = vochTarget(u)
              const khPct = curMax > 0 ? Math.min(100, Math.round(uKh/curMax*100)) : 0
              const vPct = vTarget > 0 ? Math.min(100, Math.round(uVocht/vTarget*100)) : 0
              const khKleur = uKh > curMax ? "#ef4444" : uKh >= curMin ? "#22c55e" : khPct >= 50 ? "#fbbf24" : "#f97316"
              const vKleur = uVocht > vTarget*1.3 ? "#ef4444" : vPct >= 80 ? "#22c55e" : vPct >= 50 ? "#fbbf24" : "#f97316"
              const isLast = u === aantalUren - 1
              const restMin = isLast ? (totMin % 60 || 60) : 60

              return (
                <div key={u} style={{ marginBottom: 8 }}>
                  {/* Uur header */}
                  <div style={{ background: "#1e293b", borderRadius: "10px 10px 0 0", padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ color: "#f8fafc", fontWeight: 800, fontSize: "0.88rem" }}>
                      UUR {u+1} — {uurStartTijd(u)}
                      {isLast && restMin < 60 && <span style={{ color: "#f97316", fontSize: "0.72rem" }}> ⏱ nog {restMin} min</span>}
                    </span>
                    <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                      {geenKh ? "Geen extra KH" : `Doel: ${curMin}–${curMax}g KH`}
                    </span>
                  </div>

                  {/* Notitie veld */}
                  <div style={{ background: "#141414", padding: "4px 12px" }}>
                    <input defaultValue={notities[u] || ""}
                      onBlur={e => setNotities(prev => ({ ...prev, [u]: e.target.value }))}
                      placeholder="Notitie (bv. T2 wisseling, cola station...)"
                      style={{ width: "100%", background: "none", border: "none", outline: "none", color: "#64748b", fontSize: "0.72rem", fontStyle: "italic" }} />
                  </div>

                  {/* Rijen */}
                  {getUur(u).map((rij, i) => {
                    const prod = alleProducten.find(p => p.lbl === rij.prod)
                    const rijKh = Math.round((prod?.kh || 0) * rij.aantal)
                    return (
                      <div key={i} style={{ display: "grid", gridTemplateColumns: "70px 1fr 55px 90px 55px 28px", gap: 4, padding: "4px 4px", background: i%2===0 ? "#0a0a0a" : "#0f172a", alignItems: "center" }}>
                        <div>{sel(rij.timing, v => setRij(u,i,"timing",v), TIMING_OPTIES)}</div>
                        <div>
                          <select value={rij.prod} onChange={e => setRij(u,i,"prod",e.target.value)}
                            style={{ width: "100%", padding: "5px 4px", background: "#0f172a", border: "1px solid #1e293b", borderRadius: 5, color: "#f5f3ef", fontSize: "0.75rem", outline: "none" }}>
                            {alleProducten.map((p, pi) => <option key={`${p.lbl}_${pi}`} value={p.lbl}>{p.lbl}</option>)}
                          </select>
                        </div>
                        <div>
                          <input type="number" min={0.5} max={10} step={0.5} value={rij.aantal}
                            onChange={e => setRij(u,i,"aantal",parseFloat(e.target.value)||1)}
                            style={{ width: "100%", padding: "5px 4px", background: "#0f172a", border: "1px solid #1e293b", borderRadius: 5, color: "#f5f3ef", fontSize: "0.75rem", outline: "none", textAlign: "center" as const }} />
                        </div>
                        <div>{sel(rij.water, v => setRij(u,i,"water",v), WATER_OPTIES)}</div>
                        <div style={{ textAlign: "center" as const, fontSize: "0.75rem", color: rijKh > 0 ? "#f97316" : "#334155", fontWeight: 700 }}>{rijKh > 0 ? `${rijKh}g` : "—"}</div>
                        <button onClick={() => verwijderRij(u,i)} style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "0.85rem" }}>🗑</button>
                      </div>
                    )
                  })}

                  {/* Rij toevoegen */}
                  <div style={{ background: "#0a0a0a", padding: "4px 8px", display: "flex", justifyContent: "flex-end" }}>
                    <button onClick={() => voegRijToe(u)} style={{ fontSize: "0.72rem", color: "#3b82f6", background: "none", border: "none", cursor: "pointer" }}>➕ Rij</button>
                  </div>

                  {/* Balken */}
                  <div style={{ background: "#0a0a0a", borderRadius: "0 0 10px 10px", padding: "6px 12px 8px" }}>
                    {!geenKh && curMax > 0 && (
                      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                        <span style={{ fontSize: "0.65rem", color: "#64748b", width: 22 }}>KH</span>
                        <div style={{ flex: 1, background: "#1e293b", borderRadius: 3, height: 7 }}>
                          <div style={{ height: "100%", width: `${khPct}%`, background: khKleur, borderRadius: 3 }} />
                        </div>
                        <span style={{ fontSize: "0.65rem", color: khKleur, width: 45, textAlign: "right" as const }}>{uKh}g</span>
                      </div>
                    )}
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: "0.65rem", color: "#64748b", width: 22 }}>💧</span>
                      <div style={{ flex: 1, background: "#1e293b", borderRadius: 3, height: 7 }}>
                        <div style={{ height: "100%", width: `${vPct}%`, background: vKleur, borderRadius: 3 }} />
                      </div>
                      <span style={{ fontSize: "0.65rem", color: vKleur, width: 45, textAlign: "right" as const }}>{uVocht}ml</span>
                    </div>
                  </div>
                </div>
              )
            })}

            {/* Totaal */}
            <div style={{ background: "#1e293b", borderRadius: 10, padding: "12px 16px", display: "flex", justifyContent: "space-between", marginTop: 8 }}>
              <span style={{ color: "#94a3b8", fontWeight: 700 }}>TOTAAL RACE</span>
              <div style={{ display: "flex", gap: 16 }}>
                <span style={{ color: "#3b82f6", fontWeight: 700 }}>💧 {totaalVocht}ml</span>
                <span style={{ color: "#f8fafc", fontWeight: 900 }}>{totaalKh}g KH</span>
              </div>
            </div>

            {/* Reset + Genereer */}
            <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
              <button onClick={() => { setUrenData({}); setPreviewActief(false) }}
                style={{ flex: 1, padding: "10px 0", background: "#1e293b", color: "#64748b", border: "1px solid #334155", borderRadius: 10, fontSize: "0.82rem", cursor: "pointer" }}>
                🔄 Reset
              </button>
              <button onClick={() => genereerRapport(urenData, notities)}
                disabled={rapportLaden}
                style={{ flex: 2, padding: "12px 0", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 10, fontSize: "0.88rem", fontWeight: 700, cursor: "pointer" }}>
                {rapportLaden ? "⏳ Genereren..." : "📄 Genereer Race Nutrition Plan"}
              </button>
            </div>

            {rapport && (
              <div style={{ marginTop: 12 }}>
                <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid #22c55e", borderRadius: 10, padding: "10px 14px", marginBottom: 10, fontSize: "0.82rem", color: "#22c55e" }}>
                  ✓ Rapport klaar! Download hieronder of bekijk het in je 📁 Mijn Dossier.
                </div>
                <a href={`data:text/html;charset=utf-8,${encodeURIComponent(rapport)}`}
                  download={`Carboo_RacePlan_${atleetNaam.replace(/ /g,"_")}.html`}
                  style={{ display: "block", width: "100%", padding: "12px 0", background: "#22c55e", color: "#0c0c0c", borderRadius: 10, fontSize: "0.88rem", fontWeight: 700, cursor: "pointer", textAlign: "center" as const, textDecoration: "none", marginBottom: 8 }}>
                  📥 Download Race Nutrition Plan (HTML)
                </a>
    
              </div>
            )}
          </div>
        )}
      </div>
    )
  }



  function renderSamenvatting() {
    const totMin = data.totale_min || berekenDuur()
    const { target } = clDagTarget()
    return (
      <div>
        <CoachBubble tekst={`🎉 <b>Super gedaan, ${atleetNaam || "Atleet"}!</b> Hier is jouw volledig gepersonaliseerd race nutrition plan.`} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10, marginBottom: 20 }}>
          {[
            ["Atleet", atleetNaam || "—", "#f97316"],
            ["Wedstrijd", wedstrijdNaam || "—", "#3b82f6"],
            ["Sport", `${SPORT_ICONS[sport] || ""} ${sport}`, "#22c55e"],
            ["Duur", `${Math.floor(totMin/60)}u${(totMin%60).toString().padStart(2,"0")}m`, "#8b5cf6"],
          ].map(([lbl, val, color]) => (
            <div key={lbl as string} style={{ textAlign: "center", padding: 12, background: "#0f172a", borderRadius: 10, borderTop: `3px solid ${color}` }}>
              <div style={{ fontSize: "0.62rem", color: "#64748b", fontWeight: 700 }}>{lbl}</div>
              <div style={{ fontSize: "0.95rem", fontWeight: 800, color: "#f8fafc", marginTop: 4 }}>{val}</div>
            </div>
          ))}
        </div>
        <div style={card}>
          <div style={{ fontSize: "0.72rem", color: "#f97316", fontWeight: 700, marginBottom: 12 }}>📊 CARBOLOADING OVERZICHT</div>
          {[1, 2].map(dag => {
            const dagKh = Math.round(clDagKh(dag))
            const pct = Math.min(100, Math.round(dagKh / target * 100))
            const kleur = pct >= 80 ? "#22c55e" : pct >= 50 ? "#fbbf24" : "#ef4444"
            return (
              <div key={dag} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ color: "#f8fafc", fontWeight: 700 }}>Dag {dag}</span>
                  <span style={{ color: kleur }}>{dagKh}g / {target}g</span>
                </div>
                <div style={{ height: 8, background: "#0f172a", borderRadius: 4 }}>
                  <div style={{ height: "100%", width: `${Math.min(pct, 100)}%`, background: kleur, borderRadius: 4 }} />
                </div>
              </div>
            )
          })}
        </div>
        <div style={card}>
          <div style={{ fontSize: "0.72rem", color: "#f97316", fontWeight: 700, marginBottom: 10 }}>🏁 RACEDAG SAMENVATTING</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div><div style={{ fontSize: "0.65rem", color: "#64748b" }}>Laatste maaltijd om</div><div style={{ fontSize: "0.95rem", fontWeight: 700 }}>{ontbijtTijd()}</div></div>
            <div><div style={{ fontSize: "0.65rem", color: "#64748b" }}>KH voor de start</div><div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#f97316" }}>{Math.round(rdKhTotaal())}g</div></div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          <button onClick={() => setStap(5)} style={{ flex: 1, padding: "12px 0", background: "#1e293b", color: "#94a3b8", border: "1px solid #334155", borderRadius: 10, fontSize: "0.85rem", fontWeight: 700, cursor: "pointer" }}>← Raceplan</button>
          <button onClick={() => { setStap(0); setData({}); setClWaarden({}); setRdWaarden({}); setRapport("") }}
            style={{ flex: 1, padding: "12px 0", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 10, fontSize: "0.85rem", fontWeight: 700, cursor: "pointer" }}>
            🔄 Nieuw plan
          </button>
        </div>
      </div>
    )
  }

  const stapRenderers = [renderWelkom, renderProfiel, renderWedstrijd, renderCarboloading, renderRacedag, renderRaceplan, renderSamenvatting]

  return (
    <div style={s}>
      <div style={{ background: "linear-gradient(135deg,#1e293b,#0f172a)", borderRadius: 16, padding: "18px 22px", marginBottom: 20, borderLeft: "5px solid #f97316", display: "flex", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: "0.68rem", color: "#f97316", fontWeight: 800, letterSpacing: 2 }}>🏁 RACE NUTRITION PLAN</div>
          <div style={{ fontSize: "1.1rem", fontWeight: 900, color: "#f8fafc", marginTop: 2 }}>{STAP_LABELS[stap]}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "0.68rem", color: "#64748b" }}>Atleet</div>
          <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f8fafc" }}>{atleetNaam || user?.email?.split("@")[0] || "—"}</div>
        </div>
      </div>
      <ProgressBar stap={stap} />
      {(stapRenderers[stap] || renderWelkom)()}
    </div>
  )
}
