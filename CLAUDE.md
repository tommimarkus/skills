# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Code plugin marketplace**, not an application. The root `.claude-plugin/marketplace.json` registers one or more plugin subdirectories. There is nothing to build, lint, or test — content is Markdown + YAML. Validation is structural (correct filenames, frontmatter, schema) and semantic (does the skill's described workflow still match its SKILL.md).

## Directory layout

```
.claude-plugin/marketplace.json        ← marketplace manifest (lists plugins, owner, etc.)
<plugin-name>/
  .claude-plugin/plugin.json           ← plugin manifest
  agents/<skill-name>.md               ← one subagent per skill, same name
  skills/<skill-name>/SKILL.md         ← skill workflow
                     /extensions/      ← per-stack smell packs (see below)
                     /references/      ← smell catalog + reusable procedures
                     /config.yaml      ← optional, skill-specific (not a Claude Code standard)
undecided/                             ← skills not yet assigned to a plugin (NOT in marketplace.json)
  agents/<name>.md                     ← matching subagents sit here too
  <skill-name>/                        ← same shape as a plugin's skill dir
```

When moving a skill out of `undecided/` into a plugin (or vice versa), **also move its matching subagent file** in `agents/<name>.md`. Skill and subagent are paired by identical name.

## Plugin registration

Adding a new plugin:
1. Create `<plugin-name>/.claude-plugin/plugin.json` (required: `name`, `version`, `description`; use `author: {name, email}` and `license: MIT` defaults from memory).
2. Add it to `marketplace.json` under `plugins[]` with `name`, `source: ./<plugin-name>`, `version`, `description`.
3. Plugin description in `plugin.json` and in `marketplace.json#plugins[]` should stay in sync.

## Skill architecture (shared pattern across skills)

Skills in this repo follow a recurring shape. Understand it before editing any SKILL.md:

- **Rubric vs workflow separation.** SKILL.md is a *workflow* for applying a rubric; the rubric prose lives in a separate file. Rubrics are **bundled with the plugin** at `<plugin>/docs/security-reference/*.md` and `<plugin>/docs/quality-reference/*.md` (relative paths like `../../docs/security-reference/devsecops.md` resolve to these from a skill dir). SKILL.md must **cite** rubric sections and smell codes — never duplicate rubric prose.
- **Quick vs Deep modes.** Every audit skill exposes both. Quick = single file / PR diff, per-finding output only. Deep = whole-repo, full sectioned rollup, may use MCP probes. If the user request is ambiguous, the skill asks.
- **Findings cite codes, not prose.** Reports use smell codes like `DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`. The prose lives in the rubric.
- **Extensions are per-stack smell packs** in `skills/<skill>/extensions/*.md`. They are loaded on demand based on detected target type. They can **ADD** namespaced smells (`<ext>.HC-N`, `<ext>.LC-N`, `<ext>.POS-N`) or **CARVE OUT** core smells for idiomatic framework patterns — they **never override** core rules. Each skill's `extensions/README.md` is the authoritative convention for that skill; follow its required-sections list exactly when adding a new extension.
- **Supporting files live under `references/`.** `references/smell-catalog.md` is the compact code index; `references/procedures/*.md` are reusable sub-procedures the workflow steps into.
- **Output footers disclose state.** Every report ends with a footer listing which extensions loaded, MCP availability, cost stance (if applicable), and the rubric path. Don't remove these — they're how users audit the auditor.

## Subagents

Every skill has a matching subagent at `<plugin>/agents/<skill-name>.md`. The subagent is a thin one-shot wrapper: it invokes the skill via the `Skill` tool, follows the skill's instructions, and presents results in the skill's required shape. Subagent frontmatter: `name`, `description` (mirror the skill's description for discoverability), `tools`, `model`. When editing a skill's invocation contract (output format, required footer fields), update the matching subagent.

## Skill-specific notes

- **`devsecops-audit`** has a `config.yaml` controlling cost stance (`free` / `mixed` / `full`), with a documented resolution precedence (invocation arg > config.yaml > audited repo's `CLAUDE.md` § "Cost Guidance" > default `full`). Only `bicep.md` currently uses cost banding.
- **`test-quality-audit`** dispatches on detected test type in step 0b to select one of three rubrics (unit / integration / E2E). Extensions can use either a single-file layout (`<stack>.md`) or a core + rubric-addon layout (`<stack>-core.md` plus `<stack>-unit.md`, `-integration.md`, `-e2e.md`). The `.NET` extension is the reference for the addon pattern.

## Things that are not standard Claude Code

- `skills/<skill>/config.yaml` — skill-internal, not read by the Claude Code runtime. Safe to leave alone when editing plugin metadata.
- `skills/<skill>/extensions/` and `skills/<skill>/references/` — skill-internal supporting files (docs allow arbitrary files alongside `SKILL.md`), not a Claude Code feature.
