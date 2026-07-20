# Extension Authoring

Use this only when editing or adding `software-design` extensions.

Extensions add stack evidence and namespaced `*.SD-*` smells; they never replace
the core reference. Keep each file narrow: load cues, official platform sources,
assimilation signals, design defaults, mandatory validation, smell codes, and
review notes. Add support only when pressure cases show the core plus a strong
base model misses stack-specific design signals.

Each extension declares two code surfaces: the `Smell codes:` family globs
(`<ext>.SD-B-*`) describe coverage scope only and are never citable; the
`Key codes:` line defines the extension's fixed citable set. Reviews emit only
defined key codes (or core `SD-*`). To report a new finding kind, add and
define a key code first.

Current extensions: `dotnet.md`, `java.md`, `rust.md`, `typescript.md`,
`shell-script.md`, and `python.md`.
