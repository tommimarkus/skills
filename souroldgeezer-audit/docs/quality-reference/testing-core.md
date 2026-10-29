# Test Quality — Shared Core

Shared discipline and shared sources for the three lane rubrics
([unit-testing.md](unit-testing.md), [integration-testing.md](integration-testing.md),
[e2e-testing.md](e2e-testing.md)). Lane rubrics cite this file; per-lane
adaptations stay in the lane rubric.

## Shared discipline

- **Scope statement common to all three rubrics.** These documents do not
  analyze any specific codebase; they state principles, smells, and rubrics.
- **Trustworthy, readable, maintainable** — Osherove's three pillars; the
  canonical definition lives in [unit-testing.md §2.6](unit-testing.md). A test
  failing these pillars removes coverage without visible cost. Each lane rubric
  keeps only its lane-specific consequence sentence (integration §2.8, e2e §2.8).

## Pinned expectations and re-pin review

Assess individual assertions, including mixed assertions in one test; filenames,
hash equality, snapshot syntax, repeated failures, or re-pin history alone do
not establish coupling. Before recommending an update, identify the protected
contract and expectation source: an accepted requirement, compatibility promise,
reviewed source/artifact, or justified baseline. Inspect the underlying source
and behavioral delta rather than accepting regenerated output.

- **Implementation regression:** preserve the expectation; recommend fixing the
  implementation.
- **Intentional contract change:** update the obsolete expectation with the
  contract rationale under the project's behavioral-change discipline.
- **Legitimate artifact-identity change:** after reviewing the changed artifact
  and provenance, update its identity expectation while retaining semantic and
  compatibility checks. Computing a digest of reviewed bytes establishes
  identity, not semantic correctness.
- **Incidental coupling:** recommend an assertion at the intended seam without
  silently discarding distinct regression protection.

Preserve justified exact hashes, wording, canonicalization, byte stability, and
replay checks. Missing contract or expectation provenance is an evidence limit,
not permission to re-pin or proof that an assertion is disposable. Apply these
rules before snapshot smells or structure-coupled history; retain existing
supersession and `verify-then-retire` gates for lost coverage.

For authorized remediation, use focused diagnosis and convergence, then affected
component checks using the consumer's documented dependency map when available,
then required acceptance gates at project cadence. Avoid repeated broad acceptance
attempts while focused failures remain unresolved; never waive required gates.
This is advice about execution scope, not authority for an audit to edit tests
or run a suite in Quick mode. Ordinary change rationale suffices: no new pin
registry, mandatory paperwork, or mutation run on every change.

## Local confirmation and task authority

Apply existing task authority to cheap, known-safe local confirmations,
including a bounded rerun needed to resolve a finding. Check the command,
target, known runtime, isolation, and side effects; installed tooling or a
short estimate alone does not establish safety. Explicit **no reruns**, **use
existing results only**, read-only-without-execution, and authorized-count or
scope limits are binding. Do not ask again for an already authorized action.
Ask before unknown, materially costly, browser, external-service, mutation,
or otherwise state-changing work that existing authority does not cover.
When execution is excluded or unsafe, continue from available evidence and
state the limit. Confirmation does not authorize edits, expand audit coverage,
or turn a bounded inspection into a suite-level verdict.

## Shared sources

These source entries appear in more than one lane rubric. The integration and
E2E rubrics cite this section and keep only their lane-specific annotation
lines.

### Google Testing
- Winters, Manshreck, Wright — *Software Engineering at Google*, ch. 11
  ("Testing Overview") — the small / medium / large test sizing taxonomy.
- [Just Say No to More End-to-End Tests](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html)
- [Hermetic Servers](https://testing.googleblog.com/2012/10/hermetic-servers.html)
