#!/bin/bash
# Step 2: 4-bit ALU, verification and the automated standard-cell implementation (design D3).
# Three designs go through the whole flow with the OSU018 cells:
#   beh    rtl/alu4.v              behavioural RTL, synthesized
#   slice  rtl/alu4_slice.v        bit-sliced RTL, synthesized
#   map    rtl/alu4_map_osu018.v   hand-mapped netlist (inverting multiplexers, FAX1 full adders);
#                                  synthesis cannot use two-output cells, the hand mapping can
#   1. exhaustive simulation of the three descriptions (iverilog, 2048 vectors)
#   2. Yosys synthesis onto the OSU018 cells (cell count, area)
#   3. gate-level simulation of the netlists
#   4. OpenSTA worst-case delay
#   5. Qflow synthesis, placement, routing, layout migration and LVS
#   6. Magic: DRC with the real cell layouts and transistor-level extraction
#   7. Ngspice: every layout and its cell-level netlist (before layout) with the
#      project's ALU testbench (sim/alutb.py): function, delay, energy per operation, leakage
# Usage (from the repository root):  bash step2_rtl_baseline/run.sh       (about 15-25 minutes)
cd "$(dirname "$0")" || exit 1
TECH=/apps/vlsi/share/qflow/tech/osu018
LIB=$TECH/osu018_stdcells.lib
DESIGNS="beh slice map"
rtl() {
    case "$1" in
        beh) echo ../rtl/alu4.v ;;
        slice) echo ../rtl/alu4_slice.v ;;
        *) echo ../rtl/alu4_map_osu018.v ;;
    esac
}
rm -rf out qflow qflow_beh qflow_slice qflow_map
mkdir -p out/sim

echo "[1/7] simulation of the three descriptions (iverilog)"
for d in $DESIGNS; do
    if [ "$d" = map ]; then
        iverilog -g2012 -DGATE -o out/sim_$d ../tb/tb_alu4.v "$(rtl $d)" $TECH/osu018_stdcells.v \
            > out/iverilog_$d.log 2>&1
    else
        iverilog -g2012 -o out/sim_$d ../tb/tb_alu4.v "$(rtl $d)" > out/iverilog_$d.log 2>&1
    fi
    vvp -n out/sim_$d > out/sim_$d.log 2>&1
done

echo "[2/7] synthesis onto OSU018 cells (yosys)"
for d in $DESIGNS; do
    if [ "$d" = map ]; then
        # already a netlist of library cells: only counted
        cp "$(rtl $d)" out/${d}_syn.v
        cat > out/synth_$d.ys <<EOF
read_liberty -lib $LIB
read_verilog $(rtl $d)
hierarchy -check -top alu4
stat -liberty $LIB
EOF
    else
        cat > out/synth_$d.ys <<EOF
read_verilog $(rtl $d)
synth -top alu4 -flatten
abc -liberty $LIB
opt_clean -purge
stat -liberty $LIB
write_verilog -noattr -noexpr out/${d}_syn.v
EOF
    fi
    yosys -s out/synth_$d.ys > out/yosys_$d.log 2>&1
done

echo "[3/7] gate-level simulation of the netlists"
for d in $DESIGNS; do
    iverilog -g2012 -DGATE -o out/sim_gate_$d ../tb/tb_alu4.v out/${d}_syn.v $TECH/osu018_stdcells.v \
        > out/iverilog_gate_$d.log 2>&1
    vvp -n out/sim_gate_$d > out/sim_gate_$d.log 2>&1
done

echo "[4/7] static timing of the netlists (OpenSTA)"
for d in $DESIGNS; do
    cat > out/sta_$d.tcl <<EOF
read_liberty $LIB
read_verilog out/${d}_syn.v
link_design alu4
create_clock -name vclk -period 10
set_input_delay 0 -clock vclk [all_inputs]
set_output_delay 0 -clock vclk [all_outputs]
set_input_transition 0.05 [all_inputs]
set_load 0.01 [all_outputs]
report_checks -path_delay max -digits 3
exit
EOF
    sta -no_splash -exit out/sta_$d.tcl > out/sta_$d.log 2>&1
done

echo "[5/7] automated place and route of the three designs (qflow), 1-3 minutes each"
for d in $DESIGNS; do
    q=qflow_$d
    mkdir -p $q/source $q/synthesis $q/layout $q/log
    cp "$(rtl $d)" $q/source/alu4.v
    (cd $q && qflow -T osu018 synthesize place route backanno migrate lvs alu4 \
        > ../out/qflow_$d.log 2>&1)
done

echo "[6/7] DRC with real cell layouts and transistor-level extraction (magic)"
for d in $DESIGNS; do
    if [ -f qflow_$d/layout/alu4.mag ]; then
        (cd qflow_$d/layout && magic -dnull -noconsole ../../layout_check.tcl \
            > ../../out/magic_$d.log 2>&1)
    else
        echo "ERROR: qflow_$d/layout/alu4.mag not created (see out/qflow_$d.log)" > out/magic_$d.log
    fi
done

echo "[7/7] transistor-level simulation (ngspice): 6 netlists, a few minutes each"
for d in $DESIGNS; do
    python3 ../sim/alutb.py qflow_$d/layout/alu4_pex.spice --top alu4 --width 4 \
        --label ${d}_post --out out/sim > out/sim/${d}_post.out 2>&1 &
done
wait
for d in $DESIGNS; do
    python3 ../sim/alutb.py qflow_$d/synthesis/alu4.spc --lib $TECH/osu018_stdcells.sp \
        --top alu4 --width 4 --label ${d}_pre --out out/sim > out/sim/${d}_pre.out 2>&1 &
done
wait

python3 summary.py | tee out/summary.txt
