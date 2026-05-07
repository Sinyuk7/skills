#!/usr/bin/env bash

# Skills Sync Script
# Purpose: Create symlinks for skills in the current directory to various agent directories
# Compatible with: Linux (best), macOS (Bash 3.2+, BSD tools), Windows Git Bash/WSL (with Developer Mode)
#
# Usage:
#   ./init.sh [OPTIONS]
#
# Options:
#   --claude        Sync to ~/.claude/skills
#   --codex         Sync to ~/.codex/skills
#   --agents        Sync to ~/.agents/skills (canonical user-level store)
#   --codemaker     Sync to ~/.codemaker/skills
#   --all           Sync to all known agent directories
#   --dry-run       Show what would be done without making changes
#   --force         Override conflicting SYMLINKS only (safe)
#   --force-all     Override including REAL DIRECTORIES (DESTRUCTIVE - will delete data!)
#   --refresh       Remove and recreate same-name entries before linking
#   --kill-stale    Terminate known CodeMaker/Qzhddr backend processes after sync
#   --skill <name>  Sync only the specified skill (can be repeated). REQUIRED.
#   --help          Show this help message
#
# Without options, syncs to default agents: .agents, .claude, .codex, .codemaker
# A specific skill MUST be selected via --skill <name>; bulk/all-skill sync is disabled.
#
# Notes:
#   - Uses absolute paths for symlinks to avoid relative path resolution issues
#   - On Windows, symlink creation requires Developer Mode or admin privileges
#   - Skips conflicts by default; --force only overrides symlinks
#   - --force-all WILL DELETE real directories - use with extreme caution!

# ========================================
# Configuration
# ========================================

# Agent directory map (compatible with Bash 3.2+)
# Format: "agent_name:path" pairs
KNOWN_AGENTS=(
    "agents:.agents/skills"          # Canonical user-level store (Codex/open-agent-skills standard)
    "claude:.claude/skills"          # Claude Code
    "codex:.codex/skills"            # Codex
    "codemaker:.codemaker/skills"    # CodeMaker
    "cursor:.cursor/skills"          # Cursor
)

# Default agents to sync (if no --agent flags provided)
DEFAULT_AGENTS=("agents" "claude" "codex" "codemaker")

# Helper function to get agent path by name
get_agent_path() {
    local agent_name="$1"
    for entry in "${KNOWN_AGENTS[@]}"; do
        local name="${entry%%:*}"
        local path="${entry#*:}"
        if [[ "$name" == "$agent_name" ]]; then
            echo "$path"
            return 0
        fi
    done
    return 1
}

# Helper function to get all agent names
get_all_agent_names() {
    for entry in "${KNOWN_AGENTS[@]}"; do
        echo "${entry%%:*}"
    done
}

# Helper function to deduplicate and sort array
dedupe_array() {
    [[ $# -eq 0 ]] && return
    local -a arr=("$@")
    local -a result=()
    local -a seen=()
    
    for item in "${arr[@]}"; do
        local found=0
        if [[ ${#seen[@]} -gt 0 ]]; then
            for s in "${seen[@]}"; do
                if [[ "$s" == "$item" ]]; then
                    found=1
                    break
                fi
            done
        fi
        if [[ $found -eq 0 ]]; then
            result+=("$item")
            seen+=("$item")
        fi
    done
    
    [[ ${#result[@]} -gt 0 ]] && printf '%s\n' "${result[@]}"
}

# Enable strict mode AFTER helper functions are defined
set -euo pipefail

# ========================================
# Colors and Logging
# ========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_dry_run() {
    echo -e "${CYAN}[DRY-RUN]${NC} $1"
}

# ========================================
# Environment Detection
# ========================================

# Get user home directory in a cross-platform way
get_user_home() {
    # Prefer $HOME even on Windows Git Bash for consistency
    echo "${HOME}"
}

USER_HOME=$(get_user_home)

# Detect if running on Windows (for symlink warnings)
is_windows() {
    [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]
}

# ========================================
# Script Setup
# ========================================

# Get the absolute path of the current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/skills"

# Runtime flags
DRY_RUN=false
FORCE=false
FORCE_ALL=false
REFRESH=false
KILL_STALE=false
SELECTED_AGENTS=()
SELECTED_SKILLS=()

# ========================================
# Help
# ========================================

show_help() {
    cat << 'EOF'
Skills Sync Script

Syncs skill directories from ./skills to agent skill directories via symlinks.

USAGE:
    ./init.sh [OPTIONS]

OPTIONS:
    --claude        Sync to ~/.claude/skills
    --codex         Sync to ~/.codex/skills
    --agents        Sync to ~/.agents/skills (canonical store)
    --codemaker     Sync to ~/.codemaker/skills
    --cursor        Sync to ~/.cursor/skills
    --all           Sync to all known agent directories
    --dry-run       Show what would be done without making changes
    --force         Override conflicting SYMLINKS only (safe)
    --force-all     Override including REAL DIRECTORIES (DESTRUCTIVE!)
    --refresh       Remove and recreate same-name entries before linking
    --kill-stale    Terminate known CodeMaker/Qzhddr backend processes after sync
    --skill <name>  Sync only the specified skill (REQUIRED, can be repeated)
    --help          Show this help message

EXAMPLES:
    ./init.sh --skill issue-triage                   # Sync only issue-triage to default agents
    ./init.sh --skill issue-triage --skill mcp-builder
                                                     # Sync multiple specific skills
    ./init.sh --claude --codex --skill issue-triage  # Sync only issue-triage to Claude and Codex
    ./init.sh --all --skill issue-triage             # Sync issue-triage to all known agents
    ./init.sh --dry-run --skill issue-triage         # Preview what would be done
    ./init.sh --force --skill issue-triage           # Override conflicting symlinks
    ./init.sh --force-all --skill issue-triage       # Override everything (DANGER: deletes real directories!)
    ./init.sh --refresh --skill issue-triage         # Recreate managed entries even if already linked
    ./init.sh --refresh --kill-stale --skill issue-triage
                                                     # Recreate links, then restart stale CodeMaker backends

NOTES:
    - Uses absolute symlink paths to avoid resolution issues
    - On Windows, requires Developer Mode or admin privileges for symlinks
    - Skips conflicts by default
    - Sync updates files on disk only; it does NOT hot-reload already-activated skills
    - Some agents may cache skill content per session/thread and require a new chat or restart
    - --force only overrides symlinks (safe)
    - --force-all WILL DELETE real directories (use with extreme caution!)
    - --refresh touches only same-name managed skill entries under selected agent roots
    - --kill-stale only affects known CodeMaker/Qzhddr backend processes
    - --skill <name> is REQUIRED; the script refuses to sync all skills at once
    - Default agents: .agents (canonical), .claude, .codex, .codemaker

EOF
}

# ========================================
# Argument Parsing
# ========================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --force-all)
                FORCE_ALL=true
                FORCE=true  # force-all implies force
                shift
                ;;
            --refresh)
                REFRESH=true
                shift
                ;;
            --kill-stale)
                KILL_STALE=true
                shift
                ;;
            --all)
                # Get all agent names
                while IFS= read -r agent; do
                    SELECTED_AGENTS+=("$agent")
                done < <(get_all_agent_names)
                shift
                ;;
            --claude|--codex|--agents|--codemaker|--cursor)
                agent_name="${1#--}"
                if get_agent_path "$agent_name" > /dev/null 2>&1; then
                    SELECTED_AGENTS+=("$agent_name")
                else
                    log_error "Unknown agent: $agent_name"
                    exit 1
                fi
                shift
                ;;
            --skill)
                if [[ $# -lt 2 || -z "${2:-}" || "${2:0:2}" == "--" ]]; then
                    log_error "--skill requires a skill name argument"
                    exit 1
                fi
                SELECTED_SKILLS+=("$2")
                shift 2
                ;;
            --skill=*)
                skill_value="${1#--skill=}"
                if [[ -z "$skill_value" ]]; then
                    log_error "--skill requires a skill name argument"
                    exit 1
                fi
                SELECTED_SKILLS+=("$skill_value")
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Deduplicate and sort selected agents
    if [[ ${#SELECTED_AGENTS[@]} -gt 0 ]]; then
        local -a deduped=()
        while IFS= read -r agent; do
            [[ -n "$agent" ]] && deduped+=("$agent")
        done < <(dedupe_array "${SELECTED_AGENTS[@]}")
        if [[ ${#deduped[@]} -gt 0 ]]; then
            SELECTED_AGENTS=("${deduped[@]}")
        fi
    else
        # Use defaults if no agents selected
        SELECTED_AGENTS=("${DEFAULT_AGENTS[@]}")
    fi

    # A specific skill MUST be selected; bulk sync is intentionally disabled.
    if [[ ${#SELECTED_SKILLS[@]} -eq 0 ]]; then
        log_error "You must specify at least one skill via --skill <name>"
        echo "Use --help for usage information"
        exit 1
    fi

    # Deduplicate selected skills
    local -a skills_deduped=()
    while IFS= read -r s; do
        [[ -n "$s" ]] && skills_deduped+=("$s")
    done < <(dedupe_array "${SELECTED_SKILLS[@]}")
    if [[ ${#skills_deduped[@]} -gt 0 ]]; then
        SELECTED_SKILLS=("${skills_deduped[@]}")
    fi
}

has_selected_agent() {
    local wanted="$1"
    local agent_name

    for agent_name in "${SELECTED_AGENTS[@]}"; do
        if [[ "$agent_name" == "$wanted" ]]; then
            return 0
        fi
    done

    return 1
}

# ========================================
# Symlink Management
# ========================================

# Get the real path of a symlink target (cross-platform)
get_real_path() {
    local path="$1"
    # Try Python first (most portable)
    if command -v python3 > /dev/null 2>&1; then
        python3 -c "import os; print(os.path.realpath('$path'))" 2>/dev/null || echo "$path"
    elif command -v python > /dev/null 2>&1; then
        python -c "import os; print(os.path.realpath('$path'))" 2>/dev/null || echo "$path"
    elif command -v readlink > /dev/null 2>&1; then
        # Try readlink -f (GNU), fallback to just readlink
        readlink -f "$path" 2>/dev/null || readlink "$path" 2>/dev/null || echo "$path"
    else
        echo "$path"
    fi
}

# Create a symlink, handling conflicts based on flags
# Returns via global counters (to avoid set -e issues with return codes)
# Sets: RESULT_CREATED=1, RESULT_ALREADY_OK=1, RESULT_SKIPPED=1, or RESULT_FAILED=1
create_symlink() {
    local source="$1"
    local target="$2"
    local skill_name="$3"
    
    # Reset result flags
    RESULT_CREATED=0
    RESULT_ALREADY_OK=0
    RESULT_SKIPPED=0
    RESULT_FAILED=0
    
    # Check if target exists
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ "$REFRESH" == true ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                log_dry_run "Would refresh: $skill_name"
                RESULT_SKIPPED=1
                return
            fi

            if [[ -L "$target" ]]; then
                rm -f "$target"
            else
                rm -rf "$target"
            fi

            if ln -s "$source" "$target" 2>/dev/null; then
                log_success "Refreshed: $skill_name"
                RESULT_CREATED=1
            else
                log_error "Failed to refresh: $skill_name"
                RESULT_FAILED=1
            fi
            return
        fi

        # It's a symlink
        if [[ -L "$target" ]]; then
            local current_link
            current_link=$(readlink "$target" 2>/dev/null || echo "")
            
            # Try to compare real paths if possible
            local source_real
            local target_real
            source_real=$(get_real_path "$source")
            target_real=$(get_real_path "$target")
            
            if [[ "$current_link" == "$source" ]] || [[ "$source_real" == "$target_real" ]]; then
                if [[ "$DRY_RUN" == true ]]; then
                    log_dry_run "Already correct: $skill_name"
                else
                    log_info "Already OK: $skill_name"
                fi
                RESULT_ALREADY_OK=1
                return
            else
                if [[ "$FORCE" == true ]]; then
                    if [[ "$DRY_RUN" == true ]]; then
                        log_dry_run "Would recreate: $skill_name (currently: $current_link)"
                    else
                        rm -f "$target"
                        if ln -s "$source" "$target" 2>/dev/null; then
                            log_success "Recreated: $skill_name"
                            RESULT_CREATED=1
                        else
                            log_error "Failed to recreate: $skill_name"
                            if is_windows; then
                                log_warning "  Windows requires Developer Mode or admin privileges"
                            fi
                            RESULT_FAILED=1
                        fi
                    fi
                    return
                else
                    log_warning "Conflict (symlink): $skill_name -> $current_link (use --force)"
                    RESULT_SKIPPED=1
                    return
                fi
            fi
        # It's a real directory or file
        else
            if [[ "$FORCE_ALL" == true ]]; then
                if [[ "$DRY_RUN" == true ]]; then
                    log_dry_run "Would DELETE and replace: $skill_name (real directory/file)"
                else
                    log_warning "DELETING real directory: $skill_name"
                    rm -rf "$target"
                    if ln -s "$source" "$target" 2>/dev/null; then
                        log_success "Replaced: $skill_name"
                        RESULT_CREATED=1
                    else
                        log_error "Failed to replace: $skill_name"
                        RESULT_FAILED=1
                    fi
                fi
                return
            else
                log_warning "Conflict (real dir/file): $skill_name (use --force-all to DELETE)"
                RESULT_SKIPPED=1
                return
            fi
        fi
    fi
    
    # Target doesn't exist, create symlink
    if [[ "$DRY_RUN" == true ]]; then
        log_dry_run "Would create: $skill_name"
        RESULT_CREATED=1
    else
        if ln -s "$source" "$target" 2>/dev/null; then
            log_success "Created: $skill_name"
            RESULT_CREATED=1
        else
            log_error "Failed to create: $skill_name"
            if is_windows; then
                log_warning "  Windows requires Developer Mode or admin privileges"
            fi
            RESULT_FAILED=1
        fi
    fi
}

collect_pids_by_substring() {
    local needle="$1"

    ps ax -o pid= -o command= 2>/dev/null | awk -v needle="$needle" '{ cmd = substr($0, index($0, $2)); if (index(cmd, needle)) print $1 }'
}

kill_process_group_by_substring() {
    local label="$1"
    local needle="$2"
    local -a pids=()
    local pid

    while IFS= read -r pid; do
        [[ -n "$pid" ]] && pids+=("$pid")
    done < <(collect_pids_by_substring "$needle")

    if [[ ${#pids[@]} -eq 0 ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            log_dry_run "No $label processes found"
        else
            log_info "No $label processes found"
        fi
        return
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log_dry_run "Would terminate $label PID(s): ${pids[*]}"
        return
    fi

    log_warning "Terminating $label PID(s): ${pids[*]}"
    kill "${pids[@]}" 2>/dev/null || true
    sleep 1

    local -a stubborn=()
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            stubborn+=("$pid")
        fi
    done

    if [[ ${#stubborn[@]} -gt 0 ]]; then
        log_warning "Escalating to SIGKILL for $label PID(s): ${stubborn[*]}"
        kill -9 "${stubborn[@]}" 2>/dev/null || true
        sleep 1
    fi

    local -a survivors=()
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            survivors+=("$pid")
        fi
    done

    if [[ ${#survivors[@]} -eq 0 ]]; then
        log_success "Terminated $label"
    else
        log_warning "$label still running after restart attempt: ${survivors[*]}"
    fi
}

restart_stale_processes() {
    echo ""
    log_info "Refreshing stale backend processes"

    kill_process_group_by_substring "CodeMaker gateway" "codemaker.bin gateway"
    kill_process_group_by_substring "CodeMaker agent" "codemaker-agent-"
    kill_process_group_by_substring "QzhddrAgent" "QzhddrAgent"
    kill_process_group_by_substring "QzhddrSrv" "QzhddrSrv"
}

print_post_sync_notes() {
    if has_selected_agent "codemaker"; then
        echo ""
        log_warning "CodeMaker caveat:"
        echo "  - init.sh only syncs skill files on disk."
        echo "  - Already-activated skills can keep the old instruction snapshot for the current session/thread."
        if [[ "$KILL_STALE" == true ]]; then
            echo "  - Known CodeMaker/Qzhddr backends were restarted; reopen CodeMaker if it was running."
        else
            echo "  - Use --kill-stale if you want init.sh to restart known CodeMaker/Qzhddr backends."
            echo "  - Otherwise, start a new chat or restart CodeMaker after changing SKILL content."
        fi
        echo "  - Runtime cwd still comes from CodeMaker's active workspace/session, not from init.sh."
    fi
}

# ========================================
# Main Logic
# ========================================

main() {
    parse_args "$@"
    
    # Header
    echo ""
    log_info "======================================"
    log_info "Skills Sync Script"
    log_info "======================================"
    if [[ "$DRY_RUN" == true ]]; then
        log_dry_run "DRY-RUN mode (no changes will be made)"
    fi
    if [[ "$REFRESH" == true ]]; then
        log_warning "REFRESH mode (will recreate same-name managed entries)"
    elif [[ "$FORCE_ALL" == true ]]; then
        log_error "FORCE-ALL mode (WILL DELETE real directories!)"
    elif [[ "$FORCE" == true ]]; then
        log_warning "FORCE mode (will override conflicting symlinks)"
    fi
    if [[ "$KILL_STALE" == true ]]; then
        log_warning "KILL-STALE mode (will terminate known CodeMaker/Qzhddr backends)"
    fi
    echo ""
    log_info "User Home: $USER_HOME"
    log_info "Source: $SOURCE_DIR"
    log_info "Target Agents: ${SELECTED_AGENTS[*]}"
    log_info "Selected Skills: ${SELECTED_SKILLS[*]}"
    echo ""
    
    # Validate source directory
    if [[ ! -d "$SOURCE_DIR" ]]; then
        log_error "Source directory does not exist: $SOURCE_DIR"
        exit 1
    fi

    # Validate every requested skill exists in source dir (directory or symlink)
    local skills=()
    local missing_skills=()
    for skill_name in "${SELECTED_SKILLS[@]}"; do
        local skill_path="$SOURCE_DIR/$skill_name"
        if [[ -d "$skill_path" || -L "$skill_path" ]]; then
            skills+=("$skill_name")
        else
            missing_skills+=("$skill_name")
        fi
    done

    if [[ ${#missing_skills[@]} -gt 0 ]]; then
        log_error "The following requested skill(s) do not exist under $SOURCE_DIR:"
        for m in "${missing_skills[@]}"; do
            echo "  - $m"
        done
        exit 1
    fi
    
    if [[ ${#skills[@]} -eq 0 ]]; then
        log_warning "No skills resolved from --skill arguments"
        exit 0
    fi
    
    log_info "Syncing ${#skills[@]} skill(s):"
    for skill in "${skills[@]}"; do
        echo "  - $skill"
    done
    echo ""
    
    # Windows symlink warning
    if is_windows && [[ "$DRY_RUN" == false ]]; then
        log_warning "Windows detected: symlinks require Developer Mode or admin privileges"
        echo ""
    fi
    
    # Process each target agent
    local total_created=0
    local total_already_ok=0
    local total_skipped=0
    local total_failed=0
    
    for agent_name in "${SELECTED_AGENTS[@]}"; do
        local agent_path
        agent_path=$(get_agent_path "$agent_name")
        local target_base="$USER_HOME/$agent_path"
        
        log_info "Processing: $agent_name ($target_base)"
        
        # Create target directory if needed
        if [[ ! -d "$target_base" ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                log_dry_run "Would create directory: $target_base"
            else
                if mkdir -p "$target_base" 2>/dev/null; then
                    log_success "Created directory: $target_base"
                else
                    log_error "Failed to create directory: $target_base"
                    echo ""
                    continue
                fi
            fi
        fi
        
        # Sync each skill
        local created=0
        local already_ok=0
        local skipped=0
        local failed=0
        
        for skill in "${skills[@]}"; do
            local source_path="$SOURCE_DIR/$skill"
            local target_path="$target_base/$skill"
            
            # Call create_symlink - it sets RESULT_* globals to avoid set -e issues
            create_symlink "$source_path" "$target_path" "$skill"
            
            # Collect results from globals
            created=$((created + RESULT_CREATED))
            already_ok=$((already_ok + RESULT_ALREADY_OK))
            skipped=$((skipped + RESULT_SKIPPED))
            failed=$((failed + RESULT_FAILED))
        done
        
        # Summary for this agent
        echo ""
        log_info "Summary for $agent_name:"
        if [[ $created -gt 0 ]]; then
            log_success "  Created: $created"
        fi
        if [[ $already_ok -gt 0 ]]; then
            log_info "  Already OK: $already_ok"
        fi
        if [[ $skipped -gt 0 ]]; then
            log_warning "  Skipped: $skipped"
        fi
        if [[ $failed -gt 0 ]]; then
            log_error "  Failed: $failed"
        fi
        echo ""
        
        total_created=$((total_created + created))
        total_already_ok=$((total_already_ok + already_ok))
        total_skipped=$((total_skipped + skipped))
        total_failed=$((total_failed + failed))
    done
    
    # Final summary
    log_info "======================================"
    log_info "Overall Summary"
    log_info "======================================"
    if [[ $total_created -gt 0 ]]; then
        log_success "Created: $total_created"
    fi
    if [[ $total_already_ok -gt 0 ]]; then
        log_info "Already OK: $total_already_ok"
    fi
    if [[ $total_skipped -gt 0 ]]; then
        log_warning "Skipped: $total_skipped"
    fi
    if [[ $total_failed -gt 0 ]]; then
        log_error "Failed: $total_failed"
    fi
    echo ""
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "This was a dry-run. Run without --dry-run to apply changes."
    elif [[ $total_failed -eq 0 ]]; then
        if [[ "$KILL_STALE" == true ]]; then
            restart_stale_processes
        fi
        log_success "Sync completed successfully!"
        print_post_sync_notes
    else
        log_warning "Sync completed with some failures"
        exit 1
    fi
}

# Run main
main "$@"
