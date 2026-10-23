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
