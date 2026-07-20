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
and uv docs https://docs.astral.sh/uv/.

Inspect package layout (`src/` or flat, `__init__.py` re-exports, `__all__`,
PEP 420 namespace packages), import graph and dependency direction,
distribution surface (`[project]` metadata, extras, entry points, wheel
contents), ORM/schema/DTO/domain splits, entrypoints, packaging/lock/version
pins, import-time behavior, `sys.path`, globals/caches, env reads,
stdout/stderr, exit codes, subprocess argv/cwd/env/timeout, `PATH`
resolution, and validation (`ruff`, mypy/pyright, `python -m py_compile`,
import smoke, or a distribution build).

Defaults: package and module boundaries follow ownership and policy; the
distribution/import surface (`[project]` metadata, entry points, extras, and
the names a package re-exports) is a public contract; consumers import the
public surface, not internal module paths; policy/domain modules do not
import adapters or frameworks; entrypoints own parsing/env/exit only; imports
do not run workflow, mutate `sys.path`, configure root logging, or do I/O;
workflow state moves through args/returns; machine stdout stays clean; exit
codes/cwd/tools/paths are public contracts when other tooling depends on
them; prefer stdlib unless a dependency removes more maintenance than it
adds.

For Build mode, include `devsecops-audit` Quick review when available.
Otherwise use `ruff check`, `mypy --strict`, `pyright`,
`python -m py_compile`, import smoke, or a distribution build.

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
