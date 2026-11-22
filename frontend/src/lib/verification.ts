import type { VerificationResult, VerificationSummary } from '../api/types'
import type { Tone } from './tones'

export interface RuleGroup {
  rule: string
  passed: number
  failed: number
  checks: VerificationResult[]
}

export function groupByRule(details: VerificationResult[] = []): RuleGroup[] {
  const map = new Map<string, RuleGroup>()
  for (const d of details) {
    const g = map.get(d.rule) ?? { rule: d.rule, passed: 0, failed: 0, checks: [] }
    if (d.passed) g.passed++
    else g.failed++
    g.checks.push(d)
    map.set(d.rule, g)
  }
  return [...map.values()].sort((a, b) => b.failed - a.failed || a.rule.localeCompare(b.rule))
}

export function prettyRule(rule: string): string {
  return rule.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function scoreTone(summary: VerificationSummary): Tone {
  if (summary.failed === 0) return 'laser'
  return summary.passed / Math.max(1, summary.total_checks) >= 0.7 ? 'warn' : 'alert'
}

