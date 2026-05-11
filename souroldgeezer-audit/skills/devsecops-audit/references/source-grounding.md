# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local DevSecOps audit workflow, bundled rubric, extensions, and procedure
contracts. They do not copy external prompts, workflow files, IaC examples,
tables, diagrams, screenshots, or documentation.

- Source: `../../../docs/security-reference/devsecops.md`.
  Handling: local bundled rubric owned by this repo; eval prompts are original
  synthetic scenarios for quick/deep mode selection, presence-vs-efficacy
  evidence, and honest static limits.
- Source: `extensions/*.md` and `references/procedures/*.md`.
  Handling: local extension and procedure contracts; eval cases exercise
  extension loading, cost stance, MCP availability, and output disclosure
  without reproducing external configuration examples.
- Source: installed Codex Security plugin skill metadata and
  `codex-security:security-scan` workflow name.
  Handling: local runtime capability reference only; the eval case is original
  synthetic prose and does not copy the plugin workflow body.
- Source:
  https://codeql.github.com/codeql-query-help/csharp/cs-log-forging/.
  Handling: external source anchor for the C# log-forging concern, CWE-117
  mapping, and remediation direction. The bundled `dns.HC-15` wording and
  behavior eval are original repo-authored paraphrase; no CodeQL examples,
  query code, or prose are copied.
- Source: https://github.com/tommimarkus/skills/issues/46.
  Handling: local issue records the repo-specific coverage gap and acceptance
  direction. The behavior eval is synthetic and does not copy issue text.
