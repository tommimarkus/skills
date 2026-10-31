# Release Checklist

Use this before publishing a release. Local version preparation follows the
contributor guide's proportionate checks; it does not itself authorize publication. Start with
[the contributor guide](contributing.md) for worktree and validation ownership,
and use the [maintenance procedures](maintenance-procedures.md) for rare
operational changes.

## Checklist

### Check packaging and versions

- Confirm the shared Claude marketplace still points at existing plugin paths.
- Confirm each plugin retains its Claude `.claude-plugin/plugin.json` manifest
  and the Claude marketplace entry keeps the same `name` and `description`.
- Confirm the additive Codex marketplace exposes the same plugin set, order, and
  local paths, and each plugin has `.codex-plugin/plugin.json`.
- Confirm the Claude and Codex manifests express the same semantic version:
  padded `YYYY.0M.MICRO` in Claude and normalized `YYYY.M.MICRO` in Codex.
  Keep `.antigravity-plugin/plugin.json` and any native Copilot / root `plugin.json`
  normalized version aligned with Codex. Neither marketplace may carry a `version` key.
- Validate every Codex plugin with the current first-party plugin validator when
  the installed CLI exposes one.

### Verify the candidate

- From the exact clean candidate commit, run `python3 -B
  scripts/publication_check.py --repo-root . record` as part of the integration
  that stamps the version, not later at push time. It runs the complete
  ordered [contributor validation](contributing.md#validate-the-change) with
  the host smoke unconditionally, without `--changed-since`, and records the
  commit/tree-bound result. Require all five Claude/Codex isolated installs,
  all 16 shared public skills, the isolated Copilot architecture install,
  Claude component/strict validation, all three external-Dediren adapter
  handshakes, and unchanged normal plugin/config profiles. Record an
  unavailable standalone Codex validator as a skip.
- Confirm the plugin docs still link every shipped skill.
- Confirm `README.md` still acts as the product map.
- Inspect `git diff --check` for whitespace errors.
- Review the README and the relevant contributor guide when the release changes
  the documented public surface.
- Confirm security-sensitive release notes identify the affected surface,
  fixed plugin version, and user update action without disclosing an unresolved
  private report. Notify the reporter through the private advisory when one
  exists.

After the fixed one-commit version-only follow-up, run `python3 -B
scripts/publication_check.py --repo-root . record --version-followup`. The
optional pre-push hook accepts only the exact recorded candidate or follow-up;
it is a local, bypassable control and does not replace review or remote
enforcement.

## Versioning guidance

Keep the established Claude/README CalVer spelling `YYYY.0M.MICRO` as the
release authority. Derive Codex and any native Copilot manifest's strict-SemVer
spelling `YYYY.M.MICRO` from it.

- Patch: documentation-only edits, link fixes, or other changes that do not
  alter shipped skill behavior or installed-plugin update checks.
- Minor: additive, backwards-compatible changes to the public surface, such as
  a new skill, a new docs page, or a new non-breaking validation path.
- Major: backwards-incompatible changes such as removing or renaming a skill,
  changing a plugin name, moving a canonical reference path, or changing an
  output contract.

Feature branches carry no release increment. At integration on `main`, compute
the next stamp with `scripts/version_stamp.py`, then update the Claude manifest,
Codex manifest, Antigravity manifest, any native Copilot manifest, and matching
README cell together.
Do not add a version to a marketplace entry.
