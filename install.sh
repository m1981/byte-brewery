#!/bin/bash
set -e

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python venv and pipx on Ubuntu/Debian
install_prerequisites_debian() {
    echo "Installing Python prerequisites..."
    # Get Python version
    PY_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    
    # Install python3-venv for the specific version
    sudo apt-get update -y || true
    sudo apt-get install -y python${PY_VERSION}-venv python3-pip || {
        echo "Failed to install using apt. Trying alternative method..."
        python3 -m pip install --user virtualenv
    }
    
    # Install pipx
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    
    # Add to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
}

# Check and install prerequisites if needed
if ! command_exists pipx; then
    echo "pipx not found. Installing prerequisites..."
    if command_exists brew; then
        brew install pipx
        pipx ensurepath
    elif command_exists apt-get; then
        install_prerequisites_debian
    else
        python3 -m pip install --user virtualenv
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Verify pipx installation
    if ! command_exists pipx; then
        echo "Adding ~/.local/bin to PATH for current session..."
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Final verification
    if ! command_exists pipx; then
        echo "Error: Failed to install pipx. Please try manually:"
        echo "sudo apt-get install python3-venv python3-pip"
        echo "python3 -m pip install --user pipx"
        echo "python3 -m pipx ensurepath"
        exit 1
    fi
fi

# Install the package using pipx
echo "Installing byte-brewery using pipx..."
pipx install --force "git+https://github.com/m1981/byte-brewery.git@main"

# Get the installation directory
PACKAGE_DIR=$(pipx list --json | grep -o '"venv": "[^"]*"' | grep -m1 "byte-brewery" | cut -d'"' -f4)

if [ -z "$PACKAGE_DIR" ]; then
    echo "Error: Could not determine installation directory."
    exit 1
fi

# Create symlinks for all scripts in bin directory
echo "Setting up command-line tools..."
BIN_DIR="$PACKAGE_DIR/bin"
DEST_DIR="$HOME/.local/bin"
mkdir -p "$DEST_DIR"

# Ensure destination directory is in PATH
if [[ ":$PATH:" != *":$DEST_DIR:"* ]]; then
    echo "Adding $DEST_DIR to PATH in your profile..."
    if [ -f "$HOME/.bashrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo "Added to .bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
        echo "Added to .zshrc"
    else
        echo "Warning: Could not find .bashrc or .zshrc to update PATH"
        echo "Please add $DEST_DIR to your PATH manually"
    fi
fi

# Create symlinks for all executable files in bin
if [ -d "$BIN_DIR" ]; then
    for script in "$BIN_DIR"/*; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            script_name=$(basename "$script")
            ln -sf "$script" "$DEST_DIR/$script_name"
            echo "Linked $script_name"
        fi
    done
else
    echo "Warning: bin directory not found at $BIN_DIR"
fi

echo "Installation complete! All commands are now available."
echo "You may need to restart your terminal for the changes to take effect."
echo "You can run 'byte-help' to see available commands."

