const BASE = import.meta.env.VITE_API_URL ?? ''

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

export const api = {
  prospects: (rm?: string, band?: string) => {
    const p = new URLSearchParams()
    if (rm) p.set('rm_id', rm)
    if (band) p.set('band', band)
    return get<Prospect[]>(`/api/v1/prospects/?${p}`)
  },
  prospect: (id: string) => get<Prospect>(`/api/v1/prospects/${id}`),
  scoreDetail: (id: string) => get<ScoreDetail>(`/api/v1/score/${id}`),
  pipelineStats: () => get<PipelineStats>('/api/v1/pipeline/stats'),
  updateStage: (id: string, stage: string) =>
    patch<Prospect>(`/api/v1/prospects/${id}/stage`, { stage }),
  askCopilot: (question: string, rm_id = '') =>
    post<{ answer: string; model_used: string }>('/api/v1/copilot/ask', { question, rm_id }),
}

export interface Prospect {
  prospect_id: string
  name: string
  age: number
  city: string
  state: string
  segment: string
  annual_income: number
  existing_customer: boolean
  life_event: string
  lead_score: number
  lead_band: 'Hot' | 'Warm' | 'Lukewarm' | 'Cold'
  recommended_product: string
  recommended_channel: string
  recommended_timing: string
  pipeline_stage: string
  rm_id: string
  score_version: string
}

export interface Contribution {
  component: string
  raw_value: number
  contribution: number
  description: string
}

export interface ScoreDetail {
  prospect_id: string
  lead_score: number
  lead_band: string
  score_version: string
  contributions: Contribution[]
}

export interface PipelineStats {
  total: number
  avg_score: number
  hot_prospects: number
  by_band: { band: string; count: number; avg_score: number }[]
  by_stage: { stage: string; count: number }[]
}
