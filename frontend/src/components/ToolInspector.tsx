import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, Clock, FileBox, Gauge, Hash, X } from 'lucide-react'
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ToolResult } from '../api/types'
import { cn } from '../lib/cn'
import { formatMs, formatValue } from '../lib/format'
import { extractSql, toolMeta } from '../lib/tools'
import { CodeBlock } from './CodeBlock'
import { toneText } from '../lib/tones'
import { Pill, SectionLabel } from './ui/primitives'

interface InspectorCtx {
  open: (tool: ToolResult, focusMetric?: string) => void
  close: () => void
}

const Ctx = createContext<InspectorCtx>({ open: () => {}, close: () => {} })

// eslint-disable-next-line react-refresh/only-export-components
export const useInspector = () => useContext(Ctx)

const MAX_OUTPUT_CHARS = 12_000

export const InspectorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tool, setTool] = useState<ToolResult | null>(null)
  const [focusMetric, setFocusMetric] = useState<string | undefined>()

  const open = useCallback((t: ToolResult, metric?: string) => {
    setTool(t)
    setFocusMetric(metric)
  }, [])
  const close = useCallback(() => setTool(null), [])

  useEffect(() => {
    if (!tool) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && close()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [tool, close])

  const value = useMemo(() => ({ open, close }), [open, close])

  return (
    <Ctx.Provider value={value}>
      {children}
      <AnimatePresence>
        {tool && (
          <>
            <motion.div
              key="scrim"
              className="fixed inset-0 z-50 bg-black/55 backdrop-blur-[2px]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={close}
            />
            <motion.aside
              key="drawer"
              role="dialog"
              aria-label={`Inspector: ${tool.tool}`}
              className="glass-strong fixed inset-y-2 right-2 z-50 flex w-[min(560px,calc(100vw-16px))] flex-col overflow-hidden rounded-2xl"
              initial={{ x: '105%', opacity: 0.6 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '105%', opacity: 0.6 }}
              transition={{ type: 'spring', stiffness: 340, damping: 36 }}
            >
              <InspectorBody tool={tool} focusMetric={focusMetric} onClose={close} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </Ctx.Provider>
  )
}

const InspectorBody: React.FC<{ tool: ToolResult; focusMetric?: string; onClose: () => void }> = ({
  tool,
  focusMetric,
  onClose,
}) => {
  const meta = toolMeta(tool.tool)
  const Icon = meta.icon
  const sql = extractSql(tool.args)
  const argsRest = useMemo(() => {
    if (!tool.args) return {}
    if (!sql) return tool.args
    const copy: Record<string, unknown> = { ...tool.args }
    for (const k of ['sql', 'query', 'statement']) if (copy[k] === sql) delete copy[k]
    return copy
  }, [tool.args, sql])

  const outputStr = useMemo(() => {
    if (tool.output === undefined || tool.output === null) return null
    let out = tool.output
    if (out && typeof out === 'object' && 'plotly_spec' in out) {
      out = { ...out, plotly_spec: '[plotly figure — rendered in report]' }
    }
    const s = typeof out === 'string' ? out : JSON.stringify(out, null, 2)
    return s.length > MAX_OUTPUT_CHARS ? `${s.slice(0, MAX_OUTPUT_CHARS)}\n… (${s.length - MAX_OUTPUT_CHARS} more chars)` : s
  }, [tool.output])

  const ok = tool.status === 'ok'

  return (
    <>
      <div className="relative border-b border-line px-5 pb-4 pt-5">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-neon/70 to-transparent" />
        <div className="flex items-start gap-3">
          <div
            className={cn(
              'grid size-10 place-items-center rounded-xl border border-line-strong bg-white/[0.03]',
              toneText[meta.tone],
            )}
          >
            <Icon className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-mute">
              Tool inspector · {meta.family}
            </div>
            <h3 className="truncate font-mono text-lg font-semibold text-ink">{tool.tool}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid size-8 place-items-center rounded-lg border border-line text-ink-mute transition-colors hover:border-line-strong hover:text-ink"
            aria-label="Close inspector"
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="mt-4 grid grid-cols-4 gap-2">
          <Fact icon={Hash} k="id" v={tool.id || '—'} />
          <Fact icon={Gauge} k="status" v={tool.status} tone={ok ? 'text-emerald-300' : 'text-rose-300'} />
          <Fact icon={Clock} k="latency" v={formatMs(tool.runtime_ms)} />
          <Fact icon={FileBox} k="artifacts" v={String(tool.artifacts?.length ?? 0)} />
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
        {tool.warnings?.length > 0 && (
          <div className="space-y-1.5 rounded-xl border border-warn/25 bg-warn/[0.05] p-3">
            {tool.warnings.map((w, i) => (
              <div key={i} className="flex gap-2 text-[12px] text-amber-200">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-amber-400" />
                {w}
              </div>
            ))}
          </div>
        )}

        {tool.metrics?.length > 0 && (
          <section>
            <SectionLabel count={tool.metrics.length} tone="neon">
              Exported metrics
            </SectionLabel>
            <div className="overflow-hidden rounded-xl border border-line">
              <table className="w-full font-mono text-[11px]">
                <tbody>
                  {tool.metrics.map((m, i) => {
                    const focused = focusMetric === m.name
                    return (
                      <tr
                        key={i}
                        className={cn(
                          'border-b border-line last:border-0 transition-colors',
                          focused ? 'bg-neon/[0.08]' : i % 2 ? 'bg-white/[0.012]' : '',
                        )}
                      >
                        <td className={cn('px-3 py-1.5', focused ? 'text-cyan-100' : 'text-ink-dim')}>
                          {focused && <span className="mr-1.5 text-neon">▸</span>}
                          {m.name}
                        </td>
                        <td className="px-3 py-1.5 text-right font-semibold text-ink">{formatValue(m.value)}</td>
                        <td className="w-16 px-3 py-1.5 text-right text-ink-mute">{m.unit}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {sql && (
          <section>
            <SectionLabel tone="neon">Query</SectionLabel>
            <CodeBlock code={sql} lang="sql" label="duckdb · sql" />
          </section>
        )}

        {Object.keys(argsRest).length > 0 && (
          <section>
            <SectionLabel>Arguments</SectionLabel>
            <CodeBlock code={JSON.stringify(argsRest, null, 2)} lang="json" label="args.json" maxHeight={220} />
          </section>
        )}

        {tool.artifacts?.length > 0 && (
          <section>
            <SectionLabel count={tool.artifacts.length}>Artifacts</SectionLabel>
            <div className="flex flex-wrap gap-1.5">
              {tool.artifacts.map((a, i) => (
                <Pill key={i} tone="brand" mono={false} className="font-mono normal-case">
                  {a.type}: {a.ref}
                </Pill>
              ))}
            </div>
          </section>
        )}

        {outputStr && (
          <section>
            <SectionLabel>Raw output</SectionLabel>
            <CodeBlock code={outputStr} lang="json" label="output.json" maxHeight={420} />
          </section>
        )}
      </div>
    </>
  )
}

const Fact: React.FC<{ icon: typeof Hash; k: string; v: string; tone?: string }> = ({
  icon: Icon,
  k,
  v,
  tone,
}) => (
  <div className="min-w-0 rounded-lg border border-line bg-white/[0.02] px-2.5 py-2">
    <div className="flex items-center gap-1 font-mono text-[8.5px] uppercase tracking-[0.16em] text-ink-mute">
      <Icon className="size-2.5" /> {k}
    </div>
    <div className={cn('mt-0.5 truncate font-mono text-[12px] font-semibold text-ink', tone)} title={v}>
      {v}
    </div>
  </div>
)
