import React, { useEffect, useState } from 'react'
import { listDemoDatasets, uploadDataset } from '../api/client'
import type { DatasetProfile, DemoDataset } from '../api/types'

interface DatasetPanelProps {
  selectedDatasetId: string | null
  onDatasetSelected: (datasetId: string, profile?: DatasetProfile) => void
}

export const DatasetPanel: React.FC<DatasetPanelProps> = ({
  selectedDatasetId,
  onDatasetSelected,
}) => {
  const [demoDatasets, setDemoDatasets] = useState<DemoDataset[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listDemoDatasets()
      .then((res) => {
        setDemoDatasets(res.datasets || [])
        // If nothing selected yet, select the first demo dataset
        if (!selectedDatasetId && res.datasets && res.datasets.length > 0) {
          onDatasetSelected(res.datasets[0].id)
        }
      })
      .catch((err) => console.error('Failed to load demo datasets:', err))
  }, [])

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    setError(null)
    try {
      const res = await uploadDataset(file)
      onDatasetSelected(res.dataset_id, res.profile)
    } catch (err: any) {
      setError(err.message || 'File upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }

  return (
    <div className="card" style={{ gap: '16px' }}>
      <div className="card-header">
        <h2 className="card-title">Dataset Selection</h2>
        <span className="badge badge-indigo">DuckDB Powered</span>
      </div>

      {/* Demo Dataset Selector */}
      <div>
        <label
          style={{
            display: 'block',
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            marginBottom: '6px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Preset Benchmark Datasets
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {demoDatasets.map((ds) => {
            const isSelected = selectedDatasetId === ds.id
            return (
              <button
                key={ds.id}
                onClick={() => onDatasetSelected(ds.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: isSelected
                    ? '1px solid var(--accent-indigo)'
                    : '1px solid var(--border-subtle)',
                  background: isSelected
                    ? 'rgba(99, 102, 241, 0.15)'
                    : 'rgba(255, 255, 255, 0.02)',
                  color: isSelected ? '#fff' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '13px' }}>{ds.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {ds.row_count.toLocaleString()} rows • {ds.column_count} cols
                  </div>
                </div>
                {isSelected && <span style={{ color: 'var(--accent-indigo)', fontSize: '14px' }}>●</span>}
              </button>
            )
          })}
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div>
        <label
          style={{
            display: 'block',
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            marginBottom: '6px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Upload Custom Dataset
        </label>
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragActive(true)
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragActive ? 'var(--accent-indigo)' : 'var(--border-subtle)'}`,
            borderRadius: 'var(--radius-md)',
            padding: '20px 14px',
            textAlign: 'center',
            background: dragActive ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-input)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          onClick={() => document.getElementById('dataset-file-input')?.click()}
        >
          <input
            id="dataset-file-input"
            type="file"
            accept=".csv,.parquet"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0])
              }
            }}
          />
          <div style={{ fontSize: '24px', marginBottom: '4px' }}>📁</div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {isUploading ? 'Uploading & profiling...' : 'Drop CSV / Parquet here'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
            or click to browse local files (max 50MB)
          </div>
        </div>
        {error && (
          <div
            style={{
              marginTop: '8px',
              fontSize: '12px',
              color: 'var(--accent-rose)',
              background: 'rgba(244, 63, 94, 0.1)',
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
