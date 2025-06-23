  #!/bin/bash

process_file() {
    local file="$1"
    local relative_file=$(basename "$file")

    echo "$file"

    #  Imporrt s (typically at the top)
    local imports=$(grep -E "^import .*" "$file" | sed 's/ as .*//g' | sort)
    if [ ! -z "$imports" ]; then
        echo "Imports:"
        echo "$imports"
    fi

    # Types and Interfaces (usually after imports)
    local types=$(grep -E "^(export )?(interface|type) [A-Z]" "$file")
    if [ ! -z "$types" ]; then
        echo "Types and Interfaces:"
        echo "$types"
    fi

    # For test files, check test setup first
    if [[ "$file" == *".test."* || "$file" == *".spec."* ]]; then
        # Vitest Mocks (usually set up early)
        local mocks=$(grep -E "vi\.(mock|fn|spyOn)" "$file" | sort | uniq)
        if [ ! -z "$mocks" ]; then
            echo "Mocks:"
            echo "$mocks"
        fi

        # Test Environment Setup
        local test_env=$(grep -E "(vi\.useFakeTimers|vi\.useRealTimers)" "$file" | sort | uniq)
        if [ ! -z "$test_env" ]; then
            echo "Test Environment Setup:"
            echo "$test_env"
        fi

        # Vitest Hooks (usually at the beginning of test files)
        local test_hooks=$(grep -E "^[[:space:]]*(beforeAll|afterAll|beforeEach|afterEach)\(" "$file" | sort | uniq)
        if [ ! -z "$test_hooks" ]; then
            echo "Test Hooks:"
            echo "$test_hooks"
        fi

        # Vitest Test Suites
        local test_suites=$(grep -E "^describe\(.*" "$file")
        if [ ! -z "$test_suites" ]; then
            echo "Test Suites:"
            echo "$test_suites"
        fi

        # Vitest Test Cases
        local test_cases=$(grep -E "^[[:space:]]*(test|it)\(.*" "$file")
        if [ ! -z "$test_cases" ]; then
            echo "Test Cases:"
            echo "$test_cases"
        fi

        # Testing Library Utilities - exclude import statements
        local test_utils=$(grep -E "(render|screen|fireEvent|waitFor|within)" "$file" | grep -v "^import" | sort | uniq)
        if [ ! -z "$test_utils" ]; then
            echo "Testing Library Usage:"
            echo "$test_utils"
        fi

        # Vitest Assertions
        local assertions=$(grep -E "expect\(.*\)\.(to|not)\." "$file" | sort | uniq)
        if [ ! -z "$assertions" ]; then
            echo "Assertions:"
            echo "$assertions"
        fi

        # Snapshot Testing
        local snapshots=$(grep -E "toMatchSnapshot|toMatchInlineSnapshot" "$file" | sort | uniq)
        if [ ! -z "$snapshots" ]; then
            echo "Snapshot Tests:"
            echo "$snapshots"
        fi
    else
        # For React component files
        # Hook Definitions (usually before components)
        local hook_defs=$(grep -E "^const use[A-Z][a-zA-Z]* = .*=>" "$file")
        if [ ! -z "$hook_defs" ]; then
            echo "Custom Hook Definitions:"
            echo "$hook_defs"
        fi

        # Component Definitions
        local components=$(grep -E "^const [A-Z][a-zA-Z]* = (React\.memo\(|React\.forwardRef\(|\([^)]*\).*=>)" "$file")
        if [ ! -z "$components" ]; then
            echo "Component Definitions:"
            echo "$components"
        fi

        # React Hooks Usage (inside components)
        local react_hooks=$(grep -E "  const .* = (useState|useEffect|useRef|useCallback|useMemo)" "$file" | sort | uniq)
        if [ ! -z "$react_hooks" ]; then
            echo "React Hooks Usage:"
            echo "$react_hooks"
        fi

        # Custom Hooks Usage (inside components)
        local custom_hooks=$(grep -E "  const .* = use[A-Z][a-zA-Z]*" "$file" | grep -v "useState\|useEffect\|useRef\|useCallback\|useMemo\|useStore" | awk '!seen[$0]++' | sort)
        if [ ! -z "$custom_hooks" ]; then
            echo "Custom Hooks Usage:"
            echo "$custom_hooks"
        fi

        # Store Selectors (inside components)
        local selectors=$(grep -E "  const .* = useStore\(.*\);" "$file" | grep -v "set[A-Z]" | sort | uniq)
        if [ ! -z "$selectors" ]; then
            echo "Store Selectors:"
            echo "$selectors"
        fi

        # Store Actions (inside components)
        local actions=$(grep -E "  const .* = useStore\(.*\);" "$file" | grep "set[A-Z]" | sort | uniq)
        if [ ! -z "$actions" ]; then
            echo "Store Actions:"
            echo "$actions"
        fi

        # Store State Access (can be anywhere)
        local state_access=$(grep -E "\.getState\(\)" "$file" | sort | uniq)
        if [ ! -z "$state_access" ]; then
            echo "Store State Access:"
            echo "$state_access"
        fi

        # JSX Root Elements (to understand component structure)
        local jsx_roots=$(grep -E "return \(" "$file" -A 2 | grep -E "^ *<[A-Z][a-zA-Z]*|^ *<>" | head -n 1 | sed 's/^ *//')
        if [ ! -z "$jsx_roots" ]; then
            echo "JSX Root Elements:"
            echo "$jsx_roots"
        fi

        # JSX Custom Components (to see what components are used in rendering)
        local jsx_components=$(grep -E "[ (]<[A-Z][a-zA-Z]*" "$file" | grep -v "return" | sed 's/.*\(<[A-Z][a-zA-Z]*[^>]*>\)/\1/' | sort | uniq)
        if [ ! -z "$jsx_components" ]; then
            echo "JSX Components Used:"
            echo "$jsx_components"
        fi
    fi

    # Exported Items (usually at the end)
    local exports=$(grep -E "^export (const|default|function)" "$file")
    if [ ! -z "$exports" ]; then
        echo "Exports:"
        echo "$exports"
    fi

    prinft "\n"
}

# Function to run regression test
run_regression_test() {
    local test_dir=$(realpath "$1")  # Changed from $2 to $1
    echo "🧪 Running regression test from directory: $test_dir"

    # Check if test directory exists
    if [ ! -d "$test_dir" ]; then
        echo "❌ Error: Test directory doesn't exist: $test_dir"
        exit 1
    fi

    # Check if test files exist in the specified directory
    if [ ! -f "$test_dir/test-file.tsx" ] || [ ! -f "$test_dir/summary_output.txt" ]; then
        echo "❌ Error: Missing test files in $test_dir (test-file.tsx or summary_output.txt)"
        exit 1
    fi

    # Create temporary output file
    local temp_output=$(mktemp)

    # Run analysis on test file
    process_file "$test_dir/test-file.tsx" > "$temp_output"

    # Compare with reference output
    echo "=== Diff ================================================="
    if diff -u "$test_dir/summary_output.txt" "$temp_output"; then
        echo "✅ Regression test passed! Output matches reference."
        rm "$temp_output"
        exit 0
    else
        echo "❌ Regression test failed! See differences above."
        rm "$temp_output"
        exit 1
    fi
}


# Main script logic
if [ "$1" == "--test" ]; then
    if [ -z "$2" ]; then
        echo "Error: Please provide test directory path"
        echo "Usage for test: rsum --test <test_directory_path>"
        exit 1
    fi
    run_regression_test "$2"  # Pass the second argument to run_regression_test
else
    echo "🔮 Ultimate File Analysis Magic V11 - FINAL PERFECTION ✨"
    echo "=================================================="

    # Check if receiving input from pipe
    if [ -p /dev/stdin ]; then
        # Read from stdin (pipe)
        while read -r file; do
            if [[ $file =~ \.(ts|tsx|js|jsx)$ ]] && [[ ! $file =~ node_modules ]]; then
                process_file "$file"
            fi
        done
    else
        # Original directory processing logic
        if [ -z "$1" ]; then
            echo "Error: Please provide a directory path or pipe input"
            echo "Usage: rsum "
            echo "       find . -name \"*.ts\" | rsum"
            echo '       find . -path '*/src/*.ts' | grep -v 'node_modules' | grep -v 'stryker' | grep -v 'test' | rsum'
            exit 1
        fi
    fi
fi
