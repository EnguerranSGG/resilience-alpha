// Miroir TypeScript des contrats d'API (docs/api/, docs/contracts/).

export type PaymentStatus = 'PENDING' | 'COMPLETED' | 'FAILED'
export type Currency = 'EUR' | 'USD' | 'GBP' | 'CHF'

export interface Payment {
  id: string
  user_id: string
  amount: string
  currency: Currency
  description: string | null
  status: PaymentStatus
  failure_reason: string | null
  idempotency_key: string
  created_at: string
}

export interface PaymentCreate {
  amount: string
  currency: Currency
  description?: string
}

export interface CreatePaymentResult {
  payment: Payment
  replayed: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface Session {
  username: string
  token: string
  expiresAt: number
}

export interface HealthStatus {
  status: 'ok' | 'degraded'
  service: string
  checks: Record<string, boolean>
}

export type RemediationState = 'NORMAL' | 'SUSPECT' | 'MITIGATING' | 'RECOVERED' | 'FAILED'
export type ExecutionMode = 'simulated' | 'ansible'

export interface RemediationStatus {
  state: RemediationState
  execution_mode: ExecutionMode
  active_profile: string
  last_transition_at: string
  current_incident_id: string | null
}

export interface TimelineEntry {
  at: string
  kind: string
  message: string
}

export interface Incident {
  incident_id: string
  opened_at: string
  closed_at: string | null
  state: RemediationState
  trigger_event_id: string
  action: string | null
  execution_mode: ExecutionMode
  verification_passed: boolean | null
  timeline: TimelineEntry[]
}
