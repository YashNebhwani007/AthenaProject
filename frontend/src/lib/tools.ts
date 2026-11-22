import {
  BarChart3,
  Brain,
  Database,
  FlaskConical,
  type LucideIcon,
  ScanSearch,
  ShieldAlert,
  Sigma,
  Sparkles,
  Wand2,
  Wrench,
} from 'lucide-react'
import type { Tone } from './tones'

export interface ToolMeta {
  icon: LucideIcon
  tone: Tone
  family: string
}

const TOOL_META: Record<string, ToolMeta> = {
  profile: { icon: ScanSearch, tone: 'neon', family: 'profiling' },
  run_sql: { icon: Database, tone: 'neon', family: 'duckdb' },
  duckdb_query: { icon: Database, tone: 'neon', family: 'duckdb' },
  recommend_test: { icon: Wand2, tone: 'brand', family: 'stats' },
  stats_test: { icon: Sigma, tone: 'brand', family: 'stats' },
  train_model: { icon: Brain, tone: 'laser', family: 'ml' },
  predict_model: { icon: Sparkles, tone: 'laser', family: 'ml' },
  explain_model: { icon: FlaskConical, tone: 'laser', family: 'shap' },
  shap_explain: { icon: FlaskConical, tone: 'laser', family: 'shap' },
  check_leakage: { icon: ShieldAlert, tone: 'warn', family: 'audit' },
  make_plot: { icon: BarChart3, tone: 'brand', family: 'viz' },
}

export function toolMeta(tool: string): ToolMeta {
  return TOOL_META[tool] ?? { icon: Wrench, tone: 'mute', family: 'tool' }
}

/** Pull a SQL string out of tool args, if one is present. */
export function extractSql(args: Record<string, unknown> | undefined): string | null {
  if (!args) return null
  for (const k of ['sql', 'query', 'statement']) {
    const v = args[k]
    if (typeof v === 'string' && /\b(select|with|from)\b/i.test(v)) return v
  }
  return null
}
