import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ScoreChart({ weeks }) {
  const data = weeks
    .filter((w) => w.anomaly_score !== null && w.anomaly_score !== undefined)
    .map((w) => ({ week: w.week, score: w.anomaly_score }))

  if (data.length === 0) return null

  return (
    <div className="bg-white/[0.035] backdrop-blur-md border border-border rounded-2xl p-5">
      <div className="font-mono text-[0.7rem] text-textLo uppercase tracking-[0.1em] mb-3">
        Isolation Forest anomaly score per week (lower = more anomalous)
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="scoreLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#22D3EE" />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="week"
            tick={{ fill: '#8B8B9A', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={{ stroke: 'rgba(255,255,255,0.09)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8B8B9A', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={{ stroke: 'rgba(255,255,255,0.09)' }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#12121C',
              border: '1px solid rgba(255,255,255,0.09)',
              borderRadius: 10,
              fontSize: 12,
              fontFamily: 'JetBrains Mono, monospace',
            }}
            labelStyle={{ color: '#F3F3F7' }}
          />
          <Line type="monotone" dataKey="score" stroke="url(#scoreLine)" strokeWidth={2.5} dot={{ r: 3, fill: '#8B5CF6' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
