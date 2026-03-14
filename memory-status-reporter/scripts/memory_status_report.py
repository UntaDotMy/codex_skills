from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

sys.dont_write_bytecode = True

from memory_store import (
    collect_workspace_rollout_matches,
    load_research_cache_entries,
    parse_timestamp,
    resolve_memory_scope,
    summarize_research_cache_entry,
)


@dataclass
class RolloutSummary:
    file_path: str
    title: str
    updated_at: datetime
    task_outcomes: list[str]
    reusable_knowledge: list[str]
    rewarded_patterns: list[str]
    research_cache_updates: list[str]
    stale_findings: list[str]
    issues: list[str]


OPEN_MARKERS = (
    "outstanding",
    "pending",
    "blocked",
    "remain",
    "needs user",
    "need user",
    "later steps depend",
    "depends on user",
    "not fixed",
    "not yet",
    "still ",
    "cannot ",
    "can't ",
    "follow-up",
)

RESOLVED_MARKERS = (
    "resolved",
    "fixed",
    "re-added",
    "restored",
    "patched",
    "adjusted",
    "reran",
    "rerun",
    "validated",
    "worked after",
    "switched",
    "unblocked",
)

ACTION_MARKERS = (
    "had to",
    "after ",
    "by ",
    "split ",
    "re-added",
    "restored",
    "patched",
    "adjusted",
    "switched",
)


TOOL_MARKERS = (
    "tool",
    "js_repl",
    "exec_command",
    "write_stdin",
    "apply_patch",
    "spawn_agent",
    "send_input",
    "resume_agent",
    "wait call",
    "command substitution",
    "grep",
    "sed",
    "rg ",
    "python3",
    "shell",
)


def is_tool_issue(issue_text: str) -> bool:
    normalized_issue = issue_text.lower()
    return any(marker in normalized_issue for marker in TOOL_MARKERS)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a human-style memory status report from Codex memory artifacts."
    )
    parser.add_argument(
        "--memory-base",
        type=Path,
        default=Path("~/.codex/memories").expanduser(),
        help="Path to the Codex memories directory.",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Anchor date in YYYY-MM-DD. Defaults to today in the selected timezone.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of trailing calendar days to include ending on --date.",
    )
    parser.add_argument(
        "--timezone",
        type=str,
        default=None,
        help="IANA timezone name. Defaults to the local timezone.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "compact"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output file path.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Optional workspace root for scoped memory and research-cache reporting.",
    )
    parser.add_argument(
        "--agent-role",
        type=str,
        default=None,
        help="Optional agent role for role-local scoped reporting.",
    )
    parser.add_argument(
        "--workstream-key",
        type=str,
        default=None,
        help="Optional workstream or branch key for a narrower reporting lane.",
    )
    parser.add_argument(
        "--agent-instance",
        type=str,
        default=None,
        help="Optional agent-instance lane for per-agent scoped reporting.",
    )
    return parser.parse_args()


def resolve_timezone(timezone_name: str | None) -> ZoneInfo:
    if timezone_name:
        return ZoneInfo(timezone_name)
    local_timezone = datetime.now().astimezone().tzinfo
    if isinstance(local_timezone, ZoneInfo):
        return local_timezone
    local_timezone_name = getattr(local_timezone, "key", None)
    if local_timezone_name:
        return ZoneInfo(local_timezone_name)
    return ZoneInfo("UTC")


def parse_anchor_date(raw_date: str | None, timezone_value: ZoneInfo) -> date:
    if raw_date:
        return date.fromisoformat(raw_date)
    return datetime.now(timezone_value).date()


def parse_iso_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    normalized_value = raw_value.strip().replace("Z", "+00:00")
    try:
        parsed_value = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None
    if parsed_value.tzinfo is None:
        return parsed_value.replace(tzinfo=UTC)
    return parsed_value


def extract_bullets_after_label(lines: list[str], label: str) -> list[str]:
    start_index = None
    for line_index, line in enumerate(lines):
        if line.strip() == label:
            start_index = line_index + 1
            break
    if start_index is None:
        return []

    bullets: list[str] = []
    for line in lines[start_index:]:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith("- "):
            bullets.append(stripped_line[2:].strip())
            continue
        if bullets and (
            stripped_line.startswith("## ")
            or stripped_line.endswith(":")
            or stripped_line.startswith("rollout_slug:")
        ):
            break
        if bullets:
            bullets[-1] = f"{bullets[-1]} {stripped_line}"
    return bullets


def extract_bullets_under_heading(lines: list[str], heading: str) -> list[str]:
    in_heading = False
    bullets: list[str] = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line == heading:
            in_heading = True
            continue
        if in_heading and stripped_line.startswith("## ") and stripped_line != heading:
            break
        if in_heading and stripped_line.startswith("- "):
            bullets.append(stripped_line[2:].strip())
        elif in_heading and bullets and stripped_line and not stripped_line.startswith("#"):
            bullets[-1] = f"{bullets[-1]} {stripped_line}"
    return bullets


def parse_rollout_summary(file_path: Path, timezone_value: ZoneInfo) -> RolloutSummary | None:
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    updated_at_match = re.search(r"^updated_at:\s*(.+)$", text, flags=re.MULTILINE)
    parsed_updated_at = parse_iso_datetime(updated_at_match.group(1) if updated_at_match else None)
    if parsed_updated_at is None:
        file_date_match = re.match(r"(\d{4}-\d{2}-\d{2})", file_path.name)
        if file_date_match is None:
            return None
        fallback_date = date.fromisoformat(file_date_match.group(1))
        parsed_updated_at = datetime.combine(fallback_date, time.min, timezone_value)

    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem

    task_outcomes = [
        match.group(1).strip().lower()
        for match in re.finditer(r"^Outcome:\s*(.+)$", text, flags=re.MULTILINE)
    ]
    reusable_knowledge = extract_bullets_after_label(lines, "Reusable knowledge:")
    rewarded_patterns = extract_bullets_after_label(lines, "Rewarded patterns:")
    research_cache_updates = extract_bullets_after_label(lines, "Research cache updates:")
    stale_findings = extract_bullets_after_label(lines, "Stale findings:")
    issues = extract_bullets_after_label(lines, "Things that did not work / can be improved:")

    return RolloutSummary(
        file_path=str(file_path),
        title=title,
        updated_at=parsed_updated_at.astimezone(timezone_value),
        task_outcomes=task_outcomes,
        reusable_knowledge=reusable_knowledge,
        rewarded_patterns=rewarded_patterns,
        research_cache_updates=research_cache_updates,
        stale_findings=stale_findings,
        issues=issues,
    )


def classify_issue(issue_text: str, all_tasks_succeeded: bool) -> str:
    normalized_issue = issue_text.lower()
    if any(marker in normalized_issue for marker in OPEN_MARKERS):
        return "open"
    if any(marker in normalized_issue for marker in RESOLVED_MARKERS):
        return "resolved"
    if all_tasks_succeeded and any(marker in normalized_issue for marker in ACTION_MARKERS):
        return "resolved"
    return "unclear"


def collect_rollout_summaries(
    memory_base: Path,
    timezone_value: ZoneInfo,
    file_paths: list[Path] | None = None,
) -> list[RolloutSummary]:
    rollout_directory = memory_base / "rollout_summaries"
    if file_paths is None and not rollout_directory.exists():
        return []

    candidate_paths = file_paths if file_paths is not None else sorted(rollout_directory.glob("*.md"))
    summaries: list[RolloutSummary] = []
    for file_path in candidate_paths:
        parsed_summary = parse_rollout_summary(file_path, timezone_value)
        if parsed_summary is not None:
            summaries.append(parsed_summary)

    summaries.sort(key=lambda summary: summary.updated_at)
    return summaries


def collect_window_summaries(
    summaries: list[RolloutSummary],
    window_start: datetime,
    window_end: datetime,
) -> list[RolloutSummary]:
    return [
        summary
        for summary in summaries
        if window_start <= summary.updated_at < window_end
    ]


def collect_user_needs(memory_summary_text: str) -> list[str]:
    lines = memory_summary_text.splitlines()
    needs = []
    for label in (
        "Their recurring priority lanes are:",
        "They consistently prefer:",
        "Collaboration style that works best:",
    ):
        needs.extend(extract_bullets_after_label(lines, label))
    return needs


def collect_general_tips(memory_summary_text: str) -> list[str]:
    return extract_bullets_under_heading(memory_summary_text.splitlines(), "## General Tips")


def collect_memory_learnings(memory_text: str) -> list[str]:
    lines = memory_text.splitlines()
    learnings: list[str] = []
    in_learning_block = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "### learnings":
            in_learning_block = True
            continue
        if in_learning_block and stripped_line.startswith("### ") and stripped_line != "### learnings":
            in_learning_block = False
        if in_learning_block and stripped_line.startswith("- "):
            learnings.append(stripped_line[2:].strip())
    return learnings


def collect_simple_bullets(memory_text: str) -> list[str]:
    return [
        stripped_line[2:].strip()
        for stripped_line in (line.strip() for line in memory_text.splitlines())
        if stripped_line.startswith("- ")
    ]


def read_optional_text(file_path: Path | None) -> str:
    if file_path is None or not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def deduplicate_preserving_order(items: list[str]) -> list[str]:
    seen_items: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        normalized_item = item.strip()
        if not normalized_item or normalized_item in seen_items:
            continue
        seen_items.add(normalized_item)
        unique_items.append(normalized_item)
    return unique_items


def build_recent_context(
    all_summaries: list[RolloutSummary],
    window_start: datetime,
) -> list[str]:
    previous_summaries = [summary for summary in all_summaries if summary.updated_at < window_start]
    if not previous_summaries:
        return []
    latest_summary = previous_summaries[-1]
    context_lines = [
        (
            "No dated rollout summary fell inside the requested window. "
            f"Most recent captured activity was {latest_summary.updated_at.date()} "
            f"from \"{latest_summary.title}.\""
        )
    ]
    for knowledge_item in latest_summary.reusable_knowledge[:2]:
        context_lines.append(
            f"Most recent durable learning: {knowledge_item}"
        )
    return context_lines


def normalize_pattern_key(raw_text: str) -> str:
    normalized_text = raw_text.lower().strip()
    normalized_text = re.sub(r"\s+", " ", normalized_text)
    normalized_text = re.sub(r"[^a-z0-9 ]", "", normalized_text)
    return normalized_text


def classify_research_cache_update(update_text: str) -> str:
    normalized_update = update_text.lower()
    if any(marker in normalized_update for marker in ("stale", "refresh", "refreshed", "expired", "version-sensitive", "date-sensitive")):
        return "refresh"
    if any(marker in normalized_update for marker in ("reused", "cache hit", "reused result", "reapplied", "reused finding")):
        return "reused"
    return "new"


def collect_repeated_penalty_patterns(window_summaries: list[RolloutSummary]) -> list[str]:
    repeated_pattern_counts: dict[str, int] = {}
    repeated_pattern_examples: dict[str, str] = {}

    for summary in window_summaries:
        all_tasks_succeeded = bool(summary.task_outcomes) and all(
            task_outcome == "success" for task_outcome in summary.task_outcomes
        )
        for issue in summary.issues:
            issue_status = classify_issue(issue, all_tasks_succeeded)
            if issue_status == "resolved":
                continue
            normalized_issue = normalize_pattern_key(issue)
            if not normalized_issue:
                continue
            repeated_pattern_counts[normalized_issue] = repeated_pattern_counts.get(normalized_issue, 0) + 1
            repeated_pattern_examples.setdefault(normalized_issue, issue)

    return [
        f"{repeated_pattern_examples[normalized_issue]} (repeated {repeat_count} times)"
        for normalized_issue, repeat_count in repeated_pattern_counts.items()
        if repeat_count > 1
    ]


def compute_daily_growth_units(
    summaries: list[RolloutSummary],
) -> dict[date, int]:
    growth_units_by_day: dict[date, int] = {}
    for summary in summaries:
        all_tasks_succeeded = bool(summary.task_outcomes) and all(
            task_outcome == "success" for task_outcome in summary.task_outcomes
        )
        resolved_issues = sum(
            1
            for issue in summary.issues
            if classify_issue(issue, all_tasks_succeeded) == "resolved"
        )
        day_key = summary.updated_at.date()
        growth_units_by_day[day_key] = growth_units_by_day.get(day_key, 0) + len(summary.reusable_knowledge) + resolved_issues
    return growth_units_by_day


def compute_status(
    summary_count: int,
    failed_tasks: int,
    open_issues: int,
    resolved_issues: int,
    partial_tasks: int,
    unclear_issues: int,
) -> str:
    if summary_count == 0:
        return "Quiet"
    if failed_tasks > 0 or open_issues > resolved_issues:
        return "Needs Attention"
    if partial_tasks > 0 or open_issues > 0 or unclear_issues > 0:
        return "Mixed"
    return "Healthy"


def compute_confidence(summary_count: int, durable_context_count: int) -> str:
    if summary_count >= 2 and durable_context_count >= 3:
        return "High"
    if summary_count >= 1 or durable_context_count >= 3:
        return "Medium"
    return "Low"


def format_percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{(100 * numerator / denominator):.1f}%"


def collect_recent_scoped_cache_entries(
    scoped_cache_entries: list[dict],
    window_start: datetime,
    window_end: datetime,
    timezone_value: ZoneInfo,
) -> list[dict]:
    recent_entries: list[dict] = []
    for entry in scoped_cache_entries:
        updated_at = parse_timestamp(str(entry.get("updated_at") or entry.get("recorded_at")))
        if updated_at is None:
            continue
        localized_updated_at = updated_at.astimezone(timezone_value)
        if window_start <= localized_updated_at < window_end:
            recent_entries.append(entry)
    recent_entries.sort(
        key=lambda entry: parse_timestamp(str(entry.get("updated_at") or entry.get("recorded_at"))) or datetime.min.replace(
            tzinfo=UTC
        )
    )
    return recent_entries


def build_report_payload(
    memory_base: Path,
    anchor_date: date,
    days: int,
    timezone_value: ZoneInfo,
    workspace_root: Path | None = None,
    agent_role: str | None = None,
    workstream_key: str | None = None,
    agent_instance: str | None = None,
) -> dict:
    memory_scope = resolve_memory_scope(
        memory_base=memory_base,
        workspace_root=workspace_root,
        agent_role=agent_role,
        workstream_key=workstream_key,
        agent_instance=agent_instance,
    )
    matching_rollout_paths = (
        collect_workspace_rollout_matches(
            memory_base,
            memory_scope.workspace_root,
            workstream_key=memory_scope.workstream_key,
            agent_instance=memory_scope.agent_instance,
            max_results=64,
        )
        if workspace_root is not None
        else None
    )
    all_summaries = collect_rollout_summaries(memory_base, timezone_value, file_paths=matching_rollout_paths)

    window_end = datetime.combine(anchor_date, time.min, timezone_value) + timedelta(days=1)
    window_start = window_end - timedelta(days=days)
    window_summaries = collect_window_summaries(all_summaries, window_start, window_end)
    scoped_cache_entries = load_research_cache_entries(memory_scope)
    recent_scoped_cache_entries = collect_recent_scoped_cache_entries(
        scoped_cache_entries,
        window_start,
        window_end,
        timezone_value,
    )

    task_outcomes = [
        task_outcome
        for summary in window_summaries
        for task_outcome in summary.task_outcomes
    ]
    successful_tasks = sum(task_outcome == "success" for task_outcome in task_outcomes)
    partial_tasks = sum(task_outcome == "partial" for task_outcome in task_outcomes)
    failed_tasks = len(task_outcomes) - successful_tasks - partial_tasks

    reusable_knowledge = [
        knowledge_item
        for summary in window_summaries
        for knowledge_item in summary.reusable_knowledge
    ]
    rewarded_patterns = [
        rewarded_pattern
        for summary in window_summaries
        for rewarded_pattern in summary.rewarded_patterns
    ]
    research_cache_updates = [
        cache_update
        for summary in window_summaries
        for cache_update in summary.research_cache_updates
    ]
    research_cache_updates.extend(
        summarize_research_cache_entry(cache_entry)
        for cache_entry in recent_scoped_cache_entries
    )
    stale_findings = [
        stale_finding
        for summary in window_summaries
        for stale_finding in summary.stale_findings
    ]
    stale_findings.extend(
        summarize_research_cache_entry(cache_entry)
        for cache_entry in scoped_cache_entries
        if str(cache_entry.get("status", "fresh")).lower() in {"stale", "superseded"}
    )
    repeated_penalty_patterns = collect_repeated_penalty_patterns(window_summaries)
    rewarded_patterns = [
        *rewarded_patterns,
        *(
            summarize_research_cache_entry(cache_entry)
            for cache_entry in recent_scoped_cache_entries
            if str(cache_entry.get("reinforcement", "neutral")).lower() == "rewarded"
        ),
    ]
    repeated_penalty_patterns.extend(
        summarize_research_cache_entry(cache_entry)
        for cache_entry in recent_scoped_cache_entries
        if str(cache_entry.get("reinforcement", "neutral")).lower() == "penalty"
    )

    classified_issues = []
    for summary in window_summaries:
        all_tasks_succeeded = bool(summary.task_outcomes) and all(
            task_outcome == "success" for task_outcome in summary.task_outcomes
        )
        for issue in summary.issues:
            classified_issues.append(
                {
                    "status": classify_issue(issue, all_tasks_succeeded),
                    "text": issue,
                    "title": summary.title,
                    "updated_at": summary.updated_at.date().isoformat(),
                }
            )

    resolved_issues = [issue for issue in classified_issues if issue["status"] == "resolved"]
    open_issues = [issue for issue in classified_issues if issue["status"] == "open"]
    unclear_issues = [issue for issue in classified_issues if issue["status"] == "unclear"]
    resolved_tool_issues = [issue for issue in resolved_issues if is_tool_issue(issue["text"])]
    open_tool_issues = [issue for issue in open_issues if is_tool_issue(issue["text"])]
    unclear_tool_issues = [issue for issue in unclear_issues if is_tool_issue(issue["text"])]
    penalty_patterns = stale_findings + repeated_penalty_patterns
    reused_cache_updates = [
        cache_update
        for cache_update in research_cache_updates
        if classify_research_cache_update(cache_update) == "reused"
    ]
    refreshed_cache_updates = [
        cache_update
        for cache_update in research_cache_updates
        if classify_research_cache_update(cache_update) == "refresh"
    ]

    agent_instance_memory_text = read_optional_text(memory_scope.agent_instance_memory_file)
    agent_memory_text = read_optional_text(memory_scope.agent_memory_file)
    workstream_memory_text = read_optional_text(memory_scope.workstream_memory_file)
    workstream_summary_text = read_optional_text(memory_scope.workstream_summary_file)
    session_state_text = read_optional_text(memory_scope.session_state_file)
    working_buffer_text = read_optional_text(memory_scope.working_buffer_file)
    workspace_memory_text = read_optional_text(memory_scope.workspace_memory_file)
    workspace_summary_text = read_optional_text(memory_scope.workspace_summary_file)
    global_memory_text = read_optional_text(memory_scope.global_memory_file)
    global_summary_text = read_optional_text(memory_scope.global_summary_file)
    session_state_items = [f"Session state: {item}" for item in collect_simple_bullets(session_state_text)[-4:]]
    working_buffer_items = [f"Working buffer: {item}" for item in collect_simple_bullets(working_buffer_text)[-4:]]

    scoped_memory_learnings = deduplicate_preserving_order(
        collect_memory_learnings(agent_instance_memory_text)
        + collect_memory_learnings(agent_memory_text)
        + collect_memory_learnings(workstream_memory_text)
        + collect_memory_learnings(workspace_memory_text)
    )
    memory_learnings = deduplicate_preserving_order(
        scoped_memory_learnings + collect_memory_learnings(global_memory_text)
    )
    user_needs = deduplicate_preserving_order(
        collect_user_needs(workstream_summary_text)
        + collect_user_needs(workspace_summary_text)
        + collect_user_needs(global_summary_text)
    )
    general_tips = deduplicate_preserving_order(
        collect_general_tips(workstream_summary_text)
        + collect_general_tips(workspace_summary_text)
        + collect_general_tips(global_summary_text)
    )
    if not reusable_knowledge:
        reusable_knowledge = scoped_memory_learnings[:]
    else:
        reusable_knowledge = deduplicate_preserving_order(reusable_knowledge + scoped_memory_learnings)
    durable_bank_size = len(memory_learnings) + len(user_needs) + len(general_tips)
    closure_ready = failed_tasks == 0 and partial_tasks == 0 and len(open_issues) == 0 and len(unclear_issues) == 0
    self_healing_actions: list[str] = []
    if partial_tasks > 0:
        self_healing_actions.append(
            "Reconcile every explicit user requirement against evidence before presenting the work as complete."
        )
    if open_issues:
        self_healing_actions.append("Resolve captured open issues before closing the active workstream.")
    if unclear_issues:
        self_healing_actions.append("Clarify unclear issues or upgrade them into explicit validation tasks before finalizing.")
    if stale_findings:
        self_healing_actions.append("Refresh or archive stale research-cache entries before reusing them in future turns.")
    if not self_healing_actions:
        self_healing_actions.append("No automatic self-healing action is pending in the requested window.")

    growth_units = len(reusable_knowledge) + len(resolved_issues)
    growth_units_by_day = compute_daily_growth_units(all_summaries)
    trailing_days = [
        anchor_date - timedelta(days=day_offset)
        for day_offset in range(1, 8)
    ]
    trailing_average = sum(growth_units_by_day.get(trailing_day, 0) for trailing_day in trailing_days) / len(trailing_days)
    momentum_value = None
    if trailing_average > 0:
        momentum_value = 100 * (growth_units / max(days, 1)) / trailing_average

    report_payload = {
        "window_start": window_start.date().isoformat(),
        "window_end": (window_end - timedelta(days=1)).date().isoformat(),
        "days": days,
        "workspace_slug": memory_scope.workspace_slug,
        "workstream_key": memory_scope.workstream_key,
        "agent_role": memory_scope.agent_role,
        "agent_instance": memory_scope.agent_instance,
        "status": compute_status(
            len(window_summaries),
            failed_tasks,
            len(open_issues),
            len(resolved_issues),
            partial_tasks,
            len(unclear_issues),
        ),
        "confidence": compute_confidence(len(window_summaries), durable_bank_size),
        "summary_count": len(window_summaries),
        "task_counts": {
            "total": len(task_outcomes),
            "success": successful_tasks,
            "partial": partial_tasks,
            "failed": failed_tasks,
        },
        "closure_ready": closure_ready,
        "self_healing_actions": self_healing_actions,
        "learning_items": reusable_knowledge,
        "rewarded_patterns": rewarded_patterns,
        "penalty_patterns": penalty_patterns,
        "research_cache": {
            "updates": research_cache_updates,
            "reused": reused_cache_updates,
            "refreshed": refreshed_cache_updates,
            "stale": stale_findings,
        },
        "mistakes": {
            "resolved": resolved_issues,
            "open": open_issues,
            "unclear": unclear_issues,
        },
        "tool_mistakes": {
            "resolved": resolved_tool_issues,
            "open": open_tool_issues,
            "unclear": unclear_tool_issues,
        },
        "user_needs": user_needs,
        "durable_bank_size": durable_bank_size,
        "growth_units": growth_units,
        "task_completion_rate": format_percentage(successful_tasks, len(task_outcomes)),
        "learning_capture_rate": format_percentage(
            sum(bool(summary.reusable_knowledge) for summary in window_summaries),
            len(window_summaries),
        ),
        "mistake_resolution_rate": format_percentage(
            len(resolved_issues),
            len(classified_issues),
        ),
        "tool_mistake_resolution_rate": format_percentage(
            len(resolved_tool_issues),
            len(resolved_tool_issues) + len(open_tool_issues) + len(unclear_tool_issues),
        ),
        "reward_strength": len(rewarded_patterns) + len(reusable_knowledge),
        "penalty_pressure": len(penalty_patterns) + len(open_issues) + len(unclear_issues),
        "cache_reuse_rate": format_percentage(len(reused_cache_updates), len(research_cache_updates)),
        "cache_freshness_risk": len(stale_findings),
        "brain_growth_rate": format_percentage(growth_units, durable_bank_size),
        "learning_momentum": None if momentum_value is None else f"{momentum_value:.1f}%",
        "recent_context": deduplicate_preserving_order(
            session_state_items + working_buffer_items + build_recent_context(all_summaries, window_start)
        ),
        "source_files": {
            "memory": str(memory_base / "MEMORY.md"),
            "memory_summary": str(memory_base / "memory_summary.md"),
            "raw_memories": str(memory_scope.raw_memories_file),
            "rollout_directory": str(memory_base / "rollout_summaries"),
            "workspace_memory": str(memory_scope.workspace_memory_file),
            "workspace_summary": str(memory_scope.workspace_summary_file),
            "workstream_memory": str(memory_scope.workstream_memory_file),
            "workstream_summary": str(memory_scope.workstream_summary_file),
            "session_state": str(memory_scope.session_state_file),
            "working_buffer": str(memory_scope.working_buffer_file),
            "wal": str(memory_scope.wal_file),
            "workspace_reference_directory": str(memory_scope.workspace_reference_directory),
            "workstream_reference_directory": str(memory_scope.workstream_reference_directory),
            "agent_memory": None if memory_scope.agent_memory_file is None else str(memory_scope.agent_memory_file),
            "agent_instance_memory": (
                None if memory_scope.agent_instance_memory_file is None else str(memory_scope.agent_instance_memory_file)
            ),
            "research_cache": str(memory_scope.research_cache_file),
            "matching_rollout_summaries": [
                str(rollout_match)
                for rollout_match in (matching_rollout_paths or [])
            ],
        },
    }
    return report_payload


def render_markdown(report_payload: dict) -> str:
    learning_lines = report_payload["learning_items"][:]
    if not learning_lines:
        learning_lines = report_payload["recent_context"][:]
    if not learning_lines:
        learning_lines = ["No durable learning was captured in the requested window."]
    elif len(learning_lines) > 12:
        remaining_learning_count = len(learning_lines) - 12
        learning_lines = learning_lines[:12] + [
            f"... {remaining_learning_count} more learning item(s) captured in the window."
        ]

    needs_lines = report_payload["user_needs"][:6]
    if not needs_lines:
        needs_lines = ["No recurring user-needs summary is available yet in memory_summary.md."]

    rewarded_pattern_lines = report_payload["rewarded_patterns"][:8]
    if not rewarded_pattern_lines:
        rewarded_pattern_lines = ["No rewarded patterns were captured in the requested window."]

    research_cache_lines: list[str] = []
    if report_payload["research_cache"]["reused"]:
        research_cache_lines.extend(
            f"Reused: {cache_update}" for cache_update in report_payload["research_cache"]["reused"][:6]
        )
    if report_payload["research_cache"]["refreshed"]:
        research_cache_lines.extend(
            f"Refreshed: {cache_update}" for cache_update in report_payload["research_cache"]["refreshed"][:6]
        )
    if report_payload["research_cache"]["stale"]:
        research_cache_lines.extend(
            f"Stale: {cache_update}" for cache_update in report_payload["research_cache"]["stale"][:6]
        )
    if not research_cache_lines:
        research_cache_lines = ["No research-cache updates were captured in the requested window."]

    mistake_lines: list[str] = []
    for status_name in ("resolved", "open", "unclear"):
        items = report_payload["mistakes"][status_name]
        if items:
            for item in items:
                mistake_lines.append(
                    f"{status_name.title()}: {item['text']} ({item['updated_at']} • {item['title']})"
                )
    if not mistake_lines:
        mistake_lines = ["No mistakes were captured in the rollout summaries for this window."]

    tool_mistake_lines: list[str] = []
    for status_name in ("resolved", "open", "unclear"):
        items = report_payload["tool_mistakes"][status_name]
        if items:
            for item in items:
                tool_mistake_lines.append(
                    f"{status_name.title()}: {item['text']} ({item['updated_at']} • {item['title']})"
                )
    if not tool_mistake_lines:
        tool_mistake_lines = ["No tool-use mistakes were captured in the rollout summaries for this window."]

    momentum_value = report_payload["learning_momentum"] or "n/a"

    lines = [
        "# Memory Status Report",
        f"- Window: {report_payload['window_start']} to {report_payload['window_end']} ({report_payload['days']} day window)",
        f"- Status: {report_payload['status']}",
        f"- Confidence: {report_payload['confidence']}",
        (
            "- Sources: "
            f"{report_payload['summary_count']} rollout summary file(s), "
            "MEMORY.md, memory_summary.md, and scoped workspace memory/cache files"
        ),
        "",
        "## What I Learned",
    ]
    lines.extend(f"- {line}" for line in learning_lines)
    lines.extend(
        [
            "",
            "## Rewarded Patterns",
        ]
    )
    lines.extend(f"- {line}" for line in rewarded_pattern_lines)
    lines.extend(
        [
            "",
            "## Mistakes Encountered",
        ]
    )
    lines.extend(f"- {line}" for line in mistake_lines)
    lines.extend(
        [
            "",
            "## Tool-Use Mistakes",
        ]
    )
    lines.extend(f"- {line}" for line in tool_mistake_lines)
    lines.extend(
        [
            "",
            "## Research Cache Health",
        ]
    )
    lines.extend(f"- {line}" for line in research_cache_lines)
    lines.extend(
        [
            "",
            "## Self-Healing Queue",
        ]
    )
    lines.extend(f"- {line}" for line in report_payload["self_healing_actions"])
    lines.extend(
        [
            "",
            "## Needs I Remember",
        ]
    )
    lines.extend(f"- {line}" for line in needs_lines)
    lines.extend(
        [
            "",
            "## Learning Stats (Heuristic)",
            (
                "- Task completion: "
                f"{report_payload['task_completion_rate']} "
                f"({report_payload['task_counts']['success']} of {report_payload['task_counts']['total']} task outcomes succeeded)"
            ),
            (
                "- Learning capture: "
                f"{report_payload['learning_capture_rate']} "
                f"({sum(1 for item in report_payload['learning_items'])} learning item(s) captured in the window)"
            ),
            (
                "- Mistake resolution: "
                f"{report_payload['mistake_resolution_rate']} "
                f"({len(report_payload['mistakes']['resolved'])} resolved of "
                f"{len(report_payload['mistakes']['resolved']) + len(report_payload['mistakes']['open']) + len(report_payload['mistakes']['unclear'])} captured mistake(s))"
            ),
            (
                f"- Tool-mistake resolution: {report_payload['tool_mistake_resolution_rate']} "
                f"({len(report_payload['tool_mistakes']['resolved'])} resolved of "
                f"{len(report_payload['tool_mistakes']['resolved']) + len(report_payload['tool_mistakes']['open']) + len(report_payload['tool_mistakes']['unclear'])} captured tool mistake(s))"
            ),
            f"- Reward strength: {report_payload['reward_strength']} rewarded unit(s)",
            f"- Penalty pressure: {report_payload['penalty_pressure']} penalty unit(s)",
            f"- Cache reuse: {report_payload['cache_reuse_rate']} ({len(report_payload['research_cache']['reused'])} reused of {len(report_payload['research_cache']['updates'])} cache update(s))",
            f"- Cache freshness risk: {report_payload['cache_freshness_risk']} stale finding(s)",
            f"- Brain size now: {report_payload['durable_bank_size']} durable memory unit(s)",
            (
                "- Brain growth in window: "
                f"+{report_payload['growth_units']} growth unit(s) "
                f"({report_payload['brain_growth_rate']} of the current durable bank)"
            ),
            f"- Learning momentum: {momentum_value}",
            "",
            "## Reality Check",
            "- Brain size, brain growth, and momentum are heuristic memory-health metrics derived from saved artifacts, not literal cognition measurements.",
            "- If the window is quiet or thin, the report says so rather than inventing extra certainty.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_compact_markdown(report_payload: dict) -> str:
    learning_lines = report_payload["learning_items"][:3]
    if not learning_lines:
        learning_lines = report_payload["recent_context"][:3]
    if not learning_lines:
        learning_lines = ["No durable learning was captured in the requested window."]

    mistake_count = sum(len(report_payload["mistakes"][status_name]) for status_name in ("resolved", "open", "unclear"))
    tool_mistake_count = sum(
        len(report_payload["tool_mistakes"][status_name]) for status_name in ("resolved", "open", "unclear")
    )
    rewarded_pattern_count = len(report_payload["rewarded_patterns"])
    stale_cache_count = len(report_payload["research_cache"]["stale"])
    open_mistake_count = len(report_payload["mistakes"]["open"]) + len(report_payload["tool_mistakes"]["open"])
    momentum_value = report_payload["learning_momentum"] or "n/a"

    lines = [
        "## Learning Snapshot",
        f"- Window: {report_payload['window_start']} to {report_payload['window_end']}",
        f"- Status: {report_payload['status']} ({report_payload['confidence']} confidence)",
        f"- Closure ready: {'yes' if report_payload['closure_ready'] else 'no'}",
        "- Learned today:",
    ]
    lines.extend(f"  - {line}" for line in learning_lines)
    lines.extend(
        [
            (
                "- Mistakes: "
                f"{mistake_count} captured, {len(report_payload['mistakes']['resolved'])} resolved, "
                f"{len(report_payload['mistakes']['open'])} open, {len(report_payload['mistakes']['unclear'])} unclear"
            ),
            (
                "- Tool-use mistakes: "
                f"{tool_mistake_count} captured, {len(report_payload['tool_mistakes']['resolved'])} resolved, "
                f"{len(report_payload['tool_mistakes']['open'])} open, {len(report_payload['tool_mistakes']['unclear'])} unclear"
            ),
            (
                "- Reinforcement: "
                f"reward strength {report_payload['reward_strength']} with {rewarded_pattern_count} rewarded pattern(s), "
                f"penalty pressure {report_payload['penalty_pressure']}, cache freshness risk {stale_cache_count}"
            ),
            f"- Self-healing queue: {report_payload['self_healing_actions'][0]}",
            (
                "- Memory health (heuristic): "
                f"brain size {report_payload['durable_bank_size']}, "
                f"growth +{report_payload['growth_units']}, "
                f"momentum {momentum_value}, "
                f"open issues {open_mistake_count}"
            ),
            "- Reality check: these learning and brain-growth numbers are heuristics derived from saved artifacts, not literal cognition.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    arguments = parse_arguments()
    try:
        timezone_value = resolve_timezone(arguments.timezone)
    except ZoneInfoNotFoundError as error:
        raise SystemExit(f"Unknown timezone: {arguments.timezone}") from error

    anchor_date = parse_anchor_date(arguments.date, timezone_value)
    report_payload = build_report_payload(
        memory_base=arguments.memory_base.expanduser(),
        anchor_date=anchor_date,
        days=arguments.days,
        timezone_value=timezone_value,
        workspace_root=arguments.workspace_root,
        agent_role=arguments.agent_role,
        workstream_key=arguments.workstream_key,
        agent_instance=arguments.agent_instance,
    )

    if arguments.format == "json":
        rendered_output = json.dumps(report_payload, indent=2, default=str) + "\n"
    elif arguments.format == "compact":
        rendered_output = render_compact_markdown(report_payload)
    else:
        rendered_output = render_markdown(report_payload)

    if arguments.output is not None:
        output_path = arguments.output.expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_output, encoding="utf-8")

    print(rendered_output, end="")


if __name__ == "__main__":
    main()
