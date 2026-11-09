# Design-rule check and transistor-level extraction of a Qflow layout made with the
# project cell library, with the real cell layouts (mag/) in place of the LEF outlines.
# Run from <qflow directory>/layout, where Qflow wrote its .magicrc and run.sh wrote
# pl_cells.tcl (PL_CELLS: cell names, PL_MAG: absolute path of mag/):
#   magic -dnull -noconsole ../../layout_check.tcl
# Writes alu4_pex.spice (flat: every transistor plus all parasitic capacitances) and alu4_full.gds.
source pl_cells.tcl
foreach c $PL_CELLS {
    load $PL_MAG/$c
}
load alu4
select top cell
set bbox [box values]
puts "CELL_BBOX $bbox"
if {[lindex $bbox 2] <= [lindex $bbox 0] || [lindex $bbox 3] <= [lindex $bbox 1]} {
    puts "ERROR: layout alu4 is empty or did not load"
    quit -noprompt
}
expand

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

extract do local
extract all
ext2spice hierarchy off
ext2spice format ngspice
ext2spice scale off
ext2spice cthresh 0
ext2spice -o alu4_pex.spice
puts "EXTRACTED alu4_pex.spice"

gds write alu4_full.gds
puts "GDS_WRITTEN alu4_full.gds"
quit -noprompt
