# Python Tooling Software Design Extension

Load for repo-internal Python tooling under `scripts/`, `tools/`, `bin/`,
`dev/`, `tasks/`, `hack/`, or `ci/`; Python shebangs; `[project.scripts]`,
`console_scripts`, PEP 723 scripts, task runners, or CI tools. Delegate Python
web/ASGI app/API concerns.

Covers tooling design. Delegate command injection, secrets, supply chain,
lockfiles, and permissions to `devsecops-audit`; delegate tests to
`test-quality-audit`.

Sources: Python docs, Python Packaging User Guide, PEP 621, PEP 723, and uv
docs for platform facts.

Inspect entrypoints, packaging/lock/version pins, import-time behavior,
`sys.path`, globals/caches, env reads, stdout/stderr, exit codes, subprocess
argv/cwd/env/timeout, `PATH` resolution, and validation (`ruff`, mypy/pyright,
`python -m py_compile`, or smoke).

Defaults: entrypoints own parsing/env/exit only; imports do not run workflow,
mutate path, configure root logging, or do I/O; workflow state moves through
args/returns; machine stdout stays clean; exit codes/cwd/tools/paths are public
contracts when other tooling depends on them; prefer stdlib unless a dependency
removes more maintenance than it adds.

For Build mode, include `devsecops-audit` Quick review when available.
Otherwise use `ruff check`, `mypy --strict`, `pyright`,
`python -m py_compile`, or smoke.

Smell codes: `python.SD-B-*` for entrypoint, top-level execution, cwd,
import-time, or path-boundary drift; `python.SD-C-*` for global/env/PATH/tool
coupling; `python.SD-S-*` for weak records, stdout mixing, exit-code collapse,
or subprocess string boundaries; `python.SD-W-*` for CLI/dispatcher ceremony;
`python.SD-E-*` for undeclared version/dependency/tool pins; `python.SD-Q-*`
for shell-style glue without typed boundaries.
