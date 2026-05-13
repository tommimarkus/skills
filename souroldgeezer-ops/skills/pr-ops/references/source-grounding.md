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
