# Professional readiness — OEF view quality

Use this procedure after Build / Extract has produced the candidate OEF view set, and during Review artefact checks. It judges the architecture artefact itself: OEF model quality, viewpoint fit, diagram communication, and reviewability. It does not judge the consuming project's README, rendered screenshots, gallery, publication page, or CI packaging.

## Quality levels

- **model-valid:** XML/OEF structure, element types, relationship types, and basic ArchiMate well-formedness are correct.
- **diagram-readable:** `model-valid` plus readable layout, bounded density, fitting labels, meaningful grouping, and connectors that avoid unrelated nodes.
- **review-ready:** `diagram-readable` plus a clear architecture question per view, correct viewpoint semantics, curated content, and enough context for an architect to review the model without hidden verbal explanation.

Default Build / Extract target: `diagram-readable`. Default Review target: assess whether the artifact reaches `review-ready`.

## View review loop

For each `<view>`:

1. **State the question.** Write the one architecture question the view answers. If no concise question exists, emit `AD-Q1`.
2. **Check the viewpoint.** Confirm the OEF `viewpoint=` is the right concern for that question. If not, emit `AD-Q2`.
3. **Identify the reviewer.** Name the likely reviewer: enterprise architect, solution architect, product owner, platform engineer, operations, security, or delivery lead. Labels and detail level must suit that audience.
4. **Curate content.** Remove, group, split, or demote elements that are present only because extraction found them. Extraction traceability belongs in the model; the view should show only what supports its question. Use `AD-Q5` for leakage.
5. **Find the main path.** A professional view has a dominant chain: capability realisation, service realisation, process trigger/flow, technology hosting, migration plateau/gap, or motivation-to-requirement trace. If relationship completeness hides that path, emit `AD-Q6`.
6. **Check hierarchy.** Important nodes and relationships should read first. If everything has equal visual weight, equal density, or equal naming prominence, emit `AD-Q4`.
7. **Check labels.** Prefer domain-facing names in stakeholder and architecture-review views. Code-facing names are acceptable in implementation drill-downs and traceability notes. Generic, duplicated, or code-shaped labels in the wrong view trigger `AD-Q10`.
8. **Check renderability.** A professional view must be materialized in OEF:
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

Use the lowest level justified by evidence:

- Return `model-valid` when syntax and notation are sound but layout or communication is not dependable.
- Return `model-valid` when a generated view lacks materialized node or connection geometry.
- Return `model-valid` when any unresolved `AD-L11` finding exists. Connector-through-node is a blocking enterprise architecture readability failure, regardless of otherwise-valid XML.
- Return `model-valid` when unresolved `AD-L12`, `AD-L13`, `AD-L14`, or `AD-L15` findings make layout communication unreliable.
- Return `diagram-readable` when views can be read but still need curation, viewpoint sharpening, or decision context before formal review.
- Return `review-ready` only when no unresolved `AD-Q*`, `AD-L2`, `AD-L3`, `AD-L4`, `AD-L11`, `AD-L12`, `AD-L13`, `AD-L14`, `AD-L15`, `AD-B-*`, `AD-6`, or `AD-2` finding blocks the review purpose.

Review output should lead with:

```text
Professional readiness: model-valid | diagram-readable | review-ready
Top artifact blockers: <none | AD-Q*/AD-L*/AD-B*/AD-* codes with one-line reasons>
```

Recommended next tasks must be modeling tasks, for example: sharpen the view question, split an inventory view, connect Motivation elements to affected architecture elements, clarify a realisation spine, add process handoffs, or rename code-shaped labels. Do not recommend README rows, render generation, galleries, screenshots, or project CI as architecture-design tasks.
