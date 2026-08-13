---
name: ip-hygiene
description: Use when skill, agent, bundled reference, manifest, marketplace/runtime metadata, plugin guidance, or bundled asset edits may touch third-party marks, copied source, licences, assets, or existing IP/source hygiene issues. Focused on plugin and skill publication surfaces; not general legal advice.
---

# IP Hygiene

Evidence-bounded copyright, database-right, trade-mark, licence, and asset
hygiene for plugin and skill publication surfaces. This is not legal advice. It
does not provide legal clearance, does not certify compliance, and does not perform a freedom-to-operate search.
No finding or verdict is legal clearance.

Inputs: the proposed act or current diff; touched paths or review boundary;
source identity and provenance; target repo guidance; the material's actual
licence/version/file notices; intended distribution form and audience; and any
jurisdiction facts supplied by the user. Inspect available repository evidence.
Ask when a load-bearing fact is unavailable; do not infer permission.

## Scope And Load Map

Use this skill for published skills, agents, references, extensions, fixtures,
templates, scripts, assets, plugin manifests, marketplace/runtime metadata, and
repo guidance that describes those surfaces. General repo-wide IP hygiene is future scope.

This skill does not decide patents or freedom to operate, privacy and data protection,
trade secrets, publicity and personality rights, defamation, export controls or
sanctions, competition law, employment ownership, or general contract disputes.
It does not resolve title or give country-specific clearance.
Route those questions to qualified counsel or the owning review path.

Load only the references selected by the evidence:

- source/provenance or an authority dispute: [authority-index.md](references/authority-index.md)
- copied text, code, examples, interfaces, tables, or datasets: [copyright.md](references/copyright.md)
- public marks, names, symbols, logos, affiliation, or branding: [trademark.md](references/trademark.md)
- licences, notices, third-party code, schemas, data, fonts, or media: [licence-assets.md](references/licence-assets.md)
- a pre-existing issue reached through touched content: [drive-by.md](references/drive-by.md)
- scope, remedy, or legal-policy boundary changes: [fence-posts.md](references/fence-posts.md)
- an old link targeting the pre-split router: [ip-hygiene-reference.md](references/ip-hygiene-reference.md)

When changing trigger, workflow, gates, source, or eval behavior, inspect
`references/evals/`, its accuracy corpus, and
[source-grounding.md](references/source-grounding.md). Keep evals synthetic or
originally paraphrased. Build a blind evaluator bundle, then give the evaluator
only that bundle:

`${CLAUDE_SKILL_DIR}/references/scripts/build_ip_hygiene_blind_bundle.py --repo-root <repo-root> --output <empty-bundle-dir>`

In Codex, replace `${CLAUDE_SKILL_DIR}` with the absolute `<skill-dir>` reported
for this loaded `SKILL.md`. The evaluator reads only its assigned bundle and
must structurally validate its actual records with:

`${CLAUDE_SKILL_DIR}/references/scripts/validate_ip_hygiene_actual.py --cases <bundle-dir>/cases.jsonl --actual <actual.jsonl>`

In Codex, replace `${CLAUDE_SKILL_DIR}` with the absolute `<skill-dir>` reported
for this loaded `SKILL.md`. An outside read or expected-outcome exposure is
`blocked:contaminated`, with no results produced or revised. The parent alone
privately scores behavior after receiving actual records:

`${CLAUDE_SKILL_DIR}/references/scripts/score_ip_hygiene_eval.py --cases ${CLAUDE_SKILL_DIR}/references/evals/accuracy-corpus/cases.jsonl --expected ${CLAUDE_SKILL_DIR}/references/evals/accuracy-corpus/expected.jsonl --actual <actual.jsonl> --families <comma-separated-families>`

In Codex, replace `${CLAUDE_SKILL_DIR}` with the absolute `<skill-dir>` reported
for this loaded `SKILL.md`. Structural corpus checks do not establish model
recall; this command compares the separately produced blind results.

## Criteria And Authority

Every conclusion cites one criterion family and classifies the authority it
uses. The authority classes are: binding law, binding-law harmonization source,
operative licence term, holder policy, project convention, and conservative
repository policy. They are not interchangeable: a directive is a
harmonization source until applicable national implementation is established, a
holder request is not legislation, and a repository default does not establish
infringement.

Use these stable criteria families; the loaded reference supplies the numbered
criterion:

- `IP-SRC-*` — source identity, provenance, authority, applicability, and the
  separation between citation and permission.
- `IP-COPY-*` — protected expression, quotation, paraphrase, software, and
  non-text copying.
- `IP-DB-*` — database copyright, protected selection/arrangement, and sui
  generis extraction or re-utilization.
- `IP-LIC-*` — operative licence, covered material and act, notices,
  modifications, combinations, distribution, and special permissions.
- `IP-MARK-*` — referential use, artifact branding, registration, endorsement,
  holder policy, and optional symbol convention.

Conform to [audit-craft.md](../../docs/audit-reference/audit-craft.md) sections
2, 3, and 5, including skepticism, fact-vs-inference, read-only audit stance,
the 5 C's, independence, and the disclosure footer. Apply
[materiality.md](../../docs/audit-reference/materiality.md) to the risk tier;
do not let subject risk change finding severity or gate precedence.

## Select A Lane

The lanes are prospective decision, limited-assurance triage, and
reasonable-hygiene in-depth review.

- **Prospective decision** — the user asks whether or how a specified future
  act can proceed. Test that act against the identified source, audience,
  distribution form, and authority. Return `prospective decision:
  <proceed-with-stated-controls | do-not-proceed | insufficient-evidence |
  counsel-required>` plus the stated decision controls, supporting evidence,
  and limits. State the controlling non-publication step for `do-not-proceed`
  or `counsel-required`; never emit a bare outcome. This is a scoped hygiene
  decision, not clearance.
- **Limited-assurance triage** — a change-scoped or path-scoped review. It does
  not enumerate the whole publication surface. Emit findings, one `triage
  gate:` line, and a limited-assurance footer.
- **Reasonable-hygiene in-depth review** — the user names in-depth/full review,
  repo guidance requires it, or the boundary is a whole plugin/publication
  surface. Enumerate and risk-survey the surface, then emit findings, exactly one
  in-depth verdict, and a `reasonable-hygiene in-depth` footer. Reasonable hygiene is not
  reasonable legal assurance.

If the requested lane or boundary is ambiguous, ask before fieldwork.

## Triage Procedure

When paths are available, first run the read-only objective pre-filter:

`${CLAUDE_SKILL_DIR}/references/scripts/ip-prefilter.sh --format text -- <touched paths>`

Claude Code substitutes `${CLAUDE_SKILL_DIR}` with this skill's installed path.
In Codex, replace it with the absolute `<skill-dir>` reported for this loaded
`SKILL.md`. Execute it as a black box; inspect `references/scripts/` only when
maintaining that machinery.

The pre-filter finds filesystem candidates, not legal conclusions. An empty
result does not rule out marks, copied prose, inline code, or uncertain source
authority. Answer all five questions by judgment:

1. Does a public surface mention or brand with a third-party mark, logo,
   product, organization, or standard?
2. Does the change quote, closely paraphrase, restructure, or copy text?
3. Does it copy code, configuration, an example, interface expression, figure,
   table, schema, fixture, or dataset?
4. Does it bundle or redistribute third-party software, documentation, schema,
   data, font, binary, image, audio, video, logo, SDK, or sample?
5. Does a touched edit reproduce, modify, link, or otherwise propagate a
   pre-existing issue in the same file or source it uses?

All no: emit `nothing to check`. Any yes or unknown: load only the relevant
references and record the evidence gap or finding.

### Triage Gate

Emit exactly one `triage gate: <fail | not-evaluated |
pass-limited>` line after findings or `stopped:` and before the footer. Do not emit this line in in-depth mode.
Do not emit it in the prospective lane either. Apply audit-craft section 4a:

- `fail` only when a substantiated in-scope `block` confirms misleading mark claims or branding,
  unauthorized logos or endorsement implications,
  unlicensed copied expression, missing operative copyright or licence notices,
  or incompatible or restricted bundled content.
- `not-evaluated` when evidence prevents ruling out a block. In particular,
  unclear source authority, holder policy, or redistribution terms are
  `not-evaluated` unless a confirmed blocker already makes the gate `fail`.
  Missing operative licence, jurisdiction/applicability, or other required
  evidence follows the same rule.
- `pass-limited` otherwise. Ordinary mark-symbol, grammar, or optional-attribution convention issues are
nonblocking unless loaded authority makes them distribution-critical: preserve
their underlying `warn` or `info` severity.

A remediated blocker requires a clean triage rerun before `pass-limited`.

### Classification Decision Boundaries

Use these mechanical boundaries before assigning severity and the lane outcome:

- Unsupported registration or endorsement claims that the supplied evidence
  establishes as false are misleading mark claims: record a `block` and
  `fail`. A requested symbol or presentation convention that is not a
  distribution condition remains `warn` or `info` and `pass-limited`.
- Known copied expression with no supplied permission may be blocked by
  conservative repository policy without asserting infringement; citation or
  paid access is not permission. Similarity without a settled copying basis,
  or a result that depends on missing exception/applicability facts, is a
  `warn` and `not-evaluated`, never `pass-limited` while a block cannot be
  ruled out.
- A drive-by candidate outside the bounded publication act still receives an
  `IP-SRC-4` deferred observation. It does not fail the in-scope gate when the
  stated act neither edits, builds, links, nor distributes it.
- A documented preference for later or broader counsel review is
  `recommended` when the present hygiene decision is complete; it does not
  become `required` and does not change the gate or verdict.

Classify the proposition actually stated in the finding. A directly observed
source fact remains a fact; an application of a legal category, protection,
likelihood, exception, or disputed merits proposition is an inference. When a
record needs both, split the findings or write the condition so its
`fact | inference` label is unambiguous. For database rights, a potential
Directive category is a binding-law harmonization-source inference until
operative national law and applicability are established; a separate stop
based only on missing permission or law may instead be a factual conservative
repository-policy finding.

## In-Depth Procedure And Verdict

1. Enumerate every in-scope publication surface and the distribution forms it
   produces. Record exclusions.
2. Survey risk before catalog work; prioritize public names/branding, bundled
   or vendored material, notices, generated packages, and copied documentation.
3. Run the pre-filter over the full enumeration, then apply all five triage
   questions per surface and all hit criteria.
4. Corroborate source identity, actual file-level licence, holder policy, and
   jurisdiction/applicability. Mark static conclusions as inference. At scale,
   sample and project under audit-craft section 6 and disclose the basis.
5. Emit findings and exactly
   `in-depth verdict: <blocked | qualified | no-blocker-identified>`:
   - `blocked` — a substantiated blocking condition or mandatory counsel
     escalation prevents a repository hygiene decision;
   - `qualified` — no substantiated block remains, but findings or material
     evidence/sampling limitations qualify the result;
   - `no-blocker-identified` — sufficient appropriate evidence over the stated
     surface identified no blocking criterion. It does not mean clean,
     non-infringing, compatible, or cleared.

Every in-depth result names the reviewed surface, exclusions, supporting
evidence, and limits, including an explicit `none` where there are no
exclusions. A verdict without that boundary evidence is incomplete.

## Finding And Remediation Contract

Audits are read-only by default. Emit one structured `finding:` record per
issue. Each record must contain:

- criterion and authority class;
- condition and exact location;
- source identity and provenance;
- intended act — mention, link, quote, copy, modify, aggregate, link/import, execute, or redistribute;
- distribution form and audience;
- jurisdiction and applicability;
- fact or inference, confidence and evidence;
- cause, consequence, recommendation, severity, risk tier, and counsel outcome.

Ground the lane evidence and each finding in at least one distinctive source,
material, path, quantity, or quoted claim from the reviewed facts. Equivalent
paraphrase is acceptable; generic phrases such as `case evidence` are not.

`counsel outcome` is `not-triggered`, `recommended`, or `required`, with the
trigger stated. Use `recommended` only for a documented, non-mandatory
risk-management referral when the hygiene decision can be completed from the
available evidence and no mandatory stop below applies. It does not change the
finding severity, gate, verdict, or decision, and it is never a substitute for
missing load-bearing evidence. Use `not-triggered` when neither that prudent
referral nor a mandatory trigger is evidenced. A no-finding run emits `nothing to check` or `checked: <reviewed criterion codes and surfaces>; no IP hygiene changes needed`;
neither is clearance.

Only an explicit fix request authorizes repairs. Keep audit findings unchanged,
make the requested bounded repair, and add a separate `remediated:` record with
the finding ID, changed location, action, authority used, and verification. A
fresh rerun is required for a new gate or verdict. Do not reuse a pre-fix result.
The former `fixed: <path:line> - <remedy summary> [<severity>|<risk tier>];
consequence: <effect if unaddressed>` form is retired in favor of `remediated:`.

For an out-of-bound drive-by issue, preserve the compact observation:
`deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit [<severity>|<risk tier>]`,
and include its full finding data.

## Counsel Escalation And Stops

Set `counsel outcome: required`, stop the affected decision, and do not propose
legal conclusions for a live or threatened dispute; a cease-and-desist or other
demand; a bespoke agreement; contested ownership; unresolved combined-work or copyleft classification;
country-specific clearance; or reliance on a disputed exception. The unaffected
review boundary may continue if it remains separable.

Classify a counsel-only stop from the evidence that supports the stop. When the
facts establish only the dispute, demand, bespoke agreement, contested title,
unresolved classification, country-specific request, or disputed exception,
record a `warn` under conservative repository policy and do not promote it to a
`block`, binding-law conclusion, holder-policy breach, or operative-licence
conclusion. A separate merits finding requires separate substantiating evidence.

Also stop the affected decision when source identity, authority, licence text,
holder policy, intended act, distribution form/audience, or
jurisdiction/applicability is load-bearing and unknown; a remedy would delete a
load-bearing reference; or the question falls outside the declared scope. State
the exact missing fact. Never turn absence of evidence into permission or a
block.

## Disclosure And Verification

Every output ends with the audit-craft section 5 footer: extensions loaded;
tool/MCP availability; reference paths and authority classes; evidence limits
(for triage, touched paths plus drive-by neighbors examined and untouched files
not swept); independence (`independent | self-review | unknown`); and assurance
level (`prospective bounded decision | limited triage | reasonable-hygiene
in-depth`). Restate that the result is not legal advice, clearance,
certification, or an FTO opinion.

After editing this skill or references in the marketplace source repo, run its
focused tests and `scripts/skill-architecture-report.sh .` from the clean task
worktree. When editing `authority-index.md`, spot-check affected primary-source
links and report verification limits.
