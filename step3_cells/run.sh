#!/bin/bash
# Step 3a: cell circuit-style comparison at 1.8 V, reference sizing, FO4 load.
# Usage (from the repository root):  bash step3_cells/run.sh
cd "$(dirname "$0")" || exit 1
rm -rf out
mkdir -p out
python3 run_cells.py --vdd 1.8 --period 2e-9 | tee out/summary.txt
