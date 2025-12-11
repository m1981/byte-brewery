#!/bin/bash
set -e

REPO_URL="https://github.com/m1981/byte-brewery.git"
INSTALL_DIR="$HOME/.local/bin"

echo "🍺 Brewing byte-brewery installation..."

# 1. Check for pipx
if ! command -v pipx &> /dev/null; then
    echo "❌ pipx is not installed."
    echo "   Please install it first:"
    echo "   - Mac: brew install pipx"
    echo "   - Linux: sudo apt install pipx"
    echo "   Then run: pipx ensurepath"
    exit 1
fi

# 2. Determine Source (Local vs Remote)
# If pyproject.toml exists here, we use the current folder.
# If not, we clone the repo to a temp folder.
if [ -f "pyproject.toml" ]; then
    echo "📂 Detected local source installation."
    SOURCE_DIR="."
    CLEANUP=false
else
    echo "🌐 Cloning repository from GitHub..."
    SOURCE_DIR=$(mktemp -d)
    git clone -q "$REPO_URL" "$SOURCE_DIR"
    CLEANUP=true
fi

# 3. Install Python Tools via pipx
echo "📦 Installing Python tools via pipx..."
# We install from SOURCE_DIR
pipx install "$SOURCE_DIR" --force

# 4. Install Shell Scripts
echo "🐚 Installing shell scripts to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copy rsum from the source directory
if [ -f "$SOURCE_DIR/bin/rsum" ]; then
    cp "$SOURCE_DIR/bin/rsum" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/rsum"
fi

# 5. Cleanup (Only if we cloned)
if [ "$CLEANUP" = true ]; then
    echo "🧹 Cleaning up temp files..."
    rm -rf "$SOURCE_DIR"
fi

# 6. Path Check
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  $INSTALL_DIR is not in your PATH."
    echo "   Add this to your shell config: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo "✅ Installation complete! Run 'aug --help' to test."