# GitHub Actions Extension

Load this routing card when audit targets include `.github/workflows/*.y?ml`,
reusable workflows, or composite/Docker/Node action metadata.

Full rules: [../../../docs/security-reference/devsecops-extensions/github-actions.md](../../../docs/security-reference/devsecops-extensions/github-actions.md)

Adds `gha.*` findings and positives for CI/CD flow control, token permissions,
pinning, dangerous triggers, shell injection, reusable workflow pinning,
self-hosted runners, job timeouts, OIDC, and production environment gates. Apply
the full rule file before emitting `gha.*` codes or carve-outs.
