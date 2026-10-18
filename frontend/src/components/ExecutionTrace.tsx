import React, { useEffect, useRef, useState } from 'react'
import type { ToolResult } from '../api/types'

interface ExecutionTraceProps {
  trace: ToolResult[]
  isExecuting?: boolean
  currentStepMessage?: string | null
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({
  trace,
  isExecuting,
  currentStepMessage,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [trace, isExecuting])

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="card" style={{ gap: '14px', height: '100%', minHeight: '500px' }}>
      <div className="card-header">
        <div>
          <h2 className="card-title">Execution Trace</h2>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Deterministic Tool Calling Timeline
          </div>
        </div>
        <span className="badge badge-indigo">{trace.length} Steps</span>
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          overflowY: 'auto',
          flex: 1,
          paddingRight: '4px',
        }}
      >
        {trace.length === 0 && !isExecuting && (
          <div
            style={{
              padding: '24px 12px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '12px',
            }}
          >
            No tool calls dispatched yet. Submit a query to inspect live execution.
          </div>
        )}

        {trace.map((step, idx) => {
          const isExpanded = expandedId === step.id
          const isOk = step.status === 'ok'

          return (
            <div
              key={step.id || idx}
              style={{
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-input)',
                overflow: 'hidden',
                transition: 'all 0.15s ease',
              }}
            >
              {/* Step Summary Bar */}
              <button
                onClick={() => toggleExpand(step.id)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'transparent',
                  border: 'none',
                  color: 'inherit',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      color: 'var(--accent-indigo)',
                      fontWeight: 700,
                    }}
                  >
                    {step.id || `t${idx + 1}`}
                  </span>
                  <span style={{ fontSize: '13px', fontWeight: 600 }}>{step.tool}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {step.runtime_ms ? `${Math.round(step.runtime_ms)}ms` : ''}
                  </span>
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: isOk ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                    }}
                  />
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    {isExpanded ? '▲' : '▼'}
                  </span>
                </div>
              </button>

              {/* Expanded Inspection Pane */}
              {isExpanded && (
                <div
                  style={{
                    padding: '10px 12px',
                    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                    background: 'rgba(0, 0, 0, 0.2)',
                    fontSize: '11px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  {step.args && Object.keys(step.args).length > 0 && (
                    <div>
                      <div style={{ color: 'var(--text-muted)', marginBottom: '2px' }}>
                        Arguments:
                      </div>
                      <pre
                        style={{
                          background: 'var(--bg-main)',
                          padding: '6px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '10px',
                          overflowX: 'auto',
                        }}
                      >
                        {JSON.stringify(step.args, null, 2)}
                      </pre>
                    </div>
                  )}

                  {step.metrics && step.metrics.length > 0 && (
                    <div>
                      <div style={{ color: 'var(--text-muted)', marginBottom: '2px' }}>
                        Exported Metrics ({step.metrics.length}):
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {step.metrics.map((m, mIdx) => (
                          <span
                            key={mIdx}
                            style={{
                              background: 'rgba(6, 182, 212, 0.1)',
                              border: '1px solid rgba(6, 182, 212, 0.25)',
                              color: 'var(--accent-cyan)',
                              padding: '2px 6px',
                              borderRadius: 'var(--radius-sm)',
                              fontFamily: 'var(--font-mono)',
                              fontSize: '10px',
                            }}
                          >
                            {m.name}: {String(m.value)} {m.unit}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {step.warnings && step.warnings.length > 0 && (
                    <div style={{ color: 'var(--accent-amber)' }}>
                      ⚠️ {step.warnings.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {/* Live execution indicator */}
        {isExecuting && (
          <div
            style={{
              padding: '12px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(99, 102, 241, 0.08)',
              border: '1px dashed var(--accent-indigo)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '12px',
            }}
          >
            <div className="pulse" style={{ fontSize: '14px' }}>
              ⚡
            </div>
            <div style={{ color: 'var(--accent-indigo)', fontWeight: 500 }}>
              {currentStepMessage || 'Reasoning & dispatching tool calls...'}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
