#!/usr/bin/env python3
"""Register and execute the prospective joint-relocation V3 comparison stages."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from adaptive_swarms.joint_study import main
if __name__ == "__main__":
    main()
