import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import ProspectCard from '../components/ProspectCard'
import { bandColor } from '../lib/utils'

const BANDS = ['All', 'Hot', 'Warm', 'Lukewarm', 'Cold']

export default function Dashboard() {
  const [band, setBand] = useState('All')

  const { data: stats } = useQuery({ queryKey: ['stats'], queryFn: api.pipelineStats })
  const { data: prospects = [], isLoading } = useQuery({
    queryKey: ['prospects', band],
    queryFn: () => api.prospects(undefined, band === 'All' ? undefined : band),
  })

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-idbi-700 text-white px-6 py-4 flex items-center justify-between shadow">
        <div>
          <h1 className="text-lg font-bold">🧭 Project Disha</h1>
          <p className="text-xs text-blue-200">Prospect Assist AI · IDBI Innovate 2026 · PS-2</p>
        </div>
        <div className="text-right text-xs text-blue-200">
          <p>RM Dashboard</p>
          <p>{new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
        </div>
      </header>

      {/* Stats bar */}
      {stats && (
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex gap-6 text-sm">
          <div>
            <span className="text-slate-500">Total</span>{' '}
            <span className="font-bold text-slate-800">{stats.total}</span>
          </div>
          <div>
            <span className="text-slate-500">Avg Score</span>{' '}
            <span className="font-bold text-idbi-700">{stats.avg_score}</span>
          </div>
          <div>
            <span className="text-red-500 font-medium">🔥 Hot</span>{' '}
            <span className="font-bold text-slate-800">{stats.hot_prospects}</span>
          </div>
          {stats.by_band.map(b => (
            <div key={b.band} className="hidden sm:block">
              <span className={`text-xs px-2 py-0.5 rounded-full border ${bandColor(b.band)}`}>{b.band}</span>{' '}
              <span className="font-medium">{b.count}</span>
            </div>
          ))}
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Filters */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {BANDS.map(b => (
            <button
              key={b}
              onClick={() => setBand(b)}
              className={`text-sm px-4 py-1.5 rounded-full border transition-colors ${
                band === b
                  ? 'bg-idbi-700 text-white border-idbi-700'
                  : 'bg-white text-slate-600 border-slate-300 hover:border-idbi-500'
              }`}
            >
              {b}
            </button>
          ))}
          <span className="ml-auto text-sm text-slate-500 self-center">
            {prospects.length} prospect{prospects.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 h-40 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {prospects.map(p => <ProspectCard key={p.prospect_id} prospect={p} />)}
          </div>
        )}
      </div>
    </div>
  )
}
