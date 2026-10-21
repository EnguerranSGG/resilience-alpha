import { useRef, useState, useCallback } from 'react'
import { ApiError, login } from '../services/api.ts'
import type { Session } from '../types/api.ts'

type Step = 'username' | 'camera' | 'password' | 'locked'

const FACE_AUTH_URL = '/face'  // proxied via gateway

async function verifyFace(username: string, imageB64: string): Promise<{ recognized: boolean; message: string; locked: boolean; locked_seconds: number }> {
  const res = await fetch(`${FACE_AUTH_URL}/face/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, image_b64: imageB64 }),
  })
  return res.json()
}

async function notifyPasswordOk() {
  await fetch(`${FACE_AUTH_URL}/face/password-ok`, { method: 'POST' }).catch(() => {})
}
async function notifyPasswordFail() {
  await fetch(`${FACE_AUTH_URL}/face/password-fail`, { method: 'POST' }).catch(() => {})
}

export default function LoginPage({ onLogin }: { onLogin: (session: Session) => void }) {
  const [step, setStep] = useState<Step>('username')
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [lockedSeconds, setLockedSeconds] = useState(0)

  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
    } catch {
      setError('Impossible d\'accéder à la caméra USB')
    }
  }, [])

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
  }, [])

  const captureFrame = useCallback((): string => {
    const video = videoRef.current!
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    canvas.getContext('2d')!.drawImage(video, 0, 0)
    return canvas.toDataURL('image/jpeg').split(',')[1]
  }, [])

  // Étape 1 → 2 : valider l'identifiant et ouvrir la caméra
  const handleUsernameSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim()) return
    setError(null)
    setStep('camera')
    await startCamera()
  }

  // Étape 2 : capturer et envoyer au service facial
  const handleFaceVerify = async () => {
    setPending(true)
    setError(null)
    try {
      const b64 = captureFrame()
      const result = await verifyFace(username, b64)
      if (result.recognized) {
        stopCamera()
        setStep('password')
      } else if (result.locked) {
        setLockedSeconds(result.locked_seconds)
        stopCamera()
        setStep('locked')
      } else {
        setError(result.message)
      }
    } catch {
      setError('Erreur de communication avec le service facial')
    } finally {
      setPending(false)
    }
  }

  // Étape 3 : soumettre le mot de passe
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPending(true)
    setError(null)
    try {
      const session = await login(username, password)
      await notifyPasswordOk()
      onLogin(session)
    } catch (err) {
      await notifyPasswordFail()
      const msg = err instanceof ApiError && err.status === 401 ? 'Mot de passe invalide' : String(err)
      setError(msg)
      // Retour à l'étape 1
      setPassword('')
      setUsername('')
      setStep('username')
    } finally {
      setPending(false)
    }
  }

  const reset = () => {
    stopCamera()
    setStep('username')
    setUsername('')
    setPassword('')
    setError(null)
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-slate-50">
      <div className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h1 className="text-xl font-bold">RESILIENCE-ALPHA</h1>
          <p className="text-sm text-slate-500">Plateforme de paiement fictive — environnement de laboratoire</p>
        </div>

        {/* Indicateur d'étapes */}
        <div className="flex gap-2 text-xs text-slate-400">
          {(['username', 'camera', 'password'] as const).map((s, i) => (
            <span key={s} className={`flex items-center gap-1 ${step === s ? 'text-indigo-600 font-semibold' : ''}`}>
              {i > 0 && <span>›</span>}
              {i === 0 ? 'Identifiant' : i === 1 ? 'Reconnaissance' : 'Mot de passe'}
            </span>
          ))}
        </div>

        {/* Étape 1 — Identifiant */}
        {step === 'username' && (
          <form onSubmit={handleUsernameSubmit} className="space-y-4">
            <label className="block text-sm">
              Identifiant
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                autoComplete="username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            </label>
            {error && <p className="text-sm text-rose-700">{error}</p>}
            <button type="submit" className="w-full rounded-md bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-500">
              Continuer
            </button>
          </form>
        )}

        {/* Étape 2 — Caméra / reconnaissance faciale */}
        {step === 'camera' && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">Regardez la caméra pour confirmer votre identité.</p>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full rounded-lg border border-slate-200 bg-black"
              style={{ height: 240 }}
            />
            {error && <p className="text-sm text-rose-700">{error}</p>}
            <div className="flex gap-2">
              <button
                onClick={handleFaceVerify}
                disabled={pending}
                className="flex-1 rounded-md bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {pending ? 'Analyse…' : 'Vérifier mon visage'}
              </button>
              <button onClick={reset} className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
                Annuler
              </button>
            </div>
          </div>
        )}

        {/* Étape 3 — Mot de passe */}
        {step === 'password' && (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <p className="text-sm text-green-700 font-medium">✓ Visage reconnu — saisissez votre mot de passe</p>
            <label className="block text-sm">
              Mot de passe
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoFocus
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
          </form>
        )}

        {/* Compte bloqué */}
        {step === 'locked' && (
          <div className="space-y-4 text-center">
            <p className="text-rose-700 font-semibold">Compte temporairement bloqué</p>
            <p className="text-sm text-slate-500">Trop de tentatives échouées. Réessayez dans {lockedSeconds}s.</p>
            <button onClick={reset} className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">
              Retour
            </button>
          </div>
        )}

        <p className="text-xs text-slate-400">
          Le mot de passe du compte « demo » est généré localement par scripts/generate-secrets.sh.
        </p>
      </div>
    </main>
  )
}
