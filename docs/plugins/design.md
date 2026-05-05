# `souroldgeezer-design`

`souroldgeezer-design` ships the software, UI, and API design plugin. The
architecture model workflow now lives in a dedicated sibling plugin.

## Skills

| Skill | What it covers | Notes |
|---|---|---|
| [software-design](../../souroldgeezer-design/skills/software-design/SKILL.md) | Sustainable software design for code, module, script, and library boundaries | Uses stack extensions for .NET, shell scripts, and Python |
| [responsive-design](../../souroldgeezer-design/skills/responsive-design/SKILL.md) | Responsive web UI build, review, and lookup | Uses stack extensions for Blazor WebAssembly and Blazor Web App `.Client` projects |
| [api-design](../../souroldgeezer-design/skills/api-design/SKILL.md) | HTTP API build, extract, review, and lookup | Uses runtime and data-store extensions when the target matches |

## Packaging notes

- Claude Code and Codex share the same marketplace entry for this plugin.
- The plugin keeps the software, UI, and API surfaces together because they
  share the same design boundary and reference style.
- Architecture moved out to a dedicated plugin to keep the public surface
  aligned with the runtime split.
