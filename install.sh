#!/bin/bash
set -e

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python dependencies
install_python_deps() {
    echo "Installing Python dependencies..."
    if command_exists pip3; then
        pip3 install --user -r requirements.txt
    else
        echo "Error: pip3 not found. Please install Python3 and pip."
        exit 1
    fi
}

# Create installation directory
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Clone the repository to a temporary location
TMP_DIR=$(mktemp -d)
echo "Cloning repository to $TMP_DIR..."
git clone https://github.com/m1981/byte-brewery.git "$TMP_DIR"

# Install Python dependencies if any exist
if [ -f "$TMP_DIR/requirements.txt" ]; then
    install_python_deps
fi

# Copy all scripts to installation directory
echo "Installing scripts to $INSTALL_DIR..."
cp "$TMP_DIR/bin/"* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR"/*

# Add installation directory to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
    echo "Added $INSTALL_DIR to PATH in .bashrc and .zshrc"
fi

# Clean up
rm -rf "$TMP_DIR"

echo "Installation complete! All tools are now available."
echo "You may need to restart your terminal or run 'source ~/.bashrc' for the changes to take effect."
echo "Available tools: $(ls -1 $INSTALL_DIR | tr '\n' ' ')"


