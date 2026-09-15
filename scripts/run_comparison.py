#!/usr/bin/env python3
"""Freeze selected programs and run the reserved paired comparison."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_swarms.comparison import main


if __name__ == "__main__":
    main()
