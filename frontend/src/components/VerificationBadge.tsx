import { AnimatePresence, motion } from 'framer-motion'
import {
  CheckCircle2,
  ChevronDown,
  Lightbulb,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Wrench,
  XCircle,
} from 'lucide-react'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import type { VerificationSummary } from '../api/types'
import { groupByRule, prettyRule, type RuleGroup, scoreTone } from '../lib/verification'
import { cn } from '../lib/cn'
import { toneHex } from '../lib/tones'
import { RadialGauge } from './ui/primitives'

interface VerificationBadgeProps {
  summary: VerificationSummary | null
  pending?: boolean
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({ summary, pending }) => {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const groups = useMemo(() => groupByRule(summary?.details), [summary])

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onDown)
    window.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  if (!summary || summary.total_checks === 0) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-line bg-white/[0.02] px-3 py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-mute">
        {pending ? <Loader2 className="size-3.5 animate-spin text-neon" /> : <ShieldCheck className="size-3.5" />}
        {pending ? 'verifying…' : 'pending verification'}
      </div>
    )
  }

  const tone = scoreTone(summary)
  const allPassed = summary.failed === 0
  const ratio = summary.passed / Math.max(1, summary.total_checks)

  return (
    <div ref={ref} className="relative">
      <motion.button
        type="button"
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="flex items-center gap-2.5 rounded-xl border bg-white/[0.02] py-1 pl-1 pr-3 transition-colors"
        style={{ borderColor: `${toneHex[tone]}44`, boxShadow: `0 0 24px -10px ${toneHex[tone]}` }}
      >
        <RadialGauge value={ratio} size={40} stroke={3.5} tone={tone} ticks={false} label={<span className="text-[10px]">{Math.round(ratio * 100)}</span>} />
        <div className="text-left">
          <div className="flex items-center gap-1 font-mono text-[9px] uppercase tracking-[0.16em] text-ink-mute">
            {allPassed ? (
              <ShieldCheck className="size-3 text-emerald-400" />
            ) : (
              <ShieldAlert className="size-3" style={{ color: toneHex[tone] }} />
            )}
            verifier
          </div>
          <div className="font-mono text-[12px] font-semibold text-ink">
            {summary.passed}/{summary.total_checks} <span className="font-normal text-ink-mute">checks</span>
          </div>
        </div>
        <ChevronDown className={cn('size-3.5 text-ink-mute transition-transform', open && 'rotate-180')} />
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className="glass-strong absolute right-0 top-full z-30 mt-2 w-[min(400px,calc(100vw-32px))] origin-top-right rounded-2xl p-4"
          >
            <div className="mb-3 flex items-center justify-between border-b border-line pb-3">
              <div>
                <div className="text-[13px] font-semibold text-ink">Verifier audit</div>
                <div className="font-mono text-[10px] text-ink-mute">
                  {groups.length} rules · {summary.unverified_claims} unverified claims
                </div>
              </div>
              <div className="flex items-center gap-1 rounded-lg border border-line px-2 py-1 font-mono text-[10px] text-ink-dim">
                <Wrench className="size-3 text-indigo-300" /> {summary.repairs_attempted} repairs
              </div>
            </div>

            <div className="flex max-h-[340px] flex-col gap-2 overflow-y-auto pr-1">
              {groups.map((g) => (
                <RuleRow key={g.rule} group={g} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

const RuleRow: React.FC<{ group: RuleGroup }> = ({ group }) => {
  const [open, setOpen] = useState(group.failed > 0)
  const total = group.passed + group.failed
  const ok = group.failed === 0
  return (
    <div className={cn('rounded-xl border', ok ? 'border-laser/15 bg-laser/[0.03]' : 'border-alert/20 bg-alert/[0.04]')}>
      <button type="button" onClick={() => setOpen((o) => !o)} className="flex w-full items-center gap-2 px-3 py-2 text-left">
        {ok ? <CheckCircle2 className="size-3.5 text-emerald-400" /> : <XCircle className="size-3.5 text-rose-400" />}
        <span className="flex-1 text-[12px] font-medium text-ink">{prettyRule(group.rule)}</span>
        <span className="font-mono text-[10px] text-ink-mute">
          {group.passed}/{total}
        </span>
        <ChevronDown className={cn('size-3 text-ink-mute transition-transform', open && 'rotate-180')} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-1.5 px-3 pb-2.5">
              {group.checks.map((c, i) => (
                <div key={i} className="border-l-2 pl-2 text-[11px]" style={{ borderColor: c.passed ? toneHex.laser : toneHex.alert }}>
                  <div className="flex justify-between font-mono text-[10px]">
                    <span className="text-ink-dim">{c.finding_id ? `finding ${c.finding_id}` : 'global'}</span>
                    <span className={c.passed ? 'text-emerald-400' : 'text-rose-400'}>{c.passed ? 'PASS' : 'FAIL'}</span>
                  </div>
                  {c.issue && <div className="mt-0.5 text-ink-dim">{c.issue}</div>}
                  {c.suggestion && (
                    <div className="mt-0.5 flex gap-1 text-cyan-200/90">
                      <Lightbulb className="mt-0.5 size-3 shrink-0" /> {c.suggestion}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
