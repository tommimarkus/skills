# GitHub Actions Lifting Rules

Use for Extract when `.github/workflows/` is in scope and the requested concern
includes delivery, migration, release, environment promotion, or governance.

## Source Mapping

| Source evidence | Prefer | Avoid |
|---|---|---|
| Workflow files | Workflow files are Work Package candidates only when delivery architecture is in scope | Routine CI in architecture views |
| Jobs | Jobs can be implementation steps or grouped work inside a Work Package | Separate Work Package for every job |
| Artifacts and deployment packages | Artifacts and deployment packages can be Deliverables | Application Component |
| Environment promotion or release occurrence | Implementation Event; Plateau only when source or architect intent describes state transition | Migration state from parallel environments alone |
| Build/test/lint-only workflow | Omit unless delivery governance is requested | Business Process |

Routine CI stays out unless delivery architecture is requested.

## Relationships

- Job dependencies and environment promotion: Triggering when order/causality is
  the claim; Flow when a deployable artifact or payload moves between steps.
- Deployment workflow to produced artifact: Realization or Flow by claim.
- Work Package to Deliverable: Realization when the work produces the
  deliverable.

## Package Output

Do not infer migration from parallel environments. Record source paths/job
names. Use source-backed groups for environments, release lanes, stages, or job
clusters when workflow structure shows a boundary.
