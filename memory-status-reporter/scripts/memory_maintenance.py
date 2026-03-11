from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from memory_store import current_timestamp, ensure_memory_scope_layout, resolve_memory_scope


def approximate_token_count(text: str) -> int:
    stripped_text = text.strip()
    if not stripped_text:
        return 0
    return max(1, math.ceil(len(stripped_text) / 4))


def read_text(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def append_markdown_entry(file_path: Path, heading: str, bullet_text: str) -> None:
    existing_text = read_text(file_path).rstrip()
    new_block = f"## {heading}\n- {bullet_text}\n"
    if not existing_text:
        file_path.write_text(f"{new_block}", encoding="utf-8")
        return
    file_path.write_text(f"{existing_text}\n\n{new_block}", encoding="utf-8")


def record_session_state(
    session_state_file: Path,
    wal_file: Path,
    category: str,
    detail: str,
    title: str | None,
    source: str,
) -> dict:
    timestamp = current_timestamp()
    wal_entry = {
        "recorded_at": timestamp,
        "category": category,
        "title": title,
        "detail": detail.strip(),
        "source": source.strip(),
    }
    existing_wal = read_text(wal_file)
    wal_file.write_text(
        f"{existing_wal}{json.dumps(wal_entry, ensure_ascii=True, sort_keys=True)}\n",
        encoding="utf-8",
    )
    heading = timestamp[:10]
    summary_prefix = f"[{category}]"
    if title:
        summary_prefix = f"{summary_prefix} {title.strip()}:"
    append_markdown_entry(session_state_file, heading, f"{summary_prefix} {detail.strip()}".strip())
    return wal_entry


def append_working_buffer(working_buffer_file: Path, text: str) -> dict:
    timestamp = current_timestamp()
    append_markdown_entry(working_buffer_file, timestamp[:10], f"{timestamp} - {text.strip()}")
    return {
        "recorded_at": timestamp,
        "text": text.strip(),
    }


def split_markdown_chunks(text: str) -> tuple[list[str], list[str]]:
    if not text.strip():
        return [], []
    lines = text.splitlines()
    header_lines: list[str] = []
    body_start = 0
    while body_start < len(lines):
        stripped_line = lines[body_start].strip()
        if body_start == 0 and stripped_line.startswith("#"):
            header_lines.append(lines[body_start])
            body_start += 1
            continue
        if stripped_line == "":
            body_start += 1
            if header_lines:
                break
            continue
        break
    body_lines = lines[body_start:]
    chunks: list[str] = []
    current_chunk: list[str] = []
    for line in body_lines:
        if line.strip() == "":
            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())
                current_chunk = []
            continue
        current_chunk.append(line)
    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())
    return header_lines, chunks


def render_markdown_chunks(header_lines: list[str], chunks: list[str]) -> str:
    rendered_parts: list[str] = []
    if header_lines:
        rendered_parts.append("\n".join(header_lines).strip())
    rendered_parts.extend(chunk for chunk in chunks if chunk.strip())
    rendered_text = "\n\n".join(rendered_parts).strip()
    return f"{rendered_text}\n" if rendered_text else ""


def trim_chunks_to_budget(
    header_lines: list[str],
    chunks: list[str],
    max_tokens: int,
) -> tuple[list[str], list[str]]:
    kept_chunks: list[str] = []
    kept_text = render_markdown_chunks(header_lines, kept_chunks)
    for chunk in reversed(chunks):
        candidate_chunks = [chunk, *kept_chunks]
        candidate_text = render_markdown_chunks(header_lines, candidate_chunks)
        if approximate_token_count(candidate_text) <= max_tokens or not kept_chunks:
            kept_chunks = candidate_chunks
            kept_text = candidate_text
            continue
        break
    removed_chunks = chunks[: max(0, len(chunks) - len(kept_chunks))]
    return kept_chunks, removed_chunks


def archive_trimmed_chunks(archive_directory: Path, file_label: str, removed_chunks: list[str]) -> Path | None:
    if not removed_chunks:
        return None
    archive_file = archive_directory / f"trim-{current_timestamp().replace(':', '-')}-{file_label}.md"
    archive_text = "# Trim Archive\n\n" + "\n\n".join(removed_chunks).strip() + "\n"
    archive_file.write_text(archive_text, encoding="utf-8")
    return archive_file


def rendered_file_token_count(header_lines: list[str], chunks: list[str]) -> int:
    return approximate_token_count(render_markdown_chunks(header_lines, chunks))


def trim_scope_files(scope, max_file_tokens: int, max_total_tokens: int) -> dict:
    l1_files = [
        ("workspace_summary", scope.workspace_summary_file),
        ("workstream_summary", scope.workstream_summary_file),
        ("session_state", scope.session_state_file),
        ("working_buffer", scope.working_buffer_file),
    ]
    file_reports: list[dict] = []
    file_states: list[dict] = []
    total_before = 0

    for file_label, file_path in l1_files:
        original_text = read_text(file_path)
        before_tokens = approximate_token_count(original_text)
        header_lines, chunks = split_markdown_chunks(original_text)
        kept_chunks, removed_chunks = trim_chunks_to_budget(header_lines, chunks, max_file_tokens)
        total_before += before_tokens
        file_states.append(
            {
                "file_label": file_label,
                "file_path": file_path,
                "original_text": original_text,
                "before_tokens": before_tokens,
                "header_lines": header_lines,
                "kept_chunks": kept_chunks,
                "removed_chunks": removed_chunks,
            }
        )

    total_after = sum(
        rendered_file_token_count(file_state["header_lines"], file_state["kept_chunks"])
        for file_state in file_states
    )

    while total_after > max_total_tokens:
        trim_candidate = max(
            (file_state for file_state in file_states if file_state["kept_chunks"]),
            key=lambda file_state: rendered_file_token_count(
                file_state["header_lines"],
                file_state["kept_chunks"],
            ),
            default=None,
        )
        if trim_candidate is None:
            break
        trim_candidate["removed_chunks"].append(trim_candidate["kept_chunks"].pop(0))
        total_after = sum(
            rendered_file_token_count(file_state["header_lines"], file_state["kept_chunks"])
            for file_state in file_states
        )

    for file_state in file_states:
        trimmed_text = render_markdown_chunks(file_state["header_lines"], file_state["kept_chunks"])
        archive_file = archive_trimmed_chunks(
            scope.archive_directory,
            file_state["file_label"],
            file_state["removed_chunks"],
        )
        if trimmed_text != file_state["original_text"]:
            file_state["file_path"].write_text(trimmed_text, encoding="utf-8")
        after_tokens = approximate_token_count(read_text(file_state["file_path"]))
        file_reports.append(
            {
                "file_label": file_state["file_label"],
                "file_path": str(file_state["file_path"]),
                "before_tokens": file_state["before_tokens"],
                "after_tokens": after_tokens,
                "archive_file": None if archive_file is None else str(archive_file),
            }
        )

    return {
        "max_file_tokens": max_file_tokens,
        "max_total_tokens": max_total_tokens,
        "before_total_tokens": total_before,
        "after_total_tokens": sum(file_report["after_tokens"] for file_report in file_reports),
        "within_total_budget": total_after <= max_total_tokens,
        "file_reports": file_reports,
    }


def extract_canonical_rules(*texts: str) -> list[str]:
    rules: list[str] = []
    for text in texts:
        for line in text.splitlines():
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if not (stripped_line.startswith("- ") or re.match(r"^\d+\.\s+", stripped_line)):
                continue
            normalized_line = stripped_line.lower()
            if any(
                marker in normalized_line
                for marker in ("must", "never", "always", "do not", "prefer", "only", "treat")
            ):
                rules.append(stripped_line.lstrip("- ").strip())
    return rules


def tokenize_for_similarity(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def evaluate_observed_behavior(canonical_rules: list[str], observed_items: list[str]) -> list[dict]:
    findings: list[dict] = []
    canonical_rule_tokens = [(rule, tokenize_for_similarity(rule)) for rule in canonical_rules]
    for observed_item in observed_items:
        observed_tokens = tokenize_for_similarity(observed_item)
        best_rule = ""
        best_score = 0.0
        for rule, rule_tokens in canonical_rule_tokens:
            if not observed_tokens or not rule_tokens:
                continue
            overlap_score = len(observed_tokens & rule_tokens) / len(observed_tokens)
            if overlap_score > best_score:
                best_score = overlap_score
                best_rule = rule
        findings.append(
            {
                "observed": observed_item,
                "matched_rule": best_rule or None,
                "match_score": round(best_score, 3),
                "status": "aligned" if best_score >= 0.35 else "drift_candidate",
                "correction": best_rule or "No strong canonical rule match found; inspect recent behavior manually.",
            }
        )
    return findings


def render_markdown_report(payload: dict) -> str:
    lines = ["# Memory Maintenance"]
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"## {key.replace('_', ' ').title()}")
            if not value:
                lines.append("- none")
                continue
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"- {json.dumps(item, ensure_ascii=True, sort_keys=True)}")
                else:
                    lines.append(f"- {item}")
        elif isinstance(value, dict):
            lines.append(f"## {key.replace('_', ' ').title()}")
            for child_key, child_value in value.items():
                lines.append(f"- {child_key}: {child_value}")
        else:
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines) + "\n"


def add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory-base", type=Path, default=Path("~/.codex/memories").expanduser())
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--agent-role", type=str, default=None)
    parser.add_argument("--workstream-key", type=str, default=None)
    parser.add_argument("--agent-instance", type=str, default=None)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Maintain scoped session state, working buffers, and memory trim or recalibration workflows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    write_parser = subparsers.add_parser("write-session-state", help="Write a correction or decision with WAL semantics.")
    add_scope_arguments(write_parser)
    write_parser.add_argument(
        "--category",
        choices=("correction", "decision", "proper-noun", "preference", "value", "learning"),
        required=True,
    )
    write_parser.add_argument("--detail", required=True)
    write_parser.add_argument("--title", default=None)
    write_parser.add_argument("--source", default="user-message")

    buffer_parser = subparsers.add_parser("append-working-buffer", help="Append one working-buffer entry.")
    add_scope_arguments(buffer_parser)
    buffer_parser.add_argument("--text", required=True)

    trim_parser = subparsers.add_parser("trim", help="Trim L1 scoped memory files into the archive when they exceed budget.")
    add_scope_arguments(trim_parser)
    trim_parser.add_argument("--max-file-tokens", type=int, default=1000)
    trim_parser.add_argument("--max-total-tokens", type=int, default=7000)

    recalibrate_parser = subparsers.add_parser(
        "recalibrate",
        help="Re-read scoped memory files and compare optional observed behavior notes against canonical rules.",
    )
    add_scope_arguments(recalibrate_parser)
    recalibrate_parser.add_argument(
        "--observed",
        action="append",
        default=[],
        help="Observed recent behavior to compare against the current workspace guidance. Pass multiple times.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    scope = resolve_memory_scope(
        memory_base=arguments.memory_base,
        workspace_root=arguments.workspace_root,
        agent_role=arguments.agent_role,
        workstream_key=arguments.workstream_key,
        agent_instance=arguments.agent_instance,
    )
    ensure_memory_scope_layout(scope)

    if arguments.command == "write-session-state":
        payload = record_session_state(
            session_state_file=scope.session_state_file,
            wal_file=scope.wal_file,
            category=arguments.category,
            detail=arguments.detail,
            title=arguments.title,
            source=arguments.source,
        )
    elif arguments.command == "append-working-buffer":
        payload = append_working_buffer(scope.working_buffer_file, arguments.text)
    elif arguments.command == "trim":
        payload = trim_scope_files(
            scope=scope,
            max_file_tokens=arguments.max_file_tokens,
            max_total_tokens=arguments.max_total_tokens,
        )
    elif arguments.command == "recalibrate":
        canonical_rules = extract_canonical_rules(
            read_text(scope.workspace_summary_file),
            read_text(scope.workstream_summary_file),
            read_text(scope.session_state_file),
            read_text(scope.working_buffer_file),
        )
        payload = {
            "workspace_slug": scope.workspace_slug,
            "workstream_key": scope.workstream_key,
            "canonical_rule_count": len(canonical_rules),
            "canonical_rules": canonical_rules[:12],
            "observed_count": len(arguments.observed),
            "observed_findings": evaluate_observed_behavior(canonical_rules, arguments.observed),
            "note": (
                "No explicit observed behavior was supplied; this is a baseline recalibration pass."
                if not arguments.observed
                else "Observed behavior was compared against the current scoped guidance."
            ),
        }
    else:
        raise SystemExit(f"Unsupported command: {arguments.command}")

    if arguments.format == "markdown":
        print(render_markdown_report(payload), end="")
        return
    print(json.dumps(payload, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
