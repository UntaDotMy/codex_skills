from __future__ import annotations

import os
import re
import shutil
import subprocess
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
            if prompt_word_count(yaml_text) > 260:
                over_limit.append(skill_directory.name)

        self.assertEqual([], over_limit, f"overlong prompts: {over_limit}")

    def test_agent_prompts_keep_cache_handoff_and_autonomy_guidance(self) -> None:
        missing_cache_guidance: list[str] = []
        missing_autonomy_guidance: list[str] = []
        missing_handoff_guidance: list[str] = []

        for skill_directory in SKILL_DIRECTORIES:
            yaml_text = read_text(skill_directory / "agents" / "openai.yaml")
            if "freshness-aware research cache" not in yaml_text:
                missing_cache_guidance.append(skill_directory.name)
            if "keep iterating in the same turn" not in yaml_text:
                missing_autonomy_guidance.append(skill_directory.name)
            if "reuse the same-role agent" not in yaml_text or "keep the handoff bounded" not in yaml_text:
                missing_handoff_guidance.append(skill_directory.name)

        self.assertEqual([], missing_cache_guidance, f"missing cache guidance: {missing_cache_guidance}")
        self.assertEqual([], missing_autonomy_guidance, f"missing autonomy guidance: {missing_autonomy_guidance}")
        self.assertEqual([], missing_handoff_guidance, f"missing handoff guidance: {missing_handoff_guidance}")

    def test_core_guidance_requires_lifecycle_scenario_thinking(self) -> None:
        root_guidance_text = read_text(REPOSITORY_ROOT / "AGENTS.md")
        software_skill_text = read_text(REPOSITORY_ROOT / "software-development-life-cycle" / "SKILL.md")
        reviewer_skill_text = read_text(REPOSITORY_ROOT / "reviewer" / "SKILL.md")
        ui_skill_text = read_text(REPOSITORY_ROOT / "ui-design-systems-and-responsive-interfaces" / "SKILL.md")
        ux_skill_text = read_text(REPOSITORY_ROOT / "ux-research-and-experience-strategy" / "SKILL.md")

        self.assertIn("relevant lifecycle scenarios", root_guidance_text)
        self.assertIn("execution contexts users actually depend on", root_guidance_text)
        self.assertIn("lifecycle scenario sweep", software_skill_text)
        self.assertIn("lifecycle, recovery, and local-state scenarios", reviewer_skill_text)
        self.assertIn("continuity-heavy flows", ui_skill_text)
        self.assertIn("continuity-heavy flows", ux_skill_text)
        self.assertNotIn("for 1:1 messaging", ui_skill_text)
        self.assertNotIn("for 1:1 messaging", ux_skill_text)
        self.assertNotIn("Messaging Surface Rehabilitation", ui_skill_text)
        self.assertNotIn("Messaging Familiarity Gap", ux_skill_text)

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


if __name__ == "__main__":
    unittest.main()
