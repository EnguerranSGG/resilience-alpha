import { useState } from 'react'
import { ApiError, getPayment } from '../services/api.ts'
import type { Payment, PaymentStatus, Session } from '../types/api.ts'
import Card from './Card.tsx'
import StatusBadge from './StatusBadge.tsx'

const TONE: Record<PaymentStatus, 'ok' | 'warn' | 'error'> = {
  COMPLETED: 'ok',
  PENDING: 'warn',
  FAILED: 'error',
}

export default function PaymentList({
  session,
  payments,
  error,
  onRefresh,
}: {
  session: Session
  payments: Payment[]
  error: string | null
  onRefresh: () => void
}) {
  const [lookupId, setLookupId] = useState('')
  const [lookup, setLookup] = useState<Payment | string | null>(null)

  const find = async (event: React.FormEvent) => {
    event.preventDefault()
    try {
      setLookup(await getPayment(session, lookupId.trim()))
    } catch (err) {
      setLookup(err instanceof ApiError ? `Erreur ${err.status} : ${err.message}` : String(err))
    }
  }

  return (
    <Card
      title="Mes transactions"
      aside={
        <button onClick={onRefresh} className="text-sm font-medium text-indigo-600 hover:underline">
          Actualiser
        </button>
      }
    >
      {error && <p className="mb-2 text-sm text-rose-700">{error}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2">Date</th>
              <th>Montant</th>
              <th>Statut</th>
              <th>Identifiant</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {payments.map((p) => (
              <tr key={p.id}>
                <td className="py-2">{new Date(p.created_at).toLocaleTimeString('fr-FR')}</td>
                <td className="font-mono">
                  {p.amount} {p.currency}
                </td>
                <td>
                  <StatusBadge tone={TONE[p.status]}>{p.status}</StatusBadge>
                </td>
                <td className="font-mono text-xs text-slate-500">{p.id.slice(0, 8)}…</td>
              </tr>
            ))}
            {payments.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-400">
                  Aucune transaction
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <form onSubmit={find} className="mt-4 flex gap-2">
        <input
          className="flex-1 rounded-md border border-slate-300 px-3 py-1.5 font-mono text-xs"
          placeholder="Identifiant de transaction"
          value={lookupId}
          onChange={(e) => setLookupId(e.target.value)}
          required
        />
        <button className="rounded-md border border-slate-300 px-3 text-sm">Consulter</button>
      </form>
      {lookup && (
        <pre className="mt-2 overflow-x-auto rounded bg-slate-50 p-2 text-xs">
          {typeof lookup === 'string' ? lookup : JSON.stringify(lookup, null, 2)}
        </pre>
      )}
    </Card>
  )
}
