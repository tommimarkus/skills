# External validation handoff — Archi and schema findings

Use this procedure when the user supplies or reports validation evidence from
outside the skill, including Archi import errors, Archi Validate Model output,
`xmllint --schema` output, or another conformant ArchiMate tool's model
validation report.

This is an evidence handoff, not a mandatory extra gate for every run. When no
external validation report is supplied, disclose `not supplied/run` in the
footer and continue with the skill's source checks. When the user asks about
tool-reported findings but has not supplied the report, ask for the pasted or
exported findings before judging them.

## Triage

1. Record the report source, file path when known, total finding count, and
   whether the tool classified findings as errors, warnings, or info. Summarize
   long reports; do not paste a huge raw log into the response.
2. Deduplicate by model element, relationship, view, identifier, and message
   shape. Keep enough evidence to locate each distinct defect.
3. Map each distinct finding to the narrowest existing code:
   - invalid or unknown ArchiMate element, layer, or aspect -> `AD-1` / `AD-3`
   - invalid relationship or relationship endpoint pair -> `AD-2`
   - view node or connection abstract-type / missing `xsi:type` issue -> `AD-15`
   - metadata namespace issue -> `AD-16`
   - model child order, illegal model child, duplicate identifier, or import /
     schema structural issue -> `AD-17`
   - missing forward-only or lift-candidate marker -> `AD-14` / `AD-14-LC`
   - view purpose, viewpoint, process, or layout issue -> `AD-Q*`, `AD-B-*`,
     or `AD-L*`
   - current-code mismatch -> `AD-DR-*`
4. Use `AD-22` only when the tool finding is real validation evidence but the
   exact model smell is not yet represented or has not been triaged. `AD-22` is
   a stop sign to classify or repair the finding, not a replacement for a
   better `AD-*` code.

## Readiness impact

- Import or schema failures mean the artifact is not yet proven `model-valid`.
  Report `Artifact quality: not assessed (external validation blockers)` until
  those failures are fixed or mapped to resolved `AD-15` / `AD-16` / `AD-17`
  findings.
- Archi Validate Model findings on an imported model cap the affected view or
  artifact at `model-valid` until every error/warning is either fixed, mapped to
  a remaining `AD-*` blocker, or explicitly documented as an architect-owned
  intentional exception.
- Unmapped `AD-22` findings cap the artifact at `model-valid`; escalate to
  `block` when the external tool reported an error, import failure, or schema
  failure.

## Footer

Add an `External validation handoff` line to the footer:

```text
External validation handoff: not supplied/run
External validation handoff: Archi Validate Model supplied; findings 42 total, 31 mapped, 7 fixed, 4 unresolved, 0 unmapped
External validation handoff: xmllint --schema supplied; import/schema blockers 2 unresolved (AD-17)
```
