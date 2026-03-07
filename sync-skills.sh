#!/bin/bash

# Sync and Validate Script for Codex and Claude Skills
# This script syncs skills to their respective global directories and validates them

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
CLAUDE_SOURCE="$SCRIPT_DIR/claude"

# Detect OS and set target directories
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash)
    CODEX_TARGET="$HOME/.codex"
    CLAUDE_TARGET="$HOME/.claude/skills"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CODEX_TARGET="$HOME/.codex"
    CLAUDE_TARGET="$HOME/.claude/skills"
else
    # Linux
    CODEX_TARGET="$HOME/.codex"
    CLAUDE_TARGET="$HOME/.claude/skills"
fi

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

    # Codex skills should not carry Claude Code metadata.
    if grep -q "^allowed-tools:" "$skill_dir/SKILL.md"; then
        print_error "Codex skill contains Claude-only 'allowed-tools' field: $skill_name"
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

    if ! grep -qi "keep at most one live same-role agent by default" "$skill_dir/SKILL.md" || ! grep -q "fork_context" "$skill_dir/SKILL.md"; then
        print_error "Codex SKILL.md must require same-role agent reuse and fork_context default-off: $skill_name"
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

    # Enforce separation: Codex skills should not reference Claude Code docs.
    local banned_regex='docs\.anthropic\.com|Claude[[:space:]]+Code|Anthropic'
    if grep -RInE "$banned_regex" "$skill_dir" --include="*.md" > /dev/null 2>&1; then
        print_error "Claude-only references found in Codex skill: $skill_name"
        grep -RInE "$banned_regex" "$skill_dir" --include="*.md" | head -n 20
        return 1
    fi

    return 0
}

validate_codex_agent_config() {
    local skill_name=$1
    local config_file=$2
    local expected_reasoning=""

    case "$skill_name" in
        backend-and-data-architecture|cloud-and-devops-expert|mobile-development-life-cycle|qa-and-automation-engineer|web-development-life-cycle)
            expected_reasoning="high"
            ;;
        git-expert|ui-design-systems-and-responsive-interfaces)
            expected_reasoning="high"
            ;;
        reviewer|security-and-compliance-auditor|software-development-life-cycle|ux-research-and-experience-strategy)
            expected_reasoning="xhigh"
            ;;
        *)
            print_error "No Codex model policy defined for skill: $skill_name"
            return 1
            ;;
    esac

    if grep -q "^model:" "$config_file"; then
        print_error "Codex skill config should not pin model; rely on workspace default GPT-5.4: $skill_name"
        return 1
    fi

    if ! grep -q "^reasoning_effort: \"$expected_reasoning\"$" "$config_file"; then
        print_error "Unexpected reasoning_effort for Codex skill $skill_name (expected $expected_reasoning)"
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

    if ! grep -q "keep at most one live same-role agent by default" "$config_file" || ! grep -q "fork_context off unless the exact parent thread history is required" "$config_file"; then
        print_error "Codex agent prompt must require same-role agent reuse and fork_context default-off: $skill_name"
        return 1
    fi

    if ! grep -q "maintain a lightweight spawned-agent list" "$config_file" || ! grep -q "send a robust handoff covering the exact objective" "$config_file"; then
        print_error "Codex agent prompt must require spawned-agent tracking and robust delegation packets: $skill_name"
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

        if ! grep -qi "robust handoff packet" "$file"; then
            print_error "Missing robust sub-agent handoff policy in AGENTS.md"
            return 1
        fi
    fi

    return 0
}

validate_codex_repo_docs() {
    local failed=0
    local guidance_files=(
        "$CODEX_SOURCE/AGENTS.md"
        "$CODEX_SOURCE/00-skill-routing-and-escalation.md"
        "$CODEX_SOURCE/README.md"
        "$CODEX_SOURCE/VALIDATION_REPORT.md"
    )

    print_info "Validating Codex guidance files..."

    for guidance_file in "${guidance_files[@]}"; do
        if ! validate_codex_guidance_file "$guidance_file"; then
            ((failed+=1))
        fi
    done

    if [[ $failed -ne 0 ]]; then
        print_error "$failed Codex guidance file(s) failed validation"
        return 1
    fi

    print_success "Codex guidance files validated"
    return 0
}

# Validate a Claude skill directory for Claude-specific requirements and separation.
validate_claude_skill_dir() {
    local skill_dir=$1
    local skill_name=$(basename "$skill_dir")

    if ! validate_skill "$skill_dir/SKILL.md"; then
        return 1
    fi

    # Claude Code skills should declare allowed-tools so the agent can pick the right capabilities.
    if ! grep -q "^allowed-tools:" "$skill_dir/SKILL.md"; then
        print_error "Missing required Claude 'allowed-tools' field in: $skill_name"
        return 1
    fi

    # Claude Code does not use Codex agents configs.
    if [[ -d "$skill_dir/agents" ]]; then
        print_error "Claude skill contains Codex-only agents/ directory: $skill_name"
        return 1
    fi

    # Claude mirrors must retain their supporting reference material.
    if [[ ! -d "$skill_dir/references" ]]; then
        print_error "Missing references/ directory for Claude skill: $skill_name"
        return 1
    fi

    # Enforce separation: Claude skills must not include Codex-only operational guidance or links.
    local banned_regex='developers\.openai\.com/codex|github\.com/openai/skills|OpenAI[[:space:]]+Codex|js_repl|spawn_agent|codex\.tool|config\.toml|(^|[^[:alnum:]_])codex([^[:alnum:]_]|$)'
    if grep -RInEi "$banned_regex" "$skill_dir" --include="*.md" > /dev/null 2>&1; then
        print_error "Codex-only references found in Claude skill: $skill_name"
        grep -RInEi "$banned_regex" "$skill_dir" --include="*.md" | head -n 20
        return 1
    fi

    return 0
}

# Function to sync Codex skills
sync_codex() {
    print_info "Syncing Codex skills..."

    # Create target directory if it doesn't exist
    mkdir -p "$CODEX_TARGET"
    mkdir -p "$CODEX_TARGET/skills"

    if ! validate_codex_repo_docs; then
        print_error "Codex guidance validation failed, aborting Codex sync"
        return 1
    fi

    # Enforce environment separation: remove any Claude-only skill that may have been synced into Codex previously.
    if [[ -d "$CODEX_TARGET/skills/claude-api" ]]; then
        print_warning "Removing Claude-only skill from Codex target: claude-api"
        rm -rf "$CODEX_TARGET/skills/claude-api"
    fi
    if [[ -d "$CODEX_TARGET/claude-api" ]]; then
        print_warning "Removing legacy Claude-only skill from Codex target root: claude-api"
        rm -rf "$CODEX_TARGET/claude-api"
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
        # Skip claude directory
        if [[ "$(basename "$skill_dir")" == "claude" ]]; then
            continue
        fi

        skill_name=$(basename "$skill_dir")

        # Skip if not a skill directory (no SKILL.md)
        if [[ ! -f "$skill_dir/SKILL.md" ]]; then
            continue
        fi

        print_info "Syncing $skill_name..."

        # Validate skill
        if ! validate_codex_skill_dir "$skill_dir"; then
            print_error "Validation failed for $skill_name, skipping..."
            continue
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

        # Copy SKILL.md
        cp "$skill_dir/SKILL.md" "$CODEX_TARGET/skills/$skill_name/SKILL.md"

        # Copy references directory if exists
        if [[ -d "$skill_dir/references" ]]; then
            mkdir -p "$CODEX_TARGET/skills/$skill_name/references"
            cp -r "$skill_dir/references/." "$CODEX_TARGET/skills/$skill_name/references/"
        fi

        # Copy agents configuration if exists (Codex CLI uses agents/openai.yaml)
        if [[ -d "$skill_dir/agents" ]]; then
            mkdir -p "$CODEX_TARGET/skills/$skill_name/agents"
            cp -r "$skill_dir/agents/." "$CODEX_TARGET/skills/$skill_name/agents/"
        fi

        print_success "Synced $skill_name to Codex"
    done

    print_success "Codex skills sync complete!"
}

# Function to sync Claude skills
sync_claude() {
    print_info "Syncing Claude skills..."

    # Check if Claude source directory exists
    if [[ ! -d "$CLAUDE_SOURCE" ]]; then
        print_warning "Claude source directory not found, creating..."
        mkdir -p "$CLAUDE_SOURCE"
    fi

    # Create target directory if it doesn't exist
    mkdir -p "$CLAUDE_TARGET"

    # Check if Claude skills exist
    if [[ ! "$(ls -A "$CLAUDE_SOURCE")" ]]; then
        print_warning "No Claude skills found in $CLAUDE_SOURCE"
        print_info "Claude skills should be created separately from Codex skills"
        return 0
    fi

    # Sync each skill directory
    for skill_dir in "$CLAUDE_SOURCE"/*/; do
        skill_name=$(basename "$skill_dir")

        # Skip if not a skill directory (no SKILL.md)
        if [[ ! -f "$skill_dir/SKILL.md" ]]; then
            continue
        fi

        print_info "Syncing $skill_name to Claude..."

        # Validate skill
        if ! validate_claude_skill_dir "$skill_dir"; then
            print_error "Validation failed for $skill_name, skipping..."
            continue
        fi

        # Refresh target to the latest: remove prior sync to prevent stale files.
        if [[ -d "$CLAUDE_TARGET/$skill_name" ]]; then
            rm -rf "$CLAUDE_TARGET/$skill_name"
        fi

        # Create target skill directory
        mkdir -p "$CLAUDE_TARGET/$skill_name"

        # Copy SKILL.md
        cp "$skill_dir/SKILL.md" "$CLAUDE_TARGET/$skill_name/SKILL.md"

        # Copy references directory if exists
        if [[ -d "$skill_dir/references" ]]; then
            mkdir -p "$CLAUDE_TARGET/$skill_name/references"
            cp -r "$skill_dir/references/." "$CLAUDE_TARGET/$skill_name/references/"
        fi

        # Copy examples directory if exists
        if [[ -d "$skill_dir/examples" ]]; then
            mkdir -p "$CLAUDE_TARGET/$skill_name/examples"
            cp -r "$skill_dir/examples/." "$CLAUDE_TARGET/$skill_name/examples/"
        fi

        # Copy scripts directory if exists
        if [[ -d "$skill_dir/scripts" ]]; then
            mkdir -p "$CLAUDE_TARGET/$skill_name/scripts"
            cp -r "$skill_dir/scripts/." "$CLAUDE_TARGET/$skill_name/scripts/"
        fi

        # Copy template.md if exists
        if [[ -f "$skill_dir/template.md" ]]; then
            cp "$skill_dir/template.md" "$CLAUDE_TARGET/$skill_name/template.md"
        fi

        print_success "Synced $skill_name to Claude"
    done

    print_success "Claude skills sync complete!"
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
        # Skip claude directory
        if [[ "$(basename "$skill_dir")" == "claude" ]]; then
            continue
        fi

        if [[ -f "$skill_dir/SKILL.md" ]]; then
            if ! validate_codex_skill_dir "$skill_dir"; then
                ((failed+=1))
            fi
        fi
    done

    # Validate Claude skills
    if [[ -d "$CLAUDE_SOURCE" ]]; then
        print_info "Validating Claude skills..."
        for skill_dir in "$CLAUDE_SOURCE"/*/; do
            if [[ -f "$skill_dir/SKILL.md" ]]; then
                if ! validate_claude_skill_dir "$skill_dir"; then
                    ((failed+=1))
                fi
            fi
        done
    fi

    if [[ $failed -eq 0 ]]; then
        print_success "All skills validated successfully!"
        return 0
    else
        print_error "$failed skill(s) failed validation"
        return 1
    fi
}

# Function to show status
show_status() {
    print_info "Skill Sync Status"
    echo ""

    print_info "Codex Skills:"
    echo "  Source: $CODEX_SOURCE"
    echo "  Target: $CODEX_TARGET/skills"

    local codex_source_count=0
    local codex_synced_count=0
    for skill_dir in "$CODEX_SOURCE"/*/; do
        if [[ "$(basename "$skill_dir")" == "claude" ]]; then
            continue
        fi
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            ((codex_source_count+=1))
            local skill_name=$(basename "$skill_dir")
            if [[ -f "$CODEX_TARGET/skills/$skill_name/SKILL.md" ]]; then
                ((codex_synced_count+=1))
            fi
        fi
    done

    if [[ -d "$CODEX_TARGET/skills" ]]; then
        echo "  Synced skills: $codex_synced_count/$codex_source_count"
    else
        echo "  Synced skills: 0/$codex_source_count (target directory not found)"
    fi

    echo ""
    print_info "Claude Skills:"
    echo "  Source: $CLAUDE_SOURCE"
    echo "  Target: $CLAUDE_TARGET"

    local claude_source_count=0
    local claude_synced_count=0
    if [[ -d "$CLAUDE_SOURCE" ]]; then
        for skill_dir in "$CLAUDE_SOURCE"/*/; do
            if [[ -f "$skill_dir/SKILL.md" ]]; then
                ((claude_source_count+=1))
                local skill_name=$(basename "$skill_dir")
                if [[ -f "$CLAUDE_TARGET/$skill_name/SKILL.md" ]]; then
                    ((claude_synced_count+=1))
                fi
            fi
        done
    fi

    if [[ -d "$CLAUDE_TARGET" ]]; then
        echo "  Synced skills: $claude_synced_count/$claude_source_count"
    else
        echo "  Synced skills: 0/$claude_source_count (target directory not found)"
    fi

    echo ""
}

# Main script
main() {
    echo ""
    print_info "Codex & Claude Skills Sync and Validation"
    echo ""

    case "${1:-}" in
        codex)
            sync_codex
            ;;
        claude)
            sync_claude
            ;;
        validate)
            validate_all
            ;;
        status)
            show_status
            ;;
        all|"")
            validate_all
            if [[ $? -eq 0 ]]; then
                sync_codex
                sync_claude
            else
                print_error "Validation failed, skipping sync"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 {codex|claude|validate|status|all}"
            echo ""
            echo "Commands:"
            echo "  codex     - Sync Codex skills only"
            echo "  claude    - Sync Claude skills only"
            echo "  validate  - Validate all skills without syncing"
            echo "  status    - Show sync status"
            echo "  all       - Validate and sync both (default)"
            exit 1
            ;;
    esac

    echo ""
    print_success "Done!"
}

main "$@"
