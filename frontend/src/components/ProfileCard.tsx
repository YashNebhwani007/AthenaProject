import React from 'react'
import type { DatasetProfile } from '../api/types'

interface ProfileCardProps {
  datasetId: string | null
  profile: DatasetProfile | null
  isLoading?: boolean
}

export const ProfileCard: React.FC<ProfileCardProps> = ({
  datasetId,
  profile,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="card" style={{ padding: '24px', textAlign: 'center' }}>
        <div style={{ fontSize: '20px', marginBottom: '8px' }} className="pulse">
          ⚡
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
          Generating exploratory profile...
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="card" style={{ padding: '24px', textAlign: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          Select or upload a dataset to view its profile.
        </div>
      </div>
    )
  }

  const columns = Object.entries(profile.columns || {})

  return (
    <div className="card" style={{ gap: '16px' }}>
      <div className="card-header">
        <div>
          <h2 className="card-title">Dataset Health & Profile</h2>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{datasetId}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-indigo">{profile.row_count.toLocaleString()} rows</span>
          <span className="badge badge-indigo">{profile.column_count} cols</span>
        </div>
      </div>

      {/* Quality Warnings Alert Banner */}
      {profile.quality_warnings && profile.quality_warnings.length > 0 && (
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
          }}
        >
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              color: 'var(--accent-amber)',
              marginBottom: '6px',
            }}
          >
            ⚠️ Data Quality Warnings ({profile.quality_warnings.length})
          </div>
          <ul
            style={{
              fontSize: '11px',
              color: 'var(--text-secondary)',
              paddingLeft: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            {profile.quality_warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Targets & Duplicates Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '10px',
          background: 'rgba(255, 255, 255, 0.02)',
          padding: '10px',
          borderRadius: 'var(--radius-sm)',
          fontSize: '12px',
        }}
      >
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Duplicate rows: </span>
          <span style={{ fontWeight: 600 }}>{profile.duplicate_rows}</span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Targets: </span>
          <span style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>
            {profile.suspected_targets?.join(', ') || 'None detected'}
          </span>
        </div>
      </div>

      {/* Column Schema & Missingness List */}
      <div>
        <div
          style={{
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            marginBottom: '8px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Columns & Completeness
        </div>
        <div
          style={{
            maxHeight: '260px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            paddingRight: '4px',
          }}
        >
          {columns.map(([colName, info]) => {
            const nullPct = info.null_percent || 0
            const barColor =
              nullPct > 30
                ? 'var(--accent-rose)'
                : nullPct > 5
                ? 'var(--accent-amber)'
                : 'var(--accent-emerald)'

            return (
              <div
                key={colName}
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '4px',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px',
                      fontWeight: 500,
                    }}
                  >
                    {colName}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {info.dtype} • {info.unique_count} unique
                  </span>
                </div>
                {/* Missingness Progress Bar */}
                <div
                  style={{
                    height: '4px',
                    background: 'rgba(255, 255, 255, 0.06)',
                    borderRadius: '2px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(100, Math.max(0, 100 - nullPct))}%`,
                      background: barColor,
                    }}
                  />
                </div>
                {nullPct > 0 && (
                  <div
                    style={{
                      fontSize: '10px',
                      color: barColor,
                      marginTop: '2px',
                      textAlign: 'right',
                    }}
                  >
                    {nullPct.toFixed(1)}% null
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
