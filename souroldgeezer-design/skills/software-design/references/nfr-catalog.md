# Software Design NFR Catalog

Load only when non-functional/quality requirements, SLAs/SLOs, latency/
availability/throughput targets, or quality attributes are in scope. Do not
expand into a generic quality-engineering tutorial; rely on the base model for
attribute definitions and keep this aid focused on naming, measuring,
allocating, and delegating. For each in-scope NFR require `Name`, `Scenario`,
`Owner`; otherwise treat as `SD-Q-1` (no measure) or `SD-Q-3` (no owner).

## 1. Name from the taxonomy

Check each in-scope NFR against the ISO/IEC 25010 (SQuaRE) product-quality
characteristics so a category is not silently dropped. Current edition
(ISO/IEC 25010:2023): Functional Suitability, Performance Efficiency,
Compatibility, Interaction Capability, Reliability, Security, Maintainability,
Flexibility, Safety. (Verify the edition and exact set against the official ISO
source before relying on it; the 2011 edition used Usability and Portability and
omitted Safety.) Names anchor vocabulary only; depth per attribute is delegated.

## 2. Make it measurable (quality-attribute scenario)

Express each in-scope NFR as a scenario, not an adjective:

`stimulus` (triggering condition) -> `artifact` (the boundary under load) ->
`response` (observable behavior) -> `response measure` (the threshold).

Example: at 2x peak request rate (stimulus), the pricing module (artifact)
returns a quote (response) with p99 latency under 200 ms (response measure).

An NFR with no response measure is a claim, not a requirement: sharpen it before
treating it as a design force (`SD-Q-1`).

## 3. Allocate to an owning boundary

Every in-scope NFR names the boundary accountable for meeting it. An NFR with no
owning boundary is `SD-Q-3`: assign it to one owner, or split it across owners
with explicit per-owner measures.

## Discipline

| Item | Rule |
|---|---|
| Force | A measured quality requirement shapes the design; an unmeasured one does not. |
| Smell map | Missing measure -> `SD-Q-1`; unmeasured tactic -> `SD-Q-2`; no owning boundary -> `SD-Q-3`. |
| Evidence | Threshold needs `[runtime]`; owner/scope needs `[human]`; presence is `[static]`. |
| Delegation | Per-attribute tactics go to `app-design` / `api-design` / `infra-design`, `devsecops-audit`, `test-quality-audit`. |
