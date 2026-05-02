'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Dashboard() {
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const stored = localStorage.getItem('carboo_user')
    if (!stored) { router.push('/'); return }
    setUser(JSON.parse(stored))
  }, [router])

  function handleLogout() {
    localStorage.removeItem('carboo_user')
    router.push('/')
  }

  if (!user) return null

  const modules = [
    { id: 'fuelc', naam: 'FuelC', sub: 'Voeding & Dagschema', emoji: '⚡' },
    { id: 'coach', naam: 'Coach', sub: 'Begeleiding & Advies', emoji: '🎯' },
    { id: 'raceprep', naam: 'Race Prep', sub: 'Wedstrijdvoorbereiding', emoji: '🏁' },
    { id: 'testing', naam: 'Train the Gut', sub: 'Darmen trainen', emoji: '🧪' },
  ]

  return (
    <div className="min-h-screen bg-[#0a0f1e]">
      <header className="bg-[#1e293b] border-b border-[#334155] px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black tracking-widest text-white">CAR<span className="text-[#f97316]">BOO</span></h1>
            <p className="text-[#64748b] text-xs tracking-widest">SPORTS NUTRITION COACH</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-white font-semibold text-sm">{user.name}</div>
              <div className="text-[#64748b] text-xs"><span className="text-[#f97316] font-bold">{user.credits || 0}</span> credits</div>
            </div>
            <button onClick={handleLogout} className="text-[#64748b] hover:text-white text-sm border border-[#334155] rounded-lg px-3 py-1.5 transition-colors">
              Uitloggen
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h2 className="text-white text-xl font-bold">Jouw Nutrition Tools</h2>
          <p className="text-[#64748b] text-sm mt-1">Kies een module om te starten</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {modules.map(mod => (
            <button key={mod.id} onClick={() => router.push(`/${mod.id}`)}
              className="bg-[#1e293b] border border-[#334155] rounded-2xl p-6 text-left hover:border-[#f97316] hover:scale-[1.02] transition-all group">
              <div className="text-4xl mb-4">{mod.emoji}</div>
              <div className="text-white font-bold text-lg group-hover:text-[#f97316] transition-colors">{mod.naam}</div>
              <div className="text-[#64748b] text-sm mt-1">{mod.sub}</div>
            </button>
          ))}
        </div>
      </main>
    </div>
  )
}