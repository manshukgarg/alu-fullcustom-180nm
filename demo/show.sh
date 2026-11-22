#!/bin/bash
# Demonstration views of the project for the ChipCraft lab desktop. Every view opens the
# design data of the repository in the tool that produced or checks it.
#
#   bash demo/show.sh schematic [cell]    transistor schematic in Xschem               (fb4)
#   bash demo/show.sh layout [cell]       cell layout in Magic, after a new DRC,
#                                         extraction and LVS of the cell               (fb4)
#   bash demo/show.sh chip [design]       routed 4-bit ALU in KLayout                  (fb)
#   bash demo/show.sh chip-magic [design] routed 4-bit ALU in Magic                    (fb)
#   bash demo/show.sh cell-sim [cell]     simulation of fb4 or cs: function table, waveforms
#   bash demo/show.sh chip-sim [design]   simulation of the extracted routed ALU: 32 vectors
#   bash demo/show.sh alu-sim [design]    ALU from one cell set at transistor level: 32 vectors
#   bash demo/show.sh alu-delay [design]  slowest transition of that ALU, waveforms
#   bash demo/show.sh results             result tables of Steps 3c, 5 and 6
#
# cells:          fb4 cs fa xor2 mux2 mux2i nand2 nor2 and2 or2 inv buf (library pl018),
#                 or any cell in mag/ (opt_fa, conv_xor2, ...)
# routed designs: fb (proposed), beh slice map (D4, pl018 cells), osu-beh osu-slice osu-map
#                 (D3, OSU018 cells); chip views need the layouts of the last lab run
# ALU designs:    fb (proposed) pl opt conv gate (alu-sim and alu-delay)
# Options:        --no-plot (simulations: tables only)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEMO=$ROOT/demo
OUT=$DEMO/out
OSU=/apps/vlsi/share/qflow/tech/osu018
TECH=$ROOT/tech/pl018

usage() {
    awk 'NR >= 4 && /^#/ {sub(/^# ?/, ""); print} /^ROOT=/ {exit}' "$0"
    exit "${1:-0}"
}

need() {
    for t in "$@"; do
        command -v "$t" > /dev/null 2>&1 || { echo "ERROR: '$t' is not installed here (run this in the lab)"; exit 1; }
    done
}

need_display() {
    [ -n "$DISPLAY" ] || { echo "ERROR: no graphical display (DISPLAY is not set); use the lab desktop"; exit 1; }
}

cellname() {
    local c=$1
    if [ -f "$ROOT/mag/$c.mag" ]; then echo "$c"
    elif [ -f "$ROOT/mag/pl_$c.mag" ]; then echo "pl_$c"
    else echo "ERROR: no layout mag/$c.mag or mag/pl_$c.mag" >&2; return 1
    fi
}

designdir() {
    case "$1" in
        osu-*) echo "$ROOT/step2_rtl_baseline/qflow_${1#osu-}" ;;
        *) echo "$ROOT/step5_library/qflow_$1" ;;
    esac
}

describe() {
    case "$1" in
        pl_fb4) echo "function block FB4: P = C[2A+B], 4:1 transmission-gate tree, inverters, buffer" ;;
        pl_cs) echo "carry-sum cell CS: CO = P ? CI : A,  Y = K ? P : P xor CI" ;;
        pl_fa) echo "full adder, transmission-gate style" ;;
        pl_*) echo "library pl018 cell" ;;
        opt_*) echo "minimum-PDP cell (Step 4 library)" ;;
        conv_*) echo "conventional static CMOS cell (Step 4 library)" ;;
        *) echo "cell" ;;
    esac
}

lvs_verdict() {    # verdict of Netgen reports (files given as arguments)
    local t
    t=$(cat "$@" 2> /dev/null)
    if [ -z "$t" ]; then echo "no result"
    elif echo "$t" | grep -qi "do not match\|failed matching"; then echo "MISMATCH"
    elif echo "$t" | grep -qi "failed pin matching\|port errors"; then echo "pins differ"
    elif echo "$t" | grep -qi "property errors\|missing properties"; then echo "device sizes differ"
    elif echo "$t" | grep -qi "match uniquely\|circuits match with\|match correctly"; then echo "match"
    else echo "no result"
    fi
}

# Xschem schematic netlist of a cell as a subcircuit (demo/xschem/<cell>.sch); prints its path
schematic_netlist() {
    local cell=$1 dir=$OUT/xschem
    [ -f "$DEMO/xschem/$cell.sch" ] && command -v xschem > /dev/null 2>&1 || return 1
    mkdir -p "$dir"
    rm -f "$dir/$cell.spice"
    (cd "$DEMO/xschem" && xschem --rcfile "$DEMO/xschem/xschemrc" -n -s -q -x -o "$dir" "$cell.sch" \
        > "$dir/${cell}_netlist.log" 2>&1)
    [ -s "$dir/$cell.spice" ] || return 1
    # top level as a subcircuit: Xschem comments it out unless the LVS option is set
    sed -e 's/^\*\*\.subckt/.subckt/' -e 's/^\*\*\.ends/.ends/' "$dir/$cell.spice" > "$dir/${cell}_sch.spice"
    echo "$dir/${cell}_sch.spice"
}

view_schematic() {
    local cell
    cell=$(cellname "${1:-fb4}") || exit 1
    need xschem
    need_display
    [ -f "$DEMO/xschem/$cell.sch" ] || {
        echo "No schematic demo/xschem/$cell.sch; schematics: $(cd "$DEMO/xschem" && ls *.sch | tr '\n' ' ')"
        exit 1; }
    echo "Schematic $cell ($(describe "$cell"))"
    if net=$(schematic_netlist "$cell"); then
        echo "  netlist written by Xschem: $(grep -c '^M' "$net") transistors ($net)"
    fi
    echo "Opening Xschem: f fits the drawing; click a wire and press k to highlight its net (Shift+K clears);"
    echo "n writes the netlist, Shift+A shows it."
    cd "$DEMO/xschem" && exec xschem --rcfile "$DEMO/xschem/xschemrc" "$cell.sch"
}

view_layout() {
    local cell ref setup sch
    cell=$(cellname "${1:-fb4}") || exit 1
    need magic
    mkdir -p "$OUT/magic"
    cd "$OUT/magic" || exit 1
    rm -f "${cell}_lvs.spice" "${cell}_lvs.out"
    echo "Cell $cell: $(describe "$cell")"
    echo "[1/2] design-rule check and extraction (Magic, SCN6M_SUBM.10 rules, lambda = 0.1 um)"
    DEMO_CELL=$cell magic -dnull -noconsole -rcfile "$ROOT/tech/magicrc" ../../magic_check.tcl \
        > "${cell}_check.log" 2>&1
    if ! grep -q "^EXTRACTED" "${cell}_check.log"; then
        echo "ERROR: Magic did not finish; see $OUT/magic/${cell}_check.log"
        exit 1
    fi
    grep "^DRC:" "${cell}_check.log" | sed 's/^DRC: /      /'
    echo "      DRC errors: $(awk '/^DRC_ERRORS/{print $2}' "${cell}_check.log")"
    echo "      extracted: $(grep -c '^M.* nfet ' "${cell}_lvs.spice") nfet + $(grep -c '^M.* pfet ' "${cell}_lvs.spice") pfet transistors"
    case "$cell" in
        pl_*) ref=$TECH/pl018_cells.sp; setup=$TECH/pl018_setup.tcl ;;
        *) ref=$ROOT/step4_layout/ref/$cell.spice; setup=$OSU/osu018_setup.tcl ;;
    esac
    if sch=$(schematic_netlist "$cell"); then
        ref=$sch
        echo "[2/2] layout versus schematic (Netgen): extraction against the Xschem schematic"
    else
        echo "[2/2] layout versus schematic (Netgen): extraction against the cell netlist"
    fi
    if command -v netgen > /dev/null 2>&1 && [ -f "$ref" ] && [ "$cell" != pl_fill ]; then
        netgen -batch lvs "${cell}_lvs.spice $cell" "$ref $cell" "$setup" "${cell}_lvs.out" \
            > "${cell}_netgen.log" 2>&1
        cat "${cell}_lvs.out" "${cell}_netgen.log" 2> /dev/null | grep -E "^Circuit 1 contains" | head -2 \
            | sed 's/^/      /'
        echo "      result: $(lvs_verdict "${cell}_lvs.out" "${cell}_netgen.log")   (report: $OUT/magic/${cell}_lvs.out)"
    else
        echo "      skipped (netgen or the reference netlist not available)"
    fi
    need_display
    echo "Opening the layout in Magic ..."
    DEMO_CELL=$cell exec magic -rcfile "$ROOT/tech/magicrc" ../../magic_view.tcl
}

chip_facts() {    # facts of a routed design from the logs of the last lab run
    python3 "$DEMO/tools/facts.py" "$1"
}

view_chip() {
    local d=${1:-fb} q gds
    q=$(designdir "$d")
    gds=$q/layout/alu4_full.gds
    [ -f "$gds" ] || { echo "ERROR: $gds not found; run the step that builds design '$d' first"; exit 1; }
    need klayout
    need_display
    chip_facts "$d"
    # KLayout settings for the demo: open with every hierarchy level (the cell contents) and
    # fitted to the window; a separate settings file, the user's own KLayout settings stay as they are
    local rc=$DEMO/out/klayout/klayoutrc
    mkdir -p "$DEMO/out/klayout"
    cat > "$rc" <<'XML'
<?xml version="1.0" encoding="utf-8"?>
<config>
 <full-hierarchy-new-cell>true</full-hierarchy-new-cell>
 <initial-hier-depth>99</initial-hier-depth>
 <fit-new-cell>true</fit-new-cell>
</config>
XML
    echo "Opening the GDS written by Magic (routing and cell layouts) in KLayout"
    echo "If the cells show as empty frames: click once inside the KLayout window, then press *"
    echo "(menu Display > Full Hierarchy) and F2 (Display > Zoom Fit). Keys typed here go to the terminal."
    exec klayout -c "$rc" -l "$DEMO/scmos.lyp" "$gds"
}

view_chip_magic() {
    local d=${1:-fb} q
    q=$(designdir "$d")
    [ -f "$q/layout/alu4.mag" ] || { echo "ERROR: $q/layout/alu4.mag not found; run the step first"; exit 1; }
    need magic
    need_display
    chip_facts "$d"
    echo "Opening the routed layout in Magic (start-up file of the Qflow run)"
    cd "$q/layout" && exec magic "$DEMO/magic_chip.tcl"
}

results() {
    local f
    for f in step3_cells/out/alu_cells_summary.txt step5_library/out/summary.txt \
             step6_alu_schematic/out/summary.txt; do
        echo "=============================================================================="
        if [ -f "$ROOT/$f" ]; then echo "$f"; cat "$ROOT/$f"
        else echo "$f: not present (run that step first)"
        fi
    done
}

view=$1
[ $# -gt 0 ] && shift
case "$view" in
    schematic) view_schematic "$@" ;;
    layout) view_layout "$@" ;;
    chip) view_chip "$@" ;;
    chip-magic) view_chip_magic "$@" ;;
    cell-sim) need ngspice; exec python3 "$DEMO/tools/wave.py" cell "$@" ;;
    chip-sim) need ngspice; exec python3 "$DEMO/tools/wave.py" chip-test "$@" ;;
    alu-sim) need ngspice; exec python3 "$DEMO/tools/wave.py" alu-test "$@" ;;
    alu-delay) need ngspice; exec python3 "$DEMO/tools/wave.py" alu-delay "$@" ;;
    results) results ;;
    ""|-h|--help|help) usage 0 ;;
    *) echo "unknown view '$view'"; usage 1 ;;
esac
