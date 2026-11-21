# Design-rule check and extraction of one cell for the demonstration (batch mode).
# Started by demo/show.sh from demo/out/magic with the cell in DEMO_CELL:
#   magic -dnull -noconsole -rcfile ../../../tech/magicrc ../../magic_check.tcl
set cell $::env(DEMO_CELL)
load ../../../mag/$cell -force
select top cell
set bbox [box values]
if {[lindex $bbox 2] <= [lindex $bbox 0]} {
    puts "ERROR: cell $cell is empty or did not load"
    quit -noprompt
}
drc euclidean on
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
ext2spice lvs
ext2spice format ngspice
ext2spice scale off
ext2spice -o ${cell}_lvs.spice
puts "EXTRACTED ${cell}_lvs.spice"
quit -noprompt
