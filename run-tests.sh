#!/bin/bash

set -euo pipefail

# Initialize PYTHONPATH if not set
PYTHONPATH="${PYTHONPATH:-}"

# Add src directory to PYTHONPATH
if [[ -z "${PYTHONPATH}" ]]; then
    export PYTHONPATH="$PWD/src"
else
    export PYTHONPATH="$PWD/src:${PYTHONPATH}"
fi

# Run tests with coverage
coverage run -m pytest tests/test* --maxfail 3
coverage html
coverage report
