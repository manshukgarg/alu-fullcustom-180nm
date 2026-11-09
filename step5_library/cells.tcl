# Magic batch script for Step 5: design-rule check and extraction of every library
# cell listed in out/cells.txt. Run from step5_library/out/cells:
#   magic -dnull -noconsole -rcfile ../../../tech/magicrc ../../cells.tcl
set fp [open ../cells.txt r]
set cells [string trim [read $fp]]
close $fp
drc euclidean on
foreach cell $cells {
    load ../../../mag/$cell -force
    select top cell
    set bbox [box values]
    puts "CELL_BBOX $cell $bbox"
    if {[lindex $bbox 2] <= [lindex $bbox 0]} {
        puts "ERROR: cell $cell is empty or did not load"
        continue
    }
    drc check
    drc catchup
    set total 0
    foreach {why boxes} [drc listall why] {
        puts "DRC: $cell: $why ([llength $boxes])"
        incr total [llength $boxes]
    }
    puts "DRC_ERRORS $cell $total"
    extract do local
    extract all
    # netlist for LVS: devices only, dimensions in microns
    ext2spice lvs
    ext2spice format ngspice
    ext2spice scale off
    ext2spice -o ${cell}_lvs.spice
    # netlist for characterization: devices plus all parasitic capacitances
    ext2spice cthresh 0
    ext2spice -o ${cell}_pex.spice
    puts "EXTRACTED $cell"
}
quit -noprompt
