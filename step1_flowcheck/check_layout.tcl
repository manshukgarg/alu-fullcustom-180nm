# Magic batch script: design-rule check, extraction and netlist export.
# Run from step1_flowcheck/:
#   magic -dnull -noconsole -rcfile ../tech/magicrc check_layout.tcl

set cell inv
load ../mag/$cell -force

# stop if the layout did not load (an empty cell would pass every check)
select top cell
set bbox [box values]
puts "CELL_BBOX $bbox"
if {[lindex $bbox 2] <= [lindex $bbox 0] || [lindex $bbox 3] <= [lindex $bbox 1]} {
    puts "ERROR: cell $cell is empty or did not load"
    quit -noprompt
}

# full design-rule check of the top cell
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

# extraction (writes $cell.ext in the current directory)
extract do local
extract all

# netlist for LVS: devices only, dimensions in microns
ext2spice lvs
ext2spice format ngspice
ext2spice scale off
ext2spice -o ${cell}_lvs.spice

# netlist for post-layout simulation: devices plus all parasitic capacitances
ext2spice cthresh 0
ext2spice -o ${cell}_pex.spice

quit -noprompt
