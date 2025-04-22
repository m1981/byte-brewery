#!/bin/bash

# Define installation directory
INSTALL_DIR="/usr/local/bin"
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

# Copy executables to installation directory
sudo cp bin/* "$INSTALL_DIR/"

# Clean up
cd ..
rm -rf "$TMP_DIR"

echo "Installation complete! byte-brewery tools are now available."

