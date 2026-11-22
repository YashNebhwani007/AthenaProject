import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertOctagon,
  AlertTriangle,
  BarChart3,
  Binary,
  Brain,
  CheckCircle2,
  ChevronDown,
  Compass,
  FileSearch,
  GitCompareArrows,
  Lightbulb,
  Loader2,
  type LucideIcon,
  Microscope,
  Radar,
  ShieldCheck,
  Sigma,
  Sparkles,
  XCircle,
} from 'lucide-react'
import React, { Suspense, lazy, useMemo, useState } from 'react'
import type {
  ClaimType,
  Confidence,
  Finding,
  Report,
  ToolResult,
  VerificationResult,
  VerificationSummary,
} from '../api/types'
import type { RunMeta } from '../hooks/useAthenaSession'
import { cn } from '../lib/cn'
import { formatCompact, formatMs, formatValue } from '../lib/format'
import { toolMeta } from '../lib/tools'
import { EvidenceChip } from './EvidenceChip'
import type { PlotlySpec } from './PlotlyChart'
import { useInspector } from './ToolInspector'
import { groupByRule, prettyRule } from '../lib/verification'
import { VerificationBadge } from './VerificationBadge'
import { type Tone, toneHex } from '../lib/tones'
import { EmptyState, Panel, Pill, RadialGauge, SectionLabel, Skeleton } from './ui/primitives'

const PlotlyChart = lazy(() => import('./PlotlyChart'))

interface ReportViewProps {
  report: Report | null
  verification: VerificationSummary | null
  trace: ToolResult[]
  isAnalyzing?: boolean
  errorMessage?: string | null
  isDraft?: boolean
  runMeta?: RunMeta | null
  hasDataset?: boolean
}

const CLAIM_META: Record<ClaimType, { icon: LucideIcon; tone: Tone; label: string }> = {
  descriptive: { icon: Binary, tone: 'neon', label: 'Descriptive' },
  comparative: { icon: GitCompareArrows, tone: 'brand', label: 'Comparative' },
  statistical: { icon: Sigma, tone: 'brand', label: 'Statistical' },
  predictive: { icon: Brain, tone: 'laser', label: 'Predictive' },
  causal: { icon: Compass, tone: 'warn', label: 'Causal' },
}

const CONFIDENCE_META: Record<Confidence, { tone: Tone; label: string; bars: number; blurb: string }> = {
  high: {
    tone: 'laser',
    label: 'High',
    bars: 3,
    blurb: 'Fully grounded in statistical significance with no data-quality caveats.',
  },
  medium: {
    tone: 'warn',
    label: 'Medium',
    bars: 2,
    blurb: 'Statistically supported with minor missingness or sample constraints.',
  },
  low: {
    tone: 'alert',
    label: 'Low',
    bars: 1,
    blurb: 'Observational or exploratory — requires human review before acting.',
  },
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
}
const rise = {
  hidden: { opacity: 0, y: 14, filter: 'blur(4px)' },
  show: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  },
}

export const ReportView: React.FC<ReportViewProps> = ({
  report,
  verification,
  trace,
  isAnalyzing,
  errorMessage,
  isDraft,
  runMeta,
  hasDataset = true,
}) => {
  const plotSpecs = useMemo(
    () =>
      trace
        .filter((t) => t.tool === 'make_plot' && t.output?.plotly_spec)
        .map((t) => ({ id: t.id, spec: t.output.plotly_spec as PlotlySpec, summary: t.output?.summary as string | undefined })),
    [trace],
  )

  const checksByFinding = useMemo(() => {
    const m = new Map<string, VerificationResult[]>()
    for (const d of verification?.details ?? []) {
      if (!d.finding_id) continue
      m.set(d.finding_id, [...(m.get(d.finding_id) ?? []), d])
    }
    return m
  }, [verification])

  if (isAnalyzing && !report) return <AnalyzingState toolCount={trace.length} />

  if (errorMessage && !report) {
    return (
      <Panel className="!border-alert/25">
        <EmptyState icon={AlertOctagon} tone="alert" title="Analysis fault" body={errorMessage} />
      </Panel>
    )
  }

  if (!report) {
    return (
      <Panel corners>
        <EmptyState
          icon={Radar}
          title={hasDataset ? 'Awaiting directive' : 'No data source mounted'}
          body={
            hasDataset
              ? 'Issue a question in the command bar. Athena plans an analysis, runs deterministic tools, and verifies every claim against tool outputs before reporting.'
              : 'Select a preset dataset or ingest a file from the left panel to begin.'
          }
          className="py-16"
        >
          <div className="mt-6 grid w-full max-w-lg grid-cols-3 gap-2">
            {[
              { icon: FileSearch, k: 'Plan', v: 'Decompose the question' },
              { icon: Microscope, k: 'Execute', v: 'SQL · stats · ML · SHAP' },
              { icon: ShieldCheck, k: 'Verify', v: '5-point claim audit' },
            ].map((s, i) => (
              <motion.div
                key={s.k}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + i * 0.08 }}
                className="rounded-xl border border-line bg-white/[0.02] p-3 text-left"
              >
                <s.icon className="mb-2 size-4 text-neon" />
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink-dim">{s.k}</div>
                <div className="mt-0.5 text-[11px] text-ink-mute">{s.v}</div>
              </motion.div>
            ))}
          </div>
        </EmptyState>
      </Panel>
    )
  }

  const evidenceCount = report.findings.reduce((a, f) => a + (f.evidence?.length || 0), 0)
  const groundedFindings = report.findings.filter((f) => f.evidence?.length > 0).length
  const groundedRate = report.findings.length ? groundedFindings / report.findings.length : 0
  const verifyRatio = verification?.total_checks ? verification.passed / verification.total_checks : 0

  return (
    <motion.div
      key={report.question}
      variants={stagger}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-4"
    >
      {/* Header */}
      <motion.div variants={rise}>
        <Panel className="relative z-20 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-1.5">
                {report.answerable ? (
                  <Pill tone="laser" icon={CheckCircle2}>answerable</Pill>
                ) : (
                  <Pill tone="warn" icon={AlertTriangle}>refusal · insufficient data</Pill>
                )}
                <AnimatePresence>
                  {isDraft && (
                    <motion.span initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}>
                      <Pill tone="neon" icon={Loader2} className="[&>svg]:animate-spin">
                        draft · verifying
                      </Pill>
                    </motion.span>
                  )}
                </AnimatePresence>
                {runMeta && <Pill>run {runMeta.run_id.slice(0, 8)}</Pill>}
              </div>
              <h1 className="text-[19px] font-semibold leading-snug tracking-tight text-ink">{report.question}</h1>
            </div>
            <VerificationBadge summary={verification} pending={isAnalyzing} />
          </div>

          {/* KPI strip */}
          <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Kpi label="Findings" value={String(report.findings.length)} />
            <Kpi label="Evidence refs" value={String(evidenceCount)} />
            <Kpi
              label="Grounded"
              value={`${Math.round(groundedRate * 100)}%`}
              tone={groundedRate === 1 ? 'laser' : groundedRate > 0.5 ? 'warn' : 'alert'}
            />
            {runMeta ? (
              <Kpi
                label="Runtime · tokens"
                value={`${formatMs(runMeta.total_runtime_ms)} · ${formatCompact(runMeta.total_tokens)}`}
              />
            ) : (
              <Kpi
                label="Verified"
                value={verification?.total_checks ? `${Math.round(verifyRatio * 100)}%` : '—'}
                tone={verification?.failed === 0 && verification.total_checks ? 'laser' : undefined}
              />
            )}
          </div>
        </Panel>
      </motion.div>

      {/* TL;DR */}
      <motion.div variants={rise}>
        <div className="glass relative overflow-hidden rounded-2xl p-5 pl-6">
          <div className="absolute inset-y-0 left-0 w-[3px] bg-gradient-to-b from-neon via-brand to-transparent shadow-[0_0_20px_2px_rgba(0,240,255,0.45)]" />
          <div className="pointer-events-none absolute -left-20 -top-20 size-56 rounded-full bg-neon/10 blur-3xl" />
          <div className="relative mb-2 flex items-center gap-2 font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-neon">
            <Sparkles className="size-3.5" />
            Executive summary
          </div>
          <RevealText key={report.tldr} text={report.tldr} className="relative text-[15px] leading-relaxed text-ink" />
        </div>
      </motion.div>

      {/* Visual evidence */}
      {plotSpecs.length > 0 && (
        <motion.div variants={rise}>
          <SectionLabel icon={BarChart3} count={plotSpecs.length}>
            Visual evidence
          </SectionLabel>
          <div className={cn('grid gap-3', plotSpecs.length > 1 && '2xl:grid-cols-2')}>
            {plotSpecs.map((p, idx) => (
              <Panel key={p.id || idx} className="overflow-hidden p-3">
                <Suspense fallback={<Skeleton className="h-[320px]" />}>
                  <PlotlyChart spec={p.spec} />
                </Suspense>
                {p.summary && <p className="mt-2 px-1 text-[11.5px] leading-relaxed text-ink-mute">{p.summary}</p>}
              </Panel>
            ))}
          </div>
        </motion.div>
      )}

      {/* Findings */}
      {report.findings.length > 0 && (
        <motion.div variants={rise}>
          <SectionLabel icon={Microscope} count={report.findings.length} tone="neon">
            Grounded findings
          </SectionLabel>
          <motion.div variants={stagger} className="flex flex-col gap-2.5">
            {report.findings.map((f, i) => (
              <FindingCard key={f.id} finding={f} index={i} trace={trace} checks={checksByFinding.get(f.id) ?? []} />
            ))}
          </motion.div>
        </motion.div>
      )}

      {/* Recommendations */}
      {report.recommendations?.length > 0 && (
        <motion.div variants={rise}>
          <SectionLabel icon={Lightbulb} count={report.recommendations.length} tone="laser">
            Actionable guidance
          </SectionLabel>
          <div className="grid gap-2.5 xl:grid-cols-2">
            {report.recommendations.map((rec, idx) => {
              const c = CONFIDENCE_META[rec.confidence] ?? CONFIDENCE_META.low
              return (
                <motion.div
                  key={idx}
                  variants={rise}
                  whileHover={{ y: -2 }}
                  className="glass group relative overflow-hidden rounded-2xl p-4"
                >
                  <div
                    className="pointer-events-none absolute -right-12 -top-12 size-32 rounded-full opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-30"
                    style={{ background: toneHex[c.tone] }}
                  />
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink-mute">
                      REC-{String(idx + 1).padStart(2, '0')}
                    </span>
                    <div className="flex items-center gap-2" title={c.blurb}>
                      <div className="flex items-end gap-[2px]">
                        {[1, 2, 3].map((b) => (
                          <span
                            key={b}
                            className="w-[3px] rounded-sm"
                            style={{
                              height: 4 + b * 3,
                              background: b <= c.bars ? toneHex[c.tone] : 'rgba(255,255,255,0.1)',
                              boxShadow: b <= c.bars ? `0 0 6px ${toneHex[c.tone]}` : undefined,
                            }}
                          />
                        ))}
                      </div>
                      <Pill tone={c.tone}>{c.label}</Pill>
                    </div>
                  </div>
                  <p className="relative text-[13px] leading-relaxed text-ink">{rec.text}</p>
                  {rec.supported_by?.length > 0 && (
                    <div className="relative mt-3 flex flex-wrap items-center gap-1">
                      <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-ink-mute">backed by</span>
                      {rec.supported_by.map((s) => (
                        <span key={s} className="rounded-md border border-line-strong px-1.5 font-mono text-[10px] text-ink-dim">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Caveats */}
      {report.caveats?.length > 0 && (
        <motion.div variants={rise}>
          <div className="rounded-2xl border border-warn/20 bg-warn/[0.035] p-4">
            <SectionLabel icon={AlertTriangle} tone="warn" count={report.caveats.length}>
              Caveats & limitations
            </SectionLabel>
            <ul className="flex flex-col gap-1.5">
              {report.caveats.map((c, i) => (
                <li key={i} className="flex gap-2.5 text-[12.5px] leading-relaxed text-ink-dim">
                  <span className="mt-2 size-1 shrink-0 rounded-full bg-amber-400 shadow-[0_0_6px_var(--color-warn)]" />
                  {c}
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Verification matrix */}
      {verification && verification.total_checks > 0 && (
        <motion.div variants={rise}>
          <VerificationMatrix summary={verification} />
        </motion.div>
      )}
    </motion.div>
  )
}

/* -------------------------------------------------------------------------- */

const FindingCard: React.FC<{
  finding: Finding
  index: number
  trace: ToolResult[]
  checks: VerificationResult[]
}> = ({ finding, index, trace, checks }) => {
  const [open, setOpen] = useState(false)
  const inspector = useInspector()
  const meta = CLAIM_META[finding.claim_type] ?? CLAIM_META.descriptive
  const failed = checks.filter((c) => !c.passed)
  const status: Tone = checks.length === 0 ? 'mute' : failed.length ? 'alert' : 'laser'
  const sources = useMemo(() => {
    const ids = new Set(finding.evidence?.map((e) => e.tool_result_id))
    return trace.filter((t) => ids.has(t.id))
  }, [finding.evidence, trace])

  return (
    <motion.div
      variants={rise}
      layout
      className={cn(
        'glass group relative overflow-hidden rounded-2xl transition-colors',
        open && '!border-neon/20',
      )}
    >
      <div
        className="absolute inset-y-3 left-0 w-[2px] rounded-full transition-opacity"
        style={{ background: toneHex[meta.tone], boxShadow: `0 0 10px ${toneHex[meta.tone]}`, opacity: open ? 1 : 0.5 }}
      />
      <div className="p-4 pl-5">
        <div className="mb-2 flex items-center gap-2">
          <span className="font-mono text-[10px] font-semibold text-ink-mute">
            F{String(index + 1).padStart(2, '0')}
          </span>
          <span className="font-mono text-[10px] text-ink-mute/70">{finding.id}</span>
          <Pill tone={meta.tone} icon={meta.icon}>
            {meta.label}
          </Pill>
          <span className="ml-auto flex items-center gap-1 font-mono text-[10px]">
            {status === 'laser' && (
              <>
                <ShieldCheck className="size-3.5 text-emerald-400" />
                <span className="text-emerald-400">verified</span>
              </>
            )}
            {status === 'alert' && (
              <>
                <XCircle className="size-3.5 text-rose-400" />
                <span className="text-rose-400">{failed.length} failed</span>
              </>
            )}
            {status === 'mute' && <span className="text-ink-mute">unchecked</span>}
          </span>
        </div>

        <p className="text-[13.5px] leading-relaxed text-ink">{finding.text}</p>

        {finding.evidence?.length > 0 ? (
          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            {finding.evidence.map((ev, i) => (
              <EvidenceChip key={i} evidence={ev} trace={trace} />
            ))}
          </div>
        ) : (
          <div className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-alert/25 bg-alert/[0.05] px-2 py-1 font-mono text-[10px] text-rose-300">
            <AlertTriangle className="size-3" /> no evidence cited
          </div>
        )}

        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="mt-3 flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-mute transition-colors hover:text-neon"
        >
          <ChevronDown className={cn('size-3 transition-transform duration-300', open && 'rotate-180')} />
          {open ? 'hide' : 'show'} rationale
        </button>
      </div>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="grid gap-3 border-t border-line bg-black/20 p-4 pl-5 md:grid-cols-2">
              <div>
                <div className="mb-2 font-mono text-[9.5px] uppercase tracking-[0.16em] text-ink-mute">
                  Source tools
                </div>
                <div className="flex flex-col gap-1.5">
                  {sources.length === 0 && <div className="text-[11px] text-ink-mute">No matching trace entries.</div>}
                  {sources.map((s) => {
                    const tm = toolMeta(s.tool)
                    return (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => inspector.open(s)}
                        className="flex items-center gap-2 rounded-lg border border-line bg-white/[0.02] px-2.5 py-1.5 text-left transition-colors hover:border-neon/30"
                      >
                        <tm.icon className="size-3.5" style={{ color: toneHex[tm.tone] }} />
                        <span className="flex-1 truncate font-mono text-[11px] text-ink">{s.tool}</span>
                        <span className="font-mono text-[9.5px] text-ink-mute">{formatMs(s.runtime_ms)}</span>
                      </button>
                    )
                  })}
                  {finding.evidence?.map((ev, i) => {
                    const m = trace.find((t) => t.id === ev.tool_result_id)?.metrics.find((x) => x.name === ev.metric)
                    return (
                      <div key={i} className="flex justify-between font-mono text-[10.5px]">
                        <span className="truncate text-ink-dim">{ev.metric}</span>
                        <span className={m ? 'text-cyan-200' : 'text-rose-300'}>
                          {m ? `${formatValue(m.value)} ${m.unit ?? ''}` : 'unresolved'}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div>
                <div className="mb-2 font-mono text-[9.5px] uppercase tracking-[0.16em] text-ink-mute">
                  Verifier checks
                </div>
                <div className="flex flex-col gap-1.5">
                  {checks.length === 0 && <div className="text-[11px] text-ink-mute">No finding-level checks recorded.</div>}
                  {checks.map((c, i) => (
                    <div key={i} className="flex items-start gap-2 text-[11px]">
                      {c.passed ? (
                        <CheckCircle2 className="mt-px size-3.5 shrink-0 text-emerald-400" />
                      ) : (
                        <XCircle className="mt-px size-3.5 shrink-0 text-rose-400" />
                      )}
                      <div>
                        <div className="text-ink-dim">{prettyRule(c.rule)}</div>
                        {c.issue && <div className="text-ink-mute">{c.issue}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/* -------------------------------------------------------------------------- */

const VerificationMatrix: React.FC<{ summary: VerificationSummary }> = ({ summary }) => {
  const groups = groupByRule(summary.details)
  const ratio = summary.passed / Math.max(1, summary.total_checks)
  const tone: Tone = summary.failed === 0 ? 'laser' : ratio >= 0.7 ? 'warn' : 'alert'
  return (
    <Panel className="p-5">
      <SectionLabel icon={ShieldCheck} tone="laser">
        Verification engine
      </SectionLabel>
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <RadialGauge value={ratio} size={112} stroke={7} tone={tone} label={`${Math.round(ratio * 100)}%`} sublabel="integrity" />
        <div className="grid flex-1 gap-2">
          {groups.map((g, i) => {
            const total = g.passed + g.failed
            return (
              <div key={g.rule}>
                <div className="mb-1 flex justify-between text-[11.5px]">
                  <span className="text-ink-dim">{prettyRule(g.rule)}</span>
                  <span className="font-mono text-[10.5px] text-ink-mute">
                    <span className="text-emerald-400">{g.passed}</span>
                    {g.failed > 0 && <span className="text-rose-400"> / {g.failed}✕</span>}
                    <span> of {total}</span>
                  </span>
                </div>
                <div className="flex h-1.5 gap-px overflow-hidden rounded-full bg-white/[0.04]">
                  <motion.div
                    className="h-full bg-laser"
                    style={{ boxShadow: '0 0 8px var(--color-laser)' }}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${(g.passed / total) * 100}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: i * 0.06 }}
                  />
                  <motion.div
                    className="h-full bg-alert"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${(g.failed / total) * 100}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: i * 0.06 + 0.2 }}
                  />
                </div>
              </div>
            )
          })}
          <div className="mt-1 flex flex-wrap gap-3 font-mono text-[10px] text-ink-mute">
            <span>repairs: <span className="text-ink">{summary.repairs_attempted}</span></span>
            <span>unverified claims: <span className={summary.unverified_claims ? 'text-rose-300' : 'text-ink'}>{summary.unverified_claims}</span></span>
          </div>
        </div>
      </div>
    </Panel>
  )
}

/* -------------------------------------------------------------------------- */

const AnalyzingState: React.FC<{ toolCount: number }> = ({ toolCount }) => (
  <Panel glow className="relative overflow-hidden">
    <div className="pointer-events-none absolute inset-0 opacity-40">
      <div className="absolute inset-x-0 top-0 h-full w-1/3 animate-scan bg-gradient-to-r from-transparent via-neon/10 to-transparent" />
    </div>
    <div className="relative flex flex-col items-center px-6 py-14 text-center">
      <div className="relative mb-5 grid size-24 place-items-center">
        <div className="absolute inset-0 rounded-full border border-neon/20" />
        <div className="absolute inset-3 rounded-full border border-brand/25" />
        <div className="absolute inset-0 animate-spin-slow rounded-full border-t border-neon shadow-[0_0_20px_-4px_var(--color-neon)]" />
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ background: 'conic-gradient(from 0deg, transparent 0deg, rgba(0,240,255,0.25) 40deg, transparent 80deg)' }}
          animate={{ rotate: 360 }}
          transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
        />
        <Radar className="relative size-7 text-neon" />
      </div>
      <h3 className="text-sm font-semibold text-ink">Autonomous analysis in progress</h3>
      <p className="mt-1.5 max-w-md text-xs leading-relaxed text-ink-mute">
        Executing deterministic tools, testing hypotheses and binding evidence. The draft report will
        materialise here as soon as findings are ready.
      </p>
      <div className="mt-6 w-full max-w-md space-y-2">
        <Skeleton className="h-3" />
        <Skeleton className="h-3 w-5/6" />
        <Skeleton className="h-3 w-2/3" />
      </div>
      <div className="mt-4 font-mono text-[10px] text-ink-mute">{toolCount} tool results received</div>
    </div>
  </Panel>
)

const Kpi: React.FC<{ label: string; value: string; tone?: Tone }> = ({ label, value, tone }) => (
  <div className="rounded-xl border border-line bg-white/[0.02] px-3 py-2">
    <div className="font-mono text-[9px] uppercase tracking-[0.16em] text-ink-mute">{label}</div>
    <div className="mt-0.5 truncate font-mono text-[15px] font-semibold text-ink" style={tone ? { color: toneHex[tone] } : undefined}>
      {value}
    </div>
  </div>
)

/** Word-by-word reveal for the executive summary. */
const RevealText: React.FC<{ text: string; className?: string }> = ({ text, className }) => {
  const words = text.split(/(\s+)/)
  const step = Math.min(0.025, 1.2 / Math.max(1, words.length))
  return (
    <p className={className}>
      {words.map((w, i) =>
        /^\s+$/.test(w) ? (
          w
        ) : (
          <motion.span
            key={i}
            initial={{ opacity: 0, filter: 'blur(6px)' }}
            animate={{ opacity: 1, filter: 'blur(0px)' }}
            transition={{ delay: i * step, duration: 0.35 }}
            className="inline-block"
          >
            {w}
          </motion.span>
        ),
      )}
    </p>
  )
}
