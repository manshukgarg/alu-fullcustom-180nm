# Full design-rule check of the Qflow layout with the real OSU018 cell layouts
# (GDS view, not the LEF outlines), listing every error type with its count.
# Run from step2_rtl_baseline/qflow/layout, where Qflow wrote its .magicrc:
#   magic -dnull -noconsole ../../drc_detail.tcl
gds readonly true
gds rescale false
gds read /apps/vlsi/share/qflow/tech/osu018/osu018_stdcells.gds2
load alu8
select top cell
set bbox [box values]
puts "CELL_BBOX $bbox"
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
quit -noprompt
