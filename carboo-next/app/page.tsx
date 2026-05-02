'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Fout bij inloggen.')
        setLoading(false)
        return
      }

      localStorage.setItem('carboo_user', JSON.stringify(data.user))
      router.push('/dashboard')

    } catch {
      setError('Er ging iets mis.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <h1 className="text-5xl font-black tracking-widest text-white">
            CAR<span className="text-[#f97316]">BOO</span>
          </h1>
          <p className="text-[#64748b] text-xs tracking-widest mt-2">SPORTS NUTRITION COACH</p>
        </div>
        <div className="bg-[#1e293b] rounded-2xl border border-[#334155] p-8">
          <h2 className="text-white font-bold text-lg mb-6">Inloggen</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-[#64748b] text-xs font-semibold tracking-wider block mb-2">E-MAILADRES</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-[#0f172a] border border-[#334155] rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-[#f97316] transition-colors"
                placeholder="jouw@email.com"
                required
              />
            </div>
            <div>
              <label className="text-[#64748b] text-xs font-semibold tracking-wider block mb-2">WACHTWOORD</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-[#0f172a] border border-[#334155] rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-[#f97316] transition-colors"
                placeholder="••••••••"
                required
              />
            </div>
            {error && (
              <div className="bg-red-900/30 border border-red-500/50 rounded-xl px-4 py-3 text-red-400 text-sm">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#f97316] hover:bg-[#ea6c0a] disabled:opacity-50 text-white font-bold py-3 rounded-xl transition-colors mt-2"
            >
              {loading ? 'Laden...' : 'Inloggen'}
            </button>
          </form>
        </div>
        <p className="text-center text-[#475569] text-xs mt-6">© 2025 Carboo · Sports Nutrition</p>
      </div>
    </div>
  )
}