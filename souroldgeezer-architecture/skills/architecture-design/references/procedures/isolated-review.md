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

   It accepts only workspace-relative package/dependency/output paths, rejects
   absolute or escaping paths, symlinks, nonregular files, nested fragments,
   input/output collisions, a destination collision, and source/destination
   overlap. It copies the package tree plus declared external models, policies,
   fragments, existing outputs, gallery/theme files byte-for-byte and writes
   `.architecture-review-copy.json`. JSON stdout: exit 0 success, 1 original
   changed (verify only), 2 input/isolation/I/O failure. It never promotes or
   removes a copy.
3. Validate every copied model with its semantic profile, then make at most one
   native package build using the copied workspace root and copied `package.json`.
   Extract requires this build capability when it generates artifacts. Prefer MCP;
   use the same resolved CLI only if MCP is unavailable. Do not retry or fall back
   after an uncertain artifact-writing call.
4. Any title-band/gallery post-render work targets only the copy. Preserve failed
   copy evidence at its disclosed persistent path. Do not tune source/layout or
   repair inputs during Review.
5. Recheck the original snapshot after the run:

   ```bash
   python3 <skill-dir>/references/scripts/review-copy.py verify-original \
     --manifest /abs/persistent-review-copy/.architecture-review-copy.json
   ```

   A changed result invalidates snapshot comparison and is reported; it does not
   modify either tree. Report original evidence, isolated build outcome, copy and
   manifest paths, and integrity outcome as distinct fields.
