# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local DevSecOps audit workflow, bundled rubric, extensions, and procedure
contracts. They do not copy external prompts, workflow files, IaC examples,
tables, diagrams, screenshots, or documentation.

- Source: `../../../docs/security-reference/devsecops.md`.
  Handling: local bundled rubric owned by this repo; eval prompts are original
  synthetic scenarios for quick/deep mode selection, presence-vs-efficacy
  evidence, Quick-gate status, and honest static limits.
- Source: `extensions/*.md` and `references/procedures/*.md`.
  Handling: local extension and procedure contracts; eval cases exercise
  extension loading, cost stance, MCP availability, and output disclosure
  without reproducing external configuration examples.
- Source: `references/procedures/evidence-per-release.md`,
  `references/procedures/stage-coverage-matrix.md`, and
  `references/procedures/cost-stance-detection.md`.
  Handling: the release-evidence and presence-versus-efficacy scenarios are
  original synthetic cases covering unavailable live evidence, an unexecuted
  hook, 95-percent pinning density, and Codex-only target-repository cost
  guidance. They test evidence limits and runtime scope, not copied examples.
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
- Sources:
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#how-permissions-are-calculated-for-a-workflow-job,
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstrategyfail-fast,
  and https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#always.
  Handling: primary references for effective `GITHUB_TOKEN` scope, matrix
  cancellation, and status-condition behavior. The rubric wording and synthetic
  scan-failure cases are original; settings and required-check results remain
  evidence an auditor must inspect.
- Sources: https://slsa.dev/spec/v1.0/levels and
  https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier.
  Handling: primary anchors for SLSA v1.0 level requirements and Cosmos DB
  free-tier capacity/billing claims. The rubric paraphrases these properties;
  synthetic cases distinguish standard requirements from a separately declared
  project policy and distinguish the free discount from workload capacity.
- Source:
  https://learn.microsoft.com/dotnet/azure/sdk/authentication/best-practices#use-deterministic-credentials-in-production-environments.
  Handling: primary anchor for production credential selection. The positive
  example selects `ManagedIdentityCredential` explicitly; the rubric does not
  claim that one managed-identity option disables other credential-chain
  sources.
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
- Source: https://pyjwt.readthedocs.io/en/stable/api.html,
  https://docs.djangoproject.com/en/stable/ref/settings/,
  https://docs.djangoproject.com/en/stable/topics/auth/passwords/,
  https://docs.djangoproject.com/en/stable/ref/middleware/,
  https://flask.palletsprojects.com/en/stable/web-security/,
  https://docs.python.org/3/library/hashlib.html,
  https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/,
  https://fastapi.tiangolo.com/tutorial/security/,
  https://www.django-rest-framework.org/api-guide/permissions/,
  https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md.
  Handling: primary anchors for the Python `pys.HC-10`..`pys.HC-14` and
  `pys.POS-6`..`pys.POS-9` rules. The pack, catalog, and evals paraphrase them
  in original synthetic wording; no upstream examples or prose are copied.
- Source: Node.js child process, crypto, and TLS documentation; MDN dynamic
  import and HTML sink documentation; Vite server options; OWASP SSRF Prevention
  Cheat Sheet.
  Handling: primary anchors for the JavaScript/TypeScript `jsts.*` pack's risk
  direction. The routing card, rule pack, catalog, and evals use original
  synthetic scenarios and paraphrases only; no upstream examples or prose are
  copied.
- Source: https://learn.microsoft.com/en-us/dotnet/api/microsoft.identitymodel.tokens.tokenvalidationparameters,
  https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.http.cookieoptions,
  https://learn.microsoft.com/en-us/aspnet/core/security/samesite,
  https://learn.microsoft.com/en-us/dotnet/standard/security/vulnerabilities-cbc-mode,
  https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/consumer-apis/password-hashing,
  https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclienthandler.dangerousacceptanyservercertificatevalidator,
  https://learn.microsoft.com/en-us/sql/connect/ado-net/connection-string-syntax,
  https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md.
  Handling: primary anchors for the .NET `dns.HC-16`..`dns.HC-20` and
  `dns.POS-6`..`dns.POS-9` rules. The pack, catalog, and evals paraphrase them
  in original synthetic wording; no upstream examples or prose are copied.
- Source: https://github.com/auth0/node-jsonwebtoken,
  https://github.com/panva/jose/blob/main/docs/jwt/verify/functions/jwtVerify.md,
  https://github.com/expressjs/session,
  https://expressjs.com/en/api.html,
  https://nextjs.org/docs/app/guides/data-security,
  https://nextjs.org/docs/app/guides/authentication,
  https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md.
  Handling: primary anchors for the JavaScript/TypeScript `jsts.HC-12`..`jsts.HC-16`
  and `jsts.POS-12`..`jsts.POS-15` rules (Node crypto is already anchored). The
  pack, catalog, and evals paraphrase them in original synthetic wording; no
  upstream examples or prose are copied.
- Source: https://github.com/OWASP/ASVS/releases/tag/v5.0.0_release
  (asset `OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json`,
  SHA-256 `8201b20eec2908c3380ac600c91c8ba746346fbb808859366abb232027532311`)
  and https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md.
  Handling: OWASP ASVS 5.0.0 is published by the OWASP Foundation under CC BY-SA
  4.0 and is attributed here. `../../../docs/security-reference/devsecops-asvs-crosswalk.md`
  takes only requirement IDs, levels, and chapter names from the release asset
  and Appendix C. Its classifications and the ASVS trigger and behavior evals are
  original repo-authored work; no requirement text, section text, or appendix
  tables are copied.
- Source: `references/procedures/threat-model-planning.md`.
  Handling: repo-authored threat-model planning procedure that drives the Deep
  mode Risk plan output; crown-jewels, trust-boundary, and attacker-goal
  taxonomy is original to this repo; no external procedure prose copied.

- Report presentation now defaults to concise findings while explicit detailed
  consumers retain rubric fields and exact verdicts. Original cases protect
  material security consequences and unknown enforcement evidence; no vendor
  requirements or external incident examples were added.
