# ArchiMate — a reference for architecture design

## 1. Context

`architecture-design` answers *what the enterprise consists of* — which capability does this serve, which application service realises it, which technology node hosts it, which motivational driver justifies its existence. Its sole notation is ArchiMate.

This reference is the authoritative ground for the skill. It grounds in **The Open Group ArchiMate® 3.2 Specification, March 2023** (C226). It is opinionated about layer scope, element use, relationship well-formedness, the ArchiMate® Model Exchange File Format (OEF) serialisation used as the sole output, and which layers are round-trip-able with code versus forward-only.

**Notation conformance.** The skill emits ArchiMate 3.2 models as **OEF XML** (The Open Group ArchiMate® Model Exchange File Format 3.2, Appendix E of C226). Files are loadable by Archi, BiZZdesign Enterprise Studio, Sparx Enterprise Architect, Orbus iServer, Avolution ABACUS, HOPEX, and every mainstream ArchiMate tool. The skill does not bundle The Open Group's XSD schemas; emitted files reference the canonical schema URL (`xsi:schemaLocation`) so downstream validators fetch it from The Open Group directly. Validation beyond the skill's own well-formedness checks is pushed to the architect's toolchain — open the file in Archi or run `xmllint --schema <schema-url> <file>.oef.xml`.

**Scope.** ArchiMate Core Framework (Business, Application, Technology layers) plus the Physical, Strategy, Motivation, and Implementation & Migration extensions. Composite elements (Location, Grouping) are in scope. ViewPoints are out of scope as a first-class construct in v1 — the reference instead documents a small set of diagram kinds that cover the concrete use cases (capability map, application cooperation, technology realisation, migration view). See §9.

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
Business / Application / Technology is the default palette. A diagram claiming to model "architecture" should draw from these three unless the diagram kind is explicitly a motivation view, a strategy view, a migration view, or a physical view. This keeps diagrams legible and prevents the "everything everywhere" soup that ArchiMate's expressive range enables.

### 2.5 Relationships have well-formedness constraints
Not every relationship is valid between every pair of element types. ArchiMate 3.2 Appendix B (Relationships Table) is the authoritative source. The skill's Review mode cites this table; Build and Extract emit only relationships that are well-formed per the table. A diagram with invalid relationships (e.g., a Business Process *realising* a Technology Node) is a smell regardless of how expressive it looks.

### 2.6 One layer does not imply one diagram
A layered architecture can still be shown on a single diagram; a single layer can still require multiple diagrams. The rule is *one concern per diagram*, not *one layer per diagram*. Capability Map, Application Cooperation, Technology Realisation, and Migration View are each a single concern that pins the diagram's kind.

### 2.7 Extractability tracks the layer model
Some layers live in code and infrastructure; others live in the architect's head and the business's strategy documents. This is a property of the notation, not a limitation of the skill — see §7.

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
- **Business Collaboration** — an aggregate of two or more Actors or Roles that cooperate to perform collective behaviour.
- **Business Process** — a time-ordered choreography of work steps that delivers a defined business outcome (order shipped, claim paid, user onboarded). Distinct from Business Function in being intrinsically sequential rather than competency-grouped.
- **Business Function** — behaviour grouped by competency or capability rather than by sequence — *Procurement*, *Treasury*, *Customer Support*. Reorders orthogonally to Processes: the same Process typically passes through multiple Functions.
- **Business Interaction** — collective behaviour performed by a Collaboration.
- **Business Service** — the exposed behaviour of a Process, Function, or Interaction that delivers value to a customer. Services, not processes, are what the Application Layer realises or consumes.
- **Business Event** — something that happens (internally or externally) that triggers or is triggered by business behaviour.
- **Business Object** — a unit of information with business relevance. Customer, Contract, Order. The Data Object in the Application Layer *realises* the Business Object.
- **Contract** — the specification of rights, obligations, and service levels between a provider and a consumer — the behavioural agreement (SLA, data-sharing terms, compliance scope) captured independently of any specific implementation.
- **Product** — a commercial or internal bundle — a coordinated set of Services, Business Objects, and Contracts packaged and delivered as one. Example: a *Premium Support* Product bundling a Service Desk service, an SLA, and customer-portal access.

**Default.** Model the Business Layer via Business Process and Business Service first; add Function only when a process is too fine-grained; add Actor/Role only when ownership matters to the diagram.

### 4.2 Application Layer (ArchiMate 3.2 Chapter 6)

- **Application Component** — a software unit that is independently deployable and replaceable — a microservice, a library, a serverless Function App, a Blazor WebAssembly client, a worker. Components expose behaviour through Application Interfaces and realise Application Services.
- **Application Collaboration** — an aggregate of two or more Components cooperating.
- **Application Interface** — the consumption surface of an Application Service — an HTTP endpoint, a gRPC contract, a UI route, a library method signature — through which a Role, another Component, or a Technology Node actually invokes the Service.
- **Application Function** — automated behaviour performed by a Component.
- **Application Process** — a sequence of application behaviours that achieves a specific result.
- **Application Interaction** — collective application behaviour performed by a Collaboration.
- **Application Service** — the exposed behaviour that fulfills a need (often a Business Service).
- **Application Event** — a state change that triggers or is triggered by application behaviour.
- **Data Object** — an automation-facing data structure — records, JSON payloads, database rows, message bodies — that Application Components read, write, or transform. Typically realises a Business Object from the business layer.

**Default.** Model via Application Component, Application Service, and Application Interface as the triad: the component *realises* the service, the service is *exposed through* the interface. Use Application Function only when the component's internals matter to the diagram.

### 4.3 Technology Layer (ArchiMate 3.2 Chapter 7)

- **Node** — a runtime or hosting container that holds System Software and Artifacts and exchanges data with other Nodes. Typical modelling units: a virtual machine, a Kubernetes pod, an Azure App Service / Function App instance, an App Service plan, a physical data-centre server.
- **Device** — a physical computational resource.
- **System Software** — software environment for specific types of components and data objects. The .NET runtime, a database engine, an operating system.
- **Technology Collaboration** — an aggregate of two or more Nodes cooperating.
- **Path** — a link between Nodes along which communication can occur. An instance of a Communication Network.
- **Communication Network** — a medium between Nodes.
- **Technology Interface** — the access mechanism through which a Node's Technology Service becomes consumable — a network endpoint, a protocol binding, a shared-resource handle.
- **Technology Function** — automated behaviour performed by a Node.
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

**Default.** Use Plateau + Gap + Work Package in any Migration View that answers "how do we get from here to there." A Migration view without a Plateau axis is not a Migration view.

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

- **Specialisation** — element is a specialised form of another. Solid line with open triangle (same notation as UML generalisation).

### 5.5 Well-formedness rules (the short version)

- **Active structure ≠ behaviour ≠ passive structure.** Composition, Aggregation are within an aspect; Assignment crosses aspects.
- **Realisation is directional and crosses abstraction levels.** Application Service → Business Service; Application Component → Application Service; Technology Service → Application infrastructure needs.
- **Serving is directional.** The served element depends on the serving element. A Business Service is *served by* an Application Service, not the other way round.
- **Triggering and Flow live among behaviour elements.** Do not Trigger a Business Object — Trigger a Process that Accesses the Object.
- **Influence is Motivation-only in origin.** Influence a Goal, a Principle, a Requirement — not an Application Component (use Association or a Motivation–Core Realisation instead).

When in doubt, consult ArchiMate 3.2 Appendix B before emitting a relationship the reference has not surfaced here.

## 6. OEF XML serialisation

The skill emits ArchiMate 3.2 models in The Open Group's **ArchiMate® Model Exchange File Format (OEF) 3.2**, defined in Appendix E of the ArchiMate 3.2 Specification (C226). OEF XML is the canonical portable interchange format for ArchiMate models; it is read and written by Archi, BiZZdesign Enterprise Studio, Sparx Enterprise Architect, Orbus iServer, Avolution ABACUS, HOPEX, and other conformant tools.

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
    Technology-Realisation view for the checkout feature.
    Generated by architecture-design; do not hand-edit layout coordinates.
  </documentation>

  <!-- elements, relationships, organizations, views go here -->
</model>
```

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
          viewpoint="Technology">
      <name xml:lang="en">Checkout — Technology Realisation</name>

      <node identifier="id-n-api" elementRef="id-orders-api"
            x="120" y="120" w="180" h="64"/>
      <node identifier="id-n-svc" elementRef="id-orders-place"
            x="120" y="220" w="180" h="64"/>
      <node identifier="id-n-cosmos" elementRef="id-cosmos-main"
            x="120" y="340" w="180" h="64"/>

      <connection identifier="id-c-1" relationshipRef="id-rel-1"
                  source="id-n-api" target="id-n-svc"/>
      <connection identifier="id-c-2" relationshipRef="id-rel-2"
                  source="id-n-api" target="id-n-cosmos"/>
    </view>
  </diagrams>
</views>
```

**Viewpoint attribute** carries the canonical ArchiMate 3.2 viewpoint name when one applies (Application Cooperation, Technology, Motivation, Migration, Implementation and Deployment, etc.); custom kinds may omit it. The skill's supported diagram kinds (§9) map to these values.

**Element identity is shared across views.** Placing an element in three diagrams creates three `<node>` entries — three placements with their own coordinates — but the element itself appears once in `<elements>`. This is the model-vs-view separation at the heart of OEF: an Application Component is *one* thing, and every view that shows it shows the same thing.

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
- **XSD validation is not the skill's job.** OEF files are structurally validated by the downstream tool (Archi on import; `xmllint --schema <url>`). The skill enforces ArchiMate well-formedness (layer discipline, Appendix B relationship validity) in Build and Review; it does not run schema validation at runtime. See §1 for the rationale.
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
| **Business** | Business Processes, Services, Actors, Roles live in domain understanding, not in code. An Azure Function named `ProcessOrder` is not a Business Process — it may be the Application Function realising one, but the Process itself is a decision the architect makes | Emitted as a typed stub: `' forward-only — architect fills in: Business Layer` block with suggested placeholders inferred from Application Component names (e.g., a Component called `OrdersApi` implies a plausible Business Service *Order Management*) |
| **Motivation** | Drivers, Goals, Outcomes, Principles, Requirements live in strategy documents, architectural decision records, compliance artefacts. Extracting them from code would be fabrication | Emitted as a typed stub identifying where the architect should input |
| **Strategy** | Capabilities and Value Streams are organisational artefacts, not codebase ones | Emitted as a typed stub |

### 7.3 The forward-only marker

Every Extract output that includes typed stubs for forward-only layers prefixes those sections with:

```
' =============================================================================
' FORWARD-ONLY — this layer was not extracted from source
' The architect must fill in: <layer name>
' The skill inferred suggestive placeholders from Application element labels
' =============================================================================
```

The footer (§9 of SKILL.md) lists which layers were lifted vs stubbed so the architect's review focus is clear.

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
- **`AD-14` Forward-only layer emitted without the marker** — Extract output that populated Business/Motivation/Strategy elements without the `FORWARD-ONLY` header block.

## 9. Diagram kinds supported in v1

The skill supports a deliberately small set of ArchiMate diagram kinds. Each kind fixes the element palette and the concern, preventing layer soup.

### 9.1 Capability Map (Strategy + Business)
Elements: Capability (primary), Business Function, Business Service (optional). Realisation and Composition relationships. Used by architects to answer "what do we do" before "how do we do it."

### 9.2 Application Cooperation (Application)
Elements: Application Component (primary), Application Service, Application Interface, Application Collaboration. Serving, Used-by, Realisation, Composition, Assignment. Used to show how software parts cooperate.

### 9.3 Application-to-Business Realisation (Business + Application)
Elements: Business Service (primary), Application Service realising it, Application Component realising the Application Service. Realisation relationships form the spine. Used to answer "which software realises which business service" at a single glance.

### 9.4 Technology Realisation (Application + Technology)
Elements: Application Component, Technology Service, Node, System Software, Artifact. Used-by, Realisation, Assignment, Composition. Path and Communication Network when networking is material.

### 9.5 Migration View (Implementation & Migration + any layer)
Elements: Plateau (primary — at least Baseline and Target), Gap, Work Package, Deliverable, Implementation Event. Elements from other layers appear *within* a Plateau to show state at that point in time.

### 9.6 Motivation View (Motivation only)
Elements: Stakeholder, Driver, Assessment, Goal, Outcome, Requirement, Constraint, Principle. Influence and Realisation relationships. Linked to Core views via separate realisation arrows from Core elements to Motivation elements.

Diagram kinds not in this list (Product Map, Organisation Structure, Business Process Cooperation, Information Structure, Service Realisation, Layered, Physical) are expressible in OEF XML — the element and relationship vocabulary is unbounded — but the skill does not generate them as a first-class diagram kind in v1. An architect can model them directly in Archi and the skill's Review mode will still parse the result.

## 10. Review checklist

Each item is tagged with a verification layer consistent with other reference docs: `[static]` (can be verified from the diagram source alone), `[runtime]` (requires reading the current code / IaC at the canonical paths).

- [static] Diagram declares its kind (§9) implicitly via element palette; no layer soup (`AD-1`, `AD-7`).
- [static] Every relationship is valid per ArchiMate 3.2 Appendix B (`AD-2`).
- [static] Every behaviour element has an active structure assigned; every passive-structure element is accessed only through a behaviour (`AD-3`, `AD-4`).
- [static] Realisation chains are complete for the scope of the diagram: Business Service has a realising Application Service; Application Service has a realising Application Component; Application Component is assigned to a Technology Node if the diagram reaches Technology (`AD-6`).
- [static] Association used at most once per diagram, and only where no other relationship fits (`AD-5`).
- [static] Element identifiers and `<name>` values agree semantically (`AD-8`).
- [static] Extract output with forward-only layers carries the FORWARD-ONLY marker (`AD-14`).
- [runtime] Application Components in this diagram correspond to real projects in the solution (for .NET: `*.csproj`); components that have no project are flagged as *planned* or *external*.
- [runtime] Technology Nodes in this diagram correspond to IaC resources (for Azure: Bicep). Nodes that have no IaC are flagged as *planned* or *out-of-scope*.
- [runtime] Implementation & Migration Work Packages in this diagram correspond to workflows in `.github/workflows/` where applicable.
- [runtime] Application Components that represent HTTP APIs have corresponding Azure Function Apps or equivalent described by `serverless-api-design` output; drift between the ArchiMate component set and the deployed API set is reported.
- [runtime] Application Components that represent UI apps have corresponding Blazor WebAssembly projects or equivalent described by `responsive-design` output; drift is reported.

## 11. Authoritative sources

- The Open Group, *ArchiMate® 3.2 Specification* (C226), March 2023. Chapter references in this document point to this version.
- The Open Group ArchiMate 3.2 Appendix B — Relationships Table (canonical source of well-formedness rules).
- The Open Group ArchiMate Model Exchange File Format 3.2 (OEF) — out of scope for v1 but the canonical interchange format.
- The Open Group ArchiMate® Model Exchange File Format (OEF) 3.2 — Appendix E of C226 — the serialisation format the skill emits. The Open Group publishes the canonical XSD schemas at `http://www.opengroup.org/xsd/archimate/`; the skill references them by URL in generated files and does not bundle them.
- Archi ([archimatetool.com](https://www.archimatetool.com)) — the free, open-source reference ArchiMate modelling tool. Used by architects to open, visualise, and edit the skill's OEF output.

## 12. Sibling design references

The `architecture-design` skill co-exists with two siblings in `souroldgeezer-design`. Each sibling's output is an Application Component in the architect's model — the sibling references document what that component looks like on its own terms.

- `../ui-reference/responsive-design.md` — UI surface of a Blazor WebAssembly or HTML/CSS/JS Application Component.
- `../api-reference/serverless-api-design.md` — HTTP API surface of an Azure Functions .NET Application Component, including Technology-Layer details (Cosmos DB, Blob Storage, Key Vault, managed identity) that appear as Nodes and System Software in ArchiMate Technology Realisation views.
