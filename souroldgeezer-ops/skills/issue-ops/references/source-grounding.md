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
- Source: `souroldgeezer-ops/docs/provider-reference/github.md § Tooling Order`,
  `souroldgeezer-ops/docs/provider-reference/provider-lifecycle-core.md`, and
  the issue core.
  Handling: local operation-capability and closure-order rules; added behavior
  cases are original synthetic scenarios for partial provider capability,
  authentication gates, and automatic-closure reconciliation.
- Source: [GitHub closing-keyword behavior](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
  Handling: cited as a provider behavior anchor; issue guidance uses non-closing
  references until verification and the final marker are ready.
- Source: GitLab Docs at <https://docs.gitlab.com/api/rest/authentication/>,
  <https://docs.gitlab.com/api/issues/>,
  <https://docs.gitlab.com/api/notes/>,
  <https://docs.gitlab.com/api/issue_links/>,
  <https://docs.gitlab.com/api/merge_requests/>,
  <https://docs.gitlab.com/cli/issue/>, and
  <https://docs.gitlab.com/user/project/issues/managing_issues/> and
  <https://docs.gitlab.com/user/project/issues/crosslinking_issues/>.
  Handling: official source anchors are linked; GitLab mechanics are
  paraphrased in repo-authored wording. Closing patterns in commit messages
  and merge-request descriptions can close local and cross-project issues on
  default-branch integration; `Ref` references cross-link without invoking
  those closing patterns. Direct-main guidance therefore uses non-closing
  references until post-integration verification and the final lifecycle
  marker are complete, then requires a live-state reread before explicit close.
