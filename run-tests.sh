#!/bin/bash

set -euo pipefail

if [ "${1-}" = "coverage" ]; then
    coverage run -m pytest tests/test* --maxfail 3
    coverage html
    coverage report
else
    python3 -m unittest discover -s tests -p 'test*.py'
fi
