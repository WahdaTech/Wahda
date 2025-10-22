#!/bin/bash

set -euxo pipefail

ruff check .

ruff format --check .

mypy $(find . -type f \( -name "*.py" -o -name "*.pyi" \) ! -path './venv/*' ! -path './proto/*.py')

python -m pytest
