# Extension Authoring

Use this only when editing or adding `software-design` extensions.

Extensions add stack evidence and namespaced `*.SD-*` smells; they never replace
the core reference. Keep each file narrow: load cues, official platform sources,
assimilation signals, design defaults, mandatory validation, smell codes, and
review notes. Add support only when pressure cases show the core plus a strong
base model misses stack-specific design signals.

Before landing a new or materially restructured extension, run the
clean-context expert probe in `../evals/expert-probe.md` and record the run
there; never re-run it against unchanged content.

Each extension declares two code surfaces: the `Smell codes:` family globs
(`<ext>.SD-B-*`) describe coverage scope only and are never citable; the
`Key codes:` line defines the extension's fixed citable set. Reviews emit only
defined key codes (or core `SD-*`). To report a new finding kind, add and
define a key code first.

Per-stack test-code lane files live at `extensions/<stack>/test-code.md`
(`csharp/test-code.md`, `java/test-code.md`, `python/test-code.md`,
`rust/test-code.md`, `shell-script/test-code.md`, `typescript/test-code.md`).
Keep each at most about 70 lines with these sections in order:
`# <Stack> Test-Code Lane` (load cue plus a `Sources:` line linking the official
runner, fixture, time, and parallel-run docs), `## Shared test support`,
`## Setup lifetime`, `## Time, randomness, and ambient environment`,
`## Isolation and parallel runs`, `## Lanes and durations`, and the closing line
"Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`."
They load only through the SKILL.md test-code route, state the principle and
main variants, never mandate a tool the project does not use or add a
dependency. Expert-probe lenses: A = expert test-code practice for the stack;
B = what a reviewer checks in a mature suite's support structure.

Current extensions: `csharp.md`, `java.md`, `rust.md`, `typescript.md`,
`shell-script.md`, and `python.md`.
