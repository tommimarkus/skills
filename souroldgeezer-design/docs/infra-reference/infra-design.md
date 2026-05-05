# Infrastructure Design Reference

## 1. Purpose and Boundary

Infrastructure design makes cloud and deployment systems understandable,
deployable, recoverable, and evolvable before implementation or rollout. It
owns IaC shape, topology, environments, state, identity placement as a design
input, observability handoff, rollout/rollback design, and drift management.

It does not replace application architecture, API contracts, code/module
design, UI design, security audit, or test-quality review. Those concerns are
delegated to their sibling skills.

## 2. Principles

1. **Topology is a contract.** Resource placement, dependency direction, and
   ownership boundaries should be visible in source or deployment records.
2. **IaC expresses intent, not inventory.** Modules should name workload or
   platform concepts, not wrap single resources without a design force.
3. **Environment strategy is explicit.** Dev, test, staging, production, and
   ephemeral environments must differ by declared parameters and policy, not by
   unreviewed copies.
4. **State has one owner.** Remote state, migration records, imports, and
   generated artifacts need clear custody and rollback paths.
5. **Identity is part of the design.** Managed/workload identity, secret
   handoff, and role-assignment boundaries shape the topology even when a
   security audit owns least-privilege findings.
6. **Operations are designed, not appended.** Monitoring, alerting, restore
   paths, what-if/plan reviews, and rollback hooks must be named before
   rollout.
7. **Drift is expected.** The design should state how source, state, cloud
   control-plane truth, and architecture models are reconciled.

## 3. Decision Defaults

### 3.1 Topology Ownership

Default to topology grouped by workload boundary and operational ownership.
Shared platform resources are separate only when their lifecycle, access model,
or blast radius is different from the workload that consumes them.

### 3.2 IaC Module Boundaries

Create a module when it represents a reusable infrastructure concept with a
stable input/output contract. Avoid modules that only rename one resource type.
Keep the module tree shallow unless a deeper split reduces blast radius or
release coupling.

### 3.3 Environment Promotion

Use one source pattern promoted through environments with parameter files,
variable files, or deployment inputs. Do not maintain copy-pasted environment
trees unless the environment is intentionally divergent and the reason is
documented.

### 3.4 State Ownership

Use remote state for team-managed infrastructure, with locking and access
control. Never treat committed state files, local-only state, or manual state
edits as a collaborative design. Import and move operations need reviewable
migration records.

### 3.5 Identity Boundaries

Prefer managed/workload identity for runtime and deployment actors where the
platform supports it. Keep identity assignment close to the resource owner, and
delegate least-privilege evaluation to `devsecops-audit`.

### 3.6 Network and Ingress Boundaries

Place ingress, private connectivity, DNS, and egress controls at boundaries a
team can reason about and test. Do not hide network dependencies in resource
defaults or separate files with no dependency path back to the workload.

### 3.7 Secrets and Configuration Handoff

IaC should declare where secrets and runtime configuration come from, but it
should not embed secret material. Secret exposure and policy hardening are
security-audit concerns; configuration ownership and handoff are
infrastructure-design concerns.

### 3.8 Observability and Operability

Each deployable topology should name its telemetry sink, alert owner, dashboard
or query handoff, backup/restore expectation, and rollout verification layer.
Static source can verify wiring intent; runtime telemetry proves behavior.

### 3.9 Rollout, Rollback, and Migration

State-changing infrastructure changes need a rollout path, a rollback or
forward-fix path, and an explicit verification layer. Destructive replacements,
data migrations, and identity/network changes require human approval unless the
user has already supplied that policy.

### 3.10 Drift and Lifecycle Management

Design for drift detection between source, state, cloud control-plane truth,
and architecture models. Generated artifacts should be either ignored and
rebuildable or committed with a clear source-of-truth rule.

## 4. Primitives

| Primitive | Use for | Design check |
|---|---|---|
| Resource group / stack / project boundary | Lifecycle and ownership grouping | Does one team own deploy, observe, and retire it? |
| Module | Reusable infrastructure concept | Does it raise abstraction above raw resources? |
| Environment parameter set | Promotion differences | Are differences intentional and reviewable? |
| Remote state backend | Team-managed state | Is locking/access control available? |
| Deployment identity | Applying infrastructure | Is the actor separate from runtime identity? |
| Runtime identity | Workload access to dependencies | Is ownership close to the consuming resource? |
| Plan / what-if output | Pre-deployment verification | Is it reviewed before irreversible change? |
| Telemetry sink | Runtime evidence | Is the handoff visible in source or deployment config? |

## 5. Patterns

### 5.1 Workload Module with Platform Inputs

Use a workload module for resources that deploy and roll back together. Accept
platform dependencies as inputs instead of creating hidden cross-cutting
resources inside the module.

### 5.2 Shared Platform Foundation

Use a separate foundation layer for network, DNS, policy, identity platform, or
logging only when its lifecycle and access model are separate from workloads.
Expose stable outputs to workload deployments.

### 5.3 Environment Parameter Promotion

Keep topology source common and promote by parameter or variable files. The
environment-specific surface should show only intended differences: capacity,
region, feature flags, and integration endpoints.

### 5.4 Remote State per Ownership Boundary

Separate state by ownership and blast radius, not by every folder. Cross-state
data access should be explicit and rare because it couples rollout order.

### 5.5 What-If / Plan-Gated Rollout

Run a non-mutating preview before applying infrastructure changes. Treat
unexpected replacement, deletion, or broad permission change as a review stop.

### 5.6 Import / Move Migration Record

When existing resources move under IaC or change address, record the import,
move, or refactor path in source so future plans do not destroy and recreate
stateful resources accidentally.

### 5.7 Observability Handoff

The topology declares telemetry sinks, alert routing, and dashboard/query
handoff. The implementation may live in platform tooling, but the dependency is
part of infrastructure design.

## 6. Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `ID-TOP-1` | Mixed lifecycle topology | Resources with different deploy/rollback owners share one boundary. | warn |
| `ID-TOP-2` | Hidden platform dependency | Workload deployment creates or assumes shared network, DNS, identity, or logging resources without an explicit platform contract. | warn |
| `ID-TOP-3` | Environment as topology fork | Environments are copy-pasted directories with unexplained structural differences. | warn; block when added code extends the fork |
| `ID-IAC-1` | Thin resource wrapper module | Module wraps one resource type without a higher-level infrastructure concept. | info; warn when mandatory |
| `ID-IAC-2` | Deep module cascade | Module tree obscures dependency direction or forces broad changes for a narrow resource. | warn |
| `ID-IAC-3` | Generated artifact ambiguity | Generated templates, plans, or provider output are committed without a source-of-truth rule. | warn |
| `ID-ENV-1` | Ambient environment selection | Deployment chooses environment from caller shell, default subscription, workspace, or current directory without an explicit input. | warn |
| `ID-ENV-2` | Undeclared promotion policy | No source-visible rule explains how changes move from dev/test/staging to production. | warn |
| `ID-STATE-1` | Local or committed team state | Team-managed infrastructure relies on local state files or state committed to source. | block |
| `ID-STATE-2` | Missing migration record | Import, state move, or resource rename is required but not captured in source or plan notes. | warn; block when replacement risk is stateful |
| `ID-STATE-3` | Cross-state dependency sprawl | Multiple stacks read each other's state outputs with no ownership boundary. | warn |
| `ID-OPS-1` | No rollout verification layer | Change can apply without plan/what-if, smoke, telemetry, or human review gate. | warn; block for destructive changes |
| `ID-OPS-2` | Observability afterthought | Resources deploy without declaring telemetry sink, alert route, or operations handoff. | warn |
| `ID-OPS-3` | Restore path absent | Stateful resources have no backup/restore or recovery expectation in the design. | warn |
| `ID-EVO-1` | Drift reconciliation absent | No process or tooling reconciles source, state, and cloud control-plane truth. | warn |
| `ID-EVO-2` | Versionless platform dependency | Provider, module, CLI, or deployment action version is unconstrained where changes can alter plans. | warn |

## 7. Checklist with Verification Layers

| Check | Layer |
|---|---|
| IaC root and module boundaries match ownership and lifecycle. | static |
| Environment selection is explicit and reviewable. | static |
| State backend is remote, locked, and outside source control for team-managed infra. | iac |
| Plan or what-if output is required before apply. | plan |
| Runtime identity and deployment identity are distinct design actors. | iac |
| Secret material is referenced, not embedded. | static; delegate hardening to `devsecops-audit` |
| Telemetry sink and operations handoff are declared. | iac; runtime confirms behavior |
| Backup/restore expectation is named for stateful resources. | iac; runtime confirms restore success |
| Destructive replacements and migrations have approval and recovery path. | plan; human |
| Architecture model drift is checked when `docs/architecture/<feature>.oef.xml` exists. | static; delegate to `architecture-design` |

## 8. Out of Scope and Delegation Map

- HTTP API contract, auth behavior, idempotency, problem+json, retries, API
  observability: `api-design`.
- Code/module/script design: `software-design`.
- Responsive UI and WCAG behavior: `responsive-design`.
- ArchiMate/OEF modeling, rendered diagrams, and model drift: `architecture-design`.
- Security posture, secrets, least privilege, pipeline hardening, supply chain:
  `devsecops-audit`.
- Unit, integration, and E2E test quality: `test-quality-audit`.
