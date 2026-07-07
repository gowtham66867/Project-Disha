import { useNavigate } from 'react-router-dom'
import type { Prospect } from '../lib/api'
import { bandColor, bandDot, fmt, stageColor } from '../lib/utils'

interface Props { prospect: Prospect }

export default function ProspectCard({ prospect: p }: Props) {
  const nav = useNavigate()
  return (
    <div
      onClick={() => nav(`/prospect/${p.prospect_id}`)}
      className="bg-white rounded-xl border border-slate-200 p-4 cursor-pointer hover:shadow-md hover:border-idbi-500 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-semibold text-slate-800">{p.name}</p>
          <p className="text-xs text-slate-500">{p.segment} · {p.city}</p>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${bandColor(p.lead_band)}`}>
          <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${bandDot(p.lead_band)}`} />
          {p.lead_band}
        </span>
      </div>

      <div className="flex items-center gap-3 mb-3">
        <div className="flex-1 bg-slate-100 rounded-full h-2">
          <div
            className="h-2 rounded-full bg-idbi-500 transition-all"
            style={{ width: `${p.lead_score}%` }}
          />
        </div>
        <span className="text-sm font-bold text-idbi-700 w-10 text-right">
          {p.lead_score.toFixed(0)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-1 text-xs text-slate-600 mb-3">
        <span>Income: {fmt(p.annual_income)}</span>
        <span>{p.existing_customer ? '✓ Existing' : '+ New'}</span>
        {p.life_event && <span className="col-span-2 text-indigo-600">🎯 {p.life_event.replace(/_/g, ' ')}</span>}
      </div>

      <div className="flex items-center justify-between">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${stageColor(p.pipeline_stage)}`}>
          {p.pipeline_stage}
        </span>
        <p className="text-xs text-slate-500 truncate max-w-[140px]">{p.recommended_product}</p>
      </div>
    </div>
  )
}
