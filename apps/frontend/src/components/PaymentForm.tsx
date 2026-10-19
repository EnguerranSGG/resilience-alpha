import { useState } from 'react'
import { ApiError, createPayment, newIdempotencyKey } from '../services/api.ts'
import type { CreatePaymentResult, Currency, Session } from '../types/api.ts'
import Card from './Card.tsx'

const AMOUNT_PATTERN = /^\d{1,10}(\.\d{1,2})?$/

export default function PaymentForm({
  session,
  onCreated,
}: {
  session: Session
  onCreated: (result: CreatePaymentResult) => void
}) {
  const [amount, setAmount] = useState('12.50')
  const [currency, setCurrency] = useState<Currency>('EUR')
  const [description, setDescription] = useState('Paiement fictif de démonstration')
  // La clé est conservée tant que la demande n'a pas abouti : un nouvel essai ne crée pas de doublon.
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey)
  const [pending, setPending] = useState(false)
  const [message, setMessage] = useState<{ tone: 'ok' | 'error'; text: string } | null>(null)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!AMOUNT_PATTERN.test(amount)) {
      setMessage({ tone: 'error', text: 'Montant invalide (ex. 12.50)' })
      return
    }
    setPending(true)
    setMessage(null)
    try {
      const result = await createPayment(session, { amount, currency, description }, idempotencyKey)
      onCreated(result)
      setMessage({
        tone: 'ok',
        text: result.replayed
          ? `Demande déjà traitée : transaction ${result.payment.id} renvoyée sans doublon`
          : `Transaction ${result.payment.status} (${result.payment.id})`,
      })
      setIdempotencyKey(newIdempotencyKey())
    } catch (error) {
      const text = error instanceof ApiError ? `Erreur ${error.status} : ${error.message}` : String(error)
      setMessage({ tone: 'error', text: `${text} — vous pouvez réessayer avec la même clé.` })
    } finally {
      setPending(false)
    }
  }

  return (
    <Card title="Nouvelle transaction fictive">
      <form onSubmit={submit} className="space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <label className="col-span-2 text-sm">
            Montant
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </label>
          <label className="text-sm">
            Devise
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as Currency)}
            >
              {(['EUR', 'USD', 'GBP', 'CHF'] as const).map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="block text-sm">
          Libellé
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            maxLength={140}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <p className="font-mono text-xs text-slate-400">Idempotency-Key : {idempotencyKey}</p>
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-md bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {pending ? 'Envoi…' : 'Payer (fictif)'}
        </button>
        {message && (
          <p className={`text-sm ${message.tone === 'ok' ? 'text-emerald-700' : 'text-rose-700'}`}>{message.text}</p>
        )}
      </form>
    </Card>
  )
}
