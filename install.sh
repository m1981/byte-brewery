#!/bin/bash
set -e

echo "🍺 Brewing byte-brewery installation..."

# 1. Check for pipx (The modern way to run python tools)
if ! command -v pipx &> /dev/null; then
    echo "❌ pipx is not installed."
    echo "   Please install it first:"
    echo "   - Mac: brew install pipx"
    echo "   - Linux: sudo apt install pipx (or pip install --user pipx)"
    echo "   Then run: pipx ensurepath"
    exit 1
fi

# 2. Install the Python Package using pipx
# This reads pyproject.toml, installs dependencies, and creates the 'aug' command
echo "📦 Installing Python tools via pipx..."
pipx install . --force

# 3. Install Shell Scripts (The only manual part)
# We only copy non-python scripts now
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

echo "🐚 Installing shell scripts to $INSTALL_DIR..."

# Copy rsum and ensure it's executable
if [ -f "bin/rsum" ]; then
    cp "bin/rsum" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/rsum"
fi

# Add to path if missing (Standard check)
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  $INSTALL_DIR is not in your PATH."
    echo "   Add this to your shell config: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo "✅ Installation complete! Run 'aug --help' to test."