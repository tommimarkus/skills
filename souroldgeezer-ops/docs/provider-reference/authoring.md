# Provider Extension Authoring

Shared authoring template for provider extensions of `issue-ops` and `pr-ops`.
Both skills' `extensions/README.md` cite this file for their `## Required
Sections` template and layer their own skill-specific additions on top; a
skill's own core contracts are unaffected by this reference.

## Required Sections

Each provider extension is a single markdown file in its skill's `extensions/`
directory with:

- **Load condition**: which URLs, remotes, identifiers, tooling, or user
  wording identify this tracker (issue-ops) or provider (pr-ops).
- **State resolution**: the live tracker/provider and local git facts to
  inspect before acting.
- **Tooling order**: provider integrations in preferred order, with auth and
  repository-identity checks.
- **Lifecycle marker or status model**: how visible progress is written,
  edited, or skipped when permission is missing (pr-ops also skips when
  public noise would be excessive).
- **Escalation gates**: provider-specific stale-state, permission, concurrent
  actor, public-comment, and closure-safety stops (pr-ops adds check, review,
  and merge-safety stops).
- **Completion rules**: issue-ops: exact pre-close refresh checks and final
  reporting requirements. pr-ops: final refresh checks and final reporting
  requirements.

Add a new provider extension only when the provider has enough lifecycle
mechanics to keep out of the always-loaded core skill. Keep public platform
claims anchored to official provider documentation when they are not obvious
from live tooling behavior.
