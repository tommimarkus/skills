# External Validation Handoff

Use for optional OEF export or supplied downstream importer/schema validation.

## Rules

1. Normal Build/Extract/Review/Lookup does not require export.
2. Requested export without `export-policy.json`: `ARCH-E-3`, blocked.
3. `dediren export` failure: `ARCH-E-1`.
4. Supplied downstream finding: map to `ARCH-E-2` or narrower model/view/render
   code when one fits.
5. Footer: supplied, mapped, unresolved, and unmapped counts.

OEF is compatibility output. Fix package source or export policy first, then
recreate the export.
