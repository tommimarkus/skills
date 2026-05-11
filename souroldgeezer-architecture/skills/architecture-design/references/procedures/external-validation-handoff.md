# External Validation Handoff

Use when the user requests optional OEF export or supplies downstream importer,
schema, or conformant-tool validation evidence.

## Rules

1. Do not require export for normal Build, Extract, Review, or Lookup.
2. If export is requested and `export-policy.json` is missing, report
   `ARCH-E-3` and set export readiness to blocked.
3. If `dediren export` fails, report `ARCH-E-1`.
4. If the user supplies downstream validation evidence for the exported file,
   map each unresolved finding to `ARCH-E-2` or a narrower model/view/render
   finding when one fits.
5. Report total supplied findings, mapped findings, unresolved findings, and
   unmapped findings in the footer.

OEF is compatibility output. Fix package source or export policy first, then
recreate the export.
