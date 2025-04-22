#!/bin/bash
set -e  # Exit on error

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Check minimum Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.6" | bc -l) )); then
    echo "Error: Python 3.6 or higher is required"
    exit 1
fi

# Define installation directory
INSTALL_DIR="/usr/local/bin"
SHARE_DIR="/usr/local/share"
REPO_NAME="byte-brewery"
GITHUB_USER="m1981"
GITHUB_BRANCH="main"

echo "Installing byte-brewery tools..."

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Download repository
curl -L "https://github.com/$GITHUB_USER/$REPO_NAME/archive/$GITHUB_BRANCH.zip" -o "$REPO_NAME.zip"

# Unzip
unzip "$REPO_NAME.zip"

# Move to extracted directory
cd "$REPO_NAME-$GITHUB_BRANCH"

# Make scripts executable
chmod +x bin/*

# Create share directory and copy repository contents
sudo mkdir -p "$SHARE_DIR/$REPO_NAME"
sudo cp -R * "$SHARE_DIR/$REPO_NAME/"

# Install Python package
cd "$SHARE_DIR/$REPO_NAME"
if command -v pip3 &> /dev/null; then
    sudo pip3 install --no-cache-dir -e .
elif command -v pip &> /dev/null; then
    sudo pip install --no-cache-dir -e .
else
    echo "Error: pip not found. Please install Python and pip."
    exit 1
fi

# Create symbolic links for executables
cd "$INSTALL_DIR"
for tool in "$SHARE_DIR/$REPO_NAME/bin"/*; do
    if [ -f "$tool" ]; then
        sudo ln -sf "$tool" .
    fi
done

# Add completion if available
if [ -f "$SHARE_DIR/$REPO_NAME/completion/aug-completion.bash" ]; then
    sudo cp "$SHARE_DIR/$REPO_NAME/completion/aug-completion.bash" /etc/bash_completion.d/
fi

# Verify all required tools are available
for cmd in aug byte-help; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd installation failed"
        exit 1
    fi
done

# Clean up
cd ..
rm -rf "$TMP_DIR"

# Verify installation
if command -v aug &> /dev/null; then
    echo "Installation complete! byte-brewery tools are now available."
    echo "Try running 'byte-help' to see available tools."
else
    echo "Installation may have failed. Please check error messages above."
    exit 1
fi

