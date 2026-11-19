# Athena React Frontend

The Athena frontend is a React 18 single-page application engineered for real-time observability
of autonomous analytical agent trajectories and interactive exploration of decision reports.

---

## 1. Quick Start

```bash
cd frontend

# Install Node dependencies
npm install

# Run local development server with Vite HMR
npm run dev

# Build production bundle (emits to dist/)
npm run build
```

---

## 2. Directory Structure

```
frontend/src/
├── api/             # HTTP client and TypeScript interfaces
│   ├── client.ts    # Fetch and SSE stream listeners
│   └── types.ts     # Data models and discriminated union types
├── components/      # Modular UI components
│   ├── BenchmarkView.tsx   # Benchmark scorecards and evaluation matrices
│   ├── DatasetPicker.tsx   # Demo dataset selection dropdown
│   ├── ExecutionTrace.tsx  # Step-by-step tool timeline and token meters
│   └── ReportView.tsx      # Verified markdown report with KaTeX
├── styles/          # Tailwind configuration and theme tokens
├── App.tsx          # Root application workspace layout
└── main.tsx         # React DOM mounting entrypoint
```

---

## 3. Streaming Event Ingestion
The UI connects to `/api/sessions/{id}/ask` using Server-Sent Events (SSE). Incoming events are
parsed into typed payloads via `frontend/src/api/types.ts` and update the active trace timeline
without blocking the main JavaScript rendering thread.
