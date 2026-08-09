# Claude Code Execution Adapter

Read this adapter when an approved `planning-policy` plan dispatches its steps
through Claude Code. It adds host execution details to the portable tier roster;
it does not replace the shared workflow.

Use the `Agent` tool once per decomposed step. Assign the cheapest tier that
fits and preserve these portable Claude aliases and effort values exactly:

| Tier | Model alias | Effort |
|---|---|---|
| `plan-step-mechanical` | `haiku` | `low` |
| `plan-step-standard` | `sonnet` | `medium` |
| `plan-step-analytical` | `opus` | `high` |
| `plan-step-deep` | `opus` | `xhigh` |

Never substitute a versioned model identifier for an alias and never silently
downgrade a requested tier. If Claude Code cannot provide the requested alias or
effort, return `blocked:model_unavailable` with the requested tier, alias, and
effort; the parent must reassign the step or execute it locally.

Every Agent assignment includes: task and boundary; named inputs and prior
decisions; one scoped acceptance check; size band; return contract; and the
requested tier, alias, and effort. The parent keeps integration and the plan's
final verification; an agent verifies only its own drafting. If the work exceeds
its size band, the agent stops and asks the parent to re-cut it rather than
expanding scope. If an assignment is missing a load-bearing field, return
`blocked:missing_input` with the missing fields.

Run `claude plugin validate --strict` through the repository validation path to
validate configured aliases and efforts. It does not establish the underlying
version that Claude Code resolves for an alias.
