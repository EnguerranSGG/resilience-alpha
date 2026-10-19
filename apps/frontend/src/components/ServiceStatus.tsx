import { getHealth } from '../services/api.ts'
import { usePolling } from '../services/usePolling.ts'
import Card from './Card.tsx'
import StatusBadge from './StatusBadge.tsx'

export default function ServiceStatus() {
  const { data, error, updatedAt } = usePolling(getHealth, 3000)
  const healthy = data?.status === 'ok' && !error

  return (
    <Card
      title="État du service de paiement"
      aside={
        <StatusBadge tone={error ? 'error' : healthy ? 'ok' : 'warn'}>
          {error ? 'INJOIGNABLE' : healthy ? 'OPÉRATIONNEL' : 'DÉGRADÉ'}
        </StatusBadge>
      }
    >
      {error && <p className="text-sm text-rose-700">Dernière erreur : {error}</p>}
      {data && (
        <ul className="grid grid-cols-2 gap-2 text-sm">
          {Object.entries(data.checks).map(([name, ok]) => (
            <li key={name} className="flex items-center justify-between rounded bg-slate-50 px-3 py-1.5">
              <span className="font-mono text-slate-600">{name}</span>
              <StatusBadge tone={ok ? 'ok' : 'error'}>{ok ? 'OK' : 'KO'}</StatusBadge>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-xs text-slate-400">
        Contrôle toutes les 3 s via la passerelle{updatedAt ? ` — ${updatedAt.toLocaleTimeString('fr-FR')}` : ''}
      </p>
    </Card>
  )
}
