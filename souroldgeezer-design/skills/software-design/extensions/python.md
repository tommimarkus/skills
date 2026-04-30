# Python Tooling Software Design Extension

Load this extension for repo-internal Python tooling: `.py` files under
`scripts/`, `tools/`, `bin/`, `dev/`, `tasks/`, `hack/`, or `ci/`; files with
a `#!/usr/bin/env python*` shebang or equivalent `python` / `python3`
shebang; entries referenced from `[project.scripts]` or `console_scripts`;
files with a PEP 723 `# /// script` inline-metadata block; or scripts
invoked from `Makefile`, `justfile`, `tox.ini`, `noxfile.py`, or
`.github/workflows/**`. Skip when the file or project imports a web/ASGI
framework (`django`, `flask`, `fastapi`, `starlette`, `aiohttp`, `litestar`,
`sanic`, `bottle`, `pyramid`, `tornado`, `quart`).

This extension covers tooling design, not application/service runtime,
security posture, or test-quality minutiae. Delegate command-injection,
secret, dependency-supply-chain, lockfile, and permission posture to
`devsecops-audit`, test quality to `test-quality-audit`, web/HTTP runtime
concerns to `serverless-api-design`, and code-to-architecture drift to
`architecture-design` when the script is only an adapter around those
concerns.

## Platform Sources

Use primary runtime and packaging documentation for platform facts:

- Python language reference and library: https://docs.python.org/3/
- Python tutorial — modules and packages:
  https://docs.python.org/3/tutorial/modules.html
- Python Packaging User Guide: https://packaging.python.org/
- PEP 257 — Docstring Conventions: https://peps.python.org/pep-0257/
- PEP 484 — Type Hints: https://peps.python.org/pep-0484/
- PEP 621 — Project metadata in `pyproject.toml`:
  https://peps.python.org/pep-0621/
- PEP 723 — Inline script metadata: https://peps.python.org/pep-0723/
- Astral uv documentation: https://docs.astral.sh/uv/

Any claim about whether a Python construct is good design must cite the
core software-design reference and, where relevant, the smell catalog.
Platform sources explain runtime and packaging behavior; they do not
decide boundary quality.

## Project Assimilation Signals

Inspect:

1. Entry-point evidence: shebangs, `if __name__ == "__main__":` blocks,
   `[project.scripts]` / `console_scripts` entries, PEP 723 `# /// script`
   metadata, and how scripts are invoked (`Makefile`, `justfile`,
   `tox.ini`, `noxfile.py`, CI workflows).
2. Package layout: single-file script, flat module, `src/` layout, or
   implicit-namespace package; presence of `__init__.py` and
   `__main__.py`.
3. Dependency contract and reproducibility: `pyproject.toml` (PEP 621),
   `uv.lock` / `poetry.lock` / `requirements*.txt` / `Pipfile.lock`,
   lockfile freshness, pinned vs unpinned dev tools, PEP 723 inline
   dependency pins, and the runtime Python-version contract
   (`requires-python`, `.python-version`, `tool.uv.python`).
4. Sourcing graph: imports, `__all__`, re-exports, `sys.path` mutation,
   `importlib`, plugin entry points (`[project.entry-points]`).
5. Process and state contracts: `argparse` / `click` / `typer` parser
   shape, `sys.argv` reads outside the entrypoint, `sys.exit` placement,
   exit-code conventions, and exceptions vs error returns.
6. I/O contracts: stdout-vs-stderr discipline, `print` vs `logging`,
   machine-readable output (JSON / CSV) discipline, working-directory
   assumptions, and `pathlib` vs `os.path` consistency.
7. External-process boundary: `subprocess.run` / `Popen` shape,
   `shell=True` use, command construction (list vs string), and how
   `PATH` and external-tool dependencies are resolved.
8. Type-hint and runtime-validation surface: `typing` use at module
   boundaries, `dataclass` / `pydantic` / `attrs` choice, `mypy` /
   `pyright` configuration, and where validation lives.
9. Existing validation commands: `ruff check`, `mypy --strict`,
   `pyright`, `python -m py_compile`, `pytest`, pre-commit hooks, and
   CI matrix shape.

## Python Tooling Design Defaults

- Declare one entry-point boundary per script. A shebang plus
  `if __name__ == "__main__":`, a `[project.scripts]` console-script,
  or a PEP 723 single-file tool — not three of them disagreeing.
- Keep entrypoints thin. Argument parsing, environment checks, and
  `sys.exit` belong at the edge; reusable workflow belongs in
  importable functions reachable without running the script.
- Treat modules as modules. Importing a module must not perform IO,
  parse arguments, mutate `sys.path`, or run workflow. `__init__.py`
  is for surface declaration, not execution.
- Avoid module-level mutable state. Modules expose functions and
  constants; when state is unavoidable, declare its lifecycle,
  ownership, and reset contract at the entrypoint that creates it,
  not as a module-level global or `_singleton` cache.
- Confine `sys.path` and `PYTHONPATH` mutation to the entry point or a
  documented bootstrap. Reaching project files via `sys.path.insert(0,
  ...)` deep in a helper hides the package boundary.
- Centralize logger configuration at the entrypoint. Modules acquire
  loggers via `logging.getLogger(__name__)` and never call
  `logging.basicConfig` or attach handlers at import.
- Read external configuration once at startup into a typed config
  object. Pass workflow state between functions and modules through
  arguments and return values, not through `os.environ` reads or
  writes.
- Make external-command dependencies explicit. Use `subprocess.run([...])`
  with a list argv, an explicit `cwd`, an explicit `env`, and an
  explicit `timeout`. Resolve binaries with `shutil.which` at a startup
  check, not mid-workflow.
- Keep stdout as a data contract when callers parse it. Send progress,
  diagnostics, and prompts to stderr or a named log channel; never mix
  machine-readable JSON with human chrome on stdout.
- Treat exit codes as part of the public interface. Document the
  contract; do not let uncaught exceptions or incidental `sys.exit`
  placement become the de facto failure protocol.
- Use `pathlib.Path` for path arithmetic. Pick one canonical
  working-directory contract per script; own `str ↔ Path` conversion
  at named boundaries.
- Apply type hints at module and function boundaries crossed by other
  modules or by `[project.scripts]` consumers. Do narrow runtime
  validation at the I/O edge (CLI parser, JSON read, subprocess output
  parse), not deep in domain logic.
- Declare the reproducibility contract. Pin a Python version
  (`requires-python` or `.python-version` or PEP 723 `requires-python`),
  pin the dependency set with a lockfile or PEP 723 inline pins, and
  pin tool versions used in CI. One runtime manager per project.
- Reach for the standard library first. Add a third-party dependency
  only when its cost beats the maintenance footprint and the surface it
  replaces is non-trivial.
- Tooling whose domain logic grows stateful, long-running, multi-service,
  or richly transformational should graduate out of "tooling" into a
  typed library or service rather than stretch shell-style Python
  further.

## Validation Requirement

For Build mode on Python tooling targets, the `Validation step` MUST
include a `devsecops-audit` Quick review when that skill is available
in the current runtime. Python tooling can separate design posture from
command-injection, secret, dependency-supply-chain, and permission
posture, but it must still route the security validation explicitly. If
`devsecops-audit` is unavailable, state that in `Delegations` or
`Limits` and choose the next cheapest available validation step from
this fallback chain: `ruff check` → `mypy --strict` or `pyright` →
`python -m py_compile` → a project smoke command.

## Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `python.SD-B-1` | Ambiguous entry-point boundary | Shebang, `[project.scripts]` entry, PEP 723 metadata, and documented invocation imply different entry shapes; or a file is launched both as `python file.py` and as a console script with different semantics. | warn; block when introducing a new externally-invokable entrypoint (`[project.scripts]` console script, PEP 723 single-file tool, or new packaged CLI) |
| `python.SD-B-2` | Entry point owns library policy | CLI parsing, top-level execution, reusable functions, and domain decisions are tangled in one file with no `if __name__ == "__main__":` separation. | warn |
| `python.SD-B-3` | Hidden working-directory contract | Script assumes launch directory, `os.chdir` deep in helpers, or relative paths exposed without an owner. | warn |
| `python.SD-B-4` | Import-time workflow | Module performs IO, parses arguments, opens connections, or runs workflow at top level; `__init__.py` runs side effects on package import. (`sys.path` mutation is covered by `python.SD-B-5`.) | warn; block when imported by multiple entrypoints |
| `python.SD-B-5` | sys.path stitching | Code mutates `sys.path` or `PYTHONPATH` from inside a module to reach project files instead of declaring a package, using a console script, or running through a documented bootstrap. | warn |
| `python.SD-C-1` | Module-state coupling | Modules use module-level mutable globals, `_singleton` caches, or class-level state that accumulates across imports without a reset contract or explicit ownership. | warn; block when cleanup/error paths depend on it |
| `python.SD-C-2` | Environment backchannel | Modules pass workflow state between functions or modules through `os.environ` reads/writes instead of arguments, return values, or a startup-loaded typed config object. (Reading `os.environ` once at startup into a config object is normal.) | warn |
| `python.SD-C-3` | PATH / executable shadow contract | Script depends on caller `PATH` ordering, unqualified project-local tools, shell aliases, or unspecified executable locations instead of an explicit external-command boundary. | warn |
| `python.SD-C-4` | Implicit logger configuration | Modules call `logging.basicConfig`, attach handlers at import, or rely on the caller's root logger state instead of declaring a configuration boundary at the entrypoint. | warn |
| `python.SD-S-1` | Untyped boundary contract | Public functions, CLI-parser results, and inter-module returns lack type hints where `dataclass` / `TypedDict` / `pydantic` / `attrs` would make the contract explicit. | warn |
| `python.SD-S-2` | Stream contract ambiguity | Machine-readable stdout, human progress, prompts, and diagnostics share one stream that downstream callers parse by convention; `print` used for both data and chrome. | warn |
| `python.SD-S-3` | Exit-code protocol drift | Exceptions, `sys.exit` calls, and return values use the same status for different meanings; uncaught exceptions become the de facto failure protocol; callers cannot tell a bug from a documented refusal. | warn |
| `python.SD-S-4` | Subprocess command-construction ambiguity | `subprocess` calls use `shell=True` with constructed strings, pass argv as a string, or build commands by `" ".join(...)` instead of a list, blurring the data/command boundary. | warn |
| `python.SD-S-5` | Path representation drift | `os.path.join`, raw string concatenation, and `pathlib` mix in the same workflow; `str` and `Path` cross function boundaries without a named conversion. | warn |
| `python.SD-W-1` | CLI framework ceremony | `click` / `typer` / `cleo` / `argparse` subcommand registries wrap a small fixed workflow with no current variation; framework adds files without reducing cost. | info; warn when mandatory |
| `python.SD-W-2` | Reimplemented task runner | Custom Python dispatcher duplicates `make` / `just` / `nox` / `tox` / npm-script / CI lifecycle behavior without a current design force. | info |
| `python.SD-E-1` | Reproducibility contract drift | Python version is not declared (`requires-python` / `.python-version` / PEP 723); dependencies are not pinned (no lockfile or no PEP 723 inline pins); tool versions in CI drift from what the script was developed against. | warn |
| `python.SD-E-2` | Async surface for sync tooling | `asyncio.run` or coroutines wrap a sequential workflow with no concurrent I/O, raising debugging and traceback cost without a current force. | warn |
| `python.SD-E-3` | Dependency for stdlib reach | A third-party dependency replaces a small stdlib equivalent (`requests` for one-shot GET, `click` for two args, `pydantic` for a 3-field record); severity escalates when the dependency now reaches into more workflow than its original justification. | info; warn when the dep is otherwise the only third-party reach |
| `python.SD-Q-1` | Shell-style Python tooling | Python script chains `subprocess` calls, dynamic shell-out, and string-based command construction as its primary logic. | warn |
| `python.SD-Q-2` | Tooling absorbs structured workflow | Python tooling owns durable state, multi-service orchestration, complex retries, or rich data transformation better placed in a typed library or service. | warn |

## Review Notes

- Use entry-point evidence (shebang, `[project.scripts]`, PEP 723,
  documented invocation) before inferring whether a `.py` file targets
  tooling, library, or app.
- Do not flag PEP 723 inline metadata as deficient packaging; it is a
  deliberate single-file-script design choice. Flag drift between PEP
  723 metadata and `pyproject.toml` when both exist.
- Missing type hints are not a design finding by themselves. Flag the
  missing-hint smell only at function or module boundaries crossed by
  other modules or by `[project.scripts]` consumers.
- For reproducibility findings, prefer one finding per drift kind
  (Python version, runtime dependencies, dev tool pinning) over
  scattering one finding per missing pin.
- Do not flag `subprocess.run([...], shell=False)` for being subprocess.
  Flag the boundary, command-construction, PATH-resolution, or stream /
  exit-code discipline issues.
- When `subprocess`, network calls, file-system mutation outside
  `$TMPDIR`, generated code, or downloaded tools are in scope, record a
  `devsecops-audit` Quick review delegation in addition to any design
  finding.
- When flagging `python.SD-Q-1`, name the cheaper alternative shape
  (a typed module plus a bash entrypoint, or a typed library) so the
  recommendation is concrete; do not flag without a clearer better
  target.
- Apply `python.SD-E-2` conservatively. Flag the async-for-sync-tooling
  smell only when all awaited calls visibly trace to non-concurrent
  operations from direct source inspection; if the call graph is
  opaque, defer to a runtime trace.
- Lint and type-check results validate evidence. They do not become
  software-design findings unless the result exposes boundary, coupling,
  semantic, evolution, or tradeoff risk.
