# Development-tooling behavior evidence

## Fresh-context host probes, 2026-11-02

Tested guidance/fixture revision: `f965e4409d856cfe13467faae9c38347f9de469f`
(base `6e812f9`). Each host started a new session with no inherited conversation.
The original prompt selected software-design Review, named its shared entry and
the Lantern fixture, prohibited edits/installations/delegation, and requested
independent source inspection and representative read-only execution. It also
asked about suitable reuse, a useful first-use comparator under implementation
authority, a trivial heading edit, and API ownership after discovering an importer
defect. The prompt did not supply the planted defect or expected trace.

| Host | Runtime / model evidence | Outcome |
|---|---|---|
| Codex | CLI `0.166.0`; host default model, exact model identity not emitted by the captured JSONL and therefore unknown | Exit 0. Loaded the conditional procedure, checked source clauses and executed five bounded examples including RELAY failure, and confirmed cap 9 versus source cap 6. |
| Claude Code | CLI `2.1.316`; result JSON reported `claude-opus-5-5` | Exit 0. Loaded the procedure, independently executed five traces plus RELAY failure, found the cap defect and source-body-insensitive importer, and preserved Review authority. |

Codex read the fixture README before execution; that README reveals the planted
defect and expected traces. Its result supports source checking and execution,
not an unprimed independent derivation. Claude skipped the README and oracle
when deriving its expectations. The final independent reviewer caught the earlier
overbroad Codex wording; this disclosure corrects it without rerunning the probe.

Both hosts recommended upstream repair followed by regeneration, preservation of
authored overrides, and explicit ambiguous/unsupported RELAY handling. Both
separated the four evidence layers, declined a complete-simulation claim, chose
the suitable existing command, allowed the worthwhile first-use tool, skipped
tooling guidance for a known trivial edit, and retained API contract ownership.
Parent inspection graded those observed decisions against the authored rubrics;
this is one representative Review probe per host, not eight independently executed
cases, a comparative score, an activation/discovery trial, or a quality benchmark.
The reuse/first-use/trivial/sibling answers were decisions, not implementations.
The probe named the entry, so trigger activation is checked structurally, not
established by these host runs. Neither host implemented a first-use tool in this
read-only probe. No baseline/noise comparison or universal adherence is claimed.

Commands used the original prompt on stdin, from the tested task worktree:

```text
codex exec --ephemeral --ignore-user-config --sandbox read-only --json --output-last-message <response> -
claude -p --no-session-persistence --setting-sources '' --strict-mcp-config --mcp-config '{"mcpServers":{}}' --tools Read,Grep,Glob,Bash --permission-mode plan --output-format json
```

Each invocation had an outer 180-second timeout. Initial sandbox attempts were
not passes: Codex could not initialize its local app-server (read-only filesystem),
and Claude produced no result before timeout (exit 124). The permitted host-level
retries above completed; the Codex child retained its read-only sandbox and Claude
retained plan permissions. No contributor configuration or model pin was changed.
The Claude result reported no permission denials and no spawned subagents.
Raw local prompt, stdout/stderr, Codex JSONL, and Claude result JSON are retained
beside the task worktrees in the primary checkout's ignored
`.worktrees/development-tooling-evidence/` (moved there for integration cleanup); they are
author evidence, not required installed consumer inputs. Exact Codex model identity
is unavailable evidence, separate from both observed behavior and structural checks.

## Parent execution checks

On the same original fixture, structural validation passed and observed saturation
was `[2,4,6,8]`, disagreeing with the independent source oracle `[2,4,6,6]`.
In a disposable copy under the persistent task worktree, the parent repaired the
importer mapping and regenerated records. Saturation, damp, drain/pulse interaction,
and zero-floor examples matched the oracle; all three scope identities remained;
authored overrides remained byte-identical. A second copy-only update to source
revision 2/cap 5, importer mapping and data produced `[2,4,5,5]` with overrides
unchanged. The bundled intentionally defective fixture was preserved. This proves
these bounded examples, not a general extractor or complete simulation readiness.

## Review and verification

A fresh independent read-only implementation review of `6e812f9..f965e44` found
no substantive findings against the approved intent. A separate independent
in-depth source/IP review enumerated and inspected all 34 changed paths without
sampling and ran the full-boundary prefilter (exit 0, no candidates). It checked
repository MIT terms, original fixture/source-grounding evidence, notices,
derived outputs, and referential marks under project convention/conservative
repository policy; no source/IP remediation was identified.

`in-depth verdict: no-blocker-identified`

Assurance: reasonable-hygiene in-depth; no exclusions within the changed-path
population. Unchanged content beyond relevant licence/mark context, installed
artifacts, external similarity/register searches, and runtime correctness were
excluded. Original authorship is repository-asserted and corroborated by source
inspection, not independently proven ownership. Counsel was not triggered. This
is not legal clearance. The later evidence-only report and compact planning cue
receive a separate delta review before delivery.

The full candidate sequence initially found two planning parent-route load-budget
failures (3,671/3,679 versus 3,650) among 1,772 tests, with 27 skips. The enabling-tool
cue was shortened while retaining existing scope/authority and strict-plan rules;
the focused planning cost checks then passed without increasing the budgets.
Initial fragmentation exited 123 because an empty in-progress host output used a
`.json` suffix; renaming runtime output as logs resolved it, and fragmentation
passed. The initial isolated smoke failed on sandbox DNS while fetching fresh,
checksum-verified Dediren provisioning. The network-enabled retry passed five
plugin installs, 16 shared skills, Claude/Copilot discovery, eight Dediren tools
per adapter, and normal-profile fingerprint preservation. Its standalone Codex
validator was an explicit skip because this CLI has no `plugin validate` command.
Full-suite correction and final delta checks are recorded at delivery; these
initial failed gates remain evidence and are not described as passes.

After that correction, the documented full unittest command passed: **1,772 tests,
27 skipped**, exit 0. Standard parent-route proxies are 3,640 (Claude) and 3,648
(Codex), within the unchanged 3,650 ceilings. Strict architecture revalidation
reported zero findings; scoped Lean inspection of this evidence record reported
none. The earlier full Lean run exited 0 with advisory findings, including an
existing IP-hygiene body-budget warning in unchanged content. Diff and version
checks passed; the branch changes no version cells. The failed initial suite,
corrected suite, architecture, fragmentation, smoke and guard logs remain in the
same ignored local evidence directory. No landing, stamping, or publication was
performed or authorized by these verification results.

## Integration follow-up: ecosystem tools and user preferences

The user refined the intended behavior before landing: recommend suitable
established tools even when absent, prefer the least restrictive suitable
licence where choices remain open, retain user/project choices, avoid named-tool
mandates, and recognize task-specific favorites in conversation or relevant
existing project materials without a required file format or location.

Fresh read-only Lookup probes tested `9452534dd27974413842c59a029fdaaaa177a9ab`
using the same host commands and 180-second bounds recorded above. Codex CLI
`0.166.0` completed with exit 0 (exact model still not emitted); Claude Code
`2.1.316` completed with exit 0 and reported `claude-opus-5-5`. Both read the
entry and shared procedure, without eval cases or earlier results, and answered
three original synthetic scenarios:

- Recommend absent Tool A over equally suitable installed Tool B when supplied
  A terms permit use/modification/redistribution with notice and B adds a
  commercial-use restriction; explain setup and do not install without authority.
- Recommend the user's suitable favored B for data queries over more popular,
  less restrictive C; keep the separate A preference scoped to schema comparison;
  honor a later explicit request for C for this query. Ordinary prose preferences
  need no standard file, schema, syntax, or workspace location.
- Do not override a suitable explicit broader toolchain choice merely for adoption
  or licence preference. Recommendations are distinct from mandatory tooling.

Parent inspection found both responses consistent with those supplied facts and
the new guidance. These are three decision scenarios in one new Lookup session
per host, not actual installation, industry-tool ranking, real licence analysis,
or a test of autonomous preference discovery across arbitrary on-disk formats.
The preference facts were supplied by the prompt. No named-product mandate,
preference schema, or configuration system was added. The preliminary
`ecosystem-*` host runs tested only absent-tool/licence decisions before the
later preference refinements; they are not the final-candidate evidence.
Raw final prompt, outputs and Codex JSONL use the `preferences-final-*` prefix
in the same ignored local evidence directory. Thirty-five focused tests passed;
new synthetic-case coverage checks first failed before the cases were added.

Fresh independent implementation review accepted the guidance and identified
stale load measurements; the figures were refreshed and earlier measurements
explicitly labelled historical. Separate independent source/IP review inspected
all ten changed paths in `410a965..9452534` without sampling, found no remediation
issue, and extended its prior reasonable-hygiene verdict. Hypothetical supplied
terms are original fixtures, not copied product licences or legal clearance.
The parent retains final integration verification and the exact local receipts.
