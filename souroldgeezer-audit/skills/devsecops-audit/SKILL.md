---
name: devsecops-audit
description: >-
  Use when auditing DevSecOps security posture for CI/CD workflows, IaC, containers, releases, or code-level security smells. Supports quick PR/file audits and deep repo reviews. Defer non-security design to sibling software, infra, API, app, architecture, and test-quality skills.
---

# DevSecOps Audit

Audit whether controls affect what ships. Use `../../docs/security-reference/devsecops.md`
and cite `../../docs/security-reference/devsecops-smell-catalog.md` codes; do
not restate rubric prose.

## Contract

Own Quick/Deep audits for CI/CD, IaC, containers, releases, supply-chain
evidence, and security code smells. Delegate non-security design/test work to
sibling skills.

Inputs: files/diffs/repo scope, mode, cost stance, release/live evidence, and
tools. If ambiguous, ask the user when mode/scope/cost stance/MCP or network
use/destructive action/sibling ownership lacks a safe default; otherwise
continue. Reject false positives, state confidence and honest limits, and never
claim runtime enforcement, reachability, account control, rotation, or
provenance from unsupported evidence.

## Load Map

Load `extensions/github-actions.md` and `docs/security-reference/devsecops-extensions/github-actions.md` when workflows/actions match.
Load `extensions/bicep.md` and `docs/security-reference/devsecops-extensions/bicep.md` when Bicep/Azure IaC matches.
Load `extensions/dockerfile.md` and `docs/security-reference/devsecops-extensions/dockerfile.md` when Docker/Compose/container targets match.
Load `extensions/dotnet-security.md` and `docs/security-reference/devsecops-extensions/dotnet-security.md` when C#/.NET/appsettings targets match.
Load `extensions/README.md` only when editing extensions.

Load `references/procedures/cost-stance-detection.md` when resolving cost stance. Load `references/procedures/stage-coverage-matrix.md`, `references/procedures/evidence-per-release.md`, and `references/procedures/mcp-github-probes.md` when running Deep mode.

Before editing triggers/workflow/extensions/grounding/evals, load `references/evals` and `references/source-grounding.md`; keep evals synthetic.

## Workflow

1. Select mode, scope, target types, evidence layers, and delegations.
2. Prefer `rg`; inspect workflow/IaC/container/code/release/security files,
   then load and announce extensions.
3. Resolve cost stance from invocation, `config.yaml`, repo guidance, then
   default `full`; disclose source.
4. Use `codex-security:security-scan` when available and app-code vulnerability
   coverage overlaps; otherwise disclose unavailable/not applicable.
5. For Deep, probe GitHub MCP once; on failure record unavailable and continue
   static-only. Never retry.
6. Apply codes, separate fact from inference, reject unsupported findings, then
   emit output/footer.

## Outputs

- Quick: findings only; no rollup or MCP probes.
- Deep: rubric §9 sections 1-12: scope, target levels, stage matrix,
  CICD-SEC scan, smells, positives, provenance, evidence-per-release,
  framework coupling, live-state block, verdict, honest limits.

Findings use `[CODE] type: path:line` with severity, stage, evidence, action,
and citation. Severity is `block`, `warn`, or `info`. If none, say so with
limits. Every answer reports extensions, cost stance/source, Codex Security,
rubric path, and evidence limits. Deep also reports MCP GitHub, verdict
(`enforcing`, `partial`, `decorative`), and rubric §8 limits.

## Stop Conditions

Stop when scope is missing, sibling ownership dominates, needed live evidence is
absent, cost-gated findings lack stance, MCP/tool failure would be retried,
output would copy rubric/vendor prose, or confidence is too low.

Rerun `scripts/skill-architecture-report.sh .` after skill edits.
