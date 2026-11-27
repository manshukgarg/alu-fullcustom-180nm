#!/bin/bash
# Verilog part of the demonstration, for the ChipCraft lab terminal:
#   1. the behavioural RTL against the self-checking test bench (all 2048 input cases)
#   2. the proposed ALU netlist (FB4, CS and library cells) against the same bench
#   3. Yosys synthesis of the behavioural RTL onto the OSU 0.18 um cells and onto pl018
# The commands are those of step2_rtl_baseline/run.sh and step5_library/run.sh.
#
#   bash demo/verilog.sh        press Enter before each step
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=$ROOT/demo/out/verilog
OSU=/apps/vlsi/share/qflow/tech/osu018/osu018_stdcells.lib
PL=$ROOT/tech/pl018/pl018_cells.lib
mkdir -p "$OUT"

for t in iverilog vvp yosys; do
    command -v "$t" > /dev/null 2>&1 || { echo "ERROR: '$t' is not installed here (run this in the lab)"; exit 1; }
done

step() {
    echo
    echo "=== $1"
    echo "    $2"
    read -r -p "    press Enter to run " _
}

step "1/3  RTL test of the behavioural Verilog (rtl/alu4.v)" \
     "test bench tb/tb_alu4.v: 8 operations x 16 values of a x 16 values of b = 2048 cases, checked"
echo "    iverilog -g2012 -o sim_rtl tb/tb_alu4.v rtl/alu4.v && vvp -n sim_rtl"
iverilog -g2012 -o "$OUT/sim_rtl" "$ROOT/tb/tb_alu4.v" "$ROOT/rtl/alu4.v" && vvp -n "$OUT/sim_rtl"

step "2/3  Test of the proposed ALU netlist (rtl/alu4_fb_pl018.v)" \
     "27 cells: 4 x FB4, 4 x CS, decoder and flags; Verilog models of the pl018 cells; same 2048 cases"
echo "    iverilog -g2012 -DGATE -o sim_fb tb/tb_alu4.v rtl/alu4_fb_pl018.v tech/pl018/pl018_cells.v && vvp -n sim_fb"
iverilog -g2012 -DGATE -o "$OUT/sim_fb" "$ROOT/tb/tb_alu4.v" "$ROOT/rtl/alu4_fb_pl018.v" "$ROOT/tech/pl018/pl018_cells.v" \
    && vvp -n "$OUT/sim_fb"

step "3/3  Synthesis of the behavioural Verilog with Yosys" \
     "read_verilog, synth, abc -liberty (map onto the cells of the library), stat (cells and area)"
for lib in "$OSU" "$PL"; do
    name=$(basename "$lib" .lib)
    if [ ! -f "$lib" ]; then
        echo "    ($lib not found: skipped; it is written by step5_library/run.sh)"
        continue
    fi
    echo
    echo "--- library $name"
    yosys -p "read_verilog $ROOT/rtl/alu4.v; synth -top alu4 -flatten; abc -liberty $lib; opt_clean -purge; stat -liberty $lib" \
        > "$OUT/yosys_$name.log" 2>&1 || { echo "    Yosys failed: see $OUT/yosys_$name.log"; continue; }
    sed -n '/Printing statistics/,$p' "$OUT/yosys_$name.log" | grep -v "^$" | grep -v "End of script" | head -40
done
echo
echo "Logs: $OUT"
