# IP Hygiene Prospective Decision

Load this before deciding a prospective act, per
[SKILL.md § Select A Lane](../../SKILL.md). Triage and in-depth review do not
load it.

## Outcome Contract

Test that act against the identified source, audience, distribution form, and
authority. Return `prospective decision:
<proceed-with-stated-controls | do-not-proceed | insufficient-evidence |
counsel-required>` plus the stated decision controls, supporting evidence,
and limits. State the controlling non-publication step for `do-not-proceed`
or `counsel-required`; never emit a bare outcome. This is a scoped hygiene
decision, not clearance.
