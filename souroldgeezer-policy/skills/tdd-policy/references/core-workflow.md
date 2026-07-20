# TDD Policy Core Workflow

Standing test-first discipline for repositories that initialize this policy, and
the on-demand "enforce TDD now" path. Installing the plugin is passive; a
consuming repo opts in through its own guidance. Once initialized, that guidance
is standing enforcement authority before implementation-code changes.

## Invariant

Every behavioral code change is preceded by a failing test that specifies the
intent, and shipped behavior is covered by a test that would fail if it
regressed. Enforcement of this invariant lives in the standing guidance line
(always in context), not in this skill — the skill supplies procedure, config,
variants, and opt-out handling on demand.

## Standing block template

`adopt-guidance` and the default init block MUST write a standing line that
carries the invariant inline, not a bare pointer. Template:

> `tdd-policy: <variant> — a failing test precedes implementation; RED→GREEN→REFACTOR;
> shipped behavior stays covered by a test that fails on regression. Scope <globs>.
> Exceptions <list> (logged). Enforcement <model|model+gate>.`

Design test: a model must be able to enforce the core behavior from this line
alone, skill unloaded. If it cannot, the line is underspecified — expand it.

## Default profile

Bare `tdd-policy` (no options) resolves to: variant `test-first`; scope =
production source (excludes tests, generated, migrations, config); exceptions =
spikes/prototypes/throwaway/generated (logged); enforcement `model`.

## Variants (both preserve the invariant)

- `test-first` (default): strict RED→GREEN→REFACTOR — write the failing test,
  watch it fail, implement minimally, refactor.
- `test-alongside`: test and implementation in one change, test written and
  failing first.

`test-after` + coverage floor **relaxes the invariant** and is therefore NOT a
variant — it is a logged opt-out downgrade (see Opt-out ladder), never offered
as a way to "do TDD."

## Config options

- `variant`, `scope` (globs), `exceptions` (list), `enforcement`
  (`model` | `model+gate`), `coverage-floor` (optional numeric). Semantics one
  line each.

## Opt-out ladder (must stay low-friction — this is where choice lives)

- Disable: negate/remove the init line, or `tdd-policy: off`.
- Per-task: a single phrase ("skip TDD — spike") → applied and logged in the
  footer, never silent.
- Per-scope: `exceptions` / `scope` globs.
- Downgrade: `test-after` + coverage floor — relaxes the invariant, logged as an
  opt-out, not a variant.

Every path is one line or one phrase; none require ceremony.

## Graceful degradation

If adopting guidance is malformed, ambiguous, or self-contradictory, stop and
ask or no-op — never mass-generate output. Narrow scope keeps any failure local.

## Enforcement — honest limits

Phase 1 is model-behavioral: an enforced-by-default posture, NOT a mechanical
guarantee. Standing instructions decay over long sessions and the
"about-to-write-code" moment is fuzzy, so a model can drift past it. The only
mechanical enforcement is the optional `enforcement: model+gate` PreToolUse hook
(phase 2). State this limit; do not oversell.

## Delegation

- Test adequacy / brittle assertions → `test-quality-audit`.
- Code/module design → `software-design`.
- Commit/branch preflight → `git-workflow-policy`. PR/MR → `pr-ops`. Issues → `issue-ops`.

## Output footer

End every run with:

```
tdd-policy: <mode> | variant <v> | exceptions/opt-outs applied: <list|none> |
enforcement <model|model+gate>, gate <ran|n/a> | reference core-workflow.md | delegated: <list|none>
```
