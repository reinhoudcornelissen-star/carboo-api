"use client"
import { useState, useEffect, useRef } from "react"
import { useAuth } from "@/lib/auth-context"
import Bibliotheek from "./bibliotheek"
import Dagschema from "./dagschema"
import AnalysesComponent from "./analyses"

const API = "https://carboo-api.onrender.com"

const TABS = [
  { id: "profiel",     label: "👤 Profiel" },
  { id: "trainingen",  label: "🏃 Trainingen" },
  { id: "bibliotheek", label: "📚 Bibliotheek" },
  { id: "dagschema",   label: "📅 Dagschema" },
  { id: "analyses",    label: "📊 Analyses" },
]

const ACTIVITEIT_OPTIES = [
  { label: "Weinig actief (zittend werk)", factor: 1.2 },
  { label: "Licht actief (1-3x/week buiten)", factor: 1.375 },
  { label: "Matig actief (3-5x/week buiten)", factor: 1.55 },
  { label: "Zeer actief (6-7x/week buiten)", factor: 1.725 },
  { label: "Extreem actief (2x/dag trainen)", factor: 1.9 },
]

const DOELSTELLING_OPTIES = [
  "Gewicht verliezen", "Gewicht behouden", "Spiermassa opbouwen",
  "Prestatie maximaliseren", "Herstel optimaliseren",
]

const EETPATROON_OPTIES = [
  "Klassiek (3 maaltijden)",
  "Intermittent fasting (16/8)",
  "Intermittent fasting (18/6)",
]

const TUSSENDOORTJE_OPTIES = [
  { aantal: 0, label: "Geen tussendoortjes" },
  { aantal: 1, label: "1 tussendoortje", momenten: ["Voormiddag"] },
  { aantal: 2, label: "2 tussendoortjes", momenten: ["Voormiddag", "Namiddag"] },
  { aantal: 3, label: "3 tussendoortjes", momenten: ["Voormiddag", "Namiddag", "Avondtussendoortje"] },
]

const KG_PER_WEEK = [0.25, 0.5, 0.75, 1.0]

const MET_WAARDEN: Record<string, Record<string, number>> = {
  "Fietsen":        { "Z1": 4.0, "Z2": 6.0, "Z3": 8.5,  "Z4": 10.5, "Z5": 13.0 },
  "Lopen":          { "Z1": 5.0, "Z2": 7.5, "Z3": 10.0, "Z4": 12.5, "Z5": 15.0 },
  "Zwemmen":        { "Z1": 4.5, "Z2": 6.5, "Z3": 8.5,  "Z4": 10.5, "Z5": 12.5 },
  "Triatlon":       { "Z1": 5.0, "Z2": 7.0, "Z3": 9.0,  "Z4": 11.5, "Z5": 14.0 },
  "Krachttraining": { "Z1": 3.0, "Z2": 4.0, "Z3": 5.5,  "Z4": 6.5,  "Z5": 7.5  },
  "Andere":         { "Z1": 4.0, "Z2": 6.0, "Z3": 8.0,  "Z4": 10.0, "Z5": 12.0 },
}

const ZONE_KLEUREN: Record<string, string> = {
  "Z1": "#3b82f6", "Z2": "#22c55e", "Z3": "#fbbf24", "Z4": "#f97316", "Z5": "#ef4444"
}

const SEGMENT_TYPES = [
  { naam: "Opwarming", standaard_zone: "Z1" },
  { naam: "Duurblok", standaard_zone: "Z2" },
  { naam: "Tempowerk", standaard_zone: "Z3" },
  { naam: "Drempelwerk", standaard_zone: "Z4" },
  { naam: "Intervalwerk", standaard_zone: "Z5" },
  { naam: "Cooldown", standaard_zone: "Z1" },
]

const ZONES = ["Z1 — Herstel", "Z2 — Duur", "Z3 — Tempo", "Z4 — Drempel", "Z5 — VO2max"]

interface Segment { naam: string; duur_min: number; zone: string }

function berekenBMR(geslacht: string, gewicht: number, lengte: number, leeftijd: number) {
  if (geslacht === "Man") return Math.round(10 * gewicht + 6.25 * lengte - 5 * leeftijd + 5)
  return Math.round(10 * gewicht + 6.25 * lengte - 5 * leeftijd - 161)
}

function getMomenten(eetpatroon: string, aantalTussendoortjes: number): string[] {
  if (eetpatroon.includes("fasting")) return ["Eerste maaltijd", "Tweede maaltijd", "Derde maaltijd"]
  const basis = ["Ontbijt", "Lunch", "Avondmaal"]
  const opt = TUSSENDOORTJE_OPTIES.find(t => t.aantal === aantalTussendoortjes)
  const extra = opt?.momenten || []
  const result: string[] = ["Ontbijt"]
  if (extra.includes("Voormiddag")) result.push("Voormiddag")
  result.push("Lunch")
  if (extra.includes("Namiddag")) result.push("Namiddag")
  result.push("Avondmaal")
  if (extra.includes("Avondtussendoortje")) result.push("Avondtussendoortje")
  return result
}

function berekenKcalSegmenten(sport: string, segmenten: Segment[], gewicht: number): number {
  return segmenten.reduce((tot, seg) => {
    const z = seg.zone.split(" ")[0]
    const met = MET_WAARDEN[sport]?.[z] || MET_WAARDEN["Andere"][z] || 6
    return tot + Math.round(met * gewicht * (seg.duur_min / 60))
  }, 0)
}

function s(stijl: object) { return stijl as React.CSSProperties }

async function apiFetch(path: string, options: RequestInit = {}, token?: string | null) {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...(options.headers as any) } })
  if (!res.ok) throw new Error(`API fout: ${res.status}`)
  return res.json()
}

// ── HOOFDPAGINA ───────────────────────────────────────────────────────────────
export default function FuelingPage() {
  const { token } = useAuth()
  const [tab, setTab] = useState("profiel")
  const [profiel, setProfiel] = useState<any>(() => {
    // Laad profiel uit localStorage als cache zodat het direct beschikbaar is
    try {
      const cached = localStorage.getItem("carboo_profiel")
      return cached ? JSON.parse(cached) : null
    } catch { return null }
  })

  useEffect(() => {
    if (!token) return
    apiFetch("/api/fuelc/profiel", {}, token)
      .then(d => {
        if (d.profiel) {
          setProfiel(d.profiel)
          // Sla op in localStorage als cache
          try { localStorage.setItem("carboo_profiel", JSON.stringify(d.profiel)) } catch {}
        }
      })
      .catch(() => {})
  }, [token])

  // Wrap setProfiel om ook localStorage bij te werken
  function updateProfiel(p: any) {
    setProfiel(p)
    try { localStorage.setItem("carboo_profiel", JSON.stringify(p)) } catch {}
  }

  return (
    <div style={s({ padding: "24px", maxWidth: 1100, margin: "0 auto" })}>
      <div style={s({ marginBottom: 24 })}>
        <div style={s({ fontSize: "0.65rem", color: "#f97316", letterSpacing: 3, marginBottom: 4 })}>FUELING COACH</div>
        <div style={s({ fontFamily: "'Bebas Neue', sans-serif", fontSize: "1.8rem", color: "#f5f3ef", letterSpacing: 1 })}>
          Voeding × Prestatie
        </div>
      </div>

      <div style={s({ display: "flex", gap: 4, marginBottom: 24, flexWrap: "wrap" })}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={s({
            padding: "8px 16px", borderRadius: 8,
            background: tab === t.id ? "#f97316" : "#1a1a1a",
            color: tab === t.id ? "#0c0c0c" : "#888",
            border: "1px solid " + (tab === t.id ? "#f97316" : "#2a2a2a"),
            cursor: "pointer", fontSize: "0.82rem", fontWeight: 600,
          })}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={s({ background: "#141414", border: "1px solid #2a2a2a", borderRadius: 16, padding: 28 })}>
        {tab === "profiel"     && <Profiel key={token || "geen-token"} profiel={profiel} setProfiel={updateProfiel} token={token} />}
        {tab === "trainingen"  && <Trainingen token={token} profiel={profiel} />}
        {tab === "bibliotheek" && <Bibliotheek token={token} />}
        {tab === "dagschema"   && <Dagschema profiel={profiel} token={token} />}
        {tab === "analyses"    && <Analyses profiel={profiel} token={token} setProfiel={updateProfiel} />}
      </div>
    </div>
  )
}

// ── PROFIEL ──────────────────────────────────────────────────────────────────
function Profiel({ profiel, setProfiel, token }: { profiel: any, setProfiel: (p: any) => void, token: string | null }) {
  const standaard = {
    geslacht: "Man", leeftijd: 30, gewicht_kg: 70, lengte_cm: 175,
    activiteit: ACTIVITEIT_OPTIES[2].label, doelstelling: "Prestatie maximaliseren",
    verlies_kg_week: 0.5, eet_patroon: "Klassiek (3 maaltijden)",
    tussendoortjes: 3, kh_doel_pct: 50, eiwit_doel_pct: 25, vet_doel_pct: 25,
  }
  const [form, setForm] = useState(() => {
    const p = profiel || {}
    return {
      ...standaard,
      ...p,
      tussendoortjes: (p.tussendoortjes != null) ? p.tussendoortjes : 3,
    }
  })
  const [maaltijdTijden, setMaaltijdTijden] = useState<Record<string, string>>(() => {
    const basis = {
      "Ontbijt": "07:30", "Voormiddag": "10:00", "Lunch": "12:30",
      "Namiddag": "15:30", "Avondmaal": "18:30", "Avondtussendoortje": "20:00",
      "Eerste maaltijd": "12:00", "Tweede maaltijd": "16:00", "Derde maaltijd": "20:00",
    }
    if (profiel?.momenten_tijden) {
      try { return { ...basis, ...JSON.parse(profiel.momenten_tijden) } } catch (_) {}
    }
    return basis
  })
  const [opgeslagen, setOpgeslagen] = useState(false)
  const [laden, setLaden] = useState(false)
  const [fout, setFout] = useState("")
  const isIngevuld = useRef(false)

  // Als profiel binnenkomt terwijl form nog leeg is (API trager dan render), vul dan in
  useEffect(() => {
    if (profiel && !isIngevuld.current) {
      isIngevuld.current = true
      const basis = {
        "Ontbijt": "07:30", "Voormiddag": "10:00", "Lunch": "12:30",
        "Namiddag": "15:30", "Avondmaal": "18:30", "Na training": "20:00",
        "Eerste maaltijd": "12:00", "Tweede maaltijd": "16:00", "Derde maaltijd": "20:00",
      }
      setForm({ ...standaard, ...profiel, tussendoortjes: (profiel.tussendoortjes != null) ? profiel.tussendoortjes : 3 })
      if (profiel.momenten_tijden) {
        try { setMaaltijdTijden({ ...basis, ...JSON.parse(profiel.momenten_tijden) }) } catch {}
      }
    }
  }, [profiel])

  const bmr = berekenBMR(form.geslacht, form.gewicht_kg, form.lengte_cm, form.leeftijd)
  const factor = ACTIVITEIT_OPTIES.find(a => a.label === form.activiteit)?.factor || 1.55
  const tdee = Math.round(bmr * factor)
  const kcalDeficit = form.doelstelling === "Gewicht verliezen" ? Math.round(form.verlies_kg_week * 7700 / 7) : 0
  const energieDoel = Math.max(1200, tdee - kcalDeficit)
  const totaalPct = form.kh_doel_pct + form.eiwit_doel_pct + form.vet_doel_pct

  function setMacro(key: string, val: number) {
    setForm(f => ({ ...f, [key]: Math.min(90, Math.max(5, val)) }))
  }

  async function opslaan() {
    if (!token) return
    setLaden(true); setFout("")
    const data = { ...form, bmr, tdee_basis: tdee, energie_doel: energieDoel, momenten_tijden: JSON.stringify(maaltijdTijden) }
    try {
      await apiFetch("/api/fuelc/profiel", { method: "POST", body: JSON.stringify(data) }, token)
      setProfiel(data)
      setOpgeslagen(true)
      setTimeout(() => setOpgeslagen(false), 3000)
    } catch { setFout("Kon niet opslaan. Controleer verbinding.") }
    finally { setLaden(false) }
  }

  return (
    <div>
      <div style={s({ fontSize: "0.65rem", color: "#f97316", letterSpacing: 3, marginBottom: 20 })}>JOUW PROFIEL</div>

      <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>LICHAAMSGEGEVENS</div>
      <div style={s({ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 24 })}>
        <div>
          <label style={s({ fontSize: "0.65rem", color: "#64748b", display: "block", marginBottom: 6 })}>GESLACHT</label>
          <select value={form.geslacht} onChange={e => setForm({ ...form, geslacht: e.target.value })}
            style={s({ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem" })}>
            <option>Man</option><option>Vrouw</option>
          </select>
        </div>
        {[{ label: "LEEFTIJD (jaar)", key: "leeftijd" }, { label: "GEWICHT (kg)", key: "gewicht_kg" }, { label: "LENGTE (cm)", key: "lengte_cm" }].map(v => (
          <div key={v.key}>
            <label style={s({ fontSize: "0.65rem", color: "#64748b", display: "block", marginBottom: 6 })}>{v.label}</label>
            <input type="number" value={(form as any)[v.key]} onChange={e => setForm({ ...form, [v.key]: Number(e.target.value) })}
              style={s({ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem", outline: "none" })} />
          </div>
        ))}
      </div>

      <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>ACTIVITEITSNIVEAU</div>
      <div style={s({ display: "flex", flexDirection: "column", gap: 6, marginBottom: 24 })}>
        {ACTIVITEIT_OPTIES.map(a => (
          <button key={a.label} onClick={() => setForm({ ...form, activiteit: a.label })} style={s({
            padding: "10px 14px", borderRadius: 8, textAlign: "left",
            background: form.activiteit === a.label ? "rgba(249,115,22,0.12)" : "#1e293b",
            border: "1px solid " + (form.activiteit === a.label ? "rgba(249,115,22,0.4)" : "#2a2a2a"),
            color: form.activiteit === a.label ? "#f97316" : "#888",
            cursor: "pointer", fontSize: "0.82rem",
          })}>{a.label}</button>
        ))}
      </div>

      <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>DOELSTELLING</div>
      <div style={s({ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 16 })}>
        {DOELSTELLING_OPTIES.map(d => (
          <button key={d} onClick={() => setForm({ ...form, doelstelling: d })} style={s({
            padding: "9px 12px", borderRadius: 8,
            background: form.doelstelling === d ? "rgba(249,115,22,0.12)" : "#1e293b",
            border: "1px solid " + (form.doelstelling === d ? "rgba(249,115,22,0.4)" : "#2a2a2a"),
            color: form.doelstelling === d ? "#f97316" : "#888",
            cursor: "pointer", fontSize: "0.78rem",
          })}>{d}</button>
        ))}
      </div>

      {form.doelstelling === "Gewicht verliezen" && (
        <div style={s({ background: "#1e293b", borderRadius: 10, padding: 16, marginBottom: 24 })}>
          <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 12 })}>TEMPO GEWICHTSVERLIES</div>
          <div style={s({ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8 })}>
            {KG_PER_WEEK.map(kg => (
              <button key={kg} onClick={() => setForm({ ...form, verlies_kg_week: kg })} style={s({
                padding: "10px 8px", borderRadius: 8, textAlign: "center",
                background: form.verlies_kg_week === kg ? "rgba(249,115,22,0.12)" : "#0f172a",
                border: "1px solid " + (form.verlies_kg_week === kg ? "rgba(249,115,22,0.4)" : "#2a2a2a"),
                color: form.verlies_kg_week === kg ? "#f97316" : "#888", cursor: "pointer",
              })}>
                <div style={s({ fontSize: "1rem", fontWeight: 800 })}>{kg}</div>
                <div style={s({ fontSize: "0.65rem", marginTop: 2 })}>kg/week</div>
                <div style={s({ fontSize: "0.6rem", color: "#475569", marginTop: 2 })}>-{Math.round(kg * 7700 / 7)} kcal</div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>EETPATROON</div>
      <div style={s({ display: "flex", flexDirection: "column", gap: 6, marginBottom: 16 })}>
        {EETPATROON_OPTIES.map(e => (
          <button key={e} onClick={() => setForm({ ...form, eet_patroon: e })} style={s({
            padding: "10px 14px", borderRadius: 8, textAlign: "left",
            background: form.eet_patroon === e ? "rgba(249,115,22,0.12)" : "#1e293b",
            border: "1px solid " + (form.eet_patroon === e ? "rgba(249,115,22,0.4)" : "#2a2a2a"),
            color: form.eet_patroon === e ? "#f97316" : "#888", cursor: "pointer", fontSize: "0.82rem",
          })}>{e}</button>
        ))}
      </div>

      {!form.eet_patroon.includes("fasting") && (
        <>
          <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>TUSSENDOORTJES</div>
          <div style={s({ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8, marginBottom: 20 })}>
            {TUSSENDOORTJE_OPTIES.map(opt => (
              <button key={opt.aantal} onClick={() => setForm({ ...form, tussendoortjes: opt.aantal })} style={s({
                padding: "10px 14px", borderRadius: 8, textAlign: "left",
                background: form.tussendoortjes === opt.aantal ? "rgba(249,115,22,0.12)" : "#1e293b",
                border: "1px solid " + (form.tussendoortjes === opt.aantal ? "rgba(249,115,22,0.4)" : "#2a2a2a"),
                color: form.tussendoortjes === opt.aantal ? "#f97316" : "#888", cursor: "pointer", fontSize: "0.82rem",
              })}>
                <div style={s({ fontWeight: 700 })}>{opt.label}</div>
                {opt.momenten && <div style={s({ fontSize: "0.7rem", color: "#64748b", marginTop: 3 })}>{opt.momenten.join(", ")}</div>}
              </button>
            ))}
          </div>
        </>
      )}

      <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>MAALTIJDTIJDEN</div>
      <div style={s({ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 24 })}>
        {getMomenten(form.eet_patroon, form.tussendoortjes || 0).map(mom => (
          <div key={mom} style={s({ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#1e293b", borderRadius: 8, padding: "10px 14px" })}>
            <span style={s({ fontSize: "0.82rem", color: "#f5f3ef" })}>{mom}</span>
            <input type="time" value={maaltijdTijden[mom] || "12:00"}
              onChange={e => setMaaltijdTijden({ ...maaltijdTijden, [mom]: e.target.value })}
              style={s({ background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f97316", padding: "4px 8px", fontSize: "0.82rem", fontWeight: 700 })} />
          </div>
        ))}
      </div>

      <div style={s({ fontSize: "0.7rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>
        MACROVERDELING
        <span style={s({ marginLeft: 8, color: totaalPct === 100 ? "#22c55e" : "#f97316" })}>({totaalPct}% — {totaalPct === 100 ? "✓" : "doel is 100%"})</span>
      </div>
      <div style={s({ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 })}>
        {[
          { label: "Koolhydraten", key: "kh_doel_pct", kleur: "#22c55e", gram: Math.round(energieDoel * form.kh_doel_pct / 100 / 4) },
          { label: "Eiwit", key: "eiwit_doel_pct", kleur: "#3b82f6", gram: Math.round(energieDoel * form.eiwit_doel_pct / 100 / 4) },
          { label: "Vet", key: "vet_doel_pct", kleur: "#f97316", gram: Math.round(energieDoel * form.vet_doel_pct / 100 / 9) },
        ].map(m => (
          <div key={m.key}>
            <div style={s({ display: "flex", justifyContent: "space-between", marginBottom: 6 })}>
              <span style={s({ fontSize: "0.85rem", color: "#f5f3ef" })}>{m.label}</span>
              <span style={s({ fontSize: "0.85rem", color: m.kleur, fontWeight: 700 })}>{(form as any)[m.key]}% · {m.gram}g/dag</span>
            </div>
            <input type="range" min={5} max={80} value={(form as any)[m.key]}
              onChange={e => setMacro(m.key, Number(e.target.value))}
              style={s({ width: "100%", accentColor: m.kleur, cursor: "pointer" })} />
          </div>
        ))}
      </div>

      <div style={s({ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10, marginBottom: 24 })}>
        {[
          { label: "BMR", waarde: bmr, kleur: "#3b82f6", sub: "basaal" },
          { label: "TDEE", waarde: tdee, kleur: "#f97316", sub: "activiteit" },
          { label: "ENERGIE DOEL", waarde: energieDoel, kleur: "#22c55e", sub: kcalDeficit > 0 ? `-${kcalDeficit} deficit` : "onderhoud" },
        ].map(k => (
          <div key={k.label} style={s({ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: 14, textAlign: "center" })}>
            <div style={s({ fontSize: "0.58rem", color: "#64748b", letterSpacing: 2, marginBottom: 6 })}>{k.label}</div>
            <div style={s({ fontSize: "1.6rem", fontWeight: 800, color: k.kleur })}>{k.waarde}</div>
            <div style={s({ fontSize: "0.65rem", color: "#64748b", marginTop: 2 })}>{k.sub}</div>
          </div>
        ))}
      </div>

      {fout && <div style={s({ padding: "10px 14px", marginBottom: 12, borderRadius: 8, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#ef4444", fontSize: "0.82rem" })}>⚠️ {fout}</div>}

      <button onClick={opslaan} disabled={laden} style={s({
        width: "100%", padding: 14, background: laden ? "#333" : "#f97316",
        color: "#0c0c0c", border: "none", borderRadius: 10,
        fontFamily: "'Bebas Neue', sans-serif", fontSize: "0.95rem", letterSpacing: 1,
        cursor: laden ? "not-allowed" : "pointer",
        boxShadow: "0 8px 24px rgba(249,115,22,0.25)",
      })}>
        {laden ? "OPSLAAN..." : "💾 PROFIEL OPSLAAN"}
      </button>

      {opgeslagen && (
        <div style={s({ marginTop: 12, padding: "10px 14px", background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)", borderRadius: 8, color: "#22c55e", fontSize: "0.82rem", textAlign: "center" })}>
          ✅ Profiel opgeslagen!
        </div>
      )}
    </div>
  )
}

// ── TRAININGEN ───────────────────────────────────────────────────────────────
function Trainingen({ token, profiel }: { token: string | null, profiel: any }) {
  const gewicht = profiel?.gewicht_kg || 70
  const [trainingen, setTrainingen] = useState<any[]>([])
  const [toonVoeg, setToonVoeg] = useState(false)
  const [fout, setFout] = useState("")
  const [uitgebreid, setUitgebreid] = useState(false)
  const [enkeleZone, setEnkeleZone] = useState("Z2")
  const [enkeleDuur, setEnkeleDuur] = useState(60)
  const [segmenten, setSegmenten] = useState<Segment[]>([
    { naam: "Opwarming", duur_min: 15, zone: "Z1" },
    { naam: "Duurblok", duur_min: 45, zone: "Z2" },
    { naam: "Cooldown", duur_min: 10, zone: "Z1" },
  ])
  const [nieuw, setNieuw] = useState({
    datum: new Date().toISOString().split("T")[0],
    sport: "Fietsen", starttijd: "07:00", notitie: "",
  })

  const sporten = ["Fietsen", "Lopen", "Zwemmen", "Triatlon", "Krachttraining", "Andere"]
  const totaalDuur = uitgebreid ? segmenten.reduce((a, s) => a + s.duur_min, 0) : enkeleDuur
  const totaalKcal = uitgebreid
    ? berekenKcalSegmenten(nieuw.sport, segmenten, gewicht)
    : Math.round((MET_WAARDEN[nieuw.sport]?.[enkeleZone] || 6) * gewicht * (enkeleDuur / 60))

  useEffect(() => {
    if (!token) return
    apiFetch("/api/fuelc/trainingen", {}, token).then(d => setTrainingen(d.trainingen || [])).catch(() => {})
  }, [token])

  function voegSegmentToe() { setSegmenten([...segmenten, { naam: "Duurblok", duur_min: 20, zone: "Z2" }]) }
  function updateSegment(idx: number, field: string, val: any) {
    setSegmenten(segmenten.map((s, i) => i === idx ? { ...s, [field]: val } : s))
  }
  function verwijderSegment(idx: number) {
    if (segmenten.length > 1) setSegmenten(segmenten.filter((_, i) => i !== idx))
  }

  async function voegToe() {
    if (!token) return
    setFout("")
    try {
      const data = { ...nieuw, duur_min: totaalDuur, kcal_verbranding: totaalKcal, afstand_km: 0,
        zone_verdeling: uitgebreid ? JSON.stringify(segmenten) : JSON.stringify([{ naam: "Training", duur_min: enkeleDuur, zone: enkeleZone }]) }
      await apiFetch("/api/fuelc/trainingen", { method: "POST", body: JSON.stringify(data) }, token)
      setToonVoeg(false)
      setSegmenten([{ naam: "Opwarming", duur_min: 15, zone: "Z1" }, { naam: "Duurblok", duur_min: 45, zone: "Z2" }, { naam: "Cooldown", duur_min: 10, zone: "Z1" }])
      const d = await apiFetch("/api/fuelc/trainingen", {}, token)
      setTrainingen(d.trainingen || [])
    } catch { setFout("Kon niet opslaan.") }
  }

  async function verwijder(id: string) {
    try {
      await apiFetch(`/api/fuelc/trainingen/${id}`, { method: "DELETE" }, token)
      setTrainingen(trainingen.filter((t: any) => t.id !== id))
    } catch {}
  }

  const totaalKcalWeek = trainingen
    .filter((t: any) => { const d = new Date(t.datum); return d >= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) })
    .reduce((a: number, t: any) => a + (t.kcal_verbranding || 0), 0)

  return (
    <div>
      <div style={s({ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 })}>
        <div>
          <div style={s({ fontSize: "0.65rem", color: "#f97316", letterSpacing: 3 })}>TRAININGEN</div>
          {totaalKcalWeek > 0 && <div style={s({ fontSize: "0.75rem", color: "#64748b", marginTop: 2 })}>7 dagen: <span style={s({ color: "#22c55e", fontWeight: 700 })}>{totaalKcalWeek} kcal</span></div>}
        </div>
        <button onClick={() => setToonVoeg(!toonVoeg)} style={s({ background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, padding: "8px 16px", cursor: "pointer", fontWeight: 700, fontSize: "0.82rem" })}>
          + Training
        </button>
      </div>

      {toonVoeg && (
        <div style={s({ background: "#1e293b", borderRadius: 10, padding: 16, marginBottom: 16 })}>
          {/* Modus toggle */}
          <div style={s({ display: "flex", gap: 4, marginBottom: 16, background: "#0f172a", borderRadius: 8, padding: 4 })}>
            <button onClick={() => setUitgebreid(false)} style={s({ flex: 1, padding: "8px 0", borderRadius: 6, border: "none", cursor: "pointer", background: !uitgebreid ? "#1e293b" : "transparent", color: !uitgebreid ? "#f97316" : "#555", fontSize: "0.82rem", fontWeight: 600 })}>⚡ Snel</button>
            <button onClick={() => setUitgebreid(true)} style={s({ flex: 1, padding: "8px 0", borderRadius: 6, border: "none", cursor: "pointer", background: uitgebreid ? "#1e293b" : "transparent", color: uitgebreid ? "#f97316" : "#555", fontSize: "0.82rem", fontWeight: 600 })}>📊 Segmenten</button>
          </div>

          {/* Basisinfo */}
          <div style={s({ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 14 })}>
            <div>
              <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>SPORT</div>
              <select value={nieuw.sport} onChange={e => setNieuw({ ...nieuw, sport: e.target.value })}
                style={s({ width: "100%", padding: "8px 10px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem" })}>
                {sporten.map(sp => <option key={sp}>{sp}</option>)}
              </select>
            </div>
            <div>
              <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>DATUM</div>
              <input type="date" value={nieuw.datum} onChange={e => setNieuw({ ...nieuw, datum: e.target.value })}
                style={s({ width: "100%", padding: "8px 10px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem" })} />
            </div>
            <div>
              <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>STARTTIJD</div>
              <input type="time" value={nieuw.starttijd} onChange={e => setNieuw({ ...nieuw, starttijd: e.target.value })}
                style={s({ width: "100%", padding: "8px 10px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem" })} />
            </div>
          </div>

          {/* Snel of segmenten */}
          {!uitgebreid ? (
            <div style={s({ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 })}>
              <div>
                <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>DUUR (min)</div>
                <input type="number" value={enkeleDuur} onChange={e => setEnkeleDuur(Number(e.target.value))}
                  style={s({ width: "100%", padding: "8px 10px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem" })} />
              </div>
              {nieuw.sport === "Krachttraining" ? (
                <div>
                  <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>
                    INTENSITEIT — <span style={s({ color: "#f97316" })}>{enkeleZone === "Z1" ? "Licht" : enkeleZone === "Z2" ? "Matig" : enkeleZone === "Z3" ? "Zwaar" : enkeleZone === "Z4" ? "Zeer zwaar" : "Maximaal"}</span>
                  </div>
                  <input type="range" min={1} max={5} value={parseInt(enkeleZone[1])} onChange={e => setEnkeleZone(`Z${e.target.value}`)}
                    style={s({ width: "100%", marginTop: 12, accentColor: ZONE_KLEUREN[enkeleZone], cursor: "pointer" })} />
                  <div style={s({ display: "flex", justifyContent: "space-between", fontSize: "0.62rem", color: "#475569", marginTop: 4 })}>
                    <span>Licht</span><span>Intens</span>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>INTENSITEIT</div>
                  <select value={enkeleZone} onChange={e => setEnkeleZone(e.target.value)}
                    style={s({ width: "100%", padding: "8px 10px", background: "#0f172a", border: `1px solid ${ZONE_KLEUREN[enkeleZone]}`, borderRadius: 6, color: ZONE_KLEUREN[enkeleZone], fontSize: "0.85rem", fontWeight: 700 })}>
                    {Object.entries(ZONE_KLEUREN).map(([z]) => <option key={z} value={z}>{z} — {["Herstel","Duur","Tempo","Drempel","VO2max"][parseInt(z[1])-1]}</option>)}
                  </select>
                </div>
              )}
            </div>
          ) : (
            <>
              <div style={s({ fontSize: "0.62rem", color: "#64748b", letterSpacing: 2, marginBottom: 10 })}>TRAININGSSTRUCTUUR</div>
              <div style={s({ display: "flex", height: 8, borderRadius: 4, overflow: "hidden", marginBottom: 12 })}>
                {segmenten.map((seg, i) => <div key={i} style={s({ flex: seg.duur_min, background: ZONE_KLEUREN[seg.zone] || "#334155" })} />)}
              </div>
              {segmenten.map((seg, idx) => (
                <div key={idx} style={s({ display: "grid", gridTemplateColumns: "2fr 1fr 1fr auto", gap: 8, alignItems: "center", marginBottom: 8 })}>
                  <select value={seg.naam} onChange={e => updateSegment(idx, "naam", e.target.value)}
                    style={s({ padding: "7px 10px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem" })}>
                    {SEGMENT_TYPES.map(t => <option key={t.naam}>{t.naam}</option>)}
                  </select>
                  <div style={s({ display: "flex", alignItems: "center", gap: 4 })}>
                    <input type="number" value={seg.duur_min} min={1} onChange={e => updateSegment(idx, "duur_min", Number(e.target.value))}
                      style={s({ width: "100%", padding: "7px 8px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem" })} />
                    <span style={s({ fontSize: "0.68rem", color: "#555", whiteSpace: "nowrap" })}>min</span>
                  </div>
                  <select value={seg.zone} onChange={e => updateSegment(idx, "zone", e.target.value)}
                    style={s({ padding: "7px 8px", background: "#0f172a", border: `1px solid ${ZONE_KLEUREN[seg.zone] || "#2a2a2a"}`, borderRadius: 6, color: ZONE_KLEUREN[seg.zone] || "#f5f3ef", fontSize: "0.82rem", fontWeight: 700 })}>
                    {Object.keys(ZONE_KLEUREN).map(z => <option key={z} value={z}>{z}</option>)}
                  </select>
                  <button onClick={() => verwijderSegment(idx)} style={s({ background: "none", border: "none", color: "#475569", cursor: "pointer", fontSize: "1rem", padding: "0 4px" })}>✕</button>
                </div>
              ))}
              <button onClick={voegSegmentToe} style={s({ background: "transparent", border: "1px dashed #2a2a2a", color: "#555", borderRadius: 6, padding: "6px 14px", cursor: "pointer", fontSize: "0.78rem", marginBottom: 14, width: "100%" })}>
                + Segment toevoegen
              </button>
            </>
          )}

          {/* Samenvatting */}
          <div style={s({ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 14 })}>
            {[{ label: "TOTAAL DUUR", waarde: `${totaalDuur} min`, kleur: "#f97316" }, { label: "KCAL VERBRAND", waarde: `${totaalKcal}`, kleur: "#22c55e" }].map(k => (
              <div key={k.label} style={s({ background: "#0f172a", borderRadius: 8, padding: "8px 12px", textAlign: "center" })}>
                <div style={s({ fontSize: "0.58rem", color: "#64748b", marginBottom: 3 })}>{k.label}</div>
                <div style={s({ fontSize: "1rem", fontWeight: 800, color: k.kleur })}>{k.waarde}</div>
              </div>
            ))}
          </div>

          <div style={s({ marginBottom: 12 })}>
            <div style={s({ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 })}>NOTITIE</div>
            <input value={nieuw.notitie} onChange={e => setNieuw({ ...nieuw, notitie: e.target.value })} placeholder="Gevoel, omstandigheden..."
              style={s({ width: "100%", padding: "8px 10px", background: "#0f172a", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem" })} />
          </div>

          {fout && <div style={s({ color: "#ef4444", fontSize: "0.78rem", marginBottom: 8 })}>⚠️ {fout}</div>}
          <div style={s({ display: "flex", gap: 8 })}>
            <button onClick={voegToe} style={s({ flex: 1, padding: "10px 0", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 700 })}>✓ Opslaan</button>
            <button onClick={() => setToonVoeg(false)} style={s({ padding: "10px 16px", background: "transparent", border: "1px solid #2a2a2a", color: "#555", borderRadius: 8, cursor: "pointer" })}>Annuleer</button>
          </div>
        </div>
      )}

      {trainingen.length === 0 ? (
        <div style={s({ textAlign: "center", padding: "40px 20px", color: "#555" })}>Nog geen trainingen gelogd.</div>
      ) : trainingen.map((t: any) => {
        let segs: Segment[] = []
        try { segs = JSON.parse(t.zone_verdeling || "[]") } catch {}
        return (
          <div key={t.id} style={s({ background: "#1e293b", borderRadius: 10, padding: "12px 16px", marginBottom: 8 })}>
            <div style={s({ display: "flex", justifyContent: "space-between", alignItems: "flex-start" })}>
              <div style={s({ flex: 1 })}>
                <div style={s({ fontWeight: 700, color: "#f5f3ef", fontSize: "0.9rem", marginBottom: 3 })}>{t.sport}</div>
                <div style={s({ fontSize: "0.75rem", color: "#64748b", marginBottom: segs.length > 0 ? 8 : 0 })}>
                  {new Date(t.datum + "T12:00:00").toLocaleDateString("nl-BE")}{t.starttijd ? ` om ${t.starttijd}` : ""} · {t.duur_min} min
                </div>
                {segs.length > 0 && (
                  <>
                    <div style={s({ display: "flex", height: 5, borderRadius: 3, overflow: "hidden", marginBottom: 6, gap: 1 })}>
                      {segs.map((seg, i) => <div key={i} style={s({ flex: seg.duur_min, background: ZONE_KLEUREN[seg.zone] || "#334155", borderRadius: 2 })} />)}
                    </div>
                    <div style={s({ display: "flex", gap: 6, flexWrap: "wrap" })}>
                      {segs.map((seg, i) => (
                        <span key={i} style={s({ fontSize: "0.65rem", color: ZONE_KLEUREN[seg.zone], background: `${ZONE_KLEUREN[seg.zone]}18`, padding: "2px 7px", borderRadius: 4 })}>
                          {seg.naam} {seg.duur_min}' {seg.zone}
                        </span>
                      ))}
                    </div>
                  </>
                )}
                {t.notitie && <div style={s({ fontSize: "0.72rem", color: "#475569", marginTop: 4 })}>{t.notitie}</div>}
              </div>
              <div style={s({ display: "flex", alignItems: "center", gap: 12, marginLeft: 12 })}>
                {t.kcal_verbranding > 0 && (
                  <div style={s({ textAlign: "right" })}>
                    <div style={s({ fontSize: "1rem", fontWeight: 800, color: "#22c55e" })}>{t.kcal_verbranding}</div>
                    <div style={s({ fontSize: "0.65rem", color: "#64748b" })}>kcal</div>
                  </div>
                )}
                <button onClick={() => verwijder(t.id)} style={s({ background: "none", border: "none", color: "#475569", cursor: "pointer", fontSize: "1.1rem" })}>✕</button>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Analyses is een extern component (analyses.tsx)
function Analyses({ profiel, token }: { profiel: any, token: string | null }) {
  return <AnalysesComponent profiel={profiel} token={token} />
}
