from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_store import (
    collect_workspace_rollout_matches,
    ensure_memory_scope_layout,
    resolve_memory_scope,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve workspace-scoped memory, workstream lanes, agent lanes, and shared research-cache paths."
    )
    parser.add_argument(
        "--memory-base",
        type=Path,
        default=Path("~/.codex/memories").expanduser(),
        help="Path to the Codex memories directory.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root to scope memory and cache lookups.",
    )
    parser.add_argument(
        "--agent-role",
        type=str,
        default=None,
        help="Optional agent role for role-local memory paths.",
    )
    parser.add_argument(
        "--workstream-key",
        type=str,
        default=None,
        help="Optional workstream or branch key for a narrower memory lane. Defaults to the current branch when available.",
    )
    parser.add_argument(
        "--agent-instance",
        type=str,
        default=None,
        help="Optional agent-instance lane for per-agent notes inside the selected role and workstream.",
    )
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="Create the scoped workspace, workstream, agent, archive, and cache paths if they do not exist yet.",
    )
    parser.add_argument(
        "--max-rollouts",
        type=int,
        default=8,
        help="Maximum number of matching rollout summaries to report.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args()


def render_markdown(scope_payload: dict) -> str:
    lines = [
        "# Memory Scope",
        f"- Workspace root: {scope_payload['workspace_root']}",
        f"- Workspace slug: {scope_payload['workspace_slug']}",
        f"- Workstream key: {scope_payload['workstream_key']}",
        f"- Agent role: {scope_payload['agent_role'] or 'none'}",
        f"- Agent instance: {scope_payload['agent_instance'] or 'none'}",
        "",
        "## Search Order",
    ]
    lines.extend(f"- {path}" for path in scope_payload["search_order"])
    lines.extend(
        [
            "",
            "## Write Targets",
            f"- Workspace memory: {scope_payload['write_targets']['workspace_memory']}",
            f"- Workspace summary: {scope_payload['write_targets']['workspace_summary']}",
            f"- Session state: {scope_payload['write_targets']['session_state']}",
            f"- Working buffer: {scope_payload['write_targets']['working_buffer']}",
            f"- Write-ahead log: {scope_payload['write_targets']['wal']}",
            f"- Spawned-agent registry: {scope_payload['write_targets']['spawned_agent_registry']}",
            f"- Workstream memory: {scope_payload['write_targets']['workstream_memory']}",
            f"- Workstream summary: {scope_payload['write_targets']['workstream_summary']}",
            f"- Research cache: {scope_payload['write_targets']['research_cache']}",
            f"- Archive directory: {scope_payload['write_targets']['archive_directory']}",
            f"- Workspace reference directory: {scope_payload['write_targets']['workspace_reference_directory']}",
            f"- Workstream reference directory: {scope_payload['write_targets']['workstream_reference_directory']}",
        ]
    )
    if scope_payload["write_targets"]["agent_memory"] is not None:
        lines.append(f"- Agent memory: {scope_payload['write_targets']['agent_memory']}")
    if scope_payload["write_targets"]["agent_instance_memory"] is not None:
        lines.append(f"- Agent instance memory: {scope_payload['write_targets']['agent_instance_memory']}")
    lines.extend(
        [
            "",
            "## Matching Rollout Summaries",
        ]
    )
    rollout_matches = scope_payload["matching_rollout_summaries"]
    if rollout_matches:
        lines.extend(f"- {rollout_path}" for rollout_path in rollout_matches)
    else:
        lines.append("- No workspace-matching rollout summaries were found yet.")
    return "\n".join(lines) + "\n"


def main() -> None:
    arguments = parse_arguments()
    scope = resolve_memory_scope(
        memory_base=arguments.memory_base,
        workspace_root=arguments.workspace_root,
        agent_role=arguments.agent_role,
        workstream_key=arguments.workstream_key,
        agent_instance=arguments.agent_instance,
    )
    if arguments.create_missing:
        ensure_memory_scope_layout(scope)

    rollout_matches = collect_workspace_rollout_matches(
        scope.memory_base,
        scope.workspace_root,
        workstream_key=scope.workstream_key,
        agent_instance=scope.agent_instance,
        max_results=arguments.max_rollouts,
    )
    search_order = []
    if scope.agent_instance_memory_file is not None:
        search_order.append(str(scope.agent_instance_memory_file))
    if scope.agent_memory_file is not None:
        search_order.append(str(scope.agent_memory_file))
    search_order.extend(
        [
            str(scope.session_state_file),
            str(scope.working_buffer_file),
            str(scope.workstream_summary_file),
            str(scope.workstream_memory_file),
            str(scope.workstream_reference_directory),
            str(scope.workspace_summary_file),
            str(scope.workspace_memory_file),
            str(scope.workspace_reference_directory),
            str(scope.research_cache_file),
            *(str(rollout_match) for rollout_match in rollout_matches),
            str(scope.global_memory_file),
            str(scope.global_summary_file),
            str(scope.raw_memories_file),
        ]
    )
    scope_payload = {
        "workspace_root": str(scope.workspace_root),
        "workspace_slug": scope.workspace_slug,
        "workstream_key": scope.workstream_key,
        "agent_role": scope.agent_role,
        "agent_instance": scope.agent_instance,
        "search_order": search_order,
        "write_targets": {
            "workspace_memory": str(scope.workspace_memory_file),
            "workspace_summary": str(scope.workspace_summary_file),
            "workstream_memory": str(scope.workstream_memory_file),
            "workstream_summary": str(scope.workstream_summary_file),
            "session_state": str(scope.session_state_file),
            "working_buffer": str(scope.working_buffer_file),
            "wal": str(scope.wal_file),
            "spawned_agent_registry": str(scope.spawned_agent_registry_file),
            "workspace_reference_directory": str(scope.workspace_reference_directory),
            "workstream_reference_directory": str(scope.workstream_reference_directory),
            "agent_memory": None if scope.agent_memory_file is None else str(scope.agent_memory_file),
            "agent_instance_memory": (
                None if scope.agent_instance_memory_file is None else str(scope.agent_instance_memory_file)
            ),
            "research_cache": str(scope.research_cache_file),
            "archive_directory": str(scope.archive_directory),
        },
        "matching_rollout_summaries": [str(rollout_match) for rollout_match in rollout_matches],
    }

    if arguments.format == "markdown":
        print(render_markdown(scope_payload), end="")
        return

    print(json.dumps(scope_payload, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
