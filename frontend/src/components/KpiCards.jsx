export default function KpiCards({ summary }) {
  const items = [
    { label: 'Weeks analyzed', value: summary.total_weeks, cls: 'text-textHi' },
    { label: 'Weeks flagged', value: summary.flagged_weeks, cls: 'text-danger' },
    { label: 'Baseline warm-up weeks', value: summary.insufficient_history_weeks, cls: 'text-neutral' },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-white/[0.035] backdrop-blur-md border border-border rounded-2xl px-5 py-4.5
                     hover:border-borderStrong transition-colors"
        >
          <div className="text-[0.76rem] text-textLo font-medium uppercase tracking-wide mb-2">
            {item.label}
          </div>
          <div className={`font-mono text-[2.1rem] font-bold tracking-tight leading-none ${item.cls}`}>
            {item.value}
          </div>
        </div>
      ))}
    </div>
  )
}
