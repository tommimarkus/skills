# Skill Architecture Craft Standard

This is the canonical advisory standard for authoring, reviewing, and improving
skills in this repository. It applies to published plugin skills, matching
agents, runtime metadata, bundled references, repo-internal authoring skills,
and documentation that describes those surfaces.

This standard is broader than anti-bloat. A good skill has precise triggering,
calibrated workflow language, progressive disclosure, runtime parity,
deterministic validation, context discipline, stop conditions, output contracts,
rerun guidance, behavioral evidence, and an improvement loop that can detect
both progress and degradation.

Use this document for judgment only after deterministic validation is exhausted.
Use `scripts/skill-architecture-report.sh` for repeatable detection and report
formatting when that script is available; skill workflows should stay thin by
delegating structural validation to the tool.

## Load Conditions

Load this document at the start of any task that creates, edits, reviews,
triages, plans, or fixes a skill-related surface in this repository. That
includes published plugin skills, matching agents, runtime metadata, bundled
references, extensions, deterministic machinery, manifests, marketplace
entries, repo-internal authoring skills, and repo docs that describe those
surfaces.

Use it before choosing the change shape. The report is the repeatable closeout
check, but it cannot recover decisions that were made without the craft standard
in context.

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
- Keep runtime metadata synchronized across the Claude Code surfaces: plugin
  manifests, marketplace entries, and the matching subagent files.

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

A capability the `SKILL.md` advertises must be one the pinned runtime can
actually express. Verify a composed claim — a specific mode × notation × export
combination — against the runtime before shipping it; if the runtime cannot
express the combination, narrow the claim rather than let an agent invent an
ad-hoc shape to satisfy it. Back a load-bearing composed claim with a fixture or
eval that exercises it — the combinations the workflow leans on, not every
permutation.

When the skill's core result is computed by a bundled deterministic script,
prefer a single adaptive path over Quick/Deep or Build/Extract/Review mode
dispatch. Derive the assurance or coverage disclosure from input scope (partial
or diff input gives limited assurance; full enumeration gives reasonable).
Reserve mode dispatch for skills whose work needs per-scope LLM-judgment
calibration.

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
- When a reference prescribes a best-practice that picks a convention, scheme,
  or tool, state the underlying invariant and the major production-proven
  variants rather than mandating one popular option; before settling on one,
  check whether this repo's own practice already uses a different one (e.g.
  CalVer, not SemVer) — mandating an option the repo contradicts in its own
  dogfooding is an internal-consistency smell.
- A reference that disclaims a concern to a runtime layer — an "X cannot be
  proven from static source" line, or assigning X *only* to a runtime evidence
  layer — has bounded the *evidence*, not the *design obligation*. That concern
  still owes a design-time expectation: a decision default, and where reviewable
  a named smell, for the design intent of X — or an explicit delegation to the
  sibling that owns it. A concern that appears *only* in the disclaimer or
  "cannot prove" list is an undelegated hole, not a scope-out; when authoring or
  reviewing a reference, cross-check each such disclaimer for its paired
  obligation. Validated on the design references —
  [infra-design §3.11](../souroldgeezer-design/docs/infra-reference/infra-design.md)
  pairs the "actual spend is a runtime fact" disclaimer with a cost-intent
  default and the `ID-COST-1` smell, the shape to copy.
- Cite cross-file reference paths as markdown links, not bare relative paths in
  inline-code spans, so a depth-wrong or stale citation surfaces in link checks
  instead of passing the gate silently.
- Exception: to add a bundled dev/maintainer doc *without* counting it toward the
  skill's per-use load closure, reference it in `SKILL.md` as an inline-code path,
  not a markdown link — the load-closure resolver follows every markdown link in
  `SKILL.md` (after stripping code, so section placement is irrelevant) — and put
  the link-checkable markdown link on a non-closure surface such as `CLAUDE.md`.
- Preserve a stable finding-code namespace when references define review rules.
- Do not assume Claude will infer an overlay from folder naming alone.
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
- If a load map caps what a narrow mode loads (e.g. a Lookup loads at most one
  extension or matched section, not the whole detected set), the same gating
  text must name an escalation cue to a fuller mode or an explicit ask for the
  cases the cap excludes; otherwise the cap is a silent fidelity-floor violation.
- If a mode or lens is expensive and only occasionally needed (live network or
  subagent calls, long runtime), default it to explicit opt-in that fires only
  on an explicit request, not surface-gated auto-firing. A routine invocation of
  the host skill must stay cheap and make zero agent or network calls unless the
  user asked for the expensive path.

This is a runtime contract, not just documentation style. Claude Code keeps
skill names and descriptions available for selection, then loads the full skill
when invoked; supporting files are read only when the skill points to them and
the task needs them. References and extensions must be visible from `SKILL.md`
with enough context for a fresh agent to choose the right file without exploring
the tree.

### 4. Deterministic machinery

Deterministic machinery is for work that should not depend on model judgment:

- `scripts/**` for validation, extraction, rendering, reporting, manifest sync,
  or other repeatable checks.
- `fixtures/**` for stable inputs that exercise behavior and regressions.
- `templates/**` for output shapes the agent should fill rather than invent.
- `assets/**` for redistributable files needed by the skill.
- packaged runtime artifacts for redistributable deterministic tools whose
  source and build tooling live in a separate repo-level project, not the
  shipped skill. Keep them with the skill's other deterministic machinery (for
  example under `references/scripts/`). The package or fetch script must rebuild
  or re-pin the artifact from its upstream source, keep development-only source
  and build outputs out of the shipped skill runtime, and print enough evidence
  for reviewers to verify what was included.

Prefer machinery when the check is structural, repetitive, brittle under prose,
or important enough to rerun after every change. Prose should explain why a
rule matters and how to interpret edge cases; scripts should calculate what can
be calculated.

A bundled compensating script is not automatically a thin shim just because a
pinned upstream runtime ships a new tool surface (for example an MCP server)
that appears to subsume it. Before migrating or deleting it, enumerate what it
does *beyond* invoking the runtime and attribute each responsibility to either
an upstream capability gap or a local convention of ours. When the new surface
has the same shape as the old one, those gaps persist — migrating cannot remove
the compensating layer, it only relocates tested machinery into per-run model
judgment, the silent-corruption class the script existed to prevent. Keep the
script for the gap lanes, file the capability gaps upstream, and migrate only the
lanes where the new surface is a genuine switch.

When a gate or pre-filter is meant to widen what gets caught, check it against
each subclass of the target signal: a heuristic can silently exclude the very
case it was added for (e.g. a turn-count filter drops single-turn self-correction).

Before adding an enforcement or prevention layer (for example a blocking
at-edit hook) on top of a detector, run the detector on the real target corpus
and measure how many of its findings are intentional or structural. If most are
idiomatic (parallel structure, subagent mirrors, thin wrappers), the fix is
engine-level carve-outs that recognize the idiom, not per-instance registry
exemptions or shipping a noisy enforcement layer.

Dogfood a deterministic engine on the real corpus before calling the task done —
especially one that concatenates or relates multiple files (a clone detector, a
cross-reference resolver, a repo-wide cost model). The synthetic fixtures in a
test ledger are tiny by construction and systematically miss the cross-file and
scale cases the real repository exercises: a seed window straddling a file
boundary in a concatenated token stream, or a citation written relative to a base
the resolver never modeled. For a reference / citation / path-resolution detector
specifically, model *every* base the corpus cites from (doc-dir, skill-root,
plugin-root) and exclude non-citation contexts — fenced and inline code,
regex/glob snippets, illustrative convention mentions — then confirm the
false-positive rate on the real corpus before shipping; a
resolver that models only some bases structurally yields all-false-positives on a
repo whose citations use the ones it omitted.

Skill-local scripts should be usable without an agent reverse-engineering them:
provide noninteractive help, stable exit codes, and structured output when a
downstream check needs machine-readable results. Stateful scripts should expose
a dry-run mode or be idempotent enough that rerunning them cannot silently
corrupt the repository or generated artifacts.

A mutating script that resolves its target repository root from its own location
(`Path(__file__)…`) instead of from the working directory or an explicit
`--repo-root` can silently write to the *wrong* checkout: run one checkout's copy
from inside another git worktree with the root left at its `__file__`-derived
default, and the mutation lands where the script lives, not where you are
standing. Guard every *mutating* subcommand whose root was left at that default — refuse,
or at least warn — unless the resolved root is the same git worktree as the
current directory (`git -C <cwd> rev-parse --show-toplevel` equals the resolved
root's toplevel); an explicit `--repo-root` is a deliberate target and is exempt.
A plain path-ancestor test is not enough where worktrees nest under the primary
checkout (`.worktrees/**`, `.claude/worktrees/**`): the primary root is an
ancestor of a nested worktree's directory, so the check passes while the write
still hits the wrong tree. Read-only subcommands are exempt; the safest default
is to resolve the root from the working directory (as `scripts/version_stamp.py`
does), so a missing `--repo-root` targets the checkout you are in.

A skill that invokes a script bundled beside its `SKILL.md` must reference it
through a documented Claude Code path substitution — canonically
`${CLAUDE_SKILL_DIR}` (the skill's own directory), or another documented
variable that substitutes inline in skill and agent content such as
`${CLAUDE_PLUGIN_ROOT}`. A bare or invented shell variable like `$SKILL_DIR` is
never substituted: it expands to empty, so the bundled script is silently
unfindable once the plugin is installed, and only appears to work in the
marketplace source repo through a guessable relative path. Reference files read
raw are not substituted, so establish the value in `SKILL.md` and carry it into
any procedure the workflow steps into. Substitution reaches skill and agent
*content*, but not every context equally: `${CLAUDE_SKILL_DIR}` expands in the
`SKILL.md` body, while `${CLAUDE_PLUGIN_ROOT}` expands inline in skill/agent
content **and** in hook, monitor, and MCP/LSP-config commands. Critically,
`${CLAUDE_SKILL_DIR}` is **not** substituted in `SKILL.md` frontmatter hook
commands — there it expands to empty exactly as a bare variable would (a known
Claude Code limitation, `anthropics/claude-code#36135`, closed not-planned). So a
bundled script invoked from a frontmatter hook must use `${CLAUDE_PLUGIN_ROOT}`
(e.g. `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/references/scripts/...`), which the
plugin reference documents as substituted in hook commands and exported to hook
processes; reserve `${CLAUDE_SKILL_DIR}` for the skill body and the procedures it
carries the value into. Before copying a sibling skill's
invocation convention — or declaring that sibling broken — verify the
substitution mechanism against the official skills and plugins docs; pinned
upstream engines vendored inside a skill are internal and resolve through the
same documented substitution, not a bare variable.

A skill that ships a hook entrypoint (a guard or gate script) must include an
integration test that drives the entrypoint's `main()` over the actual hook
payload for each event it claims to support (PreToolUse, Stop, and so on) and
asserts the documented decision or output. Unit tests on helper functions do not
prove the wired hook fires; cross-check the advertised hook events against the
events the entrypoint actually handles, because a recommended-default hook that
silently does nothing is worse than none.

To test whether a change-triggered gate's finding is caused by your edit rather
than pre-existing, the control run must still trip the gate's trigger. Removing
the change entirely (a stash or revert) also removes the trigger a dirty-file or
diff-scoped gate keys on, so it enumerates nothing and a clean result proves
nothing about the finding. Use a content-neutral control that still fires the
enumeration path — a whitespace-only edit to the same file at baseline content:
if the finding reproduces there, it is content-independent and pre-existing, not
caused by your change.

## Behavioral Evidence

Behavioral evidence records why a skill should keep its current trigger,
workflow, model-family split, or high-risk rejection gate. It is not a second
workflow and should not live in always-loaded context.

Use [skill-evaluation.md](skill-evaluation.md) for the JSONL field contracts and
source-hygiene template when creating or reviewing evaluation artifacts.

Store skill-scoped evidence under one-hop support files:

- `references/evals/trigger-cases.jsonl` for prompts that should and should
  not activate the skill.
- `references/evals/behavior-cases.jsonl` for task prompts, expected artifacts,
  required checks, forbidden behavior, and grading notes.
- `references/evals/model-pressure.md` when a model family or runtime extension
  exists because a generic core failed pressure scenarios.
- `references/source-grounding.md` when the skill extracts lessons from real
  traces, issues, reviews, runbooks, or correction history.

Every eval case should be synthetic or originally paraphrased unless a specific
source licence and quotation context have been reviewed. Link source material by
URL or local path, and follow the no-copy enumeration in
[skill-evaluation.md](skill-evaluation.md) "Source Hygiene"; do not paste
third-party material into the plugin bundle.

Trigger eval packs must contain both positive and negative cases. Negative
cases are not filler; they are the evidence that the skill does not steal work
from sibling skills or broad generic-agent tasks.

Behavior eval packs should test output and decision quality, not only whether
an answer was produced. A useful case names the expected artifacts, required
checks, forbidden behaviors, and a deterministic or rubric-based grader.

High-risk skills — security, audit, review, IP, or test-quality workflows —
need explicit rationalization gates. They should tell agents how to reject
plausible but unsupported findings, downgrade low-confidence evidence, and
avoid both false positives and false negatives.

## Model-Family Calibration

Use a generic core with specialized extensions. The generic core is the default
contract. Specialized model or runtime extensions are narrow overlays, not
parallel skills and not a reason to duplicate the core workflow.

First learn what works well for each target runtime and model tier. Then express
the instruction in generalized language when one shape meets the quality bar
across Claude Opus, Claude Sonnet, and Claude Haiku.

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

- Stronger reasoning models such as Opus and Sonnet can tolerate more evidence
  synthesis, but still need explicit boundaries, stop conditions, and
  verification commands.
- Faster or smaller models such as Haiku need fewer modes, tighter defaults,
  shorter references, concrete accepted/rejected target examples, and
  deterministic pre-checks for high-variance judgments.

Create a model-family extension only when the evidence says to split:

- The same eval prompt passes for one family or tier and fails for another.
- A smaller model loses actionability without extra rails.
- A metadata length or packaging limit forces different wording for a tier.
- A deterministic helper is needed for one model tier but not another.
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
- **Runtime metadata sync:** The Claude Code plugin manifest, marketplace entry,
  and matching subagent describe the same user-facing capability.
- **Release hygiene:** Version, manifest, marketplace, README, and install
  guidance changes travel together when a published surface changes.
- **IP/source hygiene:** Source material is linked, paraphrased in original
  wording, and only bundled when redistribution is allowed.

## Advisory Report Contract

`scripts/skill-architecture-report.sh` should validate everything that can be
validated deterministically or with bounded heuristics. Its Markdown report is
for an AI-agent reader; its JSON output is for thin skill workflows and future
automation. The report is not just a human lint log; it should tell the next
agent what to fix, why it matters, and how to verify the fix.

Each finding should include:

- Stable finding code.
- Severity.
- Target path.
- Evidence.
- Violated rule from this standard.
- Claude impact.
- Concrete next action.
- Verification or rerun command.

Reports should group targets by skill or repo surface so an agent can fix a
coherent area without mixing unrelated ownership. The final section must be
`Next Iteration` with the top 3-5 fixes, ordered by expected skill-quality lift.

Coverage reporting must be hard to game. Rule weights are derived from severity,
not chosen per catalog entry. Current fixed weights are `blocker=13`, `high=8`,
`medium=5`, and `low=3`. The report should show deterministic, heuristic,
manual-prompt, uncovered, and total weighted coverage, plus per-report-group
coverage with an `80%` minimum floor. Manual prompts count only when they are
explicit prompts an agent can run; uncovered items remain visible coverage debt.

The replacement claim is empirical, not catalog arithmetic. The report should
run a local gold ledger of skill-only findings and publish:

- ledger case count,
- skill-only gold finding count,
- tool-detected gold finding count,
- manual-only or missed finding count,
- automated replacement recall.

The minimum bar is 500 local gold-finding cases and `>=90%` automated
replacement recall. Report-engine tests should grow through a ledger of one
case per line, with contiguous IDs, ordered complexity, unique intent, a
`gold_issue` record, and duplicate fingerprint checks before execution.

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

Beyond this per-change loop, the repository runs a cross-session capture
loop. A Stop hook invokes the `lesson-capture` skill to distill one
generalizable (Layer-2, developing-the-skills) lesson from a session
and file it as a `lesson-candidate` GitHub™ issue (rendered by the pure
`scripts/lessons_issue.py`, hard secret-scanned at capture, deduped
by fingerprint, fail-open). Graduation is ordinary issue handling:
`issue-ops` (or the repo-internal `github-issue-lifecycle` overlay)
drives each issue to the Definition of Done embedded in its body, which
routes prose and policy lessons into the relevant docs (this standard,
`CLAUDE.md`, or a skill's own files) and deterministic lessons into a
`tests/skill_architecture_report_ledger.jsonl` (`SAC-T#####`) fixture when
the report engine already detects the smell. That capture → graduate
path is how a one-off correction becomes a standing rule that feeds
back into this document. Two further `Stop` hooks run first-party gates:
`stop-skill-architecture.sh` prompts the `skill_architecture_report.py` run
(trigger metadata + manifest/marketplace/agent sync), and `stop-lean-cost.sh`
runs lean-audit's per-use cost/fidelity guard. Both run as first-party
Stop hooks registered in `.claude/settings.json` and replaced the former
external-plugin `evaluate-skill` / `plugin-eval` hooks.

## Degradation Checks

Before finishing a skill change, inspect for these common regressions:

- The trigger became louder but less precise.
- The workflow added steps without changing decisions or failure detection.
- The skill now duplicates a sibling skill instead of delegating.
- Heavy reference material moved into always-loaded context.
- Plugin manifest, marketplace entry, and matching subagent metadata diverged.
- Deterministic checks were replaced by prose-only reminders.
- Output fields became optional without a compensating reason.
- Rerun guidance was removed or became ambiguous.
- Source anchors were copied as prose instead of linked and paraphrased.
- Feature utilization of a version-pinned or vendored upstream tool was judged
  against a stale local cache instead of the actually-pinned release.
- A deterministic gate hand-maintains a model of a fact an authority already
  owns — ignored paths, the repo file set, citation syntax — instead of
  deriving it, so the copy drifts (e.g. an ignore list that misses a worktree
  directory `.gitignore` already lists). Derive it from the authority (git,
  `.gitignore`) and keep a graceful fallback for non-git targets.
- A defect was resolved only by a local workaround — warming a runtime cache,
  editing installed state, hand-downloading a runtime — that repairs the current
  machine but not a fresh install. The durable fix must change the distributed
  artifact (launcher, manifest, skill, agent) so an empty-state install
  self-heals, verified against the cold/fresh-install path, not the warmed local
  machine.

## Source Anchors

Use these as anchors for current authoring and validation decisions. Link to
them; do not copy their prose into repo guidance.

- Anthropic Agent Skills overview:
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview>
- Claude Code skills:
  <https://code.claude.com/docs/en/skills>
- Anthropic Claude Skills best practices:
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- Claude Code plugin creation:
  <https://code.claude.com/docs/en/plugins>
- Claude Code plugin marketplace distribution:
  <https://code.claude.com/docs/en/plugin-marketplaces>
- Claude Code plugin reference:
  <https://code.claude.com/docs/en/plugins-reference>
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
