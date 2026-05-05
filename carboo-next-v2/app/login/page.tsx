"use client"
import { useState } from "react"
import { createSupabaseBrowserClient } from "@/lib/supabase"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [wachtwoord, setWachtwoord] = useState("")
  const [modus, setModus] = useState<"login" | "register">("login")
  const [fout, setFout] = useState("")
  const [laden, setLaden] = useState(false)
  const [akkoord, setAkkoord] = useState(false)
  const router = useRouter()
  const supabase = createSupabaseBrowserClient()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFout("")
    if (modus === "register" && !akkoord) {
      setFout("Je moet akkoord gaan met de gebruiksvoorwaarden.")
      return
    }
    setLaden(true)
    try {
      if (modus === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password: wachtwoord })
        if (error) throw error
        router.push("/app/fueling")
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
    <div style={{ minHeight: "100vh", background: "#0c0c0c", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: "2.5rem", letterSpacing: 3, color: "#f5f3ef" }}>
            CAR<span style={{ color: "#f97316" }}>B</span>OO
          </div>
          <div style={{ fontSize: "0.7rem", color: "#555", letterSpacing: 3, marginTop: 6 }}>SPORTS NUTRITION COACH</div>
        </div>

        <div style={{ background: "#141414", border: "1px solid #2a2a2a", borderRadius: 16, padding: "36px 32px" }}>
          <div style={{ display: "flex", marginBottom: 28, gap: 4 }}>
            {(["login", "register"] as const).map(m => (
              <button key={m} onClick={() => { setModus(m); setFout(""); setAkkoord(false) }} style={{
                flex: 1, padding: "10px 0",
                background: modus === m ? "#f97316" : "transparent",
                color: modus === m ? "#0c0c0c" : "#555",
                border: modus === m ? "none" : "1px solid #2a2a2a",
                borderRadius: 8, cursor: "pointer",
                fontFamily: "'Bebas Neue', sans-serif",
                fontSize: "0.85rem", letterSpacing: 1,
              }}>
                {m === "login" ? "INLOGGEN" : "REGISTREREN"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: "0.7rem", color: "#555", letterSpacing: 2, display: "block", marginBottom: 8 }}>E-MAILADRES</label>
              <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                placeholder="jij@voorbeeld.com"
                style={{ width: "100%", padding: "12px 16px", background: "#1a1a1a", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem", outline: "none" }} />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ fontSize: "0.7rem", color: "#555", letterSpacing: 2, display: "block", marginBottom: 8 }}>WACHTWOORD</label>
              <input type="password" required value={wachtwoord} onChange={e => setWachtwoord(e.target.value)}
                placeholder="••••••••"
                style={{ width: "100%", padding: "12px 16px", background: "#1a1a1a", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem", outline: "none" }} />
            </div>

            {/* Disclaimer vinkje — enkel bij registreren */}
            {modus === "register" && (
              <div style={{ marginBottom: 20, display: "flex", alignItems: "flex-start", gap: 10 }}>
                <input
                  type="checkbox"
                  id="akkoord"
                  checked={akkoord}
                  onChange={e => setAkkoord(e.target.checked)}
                  style={{ marginTop: 2, accentColor: "#f97316", width: 16, height: 16, cursor: "pointer", flexShrink: 0 }}
                />
                <label htmlFor="akkoord" style={{ fontSize: "0.78rem", color: "#888", lineHeight: 1.5, cursor: "pointer" }}>
                  Ik ga akkoord met de{" "}
                  <a href="/voorwaarden" target="_blank" style={{ color: "#f97316", textDecoration: "underline" }}>
                    gebruiksvoorwaarden
                  </a>{" "}
                  en het{" "}
                  <a href="/privacy" target="_blank" style={{ color: "#f97316", textDecoration: "underline" }}>
                    privacybeleid
                  </a>{" "}
                  van Carboo. Ik begrijp dat de adviezen van Carboo geen vervanging zijn voor professioneel medisch of diëtistisch advies.
                </label>
              </div>
            )}

            {fout && (
              <div style={{
                padding: "10px 14px", marginBottom: 16, borderRadius: 8,
                background: fout.startsWith("✅") ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                border: `1px solid ${fout.startsWith("✅") ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
                color: fout.startsWith("✅") ? "#22c55e" : "#ef4444",
                fontSize: "0.82rem",
              }}>
                {fout}
              </div>
            )}

            <button type="submit" disabled={laden || (modus === "register" && !akkoord)} style={{
              width: "100%", padding: "14px 0",
              background: laden || (modus === "register" && !akkoord) ? "#333" : "#f97316",
              color: modus === "register" && !akkoord ? "#555" : "#0c0c0c",
              border: "none", borderRadius: 10,
              fontFamily: "'Bebas Neue', sans-serif",
              fontSize: "0.95rem", letterSpacing: 1,
              cursor: laden || (modus === "register" && !akkoord) ? "not-allowed" : "pointer",
              boxShadow: modus === "register" && !akkoord ? "none" : "0 8px 24px rgba(249,115,22,0.25)",
              transition: "all 0.2s",
            }}>
              {laden ? "EVEN WACHTEN..." : modus === "login" ? "INLOGGEN →" : "ACCOUNT AANMAKEN →"}
            </button>
          </form>

          {modus === "register" && (
            <div style={{ marginTop: 20, padding: "12px 16px", background: "rgba(249,115,22,0.06)", border: "1px solid rgba(249,115,22,0.15)", borderRadius: 8, fontSize: "0.78rem", color: "#888", textAlign: "center" }}>
              ✓ 7 dagen gratis · ✓ Geen creditcard · ✓ €9,99/maand daarna
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
