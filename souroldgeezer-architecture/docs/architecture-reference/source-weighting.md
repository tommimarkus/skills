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

## Use During Extract

Use this reference before writing model source when repo evidence can map to
multiple ArchiMate element, relationship, or view choices. The weight is an
extraction prior, not a confidence score: start with the heaviest applicable
lane, reject semantic invalidity, then refine with exact local evidence,
architect intent, and view readability.

For each non-obvious choice, record: source fact, plausible candidates,
selected concept/relation/view, weighted reason, rejected alternative, and
evidence label.

## Source-To-ArchiMate Selection Matrix

| Source evidence | Prefer | Avoid |
|---|---|---|
| Deployable app, module, service host, SPA, Function App, worker, or logical application boundary | Application Component | Business Actor, Capability, or Application Service unless the source proves that concern |
| API route, GUI, SDK, endpoint, queue surface, protocol surface, or access point | Application Interface | Application Service when the concern is the access surface |
| Consumed behavior exposed through an interface, such as lookup, authentication, signup, rendering, notification, or query behavior | Application Service | Application Interface unless the endpoint or access mechanism is the concern |
| Internal handler, algorithm, orchestration step, computation, or module-owned behavior | Application Function; Application Process when ordered behavior/outcome is the view concern | Application Service if the behavior is not exposed or consumed |
| Ordered application behavior with a meaningful outcome | Application Process | Business Process unless business ownership, actor, or stakeholder evidence exists |
| Source-backed workflow with business actor, business outcome, or stakeholder-confirmed process semantics | Business Process candidate | Final Business Process without architect or stakeholder confirmation |
| State change, callback, trigger, timer, queue message, webhook, or deployment occurrence | Application Event, Business Event candidate, or Implementation Event by layer | Process if the evidence only proves a state change |
| DTO, message, database table, persisted logical data, or API payload | Data Object | Business Object unless business meaning is explicit |
| Build artifact, package, container image, deployable file, or IaC-produced unit | Artifact or Deliverable by concern | Application Component when the evidence is physical/deployment packaging |
| Azure/AWS resource, runtime, network, store, identity, monitor, or platform service | Technology layer element, Technology Service, System Software, Node, or Artifact by concern | Application element because a cloud product name appears |
| GitHub Actions deployment or release workflow | Work Package, Deliverable, Implementation Event, Plateau by concern | Business Process or Technology Process by default |
| Product/domain word in code, such as customer, run, guild, player, order, or signup | No Business Capability/Goal/Product by default | Capability, Value Stream, Goal, Product, Outcome without business-source evidence |

## Relationship Selection Ladder

Use the narrowest valid relationship that represents the architectural claim:

1. Composition or Aggregation for whole/part.
2. Assignment for active structure performing behavior.
3. Realization for concrete fulfilling abstract.
4. Serving for behavior/service used by a consumer.
5. Access for data read/write/use.
6. Flow for transfer.
7. Triggering for temporal or causal sequence.
8. Association only when no narrower valid relationship is evidenced.

Association is a disclosed fallback, not a default relationship for uncertainty.

## View Recipes

| View concern | Preferred view shape | Split trigger |
|---|---|---|
| What is inside one application or application family | Application Structure | Dependencies, hosting, or flow becomes the primary message |
| Which applications depend on exposed behavior or shared data | Application Cooperation | Data flow, protocol detail, hosting, or security dominates the view |
| Which business or UI process uses application services | Application Usage | Exact UI behavior or API wire contracts become the detail |
| How application components use runtime technology | Technology Usage | Hosting, data, identity/security, and observability compete for attention |
| How deployable artifacts map to runtime technology | Implementation and Deployment | Migration sequence or governance is the concern |
| How a service is realized by behavior and structure | Service Realization | The realization chain is hidden by unrelated dependencies |
| How source-backed delivery changes move the landscape | Implementation and Migration | Parallel environments are shown without source-backed state transition |
| Why a change matters | Motivation or Strategy only with architect intent or business-source evidence | Source-code names are the only evidence |

## Evidence Labels

- `source-backed`: directly supported by repo, package, or supplied source evidence.
- `candidate-from-source`: plausible from source but needs architect or stakeholder confirmation.
- `architect-owned`: supplied by user or architecture intent, not extracted from source.
- `weak-evidence`: source hints exist but are insufficient for an accepted architecture claim.
- `overlay-only`: portfolio, cloud, or framework context that must not decide generic ArchiMate classification.

## Anti-Patterns

- Inventory view: every discovered project, route, resource, or workflow is modeled without a stakeholder concern.
- API/service collapse: access surfaces are modeled as Application Services and exposed behavior disappears.
- Business invention: Capability, Goal, Product, Value Stream, or Outcome is inferred from code naming.
- Cloud classifier drift: CAF, AWS Well-Architected, or vendor product names decide generic ArchiMate type.
- Association fog: Association is used when Composition, Assignment, Realization, Serving, Access, Flow, or Triggering is evidenced.
- Mixed-concern view: structure, dependency, flow, hosting, security, and observability compete in one diagram.

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
