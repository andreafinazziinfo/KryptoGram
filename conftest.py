"""Pytest configuration and root import resolution."""

import sys
from pathlib import Path

# Assicura che la root del repository sia sempre in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
