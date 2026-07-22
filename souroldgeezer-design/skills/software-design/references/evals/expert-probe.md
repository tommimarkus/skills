# Expert Probe

Clean-context coverage oracle for `software-design` extensions. Run when
authoring a new extension or materially restructuring an existing one; never
re-run against unchanged content — a passed probe of an unchanged surface
under the same lens is a re-roll, not evidence.

Position: complements `accuracy-corpus/` (labeled-case Review recall and
false-positive rate) and `model-pressure.md` (whether an extension should
exist at all). The probe tests whether an extension plus its routing is
complete in obvious places; the accuracy corpus cannot see coverage unknowns
because its cases are written inside the skill's own framing. A behavioral
eval run by a model, never a deterministic gate; not wired into CI; not
linked from `SKILL.md`, so it adds no per-use load cost.

Protocol:

1. Spawn a fresh agent with clean context. It must not read the extension,
   the core reference, the catalogs, or this file; it formulates from its
   own expertise only and writes the formulation out before opening any
   repo file.
2. Run two lenses as separate formulations. Lens A (boundary): expert
   practitioner guidance for the stack, curriculum-style — stress-tests the
   delegation boundary. Lens B (center of gravity): what an expert reviewer
   checks in a mature codebase's structural, build, and module design for
   the stack — stress-tests the extension's own claims.
3. An agent holding both artifacts diffs formulation against extension and
   classifies every divergence: covered-by-core (cite the section or `SD-*`
   code and open it to verify), sibling-owned (name the skill and check its
   contract), linter-territory, or genuine gap. Routing is verified, never
   asserted.
4. Genuine gaps become extension edits under the key-code discipline in
   `../procedures/extension-authoring.md`; a gap implying a new key code or
   a contentious addition is logged and surfaced, not silently added. The
   default disposition for language-semantic divergences is routing to
   core, not addition.
5. Record a run entry below: date, extension, lens, probing model,
   divergence classes seen, gaps and their disposition.

Probe strength is model-dependent — record the model, as the accuracy
corpus does. Formulations are original synthetic expert prose; no
third-party text.

Run log:

- 2026-07-22 `java.md` lens A (Fable 5): no gaps. Curriculum-side
  divergences all routed — language semantics to core `SD-*` (§3.9
  concurrency/error contracts and the `SD-S` family verified), correctness
  pitfalls to linter territory, tests/security/HTTP to siblings.
  Extension-side surplus (non-hierarchical package access, `java.SD-B-1`
  module identity, `java.SD-Q-1` generated boundaries) confirmed the
  build-graph-first priority.
