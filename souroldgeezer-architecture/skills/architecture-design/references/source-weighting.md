# Source-Weighted Selection

Use this when source evidence allows more than one plausible ArchiMate element,
relationship, or view shape. It is a tie-breaker below local evidence,
architect intent, and `validate --plugin generic-graph --profile archimate`.

## Gate

The package workflow is ArchiMate 3.2 based. As of 2026-05-16, The Open Group
library also lists ArchiMate 4 materials; do not import ArchiMate 4 language
changes until this skill, fixtures, dediren validation, and exports are upgraded
together.

Decision order:

1. Preserve explicit source evidence and architect intent.
2. Reject ArchiMate 3.2 semantic invalidity.
3. Apply the weighted guidance below.
4. Refine for view concern, readability, and SVG/render evidence.

## Quality Bar

The user-facing result must be source-backed, semantically valid, readable, and
explainable. When a modelling choice is non-obvious, do not just emit the chosen
element or relation. Carry a compact rationale:

- source fact or architect intent used;
- plausible ArchiMate candidates considered;
- chosen element/relation/view shape and why the weighted guidance favors it;
- rejected alternative when it is likely a reviewer would ask about it;
- confidence: `source-backed`, `architect-owned`, or `weak-evidence`.

If evidence is weak, choose the least specific valid concept, mark the richer
claim architect-owned, or ask the user. Do not manufacture Business,
Motivation, Strategy, ownership, lifecycle, or cloud-quality claims from code
or IaC naming alone.

## Weighted Guidance

The researched sources are not equal. Let higher-weight lanes control default
wording and modelling choices; use lower-weight lanes only in their domain.

**44 points: standards, origin, and architecture-description discipline**

The Open Group, Lankhorst, and ISO 42010 drive the default stance: model the
stakeholder concern, keep abstraction levels deliberate, and prefer a valid
ArchiMate concept whose semantics match the evidence. A diagram should answer a
viewpoint question; it should not become a complete inventory because the source
repository contains many facts. Official examples and method guidance are strong
sanity checks, but do not override local evidence or semantic validation.

**34 points: practical ArchiMate selection and readability**

Wierda, Hosiaisluoma, and Bizzdesign supply the strongest practical
classification defaults:

- Application Component: application unit, product, module, deployable app, or
  owned application boundary.
- Application Service: exposed application behavior, capability offered by an
  application, or functional dependency between consumers and providers.
- Application Interface: concrete access point such as GUI, API, app-to-app
  interface, or operation surface.
- Application Function/Process: internal behavior only when that behavior is
  the view concern; ordinary dependency views usually stop at component,
  service, interface, and data object.
- Serving, Access, Assignment, Composition, Aggregation, Flow, and Triggering:
  use the narrowest relationship that says what the source proves. Avoid Flow
  or Triggering for every message when the view is really about cooperation or
  dependency.
- Split views when viewpoint scope, abstraction level, or route density makes a
  diagram hard to read.

**14 points: enterprise-practice context**

MIT CISR and IASA guide business context, not low-level notation. Use Business
Capability, Value Stream, Goal, Outcome, Course of Action, decision, or quality
attribute framing only when there is architect intent or business-source
evidence. Do not infer business architecture forward from code, IaC, or cloud
resources alone.

**8 points: artifact discipline and platform overlays**

Kotusev is the counterweight against giant all-purpose EA artifacts: prefer a
small useful landscape, outline, decision, standard, or design view over an
attempted complete enterprise book. SAP LeanIX, Microsoft CAF, and AWS
Well-Architected are overlays only; use them for portfolio lifecycle, cloud
governance, landing-zone, cost, reliability, and platform quality concerns when
the source system is actually SAP LeanIX, Azure, or AWS. They do not decide
generic ArchiMate classification.

## Conflict Rules

- If a higher-weight lane conflicts with a lower-weight lane, use the
  higher-weight lane unless the lower-weight source is the only one in the
  exact domain.
- If practitioner guidance conflicts with semantic validation, validation wins
  and the finding should explain the rejected modelling choice.
- If source evidence is weak, choose the least specific valid element and mark
  architect-owned intent instead of inventing a richer business or strategy
  model.
- Use semantic Grouping only for evidenced responsibility, trust, participant,
  environment, ownership, hosting, or orchestration boundaries. Layout grouping
  belongs in view/render metadata.

## Source Anchors

Follow the anchor when a decision needs live source confirmation.

| W | Source | Lane | Anchor |
|---:|---|---|---|
| 18 | The Open Group: TOGAF, ArchiMate, ArchiSurance | Standards and official method/examples. | `https://publications.opengroup.org/archimate-library`; `https://help.opengroup.org/hc/en-us/articles/32115987894930-How-the-ArchiMate-Language-and-the-TOGAF-Standard-Complement-Each-Other` |
| 14 | Marc Lankhorst | Modelling heuristics, viewpoints, abstraction. | `https://link.springer.com/book/10.1007/3-540-27505-3` |
| 13 | Gerben Wierda | Practical patterns, anti-patterns, notation nuance. | `https://ea.rna.nl/mastering-archimate-edition-3-2/`; `https://ea.rna.nl/archimate/free-archimate-overview-pdf/` |
| 12 | ISO/IEC/IEEE 42010 | Stakeholders, concerns, viewpoints, model kinds. | `https://www.iso.org/standard/74393.html` |
| 11 | Eero Hosiaisluoma | Application/service/interface/API/GUI choices. | `https://www.hosiaisluoma.fi/ArchiMate-Cookbook.pdf` |
| 10 | Bizzdesign | Viewpoint restriction, abstraction, cooperation readability. | `https://resources.bizzdesign.com/blog/practical-archimate-viewpoints-for-the-application-layer`; `https://bizzdesign.com/blog/an-overview-of-the-levels-of-abstraction-in-enterprise-architecture` |
| 8 | MIT CISR | Operating model, standardization/integration, capability framing. | `https://cisr.mit.edu/content/classic-topics-enterprise-architecture` |
| 6 | IASA BTABoK | Practice, stakeholders, decisions, quality attributes. | `https://iasa-global.github.io/btabok/index.html` |
| 5 | Kotusev / EA on a Page | Artifact usefulness and anti-inventory pressure. | `https://eaonapage.com/`; `https://kotusev.com/` |
| 3 | SAP LeanIX, Microsoft CAF, AWS WA | Portfolio/cloud overlays only. | `https://www.leanix.net/en/products/application-portfolio-management`; `https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/overview`; `https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html` |
