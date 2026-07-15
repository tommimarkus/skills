# External Validation Handoff

Use for optional OEF/XMI export or supplied downstream importer/schema
validation.

## Rules

1. Normal Build/Extract/Review/Lookup does not require export.
2. Requested export without `export-policy.json`: `ARCH-E-3`, blocked.
3. `dediren_build` export-lane (`oef_policy` / `xmi_policy`) failure: `ARCH-E-1`.
4. Supplied downstream finding: map to `ARCH-E-2` or narrower model/view/render
   code when one fits.
5. Footer: supplied, mapped, unresolved, and unmapped counts.

OEF and XMI are compatibility output. Fix package source or export policy first,
then recreate the export.

## Required fidelity disclosures

An `ok` export envelope proves the command ran, not that the whole model
survived: the pinned runtime keeps `status: ok` and declares any omission
through `info` diagnostics. Read `.diagnostics[]`, compare the export content
against package source, and disclose coverage in the footer's `Export readiness`
qualifier (see [output-format](../output-format.md)):

1. **View coverage (OEF).** One export policy binds exactly one
   `view_identifier`, so each run exports a single view. When the source
   declares more views than the exported one, the runtime declares the omission
   with the `info` diagnostic `DEDIREN_OEF_VIEWS_OMITTED` (naming the omitted
   view ids and count) while the envelope `status` stays `ok` (dediren
   2026.07.1+); read `.diagnostics[]` and enumerate exported vs. omitted views
   (e.g. `OEF ready (1 of 2 views)`). Export the other views to represent them.
2. **Property preservation (OEF).** Node/relationship `properties` — including
   evidence labels such as `candidate-from-source` — are preserved through
   export as OEF `<propertyDefinitions>` plus per-element `<property>`/`<value>`
   (dediren 2026.07.1+; earlier runtimes dropped them silently). Because a
   downstream ArchiMate tool renders them as generic properties with no
   candidate/confirmed distinction, when candidate or evidence-labeled content
   is exported disclose that the downstream tool shows it indistinguishably from
   confirmed architecture.
3. **Content coverage (XMI).** The `uml-xmi` export represents the single
   laid-out view's class-diagram structure — classes, associations, and
   attributes with canonical UML 2.5.1 serialization (multiplicities as owned
   `lowerValue`/`upperValue`, attribute types resolved to `uml:PrimitiveType`
   or in-scope classifiers) (dediren 2026.07.1+). Content outside the exported
   view — other views' elements/relationships and sequence/deployment/activity
   dynamic content — is declared, not dropped silently, with `info` diagnostics
   `DEDIREN_XMI_ELEMENTS_OMITTED` / `DEDIREN_XMI_RELATIONSHIPS_OMITTED` while the
   envelope `status` stays `ok`; read `.diagnostics[]`, qualify as e.g. `XMI
   ready (classes only)`, and report the gap under `Dediren tool issues`.
4. **Schema validation.** Disclose which schema the evidence used — and, for
   XMI, which validation level was reached.
   - *OEF (ArchiMate).* The OEF document always carries a `<views>`/`<diagrams>`
     element, so it declares and validates against the Open Group
     `archimate3_Diagram.xsd`; its embedded `schemaLocation` names that diagram
     schema (dediren 2026.07.1+; earlier runtimes named the model-only
     `archimate3_Model.xsd`, which rejects `<views>`).
   - *XMI (UML).* Validation of the `uml-xmi` output is partial (`uml-xmi
     capabilities` → `schema_validation.kind: omg-xmi-xsd-partial`): pointing
     `DEDIREN_XMI_SCHEMA_PATH` at the bare OMG `XMI.xsd` — the schema the runtime
     caches by default — checks only the XMI envelope, not the UML content, so a
     canonical serialization (item 3) is not itself a schema-validated one. To
     schema-check the emitted `uml:*` content, point `DEDIREN_XMI_SCHEMA_PATH` at
     a driver schema that imports `XMI.xsd` plus a UML 2.5.1 XSD and run `xmllint
     --nonet --noout --schema <driver.xsd> <document>`; OMG publishes no
     importable UML 2.5.1 XSD, so supply or generate one (for example from the
     Eclipse UML2 metamodel) or import the document into a UML tool. Never report
     "XMI schema-validated" when only the envelope was checked; report the
     achieved level under `Dediren tool issues`.
   In restricted environments pre-fetch XSDs and pass offline paths per
   [self-check](self-check.md) envelope/schema guidance.
