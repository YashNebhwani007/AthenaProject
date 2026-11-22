import { motion } from 'framer-motion'
import { BarChart3, Cpu, LayoutDashboard, ShieldCheck } from 'lucide-react'
import React from 'react'
import { useBackendLink } from '../hooks/useTelemetry'
import { cn } from '../lib/cn'
import { formatMs } from '../lib/format'
import type { Tone } from '../lib/tones'
import { StatusDot } from './ui/primitives'

export type AppTab = 'workspace' | 'benchmark'

interface HeaderProps {
  activeTab: AppTab
  onTabChange: (tab: AppTab) => void
  isAnalyzing: boolean
}

const TABS: { id: AppTab; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'workspace', label: 'Workspace', icon: LayoutDashboard },
  { id: 'benchmark', label: 'Benchmark Suite', icon: BarChart3 },
]

export const AthenaLogo: React.FC<{ active?: boolean }> = ({ active }) => (
  <div className="relative grid size-9 place-items-center">
    <div
      className={cn(
        'absolute inset-0 rounded-xl bg-gradient-to-br from-neon/40 via-brand/40 to-transparent blur-md transition-opacity duration-700',
        active ? 'opacity-100' : 'opacity-50',
      )}
    />
    <div className="relative grid size-9 place-items-center rounded-xl border border-white/15 bg-gradient-to-br from-[#121a2e] to-[#070a12]">
      <svg viewBox="0 0 24 24" className="size-5" fill="none">
        <defs>
          <linearGradient id="athena-mark" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#00f0ff" />
            <stop offset="1" stopColor="#818cf8" />
          </linearGradient>
        </defs>
        <path
          d="M12 2.5 L21 20.5 H16.4 L12 11.2 L7.6 20.5 H3 Z"
          stroke="url(#athena-mark)"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M8.9 15.6 H15.1" stroke="url(#athena-mark)" strokeWidth="1.6" />
        <circle cx="12" cy="2.6" r="1.3" fill="#00f0ff" />
      </svg>
      {active && (
        <motion.span
          className="absolute inset-0 rounded-xl border border-neon/60"
          initial={{ opacity: 0.8, scale: 1 }}
          animate={{ opacity: 0, scale: 1.45 }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }}
        />
      )}
    </div>
  </div>
)

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange, isAnalyzing }) => {
  const link = useBackendLink()

  const linkTone: Tone =
    link.state === 'online' ? 'laser' : link.state === 'degraded' ? 'warn' : link.state === 'offline' ? 'alert' : 'mute'
  const linkLabel = isAnalyzing
    ? 'AGENT ACTIVE'
    : link.state === 'online'
      ? 'SYSTEM READY'
      : link.state === 'degraded'
        ? 'LINK DEGRADED'
        : link.state === 'offline'
          ? 'BACKEND OFFLINE'
          : 'HANDSHAKE…'

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-abyss/70 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-[1920px] items-center gap-4 px-4 lg:px-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <AthenaLogo active={isAnalyzing} />
          <div className="leading-none">
            <div className="text-gradient text-[15px] font-bold tracking-[0.22em]">ATHENA</div>
            <div className="mt-1 hidden font-mono text-[9px] uppercase tracking-[0.2em] text-ink-mute sm:block">
              Autonomous Data Scientist · Cockpit
            </div>
          </div>
        </div>

        {/* Segmented switch */}
        <nav className="mx-auto flex items-center rounded-xl border border-line bg-white/[0.02] p-1">
          {TABS.map((t) => {
            const active = activeTab === t.id
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => onTabChange(t.id)}
                className={cn(
                  'relative flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                  active ? 'text-ink' : 'text-ink-mute hover:text-ink-dim',
                )}
              >
                {active && (
                  <motion.span
                    layoutId="tab-pill"
                    className="absolute inset-0 rounded-lg border border-neon/25 bg-gradient-to-b from-neon/[0.12] to-brand/[0.06] shadow-[0_0_20px_-8px_var(--color-neon)]"
                    transition={{ type: 'spring', stiffness: 420, damping: 34 }}
                  />
                )}
                <t.icon className={cn('relative size-3.5', active && 'text-neon')} />
                <span className="relative hidden sm:inline">{t.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Right cluster */}
        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-1.5 rounded-lg border border-line px-2.5 py-1.5 font-mono text-[10px] text-ink-mute xl:flex">
            <Cpu className="size-3 text-indigo-300" />
            <span>DUAL-MODEL</span>
            <span className="text-line-strong">/</span>
            <ShieldCheck className="size-3 text-emerald-400" />
            <span>AUTO-VERIFIED</span>
          </div>
          <div
            className={cn(
              'flex items-center gap-2 whitespace-nowrap rounded-lg border px-2.5 py-1.5 font-mono text-[10px] font-semibold tracking-[0.12em] transition-colors duration-500',
              isAnalyzing
                ? 'border-neon/30 bg-neon/[0.06] text-cyan-200'
                : linkTone === 'laser'
                  ? 'border-laser/25 bg-laser/[0.06] text-emerald-300'
                  : linkTone === 'warn'
                    ? 'border-warn/25 bg-warn/[0.06] text-amber-300'
                    : linkTone === 'alert'
                      ? 'border-alert/25 bg-alert/[0.06] text-rose-300'
                      : 'border-line text-ink-mute',
            )}
            title={link.version ? `Athena API v${link.version}` : undefined}
          >
            <StatusDot tone={isAnalyzing ? 'neon' : linkTone} pulse={link.state !== 'offline'} />
            <span>{linkLabel}</span>
            {link.latency !== null && (
              <span className="hidden font-normal text-ink-mute md:inline">
                {formatMs(link.latency)}
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
