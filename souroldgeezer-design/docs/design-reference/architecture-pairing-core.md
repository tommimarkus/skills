# Architecture Pairing Core

Shared architecture-pairing mechanics for the design skills (`api-design`,
`software-design`; siblings may adopt the same contract). Each consuming skill's
`references/procedures/architecture-pairing.md` cites this file and adds only
its own load condition, element mappings, and any dispatch narrowing.

Canonical package path: `docs/architecture/<feature>.dediren/`.

## Review Or Extract Rules

- Review mode: auto-detect a matching package. If exactly one package matches,
  dispatch to `architecture-design` Review for drift detection and include
  `ARCH-X-*` findings after the skill's own findings; a skill's pairing
  procedure may narrow this dispatch to changes a lifted view could reflect.
  If no package exists, report `Architecture pairing: none`. If multiple
  packages match, ask for the feature slug.
- Extract/Build mode: update architecture only when the user opts in with words
  such as "also update the architecture model" or supplies the package path.
- Element mappings are per skill: each consuming skill's pairing procedure
  defines how its domain concepts become ArchiMate elements and relationships,
  contributed only when source evidence supports them.
- The design skill never edits ArchiMate semantics directly. It dispatches to
  `architecture-design` and reports the result.

## Footer Field

Use one of:

```text
Architecture pairing: drift-check clean
Architecture pairing: <n> drift findings
Architecture pairing: extract refreshed
Architecture pairing: none
Architecture pairing: ambiguous package path - asked user
```
