# Java Lifting Rules

Use for Extract when Java builds, modules, services, CLIs, hosted workers,
typed clients, or Java framework entrypoints are in scope. Load
`../source-weighting.md` before classifying ambiguous surfaces.

Generic Java first. Treat Spring-specific evidence and Quarkus-specific
evidence as additive framework signals, not the default classifier for every
Java source tree.

## Source Mapping

| Source evidence | Prefer | Avoid |
|---|---|---|
| Multi-module Maven or Gradle build, parent POM, settings file, or included build | Repository/package context and source evidence grouping | Application Component by itself |
| Deployable JAR, WAR, service, CLI, or worker module | Application Component | Capability, Business Actor, or Application Service without exposed behavior evidence |
| Public HTTP/resource/controller method, RPC endpoint, CLI command, SDK/client entrypoint, listener, or queue/topic consumer surface | Application Interface | Application Service when the access surface is the concern |
| Exposed behavior consumed by another component, client, route, message, or command | Application Service | Application Interface when behavior is the concern |
| Internal handler, use-case class, command handler, scheduled task body, algorithm, or module-owned logic | Application Function; Application Process when ordered behavior/outcome is the concern | Application Service if not exposed or consumed |
| DTO, record, event, message, schema-bound type, JPA entity, persistence model, or API payload | Data Object | Business Object without business-source evidence |
| Repository, DAO, gateway, mapper, or client adapter | Application Function or Application Component by boundary concern; Access relationship to Data Object when passive data use is identified | Data store or Business Object by name alone |
| Generated sources, OpenAPI/gRPC stubs, annotation-processor output, shaded JAR, native image, or container image | Artifact or Deliverable by concern | Application Component unless it represents a deployable runtime boundary |
| Batch, scheduler, saga, stream, or message choreography | Application Process by default; Business Process candidate only with outcome and participant context | Final Business Process from class or topic names alone |

## Spring Evidence

Spring-specific evidence is additive. Use it only after the generic Java rule
has established the source fact.

- `@Controller`, `@RestController`, `@RequestMapping`, WebFlux handlers, and
  Spring Cloud Gateway routes identify access surfaces.
- `@Service`, `@Component`, use-case beans, and handlers can support
  Application Function or exposed Application Service by concern; the annotation
  alone does not prove a service abstraction.
- Spring Boot auto-configuration, starters, profiles, and application
  properties are framework and runtime evidence; use them to confirm hosting,
  dependency, or configuration paths, not to create business architecture.
- Actuator endpoints are management access surfaces when observability or
  operations are in scope; otherwise keep them out of application collaboration
  views.
- `@Repository`, Spring Data repositories, `JdbcTemplate`, and JPA access paths
  support Access relationships to Data Objects when data use is clear.
- `@Scheduled`, `@Async`, Spring Batch jobs, listeners, and integration flows
  can support Application Event, Application Process, or Flow/Triggering by
  concern.

## Quarkus Evidence

Quarkus-specific evidence is additive. Use it only after the generic Java rule
has established the source fact.

- JAX-RS resources, RESTEasy Reactive routes, gRPC services, Picocli commands,
  and messaging connectors identify access surfaces.
- CDI beans, application services, command handlers, and Panache repositories
  can support Application Function, Application Component, or Access choices by
  boundary concern.
- Quarkus extensions and build steps are framework/runtime evidence; use them
  to confirm runtime capabilities or generated artifacts, not generic ArchiMate
  element types.
- Dev Services and profile-specific configuration are local/dev topology
  evidence unless source or architect intent says they represent target
  architecture.
- Scheduler, Reactive Messaging, Kafka, AMQP, and SmallRye flows can support
  Application Event, Application Process, Flow, or Triggering when ordering or
  message movement is the claim.
- Native-image, container-image, and deployment descriptors are Artifact or
  technology/deployment evidence unless they represent a runtime component
  boundary.

## Relationships

- Module dependency: Composition for strong package/part ownership; Serving
  only when runtime dependency behavior is the claim.
- Component to exposed behavior: Realization when the component fulfills the
  service abstraction.
- Component/service to endpoint, CLI, SDK, listener, or resource surface:
  Composition or Aggregation for ownership; Realization only when the model says
  the component fulfills the interface abstraction.
- Handler, scheduler, batch, or message sequence: Triggering when order or
  causality is the claim; Flow when payload movement is the claim.
- Repository/client data access: Access only when passive data use is
  identified.

## Package Output

Add source refs and only views with a clear question. Use source-backed groups
for deployable modules, bounded contexts, packages that express ownership,
runtime boundaries, messaging lanes, or meaningful dependency clusters. Avoid
grouping generic shared libraries, utility packages, or framework annotations
as architecture boundaries.
