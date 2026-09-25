const STYLES = {
  claude: 'bg-success/[0.14] text-success border-success/25',
  gemini: 'bg-violet/[0.14] text-[#C4B5FD] border-violet/30',
  template: 'bg-neutral/[0.14] text-neutral border-neutral/25',
}

export default function StatusChip({ status }) {
  if (!status) return <span className="text-xs text-textLo font-mono">Loading…</span>

  const cls = STYLES[status.backend] || STYLES.template
  return (
    <div>
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.76rem] font-mono font-semibold border ${cls}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current shadow-[0_0_6px_currentColor]" />
        {status.label}
      </span>
      <p className="text-xs text-textLo mt-1.5 leading-relaxed">{status.detail}</p>
    </div>
  )
}
