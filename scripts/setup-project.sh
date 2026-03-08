#!/usr/bin/env bash
set -euo pipefail

PRESET="${1:-p1-ja}"
REPO="yasuwrldhyper/ai-skills-collection"
VALID_PRESETS=("p1-ja" "p1-en" "must-ja" "must-en")

# Validate preset
valid=false
for p in "${VALID_PRESETS[@]}"; do
  [[ "$PRESET" == "$p" ]] && valid=true && break
done
if [[ "$valid" == "false" ]]; then
  echo "Error: Unknown preset '${PRESET}'"
  echo "Available presets: ${VALID_PRESETS[*]}"
  exit 1
fi

echo "==> Installing skills from ${REPO}..."

# Install 3 skills
for skill in worktree-implement resolve-pr-reviews review-comment-convention; do
  echo "    Installing ${skill}..."
  npx skills add "${REPO}@${skill}" -y 2>/dev/null || {
    echo "    Warning: Failed to install ${skill}. Continuing..."
  }
done

echo "==> Applying review convention (preset: ${PRESET})..."

# Download template
TEMPLATE_URL="https://raw.githubusercontent.com/${REPO}/main/templates/review-convention/${PRESET}.md"
CONVENTION=$(curl -fsSL "$TEMPLATE_URL") || {
  echo "Error: Failed to download template from ${TEMPLATE_URL}"
  exit 1
}

# Write to .github/copilot-instructions.md
mkdir -p .github
if [[ -f .github/copilot-instructions.md ]]; then
  if grep -q "## Code Review Comment Convention\|## コードレビューコメント規約" .github/copilot-instructions.md 2>/dev/null; then
    echo "    .github/copilot-instructions.md already has convention section (skipped)"
  else
    printf '\n%s\n' "$CONVENTION" >> .github/copilot-instructions.md
    echo "    Appended to .github/copilot-instructions.md"
  fi
else
  printf '# Copilot Instructions\n\n%s\n' "$CONVENTION" > .github/copilot-instructions.md
  echo "    Created .github/copilot-instructions.md"
fi

# Write to CLAUDE.md if exists
if [[ -f CLAUDE.md ]]; then
  if grep -q "## Code Review Comment Convention\|## コードレビューコメント規約" CLAUDE.md 2>/dev/null; then
    echo "    CLAUDE.md already has convention section (skipped)"
  else
    printf '\n%s\n' "$CONVENTION" >> CLAUDE.md
    echo "    Appended to CLAUDE.md"
  fi
else
  echo "    CLAUDE.md not found (skipped)"
fi

echo ""
echo "Done! Installed skills:"
echo "  - /worktree-implement"
echo "  - /resolve-pr-reviews"
echo "  - /review-comment-convention"
echo ""
echo "Convention preset: ${PRESET}"
echo "To customize: /review-comment-convention setup"
