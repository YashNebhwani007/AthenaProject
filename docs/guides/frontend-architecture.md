# Frontend Architecture & SSE Streaming State Manual

Athena's frontend is a responsive single-page React 18 application styled with Tailwind CSS,
designed to render real-time analytical traces, interactive Plotly visualizations, and verified decision reports.

---

## 1. Tech Stack
- **Framework:** React 18 with TypeScript (`strict: true`)
- **Build Tool:** Vite with Hot Module Replacement (HMR)
- **Styling:** Tailwind CSS + Lucide React icon set
- **Charts:** Plotly.js (`plotly.js-dist-min`) + React-Plotly
- **Streaming:** Server-Sent Events (SSE) via native `EventSource` and `fetch` polyfill

---

## 2. Component Hierarchy
```
App.tsx
├── Header (Session & Model Status, Dataset Picker)
├── Main Workspace
│   ├── Left Column: ExecutionTrace.tsx
│   │   ├── StepTimeline (Tool invocation cards, runtime ms)
│   │   └── TokenBudgetMeter (Input/Output token meters)
│   └── Right Column: ReportView.tsx
│       ├── ExecutiveSummary (TL;DR block)
│       ├── FindingsAccordion (Categorized claims + tool citations)
│       ├── Visualizations (Plotly chart container)
│       ├── RecommendationsCard (Numbered action items + confidence pills)
│       └── CaveatsList (Data quality warnings & limitations)
└── Footer (Verification Status Badge)
```

---

## 3. SSE Stream State Machine
During an analytical run, the frontend ingests a stream of typed SSE events:
1. `step_start`: Agent initiates a tool call (`tool_name`, `args`).
2. `step_complete`: Tool outputs metrics and artifacts (`runtime_ms`, `metrics`).
3. `verification_start`: Report draft submitted to 5-point adversarial verifier.
4. `verification_repair`: Issue detected; agent initiates repair loop iteration.
5. `final_report`: Verified decision report delivered with placeholders resolved.
6. `stream_end`: Run finalized; connection cleanly terminated.
