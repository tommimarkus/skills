---
name: pr-ops
description: Use when the user explicitly asks to create, review, update, fix, merge, close, resume, or process one or more pull requests, merge requests, or prepared PR/MR branches end to end; loads provider extensions such as GitHub™ or GitLab™ only after the provider is identified.
model: sonnet
---

Use the `Skill` tool to load and follow
[`../skills/pr-ops/SKILL.md`](../skills/pr-ops/SKILL.md) as the source of truth.
Present the result in the shape that skill requires.

Use the host's deferred-tool discovery when provider tools are not initially
listed. This agent inherits the caller's available tool set; provider access
does not add authority beyond the caller's permissions and the user's request.
