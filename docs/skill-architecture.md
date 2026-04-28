# Skill Architecture Craft Standard

This is the canonical advisory standard for authoring, reviewing, and improving
skills in this repository. It applies to published plugin skills, matching
agents, runtime metadata, bundled references, repo-internal authoring skills,
and documentation that describes those surfaces.

This standard is broader than anti-bloat. A good skill has precise triggering,
calibrated workflow language, progressive disclosure, runtime parity,
deterministic validation, context discipline, stop conditions, output contracts,
rerun guidance, and an improvement loop that can detect both progress and
degradation.

Use this document for judgment. Use `scripts/skill-architecture-report.sh` for
repeatable detection and report formatting when that script is available.

## Four Authoring Surfaces

### 1. Trigger metadata

Trigger metadata is the pre-load contract. It decides whether the agent reads
the workflow at all.

Write trigger metadata to maximize useful activation, not raw activation:

- Name the task, symptom, artifact, runtime, or user wording that should load
  the skill.
- Keep workflow steps out of descriptions unless the runtime requires a brief
  capability summary. A description that reads like a shortcut can cause agents
  to skip the full workflow.
- Include clear exclusions when sibling skills own nearby work.
- Avoid broad phrases such as "best practices", "general help", or "any code"
  unless the skill truly owns that surface.
- Keep runtime metadata synchronized across Claude Code and Codex surfaces:
  plugin manifests, marketplace entries, agent files, project-scoped Codex
  agents, and per-skill Codex metadata.

Trigger quality is a precision and recall problem. Low precision wastes context
and can steer agents into the wrong workflow. Low recall means the skill exists
but does not load when users need it.

### 2. Always-loaded workflow `SKILL.md`

`SKILL.md` is the small working set the agent reads when the skill triggers.

It should contain:

- A direct purpose statement and ownership boundary.
- Mode selection or task classification when the skill has more than one path.
- Ordered steps that change decisions, not generic coding-agent behavior.
- Explicit ask-vs-continue rules for ambiguity, missing inputs, cost, safety,
  destructive operations, or unsupported targets.
- Stop conditions for out-of-scope work, insufficient evidence, missing tools,
  failed validation, conflicting user requirements, or degraded context.
- Output contracts with required fields, evidence expectations, and disclosure
  footer requirements.
- Pointers to on-demand references, scripts, fixtures, and templates with
  concrete load conditions.

Keep the body compact enough that an agent can hold the whole workflow in active
context while doing real work. Move taxonomies, examples, long rubrics, and
stack-specific rules out of `SKILL.md` unless they are needed every time.

### 3. On-demand knowledge

On-demand knowledge lives behind explicit load conditions:

- `docs/*-reference/**` for bundled canonical reference material and rubrics.
- `references/**` for procedures, smell catalogs, examples, fixtures
  descriptions, and source notes scoped to a skill.
- `extensions/**` for stack, platform, or domain packs that add rules without
  replacing the core workflow.

Use progressive disclosure deliberately:

- Put the decision to load a document in `SKILL.md` with the exact relative path
  and a "read this when..." condition.
- Give each reference a narrow reason to exist.
- Split heavy material by task path or target platform.
- Keep source anchors as links and paraphrase in original wording.
- Preserve a stable finding-code namespace when references define review rules.
- Do not assume Claude or Codex will infer an overlay from folder naming alone.
  If an extension matters, the core workflow must name when to load it.

For extension overlays, `SKILL.md` owns selection:

- List each extension path from the core workflow or a one-hop load map.
- State the trigger signal: file type, framework, runtime, task mode, failure
  mode, or user wording.
- Say whether the extension adds rules, replaces a step, supplies examples, or
  provides validation commands.
- Require the agent to read the extension before applying extension-specific
  rules.
- Keep extension files narrow enough that loading one does not pull unrelated
  platform or model guidance into context.
- If a model/runtime-specific extension exists, state the eval or pressure
  scenario that justified the split and the command or prompt set used to retest
  whether it can merge back into the generic core.

This is a runtime contract, not just documentation style. Codex exposes skill
metadata first, then loads the skill body after selection; optional
`agents/openai.yaml` can influence UI metadata, invocation policy, and tool
dependencies. Claude Code keeps skill names and descriptions available for
selection, then loads the full skill when invoked; supporting files are read
only when the skill points to them and the task needs them. In both runtimes,
references and extensions must be visible from `SKILL.md` with enough context
for a fresh agent to choose the right file without exploring the tree.

### 4. Deterministic machinery

Deterministic machinery is for work that should not depend on model judgment:

- `scripts/**` for validation, extraction, rendering, reporting, manifest sync,
  or other repeatable checks.
- `fixtures/**` for stable inputs that exercise behavior and regressions.
- `templates/**` for output shapes the agent should fill rather than invent.
- `assets/**` for redistributable files needed by the skill.

Prefer machinery when the check is structural, repetitive, brittle under prose,
or important enough to rerun after every change. Prose should explain why a
rule matters and how to interpret edge cases; scripts should calculate what can
be calculated.

## Model-Family Calibration

Use a generic core with specialized extensions. The generic core is the default
contract. Specialized model or runtime extensions are narrow overlays, not
parallel skills and not a reason to duplicate the core workflow.

First learn what works well for each target runtime and model tier. Then express
the instruction in generalized language when one shape meets the quality bar
across Claude Opus, Claude Sonnet, Claude Haiku, Codex GPT, and Codex GPT-mini.

The generic core should usually prefer:

- Clear task ownership and near-miss boundaries before procedure.
- Ordered steps that change decisions.
- Conditions before actions.
- Explicit ask, stop, continue, and validation rules.
- Fixed output contracts for repeatable comparison.
- Deterministic helpers for structural, repetitive, or high-risk checks.
- Plain active language with hard mandatory terms reserved for hard gates.

Use specialized extensions only when the generic core fails pressure scenarios
or fresh-agent tests for a specific family or tier, and the difference cannot be
solved with clearer general wording, deterministic machinery, or a narrower task
boundary.

Calibrate potential extensions against likely model differences:

- Stronger reasoning models such as Opus, Sonnet, and Codex GPT can tolerate
  more evidence synthesis, but still need explicit boundaries, stop conditions,
  and verification commands.
- Faster or smaller models such as Haiku and GPT-mini need fewer modes, tighter
  defaults, shorter references, concrete accepted/rejected target examples, and
  deterministic pre-checks for high-variance judgments.
- Runtime trigger surfaces differ. Claude and Codex metadata should still
  describe the same capability, but the exact field length, default prompt, and
  agent/subagent packaging constraints may require runtime-specific metadata.

Create a model or runtime extension only when the evidence says to split:

- The same eval prompt passes for one family or tier and fails for another.
- A smaller model loses actionability without extra rails.
- A runtime metadata limit or packaging rule forces different wording.
- A deterministic helper is needed for one runtime path but not the other.
- General wording causes over-triggering, under-triggering, or degraded output
  for a specific target after at least one rewrite attempt.

When an extension is justified, keep the common rule in the generic core and
make the extension as small as possible. State the load condition, the evidence
that justified the split, and how to rerun the comparison. Remove or merge the
extension back into the core when later evals show the generalized instruction
meets the same standard.

## Craft Scorecard

Review skills against these dimensions:

- **Trigger quality:** The skill activates for the right user intents and avoids
  stealing work from sibling skills.
- **Task-value lift:** The skill changes decisions, catches failures, or improves
  outputs beyond what a generic coding agent would already do.
- **Context efficiency:** The always-loaded workflow stays compact and pushes
  heavy knowledge behind explicit load conditions.
- **Agentic operability:** The workflow gives enough procedure, evidence rules,
  stop conditions, and output shape for an agent to act without improvising the
  contract.
- **Degree-of-freedom calibration:** The skill grants judgment where judgment is
  needed and uses deterministic checks where prose would be brittle.
- **Runtime parity:** Claude Code and Codex packaging, metadata, agents, and
  cache/install guidance describe the same user-facing capability.
- **Release hygiene:** Version, manifest, marketplace, README, and install
  guidance changes travel together when a published surface changes.
- **IP/source hygiene:** Source material is linked, paraphrased in original
  wording, and only bundled when redistribution is allowed.

## Advisory Report Contract

`scripts/skill-architecture-report.sh` should produce reports for an AI-agent
reader. The report is not just a human lint log; it should tell the next agent
what to fix, why it matters, and how to verify the fix.

Each finding should include:

- Stable finding code.
- Severity.
- Target path.
- Evidence.
- Violated rule from this standard.
- Claude impact.
- Codex impact.
- Concrete next action.
- Verification or rerun command.

Reports should group targets by skill or repo surface so an agent can fix a
coherent area without mixing unrelated ownership. The final section must be
`Next Iteration` with the top 3-5 fixes, ordered by expected skill-quality lift.

Recommended severity meanings:

- `blocker`: The skill can mis-trigger, fail to run, ship broken runtime
  metadata, violate source/IP rules, or produce materially unsafe guidance.
- `high`: The skill can produce wrong or incomplete work in common scenarios.
- `medium`: The skill is usable but wastes context, leaves important ambiguity,
  weakens validation, or creates cross-runtime drift.
- `low`: The issue is polish, maintainability, or future-proofing with limited
  immediate user impact.

Recommended report skeleton:

```text
# Skill Architecture Report

## Scope
- Targets:
- Command:
- Baseline:

## Findings
### SA-TRIGGER-001 [high] path/to/SKILL.md
- Evidence:
- Violated rule:
- Claude impact:
- Codex impact:
- Next action:
- Verify:

## Grouped Targets
- skill-name:

## Next Iteration
1.
2.
3.
```

## Improvement Loop

Use the improvement loop when changing skill architecture, trigger behavior,
workflow wording, runtime metadata, references, or deterministic machinery.

1. Capture a baseline report from `scripts/skill-architecture-report.sh`.
2. Run the fixed eval prompts or pressure scenarios for the target skill.
3. Make one focused change.
4. Rerun the report and the same eval prompts.
5. Optionally run a fresh-agent forward test when actionability matters more
   than local reasoning.
6. Classify the result as improvement, neutral, or degradation.

Classification rules:

- **Improvement:** The target issue is resolved; no same-or-higher severity
  regression appears; the fixed eval set is equal or better; fresh-agent
  actionability is preserved or improved when tested.
- **Neutral:** The target issue is partly addressed or readability improves, but
  report/eval outcomes do not move enough to claim progress.
- **Degradation:** The target remains unresolved, a same-or-higher severity
  regression appears, eval results worsen, runtime parity drifts, or a fresh
  agent loses actionability.

Do not claim improvement from prose preference alone. Tie the claim to the
report, eval prompts, or forward-test behavior.

## Degradation Checks

Before finishing a skill change, inspect for these common regressions:

- The trigger became louder but less precise.
- The workflow added steps without changing decisions or failure detection.
- The skill now duplicates a sibling skill instead of delegating.
- Heavy reference material moved into always-loaded context.
- Codex metadata and Claude Code metadata diverged.
- Deterministic checks were replaced by prose-only reminders.
- Output fields became optional without a compensating reason.
- Rerun guidance was removed or became ambiguous.
- Source anchors were copied as prose instead of linked and paraphrased.

## Source Anchors

Use these as anchors for current authoring and validation decisions. Link to
them; do not copy their prose into repo guidance.

- Anthropic Agent Skills overview:
  <https://docs.claude.com/en/docs/agents-and-tools/agent-skills>
- Claude Code skills:
  <https://code.claude.com/docs/en/skills>
- Anthropic Claude Skills best practices:
  <https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices>
- Claude Code plugin creation:
  <https://code.claude.com/docs/en/plugins>
- Claude Code plugin marketplace distribution:
  <https://code.claude.com/docs/en/plugin-marketplaces>
- Claude Code plugin reference:
  <https://code.claude.com/docs/en/plugins-reference>
- OpenAI Codex skills:
  <https://developers.openai.com/codex/skills>
- OpenAI Codex plugins:
  <https://developers.openai.com/codex/plugins>
- OpenAI Codex plugin build guide:
  <https://developers.openai.com/codex/plugins/build>
- OpenAI Codex subagents:
  <https://developers.openai.com/codex/subagents>
- OpenAI prompt guidance:
  <https://developers.openai.com/api/docs/guides/prompt-engineering>
- ISO 24495-1 plain language:
  <https://www.iso.org/standard/78907.html>
- ASD-STE100 Simplified Technical English:
  <https://www.asd-ste100.org/>
- Cognitive load theory:
  <https://doi.org/10.1016/0361-476X(88)90023-7>
- Lost in the Middle:
  <https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/Lost-in-the-Middle-How-Language-Models-Use-Long>
- Prompt formatting sensitivity:
  <https://arxiv.org/abs/2310.11324>
- Prompt order sensitivity:
  <https://www.ornl.gov/publication/prompt-phrase-ordering-using-large-language-models-hpc-evaluating-prompt-sensitivity>
- Information retrieval precision and recall:
  <https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-in-information-retrieval-1.html>
