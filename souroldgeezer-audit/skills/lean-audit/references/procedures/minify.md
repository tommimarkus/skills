# Minify Lens (LA-MIN-1 / LA-MIN-2 / LA-MIN-3) — OPT-IN, PROPOSE-ONLY

Load this ONLY when the request explicitly asks for a minification / reduction
proposal (e.g. "minify this skill", "shrink the always-loaded context and give
me a diff", "propose a token reduction"). This lens is never part of a default
waste run and is never auto-fired by surface detection. It is the action arm of
lean-audit: it consumes the waste and per-use lenses' findings and produces a
reviewable diff plus a fidelity report. It NEVER writes target files — applying
a proposed diff is a separate, explicit user action outside this skill
([`../../../../docs/audit-reference/audit-craft.md`](../../../../docs/audit-reference/audit-craft.md)
§2: separate audit from repair; this lens produces the repair proposal, not the
repair). Cite codes from [`../smell-catalog.md`](../smell-catalog.md); do not
restate catalog prose. Prose/skill surfaces only: source code is never
rewritten here (see Stage 1 exclusions).

## When this lens runs

Gate: an explicit minification / reduction-proposal request. No such request →
emit nothing, build no shadow workspace, produce no diff. A plain
duplication/waste request does NOT activate this lens. The lens makes zero
agent or network calls — every gate below uses only the bundled scripts.

## Stage 1 — Locate (reuse existing detection; no new engine)

Run the SKILL.md Workflow steps 1–5 first if not already run this session —
their ranked, materiality-tiered worklist is this stage's input. Map findings
to reduction classes:

- `LA-DUP-1` / `LA-DUP-2` → **dedupe-to-canonical**: replace the restated
  passage with a markdown-link citation to its canonical home (the registry's
  declared canonical when one exists).
- `LA-STALE-1` / `LA-STALE-2` → **repair-or-remove stale prose**: delete or
  correct prose describing structures that no longer exist.
- `LA-DEAD-1` → **delete-dead**: remove the unreferenced file and any mentions
  that would dangle.
- `LA-BLOAT-1` / `LA-BLOAT-2` → **hoist**: move the heavy always-loaded block
  to a `references/` file behind an explicit load condition.
- `LA-PUC-1/2/3` (when the target has entry artifacts) → the per-use
  procedure's recommended move (mode-gate / split / partition), inheriting its
  fidelity-safety class and the escalation-cue rule from
  [`per-use-cost.md`](per-use-cost.md).

Exclusions (never enter the worklist):

- Registry carve-outs (`[[carve_out]]` / `exempt_paths`) and
  `<!-- lean-audit:sync-intentional -->` / `lean-audit:dup-intentional` marked
  blocks — the engine already exempts them; do not re-nominate by hand.
- `LA-CODE-DUP-*` clones and any source-code rewrite: emit an `LA-MIN-3`
  referral to the owning skill (`software-design` for semantic restructure)
  instead. Minify rewrites prose/skill surfaces only.

Rank the remaining items by projected token delta × per-use weight (the
per-use dial from [`per-use-cost.md`](per-use-cost.md), when inferred) × the
P0–P3 worklist priority. Output: a reduction worklist of
`(target file, consumed finding codes, reduction class, projected delta)`.

## Stage 2 — Propose

For each worklist item, draft the concrete minified rewrite as a unified diff
against the target file. Before drafting, build the item's **obligation
ledger**: enumerate every atomic obligation in the touched region — each
instruction, stop condition, output-contract clause, load condition,
escalation cue, finding code, and section heading cited from elsewhere — and
assign each a disposition: `kept` (still present), `moved-to <path>#<section>`
(hoisted), or `cited-at <canonical path>#<section>` (deduped). **No obligation
may be dropped.** The ledger is Stage 3's G7 evidence and part of the emit.

Dial composition (from [`per-use-cost.md`](per-use-cost.md) "Infer the dial"):
on a structural-only-dial target (audit skills), propose structural-safe
reductions freely; a needs-adversarial-review reduction may be proposed ONLY
after the full Stage 3 gate passes, and is additionally marked
`maintainer-review required` in the emit. On a compression-tolerant-dial
target the same gates apply; only the ranking weight changes.

Every reduction that caps or moves loadable content MUST include its
escalation cue (the pointer telling the executor how to re-load the excluded
content) — per-use-cost.md classification rule 2. A missing cue is a Stage 3
rejection (`escalation-cue-missing`), not a style note.

## Stage 3 — Fidelity-verify (adversarial; fail-closed)

**Shadow workspace.** Never touch the target tree. Copy the audited root (the
same `<dir>` the engine scanned in Workflow step 2) to a scratch directory
(e.g. `$TMPDIR/lean-minify-<timestamp>/`), preserving repo-relative paths so
every relative link and script pointer resolves identically. Apply the
proposed diffs for one target (batched per target file) to the copy only.
When the audited root is too large to copy, mirror at minimum the full
resolved closure of every affected entry artifact plus every non-markdown
pointer target cited from edited files, and disclose the reduced mirror.

**Deterministic gates** (all must pass; commands are repo-root-relative, run
against the shadow copy):

- **G1 before-inventory:**
  `skill_load_cost.py baseline --files <before-closure files> --code-patterns <patterns.json> --out before.json`
  — closure from `skill_load_cost.py resolve_closure <entry>` for skill
  targets; for plain-doc targets, the edited files plus every file they link.
- **G2 inventory + pointer diff:**
  `skill_load_cost.py diff --baseline before.json --files <after-closure files> --code-patterns <patterns.json>`
  must exit 0 — no missing code, no missing section, no dangling pointer.
- **G3 stale/anchor scan:** run `lean_engine.py <shadow-root> --format json`
  and compare `LA-STALE-1` findings to the before run: no NEW broken link or
  `#anchor`. (G2's pointer check is existence-only; G3 covers anchors.)
- **G4 delta measurement:** write an ad-hoc scenarios file listing the
  before-closure files, run `skill_load_cost.py snapshot` once with
  `--root <audited root>` and once with `--root <shadow root>` (after-closure
  file list), and record the token delta; for skill targets also record the
  per-use closure delta (`resolve_closure` before vs after — files removed
  from the always-loaded set).

**Judgment gates** (adversarial; disclosed as inference, audit-craft §2):

- **G5 covered-elsewhere semantic resolution:** for every citation a reduction
  relies on, READ the canonical target and confirm it actually carries the
  removed content at equal or greater precision — existence (G2) is not
  sufficiency. A paraphrase that loses a qualifier, threshold, or exception is
  `semantic-loss`.
- **G6 target eval re-run:** when the target skill ships
  `references/evals/trigger-cases.jsonl` / `behavior-cases.jsonl`, re-judge
  every case against the AFTER state: each trigger prompt must keep its
  `expected_activation` under the proposed trigger metadata; each behavior
  case's `required_checks` and `expected_artifacts` must remain instructed by
  the after closure and no `forbidden_behaviors` newly enabled. Any flip is
  `eval-regression`. When the target has NO eval pack, reductions that touch
  trigger metadata (frontmatter description) or output-contract / stop-condition
  text are rejected `gate-unavailable`; other reductions may proceed on
  G5 + G7 with the gap disclosed.
- **G7 intent diff:** re-verify the Stage 2 obligation ledger against the
  after text, obligation by obligation; any `dropped` or unmappable obligation
  is `obligation-dropped`.
- **G8 escalation cue:** confirm every capping/moving reduction carries its
  re-load cue (`escalation-cue-missing` otherwise).

**Failure handling.** Gates run per target batch. On failure, bisect: revert
the smallest set of reductions whose removal makes all gates pass; reject that
set as `LA-MIN-2` with the failing gate's reason code and evidence. If a
required deterministic gate cannot run (harness or engine unavailable), reject
the affected reductions `gate-unavailable` — this lens is FAIL-CLOSED for
acceptance, the opposite of the detection lenses' fail-open: an unverified
detection degrades with disclosure, an unverified edit is never proposed.

## Stage 4 — Emit

Per accepted reduction (`LA-MIN-1`):

- **code** — `LA-MIN-1`
- **target** — file (and section) the diff applies to
- **consumed findings** — the `LA-*` codes from Stage 1 it remediates
- **reduction class** — dedupe-to-canonical | hoist | tighten | delete-dead |
  per-use move (gate/split/partition)
- **diff** — the unified diff, fenced, apply-ready but NOT applied
- **token delta** — from G4
- **per-use closure delta** — for skill targets, from G4
- **fidelity-safety** — structural-safe | needs-adversarial-review
  (+ `maintainer-review required` on structural-only-dial targets)
- **obligation ledger** — the Stage 2 ledger with final dispositions

Per rejected reduction (`LA-MIN-2`): code, target, reduction class, reason
code, and the failing evidence (the regression line, flipped eval id, or
dropped obligation). Per referral (`LA-MIN-3`): the clone pair or source
surface and the owning skill.

Close with the named `fidelity:` block: reductions proposed / accepted /
rejected (by reason code) · total token delta · per-use closure delta(s) ·
pointer verification result (G2 + G3) · evals re-run (case counts + result,
or "no eval pack — restricted classes") · shadow-workspace path. Proposed
diffs live in the report output (or a user-requested scratch file); never in
the target tree.

## Disclosure (feeds the SKILL.md footer)

Report the run's minify footer fields exactly as specified in
[`../../SKILL.md`](../../SKILL.md) §"Output footer (audit-craft §5)" (the
minify block) — do not improvise or drop fields. The propose-only attestation
("no target files written") is how the lens's read-only conformance stays
auditable.
