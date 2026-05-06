# Dockerfile Extension

Load this routing card when audit targets include `Dockerfile`,
`docker-compose*.y?ml`, image-build workflows, or container runtime config.

Full rules: [../../../docs/security-reference/devsecops-extensions/dockerfile.md](../../../docs/security-reference/devsecops-extensions/dockerfile.md)

Adds `docker.*` findings and positives for digest pinning, root users, copied
secrets, privileged compose services, mutable package installs, healthchecks,
non-root execution, and read-only root filesystems. Apply the full rule file
before emitting Docker codes or carve-outs.
