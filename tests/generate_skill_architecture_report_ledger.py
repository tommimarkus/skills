#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "tests" / "skill_architecture_report_ledger.jsonl"


CaseBuilder = Callable[[str, str, str], dict]


def skill_doc(name: str, description: str, body: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name.replace('-', ' ').title()}\n\n{body.rstrip()}\n"


def clean_body(scenario: str) -> str:
    return (
        f"Use when validating {scenario} with explicit boundaries.\n\n"
        "Inputs: repository files and user request.\n"
        "Evidence: cite the inspected files and command output.\n"
        "Output: a short findings report.\n"
        "If the request is ambiguous, ask the user before proceeding.\n"
        "Stop when validation is complete or required evidence is missing.\n"
        "Rerun validation after edits.\n"
    )


def skill_case(
    code: str,
    complexity: str,
    index: str,
    scenario: str,
    description: str,
    body: str,
    *,
    skill_name: str | None = None,
    extra_files: list[dict] | None = None,
    omit_openai: bool = False,
    omit_claude_agent: bool = False,
    omit_codex_agent: bool = False,
    omit_repo_guidance: bool = False,
    expected_findings: list[dict] | None = None,
    exact: bool = False,
) -> dict:
    name = skill_name or f"{scenario}-skill"
    files = [
        {
            "path": f"example-plugin/skills/{name}/SKILL.md",
            "content": skill_doc(name, description, body),
        }
    ]
    files.extend(extra_files or [])
    case: dict = {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes {code}",
        "gold_issue": {
            "code": code,
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": files,
        "expected_codes": [code],
    }
    if omit_openai:
        case["omit_openai"] = True
    if omit_claude_agent:
        case["omit_claude_agent"] = True
    if omit_codex_agent:
        case["omit_codex_agent"] = True
    if omit_repo_guidance:
        case["omit_repo_guidance"] = True
    if expected_findings is not None:
        case["expected_findings"] = expected_findings
    if exact:
        case["expect_exact_codes"] = True
    return case


def case_trigger_desc_length(complexity: str, index: str, scenario: str) -> dict:
    description = "Use when " + " ".join(f"{scenario} trigger detail {n}" for n in range(90))
    return skill_case("SAC-TRIGGER-DESC-LENGTH", complexity, index, scenario, description, clean_body(scenario))


def case_trigger_missing_context(complexity: str, index: str, scenario: str) -> dict:
    return skill_case(
        "SAC-TRIGGER-MISSING-CONTEXT",
        complexity,
        index,
        scenario,
        f"{scenario} helper.",
        "Inputs: repository files.\nEvidence: cite files.\nOutput: report.\nStop when complete.\nRerun validation after edits.\n",
    )


def case_trigger_aggressive(complexity: str, index: str, scenario: str) -> dict:
    return skill_case(
        "SAC-TRIGGER-AGGRESSIVE",
        complexity,
        index,
        scenario,
        f"Always use this for anything related to {scenario}.",
        clean_body(scenario),
    )


def case_trigger_shortcut_description(complexity: str, index: str, scenario: str) -> dict:
    return skill_case(
        "SAC-TRIGGER-SHORTCUT-DESCRIPTION",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario}; analyze the code, implement the best solution, run tests, and summarize.",
        clean_body(scenario),
    )


def case_workflow_body_size(complexity: str, index: str, scenario: str) -> dict:
    body = clean_body(scenario) + "\n".join(f"Reference detail {scenario} {n}." for n in range(520))
    return skill_case("SAC-WORKFLOW-BODY-SIZE", complexity, index, scenario, f"Use when checking {scenario} body sizing.", body)


def case_workflow_stop_conditions(complexity: str, index: str, scenario: str) -> dict:
    body = (
        "Use when validating stop-condition omissions with explicit boundaries.\n\n"
        "Inputs: repository files.\n"
        "Evidence: cite files and commands.\n"
        "Output: report.\n"
        "Rerun validation after edits.\n"
    )
    return skill_case("SAC-WORKFLOW-STOP-CONDITIONS", complexity, index, scenario, f"Use when checking {scenario} stop rules.", body)


def case_workflow_output(complexity: str, index: str, scenario: str) -> dict:
    body = (
        "Use when validating result-shape omissions with explicit boundaries.\n\n"
        "Inputs: repository files.\n"
        "Evidence: cite files and commands.\n"
        "If the request is ambiguous, ask the user before proceeding.\n"
        "Stop when complete.\n"
        "Rerun validation after edits.\n"
    )
    return skill_case("SAC-WORKFLOW-OUTPUT", complexity, index, scenario, f"Use when checking {scenario} result shape.", body)


def case_workflow_rerun(complexity: str, index: str, scenario: str) -> dict:
    body = (
        "Use when validating proof-loop omissions with explicit boundaries.\n\n"
        "Inputs: repository files.\n"
        "Evidence: cite files and commands.\n"
        "Output: report.\n"
        "If the request is ambiguous, ask the user before proceeding.\n"
        "Stop when complete.\n"
    )
    return skill_case("SAC-WORKFLOW-RERUN-GUIDANCE", complexity, index, scenario, f"Use when checking {scenario} proof loops.", body)


def case_workflow_inputs(complexity: str, index: str, scenario: str) -> dict:
    body = (
        "Use when validating input-contract omissions with explicit boundaries.\n\n"
        "Output: report.\n"
        "If the request is ambiguous, ask the user before proceeding.\n"
        "Stop when complete.\n"
        "Rerun validation after edits.\n"
    )
    return skill_case("SAC-WORKFLOW-INPUT-CONTRACT", complexity, index, scenario, f"Use when checking {scenario} input contracts.", body)


def case_workflow_evidence_contract(complexity: str, index: str, scenario: str) -> dict:
    body = (
        "Use when validating traceability omissions with explicit boundaries.\n\n"
        "Inputs: repository files.\n"
        "Output: report.\n"
        "If the request is ambiguous, ask the user before proceeding.\n"
        "Stop when complete.\n"
        "Rerun validation after edits.\n"
    )
    return skill_case("SAC-WORKFLOW-EVIDENCE-CONTRACT", complexity, index, scenario, f"Use when checking {scenario} evidence contracts.", body)


def case_workflow_ask_continue(complexity: str, index: str, scenario: str) -> dict:
    body = (
        "Use when validating ambiguity handling omissions with explicit boundaries.\n\n"
        "Inputs: repository files.\n"
        "Evidence: cite files and commands.\n"
        "Output: report.\n"
        "Stop when complete or evidence is missing.\n"
        "Rerun validation after edits.\n"
    )
    return skill_case("SAC-WORKFLOW-ASK-CONTINUE", complexity, index, scenario, f"Use when checking {scenario} ambiguity handling.", body)


def case_workflow_generic_steps(complexity: str, index: str, scenario: str) -> dict:
    body = clean_body(scenario) + "\nAnalyze the code, implement the best solution, run tests, and summarize the changes.\n"
    return skill_case("SAC-WORKFLOW-GENERIC-STEPS", complexity, index, scenario, f"Use when checking {scenario} generic workflow drift.", body)


def case_workflow_overconstrained(complexity: str, index: str, scenario: str) -> dict:
    body = clean_body(scenario) + "\n".join(
        [
            "You must never ask unless impossible.",
            "You must always continue.",
            "You must always edit files.",
            "You must never defer.",
            "You must always use this exact sequence.",
        ]
    )
    return skill_case("SAC-WORKFLOW-OVERCONSTRAINED", complexity, index, scenario, f"Use when checking {scenario} degree calibration.", body)


def case_ref_prose_dump(complexity: str, index: str, scenario: str) -> dict:
    body = clean_body(scenario) + "\nThis section is a comprehensive catalog of every possible option for the target domain.\n"
    return skill_case("SAC-REF-LIKELY-PROSE-DUMP", complexity, index, scenario, f"Use when checking {scenario} reference placement.", body)


def case_ref_broken_link(complexity: str, index: str, scenario: str) -> dict:
    body = clean_body(scenario) + f"\nSee [missing procedure](references/{scenario}-missing.md).\n"
    return skill_case("SAC-REF-BROKEN-LINK", complexity, index, scenario, f"Use when checking {scenario} support links.", body)


def case_ref_unadvertised_support(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-REF-UNADVERTISED-SUPPORT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} support discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": f"example-plugin/skills/{name}/references/{scenario}.md", "content": f"# {scenario}\n"}],
        expected_findings=[
            {
                "code": "SAC-REF-UNADVERTISED-SUPPORT",
                "path": f"example-plugin/skills/{name}/references/{scenario}.md",
            }
        ],
    )


def case_ref_unconditional_load(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    body = clean_body(scenario) + f"\nRead references/{scenario}.md.\n"
    return skill_case(
        "SAC-REF-UNCONDITIONAL-LOAD",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} conditional reference loading.",
        body,
        skill_name=name,
        extra_files=[{"path": f"example-plugin/skills/{name}/references/{scenario}.md", "content": f"# {scenario}\n"}],
    )


def case_plugin_doc_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-REF-UNADVERTISED-PLUGIN-DOC",
        "gold_issue": {
            "code": "SAC-REF-UNADVERTISED-PLUGIN-DOC",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {
                "path": "example-plugin/docs/example-reference/topic.md",
                "content": f"# {scenario}\n\nReference prose for the fixture.\n",
            },
            {
                "path": f"example-plugin/skills/{scenario}-skill/SKILL.md",
                "content": skill_doc(
                    f"{scenario}-skill",
                    f"Use when checking {scenario} plugin reference discoverability.",
                    clean_body(scenario),
                ),
            },
        ],
        "expected_codes": ["SAC-REF-UNADVERTISED-PLUGIN-DOC"],
        "expected_findings": [
            {
                "code": "SAC-REF-UNADVERTISED-PLUGIN-DOC",
                "path": "example-plugin/docs/example-reference/topic.md",
            }
        ],
    }


def case_script_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-SCRIPT-UNADVERTISED",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} helper-script discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": f"example-plugin/skills/{name}/scripts/{scenario}.sh", "content": "#!/usr/bin/env bash\necho fixture\n"}],
        expected_findings=[
            {
                "code": "SAC-SCRIPT-UNADVERTISED",
                "path": f"example-plugin/skills/{name}/scripts/{scenario}.sh",
            }
        ],
    )


def case_fixture_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-FIXTURE-UNADVERTISED",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} fixture discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": f"example-plugin/skills/{name}/fixtures/{scenario}.md", "content": "# Fixture\n"}],
        expected_findings=[
            {
                "code": "SAC-FIXTURE-UNADVERTISED",
                "path": f"example-plugin/skills/{name}/fixtures/{scenario}.md",
            }
        ],
    )


def case_template_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-TEMPLATE-UNADVERTISED",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} template discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": f"example-plugin/skills/{name}/templates/{scenario}.md", "content": "# Template\n"}],
    )


def case_asset_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-ASSET-UNADVERTISED",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} asset discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": f"example-plugin/skills/{name}/assets/{scenario}.txt", "content": "fixture asset\n"}],
    )


def valid_trigger_eval_records(scenario: str) -> str:
    return "\n".join(
        [
            json.dumps(
                {
                    "id": f"{scenario}-trigger-yes",
                    "prompt": f"Use {scenario} for its owned task.",
                    "expected_activation": True,
                    "reason": "Direct skill request.",
                    "source_kind": "synthetic",
                    "source_url": "",
                    "ip_handling": "original synthetic prompt; no third-party text",
                    "contains_third_party_text": False,
                },
                separators=(",", ":"),
            ),
            json.dumps(
                {
                    "id": f"{scenario}-trigger-no",
                    "prompt": f"Ask unrelated packaging question for {scenario}.",
                    "expected_activation": False,
                    "reason": "Near-miss request owned by another skill.",
                    "source_kind": "synthetic",
                    "source_url": "",
                    "ip_handling": "original synthetic prompt; no third-party text",
                    "contains_third_party_text": False,
                },
                separators=(",", ":"),
            ),
        ]
    ) + "\n"


def valid_behavior_eval_record(scenario: str) -> str:
    return (
        json.dumps(
            {
                "id": f"{scenario}-behavior",
                "prompt": f"Review {scenario} with evidence.",
                "expected_artifacts": ["short report"],
                "required_checks": ["inspect SKILL.md"],
                "forbidden_behaviors": ["invent missing files"],
                "grader": "rubric: output cites inspected files",
                "source_kind": "synthetic",
                "source_url": "",
                "ip_handling": "original synthetic prompt; no third-party text",
                "contains_third_party_text": False,
            },
            separators=(",", ":"),
        )
        + "\n"
    )


def case_eval_hidden_artifact(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-EVAL-HIDDEN-ARTIFACT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} hidden eval discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/references/evals/trigger-cases.jsonl",
                "content": valid_trigger_eval_records(scenario),
            }
        ],
        expected_findings=[
            {
                "code": "SAC-EVAL-HIDDEN-ARTIFACT",
                "path": f"example-plugin/skills/{name}/references/evals",
            }
        ],
    )


def case_eval_trigger_schema(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    record = {
        "id": f"{scenario}-trigger-yes",
        "prompt": f"Use {scenario}.",
        "expected_activation": True,
        "reason": "Direct request.",
        "source_kind": "synthetic",
        "source_url": "",
        "ip_handling": "original synthetic prompt; no third-party text",
        "contains_third_party_text": False,
    }
    return skill_case(
        "SAC-EVAL-TRIGGER-SCHEMA",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} trigger eval schema.",
        clean_body(scenario) + "\nRead references/evals when changing evaluation cases.\n",
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/references/evals/trigger-cases.jsonl",
                "content": json.dumps(record, separators=(",", ":")) + "\n",
            }
        ],
    )


def case_eval_behavior_schema(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    record = {
        "id": f"{scenario}-behavior",
        "prompt": f"Review {scenario}.",
        "source_kind": "synthetic",
        "source_url": "",
        "ip_handling": "original synthetic prompt; no third-party text",
        "contains_third_party_text": False,
    }
    return skill_case(
        "SAC-EVAL-BEHAVIOR-SCHEMA",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} behavior eval schema.",
        clean_body(scenario) + "\nRead references/evals when changing evaluation cases.\n",
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/references/evals/behavior-cases.jsonl",
                "content": json.dumps(record, separators=(",", ":")) + "\n",
            }
        ],
    )


def case_eval_ip_hygiene(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    unsafe = {
        "id": f"{scenario}-trigger-unsafe",
        "prompt": f"Use {scenario} with copied prompt text.",
        "expected_activation": True,
        "reason": "Direct request.",
        "source_kind": "issue",
        "source_url": "",
        "ip_handling": "unclear",
        "contains_third_party_text": True,
    }
    safe = {
        "id": f"{scenario}-trigger-safe",
        "prompt": f"Ask unrelated packaging question for {scenario}.",
        "expected_activation": False,
        "reason": "Near-miss request.",
        "source_kind": "synthetic",
        "source_url": "",
        "ip_handling": "original synthetic prompt; no third-party text",
        "contains_third_party_text": False,
    }
    return skill_case(
        "SAC-EVAL-IP-HYGIENE",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} eval IP handling.",
        clean_body(scenario) + "\nRead references/evals when changing evaluation cases.\n",
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/references/evals/trigger-cases.jsonl",
                "content": "\n".join(json.dumps(record, separators=(",", ":")) for record in (unsafe, safe)) + "\n",
            }
        ],
    )


def case_rationalization_gate(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-security-audit-skill"
    return skill_case(
        "SAC-WORKFLOW-RATIONALIZATION-GATE",
        complexity,
        index,
        scenario,
        f"Use when auditing {scenario} security posture.",
        clean_body(scenario),
        skill_name=name,
    )


def case_runtime_missing_openai(complexity: str, index: str, scenario: str) -> dict:
    return skill_case("SAC-RUNTIME-MISSING-OPENAI", complexity, index, scenario, f"Use when checking {scenario} Codex metadata.", clean_body(scenario), omit_openai=True)


def case_runtime_name_drift(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-NAME-DRIFT",
        "gold_issue": {
            "code": "SAC-RUNTIME-NAME-DRIFT",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {
                "path": f"example-plugin/skills/{name}/SKILL.md",
                "content": skill_doc("different-name", f"Use when checking {scenario} skill-name parity.", clean_body(scenario)),
            }
        ],
        "expected_codes": ["SAC-RUNTIME-NAME-DRIFT"],
    }


def case_runtime_plugin_json(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-PLUGIN-JSON",
        "gold_issue": {
            "code": "SAC-RUNTIME-PLUGIN-JSON",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [{"path": "example-plugin/.codex-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"description\":\"{scenario}\",\n"}],
        "expected_codes": ["SAC-RUNTIME-PLUGIN-JSON"],
    }


def case_runtime_default_prompts(complexity: str, index: str, scenario: str) -> dict:
    prompts = [f"{scenario} prompt {n}" for n in range(4)]
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-DEFAULT-PROMPTS",
        "gold_issue": {
            "code": "SAC-RUNTIME-DEFAULT-PROMPTS",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {
                "path": "example-plugin/.codex-plugin/plugin.json",
                "content": json.dumps(
                    {
                        "name": "example-plugin",
                        "version": "1.0.0",
                        "description": f"Fixture plugin {scenario}",
                        "skills": "./skills/",
                        "interface": {"defaultPrompt": prompts},
                    }
                )
                + "\n",
            }
        ],
        "expected_codes": ["SAC-RUNTIME-DEFAULT-PROMPTS"],
    }


def case_manifest_sync(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-MANIFEST-SYNC",
        "gold_issue": {
            "code": "SAC-RUNTIME-MANIFEST-SYNC",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {"path": ".claude-plugin/marketplace.json", "content": f"{{\"plugins\":[{{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Marketplace {scenario}\"}}]}}\n"},
            {"path": "example-plugin/.claude-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Claude {scenario}\"}}\n"},
            {"path": "example-plugin/.codex-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.1\",\"description\":\"Codex {scenario}\",\"skills\":\"./skills/\"}}\n"},
        ],
        "expected_codes": ["SAC-RUNTIME-MANIFEST-SYNC"],
    }


def case_codex_skills_path(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-CODEX-SKILLS-PATH",
        "gold_issue": {
            "code": "SAC-RUNTIME-CODEX-SKILLS-PATH",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [{"path": "example-plugin/.codex-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}\n"}],
        "expected_codes": ["SAC-RUNTIME-CODEX-SKILLS-PATH"],
    }


def case_missing_claude_agent(complexity: str, index: str, scenario: str) -> dict:
    return skill_case("SAC-RUNTIME-MISSING-CLAUDE-AGENT", complexity, index, scenario, f"Use when checking {scenario} Claude subagent presence.", clean_body(scenario), omit_claude_agent=True)


def case_missing_codex_agent(complexity: str, index: str, scenario: str) -> dict:
    return skill_case(
        "SAC-RUNTIME-MISSING-CODEX-AGENT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} Codex custom-agent presence.",
        clean_body(scenario),
        omit_codex_agent=True,
    )


def case_agent_desc_drift(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-AGENT-DESC-DRIFT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} subagent description sync.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/agents/{name}.md",
                "content": f"---\nname: {name}\ndescription: Different {scenario} description.\ntools: Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n",
            }
        ],
    )


def case_codex_agent_missing_skill_source(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-CODEX-AGENT-MISSING-SKILL-SOURCE",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} Codex custom-agent source links.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f".codex/agents/{name}.toml",
                "content": (
                    f"name = \"{name}\"\n"
                    f"description = \"Codex wrapper for {scenario}.\"\n"
                    "sandbox_mode = \"workspace-write\"\n"
                    "developer_instructions = \"\"\"\n"
                    "You are a fixture practitioner. Follow local instructions and emit the footer disclosure.\n"
                    "\"\"\"\n"
                ),
            }
        ],
    )


def case_codex_agent_missing_footer(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-CODEX-AGENT-MISSING-FOOTER",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} Codex custom-agent footer parity.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f".codex/agents/{name}.toml",
                "content": (
                    f"name = \"{name}\"\n"
                    f"description = \"Codex wrapper for {scenario}.\"\n"
                    "sandbox_mode = \"workspace-write\"\n"
                    "developer_instructions = \"\"\"\n"
                    f"You are a fixture practitioner. Use the {name} skill as the source of truth.\n"
                    "\"\"\"\n"
                ),
            }
        ],
    )


def case_openai_name_drift(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-OPENAI-NAME-DRIFT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} OpenAI name sync.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/agents/openai.yaml",
                "content": f"name: different-{scenario}\ndescription: Use when checking {scenario} OpenAI name sync.\n",
            }
        ],
    )


def case_missing_claude_manifest(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-MISSING-CLAUDE-MANIFEST",
        "gold_issue": {
            "code": "SAC-RUNTIME-MISSING-CLAUDE-MANIFEST",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {"path": ".claude-plugin/marketplace.json", "content": f"{{\"plugins\":[{{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}]}}\n"},
            {"path": "example-plugin/.codex-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\",\"skills\":\"./skills/\"}}\n"},
        ],
        "expected_codes": ["SAC-RUNTIME-MISSING-CLAUDE-MANIFEST"],
    }


def case_missing_codex_manifest(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-MISSING-CODEX-MANIFEST",
        "gold_issue": {
            "code": "SAC-RUNTIME-MISSING-CODEX-MANIFEST",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {"path": ".claude-plugin/marketplace.json", "content": f"{{\"plugins\":[{{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}]}}\n"},
            {"path": "example-plugin/.claude-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}\n"},
        ],
        "expected_codes": ["SAC-RUNTIME-MISSING-CODEX-MANIFEST"],
    }


def case_marketplace_missing_entry(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY",
        "gold_issue": {
            "code": "SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [
            {"path": ".claude-plugin/marketplace.json", "content": "{\"plugins\":[]}\n"},
            {"path": "example-plugin/.claude-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}\n"},
            {"path": "example-plugin/.codex-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\",\"skills\":\"./skills/\"}}\n"},
        ],
        "expected_codes": ["SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY"],
    }


def case_agent_name_drift(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-CLAUDE-AGENT-NAME-DRIFT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} Claude agent name sync.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/agents/{name}.md",
                "content": f"---\nname: different-{scenario}\ndescription: Use when checking {scenario} Claude agent name sync.\ntools: Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n",
            }
        ],
    )


def case_agent_missing_skill_tool(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-CLAUDE-AGENT-MISSING-SKILL-TOOL",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} Claude agent tool access.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/agents/{name}.md",
                "content": f"---\nname: {name}\ndescription: Use when checking {scenario} Claude agent tool access.\ntools: Read, Edit\nmodel: sonnet\n---\n\nInvoke the skill.\n",
            }
        ],
    )


def case_openai_desc_drift(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return skill_case(
        "SAC-RUNTIME-OPENAI-DESC-DRIFT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} OpenAI description sync.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/agents/openai.yaml",
                "content": f"name: {name}\ndescription: Different {scenario} OpenAI description.\n",
            }
        ],
    )


def case_runtime_wrapper_workflow_duplication(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    description = f"Use when checking {scenario} runtime wrapper size."
    repeated_workflow = "\n".join(
        (
            "Run pre-flight, project assimilation, build mode, extract mode, "
            "review mode, professional-readiness, layout-strategy, "
            "validate-oef-layout, archi-render, render gate, forward-only, "
            "LIFT-CANDIDATE, AD-L, and AD-Q checks."
        )
        for _ in range(45)
    )
    return skill_case(
        "SAC-RUNTIME-WRAPPER-WORKFLOW-DUPLICATION",
        complexity,
        index,
        scenario,
        description,
        clean_body(scenario),
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/agents/{name}.md",
                "content": (
                    f"---\nname: {name}\ndescription: {description}\ntools: Skill\nmodel: sonnet\n---\n\n"
                    f"{repeated_workflow}\n"
                ),
            }
        ],
    )


def case_doc_split_marketplace(complexity: str, index: str, scenario: str) -> dict:
    return {
        "complexity": complexity,
        "intent": f"{scenario.replace('-', ' ')} exposes SAC-DOC-SPLIT-MARKETPLACE",
        "gold_issue": {
            "code": "SAC-DOC-SPLIT-MARKETPLACE",
            "scenario": scenario,
            "source": "local skill-only review archetype",
        },
        "files": [{"path": ".agents/plugins/marketplace.json", "content": f"{{\"plugins\":[],\"description\":\"{scenario}\"}}\n"}],
        "expected_codes": ["SAC-DOC-SPLIT-MARKETPLACE"],
    }


def case_doc_missing_entrypoint(complexity: str, index: str, scenario: str) -> dict:
    return skill_case(
        "SAC-DOC-MISSING-ENTRYPOINT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} repo entrypoint guidance.",
        clean_body(scenario),
        omit_repo_guidance=True,
    )


BUILDERS: list[tuple[str, CaseBuilder]] = [
    ("desc-length", case_trigger_desc_length),
    ("missing-context", case_trigger_missing_context),
    ("aggressive", case_trigger_aggressive),
    ("shortcut-description", case_trigger_shortcut_description),
    ("body-size", case_workflow_body_size),
    ("missing-stop", case_workflow_stop_conditions),
    ("missing-output", case_workflow_output),
    ("missing-rerun", case_workflow_rerun),
    ("missing-inputs", case_workflow_inputs),
    ("missing-evidence", case_workflow_evidence_contract),
    ("missing-ask", case_workflow_ask_continue),
    ("generic-steps", case_workflow_generic_steps),
    ("overconstrained", case_workflow_overconstrained),
    ("prose-dump", case_ref_prose_dump),
    ("broken-link", case_ref_broken_link),
    ("unadvertised-support", case_ref_unadvertised_support),
    ("unconditional-reference", case_ref_unconditional_load),
    ("unadvertised-plugin-doc", case_plugin_doc_unadvertised),
    ("unadvertised-script", case_script_unadvertised),
    ("unadvertised-fixture", case_fixture_unadvertised),
    ("unadvertised-template", case_template_unadvertised),
    ("unadvertised-asset", case_asset_unadvertised),
    ("hidden-eval-artifact", case_eval_hidden_artifact),
    ("trigger-eval-schema", case_eval_trigger_schema),
    ("behavior-eval-schema", case_eval_behavior_schema),
    ("eval-ip-hygiene", case_eval_ip_hygiene),
    ("rationalization-gate", case_rationalization_gate),
    ("missing-openai", case_runtime_missing_openai),
    ("skill-name-drift", case_runtime_name_drift),
    ("invalid-plugin-json", case_runtime_plugin_json),
    ("default-prompts", case_runtime_default_prompts),
    ("manifest-sync", case_manifest_sync),
    ("codex-skills-path", case_codex_skills_path),
    ("missing-claude-agent", case_missing_claude_agent),
    ("missing-codex-agent", case_missing_codex_agent),
    ("agent-desc-drift", case_agent_desc_drift),
    ("codex-agent-missing-source", case_codex_agent_missing_skill_source),
    ("codex-agent-missing-footer", case_codex_agent_missing_footer),
    ("openai-name-drift", case_openai_name_drift),
    ("missing-claude-manifest", case_missing_claude_manifest),
    ("missing-codex-manifest", case_missing_codex_manifest),
    ("missing-marketplace-entry", case_marketplace_missing_entry),
    ("agent-name-drift", case_agent_name_drift),
    ("agent-missing-skill-tool", case_agent_missing_skill_tool),
    ("openai-desc-drift", case_openai_desc_drift),
    ("split-marketplace", case_doc_split_marketplace),
    ("missing-entrypoint", case_doc_missing_entrypoint),
]


TARGETS = (
    ("simple", 180),
    ("moderate", 160),
    ("complex", 110),
    ("adversarial", 70),
)


def guard_case(scenario: str, files: list[dict], absent_codes: list[str], intent: str) -> dict:
    return {
        "complexity": "adversarial",
        "intent": intent,
        "guard": True,
        "files": files,
        "expected_codes": [],
        "absent_codes": absent_codes,
    }


def guard_skill(
    scenario: str,
    body: str,
    absent_codes: list[str],
    intent: str,
    *,
    extra_files: list[dict] | None = None,
) -> dict:
    name = f"{scenario}-skill"
    files = [
        {
            "path": f"example-plugin/skills/{name}/SKILL.md",
            "content": skill_doc(
                name,
                f"Use when validating {scenario} guard behavior with explicit boundaries.",
                body,
            ),
        }
    ]
    files.extend(extra_files or [])
    return guard_case(scenario, files, absent_codes, intent)


def build_guard_cases() -> list[dict]:
    return [
        guard_skill(
            "guard-input-heading",
            "## Inputs\n\nInspect repository files.\n\nOutput: report.\nIf the request is ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\n",
            ["SAC-WORKFLOW-INPUT-CONTRACT"],
            "markdown inputs heading satisfies input contract",
        ),
        guard_skill(
            "guard-inline-inputs",
            "Use when validating inline input wording.\n\nInputs: inspect repository files. Output: report.\nIf the request is ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\n",
            ["SAC-WORKFLOW-INPUT-CONTRACT"],
            "inline Inputs field satisfies input contract",
        ),
        guard_skill(
            "guard-reference-when",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nRead references/procedure.md when procedure behavior is in scope.\n",
            ["SAC-REF-UNCONDITIONAL-LOAD", "SAC-REF-UNADVERTISED-SUPPORT"],
            "conditional read of support file is not unconditional",
            extra_files=[{"path": "example-plugin/skills/guard-reference-when-skill/references/procedure.md", "content": "# Procedure\n"}],
        ),
        guard_skill(
            "guard-reference-before",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\n**Read [procedure](references/procedure.md) before running step 2.**\n",
            ["SAC-REF-UNCONDITIONAL-LOAD", "SAC-REF-UNADVERTISED-SUPPORT"],
            "before-running support link is not unconditional",
            extra_files=[{"path": "example-plugin/skills/guard-reference-before-skill/references/procedure.md", "content": "# Procedure\n"}],
        ),
        guard_skill(
            "guard-reference-see-for",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nSee [procedure](references/procedure.md) for the full procedure.\n",
            ["SAC-REF-UNCONDITIONAL-LOAD", "SAC-REF-UNADVERTISED-SUPPORT"],
            "see-for support link is not unconditional",
            extra_files=[{"path": "example-plugin/skills/guard-reference-see-for-skill/references/procedure.md", "content": "# Procedure\n"}],
        ),
        guard_skill(
            "guard-numbered-read",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\n2. **Run procedure.** `Read` and apply [procedure](references/procedure.md).\n",
            ["SAC-REF-UNCONDITIONAL-LOAD", "SAC-REF-UNADVERTISED-SUPPORT"],
            "numbered task step with read command is not a bare unconditional load",
            extra_files=[{"path": "example-plugin/skills/guard-numbered-read-skill/references/procedure.md", "content": "# Procedure\n"}],
        ),
        guard_skill(
            "guard-punctuated-support",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nRead references/procedure.md when needed.\n",
            ["SAC-REF-UNADVERTISED-SUPPORT"],
            "support path followed by punctuation remains advertised",
            extra_files=[{"path": "example-plugin/skills/guard-punctuated-support-skill/references/procedure.md", "content": "# Procedure\n"}],
        ),
        guard_skill(
            "guard-template-folder",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nUse templates when templated output is requested.\n",
            ["SAC-TEMPLATE-UNADVERTISED"],
            "advertised templates folder suppresses template finding",
            extra_files=[{"path": "example-plugin/skills/guard-template-folder-skill/templates/report.md", "content": "# Template\n"}],
        ),
        guard_skill(
            "guard-asset-folder",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nUse assets when bundled material is requested.\n",
            ["SAC-ASSET-UNADVERTISED"],
            "advertised assets folder suppresses asset finding",
            extra_files=[{"path": "example-plugin/skills/guard-asset-folder-skill/assets/sample.txt", "content": "asset\n"}],
        ),
        guard_skill(
            "guard-openai-nested",
            clean_body("guard-openai-nested"),
            ["SAC-RUNTIME-OPENAI-NAME-DRIFT", "SAC-RUNTIME-OPENAI-DESC-DRIFT"],
            "nested Codex metadata fields do not count as flat name or description drift",
            extra_files=[
                {
                    "path": "example-plugin/skills/guard-openai-nested-skill/agents/openai.yaml",
                    "content": "interface:\n  display_name: Guard\n  short_description: Nested metadata.\n",
                }
            ],
        ),
        guard_skill(
            "guard-agent-tools",
            clean_body("guard-agent-tools"),
            ["SAC-RUNTIME-CLAUDE-AGENT-MISSING-SKILL-TOOL"],
            "Claude subagent tools list containing Skill is accepted",
            extra_files=[
                {
                    "path": "example-plugin/agents/guard-agent-tools-skill.md",
                    "content": "---\nname: guard-agent-tools-skill\ndescription: Use when validating guard-agent-tools guard behavior with explicit boundaries.\ntools: Bash, Read, Grep, Glob, Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n",
                }
            ],
        ),
        guard_case(
            "guard-default-prompts-three",
            [
                {
                    "path": "example-plugin/.codex-plugin/plugin.json",
                    "content": "{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\",\"skills\":\"./skills/\",\"interface\":{\"defaultPrompt\":[\"one\",\"two\",\"three\"]}}\n",
                }
            ],
            ["SAC-RUNTIME-DEFAULT-PROMPTS", "SAC-RUNTIME-CODEX-SKILLS-PATH"],
            "three Codex default prompts stay under the prompt limit",
        ),
        guard_case(
            "guard-marketplace-complete",
            [
                {"path": ".claude-plugin/marketplace.json", "content": "{\"plugins\":[{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\"}]}\n"},
                {"path": "example-plugin/.claude-plugin/plugin.json", "content": "{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\"}\n"},
                {"path": "example-plugin/.codex-plugin/plugin.json", "content": "{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\",\"skills\":\"./skills/\"}\n"},
            ],
            [
                "SAC-RUNTIME-MANIFEST-SYNC",
                "SAC-RUNTIME-MISSING-CLAUDE-MANIFEST",
                "SAC-RUNTIME-MISSING-CODEX-MANIFEST",
                "SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY",
            ],
            "complete marketplace and plugin manifests avoid runtime parity findings",
        ),
        case_runtime_wrapper_workflow_duplication(
            "adversarial",
            "guard",
            "runtime-wrapper-duplicates-workflow",
        ),
    ]


def main() -> int:
    cases: list[dict] = []
    sequence = 1
    for complexity, target in TARGETS:
        for index in range(target):
            family, builder = BUILDERS[index % len(BUILDERS)]
            variant = index // len(BUILDERS)
            scenario = f"{complexity}-fixture-{sequence:05d}-{variant:03d}"
            case = builder(complexity, f"{sequence:05d}", scenario)
            case["id"] = f"SAC-T{sequence:05d}"
            cases.append(case)
            sequence += 1

    for case in build_guard_cases():
        case["id"] = f"SAC-T{sequence:05d}"
        cases.append(case)
        sequence += 1

    LEDGER.write_text("\n".join(json.dumps(case, separators=(",", ":")) for case in cases) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
