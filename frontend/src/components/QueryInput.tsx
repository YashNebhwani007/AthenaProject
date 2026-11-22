import { AnimatePresence, motion } from 'framer-motion'
import { CornerDownLeft, History, Info, Sparkles, Square, Terminal } from 'lucide-react'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '../lib/cn'
import { Kbd } from './ui/primitives'

interface QueryInputProps {
  onSubmit: (question: string) => void
  isLoading: boolean
  onCancel?: () => void
  clarificationMessage?: string | null
  datasetId?: string | null
}

const PROMPTS: Record<string, string[]> = {
  telco: [
    'What is the overall churn rate across all customers?',
    'Are monthly charges significantly different between churned and active users?',
    'Train a predictive model to forecast customer churn.',
    'Which features are the strongest drivers of churn?',
  ],
  housing: [
    'What is the correlation between median income and house value?',
    'Train a model to predict median house value and explain the top drivers.',
    'Is house value significantly different across ocean proximity groups?',
  ],
  titanic: [
    'Analyze the key drivers of passenger survival.',
    'Did survival rate differ significantly between passenger classes?',
    'Is fare correlated with age?',
  ],
  income: [
    'What share of adults earn more than 50K?',
    'Is hours-per-week significantly different between income groups?',
    'Train a model to predict high income and explain it with SHAP.',
  ],
  default: [
    'Profile this dataset and summarise key data quality issues.',
    'Which numeric columns are most strongly correlated?',
    'Train a predictive model for the suspected target and explain its drivers.',
  ],
}

function promptsFor(datasetId?: string | null): string[] {
  const id = (datasetId || '').toLowerCase()
  if (id.includes('telco') || id.includes('churn')) return PROMPTS.telco
  if (id.includes('housing') || id.includes('california')) return PROMPTS.housing
  if (id.includes('titanic')) return PROMPTS.titanic
  if (id.includes('adult') || id.includes('income')) return PROMPTS.income
  return PROMPTS.default
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading,
  onCancel,
  clarificationMessage,
  datasetId,
}) => {
  const [question, setQuestion] = useState('')
  const [focused, setFocused] = useState(false)
  const [history, setHistory] = useState<string[]>([])
  const [historyIdx, setHistoryIdx] = useState(-1)
  const ref = useRef<HTMLTextAreaElement>(null)
  const prompts = useMemo(() => promptsFor(datasetId), [datasetId])
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)

  // Global Cmd/Ctrl+K focuses the command bar
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        ref.current?.focus()
        ref.current?.select()
      }
      if (e.key === 'Escape' && isLoading && onCancel) onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isLoading, onCancel])

  // Auto-grow textarea
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = '0px'
    el.style.height = `${Math.min(140, el.scrollHeight)}px`
  }, [question])

  const submit = () => {
    const q = question.trim()
    if (!q || isLoading) return
    setHistory((h) => [q, ...h.filter((x) => x !== q)].slice(0, 20))
    setHistoryIdx(-1)
    onSubmit(q)
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
      return
    }
    if (e.key === 'ArrowUp' && history.length && (question === '' || historyIdx >= 0)) {
      e.preventDefault()
      const next = Math.min(history.length - 1, historyIdx + 1)
      setHistoryIdx(next)
      setQuestion(history[next])
    }
    if (e.key === 'ArrowDown' && historyIdx >= 0) {
      e.preventDefault()
      const next = historyIdx - 1
      setHistoryIdx(next)
      setQuestion(next >= 0 ? history[next] : '')
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <motion.div
        animate={{
          boxShadow: focused
            ? '0 0 0 1px rgba(0,240,255,0.35), 0 0 40px -10px rgba(0,240,255,0.45), 0 20px 50px -24px rgba(0,0,0,0.8)'
            : '0 0 0 1px rgba(255,255,255,0.07), 0 0 0px 0px rgba(0,240,255,0), 0 20px 50px -24px rgba(0,0,0,0.8)',
        }}
        transition={{ duration: 0.3 }}
        className="glass relative overflow-hidden rounded-2xl !border-transparent"
      >
        {/* Animated top hairline */}
        <div
          className={cn(
            'absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-neon to-transparent transition-opacity duration-500',
            focused || isLoading ? 'opacity-80' : 'opacity-20',
          )}
        />
        {isLoading && (
          <div className="absolute inset-x-0 bottom-0 h-px overflow-hidden">
            <div className="h-full w-1/3 animate-scan bg-gradient-to-r from-transparent via-neon to-transparent" />
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault()
            submit()
          }}
          className="flex items-start gap-3 p-3 pl-4"
        >
          <div className="mt-2 flex items-center gap-1.5 font-mono text-[11px] text-neon">
            <Terminal className="size-4" />
            <span className="hidden sm:inline">athena</span>
            <span className="text-ink-mute">›</span>
          </div>
          <textarea
            ref={ref}
            rows={1}
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value)
              setHistoryIdx(-1)
            }}
            onKeyDown={onKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            disabled={isLoading}
            placeholder="Ask an analytical question…"
            className="min-h-9 flex-1 resize-none bg-transparent py-2 text-[14px] leading-6 text-ink placeholder:text-ink-mute focus:outline-none disabled:opacity-60"
          />
          <div className="flex items-center gap-2 pt-0.5">
            {!focused && !question && !isLoading && (
              <span className="hidden items-center gap-1 md:flex">
                <Kbd>{isMac ? '⌘' : 'Ctrl'}</Kbd>
                <Kbd>K</Kbd>
              </span>
            )}
            <AnimatePresence mode="wait" initial={false}>
              {isLoading ? (
                <motion.button
                  key="stop"
                  type="button"
                  onClick={onCancel}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex h-9 items-center gap-2 rounded-xl border border-alert/40 bg-alert/10 px-3.5 text-xs font-semibold text-rose-200 transition-colors hover:bg-alert/20"
                >
                  <Square className="size-3 fill-current" />
                  Abort
                  <Kbd className="border-alert/30 text-rose-300/80">Esc</Kbd>
                </motion.button>
              ) : (
                <motion.button
                  key="go"
                  type="submit"
                  disabled={!question.trim()}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  whileHover={question.trim() ? { scale: 1.03 } : undefined}
                  whileTap={question.trim() ? { scale: 0.97 } : undefined}
                  className={cn(
                    'relative flex h-9 items-center gap-2 overflow-hidden rounded-xl px-4 text-xs font-semibold transition-all',
                    question.trim()
                      ? 'bg-gradient-to-r from-cyan-400 to-indigo-500 text-abyss shadow-[0_0_24px_-4px_rgba(0,240,255,0.6)]'
                      : 'border border-line bg-white/[0.03] text-ink-mute',
                  )}
                >
                  <Sparkles className="size-3.5" />
                  Analyze
                  <CornerDownLeft className="size-3 opacity-70" />
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </form>
      </motion.div>

      {/* Suggestions */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 font-mono text-[9.5px] uppercase tracking-[0.16em] text-ink-mute">
          Suggested
        </span>
        <AnimatePresence mode="popLayout">
          {prompts.map((p, i) => (
            <motion.button
              layout
              key={p}
              type="button"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => {
                setQuestion(p)
                ref.current?.focus()
              }}
              disabled={isLoading}
              className="max-w-full truncate rounded-full border border-line bg-white/[0.02] px-2.5 py-1 text-[11px] text-ink-dim transition-all hover:border-neon/35 hover:bg-neon/[0.06] hover:text-cyan-100 disabled:opacity-40"
            >
              {p}
            </motion.button>
          ))}
        </AnimatePresence>
        {history.length > 0 && (
          <span
            className="ml-auto flex items-center gap-1 font-mono text-[9.5px] text-ink-mute"
            title="Press ↑ in the command bar to recall"
          >
            <History className="size-3" /> {history.length} recent · ↑
          </span>
        )}
      </div>

      <AnimatePresence>
        {clarificationMessage && (
          <motion.div
            initial={{ opacity: 0, y: -6, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -6, height: 0 }}
            className="overflow-hidden"
          >
            <div className="flex items-start gap-2.5 rounded-xl border border-neon/25 bg-neon/[0.05] px-3.5 py-2.5 text-[12.5px] text-cyan-100">
              <Info className="mt-0.5 size-4 shrink-0 text-neon" />
              <div>
                <div className="mb-0.5 font-mono text-[9.5px] uppercase tracking-[0.16em] text-neon/80">
                  Clarification requested
                </div>
                {clarificationMessage}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
