import React from 'react'
import Plot from 'react-plotly.js'
import type { Report, ToolResult, VerificationSummary } from '../api/types'
import { EvidenceChip } from './EvidenceChip'
import { VerificationBadge } from './VerificationBadge'

interface ReportViewProps {
  report: Report | null
  verification: VerificationSummary | null
  trace: ToolResult[]
}

export const ReportView: React.FC<ReportViewProps> = ({
  report,
  verification,
  trace,
}) => {
  if (!report) {
    return (
      <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '32px', marginBottom: '12px' }}>📊</div>
        <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
          No Analysis Generated Yet
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Select a dataset and ask an analytical question above to receive an evidence-backed report.
        </p>
      </div>
    )
  }

  // Find Plotly specs from make_plot tool results
  const plotSpecs = trace
    .filter((t) => t.tool === 'make_plot' && t.output?.plotly_spec)
    .map((t) => t.output.plotly_spec)

  return (
    <div className="card" style={{ gap: '20px' }}>
      {/* Header Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '16px',
        }}
      >
        <div>
          <span
            className={`badge ${report.answerable ? 'badge-green' : 'badge-amber'}`}
            style={{ marginBottom: '8px' }}
          >
            {report.answerable ? 'Answerable Claim' : 'Refusal / Data Insufficient'}
          </span>
          <h1
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.3,
            }}
          >
            {report.question}
          </h1>
        </div>
        <VerificationBadge summary={verification} />
      </div>

      {/* Executive Summary TL;DR */}
      <div
        style={{
          background: 'rgba(99, 102, 241, 0.08)',
          borderLeft: '4px solid var(--accent-indigo)',
          borderRadius: 'var(--radius-sm)',
          padding: '16px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--accent-indigo)',
            marginBottom: '4px',
          }}
        >
          Executive Summary
        </div>
        <p style={{ fontSize: '14px', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {report.tldr}
        </p>
      </div>

      {/* Interactive Charts (if make_plot was invoked) */}
      {plotSpecs.length > 0 && (
        <div>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: 'var(--text-secondary)',
              marginBottom: '10px',
            }}
          >
            Visual Evidence
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {plotSpecs.map((spec, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-input)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <Plot
                  data={spec.data || []}
                  layout={{
                    ...(spec.layout || {}),
                    autosize: true,
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    font: { color: '#94a3b8' },
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%', height: '320px' }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Findings with Grounded Evidence Chips */}
      <div>
        <div
          style={{
            fontSize: '12px',
            fontWeight: 700,
            textTransform: 'uppercase',
            color: 'var(--text-secondary)',
            marginBottom: '10px',
          }}
        >
          Grounded Findings ({report.findings.length})
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {report.findings.map((finding) => (
            <div
              key={finding.id}
              style={{
                background: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '6px',
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 700,
                    color: 'var(--accent-indigo)',
                  }}
                >
                  [{finding.id.toUpperCase()}]
                </span>
                <span className="badge badge-indigo" style={{ fontSize: '10px' }}>
                  {finding.claim_type}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '8px' }}>
                {finding.text}
              </p>
              {/* Evidence Chips */}
              {finding.evidence && finding.evidence.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginRight: '4px' }}>
                    Cited Evidence:
                  </span>
                  {finding.evidence.map((ev, i) => (
                    <EvidenceChip key={i} evidence={ev} trace={trace} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Actionable Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: 'var(--text-secondary)',
              marginBottom: '10px',
            }}
          >
            Actionable Guidance ({report.recommendations.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {report.recommendations.map((rec, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(16, 185, 129, 0.05)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
                    Recommendation #{idx + 1}
                  </span>
                  <span className="badge badge-green">
                    Confidence: {rec.confidence.toUpperCase()}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {rec.text}
                </p>
                {rec.supported_by && rec.supported_by.length > 0 && (
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Supported by finding(s): {rec.supported_by.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Caveats & Methodological Limitations */}
      {report.caveats && report.caveats.length > 0 && (
        <div>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: 'var(--accent-amber)',
              marginBottom: '6px',
            }}
          >
            Caveats & Analytical Limitations
          </div>
          <ul
            style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              paddingLeft: '18px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            {report.caveats.map((c, idx) => (
              <li key={idx}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
