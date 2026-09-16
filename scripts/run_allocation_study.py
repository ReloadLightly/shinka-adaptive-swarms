#!/usr/bin/env python3
"""Run explicitly staged allocation-v2 validation and frozen final comparisons."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_swarms.allocation_study import main

if __name__ == "__main__":
    main()
