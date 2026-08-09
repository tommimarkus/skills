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
- Source: `../../../docs/audit-reference/audit-craft.md`,
  `../../../docs/audit-reference/materiality.md`, and
  `../../../docs/audit-reference/sampling-projection.md`.
  Handling: local bundled references owned by this repo; eval cases exercise
  audit craft, materiality, and sampling projection output contracts and do not
  reproduce rubric prose.
- Source: `references/golden-corpus/` (devsecops-audit-cases.jsonl, index.md).
  Handling: repo-authored evaluation fixture; KEV/CVE identifiers used as corpus
  entry labels are external taxonomy references, not copied prose; all scenario
  descriptions, expected findings, and grading notes are original synthetic
  constructs owned by this repo.
- Source: Python documentation for security considerations, pickle, subprocess,
  tarfile, secrets, and tempfile; Requests SSL verification; SQLAlchemy bound
  parameters; OWASP SSRF Prevention Cheat Sheet.
  Handling: primary/official anchors for the Python `pys.*` rule pack's risk
  direction. The pack, catalog, and eval use original paraphrases and synthetic
  scenarios only; they do not reproduce external examples or prose.
- Source: Node.js child process, crypto, and TLS documentation; MDN dynamic
  import and HTML sink documentation; Vite server options; OWASP SSRF Prevention
  Cheat Sheet.
  Handling: primary anchors for the JavaScript/TypeScript `jsts.*` pack's risk
  direction. The routing card, rule pack, catalog, and evals use original
  synthetic scenarios and paraphrases only; no upstream examples or prose are
  copied.
- Source: `references/procedures/threat-model-planning.md`.
  Handling: repo-authored threat-model planning procedure that drives the Deep
  mode Risk plan output; crown-jewels, trust-boundary, and attacker-goal
  taxonomy is original to this repo; no external procedure prose copied.
