# Python Tooling Software Design Extension

Load for repo-internal Python tooling: `.py` files under `scripts/`, `tools/`,
`bin/`, `dev/`, `tasks/`, `hack/`, or `ci/`; Python shebangs; `[project.scripts]`
/ `console_scripts`; PEP 723 inline scripts; or Python tools invoked from task
runners or CI. Skip Python web/ASGI apps (`django`, `flask`, `fastapi`,
`starlette`, `aiohttp`, `litestar`, `sanic`, `bottle`, `pyramid`, `tornado`,
`quart`) and delegate app/API concerns.

This extension covers tooling design, not security posture or test quality.
Delegate command injection, secrets, dependency supply chain, lockfiles, and
permissions to `devsecops-audit`; delegate test quality to
`test-quality-audit`.

## Sources

Use Python docs, Python Packaging User Guide, PEP 621, PEP 723, and uv docs for
platform facts. Cite the core software-design reference for design judgments.

## Assimilation Signals

Inspect only what affects design shape:

- entrypoint shape: shebang, `if __name__ == "__main__"`, console script, PEP
  723, documented invocation;
- packaging and reproducibility: `pyproject.toml`, locks, `requires-python`,
  `.python-version`, inline dependencies, CI tool pins;
- import and state boundaries: package layout, `__init__.py`, `__main__.py`,
  re-exports, `sys.path`, globals, caches;
- process and I/O contracts: CLI parser, environment reads, stdout/stderr,
  exit codes, subprocess argv/cwd/env/timeout, `PATH` resolution;
- validation surface: `ruff`, `mypy`/`pyright`, `python -m py_compile`, smoke
  command, or project tests.

## Design Defaults

- Keep entrypoints thin; parsing, environment checks, and `sys.exit` stay at
  the edge.
- Imports must not run workflow, mutate path state, configure logging, or do
  I/O.
- Pass workflow state through arguments and return values, not module globals
  or `os.environ` backchannels.
- Keep machine-readable stdout clean; diagnostics go to stderr or logging.
- Treat exit codes, working directory, external tools, and path types as public
  contracts when other tooling depends on them.
- Prefer the standard library unless a dependency clearly removes more
  maintenance cost than it adds.
- Graduate complex durable state, retries, or rich transformation into a typed
  library or service instead of stretching script tooling.

## Validation Requirement

For Build mode on Python tooling targets, the `Validation step` MUST include a
`devsecops-audit` Quick review when that skill is available. If unavailable,
state that in `Delegations` or `Limits` and use the cheapest available fallback:
`ruff check`, `mypy --strict` or `pyright`, `python -m py_compile`, or a project
smoke command.

## Smells

| Code | Signal | Default |
|---|---|---|
| `python.SD-B-1` | Entry-point shapes disagree or expose different semantics. | warn; block when adding a public entrypoint |
| `python.SD-B-2` | CLI parsing, top-level execution, and reusable policy are tangled. | warn |
| `python.SD-B-3` | Working-directory contract is hidden or changed deep in helpers. | warn |
| `python.SD-B-4` | Import-time workflow or `__init__.py` side effects. | warn; block when shared |
| `python.SD-B-5` | `sys.path` / `PYTHONPATH` stitching hides package boundaries. | warn |
| `python.SD-C-1` | Module globals, singleton caches, or class state couple runs. | warn; block when cleanup depends on it |
| `python.SD-C-2` | `os.environ` carries workflow state between modules. | warn |
| `python.SD-C-3` | Caller `PATH` or unqualified project tools decide behavior. | warn |
| `python.SD-C-4` | Modules configure root logging or handlers at import time. | warn |
| `python.SD-S-1` | Public boundary contracts lack useful types or structured records. | warn |
| `python.SD-S-2` | Machine-readable stdout mixes with human progress or prompts. | warn |
| `python.SD-S-3` | Exit-code meanings are undocumented or collapse distinct failures. | warn |
| `python.SD-S-4` | Subprocess command/data boundary is blurred by strings or `shell=True`. | warn |
| `python.SD-S-5` | `str`, `Path`, and raw path concatenation drift across boundaries. | warn |
| `python.SD-W-1` | CLI framework wraps a small fixed workflow without current variation. | info; warn when mandatory |
| `python.SD-W-2` | Python dispatcher duplicates task-runner or CI lifecycle behavior. | info |
| `python.SD-E-1` | Python version, dependency, or tool-pin contract is undeclared. | warn |
| `python.SD-E-2` | Async surface wraps visibly sequential sync tooling. | warn |
| `python.SD-E-3` | Third-party dependency replaces a trivial standard-library shape. | info; warn when it is the only external dependency |
| `python.SD-Q-1` | Python is acting as shell glue without a clearer typed boundary. | warn |
| `python.SD-Q-2` | Tooling owns durable state or orchestration that belongs elsewhere. | warn |

## Review Notes

Do not flag missing type hints, subprocess use, PEP 723, or a CLI framework by
itself. Flag the boundary, coupling, semantic, evolution, or tradeoff risk and
name the smaller shape that would reduce it.
