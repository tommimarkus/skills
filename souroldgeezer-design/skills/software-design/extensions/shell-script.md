# Shell Script Software Design Extension

Load this extension for shell scripts and shell-script modules: `.sh`, `.bash`,
`.zsh`, executable text files with `bash`, `zsh`, or `sh` shebangs, sourced
function libraries, shell completion/bootstrap code, or scripts that advertise
Linux, macOS, or WSL compatibility.

This extension covers script and module design, not command-injection hardening,
secret handling, OS provisioning, or test-quality minutiae. Delegate security
posture to `devsecops-audit`, test quality to `test-quality-audit`, and
deployment topology / IaC ownership to `architecture-design` or
`api-design` when the script is only an adapter around those
concerns.

## Platform Sources

Use primary runtime and platform documentation for platform facts:

- GNU Bash Reference Manual: https://www.gnu.org/software/bash/manual/bash.html
- Z Shell Manual: https://zsh.sourceforge.io/Doc/Release/
- POSIX Shell Command Language:
  https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html
- Apple Terminal User Guide for macOS shell defaults:
  https://support.apple.com/guide/terminal/change-the-default-shell-trml113/mac
- Microsoft Learn WSL file-system and command-interoperability guidance:
  https://learn.microsoft.com/en-us/windows/wsl/filesystems

Any claim about whether a shell construct is good design must cite the core
software-design reference and, where relevant, the smell catalog. Platform
sources explain runtime behavior; they do not decide boundary quality.

## Project Assimilation Signals

Inspect:

1. Shebangs, documented invocation commands, file suffixes, and executable bits.
2. Bash-specific and zsh-specific tokens: `BASH_SOURCE`, `ZSH_VERSION`,
   `setopt`, `emulate`, `autoload`, `zmodload`, arrays, associative arrays, and
   process substitution.
3. Sourcing graph: `source`, `.`, shared `lib/*.sh`, completion files, and
   bootstrap scripts.
4. Option and failure policy: `set -e`, `set -u`, `set -o pipefail`, `trap`,
   `ERR`, zsh `setopt`, and whether these leak through sourced files.
5. Platform probes and adapters: `uname`, `$OSTYPE`, `sw_vers`, `/proc/version`,
   `/mnt/c`, `wsl.exe`, `powershell.exe`, `command -v`, and GNU-vs-BSD utility
   flag handling.
6. Path and data contracts: quoting, arrays vs strings, newline-delimited data,
   globbing, `IFS`, temporary directories, and cleanup ownership.
7. Working-directory, stream, exit-code, pipeline, and background-process
   contracts.
8. External command dependencies, `PATH` assumptions, and where dependencies
   are checked.
9. Existing validation commands: `bash -n`, `zsh -n`, ShellCheck, Bats, ZUnit,
   CI matrix jobs, or project-specific smoke scripts.

## Shell Script Design Defaults

- Declare one interpreter boundary per entrypoint: Bash, zsh, or an explicit
  cross-shell subset. Do not let a `.sh` suffix or caller shell choose
  semantics accidentally.
- For a file intended to run under both Bash and zsh, keep the executable body
  to a shared subset and validate with both interpreters. When language-specific
  features are useful, split them behind small shell-specific adapters.
- Keep entrypoints thin. Put reusable decisions in sourced functions or a
  separate implementation command; keep argument parsing, environment checks,
  and process exit behavior at the edge.
- Treat sourced files as modules with a narrow contract. They should define
  functions and constants, avoid executing workflow on import, and avoid
  changing caller options unless they restore them.
- Centralize shell options, traps, cleanup, and error rendering near the
  entrypoint. Global shell state is part of the module interface even when it is
  invisible in function signatures.
- Isolate Linux, macOS, and WSL differences behind capability probes and helper
  functions. Workflow policy should call a normalized operation, not scatter
  platform branches through every step.
- Prefer capability detection over OS-name branching when possible. Use OS
  probes only when the behavior difference is genuinely platform-specific.
- Make external command dependencies explicit at startup or at the adapter that
  owns them. Avoid discovering missing tools halfway through a state-changing
  workflow.
- Keep stdout as a data contract when callers parse it. Send progress,
  diagnostics, and prompts to stderr or a named log channel.
- Treat exit codes as part of the public interface. Do not rely on incidental
  last-command status, masked pipeline failures, or platform-specific command
  status differences.
- Own temporary files, directories, file descriptors, and background processes
  in one boundary with cleanup that runs on success, failure, and interruption.
- Keep long-lived domain policy out of shell when the workflow has rich data
  structures, durable state, retries, or many collaborators. Shell is a good
  orchestration edge, not a universal application layer.

## Validation Requirement

For Build mode on shell-script targets, the `Validation step` MUST include a
`devsecops-audit` Quick review when that skill is available in the current
runtime. Shell design can separate design posture from command-injection,
secret, permission, and supply-chain posture, but it must still route the
security validation explicitly. If `devsecops-audit` is unavailable, state that
in `Delegations` or `Limits` and choose the next cheapest available validation
step, such as `bash -n`, `zsh -n`, ShellCheck, or a project smoke command.

## Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `shell.SD-B-1` | Ambiguous interpreter boundary | Shebang, suffix, docs, and syntax imply different shells, or Bash/zsh features appear under `sh`. | warn; block when new cross-platform entrypoint |
| `shell.SD-B-2` | Entry point owns library policy | CLI parsing, import-time execution, reusable functions, and domain decisions are tangled in one script. | warn |
| `shell.SD-B-3` | Startup-file dependency | Non-interactive script depends on aliases, functions, options, or variables from `.bashrc`, `.zshrc`, profiles, or the caller's interactive shell. | warn |
| `shell.SD-B-4` | Hidden working-directory contract | Script assumes launch directory, changes directory in shared functions, or exposes relative paths without an owner. | warn |
| `shell.SD-B-5` | Import-time workflow | Sourced file performs IO, exits, starts processes, parses arguments, or mutates caller state before an explicit function call. | warn; block when sourced by multiple entrypoints |
| `shell.SD-C-1` | Sourced-state coupling | Sourced files mutate globals, shell options, traps, `IFS`, positional parameters, or working directory without an explicit restore contract. | warn; block when cleanup/error paths depend on it |
| `shell.SD-C-2` | Platform probe scattering | Linux, macOS, WSL, GNU/BSD, or Windows-path checks are repeated through workflow policy instead of isolated behind adapters. | warn |
| `shell.SD-C-3` | PATH shadow contract | Script relies on caller `PATH` ordering, unqualified project-local tools, aliases, or functions instead of an explicit command boundary. | warn |
| `shell.SD-C-4` | Environment backchannel | Modules communicate workflow state through exported variables or ambient globals instead of arguments, outputs, or a named config contract. | warn |
| `shell.SD-S-1` | Word contract ambiguity | Paths, lists, records, or command output move through untyped strings where arrays, delimiters, or a parse boundary should be explicit. | warn |
| `shell.SD-S-2` | Cross-shell semantic drift | Arrays, globbing, option state, `[[ ]]`, process substitution, or completion/autoload behavior assumes Bash and zsh behave the same without a declared boundary. | warn |
| `shell.SD-S-3` | Exit-code protocol drift | Functions and commands use the same status for different meanings, drop status through `local`, `echo`, or command substitution, or leave callers to infer failure semantics. | warn |
| `shell.SD-S-4` | Stream contract ambiguity | Machine-readable stdout, human progress, prompts, and diagnostics share one stream that downstream callers parse by convention. | warn |
| `shell.SD-S-5` | Generated shell string contract | Workflow builds shell command strings for re-parsing where arrays, functions, or direct command invocation would make the boundary explicit. | warn |
| `shell.SD-W-1` | Shell framework ceremony | Dispatcher/plugin/config frameworks are added around a small fixed workflow with no current variation. | info; warn when mandatory |
| `shell.SD-W-2` | Reimplemented task runner | Custom shell dispatcher duplicates make, just, npm scripts, CI jobs, or package-manager lifecycle behavior without a current design force. | info |
| `shell.SD-E-1` | Portability hidden in policy | GNU-only flags, BSD utility differences, `/mnt/c` paths, `wsl.exe`, or `sw_vers` calls are embedded in business workflow instead of a portability adapter. | warn |
| `shell.SD-E-2` | Trap and option crosscut | `trap`, `ERR`, `set -e`, `pipefail`, or zsh option choices affect sourced modules or caller code without a documented boundary. | warn |
| `shell.SD-E-3` | Pipeline failure opacity | Pipelines, command substitutions, subshells, or grouped commands mask partial failures while later workflow steps proceed. | warn |
| `shell.SD-E-4` | Temporary resource leak | Temporary files, directories, file descriptors, locks, or background processes lack a single cleanup owner across success, failure, and interrupt paths. | warn |
| `shell.SD-Q-1` | Shell absorbs structured workflow | Shell owns durable state, complex retries, rich data transformation, or multi-service orchestration better placed in a typed module, IaC workflow, or service. | warn |
| `shell.SD-Q-2` | Portability promise unverified | Docs or naming claim Bash/zsh or Linux/macOS/WSL support without validation under each promised interpreter/platform boundary. | warn |

## Review Notes

- Use shebang and documented invocation evidence before inferring which shell a
  file targets.
- Do not flag Bash-specific or zsh-specific syntax merely because it is not
  POSIX. Flag it when the interpreter boundary is ambiguous or the requested
  support includes another shell.
- For Linux, macOS, and WSL support, treat GNU/BSD utility drift and Windows
  path interop as design-boundary evidence, not just lint style.
- When command construction, secrets, permissions, dependency pinning, or
  downloaded code are in scope, record a `devsecops-audit` Quick review
  delegation in addition to any design finding.
- Syntax checks (`bash -n`, `zsh -n`) and linters validate evidence. They do not
  become software-design findings unless the result exposes boundary,
  dependency, semantic, evolution, or tradeoff risk.
