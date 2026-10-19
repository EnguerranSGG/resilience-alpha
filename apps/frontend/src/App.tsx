import { useState } from 'react'
import DashboardPage from './pages/DashboardPage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import type { Session } from './types/api.ts'

// Le jeton reste en mémoire : un rechargement de page impose une nouvelle connexion.
export default function App() {
  const [session, setSession] = useState<Session | null>(null)

  return session ? (
    <DashboardPage session={session} onLogout={() => setSession(null)} />
  ) : (
    <LoginPage onLogin={setSession} />
  )
}
