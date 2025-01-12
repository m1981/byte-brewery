#!/bin/bash
echo "🔮 Ultimate File Analysis Magic V11 - FINAL PERFECTION ✨"
echo "=================================================="
echo "Imports:"
grep -E "^import .*" "$1" | sed 's/ as .*//g' | awk '!seen[$NF]++' | sort -u
echo -e "\nTypes and Interfaces:"
grep -E "^(export )?(interface|type) [A-Z]" "$1"
echo -e "\nHook Definitions:"
grep -E "^const use[A-Z][a-zA-Z]* = .*=>" "$1"
echo -e "\nReact Hooks Usage:"
grep -E "  const .* = (useState|useEffect|useRef|useCallback|useMemo)" "$1" | sort | uniq
echo -e "\nCustom Hooks Usage:"
grep -E "  const .* = use[A-Z][a-zA-Z]*" "$1" | grep -v "useState\|useStore" | awk '!seen[$0]++' | sort
echo -e "\nStore Selectors:"
grep -E "  const .* = useStore\(.*\);" "$1" | grep -v "set[A-Z]" | sort | uniq
echo -e "\nStore Actions:"
grep -E "  const .* = useStore\(.*\);" "$1" | grep "set[A-Z]" | sort | uniq
echo -e "\nStore State Access:"
grep -E "\.getState\(\)" "$1" | sort | uniq
echo -e "\nExported Items:"
grep -E "^export (const|default|function)" "$1"
echo -e "\nComponent Definitions:"
grep -E "^const [A-Z][a-zA-Z]* = (React\.memo\(|React\.forwardRef\(|\([^)]*\).*=>)" "$1"
