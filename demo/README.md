# Demonstration views

Views of the project's design data in the tools that produced and checked it, for the
ChipCraft lab desktop: Xschem (schematics), Magic and Netgen (layout, design-rule check,
extraction, layout versus schematic), KLayout (routed chip) and Ngspice (simulation with
waveforms). Every view starts from the files in this repository and the results of the last
lab run of the steps; nothing is precomputed for the demonstration.

```
git pull
bash demo/show.sh                      # list of the views
```

| Command | Tool | Shows |
| --- | --- | --- |
| `bash demo/show.sh schematic fb4` | Xschem | transistor schematic of the function block FB4 (also `cs`) |
| `bash demo/show.sh layout fb4` | Magic, Netgen | new DRC and extraction of the cell, LVS of the extraction against the Xschem schematic, then the layout (any cell: `cs`, `fa`, `xor2`, `opt_fa`, ...) |
| `bash demo/show.sh cell-sim fb4` | Ngspice | the cell with the six function codes of the ALU (`cs`: all 16 input states): table checked against the function, delays, waveforms |
| `bash demo/show.sh chip fb` | KLayout | the routed proposed ALU with the cell layouts (also `beh`, `slice`, `map`, `osu-slice`, ...) |
| `bash demo/show.sh chip-magic fb` | Magic | the same layout in Magic |
| `bash demo/show.sh chip-sim fb` | Ngspice | the netlist extracted from the routed layout (every transistor and parasitic capacitance): 32 vectors, eight operations, checked, waveforms |
| `bash demo/show.sh alu-sim fb` | Ngspice | the ALU from one cell set at transistor level (`fb`, `pl`, `opt`, `conv`, `gate`) |
| `bash demo/show.sh alu-delay fb` | Ngspice | the slowest transition of that ALU, waveforms |
| `bash demo/show.sh results` | terminal | result tables of Steps 3c, 5 and 6 |

The chip views use the layouts of the last run of Step 5 (`fb`, `beh`, `slice`, `map`) and
Step 2 (`osu-*`); `layout` and `cell-sim` use the extracted cells of Step 5 when present.
Simulations accept `--no-plot` for the tables alone.

## Guided tour

`bash demo/tour.sh` opens the views below one after the other (close each window to go on;
`bash demo/tour.sh --list` lists them, `bash demo/tour.sh 4` starts at view 4).

## Suggested order (about ten minutes)

1. `schematic fb4`: the circuit of the new cell; A and B select one of the four function
   bits C0..C3 through two levels of transmission gates.
2. `cell-sim fb4`: the cell computes every ALU function from its code; delay with the
   fan-out-of-four load.
3. `layout fb4`: the drawn layout; DRC 0 and the extraction matches the schematic (LVS).
4. `chip fb`: the 4-bit ALU placed and routed with the project library.
5. `chip-sim fb`: the extracted chip works on all eight operations.
6. `results`: delay, energy, area and transistor count of every design.

## Using the tools

- Xschem: `f` fits the drawing; click a wire and press `k` to highlight its net, `Shift+K`
  clears; `n` writes the netlist, `Shift+A` shows it after netlisting.
- Magic: `v` fits the cell; type `drc why` in the console for a highlighted rule error,
  `see no metal2` / `see metal2` to hide or show a layer.
- KLayout opens with every hierarchy level shown and fitted (settings file `demo/out/klayout/klayoutrc`).
  If the cells appear as empty frames, click once inside the KLayout window, then `*` (Display >
  Full Hierarchy) and `F2` (Display > Zoom Fit); keys typed in the terminal do not reach KLayout;
  layers are switched in the layer panel.
- Ngspice: drag a rectangle in a plot window to zoom; type `quit` in the terminal to close.

## Files

| File | Content |
| --- | --- |
| `show.sh` | the views |
| `xschem/pl_fb4.sch`, `xschem/pl_cs.sch` | schematics of the two ALU-specific cells |
| `xschem/pl018_*.sym`, `xschem/xschemrc` | device and label symbols, Xschem start-up file |
| `tools/schematics.py` | writes the schematics and checks every device against `tech/pl018/pl018_cells.sp` |
| `tools/wave.py` | simulations, checks and waveform windows |
| `tools/facts.py` | facts of a routed design from the logs of the last run |
| `magic_check.tcl`, `magic_view.tcl`, `magic_chip.tcl` | Magic scripts of the layout and chip views |
| `scmos.lyp` | KLayout layer colours for the GDS layers of the SCN6M_SUBM.10 rules |

Output of the views is written to `demo/out/` (not in the repository).
