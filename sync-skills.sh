#!/bin/bash

# Sync and validate script for the Codex skill pack.
# This script validates the repo, syncs skills into the active Codex home,
# and keeps the live memory-status wiring aligned with the repo.

set -e  # Exit on error

# Silence deprecated environment noise inherited from some shells.
unset GREP_OPTIONS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP_DEFAULT_REPOSITORY_URL="https://github.com/UntaDotMy/codex_skills.git"
BOOTSTRAP_DEFAULT_REPOSITORY_BRANCH="main"
CODEX_SOURCE="$SCRIPT_DIR"
SYNC_SKILLS_MANAGER_VERSION="2026.03.12.1"
SYNC_SKILLS_INTERNAL_UPDATE_RESUME_COMMAND="__resume-after-self-update"

bootstrap_repository_layout_is_complete() {
    local repository_path=$1

    [[ -f "$repository_path/AGENTS.md" ]] && \
    [[ -f "$repository_path/README.md" ]] && \
    [[ -f "$repository_path/00-skill-routing-and-escalation.md" ]] && \
    [[ -f "$repository_path/sync-skills.sh" ]] && \
    [[ -f "$repository_path/reviewer/SKILL.md" ]]
}

resolve_bootstrap_repository_path() {
    if [[ -n "${CODEX_SKILLS_REPOSITORY_PATH:-}" ]]; then
        printf "%s\n" "$CODEX_SKILLS_REPOSITORY_PATH"
        return 0
    fi

    return 0
}

bootstrap_repository_path_is_persistent() {
    [[ -n "${CODEX_SKILLS_REPOSITORY_PATH:-}" ]]
}

bootstrap_print_info() {
    printf "[INFO] %s\n" "$1"
}

bootstrap_print_error() {
    printf "[ERROR] %s\n" "$1" >&2
}

bootstrap_ensure_git_available() {
    if ! command -v git >/dev/null 2>&1; then
        bootstrap_print_error "Git is required when sync-skills.sh is used as a standalone bootstrap entrypoint."
        exit 1
    fi
}

bootstrap_prepare_repository_for_run() {
    local repository_url=$1
    local repository_branch=$2
    local requested_repository_path
    local repository_parent_path
    local runtime_repository_path

    requested_repository_path="$(resolve_bootstrap_repository_path)"
    if [[ -n "$requested_repository_path" ]]; then
        if bootstrap_repository_layout_is_complete "$requested_repository_path" && [[ -d "$requested_repository_path/.git" ]]; then
            printf "%s\n" "$requested_repository_path"
            return 0
        fi

        if [[ "$requested_repository_path" == "$SCRIPT_DIR" ]]; then
            bootstrap_print_error "Standalone bootstrap cannot reuse the current script directory as the requested repository path: $requested_repository_path"
            exit 1
        fi

        repository_parent_path="$(dirname "$requested_repository_path")"
        mkdir -p "$repository_parent_path"
        if [[ -e "$requested_repository_path" ]] && [[ -n "$(find "$requested_repository_path" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]]; then
            bootstrap_print_error "Requested bootstrap repository path exists but is not a valid codex_skills Git clone: $requested_repository_path"
            bootstrap_print_error "Remove that path or choose a clean CODEX_SKILLS_REPOSITORY_PATH before retrying."
            exit 1
        fi

        bootstrap_print_info "Cloning requested codex_skills repo into $requested_repository_path" >&2
        git clone --branch "$repository_branch" --single-branch "$repository_url" "$requested_repository_path"
        printf "%s\n" "$requested_repository_path"
        return 0
    fi

    repository_parent_path="${TMPDIR:-/tmp}"
    mkdir -p "$repository_parent_path"
    runtime_repository_path="$(mktemp -d "$repository_parent_path/codex_skills.bootstrap.XXXXXX")"
    bootstrap_print_info "Cloning fresh temporary codex_skills repo for this run" >&2
    if ! git clone --branch "$repository_branch" --single-branch "$repository_url" "$runtime_repository_path"; then
        rm -rf "$runtime_repository_path"
        exit 1
    fi
    printf "%s\n" "$runtime_repository_path"
}

bootstrap_cleanup_runtime_repository() {
    local runtime_repository_path="${CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH:-}"

    [[ -n "$runtime_repository_path" ]] || return 0
    if [[ "${CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT:-false}" == "true" ]]; then
        return 0
    fi
    if ! bootstrap_current_script_owns_runtime_repository; then
        return 0
    fi

    if [[ -d "$runtime_repository_path" ]]; then
        rm -rf "$runtime_repository_path"
    fi
}

bootstrap_current_script_owns_runtime_repository() {
    local current_script_path="${BASH_SOURCE[0]}"
    local runtime_entry_script_path="${CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH:-${CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH:-}}"

    [[ -n "${CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH:-}" ]] || return 1
    [[ -n "$runtime_entry_script_path" ]] || return 1
    [[ "$current_script_path" == "$runtime_entry_script_path" ]]
}

BOOTSTRAP_EXTERNAL_SCRIPT_REFRESH_RESULT="unchanged"

bootstrap_refresh_external_entry_script_copy() {
    local external_script_path=$1
    local managed_script_path=$2
    local external_directory
    local temporary_script_path

    BOOTSTRAP_EXTERNAL_SCRIPT_REFRESH_RESULT="unchanged"

    [[ -n "$external_script_path" ]] || return 0
    [[ -f "$external_script_path" ]] || return 0
    [[ -f "$managed_script_path" ]] || return 0

    if [[ "$external_script_path" == "$managed_script_path" ]]; then
        return 0
    fi

    if cmp -s "$managed_script_path" "$external_script_path"; then
        return 0
    fi

    external_directory="$(dirname "$external_script_path")"
    if [[ ! -w "$external_directory" ]] || [[ ! -w "$external_script_path" ]]; then
        bootstrap_print_info "Staged bootstrap repo is newer, but the standalone entry script is not writable: $external_script_path"
        BOOTSTRAP_EXTERNAL_SCRIPT_REFRESH_RESULT="unwritable"
        return 0
    fi

    temporary_script_path="$(mktemp "$external_directory/.codex-bootstrap-sync.XXXXXX")" || {
        bootstrap_print_info "Unable to allocate a temporary file to refresh the standalone entry script: $external_script_path"
        return 0
    }

    if cp -p "$managed_script_path" "$temporary_script_path" && mv "$temporary_script_path" "$external_script_path"; then
        bootstrap_print_info "Refreshed standalone entry script from the staged bootstrap repo: $external_script_path"
        BOOTSTRAP_EXTERNAL_SCRIPT_REFRESH_RESULT="refreshed"
        return 0
    fi

    rm -f "$temporary_script_path"
    bootstrap_print_info "Unable to refresh the standalone entry script automatically: $external_script_path"
    BOOTSTRAP_EXTERNAL_SCRIPT_REFRESH_RESULT="failed"
    return 0
}

refresh_bootstrap_entry_script_from_repo() {
    local external_script_path="${CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH:-}"
    local managed_script_path

    [[ -n "$external_script_path" ]] || return 0
    managed_script_path="$CODEX_SOURCE/$(basename "$external_script_path")"
    bootstrap_refresh_external_entry_script_copy "$external_script_path" "$managed_script_path"
}

bootstrap_delegate_if_needed() {
    local repository_url
    local repository_branch
    local runtime_repository_path
    local current_script_path
    local delegate_script_path
    local exit_status

    if bootstrap_repository_layout_is_complete "$SCRIPT_DIR"; then
        return 0
    fi

    current_script_path="${BASH_SOURCE[0]}"
    repository_url="${CODEX_SKILLS_REPOSITORY_URL:-$BOOTSTRAP_DEFAULT_REPOSITORY_URL}"
    repository_branch="${CODEX_SKILLS_REPOSITORY_BRANCH:-$BOOTSTRAP_DEFAULT_REPOSITORY_BRANCH}"

    runtime_repository_path="${CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH:-}"
    if [[ -n "$runtime_repository_path" ]] && ! bootstrap_current_script_owns_runtime_repository; then
        unset CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH
        unset CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT
        unset CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH
        unset CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH
        runtime_repository_path=""
    fi
    if [[ -n "$runtime_repository_path" ]]; then
        if ! bootstrap_repository_layout_is_complete "$runtime_repository_path"; then
            bootstrap_print_error "Staged bootstrap repository is missing the required codex_skills files: $runtime_repository_path"
            exit 1
        fi

        delegate_script_path="$runtime_repository_path/sync-skills.sh"
        if [[ ! -f "$delegate_script_path" ]]; then
            bootstrap_print_error "Staged bootstrap repository is missing sync-skills.sh: $runtime_repository_path"
            exit 1
        fi

        bootstrap_print_info "Using staged bootstrap repo: $runtime_repository_path"
        set +e
        bash "$delegate_script_path" "$@"
        exit_status=$?
        set -e
        bootstrap_cleanup_runtime_repository
        exit "$exit_status"
    fi

    bootstrap_ensure_git_available
    runtime_repository_path="$(bootstrap_prepare_repository_for_run "$repository_url" "$repository_branch")"
    export CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH="$current_script_path"
    export CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH="$runtime_repository_path"
    export CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH="$current_script_path"
    if bootstrap_repository_path_is_persistent; then
        export CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT="true"
    else
        export CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT="false"
    fi

    bootstrap_refresh_external_entry_script_copy "$current_script_path" "$runtime_repository_path/$(basename "$current_script_path")"
    if [[ "$BOOTSTRAP_EXTERNAL_SCRIPT_REFRESH_RESULT" == "refreshed" ]]; then
        bootstrap_print_info "Restarting into the refreshed standalone entry script before continuing."
        exec bash "$current_script_path" "$@"
    fi

    delegate_script_path="$runtime_repository_path/sync-skills.sh"
    if [[ ! -f "$delegate_script_path" ]]; then
        bootstrap_print_error "Staged bootstrap repository is missing sync-skills.sh: $runtime_repository_path"
        bootstrap_cleanup_runtime_repository
        exit 1
    fi

    bootstrap_print_info "Using fresh bootstrap repo: $runtime_repository_path"
    set +e
    bash "$delegate_script_path" "$@"
    exit_status=$?
    set -e
    bootstrap_cleanup_runtime_repository
    exit "$exit_status"
}

bootstrap_delegate_if_needed "$@"
refresh_bootstrap_entry_script_from_repo

detect_platform_name() {
    local uname_value
    uname_value="$(uname -s 2>/dev/null || true)"

    case "$uname_value" in
        Darwin*)
            echo "macos"
            ;;
        Linux*)
            echo "linux"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        *)
            case "$OSTYPE" in
                darwin*)
                    echo "macos"
                    ;;
                msys*|cygwin*|win32*)
                    echo "windows"
                    ;;
                *)
                    echo "linux"
                    ;;
            esac
            ;;
    esac
}

resolve_windows_home_directory() {
    if [[ -n "${USERPROFILE:-}" ]] && command -v cygpath >/dev/null 2>&1; then
        cygpath -u "$USERPROFILE"
        return 0
    fi

    if [[ -n "${USERPROFILE:-}" ]]; then
        printf '%s\n' "$USERPROFILE"
        return 0
    fi

    printf '%s\n' "$HOME"
}

resolve_codex_target_directory() {
    if [[ -n "${CODEX_TARGET_OVERRIDE:-}" ]]; then
        printf '%s\n' "$CODEX_TARGET_OVERRIDE"
        return 0
    fi

    if [[ "$(detect_platform_name)" == "windows" ]]; then
        printf '%s/.codex\n' "$(resolve_windows_home_directory)"
        return 0
    fi

    printf '%s/.codex\n' "$HOME"
}

PLATFORM_NAME="$(detect_platform_name)"
CODEX_TARGET="$(resolve_codex_target_directory)"

MANAGED_ROUTING_REQUIRED_CONFIG_LINES=(
    "- Route directly to the primary domain skill when the task clearly belongs to one surface."
    "- Use software-development-life-cycle when the work is mainly sequencing, cross-domain planning, or architecture framing."
    "- Start with reviewer only for audits, production-readiness checks, explicit gap-finding, or final validation."
    "- Return to reviewer for the final quality check when a separate implementation skill owned the work."
    "- Route to git-expert for repository-state, branching, and recovery work."
    "- If a non-trivial task clearly belongs to one specialist surface, do not stay solo by default; route to that owning skill or staff a bounded specialist lane instead of keeping all work in the main lane."
    "- Load specialist skills when the task clearly requires domain expertise: reviewer, software-development-life-cycle, web-development-life-cycle, mobile-development-life-cycle, backend-and-data-architecture, cloud-and-devops-expert, qa-and-automation-engineer, security-and-compliance-auditor, ui-design-systems-and-responsive-interfaces, ux-research-and-experience-strategy, git-expert, and memory-status-reporter."
)

MEMORY_STATUS_REQUIRED_CONFIG_LINES=(
    "- Route to memory-status-reporter for memory status, daily learning recaps, mistake ledgers, user-needs summaries, and heuristic growth reporting."
    "- When durable memory must change, delegate the write to memory-status-reporter when that lane is available, let it report what changed, and validate the touched memory files before finalizing."
    "- Use SESSION-STATE.md only for durable corrections, decisions, names, preferences, exact values, or confirmed constraints; use working-buffer.md only for long-running or high-context work; use research_cache.py, completion_gate.py, and agent_registry.py only when their specific trigger conditions apply."
    "- Start every non-trivial task by translating the raw request into a working brief: user story, desired outcome, constraints, assumptions, acceptance criteria, edge cases, and validation plan."
    "- If the request names a function, module, route, or script, keep the first implementation pass anchored to that named scope and widen only when traced impact proves it is required."
    "- If a non-trivial task clearly belongs to one specialist surface, do not stay solo by default; route to that owning skill or staff a bounded specialist lane instead of keeping all work in the main lane."
    "- For multi-part requests, preserve one top-level plan item per explicit user task and give each top-level item its own breakdown, validation target, and completion check before implementation."
    "- Strengthen vague prompts from repository, runtime, and memory evidence before acting; if business logic remains ambiguous, clarify instead of drifting."
    "- When business intent remains ambiguous after repository and runtime inspection, use request_user_input to confirm direction instead of guessing."
    "- For code work, prefer test-first when practical by starting with a failing test or executable acceptance check before implementation."
    "- Keep researching during implementation whenever APIs, tools, edge cases, or best practices are uncertain; do not trust stale memory alone."
    "- When validation, testing, or review reveals another in-scope bug or quality gap, keep iterating in the same turn and fix the next issue before handing off; only stop early when blocked by ambiguity, external access limits, or a clearly labeled out-of-scope item."
    "- Before starting a fresh research loop, check local memory and any freshness-aware research cache for a matching reusable finding; reuse it when the recorded freshness still fits the task, and only go to live external research for what is missing, stale, uncertain, or explicitly time-sensitive."
    "- Resolve workspace-scoped memory and shared research-cache paths before loading broad global memory: prefer ~/.codex/memories/workspaces/<workspace-slug>/ for shared project notes, ~/.codex/memories/workspaces/<workspace-slug>/workstreams/<workstream-key>/ for focused task notes, ~/.codex/memories/agents/<role>/<workspace-slug>/workstreams/<workstream-key>/ for role-local notes, ~/.codex/memories/agents/<role>/<workspace-slug>/workstreams/<workstream-key>/instances/<agent-instance>/ for reused agent-instance notes, and archive stale or superseded findings instead of replaying all history."
    "- Use a context retrieval ladder to save tokens: exact file or symbol search first, then targeted snippets, then full-file reads only for the files you will edit or directly depend on."
    "- Prefer surgical patches and modular edits: change only impacted ranges, keep stable prefixes for cache reuse, and avoid rewriting whole files when a targeted patch is sufficient."
    "- Prefer small, reviewable patch batches, then re-read the touched code and rerun the narrowest proving validation before adding the next batch."
    "- Prefer modular structure: keep entrypoints thin, move named logic into focused files, and separate backend, API, frontend, workers, and tests when the project spans those concerns."
    "- Do not stop at a workaround that merely appears to pass; confirm the root cause, implement the real fix, and avoid backward compatibility unless it was explicitly requested."
    "- Keep committed comments and documentation professional, concise, and neutral; avoid first-person and second-person pronouns unless quoting user-provided or source material."
    "- Before finalizing non-trivial work, re-read the working brief, acceptance criteria, and touched files, then append a compact Learning Snapshot grounded in memory artifacts when available."
    "- Before the final answer, reconcile every explicit user requirement against current evidence and do not present unresolved work as complete."
    "- For non-trivial tasks, record explicit user requirements in the scoped completion ledger and rerun completion_gate.py check before the final answer; do not close the workstream while tracked requirements remain pending, in progress, or blocked without an honest blocker report."
    "- A progress, recap, audit, or \"what is done or not done\" request does not suspend execution when fixable in-scope work remains; answer honestly, then continue the loop until the requested job is actually complete."
    "- If a tool call fails or is misused and the fix teaches a reusable lesson, record it as a mistake with tool name, symptom, cause, fix, and prevention note in rollout summaries and durable memory."
    "- Promote validated wins into rewarded patterns, repeated mistakes into penalty patterns, and reusable research into a freshness-aware cache so future tasks research only what is new."
    "- If a required sub-agent is still needed, do not use send_input(..., interrupt=true) or close it to rush synthesis; reuse the same live agent, keep the handoff bounded, and wait for terminal state unless the user explicitly cancels or redirects."
    "- When sub-agents are running, keep doing non-conflicting local work instead of idling, and wait only when the next step truly depends on their result."
)

config_has_required_memory_status_lines() {
    local config_file=$1
    local required_line

    [[ -f "$config_file" ]] || return 1

    for required_line in "${MEMORY_STATUS_REQUIRED_CONFIG_LINES[@]}"; do
        if ! grep -qF -- "$required_line" "$config_file"; then
            return 1
        fi
    done

    return 0
}

config_has_required_managed_routing_lines() {
    local config_file=$1
    local required_line

    [[ -f "$config_file" ]] || return 1

    for required_line in "${MANAGED_ROUTING_REQUIRED_CONFIG_LINES[@]}"; do
        if ! grep -qF -- "$required_line" "$config_file"; then
            return 1
        fi
    done

    return 0
}

config_has_any_managed_routing_lines() {
    local config_file=$1
    local required_line

    [[ -f "$config_file" ]] || return 1

    for required_line in "${MANAGED_ROUTING_REQUIRED_CONFIG_LINES[@]}"; do
        if grep -qF -- "$required_line" "$config_file"; then
            return 0
        fi
    done

    return 1
}

config_has_any_memory_status_lines() {
    local config_file=$1
    local required_line

    [[ -f "$config_file" ]] || return 1

    if grep -q "^\[agents\.memory-status-reporter\]" "$config_file"; then
        return 0
    fi

    for required_line in "${MEMORY_STATUS_REQUIRED_CONFIG_LINES[@]}"; do
        if grep -qF -- "$required_line" "$config_file"; then
            return 0
        fi
    done

    return 1
}

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    local title=$1
    printf '\n%s%s%s\n' "$BOLD$CYAN" "$title" "$NC"
}

print_menu_option() {
    local option_key=$1
    local option_label=$2
    printf '  %b[%s]%b %s\n' "$BOLD$CYAN" "$option_key" "$NC" "$option_label"
}

supports_interactive_output() {
    [[ -n "${TERM:-}" ]] && [[ "${TERM:-}" != "dumb" ]] && [[ -t 1 ]]
}

print_header() {
    local title=$1
    printf '\n%s%s%s\n' "$BOLD$CYAN" "$title" "$NC"
}

print_key_value() {
    local label=$1
    local value=$2
    printf '  %-28s %s\n' "$label" "$value"
}

print_status_line() {
    local status_label=$1
    local detail=$2
    printf '\r\033[2K%b[%s]%b %s' "$BOLD$CYAN" "$status_label" "$NC" "$detail"
}

finish_status_line() {
    local status_label=$1
    local detail=$2
    print_status_line "$status_label" "$detail"
    printf '\n'
}

print_inline_step() {
    local message=$1
    print_status_line "run" "$message"
}

print_inline_result() {
    local status=$1
    local detail=$2
    case "$status" in
        ok)
            finish_status_line "OK" "$detail"
            ;;
        warn)
            finish_status_line "WARN" "$detail"
            ;;
        error)
            finish_status_line "FAIL" "$detail"
            ;;
        *)
            finish_status_line "INFO" "$detail"
            ;;
    esac
}

run_task_line() {
    local task_label=$1
    shift
    run_quiet_with_spinner "$task_label" "$@"
}

run_with_spinner() {
    local loading_message=$1
    shift
    local spinner_pid
    local command_exit_code
    local spinner_delay=0.1

    if ! supports_interactive_output; then
        print_inline_step "$loading_message"
        set +e
        "$@"
        command_exit_code=$?
        set -e
        if [[ $command_exit_code -eq 0 ]]; then
            print_inline_result ok "$loading_message"
        else
            print_inline_result error "$loading_message"
        fi
        return $command_exit_code
    fi

    (
        local spinner_index=0
        while true; do
            spinner_index=$(((spinner_index + 1) % 4))
            case "$spinner_index" in
                0) print_status_line "run" "$loading_message |" ;;
                1) print_status_line "run" "$loading_message /" ;;
                2) print_status_line "run" "$loading_message -" ;;
                *) print_status_line "run" "$loading_message \\" ;;
            esac
            sleep "$spinner_delay"
        done
    ) &
    spinner_pid=$!

    set +e
    "$@"
    command_exit_code=$?
    set -e

    kill "$spinner_pid" >/dev/null 2>&1 || true
    wait "$spinner_pid" 2>/dev/null || true

    if [[ $command_exit_code -eq 0 ]]; then
        finish_status_line "OK" "$loading_message"
    else
        finish_status_line "FAIL" "$loading_message"
    fi

    return $command_exit_code
}

run_quiet_with_spinner() {
    local loading_message=$1
    shift
    local spinner_pid
    local command_exit_code
    local spinner_delay=0.1
    local temporary_output_file
    temporary_output_file="$(mktemp)"

    if ! supports_interactive_output; then
        print_inline_step "$loading_message"
        set +e
        "$@" >"$temporary_output_file" 2>&1
        command_exit_code=$?
        set -e
        if [[ $command_exit_code -eq 0 ]]; then
            print_inline_result ok "$loading_message"
            rm -f "$temporary_output_file"
            return 0
        fi

        print_inline_result error "$loading_message"
        cat "$temporary_output_file" >&2
        rm -f "$temporary_output_file"
        return $command_exit_code
    fi

    (
        local spinner_index=0
        while true; do
            spinner_index=$(((spinner_index + 1) % 4))
            case "$spinner_index" in
                0) print_status_line "run" "$loading_message |" ;;
                1) print_status_line "run" "$loading_message /" ;;
                2) print_status_line "run" "$loading_message -" ;;
                *) print_status_line "run" "$loading_message \\" ;;
            esac
            sleep "$spinner_delay"
        done
    ) &
    spinner_pid=$!

    set +e
    "$@" >"$temporary_output_file" 2>&1
    command_exit_code=$?
    set -e

    kill "$spinner_pid" >/dev/null 2>&1 || true
    wait "$spinner_pid" 2>/dev/null || true

    if [[ $command_exit_code -eq 0 ]]; then
        finish_status_line "OK" "$loading_message"
        rm -f "$temporary_output_file"
        return 0
    fi

    finish_status_line "FAIL" "$loading_message"
    cat "$temporary_output_file" >&2
    rm -f "$temporary_output_file"
    return $command_exit_code
}

parallel_worker_limit() {
    local detected_cpu_count

    if command -v nproc >/dev/null 2>&1; then
        detected_cpu_count="$(nproc)"
    elif command -v getconf >/dev/null 2>&1; then
        detected_cpu_count="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
    elif [[ -n "${NUMBER_OF_PROCESSORS:-}" ]]; then
        detected_cpu_count="$NUMBER_OF_PROCESSORS"
    else
        detected_cpu_count=4
    fi

    if [[ -z "$detected_cpu_count" ]] || ! [[ "$detected_cpu_count" =~ ^[0-9]+$ ]] || [[ "$detected_cpu_count" -lt 1 ]]; then
        detected_cpu_count=4
    fi

    if [[ "$detected_cpu_count" -gt 8 ]]; then
        detected_cpu_count=8
    fi

    printf '%s\n' "$detected_cpu_count"
}

run_items_in_parallel() {
    local worker_function_name=$1
    shift
    local worker_limit=$1
    shift
    local worker_items=("$@")
    local active_job_pids=()
    local overall_result=0
    local worker_item
    local completed_job_pid

    if [[ ${#worker_items[@]} -eq 0 ]]; then
        return 0
    fi

    for worker_item in "${worker_items[@]}"; do
        "$worker_function_name" "$worker_item" &
        active_job_pids+=("$!")
        if [[ ${#active_job_pids[@]} -ge $worker_limit ]]; then
            completed_job_pid="${active_job_pids[0]}"
            if ! wait "$completed_job_pid"; then
                overall_result=1
            fi
            active_job_pids=("${active_job_pids[@]:1}")
        fi
    done

    for completed_job_pid in "${active_job_pids[@]}"; do
        if ! wait "$completed_job_pid"; then
            overall_result=1
        fi
    done

    return $overall_result
}

list_repo_skill_directories() {
    local skill_directory

    for skill_directory in "$CODEX_SOURCE"/*/; do
        if [[ -f "$skill_directory/SKILL.md" ]]; then
            printf '%s\n' "$skill_directory"
        fi
    done | LC_ALL=C sort
}

populate_array_from_command() {
    local array_name=$1
    shift
    local item

    eval "$array_name=()"
    while IFS= read -r item; do
        [[ -n "$item" ]] || continue
        eval "$array_name+=(\"\$item\")"
    done < <("$@")
}

repo_skill_directories_array() {
    populate_array_from_command REPO_SKILL_DIRECTORIES list_repo_skill_directories
}

PARALLEL_VALIDATION_STATUS_DIRECTORY=""

validate_skill_directory_worker() {
    local skill_directory=$1
    local skill_name
    local skill_log_file
    skill_name="$(basename "$skill_directory")"
    skill_log_file="$PARALLEL_VALIDATION_STATUS_DIRECTORY/$skill_name.log"

    if validate_codex_skill_dir "$skill_directory" >"$skill_log_file" 2>&1; then
        : > "$PARALLEL_VALIDATION_STATUS_DIRECTORY/$skill_name.ok"
    else
        : > "$PARALLEL_VALIDATION_STATUS_DIRECTORY/$skill_name.failed"
    fi
}

collect_failed_skill_names_parallel() {
    local status_directory
    local worker_limit
    local skill_directory

    status_directory="$(mktemp -d)"
    PARALLEL_VALIDATION_STATUS_DIRECTORY="$status_directory"
    repo_skill_directories_array
    worker_limit="$(parallel_worker_limit)"

    if [[ ${#REPO_SKILL_DIRECTORIES[@]} -eq 0 ]]; then
        rm -rf "$status_directory"
        PARALLEL_VALIDATION_STATUS_DIRECTORY=""
        return 0
    fi

    run_items_in_parallel validate_skill_directory_worker "$worker_limit" "${REPO_SKILL_DIRECTORIES[@]}"

    for skill_directory in "${REPO_SKILL_DIRECTORIES[@]}"; do
        local skill_name
        skill_name="$(basename "$skill_directory")"
        if [[ -f "$status_directory/$skill_name.failed" ]]; then
            printf '%s\n' "$skill_name"
        fi
    done

    rm -rf "$status_directory"
    PARALLEL_VALIDATION_STATUS_DIRECTORY=""
}

PARALLEL_CHECKSUM_STATUS_DIRECTORY=""

verify_skill_checksum_worker() {
    local skill_name=$1
    local checksum_log_file="$PARALLEL_CHECKSUM_STATUS_DIRECTORY/$skill_name.log"

    if verify_skill_checksum "$skill_name" >"$checksum_log_file" 2>&1; then
        : > "$PARALLEL_CHECKSUM_STATUS_DIRECTORY/$skill_name.ok"
    else
        : > "$PARALLEL_CHECKSUM_STATUS_DIRECTORY/$skill_name.failed"
    fi
}

collect_failed_checksum_skill_names_parallel() {
    local status_directory
    local worker_limit
    local skill_name

    status_directory="$(mktemp -d)"
    PARALLEL_CHECKSUM_STATUS_DIRECTORY="$status_directory"
    repo_skill_names_array
    worker_limit="$(parallel_worker_limit)"

    if [[ ${#REPO_SKILL_NAMES[@]} -eq 0 ]]; then
        rm -rf "$status_directory"
        PARALLEL_CHECKSUM_STATUS_DIRECTORY=""
        return 0
    fi

    run_items_in_parallel verify_skill_checksum_worker "$worker_limit" "${REPO_SKILL_NAMES[@]}"

    for skill_name in "${REPO_SKILL_NAMES[@]}"; do
        if [[ -f "$status_directory/$skill_name.failed" ]]; then
            printf '%s\n' "$skill_name"
        fi
    done

    rm -rf "$status_directory"
    PARALLEL_CHECKSUM_STATUS_DIRECTORY=""
}

skill_manager_state_directory() {
    printf '%s/.codex-skill-manager\n' "$CODEX_TARGET"
}

skill_manager_manifest_directory() {
    printf '%s/manifests\n' "$(skill_manager_state_directory)"
}

skill_manager_metadata_file() {
    printf '%s/install-metadata.txt\n' "$(skill_manager_state_directory)"
}

skill_manager_local_home_agent_override_file() {
    printf '%s/local-home-agent-overrides.json\n' "$(skill_manager_state_directory)"
}

seed_default_local_home_agent_overrides() {
    local override_file
    local seed_result

    override_file="$(skill_manager_local_home_agent_override_file)"
    mkdir -p "$(skill_manager_state_directory)"

    seed_result="$(run_python - "$override_file" <<'PY'
from pathlib import Path
import json
import sys

override_file = Path(sys.argv[1])
if override_file.exists():
    try:
        payload = json.loads(override_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid local home-agent override file {override_file}: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit(f"Local home-agent override file must contain a JSON object: {override_file}")
else:
    payload = {}

agent_payload = payload.get("memory-status-reporter", {})
if agent_payload is None:
    agent_payload = {}
if not isinstance(agent_payload, dict):
    raise SystemExit(
        f"Local home-agent override entry for memory-status-reporter must be a JSON object: {override_file}"
    )

changed = False
if agent_payload.get("model") != "gpt-5.4":
    agent_payload["model"] = "gpt-5.4"
    changed = True
if agent_payload.get("reasoning_effort") != "low":
    agent_payload["reasoning_effort"] = "low"
    changed = True

payload["memory-status-reporter"] = agent_payload

if changed or not override_file.exists():
    override_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("updated")
else:
    print("unchanged")
PY
)" || return 1

    if [[ "$seed_result" == "updated" ]]; then
        print_success "Seeded local home-agent overrides for memory-status-reporter"
    fi
}

read_local_home_agent_override_value() {
    local home_agent_name=$1
    local field_name=$2
    local override_file

    override_file="$(skill_manager_local_home_agent_override_file)"
    [[ -f "$override_file" ]] || return 0

    run_python - "$override_file" "$home_agent_name" "$field_name" <<'PY'
from pathlib import Path
import json
import sys

override_file = Path(sys.argv[1])
home_agent_name = sys.argv[2]
field_name = sys.argv[3]

try:
    payload = json.loads(override_file.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid local home-agent override file {override_file}: {exc}")

if not isinstance(payload, dict):
    raise SystemExit(f"Local home-agent override file must contain a JSON object: {override_file}")

agent_payload = payload.get(home_agent_name, {})
if agent_payload is None:
    agent_payload = {}

if not isinstance(agent_payload, dict):
    raise SystemExit(
        f"Local home-agent override entry for {home_agent_name} must be a JSON object: {override_file}"
    )

value = agent_payload.get(field_name, "")
if value is None:
    value = ""

if value != "" and not isinstance(value, str):
    raise SystemExit(
        f"Local home-agent override field {field_name!r} for {home_agent_name} must be a string"
    )

print(value)
PY
}

pack_has_repo_managed_files() {
    local installed_skill_name
    local installed_agent_profile_name

    if [[ -f "$CODEX_TARGET/AGENTS.md" ]] || [[ -f "$CODEX_TARGET/00-skill-routing-and-escalation.md" ]]; then
        return 0
    fi

    if [[ -f "$CODEX_TARGET/agents/memory-status-reporter.toml" ]] || config_has_any_memory_status_lines "$CODEX_TARGET/config.toml" || config_has_any_managed_routing_lines "$CODEX_TARGET/config.toml" || config_has_any_repo_managed_agent_sections "$CODEX_TARGET/config.toml"; then
        return 0
    fi

    while IFS= read -r installed_agent_profile_name; do
        [[ -n "$installed_agent_profile_name" ]] || continue
        if [[ -f "$CODEX_TARGET/agent-profiles/$installed_agent_profile_name.toml" ]]; then
            return 0
        fi
    done < <(list_repo_agent_profile_names)

    while IFS= read -r installed_skill_name; do
        [[ -n "$installed_skill_name" ]] || continue
        if [[ -d "$CODEX_TARGET/skills/$installed_skill_name" ]]; then
            return 0
        fi
    done < <(list_repo_skill_names)

    return 1
}

pack_is_installed() {
    if [[ -f "$(skill_manager_metadata_file)" ]] || [[ -f "$(managed_skill_inventory_file)" ]] || [[ -f "$(managed_home_agent_inventory_file)" ]] || [[ -f "$(managed_agent_profile_inventory_file)" ]]; then
        return 0
    fi

    pack_has_repo_managed_files
}

ensure_skill_manager_state_directories() {
    mkdir -p "$(skill_manager_manifest_directory)/source"
    mkdir -p "$(skill_manager_manifest_directory)/target"
}

get_repo_version() {
    git -C "$CODEX_SOURCE" rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

get_manager_version() {
    printf '%s\n' "$SYNC_SKILLS_MANAGER_VERSION"
}

get_installed_version() {
    local metadata_file
    metadata_file="$(skill_manager_metadata_file)"

    if [[ -f "$metadata_file" ]]; then
        awk -F= '/^repo_version=/{print $2}' "$metadata_file"
        return 0
    fi

    if ! pack_is_installed; then
        echo "not installed"
        return 0
    fi

    echo "unknown"
}

sync_script_version_from_file() {
    local script_path=${1:-"$CODEX_SOURCE/sync-skills.sh"}
    local version_line

    if [[ ! -f "$script_path" ]]; then
        printf 'missing\n'
        return 0
    fi

    version_line="$(grep -E '^SYNC_SKILLS_MANAGER_VERSION=' "$script_path" | head -n 1 || true)"
    if [[ -z "$version_line" ]]; then
        printf 'unknown\n'
        return 0
    fi

    version_line="${version_line#*=}"
    version_line="${version_line#\"}"
    version_line="${version_line%\"}"
    printf '%s\n' "$version_line"
}

sync_script_checksum_from_file() {
    local script_path=${1:-"$CODEX_SOURCE/sync-skills.sh"}

    if [[ ! -f "$script_path" ]]; then
        printf 'missing\n'
        return 0
    fi

    md5_for_file "$script_path"
}

git_repository_available() {
    command -v git >/dev/null 2>&1 && git -C "$CODEX_SOURCE" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

git_remote_url_for_name() {
    local remote_name=$1
    git -C "$CODEX_SOURCE" remote get-url "$remote_name" 2>/dev/null || true
}

git_fetch_remote_noninteractive() {
    local remote_name=$1
    GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never git -C "$CODEX_SOURCE" fetch --prune "$remote_name"
}

git_current_branch() {
    git -C "$CODEX_SOURCE" rev-parse --abbrev-ref HEAD 2>/dev/null || true
}

git_upstream_ref() {
    git -C "$CODEX_SOURCE" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true
}

git_default_remote_head_ref() {
    git -C "$CODEX_SOURCE" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null || true
}

git_resolve_update_source_ref() {
    local upstream_ref
    local current_branch
    local remote_head_ref

    upstream_ref="$(git_upstream_ref)"
    if [[ -n "$upstream_ref" ]]; then
        printf '%s\n' "$upstream_ref"
        return 0
    fi

    current_branch="$(git_current_branch)"
    if [[ -n "$current_branch" ]] && git -C "$CODEX_SOURCE" show-ref --verify --quiet "refs/remotes/origin/$current_branch"; then
        printf 'origin/%s\n' "$current_branch"
        return 0
    fi

    remote_head_ref="$(git_default_remote_head_ref)"
    if [[ -n "$remote_head_ref" ]]; then
        printf '%s\n' "$remote_head_ref"
        return 0
    fi

    return 1
}

git_worktree_is_clean() {
    [[ -z "$(git -C "$CODEX_SOURCE" status --porcelain 2>/dev/null)" ]]
}

git_update_relationship() {
    local update_ref=$1
    local local_commit
    local remote_commit
    local merge_base

    local_commit="$(git -C "$CODEX_SOURCE" rev-parse HEAD 2>/dev/null || true)"
    remote_commit="$(git -C "$CODEX_SOURCE" rev-parse "$update_ref" 2>/dev/null || true)"
    merge_base="$(git -C "$CODEX_SOURCE" merge-base HEAD "$update_ref" 2>/dev/null || true)"

    if [[ -z "$local_commit" ]] || [[ -z "$remote_commit" ]] || [[ -z "$merge_base" ]]; then
        printf 'unknown\n'
        return 0
    fi

    if [[ "$local_commit" == "$remote_commit" ]]; then
        printf 'up_to_date\n'
    elif [[ "$merge_base" == "$local_commit" ]]; then
        printf 'behind\n'
    elif [[ "$merge_base" == "$remote_commit" ]]; then
        printf 'ahead\n'
    else
        printf 'diverged\n'
    fi
}

write_install_metadata() {
    local metadata_file
    metadata_file="$(skill_manager_metadata_file)"

    ensure_skill_manager_state_directories
    cat > "$metadata_file" <<EOF
repo_version=$(get_repo_version)
manager_version=$(get_manager_version)
updated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
platform=$PLATFORM_NAME
target=$CODEX_TARGET
EOF
}

managed_skill_inventory_file() {
    printf '%s/managed-skills.txt\n' "$(skill_manager_state_directory)"
}

managed_home_agent_inventory_file() {
    printf '%s/managed-home-agents.txt\n' "$(skill_manager_state_directory)"
}

managed_agent_profile_inventory_file() {
    printf '%s/managed-agent-profiles.txt\n' "$(skill_manager_state_directory)"
}

list_skill_agent_config_files() {
    local skill_name=$1
    local agents_directory="$CODEX_SOURCE/$skill_name/agents"

    [[ -d "$agents_directory" ]] || return 0

    find "$agents_directory" -maxdepth 1 -type f -name '*.yaml' | LC_ALL=C sort
}

home_agent_name_from_agent_config() {
    local skill_name=$1
    local agent_config_path=$2
    local agent_config_basename
    agent_config_basename="$(basename "$agent_config_path" .yaml)"

    if [[ "$agent_config_basename" == "openai" ]]; then
        printf '%s\n' "$skill_name"
        return 0
    fi

    printf '%s\n' "$agent_config_basename"
}

write_managed_skill_inventory_from_repo() {
    local inventory_file
    inventory_file="$(managed_skill_inventory_file)"

    ensure_skill_manager_state_directories
    list_repo_skill_names > "$inventory_file"
}

emit_managed_home_agent_inventory_from_repo() {
    local skill_name
    local agent_config_path
    local home_agent_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        while IFS= read -r agent_config_path; do
            [[ -n "$agent_config_path" ]] || continue
            home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
            printf '%s|%s\n' "$skill_name" "$home_agent_name"
        done < <(list_skill_agent_config_files "$skill_name")
    done < <(list_repo_skill_names) | LC_ALL=C sort -u
}

write_managed_home_agent_inventory_from_repo() {
    local inventory_file

    inventory_file="$(managed_home_agent_inventory_file)"
    ensure_skill_manager_state_directories

    emit_managed_home_agent_inventory_from_repo > "$inventory_file"
}

write_managed_agent_profile_inventory_from_repo() {
    local inventory_file

    inventory_file="$(managed_agent_profile_inventory_file)"
    ensure_skill_manager_state_directories
    list_repo_agent_profile_names > "$inventory_file"
}

remove_skill_from_managed_inventory() {
    local skill_name=$1
    local inventory_file
    local temporary_inventory_file
    inventory_file="$(managed_skill_inventory_file)"

    [[ -f "$inventory_file" ]] || return 0

    temporary_inventory_file="$(mktemp)"
    grep -vxF -- "$skill_name" "$inventory_file" > "$temporary_inventory_file" || true
    mv "$temporary_inventory_file" "$inventory_file"
}

remove_home_agent_from_managed_inventory() {
    local skill_name=$1
    local home_agent_name=$2
    local inventory_file
    local temporary_inventory_file

    inventory_file="$(managed_home_agent_inventory_file)"
    [[ -f "$inventory_file" ]] || return 0

    temporary_inventory_file="$(mktemp)"
    grep -vxF -- "$skill_name|$home_agent_name" "$inventory_file" > "$temporary_inventory_file" || true
    mv "$temporary_inventory_file" "$inventory_file"
}

remove_agent_profile_from_managed_inventory() {
    local agent_profile_name=$1
    local inventory_file
    local temporary_inventory_file

    inventory_file="$(managed_agent_profile_inventory_file)"
    [[ -f "$inventory_file" ]] || return 0

    temporary_inventory_file="$(mktemp)"
    grep -vxF -- "$agent_profile_name" "$inventory_file" > "$temporary_inventory_file" || true
    mv "$temporary_inventory_file" "$inventory_file"
}

list_tracked_managed_skill_names() {
    local inventory_file
    local skill_name
    inventory_file="$(managed_skill_inventory_file)"

    if [[ -f "$inventory_file" ]]; then
        awk 'NF {print $0}' "$inventory_file" | LC_ALL=C sort -u
        return 0
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        if [[ -d "$CODEX_TARGET/skills/$skill_name" ]]; then
            printf '%s\n' "$skill_name"
        fi
    done < <(list_repo_skill_names) | LC_ALL=C sort
}

list_tracked_managed_agent_profile_names() {
    local inventory_file
    local agent_profile_name

    inventory_file="$(managed_agent_profile_inventory_file)"
    if [[ -f "$inventory_file" ]]; then
        awk 'NF {print $0}' "$inventory_file" | LC_ALL=C sort -u
        return 0
    fi

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        if [[ -f "$CODEX_TARGET/agent-profiles/$agent_profile_name.toml" ]]; then
            printf '%s\n' "$agent_profile_name"
        fi
    done < <(list_repo_agent_profile_names) | LC_ALL=C sort
}

list_removed_repo_managed_skill_names() {
    local skill_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        if [[ ! -d "$CODEX_SOURCE/$skill_name" ]] || [[ ! -f "$CODEX_SOURCE/$skill_name/SKILL.md" ]]; then
            printf '%s\n' "$skill_name"
        fi
    done < <(list_tracked_managed_skill_names) | LC_ALL=C sort
}

list_removed_repo_managed_agent_profile_names() {
    local agent_profile_name

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        if ! grep -qxF -- "$agent_profile_name" < <(list_repo_agent_profile_names); then
            printf '%s\n' "$agent_profile_name"
        fi
    done < <(list_tracked_managed_agent_profile_names) | LC_ALL=C sort
}

list_tracked_home_agent_names_for_skill() {
    local skill_name=$1
    local inventory_file

    inventory_file="$(managed_home_agent_inventory_file)"
    if [[ -f "$inventory_file" ]]; then
        awk -F'|' -v selected_skill="$skill_name" '$1 == selected_skill && NF >= 2 {print $2}' "$inventory_file" | LC_ALL=C sort -u
        return 0
    fi

    printf '%s\n' "$skill_name"
}

expected_reasoning_for_home_agent() {
    local home_agent_name=$1
    local fallback_reasoning=$2

    printf '%s\n' "$fallback_reasoning"
}

PYTHON_LAUNCHER=""

detect_python_launcher() {
    if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
        echo "python3"
        return 0
    fi

    if command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
        echo "python"
        return 0
    fi

    if command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
        echo "py -3"
        return 0
    fi

    return 1
}

config_has_agent_section() {
    local config_file=$1
    local home_agent_name=$2
    local section_header="[agents.$home_agent_name]"

    [[ -f "$config_file" ]] || return 1
    grep -qF -- "$section_header" "$config_file"
}

config_has_any_repo_managed_agent_sections() {
    local config_file=$1
    local home_agent_name

    [[ -f "$config_file" ]] || return 1

    while IFS= read -r home_agent_name; do
        [[ -n "$home_agent_name" ]] || continue
        if config_has_agent_section "$config_file" "$home_agent_name"; then
            return 0
        fi
    done < <(list_repo_agent_profile_names)

    return 1
}

ensure_python_shell_aliases() {
    case "$PYTHON_LAUNCHER" in
        "py -3")
            if ! python3 -c "import sys" >/dev/null 2>&1; then
                python3() {
                    py -3 "$@"
                }
            fi
            ;;
        "python")
            if ! python3 -c "import sys" >/dev/null 2>&1; then
                python3() {
                    python "$@"
                }
            fi
            ;;
    esac
}

ensure_python_launcher() {
    if [[ -n "${PYTHON_LAUNCHER:-}" ]]; then
        ensure_python_shell_aliases
        return 0
    fi

    PYTHON_LAUNCHER="$(detect_python_launcher)" || {
        print_error "Python 3 is required for install, update, and config wiring. Install Python 3 or ensure python, python3, or py -3 is available."
        return 1
    }

    ensure_python_shell_aliases
    return 0
}

run_python() {
    ensure_python_launcher || return 1

    case "$PYTHON_LAUNCHER" in
        "py -3")
            py -3 "$@"
            ;;
        *)
            "$PYTHON_LAUNCHER" "$@"
            ;;
    esac
}

ensure_sync_runtime_prerequisites() {
    ensure_python_launcher || return 1

    if ! md5_for_file "$CODEX_SOURCE/AGENTS.md" >/dev/null 2>&1; then
        return 1
    fi

    return 0
}

SKILL_SYNC_DIRECTORIES=(
    "references"
    "scripts"
    "data"
    "agents"
    "templates"
    "examples"
    "assets"
)

md5_for_file() {
    local file_path=$1

    if command -v md5sum >/dev/null 2>&1; then
        md5sum "$file_path" | awk '{sub(/^\\/, "", $1); print tolower($1)}'
        return 0
    fi

    if command -v md5 >/dev/null 2>&1; then
        md5 -q "$file_path" | tr '[:upper:]' '[:lower:]'
        return 0
    fi

    if command -v openssl >/dev/null 2>&1; then
        openssl md5 "$file_path" | awk '{print tolower($NF)}'
        return 0
    fi

    if command -v certutil >/dev/null 2>&1; then
        local certutil_path="$file_path"
        if command -v cygpath >/dev/null 2>&1; then
            certutil_path="$(cygpath -w "$file_path")"
        fi
        certutil -hashfile "$certutil_path" MD5 | awk 'NR==2 {print tolower($1)}'
        return 0
    fi

    print_error "No MD5 checksum tool is available on this system"
    return 1
}

files_have_same_content() {
    local source_path=$1
    local target_path=$2

    [[ -f "$source_path" ]] || return 1
    [[ -f "$target_path" ]] || return 1

    if command -v cmp >/dev/null 2>&1; then
        cmp -s "$source_path" "$target_path"
        return $?
    fi

    diff -q "$source_path" "$target_path" >/dev/null 2>&1
}

skill_directories_match_without_md5() {
    local source_directory=$1
    local target_directory=$2

    [[ -d "$source_directory" ]] || return 1
    [[ -d "$target_directory" ]] || return 1

    diff -qr \
        --exclude='tests' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.DS_Store' \
        "$source_directory" "$target_directory" >/dev/null 2>&1
}

build_directory_manifest() {
    local directory_path=$1

    [[ -d "$directory_path" ]] || return 1

    (
        cd "$directory_path"
        while IFS= read -r relative_path; do
            local normalized_path
            local checksum
            normalized_path="${relative_path#./}"
            checksum="$(md5_for_file "$directory_path/$normalized_path")"
            printf '%s|%s\n' "$normalized_path" "$checksum"
        done < <(find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '.DS_Store' | LC_ALL=C sort)
    )
}

build_skill_manifest() {
    local directory_path=$1
    local relative_directory

    [[ -d "$directory_path" ]] || return 1

    (
        cd "$directory_path"

        if [[ -f "SKILL.md" ]]; then
            printf '%s|%s\n' "SKILL.md" "$(md5_for_file "$directory_path/SKILL.md")"
        fi

        for relative_directory in "${SKILL_SYNC_DIRECTORIES[@]}"; do
            if [[ -d "$relative_directory" ]]; then
                while IFS= read -r relative_path; do
                    local normalized_path
                    local checksum
                    normalized_path="${relative_path#./}"
                    checksum="$(md5_for_file "$directory_path/$normalized_path")"
                    printf '%s|%s\n' "$normalized_path" "$checksum"
                done < <(find "$relative_directory" -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '.DS_Store' | LC_ALL=C sort)
            fi
        done | LC_ALL=C sort
    )
}

save_manifest_snapshot() {
    local manifest_kind=$1
    local manifest_name=$2
    local manifest_source_path=$3

    ensure_skill_manager_state_directories
    cp "$manifest_source_path" "$(skill_manager_manifest_directory)/$manifest_kind/$manifest_name.md5"
}

list_repo_skill_names() {
    local skill_dir
    for skill_dir in "$CODEX_SOURCE"/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            basename "$skill_dir"
        fi
    done | LC_ALL=C sort
}

list_repo_agent_profile_names() {
    local skill_name
    local agent_config_path

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        while IFS= read -r agent_config_path; do
            [[ -n "$agent_config_path" ]] || continue
            home_agent_name_from_agent_config "$skill_name" "$agent_config_path"
        done < <(list_skill_agent_config_files "$skill_name")
    done < <(list_repo_skill_names) | LC_ALL=C sort -u
}

repo_skill_names_array() {
    populate_array_from_command REPO_SKILL_NAMES list_repo_skill_names
}

installed_skill_names_array() {
    populate_array_from_command INSTALLED_SKILL_NAMES list_installed_skill_names
}

list_installed_skill_names() {
    local skill_dir

    [[ -d "$CODEX_TARGET/skills" ]] || return 0

    for skill_dir in "$CODEX_TARGET"/skills/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            basename "$skill_dir"
        fi
    done | LC_ALL=C sort
}

copy_skill_directory_if_present() {
    local source_skill_directory=$1
    local target_skill_directory=$2
    local relative_directory=$3

    if [[ -d "$source_skill_directory/$relative_directory" ]]; then
        mkdir -p "$target_skill_directory/$relative_directory"
        cp -r "$source_skill_directory/$relative_directory/." "$target_skill_directory/$relative_directory/"
    fi
}

prune_runtime_noise_in_directory() {
    local directory_path=$1

    [[ -d "$directory_path" ]] || return 0

    find "$directory_path" -type d \( -name tests -o -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
    find "$directory_path" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
}

prune_repo_managed_installation_noise() {
    local skill_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        prune_runtime_noise_in_directory "$CODEX_TARGET/skills/$skill_name"
        prune_runtime_noise_in_directory "$CODEX_TARGET/$skill_name"
    done < <(list_repo_skill_names)
}

list_repo_managed_installation_noise_paths() {
    local skill_name
    local skill_directory

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        for skill_directory in "$CODEX_TARGET/skills/$skill_name" "$CODEX_TARGET/$skill_name"; do
            [[ -d "$skill_directory" ]] || continue
            find "$skill_directory" \( -type d \( -name tests -o -name __pycache__ -o -name .pytest_cache \) -o -type f \( -name '*.pyc' -o -name '*.pyo' \) \) -print
        done
    done < <(list_repo_skill_names) | LC_ALL=C sort -u
}

verify_repo_managed_installation_hygiene() {
    local leaked_path
    local failed=0

    while IFS= read -r leaked_path; do
        [[ -n "$leaked_path" ]] || continue
        print_error "Managed install contains runtime-noise artifact: $leaked_path"
        failed=1
    done < <(list_repo_managed_installation_noise_paths)

    if [[ $failed -eq 0 ]]; then
        print_success "Installed runtime hygiene verified"
        return 0
    fi

    print_error "Managed install runtime hygiene verification failed"
    return 1
}

copy_managed_skill_content() {
    local source_skill_directory=$1
    local target_skill_directory=$2
    local relative_directory

    cp "$source_skill_directory/SKILL.md" "$target_skill_directory/SKILL.md"

    for relative_directory in "${SKILL_SYNC_DIRECTORIES[@]}"; do
        copy_skill_directory_if_present "$source_skill_directory" "$target_skill_directory" "$relative_directory"
    done

    prune_runtime_noise_in_directory "$target_skill_directory"
}

verify_root_file_checksum() {
    local relative_path=$1
    local source_path="$CODEX_SOURCE/$relative_path"
    local target_path="$CODEX_TARGET/$relative_path"
    local source_checksum
    local target_checksum

    if [[ ! -f "$source_path" ]]; then
        print_error "Source file missing for checksum verification: $source_path"
        return 1
    fi

    if [[ ! -f "$target_path" ]]; then
        print_error "Target file missing for checksum verification: $target_path"
        return 1
    fi

    source_checksum="$(md5_for_file "$source_path")"
    target_checksum="$(md5_for_file "$target_path")"

    if [[ "$source_checksum" != "$target_checksum" ]]; then
        print_error "Checksum mismatch for $relative_path"
        return 1
    fi

    print_success "MD5 verified for $relative_path"
}

verify_skill_checksum() {
    local skill_name=$1
    local source_directory="$CODEX_SOURCE/$skill_name"
    local target_directory="$CODEX_TARGET/skills/$skill_name"
    local source_manifest
    local target_manifest

    if [[ ! -d "$source_directory" ]]; then
        print_error "Skill does not exist in repo: $skill_name"
        return 1
    fi

    if [[ ! -d "$target_directory" ]]; then
        print_error "Skill is not installed in Codex home: $skill_name"
        return 1
    fi

    source_manifest="$(mktemp)"
    target_manifest="$(mktemp)"

    build_skill_manifest "$source_directory" > "$source_manifest"
    build_skill_manifest "$target_directory" > "$target_manifest"

    save_manifest_snapshot "source" "$skill_name" "$source_manifest"
    save_manifest_snapshot "target" "$skill_name" "$target_manifest"

    if diff -u "$source_manifest" "$target_manifest" >/dev/null; then
        rm -f "$source_manifest" "$target_manifest"
        print_success "MD5 verified for skill: $skill_name"
        return 0
    fi

    print_error "MD5 verification failed for skill: $skill_name"
    diff -u "$source_manifest" "$target_manifest" || true
    rm -f "$source_manifest" "$target_manifest"
    return 1
}

find_agent_config_path_for_home_agent_name() {
    local selected_home_agent_name=$1
    local skill_name
    local agent_config_path
    local home_agent_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        while IFS= read -r agent_config_path; do
            [[ -n "$agent_config_path" ]] || continue
            home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
            if [[ "$home_agent_name" == "$selected_home_agent_name" ]]; then
                printf '%s\n' "$agent_config_path"
                return 0
            fi
        done < <(list_skill_agent_config_files "$skill_name")
    done < <(list_repo_skill_names)

    return 1
}

verify_agent_profile_checksum() {
    local agent_profile_name=$1
    local target_path="$CODEX_TARGET/agent-profiles/$agent_profile_name.toml"
    local expected_profile_path
    local agent_config_path
    local expected_checksum
    local target_checksum

    agent_config_path="$(find_agent_config_path_for_home_agent_name "$agent_profile_name")" || {
        print_error "Unable to resolve source agent config for agent profile: $agent_profile_name"
        return 1
    }

    if [[ ! -f "$target_path" ]]; then
        print_error "Agent profile is not installed in Codex home: $agent_profile_name"
        return 1
    fi

   expected_profile_path="$(mktemp)"
    write_codex_agent_toml "$agent_config_path" "$expected_profile_path" "$agent_profile_name" "agent-profile" >/dev/null || {
        rm -f "$expected_profile_path"
        print_error "Unable to generate expected skill agent profile: $agent_profile_name"
        return 1
    }

    expected_checksum="$(md5_for_file "$expected_profile_path")"
    target_checksum="$(md5_for_file "$target_path")"

    if [[ "$expected_checksum" != "$target_checksum" ]]; then
        print_error "MD5 verification failed for skill agent profile: $agent_profile_name"
        rm -f "$expected_profile_path"
        return 1
    fi

    rm -f "$expected_profile_path"
    print_success "MD5 verified for skill agent profile: $agent_profile_name"
}

verify_pack_checksums() {
    local failed=0
    local skill_name
    local failed_checksum_skill_name
    local agent_profile_name

    if ! pack_is_installed; then
        print_error "Codex skill pack is not installed in Codex home: $CODEX_TARGET"
        return 1
    fi

    while IFS= read -r root_guidance_relative_path; do
        [[ -n "$root_guidance_relative_path" ]] || continue
        run_task_line "verify $root_guidance_relative_path" verify_root_file_checksum "$root_guidance_relative_path" || failed=1
    done < <(list_root_guidance_relative_paths)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        if ! verify_agent_profile_checksum "$agent_profile_name"; then
            failed=1
        fi
    done < <(list_repo_agent_profile_names)

    while IFS= read -r failed_checksum_skill_name; do
        [[ -n "$failed_checksum_skill_name" ]] || continue
        print_error "MD5 verification failed for installed skill: $failed_checksum_skill_name"
        failed=1
    done < <(collect_failed_checksum_skill_names_parallel)

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        print_error "Managed installed skill no longer exists in the repo: $skill_name"
        failed=1
    done < <(list_removed_repo_managed_skill_names)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        print_error "Managed installed agent profile no longer exists in the repo: $agent_profile_name"
        failed=1
    done < <(list_removed_repo_managed_agent_profile_names)

    run_task_line "verify runtime hygiene" verify_repo_managed_installation_hygiene || failed=1

    if [[ $failed -eq 0 ]]; then
        print_success "All MD5 verification checks passed"
        return 0
    fi

    print_error "One or more MD5 verification checks failed"
    return 1
}

verify_root_file_sync_match() {
    local relative_path=$1
    local source_path="$CODEX_SOURCE/$relative_path"
    local target_path="$CODEX_TARGET/$relative_path"

    if [[ ! -f "$source_path" ]]; then
        print_error "Source file missing for sync verification: $source_path"
        return 1
    fi

    if [[ ! -f "$target_path" ]]; then
        print_error "Target file missing for sync verification: $target_path"
        return 1
    fi

    if ! files_have_same_content "$source_path" "$target_path"; then
        print_error "Content mismatch for synced root file: $relative_path"
        return 1
    fi

    print_success "Content verified for $relative_path"
    return 0
}

verify_agent_profile_sync_match() {
    local agent_profile_name=$1
    local target_path="$CODEX_TARGET/agent-profiles/$agent_profile_name.toml"
    local expected_profile_path
    local agent_config_path

    agent_config_path="$(find_agent_config_path_for_home_agent_name "$agent_profile_name")" || {
        print_error "Unable to resolve source agent config for sync verification: $agent_profile_name"
        return 1
    }

    if [[ ! -f "$target_path" ]]; then
        print_error "Agent profile is not installed in Codex home: $agent_profile_name"
        return 1
    fi

    expected_profile_path="$(mktemp)"
    write_codex_agent_toml "$agent_config_path" "$expected_profile_path" "$agent_profile_name" "agent-profile" >/dev/null || {
        rm -f "$expected_profile_path"
        print_error "Unable to generate expected skill agent profile: $agent_profile_name"
        return 1
    }

    if ! files_have_same_content "$expected_profile_path" "$target_path"; then
        rm -f "$expected_profile_path"
        print_error "Content verification failed for skill agent profile: $agent_profile_name"
        return 1
    fi

    rm -f "$expected_profile_path"
    print_success "Content verified for skill agent profile: $agent_profile_name"
    return 0
}

verify_inventory_file_matches_command() {
    local inventory_label=$1
    local inventory_file=$2
    shift 2
    local expected_inventory_file

    if [[ ! -f "$inventory_file" ]]; then
        print_error "Missing managed inventory file: $inventory_label ($inventory_file)"
        return 1
    fi

    expected_inventory_file="$(mktemp)"
    "$@" > "$expected_inventory_file" || {
        rm -f "$expected_inventory_file"
        print_error "Unable to build expected managed inventory for: $inventory_label"
        return 1
    }

    if ! diff -u "$expected_inventory_file" "$inventory_file" >/dev/null; then
        rm -f "$expected_inventory_file"
        print_error "Managed inventory drift detected for: $inventory_label"
        return 1
    fi

    rm -f "$expected_inventory_file"
    print_success "Managed inventory verified for: $inventory_label"
    return 0
}

verify_managed_inventory_files_match_repo() {
    local failed=0

    verify_inventory_file_matches_command \
        "skills" \
        "$(managed_skill_inventory_file)" \
        list_repo_skill_names || failed=1
    verify_inventory_file_matches_command \
        "home agents" \
        "$(managed_home_agent_inventory_file)" \
        emit_managed_home_agent_inventory_from_repo || failed=1
    verify_inventory_file_matches_command \
        "agent profiles" \
        "$(managed_agent_profile_inventory_file)" \
        list_repo_agent_profile_names || failed=1

    if [[ $failed -eq 0 ]]; then
        print_success "All managed inventories match the repo"
        return 0
    fi

    print_error "One or more managed inventories drifted from the repo"
    return 1
}

verify_memory_status_reporter_home_wiring_present() {
    local memory_status_home_agent_file="$CODEX_TARGET/agents/memory-status-reporter.toml"
    local home_config_file="$CODEX_TARGET/config.toml"

    if [[ ! -f "$memory_status_home_agent_file" ]]; then
        print_error "memory-status-reporter home agent wiring is missing: $memory_status_home_agent_file"
        return 1
    fi

    if ! config_has_required_memory_status_lines "$home_config_file"; then
        print_error "Codex home config is missing required memory-status-reporter wiring: $home_config_file"
        return 1
    fi

    print_success "memory-status-reporter home wiring verified"
    return 0
}

verify_managed_config_routing_present() {
    local home_config_file="$CODEX_TARGET/config.toml"

    if ! config_has_required_managed_routing_lines "$home_config_file"; then
        print_error "Codex home config is missing required managed routing instructions: $home_config_file"
        return 1
    fi

    print_success "Managed routing config verified"
    return 0
}

verify_home_agent_config_section_sync_match() {
    local openai_yaml_path=$1
    local home_agent_name=$2
    local home_config_file="$CODEX_TARGET/config.toml"
    local short_description

    if [[ ! -f "$home_config_file" ]]; then
        print_error "Codex home config is missing: $home_config_file"
        return 1
    fi

    short_description=$(extract_codex_openai_value "$openai_yaml_path" "short_description") || {
        print_error "Unable to extract short_description for $home_agent_name"
        return 1
    }

    run_python - "$home_config_file" "$home_agent_name" "$short_description" <<'PY'
from pathlib import Path
import json
import re
import sys

config_path = Path(sys.argv[1])
home_agent_name = sys.argv[2]
short_description = sys.argv[3]
config_text = config_path.read_text(encoding="utf-8")

section_pattern = re.compile(rf"(?ms)^\[agents\.{re.escape(home_agent_name)}\]\n.*?(?=^\[|\Z)")
section_match = section_pattern.search(config_text)
if section_match is None:
    raise SystemExit(f"Missing [agents.{home_agent_name}] section in {config_path}")

section_text = section_match.group(0)
expected_description_line = f"description = {json.dumps(short_description)}"
expected_config_file_line = f"config_file = {json.dumps(f'agents/{home_agent_name}.toml')}"

if expected_description_line not in section_text:
    raise SystemExit(
        f"[agents.{home_agent_name}] section has unexpected description in {config_path}"
    )
if expected_config_file_line not in section_text:
    raise SystemExit(
        f"[agents.{home_agent_name}] section has unexpected config_file path in {config_path}"
    )
PY

    print_success "Config section verified for managed home agent: $home_agent_name"
    return 0
}

verify_home_agent_config_sections_match_repo() {
    local skill_name
    local agent_config_path
    local home_agent_name
    local failed=0

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        while IFS= read -r agent_config_path; do
            [[ -n "$agent_config_path" ]] || continue
            home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
            if ! verify_home_agent_config_section_sync_match "$agent_config_path" "$home_agent_name"; then
                failed=1
            fi
        done < <(list_skill_agent_config_files "$skill_name")
    done < <(list_repo_skill_names)

    if [[ $failed -eq 0 ]]; then
        print_success "Managed [agents.*] config sections verified"
        return 0
    fi

    print_error "One or more managed [agents.*] config sections are missing or mismatched"
    return 1
}

verify_synced_skill_and_home_agent_presence() {
    local skill_name
    local skill_path
    local home_agent_name
    local agent_config_path
    local failed=0

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        skill_path="$CODEX_TARGET/skills/$skill_name/SKILL.md"
        if [[ ! -f "$skill_path" ]]; then
            print_error "Managed skill is missing after sync: $skill_name"
            failed=1
        fi

        while IFS= read -r agent_config_path; do
            [[ -n "$agent_config_path" ]] || continue
            home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
            if [[ ! -f "$CODEX_TARGET/agents/$home_agent_name.toml" ]]; then
                print_error "Managed home agent is missing after sync: $home_agent_name"
                failed=1
            fi
        done < <(list_skill_agent_config_files "$skill_name")
    done < <(list_repo_skill_names)

    if [[ $failed -eq 0 ]]; then
        print_success "Managed skill and home-agent presence verified"
        return 0
    fi

    print_error "One or more managed skills or home agents are missing after sync"
    return 1
}

verify_sync_operation_health() {
    local failed=0
    local root_guidance_relative_path
    local skill_name
    local agent_profile_name

    if ! pack_is_installed; then
        print_error "Codex skill pack is not installed in Codex home: $CODEX_TARGET"
        return 1
    fi

    while IFS= read -r root_guidance_relative_path; do
        [[ -n "$root_guidance_relative_path" ]] || continue
        run_task_line "verify $root_guidance_relative_path" verify_root_file_sync_match "$root_guidance_relative_path" || failed=1
    done < <(list_root_guidance_relative_paths)

    run_task_line "verify managed skills" verify_synced_skill_and_home_agent_presence || failed=1

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        if ! verify_agent_profile_sync_match "$agent_profile_name"; then
            failed=1
        fi
    done < <(list_repo_agent_profile_names)

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        print_error "Managed installed skill no longer exists in the repo: $skill_name"
        failed=1
    done < <(list_removed_repo_managed_skill_names)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        print_error "Managed installed agent profile no longer exists in the repo: $agent_profile_name"
        failed=1
    done < <(list_removed_repo_managed_agent_profile_names)

    run_task_line "verify managed inventories" verify_managed_inventory_files_match_repo || failed=1
    run_task_line "verify managed routing config" verify_managed_config_routing_present || failed=1
    run_task_line "verify agent config sections" verify_home_agent_config_sections_match_repo || failed=1
    run_task_line "verify memory wiring" verify_memory_status_reporter_home_wiring_present || failed=1
    run_task_line "verify runtime hygiene" verify_repo_managed_installation_hygiene || failed=1

    if [[ $failed -eq 0 ]]; then
        print_success "Fast install/update verification passed"
        return 0
    fi

    print_error "Fast install/update verification failed"
    return 1
}

verify_sync_operation_result() {
    local verification_mode="${CODEX_SYNC_POST_SYNC_VERIFICATION_MODE:-fast}"

    case "$verification_mode" in
        full)
            verify_pack_checksums
            return $?
            ;;
        none)
            print_warning "Skipping post-sync verification because CODEX_SYNC_POST_SYNC_VERIFICATION_MODE=none"
            return 0
            ;;
        fast)
            verify_sync_operation_health
            return $?
            ;;
        *)
            print_error "Unsupported CODEX_SYNC_POST_SYNC_VERIFICATION_MODE value: $verification_mode"
            print_info "Expected fast, full, or none."
            return 1
            ;;
    esac
}

# Function to validate skill file
validate_skill() {
    local file=$1
    local skill_name=$(basename "$(dirname "$file")")

    print_info "Validating $skill_name..."

    # Check if file exists
    if [[ ! -f "$file" ]]; then
        print_error "Skill file not found: $file"
        return 1
    fi

    # Check for YAML frontmatter opening and closing markers.
    if [[ "$(head -n 1 "$file")" != "---" ]]; then
        print_error "Missing opening YAML frontmatter in $file"
        return 1
    fi

    if ! tail -n +2 "$file" | grep -q "^---$"; then
        print_error "Missing closing YAML frontmatter in $file"
        return 1
    fi

    # Check for required fields
    if ! grep -q "^name:" "$file"; then
        print_error "Missing 'name' field in $file"
        return 1
    fi

    if ! grep -q "^description:" "$file"; then
        print_error "Missing 'description' field in $file"
        return 1
    fi

    # Check for shortform variable names in fenced code blocks (warning only).
    # Scanning full Markdown files causes false positives on plain-language words like "data".
    if awk 'BEGIN{in_block=0} substr($0,1,3)=="```"{in_block=!in_block; next} in_block{print}' "$file" | grep -E "\b(usr|btn|tmp|data|res|req|arr|obj|fn|cb|idx|len|str|num)\b([[:space:]]*:[^=]+)?[[:space:]]*=" | grep -v "❌ BAD:" | grep -v "BAD:" | grep -v "REJECT" | grep -v "shortform" | grep -v "metadata:" | grep -v "N+1" > /dev/null 2>&1; then
        print_warning "Possible shortform variable names found in $file (check if they're in examples)"
    fi

    print_success "$skill_name validated"
    return 0
}

file_contains_all_patterns() {
    local file_path=$1
    shift
    local required_pattern

    for required_pattern in "$@"; do
        if ! grep -Eqi -- "$required_pattern" "$file_path"; then
            return 1
        fi
    done

    return 0
}

markdown_section_content() {
    local file_path=$1
    local section_heading=$2

    awk -v heading="$section_heading" '
        function heading_level(line,    level_value) {
            match(line, /^#+/)
            level_value = RLENGTH
            return level_value
        }

        /^#+ / {
            current_heading_title = $0
            sub(/^#+ /, "", current_heading_title)

            if (!in_section && current_heading_title == heading) {
                in_section = 1
                target_level = heading_level($0)
                next
            }

            if (in_section && heading_level($0) <= target_level) {
                exit
            }
        }

        in_section { print }
    ' "$file_path"
}

markdown_section_has_minimum_bullets() {
    local file_path=$1
    local section_heading=$2
    local minimum_bullet_count=$3
    local actual_bullet_count

    actual_bullet_count=$(markdown_section_content "$file_path" "$section_heading" | grep -Ec '^[[:space:]]*[-*][[:space:]]' || true)
    [[ "$actual_bullet_count" -ge "$minimum_bullet_count" ]]
}

markdown_section_contains_all_patterns() {
    local file_path=$1
    local section_heading=$2
    shift 2
    local required_pattern
    local section_content

    section_content="$(markdown_section_content "$file_path" "$section_heading")"
    [[ -n "$section_content" ]] || return 1

    for required_pattern in "$@"; do
        if ! printf '%s\n' "$section_content" | grep -Eqi -- "$required_pattern"; then
            return 1
        fi
    done

    return 0
}

markdown_first_matching_heading() {
    local file_path=$1
    local heading_pattern=$2

    grep -E "^## (${heading_pattern})$" "$file_path" | head -n 1 | sed 's/^## //'
}

skill_has_required_runtime_guidance() {
    local file_path=$1

    file_contains_all_patterns "$file_path" \
        'js_repl' \
        'codex\.tool' \
        'research-cache|research cache|freshness-aware' \
        'keep iterating in the same turn' \
        'terminal state before finalizing|wait[^\n]*required sub-agent' \
        'Do not close a required running sub-agent|forbid closing a running required sub-agent early' \
        'keep at most one live same-role agent' \
        'never spawn a second same-role sub-agent if one already exists' \
        'always reuse it with .*send_input.*resume_agent|always reuse it with `send_input` or `resume_agent`' \
        'resume a closed same-role agent before considering any new spawn' \
        'fork_context' \
        'maintain a lightweight spawned-agent list' \
        'send a robust handoff covering the exact objective'
}

agent_config_has_required_runtime_guidance() {
    local file_path=$1

    file_contains_all_patterns "$file_path" \
        'working brief' \
        'workspace-scoped memory' \
        'freshness-aware research cache' \
        'Research current external information before trusting internal knowledge' \
        'request_user_input' \
        'keep iterating in the same turn' \
        'do not stay solo by default' \
        'one top-level plan item per explicit user task, with a short per-item breakdown' \
        'explicit user requirement' \
        'do not present unresolved work as complete' \
        'status requests are checkpoints, not stop signals' \
        'js_repl' \
        'codex\.tool' \
        'reuse the same-role agent' \
        'keep the handoff bounded' \
        'interrupt=true' \
        'terminal state before finalizing|wait[^\n]*terminal state' \
        'keep doing non-conflicting local work instead of idling'
}

# Validate a Codex skill directory for Codex-specific requirements and separation.
validate_codex_skill_dir() {
    local skill_dir=$1
    local skill_name=$(basename "$skill_dir")
    local agent_config_path
    local home_agent_name
    local output_expectation_count=0
    local clarify_count=0
    local lifecycle_count=0

    if ! validate_skill "$skill_dir/SKILL.md"; then
        return 1
    fi

    # Codex skills should not carry unsupported vendor-specific metadata.
    if grep -q "^allowed-tools:" "$skill_dir/SKILL.md"; then
        print_error "Codex skill contains unsupported vendor-specific 'allowed-tools' field: $skill_name"
        return 1
    fi

    # Codex CLI skill configuration lives in agents/openai.yaml.
    if [[ ! -f "$skill_dir/agents/openai.yaml" ]]; then
        print_error "Missing Codex agents/openai.yaml for skill: $skill_name"
        return 1
    fi

    # Expert-grade skills must ship reference material, not only a top-level summary.
    if [[ ! -d "$skill_dir/references" ]]; then
        print_error "Missing references/ directory for Codex skill: $skill_name"
        return 1
    fi

    if ! grep -q '^## Use This Skill When$' "$skill_dir/SKILL.md"; then
        print_error "Codex skill is missing a Use This Skill When section: $skill_name"
        return 1
    fi

    if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Use This Skill When" 3; then
        print_error "Codex skill is missing concrete trigger boundaries in Use This Skill When: $skill_name"
        return 1
    fi

    local scenario_heading
    scenario_heading="$(markdown_first_matching_heading "$skill_dir/SKILL.md" 'Real-World Scenarios|Real-World Failure Scenarios|Real-World Review Scenarios')"
    if [[ -z "$scenario_heading" ]]; then
        print_error "Codex skill is missing a real-world scenario section: $skill_name"
        return 1
    fi

    if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "$scenario_heading" 2; then
        print_error "Codex skill is missing concrete real-world scenario coverage: $skill_name"
        return 1
    fi

    output_expectation_count=$(grep -c '^## Output Expectations$' "$skill_dir/SKILL.md" || true)
    if [[ "$output_expectation_count" -gt 1 ]]; then
        print_error "Codex skill has duplicate Output Expectations sections: $skill_name"
        return 1
    fi

    clarify_count=$(grep -c '^## When to Clarify First$' "$skill_dir/SKILL.md" || true)
    if [[ "$clarify_count" -gt 1 ]]; then
        print_error "Codex skill has duplicate When to Clarify First sections: $skill_name"
        return 1
    fi

    lifecycle_count=$(grep -c '^## Sub-Agent Lifecycle Rules$' "$skill_dir/SKILL.md" || true)
    if [[ "$lifecycle_count" -gt 1 ]]; then
        print_error "Codex skill has duplicate Sub-Agent Lifecycle Rules sections: $skill_name"
        return 1
    fi

    while IFS= read -r agent_config_path; do
        [[ -n "$agent_config_path" ]] || continue
        home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
        if ! validate_codex_agent_config "$skill_name" "$home_agent_name" "$agent_config_path"; then
            return 1
        fi
    done < <(list_skill_agent_config_files "$skill_name")

    if ! skill_has_required_runtime_guidance "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md is missing required runtime guidance for Codex orchestration and delegation: $skill_name"
        return 1
    fi

    if [[ "$skill_name" != "reviewer" ]] && [[ "$skill_name" != "memory-status-reporter" ]] && grep -q '^## Output Expectations$' "$skill_dir/SKILL.md"; then
        if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Output Expectations" 4; then
            print_error "Codex skill is missing a sufficiently concrete Output Expectations section: $skill_name"
            return 1
        fi
    fi

    # Codex skills must reference Codex-native tools and agent profiles only.
    local invalid_codex_runtime_regex='[`](ask_user|replace|grep_search|read_file|write_file|run_terminal|run_terminal_cmd|generalist)[`]'
    if grep -nE "$invalid_codex_runtime_regex" "$skill_dir/SKILL.md" > /dev/null 2>&1; then
        print_error "Non-Codex tool or agent-profile names found in Codex skill: $skill_name"
        grep -nE "$invalid_codex_runtime_regex" "$skill_dir/SKILL.md" | head -n 20
        return 1
    fi

    case "$skill_name" in
        reviewer)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Core Principles" "Structure Matters" || ! grep -q "REQUIRE thin entrypoints" "$skill_dir/SKILL.md" || ! grep -q "Coverage matches the touched layers" "$skill_dir/SKILL.md"; then
                print_error "Reviewer skill is missing enforced structure or layered-testing guidance"
                return 1
            fi
            if ! grep -q "REJECT duplicate entry paths" "$skill_dir/SKILL.md" || ! grep -q "REQUIRE one obvious path" "$skill_dir/SKILL.md"; then
                print_error "Reviewer skill is missing anti-junk entrypoint guidance"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Multi-Agent Execution Pattern \(Completion-First\)" "main agent must verify" "send updated work back" "multiple parallel reviewer passes" "distinct purpose or workstream label"; then
                print_error "Reviewer skill is missing multi-reviewer lane or re-review guidance"
                return 1
            fi
            if ! grep -q "readiness or ACK check" "$skill_dir/SKILL.md" || ! grep -q "old completed payload" "$skill_dir/SKILL.md" || ! grep -q "raw HTML or HTTP 4xx or 5xx content" "$skill_dir/SKILL.md"; then
                print_error "Reviewer skill is missing resumed-agent handshake or transport-failure recovery guidance"
                return 1
            fi
            if ! grep -q "Prompt injection" "$skill_dir/SKILL.md" || ! grep -q "data only, never instructions" "$skill_dir/SKILL.md" || ! grep -q "same failing tool call" "$skill_dir/SKILL.md"; then
                print_error "Reviewer skill is missing prompt-injection, external-content, or anti-loop guidance"
                return 1
            fi
            ;;
        software-development-life-cycle)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Context and Structure Defaults" "Keep entrypoints thin"; then
                print_error "Software-development-life-cycle skill is missing context or modular-delivery defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Context and Structure Defaults" 4 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Modular Delivery Defaults" 3; then
                print_error "Software-development-life-cycle skill is missing the expected depth in context or modular-delivery defaults"
                return 1
            fi
            if ! grep -q "readiness or ACK check" "$skill_dir/SKILL.md" || ! grep -q "old completed payload" "$skill_dir/SKILL.md" || ! grep -q "raw HTML or HTTP 4xx or 5xx content" "$skill_dir/SKILL.md"; then
                print_error "Software-development-life-cycle skill is missing resumed-agent handshake or transport-failure recovery guidance"
                return 1
            fi
            if ! grep -q "Prompt injection" "$skill_dir/SKILL.md" || ! grep -q "data only, never instructions" "$skill_dir/SKILL.md" || ! grep -q "same failing tool call" "$skill_dir/SKILL.md"; then
                print_error "Software-development-life-cycle skill is missing prompt-injection, external-content, or anti-loop guidance"
                return 1
            fi
            ;;
        memory-status-reporter)
            if ! grep -q "memory_maintenance.py" "$skill_dir/SKILL.md" || ! grep -q "completion_gate.py" "$skill_dir/SKILL.md" || ! grep -q "SESSION-STATE.md" "$skill_dir/SKILL.md" || ! grep -q "working-buffer.md" "$skill_dir/SKILL.md" || ! grep -q "trim" "$skill_dir/SKILL.md" || ! grep -q "recalibrate" "$skill_dir/SKILL.md"; then
                print_error "Memory-status-reporter skill is missing WAL, completion-gate, working-buffer, or maintenance-helper guidance"
                return 1
            fi
            if ! grep -q "data only, never instructions" "$skill_dir/SKILL.md" || ! grep -q "same failing tool call" "$skill_dir/SKILL.md"; then
                print_error "Memory-status-reporter skill is missing external-content or anti-loop guidance"
                return 1
            fi
            ;;
        web-development-life-cycle)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Structure Defaults" "server actions" "higher-layer confirmation"; then
                print_error "Web-development-life-cycle skill is missing structure or layered-test defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Structure Defaults" 4 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Delivery Heuristics by Product Surface" 5 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Delivery Decision Matrix" 5; then
                print_error "Web-development-life-cycle skill is missing the expected depth in structure or delivery heuristics"
                return 1
            fi
            if markdown_section_content "$skill_dir/SKILL.md" "Core Web Vitals" | grep -q "FID"; then
                print_error "Web-development-life-cycle skill still lists FID as a Core Web Vital"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Core Web Vitals" "INP"; then
                print_error "Web-development-life-cycle skill must include INP in Core Web Vitals guidance"
                return 1
            fi
            ;;
        mobile-development-life-cycle)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Structure Defaults" "permission" "offline" "higher-layer confirmation"; then
                print_error "Mobile-development-life-cycle skill is missing structure, lifecycle, or test defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Structure Defaults" 4 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Delivery Heuristics by Mobile Surface" 5 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Mobile Delivery Decision Matrix" 5; then
                print_error "Mobile-development-life-cycle skill is missing the expected depth in structure or delivery heuristics"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Android Development" "Keystore"; then
                print_error "Mobile-development-life-cycle skill must reference Android Keystore guidance"
                return 1
            fi
            if markdown_section_content "$skill_dir/SKILL.md" "Android Development" | grep -q "Keychain"; then
                print_error "Mobile-development-life-cycle skill incorrectly references Keychain in Android guidance"
                return 1
            fi
            ;;
        backend-and-data-architecture)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Structure Defaults" "transport adapters" "services or use cases"; then
                print_error "Backend-and-data-architecture skill is missing structure defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Structure Defaults" 4; then
                print_error "Backend-and-data-architecture skill is missing the expected depth in structure defaults"
                return 1
            fi
            ;;
        qa-and-automation-engineer)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Layered Coverage Defaults" "higher-layer confirmation" "module or layer they protect"; then
                print_error "QA-and-automation-engineer skill is missing layered-coverage defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Layered Coverage Defaults" 4; then
                print_error "QA-and-automation-engineer skill is missing the expected depth in layered-coverage defaults"
                return 1
            fi
            ;;
        ui-design-systems-and-responsive-interfaces)
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Design Intelligence Packet" 5 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Brownfield Redesign Defaults" 4; then
                print_error "UI skill is missing the expected depth in design-intelligence or brownfield defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "UI Copy and Flow Defaults" 6; then
                print_error "UI skill is missing concise-copy and flow defaults"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "UI Copy and Flow Defaults" "helper text only" "filler copy" "obvious next action"; then
                print_error "UI skill is missing concise-copy guardrails"
                return 1
            fi
            if ! grep -q "Storybook, Ladle, or Histoire" "$skill_dir/SKILL.md"; then
                print_error "UI skill is missing component-verification defaults"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "UI and UX Ownership Boundary" "UI owns" "UX owns"; then
                print_error "UI skill is missing bounded UI-vs-UX ownership guidance"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Professional Polish Checks" "No emoji as product UI icons"; then
                print_error "UI skill is missing professional-polish delivery checks"
                return 1
            fi
            if [[ ! -f "$skill_dir/scripts/design_intelligence.py" ]] || [[ ! -f "$skill_dir/data/design_intelligence_catalog.json" ]]; then
                print_error "UI skill is missing the local design-intelligence generator or catalog"
                return 1
            fi
            if [[ ! -f "$skill_dir/references/55-design-intelligence-brownfield-and-component-verification.md" ]] || ! grep -q "55-design-intelligence-brownfield-and-component-verification.md" "$skill_dir/references/00-ui-knowledge-map.md"; then
                print_error "UI skill references are missing the design-intelligence brownfield reference wiring"
                return 1
            fi
            if [[ ! -f "$skill_dir/references/57-codex-design-intelligence-generator.md" ]] || ! grep -q "57-codex-design-intelligence-generator.md" "$skill_dir/references/00-ui-knowledge-map.md"; then
                print_error "UI skill references are missing the Codex design-intelligence generator wiring"
                return 1
            fi
            ;;
        ux-research-and-experience-strategy)
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Experience Brief Defaults" 5 || ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Brownfield Redesign and Artifact Persistence" 4; then
                print_error "UX skill is missing the expected depth in experience-brief or brownfield defaults"
                return 1
            fi
            if ! markdown_section_has_minimum_bullets "$skill_dir/SKILL.md" "Flow-First UX Defaults" 6; then
                print_error "UX skill is missing flow-first delivery defaults"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Flow-First UX Defaults" "supporting sentence under every heading" "helper text only" "filler"; then
                print_error "UX skill is missing concise-writing guardrails"
                return 1
            fi
            if ! grep -q "Storybook, Ladle, Histoire" "$skill_dir/SKILL.md"; then
                print_error "UX skill is missing validation-loop defaults"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "UX and UI Ownership Boundary" "UX owns" "UI owns"; then
                print_error "UX skill is missing bounded UX-vs-UI ownership guidance"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Decision Confidence and Recovery Checks" "Errors preserve progress"; then
                print_error "UX skill is missing decision-confidence or recovery checks"
                return 1
            fi
            if [[ ! -f "$skill_dir/references/55-experience-briefs-brownfield-and-validation-loops.md" ]] || ! grep -q "55-experience-briefs-brownfield-and-validation-loops.md" "$skill_dir/references/00-ux-knowledge-map.md"; then
                print_error "UX skill references are missing the experience-brief brownfield reference wiring"
                return 1
            fi
            ;;
        cloud-and-devops-expert)
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Deployment Stage and Adversarial Readiness" "alpha" "beta" "canary" "release" "blue-green" "load-balancer traffic shifting" "red-team" "blue-team"; then
                print_error "Cloud-and-devops-expert skill is missing staged-rollout or adversarial-readiness doctrine"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Production Gates" "Stage Gate" "Evidence Gate"; then
                print_error "Cloud-and-devops-expert skill is missing rollout stage or evidence gates"
                return 1
            fi
            ;;
        git-expert)
            if markdown_section_content "$skill_dir/SKILL.md" "Essential Git Commands" | grep -Eq 'git rebase -i|git reset --hard|git checkout -- <file>|git filter-branch'; then
                print_error "Git skill keeps high-risk commands inside Essential Git Commands"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "High-Risk Operations \(Explicit User Approval Only\)" "explicit user approval" "git reset --hard" "git rebase -i"; then
                print_error "Git skill is missing explicit high-risk operation gating"
                return 1
            fi
            if ! markdown_section_contains_all_patterns "$skill_dir/SKILL.md" "Issue-Driven Worktree Flow" "git worktree add" "clean" "CI and CD" "sensitive"; then
                print_error "Git skill is missing issue-driven worktree, clean-push, or CI/CD workflow doctrine"
                return 1
            fi
            ;;
    esac

    # Enforce separation: Codex skills should not reference legacy external-vendor docs.
    local banned_regex='docs\.[Aa]nthropic\.com|[Cc][Ll][Aa][Uu][Dd][Ee][[:space:]]+Code|[Aa]nthropic'
    if grep -RInE "$banned_regex" "$skill_dir" --include="*.md" > /dev/null 2>&1; then
        print_error "Legacy external-vendor references found in Codex skill: $skill_name"
        grep -RInE "$banned_regex" "$skill_dir" --include="*.md" | head -n 20
        return 1
    fi

    return 0
}

validate_codex_agent_config() {
    local skill_name=$1
    local home_agent_name=$2
    local config_file=$3
    local expected_reasoning="medium"
    local configured_model=""
    local expected_allow_implicit="true"
    local default_prompt_word_count=0
    local default_prompt_character_count=0
    expected_reasoning="$(expected_reasoning_for_home_agent "$home_agent_name" "$expected_reasoning")"

    if grep -q "^model:" "$config_file"; then
        configured_model=$(awk -F'"' '/^model: / {print $2; exit}' "$config_file")
        print_error "Codex skill config should not pin model in agents/openai.yaml: $home_agent_name ($configured_model)"
        return 1
    fi

    if ! grep -q "^reasoning_effort: \"$expected_reasoning\"$" "$config_file"; then
        print_error "Unexpected reasoning_effort for Codex skill $skill_name (expected $expected_reasoning for $home_agent_name)"
        return 1
    fi

    if ! agent_config_has_required_runtime_guidance "$config_file"; then
        print_error "Codex agent prompt is missing required runtime guidance for research, orchestration, or prompt alignment: $skill_name"
        return 1
    fi

    default_prompt_word_count="$(extract_codex_openai_value "$config_file" "default_prompt" | wc -w | awk '{print $1}')"
    if [[ "$default_prompt_word_count" -gt 260 ]]; then
        print_error "Codex agent prompt is too long and likely duplicates repo policy: $skill_name ($default_prompt_word_count words)"
        return 1
    fi

    default_prompt_character_count="$(extract_codex_openai_value "$config_file" "default_prompt" | wc -c | awk '{print $1}')"
    if [[ "$default_prompt_character_count" -gt 1601 ]]; then
        print_error "Codex agent prompt is too long and likely duplicates repo policy: $skill_name ($default_prompt_character_count characters)"
        return 1
    fi

    case "$skill_name" in
        reviewer|software-development-life-cycle|memory-status-reporter|git-expert)
            expected_allow_implicit="false"
            ;;
    esac

    if ! grep -q "^  allow_implicit_invocation: $expected_allow_implicit$" "$config_file"; then
        print_error "Unexpected allow_implicit_invocation policy for Codex skill: $skill_name"
        return 1
    fi

    if [[ "$home_agent_name" == "reviewer" ]]; then
        if ! grep -q "findings first" "$config_file" || ! grep -q "Do not mutate code by default" "$config_file"; then
            print_error "Reviewer-family prompts must stay review-first and non-mutating by default: $home_agent_name"
            return 1
        fi
        if ! grep -q "named surface" "$config_file" || ! grep -q "validated patch batches" "$config_file" || ! grep -q "workaround-only" "$config_file"; then
            print_error "Reviewer-family prompts must keep named-scope, patch-batch, and root-cause discipline explicit: $home_agent_name"
            return 1
        fi
    fi

    if [[ "$skill_name" == "software-development-life-cycle" ]] && { ! grep -q "named scope" "$config_file" || ! grep -q "patch batch" "$config_file"; }; then
        print_error "SDLC prompt must keep named-scope and patch-batch doctrine explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && ! grep -q "design intelligence packet" "$config_file"; then
        print_error "UI skill prompt must require a design intelligence packet: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && { ! grep -q "UI owns" "$config_file" || ! grep -q "UX owns" "$config_file" || ! grep -q "Storybook, Ladle, or Histoire" "$config_file"; }; then
        print_error "UI skill prompt must keep UI-vs-UX ownership and component-preview validation explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && ! grep -q 'scripts/design_intelligence.py' "$config_file"; then
        print_error "UI skill prompt must point to the local design-intelligence generator: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && { ! grep -q "Benchmark 2-3 mature product-family surfaces" "$config_file" || ! grep -q "brownfield changes targeted" "$config_file"; }; then
        print_error "UI skill prompt must keep benchmarking and targeted brownfield guidance explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && { ! grep -q "hardcoded design values" "$config_file" || ! grep -q "implementation-ready" "$config_file"; }; then
        print_error "UI skill prompt must keep anti-hardcoding and implementation-ready guidance explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ux-research-and-experience-strategy" ]] && ! grep -q "experience brief" "$config_file"; then
        print_error "UX skill prompt must require experience-brief hardening: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ux-research-and-experience-strategy" ]] && { ! grep -q "UX owns" "$config_file" || ! grep -q "UI owns" "$config_file" || ! grep -q "Storybook, Ladle, or Histoire" "$config_file"; }; then
        print_error "UX skill prompt must keep UX-vs-UI ownership and component-preview validation explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ux-research-and-experience-strategy" ]] && { ! grep -q "Benchmark 2-3 mature flows" "$config_file" || ! grep -q "brownfield changes targeted" "$config_file"; }; then
        print_error "UX skill prompt must keep benchmarking and targeted brownfield guidance explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ux-research-and-experience-strategy" ]] && { ! grep -q "completion note" "$config_file" || ! grep -q "live testing" "$config_file"; }; then
        print_error "UX prompt must keep completion-note and live-testing residue guidance explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "memory-status-reporter" ]] && { ! grep -q "tool-use mistakes" "$config_file" || ! grep -q "patterns were rewarded" "$config_file" || ! grep -q "research-cache items look stale" "$config_file" || ! grep -q "act as the memory writer" "$config_file" || ! grep -q "report what changed" "$config_file" || ! grep -q "verify the touched memory files are clean and in sync" "$config_file"; }; then
        print_error "Memory status prompt must mention tool-use mistakes, rewarded patterns, research cache health, and memory-writer reporting: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "git-expert" ]] && { ! grep -q "configured Git author identity" "$config_file" || ! grep -q "git config user.name" "$config_file" || ! grep -q "git config user.email" "$config_file"; }; then
        print_error "Git prompt must preserve configured Git author identity: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "git-expert" ]] && { ! grep -q "issue-driven worktree" "$config_file" || ! grep -q "CI/CD-gated PRs" "$config_file" || ! grep -q "sensitive data leakage" "$config_file"; }; then
        print_error "Git prompt must keep issue-driven worktree and clean-push doctrine explicit: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "cloud-and-devops-expert" ]] && { ! grep -q "alpha, beta, canary, release, or blue-green" "$config_file" || ! grep -q "load-balancer behavior" "$config_file" || ! grep -q "red-team versus blue-team" "$config_file" || ! grep -q "rollback owner" "$config_file" || ! grep -q "abort signal" "$config_file"; }; then
        print_error "Cloud prompt must keep staged rollout and adversarial-readiness doctrine explicit: $skill_name"
        return 1
    fi

    return 0
}
# Validate repo-level Codex guidance that is synced or used alongside root skills.
validate_codex_guidance_file() {
    local file=$1

    if [[ ! -f "$file" ]]; then
        print_error "Missing Codex guidance file: $file"
        return 1
    fi

    local invalid_codex_runtime_regex='[`](ask_user|replace|grep_search|read_file|write_file|run_terminal|run_terminal_cmd|generalist)[`]'
    if grep -nE "$invalid_codex_runtime_regex" "$file" > /dev/null 2>&1; then
        print_error "Non-Codex tool or agent-profile names found in Codex guidance: $file"
        grep -nE "$invalid_codex_runtime_regex" "$file" | head -n 20
        return 1
    fi

    if [[ "$(basename "$file")" == "AGENTS.md" ]]; then
        if ! grep -qi "do not silently ignore, abandon, or interrupt a required sub-agent" "$file"; then
            print_error "Missing required sub-agent completion policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "local evidence looks" "$file"; then
            print_error "Missing anti-rush sub-agent policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Never close a required sub-agent while its status is still running or queued" "$file"; then
            print_error "Missing no-close-while-running policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Route directly to the primary domain skill" "$file"; then
            print_error "Missing direct-to-domain default routing policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi 'Start with `reviewer` only for audits' "$file"; then
            print_error "Missing narrowed reviewer-first default policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Treat internal knowledge as a starting hypothesis, not proof" "$file"; then
            print_error "Missing current-research-first policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "do not accept generic answers" "$file"; then
            print_error "Missing anti-generic research policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Layered Memory" "$file"; then
            print_error "Missing layered-memory policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Scope-First Memory Rule" "$file" || ! grep -qi "~/.codex/memories/workspaces/<workspace-slug>/" "$file" || ! grep -qi "workstreams/<workstream-key>" "$file" || ! grep -qi "instances/<agent-instance>" "$file" || ! grep -qi "~/.codex/memories/agents/<role>/<workspace-slug>/" "$file"; then
            print_error "Missing scoped-memory lookup policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Reinforcement Memory (Reward/Penalty Loop)" "$file" || ! grep -qi "Research Cache Requirement" "$file" || ! grep -qi "Freshness Rule" "$file"; then
            print_error "Missing reinforcement-memory, research-cache, or freshness policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Stale Memory Handling" "$file"; then
            print_error "Missing stale-memory handling policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "skip redundant live research" "$file" || ! grep -qi "missing, uncertain, stale, or explicitly time-sensitive parts" "$file"; then
            print_error "Missing cache-first research-reuse gate in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Do not stop at the first bug uncovered by validation" "$file"; then
            print_error "Missing validation autonomy rule in AGENTS.md"
            return 1
        fi

        if ! grep -qi "maintain a lightweight per-project spawned-agent list" "$file"; then
            print_error "Missing spawned-agent registry policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "interrupt=true" "$file"; then
            print_error "Missing no-interrupt-rush policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "never spawn a second same-role sub-agent if one already exists" "$file" || ! grep -qi 'always reuse it with `send_input` or `resume_agent`' "$file" || ! grep -qi "resume the closed same-role agent before considering any new spawn" "$file"; then
            print_error "Missing strict same-role reuse policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "robust handoff packet" "$file"; then
            print_error "Missing robust sub-agent handoff policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "working brief" "$file" || ! grep -qi "Tool Mistakes Count" "$file" || ! grep -qi "Prefer test-first when practical" "$file" || ! grep -qi "Context Retrieval Ladder" "$file" || ! grep -qi "Learning Snapshot" "$file" || ! grep -qi "Prefer modular structure" "$file" || ! grep -qi "Keep route handlers, controllers, pages, CLI entrypoints, and main scripts short" "$file"; then
            print_error "Missing prompt-alignment, context-efficiency, modularity, thin-entrypoint, tool-mistake, or learning-snapshot policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Named Scope First" "$file" || ! grep -qi "small, batch-sized patches" "$file" || ! grep -qi "fake completion or workaround-only delivery" "$file" || ! grep -qi "Avoid first-person and second-person pronouns" "$file"; then
            print_error "Missing named-scope, small-batch, real-fix, or professional-language policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "Extend an existing entrypoint, installer, updater, or wrapper before adding a new one" "$file" || ! grep -qi "Keep one obvious install or update path per platform" "$file"; then
            print_error "Missing anti-junk entrypoint and duplicate-wrapper policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "parallel reviewer validation" "$file" || ! grep -qi "spawn multiple" "$file" || ! grep -qi "reviewer output before acting" "$file"; then
            print_error "Missing multi-reviewer lane policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "readiness or ACK check" "$file" || ! grep -qi "old completed payload" "$file" || ! grep -qi "raw HTML or HTTP 4xx or 5xx content" "$file"; then
            print_error "Missing resumed-agent handshake or transport-failure recovery policy in AGENTS.md"
            return 1
        fi

       if ! grep -qi "Do not pin a specific model inside ordinary root Codex" "$file" || ! grep -qi "local-home-agent-overrides.json" "$file" || ! grep -qi "gpt-5.4" "$file" || ! grep -qi 'reasoning_effort: "low"' "$file" || ! grep -qi "cannot be model-pinned from repo policy alone unless the runtime exposes model selection directly" "$file"; then
           print_error "Missing model-split, local-override, or runtime model-selection boundary policy in AGENTS.md"
           return 1
       fi

        if ! grep -qi "~/.codex/agent-profiles/\*\.toml" "$file" || ! grep -qi "12 skill-owned agent profiles" "$file"; then
            print_error "Missing skill-agent-profile sync policy in AGENTS.md"
            return 1
        fi

        if ! grep -qi "every explicit user requirement" "$file" || ! grep -qi "Do not present unresolved work as complete" "$file" || ! grep -qi "does not suspend execution when fixable in-scope work remains" "$file" || ! grep -qi "do not stay solo by default" "$file" || ! grep -qi "one top-level plan item per explicit user task" "$file" || ! grep -qi "per-item breakdown" "$file"; then
            print_error "Missing completion reconciliation or no-soft-stop enforcement in AGENTS.md"
            return 1
        fi
        if ! grep -qi "Never hardcode runtime values" "$file" || ! grep -qi "Hold the final output until the closing check is explicit" "$file" || ! grep -qi "staged rollout doctrine" "$file" || ! grep -qi "generic-looking UI repair" "$file" || ! grep -qi "journey friction" "$file"; then
            print_error "Missing hardcoding, final-hold, cloud rollout, or UI/UX routing doctrine in AGENTS.md"
            return 1
        fi
        if ! grep -qi "WAL Protocol" "$file" || ! grep -qi "SESSION-STATE.md" "$file" || ! grep -qi "working-buffer.md" "$file" || ! grep -qi "Trim Protocol" "$file" || ! grep -qi "recalibrate" "$file" || ! grep -qi "Prompt Injection Defense" "$file" || ! grep -qi "External Content Security" "$file" || ! grep -qi "Cross-Platform Script Portability" "$file" || ! grep -qi "Parallel Main-Agent Throughput" "$file"; then
            print_error "Missing WAL, memory-maintenance, security-boundary, or cross-platform policy in AGENTS.md"
            return 1
        fi
    fi

    if [[ "$(basename "$file")" == "README.md" ]]; then
        if ! grep -qi "Research cache" "$file" || ! grep -qi "Reinforcement memory" "$file" || ! grep -qi "rewarded patterns" "$file" || ! grep -qi "github-update" "$file" || ! grep -qi "skip redundant live research" "$file"; then
            print_error "Missing research-cache, GitHub update, or reinforcement-memory workflow in README.md"
            return 1
        fi
        if ! grep -qi "resolve_memory_scope.py" "$file" || ! grep -qi "research_cache.py" "$file" || ! grep -qi "workspace memory" "$file" || ! grep -qi "workstreams/<workstream-key>" "$file" || ! grep -qi "instances/<agent-instance>" "$file" || ! grep -qi "archive-stale" "$file"; then
            print_error "Missing scoped-memory or research-cache helper workflow in README.md"
            return 1
        fi
       if ! grep -qi "sync-skills.ps1" "$file" || ! grep -qi "delegates to `sync-skills.sh`" "$file" || ! grep -qi "Git Bash on Windows" "$file" || ! grep -qi "runtime-guardrails-and-memory-protocols.md" "$file" || ! grep -qi "do not stay solo by default" "$file" || ! grep -qi "top-level plan item per explicit user task" "$file" || ! grep -qi "local-home-agent-overrides.json" "$file" || ! grep -qi "memory writer" "$file"; then
           print_error "Missing Windows wrapper, runtime-guardrails, local-override, or memory-writer documentation in README.md"
           return 1
       fi
        if ! grep -qi "agent-profiles/\*\.toml" "$file" || ! grep -qi "skill agent profiles: 12/12" "$file"; then
            print_error "Missing skill-agent-profile mirror documentation in README.md"
            return 1
        fi
        if ! grep -qi "Pair UI Output With UX Evidence" "$file" || ! grep -qi "issue-driven worktree" "$file" || ! grep -qi "Hold the answer until closure is proven" "$file"; then
            print_error "Missing README parity for UI/UX, Git workflow, or completion proof doctrine"
            return 1
        fi
        if ! grep -qi "Honor the named scope" "$file" || ! grep -qi "Small validated batches" "$file" || ! grep -qi "handoff packets small, scope-true, and validation-aware" "$file"; then
            print_error "Missing named-scope, small-batch, or handoff-packet discipline in README.md"
            return 1
        fi
   fi

    if [[ "$(basename "$file")" == "00-skill-routing-and-escalation.md" ]]; then
        if ! grep -qi "Reuse Fresh Research First" "$file" || ! grep -qi "Fix The Next Bug Too" "$file" || ! grep -qi "Requirement Reconciliation Before Close" "$file" || ! grep -qi "Status Requests Do Not End The Job" "$file" || ! grep -qi "Write Corrections Before Responding" "$file" || ! grep -qi "Resolve workspace-scoped memory first" "$file" || ! grep -qi "agent-instance lane" "$file" || ! grep -qi "Use Solo Mode Deliberately" "$file" || ! grep -qi "Planning Defaults" "$file" || ! grep -qi "memory-status-reporter" "$file" || ! grep -qi "report what changed" "$file"; then
            print_error "Missing cache-first, no-soft-stop, WAL, autonomy, or delegated-memory routing defaults in 00-skill-routing-and-escalation.md"
            return 1
        fi
        if ! grep -qi "Honor The Named Scope First" "$file" || ! grep -qi "Small Validated Batches Beat Huge Rewrites" "$file" || ! grep -qi "Real Solutions Over Plausible Workarounds" "$file" || ! grep -qi "Anchor handoffs to the user story and named scope" "$file"; then
            print_error "Missing named-scope, small-batch, real-solution, or handoff-anchor policy in 00-skill-routing-and-escalation.md"
            return 1
        fi
    fi

    if [[ "$(basename "$file")" == "VALIDATION_REPORT.md" ]]; then
        if ! grep -qi "github-update" "$file" || ! grep -qi "cache-first research gate" "$file" || ! grep -qi "keep-iterating completion rule" "$file"; then
            print_error "Missing GitHub update, cache-first, or autonomy hardening evidence in VALIDATION_REPORT.md"
            return 1
        fi
    fi

    return 0
}

count_codex_skill_dirs() {
    local codex_skill_count=0

    for skill_dir in "$CODEX_SOURCE"/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            ((codex_skill_count+=1))
        fi
    done

    echo "$codex_skill_count"
}

validate_codex_repo_docs() {
    local failed=0
    local guidance_files=(
        "$CODEX_SOURCE/AGENTS.md"
        "$CODEX_SOURCE/00-skill-routing-and-escalation.md"
        "$CODEX_SOURCE/README.md"
        "$CODEX_SOURCE/VALIDATION_REPORT.md"
    )
    local codex_skill_count
    codex_skill_count=$(count_codex_skill_dirs)
    local expected_inventory_line
    printf -v expected_inventory_line 'Codex inventory: accurate and complete at `%s` skills' "$codex_skill_count"

    print_info "Validating Codex guidance files..."

    for guidance_file in "${guidance_files[@]}"; do
        if ! validate_codex_guidance_file "$guidance_file"; then
            ((failed+=1))
        fi
    done

    if [[ -d "$CODEX_SOURCE/claude" ]]; then
        print_error "Legacy vendor mirror directory must be removed; this repo is Codex-only now"
        ((failed+=1))
    fi

    if ! grep -q "### Codex CLI Skills ($codex_skill_count Total)" "$CODEX_SOURCE/README.md"; then
        print_error "README.md Codex skill count is out of sync with the repo inventory"
        ((failed+=1))
    fi

    if ! grep -q "Located in root directories ($codex_skill_count skill directories total)" "$CODEX_SOURCE/README.md"; then
        print_error "README.md root skill directory count is out of sync with the repo inventory"
        ((failed+=1))
    fi

    if ! grep -q "## Setup" "$CODEX_SOURCE/README.md" || ! grep -q "## Context Efficiency Playbook" "$CODEX_SOURCE/README.md" || ! grep -q "## Memory Growth Reporting" "$CODEX_SOURCE/README.md"; then
        print_error "README.md is missing setup, context-efficiency, or memory-reporting sections"
        ((failed+=1))
    fi

    if ! grep -q "## Codex CLI Skills ($codex_skill_count Total)" "$CODEX_SOURCE/00-skill-routing-and-escalation.md"; then
        print_error "00-skill-routing-and-escalation.md Codex skill count is out of sync with the repo inventory"
        ((failed+=1))
    fi

    if ! grep -q "only one skill owns the final synthesis" "$CODEX_SOURCE/00-skill-routing-and-escalation.md" || ! grep -q "let \*\*ux-research-and-experience-strategy\*\* manage the work" "$CODEX_SOURCE/00-skill-routing-and-escalation.md" || ! grep -q "let \*\*ui-design-systems-and-responsive-interfaces\*\* manage the work" "$CODEX_SOURCE/00-skill-routing-and-escalation.md"; then
        print_error "00-skill-routing-and-escalation.md is missing explicit UI-versus-UX ownership routing"
        ((failed+=1))
    fi

    if ! grep -q "### Root Codex Skills ($codex_skill_count)" "$CODEX_SOURCE/VALIDATION_REPORT.md"; then
        print_error "VALIDATION_REPORT.md Codex skill count is out of sync with the repo inventory"
        ((failed+=1))
    fi

    if ! grep -qF "$expected_inventory_line" "$CODEX_SOURCE/VALIDATION_REPORT.md"; then
        print_error "VALIDATION_REPORT.md final Codex inventory count is out of sync with the repo inventory"
        ((failed+=1))
    fi

    if rg -n "[Cc][Ll][Aa][Uu][Dd][Ee]|[Cc][Ll][Aa][Uu][Dd][Ee]/|[Aa]nthropic" "$CODEX_SOURCE/README.md" "$CODEX_SOURCE/00-skill-routing-and-escalation.md" "$CODEX_SOURCE/VALIDATION_REPORT.md" > /dev/null 2>&1; then
        print_error "Top-level Codex guidance still contains legacy external-vendor references"
        ((failed+=1))
    fi

    if [[ $failed -ne 0 ]]; then
        print_error "$failed Codex guidance file(s) failed validation"
        return 1
    fi

    print_success "Codex guidance files validated"
    return 0
}

run_repo_contract_tests() {
    ensure_python_launcher || return 1
    local requested_contract_test_workers="${CODEX_CONTRACT_TEST_WORKERS:-}"

    run_python -m py_compile \
        "$CODEX_SOURCE/memory-status-reporter/scripts/memory_store.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/resolve_memory_scope.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/memory_maintenance.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/memory_status_report.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/research_cache.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/completion_gate.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/agent_registry.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/agent_packets.py" \
        "$CODEX_SOURCE/memory-status-reporter/scripts/loop_guard.py" \
        "$CODEX_SOURCE/tests/parallel_contract_test_runner.py" \
        "$CODEX_SOURCE/ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py" \
        "$CODEX_SOURCE/tests/test_skill_pack_contracts.py" || return 1

    if [[ -n "$requested_contract_test_workers" ]]; then
        run_python "$CODEX_SOURCE/tests/parallel_contract_test_runner.py" --workers "$requested_contract_test_workers"
        return $?
    fi

    run_python "$CODEX_SOURCE/tests/parallel_contract_test_runner.py"
}

validate_should_skip_contract_tests() {
    [[ "${CODEX_SKIP_VALIDATE_CONTRACT_TESTS:-0}" == "1" ]] && [[ "${CODEX_SKIP_VALIDATE_SMOKE:-0}" == "1" ]]
}

extract_codex_openai_value() {
    local openai_yaml_path=$1
    local field_name=$2

    run_python - "$openai_yaml_path" "$field_name" <<'PY'
from pathlib import Path
import json
import re
import sys

openai_yaml_path = Path(sys.argv[1])
field_name = sys.argv[2]
openai_yaml_text = openai_yaml_path.read_text(encoding="utf-8")

field_patterns = {
    "model": r'^model:\s*(".*")\s*$',
    "reasoning_effort": r'^reasoning_effort:\s*(".*")\s*$',
    "short_description": r'^\s+short_description:\s*(".*")\s*$',
    "default_prompt": r'^\s+default_prompt:\s*(".*")\s*$',
}

field_pattern = field_patterns.get(field_name)
if field_pattern is None:
    raise SystemExit(f"Unsupported field: {field_name}")

field_match = re.search(field_pattern, openai_yaml_text, flags=re.MULTILINE)
if field_match is None:
    raise SystemExit(f"Missing {field_name} in {openai_yaml_path}")

print(json.loads(field_match.group(1)))
PY
}

extract_codex_openai_optional_value() {
    local openai_yaml_path=$1
    local field_name=$2

    extract_codex_openai_value "$openai_yaml_path" "$field_name" 2>/dev/null || true
}

write_codex_agent_toml() {
    local openai_yaml_path=$1
    local target_toml_path=$2
    local home_agent_name=$3
    local sync_mode=$4
    local override_file

    if [[ ! -f "$openai_yaml_path" ]]; then
        print_warning "Skipping $sync_mode sync for $home_agent_name because $openai_yaml_path is missing"
        return 0
    fi

    override_file="$(skill_manager_local_home_agent_override_file)"

    run_python - "$openai_yaml_path" "$target_toml_path" "$home_agent_name" "$sync_mode" "$override_file" <<'PY'
from pathlib import Path
import json
import re
import sys

openai_yaml_path = Path(sys.argv[1])
target_toml_path = Path(sys.argv[2])
home_agent_name = sys.argv[3]
sync_mode = sys.argv[4]
override_file = Path(sys.argv[5])

openai_yaml_text = openai_yaml_path.read_text(encoding="utf-8")
field_patterns = {
    "model": r'^model:\s*(".*")\s*$',
    "reasoning_effort": r'^reasoning_effort:\s*(".*")\s*$',
    "default_prompt": r'^\s+default_prompt:\s*(".*")\s*$',
}

def extract_field(field_name: str, required: bool) -> str:
    field_pattern = field_patterns[field_name]
    field_match = re.search(field_pattern, openai_yaml_text, flags=re.MULTILINE)
    if field_match is None:
        if required:
            raise SystemExit(f"Missing {field_name} in {openai_yaml_path}")
        return ""
    return json.loads(field_match.group(1))

default_prompt = extract_field("default_prompt", required=True)
pinned_model = extract_field("model", required=False)
configured_reasoning = extract_field("reasoning_effort", required=False)
default_managed_model = "gpt-5.4"
default_managed_reasoning = "medium"
shared_execution_lines = [
    "Do not call tools directly in this runtime; route all tool work through js_repl with codex.tool(...).",
    "Before fresh live research on a reusable question, run research_cache.py lookup or an equivalent shared cache check and only browse live for missing, stale, uncertain, or time-sensitive gaps.",
    "If the request names a function, module, route, or script, keep the first implementation pass anchored to that named scope and widen only when traced impact proves it is required.",
    "Prefer small, reviewable patch batches, then re-read the touched code and rerun the narrowest proving validation before adding the next batch.",
    "Do not stop at a workaround that merely appears to pass; confirm the root cause, implement the real fix, and avoid backward compatibility unless it was explicitly requested.",
    "Keep committed comments and documentation professional, concise, and neutral; avoid first-person and second-person pronouns unless quoting user-provided or source material.",
    "For non-trivial tasks, keep the scoped completion ledger current and rerun completion_gate.py check before the final answer.",
    "If a required sub-agent is still running after wait times out, continue non-conflicting local work and wait again until terminal state before finalizing.",
]

if override_file.exists():
    try:
        payload = json.loads(override_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid local home-agent override file {override_file}: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit(f"Local home-agent override file must contain a JSON object: {override_file}")
else:
    payload = {}

if home_agent_name == "memory-status-reporter":
    agent_payload = payload.get(home_agent_name, {})
else:
    agent_payload = {}
if agent_payload is None:
    agent_payload = {}
if not isinstance(agent_payload, dict):
    raise SystemExit(
        f"Local home-agent override entry for {home_agent_name} must be a JSON object: {override_file}"
    )

local_override_model = agent_payload.get("model", "")
local_override_reasoning = agent_payload.get("reasoning_effort", "")
for field_name, value in {
    "model": local_override_model,
    "reasoning_effort": local_override_reasoning,
}.items():
    if value is None:
        value = ""
    if value != "" and not isinstance(value, str):
        raise SystemExit(
            f"Local home-agent override field {field_name!r} for {home_agent_name} must be a string"
        )
    if field_name == "model":
        local_override_model = value
    else:
        local_override_reasoning = value

if local_override_model:
    effective_model = local_override_model
elif pinned_model:
    effective_model = pinned_model
else:
    effective_model = default_managed_model

if local_override_reasoning:
    effective_reasoning = local_override_reasoning
elif configured_reasoning:
    effective_reasoning = configured_reasoning
else:
    effective_reasoning = default_managed_reasoning

if "'''" in default_prompt:
    raise SystemExit("Triple single quotes are not supported inside developer_instructions")

missing_execution_lines = [line for line in shared_execution_lines if line not in default_prompt]
if missing_execution_lines:
    execution_policy_block = "\n\nExecution policy:\n" + "\n".join(
        f"- {line}" for line in missing_execution_lines
    )
    default_prompt = default_prompt.rstrip() + execution_policy_block

target_toml_path.parent.mkdir(parents=True, exist_ok=True)
output_lines = []
if effective_model:
    output_lines.append(f'model = "{effective_model}"')
if effective_reasoning:
    output_lines.append(f'model_reasoning_effort = "{effective_reasoning}"')
output_lines.append("developer_instructions = '''")
output_lines.append(default_prompt)
output_lines.append("'''")
target_toml_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
PY
}

sync_codex_home_agent_from_yaml() {
    local skill_name=$1
    local openai_yaml_path=$2
    local home_agent_name=$3
    local home_agent_file="$CODEX_TARGET/agents/$home_agent_name.toml"

    write_codex_agent_toml "$openai_yaml_path" "$home_agent_file" "$home_agent_name" "home-agent" || return 1
    sync_codex_home_agent_config_section_from_yaml "$openai_yaml_path" "$home_agent_name" || return 1
    print_success "Synced $home_agent_name home agent config to Codex"
    return 0
}

sync_codex_agent_profile_from_yaml() {
    local skill_name=$1
    local openai_yaml_path=$2
    local home_agent_name=$3
    local agent_profile_file="$CODEX_TARGET/agent-profiles/$home_agent_name.toml"

    write_codex_agent_toml "$openai_yaml_path" "$agent_profile_file" "$home_agent_name" "agent-profile"
    print_success "Synced $home_agent_name agent profile to Codex"
    return 0
}

sync_codex_home_agent_config_section_from_yaml() {
    local openai_yaml_path=$1
    local home_agent_name=$2
    local home_config_file="$CODEX_TARGET/config.toml"
    local short_description

    if [[ ! -f "$openai_yaml_path" ]]; then
        print_warning "Skipping home config section sync for $home_agent_name because $openai_yaml_path is missing"
        return 0
    fi

    short_description=$(extract_codex_openai_value "$openai_yaml_path" "short_description") || {
        print_error "Unable to extract short_description for $home_agent_name"
        return 1
    }

    run_python - "$home_config_file" "$home_agent_name" "$short_description" <<'PY'
from pathlib import Path
import json
import re
import sys

home_config_file = Path(sys.argv[1])
home_agent_name = sys.argv[2]
short_description = sys.argv[3]
config_file_relative_path = f"agents/{home_agent_name}.toml"
config_text = home_config_file.read_text(encoding="utf-8") if home_config_file.exists() else ""

agent_section = (
    f"[agents.{home_agent_name}]\n"
    f"description = {json.dumps(short_description)}\n"
    f"config_file = {json.dumps(config_file_relative_path)}\n"
)

section_pattern = re.compile(rf"(?ms)^\[agents\.{re.escape(home_agent_name)}\]\n.*?(?=^\[|\Z)")
if section_pattern.search(config_text):
    config_text = section_pattern.sub(agent_section + "\n", config_text, count=1)
else:
    if config_text and not config_text.endswith("\n"):
        config_text += "\n"
    if config_text.strip():
        config_text += "\n"
    config_text += agent_section

home_config_file.write_text(config_text, encoding="utf-8")
PY

    print_success "Synced [agents.$home_agent_name] config section to Codex"
    return 0
}

sync_managed_config_routing_instructions() {
    local home_config_file="$CODEX_TARGET/config.toml"
    local required_routing_lines_file

    required_routing_lines_file="$(mktemp)"
    printf '%s\n' "${MANAGED_ROUTING_REQUIRED_CONFIG_LINES[@]}" > "$required_routing_lines_file"

    run_python - "$home_config_file" "$required_routing_lines_file" <<'PY'
from pathlib import Path
import re
import sys

home_config_file = Path(sys.argv[1])
routing_lines = [
    line
    for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    if line.strip()
]
block_header = "Managed skill-pack routing:"
block_footer = "Managed skill-pack routing end."
managed_block = "\n".join([block_header, *routing_lines, block_footer])
config_text = home_config_file.read_text(encoding="utf-8") if home_config_file.exists() else ""

if "developer_instructions = '''" not in config_text:
    config_text = "developer_instructions = '''\n'''\n\n" + config_text.lstrip()

developer_instructions_close = "\n'''"
execution_policy_anchor = "Execution policy:"
block_pattern = re.compile(
    rf"{re.escape(block_header)}\n.*?\n{re.escape(block_footer)}\n?",
    flags=re.DOTALL,
)

if block_pattern.search(config_text):
    config_text = block_pattern.sub(managed_block + "\n", config_text, count=1)
elif execution_policy_anchor in config_text:
    config_text = config_text.replace(
        execution_policy_anchor,
        managed_block + "\n\n" + execution_policy_anchor,
        1,
    )
elif developer_instructions_close in config_text:
    config_text = config_text.replace(
        developer_instructions_close,
        "\n" + managed_block + developer_instructions_close,
        1,
    )
else:
    config_text = config_text.rstrip() + "\n" + managed_block + "\n"

home_config_file.write_text(config_text, encoding="utf-8")
PY

    rm -f "$required_routing_lines_file"

    print_success "Synced managed routing into Codex config.toml developer_instructions"
    return 0
}

sync_codex_home_agents_for_skill() {
    local skill_name=$1
    local agent_config_path
    local home_agent_name

    remove_stale_home_agents_for_skill "$skill_name"

    while IFS= read -r agent_config_path; do
        [[ -n "$agent_config_path" ]] || continue
        home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
        if ! sync_codex_home_agent_from_yaml "$skill_name" "$agent_config_path" "$home_agent_name"; then
            print_error "Failed to sync $home_agent_name home agent config"
            return 1
        fi
    done < <(list_skill_agent_config_files "$skill_name")

    return 0
}

sync_skill_agent_profiles_to_codex() {
    local skill_name
    local agent_config_path
    local home_agent_name
    local legacy_agent_profile_name

    mkdir -p "$CODEX_TARGET/agent-profiles"

    for legacy_agent_profile_name in default explorer worker architect awaiter; do
        rm -f "$CODEX_TARGET/agent-profiles/$legacy_agent_profile_name.toml"
    done

    while IFS= read -r home_agent_name; do
        [[ -n "$home_agent_name" ]] || continue
        if ! grep -qxF -- "$home_agent_name" < <(list_repo_agent_profile_names); then
            rm -f "$CODEX_TARGET/agent-profiles/$home_agent_name.toml"
            remove_agent_profile_from_managed_inventory "$home_agent_name"
        fi
    done < <(list_tracked_managed_agent_profile_names)

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        while IFS= read -r agent_config_path; do
            [[ -n "$agent_config_path" ]] || continue
            home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
            if ! sync_codex_agent_profile_from_yaml "$skill_name" "$agent_config_path" "$home_agent_name"; then
                print_error "Failed to sync $home_agent_name agent profile"
                return 1
            fi
        done < <(list_skill_agent_config_files "$skill_name")
    done < <(list_repo_skill_names)

    write_managed_agent_profile_inventory_from_repo
    return 0
}

sync_memory_status_reporter_home_wiring() {
    local skill_name="memory-status-reporter"
    local openai_yaml_path="$CODEX_SOURCE/$skill_name/agents/openai.yaml"
    local home_config_file="$CODEX_TARGET/config.toml"
    local routing_line="${MEMORY_STATUS_REQUIRED_CONFIG_LINES[0]}"
    local required_execution_lines_file

    if [[ ! -f "$openai_yaml_path" ]]; then
        print_warning "Skipping live home wiring for $skill_name because $openai_yaml_path is missing"
        return 0
    fi

    if ! sync_managed_config_routing_instructions; then
        print_error "Failed to sync managed routing into Codex config.toml"
        return 1
    fi

    required_execution_lines_file="$(mktemp)"
    printf '%s\n' "${MEMORY_STATUS_REQUIRED_CONFIG_LINES[@]:1}" > "$required_execution_lines_file"

    run_python - "$home_config_file" "$routing_line" "$required_execution_lines_file" <<'PY'
from pathlib import Path
import re
import sys

home_config_file = Path(sys.argv[1])
routing_line = sys.argv[2]
required_execution_lines = [
    line
    for line in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines()
    if line.strip()
]
config_text = home_config_file.read_text(encoding="utf-8") if home_config_file.exists() else ""

if "developer_instructions = '''" not in config_text:
    config_text = "developer_instructions = '''\n'''\n\n" + config_text.lstrip()

if routing_line not in config_text:
    developer_instructions_close = "\n'''"
    git_anchor = "- Route to git-expert for repository-state, branching, and recovery work."
    execution_policy_anchor = "Execution policy:"

    if git_anchor in config_text:
        config_text = config_text.replace(git_anchor, f"{git_anchor}\n{routing_line}", 1)
    elif execution_policy_anchor in config_text:
        config_text = config_text.replace(execution_policy_anchor, f"{routing_line}\n\n{execution_policy_anchor}", 1)
    elif developer_instructions_close in config_text:
        config_text = config_text.replace(developer_instructions_close, f"\n{routing_line}{developer_instructions_close}", 1)
    else:
        config_text = config_text.rstrip() + "\n" + routing_line + "\n"

execution_policy_anchor = "Execution policy:"
if execution_policy_anchor in config_text:
    for required_line in required_execution_lines:
        if required_line not in config_text:
            config_text = config_text.replace(execution_policy_anchor, f"{execution_policy_anchor}\n{required_line}", 1)
else:
    missing_execution_lines = [
        required_line
        for required_line in required_execution_lines
        if required_line not in config_text
    ]
    if missing_execution_lines:
        developer_instructions_close = "\n'''"
        execution_policy_block = "\n\nExecution policy:\n" + "\n".join(missing_execution_lines)
        if developer_instructions_close in config_text:
            config_text = config_text.replace(developer_instructions_close, execution_policy_block + developer_instructions_close, 1)
        else:
            config_text = config_text.rstrip() + execution_policy_block + "\n"

home_config_file.write_text(config_text, encoding="utf-8")
PY

    rm -f "$required_execution_lines_file"
    sync_codex_home_agent_config_section_from_yaml "$openai_yaml_path" "$skill_name" || return 1

    print_success "Synced $skill_name global routing into Codex config.toml"
    return 0
}

ensure_memory_hygiene_layout() {
    mkdir -p \
        "$CODEX_TARGET/memories/workspaces" \
        "$CODEX_TARGET/memories/agents" \
        "$CODEX_TARGET/memories/research_cache" \
        "$CODEX_TARGET/memories/archive" \
        "$CODEX_TARGET/memories/reports"
}

sync_root_guidance_files() {
    local relative_path
    local source_path
    local target_path

    while IFS= read -r relative_path; do
        [[ -n "$relative_path" ]] || continue
        source_path="$CODEX_SOURCE/$relative_path"
        target_path="$CODEX_TARGET/$relative_path"

        if [[ -f "$source_path" ]]; then
            mkdir -p "$(dirname "$target_path")"
            cp "$source_path" "$target_path"
            print_success "Synced $relative_path to Codex"
        else
            print_warning "$relative_path not found in source"
        fi
    done < <(list_root_guidance_relative_paths)
}

list_root_guidance_relative_paths() {
    cat <<'EOF'
AGENTS.md
00-skill-routing-and-escalation.md
docs/runtime-guardrails-and-memory-protocols.md
docs/open-source-memory-patterns.md
docs/security-audit-status.md
EOF
}

sync_skill_to_codex() {
    local skill_name=$1
    local source_skill_directory="$CODEX_SOURCE/$skill_name"
    local target_skill_directory="$CODEX_TARGET/skills/$skill_name"

    print_info "Syncing $skill_name..."

    if [[ "${CODEX_SYNC_PREREQUISITES_VALIDATED:-false}" != "true" ]]; then
        if ! validate_codex_skill_dir "$source_skill_directory"; then
            print_error "Validation failed for $skill_name, aborting Codex sync to prevent stale home state"
            return 1
        fi
    fi

    if [[ -d "$CODEX_TARGET/$skill_name" ]]; then
        print_warning "Removing legacy Codex skill directory: $CODEX_TARGET/$skill_name"
        rm -rf "$CODEX_TARGET/$skill_name"
    fi

    if [[ -d "$target_skill_directory" ]]; then
        rm -rf "$target_skill_directory"
    fi

    mkdir -p "$target_skill_directory"
    copy_managed_skill_content "$source_skill_directory" "$target_skill_directory"

    if ! sync_codex_home_agents_for_skill "$skill_name"; then
        print_error "Failed to sync $skill_name home agents"
        return 1
    fi

    print_success "Synced $skill_name to Codex"
    return 0
}

# Function to sync Codex skills
sync_codex() {
    local skill_name

    if ! ensure_sync_runtime_prerequisites; then
        print_error "Runtime prerequisites failed, aborting Codex sync"
        return 1
    fi

    mkdir -p "$CODEX_TARGET"
    mkdir -p "$CODEX_TARGET/skills"
    mkdir -p "$CODEX_TARGET/agents"
    mkdir -p "$CODEX_TARGET/agent-profiles"
    mkdir -p "$CODEX_TARGET/memories"

    run_task_line "seed local overrides" seed_default_local_home_agent_overrides || return 1

    run_task_line "validate docs" validate_codex_repo_docs || {
        print_error "Codex guidance validation failed, aborting Codex sync"
        return 1
    }

    run_task_line "sync memory layout" ensure_memory_hygiene_layout || return 1

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        run_task_line "remove stale $skill_name" remove_skill_installation "$skill_name" || return 1
    done < <(list_removed_repo_managed_skill_names)

    run_task_line "sync root guidance" sync_root_guidance_files || return 1

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        run_task_line "sync $skill_name" sync_skill_to_codex "$skill_name" || return 1
    done < <(list_repo_skill_names)

    run_task_line "sync skill agent profiles" sync_skill_agent_profiles_to_codex || return 1

    run_task_line "sync memory wiring" sync_memory_status_reporter_home_wiring || {
        print_error "Failed to sync memory-status-reporter live home wiring"
        return 1
    }

    run_task_line "prune install noise" prune_repo_managed_installation_noise || return 1

    run_task_line "write install metadata" write_install_metadata || return 1
    run_task_line "track managed skills" write_managed_skill_inventory_from_repo || return 1
    run_task_line "track managed agents" write_managed_home_agent_inventory_from_repo || return 1
    run_task_line "track managed agent profiles" write_managed_agent_profile_inventory_from_repo || return 1

    if ! verify_sync_operation_result; then
        print_error "Post-sync verification failed after sync; Codex home may be partial"
        return 1
    fi

    refresh_bootstrap_entry_script_from_repo
    print_success "Codex skills sync complete"
}

sync_codex_delta_update() {
    local root_files_changed=$1
    shift
    local changed_skills=("$@")
    local removed_skills=()
    local skill_name

    if ! seed_default_local_home_agent_overrides; then
        print_error "Failed to seed local home-agent overrides"
        return 1
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        removed_skills+=("$skill_name")
    done < <(list_removed_repo_managed_skill_names)

    if [[ "$root_files_changed" == "true" ]]; then
        sync_root_guidance_files
    fi

    ensure_memory_hygiene_layout

    if [[ ${#removed_skills[@]} -gt 0 ]]; then
        print_info "Removing repo-managed skills no longer present in source: ${removed_skills[*]}"
        for skill_name in "${removed_skills[@]}"; do
            remove_skill_installation "$skill_name"
        done
    fi

    for skill_name in "${changed_skills[@]}"; do
        if ! sync_skill_to_codex "$skill_name"; then
            return 1
        fi
    done

    if ! sync_skill_agent_profiles_to_codex; then
        print_error "Failed to sync skill agent profiles"
        return 1
    fi

    if [[ "$root_files_changed" == "true" ]] || [[ " ${changed_skills[*]} " == *" memory-status-reporter "* ]]; then
        if ! sync_memory_status_reporter_home_wiring; then
            print_error "Failed to sync memory-status-reporter live home wiring"
            return 1
        fi
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        if ! sync_codex_home_agents_for_skill "$skill_name"; then
            print_error "Failed to refresh $skill_name home agent config"
            return 1
        fi
    done < <(list_repo_skill_names)

    if ! prune_repo_managed_installation_noise; then
        print_error "Failed to prune managed install noise"
        return 1
    fi

    write_install_metadata
    write_managed_skill_inventory_from_repo
    write_managed_home_agent_inventory_from_repo
    write_managed_agent_profile_inventory_from_repo

    if ! verify_sync_operation_result; then
        print_error "Post-sync verification failed after update; Codex home may be partial"
        return 1
    fi

    print_success "Codex skills delta update complete!"
    return 0
}
# Function to validate all skills
validate_all() {
    local failed=0
    local failed_skill_name

    run_task_line "validate docs" validate_codex_repo_docs || ((failed+=1))

    while IFS= read -r failed_skill_name; do
        [[ -n "$failed_skill_name" ]] || continue
        print_error "Validation failed for skill: $failed_skill_name"
        ((failed+=1))
    done < <(collect_failed_skill_names_parallel)

    if validate_should_skip_contract_tests; then
        print_info "Skipping nested contract suite because CODEX_SKIP_VALIDATE_CONTRACT_TESTS=1"
    else
        run_task_line "contract tests" run_repo_contract_tests || ((failed+=1))
    fi

    if [[ $failed -eq 0 ]]; then
        print_success "All skills validated successfully"
        return 0
    fi

    print_error "$failed skill(s) failed validation"
    return 1
}

validate_sync_operation_prerequisites() {
    local validation_mode="${CODEX_SYNC_VALIDATION_MODE:-fast}"
    local failed=0
    local failed_skill_name

    case "$validation_mode" in
        full)
            validate_all
            return $?
            ;;
        none)
            print_warning "Skipping install/update validation because CODEX_SYNC_VALIDATION_MODE=none"
            return 0
            ;;
        fast)
            run_task_line "validate docs" validate_codex_repo_docs || ((failed+=1))

            while IFS= read -r failed_skill_name; do
                [[ -n "$failed_skill_name" ]] || continue
                print_error "Validation failed for skill: $failed_skill_name"
                ((failed+=1))
            done < <(collect_failed_skill_names_parallel)

            if [[ $failed -eq 0 ]]; then
                print_success "Fast install/update validation passed"
                return 0
            fi

            print_error "$failed skill(s) failed fast install/update validation"
            return 1
            ;;
        *)
            print_error "Unsupported CODEX_SYNC_VALIDATION_MODE value: $validation_mode"
            print_info "Expected fast, full, or none."
            return 1
            ;;
    esac
}

PARALLEL_MANIFEST_STATUS_DIRECTORY=""

run_manifest_check_worker() {
    local skill_name=$1
    local source_directory="$CODEX_SOURCE/$skill_name"
    local target_directory="$CODEX_TARGET/skills/$skill_name"

    if [[ ! -d "$target_directory" ]]; then
        printf '%s\n' "$skill_name" > "$PARALLEL_MANIFEST_STATUS_DIRECTORY/$skill_name.changed"
        return 0
    fi

    if ! skill_directories_match_without_md5 "$source_directory" "$target_directory"; then
        printf '%s\n' "$skill_name" > "$PARALLEL_MANIFEST_STATUS_DIRECTORY/$skill_name.changed"
    fi
}

collect_changed_skills_parallel() {
    local status_directory
    local skill_name
    local worker_limit
    local parallel_exit_code=0

    status_directory="$(mktemp -d)"
    PARALLEL_MANIFEST_STATUS_DIRECTORY="$status_directory"
    repo_skill_names_array
    worker_limit="$(parallel_worker_limit)"

    if [[ ${#REPO_SKILL_NAMES[@]} -eq 0 ]]; then
        rm -rf "$status_directory"
        return 0
    fi

    if ! run_items_in_parallel run_manifest_check_worker "$worker_limit" "${REPO_SKILL_NAMES[@]}"; then
        parallel_exit_code=1
    fi

    for skill_name in "${REPO_SKILL_NAMES[@]}"; do
        if [[ -f "$status_directory/$skill_name.changed" ]]; then
            printf '%s\n' "$skill_name"
        fi
    done

    rm -rf "$status_directory"
    PARALLEL_MANIFEST_STATUS_DIRECTORY=""
    return $parallel_exit_code
}

collect_changed_agent_profile_names() {
    local agent_profile_name

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        if ! verify_agent_profile_sync_match "$agent_profile_name" >/dev/null 2>&1; then
            printf "%s\n" "$agent_profile_name"
        fi
    done < <(list_repo_agent_profile_names)
}

agent_profiles_need_update() {
    if [[ -n "$(collect_changed_agent_profile_names)" ]]; then
        return 0
    fi

    if [[ -n "$(list_removed_repo_managed_agent_profile_names)" ]]; then
        return 0
    fi

    return 1
}

skill_needs_update() {
    local skill_name=$1
    local changed_skill_name

    while IFS= read -r changed_skill_name; do
        [[ -n "$changed_skill_name" ]] || continue
        if [[ "$changed_skill_name" == "$skill_name" ]]; then
            return 0
        fi
    done < <(collect_changed_skills_parallel)

    return 1
}

collect_removed_skills() {
    local removed_skills=()
    local skill_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        removed_skills+=("$skill_name")
    done < <(list_removed_repo_managed_skill_names)

    if [[ ${#removed_skills[@]} -eq 0 ]]; then
        return 0
    fi

    printf '%s\n' "${removed_skills[@]}"
}

core_files_need_update() {
    if root_guidance_files_need_update; then
        return 0
    fi

    if agent_profiles_need_update; then
        return 0
    fi

    return 1
}

root_guidance_files_need_update() {
    local relative_path

    while IFS= read -r relative_path; do
        [[ -n "$relative_path" ]] || continue
        local source_path="$CODEX_SOURCE/$relative_path"
        local target_path="$CODEX_TARGET/$relative_path"

        if [[ ! -f "$target_path" ]]; then
            return 0
        fi

        if ! files_have_same_content "$source_path" "$target_path"; then
            return 0
        fi
    done < <(list_root_guidance_relative_paths)

    return 1
}

show_checksum_status() {
    local changed_skills=()
    local removed_skills=()
    local changed_agent_profiles=()
    local removed_agent_profiles=()
    local skill_name
    local agent_profile_name

    if ! pack_is_installed; then
        echo "  core file checksum status: not installed"
        echo "  skill agent profile checksum status: not installed"
        echo "  skill checksum status: not installed"
        echo "  stale managed skills: none"
        echo "  stale managed agent profiles: none"
        return 0
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        if skill_needs_update "$skill_name"; then
            changed_skills+=("$skill_name")
        fi
    done < <(list_repo_skill_names)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        changed_agent_profiles+=("$agent_profile_name")
    done < <(collect_changed_agent_profile_names)

    if core_files_need_update; then
        echo "  core file checksum status: drift detected"
    else
        echo "  core file checksum status: in sync"
    fi

    if [[ ${#changed_skills[@]} -eq 0 ]]; then
        echo "  skill checksum status: all installed skills match source"
    else
        echo "  skill checksum status: drift in ${changed_skills[*]}"
    fi

    if [[ ${#changed_agent_profiles[@]} -eq 0 ]]; then
        echo "  skill agent profile checksum status: all installed agent profiles match source"
    else
        echo "  skill agent profile checksum status: drift in ${changed_agent_profiles[*]}"
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        removed_skills+=("$skill_name")
    done < <(list_removed_repo_managed_skill_names)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        removed_agent_profiles+=("$agent_profile_name")
    done < <(list_removed_repo_managed_agent_profile_names)

    if [[ ${#removed_skills[@]} -eq 0 ]]; then
        echo "  stale managed skills: none"
    else
        echo "  stale managed skills: ${removed_skills[*]}"
    fi

    if [[ ${#removed_agent_profiles[@]} -eq 0 ]]; then
        echo "  stale managed agent profiles: none"
    else
        echo "  stale managed agent profiles: ${removed_agent_profiles[*]}"
    fi
}

remove_home_agent_installation() {
    local skill_name=$1
    local home_agent_name=$2

    if [[ -f "$CODEX_TARGET/agents/$home_agent_name.toml" ]]; then
        rm -f "$CODEX_TARGET/agents/$home_agent_name.toml"
    fi

    if [[ -f "$CODEX_TARGET/agent-profiles/$home_agent_name.toml" ]]; then
        rm -f "$CODEX_TARGET/agent-profiles/$home_agent_name.toml"
    fi

    strip_codex_home_agent_config_section "$home_agent_name"

    remove_home_agent_from_managed_inventory "$skill_name" "$home_agent_name"
    remove_agent_profile_from_managed_inventory "$home_agent_name"
}

remove_stale_home_agents_for_skill() {
    local skill_name=$1
    local tracked_home_agent_name
    local expected_home_agent_names

    expected_home_agent_names="$(list_skill_agent_config_files "$skill_name" | while IFS= read -r agent_config_path; do
        [[ -n "$agent_config_path" ]] || continue
        home_agent_name_from_agent_config "$skill_name" "$agent_config_path"
    done)"

    while IFS= read -r tracked_home_agent_name; do
        [[ -n "$tracked_home_agent_name" ]] || continue
        if ! grep -qxF -- "$tracked_home_agent_name" <<< "$expected_home_agent_names"; then
            if [[ "$tracked_home_agent_name" == "memory-status-reporter" ]]; then
                strip_memory_status_reporter_home_wiring
            fi
            remove_home_agent_installation "$skill_name" "$tracked_home_agent_name"
        fi
    done < <(list_tracked_home_agent_names_for_skill "$skill_name")
}

strip_memory_status_reporter_home_wiring() {
    local home_config_file="$CODEX_TARGET/config.toml"
    local routing_line="${MEMORY_STATUS_REQUIRED_CONFIG_LINES[0]}"
    local required_execution_lines_file

    [[ -f "$home_config_file" ]] || return 0

    required_execution_lines_file="$(mktemp)"
    printf '%s\n' "${MEMORY_STATUS_REQUIRED_CONFIG_LINES[@]:1}" > "$required_execution_lines_file"

    run_python - "$home_config_file" "$routing_line" "$required_execution_lines_file" <<'PY'
from pathlib import Path
import re
import sys

config_path = Path(sys.argv[1])
routing_line = sys.argv[2]
required_execution_lines = [
    line
    for line in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines()
    if line.strip()
]
config_text = config_path.read_text(encoding="utf-8")
config_text = config_text.replace(routing_line + "\n", "")
config_text = config_text.replace("\n" + routing_line, "")
for required_line in required_execution_lines:
    config_text = config_text.replace(required_line + "\n", "")
config_text = re.sub(r"\nExecution policy:\n(?=\n|''')", "\n", config_text)
config_text = re.sub(r"\n{3,}", "\n\n", config_text).strip() + "\n"
config_path.write_text(config_text, encoding="utf-8")
PY

    rm -f "$required_execution_lines_file"
}

strip_managed_config_routing_instructions() {
    local home_config_file="$CODEX_TARGET/config.toml"

    [[ -f "$home_config_file" ]] || return 0

    run_python - "$home_config_file" <<'PY'
from pathlib import Path
import re
import sys

config_path = Path(sys.argv[1])
config_text = config_path.read_text(encoding="utf-8")
block_header = "Managed skill-pack routing:"
block_footer = "Managed skill-pack routing end."
block_pattern = re.compile(
    rf"{re.escape(block_header)}\n.*?\n{re.escape(block_footer)}\n?",
    flags=re.DOTALL,
)
config_text = block_pattern.sub("", config_text)
config_text = re.sub(r"\n{3,}", "\n\n", config_text).strip()
config_path.write_text((config_text + "\n") if config_text else "", encoding="utf-8")
PY
}

strip_codex_home_agent_config_section() {
    local home_agent_name=$1
    local home_config_file="$CODEX_TARGET/config.toml"

    [[ -f "$home_config_file" ]] || return 0

    run_python - "$home_config_file" "$home_agent_name" <<'PY'
from pathlib import Path
import re
import sys

config_path = Path(sys.argv[1])
home_agent_name = sys.argv[2]
config_text = config_path.read_text(encoding="utf-8")
section_pattern = re.compile(rf"(?ms)^\[agents\.{re.escape(home_agent_name)}\]\n.*?(?=^\[|\Z)")
config_text = section_pattern.sub("", config_text)
config_text = re.sub(r"\n{3,}", "\n\n", config_text).strip()
config_path.write_text((config_text + "\n") if config_text else "", encoding="utf-8")
PY
}

remove_skill_installation() {
    local skill_name=$1
    local home_agent_name

    if [[ -f "$CODEX_TARGET/config.toml" ]]; then
        ensure_python_launcher || return 1
    fi

    if [[ -d "$CODEX_TARGET/skills/$skill_name" ]]; then
        rm -rf "$CODEX_TARGET/skills/$skill_name"
    fi

    while IFS= read -r home_agent_name; do
        [[ -n "$home_agent_name" ]] || continue
        if [[ "$home_agent_name" == "memory-status-reporter" ]]; then
            strip_memory_status_reporter_home_wiring
        fi
        remove_home_agent_installation "$skill_name" "$home_agent_name"
    done < <(list_tracked_home_agent_names_for_skill "$skill_name")

    rm -f "$(skill_manager_manifest_directory)/source/$skill_name.md5" 2>/dev/null || true
    rm -f "$(skill_manager_manifest_directory)/target/$skill_name.md5" 2>/dev/null || true

    remove_skill_from_managed_inventory "$skill_name"

    if [[ -d "$CODEX_TARGET/skills/$skill_name" ]]; then
        print_error "Failed to remove skill: $skill_name"
        return 1
    fi

    print_success "Removed skill from Codex home: $skill_name"
}

remove_skill_pack() {
    local skill_name
    local legacy_agent_profile_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        remove_skill_installation "$skill_name"
    done < <(list_tracked_managed_skill_names)

    strip_managed_config_routing_instructions

    for legacy_agent_profile_name in default explorer worker architect awaiter; do
        rm -f "$CODEX_TARGET/agent-profiles/$legacy_agent_profile_name.toml"
    done

    rm -f "$CODEX_TARGET/AGENTS.md"
    rm -f "$CODEX_TARGET/00-skill-routing-and-escalation.md"
    rm -rf "$(skill_manager_state_directory)" 2>/dev/null || true

    if [[ -f "$CODEX_TARGET/AGENTS.md" ]] || [[ -f "$CODEX_TARGET/00-skill-routing-and-escalation.md" ]]; then
        print_error "Failed to remove one or more core repo-managed Codex files"
        return 1
    fi

    print_success "Removed repo-managed Codex skill pack files from $CODEX_TARGET"
}

apply_repo_managed_changes() {
    local changed_skills=()
    local removed_skills=()
    local changed_agent_profiles=()
    local removed_agent_profiles=()
    local skill_name
    local root_files_changed="false"

    if ! ensure_sync_runtime_prerequisites; then
        print_error "Runtime prerequisites failed, aborting update"
        return 1
    fi

    if ! seed_default_local_home_agent_overrides; then
        print_error "Failed to seed local home-agent overrides"
        return 1
    fi

    if ! pack_is_installed; then
        print_info "No installed Codex skill pack was found in $CODEX_TARGET; running install instead of a delta refresh"
        sync_codex
        return $?
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        changed_skills+=("$skill_name")
    done < <(collect_changed_skills_parallel)

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        changed_agent_profiles+=("$skill_name")
    done < <(collect_changed_agent_profile_names)

   while IFS= read -r skill_name; do
       [[ -n "$skill_name" ]] || continue
       removed_skills+=("$skill_name")
   done < <(list_removed_repo_managed_skill_names)

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        removed_agent_profiles+=("$skill_name")
    done < <(list_removed_repo_managed_agent_profile_names)

   if root_guidance_files_need_update; then
       root_files_changed="true"
   fi

    if [[ "$root_files_changed" == "false" ]] && [[ ${#changed_skills[@]} -eq 0 ]] && [[ ${#removed_skills[@]} -eq 0 ]] && [[ ${#changed_agent_profiles[@]} -eq 0 ]] && [[ ${#removed_agent_profiles[@]} -eq 0 ]]; then
        print_success "Installed skill pack is already up to date"
        verify_sync_operation_result || return 1
        write_install_metadata || return 1
        refresh_bootstrap_entry_script_from_repo
        return 0
    fi

    print_info "update plan: manager=$(get_manager_version) repo=$(get_repo_version) installed=$(get_installed_version) changed=${#changed_skills[@]} removed=${#removed_skills[@]} agent_profiles=${#changed_agent_profiles[@]} retired_agent_profiles=${#removed_agent_profiles[@]} root_refresh=$root_files_changed"
    sync_codex_delta_update "$root_files_changed" "${changed_skills[@]}" || return 1
    refresh_bootstrap_entry_script_from_repo
}

install_codex() {
    run_task_line "validate" validate_sync_operation_prerequisites || return 1

    if pack_is_installed; then
        print_info "Skill pack already exists in $CODEX_TARGET; install will refresh only the changed repo-managed files, including AGENTS.md and root routing when needed."
        CODEX_SYNC_PREREQUISITES_VALIDATED=true run_task_line "sync changes to $CODEX_TARGET" apply_repo_managed_changes
        return $?
    fi

    CODEX_SYNC_PREREQUISITES_VALIDATED=true run_task_line "install to $CODEX_TARGET" sync_codex
}

refresh_repo_before_update_if_possible() {
    local update_ref
    local remote_name
    local remote_branch
    local relationship
    local remote_url
    local previous_script_checksum
    local previous_manager_version
    local current_script_checksum
    local current_manager_version

    if ! ensure_sync_runtime_prerequisites; then
        print_error "Runtime prerequisites failed, aborting update"
        return 1
    fi

    if ! git_repository_available; then
        print_info "Git is unavailable for remote manager checks; using the current local repo state."
        return 0
    fi

    update_ref="$(git_resolve_update_source_ref || true)"
    if [[ -z "$update_ref" ]]; then
        print_info "No tracked remote update source was found; using the current local repo state."
        return 0
    fi

    remote_name="${update_ref%%/*}"
    remote_branch="${update_ref#*/}"
    remote_url="$(git_remote_url_for_name "$remote_name")"
    if [[ -z "$remote_url" ]]; then
        print_warning "No remote URL is configured for $remote_name in $CODEX_SOURCE; using the current local repo state."
        return 0
    fi

    if ! run_task_line "fetch $remote_name" git_fetch_remote_noninteractive "$remote_name"; then
        print_warning "Unable to refresh $update_ref; using the current local repo state."
        return 0
    fi

    if ! git_worktree_is_clean; then
        print_warning "Repository has local changes, so remote manager update is skipped. The current local repo state will still be synced into Codex home."
        return 0
    fi

    relationship="$(git_update_relationship "$update_ref")"
    case "$relationship" in
        up_to_date)
            print_success "Repository already matches $update_ref"
            ;;
        behind)
            previous_script_checksum="$(sync_script_checksum_from_file "$CODEX_SOURCE/sync-skills.sh")"
            previous_manager_version="$(sync_script_version_from_file "$CODEX_SOURCE/sync-skills.sh")"
            run_task_line "pull $update_ref" git -C "$CODEX_SOURCE" pull --ff-only "$remote_name" "$remote_branch" || return 1
            current_script_checksum="$(sync_script_checksum_from_file "$CODEX_SOURCE/sync-skills.sh")"
            current_manager_version="$(sync_script_version_from_file "$CODEX_SOURCE/sync-skills.sh")"
            if [[ "$previous_script_checksum" != "$current_script_checksum" ]]; then
                print_info "sync-skills.sh changed during the repo update (${previous_manager_version} -> ${current_manager_version}); restarting into the refreshed manager before continuing."
                refresh_bootstrap_entry_script_from_repo
                exec bash "$CODEX_SOURCE/sync-skills.sh" "$SYNC_SKILLS_INTERNAL_UPDATE_RESUME_COMMAND"
            fi
            ;;
        ahead)
            print_info "Local repository is ahead of $update_ref; syncing the newer local repo state into Codex home."
            ;;
        diverged)
            print_warning "Repository diverged from $update_ref; skipping remote manager update and syncing the current local repo state instead."
            ;;
        *)
            print_warning "Unable to compare the repo with $update_ref after fetch; syncing the current local repo state instead."
            ;;
    esac

    return 0
}

update_codex() {
    refresh_repo_before_update_if_possible || return 1
    run_task_line "validate" validate_sync_operation_prerequisites || return 1
    CODEX_SYNC_PREREQUISITES_VALIDATED=true run_task_line "apply repo updates" apply_repo_managed_changes
}

update_codex_from_github() {
    update_codex
}

choose_installed_skill_interactively() {
    local installed_skills=()
    local selected_skill

    populate_array_from_command installed_skills list_installed_skill_names
    if [[ ${#installed_skills[@]} -eq 0 ]]; then
        print_warning "No installed skills were found in $CODEX_TARGET/skills"
        return 1
    fi

    print_info "Select an installed skill:"
    select selected_skill in "${installed_skills[@]}" "Cancel"; do
        if [[ "$selected_skill" == "Cancel" ]]; then
            return 1
        fi
        if [[ -n "$selected_skill" ]]; then
            printf '%s\n' "$selected_skill"
            return 0
        fi
        print_warning "Choose a valid option."
    done
}

prompt_yes_no() {
    local prompt_message=$1
    local default_answer=${2:-Y}
    local user_input

    read -r -p "$prompt_message [$default_answer/n]: " user_input
    user_input="${user_input:-$default_answer}"
    [[ "$user_input" =~ ^[Yy]$ ]]
}

run_interactive_menu() {
    local menu_choice

    while true; do
        echo ""
        print_header "Codex Skill Manager"
        print_menu_option "1" "Install - install the skill pack, or refresh changed repo-managed files when it is already installed"
        print_menu_option "2" "Update  - check for manager/repo updates first, restart into the new script if needed, then update installed skills"
        print_menu_option "3" "Status  - check manager version, self-update state, skill-pack update state, and wiring health"
        print_menu_option "4" "Quit"
        echo ""
        read -r -p "select: " menu_choice

        case "$menu_choice" in
            i|install|1)
                if prompt_yes_no "Install the repo skill pack into $CODEX_TARGET? If it is already installed, only changed repo-managed files will be refreshed."; then
                    install_codex
                fi
                ;;
            u|update|2)
                if prompt_yes_no "Check for manager updates first, restart into the new script if needed, and then update the installed skill pack in $CODEX_TARGET?"; then
                    update_codex_from_github
                fi
                ;;
            st|status|3)
                show_status
                ;;
            q|quit|4)
                print_success "Goodbye"
                return 0
                ;;
            *)
                print_warning "Choose a valid option"
                ;;
        esac
    done
}

# Function to show status
summarize_self_update_status() {
    local update_ref
    local relationship
    local dirty_note=""

    if ! git_repository_available; then
        printf 'local repo only (git unavailable)\n'
        return 0
    fi

    update_ref="$(git_resolve_update_source_ref || true)"
    if [[ -z "$update_ref" ]]; then
        printf 'local repo only (no tracked remote update source)\n'
        return 0
    fi

    if ! git_worktree_is_clean; then
        dirty_note="; local changes present"
    fi

    relationship="$(git_update_relationship "$update_ref")"
    case "$relationship" in
        up_to_date)
            printf 'up to date with %s (cached remote state)%s\n' "$update_ref" "$dirty_note"
            ;;
        behind)
            printf 'update available from %s (cached remote state)%s\n' "$update_ref" "$dirty_note"
            ;;
        ahead)
            printf 'local repo is ahead of %s (cached remote state)%s\n' "$update_ref" "$dirty_note"
            ;;
        diverged)
            printf 'local repo diverged from %s (cached remote state)%s\n' "$update_ref" "$dirty_note"
            ;;
        *)
            printf 'unknown for %s (cached remote state)%s\n' "$update_ref" "$dirty_note"
            ;;
    esac
}

summarize_skill_pack_update_status() {
    local changed_skills=()
    local removed_skills=()
    local changed_agent_profiles=()
    local removed_agent_profiles=()
    local detail_parts=()
    local skill_name
    local agent_profile_name

    if ! pack_is_installed; then
        printf 'not installed\n'
        return 0
    fi

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        changed_skills+=("$skill_name")
    done < <(collect_changed_skills_parallel)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        changed_agent_profiles+=("$agent_profile_name")
    done < <(collect_changed_agent_profile_names)

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        removed_skills+=("$skill_name")
    done < <(list_removed_repo_managed_skill_names)

    while IFS= read -r agent_profile_name; do
        [[ -n "$agent_profile_name" ]] || continue
        removed_agent_profiles+=("$agent_profile_name")
    done < <(list_removed_repo_managed_agent_profile_names)

    if ! core_files_need_update && [[ ${#changed_skills[@]} -eq 0 ]] && [[ ${#removed_skills[@]} -eq 0 ]] && [[ ${#changed_agent_profiles[@]} -eq 0 ]] && [[ ${#removed_agent_profiles[@]} -eq 0 ]]; then
        printf 'up to date\n'
        return 0
    fi

    if root_guidance_files_need_update; then
        detail_parts+=("root guidance changed")
    fi

    if [[ ${#changed_skills[@]} -gt 0 ]]; then
        detail_parts+=("${#changed_skills[@]} skill change(s)")
    fi

    if [[ ${#changed_agent_profiles[@]} -gt 0 ]]; then
        detail_parts+=("${#changed_agent_profiles[@]} agent profile change(s)")
    fi

    if [[ ${#removed_skills[@]} -gt 0 ]]; then
        detail_parts+=("${#removed_skills[@]} retired skill(s)")
    fi

    if [[ ${#removed_agent_profiles[@]} -gt 0 ]]; then
        detail_parts+=("${#removed_agent_profiles[@]} retired agent profile(s)")
    fi

    printf 'update available (%s)\n' "$(IFS=", "; echo "${detail_parts[*]}")"
}

show_status() {
    local self_update_status
    local skill_pack_update_status

    self_update_status="$(summarize_self_update_status)"
    skill_pack_update_status="$(summarize_skill_pack_update_status)"

    print_info "Codex Skill Pack Status"
    echo ""
    print_info "Summary:"
    print_key_value "Manager version:" "$(get_manager_version)"
    print_key_value "Repo version:" "$(get_repo_version)"
    print_key_value "Installed version:" "$(get_installed_version)"
    print_key_value "Self update status:" "$self_update_status"
    print_key_value "Skill pack update status:" "$skill_pack_update_status"
    echo ""

    print_info "Codex Skills:"
    echo "  Source: $CODEX_SOURCE"
    echo "  Target: $CODEX_TARGET/skills"
    echo "  Platform: $PLATFORM_NAME"
    if git_repository_available; then
        local git_remote_name
        local git_remote_url
        local git_update_source
        git_update_source="$(git_resolve_update_source_ref || true)"
        git_remote_name="${git_update_source%%/*}"
        if [[ -n "$git_remote_name" ]] && [[ "$git_remote_name" != "$git_update_source" ]]; then
            git_remote_url="$(git_remote_url_for_name "$git_remote_name")"
        fi
        echo "  Git remote: ${git_remote_url:-not configured}"
        echo "  Git update source: ${git_update_source:-not configured}"
    else
        echo "  Git remote: unavailable"
        echo "  Git update source: unavailable"
    fi

    local codex_source_count=0
    local codex_synced_count=0
   local codex_home_agent_total=0
   local codex_home_agent_explicit=0
   local codex_home_agent_medium=0
   local codex_home_agent_non_medium=()
   local codex_home_agent_config_sections=0
    local codex_agent_profile_total=0
    local codex_agent_profile_synced=0
    local codex_agent_profile_medium=0
   for skill_dir in "$CODEX_SOURCE"/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            ((codex_source_count+=1))
            local skill_name=$(basename "$skill_dir")
            if [[ -f "$CODEX_TARGET/skills/$skill_name/SKILL.md" ]]; then
                ((codex_synced_count+=1))
            fi

            local agent_config_path
            while IFS= read -r agent_config_path; do
                [[ -n "$agent_config_path" ]] || continue
               local home_agent_name
               home_agent_name="$(home_agent_name_from_agent_config "$skill_name" "$agent_config_path")"
               local home_agent_file="$CODEX_TARGET/agents/$home_agent_name.toml"
                local agent_profile_file="$CODEX_TARGET/agent-profiles/$home_agent_name.toml"
               ((codex_agent_profile_total+=1))
               if [[ -f "$home_agent_file" ]]; then
                   ((codex_home_agent_total+=1))
                   if grep -q '^model = "gpt-5.4"$' "$home_agent_file" && grep -q '^model_reasoning_effort =' "$home_agent_file"; then
                       ((codex_home_agent_explicit+=1))
                   fi
                   if grep -q '^model_reasoning_effort = "medium"$' "$home_agent_file"; then
                       ((codex_home_agent_medium+=1))
                   else
                       codex_home_agent_non_medium+=("$home_agent_name")
                   fi
               fi
               if config_has_agent_section "$CODEX_TARGET/config.toml" "$home_agent_name"; then
                   ((codex_home_agent_config_sections+=1))
               fi
                if [[ -f "$agent_profile_file" ]]; then
                    ((codex_agent_profile_synced+=1))
                    if grep -q '^model_reasoning_effort = "medium"$' "$agent_profile_file"; then
                        ((codex_agent_profile_medium+=1))
                    fi
                fi
           done < <(list_skill_agent_config_files "$skill_name")
       fi
   done

    if [[ -d "$CODEX_TARGET/skills" ]]; then
        echo "  Synced skills: $codex_synced_count/$codex_source_count"
    else
        echo "  Synced skills: 0/$codex_source_count (target directory not found)"
    fi

    echo ""
    print_info "Codex Home Wiring:"
    if [[ -f "$CODEX_TARGET/agents/memory-status-reporter.toml" ]]; then
        echo "  memory-status-reporter agent: synced"
    else
        echo "  memory-status-reporter agent: missing"
    fi

    local memory_status_override_model
    local memory_status_override_reasoning
    memory_status_override_model="$(read_local_home_agent_override_value "memory-status-reporter" "model" || true)"
    memory_status_override_reasoning="$(read_local_home_agent_override_value "memory-status-reporter" "reasoning_effort" || true)"
    if [[ -n "$memory_status_override_model" ]]; then
        echo "  memory-status-reporter local override: $memory_status_override_model (${memory_status_override_reasoning:-default reasoning})"
    else
        echo "  memory-status-reporter local override: missing"
    fi

    if [[ -f "$CODEX_TARGET/config.toml" ]] && grep -q "^\[agents\.memory-status-reporter\]" "$CODEX_TARGET/config.toml" && config_has_required_memory_status_lines "$CODEX_TARGET/config.toml"; then
        echo "  memory-status-reporter config: synced"
    elif config_has_any_memory_status_lines "$CODEX_TARGET/config.toml"; then
        echo "  memory-status-reporter config: partial"
    else
        echo "  memory-status-reporter config: missing"
    fi

    if config_has_required_managed_routing_lines "$CODEX_TARGET/config.toml"; then
        echo "  managed routing config: synced"
    elif config_has_any_managed_routing_lines "$CODEX_TARGET/config.toml"; then
        echo "  managed routing config: partial"
    else
        echo "  managed routing config: missing"
    fi

   if [[ -d "$CODEX_TARGET/memories/workspaces" ]] && [[ -d "$CODEX_TARGET/memories/agents" ]] && [[ -d "$CODEX_TARGET/memories/research_cache" ]] && [[ -d "$CODEX_TARGET/memories/archive" ]]; then
       echo "  memory scope layout: synced"
   else
       echo "  memory scope layout: missing"
   fi

    echo "  skill agent profiles: $codex_agent_profile_synced/$codex_agent_profile_total"
    if [[ $codex_agent_profile_total -gt 0 ]]; then
        echo "  skill agent profile medium baseline: $codex_agent_profile_medium/$codex_agent_profile_total"
    fi

    if [[ $codex_home_agent_total -gt 0 ]]; then
        echo "  agent explicit wiring: $codex_home_agent_explicit/$codex_home_agent_total"
        echo "  agent medium baseline: $codex_home_agent_medium/$codex_home_agent_total"
        echo "  agent config sections: $codex_home_agent_config_sections/$codex_home_agent_total"
        if [[ ${#codex_home_agent_non_medium[@]} -gt 0 ]]; then
            echo "  agent non-medium overrides: ${codex_home_agent_non_medium[*]}"
        fi
    else
        echo "  agent explicit wiring: 0/0"
        echo "  agent medium baseline: 0/0"
        echo "  agent config sections: 0/0"
    fi

    echo ""
    print_info "MD5 Verification:"
    show_checksum_status
    echo ""
}

# Main script
show_usage() {
    echo "Usage: $0 [menu|install|i|update|u|status|st|validate|verify|remove|all]"
    echo ""
    echo "Commands:"
    echo "  menu              - Open the simple interactive manager with Install, Update, Status, and Quit"
    echo "  install | i       - Install the skill pack, or refresh changed repo-managed files if it is already installed"
    echo "  update | u        - Check for repo/manager updates first, restart into the refreshed script if needed, then update installed skills"
    echo "  status | st       - Show manager version, self-update state, skill-pack update state, and checksum drift"
    echo "  validate          - Advanced: validate all skills without syncing"
    echo "  verify | v        - Advanced: verify the installed skill pack with MD5 checksums"
    echo "  verify <skill>    - Advanced: verify one installed skill with MD5 checksums"
    echo "  remove            - Advanced: remove the full repo-managed skill pack"
    echo "  remove <skill>    - Advanced: remove one installed skill by name"
    echo "  uninstall         - Alias for remove"
    echo "  all               - Validate and install"
    echo ""
    echo "Legacy aliases:"
    echo "  sync | s | codex  - Alias for install"
    echo "  github-update | gu | upgrade - Alias for update"
    echo ""
    echo "Environment:"
    echo "  CODEX_TARGET_OVERRIDE=/custom/path/.codex  Override the Codex home target"
    echo "  CODEX_SKILLS_REPOSITORY_PATH=/path/to/codex_skills  Use an explicit repo path instead of a fresh temporary bootstrap clone"
    echo "  CODEX_SKILLS_REPOSITORY_URL=https://github.com/owner/repo.git  Override the bootstrap clone source"
    echo "  CODEX_SKILLS_REPOSITORY_BRANCH=main  Override the bootstrap clone branch"
    echo "  CODEX_SYNC_VALIDATION_MODE=fast|full|none  Choose install/update validation depth (default: fast)"
    echo "  CODEX_SYNC_POST_SYNC_VERIFICATION_MODE=fast|full|none  Choose install/update post-sync verification depth (default: fast)"
}

main() {
    print_header "Codex Skills"

    case "${1:-}" in
        menu)
            run_interactive_menu
            ;;
        install|i)
            install_codex
            ;;
        sync|s|codex)
            install_codex
            ;;
        update|u)
            update_codex
            ;;
        github-update|gu|upgrade)
            update_codex_from_github
            ;;
        "$SYNC_SKILLS_INTERNAL_UPDATE_RESUME_COMMAND")
            run_task_line "validate" validate_all || {
                print_error "Validation failed after the manager restarted"
                exit 1
            }
            run_task_line "apply repo updates" apply_repo_managed_changes
            ;;
        remove|uninstall)
            if [[ -n "${2:-}" ]]; then
                remove_skill_installation "$2"
            else
                remove_skill_pack
            fi
            ;;
        verify|v)
            if [[ -n "${2:-}" ]]; then
                run_task_line "verify $2" verify_skill_checksum "$2"
            else
                verify_pack_checksums
            fi
            ;;
        validate)
            validate_all
            ;;
        status|st)
            show_status
            ;;
        "")
            run_interactive_menu
            ;;
        all)
            install_codex
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac

    print_success "Done"
}

main "$@"
