from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_intelligence.py"
CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "design_intelligence_catalog.json"


def load_script_module():
    specification = importlib.util.spec_from_file_location("design_intelligence", SCRIPT_PATH)
    module = importlib.util.module_from_spec(specification)
    assert specification.loader is not None
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


class DesignIntelligenceScriptTests(unittest.TestCase):
    def test_catalog_is_valid_json(self) -> None:
        catalog_payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertIn("product_archetypes", catalog_payload)
        self.assertIn("style_families", catalog_payload)
        self.assertGreater(len(catalog_payload["product_archetypes"]), 3)

    def test_fintech_query_selects_fintech_archetype(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "fintech banking dashboard with secure transfers",
            "--format",
            "json",
        ]
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed_process.stdout)
        self.assertEqual(payload["product_archetype"]["id"], "fintech-product")
        self.assertEqual(payload["style_family"]["id"], "minimal-trust")

    def test_persist_uses_safe_slug_when_project_name_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "wellness clinic booking flow",
                "--persist",
                "--output-dir",
                temporary_directory,
            ]
            completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertIn('"master":', completed_process.stdout)
            master_file_path = Path(temporary_directory) / "docs" / "design-system" / "MASTER.md"
            self.assertTrue(master_file_path.exists())
            master_text = master_file_path.read_text(encoding="utf-8")
            self.assertIn("project-slug: wellness-clinic-booking-flow", master_text)

    def test_page_override_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "ecommerce checkout optimization",
                "--persist",
                "--project-name",
                "Storefront Revamp",
                "--page",
                "Checkout Flow",
                "--output-dir",
                temporary_directory,
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            page_file_path = (
                Path(temporary_directory)
                / "docs"
                / "design-system"
                / "pages"
                / "checkout-flow.md"
            )
            self.assertTrue(page_file_path.exists())
            self.assertIn("Override Guidance", page_file_path.read_text(encoding="utf-8"))

    def test_internal_slug_resolver_uses_fallback(self) -> None:
        design_intelligence_module = load_script_module()
        self.assertEqual(
            design_intelligence_module.resolve_project_slug(None, "Portfolio Refresh"),
            "portfolio-refresh",
        )
        self.assertEqual(
            design_intelligence_module.resolve_project_slug(None, "!!!"),
            "design-system",
        )

    def test_flutter_stack_biases_mobile_recommendation(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "mobile habit tracker companion app with streaks and reminders",
            "--stack",
            "flutter",
            "--format",
            "json",
        ]
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed_process.stdout)
        self.assertEqual(payload["product_archetype"]["id"], "mobile-companion")
        self.assertEqual(payload["style_family"]["id"], "native-mobile-layering")
        self.assertEqual(payload["stack_profile"]["id"], "flutter-mobile")

    def test_direct_messaging_query_selects_messaging_archetype(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "direct messaging mobile app with unread states voice notes and conversation list",
            "--stack",
            "flutter",
            "--format",
            "json",
        ]
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed_process.stdout)
        self.assertEqual(payload["product_archetype"]["id"], "messaging-product")
        self.assertEqual(payload["style_family"]["id"], "conversation-first-clarity")
        self.assertEqual(payload["platform"], "mobile")
        self.assertFalse(payload["needs_clarification"])

    def test_messaging_behavior_is_catalog_driven(self) -> None:
        script_text = SCRIPT_PATH.read_text(encoding="utf-8")
        catalog_payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        messaging_entry = next(
            entry for entry in catalog_payload["product_archetypes"] if entry["id"] == "messaging-product"
        )

        self.assertNotIn('if product_archetype.identifier == "messaging-product"', script_text)
        self.assertIn("professional_polish_checks", messaging_entry)
        self.assertIn("recovery_checks", messaging_entry)
        self.assertIn("verification_checks", messaging_entry)

    def test_query_only_react_native_phrase_selects_correct_stack_profile(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "react native mobile marketplace app",
            "--format",
            "json",
        ]
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed_process.stdout)
        self.assertEqual(payload["stack_profile"]["id"], "react-native-mobile")

    def test_json_output_includes_polish_and_recovery_checks(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "ai workspace for research copilots and prompt reviews",
            "--stack",
            "nextjs",
            "--component-library",
            "shadcn",
            "--format",
            "json",
        ]
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed_process.stdout)
        self.assertEqual(payload["product_archetype"]["id"], "ai-workspace")
        self.assertEqual(payload["stack_profile"]["id"], "nextjs-app-router")
        self.assertIn("Map the design direction onto shadcn primitives instead of forking a second component language.", payload["stack_adaptation_guidance"])
        self.assertIn(
            "Use outcome-specific CTA labels instead of generic verbs such as Submit, Continue, or Learn More.",
            payload["professional_polish_checks"],
        )
        self.assertIn(
            "Preserve entered data and user progress after validation, network, or permission failures.",
            payload["recovery_checks"],
        )
        self.assertIn("target_user", payload["design_intelligence_packet"])
        self.assertIn("trigger", payload["design_intelligence_packet"])
        self.assertIn("primary_surface_model", payload["design_intelligence_packet"])
        self.assertIn("critical_failure_modes", payload["design_intelligence_packet"])
        self.assertIn("benchmark_strategy", payload["design_intelligence_packet"])
        self.assertIn("selection_signals", payload["design_intelligence_packet"])

    def test_low_confidence_query_sets_clarification_flag(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "redesign the app",
            "--format",
            "json",
        ]
        completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed_process.stdout)
        self.assertTrue(payload["needs_clarification"])
        self.assertIn("surface-specific detail", payload["clarification_reason"])
        self.assertNotIn("product_archetype", payload)
        self.assertIn("requested_brief_fields", payload)
        self.assertEqual(
            payload["selection_signals"]["product_archetype"]["meaningful_matched_keywords"],
            [],
        )

    def test_low_confidence_query_cannot_persist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "redesign the app",
                "--persist",
                "--output-dir",
                temporary_directory,
            ]
            completed_process = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(completed_process.returncode, 0)
            self.assertIn("Cannot persist a low-confidence design recommendation.", completed_process.stderr)

    def test_home_like_layout_can_run_with_relative_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_root = Path(temporary_directory) / "ui-design-systems-and-responsive-interfaces"
            scripts_directory = skill_root / "scripts"
            data_directory = skill_root / "data"
            scripts_directory.mkdir(parents=True, exist_ok=True)
            data_directory.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SCRIPT_PATH, scripts_directory / "design_intelligence.py")
            shutil.copy2(CATALOG_PATH, data_directory / "design_intelligence_catalog.json")

            command = [
                sys.executable,
                str(scripts_directory / "design_intelligence.py"),
                "marketing landing page for a product launch",
                "--format",
                "compact",
            ]
            completed_process = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertIn("Marketing Landing Page", completed_process.stdout)


if __name__ == "__main__":
    unittest.main()
