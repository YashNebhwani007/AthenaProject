/* eslint-disable @typescript-eslint/no-explicit-any */
import { AnimatePresence, motion } from 'framer-motion'
import {
  BarChart3,
  CheckCircle2,
  FlaskConical,
  Gauge,
  ListChecks,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldOff,
  Target,
  XCircle,
} from 'lucide-react'
import React, { useEffect, useMemo, useState } from 'react'
import { getBenchmarkResults } from '../api/client'
import { cn } from '../lib/cn'
import { formatMs, pct } from '../lib/format'
import { type Tone, toneHex } from '../lib/tones'
import { EmptyState, Panel, PanelHeader, Pill, RadialGauge, SectionLabel, Skeleton } from './ui/primitives'

interface Summary {
  total_questions?: number
  passed?: number
  failed?: number
  accuracy: number
  hallucination_rate: number
  refusal_accuracy: number
  leakage_recall: number
}

const SYSTEM_LABEL: Record<string, string> = {
  A1: 'Athena · full system',
  A2: 'Athena · no verifier',
  B1: 'Plain LLM baseline',
}

const METRICS: {
  key: keyof Summary
  label: string
  blurb: string
  icon: typeof Gauge
  tone: Tone
  lowerIsBetter?: boolean
}[] = [
  { key: 'accuracy', label: 'Accuracy', blurb: 'Agent + verifier + repair loop', icon: Target, tone: 'laser' },
  {
    key: 'hallucination_rate',
    label: 'Hallucination rate',
    blurb: 'Numeric & factual claim errors',
    icon: ShieldOff,
    tone: 'brand',
    lowerIsBetter: true,
  },
  { key: 'refusal_accuracy', label: 'Refusal accuracy', blurb: 'Safe refusal & injection defense', icon: ShieldCheck, tone: 'neon' },
  { key: 'leakage_recall', label: 'Leakage recall', blurb: 'Planted leakage detection', icon: FlaskConical, tone: 'warn' },
]

export const BenchmarkView: React.FC = () => {
  const [data, setData] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedSystem, setSelectedSystem] = useState<string>('all')
  const [status, setStatus] = useState<'all' | 'pass' | 'fail'>('all')
  const [query, setQuery] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const reload = () => {
    setIsLoading(true)
    setReloadKey((k) => k + 1)
  }

  useEffect(() => {
    getBenchmarkResults()
      .then((res) => setData(res))
      .catch((err) => {
        console.error('Failed to load benchmark:', err)
        setData(null)
      })
      .finally(() => setIsLoading(false))
  }, [reloadKey])

  const summaries: Record<string, Summary> = data?.summaries || {}
  const systems = Object.keys(summaries)

  const rows = useMemo(() => {
    const out: any[] = []
    for (const [sys, records] of Object.entries<any[]>(data?.details || {})) {
      if (selectedSystem !== 'all' && selectedSystem !== sys) continue
      for (const r of records) {
        if (status === 'pass' && !r.passed) continue
        if (status === 'fail' && r.passed) continue
        const hay = `${r.question_id} ${r.answer_type} ${r.issue ?? ''}`.toLowerCase()
        if (query && !hay.includes(query.toLowerCase())) continue
        out.push({ ...r, system: sys })
      }
    }
    return out
  }, [data, selectedSystem, status, query])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-2xl" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    )
  }

  if (!data || data.error) {
    return (
      <Panel corners>
        <EmptyState
          icon={BarChart3}
          title="Benchmark results unavailable"
          body={
            <>
              Compile results with{' '}
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-cyan-200">
                python -m benchmark.runner --questions all
              </code>
            </>
          }
          className="py-16"
        >
          <button
            type="button"
            onClick={reload}
            className="mt-5 flex items-center gap-2 rounded-lg border border-line-strong px-3 py-1.5 text-xs text-ink-dim hover:border-neon/40 hover:text-ink"
          >
            <RefreshCw className="size-3.5" /> Retry
          </button>
        </EmptyState>
      </Panel>
    )
  }

  const a1 = summaries.A1

  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.07 } } }}
      className="flex flex-col gap-4"
    >
      {/* Title strip */}
      <motion.div variants={fade} className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-neon">Evaluation harness</div>
          <h1 className="text-gradient text-2xl font-semibold tracking-tight">Benchmark Suite</h1>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {data.filter && <Pill tone="brand">suite: {data.filter}</Pill>}
          {data.repeats && <Pill>repeats ×{data.repeats}</Pill>}
          {data.timestamp && <Pill>{new Date(data.timestamp).toLocaleString()}</Pill>}
          <button
            type="button"
            onClick={reload}
            className="grid size-7 place-items-center rounded-lg border border-line text-ink-mute hover:border-neon/40 hover:text-neon"
            aria-label="Reload benchmark results"
          >
            <RefreshCw className="size-3.5" />
          </button>
        </div>
      </motion.div>

      {/* KPI gauges */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {METRICS.map((m) => {
          const v = a1 ? Number(a1[m.key]) : 0
          const shown = m.lowerIsBetter ? 1 - v : v
          return (
            <motion.div key={m.key} variants={fade} whileHover={{ y: -3 }}>
              <Panel className="group relative flex items-center gap-4 overflow-hidden p-4">
                <div
                  className="pointer-events-none absolute -right-10 -top-10 size-28 rounded-full opacity-20 blur-3xl transition-opacity group-hover:opacity-40"
                  style={{ background: toneHex[m.tone] }}
                />
                <RadialGauge value={shown} tone={m.tone} label={a1 ? pct(v, 0) : 'N/A'} sublabel="A1" />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-[13px] font-semibold text-ink">
                    <m.icon className="size-3.5" style={{ color: toneHex[m.tone] }} />
                    {m.label}
                  </div>
                  <div className="mt-1 text-[11px] leading-snug text-ink-mute">{m.blurb}</div>
                  {m.lowerIsBetter && (
                    <div className="mt-1.5 font-mono text-[9px] uppercase tracking-widest text-ink-mute">lower is better</div>
                  )}
                </div>
              </Panel>
            </motion.div>
          )
        })}
      </div>

      {/* Comparison */}
      <motion.div variants={fade}>
        <Panel className="p-5">
          <PanelHeader
            icon={Gauge}
            title="System comparison"
            subtitle={systems.join(' vs ')}
            className="mb-5"
          />
          <div className="grid gap-6 lg:grid-cols-4">
            {METRICS.map((m) => (
              <div key={m.key}>
                <SectionLabel>{m.label}</SectionLabel>
                <div className="flex flex-col gap-2.5">
                  {systems.map((sys, i) => {
                    const v = Number(summaries[sys][m.key]) || 0
                    const best = systems.every((o) =>
                      m.lowerIsBetter ? v <= Number(summaries[o][m.key]) : v >= Number(summaries[o][m.key]),
                    )
                    return (
                      <div key={sys}>
                        <div className="mb-1 flex items-center justify-between font-mono text-[10.5px]">
                          <span className={cn(sys === 'A1' ? 'text-cyan-200' : 'text-ink-dim')}>{sys}</span>
                          <span className={cn('font-semibold', best ? 'text-ink' : 'text-ink-mute')}>
                            {pct(v)}
                            {best && <span className="ml-1 text-emerald-400">▲</span>}
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.04]">
                          <motion.div
                            className="h-full rounded-full"
                            style={{
                              background: `linear-gradient(90deg, ${toneHex[m.tone]}55, ${toneHex[m.tone]})`,
                              boxShadow: sys === 'A1' ? `0 0 8px ${toneHex[m.tone]}` : undefined,
                              opacity: sys === 'A1' ? 1 : 0.55,
                            }}
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.max(1, v * 100)}%` }}
                            transition={{ duration: 0.9, delay: 0.2 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-[12px]">
              <thead>
                <tr className="border-b border-line font-mono text-[9.5px] uppercase tracking-[0.14em] text-ink-mute">
                  <th className="py-2 pr-3 font-medium">System</th>
                  <th className="py-2 pr-3 font-medium">Architecture</th>
                  <th className="py-2 pr-3 font-medium">Pass</th>
                  {METRICS.map((m) => (
                    <th key={m.key} className="py-2 pr-3 text-right font-medium">
                      {m.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {systems.map((sys) => {
                  const s = summaries[sys]
                  return (
                    <tr key={sys} className="border-b border-line/60 transition-colors last:border-0 hover:bg-white/[0.02]">
                      <td className="py-2.5 pr-3 font-mono font-semibold text-cyan-200">{sys}</td>
                      <td className="py-2.5 pr-3 text-ink-dim">{SYSTEM_LABEL[sys] ?? sys}</td>
                      <td className="py-2.5 pr-3 font-mono text-ink-dim">
                        {s.passed ?? '—'}/{s.total_questions ?? '—'}
                      </td>
                      {METRICS.map((m) => (
                        <td key={m.key} className="py-2.5 pr-3 text-right font-mono text-ink">
                          {pct(Number(s[m.key]) || 0)}
                        </td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      </motion.div>

      {/* Itemized */}
      <motion.div variants={fade}>
        <Panel className="p-5">
          <PanelHeader
            icon={ListChecks}
            title="Itemized evaluation"
            subtitle={`${rows.length} records`}
            className="mb-4"
          />
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Segmented
              value={selectedSystem}
              onChange={setSelectedSystem}
              options={[{ id: 'all', label: 'All' }, ...systems.map((s) => ({ id: s, label: s }))]}
              layoutId="bench-sys"
            />
            <Segmented
              value={status}
              onChange={(v) => setStatus(v as typeof status)}
              options={[
                { id: 'all', label: 'Any' },
                { id: 'pass', label: 'Pass' },
                { id: 'fail', label: 'Fail' },
              ]}
              layoutId="bench-status"
            />
            <div className="relative ml-auto">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3 -translate-y-1/2 text-ink-mute" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="search id, type, issue"
                className="h-8 w-56 rounded-lg border border-line bg-black/20 pl-7 pr-2 font-mono text-[11px] text-ink placeholder:text-ink-mute focus:border-neon/40 focus:outline-none"
              />
            </div>
          </div>

          <div className="max-h-[460px] overflow-auto rounded-xl border border-line">
            <table className="w-full min-w-[720px] text-left text-[12px]">
              <thead className="sticky top-0 z-10 bg-hull/95 backdrop-blur">
                <tr className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-ink-mute">
                  <th className="px-3 py-2 font-medium">Question</th>
                  <th className="px-3 py-2 font-medium">System</th>
                  <th className="px-3 py-2 font-medium">Type</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 text-right font-medium">Latency</th>
                  <th className="px-3 py-2 font-medium">Issue / note</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {rows.map((r, i) => (
                    <motion.tr
                      key={`${r.system}-${r.question_id}-${r.repeat ?? i}`}
                      layout
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="border-t border-line/60 hover:bg-white/[0.02]"
                    >
                      <td className="px-3 py-2 font-mono text-ink">{r.question_id}</td>
                      <td className="px-3 py-2 font-mono text-cyan-200">{r.system}</td>
                      <td className="px-3 py-2 text-ink-dim">{r.answer_type}</td>
                      <td className="px-3 py-2">
                        {r.passed ? (
                          <Pill tone="laser" icon={CheckCircle2}>pass</Pill>
                        ) : (
                          <Pill tone="alert" icon={XCircle}>fail</Pill>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-ink-mute">
                        {r.runtime_ms !== undefined ? formatMs(r.runtime_ms) : '—'}
                      </td>
                      <td className={cn('px-3 py-2', r.issue ? 'text-rose-200/90' : 'text-ink-mute')}>
                        {r.issue || 'Verified correct'}
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
            {rows.length === 0 && (
              <div className="py-10 text-center font-mono text-[11px] text-ink-mute">no records match filters</div>
            )}
          </div>
        </Panel>
      </motion.div>
    </motion.div>
  )
}

const fade = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] as const } },
}

const Segmented: React.FC<{
  value: string
  onChange: (v: string) => void
  options: { id: string; label: string }[]
  layoutId: string
}> = ({ value, onChange, options, layoutId }) => (
  <div className="flex rounded-lg border border-line bg-black/20 p-0.5">
    {options.map((o) => (
      <button
        key={o.id}
        type="button"
        onClick={() => onChange(o.id)}
        className={cn(
          'relative rounded-md px-2.5 py-1 font-mono text-[10.5px] transition-colors',
          value === o.id ? 'text-ink' : 'text-ink-mute hover:text-ink-dim',
        )}
      >
        {value === o.id && (
          <motion.span
            layoutId={layoutId}
            className="absolute inset-0 rounded-md border border-neon/25 bg-neon/[0.08]"
            transition={{ type: 'spring', stiffness: 500, damping: 40 }}
          />
        )}
        <span className="relative">{o.label}</span>
      </button>
    ))}
  </div>
)
