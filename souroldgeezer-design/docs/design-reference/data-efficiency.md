# Data-Efficiency Procedure

Use for touched collections or storage paths in Build/Review and explicit debt
assessment. Factual Extract records the access path and unknown scale without
prescribing changes. Lookup reads the matched section; escalate to Build/Review
for cross-section decisions. File Edit returns before this procedure.

## 1. Establish the path and its semantics

Record expected cardinality and growth, dominant operations, lookup frequency,
and the request or batch boundary. Leave unknown scale unknown; ask only when
it changes a material choice. Preserve ordering, duplicates, equality, mutation
semantics, consistency, transactions, cancellation, cleanup, and ownership.

## 2. Compare the smallest compatible shape

A direct scan can be the clearest choice for small bounded inputs or one-off
work. For repeated membership or key lookup, compare a local keyed structure's
construction and retained memory with repeated scans. Use ordered/range
structures or queue/priority operations when those are the dominant needs.
Account for mutation, allocation, key stability, and index maintenance. A set
can discard required duplicates; a keyed index must not silently choose among
duplicate keys or replace output order. There is no universal collection default.

Identify repeated scans, sorting, or enumeration from the actual call path.
Reduce repeated work before adding a cache or parallelism. Avoid claiming a
runtime improvement from an operation-count comparison alone.

## 3. Shape storage work deliberately

Trace queries and round trips, including N+1 IO, unnecessary fields or rows,
early materialization, repeated enumeration, and unbounded intermediate buffers.
Push compatible filters, projections, and limits to storage while preserving
authorization and result semantics. A bounded response does not bound preceding
retrieval or materialization. Inspect query/index compatibility; confirm index
use from a query plan, not its mere definition. Account for write/index costs.

Choose bounded batching or streaming when appropriate; check whether the provider
buffers internally. Preserve snapshot/transaction, cancellation, failure and
cleanup contracts, and bound concurrency. Reusable clients, pools, and handlers
are distinct from scoped connection/session/transaction handles; preserve
supported factory-managed HTTP clients. Do not invent a batch size or pool limit.

## 4. Calibrate evidence and report

Source evidence supports operation-count, boundedness, and semantic decisions;
it does not require a profile. Measured gains, bottleneck attribution, caches,
and added tuning complexity need representative workload evidence, ownership,
and an appropriate rollback. Separate static/graph facts from runtime impact.

Software findings use `SD-Q-5` for source-grounded avoidable amplification or
unbounded work against a known access pattern. Warn with workload and consequence;
block only a demonstrated correctness/resource-budget breach. Small bounded
inputs, one-off scans, necessary ordering/duplicates, justified buffering, and
measured tradeoffs are guards. HTTP-to-storage findings belong to API-design's
data-access code; report each defect once under its owner.
