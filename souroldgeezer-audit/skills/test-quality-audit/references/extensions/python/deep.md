# Extension: Python — deep (Deep mode only)

Loaded only in Deep mode (SUT enumeration, determinism, mutation). For smells,
detection, and carve-outs see [core](core.md).

## SUT surface enumeration

Python gap detection is approximate and deep-mode only. Consumed by [SKILL.md
§ SUT surface enumeration](../../../SKILL.md) — step 2.5 of the deep-mode
workflow. Applies under the unit and integration rubrics; do not run against
E2E-only targets.

### SUT identification

For a given test project or test directory:

1. Inspect imports from the test package and the project's metadata to identify
   the source package under test.
2. Exclude `tests/`, `.venv/`, build artifacts, generated caches, and migrations
   unless migration enumeration is active.
3. Prefer the project's declared source roots and public package entry points;
   if those are absent, inspect the non-test Python modules reached by the
   selected tests.

### Gap classes

Use the following source patterns to enumerate testable surfaces. Return each
match with its symbol or route identifier and `file:line`.

- **`Gap-API`:** public functions/classes in non-test modules matching
  `^def [a-zA-Z_][a-zA-Z0-9_]*\\(`, `^async def ...`, or `^class ...`, excluding
  names starting `_`.
- **`Gap-Route`:** decorators such as `@app.route`, `@router.get`,
  `@router.post`, Django `path(...)`, and `re_path(...)`.
- **`Gap-Migration`:** Alembic revision files under `versions/` or Django
  migration classes/files under `migrations/`.
- **`Gap-Throw`:** `raise <ExceptionType>` in public functions or route
  handlers.
- **`Gap-Validate`:** Pydantic field constraints, dataclass validation,
  Marshmallow schema fields, Django form/model validators, and explicit
  request-schema validators.

### Cross-reference matching

Cross-reference by symbol name, route string, migration revision/name, or
exception type in test names, assertions, and bodies. Classify identifier-only,
import-only, route-status-only, and valid-payload-only tests as
`referenced-weak` or `referenced-incidental`; they do not suppress gaps for
missing invalid, auth, boundary, throw, migration, or state-change behavior.
Treat all static-only results as probable until mutation or manual review
confirms them.

## Determinism verification

Consumed by [SKILL.md § Determinism verification](../../../SKILL.md) — step 4.5
of the deep-mode workflow. For a non-E2E scope, use the project's documented
test runner. When pytest is the project runner, the cheap rerun is:

```bash
pytest -q --maxfail=1
pytest -q --maxfail=1
```

Use only when the suite has fewer than 500 tests and the first run finishes
under 60 seconds, or when the user opts in. Compare failing test node IDs
between runs. If the project uses another runner, preserve its equivalent
non-E2E command and compare its test identities instead of introducing pytest.

## Mutation tool

Consumed by the deep-mode mutation section only. Use the project's configured
mutation command/tool before considering a fallback. The project-configured
mutation tool is authoritative. Inspect the project's
`pyproject.toml`, task runner, Makefile, CI workflow, and contributor docs for
the configured tool, detection command, source-selection options, and report
parser. Run that project command through its normal environment and preserve
its documented installation and output conventions; do not select a package
manager or replace a project command with a generic global invocation.

If no project-configured mutation equivalent exists, offer Mutmut as an
explicit fallback and run it only after the user accepts the fallback path.

### Tool name and link

- **Preferred:** the mutation tool and command declared by the project.
- **Fallback:** Mutmut, https://mutmut.readthedocs.io/

### Install instructions

For a project-configured tool, follow the project's existing development
dependency and task-runner instructions. For the Mutmut fallback, add Mutmut
through the project's documented development-dependency mechanism; do not
invent a package-manager choice. If the project has no dependency-management
convention, ask before proposing an installation command.

### Detection command

Run the project's configured tool-detection command first. Only for the
accepted Mutmut fallback, use the project's Python interpreter/environment for
this side-effect-free check:

```bash
python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('mutmut') else 1)"
```

### Run command

Run the project's configured mutation command, source-selection options, and
reporter first. Only for the accepted Mutmut fallback, use:

```bash
mutmut run
mutmut results
```

If a project-configured tool needs explicit source paths, use its documented
configuration. If the Mutmut fallback needs explicit source paths, use the
project's documented Mutmut configuration or
`mutmut run --paths-to-mutate <package>`.

### Known SUT limitations

- Native extension modules and generated C bindings may not be safely mutated;
  skip those modules and mutate the Python boundary around them.
- Framework-heavy import side effects can make mutation runs fail before tests
  start; use the project's existing configuration/source boundaries when
  available, or skip the affected target and disclose the limitation.
- E2E/browser targets are out of scope for mutation; mutate the application
  package, not browser tests.

### Output parser notes

For a project-configured tool, parse its configured machine-readable report or
summary first and preserve the tool's documented fields. Only for the accepted
Mutmut fallback, capture the overall killed/survived/timeout summary from
`mutmut results`. When JSON or JUnit output is configured for that fallback,
prefer that machine output; otherwise report text-summary evidence and
surviving mutant locations.
