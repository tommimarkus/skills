#!/usr/bin/env python3
# lean-audit:dup-intentional — parallel per-case test bodies kept literal for readability
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


def _base_envelope(code: str, complexity: str, scenario: str, files: list) -> dict:
    """The complexity/intent/gold_issue/files/expected_codes envelope shared by every
    case builder, whether it goes through skill_case or builds its own `files` list
    from scratch (marketplace.json, plugin.json, ...)."""
    return {
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
    omit_claude_agent: bool = False,
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
    case = _base_envelope(code, complexity, scenario, files)
    if omit_claude_agent:
        case["omit_claude_agent"] = True
    if omit_repo_guidance:
        case["omit_repo_guidance"] = True
    if expected_findings is not None:
        case["expected_findings"] = expected_findings
    if exact:
        case["expect_exact_codes"] = True
    return case


def bare_case(code: str, complexity: str, scenario: str, files: list, *,
              expected_findings: list | None = None) -> dict:
    """Case envelope for the builders that construct their own `files` list from
    scratch (marketplace.json, plugin.json, ...) rather than going through skill_case."""
    case = _base_envelope(code, complexity, scenario, files)
    if expected_findings is not None:
        case["expected_findings"] = expected_findings
    return case


def case_unadvertised_artifact(
    code: str, complexity: str, index: str, scenario: str, *,
    kind: str, subdir: str, filename: str, content: str, expect_finding: bool = True,
) -> dict:
    """A skill with one extra file under `subdir` that SKILL.md never references.
    Shared shape for the SAC-*-UNADVERTISED case builders (references/scripts/
    fixtures/templates/assets)."""
    name = f"{scenario}-skill"
    path = f"example-plugin/skills/{name}/{subdir}/{filename}"
    return skill_case(
        code, complexity, index, scenario,
        f"Use when checking {scenario} {kind} discoverability.",
        clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": path, "content": content}],
        expected_findings=[{"code": code, "path": path}] if expect_finding else None,
    )


def case_with_agent_file(code: str, complexity: str, index: str, scenario: str, *,
                         description: str, agent_content: str) -> dict:
    """A skill with a companion agents/<name>.md file whose frontmatter drifts from
    the skill in some way. Shared shape for the SAC-RUNTIME-*AGENT* case builders."""
    name = f"{scenario}-skill"
    return skill_case(
        code, complexity, index, scenario, description, clean_body(scenario),
        skill_name=name,
        extra_files=[{"path": f"example-plugin/agents/{name}.md", "content": agent_content}],
    )


def case_with_eval_file(code: str, complexity: str, index: str, scenario: str, *,
                        description: str, eval_filename: str, content: str) -> dict:
    """A skill whose Load-Map cites references/evals, with one evals file containing
    `content`. Shared shape for the SAC-EVAL-* schema/hygiene case builders."""
    name = f"{scenario}-skill"
    return skill_case(
        code, complexity, index, scenario, description,
        clean_body(scenario) + "\nRead references/evals when changing evaluation cases.\n",
        skill_name=name,
        extra_files=[
            {
                "path": f"example-plugin/skills/{name}/references/evals/{eval_filename}",
                "content": content,
            }
        ],
    )


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
    return case_unadvertised_artifact(
        "SAC-REF-UNADVERTISED-SUPPORT", complexity, index, scenario,
        kind="support", subdir="references", filename=f"{scenario}.md", content=f"# {scenario}\n",
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
    return bare_case(
        "SAC-REF-UNADVERTISED-PLUGIN-DOC", complexity, scenario,
        files=[
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
        expected_findings=[
            {
                "code": "SAC-REF-UNADVERTISED-PLUGIN-DOC",
                "path": "example-plugin/docs/example-reference/topic.md",
            }
        ],
    )


def case_ref_private_plugin_root(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    reference_path = f"example-plugin/references/{scenario}-procedures/check.md"
    body = clean_body(scenario) + f"\nRead ../../references/{scenario}-procedures/check.md when the detailed procedure is in scope.\n"
    return skill_case(
        "SAC-REF-PRIVATE-PLUGIN-ROOT",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} support ownership locality.",
        body,
        skill_name=name,
        extra_files=[{"path": reference_path, "content": "# Private Procedure\n"}],
        expected_findings=[
            {
                "code": "SAC-REF-PRIVATE-PLUGIN-ROOT",
                "path": reference_path,
            }
        ],
    )


def case_script_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    return case_unadvertised_artifact(
        "SAC-SCRIPT-UNADVERTISED", complexity, index, scenario,
        kind="helper-script", subdir="scripts", filename=f"{scenario}.sh",
        content="#!/usr/bin/env bash\necho fixture\n",
    )


def case_fixture_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    return case_unadvertised_artifact(
        "SAC-FIXTURE-UNADVERTISED", complexity, index, scenario,
        kind="fixture", subdir="fixtures", filename=f"{scenario}.md", content="# Fixture\n",
    )


def case_template_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    return case_unadvertised_artifact(
        "SAC-TEMPLATE-UNADVERTISED", complexity, index, scenario,
        kind="template", subdir="templates", filename=f"{scenario}.md", content="# Template\n",
        expect_finding=False,
    )


def case_asset_unadvertised(complexity: str, index: str, scenario: str) -> dict:
    return case_unadvertised_artifact(
        "SAC-ASSET-UNADVERTISED", complexity, index, scenario,
        kind="asset", subdir="assets", filename=f"{scenario}.txt", content="fixture asset\n",
        expect_finding=False,
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
    return case_with_eval_file(
        "SAC-EVAL-TRIGGER-SCHEMA", complexity, index, scenario,
        description=f"Use when checking {scenario} trigger eval schema.",
        eval_filename="trigger-cases.jsonl",
        content=json.dumps(record, separators=(",", ":")) + "\n",
    )


def case_eval_behavior_schema(complexity: str, index: str, scenario: str) -> dict:
    record = {
        "id": f"{scenario}-behavior",
        "prompt": f"Review {scenario}.",
        "source_kind": "synthetic",
        "source_url": "",
        "ip_handling": "original synthetic prompt; no third-party text",
        "contains_third_party_text": False,
    }
    return case_with_eval_file(
        "SAC-EVAL-BEHAVIOR-SCHEMA", complexity, index, scenario,
        description=f"Use when checking {scenario} behavior eval schema.",
        eval_filename="behavior-cases.jsonl",
        content=json.dumps(record, separators=(",", ":")) + "\n",
    )


def case_eval_ip_hygiene(complexity: str, index: str, scenario: str) -> dict:
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
    return case_with_eval_file(
        "SAC-EVAL-IP-HYGIENE", complexity, index, scenario,
        description=f"Use when checking {scenario} eval IP handling.",
        eval_filename="trigger-cases.jsonl",
        content="\n".join(json.dumps(record, separators=(",", ":")) for record in (unsafe, safe)) + "\n",
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


def case_runtime_name_drift(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    return bare_case(
        "SAC-RUNTIME-NAME-DRIFT", complexity, scenario,
        files=[
            {
                "path": f"example-plugin/skills/{name}/SKILL.md",
                "content": skill_doc("different-name", f"Use when checking {scenario} skill-name parity.", clean_body(scenario)),
            }
        ],
    )


def case_runtime_plugin_json(complexity: str, index: str, scenario: str) -> dict:
    return bare_case(
        "SAC-RUNTIME-PLUGIN-JSON", complexity, scenario,
        files=[
            {"path": ".claude-plugin/marketplace.json", "content": f"{{\"plugins\":[{{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}]}}\n"},
            {"path": "example-plugin/.claude-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"description\":\"{scenario}\",\n"}],
    )


def case_manifest_sync(complexity: str, index: str, scenario: str) -> dict:
    # Marketplace entry deliberately carries no "version" key (plugin.json is the
    # sole authority) so this fixture isolates description drift; a marketplace
    # entry that carries a version key at all is its own gold case, see
    # build_guard_cases()'s "marketplace-entry-carries-version-key".
    return bare_case(
        "SAC-RUNTIME-MANIFEST-SYNC", complexity, scenario,
        files=[
            {"path": ".claude-plugin/marketplace.json", "content": f"{{\"plugins\":[{{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"description\":\"Marketplace {scenario}\"}}]}}\n"},
            {"path": "example-plugin/.claude-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Claude {scenario}\"}}\n"},
        ],
    )


def case_missing_claude_agent(complexity: str, index: str, scenario: str) -> dict:
    return skill_case("SAC-RUNTIME-MISSING-CLAUDE-AGENT", complexity, index, scenario, f"Use when checking {scenario} Claude subagent presence.", clean_body(scenario), omit_claude_agent=True)


def case_agent_desc_drift(complexity: str, index: str, scenario: str) -> dict:
    return case_with_agent_file(
        "SAC-RUNTIME-AGENT-DESC-DRIFT", complexity, index, scenario,
        description=f"Use when checking {scenario} subagent description sync.",
        agent_content=f"---\nname: {scenario}-skill\ndescription: Different {scenario} description.\ntools: Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n",
    )


def case_missing_claude_manifest(complexity: str, index: str, scenario: str) -> dict:
    return bare_case(
        "SAC-RUNTIME-MISSING-CLAUDE-MANIFEST", complexity, scenario,
        files=[
            {"path": ".claude-plugin/marketplace.json", "content": f"{{\"plugins\":[{{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}]}}\n"},
        ],
    )


def case_marketplace_missing_entry(complexity: str, index: str, scenario: str) -> dict:
    return bare_case(
        "SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY", complexity, scenario,
        files=[
            {"path": ".claude-plugin/marketplace.json", "content": "{\"plugins\":[]}\n"},
            {"path": "example-plugin/.claude-plugin/plugin.json", "content": f"{{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin {scenario}\"}}\n"},
        ],
    )


def case_agent_name_drift(complexity: str, index: str, scenario: str) -> dict:
    return case_with_agent_file(
        "SAC-RUNTIME-CLAUDE-AGENT-NAME-DRIFT", complexity, index, scenario,
        description=f"Use when checking {scenario} Claude agent name sync.",
        agent_content=f"---\nname: different-{scenario}\ndescription: Use when checking {scenario} Claude agent name sync.\ntools: Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n",
    )


def case_agent_missing_skill_tool(complexity: str, index: str, scenario: str) -> dict:
    return case_with_agent_file(
        "SAC-RUNTIME-CLAUDE-AGENT-MISSING-SKILL-TOOL", complexity, index, scenario,
        description=f"Use when checking {scenario} Claude agent tool access.",
        agent_content=f"---\nname: {scenario}-skill\ndescription: Use when checking {scenario} Claude agent tool access.\ntools: Read, Edit\nmodel: sonnet\n---\n\nInvoke the skill.\n",
    )


def case_runtime_bundled_script_var(complexity: str, index: str, scenario: str) -> dict:
    name = f"{scenario}-skill"
    body = clean_body(scenario) + (
        "\nResolve the bundled checker from the skill directory before reporting:\n\n"
        "```bash\n"
        'bash "$SKILL_DIR"/references/scripts/check.sh --strict\n'
        "```\n"
    )
    return skill_case(
        "SAC-RUNTIME-BUNDLED-SCRIPT-VAR",
        complexity,
        index,
        scenario,
        f"Use when checking {scenario} bundled-script path substitution.",
        body,
        skill_name=name,
        expected_findings=[
            {
                "code": "SAC-RUNTIME-BUNDLED-SCRIPT-VAR",
                "path": f"example-plugin/skills/{name}/SKILL.md",
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
    ("private-plugin-root-reference", case_ref_private_plugin_root),
    ("unadvertised-script", case_script_unadvertised),
    ("unadvertised-fixture", case_fixture_unadvertised),
    ("unadvertised-template", case_template_unadvertised),
    ("unadvertised-asset", case_asset_unadvertised),
    ("hidden-eval-artifact", case_eval_hidden_artifact),
    ("trigger-eval-schema", case_eval_trigger_schema),
    ("behavior-eval-schema", case_eval_behavior_schema),
    ("eval-ip-hygiene", case_eval_ip_hygiene),
    ("rationalization-gate", case_rationalization_gate),
    ("skill-name-drift", case_runtime_name_drift),
    ("invalid-plugin-json", case_runtime_plugin_json),
    ("manifest-sync", case_manifest_sync),
    ("missing-claude-agent", case_missing_claude_agent),
    ("agent-desc-drift", case_agent_desc_drift),
    ("missing-claude-manifest", case_missing_claude_manifest),
    ("missing-marketplace-entry", case_marketplace_missing_entry),
    ("agent-name-drift", case_agent_name_drift),
    ("agent-missing-skill-tool", case_agent_missing_skill_tool),
    ("missing-entrypoint", case_doc_missing_entrypoint),
    ("bundled-script-var", case_runtime_bundled_script_var),
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
            "guard-pycache-not-support",
            "Inputs: files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nRead references/tool-notes.md when tooling behavior is in scope.\n",
            ["SAC-REF-UNADVERTISED-SUPPORT"],
            "regenerated bytecode caches are environment noise, not unadvertised support",
            extra_files=[
                {"path": "example-plugin/skills/guard-pycache-not-support-skill/references/tool-notes.md", "content": "# Tool notes\n"},
                {"path": "example-plugin/skills/guard-pycache-not-support-skill/references/__pycache__/helper.cpython-311.pyc", "content": "fake bytecode placeholder\n"},
            ],
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
            "guard-shared-plugin-root-reference",
            "Inputs: files.\nEvidence: cite files.\nOutput: report.\nIf ambiguous, ask the user.\nStop when complete.\nRerun validation after edits.\nRead ../../references/shared-guidance/check.md when shared plugin guidance applies.\n",
            ["SAC-REF-PRIVATE-PLUGIN-ROOT"],
            "documented shared plugin-root reference is allowed",
            extra_files=[
                {
                    "path": "example-plugin/references/README.md",
                    "content": "# Plugin References\n\n`shared-guidance/check.md` is shared plugin-level canonical guidance for all skills.\n",
                },
                {
                    "path": "example-plugin/references/shared-guidance/check.md",
                    "content": "# Shared Guidance\n",
                },
            ],
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
            "guard-marketplace-complete",
            [
                {"path": ".claude-plugin/marketplace.json", "content": "{\"plugins\":[{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"description\":\"Fixture plugin\"}]}\n"},
                {"path": "example-plugin/.claude-plugin/plugin.json", "content": "{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\"}\n"},
            ],
            [
                "SAC-RUNTIME-MANIFEST-SYNC",
                "SAC-RUNTIME-MISSING-CLAUDE-MANIFEST",
                "SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY",
            ],
            "complete marketplace and plugin manifests avoid runtime parity findings",
        ),
        bare_case(
            "SAC-RUNTIME-MANIFEST-SYNC",
            "adversarial",
            "marketplace-entry-carries-version-key",
            files=[
                {"path": ".claude-plugin/marketplace.json", "content": "{\"plugins\":[{\"name\":\"example-plugin\",\"source\":\"./example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\"}]}\n"},
                {"path": "example-plugin/.claude-plugin/plugin.json", "content": "{\"name\":\"example-plugin\",\"version\":\"1.0.0\",\"description\":\"Fixture plugin\"}\n"},
            ],
        ),
        guard_skill(
            "guard-established-skill-dir-alias",
            clean_body("guard-established-skill-dir-alias")
            + (
                "\nThe skill directory is `${CLAUDE_SKILL_DIR}`; use it wherever a "
                'bundled-script command shows `"$SKILL_DIR"`.\n\n'
                "```bash\n"
                'bash "$SKILL_DIR"/references/scripts/check.sh --strict\n'
                "```\n"
            ),
            ["SAC-RUNTIME-BUNDLED-SCRIPT-VAR"],
            "skill-dir alias established from CLAUDE_SKILL_DIR is not a bare-variable regression",
        ),
        case_runtime_wrapper_workflow_duplication(
            "adversarial",
            "guard",
            "runtime-wrapper-duplicates-workflow",
        ),
        guard_skill(
            "guard-adjectival-load-opener",
            clean_body("guard-adjectival-load-opener")
            + (
                "\nRead-only pass: inspect references/gallery-notes.md output.\n"
                "Load balancer notes live in references/topology-notes.md today.\n"
                "Open source attribution sits in references/licence-notes.md here.\n"
                "Read replica guidance sits in references/db-notes.md now.\n"
            ),
            ["SAC-REF-UNCONDITIONAL-LOAD", "SAC-REF-UNADVERTISED-SUPPORT"],
            "adjectival read-/load-/open- compound opener next to a bundled path is not an unconditional support load",
            extra_files=[
                {"path": "example-plugin/skills/guard-adjectival-load-opener-skill/references/gallery-notes.md", "content": "# Gallery notes\n"},
                {"path": "example-plugin/skills/guard-adjectival-load-opener-skill/references/topology-notes.md", "content": "# Topology notes\n"},
                {"path": "example-plugin/skills/guard-adjectival-load-opener-skill/references/licence-notes.md", "content": "# Licence notes\n"},
                {"path": "example-plugin/skills/guard-adjectival-load-opener-skill/references/db-notes.md", "content": "# DB notes\n"},
            ],
        ),
        guard_skill(
            "guard-and-stop-terminal",
            "Inputs: repository files.\n"
            "Evidence: cite files and commands.\n"
            "Output: report.\n"
            "Clarify scope with the requester when the request is ambiguous.\n"
            "Finish the checks and stop.\n"
            "Rerun validation after edits.\n",
            ["SAC-WORKFLOW-STOP-CONDITIONS"],
            "and-stop terminal phrasing satisfies the stop-condition contract",
        ),
        guard_skill(
            "guard-safe-default-arm",
            "Inputs: repository files.\n"
            "Evidence: cite files and commands.\n"
            "Output: report.\n"
            "Stop when complete.\n"
            "If you are unsure, take the documented default.\n"
            "Rerun validation after edits.\n",
            ["SAC-WORKFLOW-ASK-CONTINUE"],
            "if-unsure safe-default arm satisfies the ask-vs-continue contract",
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
