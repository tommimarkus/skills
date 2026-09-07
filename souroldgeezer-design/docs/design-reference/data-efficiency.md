# Data-Efficiency Procedure

## Route

Load for Build/Review collections, storage, batches, streams, caches, and
repeated paths. Debt Extract records facts; Lookup reads the matched section;
File Edit returns. Ask about unknown scale only when it changes a material choice.

## Path and shape

Inspect cardinality, growth, dominant operations, lookup frequency, construction,
mutation, allocation/retention, equality, duplicates, ordering, consistency,
transactions, cancellation, cleanup, and ownership. Compare scans, keyed lookup,
ordered/range, and queue/priority shapes. Remove repeated scans/sorts/enumeration,
N+1 IO, unnecessary fields/rows, early materialization, round trips, and unbounded
buffers before cache/parallelism. Push compatible filters/projections/limits to
storage; never claim index use without a plan. Bound batching/streaming/concurrency;
distinguish reusable clients/pools/handlers and factory-managed HTTP clients from
scoped connection/session/transaction handles.

## Evidence and findings

Source evidence supports operation, boundedness, and semantic choices; claimed
gains, bottlenecks, caches, and tuning need workload evidence, owner, rollback.
`SD-Q-5` warns on known avoidable amplification; block only demonstrated
correctness/resource-budget breach. Small/one-off scans, necessary order/duplicates,
justified buffers, and measured tradeoffs are guards.
