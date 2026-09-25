const STYLES = {
  flagged: 'bg-danger/[0.14] text-danger border-danger/25',
  normal: 'bg-success/[0.14] text-success border-success/25',
  insufficient_history: 'bg-neutral/[0.14] text-neutral border-neutral/25',
}

const LABELS = {
  flagged: 'Flagged',
  normal: 'Normal',
  insufficient_history: 'Baseline',
}

export default function StatusPill({ status }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-[0.72rem] font-mono font-bold tracking-wide border ${STYLES[status]}`}
    >
      {LABELS[status].toUpperCase()}
    </span>
  )
}
