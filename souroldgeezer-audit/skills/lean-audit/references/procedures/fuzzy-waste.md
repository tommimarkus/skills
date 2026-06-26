# Fuzzy Waste Procedure (LA-STALE-2 / LA-BLOAT-2)

Load when running lean-audit. These two codes are NOT deterministic — the engine
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

Both codes are `warn` — never `block`. Disclose them as inference in the output.
