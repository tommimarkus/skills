# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local pr-ops workflow and provider-extension contract. They do not copy pull
request text, review comments, check logs, tracker payloads, or external
provider documentation.

- Source: `../SKILL.md`.
  Handling: local public-skill workflow; eval prompts are original synthetic
  scenarios for trigger precision, full-cycle monitoring, review-only mode,
  feedback remediation, and merge safety.
- Source: `extensions/github.md`, `extensions/gitlab.md`, and
  `extensions/README.md`.
  Handling: local provider extension mechanics; eval cases mention PR state and
  checks without copying live provider content.
- Source: `references/core-workflow.md` and the provider references' Tooling
  Order sections.
  Handling: local authority and per-operation route rules; synthetic evals
  cover diagnosed in-scope repair, missing MCP operations, and auth gates.
- Source: [GitHub closing-keyword behavior](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
  Handling: cited as a provider behavior anchor; workflow and evaluation
  wording are original and require explicit closure reconciliation.
- Source: [Claude Code subagent tool availability](https://code.claude.com/docs/en/sub-agents#available-tools).
  Handling: public agent wrappers omit a fixed tool allowlist to inherit the
  caller's available tools; this inherits tool access without granting new
  user or provider authority.
- Source: GitLab Docs at <https://docs.gitlab.com/api/merge_requests/>,
  <https://docs.gitlab.com/api/notes/>,
  <https://docs.gitlab.com/api/discussions/>,
  <https://docs.gitlab.com/api/pipelines/>,
  <https://docs.gitlab.com/api/jobs/>,
  <https://docs.gitlab.com/api/merge_request_approvals/>,
  <https://docs.gitlab.com/cli/mr/create/>,
  <https://docs.gitlab.com/cli/mr/list/>,
  <https://docs.gitlab.com/cli/mr/view/>,
  <https://docs.gitlab.com/cli/mr/note/create/>,
  <https://docs.gitlab.com/cli/mr/merge/>,
  <https://docs.gitlab.com/cli/mr/rebase/>, and
  <https://docs.gitlab.com/cli/ci/get/>.
  Handling: official source anchors are linked; GitLab mechanics are
  paraphrased in repo-authored workflow language.
