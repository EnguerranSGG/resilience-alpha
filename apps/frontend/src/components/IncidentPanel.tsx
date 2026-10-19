import { getIncidents, getRemediationStatus } from '../services/api.ts'
import { usePolling } from '../services/usePolling.ts'
import type { RemediationState } from '../types/api.ts'
import Card from './Card.tsx'
import StatusBadge from './StatusBadge.tsx'

const TONE: Record<RemediationState, 'ok' | 'warn' | 'error' | 'neutral'> = {
  NORMAL: 'ok',
  SUSPECT: 'warn',
  MITIGATING: 'warn',
  RECOVERED: 'ok',
  FAILED: 'error',
}

export default function IncidentPanel() {
  const status = usePolling(getRemediationStatus, 2000)
  const incidents = usePolling(getIncidents, 3000)
  const current = status.data

  return (
    <Card
      title="Incident & remédiation"
      aside={current ? <StatusBadge tone={TONE[current.state]}>{current.state}</StatusBadge> : null}
    >
      {status.error && !current && (
        <p className="text-sm text-slate-500">Moteur de remédiation non joignable ({status.error}).</p>
      )}
      {current && (
        <dl className="mb-4 grid grid-cols-3 gap-2 text-sm">
          <div>
            <dt className="text-xs text-slate-500">Exécuteur</dt>
            <dd>
              {current.execution_mode === 'simulated' ? (
                <StatusBadge tone="warn">SIMULATION</StatusBadge>
              ) : (
                <StatusBadge tone="neutral">ansible</StatusBadge>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Profil passerelle</dt>
            <dd className="font-mono">{current.active_profile}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Dernière transition</dt>
            <dd>{new Date(current.last_transition_at).toLocaleTimeString('fr-FR')}</dd>
          </div>
        </dl>
      )}
      {current?.execution_mode === 'simulated' && (
        <p className="mb-3 rounded bg-amber-50 p-2 text-xs text-amber-800">
          Mode SIMULATION : les décisions sont réelles mais aucune configuration n'est modifiée.
        </p>
      )}
      <ol className="max-h-80 space-y-3 overflow-y-auto">
        {(incidents.data ?? []).map((incident) => (
          <li key={incident.incident_id} className="rounded-lg border border-slate-200 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-xs">{incident.incident_id}</span>
              <StatusBadge tone={TONE[incident.state]}>{incident.state}</StatusBadge>
            </div>
            <ul className="space-y-1 text-xs">
              {incident.timeline.map((entry, index) => (
                <li key={`${entry.at}-${index}`} className="grid grid-cols-[5rem_6rem_1fr] gap-2">
                  <span className="text-slate-400">{new Date(entry.at).toLocaleTimeString('fr-FR')}</span>
                  <span className="font-semibold text-slate-600">{entry.kind}</span>
                  <span className="break-words text-slate-700">{entry.message}</span>
                </li>
              ))}
            </ul>
          </li>
        ))}
        {incidents.data?.length === 0 && <li className="text-sm text-slate-400">Aucun incident enregistré.</li>}
      </ol>
    </Card>
  )
}
