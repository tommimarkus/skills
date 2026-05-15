# Source Evidence Evaluator

Use this architecture-design reference as the first-pass evaluator when source
evidence permits multiple valid ArchiMate element, relationship, or view
choices. It distills the research sources into weighted source-evidence lanes:
the heaviest applicable lane shapes the initial interpretation, then local
evidence, architect intent, ArchiMate semantic validation, and render/readability
evidence confirm or reject that interpretation.

This workflow is ArchiMate 3.2 based. Do not import ArchiMate 4 language until
the skill, fixtures, validation, and exports upgrade together.

## Evaluation Order

1. Preserve explicit local source evidence and architect intent.
2. Reject ArchiMate 3.2 semantic invalidity.
3. Apply the heaviest applicable evidence lane below.
4. Let lower-weight exact-domain evidence refine, not erase, higher-weight
   defaults.
5. Refine for view concern, readability, SVG/render evidence, and disclosure.

## Evidence Lanes

| Weight | Lane | Sources | Evaluates |
|---:|---|---|---|
| 44 | Standards/method | The Open Group, Lankhorst, ISO 42010 | Stakeholder concern, viewpoint fit, abstraction level, ArchiMate semantics, conformance boundary, and inventory pressure. |
| 34 | Practical notation/readability | Wierda, Hosiaisluoma, Bizzdesign | Application Component/Service/Interface/Function choices, relationship narrowness, API/GUI access-surface handling, cooperation readability, and split-view pressure. |
| 14 | Enterprise practice | MIT CISR, IASA BTABoK | Business Capability, Value Stream, Goal, Outcome, Course of Action, decision, stakeholder, and quality-attribute claims when architect intent or business-source evidence exists. |
| 8 | Artifact/platform overlays | Kotusev/EA on a Page, SAP LeanIX, Microsoft CAF, AWS WA | Useful artifact size, portfolio/cloud governance overlays, landing-zone/cost/reliability/platform-quality context; never generic ArchiMate classification authority. |

## Scoring Rules

- Standards/method wins the first reading unless local source evidence is
  explicit, architect intent says otherwise, or semantic validation rejects it.
- Practical notation/readability is the main classifier for source-extracted
  Application-layer and relationship choices.
- Enterprise practice cannot create business architecture from code, IaC, or
  cloud names alone; mark richer claims `architect-owned` or `weak-evidence`.
- Platform guidance is overlay evidence only. Azure/AWS/CAF/WA evidence may
  explain hosting or operational concern, not decide generic ArchiMate type.
- Use semantic Grouping only for evidenced responsibility, trust, participant,
  environment, ownership, hosting, or orchestration boundaries; layout grouping
  stays in view/render metadata.

For non-obvious choices, output: source fact, plausible candidates, selected
concept/relation/view, weighted reason, rejected alternative, confidence.

## Source Anchors

These anchors identify the public sources distilled into the evaluator. Confirm
live only when the source is load-bearing for the current decision.

| W | Source | Anchor |
|---:|---|---|
| 18 | The Open Group: ArchiMate, TOGAF, ArchiSurance | `https://publications.opengroup.org/archimate-library`; `https://help.opengroup.org/hc/en-us/articles/32115987894930-How-the-ArchiMate-Language-and-the-TOGAF-Standard-Complement-Each-Other` |
| 14 | Marc Lankhorst | `https://link.springer.com/book/10.1007/3-540-27505-3` |
| 13 | Gerben Wierda | `https://ea.rna.nl/mastering-archimate-edition-3-2/`; `https://ea.rna.nl/archimate/free-archimate-overview-pdf/` |
| 12 | ISO/IEC/IEEE 42010 | `https://www.iso.org/standard/74393.html` |
| 11 | Eero Hosiaisluoma | `https://www.hosiaisluoma.fi/ArchiMate-Cookbook.pdf` |
| 10 | Bizzdesign | `https://resources.bizzdesign.com/blog/practical-archimate-viewpoints-for-the-application-layer`; `https://bizzdesign.com/blog/an-overview-of-the-levels-of-abstraction-in-enterprise-architecture` |
| 8 | MIT CISR | `https://cisr.mit.edu/content/classic-topics-enterprise-architecture` |
| 6 | IASA BTABoK | `https://iasa-global.github.io/btabok/index.html` |
| 5 | Kotusev / EA on a Page | `https://eaonapage.com/`; `https://kotusev.com/` |
| 3 | SAP LeanIX, Microsoft CAF, AWS WA | `https://www.leanix.net/en/products/application-portfolio-management`; `https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/overview`; `https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html` |
