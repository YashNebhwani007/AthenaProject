import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUpRight, Link2, Unlink } from 'lucide-react'
import React, { useRef, useState } from 'react'
import type { EvidenceRef, ToolResult } from '../api/types'
import { cn } from '../lib/cn'
import { formatMs, formatValue } from '../lib/format'
import { toolMeta } from '../lib/tools'
import { useInspector } from './ToolInspector'
import { toneText } from '../lib/tones'


interface EvidenceChipProps {
  evidence: EvidenceRef
  trace: ToolResult[]
}

export const EvidenceChip: React.FC<EvidenceChipProps> = ({ evidence, trace }) => {
  const [hover, setHover] = useState(false)
  const [below, setBelow] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)
  const inspector = useInspector()
  const timer = useRef<number | undefined>(undefined)

  const toolResult = trace.find((t) => t.id === evidence.tool_result_id)
  const metricObj = toolResult?.metrics?.find((m) => m.name === evidence.metric)
  const resolved = !!metricObj
  const meta = toolResult ? toolMeta(toolResult.tool) : null
  const Icon = meta?.icon ?? Unlink

  const show = () => {
    window.clearTimeout(timer.current)
    const r = ref.current?.getBoundingClientRect()
    setBelow(!!r && r.top < 240)
    setHover(true)
  }
  const hide = () => {
    timer.current = window.setTimeout(() => setHover(false), 120)
  }

  return (
    <span ref={ref} className="relative inline-flex" onMouseEnter={show} onMouseLeave={hide}>
      <button
        type="button"
        onFocus={show}
        onBlur={hide}
        onClick={() => toolResult && inspector.open(toolResult, evidence.metric)}
        disabled={!toolResult}
        className={cn(
          'inline-flex max-w-full items-center gap-1.5 rounded-lg border px-2 py-[3px] font-mono text-[10.5px] transition-all duration-200',
          resolved
            ? 'border-neon/25 bg-neon/[0.06] text-cyan-200 hover:border-neon/50 hover:bg-neon/[0.12] hover:shadow-[0_0_14px_-4px_var(--color-neon)]'
            : 'border-alert/30 bg-alert/[0.06] text-rose-300',
        )}
      >
        <Icon className={cn('size-3 shrink-0', meta ? toneText[meta.tone] : 'text-rose-400')} />
        <span className="truncate text-ink-mute">{evidence.tool_result_id}.</span>
        <span className="truncate">{evidence.metric}</span>
        {metricObj && (
          <>
            <span className="text-ink-mute">=</span>
            <span className="font-semibold text-ink">{formatValue(metricObj.value)}</span>
          </>
        )}
      </button>

      <AnimatePresence>
        {hover && (
          <motion.div
            initial={{ opacity: 0, y: below ? -4 : 4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: below ? -4 : 4, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            onMouseEnter={show}
            onMouseLeave={hide}
            className={cn(
              'glass-strong absolute left-0 z-40 w-72 rounded-xl p-3 text-left',
              below ? 'top-full mt-2' : 'bottom-full mb-2',
            )}
          >
            {toolResult ? (
              <>
                <div className="mb-2 flex items-center gap-2 border-b border-line pb-2">
                  <Link2 className="size-3.5 text-neon" />
                  <span className="flex-1 font-mono text-[11px] font-semibold text-ink">{toolResult.tool}</span>
                  <span
                    className={cn(
                      'font-mono text-[9.5px] uppercase',
                      toolResult.status === 'ok' ? 'text-emerald-400' : 'text-rose-400',
                    )}
                  >
                    {toolResult.status}
                  </span>
                  <span className="font-mono text-[9.5px] text-ink-mute">{formatMs(toolResult.runtime_ms)}</span>
                </div>
                {metricObj ? (
                  <div className="mb-2">
                    <div className="font-mono text-[9px] uppercase tracking-[0.16em] text-ink-mute">
                      {metricObj.name}
                    </div>
                    <div className="font-mono text-xl font-semibold text-neon">
                      {formatValue(metricObj.value)}
                      <span className="ml-1 text-[11px] font-normal text-ink-mute">{metricObj.unit}</span>
                    </div>
                  </div>
                ) : (
                  <div className="mb-2 text-[11px] text-rose-300">
                    Metric “{evidence.metric}” not exported by this tool.
                  </div>
                )}
                {toolResult.args && Object.keys(toolResult.args).length > 0 && (
                  <div className="max-h-24 overflow-hidden rounded-lg bg-black/30 p-2 font-mono text-[9.5px] leading-relaxed text-ink-dim">
                    {Object.entries(toolResult.args)
                      .slice(0, 5)
                      .map(([k, v]) => (
                        <div key={k} className="truncate">
                          <span className="text-indigo-300">{k}</span>: {typeof v === 'string' ? v : JSON.stringify(v)}
                        </div>
                      ))}
                  </div>
                )}
                <div className="mt-2 flex items-center gap-1 font-mono text-[9.5px] text-neon/80">
                  click to open inspector <ArrowUpRight className="size-3" />
                </div>
              </>
            ) : (
              <div className="text-[11px] text-rose-300">
                Tool result <span className="font-mono">{evidence.tool_result_id}</span> is not present in the
                execution trace — this citation is ungrounded.
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  )
}
