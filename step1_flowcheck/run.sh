#!/bin/bash
# Step 1 flow check on one inverter: schematic simulation, layout DRC,
# extraction, LVS and post-layout simulation.
# Usage (from the repository root):  bash step1_flowcheck/run.sh
cd "$(dirname "$0")" || exit 1
TECH=/apps/vlsi/share/qflow/tech/osu018
mkdir -p out
rm -f out/* inv.ext inv_lvs.spice inv_pex.spice

echo "[1/4] schematic simulation (ngspice)"
cp inv_sch.spice out/dut.spice
ngspice -b tb_inv_dc.sp   > out/sch_dc.log   2>&1
ngspice -b tb_inv_tran.sp > out/sch_tran.log 2>&1

echo "[2/4] DRC and extraction (magic)"
magic -dnull -noconsole -rcfile ../tech/magicrc check_layout.tcl > out/magic.log 2>&1
mv -f inv.ext inv_lvs.spice inv_pex.spice out/ 2>/dev/null

echo "[3/4] LVS (netgen)"
netgen -batch lvs "out/inv_lvs.spice inv" "inv_ref.spice inv" \
    "$TECH/osu018_setup.tcl" out/lvs.out > out/netgen.log 2>&1

echo "[4/4] post-layout simulation (ngspice)"
if [ -s out/inv_pex.spice ]; then
    cp out/inv_pex.spice out/dut.spice
    ngspice -b tb_inv_dc.sp   > out/pex_dc.log   2>&1
    ngspice -b tb_inv_tran.sp > out/pex_tran.log 2>&1
fi

# value of a .meas result from a log, multiplied by a scale factor
meas() {
    [ -f "$1" ] || { printf "n/a"; return; }
    awk -v n="$2" -v s="$3" '$1==n && $2=="=" {printf "%.3f", $3*s; f=1; exit}
        END {if (!f) printf "n/a"}' "$1"
}

{
    echo "================================================================"
    echo "STEP 1 SUMMARY  inverter Wn 1.0 um / Wp 2.0 um / L 0.2 um, 1.8 V, 27 C"
    echo "================================================================"
    echo "DRC errors : $(awk '/^DRC_ERRORS/ {print $2}' out/magic.log)"
    grep '^DRC:' out/magic.log
    echo "LVS        : $(grep -ihE 'final result|circuits match|do not match' out/lvs.out out/netgen.log 2>/dev/null | tail -1)"
    echo
    printf "%-26s %12s %12s\n" "metric" "schematic" "post-layout"
    for row in "vm|switching threshold VM (V)|1|dc" \
               "tphl|tpHL (ps)|1e12|tran" "tplh|tpLH (ps)|1e12|tran" \
               "tp|tp average (ps)|1e12|tran" "tr|rise time 10-90 (ps)|1e12|tran" \
               "tf|fall time 90-10 (ps)|1e12|tran" "pavg|power at 500 MHz (uW)|1e6|tran" \
               "pdp|PDP (fJ)|1e15|tran"; do
        IFS='|' read -r key text scale an <<< "$row"
        printf "%-26s %12s %12s\n" "$text" "$(meas out/sch_$an.log $key $scale)" \
            "$(meas out/pex_$an.log $key $scale)"
    done
    echo
    echo "---- extracted netlist (out/inv_lvs.spice) ----"
    cat out/inv_lvs.spice 2>/dev/null || echo "(not created: see out/magic.log)"
} | tee out/summary.txt

if ! grep -q '^DRC_ERRORS' out/magic.log; then
    echo; echo "---- last lines of out/magic.log ----"; tail -20 out/magic.log
fi
