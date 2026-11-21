# Opens a routed ALU in the Magic window with the real cell layouts in place of the LEF
# outlines, as the layout checks of Steps 2 and 5 do (demo/show.sh chip-magic).
# Run from <qflow directory>/layout:  magic ../../../demo/magic_chip.tcl
if {[file exists pl_cells.tcl]} {
    # Step 5: the project library pl018 (cell names and mag/ path written by run.sh)
    source pl_cells.tcl
    foreach c $PL_CELLS {
        load $PL_MAG/$c
    }
} else {
    # Step 2: the OSU018 cells
    gds readonly true
    gds rescale false
    gds read /apps/vlsi/share/qflow/tech/osu018/osu018_stdcells.gds2
}
load alu4
select top cell
expand
view
select clear
drc on
puts ""
puts "Routed ALU loaded with the cell layouts. 'v' fits the window; 'drc why' in this console"
puts "explains a highlighted rule error; 'expand' / 'unexpand' show or hide the cell contents."
