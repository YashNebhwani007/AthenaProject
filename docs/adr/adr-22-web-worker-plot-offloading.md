# ADR-22: Web Worker Offloading for Large Interactive Visualizations

## Status
Accepted

## Context
When Athena visualizes high-dimensional datasets (such as California Housing block groups or
multivariate scatter plots with >20,000 coordinate pairs), generating Plotly WebGL buffers
or computing client-side binning on the main JavaScript thread causes perceptible frame drops
and interface freezing during live streaming.

## Decision
1. Offload heavy client-side coordinate parsing, histogram bin calculations, and JSON deserialization to dedicated Web Workers (`worker-pool.ts`).
2. Transmit structured array buffers between the main UI thread and Web Workers using `Transferable Objects` to eliminate costly memory clones.
3. Automatically downsample scatter plots exceeding 10,000 points using the Largest-Triangle-Three-Buckets (LTTB) algorithm prior to rendering.

## Consequences
- The main thread maintains 60 FPS responsiveness during heavy data ingestion.
- Background worker crashes do not terminate the user session.
- Seamless interactivity for zoom and pan across multi-thousand record plots.
