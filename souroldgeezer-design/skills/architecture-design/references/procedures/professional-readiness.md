# Professional readiness — OEF view quality

Use this procedure after Build / Extract has produced the candidate OEF view set, and during Review artefact checks. It judges the architecture artefact itself: OEF model quality, viewpoint fit, diagram communication, and reviewability. It does not judge the consuming project's README, rendered screenshots, gallery, publication page, or CI packaging.

The procedure reports two orthogonal axes per view: **readiness** (visual and notational quality, classified per `<view>` and rolled up to the artifact) and **authority** (who or what backs the architecture content). Authority does not gate readiness — a forward-only view can be `review-ready` for visual quality while remaining `forward-only-or-inferred` for content authority. Both axes are emitted in the per-view matrix; the architect reads them together when deciding whether the diagram is fit for the next consumer. See reference §2.8 (readiness) and §2.9 (authority).

A view is judged by final OEF materialization and visual/semantic quality, not
by the layout backend used. Fallback geometry, future backend geometry, and
hand-authored coordinates all pass through the same readiness and `AD-L*`
checks.

When the packaged layout runtime is used, readiness also consumes its contract
and runtime diagnostics: schema validation failure caps the affected run at
`model-valid`; route-repair and global-polish controlled failures cap the
affected view until repaired; blank, tiny, cropped, or over-tolerance PNG
validation failures cap visual-quality claims for the rendered view.

## Quality levels

- **model-valid:** XML/OEF structure, element types, relationship types, and basic ArchiMate well-formedness are correct.
- **diagram-readable:** `model-valid` plus readable layout, bounded density, fitting labels, meaningful grouping, and connectors that avoid unrelated nodes.
- **review-ready:** `diagram-readable` plus a clear architecture question per view, correct viewpoint semantics, curated content, and enough context for an architect to review the model without hidden verbal explanation.

Default Build / Extract target: `diagram-readable`. Default Review target: assess whether the artifact reaches `review-ready`.

## Authority levels

- **lifted-from-source** — every element in the view resolves to a current source: a `*.csproj` (Application Layer), a Bicep resource (Technology Layer), a workflow file (Implementation & Migration), or a confirmed `LIFT-CANDIDATE` (Business Process / Event / Interaction). This is the default when the view contains no forward-only or unconfirmed lifted content.
- **forward-only-or-inferred** — view contains at least one element from a `FORWARD-ONLY — architect fills in` block (Business Actor / Role / Collaboration / Object / Contract / Product / Service / Function / Motivation / Strategy / Physical), or at least one `LIFT-CANDIDATE` marker the architect has not confirmed. This is the default when any element in the view is forward-only or unconfirmed.
- **architect-approved** — architect has reviewed and approved the view's content. Asserted explicitly via `<property propertyDefinitionRef="propid-authority"><value xml:lang="en">architect-approved</value></property>` on the `<view>` (per reference §6.4b).
- **stakeholder-validated** — domain stakeholder (named in the view's `<documentation>`) has signed off on the architecture claims the view makes. Asserted via `<property propertyDefinitionRef="propid-authority"><value xml:lang="en">stakeholder-validated</value></property>` on the `<view>`.

**Default derivation rule:** scan the view's element references; if every element resolves to a current source and no `LIFT-CANDIDATE` is unconfirmed, default authority is `lifted-from-source`; otherwise `forward-only-or-inferred`. Architect overrides take precedence over the default.

**Override contradiction (`AD-Q11`):** when a view carries `propid-authority="architect-approved"` or `"stakeholder-validated"` while still containing unresolved `FORWARD-ONLY` or `LIFT-CANDIDATE` content, emit `AD-Q11`. The override claims human endorsement of architecture content the view itself shows as unconfirmed. Severity: `warn` by default; escalate to `block` for stakeholder-facing reports.

## View review loop

For each `<view>`:

1. **State the question.** Write the one architecture question the view answers. If no concise question exists, emit `AD-Q1`.
2. **Check the viewpoint.** Confirm the OEF `viewpoint=` is the right concern for that question. If not, emit `AD-Q2`.
3. **Identify the reviewer.** Name the likely reviewer: enterprise architect, solution architect, product owner, platform engineer, operations, security, or delivery lead. Labels and detail level must suit that audience.
4. **Curate content.** Remove, group, split, or demote elements that are present only because extraction found them. Extraction traceability belongs in the model; the view should show only what supports its question. Use `AD-Q5` for leakage.
5. **Find the main path.** A professional view has a dominant chain: capability realisation, service realisation, process trigger/flow, technology hosting, migration plateau/gap, or motivation-to-requirement trace. If relationship completeness hides that path, emit `AD-Q6`.
6. **Check hierarchy.** Important nodes and relationships should read first. If everything has equal visual weight, equal density, or equal naming prominence, emit `AD-Q4`.
7. **Check labels.** Prefer domain-facing names in stakeholder and architecture-review views. Code-facing names are acceptable in implementation drill-downs and traceability notes. Generic, duplicated, or code-shaped labels in the wrong view trigger `AD-Q10`.
8. **Check duplicate stories.** For §9.3 Service Realization views, compare
   each process-rooted view's realization-story fingerprint. If two views have
   the same Application / Technology / data / security / deployment / UI-entry
   story and only the Business Process root differs, emit `AD-B-14` unless the
   view documentation explains a material business difference.
9. **Check renderability.** A professional view must be materialized in OEF:
   non-legend element nodes have `elementRef`, `x`, `y`, `w`, and `h`, and
   the relationships that carry the visual story have relationship
   connections with concrete source/target view nodes. A view with only model
   elements and relationships, or one that renders as Archi's empty placeholder,
   is capped at `model-valid` until geometry is emitted.

## Viewpoint gates

| Viewpoint | Review-ready gate | Finding |
|---|---|---|
| Capability Map | Separates business capability from app inventory; shows ownership, maturity, priority, investment relevance, or realisation when known | `AD-Q1`, `AD-Q5` |
| Application Cooperation | Clarifies collaboration boundaries, integration paths, and responsibility split | `AD-Q1`, `AD-Q4`, `AD-Q6` |
| Service Realization | Shows an auditable Business Process / Business Service → Application Service → Application Component chain, reaching Technology when in scope | `AD-Q9` |
| Technology Usage | Distinguishes runtime node, system software, artifact, technology service, and network/path concerns when relevant | `AD-Q6`, `AD-12` |
| Migration | Shows plateau, gap, work package, deliverable, event, and dependency logic clearly enough to support planning | `AD-Q1`, `AD-9` |
| Motivation | Distinguishes stakeholders, drivers, assessments, goals, outcomes, principles, requirements, and constraints, then connects them to affected architecture decisions or elements | `AD-Q7` |
| Business Process Cooperation | Shows trigger/flow, handoffs, responsibilities, passive objects accessed, and terminal value outcome | `AD-Q8` |

## Quality verdict

Quality is classified **per `<view>` first**, then rolled up to the artifact as the worst-view minimum. A diagram in which one Service Realization view is `review-ready` while a Technology Usage view is `model-valid` is honestly an artifact-level `model-valid` — but the per-view matrix shows the architect exactly which view is the bottleneck and why, so the next iteration can target only that view.

For each `<view>`, use the lowest level justified by evidence:

- Return `model-valid` when syntax and notation are sound but layout or communication is not dependable.
- Return `model-valid` when a generated view lacks materialized node or connection geometry.
- Return `model-valid` when `layoutRequest` or `layoutResult` schema validation
  fails before OEF materialization.
- Return `model-valid` when any unresolved `AD-L11` finding exists *for this view*. Connector-through-node is a blocking enterprise architecture readability failure, regardless of otherwise-valid XML.
- Return `model-valid` when route repair reports `LAYOUT_NO_ROUTE` or
  `LAYOUT_LOCKED_ROUTE_INVALID` and the OEF still depends on that route for its
  visual story.
- Return `model-valid` when global polish returns
  `LAYOUT_GLOBAL_POLISH_NO_IMPROVEMENT` for a view whose stated target requires
  the unresolved defect to be fixed.
- Return `model-valid` for changed rendered views when `validate-png` reports
  blank, tiny, cropped-to-edge, dimension mismatch, or baseline drift above the
  accepted tolerance.
- Return `model-valid` when unresolved `AD-L12` through `AD-L20` findings make this view's layout communication unreliable.
- Return `diagram-readable` when this view can be read but still needs curation, viewpoint sharpening, or decision context before formal review.
- Return `review-ready` only when no unresolved `AD-Q*`, `AD-L2`, `AD-L3`, `AD-L4`, `AD-L11` through `AD-L20`, `AD-B-*`, `AD-6`, or `AD-2` finding blocks this view's review purpose.

Cross-view smells (`AD-B-8`, `AD-B-9`, `AD-B-13`, `AD-B-14`, `AD-DR-*`) are attributed to *every* view they cap — a missing §9.7 cooperation view caps the orphan §9.3 view and any other §9.3 in the same realization story; a duplicate `AD-B-14` caps every view that shares the duplicated fingerprint.

Findings emitted by the source-geometry gate carry a `<view-id>` token in their evidence; map that to the per-view bucket directly. Findings without a view scope (model-level smells like `AD-15`, `AD-17`, `AD-14`) cap the *artifact* rollup but do not change individual view classifications.

The **artifact rollup** is `min(per-view classifications)` ordered `model-valid < diagram-readable < review-ready`. If the artifact carries unresolved model-level blockers (`AD-15`, `AD-17`, `AD-14`, `AD-14-LC`, `AD-16`), cap the rollup at `model-valid` regardless of per-view scores.

**Render gate (when visual quality is in scope).** When the user has requested visual quality — explicit render request, render-polish loop, or Build / Extract with the `[visual]` self-check requested — and render did not run (Archi missing, `DISPLAY` unavailable, `archi-render.sh` blocker, or any other render prerequisite reported "not run" by the self-check), the changed views cap at `model-valid` until render runs. *Changed views* means views modified in the current run (Build emits, Extract re-emits, or Review's render-polish loop targets); unchanged views inherit their prior classification when one exists. Static `AD-L*` findings from the source-geometry gate still constrain the rollup further; the render gate is an additional cap, not a substitute. When the user has not requested visual quality, the render gate does not apply — the skill's source-geometry gate is the visual proxy and per-view readiness is derived from `[static]` checks alone.

Review output should lead with the per-view matrix, then the rollup:

```text
Per-view readiness:
  | View id                       | Viewpoint                       | Readiness        | Authority                  | Top blockers          |
  |---|---|---|---|---|
  | id-view-bpc-checkout          | Business Process Cooperation    | review-ready     | lifted-from-source         | none                  |
  | id-view-sr-place-order        | Service Realization             | diagram-readable | lifted-from-source         | AD-Q9, AD-B-7         |
  | id-view-app-checkout          | Application Cooperation         | model-valid      | lifted-from-source         | AD-L11                |
  | id-view-mot-checkout          | Motivation                      | review-ready     | forward-only-or-inferred   | none                  |

Artifact rollup: model-valid (worst-view minimum; model-level blockers: none)
Top artifact blockers: <none | AD-Q*/AD-L*/AD-B*/AD-* codes with one-line reasons>
```

Build / Extract emit the same matrix in their self-check block; the matrix is required when the artifact contains more than one materialized view, optional (single-row matrix is acceptable) for single-view files. The Authority column is required.

Recommended next tasks must be modeling tasks, for example: sharpen the view question, split an inventory view, connect Motivation elements to affected architecture elements, clarify a realisation spine, add process handoffs, or rename code-shaped labels. Do not recommend README rows, render generation, galleries, screenshots, or project CI as architecture-design tasks.
