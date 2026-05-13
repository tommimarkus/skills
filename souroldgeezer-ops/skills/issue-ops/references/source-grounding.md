# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local issue-ops workflow and provider-extension contract. They do not copy
issue text, tracker payloads, review comments, branch names from real work, or
external provider documentation.

- Source: `../SKILL.md`.
  Handling: local public-skill workflow; eval prompts are original synthetic
  scenarios for trigger precision, queue limits, provider selection, and
  issue-to-PR handoff.
- Source: `extensions/github.md` and `extensions/README.md`.
  Handling: local provider extension mechanics; eval cases mention provider
  state and lifecycle markers without copying live tracker content.
- Source: `extensions/gitlab.md`.
  Handling: local GitLab provider extension mechanics; eval cases mention
  provider state, lifecycle notes, and merge-request handoff limits without
  copying live tracker content.
- Source: GitLab Docs at <https://docs.gitlab.com/api/rest/authentication/>,
  <https://docs.gitlab.com/api/issues/>,
  <https://docs.gitlab.com/api/notes/>,
  <https://docs.gitlab.com/api/issue_links/>,
  <https://docs.gitlab.com/api/merge_requests/>,
  <https://docs.gitlab.com/cli/issue/>, and
  <https://docs.gitlab.com/user/project/issues/managing_issues/>.
  Handling: official source anchors are linked; GitLab mechanics are
  paraphrased in repo-authored wording.
