import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import ScoreGauge from '../components/ScoreGauge'
import { bandColor, fmt, stageColor } from '../lib/utils'

const STAGES = ['New', 'Contacted', 'Interested', 'Proposal Sent', 'Won', 'Lost']

export default function ProspectDetail() {
  const { id } = useParams<{ id: string }>()
  const nav = useNavigate()
  const qc = useQueryClient()

  const { data: p, isLoading: pLoading } = useQuery({
    queryKey: ['prospect', id],
    queryFn: () => api.prospect(id!),
  })

  const { data: score, isLoading: sLoading } = useQuery({
    queryKey: ['score', id],
    queryFn: () => api.scoreDetail(id!),
  })

  const stageMut = useMutation({
    mutationFn: (stage: string) => api.updateStage(id!, stage),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prospect', id] })
      qc.invalidateQueries({ queryKey: ['prospects'] })
    },
  })

  if (pLoading || sLoading) {
    return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading…</div>
  }
  if (!p || !score) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Prospect not found</div>
  }

  const maxContrib = Math.max(...score.contributions.map(c => Math.abs(c.contribution)))

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-idbi-700 text-white px-6 py-4 flex items-center gap-4">
        <button onClick={() => nav(-1)} className="text-blue-200 hover:text-white text-sm">← Back</button>
        <div>
          <h1 className="text-lg font-bold">{p.name}</h1>
          <p className="text-xs text-blue-200">{p.prospect_id} · {p.segment} · {p.city}, {p.state}</p>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Score card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-600 mb-4">Lead Score</h2>
          <div className="flex items-center gap-6">
            <ScoreGauge score={p.lead_score} band={p.lead_band} />
            <div>
              <span className={`text-sm px-3 py-1 rounded-full border font-semibold ${bandColor(p.lead_band)}`}>
                {p.lead_band}
              </span>
              <p className="text-xs text-slate-500 mt-2">v{p.score_version}</p>
              <p className="text-xs text-slate-500">{p.existing_customer ? '✓ Existing customer' : '+ New prospect'}</p>
            </div>
          </div>

          {/* Contribution bars */}
          <div className="mt-5 space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Score Breakdown</p>
            {score.contributions.map(c => (
              <div key={c.component}>
                <div className="flex justify-between text-xs text-slate-600 mb-0.5">
                  <span>{c.component.replace(/_/g, ' ')}</span>
                  <span className={c.contribution >= 0 ? 'text-green-600' : 'text-red-500'}>
                    {c.contribution >= 0 ? '+' : ''}{c.contribution.toFixed(1)} pts
                  </span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${c.contribution >= 0 ? 'bg-green-500' : 'bg-red-400'}`}
                    style={{ width: `${(Math.abs(c.contribution) / maxContrib) * 100}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">{c.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* NBA + Profile */}
        <div className="space-y-4">
          {/* Next Best Action */}
          <div className="bg-idbi-50 border border-idbi-500/30 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-idbi-700 mb-3">🎯 Next Best Action</h2>
            <div className="space-y-2 text-sm">
              <div className="flex gap-2">
                <span className="text-slate-500 w-20 shrink-0">Product</span>
                <span className="font-medium text-slate-800">{p.recommended_product}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-slate-500 w-20 shrink-0">Channel</span>
                <span className="font-medium text-slate-800">{p.recommended_channel}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-slate-500 w-20 shrink-0">Timing</span>
                <span className="font-medium text-slate-800">{p.recommended_timing}</span>
              </div>
            </div>
          </div>

          {/* Profile */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="text-sm font-semibold text-slate-600 mb-3">Profile</h2>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-slate-500">Income</dt><dd className="font-medium">{fmt(p.annual_income)}</dd>
              <dt className="text-slate-500">Age</dt><dd className="font-medium">{p.age} yrs</dd>
              <dt className="text-slate-500">Life Event</dt><dd className="font-medium">{p.life_event?.replace(/_/g, ' ') || '—'}</dd>
              <dt className="text-slate-500">RM</dt><dd className="font-medium">{p.rm_id}</dd>
            </dl>
          </div>

          {/* Stage */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="text-sm font-semibold text-slate-600 mb-3">Pipeline Stage</h2>
            <div className="flex flex-wrap gap-2">
              {STAGES.map(s => (
                <button
                  key={s}
                  onClick={() => stageMut.mutate(s)}
                  disabled={stageMut.isPending}
                  className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all border ${
                    p.pipeline_stage === s
                      ? `${stageColor(s)} border-current ring-2 ring-offset-1 ring-current`
                      : 'bg-slate-50 text-slate-500 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
