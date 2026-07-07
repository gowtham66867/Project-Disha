export function bandColor(band: string) {
  return {
    Hot:      'bg-red-100 text-red-700 border-red-300',
    Warm:     'bg-orange-100 text-orange-700 border-orange-300',
    Lukewarm: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    Cold:     'bg-blue-100 text-blue-700 border-blue-300',
  }[band] ?? 'bg-slate-100 text-slate-600 border-slate-300'
}

export function bandDot(band: string) {
  return {
    Hot:      'bg-red-500',
    Warm:     'bg-orange-400',
    Lukewarm: 'bg-yellow-400',
    Cold:     'bg-blue-400',
  }[band] ?? 'bg-slate-400'
}

export function fmt(n: number) {
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`
  if (n >= 100000)  return `₹${(n / 100000).toFixed(1)}L`
  return `₹${n.toLocaleString('en-IN')}`
}

export function stageColor(stage: string) {
  return {
    New:            'bg-slate-100 text-slate-600',
    Contacted:      'bg-indigo-100 text-indigo-700',
    Interested:     'bg-blue-100 text-blue-700',
    'Proposal Sent':'bg-purple-100 text-purple-700',
    Won:            'bg-green-100 text-green-700',
    Lost:           'bg-red-100 text-red-600',
  }[stage] ?? 'bg-slate-100 text-slate-600'
}
