# IP Hygiene Trademark Checks

Load this when triage Q1 hits.

## Public-Visible Surfaces

Treat these as public-visible unless target repo guidance says otherwise:
`README.md`, `AGENTS.md`, `CLAUDE.md`, marketplace manifests, plugin manifests,
and frontmatter `description:` fields.

## Convention

Apply the convention resolved by `SKILL.md`. If the target repo has no
convention, use the default convention: descriptive nominative references, no
default per-mark attribution block, and `®` / `™` on significant
public-visible uses when a mark is registered or claimed and the symbol is
known.

## Check

- Add or preserve mark symbols according to the resolved project convention.
- Mid-paragraph repeats in the same file may omit the symbol unless project
  guidance requires every significant mention.
- Internal references, procedures, extensions, and smell catalogs do not need
  symbols on every mention.
- Use product and standard marks adjectivally: product/standard mark plus noun.
  Do not pluralize or use product/standard marks possessively.
- Corporate-name possessives are allowed when referring to the company, not a
  product or standard.
- Avoid wording that implies endorsement, certification, commercial connection,
  unfair advantage, denigration, or imitation.
- Do not bundle or inline logos, brand kits, or icon sets.
- Do not add per-mark attribution blocks unless a specific holder policy or
  project convention makes attribution a condition.
- Do not remove load-bearing nominative references merely to reduce risk.

## Remedies

- Missing symbol under the resolved convention: add `®` or `™`.
- Product/standard grammar problem: rewrite to descriptive nominative use.
- Endorsement, affiliation, denigration, unfair advantage, or imitation risk:
  reword or stop if no safe wording preserves the skill.
- Load-bearing uncertainty about holder policy or project convention: stop and
  ask.

## Source Anchors

Use `authority-index.md` for: EUTMR Art 14, Lanham Act, New Kids, Welles,
Gillette, BMW v Deenik, The Open Group trademarks, Microsoft trademark
guidelines, OMG, W3C, GitHub, IETF.
