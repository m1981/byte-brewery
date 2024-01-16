#!/bin/bash

set -eu
python3 -m unittest discover -s tests -p 'test*.py'
