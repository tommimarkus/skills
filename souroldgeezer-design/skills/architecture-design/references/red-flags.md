## Red Flags

Output contains any of the following? Stop; fix before delivering:

- **Invalid relationship per Appendix B.** Fix per `AD-2`; consult ArchiMate® 3.2 Appendix B (Relationships Table).
- **View cannot answer an architecture question.** Fix per `AD-Q1` / `AD-Q2`; either sharpen the view's purpose and viewpoint or remove the view.
- **Generated view has no materialized geometry.** Add concrete `<node xsi:type="Element">` placements and `<connection xsi:type="Relationship">` routing for every emitted view; element / relationship definitions alone are not a professional diagram.
- **Duplicate OEF `identifier` values.** Fix per `AD-17`; every model element, relationship, view node, and view connection identifier shares one XML ID space.
- **Review-ready claimed while professional-quality findings remain.** Fix `AD-Q*` findings first, then restate the quality level honestly as `model-valid` or `diagram-readable` if gaps remain.
- **Forward-only or lift-candidate markers missing.** Fix `AD-14` / `AD-14-LC`; Business, Motivation, Strategy, and Physical forward-only output needs the XML-comment marker, and lifted Business Process / Event / Interaction elements need `LIFT-CANDIDATE` markers with `source=` and `confidence=`.
- **Layer soup.** Fix `AD-1`; pick one of the seven supported diagram kinds.
- **Business Process Cooperation or Service Realization gaps.** Fix `AD-B-*`; process views need the required Triggering / Flow chain, realization coverage, drill-downs, process coverage, and UI entrypoint modeling where applicable.
- **Missing Realisation chain.** Fix `AD-6`; Business Service needs a realising Application Service, and Application Service needs a realising Application Component.
- **Active structure directly accessing passive structure.** Fix `AD-4`; put a Process or Function between Actor and Business Object.
- **Association overuse.** Fix `AD-5`; pick a typed relationship.
- **Migration view without a Plateau axis.** Fix `AD-9`.
- **RBAC-only technology path without visible Managed Identity Access.** Fix `AD-18`.
- **Fictitious or semantically wrong deployment Plateaus.** Fix `AD-19` / `AD-20`.
- **External Application Component without trust-boundary Grouping.** Fix `AD-21`.
- **Extract refused with no guidance.** Suggest Build mode and name the forward-only layers.
- **Drift finding asserts a pass from static review alone.** Restate as "source-aligned; drift re-check required against current code/IaC."
- **Invalid or misspelled `xsi:type`.** Fix per reference §6.2/§6.3; misspellings break tool import.
- **View `<node>` or `<connection>` without `xsi:type`.** Fix `AD-15`; `xmllint --noout` is insufficient.
- **Metadata payload in the ArchiMate® namespace.** Fix `AD-16`; catalog payload elements need a non-ArchiMate namespace.
- **Model children invalid or out of OEF sequence.** Fix `AD-17`; child order is `name -> documentation -> metadata -> elements -> relationships -> organizations -> propertyDefinitions -> views`, and model-root `<properties>` is invalid.
- **Layer-ordering, overlap, undersize, view-budget, nested-plus-edge, off-grid, hierarchy, or canvas-origin layout defects.** Fix `AD-L1` through `AD-L10` before claiming `diagram-readable`.
- **Connector passes through an unrelated node, or endpoint bendpoint sits inside the endpoint box.** Fix `AD-L11`; readiness cannot exceed `model-valid`.
- **Layout request/result schema validation failed.** Fix the JSON contract or the OEF-to-layout handoff before materializing geometry.
- **Route repair reports no route or invalid locked route.** Fix the route or disclose the readiness cap; do not silently move locked nodes.
- **Rendered PNG validator reports blank, tiny, cropped, or over-tolerance drift.** Re-render or repair geometry before claiming visual quality.
- **View-orphan, stacked connector, wide gap, fan-out crisscross, long bus route, duplicate visible story path, misleading boundary crossing, ambiguous nested ownership, or hidden Service Realization spine.** Fix `AD-L12` through `AD-L20`.
- **Duplicate Service Realization drill-downs for the same realization story.** Fix `AD-B-14`; consolidate unless the process changes application, data, technology, security, deployment, UI-entry, or business semantics materially.
- **Authority override contradicted by content.** Fix `AD-Q11`; either resolve the underlying `FORWARD-ONLY` / `LIFT-CANDIDATE` content (architect fills in or confirms the lift) or remove the `propid-authority` override until the content is genuinely backed.
