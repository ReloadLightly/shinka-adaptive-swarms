#!/usr/bin/env python3
"""Render completed v3 comparisons from saved outcomes only."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.joint_figures import render_joint_study

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="V3 frozen study directory with completed analysis.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/joint_relocation_v3")
    args = parser.parse_args()
    render_joint_study(args.run, args.output)
