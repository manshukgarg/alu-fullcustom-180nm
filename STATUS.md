# Project status and handover

**Project:** Design and Performance Analysis of a Full-Custom ALU Using Optimized Standard Cells
(4-bit since the review of 31 October 2026; originally 8-bit)
**Owner:** Manshuk Garg (Thapar Institute), with Aditya Kumar, Gourangi Tyagi, Kashish Goyal
**Deadline:** 27 November 2026 (paper submission to a Scopus-indexed venue)
**Repository:** https://github.com/manshukgarg/alu-fullcustom-180nm

## Review of 31 October 2026

* The ALU is reduced from 8 to 4 bits; the time saved goes into novelty and results, so that the
  work is publishable and can be defended at M.Tech level.
* Novelty is expected at transistor level (new 2- and 3-input cells with a clear circuit idea);
  working at 180 nm is not new in itself.
* Recent literature to be read and cited; two papers were selected as the starting point:
  Azimi, De Sio, Sterpone, IEEE TVLSI 29(8), 2021, and Cui, Vacca, Sterpone, Azimi, IEEE NorCAS 2025.
* Work division: Manshuk Garg runs the automated (Verilog) flow and every ChipCraft run;
  Aditya Kumar, Gourangi Tyagi and Kashish Goyal design the cells and the full-custom ALU.
* Novelty direction under consideration: radiation-aware low-power cells and a selectively
  hardened ALU. Not yet presented to the professor (as of 9 November).

## Decisions of 9 November 2026

* The teammates design their cells in LTspice with the project's 180 nm models
  (conventions in `docs/ltspice_cells.md`).
* Option A first: the project builds its own cell library for the automated flow
  (Liberty, LEF, SPICE, Verilog views) and implements the same ALU with it (design D4),
  so the proposed cells are evaluated as a real standard-cell library and the gain of
  the cells is separated from the gain of full-custom layout (Step 5).
* Option B afterwards, only if the teammates and the professor agree: fault injection on
  the synthesized netlist and selective hardening of the most sensitive gates.

## LTspice cell set received on 14 November 2026

* Content: NOT, NAND2, NOR2, AND2, OR2, XOR2, XNOR2, half and full adder, half and full
  subtractor, MUX2 and an 8-bit ALU (AND, OR, XOR, ADD) as SPICE text, with truth tables.
* It could not be used as delivered: generic level-1 transistor models with L = 0.18 um
  instead of the project models, no simulation results (all marked pending), only the
  NOT, NAND2 and NOR2 files run on their own (the others call gates their file does not
  define, the ALU files pass the wrong number of nodes to the inverter), the full-subtractor
  borrow is wrong in 3 of 8 cases, and the ALU is 8-bit with four operations and no flags.
  The circuits are textbook gate-level compositions; none is a new cell.
* What was taken over: its gates have the proportions of the project's static gates at
  k = 0.4, r = 2, so the set was re-entered in the project technology
  (`step3_cells/cellnet.py`): AND2 and OR2 as cells, and the NAND-based XOR (16 T), the
  AND/OR multiplexer (20 T) and the eleven-NAND full adder (44 T) as the gate-level
  reference style of the cell comparison. AND2 and OR2 were added to the library pl018.
* New transistor-level cells: see "ALU-specific cells" below (16 November).

## Decisions of 15 November 2026

* The complete work (cells, ALU, novelty, layout) is done in this repository; the teammates
  receive it as a package of LTspice files (`ltspice_package/`, no repository access).
* Novelty: cells designed for this ALU (3- and more-input cells), not general gates.
* Layout: own cells, hand-mapped ALU placed and routed by Qflow; the comparison with a
  full-custom ALU layout stays at schematic level.
* Ngspice 46 was built in the working environment of the assistant, so cell and ALU
  simulations no longer wait for a lab session. The Step 1 inverter gives 95.04 ps there
  (lab: 95.0 ps). Magic, Netgen, Yosys, Qflow and OpenSTA exist only in the lab.

## ALU-specific cells (16 November 2026)

Two cells that together form one ALU bit (44 transistors), described in `docs/alu_cells.md`:

* **FB4** (`fb4_tg20`, 20 T, library cell `pl_fb4`): P = C0, C1, C2 or C3 for (A, B) = 00, 01,
  10, 11. Four code lines common to all bits select the function of the operand bits.
* **CS** (`cs_tg24`, 24 T, library cell `pl_cs`): CO = CI if P = 1, else A; Y = P if K = 1,
  else P xor CI. Carry multiplexer without a generate signal, and the result selection.
* A decoder of ten library cells sets the code lines from the operation select.
* Known ideas behind them (to be cited, not claimed): the function block of the OM-2 data
  path (Mead and Conway, 1980) and the propagate-steered carry multiplexer with XOR of FPGA
  logic cells. The project's contribution is their combination into two restoring
  transmission-gate standard cells, their sizing and layout in 180 nm, and the measured
  comparison. A search of recent literature for similar cells is still to be done.
* Sizes (Step 3c, minimum PDP): FB4 k 0.4, r 2.5 (450.2 ps, 18.95 fJ); CS k 0.8, r 1.5
  (458.6 ps, 33.64 fJ). Against the same functions composed of pl018 cells: PDP -12 % and
  -18 %, transistors -17 % and -20 %; against static CMOS: PDP -73 % and -64 %.
* Layouts: `pl_fb4` 14.4 x 8.0 um, `pl_cs` 13.6 x 8.0 um, clean in the generator's checks.

## Results of 16 November 2026 (Ngspice 46, before layout)

Files in `results/ngspice46_2026-11-16/`. The lab runs of the same scripts are the reference
for the paper and should reproduce them.

4-bit ALU from each cell set (Step 6; 229 transitions, all correct in every design):

| Design | Cells | Transistors | Worst delay (ps) | Energy per operation (fJ) | Leakage (nW) | Energy x delay (fJ ns) |
| --- | --- | --- | --- | --- | --- | --- |
| gate: gate-level cells of the LTspice set | 60 | 842 | 2925.4 | 2039.6 | 1.41 | 5966.7 |
| conv: conventional static CMOS (D1 schematic) | 60 | 578 | 2979.6 | 3509.8 | 2.02 | 10457.9 |
| opt: minimum-PDP cells (D2 schematic) | 69 | 402 | 2267.5 | 1102.1 | 0.81 | 2499.1 |
| pl: library pl018, inverting multiplexers | 66 | 458 | 2310.7 | 1312.8 | 0.93 | 3033.6 |
| fb: FB4 and CS per bit (proposed) | 28 | 272 | 2076.2 | 870.6 | 0.47 | 1807.5 |

Proposed against conventional: transistors -53 %, delay -30 %, energy -75 %, leakage -76 %,
energy x delay -83 %. Proposed against opt: transistors -32 %, delay -8 %, energy -21 %.

Lab run of Step 6 (ChipCraft, 16 November): all five designs 229/229 correct; energy per
operation and leakage identical to the table; worst delays 2925.4, 2979.3, 2270.8, 2310.4 and
2076.2 ps (gate, conv, opt, pl, fb), within 0.15 % of the table. The lab values are the ones
to quote in the paper.

Sizing sweep (Step 3b, 21 candidates x 40 sizes), minimum-PDP size of every function:

| Function | Selected cell | k | r | tmax (ps) | PDP (fJ) | Static CMOS at k 1, r 2 |
| --- | --- | --- | --- | --- | --- | --- |
| INV | inv_cmos | 0.8 | 2.5 | 149.0 | 9.65 | 152.0 ps, 9.99 fJ |
| NAND2 | nand2_cmos | 0.6 | 3 | 184.9 | 10.62 | 196.1 ps, 12.28 fJ |
| NOR2 | nor2_cmos | 0.6 | 2.5 | 222.6 | 13.36 | 205.7 ps, 13.77 fJ |
| AND2 | and2_cmos | 0.6 | 2.5 | 247.6 | 15.02 | |
| OR2 | or2_cmos | 0.8 | 1.5 | 283.8 | 17.79 | |
| XOR2 | xor_tg8 (library: xor_tgb10, k 0.8, r 1.5, 322.0 ps, 21.94 fJ) | 0.6 | 3 | 260.3 | 20.11 | 365.5 ps, 42.69 fJ |
| MUX2 | mux_tg6 (library: mux_tgb10, k 0.6, r 2, 333.5 ps, 22.98 fJ) | 0.4 | 3 | 250.0 | 16.28 | 401.8 ps, 46.60 fJ |
| MUX2I | muxi_tg8 | 0.6 | 2.5 | 282.1 | 19.38 | 337.4 ps, 36.49 fJ |
| FA | fa_tgab24 | 0.3 | 2.5 | 589.6 | 63.95 | 651.0 ps, 159.44 fJ |

Delays include the input driver (two X1 inverters). These sizes are in
`step4_layout/library.json` and `step5_library/library.json`; the layouts, the library views
and the ALU netlists were regenerated with them. The sizes of the first lab sweep (30 October)
are superseded: its summary mislabelled k and it measured the delay from the cell input.

## First lab run of Step 5 (21 November 2026)

Library cells (Magic DRC, Netgen LVS, characterization from the extracted layouts;
worst arc at 16 fF load and 80 ps input slope):

| Cell | Sites | Area (um2) | T | DRC | LVS | Cin max (fF) | tpd rise/fall (ps) | Leakage (nW) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pl_inv | 3 | 19.2 | 2 | 0 | match | 9.5 | 84/80 | 0.007 |
| pl_buf | 4 | 25.6 | 4 | 0 | match | 12.0 | 131/136 | 0.028 |
| pl_nand2 | 3 | 19.2 | 4 | 0 | match | 10.4 | 107/90 | 0.010 |
| pl_nor2 | 3 | 19.2 | 4 | 0 | match | 11.9 | 117/129 | 0.009 |
| pl_and2 | 5 | 32.0 | 6 | 0 | match | 9.6 | 152/179 | 0.015 |
| pl_or2 | 4 | 25.6 | 6 | 0 | match | 11.0 | 178/177 | 0.015 |
| pl_xor2 | 7 | 44.8 | 10 | 0 | match | 13.5 | 274/269 | 0.016 |
| pl_mux2 | 8 | 51.2 | 10 | 0 | match | 13.8 | 269/313 | 0.012 |
| pl_mux2i | 6 | 38.4 | 8 | 0 | match | 17.1 | 220/206 | 0.009 |
| pl_fa | 18 | 115.2 | 24 | 0 | match | 14.1 | 545/619 | 0.029 |
| pl_fb4 | 18 | 115.2 | 20 | 0 | match | 21.8 | 400/465 | 0.014 |
| pl_cs | 17 | 108.8 | 24 | 0 | match | 26.2 | 414/424 | 0.030 |

Routed ALUs with pl018 (D4) and the proposed ALU:

| | beh | slice | map | fb (proposed) |
| --- | --- | --- | --- | --- |
| Exhaustive and gate-level tests | 2048/2048 | 2048/2048 | 2048/2048 | 2048/2048 |
| Yosys cells, area (um2) | 147, 3219.2 | 89, 2003.2 | 60, 2188.8 | 27, 1395.2 |
| OpenSTA worst delay (ns) | 1.709 | 2.353 | 2.626 | 3.022 |
| Cells placed (Qflow buffers included) | 201 | 116 | 94 | 57 |
| Die (um) | 84.8 x 54.0 | 66.4 x 46.0 | 70.4 x 46.0 | 60.8 x 38.0 |
| Routing | complete | 2 nets failed | 1 net failed | complete |
| Qflow LVS | 5 errors | 4 errors | 27 errors | match |
| Magic DRC with real cells | 1145 | 515 | 800 | 416 |
| Before layout: worst delay (ps), energy (fJ) | 1651.8, 2473.0 | 1887.9, 1863.3 | 2420.3, 1702.2 | 2132.9, 1246.0 |
| After layout: cycles correct | 141/229 | 55/229 | 13/229 | 229/229 |
| After layout: worst delay (ps), energy (fJ), leakage (nW) | not valid | not valid | not valid | 2727.3, 1471.5, 0.69 |

Findings:
* Both ALU-specific cells pass Magic DRC and Netgen LVS; the proposed ALU routes completely,
  matches LVS and is correct after layout (worst delay +27.9 %, energy +18.1 % over its
  pre-layout netlist, which has no Qflow buffers).
* Magic DRC errors of all four ALUs: the well and substrate taps in the rails shared by
  neighbouring rows did not line up (contacts of different cells partly overlapping or
  1-3 lambda apart). Fixed on 21 Nov: one tap per site, centred on it (taps of all cells
  coincide or are 4 lambda apart); `layout/abut_check.py` reproduces the lab errors with
  the old cells and finds none with the new ones. The abstract views did not change.
* beh, slice and map fail after layout: failed routes in slice and map, LVS errors in all
  three and static currents of 0.4-1.1 mW (unconnected or shorted nets). The proposed
  design is not affected. The summaries now list the unreachable pins, failed nets,
  unmatched nets and wrong outputs; the next lab run of Step 5 gives the cause.
* Qflow's fanout buffering (`fanout_options -l 100 -c 20`, as for OSU018) inserts many
  buffers with a single-strength library: fb 27 cells before, 57 placed.

## LTspice package (16 November 2026)

`ltspice_package/` (zip `ALU4_180nm_LTspice.zip`, written by `sim/make_ltspice_package.py`):
model file with LEVEL = 8, five cell files, five ALU netlists, 38 cell decks and three decks
per ALU (function with 32 vectors, slowest transition, energy per operation), expected
results, result tables and a guide. The decks use only statements common to LTspice and
Ngspice; every deck was run with Ngspice 46 and agrees with the project flow. None has been
run in LTspice yet: the first LTspice run is to be compared with `expected_results.txt`.
The package contains no link to this repository.

## Fixed decisions

| Item | Decision |
| --- | --- |
| Process | 180 nm (TSMC 0.18 um), VDD 1.8 V |
| Transistor models | MOSIS TSMC 0.18 um BSIM3v3.1, lot T14B, renamed `nfet`/`pfet` (`models/tsmc018_t14b.lib`) |
| Layout rules | MOSIS SCMOS SCN6M_SUBM, lambda = 0.1 um, minimum drawn L = 0.2 um (OSU018 kit, `/apps/vlsi/share/qflow/tech/osu018`) |
| Tools | NIELIT ChipCraft lab only: Magic 8.3.629, Netgen, Ngspice 46, Yosys 0.64, Qflow, OpenSTA, iverilog |
| ALU | 4 bits, 8 operations (ADD, SUB, INC, DEC, AND, OR, XOR, NOT), flags C V Z N, bit-sliced, ripple carry (`rtl/alu4.v`, `rtl/alu4_slice.v`; the width is a parameter) |
| Designs compared | D1 conventional static-CMOS cells and D2 minimum-PDP cells, same slice, at schematic level; D3 automated flow with the OSU018 cells; D4 the same automated flow with the project library pl018; P the proposed function-block ALU (FB4 and CS per bit), at schematic level and placed and routed with pl018. D3 and D4 each in three versions: `beh` and `slice` synthesized from the behavioural and the bit-sliced RTL, `map` a hand-mapped netlist (slice with inverting multiplexers and the library's full adder, which synthesis cannot use because it has two outputs); P is the hand-mapped netlist `fb` in Step 5 |
| Project library pl018 (automated flow) | Restoring cells only (every output driven by an inverter or a static gate): INV, BUF (output buffer), NAND2, NOR2, AND2, OR2, XOR2 (TG + inverter), MUX2 (TG + two inverters), MUX2I, FA, the ALU-specific cells FB4 and CS, filler; 0.8 x 8.0 um site; pin pads centred on OSU018 routing-track crossings; OSU018 LEF technology section; NLDM Liberty (5 x 5, load x slew) characterized with Ngspice from the extracted layouts |
| Netlist checks without a simulator | `sim/switchsim.py`: switch-level evaluation of transistor netlists, all vectors at once; every cell netlist (`step3_cells/check_netlists.py`) and every generated ALU netlist (`sim/gen_alu.py`, 2048 vectors) is checked before it is committed |
| ALU measurement | `sim/alutb.py`, identical for every design: inputs through two X1 inverters, FO4 loads, 18 full-length carry propagations plus 24 random operand changes per operation, settling delay including glitches, energy per operation from the ALU supply, leakage from 16 DC states (two runs at gmin 1e-12 and 1e-13 S, extrapolated to gmin = 0). The structural ALUs buffer their select lines internally |
| Cell template | 8.0 um row height (OSU018 uses 10 um), shared rails, taps under rails; NMOS up to 2.4 um and PMOS up to 3.2 um per finger |
| Cell metric | Worst delay over every input transition, measured from the input of the last driver inverter (FO4 load); power includes the drivers; selection by minimum PDP with full swing. Cells with more than three inputs (FB4, CS): every change of one input in every state of the others, evaluated from the waveforms (`sim/cellbench.py`) |
| Cell layouts | Generated by `layout/cellgen.py`, checked by `layout/drc.py` and `layout/extract.py` before commit; Magic DRC and Netgen LVS in the lab are the sign-off |

## How the work is done

Claude writes the designs and test scripts and pushes them to the repository.
In ChipCraft the owner runs `git pull` and one command per step (`bash stepN_.../run.sh`);
each script prints a one-screen summary, which is sent back as a screenshot. Steps that need
only Python and Ngspice (3, 3c, 6, the LTspice package) are also run by Claude.
Every layout is a normal Magic file that opens in the Magic GUI; every circuit is a
normal SPICE netlist; schematics, layout views and plots for the paper and slides are
produced from these files. Layouts are generated outside the lab (the generator needs
numpy) and committed; the lab verifies them.

## Progress

| Step | Content | Status | Key result |
| --- | --- | --- | --- |
| 0 | Lab check, models, GitHub repository | done | all tools present; ChipCraft has internet |
| 1 | Inverter: simulate, layout, DRC, LVS, post-layout | done | DRC 0, LVS match, delay 95.0 ps schematic / 101.6 ps post-layout |
| 2, 8-bit | ALU Verilog and automated baseline (30 Oct) | done, superseded | 524,288-vector test passes; 136 cells, 4,090 um2, 1.59 ns; Qflow layout DRC and LVS clean |
| 2, 4-bit | Automated flow D3, complete: netlist and gate-level tests, Yosys, OpenSTA, Qflow, DRC with real cells, transistor-level extraction, post-layout ALU simulation, for `beh`, `slice` and `map` | scripts ready (15 Nov) | lab run of `step2_rtl_baseline/run.sh` next |
| 3a | 16 candidate cell circuits compared (reference size) | done (30 Oct) | TG styles best: XOR2 -51 %, MUX2 -64 %, FA -46 % PDP vs static CMOS; 5 candidates added on 15 Nov (AND2, OR2 and the gate-level XOR, MUX, FA), measured with the sweep |
| 3b | Sizing sweep of every candidate (21 candidates, 8 widths x 5 P/N ratios) | done; the lab run of 21 Nov gives identical results | sizes above; `run_cells.py --resume` continues an interrupted sweep |
| 3c | ALU-specific cells FB4 and CS: sizing and comparison with composed library cells (`step3_cells/run_alu_cells.sh`) | done; the lab run of 16 Nov gives identical results | FB4 k 0.4, r 2.5; CS k 0.8, r 1.5 |
| 4 | Layouts of both cell libraries, DRC/LVS, post-layout cell numbers | 13 of 14 generated, optimized cells regenerated with the final sizes (16 Nov) | conventional full adder outstanding; `opt_fa` is laid out on the placement grid (the free-width placement does not route at k 0.3); lab verification pending |
| 5 | Project cell library pl018 and the automated ALU with it, D4, and the proposed ALU P: cell DRC/LVS, Liberty characterization, Yosys, Qflow, DRC with real cells, post-layout ALU simulation, comparison with D3 | first lab run 21 Nov; rerun with the tap fix next | all 13 cells DRC 0 and LVS match; proposed ALU routed, LVS match, correct after layout; ALU DRC errors from the rail taps fixed; beh, slice and map fail after layout (cause pending, see above) |
| 6 | 4-bit ALU at transistor level from each cell set, before layout (`step6_alu_schematic`): gate-level, conventional (D1), minimum-PDP (D2), pl018, proposed (P) | done, confirmed in the lab (16 Nov) | table above |
| 6b | Full-custom layout of the ALU (D1, D2) | not planned | the laid-out designs of the paper are D3, D4 and P (decision of 15 Nov) |
| 7 | Comparison of all designs after layout with `sim/alutb.py`: delay, energy per operation, leakage, area; supply and temperature sweep; Monte Carlo | pending | after the lab runs of Steps 2 and 5 |
| 8 | Figures, paper (IEEE format), slides | pending | 21-27 Nov |

## Step 5: how the library is made

`step5_library/gen_library.py` (run outside the lab, needs numpy) lays out every cell of
`step5_library/library.json` in grid mode, writes `mag/pl_*.mag`, caches the geometry of
every net in `step5_library/build/`, and writes the views: `tech/pl018/pl018_cells.lef`
(pins are the complete metal of each pin net, internal nets are obstructions),
`pl018_cells.sp`, `pl018_cells.v` and `step5_library/cells.json`. In the lab,
`step5_library/run.sh` verifies the cells, characterizes them into
`tech/pl018/pl018_cells.lib` and runs the automated flow with `QFLOW_TECH_DIR=tech/pl018`.
The sizes in `library.json` are those of the line "Automated-flow library (restoring
outputs ...)" of the Step 3b summary and, for `pl_fb4` and `pl_cs`, of Step 3c.

## Lab order and expected results (as of 16 November)

```
git pull
bash step6_alu_schematic/run.sh    # 10 min, needs only Python and Ngspice
bash step3_cells/run_alu_cells.sh  # 5-10 min, needs only Python and Ngspice
bash step2_rtl_baseline/run.sh     # 15-25 min
bash step5_library/run.sh          # 30-40 min, after Step 2 (it compares with it)
bash step3_cells/run_sweep.sh      # 20-30 min, last (repeats the sweep for the record)
```

* Step 6 must reproduce `results/ngspice46_2026-11-16/step6_summary.txt`; Step 3c
  `step3c_alu_cells_summary.txt` with "alu_cells.json: same" for both cells; Step 3b
  `step3b_sweep_summary.txt`.
* Steps 2 and 5: all tests 2048/2048; Qflow routing complete and LVS match for every design;
  Magic DRC 0; every transistor-level column correct. Step 5 also reports DRC and LVS of the
  13 library cells, among them the first lab check of `pl_fb4` and `pl_cs`.
* `map` and `fb` are the first Qflow runs on hand-mapped netlists; if Qflow rejects them,
  the columns `beh` and `slice` are unaffected.
* None of the Step 2 and Step 5 scripts has run on the lab tools yet. They were run end to
  end outside the lab against stand-ins for Magic, Netgen, Yosys, Qflow and OpenSTA that
  reproduce the file formats, which checks paths, formats and the summaries, not the tools.

## Resuming in a new chat

Paste this as the first message:

> Continue my full-custom ALU project (4-bit since 31 Oct). Repository: github.com/manshukgarg/alu-fullcustom-180nm
> (GitHub is connected; clone it and read STATUS.md and README.md first). I run everything in the
> NIELIT ChipCraft lab with git pull and the step scripts, and send screenshots of the summaries.
