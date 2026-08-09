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
- 2026-07-22 `java.md` lens B (Fable 5): two gaps fixed — shaded/relocated
  artifacts added to inspect plus a shading default (findings route
  `java.SD-B-1`/core), and published-artifact compatibility named binary,
  not source, with an API-compatibility diff added to validation.
  Adjudicated covered: Gradle `api`-vs-`implementation` leakage (dependency
  scopes + core `SD-B-3`), convention-plugin coupling (core `SD-C-3`),
  classloader-scoped state (core `SD-C-4`), executable architecture rules
  (core evidence layers). Merge back either addition if fresh-agent reviews
  catch the class via core alone.
- 2026-07-22 `csharp.md` lenses A+B (Fable 5): three gaps fixed —
  `Directory.Packages.props` load cue (central package management was
  uncued), API-compatibility diff in validation plus binary-not-source
  default (parity with java), and DI lifetimes as contracts with captive
  dependencies named (routes core `SD-C-4`). Adjudicated covered: TFM
  strategy (core §3.8/`SD-E-5`), source-generator packaging depth
  (`csharp.SD-Q-1`), artifact naming alignment (core `SD-B-1`), build
  provenance (devsecops-audit). Same merge-back condition.
- 2026-07-22 `rust.md` lenses A+B (Fable 5): two gaps fixed — a
  semantic-carrier default (enums/newtypes/typestate; both lenses flagged
  the always-`Some` two-phase smell, and siblings all carry the parity
  line), and semver discipline (API/semver diff in validation; auto-trait
  status named part of the contract — a silent major break neither family
  glob reached). Adjudicated covered: `[workspace.dependencies]`
  (`Cargo.toml` cue + core `SD-C-5`), `#[non_exhaustive]`/sealed traits
  (`rust.SD-E-*` scope → core `SD-E`), MSRV/publish hygiene (core §3.8 +
  release-policy), compile-time blast radius (core §3.6). Same merge-back.
- 2026-07-22 `typescript.md` lenses A+B (Fable 5): three defaults plus
  validation parity fixed — discriminated-union/literal-union semantic
  carriers; project-reference graph and package dependency graph tell one
  story (the java `SD-B-1` analog, previously family-only); module-level
  state duplicates per module instance under dual-format or skewed loads
  (the dual-package hazard class, also covering peer-dep misclassification
  consequences); public-types compatibility diff in validation. Adjudicated
  covered: phantom dependencies (core hidden coupling), type masquerading
  (`typescript.SD-B-2` exactly), barrels (family scope), `sideEffects` flag
  (`SD-B-2`-adjacent). Same merge-back.
- 2026-07-22 `python.md` lenses A+B (Fable 5): three inspect/default gaps
  fixed — async event-loop/executor ownership in inspect (sole extension
  without a concurrency-ownership item; `contextvars`-vs-thread-local under
  async routes core §3.9), `py.typed` in the distribution surface plus a
  typed-public-surface contract default (parity with csharp's
  nullable-contract line), and generated code in inspect (sole extension
  not naming it). Surfaced, not added: a generated-boundary key code
  (`SD-Q-1` parity with java/rust/csharp) — needs an owner decision.
  Adjudicated covered: root-facade import cost (`python.SD-B-*` → core),
  `lru_cache` hidden singletons (`python.SD-C-1`), metaclass ladder (core).
  Same merge-back.
- 2026-08-09 `python.md` lenses A+B (GPT-5.6 Terra): one gap fixed — public
  annotation/overload compatibility-diff and release impact were added to the
  typed-public-surface contract, using the project's configured compatibility
  check first and a bounded manual/generated diff only as fallback. Other
  Python/API pressure areas were covered or delegated: project-first
  assimilation, async/resource ownership, context-local state, API contract
  routing, and security/test/release policy boundaries. No Python smell code
  was added.
- 2026-07-22 `shell-script.md` lenses A+B (Fable 5): one gap fixed — env
  added to the inspected contracts (the inbound env-var config surface;
  parity with python's env reads). Otherwise the tightest mapping of the
  sweep: both lenses' material lands on the five key codes repeatedly
  (`shell.SD-B-1`, `SD-C-1`, `SD-S-3`, `SD-S-4`, `SD-Q-1`). Adjudicated
  covered: flat-namespace prefix discipline (core `SD-S-1`), errexit-stance
  inheritance across sourcing (`shell.SD-C-1` restore contract).
