#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Boilerplate — Project Setup
#
# Usage (curl):
#   bash <(curl -sSL https://raw.githubusercontent.com/johnOfGod33/fastapi-boilerplate/main/setup.sh)
#
# Usage (local):
#   bash setup.sh --local
#   bash setup.sh --local --name my-api --dest ~/projects/my-api
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BOILERPLATE_REPO="https://github.com/johnOfGod33/fastapi-boilerplate.git"

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD='\033[1m'
RESET='\033[0m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
DIM='\033[2m'

# ── Helpers ───────────────────────────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}┌──────────────────────────────────────┐${RESET}"
    echo -e "${BLUE}${BOLD}│   FastAPI Boilerplate — New Project   │${RESET}"
    echo -e "${BLUE}${BOLD}└──────────────────────────────────────┘${RESET}"
    echo ""
}

print_done() {
    local name="$1" dest="$2"
    echo ""
    echo -e "${GREEN}${BOLD}┌──────────────────────────────────────┐${RESET}"
    echo -e "${GREEN}${BOLD}│   Project ready!                      │${RESET}"
    echo -e "${GREEN}${BOLD}└──────────────────────────────────────┘${RESET}"
    echo ""
    echo -e "  ${BOLD}Name    :${RESET} $name"
    echo -e "  ${BOLD}Location:${RESET} $dest"
    echo ""
    echo -e "  ${CYAN}cd $dest${RESET}"
    echo -e "  ${CYAN}make install && make run-dev${RESET}"
    echo ""
}

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
info() { echo -e "  ${BLUE}→${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} $1"; }
die()  { echo -e "  ${RED}✗${RESET} $1" >&2; exit 1; }

# Read from /dev/tty so the script works with both `curl | bash` and direct run
ask() {
    local __var="$1" __prompt="$2" __default="${3:-}"
    local __display_default=""

    [ -n "$__default" ] && __display_default=" [${__default}]"
    printf "  ${CYAN}%s${RESET}%s: " "$__prompt" "$__display_default" >/dev/tty

    local __value
    read -r __value </dev/tty
    [ -z "$__value" ] && __value="$__default"
    printf -v "$__var" '%s' "$__value"
}

# ask_choice VAR "Prompt" "value1" "Label 1" "value2" "Label 2" ...
ask_choice() {
    local __var="$1" __prompt="$2"
    shift 2
    local __options=("$@")
    local __count=$(( ${#__options[@]} / 2 ))

    printf "  ${CYAN}%s${RESET}\n" "$__prompt" >/dev/tty
    local i=1 j=0
    while [ $j -lt ${#__options[@]} ]; do
        printf "    ${DIM}%d)${RESET} %s\n" "$i" "${__options[$((j+1))]}" >/dev/tty
        i=$((i+1)); j=$((j+2))
    done

    local __answer
    while true; do
        printf "  ${CYAN}Choice [1-%d]:${RESET} " "$__count" >/dev/tty
        read -r __answer </dev/tty
        if [[ "$__answer" =~ ^[0-9]+$ ]] && [ "$__answer" -ge 1 ] && [ "$__answer" -le "$__count" ]; then
            local __idx=$(( (__answer - 1) * 2 ))
            printf -v "$__var" '%s' "${__options[$__idx]}"
            return
        fi
        warn "Please enter a number between 1 and $__count."
    done
}

ask_yn() {
    local __prompt="$1" __default="${2:-n}"
    local __hint="y/N"
    [ "$__default" = "y" ] && __hint="Y/n"

    printf "  ${YELLOW}%s${RESET} [%s]: " "$__prompt" "$__hint" >/dev/tty
    local __answer
    read -r __answer </dev/tty
    [ -z "$__answer" ] && __answer="$__default"
    [[ "$__answer" =~ ^[Yy]$ ]]
}

slugify() {
    echo "$1" \
        | tr '[:upper:]' '[:lower:]' \
        | sed 's/[^a-z0-9]/-/g' \
        | sed 's/-\+/-/g' \
        | sed 's/^-//;s/-$//'
}

gen_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null \
        || openssl rand -hex 32 2>/dev/null \
        || LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c 64
}

expand_path() {
    echo "${1/#\~/$HOME}"
}

# ── Argument parsing ──────────────────────────────────────────────────────────
ARG_NAME=""
ARG_DEST=""
LOCAL_MODE="false"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name|-n)  ARG_NAME="$2"; shift 2 ;;
        --dest|-d)  ARG_DEST="$2"; shift 2 ;;
        --local|-l) LOCAL_MODE="true"; shift ;;
        --help|-h)
            echo "Usage: bash setup.sh [--name NAME] [--dest DEST] [--local]"
            echo ""
            echo "  --local, -l   Copy local directory instead of cloning from GitHub"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ── Checks ────────────────────────────────────────────────────────────────────
command -v git >/dev/null 2>&1 || die "git is required but not installed."

# ── Interactive prompts ───────────────────────────────────────────────────────
print_header

# Project name
if [ -n "$ARG_NAME" ]; then
    PROJECT_NAME="$ARG_NAME"
else
    ask PROJECT_NAME "Project name"
fi
while [ -z "$PROJECT_NAME" ]; do
    warn "Project name cannot be empty."
    ask PROJECT_NAME "Project name"
done

PROJECT_SLUG=$(slugify "$PROJECT_NAME")

# Description
ask PROJECT_DESCRIPTION "Description" "A FastAPI backend for ${PROJECT_NAME}"

# Destination
if [ -n "$ARG_DEST" ]; then
    DEST="$ARG_DEST"
else
    ask DEST "Destination" "$HOME/Desktop/Projects/$PROJECT_SLUG"
fi
DEST=$(expand_path "$DEST")

# Git platform
echo ""
ask_choice GIT_PLATFORM "Git platform" \
    "github" "GitHub" \
    "gitlab" "GitLab" \
    "none"   "None (no CI files)"

# MkDocs
echo ""
USE_MKDOCS="n"
ask_yn "Include MkDocs documentation?" "y" && USE_MKDOCS="y" || true

# ── Overwrite guard ───────────────────────────────────────────────────────────
if [ -d "$DEST" ]; then
    echo ""
    if ! ask_yn "Directory $DEST already exists. Overwrite?" "n"; then
        echo "Aborted."
        exit 0
    fi
    rm -rf "$DEST"
fi

# ── Clone / copy boilerplate ──────────────────────────────────────────────────
echo ""
if [ "$LOCAL_MODE" = "true" ]; then
    info "Copying local boilerplate from $SCRIPT_DIR..."
    rsync -a \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='.env.dev' \
        --exclude='setup.sh' \
        "$SCRIPT_DIR/" "$DEST/"
    ok "Boilerplate copied (local)"
else
    info "Cloning boilerplate..."
    git clone --depth 1 --quiet "$BOILERPLATE_REPO" "$DEST" \
        || die "Failed to clone $BOILERPLATE_REPO"
    rm -rf "$DEST/.git"
    rm -f  "$DEST/setup.sh"
    ok "Boilerplate cloned"
fi

# ── CI files ──────────────────────────────────────────────────────────────────
case "$GIT_PLATFORM" in
    github)
        rm -rf "$DEST/.gitlab" "$DEST/.gitlab-ci.yml"
        ok "GitLab CI files removed (GitHub selected)"
        ;;
    gitlab)
        rm -rf "$DEST/.github"
        ok "GitHub Actions files removed (GitLab selected)"
        ;;
    none)
        rm -rf "$DEST/.github" "$DEST/.gitlab" "$DEST/.gitlab-ci.yml"
        ok "CI files removed"
        ;;
esac

# ── MkDocs ────────────────────────────────────────────────────────────────────
if [ "$USE_MKDOCS" = "y" ]; then
    if [ -f "$DEST/mkdocs.yml" ]; then
        sed -i \
            -e "s|{{project_name}}|${PROJECT_NAME}|g" \
            -e "s|{{project_description}}|${PROJECT_DESCRIPTION}|g" \
            "$DEST/mkdocs.yml"
    fi
    for f in "$DEST/docs/"*.md; do
        [ -f "$f" ] || continue
        sed -i \
            -e "s|{{project_name}}|${PROJECT_NAME}|g" \
            -e "s|{{project_description}}|${PROJECT_DESCRIPTION}|g" \
            "$f"
    done
    ok "MkDocs configured"
else
    rm -f  "$DEST/mkdocs.yml"
    rm -rf "$DEST/docs"
    ok "MkDocs files removed"
fi

# ── README ────────────────────────────────────────────────────────────────────
if [ -f "$DEST/README.template.md" ]; then
    sed \
        -e "s|{{project_name}}|${PROJECT_NAME}|g" \
        -e "s|{{project_description}}|${PROJECT_DESCRIPTION}|g" \
        "$DEST/README.template.md" > "$DEST/README.md"
    rm -f "$DEST/README.template.md"
    ok "README.md generated"
fi

# ── .env.dev ──────────────────────────────────────────────────────────────────
if [ -f "$DEST/.env.example" ]; then
    echo ""
    echo -e "  ${CYAN}${BOLD}Configure .env.dev${RESET}  ${DIM}(Enter to keep default)${RESET}"
    echo ""

    rm -f "$DEST/.env.dev"

    while IFS= read -r line || [ -n "$line" ]; do
        if [[ -z "$line" || "$line" == \#* ]]; then
            echo "$line" >> "$DEST/.env.dev"
            continue
        fi
        if [[ "$line" != *"="* ]]; then
            echo "$line" >> "$DEST/.env.dev"
            continue
        fi

        KEY="${line%%=*}"
        VALUE="${line#*=}"

        if [ "$KEY" = "MONGODB_DB_NAME" ] && [ -z "$VALUE" ]; then
            VALUE="$PROJECT_SLUG"
        fi

        if [ "$KEY" = "JWT_SECRET" ] && [ -z "$VALUE" ]; then
            VALUE=$(gen_secret)
            echo -e "    ${CYAN}${KEY}${RESET}: ${DIM}auto-generated${RESET}" >/dev/tty
            echo "$KEY=$VALUE" >> "$DEST/.env.dev"
            continue
        fi

        ask ENV_VALUE "  ${KEY}" "$VALUE"
        echo "$KEY=$ENV_VALUE" >> "$DEST/.env.dev"

    done < "$DEST/.env.example"

    ok ".env.dev created"
fi

# ── Git init ──────────────────────────────────────────────────────────────────
echo ""
info "Initializing git repository..."
git -C "$DEST" init --quiet
git -C "$DEST" add .
git -C "$DEST" commit --quiet -m "chore: initial commit from boilerplate"
ok "Git repository initialized"

# ── Done ──────────────────────────────────────────────────────────────────────
print_done "$PROJECT_NAME" "$DEST"
