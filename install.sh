#!/bin/bash
set -e

REPO_URL="https://github.com/m1981/byte-brewery.git"
INSTALL_DIR="$HOME/.local/bin"

echo "🍺 Brewing byte-brewery installation..."
echo "🔍 DEBUG: Current directory is: $(pwd)"

# 1. Check for pipx
if ! command -v pipx &> /dev/null; then
    echo "❌ pipx is not installed."
    echo "   Please install it first (brew install pipx / sudo apt install pipx)"
    exit 1
fi

# 2. Determine Source (Local vs Remote)
# We check if pyproject.toml exists in the current folder.
if [ -f "pyproject.toml" ]; then
    echo "📂 DEBUG: Found pyproject.toml locally."
    echo "📂 Detected local source installation."
    SOURCE_DIR="."
    CLEANUP=false
else
    echo "🌐 DEBUG: No pyproject.toml found here."
    echo "🌐 Cloning repository from GitHub to temp folder..."
    SOURCE_DIR=$(mktemp -d)
    echo "🌐 DEBUG: Cloning to $SOURCE_DIR"

    # Clone quietly (-q) but show errors if it fails
    git clone -q "$REPO_URL" "$SOURCE_DIR"
    CLEANUP=true
fi

# 3. Install Python Tools via pipx
echo "📦 Installing Python tools via pipx..."
echo "📦 DEBUG: Running 'pipx install $SOURCE_DIR --force'"

# We install from the determined SOURCE_DIR
pipx install "$SOURCE_DIR" --force

# 4. Install Shell Scripts
echo "🐚 Installing shell scripts to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copy rsum from the source directory
if [ -f "$SOURCE_DIR/bin/rsum" ]; then
    cp "$SOURCE_DIR/bin/rsum" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/rsum"
    echo "🐚 DEBUG: Copied rsum"
else
    echo "⚠️  DEBUG: Could not find bin/rsum in $SOURCE_DIR"
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