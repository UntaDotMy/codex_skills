from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class MemoryScope:
    memory_base: Path
    workspace_root: Path
    workspace_slug: str
    workstream_key: str
    agent_role: str | None
    agent_instance: str | None
    workspace_directory: Path
    workspace_memory_directory: Path
    workspace_reference_directory: Path
    workspace_memory_file: Path
    workspace_summary_file: Path
    workstream_directory: Path
    workstream_memory_directory: Path
    workstream_reference_directory: Path
    workstream_memory_file: Path
    workstream_summary_file: Path
    session_state_file: Path
    working_buffer_file: Path
    wal_file: Path
    spawned_agent_registry_file: Path
    agent_directory: Path | None
    agent_memory_file: Path | None
    agent_instance_directory: Path | None
    agent_instance_memory_file: Path | None
    research_cache_directory: Path
    research_cache_file: Path
    archive_directory: Path
    reports_directory: Path
    global_memory_file: Path
    global_summary_file: Path
    raw_memories_file: Path
    rollout_directory: Path


def parse_timestamp(raw_value: str | None) -> datetime | None:
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


def current_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def infer_freshness_window(freshness: str | None) -> timedelta | None:
    normalized_freshness = (freshness or "").strip().lower()
    if not normalized_freshness:
        return None

    if "hour" in normalized_freshness:
        return timedelta(hours=1)
    if "daily" in normalized_freshness or "day" in normalized_freshness:
        return timedelta(days=1)
    if "weekly" in normalized_freshness or "week" in normalized_freshness:
        return timedelta(days=7)
    if "monthly" in normalized_freshness or "month" in normalized_freshness:
        return timedelta(days=30)
    if "quarter" in normalized_freshness:
        return timedelta(days=90)
    if "yearly" in normalized_freshness or "annual" in normalized_freshness or "year" in normalized_freshness:
        return timedelta(days=365)

    return None


def is_entry_past_inferred_freshness_window(entry: dict, reference_time: datetime | None = None) -> bool:
    freshness_window = infer_freshness_window(str(entry.get("freshness", "")))
    if freshness_window is None:
        return False

    updated_at = parse_timestamp(str(entry.get("updated_at") or entry.get("recorded_at")))
    if updated_at is None:
        return False

    comparison_time = reference_time or datetime.now(UTC)
    return updated_at + freshness_window < comparison_time


def normalize_workspace_root(workspace_root: Path | None) -> Path:
    return (workspace_root or Path.cwd()).expanduser().resolve()


def sanitize_scope_key(raw_value: str | None, fallback_value: str | None = None) -> str | None:
    if not raw_value:
        return fallback_value
    normalized_value = re.sub(r"[^a-z0-9-]+", "-", raw_value.lower()).strip("-")
    return normalized_value or fallback_value


def sanitize_agent_role(agent_role: str | None) -> str | None:
    return sanitize_scope_key(agent_role)


def sanitize_agent_instance(agent_instance: str | None) -> str | None:
    return sanitize_scope_key(agent_instance)


def slugify_workspace_root(workspace_root: Path) -> str:
    normalized_path = workspace_root.as_posix().lower().replace(":", "")
    workspace_slug = re.sub(r"[^a-z0-9]+", "-", normalized_path).strip("-")
    return workspace_slug or "workspace"


def detect_git_workstream_key(workspace_root: Path) -> str | None:
    try:
        completed_process = subprocess.run(
            ["git", "-C", str(workspace_root), "rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None

    if completed_process.returncode != 0:
        return None

    branch_name = completed_process.stdout.strip()
    if not branch_name or branch_name == "HEAD":
        return None
    return sanitize_scope_key(branch_name)


def resolve_workstream_key(explicit_workstream_key: str | None, workspace_root: Path) -> str:
    environment_workstream_key = os.environ.get("CODEX_WORKSTREAM_KEY")
    detected_workstream_key = detect_git_workstream_key(workspace_root)
    return (
        sanitize_scope_key(explicit_workstream_key)
        or sanitize_scope_key(environment_workstream_key)
        or detected_workstream_key
        or "default"
    )


def resolve_agent_instance(explicit_agent_instance: str | None) -> str | None:
    return sanitize_agent_instance(explicit_agent_instance or os.environ.get("CODEX_AGENT_INSTANCE"))


def resolve_memory_scope(
    memory_base: Path,
    workspace_root: Path | None = None,
    agent_role: str | None = None,
    workstream_key: str | None = None,
    agent_instance: str | None = None,
) -> MemoryScope:
    resolved_memory_base = memory_base.expanduser().resolve()
    resolved_workspace_root = normalize_workspace_root(workspace_root)
    sanitized_agent_role = sanitize_agent_role(agent_role)
    resolved_workstream_key = resolve_workstream_key(workstream_key, resolved_workspace_root)
    resolved_agent_instance = resolve_agent_instance(agent_instance)
    workspace_slug = slugify_workspace_root(resolved_workspace_root)
    workspace_directory = resolved_memory_base / "workspaces" / workspace_slug
    workspace_memory_directory = workspace_directory / "memory"
    workspace_reference_directory = workspace_directory / "reference"
    workstream_directory = workspace_directory / "workstreams" / resolved_workstream_key
    workstream_memory_directory = workstream_directory / "memory"
    workstream_reference_directory = workstream_directory / "reference"
    agent_directory = (
        resolved_memory_base
        / "agents"
        / sanitized_agent_role
        / workspace_slug
        / "workstreams"
        / resolved_workstream_key
        if sanitized_agent_role
        else None
    )
    agent_instance_directory = (
        None
        if agent_directory is None or resolved_agent_instance is None
        else agent_directory / "instances" / resolved_agent_instance
    )
    return MemoryScope(
        memory_base=resolved_memory_base,
        workspace_root=resolved_workspace_root,
        workspace_slug=workspace_slug,
        workstream_key=resolved_workstream_key,
        agent_role=sanitized_agent_role,
        agent_instance=resolved_agent_instance,
        workspace_directory=workspace_directory,
        workspace_memory_directory=workspace_memory_directory,
        workspace_reference_directory=workspace_reference_directory,
        workspace_memory_file=workspace_directory / "MEMORY.md",
        workspace_summary_file=workspace_directory / "SUMMARY.md",
        workstream_directory=workstream_directory,
        workstream_memory_directory=workstream_memory_directory,
        workstream_reference_directory=workstream_reference_directory,
        workstream_memory_file=workstream_directory / "MEMORY.md",
        workstream_summary_file=workstream_directory / "SUMMARY.md",
        session_state_file=workstream_memory_directory / "SESSION-STATE.md",
        working_buffer_file=workstream_memory_directory / "working-buffer.md",
        wal_file=workstream_memory_directory / "session-wal.jsonl",
        spawned_agent_registry_file=workstream_memory_directory / "spawned-agent-registry.json",
        agent_directory=agent_directory,
        agent_memory_file=None if agent_directory is None else agent_directory / "MEMORY.md",
        agent_instance_directory=agent_instance_directory,
        agent_instance_memory_file=(
            None if agent_instance_directory is None else agent_instance_directory / "MEMORY.md"
        ),
        research_cache_directory=resolved_memory_base / "research_cache" / workspace_slug,
        research_cache_file=resolved_memory_base / "research_cache" / workspace_slug / "cache.jsonl",
        archive_directory=resolved_memory_base / "archive" / workspace_slug / "workstreams" / resolved_workstream_key,
        reports_directory=resolved_memory_base / "reports",
        global_memory_file=resolved_memory_base / "MEMORY.md",
        global_summary_file=resolved_memory_base / "memory_summary.md",
        raw_memories_file=resolved_memory_base / "raw_memories.md",
        rollout_directory=resolved_memory_base / "rollout_summaries",
    )


def ensure_memory_scope_layout(scope: MemoryScope) -> None:
    scope.workspace_directory.mkdir(parents=True, exist_ok=True)
    scope.workspace_memory_directory.mkdir(parents=True, exist_ok=True)
    scope.workspace_reference_directory.mkdir(parents=True, exist_ok=True)
    scope.workstream_directory.mkdir(parents=True, exist_ok=True)
    scope.workstream_memory_directory.mkdir(parents=True, exist_ok=True)
    scope.workstream_reference_directory.mkdir(parents=True, exist_ok=True)
    scope.research_cache_directory.mkdir(parents=True, exist_ok=True)
    scope.archive_directory.mkdir(parents=True, exist_ok=True)
    scope.reports_directory.mkdir(parents=True, exist_ok=True)
    if scope.agent_directory is not None:
        scope.agent_directory.mkdir(parents=True, exist_ok=True)
    if scope.agent_instance_directory is not None:
        scope.agent_instance_directory.mkdir(parents=True, exist_ok=True)

    default_file_contents = {
        scope.workspace_memory_file: "# Workspace Memory\n\n",
        scope.workspace_summary_file: "# Workspace Summary\n\n",
        scope.workstream_memory_file: "# Workstream Memory\n\n",
        scope.workstream_summary_file: "# Workstream Summary\n\n",
        scope.session_state_file: "# Session State\n\n",
        scope.working_buffer_file: "# Working Buffer\n\n",
        scope.research_cache_file: "",
        scope.wal_file: "",
        scope.spawned_agent_registry_file: "[]\n",
    }
    if scope.agent_memory_file is not None:
        default_file_contents[scope.agent_memory_file] = "# Agent Memory\n\n"
    if scope.agent_instance_memory_file is not None:
        default_file_contents[scope.agent_instance_memory_file] = "# Agent Instance Memory\n\n"

    for file_path, default_content in default_file_contents.items():
        if not file_path.exists():
            file_path.write_text(default_content, encoding="utf-8")


def build_scope_markers(scope_key: str | None) -> set[str]:
    sanitized_scope_key = sanitize_scope_key(scope_key)
    if not sanitized_scope_key:
        return set()

    marker_variants = {
        sanitized_scope_key.lower(),
        sanitized_scope_key.lower().replace("-", "/"),
        sanitized_scope_key.lower().replace("-", "_"),
        sanitized_scope_key.lower().replace("-", " "),
    }
    return {marker for marker in marker_variants if marker}


def normalize_rollout_metadata_path(path_value: str | None) -> str | None:
    if not path_value:
        return None
    normalized_path = path_value.strip().replace("\\", "/").lower()
    if normalized_path.startswith("//?/unc/"):
        normalized_path = "//" + normalized_path[len("//?/unc/") :]
    elif normalized_path.startswith("//?/"):
        normalized_path = normalized_path[len("//?/") :]
    if normalized_path.startswith("/private/var/") or normalized_path.startswith("/private/tmp/"):
        normalized_path = normalized_path[len("/private") :]
    normalized_path = normalized_path.rstrip("/")
    return normalized_path or None


def parse_rollout_summary_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line:
            if metadata:
                break
            continue
        if stripped_line.startswith("#"):
            break
        metadata_match = re.match(r"^([a-z_]+):\s*(.+)$", raw_line)
        if metadata_match is None:
            if metadata:
                break
            continue
        metadata[metadata_match.group(1).lower()] = metadata_match.group(2).strip()
    return metadata


def collect_workspace_rollout_matches(
    memory_base: Path,
    workspace_root: Path,
    workstream_key: str | None = None,
    agent_instance: str | None = None,
    max_results: int = 8,
) -> list[Path]:
    rollout_directory = memory_base.expanduser() / "rollout_summaries"
    if not rollout_directory.exists():
        return []

    normalized_workspace_root = normalize_workspace_root(workspace_root)
    target_workspace_path = normalize_rollout_metadata_path(normalized_workspace_root.as_posix())
    target_workstream_key = sanitize_scope_key(workstream_key)
    target_agent_instance = sanitize_agent_instance(agent_instance)

    matched_files: list[tuple[float, Path]] = []
    for file_path in sorted(rollout_directory.glob("*.md")):
        metadata = parse_rollout_summary_metadata(file_path.read_text(encoding="utf-8"))
        metadata_workspace_path = normalize_rollout_metadata_path(metadata.get("cwd"))
        if target_workspace_path is None or metadata_workspace_path != target_workspace_path:
            continue
        metadata_workstream_key = sanitize_scope_key(
            metadata.get("git_branch") or metadata.get("workstream_key")
        )
        if target_workstream_key and metadata_workstream_key != target_workstream_key:
            continue
        metadata_agent_instance = sanitize_agent_instance(metadata.get("agent_instance"))
        if target_agent_instance and metadata_agent_instance != target_agent_instance:
            continue

        matched_files.append((file_path.stat().st_mtime, file_path))

    matched_files.sort(key=lambda item: item[0], reverse=True)
    return [file_path for _, file_path in matched_files[:max_results]]


def normalize_lookup_key(raw_text: str) -> str:
    normalized_text = raw_text.lower().strip()
    normalized_text = re.sub(r"\s+", " ", normalized_text)
    normalized_text = re.sub(r"[^a-z0-9 ]", "", normalized_text)
    return normalized_text


def load_research_cache_entries(scope: MemoryScope) -> list[dict]:
    if not scope.research_cache_file.exists():
        return []

    entries: list[dict] = []
    for raw_line in scope.research_cache_file.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            parsed_entry = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed_entry, dict):
            entries.append(parsed_entry)
    return entries


def save_research_cache_entries(scope: MemoryScope, entries: list[dict]) -> None:
    ensure_memory_scope_layout(scope)
    serialized_entries = "\n".join(
        json.dumps(entry, ensure_ascii=True, sort_keys=True)
        for entry in entries
    )
    scope.research_cache_file.write_text(
        f"{serialized_entries}\n" if serialized_entries else "",
        encoding="utf-8",
    )


def lookup_research_cache_entries(
    scope: MemoryScope,
    query: str,
    max_results: int = 5,
    include_stale: bool = False,
) -> list[dict]:
    normalized_query = normalize_lookup_key(query)
    query_tokens = [token for token in normalized_query.split(" ") if token]
    if not query_tokens:
        return []

    scored_entries: list[tuple[int, datetime, dict]] = []
    for entry in load_research_cache_entries(scope):
        entry_status = str(entry.get("status", "fresh")).lower()
        entry_is_stale = entry_status in {"stale", "superseded"} or is_entry_past_inferred_freshness_window(entry)
        if not include_stale and entry_is_stale:
            continue

        searchable_parts = [
            str(entry.get("question", "")),
            str(entry.get("answer", "")),
            " ".join(str(tag) for tag in entry.get("tags", [])),
            " ".join(str(source) for source in entry.get("sources", [])),
        ]
        normalized_haystack = normalize_lookup_key(" ".join(searchable_parts))
        if not normalized_haystack:
            continue

        score = 0
        if normalized_query and normalized_query in normalized_haystack:
            score += 3
        score += sum(token in normalized_haystack for token in query_tokens)
        if score == 0:
            continue

        updated_at = parse_timestamp(str(entry.get("updated_at") or entry.get("recorded_at"))) or datetime.min.replace(
            tzinfo=UTC
        )
        scored_entries.append((score, updated_at, entry))

    scored_entries.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [entry for _, _, entry in scored_entries[:max_results]]


def record_research_cache_entry(
    scope: MemoryScope,
    question: str,
    answer: str,
    sources: list[str],
    freshness: str,
    tags: list[str] | None = None,
    agent_role: str | None = None,
    agent_instance: str | None = None,
    status: str = "fresh",
    reinforcement: str = "neutral",
    confidence: str | None = None,
    note: str | None = None,
    entry_key: str | None = None,
) -> dict:
    ensure_memory_scope_layout(scope)
    normalized_entry_key = entry_key or normalize_lookup_key(question)
    timestamp_now = current_timestamp()
    existing_entries = load_research_cache_entries(scope)
    existing_entry = next(
        (
            entry
            for entry in existing_entries
            if str(entry.get("entry_key", "")) == normalized_entry_key
        ),
        None,
    )

    recorded_at = existing_entry.get("recorded_at") if existing_entry else timestamp_now
    updated_entry = {
        "entry_key": normalized_entry_key,
        "question": question.strip(),
        "answer": answer.strip(),
        "sources": [source for source in sources if source],
        "tags": [tag for tag in (tags or []) if tag],
        "freshness": freshness.strip(),
        "status": status.strip().lower() or "fresh",
        "reinforcement": reinforcement.strip().lower() or "neutral",
        "confidence": None if confidence is None else confidence.strip(),
        "note": None if note is None else note.strip(),
        "workspace_slug": scope.workspace_slug,
        "workstream_key": scope.workstream_key,
        "agent_role": sanitize_agent_role(agent_role) or scope.agent_role,
        "agent_instance": sanitize_agent_instance(agent_instance) or scope.agent_instance,
        "recorded_at": recorded_at,
        "updated_at": timestamp_now,
    }

    remaining_entries = [
        entry
        for entry in existing_entries
        if str(entry.get("entry_key", "")) != normalized_entry_key
    ]
    remaining_entries.append(updated_entry)
    remaining_entries.sort(
        key=lambda entry: parse_timestamp(str(entry.get("updated_at"))) or datetime.min.replace(tzinfo=UTC)
    )
    save_research_cache_entries(scope, remaining_entries)
    return updated_entry


def update_research_cache_entry(
    scope: MemoryScope,
    entry_key: str,
    *,
    status: str | None = None,
    reinforcement: str | None = None,
    note: str | None = None,
) -> dict:
    existing_entries = load_research_cache_entries(scope)
    normalized_entry_key = entry_key.strip()
    timestamp_now = current_timestamp()
    updated_entry: dict | None = None
    updated_entries: list[dict] = []

    for entry in existing_entries:
        if str(entry.get("entry_key", "")) != normalized_entry_key:
            updated_entries.append(entry)
            continue

        updated_entry = dict(entry)
        if status is not None:
            updated_entry["status"] = status.strip().lower()
        if reinforcement is not None:
            updated_entry["reinforcement"] = reinforcement.strip().lower()
        if note is not None:
            updated_entry["note"] = note.strip()
        updated_entry["updated_at"] = timestamp_now
        updated_entries.append(updated_entry)

    if updated_entry is None:
        raise KeyError(f"Research cache entry not found: {normalized_entry_key}")

    save_research_cache_entries(scope, updated_entries)
    return updated_entry


def summarize_research_cache_entry(entry: dict) -> str:
    question = str(entry.get("question", "unnamed research finding")).strip()
    status = str(entry.get("status", "fresh")).strip().lower()
    freshness = str(entry.get("freshness", "unspecified freshness")).strip()
    reinforcement = str(entry.get("reinforcement", "neutral")).strip().lower()
    return f"{question} ({status}; freshness: {freshness}; reinforcement: {reinforcement})"


def archive_research_cache_entries(
    scope: MemoryScope,
    statuses: tuple[str, ...] = ("stale", "superseded"),
) -> list[dict]:
    normalized_statuses = {status.strip().lower() for status in statuses if status.strip()}
    if not normalized_statuses:
        return []

    existing_entries = load_research_cache_entries(scope)
    if not existing_entries:
        return []

    archived_at = current_timestamp()
    entries_to_archive: list[dict] = []
    remaining_entries: list[dict] = []
    for entry in existing_entries:
        entry_status = str(entry.get("status", "fresh")).strip().lower()
        if entry_status in normalized_statuses:
            archived_entry = dict(entry)
            archived_entry["archived_at"] = archived_at
            entries_to_archive.append(archived_entry)
            continue
        remaining_entries.append(entry)

    if not entries_to_archive:
        return []

    ensure_memory_scope_layout(scope)
    archive_file = scope.archive_directory / "research_cache_archive.jsonl"
    archive_lines = []
    if archive_file.exists():
        archive_lines = [
            raw_line
            for raw_line in archive_file.read_text(encoding="utf-8").splitlines()
            if raw_line.strip()
        ]
    archive_lines.extend(
        json.dumps(entry, ensure_ascii=True, sort_keys=True)
        for entry in entries_to_archive
    )
    archive_file.write_text("\n".join(archive_lines) + "\n", encoding="utf-8")
    save_research_cache_entries(scope, remaining_entries)
    return entries_to_archive
