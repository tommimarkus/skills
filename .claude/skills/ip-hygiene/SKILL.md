---
name: ip-hygiene
description: Use when repo skill, agent, reference, manifest, marketplace/runtime metadata, or repo-guidance edits may touch third-party marks, copied source, licences, bundled assets, or existing IP issues.
---

# IP Hygiene

Repo-internal copyright, trademark, licence, and bundled-asset check for
skill-related or repo-guidance diffs. Not legal advice or a validator.

Inputs: current diff, touched paths, and referenced source/licence claims. If
missing, inspect the working tree or ask.

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
- **Confidence:** if authority, licence terms, or trademark policy are unclear
  and load-bearing, stop and ask instead of inventing a remedy.

## Check Buckets

Buckets: **copyright**, **trademark**, **licence/assets**, **drive-by**.
For drive-by, fix only small same-file issues with already-open authority;
otherwise use the deferred output. Fix copies introduced by the current edit.

## Stop Conditions

Stop and ask before finishing when:

- vendor policy, licence, or authority is ambiguous and load-bearing;
- asset redistribution terms are unclear or restrictive;
- a remedy would remove a load-bearing reference;
- the issue is outside copyright, trademark, licence, or bundled-asset hygiene.

## Output Contract

Return exactly one of:

- `nothing to check`
- `checked: <bucket list>; no IP hygiene changes needed`
- `fixed: <path:line> - <remedy summary>`
- `deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit`

For fixes, include the source authority or reference path used.

## Verification

After editing this skill or references, rerun
`scripts/skill-architecture-report.sh .`.
