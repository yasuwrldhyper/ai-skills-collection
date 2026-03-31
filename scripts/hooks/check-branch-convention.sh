#!/usr/bin/env bash
# Claude Code PreToolUse hook: validate branch naming convention
# Reads tool call JSON from stdin; blocks if branch name violates .branch-strategy.json
#
# Exit codes:
#   0 - allow (no violation or not a branch-creation command)
#   2 - block (convention violation)

set -euo pipefail

# Read the full hook payload
PAYLOAD=$(cat)

# Extract the bash command from the tool input
COMMAND=$(echo "$PAYLOAD" | jq -r '.tool_input.command // empty')

# Exit 0 if no command (shouldn't happen, but be defensive)
[ -z "$COMMAND" ] && exit 0

# Extract branch name from branch-creation commands:
#   git checkout -b <name>
#   git checkout -b <name> <base>
#   git switch -c <name>
#   git branch <name>
#   git branch <name> <base>
BRANCH=""
if echo "$COMMAND" | grep -qE 'git (checkout|switch) -[cCb]'; then
  BRANCH=$(echo "$COMMAND" | sed -E 's/.*git (checkout|switch) -[cCb][[:space:]]+([^[:space:]]+).*/\2/')
elif echo "$COMMAND" | grep -qE '^git branch [^-]'; then
  BRANCH=$(echo "$COMMAND" | sed -E 's/.*git branch[[:space:]]+([^[:space:]]+).*/\1/')
fi

# Exit 0 if this is not a branch-creation command
[ -z "$BRANCH" ] && exit 0

# Find .branch-strategy.json at project root or up to 5 levels up
PROJECT_ROOT=""
DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
if [ -f "$DIR/.branch-strategy.json" ]; then
  PROJECT_ROOT="$DIR"
else
  CHECK="$DIR"
  for _ in 1 2 3 4 5; do
    CHECK=$(dirname "$CHECK")
    if [ -f "$CHECK/.branch-strategy.json" ]; then
      PROJECT_ROOT="$CHECK"
      break
    fi
  done
fi

# Exit 0 if no config found (convention not configured for this project)
[ -z "$PROJECT_ROOT" ] && exit 0

CONFIG="$PROJECT_ROOT/.branch-strategy.json"
PATTERN=$(jq -r '.branchPattern // empty' "$CONFIG")
MAX_LEN=$(jq -r '.maxBranchNameLength // 60' "$CONFIG")

# Protected branches are always allowed
while IFS= read -r pb; do
  [ "$BRANCH" = "$pb" ] && exit 0
done < <(jq -r '.protectedBranches[]?' "$CONFIG")

# environmentBranches are also exempt from the naming convention
while IFS= read -r eb; do
  [ "$BRANCH" = "$eb" ] && exit 0
done < <(jq -r '.environmentBranches[]?' "$CONFIG")

# Exit 0 if no pattern configured
[ -z "$PATTERN" ] && exit 0

# Validate length
if [ "${#BRANCH}" -gt "$MAX_LEN" ]; then
  echo "Branch name too long: '$BRANCH' (${#BRANCH} chars, max $MAX_LEN)" >&2
  echo "Tip: shorten the description part after the prefix" >&2
  exit 2
fi

# Validate pattern
if ! echo "$BRANCH" | grep -qE "$PATTERN"; then
  # Build a helpful example from configured prefixes
  FIRST_PREFIX=$(jq -r '.branchPrefixes | to_entries[0] | .value' "$CONFIG" 2>/dev/null || echo "feat/")
  echo "Branch name '$BRANCH' violates the convention for this project." >&2
  echo "Required pattern: $PATTERN" >&2
  echo "Example valid name: ${FIRST_PREFIX}your-description" >&2
  echo "Run '/branch-strategy show' to see the full naming convention." >&2
  exit 2
fi

exit 0
