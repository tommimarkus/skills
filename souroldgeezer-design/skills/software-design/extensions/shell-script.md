# Shell Script Software Design Extension

Load for `.sh`, `.bash`, `.zsh`, executable shell shebangs, sourced function
libraries, completions, bootstrap code, or scripts claiming Linux, macOS, or
WSL support.

Covers script/module design. Delegate injection/secrets to `devsecops-audit`,
provisioning to `infra-design`, endpoint contracts to `api-design`, and tests
to `test-quality-audit`.

Use GNU Bash, Z Shell, POSIX shell, Apple Terminal, and Microsoft WSL docs only
for platform facts. Inspect interpreter contract, sourcing graph, options/traps
and globals, cwd/stdout/stderr/exit contracts, platform probes, dependency
checks, temp resources, background jobs, and validation (`bash -n`, `zsh -n`,
ShellCheck, Bats/ZUnit, or smoke).

Defaults: one interpreter boundary per entrypoint; entrypoints stay thin;
sourced files define functions/constants and restore caller state; options,
traps, cleanup, and dependency checks have one owner; portability differences
hide behind probes/adapters; parsed stdout stays machine-readable; rich durable
state or multi-service orchestration leaves shell.

For Build mode, include `devsecops-audit` Quick review when available.
Otherwise use `bash -n`, `zsh -n`, ShellCheck, or a smoke command.

Smell codes: `shell.SD-B-*` for shell/cwd/import boundary drift;
`shell.SD-C-*` for global, trap, `PATH`, platform, or ambient coupling;
`shell.SD-S-*` for stringly data, Bash/zsh semantic drift, exit-code masking,
or stdout/diagnostic mixing; `shell.SD-W-*` for dispatcher ceremony;
`shell.SD-E-*` for portability, trap, pipeline, or cleanup fragility;
`shell.SD-Q-*` for misplaced structured state or unsupported platform claims.

Do not flag Bash/zsh-specific syntax merely for being non-POSIX. Flag it when
the interpreter boundary or promised platform support makes it a design risk.
