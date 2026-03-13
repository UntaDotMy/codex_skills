from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_skill_pack_contracts import (
    REPOSITORY_ROOT,
    run_bash,
    write_sync_script_without_main,
)


class InstallRepairContractTests(unittest.TestCase):
    def test_pack_is_not_installed_when_repo_managed_agent_config_points_to_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                '[agents.architect]\n'
                'description = "Stale legacy architect alias"\n'
                'config_file = "agents/backend-and-data-architecture.toml"\n'
                'EOF\n'
                'if pack_is_installed; then exit 1; fi'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_pack_is_not_installed_when_explicit_managed_agent_section_points_to_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                '[agents.backend-and-data-architecture]\n'
                'description = "Managed backend agent section"\n'
                'config_file = "agents/backend-and-data-architecture.toml"\n'
                'EOF\n'
                'if pack_is_installed; then exit 1; fi'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )

    def test_install_uses_full_sync_when_only_repo_managed_config_fragments_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            full_sync_marker_path = temporary_path / "full-sync.marker"
            delta_sync_marker_path = temporary_path / "delta-sync.marker"
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                '[agents.architect]\n'
                'description = "Stale legacy architect alias"\n'
                'config_file = "agents/backend-and-data-architecture.toml"\n'
                'EOF\n'
                'validate_sync_operation_prerequisites() { return 0; }; '
                f'sync_codex() {{ : > "{full_sync_marker_path}"; return 0; }}; '
                f'apply_repo_managed_changes() {{ : > "{delta_sync_marker_path}"; return 0; }}; '
                'install_codex'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertTrue(full_sync_marker_path.exists())
            self.assertFalse(delta_sync_marker_path.exists())

    def test_status_keeps_installed_version_clean_for_partial_managed_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sourced_script_path = write_sync_script_without_main(temporary_path)
            command = (
                f'source "{sourced_script_path}"; '
                f'CODEX_SOURCE="{REPOSITORY_ROOT}"; '
                f'CODEX_TARGET="{temporary_path / ".codex"}"; '
                'mkdir -p "$CODEX_TARGET"; '
                'cat > "$CODEX_TARGET/config.toml" <<\'EOF\'\n'
                '[agents.backend-and-data-architecture]\n'
                'description = "Managed backend agent section"\n'
                'config_file = "agents/backend-and-data-architecture.toml"\n'
                'EOF\n'
                'show_status'
            )
            completed_process = run_bash(command)
            self.assertEqual(
                0,
                completed_process.returncode,
                completed_process.stdout + completed_process.stderr,
            )
            self.assertIn("Installed version:           not installed", completed_process.stdout)
            self.assertNotIn("backend-and-data-architecture.toml", completed_process.stdout)


if __name__ == "__main__":
    unittest.main()
