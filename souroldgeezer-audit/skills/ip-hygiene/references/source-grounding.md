# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the original internal IP hygiene workflow and references. They do not copy
legal source text, vendor policies, issue text, examples, schemas, tables, or
external docs.

- Source: `souroldgeezer-audit/skills/ip-hygiene/SKILL.md`.
  Handling: local repo-authored workflow; eval prompts exercise the triage
  contract, false-positive rejection, false-negative rejection, configurable
  conventions, focused scope, and stop conditions.
- Source: `souroldgeezer-audit/skills/ip-hygiene/references/{copyright,trademark,licence-assets,drive-by}.md`.
  Handling: local operational rules; eval prompts paraphrase decision
  categories and do not reproduce legal authority text.
- Source: `souroldgeezer-audit/skills/ip-hygiene/references/authority-index.md`.
  Handling: URL-level source notes only; eval prompts do not copy legal source
  language or vendor policy text.
- Source: `souroldgeezer-audit/docs/audit-reference/audit-craft.md` and
  `souroldgeezer-audit/docs/audit-reference/materiality.md`.
  Handling: local bundled references owned by this repo; eval cases exercise
  audit craft and materiality output contracts and do not reproduce rubric prose.
- Source: `souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/`.
  Handling: repo-authored planted-defect fixtures scoring recall and
  false-positive rate. Forty-two cases cover each coded criterion family and every
  individual code, all three lanes, every prospective and in-depth outcome,
  ambiguity, every counsel-outcome enum, all counsel-required stops, and clean controls. Expected records
  are withheld from blind evaluators. Every prompt instead gives distinct,
  wholly fictional material, provenance, intended act/distribution, the
  explicitly requested lane, and the scenario's ambiguity or counsel-trigger
  facts. Blind input uses opaque case IDs, omits family labels, and does not
  name an expected code, authority class, or decision. The deterministic scorer
  checks required alternative-code groups, correlated allowed codes, severity,
  every authority class (including the distinction between harmonization
  sources and operative binding law), lane/verdict, fact status, counsel, and
  clearance overclaim. Parent-held case anchors require the evaluator's lane
  evidence and every individual finding to identify at least one distinctive
  fact from its assigned case; generic placeholders fail. Independently
  required propositions also carry private code-group-specific
  condition/location anchors, preventing one planted condition from grounding
  another while keeping genuine alternative codes together only inside the
  same proposition group. Mixed fact/inference codes carry private factual
  proposition anchors; fact-only codes remain bound to their case anchors. The
  scorer makes legal-category, protected-status, exception, likelihood,
  infringement, and disputed-merits propositions inference-only. Directly
  observed content, provenance, evidence, and explicit factual conservative
  repository-policy propositions remain eligible for `fact`. The scorer also
  validates the complete expected schema and its exact
  identity match with the assigned case corpus before behavioral scoring.
  Structural completeness is not evidence of model recall. No content is
  copied from a real source. Blind evaluators receive only the deterministic
  allowlisted bundle: raw cases, the public workflow, directly required local
  references, instructions, and coverage-aware structural validator. Expected records,
  parent scoring, source grounding, repository tests/history, prior diagnoses,
  and evaluator caches remain outside that bundle. The child validates output
  structure and exact assigned-case coverage only; the parent privately scores
  behavior and rejects unexpected case IDs even under a family filter.

Residual limit: isolation is not a sandboxing guarantee. The harness injects
this repo's own guidance (`CLAUDE.md`, `README.md`, `AGENTS.md`, plus agent
memory) into every subagent regardless of the bundle, and that injected
context reaches the evaluator before it ever reads
`EVALUATOR_INSTRUCTIONS.md`. Nothing inside this skill can prevent that
delivery order. Isolation instead rests on two things together: the
instruction to read only the assigned bundle, and a deterministic gate
(`tests/ip_hygiene_blind_bundle_test.py`) asserting the injected guidance
files carry no corpus case ID and no distinctive case material, the latter
derived from the corpus's own evidence anchors rather than a second list. That gate
keeps today's injected context non-contaminating; it does not sandbox the
evaluator, and a future edit to those guidance files could still contaminate
a run if it slips past the gate.
