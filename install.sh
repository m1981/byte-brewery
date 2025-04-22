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

echo "Installation complete! 'aug' command is now available."
echo "You may need to restart your terminal for the changes to take effect."
echo "You can run 'aug --help' to see available commands."

