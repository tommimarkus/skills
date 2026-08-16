# Extension: Java — deep-mode procedures

Deep-mode-only procedures for the Java test-quality-audit extension:
SUT surface enumeration, determinism verification, and the PIT mutation
tool declaration. Loaded only in Deep mode, for any rubric; Quick audits
never load it. Detection, dispatch, and smells stay in [`core.md`](core.md).

## SUT Surface Enumeration

Java gap detection is approximate and deep-mode only.

- **SUT identification:** inspect Maven modules, Gradle projects/source sets,
  `src/main/java`, package names, and imports from tests.
- **`Gap-API`:** public classes, exported module packages, public methods on
  application services, public records/enums, and CLI entrypoints.
- **`Gap-Route`:** controller/router/resource annotations, servlet/filter
  mappings, route tables, or framework adapters when API review is not already
  delegated.
- **`Gap-CLI`:** `main(String[] args)`, command classes, parser subcommands,
  exit-code contracts, stdout/stderr contracts, and generated launchers.
- **`Gap-Error`:** checked exceptions, runtime exception families, validation
  failures, typed error responses, and negative partitions.
- **`Gap-Validate`:** Jakarta/Bean Validation annotations, custom validators,
  parser constraints, enum/state guards, and branch predicates.
- **`Gap-Migration`:** migration files, schema changelogs, and upgrade/downgrade
  scripts exercised by Java integration tests.

Identifier-only tests, import-only tests, status-only HTTP assertions,
compile-only references, and happy-path-only parameter rows are
`referenced-weak` for error, auth, migration, state-change, and invalid-input
gaps. Static-only gaps stay probable until mutation, coverage, or manual review
confirms them.

## Determinism Verification

Cheap rerun command for non-E2E scopes:

```bash
mvn -q test
mvn -q test
```

or for Gradle projects:

```bash
./gradlew test
./gradlew test
```

Use only when the suite is small enough to finish under 60 seconds per run or
the user opts in. Compare failing test classes/methods between runs. If the
project separates integration tests under Maven Failsafe or a Gradle custom
source set, rerun the project-specific integration command instead.

## Mutation Tool

### Tool name and link

PIT: https://pitest.org/

### Install instructions

For Maven, add `org.pitest:pitest-maven` to the build plugins or invoke the
plugin directly from the command line. For Gradle, use the project's configured
PIT Gradle plugin if present.

### Detection command

```bash
grep -R "pitest\\|org.pitest" pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts 2>/dev/null
```

### Run command

Maven:

```bash
mvn test-compile org.pitest:pitest-maven:mutationCoverage
```

Gradle when the PIT plugin is configured:

```bash
./gradlew pitest
```

### Known SUT limitations

- Cross-module tests need explicit PIT configuration; otherwise a module may be
  mutated against only its own tests and understate coverage.
- Generated code, annotation-processor output, framework proxies, and bytecode
  enhancement can produce poor mutant signal; mutate the handwritten module
  that owns policy when possible.
- E2E/browser suites are usually too expensive for mutation; mutate Java policy
  modules behind the browser/API boundary instead.
- Equivalent mutants and timeout-sensitive concurrency code require manual
  interpretation; surviving mutants are investigation evidence, not automatic
  findings.

### Output parser notes

Read `target/pit-reports/**/mutations.xml` for Maven runs when XML is enabled
by the project; otherwise report the HTML report directory and summarize
survived/no-coverage mutants by class and line. For Gradle plugin runs, prefer
the configured XML output path when present.
