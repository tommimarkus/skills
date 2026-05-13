---
name: devsecops-audit
description: >-
  Use when auditing DevSecOps posture for CI/CD, IaC, containers, releases, supply-chain evidence, or code-level security smells. Supports quick PR/file audits and deep repo reviews. Defer non-security design and test-quality work to sibling skills.
---

# DevSecOps Audit

Audit whether controls affect what ships. Use `../../docs/security-reference/devsecops.md`;
cite `../../docs/security-reference/devsecops-smell-catalog.md` codes without
restating rubric prose.

## Contract

Own Quick/Deep audits for CI/CD, IaC, containers, releases, supply-chain
evidence, and security code smells. Delegate non-security design/test work.

Inputs: scope, mode, cost stance, release/live evidence, and tools. If ambiguous,
ask the user when mode/scope/cost stance/MCP/network/destructive
action/sibling boundary lacks a safe default; otherwise continue. Reject false
positives; state confidence and honest limits. Never claim enforcement,
reachability, account control, rotation, or provenance without evidence.

## Load Map

Load `extensions/github-actions.md` and `docs/security-reference/devsecops-extensions/github-actions.md` when workflows/actions match.
Load `extensions/bicep.md` and `docs/security-reference/devsecops-extensions/bicep.md` when Bicep/Azure IaC matches.
Load `extensions/dockerfile.md` and `docs/security-reference/devsecops-extensions/dockerfile.md` when Docker/Compose/container targets match.
Load `extensions/dotnet-security.md` and `docs/security-reference/devsecops-extensions/dotnet-security.md` when C#/.NET/appsettings targets match.
Load `references/procedures/cost-stance-detection.md` when resolving cost stance.
Load `references/procedures/stage-coverage-matrix.md`, `references/procedures/evidence-per-release.md`, and `references/procedures/mcp-github-probes.md` when running Deep mode.
Load `references/procedures/extension-authoring.md` only when editing extensions.
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
6. Apply codes; separate fact from inference; emit output/footer.

## Outputs

- Quick: findings only; no rollup or MCP probes.
- Deep: rubric §9 sections 1-12: scope, target levels, stage matrix,
  CICD-SEC scan, smells, positives, provenance, evidence-per-release,
  framework coupling, live-state block, verdict, honest limits.

Findings use `[CODE] type: path:line` with severity (`block`, `warn`, `info`),
stage, evidence, action, and citation. If none, say so with limits. Every answer
reports extensions, cost stance/source, Codex Security, rubric path, and
evidence limits. Deep also reports MCP GitHub, verdict (`enforcing`, `partial`,
`decorative`), and rubric §8 limits.

## Stop Conditions

Stop when scope is missing, sibling ownership dominates, live evidence is absent,
cost-gated findings lack stance, MCP/tool failure would be retried, output would
copy rubric/vendor prose, or confidence is too low.

Rerun `scripts/skill-architecture-report.sh .` after skill edits.
