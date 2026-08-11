# API Surface Architecture

Load when a request asks whether HTTP API surfaces should overlap, remain
separate, aggregate, consolidate, standardize, or retire. This procedure owns
HTTP contract portfolio decisions only. It excludes gRPC, GraphQL, DDD,
enterprise governance, organizational design, and architecture-model edits;
delegate model changes through [architecture-pairing.md](architecture-pairing.md).

## Evidence And Default

Start with contract inventories: capability, operation, contract/version,
consumer, trust boundary, lifecycle state, owner named in source if present,
and gateway/client wiring. Trace one consumer journey per proposed overlap.
Use available usage/deprecation evidence, but label its absence. Never infer
traffic, latency, organizational ownership, or runtime benefit from static
contracts.

Default to one canonical HTTP contract per capability and consumer/trust/lifecycle
boundary. Retain separation only when evidence documents a migration,
consumer-specific BFF, public/private trust split, regulatory/regional
separation, or explicit scale/failure-domain need.

## Procedure

1. Inventory contracts and versions, then map each to capability, consumers,
   trust, lifecycle, and gateway/client wiring.
2. Compare consumer journeys and policies (auth, errors, versioning,
   deprecation, and aggregation). Separate observed facts from hypotheses.
3. Choose one decision: **keep**, **separate**, **standardize**, **aggregate**,
   **consolidate**, or **deprecate**. State the boundary, evidence, migration
   effect, and verification layer.
4. In Build, select and justify the portfolio decision in the contract shape.
   In Extract, inventory only; do not emit findings unless debt is requested.
   In Review, emit coded findings below. In Lookup, answer one bounded rule or
   exception with its verification limit.
5. If a decision needs an architecture model, delegate via the existing pairing
   procedure; do not edit an architecture package here.

## Review Taxonomy

- **SAD-A-capability-overlap** — same capability and boundary have competing
  canonical contracts without an intentional separation.
- **SAD-A-policy-drift** — equivalent contracts drift in auth, error, version,
  or lifecycle policy without boundary evidence.
- **SAD-A-consumer-chattiness** — a consumer journey has avoidable sequential
  calls where an aggregation boundary is supported; runtime latency remains
  unproven without runtime evidence.
- **SAD-A-internal-boundary-leak** — an external boundary exposes an internal
  service contract instead of a boundary-owned contract.
- **SAD-A-lifecycle-sprawl** — versions or deprecations lack a retirement
  decision or available lifecycle evidence.
- **SAD-A-duplicated-aggregation** — repeated downstream composition lacks a
  consumer-specific rationale.

For every Review finding, provide code, evidence, affected boundary, severity,
recommended decision, and reference citation. Withhold a finding when the
inventory cannot establish the capability or boundary; request the missing
evidence or report the limit.
