# lean-audit bundled Python® tooling — maintainer guide

Developer documentation for the Python that powers the `lean-audit` skill. Read
this **before changing anything under this directory** so you don't have to
reverse-engineer the shim→package contract, the module graph, the finding codes,
or the test gates first. This file is a maintainer reference; it is **not** loaded
during a skill run and is deliberately kept out of the SKILL.md Load Map.

For what the tool *reports* (operator view), stay in
[`../../SKILL.md`](../../SKILL.md) and the finding codes in
[`../smell-catalog.md`](../smell-catalog.md). This guide is the *internals* view.

- Runtime: **standard library only, Python ≥ 3.11.** No third-party imports, so no
  dependency resolution is needed — but `tomllib` is stdlib only from 3.11, so the
  ≥3.11 floor is real. Invoke every shim with `uv` as the primary runner (it
  provisions/selects a conforming interpreter even when the system `python3` is
  older); the shims declare `requires-python = ">=3.11"` and guard `sys.version_info`
  at startup, exiting 3 with a legible message before the package import when run
  under an older `python3`.
- Quality bar: **ruff + `mypy --strict`**, scoped to this tree (see
  [§ The enforced standard](#the-enforced-standard)).
- Contract: the six top-level scripts are **stable published paths**; the logic
  lives in the sibling [`leanaudit/`](leanaudit/) package.

## The shim → package contract

Each top-level `.py` here is a thin **entry shim** over one `leanaudit/` module.
The shim path is the downstream contract (SKILL.md, `hook-recipe.md`, and the
repo Stop hook all invoke these paths); the implementation is free to move within
the package as long as the shim keeps re-exporting it. Every shim is identical
boilerplate — e.g. [`code_lens.py`](code_lens.py):

```python
#!/usr/bin/env python3
"""Entry shim — stable published path. Implementation: leanaudit.clones."""

# lean-audit:dup-intentional — mandated identical entry-shim boilerplate (published-path contract)
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from leanaudit.clones import *   # noqa: E402,F403
from leanaudit.clones import main # noqa: E402
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

Three facts are load-bearing when you touch a shim:

1. **The `sys.path.insert(0, ...)` side effect is what makes the package
   importable.** It puts this `scripts/` directory on `sys.path` so the absolute
   `leanaudit.<module>` imports resolve. Anything that imports a package module
   must load its shim first — the tests depend on this ordering.
2. **The `# lean-audit:dup-intentional` marker suppresses the clone lens** on the
   deliberately-identical boilerplate. This is the *whole-file* scope, which is
   right here (a shim is boilerplate end to end) and wrong on a logic module — do
   not copy it into `leanaudit/`; a logic module that genuinely needs a
   declaration uses the region scope
   ([§ Declaring intentional duplication](#declaring-intentional-duplication)).
3. **The six paths are a published contract.** Renaming, removing, or changing a
   shim's re-export surface is a breaking change. The shim↔package parity test
   pins it (see the test matrix).

| Entry shim (published path) | Implementation | `__main__` form |
|---|---|---|
| [`lean_engine.py`](lean_engine.py) | [`leanaudit/engine.py`](leanaudit/engine.py) (+ `discovery`, `registry` re-exported) | `raise SystemExit(main(sys.argv[1:]))` |
| [`code_lens.py`](code_lens.py) | [`leanaudit/clones.py`](leanaudit/clones.py) | `raise SystemExit(main(sys.argv[1:]))` |
| [`skill_load_cost.py`](skill_load_cost.py) | [`leanaudit/load_cost.py`](leanaudit/load_cost.py) | `raise SystemExit(main())` |
| [`lean_guard.py`](lean_guard.py) | [`leanaudit/guard_lean.py`](leanaudit/guard_lean.py) | `main()` (returns `None`) |
| [`load_cost_guard.py`](load_cost_guard.py) | [`leanaudit/guard_load_cost.py`](leanaudit/guard_load_cost.py) | `raise SystemExit(main())` |
| [`workflow_cost.py`](workflow_cost.py) | [`leanaudit/workflow_cost.py`](leanaudit/workflow_cost.py) (+ `context_trace`) | `raise SystemExit(main(sys.argv[1:]))` |

## Module map of `leanaudit/`

Twelve files (`__init__.py` + eleven modules). No import cycles. Six foundational
**leaves**, three analysis **engines**, two hook **drivers**:

```
hook_envelope ─┐                              (leaf: envelope parse / decision shaping)
discovery ─────┼─▶ engine  ─▶ guard_lean       (markdown dup engine + its PreToolUse guard)
registry ──────┘   clones                      (code-clone engine)
cli ───────────────▲ ▲                         (leaf: the two engines' shared CLI flags)
load_cost ─────────────────▶ guard_load_cost   (per-use cost engine + its dual-mode guard)
context_trace ─┬───────────▶ workflow_cost     (metadata-only adapters + run forecast)
discovery ─────┤
load_cost ─────┘
```

Two leaves back no shim of their own (`hook_envelope`, `cli`) — they exist to
single-source a contract two siblings share.

| Module | Role | Responsibility | Depends on |
|---|---|---|---|
| [`hook_envelope.py`](leanaudit/hook_envelope.py) | leaf | Parse the PreToolUse/Stop hook JSON payload, shape the `permissionDecision` envelope Claude Code™ reads, and log one fail-open diagnostic line to stderr. Public: `HookPayload`, `read_payload`, `permission_decision`, `fail_open_log`. | stdlib |
| [`discovery.py`](leanaudit/discovery.py) | leaf | Git-aware repo enumeration (tracked + untracked-not-ignored) and the "is this markdown a *guarded* surface" predicate. Public: `is_guarded`, `repo_paths`, `read_repo`. **Its git-enumeration block is a *declared* intentional twin of `scripts/skill_architecture_report.py`, pinned by `GitEnumerationParityTest` — change both together.** | stdlib |
| [`registry.py`](leanaudit/registry.py) | leaf | Load `.lean-audit.toml` canonical homes / carve-outs / exempt paths / the optional `[verbosity]` thresholds, plus the built-in defaults and the `sync-intentional` and `verbose-intentional` overrides. Public: `Registry`, `VerbosityConfig`, `load_registry`, `carved_out`, `path_exempt`, `has_override`, `has_verbose_override`. | stdlib |
| [`cli.py`](leanaudit/cli.py) | leaf | The argparse flags both engine CLIs accept identically (`--registry`, `--format`), single-sourced so the two declarations cannot drift; call it after a CLI's own flags to keep `--help` ordering. Public: `add_shared_flags`. | stdlib |
| [`load_cost.py`](leanaudit/load_cost.py) | leaf | Per-use load-cost measurement and the fidelity-baseline model: closure resolution, inventory extraction/diff, pointer and cost-regression checks, plus the `guard_tokens` deterministic closed-token gate (G2v) backing minify's `tighten` class. Backs the `skill_load_cost.py` CLI. Public: `resolve_closure`, `extract_inventory`, `diff_inventory`, `cost_regressions`, `guard_tokens`, `main`, … | stdlib |
| [`context_trace.py`](leanaudit/context_trace.py) | leaf | Normalize provider/host usage metadata, split model-visible/out-of-band tool results, and aggregate without retaining raw content. Public: `UsageEvent`, `normalize_trace_records`, `read_trace_file`, `summarize_trace`. | stdlib |
| [`engine.py`](leanaudit/engine.py) | engine | The deterministic **markdown** duplication/waste engine: normalize→shingle→containment scoring, section index, the emitters for `LA-DUP-*`, `LA-STALE-1`, `LA-DEAD-1`, `LA-BLOAT-1`, and the `LA-VERBOSE-1` verbosity nominator (`filler_density` / `scaffold_count` / `repeat_ratio`, composite ≥ 2-signal gate). `evaluate_added_block` is shared by the CLI and the PreToolUse guard. | `cli`, `discovery`, `registry` |
| [`clones.py`](leanaudit/clones.py) | engine | The **source-code** copy-paste clone lens: per-language comment/string/number-stripping tokenizer, seed-and-extend window matcher, identifier-diversity filter, and the `LA-CODE-DUP-*` emitters. | `cli`, `discovery` |
| [`workflow_cost.py`](leanaudit/workflow_cost.py) | engine | The **run-viability** analyzer: orchestrator nomination, local tool-schema inventory, three-lane stage simulation, verification reserve, worker/handoff multiplication, and optional metadata-only trace calibration (`LA-RUN-*`, `LA-ORCH-*`). | `context_trace`, `discovery`, `load_cost` |
| [`guard_lean.py`](leanaudit/guard_lean.py) | driver | PreToolUse guard hook (opt-in, fail-open). Reconstructs the edit's added text, and if a guarded-markdown edit introduces a *new* block-severity dup (via `engine.evaluate_added_block`) returns a `deny`. No dup logic of its own. Public: `evaluate`, `main`. | `hook_envelope`, `discovery`, `engine` |
| [`guard_load_cost.py`](leanaudit/guard_load_cost.py) | driver | Dual-mode per-use guard (opt-in, fail-open). PreToolUse: soft-block an edit that would drop an inventoried code/section/pointer below a skill's fidelity floor. Stop: enumerate session-changed `.md`, map each to its owning skill, block on fidelity regression; cost growth is advisory only. Public: `decide`, `post_edit_content`, `cost_warn_decision`, `run_stop_mode`, `main`. | `hook_envelope`, `load_cost` |
| `__init__.py` | — | Package docstring: states the stdlib-only / Py3.11+ runtime and that the entry paths are the published contract. | — |

Every module declares an explicit `__all__`; the parity test asserts each shim
re-exports it fully, so add new public names to `__all__` when you extend a
module (ruff `F822` only catches the reverse — names in `__all__` that don't
exist).

## The three analysis engines (CLIs)

All three are pure, deterministic, and scan a **directory** (never a single file — the
skill filters findings to its in-scope path set after the run). Output is text or
`--format json`. Cite the codes from [`../smell-catalog.md`](../smell-catalog.md);
this guide does not redefine them.

- **`lean_engine.py <dir>`** — markdown duplication/waste. Emits `LA-DUP-1/2`,
  `LA-STALE-1`, `LA-DEAD-1`, `LA-BLOAT-1`, `LA-VERBOSE-1`. Flags: `--added-text -` (score one
  block from stdin, needs `--source`), `--corpus-root`, `--registry`,
  `--format {text,json}`. **Exit 0** = clean, **1** = a block-severity finding
  present, **2** = engine error (bad args, unreadable file, TOML/regex error).
- **`code_lens.py <dir>`** — source-code copy-paste clones. Emits
  `LA-CODE-DUP-1/2`. Flags: `--min-tokens` (default 20), `--registry`,
  `--format {text,json}`. Same exit-code convention (2 also on `--min-tokens < 1`).
- **`workflow_cost.py <dir>`** — orchestrator/run viability. Emits source
  nominations plus optional scenario-forecast `LA-RUN-*` / `LA-ORCH-*` findings.
  Flags: `--scenario`, repeatable `--trace`, `--context-window`,
  `--verification-reserve`, `--format {text,json}`. Exit 1 only when a block
  forecast exists; exit 2 on invalid input. Traces are metadata-only.

The markdown and clone engines read `.lean-audit.toml` when present
([§ Config & data](#config-and-data-files)); absent it, they run heuristic-only.

## Declaring intentional duplication

Each engine honours an in-file **marker** that declares duplication deliberate.
The markdown side matches an HTML comment (`registry.OVERRIDE` /
`VERBOSE_OVERRIDE`); the clone lens matches a **line comment** of the scanned
file's own language, taken from that file's `COMMENT_PROFILES` entry (`#` for
`.py`/`.sh`/`.rb`, `//` for the C family, either for `.php`). Anchoring to a
comment is load-bearing: a bare substring test made `clones.py` — whose
`INTENTIONAL_MARKER = "…"` assignment *is* the marker text — exempt itself from
its own corpus. A marker inside a string literal declares nothing.

Two scopes, both implemented in `leanaudit/clones.py`:

| Scope | Form | Where it is applied |
|---|---|---|
| Whole file | `<comment> lean-audit:dup-intentional — <rationale>` | `read_sources` drops the file from the corpus |
| Region | `<comment> lean-audit:dup-intentional:begin` … `:end` | `scan_dir` post-filters the clone list |

The region form exists so a **logic module** can declare one intentional clone
without blanketing the file (repo policy puts the whole-file marker on
boilerplate/data only). Its rules, all pinned by tests:

- **Containment, not overlap** — a clone is dropped only when its span lies
  wholly inside *one* marked region; a partly-overlapping region reports as
  normal, and two adjacent regions never jointly cover a span neither declared.
- **Either side** — a pair is suppressed when *either* of its two sides is
  contained in a region of that side's own file, mirroring the whole-file marker.
- **Raw-line scan** — regions are read off the source text (comments are stripped
  before tokenizing), then intersected with `Clone.lines` / `Clone.matched_lines`,
  which are source line ranges.
- **Edges** — nesting is depth-counted (an inner pair does not close the outer
  region); an unclosed `:begin` runs to end of file; a stray `:end` is ignored;
  an unrecognized suffix degrades to the whole-file form.

Region suppression is deliberately **not** in `read_sources`: that function is a
published re-export ([§ shim → package contract](#the-shim--package-contract)),
so narrowing its return would be a breaking change. Keep new suppression scopes
in the `scan_dir` post-filter, which already holds both the raw source text and
the clone list.

## The two guard hooks

Guards are **opt-in and fail-open** — they ship OFF, and any error, timeout,
missing file, or out-of-scope path results in *allow* with at most one stderr
line. Enablement (both the PreToolUse and Stop forms, and how to override a
block) is fully documented in [`../hook-recipe.md`](../hook-recipe.md); don't
duplicate that here. What a maintainer needs to know about the code:

- Both parse their payload and shape their decision through
  [`leanaudit/hook_envelope.py`](leanaudit/hook_envelope.py); keep stdout
  **decision-only** and send diagnostics to stderr via `fail_open_log`.
- `lean_guard.py` is PreToolUse-only and adds no logic beyond
  `engine.evaluate_added_block`.
- `load_cost_guard.py` branches on the payload: a `file_path` present ⇒
  PreToolUse; absent ⇒ Stop mode (`run_stop_mode`, which diffs session-changed
  markdown against committed baselines). **The Stop path is the one wired into
  this repo**, via `scripts/agent-hooks/stop-lean-cost.sh` (at the marketplace
  source-repo root, registered in `.claude/settings.json`), which runs the guard
  with `uv` as the primary interpreter (it provisions the required Python ≥3.11
  even when the system `python3` is older), falls back to a ≥3.11 `python3`, and
  fails open (exit 0) when neither is available. Stdlib-only is not enough on
  its own — `tomllib` is stdlib only from 3.11 — so the floor, not the dependency
  set, is what makes the interpreter choice matter.
- Fidelity regression **blocks**; cost growth is **advisory** (tolerance 200
  tokens) and never blocks.

If you add or change a hook event a guard handles, add an integration test that
drives its `main()` over a real payload for that event — helper-function unit
tests don't prove the wired hook fires.

## The per-use cost harness

`skill_load_cost.py` ([`leanaudit/load_cost.py`](leanaudit/load_cost.py)) is an
argparse CLI with **required subcommands**. It backs the surface-gated per-use
lens; the operator procedure is [`../procedures/per-use-cost.md`](../procedures/per-use-cost.md).

| Subcommand | Does | Exit |
|---|---|---|
| `resolve_closure <SKILL.md>` | Print the transitive Load-Map markdown-link closure of a skill. | 0 |
| `measure --scenarios … --id …` | Token-size one scenario's file set. | 0 |
| `baseline --files … --code-patterns … --out …` | Build a `{codes, sections}` fidelity baseline from a closure. | 0 |
| `diff --baseline … --files … --code-patterns …` | Report fidelity loss vs a baseline. | 1 if regressions, else 0 |
| `guard_tokens --before … --after … --code-patterns …` | G2v closed-token gate for a minify `tighten` rewrite: after must preserve every code/link/inline-code/number/ALL-CAPS-normative token and not drop a negation's count. | 1 if any dropped, else 0 |
| `snapshot --scenarios … --out …` | Write the `{scenario: token-total}` cost floor. | 0 |

Errors (`OSError` / bad JSON / bad regex / unknown `--id`) exit **2**. The token
count is a deterministic word/punctuation proxy, not a model tokenizer — only the
before/after delta is meaningful, so a stable proxy is sufficient.

## Config and data files

**Read by the tooling:**

- `.lean-audit.toml` (at the marketplace source-repo root) —
  the registry the engines read: `[[carve_out]]` glob pairs (declared intentional
  parallels, with `{name}` captures), `[[canonical_home]]`, `exempt_paths`, and
  `code_extensions`. This repo's file is carve-out-only.
- `pyproject.toml` (at the marketplace source-repo root) — scopes ruff
  (`[tool.ruff] include`) and mypy (`[tool.mypy] files`) to **this scripts tree
  only**, and sets the repo-local `uv` cache.

**Read by the per-use harness and the Stop guard, under
`tests/skill_load_cost/` (at the marketplace source-repo root):**

| File | Shape | Meaning of a regression |
|---|---|---|
| `baselines/<skill>.json` | `{codes[], sections[]}` fidelity floor per guarded skill | An edit that drops a listed code/section below the floor → fidelity block. |
| `scenarios.json` | `[{id, skill, files[]}]` per-use scenarios | Defines the file sets the cost lens measures. |
| `cost-snapshot.json` | `{scenario-id: token-total}` cost floor | Growth beyond tolerance → advisory only (never blocks). |
| `code_patterns.json` | `[regex]` for smell/reference codes | Defines what `extract_inventory` counts as a "code". |

**Regenerate a fidelity baseline the sanctioned way** — in the marketplace
source repo (the `tests/skill_load_cost/` paths below sit at its root), from
the skill's own closure, never a directory glob (a glob-built floor would
"protect" content the guard's closure cannot reach, yielding phantom
regressions):

```bash
uv run python .../skill_load_cost.py resolve_closure <SKILL.md> --json          # closure file list
uv run python .../skill_load_cost.py baseline --files <closure files…> \
  --code-patterns ../../../../../tests/skill_load_cost/code_patterns.json \
  --out ../../../../../tests/skill_load_cost/baselines/<skill>.json
```

The tooling never mutates the repo on its own: only `baseline`/`snapshot` write,
and only to an explicit `--out`; engines and guards print to stdout.

## The enforced standard

Scoped to this tree via `pyproject.toml`: **stdlib-only, `target-version=py311`,
`line-length=100`, ruff lint select `E,F,W,I,UP,B`, `mypy --strict`.** The gate
is `tests/lean_audit_python_standard_test.py` (at the marketplace source-repo root),
which shells out to three checks (it **skips**, not fails, when the toolchain is
offline — a green offline run may mean "skipped," so confirm it actually ran):

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
```

Run `uv` from the repo root (or a wrapper that `cd`s there) so the repo-local
`.cache/uv` and `uv.lock` apply.

## Test matrix

All tests live at the marketplace source-repo root under `tests/`. Run one with
`uv run python -m unittest tests.<module>`. Keep every one green after a change.

| Test | Covers |
|---|---|
| `tests/lean_audit_python_standard_test.py` | ruff + `mypy --strict` gate. |
| `tests/lean_audit_shims_test.py` | Shim↔package parity: each shim re-exports its module's `__all__`; `--help` smoke; every public name is declared in `__all__`. |
| `tests/lean_engine_test.py` | Markdown engine + ledger calibration (`tests/lean_engine_ledger.jsonl`) at **≥0.90 precision AND recall**. |
| `tests/lean_verbosity_test.py` | Verbosity nominator (`LA-VERBOSE-1`) helpers + ledger calibration (`tests/lean_verbosity_ledger.jsonl`) at **≥0.90 precision AND recall**, plus a bounded live-repo residual. |
| `tests/lean_code_lens_test.py` | Clone lens + ledger calibration (`tests/lean_code_ledger.jsonl`) at the shipped `DEFAULT_MIN_CLONE_TOKENS`, **≥0.90 precision/recall**. |
| `tests/lean_workflow_cost_test.py` | Static orchestrator/run findings (`tests/lean_workflow_ledger.jsonl`) at **≥0.90 precision/recall**, three-lane forecast, verification reserve, trace adapters, and metadata-only output. |
| `tests/skill_load_cost_test.py` | Per-use harness; plus every committed baseline must be satisfiable by the guard's own closure. |
| `tests/lean_guard_test.py` | PreToolUse dup guard, incl. subprocess `main()` smoke. |
| `tests/load_cost_guard_test.py` | Per-use guard (PreToolUse + Stop); plus the guard stays silent on a clean tree for every committed baseline. |

Shared helper `tests/surface_test_lib.py`
(`REPO_ROOT`, `load_script_module`, `assert_precision_recall_at_least`) is
imported, not run. Run the whole set at once:

```bash
uv run python -m unittest \
  tests.lean_audit_python_standard_test tests.lean_audit_shims_test \
  tests.lean_engine_test tests.lean_code_lens_test tests.lean_workflow_cost_test \
  tests.skill_load_cost_test \
  tests.lean_guard_test tests.load_cost_guard_test
```

## Making a common change safely

Work in a clean feature worktree (repo-scanning gates over-count in the primary
checkout, which has nested worktrees). Every recipe ends with: rerun the affected
tests, then [§ Before you finish](#before-you-finish).

- **Add / retune a markdown finding code** → edit `leanaudit/engine.py`; add or
  update a code entry in [`../smell-catalog.md`](../smell-catalog.md); add gold
  rows to `tests/lean_engine_ledger.jsonl` and keep `lean_engine_test.py`
  ≥0.90 precision/recall. The `LA-VERBOSE-1` nominator is `info`-only (it cannot
  ride the block-keyed engine ledger), so it calibrates against its own
  `tests/lean_verbosity_ledger.jsonl` / `lean_verbosity_test.py` at the same bar.
- **Add a language to the clone lens** → extend `COMMENT_PROFILES` /
  `DEFAULT_EXTENSIONS` in `leanaudit/clones.py`; add ledger rows to
  `tests/lean_code_ledger.jsonl`; keep `lean_code_lens_test.py` green.
- **Add a harness subcommand** → add the handler + a new `argparse` subparser in
  `leanaudit/load_cost.py`, extend `__all__`, and add cases to
  `skill_load_cost_test.py`.
- **Change workflow forecast or trace normalization** → edit `workflow_cost.py`
  and/or `context_trace.py`; add a planted positive and paired negative to
  `tests/lean_workflow_ledger.jsonl` or an exact adapter/forecast case to
  `tests/lean_workflow_cost_test.py`; preserve metadata-only output.
- **Change guard behavior** → edit the driver in `leanaudit/`; add an integration
  test that drives its `main()` over a real payload for each event; update
  [`../hook-recipe.md`](../hook-recipe.md) if enablement or override changes.
- **Onboard a new guarded skill's fidelity floor** → regenerate its baseline the
  sanctioned way ([§ Config & data](#config-and-data-files)) and confirm the two
  committed-baseline closure-parity tests pass.
- **Touch a shim's boilerplate** → usually don't. The six paths are a published
  contract; keep the `dup-intentional` marker and re-export surface intact, and
  rerun `lean_audit_shims_test.py`. Restructuring the scanned engines requires a
  **classified** before/after finding-set diff (every delta must be a path rename
  of a base finding, an in-class declared suppression, or an adjudicated new
  class) — byte/set equality against the old baseline is unachievable by design.
  See CLAUDE.md § Repo-local Python® tooling for the classified-diff rule.

## Before you finish

- Rerun the affected tests, and the standard gate, and confirm they *ran* (not
  skipped offline).
- **Dogfood the engine on your own change** — run `lean_engine.py` over the
  changed markdown and confirm no unexpected `LA-DUP-*` / `LA-STALE-1`. This
  guide, being under `references/`, is itself scanned: cite, don't restate.
- Regenerate any affected baseline/snapshot the sanctioned way — never a glob.
- Run `scripts/skill-architecture-report.sh .` (at the marketplace source-repo
  root; repo tooling, not bundled with the installed plugin) and
  `git diff --check`.
- **Version stamping happens at integration on `main`, never in the worktree.**
  A change under this tree is a mandatory `souroldgeezer-audit` stamp; the feature
  branch must touch no version cell. See CLAUDE.md § Plugin versioning.
