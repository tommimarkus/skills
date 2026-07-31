# Platform-Redundancy Lens (LA-NAT-1 / LA-NAT-2) — OPT-IN

Load this ONLY when the request explicitly asks whether custom artifacts reinvent
a capability Claude Code or Codex now provides natively. This lens is never part of a
default waste run and is never auto-fired by surface detection. It is read-only,
advisory, and judgment-based — the engine does not detect `LA-NAT-*`. Disclose its
findings as inference plus a live check (see
[`../../../../docs/audit-reference/audit-craft.md`](../../../../docs/audit-reference/audit-craft.md)
§2). Cite codes from [`../smell-catalog.md`](../smell-catalog.md); do not restate
catalog prose.

## Core principle: patterns are static, capabilities are live

This catalog holds **what to suspect**, never **what is native**. Claude Code's
and Codex's feature sets change fast, so a verdict is never taken from this file.
For Claude Code it comes from a live `claude-code-guide` consultation; for Codex
it comes from current official OpenAI documentation. A reinvention pattern
stays useful even when its verdict flips; only the live check decides whether a
candidate is actually redundant today.

## When this lens runs

Gate: an explicit native/platform-redundancy request (e.g. "is anything here
already provided by Claude Code natively?", "is Codex already doing this?",
"am I reinventing platform features?",
"platform-redundancy check"). No such request → emit nothing. A plain
duplication/waste request does NOT activate this lens and triggers no agent or
network call.

## Reinvention-pattern catalog (candidates to suspect)

Each entry is a *pattern to nominate*, mapped to a suspected native capability.
Nomination is not a finding — every candidate must pass the live check below.

**Custom hooks & scripts**
- bespoke dangerous-command blocker / allowlist script → native hooks + permission rules
- commit-message linter invoked by a custom script → native hooks (PreToolUse / Stop)
- file-protection / "don't touch X" guard script → native permission rules / hooks
- format-on-save or run-tests-on-stop wrapper → native PostToolUse / Stop hooks

**Guidance prose (CLAUDE.md / AGENTS.md / skill prose)**
- "maintain a TODO / task list" → native todo tracking
- "spawn parallel workers / sub-tasks" → native subagents / Task
- "use a scratchpad or git worktree for isolation" → native worktrees
- "plan before acting / get approval first" → native plan mode
- "remember X across sessions" → native memory
- "search the web / fetch this URL" → native WebSearch / WebFetch
- "run this long task in the background" → native background tasks

**Custom skills / commands / agents**
- a hand-rolled commit / code-review / research command or skill → built-in equivalents

**Custom MCP / integrations**
- a bespoke filesystem / git / fetch MCP server → native file tools / `gh` / WebFetch

Treat this list as seed coverage, not a closed set — nominate any artifact whose
job plausibly overlaps a platform capability.

## Stage 1 — Candidate detection (deterministic)

Scan the in-scope artifacts, match against the catalog, and emit candidates of the
shape `(custom artifact path + quoted excerpt, suspected native capability)`. Do
not assign a verdict. Record the artifact family for each candidate (hooks/scripts,
guidance prose, skills/commands/agents, MCP).

## Stage 2 — Live verification (runtime-specific)

First identify the runtime named by the request or active plugin surface. Never
transfer a capability verdict from one runtime to the other.

**Claude Code lane.** For each candidate, consult the `claude-code-guide`
subagent with a question of the form: "Does Claude Code natively provide
<capability>? If yes, cite the official docs, and note any caveats, required
configuration, or version floor. If no, say so." Use its cited answer as the
evidence. This preserves the established Claude workflow.

This lane requires the ability to dispatch `claude-code-guide`. When
`lean-audit` runs in the main conversation that capability is present. When it
runs *as a subagent* (its own tool set is `Bash, Read, Grep, Glob, Skill` — no
`Agent`/`WebFetch`), the live check is unavailable: run Stage 1 only, emit each
candidate as an unverified `LA-NAT-2` review item, and disclose the degraded
coverage. Documented fallback when the main context lacks that agent type: a
targeted fetch of official Claude Code docs with the same citation discipline.

**Codex lane.** For each candidate, consult the current official OpenAI docs or
Codex manual capability, cite the supporting page, and record caveats, required
configuration, or version floors. If official-doc access is unavailable, run
Stage 1 only, emit each candidate as an unverified `LA-NAT-2` review item, and
disclose the degraded coverage.

In both lanes, never promote to `LA-NAT-1` without a live citation.

## Stage 3 — Synthesis and tiering

Map each verified candidate to a code and confidence:

- Agent confirms a **drop-in** native equivalent (cited) → `LA-NAT-1`, confidence `HIGH`.
- Agent confirms native covers the **core but with caveats / config** (cited) → `LA-NAT-1`, confidence `MEDIUM`.
- Agent is **uncertain / partial overlap**, or the live check was unavailable → `LA-NAT-2`, confidence `LOW` (review).
- Agent confirms **not native** → non-finding; record the candidate and the reason, emit no code.

audit-craft §2 governs: the nomination is inference; the citation is the fact that
promotes it.

## Emit (per finding)

- **code** — `LA-NAT-1` or `LA-NAT-2`
- **confidence** — `HIGH` / `MEDIUM` / `LOW`
- **artifact** — the custom artifact path + the quoted excerpt that reinvents the capability
- **family** — hooks/scripts | guidance prose | skills/commands/agents | MCP
- **native alternative** — the capability the platform provides, with the doc citation(s) from the live check (or "unverified — live check unavailable" for `LA-NAT-2`)
- **caveats** — for `MEDIUM`: the config / version / behavioural gaps the native version has
- **consequence** — the maintenance cost of keeping the reinvented version (audit-craft §3 consequence field)
- **recommended move** — always *review*, framed as "review and decide; do not blind-delete — your custom version may intentionally do more"
- **risk tier** — per [`../../../../docs/audit-reference/materiality.md`](../../../../docs/audit-reference/materiality.md); a reinvention in a high-fan-in surface (e.g. CLAUDE.md) outranks the same in a leaf file. Combine with severity into the P0–P3 worklist.

## Disclosure (feeds the SKILL.md footer)

Report the run's lens footer fields exactly as specified in
[`../../SKILL.md`](../../SKILL.md) §"Output footer (audit-craft §5)" (the
platform-redundancy block) — do not improvise or drop fields. The observed-on
date and the disclosed network dependency are how the lens's non-determinism
stays honest.
