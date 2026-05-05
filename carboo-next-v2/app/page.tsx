"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

export default function Home() {
  const { user, laden } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!laden) {
      if (user) router.push("/app/fueling")
      else router.push("/login")
    }
  }, [user, laden])

  return (
    <div style={{ minHeight: "100vh", background: "#0c0c0c", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ color: "#f97316", fontFamily: "'Bebas Neue', sans-serif", fontSize: "1.5rem", letterSpacing: 4 }}>
        CAR<span style={{ color: "#f5f3ef" }}>B</span>OO
      </div>
    </div>
  )
}
