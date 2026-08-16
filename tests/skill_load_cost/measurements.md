# test-quality-audit per-use load cost

| Scenario | Before | After | Delta |
|---|---|---|---|
| quick-node-unit | 23251 | 20037 | -3214 |
| deep-nextjs-suite | 44360 | 44610 | +250 |

## Load-set reductions (not captured by fixed-file scenarios)

The fixed-file-list scenarios measure content-token changes only — they cannot
show load-SET changes because the file list is declared, not derived from the
Load Map at runtime.

Task 9's real win: Quick mode no longer loads
`materiality.md` (333 tok) + `sampling-projection.md` (200 tok) = **533 tokens**
saved per Quick audit, per the tightened Load Map. These files were never in the
`quick-node-unit` scenario list (it was already minimal), so the removal does
not appear in the scenario delta above. The SKILL.md grew by +126 tokens due to
the Load Map clarifications across all tasks, which accounts for the small upward
tick in both scenario totals.

## Summary

The headline Quick win is a **−3214-token content reduction** in the
`quick-node-unit` scenario (23251 → 20037): the Deep-only split of
`nodejs/core.md` removed 3340 tokens from the Quick load path (base 14384 →
tip 11044), partly offset by a +126-token SKILL.md growth (base 1229 → tip
1355) from the Load Map clarifications. On top of that, the Load Map tightening
(Task 9) removes `materiality.md` (333 tok) and `sampling-projection.md`
(200 tok) from Quick mode entirely, a further **533 tokens per Quick audit**
that the fixed-file scenario cannot show because those files were never in the
declared list. Together the per-use Quick saving is **−3747 tokens** (3214
content + 533 load-set). The Deep scenario stayed nearly flat (+250 tokens,
within noise) by design — Deep mode still loads everything including the new
`deep.md` files, so no content was net-removed from that path. Task 8 was a
cross-file restatement pass that found no true duplicate content to factor out
of `nextjs/core.md` — the nodejs and nextjs cores are disjoint by design,
already factored to their respective homes — so it made no change. Fidelity
diff: 0 regressions across all tasks — the `uv run python souroldgeezer-audit/skills/lean-audit/references/scripts/skill_load_cost.py diff`
gate exited 0 at every task where it was run, and the full
`TestQualityAuditBaselineTest` suite passes at branch tip.

## Extension applicability & load gating — 2026-08

Root cause fixed: the `Applies to:` vocabulary in `references/extensions/authoring.md`
documented only `unit` / `integration` / `unit, integration` and called the last
"rubric-neutral". That predates the E2E lane, so every stack parked its two-rubric
smell body in the always-loaded `core.md` — which E2E audits load in full, of which
none applied. Separately, `deep.md` existed only for `nodejs` / `nextjs` / `python`,
so `dotnet` / `java` / `rust` / `robotframework` charged every **Quick** audit for
SUT enumeration, determinism, and mutation declarations.

Two scenarios (`quick-node-e2e`, `deep-dotnet-e2e`) were added **first** — the E2E
path had no declared scenario, so this waste was invisible to the gate.

| Scenario | Before | After | Delta |
|---|---|---|---|
| `quick-node-unit` | 22667 | 23254 | +587 |
| `quick-node-e2e` | 28044 | 24723 | **−3321** |
| `deep-nextjs-suite` | 48809 | 49166 | +357 |
| `quick-python-unit` | 11391 | 11578 | +187 |
| `deep-python-suite` | 16908 | 17095 | +187 |
| `deep-dotnet-e2e` | 27991 | 22691 | **−5300** |

The wins are confined to the E2E paths (−8621 combined); the four other paths pay
+1318 combined. That cost is deliberate and mostly **earned content**, not overhead:
the keepers that now declare `e2e` gained E2E-correct guidance they previously
lacked (Playwright `page.clock` for the real-clock smells, `forbidOnly` for committed
focus markers, `test.fixme` for skips), and `SKILL.md` gained the escalation cue that
[docs/skill-architecture.md](../../docs/skill-architecture.md) § On-demand knowledge
requires whenever a load map caps a mode. The `quick-python-unit` / `deep-python-suite`
+187 is exactly that always-on `SKILL.md` growth — Python's own files did not change
structurally.

Adjudication, not a mechanical move: all 42 two-rubric smells in `nodejs` and `dotnet`
were re-judged against the E2E rubric. 10 of 23 Node and 5 of 19 .NET genuinely apply
to browser-driven specs and **stayed** in `core.md` re-marked `unit, integration, e2e`;
the rest moved to `<stack>/unit-integration.md`. Small cores (`java`, `python`, `rust`)
keep their two-rubric smells inline under a `## Shared Smells (unit + integration)`
heading — below roughly 2000 tokens of smell body the split stops paying, a threshold
now documented in `authoring.md`.

Fidelity: classified before/after inventory diff over the resolved closure showed
**62 codes, 0 lost, 0 gained**. The only baseline section lost was the renamed
`Rubric-Neutral Smells`; six gained entries are the new files' titles. Full suite
990 tests OK; `skill-architecture-report.sh` clean; `load_cost_guard.py` exit 0.

# api-design per-use load cost

api-design's per-use weight is dominated by its stack extensions (27,745 tokens
across five files); SKILL.md (1405) and the core reference (~9787) load
identically across modes. The reductions here are therefore load-SET reductions
on the extension layer — captured by comparing declared load lists, not by
content shrink. (This change grew SKILL.md by ~114 tokens — the Load Map
mode-gating paragraph plus the escalation cue — an always-on cost in every mode,
netted into the win-#1 figure below.)

## Win #1 — Lookup mode-gating (implemented)

The Load Map previously listed each stack extension under "Load what applies"
with a detection-signal trigger and no mode qualifier, so a Lookup on a
multi-stack repo could load every detected stack's full extension. The tightened
Load Map gates the five stack extensions to Build/Extract/Review and restricts
Lookup to the core-reference matched section plus, at most, the single extension
the question is specifically about.

Extension tokens loaded per Lookup on a Functions + Cosmos + Blob repo:

| Lookup kind | Before (load-on-detection) | After (win #1) | Delta |
|---|---|---|---|
| general principle / status / header | 18747 (afdotnet 7034 + cosmos 5591 + blob 6122) | 0 | **−18747** |
| stack-specific (one stack) | 18747 | 7034 (the matched extension) | **−11713** |

The extension-load delta is the headline. The ~75-token SKILL.md growth this
change adds loads in every mode, so the net per-use reduction on a general
Lookup is **~−18633** (18747 extension tokens removed, less the 114 always-on
tokens added); on a stack-specific Lookup it is **~−11599**. The
`lookup-functions` scenario lists the whole core reference as a conservative
upper bound; a real Lookup loads only the matched section plus immediate
context.

## Win #2 — Build/Review extension partition (measured, not implemented)

Each stack extension is organized by purpose: a shared core (name + detection
signals, hosting-model surface, applies-to sections), a Build/Extract slice
(primitives, patterns, mapping table), and a Review slice (smell codes,
carve-outs, project-assimilation discovery). All three load together today.
Splitting each `<stack>.md` into `<stack>/core.md` + `<stack>/build.md` +
`<stack>/review.md` — the proven test-quality-audit deep-split pattern — lets a
single-mode run load only the slice it needs.

Per-extension slice weights (tokens, classified by top-level section):

| Extension | shared | build | review | total |
|---|---|---|---|---|
| azure-functions-dotnet | 830 | 3884 | 2320 | 7034 |
| nodejs | 1094 | 1846 | 1842 | 4782 |
| nextjs | 1177 | 1204 | 1835 | 4216 |
| azure-cosmosdb | 751 | 2766 | 2074 | 5591 |
| azure-blob-storage | 668 | 3174 | 2280 | 6122 |
| **all five** | 4520 | 12874 | 10351 | 27745 |

Projected per-use savings (drop the slice the mode never reads):
- A Build/Extract run drops the review slice — up to **−10351** with all five
  extensions in scope; **−4394** for the committed `build-functions-cosmos`
  scenario (afdotnet 2320 + cosmos 2074).
- A Review run drops the build slice — up to **−12874** with all five in scope;
  **−9824** for `review-functions-cosmos-blob` (afdotnet 3884 + cosmos 2766 +
  blob 3174).

Risk (why it is measured, not landed here): the partition moves prose under
shared headers, which the fidelity diff gate cannot see — it tracks codes +
section headers + pointers, not prose relocated under an existing header.
Extension cross-references (patterns ↔ smell codes; carve-outs that contrast a
smell code) must stay reachable in their loading mode, so an adversarial
per-reference review is required before committing the split, exactly as flagged
for the test-quality factoring. Recommended as a scoped follow-up.

## Summary

Win #1 (Lookup mode-gating) is committed: it removes up to **18747 extension
tokens** from a general Lookup and **11713** from a stack-specific Lookup on a
three-stack repo (net **~−18633** / **~−11599** after the ~114-token SKILL.md
growth this change adds), with zero fidelity loss — the matched extension stays
reachable for genuinely stack-specific questions. The api-design fidelity
baseline (218 codes, 210 sections) and the `ApiDesignBaselineTest` regression
gate are established as groundwork. Win #2 (the Build/Review extension
partition) is measured at **−10351 review-slice / −12874 build-slice** with all
five extensions in scope (−4394 / −9824 on the committed two- and three-stack
scenarios) and recommended as a scoped follow-up pending the adversarial
cross-reference review the diff gate cannot automate.

# software-design per-use load cost

Guard coverage added 2026-07: scenarios (`sd-lookup-principle`, `sd-build-csharp`,
`sd-review-typescript`), committed baseline, `SD-*` code patterns.

| Scenario | Before | After | Delta |
|---|---|---|---|
| sd-lookup-principle | 4484 | 1542 | -2942 |
| sd-build-csharp | 5359 | 5447 | +88 |
| sd-review-typescript | 8041 | 8129 | +88 |

The lookup drop is a load-SET change: Lookup no longer loads the core
reference (3094 tokens); catalogs carry `Cite` section anchors so citations
survive, with an escalation cue for catalog-insufficient lookups. Build/
Extract/Review kept their load set; their small growth is the Load Map
wording. The former `§§2-7,9` scoping was cosmetic (whole-file reads) and
silently excluded §8's evidence-layer definitions; the load instruction is
now whole-file. Fidelity: `skill_load_cost.py diff` exit 0 at every task;
`SoftwareDesignBaselineTest` green.

The After values include a follow-up cite-wording refinement (+11 tok to
SKILL.md across all three modes): the Load Map now says Lookup cites "the
core-reference section it names for Lookup (a `Cite` column or a cite
sentence)" so the instruction reads correctly for the pattern/NFR catalogs
(which name the section in a sentence, not a `Cite` column).

# architecture-design per-use load cost

Guard coverage added for issue #66: scenarios (`arch-lookup-notation`,
`arch-build-archimate`, `arch-extract-dotnet`, `arch-review-package`),
committed baseline, `ARCH-*` code patterns.

| Scenario | Tokens |
|---|---|
| arch-lookup-notation | 1922 |
| arch-build-archimate | 14144 |
| arch-extract-dotnet | 15286 |
| arch-review-package | 15521 |

The headline per-use win is a load-SET reduction the fixed-file scenarios only
partly capture. Before #66, SKILL.md step 1 force-loaded the whole 771-line
`architecture.md` plus the operational workflow for **every** mode, and step 2's
self-check pulled the dediren bundle agent guide (~564 lines, resolved from the
release bundle) for every non-Lookup mode. After #66:

- **Lookup** no longer loads `architecture.md`, the operational workflow, or
  self-check at all when the answer makes no runtime claim — it reads only the
  cited section (or the one notation file). `arch-lookup-notation` (1922 tokens)
  models this cheap path; the pre-fix Lookup paid close to the full Build
  closure.
- **Build / Extract / Review** read only the `architecture.md` sections the mode
  needs (per the step-1 map), not the whole file. The token proxy reads whole
  files, so the scenario totals above list `architecture.md` at full size — an
  upper bound; the real per-use read is the section subset.
- The **runtime agent guide** (`dediren_guide`) is deferred to the moment
  source-JSON authoring, a command handoff, or a repair loop is imminent. It is
  returned by the selected host runtime, not loaded from a repo file, so no
  scenario measures it; a notation Lookup or a mechanical edit that reaches no
  runtime command never loads that external guidance.

Fidelity floor: the `architecture-design` baseline (32 codes — 28 `ARCH-*` plus
`E-1..E-4` — and 104 sections) and `ArchitectureDesignBaselineTest` guard that
the section-scoping and agent-guide deferral leave every finding code and
reference section reachable across the skill closure. The step-1 escalation cue
("this map is a floor, not a cap") keeps a mode free to pull any other section
the moment the task reaches it — the guard the earlier bare `§§2-7,9`
software-design scoping (above) lacked before it was reverted to whole-file.

# lean-audit minify lens — per-use load cost

| Scenario | Before | After | Delta |
|---|---|---|---|
| lean-audit-default | 6841 | 7845 | +1004 |
| lean-audit-minify (new) | — | 12781 | n/a |

The default-path growth is the SKILL.md wiring (the minify Contract paragraph,
opt-in section, Load Map bullet, Rules, and footer block) plus the `LA-MIN-*`
catalog band; `procedures/minify.md` itself is opt-in and loads only in the
`lean-audit-minify` scenario, so it never enters the default always-loaded
path. Fidelity baseline regenerated from `resolve_closure` (now inventories
`LA-MIN-1/2/3` and the minify sections: 14 -> 18 codes, 66 -> 73 sections).

Note: `resolve_closure` follows every markdown link regardless of load
condition, so the opt-in `procedures/minify.md` (and `platform-redundancy.md`)
appear in the SKILL.md closure and fidelity baseline even though they load only
on explicit request. The `lean-audit-minify` scenario total (12536) is
therefore a conservative upper bound on the real opt-in per-use read.

# lean-audit run viability and progressive disclosure — 2026-08

The former `lean-audit-default` scenario is now the explicit
`lean-audit-prose` path. Conditional code bands moved from the core smell
catalog into their owning procedures, and duplicated execution/maintenance
prose was removed from always-loaded `SKILL.md`.

| Scenario | Before | After | Delta |
|---|---:|---:|---:|
| ordinary prose (`default` → `prose`) | 9632 | 7680 | **-1952 (-20.3%)** |
| source-code duplication | new | 7680 | n/a |
| skill-surface/per-use | new | 10140 | n/a |
| staged-run viability | new | 13327 | n/a |
| trace-calibrated run viability | new | 13327 | n/a |
| platform redundancy | new | 11795 | n/a |
| minify | 15771 | 13867 | **-1904 (-12.1%)** |

The ordinary path is the representative high-frequency win. The less common
run-viability path deliberately spends another 5647 proxy tokens on the
per-use and run procedures so it can model phases, coordinator/worker budgets,
tool and hook exposure, log visibility, low/expected/high lanes, verification
reserve, and metadata-only trace calibration. Those references are absent from
ordinary prose/source audits. Fixed-file scenarios are conservative: executable
scripts are invoked as tools and are not counted as prompt context.

## Scaled-audit contract — 2026-08

Adds the shared `docs/audit-reference/scaled-audit.md` (delegation protocol +
evidence-durability floor + divisible/parent-only lane table) and routes all four
audit skills to it. This section records the **cost** of that routing, because the
change deliberately adds always-loaded tokens for the first time since the
extension gating work above.

The reference itself is **1110 tokens and strictly conditional** — it appears on no
normal Quick/Deep path. Only the routing is always-loaded:

| Always-loaded addition | Cost | Paid by |
|---|---:|---|
| `audit-craft.md` §6a pointer | **+54** | every audit (audit-craft loads in all modes) |
| `test-quality-audit/SKILL.md` gating sentence | +85 | test-quality-audit |
| `lean-audit/SKILL.md` gating sentence | +92 | lean-audit |
| `devsecops-audit/SKILL.md` gating sentence | unmeasured | — no declared scenario exists |
| `ip-hygiene/SKILL.md` gating sentence | unmeasured | — no declared scenario exists |

Measured per scenario:

| Scenario | Before | After | Delta |
|---|---:|---:|---:|
| `quick-python-unit` | 11578 | 11717 | +139 |
| `deep-python-suite` | 17095 | 17234 | +139 |
| `deep-dotnet-e2e` | 22691 | 22830 | +139 |
| `quick-node-unit` | 23254 | 23393 | +139 |
| `quick-node-e2e` | 24723 | 24862 | +139 |
| `deep-nextjs-suite` | 49166 | 49305 | +139 |
| `lean-audit-declared-composed-profile` | 5802 | 5894 | +92 |
| `lean-audit-prose` / `-source-code` | 8224 | 8370 | +146 |
| `lean-audit-skill-surface` | 11381 | 11527 | +146 |
| `lean-audit-platform-redundancy` | 13036 | 13182 | +146 |
| `lean-audit-run-viability` / `-trace-calibration` | 15595 | 15741 | +146 |
| `lean-audit-minify` | 15108 | 15254 | +146 |
| `deep-dotnet-e2e-scaled` (new) | n/a | 23940 | +1110 over `deep-dotnet-e2e` |

The +139 / +146 / +92 figures decompose exactly into the table above and nothing
else: `lean-audit-declared-composed-profile` loads `lean-audit/SKILL.md` without
`audit-craft.md`, isolating the +92, which leaves §6a at +54 and the
test-quality-audit sentence at +85. No path moved by anything near 1110, so the
reference did not leak onto an unconditional load line.

`deep-dotnet-e2e-scaled` was added *before* the content change so the conditional
path is visible to the gate at all — repeating the lesson from the extension
gating work above, that a gate only sees the paths someone declared.

**Two coverage gaps this measurement cannot close.** `devsecops-audit` and
`ip-hygiene` have no declared load-cost scenario of any kind, so their gating
sentences are unmeasured and the guard cannot see either skill. That predates this
change and is recorded here rather than fixed, since adding two skills' scenario
coverage is its own piece of work.

## Audit-plugin fidelity floors — 2026-08

Closes the coverage gap recorded at the end of the scaled-audit section above.
The framing there was wrong and is corrected here: `load_cost_guard.py` is a
**fidelity floor**, not a cost tracker. It soft-blocks an edit that makes a code,
section, or Load-Map pointer unreachable, and it *always allows* on a missing
baseline. So the consequence of the gap was not an unknown token count — it was
that **nothing prevented a silent deletion of a finding code** from
`devsecops-audit` or `ip-hygiene`. Cost growth is advisory in that engine and
never blocks.

Baselines added (generated from `resolve_closure`, no new machinery):

| Skill | Closure files | Codes | Sections |
|---|---:|---:|---:|
| `devsecops-audit` | 27 | 84 | 274 |
| `ip-hygiene` | 20 | 23 | 103 |

`ip-hygiene` required two new `code_patterns.json` entries first. Before them it
produced **0 codes / 103 sections** — a baseline that reads as coverage while
protecting no finding code at all. It needs a *pair*, matching the existing
`SD-*` precedent: core `IP-(SRC|COPY|DB|LIC|MARK)-n` (21 codes) plus namespaced
extension codes (`js.IP-SRC-2`, `python.IP-LIC-1`).

**Positive control, not a green run.** A guard that fails open and a guard that
passes are indistinguishable from a clean suite, so both were probed directly by
feeding the guard a PreToolUse edit deleting a code that occurs exactly once in
the closure (a code appearing twice stays reachable, and allowing is then
correct). Both returned `deny`:

- `IP-COPY-4` in `references/copyright.md` → `deny` — "missing code (unreachable across skill)"
- `DSO-HC-13` in `devsecops-smell-catalog.md` → `deny` — same

Scenarios added, and the new-path costs:

| Scenario | Tokens |
|---|---:|
| `ip-triage-js` | 11746 |
| `ip-indepth-python` | 15318 |
| `quick-devsecops-gha` | 23926 |
| `deep-devsecops-gha` | 29124 |

All 15 pre-existing scenarios re-measured **byte-identical**; the additions
perturb nothing. Adding the two `IP-*` patterns also leaves every existing
baseline's `codes` array **identical** — verified by regenerating all five against
the new pattern set — so the patterns do not over-match.

**Pre-existing section drift, found but not fixed here.** Regenerating the five
existing baselines shows section-set drift against what is committed, present
with the *old* pattern file too, so unrelated to this change. Most is additive
(closures gained sections the committed floor predates). One is not:
`architecture-design`'s committed baseline contains
`"Visible Title Band Post-Render Step"`, which its current closure no longer
produces — a floor item that has genuinely gone unreachable. The guard's Stop path
only checks session-changed files, so nothing surfaced it. Recorded for a separate
change rather than repaired here.

**The standing cost.** A baseline is a freshness obligation: future edits inside
those 47 closure files must keep it current. That recurring cost is the price of
the protection.
