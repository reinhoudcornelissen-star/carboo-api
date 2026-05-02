"use client"
import { useState } from "react"
import { createSupabaseBrowserClient } from "@/lib/supabase"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const [email, setEmail]       = useState("")
  const [wachtwoord, setWachtwoord] = useState("")
  const [modus, setModus]       = useState<"login" | "register">("login")
  const [fout, setFout]         = useState("")
  const [laden, setLaden]       = useState(false)
  const router = useRouter()
  const supabase = createSupabaseBrowserClient()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFout(""); setLaden(true)
    try {
      if (modus === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password: wachtwoord })
        if (error) throw error
        router.push("/app")
      } else {
        const { error } = await supabase.auth.signUp({ email, password: wachtwoord })
        if (error) throw error
        setFout("✅ Check je e-mail voor de bevestigingslink.")
      }
    } catch (err: any) {
      setFout(err.message || "Er ging iets mis.")
    } finally {
      setLaden(false)
    }
  }

  return (
    <div style={{
      minHeight: "100vh", background: "#0c0c0c",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'Instrument Sans', sans-serif", padding: "20px",
    }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <a href="/" style={{
            fontFamily: "'Bebas Neue', sans-serif",
            fontSize: "2rem", fontWeight: 800, letterSpacing: 2,
            color: "#f5f3ef", textDecoration: "none",
          }}>
            CAR<span style={{ color: "#f97316" }}>B</span>OO
          </a>
          <div style={{ fontSize: "0.72rem", color: "#555", letterSpacing: 3, marginTop: 6 }}>
            SPORTS NUTRITION COACH
          </div>
        </div>

        {/* Card */}
        <div style={{
          background: "#141414", border: "1px solid #2a2a2a",
          borderRadius: 16, padding: "36px 32px",
        }}>
          {/* Tabs */}
          <div style={{ display: "flex", marginBottom: 28, gap: 4 }}>
            {(["login", "register"] as const).map(m => (
              <button key={m} onClick={() => { setModus(m); setFout("") }} style={{
                flex: 1, padding: "10px 0",
                background: modus === m ? "#f97316" : "transparent",
                color: modus === m ? "#0c0c0c" : "#555",
                border: modus === m ? "none" : "1px solid #2a2a2a",
                borderRadius: 8, cursor: "pointer",
                fontFamily: "'Bebas Neue', sans-serif",
                fontSize: "0.85rem", fontWeight: 700, letterSpacing: 1,
                transition: "all 0.2s",
              }}>
                {m === "login" ? "INLOGGEN" : "REGISTREREN"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            {/* Email */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: "0.72rem", color: "#555", letterSpacing: 2, display: "block", marginBottom: 8 }}>
                E-MAILADRES
              </label>
              <input
                type="email" required value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="jij@voorbeeld.com"
                style={{
                  width: "100%", padding: "12px 16px",
                  background: "#1a1a1a", border: "1px solid #2a2a2a",
                  borderRadius: 8, color: "#f5f3ef",
                  fontSize: "0.9rem", outline: "none",
                  fontFamily: "inherit",
                }}
              />
            </div>

            {/* Wachtwoord */}
            <div style={{ marginBottom: 24 }}>
              <label style={{ fontSize: "0.72rem", color: "#555", letterSpacing: 2, display: "block", marginBottom: 8 }}>
                WACHTWOORD
              </label>
              <input
                type="password" required value={wachtwoord}
                onChange={e => setWachtwoord(e.target.value)}
                placeholder="••••••••"
                style={{
                  width: "100%", padding: "12px 16px",
                  background: "#1a1a1a", border: "1px solid #2a2a2a",
                  borderRadius: 8, color: "#f5f3ef",
                  fontSize: "0.9rem", outline: "none",
                  fontFamily: "inherit",
                }}
              />
            </div>

            {/* Fout/succes melding */}
            {fout && (
              <div style={{
                padding: "10px 14px", marginBottom: 16, borderRadius: 8,
                background: fout.startsWith("✅") ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                border: `1px solid ${fout.startsWith("✅") ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
                color: fout.startsWith("✅") ? "#22c55e" : "#ef4444",
                fontSize: "0.82rem", lineHeight: 1.5,
              }}>
                {fout}
              </div>
            )}

            {/* Submit */}
            <button type="submit" disabled={laden} style={{
              width: "100%", padding: "14px 0",
              background: laden ? "#555" : "#f97316",
              color: "#0c0c0c", border: "none", borderRadius: 10,
              fontFamily: "'Bebas Neue', sans-serif",
              fontSize: "0.95rem", fontWeight: 700, letterSpacing: 1,
              cursor: laden ? "not-allowed" : "pointer",
              transition: "background 0.2s",
              boxShadow: laden ? "none" : "0 8px 24px rgba(249,115,22,0.25)",
            }}>
              {laden ? "EVEN WACHTEN..." : modus === "login" ? "INLOGGEN →" : "ACCOUNT AANMAKEN →"}
            </button>
          </form>

          {/* Trial info */}
          {modus === "register" && (
            <div style={{
              marginTop: 20, padding: "12px 16px",
              background: "rgba(249,115,22,0.06)",
              border: "1px solid rgba(249,115,22,0.15)",
              borderRadius: 8, fontSize: "0.78rem", color: "#888", textAlign: "center",
            }}>
              ✓ 7 dagen gratis · ✓ Geen creditcard · ✓ €9,99/maand daarna
            </div>
          )}
        </div>

        <div style={{ textAlign: "center", marginTop: 24, fontSize: "0.75rem", color: "#333" }}>
          <a href="/" style={{ color: "#555", textDecoration: "none" }}>← Terug naar carboo.app</a>
        </div>
      </div>
    </div>
  )
}
