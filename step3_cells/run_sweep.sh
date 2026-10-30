#!/bin/bash
# Step 3b: size every candidate cell (7 width scales x 4 P/N ratios) at 1.8 V, FO4 load,
# and select the minimum-PDP size of each style.
# Usage (from the repository root):  bash step3_cells/run_sweep.sh
cd "$(dirname "$0")" || exit 1
mkdir -p out
python3 run_cells.py --sweep --vdd 1.8 --period 2e-9 | tee out/sweep_summary.txt
