"use client"
import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"

const API = "https://carboo-api.onrender.com"

// ─── TYPES ───────────────────────────────────────────────────────────────────
interface CoachProfiel {
  id: string; naam: string; bio: string; specialisatie: string; email: string; verified: boolean
}
interface Relatie {
  id: string; status: string; aangemaakt: string
  carboo_coaches: { naam: string; bio: string; specialisatie: string; email: string }
  carboo_coach_privacy?: Privacy
}
interface Privacy {
  fuelc_dagschema: boolean; fuelc_analyses: boolean
  race_plannen: boolean; train_gut: boolean; dossier: boolean
}
interface Klant {
  id: string; klant_id: string; aangemaakt: string
  carboo_coach_privacy?: Privacy | Privacy[]
}
interface Opmerking {
  id: string; tekst: string; item_type: string; item_label: string
  gelezen: boolean; aangemaakt: string
  carboo_coaches?: { naam: string }
  carboo_coach_reacties?: { id: string; tekst: string; aangemaakt: string }[]
}

// ─── STIJLEN ─────────────────────────────────────────────────────────────────
const s = { background: "#141414", minHeight: "100vh", padding: "20px 16px", fontFamily: "system-ui, sans-serif", color: "#f5f3ef" }
const card = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 16, marginBottom: 12 }
const pill = (actief: boolean, kleur = "#3b82f6") => ({
  padding: "6px 14px", borderRadius: 20, fontSize: "0.75rem", fontWeight: 600 as const,
  cursor: "pointer" as const, border: "none",
  background: actief ? `rgba(59,130,246,0.15)` : "#1e293b",
  color: actief ? kleur : "#64748b"
})
const btn = (kleur = "#3b82f6", klein = false) => ({
  padding: klein ? "6px 14px" : "10px 20px",
  background: kleur, color: kleur === "#1e293b" ? "#94a3b8" : "#0c0c0c",
  border: kleur === "#1e293b" ? "1px solid #334155" : "none",
  borderRadius: 8, fontSize: klein ? "0.78rem" : "0.85rem",
  fontWeight: 700 as const, cursor: "pointer" as const
})

// ─── HOOFDCOMPONENT ───────────────────────────────────────────────────────────
export default function CoachZonePage() {
  const { user, token } = useAuth()
  const [modus, setModus] = useState<"kies" | "coach" | "klant">("kies")
  const [laden, setLaden] = useState(true)
  const [coachProfiel, setCoachProfiel] = useState<CoachProfiel | null>(null)
  const [mijnCoaches, setMijnCoaches] = useState<Relatie[]>([])
  const [mijnKlanten, setMijnKlanten] = useState<Klant[]>([])
  const [opmerkingen, setOpmerkingen] = useState<Opmerking[]>([])
  const [ongelezen, setOngelezen] = useState(0)
  const [melding, setMelding] = useState("")

  // Coach profiel form
  const [coachNaam, setCoachNaam] = useState("")
  const [coachBio, setCoachBio] = useState("")
  const [coachSpec, setCoachSpec] = useState("")
  const [coachEmail, setCoachEmail] = useState(user?.email || "")
  const [coachOpslaan, setCoachOpslaan] = useState(false)

  // Invite
  const [inviteLink, setInviteLink] = useState("")
  const [inviteLaden, setInviteLaden] = useState(false)

  // Geselecteerde klant (coach dashboard)
  const [gekozenKlant, setGekozenKlant] = useState<Klant | null>(null)
  const [klantData, setKlantData] = useState<any>(null)
  const [klantDataLaden, setKlantDataLaden] = useState(false)
  const [nieuweOpmerking, setNieuweOpmerking] = useState("")
  const [opmerkingItemType, setOpmerkingItemType] = useState("algemeen")
  const [opmerkingItemLabel, setOpmerkingItemLabel] = useState("")
  const [notitie, setNotitie] = useState("")
  const [notities, setNotities] = useState<any[]>([])

  // Privacy toggles (klant)
  const [privacyMap, setPrivacyMap] = useState<Record<string, Privacy>>({})

  // Reactie
  const [reactieTekst, setReactieTekst] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!token) return
    laadAlles()
  }, [token])

  async function laadAlles() {
    setLaden(true)
    const h = { Authorization: `Bearer ${token}` }
    try {
      const [cpRes, mcRes, mkRes, ompRes] = await Promise.all([
        fetch(`${API}/api/coach/profiel`, { headers: h }),
        fetch(`${API}/api/coach/mijn-coaches`, { headers: h }),
        fetch(`${API}/api/coach/mijn-klanten`, { headers: h }),
        fetch(`${API}/api/coach/opmerkingen/klant`, { headers: h }),
      ])
      const [cp, mc, mk, omp] = await Promise.all([cpRes.json(), mcRes.json(), mkRes.json(), ompRes.json()])
      if (cp.profiel) {
        setCoachProfiel(cp.profiel)
        setCoachNaam(cp.profiel.naam)
        setCoachBio(cp.profiel.bio || "")
        setCoachSpec(cp.profiel.specialisatie || "")
        setCoachEmail(cp.profiel.email || user?.email || "")
        if (!modus || modus === "kies") setModus("coach")
      }
      setMijnCoaches(mc.coaches || [])
      setMijnKlanten(mk.klanten || [])
      setOpmerkingen(omp.opmerkingen || [])
      setOngelezen(omp.ongelezen || 0)
      // Privacy map
      const pm: Record<string, Privacy> = {}
      ;(mc.coaches || []).forEach((rel: Relatie) => {
        if (rel.carboo_coach_privacy) pm[rel.id] = rel.carboo_coach_privacy as Privacy
      })
      setPrivacyMap(pm)
      if (!cp.profiel && (mc.coaches || []).length > 0 && modus === "kies") setModus("klant")
    } catch {}
    setLaden(false)
  }

  async function slaCoachProfielOp() {
    setCoachOpslaan(true)
    try {
      await fetch(`${API}/api/coach/profiel`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ naam: coachNaam, bio: coachBio, specialisatie: coachSpec, email: coachEmail })
      })
      setMelding("✓ Coach profiel opgeslagen!")
      await laadAlles()
      setModus("coach")
      setTimeout(() => setMelding(""), 3000)
    } catch { setMelding("Fout bij opslaan.") }
    setCoachOpslaan(false)
  }

  async function genereerInvite() {
    setInviteLaden(true)
    try {
      const r = await fetch(`${API}/api/coach/invite/genereer`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }
      })
      const d = await r.json()
      const fullLink = `${window.location.origin}${d.link}`
      setInviteLink(fullLink)
    } catch {}
    setInviteLaden(false)
  }

  async function laadKlantData(klant: Klant) {
    setGekozenKlant(klant)
    setKlantDataLaden(true)
    setKlantData(null)
    try {
      const r = await fetch(`${API}/api/coach/klant/${klant.klant_id}/data`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const d = await r.json()
      setKlantData(d)
      // Laad notities
      const n = await fetch(`${API}/api/coach/notities/${klant.klant_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const nd = await n.json()
      setNotities(nd.notities || [])
    } catch {}
    setKlantDataLaden(false)
  }

  async function plaatsOpmerking() {
    if (!gekozenKlant || !nieuweOpmerking.trim()) return
    try {
      await fetch(`${API}/api/coach/opmerkingen`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          relatie_id: gekozenKlant.id, klant_id: gekozenKlant.klant_id,
          tekst: nieuweOpmerking, item_type: opmerkingItemType,
          item_label: opmerkingItemLabel || null
        })
      })
      setNieuweOpmerking(""); setOpmerkingItemLabel("")
      setMelding("✓ Opmerking verstuurd!")
      setTimeout(() => setMelding(""), 3000)
    } catch {}
  }

  async function slaNotitieOp() {
    if (!gekozenKlant || !notitie.trim()) return
    try {
      await fetch(`${API}/api/coach/notities`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ klant_id: gekozenKlant.klant_id, tekst: notitie })
      })
      setNotitie("")
      const n = await fetch(`${API}/api/coach/notities/${gekozenKlant.klant_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const nd = await n.json()
      setNotities(nd.notities || [])
    } catch {}
  }

  async function updatePrivacy(relatieId: string, veld: keyof Privacy, waarde: boolean) {
    const huidig = privacyMap[relatieId] || { fuelc_dagschema: true, fuelc_analyses: false, race_plannen: true, train_gut: false, dossier: false }
    const nieuw = { ...huidig, [veld]: waarde }
    setPrivacyMap(prev => ({ ...prev, [relatieId]: nieuw }))
    await fetch(`${API}/api/coach/privacy/${relatieId}`, {
      method: "PUT", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ relatie_id: relatieId, ...nieuw })
    })
  }

  async function plaatsReactie(opmId: string) {
    const tekst = reactieTekst[opmId]
    if (!tekst?.trim()) return
    await fetch(`${API}/api/coach/reacties`, {
      method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ opmerking_id: opmId, tekst })
    })
    setReactieTekst(prev => ({ ...prev, [opmId]: "" }))
    await laadAlles()
  }

  async function markeerGelezen(id: string) {
    await fetch(`${API}/api/coach/opmerkingen/${id}/gelezen`, {
      method: "PUT", headers: { Authorization: `Bearer ${token}` }
    })
    setOpmerkingen(prev => prev.map(o => o.id === id ? { ...o, gelezen: true } : o))
    setOngelezen(prev => Math.max(0, prev - 1))
  }

  async function verwijderCoach(relatieId: string) {
    if (!confirm("Wil je deze coach verwijderen? Dit verwijdert ook alle gedeelde data.")) return
    await fetch(`${API}/api/coach/mijn-coaches/${relatieId}`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` }
    })
    await laadAlles()
  }

  if (laden) return <div style={s}><div style={{ textAlign: "center", padding: 60, color: "#3b82f6" }}>⏳ Laden...</div></div>

  // ─── KEUZE SCHERM ─────────────────────────────────────────────────────────
  if (modus === "kies") return (
    <div style={s}>
      <div style={{ background: "linear-gradient(135deg,#1e293b,#0f172a)", borderRadius: 16, padding: "24px 22px", marginBottom: 24, borderLeft: "5px solid #3b82f6", textAlign: "center" as const }}>
        <div style={{ fontSize: "0.68rem", color: "#3b82f6", fontWeight: 800, letterSpacing: 2, marginBottom: 8 }}>👥 COACH ZONE</div>
        <div style={{ fontSize: "1rem", color: "#94a3b8" }}>Ben je coach of atleet?</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div style={{ ...card, cursor: "pointer", textAlign: "center" as const, padding: 28, border: "1px solid rgba(167,139,250,0.3)" }} onClick={() => setModus("coach")}>
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🎓</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#f5f3ef", marginBottom: 6 }}>Ik ben coach</div>
          <div style={{ fontSize: "0.78rem", color: "#475569" }}>Sportdiëtist, trainer of begeleider</div>
        </div>
        <div style={{ ...card, cursor: "pointer", textAlign: "center" as const, padding: 28, border: "1px solid rgba(59,130,246,0.3)" }} onClick={() => setModus("klant")}>
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🏃</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#f5f3ef", marginBottom: 6 }}>Ik ben atleet</div>
          <div style={{ fontSize: "0.78rem", color: "#475569" }}>Bekijk en beheer je coaches</div>
        </div>
      </div>
    </div>
  )

  // ─── COACH MODUS ──────────────────────────────────────────────────────────
  if (modus === "coach") return (
    <div style={s}>
      <div style={{ background: "linear-gradient(135deg,#1e293b,#0f172a)", borderRadius: 16, padding: "18px 22px", marginBottom: 20, borderLeft: "5px solid #a78bfa", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: "0.68rem", color: "#a78bfa", fontWeight: 800, letterSpacing: 2, marginBottom: 4 }}>🎓 COACH DASHBOARD</div>
          <div style={{ fontSize: "0.9rem", color: "#f5f3ef", fontWeight: 700 }}>{coachProfiel?.naam || "Nieuw profiel"}</div>
        </div>
        <button style={btn("#1e293b", true)} onClick={() => setModus("klant")}>→ Atleet modus</button>
      </div>

      {melding && <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid #22c55e", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: "0.82rem", color: "#22c55e" }}>{melding}</div>}

      {/* Coach profiel */}
      <div style={card}>
        <div style={{ fontSize: "0.6rem", color: "#a78bfa", letterSpacing: 3, marginBottom: 14 }}>MIJN COACH PROFIEL</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
          {[["Naam", coachNaam, setCoachNaam, "Jouw naam"], ["Email", coachEmail, setCoachEmail, "coach@example.com"]].map(([lbl, val, set, ph]) => (
            <div key={lbl as string}>
              <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3, fontWeight: 700 }}>{lbl as string}</div>
              <input value={val as string} onChange={e => (set as any)(e.target.value)} placeholder={ph as string}
                style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem", outline: "none" }} />
            </div>
          ))}
        </div>
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3, fontWeight: 700 }}>SPECIALISATIE</div>
          <input value={coachSpec} onChange={e => setCoachSpec(e.target.value)} placeholder="bv. Duursport, triatlon, voedingscoaching"
            style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem", outline: "none" }} />
        </div>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 3, fontWeight: 700 }}>BIO</div>
          <textarea value={coachBio} onChange={e => setCoachBio(e.target.value)} rows={2} placeholder="Korte beschrijving..."
            style={{ width: "100%", padding: "8px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.85rem", outline: "none", resize: "none" as const }} />
        </div>
        <button onClick={slaCoachProfielOp} disabled={coachOpslaan} style={{ ...btn("#a78bfa"), width: "100%" }}>
          {coachOpslaan ? "⏳ Opslaan..." : "✓ Profiel opslaan"}
        </button>
      </div>

      {/* Invite link genereren */}
      {coachProfiel && (
        <div style={card}>
          <div style={{ fontSize: "0.6rem", color: "#a78bfa", letterSpacing: 3, marginBottom: 12 }}>KLANT UITNODIGEN</div>
          <div style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: 12 }}>
            Genereer een unieke link (7 dagen geldig). Stuur deze naar je atleet — hij/zij keurt de uitnodiging goed en stelt in wat jij mag zien.
          </div>
          <button onClick={genereerInvite} disabled={inviteLaden} style={{ ...btn("#a78bfa"), width: "100%", marginBottom: inviteLink ? 10 : 0 }}>
            {inviteLaden ? "⏳ Genereren..." : "🔗 Genereer invite link"}
          </button>
          {inviteLink && (
            <div style={{ background: "#141414", borderRadius: 8, padding: "10px 14px", display: "flex", gap: 8, alignItems: "center" }}>
              <div style={{ flex: 1, fontSize: "0.75rem", color: "#60a5fa", wordBreak: "break-all" as const }}>{inviteLink}</div>
              <button onClick={() => navigator.clipboard.writeText(inviteLink)} style={{ ...btn("#1e293b", true), flexShrink: 0 }}>📋 Kopieer</button>
            </div>
          )}
        </div>
      )}

      {/* Klanten lijst */}
      {mijnKlanten.length > 0 && (
        <div style={card}>
          <div style={{ fontSize: "0.6rem", color: "#a78bfa", letterSpacing: 3, marginBottom: 14 }}>MIJN ATLETEN ({mijnKlanten.length})</div>
          {mijnKlanten.map(klant => {
            const privacy = Array.isArray(klant.carboo_coach_privacy) ? klant.carboo_coach_privacy[0] : klant.carboo_coach_privacy
            const actief = gekozenKlant?.id === klant.id
            return (
              <div key={klant.id} style={{ background: actief ? "rgba(167,139,250,0.08)" : "#141414", borderRadius: 10, padding: "12px 14px", marginBottom: 8, border: actief ? "1px solid rgba(167,139,250,0.3)" : "1px solid #1e293b" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: actief ? 12 : 0 }}>
                  <div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f5f3ef" }}>Atleet {klant.klant_id.slice(0, 8)}...</div>
                    <div style={{ fontSize: "0.68rem", color: "#475569" }}>Lid sinds {new Date(klant.aangemaakt).toLocaleDateString("nl-BE")}</div>
                    <div style={{ display: "flex", gap: 4, marginTop: 4, flexWrap: "wrap" as const }}>
                      {privacy && Object.entries({
                        fuelc_dagschema: "Dagschema", fuelc_analyses: "Analyses",
                        race_plannen: "Race", train_gut: "Gut", dossier: "Dossier"
                      }).filter(([k]) => (privacy as any)[k]).map(([, lbl]) => (
                        <span key={lbl} style={{ fontSize: "0.6rem", background: "rgba(167,139,250,0.1)", color: "#a78bfa", padding: "1px 6px", borderRadius: 4 }}>{lbl}</span>
                      ))}
                    </div>
                  </div>
                  <button onClick={() => actief ? setGekozenKlant(null) : laadKlantData(klant)} style={btn("#a78bfa", true)}>
                    {actief ? "Sluiten" : "Bekijken →"}
                  </button>
                </div>

                {/* Klant detail */}
                {actief && (
                  <div>
                    {klantDataLaden ? (
                      <div style={{ color: "#a78bfa", fontSize: "0.82rem" }}>⏳ Data laden...</div>
                    ) : klantData ? (
                      <div>
                        {/* Tabs: data / opmerking / notitie */}
                        {(() => {
                          const [detailTab, setDetailTab] = useState<"data"|"opmerking"|"notitie">("data")
                          return (
                            <div>
                              <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
                                {(["data", "opmerking", "notitie"] as const).map(t => (
                                  <button key={t} style={pill(detailTab === t, "#a78bfa")} onClick={() => setDetailTab(t)}>
                                    {t === "data" ? "📊 Data" : t === "opmerking" ? "💬 Opmerking sturen" : "📝 Privé notitie"}
                                  </button>
                                ))}
                              </div>

                              {detailTab === "data" && (
                                <div>
                                  {klantData.dagschema && klantData.dagschema.length > 0 && (
                                    <div style={{ marginBottom: 10 }}>
                                      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 6, fontWeight: 700 }}>DAGSCHEMA (laatste 14 dagen)</div>
                                      {klantData.dagschema.slice(0, 5).map((dag: any) => (
                                        <div key={dag.datum} style={{ fontSize: "0.75rem", color: "#94a3b8", padding: "4px 0", borderBottom: "1px solid #1e293b" }}>
                                          {dag.datum} · {dag.naam} · {dag.kcal}kcal
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                  {klantData.race_plannen && klantData.race_plannen.length > 0 && (
                                    <div style={{ marginBottom: 10 }}>
                                      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 6, fontWeight: 700 }}>RACE PLANNEN</div>
                                      {klantData.race_plannen.map((r: any) => (
                                        <div key={r.id} style={{ fontSize: "0.75rem", color: "#94a3b8", padding: "4px 0", borderBottom: "1px solid #1e293b" }}>
                                          {r.naam} · {new Date(r.datum).toLocaleDateString("nl-BE")}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                  {klantData.gut_sessies && klantData.gut_sessies.length > 0 && (
                                    <div>
                                      <div style={{ fontSize: "0.65rem", color: "#64748b", marginBottom: 6, fontWeight: 700 }}>TRAIN THE GUT SESSIES</div>
                                      {klantData.gut_sessies.slice(0, 5).map((s: any) => (
                                        <div key={s.id} style={{ fontSize: "0.75rem", color: "#94a3b8", padding: "4px 0", borderBottom: "1px solid #1e293b" }}>
                                          {s.datum} · Week {s.week_nummer} · {s.duur_min}min · {s.intensiteit}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                  {!klantData.dagschema?.length && !klantData.race_plannen?.length && !klantData.gut_sessies?.length && (
                                    <div style={{ color: "#334155", fontSize: "0.78rem" }}>Geen data beschikbaar (check privacy instellingen van atleet).</div>
                                  )}
                                </div>
                              )}

                              {detailTab === "opmerking" && (
                                <div>
                                  <div style={{ marginBottom: 10 }}>
                                    <div style={{ fontSize: "0.62rem", color: "#64748b", marginBottom: 4, fontWeight: 700 }}>GELINKT AAN</div>
                                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" as const, marginBottom: 8 }}>
                                      {["algemeen", "dagschema", "race_plan", "gut_sessie", "analyse"].map(t => (
                                        <button key={t} style={pill(opmerkingItemType === t, "#a78bfa")} onClick={() => setOpmerkingItemType(t)}>{t}</button>
                                      ))}
                                    </div>
                                    {opmerkingItemType !== "algemeen" && (
                                      <input value={opmerkingItemLabel} onChange={e => setOpmerkingItemLabel(e.target.value)}
                                        placeholder="Beschrijving (bv. 'Dinsdag 6 mei' of 'Ironman plan')"
                                        style={{ width: "100%", padding: "8px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none", marginBottom: 8 }} />
                                    )}
                                  </div>
                                  <textarea value={nieuweOpmerking} onChange={e => setNieuweOpmerking(e.target.value)} rows={3}
                                    placeholder="Schrijf een opmerking voor je atleet..."
                                    style={{ width: "100%", padding: "10px 12px", background: "#0f172a", border: "1px solid #334155", borderRadius: 8, color: "#f5f3ef", fontSize: "0.85rem", outline: "none", resize: "none" as const, marginBottom: 8 }} />
                                  <button onClick={plaatsOpmerking} style={{ ...btn("#a78bfa"), width: "100%" }}>💬 Opmerking sturen</button>
                                </div>
                              )}

                              {detailTab === "notitie" && (
                                <div>
                                  <div style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.2)", borderRadius: 8, padding: "8px 12px", marginBottom: 10, fontSize: "0.72rem", color: "#fbbf24" }}>
                                    🔒 Privé notities zijn enkel voor jou zichtbaar. De atleet ziet deze nooit.
                                  </div>
                                  {notities.map((n: any) => (
                                    <div key={n.id} style={{ background: "#141414", borderRadius: 8, padding: "10px 12px", marginBottom: 6, fontSize: "0.78rem", color: "#94a3b8" }}>
                                      <div style={{ marginBottom: 3 }}>{n.tekst}</div>
                                      <div style={{ fontSize: "0.65rem", color: "#334155" }}>{new Date(n.aangemaakt).toLocaleDateString("nl-BE")}</div>
                                    </div>
                                  ))}
                                  <textarea value={notitie} onChange={e => setNotitie(e.target.value)} rows={3}
                                    placeholder="Privé notitie over deze atleet..."
                                    style={{ width: "100%", padding: "10px 12px", background: "#0f172a", border: "1px solid #334155", borderRadius: 8, color: "#f5f3ef", fontSize: "0.85rem", outline: "none", resize: "none" as const, marginBottom: 8 }} />
                                  <button onClick={slaNotitieOp} style={{ ...btn("#fbbf24"), width: "100%" }}>📝 Notitie opslaan</button>
                                </div>
                              )}
                            </div>
                          )
                        })()}
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {coachProfiel && mijnKlanten.length === 0 && (
        <div style={{ ...card, textAlign: "center" as const, padding: 32 }}>
          <div style={{ fontSize: "2rem", marginBottom: 10 }}>👥</div>
          <div style={{ color: "#94a3b8", marginBottom: 6 }}>Nog geen atleten</div>
          <div style={{ fontSize: "0.78rem", color: "#475569" }}>Genereer een invite link en stuur die naar je atleet.</div>
        </div>
      )}
    </div>
  )

  // ─── KLANT MODUS ──────────────────────────────────────────────────────────
  return (
    <div style={s}>
      <div style={{ background: "linear-gradient(135deg,#1e293b,#0f172a)", borderRadius: 16, padding: "18px 22px", marginBottom: 20, borderLeft: "5px solid #3b82f6", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: "0.68rem", color: "#3b82f6", fontWeight: 800, letterSpacing: 2, marginBottom: 4 }}>🏃 MIJN COACHES</div>
          <div style={{ fontSize: "0.88rem", color: "#94a3b8" }}>Beheer je coaches en privacy-instellingen</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {ongelezen > 0 && <span style={{ background: "#ef4444", color: "#fff", fontSize: "0.72rem", fontWeight: 700, padding: "2px 8px", borderRadius: 10 }}>{ongelezen} nieuw</span>}
          <button style={btn("#1e293b", true)} onClick={() => setModus("coach")}>→ Coach modus</button>
        </div>
      </div>

      {melding && <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid #22c55e", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: "0.82rem", color: "#22c55e" }}>{melding}</div>}

      {/* Opmerkingen van coaches */}
      {opmerkingen.length > 0 && (
        <div style={card}>
          <div style={{ fontSize: "0.6rem", color: "#3b82f6", letterSpacing: 3, marginBottom: 14 }}>
            OPMERKINGEN VAN COACH {ongelezen > 0 && <span style={{ background: "#ef4444", color: "#fff", fontSize: "0.6rem", padding: "1px 6px", borderRadius: 8, marginLeft: 6 }}>{ongelezen} ongelezen</span>}
          </div>
          {opmerkingen.slice(0, 10).map(opm => (
            <div key={opm.id} style={{ background: opm.gelezen ? "#141414" : "rgba(59,130,246,0.05)", borderRadius: 10, padding: "12px 14px", marginBottom: 8, border: opm.gelezen ? "1px solid #1e293b" : "1px solid rgba(59,130,246,0.3)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: "0.72rem", color: "#3b82f6", fontWeight: 700 }}>{opm.carboo_coaches?.naam || "Coach"}</span>
                  {opm.item_label && <span style={{ fontSize: "0.65rem", color: "#475569", background: "#1e293b", padding: "1px 6px", borderRadius: 4 }}>{opm.item_type}: {opm.item_label}</span>}
                  {!opm.gelezen && <span style={{ fontSize: "0.6rem", background: "#ef4444", color: "#fff", padding: "1px 5px", borderRadius: 4 }}>Nieuw</span>}
                </div>
                <span style={{ fontSize: "0.65rem", color: "#334155" }}>{new Date(opm.aangemaakt).toLocaleDateString("nl-BE")}</span>
              </div>
              <div style={{ fontSize: "0.85rem", color: "#f5f3ef", lineHeight: 1.5, marginBottom: 8 }}>{opm.tekst}</div>

              {/* Reacties */}
              {(opm.carboo_coach_reacties || []).map(r => (
                <div key={r.id} style={{ background: "#0f172a", borderRadius: 6, padding: "6px 10px", marginBottom: 4, fontSize: "0.75rem", color: "#94a3b8", borderLeft: "2px solid #3b82f6" }}>
                  {r.tekst}
                </div>
              ))}

              <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                {!opm.gelezen && (
                  <button onClick={() => markeerGelezen(opm.id)} style={btn("#1e293b", true)}>✓ Gelezen</button>
                )}
                <input value={reactieTekst[opm.id] || ""} onChange={e => setReactieTekst(prev => ({ ...prev, [opm.id]: e.target.value }))}
                  placeholder="Reageer..."
                  style={{ flex: 1, padding: "5px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.78rem", outline: "none" }} />
                <button onClick={() => plaatsReactie(opm.id)} style={btn("#3b82f6", true)}>→</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Mijn coaches */}
      {mijnCoaches.length === 0 ? (
        <div style={{ ...card, textAlign: "center" as const, padding: 32 }}>
          <div style={{ fontSize: "2rem", marginBottom: 10 }}>🎓</div>
          <div style={{ color: "#94a3b8", marginBottom: 6 }}>Nog geen coach gekoppeld</div>
          <div style={{ fontSize: "0.78rem", color: "#475569" }}>
            Vraag je coach om een invite link te genereren via Carboo. Na acceptatie bepaal jij wat hij mag zien.
          </div>
        </div>
      ) : (
        mijnCoaches.map(rel => {
          const privacy = privacyMap[rel.id] || { fuelc_dagschema: true, fuelc_analyses: false, race_plannen: true, train_gut: false, dossier: false }
          const coach = rel.carboo_coaches
          return (
            <div key={rel.id} style={card}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f5f3ef", marginBottom: 3 }}>🎓 {coach.naam}</div>
                  {coach.specialisatie && <div style={{ fontSize: "0.72rem", color: "#60a5fa", marginBottom: 2 }}>{coach.specialisatie}</div>}
                  {coach.bio && <div style={{ fontSize: "0.72rem", color: "#475569" }}>{coach.bio}</div>}
                </div>
                <button onClick={() => verwijderCoach(rel.id)} style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "0.72rem" }}>Toegang intrekken</button>
              </div>

              <div style={{ fontSize: "0.6rem", color: "#64748b", letterSpacing: 2, marginBottom: 10, fontWeight: 700 }}>WAT MAG DEZE COACH ZIEN?</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {[
                  { veld: "fuelc_dagschema" as keyof Privacy, label: "🍽️ FuelC — Dagschema", sub: "Maaltijden en porties" },
                  { veld: "fuelc_analyses" as keyof Privacy, label: "📊 FuelC — Analyses", sub: "Scores en voedingskwaliteit" },
                  { veld: "race_plannen" as keyof Privacy, label: "🏁 Race plannen", sub: "Rapporten en schema's" },
                  { veld: "train_gut" as keyof Privacy, label: "🍽️ Train the Gut", sub: "Sessies en winkelmandje" },
                  { veld: "dossier" as keyof Privacy, label: "📁 Mijn Dossier", sub: "Opgeslagen rapporten" },
                ].map(item => {
                  const aan = privacy[item.veld]
                  return (
                    <div key={item.veld} onClick={() => updatePrivacy(rel.id, item.veld, !aan)}
                      style={{ background: aan ? "rgba(59,130,246,0.08)" : "#141414", border: `1px solid ${aan ? "rgba(59,130,246,0.3)" : "#1e293b"}`, borderRadius: 8, padding: "10px 12px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{ fontSize: "0.75rem", color: aan ? "#60a5fa" : "#475569", fontWeight: 600 }}>{item.label}</div>
                        <div style={{ fontSize: "0.65rem", color: "#334155" }}>{item.sub}</div>
                      </div>
                      <div style={{ width: 36, height: 20, borderRadius: 10, background: aan ? "#3b82f6" : "#334155", position: "relative" as const, transition: "background 0.2s", flexShrink: 0 }}>
                        <div style={{ position: "absolute" as const, top: 2, left: aan ? 18 : 2, width: 16, height: 16, borderRadius: "50%", background: "#fff", transition: "left 0.2s" }} />
                      </div>
                    </div>
                  )
                })}
              </div>
              <div style={{ fontSize: "0.65rem", color: "#334155", marginTop: 8, textAlign: "center" as const }}>
                Klik op een module om toegang aan/uit te zetten. Wijzigingen zijn meteen van kracht.
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
