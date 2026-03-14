from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}
PYTHON_SUFFIXES = {".py"}
ASSET_SUFFIXES = {".json", ".md", ".toml", ".yaml", ".yml"}
TEXT_SUFFIXES = PYTHON_SUFFIXES | ASSET_SUFFIXES | {".ps1", ".sh", ".txt"}
EXECUTABLE_TEXT_SUFFIXES = {".json", ".ps1", ".py", ".sh", ".toml", ".yaml", ".yml"}
TERMINAL_STATUSES = {"closed", "completed"}


@dataclass(frozen=True)
class GateProblem:
    relative_path: str
    message: str
    line_number: int | None = None

    def render(self) -> str:
        if self.line_number is None:
            return f"{self.relative_path}: {self.message}"
        return f"{self.relative_path}:{self.line_number}: {self.message}"


@dataclass(frozen=True)
class ModuleRecord:
    relative_path: Path
    dotted_name: str
    scope_directory: str
    top_level_scope: str


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repo-scoped quality gates without external toolchain dependencies.")
    parser.add_argument(
        "gate_name",
        choices=(
            "formatter",
            "lint",
            "types",
            "circular-imports",
            "import-safety",
            "assets",
        ),
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def should_skip_path(relative_path: Path) -> bool:
    return any(path_part in SKIP_DIRECTORY_NAMES for path_part in relative_path.parts)


def iter_repo_files(root_path: Path, suffixes: set[str]) -> list[Path]:
    matching_paths: list[Path] = []
    for candidate_path in root_path.rglob("*"):
        if not candidate_path.is_file():
            continue
        relative_path = candidate_path.relative_to(root_path)
        if should_skip_path(relative_path):
            continue
        if candidate_path.suffix.lower() not in suffixes:
            continue
        matching_paths.append(candidate_path)
    return sorted(matching_paths)


def read_utf8_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def relative_label(root_path: Path, file_path: Path) -> str:
    return file_path.relative_to(root_path).as_posix()


def collect_text_layout_problems(root_path: Path, file_paths: list[Path]) -> list[GateProblem]:
    problems: list[GateProblem] = []
    for file_path in file_paths:
        relative_path = relative_label(root_path, file_path)
        file_text = read_utf8_text(file_path)
        if "\r" in file_text:
            problems.append(GateProblem(relative_path, "contains CRLF line endings"))
        if file_text and not file_text.endswith("\n"):
            problems.append(GateProblem(relative_path, "missing trailing newline"))
        for line_number, line_text in enumerate(file_text.splitlines(), start=1):
            if line_text.rstrip(" ") != line_text:
                problems.append(GateProblem(relative_path, "contains trailing whitespace", line_number))
                break
    return problems


def collect_merge_conflict_problems(root_path: Path, file_paths: list[Path]) -> list[GateProblem]:
    problems: list[GateProblem] = []
    for file_path in file_paths:
        relative_path = relative_label(root_path, file_path)
        for line_number, line_text in enumerate(read_utf8_text(file_path).splitlines(), start=1):
            stripped_line = line_text.strip()
            if stripped_line.startswith("<<<<<<<") or stripped_line == "=======" or stripped_line.startswith(">>>>>>>"):
                problems.append(GateProblem(relative_path, "contains unresolved merge conflict marker", line_number))
                break
    return problems


def parse_python_module(file_path: Path) -> ast.AST:
    return ast.parse(read_utf8_text(file_path), filename=str(file_path))


def collect_python_parse_problems(root_path: Path, python_files: list[Path]) -> tuple[list[ast.AST], list[GateProblem]]:
    syntax_trees: list[ast.AST] = []
    problems: list[GateProblem] = []
    for file_path in python_files:
        try:
            syntax_trees.append(parse_python_module(file_path))
        except SyntaxError as syntax_error:
            problems.append(
                GateProblem(
                    relative_label(root_path, file_path),
                    syntax_error.msg or "syntax error",
                    syntax_error.lineno,
                )
            )
    return syntax_trees, problems


def collect_breakpoint_problems(
    root_path: Path,
    python_files: list[Path],
    syntax_trees: list[ast.AST],
) -> list[GateProblem]:
    problems: list[GateProblem] = []
    for file_path, syntax_tree in zip(python_files, syntax_trees, strict=True):
        relative_path = relative_label(root_path, file_path)
        for syntax_node in ast.walk(syntax_tree):
            if not isinstance(syntax_node, ast.Call):
                continue
            if isinstance(syntax_node.func, ast.Name) and syntax_node.func.id == "breakpoint":
                problems.append(
                    GateProblem(relative_path, "contains breakpoint() call", getattr(syntax_node, "lineno", None))
                )
                break
    return problems


def is_test_file(relative_path: Path) -> bool:
    return "tests" in relative_path.parts or relative_path.name.startswith("test_")


def iter_function_arguments(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    return [
        *function_node.args.posonlyargs,
        *function_node.args.args,
        *function_node.args.kwonlyargs,
    ]


def collect_type_annotation_problems(
    root_path: Path,
    python_files: list[Path],
    syntax_trees: list[ast.AST],
) -> list[GateProblem]:
    problems: list[GateProblem] = []
    for file_path, syntax_tree in zip(python_files, syntax_trees, strict=True):
        relative_path = file_path.relative_to(root_path)
        if is_test_file(relative_path):
            continue
        relative_label_text = relative_path.as_posix()
        for syntax_node in ast.walk(syntax_tree):
            if not isinstance(syntax_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            missing_argument_names = [
                argument.arg
                for argument in iter_function_arguments(syntax_node)
                if argument.arg not in {"self", "cls"} and argument.annotation is None
            ]
            if syntax_node.args.vararg is not None and syntax_node.args.vararg.annotation is None:
                missing_argument_names.append(syntax_node.args.vararg.arg)
            if syntax_node.args.kwarg is not None and syntax_node.args.kwarg.annotation is None:
                missing_argument_names.append(syntax_node.args.kwarg.arg)
            if missing_argument_names:
                joined_names = ", ".join(missing_argument_names)
                problems.append(
                    GateProblem(
                        relative_label_text,
                        f"missing argument annotations for {joined_names}",
                        getattr(syntax_node, "lineno", None),
                    )
                )
            if syntax_node.returns is None:
                problems.append(
                    GateProblem(
                        relative_label_text,
                        f"missing return annotation for {syntax_node.name}",
                        getattr(syntax_node, "lineno", None),
                    )
                )
    return problems


def build_module_records(root_path: Path, python_files: list[Path]) -> list[ModuleRecord]:
    module_records: list[ModuleRecord] = []
    for file_path in python_files:
        relative_path = file_path.relative_to(root_path)
        dotted_parts = relative_path.with_suffix("").parts
        if relative_path.name == "__init__.py":
            dotted_parts = relative_path.parent.parts
        dotted_name = ".".join(dotted_parts)
        module_records.append(
            ModuleRecord(
                relative_path=relative_path,
                dotted_name=dotted_name,
                scope_directory=relative_path.parent.as_posix(),
                top_level_scope=relative_path.parts[0] if relative_path.parts else "",
            )
        )
    return module_records


def resolve_import_target(
    source_record: ModuleRecord,
    import_module_name: str,
    level: int,
    dotted_module_map: dict[str, Path],
    sibling_module_map: dict[tuple[str, str], Path],
) -> Path | None:
    if level > 0:
        base_parts = list(source_record.relative_path.parent.parts)
        if level > 1:
            base_parts = base_parts[: len(base_parts) - (level - 1)]
        relative_module_name = ".".join(base_parts + ([import_module_name] if import_module_name else []))
        return dotted_module_map.get(relative_module_name)

    if import_module_name in dotted_module_map:
        return dotted_module_map[import_module_name]

    if "." not in import_module_name:
        return sibling_module_map.get((source_record.scope_directory, import_module_name))

    return dotted_module_map.get(import_module_name)


def build_local_dependency_graph(root_path: Path) -> tuple[dict[Path, set[Path]], list[GateProblem]]:
    python_files = iter_repo_files(root_path, PYTHON_SUFFIXES)
    syntax_trees, parse_problems = collect_python_parse_problems(root_path, python_files)
    if parse_problems:
        return {}, parse_problems

    module_records = build_module_records(root_path, python_files)
    dotted_module_map = {
        module_record.dotted_name: module_record.relative_path
        for module_record in module_records
        if module_record.dotted_name
    }
    sibling_module_map = {
        (module_record.scope_directory, module_record.relative_path.stem): module_record.relative_path
        for module_record in module_records
    }
    dependency_graph: dict[Path, set[Path]] = {module_record.relative_path: set() for module_record in module_records}

    for module_record, syntax_tree in zip(module_records, syntax_trees, strict=True):
        for syntax_node in ast.walk(syntax_tree):
            if isinstance(syntax_node, ast.Import):
                for alias in syntax_node.names:
                    target_path = resolve_import_target(
                        module_record,
                        alias.name,
                        0,
                        dotted_module_map,
                        sibling_module_map,
                    )
                    if target_path is not None and target_path != module_record.relative_path:
                        dependency_graph[module_record.relative_path].add(target_path)
            elif isinstance(syntax_node, ast.ImportFrom):
                target_path = resolve_import_target(
                    module_record,
                    syntax_node.module or "",
                    syntax_node.level,
                    dotted_module_map,
                    sibling_module_map,
                )
                if target_path is not None and target_path != module_record.relative_path:
                    dependency_graph[module_record.relative_path].add(target_path)

    return dependency_graph, []


def detect_cycle(dependency_graph: dict[Path, set[Path]]) -> list[Path] | None:
    visited_states: dict[Path, str] = {}
    traversal_stack: list[Path] = []

    def visit(node_path: Path) -> list[Path] | None:
        node_state = visited_states.get(node_path)
        if node_state == "active":
            cycle_start_index = traversal_stack.index(node_path)
            return traversal_stack[cycle_start_index:] + [node_path]
        if node_state == "complete":
            return None

        visited_states[node_path] = "active"
        traversal_stack.append(node_path)
        for dependency_path in sorted(dependency_graph.get(node_path, set())):
            detected_cycle = visit(dependency_path)
            if detected_cycle is not None:
                return detected_cycle
        traversal_stack.pop()
        visited_states[node_path] = "complete"
        return None

    for module_path in sorted(dependency_graph):
        detected_cycle = visit(module_path)
        if detected_cycle is not None:
            return detected_cycle
    return None


def collect_circular_import_problems(root_path: Path) -> list[GateProblem]:
    dependency_graph, parse_problems = build_local_dependency_graph(root_path)
    if parse_problems:
        return parse_problems
    detected_cycle = detect_cycle(dependency_graph)
    if detected_cycle is None:
        return []
    cycle_text = " -> ".join(module_path.as_posix() for module_path in detected_cycle)
    return [GateProblem(detected_cycle[0].as_posix(), f"detected local import cycle: {cycle_text}")]


def collect_import_safety_problems(root_path: Path) -> list[GateProblem]:
    dependency_graph, parse_problems = build_local_dependency_graph(root_path)
    if parse_problems:
        return parse_problems

    problems: list[GateProblem] = []
    for source_path, target_paths in dependency_graph.items():
        source_top_level = source_path.parts[0] if source_path.parts else ""
        if source_top_level == "tests":
            continue
        for target_path in sorted(target_paths):
            target_top_level = target_path.parts[0] if target_path.parts else ""
            if target_top_level == source_top_level:
                continue
            problems.append(
                GateProblem(
                    source_path.as_posix(),
                    f"cross-scope import reaches {target_path.as_posix()}",
                )
            )
    return problems


def collect_asset_parse_problems(root_path: Path, asset_files: list[Path]) -> list[GateProblem]:
    problems: list[GateProblem] = []
    for file_path in asset_files:
        suffix = file_path.suffix.lower()
        relative_path = relative_label(root_path, file_path)
        file_text = read_utf8_text(file_path)
        try:
            if suffix == ".json":
                json.loads(file_text)
            elif suffix == ".toml":
                tomllib.loads(file_text)
        except Exception as parsing_error:
            problems.append(GateProblem(relative_path, f"failed to parse {suffix}: {parsing_error}"))
    return problems


def run_formatter_gate(root_path: Path) -> list[GateProblem]:
    return collect_text_layout_problems(root_path, iter_repo_files(root_path, PYTHON_SUFFIXES))


def run_lint_gate(root_path: Path) -> list[GateProblem]:
    python_files = iter_repo_files(root_path, PYTHON_SUFFIXES)
    syntax_trees, parse_problems = collect_python_parse_problems(root_path, python_files)
    return (
        parse_problems
        + collect_breakpoint_problems(root_path, python_files, syntax_trees)
        + collect_merge_conflict_problems(root_path, iter_repo_files(root_path, EXECUTABLE_TEXT_SUFFIXES))
    )


def run_types_gate(root_path: Path) -> list[GateProblem]:
    python_files = iter_repo_files(root_path, PYTHON_SUFFIXES)
    syntax_trees, parse_problems = collect_python_parse_problems(root_path, python_files)
    return parse_problems + collect_type_annotation_problems(root_path, python_files, syntax_trees)


def run_assets_gate(root_path: Path) -> list[GateProblem]:
    asset_files = iter_repo_files(root_path, ASSET_SUFFIXES)
    return collect_text_layout_problems(root_path, asset_files) + collect_asset_parse_problems(root_path, asset_files)


def main() -> int:
    arguments = parse_arguments()
    root_path = arguments.root.expanduser().resolve()

    if arguments.gate_name == "formatter":
        problems = run_formatter_gate(root_path)
    elif arguments.gate_name == "lint":
        problems = run_lint_gate(root_path)
    elif arguments.gate_name == "types":
        problems = run_types_gate(root_path)
    elif arguments.gate_name == "circular-imports":
        problems = collect_circular_import_problems(root_path)
    elif arguments.gate_name == "import-safety":
        problems = collect_import_safety_problems(root_path)
    elif arguments.gate_name == "assets":
        problems = run_assets_gate(root_path)
    else:
        raise SystemExit(f"Unsupported gate: {arguments.gate_name}")

    if not problems:
        print(f"PASS {arguments.gate_name}")
        return 0

    for problem in problems:
        print(problem.render(), file=sys.stderr)
    print(f"FAIL {arguments.gate_name}: {len(problems)} problem(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
