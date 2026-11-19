# ADR-30: Human-in-the-Loop Interactive Verification Checkpoints

## Status
Accepted

## Context
While Athena's automated verifier loop successfully corrects >85% of claim-evidence inconsistencies,
certain sensitive analytical decisions (e.g. discarding high-missingness columns, overriding
target leakage warnings, or executing high-stakes business recommendations) benefit from explicit analyst approval.

## Decision
1. Introduce optional interactive verification checkpoints triggered before finalized report rendering.
2. If `Settings.human_in_the_loop` is enabled:
   - When verifier Rule V5 encounters high-severity leakage, pause the session and emit a `checkpoint_required` SSE event.
   - The user interface prompts the analyst with an interactive decision modal: "Approve Caveats", "Rerun with Pruning", or "Abort Run".
   - The orchestrator resumes execution only after receiving a signed decision token via `POST /api/sessions/{id}/checkpoint`.
3. In headless or CI/batch mode, default to automated heuristic policy without pausing.

## Consequences
- Prevents autonomous agents from deploying decisions on flagged data without human oversight.
- Empowers domain experts to guide agent trade-offs on complex domain-specific caveats.
- Seamless compatibility with both interactive React UI and automated CI benchmark runs.
