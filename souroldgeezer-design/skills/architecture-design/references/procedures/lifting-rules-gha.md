# Lifting rules — GitHub Actions to ArchiMate® Implementation & Migration

Rules for lifting ArchiMate® **Implementation & Migration Layer** elements from `.github/workflows/*.yml` files. Invoked by Extract mode.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). This procedure cites §4.7 (Implementation & Migration elements) and §7.1 (extractability per layer).

## Sources read

- `.github/workflows/*.yml` — all workflow files.
- Workflow `name:` field for human-readable labels.
- `on:` triggers to distinguish continuous deploy workflows from ad-hoc / scheduled / manual ones.
- `jobs:` and `jobs.*.environment:` fields to discover Plateaus.
- `jobs.*.steps:` with deploy actions (`azure/*-deploy`, `Azure/login`, `actions/deploy-pages`) to identify Work Packages proper vs. build-only jobs.

Out of scope: Azure Pipelines YAML (different stack; future extension); GitLab CI; third-party CI scripts.

## Mapping rules

### Workflow files → Work Package

| Detection | ArchiMate element |
|---|---|
| Workflow file with a deploy job (contains `Azure/login` + any `azure/*-deploy` action, OR `actions/deploy-pages`, OR `az webapp deploy`, OR `az functionapp deployment`, OR Bicep-deploy steps) | **Work Package** — identifier derived from workflow filename without `.yml`, `<name>` = workflow `name` field |
| Workflow file with only build / test / lint steps | Not lifted as a Work Package; noted in the extraction summary but architectural-only repos have no Implementation & Migration lift |
| Workflow file purely for repository housekeeping (Dependabot auto-merge, label sync, stale-issue bot) | Not lifted |

### Job environments → Plateau

Each distinct `environment:` value across all deploy jobs becomes a **Plateau**. Convention:

| Environment value pattern | ArchiMate Plateau label |
|---|---|
| `dev` / `development` | *Development* |
| `test` / `qa` / `staging` / `stg` | *Test* / *Staging* (preserve the project's label) |
| `prod` / `production` | *Production* |
| Any other value | Preserved verbatim as the Plateau label |

If no `environment:` field is used anywhere, the workflow is still a Work Package but with a single **Plateau** labelled *Production* when IaC tags or parameters show production, otherwise *Target* (the canonical unknown-environment default). Do **not** emit Development / Staging / Production as a trio unless the workflow or IaC actually contains those environments.

### Deploy jobs → Implementation Event

Each successful deploy job run is a candidate **Implementation Event** — a state change marking a move from one Plateau to the next. The procedure emits **one Implementation Event per (Work Package × target Plateau) pair**, not one per git commit or workflow run:

| Detection | ArchiMate element |
|---|---|
| A `jobs.<name>:` with `environment: dev` | **Implementation Event** — *Deploy to Development* (Work Package reaches Development Plateau) |
| A `jobs.<name>:` with `environment: prod` gated on approval (`required_reviewers` in the environment's repo settings) | **Implementation Event** — *Deploy to Production* with `gate: required_reviewers` annotation |
| A job matrix with multiple environments | One Implementation Event per matrix entry |

### Plateau transitions → Gap

Plateau-to-Plateau transitions represent architectural migration only when there is explicit as-is / to-be migration intent in the architect prompt or existing view documentation. Normal multi-environment deployment is parallel topology, not migration. If a workflow defines a sequence such as `deploy-dev` then `deploy-staging` then `deploy-prod`, model that sequence as deployment control in documentation on the Work Package / Implementation Events, not as Plateau Triggering.

Extract never creates Gaps from workflow sequencing alone. Only emit **Gaps** for true migration:

| Detection | ArchiMate element |
|---|---|
| Architect-supplied as-is / to-be migration intent, with two Plateau states | **Gap** between the source Plateau and the target Plateau |
| Manual-approval gate on a Plateau-advancing migration step | Gap annotated `gate: manual-approval` |

If the architect's existing diagram already labels Gaps with specific migration themes (e.g., *Feature rollout*, *Decommission legacy*), Extract preserves those labels and only adds a Gap if one is genuinely new. Review emits `AD-20` when Plateaus that look like parallel environments are connected by Triggering without migration intent, and `AD-19` when a Plateau has no environment evidence in workflow or IaC.

### Deliverables (optional)

Workflows that produce a discrete, named artefact (a release tag, a signed container image, a published NuGet package) and reference it downstream map to a **Deliverable**. Detection is signal-heavy:

| Detection | ArchiMate element |
|---|---|
| `actions/upload-artifact` with a stable named artifact + `actions/download-artifact` with the same name in a downstream job | **Deliverable** — label = artifact name; related to the Work Package via Composition |
| `actions/create-release` / `softprops/action-gh-release` | **Deliverable** — *GitHub Release* composed on the Work Package |
| `docker/build-push-action` pushing to a registry | **Deliverable** — *container image* (name = pushed tag) composed on the Work Package |

If Deliverables are noisy and the architect hasn't asked for them, the procedure omits them and leaves only Work Packages + Plateaus + Implementation Events for Deployment Topology, or Work Packages + Plateaus + Gaps + Implementation Events for explicit Migration.

## Naming conventions

- **Work Package identifier** — `id-wp-<slug>` where `<slug>` is the workflow filename without `.yml`, hyphens preserved: `deploy-prod.yml` → `id-wp-deploy-prod`; `<name>` = the workflow `name:` field.
- **Plateau identifier** — `id-plateau-<env>` where `<env>` is the environment value lowercased.
- **Implementation Event identifier** — `id-event-deploy-<env>` per (Work Package, Plateau).
- **Gap identifier** — `id-gap-<source>-to-<target>`.
- **Deliverable identifier** — `id-deliverable-<name>`.

## Output shape

Lifted elements are emitted as OEF XML into the canonical file at `docs/architecture/<feature>.oef.xml`. Fragment:

```xml
<!-- ==== Implementation & Migration Layer (lifted from .github/workflows/) ==== -->

<elements>
  <element identifier="id-wp-deploy" xsi:type="WorkPackage">
    <name xml:lang="en">Deploy (deploy.yml)</name>
  </element>
  <element identifier="id-plateau-dev" xsi:type="Plateau">
    <name xml:lang="en">Development</name>
  </element>
  <element identifier="id-plateau-staging" xsi:type="Plateau">
    <name xml:lang="en">Staging</name>
  </element>
  <element identifier="id-plateau-prod" xsi:type="Plateau">
    <name xml:lang="en">Production</name>
  </element>
  <element identifier="id-event-deploy-dev" xsi:type="ImplementationEvent">
    <name xml:lang="en">Deploy to Development</name>
  </element>
  <element identifier="id-event-deploy-staging" xsi:type="ImplementationEvent">
    <name xml:lang="en">Deploy to Staging</name>
  </element>
  <element identifier="id-event-deploy-prod" xsi:type="ImplementationEvent">
    <name xml:lang="en">Deploy to Production (gated)</name>
  </element>
</elements>

<relationships>
  <relationship identifier="id-rel-wp-to-event-dev"
                source="id-wp-deploy" target="id-event-deploy-dev"
                xsi:type="Triggering"/>
  <relationship identifier="id-rel-wp-realizes-dev"
                source="id-wp-deploy" target="id-plateau-dev"
                xsi:type="Realization"/>
  <relationship identifier="id-rel-wp-realizes-staging"
                source="id-wp-deploy" target="id-plateau-staging"
                xsi:type="Realization"/>
  <relationship identifier="id-rel-wp-realizes-prod"
                source="id-wp-deploy" target="id-plateau-prod"
                xsi:type="Realization"/>
</relationships>
```

The fragment above is the Deployment Topology pattern: the environments are sibling Plateaus, and the workflow Realizes each target state. Plateau-to-Plateau Triggering is reserved for architect-authored as-is / to-be migration.

## Cross-layer linking

Implementation & Migration is meaningful only when it touches the Application or Technology Layer it moves. Where a workflow targets a specific Bicep resource (discoverable by resource-name or resource-group naming convention), emit:

| Detection | ArchiMate relationship |
|---|---|
| Workflow `Azure/login` scoped to a specific subscription + `az deployment group create -f infra/main.bicep` or equivalent | **Realisation** from the Work Package to each Technology Node it deploys (read from [lifting-rules-bicep.md](lifting-rules-bicep.md)) |
| Workflow publishing an Application Component (Function App zip deploy, Static Web App deploy) | **Realisation** from the Work Package to the Application Component it deploys |

Where no resource target is discoverable, omit the cross-layer link — the skill does not invent connections.

## What this procedure does not do

- Lift **Strategy** Course of Action from workflows. A workflow is a Work Package, not a Course of Action — Strategy is forward-only per reference §7.2.
- Validate the workflow security posture. That is [`devsecops-audit`](../../../../../souroldgeezer-audit/skills/devsecops-audit/SKILL.md)'s scope, not this skill's.
- Model **Ad-hoc** runs per `workflow_dispatch`. Manual dispatches are operational events, not architectural ones; they don't add Implementation Events to the ArchiMate model.
- Track historical runs. The skill reads the workflow *definitions* to infer the Migration view shape; it does not read GitHub Actions run history.
