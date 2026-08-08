# Python Software Design Extension

Load for Python packages, applications, libraries, and tooling:
`pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `src/` or flat
package layouts, `__init__.py`, modules and import graphs, wheel/sdist
distribution surface; repo-internal tooling under `scripts/`, `tools/`,
`bin/`, `dev/`, `tasks/`, `hack/`, or `ci/`; Python shebangs;
`[project.scripts]`, `console_scripts`, PEP 723 scripts, task runners, or CI
tools.

Covers Python package/module/application/library and tooling design. The
internal module, package, domain-model, and import design of a Python
service, application, or library is owned here; only its web/ASGI HTTP
contract layer (routes, request/response schemas, OpenAPI) delegates to
`api-design`, and UI to `app-design`. Delegate command injection, secrets,
supply chain, lockfiles, and permissions to `devsecops-audit`; delegate tests
to `test-quality-audit`.

Sources for platform facts: the import system
https://docs.python.org/3/reference/import.html, the Python Packaging User
Guide https://packaging.python.org/, PEP 8 https://peps.python.org/pep-0008/,
PEP 420 https://peps.python.org/pep-0420/, PEP 621
https://peps.python.org/pep-0621/, PEP 723 https://peps.python.org/pep-0723/,
PEP 561 https://peps.python.org/pep-0561/, the `asyncio` task and runner
documentation https://docs.python.org/3/library/asyncio-task.html and
https://docs.python.org/3/library/asyncio-runner.html, `contextvars`
https://docs.python.org/3/library/contextvars.html, typing
https://docs.python.org/3/library/typing.html, profiling
https://docs.python.org/3/library/profile.html, and uv docs
https://docs.astral.sh/uv/.

First assimilate the project rather than importing a preferred Python shape:
record the Python floor (`requires-python`, CI matrices, and runtime images),
framework and execution model, package layout, existing sync/async and
resource-lifetime conventions, public entrypoints, generated-code ownership,
and the checks and tools the repository already documents. Treat `pyproject.toml`,
lockfiles, task-runner configuration, and neighboring modules as evidence;
run the project's checks or say which evidence is unavailable. If the project
does not settle a choice, explain the forces and viable alternatives and make
the smallest safe move. This is an assimilation step, not a mandate to adopt
uv, a formatter, a type checker, or a particular framework.

Inspect package layout (`src/` or flat, `__init__.py` re-exports, `__all__`,
PEP 420 namespace packages), import graph and dependency direction,
distribution surface (`[project]` metadata, extras, entry points, `py.typed`,
wheel contents), ORM/schema/DTO/domain splits, entrypoints,
packaging/lock/version pins, import-time behavior, generated code, `sys.path`,
globals/caches, env reads, stdout/stderr, exit codes, subprocess
argv/cwd/env/timeout, `PATH` resolution, and validation selected from the
project's conventions (for example import smoke, `py_compile`, a distribution
build, or its configured type/lint checks).

For each file, socket, database session, HTTP client, stream, task group,
executor, or other resource, identify the owner that creates it, bounds its
lifetime, closes or cancels it, joins any child work, and reports failure.
Use `SD-C-6` when spawned work is detached or cancellation has no owner; a
context manager is evidence of ownership, not a required style. At every
sync/async boundary, name the event-loop owner, any executor or thread/process
pool owner, the blocking operation being crossed, and how cancellation and
failure travel back. Do not assume `asyncio.to_thread`, an executor, or a
background task is harmless merely because it avoids blocking the caller.
Use `contextvars` for genuinely task/request-local ambient metadata only when
the project needs that propagation; keep business state explicit when it
crosses a boundary, and distinguish context-local state from thread-local,
module-global, and process-global state. Apply the lifetime and cleanup test
to all of them (`SD-C-4` where mutable state couples flows).

Treat the distribution and typing surface as a contract: `py.typed`, public
annotations, overloads, protocols, re-exports, and generated stubs all affect
what consumers can rely on. Check that the package's declared and runtime
surfaces agree and that type-only claims do not silently stand in for runtime
validation; route HTTP schemas and API error contracts to `api-design`.
Before recommending a performance change, establish the user-visible measure,
capture a representative profile or other runtime evidence, and identify the
owning boundary for the bottleneck. Optimize the smallest evidenced hot path,
then re-measure; do not turn a profiler, benchmark, or tool choice into a
style rule. If retries, timeouts, fallbacks, or exception translation cross
layers, preserve their contract and name one owner: use core `SD-S-5` for
collapsed failure meanings and `SD-Q-4` for stacked failure handling.

Defaults: package and module boundaries follow ownership and policy; the
distribution/import surface (`[project]` metadata, entry points, extras, and
the names a package re-exports) is a public contract; consumers import the
public surface, not internal module paths; policy/domain modules do not
import adapters or frameworks; entrypoints own parsing/env/exit only; imports
do not run workflow, mutate `sys.path`, configure root logging, or do I/O;
workflow state moves through args/returns; machine stdout stays clean; exit
codes/cwd/tools/paths are public contracts when other tooling depends on
them; prefer stdlib unless a dependency removes more maintenance than it
adds; a shipped `py.typed` makes the annotated public surface a contract.

For Build mode, include `devsecops-audit` Quick review when available. Route
tests and test-quality claims to `test-quality-audit`; route HTTP/API contract
work to `api-design`; and leave implementation style to the project's own
conventions. Otherwise choose the project's available evidence, such as
`python -m py_compile`, import smoke, a distribution build, or configured
type/lint checks, and disclose unavailable checks rather than prescribing a
tool. Async lifetime/error findings use the core `SD-C-6`, `SD-S-5`, and
`SD-Q-4` codes; this extension adds no Python smell codes.

Smell codes: `python.SD-B-*` for package/module/public-surface, entrypoint,
top-level execution, cwd, import-time, or path-boundary drift;
`python.SD-C-*` for dependency-direction, deep-import, circular-import, or
global/env/PATH/tool coupling; `python.SD-S-*` for weak records,
ORM/schema/DTO/domain collapse, stdout mixing, exit-code collapse, or
subprocess string boundaries; `python.SD-W-*` for CLI/dispatcher or
package/abstraction ceremony; `python.SD-E-*` for undeclared
version/dependency/tool pins or unmanaged distribution-surface change;
`python.SD-Q-*` for shell-style glue without typed boundaries or annotations
treated as runtime validation.

Key codes: `python.SD-B-1` declared packaging and the real import surface
disagree (layout, `[project]` metadata, and re-exports tell different
contract stories); `python.SD-B-4` import-time workflow/I/O/logging side
effects; `python.SD-C-1` globals, singleton caches, env vars, or class state
couple runs; `python.SD-C-2` policy/domain modules import
adapters/frameworks, or an import cycle couples packages; `python.SD-C-3`
consumers deep-import internals, bypassing the package's public surface;
`python.SD-S-1` ORM/serializer/DTO and domain model collapse hides ownership;
`python.SD-S-2` machine stdout mixes diagnostics; `python.SD-S-3` exit codes
collapse distinct failures; `python.SD-E-1` version/dependency/tool pin
contract is undeclared.

Only these key codes are citable; the `Smell codes:` families above describe
scope only. Emit core `SD-*` for anything not covered by a key code.

Do not flag `src/` vs flat layout, namespace packages, `__init__.py`
re-exports, relative imports, or missing type annotations by themselves. Flag
the boundary, coupling, semantic, evolution, or tradeoff risk and name the
smaller shape.
