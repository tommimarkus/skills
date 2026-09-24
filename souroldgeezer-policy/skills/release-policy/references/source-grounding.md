# Release Policy Source Grounding

This skill centralizes duplicated release, versioning, tagging, and publication
guidance into a passive policy that repositories initialize with version and
distribution options plus local exceptions. Plugin installation alone does not
enforce it; loaded repo guidance initialization is the standing enforcement
trigger for matching release actions. Adopt mode consolidates existing related
guidance into initialization options or local exceptions instead of leaving
parallel release authority. Keep guidance original; link external manuals only
when needed.

## Boundary Decisions

- Developer git movement and version-policy placement: `git-workflow-policy`.
- PR/MR lifecycle writes: `pr-ops`.
- Issue lifecycle work: `issue-ops`.
- Release readiness, version updates, tags, provider releases, publication, and
  post-release verification: `release-policy`.
- Security controls: `devsecops-audit`.
- Test-suite adequacy: `test-quality-audit`.

## Verification Evidence Decision

Treat a clean candidate commit plus its ordered verification plan as the unit
that owns full-gate evidence. Exact fast-forward integration preserves that
unit. A documented atomic fixed-surface version-only follow-up is a narrower
verification event: focused version or metadata checks cover the only allowed
change. Any source, plan, evidence, surface, or integration drift breaks that
equivalence and restores the full gate; conflicting repository or host policy
always stops reuse.

## Authority Continuity Decision

An initialized rule or explicit request that names an action and target is
authority for that matching action after its verification gates pass. An
unconditional later ask would erase that grant and make routine execution
contradict the initialization. Ask when the target or action falls outside the
grant; a broad release intent does not name an external publication target.
The synthetic behavior case pairs an already-authorized tag and provider
release with an unnamed target to preserve both sides of this boundary.
