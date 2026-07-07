interface Props { score: number; band: string }

const ARC_R = 54
const CX = 70, CY = 70
const circumference = Math.PI * ARC_R

function bandStroke(band: string) {
  return { Hot: '#ef4444', Warm: '#f97316', Lukewarm: '#eab308', Cold: '#3b82f6' }[band] ?? '#94a3b8'
}

export default function ScoreGauge({ score, band }: Props) {
  const pct = score / 100
  const dash = pct * circumference
  const gap = circumference - dash

  return (
    <svg viewBox="0 0 140 80" className="w-36">
      {/* track */}
      <path
        d={`M ${CX - ARC_R} ${CY} A ${ARC_R} ${ARC_R} 0 0 1 ${CX + ARC_R} ${CY}`}
        fill="none" stroke="#e2e8f0" strokeWidth="10" strokeLinecap="round"
      />
      {/* fill */}
      <path
        d={`M ${CX - ARC_R} ${CY} A ${ARC_R} ${ARC_R} 0 0 1 ${CX + ARC_R} ${CY}`}
        fill="none"
        stroke={bandStroke(band)}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${gap}`}
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
      <text x={CX} y={CY - 4} textAnchor="middle" fontSize="22" fontWeight="700" fill="#1e293b">
        {Math.round(score)}
      </text>
      <text x={CX} y={CY + 14} textAnchor="middle" fontSize="9" fill="#64748b">
        / 100
      </text>
    </svg>
  )
}
