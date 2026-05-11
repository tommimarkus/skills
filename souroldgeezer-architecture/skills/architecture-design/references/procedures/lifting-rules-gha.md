# GitHub Actions Lifting Rules

Use for Extract when `.github/workflows/` is in scope.

## Elements

- Workflows that build, test, deploy, migrate, or release become Work Packages
  when they are relevant to the feature.
- Jobs or environments can support Plateaus, deliverables, or implementation
  events when they represent architecture-significant states.
- Routine CI jobs stay out of architecture views unless the user asks to model
  delivery architecture.

## Relationships

- Job dependencies and environment promotion can support Triggering or Flow
  relationships.
- Deployment workflows can realize or serve the technology/application state
  they deliver when source evidence is explicit.

## Package Output

Do not invent migration intent from parallel workflow environments. Record
source paths and job names on lifted elements.

Use source-backed groups for environments, release lanes, deployment stages, or
job clusters when workflow structure shows a boundary. Routine build/test jobs
do not need groups unless delivery architecture is the requested view concern.
