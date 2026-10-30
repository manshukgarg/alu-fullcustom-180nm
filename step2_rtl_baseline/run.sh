#!/bin/bash
# Step 2: RTL verification and the automated standard-cell baseline (OSU018 cells).
#   1. exhaustive simulation of both ALU models (behavioural and bit-sliced)
#   2. Yosys synthesis of both models onto the OSU018 library (cell count, area)
#   3. gate-level simulation of the synthesized netlist
#   4. OpenSTA worst-case delay of the synthesized netlist
#   5. Qflow synthesis, placement, routing, extraction, LVS and DRC
# Usage (from the repository root):  bash step2_rtl_baseline/run.sh
cd "$(dirname "$0")" || exit 1
TECH=/apps/vlsi/share/qflow/tech/osu018
LIB=$TECH/osu018_stdcells.lib
mkdir -p out
rm -rf out/* qflow

echo "[1/5] RTL simulation of both models (iverilog)"
for m in alu8 alu8_slice; do
    iverilog -g2012 -o out/sim_$m ../tb/tb_alu8.v ../rtl/$m.v > out/iverilog_$m.log 2>&1
    vvp -n out/sim_$m > out/sim_$m.log 2>&1
done

echo "[2/5] synthesis onto OSU018 cells (yosys)"
for m in alu8 alu8_slice; do
    cat > out/synth_$m.ys <<EOF
read_verilog ../rtl/$m.v
synth -top alu8 -flatten
abc -liberty $LIB
opt_clean -purge
stat -liberty $LIB
write_verilog -noattr -noexpr out/${m}_syn.v
EOF
    yosys -s out/synth_$m.ys > out/yosys_$m.log 2>&1
done

echo "[3/5] gate-level simulation of the synthesized netlist"
iverilog -g2012 -DGATE -o out/sim_gate ../tb/tb_alu8.v out/alu8_syn.v $TECH/osu018_stdcells.v \
    > out/iverilog_gate.log 2>&1
vvp -n out/sim_gate > out/sim_gate.log 2>&1

echo "[4/5] static timing of the synthesized netlist (OpenSTA)"
cat > out/sta.tcl <<EOF
read_liberty $LIB
read_verilog out/alu8_syn.v
link_design alu8
create_clock -name vclk -period 10
set_input_delay 0 -clock vclk [all_inputs]
set_output_delay 0 -clock vclk [all_outputs]
set_input_transition 0.05 [all_inputs]
set_load 0.01 [all_outputs]
report_checks -path_delay max -digits 3
exit
EOF
sta -no_splash -exit out/sta.tcl > out/sta.log 2>&1

echo "[5/5] automated place and route (qflow -T osu018), about 1-3 minutes"
mkdir -p qflow/source qflow/synthesis qflow/layout qflow/log
cp ../rtl/alu8.v qflow/source/alu8.v
(cd qflow && qflow -T osu018 synthesize place sta route backanno migrate lvs drc alu8 \
    > ../out/qflow.log 2>&1)

{
    echo "================================================================"
    echo "STEP 2 SUMMARY  8-bit ALU, RTL checks and OSU018 automated baseline"
    echo "================================================================"
    echo "RTL, behavioural      : $(grep -h '^TESTS' out/sim_alu8.log)"
    echo "RTL, bit-sliced       : $(grep -h '^TESTS' out/sim_alu8_slice.log)"
    echo "Gate-level (Yosys)    : $(grep -h '^TESTS' out/sim_gate.log)"
    for m in alu8 alu8_slice; do
        echo "Yosys $m :"
        grep -iE "chip area|cells$|cells:|number of cells" out/yosys_$m.log | tail -3 | sed 's/^/    /'
    done
    echo "OpenSTA worst path (synthesized netlist, 10 fF loads):"
    grep -E "data arrival time|slack" out/sta.log | head -3 | sed 's/^/    /'
    echo "Qflow die area        : $(grep -h DIEAREA qflow/layout/alu8.def 2>/dev/null | head -1)"
    echo "Qflow key lines:"
    grep -hiE "failed route|routes failed|no failed|circuits match|do not match|drc error|total error|worst slack|computed maximum|arrival" \
        qflow/log/*.log 2>/dev/null | tail -12 | sed 's/^/    /'
    echo "---- last lines of the qflow run ----"
    tail -8 out/qflow.log
    for f in out/iverilog_*.log; do
        [ -s "$f" ] && { echo "---- $f ----"; head -5 "$f"; }
    done
} | tee out/summary.txt
