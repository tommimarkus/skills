# External Validation Handoff

Use for optional OEF/XMI export or supplied downstream importer/schema
validation.

## Rules

1. Normal Build/Extract/Review/Lookup does not require export.
2. Requested export without `export-policy.json`: `ARCH-E-3`, blocked.
3. `dediren export` failure: `ARCH-E-1`.
4. Supplied downstream finding: map to `ARCH-E-2` or narrower model/view/render
   code when one fits.
5. Footer: supplied, mapped, unresolved, and unmapped counts.

OEF and XMI are compatibility output. Fix package source or export policy first,
then recreate the export.

## Required fidelity disclosures

An `ok` export envelope proves the command ran, not that the model survived.
Before claiming export readiness, compare the export content against package
source and disclose coverage in the footer's `Export readiness` qualifier
(see [output-format](../output-format.md)):

1. **View coverage (OEF).** One export policy binds exactly one
   `view_identifier`; a multi-view package exports one diagram per run.
   Enumerate exported vs. omitted views (e.g. `OEF ready (1 of 2 views)`).
2. **Property loss (OEF).** Node/relationship `properties` — including
   evidence labels such as `candidate-from-source` — do not survive export.
   When candidate or evidence-labeled content is exported, disclose that the
   downstream tool shows it indistinguishably from confirmed architecture.
3. **Content coverage (XMI).** Verify which authored kinds appear in the
   export; on the release-resolved runtime (verified on 2026.07.0) only class
   structure survives — associations, sequence interactions, and deployment
   content are omitted with an `ok` envelope, and multiplicities/attribute
   types are serialized non-canonically. Qualify as e.g. `XMI ready (classes
   only)` and report the gap under `Dediren tool issues`.
4. **Schema validation.** Diagram-bearing OEF validates against the Open Group
   `archimate3_Diagram.xsd` (its embedded `schemaLocation` names
   `archimate3_Model.xsd`, which rejects `<views>`); disclose which schema the
   evidence used. In restricted environments pre-fetch XSDs and pass offline
   paths per [self-check](self-check.md) envelope/schema guidance.
