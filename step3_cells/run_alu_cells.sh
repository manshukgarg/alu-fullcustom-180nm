#!/bin/bash
# Step 3c: the two ALU-specific cells (function block FB4, carry-sum cell CS): sizing on the
# k x r grid of the cell sweep and comparison with the same functions composed of library
# cells, at 1.8 V with FO4 loads. Needs only Python and Ngspice; about 5-10 minutes.
# Usage (from the repository root):  bash step3_cells/run_alu_cells.sh
# Reprint the summary later without simulating:  python3 step3_cells/run_alu_cells.py --report
cd "$(dirname "$0")" || exit 1
mkdir -p out
rm -f out/wb_*
python3 check_netlists.py | tail -1
python3 run_alu_cells.py | tee out/alu_cells_summary.txt
