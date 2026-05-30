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

# ── 2. Install Python packages as uv tools ──────────────────────────────────
# Each package gets its own isolated virtualenv managed by uv.
# --editable means edits to source files take effect immediately without reinstall.
echo "📦 Installing Python packages as uv tools..."

UV_PACKAGES=(
    "packages/aireview"
    "packages/augment_ai"
    "packages/prompt_extractor"
    "packages/utils"
    "packages/svelte_mapper"
)

for pkg in "${UV_PACKAGES[@]}"; do
    pkg_path="$REPO_DIR/$pkg"
    pkg_name=$(basename "$pkg")
    echo "   → Installing $pkg_name..."
    uv tool install --editable "$pkg_path" --force
done

# ── 3. Install shell scripts to ~/.local/bin ────────────────────────────────
# Pure bash scripts that need no Python environment.
echo "🐚 Installing shell scripts to $BIN_DIR..."
mkdir -p "$BIN_DIR"

SHELL_SCRIPTS=("rsum" "byte-help")

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

# ── 4. Install tools.json manifest (used by byte-help) ─────────────────────
cp "$REPO_DIR/bin/tools.json" "$BIN_DIR/tools.json"
echo "   → Installed: tools.json"

# ── 5. Install standalone scripts from bin/ ─────────────────────────────────
# Scripts that have no package home yet (e.g. thin wrappers, shell utilities).
# NOTE: pysum and lsproj are NOT here — they are installed via uv tool (Step 2)
#       as proper entry points in packages/utils.
echo "🔧 Installing standalone scripts..."

STANDALONE_SCRIPTS=("mdcat" "export-chats" "git-recent")

for file in "${STANDALONE_SCRIPTS[@]}"; do
    src="$REPO_DIR/bin/$file"
    if [ -f "$src" ]; then
        cp "$src" "$BIN_DIR/"
        chmod +x "$BIN_DIR/$file"
        echo "   → Installed: $file"
    else
        echo "   ⚠️  Warning: bin/$file not found, skipping."
    fi
done

# ── 6. Install Node.js tooling (summarize.ts etc.) ─────────────────────────
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

# ── 7. PATH check ───────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "⚠️  ${BIN_DIR} is not in your PATH."
    echo "   Add this to your ~/.zshrc:"
    echo "   export PATH=\"${BIN_DIR}:\$PATH\""
fi

# ── 8. Summary ──────────────────────────────────────────────────────────────
echo ""
echo "✅ Installation complete!"
echo ""
echo "💡 Run 'byte-help' to see all installed tools."
echo "   Run 'byte-help --sources' to see which package provides each tool."
echo "   To update after code changes: just edit — --editable installs reflect changes immediately."
echo "   To reinstall from scratch:    ./install.sh"
