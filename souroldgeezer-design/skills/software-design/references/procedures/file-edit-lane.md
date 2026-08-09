# File Edit Lane

Use this procedure only through the early-return selection in `SKILL.md`. It
handles a bounded content edit to a non-code text or structured-data file. It
does not make module, architecture, API, UI, infrastructure, security, or test
design decisions.

## Eligibility

Use the lane when all of these are true:

- The target is Markdown, plain text, JSON/JSONL, YAML, TOML, XML, CSV,
  INI/properties, or a similar non-code data/text format.
- The requested result is an explicit content operation such as add, remove,
  replace, rename a field, reorder, normalize, or format.
- The edit is bounded enough to validate directly.
- It neither changes source code nor requires a design tradeoff or a decision
  owned by a sibling skill.

An embedded program, template with executable semantics, schema/API redesign,
module or dependency choice, broad migration, or ambiguous destructive rewrite
does not qualify. Route it to the normal owning workflow or ask. File extension
alone never overrides the content and decision boundary.

## Selection precedence

Apply this order and stop at the first source that settles a safe operation:

1. Follow the user's explicit tool, operation, or output requirement.
2. Follow repository guidance. Where that guidance applies, prefer `jq` for
   JSON and Mike Farah `yq` for YAML frontmatter, YAML, TOML, and XML.
3. Reuse a fresh entry from the lane's advisory capability cache, when the host
   exposes one. User and repository requirements always override it; ignore a
   stale entry.
4. Perform cheap, bounded discovery of a plausible executable and its version
   or operation help. Do not crawl the machine or enumerate unrelated tools.
5. Consult bounded official documentation only when the operation is still
   unresolved and the environment permits it. Local repository configuration,
   the installed version, and observed behavior remain authoritative.
6. Fall back to `apply_patch` for a small literal edit or to the smallest
   task-scoped snippet that can express the operation safely. A cached,
   documented, or generated snippet is advisory: adapt it to the exact format
   and target, inspect its effect, and never treat its presence as permission to
   mutate.

Capability identifiers describe the format and operation, never a target path
or filename. For example, identify a capability as `json-sort` or `yaml-set`,
not by the file it may edit. Do not let a cache entry carry target-specific
authority or override current user/repository instructions.

When the lane loads and its cache helper is available, let that helper perform
opportunistic garbage collection once. Garbage-collection absence or failure is
not a reason to block the edit; continue without cached advice. Do not invent a
cache location, schema, freshness rule, or cleanup command when the helper does
not expose one.

## Edit and validate

Prefer a format-aware tool's native atomic or in-place operation when its
installed version supports the exact operation, it preserves required comments
and formatting, and its failure behavior cannot leave a partial target.
Otherwise use `apply_patch`. Keep any fallback snippet bounded to the named
input and output, avoid unrelated rewrites, and inspect the resulting diff.

Validate at the cheapest sufficient layers:

1. Re-read the edited region and confirm the requested content invariant.
2. Parse or lint structured formats with the repository-required or selected
   format-aware tool.
3. Run any focused repository validation that owns the edited artifact.
4. Inspect the diff for unintended reformatting, reordering, or adjacent edits.

If safe validation is unavailable, stop and say what evidence is missing. Do
not escalate into the software-design references merely to complete a file
operation.

## Narrow result

Report `lane: File Edit`, changed paths, the selected format-operation
capability and why it won precedence, validation evidence, and any limit. Do not
emit the normal software-design mode, layers, assimilation, architecture
pairing, findings, or footer.
