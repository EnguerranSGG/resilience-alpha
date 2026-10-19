import type {
  CreatePaymentResult,
  HealthStatus,
  Incident,
  Payment,
  PaymentCreate,
  RemediationStatus,
  Session,
  TokenResponse,
} from '../types/api.ts'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request(path: string, init: RequestInit = {}, token?: string): Promise<Response> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Corps non JSON (ex. 429 de la passerelle) : on garde le statut HTTP.
    }
    throw new ApiError(response.status, detail || `HTTP ${response.status}`)
  }
  return response
}

async function json<T>(response: Response): Promise<T> {
  return (await response.json()) as T
}

export function newIdempotencyKey(): string {
  return `web-${crypto.randomUUID()}`
}

export async function login(username: string, password: string): Promise<Session> {
  const response = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  const token = await json<TokenResponse>(response)
  return { username, token: token.access_token, expiresAt: Date.now() + token.expires_in * 1000 }
}

export async function createPayment(
  session: Session,
  payload: PaymentCreate,
  idempotencyKey: string,
): Promise<CreatePaymentResult> {
  const response = await request(
    '/api/payments',
    { method: 'POST', body: JSON.stringify(payload), headers: { 'Idempotency-Key': idempotencyKey } },
    session.token,
  )
  return {
    payment: await json<Payment>(response),
    replayed: response.headers.get('Idempotent-Replayed') === 'true',
  }
}

export async function listPayments(session: Session): Promise<Payment[]> {
  const response = await request('/api/payments?limit=20', {}, session.token)
  return (await json<{ items: Payment[] }>(response)).items
}

export async function getPayment(session: Session, id: string): Promise<Payment> {
  return json<Payment>(await request(`/api/payments/${encodeURIComponent(id)}`, {}, session.token))
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch('/api/health/ready', { headers: { Accept: 'application/json' } })
  if (response.status !== 200 && response.status !== 503) {
    throw new ApiError(response.status, `HTTP ${response.status}`)
  }
  return json<HealthStatus>(response)
}

export async function getRemediationStatus(): Promise<RemediationStatus> {
  return json<RemediationStatus>(await request('/api/remediation/status'))
}

export async function getIncidents(): Promise<Incident[]> {
  return json<Incident[]>(await request('/api/remediation/incidents'))
}
