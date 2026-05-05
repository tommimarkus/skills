# `souroldgeezer-audit`

`souroldgeezer-audit` ships the audit plugin for DevSecOps posture and test
quality. It stays rubric-driven: the skills apply bundled references and report
smell codes, but they do not duplicate the rubric prose.

## Skills

| Skill | What it covers | Notes |
|---|---|---|
| [devsecops-audit](../../souroldgeezer-audit/skills/devsecops-audit/SKILL.md) | Pipelines, IaC, release artifacts, and code-level security smells | Loads per-stack extensions on demand |
| [test-quality-audit](../../souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | Unit, integration, and E2E test quality | Dispatches by detected test type |

## Packaging notes

- Claude Code and Codex share the same marketplace entry for this plugin.
- Each skill has a matching Claude Code subagent and Codex per-skill metadata.
- Extension details and rubrics stay in the skill tree and bundled references.
