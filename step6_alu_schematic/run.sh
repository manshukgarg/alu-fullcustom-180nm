#!/bin/bash
# Step 6: the 4-bit ALU at transistor level, built from each cell style (before layout).
# The same ALU structure is composed from four cell sets and measured with the project's
# ALU testbench (sim/alutb.py), so the cell styles are compared at ALU level:
#   gate   gate-level cells of the LTspice cell set (NAND-based XOR, multiplexer and full adder)
#   conv   conventional static CMOS cells (design D1, schematic)
#   opt    minimum-PDP cells of Step 3, unbuffered pass-gate cells included (design D2, schematic)
#   pl     cells of the automated-flow library pl018, slice with inverting multiplexers
# The netlists in netlists/ are written by sim/gen_alu.py (not run here).
#   1. logic check of all cell and ALU netlists at switch level (Python, no simulator)
#   2. Ngspice: function, delay, energy per operation and leakage of the four ALUs
# Usage (from the repository root):  bash step6_alu_schematic/run.sh      (about 5-10 minutes)
cd "$(dirname "$0")" || exit 1
rm -rf out
mkdir -p out

echo "[1/2] logic check of the cell and ALU netlists (switch level)"
python3 ../step3_cells/check_netlists.py > out/check_cells.txt 2>&1
python3 ../sim/gen_alu.py --check > out/check_alu.txt 2>&1
tail -1 out/check_cells.txt
grep -c "correct" out/check_alu.txt | sed 's/$/ ALU netlists correct on all 2048 vectors/'

echo "[2/2] transistor-level simulation of the four ALUs (ngspice), a few minutes"
for pair in "gate conv" "opt pl"; do
    for d in $pair; do
        python3 ../sim/alutb.py netlists/alu4_$d.sp --top alu4 --width 4 --label $d --out out \
            > out/$d.out 2>&1 &
    done
    wait
done

python3 summary.py | tee out/summary.txt
