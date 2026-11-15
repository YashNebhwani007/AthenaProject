/**
 * Athena Frontend API and SSE streaming client.
 */

import type { DatasetProfile, DemoDataset, RunResult, SSEMessage } from './types'

const API_BASE = '/api'

export async function uploadDataset(file: File): Promise<{
  dataset_id: string
  filename: string
  row_count: number
  column_count: number
  profile: DatasetProfile
}> {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/datasets`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function getProfile(datasetId: string): Promise<{
  dataset_id: string
  profile: DatasetProfile
}> {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}/profile`)
  if (!res.ok) {
    throw new Error(`Failed to load profile for ${datasetId}`)
  }
  return res.json()
}

export async function listDemoDatasets(): Promise<{ datasets: DemoDataset[] }> {
  const res = await fetch(`${API_BASE}/demo-datasets`)
  if (!res.ok) {
    throw new Error('Failed to list demo datasets')
  }
  return res.json()
}

export async function createSession(datasetId: string): Promise<{
  session_id: string
  dataset_id: string
}> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId }),
  })
  if (!res.ok) {
    throw new Error('Failed to create session')
  }
  return res.json()
}

export function askQuestionStream(
  sessionId: string,
  question: string,
  onEvent: (msg: SSEMessage) => void,
  onComplete?: () => void,
  onError?: (err: any) => void,
  datasetId?: string | null
): () => void {
  const controller = new AbortController()

  fetch(`${API_BASE}/sessions/${sessionId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, dataset_id: datasetId }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok || !response.body) {
        const errorText = await response.text().catch(() => '')
        let message = `Streaming connection failed (HTTP ${response.status})`
        try {
          const parsed = JSON.parse(errorText)
          if (parsed.detail) message = parsed.detail
        } catch {}
        throw new Error(message)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const processBlock = (block: string) => {
        if (!block.trim()) return
        let eventType = 'message'
        let dataStr = ''

        for (const line of block.split('\n')) {
          const trimmed = line.trim()
          if (trimmed.startsWith('event:')) {
            eventType = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            const val = trimmed.slice(5).trim()
            dataStr = dataStr ? `${dataStr}\n${val}` : val
          }
        }

        if (dataStr) {
          try {
            const parsedData = JSON.parse(dataStr)
            onEvent({ event: eventType as any, data: parsedData })
          } catch {
            onEvent({ event: eventType as any, data: dataStr })
          }
        }
      }

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        // Normalize CRLF (\r\n) and CR (\r) to LF (\n) so \n\n splitting reliably finds SSE blocks
        const normalized = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
        const blocks = normalized.split('\n\n')
        // Last block may be incomplete until next read
        buffer = blocks.pop() || ''

        for (const block of blocks) {
          processBlock(block)
        }
      }

      // Process any trailing complete block left in buffer
      if (buffer.trim()) {
        const normalized = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
        const blocks = normalized.split('\n\n')
        for (const block of blocks) {
          processBlock(block)
        }
      }

      onComplete?.()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

  return () => controller.abort()
}

export async function getRun(runId: string): Promise<RunResult> {
  const res = await fetch(`${API_BASE}/runs/${runId}`)
  if (!res.ok) {
    throw new Error(`Run ${runId} not found`)
  }
  return res.json()
}

export async function getBenchmarkResults(): Promise<any> {
  const res = await fetch(`${API_BASE}/benchmark/results`)
  if (!res.ok) {
    throw new Error('Benchmark results not found')
  }
  return res.json()
}
