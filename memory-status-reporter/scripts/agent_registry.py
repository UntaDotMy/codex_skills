from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from memory_store import (
    current_timestamp,
    ensure_memory_scope_layout,
    resolve_memory_scope,
    sanitize_agent_instance,
    sanitize_agent_role,
)


STATUS_PRIORITY = {
    "running": 0,
    "queued": 1,
    "completed": 2,
    "closed": 3,
    "unhealthy": 4,
}
DEFAULT_LOOKUP_STATUSES = ("running", "queued", "completed", "closed")
TERMINAL_STATUSES = ("completed", "closed")


def add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory-base", type=Path, default=Path("~/.codex/memories").expanduser())
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--workstream-key", type=str, default=None)
    parser.add_argument("--agent-instance", type=str, default=None)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track spawned agents by role and workstream so same-role lanes can be reused instead of respawned blindly."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser("register", help="Create or update one spawned-agent record.")
    add_scope_arguments(register_parser)
    register_parser.add_argument("--agent-id", required=True)
    register_parser.add_argument("--agent-role", required=True)
    register_parser.add_argument("--status", required=True, choices=tuple(STATUS_PRIORITY.keys()))
    register_parser.add_argument("--purpose", default=None)
    register_parser.add_argument("--note", default=None)
    register_parser.add_argument(
        "--required",
        action="store_true",
        help="Mark this lane as required for the current workstream so closure checks enforce terminal completion.",
    )

    lookup_parser = subparsers.add_parser("lookup", help="Find the best reusable agent for one role.")
    add_scope_arguments(lookup_parser)
    lookup_parser.add_argument("--agent-role", required=True)
    lookup_parser.add_argument(
        "--status",
        dest="statuses",
        action="append",
        default=[],
        choices=tuple(STATUS_PRIORITY.keys()),
    )
    lookup_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    list_parser = subparsers.add_parser("list", help="List registry entries for the scoped workstream.")
    add_scope_arguments(list_parser)
    list_parser.add_argument("--agent-role", default=None)
    list_parser.add_argument(
        "--status",
        dest="statuses",
        action="append",
        default=[],
        choices=tuple(STATUS_PRIORITY.keys()),
    )
    list_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    status_parser = subparsers.add_parser("set-status", help="Update the status or note for an existing agent id.")
    add_scope_arguments(status_parser)
    status_parser.add_argument("--agent-id", required=True)
    status_parser.add_argument("--status", required=True, choices=tuple(STATUS_PRIORITY.keys()))
    status_parser.add_argument("--note", default=None)

    unhealthy_parser = subparsers.add_parser(
        "mark-unhealthy",
        help="Mark an existing lane unhealthy so future lookup stops reusing it by default.",
    )
    add_scope_arguments(unhealthy_parser)
    unhealthy_parser.add_argument("--agent-id", required=True)
    unhealthy_parser.add_argument("--reason", required=True)

    required_parser = subparsers.add_parser(
        "check-required-completion",
        help="Report whether every required lane in the scoped workstream has reached a terminal status.",
    )
    add_scope_arguments(required_parser)
    required_parser.add_argument("--agent-role", default=None)
    required_parser.add_argument(
        "--require-terminal",
        action="store_true",
        help="Exit non-zero when any required lane is still non-terminal or when none are recorded.",
    )
    required_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    return parser.parse_args()


def load_registry(registry_file: Path) -> list[dict]:
    if not registry_file.exists():
        return []
    raw_text = registry_file.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []
    payload = json.loads(raw_text)
    if not isinstance(payload, list):
        raise SystemExit(f"Spawned-agent registry must be a JSON list: {registry_file}")
    return [entry for entry in payload if isinstance(entry, dict)]


def save_registry(registry_file: Path, entries: list[dict]) -> None:
    registry_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def normalize_statuses(raw_statuses: list[str]) -> tuple[str, ...]:
    return tuple(raw_statuses) if raw_statuses else DEFAULT_LOOKUP_STATUSES


def sort_registry_entries(entries: list[dict]) -> list[dict]:
    return sorted(
        entries,
        key=lambda entry: (
            STATUS_PRIORITY.get(str(entry.get("status", "")).lower(), 99),
            str(entry.get("updated_at", "")),
        ),
    )


def upsert_registry_entry(
    entries: list[dict],
    *,
    agent_id: str,
    agent_role: str,
    workstream_key: str,
    workspace_slug: str,
    status: str,
    purpose: str | None,
    note: str | None,
    agent_instance: str | None,
    required: bool,
) -> dict:
    now = current_timestamp()
    sanitized_role = sanitize_agent_role(agent_role)
    sanitized_instance = sanitize_agent_instance(agent_instance)
    for entry in entries:
        if str(entry.get("agent_id")) == agent_id:
            entry.update(
                {
                    "agent_role": sanitized_role,
                    "workstream_key": workstream_key,
                    "workspace_slug": workspace_slug,
                    "status": status,
                    "purpose": purpose,
                    "note": note,
                    "agent_instance": sanitized_instance,
                    "required": required,
                    "updated_at": now,
                }
            )
            return entry

    new_entry = {
        "agent_id": agent_id,
        "agent_role": sanitized_role,
        "workstream_key": workstream_key,
        "workspace_slug": workspace_slug,
        "status": status,
        "purpose": purpose,
        "note": note,
        "agent_instance": sanitized_instance,
        "required": required,
        "recorded_at": now,
        "updated_at": now,
    }
    entries.append(new_entry)
    return new_entry


def select_registry_entries(
    entries: list[dict],
    *,
    agent_role: str | None,
    statuses: tuple[str, ...],
) -> list[dict]:
    normalized_role = None if agent_role is None else sanitize_agent_role(agent_role)
    normalized_statuses = {status.lower() for status in statuses}
    selected_entries = []
    for entry in entries:
        entry_role = sanitize_agent_role(str(entry.get("agent_role")))
        entry_status = str(entry.get("status", "")).lower()
        if normalized_role is not None and entry_role != normalized_role:
            continue
        if normalized_statuses and entry_status not in normalized_statuses:
            continue
        selected_entries.append(entry)
    return sort_registry_entries(selected_entries)


def render_markdown(entries: list[dict], heading: str) -> str:
    lines = [heading]
    if not entries:
        lines.append("- No matching agent registry entries were found.")
        return "\n".join(lines) + "\n"
    for entry in entries:
        purpose_text = f" | purpose={entry['purpose']}" if entry.get("purpose") else ""
        instance_text = f" | instance={entry['agent_instance']}" if entry.get("agent_instance") else ""
        note_text = f" | note={entry['note']}" if entry.get("note") else ""
        required_text = " | required=true" if entry.get("required") else ""
        lines.append(
            f"- {entry['agent_role']} {entry['agent_id']} status={entry['status']}{purpose_text}{instance_text}{note_text}{required_text}"
        )
    return "\n".join(lines) + "\n"


def summarize_required_completion(entries: list[dict], agent_role: str | None = None) -> dict:
    normalized_role = None if agent_role is None else sanitize_agent_role(agent_role)
    required_entries = []
    for entry in entries:
        if not entry.get("required"):
            continue
        if normalized_role is not None and sanitize_agent_role(str(entry.get("agent_role"))) != normalized_role:
            continue
        required_entries.append(entry)

    blocking_entries = [
        entry
        for entry in required_entries
        if str(entry.get("status", "")).lower() not in TERMINAL_STATUSES
    ]
    closure_ready = bool(required_entries) and not blocking_entries
    next_actions: list[str] = []
    if not required_entries:
        next_actions.append("No required lanes are recorded yet; register required sub-agents before claiming closure.")
    if blocking_entries:
        next_actions.append("Wait again or replace unhealthy required lanes until every required lane reaches completed or closed.")
    if not next_actions:
        next_actions.append("All required lanes are terminal. The workstream is safe to close.")

    return {
        "required_agent_count": len(required_entries),
        "terminal_required_count": len(required_entries) - len(blocking_entries),
        "non_terminal_required_count": len(blocking_entries),
        "closure_ready": closure_ready,
        "non_terminal_required_agents": sort_registry_entries(blocking_entries),
        "next_actions": next_actions,
    }


def main() -> None:
    arguments = parse_arguments()
    scope = resolve_memory_scope(
        memory_base=arguments.memory_base,
        workspace_root=arguments.workspace_root,
        workstream_key=arguments.workstream_key,
        agent_instance=arguments.agent_instance,
    )
    ensure_memory_scope_layout(scope)
    registry_entries = load_registry(scope.spawned_agent_registry_file)

    if arguments.command == "register":
        updated_entry = upsert_registry_entry(
            registry_entries,
            agent_id=arguments.agent_id,
            agent_role=arguments.agent_role,
            workstream_key=scope.workstream_key,
            workspace_slug=scope.workspace_slug,
            status=arguments.status,
            purpose=arguments.purpose,
            note=arguments.note,
            agent_instance=arguments.agent_instance,
            required=arguments.required,
        )
        save_registry(scope.spawned_agent_registry_file, sort_registry_entries(registry_entries))
        print(json.dumps(updated_entry, indent=2) + "\n", end="")
        return

    if arguments.command == "lookup":
        selected_entries = select_registry_entries(
            registry_entries,
            agent_role=arguments.agent_role,
            statuses=normalize_statuses(arguments.statuses),
        )
        best_match = selected_entries[0] if selected_entries else None
        if arguments.format == "markdown":
            print(render_markdown([] if best_match is None else [best_match], "# Agent Registry Lookup"), end="")
        else:
            print(json.dumps(best_match, indent=2) + "\n", end="")
        return

    if arguments.command == "list":
        selected_entries = select_registry_entries(
            registry_entries,
            agent_role=arguments.agent_role,
            statuses=tuple(arguments.statuses),
        )
        if arguments.format == "markdown":
            print(render_markdown(selected_entries, "# Agent Registry Entries"), end="")
        else:
            print(json.dumps(selected_entries, indent=2) + "\n", end="")
        return

    if arguments.command == "check-required-completion":
        payload = {
            "registry_path": str(scope.spawned_agent_registry_file),
            **summarize_required_completion(registry_entries, arguments.agent_role),
        }
        if arguments.format == "markdown":
            print(
                render_markdown(
                    payload["non_terminal_required_agents"],
                    "# Required Agent Completion",
                ),
                end="",
            )
        else:
            print(json.dumps(payload, indent=2) + "\n", end="")
        if arguments.require_terminal and not payload["closure_ready"]:
            raise SystemExit(1)
        return

    if arguments.command in {"set-status", "mark-unhealthy"}:
        new_status = arguments.status if arguments.command == "set-status" else "unhealthy"
        new_note = arguments.note if arguments.command == "set-status" else arguments.reason
        matching_entry = next(
            (entry for entry in registry_entries if str(entry.get("agent_id")) == arguments.agent_id),
            None,
        )
        if matching_entry is None:
            raise SystemExit(f"Agent id not found in registry: {arguments.agent_id}")
        matching_entry["status"] = new_status
        matching_entry["note"] = new_note
        matching_entry["updated_at"] = current_timestamp()
        save_registry(scope.spawned_agent_registry_file, sort_registry_entries(registry_entries))
        print(json.dumps(matching_entry, indent=2) + "\n", end="")
        return

    raise SystemExit(f"Unsupported command: {arguments.command}")


if __name__ == "__main__":
    main()
