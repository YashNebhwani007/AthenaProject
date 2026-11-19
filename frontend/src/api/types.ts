/**
 * Athena TypeScript API types matching backend schemas.
 */

export type ToolStatus = 'ok' | 'error'

export interface Metric {
  name: string
  value: number | string
  unit: string
}

export interface Artifact {
  type: string
  ref: string
}

export interface ToolResult {
  id: string
  tool: string
  args: Record<string, any>
  status: ToolStatus
  output: any
  metrics: Metric[]
  artifacts: Artifact[]
  warnings: string[]
  runtime_ms: number
}

export type ClaimType =
  | 'descriptive'
  | 'comparative'
  | 'statistical'
  | 'predictive'
  | 'causal'

export interface EvidenceRef {
  tool_result_id: string
  metric: string
}

export interface Finding {
  id: string
  text: string
  claim_type: ClaimType
  evidence: EvidenceRef[]
}

export type Confidence = 'low' | 'medium' | 'high'

export interface Recommendation {
  text: string
  supported_by: string[]
  confidence: Confidence
}

export interface Report {
  question: string
  answerable: boolean
  tldr: string
  findings: Finding[]
  caveats: string[]
  recommendations: Recommendation[]
}

export interface VerificationResult {
  rule: string
  finding_id?: string | null
  passed: boolean
  issue?: string | null
  suggestion?: string | null
}

export interface VerificationSummary {
  total_checks: number
  passed: number
  failed: number
  unverified_claims: number
  repairs_attempted: number
  details: VerificationResult[]
}

export interface RunResult {
  run_id: string
  session_id: string
  question: string
  report: Report
  verification: VerificationSummary
  trace: ToolResult[]
  created_at?: string
  total_steps: number
  total_tokens: number
  total_runtime_ms: number
}

export interface DatasetHandle {
  dataset_id: string
  table_name: string
  row_count: number
  column_count: number
}

export interface DatasetProfile {
  row_count: number
  column_count: number
  columns: Record<
    string,
    {
      dtype: string
      null_count: number
      null_percent: number
      unique_count: number
      min?: any
      max?: any
      mean?: any
      std?: any
    }
  >
  quality_warnings: string[]
  suspected_targets: string[]
  duplicate_rows: number
}

export interface DemoDataset {
  id: string
  name: string
  path: string
  format: string
  row_count: number
  column_count: number
  description: string
  target_column?: string
}

export type SSEEventType =
  | 'step_started'
  | 'tool_result'
  | 'report_draft'
  | 'verification'
  | 'final'
  | 'error'
  | 'status'
  | 'clarification_needed'

export interface StepStartedPayload {
  step_index: number
  tool: string
  args: Record<string, any>
}

export interface VerificationEventPayload {
  summary: VerificationSummary
  iteration: number
  repaired: boolean
}

export interface FinalReportPayload {
  run_result: RunResult
}

export interface SSEMessage {
  event: SSEEventType
  data: any
}
