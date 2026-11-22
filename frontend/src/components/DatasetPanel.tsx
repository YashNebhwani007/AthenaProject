import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Loader2,
  ShieldAlert,
  Target,
  UploadCloud,
} from 'lucide-react'
import React, { useEffect, useRef, useState } from 'react'
import { listDemoDatasets, uploadDataset } from '../api/client'
import type { DatasetProfile, DemoDataset } from '../api/types'
import { cn } from '../lib/cn'
import { formatCompact } from '../lib/format'
import {  } from '../lib/tones'
import { Panel, PanelHeader, Pill, SectionLabel, Skeleton } from './ui/primitives'

interface DatasetPanelProps {
  selectedDatasetId: string | null
  onDatasetSelected: (datasetId: string, profile?: DatasetProfile) => void
}

interface UploadedDataset {
  id: string
  name: string
  rows: number
  cols: number
}

export const DatasetPanel: React.FC<DatasetPanelProps> = ({
  selectedDatasetId,
  onDatasetSelected,
}) => {
  const [demoDatasets, setDemoDatasets] = useState<DemoDataset[]>([])
  const [uploaded, setUploaded] = useState<UploadedDataset[]>([])
  const [isListing, setIsListing] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const didInit = useRef(false)

  useEffect(() => {
    if (didInit.current) return
    didInit.current = true
    listDemoDatasets()
      .then((res) => {
        setDemoDatasets(res.datasets || [])
        if (!selectedDatasetId && res.datasets && res.datasets.length > 0) {
          onDatasetSelected(res.datasets[0].id)
        }
      })
      .catch((err) => {
        console.error('Failed to load demo datasets:', err)
        setError('Could not reach the Athena API. Is the backend running on :8000?')
      })
      .finally(() => setIsListing(false))
  }, [selectedDatasetId, onDatasetSelected])

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    setError(null)
    try {
      const res = await uploadDataset(file)
      setUploaded((prev) => [
        { id: res.dataset_id, name: res.filename || file.name, rows: res.row_count, cols: res.column_count },
        ...prev.filter((u) => u.id !== res.dataset_id),
      ])
      onDatasetSelected(res.dataset_id, res.profile)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'File upload failed')
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
    <Panel className="flex flex-col gap-4 p-4">
      <PanelHeader
        icon={Database}
        title="Data Sources"
        subtitle="DuckDB · in-process OLAP"
        right={<Pill tone="neon">{demoDatasets.length + uploaded.length} mounted</Pill>}
      />

      <div>
        <SectionLabel>Preset Datasets</SectionLabel>
        <div className="flex flex-col gap-1.5">
          {isListing &&
            Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[52px]" />)}

          {uploaded.map((u) => (
            <DatasetRow
              key={u.id}
              active={selectedDatasetId === u.id}
              onClick={() => onDatasetSelected(u.id)}
              name={u.name}
              meta={`${formatCompact(u.rows)} rows · ${u.cols} cols`}
              format="upload"
            />
          ))}

          {demoDatasets.map((ds, i) => (
            <motion.div
              key={ds.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04, duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            >
              <DatasetRow
                active={selectedDatasetId === ds.id}
                onClick={() => onDatasetSelected(ds.id)}
                name={ds.name}
                meta={`${formatCompact(ds.row_count)} rows · ${ds.column_count} cols`}
                format={ds.format}
                target={ds.target_column}
                leakage={ds.id.includes('leakage')}
                description={ds.description}
              />
            </motion.div>
          ))}
        </div>
      </div>

      <div>
        <SectionLabel>Ingest Custom</SectionLabel>
        <motion.button
          type="button"
          onDragOver={(e) => {
            e.preventDefault()
            setDragActive(true)
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
          animate={dragActive ? { scale: 1.015 } : { scale: 1 }}
          className={cn(
            'group relative flex w-full flex-col items-center overflow-hidden rounded-xl border border-dashed px-4 py-5 text-center transition-all duration-300',
            dragActive
              ? 'border-neon bg-neon/[0.06] shadow-[0_0_30px_-6px_var(--color-neon),inset_0_0_30px_-12px_var(--color-neon)]'
              : 'border-line-strong bg-white/[0.015] hover:border-neon/40 hover:bg-neon/[0.03]',
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.parquet"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) handleFileUpload(e.target.files[0])
              e.target.value = ''
            }}
          />
          {(dragActive || isUploading) && (
            <span className="pointer-events-none absolute inset-y-0 left-0 w-1/4 animate-scan bg-gradient-to-r from-transparent via-neon/20 to-transparent" />
          )}
          <div
            className={cn(
              'mb-2 grid size-9 place-items-center rounded-lg border transition-colors',
              dragActive
                ? 'border-neon/50 text-neon'
                : 'border-line-strong text-ink-dim group-hover:text-neon',
            )}
          >
            {isUploading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <UploadCloud className="size-4" />
            )}
          </div>
          <div className="text-xs font-semibold text-ink">
            {isUploading ? 'Ingesting & profiling…' : dragActive ? 'Release to ingest' : 'Drop CSV / Parquet'}
          </div>
          <div className="mt-0.5 font-mono text-[10px] text-ink-mute">or click to browse · max 50MB</div>
        </motion.button>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-2 flex items-start gap-2 rounded-lg border border-alert/25 bg-alert/[0.07] px-3 py-2 text-[11px] text-rose-200">
                <AlertTriangle className="mt-px size-3.5 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Panel>
  )
}

const DatasetRow: React.FC<{
  active: boolean
  onClick: () => void
  name: string
  meta: string
  format: string
  target?: string
  leakage?: boolean
  description?: string
}> = ({ active, onClick, name, meta, format, target, leakage, description }) => (
  <button
    type="button"
    onClick={onClick}
    title={description}
    className={cn(
      'group relative flex w-full items-center gap-3 overflow-hidden rounded-xl border px-3 py-2.5 text-left transition-all duration-300',
      active
        ? 'border-neon/30 bg-gradient-to-r from-neon/[0.09] to-brand/[0.04]'
        : 'border-line bg-white/[0.015] hover:border-line-strong hover:bg-white/[0.035]',
    )}
  >
    {active && (
      <motion.span
        layoutId="dataset-active-rail"
        className="absolute inset-y-2 left-0 w-[2px] rounded-full bg-neon shadow-[0_0_10px_var(--color-neon)]"
        transition={{ type: 'spring', stiffness: 500, damping: 38 }}
      />
    )}
    <div
      className={cn(
        'grid size-8 shrink-0 place-items-center rounded-lg border transition-colors',
        active ? 'border-neon/30 bg-neon/10 text-neon' : 'border-line text-ink-mute group-hover:text-ink-dim',
      )}
    >
      {leakage ? <ShieldAlert className="size-4" /> : <FileSpreadsheet className="size-4" />}
    </div>
    <div className="min-w-0 flex-1">
      <div className={cn('truncate text-[12.5px] font-medium', active ? 'text-ink' : 'text-ink-dim')}>
        {name}
      </div>
      <div className="mt-0.5 flex min-w-0 items-center gap-2 font-mono text-[10px] text-ink-mute">
        <span className="shrink-0 whitespace-nowrap">{meta}</span>
        {target && (
          <span className="flex min-w-0 items-center gap-0.5 truncate text-emerald-400/80">
            <Target className="size-2.5" />
            {target}
          </span>
        )}
      </div>
    </div>
    <div className="flex shrink-0 flex-col items-end gap-1">
      <span className="font-mono text-[9px] uppercase tracking-wider text-ink-mute">{format}</span>
      {active && <CheckCircle2 className="size-3.5 text-neon" />}
    </div>
  </button>
)
