# Extensions

Per-stack routing cards loaded on demand by the devsecops-audit skill. The core
workflow in `../SKILL.md` is framework-neutral; these files keep the trigger
surface light and point to full rule packs under
`../../../docs/security-reference/devsecops-extensions/`.

## Load order

1. The skill detects target type(s) by globbing the audit target.
2. Every matching routing card is loaded.
3. The linked full rule pack is loaded before emitting extension-specific codes.
4. Each extension's smells, positive signals, and carve-outs are added to the active rubric.
5. On conflict between a carve-out and a core smell, the carve-out wins — but only for the exact pattern described.

Extensions **never override** core rules. They may only **add** or **carve out**.

## File layout per extension

Each extension file in this directory is intentionally short. Required content:

- Detection signals.
- Link to the full rule pack under `docs/security-reference/devsecops-extensions/`.
- Code namespace and high-level concern set.
- Any cost-stance routing note.

## Current extensions

| File | Applies to | Notes |
|---|---|---|
| `github-actions.md` | `.github/workflows/*.yml` | CI workflow routing; full `gha.*` rules in docs |
| `bicep.md` | `infra/**/*.bicep` | Azure IaC routing; Band 1/Band 2 `bicep.*` rules in docs |
| `dockerfile.md` | `**/Dockerfile`, `**/docker-compose*.yml` | Container routing; full `docker.*` rules in docs |
| `dotnet-security.md` | C# under `api/` `app/` `shared/` `tests/` | .NET security routing; full `dns.*` rules in docs |

## Cost banding

Extensions that cover Azure resources (currently `bicep.md`) split their smell codes into two bands by remediation cost:

- **Band 1 — always-block.** Remediation is free or near-free (config toggle, IaC edit). Fires under all cost stances.
- **Band 2 — cost-gated.** Remediation requires a paid Azure SKU. Fires only under `costStance: full` or when explicitly listed in `mixedEnabled`.

See `../references/procedures/cost-stance-detection.md` for how the stance is resolved.

## Adding a new extension

1. Copy one of the existing routing cards as a template.
2. Pick a short name prefix (e.g. `tf` for Terraform, `k8s` for Kubernetes).
3. Add detection signals.
4. Add the full rule pack under `../../../docs/security-reference/devsecops-extensions/`.
5. Add smell codes, namespaced with your prefix.
6. Add the extension to the catalog at `../../../docs/security-reference/devsecops-smell-catalog.md`.
7. Add the extension to the table above.
8. Update `../SKILL.md` with the new detection mapping.
9. If the extension covers Azure (or any other cloud with paid security SKUs), split its codes into Band 1 / Band 2 / positive.
