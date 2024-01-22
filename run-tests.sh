#!/bin/bash

set -euo pipefail

if [ "${1-}" = "coverage" ]; then
    coverage run -m pytest tests/* --maxfail 3
    coverage report
    coverage html
else
    python3 -m unittest discover -s tests -p 'test*.py'
fi
