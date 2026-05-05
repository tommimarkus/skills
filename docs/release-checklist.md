# Release Checklist

Use this before publishing a release or bumping a plugin version.

## Checklist

- Confirm the shared marketplace still points at existing plugin paths.
- Confirm each plugin has matching Claude and Codex manifests.
- Confirm `name`, `version`, and `description` are synchronized across the
  marketplace entry and both manifests.
- Confirm the plugin docs still link every shipped skill.
- Confirm `README.md` still acts as the product map.
- Run the validation commands listed in `README.md`.
- Inspect `git diff --check` for whitespace errors.
- Update `docs/refactor/fragmentation-execplan.md` if the release changes the
  documented public surface.

## Versioning guidance

Use semver at the plugin level.

- Patch: documentation-only edits, link fixes, or other changes that do not
  alter shipped skill behavior or installed-plugin update checks.
- Minor: additive, backwards-compatible changes to the public surface, such as
  a new skill, a new docs page, or a new non-breaking validation path.
- Major: backwards-incompatible changes such as removing or renaming a skill,
  changing a plugin name, moving a canonical reference path, or changing an
  output contract.

When a plugin version changes, update the matching Claude manifest, Codex
manifest, and marketplace entry in the same change.
