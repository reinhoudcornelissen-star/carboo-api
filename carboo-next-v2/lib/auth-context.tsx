"use client"
import { createContext, useContext, useEffect, useState } from "react"
import { createSupabaseBrowserClient } from "@/lib/supabase"
import type { User } from "@supabase/supabase-js"

interface AuthContext {
  user: User | null
  token: string | null
  laden: boolean
  uitloggen: () => Promise<void>
}

const AuthCtx = createContext<AuthContext>({
  user: null, token: null, laden: true,
  uitloggen: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [laden, setLaden] = useState(true)
  const supabase = createSupabaseBrowserClient()

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null)
      setToken(data.session?.access_token ?? null)
      setLaden(false)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      setToken(session?.access_token ?? null)
      setLaden(false)
    })
    return () => subscription.unsubscribe()
  }, [])

  async function uitloggen() {
    await supabase.auth.signOut()
    window.location.href = "/login"
  }

  return (
    <AuthCtx.Provider value={{ user, token, laden, uitloggen }}>
      {children}
    </AuthCtx.Provider>
  )
}

export const useAuth = () => useContext(AuthCtx)
