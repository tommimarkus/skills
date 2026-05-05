# Infra-Design Source Grounding

This skill exists because infrastructure design sits between code-level design,
API design, architecture modeling, and security audit work. Agents need a
dedicated workflow for IaC boundaries, environment promotion, state, rollout,
and operations handoff without stretching `software-design`, `api-design`,
`architecture-design`, or `devsecops-audit`.

The first extension set is Azure, Terraform, and Bicep because the approved
design asked for a core infrastructure skill plus immediate platform/IaC
overlays. The extensions are intentionally narrow: they add detection signals,
source anchors, design defaults, and finding namespaces, but they do not replace
the generic infrastructure-design core.

Source handling:

- Trigger and behavior cases are synthetic and originally phrased.
- Platform facts in extensions should link to official vendor documentation and
  be paraphrased in original wording.
- Do not copy vendor examples, generated provider docs, code samples, schemas,
  diagrams, or tables into the plugin bundle.

Boundary pressure cases:

- A request about endpoint contracts should route to `api-design`.
- A request about code/module/script shape should route to `software-design`.
- A request about ArchiMate/OEF diagrams or code-to-architecture drift should
  route to `architecture-design`.
- A request about secrets, least privilege, supply chain, or pipeline hardening
  should route to `devsecops-audit`.
- A request about unit, integration, or E2E test quality should route to
  `test-quality-audit`.
