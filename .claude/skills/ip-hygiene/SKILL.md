---
name: ip-hygiene
description: Use when changing skill, agent, bundled reference, extension, manifest, marketplace, Codex metadata, or repo guidance content in this repository and the edit may touch third-party marks, copyrighted source material, licences, bundled assets, or pre-existing IP issues.
---

# IP Hygiene

## Purpose

Apply this repo's copyright, trademark, and licence discipline before finishing
skill-related or repo-guidance edits. This is a repo-internal authoring check,
not legal advice and not a validator.

Use the detailed reference at
[references/ip-hygiene-reference.md](references/ip-hygiene-reference.md) when
any triage question hits, when a remedy is unclear, or when source authority is
needed for a consequential change.

## Inputs

Inspect the current diff, the touched files, and any source material or licence
claims referenced by the edit. When the diff is unavailable, ask for the
changed paths or inspect the working tree before triage.

## Applies To

Invoke for create, modify, rename, move, or delete operations touching:

- `souroldgeezer-*/skills/<name>/SKILL.md`, `extensions/`, `references/`,
  `fixtures/`, `templates/`, or skill-local scripts.
- `souroldgeezer-*/agents/<name>.md`.
- `souroldgeezer-*/docs/*-reference/**`.
- `souroldgeezer-*/.claude-plugin/plugin.json`,
  `souroldgeezer-*/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, and any future marketplace manifest.
- `souroldgeezer-*/skills/<name>/agents/openai.yaml`.
- `.codex/agents/*.toml`.
- `.claude/skills/<name>/**`.
- `CLAUDE.md`, `AGENTS.md`, and `README.md` sections that describe these
  surfaces.

Do not invoke for pure build-only or helper-script edits that do not touch the
surfaces above and do not copy, describe, bundle, or expose third-party content.

## Public-Visible Surfaces

Apply trademark first-and-subsequent-significant mention discipline to files
rendered for humans or exposed through agent/skill/plugin pickers:

- `README.md`, `AGENTS.md`, and `CLAUDE.md`.
- `.claude-plugin/marketplace.json`.
- `<plugin>/.claude-plugin/plugin.json`.
- `<plugin>/.codex-plugin/plugin.json`.
- `<plugin>/skills/<name>/agents/openai.yaml`.
- `.codex/agents/*.toml` descriptions.
- Frontmatter `description:` fields of `SKILL.md` and `agents/*.md`.

Internal reference bodies, extension prose, procedures, and smell catalogs do
not require a mark on every mention. Use descriptive naming consistently.

## Triage

Answer these before finishing the edit:

1. **Public-surface trademark.** Does the diff mention a third-party registered
   trademark, product name, or named standard on a public-visible surface?
2. **Copyrighted text.** Does the diff quote, closely paraphrase, summarize, or
   restructure source prose from a specification, standard, documentation page,
   textbook, article, or published reference?
3. **Copyrighted non-text.** Does the diff include or modify code samples,
   configuration fragments, sample files, diagrams, figures, tables, fixtures,
   or examples from third-party material?
4. **Third-party asset or schema.** Does the diff bundle or point at a
   third-party schema, spec file, binary, logo, icon set, SDK, or sample file?
5. **Drive-by propagation.** Does the touched file contain pre-existing content
   that would hit questions 1-4, especially content copied or linked by this
   edit?

If all answers are no, exit with `nothing to check`.

If any answer is yes, read
[references/ip-hygiene-reference.md](references/ip-hygiene-reference.md) and run
only the relevant check buckets below.

## Check Buckets

### Copyright

- Do not reproduce third-party prose, examples, fixtures, code, diagrams,
  tables, schemas, or sample files verbatim or near-verbatim unless the source
  licence and quotation context allow it.
- Prefer original paraphrase with an in-prose source citation when a specific
  source influenced the wording.
- Treat structured spec tables and enumerations as protected structure in EU
  contexts; do not copy row order, grouping, and column design as a dataset.
- Reference restrictive third-party assets by canonical URL instead of bundling.
- Bundle only permissively licensed assets after verifying the specific file
  licence and preserving required attribution.

### Trademark

- On public-visible surfaces, add `®` or `™` on first and subsequent significant
  uses of registered or claimed marks.
- Use product and standard marks adjectivally: for example, "ArchiMate®
  modeling language" or "Microsoft Azure service", not possessive or pluralized
  product-mark forms.
- Avoid wording that implies endorsement, certification, commercial connection,
  denigration, unfair advantage, imitation, or replica status.
- Do not add per-mark attribution blocks unless a specific holder policy makes
  that a condition for the use.
- Do not remove load-bearing nominative references merely to reduce risk.

### Licence

- Mere descriptive mention of a library, tool, product, or standard does not
  import its licence into this repo.
- Bundled third-party code or assets keep their upstream licence. Do not bundle
  GPL-family, AGPL, LGPL, or share-alike content into this MIT-licensed repo
  without an explicit compatible distribution decision.
- Do not imply this repo's MIT licence grants rights in third-party standards,
  schemas, docs, or software.
- Treat AI-authored content as covered by the repo's contribution convention,
  while preserving source hygiene for any third-party material it used.

## Remedies

Choose the remedy by concern type:

| Concern | Required remedy |
|---|---|
| Verbatim or near-verbatim copyright match | Paraphrase into original expression with source citation |
| Trademark first/subsequent significant mention missing `®` or `™` | Add the symbol |
| Bundled third-party asset under a non-permissive or unclear licence | Replace with canonical URL reference |
| Endorsement implication or product-mark grammar issue | Reword to descriptive nominative use |
| No safe repair and reference is non-load-bearing | Remove with written justification |

When using the last-resort removal remedy, state why the first four remedies do
not apply and why removing the reference does not break the skill.

## Drive-By Scope

Fix incidentally observed pre-existing issues inline only when the change is
small, same-file, and directly supported by already-open source authority.
Otherwise flag the observation without expanding scope.

Always fix copies introduced by the current edit, even if the source issue must
be deferred.

## Stop Conditions

Stop and ask the user before finishing when:

- A vendor policy, licence, or legal authority is ambiguous and load-bearing.
- A user asks to bundle a third-party asset whose redistribution terms are
  unclear or restrictive.
- A remedy would remove a load-bearing reference from the skill.
- The issue falls outside copyright, trademark, licence, or bundled-asset
  hygiene: patents, privacy, export control, trade secrets, right of publicity,
  defamation, contracts, or jurisdiction-specific legal advice.

## Output Contract

Return one of:

- `nothing to check` when all triage answers are no.
- `checked: <bucket list>; no IP hygiene changes needed` when triage hits but
  no remedy is required.
- `fixed: <path:line> - <remedy summary>` for inline fixes.
- `deferred drive-by observation at <path:line> - <issue>; recommend separate
  retroactive audit` when an observed pre-existing issue exceeds current scope.

When a fix is made, include the source authority or reference path used to close
the concern.

## Verification

After editing this skill or its reference, rerun this validation command:

```bash
scripts/skill-architecture-report.sh .
```
