# ArchiMate — a reference for architecture design

## 1. Context

`architecture-design` answers *what the enterprise consists of* — which capability does this serve, which application service realises it, which technology node hosts it, which motivational driver justifies its existence. Its sole notation is the ArchiMate modeling language.

This reference is the authoritative ground for the skill. It grounds in **The Open Group ArchiMate® 3.2 Specification, March 2023** (C226). It is opinionated about layer scope, element use, relationship well-formedness, the ArchiMate® Model Exchange File Format (OEF) serialisation used as the sole output, and which layers are round-trip-able with code versus forward-only.

**Notation conformance.** The skill emits ArchiMate 3.2 models as **OEF XML** (The Open Group ArchiMate® Model Exchange File Format 3.2, Appendix E of C226). Files are loadable by Archi, BiZZdesign Enterprise Studio, Sparx Enterprise Architect, Orbus iServer, Avolution ABACUS, HOPEX, and every mainstream ArchiMate tool. The skill does not bundle The Open Group's XSD schemas; emitted files reference the canonical schema URL (`xsi:schemaLocation`) so downstream validators fetch it from The Open Group directly. Validation beyond the skill's own well-formedness checks is pushed to the architect's toolchain — open the file in Archi or run `xmllint --schema <schema-url> <file>.oef.xml`.

**Scope.** ArchiMate Core Framework (Business, Application, Technology layers) plus the Physical, Strategy, Motivation, and Implementation & Migration extensions. Composite elements (Location, Grouping) are in scope. ViewPoints are out of scope as a first-class construct in v1 — the reference instead documents a small set of diagram kinds that cover the concrete use cases (capability map, application cooperation, service realization, technology usage, migration). See §9.

## 2. Principles

### 2.1 Layer separation is a rule, not a recommendation
ArchiMate's layers encode *different concerns*, not *different styles*. A Business Process cannot "host" an Application Component; an Application Service cannot "realise" a Business Goal. Mixing layers within a single box or labelling a box with two stereotypes is a smell. When two concerns interact, they interact through a relationship that crosses the layer boundary (Realisation, Serving, Used-by, Assignment), not through a merged element.

### 2.2 Element ≠ box
Every ArchiMate diagram is a projection of a model. The same element may appear in multiple views with different relationships surfaced in each. Drawing the same Application Service twice in the same diagram without clearly indicating that the two boxes are the same element is a smell — prefer grouping or single-instance placement.

### 2.3 Active / Behaviour / Passive aspects
Within a layer, elements are categorised by aspect:
- **Active structure** — something that performs behaviour (actor, role, application component, node).
- **Behaviour** — the behaviour itself (process, function, service, event, interaction).
- **Passive structure** — something behaviour acts on (business object, data object, artifact).

The core well-formedness rule follows: **active structure is *assigned to* behaviour; behaviour *accesses* passive structure; behaviour *realises* services; services *are used by* elements in a higher layer or the same layer.** A diagram that shows an Actor *accessing* a Business Object directly — without a Business Process or Business Function in between — is malformed at the reference level; see §4.3 and §8.

### 2.4 Core layers are the default; extensions are opt-in per diagram
Business / Application / Technology is the default palette. A diagram claiming to model "architecture" should draw from these three unless the diagram kind is explicitly a motivation view, a strategy view, a migration view, or a physical view. This keeps diagrams legible and prevents the "everything everywhere" soup that the expressive range of the ArchiMate notation enables.

### 2.5 Relationships have well-formedness constraints
Not every relationship is valid between every pair of element types. ArchiMate 3.2 Appendix B (Relationships Table) is the authoritative source. The skill's Review mode cites this table; Build and Extract emit only relationships that are well-formed per the table. A diagram with invalid relationships (e.g., a Business Process *realising* a Technology Node) is a smell regardless of how expressive it looks.

### 2.6 One layer does not imply one diagram
A layered architecture can still be shown on a single diagram; a single layer can still require multiple diagrams. The rule is *one concern per diagram*, not *one layer per diagram*. Capability Map, Application Cooperation, Technology Usage, and Migration are each a single concern that pins the diagram's kind.

### 2.7 Extractability tracks the layer model
Some layers live in code and infrastructure; others live in the architect's head and the business's strategy documents. This is a property of the notation, not a limitation of the skill — see §7.

### 2.8 Valid model is the floor, not the finish line
An OEF file can be syntactically valid and still fail as an architecture artefact. The skill therefore distinguishes three quality levels:

- **model-valid** — XML, OEF sequence, element types, relationship types, and basic ArchiMate well-formedness are correct.
- **diagram-readable** — `model-valid` plus legible views: labels fit, density is bounded, groups are meaningful, and connectors do not cross unrelated elements or otherwise obscure the message.
- **review-ready** — each view answers a specific architecture question, uses the right viewpoint, connects motivation / process / service / technology claims to the elements they affect, and avoids raw extraction inventory.

Build and Extract target at least `diagram-readable` unless the architect asks only for a model-valid draft. Review reports whether the artefact reaches `review-ready`. Project documentation packaging — README rows, render galleries, screenshots, publication pages, and CI package checks — belongs to the consuming project, not to this reference.

## 3. Layers and aspects

ArchiMate 3.2 (Chapter 3 — Generic Metamodel; Chapter 4 — Core Elements; Chapter 5 — Business Layer; Chapter 6 — Application Layer; Chapter 7 — Technology Layer; Chapter 8 — Physical Elements; Chapter 9 — Motivation; Chapter 10 — Strategy; Chapter 11 — Implementation & Migration; Chapter 12 — Relationships).

### 3.1 The seven layers

| Layer | Concern | Examples |
|---|---|---|
| **Strategy** | Where the organisation is heading | Course of Action, Capability, Resource, Value Stream |
| **Business** | What the organisation does for whom | Business Actor, Business Role, Business Process, Business Function, Business Service, Business Object, Contract |
| **Application** | How software realises business services | Application Component, Application Collaboration, Application Service, Application Interface, Application Function, Application Process, Data Object |
| **Technology** | Platforms and infrastructure that host applications | Node, Device, System Software, Technology Collaboration, Technology Service, Technology Interface, Technology Function, Technology Process, Technology Interaction, Artifact, Communication Network, Path |
| **Physical** | Real-world physical environment | Equipment, Facility, Distribution Network, Material |
| **Motivation** | Why architecture changes | Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Value, Meaning |
| **Implementation & Migration** | How we get from here to there | Work Package, Deliverable, Implementation Event, Plateau, Gap |

Composite elements **Location** and **Grouping** span all layers.

### 3.2 Aspect columns

The layers are crossed by aspect columns in the ArchiMate Core Framework (ArchiMate 3.2 §3.1):

| | Active structure | Behaviour | Passive structure |
|---|---|---|---|
| **Business** | Actor, Role, Collaboration | Process, Function, Interaction, Service, Event | Business Object, Contract, Product |
| **Application** | Component, Collaboration | Process, Function, Interaction, Service, Event | Data Object |
| **Technology** | Node, Device, System Software, Collaboration, Path, Communication Network | Process, Function, Interaction, Service, Event | Artifact |

Motivation and Strategy have their own aspect structure (Strategy uses Resource / Capability / Course of Action; Motivation uses Stakeholder / Driver / Goal / Outcome / Principle / Requirement / Constraint / Value / Meaning / Assessment).

**Default reading direction.** Vertically by layer (Strategy on top, Technology on bottom, Motivation to the left, Implementation & Migration to the right). Horizontally by aspect (Active structure on the left, Behaviour in the middle, Passive structure on the right). Diagrams that invert this read as contrarian for no benefit.

### 3.3 Core Framework vs full framework

The Core Framework is Business / Application / Technology across the three aspect columns (ArchiMate 3.2 §3.1). Everything else is strictly an extension. A diagram should declare — implicitly by choice of elements, or explicitly in a header — whether it is a Core diagram or uses extensions.

**Default.** New diagrams stay in the Core Framework unless the question being answered is explicitly motivational ("why"), strategic ("where are we going"), physical ("what is the building"), or migration-related ("how do we get there from here"). An architect drafting an Application Cooperation view should not reach for Motivation elements — they belong in a paired Motivation view.

## 4. Elements by layer

Only the most frequently used elements are surfaced here; consult ArchiMate 3.2 Chapters 5–11 for the full catalog. The omission is deliberate — the reference enforces a small, high-signal vocabulary.

### 4.1 Business Layer (ArchiMate 3.2 Chapter 5)

- **Business Actor** — any party that can act in the business domain: a person, a team, a department, an external organisation such as a customer or supplier. Notation: person icon. Actors don't perform behaviour directly — they occupy Roles, and Roles perform behaviour.
- **Business Role** — a named pattern of responsibility that an Actor takes on when it performs behaviour. Assignment flows Actor → Role → Behaviour: the Role is the thing formally tied to a Process, Function, or Interaction, with the Actor as its occupant.
- **Business Collaboration** — a grouping of Actors or Roles that operates as a single compound unit of business agency — the collective counterpart to individual Actor / Role participation; modelled when the joint action is itself what the architecture needs to name.
- **Business Process** — a time-ordered choreography of work steps that delivers a defined business outcome (order shipped, claim paid, user onboarded). Distinct from Business Function in being intrinsically sequential rather than competency-grouped.
- **Business Function** — behaviour grouped by competency or capability rather than by sequence — *Procurement*, *Treasury*, *Customer Support*. Reorders orthogonally to Processes: the same Process typically passes through multiple Functions.
- **Business Interaction** — collective behaviour performed by a Collaboration.
- **Business Service** — the exposed behaviour of a Process, Function, or Interaction that delivers value to a customer. Services, not processes, are what the Application Layer realises or consumes.
- **Business Event** — a discrete occurrence — external (regulatory deadline, customer arrival, partner notification) or internal (inventory threshold, timer expiry, escalation) — that starts, interrupts, or concludes a behavioural flow.
- **Business Object** — a unit of information with business relevance. Customer, Contract, Order. The Data Object in the Application Layer *realises* the Business Object.
- **Contract** — the specification of rights, obligations, and service levels between a provider and a consumer — the behavioural agreement (SLA, data-sharing terms, compliance scope) captured independently of any specific implementation.
- **Product** — a commercial or internal bundle — a coordinated set of Services, Business Objects, and Contracts packaged and delivered as one. Example: a *Premium Support* Product bundling a Service Desk service, an SLA, and customer-portal access.

**Default.** Model the Business Layer via Business Process and Business Service first; add Function only when a process is too fine-grained; add Actor/Role only when ownership matters to the diagram.

**User-driven vs system-driven process steps.** A Business Process (or Event / Interaction) is *user-driven* when it carries an Assignment from a Business Actor — optionally playing a Business Role — whose Actor represents a human user of the system (Customer, Admin, Support Agent, External Partner). It is *system-driven* when it has no Actor Assignment, or is Assigned only to Application Services that realise it. The distinction is load-bearing for §9.3 Service Realization (Process-rooted modality): user-driven steps must show a UI entry point (UI Application Component + Application Interface); system-driven steps need not. Cross-referenced from §9.7 and §9.3.

### 4.2 Application Layer (ArchiMate 3.2 Chapter 6)

- **Application Component** — a software unit that is independently deployable and replaceable — a microservice, a library, a serverless Function App, a Blazor WebAssembly client, a worker. Components expose behaviour through Application Interfaces and realise Application Services.
- **Application Collaboration** — a grouping of Application Components acting as one compound unit; useful when a multi-Component subsystem delivers a single Application Service and the coupling between Components is itself an architectural concern.
- **Application Interface** — the consumption surface of an Application Service — an HTTP endpoint, a gRPC contract, a UI route, a library method signature — through which a Role, another Component, or a Technology Node actually invokes the Service.
- **Application Function** — a named internal capability of an Application Component: what the Component does under the hood, prior to any exposure. Contrast with Application Service (the capability offered for consumption) and Application Interface (the consumption surface).
- **Application Process** — an ordered chain of Application Function calls and sub-behaviours that together deliver a defined automated outcome — the Application Layer counterpart to a Business Process.
- **Application Interaction** — the joint behaviour emitted by an Application Collaboration when its Components operate together — modelled when the inter-Component dynamics (not the individual Component's behaviour) is the architecturally interesting thing.
- **Application Service** — the exposed behaviour that fulfills a need (often a Business Service).
- **Application Event** — a state change that triggers or is triggered by application behaviour.
- **Data Object** — an automation-facing data structure — records, JSON payloads, database rows, message bodies — that Application Components read, write, or transform. Typically realises a Business Object from the business layer.

**Default.** Model via Application Component, Application Service, and Application Interface as the triad: the component *realises* the service, the service is *exposed through* the interface. Use Application Function only when the component's internals matter to the diagram.

### 4.3 Technology Layer (ArchiMate 3.2 Chapter 7)

- **Node** — a runtime or hosting container that holds System Software and Artifacts and exchanges data with other Nodes. Typical modelling units: a virtual machine, a Kubernetes pod, an Azure App Service / Function App instance, an App Service plan, a physical data-centre server.
- **Device** — a physical computational resource.
- **System Software** — software environment for specific types of components and data objects. The .NET runtime, a database engine, an operating system.
- **Technology Collaboration** — a grouping of Technology Nodes acting as a single platform unit; modelled when cluster / farm / mesh / redundancy-group behaviour is the architectural concern rather than individual Node capability.
- **Path** — a link between Nodes along which communication can occur. An instance of a Communication Network.
- **Communication Network** — a medium between Nodes.
- **Technology Interface** — the access mechanism through which a Node's Technology Service becomes consumable — a network endpoint, a protocol binding, a shared-resource handle.
- **Technology Function** — a named internal capability of a Technology Node: what the Node computes, routes, stores, or enforces at the platform level. Contrast with Technology Service (the exposed, consumable form of the same capability).
- **Technology Process / Technology Interaction / Technology Event** — dynamic behaviour at the technology layer.
- **Technology Service** — the exposed behaviour that an element outside the Technology Layer consumes.
- **Artifact** — a concrete deployable produced by a build pipeline and consumed by a deployment step — the tangible thing that lands on a Node. JARs, DLLs, `.csproj` build outputs, ARM/Bicep templates, Docker images, signed zip packages.

**Default.** Model via Node, System Software (hosting the Node), Technology Service (exposed by the Node), and Artifact (deployed to the Node). Path and Communication Network are required when the diagram reasons about latency, locality, or regulatory data residency; they are noise otherwise.

### 4.4 Physical Layer (ArchiMate 3.2 Chapter 8)

Physical elements extend the Technology Layer with real-world material structure:

- **Equipment** — physical machinery, vehicles, or devices that actively perform work or host technology.
- **Facility** — a physical structure (building, room, data centre) that houses Equipment.
- **Distribution Network** — a physical network (power, water, transport).
- **Material** — passive physical substance acted on by Equipment.

**Default.** Include Physical Layer elements only in diagrams where geography, power, or physical flow are material concerns (data-centre topology, manufacturing, logistics). Otherwise omit.

### 4.5 Motivation (ArchiMate 3.2 Chapter 9)

- **Stakeholder** — any party whose interests the architecture affects — a person, a team, a regulator, an external organisation. Each Stakeholder holds Concerns the architecture must address.
- **Driver** — an external or internal condition that motivates change.
- **Assessment** — the result of analysis of a Driver.
- **Goal** — a declared desired end state — *grow Latin American revenue by 15% this FY*. Directional and specific, but not yet operationalised.
- **Outcome** — a measurable achievement — the observable evidence that a Goal has been met. *LatAm revenue grew from $50M to $58M in Q3* is an Outcome evidencing its paired Goal.
- **Principle** — a durable architectural norm — *all inter-service communication uses managed identity, not shared secrets* — that applies broadly and evolves rarely. Shapes many Requirements rather than being satisfied by one.
- **Requirement** — a specific, verifiable need — *the system must support SSO via Entra ID for all internal users* — usually traceable to a Goal or a Principle.
- **Constraint** — a restriction on the way a Requirement is realised.
- **Value** — what an element is worth to a particular Stakeholder — utility, revenue impact, strategic position. The same element may hold different Value for different Stakeholders.
- **Meaning** — the interpretive context attached to an element — what this Component / Service / Process signifies to a particular audience. The same element may carry different Meaning to compliance, engineering, and sales audiences.

**Default.** Motivation elements live in dedicated Motivation views; they do not clutter Core views. A Core element can be annotated with its Motivation elements via the Realisation relationship in a separate diagram.

### 4.6 Strategy (ArchiMate 3.2 Chapter 10)

- **Resource** — anything under organisational control that the architecture draws on — financial capital, people, data, software licences, physical infrastructure, intellectual property. The building blocks of Capabilities.
- **Capability** — what an Actor, team, or system is able to do — *real-time fraud detection*, *multi-currency settlement*. Typically realised by a combination of Resources, Application Components, and Business Functions.
- **Value Stream** — the end-to-end activity chain that delivers a customer-visible outcome, from *customer recognises a need* to *customer receives value*. Organises work around delivery rather than around departmental ownership.
- **Course of Action** — a named strategy, initiative, or transformation programme that configures Capabilities and Resources toward specific Goals. Realises Goals and shapes the Plateaus in a Migration view.

**Default.** Strategy elements live in dedicated Strategy views (Capability Map, Value Stream Map, Resource Map). A Capability is realised by a Business Function or Process in the Business Layer — model that realisation explicitly.

### 4.7 Implementation & Migration (ArchiMate 3.2 Chapter 11)

- **Work Package** — a bounded piece of work with a defined owner, timeline, and output — an epic, a project, a change programme, a sprint. Composes Deliverables; triggers Implementation Events.
- **Deliverable** — the concrete thing a Work Package produces — a shipped release, a signed contract, a completed migration, a decommissioned system. What the Work Package is measured against.
- **Implementation Event** — a discrete moment in the transformation — go-live, Plateau cut-over, sign-off, regulatory milestone. Marks the transitions between Plateaus.
- **Plateau** — a named architectural snapshot at one point in the transformation — typically *Baseline* (today), one or more *Transition* states, and *Target* (the intended destination). Each Plateau is internally consistent even if the journey between them isn't.
- **Gap** — the delta between two Plateaus — what must be added, removed, or changed to move from one architectural state to the next. Closed by Work Packages.

**Default.** Use Plateau + Gap + Work Package in any Migration view that answers "how do we get from here to there." A Migration view without a Plateau axis is not a Migration view.

### 4.8 Composite: Location, Grouping

- **Location** — a tag for where something resides, physically or conceptually — *EU-West data centre*, *Tokyo office*, *customer-facing channel*. Applied to Actors, Nodes, Facilities, or the Behaviour they perform.
- **Grouping** — an arbitrary collection of elements. Expresses informal aggregation for visual clarity — use sparingly, as it has no formal semantics beyond aggregation.

## 5. Relationships

ArchiMate 3.2 Chapter 12 and Appendix B enumerate the valid element-to-element relationships. The reference summarises the most common; the authoritative source is Appendix B (Relationships Table), which the skill's Review mode cites directly.

### 5.1 Structural

- **Composition** — element is composed of other elements (strong ownership). Solid line, filled diamond at whole end.
- **Aggregation** — element groups other elements (weak ownership; parts may exist independently). Solid line, open diamond at whole end.
- **Assignment** — assignment of active structure to behaviour, or of behaviour to a passive structure. Solid line, filled circles at both ends.
- **Realisation** — entity realises another (an Application Service realises a Business Service; an Application Component realises an Application Service). Dashed line, open triangle at realised end.

### 5.2 Dependency

- **Serving** — element provides its behaviour/functionality to another. Arrow: open arrowhead at the served element.
- **Used-by** (deprecated alias in newer writing; prefer Serving or Access depending on what is being expressed).
- **Access** — behaviour reads, writes, or manipulates a passive-structure element. Dashed line with direction indicating read/write/read-write.
- **Influence** — element positively or negatively affects the realisation of a Motivation element. Dashed line with open arrowhead and `+` or `−` label.
- **Association** — unspecified relationship (last resort — if you reach for Association, you haven't picked the right one yet).

### 5.3 Dynamic

- **Triggering** — temporal or causal — one element triggers the next. Solid line with filled arrowhead.
- **Flow** — transfer from one element to another (information, value, material). Dashed line with filled arrowhead.

### 5.4 Other

- **Specialisation** — element is a specialised form of another. Solid line with open triangle (same notation as UML® generalisation).

### 5.5 Well-formedness rules (the short version)

- **Active structure ≠ behaviour ≠ passive structure.** Composition, Aggregation are within an aspect; Assignment crosses aspects.
- **Realisation is directional and crosses abstraction levels.** Application Service → Business Service; Application Component → Application Service; Technology Service → Application infrastructure needs.
- **Serving is directional.** The served element depends on the serving element. A Business Service is *served by* an Application Service, not the other way round.
- **Triggering and Flow live among behaviour elements.** Do not Trigger a Business Object — Trigger a Process that Accesses the Object.
- **Influence is Motivation-only in origin.** Influence a Goal, a Principle, a Requirement — not an Application Component (use Association or a Motivation–Core Realisation instead).

When in doubt, consult ArchiMate 3.2 Appendix B before emitting a relationship the reference has not surfaced here.

## 6. OEF XML serialisation

The skill emits ArchiMate 3.2 models in The Open Group's **ArchiMate® Model Exchange File Format (OEF) 3.2**, defined in Appendix E of the ArchiMate 3.2 Specification (C226). OEF XML is the canonical portable interchange format for ArchiMate models; it is read and written by any ArchiMate-conformant tool (see §1 for the specific tools the skill has been validated against).

**Element sequence under `<model>`.** OEF fixes the child order for `ModelType`, verified against both the public XSD at `http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd` and Archi's bundled XSD: `name` (required) → `documentation` (optional) → `metadata` (optional) → `elements` (optional) → `relationships` (optional) → `organizations` (optional, may repeat) → `propertyDefinitions` (optional) → `views` (optional, contributed by `archimate3_Diagram.xsd`'s `xs:redefine` of `ViewsType`). The order is mandatory — `xs:sequence` enforces strict ordering. A top-level `<properties>` block on `<model>` is invalid OEF; properties are used on elements, relationships, and views, not on the model root. Invalid or out-of-order top-level children fail Archi's import with `cvc-complex-type.2.4.a` regardless of XML well-formedness — `xmllint --noout` does not catch it (`AD-17`).

### 6.1 Namespace, schema, and root

Every emitted file is a `<model>` element in the ArchiMate 3.0 namespace. The Open Group's XSD schemas are not bundled with the skill; files point at the canonical schema URL so downstream validators fetch it directly.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/
                           http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"
       identifier="id-checkout-model">

  <name xml:lang="en">Checkout architecture</name>
  <documentation xml:lang="en">
    Technology Usage view for the checkout feature.
    Generated by architecture-design; do not hand-edit layout coordinates.
  </documentation>

  <!-- metadata (optional)            — see §6.1a -->
  <!-- elements                       — see §6.2 -->
  <!-- relationships                  — see §6.3 -->
  <!-- organizations (optional)       — see §6.5 -->
  <!-- propertyDefinitions (optional) — see §6.4b and relationship/view properties -->
  <!-- views                          — see §6.4 -->
</model>
```

### 6.1a Metadata (optional)

OEF reserves the optional `<metadata>` block for cataloguing metadata that lives outside the ArchiMate vocabulary. Schema-wise, `MetadataType` uses the `SchemaInfoGroup` content model: an optional `<schema>` element naming the catalog (a URI string in the ArchiMate namespace), an optional `<schemaversion>` element giving the catalog version (also in the ArchiMate namespace), followed by an `<xs:any namespace="##other"/>` wildcard for the catalog payload. **The catalog payload elements must come from a non-ArchiMate namespace** — Dublin Core (`http://purl.org/dc/elements/1.1/`) is the canonical choice. `<schema>` and `<schemaversion>` themselves stay in the ArchiMate namespace; only their string values reference the external catalog.

```xml
<metadata>
  <schema>http://purl.org/dc/elements/1.1/</schema>
  <schemaversion>1.1</schemaversion>
  <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Checkout architecture</dc:title>
  <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">architecture-design 0.7.0</dc:creator>
</metadata>
```

The block sits between `<documentation>` and `<elements>` per the §6 child-element sequence.

**`xmllint --noout` does not catch a metadata-namespace violation** — it only checks XML well-formedness. The schema-level check is `xmllint --schema http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd <file>.oef.xml`, or import via Archi which validates against its bundled XSD on read. Build mode emits a Dublin Core `<metadata>` block by default; Extract preserves an existing block verbatim.

### 6.2 Elements

Elements live under a top-level `<elements>` container. Each element carries an `identifier` (stable across re-extracts), a `xsi:type` (one of the ArchiMate 3.2 element names per §3–§4 of this reference), and a `<name>`. Optional `<documentation>` carries free-text description.

```xml
<elements>
  <element identifier="id-orders-api" xsi:type="ApplicationComponent">
    <name xml:lang="en">Orders API</name>
    <documentation xml:lang="en">Azure Functions isolated-worker; realises the Place Order business service.</documentation>
  </element>
  <element identifier="id-orders-place" xsi:type="ApplicationService">
    <name xml:lang="en">Place Order</name>
  </element>
  <element identifier="id-cosmos-main" xsi:type="Node">
    <name xml:lang="en">Cosmos DB account</name>
  </element>
  <element identifier="id-orders-goal" xsi:type="Goal">
    <name xml:lang="en">Checkout conversion ≥ 60%</name>
  </element>
</elements>
```

**The `xsi:type` vocabulary is fixed** by the ArchiMate 3.2 element catalog (§4 of this reference). Valid values include `BusinessActor`, `BusinessRole`, `BusinessCollaboration`, `BusinessProcess`, `BusinessFunction`, `BusinessInteraction`, `BusinessService`, `BusinessEvent`, `BusinessObject`, `Contract`, `Product`; `ApplicationComponent`, `ApplicationCollaboration`, `ApplicationInterface`, `ApplicationFunction`, `ApplicationProcess`, `ApplicationInteraction`, `ApplicationService`, `ApplicationEvent`, `DataObject`; `Node`, `Device`, `SystemSoftware`, `TechnologyCollaboration`, `Path`, `CommunicationNetwork`, `TechnologyInterface`, `TechnologyFunction`, `TechnologyProcess`, `TechnologyInteraction`, `TechnologyEvent`, `TechnologyService`, `Artifact`; Physical (`Equipment`, `Facility`, `DistributionNetwork`, `Material`); Motivation (`Stakeholder`, `Driver`, `Assessment`, `Goal`, `Outcome`, `Principle`, `Requirement`, `Constraint`, `Value`, `Meaning`); Strategy (`Resource`, `Capability`, `ValueStream`, `CourseOfAction`); Implementation & Migration (`WorkPackage`, `Deliverable`, `ImplementationEvent`, `Plateau`, `Gap`); and composite (`Location`, `Grouping`).

### 6.3 Relationships

Relationships live under a top-level `<relationships>` container. Each relationship carries an `identifier`, a `source` and `target` (both reference element identifiers), a `xsi:type` (one of the ArchiMate 3.2 relationship names per §5 and Appendix B), and optional `<name>` / `<documentation>`.

```xml
<relationships>
  <relationship identifier="id-rel-1"
                source="id-orders-api" target="id-orders-place"
                xsi:type="Realization"/>
  <relationship identifier="id-rel-2"
                source="id-orders-api" target="id-cosmos-main"
                xsi:type="Serving"/>
  <relationship identifier="id-rel-3"
                source="id-orders-api" target="id-orders-goal"
                xsi:type="Influence">
    <properties>
      <property propertyDefinitionRef="propid-strength">
        <value xml:lang="en">+</value>
      </property>
    </properties>
  </relationship>
</relationships>
```

**Relationship `xsi:type` vocabulary** (ArchiMate 3.2 §5 / Appendix B): `Composition`, `Aggregation`, `Assignment`, `Realization` (American spelling — the schema uses the American form), `Serving`, `Access` (with `accessType` attribute: `Read`, `Write`, `ReadWrite`, or omitted for unspecified), `Influence`, `Triggering`, `Flow`, `Specialization`, `Association`. Every emitted relationship must be valid per Appendix B for the given source/target element-type pair; the skill enforces this in Build and Extract and flags it in Review (`AD-2`).

### 6.4 Views and diagrams

Diagrams are expressed under `<views>/<diagrams>`. Each `<view>` is a specific ArchiMate diagram kind (§9 of this reference) expressed as a `viewpoint` attribute. A view contains `<node>` placements referencing elements and `<connection>` placements referencing relationships. Layout coordinates (`x`, `y`, `w`, `h`) are in pixels; origin top-left.

```xml
<views>
  <diagrams>
    <view identifier="id-view-tech"
          xsi:type="Diagram"
          viewpoint="Technology Usage">
      <name xml:lang="en">Checkout — Technology Usage</name>

      <node xsi:type="Element" identifier="id-n-api" elementRef="id-orders-api"
            x="120" y="120" w="180" h="64"/>
      <node xsi:type="Element" identifier="id-n-svc" elementRef="id-orders-place"
            x="120" y="220" w="180" h="64"/>
      <node xsi:type="Element" identifier="id-n-cosmos" elementRef="id-cosmos-main"
            x="120" y="340" w="180" h="64"/>

      <connection xsi:type="Relationship" identifier="id-c-1" relationshipRef="id-rel-1"
                  source="id-n-api" target="id-n-svc"/>
      <connection xsi:type="Relationship" identifier="id-c-2" relationshipRef="id-rel-2"
                  source="id-n-api" target="id-n-cosmos"/>
    </view>
  </diagrams>
</views>
```

**Abstract-type + `xsi:type` pattern.** `<view>`, `<node>`, and `<connection>` are all typed as abstract complexTypes in OEF (`ViewType`, `ViewNodeType`, `ConnectionType` respectively); every instance disambiguates via `xsi:type`. `<view>` concretises to `Diagram` (the only shape the skill emits in v1). `<node>` concretises to `Element` (when `elementRef` references a model element — the default for skill output), `Container` (layout-only), or `Label` (text). `<connection>` concretises to `Relationship` (when `relationshipRef` references a model relationship — the default) or `Line` (visual-only). Omitting `xsi:type` on a `<node>` or `<connection>` triggers `cvc-type.2` on schema-validating importers (Archi) and is flagged as `AD-15`.

**Viewpoint attribute.** Every §9 diagram kind has a canonical ArchiMate 3.2 Viewpoint enum value drawn from `ViewpointsEnum` in `archimate3_View.xsd`; the skill emits the exact enum string. The §9 English label and `viewpoint=` attribute value are identical (see §9 for the seven canonical strings). The XSD types `viewpoint` as `xs:union` of `xs:string` and `ViewpointsEnum`, so custom strings are schema-valid; the skill does not use them — every supported kind has a canonical match.

**Element identity is shared across views.** Placing an element in three diagrams creates three `<node>` entries — three placements with their own coordinates — but the element itself appears once in `<elements>`. This is the model-vs-view separation at the heart of OEF: an Application Component is *one* thing, and every view that shows it shows the same thing.

Generated views are materialized. Build and Extract do not emit valid-looking
`<elements>` / `<relationships>` inventories with empty `<view>` placeholders.
Each generated view contains Element nodes with `elementRef`, `x`, `y`, `w`,
and `h`, plus Relationship connections whose `source` and `target` point at
the view-node identifiers. A blank `100 × 100` placeholder is importable
model inventory, not a diagram-readable architecture view.

Identifier uniqueness is global. OEF `identifier` attributes share one XML ID
space across model elements, model relationships, views, view nodes, view
connections, property definitions, and organization items. A view node must
never reuse the model element identifier it references.

### 6.4a Layout strategy

Coordinate emission is governed by a deterministic three-tier procedure introduced in 0.8.0. The full algorithm, worked example, and edge-case handling live in [../../skills/architecture-design/references/procedures/layout-strategy.md](../../skills/architecture-design/references/procedures/layout-strategy.md); what follows is the structural contract that Review mode checks and architects can read off without loading the procedure.

**Three tiers.**
- **Tier 0** preserves architect-positioned `<node>` placements verbatim from any prior view at the canonical path. Re-Extract never churns hand-edited coordinates.
- **Tier 1** runs the Sugiyama-v1 core engine: cycle handling → layer assignment → within-layer ordering (4-pass barycentric) → coordinate assignment (median heuristic) → Manhattan A* edge routing (obstacle-avoiding) → bounding-box normalisation (used region shifted to `(40, 40)` origin).
- **Tier 2** applies the per-viewpoint specialisation matching the §9 diagram kind. Most specialisations override only Tier 1 phases 3–4 (within-layer ordering + coordinate assignment); §9.5 Migration replaces phases 2–4; §9.4 Technology Usage carves phase 5 for hosting Assignment edges; §9.7 Business Process Cooperation runs the existing process-flow lane procedure.

**Grid.** 10 px. Every `x`, `y`, `w`, `h`, and `<bendpoint>` is a multiple of 10. Archi's default snap-to-grid is 10 px.

**Layer ordering — semantic, not absolute.** Strategy first (top), Business, Application, Technology, Physical last (bottom). After Tier 1 phase 6 normalisation, the first populated layer's row starts at `y = 40`; absolute y-values are content-dependent (bands grow with content), so the AD-L1 smell is a **relative** ordering check, not an absolute-band check.

**Aspect bias — preserved.** Within each layer, the five-aspect arrangement (Motivation left, Active structure, Behaviour, Passive structure, Implementation & Migration right) biases x-direction. Phase 4 places nodes with no cross-layer incoming edges at the centre of their aspect column.

**Default sizes.** Structure (Component, Node, Actor, Role, Interface, Artifact) = `160 × 64` (was `140 × 60`). Behaviour (Process, Function, Service, Event) = `180 × 64` (was `160 × 60`). Motivation / Strategy = `180 × 64`. Passive (Data Object, Business Object, Contract, Product) = `140 × 64`. Implementation & Migration = `180 × 64`. Junction = `14 × 14`. Grouping = computed from children, minimum `240 × 140`. Minimum for any element: `120 × 55`.

**Gutters.** 40 px between siblings (was 20). 60 px between layers (was 40). 80 px between layers in §9.3 Service Realization specialisation (Tier 2).

**Nesting over explicit edge.** Composition, Aggregation, and Realization relationships between two elements in the same cell render as a nested `<node>` placement; the corresponding `<connection>` is suppressed in that view via `<property propertyDefinitionRef="propid-archi-arm"><value xml:lang="en">hide</value></property>` on the relationship. Existing rule, preserved.

**Edge routing.** Orthogonal only (right-angle bends). Manhattan path-finding around node-body obstacles (Tier 1 phase 5, A*). Bend points emitted as `<bendpoint>` children of `<connection>`. Connections attach to side-midpoints, never corners. Parallel edges in the same lane space 20 px apart. Re-Extract may preserve prior connection bendpoints only when the relationship reference and source/target endpoints are unchanged and the preserved route still clears the `AD-L11` intersection check; relationship replacement or source/target inversion requires rerouting.

**View budget.** A view is compact when it carries at most 20 elements and 30 relationships; nesting depth capped at 2.

**Process-flow exception (§9.7).** Existing reference §9.7 process-flow lanes preserved verbatim — Tier 2 specialisation that replaces Tier 1 phases 3–4 with the existing three-lane horizontal strip rule (Active above, Behaviour middle, Passive below).

**Style.** Do not emit `<style>` on `<node>` placements. Undeclared style lets each rendering tool apply its layer-idiomatic colours (yellow Business / turquoise Application / green Technology in Archi's default theme). The only acceptable `<style>` emission is a neutral fill on a Grouping to distinguish it from contained elements.

**Re-extract preserves architect positions.** Existing rule, preserved (Tier 0).

**No model-level layout marker.** Build and Extract do not emit a `propid-archi-model-banded` property or any other marker on the `<model>` element. The OEF model root cannot carry `<properties>` in Archi's schema-validating import path. Review therefore validates the §6.4a layout contract directly from each view's geometry rather than from a marker.

### 6.4b View-emission control properties

Two property definitions used by the process-view emission contract (per [`references/procedures/process-view-emission.md`](../../skills/architecture-design/references/procedures/process-view-emission.md)) to give architects opt-out control over auto-emission. The skill emits these `<propertyDefinition>` declarations once per model under `<propertyDefinitions>` only when at least one element carries a matching `<property>` instance — never auto-injected on a legacy file.

**`propid-coop-view-exclude`** — set on a Business Process to exclude it from the feature's §9.7 Business Process Cooperation view. Suppresses `AD-B-13`. Use cases: deprecated processes kept for documentation, planned-but-not-yet-implemented stubs, externally-owned processes referenced but not modelled.

```xml
<propertyDefinition identifier="propid-coop-view-exclude" type="string">
  <name xml:lang="en">coop-view-exclude</name>
</propertyDefinition>
```

Instance form on a Business Process element:

```xml
<property propertyDefinitionRef="propid-coop-view-exclude">
  <value xml:lang="en">true</value>
</property>
```

**`propid-drilldown-exclude`** — set on a Business Process to suppress emission of its own §9.3 Service Realization (Process-rooted modality) drill-down view. Suppresses `AD-B-12`. Use cases: thin sub-orchestrator helpers without independent realisation, processes the architect wants in cooperation overview but not as a stand-alone diagram.

```xml
<propertyDefinition identifier="propid-drilldown-exclude" type="string">
  <name xml:lang="en">drilldown-exclude</name>
</propertyDefinition>
```

Instance form mirrors the cooperation case (different `propertyDefinitionRef`).

**Both follow the existing OEF property-definition pattern.** The `<name>` child is mandatory per the OEF schema (`PropertyDefinitionType` requires `<name>`); the self-closing form `<propertyDefinition .../>` fails Archi's import with `cvc-complex-type.2.4.b` and triggers `AD-17`.

**Orthogonal concerns.** The two properties control different emission decisions and should not be conflated. `propid-coop-view-exclude` controls *inclusion in the §9.7 overview*; `propid-drilldown-exclude` controls *emission of a per-process §9.3 drill-down*. Setting one does not imply the other.

### 6.5 Organizations (folder structure)

Optional. Tools like Archi present models in a folder tree. OEF exposes this via `<organizations>`:

```xml
<organizations>
  <item>
    <label xml:lang="en">Business</label>
    <item identifierRef="id-orders-place"/>
  </item>
  <item>
    <label xml:lang="en">Application</label>
    <item identifierRef="id-orders-api"/>
  </item>
  <item>
    <label xml:lang="en">Technology</label>
    <item identifierRef="id-cosmos-main"/>
  </item>
</organizations>
```

**The skill emits a default organization structure** grouping elements by ArchiMate layer (Strategy / Business / Application / Technology / Physical / Motivation / Implementation & Migration). Architects editing the model in Archi can rearrange; re-extract preserves architect-chosen structure where it can detect it.

### 6.6 Identifiers

- Format: `id-<short-slug>` where `<short-slug>` is stable across re-extracts.
- Source of slug: the project identifier (csproj name, Bicep symbolic name, workflow filename) normalised to lowercase + hyphens.
- Collision avoidance: if two sources produce the same slug, append a suffix: `id-orders-api-func`, `id-orders-api-comp`.
- **Identifiers are the coupling mechanism for re-extract idempotency.** An Application Component whose identifier is `id-orders-api` stays `id-orders-api` forever, across any number of re-extracts, unless the underlying source project is renamed.

### 6.7 Naming

- Element `<name>` is title-case for structural/passive elements; imperative-verb-noun for behaviour (Business Process, Application Function).
- Name and identifier must agree semantically — `id-orders-api` labelled "Payment Service" is a bug. Review flags this (`AD-8`).
- Localisation: `<name>` carries `xml:lang` (default `en`); additional languages attach as sibling `<name xml:lang="de">…</name>` entries. The skill emits `en` only.

### 6.8 Coverage

What OEF carries faithfully:

- Every ArchiMate 3.2 element type (§3–§4) via `xsi:type`.
- Every ArchiMate 3.2 relationship type (§5 / Appendix B) via `xsi:type`, with `accessType` attribute for Access.
- Full model-vs-view separation: shared element identity across multiple diagrams.
- Typed documentation per element and per relationship.
- Custom properties via `<propertyDefinitions>` + `<properties>`.
- Layout coordinates for each node placement, explicit and inspectable.
- Organization structure grouping elements by concern.

### 6.9 Gaps

- **Viewpoint-specific metadata beyond the `viewpoint` attribute** — concerns tables, stakeholder-viewpoint cross-references, pattern templates — are not modelled by OEF directly; architects extend via custom properties or by splitting into multiple views.
- **XSD validation is not the skill's job.** OEF files are structurally validated by the downstream tool (Archi on import; `xmllint --schema <url>`). The skill enforces ArchiMate well-formedness (layer discipline, Appendix B relationship validity) in Build and Review; it does not run schema validation at runtime. **Note:** `xmllint --noout` alone is XML well-formedness only and does *not* catch schema-level issues such as abstract-type violations (`AD-15`). For schema-level confidence, use `xmllint --schema http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd <file>.oef.xml` or open in Archi. See §1 for the rationale.
- **Archi-specific canvas features** — custom figures, visual groupings that are not ArchiMate elements, canvas styling presets — are lost. OEF is tool-neutral; the richer Archi-native `.archimate` format preserves them, at the cost of tool lock-in.

### 6.10 When OEF is not enough

If the diagram requires:
- Archi-specific canvas or visual styling (custom figures, group colours) — model in Archi's native `.archimate` format directly; the skill does not support that format in v1, and
- ViewPoint metadata beyond the `viewpoint` attribute — model as custom properties, or use Archi's viewpoint editor,

then the diagram is out of scope for `architecture-design` Build mode and the architect should edit it in Archi directly. The skill's Review mode can still parse and review the OEF export from Archi.

## 7. Extractability — per layer

**Extract mode lifts ArchiMate diagrams asymmetrically.** Some layers live in code and infrastructure; others live in the architect's strategic thinking. The split is a property of the notation itself and is surfaced in Extract output so the architect knows where they still need to fill in.

### 7.1 Extractable layers and sources

| Layer | Extractable from | Notes |
|---|---|---|
| **Application** | `*.sln`, `*.csproj`, `host.json`, `staticwebapp.config.json`, `package.json`, NuGet references | Each project becomes an Application Component; inter-project references become Used-by or Composition; `host.json` triggers and bindings become Application Interfaces |
| **Technology** | Bicep, `host.json`, `staticwebapp.config.json`, `azure.yaml`, IaC of all dialects the skill supports | Bicep `Microsoft.Web/sites`, `Microsoft.Storage/storageAccounts`, `Microsoft.DocumentDB/databaseAccounts`, `Microsoft.KeyVault/vaults` become Technology Nodes; dependsOn and SKU become Composition and properties of the Node; network `Microsoft.Network/virtualNetworks` and `privateEndpoints` become Communication Network and Path |
| **Physical** | Not extracted in v1 | Forward-only |
| **Implementation & Migration** | `.github/workflows/*.yml`, `azure-pipelines.yml` | Deploy jobs become Work Packages; environments (Dev/Staging/Prod) become Plateaus; the movement between environments becomes Gap closure |

### 7.2 Forward-only layers

| Layer | Why forward-only | Extract output |
|---|---|---|
| **Business** (Actor, Role, Collaboration, Object, Contract, Product, Service, Function) | These elements live in domain understanding, not in code. Naming, ownership, agreements, and competency grouping are architect decisions | Emitted as a typed stub: `' forward-only — architect fills in: Business Layer` block with suggested placeholders inferred from Application Component names (e.g., a Component called `OrdersApi` implies a plausible Business Service *Order Management*) |
| **Business** (Process, Event, Interaction) | Partially extractable from backend workflow sources. When Durable Functions orchestrators or Logic Apps workflow definitions are present, their chain shape is a reasonable candidate for a Business Process (with Events at triggers); the architect confirms or rejects. When those sources are absent, the elements remain forward-only | Emitted with a per-element `LIFT-CANDIDATE` marker (§7.4) citing the source path and a confidence score. Architect removes the marker to accept, or removes the element to reject |
| **Motivation** | Drivers, Goals, Outcomes, Principles, Requirements live in strategy documents, architectural decision records, compliance artefacts. Extracting them from code would be fabrication | Emitted as a typed stub identifying where the architect should input |
| **Strategy** | Capabilities and Value Streams are organisational artefacts, not codebase ones | Emitted as a typed stub |

### 7.3 The forward-only marker

Every Extract output that includes typed stubs for forward-only layers prefixes those sections with:

```xml
<!--
==============================================================================
FORWARD-ONLY — this layer was not extracted from source
The architect must fill in: <layer name>
The skill inferred suggestive placeholders from Application element labels
==============================================================================
-->
```

Render as an XML comment in OEF output (the only output format the skill emits in v1; reference §6.10). The marker body must not contain `--` per XML well-formedness — use `=` for the rule line, not `-`. The `LIFT-CANDIDATE` marker (§7.4) is already XML-comment form and unchanged.

The footer (§9 of SKILL.md) lists which layers were lifted vs stubbed so the architect's review focus is clear.

Forward-only stubs must also be visible in seed views when Extract emits them. Strategy Capability stubs appear in a FORWARD-ONLY Capability Map seed view; Motivation stubs appear in a FORWARD-ONLY Motivation seed view. The seed views are scaffolds for the architect to validate or rewrite, not claims that source code proved those layers.

### 7.4 Lift candidates for Business Process / Event / Interaction

Business Process, Event, and Interaction sit between the forward-only and extractable categories: their shape is plausibly readable from backend workflow sources, but the final naming, granularity, and business framing are architect calls. Extract emits them with a per-element `LIFT-CANDIDATE` marker so the architect can confirm or reject each one independently.

**Marker format.** An XML comment immediately preceding the `<element>`:

```xml
<!-- LIFT-CANDIDATE — architect confirms: source={path/to/source:line}, confidence=high|medium|low -->
<element identifier="id-place-order-proc" xsi:type="BusinessProcess">
  <name xml:lang="en">Place Order</name>
</element>
```

The `source=` attribute cites the file path (and optional line number) of the orchestrator / workflow that motivated the lift. The `confidence=` attribute captures how unambiguously the chain shape mapped — `high` for an unambiguous linear or fan-out-fan-in chain; `medium` for nested sub-orchestrators, dynamic activity names, or multiple triggers; `low` for heuristic fallback. The `source=` attribute is how reverse Lookup (SKILL.md) resolves "which process does this symbol belong to" without an auxiliary index file.

**Architect workflow.** On first review, either (a) accept by deleting the `LIFT-CANDIDATE` comment and keeping the element, (b) reject by deleting both the comment and the element, or (c) rename and enrich the element (Role Assignment, Access to Business Objects, Triggering edges that the lifter didn't see) while keeping the marker until the step is audited. The marker never re-emerges once deleted; re-running Extract on the same source produces the same element identifier and leaves accepted elements alone.

**Lifting sources (v1).** Durable Functions orchestrators (`[OrchestrationTrigger]` / `[Function]` pairs using `IDurableOrchestrationContext` or `TaskOrchestrationContext`) and Logic Apps definitions (`workflow.json`, `*.logicapp.json`, or Bicep `Microsoft.Logic/workflows`). Service Bus subscription chains are a plausible v2 source. GitHub Actions workflows continue to lift to the Implementation & Migration layer (Work Packages) — they describe deployment, not business flow.

**UI routes are not lifted in v1.** §9.3 Service Realization views (Process-rooted modality) that include a UI Application Component and Application Interface at the entry point for a user-driven Business Process are hand-authored by the architect. The Blazor idiom (v1): UI Application Component `<name>` = the Blazor page component's file path; Application Interface `<name>` = the `@page` route string. Other frontend stacks (Next.js App Router / Pages Router, React Router) follow the same convention but do not carry a v1-specific idiom callout. Full authoring rules in [../../skills/architecture-design/references/procedures/lifting-rules-process.md](../../skills/architecture-design/references/procedures/lifting-rules-process.md).

**Drift.** A lifted element whose `source=` file no longer exists (or no longer defines the matching orchestrator / workflow) triggers `AD-DR-11`; an orchestrator / workflow in the repo that no Business Process references triggers `AD-DR-12`. Both are `warn` — the architect decides which side reconciles.

## 8. Common smells

Codes are used in the skill's smell catalog and the Review mode output:

- **`AD-1` Layer soup** — a single diagram with Business, Application, Technology, Motivation, and Strategy elements mixed without a clear concern. Diagrams try to do everything, succeed at nothing.
- **`AD-2` Invalid relationship per Appendix B** — e.g., Business Process *realising* a Technology Node, Application Component *triggering* a Business Actor.
- **`AD-3` Double aspect** — an element stereotyped as both Active structure and Behaviour (e.g., a box labelled both "Component" and "Service").
- **`AD-4` Active structure directly accessing passive structure** — Actor → Business Object without a Process or Function in between.
- **`AD-5` Association overuse** — more than one Association per diagram usually indicates the architect has not picked a real relationship type.
- **`AD-6` Missing realisation chain** — a Business Service with no Application Service realising it; an Application Service with no Application Component realising it.
- **`AD-7` Core/extension mixing without cause** — a diagram claiming to be a Core view that includes Motivation elements, or vice versa.
- **`AD-8` Identifier / label mismatch** — element `identifier` carries semantics inconsistent with its `<name>` (e.g., `id-orders-api` labelled "Payment Service").
- **`AD-9` Missing Plateau axis in a Migration view** — Implementation & Migration diagram without Plateau + Gap.
- **`AD-10` Motivation elements in a non-Motivation view without Realisation** — an Application Component directly tagged with a Goal without the intervening Realisation.
- **`AD-11` Empty Grouping** — a Grouping with no elements, or a Grouping whose only purpose is visual (prefer Location, or drop it).
- **`AD-12` Technology Layer reasoning without Path / Communication Network when concerns are latency or residency** — network-sensitive diagram drawn as if network is frictionless.
- **`AD-13` Ambiguous Product/Contract/Service** — Product modelled with Service semantics or vice versa; Contract used as a documentation placeholder without a formal agreement.
- **`AD-14` Forward-only layer emitted without the marker** — Extract output that populated Business (Actor / Role / Collaboration / Object / Contract / Product / Service / Function) / Motivation / Strategy elements without the `FORWARD-ONLY` header block (§7.3).
- **`AD-14-LC` Lift-candidate emitted without the marker** — Extract output that populated a Business Process, Business Event, or Business Interaction from a backend workflow source without the per-element `LIFT-CANDIDATE` comment (§7.4). Without the marker, the architect cannot distinguish a confirmed element from an unreviewed candidate, and reverse Lookup has no `source=` anchor.
- **`AD-15` View-placement `xsi:type` missing** — view `<node>` emitted without `xsi:type` (one of `Element` / `Container` / `Label`), or view `<connection>` emitted without `xsi:type` (one of `Relationship` / `Line`). OEF's `ViewNodeType` and `ConnectionType` are abstract complexTypes — every instance must disambiguate via `xsi:type`. Archi's XSD-validating import rejects bare elements with `cvc-type.2: The type definition cannot be abstract`. `xmllint --noout` does *not* catch this; `xmllint --schema <url>` does.
- **`AD-16` Metadata catalog payload in the ArchiMate namespace** — the `<metadata>` block's catalog payload elements (the actual cataloging content beyond the optional `<schema>` / `<schemaversion>` SchemaInfoGroup prelude) emitted in the ArchiMate namespace (`http://www.opengroup.org/xsd/archimate/3.0/`). OEF's `MetadataType` accepts the prelude in the ArchiMate namespace but routes catalog content through `<xs:any namespace="##other"/>`, requiring it to come from a non-ArchiMate namespace such as Dublin Core (`http://purl.org/dc/elements/1.1/`). See §6.1a. `xmllint --noout` does *not* catch this; `xmllint --schema <url>` and Archi import do. Inverse error (placing `<schema>` or `<schemaversion>` in a non-ArchiMate namespace) also fails — they ARE schema-declared elements in `SchemaInfoGroup` and must inherit the document default namespace.
- **`AD-17` Invalid model child element, sequence, or XML ID space** — top-level children of `<model>` emitted in an order that violates `ModelType`'s `xs:sequence`, top-level children that the schema does not permit at all, or duplicate `identifier` values in the OEF file. The mandatory order is `name → documentation → metadata → elements → relationships → organizations → propertyDefinitions → views` (see §6). A model-root `<properties>` block is invalid, even when used only to carry a layout marker. Archi rejects invalid children, out-of-order children, or duplicate XML IDs during schema-validating import; `xmllint --noout` does *not* catch this; `xmllint --schema <url>` and Archi import do.
- **`AD-18` Invisible RBAC** — a Technology Node marked RBAC-only (`disableLocalAuth=true`, `allowSharedKeyAccess=false`, `enableRbacAuthorization=true`, or equivalent) has a Serving / Used-by path from an Application Component but no Access relationship from the corresponding Managed Identity to the protected resource. The data path is drawn without its authorization path.
- **`AD-19` Fictitious plateaus** — Extract emits deployment Plateaus that have no supporting GitHub environment, `jobs.*.environment`, matrix environment, environment-tagged Bicep parameter set, or environment-specific deploy job.
- **`AD-20` Plateau triggering without migration intent** — Plateaus that represent parallel deployment environments are connected by Triggering / Gap relationships even though the view documentation does not state an explicit as-is / to-be migration. Parallel environments coexist; they do not become one another.
- **`AD-21` Unbounded external component** — an Application Component marked external / third-party, inferred from non-local HTTP base addresses, or discovered from CSP allowlists is not aggregated into an external trust-boundary Grouping in Application Cooperation views.

### Professional artefact quality smells — `AD-Q*`

These smells are static review findings over OEF views. They do not test project packaging, render galleries, README tables, or CI publication.

- **`AD-Q1` Inventory view** — a view lists discovered elements but does not answer an architecture question.
- **`AD-Q2` Viewpoint mismatch** — the selected viewpoint does not match the concern being communicated.
- **`AD-Q3` Unreviewable density** — a view is technically laid out but too crowded for practical review.
- **`AD-Q4` Weak visual hierarchy** — all elements and relationships appear equally important, hiding the architectural point.
- **`AD-Q5` Extraction leakage** — implementation trivia appears in a conceptual or stakeholder-facing view.
- **`AD-Q6` Relationship noise** — mechanically complete relationships obscure the main dependency, realisation, or process path.
- **`AD-Q7` Orphaned decision context** — risks, constraints, drivers, goals, requirements, or principles appear without a clear connection to affected architecture elements.
- **`AD-Q8` Process thinness** — a Business Process Cooperation view shows actors or systems but not handoffs, responsibilities, trigger/flow, or value outcome.
- **`AD-Q9` Service Realization thinness** — a Service Realization view names services but does not show the realisation chain clearly enough to audit.
- **`AD-Q10` Label ambiguity** — labels are valid XML names but too generic, duplicated, or code-shaped for the intended architecture audience.

### Layout smells — `AD-L*`

Artefact smells specific to `<view>` layout, derived from the §6.4a Layout strategy contract. Every `AD-L*` is `[static]` — verifiable from the `.oef.xml` source alone, no runtime reads needed.

- **`AD-L1` Layer-ordering violation** — an element's `y` coordinate violates the relative ordering of its ArchiMate layer (Strategy above Business above Application above Technology above Physical) after Tier 1 phase 6 bbox normalisation per §6.4a. An Application Component placed below an element in the Technology layer makes the diagram visually lie about what layer the element is in.
- **`AD-L2` Node overlap** — two `<node>` placements at the same nesting depth in the same view whose bounding boxes intersect. Rendering tools render one on top of the other; the diagram is unreadable.
- **`AD-L3` Undersize** — `w < 120` or `h < 55`, or `w` is smaller than the `<name>` length would need at the default font. Label truncates in Archi and in most other tools; the element becomes ambiguous.
- **`AD-L4` View density** — view exceeds 20 elements or 30 relationships, or nesting depth exceeds 2. Readability drops sharply past these thresholds (ArchiMate Cookbook, The Open Group, "compact and readable"); split the view or promote a cluster to a Grouping.
- **`AD-L5` Excessive crossings** — edge-crossing count exceeds `node_count / 6` (threshold tightened in 0.8.0 from the pre-0.8.0 `node_count / 4` because Tier 1 phase 3's 4-pass barycentric crossing-minimisation materially reduces crossings vs the pre-0.8.0 1-pass procedure). Indicates either over-density (address via `AD-L4`) or poor placement (re-run Tier 1 phase 3).
- **`AD-L6` Non-orthogonal routing** — a `<connection>` whose source and target don't share an x or y coordinate carries no `<bendpoint>`, so renderers draw a diagonal line. The diagram mixes routing styles and reads inconsistently.
- **`AD-L7` Nested-plus-edge** — a `<node>` is visually nested inside its parent *and* a visible `<connection>` for the parent-child relationship is emitted in the same view. The relationship is represented twice; Archi's ARM handles this poorly. Either hide the edge (add the `propid-archi-arm` = `hide` property to the relationship) or draw the elements side-by-side.
- **`AD-L8` Off-grid coordinates** — any `x`, `y`, `w`, `h`, or `<bendpoint>` coordinate that is not a multiple of 10. Diagrams drift visually on re-open / re-snap; git diffs churn on unrelated edits.
- **`AD-L9` Hierarchy not respected** — a Realization / Used-by / Serving relationship between same-layer elements is drawn against topological direction (e.g. realised-by-edge points up the layer when the realised element is below). Tier 1 phase 3's topological sort plus phase 1's cycle handling prevents this; the smell catches violations introduced by hand-edit or by a pre-Tier-1 procedure run.
- **`AD-L10` Canvas not normalised** — the top-left of the view's used region (smallest `x` / `y` over all `<node>` placements + `<bendpoint>`s) is not at `(40, 40) ± 10 px`. Tier 1 phase 6 (bbox normalisation) emits a normalised canvas naturally; the smell catches non-normalised legacy or hand-shifted output.
- **`AD-L11` Connector through unrelated node** — a `<connection>` segment crosses the bounding box of a `<node>` that is neither the source, target, nor a required ancestor/container of the source or target needed to exit nested structure. This includes stale bendpoints reused after a relationship is replaced or its source/target endpoints are inverted. This is a blocking layout smell: it visually implies ownership, flow, or relationship semantics that do not exist. Build / Extract must reroute with deterministic bendpoints or fail self-check; Review cannot classify the artefact above `model-valid` while this smell is present.
- **`AD-L12` View-orphan element** — a `<node>` appears in a view with no incoming or outgoing `<connection>` to another node in the same view and is not explicitly documented as a legend, note, or intentional placeholder. The element floats without a readable architecture claim.
- **`AD-L13` Stacked connector lane** — two or more visible connections share the same source-side or target-side lane closely enough that arrowheads or labels overlap. Parallel edges in the same lane must be spaced at least 20 px apart per §6.4a.
- **`AD-L14` Wide empty layer gap** — the vertical gap between occupied layer bands exceeds 100 px after normalisation without a containing Grouping, title block, or documented whitespace purpose. The view reads as sparse or disconnected.
- **`AD-L15` Local fan-out crisscross** — three or more visible connections from the same source or to the same target cross each other or cross a non-endpoint sibling node. Re-order siblings, group the fan-out, or route lanes explicitly.

### Process-flow smells — `AD-B-*`

Artefact smells specific to §9.7 Business Process Cooperation and §9.3 Service Realization. All `[static]` — verifiable from the `.oef.xml` source alone.

- **`AD-B-1` Missing trigger chain** — a Business Process Cooperation view with two or more Behaviour elements (Business Process / Event / Interaction) that are not linked by any Triggering or Flow relationship into one temporal chain. The diagram shows steps without ordering; the "in what order does the business do what" question is unanswered.
- **`AD-B-2` Disconnected participant** — a Business Actor, Role, or Collaboration placed in a §9.7 view with no Assignment relationship to any Behaviour element in that view. The participant is visually present but plays no part in the flow.
- **`AD-B-3` Orphan Business Object** — a Business Object, Contract, Product, or Data Object (realising a Business Object) in a §9.7 view with no Access relationship from any Behaviour element. The passive-structure element floats; cf. `AD-4` for the related active-structure direct-access case.
- **`AD-B-4` Non-Business element in Business Process Cooperation** — an Application, Technology, Motivation, or Strategy element present in a §9.7 view. Tighter than `AD-7` for this view kind specifically — §9.7 is a single-layer view by construction.
- **`AD-B-5` Chain without entry or exit** — a §9.7 temporal chain has no Business Event at its origin (no trigger) and no terminal Business Service or Business Event (no declared outcome). The process appears to start and end in the middle of the air.
- **`AD-B-6` Service Realization without realising Application Service** — a §9.3 view in the Process-rooted modality (Business Process at the top) with no Application Service realising the Business Process. The "how is this step implemented" question fails at the first hop. Fires only when the §9.3 view contains a Business Process; the Service-rooted modality is unaffected.
- **`AD-B-7` Service Realization without realising Application Component** — a §9.3 view with an Application Service present but no Application Component realising that service. The Realisation spine breaks at the Application layer before reaching a deployable artefact. Applies to both content modalities of §9.3 (Service-rooted and Process-rooted).
- **`AD-B-8` Orphan Business Process — §9.7 end** — a Business Process in a §9.7 view has no Realisation chain into any §9.3 view (Process-rooted modality) for the same feature. The macro view claims the process exists; the drill-down views do not realise it. Between-view invariant of §7.4.
- **`AD-B-9` Orphan Application Service — §9.3 end** — an Application Service in a §9.3 view (Process-rooted modality) realises no Business Process present in any §9.7 view for the same feature. The drill-down claims to realise a process that the macro view does not know about. Symmetric to `AD-B-8`.
- **`AD-B-10` User-driven process without UI entry point** — a §9.3 view in the Process-rooted modality whose Business Process carries a Business Actor Assignment in the paired §9.7 view (per §4.1's user-driven definition) lacks a UI Application Component and Application Interface at its entry point. Full-stack agents reading the model cannot tell which UI surface the user interacts with.
- **`AD-B-11` Single-process cooperation view** — a `<view>` with `viewpoint="Business Process Cooperation"` containing exactly one `xsi:type="BusinessProcess"` element. By the spec definition of "cooperation" (≥ 2 cooperating elements), a single-process §9.7 is structurally wrong. Severity: `warn`. Action: either add the feature's other top-level processes (per [`process-view-emission.md`](../../skills/architecture-design/references/procedures/process-view-emission.md) §2 rule 1), or change the view's `viewpoint` to `"Service Realization"` for single-process focus. Reference: ArchiMate® 3.2 §14 (Viewpoints) + this reference §9.7.
- **`AD-B-12` Sub-process without its own §9.3 drill-down** — a Business Process X with at least one incoming `xsi:type="Composition"` relationship from another Business Process Y, AND no `<view>` with `viewpoint="Service Realization"` rooted on X (rooted = X is the topmost element in the realisation stack, identifier match). Suppression: X carrying `<property propertyDefinitionRef="propid-drilldown-exclude"><value xml:lang="en">true</value></property>` (per §6.4b). Severity: `warn`. Action: emit a §9.3 view rooted on X, or set `propid-drilldown-exclude=true` if intentional. Reference: this reference §9.3 + [`process-view-emission.md`](../../skills/architecture-design/references/procedures/process-view-emission.md) §2 rule 2.
- **`AD-B-13` Top-level process missing from §9.7** — a Business Process X with **no** incoming `xsi:type="Composition"` relationship from any other Business Process (X is top-level), AND X is not present as a node in any `<view>` with `viewpoint="Business Process Cooperation"` in the same canonical file. Suppression: X carrying `<property propertyDefinitionRef="propid-coop-view-exclude"><value xml:lang="en">true</value></property>` (per §6.4b). Severity: `warn`. Action: add X as a node in the feature's §9.7 view, or set `propid-coop-view-exclude=true` if intentional (deprecated, planned, external). Reference: this reference §9.7 + [`process-view-emission.md`](../../skills/architecture-design/references/procedures/process-view-emission.md) §2 rule 1.

### Drift smells — `AD-DR-*`

Runtime smells that require reading current code / IaC / workflow state against the diagram. These extend the existing `AD-DR-*` namespace documented in [`drift-detection.md`](../../skills/architecture-design/references/procedures/drift-detection.md); the two new codes below cover hybrid process drift (§7.4).

- **`AD-DR-11` Model process has no code** — a Business Process / Event / Interaction in a `docs/architecture/**/*.oef.xml` file has no matching Durable Functions orchestrator or Logic Apps workflow in the repo (either by `LIFT-CANDIDATE source=` mismatch, or by `<name>` mismatch when no `LIFT-CANDIDATE` is present) and no `planned` / `external` property marking it as intentionally absent.
- **`AD-DR-12` Code workflow has no model** — a Durable Functions orchestrator or Logic Apps workflow exists in the repo but no Business Process element in any OEF file names it (directly or via `LIFT-CANDIDATE source=`). The architecture model trails the code; either the workflow should become a Business Process, or the model should acknowledge it as out of scope.

## 9. Diagram kinds supported in v1

The skill supports seven ArchiMate diagram kinds. Each kind fixes the element palette and the concern, preventing layer soup. The §9 English label and the OEF `viewpoint=` attribute value are identical — every kind maps 1:1 to a canonical ArchiMate 3.2 Viewpoint per `ViewpointsEnum`.

### 9.1 Capability Map (Strategy + Business)
**`viewpoint="Capability Map"`.** Elements: Capability (primary), Business Function, Business Service (optional). Realisation and Composition relationships. Used by architects to answer "what do we do" before "how do we do it."

**Professional gate.** A Capability Map separates business capability from application or implementation structure. When known, it surfaces ownership, maturity, priority, investment relevance, or capability realisation; otherwise it is probably an application inventory in disguise (`AD-Q1` / `AD-Q5`).

### 9.2 Application Cooperation (Application)
**`viewpoint="Application Cooperation"`.** Elements: Application Component (primary), Application Service, Application Interface, Application Collaboration. Serving, Used-by, Realisation, Composition, Assignment. Used to show how software parts cooperate.

**Professional gate.** The view clarifies collaboration boundaries, integration paths, and responsibility split. Components should not merely sit next to each other; the selected relationships should make the cooperation pattern legible (`AD-Q1`, `AD-Q4`, `AD-Q6`).

### 9.3 Service Realization (Business + Application + Technology, optionally UI-aware)
**`viewpoint="Service Realization"`.** Two content modalities under one canonical viewpoint:

- **Service-rooted modality.** Business Service (primary, at the top), Application Service realising it, Application Component realising the Application Service. Realisation relationships form the spine. Used to answer "which software realises which business service" at a single glance.
- **Process-rooted UI-aware modality.** Business Process (primary, at the top); UI Application Component Realising the Business Process for user-driven steps; Application Interface Assigned to the UI Component (the route); Application Service Realising the Business Process via the backend call path; Backend Application Component Realising the Application Service; Technology Service / Node hosting both Components. Distinct from the Service-rooted modality (which starts from Business Service); the Process-rooted modality starts from a Business Process and includes the UI entry point, so full-stack readers can see both the front-end surface and the back-end stack in one diagram. Blazor idiom (v1): UI Application Component `<name>` = the Blazor page component's file path (e.g., `src/Client/Pages/Checkout.razor`); Application Interface `<name>` = the `@page` route string (e.g., `/checkout`). Other frontend stacks follow the same convention without a v1 callout.

UI-awareness is a content rule, not a kind discriminator: when a §9.3 view contains a Business Process with a Business Actor Assignment in the paired §9.7 view (per §4.1's user-driven definition), the UI entry point is required (`AD-B-10`).

Layout follows the default banded grid; the Application band may hold up to 4 elements (UI Component, Interface, Service, Backend Component) at the `AD-L4` 4-per-cell budget.

**Professional gate.** The realisation chain is the message: Business Process or Business Service → Application Service → Application Component → Technology Service / Node when technology is in scope. A view that names services without this auditable spine triggers `AD-Q9` even if its individual relationships are valid.

**View emission contract.** Per [`process-view-emission.md`](../../skills/architecture-design/references/procedures/process-view-emission.md), every orchestrator-level Business Process (top-level + Composition-nested sub-orchestrators) has its own §9.3 view rooted on it in the canonical feature file. Sub-processes without their own view trigger `AD-B-12` unless the architect sets `propid-drilldown-exclude=true` on the process (§6.4b). Activity-call steps (Triggering-chained, not Composition-nested) stay as nodes inside the parent's §9.3 — they are not orchestrator-level and do not get separate views.

### 9.4 Technology Usage (Application + Technology)
**`viewpoint="Technology Usage"`.** Elements: Application Component, Technology Service, Node, System Software, Artifact. Used-by, Realisation, Assignment, Composition. Path and Communication Network when networking is material. Matches the canonical ArchiMate Technology Usage Viewpoint (how applications use technology infrastructure); distinct from the bare Technology Viewpoint which is technology-only.

**Professional gate.** The view distinguishes runtime infrastructure, deployment nodes, system software, technology services, artifacts, and network paths when those concerns matter. If latency, residency, or platform ownership is part of the question, Path / Communication Network elements must carry that point (`AD-12`, `AD-Q6`).

### 9.5 Migration and Deployment Topology (Implementation & Migration + any layer)
**`viewpoint="Migration"`.** The OEF viewpoint stays the ArchiMate Migration viewpoint, but the skill distinguishes two content patterns:

- **Migration view** — true as-is → to-be architectural state change. Elements: Plateau (at least Baseline and Target), Gap, Work Package, Deliverable, Implementation Event. Plateau-to-Plateau Triggering / Gap chains are valid only when the view documentation states the migration intent.
- **Deployment Topology view** — parallel environments such as development, staging, and production. Plateaus are sibling snapshots that coexist. They are not connected by Triggering relationships to each other. One Work Package may Realize every environment Plateau, with environment-specific configuration recorded as Plateau documentation or properties.

Extract never invents as-is / to-be migration from workflow files. Workflow extraction emits a Deployment Topology pattern when environments are present and a single target Plateau when only one deployment target is evidenced.

**Professional gate.** A Migration view shows Plateau, Gap, Work Package, Deliverable, and dependency logic clearly enough to support planning. A Deployment Topology view shows the actual environments evidenced by code/IaC/workflows and the Work Package(s) that deploy to them. Fictitious environments trigger `AD-19`; Plateau-to-Plateau Triggering without migration intent triggers `AD-20`.

### 9.6 Motivation (Motivation only)
**`viewpoint="Motivation"`.** Elements: Stakeholder, Driver, Assessment, Goal, Outcome, Requirement, Constraint, Principle. Influence and Realisation relationships. Linked to Core views via separate realisation arrows from Core elements to Motivation elements.

**Professional gate.** The view distinguishes drivers, assessments, goals, outcomes, principles, constraints, and requirements, then connects them to the architecture elements they influence or constrain. Floating motivation elements trigger `AD-Q7`.

### 9.7 Business Process Cooperation (Business only)
**`viewpoint="Business Process Cooperation"`.** Elements: Business Process, Business Event, Business Interaction (primary, Behaviour); Business Actor, Business Role, Business Collaboration (Active structure, optional); Business Object, Contract, Product, Data Object (Passive structure, optional). Relationships: Triggering and Flow form the temporal chain; Assignment binds Actor / Role / Collaboration to Behaviour; Access binds Behaviour to Passive structure; Serving surfaces outward-facing Business Services. Used to answer "in what order does the business do what, and with whom". Layout is the process-flow exception in §6.4a — Behaviour left-to-right along the Triggering/Flow chain, Active structure above, Passive structure below. User-driven steps carry a Business Actor Assignment per §4.1; see §9.3's Process-rooted modality for the cross-layer drill-down that shows how each step is realised, including the UI surface.

**Professional gate.** The view shows handoffs, responsibilities, triggering, flow, passive objects accessed, and terminal value outcome. A view that merely places actors and systems around a process name triggers `AD-Q8`.

**View emission contract.** Per [`process-view-emission.md`](../../skills/architecture-design/references/procedures/process-view-emission.md), a feature has exactly one §9.7 view containing every top-level Business Process (root of its Composition tree — no incoming Composition from another Business Process). Top-level processes missing from the §9.7 trigger `AD-B-13` unless the architect sets `propid-coop-view-exclude=true` (§6.4b). A §9.7 view containing only one Business Process triggers `AD-B-11` (cooperation requires ≥ 2 cooperating elements per the spec definition).

Diagram kinds not in this list (Product Map, Organisation Structure, Information Structure, Layered, Physical) are expressible in OEF XML — the element and relationship vocabulary is unbounded — but the skill does not generate them as a first-class diagram kind in v1. An architect can model them directly in Archi and the skill's Review mode will still parse the result.

## 10. Review checklist

Each item is tagged with a verification layer consistent with other reference docs: `[static]` (can be verified from the diagram source alone), `[visual]` (requires rendering and inspecting diagram output), `[runtime]` (requires reading the current code / IaC at the canonical paths).

- [static] Diagram declares its kind (§9) implicitly via element palette; no layer soup (`AD-1`, `AD-7`).
- [static] Every relationship is valid per ArchiMate 3.2 Appendix B (`AD-2`).
- [static] Every OEF `identifier` attribute is unique across the file; view-node and view-connection identifiers do not reuse model element or relationship identifiers (`AD-17`).
- [static] Every view `<node>` carries `xsi:type` (one of `Element` / `Container` / `Label`); every view `<connection>` carries `xsi:type` (one of `Relationship` / `Line`) (`AD-15`). Grep-verifiable: every `<node ` and `<connection ` inside `<views>` has an `xsi:type=` attribute.
- [static] Every generated view is materialized with Element node geometry (`elementRef`, `x`, `y`, `w`, `h`) and Relationship connections for the relationships that carry the view's visual story.
- [static] The `<metadata>` block's catalog payload elements come from a non-ArchiMate namespace (`AD-16`). Grep-verifiable: skip the optional `<schema>` and `<schemaversion>` prelude (these legitimately inherit the ArchiMate default namespace per `SchemaInfoGroup`); for every other direct child of `<metadata>`, confirm it carries either a default namespace declaration `xmlns="..."` or a prefixed declaration `xmlns:<prefix>="..."` (or inherits one from an ancestor) whose URI is not `http://www.opengroup.org/xsd/archimate/3.0/`.
- [static] Every emitted `.oef.xml`'s top-level child elements appear in the OEF-mandated sequence per §6 (`AD-17`). Grep-verifiable: parse the file's direct children of `<model>` (via `xmlstarlet sel -t -m '/*[local-name()="model"]/*' -v 'local-name()' -n` or equivalent — the namespace-agnostic form avoids xmlstarlet's default-namespace binding pitfall) and confirm the sequence is a valid prefix of `name, documentation, metadata, elements, relationships, organizations, propertyDefinitions, views`; any model-root `properties` child is invalid.
- [static] Each view answers a stated architecture question and uses a viewpoint that matches that concern (`AD-Q1`, `AD-Q2`).
- [static] Each view is reviewable without hidden explanation: density is bounded, visual hierarchy is clear, relationships emphasize the main path, and labels suit the intended architecture audience (`AD-Q3`, `AD-Q4`, `AD-Q6`, `AD-Q10`).
- [static] Conceptual or stakeholder-facing views do not leak low-level implementation trivia except where the view explicitly traces implementation (`AD-Q5`).
- [static] Every behaviour element has an active structure assigned; every passive-structure element is accessed only through a behaviour (`AD-3`, `AD-4`).
- [static] Realisation chains are complete for the scope of the diagram: Business Service has a realising Application Service; Application Service has a realising Application Component; Application Component is assigned to a Technology Node if the diagram reaches Technology (`AD-6`).
- [static] Association used at most once per diagram, and only where no other relationship fits (`AD-5`).
- [static] Element identifiers and `<name>` values agree semantically (`AD-8`).
- [static] Extract output with forward-only layers carries the FORWARD-ONLY marker (`AD-14`).
- [static] Extract output with lifted Business Process / Event / Interaction elements carries a per-element `LIFT-CANDIDATE` comment with `source=` and `confidence=` attributes (`AD-14-LC`).
- [static] Motivation views connect drivers, goals, outcomes, principles, constraints, and requirements to the architecture elements or decisions they affect (`AD-Q7`).
- [static] Business Process Cooperation (§9.7) views have a connected Triggering/Flow chain (`AD-B-1`); participants are Assigned to Behaviour (`AD-B-2`); Passive structure is Accessed by Behaviour (`AD-B-3`); only Business-layer elements are present (`AD-B-4`); and the chain has a declared entry Event and terminal outcome (`AD-B-5`).
- [static] Business Process Cooperation (§9.7) views show handoffs, responsibilities, and value flow clearly enough for review (`AD-Q8`).
- [static] Service Realization (§9.3) views in the Process-rooted modality show a Realisation chain from Business Process through at least one Application Service (`AD-B-6`); §9.3 views in either modality show an Application Component realising the Application Service (`AD-B-7`). Between-view invariant: each §9.7 Business Process has a realising chain in a §9.3 view (Process-rooted modality) for the same feature (`AD-B-8`), and each §9.3 Application Service that realises a Business Process realises one present in some §9.7 view for the same feature (`AD-B-9`).
- [static] Service Realization (§9.3) views expose an auditable realization spine rather than just naming services (`AD-Q9`).
- [static] §9.3 views in the Process-rooted modality for user-driven Business Processes (carrying a Business Actor Assignment per §4.1) include a UI Application Component and Application Interface at the entry point (`AD-B-10`).
- [static] Every `<view>` with `viewpoint="Business Process Cooperation"` contains ≥ 2 Business Process elements (`AD-B-11`).
- [static] Every Business Process with an incoming `xsi:type="Composition"` relationship from another Business Process has a `<view>` with `viewpoint="Service Realization"` rooted on it, unless `<property propertyDefinitionRef="propid-drilldown-exclude"><value xml:lang="en">true</value></property>` is set on the process (`AD-B-12`).
- [static] Every Business Process with no incoming `xsi:type="Composition"` relationship from another Business Process is present as a node in some `<view>` with `viewpoint="Business Process Cooperation"` in the same canonical file, unless `<property propertyDefinitionRef="propid-coop-view-exclude"><value xml:lang="en">true</value></property>` is set on the process (`AD-B-13`).
- [static] Every element's `y` coordinate respects the relative layer ordering of its ArchiMate layer (Strategy above Business above Application above Technology above Physical) after Tier 1 phase 6 bbox normalisation per §6.4a (`AD-L1`).
- [static] No two `<node>` placements in the same view overlap — bounding-box intersection is zero for every pair at the same nesting depth (`AD-L2`).
- [static] Every element's `w ≥ 120` and `h ≥ 55`; `w` is large enough that the `<name>` does not truncate at the default Archi font (heuristic: 7 px per character) (`AD-L3`).
- [static] Each view carries at most 20 elements and 30 relationships; nesting depth ≤ 2 (`AD-L4`).
- [static] Edge crossings per view are bounded by `node_count / 6` (threshold tightened in 0.8.0; see §8) (`AD-L5`).
- [static] Every `<connection>` in the view uses orthogonal routing: bend points are present whenever source and target do not share an x or y coordinate (`AD-L6`).
- [static] No element is simultaneously nested inside a parent and connected to that parent by a visible `<connection>` — the parent-child relationship is represented once, not twice (`AD-L7`).
- [static] Every `x`, `y`, `w`, `h`, and `<bendpoint>` coordinate is a multiple of 10 (`AD-L8`).
- [static] Every Realization / Used-by / Serving relationship between same-layer elements respects topological direction (`AD-L9`).
- [static] The view's used-region top-left is at `(40, 40) ± 10 px` after Tier 1 phase 6 bbox normalisation (`AD-L10`).
- [static] Every `<connection>` segment avoids `<node>` bounding boxes other than the source, target, and required source/target ancestor containers (`AD-L11`); preserved bendpoints are revalidated after relationship replacement or source/target inversion.
- [static] Every non-legend `<node>` in a view participates in at least one same-view connection (`AD-L12`).
- [static] Parallel or near-parallel connectors are lane-spaced so arrowheads and labels do not stack (`AD-L13`).
- [static] Inter-layer whitespace is compact enough that occupied bands read as one diagram, not disconnected islands (`AD-L14`).
- [static] Local fan-out connectors do not crisscross or route across non-endpoint sibling nodes (`AD-L15`).
- [visual] When an Archi or ArchiMate-conformant renderer is available in the current project, render every view and inspect all outputs before claiming `diagram-readable` or `review-ready`; do not sample. Reject views with connector-through-node, stacked arrows, orphan elements, excessive empty bands, or fan-out crisscross even if the XML is otherwise model-valid. If no renderer is available, disclose that render inspection was not run.
- [runtime] Application Components in this diagram correspond to real projects in the solution (for .NET: `*.csproj`); components that have no project are flagged as *planned* or *external*.
- [runtime] Technology Nodes in this diagram correspond to IaC resources (for Azure: Bicep). Nodes that have no IaC are flagged as *planned* or *out-of-scope*.
- [runtime] Implementation & Migration Work Packages in this diagram correspond to workflows in `.github/workflows/` where applicable.
- [runtime] Application Components that represent HTTP APIs have corresponding Azure Function Apps or equivalent described by `serverless-api-design` output; drift between the ArchiMate component set and the deployed API set is reported.
- [runtime] Application Components that represent UI apps have corresponding Blazor WebAssembly projects or equivalent described by `responsive-design` output; drift is reported.
- [runtime] Business Processes in `docs/architecture/**/*.oef.xml` have matching Durable Functions orchestrators or Logic Apps workflows in the repo (`AD-DR-11`), and every Durable Functions orchestrator and Logic Apps workflow is referenced by some Business Process (`AD-DR-12`); `LIFT-CANDIDATE source=` paths resolve to existing files.

## 11. Authoritative sources

- The Open Group, *ArchiMate® 3.2 Specification* (C226), March 2023. Chapter references in this document point to this version.
- The Open Group ArchiMate 3.2 Appendix B — Relationships Table (canonical source of well-formedness rules).
- The Open Group ArchiMate Model Exchange File Format 3.2 (OEF) — out of scope for v1 but the canonical interchange format.
- The Open Group ArchiMate® Model Exchange File Format (OEF) 3.2 — Appendix E of C226 — the serialisation format the skill emits. The Open Group publishes the canonical XSD schemas at `http://www.opengroup.org/xsd/archimate/`; the skill references them by URL in generated files and does not bundle them.
- Archi ([archimatetool.com](https://www.archimatetool.com)) — the free, open-source reference ArchiMate modelling tool. Used by architects to open, visualise, and edit the skill's OEF output.

## 12. Sibling design references

The `architecture-design` skill co-exists with two siblings in `souroldgeezer-design`. Each sibling's output is an Application Component in the architect's model — the sibling references document what that component looks like on its own terms.

- `../ui-reference/responsive-design.md` — UI surface of a Blazor WebAssembly or HTML/CSS/JS Application Component.
- `../api-reference/serverless-api-design.md` — HTTP API surface of an Azure Functions .NET Application Component, including Technology-Layer details (Cosmos DB, Blob Storage, Key Vault, managed identity) that appear as Nodes and System Software in ArchiMate Technology Usage views.
