// lib/api.ts — Carboo centrale API client

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, err.detail || "API fout")
  }
  return res.json()
}

// ── COACH MODULE ──────────────────────────────────────────────────────────────

export async function berekenKH(sport: string, minuten: number) {
  return apiFetch<{ min_kh: number; max_kh: number }>(
    `/api/coach/bereken-kh?sport=${sport}&minuten=${minuten}`,
    { method: "POST" }
  )
}

export async function genereerRapport(coachData: CoachData, gebruikerNaam: string, token: string) {
  return apiFetch<{ html: string }>(
    "/api/coach/genereer-rapport",
    { method: "POST", body: JSON.stringify({ coach_data: coachData, gebruiker_naam: gebruikerNaam }) },
    token
  )
}

export async function downloadPdf(coachData: CoachData, gebruikerNaam: string, token: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/coach/genereer-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ coach_data: coachData, gebruiker_naam: gebruikerNaam }),
  })
  if (!res.ok) throw new ApiError(res.status, "PDF generatie mislukt")
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `Carboo_RacePlan_${coachData.atleet_naam.replace(/ /g, "_")}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

export async function slaaPlanOp(coachData: CoachData, gebruikerNaam: string, token: string) {
  return apiFetch("/api/coach/sla-plan-op",
    { method: "POST", body: JSON.stringify({ coach_data: coachData, gebruiker_naam: gebruikerNaam }) }, token)
}

export async function haalPlanOp(token: string) {
  return apiFetch<{ plan: CoachData | null }>("/api/coach/haal-plan-op", {}, token)
}

// ── FUELC MODULE ──────────────────────────────────────────────────────────────

export async function getFuelcProfiel(token: string) {
  return apiFetch<{ profiel: any }>("/api/fuelc/profiel", {}, token)
}
export async function slaFuelcProfiel(profiel: any, token: string) {
  return apiFetch("/api/fuelc/profiel", { method: "POST", body: JSON.stringify(profiel) }, token)
}

export async function getTrainingen(token: string) {
  return apiFetch<{ trainingen: any[] }>("/api/fuelc/trainingen", {}, token)
}
export async function voegTrainingToe(training: any, token: string) {
  return apiFetch("/api/fuelc/trainingen", { method: "POST", body: JSON.stringify(training) }, token)
}
export async function verwijderTraining(id: string, token: string) {
  return apiFetch(`/api/fuelc/trainingen/${id}`, { method: "DELETE" }, token)
}

export async function getDagboek(datum: string, token: string) {
  return apiFetch<{ items: any[] }>(`/api/fuelc/dagboek/${datum}`, {}, token)
}
export async function voegDagboekToe(item: any, token: string) {
  return apiFetch("/api/fuelc/dagboek", { method: "POST", body: JSON.stringify(item) }, token)
}
export async function verwijderDagboekItem(id: string, token: string) {
  return apiFetch(`/api/fuelc/dagboek/${id}`, { method: "DELETE" }, token)
}
export async function updateDagboekItem(id: string, update: any, token: string) {
  return apiFetch(`/api/fuelc/dagboek/${id}`, { method: "PUT", body: JSON.stringify(update) }, token)
}

export async function getWelzijn(van: string, tot: string, token: string) {
  return apiFetch<{ welzijn: any[] }>(`/api/fuelc/welzijn?van=${van}&tot=${tot}`, {}, token)
}
export async function slaWelzijnOp(welzijn: any, token: string) {
  return apiFetch("/api/fuelc/welzijn", { method: "POST", body: JSON.stringify(welzijn) }, token)
}

export async function getBibliotheek(token: string) {
  return apiFetch<{ producten: any[] }>("/api/fuelc/bibliotheek", {}, token)
}
export async function voegProductToe(product: any, token: string) {
  return apiFetch("/api/fuelc/bibliotheek", { method: "POST", body: JSON.stringify(product) }, token)
}
export async function updateProduct(id: string, update: any, token: string) {
  return apiFetch(`/api/fuelc/bibliotheek/${id}`, { method: "PATCH", body: JSON.stringify(update) }, token)
}
export async function verwijderProduct(id: string, token: string) {
  return apiFetch(`/api/fuelc/bibliotheek/${id}`, { method: "DELETE" }, token)
}

export async function getRecepten(token: string) {
  return apiFetch<{ recepten: any[] }>("/api/fuelc/recepten", {}, token)
}
export async function voegReceptToe(recept: any, token: string) {
  return apiFetch("/api/fuelc/recepten", { method: "POST", body: JSON.stringify(recept) }, token)
}
export async function verwijderRecept(id: string, token: string) {
  return apiFetch(`/api/fuelc/recepten/${id}`, { method: "DELETE" }, token)
}

export async function getDagmenu(token: string) {
  return apiFetch<{ menus: any[] }>("/api/fuelc/dagmenu", {}, token)
}
export async function slaaDagmenuOp(menu: any, token: string) {
  return apiFetch("/api/fuelc/dagmenu", { method: "POST", body: JSON.stringify(menu) }, token)
}
export async function verwijderDagmenu(id: string, token: string) {
  return apiFetch(`/api/fuelc/dagmenu/${id}`, { method: "DELETE" }, token)
}

export async function getZones(sport: string, token: string) {
  return apiFetch<{ zones: any }>(`/api/fuelc/zones/${sport}`, {}, token)
}
export async function slaZonesOp(data: any, token: string) {
  return apiFetch("/api/fuelc/zones", { method: "POST", body: JSON.stringify(data) }, token)
}

// ── TRAIN THE GUT MODULE ──────────────────────────────────────────────────────

export async function getGutData(token: string) {
  return apiFetch<{ data: any }>("/api/gut/data", {}, token)
}
export async function slaGutDataOp(data: any, token: string) {
  return apiFetch("/api/gut/data", { method: "POST", body: JSON.stringify(data) }, token)
}

export async function getGutLogs(token: string) {
  return apiFetch<{ logs: any[] }>("/api/gut/logs", {}, token)
}
export async function slaGutLogOp(log: any, token: string) {
  return apiFetch("/api/gut/logs", { method: "POST", body: JSON.stringify(log) }, token)
}

export async function genereerGutSchema(data: any, logs: any, actieveFase: string, token: string) {
  return apiFetch<{ schema: any }>(
    "/api/gut/schema",
    { method: "POST", body: JSON.stringify({ data, logs, actieve_fase: actieveFase }) },
    token
  )
}

// ── CREDITS ───────────────────────────────────────────────────────────────────

export async function getCredits(token: string) {
  return apiFetch<{ credits: number }>("/api/credits", {}, token)
}
export async function gebruikCredit(omschrijving: string, token: string) {
  return apiFetch<{ credits: number }>(
    `/api/credits/gebruik?omschrijving=${encodeURIComponent(omschrijving)}`,
    { method: "POST" }, token
  )
}

// ── TYPES ────────────────────────────────────────────────────────────────────

export interface CoachData {
  atleet_naam: string
  wedstrijd_naam: string
  gewicht: number
  sport: string
  niveau: string
  ervaring: string
  wedstrijd_datum: string
  start_time: string
  eind_time: string
  totale_min: number
  temp: number
  vochtigheid: number
  hoogte: number
  min_kh: number
  max_kh: number
  dag_target?: number
  factor?: number
  [key: string]: any
}
