"use client"
import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"

const API = "https://carboo-api.onrender.com"

interface Rapport {
  id: string
  naam: string
  type: string
  meta: Record<string, any>
  datum: string
}

const TYPE_ICONS: Record<string, string> = {
  race_plan: "🏁",
  gut_log: "🍽️",
  analyse: "📊",
}

const TYPE_LABELS: Record<string, string> = {
  race_plan: "Race Nutrition Plan",
  gut_log: "Train the Gut",
  analyse: "Analyse",
}

export default function DossierPage() {
  const { token } = useAuth()
  const [rapporten, setRapporten] = useState<Rapport[]>([])
  const [laden, setLaden] = useState(true)
  const [geopend, setGeopend] = useState<string | null>(null)
  const [rapportHtml, setRapportHtml] = useState("")
  const [htmlLaden, setHtmlLaden] = useState(false)
  const [verwijderBezig, setVerwijderBezig] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    laadRapporten()
  }, [token])

  async function laadRapporten() {
    setLaden(true)
    try {
      const r = await fetch(`${API}/api/dossier/rapporten`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const d = await r.json()
      setRapporten(d.rapporten || [])
    } catch {}
    setLaden(false)
  }

  async function openRapport(id: string) {
    if (geopend === id) { setGeopend(null); setRapportHtml(""); return }
    setGeopend(id)
    setHtmlLaden(true)
    try {
      const r = await fetch(`${API}/api/dossier/rapporten/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const d = await r.json()
      setRapportHtml(d.html || "")
    } catch { setRapportHtml("<p>Kon rapport niet laden.</p>") }
    setHtmlLaden(false)
  }

  async function verwijderRapport(id: string) {
    setVerwijderBezig(id)
    try {
      await fetch(`${API}/api/dossier/rapporten/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      })
      setRapporten(prev => prev.filter(r => r.id !== id))
      if (geopend === id) { setGeopend(null); setRapportHtml("") }
    } catch {}
    setVerwijderBezig(null)
  }

  function downloadRapport(naam: string) {
    const a = document.createElement("a")
    a.href = `data:text/html;charset=utf-8,${encodeURIComponent(rapportHtml)}`
    a.download = `${naam.replace(/ /g, "_")}.html`
    a.click()
  }

  function formatDatum(iso: string) {
    return new Date(iso).toLocaleDateString("nl-BE", {
      day: "numeric", month: "long", year: "numeric"
    })
  }

  const s = {
    background: "#141414", minHeight: "100vh", padding: "20px 16px",
    fontFamily: "system-ui, sans-serif", color: "#f5f3ef"
  }
  const card = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, marginBottom: 10 }

  const groepenRace = rapporten.filter(r => r.type === "race_plan")
  const groepenGut = rapporten.filter(r => r.type === "gut_log")
  const groepenAndere = rapporten.filter(r => !["race_plan", "gut_log"].includes(r.type))

  function RapportGroep({ titel, items }: { titel: string; items: Rapport[] }) {
    if (items.length === 0) return null
    return (
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: "0.6rem", color: "#f97316", letterSpacing: 3, fontWeight: 700, marginBottom: 12 }}>{titel}</div>
        {items.map(rapport => (
          <div key={rapport.id} style={card}>
            {/* Rapport header */}
            <div style={{ padding: "14px 16px", display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}
              onClick={() => openRapport(rapport.id)}>
              <div style={{ fontSize: "1.4rem", flexShrink: 0 }}>{TYPE_ICONS[rapport.type] || "📄"}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f5f3ef", marginBottom: 2 }}>{rapport.naam}</div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" as const }}>
                  <span style={{ fontSize: "0.68rem", color: "#475569" }}>{formatDatum(rapport.datum)}</span>
                  {rapport.meta?.sport && <span style={{ fontSize: "0.68rem", color: "#64748b" }}>· {rapport.meta.sport}</span>}
                  {rapport.meta?.duur && <span style={{ fontSize: "0.68rem", color: "#64748b" }}>· {rapport.meta.duur}</span>}
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
                <span style={{ fontSize: "0.75rem", color: geopend === rapport.id ? "#f97316" : "#334155" }}>
                  {geopend === rapport.id ? "▲" : "▼"}
                </span>
                <button
                  onClick={e => { e.stopPropagation(); verwijderRapport(rapport.id) }}
                  disabled={verwijderBezig === rapport.id}
                  style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "0.85rem", padding: "4px 6px" }}>
                  {verwijderBezig === rapport.id ? "..." : "🗑"}
                </button>
              </div>
            </div>

            {/* Rapport inhoud */}
            {geopend === rapport.id && (
              <div style={{ borderTop: "1px solid #1e293b" }}>
                {/* Acties */}
                <div style={{ padding: "10px 16px", display: "flex", gap: 8 }}>
                  <a
                    href={`data:text/html;charset=utf-8,${encodeURIComponent(rapportHtml)}`}
                    download={`${rapport.naam.replace(/ /g, "_")}.html`}
                    style={{ padding: "8px 16px", background: "#22c55e", color: "#0c0c0c", borderRadius: 8, fontSize: "0.82rem", fontWeight: 700, textDecoration: "none", display: "inline-block" }}>
                    📥 Download HTML
                  </a>
                  <button
                    onClick={() => {
                      const w = window.open("", "_blank")
                      if (w) { w.document.write(rapportHtml); w.document.close() }
                    }}
                    style={{ padding: "8px 16px", background: "#1e293b", color: "#94a3b8", border: "1px solid #334155", borderRadius: 8, fontSize: "0.82rem", cursor: "pointer" }}>
                    👁 Bekijk
                  </button>
                </div>

                {/* Preview */}
                {htmlLaden ? (
                  <div style={{ padding: 24, textAlign: "center" as const, color: "#f97316" }}>⏳ Laden...</div>
                ) : (
                  <div style={{ padding: "0 16px 16px" }}>
                    <iframe
                      srcDoc={rapportHtml}
                      style={{ width: "100%", height: 500, border: "1px solid #1e293b", borderRadius: 8, background: "#fff" }}
                      title={rapport.naam}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div style={s}>
      {/* Header */}
      <div style={{ background: "linear-gradient(135deg,#1e293b,#0f172a)", borderRadius: 16, padding: "18px 22px", marginBottom: 24, borderLeft: "5px solid #f97316" }}>
        <div style={{ fontSize: "0.68rem", color: "#f97316", fontWeight: 800, letterSpacing: 2, marginBottom: 4 }}>📁 MIJN DOSSIER</div>
        <div style={{ fontSize: "1rem", color: "#94a3b8", fontSize: "0.88rem" as any }}>
          Al je race nutrition plannen en logs op één plek. Max 20 plannen opgeslagen.
        </div>
      </div>

      {laden ? (
        <div style={{ textAlign: "center" as const, color: "#f97316", padding: 40 }}>⏳ Laden...</div>
      ) : rapporten.length === 0 ? (
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 32, textAlign: "center" as const }}>
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>📭</div>
          <div style={{ color: "#f5f3ef", fontWeight: 700, marginBottom: 8 }}>Nog geen plannen opgeslagen</div>
          <div style={{ color: "#475569", fontSize: "0.85rem", marginBottom: 20 }}>
            Genereer een Race Nutrition Plan en sla het op in je dossier.
          </div>
          <a href="/app/coach" style={{ display: "inline-block", padding: "10px 24px", background: "#f97316", color: "#0c0c0c", borderRadius: 10, fontWeight: 700, fontSize: "0.88rem", textDecoration: "none" }}>
            🏁 Maak een Race Nutrition Plan
          </a>
        </div>
      ) : (
        <>
          {/* Teller */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <span style={{ fontSize: "0.75rem", color: "#475569" }}>{rapporten.length}/20 plannen opgeslagen</span>
            <div style={{ background: "#1e293b", borderRadius: 20, height: 6, width: 120, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${rapporten.length / 20 * 100}%`, background: rapporten.length >= 18 ? "#ef4444" : "#f97316", borderRadius: 20 }} />
            </div>
          </div>

          <RapportGroep titel="🏁 RACE NUTRITION PLANNEN" items={groepenRace} />
          <RapportGroep titel="🍽️ TRAIN THE GUT LOGS" items={groepenGut} />
          <RapportGroep titel="📄 ANDERE" items={groepenAndere} />
        </>
      )}

      {/* Coming soon */}
      <div style={{ background: "#0f172a", border: "1px dashed #334155", borderRadius: 12, padding: 20, marginTop: 8, textAlign: "center" as const }}>
        <div style={{ fontSize: "1.5rem", marginBottom: 8 }}>🍽️</div>
        <div style={{ color: "#64748b", fontSize: "0.82rem" }}>
          <b style={{ color: "#94a3b8" }}>Train the Gut</b> module — binnenkort beschikbaar<br />
          Systematisch je darmen trainen voor langdurige inspanning
        </div>
      </div>
    </div>
  )
}
