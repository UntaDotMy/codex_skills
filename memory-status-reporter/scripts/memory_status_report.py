from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass
class RolloutSummary:
    file_path: str
    title: str
    updated_at: datetime
    task_outcomes: list[str]
    reusable_knowledge: list[str]
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
    issues = extract_bullets_after_label(lines, "Things that did not work / can be improved:")

    return RolloutSummary(
        file_path=str(file_path),
        title=title,
        updated_at=parsed_updated_at.astimezone(timezone_value),
        task_outcomes=task_outcomes,
        reusable_knowledge=reusable_knowledge,
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


def collect_rollout_summaries(memory_base: Path, timezone_value: ZoneInfo) -> list[RolloutSummary]:
    rollout_directory = memory_base / "rollout_summaries"
    if not rollout_directory.exists():
        return []

    summaries: list[RolloutSummary] = []
    for file_path in sorted(rollout_directory.glob("*.md")):
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


def build_report_payload(
    memory_base: Path,
    anchor_date: date,
    days: int,
    timezone_value: ZoneInfo,
) -> dict:
    all_summaries = collect_rollout_summaries(memory_base, timezone_value)

    window_end = datetime.combine(anchor_date, time.min, timezone_value) + timedelta(days=1)
    window_start = window_end - timedelta(days=days)
    window_summaries = collect_window_summaries(all_summaries, window_start, window_end)

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

    memory_text = (memory_base / "MEMORY.md").read_text(encoding="utf-8") if (memory_base / "MEMORY.md").exists() else ""
    memory_summary_text = (memory_base / "memory_summary.md").read_text(encoding="utf-8") if (memory_base / "memory_summary.md").exists() else ""

    memory_learnings = collect_memory_learnings(memory_text)
    user_needs = collect_user_needs(memory_summary_text)
    general_tips = collect_general_tips(memory_summary_text)
    durable_bank_size = len(memory_learnings) + len(user_needs) + len(general_tips)

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
        "learning_items": reusable_knowledge,
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
        "brain_growth_rate": format_percentage(growth_units, durable_bank_size),
        "learning_momentum": None if momentum_value is None else f"{momentum_value:.1f}%",
        "recent_context": build_recent_context(all_summaries, window_start),
        "source_files": {
            "memory": str(memory_base / "MEMORY.md"),
            "memory_summary": str(memory_base / "memory_summary.md"),
            "rollout_directory": str(memory_base / "rollout_summaries"),
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
            "MEMORY.md, and memory_summary.md"
        ),
        "",
        "## What I Learned",
    ]
    lines.extend(f"- {line}" for line in learning_lines)
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
    open_mistake_count = len(report_payload["mistakes"]["open"]) + len(report_payload["tool_mistakes"]["open"])
    momentum_value = report_payload["learning_momentum"] or "n/a"

    lines = [
        "## Learning Snapshot",
        f"- Window: {report_payload['window_start']} to {report_payload['window_end']}",
        f"- Status: {report_payload['status']} ({report_payload['confidence']} confidence)",
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
