# Cell design in LTspice: project conventions

Cells designed in LTspice use the same transistor models and measurement
conventions as the rest of the project, so that their results can be compared
with the Step 3 cells and so that they can enter the project cell library used
by the automated flow (Step 5).

## Models and devices

| Item | Setting |
| --- | --- |
| Model file | `models/tsmc018_t14b.lib` (TSMC 0.18 um, BSIM3v3.1, MOSIS lot T14B); copy it next to the schematic and add the directive `.include tsmc018_t14b.lib` |
| Transistors | `nmos4` and `pmos4` symbols, value `nfet` and `pfet` (the model names in the file) |
| Bulk | NMOS bulk to `gnd`, PMOS bulk to `vdd` |
| Length | `l=0.2u` (minimum drawn length of the layout rules) |
| Width | multiples of `0.1u`, at least `0.4u`; wider than 2.4 um (NMOS) or 3.2 um (PMOS) is allowed and is folded into fingers in the layout |
| Supply, temperature | 1.8 V, 27 C (`.temp 27`) |

## Measurement (as Step 3)

* Every input is driven through two X1 inverters (Wn 1.0 um, Wp 2.0 um) from an
  ideal pulse source; every output drives four X1 inverters (fan-out of four).
* Every input transition is applied once; the delay of a transition runs from the
  input of the last driver inverter to the 50 % point of the output; the worst
  transition is reported.
* Average power includes the input drivers; PDP = average power x worst delay.
* Output levels must reach within 10 % of the rails.

## What to hand over for each new cell

1. The transistor netlist (View > SPICE Netlist), with pin names `A`, `B`, `C` for
   inputs, `Y` (or `S`, `CO`) for outputs, and `vdd`, `gnd`.
2. The function (truth table) and the transistor sizes.
3. The simulation results (worst delay, average power, PDP) under the conditions above.

From the netlist and the function, the cell is laid out by the project generator,
checked in Magic (DRC, LVS), characterized into the Liberty library and used by the
automated flow (step5_library). Only cells whose outputs are driven by an inverter
or a static gate are used by the automated flow; unbuffered pass-gate cells remain
for the full-custom slice.
