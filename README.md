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

## Repository layout

| Path | Contents |
| --- | --- |
| `models/` | Transistor models (`nfet`, `pfet`) |
| `tech/magicrc` | Magic start-up file that loads the SCN6M_SUBM.10 rules |
| `layout/` | Python layout generator: rule-checked Magic cells on the lambda grid |
| `mag/` | Generated Magic layouts |
| `step1_flowcheck/` | End-to-end flow check on one inverter |
| `rtl/`, `tb/` | ALU Verilog models (behavioural and bit-sliced) and the exhaustive testbench |
| `step2_rtl_baseline/` | RTL verification and the automated OSU018 baseline (Yosys, Qflow, OpenSTA) |
| `step3_cells/` | Candidate cell circuits (XOR2, MUX2, FA, gates) and their Ngspice comparison |

## Cell template

Row height 8.0 um (80 lambda), rails 0.6 um wide on metal1 and shared between
mirrored rows, NMOS on the ground side and PMOS in a full-width n-well on the
supply side, substrate and well taps under the rails. Drawn channel length is
0.2 um (2 lambda), the SCMOS SUBM minimum.

## Running Step 1 (in ChipCraft)

```
git clone https://github.com/<user>/alu-fullcustom-180nm.git
cd alu-fullcustom-180nm
bash step1_flowcheck/run.sh
```

The script simulates the inverter schematic, runs Magic DRC and extraction,
compares layout and schematic with Netgen, simulates the extracted layout, and
writes `step1_flowcheck/out/summary.txt`.

To view the layout: `cd step1_flowcheck && magic -rcfile ../tech/magicrc ../mag/inv.mag`

## Status

| Step | Content | Result |
| --- | --- | --- |
| 1 | Inverter flow check | DRC clean, LVS match, post-layout delay +6.9 % over schematic |
| 2 | ALU RTL and automated baseline | RTL, bit-sliced RTL and gate netlist pass all 524,288 vectors; bit-sliced RTL: 136 OSU018 cells, 4090 um2, 1.59 ns (OpenSTA); Qflow layout routed, LVS clean, DRC clean (GDS view) |
| 3 | Cell topology comparison and sizing | in progress |
