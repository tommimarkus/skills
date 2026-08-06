# Release Checklist

Use this before publishing a release or bumping a plugin version.

## Checklist

- Confirm the shared Claude marketplace still points at existing plugin paths.
- Confirm each plugin retains its Claude `.claude-plugin/plugin.json` manifest
  and the Claude marketplace entry keeps the same `name` and `description`.
- Confirm the additive Codex marketplace exposes the same plugin set, order, and
  local paths, and each plugin has `.codex-plugin/plugin.json`.
- Confirm both manifests express the same semantic version: padded
  `YYYY.0M.MICRO` in Claude and normalized `YYYY.M.MICRO` in Codex. Neither
  marketplace may carry a `version` key.
- Validate every Codex plugin with the current first-party plugin validator when
  the installed CLI exposes one.
- Run `scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation .`
  with both CLIs available; require all five isolated installs, all 15 shared
  skills, Claude component/strict validation, both Dediren adapter handshakes,
  and unchanged normal plugin/config profiles. Record an unavailable standalone
  Codex validator as a skip.
- Confirm the plugin docs still link every shipped skill.
- Confirm `README.md` still acts as the product map.
- Run the validation commands listed in `README.md`.
- Inspect `git diff --check` for whitespace errors.
- Update `docs/refactor/fragmentation-execplan.md` if the release changes the
  documented public surface.

## Versioning guidance

Keep the established Claude/README CalVer spelling `YYYY.0M.MICRO` as the
release authority. Derive Codex's strict-SemVer spelling `YYYY.M.MICRO` from it.

- Patch: documentation-only edits, link fixes, or other changes that do not
  alter shipped skill behavior or installed-plugin update checks.
- Minor: additive, backwards-compatible changes to the public surface, such as
  a new skill, a new docs page, or a new non-breaking validation path.
- Major: backwards-incompatible changes such as removing or renaming a skill,
  changing a plugin name, moving a canonical reference path, or changing an
  output contract.

Feature branches carry no release increment. At integration on `main`, compute
the next stamp with `scripts/version_stamp.py`, then update the Claude manifest,
Codex manifest, and matching README cell together. Do not add a version to a
marketplace entry.
