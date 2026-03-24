#!/usr/bin/env bash
set -euo pipefail

REPO="abrahambahez/scholartools"
LANG="en"
UNINSTALL=false

DOCS_DIR=$(xdg-user-dir DOCUMENTS 2>/dev/null || true)
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-${DOCS_DIR:-$HOME/Documents}}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG="$2"; shift 2 ;;
    --uninstall) UNINSTALL=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if $UNINSTALL; then
  rm -f "$SKILLS_DIR"/scholartools-*-"$LANG"-*.zip
  echo "Uninstalled scholartools skills from $SKILLS_DIR"
  exit 0
fi

RELEASE=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest")
ASSET_URLS=$(echo "$RELEASE" | grep -o '"browser_download_url": "[^"]*scholartools-[^"]*-'"$LANG"'-[^"]*\.zip"' | grep -o 'https://[^"]*')

if [ -z "$ASSET_URLS" ]; then
  echo "Error: no skills assets found for language '$LANG'" >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"

while IFS= read -r url; do
  filename=$(basename "$url")
  curl -fsSL -o "$SKILLS_DIR/$filename" "$url"
  echo "Downloaded: $filename → $SKILLS_DIR"
done <<< "$ASSET_URLS"
