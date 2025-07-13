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

# Function to install Python package
install_python_package() {
    echo "Installing Python package..."
    cd "$TMP_DIR"
    
    # Try with --user flag first
    if pip3 install --user . >/dev/null 2>&1; then
        echo "Package installed successfully."
    # If that fails, try with break-system-packages
    elif pip3 install --user --break-system-packages . >/dev/null 2>&1; then
        echo "Package installed with --break-system-packages flag."
    # If both fail, create a virtual environment
    else
        echo "Creating virtual environment for byte-brewery..."
        VENV_DIR="$HOME/.local/venvs/byte-brewery"
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        pip3 install .
        deactivate
        
        # Create wrapper scripts that activate the venv before running
        for script in "$INSTALL_DIR"/aug*; do
            if [ -f "$script" ]; then
                mv "$script" "${script}.original"
                cat > "$script" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
"${script}.original" "\$@"
deactivate
EOF
                chmod +x "$script"
            fi
        done
        echo "Package installed in virtual environment at $VENV_DIR"
    fi
    
    cd - > /dev/null
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

# Install the Python package
install_python_package

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


