#!/usr/bin/env sh
set -e

SCRIPT_DIR=$(dirname "$0")
INSTALL_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/scht" "$INSTALL_DIR/scht"
chmod +x "$INSTALL_DIR/scht"

echo "scht installed to $INSTALL_DIR/scht"
echo "Add $INSTALL_DIR to your PATH if it is not already there."
