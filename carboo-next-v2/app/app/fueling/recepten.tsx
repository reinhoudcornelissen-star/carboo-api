"use client"
import { useState, useEffect } from "react"

const API = "https://carboo-api.onrender.com"

const RECEPT_TYPES = ["Alle", "Ontbijt", "Lunch", "Avondmaal", "Snack", "Sportvoeding", "Herstel"]

interface Ingredient {
  naam: string
  hoeveelheid_g: number
  kcal: number
  kh: number
  eiwit: number
  vet: number
  vezels: number
}

interface Recept {
  id: string
  naam: string
  type: string
  kcal: number
  kh: number
  eiwit: number
  vet: number
  vezels: number
  natrium: number
  ingredienten: Ingredient[]
  bereiding: string
  is_globaal: boolean
  eigen: boolean
  score?: number
  aantal_scores?: number
}

const LEGE_FORM = {
  naam: "", type: "Ontbijt", bereiding: "",
  ingredienten: [] as Ingredient[],
}

const LEEG_INGREDIENT: Ingredient = {
  naam: "", hoeveelheid_g: 100, kcal: 0, kh: 0, eiwit: 0, vet: 0, vezels: 0
}

function berekenTotaal(ingredienten: Ingredient[]) {
  return ingredienten.reduce((acc, ing) => {
    const f = ing.hoeveelheid_g / 100
    return {
      kcal: acc.kcal + ing.kcal * f,
      kh: acc.kh + ing.kh * f,
      eiwit: acc.eiwit + ing.eiwit * f,
      vet: acc.vet + ing.vet * f,
      vezels: acc.vezels + ing.vezels * f,
    }
  }, { kcal: 0, kh: 0, eiwit: 0, vet: 0, vezels: 0 })
}

function r(n: number) { return Math.round(n * 10) / 10 }

export default function Recepten({ token }: { token: string | null }) {
  const [recepten, setRecepten] = useState<Recept[]>([])
  const [zoek, setZoek] = useState("")
  const [typeFilter, setTypeFilter] = useState("Alle")
  const [toonFilter, setToonFilter] = useState<"alles" | "eigen" | "community">("alles")
  const [geselecteerd, setGeselecteerd] = useState<Recept | null>(null)
  const [toonForm, setToonForm] = useState(false)
  const [form, setForm] = useState(LEGE_FORM)
  const [laden, setLaden] = useState(false)
  const [opslaan, setOpslaan] = useState(false)
  const [fout, setFout] = useState("")
  const [mijnScore, setMijnScore] = useState<number>(0)

  useEffect(() => {
    if (!token) return
    laadRecepten()
  }, [token])

  async function laadRecepten() {
    setLaden(true)
    try {
      const d = await fetch(`${API}/api/fuelc/recepten`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => r.json())
      setRecepten((d.recepten || []).map((r: any) => ({
        ...r,
        eigen: !r.is_globaal,
        ingredienten: typeof r.ingredienten === "string"
          ? JSON.parse(r.ingredienten || "[]")
          : r.ingredienten || [],
      })))
    } catch {}
    finally { setLaden(false) }
  }

  async function slaReceptOp() {
    if (!token || !form.naam) { setFout("Naam is verplicht."); return }
    if (form.ingredienten.length === 0) { setFout("Voeg minstens 1 ingrediënt toe."); return }
    setOpslaan(true); setFout("")
    const totaal = berekenTotaal(form.ingredienten)
    try {
      await fetch(`${API}/api/fuelc/recepten`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          naam: form.naam,
          type: form.type,
          bereiding: form.bereiding,
          ingredienten: JSON.stringify(form.ingredienten),
          kcal: Math.round(totaal.kcal),
          kh: r(totaal.kh),
          eiwit: r(totaal.eiwit),
          vet: r(totaal.vet),
          vezels: r(totaal.vezels),
          natrium: 0,
          is_globaal: false,
        })
      })
      setToonForm(false)
      setForm(LEGE_FORM)
      await laadRecepten()
    } catch { setFout("Kon niet opslaan.") }
    finally { setOpslaan(false) }
  }

  async function verwijderRecept(id: string) {
    if (!token) return
    await fetch(`${API}/api/fuelc/recepten/${id}`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` }
    })
    setRecepten(r => r.filter(x => x.id !== id))
    if (geselecteerd?.id === id) setGeselecteerd(null)
  }

  function updateIngredient(idx: number, field: string, val: any) {
    setForm(f => ({
      ...f,
      ingredienten: f.ingredienten.map((ing, i) =>
        i === idx ? { ...ing, [field]: val } : ing
      )
    }))
  }

  function voegIngredientToe() {
    setForm(f => ({ ...f, ingredienten: [...f.ingredienten, { ...LEEG_INGREDIENT }] }))
  }

  function verwijderIngredient(idx: number) {
    setForm(f => ({ ...f, ingredienten: f.ingredienten.filter((_, i) => i !== idx) }))
  }

  const lijst = recepten.filter(r => {
    if (zoek && !r.naam.toLowerCase().includes(zoek.toLowerCase())) return false
    if (typeFilter !== "Alle" && r.type !== typeFilter) return false
    if (toonFilter === "eigen" && !r.eigen) return false
    if (toonFilter === "community" && r.eigen) return false
    return true
  })

  const totaalForm = berekenTotaal(form.ingredienten)

  const typeKleur: Record<string, string> = {
    "Ontbijt": "#f97316", "Lunch": "#22c55e", "Avondmaal": "#3b82f6",
    "Snack": "#fbbf24", "Sportvoeding": "#8b5cf6", "Herstel": "#06b6d4"
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: "0.65rem", color: "#f97316", letterSpacing: 3, fontWeight: 700 }}>RECEPTEN</div>
          <div style={{ fontSize: "0.72rem", color: "#475569", marginTop: 2 }}>{recepten.length} recepten · {recepten.filter(r => r.eigen).length} eigen</div>
        </div>
        <button onClick={() => { setToonForm(!toonForm); setFout("") }}
          style={{ background: toonForm ? "#1e293b" : "#f97316", color: toonForm ? "#888" : "#0c0c0c", border: toonForm ? "1px solid #2a2a2a" : "none", borderRadius: 8, padding: "8px 16px", cursor: "pointer", fontWeight: 700, fontSize: "0.82rem" }}>
          {toonForm ? "✕ Annuleer" : "+ Nieuw recept"}
        </button>
      </div>

      {/* Formulier nieuw recept */}
      {toonForm && (
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 20 }}>
          <div style={{ fontSize: "0.65rem", color: "#f97316", letterSpacing: 3, marginBottom: 14, fontWeight: 700 }}>NIEUW RECEPT</div>

          {/* Naam + type */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
            <div style={{ gridColumn: "1/-1" }}>
              <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 }}>NAAM *</div>
              <input value={form.naam} onChange={e => setForm({ ...form, naam: e.target.value })} placeholder="Receptnaam"
                style={{ width: "100%", padding: "9px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.88rem", outline: "none" }} />
            </div>
            <div>
              <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 }}>TYPE</div>
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}
                style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.82rem" }}>
                {RECEPT_TYPES.filter(t => t !== "Alle").map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 }}>PORTIES</div>
              <input type="number" defaultValue={1} min={1}
                style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.82rem" }} />
            </div>
          </div>

          {/* Ingrediënten */}
          <div style={{ fontSize: "0.62rem", color: "#64748b", letterSpacing: 2, marginBottom: 8 }}>INGREDIËNTEN</div>

          {/* Header rij */}
          {form.ingredienten.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr 1fr 28px", gap: 6, marginBottom: 4, padding: "0 4px" }}>
              {["Naam", "Gram", "Kcal", "KH", "Eiwit", "Vet", "Vezels", ""].map((h, i) => (
                <div key={i} style={{ fontSize: "0.58rem", color: "#475569" }}>{h}</div>
              ))}
            </div>
          )}

          {form.ingredienten.map((ing, idx) => (
            <div key={idx} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr 1fr 28px", gap: 6, marginBottom: 6, alignItems: "center" }}>
              <input value={ing.naam} onChange={e => updateIngredient(idx, "naam", e.target.value)} placeholder="Ingrediënt"
                style={{ padding: "7px 8px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.78rem", outline: "none" }} />
              {["hoeveelheid_g", "kcal", "kh", "eiwit", "vet", "vezels"].map(field => (
                <input key={field} type="number" value={(ing as any)[field]}
                  onChange={e => updateIngredient(idx, field, Number(e.target.value))}
                  style={{ padding: "7px 6px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.78rem", textAlign: "center" }} />
              ))}
              <button onClick={() => verwijderIngredient(idx)}
                style={{ background: "none", border: "none", color: "#475569", cursor: "pointer", fontSize: "0.85rem", padding: 0 }}>✕</button>
            </div>
          ))}

          <button onClick={voegIngredientToe}
            style={{ width: "100%", padding: "8px 0", background: "transparent", border: "1px dashed #2a2a2a", color: "#475569", borderRadius: 8, cursor: "pointer", fontSize: "0.78rem", marginBottom: 14 }}>
            + Ingrediënt toevoegen
          </button>

          {/* Auto totaal */}
          {form.ingredienten.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 8, marginBottom: 14 }}>
              {[
                { l: "Kcal", v: Math.round(totaalForm.kcal), k: "#f97316" },
                { l: "KH", v: r(totaalForm.kh) + "g", k: "#22c55e" },
                { l: "Eiwit", v: r(totaalForm.eiwit) + "g", k: "#3b82f6" },
                { l: "Vet", v: r(totaalForm.vet) + "g", k: "#fbbf24" },
                { l: "Vezels", v: r(totaalForm.vezels) + "g", k: "#64748b" },
              ].map(k => (
                <div key={k.l} style={{ background: "#1e293b", borderRadius: 8, padding: "8px 10px", textAlign: "center" }}>
                  <div style={{ fontSize: "0.58rem", color: "#64748b", marginBottom: 2 }}>{k.l}</div>
                  <div style={{ fontSize: "0.95rem", fontWeight: 800, color: k.k }}>{k.v}</div>
                </div>
              ))}
            </div>
          )}

          {/* Bereiding */}
          <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 4 }}>BEREIDING (optioneel)</div>
          <textarea value={form.bereiding} onChange={e => setForm({ ...form, bereiding: e.target.value })}
            placeholder="Beschrijf de bereiding stap voor stap..." rows={4}
            style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.82rem", resize: "vertical", outline: "none", marginBottom: 14 }} />

          {fout && <div style={{ color: "#ef4444", fontSize: "0.8rem", marginBottom: 10 }}>⚠️ {fout}</div>}
          <button onClick={slaReceptOp} disabled={opslaan}
            style={{ width: "100%", padding: "11px 0", background: opslaan ? "#333" : "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, cursor: opslaan ? "not-allowed" : "pointer", fontWeight: 700, fontSize: "0.88rem" }}>
            {opslaan ? "Opslaan..." : "✓ Recept opslaan"}
          </button>
        </div>
      )}

      {/* Zoek + filters */}
      <input placeholder="🔍 Zoek recept..." value={zoek} onChange={e => setZoek(e.target.value)}
        style={{ width: "100%", padding: "10px 14px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.85rem", marginBottom: 10, outline: "none" }} />

      <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
        {(["alles", "eigen", "community"] as const).map(f => (
          <button key={f} onClick={() => setToonFilter(f)}
            style={{ padding: "5px 14px", borderRadius: 20, border: "none", cursor: "pointer", fontSize: "0.75rem", fontWeight: 600, background: toonFilter === f ? "#f97316" : "#1e293b", color: toonFilter === f ? "#0c0c0c" : "#64748b" }}>
            {f === "alles" ? "Alles" : f === "eigen" ? "✏️ Eigen" : "🌍 Community"}
          </button>
        ))}
      </div>

      {/* Type filter */}
      <div style={{ display: "flex", gap: 6, overflowX: "auto", marginBottom: 16, paddingBottom: 4 }}>
        {RECEPT_TYPES.map(t => (
          <button key={t} onClick={() => setTypeFilter(t)}
            style={{ padding: "5px 12px", borderRadius: 20, border: "none", cursor: "pointer", fontSize: "0.72rem", fontWeight: 600, whiteSpace: "nowrap", background: typeFilter === t ? (typeKleur[t] || "#f97316") : "#1e293b", color: typeFilter === t ? "#0c0c0c" : "#64748b" }}>
            {t}
          </button>
        ))}
      </div>

      {/* Recepten grid */}
      <div style={{ display: "grid", gridTemplateColumns: geselecteerd ? "1fr 320px" : "repeat(auto-fill, minmax(280px, 1fr))", gap: 12, alignItems: "start" }}>

        {/* Lijst */}
        <div style={{ display: "grid", gridTemplateColumns: geselecteerd ? "1fr" : "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
          {laden ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "#475569" }}>Laden...</div>
          ) : lijst.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "#475569", fontSize: "0.85rem", gridColumn: "1/-1" }}>
              {zoek || typeFilter !== "Alle" ? "Geen recepten gevonden." : "Nog geen recepten. Maak je eerste recept aan!"}
            </div>
          ) : lijst.map(recept => (
            <div key={recept.id} onClick={() => setGeselecteerd(geselecteerd?.id === recept.id ? null : recept)}
              style={{ background: "#1e293b", borderRadius: 10, padding: 16, cursor: "pointer", border: "1px solid " + (geselecteerd?.id === recept.id ? "#f97316" : "#2a2a2a"), transition: "all 0.1s" }}>
              {/* Type badge + naam */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div>
                  <span style={{ fontSize: "0.62rem", fontWeight: 700, color: typeKleur[recept.type] || "#f97316", background: `${typeKleur[recept.type] || "#f97316"}18`, padding: "2px 8px", borderRadius: 4, display: "inline-block", marginBottom: 6 }}>
                    {recept.type}
                  </span>
                  <div style={{ fontWeight: 700, color: "#f5f3ef", fontSize: "0.9rem" }}>{recept.naam}</div>
                </div>
                {recept.eigen && (
                  <button onClick={e => { e.stopPropagation(); verwijderRecept(recept.id) }}
                    style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "0.85rem" }}>✕</button>
                )}
              </div>

              {/* Macros */}
              <div style={{ display: "flex", gap: 10, marginBottom: 8 }}>
                {[
                  { l: "Kcal", v: recept.kcal, k: "#f97316" },
                  { l: "KH", v: recept.kh + "g", k: "#22c55e" },
                  { l: "Eiwit", v: recept.eiwit + "g", k: "#3b82f6" },
                  { l: "Vet", v: recept.vet + "g", k: "#fbbf24" },
                ].map(m => (
                  <div key={m.l} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "0.7rem", fontWeight: 800, color: m.k }}>{m.v}</div>
                    <div style={{ fontSize: "0.58rem", color: "#475569" }}>{m.l}</div>
                  </div>
                ))}
              </div>

              {/* Ingrediënten preview */}
              {recept.ingredienten?.length > 0 && (
                <div style={{ fontSize: "0.68rem", color: "#475569" }}>
                  {recept.ingredienten.slice(0, 3).map(i => i.naam).join(", ")}
                  {recept.ingredienten.length > 3 && ` +${recept.ingredienten.length - 3} meer`}
                </div>
              )}

              {!recept.eigen && (
                <div style={{ fontSize: "0.62rem", color: "#64748b", marginTop: 6 }}>🌍 Community recept</div>
              )}
            </div>
          ))}
        </div>

        {/* Detail paneel */}
        {geselecteerd && (
          <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
              <div>
                <span style={{ fontSize: "0.6rem", fontWeight: 700, color: typeKleur[geselecteerd.type] || "#f97316", background: `${typeKleur[geselecteerd.type] || "#f97316"}18`, padding: "2px 8px", borderRadius: 4, display: "inline-block", marginBottom: 6 }}>
                  {geselecteerd.type}
                </span>
                <div style={{ fontWeight: 700, color: "#f5f3ef", fontSize: "0.95rem" }}>{geselecteerd.naam}</div>
              </div>
              <button onClick={() => setGeselecteerd(null)} style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "1rem" }}>✕</button>
            </div>

            {/* Macros samenvatting */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 16 }}>
              {[
                { l: "Kcal", v: geselecteerd.kcal, k: "#f97316" },
                { l: "KH", v: geselecteerd.kh + "g", k: "#22c55e" },
                { l: "Eiwit", v: geselecteerd.eiwit + "g", k: "#3b82f6" },
                { l: "Vet", v: geselecteerd.vet + "g", k: "#fbbf24" },
              ].map(m => (
                <div key={m.l} style={{ background: "#1e293b", borderRadius: 8, padding: "8px 10px", textAlign: "center" }}>
                  <div style={{ fontSize: "0.58rem", color: "#64748b", marginBottom: 2 }}>{m.l}</div>
                  <div style={{ fontSize: "1rem", fontWeight: 800, color: m.k }}>{m.v}</div>
                </div>
              ))}
            </div>

            {/* Ingrediënten */}
            {geselecteerd.ingredienten?.length > 0 && (
              <>
                <div style={{ fontSize: "0.6rem", color: "#64748b", letterSpacing: 2, marginBottom: 8, fontWeight: 700 }}>INGREDIËNTEN</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 16 }}>
                  {geselecteerd.ingredienten.map((ing, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid #1e293b" }}>
                      <span style={{ fontSize: "0.78rem", color: "#94a3b8" }}>{ing.naam}</span>
                      <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#f5f3ef" }}>{ing.hoeveelheid_g}g</span>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Bereiding */}
            {geselecteerd.bereiding && (
              <>
                <div style={{ fontSize: "0.6rem", color: "#64748b", letterSpacing: 2, marginBottom: 8, fontWeight: 700 }}>BEREIDING</div>
                <div style={{ fontSize: "0.78rem", color: "#94a3b8", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                  {geselecteerd.bereiding}
                </div>
              </>
            )}

            {/* Score */}
            {!geselecteerd.eigen && (
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #1e293b" }}>
                <div style={{ fontSize: "0.6rem", color: "#64748b", letterSpacing: 2, marginBottom: 8, fontWeight: 700 }}>BEOORDEEL DIT RECEPT</div>
                <div style={{ display: "flex", gap: 6 }}>
                  {[1, 2, 3, 4, 5].map(s => (
                    <button key={s} onClick={() => setMijnScore(s)}
                      style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.4rem", color: s <= mijnScore ? "#fbbf24" : "#334155" }}>
                      ★
                    </button>
                  ))}
                  {mijnScore > 0 && (
                    <span style={{ fontSize: "0.75rem", color: "#fbbf24", alignSelf: "center", marginLeft: 4 }}>
                      {["", "Slecht", "Matig", "Goed", "Zeer goed", "Uitstekend"][mijnScore]}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
