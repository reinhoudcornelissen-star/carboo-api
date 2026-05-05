"use client"
import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { useParams, useRouter } from "next/navigation"

const API = "https://carboo-api.onrender.com"

export default function InvitePage() {
  const { token } = useAuth()
  const params = useParams()
  const router = useRouter()
  const inviteToken = params?.token as string

  const [info, setInfo] = useState<any>(null)
  const [laden, setLaden] = useState(true)
  const [fout, setFout] = useState("")
  const [bezig, setBezig] = useState(false)
  const [klaar, setKlaar] = useState(false)

  useEffect(() => {
    if (!inviteToken) return
    fetch(`${API}/api/coach/invite/${inviteToken}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json() })
      .then(d => setInfo(d.relatie))
      .catch(() => setFout("Deze uitnodiging is niet gevonden of verlopen."))
      .finally(() => setLaden(false))
  }, [inviteToken])

  async function accepteer() {
    if (!token) { setFout("Log eerst in om de uitnodiging te accepteren."); return }
    setBezig(true)
    try {
      const r = await fetch(`${API}/api/coach/invite/${inviteToken}/accepteer`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }
      })
      if (!r.ok) throw new Error()
      setKlaar(true)
      setTimeout(() => router.push("/app/coach-zone"), 2000)
    } catch { setFout("Fout bij accepteren. Probeer opnieuw.") }
    setBezig(false)
  }

  async function weiger() {
    setBezig(true)
    await fetch(`${API}/api/coach/invite/${inviteToken}/weiger`, { method: "POST" })
    router.push("/app")
    setBezig(false)
  }

  const s = { background: "#141414", minHeight: "100vh", padding: "40px 20px", fontFamily: "system-ui, sans-serif", color: "#f5f3ef", display: "flex", alignItems: "flex-start", justifyContent: "center" }

  if (laden) return <div style={s}><div style={{ color: "#3b82f6", marginTop: 60 }}>⏳ Uitnodiging laden...</div></div>

  if (fout) return (
    <div style={s}>
      <div style={{ maxWidth: 420, width: "100%", background: "#0f172a", borderRadius: 16, padding: 32, border: "1px solid rgba(239,68,68,0.3)", textAlign: "center" as const }}>
        <div style={{ fontSize: "2rem", marginBottom: 12 }}>❌</div>
        <div style={{ color: "#ef4444", marginBottom: 8, fontWeight: 700 }}>Uitnodiging niet geldig</div>
        <div style={{ color: "#64748b", fontSize: "0.82rem", marginBottom: 20 }}>{fout}</div>
        <a href="/app" style={{ color: "#3b82f6", fontSize: "0.82rem" }}>← Terug naar Carboo</a>
      </div>
    </div>
  )

  if (klaar) return (
    <div style={s}>
      <div style={{ maxWidth: 420, width: "100%", background: "#0f172a", borderRadius: 16, padding: 32, border: "1px solid rgba(34,197,94,0.3)", textAlign: "center" as const }}>
        <div style={{ fontSize: "2rem", marginBottom: 12 }}>✅</div>
        <div style={{ color: "#22c55e", fontWeight: 700, marginBottom: 6 }}>Uitnodiging geaccepteerd!</div>
        <div style={{ color: "#64748b", fontSize: "0.82rem" }}>Je wordt doorgestuurd naar Coach Zone...</div>
      </div>
    </div>
  )

  const coach = info?.carboo_coaches || {}

  return (
    <div style={s}>
      <div style={{ maxWidth: 420, width: "100%" }}>
        <div style={{ background: "#0f172a", borderRadius: 16, padding: 28, border: "1px solid rgba(59,130,246,0.3)", marginBottom: 16 }}>
          <div style={{ fontSize: "0.65rem", color: "#3b82f6", letterSpacing: 3, marginBottom: 16, fontWeight: 700 }}>UITNODIGING CARBOO COACH ZONE</div>

          <div style={{ display: "flex", gap: 14, alignItems: "center", marginBottom: 20 }}>
            <div style={{ width: 52, height: 52, borderRadius: "50%", background: "rgba(167,139,250,0.15)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.6rem", border: "2px solid rgba(167,139,250,0.3)", flexShrink: 0 }}>
              🎓
            </div>
            <div>
              <div style={{ fontSize: "1rem", fontWeight: 700, color: "#f5f3ef" }}>{coach.naam || "Carboo Coach"}</div>
              {coach.specialisatie && <div style={{ fontSize: "0.75rem", color: "#60a5fa", marginTop: 2 }}>{coach.specialisatie}</div>}
              {coach.email && <div style={{ fontSize: "0.72rem", color: "#475569", marginTop: 2 }}>{coach.email}</div>}
            </div>
          </div>

          {coach.bio && (
            <div style={{ background: "#141414", borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontSize: "0.78rem", color: "#94a3b8", lineHeight: 1.5 }}>
              {coach.bio}
            </div>
          )}

          <div style={{ background: "rgba(59,130,246,0.05)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: 10, padding: "14px 16px", marginBottom: 20 }}>
            <div style={{ fontSize: "0.65rem", color: "#3b82f6", fontWeight: 700, marginBottom: 8 }}>WAT GEBEURT ER ALS JE ACCEPTEERT?</div>
            <div style={{ fontSize: "0.75rem", color: "#94a3b8", lineHeight: 1.6 }}>
              ✓ De coach krijgt leesrecht op data die jij kiest te delen<br />
              ✓ Jij bepaalt per module wat zichtbaar is (dagschema, analyses, race plannen, Train the Gut, dossier)<br />
              ✓ De coach kan je opmerkingen sturen<br />
              ✓ Je kan de toegang op elk moment intrekken<br />
              ✗ De coach kan nooit iets wijzigen in jouw data
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={weiger} disabled={bezig}
              style={{ flex: 1, padding: "12px 0", background: "#1e293b", color: "#64748b", border: "1px solid #334155", borderRadius: 10, fontSize: "0.85rem", fontWeight: 700, cursor: "pointer" }}>
              Weigeren
            </button>
            <button onClick={accepteer} disabled={bezig}
              style={{ flex: 2, padding: "12px 0", background: "#3b82f6", color: "#fff", border: "none", borderRadius: 10, fontSize: "0.88rem", fontWeight: 700, cursor: "pointer" }}>
              {bezig ? "⏳ Even wachten..." : "✓ Uitnodiging accepteren"}
            </button>
          </div>
        </div>

        <div style={{ fontSize: "0.68rem", color: "#334155", textAlign: "center" as const }}>
          Deze uitnodiging verloopt over 7 dagen · Carboo deelt nooit data zonder jouw toestemming
        </div>
      </div>
    </div>
  )
}
