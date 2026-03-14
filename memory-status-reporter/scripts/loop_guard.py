from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from memory_store import current_timestamp, ensure_memory_scope_layout, resolve_memory_scope


def add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory-base", type=Path, default=Path("~/.codex/memories").expanduser())
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--workstream-key", type=str, default=None)
    parser.add_argument("--agent-instance", type=str, default=None)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track repeated failure signatures so anti-loop rules can use scoped evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Check whether a failure signature has repeated enough times to require a changed approach.",
    )
    add_scope_arguments(check_parser)
    check_parser.add_argument("--signature", required=True)
    check_parser.add_argument("--threshold", type=int, default=2)

    record_parser = subparsers.add_parser(
        "record-failure",
        help="Record one failing attempt for the scoped workstream.",
    )
    add_scope_arguments(record_parser)
    record_parser.add_argument("--signature", required=True)
    record_parser.add_argument("--tool-name", default=None)
    record_parser.add_argument("--summary", required=True)
    record_parser.add_argument("--hypothesis", default=None)
    record_parser.add_argument("--next-change", default=None)
    record_parser.add_argument("--source", default="local-run")

    resolve_parser = subparsers.add_parser(
        "resolve",
        help="Mark a failure signature resolved after the approach changed or the bug was fixed.",
    )
    add_scope_arguments(resolve_parser)
    resolve_parser.add_argument("--signature", required=True)
    resolve_parser.add_argument("--resolution", required=True)
    return parser.parse_args()


def load_entries(loop_guard_file: Path) -> list[dict]:
    if not loop_guard_file.exists():
        return []
    entries: list[dict] = []
    for raw_line in loop_guard_file.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            parsed_entry = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed_entry, dict):
            entries.append(parsed_entry)
    return entries


def append_entry(loop_guard_file: Path, entry: dict) -> dict:
    existing_text = loop_guard_file.read_text(encoding="utf-8") if loop_guard_file.exists() else ""
    loop_guard_file.write_text(
        f"{existing_text}{json.dumps(entry, ensure_ascii=True, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return entry


def select_active_failures(entries: list[dict], signature: str) -> list[dict]:
    active_failures: list[dict] = []
    for entry in entries:
        if entry.get("signature") != signature:
            continue
        if entry.get("event_type") == "resolved":
            active_failures = []
            continue
        if entry.get("event_type") == "failure":
            active_failures.append(entry)
    return active_failures


def render_markdown(payload: dict) -> str:
    lines = ["# Loop Guard"]
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"## {key.replace('_', ' ').title()}")
            if value:
                lines.extend(f"- {json.dumps(item, ensure_ascii=True, sort_keys=True)}" for item in value)
            else:
                lines.append("- none")
            continue
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines) + "\n"


def main() -> None:
    arguments = parse_arguments()
    scope = resolve_memory_scope(
        memory_base=arguments.memory_base,
        workspace_root=arguments.workspace_root,
        workstream_key=arguments.workstream_key,
        agent_instance=arguments.agent_instance,
    )
    ensure_memory_scope_layout(scope)
    loop_guard_file = scope.workstream_memory_directory / "loop-guard.jsonl"
    if not loop_guard_file.exists():
        loop_guard_file.write_text("", encoding="utf-8")

    if arguments.command == "record-failure":
        payload = append_entry(
            loop_guard_file,
            {
                "recorded_at": current_timestamp(),
                "event_type": "failure",
                "signature": arguments.signature,
                "tool_name": arguments.tool_name,
                "summary": arguments.summary,
                "hypothesis": arguments.hypothesis,
                "next_change": arguments.next_change,
                "source": arguments.source,
                "workstream_key": scope.workstream_key,
                "agent_instance": scope.agent_instance,
            },
        )
    elif arguments.command == "resolve":
        payload = append_entry(
            loop_guard_file,
            {
                "recorded_at": current_timestamp(),
                "event_type": "resolved",
                "signature": arguments.signature,
                "resolution": arguments.resolution,
                "workstream_key": scope.workstream_key,
                "agent_instance": scope.agent_instance,
            },
        )
    elif arguments.command == "check":
        all_entries = load_entries(loop_guard_file)
        active_failures = select_active_failures(all_entries, arguments.signature)
        payload = {
            "signature": arguments.signature,
            "repeat_count": len(active_failures),
            "threshold": arguments.threshold,
            "should_change_approach": len(active_failures) >= arguments.threshold,
            "latest_failures": active_failures[-3:],
            "note": (
                "Change inputs, scope, tool, search terms, or execution order before retrying."
                if len(active_failures) >= arguments.threshold
                else "Retry budget is still available, but record each failed attempt."
            ),
        }
    else:
        raise SystemExit(f"Unsupported command: {arguments.command}")

    if arguments.format == "markdown":
        print(render_markdown(payload), end="")
        return
    print(json.dumps(payload, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
