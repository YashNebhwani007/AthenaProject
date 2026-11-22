import { useEffect, useState } from 'react'
import { API_ORIGIN } from '../api/client'

export type LinkState = 'online' | 'degraded' | 'offline' | 'probing'

/** Polls the backend health endpoint and reports link state + round-trip latency. */
export function useBackendLink(intervalMs = 15_000) {
  const [state, setState] = useState<LinkState>('probing')
  const [latency, setLatency] = useState<number | null>(null)
  const [version, setVersion] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const probe = async () => {
      const t0 = performance.now()
      try {
        let res = await fetch(`${API_ORIGIN}/health`, { cache: 'no-store' })
        if (!res.ok) res = await fetch(`${API_ORIGIN}/api/demo-datasets`, { cache: 'no-store' })
        const dt = performance.now() - t0
        if (!alive) return
        setLatency(dt)
        if (res.ok) {
          const body = await res.json().catch(() => ({}))
          if (body?.version) setVersion(body.version)
          setState(dt > 1500 ? 'degraded' : 'online')
        } else {
          setState('degraded')
        }
      } catch {
        if (!alive) return
        setState('offline')
        setLatency(null)
      }
    }
    probe()
    const id = window.setInterval(probe, intervalMs)
    return () => {
      alive = false
      window.clearInterval(id)
    }
  }, [intervalMs])

  return { state, latency, version }
}

/** Ticking elapsed-time readout between start and (optional) end. */
export function useElapsed(start: number | null, end: number | null): number {
  const [now, setNow] = useState(() => performance.now())
  useEffect(() => {
    if (start === null || end !== null) return
    const id = window.setInterval(() => setNow(performance.now()), 100)
    return () => window.clearInterval(id)
  }, [start, end])
  if (start === null) return 0
  return (end ?? now) - start
}
