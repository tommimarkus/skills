# API Architecture Pairing

Load when a paired ArchiMate dediren package exists or the user asks to update
architecture after API work.

Canonical package path: `docs/architecture/<feature>.dediren/`.

## Review Or Extract Rules

- Review mode: auto-detect a matching package. If exactly one package matches,
  dispatch to `architecture-design` Review for drift detection and include
  `ARCH-X-*` findings after the API findings. If no package exists, report
  `Architecture pairing: none`. If multiple packages match, ask for the feature
  slug.
- Extract/Build mode: update architecture only when the user opts in with words
  such as "also update the architecture model" or supplies the package path.
- API runtime projects become Application Components. Routes become Application
  Interfaces. Runtime/data/storage extensions may contribute Technology Layer
  relationships only when source evidence supports them.
- `api-design` never edits ArchiMate semantics directly. It dispatches to
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
