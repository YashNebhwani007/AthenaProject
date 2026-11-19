# ADR-36: Automated Causal Graph Acyclicity Validation

## Status
Accepted

## Context
Athena's causal inference tools and DoWhy/EconML integrations require structural causal models
represented as Directed Acyclic Graphs (DAGs). When users or automated agents construct causal graphs,
inadvertent circular dependencies (cycles) violate DAG requirements, resulting in non-identifiable
causal effects and unhandled runtime exceptions.

## Decision
1. Prior to estimating causal treatment effects, execute cycle detection using Tarjan's strongly
   connected components algorithm or `networkx.is_directed_acyclic_graph()`.
2. If a cycle is detected, fail fast with a structured `ToolResult` error containing the exact cycle path.
3. Provide automated suggestions to break bidirectional feedback loops by introducing temporal lags.

## Consequences
- Prevents opaque mathematical solver crashes during backdoor adjustment set calculation.
- Empowers users with actionable debugging feedback showing the exact cycle cycle nodes.
- Maintains formal mathematical rigor across all causal inference reports.
