from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from memory_store import (
    archive_research_cache_entries,
    ensure_memory_scope_layout,
    lookup_research_cache_entries,
    record_research_cache_entry,
    resolve_memory_scope,
    summarize_research_cache_entry,
    update_research_cache_entry,
)


def add_scope_arguments(parser: argparse.ArgumentParser) -> None:
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
        help="Workspace root for cache scoping.",
    )
    parser.add_argument(
        "--agent-role",
        type=str,
        default=None,
        help="Optional agent role for role-local cache entries.",
    )
    parser.add_argument(
        "--workstream-key",
        type=str,
        default=None,
        help="Optional workstream or branch key for a narrower cache lane.",
    )
    parser.add_argument(
        "--agent-instance",
        type=str,
        default=None,
        help="Optional agent-instance lane for per-agent notes attached to cache entries.",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lookup, record, and maintain the freshness-aware research cache."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Search for matching research cache entries.")
    add_scope_arguments(lookup_parser)
    lookup_parser.add_argument("--query", required=True, help="Question or search phrase to match.")
    lookup_parser.add_argument("--max-results", type=int, default=5, help="Maximum number of matches to return.")
    lookup_parser.add_argument(
        "--include-stale",
        action="store_true",
        help="Include stale or superseded cache entries in the results.",
    )
    lookup_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )

    record_parser = subparsers.add_parser("record", help="Create or refresh one research cache entry.")
    add_scope_arguments(record_parser)
    record_parser.add_argument("--question", required=True, help="Reusable question the cache entry answers.")
    record_parser.add_argument("--answer", required=True, help="Concise reusable answer or pattern.")
    record_parser.add_argument(
        "--source",
        dest="sources",
        action="append",
        default=[],
        help="Source URL or citation. Pass multiple times for multiple sources.",
    )
    record_parser.add_argument("--freshness", required=True, help="Freshness guidance for reuse.")
    record_parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        help="Optional search tag. Pass multiple times for multiple tags.",
    )
    record_parser.add_argument("--entry-key", default=None, help="Optional stable key for updates.")
    record_parser.add_argument("--confidence", default=None, help="Optional confidence note.")
    record_parser.add_argument("--note", default=None, help="Optional additional note.")
    record_parser.add_argument(
        "--status",
        choices=("fresh", "stale", "superseded"),
        default="fresh",
        help="Initial cache status.",
    )
    record_parser.add_argument(
        "--reinforcement",
        choices=("neutral", "rewarded", "penalty"),
        default="neutral",
        help="Reinforcement signal for the finding.",
    )

    stale_parser = subparsers.add_parser(
        "mark-stale",
        help="Mark a cache entry stale and give it a penalty reinforcement signal.",
    )
    add_scope_arguments(stale_parser)
    stale_parser.add_argument("--entry-key", required=True, help="Stable cache key to update.")
    stale_parser.add_argument("--reason", required=True, help="Why the entry became stale.")

    reward_parser = subparsers.add_parser(
        "reward",
        help="Promote a cache entry to a rewarded reusable pattern after validation.",
    )
    add_scope_arguments(reward_parser)
    reward_parser.add_argument("--entry-key", required=True, help="Stable cache key to update.")
    reward_parser.add_argument("--note", required=True, help="Validation note for the rewarded entry.")

    archive_parser = subparsers.add_parser(
        "archive-stale",
        help="Move stale or superseded cache entries into the scoped archive lane.",
    )
    add_scope_arguments(archive_parser)
    archive_parser.add_argument(
        "--status",
        dest="statuses",
        action="append",
        default=[],
        choices=("stale", "superseded"),
        help="Status to archive. Pass multiple times to archive more than one status. Defaults to stale and superseded.",
    )

    return parser.parse_args()


def render_markdown_lookup(entries: list[dict]) -> str:
    lines = ["# Research Cache Lookup"]
    if not entries:
        lines.append("- No matching cache entries were found.")
        return "\n".join(lines) + "\n"

    for entry in entries:
        lines.append(f"- {summarize_research_cache_entry(entry)}")
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

    if arguments.command == "lookup":
        cache_entries = lookup_research_cache_entries(
            scope,
            query=arguments.query,
            max_results=arguments.max_results,
            include_stale=arguments.include_stale,
        )
        if arguments.format == "markdown":
            print(render_markdown_lookup(cache_entries), end="")
        else:
            print(json.dumps(cache_entries, indent=2) + "\n", end="")
        return

    ensure_memory_scope_layout(scope)

    if arguments.command == "record":
        cache_entry = record_research_cache_entry(
            scope,
            question=arguments.question,
            answer=arguments.answer,
            sources=arguments.sources,
            freshness=arguments.freshness,
            tags=arguments.tags,
            agent_role=arguments.agent_role,
            agent_instance=arguments.agent_instance,
            status=arguments.status,
            reinforcement=arguments.reinforcement,
            confidence=arguments.confidence,
            note=arguments.note,
            entry_key=arguments.entry_key,
        )
        print(json.dumps(cache_entry, indent=2) + "\n", end="")
        return

    if arguments.command == "mark-stale":
        cache_entry = update_research_cache_entry(
            scope,
            entry_key=arguments.entry_key,
            status="stale",
            reinforcement="penalty",
            note=arguments.reason,
        )
        print(json.dumps(cache_entry, indent=2) + "\n", end="")
        return

    if arguments.command == "reward":
        cache_entry = update_research_cache_entry(
            scope,
            entry_key=arguments.entry_key,
            reinforcement="rewarded",
            note=arguments.note,
        )
        print(json.dumps(cache_entry, indent=2) + "\n", end="")
        return

    if arguments.command == "archive-stale":
        archive_statuses = tuple(arguments.statuses) if arguments.statuses else ("stale", "superseded")
        archived_entries = archive_research_cache_entries(scope, statuses=archive_statuses)
        print(json.dumps(archived_entries, indent=2) + "\n", end="")
        return

    raise SystemExit(f"Unsupported command: {arguments.command}")


if __name__ == "__main__":
    main()
