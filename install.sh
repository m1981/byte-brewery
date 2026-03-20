#!/bin/bash
set -e

REPO_URL="https://github.com/m1981/byte-brewery.git"
# Use pipx's default bin location if available, otherwise fallback to ~/.local/bin
INSTALL_DIR="${PIPX_BIN_DIR:-$HOME/.local/bin}"
FILES_TO_COPY=("rsum" "byte-help" "tools.json" "lsproj")

echo "🍺 Brewing byte-brewery installation..."

# 1. Check for pipx
if ! command -v pipx &> /dev/null; then
    echo "❌ pipx is not installed."
    echo "   MacOS: brew install pipx"
    exit 1
fi

# 2. Determine Source (Local vs Remote)
# We check if pyproject.toml exists AND if it belongs to byte-brewery.
IS_LOCAL_SOURCE=false

if [ -f "pyproject.toml" ]; then
    # Grep for the package name to ensure we aren't in a random python project
    if grep -q 'name = "byte-brewery"' pyproject.toml || grep -q "name = 'byte-brewery'" pyproject.toml; then
        IS_LOCAL_SOURCE=true
    else
        echo "⚠️  DEBUG: Found pyproject.toml, but it belongs to another project."
    fi
fi

if [ "$IS_LOCAL_SOURCE" = true ]; then
    echo "📂 DEBUG: Verified local byte-brewery source."
    SOURCE_DIR="."
    CLEANUP=false
else
    echo "🌐 DEBUG: Downloading fresh copy from GitHub..."
    SOURCE_DIR=$(mktemp -d)
    echo "🌐 DEBUG: Cloning to $SOURCE_DIR"

    # Clone quietly (-q) but show errors if it fails
    git clone -q "$REPO_URL" "$SOURCE_DIR"
    CLEANUP=true
fi

# 3. Install Python Tools
echo "📦 Installing Python package..."
# Ensure we install dependencies defined in pyproject.toml
pipx install "$SOURCE_DIR" --force --pip-args="--no-cache-dir"

# 4. Install Shell Scripts (The Hybrid Part)
echo "🐚 Installing shell scripts to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# ADD "lsproj" HERE 👇
FILES_TO_COPY=("rsum" "byte-help" "tools.json" "lsproj" "summarize.ts")

for file in "${FILES_TO_COPY[@]}"; do
    if [ -f "$SOURCE_DIR/bin/$file" ]; then
        cp "$SOURCE_DIR/bin/$file" "$INSTALL_DIR/"

        # Only make scripts executable, not the json
        if [[ "$file" != *.json ]]; then
            chmod +x "$INSTALL_DIR/$file"
        fi
        echo "   - Installed: $file"
    else
        echo "⚠️  Warning: bin/$file not found in source."
    fi
done

# Install Node.js dependencies for TypeScript scripts
if [ -f "$SOURCE_DIR/bin/package.json" ]; then
    echo "📦 Installing Node.js dependencies for TypeScript tools..."
    cp "$SOURCE_DIR/bin/package.json" "$INSTALL_DIR/"
    if [ -d "$SOURCE_DIR/bin/node_modules" ]; then
        cp -r "$SOURCE_DIR/bin/node_modules" "$INSTALL_DIR/"
        echo "   - Installed: node_modules"
    else
        # Install dependencies if node_modules doesn't exist
        if command -v npm &> /dev/null; then
            npm install --prefix "$INSTALL_DIR" --silent
            echo "   - Installed: node_modules (via npm)"
        fi
    fi
fi



# 5. Cleanup (Only if we cloned)
if [ "$CLEANUP" = true ]; then
    rm -rf "$SOURCE_DIR"
fi

# 6. Path Validation (Crucial for macOS)
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  WARNING: $INSTALL_DIR is not in your PATH."
    echo "   Add this to ~/.zshrc or ~/.bash_profile:"
    echo "   export PATH=\"$INSTALL_DIR:\$PATH\""
fi

echo "✅ Installation complete!"