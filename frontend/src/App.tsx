import { AnimatePresence, motion } from 'framer-motion'
import React, { useState } from 'react'
import { BenchmarkView } from './components/BenchmarkView'
import { DatasetPanel } from './components/DatasetPanel'
import { ExecutionTrace } from './components/ExecutionTrace'
import { type AppTab, Header } from './components/Header'
import { MissionStatus } from './components/MissionStatus'
import { ProfileCard } from './components/ProfileCard'
import { QueryInput } from './components/QueryInput'
import { ReportView } from './components/ReportView'
import { InspectorProvider } from './components/ToolInspector'
import { useAthenaSession } from './hooks/useAthenaSession'
import { formatCompact, formatMs } from './lib/format'

const pageTransition = {
  initial: { opacity: 0, y: 10, filter: 'blur(6px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
  exit: { opacity: 0, y: -10, filter: 'blur(6px)' },
  transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] as const },
}

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AppTab>('workspace')
  const s = useAthenaSession()

  return (
    <InspectorProvider>
      <div className="cockpit-backdrop" aria-hidden>
        <div className="cockpit-orb -left-40 top-20 size-[520px] bg-brand/[0.10]" />
        <div className="cockpit-orb -right-32 top-[40%] size-[460px] bg-neon/[0.06] [animation-delay:-6s]" />
      </div>
      <div className="scanlines" aria-hidden />

      <div className="relative z-10 flex min-h-full flex-col">
        <Header activeTab={activeTab} onTabChange={setActiveTab} isAnalyzing={s.isAnalyzing} />

        <AnimatePresence mode="wait">
          {activeTab === 'benchmark' ? (
            <motion.main
              key="benchmark"
              {...pageTransition}
              className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-6 lg:px-6"
            >
              <BenchmarkView />
            </motion.main>
          ) : (
            <motion.main
              key="workspace"
              {...pageTransition}
              className="mx-auto grid w-full max-w-[1920px] flex-1 grid-cols-[minmax(0,1fr)] gap-4 px-4 py-4 lg:grid-cols-[300px_minmax(0,1fr)] lg:px-6 xl:grid-cols-[300px_minmax(0,1fr)_380px] xl:overflow-hidden xl:h-[calc(100vh-56px-32px)]"
            >
              {/* Left: data sources & health */}
              <aside className="flex min-w-0 flex-col gap-4 xl:overflow-y-auto xl:pb-2 xl:pr-1">
                <DatasetPanel selectedDatasetId={s.selectedDatasetId} onDatasetSelected={s.selectDataset} />
                <ProfileCard datasetId={s.selectedDatasetId} profile={s.profile} isLoading={s.isLoadingProfile} />
              </aside>

              {/* Center: command + report */}
              <section className="flex min-w-0 flex-col gap-4 xl:overflow-y-auto xl:pb-6 xl:pr-1">
                <QueryInput
                  onSubmit={s.ask}
                  isLoading={s.isAnalyzing}
                  onCancel={s.cancel}
                  clarificationMessage={s.clarification}
                  datasetId={s.selectedDatasetId}
                />
                <MissionStatus
                  stage={s.stage}
                  message={s.currentStepMsg}
                  question={s.question}
                  startedAt={s.startedAt}
                  endedAt={s.endedAt}
                  toolCount={s.trace.length}
                  verifyIterations={s.verifyIterations}
                />
                <ReportView
                  report={s.report}
                  verification={s.verification}
                  trace={s.trace}
                  isAnalyzing={s.isAnalyzing}
                  errorMessage={s.errorMessage}
                  isDraft={s.isDraft}
                  runMeta={s.runMeta}
                  hasDataset={!!s.selectedDatasetId}
                />
              </section>

              {/* Right: flight recorder */}
              <aside className="min-h-0 min-w-0 lg:col-span-2 xl:col-span-1 xl:pb-2">
                <ExecutionTrace
                  trace={s.trace}
                  isExecuting={s.isAnalyzing}
                  currentStepMessage={s.currentStepMsg}
                  errorMessage={s.errorMessage}
                  pendingStep={s.pendingStep}
                  log={s.log}
                />
              </aside>
            </motion.main>
          )}
        </AnimatePresence>

        {/* Telemetry footer */}
        <footer className="sticky bottom-0 z-30 border-t border-line bg-abyss/80 backdrop-blur-xl">
          <div className="mx-auto flex h-8 max-w-[1920px] items-center gap-4 overflow-hidden px-4 font-mono text-[10px] text-ink-mute lg:px-6">
            <FootItem k="dataset" v={s.selectedDatasetId ?? '—'} />
            <FootItem k="session" v={s.sessionId ? s.sessionId.slice(0, 12) : '—'} />
            <FootItem k="stage" v={s.stage} accent={s.isAnalyzing} />
            <FootItem k="tools" v={String(s.trace.length)} />
            {s.runMeta && (
              <>
                <FootItem k="runtime" v={formatMs(s.runMeta.total_runtime_ms)} />
                <FootItem k="tokens" v={formatCompact(s.runMeta.total_tokens)} />
              </>
            )}
            <span className="ml-auto hidden sm:inline">ATHENA · deterministic tools · verified claims</span>
          </div>
        </footer>
      </div>
    </InspectorProvider>
  )
}

const FootItem: React.FC<{ k: string; v: string; accent?: boolean }> = ({ k, v, accent }) => (
  <span className="flex shrink-0 items-center gap-1.5">
    <span className="uppercase tracking-[0.14em]">{k}</span>
    <span className={accent ? 'text-neon' : 'text-ink-dim'}>{v}</span>
  </span>
)

export default App
