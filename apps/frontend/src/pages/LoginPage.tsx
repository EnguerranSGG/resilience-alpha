import { useState } from 'react'
import { ApiError, login } from '../services/api.ts'
import type { Session } from '../types/api.ts'

export default function LoginPage({ onLogin }: { onLogin: (session: Session) => void }) {
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      onLogin(await login(username, password))
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? 'Identifiants invalides' : String(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h1 className="text-xl font-bold">RESILIENCE-ALPHA</h1>
          <p className="text-sm text-slate-500">Plateforme de paiement fictive — environnement de laboratoire</p>
        </div>
        <label className="block text-sm">
          Identifiant
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Mot de passe
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="text-sm text-rose-700">{error}</p>}
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-md bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {pending ? 'Connexion…' : 'Se connecter'}
        </button>
        <p className="text-xs text-slate-400">
          Le mot de passe du compte « demo » est généré localement par scripts/generate-secrets.sh.
        </p>
      </form>
    </main>
  )
}
