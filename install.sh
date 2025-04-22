#!/bin/bash

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
    sudo pip3 install -e .
elif command -v pip &> /dev/null; then
    sudo pip install -e .
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

