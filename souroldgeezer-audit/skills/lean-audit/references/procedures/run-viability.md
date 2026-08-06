# Run Viability and Orchestrator Survivability

Use this procedure for `LA-RUN-*` and `LA-ORCH-*` when a skill/plugin workflow
has staged, iterative, delegated, retrying, or long-running execution, or the
request asks whether a run can finish within a token/context budget. This lens
is read-only, offline by default, and separate from the static closure cost in
`per-use-cost.md`: closure cost measures what loads; run viability models what
accumulates, repeats, fans out, and must remain available until verification.

<!-- lean-audit:workflow-intentional — four analyzer-output catalog examples below intentionally name workflow signals without declaring a runnable contract -->

## Contents

1. [The protected outcome](#the-protected-outcome)
2. [Evidence layers](#evidence-layers)
3. [Run the offline analyzer](#run-the-offline-analyzer)
4. [Find the orchestrator](#find-the-orchestrator)
5. [Inventory hook injection](#inventory-hook-injection)
6. [Build a budget scenario](#build-a-budget-scenario)
7. [Interpret the forecast](#interpret-the-forecast)
8. [Calibrate with traces](#calibrate-with-traces)
9. [Finding rules](#finding-rules)
10. [Remediation and fidelity](#remediation-and-fidelity)
11. [Output contract](#output-contract)

## The protected outcome

Protect a completed, usable verification result. Low average tokens are not a
success when retained coordinator context fills before tests finish. Measure two
quantities separately:

- **peak retained context:** whether the persistent orchestrator remains
  operational and coherent;
- **total run tokens:** all orchestrator, worker, retry, hook, schema, tool, and
  output usage, including repeated prefixes.

Reserve context for final verification. A workflow that fits its build stages
but cannot ingest the last test result is `infeasible`, not merely expensive.

## Evidence layers

Use the strongest available layer and disclose it per number:

1. **Provider/host measured:** direct usage or component token fields.
2. **Event-correlated:** aggregate usage aligned to explicit stage/tool/hook
   events without inventing an unavailable component split.
3. **Exact recount:** a provider token-count endpoint or compatible tokenizer.
4. **Controlled A/B:** equivalent captured runs differing in one exposure.
5. **Stable proxy:** the bundled word/punctuation counter; useful for deltas and
   ranges, not a claim about one model tokenizer.
6. **Unknown:** emit the gap; do not turn it into zero or a precise estimate.

Static workflow prose is inference. An observed trace confirms what happened in
that run, not what every future run will do. Separate both from user-declared
scenario assumptions.

## Run the offline analyzer

Use `uv` as primary. Claude Code:

```text
uv run "${CLAUDE_PLUGIN_ROOT}/skills/lean-audit/references/scripts/workflow_cost.py" <repo> --format json
```

Codex:

```text
uv run "<skill-dir>/references/scripts/workflow_cost.py" <repo> --format json
```

The corresponding `python3` form is a fallback only when Python is at least
3.11. Exit `0` means no block finding, `1` means a forecast emitted a block,
`2` means invalid/unreadable input, and the shim exits `3` below Python 3.11.

The offline pass reads tracked and unignored markdown workflow surfaces, local
JSON `inputSchema` / `input_schema` definitions, and recognized
`.codex/hooks.json` / `.claude/settings.json` hook registrations. It makes no
network, provider, MCP tool, hook-command, or agent call. It emits:

- workflow artifacts with proxy tokens and detected phases;
- ranked orchestrator candidates and their signals;
- locally visible tool-schema inventory;
- a content-free hook registration ledger;
- source-readable retry, progress, scope-resolution, and checkpoint findings;
- limits that prevent an exact finishability verdict.

A catalog or example surface that necessarily contains those signal words may
declare the file-wide source-nomination carve-out with the exact HTML comment
`<!-- lean-audit:workflow-intentional — rationale -->`. The comment must be a
real Markdown HTML comment outside fenced code; a bare substring, near-match,
or fenced example does not declare anything. Use it only when the whole file is
reference material rather than a runnable workflow, and include the rationale.
The analyzer still inventories hook/tool metadata from the rest of the scan.

For a file/diff audit, filter source findings to the in-scope paths as the main
workflow does. A whole-repo scan is needed to claim the entry/orchestrator graph
was fully covered.

## Find the orchestrator

An orchestrator is the persistent control plane, not merely a file named
`orchestrator`. Rank entry skills, agents, commands, and procedures using:

- lifetime across preflight, discovery, plan, build, and verify phases;
- worker/tool fan-out and collection of their results;
- participation in iteration, retry, or feedback loops;
- ownership of progress, decisions, and stop conditions;
- retained state returned to later stages;
- many incoming workflow references or high fan-in.

Treat the deterministic score as nomination. Confirm the candidate by reading
the entry path and its direct workflow pointers. When two agents alternate
control, report both and identify the handoff boundary; do not force a single
orchestrator.

The orchestrator should retain objective, approved plan, decisions, progress,
blockers, compact evidence pointers, and the next decision. Source dumps, raw
logs, complete diffs, repeated discovery inventories, and worker reasoning
belong in task-local contexts or out-of-band artifacts.

## Inventory hook injection

The default static result inventories command-hook registrations but treats the
command itself as opaque. Output includes only the runtime, config path, event,
registration/hook indexes, hook type, and `command_present: true`; it never
executes or emits the command. Unsupported hook/config shapes are disclosed
instead of guessed.

To add measured or declared injection evidence, supply repeatable content-free
JSON or JSONL fixtures:

```text
workflow_cost.py <repo> --hook-fixture hook-cost.jsonl --format json
```

Each fixture row selects one registration with exactly `path`, `event`,
`registration_index`, and `hook_index`. It may add only `enabled`, `visibility`,
`frequency`, and `proxy_tokens` evidence, for example:

```json
{"path":".codex/hooks.json","event":"Stop","registration_index":0,"hook_index":0,"enabled":true,"visibility":"model","frequency":3,"proxy_tokens":120}
```

`visibility` is `model` or `out-of-band`; `frequency` and `proxy_tokens` are
non-negative integers. The model-injected total includes a row only when it is
explicitly enabled, model-visible, and has both numeric frequency and proxy
tokens, then multiplies `frequency * proxy_tokens`. Missing or unsupported
evidence remains `unknown`, never zero or free. The ledger is evidence for the
hook row in the cost waterfall or a later scenario; it does not infer how often
a configured hook fires.

## Build a budget scenario

An exact verdict requires a JSON scenario passed through `--scenario`. Never
infer context capacity from a model name. Use a user declaration, checked host
configuration, or current cited provider documentation; otherwise leave
`context_window` absent and emit `indeterminate`.

Every scalar token field accepts an integer or a range:

```json
{"low": 1000, "expected": 1500, "high": 2500}
```

Require `0 <= low <= expected <= high`. Iterations require `low >= 1`.

```json
{
  "id": "plugin-software-process",
  "context_window": 128000,
  "verification_reserve": 16000,
  "calibration_tolerance": 0.15,
  "orchestrator": {
    "base_tokens": {"low": 9000, "expected": 11000, "high": 14000}
  },
  "stages": [
    {
      "id": "discovery",
      "role": "discovery",
      "prompt_tokens": 4000,
      "tool_schema_tokens": 1800,
      "hook_tokens": 300,
      "tool_result_tokens": {"low": 4000, "expected": 8000, "high": 14000},
      "out_of_band_result_tokens": 20000,
      "output_tokens": 1200,
      "retained_tokens": 3500,
      "compaction_target": 16000
    },
    {
      "id": "build-loop",
      "role": "build",
      "iterations": {"low": 1, "expected": 3, "high": 5},
      "prompt_tokens": 1800,
      "tool_result_tokens": 2500,
      "output_tokens": 900,
      "retained_tokens": 1200,
      "workers": {
        "count": 2,
        "shared_prefix_tokens": 3500,
        "local_tokens": 2200,
        "tool_result_tokens": 2800,
        "output_tokens": 900,
        "handoff_tokens": 450
      }
    },
    {
      "id": "verify",
      "role": "verify",
      "prompt_tokens": 2200,
      "tool_result_tokens": {"low": 2500, "expected": 5000, "high": 10000},
      "output_tokens": 1000,
      "fixed_output_tokens": 250,
      "per_item_output_tokens": 90,
      "item_count": {"low": 4, "expected": 8, "high": 15},
      "retained_tokens": 800
    }
  ]
}
```

Field semantics:

- `base_tokens`: instructions and state already held by the orchestrator.
- `prompt_tokens`: stage-local prompt/context added to each call.
- `tool_schema_tokens`: exposed tool definition tax on each call; do not count
  deferred tools that are not exposed.
- `hook_tokens`: hook output injected into model context. Out-of-band hook logs
  are zero here.
- `tool_result_tokens`: model-visible tool/test/log payload; external artifacts
  are zero here and belong in evidence paths.
- `out_of_band_result_tokens`: measured external log/artifact payload retained
  for operational visibility but never injected into model context. It appears
  in the waterfall as an observation and is excluded from model token totals.
- `output_tokens`: generated completion tokens not represented by the fixed and
  per-item components below.
- `fixed_output_tokens`: generated output paid once per stage iteration.
- `per_item_output_tokens`: generated output multiplied by `item_count` in each
  stage iteration.
- `item_count`: number of emitted findings/items/records. When fixed or per-item
  output is declared without this field, those components are excluded, the
  legacy `output_tokens` value remains, and the analyzer emits a limit. The
  missing count is unknown, not a zero-cost output forecast.
- `retained_tokens`: how much stage payload survives for later stages. When
  omitted, the analyzer conservatively retains prompt, hook, result, handoff,
  and output tokens; tool schemas are repeated per call but not retained as
  conversation history.
- `compaction_target`: orchestrator context after an explicit checkpoint. It is
  applied after the stage/loop, never inferred from words such as “concise.”
- `workers.count`: fan-out per iteration.
- `workers.shared_prefix_tokens`: instructions/evidence duplicated into every
  worker.
- `workers.local_tokens`, `tool_result_tokens`, `output_tokens`: task-local
  worker call cost; worker `out_of_band_result_tokens` has the same exclusion as
  the stage field.
- `workers.handoff_tokens`: result returned to and retained by the orchestrator.

Run it with:

```text
workflow_cost.py <repo> --scenario run-budget.json --format json
```

`--context-window` and `--verification-reserve` may override a scenario for a
declared target host. Record the override as an engagement assumption.

## Interpret the forecast

The simulator runs low, expected, and high lanes independently. For every
stage it emits iterations, peak context, context after, total tokens, worker
tokens, handoffs, out-of-band observations, and allowed coordinator context.
The top-level `cost_waterfall` balances exactly to `total_run_tokens` when its
out-of-band observation row is excluded.

Before verification, allowed coordinator context is:

```text
context_window - verification_reserve
```

During the verification stage, the full declared context window is available.
Classify:

- `feasible`: the high lane completes verification within capacity;
- `at-risk`: expected fits but high overflows;
- `infeasible`: expected overflows before or during verification;
- `indeterminate`: capacity or required stage bounds are absent.

Always report the earliest expected and upper overflow, even when a later stage
has a larger peak. Report total-use and peak-context ranges separately. Cached
input may reduce billing/latency but still occupies logical context; do not
subtract cache reads from the peak-context calculation.

## Calibrate with traces

Supply existing JSON/JSONL traces with repeatable `--trace` flags. The analyzer
normalizes common metadata shapes from OpenAI Responses, Anthropic Messages,
Codex/Claude host telemetry, and generic OpenTelemetry GenAI records. It accepts
aggregate usage even when component attribution is unavailable.

Trace handling is metadata-only:

- never emit prompts, completions, tool arguments, tool results, or log bodies;
- distinguish `visibility: model` from `visibility: out-of-band`; unknown stays
  unknown rather than model-visible or free;
- count reasoning, cache reads/writes, and tool-result observations separately;
- retain event ID, stage, actor, and adapter only for correlation.

If a scenario declares `calibration_tolerance`, emit `LA-RUN-5` when observed
total tokens exceed the expected forecast by more than that fraction. Do not
emit calibration drift without a declared tolerance.

When hidden schema/hook overhead cannot be attributed, propose an isolated A/B
capture: same synthetic workload, one exposure changed, repeated enough to show
a stable delta. Do not execute a paid/live experiment, change host logging, or
call a plugin tool from this read-only skill without separate authorization.

The current trace lane calibrates usage totals only. It does not reconstruct
raw lifecycle events, repeated unchanged hypotheses, TDD state transitions, or
specification churn. Do not claim an observed livelock, retry plateau, or
retrieval plateau from `--trace`; the corresponding source findings below audit
declared controls, not historical behavior.

## Finding rules

- `LA-RUN-1`: emit when an iteration/fan-out path lacks a finite upper bound.
  Warn; deterministic nomination plus inference.
- `LA-RUN-2`: block when expected retained context crosses capacity; warn when
  only the upper lane crosses. Deterministic scenario forecast.
- `LA-RUN-3`: block when expected verification peak exceeds capacity or earlier
  expected overflow prevents reaching verification with a result; warn for
  upper-lane-only starvation. Deterministic scenario forecast.
- `LA-RUN-4`: emit when a retry contract lacks any one of a finite bound/count,
  terminal success, terminal failure/failure summary, or escalation. A count
  alone does not clear it. Warn; deterministic nomination plus inference.
- `LA-RUN-5`: emit only against observed trace usage and a declared calibration
  tolerance. Warn; deterministic metadata-only trace calibration.
- `LA-RUN-6`: emit when an iterative path has a bound and complete terminal
  contract but no stop/escalation rule for unchanged progress, evidence, or
  hypotheses. A fixed enumerated sweep is exempt. Warn; deterministic static
  nomination plus inference, not proof that a loop stalled.
- `LA-RUN-7`: emit when broad/full/repo-wide implementation starts while scope
  or acceptance remains unresolved. Clear it only with a resolved scope packet
  naming musts, out-of-scope work, unknowns, owners, defaults, and acceptance
  checks, or a bounded discovery spike with a question, owner, and exit
  criterion. Warn; deterministic nomination plus inference.
- `LA-ORCH-1`: emit only for model-visible bulk results. Large out-of-band logs
  are a non-finding. Warn; deterministic nomination plus inference.
- `LA-ORCH-2`: require evidence that unchanged discovery is repeated, not merely
  refreshed after invalidation. Warn; deterministic nomination plus inference.
- `LA-ORCH-3`: emit when worker return content is unbounded or raw; a named
  compact schema plus evidence pointers clears it. Warn; deterministic
  nomination plus inference.
- `LA-ORCH-4`: judgment-only. Emit when a persistent coordinator performs
  task-local source/test work and retains it, not merely because one agent owns
  a small workflow. Warn; inference.
- `LA-ORCH-5`: on an iterative path, require a bounded checkpoint contract that
  preserves objective/scope, approved decisions, progress, blockers/open
  choices, compact obligation/evidence pointers, and the next action, with an
  explicit size cap and summary/return schema. A bare `checkpoint`, `summary`,
  or `compact` keyword does not clear it. Warn; deterministic nomination plus
  inference.
- `LA-ORCH-6`: emit when worker fan-out duplicates a material shared prefix;
  report the measured/projected multiplication and preserve task-local inputs.
  Warn; deterministic scenario forecast plus inference.

For each finding use audit-craft's 5 C's plus source layer, low/expected/high
cost, projected saving, frequency assumption, fidelity risk, confidence, and
break-even uses. Break-even is:

```text
one-time remediation/audit tokens / expected tokens saved per run
```

Keep auditor overhead separate from the target workflow's savings.

## Remediation and fidelity

Prefer structural controls over “be concise”:

- retain a discovery index and invalidate entries instead of rediscovering;
- give workers a bounded return schema: result, evidence paths, changed items,
  blocker, and next decision;
- keep raw logs/diffs/test artifacts out of band and return a summary plus path;
- allocate stage-local workers fresh contexts instead of making the orchestrator
  perform detailed work;
- cap attempts and name terminal success, failure, and escalation outcomes;
- stop or escalate when failures, evidence, or hypotheses stop changing;
- resolve musts, exclusions, unknowns/defaults/owners, and acceptance before a
  broad implementation, or run a bounded discovery spike first;
- checkpoint objective, decisions, progress, blockers, evidence pointers, and
  next action under a bounded return schema before compacting detail;
- reserve verification and final-answer capacity before starting build loops;
- defer unused tool schemas and expose only the tools required in that phase;
- keep parallel workers' shared prefix minimal and move stable evidence behind
  pointers.

Do not recommend deleting evidence, tests, stop conditions, error detail needed
for diagnosis, or escalation cues. A smaller handoff must keep every consumer's
obligations reachable. Mark a move `needs-adversarial-review` when it changes
who owns state, changes a failure contract, or replaces detail with a summary
whose retrieval path is not proven.

## Output contract

Emit:

1. scope and assurance;
2. orchestrator candidates, score, evidence, and confirmed role;
3. reconstructed phases and loops;
4. profile source and every assumption/unknown;
5. verdict and low/expected/high peak context plus total run tokens;
6. earliest expected/upper overflow and verification reserve remaining;
7. cost waterfall: repeated context, schemas, hooks, model-visible results,
   handoffs, workers, fixed/per-item output assumptions, and cache observations;
8. content-free hook ledger, fixture source, model-visible frequency
   multiplication, unsupported rows, and every unknown;
9. findings with 5 C's, evidence layer, projected saving, fidelity class, and
   break-even;
10. trace adapters/content policy when traces were supplied;
11. limits and the main skill's disclosure footer, plus candidates/confidence ·
    profile source · verdict · peak/total ranges · earliest overflow · reserve ·
    trace adapters and metadata-only policy.

Never claim actual production cost, performance, completion probability, or
model capacity from a static proxy. Never call an `indeterminate` run safe.
