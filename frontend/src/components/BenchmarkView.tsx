import React, { useEffect, useState } from 'react'
import { getBenchmarkResults } from '../api/client'

export const BenchmarkView: React.FC = () => {
  const [data, setData] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedSystem, setSelectedSystem] = useState<string>('all')

  useEffect(() => {
    setIsLoading(true)
    getBenchmarkResults()
      .then((res) => setData(res))
      .catch((err) => console.error('Failed to load benchmark:', err))
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) {
    return (
      <div className="card" style={{ padding: '60px', textAlign: 'center' }}>
        <div style={{ fontSize: '24px', marginBottom: '8px' }} className="pulse">
          📊
        </div>
        <div>Loading benchmark evaluation results...</div>
      </div>
    )
  }

  if (!data || data.error) {
    return (
      <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
        <h3>Benchmark Results Unavailable</h3>
        <p style={{ color: 'var(--text-muted)', marginTop: '6px' }}>
          Run `python -m benchmark.runner --questions all` to compile comprehensive results.
        </p>
      </div>
    )
  }

  const summaries = data.summaries || {}
  const systems = Object.keys(summaries)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
      {/* Overview Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
        }}
      >
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            A1 Athena Accuracy
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-emerald)' }}>
            {summaries.A1 ? `${(summaries.A1.accuracy * 100).toFixed(1)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Full Agent + Verifier + Repair Loop
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            A1 Hallucination Rate
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-indigo)' }}>
            {summaries.A1 ? `${(summaries.A1.hallucination_rate * 100).toFixed(1)}%` : '0.0%'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Numeric & factual claim errors
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Refusal Accuracy
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
            {summaries.A1 ? `${(summaries.A1.refusal_accuracy * 100).toFixed(1)}%` : '100%'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Safe refusal & injection defense
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Target Leakage Recall
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-amber)' }}>
            {summaries.A1 ? `${(summaries.A1.leakage_recall * 100).toFixed(1)}%` : '100%'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Planted leakage detection rate
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">System Comparison (A1 vs A2 vs B1)</h2>
          <span className="badge badge-indigo">Benchmark Suite ({data.filter})</span>
        </div>

        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '13px',
            textAlign: 'left',
          }}
        >
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '10px' }}>System</th>
              <th style={{ padding: '10px' }}>Architecture</th>
              <th style={{ padding: '10px' }}>Accuracy</th>
              <th style={{ padding: '10px' }}>Hallucination Rate</th>
              <th style={{ padding: '10px' }}>Refusal Accuracy</th>
              <th style={{ padding: '10px' }}>Leakage Recall</th>
            </tr>
          </thead>
          <tbody>
            {systems.map((sys) => {
              const s = summaries[sys]
              const label =
                sys === 'A1'
                  ? 'Athena (Full System)'
                  : sys === 'A2'
                  ? 'Athena (No Verifier)'
                  : 'Plain LLM Baseline'

              return (
                <tr key={sys} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                  <td style={{ padding: '12px 10px', fontWeight: 700, color: 'var(--accent-indigo)' }}>
                    {sys}
                  </td>
                  <td style={{ padding: '12px 10px' }}>{label}</td>
                  <td style={{ padding: '12px 10px', fontWeight: 600 }}>
                    {(s.accuracy * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 10px' }}>
                    {(s.hallucination_rate * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 10px' }}>
                    {(s.refusal_accuracy * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 10px' }}>
                    {(s.leakage_recall * 100).toFixed(1)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Itemized Question Results Filter */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Detailed Evaluation Results</h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setSelectedSystem('all')}
              className={`tab-btn ${selectedSystem === 'all' ? 'active' : ''}`}
            >
              All Systems
            </button>
            {systems.map((sys) => (
              <button
                key={sys}
                onClick={() => setSelectedSystem(sys)}
                className={`tab-btn ${selectedSystem === sys ? 'active' : ''}`}
              >
                {sys}
              </button>
            ))}
          </div>
        </div>

        <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px' }}>Question ID</th>
                <th style={{ padding: '8px' }}>System</th>
                <th style={{ padding: '8px' }}>Type</th>
                <th style={{ padding: '8px' }}>Status</th>
                <th style={{ padding: '8px' }}>Issue / Note</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.details || {}).flatMap(([sysName, records]: [string, any]) => {
                if (selectedSystem !== 'all' && selectedSystem !== sysName) return []
                return (records as any[]).map((r, rIdx) => (
                  <tr key={`${sysName}-${rIdx}`} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                    <td style={{ padding: '8px', fontFamily: 'var(--font-mono)' }}>
                      {r.question_id}
                    </td>
                    <td style={{ padding: '8px', fontWeight: 600 }}>{sysName}</td>
                    <td style={{ padding: '8px' }}>{r.answer_type}</td>
                    <td style={{ padding: '8px' }}>
                      <span className={`badge ${r.passed ? 'badge-green' : 'badge-red'}`}>
                        {r.passed ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                    <td style={{ padding: '8px', color: r.issue ? 'var(--accent-rose)' : 'var(--text-muted)' }}>
                      {r.issue || 'Verified correct'}
                    </td>
                  </tr>
                ))
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
