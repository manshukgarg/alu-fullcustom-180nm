#!/bin/bash
# Step 2: RTL verification and the automated standard-cell baseline (OSU018 cells).
#   1. exhaustive simulation of both ALU models (behavioural and bit-sliced)
#   2. Yosys synthesis of both models onto the OSU018 library (cell count, area)
#   3. gate-level simulation of the synthesized bit-sliced netlist
#   4. OpenSTA worst-case delay of both synthesized netlists
#   5. Qflow synthesis, placement, routing, layout migration and LVS (bit-sliced RTL)
#   6. Magic DRC of the routed layout with the real cell layouts, by error type
# Usage (from the repository root):  bash step2_rtl_baseline/run.sh
cd "$(dirname "$0")" || exit 1
TECH=/apps/vlsi/share/qflow/tech/osu018
LIB=$TECH/osu018_stdcells.lib
mkdir -p out
rm -rf out/* qflow

echo "[1/6] RTL simulation of both models (iverilog)"
for m in alu8 alu8_slice; do
    iverilog -g2012 -o out/sim_$m ../tb/tb_alu8.v ../rtl/$m.v > out/iverilog_$m.log 2>&1
    vvp -n out/sim_$m > out/sim_$m.log 2>&1
done

echo "[2/6] synthesis onto OSU018 cells (yosys)"
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

echo "[3/6] gate-level simulation of the synthesized bit-sliced netlist"
iverilog -g2012 -DGATE -o out/sim_gate ../tb/tb_alu8.v out/alu8_slice_syn.v $TECH/osu018_stdcells.v \
    > out/iverilog_gate.log 2>&1
vvp -n out/sim_gate > out/sim_gate.log 2>&1

echo "[4/6] static timing of both synthesized netlists (OpenSTA)"
for m in alu8 alu8_slice; do
    cat > out/sta_$m.tcl <<EOF
read_liberty $LIB
read_verilog out/${m}_syn.v
link_design alu8
create_clock -name vclk -period 10
set_input_delay 0 -clock vclk [all_inputs]
set_output_delay 0 -clock vclk [all_outputs]
set_input_transition 0.05 [all_inputs]
set_load 0.01 [all_outputs]
report_checks -path_delay max -digits 3
exit
EOF
    sta -no_splash -exit out/sta_$m.tcl > out/sta_$m.log 2>&1
done

echo "[5/6] automated place and route of the bit-sliced RTL (qflow), about 1-3 minutes"
mkdir -p qflow/source qflow/synthesis qflow/layout qflow/log
cp ../rtl/alu8_slice.v qflow/source/alu8.v
(cd qflow && qflow -T osu018 synthesize place route backanno migrate lvs alu8 \
    > ../out/qflow.log 2>&1)

echo "[6/6] DRC of the routed layout with real cell layouts (magic)"
if [ -f qflow/layout/alu8.mag ]; then
    (cd qflow/layout && magic -dnull -noconsole ../../drc_detail.tcl > ../../out/drc_detail.log 2>&1)
fi

{
    echo "================================================================"
    echo "STEP 2 SUMMARY  8-bit ALU, RTL checks and OSU018 automated baseline"
    echo "================================================================"
    echo "RTL, behavioural      : $(grep -h '^TESTS' out/sim_alu8.log)"
    echo "RTL, bit-sliced       : $(grep -h '^TESTS' out/sim_alu8_slice.log)"
    echo "Gate-level, bit-sliced: $(grep -h '^TESTS' out/sim_gate.log)"
    for m in alu8 alu8_slice; do
        cells=$(awk '/ cells$/ && NF==3 {c=$1} /Number of cells/ {c=$NF} END {print c}' out/yosys_$m.log)
        area=$(awk -F: '/Chip area/ {gsub(/ /,"",$2); a=$2} END {print a}' out/yosys_$m.log)
        arr=$(awk '/data arrival time/ && $1+0>0 {print $1; exit}' out/sta_$m.log)
        printf "%-11s Yosys: %4s cells, %9s um2 | OpenSTA worst delay %s ns\n" "$m" "$cells" "$area" "$arr"
    done
    echo "Qflow die area (DEF units): $(grep -h DIEAREA qflow/layout/alu8.def 2>/dev/null | head -1)"
    echo "Qflow routing   : $(grep -h 'Final:' qflow/log/route.log 2>/dev/null | tail -1)"
    echo "Qflow LVS       : $(grep -hiE 'circuits match|do not match|mismatch' qflow/log/lvs.log 2>/dev/null | tail -1)"
    echo "Magic DRC (GDS view): $(awk '/^DRC_ERRORS/ {print $2}' out/drc_detail.log 2>/dev/null) errors"
    grep '^DRC:' out/drc_detail.log 2>/dev/null | sort | uniq | head -12 | sed 's/^/    /'
    echo "---- last lines of the qflow run ----"
    tail -6 out/qflow.log
    for f in out/iverilog_*.log; do
        grep -qi 'error' "$f" 2>/dev/null && { echo "---- $f ----"; grep -i 'error' "$f" | head -5; }
    done
} | tee out/summary.txt
