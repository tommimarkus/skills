# IP Hygiene Drive-By Scope

Load this when triage Q5 hits.

## Inline Fix Threshold

Fix a pre-existing issue inline only when all are true:

- the fix is no more than 20 extra lines, or one category of trademark-symbol additions;
- the fix stays within files already opened by the original edit;
- the fix is adding `®` / `™`, rewriting a near-verbatim paraphrase in the same section, replacing a bundled asset with a URL, adding a missing source citation, or correcting product/standard-mark grammar;
- the fix does not require new source verification beyond already-open authority.

If any condition fails, defer and flag.

## Source-And-Copy Rule

- If the current edit copies content with a pre-existing violation, fix the copy. Then fix the source if it is within the inline threshold; otherwise flag the source.
- If the current edit only references violating content, flag the referenced violation even if not fixed.

## Output Templates

- `fixed: <path:line> - <remedy summary>`
- `deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit`
