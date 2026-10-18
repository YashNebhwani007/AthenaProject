import React, { useState } from 'react'
import type { EvidenceRef, ToolResult } from '../api/types'

interface EvidenceChipProps {
  evidence: EvidenceRef
  trace: ToolResult[]
}

export const EvidenceChip: React.FC<EvidenceChipProps> = ({ evidence, trace }) => {
  const [isOpen, setIsOpen] = useState(false)

  const toolResult = trace.find((t) => t.id === evidence.tool_result_id)
  const metricObj = toolResult?.metrics?.find((m) => m.name === evidence.metric)

  return (
    <div style={{ display: 'inline-block', position: 'relative', margin: '2px 4px' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          color: 'var(--accent-indigo)',
          borderRadius: 'var(--radius-full)',
          padding: '2px 8px',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          transition: 'all 0.15s ease',
        }}
      >
        <span>🔍 {evidence.tool_result_id}.{evidence.metric}</span>
        {metricObj && <span style={{ color: 'var(--text-primary)' }}>= {String(metricObj.value)}</span>}
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            bottom: '100%',
            left: '0',
            marginBottom: '8px',
            width: '300px',
            background: '#1e293b',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
            zIndex: 100,
            fontSize: '12px',
            color: 'var(--text-primary)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '6px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              paddingBottom: '4px',
            }}
          >
            <span style={{ fontWeight: 700, color: 'var(--accent-indigo)' }}>
              Tool: {toolResult?.tool || 'unknown'}
            </span>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status: </span>
            <span
              style={{
                color: toolResult?.status === 'ok' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                fontWeight: 600,
              }}
            >
              {toolResult?.status || 'n/a'}
            </span>
            <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
              Runtime: {toolResult?.runtime_ms ? `${toolResult.runtime_ms}ms` : 'n/a'}
            </span>
          </div>

          {toolResult?.args && Object.keys(toolResult.args).length > 0 && (
            <div style={{ marginBottom: '6px' }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: '2px' }}>Arguments:</div>
              <pre
                style={{
                  background: 'var(--bg-main)',
                  padding: '6px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '10px',
                  overflowX: 'auto',
                }}
              >
                {JSON.stringify(toolResult.args, null, 2)}
              </pre>
            </div>
          )}

          {metricObj && (
            <div style={{ marginTop: '6px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
              Metric Value: {String(metricObj.value)} {metricObj.unit}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
