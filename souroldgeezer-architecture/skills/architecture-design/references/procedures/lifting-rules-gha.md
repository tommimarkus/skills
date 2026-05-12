# GitHub Actions Lifting Rules

Use for Extract when `.github/workflows/` is in scope.

## Elements

- Relevant build/test/deploy/migrate/release workflows: Work Packages.
- Jobs/environments: Plateaus, deliverables, or implementation events only when
  architecture-significant.
- Routine CI stays out unless delivery architecture is requested.

## Relationships

- Job dependencies and environment promotion: Triggering or Flow.
- Deployment workflows may realize/serve delivered state when evidence is clear.

## Package Output

Do not infer migration from parallel environments. Record source paths/job names.
Use source-backed groups for environments, release lanes, stages, or job clusters
when workflow structure shows a boundary.
