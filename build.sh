#!/bin/bash
set -e
echo "Building NEXA-S package..."
python -m pip install --upgrade build
python -m build
echo "Build completed. Check dist/ for wheels."
