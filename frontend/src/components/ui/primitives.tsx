import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import React from 'react'
import { cn } from '../../lib/cn'
import { type Tone, toneClasses, toneHex, toneText } from '../../lib/tones'

export type { Tone }

/* -------------------------------------------------------------------------- */
/* Panel                                                                       */
/* -------------------------------------------------------------------------- */

interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean
  corners?: boolean
}

export const Panel: React.FC<PanelProps> = ({ className, glow, corners, children, ...rest }) => (
  <div
    className={cn(
      'glass rounded-2xl',
      glow && 'hairline-glow',
      corners && 'hud-corners',
      className,
    )}
    {...rest}
  >
    {children}
  </div>
)

interface PanelHeaderProps {
  icon?: LucideIcon
  title: string
  subtitle?: React.ReactNode
  right?: React.ReactNode
  className?: string
}

export const PanelHeader: React.FC<PanelHeaderProps> = ({
  icon: Icon,
  title,
  subtitle,
  right,
  className,
}) => (
  <div className={cn('flex items-start justify-between gap-3', className)}>
    <div className="flex min-w-0 items-center gap-2.5">
      {Icon && (
        <div className="grid size-7 shrink-0 place-items-center rounded-lg border border-neon/20 bg-neon/[0.06] text-neon shadow-[0_0_18px_-6px_var(--color-neon)]">
          <Icon className="size-3.5" strokeWidth={2.2} />
        </div>
      )}
      <div className="min-w-0">
        <h2 className="truncate text-[13px] font-semibold tracking-tight text-ink">{title}</h2>
        {subtitle && (
          <div className="truncate font-mono text-[10px] uppercase tracking-[0.14em] text-ink-mute">
            {subtitle}
          </div>
        )}
      </div>
    </div>
    {right && <div className="flex shrink-0 items-center gap-1.5">{right}</div>}
  </div>
)

/* -------------------------------------------------------------------------- */
/* Pill                                                                        */
/* -------------------------------------------------------------------------- */

interface PillProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: Tone
  icon?: LucideIcon
  mono?: boolean
}

export const Pill: React.FC<PillProps> = ({
  tone = 'mute',
  icon: Icon,
  mono = true,
  className,
  children,
  ...rest
}) => (
  <span
    className={cn(
      'inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-medium leading-4',
      mono && 'font-mono uppercase tracking-[0.08em]',
      toneClasses[tone],
      className,
    )}
    {...rest}
  >
    {Icon && <Icon className="size-3" strokeWidth={2.2} />}
    {children}
  </span>
)

/* -------------------------------------------------------------------------- */
/* Status dot                                                                  */
/* -------------------------------------------------------------------------- */

export const StatusDot: React.FC<{ tone?: Tone; pulse?: boolean; className?: string }> = ({
  tone = 'laser',
  pulse = true,
  className,
}) => (
  <span className={cn('relative inline-flex size-2', className)}>
    {pulse && (
      <span
        className="absolute inline-flex size-full animate-ping-slow rounded-full opacity-60"
        style={{ background: toneHex[tone] }}
      />
    )}
    <span
      className="relative inline-flex size-2 rounded-full"
      style={{ background: toneHex[tone], boxShadow: `0 0 10px ${toneHex[tone]}` }}
    />
  </span>
)

/* -------------------------------------------------------------------------- */
/* Section label                                                               */
/* -------------------------------------------------------------------------- */

export const SectionLabel: React.FC<{
  icon?: LucideIcon
  children: React.ReactNode
  count?: number
  tone?: Tone
  className?: string
  right?: React.ReactNode
}> = ({ icon: Icon, children, count, tone = 'mute', className, right }) => (
  <div className={cn('mb-3 flex items-center gap-2', className)}>
    {Icon && <Icon className={cn('size-3.5', toneText[tone])} strokeWidth={2.2} />}
    <span
      className={cn(
        'font-mono text-[10px] font-semibold uppercase tracking-[0.18em]',
        tone === 'mute' ? 'text-ink-dim' : toneText[tone],
      )}
    >
      {children}
    </span>
    {count !== undefined && (
      <span className="font-mono text-[10px] text-ink-mute">[{String(count).padStart(2, '0')}]</span>
    )}
    <span className="h-px flex-1 bg-gradient-to-r from-line-strong to-transparent" />
    {right}
  </div>
)

/* -------------------------------------------------------------------------- */
/* Radial gauge                                                                */
/* -------------------------------------------------------------------------- */

interface RadialGaugeProps {
  value: number // 0..1
  size?: number
  stroke?: number
  tone?: Tone
  label?: React.ReactNode
  sublabel?: React.ReactNode
  ticks?: boolean
}

export const RadialGauge: React.FC<RadialGaugeProps> = ({
  value,
  size = 88,
  stroke = 6,
  tone = 'neon',
  label,
  sublabel,
  ticks = true,
}) => {
  const clamped = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0))
  const r = (size - stroke) / 2 - 4
  const c = 2 * Math.PI * r
  const color = toneHex[tone]
  const id = React.useId()

  return (
    <div className="relative grid shrink-0 place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={`g-${id}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={color} stopOpacity={0.45} />
          </linearGradient>
        </defs>
        {ticks && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r + stroke / 2 + 3}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={1}
            strokeDasharray="1 4"
          />
        )}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#g-${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - clamped) }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="font-mono text-[15px] font-semibold leading-none text-ink">{label}</div>
          {sublabel && (
            <div className="mt-1 font-mono text-[8.5px] uppercase tracking-[0.14em] text-ink-mute">
              {sublabel}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Meter bar                                                                   */
/* -------------------------------------------------------------------------- */

export const Meter: React.FC<{
  value: number // 0..1
  tone?: Tone
  className?: string
  delay?: number
}> = ({ value, tone = 'neon', className, delay = 0 }) => {
  const clamped = Math.max(0, Math.min(1, value))
  return (
    <div className={cn('relative h-1 overflow-hidden rounded-full bg-white/[0.05]', className)}>
      <motion.div
        className="absolute inset-y-0 left-0 rounded-full"
        style={{
          background: `linear-gradient(90deg, ${toneHex[tone]}66, ${toneHex[tone]})`,
          boxShadow: `0 0 8px ${toneHex[tone]}aa`,
        }}
        initial={{ width: 0 }}
        animate={{ width: `${clamped * 100}%` }}
        transition={{ duration: 0.9, delay, ease: [0.22, 1, 0.36, 1] }}
      />
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Skeleton                                                                    */
/* -------------------------------------------------------------------------- */

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('shimmer-bg rounded-md', className)} />
)

/* -------------------------------------------------------------------------- */
/* Empty state                                                                 */
/* -------------------------------------------------------------------------- */

export const EmptyState: React.FC<{
  icon: LucideIcon
  title: string
  body?: React.ReactNode
  tone?: Tone
  className?: string
  children?: React.ReactNode
}> = ({ icon: Icon, title, body, tone = 'neon', className, children }) => (
  <div className={cn('flex flex-col items-center px-6 py-10 text-center', className)}>
    <div className="relative mb-4 grid size-14 place-items-center">
      <div
        className="absolute inset-0 animate-spin-slow rounded-full border border-dashed opacity-40"
        style={{ borderColor: toneHex[tone] }}
      />
      <div
        className="absolute inset-2 rounded-full opacity-20 blur-md"
        style={{ background: toneHex[tone] }}
      />
      <Icon className={cn('relative size-5', toneText[tone])} strokeWidth={1.8} />
    </div>
    <h3 className="text-sm font-semibold text-ink">{title}</h3>
    {body && <p className="mt-1.5 max-w-sm text-xs leading-relaxed text-ink-mute">{body}</p>}
    {children}
  </div>
)

/* -------------------------------------------------------------------------- */
/* Kbd                                                                         */
/* -------------------------------------------------------------------------- */

export const Kbd: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <kbd
    className={cn(
      'inline-flex h-5 min-w-5 items-center justify-center rounded border border-line-strong bg-white/[0.04] px-1 font-mono text-[10px] text-ink-dim',
      className,
    )}
  >
    {children}
  </kbd>
)
