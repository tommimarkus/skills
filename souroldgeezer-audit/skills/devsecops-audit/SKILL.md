---
name: devsecops-audit
description: >-
  Use when auditing DevSecOps posture for CI/CD, IaC, containers, releases, supply-chain evidence, or code-level security smells. Supports quick PR/file audits and deep repo reviews. Defer non-security design and test-quality work to sibling skills.
---

# DevSecOps Audit

Audit whether controls affect what ships. Use [`../../docs/security-reference/devsecops.md`](../../docs/security-reference/devsecops.md);
cite [`../../docs/security-reference/devsecops-smell-catalog.md`](../../docs/security-reference/devsecops-smell-catalog.md) codes without
restating rubric prose.

## Contract

Own Quick/Deep audits for CI/CD, IaC, containers, releases, supply-chain
evidence, and security code smells. Delegate non-security design/test work.

Inputs: scope, mode, cost stance, release/live evidence, and tools. If ambiguous,
ask the user when mode/scope/cost stance/MCP/network/destructive
action/sibling boundary lacks a safe default; otherwise continue. Never claim enforcement,
reachability, account control, rotation, or provenance without evidence. For discipline on
false positives, limits, and severity, see [`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §2–§3.

## Load Map

Apply the shared core before loading extensions:
- Load [`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) (discipline + output contract).
- Load [`../../docs/audit-reference/materiality.md`](../../docs/audit-reference/materiality.md) (risk tier) — in all modes; Quick findings carry the SUT risk tier.
- Load [`../../docs/audit-reference/sampling-projection.md`](../../docs/audit-reference/sampling-projection.md) (scale) — in Deep mode only, when full enumeration exceeds budget; Quick must not load it.
- Load [`../../docs/audit-reference/scaled-audit.md`](../../docs/audit-reference/scaled-audit.md) (delegation + evidence durability) — Deep only, when the subject is large enough that per-item evidence may not reach the rollup intact; Quick must not load it. If evidence starts outgrowing context mid-run, load it then rather than continuing.
This skill adds the DevSecOps rubric and `DSO-*` namespace on top; it does not restate craft.

Load [`extensions/github-actions.md`](extensions/github-actions.md) and [`../../docs/security-reference/devsecops-extensions/github-actions.md`](../../docs/security-reference/devsecops-extensions/github-actions.md) when workflows/actions match.
Load [`extensions/bicep.md`](extensions/bicep.md) and [`../../docs/security-reference/devsecops-extensions/bicep.md`](../../docs/security-reference/devsecops-extensions/bicep.md) when Bicep/Azure IaC matches.
Load [`extensions/dockerfile.md`](extensions/dockerfile.md) and [`../../docs/security-reference/devsecops-extensions/dockerfile.md`](../../docs/security-reference/devsecops-extensions/dockerfile.md) when Docker/Compose/container targets match.
Load [`extensions/dotnet-security.md`](extensions/dotnet-security.md) and [`../../docs/security-reference/devsecops-extensions/dotnet-security.md`](../../docs/security-reference/devsecops-extensions/dotnet-security.md) when C#/.NET/appsettings targets match.
Load [`extensions/python-security.md`](extensions/python-security.md) and [`../../docs/security-reference/devsecops-extensions/python-security.md`](../../docs/security-reference/devsecops-extensions/python-security.md) when Python source, web handlers, jobs, CLIs, libraries, or Python runtime/dependency targets match. Apply the pack's visible trust-boundary/taint-path evidence rule before emitting `pys.*` codes.
Load [`extensions/jsts-security.md`](extensions/jsts-security.md) and [`../../docs/security-reference/devsecops-extensions/jsts-security.md`](../../docs/security-reference/devsecops-extensions/jsts-security.md) when JavaScript, TypeScript, React, Node.js, or Vite source/configuration matches. Apply the pack's visible trust-boundary/taint-path evidence rule before emitting `jsts.*` codes; API names alone are not findings.
Load [`references/procedures/cost-stance-detection.md`](references/procedures/cost-stance-detection.md) when cost stance is not given by the invocation or `config.yaml` (an explicitly given stance needs only disclosure, not the detection procedure).
Load [`references/procedures/threat-model-planning.md`](references/procedures/threat-model-planning.md) first when running Deep mode.
Load [`references/procedures/stage-coverage-matrix.md`](references/procedures/stage-coverage-matrix.md), [`references/procedures/evidence-per-release.md`](references/procedures/evidence-per-release.md), and [`references/procedures/mcp-github-probes.md`](references/procedures/mcp-github-probes.md) when running Deep mode.
Load [`references/procedures/extension-authoring.md`](references/procedures/extension-authoring.md) only when editing extensions.
Before editing triggers/workflow/extensions/grounding/evals, load [`references/evals`](references/evals) and [`references/source-grounding.md`](references/source-grounding.md); keep evals synthetic.
Load [`references/procedures/golden-corpus-evals.md`](references/procedures/golden-corpus-evals.md) (corpus: [`references/golden-corpus/`](references/golden-corpus/)) after changing the rubric, smell catalog, output contract, or extensions; record recall per [`audit-craft.md`](../../docs/audit-reference/audit-craft.md) §8.

## Workflow

1. Select mode, scope, target types, evidence layers, and delegations.
2. For Deep, run [`references/procedures/threat-model-planning.md`](references/procedures/threat-model-planning.md) first: enumerate crown jewels, trust boundaries, attacker goals; emit the Risk plan and prioritize fieldwork high-risk-first.
3. Prefer `rg`; inspect workflow/IaC/container/code/release/security files,
   then load and announce extensions.
4. Resolve cost stance from invocation, `config.yaml`, repo guidance, then
   default `full`; disclose source.
5. Use `codex-security:security-scan` when available and app-code vulnerability
   coverage overlaps; otherwise disclose unavailable/not applicable.
6. For Deep, probe GitHub MCP once; on failure record unavailable and continue
   static-only. Never retry.
7. Apply codes only after evidence gates and carve-outs. For the
   same condition, the most-specific applicable loaded rule controls severity;
   suppress its duplicate general code. If separately applicable rules still
   overlap, duplicate overlaps use the highest applicable severity. Separate
   fact from inference; emit output/footer.

## Outputs

- Quick: findings only; no rollup or MCP probes. After Quick findings, emit
  `Quick gate: <status>` with `fail > not-evaluated > pass-limited` precedence:
  fail for a substantiated in-scope `block`; not-evaluated when required evidence
  or machinery cannot rule out blockers; otherwise pass-limited. Warn and info
  never fail the gate, risk tier remains orthogonal, and a clean rerun is
  required after remediation.
- Deep: opens with the Risk plan, then rubric §9 sections 1-12: scope, target levels, stage matrix,
  CICD-SEC scan, smells, positives, provenance, evidence-per-release,
  framework coupling, live-state block, verdict, honest limits.

Findings use `[CODE] type: path:line` with severity (`block`, `warn`, `info`),
stage, evidence, action, citation, **SUT risk tier** ([`materiality.md`](../../docs/audit-reference/materiality.md); cite signal —
auth/secrets/IaC-priv → high), and **Consequence** ([`audit-craft.md`](../../docs/audit-reference/audit-craft.md) §3). Deep worklist
priority is `severity × risk tier` per the §3 table. If none, say so with limits. Every
answer reports extensions, cost stance/source, Codex Security, rubric path, evidence
limits, independence, and assurance level. Deep also reports MCP GitHub, verdict
(`enforcing`, `partial`, `decorative`), and rubric §8 limits.

## Stop Conditions

Stop when scope is missing, sibling ownership dominates, live evidence is absent,
cost-gated findings lack stance, MCP/tool failure would be retried, output would
copy rubric/vendor prose, or confidence is too low.

Rerun obligations after craft or skill-surface changes:
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §8.
