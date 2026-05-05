"use client"
import { useState, useEffect, useMemo, useRef } from "react"
import Recepten from "./recepten"

const API = "https://carboo-api.onrender.com"
const CATEGORIEËN = [
  "Alle", "Granen en brood", "Zuivel", "Eieren", "Vlees", "Vis",
  "Schaal- en schelpdieren", "Peulvruchten", "Sojaproducten",
  "Noten en zaden", "Groenten en fruit", "Vetten en oliën",
  "Sauzen en spreads", "Dranken", "Sportvoeding",
]

import { LEGE_FORM, NEVO, type Product } from "./nevo-data"


export default function Bibliotheek({ token }: { token: string | null }) {
  const [eigen, setEigen] = useState<Product[]>([])
  const [favoriet, setFavoriet] = useState<Set<string>>(new Set(
    typeof window !== "undefined" ? JSON.parse(localStorage.getItem("carboo_fav") || "[]") : []
  ))
  const [tab, setTab] = useState<"zoek"|"scan"|"manueel">("zoek")
  const [zoek, setZoek] = useState("")
  const [cat, setCat] = useState("Alle")
  const [filter, setFilter] = useState<"alles"|"favoriet"|"eigen">("alles")
  const [geselecteerd, setGeselecteerd] = useState<Product | null>(null)
  const [zoekActief, setZoekActief] = useState(false)
  const [toonForm, setToonForm] = useState(false)
  const [form, setForm] = useState(LEGE_FORM)
  const [opslaan, setOpslaan] = useState(false)
  const [fout, setFout] = useState("")
  const [opgeslaanNaam, setOpgeslaanNaam] = useState("")
  const [scanLaden, setScanLaden] = useState(false)
  const [scanFout, setScanFout] = useState("")

  // Laad eigen producten
  useEffect(() => {
    if (!token) return
    fetch(`${API}/api/fuelc/bibliotheek`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => setEigen(mapEigen(d.producten || [])))
      .catch(() => {})
  }, [token])

  function mapEigen(producten: any[]): Product[] {
    return producten.map((p: any) => ({
      id: p.id, db_id: p.id, eigen: true, naam: p.naam,
      cat: p.categorie || "Andere",
      portie_g: p.portie_g || 100, portie_label: p.portie_label || "100g",
      kcal: p.kcal_100g || 0, kh: p.kh_100g || 0, suikers: p.suikers_100g || 0,
      vezels: p.vezels_100g || 0, eiwit: p.eiwit_100g || 0, vet: p.vet_100g || 0,
      verz: p.verzadigd_100g || 0, natrium: p.natrium_100g || 0,
      kalium: p.kalium_100g || 0, calcium: p.calcium_100g || 0,
      ijzer: p.ijzer_100g || 0, magnesium: p.magnesium_100g || 0,
      vitc: p.vitc_100g || 0, vitd: p.vitd_100g || 0,
      vitb12: p.vitb12_100g || 0, omega3: p.omega3_100g || 0, gi: p.gi || 0,
    }))
  }

  async function herlaadEigen() {
    if (!token) return
    const d = await fetch(`${API}/api/fuelc/bibliotheek`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => ({ producten: [] }))
    setEigen(mapEigen(d.producten || []))
  }

  function toggleFav(id: string) {
    setFavoriet(prev => {
      const n = new Set(prev)
      n.has(id) ? n.delete(id) : n.add(id)
      try { localStorage.setItem("carboo_fav", JSON.stringify([...n])) } catch {}
      return n
    })
  }

  const alleLijst = useMemo(() => [...NEVO, ...eigen], [eigen])

  const gefilterd = useMemo(() => alleLijst.filter(p => {
    if (zoek && !p.naam.toLowerCase().includes(zoek.toLowerCase())) return false
    if (cat !== "Alle" && p.cat !== cat) return false
    if (filter === "favoriet" && !favoriet.has(p.id)) return false
    if (filter === "eigen" && !p.eigen) return false
    return true
  }), [alleLijst, zoek, cat, filter, favoriet])

  async function slaProductOp() {
    if (!token || !form.naam) { setFout("Naam is verplicht."); return }
    setOpslaan(true); setFout("")
    try {
      await fetch(`${API}/api/fuelc/bibliotheek`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          naam: form.naam, categorie: form.cat,
          portie_g: form.portie_g, portie_label: form.portie_label,
          kcal_100g: form.kcal, kh_100g: form.kh, suikers_100g: form.suikers,
          vezels_100g: form.vezels, eiwit_100g: form.eiwit, vet_100g: form.vet,
          verzadigd_100g: form.verz, natrium_100g: form.natrium,
          kalium_100g: form.kalium, calcium_100g: form.calcium,
          ijzer_100g: form.ijzer, magnesium_100g: form.magnesium,
          vitc_100g: form.vitc, vitd_100g: form.vitd,
          vitb12_100g: form.vitb12, omega3_100g: form.omega3, gi: form.gi,
        })
      })
      await herlaadEigen()
      setToonForm(false); setForm(LEGE_FORM)
      setOpgeslaanNaam(form.naam)
      setTimeout(() => setOpgeslaanNaam(""), 3000)
    } catch { setFout("Kon niet opslaan.") }
    finally { setOpslaan(false) }
  }

  async function scanEtiket(file: File) {
    setScanLaden(true); setScanFout(""); setFout("")
    try {
      const base64 = await new Promise<string>((res, rej) => {
        const reader = new FileReader()
        reader.onload = () => res((reader.result as string).split(",")[1])
        reader.onerror = rej
        reader.readAsDataURL(file)
      })
      const response = await fetch(`${API}/api/fuelc/scan-etiket`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ image_data: base64, media_type: file.type || "image/jpeg" })
      })
      if (!response.ok) throw new Error(`${response.status}`)
      const g = await response.json()
      setForm({
        naam: g.naam || "", cat: g.categorie || "Andere",
        portie_g: g.portie_g || 100, portie_label: g.portie_label || "100g",
        kcal: g.kcal || 0, kh: g.kh || 0, suikers: g.suikers || 0, vezels: g.vezels || 0,
        eiwit: g.eiwit || 0, vet: g.vet || 0, verz: g.verz || 0, natrium: g.natrium || 0,
        kalium: g.kalium || 0, calcium: g.calcium || 0, ijzer: g.ijzer || 0,
        magnesium: g.magnesium || 0, vitc: g.vitc || 0, vitd: g.vitd || 0,
        vitb12: g.vitb12 || 0, omega3: g.omega3 || 0, gi: g.gi || 0,
      })
      setToonForm(true)
      setTab("manueel")
    } catch (e: any) {
      setScanFout("Scan mislukt. Probeer opnieuw of voer manueel in.")
    } finally { setScanLaden(false) }
  }

  const inp = (label: string, veld: keyof typeof LEGE_FORM, type = "number") => (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 3 }}>{label}</div>
      <input type={type} value={(form as any)[veld]} step="any"
        onChange={e => setForm(f => ({ ...f, [veld]: type === "number" ? parseFloat(e.target.value) || 0 : e.target.value }))}
        style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem", outline: "none" }} />
    </div>
  )

  const s = { background: "#141414", minHeight: "100vh", padding: "20px 16px", fontFamily: "system-ui, sans-serif", color: "#f5f3ef" }
  const card = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 12 }
  const pill = (actief: boolean) => ({ padding: "6px 14px", borderRadius: 20, fontSize: "0.75rem", fontWeight: 600 as const, cursor: "pointer" as const, border: "none", background: actief ? "rgba(249,115,22,0.15)" : "#1e293b", color: actief ? "#f97316" : "#64748b" })

  return (
    <div style={s}>
      <div style={{ fontSize: "0.6rem", color: "#f97316", letterSpacing: 3, marginBottom: 16 }}>📚 VOEDSELBIBLIOTHEEK</div>

      {opgeslaanNaam && (
        <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: "0.82rem", color: "#22c55e" }}>
          ✓ {opgeslaanNaam} opgeslagen
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
        <button style={pill(tab === "zoek")} onClick={() => setTab("zoek")}>🔍 Zoeken</button>
        <button style={pill(tab === "scan")} onClick={() => setTab("scan")}>📷 Etiketscan</button>
        <button style={pill(tab === "manueel")} onClick={() => setTab("manueel")}>✏️ Manueel</button>
      </div>

      {/* TAB: ZOEKEN */}
      {tab === "zoek" && (
        <div>
          {/* Zoekbalk — inklapbaar */}
          <div style={{ ...card, padding: zoekActief ? 16 : "10px 16px" }}>
            <input
              value={zoek}
              onChange={e => { setZoek(e.target.value); if (!zoekActief) setZoekActief(true) }}
              onFocus={() => setZoekActief(true)}
              placeholder="🔍 Zoek in 220 producten..."
              style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem", outline: "none" }}
            />
            {zoekActief && (
              <>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" as const, marginTop: 10 }}>
                  {(["alles","favoriet","eigen"] as const).map(f => (
                    <button key={f} style={pill(filter === f)} onClick={() => setFilter(f)}>
                      {f === "alles" ? "Alles" : f === "favoriet" ? "⭐ Favoriet" : "✏️ Eigen"}
                    </button>
                  ))}
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" as const, marginTop: 8 }}>
                  {CATEGORIEËN.map(c => (
                    <button key={c} style={pill(cat === c)} onClick={() => setCat(c)}>
                      {c}
                    </button>
                  ))}
                </div>
                <button onClick={() => { setZoekActief(false); setZoek(""); setCat("Alle"); setFilter("alles") }}
                  style={{ marginTop: 10, fontSize: "0.72rem", color: "#475569", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
                  ✕ Sluiten
                </button>
              </>
            )}
          </div>

          {zoekActief && (gefilterd.length === 0 ? (
            <div style={{ color: "#334155", fontSize: "0.82rem", textAlign: "center" as const, padding: 32 }}>
              {zoek ? `Geen resultaten voor "${zoek}"` : "Geen producten gevonden."}
            </div>
          ) : (
            gefilterd.slice(0, 30).map(p => (
              <div key={p.id} style={{ ...card, cursor: "pointer" }} onClick={() => setGeselecteerd(geselecteerd?.id === p.id ? null : p)}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                      <span style={{ fontSize: "0.88rem", color: "#f5f3ef", fontWeight: 600 }}>{p.naam}</span>
                      {p.eigen && <span style={{ fontSize: "0.6rem", background: "rgba(249,115,22,0.1)", color: "#f97316", borderRadius: 4, padding: "1px 5px" }}>eigen</span>}
                    </div>
                    <div style={{ fontSize: "0.68rem", color: "#475569" }}>
                      {p.portie_label} · {p.kcal}kcal · KH {p.kh}g · Eiwit {p.eiwit}g · Vet {p.vet}g
                    </div>
                  </div>
                  <button onClick={e => { e.stopPropagation(); toggleFav(p.id) }}
                    style={{ background: "none", border: "none", fontSize: "1rem", cursor: "pointer", color: favoriet.has(p.id) ? "#f97316" : "#334155" }}>
                    {favoriet.has(p.id) ? "⭐" : "☆"}
                  </button>
                </div>
                {geselecteerd?.id === p.id && (
                  <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid #1e293b" }}>
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" as const, fontSize: "0.7rem", color: "#64748b" }}>
                      {[["Suikers",p.suikers+"g"],["Vezels",p.vezels+"g"],["Verz.vet",p.verz+"g"],
                        ["Kalium",p.kalium+"mg"],["Calcium",p.calcium+"mg"],["IJzer",p.ijzer+"mg"],
                        ["VitD",p.vitd+"µg"],["VitB12",p.vitb12+"µg"],["Omega3",p.omega3+"g"],["GI",p.gi||"—"]].map(([l,v]) => (
                        <span key={l as string}><span style={{color:"#94a3b8"}}>{l}:</span> {v}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          ))}
        </div>
      )}

      {/* TAB: ETIKETSCAN */}
      {tab === "scan" && (
        <div style={card}>
          <div style={{ fontSize: "0.6rem", color: "#f97316", letterSpacing: 2, marginBottom: 12 }}>📷 AI ETIKETSCAN</div>
          <div style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: 16 }}>
            Maak een foto van het voedingsetiket. De AI leest automatisch alle macro's en micronutriënten uit.
          </div>
          <label style={{ display: "block", padding: "20px", background: "#1e293b", border: "2px dashed #334155", borderRadius: 10, textAlign: "center" as const, cursor: "pointer" }}>
            <div style={{ fontSize: "2rem", marginBottom: 8 }}>📸</div>
            <div style={{ fontSize: "0.82rem", color: "#94a3b8" }}>Klik om foto te uploaden</div>
            <input type="file" accept="image/*" style={{ display: "none" }}
              onChange={e => { const f = e.target.files?.[0]; if (f) scanEtiket(f) }} />
          </label>
          {scanLaden && (
            <div style={{ marginTop: 12, color: "#f97316", fontSize: "0.82rem", textAlign: "center" as const }}>
              ⏳ AI analyseert etiket...
            </div>
          )}
          {scanFout && (
            <div style={{ marginTop: 12, color: "#ef4444", fontSize: "0.78rem" }}>{scanFout}</div>
          )}
          <div style={{ marginTop: 16, fontSize: "0.72rem", color: "#334155" }}>
            Na de scan wordt het formulier automatisch ingevuld. Je kan alles nog nakijken voor opslaan.
          </div>
        </div>
      )}

      {/* TAB: MANUEEL */}
      {tab === "manueel" && (
        <div style={{ ...card, border: "1px solid rgba(249,115,22,0.3)" }}>
          <div style={{ fontSize: "0.6rem", color: "#f97316", letterSpacing: 2, marginBottom: 14 }}>NIEUW PRODUCT (per 100g)</div>
          {inp("Naam *", "naam", "text")}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 3 }}>Categorie</div>
            <select value={form.cat} onChange={e => setForm(f => ({ ...f, cat: e.target.value }))}
              style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem" }}>
              {CATEGORIEËN.filter(c => c !== "Alle").map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {inp("Portie (g)", "portie_g")}
            {inp("Portie label", "portie_label", "text")}
            {inp("Kcal", "kcal")}
            {inp("Koolhydraten (g)", "kh")}
            {inp("Suikers (g)", "suikers")}
            {inp("Vezels (g)", "vezels")}
            {inp("Eiwit (g)", "eiwit")}
            {inp("Vet (g)", "vet")}
            {inp("Verzadigd vet (g)", "verz")}
            {inp("Natrium (mg)", "natrium")}
            {inp("Kalium (mg)", "kalium")}
            {inp("Calcium (mg)", "calcium")}
            {inp("IJzer (mg)", "ijzer")}
            {inp("Magnesium (mg)", "magnesium")}
            {inp("Vit C (mg)", "vitc")}
            {inp("Vit D (µg)", "vitd")}
            {inp("Vit B12 (µg)", "vitb12")}
            {inp("Omega-3 (g)", "omega3")}
            {inp("GI", "gi")}
          </div>
          {fout && <div style={{ color: "#ef4444", fontSize: "0.75rem", marginBottom: 8 }}>{fout}</div>}
          <button onClick={slaProductOp} disabled={opslaan}
            style={{ width: "100%", padding: "12px 0", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, fontWeight: 700, cursor: "pointer", fontSize: "0.88rem", marginTop: 8 }}>
            {opslaan ? "Opslaan..." : "✓ Opslaan in mijn bibliotheek"}
          </button>
        </div>
      )}

      {/* RECEPTEN */}
      <div style={{ marginTop: 24 }}>
        <Recepten token={token} />
      </div>
    </div>
  )
}
