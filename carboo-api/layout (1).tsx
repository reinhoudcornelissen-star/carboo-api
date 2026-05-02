"use client"
import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, laden, uitloggen } = useAuth()
  const router = useRouter()
  const pad = usePathname()

  useEffect(() => {
    if (!laden && !user) router.push("/login")
  }, [user, laden])

  if (laden) return (
    <div style={{
      minHeight: "100vh", background: "#0c0c0c",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{ color: "#f97316", fontFamily: "'Bebas Neue', sans-serif", fontSize: "1.2rem", letterSpacing: 3 }}>
        CARBOO LADEN...
      </div>
    </div>
  )

  if (!user) return null

  const nav = [
    { href: "/app/fueling",  label: "⚡ Fueling",         actief: pad.includes("/fueling") },
    { href: "/app/coach",    label: "🏁 Race Coach",       actief: pad.includes("/coach") },
    { href: "/app/gut",      label: "🫀 Train the Gut",    actief: pad.includes("/gut") },
  ]

  return (
    <div style={{ minHeight: "100vh", background: "#0c0c0c" }}>
      {/* Topbar */}
      <nav style={{
        position: "fixed", top: 0, zIndex: 100, width: "100%",
        padding: "0 clamp(16px,4vw,48px)",
        height: 56,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "rgba(12,12,12,0.92)", backdropFilter: "blur(16px)",
        borderBottom: "1px solid #1e1e1e",
      }}>
        <a href="/app" style={{
          fontFamily: "'Bebas Neue', sans-serif", fontSize: "1.2rem",
          color: "#f5f3ef", textDecoration: "none", letterSpacing: 1,
        }}>
          CAR<span style={{ color: "#f97316" }}>B</span>OO
        </a>

        {/* Module nav — desktop */}
        <div style={{ display: "flex", gap: 4 }}>
          {nav.map(n => (
            <a key={n.href} href={n.href} style={{
              padding: "6px 14px", borderRadius: 8,
              background: n.actief ? "rgba(249,115,22,0.12)" : "transparent",
              color: n.actief ? "#f97316" : "#555",
              fontSize: "0.8rem", fontWeight: 600,
              textDecoration: "none", transition: "all 0.15s",
              border: n.actief ? "1px solid rgba(249,115,22,0.25)" : "1px solid transparent",
            }}>
              {n.label}
            </a>
          ))}
        </div>

        <button onClick={uitloggen} style={{
          background: "transparent", border: "1px solid #2a2a2a",
          color: "#555", padding: "6px 14px", borderRadius: 8,
          fontSize: "0.78rem", cursor: "pointer",
        }}>
          Uitloggen
        </button>
      </nav>

      {/* Content */}
      <main style={{ paddingTop: 56, minHeight: "100vh" }}>
        {children}
      </main>
    </div>
  )
}
