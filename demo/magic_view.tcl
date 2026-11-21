# Opens one cell layout in the Magic window for the demonstration.
# Started by demo/show.sh from demo/out/magic with the cell in DEMO_CELL:
#   magic -rcfile ../../../tech/magicrc ../../magic_view.tcl
set cell $::env(DEMO_CELL)
load ../../../mag/$cell -force
select top cell
expand
view
select clear
drc on
puts ""
puts "Cell $cell loaded: rails vdd (top) and gnd (bottom), PMOS in the n-well above, NMOS below."
puts "Useful commands in this console:  drc why   (explains a highlighted rule error)"
puts "                                   see no metal2 / see metal2   (hide or show a layer)"
puts "Mouse: left and right button set the box corners, middle button paints; 'v' zooms to fit."
