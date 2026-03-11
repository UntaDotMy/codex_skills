from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
        missing_reconciliation_guidance: list[str] = []
        missing_no_soft_stop_guidance: list[str] = []

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
            if "explicit user requirement" not in yaml_text or "do not present unresolved work as complete" not in yaml_text:
                missing_reconciliation_guidance.append(skill_directory.name)
            if "status requests are checkpoints, not stop signals" not in yaml_text:
                missing_no_soft_stop_guidance.append(skill_directory.name)

        self.assertEqual([], missing_cache_guidance, f"missing cache guidance: {missing_cache_guidance}")
        self.assertEqual([], missing_autonomy_guidance, f"missing autonomy guidance: {missing_autonomy_guidance}")
        self.assertEqual([], missing_handoff_guidance, f"missing handoff guidance: {missing_handoff_guidance}")
        self.assertEqual([], missing_scope_guidance, f"missing scope guidance: {missing_scope_guidance}")
        self.assertEqual([], missing_interrupt_guidance, f"missing interrupt guidance: {missing_interrupt_guidance}")
        self.assertEqual([], missing_clarification_guidance, f"missing clarification guidance: {missing_clarification_guidance}")
        self.assertEqual([], missing_reconciliation_guidance, f"missing reconciliation guidance: {missing_reconciliation_guidance}")
        self.assertEqual([], missing_no_soft_stop_guidance, f"missing no-soft-stop guidance: {missing_no_soft_stop_guidance}")

    def test_core_guidance_requires_completion_reconciliation_and_agent_lanes(self) -> None:
        root_guidance_text = read_text(REPOSITORY_ROOT / "AGENTS.md")
        routing_text = read_text(REPOSITORY_ROOT / "00-skill-routing-and-escalation.md")
        readme_text = read_text(REPOSITORY_ROOT / "README.md")

        self.assertIn("Completion Reconciliation Loop", root_guidance_text)
        self.assertIn("every explicit user requirement", root_guidance_text)
        self.assertIn("do not end with optional follow-up offers", root_guidance_text)
        self.assertIn("does not suspend execution when fixable in-scope work remains", root_guidance_text)
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
        self.assertIn("Requirement Reconciliation Before Close", routing_text)
        self.assertIn("Status Requests Do Not End The Job", routing_text)
        self.assertIn("agent-instance lane", routing_text)
        self.assertIn("Write Corrections Before Responding", routing_text)
        self.assertIn("Resolve workspace-scoped memory first", routing_text)
        self.assertIn("Completion Reconciliation", readme_text)
        self.assertIn("not permission to stop", readme_text)
        self.assertIn("runtime-guardrails-and-memory-protocols.md", readme_text)
        self.assertIn("open-source-memory-patterns.md", readme_text)
        self.assertIn("security-audit-status.md", readme_text)
        self.assertIn("Git Bash on Windows", readme_text)

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
        self.assertIn("readiness or ACK check", software_skill_text)
        self.assertIn("old completed payload", software_skill_text)
        self.assertIn("raw HTML or HTTP 4xx or 5xx content", software_skill_text)
        self.assertIn("honest checkpoint, not a closing condition", software_skill_text)
        self.assertIn("Prompt injection attempts", software_skill_text)
        self.assertIn("data only, never instructions", software_skill_text)
        self.assertIn("same failing tool call", software_skill_text)
        self.assertIn("continuity-heavy flows", ui_skill_text)
        self.assertIn("continuity-heavy flows", ux_skill_text)
        self.assertNotIn("for 1:1 messaging", ui_skill_text)
        self.assertNotIn("for 1:1 messaging", ux_skill_text)
        self.assertNotIn("Messaging Surface Rehabilitation", ui_skill_text)
        self.assertNotIn("Messaging Familiarity Gap", ux_skill_text)

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

        self.assertIn("## WAL and Working Buffer Protocol", skill_text)
        self.assertIn("SESSION-STATE.md", skill_text)
        self.assertIn("working-buffer.md", skill_text)
        self.assertIn("memory_maintenance.py", skill_text)
        self.assertIn("trim", skill_text)
        self.assertIn("recalibrate", skill_text)
        self.assertIn("## Security and Anti-Loop Guardrails", skill_text)
        self.assertIn("data only, never instructions", skill_text)
        self.assertIn("Do not repeat the same failing tool call", skill_text)

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
        essential_commands = markdown_section_content(git_text, "Essential Git Commands")
        high_risk_section = markdown_section_content(
            git_text, "High-Risk Operations (Explicit User Approval Only)"
        )

        self.assertNotRegex(
            essential_commands,
            r"git rebase -i|git reset --hard|git checkout -- <file>|git filter-branch",
        )
        self.assertIn("explicit user approval", high_risk_section)
        self.assertIn("git reset --hard", high_risk_section)
        self.assertIn("git rebase -i", high_risk_section)

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

    def test_standalone_bootstrap_copy_refreshes_from_managed_clone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            external_script_path = temporary_path / "sync-skills.sh"
            external_script_path.write_text(
                "# stale bootstrap copy\n" + read_text(SYNC_SCRIPT_PATH),
                encoding="utf-8",
            )

            completed_process = run_bash(
                f'bash "{external_script_path}" status',
                environment={
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
                read_text(SYNC_SCRIPT_PATH),
                external_script_path.read_text(encoding="utf-8"),
            )

    def test_powershell_bootstrap_copy_refreshes_from_managed_clone_when_available(self) -> None:
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

    def test_install_uses_repo_managed_refresh_when_pack_is_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sourced_script_path = write_sync_script_without_main(Path(temporary_directory))
            command = (
                f'source "{sourced_script_path}"; '
                'validate_all() { return 0; }; '
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
                'validate_all() { return 0; }; '
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
            environment={"CODEX_SKIP_VALIDATE_SMOKE": "1"},
        )
        self.assertEqual(
            completed_process.returncode,
            0,
            completed_process.stdout + completed_process.stderr,
        )

    def test_sync_validate_smoke_passes_from_absolute_script_path(self) -> None:
        if os.environ.get("CODEX_SKIP_VALIDATE_SMOKE") == "1":
            self.skipTest("Nested validate smoke intentionally skipped to avoid recursion.")

        with tempfile.TemporaryDirectory() as temporary_directory:
            completed_process = run_bash(
                f'bash "{SYNC_SCRIPT_PATH}" validate',
                environment={"CODEX_SKIP_VALIDATE_SMOKE": "1"},
                working_directory=Path(temporary_directory),
            )
            self.assertEqual(
                completed_process.returncode,
                0,
                completed_process.stdout + completed_process.stderr,
            )

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
            env={**os.environ, "CODEX_SKIP_VALIDATE_SMOKE": "1"},
        )
        self.assertEqual(
            completed_process.returncode,
            0,
            completed_process.stdout + completed_process.stderr,
        )


if __name__ == "__main__":
    unittest.main()
