/** Formatting helpers for telemetry readouts. */

export function formatMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || Number.isNaN(ms)) return '—'
  if (ms < 1) return `${Math.round(ms * 1000)}µs`
  if (ms < 1000) return `${ms < 10 ? ms.toFixed(1) : Math.round(ms)}ms`
  if (ms < 60_000) return `${(ms / 1000).toFixed(2)}s`
  const m = Math.floor(ms / 60_000)
  const s = Math.round((ms % 60_000) / 1000)
  return `${m}m ${s}s`
}

export function formatClock(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 100))
  const tenths = total % 10
  const secs = Math.floor(total / 10) % 60
  const mins = Math.floor(total / 600)
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${tenths}`
}

export function formatValue(v: unknown): string {
  if (typeof v === 'number') {
    if (!Number.isFinite(v)) return String(v)
    if (Number.isInteger(v)) return v.toLocaleString()
    const abs = Math.abs(v)
    if (abs !== 0 && (abs < 0.001 || abs >= 1e6)) return v.toExponential(3)
    return Number(v.toFixed(4)).toString()
  }
  if (v === null || v === undefined) return '—'
  return String(v)
}

export function formatCompact(n: number): string {
  return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(n)
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let v = bytes / 1024
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${units[i]}`
}

export function pct(v: number, digits = 1): string {
  return `${(v * 100).toFixed(digits)}%`
}

/** Rough in-memory footprint estimate based on dtype widths. */
export function estimateFootprint(
  rows: number,
  columns: Record<string, { dtype: string }>,
): number {
  let bytesPerRow = 0
  for (const info of Object.values(columns)) {
    const d = info.dtype.toLowerCase()
    if (d.includes('bool')) bytesPerRow += 1
    else if (d.includes('int') || d.includes('float') || d.includes('double') || d.includes('date'))
      bytesPerRow += 8
    else bytesPerRow += 24
  }
  return rows * bytesPerRow
}

export function prettyToolName(tool: string): string {
  return tool.replace(/_/g, ' ')
}
