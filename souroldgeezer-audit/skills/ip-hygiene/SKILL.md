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
- older links: [references/ip-hygiene-reference.md](references/ip-hygiene-reference.md)

When changing this skill's trigger/workflow/gates/source/evals, inspect
`references/evals/` and [references/source-grounding.md](references/source-grounding.md).
Evals stay synthetic or originally paraphrased.

## Core Conformance

Apply audit core principles before judging:
- Conform to `../../docs/audit-reference/audit-craft.md` §2 (skepticism,
  criteria-citation, independence/self-review, false-positive discipline), §3
  (the full finding contract), and §5 (disclosure footer). This skill keeps
  its IP-issue finding shape and
  triage/in-depth modes in place of §4's Quick/Deep names or a smell catalog.
- Apply `../../docs/audit-reference/materiality.md` risk tier where an IP
  issue's consequence varies (e.g. published trademark vs internal note).

## Triage

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

Return exactly one of:

- `nothing to check`
- `checked: <bucket list>; no IP hygiene changes needed`
- `fixed: <path:line> - <remedy summary>; consequence: <effect if unaddressed>`
- `deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit`

For fixes, include the source authority or reference path used.

Every output ends with a disclosure footer per audit-craft.md §5: check
bucket(s) used · tool/MCP availability · reference path(s) · evidence limits ·
independence (independent | self-review | unknown) · assurance level (limited
for triage / reasonable for in-depth).

## Verification

After editing this skill or references, rerun
`scripts/skill-architecture-report.sh .` from the target repo root when
available.
