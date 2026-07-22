# TDD Policy Core Workflow

Standing test-first discipline for repositories that initialize this policy, and
the on-demand "enforce TDD now" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before implementation-code
changes.

## Invariant

Every behavioral code change is preceded by a failing test that specifies the
intent, and shipped behavior is covered by a test that would fail if it
regressed.

## Standing block template

`adopt-guidance` and the default init block follow the posture core's
standing-line rule — the invariant inline, never a bare pointer. Template:

> `tdd-policy: <variant> — a failing test precedes implementation; RED→GREEN→REFACTOR;
> shipped behavior stays covered by a test that fails on regression. Scope <globs>.
> Exceptions <list> (logged). Enforcement <model|model+gate>.`

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

- `variant` — which discipline satisfies the invariant (`test-first` | `test-alongside`; see Variants).
- `scope` — globs the policy governs (default: production source).
- `exceptions` — categories exempt from the failing-test-first gate, always logged.
- `enforcement` — `model` (behavioral default) or `model+gate` (adds the phase-2 PreToolUse backstop).
- `coverage-floor` — optional numeric minimum for the `test-after` downgrade.

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
