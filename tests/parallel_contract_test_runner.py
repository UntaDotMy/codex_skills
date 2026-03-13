from __future__ import annotations

import argparse
import concurrent.futures
import math
import os
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TESTS_PACKAGE_NAME = "tests.test_skill_pack_contracts"
UI_DESIGN_TEST_FILE_PATH = (
    REPOSITORY_ROOT / "ui-design-systems-and-responsive-interfaces" / "tests" / "test_design_intelligence.py"
)
DEFAULT_ESTIMATED_SECONDS_PER_TARGET = 0.764

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


@dataclass(frozen=True)
class ContractTargetResult:
    target_specification: str
    command_arguments: tuple[str, ...]
    completed_process: subprocess.CompletedProcess[str]

    @property
    def succeeded(self) -> bool:
        return self.completed_process.returncode == 0


def iter_unittest_cases(test_suite: unittest.TestSuite):
    for test_item in test_suite:
        if isinstance(test_item, unittest.TestSuite):
            yield from iter_unittest_cases(test_item)
            continue
        yield test_item


def discover_contract_test_targets() -> list[str]:
    loader = unittest.defaultTestLoader
    discovered_suite = loader.loadTestsFromName(TESTS_PACKAGE_NAME)
    discovered_targets = [test_case.id() for test_case in iter_unittest_cases(discovered_suite)]

    if UI_DESIGN_TEST_FILE_PATH.exists():
        discovered_targets.append(UI_DESIGN_TEST_FILE_PATH.relative_to(REPOSITORY_ROOT).as_posix())

    return discovered_targets


def detect_process_count() -> int:
    detected_process_count = getattr(os, "process_cpu_count", None)
    if callable(detected_process_count):
        detected_value = detected_process_count()
        if detected_value:
            return detected_value

    fallback_process_count = os.cpu_count()
    if fallback_process_count:
        return fallback_process_count

    return 1


def resolve_parallel_worker_limit(
    target_count: int,
    requested_worker_count: int | None = None,
    detected_process_count: int | None = None,
    estimated_total_seconds: float | None = None,
) -> int:
    if target_count <= 0:
        return 1

    available_process_count = max(1, detected_process_count or detect_process_count())

    if requested_worker_count is not None:
        normalized_requested_worker_count = max(1, requested_worker_count)
        return min(target_count, available_process_count, normalized_requested_worker_count)

    if estimated_total_seconds is None:
        return min(target_count, available_process_count)

    estimated_worker_limit = max(1, math.ceil(estimated_total_seconds / 5.0))
    return min(target_count, available_process_count, estimated_worker_limit)


def estimate_total_runtime_seconds(target_specifications: list[str]) -> float:
    return len(target_specifications) * DEFAULT_ESTIMATED_SECONDS_PER_TARGET


def build_contract_test_command(target_specification: str) -> tuple[str, ...]:
    relative_target_path = REPOSITORY_ROOT / Path(target_specification)
    if relative_target_path.exists() and relative_target_path.suffix == ".py":
        return (sys.executable, str(relative_target_path))

    return (sys.executable, "-m", "unittest", target_specification)


def run_contract_target(target_specification: str) -> ContractTargetResult:
    command_arguments = build_contract_test_command(target_specification)
    environment = {
        **os.environ,
        "CODEX_SKIP_VALIDATE_SMOKE": os.environ.get("CODEX_SKIP_VALIDATE_SMOKE", "1"),
    }
    completed_process = subprocess.run(
        command_arguments,
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    return ContractTargetResult(
        target_specification=target_specification,
        command_arguments=command_arguments,
        completed_process=completed_process,
    )


def format_result_output(contract_target_result: ContractTargetResult) -> str:
    completed_process = contract_target_result.completed_process
    normalized_command = " ".join(contract_target_result.command_arguments)
    status_label = "PASS" if contract_target_result.succeeded else "FAIL"
    output_sections = [
        f"[{status_label}] {contract_target_result.target_specification}",
        f"command: {normalized_command}",
    ]

    if completed_process.stdout:
        output_sections.append("stdout:")
        output_sections.append(completed_process.stdout.rstrip())

    if completed_process.stderr:
        output_sections.append("stderr:")
        output_sections.append(completed_process.stderr.rstrip())

    return "\n".join(output_sections)


def run_contract_targets_in_parallel(
    target_specifications: list[str],
    worker_limit: int,
) -> list[ContractTargetResult]:
    ordered_results: list[ContractTargetResult | None] = [None] * len(target_specifications)
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_limit) as executor:
        future_by_index = {
            executor.submit(run_contract_target, target_specification): target_index
            for target_index, target_specification in enumerate(target_specifications)
        }
        for future in concurrent.futures.as_completed(future_by_index):
            target_index = future_by_index[future]
            ordered_results[target_index] = future.result()

    return [result for result in ordered_results if result is not None]


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repo contract tests in parallel.")
    parser.add_argument("--workers", type=int, default=None, help="Override the worker count.")
    parser.add_argument("--list-targets", action="store_true", help="Print discovered targets and exit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    target_specifications = discover_contract_test_targets()
    if not target_specifications:
        print("No contract-test targets were discovered.", file=sys.stderr)
        return 1

    if arguments.list_targets:
        for target_specification in target_specifications:
            print(target_specification)
        return 0

    worker_limit = resolve_parallel_worker_limit(
        target_count=len(target_specifications),
        requested_worker_count=arguments.workers,
        estimated_total_seconds=estimate_total_runtime_seconds(target_specifications),
    )
    print(
        f"Running {len(target_specifications)} contract-test target(s) across {worker_limit} worker(s)."
    )

    contract_target_results = run_contract_targets_in_parallel(target_specifications, worker_limit)
    for contract_target_result in contract_target_results:
        print(format_result_output(contract_target_result))

    failed_target_count = sum(1 for result in contract_target_results if not result.succeeded)
    if failed_target_count:
        print(f"{failed_target_count} contract-test target(s) failed.", file=sys.stderr)
        return 1

    print("All contract-test targets passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
