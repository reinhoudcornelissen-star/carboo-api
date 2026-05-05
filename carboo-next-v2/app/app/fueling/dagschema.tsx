"use client"
import type { NevoProduct } from "./nevo-data"
import { useState, useEffect, useMemo, useRef } from "react"

const API = "https://carboo-api.onrender.com"

import { NEVO as NEVO_SNEL } from "./nevo-data"

interface DagItem { id: string; moment: number; naam: string; hoeveelheid_g: number; kcal: number; kh_g: number; eiwit_g: number; vet_g: number; vezels_g: number }

type Product = NevoProduct

function calc(p: Product, g: number) {
  const f = g / 100
  const r = (v?: number) => v !== undefined ? Math.round(v * f * 10) / 10 : 0
  return {
    kcal: Math.round(p.kcal * f),
    kh_g: Math.round(p.kh * f * 10) / 10,
    eiwit_g: Math.round(p.eiwit * f * 10) / 10,
    vet_g: Math.round(p.vet * f * 10) / 10,
    vezels_g: Math.round(p.vezels * f * 10) / 10,
    suikers_g: r(p.suikers),
    verz_g: r(p.verz), kalium_mg: r(p.kalium), calcium_mg: r(p.calcium),
    ijzer_mg: r(p.ijzer), vitd_mcg: r(p.vitd), vitb12_mcg: r(p.vitb12), omega3_g: r(p.omega3),
  }
}

function datumLabel(datum: string) {
  const vandaag = new Date().toISOString().split("T")[0]
  const gisteren = new Date(Date.now() - 86400000).toISOString().split("T")[0]
  const morgen = new Date(Date.now() + 86400000).toISOString().split("T")[0]
  if (datum === vandaag) return "Vandaag"
  if (datum === gisteren) return "Gisteren"
  if (datum === morgen) return "Morgen"
  return new Date(datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "long", day: "numeric", month: "short" })
}

export default function Dagschema({ profiel, token }: { profiel: any; token: string | null }) {
  const [datum, setDatum] = useState(new Date().toISOString().split("T")[0])
  const [items, setItems] = useState<DagItem[]>([])
  const [eigenProducten, setEigenProducten] = useState<Product[]>([])
  const [recent, setRecent] = useState<Product[]>([])
  const [actieveMoment, setActieveMoment] = useState<number | null>(null)
  const [zoek, setZoek] = useState("")
  const [gekozenProduct, setGekozenProduct] = useState<Product | null>(null)
  const [portie, setPortie] = useState(100)
  const [opslaan, setOpslaan] = useState(false)
  const [fout, setFout] = useState("")
  const [sjablonen, setSjablonen] = useState<any[]>([])
  const [toonSjabloonForm, setToonSjabloonForm] = useState(false)
  const [sjabloonNaam, setSjabloonNaam] = useState("")
  const [trainingsKcal, setTrainingsKcal] = useState(0)
  const [trainingsInfo, setTrainingsInfo] = useState("")
  const [dagTrainingen, setDagTrainingen] = useState<any[]>([])
  const [recepten, setRecepten] = useState<any[]>([])
  const zoekRef = useRef<HTMLInputElement>(null)

  const energieBasis = profiel?.energie_doel || 2000
  const energieDoel = energieBasis + trainingsKcal
  const khDoel = Math.round(energieDoel * (profiel?.kh_doel_pct || 50) / 100 / 4)
  const eiwitDoel = Math.round(energieDoel * (profiel?.eiwit_doel_pct || 25) / 100 / 4)
  const vetDoel = Math.round(energieDoel * (profiel?.vet_doel_pct || 25) / 100 / 9)

  const eetpatroon = profiel?.eet_patroon || "Klassiek (3 maaltijden)"
  const aantalTuss = (profiel?.tussendoortjes != null) ? profiel.tussendoortjes : 3

  const momenten = useMemo(() => {
    if (eetpatroon.includes("fasting")) return ["Eerste maaltijd", "Tweede maaltijd", "Derde maaltijd"]
    const result = ["Ontbijt"]
    if (aantalTuss >= 1) result.push("Voormiddag")
    result.push("Lunch")
    if (aantalTuss >= 2) result.push("Namiddag")
    result.push("Avondmaal")
    if (aantalTuss >= 3) result.push("Avondtussendoortje")
    return result
  }, [eetpatroon, aantalTuss])

  const tijden = useMemo(() => {
    try { return profiel?.momenten_tijden ? JSON.parse(profiel.momenten_tijden) : {} } catch { return {} }
  }, [profiel])

  // Recepten als product voor dagschema
  const receptAlsProduct = useMemo(() => recepten.map((r: any) => {
    const ing = r.ingredienten || []
    const porties = r.aantal_porties || 1
    const tot = (veld: string) => ing.reduce((a: number, i: any) => a + (i[veld] || 0) * (i.hoeveelheid_g / 100), 0)
    return {
      id: "recept_" + r.id, naam: "🍽 " + r.naam,
      portie_g: Math.max(1, Math.round(ing.reduce((a: number, i: any) => a + i.hoeveelheid_g, 0) / porties)),
      portie_label: `1 portie`,
      kcal: Math.round(tot("kcal") / porties),
      kh: Math.round(tot("kh") / porties * 10) / 10,
      eiwit: Math.round(tot("eiwit") / porties * 10) / 10,
      vet: Math.round(tot("vet") / porties * 10) / 10,
      vezels: Math.round(tot("vezels") / porties * 10) / 10,
      suikers: 0, verz: 0, kalium: 0, calcium: 0, ijzer: 0, vitd: 0, vitb12: 0, omega3: 0,
    }
  }), [recepten])

  const alleProducten = useMemo(() => [...NEVO_SNEL, ...eigenProducten, ...receptAlsProduct], [eigenProducten, receptAlsProduct])

  const zoekResultaten = useMemo(() => {
    if (!zoek || zoek.length < 2) return []
    return alleProducten.filter(p => p.naam.toLowerCase().includes(zoek.toLowerCase())).slice(0, 8)
  }, [zoek, alleProducten])

  // Laad bibliotheek bij mount
  useEffect(() => {
    if (!token) return
    try {
      setSjablonen(JSON.parse(localStorage.getItem("carboo_sjablonen") || "[]"))
      setRecent(JSON.parse(localStorage.getItem("carboo_recent") || "[]"))
    } catch (_) {}
    async function laadBib() {
      try {
        const [bibData, recData] = await Promise.all([
          fetch(`${API}/api/fuelc/bibliotheek`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
          fetch(`${API}/api/fuelc/recepten`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => ({ recepten: [] })),
        ])
        setEigenProducten((bibData.producten || []).map((p: any) => ({
          id: p.id, naam: p.naam,
          portie_g: p.portie_g || 100, portie_label: p.portie_label || "100g",
          kcal: p.kcal_100g || 0, kh: p.kh_100g || 0,
          eiwit: p.eiwit_100g || 0, vet: p.vet_100g || 0, vezels: p.vezels_100g || 0,
          suikers: p.suikers_100g || 0, verz: p.verzadigd_100g || 0,
          kalium: p.kalium_100g || 0, calcium: p.calcium_100g || 0,
          ijzer: p.ijzer_100g || 0, vitd: p.vitd_100g || 0, vitb12: p.vitb12_100g || 0, omega3: p.omega3_100g || 0,
        })))
        setRecepten(recData.recepten || [])
      } catch (_) {}
    }
    laadBib()
  }, [token])

  // Laad dagboek + trainingen parallel bij datum-wijziging
  useEffect(() => {
    if (!token) return
    Promise.all([
      fetch(`${API}/api/fuelc/dagboek/${datum}`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json()).catch(() => ({ items: [] })),
      fetch(`${API}/api/fuelc/trainingen`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json()).catch(() => ({ trainingen: [] })),
    ]).then(([dagboek, tr]) => {
      setItems(dagboek.items || [])
      const dagTr = (tr.trainingen || []).filter((t: any) => (t.datum || "").slice(0, 10) === datum)
      const kcal = dagTr.reduce((a: number, t: any) => a + (t.kcal_verbranding || 0), 0)
      const sporten = [...new Set(dagTr.map((t: any) => t.sport))].join(", ")
      setTrainingsKcal(kcal)
      setTrainingsInfo(kcal > 0 ? `🏃 ${sporten} +${kcal} kcal` : "")
      setDagTrainingen(dagTr)
    })
  }, [datum, token])

  function navigeer(delta: number) {
    const d = new Date(datum + "T12:00:00")
    d.setDate(d.getDate() + delta)
    setDatum(d.toISOString().split("T")[0])
    setActieveMoment(null)
    setGekozenProduct(null)
    setZoek("")
  }

  function openMoment(idx: number) {
    if (actieveMoment === idx) {
      setActieveMoment(null)
    } else {
      setActieveMoment(idx)
      setGekozenProduct(null)
      setZoek("")
      setTimeout(() => zoekRef.current?.focus(), 150)
    }
  }

  function kiesProduct(p: Product) {
    setGekozenProduct(p)
    setPortie(p.portie_g)
    setZoek("")
    setFout("")
  }

  async function voegToe() {
    if (!gekozenProduct || actieveMoment === null || !token) return
    setOpslaan(true)
    setFout("")
    const waarden = calc(gekozenProduct, portie)
    try {
      // Stuur exact de veldnamen die de API verwacht
      const payload = {
        datum,
        moment: actieveMoment,
        naam: gekozenProduct.naam,
        hoeveelheid_g: portie,
        kcal: waarden.kcal,
        kh_g: waarden.kh_g,
        eiwit_g: waarden.eiwit_g,
        vet_g: waarden.vet_g,
        vezels_g: waarden.vezels_g,
        suikers_g: waarden.suikers_g || 0,
        verz_g: waarden.verz_g || 0,
        kalium_mg: waarden.kalium_mg || 0,
        calcium_mg: waarden.calcium_mg || 0,
        ijzer_mg: waarden.ijzer_mg || 0,
        vitd_mcg: waarden.vitd_mcg || 0,
        vitb12_mcg: waarden.vitb12_mcg || 0,
        omega3_g: waarden.omega3_g || 0,
      }
      const res = await fetch(`${API}/api/fuelc/dagboek`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        const errTekst = await res.text().catch(() => "")
        throw new Error(`HTTP ${res.status}: ${errTekst.slice(0, 150)}`)
      }
      // Herlaad dagboek
      const d = await fetch(`${API}/api/fuelc/dagboek/${datum}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())
      setItems(d.items || [])
      // Sla op in recent
      const nieuweRecent = [gekozenProduct, ...recent.filter(r => r.id !== gekozenProduct!.id)].slice(0, 8)
      setRecent(nieuweRecent)
      try { localStorage.setItem("carboo_recent", JSON.stringify(nieuweRecent)) } catch (_) {}
      setGekozenProduct(null)
      setZoek("")
    } catch (e: any) {
      setFout(`Fout: ${e.message}`)
    } finally {
      setOpslaan(false)
    }
  }

  async function verwijder(id: string) {
    try {
      await fetch(`${API}/api/fuelc/dagboek/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
      setItems(prev => prev.filter(i => i.id !== id))
    } catch {}
  }

  async function kopieerGisteren() {
    if (!token) return
    const gisD = new Date(Date.now() - 86400000).toISOString().split("T")[0]
    try {
      const d = await fetch(`${API}/api/fuelc/dagboek/${gisD}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())
      for (const item of (d.items || [])) {
        await fetch(`${API}/api/fuelc/dagboek`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            datum, moment: item.moment, naam: item.naam,
            hoeveelheid_g: item.hoeveelheid_g,
            kcal: item.kcal, kh_g: item.kh_g,
            eiwit_g: item.eiwit_g, vet_g: item.vet_g, vezels_g: item.vezels_g || 0,
          })
        })
      }
      const nieuw = await fetch(`${API}/api/fuelc/dagboek/${datum}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())
      setItems(nieuw.items || [])
    } catch {}
  }

  function slaanSjabloonOp() {
    if (!sjabloonNaam.trim() || items.length === 0) return
    const nieuw = { naam: sjabloonNaam.trim(), items: items.map(i => ({
      moment: i.moment, naam: i.naam, hoeveelheid_g: i.hoeveelheid_g,
      kcal: i.kcal, kh_g: i.kh_g, eiwit_g: i.eiwit_g, vet_g: i.vet_g, vezels_g: i.vezels_g || 0
    }))}
    const lijst = [...sjablonen, nieuw]
    setSjablonen(lijst)
    try { localStorage.setItem("carboo_sjablonen", JSON.stringify(lijst)) } catch (_) {}
    setSjabloonNaam("")
    setToonSjabloonForm(false)
  }

  async function laadSjabloon(sj: any) {
    if (!token) return
    for (const item of (sj.items || [])) {
      const moment = actieveMoment !== null ? actieveMoment : item.moment
      await fetch(`${API}/api/fuelc/dagboek`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          datum, moment, naam: item.naam,
          hoeveelheid_g: item.hoeveelheid_g,
          kcal: item.kcal, kh_g: item.kh_g,
          eiwit_g: item.eiwit_g, vet_g: item.vet_g, vezels_g: item.vezels_g || 0,
        })
      })
    }
    const d = await fetch(`${API}/api/fuelc/dagboek/${datum}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())
    setItems(d.items || [])
  }

  function verwijderSjabloon(idx: number) {
    const lijst = sjablonen.filter((_, i) => i !== idx)
    setSjablonen(lijst)
    try { localStorage.setItem("carboo_sjablonen", JSON.stringify(lijst)) } catch (_) {}
  }

  const totalen = items.reduce((acc, i) => ({
    kcal: acc.kcal + i.kcal, kh: acc.kh + i.kh_g, eiwit: acc.eiwit + i.eiwit_g, vet: acc.vet + i.vet_g
  }), { kcal: 0, kh: 0, eiwit: 0, vet: 0 })

  const pctKleur = (w: number, d: number) => {
    const p = w / Math.max(d, 1)
    return p > 1.05 ? "#ef4444" : p > 0.8 ? "#22c55e" : p > 0.4 ? "#f97316" : "#3b82f6"
  }

  const previewWaarden = gekozenProduct ? calc(gekozenProduct, portie) : null

  return (
    <div style={{ maxWidth: 640, margin: "0 auto" }}>

      {/* Datum navigator */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <button onClick={() => navigeer(-1)} style={{ background: "#1e293b", border: "none", color: "#64748b", borderRadius: 8, padding: "10px 16px", cursor: "pointer", fontSize: "1.1rem" }}>←</button>
        <div style={{ flex: 1, textAlign: "center" }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: "1.4rem", color: "#f5f3ef", letterSpacing: 1 }}>{datumLabel(datum)}</div>
          <div style={{ fontSize: "0.68rem", color: "#475569" }}>{new Date(datum + "T12:00:00").toLocaleDateString("nl-BE", { weekday: "long", day: "numeric", month: "long" })}</div>
        </div>
        <button onClick={() => navigeer(1)} style={{ background: "#1e293b", border: "none", color: "#64748b", borderRadius: 8, padding: "10px 16px", cursor: "pointer", fontSize: "1.1rem" }}>→</button>
      </div>

      {/* Dagdoelen */}
      <div style={{ background: "#0f172a", borderRadius: 12, padding: "14px 16px", marginBottom: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 10 }}>
          {[
            { l: "Kcal", w: Math.round(totalen.kcal), d: energieDoel, e: "" },
            { l: "KH", w: Math.round(totalen.kh), d: khDoel, e: "g" },
            { l: "Eiwit", w: Math.round(totalen.eiwit), d: eiwitDoel, e: "g" },
            { l: "Vet", w: Math.round(totalen.vet), d: vetDoel, e: "g" },
          ].map(k => (
            <div key={k.l} style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.56rem", color: "#475569", marginBottom: 2 }}>{k.l}</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 800, color: pctKleur(k.w, k.d) }}>{k.w}</div>
              <div style={{ fontSize: "0.56rem", color: "#334155" }}>/ {k.d}{k.e}</div>
              <div style={{ background: "#1e293b", borderRadius: 3, height: 3, marginTop: 4 }}>
                <div style={{ width: `${Math.min(100, Math.round(k.w / Math.max(k.d, 1) * 100))}%`, height: "100%", background: pctKleur(k.w, k.d), borderRadius: 3 }} />
              </div>
            </div>
          ))}
        </div>

        {/* Training info */}
        {trainingsInfo && (
          <div style={{ fontSize: "0.72rem", color: "#22c55e", marginBottom: 8, padding: "4px 8px", background: "rgba(34,197,94,0.08)", borderRadius: 6, display: "inline-block" }}>
            {trainingsInfo} · Totaal doel: {energieDoel} kcal
          </div>
        )}

        {/* Acties */}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <button onClick={kopieerGisteren} style={{ fontSize: "0.72rem", color: "#64748b", background: "#1e293b", border: "none", borderRadius: 6, padding: "5px 10px", cursor: "pointer" }}>
            📋 Kopieer gisteren
          </button>
          <button onClick={() => setToonSjabloonForm(!toonSjabloonForm)} style={{ fontSize: "0.72rem", color: "#64748b", background: "#1e293b", border: "none", borderRadius: 6, padding: "5px 10px", cursor: "pointer" }}>
            💾 Sla dag op
          </button>
          {sjablonen.length > 0 && (
            <select defaultValue="" onChange={e => { const i = parseInt(e.target.value); if (!isNaN(i)) laadSjabloon(sjablonen[i]); e.currentTarget.value = "" }}
              style={{ fontSize: "0.72rem", color: "#64748b", background: "#1e293b", border: "none", borderRadius: 6, padding: "5px 10px", cursor: "pointer" }}>
              <option value="" disabled>📂 Laad sjabloon...</option>
              {sjablonen.map((s, i) => <option key={i} value={i}>{s.naam} ({s.items?.length || 0} items)</option>)}
            </select>
          )}
        </div>

        {toonSjabloonForm && (
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <input value={sjabloonNaam} onChange={e => setSjabloonNaam(e.target.value)} placeholder="Naam sjabloon..." onKeyDown={e => e.key === "Enter" && slaanSjabloonOp()}
              style={{ flex: 1, padding: "7px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f5f3ef", fontSize: "0.82rem", outline: "none" }} />
            <button onClick={slaanSjabloonOp} style={{ padding: "7px 14px", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 700, fontSize: "0.78rem" }}>Opslaan</button>
            <button onClick={() => setToonSjabloonForm(false)} style={{ padding: "7px 10px", background: "transparent", border: "1px solid #2a2a2a", color: "#555", borderRadius: 6, cursor: "pointer" }}>✕</button>
          </div>
        )}
      </div>

      {/* Maaltijdmomenten */}
      {momenten.map((mom, midx) => {
        const momItems = items.filter(i => i.moment === midx)
        const momKcal = Math.round(momItems.reduce((a, i) => a + i.kcal, 0))
        const isActief = actieveMoment === midx

        return (
          <div key={mom} style={{ marginBottom: 8 }}>

            {/* Header */}
            <div onClick={() => openMoment(midx)} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "12px 16px", cursor: "pointer",
              borderRadius: isActief ? "10px 10px 0 0" : 10,
              background: isActief ? "#1e3a5f" : "#1e293b",
              border: "1px solid " + (isActief ? "#3b82f6" : "#2a2a2a"),
              transition: "all 0.15s",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontWeight: 700, color: "#f5f3ef", fontSize: "0.9rem" }}>{mom}</span>
                {tijden[mom] && <span style={{ fontSize: "0.68rem", color: "#475569" }}>{tijden[mom]}</span>}
                {momItems.length > 0 && <span style={{ fontSize: "0.65rem", color: "#64748b" }}>{momItems.length} item{momItems.length > 1 ? "s" : ""}</span>}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {momKcal > 0 && <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#f97316" }}>{momKcal} kcal</span>}
                <span style={{ color: isActief ? "#3b82f6" : "#475569", fontSize: "1.1rem", lineHeight: 1 }}>{isActief ? "−" : "+"}</span>
              </div>
            </div>

            {/* Items */}
            {momItems.length > 0 && (
              <div style={{ background: "#141414", border: "1px solid #2a2a2a", borderTop: "none", borderRadius: isActief ? 0 : "0 0 10px 10px" }}>
                {momItems.map(item => (
                  <div key={item.id} style={{ display: "flex", alignItems: "center", padding: "9px 14px", borderBottom: "1px solid #1e293b" }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: "0.84rem", color: "#f5f3ef", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.naam}</div>
                      <div style={{ fontSize: "0.65rem", color: "#475569" }}>{item.hoeveelheid_g}g · KH {item.kh_g}g · E {item.eiwit_g}g · V {item.vet_g}g</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f97316" }}>{item.kcal} kcal</span>
                      <button onClick={() => verwijder(item.id)} style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "1rem", padding: 0 }}>✕</button>
                    </div>
                  </div>
                ))}
                {/* Subtotaal moment + dagdeel opslaan */}
                <div style={{ padding: "6px 14px", fontSize: "0.72rem", color: "#475569", display: "flex", gap: 12, alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", gap: 12 }}>
                    <span style={{ color: "#f97316", fontWeight: 700 }}>{momKcal} kcal</span>
                    <span>KH {Math.round(momItems.reduce((a,i)=>a+i.kh_g,0))}g</span>
                    <span>E {Math.round(momItems.reduce((a,i)=>a+i.eiwit_g,0))}g</span>
                    <span>V {Math.round(momItems.reduce((a,i)=>a+i.vet_g,0))}g</span>
                  </div>
                  <button onClick={() => {
                    const naam = `${mom} - ${new Date(datum+"T12:00:00").toLocaleDateString("nl-BE",{day:"numeric",month:"short"})}`
                    const dagdeelItems = momItems.map(i => ({
                      moment: midx, naam: i.naam, hoeveelheid_g: i.hoeveelheid_g,
                      kcal: i.kcal, kh_g: i.kh_g, eiwit_g: i.eiwit_g, vet_g: i.vet_g, vezels_g: i.vezels_g || 0
                    }))
                    const nieuw = { naam, items: dagdeelItems }
                    const lijst = [...sjablonen, nieuw]
                    setSjablonen(lijst)
                    try { localStorage.setItem("carboo_sjablonen", JSON.stringify(lijst)) } catch(_) {}
                    alert(`✓ "${naam}" opgeslagen als sjabloon`)
                  }}
                    style={{ fontSize: "0.65rem", color: "#64748b", background: "#0f172a", border: "none", borderRadius: 5, padding: "3px 8px", cursor: "pointer" }}>
                    💾 Sla {mom} op
                  </button>
                </div>
              </div>
            )}

            {/* Toevoegpaneel */}
            {isActief && (
              <div style={{ background: "#0f172a", border: "1px solid #3b82f6", borderTop: "none", borderRadius: "0 0 10px 10px", padding: 16 }}>

                {fout && (
                  <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "8px 12px", marginBottom: 12, fontSize: "0.78rem", color: "#ef4444" }}>
                    ⚠️ {fout}
                  </div>
                )}

                {!gekozenProduct ? (
                  <div>
                    <input ref={zoekRef} value={zoek} onChange={e => setZoek(e.target.value)} placeholder="🔍 Zoek product..."
                      style={{ width: "100%", padding: "11px 14px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem", outline: "none", marginBottom: 10 }} />

                    {zoek.length >= 2 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                        {zoekResultaten.length === 0 ? (
                          <div style={{ fontSize: "0.78rem", color: "#475569", textAlign: "center", padding: 10 }}>Geen resultaten voor "{zoek}"</div>
                        ) : zoekResultaten.map(p => (
                          <div key={p.id} onClick={() => kiesProduct(p)}
                            style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px", background: "#1e293b", borderRadius: 8, cursor: "pointer", border: "1px solid #2a2a2a" }}>
                            <div>
                              <div style={{ fontSize: "0.85rem", color: "#f5f3ef", fontWeight: 500 }}>{p.naam}</div>
                              <div style={{ fontSize: "0.65rem", color: "#475569" }}>{p.portie_label} · {p.kcal} kcal · KH {p.kh}g · E {p.eiwit}g</div>
                            </div>
                            <div style={{ fontSize: "0.9rem", color: "#f97316", fontWeight: 700, alignSelf: "center" }}>+</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div>
                        {recent.length > 0 && (
                          <>
                            <div style={{ fontSize: "0.6rem", color: "#475569", letterSpacing: 2, marginBottom: 8 }}>RECENT GEBRUIKT</div>
                            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
                              {recent.slice(0, 8).map(p => (
                                <button key={p.id} onClick={() => kiesProduct(p)}
                                  style={{ padding: "6px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 20, color: "#94a3b8", cursor: "pointer", fontSize: "0.75rem" }}>
                                  {p.naam}
                                </button>
                              ))}
                            </div>
                          </>
                        )}
                        <div style={{ fontSize: "0.6rem", color: "#475569", letterSpacing: 2, marginBottom: 8 }}>SNEL KIEZEN</div>
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                          {NEVO_SNEL.slice(0, 12).map(p => (
                            <button key={p.id} onClick={() => kiesProduct(p)}
                              style={{ padding: "5px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 20, color: "#64748b", cursor: "pointer", fontSize: "0.72rem" }}>
                              {p.naam}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                      <div>
                        <div style={{ fontWeight: 700, color: "#f5f3ef", fontSize: "0.95rem" }}>{gekozenProduct.naam}</div>
                        <div style={{ fontSize: "0.65rem", color: "#475569", marginTop: 2 }}>Standaard: {gekozenProduct.portie_label}</div>
                      </div>
                      <button onClick={() => { setGekozenProduct(null); setZoek("") }}
                        style={{ fontSize: "0.75rem", color: "#64748b", background: "none", border: "none", cursor: "pointer" }}>
                        ← Ander product
                      </button>
                    </div>

                    {/* Portie slider */}
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                        <input type="range" min={5} max={500} value={portie} onChange={e => setPortie(Number(e.target.value))}
                          style={{ flex: 1, accentColor: "#f97316" }} />
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <input type="number" value={portie} onChange={e => setPortie(Math.max(1, Number(e.target.value)))} min={1}
                            style={{ width: 56, padding: "6px 8px", background: "#1e293b", border: "1px solid #f97316", borderRadius: 8, color: "#f97316", fontSize: "1rem", fontWeight: 800, textAlign: "center", outline: "none" }} />
                          <span style={{ fontSize: "0.72rem", color: "#64748b" }}>g</span>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {[
                          { l: gekozenProduct.portie_label, g: gekozenProduct.portie_g },
                          { l: "50g", g: 50 }, { l: "100g", g: 100 }, { l: "150g", g: 150 }, { l: "200g", g: 200 },
                        ].map((btn, bi) => (
                          <button key={bi} onClick={() => setPortie(btn.g)}
                            style={{ padding: "4px 10px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: "0.7rem", fontWeight: 600, background: portie === btn.g ? "#f97316" : "#1e293b", color: portie === btn.g ? "#0c0c0c" : "#64748b" }}>
                            {btn.l}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Preview */}
                    {previewWaarden && (
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, marginBottom: 14 }}>
                        {[
                          { l: "Kcal", v: previewWaarden.kcal, k: "#f97316" },
                          { l: "KH", v: previewWaarden.kh_g + "g", k: "#22c55e" },
                          { l: "Eiwit", v: previewWaarden.eiwit_g + "g", k: "#3b82f6" },
                          { l: "Vet", v: previewWaarden.vet_g + "g", k: "#fbbf24" },
                        ].map(m => (
                          <div key={m.l} style={{ background: "#1e293b", borderRadius: 8, padding: "8px", textAlign: "center" }}>
                            <div style={{ fontSize: "0.56rem", color: "#64748b", marginBottom: 2 }}>{m.l}</div>
                            <div style={{ fontSize: "0.95rem", fontWeight: 800, color: m.k }}>{m.v}</div>
                          </div>
                        ))}
                      </div>
                    )}

                    <button onClick={voegToe} disabled={opslaan} style={{
                      width: "100%", padding: "13px 0",
                      background: opslaan ? "#334155" : "#f97316",
                      color: "#0c0c0c", border: "none", borderRadius: 10,
                      cursor: opslaan ? "not-allowed" : "pointer",
                      fontFamily: "'Bebas Neue', sans-serif", fontSize: "1rem", letterSpacing: 1, fontWeight: 700,
                    }}>
                      {opslaan ? "Opslaan..." : `✓ TOEVOEGEN AAN ${mom.toUpperCase()}`}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}

      {/* Trainingsvoeding — alleen tonen als er een training is vandaag */}
      {dagTrainingen.length > 0 && (
        <div style={{ marginTop: 16, background: "#0f172a", border: "1px solid rgba(249,115,22,0.3)", borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: "0.6rem", color: "#f97316", letterSpacing: 2, marginBottom: 12 }}>🚴 VOEDING TIJDENS TRAINING</div>
          {dagTrainingen.map((tr: any, ti: number) => {
            const sport = tr.sport || "Training"
            const duur = tr.duur_min || 0
            const kcalTr = tr.kcal_verbranding || 0
            // Aanbevolen KH tijdens inspanning: 30-60g/uur
            const urenTr = duur / 60
            const khMin = Math.round(30 * urenTr)
            const khMax = Math.round(60 * urenTr)
            const momentNr = 99 + ti // apart moment voor trainingsvoeding
            const trItems = items.filter((i: any) => i.moment === momentNr)
            const trKcal = trItems.reduce((a: number, i: any) => a + (i.kcal || 0), 0)
            const trKh = trItems.reduce((a: number, i: any) => a + (i.kh_g || 0), 0)
            const isActief = actieveMoment === momentNr
            return (
              <div key={ti} style={{ marginBottom: ti < dagTrainingen.length - 1 ? 14 : 0 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div>
                    <div style={{ fontSize: "0.82rem", color: "#f5f3ef", fontWeight: 600 }}>
                      {sport} · {duur} min · {kcalTr} kcal
                    </div>
                    <div style={{ fontSize: "0.68rem", color: "#64748b" }}>
                      Aanbevolen: {khMin}–{khMax}g KH/uur tijdens inspanning
                    </div>
                  </div>
                  <button
                    onClick={() => setActieveMoment(isActief ? null : momentNr)}
                    style={{ fontSize: "0.72rem", background: isActief ? "rgba(249,115,22,0.15)" : "#1e293b", color: isActief ? "#f97316" : "#94a3b8", border: `1px solid ${isActief ? "rgba(249,115,22,0.4)" : "#2a2a2a"}`, borderRadius: 8, padding: "6px 12px", cursor: "pointer" }}>
                    + Voeding
                  </button>
                </div>

                {/* Reeds ingevoerde trainingsvoeding */}
                {trItems.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    {trItems.map((item: any) => (
                      <div key={item.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 10px", background: "#1e293b", borderRadius: 6, marginBottom: 4 }}>
                        <div>
                          <span style={{ fontSize: "0.8rem", color: "#f5f3ef" }}>{item.naam}</span>
                          <span style={{ fontSize: "0.65rem", color: "#64748b", marginLeft: 8 }}>{item.hoeveelheid_g}g · {item.kcal}kcal · KH {item.kh_g}g</span>
                        </div>
                        <button onClick={async () => {
                          await fetch(`${API}/api/fuelc/dagboek/${item.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
                          const d = await fetch(`${API}/api/fuelc/dagboek/${datum}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())
                          setItems(d.items || [])
                        }} style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "0.9rem" }}>✕</button>
                      </div>
                    ))}
                    <div style={{ fontSize: "0.72rem", color: trKh >= khMin ? "#22c55e" : "#f97316", marginTop: 4 }}>
                      Totaal: {trKcal}kcal · {Math.round(trKh)}g KH {trKh >= khMin ? "✓" : `(doel ${khMin}g)`}
                    </div>
                  </div>
                )}

                {/* Zoekpaneel voor trainingsvoeding */}
                {isActief && (
                  <div style={{ background: "#141414", border: "1px solid #f97316", borderRadius: 8, padding: 12 }}>
                    {!gekozenProduct ? (
                      <div>
                        <input value={zoek} onChange={e => setZoek(e.target.value)} placeholder="🔍 Sportgel, banaan, rijstwafels..."
                          style={{ width: "100%", padding: "10px 12px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 8, color: "#f5f3ef", fontSize: "0.9rem", outline: "none", marginBottom: 8 }} />
                        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                          {/* Snelle sportvoeding knoppen */}
                          {zoek.length < 2 && (
                            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
                              {alleProducten.filter(p => ["Sportgel","Sportdrank","Banaan","Rijstwafel","Dadels"].some(n => p.naam.includes(n))).slice(0, 5).map(p => (
                                <button key={p.id} onClick={() => kiesProduct(p)}
                                  style={{ fontSize: "0.72rem", padding: "5px 10px", background: "#1e293b", border: "1px solid #2a2a2a", borderRadius: 6, color: "#94a3b8", cursor: "pointer" }}>
                                  {p.naam} ({p.portie_label})
                                </button>
                              ))}
                            </div>
                          )}
                          {zoekResultaten.map(p => (
                            <div key={p.id} onClick={() => kiesProduct(p)}
                              style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: "#1e293b", borderRadius: 8, cursor: "pointer" }}>
                              <div>
                                <div style={{ fontSize: "0.82rem", color: "#f5f3ef" }}>{p.naam}</div>
                                <div style={{ fontSize: "0.62rem", color: "#475569" }}>{p.portie_label} · KH {p.kh}g</div>
                              </div>
                              <div style={{ color: "#f97316", fontWeight: 700, alignSelf: "center" }}>+</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ fontSize: "0.82rem", color: "#f97316", marginBottom: 10 }}>✓ {gekozenProduct.naam}</div>
                        <input type="range" min={5} max={500} step={5} value={portie} onChange={e => setPortie(Number(e.target.value))}
                          style={{ width: "100%", marginBottom: 8 }} />
                        <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: 10 }}>{portie}g · KH {Math.round(gekozenProduct.kh * portie / 100 * 10) / 10}g · {Math.round(gekozenProduct.kcal * portie / 100)}kcal</div>
                        <div style={{ display: "flex", gap: 8 }}>
                          <button onClick={async () => {
                            if (!gekozenProduct || !token) return
                            const waarden = calc(gekozenProduct, portie)
                            await fetch(`${API}/api/fuelc/dagboek`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                              body: JSON.stringify({ datum, moment: momentNr, naam: gekozenProduct.naam, hoeveelheid_g: portie, ...waarden })
                            })
                            const d = await fetch(`${API}/api/fuelc/dagboek/${datum}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())
                            setItems(d.items || [])
                            setGekozenProduct(null); setZoek("")
                          }} style={{ flex: 1, padding: "10px 0", background: "#f97316", color: "#0c0c0c", border: "none", borderRadius: 8, fontWeight: 700, cursor: "pointer", fontSize: "0.85rem" }}>
                            ✓ Toevoegen
                          </button>
                          <button onClick={() => setGekozenProduct(null)}
                            style={{ padding: "10px 14px", background: "#1e293b", color: "#64748b", border: "none", borderRadius: 8, cursor: "pointer" }}>
                            ✕
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Sjablonen lijst */}
      {sjablonen.length > 0 && (
        <div style={{ marginTop: 16, background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: 14 }}>
          <div style={{ fontSize: "0.6rem", color: "#475569", letterSpacing: 2, marginBottom: 10 }}>OPGESLAGEN SJABLONEN</div>
          {sjablonen.map((s, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: "1px solid #1e293b" }}>
              <div>
                <div style={{ fontSize: "0.82rem", color: "#f5f3ef" }}>{s.naam}</div>
                <div style={{ fontSize: "0.65rem", color: "#475569" }}>{s.items?.length || 0} items</div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => laadSjabloon(s)}
                  style={{ fontSize: "0.72rem", color: "#f97316", background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: 6, padding: "4px 10px", cursor: "pointer" }}>
                  Laden
                </button>
                <button onClick={() => verwijderSjabloon(i)}
                  style={{ background: "none", border: "none", color: "#334155", cursor: "pointer", fontSize: "0.85rem" }}>✕</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
