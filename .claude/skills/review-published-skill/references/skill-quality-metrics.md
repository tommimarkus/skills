# Skill Quality Metrics

Use this reference to assess whether a skill is strong enough for repeated
agentic development across this repository's published plugins.

## Source Basis

- Agent Skills specification: https://agentskills.io/specification
- Agent Skills best practices: https://agentskills.io/skill-creation/best-practices
- Agent Skills description optimization: https://agentskills.io/skill-creation/optimizing-descriptions
- Agent Skills evaluation guidance: https://agentskills.io/skill-creation/evaluating-skills
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Claude Code marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Codex skills: https://developers.openai.com/codex/skills
- Codex plugin build guidance: https://developers.openai.com/codex/plugins/build
- Codex subagents: https://developers.openai.com/codex/subagents

## Hard Gates

Treat these as blockers unless the change is explicitly scoped outside the
published plugin surface:

- Invalid frontmatter, missing `SKILL.md`, or skill `name` not matching the
  directory.
- `description` missing the actual trigger context, exceeding 1024 characters,
  or becoming so broad that near-miss prompts would invoke it.
- A changed published skill lacks its paired Claude subagent or Codex
  `agents/openai.yaml` metadata.
- Plugin `name`, `version`, or `description` drifts between the two plugin
  manifests and the shared marketplace entry.
- A content-changing plugin edit lacks the required semver bump.
- A skill contract change leaves `CLAUDE.md`, `AGENTS.md`, `README.md`, or a
  project-scoped custom-agent wrapper stale.
- Changed scripts are interactive, untested, or unable to explain usage and
  errors to an agent.
- Bundled references or examples reproduce third-party copyrighted expression,
  structured spec tables, diagrams, sample files, or assets without a valid
  licence and citation path.
- A changed skill removes required outputs, weakens coverage of the user tasks
  it claims to handle, adds generic advice without changing decisions or
  failure detection, or makes the workflow materially harder to run without a
  clear compensating benefit.

## Scorecard

The scorecard is the task-value check: each metric captures one concrete way a
skill should improve, or at least preserve, user outcomes. Rate each metric as
`pass`, `warn`, `fail`, or `not assessed`.

### 1. Trigger Quality

Strong skills trigger for the right user intent and stay quiet for nearby
non-matches.

Evidence to prefer:

- `description` front-loads the use case and concrete triggers.
- Positive prompts cover casual, formal, terse, and context-heavy phrasing.
- Negative prompts include near misses that share keywords but need a different
  workflow.
- Description evals, when available, use repeated runs and a fixed
  train/validation split.

Useful benchmark: about 20 trigger queries, split between should-trigger and
should-not-trigger cases, with repeated runs when practical. A should-trigger
query should usually invoke the skill; a should-not-trigger near miss should
usually not invoke it.

### 2. Context Efficiency

The skill should spend context only on instructions the agent would otherwise
miss.

Evidence to prefer:

- `SKILL.md` is under 500 lines and focused on the workflow used every run.
- Detailed rubrics, API notes, examples, and variant-specific rules live in
  one-hop `references/` or `extensions/` files.
- `SKILL.md` tells the agent exactly when to open each support file.
- The skill cites reference sections or codes instead of duplicating long
  reference prose.

Warn on duplicated reference material or menus of equal-looking options. Fail
when the main skill body becomes a reference dump or hides required procedures
in unmentioned files.

### 3. Agentic Operability

The skill should be easy for an agent to execute in a real workspace.

Evidence to prefer:

- Imperative steps with explicit inputs, outputs, and stop conditions.
- Defaults are chosen for the agent, with alternatives named only as escape
  hatches.
- Fragile or repetitive work is moved into tested scripts.
- Scripts avoid prompts, document `--help`, use clear exit codes, separate
  data from diagnostics, and keep output sizes predictable.
- Workflows include a validation loop: perform, verify, fix, rerun.

Warn when instructions are vague or require hidden human knowledge. Fail when
the agent must guess destructive behavior, production targets, or script
arguments.

### 4. Degree-of-Freedom Calibration

Match specificity to task fragility.

Pass when:

- High-freedom prose is used for judgment-heavy review or design work.
- Medium-freedom pseudocode or examples guide preferred patterns without
  freezing valid variation.
- Low-freedom scripts or exact commands cover fragile transformations,
  packaging checks, or repeated parsing.

Warn when the skill offers many choices without a default. Fail when a fragile
operation is left to ad hoc reasoning or a flexible creative task is overfit to
one narrow example.

### 5. Runtime Portability and Parity

Published skills in this repo must remain coherent across both supported
runtime surfaces.

Evidence to prefer:

- Claude skill, Claude subagent, Codex skill metadata, and Codex custom-agent
  wrapper agree on what the skill does.
- Plugin manifests and marketplace entries agree on package identity.
- Runtime-specific features are isolated to the runtime-specific metadata file
  rather than baked into the shared workflow unnecessarily.
- Packaging or discovery changes are checked against current official docs for
  both runtimes.

Warn on harmless wording drift. Fail on stale invocation contracts, missing
metadata, or manifest mismatch.

### 6. Release Hygiene

The repository should remain installable, auditable, and easy to update.

Evidence to prefer:

- JSON manifests validate with `jq`.
- YAML, TOML, and XML surfaces inspect cleanly with `yq`.
- Plugin semver bump matches the blast radius described in `CLAUDE.md`.
- Repo docs are updated in the same change when behavior or structure changes.
- The shared marketplace remains the only catalog unless a future design
  explicitly splits catalogs.

Warn when docs are technically true but incomplete. Fail when installed-plugin
users would not receive a required update or would receive inconsistent
metadata.

### 7. IP and Source Hygiene

The skill should encode reusable know-how without copying protected expression
or redistributing assets improperly.

Evidence to prefer:

- Source documents inform original wording rather than near-verbatim prose.
- Short quotations, if needed, are attributed and limited to the specific
  purpose.
- Third-party schemas, examples, sample files, diagrams, logos, and binary
  assets are linked or bundled only when the licence permits redistribution.
- Public-visible descriptions use careful nominative wording for product names
  and named standards.

Fail on silent copying, missing attribution for sourced paraphrases, or
unauthorized bundled assets.
