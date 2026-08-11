# Scope Policy Source Grounding

This skill centralizes change-footprint discipline into a passive policy that
repositories initialize with a declared scope level and escalation mode. Plugin
installation alone does not enforce it; the standing repo guidance line — which
must embed the invariant and a level — is the enforcement authority; a bare
line falls back to the default profile (`balanced` / `stop`), matching the
sibling policies rather than stopping. `adopt-guidance` consolidates existing
scope prose into that standing block. Escalation only fires when the task cannot
be completed correctly at the declared level, never for elegance, and always
with evidence. Keep guidance original; the level/escalation naming pattern below
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
