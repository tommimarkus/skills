# Isolated Review

Use only in Review when a reproducibility build is required. Original source,
policies, generated artifacts, and gallery are authoritative evidence and must
never be rebuilt in place.

1. Inspect and record original source validation, `dediren_verify` freshness,
   accessible-name/visual findings, and gallery state first. A stale or missing
   original remains a finding even if a copy later builds.
2. Use the loaded helper once in caller-owned persistent scratch (Claude:
   `${CLAUDE_SKILL_DIR}/references/scripts/review-copy.py`; Codex:
   `<skill-dir>/references/scripts/review-copy.py`):

   ```bash
   python3 <skill-dir>/references/scripts/review-copy.py prepare \
     --workspace-root /abs/workspace --package docs/architecture/feature.dediren/package.json \
     --destination /abs/persistent-review-copy
   ```

   `--workspace-root` and `--destination` are absolute; `--package` is relative
   to the workspace. Package model, policy, and output paths resolve relative to
   the package directory, while a model's fragment paths resolve relative to
   that model. Nested fragment declarations are unsupported, including an empty
   `fragments` key. The helper rejects absolute or escaping dependency/output
   paths, every symlink or nonregular input, duplicate or ancestor/descendant
   output paths, input/output and copied-file/output collisions, its reserved
   manifest path and its ancestors or descendants, an existing destination, and
   source/destination overlap.

   Before creating the destination, it binds the parsed package/model graph to
   source hashes and snapshots the package inventory plus existing or absent
   declared outputs and `gallery.html`. It then copies the package tree and all
   external models, policies, fragments, existing outputs, and gallery/theme
   files byte-for-byte without hard links. A final hash, inventory, and absence
   check detects source changes during copying. Its
   `.architecture-review-copy.json` records `architecture-review-copy-v1`, both
   absolute workspace roots, the relative package path, and each copied file's
   SHA-256 or `null` for an absent output. JSON stdout uses exit 0 for prepare or
   unchanged verification, 1 for a changed original (verify only), and 2 for an
   input, isolation, manifest, or I/O failure. It never promotes or removes a
   copy.
3. Validate every copied model with its semantic profile, then make at most one
   native package build using the copied workspace root and copied `package.json`.
   Extract requires this build capability when it generates artifacts. Prefer MCP;
   use the same resolved CLI only if MCP is unavailable. Do not retry or fall back
   after an uncertain artifact-writing call. Decode the package envelope and all
   view/export statuses through [self-check](self-check.md); do not interpret it
   as the unwrapped single-model result.
4. Any title-band/gallery post-render work targets only the copy. Preserve failed
   copy evidence at its disclosed persistent path. Do not tune source/layout or
   repair inputs during Review.
5. Recheck the original snapshot after the run:

   ```bash
   python3 <skill-dir>/references/scripts/review-copy.py verify-original \
     --manifest /abs/persistent-review-copy/.architecture-review-copy.json
   ```

   Verification checks the manifest identity and schema, every original file or
   recorded absence, and the complete original package inventory. A changed
   result invalidates snapshot comparison and is reported; malformed manifests
   are isolation failures. Neither result modifies either tree. Report original
   evidence, isolated build outcome, copy and manifest paths, and integrity
   outcome as distinct fields.
