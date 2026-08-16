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
