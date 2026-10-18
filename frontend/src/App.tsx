import React, { useState } from 'react'
import { createSession, getProfile, askQuestionStream } from './api/client'
import type { DatasetProfile, Report, ToolResult, VerificationSummary } from './api/types'
import { DatasetPanel } from './components/DatasetPanel'
import { ProfileCard } from './components/ProfileCard'
import { QueryInput } from './components/QueryInput'
import { ReportView } from './components/ReportView'
import { ExecutionTrace } from './components/ExecutionTrace'
import { BenchmarkView } from './components/BenchmarkView'

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'workspace' | 'benchmark'>('workspace')

  // Dataset & Session state
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [profile, setProfile] = useState<DatasetProfile | null>(null)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Execution & Report state
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [currentStepMsg, setCurrentStepMsg] = useState<string | null>(null)
  const [trace, setTrace] = useState<ToolResult[]>([])
  const [report, setReport] = useState<Report | null>(null)
  const [verification, setVerification] = useState<VerificationSummary | null>(null)
  const [cancelStream, setCancelStream] = useState<(() => void) | null>(null)
  const [clarification, setClarification] = useState<string | null>(null)

  const handleDatasetSelected = async (datasetId: string, providedProfile?: DatasetProfile) => {
    setSelectedDatasetId(datasetId)
    setReport(null)
    setTrace([])
    setVerification(null)
    setClarification(null)

    // Load profile if not provided directly
    if (providedProfile) {
      setProfile(providedProfile)
    } else {
      setIsLoadingProfile(true)
      try {
        const res = await getProfile(datasetId)
        setProfile(res.profile)
      } catch (err) {
        console.error('Failed to load profile:', err)
      } finally {
        setIsLoadingProfile(false)
      }
    }

    // Create session for dataset
    try {
      const sess = await createSession(datasetId)
      setSessionId(sess.session_id)
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }

  const handleAsk = async (question: string) => {
    if (!selectedDatasetId) {
      alert('Please select or upload a dataset before asking a question.')
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
        alert('Could not initialize session for query.')
        return
      }
    }

    setIsAnalyzing(true)
    setCurrentStepMsg('Initializing analysis plan...')
    setReport(null)
    setVerification(null)
    setTrace([])
    setClarification(null)

    const cancelFn = askQuestionStream(
      activeSessionId,
      question,
      (msg) => {
        if (msg.event === 'tool_result') {
          const toolResult = msg.data as ToolResult
          setTrace((prev) => [...prev, toolResult])
          setCurrentStepMsg(`Completed tool: ${toolResult.tool}`)
        } else if (msg.event === 'report_draft') {
          if (msg.data?.report) {
            setReport(msg.data.report)
          }
          setCurrentStepMsg('Drafting findings and computing grounded evidence...')
        } else if (msg.event === 'verification') {
          if (msg.data?.summary) {
            setVerification(msg.data.summary)
          }
          setCurrentStepMsg('Running 5-point rigorous verification rules...')
        } else if (msg.event === 'final') {
          if (msg.data?.run_result) {
            const run = msg.data.run_result
            setReport(run.report)
            setVerification(run.verification)
            if (run.trace && run.trace.length > 0) {
              setTrace(run.trace)
            }
          }
          setIsAnalyzing(false)
          setCurrentStepMsg(null)
        } else if (msg.event === 'clarification_needed') {
          setClarification(msg.data?.message || 'Further dataset clarification required.')
          setIsAnalyzing(false)
          setCurrentStepMsg(null)
        } else if (msg.event === 'error') {
          setCurrentStepMsg(`Error: ${msg.data?.message || JSON.stringify(msg.data)}`)
          setIsAnalyzing(false)
        }
      },
      () => {
        setIsAnalyzing(false)
        setCurrentStepMsg(null)
      },
      (err) => {
        console.error('SSE Stream error:', err)
        setIsAnalyzing(false)
        setCurrentStepMsg('Analysis connection interrupted.')
      }
    )

    setCancelStream(() => cancelFn)
  }

  const handleCancel = () => {
    if (cancelStream) {
      cancelStream()
      setCancelStream(null)
    }
    setIsAnalyzing(false)
    setCurrentStepMsg('Analysis canceled.')
  }

  return (
    <div className="app-container">
      {/* Top Application Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo">A</div>
          <div>
            <span className="brand-title">ATHENA</span>
            <span className="brand-badge" style={{ marginLeft: '10px' }}>
              Autonomous Data Scientist
            </span>
          </div>
        </div>

        <nav className="header-tabs">
          <button
            type="button"
            className={`tab-btn ${activeTab === 'workspace' ? 'active' : ''}`}
            onClick={() => setActiveTab('workspace')}
          >
            ⚡ Analysis Workspace
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
            onClick={() => setActiveTab('benchmark')}
          >
            📊 Benchmark Evaluation
          </button>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Dual-Model • Auto-Verified
          </span>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            style={{
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              fontSize: '13px',
              padding: '6px 12px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            GitHub
          </a>
        </div>
      </header>

      {/* Main Tab Content */}
      {activeTab === 'benchmark' ? (
        <main style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
          <BenchmarkView />
        </main>
      ) : (
        <main className="main-layout">
          {/* Left Column: Dataset & Data Quality Profile */}
          <aside style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <DatasetPanel
              selectedDatasetId={selectedDatasetId}
              onDatasetSelected={handleDatasetSelected}
            />
            <ProfileCard
              datasetId={selectedDatasetId}
              profile={profile}
              isLoading={isLoadingProfile}
            />
          </aside>

          {/* Center Column: Query Input & Verified Analytical Report */}
          <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <QueryInput
              onSubmit={handleAsk}
              isLoading={isAnalyzing}
              onCancel={handleCancel}
              clarificationMessage={clarification}
            />
            <ReportView report={report} verification={verification} trace={trace} />
          </section>

          {/* Right Column: Execution Trace Timeline */}
          <aside style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <ExecutionTrace
              trace={trace}
              isExecuting={isAnalyzing}
              currentStepMessage={currentStepMsg}
            />
          </aside>
        </main>
      )}
    </div>
  )
}

export default App
