#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo "🍺 Brewing byte-brewery installation..."

# ── 1. Check for uv ────────────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed."
    echo "   Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# ── 2. Install Python packages as uv tools (replaces pipx) ─────────────────
echo "📦 Installing Python packages as uv tools..."

UV_PACKAGES=(
    "packages/aireview"
    "packages/augment_ai"
    "packages/prompt_extractor"
    "packages/utils"
)

for pkg in "${UV_PACKAGES[@]}"; do
    pkg_path="$REPO_DIR/$pkg"
    pkg_name=$(basename "$pkg")
    echo "   → Installing $pkg_name..."
    # --editable: local code changes take effect immediately, no reinstall needed
    uv tool install --editable "$pkg_path" --force
done

# ── 3. Install shell scripts to ~/.local/bin ────────────────────────────────
echo "🐚 Installing shell scripts to $BIN_DIR..."
mkdir -p "$BIN_DIR"

SHELL_SCRIPTS=("rsum" "byte-help" "lsproj")

for file in "${SHELL_SCRIPTS[@]}"; do
    src="$REPO_DIR/bin/$file"
    if [ -f "$src" ]; then
        cp "$src" "$BIN_DIR/"
        chmod +x "$BIN_DIR/$file"
        echo "   → Installed: $file"
    else
        echo "   ⚠️  Warning: bin/$file not found, skipping."
    fi
done

# ── 4. Install Node.js tooling (summarize.ts etc.) ─────────────────────────
if [ -f "$REPO_DIR/bin/package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    cp "$REPO_DIR/bin/package.json" "$BIN_DIR/"

    if [ -d "$REPO_DIR/bin/node_modules" ]; then
        cp -r "$REPO_DIR/bin/node_modules" "$BIN_DIR/"
        echo "   → Copied node_modules"
    elif command -v npm &> /dev/null; then
        npm install --prefix "$BIN_DIR" --silent
        echo "   → Installed node_modules via npm"
    else
        echo "   ⚠️  npm not found, skipping Node.js dependencies."
    fi

    # Copy TypeScript scripts
    for ts_file in "$REPO_DIR/bin/"*.ts; do
        [ -f "$ts_file" ] && cp "$ts_file" "$BIN_DIR/" && echo "   → Installed: $(basename "$ts_file")"
    done
fi

# ── 5. PATH check ───────────────────────────────────────────────────────────
UV_TOOLS_BIN="${HOME}/.local/bin"  # uv tool installs here by default

if [[ ":$PATH:" != *":$UV_TOOLS_BIN:"* ]]; then
    echo ""
    echo "⚠️  ${UV_TOOLS_BIN} is not in your PATH."
    echo "   Add this to your ~/.zshrc:"
    echo "   export PATH=\"${UV_TOOLS_BIN}:\$PATH\""
fi

# ── 6. Summary ──────────────────────────────────────────────────────────────
echo ""
echo "✅ Installation complete!"
echo ""
echo "🔧 Installed CLI tools:"
echo "   Python (via uv tool): aireview, aug, aug-recap, dce, pext, chatmap, repo-map, gen-diagram"
echo "   Shell scripts:        rsum, byte-help, lsproj"
echo ""
echo "💡 To update after code changes: just edit — --editable installs reflect changes immediately."
echo "   To reinstall from scratch:    ./install.sh"
echo "   To list installed uv tools:   uv tool list"