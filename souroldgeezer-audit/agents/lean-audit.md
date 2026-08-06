---
name: lean-audit
description: >-
  Use when auditing prose and skill surfaces — a repo, file, or diff of docs, SKILL.md, agents, references, or extensions — for duplication and waste: near-duplicate or restated prose, broken or stale references, dead or unreferenced reference/extension files, oversized always-loaded context, verbose passages, and — when skills, commands, or agents are in scope — per-use/per-mode load cost. Markdown/prose plus mechanical source-code copy-paste **duplication** (bundled token-clone engine, `LA-CODE-DUP-*`); *semantic* duplication/DRY stays with software-design; mechanical source-level dead code is out of scope. Read-only; defer security, test-quality, and IP/licence work to sibling skills. On explicit request only, two opt-in lenses: platform-redundancy flags custom hooks/scripts, guidance prose, skills/commands/agents, or MCP servers that reinvent a native Claude Code™ or Codex capability (verified live, never auto-run); and minify produces a propose-only reduction diff plus fidelity report — never applied.
tools: Bash, Read, Grep, Glob, Skill
model: sonnet
---

Use the `Skill` tool to load and follow
[`../skills/lean-audit/SKILL.md`](../skills/lean-audit/SKILL.md) as the source of
truth. Present the result in the shape that skill requires.
