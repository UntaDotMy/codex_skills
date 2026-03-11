from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_store import current_timestamp, ensure_memory_scope_layout, resolve_memory_scope


VALID_STATUSES = ("pending", "in_progress", "done", "blocked")


def add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory-base", type=Path, default=Path("~/.codex/memories").expanduser())
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--workstream-key", type=str, default=None)
    parser.add_argument("--agent-instance", type=str, default=None)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track explicit requirements, require explicit blocker reports, and keep closure blocked until every requirement is done."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser(
        "record-requirement",
        help="Create or update one requirement entry in the scoped completion ledger.",
    )
    add_scope_arguments(record_parser)
    record_parser.add_argument("--requirement-id", required=True)
    record_parser.add_argument("--text", required=True)
    record_parser.add_argument("--status", choices=VALID_STATUSES, required=True)
    record_parser.add_argument("--evidence", action="append", default=[])
    record_parser.add_argument("--blocked-reason", default=None, help="Required when --status blocked.")

    check_parser = subparsers.add_parser(
        "check",
        help="Report whether the scoped workstream is actually ready to close.",
    )
    add_scope_arguments(check_parser)

    list_parser = subparsers.add_parser(
        "list",
        help="List all tracked requirements in the scoped completion ledger.",
    )
    add_scope_arguments(list_parser)
    arguments = parser.parse_args()
    if arguments.command == "record-requirement":
        if arguments.status == "blocked":
            if not arguments.blocked_reason or not arguments.blocked_reason.strip():
                parser.error("--blocked-reason is required when --status blocked")
            arguments.blocked_reason = arguments.blocked_reason.strip()
        else:
            arguments.blocked_reason = None
    return arguments


def ledger_path_for_scope(scope) -> Path:
    return scope.workstream_memory_directory / "completion-gate.json"


def load_ledger(ledger_path: Path) -> dict:
    if not ledger_path.exists():
        return {"requirements": []}
    try:
        payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"requirements": []}
    if not isinstance(payload, dict):
        return {"requirements": []}
    requirements = payload.get("requirements")
    if not isinstance(requirements, list):
        payload["requirements"] = []
    return payload


def save_ledger(ledger_path: Path, ledger_payload: dict) -> None:
    ledger_path.write_text(json.dumps(ledger_payload, indent=2) + "\n", encoding="utf-8")


def upsert_requirement(
    ledger_payload: dict,
    *,
    requirement_id: str,
    text: str,
    status: str,
    evidence: list[str],
    blocked_reason: str | None,
) -> dict:
    now = current_timestamp()
    requirements = ledger_payload.setdefault("requirements", [])
    for requirement_entry in requirements:
        if requirement_entry.get("requirement_id") != requirement_id:
            continue
        requirement_entry.update(
            {
                "text": text,
                "status": status,
                "evidence": evidence,
                "blocked_reason": blocked_reason,
                "updated_at": now,
            }
        )
        return requirement_entry

    new_requirement = {
        "requirement_id": requirement_id,
        "text": text,
        "status": status,
        "evidence": evidence,
        "blocked_reason": blocked_reason,
        "recorded_at": now,
        "updated_at": now,
    }
    requirements.append(new_requirement)
    return new_requirement


def summarize_gate(ledger_payload: dict) -> dict:
    requirements = ledger_payload.get("requirements", [])
    pending_requirements = [entry for entry in requirements if entry.get("status") == "pending"]
    in_progress_requirements = [entry for entry in requirements if entry.get("status") == "in_progress"]
    blocked_requirements = [entry for entry in requirements if entry.get("status") == "blocked"]
    done_requirements = [entry for entry in requirements if entry.get("status") == "done"]
    unresolved_requirements = pending_requirements + in_progress_requirements + blocked_requirements
    closure_ready = bool(requirements) and not unresolved_requirements

    next_actions: list[str] = []
    if pending_requirements:
        next_actions.append("Finish every pending requirement before closing the workstream.")
    if in_progress_requirements:
        next_actions.append("Move every in-progress requirement to done or blocked with explicit evidence.")
    if blocked_requirements:
        next_actions.append("A blocker is recorded and closure stays blocked; resolve it before claiming completion.")
    if not requirements:
        next_actions.append("No requirements are recorded yet; capture the explicit user asks before trying to close the workstream.")
    if not next_actions:
        next_actions.append("All tracked requirements are done. The scoped workstream is ready to close.")

    return {
        "requirement_count": len(requirements),
        "done_count": len(done_requirements),
        "pending_count": len(pending_requirements),
        "in_progress_count": len(in_progress_requirements),
        "blocked_count": len(blocked_requirements),
        "closure_ready": closure_ready,
        "unresolved_requirements": unresolved_requirements,
        "next_actions": next_actions,
    }


def render_markdown(payload: dict) -> str:
    lines = ["# Completion Gate"]
    for key in (
        "requirement_count",
        "done_count",
        "pending_count",
        "in_progress_count",
        "blocked_count",
        "closure_ready",
    ):
        if key in payload:
            lines.append(f"- {key.replace('_', ' ').title()}: {payload[key]}")
    for key in ("requirements", "unresolved_requirements", "next_actions"):
        if key not in payload:
            continue
        lines.append(f"## {key.replace('_', ' ').title()}")
        if not payload[key]:
            lines.append("- none")
            continue
        for item in payload[key]:
            if isinstance(item, dict):
                lines.append(f"- {json.dumps(item, ensure_ascii=True, sort_keys=True)}")
            else:
                lines.append(f"- {item}")
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
    ledger_path = ledger_path_for_scope(scope)
    ledger_payload = load_ledger(ledger_path)

    if arguments.command == "record-requirement":
        requirement_entry = upsert_requirement(
            ledger_payload,
            requirement_id=arguments.requirement_id,
            text=arguments.text,
            status=arguments.status,
            evidence=arguments.evidence,
            blocked_reason=arguments.blocked_reason,
        )
        save_ledger(ledger_path, ledger_payload)
        payload = {
            "ledger_path": str(ledger_path),
            "requirement": requirement_entry,
            **summarize_gate(ledger_payload),
        }
    elif arguments.command == "list":
        payload = {
            "ledger_path": str(ledger_path),
            "requirements": ledger_payload.get("requirements", []),
            **summarize_gate(ledger_payload),
        }
    elif arguments.command == "check":
        payload = {
            "ledger_path": str(ledger_path),
            **summarize_gate(ledger_payload),
        }
    else:
        raise SystemExit(f"Unsupported command: {arguments.command}")

    if arguments.format == "markdown":
        print(render_markdown(payload), end="")
        return
    print(json.dumps(payload, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
