#!/usr/bin/env bash
# Build production-ready plugin ZIP (same logic as release workflow).
# Usage: run from repository root. Output: rank-math-api-manager.zip
set -e

PLUGIN_DIR="rank-math-api-manager"
ZIP_NAME="rank-math-api-manager.zip"

rm -rf "$PLUGIN_DIR" "$ZIP_NAME"

mkdir -p "$PLUGIN_DIR"

# Copy core plugin files
cp rank-math-api-manager.php "$PLUGIN_DIR/"

# Copy includes directory if exists
if [ -d "includes" ]; then
  cp -r includes/ "$PLUGIN_DIR/"
fi

# Copy assets directory if exists (preserve assets/ so plugin URLs like assets/images/ work)
if [ -d "assets" ]; then
  cp -r assets "$PLUGIN_DIR/"
fi

# Copy essential documentation
[ -f "README.md" ] && cp README.md "$PLUGIN_DIR/"
[ -f "LICENSE" ] && cp LICENSE "$PLUGIN_DIR/"
[ -f "LICENSE.md" ] && cp LICENSE.md "$PLUGIN_DIR/"
[ -f "CHANGELOG.md" ] && cp CHANGELOG.md "$PLUGIN_DIR/"
[ -f "changelog.txt" ] && cp changelog.txt "$PLUGIN_DIR/"
[ -f "readme.txt" ] && cp readme.txt "$PLUGIN_DIR/"

# Remove development-only files
rm -rf "$PLUGIN_DIR/.git"* 2>/dev/null || true
rm -rf "$PLUGIN_DIR/.github/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/tests/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/.cursor/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/agent-skills/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/transcripts/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/agent-transcripts/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/local-notes/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/.notes/" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/node_modules/" 2>/dev/null || true
find "$PLUGIN_DIR" -name '.DS_Store' -type f -delete 2>/dev/null || true
rm -f "$PLUGIN_DIR/assets/images/icon-proof.html" 2>/dev/null || true
rm -f "$PLUGIN_DIR/assets/images/icon-direction-"*.svg 2>/dev/null || true
rm -f "$PLUGIN_DIR/TODO"*.md 2>/dev/null || true
rm -f "$PLUGIN_DIR/.env"* 2>/dev/null || true
rm -f "$PLUGIN_DIR/.gitignore" 2>/dev/null || true
rm -f "$PLUGIN_DIR/"*.code-workspace 2>/dev/null || true

zip -r "$ZIP_NAME" "$PLUGIN_DIR/"

echo "Created $ZIP_NAME"
