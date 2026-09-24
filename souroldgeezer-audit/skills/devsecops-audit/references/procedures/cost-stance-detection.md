# Cost Stance Detection

Resolve the audit's cost stance by walking the precedence chain. Return both the resolved stance (`free` | `mixed` | `full`) and the source (`arg` | `config.yaml` | applicable repository guidance | `default`) so the report footer can cite it. Repository guidance means the target repository's active `AGENTS.md` and `CLAUDE.md`; inspect both when present, regardless of the current harness, so choosing a runtime does not hide cost-policy evidence. Keep the target repository root distinct from this skill's bundled configuration root.

## Inputs

- Invocation args (if any were passed to the skill or agent).
- `skills/devsecops-audit/config.yaml` under the target repository root (may or may not be present — if absent, this step contributes nothing). Run the command from that root; do not accidentally resolve the path against the bundled plugin root unless that plugin is itself the audit target.
- `AGENTS.md` and `CLAUDE.md` at the target repository root, as applicable to the active host and scope.

## Precedence (highest wins)

1. `--cost-stance=<value>` in the invocation args
2. `skills/devsecops-audit/config.yaml` → `costStance` field
3. Applicable target-repository guidance in `AGENTS.md` / `CLAUDE.md` § "Cost Guidance" auto-detect
4. Hard default: `full`

## Step 1 — Invocation arg

Parse any token matching `--cost-stance=<value>` from the invocation args. Accept `free`, `mixed`, `full`. On invalid value, log a warning line (`invalid --cost-stance value: <value>, ignored`) and fall through to step 2.

If the arg is present and valid, return `{stance: <value>, source: arg}` and stop.

## Step 2 — Config file

Run:
```bash
test -f skills/devsecops-audit/config.yaml && yq eval '.costStance // "null"' skills/devsecops-audit/config.yaml
```

If the command prints `free`, `mixed`, or `full`, return `{stance: <that value>, source: config.yaml}` and stop. If it prints `null` or the file is missing, fall through to step 3.

When `costStance` is `mixed`, also run:
```bash
yq eval '.mixedEnabled[]' skills/devsecops-audit/config.yaml
```
to get the list of Band 2 codes to activate. Return these alongside the stance as `{stance: mixed, mixedEnabled: [...], source: config.yaml}`.

## Step 3 — Repository guidance auto-detect

Inspect each present `AGENTS.md` and `CLAUDE.md` at the target repository root. Apply the guidance scoped to the current host and task first, and retain any matching cost policy in the other file as evidence so runtime choice cannot hide it. If only one file declares a cost policy, use it unless it is explicitly scoped away from this audit. If both declare conflicting policies, disclose the conflict and do not apply Band 2 until the effective stance is resolved. Do not read the skill's own repository guidance as if it were target-repository policy. Locate headings that match (case-insensitive) `cost guidance`, `cost stance`, `cost ceiling`, or `hobby project`. In the body under those headings, search for any of:

- `prefer[s]?\s+free\s+tier`
- `free[- ]tier(\s+only)?`
- `hobby\s+project`
- `avoid\s+.*recurring\s+cost`

Use Grep, not raw shell, and search both target guidance files when present:
```
Grep with pattern "prefer.*free.*tier|free[- ]tier|hobby.*project|avoid.*recurring.*cost" in AGENTS.md CLAUDE.md (case-insensitive)
```

If one file matches, return `{stance: free, source: AGENTS.md}` or `{stance: free, source: CLAUDE.md}` as appropriate and disclose its source. If both files match with the same stance, report both sources; if they conflict, disclose the conflict and do not silently fall through to `full` or apply Band 2 until the effective stance is resolved. If neither matches, fall through to step 4.

## Step 4 — Hard default

Return `{stance: full, source: default}`.

A security skill defaulting to `full` is deliberate: silently suppressing Band 2 findings is a worse failure mode than firing too many. A repo that cares about cost must declare it.

## Output

The caller receives a struct equivalent to:
```
{stance: "free"|"mixed"|"full", source: "arg"|"config.yaml"|"AGENTS.md"|"CLAUDE.md"|"default", mixedEnabled: [code, ...]}
```

And emits a one-line disclosure for the report footer:
```
Cost stance: <stance> (source: <source>)
```

When stance is `mixed`, append:
```
Mixed Band 2 enabled: <comma-separated list of codes>
```

When stance is `free` (or `mixed` without a given extension's Band 2 codes), each extension that contributed Band 2 findings emits one `info` suppression line:
```
Cost stance: free → Band 2 smells suppressed for <extension>: <comma-separated codes>
```
