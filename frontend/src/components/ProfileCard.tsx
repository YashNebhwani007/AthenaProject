import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  Binary,
  Calendar,
  ChevronDown,
  Copy,
  Hash,
  HardDrive,
  Search,
  Target,
  Type,
} from 'lucide-react'
import React, { useMemo, useState } from 'react'
import type { DatasetProfile } from '../api/types'
import { cn } from '../lib/cn'
import { estimateFootprint, formatBytes, formatCompact, formatValue } from '../lib/format'
import { type Tone } from '../lib/tones'
import { EmptyState, Meter, Panel, PanelHeader, Pill, RadialGauge, SectionLabel, Skeleton } from './ui/primitives'

interface ProfileCardProps {
  datasetId: string | null
  profile: DatasetProfile | null
  isLoading?: boolean
}

function dtypeIcon(dtype: string) {
  const d = dtype.toLowerCase()
  if (d.includes('bool')) return Binary
  if (d.includes('int') || d.includes('float') || d.includes('double') || d.includes('decimal'))
    return Hash
  if (d.includes('date') || d.includes('time')) return Calendar
  return Type
}

export const ProfileCard: React.FC<ProfileCardProps> = ({ datasetId, profile, isLoading }) => {
  const [filter, setFilter] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [warningsOpen, setWarningsOpen] = useState(true)

  const columns = useMemo(() => Object.entries(profile?.columns || {}), [profile])

  const stats = useMemo(() => {
    if (!profile || columns.length === 0) return null
    const totalCells = profile.row_count * Math.max(1, columns.length)
    const nullCells = columns.reduce((acc, [, c]) => acc + (c.null_count || 0), 0)
    const completeness = totalCells > 0 ? 1 - nullCells / totalCells : 1
    const numeric = columns.filter(([, c]) => /int|float|double|decimal/i.test(c.dtype)).length
    const footprint = estimateFootprint(profile.row_count, profile.columns)
    const dupRatio = profile.row_count > 0 ? profile.duplicate_rows / profile.row_count : 0
    return { completeness, nullCells, numeric, categorical: columns.length - numeric, footprint, dupRatio }
  }, [profile, columns])

  if (isLoading) {
    return (
      <Panel className="flex flex-col gap-4 p-4">
        <PanelHeader icon={Activity} title="Data Health" subtitle="profiling…" />
        <div className="flex items-center gap-4">
          <Skeleton className="size-[88px] rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-9" />
        ))}
      </Panel>
    )
  }

  if (!profile || !stats) {
    return (
      <Panel className="p-4">
        <PanelHeader icon={Activity} title="Data Health" subtitle="no source mounted" />
        <EmptyState
          icon={HardDrive}
          title="Awaiting dataset"
          body="Mount a preset or ingest a file to compute completeness, schema and anomaly telemetry."
          tone="mute"
        />
      </Panel>
    )
  }

  const completenessTone: Tone =
    stats.completeness > 0.98 ? 'laser' : stats.completeness > 0.9 ? 'warn' : 'alert'
  const filtered = columns.filter(([name]) => name.toLowerCase().includes(filter.toLowerCase()))

  return (
    <Panel className="flex flex-col gap-4 p-4">
      <PanelHeader
        icon={Activity}
        title="Data Health"
        subtitle={<span className="normal-case tracking-normal">{datasetId}</span>}
        right={
          profile.quality_warnings?.length ? (
            <Pill tone="warn" icon={AlertTriangle}>
              {profile.quality_warnings.length}
            </Pill>
          ) : (
            <Pill tone="laser">nominal</Pill>
          )
        }
      />

      {/* Gauge cluster */}
      <div className="flex items-center gap-4">
        <RadialGauge
          value={stats.completeness}
          tone={completenessTone}
          label={`${(stats.completeness * 100).toFixed(1)}`}
          sublabel="complete %"
        />
        <div className="grid flex-1 grid-cols-2 gap-x-3 gap-y-2.5">
          <Readout label="Rows" value={formatCompact(profile.row_count)} />
          <Readout label="Columns" value={String(profile.column_count)} />
          <Readout label="Mem (est.)" value={formatBytes(stats.footprint)} />
          <Readout
            label="Duplicates"
            value={String(profile.duplicate_rows)}
            tone={profile.duplicate_rows > 0 ? 'warn' : undefined}
          />
          <div className="col-span-2">
            <div className="mb-1 flex justify-between font-mono text-[9px] uppercase tracking-wider text-ink-mute">
              <span>numeric {stats.numeric}</span>
              <span>categorical {stats.categorical}</span>
            </div>
            <div className="flex h-1 gap-0.5 overflow-hidden rounded-full">
              <motion.div
                className="h-full rounded-full bg-neon/80"
                initial={{ flexGrow: 0 }}
                animate={{ flexGrow: stats.numeric || 0.0001 }}
                transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
              />
              <motion.div
                className="h-full rounded-full bg-brand/80"
                initial={{ flexGrow: 0 }}
                animate={{ flexGrow: stats.categorical || 0.0001 }}
                transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Targets */}
      {profile.suspected_targets?.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="flex items-center gap-1 font-mono text-[9px] uppercase tracking-widest text-ink-mute">
            <Target className="size-3 text-emerald-400" /> targets
          </span>
          {profile.suspected_targets.map((t) => (
            <Pill key={t} tone="laser" mono={false} className="font-mono normal-case">
              {t}
            </Pill>
          ))}
        </div>
      )}

      {/* Warnings */}
      {profile.quality_warnings?.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-warn/20 bg-warn/[0.04]">
          <button
            type="button"
            onClick={() => setWarningsOpen((o) => !o)}
            className="flex w-full items-center gap-2 px-3 py-2 text-left"
          >
            <AlertTriangle className="size-3.5 text-amber-400" />
            <span className="flex-1 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-300">
              Quality caveats
            </span>
            <ChevronDown
              className={cn('size-3.5 text-amber-400/70 transition-transform', warningsOpen && 'rotate-180')}
            />
          </button>
          <AnimatePresence initial={false}>
            {warningsOpen && (
              <motion.ul
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="flex flex-col gap-1 px-3 pb-2.5"
              >
                {profile.quality_warnings.map((w, i) => (
                  <li key={i} className="flex gap-2 text-[11px] leading-snug text-ink-dim">
                    <span className="mt-1.5 size-1 shrink-0 rounded-full bg-amber-400/70" />
                    {w}
                  </li>
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Columns */}
      <div>
        <SectionLabel count={columns.length}>Schema & Completeness</SectionLabel>
        <div className="relative mb-2">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3 -translate-y-1/2 text-ink-mute" />
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="filter columns"
            className="h-7 w-full rounded-lg border border-line bg-black/20 pl-7 pr-2 font-mono text-[11px] text-ink placeholder:text-ink-mute focus:border-neon/40 focus:outline-none"
          />
        </div>
        <div className="flex max-h-[340px] flex-col gap-1 overflow-y-auto pr-1">
          {filtered.map(([name, info], i) => {
            const nullPct = info.null_percent || 0
            const tone: Tone = nullPct > 30 ? 'alert' : nullPct > 5 ? 'warn' : 'laser'
            const Icon = dtypeIcon(info.dtype)
            const isOpen = expanded === name
            const isTarget = profile.suspected_targets?.includes(name)
            const uniqRatio = profile.row_count ? info.unique_count / profile.row_count : 0
            return (
              <div
                key={name}
                className={cn(
                  'rounded-lg border transition-colors',
                  isOpen ? 'border-neon/20 bg-neon/[0.03]' : 'border-transparent hover:bg-white/[0.025]',
                )}
              >
                <button
                  type="button"
                  onClick={() => setExpanded(isOpen ? null : name)}
                  className="w-full px-2 py-1.5 text-left"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <Icon className="size-3 shrink-0 text-ink-mute" />
                    <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-ink">
                      {name}
                    </span>
                    {isTarget && <Target className="size-3 text-emerald-400" />}
                    {uniqRatio > 0.98 && <Copy className="size-3 text-ink-mute" aria-label="near-unique" />}
                    <span className="font-mono text-[9.5px] text-ink-mute">{info.dtype}</span>
                    <span
                      className={cn(
                        'w-10 text-right font-mono text-[9.5px]',
                        nullPct > 0 ? (tone === 'alert' ? 'text-rose-400' : 'text-amber-400') : 'text-ink-mute',
                      )}
                    >
                      {nullPct > 0 ? `${nullPct.toFixed(1)}%` : '0%'}
                    </span>
                  </div>
                  <Meter value={1 - nullPct / 100} tone={tone} delay={Math.min(i, 12) * 0.03} />
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.22 }}
                      className="overflow-hidden"
                    >
                      <div className="grid grid-cols-3 gap-x-2 gap-y-1.5 px-2 pb-2 pt-1 font-mono text-[10px]">
                        <Stat k="unique" v={formatCompact(info.unique_count)} />
                        <Stat k="nulls" v={formatCompact(info.null_count)} />
                        <Stat k="card." v={`${(uniqRatio * 100).toFixed(1)}%`} />
                        {info.min !== undefined && info.min !== null && <Stat k="min" v={formatValue(info.min)} />}
                        {info.max !== undefined && info.max !== null && <Stat k="max" v={formatValue(info.max)} />}
                        {info.mean !== undefined && info.mean !== null && <Stat k="mean" v={formatValue(info.mean)} />}
                        {info.std !== undefined && info.std !== null && <Stat k="std" v={formatValue(info.std)} />}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
          {filtered.length === 0 && (
            <div className="py-4 text-center font-mono text-[10px] text-ink-mute">no columns match</div>
          )}
        </div>
      </div>
    </Panel>
  )
}

const Readout: React.FC<{ label: string; value: string; tone?: Tone }> = ({ label, value, tone }) => (
  <div>
    <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-ink-mute">{label}</div>
    <div
      className={cn(
        'font-mono text-[13px] font-semibold',
        tone === 'warn' ? 'text-amber-300' : 'text-ink',
      )}
    >
      {value}
    </div>
  </div>
)

const Stat: React.FC<{ k: string; v: string }> = ({ k, v }) => (
  <div className="min-w-0">
    <div className="text-[8.5px] uppercase tracking-widest text-ink-mute">{k}</div>
    <div className="truncate text-ink-dim" title={v}>
      {v}
    </div>
  </div>
)
