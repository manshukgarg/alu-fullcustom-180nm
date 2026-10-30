#!/bin/bash
# Step 3b: size every candidate cell (8 width scales x 5 P/N ratios) at 1.8 V, FO4 load,
# and select the minimum-PDP size of each style (delay includes the input driver).
# Usage (from the repository root):  bash step3_cells/run_sweep.sh
# Reprint the summary later without simulating:  python3 step3_cells/run_cells.py --report
cd "$(dirname "$0")" || exit 1
mkdir -p out
rm -f out/tb_*
python3 run_cells.py --sweep --vdd 1.8 --period 2e-9 | tee out/sweep_summary.txt
