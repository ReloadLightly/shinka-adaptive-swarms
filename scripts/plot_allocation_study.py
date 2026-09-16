#!/usr/bin/env python3
"""Render the completed v2 comparison from saved outcomes only."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.allocation_figures import render_allocation_study


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="V2 frozen study directory with analysis.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/relocation_allocation_v2")
    args = parser.parse_args()
    render_allocation_study(args.run, args.output)
