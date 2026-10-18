import React, { useState } from 'react'

interface QueryInputProps {
  onSubmit: (question: string) => void
  isLoading: boolean
  onCancel?: () => void
  clarificationMessage?: string | null
}

const SAMPLE_PROMPTS = [
  'What is the overall churn rate across all customers?',
  'Are monthly charges significantly different between churned and active users?',
  'Train a predictive model to forecast customer churn.',
  'What is the correlation between median income and house value?',
]

export const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading,
  onCancel,
  clarificationMessage,
}) => {
  const [question, setQuestion] = useState('')

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || isLoading) return
    onSubmit(question.trim())
  }

  return (
    <div className="card" style={{ gap: '14px' }}>
      <form onSubmit={handleFormSubmit} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          className="input-field"
          placeholder="Ask an analytical question (e.g. 'Are charges significantly different between churned customers?')..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isLoading}
        />
        {isLoading ? (
          <button
            type="button"
            onClick={onCancel}
            className="btn-primary"
            style={{
              background: 'var(--accent-rose)',
              minWidth: '100px',
            }}
          >
            ⏹ Stop
          </button>
        ) : (
          <button
            type="submit"
            className="btn-primary"
            disabled={!question.trim()}
            style={{ minWidth: '110px' }}
          >
            🚀 Analyze
          </button>
        )}
      </form>

      {/* Quick Suggestion Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        <span
          style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          Quick Prompts:
        </span>
        {SAMPLE_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setQuestion(prompt)}
            disabled={isLoading}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
              borderRadius: 'var(--radius-full)',
              padding: '3px 10px',
              fontSize: '11px',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Clarification Alert */}
      {clarificationMessage && (
        <div
          style={{
            background: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            fontSize: '12px',
            color: 'var(--accent-cyan)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>ℹ️</span>
          <span>{clarificationMessage}</span>
        </div>
      )}
    </div>
  )
}
