# Python Security Extension

Load this routing card when audit targets include `*.py`, Python web handlers,
jobs, CLIs, libraries, or dependency/runtime files that execute Python.

Full rules: [../../../docs/security-reference/devsecops-extensions/python-security.md](../../../docs/security-reference/devsecops-extensions/python-security.md)

Adds `pys.*` findings and positive signals for Python security sinks, but only
when the full pack's visible trust-boundary/taint-path evidence rule is met.
Variable names alone are not provenance. Report static limits for resolved
network destinations, archive resources, and unknown producers; keep the
project's declared controls and deployment context primary rather than making
framework or tool choices prescriptive.

This is a security lens only. Delegate Python module/package design to
`software-design`, HTTP/API contracts to `api-design`, and test quality to
`test-quality-audit`.
