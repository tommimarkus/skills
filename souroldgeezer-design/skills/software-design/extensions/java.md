# Java Software Design Extension

Load for `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle*`,
`mvnw`, `gradlew`, `module-info.java`, Java source, annotation processors,
generated sources, JAR packaging, Maven multi-module builds, or Gradle source
sets.

Covers Java package/module/build/API design. Delegate Spring or HTTP contracts
to `api-design`, security/dependencies to `devsecops-audit`, and tests to
`test-quality-audit`.

Sources: JLS packages/modules
https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html, Maven POM
https://maven.apache.org/pom.html, Gradle Java plugin
https://docs.gradle.org/current/userguide/java_plugin.html, and Gradle testing
https://docs.gradle.org/current/userguide/java_testing.html.

Java packages may be grouped into a module when cohesive; use that as a
platform fact, not a design recommendation. Inspect Maven/Gradle graph, source
sets, dependency scopes, `module-info.java`, public/exported surface,
annotation processors, generated code, DTO/entity/domain splits, static state,
concurrency owners, and validation (`mvn test`, `mvn verify`, `./gradlew
check`, compile, or smoke).

Defaults: package access is not hierarchical; public/exported types are
contracts; source sets are boundaries when classpath/artifacts differ;
entrypoints/adapters stay thin; records/sealed/enums/value objects carry
semantics; interfaces need current variation, external isolation, or real
duplication.

For Build mode, include `devsecops-audit` Quick review for reflection, dynamic
loading, serialization, JNI/JNA, process execution, annotation processors,
generated code, broad `opens`, or build-plugin changes when available.

Smell codes: `java.SD-B-*` for package/module/source-set/public-surface drift;
`java.SD-C-*` for policy-to-adapter deps, service location, static/global, or
generated/reflective coupling; `java.SD-S-*` for exception, DTO/entity/domain,
or stringly state drift; `java.SD-W-*` for one-implementation interfaces;
`java.SD-E-*` for broad `exports`/`opens`; `java.SD-Q-*` for reflection,
service-loading, or generated-boundary ownership gaps.
