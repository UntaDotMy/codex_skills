from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tests.parallel_contract_test_runner import (
    discover_contract_test_targets,
    resolve_parallel_worker_limit,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT_PATH = REPOSITORY_ROOT / "sync-skills.sh"
SKILL_DIRECTORIES = sorted(
    path for path in REPOSITORY_ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").exists()
)
SCENARIO_HEADINGS = (
    "Real-World Scenarios",
    "Real-World Failure Scenarios",
    "Real-World Review Scenarios",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_section_content(text: str, heading: str) -> str:
    lines = text.splitlines()
    collected_lines: list[str] = []
    in_section = False
    target_level = 0

    for line in lines:
        if line.startswith("#"):
            hashes, _, title = line.partition(" ")
            level = len(hashes)
            if not in_section and title == heading:
                in_section = True
                target_level = level
                continue
            if in_section and level <= target_level:
                break
        if in_section:
            collected_lines.append(line)

    return "\n".join(collected_lines).strip()


def prompt_word_count(yaml_text: str) -> int:
    match = re.search(r'^[ ]{2}default_prompt: "(.*)"$', yaml_text, flags=re.MULTILINE)
    if not match:
        raise AssertionError("default_prompt line missing")
    return len(match.group(1).split())


def write_sync_script_without_main(temp_directory: Path) -> Path:
    sync_text = read_text(SYNC_SCRIPT_PATH)
    sync_text = sync_text.replace(
        'bootstrap_delegate_if_needed "$@"\nrefresh_bootstrap_entry_script_from_repo\n\n',
        "",
    )
    sync_text = sync_text.replace('bootstrap_delegate_if_needed "$@"\n\n', "")
    if 'main "$@"' not in sync_text:
        raise AssertionError('sync-skills.sh main invocation missing')
    sync_text = sync_text.rsplit('main "$@"', 1)[0].rstrip() + "\n"
    sourced_script_path = temp_directory / "sync-skills.no-main.sh"
    sourced_script_path.write_text(sync_text, encoding="utf-8")
    return sourced_script_path


def run_bash(
    command: str,
    environment: dict[str, str] | None = None,
    working_directory: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    runtime_environment = os.environ.copy()
    runtime_environment.update(environment or {})
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=working_directory or REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=runtime_environment,
    )


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text).replace("\r", "")


def current_repository_branch() -> str:
    completed_process = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed_process.returncode != 0:
        raise AssertionError(completed_process.stdout + completed_process.stderr)
    current_branch = completed_process.stdout.strip()
    if current_branch:
        return current_branch

    fallback_process = subprocess.run(
        [
            "git",
            "-C",
            str(REPOSITORY_ROOT),
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if fallback_process.returncode != 0:
        raise AssertionError(fallback_process.stdout + fallback_process.stderr)
    fallback_branch = next((line.strip() for line in fallback_process.stdout.splitlines() if line.strip()), "")
    if not fallback_branch:
        raise AssertionError("No local git branch is available for bootstrap clone tests.")
    return fallback_branch


def create_bootstrap_source_repository(parent_directory: Path) -> Path:
    bootstrap_source_path = parent_directory / "bootstrap-source"
    shutil.copytree(
        REPOSITORY_ROOT,
        bootstrap_source_path,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    commit_environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Codex Test",
        "GIT_AUTHOR_EMAIL": "codex-test@example.com",
        "GIT_COMMITTER_NAME": "Codex Test",
        "GIT_COMMITTER_EMAIL": "codex-test@example.com",
    }
    branch_name = current_repository_branch()

    init_process = subprocess.run(
        ["git", "init", str(bootstrap_source_path)],
        check=False,
        capture_output=True,
        text=True,
        env=commit_environment,
    )
    if init_process.returncode != 0:
        raise AssertionError(init_process.stdout + init_process.stderr)

    checkout_process = subprocess.run(
        ["git", "-C", str(bootstrap_source_path), "checkout", "-b", branch_name],
        check=False,
        capture_output=True,
        text=True,
        env=commit_environment,
    )
    if checkout_process.returncode != 0:
        raise AssertionError(checkout_process.stdout + checkout_process.stderr)

    add_process = subprocess.run(
        ["git", "-C", str(bootstrap_source_path), "add", "--all"],
        check=False,
        capture_output=True,
        text=True,
        env=commit_environment,
    )
    if add_process.returncode != 0:
        raise AssertionError(add_process.stdout + add_process.stderr)

    commit_process = subprocess.run(
        ["git", "-C", str(bootstrap_source_path), "commit", "-m", "bootstrap snapshot"],
        check=False,
        capture_output=True,
        text=True,
        env=commit_environment,
    )
    if commit_process.returncode != 0:
        raise AssertionError(commit_process.stdout + commit_process.stderr)

    return bootstrap_source_path


class SkillPackContractTests(unittest.TestCase):
    def test_every_skill_declares_use_this_skill_when(self) -> None:
        missing_sections: list[str] = []
        weak_sections: list[str] = []

        for skill_directory in SKILL_DIRECTORIES:
            skill_text = read_text(skill_directory / "SKILL.md")
            if "## Use This Skill When" not in skill_text:
                missing_sections.append(skill_directory.name)
                continue
            bullet_count = len(
                re.findall(r"(?m)^- ", markdown_section_content(skill_text, "Use This Skill When"))
            )
            if bullet_count < 3:
                weak_sections.append(skill_directory.name)

        self.assertEqual([], missing_sections, f"missing Use This Skill When: {missing_sections}")
        self.assertEqual([], weak_sections, f"weak Use This Skill When sections: {weak_sections}")

    def test_every_skill_has_real_world_scenarios(self) -> None:
        missing_sections: list[str] = []
        weak_sections: list[str] = []

        for skill_directory in SKILL_DIRECTORIES:
            skill_text = read_text(skill_directory / "SKILL.md")
            matching_heading = next(
                (heading for heading in SCENARIO_HEADINGS if f"## {heading}" in skill_text),
                None,
            )
            if matching_heading is None:
                missing_sections.append(skill_directory.name)
                continue
            bullet_count = len(
                re.findall(r"(?m)^- ", markdown_section_content(skill_text, matching_heading))
            )
            if bullet_count < 2:
                weak_sections.append(skill_directory.name)

        self.assertEqual([], missing_sections, f"missing scenario sections: {missing_sections}")
        self.assertEqual([], weak_sections, f"weak scenario sections: {weak_sections}")

    def test_ui_and_ux_ownership_boundaries_are_explicit(self) -> None:
        ui_text = read_text(
            REPOSITORY_ROOT / "ui-design-systems-and-responsive-interfaces" / "SKILL.md"
        )
        ux_text = read_text(
            REPOSITORY_ROOT / "ux-research-and-experience-strategy" / "SKILL.md"
        )
        routing_text = read_text(REPOSITORY_ROOT / "00-skill-routing-and-escalation.md")

        self.assertIn("## UI and UX Ownership Boundary", ui_text)
        self.assertIn("UI owns", ui_text)
        self.assertIn("UX owns", ui_text)
        self.assertIn("## UX and UI Ownership Boundary", ux_text)
        self.assertIn("UX owns", ux_text)
        self.assertIn("UI owns", ux_text)
        self.assertIn("only one skill owns the final synthesis", routing_text)

    def test_meta_skills_do_not_implicitly_shadow_domain_skills(self) -> None:
        expected_false = {
            "reviewer",
            "software-development-life-cycle",
            "memory-status-reporter",
            "git-expert",
        }

        for skill_directory in SKILL_DIRECTORIES:
            yaml_text = read_text(skill_directory / "agents" / "openai.yaml")
            expected_value = "false" if skill_directory.name in expected_false else "true"
            self.assertIn(
                f"allow_implicit_invocation: {expected_value}",
                yaml_text,
                f"unexpected implicit policy for {skill_directory.name}",
            )

    def test_default_prompts_stay_compact(self) -> None:
        over_limit: list[str] = []

        for skill_directory in SKILL_DIRECTORIES:
            yaml_text = read_text(skill_directory / "agents" / "openai.yaml")
            prompt_match = re.search(r'^[ ]{2}default_prompt: "(.*)"$', yaml_text, flags=re.MULTILINE)
            if prompt_match is None:
                over_limit.append(skill_directory.name)
                continue
            if prompt_word_count(yaml_text) > 260 or len(prompt_match.group(1)) > 1600:
                over_limit.append(skill_directory.name)

        self.assertEqual([], over_limit, f"overlong prompts: {over_limit}")

    def test_agent_prompts_keep_cache_handoff_and_autonomy_guidance(self) -> None:
        missing_cache_guidance: list[str] = []
        missing_autonomy_guidance: list[str] = []
        missing_handoff_guidance: list[str] = []
        missing_scope_guidance: list[str] = []
        missing_interrupt_guidance: list[str] = []
        missing_clarification_guidance: list[str] = []
        missing_staffing_guidance: list[str] = []
        missing_plan_breakdown_guidance: list[str] = []
        missing_reconciliation_guidance: list[str] = []
        missing_no_soft_stop_guidance: list[str] = []
        missing_honesty_guidance: list[str] = []
        missing_parallel_work_guidance: list[str] = []
        missing_js_repl_only_guidance: list[str] = []

        for skill_directory in SKILL_DIRECTORIES:
            yaml_text = read_text(skill_directory / "agents" / "openai.yaml")
            if "freshness-aware research cache" not in yaml_text:
                missing_cache_guidance.append(skill_directory.name)
            if "keep iterating in the same turn" not in yaml_text:
                missing_autonomy_guidance.append(skill_directory.name)
            if "reuse the same-role agent" not in yaml_text or "keep the handoff bounded" not in yaml_text:
                missing_handoff_guidance.append(skill_directory.name)
            if "workspace-scoped memory" not in yaml_text:
                missing_scope_guidance.append(skill_directory.name)
            if "interrupt=true" not in yaml_text:
                missing_interrupt_guidance.append(skill_directory.name)
            if "request_user_input" not in yaml_text:
                missing_clarification_guidance.append(skill_directory.name)
            if "do not stay solo by default" not in yaml_text:
                missing_staffing_guidance.append(skill_directory.name)
            if "one top-level plan item per explicit user task, with a short per-item breakdown" not in yaml_text:
                missing_plan_breakdown_guidance.append(skill_directory.name)
            if "explicit user requirement" not in yaml_text or "do not present unresolved work as complete" not in yaml_text:
                missing_reconciliation_guidance.append(skill_directory.name)
            if "status requests are checkpoints, not stop signals" not in yaml_text:
                missing_no_soft_stop_guidance.append(skill_directory.name)
            if "State what is verified, inferred, and still blocked or unvalidated" not in yaml_text:
                missing_honesty_guidance.append(skill_directory.name)
            if "keep doing non-conflicting local work instead of idling" not in yaml_text:
                missing_parallel_work_guidance.append(skill_directory.name)
            if "Route tool work through js_repl with codex.tool(...)." not in yaml_text:
                missing_js_repl_only_guidance.append(skill_directory.name)

        self.assertEqual([], missing_cache_guidance, f"missing cache guidance: {missing_cache_guidance}")
        self.assertEqual([], missing_autonomy_guidance, f"missing autonomy guidance: {missing_autonomy_guidance}")
        self.assertEqual([], missing_handoff_guidance, f"missing handoff guidance: {missing_handoff_guidance}")
        self.assertEqual([], missing_scope_guidance, f"missing scope guidance: {missing_scope_guidance}")
        self.assertEqual([], missing_interrupt_guidance, f"missing interrupt guidance: {missing_interrupt_guidance}")
        self.assertEqual([], missing_clarification_guidance, f"missing clarification guidance: {missing_clarification_guidance}")
        self.assertEqual([], missing_staffing_guidance, f"missing staffing guidance: {missing_staffing_guidance}")
        self.assertEqual([], missing_plan_breakdown_guidance, f"missing plan breakdown guidance: {missing_plan_breakdown_guidance}")
        self.assertEqual([], missing_reconciliation_guidance, f"missing reconciliation guidance: {missing_reconciliation_guidance}")
        self.assertEqual([], missing_no_soft_stop_guidance, f"missing no-soft-stop guidance: {missing_no_soft_stop_guidance}")
        self.assertEqual([], missing_honesty_guidance, f"missing honesty guidance: {missing_honesty_guidance}")
        self.assertEqual([], missing_parallel_work_guidance, f"missing parallel work guidance: {missing_parallel_work_guidance}")
        self.assertEqual([], missing_js_repl_only_guidance, f"missing js_repl guidance: {missing_js_repl_only_guidance}")

        reviewer_agent_text = read_text(REPOSITORY_ROOT / "reviewer" / "agents" / "openai.yaml")
        software_agent_text = read_text(
            REPOSITORY_ROOT / "software-development-life-cycle" / "agents" / "openai.yaml"
        )
        self.assertIn("named surface", reviewer_agent_text)
        self.assertIn("validated patch batches", reviewer_agent_text)
        self.assertIn("workaround-only", reviewer_agent_text)
        self.assertIn("named scope", software_agent_text)
        self.assertIn("patch batch", software_agent_text)

    def test_core_guidance_requires_completion_reconciliation_and_agent_lanes(self) -> None:
        root_guidance_text = read_text(REPOSITORY_ROOT / "AGENTS.md")
        routing_text = read_text(REPOSITORY_ROOT / "00-skill-routing-and-escalation.md")
        readme_text = read_text(REPOSITORY_ROOT / "README.md")

        self.assertIn("Completion Reconciliation Loop", root_guidance_text)
        self.assertIn("every explicit user requirement", root_guidance_text)
        self.assertIn("completion_gate.py", root_guidance_text)
        self.assertIn("do not end with optional follow-up offers", root_guidance_text)
        self.assertIn("does not suspend execution when fixable in-scope work remains", root_guidance_text)
        self.assertIn("do not stay solo by default", root_guidance_text)
        self.assertIn("one top-level plan item per explicit user task", root_guidance_text)
        self.assertIn("workstreams/<workstream-key>", root_guidance_text)
        self.assertIn("instances/<agent-instance>", root_guidance_text)
        self.assertIn("readiness or ACK check", root_guidance_text)
        self.assertIn("old completed payload", root_guidance_text)
        self.assertIn("raw HTML or HTTP 4xx or 5xx content", root_guidance_text)
        self.assertIn("WAL Protocol", root_guidance_text)
        self.assertIn("working-buffer.md", root_guidance_text)
        self.assertIn("Trim Protocol", root_guidance_text)
        self.assertIn("Recalibrate Protocol", root_guidance_text)
        self.assertIn("Prompt Injection Defense", root_guidance_text)
        self.assertIn("External Content Security", root_guidance_text)
        self.assertIn("Cross-Platform Script Portability", root_guidance_text)
        self.assertIn("what is verified, what is inferred, and what remains blocked", root_guidance_text)
        self.assertIn("local-home-agent-overrides.json", root_guidance_text)
        self.assertIn("gpt-5.4", root_guidance_text)
        self.assertIn('reasoning_effort: "low"', root_guidance_text)
        self.assertIn("written explicitly for the managed lanes", root_guidance_text)
        self.assertIn("~/.codex/agent-profiles/*.toml", root_guidance_text)
        self.assertIn("12 skill-owned agent profiles", root_guidance_text)
        self.assertIn("delegate the durable write to the `memory-status-reporter` lane", root_guidance_text)
        self.assertIn("Named Scope First", root_guidance_text)
        self.assertIn("small, batch-sized patches", root_guidance_text)
        self.assertIn("fake completion or workaround-only delivery", root_guidance_text)
        self.assertIn("Avoid first-person and second-person pronouns", root_guidance_text)
        self.assertIn("Never hardcode runtime values", root_guidance_text)
        self.assertIn("Hold the final output until the closing check is explicit", root_guidance_text)
        self.assertIn("staged rollout doctrine", root_guidance_text)
        self.assertIn("generic-looking UI repair", root_guidance_text)
        self.assertIn("journey friction", root_guidance_text)
        self.assertNotIn("responsible for writing the durable memory update", root_guidance_text)
        self.assertIn("Requirement Reconciliation Before Close", routing_text)
        self.assertIn("Use A Completion Ledger For Real Closure", routing_text)
        self.assertIn("completion_gate.py check", routing_text)
        self.assertIn("Status Requests Do Not End The Job", routing_text)
        self.assertIn("Honor The Named Scope First", routing_text)
        self.assertIn("Small Validated Batches Beat Huge Rewrites", routing_text)
        self.assertIn("Real Solutions Over Plausible Workarounds", routing_text)
        self.assertIn("Anchor handoffs to the user story and named scope", routing_text)
        self.assertIn("Use Solo Mode Deliberately", routing_text)
        self.assertIn("Planning Defaults", routing_text)
        self.assertIn("Do Not Ship Hardcoded Runtime Decisions", routing_text)
        self.assertIn("Hold Final Synthesis Until Closure Checks Pass", routing_text)
        self.assertIn("issue-driven Git delivery", routing_text)
        self.assertIn("traffic-shift method", routing_text)
        self.assertIn("agent-instance lane", routing_text)
        self.assertIn("Write Corrections Before Responding", routing_text)
        self.assertIn("let that lane report what changed", routing_text)
        self.assertIn("Resolve workspace-scoped memory first", routing_text)
        self.assertIn("do not front-load **reviewer** as routine triage", routing_text)
        self.assertIn("what is verified, what is inferred, and what remains blocked", routing_text)
        self.assertIn("Completion Reconciliation", readme_text)
        self.assertIn("completion-gate.json", readme_text)
        self.assertIn("not permission to stop", readme_text)
        self.assertIn("do not stay solo by default", readme_text)
        self.assertIn("top-level plan item per explicit user task", readme_text)
        self.assertIn("runtime-guardrails-and-memory-protocols.md", readme_text)
        self.assertIn("open-source-memory-patterns.md", readme_text)
        self.assertIn("security-audit-status.md", readme_text)
        self.assertIn("Git Bash on Windows", readme_text)
        self.assertIn("do not call tools directly", readme_text.lower())
        self.assertIn("local-home-agent-overrides.json", readme_text)
        self.assertIn("agent-profiles/*.toml", readme_text)
        self.assertIn("skill agent profiles: 12/12", readme_text)
        self.assertIn("let it act as the memory writer", readme_text)
        self.assertIn("seeds and preserves", readme_text)
        self.assertIn("prunes runtime-noise artifacts", readme_text)
        self.assertIn("Honor the named scope", readme_text)
        self.assertIn("Small validated batches", readme_text)
        self.assertIn("Pair UI Output With UX Evidence", readme_text)
        self.assertIn("issue-driven worktree", readme_text)
        self.assertIn("Hold the answer until closure is proven", readme_text)
        self.assertIn("handoff packets small, scope-true, and validation-aware", readme_text)
        validation_report_text = read_text(REPOSITORY_ROOT / "VALIDATION_REPORT.md")
        self.assertIn(
            "home-agent and agent-profile TOMLs are now written explicitly as `gpt-5.4` with `medium` reasoning by default",
            validation_report_text,
        )
        self.assertNotIn(
            "Repo-managed skill agents now inherit the workspace model and reasoning baseline",
            validation_report_text,
        )

    def test_runtime_guardrails_capture_working_buffer_threshold_and_bounded_self_improvement(self) -> None:
        runtime_guardrails_text = read_text(
            REPOSITORY_ROOT / "docs" / "runtime-guardrails-and-memory-protocols.md"
        )
        memory_status_skill_text = read_text(
            REPOSITORY_ROOT / "memory-status-reporter" / "SKILL.md"
        )
        open_source_memory_text = read_text(
            REPOSITORY_ROOT / "docs" / "open-source-memory-patterns.md"
        )

        self.assertIn("roughly 60 percent context usage", runtime_guardrails_text)
        self.assertIn("Bounded Self-Improvement", runtime_guardrails_text)
        self.assertIn("not hidden model retraining", runtime_guardrails_text)
        self.assertIn("octave-mcp", runtime_guardrails_text)
        self.assertIn("roughly 60 percent usage", memory_status_skill_text)
        self.assertIn("self-awareness, self-healing, self-training, and self-learning", memory_status_skill_text)
        self.assertIn("Mirror the user's", open_source_memory_text)
        self.assertIn("runtime-aware heuristic", open_source_memory_text)

    def test_core_guidance_requires_lifecycle_scenario_thinking(self) -> None:
        root_guidance_text = read_text(REPOSITORY_ROOT / "AGENTS.md")
        software_skill_text = read_text(REPOSITORY_ROOT / "software-development-life-cycle" / "SKILL.md")
        reviewer_skill_text = read_text(REPOSITORY_ROOT / "reviewer" / "SKILL.md")
        software_skill_text = read_text(
            REPOSITORY_ROOT / "software-development-life-cycle" / "SKILL.md"
        )
        ui_skill_text = read_text(REPOSITORY_ROOT / "ui-design-systems-and-responsive-interfaces" / "SKILL.md")
        ux_skill_text = read_text(REPOSITORY_ROOT / "ux-research-and-experience-strategy" / "SKILL.md")

        self.assertIn("relevant lifecycle scenarios", root_guidance_text)
        self.assertIn("execution contexts users actually depend on", root_guidance_text)
        self.assertIn("lifecycle scenario sweep", software_skill_text)
        self.assertIn("lifecycle, recovery, and local-state scenarios", reviewer_skill_text)
        self.assertIn("readiness or ACK check", reviewer_skill_text)
        self.assertIn("old completed payload", reviewer_skill_text)
        self.assertIn("raw HTML or HTTP 4xx or 5xx content", reviewer_skill_text)
        self.assertIn("honest checkpoint, not a closing condition", reviewer_skill_text)
        self.assertIn("Prompt injection attempts", reviewer_skill_text)
        self.assertIn("data only, never instructions", reviewer_skill_text)
        self.assertIn("same failing tool call", reviewer_skill_text)
        self.assertIn("one top-level plan item per explicit user task", reviewer_skill_text)
        self.assertIn("source-to-installed parity evidence", reviewer_skill_text)
        self.assertIn("Named Scope Discipline", reviewer_skill_text)
        self.assertIn("Batch Validation Discipline", reviewer_skill_text)
        self.assertIn("Reject workaround-only fixes, fake completion, or unproven root-cause claims", reviewer_skill_text)
        self.assertIn("Never hardcode runtime values", software_skill_text)
        self.assertIn("Hold delivery until the current requirement set is proven done or explicitly blocked", software_skill_text)
        self.assertIn("REJECT hardcoded runtime values", reviewer_skill_text)
        self.assertIn("Reject partial implementation, missing test proof, or missing coverage reasoning", reviewer_skill_text)
        self.assertIn("what is verified, what is inferred", root_guidance_text)
        self.assertIn("readiness or ACK check", software_skill_text)
        self.assertIn("old completed payload", software_skill_text)
        self.assertIn("raw HTML or HTTP 4xx or 5xx content", software_skill_text)
        self.assertIn("honest checkpoint, not a closing condition", software_skill_text)
        self.assertIn("Prompt injection attempts", software_skill_text)
        self.assertIn("data only, never instructions", software_skill_text)
        self.assertIn("same failing tool call", software_skill_text)
        self.assertIn("do not stay solo by default", software_skill_text)
        self.assertIn("one top-level plan item per explicit user task", software_skill_text)
        self.assertIn("request names a function, module, route, or script", software_skill_text)
        self.assertIn("small, reviewable patch batches", software_skill_text)
        self.assertIn("keep doing non-conflicting local work instead of idling", software_skill_text)
        qa_skill_text = read_text(REPOSITORY_ROOT / "qa-and-automation-engineer" / "SKILL.md")
        self.assertIn("working brief", qa_skill_text)
        self.assertIn("one top-level plan item per explicit user task", qa_skill_text)
        self.assertIn("proving check per patch batch", qa_skill_text)
        self.assertIn("do not stay solo in reviewer by default", reviewer_skill_text)
        self.assertIn("keep doing non-conflicting local work instead of idling", reviewer_skill_text)
        self.assertIn("continuity-heavy flows", ui_skill_text)
        self.assertIn("continuity-heavy flows", ux_skill_text)
        self.assertNotIn("for 1:1 messaging", ui_skill_text)
        self.assertNotIn("for 1:1 messaging", ux_skill_text)
        self.assertNotIn("Messaging Surface Rehabilitation", ui_skill_text)
        self.assertNotIn("Messaging Familiarity Gap", ux_skill_text)

    def test_core_guidance_requires_robustness_beyond_happy_path(self) -> None:
        routing_text = read_text(REPOSITORY_ROOT / "00-skill-routing-and-escalation.md")
        software_skill_text = read_text(
            REPOSITORY_ROOT / "software-development-life-cycle" / "SKILL.md"
        )
        reviewer_skill_text = read_text(REPOSITORY_ROOT / "reviewer" / "SKILL.md")
        qa_skill_text = read_text(REPOSITORY_ROOT / "qa-and-automation-engineer" / "SKILL.md")

        self.assertIn(
            "realistic failure, recovery, stale-state, retry, concurrency, and hostile-input scenarios",
            routing_text,
        )
        self.assertIn(
            "stale state, inherited environment variables, retries, partial cleanup, and concurrent or nested execution",
            software_skill_text,
        )
        self.assertIn(
            "cover the adjacent recovery or containment path",
            software_skill_text,
        )
        self.assertIn(
            "validated only on the happy path",
            reviewer_skill_text,
        )
        self.assertIn(
            "stale state, inherited environment, retries, cleanup ownership, concurrency, or hostile input",
            reviewer_skill_text,
        )
        self.assertIn(
            "happy path, failure path, recovery path, and one abuse or hostile-state path",
            qa_skill_text,
        )
        self.assertIn(
            "stale state, retries, env inheritance, partial cleanup, race conditions, or untrusted input",
            qa_skill_text,
        )

    def test_routing_docs_keep_reviewer_as_quality_gate_not_default_owner(self) -> None:
        routing_text = read_text(REPOSITORY_ROOT / "00-skill-routing-and-escalation.md")
        readme_text = read_text(REPOSITORY_ROOT / "README.md")

        self.assertIn("Final quality gate, not the default implementation owner", routing_text)
        self.assertNotIn("Final quality gate, DRY enforcement, orchestrator", routing_text)
        self.assertIn("quality gate, not the default implementation owner", readme_text)

    def test_reporting_rubric_prefers_scoped_memory_and_structured_rollout_matching(self) -> None:
        reporting_rubric_text = read_text(
            REPOSITORY_ROOT / "memory-status-reporter" / "references" / "reporting-rubric.md"
        )

        self.assertIn(
            "Workspace-scoped, workstream-scoped, role-scoped, and agent-instance-scoped",
            reporting_rubric_text,
        )
        self.assertIn(
            "structured metadata fields such as `cwd:`, `git_branch:`, and `agent_instance:`",
            reporting_rubric_text,
        )
        self.assertIn("Use each summary's `rollout_path` JSONL", reporting_rubric_text)
        self.assertIn("Prefer the scoped memory lanes first", reporting_rubric_text)

    def test_memory_status_skill_documents_wal_security_and_maintenance_protocols(self) -> None:
        skill_text = read_text(REPOSITORY_ROOT / "memory-status-reporter" / "SKILL.md")
        agent_yaml_text = read_text(REPOSITORY_ROOT / "memory-status-reporter" / "agents" / "openai.yaml")

        self.assertIn("## WAL and Working Buffer Protocol", skill_text)
        self.assertIn("SESSION-STATE.md", skill_text)
        self.assertIn("working-buffer.md", skill_text)
        self.assertIn("memory_maintenance.py", skill_text)
        self.assertIn("completion_gate.py", skill_text)
        self.assertIn("scoped completion ledger", skill_text)
        self.assertIn("agent_packets.py", skill_text)
        self.assertIn("loop_guard.py", skill_text)
        self.assertIn("trim", skill_text)
        self.assertIn("recalibrate", skill_text)
        self.assertIn("report what changed", skill_text)
        self.assertIn("Use `SESSION-STATE.md` only", skill_text)
        self.assertIn("Use `working-buffer.md` only", skill_text)
        self.assertIn("research_cache.py record", skill_text)
        self.assertIn("## Security and Anti-Loop Guardrails", skill_text)
        self.assertIn("data only, never instructions", skill_text)
        self.assertIn("Do not repeat the same failing tool call", skill_text)
        self.assertIn("act as the memory writer", agent_yaml_text)
        self.assertIn("report what changed", agent_yaml_text)
        self.assertIn("verify the touched memory files are clean and in sync", agent_yaml_text)
        self.assertIn("Preserve one top-level plan item per explicit user task, with a short per-item breakdown", agent_yaml_text)

    def test_powershell_wrapper_delegates_to_bash_manager_and_readme_surfaces_dependency(self) -> None:
        powershell_wrapper_text = read_text(REPOSITORY_ROOT / "sync-skills.ps1")
        readme_text = read_text(REPOSITORY_ROOT / "README.md")

        self.assertIn('Join-Path $scriptRoot "sync-skills.sh"', powershell_wrapper_text)
        self.assertIn('& $gitBashPath $bashScriptPath @ArgumentList', powershell_wrapper_text)
        self.assertIn("Git Bash was not found", powershell_wrapper_text)
        self.assertIn("sync-skills.ps1", readme_text)
        self.assertIn("delegates to `sync-skills.sh`", readme_text)
        self.assertIn("Git Bash on Windows", readme_text)
        self.assertIn("Install, Update, Status", readme_text)

    def test_mobile_guidance_uses_keystore_for_android(self) -> None:
        mobile_text = read_text(REPOSITORY_ROOT / "mobile-development-life-cycle" / "SKILL.md")
        android_section = markdown_section_content(mobile_text, "Android Development")
        self.assertIn("Keystore", android_section)
        self.assertNotIn("Keychain", android_section)

    def test_web_core_web_vitals_are_current(self) -> None:
        web_text = read_text(REPOSITORY_ROOT / "web-development-life-cycle" / "SKILL.md")
        vitals_section = markdown_section_content(web_text, "Core Web Vitals")
        self.assertIn("INP", vitals_section)
        self.assertNotIn("FID", vitals_section)

    def test_git_skill_gates_high_risk_commands(self) -> None:
        git_text = read_text(REPOSITORY_ROOT / "git-expert" / "SKILL.md")
        git_agent_text = read_text(REPOSITORY_ROOT / "git-expert" / "agents" / "openai.yaml")
        essential_commands = markdown_section_content(git_text, "Essential Git Commands")
        high_risk_section = markdown_section_content(
            git_text, "High-Risk Operations (Explicit User Approval Only)"
        )

        self.assertNotRegex(
            essential_commands,
            r"git rebase -i|git reset --hard|git checkout -- <file>|git filter-branch",
        )
        self.assertIn("configured Git `user.name` and `user.email`", git_text)
        self.assertIn("configured Git author identity", git_agent_text)
        self.assertIn("git config user.name", git_agent_text)
        self.assertIn("git config user.email", git_agent_text)
        self.assertIn("Issue-Driven Worktree Flow", git_text)
        self.assertIn("git worktree add", git_text)
        self.assertIn("feature-by-feature", git_text)
        self.assertIn("clean", git_text)
        self.assertIn("CI and CD", git_text)
        self.assertIn("issue-driven worktree", git_agent_text)
        self.assertIn("CI/CD-gated PRs", git_agent_text)
        self.assertIn("sensitive data leakage", git_agent_text)
        self.assertIn("explicit user approval", high_risk_section)
        self.assertIn("git reset --hard", high_risk_section)
        self.assertIn("git rebase -i", high_risk_section)

    def test_cloud_ui_and_ux_quality_doctrine_is_enforced(self) -> None:
        cloud_text = read_text(REPOSITORY_ROOT / "cloud-and-devops-expert" / "SKILL.md")
        cloud_agent_text = read_text(
            REPOSITORY_ROOT / "cloud-and-devops-expert" / "agents" / "openai.yaml"
        )
        ui_text = read_text(
            REPOSITORY_ROOT / "ui-design-systems-and-responsive-interfaces" / "SKILL.md"
        )
        ui_agent_text = read_text(
            REPOSITORY_ROOT
            / "ui-design-systems-and-responsive-interfaces"
            / "agents"
            / "openai.yaml"
        )
        ux_text = read_text(REPOSITORY_ROOT / "ux-research-and-experience-strategy" / "SKILL.md")
        ux_agent_text = read_text(
            REPOSITORY_ROOT / "ux-research-and-experience-strategy" / "agents" / "openai.yaml"
        )

        self.assertIn("Deployment Stage and Adversarial Readiness", cloud_text)
        for required_phrase in [
            "alpha",
            "beta",
            "canary",
            "release",
            "blue-green",
            "load-balancer traffic shifting",
            "red-team",
            "blue-team",
            "Evidence Gate",
        ]:
            self.assertIn(required_phrase, cloud_text)
        self.assertIn("red-team versus blue-team", cloud_agent_text)
        self.assertIn("load-balancer behavior", cloud_agent_text)
        self.assertIn("rollback owner", cloud_agent_text)
        self.assertIn("abort signal", cloud_agent_text)

        self.assertIn("Flow Proof and Quality Checks", ui_text)
        self.assertIn("brownfield work stays targeted", ui_text)
        self.assertIn("implementation-ready summary", ui_text)
        self.assertIn("Benchmark 2-3 mature product-family surfaces", ui_agent_text)
        self.assertIn("brownfield changes targeted", ui_agent_text)
        self.assertIn("hardcoded design values", ui_agent_text)
        self.assertIn("implementation-ready", ui_agent_text)

        self.assertIn("Experience Quality Proof", ux_text)
        self.assertIn("benchmark 2-3 mature flows", ux_text)
        self.assertIn("targeted to the named journey step", ux_text)
        self.assertIn("completion note", ux_text)
        self.assertIn("Benchmark 2-3 mature flows", ux_agent_text)
        self.assertIn("brownfield changes targeted", ux_agent_text)
        self.assertIn("hardcoded assumptions", ux_agent_text)
        self.assertIn("completion note", ux_agent_text)
        self.assertIn("live testing", ux_agent_text)

    def test_sync_heading_helper_detects_real_world_review_section(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                f'markdown_first_matching_heading "{REPOSITORY_ROOT / "reviewer" / "SKILL.md"}" '
                '"Real-World Scenarios|Real-World Failure Scenarios|Real-World Review Scenarios"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                completed_process.returncode,
                0,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertEqual("Real-World Review Scenarios", completed_process.stdout.strip())

    def test_standalone_bootstrap_copy_refreshes_from_fresh_temporary_clone_and_cleans_it_up(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.sh"
            temporary_bootstrap_directory = temporary_path / "tmp-bootstrap"
            temporary_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            bootstrap_source_path = create_bootstrap_source_repository(temporary_path)
            external_script_path.write_text(
                "# stale bootstrap copy\n" + read_text(SYNC_SCRIPT_PATH),
                encoding="utf-8",
            )

            completed_process = run_bash(
                f'bash "{external_script_path}" status',
                environment={
                    "CODEX_SKILLS_REPOSITORY_URL": str(bootstrap_source_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(temporary_bootstrap_directory),
                },
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertEqual(
                completed_process.returncode,
                0,
                normalized_output,
            )
            self.assertIn("Restarting into the refreshed standalone entry script before continuing.", normalized_output)
            self.assertEqual(
                read_text(SYNC_SCRIPT_PATH),
                external_script_path.read_text(encoding="utf-8"),
            )
            self.assertEqual([], list(temporary_bootstrap_directory.iterdir()))
            self.assertFalse((home_directory / ".codex-skill-pack-repos").exists())

    def test_standalone_bootstrap_without_arguments_opens_menu_and_cleans_up_temporary_clone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.sh"
            temporary_bootstrap_directory = temporary_path / "tmp-bootstrap"
            temporary_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            bootstrap_source_path = create_bootstrap_source_repository(temporary_path)
            external_script_path.write_text(read_text(SYNC_SCRIPT_PATH), encoding="utf-8")

            completed_process = run_bash(
                f'printf "4\\n" | bash "{external_script_path}"',
                environment={
                    "CODEX_SKILLS_REPOSITORY_URL": str(bootstrap_source_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(temporary_bootstrap_directory),
                },
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertEqual(0, completed_process.returncode, normalized_output)
            self.assertIn("Codex Skill Manager", normalized_output)
            self.assertIn("Install - install the skill pack", normalized_output)
            self.assertIn("Quit", normalized_output)
            self.assertEqual([], list(temporary_bootstrap_directory.iterdir()))
            self.assertFalse((home_directory / ".codex-skill-pack-repos").exists())

    def test_standalone_bootstrap_clone_failure_cleans_up_temporary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.sh"
            temporary_bootstrap_directory = temporary_path / "tmp-bootstrap"
            temporary_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            missing_repository_path = temporary_path / "missing-bootstrap-source.git"
            external_script_path.write_text(read_text(SYNC_SCRIPT_PATH), encoding="utf-8")

            completed_process = run_bash(
                f'bash "{external_script_path}" status',
                environment={
                    "CODEX_SKILLS_REPOSITORY_URL": str(missing_repository_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(temporary_bootstrap_directory),
                },
                working_directory=temporary_path,
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertNotEqual(0, completed_process.returncode, normalized_output)
            self.assertIn("Cloning fresh temporary codex_skills repo for this run", normalized_output)
            self.assertEqual([], list(temporary_bootstrap_directory.iterdir()))

    def test_standalone_bootstrap_ignores_inherited_foreign_runtime_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.sh"
            temporary_bootstrap_directory = temporary_path / "tmp-bootstrap"
            temporary_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            bootstrap_source_path = create_bootstrap_source_repository(temporary_path)
            inherited_runtime_repository_path = temporary_path / "inherited-runtime-repository"
            shutil.copytree(bootstrap_source_path, inherited_runtime_repository_path)
            external_script_path.write_text(
                "# stale bootstrap copy\n" + read_text(SYNC_SCRIPT_PATH),
                encoding="utf-8",
            )

            completed_process = run_bash(
                f'bash "{external_script_path}" status',
                environment={
                    "CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH": str(temporary_path / "foreign-sync-skills.sh"),
                    "CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH": str(temporary_path / "foreign-sync-skills.sh"),
                    "CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH": str(inherited_runtime_repository_path),
                    "CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT": "false",
                    "CODEX_SKILLS_REPOSITORY_URL": str(bootstrap_source_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(temporary_bootstrap_directory),
                },
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertEqual(
                completed_process.returncode,
                0,
                normalized_output,
            )
            self.assertIn("Restarting into the refreshed standalone entry script before continuing.", normalized_output)
            self.assertNotIn(str(inherited_runtime_repository_path), normalized_output)
            self.assertTrue(inherited_runtime_repository_path.exists())
            self.assertEqual([], list(temporary_bootstrap_directory.iterdir()))

    def test_powershell_bootstrap_copy_refreshes_from_staged_repo_when_available(self) -> None:
        powershell_path = shutil.which("pwsh") or shutil.which("powershell")
        if powershell_path is None:
            self.skipTest("PowerShell runtime is not available in this environment.")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.ps1"
            managed_powershell_script_path = REPOSITORY_ROOT / "sync-skills.ps1"
            external_script_path.write_text(
                "# stale bootstrap copy\n" + read_text(managed_powershell_script_path),
                encoding="utf-8",
            )

            completed_process = subprocess.run(
                [
                    powershell_path,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(external_script_path),
                    "status",
                ],
                cwd=REPOSITORY_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "CODEX_SKILLS_REPOSITORY_PATH": str(REPOSITORY_ROOT),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                },
            )
            self.assertEqual(
                completed_process.returncode,
                0,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertEqual(
                read_text(managed_powershell_script_path),
                external_script_path.read_text(encoding="utf-8"),
            )

    def test_powershell_standalone_bootstrap_without_arguments_opens_menu_and_cleans_up_temporary_clone(self) -> None:
        powershell_path = shutil.which("pwsh") or shutil.which("powershell")
        if powershell_path is None:
            self.skipTest("PowerShell runtime is not available in this environment.")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.ps1"
            staged_bootstrap_directory = temporary_path / "tmp-bootstrap"
            staged_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            bootstrap_source_path = create_bootstrap_source_repository(temporary_path)
            managed_powershell_script_path = REPOSITORY_ROOT / "sync-skills.ps1"
            external_script_path.write_text(
                "# stale bootstrap copy\n" + read_text(managed_powershell_script_path),
                encoding="utf-8",
            )

            completed_process = subprocess.run(
                [
                    powershell_path,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(external_script_path),
                ],
                cwd=temporary_path,
                check=False,
                capture_output=True,
                text=True,
                input="4\n",
                env={
                    **os.environ,
                    "CODEX_SKILLS_REPOSITORY_URL": str(bootstrap_source_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(staged_bootstrap_directory),
                    "TMP": str(staged_bootstrap_directory),
                    "TEMP": str(staged_bootstrap_directory),
                },
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertEqual(0, completed_process.returncode, normalized_output)
            self.assertIn("Codex Skill Manager", normalized_output)
            self.assertIn("Install - install the skill pack", normalized_output)
            self.assertIn("Quit", normalized_output)
            self.assertEqual(
                read_text(managed_powershell_script_path),
                external_script_path.read_text(encoding="utf-8"),
            )
            self.assertEqual([], list(staged_bootstrap_directory.iterdir()))
            self.assertFalse((home_directory / ".codex-skill-pack-repos").exists())

    def test_powershell_standalone_bootstrap_clone_failure_cleans_up_temporary_directory(self) -> None:
        powershell_path = shutil.which("pwsh") or shutil.which("powershell")
        if powershell_path is None:
            self.skipTest("PowerShell runtime is not available in this environment.")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.ps1"
            staged_bootstrap_directory = temporary_path / "tmp-bootstrap"
            staged_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            missing_repository_path = temporary_path / "missing-bootstrap-source.git"
            managed_powershell_script_path = REPOSITORY_ROOT / "sync-skills.ps1"
            external_script_path.write_text(read_text(managed_powershell_script_path), encoding="utf-8")

            completed_process = subprocess.run(
                [
                    powershell_path,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(external_script_path),
                    "status",
                ],
                cwd=temporary_path,
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "CODEX_SKILLS_REPOSITORY_URL": str(missing_repository_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(staged_bootstrap_directory),
                    "TMP": str(staged_bootstrap_directory),
                    "TEMP": str(staged_bootstrap_directory),
                },
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertNotEqual(0, completed_process.returncode, normalized_output)
            self.assertIn("Cloning fresh temporary codex_skills repo for this run", normalized_output)
            self.assertEqual([], list(staged_bootstrap_directory.iterdir()))

    def test_powershell_bootstrap_ignores_inherited_foreign_runtime_repository(self) -> None:
        powershell_path = shutil.which("pwsh") or shutil.which("powershell")
        if powershell_path is None:
            self.skipTest("PowerShell runtime is not available in this environment.")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.ps1"
            staged_bootstrap_directory = temporary_path / "tmp-bootstrap"
            staged_bootstrap_directory.mkdir()
            home_directory = temporary_path / "home"
            home_directory.mkdir()
            bootstrap_source_path = create_bootstrap_source_repository(temporary_path)
            inherited_runtime_repository_path = temporary_path / "inherited-runtime-repository"
            shutil.copytree(bootstrap_source_path, inherited_runtime_repository_path)
            managed_powershell_script_path = REPOSITORY_ROOT / "sync-skills.ps1"
            external_script_path.write_text(
                "# stale bootstrap copy\n" + read_text(managed_powershell_script_path),
                encoding="utf-8",
            )

            completed_process = subprocess.run(
                [
                    powershell_path,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(external_script_path),
                    "status",
                ],
                cwd=temporary_path,
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH": str(temporary_path / "foreign-sync-skills.ps1"),
                    "CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH": str(temporary_path / "foreign-sync-skills.ps1"),
                    "CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH": str(inherited_runtime_repository_path),
                    "CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT": "false",
                    "CODEX_SKILLS_REPOSITORY_URL": str(bootstrap_source_path),
                    "CODEX_SKILLS_REPOSITORY_BRANCH": current_repository_branch(),
                    "CODEX_TARGET_OVERRIDE": str(temporary_path / ".codex"),
                    "HOME": str(home_directory),
                    "TMPDIR": str(staged_bootstrap_directory),
                    "TMP": str(staged_bootstrap_directory),
                    "TEMP": str(staged_bootstrap_directory),
                },
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertEqual(0, completed_process.returncode, normalized_output)
            self.assertIn("Restarting into the refreshed standalone entry script before continuing.", normalized_output)
            self.assertNotIn(str(inherited_runtime_repository_path), normalized_output)
            self.assertTrue(inherited_runtime_repository_path.exists())
            self.assertEqual(
                read_text(managed_powershell_script_path),
                external_script_path.read_text(encoding="utf-8"),
            )
            self.assertEqual([], list(staged_bootstrap_directory.iterdir()))

    def test_menu_is_simplified_to_install_update_status_quit(self) -> None:
        completed_process = run_bash('printf "4\\n" | bash ./sync-skills.sh menu')
        normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)

        self.assertEqual(0, completed_process.returncode, normalized_output)
        self.assertIn("Install - install the skill pack", normalized_output)
        self.assertIn("Update  - check for manager/repo updates first", normalized_output)
        self.assertIn("Status  - check manager version", normalized_output)
        self.assertIn("Quit", normalized_output)
        self.assertNotIn("[s] sync", normalized_output)
        self.assertNotIn("github-update", normalized_output)
        self.assertNotIn("remove full skill pack", normalized_output)
        self.assertNotIn("verify full skill pack", normalized_output)

    def test_main_without_arguments_opens_menu_by_default(self) -> None:
        completed_process = run_bash('printf "4\\n" | bash ./sync-skills.sh')
        normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)

        self.assertEqual(0, completed_process.returncode, normalized_output)
        self.assertIn("Codex Skill Manager", normalized_output)
        self.assertIn("Install - install the skill pack", normalized_output)
        self.assertIn("Quit", normalized_output)

    def test_status_reports_manager_and_skill_update_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed_process = run_bash(
                "bash ./sync-skills.sh status",
                environment={"CODEX_TARGET_OVERRIDE": str(Path(temporary_directory) / ".codex")},
            )
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)

            self.assertEqual(0, completed_process.returncode, normalized_output)
            self.assertIn("Manager version:", normalized_output)
            self.assertIn("Self update status:", normalized_output)
            self.assertIn("Skill pack update status:", normalized_output)
            self.assertIn("Installed version:", normalized_output)
            self.assertIn("memory scope layout:", normalized_output)

    def test_memory_scope_script_resolves_workspace_workstream_and_agent_paths(self) -> None:
        script_path = (
            REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "resolve_memory_scope.py"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "example-workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            completed_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--agent-role",
                    "reviewer",
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--create-missing",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            scope_payload = json.loads(completed_process.stdout)
            self.assertEqual("reviewer", scope_payload["agent_role"])
            self.assertEqual("feature-review", scope_payload["workstream_key"])
            self.assertEqual("reviewer-lane-a", scope_payload["agent_instance"])
            self.assertIn("workspaces", scope_payload["write_targets"]["workspace_memory"])
            self.assertIn("workstreams", scope_payload["write_targets"]["workstream_memory"])
            self.assertIn("agents", scope_payload["write_targets"]["agent_memory"])
            self.assertIn("instances", scope_payload["write_targets"]["agent_instance_memory"])
            self.assertIn("research_cache", scope_payload["write_targets"]["research_cache"])
            self.assertIn("SESSION-STATE.md", scope_payload["write_targets"]["session_state"])
            self.assertIn("working-buffer.md", scope_payload["write_targets"]["working_buffer"])
            self.assertIn("session-wal.jsonl", scope_payload["write_targets"]["wal"])
            self.assertIn("spawned-agent-registry.json", scope_payload["write_targets"]["spawned_agent_registry"])
            self.assertIn("reference", scope_payload["write_targets"]["workspace_reference_directory"])
            self.assertIn("reference", scope_payload["write_targets"]["workstream_reference_directory"])
            self.assertTrue(Path(scope_payload["write_targets"]["workspace_memory"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["workstream_memory"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["agent_instance_memory"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["research_cache"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["session_state"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["working_buffer"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["wal"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["spawned_agent_registry"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["workspace_reference_directory"]).exists())
            self.assertTrue(Path(scope_payload["write_targets"]["workstream_reference_directory"]).exists())
            self.assertEqual(scope_payload["write_targets"]["agent_instance_memory"], scope_payload["search_order"][0])
            self.assertEqual(scope_payload["write_targets"]["agent_memory"], scope_payload["search_order"][1])
            self.assertEqual(scope_payload["write_targets"]["session_state"], scope_payload["search_order"][2])
            self.assertEqual(scope_payload["write_targets"]["working_buffer"], scope_payload["search_order"][3])
            self.assertEqual(scope_payload["write_targets"]["workstream_summary"], scope_payload["search_order"][4])
            self.assertEqual(scope_payload["write_targets"]["workstream_memory"], scope_payload["search_order"][5])
            self.assertEqual(
                scope_payload["write_targets"]["workstream_reference_directory"],
                scope_payload["search_order"][6],
            )
            self.assertEqual(scope_payload["write_targets"]["workspace_summary"], scope_payload["search_order"][7])
            self.assertEqual(scope_payload["write_targets"]["workspace_memory"], scope_payload["search_order"][8])
            self.assertEqual(
                scope_payload["write_targets"]["workspace_reference_directory"],
                scope_payload["search_order"][9],
            )
            self.assertEqual(scope_payload["write_targets"]["research_cache"], scope_payload["search_order"][10])
            self.assertTrue(scope_payload["search_order"][-1].endswith("raw_memories.md"))

    def test_memory_maintenance_script_handles_wal_buffer_trim_and_recalibration(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "memory_maintenance.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            write_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "write-session-state",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--category",
                    "decision",
                    "--title",
                    "Direction",
                    "--detail",
                    "Option B is the confirmed direction.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, write_process.returncode, write_process.stdout + write_process.stderr)
            write_payload = json.loads(write_process.stdout)
            self.assertEqual("decision", write_payload["category"])
            self.assertEqual("Direction", write_payload["title"])

            workspace_slug = re.sub(
                r"[^a-z0-9]+",
                "-",
                workspace_path.resolve().as_posix().lower().replace(":", ""),
            ).strip("-") or "workspace"

            session_state_path = (
                memory_base
                / "workspaces"
                / workspace_slug
                / "workstreams"
                / "feature-review"
                / "memory"
                / "SESSION-STATE.md"
            )
            working_buffer_path = session_state_path.with_name("working-buffer.md")
            wal_path = session_state_path.with_name("session-wal.jsonl")
            workspace_summary_path = (
                memory_base / "workspaces" / workspace_slug / "SUMMARY.md"
            )
            workstream_summary_path = (
                memory_base
                / "workspaces"
                / workspace_slug
                / "workstreams"
                / "feature-review"
                / "SUMMARY.md"
            )

            self.assertIn("Option B is the confirmed direction.", session_state_path.read_text(encoding="utf-8"))
            self.assertIn("Direction", session_state_path.read_text(encoding="utf-8"))
            wal_entries = [json.loads(line) for line in wal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(1, len(wal_entries))
            self.assertEqual("decision", wal_entries[0]["category"])

            buffer_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "append-working-buffer",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--text",
                    "Validated the refreshed memory workflow.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, buffer_process.returncode, buffer_process.stdout + buffer_process.stderr)
            self.assertIn(
                "Validated the refreshed memory workflow.",
                working_buffer_path.read_text(encoding="utf-8"),
            )

            workspace_summary_path.write_text(
                "# Workspace Summary\n\n"
                "## Older Notes\n- "
                + ("older detail " * 30).strip()
                + "\n\n"
                "## More Older Notes\n- "
                + ("more older detail " * 30).strip()
                + "\n\n"
                "## Policy\n- Prefer scoped memory first.\n",
                encoding="utf-8",
            )
            workstream_summary_path.write_text(
                "# Workstream Summary\n\n## Policy\n- Do not repeat the same failing tool call more than twice.\n",
                encoding="utf-8",
            )

            recalibrate_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "recalibrate",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--observed",
                    "Prefer scoped memory first.",
                    "--observed",
                    "Do not repeat the same failing tool call more than twice.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                recalibrate_process.returncode,
                recalibrate_process.stdout + recalibrate_process.stderr,
            )
            recalibrate_payload = json.loads(recalibrate_process.stdout)
            self.assertGreaterEqual(recalibrate_payload["canonical_rule_count"], 2)
            self.assertEqual(2, recalibrate_payload["observed_count"])
            self.assertEqual(
                ["aligned", "aligned"],
                [finding["status"] for finding in recalibrate_payload["observed_findings"]],
            )

            trim_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "trim",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--max-file-tokens",
                    "40",
                    "--max-total-tokens",
                    "40",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, trim_process.returncode, trim_process.stdout + trim_process.stderr)
            trim_payload = json.loads(trim_process.stdout)
            self.assertGreater(trim_payload["before_total_tokens"], trim_payload["after_total_tokens"])
            self.assertLessEqual(trim_payload["after_total_tokens"], 40)
            self.assertTrue(trim_payload["within_total_budget"])
            workspace_summary_report = next(
                file_report
                for file_report in trim_payload["file_reports"]
                if file_report["file_label"] == "workspace_summary"
            )
            self.assertIsNotNone(workspace_summary_report["archive_file"])
            self.assertTrue(Path(workspace_summary_report["archive_file"]).exists())
            trimmed_workspace_summary = workspace_summary_path.read_text(encoding="utf-8")
            self.assertNotIn("Older Notes", trimmed_workspace_summary)

    def test_memory_status_report_prefers_scoped_memory_files(self) -> None:
        scope_script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "resolve_memory_scope.py"
        report_script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "memory_status_report.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            scope_process = subprocess.run(
                [
                    sys.executable,
                    str(scope_script_path),
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--agent-role",
                    "reviewer",
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--create-missing",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, scope_process.returncode, scope_process.stdout + scope_process.stderr)
            scope_payload = json.loads(scope_process.stdout)

            Path(scope_payload["write_targets"]["workspace_memory"]).write_text(
                "# Workspace Memory\n\n### learnings\n- Workspace-scoped learning\n",
                encoding="utf-8",
            )
            Path(scope_payload["write_targets"]["workstream_memory"]).write_text(
                "# Workstream Memory\n\n### learnings\n- Workstream-scoped learning\n",
                encoding="utf-8",
            )
            Path(scope_payload["write_targets"]["agent_memory"]).write_text(
                "# Agent Memory\n\n### learnings\n- Reviewer-scoped learning\n",
                encoding="utf-8",
            )
            Path(scope_payload["write_targets"]["agent_instance_memory"]).write_text(
                "# Agent Instance Memory\n\n### learnings\n- Reviewer instance learning\n",
                encoding="utf-8",
            )
            Path(scope_payload["write_targets"]["workspace_summary"]).write_text(
                "Their recurring priority lanes are:\n- Prefer scoped memory first.\n\n## General Tips\n- Keep the handoff short.\n",
                encoding="utf-8",
            )
            Path(scope_payload["write_targets"]["workstream_summary"]).write_text(
                "Their recurring priority lanes are:\n- Keep this feature lane isolated.\n\n## General Tips\n- Reuse the same reviewer lane.\n",
                encoding="utf-8",
            )

            report_process = subprocess.run(
                [
                    sys.executable,
                    str(report_script_path),
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--agent-role",
                    "reviewer",
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, report_process.returncode, report_process.stdout + report_process.stderr)
            report_payload = json.loads(report_process.stdout)

            self.assertIn("Workspace-scoped learning", report_payload["learning_items"])
            self.assertIn("Workstream-scoped learning", report_payload["learning_items"])
            self.assertIn("Reviewer-scoped learning", report_payload["learning_items"])
            self.assertIn("Reviewer instance learning", report_payload["learning_items"])
            self.assertIn("Prefer scoped memory first.", report_payload["user_needs"])
            self.assertIn("Keep this feature lane isolated.", report_payload["user_needs"])
            self.assertGreaterEqual(report_payload["durable_bank_size"], 3)
            self.assertEqual("feature-review", report_payload["workstream_key"])
            self.assertEqual("reviewer-lane-a", report_payload["agent_instance"])

    def test_memory_status_report_filters_rollout_summaries_by_workstream_and_agent_instance(self) -> None:
        report_script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "memory_status_report.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            prefixed_workspace_path = "\\\\?\\" + str(workspace_path)
            memory_base = temporary_path / "memories"
            rollout_directory = memory_base / "rollout_summaries"
            rollout_directory.mkdir(parents=True)

            matching_summary = rollout_directory / "2026-03-11-feature-review-a.md"
            matching_summary.write_text(
                f"""thread_id: session-a
updated_at: 2026-03-11T08:00:00+00:00
cwd: {prefixed_workspace_path}
git_branch: feature/review
agent_instance: reviewer-lane-a

# Matching rollout

## Task 1: matching lane
Outcome: success

Reusable knowledge:
- Matching rollout learning
""",
                encoding="utf-8",
            )

            matching_workstream_key_summary = rollout_directory / "2026-03-11-feature-review-workstream-key.md"
            matching_workstream_key_summary.write_text(
                f"""thread_id: session-a2
updated_at: 2026-03-11T08:30:00+00:00
cwd: {workspace_path}
workstream_key: feature-review
agent_instance: reviewer-lane-a

# Matching rollout by workstream key

## Task 1: matching lane by workstream key
Outcome: success

Reusable knowledge:
- Matching workstream-key learning
""",
                encoding="utf-8",
            )

            unrelated_lane_summary = rollout_directory / "2026-03-11-feature-review-b.md"
            unrelated_lane_summary.write_text(
                f"""thread_id: session-b
updated_at: 2026-03-11T09:00:00+00:00
cwd: {workspace_path}
git_branch: feature/review
agent_instance: reviewer-lane-b

# Unrelated reviewer lane

## Task 1: unrelated lane
Outcome: success

Reusable knowledge:
- Unrelated reviewer lane learning

Things that did not work / can be improved:
- Still pending lane-specific follow-up.
""",
                encoding="utf-8",
            )

            unrelated_workstream_summary = rollout_directory / "2026-03-11-other-workstream.md"
            unrelated_workstream_summary.write_text(
                f"""thread_id: session-c
updated_at: 2026-03-11T10:00:00+00:00
cwd: {workspace_path}
git_branch: other-workstream
agent_instance: reviewer-lane-a

# Unrelated workstream

## Task 1: unrelated workstream
Outcome: success

Reusable knowledge:
- Other workstream learning
""",
                encoding="utf-8",
            )

            misleading_body_summary = rollout_directory / "2026-03-11-misleading-body.md"
            misleading_body_summary.write_text(
                f"""thread_id: session-d
updated_at: 2026-03-11T11:00:00+00:00
cwd: {workspace_path}
git_branch: other-workstream
agent_instance: reviewer-lane-b

# Misleading body match

## Task 1: prose mentions the target lane
Outcome: success

Reusable knowledge:
- Misleading body learning that should stay excluded.

Notes:
- This prose mentions feature review and reviewer lane a, but only in body text.
""",
                encoding="utf-8",
            )

            report_process = subprocess.run(
                [
                    sys.executable,
                    str(report_script_path),
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--agent-role",
                    "reviewer",
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--date",
                    "2026-03-11",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, report_process.returncode, report_process.stdout + report_process.stderr)
            report_payload = json.loads(report_process.stdout)

            self.assertEqual(2, report_payload["summary_count"])
            self.assertTrue(report_payload["closure_ready"])
            self.assertIn("Matching rollout learning", report_payload["learning_items"])
            self.assertIn("Matching workstream-key learning", report_payload["learning_items"])
            self.assertNotIn("Unrelated reviewer lane learning", report_payload["learning_items"])
            self.assertNotIn("Other workstream learning", report_payload["learning_items"])
            self.assertNotIn("Misleading body learning that should stay excluded.", report_payload["learning_items"])
            self.assertCountEqual(
                [
                    str(matching_summary),
                    str(matching_workstream_key_summary),
                ],
                report_payload["source_files"]["matching_rollout_summaries"],
            )

    def test_research_cache_script_round_trips_marks_stale_and_archives(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "research_cache.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            record_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-role",
                    "worker",
                    "--agent-instance",
                    "worker-lane-a",
                    "--question",
                    "How should the cache lookup work?",
                    "--answer",
                    "Prefer the shared workspace cache before repeating live research.",
                    "--source",
                    "https://example.com/cache",
                    "--freshness",
                    "Refresh monthly or after a tool/runtime change.",
                    "--tag",
                    "cache",
                    "--tag",
                    "memory",
                    "--entry-key",
                    "cache-lookup",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, record_process.returncode, record_process.stdout + record_process.stderr)
            record_payload = json.loads(record_process.stdout)
            self.assertEqual("feature-review", record_payload["workstream_key"])
            self.assertEqual("worker-lane-a", record_payload["agent_instance"])

            lookup_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "lookup",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--query",
                    "cache lookup",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, lookup_process.returncode, lookup_process.stdout + lookup_process.stderr)
            lookup_payload = json.loads(lookup_process.stdout)
            self.assertEqual(1, len(lookup_payload))
            self.assertEqual("cache-lookup", lookup_payload[0]["entry_key"])

            stale_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "mark-stale",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--entry-key",
                    "cache-lookup",
                    "--reason",
                    "Tooling changed and the entry must be refreshed.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, stale_process.returncode, stale_process.stdout + stale_process.stderr)
            stale_payload = json.loads(stale_process.stdout)
            self.assertEqual("stale", stale_payload["status"])
            self.assertEqual("penalty", stale_payload["reinforcement"])

    def test_research_cache_lookup_skips_entries_past_inferred_freshness_window(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "research_cache.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            record_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--question",
                    "When should cache findings expire?",
                    "--answer",
                    "Monthly guidance should stop reusing findings once the month-sized window has passed.",
                    "--source",
                    "https://example.com/freshness",
                    "--freshness",
                    "Refresh monthly or after a tool/runtime change.",
                    "--entry-key",
                    "monthly-expiry",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, record_process.returncode, record_process.stdout + record_process.stderr)

            cache_file = next(memory_base.rglob("cache.jsonl"))
            existing_entry = json.loads(cache_file.read_text(encoding="utf-8").strip())
            existing_entry["updated_at"] = "2025-01-01T00:00:00Z"
            cache_file.write_text(json.dumps(existing_entry) + "\n", encoding="utf-8")

            lookup_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "lookup",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--query",
                    "cache findings expire",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, lookup_process.returncode, lookup_process.stdout + lookup_process.stderr)
            self.assertEqual([], json.loads(lookup_process.stdout))

            include_stale_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "lookup",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--query",
                    "cache findings expire",
                    "--include-stale",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                include_stale_process.returncode,
                include_stale_process.stdout + include_stale_process.stderr,
            )
            include_stale_payload = json.loads(include_stale_process.stdout)
            self.assertEqual(1, len(include_stale_payload))
            self.assertEqual("monthly-expiry", include_stale_payload[0]["entry_key"])

    def test_agent_registry_tracks_same_role_reuse_and_unhealthy_recovery(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "agent_registry.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            register_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "register",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "reviewer-lane-a",
                    "--agent-id",
                    "019abc",
                    "--agent-role",
                    "reviewer",
                    "--status",
                    "completed",
                    "--purpose",
                    "final-gap-audit",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, register_process.returncode, register_process.stdout + register_process.stderr)
            register_payload = json.loads(register_process.stdout)
            self.assertEqual("reviewer", register_payload["agent_role"])
            self.assertEqual("completed", register_payload["status"])

            lookup_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "lookup",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-role",
                    "reviewer",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, lookup_process.returncode, lookup_process.stdout + lookup_process.stderr)
            lookup_payload = json.loads(lookup_process.stdout)
            self.assertEqual("019abc", lookup_payload["agent_id"])
            self.assertEqual("completed", lookup_payload["status"])

            unhealthy_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "mark-unhealthy",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-id",
                    "019abc",
                    "--reason",
                    "stale completed payload",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                unhealthy_process.returncode,
                unhealthy_process.stdout + unhealthy_process.stderr,
            )
            unhealthy_payload = json.loads(unhealthy_process.stdout)
            self.assertEqual("unhealthy", unhealthy_payload["status"])

            lookup_after_unhealthy_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "lookup",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-role",
                    "reviewer",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                lookup_after_unhealthy_process.returncode,
                lookup_after_unhealthy_process.stdout + lookup_after_unhealthy_process.stderr,
            )
            self.assertEqual("null", lookup_after_unhealthy_process.stdout.strip())

    def test_agent_packets_script_builds_handoff_feedback_and_readiness_packets(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "agent_packets.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            handoff_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "build-handoff",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "manager-lane",
                    "--source-agent-role",
                    "reviewer",
                    "--source-agent-id",
                    "019review",
                    "--source-agent-instance",
                    "reviewer-lane-a",
                    "--target-agent-role",
                    "worker",
                    "--target-agent-id",
                    "019worker",
                    "--target-agent-instance",
                    "worker-lane-a",
                    "--objective",
                    "Implement the scoped cache refresh.",
                    "--constraint",
                    "Do not widen the write scope.",
                    "--relevant-file",
                    str(workspace_path / "research_cache.py"),
                    "--finding",
                    "Only stale handling needs the patch.",
                    "--validation",
                    "Current tests pass before the change.",
                    "--non-goal",
                    "Do not rewrite unrelated docs.",
                    "--expected-output",
                    "Return the changed files plus the validation result.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, handoff_process.returncode, handoff_process.stdout + handoff_process.stderr)
            handoff_payload = json.loads(handoff_process.stdout)
            self.assertEqual("handoff", handoff_payload["packet_kind"])
            self.assertEqual("reviewer-lane-a", handoff_payload["source_agent"]["agent_instance"])
            self.assertEqual("worker", handoff_payload["target_agent"]["role"])
            self.assertEqual("worker-lane-a", handoff_payload["target_agent"]["agent_instance"])
            self.assertTrue(Path(handoff_payload["packet_file"]).exists())

            feedback_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "build-feedback",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "manager-lane",
                    "--source-agent-role",
                    "reviewer",
                    "--source-agent-id",
                    "019review",
                    "--source-agent-instance",
                    "reviewer-lane-a",
                    "--target-agent-role",
                    "worker",
                    "--target-agent-id",
                    "019worker",
                    "--target-agent-instance",
                    "worker-lane-a",
                    "--objective",
                    "Close the validation gap before release.",
                    "--feedback",
                    "The stale-path regression still lacks a test.",
                    "--request",
                    "Add the missing regression test and rerun the targeted validation.",
                    "--validation",
                    "Lint passed but the release gate is still blocked.",
                    "--expected-output",
                    "Return the updated test result plus any remaining risk.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, feedback_process.returncode, feedback_process.stdout + feedback_process.stderr)
            feedback_payload = json.loads(feedback_process.stdout)
            self.assertEqual("feedback", feedback_payload["packet_kind"])
            self.assertIn("The stale-path regression still lacks a test.", feedback_payload["feedback_items"])
            self.assertEqual("reviewer-lane-a", feedback_payload["source_agent"]["agent_instance"])
            self.assertEqual("worker-lane-a", feedback_payload["target_agent"]["agent_instance"])
            self.assertTrue(Path(feedback_payload["packet_file"]).exists())

            readiness_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "build-readiness-check",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--agent-instance",
                    "manager-lane",
                    "--source-agent-role",
                    "reviewer",
                    "--source-agent-id",
                    "019review",
                    "--source-agent-instance",
                    "reviewer-lane-a",
                    "--target-agent-role",
                    "worker",
                    "--target-agent-id",
                    "019worker",
                    "--target-agent-instance",
                    "worker-lane-a",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, readiness_process.returncode, readiness_process.stdout + readiness_process.stderr)
            readiness_payload = json.loads(readiness_process.stdout)
            self.assertEqual("readiness-check", readiness_payload["packet_kind"])
            self.assertIn("fresh ACK", readiness_payload["expected_output"][0])
            self.assertEqual("reviewer-lane-a", readiness_payload["source_agent"]["agent_instance"])
            self.assertEqual("worker-lane-a", readiness_payload["target_agent"]["agent_instance"])
            self.assertTrue(Path(readiness_payload["packet_file"]).exists())

    def test_loop_guard_script_flags_repeated_failures_until_resolved(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "loop_guard.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            workspace_path = temporary_path / "workspace"
            workspace_path.mkdir()
            memory_base = temporary_path / "memories"

            first_failure_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-failure",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--signature",
                    "validate-sync-heading",
                    "--tool-name",
                    "exec_command",
                    "--summary",
                    "The same validate invocation failed once.",
                    "--hypothesis",
                    "The heading matcher still uses stale input.",
                    "--next-change",
                    "Switch to the scoped helper before retrying.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                first_failure_process.returncode,
                first_failure_process.stdout + first_failure_process.stderr,
            )

            first_check_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "check",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--signature",
                    "validate-sync-heading",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, first_check_process.returncode, first_check_process.stdout + first_check_process.stderr)
            first_check_payload = json.loads(first_check_process.stdout)
            self.assertEqual(1, first_check_payload["repeat_count"])
            self.assertFalse(first_check_payload["should_change_approach"])

            second_failure_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-failure",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--signature",
                    "validate-sync-heading",
                    "--tool-name",
                    "exec_command",
                    "--summary",
                    "The same validate invocation failed twice.",
                    "--hypothesis",
                    "The same stale input is still in play.",
                    "--next-change",
                    "Change the execution shape before retrying.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                second_failure_process.returncode,
                second_failure_process.stdout + second_failure_process.stderr,
            )

            second_check_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "check",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--signature",
                    "validate-sync-heading",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                second_check_process.returncode,
                second_check_process.stdout + second_check_process.stderr,
            )
            second_check_payload = json.loads(second_check_process.stdout)
            self.assertEqual(2, second_check_payload["repeat_count"])
            self.assertTrue(second_check_payload["should_change_approach"])

            resolve_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "resolve",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--signature",
                    "validate-sync-heading",
                    "--resolution",
                    "Switched to the scoped helper and the next attempt passed.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, resolve_process.returncode, resolve_process.stdout + resolve_process.stderr)

            resolved_check_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "check",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-review",
                    "--signature",
                    "validate-sync-heading",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                resolved_check_process.returncode,
                resolved_check_process.stdout + resolved_check_process.stderr,
            )
            resolved_check_payload = json.loads(resolved_check_process.stdout)
            self.assertEqual(0, resolved_check_payload["repeat_count"])
            self.assertFalse(resolved_check_payload["should_change_approach"])

    def test_normalize_rollout_metadata_path_collapses_macos_private_aliases(self) -> None:
        scripts_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts"
        sys.path.insert(0, str(scripts_path))
        try:
            from memory_store import normalize_rollout_metadata_path
        finally:
            sys.path.pop(0)

        self.assertEqual(
            "/var/folders/example/workspace",
            normalize_rollout_metadata_path("/private/var/folders/example/workspace"),
        )
        self.assertEqual(
            "/tmp/example/workspace",
            normalize_rollout_metadata_path("/private/tmp/example/workspace"),
        )

    def test_completion_gate_reports_not_ready_without_recorded_requirements(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "completion_gate.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace_path = Path(temporary_directory) / "workspace"
            memory_base = Path(temporary_directory) / "memory-base"
            workspace_path.mkdir()
            memory_base.mkdir()

            check_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "check",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-rollout",
                    "--agent-instance",
                    "reviewer-main",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, check_process.returncode, check_process.stdout + check_process.stderr)
            payload = json.loads(check_process.stdout)
            self.assertFalse(payload["closure_ready"])
            self.assertEqual(0, payload["requirement_count"])
            self.assertIn("No requirements are recorded yet", payload["next_actions"][0])

    def test_completion_gate_requires_blocked_reason_for_blocked_requirements(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "completion_gate.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace_path = Path(temporary_directory) / "workspace"
            memory_base = Path(temporary_directory) / "memory-base"
            workspace_path.mkdir()
            memory_base.mkdir()

            blocked_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-requirement",
                    "--memory-base",
                    str(memory_base),
                    "--workspace-root",
                    str(workspace_path),
                    "--workstream-key",
                    "feature-rollout",
                    "--agent-instance",
                    "reviewer-main",
                    "--requirement-id",
                    "requirement-1",
                    "--text",
                    "Explain the real blocker.",
                    "--status",
                    "blocked",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, blocked_process.returncode)
            self.assertIn("--blocked-reason is required when --status blocked", blocked_process.stderr)

    def test_completion_gate_requires_all_requirements_to_be_done_before_closure(self) -> None:
        script_path = REPOSITORY_ROOT / "memory-status-reporter" / "scripts" / "completion_gate.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace_path = Path(temporary_directory) / "workspace"
            memory_base = Path(temporary_directory) / "memory-base"
            workspace_path.mkdir()
            memory_base.mkdir()

            scope_arguments = [
                "--memory-base",
                str(memory_base),
                "--workspace-root",
                str(workspace_path),
                "--workstream-key",
                "feature-rollout",
                "--agent-instance",
                "reviewer-main",
            ]

            first_record_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-requirement",
                    *scope_arguments,
                    "--requirement-id",
                    "requirement-1",
                    "--text",
                    "Ship the completion gate wiring.",
                    "--status",
                    "done",
                    "--evidence",
                    "Patched repo guidance.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                first_record_process.returncode,
                first_record_process.stdout + first_record_process.stderr,
            )

            second_record_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-requirement",
                    *scope_arguments,
                    "--requirement-id",
                    "requirement-2",
                    "--text",
                    "Validate the synced-home behavior.",
                    "--status",
                    "pending",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                second_record_process.returncode,
                second_record_process.stdout + second_record_process.stderr,
            )
            pending_payload = json.loads(second_record_process.stdout)
            self.assertFalse(pending_payload["closure_ready"])
            self.assertEqual(1, pending_payload["pending_count"])

            blocked_record_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-requirement",
                    *scope_arguments,
                    "--requirement-id",
                    "requirement-2",
                    "--text",
                    "Validate the synced-home behavior.",
                    "--status",
                    "blocked",
                    "--blocked-reason",
                    "Validation environment is offline.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                blocked_record_process.returncode,
                blocked_record_process.stdout + blocked_record_process.stderr,
            )
            blocked_payload = json.loads(blocked_record_process.stdout)
            self.assertFalse(blocked_payload["closure_ready"])
            self.assertEqual(1, blocked_payload["blocked_count"])

            done_record_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "record-requirement",
                    *scope_arguments,
                    "--requirement-id",
                    "requirement-2",
                    "--text",
                    "Validate the synced-home behavior.",
                    "--status",
                    "done",
                    "--evidence",
                    "Ran sync validation successfully.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                done_record_process.returncode,
                done_record_process.stdout + done_record_process.stderr,
            )
            done_payload = json.loads(done_record_process.stdout)
            self.assertTrue(done_payload["closure_ready"])
            self.assertEqual(2, done_payload["done_count"])
            self.assertEqual(0, done_payload["blocked_count"])
            self.assertTrue(done_payload["ledger_path"].endswith("completion-gate.json"))

    def test_install_uses_repo_managed_refresh_when_pack_is_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'validate_sync_operation_prerequisites() { return 0; }; '
                'pack_is_installed() { return 0; }; '
                'run_task_line() { printf "%s\\n" "$1"; return 0; }; '
                'apply_repo_managed_changes() { return 0; }; '
                'sync_codex() { return 0; }; '
                'install_codex'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertIn("validate", completed_process.stdout)
            self.assertIn("sync changes to", completed_process.stdout)
            self.assertNotIn("install to", completed_process.stdout)

    def test_main_resume_command_routes_to_repo_update_apply_step(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'run_task_line() { printf "%s\\n" "$1"; return 0; }; '
                'validate_sync_operation_prerequisites() { return 0; }; '
                'apply_repo_managed_changes() { return 0; }; '
                f'main "{SYNC_SCRIPT_PATH.name.replace("sync-skills.sh", "__resume-after-self-update")}"'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertIn("apply repo updates", completed_process.stdout)

    def test_sync_validate_smoke_passes(self) -> None:
        if os.environ.get("CODEX_SKIP_VALIDATE_SMOKE") == "1":
            self.skipTest("Nested validate smoke intentionally skipped to avoid recursion.")

        completed_process = run_bash(
            "bash ./sync-skills.sh validate",
            environment={
                "CODEX_SKIP_VALIDATE_SMOKE": "1",
                "CODEX_SKIP_VALIDATE_CONTRACT_TESTS": "1",
            },
        )
        self.assertEqual(
            completed_process.returncode,
            0,
            completed_process.stdout + completed_process.stderr,
        )
        self.assertNotIn("[run] contract tests", strip_ansi(completed_process.stdout + completed_process.stderr))

    def test_validate_all_runs_contract_tests_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                'validate_codex_repo_docs() { return 0; }; '
                'collect_failed_skill_names_parallel() { return 0; }; '
                'run_repo_contract_tests() { printf "contract-tests-ran\\n" >&2; return 1; }; '
                'validate_all'
            )
            completed_process = run_bash(command)
            self.assertEqual(1, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertIn("[run] contract tests", normalized_output)
            self.assertIn("[FAIL] contract tests", normalized_output)
            self.assertIn("contract-tests-ran", normalized_output)

    def test_fast_install_validation_skips_contract_tests_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                'validate_codex_repo_docs() { printf "docs-ran\n" >&2; return 0; }; '
                'collect_failed_skill_names_parallel() { return 0; }; '
                'run_repo_contract_tests() { printf "contract-tests-ran\n" >&2; return 1; }; '
                'validate_sync_operation_prerequisites'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertIn("[run] validate docs", normalized_output)
            self.assertNotIn("contract-tests-ran", normalized_output)
            self.assertIn("Fast install/update validation passed", normalized_output)

    def test_fast_install_validation_can_delegate_to_full_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'CODEX_SYNC_VALIDATION_MODE=full; '
                'validate_all() { printf "full-validation-ran\n" >&2; return 0; }; '
                'validate_sync_operation_prerequisites'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertIn("full-validation-ran", normalized_output)

    def test_sync_skill_to_codex_skips_redundant_validation_after_prerequisite_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides >/dev/null; '
                'validate_codex_skill_dir() { printf "unexpected-validation\n" >&2; return 9; }; '
                'CODEX_SYNC_PREREQUISITES_VALIDATED=true; '
                'sync_skill_to_codex "reviewer"'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertNotIn("unexpected-validation", completed_process.stdout + completed_process.stderr)
            self.assertTrue((temporary_path / ".codex" / "skills" / "reviewer" / "SKILL.md").exists())

    def test_sync_skill_to_codex_validates_skill_when_prerequisite_flag_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides >/dev/null; '
                'validate_codex_skill_dir() { printf "validation-called\n" >&2; return 0; }; '
                'sync_skill_to_codex "reviewer"'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertIn("validation-called", completed_process.stdout + completed_process.stderr)

    def test_fast_post_sync_verification_skips_full_skill_checksum_sweep_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'pack_is_installed() { return 0; }; '
                'list_root_guidance_relative_paths() { printf "AGENTS.md\n"; }; '
                'verify_root_file_sync_match() { printf "root-verified:%s\n" "$1" >&2; return 0; }; '
                'verify_synced_skill_and_home_agent_presence() { printf "presence-verified\n" >&2; return 0; }; '
                'list_repo_agent_profile_names() { printf "reviewer\n"; }; '
                'verify_agent_profile_sync_match() { printf "agent-profile-verified:%s\n" "$1" >&2; return 0; }; '
                'list_removed_repo_managed_skill_names() { return 0; }; '
                'list_removed_repo_managed_agent_profile_names() { return 0; }; '
                'verify_managed_inventory_files_match_repo() { printf "inventories-verified\n" >&2; return 0; }; '
                'verify_managed_config_routing_present() { printf "routing-verified\n" >&2; return 0; }; '
                'verify_memory_status_reporter_home_wiring_present() { printf "wiring-verified\n" >&2; return 0; }; '
                'verify_repo_managed_installation_hygiene() { printf "hygiene-verified\n" >&2; return 0; }; '
                'collect_failed_checksum_skill_names_parallel() { printf "unexpected-full-skill-checksum\n" >&2; return 99; }; '
                'run_task_line() { shift; "$@"; return $?; }; '
                'verify_sync_operation_result'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertIn("root-verified:AGENTS.md", normalized_output)
            self.assertIn("agent-profile-verified:reviewer", normalized_output)
            self.assertIn("routing-verified", normalized_output)
            self.assertIn("Fast install/update verification passed", normalized_output)
            self.assertNotIn("unexpected-full-skill-checksum", normalized_output)

    def test_full_post_sync_verification_mode_can_delegate_to_full_checksum_sweep(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'CODEX_SYNC_POST_SYNC_VERIFICATION_MODE=full; '
                'verify_pack_checksums() { printf "full-post-sync-verification\n" >&2; return 0; }; '
                'verify_sync_operation_result'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertIn("full-post-sync-verification", normalized_output)

    def test_apply_repo_managed_changes_repairs_config_wiring_drift_even_without_repo_file_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'ensure_sync_runtime_prerequisites() { return 0; }; '
                'seed_default_local_home_agent_overrides() { return 0; }; '
                'pack_is_installed() { return 0; }; '
                'collect_changed_skills_parallel() { return 0; }; '
                'collect_changed_agent_profile_names() { return 0; }; '
                'list_removed_repo_managed_skill_names() { return 0; }; '
                'list_removed_repo_managed_agent_profile_names() { return 0; }; '
                'root_guidance_files_need_update() { return 1; }; '
                'managed_config_wiring_needs_update() { return 0; }; '
                'sync_codex_delta_update() { printf "delta:%s|%s\n" "$1" "$2"; return 0; }; '
                'refresh_bootstrap_entry_script_from_repo() { return 0; }; '
                'apply_repo_managed_changes'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            normalized_output = strip_ansi(completed_process.stdout + completed_process.stderr)
            self.assertIn("config_refresh=true", normalized_output)
            self.assertIn("delta:false|true", normalized_output)
            self.assertNotIn("Installed skill pack is already up to date", normalized_output)

    def test_root_guidance_drift_detection_uses_direct_file_compare_without_md5(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_root = temporary_path / "source"
            target_root = temporary_path / "target"
            source_root.mkdir()
            target_root.mkdir()
            sourced_script_path = write_sync_script_without_main(temporary_path)
            relative_path = "docs/runtime-guardrails-and-memory-protocols.md"
            (source_root / "docs").mkdir()
            (target_root / "docs").mkdir()
            payload = "same content\n"
            (source_root / relative_path).write_text(payload, encoding="utf-8")
            (target_root / relative_path).write_text(payload, encoding="utf-8")
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{source_root}"; '
                f'CODEX_TARGET="{target_root}"; '
                'list_root_guidance_relative_paths() { printf "docs/runtime-guardrails-and-memory-protocols.md\n"; }; '
                'md5_for_file() { printf "unexpected-md5\n" >&2; return 9; }; '
                'set +e; root_guidance_files_need_update; status="$?"; set -e; printf "status=%s\n" "$status"'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertIn("status=1", completed_process.stdout)
            self.assertNotIn("unexpected-md5", completed_process.stdout + completed_process.stderr)

    def test_changed_agent_profile_detection_uses_direct_compare_without_md5(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agent-profiles" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides >/dev/null; '
                'sync_skill_agent_profiles_to_codex >/dev/null; '
                'md5_for_file() { printf "unexpected-md5\n" >&2; return 9; }; '
                'collect_changed_agent_profile_names'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertEqual("", completed_process.stdout.strip())
            self.assertNotIn("unexpected-md5", completed_process.stdout + completed_process.stderr)

    def test_changed_skill_detection_uses_directory_compare_without_md5(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/skills"; '
                'cp -R "$CODEX_SOURCE/reviewer" "$CODEX_TARGET/skills/reviewer"; '
                'printf "\nchanged\n" >> "$CODEX_TARGET/skills/reviewer/SKILL.md"; '
                'list_repo_skill_names() { printf "reviewer\n"; }; '
                'parallel_worker_limit() { printf "1\n"; }; '
                'run_items_in_parallel() { local worker_function_name="$1"; shift; shift; local work_item; for work_item in "$@"; do "$worker_function_name" "$work_item"; done; }; '
                'md5_for_file() { printf "unexpected-md5\n" >&2; return 9; }; '
                'collect_changed_skills_parallel'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertEqual("reviewer", completed_process.stdout.strip())
            self.assertNotIn("unexpected-md5", completed_process.stdout + completed_process.stderr)

    def test_changed_skill_detection_ignores_runtime_noise_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/skills"; '
                'cp -R "$CODEX_SOURCE/reviewer" "$CODEX_TARGET/skills/reviewer"; '
                'mkdir -p "$CODEX_TARGET/skills/reviewer/tests" "$CODEX_TARGET/skills/reviewer/__pycache__" "$CODEX_TARGET/skills/reviewer/.pytest_cache"; '
                'printf "ignored\n" > "$CODEX_TARGET/skills/reviewer/tests/runtime-noise.txt"; '
                'printf "ignored\n" > "$CODEX_TARGET/skills/reviewer/__pycache__/reviewer.cpython-313.pyc"; '
                'printf "ignored\n" > "$CODEX_TARGET/skills/reviewer/.pytest_cache/state"; '
                'printf "ignored\n" > "$CODEX_TARGET/skills/reviewer/runtime-noise.pyc"; '
                'list_repo_skill_names() { printf "reviewer\n"; }; '
                'parallel_worker_limit() { printf "1\n"; }; '
                'run_items_in_parallel() { local worker_function_name="$1"; shift; shift; local work_item; for work_item in "$@"; do "$worker_function_name" "$work_item"; done; }; '
                'md5_for_file() { printf "unexpected-md5\n" >&2; return 9; }; '
                'collect_changed_skills_parallel'
            )
            completed_process = run_bash(command)
            self.assertEqual(0, completed_process.returncode, completed_process.stdout + completed_process.stderr)
            self.assertEqual("", completed_process.stdout.strip())
            self.assertNotIn("unexpected-md5", completed_process.stdout + completed_process.stderr)

    def test_parallel_contract_test_runner_discovers_core_targets(self) -> None:
        discovered_targets = discover_contract_test_targets()
        self.assertIn(
            "tests.test_skill_pack_contracts.SkillPackContractTests.test_sync_validate_smoke_passes",
            discovered_targets,
        )
        self.assertIn(
            "ui-design-systems-and-responsive-interfaces/tests/test_design_intelligence.py",
            discovered_targets,
        )

    def test_parallel_contract_test_runner_uses_all_detected_processes_without_workload_estimate(self) -> None:
        self.assertEqual(1, resolve_parallel_worker_limit(target_count=1, detected_process_count=32))
        self.assertEqual(4, resolve_parallel_worker_limit(target_count=4, detected_process_count=32))
        self.assertEqual(
            3,
            resolve_parallel_worker_limit(
                target_count=3,
                requested_worker_count=99,
                detected_process_count=32,
            ),
        )

    def test_parallel_contract_test_runner_uses_all_detected_processes_when_estimated_workload_supports_it(self) -> None:
        self.assertEqual(
            32,
            resolve_parallel_worker_limit(
                target_count=99,
                detected_process_count=32,
                estimated_total_seconds=200.0,
            ),
        )

    def test_parallel_contract_test_runner_limits_default_workers_by_estimated_workload(self) -> None:
        self.assertEqual(
            9,
            resolve_parallel_worker_limit(
                target_count=57,
                detected_process_count=32,
                estimated_total_seconds=43.551,
            ),
        )

    def test_parallel_contract_test_runner_falls_back_to_cpu_count_when_process_count_api_is_missing(self) -> None:
        with mock.patch("tests.parallel_contract_test_runner.os.process_cpu_count", new=None, create=True):
            with mock.patch("tests.parallel_contract_test_runner.os.cpu_count", return_value=5):
                self.assertEqual(5, resolve_parallel_worker_limit(target_count=99))

    def test_repo_validation_ignores_live_reasoning_override_for_root_skill_configs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'printf "model = \"gpt-5.4\"\nmodel_reasoning_effort = \"high\"\n" > "$CODEX_TARGET/config.toml"; '
                'validate_codex_skill_dir "$CODEX_SOURCE/backend-and-data-architecture"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_local_home_agent_override_file_can_pin_fast_model_for_memory_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET" "$(skill_manager_state_directory)"; '
                'cat > "$(skill_manager_local_home_agent_override_file)" <<\'JSON\'\n'
                '{\n'
                '  "memory-status-reporter": {\n'
                '    "model": "gpt-5.4",\n'
                '    "reasoning_effort": "low"\n'
                '  }\n'
                '}\n'
                'JSON\n'
                'sync_codex_home_agent_from_yaml "memory-status-reporter" "$CODEX_SOURCE/memory-status-reporter/agents/openai.yaml" "memory-status-reporter"; '
                'cat "$CODEX_TARGET/agents/memory-status-reporter.toml"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertIn('model = "gpt-5.4"', completed_process.stdout)
            self.assertIn('model_reasoning_effort = "low"', completed_process.stdout)

    def test_skill_agent_profiles_sync_to_codex_home_with_skill_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agents" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides; '
                'while IFS= read -r skill_name; do sync_codex_home_agents_for_skill "$skill_name"; done < <(list_repo_skill_names); '
                'sync_skill_agent_profiles_to_codex; '
                'python3 - "$CODEX_TARGET" <<\'PY\'\n'
                'from pathlib import Path\n'
                'import sys\n'
                'target = Path(sys.argv[1])\n'
                'managed_agent_names = sorted(path.stem for path in (target / "agents").glob("*.toml"))\n'
                'assert len(managed_agent_names) == 12, managed_agent_names\n'
                'for agent_name in managed_agent_names:\n'
                '    for surface_name in ("agents", "agent-profiles"):\n'
                '        toml_text = (target / surface_name / f"{agent_name}.toml").read_text(encoding="utf-8")\n'
                '        assert \"model = \\\"gpt-5.4\\\"\" in toml_text\n'
                '        expected_reasoning = \"low\" if agent_name == \"memory-status-reporter\" else \"medium\"\n'
                '        assert f\"model_reasoning_effort = \\\"{expected_reasoning}\\\"\" in toml_text\n'
                'PY\n'
                "find \"$CODEX_TARGET/agent-profiles\" -maxdepth 1 -type f -name '*.toml' | wc -l; "
               "grep -q '^model = \"gpt-5.4\"$' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q '^model_reasoning_effort = \"medium\"$' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'Do not call tools directly in this runtime; route all tool work through js_repl with codex.tool(...)' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'research_cache.py lookup' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'completion_gate.py check' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'keep the first implementation pass anchored to that named scope' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'Prefer small, reviewable patch batches' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'Do not stop at a workaround that merely appears to pass' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'wait times out' \"$CODEX_TARGET/agents/reviewer.toml\"; "
               "grep -q 'Validate each patch batch before widening scope' \"$CODEX_TARGET/agents/software-development-life-cycle.toml\"; "
               "grep -q 'rollback owner' \"$CODEX_TARGET/agents/cloud-and-devops-expert.toml\"; "
               "grep -q 'abort signal' \"$CODEX_TARGET/agents/cloud-and-devops-expert.toml\"; "
               "grep -q 'hardcoded design values' \"$CODEX_TARGET/agents/ui-design-systems-and-responsive-interfaces.toml\"; "
               "grep -q 'implementation-ready' \"$CODEX_TARGET/agents/ui-design-systems-and-responsive-interfaces.toml\"; "
               "grep -q 'completion note' \"$CODEX_TARGET/agents/ux-research-and-experience-strategy.toml\"; "
               "grep -q 'live testing' \"$CODEX_TARGET/agents/ux-research-and-experience-strategy.toml\"; "
               "grep -q '^model = \"gpt-5.4\"$' \"$CODEX_TARGET/agents/memory-status-reporter.toml\"; "
               "grep -q '^model_reasoning_effort = \"low\"$' \"$CODEX_TARGET/agents/memory-status-reporter.toml\"; "
               'test -f "$CODEX_TARGET/agent-profiles/reviewer.toml"; '
               'test -f "$CODEX_TARGET/agent-profiles/memory-status-reporter.toml"; '
               "grep -q '^model = \"gpt-5.4\"$' \"$CODEX_TARGET/agent-profiles/reviewer.toml\"; "
               "grep -q '^model_reasoning_effort = \"medium\"$' \"$CODEX_TARGET/agent-profiles/reviewer.toml\"; "
               "grep -q 'Do not call tools directly in this runtime; route all tool work through js_repl with codex.tool(...)' \"$CODEX_TARGET/agent-profiles/reviewer.toml\"; "
               "grep -q 'keep the first implementation pass anchored to that named scope' \"$CODEX_TARGET/agent-profiles/reviewer.toml\"; "
               "grep -q 'Prefer small, reviewable patch batches' \"$CODEX_TARGET/agent-profiles/reviewer.toml\"; "
               "grep -q 'Validate each patch batch before widening scope' \"$CODEX_TARGET/agent-profiles/software-development-life-cycle.toml\"; "
               "grep -q 'rollback owner' \"$CODEX_TARGET/agent-profiles/cloud-and-devops-expert.toml\"; "
               "grep -q 'abort signal' \"$CODEX_TARGET/agent-profiles/cloud-and-devops-expert.toml\"; "
               "grep -q 'hardcoded design values' \"$CODEX_TARGET/agent-profiles/ui-design-systems-and-responsive-interfaces.toml\"; "
               "grep -q 'implementation-ready' \"$CODEX_TARGET/agent-profiles/ui-design-systems-and-responsive-interfaces.toml\"; "
               "grep -q 'completion note' \"$CODEX_TARGET/agent-profiles/ux-research-and-experience-strategy.toml\"; "
               "grep -q 'live testing' \"$CODEX_TARGET/agent-profiles/ux-research-and-experience-strategy.toml\"; "
               "grep -q '^model = \"gpt-5.4\"$' \"$CODEX_TARGET/agent-profiles/memory-status-reporter.toml\"; "
               "grep -q '^model_reasoning_effort = \"low\"$' \"$CODEX_TARGET/agent-profiles/memory-status-reporter.toml\"; "
                'test ! -f "$CODEX_TARGET/agent-profiles/default.toml"; '
                'test ! -f "$CODEX_TARGET/agent-profiles/explorer.toml"; '
                'test ! -f "$CODEX_TARGET/agent-profiles/worker.toml"; '
                'test ! -f "$CODEX_TARGET/agent-profiles/architect.toml"; '
                'test ! -f "$CODEX_TARGET/agent-profiles/awaiter.toml"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertIn("12", completed_process.stdout)

    def test_ensure_python_launcher_adds_python3_shim_when_windows_alias_is_unusable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            shim_directory = temporary_path / "python-shims"
            real_python_path = Path(sys.executable).as_posix()
            command = (
                f'source "{sourced_script_path}"; '
                f'shim_directory="{shim_directory}"; '
                'mkdir -p "$shim_directory"; '
                'cat > "$shim_directory/python3" <<\'SH\'\n'
                '#!/usr/bin/env bash\n'
                'echo "Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases." >&2\n'
                'exit 49\n'
                'SH\n'
                'cat > "$shim_directory/python" <<\'SH\'\n'
                '#!/usr/bin/env bash\n'
                f'exec "{real_python_path}" "$@"\n'
                'SH\n'
                'chmod +x "$shim_directory/python3" "$shim_directory/python"; '
                'PATH="$shim_directory:$PATH"; '
                'unset PYTHON_LAUNCHER; '
                'ensure_python_launcher; '
                'type python3; '
                'python3 -c "import sys"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertIn("python3 is a function", completed_process.stdout)

    def test_apply_repo_managed_changes_repairs_missing_skill_agent_profiles_even_without_skill_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
               f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agents" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides >/dev/null; '
                'while IFS= read -r skill_name; do sync_codex_home_agents_for_skill "$skill_name"; done < <(list_repo_skill_names); '
                'sync_skill_agent_profiles_to_codex >/dev/null; '
                'printf "model = \\\"gpt-5.4\\\"\\nmodel_reasoning_effort = \\\"medium\\\"\\n" > "$CODEX_TARGET/agents/memory-status-reporter.toml"; '
                'write_managed_skill_inventory_from_repo; '
                'write_managed_home_agent_inventory_from_repo; '
                'write_managed_agent_profile_inventory_from_repo; '
                'write_install_metadata; '
               'rm -rf "$CODEX_TARGET/agent-profiles"; '
                'collect_changed_skills_parallel() { return 0; }; '
                'list_removed_repo_managed_skill_names() { return 0; }; '
                'root_guidance_files_need_update() { return 1; }; '
                'verify_sync_operation_result() { return 0; }; '
               'apply_repo_managed_changes; '
               'grep -q "^model = \\\"gpt-5.4\\\"$" "$CODEX_TARGET/agents/memory-status-reporter.toml"; '
               'grep -q "^model_reasoning_effort = \\\"low\\\"$" "$CODEX_TARGET/agents/memory-status-reporter.toml"; '
               'test -f "$CODEX_TARGET/agent-profiles/reviewer.toml"; '
               'test -f "$(skill_manager_local_home_agent_override_file)"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_verify_pack_checksums_accepts_synced_skill_agent_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            setup_command = (
                'mkdir -p "$CODEX_TARGET/agents" "$CODEX_TARGET/agent-profiles" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides >/dev/null; '
                'sync_root_guidance_files >/dev/null; '
                'while IFS= read -r skill_name; do '
                'sync_codex_home_agents_for_skill "$skill_name" >/dev/null || exit $?; '
                'done < <(list_repo_skill_names); '
                'sync_skill_agent_profiles_to_codex >/dev/null; '
                'write_install_metadata; '
                'write_managed_agent_profile_inventory_from_repo; '
            )
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                f'{setup_command}'
                'collect_failed_checksum_skill_names_parallel() { return 0; }; '
                'verify_pack_checksums'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertIn("MD5 verified for skill agent profile: reviewer", completed_process.stdout)
            self.assertIn(
                "MD5 verified for skill agent profile: memory-status-reporter",
                completed_process.stdout,
            )

    def test_md5_for_file_normalizes_windows_md5sum_escape_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                'md5sum() { printf "\\\\ABCDEF1234567890ABCDEF1234567890  %s\\n" "$1"; }; '
                'md5_for_file "C:\\Users\\Example\\agent-profiles\\reviewer.toml"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertEqual("abcdef1234567890abcdef1234567890", completed_process.stdout.strip())

    def test_skill_pack_status_is_up_to_date_after_syncing_skill_agent_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            setup_command = (
                'mkdir -p "$CODEX_TARGET/agents" "$CODEX_TARGET/agent-profiles" "$(skill_manager_state_directory)"; '
                'seed_default_local_home_agent_overrides >/dev/null; '
                'sync_root_guidance_files >/dev/null; '
                'while IFS= read -r skill_name; do '
                'sync_codex_home_agents_for_skill "$skill_name" >/dev/null || exit $?; '
                'done < <(list_repo_skill_names); '
                'sync_skill_agent_profiles_to_codex >/dev/null; '
                'write_install_metadata; '
                'write_managed_agent_profile_inventory_from_repo; '
            )
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                f'{setup_command}'
                'collect_changed_skills_parallel() { return 0; }; '
                'root_guidance_files_need_update() { return 1; }; '
                'list_removed_repo_managed_skill_names() { return 0; }; '
                'list_removed_repo_managed_agent_profile_names() { return 0; }; '
                'status_output="$(summarize_skill_pack_update_status)"; '
                'printf "%s" "$status_output"; '
                'test "$status_output" = "up to date"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_install_seed_populates_memory_writer_fast_lane_without_clobbering_other_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$(skill_manager_state_directory)"; '
                'cat > "$(skill_manager_local_home_agent_override_file)" <<\'JSON\'\n'
                '{\n'
                '  "custom-helper": {\n'
                '    "model": "gpt-5.4"\n'
                '  }\n'
                '}\n'
                'JSON\n'
                'seed_default_local_home_agent_overrides; '
                'cat "$(skill_manager_local_home_agent_override_file)"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            payload = json.loads(completed_process.stdout[completed_process.stdout.index("{"):])
            self.assertEqual({"model": "gpt-5.4"}, payload["custom-helper"])
            self.assertEqual("gpt-5.4", payload["memory-status-reporter"]["model"])
            self.assertEqual("low", payload["memory-status-reporter"]["reasoning_effort"])

    def test_non_memory_managed_agent_overrides_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agents" "$(skill_manager_state_directory)"; '
                'cat > "$(skill_manager_local_home_agent_override_file)" <<\'JSON\'\n'
                '{\n'
                '  "reviewer": {\n'
                '    "model": "gpt-5.4",\n'
                '    "reasoning_effort": "low"\n'
                '  },\n'
                '  "custom-helper": {\n'
                '    "model": "gpt-5.4"\n'
                '  }\n'
                '}\n'
                'JSON\n'
                'sync_codex_home_agent_from_yaml "reviewer" "$CODEX_SOURCE/reviewer/agents/openai.yaml" "reviewer"; '
                'cat "$CODEX_TARGET/agents/reviewer.toml"; '
                'printf "\n===OVERRIDE===\n"; '
                'cat "$(skill_manager_local_home_agent_override_file)"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            reviewer_toml_text, override_text = completed_process.stdout.split("===OVERRIDE===", maxsplit=1)
            self.assertIn('model = "gpt-5.4"', reviewer_toml_text)
            self.assertIn('model_reasoning_effort = "medium"', reviewer_toml_text)
            override_payload = json.loads(override_text)
            self.assertEqual("low", override_payload["reviewer"]["reasoning_effort"])
            self.assertEqual({"model": "gpt-5.4"}, override_payload["custom-helper"])

    def test_sync_root_guidance_files_copies_runtime_reference_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'sync_root_guidance_files >/dev/null; '
                'test -f "$CODEX_TARGET/docs/runtime-guardrails-and-memory-protocols.md"; '
                'test -f "$CODEX_TARGET/docs/open-source-memory-patterns.md"; '
                'test -f "$CODEX_TARGET/docs/security-audit-status.md"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_sync_memory_status_home_wiring_preserves_top_level_user_model_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                'model = "gpt-5.4"\n'
                'model_reasoning_effort = "high"\n'
                'approval_policy = "untrusted"\n'
                '[profiles.default]\n'
                'sandbox_mode = "workspace-write"\n'
                'developer_instructions = \'\'\'\n'
                'User-owned top-level instructions stay here.\n'
                '\'\'\'\n'
                '[agents.custom-helper]\n'
                'description = "User-owned custom helper"\n'
                'config_file = "agents/custom-helper.toml"\n'
                'EOF\n'
                'sync_memory_status_reporter_home_wiring >/dev/null; '
                'python3 - "$CODEX_TARGET/config.toml" <<\'PY\'\n'
                'from pathlib import Path\n'
                'import sys\n'
                'config_text = Path(sys.argv[1]).read_text(encoding="utf-8")\n'
                'assert \"model = \\\"gpt-5.4\\\"\" in config_text\n'
                'assert \"model_reasoning_effort = \\\"high\\\"\" in config_text\n'
                'assert \"approval_policy = \\\"untrusted\\\"\" in config_text\n'
                'assert \"[profiles.default]\\n\" in config_text\n'
                'assert \"sandbox_mode = \\\"workspace-write\\\"\" in config_text\n'
                'assert \"[agents.custom-helper]\\n\" in config_text\n'
                'assert \"description = \\\"User-owned custom helper\\\"\" in config_text\n'
                'assert \"Managed skill-pack routing:\" in config_text\n'
                'assert \"Route to git-expert for repository-state, branching, and recovery work.\" in config_text\n'
                'assert \"Use software-development-life-cycle when the work is mainly sequencing, cross-domain planning, or architecture framing.\" in config_text\n'
                'assert \"[agents.memory-status-reporter]\" in config_text\n'
                'PY'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_sync_home_agent_updates_config_section_for_managed_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agents"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                'model = "gpt-5.4"\n'
                'developer_instructions = \'\'\'\n'
                'User-owned top-level instructions.\n'
                '\'\'\'\n'
                '[agents.custom-helper]\n'
                'description = "User-owned custom helper"\n'
                'config_file = "agents/custom-helper.toml"\n'
                'EOF\n'
                'sync_codex_home_agent_from_yaml "reviewer" "$CODEX_SOURCE/reviewer/agents/openai.yaml" "reviewer" >/dev/null; '
                'python3 - "$CODEX_TARGET/config.toml" <<\'PY\'\n'
                'from pathlib import Path\n'
                'import sys\n'
                'config_text = Path(sys.argv[1]).read_text(encoding="utf-8")\n'
                'assert "[agents.custom-helper]\\n" in config_text\n'
                'assert "[agents.reviewer]\\n" in config_text\n'
                'assert "description = \\\"Final code and PRD production-readiness reviewer\\\"" in config_text\n'
                'assert "config_file = \\\"agents/reviewer.toml\\\"" in config_text\n'
                'PY'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_remove_home_agent_installation_prunes_managed_config_section_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agents" "$CODEX_TARGET/agent-profiles"; '
                'printf "model = \\\"gpt-5.4\\\"\n" > "$CODEX_TARGET/agents/reviewer.toml"; '
                'printf "model = \\\"gpt-5.4\\\"\n" > "$CODEX_TARGET/agent-profiles/reviewer.toml"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                'developer_instructions = \'\'\'\n'
                'User-owned top-level instructions.\n'
                '\'\'\'\n'
                '[agents.reviewer]\n'
                'description = "Managed reviewer section"\n'
                'config_file = "agents/reviewer.toml"\n'
                '\n'
                '[agents.custom-helper]\n'
                'description = "User-owned custom helper"\n'
                'config_file = "agents/custom-helper.toml"\n'
                'EOF\n'
                'remove_home_agent_installation "reviewer" "reviewer"; '
                'python3 - "$CODEX_TARGET/config.toml" <<\'PY\'\n'
                'from pathlib import Path\n'
                'import sys\n'
                'config_text = Path(sys.argv[1]).read_text(encoding="utf-8")\n'
                'assert "[agents.reviewer]" not in config_text\n'
                'assert "[agents.custom-helper]\\n" in config_text\n'
                'PY\n'
                'test ! -f "$CODEX_TARGET/agents/reviewer.toml"; '
                'test ! -f "$CODEX_TARGET/agent-profiles/reviewer.toml"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_verify_home_agent_config_sections_match_repo_after_home_agent_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/agents" "$CODEX_TARGET/agent-profiles" "$CODEX_TARGET"; '
                'while IFS= read -r skill_name; do sync_codex_home_agents_for_skill "$skill_name" >/dev/null || exit $?; done < <(list_repo_skill_names); '
                'sync_memory_status_reporter_home_wiring >/dev/null; '
                'verify_home_agent_config_sections_match_repo'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_strip_managed_config_routing_instructions_preserves_user_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                'developer_instructions = \'\'\'\n'
                'User-owned top-level instructions stay here.\n'
                'Managed skill-pack routing:\n'
                '- Route directly to the primary domain skill when the task clearly belongs to one surface.\n'
                'Managed skill-pack routing end.\n'
                '\'\'\'\n'
                'EOF\n'
                'strip_managed_config_routing_instructions; '
                'python3 - "$CODEX_TARGET/config.toml" <<\'PY\'\n'
                'from pathlib import Path\n'
                'import sys\n'
                'config_text = Path(sys.argv[1]).read_text(encoding="utf-8")\n'
                'assert "User-owned top-level instructions stay here." in config_text\n'
                'assert "Managed skill-pack routing:" not in config_text\n'
                'PY'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_prune_repo_managed_installation_noise_removes_tests_and_caches_from_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/tests/__pycache__"; '
                'mkdir -p "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/scripts/__pycache__"; '
                'mkdir -p "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/.pytest_cache"; '
                'printf "ok\n" > "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/SKILL.md"; '
                'printf "runtime\n" > "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py"; '
                'printf "test\n" > "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/tests/test_design_intelligence.py"; '
                'printf "cache\n" > "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/scripts/__pycache__/design_intelligence.cpython-313.pyc"; '
                'printf "cache\n" > "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/.pytest_cache/state"; '
                'prune_repo_managed_installation_noise; '
                'verify_repo_managed_installation_hygiene; '
                'test ! -e "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/tests"; '
                'test ! -e "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/scripts/__pycache__"; '
                'test ! -e "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/.pytest_cache"; '
                'test -f "$CODEX_TARGET/skills/ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py"'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_sync_validate_smoke_passes_from_absolute_script_path(self) -> None:
        if os.environ.get("CODEX_SKIP_VALIDATE_SMOKE") == "1":
            self.skipTest("Nested validate smoke intentionally skipped to avoid recursion.")

        with tempfile.TemporaryDirectory() as temporary_directory:
            completed_process = run_bash(
                f'bash "{SYNC_SCRIPT_PATH}" validate',
                environment={
                    "CODEX_SKIP_VALIDATE_SMOKE": "1",
                    "CODEX_SKIP_VALIDATE_CONTRACT_TESTS": "1",
                },
                working_directory=Path(temporary_directory),
            )
            self.assertEqual(
                completed_process.returncode,
                0,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertNotIn("[run] contract tests", strip_ansi(completed_process.stdout + completed_process.stderr))

    def test_powershell_validate_smoke_passes_when_available(self) -> None:
        if os.environ.get("CODEX_SKIP_VALIDATE_SMOKE") == "1":
            self.skipTest("Nested validate smoke intentionally skipped to avoid recursion.")

        powershell_path = shutil.which("pwsh") or shutil.which("powershell")
        if powershell_path is None:
            self.skipTest("PowerShell runtime is not available in this environment.")

        completed_process = subprocess.run(
            [
                powershell_path,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REPOSITORY_ROOT / "sync-skills.ps1"),
                "validate",
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "CODEX_SKIP_VALIDATE_SMOKE": "1",
                "CODEX_SKIP_VALIDATE_CONTRACT_TESTS": "1",
            },
        )
        self.assertEqual(
            completed_process.returncode,
            0,
            completed_process.stdout + completed_process.stderr,
        )
        self.assertNotIn(
            "[run] contract tests",
            strip_ansi(completed_process.stdout + completed_process.stderr),
        )


if __name__ == "__main__":
    unittest.main()
