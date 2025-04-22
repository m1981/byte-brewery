#!/bin/bash
set -e  # Exit on error

# Function to compare version numbers
version_compare() {
    echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'
}

# Function to find Python executable
find_python() {
    local python_cmd=""
    local min_version="3.6.0"
    
    # Try different Python commands
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6; do
        if command -v "$cmd" &> /dev/null; then
            # Get version of this Python
            local version
            version=$("$cmd" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
            
            # Compare versions
            if [ "$(version_compare "$version")" -ge "$(version_compare "$min_version")" ]; then
                python_cmd="$cmd"
                break
            fi
        fi
    done

    if [ -z "$python_cmd" ]; then
        echo "Error: Python $min_version or higher is required"
        echo "Detected Python versions:"
        for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6; do
            if command -v "$cmd" &> /dev/null; then
                echo "$cmd: $("$cmd" --version 2>&1)"
            fi
        done
        exit 1
    fi

    # Export the found Python command
    echo "$python_cmd"
}

# Find suitable Python
PYTHON_CMD=$(find_python)
echo "Using Python: $($PYTHON_CMD --version)"

# Check pip installation
check_pip() {
    local pip_cmd=""
    
    # Try pip associated with the Python version
    if "$PYTHON_CMD" -m pip --version &> /dev/null; then
        pip_cmd="$PYTHON_CMD -m pip"
    elif command -v pip3 &> /dev/null; then
        pip_cmd="pip3"
    elif command -v pip &> /dev/null; then
        pip_cmd="pip"
    else
        echo "Error: pip not found. Attempting to install pip..."
        if command -v curl &> /dev/null; then
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            "$PYTHON_CMD" get-pip.py --user
            rm get-pip.py
            pip_cmd="$PYTHON_CMD -m pip"
        else
            echo "Error: curl not found. Please install pip manually."
            exit 1
        fi
    fi

    # Verify pip works
    if ! $pip_cmd --version &> /dev/null; then
        echo "Error: pip installation failed"
        exit 1
    fi

    echo "$pip_cmd"
}

# Find suitable pip
PIP_CMD=$(check_pip)
echo "Using pip: $($PIP_CMD --version)"

# Define installation directory
INSTALL_DIR="/usr/local/bin"
SHARE_DIR="/usr/local/share"
REPO_NAME="byte-brewery"
GITHUB_USER="m1981"
GITHUB_BRANCH="main"

echo "Installing byte-brewery tools..."

# Create temporary directory
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT  # Ensure cleanup on script exit

cd "$TMP_DIR"

# Download repository
if ! curl -L "https://github.com/$GITHUB_USER/$REPO_NAME/archive/$GITHUB_BRANCH.zip" -o "$REPO_NAME.zip"; then
    echo "Error: Failed to download repository"
    exit 1
fi

# Unzip with error checking
if ! unzip "$REPO_NAME.zip"; then
    echo "Error: Failed to extract repository"
    exit 1
fi

# Move to extracted directory
cd "$REPO_NAME-$GITHUB_BRANCH"

# Make scripts executable
chmod +x bin/*

# Create share directory and copy repository contents
sudo mkdir -p "$SHARE_DIR/$REPO_NAME"
sudo cp -R * "$SHARE_DIR/$REPO_NAME/"

# Install Python package
cd "$SHARE_DIR/$REPO_NAME"
if ! $PIP_CMD install --no-cache-dir -e .; then
    echo "Error: Failed to install Python package"
    exit 1
fi

# Create symbolic links for executables
cd "$INSTALL_DIR"
for tool in "$SHARE_DIR/$REPO_NAME/bin"/*; do
    if [ -f "$tool" ]; then
        sudo ln -sf "$tool" .
    fi
done

# Add completion support
COMPLETION_DIRS=("/etc/bash_completion.d" "/usr/local/etc/bash_completion.d" "$HOME/.local/share/bash-completion/completions")
COMPLETION_INSTALLED=false

for completion_dir in "${COMPLETION_DIRS[@]}"; do
    if [ -d "$completion_dir" ]; then
        # Create directory if it doesn't exist (for user directory)
        if [[ "$completion_dir" == "$HOME"* ]]; then
            mkdir -p "$completion_dir"
        fi
        
        if [[ "$completion_dir" == "$HOME"* ]]; then
            cp "$SHARE_DIR/$REPO_NAME/completion/aug-completion.bash" "$completion_dir/aug"
        else
            sudo cp "$SHARE_DIR/$REPO_NAME/completion/aug-completion.bash" "$completion_dir/aug"
        fi
        COMPLETION_INSTALLED=true
        echo "Bash completion installed in $completion_dir"
        break
    fi
done

if [ "$COMPLETION_INSTALLED" = false ]; then
    echo "Warning: Could not install bash completion. Supported directories not found."
fi

# Verify all required tools are available
for cmd in aug byte-help; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd installation failed"
        exit 1
    fi
done

# Verify installation
if command -v aug &> /dev/null; then
    echo "Installation complete! byte-brewery tools are now available."
    echo "Try running 'byte-help' to see available tools."
    if [ "$COMPLETION_INSTALLED" = true ]; then
        echo "Bash completion installed. Restart your shell or run: source ~/.bashrc"
    fi
else
    echo "Installation may have failed. Please check error messages above."
    exit 1
fi

