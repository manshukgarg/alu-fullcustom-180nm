# Design and Performance Analysis of a Full-Custom 8-bit ALU Using Optimized Standard Cells

Full-custom design of an 8-bit bit-sliced ALU in 180 nm CMOS, built from a custom
standard-cell library whose cells are optimized for minimum power-delay product.
The design is compared post-layout with a conventional static-CMOS implementation
and with an automated standard-cell implementation of the same ALU.

## Technology and tools

| Item | Choice |
| --- | --- |
| Process | TSMC 0.18 um CMOS, VDD = 1.8 V |
| Device models | MOSIS BSIM3v3.1 parameters, lot T14B (`models/tsmc018_t14b.lib`) |
| Layout rules | MOSIS SCMOS SCN6M_SUBM, lambda = 0.1 um (OSU018 kit in Qflow) |
| Layout, DRC, extraction | Magic 8.3 |
| LVS | Netgen |
| Simulation | Ngspice 46 |
| Automated baseline | Yosys, Qflow, OpenSTA with the OSU 0.18 um standard cells |

All tools run in the NIELIT ChipCraft Virtual Lab; the OSU018 kit is read from
`/apps/vlsi/share/qflow/tech/osu018`.

Current progress and the plan are in [STATUS.md](STATUS.md).

![Optimized full adder (24 transistors), generated layout](docs/figures/cells/opt_fa.png)

## Repository layout

| Path | Contents |
| --- | --- |
| `models/` | Transistor models (`nfet`, `pfet`) |
| `tech/magicrc` | Magic start-up file that loads the SCN6M_SUBM.10 rules |
| `layout/` | Layout generator: Magic writer, cell plans, placer and router, rule checker, extractor |
| `mag/` | Generated Magic layouts |
| `step1_flowcheck/` | End-to-end flow check on one inverter |
| `rtl/`, `tb/` | ALU Verilog models (behavioural and bit-sliced) and the exhaustive testbench |
| `step2_rtl_baseline/` | RTL verification and the automated OSU018 baseline (Yosys, Qflow, OpenSTA) |
| `step3_cells/` | Candidate cell circuits (XOR2, MUX2, FA, gates), their Ngspice comparison and sizing sweep |
| `step4_layout/` | Layouts of the optimized and conventional libraries: Magic DRC, Netgen LVS, post-layout simulation |
| `docs/figures/` | Layout views for the report and slides |

## Cell template

Row height 8.0 um (80 lambda), rails 0.6 um wide on metal1 and shared between
mirrored rows, NMOS on the ground side and PMOS in a full-width n-well on the
supply side, substrate and well taps under the rails. Drawn channel length is
0.2 um (2 lambda), the SCMOS SUBM minimum. Transistors up to 2.4 um (NMOS) and
3.2 um (PMOS) fit in one finger; wider ones are folded.

## Cell characterization (Step 3)

Every candidate cell is driven through two X1 inverters and loaded with four X1
inverters (FO4). The input sequence is an Eulerian circuit over all input states,
so every input transition occurs once. The worst delay over all transitions is
measured from the input of the last driver inverter, so the load a cell places on
its driver counts; power includes the drivers. Each candidate is simulated at 8
width scales (k = 0.3 to 2) and 5 P/N ratios (r = 1 to 3); the size with minimum
power-delay product, full output swing and correct logic is selected.

## Cell layout generation (Step 4)

The cells are laid out by `layout/cellgen.py` from their transistor netlists:

* Placement: a column plan per cell (`layout/library.py`) orders the transistors
  of both rows along shared diffusion (Euler paths); strips with transistors wider
  than the row are folded into two or three mirrored copies.
* Routing: a maze router on the lambda grid (polysilicon, metal1, metal2, poly
  contacts and vias) with negotiated congestion: all nets are routed, nets that
  violate spacing are rerouted with rising penalties until none remain. Gaps
  narrower than the spacing rule between parts of one net are filled.
* Pins: every input and output gets a 4 x 4 lambda metal1 pad with free metal2
  above, so the ALU-level router can land a via on it.
* Checks before a cell is written: a rule checker covering the SCN6M_SUBM rules
  of the layers used, with Magic's edge and corner semantics (`layout/drc.py`),
  and an extractor that compares the drawn devices and nets with the netlist
  (`layout/extract.py`). Magic DRC and Netgen LVS in the lab remain the sign-off.

Layouts are regenerated with `python3 step4_layout/gen_cells.py --preview`
(needs numpy and matplotlib, run outside the lab); the lab only verifies them.

## Running the steps (in ChipCraft)

```
git clone https://github.com/manshukgarg/alu-fullcustom-180nm.git
cd alu-fullcustom-180nm
bash step1_flowcheck/run.sh        # inverter flow check
bash step2_rtl_baseline/run.sh     # RTL tests and the automated OSU018 baseline
bash step3_cells/run.sh            # candidate cells at reference size
bash step3_cells/run_sweep.sh      # sizing sweep, selects the optimized library
bash step4_layout/run.sh           # DRC, LVS and post-layout simulation of both libraries
```

Each script prints a one-screen summary and writes it to `out/summary.txt` in its
directory. To view a layout: `cd step4_layout && magic -rcfile ../tech/magicrc ../mag/opt_fa.mag`

## Status

| Step | Content | Result |
| --- | --- | --- |
| 1 | Inverter flow check | DRC clean, LVS match, post-layout delay +6.9 % over schematic |
| 2 | ALU RTL and automated baseline | RTL, bit-sliced RTL and gate netlist pass all 524,288 vectors; bit-sliced RTL: 136 OSU018 cells, 4090 um2, 1.59 ns (OpenSTA); Qflow layout routed, LVS clean, DRC clean (GDS view) |
| 3 | Cell topology comparison and sizing | TG styles lowest PDP; sizing sweep rerun with the corrected script |
| 4 | Layouts of both libraries | 14 cells generated, rule check and connectivity clean; lab verification next |
