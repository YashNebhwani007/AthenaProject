# ADR-02: Orchestrator Design

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D2 — Orchestrator: hand-rolled loop vs LangGraph vs another framework.

## Context
The orchestrator runs a tool-calling loop with budgets, retries, loop detection, and clarification logic. It must be debuggable, testable, and impressive in interviews.

## Options

### Option A: Hand-Rolled Loop (Recommended)
A custom async Python loop that calls the LLM, dispatches tool calls, tracks budgets, and handles errors.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — must implement loop, budgets, retries, error handling manually |
| Debuggability | Excellent — full control, simple stack traces, easy to log |
| Testability | Excellent — can mock LLM client, inject tool results, test loop logic in isolation |
| Dependency risk | None — no framework to break or deprecate |
| Interview showcase | Strong — demonstrates deep understanding of agent architecture, not "I used a library" |
| Cost | Zero additional dependencies |

### Option B: LangGraph
Use LangGraph's state machine for the tool-calling loop.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low initially, but high when customizing (budget enforcement, custom retry logic, verifier integration) |
| Debuggability | Poor — complex graph execution model, hard to trace through framework internals |
| Testability | Medium — framework's abstractions make unit testing harder |
| Dependency risk | High — LangGraph API is unstable, breaking changes between versions |
| Interview showcase | Weak — signals framework dependence, not engineering skill |
| Cost | Additional dependency (~50+ transitive packages) |

### Option C: Instructor / Mirascope / other lightweight framework
Use a tool-calling helper library that handles JSON schema generation and response parsing.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low for the tool-calling part, but still need custom loop for budgets/retries |
| Debuggability | Good — thinner abstraction layer |
| Dependency risk | Medium — API changes possible but smaller blast radius |
| Interview showcase | Neutral — depends on which library |

## Decision
**Option A: Hand-Rolled Loop.**

Rationale:
1. The orchestrator IS the core of Athena. Building it demonstrates the deepest understanding.
2. The loop logic (budgets, retries, loop detection, clarification) is custom enough that a framework adds more friction than value.
3. Zero dependency risk. The implementation can be fully understood and explained in an interview.
4. The tool-calling protocol is simple: send messages with tool results, get back tool calls or a final response. This doesn't need a framework.

Architecture:
```
class Orchestrator:
    async def run(question, dataset_handle, config) -> RunResult:
        steps = []
        while budget.has_remaining():
            response = await llm.chat(messages, tools=tool_schemas)
            if response.is_final:
                break
            for tool_call in response.tool_calls:
                result = await dispatch_tool(tool_call)
                steps.append(Step(tool_call, result))
                messages.append(tool_result_message(result))
        draft_report = parse_report(response.content)
        verified_report = await verifier.verify(draft_report, steps)
        return RunResult(report=verified_report, trace=steps)
```

## Consequences
- Must implement: message management, tool dispatch, budget tracking (steps, tokens, wall-clock), retry logic with backoff, loop/repetition detection, error classification.
- More code to write, but each piece is unit-testable.
- No framework lock-in.
