import { Check, Copy } from 'lucide-react'
import React, { useMemo, useState } from 'react'
import { cn } from '../lib/cn'

const SQL_KEYWORDS =
  /\b(SELECT|FROM|WHERE|GROUP|BY|ORDER|HAVING|LIMIT|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|NOT|IN|IS|NULL|CASE|WHEN|THEN|ELSE|END|WITH|DISTINCT|COUNT|SUM|AVG|MIN|MAX|STDDEV|CAST|UNION|ALL|DESC|ASC|OVER|PARTITION|BETWEEN|LIKE)\b/gi

type Token = { text: string; cls?: string }

function tokenizeSql(sql: string): Token[] {
  const out: Token[] = []
  const re = new RegExp(
    `('(?:[^']|'')*')|(\\b\\d+(?:\\.\\d+)?\\b)|${SQL_KEYWORDS.source}|(--[^\\n]*)`,
    'gi',
  )
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(sql))) {
    if (m.index > last) out.push({ text: sql.slice(last, m.index) })
    if (m[1]) out.push({ text: m[0], cls: 'text-amber-300' })
    else if (m[2]) out.push({ text: m[0], cls: 'text-emerald-300' })
    else if (m[4]) out.push({ text: m[0], cls: 'text-ink-mute italic' })
    else out.push({ text: m[0], cls: 'text-neon font-semibold' })
    last = re.lastIndex
  }
  if (last < sql.length) out.push({ text: sql.slice(last) })
  return out
}

function tokenizeJson(json: string): Token[] {
  const out: Token[] = []
  const re = /("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(json))) {
    if (m.index > last) out.push({ text: json.slice(last, m.index) })
    if (m[1] && m[2]) {
      out.push({ text: m[1], cls: 'text-indigo-300' })
      out.push({ text: m[2], cls: 'text-ink-mute' })
    } else if (m[1]) out.push({ text: m[1], cls: 'text-amber-200/90' })
    else if (m[3]) out.push({ text: m[0], cls: 'text-rose-300' })
    else out.push({ text: m[0], cls: 'text-emerald-300' })
    last = re.lastIndex
  }
  if (last < json.length) out.push({ text: json.slice(last) })
  return out
}

interface CodeBlockProps {
  code: string
  lang?: 'sql' | 'json' | 'text'
  className?: string
  maxHeight?: number
  label?: string
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  lang = 'json',
  className,
  maxHeight = 320,
  label,
}) => {
  const [copied, setCopied] = useState(false)
  const tokens = useMemo(
    () => (lang === 'sql' ? tokenizeSql(code) : lang === 'json' ? tokenizeJson(code) : [{ text: code }]),
    [code, lang],
  )

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1400)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className={cn('group relative overflow-hidden rounded-xl border border-line bg-black/40', className)}>
      <div className="flex items-center justify-between border-b border-line bg-white/[0.02] px-3 py-1.5">
        <span className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-ink-mute">
          {label ?? lang}
        </span>
        <button
          type="button"
          onClick={copy}
          className="flex items-center gap-1 rounded px-1.5 py-0.5 font-mono text-[9.5px] text-ink-mute transition-colors hover:bg-white/5 hover:text-ink"
        >
          {copied ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
          {copied ? 'copied' : 'copy'}
        </button>
      </div>
      <pre
        className="overflow-auto p-3 font-mono text-[11px] leading-[1.6] text-ink-dim"
        style={{ maxHeight }}
      >
        <code>
          {tokens.map((t, i) =>
            t.cls ? (
              <span key={i} className={t.cls}>
                {t.text}
              </span>
            ) : (
              <React.Fragment key={i}>{t.text}</React.Fragment>
            ),
          )}
        </code>
      </pre>
    </div>
  )
}
