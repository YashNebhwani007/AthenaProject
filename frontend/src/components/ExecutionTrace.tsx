import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertTriangle,
  ChevronRight,
  Loader2,
  type LucideIcon,
  Radio,
  ScrollText,
  Workflow,
  XCircle,
} from 'lucide-react'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import type { ToolResult } from '../api/types'
import type { LogEntry, LogKind, PendingStep } from '../hooks/useAthenaSession'
import { cn } from '../lib/cn'
import { formatMs, formatValue } from '../lib/format'
import { toolMeta } from '../lib/tools'
import { useInspector } from './ToolInspector'
import { toneHex, toneText } from '../lib/tones'
import { EmptyState, Panel, PanelHeader, Pill, StatusDot } from './ui/primitives'

interface ExecutionTraceProps {
  trace: ToolResult[]
  isExecuting?: boolean
  currentStepMessage?: string | null
  errorMessage?: string | null
  pendingStep?: PendingStep | null
  log?: LogEntry[]
}

type View = 'timeline' | 'log'

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({
  trace,
  isExecuting,
  currentStepMessage,
  errorMessage,
  pendingStep,
  log = [],
}) => {
  const [view, setView] = useState<View>('timeline')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inspector = useInspector()

  const stats = useMemo(() => {
    const total = trace.reduce((a, t) => a + (t.runtime_ms || 0), 0)
    const max = trace.reduce((a, t) => Math.max(a, t.runtime_ms || 0), 0)
    const errors = trace.filter((t) => t.status !== 'ok').length
    const metrics = trace.reduce((a, t) => a + (t.metrics?.length || 0), 0)
    return { total, max, errors, metrics }
  }, [trace])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [trace.length, isExecuting, log.length, view])

  return (
    <Panel className="flex h-full min-h-[520px] flex-col overflow-hidden">
      <div className="border-b border-line p-4 pb-3">
        <PanelHeader
          icon={Workflow}
          title="Flight Recorder"
          subtitle="deterministic tool telemetry"
          right={
            isExecuting ? (
              <Pill tone="neon" className="gap-1.5">
                <StatusDot tone="neon" className="size-1.5" /> live
              </Pill>
            ) : (
              <Pill>{trace.length} steps</Pill>
            )
          }
        />

        {/* Summary strip */}
        <div className="mt-3 grid grid-cols-4 gap-1.5">
          <Mini k="steps" v={String(trace.length).padStart(2, '0')} />
          <Mini k="Σ latency" v={formatMs(stats.total)} />
          <Mini k="metrics" v={String(stats.metrics)} />
          <Mini k="faults" v={String(stats.errors)} tone={stats.errors ? 'text-rose-300' : undefined} />
        </div>

        {/* Latency spectrum */}
        {trace.length > 0 && (
          <div className="mt-3 flex h-6 items-end gap-[2px]" aria-label="Latency per step">
            {trace.map((t, i) => {
              const meta = toolMeta(t.tool)
              const h = stats.max ? Math.max(0.12, (t.runtime_ms || 0) / stats.max) : 0.12
              return (
                <motion.button
                  key={t.id || i}
                  type="button"
                  title={`${t.tool} · ${formatMs(t.runtime_ms)}`}
                  onClick={() => inspector.open(t)}
                  initial={{ scaleY: 0 }}
                  animate={{ scaleY: 1 }}
                  transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="flex-1 origin-bottom rounded-[2px] opacity-70 transition-opacity hover:opacity-100"
                  style={{
                    height: `${h * 100}%`,
                    background: t.status === 'ok' ? toneHex[meta.tone] : toneHex.alert,
                    boxShadow: `0 0 6px ${t.status === 'ok' ? toneHex[meta.tone] : toneHex.alert}66`,
                    maxWidth: 18,
                  }}
                />
              )
            })}
          </div>
        )}

        {/* View switch */}
        <div className="mt-3 flex rounded-lg border border-line bg-black/20 p-0.5">
          {(
            [
              ['timeline', 'Timeline', Workflow],
              ['log', 'Event stream', ScrollText],
            ] as [View, string, LucideIcon][]
          ).map(([id, label, Icon]) => (
            <button
              key={id}
              type="button"
              onClick={() => setView(id)}
              className={cn(
                'relative flex flex-1 items-center justify-center gap-1.5 rounded-md py-1 font-mono text-[10px] uppercase tracking-[0.12em] transition-colors',
                view === id ? 'text-ink' : 'text-ink-mute hover:text-ink-dim',
              )}
            >
              {view === id && (
                <motion.span
                  layoutId="trace-view"
                  className="absolute inset-0 rounded-md bg-white/[0.06]"
                  transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                />
              )}
              <Icon className="relative size-3" />
              <span className="relative">{label}</span>
              {id === 'log' && log.length > 0 && (
                <span className="relative text-ink-mute">{log.length}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        <AnimatePresence mode="wait" initial={false}>
          {view === 'timeline' ? (
            <motion.div
              key="timeline"
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 8 }}
              transition={{ duration: 0.2 }}
            >
              {trace.length === 0 && !isExecuting && !errorMessage ? (
                <EmptyState
                  icon={Radio}
                  title="Recorder idle"
                  body="Each deterministic tool call — SQL, stats tests, model training, SHAP — will stream here in real time."
                />
              ) : (
                <ol className="relative">
                  {/* Spine */}
                  <div className="absolute bottom-3 left-[13px] top-3 w-px bg-gradient-to-b from-neon/50 via-brand/30 to-transparent" />
                  {isExecuting && (
                    <div className="absolute left-[13px] top-0 h-full w-px overflow-hidden">
                      <div className="trace-fall absolute h-16 w-px bg-gradient-to-b from-transparent via-neon to-transparent" />
                    </div>
                  )}

                  <AnimatePresence initial={false}>
                    {trace.map((step, idx) => (
                      <TraceNode
                        key={step.id || idx}
                        step={step}
                        index={idx}
                        maxMs={stats.max}
                        onInspect={() => inspector.open(step)}
                      />
                    ))}
                  </AnimatePresence>

                  {isExecuting && (
                    <motion.li
                      layout
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="relative flex gap-3 pb-1"
                    >
                      <div className="relative z-10 grid size-[27px] shrink-0 place-items-center rounded-full border border-neon/60 bg-abyss text-neon shadow-[0_0_16px_-2px_var(--color-neon)]">
                        <Loader2 className="size-3.5 animate-spin" />
                      </div>
                      <div className="flex-1 rounded-xl border border-dashed border-neon/30 bg-neon/[0.04] px-3 py-2.5">
                        <div className="font-mono text-[11px] font-semibold text-cyan-100">
                          {pendingStep ? pendingStep.tool : 'reasoning'}
                          <span className="animate-blink">_</span>
                        </div>
                        <div className="mt-0.5 truncate text-[11px] text-ink-mute">
                          {currentStepMessage || 'Planning next tool call…'}
                        </div>
                      </div>
                    </motion.li>
                  )}

                  {errorMessage && !isExecuting && (
                    <motion.li
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="relative flex gap-3"
                    >
                      <div className="relative z-10 grid size-[27px] shrink-0 place-items-center rounded-full border border-alert/60 bg-abyss text-rose-400 shadow-[0_0_14px_-2px_var(--color-alert)]">
                        <XCircle className="size-3.5" />
                      </div>
                      <div className="flex-1 rounded-xl border border-alert/30 bg-alert/[0.06] px-3 py-2.5 text-[11.5px] text-rose-200">
                        <div className="mb-0.5 font-mono text-[9.5px] uppercase tracking-[0.16em] text-rose-400">
                          fault
                        </div>
                        {errorMessage}
                      </div>
                    </motion.li>
                  )}
                </ol>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="log"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.2 }}
            >
              <EventLog log={log} live={!!isExecuting} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Panel>
  )
}

const TraceNode: React.FC<{
  step: ToolResult
  index: number
  maxMs: number
  onInspect: () => void
}> = ({ step, index, maxMs, onInspect }) => {
  const meta = toolMeta(step.tool)
  const Icon = meta.icon
  const ok = step.status === 'ok'
  const ratio = maxMs ? (step.runtime_ms || 0) / maxMs : 0
  const color = ok ? toneHex[meta.tone] : toneHex.alert

  return (
    <motion.li
      layout
      initial={{ opacity: 0, x: 16, filter: 'blur(4px)' }}
      animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="relative flex gap-3 pb-3"
    >
      {/* Node */}
      <div className="relative z-10 shrink-0">
        <div
          className={cn(
            'grid size-[27px] place-items-center rounded-full border bg-abyss',
            ok ? toneText[meta.tone] : 'text-rose-400',
          )}
          style={{ borderColor: `${color}88`, boxShadow: `0 0 12px -3px ${color}` }}
        >
          <Icon className="size-3.5" />
        </div>
        <motion.span
          className="absolute inset-0 rounded-full border"
          style={{ borderColor: color }}
          initial={{ opacity: 0.9, scale: 1 }}
          animate={{ opacity: 0, scale: 1.9 }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
      </div>

      {/* Card */}
      <button
        type="button"
        onClick={onInspect}
        className="group min-w-0 flex-1 rounded-xl border border-line bg-white/[0.02] px-3 py-2.5 text-left transition-all duration-300 hover:-translate-y-px hover:border-line-strong hover:bg-white/[0.04] hover:shadow-[0_10px_30px_-15px_rgba(0,240,255,0.35)]"
      >
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9.5px] text-ink-mute">
            {String(index + 1).padStart(2, '0')}
          </span>
          <span className="min-w-0 flex-1 truncate font-mono text-[12px] font-semibold text-ink">
            {step.tool}
          </span>
          {step.warnings?.length > 0 && <AlertTriangle className="size-3 text-amber-400" />}
          <span
            className={cn(
              'rounded-md border px-1.5 py-px font-mono text-[9.5px] tabular-nums',
              ok ? 'border-line-strong text-ink-dim' : 'border-alert/40 text-rose-300',
            )}
          >
            {formatMs(step.runtime_ms)}
          </span>
          <ChevronRight className="size-3.5 text-ink-mute transition-transform group-hover:translate-x-0.5 group-hover:text-neon" />
        </div>

        {/* Latency bar */}
        <div className="mt-2 h-[2px] overflow-hidden rounded-full bg-white/[0.04]">
          <motion.div
            className="h-full rounded-full"
            style={{ background: color, boxShadow: `0 0 6px ${color}` }}
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(3, ratio * 100)}%` }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>

        {step.metrics?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {step.metrics.slice(0, 3).map((m, i) => (
              <span
                key={i}
                className="max-w-full truncate rounded-md border border-neon/15 bg-neon/[0.04] px-1.5 py-px font-mono text-[9.5px] text-cyan-200/90"
              >
                {m.name}=<span className="text-ink">{formatValue(m.value)}</span>
                {m.unit && m.unit !== 'none' ? <span className="text-ink-mute"> {m.unit}</span> : null}
              </span>
            ))}
            {step.metrics.length > 3 && (
              <span className="px-1 font-mono text-[9.5px] text-ink-mute">+{step.metrics.length - 3}</span>
            )}
          </div>
        )}
        {step.id && (
          <div className="mt-1.5 font-mono text-[9px] text-ink-mute/70">ref {step.id}</div>
        )}
      </button>
    </motion.li>
  )
}

const LOG_STYLE: Record<LogKind, string> = {
  info: 'text-ink-dim',
  tool: 'text-cyan-200',
  draft: 'text-indigo-200',
  verify: 'text-emerald-300',
  final: 'text-emerald-300',
  warn: 'text-amber-300',
  error: 'text-rose-300',
}
const LOG_TAG: Record<LogKind, string> = {
  info: 'SYS',
  tool: 'TOOL',
  draft: 'DRFT',
  verify: 'VRFY',
  final: 'DONE',
  warn: 'WARN',
  error: 'FAIL',
}

const EventLog: React.FC<{ log: LogEntry[]; live: boolean }> = ({ log, live }) => {
  if (log.length === 0) {
    return (
      <EmptyState
        icon={ScrollText}
        title="No events"
        body="The raw SSE event stream for the current run will print here."
        tone="mute"
      />
    )
  }
  return (
    <div className="rounded-xl border border-line bg-black/40 p-3 font-mono text-[10.5px] leading-[1.7]">
      {log.map((e) => (
        <motion.div
          key={e.id}
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex gap-2"
        >
          <span className="shrink-0 tabular-nums text-ink-mute">
            {(e.t / 1000).toFixed(2).padStart(6, '0')}s
          </span>
          <span className={cn('w-9 shrink-0', LOG_STYLE[e.kind])}>{LOG_TAG[e.kind]}</span>
          <span className={cn('min-w-0 break-words', LOG_STYLE[e.kind])}>{e.text}</span>
        </motion.div>
      ))}
      {live && (
        <div className="flex gap-2 text-neon">
          <span className="text-ink-mute">······</span>
          <span className="animate-blink">█</span>
        </div>
      )}
    </div>
  )
}

const Mini: React.FC<{ k: string; v: string; tone?: string }> = ({ k, v, tone }) => (
  <div className="rounded-lg border border-line bg-white/[0.015] px-2 py-1.5">
    <div className="font-mono text-[8px] uppercase tracking-[0.14em] text-ink-mute">{k}</div>
    <div className={cn('truncate font-mono text-[12px] font-semibold tabular-nums text-ink', tone)}>{v}</div>
  </div>
)
