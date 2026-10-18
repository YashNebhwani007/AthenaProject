# Athena AI — Autonomous Data Science & Decision Intelligence Agent

[![CI Test Suite](https://github.com/your-username/AthenaProject/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/AthenaProject)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Athena is an autonomous, evidence-grounded data science agent. While general-purpose LLMs and standard code interpreters produce convincingly written but mathematically hallucinated reports, confuse correlation with causation, and fit machine learning models on target-leaked features, Athena enforces **deterministic tool execution, formal hypothesis testing, leak-free machine learning, and an adversarial 5-point verification and repair loop**.

Every claim in an Athena report is linked directly to a tool execution ID, grounded within a 1% tolerance, checked for statistical significance with multiplicity corrections, and audited for data quality caveats.

![Athena Autonomous Data Science Agent Demo](docs/demo.gif)

---

## Architecture

```mermaid
graph TD
  User["Analyst / Decision Maker"] --> UI["React Frontend / Claude Desktop (MCP)"]
  UI --> API["FastAPI Server (SSE Streaming)"]
  API --> Orchestrator["Athena Orchestrator"]

  subgraph DeterministicTools["Sandboxed Deterministic Tools"]
    Orchestrator --> SQL["DuckDB (AST-Validated Read-Only SQL)"]
    Orchestrator --> Stats["SciPy / Statsmodels (Hypothesis Tests + Effect Sizes)"]
    Orchestrator --> Leak["Data Leakage Auditor (6 Independent Checks)"]
    Orchestrator --> ML["Scikit-Learn / LightGBM (Leak-Free Pipelines)"]
    Orchestrator --> Explain["SHAP Explainability (Global + Local)"]
    Orchestrator --> Viz["Plotly & Matplotlib Visualizations"]
  end

  DeterministicTools --> Trace["Step Execution Trace & Typed Metrics"]
  Trace --> DraftReport["Draft Report Generator with {{tool.metric}} Placeholders"]

  subgraph Verifier["5-Point Adversarial Verifier & Repair Loop"]
    DraftReport --> V1["V1: Numeric Grounding (±1% Rel / 0.005 Abs)"]
    DraftReport --> V2["V2: Claim-Evidence Consistency (p < α, Sign, Effect Size)"]
    DraftReport --> V3["V3: Causal Language Trap Check"]
    DraftReport --> V4["V4: Linkage (Every finding cited, every rec linked)"]
    DraftReport --> V5["V5: Data Quality & Leakage Propagation"]
    V1 & V2 & V3 & V4 & V5 --> Verdict{"All Rules Pass?"}
    Verdict -- "Violations Detected" --> RepairLoop["Repair Prompt to LLM (Up to 2 Iterations)"]
    RepairLoop --> DraftReport
    Verdict -- "All Rules Pass" --> Renderer["Placeholder Renderer"]
  end

  Renderer --> FinalReport["Verified Analytical Report + Interactive Plots"]
  FinalReport --> UI
```

---

## What Does "Verified" Mean?

Athena eliminates ungrounded LLM hallucination through a five-rule formal verification engine:

1. **V1 — Numeric Grounding:** Findings use template placeholders (e.g. `{{t1.p_value}}`) that resolve against executed tool outputs. Literal numbers in free text are checked against cited metrics with a strict 1% relative / 0.005 absolute tolerance. Uncited numbers fail verification.
2. **V2 — Claim-Evidence Consistency:** Claims asserting "significance" require $p < \alpha$ (after family-wise Bonferroni correction). Directional words ("higher", "lower") must match the mathematical effect sign. Qualitative strength labels ("strong", "moderate", "weak") must strictly correspond to standard statistical thresholds (e.g., Pearson $|r| > 0.7$, Cohen's $d > 0.8$).
3. **V3 — Causal Language Trap Check:** Observational analyses cannot use causal verbs (*causes*, *leads to*, *results in*, *due to*) unless an experimental/causal design was executed.
4. **V4 — Structural Linkage:** Every finding must cite at least one valid tool result ID in the execution trace. Every recommendation must link back to specific finding IDs.
5. **V5 — Data Quality & Leakage Propagation:** If high-severity target leakage or severe missingness (>30%) is detected, the report is rejected unless explicit caveats and model metric discounts are prominently highlighted.

If repairs fail after 2 iterations, unverified claims are degraded with visible audit badges.

---

## Benchmark Evaluation

Athena includes a standardized 42-question benchmark across 4 datasets (Telco Churn, Adult Income, California Housing, and Titanic), evaluating 8 question categories:

| Metric | System A1 (Athena Full) | System A2 (Athena Unverified) | System B1 (Plain LLM + Pandas Code) |
|---|:---:|:---:|:---:|
| **Numeric Accuracy** | **95.2%** | 88.1% | 66.7% |
| **Hallucination Rate** | **0.0%** | 4.8% | 28.6% |
| **Causal Trap Catch Rate** | **100.0%** | 60.0% | 0.0% |
| **Target Leakage Precision** | **100.0%** | 83.3% | 33.3% |
| **Target Leakage Recall** | **91.7%** | 75.0% | 41.7% |
| **Refusal / Unanswerable Accuracy** | **100.0%** | 80.0% | 20.0% |
| **Verification Pass Rate** | **97.6%** | N/A | N/A |

Run the benchmark locally:
```bash
python -m benchmark.runner --systems A1,A2,B1 --questions smoke
```

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 1. Clone & Install Backend
```bash
git clone https://github.com/your-username/AthenaProject.git
cd AthenaProject

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```bash
LLM_PROVIDER=openrouter
LLM_API_KEY=your_openrouter_api_key
LLM_MODEL=anthropic/claude-3.5-sonnet
DEMO_MODE=false
```

### 3. Build & Run Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Launch Athena API & Web App
```bash
uvicorn athena.api.main:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Model Context Protocol (MCP) Integration

Athena can be run as an MCP server over `stdio`, giving Claude Desktop, Cursor, and custom agent systems direct access to Athena's verified analytical tools:

```bash
athena-mcp
```

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "athena": {
      "command": "athena-mcp",
      "args": []
    }
  }
}
```
See [`docs/mcp-usage.md`](docs/mcp-usage.md) for full configuration and Python client examples.

---

## Architectural Decision Records (ADRs)

Key architectural decisions are documented under [`docs/adr/`](docs/adr/):

- [ADR-01: Report Generation & Verification Strategy](docs/adr/adr-01-report-generation.md)
- [ADR-02: Orchestrator Architecture & Control Flow](docs/adr/adr-02-orchestrator.md)
- [ADR-03: LLM Provider & Multi-Provider Strategy](docs/adr/adr-03-llm-provider.md)
- [ADR-04: SQL Dialect & Validation Engine](docs/adr/adr-04-sql-validation.md)
- [ADR-05: Machine Learning Tool Scope](docs/adr/adr-05-ml-scope.md)
- [ADR-06: Statistical Test Selection & Correction](docs/adr/adr-06-stats-test-selection.md)
- [ADR-07: Verifier Rule Formalization](docs/adr/adr-07-verification.md)
- [ADR-08: Frontend Architecture & Visualization](docs/adr/adr-08-frontend.md)
- [ADR-09: Deployment Target & Resource Optimization](docs/adr/adr-09-deployment.md)
- [ADR-10: Benchmark Suite Design & Ground Truth](docs/adr/adr-10-benchmark.md)
- [ADR-11: Multi-Table Architecture](docs/adr/adr-11-multi-table.md)
- [ADR-12: Session Persistence Strategy](docs/adr/adr-12-persistence.md)
- [ADR-13: MCP Transport & Packaging](docs/adr/adr-13-mcp-transport.md)

---

## Deployment

Deploy using Docker on Render or any container runtime:

```bash
docker build -t athena .
docker run -p 8000:8000 -e LLM_API_KEY="your-key" athena
```

A turnkey [`render.yaml`](render.yaml) is provided for Render's free tier.
