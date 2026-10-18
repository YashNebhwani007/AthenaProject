# ADR-08: Frontend Technology

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D8 — Frontend: React vs Streamlit/Gradio for speed; tradeoff vs polish.

## Context
The brief specifies React + Vite + TypeScript as a default (section 14) but opens D8 for discussion. The UI has specific layout requirements (left panel, center report, right trace) and streaming SSE support.

## Options

### Option A: React + Vite + TypeScript (Recommended)
Full SPA with component-based architecture.

| Dimension | Assessment |
|-----------|-----------|
| Development time | High — 3-5 days for the full UI |
| Polish potential | Excellent — full control over layout, styling, animations |
| SSE support | Excellent — native `EventSource` API |
| Three-panel layout | Easy — CSS Grid or flexbox |
| Evidence chips, expandable sections | Easy — React components |
| Interview showcase | Strong — demonstrates full-stack capability |
| Maintenance | Medium — more code, but well-structured |

### Option B: Streamlit
Rapid prototyping with Python-only frontend.

| Dimension | Assessment |
|-----------|-----------|
| Development time | Low — 1-2 days |
| Polish potential | Limited — constrained layout system, hard to customize |
| SSE support | Poor — Streamlit re-renders on every state change; no native SSE |
| Three-panel layout | Difficult — Streamlit's column system is rigid |
| Evidence chips | Hacky — requires HTML injection |
| Interview showcase | Weak — signals inability to build real frontends |
| Maintenance | Low — less code |

### Option C: Gradio
Similar to Streamlit but with better API component support.

| Dimension | Assessment |
|-----------|-----------|
| Development time | Low — 1-2 days |
| Polish potential | Limited — even more constrained than Streamlit |
| SSE support | Medium — has streaming text but not structured events |
| Three-panel layout | Difficult |
| Interview showcase | Weak — same perception issue as Streamlit |

## Decision
**Option A: React + Vite + TypeScript.**

Rationale:
1. This is a portfolio project. The frontend is what interviewers see first. A Streamlit app signals "I can't build frontends."
2. The UI requirements (three panels, SSE streaming, expandable evidence chips, verification badges) are hard to implement well in Streamlit/Gradio.
3. Development time is higher but justified by the showcase value.
4. React + Vite is the brief's default and the standard modern choice.

### Tech Stack
- **React 18+** with functional components and hooks
- **Vite** for build tooling
- **TypeScript** for type safety
- **CSS Modules** or a utility library (to be decided during implementation — keep it simple)
- **shadcn/ui** components as a starting point (accessible, professional, customizable)
- **Plotly.js** (or react-plotly.js) for chart rendering
- **EventSource API** for SSE consumption

### Layout
```
┌──────────────┬──────────────────────────┬───────────────┐
│  Left Panel  │      Center Panel        │  Right Panel  │
│              │                          │               │
│  - Upload    │  - Question Input        │  - Execution  │
│  - Demo      │  - Report View           │    Trace      │
│    Datasets  │    - TL;DR               │  - Step list  │
│  - Profile   │    - Findings + Evidence │  - Timing     │
│    Card      │    - Charts              │  - Status     │
│              │    - Caveats             │               │
│              │    - Recommendations     │               │
│              │    - Verification Badge  │               │
│              │  - Benchmark Tab         │               │
└──────────────┴──────────────────────────┴───────────────┘
```

### Key Components
- `DatasetPanel` — upload, demo picker, profile card
- `QueryInput` — question text input with submit
- `ReportView` — renders the structured report with findings, evidence chips, charts
- `EvidenceChip` — clickable badge showing tool result ID; expands to show raw tool call
- `VerificationBadge` — "12/12 verified" with color coding
- `ExecutionTrace` — live-updating timeline of agent steps
- `BenchmarkView` — results table with filtering

## Consequences
- Frontend development is a significant time investment (~3-5 days).
- If time is critically short, the brief says to cut visual polish (not the frontend entirely).
- The React app is served as static files by FastAPI in production (single deployment).
