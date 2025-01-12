#!/bin/bash

if [ -z "$1" ]; then
    echo "Error: Please provide a directory path"
    echo "Usage: $0 <directory_path>"
    exit 1
fi

if [ ! -d "$1" ]; then
    echo "Error: '$1' is not a valid directory"
    exit 1
fi

process_file() {
    local file="$1"
    echo "📁 Analyzing: $file"
    echo "=================================================="
    echo "Imports:"
    grep -E "^import .*" "$file" | sed 's/ as .*//g' | awk '!seen[$NF]++' | sort -u
    echo -e "\nTypes and Interfaces:"
    grep -E "^(export )?(interface|type) [A-Z]" "$file"
    echo -e "\nHook Definitions:"
    grep -E "^const use[A-Z][a-zA-Z]* = .*=>" "$file"
    echo -e "\nReact Hooks Usage:"
    grep -E "  const .* = (useState|useEffect|useRef|useCallback|useMemo)" "$file" | sort | uniq
    echo -e "\nCustom Hooks Usage:"
    grep -E "  const .* = use[A-Z][a-zA-Z]*" "$file" | grep -v "useState\|useStore" | awk '!seen[$0]++' | sort
    echo -e "\nStore Selectors:"
    grep -E "  const .* = useStore\(.*\);" "$file" | grep -v "set[A-Z]" | sort | uniq
    echo -e "\nStore Actions:"
    grep -E "  const .* = useStore\(.*\);" "$file" | grep "set[A-Z]" | sort | uniq
    echo -e "\nStore State Access:"
    grep -E "\.getState\(\)" "$file" | sort | uniq
    echo -e "\nExported Items:"
    grep -E "^export (const|default|function)" "$file"
    echo -e "\nComponent Definitions:"
    grep -E "^const [A-Z][a-zA-Z]* = (React\.memo\(|React\.forwardRef\(|\([^)]*\).*=>)" "$file"
    echo -e "\n\n"
}

echo "🔮 Ultimate File Analysis Magic V11 - FINAL PERFECTION ✨"
echo "=================================================="

# Find all .ts and .tsx files and process them
find "$1" -type f \( -name "*.tsffff" -o -name "*.tsxx" \) -not -path "*/node_modules/*" | while read -r file; do
    process_file "$file"
done
