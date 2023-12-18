#!/bin/bash

set -euo pipefail

# Function to safely handle each file
handle_file() {
    local file="$1"
    # Echo the filename, then the code block start marker to stdout
    echo "File: $file"
    echo '```'
    # Echo the contents of the current file to stdout
    cat "$file"
    # Echo the code block end marker to stdout
    echo '```'
    # Add a newline for spacing between files entries
    echo -e "\n"
}

# Check if any arguments were passed
if [ "$#" -eq 0 ]; then
    echo "No files specified. Usage: $0 file1 [file2 ...] > output.md" >&2
    echo ""
    echo "Concatenate one or more files into Markdown format and print to stdout." >&2
    echo "To write to a file, redirect stdout to a file using the > operator." >&2
    exit 1
fi

# Iterate over the positional parameters
for file in "$@"; do
    # Check if file exists and is a regular file
    if [ -f "$file" ]; then
        handle_file "$file"
    else
        echo "Warning: File $file does not exist or is not a regular file. Skipping." >&2
    fi
done

echo "Concatenation complete." >&2
