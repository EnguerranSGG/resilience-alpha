type Tone = 'ok' | 'warn' | 'error' | 'neutral'

const TONES: Record<Tone, string> = {
  ok: 'bg-emerald-100 text-emerald-800 ring-emerald-600/20',
  warn: 'bg-amber-100 text-amber-800 ring-amber-600/20',
  error: 'bg-rose-100 text-rose-800 ring-rose-600/20',
  neutral: 'bg-slate-100 text-slate-700 ring-slate-500/20',
}

export default function StatusBadge({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${TONES[tone]}`}>
      {children}
    </span>
  )
}
