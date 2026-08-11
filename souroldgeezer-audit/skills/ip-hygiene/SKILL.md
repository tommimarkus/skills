---
name: ip-hygiene
description: Use when skill, agent, bundled reference, manifest, marketplace/runtime metadata, plugin guidance, or bundled asset edits may touch third-party marks, copied source, licences, assets, or existing IP/source hygiene issues. Focused on plugin and skill publication surfaces; not general legal advice.
---

# IP Hygiene

Public copyright, trademark, licence, and bundled-asset hygiene check for
plugin and skill publication surfaces. This is not legal advice or a validator.

Inputs: current diff, touched paths, target repo guidance, and referenced
source/licence claims. If inputs are missing, inspect the working tree or ask.

Resolve project conventions in this order:

1. explicit user instruction for the current task;
2. target repo guidance such as `AGENTS.md`, `CLAUDE.md`, `README.md`, or a
   project policy file;
3. this skill's default convention.

Default convention: descriptive nominative references, no default per-mark
attribution block, and mark-symbol handling driven by public-visible context.
Treat this as a fallback project convention, not a universal legal rule.

Legal grounding is EU-first (see
[references/fence-posts.md](references/fence-posts.md)); remedies are chosen
to hold under stricter regimes, and non-EU authority is persuasive-only.

## Scope

Use this skill for skill/plugin publication surfaces: skills, agents,
per-skill metadata, bundled references, extensions, fixtures, templates,
scripts, assets, plugin manifests, marketplace/runtime metadata, and repo
guidance sections that describe those surfaces.

General repo-wide IP hygiene is future scope. If the task is unrelated to
skill/plugin publication surfaces, say the skill is out of scope and stop.

Load only hit buckets:

- Q1 public marks: [references/trademark.md](references/trademark.md)
- Q2/Q3 copyright: [references/copyright.md](references/copyright.md)
- Q4 assets/licences: [references/licence-assets.md](references/licence-assets.md)
- Q5 drive-by: [references/drive-by.md](references/drive-by.md)
- source authority: [references/authority-index.md](references/authority-index.md)
- policy boundary changes: [references/fence-posts.md](references/fence-posts.md)
- following a pre-split citation that targets `ip-hygiene-reference.md`: [references/ip-hygiene-reference.md](references/ip-hygiene-reference.md)

When changing this skill's trigger/workflow/gates/source/evals, inspect
`references/evals/` (including `references/evals/accuracy-corpus/`) and [references/source-grounding.md](references/source-grounding.md).
Evals stay synthetic or originally paraphrased.

## Core Conformance

Apply audit core principles before judging:
- Conform to [`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §2 (skepticism,
  criteria-citation, independence/self-review, false-positive discipline), §3
  (the full finding contract), and §5 (disclosure footer). This skill keeps
  its IP-issue finding shape and
  triage/in-depth modes in place of §4's Quick/Deep names or a smell catalog.
- Apply [`../../docs/audit-reference/materiality.md`](../../docs/audit-reference/materiality.md) risk tier where an IP
  issue's consequence varies (e.g. published trademark vs internal note).

## Triage

First, when a change set or target paths are available, run the objective
pre-filter to surface bundled-asset / schema / vendored candidates:

`${CLAUDE_SKILL_DIR}/references/scripts/ip-prefilter.sh --format text -- <touched paths>`

Claude Code substitutes `${CLAUDE_SKILL_DIR}` with this skill's installed path.
In Codex, replace it with the absolute `<skill-dir>` reported for this loaded
`SKILL.md`. A bare relative path would not resolve from the target repo's
working directory.

Execute the resolved command without loading its source. Inspect
`references/scripts/` only when maintaining the pre-filter implementation or
its packaged path wiring; ordinary triage uses the command above as a black box.

It scans only objective filesystem facts (Q3/Q4 candidates). Use its hits as
evidence when answering Q3 and Q4. It does NOT answer any question: an empty
result is NOT a clean bill of health — copied prose (Q2), inline code samples
(Q3), and public marks (Q1) are out of its reach, so still answer all five
questions by judgment. Hits raise candidates; they never replace the triage.

Before finishing, answer:

1. **Public-surface trademark:** third-party mark/product/standard on a
   public-visible surface?
2. **Copyrighted text:** quoted, close-paraphrased, summarized, or restructured
   source prose?
3. **Copyrighted non-text:** third-party code/config/sample/figure/table/fixture?
4. **Third-party asset/schema:** bundled or linked schema/spec/binary/logo/SDK/sample?
5. **Drive-by propagation:** touched file has pre-existing content that hits
   1-4, especially copied or linked by this edit?

All no: exit with `nothing to check`. Any yes: load only the relevant bucket.

### Triage Gate

Triage additionally emits exactly one `triage gate: <fail | not-evaluated |
pass-limited>` line, after any finding or `stopped:` line and before the
disclosure footer. Do not emit this line in in-depth mode.

Use the shared precedence in `audit-craft.md` §4a, with these IP-specific
blockers. Set `fail` when substantiated in-scope evidence confirms any of:

- misleading mark claims or branding;
- unauthorized logos or endorsement implications;
- unlicensed copied expression;
- missing operative copyright or licence notices; or
- incompatible or restricted bundled content.

Set `not-evaluated` when required evidence cannot rule out those blockers. In
particular, unclear source authority, holder policy, or redistribution terms
are `not-evaluated` unless a confirmed blocker already makes the gate `fail`.
Ordinary mark-symbol, grammar, or optional-attribution convention issues are
nonblocking unless loaded authority makes them distribution-critical: preserve
their underlying `warn` or `info` severity, but keep the gate `pass-limited`.
A remediated blocker requires a clean triage rerun before `pass-limited`.

## In-Depth

Run in-depth instead of change-scoped triage when the user asks for it by
name (in-depth, full, whole-surface), when repo guidance gates a breaking or
additive change on an in-depth run, or when the requested scope is a whole
plugin or publication surface rather than a change set. If the mode is
ambiguous, ask.

1. Enumerate the in-scope publication surfaces: skills, agents, references,
   extensions, fixtures, templates, scripts, assets, manifests,
   marketplace/runtime metadata, and guidance sections describing them.
2. Run the objective pre-filter over the full enumeration.
3. Answer the five triage questions per surface, loading every hit bucket.
4. Tier each finding per the materiality reference (Core Conformance); when
   enumeration exceeds budget, sample and project per audit-craft §6 and
   disclose the sampling basis.
5. Emit one Output Contract line per finding, then the closing rollup line
   `in-depth verdict: <clean | N issue(s): <bucket counts>>`, and the
   disclosure footer at reasonable assurance.

## Rationalization Gates

Before reporting an issue:

- **False positive:** do not flag descriptive internal product, library, tool,
  or standard mentions unless they copy expression, bundle material, or affect a
  public-visible surface.
- **False negative / unsupported evidence:** do not downgrade copied prose or
  examples, bundled third-party assets, unclear redistribution terms, or
  endorsement-like wording because the reference is useful.
- **Confidence:** if authority, licence terms, trademark policy, or target repo
  convention is unclear and load-bearing, stop and ask instead of inventing a
  remedy.

## Check Buckets

Buckets: **copyright**, **trademark**, **licence/assets**, **drive-by**.
For drive-by, fix only small same-file issues with already-open authority;
otherwise use the deferred output. Fix copies introduced by the current edit.

## Stop Conditions

Stop and ask before finishing when:

- vendor policy, licence, source authority, or target repo convention is
  ambiguous and load-bearing;
- asset redistribution terms are unclear or restrictive;
- a remedy would remove a load-bearing reference;
- the issue is outside copyright, trademark, licence, or bundled-asset hygiene;
- the task is outside skill/plugin publication surfaces.

## Output Contract

Emit one line per finding; a single run may emit several. A run with no
findings emits `nothing to check` (no triage hits) or
`checked: <bucket list>; no IP hygiene changes needed`. Finding lines use one
of:

- `fixed: <path:line> - <remedy summary> [<severity>|<risk tier>]; consequence: <effect if unaddressed>`
- `deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit [<severity>|<risk tier>]`
- `stopped: <the load-bearing question>` (a Stop Condition fired; ask
  instead of inventing a remedy)

Severity is block | warn | info (audit-craft §3); risk tier is high |
medium | low | unknown (materiality). In-depth runs append the rollup line
from the In-Depth section. Triage runs append the `triage gate:` line from
Triage Gate after their result or finding lines; in-depth runs do not.

For fixes, include the source authority or reference path used.

Every output ends with a disclosure footer per audit-craft.md §5: check
bucket(s) used · tool/MCP availability · reference path(s) · evidence limits
(for change-scoped triage, name the scope boundary: touched paths + drive-by
neighbors examined; untouched files not swept) · independence (independent |
self-review | unknown) · assurance level (limited for triage / reasonable for
in-depth).

## Verification

After editing this skill or references in the marketplace source repo, rerun
its `scripts/skill-architecture-report.sh .` from the repo root when available
(repo tooling, not bundled with the installed plugin).

When editing `references/authority-index.md`, spot-check that the affected
external links still resolve to the cited documents before finishing.
