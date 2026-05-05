# Professional-quality pressure cases

These are fixture expectations for the professional-readiness pass. They are intentionally expressed as small OEF/model-review scenarios rather than project package checks; README rows, PNG renders, galleries, and CI publication are outside `architecture-design` scope.

| Case | Fixture seed | Mutation / review condition | Expected finding |
|---|---|---|---|
| Inventory view | Any valid Application Cooperation or Technology Usage fixture | Add a view that lists every discovered component/resource but has no stated architecture question or dominant relationship path | `AD-Q1` |
| Over-dense readable-but-not-reviewable view | Any fixture | Keep valid OEF and non-overlapping nodes, but exceed the practical review budget or make every cluster visually equal | `AD-Q3`, possibly `AD-Q4` |
| Process thinness | `business-process-cooperation.oef.xml` | Remove Triggering/Flow handoffs, actor assignments, passive-object access, or terminal outcome while leaving process nodes present | `AD-Q8` plus applicable `AD-B-*` |
| Service realization thinness | `service-realization.oef.xml` | Keep services named but break or obscure the Business Process / Business Service → Application Service → Application Component chain | `AD-Q9` plus applicable `AD-B-6` / `AD-B-7` |
| Orphaned decision context | `motivation.oef.xml` | Leave Requirements, Constraints, Goals, or Principles floating with no clear connection to affected architecture decisions or elements | `AD-Q7` |
| Label ambiguity | Any fixture | Replace domain-facing names with duplicated generic labels such as `Service`, `Component`, `Handler`, or code-shaped names in a stakeholder-facing view | `AD-Q10` |

Use these cases when validating skill behavior after editing `professional-readiness.md`, `smell-catalog.md`, or Review-mode wording. A correct review distinguishes `model-valid` from `diagram-readable` and `review-ready`, and recommends modeling actions only.

