# Scope Policy Source Grounding

This skill centralizes change-footprint discipline into a passive policy that
repositories initialize with a declared scope level and escalation mode. Plugin
installation alone does not enforce it; the standing repo guidance line — which
must embed the invariant and a level — is the enforcement authority; a bare
line falls back to the default profile (`balanced` / `auto`). Explicit stop
settings remain constraints. `adopt-guidance` consolidates existing
scope prose into that standing block. A necessary bounded extension is justified
by the authorized outcome and concrete risk, never preference for elegance or
unrelated cleanup alone. Keep guidance original; the level/escalation naming pattern below
is conceptually grounded, not copied.

## Boundary Decisions

- Change-footprint discipline (how wide a change may reach): `scope-policy`.
- Solution minimalism and design shape (how simple a solution should be, given
  a footprint): `software-design`. This skill says nothing about that axis.
- Approach-before-build planning: `planning-policy`.
- Test-first ordering: `tdd-policy`.
- Duplication/waste assessment: `lean-audit`.
- Recording out-of-level findings instead of doing them: `issue-ops`.
- Commit/branch preflight: `git-workflow-policy`.
- Disposition of existing/legacy code encountered during a change: the design
  skills' `project-assimilation` procedure, not `scope-policy`.

## Provenance

The concept of named, switchable intensity levels controlling how much an
agent may change was referenced from the MIT-licensed ponytail project at
https://github.com/DietrichGebert/ponytail. That project's axis is solution
minimalism (how elaborate a solution may be); this skill's axis is change
footprint (how far a change may reach beyond its target). No text, level names,
rung structure, command surface, or prose from that project was reused, and no
prose, code, schema, or assets from it are bundled here — only the general
concept of a named, switchable intensity axis informed this skill's design.

An approved strict or existing immutable managed plan adds a boundary to this per-task scope
policy. A wider correctness requirement makes the leaf terminal `oversized`;
the parent retains its run evidence and seeks approval for a replacement plan.
The `auto` setting cannot rewrite the approved digest or authorize another
dispatch. Standard plans instead permit parent-reviewed `auto` escalation when
the outcome, material decisions, constraints, and acceptance remain intact.
The 2026-10-24 maintainer decision deliberately removes the accidental coupling
between routine standard assignments and immutable managed leaves. Synthetic
cases exercise both paths; they do not establish measured speed improvements.
