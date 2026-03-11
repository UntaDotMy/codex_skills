from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_store import (
    current_timestamp,
    ensure_memory_scope_layout,
    resolve_memory_scope,
    sanitize_agent_instance,
    sanitize_agent_role,
)


def add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory-base", type=Path, default=Path("~/.codex/memories").expanduser())
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--workstream-key", type=str, default=None)
    parser.add_argument("--agent-instance", type=str, default=None)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")


def add_packet_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workflow-name", default=None)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--constraint", dest="constraints", action="append", default=[])
    parser.add_argument("--relevant-file", dest="relevant_files", action="append", default=[])
    parser.add_argument("--finding", dest="current_findings", action="append", default=[])
    parser.add_argument("--validation", dest="validation_state", action="append", default=[])
    parser.add_argument("--non-goal", dest="non_goals", action="append", default=[])
    parser.add_argument("--expected-output", dest="expected_output", action="append", default=[])
    parser.add_argument("--source-agent-role", default=None)
    parser.add_argument("--source-agent-id", default=None)
    parser.add_argument("--source-agent-instance", default=None)
    parser.add_argument("--target-agent-role", default=None)
    parser.add_argument("--target-agent-id", default=None)
    parser.add_argument("--target-agent-instance", default=None)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build reusable agent handoff packets and manager-brokered feedback packets."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    handoff_parser = subparsers.add_parser(
        "build-handoff",
        help="Create a bounded handoff packet for a spawned sub-agent.",
    )
    add_scope_arguments(handoff_parser)
    add_packet_arguments(handoff_parser)

    feedback_parser = subparsers.add_parser(
        "build-feedback",
        help="Create a manager-brokered feedback packet from one agent lane to another.",
    )
    add_scope_arguments(feedback_parser)
    add_packet_arguments(feedback_parser)
    feedback_parser.add_argument("--feedback", dest="feedback_items", action="append", default=[])
    feedback_parser.add_argument("--request", dest="requests", action="append", default=[])

    readiness_parser = subparsers.add_parser(
        "build-readiness-check",
        help="Create a short readiness packet before reusing a resumed or completed lane.",
    )
    add_scope_arguments(readiness_parser)
    readiness_parser.add_argument("--workflow-name", default=None)
    readiness_parser.add_argument("--source-agent-role", default=None)
    readiness_parser.add_argument("--source-agent-id", default=None)
    readiness_parser.add_argument("--source-agent-instance", default=None)
    readiness_parser.add_argument("--target-agent-role", required=True)
    readiness_parser.add_argument("--target-agent-id", required=True)
    readiness_parser.add_argument("--target-agent-instance", default=None)
    readiness_parser.add_argument(
        "--question",
        default="Please confirm you are ready for the next scoped task and waiting for a fresh packet.",
    )
    readiness_parser.add_argument(
        "--expected-output",
        dest="expected_output",
        action="append",
        default=[],
    )
    readiness_parser.add_argument(
        "--validation",
        dest="validation_state",
        action="append",
        default=[],
    )
    return parser.parse_args()


def save_packet(packet_directory: Path, packet_kind: str, packet_payload: dict) -> Path:
    packet_directory.mkdir(parents=True, exist_ok=True)
    packet_timestamp = packet_payload["created_at"].replace(":", "-")
    packet_file = packet_directory / f"{packet_timestamp}-{packet_kind}.json"
    packet_file.write_text(json.dumps(packet_payload, indent=2) + "\n", encoding="utf-8")
    return packet_file


def build_common_packet_payload(arguments: argparse.Namespace, packet_kind: str, scope) -> dict:
    return {
        "packet_kind": packet_kind,
        "created_at": current_timestamp(),
        "workflow_name": arguments.workflow_name,
        "workspace_slug": scope.workspace_slug,
        "workstream_key": scope.workstream_key,
        "source_agent": {
            "role": sanitize_agent_role(arguments.source_agent_role),
            "agent_id": arguments.source_agent_id,
            "agent_instance": sanitize_agent_instance(arguments.source_agent_instance) or scope.agent_instance,
        },
        "target_agent": {
            "role": sanitize_agent_role(arguments.target_agent_role),
            "agent_id": arguments.target_agent_id,
            "agent_instance": sanitize_agent_instance(arguments.target_agent_instance),
        },
    }


def build_handoff_payload(arguments: argparse.Namespace, scope) -> dict:
    packet_payload = build_common_packet_payload(arguments, "handoff", scope)
    packet_payload.update(
        {
            "objective": arguments.objective,
            "constraints": arguments.constraints,
            "relevant_files": arguments.relevant_files,
            "current_findings": arguments.current_findings,
            "validation_state": arguments.validation_state,
            "non_goals": arguments.non_goals,
            "expected_output": arguments.expected_output,
        }
    )
    return packet_payload


def build_feedback_payload(arguments: argparse.Namespace, scope) -> dict:
    packet_payload = build_common_packet_payload(arguments, "feedback", scope)
    packet_payload.update(
        {
            "objective": arguments.objective,
            "constraints": arguments.constraints,
            "relevant_files": arguments.relevant_files,
            "current_findings": arguments.current_findings,
            "validation_state": arguments.validation_state,
            "non_goals": arguments.non_goals,
            "expected_output": arguments.expected_output,
            "feedback_items": arguments.feedback_items,
            "requests": arguments.requests,
        }
    )
    return packet_payload


def build_readiness_payload(arguments: argparse.Namespace, scope) -> dict:
    packet_payload = {
        "packet_kind": "readiness-check",
        "created_at": current_timestamp(),
        "workflow_name": arguments.workflow_name,
        "workspace_slug": scope.workspace_slug,
        "workstream_key": scope.workstream_key,
        "source_agent": {
            "role": sanitize_agent_role(arguments.source_agent_role),
            "agent_id": arguments.source_agent_id,
            "agent_instance": sanitize_agent_instance(arguments.source_agent_instance) or scope.agent_instance,
        },
        "target_agent": {
            "role": sanitize_agent_role(arguments.target_agent_role),
            "agent_id": arguments.target_agent_id,
            "agent_instance": sanitize_agent_instance(arguments.target_agent_instance),
        },
        "objective": "Confirm the lane is healthy before sending a fresh task packet.",
        "question": arguments.question,
        "validation_state": arguments.validation_state,
        "expected_output": arguments.expected_output
        or ["Reply with a fresh ACK before the next packet is trusted."],
    }
    return packet_payload


def render_markdown(packet_payload: dict) -> str:
    lines = [
        "# Agent Packet",
        f"- Packet kind: {packet_payload['packet_kind']}",
        f"- Created at: {packet_payload['created_at']}",
        f"- Workflow name: {packet_payload.get('workflow_name') or 'none'}",
        f"- Workspace slug: {packet_payload['workspace_slug']}",
        f"- Workstream key: {packet_payload['workstream_key']}",
        "",
        "## Source Agent",
        f"- Role: {packet_payload['source_agent'].get('role') or 'none'}",
        f"- Agent id: {packet_payload['source_agent'].get('agent_id') or 'none'}",
        f"- Agent instance: {packet_payload['source_agent'].get('agent_instance') or 'none'}",
        "",
        "## Target Agent",
        f"- Role: {packet_payload['target_agent'].get('role') or 'none'}",
        f"- Agent id: {packet_payload['target_agent'].get('agent_id') or 'none'}",
        f"- Agent instance: {packet_payload['target_agent'].get('agent_instance') or 'none'}",
        "",
    ]

    for field_name in (
        "objective",
        "question",
        "constraints",
        "relevant_files",
        "current_findings",
        "validation_state",
        "non_goals",
        "expected_output",
        "feedback_items",
        "requests",
    ):
        if field_name not in packet_payload:
            continue
        field_value = packet_payload[field_name]
        lines.append(f"## {field_name.replace('_', ' ').title()}")
        if isinstance(field_value, list):
            if field_value:
                lines.extend(f"- {item}" for item in field_value)
            else:
                lines.append("- none")
        else:
            lines.append(f"- {field_value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    arguments = parse_arguments()
    scope = resolve_memory_scope(
        memory_base=arguments.memory_base,
        workspace_root=arguments.workspace_root,
        workstream_key=arguments.workstream_key,
        agent_instance=arguments.agent_instance,
    )
    ensure_memory_scope_layout(scope)
    packet_directory = scope.workstream_reference_directory / "agent-packets"

    if arguments.command == "build-handoff":
        packet_payload = build_handoff_payload(arguments, scope)
        packet_kind = "handoff"
    elif arguments.command == "build-feedback":
        packet_payload = build_feedback_payload(arguments, scope)
        packet_kind = "feedback"
    elif arguments.command == "build-readiness-check":
        packet_payload = build_readiness_payload(arguments, scope)
        packet_kind = "readiness-check"
    else:
        raise SystemExit(f"Unsupported command: {arguments.command}")

    packet_file = save_packet(packet_directory, packet_kind, packet_payload)
    packet_payload["packet_file"] = str(packet_file)

    if arguments.format == "markdown":
        print(render_markdown(packet_payload), end="")
        return
    print(json.dumps(packet_payload, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
