# Design-rule check and transistor-level extraction of a Qflow layout, with the
# real OSU018 cell layouts (GDS view) in place of the LEF outlines.
# Run from <qflow directory>/layout, where Qflow wrote its .magicrc:
#   magic -dnull -noconsole ../../layout_check.tcl
# Writes alu4_pex.spice (flat netlist: every transistor of every cell plus all
# parasitic capacitances of cells and routing) and alu4_full.gds.
gds readonly true
gds rescale false
gds read /apps/vlsi/share/qflow/tech/osu018/osu018_stdcells.gds2
load alu4
select top cell
set bbox [box values]
puts "CELL_BBOX $bbox"
if {[lindex $bbox 2] <= [lindex $bbox 0] || [lindex $bbox 3] <= [lindex $bbox 1]} {
    puts "ERROR: layout alu4 is empty or did not load"
    quit -noprompt
}
expand

# full design-rule check, every error type with its count
drc euclidean on
drc on
drc check
drc catchup
set total 0
foreach {why boxes} [drc listall why] {
    puts "DRC: $why ([llength $boxes])"
    incr total [llength $boxes]
}
puts "DRC_ERRORS $total"

# extraction: devices of the cell layouts and capacitances of cells and wiring
extract do local
extract all
ext2spice hierarchy off
ext2spice format ngspice
ext2spice scale off
ext2spice cthresh 0
ext2spice -o alu4_pex.spice
puts "EXTRACTED alu4_pex.spice"

# complete GDS (cells included) for viewing in KLayout
gds write alu4_full.gds
puts "GDS_WRITTEN alu4_full.gds"
quit -noprompt
