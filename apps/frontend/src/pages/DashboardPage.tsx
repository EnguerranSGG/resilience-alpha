import { useCallback, useEffect, useState } from 'react'
import IncidentPanel from '../components/IncidentPanel.tsx'
import PaymentForm from '../components/PaymentForm.tsx'
import PaymentList from '../components/PaymentList.tsx'
import ServiceStatus from '../components/ServiceStatus.tsx'
import { ApiError, listPayments } from '../services/api.ts'
import type { Payment, Session } from '../types/api.ts'

export default function DashboardPage({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const [payments, setPayments] = useState<Payment[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setPayments(await listPayments(session))
      setError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onLogout()
      else setError(err instanceof Error ? err.message : String(err))
    }
  }, [session, onLogout])

  useEffect(() => {
    // Chargement initial : l'état est mis à jour à la résolution de la requête.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh()
  }, [refresh])

  return (
    <div className="mx-auto max-w-6xl p-4 md:p-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">RESILIENCE-ALPHA</h1>
          <p className="text-sm text-slate-500">Données intégralement fictives — démonstrateur de cyber-résilience</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-600">{session.username}</span>
          <button onClick={onLogout} className="rounded-md border border-slate-300 px-3 py-1">
            Déconnexion
          </button>
        </div>
      </header>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <ServiceStatus />
          <PaymentForm session={session} onCreated={() => void refresh()} />
          <PaymentList session={session} payments={payments} error={error} onRefresh={() => void refresh()} />
        </div>
        <IncidentPanel />
      </div>
    </div>
  )
}
