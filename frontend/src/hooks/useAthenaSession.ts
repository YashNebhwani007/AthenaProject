/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useRef, useState } from 'react'
import { askQuestionStream, createSession, getProfile } from '../api/client'
import type {
  DatasetProfile,
  Report,
  RunResult,
  SSEMessage,
  StepStartedPayload,
  ToolResult,
  VerificationSummary,
} from '../api/types'

export type RunStage =
  | 'idle'
  | 'planning'
  | 'executing'
  | 'drafting'
  | 'verifying'
  | 'complete'
  | 'clarify'
  | 'error'
  | 'canceled'

export type LogKind = 'info' | 'tool' | 'draft' | 'verify' | 'final' | 'warn' | 'error'

export interface LogEntry {
  id: number
  t: number // ms since run start
  kind: LogKind
  text: string
}

export interface RunMeta {
  run_id: string
  total_steps: number
  total_tokens: number
  total_runtime_ms: number
}

export interface PendingStep {
  tool: string
  args: Record<string, any>
  step_index: number
}

export function useAthenaSession() {
  // Dataset & session
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [profile, setProfile] = useState<DatasetProfile | null>(null)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Run
  const [question, setQuestion] = useState<string | null>(null)
  const [stage, setStage] = useState<RunStage>('idle')
  const [currentStepMsg, setCurrentStepMsg] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [trace, setTrace] = useState<ToolResult[]>([])
  const [pendingStep, setPendingStep] = useState<PendingStep | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [isDraft, setIsDraft] = useState(false)
  const [verification, setVerification] = useState<VerificationSummary | null>(null)
  const [verifyIterations, setVerifyIterations] = useState(0)
  const [clarification, setClarification] = useState<string | null>(null)
  const [runMeta, setRunMeta] = useState<RunMeta | null>(null)
  const [log, setLog] = useState<LogEntry[]>([])
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const [endedAt, setEndedAt] = useState<number | null>(null)

  const cancelRef = useRef<(() => void) | null>(null)
  const startRef = useRef<number>(0)
  const logSeq = useRef(0)

  const isAnalyzing = ['planning', 'executing', 'drafting', 'verifying'].includes(stage)

  const pushLog = useCallback((kind: LogKind, text: string) => {
    const entry: LogEntry = {
      id: ++logSeq.current,
      t: startRef.current ? performance.now() - startRef.current : 0,
      kind,
      text,
    }
    setLog((prev) => [...prev.slice(-199), entry])
  }, [])

  const resetRun = useCallback(() => {
    setReport(null)
    setIsDraft(false)
    setTrace([])
    setPendingStep(null)
    setVerification(null)
    setVerifyIterations(0)
    setClarification(null)
    setErrorMessage(null)
    setRunMeta(null)
    setCurrentStepMsg(null)
  }, [])

  const selectDataset = useCallback(
    async (datasetId: string, providedProfile?: DatasetProfile) => {
      cancelRef.current?.()
      cancelRef.current = null
      setSelectedDatasetId(datasetId)
      resetRun()
      setQuestion(null)
      setStage('idle')
      setLog([])
      setStartedAt(null)
      setEndedAt(null)

      if (providedProfile) {
        setProfile(providedProfile)
      } else {
        setIsLoadingProfile(true)
        setProfile(null)
        try {
          const res = await getProfile(datasetId)
          setProfile(res.profile)
        } catch (err) {
          console.error('Failed to load profile:', err)
        } finally {
          setIsLoadingProfile(false)
        }
      }

      try {
        const sess = await createSession(datasetId)
        setSessionId(sess.session_id)
      } catch (err) {
        console.error('Failed to create session:', err)
        setSessionId(null)
      }
    },
    [resetRun],
  )

  const finish = useCallback((next: RunStage) => {
    setStage(next)
    setPendingStep(null)
    setEndedAt(performance.now())
    cancelRef.current = null
  }, [])

  const handleEvent = useCallback(
    (msg: SSEMessage) => {
      const { event, data } = msg
      switch (event) {
        case 'step_started': {
          const p = data as StepStartedPayload
          setPendingStep(p)
          setStage('executing')
          setCurrentStepMsg(`Dispatching ${p.tool}…`)
          pushLog('info', `dispatch → ${p.tool}`)
          break
        }
        case 'status': {
          const text = data?.message || data?.status || (typeof data === 'string' ? data : '')
          if (text) {
            setCurrentStepMsg(text)
            pushLog('info', text)
          }
          break
        }
        case 'tool_result': {
          const tr = data as ToolResult
          setTrace((prev) => [...prev, tr])
          setPendingStep(null)
          setStage('executing')
          setCurrentStepMsg(`Completed ${tr.tool}`)
          pushLog(
            tr.status === 'ok' ? 'tool' : 'error',
            `${tr.id || '·'} ${tr.tool} ${tr.status === 'ok' ? 'ok' : 'ERR'} ${Math.round(tr.runtime_ms ?? 0)}ms · ${tr.metrics?.length ?? 0} metrics`,
          )
          break
        }
        case 'report_draft': {
          if (data?.report) {
            setReport(data.report)
            setIsDraft(true)
          }
          setStage('drafting')
          setCurrentStepMsg('Drafting findings and binding grounded evidence…')
          pushLog('draft', `draft report · ${data?.report?.findings?.length ?? 0} findings`)
          break
        }
        case 'verification': {
          if (data?.summary) setVerification(data.summary)
          setVerifyIterations((n) => n + 1)
          setStage('verifying')
          setCurrentStepMsg('Running 5-point verification rules…')
          const s = data?.summary as VerificationSummary | undefined
          pushLog(
            s && s.failed > 0 ? 'warn' : 'verify',
            s ? `verify ${s.passed}/${s.total_checks} passed · ${s.failed} failed` : 'verification pass',
          )
          break
        }
        case 'final': {
          if (data?.run_result) {
            const run = data.run_result as RunResult
            if (run.report) setReport(run.report)
            if (run.verification) setVerification(run.verification)
            if (run.trace && run.trace.length > 0) setTrace(run.trace)
            setRunMeta({
              run_id: run.run_id,
              total_steps: run.total_steps,
              total_tokens: run.total_tokens,
              total_runtime_ms: run.total_runtime_ms,
            })
          } else if (data?.report) {
            setReport(data.report)
            if (data.verification) setVerification(data.verification)
          }
          setIsDraft(false)
          setCurrentStepMsg(null)
          pushLog('final', 'final report delivered')
          finish('complete')
          break
        }
        case 'clarification_needed': {
          const m = data?.message || 'Further dataset clarification required.'
          setClarification(m)
          setCurrentStepMsg(null)
          pushLog('warn', `clarification: ${m}`)
          finish('clarify')
          break
        }
        case 'error': {
          const errMsg = data?.error || data?.message || JSON.stringify(data)
          setErrorMessage(errMsg)
          setCurrentStepMsg(`Error: ${errMsg}`)
          pushLog('error', errMsg)
          finish('error')
          break
        }
        default:
          break
      }
    },
    [finish, pushLog],
  )

  const ask = useCallback(
    async (q: string) => {
      if (!selectedDatasetId) {
        setErrorMessage('Select or upload a dataset before asking a question.')
        setStage('error')
        return
      }

      let activeSessionId = sessionId
      if (!activeSessionId) {
        try {
          const sess = await createSession(selectedDatasetId)
          activeSessionId = sess.session_id
          setSessionId(sess.session_id)
        } catch (err) {
          console.error('Failed to create session:', err)
          setErrorMessage('Could not initialize an analysis session.')
          setStage('error')
          return
        }
      }

      cancelRef.current?.()
      resetRun()
      setQuestion(q)
      setStage('planning')
      setCurrentStepMsg('Initializing analysis plan…')
      startRef.current = performance.now()
      setStartedAt(startRef.current)
      setEndedAt(null)
      logSeq.current = 0
      setLog([])
      pushLog('info', `query accepted · dataset=${selectedDatasetId}`)

      const datasetId = selectedDatasetId

      const startStreaming = (targetSessionId: string, isRetry = false) => {
        const cancelFn = askQuestionStream(
          targetSessionId,
          q,
          handleEvent,
          () => {
            // Stream closed: if no terminal event arrived, settle gracefully.
            setStage((s) =>
              ['planning', 'executing', 'drafting', 'verifying'].includes(s) ? 'complete' : s,
            )
            setPendingStep(null)
            setCurrentStepMsg(null)
            setEndedAt((e) => e ?? performance.now())
          },
          async (err) => {
            if (
              !isRetry &&
              (err?.message?.includes('404') || err?.message?.includes('Session'))
            ) {
              try {
                setCurrentStepMsg('Re-establishing analytical session…')
                pushLog('warn', 'session lost — reconnecting')
                const sess = await createSession(datasetId)
                setSessionId(sess.session_id)
                startStreaming(sess.session_id, true)
                return
              } catch (reErr) {
                console.error('Session reconnection failed:', reErr)
              }
            }
            console.error('SSE Stream error:', err)
            const errText = err?.message || 'Analysis connection interrupted.'
            setErrorMessage(errText)
            setCurrentStepMsg(`Error: ${errText}`)
            pushLog('error', errText)
            finish('error')
          },
          datasetId,
        )
        cancelRef.current = cancelFn
      }

      startStreaming(activeSessionId)
    },
    [selectedDatasetId, sessionId, resetRun, pushLog, handleEvent, finish],
  )

  const cancel = useCallback(() => {
    cancelRef.current?.()
    cancelRef.current = null
    setCurrentStepMsg('Analysis canceled.')
    pushLog('warn', 'run aborted by operator')
    finish('canceled')
  }, [finish, pushLog])

  useEffect(() => () => cancelRef.current?.(), [])

  return {
    selectedDatasetId,
    profile,
    isLoadingProfile,
    sessionId,
    question,
    stage,
    isAnalyzing,
    currentStepMsg,
    errorMessage,
    trace,
    pendingStep,
    report,
    isDraft,
    verification,
    verifyIterations,
    clarification,
    runMeta,
    log,
    startedAt,
    endedAt,
    selectDataset,
    ask,
    cancel,
  }
}

export type AthenaSession = ReturnType<typeof useAthenaSession>
