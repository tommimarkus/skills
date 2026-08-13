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
survived: the tested compatibility baseline keeps `status: ok` and declares any omission
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
3. **Content coverage (XMI).** Retain `XMI ready (<coverage>)`. When a direct
   export result is available, derive its view/count, omissions, and represented
   content from the pinned runtime's `export-result.schema.v2` `.data.assurance`
   object. Read `artifact_scope` for
   the selected view kinds and the `coverage` partitions `represented`,
   `omitted`, and `unrepresented_in_view`, including their element and
   relationship totals and by-type counts. Read the exhaustive `kind_taxonomy`
   instead of inferring whole-model or UMLDI scope from a filename: aggregate
   model and provisional UMLDI support remain class/data family only. Keep
   `DEDIREN_XMI_ELEMENTS_OMITTED` / `DEDIREN_XMI_RELATIONSHIPS_OMITTED`
   diagnostics as complementary detail. The native package-build-result does
   not surface assurance; on the default package-build path, compare the
   generated artifact against package source, read the export diagnostics, and
   disclose `assurance not surfaced by package build`. An `ok` envelope never
   erases omissions or in-view content the writer did not represent.
4. **Schema validation.** Dediren runs its own OEF/XMI schema validation in-JVM
   — it no longer shells out to `xmllint` internally, so there is no
   `*_SCHEMA_VALIDATOR` override to configure; the `DEDIREN_OEF_SCHEMA_DIR` /
   `DEDIREN_XMI_SCHEMA_PATH` / `DEDIREN_SCHEMA_CACHE_DIR` variables still govern
   where the XSDs are sourced and cached ([self-check](self-check.md)). The
   user-side deeper check below (a driver schema plus `xmllint`) is a separate,
   downstream option, not something Dediren runs. Disclose which schema the
   evidence used — and, for XMI, which validation level was reached.
   - *OEF (ArchiMate).* The OEF document always carries a `<views>`/`<diagrams>`
     element, so it declares and validates against the Open Group
     `archimate3_Diagram.xsd`; its embedded `schemaLocation` names that diagram
     schema (dediren 2026.07.1+; earlier runtimes named the model-only
     `archimate3_Model.xsd`, which rejects `<views>`).
   - *XMI (UML).* When direct-result assurance is present, read
     `.data.assurance.validation_evidence`, including the XMI schema status and
     the UML metamodel/importer evidence arrays. Map its
     `level` value `xmi-envelope-only`, `uml-content-schema-validated`, or
     `importer-validated` to exactly one disclosure: `XMI envelope only`,
     `UML-content schema`, or `importer validated`. Empty stronger-evidence
     arrays never establish the stronger level, and `xmi-envelope-only` never
     establishes conformant UML abstract syntax. [Dediren issue #71](https://github.com/tommimarkus/dediren/issues/71)
     records the provenance of the machine assurance contract. For deeper
     validation, supply a UML-content schema or validate an import with a real
     UML tool, then report the level actually run. A package-build-only result
     cannot upgrade validation strength from its diagnostic prose alone.
   In restricted environments pre-fetch XSDs and pass offline paths per
   [self-check](self-check.md) envelope/schema guidance.
