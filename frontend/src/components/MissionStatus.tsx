import { AnimatePresence, motion } from 'framer-motion'
import {
  Brain,
  CheckCircle2,
  FileText,
  type LucideIcon,
  OctagonX,
  ShieldCheck,
  Wrench,
} from 'lucide-react'
import React from 'react'
import type { RunStage } from '../hooks/useAthenaSession'
import { useElapsed } from '../hooks/useTelemetry'
import { cn } from '../lib/cn'
import { formatClock } from '../lib/format'

interface MissionStatusProps {
  stage: RunStage
  message: string | null
  question: string | null
  startedAt: number | null
  endedAt: number | null
  toolCount: number
  verifyIterations: number
}

const STAGES: { id: RunStage; label: string; icon: LucideIcon }[] = [
  { id: 'planning', label: 'Plan', icon: Brain },
  { id: 'executing', label: 'Execute', icon: Wrench },
  { id: 'drafting', label: 'Draft', icon: FileText },
  { id: 'verifying', label: 'Verify', icon: ShieldCheck },
  { id: 'complete', label: 'Deliver', icon: CheckCircle2 },
]

const ORDER: RunStage[] = ['planning', 'executing', 'drafting', 'verifying', 'complete']

export const MissionStatus: React.FC<MissionStatusProps> = ({
  stage,
  message,
  question,
  startedAt,
  endedAt,
  toolCount,
  verifyIterations,
}) => {
  const elapsed = useElapsed(startedAt, endedAt)
  const visible = stage !== 'idle'
  const active = ['planning', 'executing', 'drafting', 'verifying'].includes(stage)
  const terminalBad = stage === 'error' || stage === 'canceled'
  const currentIdx = ORDER.indexOf(stage)

  return (
    <AnimatePresence initial={false}>
      {visible && (
        <motion.div
          initial={{ opacity: 0, height: 0, y: -8 }}
          animate={{ opacity: 1, height: 'auto', y: 0 }}
          exit={{ opacity: 0, height: 0, y: -8 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="overflow-hidden"
        >
          <div
            className={cn(
              'glass relative overflow-hidden rounded-2xl px-4 py-3',
              active && 'hairline-glow',
              terminalBad && '!border-alert/25',
            )}
          >
            {/* Cyber wave while running */}
            {active && <CyberWave />}

            <div className="relative flex flex-wrap items-center gap-x-5 gap-y-3">
              {/* Pipeline */}
              <ol className="flex flex-1 items-center gap-1">
                {STAGES.map((s, i) => {
                  const done = currentIdx > i || stage === 'complete'
                  const isNow = currentIdx === i && active
                  const failedHere =
                    terminalBad && i === Math.max(0, ORDER.indexOf(lastActive(toolCount, verifyIterations)))
                  return (
                    <React.Fragment key={s.id}>
                      <li className="flex items-center gap-1.5">
                        <div
                          className={cn(
                            'relative grid size-6 place-items-center rounded-md border transition-all duration-500',
                            done && 'border-laser/40 bg-laser/10 text-emerald-300',
                            isNow && 'border-neon/60 bg-neon/15 text-neon shadow-[0_0_16px_-2px_var(--color-neon)]',
                            failedHere && 'border-alert/50 bg-alert/10 text-rose-300',
                            !done && !isNow && !failedHere && 'border-line text-ink-mute',
                          )}
                        >
                          {failedHere ? <OctagonX className="size-3" /> : <s.icon className="size-3" />}
                          {isNow && (
                            <motion.span
                              className="absolute inset-0 rounded-md border border-neon"
                              animate={{ opacity: [0.8, 0], scale: [1, 1.6] }}
                              transition={{ duration: 1.4, repeat: Infinity }}
                            />
                          )}
                        </div>
                        <span
                          className={cn(
                            'hidden font-mono text-[10px] uppercase tracking-[0.14em] md:inline',
                            isNow ? 'text-cyan-100' : done ? 'text-ink-dim' : 'text-ink-mute',
                          )}
                        >
                          {s.label}
                        </span>
                      </li>
                      {i < STAGES.length - 1 && (
                        <li className="relative mx-1 h-px min-w-3 flex-1 overflow-hidden bg-line-strong">
                          <motion.div
                            className="absolute inset-y-0 left-0 bg-gradient-to-r from-laser to-neon"
                            initial={false}
                            animate={{ width: done ? '100%' : '0%' }}
                            transition={{ duration: 0.6, ease: 'easeOut' }}
                          />
                        </li>
                      )}
                    </React.Fragment>
                  )
                })}
              </ol>

              {/* Counters */}
              <div className="flex items-center gap-4 font-mono text-[10px]">
                <Counter label="tools" value={toolCount} />
                <Counter label="verify" value={verifyIterations} />
                <div className="text-right">
                  <div className="text-[8.5px] uppercase tracking-[0.16em] text-ink-mute">T+</div>
                  <div className={cn('text-sm font-semibold tabular-nums', active ? 'text-neon' : 'text-ink')}>
                    {formatClock(elapsed)}
                  </div>
                </div>
              </div>
            </div>

            {/* Message line */}
            <div className="relative mt-2.5 flex items-center gap-2 border-t border-line pt-2 font-mono text-[11px]">
              <span
                className={cn(
                  'shrink-0',
                  terminalBad ? 'text-rose-400' : stage === 'complete' ? 'text-emerald-400' : 'text-neon',
                )}
              >
                {terminalBad ? '✕' : stage === 'complete' ? '✓' : '▸'}
              </span>
              <AnimatePresence mode="wait">
                <motion.span
                  key={message ?? stage}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18 }}
                  className="truncate text-ink-dim"
                >
                  {message ||
                    (stage === 'complete'
                      ? 'Report delivered · all claims bound to deterministic evidence'
                      : stage === 'clarify'
                        ? 'Agent requested clarification'
                        : stage === 'canceled'
                          ? 'Run aborted'
                          : stage === 'error'
                            ? 'Run failed'
                            : 'Working…')}
                </motion.span>
              </AnimatePresence>
              {active && <span className="animate-blink text-neon">▍</span>}
              {question && (
                <span className="ml-auto hidden max-w-[40%] truncate text-ink-mute lg:inline" title={question}>
                  “{question}”
                </span>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function lastActive(toolCount: number, verifyIterations: number): RunStage {
  if (verifyIterations > 0) return 'verifying'
  if (toolCount > 0) return 'executing'
  return 'planning'
}

const Counter: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div className="text-right">
    <div className="text-[8.5px] uppercase tracking-[0.16em] text-ink-mute">{label}</div>
    <motion.div
      key={value}
      initial={{ opacity: 0.4, y: -3 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-sm font-semibold tabular-nums text-ink"
    >
      {String(value).padStart(2, '0')}
    </motion.div>
  </div>
)

/** Pulsating oscilloscope-style wave behind the status strip. */
const CyberWave: React.FC = () => (
  <svg
    className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.22]"
    preserveAspectRatio="none"
    viewBox="0 0 400 60"
  >
    <defs>
      <linearGradient id="wave-g" x1="0" x2="1">
        <stop offset="0" stopColor="#00f0ff" stopOpacity="0" />
        <stop offset="0.5" stopColor="#00f0ff" />
        <stop offset="1" stopColor="#818cf8" stopOpacity="0" />
      </linearGradient>
    </defs>
    {[0, 1, 2].map((k) => (
      <motion.path
        key={k}
        fill="none"
        stroke="url(#wave-g)"
        strokeWidth={k === 0 ? 1.2 : 0.6}
        animate={{
          d: [
            wave(0 + k * 0.7, 8 + k * 3),
            wave(Math.PI + k * 0.7, 12 + k * 2),
            wave(Math.PI * 2 + k * 0.7, 8 + k * 3),
          ],
        }}
        transition={{ duration: 3 + k, repeat: Infinity, ease: 'easeInOut' }}
      />
    ))}
  </svg>
)

function wave(phase: number, amp: number): string {
  const pts: string[] = []
  for (let x = 0; x <= 400; x += 10) {
    const y = 30 + Math.sin(x / 32 + phase) * amp * Math.sin(x / 130 + phase / 2)
    pts.push(`${x === 0 ? 'M' : 'L'}${x},${y.toFixed(2)}`)
  }
  return pts.join(' ')
}
