#!/bin/bash

# Sync and validate script for the Codex skill pack.
# This script validates the repo, syncs skills into the active Codex home,
# and keeps the live memory-status wiring aligned with the repo.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_SOURCE="$SCRIPT_DIR"

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

MEMORY_STATUS_REQUIRED_CONFIG_LINES=(
    "- Route to memory-status-reporter for memory status, daily learning recaps, mistake ledgers, user-needs summaries, and heuristic growth reporting."
    "- Start every non-trivial task by translating the raw request into a working brief: user story, desired outcome, constraints, assumptions, acceptance criteria, edge cases, and validation plan."
    "- Strengthen vague prompts from repository, runtime, and memory evidence before acting; if business logic remains ambiguous, clarify instead of drifting."
    "- For code work, prefer test-first when practical by starting with a failing test or executable acceptance check before implementation."
    "- Keep researching during implementation whenever APIs, tools, edge cases, or best practices are uncertain; do not trust stale memory alone."
    "- Use a context retrieval ladder to save tokens: exact file or symbol search first, then targeted snippets, then full-file reads only for the files you will edit or directly depend on."
    "- Prefer surgical patches and modular edits: change only impacted ranges, keep stable prefixes for cache reuse, and avoid rewriting whole files when a targeted patch is sufficient."
    "- Prefer modular structure: keep entrypoints thin, move named logic into focused files, and separate backend, API, frontend, workers, and tests when the project spans those concerns."
    "- Before finalizing non-trivial work, re-read the working brief, acceptance criteria, and touched files, then append a compact Learning Snapshot grounded in memory artifacts when available."
    "- If a tool call fails or is misused and the fix teaches a reusable lesson, record it as a mistake with tool name, symptom, cause, fix, and prevention note in rollout summaries and durable memory."
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

skill_manager_state_directory() {
    printf '%s/.codex-skill-manager\n' "$CODEX_TARGET"
}

skill_manager_manifest_directory() {
    printf '%s/manifests\n' "$(skill_manager_state_directory)"
}

skill_manager_metadata_file() {
    printf '%s/install-metadata.txt\n' "$(skill_manager_state_directory)"
}

ensure_skill_manager_state_directories() {
    mkdir -p "$(skill_manager_manifest_directory)/source"
    mkdir -p "$(skill_manager_manifest_directory)/target"
}

get_repo_version() {
    git -C "$CODEX_SOURCE" rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

get_installed_version() {
    local metadata_file
    metadata_file="$(skill_manager_metadata_file)"

    if [[ -f "$metadata_file" ]]; then
        awk -F= '/^repo_version=/{print $2}' "$metadata_file"
        return 0
    fi

    echo "unknown"
}

write_install_metadata() {
    local metadata_file
    metadata_file="$(skill_manager_metadata_file)"

    ensure_skill_manager_state_directories
    cat > "$metadata_file" <<EOF
repo_version=$(get_repo_version)
updated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
platform=$PLATFORM_NAME
target=$CODEX_TARGET
EOF
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
        md5sum "$file_path" | awk '{print tolower($1)}'
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

copy_managed_skill_content() {
    local source_skill_directory=$1
    local target_skill_directory=$2
    local relative_directory

    cp "$source_skill_directory/SKILL.md" "$target_skill_directory/SKILL.md"

    for relative_directory in "${SKILL_SYNC_DIRECTORIES[@]}"; do
        copy_skill_directory_if_present "$source_skill_directory" "$target_skill_directory" "$relative_directory"
    done
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

verify_pack_checksums() {
    local failed=0
    local skill_name

    verify_root_file_checksum "AGENTS.md" || failed=1
    verify_root_file_checksum "00-skill-routing-and-escalation.md" || failed=1

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        verify_skill_checksum "$skill_name" || failed=1
    done < <(list_repo_skill_names)

    if [[ $failed -eq 0 ]]; then
        print_success "All MD5 verification checks passed."
        return 0
    fi

    print_error "One or more MD5 verification checks failed."
    return 1
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

# Validate a Codex skill directory for Codex-specific requirements and separation.
validate_codex_skill_dir() {
    local skill_dir=$1
    local skill_name=$(basename "$skill_dir")

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

    if ! validate_codex_agent_config "$skill_name" "$skill_dir/agents/openai.yaml"; then
        return 1
    fi

    if ! grep -q "js_repl" "$skill_dir/SKILL.md" || ! grep -q "codex.tool" "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md must mention js_repl + codex.tool runtime usage: $skill_name"
        return 1
    fi

    if ! grep -q "wait for them to reach a terminal state before finalizing" "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md must require waiting for required sub-agents: $skill_name"
        return 1
    fi

    if ! grep -q "Do not close a required running sub-agent merely because local evidence seems sufficient" "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md must forbid closing a running required sub-agent early: $skill_name"
        return 1
    fi

    if ! grep -qi "keep at most one live same-role agent" "$skill_dir/SKILL.md" || ! grep -qi "never spawn a second same-role sub-agent if one already exists" "$skill_dir/SKILL.md" || ! grep -qi 'always reuse it with `send_input` or `resume_agent`' "$skill_dir/SKILL.md" || ! grep -qi "resume a closed same-role agent before considering any new spawn" "$skill_dir/SKILL.md" || ! grep -q "fork_context" "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md must require strict same-role reuse, resume/send_input, and fork_context default-off: $skill_name"
        return 1
    fi

    if ! grep -q "maintain a lightweight spawned-agent list" "$skill_dir/SKILL.md" || ! grep -q "send a robust handoff covering the exact objective" "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md must require spawned-agent tracking and robust delegation packets: $skill_name"
        return 1
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
            if ! grep -qi "Structure Matters" "$skill_dir/SKILL.md" || ! grep -qi "REQUIRE thin entrypoints" "$skill_dir/SKILL.md" || ! grep -qi "Coverage matches the touched layers" "$skill_dir/SKILL.md"; then
                print_error "Reviewer skill is missing enforced structure or layered-testing guidance"
                return 1
            fi
            ;;
        software-development-life-cycle)
            if ! grep -q "## Context and Structure Defaults" "$skill_dir/SKILL.md" || ! grep -q "## Modular Delivery Defaults" "$skill_dir/SKILL.md" || ! grep -qi "Keep entrypoints thin" "$skill_dir/SKILL.md"; then
                print_error "Software-development-life-cycle skill is missing context or modular-delivery defaults"
                return 1
            fi
            ;;
        web-development-life-cycle)
            if ! grep -q "## Structure Defaults" "$skill_dir/SKILL.md" || ! grep -qi "server actions" "$skill_dir/SKILL.md" || ! grep -qi "higher-layer confirmation" "$skill_dir/SKILL.md"; then
                print_error "Web-development-life-cycle skill is missing structure or layered-test defaults"
                return 1
            fi
            ;;
        backend-and-data-architecture)
            if ! grep -q "## Structure Defaults" "$skill_dir/SKILL.md" || ! grep -qi "transport adapters" "$skill_dir/SKILL.md" || ! grep -qi "services or use cases" "$skill_dir/SKILL.md"; then
                print_error "Backend-and-data-architecture skill is missing structure defaults"
                return 1
            fi
            ;;
        qa-and-automation-engineer)
            if ! grep -q "## Layered Coverage Defaults" "$skill_dir/SKILL.md" || ! grep -qi "higher-layer confirmation" "$skill_dir/SKILL.md" || ! grep -qi "module or layer they protect" "$skill_dir/SKILL.md"; then
                print_error "QA-and-automation-engineer skill is missing layered-coverage defaults"
                return 1
            fi
            ;;
        ui-design-systems-and-responsive-interfaces)
            if ! grep -q "## Design Intelligence Packet" "$skill_dir/SKILL.md" || ! grep -q "## Brownfield Redesign Defaults" "$skill_dir/SKILL.md" || ! grep -q "Storybook, Ladle, or Histoire" "$skill_dir/SKILL.md"; then
                print_error "UI skill is missing design-intelligence, brownfield, or component-verification defaults"
                return 1
            fi
            if ! grep -q "## Professional Polish Checks" "$skill_dir/SKILL.md" || ! grep -q "No emoji as product UI icons" "$skill_dir/SKILL.md"; then
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
            if ! grep -q "## Experience Brief Defaults" "$skill_dir/SKILL.md" || ! grep -q "## Brownfield Redesign and Artifact Persistence" "$skill_dir/SKILL.md" || ! grep -q "Storybook, Ladle, Histoire" "$skill_dir/SKILL.md"; then
                print_error "UX skill is missing experience-brief, brownfield, or validation-loop defaults"
                return 1
            fi
            if ! grep -q "## Decision Confidence and Recovery Checks" "$skill_dir/SKILL.md" || ! grep -q "Errors preserve progress" "$skill_dir/SKILL.md"; then
                print_error "UX skill is missing decision-confidence or recovery checks"
                return 1
            fi
            if [[ ! -f "$skill_dir/references/55-experience-briefs-brownfield-and-validation-loops.md" ]] || ! grep -q "55-experience-briefs-brownfield-and-validation-loops.md" "$skill_dir/references/00-ux-knowledge-map.md"; then
                print_error "UX skill references are missing the experience-brief brownfield reference wiring"
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
    local config_file=$2
    local expected_model="gpt-5.4"
    local expected_reasoning="high"

    if [[ -f "$CODEX_TARGET/config.toml" ]]; then
        local detected_model
        detected_model=$(awk -F'"' '/^model = / {print $2; exit}' "$CODEX_TARGET/config.toml")
        if [[ -n "$detected_model" ]]; then
            expected_model="$detected_model"
        fi

        local detected_reasoning
        detected_reasoning=$(awk -F'"' '/^model_reasoning_effort = / {print $2; exit}' "$CODEX_TARGET/config.toml")
        if [[ -n "$detected_reasoning" ]]; then
            expected_reasoning="$detected_reasoning"
        fi
    fi

    if grep -q "^model:" "$config_file"; then
        print_error "Codex skill config should not pin model; rely on workspace default $expected_model: $skill_name"
        return 1
    fi

    if ! grep -q "^reasoning_effort: \"$expected_reasoning\"$" "$config_file"; then
        print_error "Unexpected reasoning_effort for Codex skill $skill_name (expected $expected_reasoning to match the main agent baseline)"
        return 1
    fi

    if ! grep -q "js_repl" "$config_file" || ! grep -q "codex.tool" "$config_file"; then
        print_error "Codex agent prompt must mention js_repl + codex.tool runtime usage: $skill_name"
        return 1
    fi

    if ! grep -q "Always research current external information before trusting internal knowledge" "$config_file"; then
        print_error "Codex agent prompt must require current external research: $skill_name"
        return 1
    fi

    if ! grep -q "wait for them to reach a terminal state before finalizing" "$config_file"; then
        print_error "Codex agent prompt must require waiting for required sub-agents: $skill_name"
        return 1
    fi

    if ! grep -q "Do not close a required running sub-agent merely because local evidence seems sufficient" "$config_file"; then
        print_error "Codex agent prompt must forbid closing a running required sub-agent early: $skill_name"
        return 1
    fi

    if ! grep -q "keep at most one live same-role agent" "$config_file" || ! grep -q "never spawn a second same-role sub-agent if one already exists" "$config_file" || ! grep -q "always reuse it with send_input or resume_agent" "$config_file" || ! grep -q "resume a closed same-role agent before considering any new spawn" "$config_file" || ! grep -q "fork_context off unless the exact parent thread history is required" "$config_file"; then
        print_error "Codex agent prompt must require strict same-role reuse, resume/send_input, and fork_context default-off: $skill_name"
        return 1
    fi

    if ! grep -q "maintain a lightweight spawned-agent list" "$config_file" || ! grep -q "send a robust handoff covering the exact objective" "$config_file"; then
        print_error "Codex agent prompt must require spawned-agent tracking and robust delegation packets: $skill_name"
        return 1
    fi

    if ! grep -q "working brief" "$config_file" || ! grep -q "test-first when practical" "$config_file"; then
        print_error "Codex agent prompt must require prompt alignment and test-first guidance: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && ! grep -q "Raise the design bar: act like a strong product designer" "$config_file"; then
        print_error "UI skill prompt must require a stronger product-design bar: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && { ! grep -q "design intelligence packet" "$config_file" || ! grep -q "Storybook, Ladle, or Histoire" "$config_file" || ! grep -q "master plus page-override pattern" "$config_file"; }; then
        print_error "UI skill prompt must require design-intelligence packets, brownfield-safe persistence, and component-story verification: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ui-design-systems-and-responsive-interfaces" ]] && ! grep -q 'scripts/design_intelligence.py' "$config_file"; then
        print_error "UI skill prompt must point to the local design-intelligence generator: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ux-research-and-experience-strategy" ]] && ! grep -q "Start by hardening the request into a crisp product brief" "$config_file"; then
        print_error "UX skill prompt must require crisp product-brief hardening: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "ux-research-and-experience-strategy" ]] && { ! grep -q "Build an experience brief" "$config_file" || ! grep -q "safe fallback slugs" "$config_file" || ! grep -q "Storybook, Ladle, Histoire" "$config_file"; }; then
        print_error "UX skill prompt must require experience briefs, safe persistence, and component-preview validation loops: $skill_name"
        return 1
    fi

    if [[ "$skill_name" == "memory-status-reporter" ]] && ! grep -q "tool-use mistakes" "$config_file"; then
        print_error "Memory status prompt must mention tool-use mistakes explicitly: $skill_name"
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

        if ! grep -qi "maintain a lightweight per-project spawned-agent list" "$file"; then
            print_error "Missing spawned-agent registry policy in AGENTS.md"
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
extract_codex_openai_value() {
    local openai_yaml_path=$1
    local field_name=$2

    python3 - "$openai_yaml_path" "$field_name" <<'PY'
from pathlib import Path
import json
import re
import sys

openai_yaml_path = Path(sys.argv[1])
field_name = sys.argv[2]
openai_yaml_text = openai_yaml_path.read_text(encoding="utf-8")

field_patterns = {
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

sync_codex_home_agent_from_openai() {
    local skill_name=$1
    local openai_yaml_path="$CODEX_SOURCE/$skill_name/agents/openai.yaml"
    local home_agent_file="$CODEX_TARGET/agents/$skill_name.toml"

    if [[ ! -f "$openai_yaml_path" ]]; then
        print_warning "Skipping home agent sync for $skill_name because $openai_yaml_path is missing"
        return 0
    fi

    local default_prompt
    default_prompt=$(extract_codex_openai_value "$openai_yaml_path" "default_prompt") || {
        print_error "Unable to extract default_prompt for $skill_name"
        return 1
    }

    python3 - "$home_agent_file" "$default_prompt" <<'PY'
from pathlib import Path
import sys

home_agent_file = Path(sys.argv[1])
default_prompt = sys.argv[2]

if "'''" in default_prompt:
    raise SystemExit("Triple single quotes are not supported inside developer_instructions")

home_agent_file.parent.mkdir(parents=True, exist_ok=True)
home_agent_file.write_text(
    "developer_instructions = '''\n"
    f"{default_prompt}\n"
    "'''\n",
    encoding="utf-8",
)
PY

    print_success "Synced $skill_name home agent config to Codex"
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

    local short_description
    short_description=$(extract_codex_openai_value "$openai_yaml_path" "short_description") || {
        print_error "Unable to extract short_description for $skill_name"
        return 1
    }

    required_execution_lines_file="$(mktemp)"
    printf '%s\n' "${MEMORY_STATUS_REQUIRED_CONFIG_LINES[@]:1}" > "$required_execution_lines_file"

    python3 - "$home_config_file" "$routing_line" "$short_description" "$required_execution_lines_file" <<'PY'
from pathlib import Path
import re
import sys

home_config_file = Path(sys.argv[1])
routing_line = sys.argv[2]
short_description = sys.argv[3]
required_execution_lines = [
    line
    for line in Path(sys.argv[4]).read_text(encoding="utf-8").splitlines()
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

memory_status_agent_block = (
    "[agents.memory-status-reporter]\n"
    f'description = "{short_description}"\n'
    'config_file = "agents/memory-status-reporter.toml"\n'
)

section_pattern = re.compile(r"(?ms)^\[agents\.memory-status-reporter\]\n.*?(?=^\[|\Z)")
if section_pattern.search(config_text):
    config_text = section_pattern.sub(memory_status_agent_block + "\n", config_text, count=1)
else:
    if not config_text.endswith("\n"):
        config_text += "\n"
    config_text += "\n" + memory_status_agent_block

home_config_file.write_text(config_text, encoding="utf-8")
PY

    rm -f "$required_execution_lines_file"

    print_success "Synced $skill_name global routing into Codex config.toml"
    return 0
}

# Function to sync Codex skills
sync_codex() {
    print_info "Syncing Codex skills..."

    # Create target directory if it doesn't exist
    mkdir -p "$CODEX_TARGET"
    mkdir -p "$CODEX_TARGET/skills"
    mkdir -p "$CODEX_TARGET/agents"

    if ! validate_codex_repo_docs; then
        print_error "Codex guidance validation failed, aborting Codex sync"
        return 1
    fi

    # Sync AGENTS.md
    if [[ -f "$CODEX_SOURCE/AGENTS.md" ]]; then
        cp "$CODEX_SOURCE/AGENTS.md" "$CODEX_TARGET/AGENTS.md"
        print_success "Synced AGENTS.md to Codex"
    else
        print_warning "AGENTS.md not found in source"
    fi

    # Sync skill routing
    if [[ -f "$CODEX_SOURCE/00-skill-routing-and-escalation.md" ]]; then
        cp "$CODEX_SOURCE/00-skill-routing-and-escalation.md" "$CODEX_TARGET/00-skill-routing-and-escalation.md"
        print_success "Synced skill routing to Codex"
    fi

    # Sync each skill directory
    for skill_dir in "$CODEX_SOURCE"/*/; do
        skill_name=$(basename "$skill_dir")

        # Skip if not a skill directory (no SKILL.md)
        if [[ ! -f "$skill_dir/SKILL.md" ]]; then
            continue
        fi

        print_info "Syncing $skill_name..."

        # Validate skill
        if ! validate_codex_skill_dir "$skill_dir"; then
            print_error "Validation failed for $skill_name, aborting Codex sync to prevent stale home state"
            return 1
        fi

        # Legacy cleanup: older versions synced to ~/.codex/<skill>/ instead of ~/.codex/skills/<skill>/.
        if [[ -d "$CODEX_TARGET/$skill_name" ]]; then
            print_warning "Removing legacy Codex skill directory: $CODEX_TARGET/$skill_name"
            rm -rf "$CODEX_TARGET/$skill_name"
        fi

        # Refresh target to the latest: remove prior sync to prevent stale files.
        if [[ -d "$CODEX_TARGET/skills/$skill_name" ]]; then
            rm -rf "$CODEX_TARGET/skills/$skill_name"
        fi

        # Create target skill directory (Codex expects skills under ~/.codex/skills/<skill>/)
        mkdir -p "$CODEX_TARGET/skills/$skill_name"

        copy_managed_skill_content "$skill_dir" "$CODEX_TARGET/skills/$skill_name"

        if ! sync_codex_home_agent_from_openai "$skill_name"; then
            print_error "Failed to sync $skill_name home agent config"
            return 1
        fi

        print_success "Synced $skill_name to Codex"
    done

    if ! sync_memory_status_reporter_home_wiring; then
        print_error "Failed to sync memory-status-reporter live home wiring"
        return 1
    fi

    write_install_metadata

    if ! verify_pack_checksums; then
        print_error "MD5 verification failed after sync; Codex home may be partial"
        return 1
    fi

    print_success "Codex skills sync complete!"
}
# Function to validate all skills
validate_all() {
    print_info "Validating all skills..."

    local failed=0

    if ! validate_codex_repo_docs; then
        ((failed+=1))
    fi

    # Validate Codex skills
    print_info "Validating Codex skills..."
    for skill_dir in "$CODEX_SOURCE"/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            if ! validate_codex_skill_dir "$skill_dir"; then
                ((failed+=1))
            fi
        fi
    done

    if [[ $failed -eq 0 ]]; then
        print_success "All skills validated successfully!"
        return 0
    else
        print_error "$failed skill(s) failed validation"
        return 1
    fi
}

skill_needs_update() {
    local skill_name=$1
    local source_directory="$CODEX_SOURCE/$skill_name"
    local target_directory="$CODEX_TARGET/skills/$skill_name"
    local source_manifest
    local target_manifest

    if [[ ! -d "$target_directory" ]]; then
        return 0
    fi

    source_manifest="$(mktemp)"
    target_manifest="$(mktemp)"

    build_skill_manifest "$source_directory" > "$source_manifest"
    build_skill_manifest "$target_directory" > "$target_manifest"

    if diff -u "$source_manifest" "$target_manifest" >/dev/null; then
        rm -f "$source_manifest" "$target_manifest"
        return 1
    fi

    rm -f "$source_manifest" "$target_manifest"
    return 0
}

core_files_need_update() {
    local relative_path

    for relative_path in "AGENTS.md" "00-skill-routing-and-escalation.md"; do
        local source_path="$CODEX_SOURCE/$relative_path"
        local target_path="$CODEX_TARGET/$relative_path"

        if [[ ! -f "$target_path" ]]; then
            return 0
        fi

        if [[ "$(md5_for_file "$source_path")" != "$(md5_for_file "$target_path")" ]]; then
            return 0
        fi
    done

    return 1
}

show_checksum_status() {
    local changed_skills=()
    local skill_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        if skill_needs_update "$skill_name"; then
            changed_skills+=("$skill_name")
        fi
    done < <(list_repo_skill_names)

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
}

strip_memory_status_reporter_home_wiring() {
    local home_config_file="$CODEX_TARGET/config.toml"
    local routing_line="${MEMORY_STATUS_REQUIRED_CONFIG_LINES[0]}"

    [[ -f "$home_config_file" ]] || return 0

    python3 - "$home_config_file" "$routing_line" <<'PY'
from pathlib import Path
import re
import sys

config_path = Path(sys.argv[1])
routing_line = sys.argv[2]
config_text = config_path.read_text(encoding="utf-8")
config_text = config_text.replace(routing_line + "\n", "")
config_text = config_text.replace("\n" + routing_line, "")
config_text = re.sub(r"(?ms)^\[agents\.memory-status-reporter\]\n.*?(?=^\[|\Z)", "", config_text)
config_text = re.sub(r"\n{3,}", "\n\n", config_text).strip() + "\n"
config_path.write_text(config_text, encoding="utf-8")
PY
}

remove_skill_installation() {
    local skill_name=$1

    if [[ -d "$CODEX_TARGET/skills/$skill_name" ]]; then
        rm -rf "$CODEX_TARGET/skills/$skill_name"
    fi

    if [[ -f "$CODEX_TARGET/agents/$skill_name.toml" ]]; then
        rm -f "$CODEX_TARGET/agents/$skill_name.toml"
    fi

    rm -f "$(skill_manager_manifest_directory)/source/$skill_name.md5" 2>/dev/null || true
    rm -f "$(skill_manager_manifest_directory)/target/$skill_name.md5" 2>/dev/null || true

    if [[ "$skill_name" == "memory-status-reporter" ]]; then
        strip_memory_status_reporter_home_wiring
    fi

    if [[ -d "$CODEX_TARGET/skills/$skill_name" ]] || [[ -f "$CODEX_TARGET/agents/$skill_name.toml" ]]; then
        print_error "Failed to remove skill: $skill_name"
        return 1
    fi

    print_success "Removed skill from Codex home: $skill_name"
}

remove_skill_pack() {
    local skill_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        remove_skill_installation "$skill_name"
    done < <(list_repo_skill_names)

    rm -f "$CODEX_TARGET/AGENTS.md"
    rm -f "$CODEX_TARGET/00-skill-routing-and-escalation.md"
    rm -rf "$(skill_manager_state_directory)" 2>/dev/null || true

    if [[ -f "$CODEX_TARGET/AGENTS.md" ]] || [[ -f "$CODEX_TARGET/00-skill-routing-and-escalation.md" ]]; then
        print_error "Failed to remove one or more core repo-managed Codex files"
        return 1
    fi

    print_success "Removed repo-managed Codex skill pack files from $CODEX_TARGET"
}

install_codex() {
    print_info "Installing Codex skill pack into $CODEX_TARGET"
    validate_all
    sync_codex
}

update_codex() {
    local changed_skills=()
    local skill_name

    while IFS= read -r skill_name; do
        [[ -n "$skill_name" ]] || continue
        if skill_needs_update "$skill_name"; then
            changed_skills+=("$skill_name")
        fi
    done < <(list_repo_skill_names)

    if ! core_files_need_update && [[ ${#changed_skills[@]} -eq 0 ]]; then
        print_success "Installed skill pack is already up to date."
        verify_pack_checksums
        return 0
    fi

    print_info "Repo version: $(get_repo_version)"
    print_info "Installed version: $(get_installed_version)"
    if [[ ${#changed_skills[@]} -gt 0 ]]; then
        print_info "Changed skills detected: ${changed_skills[*]}"
    else
        print_info "Core Codex home files changed; refreshing the installed skill pack."
    fi

    sync_codex
}

choose_installed_skill_interactively() {
    local installed_skills=()
    local selected_skill

    mapfile -t installed_skills < <(list_installed_skill_names)
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
    local selected_skill
    local remove_mode
    local verify_mode

    while true; do
        echo ""
        print_info "Codex Skill Manager"
        echo "  1) Install skill pack"
        echo "  2) Sync skill pack"
        echo "  3) Update installed skill pack"
        echo "  4) Remove installed skills"
        echo "  5) Verify MD5 checksums"
        echo "  6) Show status"
        echo "  7) Exit"
        echo ""
        read -r -p "Choose an option: " menu_choice

        case "$menu_choice" in
            1)
                if prompt_yes_no "Install the repo skill pack into $CODEX_TARGET?"; then
                    install_codex
                fi
                ;;
            2)
                if prompt_yes_no "Force-sync the repo skill pack into $CODEX_TARGET?"; then
                    sync_codex
                fi
                ;;
            3)
                update_codex
                ;;
            4)
                echo "  1) Remove one installed skill"
                echo "  2) Remove the full repo-managed skill pack"
                echo "  3) Cancel"
                read -r -p "Choose an option: " remove_mode
                case "$remove_mode" in
                    1)
                        selected_skill="$(choose_installed_skill_interactively)" || continue
                        if prompt_yes_no "Remove $selected_skill from $CODEX_TARGET?"; then
                            remove_skill_installation "$selected_skill"
                        fi
                        ;;
                    2)
                        if prompt_yes_no "Remove the full repo-managed skill pack from $CODEX_TARGET?" "n"; then
                            remove_skill_pack
                        fi
                        ;;
                    *)
                        print_info "Remove cancelled."
                        ;;
                esac
                ;;
            5)
                echo "  1) Verify the full installed skill pack"
                echo "  2) Verify one installed skill"
                echo "  3) Cancel"
                read -r -p "Choose an option: " verify_mode
                case "$verify_mode" in
                    1)
                        verify_pack_checksums
                        ;;
                    2)
                        selected_skill="$(choose_installed_skill_interactively)" || continue
                        verify_skill_checksum "$selected_skill"
                        ;;
                    *)
                        print_info "Verification cancelled."
                        ;;
                esac
                ;;
            6)
                show_status
                ;;
            7)
                print_success "Goodbye."
                return 0
                ;;
            *)
                print_warning "Choose a valid option."
                ;;
        esac
    done
}

# Function to show status
show_status() {
    print_info "Skill Sync Status"
    echo ""

    print_info "Codex Skills:"
    echo "  Source: $CODEX_SOURCE"
    echo "  Target: $CODEX_TARGET/skills"
    echo "  Platform: $PLATFORM_NAME"
    echo "  Repo version: $(get_repo_version)"
    echo "  Installed version: $(get_installed_version)"

    local codex_source_count=0
    local codex_synced_count=0
    local codex_home_agent_total=0
    local codex_home_agent_inheriting=0
    for skill_dir in "$CODEX_SOURCE"/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            ((codex_source_count+=1))
            local skill_name=$(basename "$skill_dir")
            if [[ -f "$CODEX_TARGET/skills/$skill_name/SKILL.md" ]]; then
                ((codex_synced_count+=1))
            fi

            local home_agent_file="$CODEX_TARGET/agents/$skill_name.toml"
            if [[ -f "$home_agent_file" ]]; then
                ((codex_home_agent_total+=1))
                if ! grep -qE '^(model|model_reasoning_effort) =' "$home_agent_file"; then
                    ((codex_home_agent_inheriting+=1))
                fi
            fi
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

    if [[ -f "$CODEX_TARGET/config.toml" ]] && grep -q "^\[agents\.memory-status-reporter\]" "$CODEX_TARGET/config.toml" && config_has_required_memory_status_lines "$CODEX_TARGET/config.toml"; then
        echo "  memory-status-reporter config: synced"
    elif [[ -f "$CODEX_TARGET/config.toml" ]]; then
        echo "  memory-status-reporter config: partial"
    else
        echo "  memory-status-reporter config: missing"
    fi

    if [[ $codex_home_agent_total -gt 0 ]]; then
        echo "  agent inheritance: $codex_home_agent_inheriting/$codex_home_agent_total"
    else
        echo "  agent inheritance: 0/0"
    fi

    echo ""
    print_info "MD5 Verification:"
    show_checksum_status
    echo ""
}

# Main script
show_usage() {
    echo "Usage: $0 {menu|install|sync|codex|update|remove|verify|validate|status|all}"
    echo ""
    echo "Commands:"
    echo "  menu              - Open the interactive installer and management menu"
    echo "  install           - Validate, sync, version-stamp, and MD5-verify the skill pack"
    echo "  sync              - Alias for codex; force-sync and MD5-verify the skill pack"
    echo "  codex             - Sync Codex skills only, then MD5-verify the result"
    echo "  update            - Detect drift with MD5, sync only when needed, then verify"
    echo "  remove            - Remove the full repo-managed skill pack"
    echo "  remove <skill>    - Remove one installed skill by name"
    echo "  verify            - Verify the installed skill pack with MD5 checksums"
    echo "  verify <skill>    - Verify one installed skill with MD5 checksums"
    echo "  validate          - Validate all skills without syncing"
    echo "  status            - Show sync status, versions, and checksum drift"
    echo "  all               - Validate and sync Codex (default)"
    echo ""
    echo "Environment:"
    echo "  CODEX_TARGET_OVERRIDE=/custom/path/.codex  Override the Codex home target"
}

main() {
    echo ""
    print_info "Codex Skills Sync and Validation"
    echo ""

    case "${1:-}" in
        menu)
            run_interactive_menu
            ;;
        install)
            install_codex
            ;;
        sync)
            sync_codex
            ;;
        codex)
            sync_codex
            ;;
        update)
            update_codex
            ;;
        remove)
            if [[ -n "${2:-}" ]]; then
                remove_skill_installation "$2"
            else
                remove_skill_pack
            fi
            ;;
        verify)
            if [[ -n "${2:-}" ]]; then
                verify_skill_checksum "$2"
            else
                verify_pack_checksums
            fi
            ;;
        validate)
            validate_all
            ;;
        status)
            show_status
            ;;
        ""|all)
            validate_all
            if [[ $? -eq 0 ]]; then
                sync_codex
            else
                print_error "Validation failed, skipping sync"
                exit 1
            fi
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac

    echo ""
    print_success "Done!"
}

main "$@"
