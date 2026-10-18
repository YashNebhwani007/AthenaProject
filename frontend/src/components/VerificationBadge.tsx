import React, { useState } from 'react'
import type { VerificationSummary } from '../api/types'

interface VerificationBadgeProps {
  summary: VerificationSummary | null
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({ summary }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!summary || summary.total_checks === 0) {
    return (
      <div className="badge badge-indigo" style={{ padding: '4px 10px' }}>
        <span>Pending Verification</span>
      </div>
    )
  }

  const isAllPassed = summary.failed === 0
  const badgeClass = isAllPassed
    ? 'badge-green'
    : summary.passed > 0
    ? 'badge-amber'
    : 'badge-red'

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`badge ${badgeClass}`}
        style={{
          cursor: 'pointer',
          padding: '6px 12px',
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          border: 'none',
        }}
      >
        <span>{isAllPassed ? '🛡️' : '⚠️'}</span>
        <span>
          {summary.passed}/{summary.total_checks} Checks Verified
        </span>
        <span style={{ fontSize: '10px' }}>{isExpanded ? '▲' : '▼'}</span>
      </button>

      {isExpanded && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: '8px',
            width: '360px',
            background: '#1e293b',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
            zIndex: 100,
            fontSize: '12px',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '10px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              paddingBottom: '6px',
            }}
          >
            <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
              Automated Verifier Audit
            </span>
            <span style={{ color: 'var(--text-muted)' }}>
              Repairs: {summary.repairs_attempted}
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              maxHeight: '260px',
              overflowY: 'auto',
            }}
          >
            {summary.details?.map((check, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px',
                  borderRadius: 'var(--radius-sm)',
                  background: check.passed
                    ? 'rgba(16, 185, 129, 0.08)'
                    : 'rgba(244, 63, 94, 0.08)',
                  borderLeft: `3px solid ${
                    check.passed ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                  }`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    [{check.rule}]{' '}
                    {check.finding_id ? `Finding ${check.finding_id}` : 'Global'}
                  </span>
                  <span
                    style={{
                      color: check.passed
                        ? 'var(--accent-emerald)'
                        : 'var(--accent-rose)',
                      fontWeight: 600,
                    }}
                  >
                    {check.passed ? 'PASSED' : 'FAILED'}
                  </span>
                </div>
                {check.issue && (
                  <div
                    style={{
                      marginTop: '4px',
                      color: 'var(--text-secondary)',
                      fontSize: '11px',
                    }}
                  >
                    {check.issue}
                  </div>
                )}
                {check.suggestion && (
                  <div
                    style={{
                      marginTop: '2px',
                      color: 'var(--accent-cyan)',
                      fontSize: '11px',
                    }}
                  >
                    💡 {check.suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
