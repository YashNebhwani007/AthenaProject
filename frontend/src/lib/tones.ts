/** Semantic accent tones shared across the cockpit. */

export type Tone = 'neon' | 'brand' | 'laser' | 'warn' | 'alert' | 'mute'

export const toneClasses: Record<Tone, string> = {
  neon: 'border-neon/25 bg-neon/[0.07] text-cyan-200',
  brand: 'border-brand/30 bg-brand/10 text-indigo-200',
  laser: 'border-laser/30 bg-laser/10 text-emerald-300',
  warn: 'border-warn/30 bg-warn/10 text-amber-300',
  alert: 'border-alert/30 bg-alert/10 text-rose-300',
  mute: 'border-line-strong bg-white/[0.03] text-ink-dim',
}

export const toneText: Record<Tone, string> = {
  neon: 'text-neon',
  brand: 'text-indigo-300',
  laser: 'text-emerald-400',
  warn: 'text-amber-400',
  alert: 'text-rose-400',
  mute: 'text-ink-dim',
}

export const toneHex: Record<Tone, string> = {
  neon: '#00f0ff',
  brand: '#818cf8',
  laser: '#10b981',
  warn: '#f59e0b',
  alert: '#f43f5e',
  mute: '#5d6878',
}

