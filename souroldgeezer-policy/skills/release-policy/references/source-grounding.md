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
- Release readiness, bumps, tags, provider releases, publication, and
  post-release verification: `release-policy`.
- Repeatable SemVer, CalVer, and PEP 440-style arithmetic: bundled
  `version-bump`; keep writes narrow and explicit.
- Security controls: `devsecops-audit`.
- Test-suite adequacy: `test-quality-audit`.
