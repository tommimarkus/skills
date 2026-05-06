# Extension — GitHub Actions

**Applies to:** `.github/workflows/*.yml`, `.github/workflows/*.yaml`, reusable workflow files, composite action `action.yml`.

**Detection signals:**

- Path matches `.github/workflows/*.y?ml`.
- Any YAML file with a top-level `jobs:` key and at least one job containing `runs-on:` or `uses:`.
- `action.yml` / `action.yaml` files with a `runs:` block and `using: composite` | `using: docker` | `using: node20`.

**Applies to rubric sections:** §4 (CICD-SEC-1, -2, -4, -5, -6, -8), §5.1 items 2, 3, 5, 7, 9, §5.3 items 2, 3, 4, §6.2 (Indirect PPE).

## Smell codes

### `gha.HC-1` — Missing `permissions:` block

**Pattern:** a workflow file (top-level) or individual job without a `permissions:` key. When the workflow does not declare `permissions:`, the effective `GITHUB_TOKEN` scope falls back to the repo/org "Workflow permissions" setting — which is **permissive** (read/write across most scopes) on orgs/repos created before Feb 2023 or any org/repo that hasn't flipped the setting. Repos created after that date default to the restricted "read" variant, but the auditor cannot see this setting from the workflow YAML alone, so the smell is still valid as written.

**Detection:** a `jobs:` block where no child job declares `permissions:` and the top level has no `permissions:` either.

**Severity:** `block`

**Rubric:** devsecops.md §5.1.3; OpenSSF Scorecard Token-Permissions.

**Remediation action:**
> Add `permissions: contents: read` at the workflow top level (or `permissions: {}` for zero-scope). Override per-job with the minimum needed write scopes. Document write scopes inline with a comment explaining why. The durable org/repo-level fix is to set the "Workflow permissions" default to "Read repository contents and packages permissions" in Settings → Actions → General — see https://docs.github.com/en/actions/reference/secure-use-reference — but workflow-level `permissions:` is per-workflow hardening that survives setting drift.

### `gha.HC-2` — Floating tag in `uses:`

**Pattern:** `uses: <owner>/<repo>@<ref>` where `<ref>` is not a 40-character commit SHA. Examples: `@main`, `@v1`, `@v1.2.3`, `@latest`.

**Detection (two-pass, default ripgrep — avoids lookaround):**

1. Enumerate every `uses:` line: `rg -nE 'uses:\s*\S+@\S+' .github/workflows/`
2. For each match, extract the ref after `@` and check whether it is exactly 40 hex characters. Any ref that is not → `gha.HC-2` finding. Refs that are 40 hex → `gha.POS-3` positive.

(If the caller insists on a single-pass regex, `rg --pcre2 'uses:\s*[^#\n]+@(?!([a-f0-9]{40}))[^\s#]+'` works with PCRE2. The two-pass form is preferred because it also drives `gha.POS-3` without a second scan.)

**Severity:** `block` (third-party) / `warn` (first-party actions when manual ownership verification confirms the action is in the same GitHub org as the audited repo — see carve-out below)

**Rubric:** devsecops.md §5.1.2; CICD-SEC-3; OpenSSF Scorecard Pinned-Dependencies.

**Remediation action:**
> Pin to a commit SHA: `uses: owner/repo@<40-char-sha>  # v1.2.3`. The tag in the trailing comment is human-readable; the SHA is the security boundary.

### `gha.HC-3` — `pull_request_target` with untrusted ref checkout

**Pattern:** a workflow triggered by `pull_request_target` that runs `actions/checkout` with `ref: ${{ github.event.pull_request.head.sha }}` or similar. This is the canonical Direct-PPE vector. GitHub applies the same warning to `workflow_run` ("has access to secrets and write tokens even when the triggering workflow lacks those permissions") — both triggers need the same treatment (see also `gha.HC-7`).

**Detection (multi-line):**
```
on:\s*\n\s*pull_request_target  →  actions/checkout  →  ref:.*pull_request
```

**Severity:** `block`

**Rubric:** devsecops.md §5.1.5; CICD-SEC-4; Scorecard Dangerous-Workflow.

**Remediation action:**
> Remove `pull_request_target` or, if required for writing back to the PR, split into a second workflow using the `workflow_run` trigger — the canonical safer pattern. The `workflow_run` workflow runs in the base-repo context with secrets but must never check out PR code; it receives artifacts produced by the untrusted `pull_request` workflow. Never check out `head.sha` in a `pull_request_target` workflow that has secret access. See https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows.

### `gha.HC-4` — Shared deploy/merge identity

**Pattern:** a single workflow that both merges (via `GITHUB_TOKEN` with `contents: write`) and deploys to production (via cloud credentials). A compromise of either side grants both.

**Detection:** a single workflow file where one job has `contents: write` and a later job (same workflow) authenticates to cloud (OIDC login, Azure/AWS/GCP credentials, Service Principal secret).

**Severity:** `warn`

**Rubric:** devsecops.md §5.1.9; CICD-SEC-1 (Insufficient Flow Control); CICD-SEC-2; CICD-SEC-5.

**Remediation action:**
> Separate deploy from merge. A merge job writes to `main`; a deploy job triggers on `push: main` with its own identity. The deploy identity must have no `contents: write` and the merge identity must have no cloud deploy permission. The GitHub-endorsed control for the deploy leg is an `environments:` protection rule with required reviewers and branch restrictions — a `production` environment gates the cloud credentials behind a human approval and restricts which branches can target it. See https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments.

### `gha.HC-5` — Security scan failure silently tolerated

**Pattern:** a job step that runs a SAST / SCA / DAST / IaC scan and its failure is masked — any of the following forms:

- `continue-on-error: true` on the scan step (or the whole job).
- `if: always()` on a later step that consumes the scan output, combined with no explicit failure re-raise.
- Shell-level `|| true`, `|| exit 0`, or `set +e` wrapping the scan command.
- Severity gate above `critical` with no justifying comment.

**Detection (ripgrep):**
```
continue-on-error:\s*true
\|\|\s*true\b
\|\|\s*exit\s+0
if:\s*always\(\)
```
Then manually verify the matched step is a security scan (CodeQL, trivy, semgrep, snyk, checkov, tfsec, etc.) or a consumer of one. Also flag matrix jobs with `fail-fast: false` where any matrix leg is a security scan — one leg failing silently hides the finding.

**Severity:** `block`

**Rubric:** devsecops.md §5.1.6; §1 (decorative control definition).

**Remediation action:**
> Remove `continue-on-error: true` (and the shell bypass forms). Change severity gate to fail the build on `high` and above. If the scan is too noisy, fix the scanner config, don't hide the findings.

### `gha.HC-6` — User-controlled input interpolated into `run:`

**Pattern:** a `run:` block that uses `${{ github.event.* }}` or `${{ inputs.* }}` directly inside shell, without intermediate env-var sanitization. Indirect script injection risk.

**Detection (ripgrep):**
```
run:.*\$\{\{\s*(github\.event|inputs)\.
```

**Severity:** `block`

**Rubric:** devsecops.md §5.2.12; CICD-SEC-4 (indirect PPE form).

**Remediation action:**
> Assign the expression to an environment variable first, then reference it from the shell: `env: INPUT: ${{ inputs.foo }}` / `run: echo "$INPUT"`. The environment variable is a boundary the shell parser cannot cross. See https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions.

### `gha.HC-7` — `workflow_run` with untrusted artifact / checkout

**Pattern:** a workflow triggered by `workflow_run` that downloads artifacts from the triggering workflow and executes them, or checks out the PR head. `workflow_run` runs in the base-repo context with full secrets and write tokens — the same Direct-PPE surface as `pull_request_target`. GitHub's events reference is explicit: "has access to secrets and write tokens even when the triggering workflow lacks those permissions."

**Detection (multi-line):**
```
on:\s*\n\s*workflow_run  →  actions/download-artifact (untrusted)
on:\s*\n\s*workflow_run  →  actions/checkout with ref pointing at PR head
```

**Severity:** `block`

**Rubric:** devsecops.md §5.1.5; CICD-SEC-4; Scorecard Dangerous-Workflow.

**Remediation action:**
> Never execute downloaded artifacts from an untrusted workflow without sandboxing. If the `workflow_run` job only comments on PRs / merges labels, keep its token scope minimal and do not check out PR code. See https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows.

### `gha.HC-8` — `persist-credentials: true` on checkout followed by push

**Pattern:** `actions/checkout` with `persist-credentials: true` (the default when unset) followed anywhere in the same job by a `git push`, `gh pr comment`, or similar operation that uses the persisted `GITHUB_TOKEN`. If the checked-out code runs scripts (pre-commit hooks, `npm install` scripts, Makefile targets), those scripts gain access to the `.git/config`-persisted token. Classic Indirect-PPE vector.

**Detection (multi-line):** every `actions/checkout` step — verify either `with: persist-credentials: false` or that no subsequent step runs code from the checkout (npm install, make, pre-commit, etc.) before the `git push`.

**Severity:** `warn` (lift to `block` when the workflow also has `contents: write` permission)

**Rubric:** devsecops.md §5.1.5; CICD-SEC-4.

**Remediation action:**
> Set `with: persist-credentials: false` on `actions/checkout`. If you need to push back, use a dedicated token passed explicitly to `git push` via an env var at the moment of use, not via persistence.

### `gha.HC-9` — `actions/github-script` with user input interpolated into JS

**Pattern:** a step using `actions/github-script` whose inline `script:` body interpolates `${{ github.event.* }}` or `${{ inputs.* }}` directly into the JavaScript. The injection surface is identical to `gha.HC-6` but the HC-6 regex is shell-focused and will miss JS.

**Detection (ripgrep):**
```
uses:\s*actions/github-script
```
Then scan the `script:` body for `${{ github.event` / `${{ inputs`.

**Severity:** `block`

**Rubric:** devsecops.md §5.2.12; CICD-SEC-4.

**Remediation action:**
> Pass the input via `github.context.payload` or via `env:` / `script:` parameters, not via string interpolation: `env: BODY: ${{ github.event.pull_request.body }}` then `script: const body = process.env.BODY;`.

### `gha.HC-10` — Reusable workflow called unpinned

**Pattern:** `uses: <owner>/<repo>/.github/workflows/<file>.yml@<ref>` or `uses: ./.github/workflows/<file>.yml@<ref>` where `<ref>` is a branch name or moving tag (e.g. `@main`, `@v1`) rather than a 40-char SHA. Local `./` paths are fine (same repo, same commit); cross-repo reusables have the same pinning requirement as third-party actions.

**Detection (ripgrep):**
```
uses:\s*\S+\.ya?ml@\S+
```
For each match, extract the ref and check it is a 40-char SHA (for cross-repo) or accept local `./` refs.

**Severity:** `block` (cross-repo) / n/a (local `./`)

**Rubric:** devsecops.md §5.1.2; CICD-SEC-3.

**Remediation action:**
> Pin cross-repo reusable workflows to a 40-char SHA, same as third-party actions. Local `./` reusables inherit the caller's SHA and do not need separate pinning.

### `gha.HC-11` — Secrets interpolated into `run:` shell without env boundary

**Pattern:** a `run:` block with `${{ secrets.* }}` interpolated directly into the shell command, rather than via `env:`. Creates two problems: the secret is liable to leak into shell history / trace output, and the shell parser sees the raw value (so a secret containing shell metacharacters can cause command breakage). Distinct from `gha.HC-6` (which is about user input); both should be fixed, but via different patterns.

**Detection (ripgrep):**
```
run:.*\$\{\{\s*secrets\.
```

**Severity:** `warn`

**Rubric:** devsecops.md §5.2.12; https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/using-secrets-in-github-actions.

**Remediation action:**
> Assign to an env var first: `env: MY_SECRET: ${{ secrets.MY_SECRET }}` / `run: curl -H "Authorization: Bearer $MY_SECRET" ...`. Never echo the secret.

### `gha.HC-12` — Self-hosted runner on public repo, or non-ephemeral

**Pattern:** a workflow `runs-on:` referencing a self-hosted runner label (`self-hosted`, or a custom label) on a public repo, or without a just-in-time / ephemeral runner guarantee. GitHub's docs: "self-hosted runners should almost never be used for public repositories." Forked-PR workflows can run attacker code on the runner host; non-ephemeral runners leak state between jobs.

**Detection (ripgrep):**
```
runs-on:\s*\[?\s*(self-hosted|[\w-]+-self-hosted)
```
Cross-reference against repo visibility (from `gh api` or audit param) and runner registration method.

**Severity:** `warn` (block on confirmed public repo)

**Rubric:** devsecops.md §5.2.*; CICD-SEC-5; CICD-SEC-10.

**Remediation action:**
> Use GitHub-hosted runners for public repos. For self-hosted, use ephemeral / JIT runners (one-shot, registered just-in-time, deregistered after the job), restrict them to private repos, and isolate per-environment.

### `gha.HC-13` — No `timeout-minutes` on jobs

**Pattern:** a job without `timeout-minutes:` set. GitHub's default is 360 minutes (6 h). A hung job or a runaway scanner burns wallet and can serve as a DoS amplifier; a compromised job with no timeout can mine cryptocurrency until the billing cap hits.

**Detection:** for each job, verify `timeout-minutes:` is set. Long scans can legitimately need > 30 min; the absence of any value is the smell.

**Severity:** `warn`

**Remediation action:**
> Set `timeout-minutes:` on every job. Default 15 for short jobs; pick a value slightly above the observed p99 runtime for long ones.

## Positive signals

### `gha.POS-1` — Explicit minimum permissions

**Pattern:** every job declares `permissions:` with `contents: read` as the default, and write scopes only where needed with a justifying comment.

**Rubric:** devsecops.md §5.3.4.

### `gha.POS-2` — OIDC federation for cloud credentials

**Pattern:** the workflow declares `permissions: id-token: write` and authenticates via `azure/login@<sha>` or equivalent with `client-id` / `tenant-id` / `subscription-id` but **no** `client-secret`.

**Rubric:** devsecops.md §5.3.2; CICD-SEC-5 defended.

### `gha.POS-3` — Commit-SHA pinning for third-party actions

**Pattern:** ratio of `uses: owner/repo@<40-char-sha>` to total `uses:` declarations ≥ 0.9 (allowing first-party actions to be a small minority).

**Rubric:** devsecops.md §5.3.3.

### `gha.POS-4` — Production deploy gated by environment protection rules

**Pattern:** a `deploy` job targeting production declares `environment: production` (or similar) where that GitHub environment is configured with required reviewers, a wait timer, and branch restrictions (detectable via `gh api /repos/{owner}/{repo}/environments/{name}` when credentials are available). Canonical GitHub mitigation for CICD-SEC-1 (Insufficient Flow Control).

**Rubric:** devsecops.md §5.3.*; https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments.

## Carve-outs

- **Do not flag `gha.HC-2` as `block` for first-party actions pinned to a version tag when the action is in the same GitHub org as the audited repo.** "Same org" is not detectable from static grep alone — determine it by parsing `uses: owner/repo@ref` and comparing `owner` against the repo's GitHub org (inferred from `git remote get-url origin` or passed as an audit parameter). When the check is inconclusive, treat the finding as `block` — the carve-out is a downgrade, not a suppression. Monorepos may configure a known first-party-org list in `config.yaml` in a future version; for v1, the downgrade requires explicit opt-in per audit run.
- **Do not flag `gha.HC-1` on reusable workflow files that declare `permissions:` at the caller site.** The permissions declaration propagates.
