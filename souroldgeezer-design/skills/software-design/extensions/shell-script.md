# Shell Script Software Design Extension

Load for shell scripts and modules: `.sh`, `.bash`, `.zsh`, executable text with
`bash`, `zsh`, or `sh` shebangs, sourced function libraries, shell completions,
bootstrap code, or scripts that advertise Linux, macOS, or WSL compatibility.

This extension covers script/module design, not command-injection hardening,
secrets, OS provisioning, or test quality. Delegate those to `devsecops-audit`,
`infra-design`, `api-design`, or `test-quality-audit` as appropriate.

## Sources

Use GNU Bash, Z Shell, POSIX Shell Command Language, Apple Terminal, and
Microsoft Learn WSL docs for platform facts. Cite the core software-design
reference for design judgments.

## Assimilation Signals

Inspect only what affects design shape:

- interpreter contract: shebang, suffix, docs, executable bit, Bash/zsh/sh
  syntax;
- sourcing graph and global state: `source`, `.`, options, traps, `IFS`,
  positional parameters, working directory;
- portability boundary: `$OSTYPE`, `uname`, `sw_vers`, `/proc/version`,
  `/mnt/c`, `wsl.exe`, GNU/BSD utility flags, capability probes;
- data/process contracts: quoting, arrays, command output parsing, stdout/stderr,
  exit codes, pipelines, background jobs, temporary resources;
- dependency checks and validation: `command -v`, `bash -n`, `zsh -n`,
  ShellCheck, Bats/ZUnit, CI matrix, or project smoke command.

## Design Defaults

- Declare one interpreter boundary per entrypoint. Cross-shell scripts must stay
  in a shared subset or split shell-specific adapters.
- Keep entrypoints thin; reusable workflow belongs in functions or an
  implementation command.
- Sourced files define functions/constants and restore any caller state they
  change.
- Centralize options, traps, cleanup, error rendering, and dependency checks at
  the owning edge.
- Hide Linux/macOS/WSL differences behind capability probes or helper adapters.
- Keep stdout machine-readable when parsed; diagnostics go to stderr.
- Treat exit codes, temporary resources, background processes, and working
  directory as public contracts.
- Move rich data structures, durable state, complex retries, or multi-service
  orchestration out of shell.

## Validation Requirement

For Build mode on shell targets, the `Validation step` MUST include a
`devsecops-audit` Quick review when available. If unavailable, state that in
`Delegations` or `Limits` and use the cheapest available fallback: `bash -n`,
`zsh -n`, ShellCheck, or a project smoke command.

## Smells

| Code | Signal | Default |
|---|---|---|
| `shell.SD-B-1` | Shebang, suffix, docs, and syntax imply different shells. | warn; block when new cross-platform entrypoint |
| `shell.SD-B-2` | CLI parsing, import-time execution, reusable functions, and policy are tangled. | warn |
| `shell.SD-B-3` | Non-interactive script depends on startup files, aliases, or caller options. | warn |
| `shell.SD-B-4` | Working-directory contract is hidden or changed in shared functions. | warn |
| `shell.SD-B-5` | Sourced file performs workflow, exits, starts processes, or mutates caller state. | warn; block when shared |
| `shell.SD-C-1` | Sourced file mutates globals/options/traps/`IFS` without restore contract. | warn; block when cleanup depends on it |
| `shell.SD-C-2` | Platform probes are scattered through workflow policy. | warn |
| `shell.SD-C-3` | Caller `PATH`, aliases, or unqualified project tools decide behavior. | warn |
| `shell.SD-C-4` | Modules communicate through exported variables or ambient globals. | warn |
| `shell.SD-S-1` | Paths/lists/records move through ambiguous strings. | warn |
| `shell.SD-S-2` | Bash and zsh semantics are treated as equivalent without a boundary. | warn |
| `shell.SD-S-3` | Exit-code meanings drift or are masked by local/pipeline/substitution behavior. | warn |
| `shell.SD-S-4` | Machine-readable stdout mixes with progress, prompts, or diagnostics. | warn |
| `shell.SD-S-5` | Generated shell strings are re-parsed where arrays/functions would be explicit. | warn |
| `shell.SD-W-1` | Framework/dispatcher/plugin shell ceremony wraps a small fixed workflow. | info; warn when mandatory |
| `shell.SD-W-2` | Custom dispatcher duplicates make/just/npm/CI lifecycle behavior. | info |
| `shell.SD-E-1` | Portability differences live in policy instead of adapters. | warn |
| `shell.SD-E-2` | Trap/options crosscut sourced modules or callers without a contract. | warn |
| `shell.SD-E-3` | Pipelines, substitutions, or subshells mask partial failures. | warn |
| `shell.SD-E-4` | Temporary files, fds, locks, or background processes lack one cleanup owner. | warn |
| `shell.SD-Q-1` | Shell owns structured state/retries/transformation better placed elsewhere. | warn |
| `shell.SD-Q-2` | Claimed Bash/zsh/Linux/macOS/WSL support lacks matching validation. | warn |

## Review Notes

Do not flag Bash-specific or zsh-specific syntax merely for being non-POSIX.
Flag it when the interpreter boundary or promised platform support makes it a
design risk. Syntax checks and linters validate evidence; they are not design
findings unless they expose boundary, dependency, semantic, evolution, or
tradeoff risk.
