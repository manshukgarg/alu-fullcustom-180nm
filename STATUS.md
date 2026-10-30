# Project status and handover

**Project:** Design and Performance Analysis of a Full-Custom 8-bit ALU Using Optimized Standard Cells
**Owner:** Manshuk Garg (Thapar Institute), with Aditya Kumar, Gourangi Tyagi, Kashish Goyal
**Deadline:** 27 November 2026 (paper submission to a Scopus-indexed venue)
**Repository:** https://github.com/manshukgarg/alu-fullcustom-180nm

## Fixed decisions

| Item | Decision |
| --- | --- |
| Process | 180 nm (TSMC 0.18 um), VDD 1.8 V; kept over 45 nm for lower risk and to match the lab's LTspice node |
| Transistor models | MOSIS TSMC 0.18 um BSIM3v3.1, lot T14B, renamed `nfet`/`pfet` (`models/tsmc018_t14b.lib`) |
| Layout rules | MOSIS SCMOS SCN6M_SUBM, lambda = 0.1 um, minimum drawn L = 0.2 um (OSU018 kit, `/apps/vlsi/share/qflow/tech/osu018`) |
| Tools | NIELIT ChipCraft lab only: Magic 8.3.629, Netgen, Ngspice 46, Yosys 0.64, Qflow, OpenSTA, iverilog |
| ALU | 8 operations (ADD, SUB, INC, DEC, AND, OR, XOR, NOT), flags C Z V N, bit-sliced, ripple carry |
| Designs compared | D1 conventional static-CMOS cells (schematic); D2 optimized cells, full-custom layout; D3 automated flow (Yosys + Qflow, OSU018 cells) |
| Cell template | 8.0 um row height (OSU018 uses 10 um), shared rails, taps under rails |

## How the work is done

Claude writes the designs and test scripts and pushes them to the repository.
In ChipCraft the owner runs `git pull` and one command per step (`bash stepN_.../run.sh`);
each script prints a one-screen summary, which is sent back as a screenshot.
Every layout is a normal Magic file that opens in the Magic GUI; every circuit is a
normal SPICE netlist; schematics, layout views and plots for the paper and slides are
produced from these files.

## Progress

| Step | Content | Status | Key result |
| --- | --- | --- | --- |
| 0 | Lab check, models, GitHub repository | done | all tools present; ChipCraft has internet |
| 1 | Inverter: simulate, layout, DRC, LVS, post-layout | done | DRC 0, LVS match, delay 95.0 ps schematic / 101.6 ps post-layout |
| 2 | ALU Verilog and automated baseline D3 | done | 524,288-vector test passes; 136 cells, 4,090 um2, 1.59 ns; Qflow layout DRC and LVS clean |
| 3a | 16 candidate cell circuits compared (reference size) | done | TG styles best: XOR2 -51 %, MUX2 -64 %, FA -46 % PDP vs static CMOS |
| 3b | Sizing sweep of every candidate (7 widths x 4 P/N ratios) | running | selects the optimized library |
| 4 | Layout of the selected cells, DRC/LVS, post-layout cell numbers | next | week of 2 Nov |
| 5 | ALU bit slice and 8-bit full-custom layout (D2); conventional ALU netlist (D1) | pending | week of 9 Nov |
| 6 | Post-layout comparison D1/D2/D3: delay, energy per operation, leakage, area, supply/temperature sweep, Monte Carlo | pending | week of 16 Nov |
| 7 | Figures, paper (IEEE format), slides | pending | 21-27 Nov |

## Resuming in a new chat

Paste this as the first message:

> Continue my full-custom 8-bit ALU project. Repository: github.com/manshukgarg/alu-fullcustom-180nm
> (GitHub is connected; clone it and read STATUS.md and README.md first). I run everything in the
> NIELIT ChipCraft lab with git pull and the step scripts, and send screenshots of the summaries.
