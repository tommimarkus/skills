# Java Software Design Extension

Load for Java projects: `pom.xml`, `build.gradle`, `build.gradle.kts`,
`settings.gradle*`, `mvnw`, `gradlew`, `module-info.java`,
`src/main/java/**/*.java`, annotation processors, generated-source directories,
JAR packaging, Maven multi-module builds, or Gradle source sets.

This extension covers Java package/module/build/API design. It does not own
HTTP endpoint contracts, Spring application structure, security posture, or
test quality. Delegate HTTP/API concerns to `api-design`, frontend app concerns
to `app-design`, security and dependency posture to `devsecops-audit`, and test
quality to `test-quality-audit`.

## Sources

Use these sources for platform and build facts:

- Oracle Java Language Specification, chapter 7, packages and modules:
  https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html
- Apache Maven POM reference:
  https://maven.apache.org/pom.html
- Gradle Java Plugin:
  https://docs.gradle.org/current/userguide/java_plugin.html
- Gradle Java testing/source-set guidance:
  https://docs.gradle.org/current/userguide/java_testing.html

Cite the core software-design reference for design judgments. The Java
Language Specification states that packages may be grouped into a module when
they are sufficiently cohesive; treat that as a platform mechanism, not as a
blanket design recommendation.

## Assimilation Signals

Inspect only what affects design shape:

- build topology: Maven parent/child modules, Gradle settings, included builds,
  source sets, dependency scopes/configurations, toolchains, generated sources,
  and annotation processors;
- package and module surface: package names, `module-info.java`, `requires`,
  `exports`, `opens`, `uses`, `provides`, public classes, package-private
  types, sealed hierarchies, records, and public interfaces;
- dependency direction: imports, Maven/Gradle module dependencies, framework
  adapters, persistence or messaging clients, reflection, and service loaders;
- API semantics: DTOs, entities, records, builders, checked/runtime exception
  boundaries, validation annotations, mappers, converters, and serialization
  types;
- state and concurrency: `static` mutable state, singletons, `ThreadLocal`,
  executor ownership, `CompletableFuture`, caches, lifecycle hooks, and shutdown
  paths;
- validation surface: `mvn test`, `mvn verify`, `./gradlew test`,
  `./gradlew check`, `javac`/toolchain settings, static analysis configured by
  the project, or a project smoke command.

## Design Defaults

- Package names should tell the boundary story. Do not treat subpackages as
  privileged access zones; Java package access is per package, not hierarchical.
- Use `module-info.java` when exported and opened packages express a real
  distribution, encapsulation, or runtime-reflection boundary.
- Public classes, public members, and exported packages are compatibility
  contracts. Prefer package-private or narrower modules until a downstream
  caller needs the surface.
- Keep `main`, `test`, integration-test, generated-source, and fixture source
  sets honest. A build source set is a design boundary when other code depends
  on its classpath or artifacts.
- Keep entrypoints and framework adapters thin. Domain policy should not live
  in servlet filters, controllers, CLI launchers, annotation processors, or
  generated glue unless that surface is the actual product boundary.
- Prefer constructor or factory injection for explicit process boundaries.
  Avoid service locator access, hidden globals, and static mutable state as
  cross-module communication.
- Treat records, sealed types, enums, and named value objects as semantic tools.
  Do not use raw `String`, `Map`, tuple-like records, or booleans for domain
  states that need names.
- Add interfaces or abstract bases only when they isolate an external boundary,
  support current variation, or remove real duplication.

## Validation Requirement

For Build mode on Java targets, the `Validation step` MUST include a
`devsecops-audit` Quick review when reflection, dynamic class loading,
serialization, JNI/JNA, process execution, annotation processors, generated
code, broad module `opens`, or build-plugin changes are in scope and that skill
is available. If unavailable, state that in `Delegations` or `Limits` and use
the cheapest applicable fallback:

- Maven: `mvn -q test` or `mvn -q verify` when the project defines the verify
  lifecycle meaningfully.
- Gradle: `./gradlew test` or `./gradlew check`.
- Compile-only: project compiler task, `mvn -q -DskipTests compile`, or
  `./gradlew classes` when tests are out of scope.

## Smells

| Code | Signal | Default |
|---|---|---|
| `java.SD-B-1` | Package names, Maven/Gradle modules, and runtime modules tell conflicting boundary stories. | warn |
| `java.SD-B-2` | `public` or exported types expose implementation details that only one package/module should know. | warn; block when new public API |
| `java.SD-B-3` | Build source sets mix production, tests, fixtures, generated code, or integration harnesses without a classpath rule. | warn |
| `java.SD-B-4` | Framework entrypoint, controller, filter, listener, or CLI launcher owns reusable policy. | warn |
| `java.SD-C-1` | Maven/Gradle module dependency points from policy into adapter, infrastructure, or framework code. | block when new |
| `java.SD-C-2` | Service locator, static singleton, `ThreadLocal`, or mutable global carries workflow state across boundaries. | warn; block when cleanup depends on it |
| `java.SD-C-3` | Annotation processor, generated mapper, or reflection registry owns business policy that cannot be reviewed independently. | warn |
| `java.SD-S-1` | Exception hierarchy collapses domain, validation, transport, and infrastructure failures into one type. | warn |
| `java.SD-S-2` | DTO, persistence entity, and domain model are the same public type without an explicit boundary decision. | warn |
| `java.SD-S-3` | Raw strings, maps, booleans, or tuple-like records encode named domain states. | warn |
| `java.SD-S-4` | Async/concurrency boundary has no owner for executor lifecycle, cancellation, timeout, or backpressure. | warn |
| `java.SD-W-1` | Interface or abstract base wraps one concrete implementation solely for tests or ceremony. | info; warn when public |
| `java.SD-W-2` | Mapper/repository/service layer only forwards fields or CRUD calls without isolating a real boundary. | info |
| `java.SD-W-3` | Inheritance or template-method base class replaces a smaller composition or strategy seam without current variation. | warn |
| `java.SD-E-1` | `module-info.java` exports or opens broad packages without a named consumer or reflection reason. | warn |
| `java.SD-E-2` | Maven dependency management or Gradle version/catalog policy hides divergent runtime dependencies across modules. | warn |
| `java.SD-Q-1` | Reflection, dynamic proxies, generated code, or service loading form a boundary with no explicit owner or validation. | block when new |

## Review Notes

- Use Java platform docs only for what packages, modules, access, source sets,
  and build constructs mean. Use the core reference for why a boundary,
  dependency direction, abstraction, or public contract is healthy or unhealthy.
- Do not flag Java syntax, annotations, inheritance, interfaces, records,
  modules, Maven, or Gradle by themselves. Flag the boundary, coupling,
  semantic, evolution, or tradeoff risk and name the smaller shape that reduces
  it.
