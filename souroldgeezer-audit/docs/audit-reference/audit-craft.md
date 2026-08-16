# Audit Craft (shared core)

Canonical audit discipline + shared output contracts for every skill in this
plugin. Domain skills CITE sections here (e.g. "see audit-craft.md §3") and add
their rubric/namespace on top; they never restate this prose. Conformance is by
named principle, not one rigid template — `ip-hygiene` maps to §2/§3/§5 without
adopting §4's Quick/Deep names.

## §1 What an audit is

Control vs subject matter: the audited artifact (test suite, pipeline, IP
surface) is a CONTROL; the thing it protects is the SUBJECT MATTER; an audit
skill provides assurance OVER that control. An audit is not an inspection or a
linter: it forms a graded, evidence-weighted opinion against cited criteria.
Assurance is reasonable (high, positive — Deep) or limited (negative,
inspect-only — Quick/triage). Absolute assurance is impossible; disclose limits.

## §2 Principles

- Criteria-citation: every finding cites a code/section; no bare opinion.
- Professional skepticism: assume the subject may be wrong; corroborate;
  seek contradiction (hunt for controls that cannot fail).
- Evidence sufficiency/appropriateness: re-performance/observed behavior >
  entity-asserted (names, comments, badges).
- Positive control before absence: when measuring what a suppression/exemption
  layer hides by stripping its markers, registry, or config, first prove the
  detector still fires under that instrumentation, and never let the
  instrumentation edit the detector's own source or a restore path that also
  holds instrumented data. Without the control, an unchanged count is
  indistinguishable from a detector you disabled, and the delta reads as
  evidence of absence.
- Fact vs inference: mark inferred or static-only conclusions as inference
  requiring verification; do not present them as confirmed fact.
- Materiality: weight by consequence of the subject being wrong (see materiality.md).
- Plan from risk before fieldwork: a Deep audit opens with a risk survey
  (enumerate the subject, tier per materiality.md, prioritize the highest-risk
  surface) before applying the catalog. Domain-best-fit: test-quality enumerates
  the SUT surface; devsecops threat-models crown jewels / trust boundaries /
  attacker goals. Catalog-first with no survey is a Quick shape — disclose it.
- Independence / self-review: disclose when the auditor authored the audited
  artifact this session; prefer a separate pass. Enum: independent | self-review | unknown.
- False-positive discipline: one finding per item; substantiate or downgrade.
- Read-only audit stance: an audit skill reads and assesses; it does not
  auto-fix the artifact unless explicitly directed. Separate audit from repair.
- Stop on ambiguity: when evidence is insufficient to form an opinion, disclose
  the gap and stop; never fabricate certainty. Prefer asking over guessing.

## §3 Finding contract (the 5 C's)

Every finding carries: criteria (cited code) · condition (evidenced location) ·
cause · consequence (Effect — what ships undetected if this is the only guard) ·
recommendation/action · severity (block | warn | info). Severity rates the
CONTROL weakness. Risk tier (high | medium | low | unknown, see materiality.md)
is an ORTHOGONAL axis rating the SUBJECT. Combine only at the remediation
worklist via this priority mapping:

| severity \ risk | high | medium | low | unknown |
|---|---|---|---|---|
| block | P0 | P1 | P2 | P1 |
| warn  | P0 | P1 | P2 | P1 |
| info  | P1 | P2 | P3 | P2 |

## §4 Mode contract

Quick/triage = limited assurance: per-finding output only, no enumeration or
rollup. Deep/in-depth = reasonable assurance: enumerate the subject surface,
roll up, sample+project at scale (§6), emit a graded verdict. Every output
states its assurance level on one line.

## §4a Bounded-lane gate

A bounded-lane gate is a mechanical status check, not a rollup or
reasonable-assurance verdict. It supplements the limited-assurance finding
output; it does not change Deep, in-depth, or full-repo behavior.

- `test-quality-audit` and `devsecops-audit` use `Quick gate: <status>`.
- `ip-hygiene` uses `triage gate: <status>`.
- `lean-audit` uses `limited-scope gate: <status>` for a bounded scope.

Status precedence is `fail` if any substantiated in-scope `block` exists;
otherwise `not-evaluated` when required evidence or machinery cannot rule out
blockers; otherwise `pass-limited`. Warn and info findings never make this gate
fail. A remediated block needs a clean rerun before the gate can pass. Subject
risk tier remains orthogonal (§3): it prioritizes remediation but does not
change the gate status.

## §5 Disclosure-footer contract

Every audit output ends with a footer reporting: extensions loaded · tool/MCP
availability · reference path(s) · evidence limits · independence · assurance
level. Domain skills append a domain-extras slot (cost stance, project
assimilation, etc.). Never remove footer fields.

## §6 Sampling and projection

See sampling-projection.md. At scale, risk-target the sample, disclose size and
basis, and project local findings to the population as inference.

## §6a Scaled audits

See scaled-audit.md — the rung before §6. Hold per-item evidence in bounded
records, delegate divisible lanes when the host offers delegation while keeping
population lanes with the parent, and disclose the rung used plus the coverage
reconciliation.

## §7 Extension pattern

Extensions ADD namespaced codes or CARVE OUT a core code for an exact idiomatic
pattern. Extensions never override core rules.

## §8 Maintenance

Behavioral evals are synthetic and repo-authored (source-grounding per skill).
Keep two evidence kinds: (1) synthetic behavior/trigger evals prove routing and
behavior; (2) a recall-calibrated accuracy corpus proves finding accuracy — that
the skill catches what is present and does not flag what is not. Every audit
skill SHOULD maintain a domain-best-fit accuracy corpus, scored for recall and
false-positive rate after any rubric / dispatch / output-contract / smell-catalog
/ extension change. Ground truth is domain-best-fit: test-quality hand-labels
snippets (no external oracle exists); devsecops plants objectively verifiable
defects (seeded secrets, known-CVE / CISA-KEV recall). A skill that measures only
triggering/behavior, never recall, has no audit-of-the-audit. After any craft
change or skill-surface edit in the marketplace source repo, rerun its
`scripts/skill-architecture-report.sh .` (repo tooling, not bundled with the
installed plugin).
