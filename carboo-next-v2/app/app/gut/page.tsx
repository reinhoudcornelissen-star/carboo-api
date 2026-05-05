"use client"
import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"

const API = "https://carboo-api.onrender.com"

// ─── CONSTANTEN ──────────────────────────────────────────────────────────────
const SPORTEN = ["Fietsen", "Lopen", "Triatlon", "Duatlon", "Crossduatlon"]
const NIVEAUS = ["Recreant", "Competitief", "Professioneel"]
const ERVARINGEN = ["Beginner", "Gevorderd", "Ervaren"]
const INTENSITEITEN = ["Laag", "Matig", "Hoog", "Race-intensiteit"]
const CATEGORIEEN = ["gel", "sportdrank", "vast", "supplement", "anders"]

const WEEK_INTENSITEIT: Record<number, string> = {
  1: "Laag", 2: "Laag", 3: "Matig", 4: "Matig", 5: "Hoog", 6: "Race-intensiteit"
}
const WEEK_MIN_DUUR: Record<number, number> = {
  1: 60, 2: 60, 3: 90, 4: 90, 5: 120, 6: 120
}

const RATIO_UITLEG: Record<string, string> = {
  "Geen vereiste — glucose/maltodextrine volstaat": "Onder 60g/uur kan je enkel glucose of maltodextrine gebruiken.",
  "2:1 glucose:fructose": "Boven 60g/uur raakt SGLT1 verzadigd. Gebruik 2 delen glucose/maltodextrine op 1 deel fructose.",
  "1:0.8 glucose:fructose": "Boven 90g/uur is 1:0.8 optimaal. Enkel haalbaar na gerichte darmaanpassing (Rowlands et al.).",
}

// ─── TYPES ───────────────────────────────────────────────────────────────────
interface Protocol {
  sport: string; wedstrijd: string; niveau: string; ervaring: string
  wedstrijd_datum: string; trainingen_per_week: number
  startdosis_g_uur: number; max_dosis_g_uur: number; week_huidig: number
}
interface Product {
  naam: string; categorie: string; kh_gram: number; hoeveelheid_ml_g: number
  tijdstip_min: number; gi_totaal: number; gi_misselijkheid: number
  gi_krampen: number; gi_opgeblazen: number; gi_diarree: number
}
interface Sessie {
  id: string; datum: string; sport: string; duur_min: number; intensiteit: string
  week_nummer: number; energie_score: number; prestatie_score: number
  notitie: string; wil_doorgaan: boolean; dosis_aanpassen: string
  producten: (Product & { id?: string })[]
}
interface WinkelmandjeItem {
  id: string; naam: string; categorie: string; kh_gram: number
  max_kh_uur: number; gem_gi_score: number; aantal_sessies: number; sport: string
}
interface Advies {
  week: number; dosis_huidig: number; ratio_advies: string
  product_adviezen: { product: string; type: string; bericht: string; gem_gi: number; n: number }[]
  protocol: Protocol
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function GiStepper({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{label}</span>
        <span style={{ fontSize: "0.72rem", color: value <= 2 ? "#22c55e" : value <= 4 ? "#fbbf24" : "#ef4444", fontWeight: 700 }}>
          {value}/10 {value === 0 ? "✓" : value <= 2 ? "licht" : value <= 4 ? "matig" : "ernstig"}
        </span>
      </div>
      <div style={{ display: "flex", gap: 3 }}>
        {Array.from({ length: 11 }, (_, i) => (
          <button key={i} onClick={() => onChange(i)}
            style={{ flex: 1, height: 22, border: "none", borderRadius: 3, cursor: "pointer",
              background: i <= value ? (value <= 2 ? "#22c55e" : value <= 4 ? "#fbbf24" : "#ef4444") : "#1e293b",
              fontSize: "0.6rem", color: i <= value ? "#0c0c0c" : "#475569", fontWeight: i === value ? 700 : 400 }}>
            {i}
          </button>
        ))}
      </div>
    </div>
  )
}

function ScoreStepper({ label, value, onChange, kleurInvers = false }: {
  label: string; value: number; onChange: (v: number) => void; kleurInvers?: boolean
}) {
  const kleur = kleurInvers
    ? (value >= 7 ? "#22c55e" : value >= 4 ? "#fbbf24" : "#ef4444")
    : (value <= 3 ? "#ef4444" : value <= 6 ? "#fbbf24" : "#22c55e")
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{label}</span>
        <span style={{ fontSize: "0.75rem", color: kleur, fontWeight: 700 }}>{value}/10</span>
      </div>
      <input type="range" min={0} max={10} step={1} value={value}
        onChange={e => onChange(parseInt(e.target.value))}
        style={{ width: "100%", accentColor: kleur }} />
    </div>
  )
}

function ProgressBalk({ waarde, max, kleur }: { waarde: number; max: number; kleur: string }) {
  const pct = Math.min(100, Math.round(waarde / max * 100))
  return (
    <div style={{ background: "#0f172a", borderRadius: 4, height: 8, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: kleur, borderRadius: 4, transition: "width 0.3s" }} />
    </div>
  )
}

const card = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 12 }
const pill = (actief: boolean, kleur = "#f97316") => ({
  padding: "6px 14px", borderRadius: 20, fontSize: "0.75rem", fontWeight: 600 as const, cursor: "pointer" as const,
  border: "none", background: actief ? `rgba(${kleur === "#f97316" ? "249,115,22" : kleur === "#22c55e" ? "34,197,94" : "59,130,246"},0.15)` : "#1e293b",
  color: actief ? kleur : "#64748b"
})

// ─── HOOFDCOMPONENT ───────────────────────────────────────────────────────────
export default function GutPage() {
  const { token } = useAuth()
  const [tab, setTab] = useState<"protocol" | "log" | "sessies" | "winkelmandje" | "advies">("protocol")
  const [protocol, setProtocol] = useState<Protocol | null>(null)
  const [sessies, setSessies] = useState<Sessie[]>([])
  const [winkelmandje, setWinkelmandje] = useState<WinkelmandjeItem[]>([])
  const [advies, setAdvies] = useState<Advies | null>(null)
  const [laden, setLaden] = useState(true)
  const [opslaan, setOpslaan] = useState(false)
  const [melding, setMelding] = useState("")

  // Protocol formulier
  const [sport, setSport] = useState("Fietsen")
  const [wedstrijd, setWedstrijd] = useState("")
  const [niveau, setNiveau] = useState("Recreant")
  const [ervaring, setErvaring] = useState("Beginner")
  const [wedstrijdDatum, setWedstrijdDatum] = useState("")
  const [trainingenPerWeek, setTrainingenPerWeek] = useState(1)
  const [dosisPreview, setDosisPreview] = useState<any>(null)

  // Sessie log formulier
  const [logDatum, setLogDatum] = useState(new Date().toISOString().slice(0, 10))
  const [logDuur, setLogDuur] = useState(90)
  const [logIntensiteit, setLogIntensiteit] = useState("Laag")
  const [logWeek, setLogWeek] = useState(1)
  const [logTemp, setLogTemp] = useState(18)
  const [logVochtigheid, setLogVochtigheid] = useState(50)
  const [logNotitie, setLogNotitie] = useState("")
  const [logEnergie, setLogEnergie] = useState(7)
  const [logPrestatie, setLogPrestatie] = useState(7)
  const [logWilDoorgaan, setLogWilDoorgaan] = useState<boolean | null>(null)
  const [logDosisAanpassen, setLogDosisAanpassen] = useState("Zelfde")
  const [logProducten, setLogProducten] = useState<Partial<Product>[]>([
    { naam: "", categorie: "gel", kh_gram: 22, hoeveelheid_ml_g: 60, tijdstip_min: 20,
      gi_totaal: 0, gi_misselijkheid: 0, gi_krampen: 0, gi_opgeblazen: 0, gi_diarree: 0 }
  ])

  useEffect(() => {
    if (!token) return
    laadAlles()
  }, [token])

  useEffect(() => {
    // Bereken dosis preview lokaal
    const basis = { Beginner: 20, Gevorderd: 40, Ervaren: 60 }[ervaring] || 20
    const sportFactor = sport === "Lopen" ? 0.8 : 1.0
    const start = Math.max(20, Math.round(basis * sportFactor / 5) * 5)
    const maxMap = { Recreant: 60, Competitief: 90, Professioneel: 120 }
    let max = (maxMap[niveau as keyof typeof maxMap] || 60)
    if (sport === "Lopen") max = Math.round(max * 0.85 / 5) * 5
    setDosisPreview({
      startdosis: start, max_dosis: max,
      wk12: start, wk34: Math.min(start + 15, max), wk56: Math.min(start + 30, max),
      ratio: start < 60 ? "Geen vereiste" : start < 90 ? "2:1 glucose:fructose" : "1:0.8 glucose:fructose"
    })
  }, [sport, niveau, ervaring])

  async function laadAlles() {
    setLaden(true)
    try {
      const headers = { Authorization: `Bearer ${token}` }
      const [pRes, sRes, wRes, aRes] = await Promise.all([
        fetch(`${API}/api/gut/protocol`, { headers }),
        fetch(`${API}/api/gut/sessies`, { headers }),
        fetch(`${API}/api/gut/winkelmandje`, { headers }),
        fetch(`${API}/api/gut/advies`, { headers }),
      ])
      const [pData, sData, wData, aData] = await Promise.all([pRes.json(), sRes.json(), wRes.json(), aRes.json()])
      if (pData.protocol) {
        setProtocol(pData.protocol)
        setSport(pData.protocol.sport)
        setNiveau(pData.protocol.niveau)
        setErvaring(pData.protocol.ervaring)
        setWedstrijd(pData.protocol.wedstrijd || "")
        setWedstrijdDatum(pData.protocol.wedstrijd_datum || "")
        setTrainingenPerWeek(pData.protocol.trainingen_per_week || 1)
        setLogWeek(pData.protocol.week_huidig || 1)
        setLogIntensiteit(WEEK_INTENSITEIT[pData.protocol.week_huidig || 1] || "Laag")
      }
      setSessies(sData.sessies || [])
      setWinkelmandje(wData.items || [])
      if (aData.protocol) setAdvies(aData)
    } catch {}
    setLaden(false)
  }

  async function slaProtocolOp() {
    setOpslaan(true)
    try {
      await fetch(`${API}/api/gut/protocol`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ sport, wedstrijd, niveau, ervaring, wedstrijd_datum: wedstrijdDatum || null, trainingen_per_week: trainingenPerWeek })
      })
      setMelding("✓ Protocol opgeslagen!")
      await laadAlles()
      setTimeout(() => setMelding(""), 3000)
    } catch { setMelding("Fout bij opslaan.") }
    setOpslaan(false)
  }

  async function slaSessionOp() {
    if (!logDuur || logDuur < 60) { setMelding("⚠️ Training moet minstens 60 minuten duren voor een valide sessie."); return }
    if (logWilDoorgaan === null) { setMelding("⚠️ Geef aan of je wil doorgaan met dit product."); return }
    setOpslaan(true)
    try {
      const producten = logProducten.filter(p => p.naam).map(p => ({
        naam: p.naam || "", categorie: p.categorie || "gel", kh_gram: p.kh_gram || 0,
        hoeveelheid_ml_g: p.hoeveelheid_ml_g || 0, tijdstip_min: p.tijdstip_min || 0,
        gi_totaal: p.gi_totaal || 0, gi_misselijkheid: p.gi_misselijkheid || 0,
        gi_krampen: p.gi_krampen || 0, gi_opgeblazen: p.gi_opgeblazen || 0, gi_diarree: p.gi_diarree || 0,
      }))
      await fetch(`${API}/api/gut/sessies`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          datum: logDatum, sport, duur_min: logDuur, intensiteit: logIntensiteit,
          week_nummer: logWeek, temp_c: logTemp, vochtigheid_pct: logVochtigheid,
          notitie: logNotitie, energie_score: logEnergie, prestatie_score: logPrestatie,
          wil_doorgaan: logWilDoorgaan, dosis_aanpassen: logDosisAanpassen, producten
        })
      })
      setMelding("✓ Sessie opgeslagen!")
      setLogNotitie(""); setLogWilDoorgaan(null); setLogDosisAanpassen("Zelfde")
      setLogProducten([{ naam: "", categorie: "gel", kh_gram: 22, hoeveelheid_ml_g: 60,
        tijdstip_min: 20, gi_totaal: 0, gi_misselijkheid: 0, gi_krampen: 0, gi_opgeblazen: 0, gi_diarree: 0 }])
      await laadAlles()
      setTab("sessies")
      setTimeout(() => setMelding(""), 3000)
    } catch { setMelding("Fout bij opslaan sessie.") }
    setOpslaan(false)
  }

  async function voegToeWinkelmandje(product: Partial<Product>, sessie: Sessie) {
    try {
      const alleGi = sessies.flatMap(s => s.producten).filter(p => p.naam === product.naam).map(p => p.gi_totaal || 0)
      const gemGi = alleGi.length ? alleGi.reduce((a, b) => a + b, 0) / alleGi.length : product.gi_totaal || 0
      const maxKh = Math.max(...sessies.flatMap(s => s.producten).filter(p => p.naam === product.naam).map(p => p.kh_gram || 0))
      await fetch(`${API}/api/gut/winkelmandje`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          naam: product.naam, categorie: product.categorie, kh_gram: product.kh_gram,
          max_kh_uur: maxKh, gem_gi_score: Math.round(gemGi * 10) / 10,
          aantal_sessies: alleGi.length, sport
        })
      })
      setMelding(`✓ ${product.naam} toegevoegd aan winkelmandje!`)
      await laadAlles()
      setTimeout(() => setMelding(""), 3000)
    } catch {}
  }

  async function verwijderWinkelmandjeItem(id: string) {
    await fetch(`${API}/api/gut/winkelmandje/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
    await laadAlles()
  }

  async function verwijderSessie(id: string) {
    await fetch(`${API}/api/gut/sessies/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
    await laadAlles()
  }

  const s = { background: "#141414", minHeight: "100vh", padding: "20px 16px", fontFamily: "system-ui, sans-serif", color: "#f5f3ef" }

  function berekenKhPerUur(sessie: Sessie): number {
    const totaalKh = sessie.producten.reduce((a, p) => a + (p.kh_gram || 0), 0)
    return sessie.duur_min > 0 ? Math.round(totaalKh / sessie.duur_min * 60) : 0
  }

  if (laden) return <div style={s}><div style={{ textAlign: "center", padding: 60, color: "#f97316" }}>⏳ Laden...</div></div>

  return (
    <div style={s}>
      {/* Header */}
      <div style={{ background: "linear-gradient(135deg,#1e293b,#0f172a)", borderRadius: 16, padding: "18px 22px", marginBottom: 20, borderLeft: "5px solid #22c55e" }}>
        <div style={{ fontSize: "0.68rem", color: "#22c55e", fontWeight: 800, letterSpacing: 2, marginBottom: 4 }}>🍽️ TRAIN THE GUT</div>
        <div style={{ fontSize: "0.88rem", color: "#94a3b8" }}>
          Train je darmen systematisch voor optimale KH-opname tijdens wedstrijden.
        </div>
        {protocol && (
          <div style={{ display: "flex", gap: 12, marginTop: 10, flexWrap: "wrap" as const }}>
            <span style={{ fontSize: "0.72rem", color: "#22c55e", background: "rgba(34,197,94,0.1)", padding: "3px 10px", borderRadius: 10, border: "1px solid rgba(34,197,94,0.2)" }}>
              Week {protocol.week_huidig}/6
            </span>
            <span style={{ fontSize: "0.72rem", color: "#60a5fa", background: "rgba(59,130,246,0.1)", padding: "3px 10px", borderRadius: 10, border: "1px solid rgba(59,130,246,0.2)" }}>
              {protocol.sport} · {protocol.niveau}
            </span>
            <span style={{ fontSize: "0.72rem", color: "#f97316", background: "rgba(249,115,22,0.1)", padding: "3px 10px", borderRadius: 10, border: "1px solid rgba(249,115,22,0.2)" }}>
              Doel: {advies?.dosis_huidig || protocol.startdosis_g_uur}g KH/uur
            </span>
            <span style={{ fontSize: "0.72rem", color: "#a78bfa", background: "rgba(167,139,250,0.1)", padding: "3px 10px", borderRadius: 10, border: "1px solid rgba(167,139,250,0.2)" }}>
              🛒 {winkelmandje.length} goedgekeurde producten
            </span>
          </div>
        )}
      </div>

      {/* Melding */}
      {melding && (
        <div style={{ background: melding.startsWith("⚠️") ? "rgba(251,191,36,0.1)" : "rgba(34,197,94,0.1)", border: `1px solid ${melding.startsWith("⚠️") ? "#fbbf24" : "#22c55e"}`, borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: "0.82rem", color: melding.startsWith("⚠️") ? "#fbbf24" : "#22c55e" }}>
          {melding}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 6, marginBottom: 20, flexWrap: "wrap" as const }}>
        {[
          { key: "protocol", label: "⚙️ Protocol" },
          { key: "log", label: "📝 Sessie loggen" },
          { key: "sessies", label: `📊 Sessies (${sessies.length})` },
          { key: "winkelmandje", label: `🛒 Winkelmandje (${winkelmandje.length})` },
          { key: "advies", label: "💡 Advies" },
        ].map(t => (
          <button key={t.key} style={pill(tab === t.key, "#22c55e")} onClick={() => setTab(t.key as any)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── TAB: PROTOCOL ── */}
      {tab === "protocol" && (
        <div>
          <div style={card}>
            <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 16 }}>STAP 1 — JOUW PROFIEL</div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
              <div>
                <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>SPORT</div>
                <select value={sport} onChange={e => setSport(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }}>
                  {SPORTEN.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>NIVEAU</div>
                <select value={niveau} onChange={e => setNiveau(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }}>
                  {NIVEAUS.map(n => <option key={n}>{n}</option>)}
                </select>
              </div>
            </div>

            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>ERVARING MET SPORTVOEDING</div>
              <div style={{ display: "flex", gap: 8 }}>
                {ERVARINGEN.map(e => (
                  <button key={e} style={{ ...pill(ervaring === e, "#22c55e"), flex: 1 }} onClick={() => setErvaring(e)}>{e}</button>
                ))}
              </div>
              <div style={{ fontSize: "0.68rem", color: "#475569", marginTop: 6 }}>
                {ervaring === "Beginner" ? "Je hebt nog nooit systematisch getest met sportvoeding tijdens training." :
                 ervaring === "Gevorderd" ? "Je gebruikt soms gels of sportdrank, maar niet systematisch." :
                 "Je test regelmatig producten en kent je eigen tolerantie goed."}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
              <div>
                <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>DOELWEDSTRIJD (optioneel)</div>
                <input value={wedstrijd} onChange={e => setWedstrijd(e.target.value)} placeholder="bv. Ironman Frankfurt"
                  style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
              </div>
              <div>
                <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>DATUM WEDSTRIJD</div>
                <input type="date" value={wedstrijdDatum} onChange={e => setWedstrijdDatum(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 8, fontWeight: 700 }}>
                AANTAL LANGE DUURTRAININGEN PER WEEK WAARBIJ JE KAN TESTEN
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {[1, 2, 3].map(n => (
                  <button key={n} style={{ ...pill(trainingenPerWeek === n, "#22c55e"), flex: 1 }} onClick={() => setTrainingenPerWeek(n)}>
                    {n}×/week
                  </button>
                ))}
              </div>
              <div style={{ fontSize: "0.68rem", color: "#475569", marginTop: 6 }}>
                Enkel lange duurtrainingen ≥60 min tellen mee. Geen druk — 1×/week is prima.
              </div>
            </div>
          </div>

          {/* Dosis preview */}
          {dosisPreview && (
            <div style={{ ...card, border: "1px solid rgba(34,197,94,0.3)" }}>
              <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 16 }}>JOUW GEPERSONALISEERD 6-WEKEN PROTOCOL</div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 16 }}>
                {[
                  { label: "Week 1–2", dosis: dosisPreview.wk12, sub: "Lage intensiteit · ≥60 min", kleur: "#22c55e" },
                  { label: "Week 3–4", dosis: dosisPreview.wk34, sub: "Matige intensiteit · ≥90 min", kleur: "#f97316" },
                  { label: "Week 5–6", dosis: dosisPreview.wk56, sub: "Race-intensiteit · ≥120 min", kleur: "#ef4444" },
                ].map(w => (
                  <div key={w.label} style={{ background: "#141414", borderRadius: 10, padding: 12, textAlign: "center" as const, borderTop: `3px solid ${w.kleur}` }}>
                    <div style={{ fontSize: "0.6rem", color: "#64748b", marginBottom: 4 }}>{w.label}</div>
                    <div style={{ fontSize: "1.2rem", fontWeight: 900, color: w.kleur }}>{w.dosis}g</div>
                    <div style={{ fontSize: "0.6rem", color: "#475569" }}>KH/uur</div>
                    <div style={{ fontSize: "0.6rem", color: "#334155", marginTop: 4 }}>{w.sub}</div>
                  </div>
                ))}
              </div>

              <div style={{ background: "rgba(167,139,250,0.08)", border: "1px solid rgba(167,139,250,0.2)", borderRadius: 8, padding: "10px 14px", marginBottom: 12 }}>
                <div style={{ fontSize: "0.65rem", color: "#a78bfa", fontWeight: 700, marginBottom: 4 }}>💊 GLUCOSE:FRUCTOSE RATIO ADVIES</div>
                <div style={{ fontSize: "0.78rem", color: "#c4b5fd" }}>{dosisPreview.ratio}</div>
                <div style={{ fontSize: "0.68rem", color: "#7c3aed", marginTop: 4 }}>
                  {RATIO_UITLEG[dosisPreview.ratio] || ""}
                </div>
              </div>

              {sport === "Lopen" && (
                <div style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.2)", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: "0.78rem", color: "#fbbf24" }}>
                  🏃 <b>Lopen:</b> GI-gevoeliger door impact. Doses zijn 15–20% lager dan fietsen. Kies vloeibare bronnen boven vast voedsel.
                </div>
              )}

              <div style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: 8, padding: "10px 14px", fontSize: "0.78rem", color: "#93c5fd" }}>
                📊 Maximum voor jouw niveau: <b>{dosisPreview.max_dosis}g KH/uur</b> — enkel haalbaar na volledige darmaanpassing over 6 weken.
              </div>
            </div>
          )}

          <button onClick={slaProtocolOp} disabled={opslaan}
            style={{ width: "100%", padding: "14px 0", background: "#22c55e", color: "#0c0c0c", border: "none", borderRadius: 10, fontSize: "0.95rem", fontWeight: 900, cursor: "pointer" }}>
            {opslaan ? "⏳ Opslaan..." : protocol ? "✓ Protocol bijwerken" : "✓ Protocol starten"}
          </button>
        </div>
      )}

      {/* ── TAB: SESSIE LOGGEN ── */}
      {tab === "log" && (
        <div>
          {!protocol && (
            <div style={{ ...card, border: "1px solid rgba(251,191,36,0.3)", color: "#fbbf24", textAlign: "center" as const, padding: 24 }}>
              ⚠️ Stel eerst je protocol in voor je een sessie logt.
              <button onClick={() => setTab("protocol")} style={{ display: "block", margin: "10px auto 0", padding: "8px 20px", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 700 }}>
                → Naar Protocol
              </button>
            </div>
          )}

          {protocol && (
            <>
              {/* Sessie basisinfo */}
              <div style={card}>
                <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 14 }}>TRAININGSSESSIE</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                  <div>
                    <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>DATUM</div>
                    <input type="date" value={logDatum} onChange={e => setLogDatum(e.target.value)}
                      style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>DUUR (min) — min. 60</div>
                    <input type="number" min={60} max={600} value={logDuur} onChange={e => setLogDuur(parseInt(e.target.value) || 60)}
                      style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: `1px solid ${logDuur < 60 ? "#ef4444" : "#2a2a2a"}`, borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
                    {logDuur < 60 && <div style={{ fontSize: "0.68rem", color: "#ef4444", marginTop: 3 }}>Minstens 60 min vereist</div>}
                  </div>
                </div>

                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 6, fontWeight: 700 }}>PROTOCOL WEEK</div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" as const }}>
                    {[1, 2, 3, 4, 5, 6].map(w => (
                      <button key={w} onClick={() => { setLogWeek(w); setLogIntensiteit(WEEK_INTENSITEIT[w]) }}
                        style={{ ...pill(logWeek === w, "#22c55e"), minWidth: 36 }}>
                        Wk {w}
                      </button>
                    ))}
                  </div>
                  {logWeek && (
                    <div style={{ marginTop: 8, fontSize: "0.72rem", color: "#64748b" }}>
                      Week {logWeek}: <span style={{ color: "#94a3b8" }}>{WEEK_INTENSITEIT[logWeek]} intensiteit · min. {WEEK_MIN_DUUR[logWeek]} min</span>
                    </div>
                  )}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <div>
                    <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>TEMP (°C)</div>
                    <input type="number" value={logTemp} onChange={e => setLogTemp(parseInt(e.target.value) || 18)}
                      style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>VOCHTIGHEID (%)</div>
                    <input type="number" value={logVochtigheid} onChange={e => setLogVochtigheid(parseInt(e.target.value) || 50)}
                      style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
                  </div>
                </div>
              </div>

              {/* Producten */}
              <div style={card}>
                <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 14 }}>GETESTE PRODUCTEN</div>

                {logProducten.map((prod, idx) => (
                  <div key={idx} style={{ background: "#141414", borderRadius: 10, padding: 14, marginBottom: 10, border: "1px solid #1e293b" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <div style={{ fontSize: "0.75rem", color: "#f97316", fontWeight: 700 }}>Product {idx + 1}</div>
                      {logProducten.length > 1 && (
                        <button onClick={() => setLogProducten(logProducten.filter((_, i) => i !== idx))}
                          style={{ background: "none", border: "none", color: "#475569", cursor: "pointer" }}>✕</button>
                      )}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
                      <div>
                        <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3 }}>NAAM PRODUCT</div>
                        <input value={prod.naam || ""} onChange={e => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, naam: e.target.value } : p))}
                          placeholder="bv. SIS Go Gel"
                          style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none" }} />
                      </div>
                      <div>
                        <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3 }}>CATEGORIE</div>
                        <select value={prod.categorie || "gel"} onChange={e => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, categorie: e.target.value } : p))}
                          style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none" }}>
                          {CATEGORIEEN.map(c => <option key={c}>{c}</option>)}
                        </select>
                      </div>
                      <div>
                        <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3 }}>KH (gram)</div>
                        <input type="number" value={prod.kh_gram || 0} onChange={e => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, kh_gram: parseInt(e.target.value) || 0 } : p))}
                          style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f97316", fontSize: "0.82rem", outline: "none" }} />
                      </div>
                      <div>
                        <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3 }}>TIJDSTIP (min na start)</div>
                        <input type="number" value={prod.tijdstip_min || 0} onChange={e => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, tijdstip_min: parseInt(e.target.value) || 0 } : p))}
                          style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none" }} />
                      </div>
                    </div>

                    {/* GI scores */}
                    <div style={{ borderTop: "1px solid #1e293b", paddingTop: 10 }}>
                      <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 8, fontWeight: 700 }}>GI KLACHTEN — 0 = geen · 10 = ernstig</div>
                      <GiStepper label="Totaal GI gevoel" value={prod.gi_totaal || 0}
                        onChange={v => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, gi_totaal: v } : p))} />
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                        <GiStepper label="Misselijkheid" value={prod.gi_misselijkheid || 0}
                          onChange={v => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, gi_misselijkheid: v } : p))} />
                        <GiStepper label="Krampen" value={prod.gi_krampen || 0}
                          onChange={v => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, gi_krampen: v } : p))} />
                        <GiStepper label="Opgeblazen" value={prod.gi_opgeblazen || 0}
                          onChange={v => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, gi_opgeblazen: v } : p))} />
                        <GiStepper label="Diarree/urgentie" value={prod.gi_diarree || 0}
                          onChange={v => setLogProducten(logProducten.map((p, i) => i === idx ? { ...p, gi_diarree: v } : p))} />
                      </div>
                    </div>

                    {/* Ratio waarschuwing */}
                    {(prod.kh_gram || 0) >= 60 && (
                      <div style={{ marginTop: 8, background: "rgba(167,139,250,0.08)", border: "1px solid rgba(167,139,250,0.2)", borderRadius: 6, padding: "8px 10px", fontSize: "0.72rem", color: "#a78bfa" }}>
                        💊 Bij {prod.kh_gram}g KH: gebruik {(prod.kh_gram || 0) >= 90 ? "1:0.8" : "2:1"} glucose:fructose ratio
                      </div>
                    )}
                  </div>
                ))}

                <button onClick={() => setLogProducten([...logProducten, { naam: "", categorie: "gel", kh_gram: 22, hoeveelheid_ml_g: 60, tijdstip_min: 20, gi_totaal: 0, gi_misselijkheid: 0, gi_krampen: 0, gi_opgeblazen: 0, gi_diarree: 0 }])}
                  style={{ width: "100%", padding: "10px 0", background: "rgba(34,197,94,0.08)", border: "1px dashed rgba(34,197,94,0.3)", borderRadius: 8, color: "#22c55e", cursor: "pointer", fontSize: "0.82rem" }}>
                  ➕ Nog een product toevoegen
                </button>
              </div>

              {/* Evaluatie */}
              <div style={card}>
                <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 14 }}>EVALUATIE NA DE SESSIE</div>
                <ScoreStepper label="Energieniveau tijdens training (0=uitgeput · 10=topvorm)" value={logEnergie} onChange={setLogEnergie} kleurInvers />
                <ScoreStepper label="Prestatiebeoordeling (0=slecht · 10=uitstekend)" value={logPrestatie} onChange={setLogPrestatie} kleurInvers />

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 8, fontWeight: 700 }}>WIL JE VERDER MET DIT PRODUCT/DEZE DOSIS?</div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button style={{ ...pill(logWilDoorgaan === true, "#22c55e"), flex: 1 }} onClick={() => setLogWilDoorgaan(true)}>✓ Ja, doorgaan</button>
                    <button style={{ ...pill(logWilDoorgaan === false, "#ef4444"), flex: 1, color: logWilDoorgaan === false ? "#ef4444" : "#64748b" }} onClick={() => setLogWilDoorgaan(false)}>✕ Nee, stoppen</button>
                  </div>
                </div>

                {logWilDoorgaan && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 8, fontWeight: 700 }}>DOSIS VOOR VOLGENDE SESSIE</div>
                    <div style={{ display: "flex", gap: 8 }}>
                      {["Zelfde", "Hoger", "Lager"].map(d => (
                        <button key={d} style={{ ...pill(logDosisAanpassen === d, "#f97316"), flex: 1 }} onClick={() => setLogDosisAanpassen(d)}>{d}</button>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>NOTITIE (optioneel)</div>
                  <textarea value={logNotitie} onChange={e => setLogNotitie(e.target.value)} rows={3}
                    placeholder="Wat viel op? Weer, maaggevoel, bijzonderheden..."
                    style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.85rem", outline: "none", resize: "none" as const }} />
                </div>
              </div>

              <button onClick={slaSessionOp} disabled={opslaan}
                style={{ width: "100%", padding: "14px 0", background: "#22c55e", color: "#0c0c0c", border: "none", borderRadius: 10, fontSize: "0.95rem", fontWeight: 900, cursor: "pointer" }}>
                {opslaan ? "⏳ Opslaan..." : "✓ Sessie opslaan"}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── TAB: SESSIES ── */}
      {tab === "sessies" && (
        <div>
          {sessies.length === 0 ? (
            <div style={{ ...card, textAlign: "center" as const, padding: 32 }}>
              <div style={{ fontSize: "2rem", marginBottom: 12 }}>📭</div>
              <div style={{ color: "#94a3b8", marginBottom: 8 }}>Nog geen sessies gelogd</div>
              <button onClick={() => setTab("log")} style={{ padding: "10px 24px", background: "#22c55e", color: "#0c0c0c", border: "none", borderRadius: 10, cursor: "pointer", fontWeight: 700, fontSize: "0.85rem" }}>
                → Log eerste sessie
              </button>
            </div>
          ) : (
            sessies.map(sessie => {
              const khUur = berekenKhPerUur(sessie)
              const gemGi = sessie.producten.length
                ? Math.round(sessie.producten.reduce((a, p) => a + (p.gi_totaal || 0), 0) / sessie.producten.length * 10) / 10
                : 0
              const giKleur = gemGi <= 2 ? "#22c55e" : gemGi <= 4 ? "#fbbf24" : "#ef4444"
              return (
                <div key={sessie.id} style={card}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#f5f3ef", marginBottom: 3 }}>
                        Week {sessie.week_nummer} · {new Date(sessie.datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "short", day: "numeric", month: "long" })}
                      </div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" as const }}>
                        <span style={{ fontSize: "0.68rem", color: "#60a5fa" }}>{sessie.duur_min} min</span>
                        <span style={{ fontSize: "0.68rem", color: "#64748b" }}>· {sessie.intensiteit}</span>
                        <span style={{ fontSize: "0.68rem", color: "#f97316" }}>· {khUur}g KH/uur</span>
                        <span style={{ fontSize: "0.68rem", color: giKleur }}>· GI {gemGi}/10</span>
                      </div>
                    </div>
                    <button onClick={() => verwijderSessie(sessie.id)}
                      style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "1rem" }}>🗑</button>
                  </div>

                  {/* Producten */}
                  {sessie.producten.map((p, i) => {
                    const gi = p.gi_totaal || 0
                    const giK = gi <= 2 ? "#22c55e" : gi <= 4 ? "#fbbf24" : "#ef4444"
                    const inMandje = winkelmandje.some(w => w.naam === p.naam)
                    return (
                      <div key={i} style={{ background: "#141414", borderRadius: 8, padding: "10px 12px", marginBottom: 6, display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: "0.82rem", color: "#f5f3ef", fontWeight: 600 }}>{p.naam}</div>
                          <div style={{ fontSize: "0.68rem", color: "#64748b" }}>{p.kh_gram}g KH · {p.categorie} · {p.tijdstip_min}min na start</div>
                          <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                            <span style={{ fontSize: "0.65rem", color: giK, background: `${giK}22`, padding: "2px 6px", borderRadius: 4 }}>GI {gi}/10</span>
                            {p.gi_misselijkheid > 0 && <span style={{ fontSize: "0.62rem", color: "#64748b" }}>misselijk:{p.gi_misselijkheid}</span>}
                            {p.gi_krampen > 0 && <span style={{ fontSize: "0.62rem", color: "#64748b" }}>krampen:{p.gi_krampen}</span>}
                          </div>
                        </div>
                        {!inMandje && sessie.wil_doorgaan && gi <= 3 && (
                          <button onClick={() => voegToeWinkelmandje(p, sessie)}
                            style={{ padding: "6px 12px", background: "rgba(34,197,94,0.15)", border: "1px solid rgba(34,197,94,0.3)", borderRadius: 8, color: "#22c55e", cursor: "pointer", fontSize: "0.72rem", fontWeight: 700, whiteSpace: "nowrap" as const }}>
                            🛒 Winkelmandje
                          </button>
                        )}
                        {inMandje && <span style={{ fontSize: "0.68rem", color: "#22c55e" }}>✓ in mandje</span>}
                      </div>
                    )
                  })}

                  {/* Bevraging resultaten */}
                  <div style={{ display: "flex", gap: 10, marginTop: 8, fontSize: "0.7rem", color: "#475569" }}>
                    <span>Energie: <b style={{ color: "#60a5fa" }}>{sessie.energie_score}/10</b></span>
                    <span>Prestatie: <b style={{ color: "#60a5fa" }}>{sessie.prestatie_score}/10</b></span>
                    <span style={{ color: sessie.wil_doorgaan ? "#22c55e" : "#ef4444" }}>
                      {sessie.wil_doorgaan ? "✓ Doorgaan" : "✕ Stoppen"} · {sessie.dosis_aanpassen}
                    </span>
                  </div>
                  {sessie.notitie && <div style={{ marginTop: 6, fontSize: "0.72rem", color: "#475569", fontStyle: "italic" }}>"{sessie.notitie}"</div>}
                </div>
              )
            })
          )}
        </div>
      )}

      {/* ── TAB: WINKELMANDJE ── */}
      {tab === "winkelmandje" && (
        <div>
          <div style={{ ...card, background: "rgba(34,197,94,0.05)", border: "1px solid rgba(34,197,94,0.2)", marginBottom: 16 }}>
            <div style={{ fontSize: "0.75rem", color: "#22c55e", marginBottom: 4 }}>
              🛒 <b>{winkelmandje.length} goedgekeurde producten</b>
            </div>
            <div style={{ fontSize: "0.72rem", color: "#475569" }}>
              Deze producten zijn door jou persoonlijk getest en goedgekeurd. Ze zijn automatisch beschikbaar als productpool in je Race Nutrition Plan.
            </div>
          </div>

          {winkelmandje.length === 0 ? (
            <div style={{ ...card, textAlign: "center" as const, padding: 32 }}>
              <div style={{ fontSize: "2rem", marginBottom: 12 }}>🛒</div>
              <div style={{ color: "#94a3b8", marginBottom: 8 }}>Nog geen producten in het winkelmandje</div>
              <div style={{ fontSize: "0.78rem", color: "#475569" }}>
                Log sessies en voeg producten met lage GI-score toe vanuit het Sessies tabblad.
              </div>
            </div>
          ) : (
            winkelmandje.map(item => {
              const giK = (item.gem_gi_score || 0) <= 2 ? "#22c55e" : (item.gem_gi_score || 0) <= 4 ? "#fbbf24" : "#ef4444"
              return (
                <div key={item.id} style={card}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f5f3ef", marginBottom: 6 }}>{item.naam}</div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" as const }}>
                        <span style={{ fontSize: "0.68rem", color: "#64748b", background: "#1e293b", padding: "2px 8px", borderRadius: 6 }}>{item.categorie}</span>
                        <span style={{ fontSize: "0.68rem", color: "#f97316", background: "rgba(249,115,22,0.1)", padding: "2px 8px", borderRadius: 6 }}>{item.kh_gram}g KH</span>
                        {item.max_kh_uur > 0 && <span style={{ fontSize: "0.68rem", color: "#60a5fa", background: "rgba(59,130,246,0.1)", padding: "2px 8px", borderRadius: 6 }}>max {item.max_kh_uur}g/uur</span>}
                        <span style={{ fontSize: "0.68rem", color: giK, background: `${giK}22`, padding: "2px 8px", borderRadius: 6 }}>GI {item.gem_gi_score}/10</span>
                        <span style={{ fontSize: "0.68rem", color: "#475569" }}>{item.aantal_sessies} sessie{item.aantal_sessies !== 1 ? "s" : ""}</span>
                      </div>
                      {(item.kh_gram || 0) >= 60 && (
                        <div style={{ marginTop: 8, fontSize: "0.68rem", color: "#a78bfa" }}>
                          💊 Aanbevolen ratio: {(item.kh_gram || 0) >= 90 ? "1:0.8 glucose:fructose" : "2:1 glucose:fructose"}
                        </div>
                      )}
                    </div>
                    <button onClick={() => verwijderWinkelmandjeItem(item.id)}
                      style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "1rem", marginLeft: 8 }}>🗑</button>
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <ProgressBalk waarde={item.gem_gi_score || 0} max={10} kleur={giK} />
                    <div style={{ fontSize: "0.62rem", color: "#334155", marginTop: 3, textAlign: "right" as const }}>GI score (lager is beter)</div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* ── TAB: ADVIES ── */}
      {tab === "advies" && (
        <div>
          {!advies?.protocol ? (
            <div style={{ ...card, textAlign: "center" as const, padding: 32, color: "#94a3b8" }}>
              Stel eerst je protocol in om advies te krijgen.
            </div>
          ) : (
            <>
              {/* Week overzicht */}
              <div style={{ ...card, border: "1px solid rgba(34,197,94,0.3)" }}>
                <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 14 }}>JOUW HUIDIGE WEEK</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 14 }}>
                  <div style={{ textAlign: "center" as const, background: "#141414", borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: "0.6rem", color: "#64748b" }}>WEEK</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 900, color: "#22c55e" }}>{advies.week}</div>
                    <div style={{ fontSize: "0.6rem", color: "#475569" }}>van 6</div>
                  </div>
                  <div style={{ textAlign: "center" as const, background: "#141414", borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: "0.6rem", color: "#64748b" }}>DOEL KH/UUR</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 900, color: "#f97316" }}>{advies.dosis_huidig}g</div>
                    <div style={{ fontSize: "0.6rem", color: "#475569" }}>per uur</div>
                  </div>
                  <div style={{ textAlign: "center" as const, background: "#141414", borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: "0.6rem", color: "#64748b" }}>SESSIES</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 900, color: "#60a5fa" }}>{sessies.filter(s => s.week_nummer === advies.week).length}</div>
                    <div style={{ fontSize: "0.6rem", color: "#475569" }}>deze week</div>
                  </div>
                </div>

                <div style={{ background: "rgba(167,139,250,0.08)", border: "1px solid rgba(167,139,250,0.2)", borderRadius: 8, padding: "10px 14px" }}>
                  <div style={{ fontSize: "0.65rem", color: "#a78bfa", fontWeight: 700, marginBottom: 4 }}>RATIO ADVIES DEZE WEEK</div>
                  <div style={{ fontSize: "0.82rem", color: "#c4b5fd" }}>{advies.ratio_advies}</div>
                  <div style={{ fontSize: "0.68rem", color: "#7c3aed", marginTop: 4 }}>
                    {RATIO_UITLEG[advies.ratio_advies] || ""}
                  </div>
                </div>
              </div>

              {/* 6 weken tijdlijn */}
              <div style={card}>
                <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 14 }}>6 WEKEN PROTOCOL TIJDLIJN</div>
                {[1,2,3,4,5,6].map(w => {
                  const startdosis = advies.protocol.startdosis_g_uur
                  const maxDosis = advies.protocol.max_dosis_g_uur
                  const wDosis = w <= 2 ? startdosis : w <= 4 ? Math.min(startdosis + 15, maxDosis) : Math.min(startdosis + 30, maxDosis)
                  const wSessies = sessies.filter(s => s.week_nummer === w)
                  const isHuidig = w === advies.week
                  const isVoltooid = w < advies.week
                  const kleur = isVoltooid ? "#22c55e" : isHuidig ? "#f97316" : "#334155"
                  return (
                    <div key={w} style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 8, padding: "8px 12px", background: isHuidig ? "rgba(249,115,22,0.05)" : "transparent", borderRadius: 8, border: isHuidig ? "1px solid rgba(249,115,22,0.2)" : "1px solid transparent" }}>
                      <div style={{ width: 28, height: 28, borderRadius: "50%", background: isVoltooid ? "#22c55e" : isHuidig ? "#f97316" : "#1e293b", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", fontWeight: 700, color: isVoltooid || isHuidig ? "#0c0c0c" : "#475569", flexShrink: 0 }}>
                        {isVoltooid ? "✓" : w}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "0.78rem", color: kleur, fontWeight: isHuidig ? 700 : 400 }}>
                          Week {w} — {w <= 2 ? "Lage intensiteit" : w <= 4 ? "Matige intensiteit" : "Race-intensiteit"}
                          {isHuidig && " ← nu"}
                        </div>
                        <div style={{ fontSize: "0.65rem", color: "#475569" }}>
                          {wDosis}g KH/uur · min. {WEEK_MIN_DUUR[w]} min · {wSessies.length} sessie{wSessies.length !== 1 ? "s" : ""} gelogd
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Product adviezen */}
              {advies.product_adviezen.length > 0 && (
                <div style={card}>
                  <div style={{ fontSize: "0.6rem", color: "#22c55e", letterSpacing: 3, marginBottom: 14 }}>ADVIES PER PRODUCT</div>
                  {advies.product_adviezen.map((a, i) => {
                    const kleur = a.type === "positief" ? "#22c55e" : a.type === "waarschuwing" ? "#ef4444" : "#fbbf24"
                    const icon = a.type === "positief" ? "✓" : a.type === "waarschuwing" ? "⚠️" : "ℹ️"
                    const inMandje = winkelmandje.some(w => w.naam === a.product)
                    return (
                      <div key={i} style={{ background: `${kleur}11`, border: `1px solid ${kleur}44`, borderRadius: 10, padding: "12px 14px", marginBottom: 8 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: kleur, marginBottom: 4 }}>{icon} {a.product}</div>
                            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{a.bericht}</div>
                            <div style={{ fontSize: "0.65rem", color: "#475569", marginTop: 4 }}>
                              Gemiddelde GI: {a.gem_gi}/10 · {a.n} sessie{a.n !== 1 ? "s" : ""}
                            </div>
                          </div>
                          {a.type === "positief" && !inMandje && (
                            <button
                              onClick={async () => {
                                const prod = sessies.flatMap(s => s.producten).find(p => p.naam === a.product)
                                if (prod) await voegToeWinkelmandje(prod, sessies[0])
                              }}
                              style={{ marginLeft: 10, padding: "6px 12px", background: "rgba(34,197,94,0.15)", border: "1px solid rgba(34,197,94,0.3)", borderRadius: 8, color: "#22c55e", cursor: "pointer", fontSize: "0.72rem", fontWeight: 700, whiteSpace: "nowrap" as const }}>
                              🛒 Toevoegen
                            </button>
                          )}
                          {inMandje && <span style={{ fontSize: "0.68rem", color: "#22c55e", marginLeft: 10 }}>✓ in mandje</span>}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Wetenschappelijke context */}
              <div style={{ ...card, border: "1px solid rgba(59,130,246,0.2)" }}>
                <div style={{ fontSize: "0.6rem", color: "#60a5fa", letterSpacing: 3, marginBottom: 12 }}>WETENSCHAPPELIJKE CONTEXT</div>
                {[
                  { titel: "Waarom 6 weken?", tekst: "2 weken GI-training verlaagt maagklachten gemiddeld al met 47% (PMC10185635, 2023). Over 6 weken bouw je een volledige darmaanpassing op." },
                  { titel: "Waarom alleen lange trainingen?", tekst: "Tijdens korte, intense trainingen is GI-belasting anders. Darmaanpassing voor racing vraagt specifiek langdurige inspanning (>60 min) bij lage-matige intensiteit." },
                  { titel: `Glucose:fructose ${advies.ratio_advies.includes("1:0.8") ? "1:0.8" : "2:1"}`, tekst: advies.ratio_advies.includes("1:0.8") ? "Boven 90g/uur: SGLT1 is verzadigd, 1:0.8 ratio optimaliseert absorptie via beide transporters (Rowlands et al., Podlogar 2022)." : "Boven 60g/uur: 2:1 glucose:fructose geeft optimale absorptie. Jeukendrup (2024): dit is de meest betrouwbare ratio voor 60–90g/uur." },
                ].map((item, i) => (
                  <div key={i} style={{ marginBottom: 10, padding: "10px 14px", background: "#141414", borderRadius: 8 }}>
                    <div style={{ fontSize: "0.75rem", color: "#60a5fa", fontWeight: 700, marginBottom: 4 }}>{item.titel}</div>
                    <div style={{ fontSize: "0.72rem", color: "#64748b", lineHeight: 1.5 }}>{item.tekst}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
