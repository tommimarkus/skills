# Threat-Model Planning

Deep-mode planning step, run BEFORE the anti-pattern and smell scans. Realizes
[audit-craft.md §2](../../../../docs/audit-reference/audit-craft.md) (plan from risk before fieldwork)
for security. Cites rubric §3 "what to threat-model"; adds no rubric prose.

## Procedure
1. Enumerate **crown jewels** — secrets/credentials, production deploy paths,
   release-signing identity, data stores crossing a classification boundary.
2. Enumerate **trust boundaries** — untrusted PR → privileged runner, third-party
   action/template → secrets, build input that is not a pinned digest, fork →
   `pull_request_target`.
3. Enumerate **attacker goals** (STRIDE-lite) — secret exfiltration, pipeline
   poisoning, artifact tampering, privilege escalation via over-scoped tokens.
4. **Prioritize**: rank pipelines/stages by (crown-jewel exposure × reachability).
   Direct enumeration and MCP-probe budget high-rank-first; risk-tier findings
   per materiality.md accordingly.

## Output: Risk plan block (feeds the §9 report)
```text
Risk plan:
  Crown jewels:      <list>
  Trust boundaries:  <list, highest-risk first>
  Priority order:    <pipelines/stages, descending risk>
```
Ungroundable assets/boundaries → mark `unknown`, never guessed.
