import { useEffect, useState } from 'react'

export interface PollingState<T> {
  data: T | null
  error: string | null
  updatedAt: Date | null
}

/** Interroge `fetcher` toutes les `intervalMs` millisecondes. */
export function usePolling<T>(fetcher: () => Promise<T>, intervalMs: number): PollingState<T> {
  const [state, setState] = useState<PollingState<T>>({ data: null, error: null, updatedAt: null })

  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      try {
        const data = await fetcher()
        if (!cancelled) setState({ data, error: null, updatedAt: new Date() })
      } catch (error) {
        if (!cancelled) {
          setState((previous) => ({
            data: previous.data,
            error: error instanceof Error ? error.message : String(error),
            updatedAt: new Date(),
          }))
        }
      }
    }
    void tick()
    const timer = window.setInterval(() => void tick(), intervalMs)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [fetcher, intervalMs])

  return state
}
