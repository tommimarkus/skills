# JavaScript/TypeScript Security Extension

Load this routing card when audit targets include JavaScript, TypeScript, React,
Node.js, or Vite source/configuration that can receive or publish data.

Full rules: [../../../docs/security-reference/devsecops-extensions/jsts-security.md](../../../docs/security-reference/devsecops-extensions/jsts-security.md)

Adds `jsts.*` findings and positive signals only with visible trust-boundary/taint-path evidence; API names alone are not findings. Keep
deployment controls and established project policy primary; report static limits
for bundled output, DNS resolution, and actual listener reachability.

This is a security lens. Delegate module design to `software-design`, HTTP/API
contracts to `api-design`, frontend behavior to `app-design`, and test quality
to `test-quality-audit`.
