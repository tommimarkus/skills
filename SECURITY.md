# Security Policy

## Supported versions

Security fixes target the current `main` branch and the latest published
version of each plugin listed in [README.md](README.md). Older plugin versions
may remain vulnerable; backports are best effort and are announced explicitly
when made.

## Report a vulnerability

The chosen private channel is GitHub private vulnerability reporting for
[`tommimarkus/skills`](https://github.com/tommimarkus/skills/security/advisories).
Its enablement is **pending and not yet verified**. Use **Report a
vulnerability** only when that button is visible on the repository's Security
page.

If the private form is unavailable, do not put exploit details, credentials,
private repository content, or a proof of concept in a public issue. No public
fallback address is declared. A public issue may ask the maintainer to enable or
name a private channel without disclosing the vulnerability. Ordinary,
non-sensitive hardening requests may use the public issue tracker.

Include the affected plugin and version or commit, host and operating system,
impact, reproduction steps, and any suggested mitigation. Remove credentials
and unrelated private data. Please allow coordinated disclosure while the
report is assessed and a fix is prepared.

## Response targets

The maintainer uses these best-effort targets:

- initial triage and acknowledgement within 7 calendar days;
- mitigation or repair for a confirmed critical issue within 7 calendar days
  of confirmation; and
- mitigation or repair for a confirmed high-severity issue within 30 calendar
  days of confirmation.

Impact, exploitability, affected users, and available mitigations determine
severity. These targets are not a service-level agreement. The maintainer
tracks exceptions and tells the reporter when a target will be missed or the
assessment changes.

Security fixes follow the repository's normal version and local-publication
gates. Where disclosure is safe, the maintainer records the affected surface,
fixed version, and update action in the release communication or advisory, and
notifies the private reporter. This project offers no vulnerability bounty.

## Security posture

The marketplace threat model, controls, assurance targets, gaps, and accepted
residual risks are documented in [docs/security-baseline.md](docs/security-baseline.md).
That document declares OWASP SCVS Level 1 as a target, not attained
conformance, and makes no SLSA level claim.
