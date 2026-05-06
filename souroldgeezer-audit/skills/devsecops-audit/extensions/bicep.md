# Bicep Extension

Load this routing card when audit targets include `*.bicep`, `*.bicepparam`,
`targetScope`, Bicep modules, or Azure resource declarations.

Full rules: [../../../docs/security-reference/devsecops-extensions/bicep.md](../../../docs/security-reference/devsecops-extensions/bicep.md)

Adds `bicep.*` findings and positives for Azure IaC controls. Band 1 findings
always apply; Band 2 findings require the resolved cost stance from
[../references/procedures/cost-stance-detection.md](../references/procedures/cost-stance-detection.md).
Apply the full rule file before emitting Bicep codes or carve-outs.
