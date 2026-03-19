#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERSION=$(grep '^version' "$PROJECT_ROOT/pyproject.toml" | head -1 | sed 's/version = "\(.*\)"/\1/')

cd "$PROJECT_ROOT"
SCHT_VERSION="$VERSION" pyinstaller .build/pyinstaller.spec --distpath dist --workpath .build/work --noconfirm
