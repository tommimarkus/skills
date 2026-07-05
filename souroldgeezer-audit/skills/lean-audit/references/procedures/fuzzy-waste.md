# Fuzzy Waste Procedure (LA-STALE-2 / LA-BLOAT-2 / LA-VERBOSE-2)

Load when running lean-audit. These codes are NOT deterministic — the engine
cannot decide them — so they are auditor inference and MUST be marked as
requiring verification (audit-craft §2, fact-vs-inference). Apply high-precision
discipline: when uncertain, downgrade or omit. A noisy waste finding erodes trust.

## LA-STALE-2 — prose describes a removed/renamed structure

Trigger: a doc names a section, file, directory, or layout that another doc is
expected to contain, but it no longer exists or was renamed.

Method:
1. Find references of the form: a quoted or back-ticked section name, a "see the X
   section" phrase, a path, or a `→ "Heading"` pointer targeting a specific named
   structure in a (possibly other) guarded file.
2. Resolve the named structure: does that heading / file / section exist now? Use
   the engine's `LA-STALE-1` output for link targets; for prose section-name
   references, check the target file's current headings.
3. Emit `LA-STALE-2` only when you can name BOTH the citing prose and the missing
   target, and cite both locations. If you cannot confirm the target is genuinely
   absent (vs. merely paraphrased), do not emit — record it "unverified" instead.

Example (real class): a maintenance rule citing README sections ("What's in
<plugin>", "How <skill> works") that the current README does not contain.

## LA-BLOAT-2 — heavy reference material in always-loaded context

Trigger: a `SKILL.md` (always-loaded) inlines material that belongs behind a load
condition — a long rubric, a large table or taxonomy, a multi-case catalog, or
stack-specific rules needed only sometimes.

Method:
1. Read the SKILL.md body. Flag a contiguous block that is (a) a rubric / table /
   taxonomy / example-set, AND (b) not needed on every invocation, AND (c) more
   than a few lines.
2. Distinguish from `LA-BLOAT-1` (the deterministic total-size check):
   `LA-BLOAT-2` is about WHAT is inlined, not just total length.
3. Emit `LA-BLOAT-2` naming the block and the reference file it should move to;
   recommend the load-condition pointer.

## LA-VERBOSE-2 — confirmed wasteful verbosity

Trigger: an engine `LA-VERBOSE-1` nomination (or a passage the user explicitly
names, disclosed as `nomination: user-directed`). Never free-scan for wordiness —
confirm only what the deterministic nominator raised (or the user pointed at).
That input boundary is the deterministic-first line and is what keeps this code
high-precision.

Method:
1. Read the nominated section and its cited metrics (tokens, filler density,
   scaffold count, repeat ratio). Draft the faithful tightening in your head, not
   in the tree — this code is detection, not repair.
2. Confirm the reduction is material: the faithful rewrite is meaningfully shorter
   (propose ≈ 30% fewer tokens as the floor). A trivial trim is not waste worth
   flagging.
3. Confirm the wordiness is NOT load-bearing. Do NOT emit when the length carries
   meaning: every obligation, qualifier ("only when…", "unless…"), threshold,
   number, negation, and enumerated item must survive the rewrite. Pedagogical
   emphasis, calibrated hedging, normative precision, and deliberately explicit
   phrasing for weaker model tiers are calibration, not *muda*.
4. Emit `LA-VERBOSE-2` citing the section, its `LA-VERBOSE-1` metrics, the
   projected token delta, and the load-bearing assessment. If you cannot confirm a
   faithful reduction exists, record it a cleared non-finding with the reason —
   do not emit.

Detection only in v1: this confirms the finding; it does not produce the rewrite.
Turning a confirmed `LA-VERBOSE-2` into a proposed reduction is the minify
`tighten` class — a separate, opt-in, not-yet-wired step.

All three inference codes (`LA-STALE-2`, `LA-BLOAT-2`, `LA-VERBOSE-2`) are `warn`
— never `block`. Disclose them as inference in the output.
