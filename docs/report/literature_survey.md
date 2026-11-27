# Literature survey: papers 2021–2026

The seventeen recent papers of Chapter 2 of the project report, with their DOI links, grouped as in the
report. Each summary gives what the paper reports. The summaries were written from the abstracts and publisher
pages of the papers. The exception is Lee et al. 2021, whose results come from the full text. Read the full paper
before quoting a number that is not in its abstract.

## Logic styles for arithmetic cells

- [Hussain et al. 2022](https://doi.org/10.1049/cds2.12097), *IET Circuits, Devices & Systems* 16(3): 18-transistor
  full-swing hybrid full adder (XOR–XNOR stage, pass transistors, inverters). HSPICE, 16 nm, 0.4–1.0 V. At 0.8 V:
  delay −34.8 %, average power −48.8 % and PDP −66.6 % against the CMOS mirror adder.
- [Sadeghi, Shiri, Rafiee 2022](https://doi.org/10.1109/LES.2021.3108474), *IEEE Embedded Systems Letters* 14(1):
  TG-based full adder with a separate module for a full-swing carry. Both outputs keep a strong drive in ripple-carry
  adders, compressors and multipliers.
- [Arul, Kathirvelu 2024](https://doi.org/10.1007/s10470-023-02217-0), *Analog Integr. Circuits Signal Process.* 119:
  20-transistor hybrid full adder around a 12-transistor XOR–XNOR circuit, GPDK 45 nm: 14.157 µm², 3.582 µW,
  72.66 ps. Cascaded to 4–64-bit ripple-carry adders and checked over corners, voltage, temperature and Monte Carlo.
- [Yin et al. 2023](https://doi.org/10.3390/electronics12153209), *Electronics* 12(15), 3209: 18-transistor
  pass-transistor full adder with post-layout power −13.78 % against a CMOS full adder. An 8-bit signed multiplier
  built from it needs 8 % less power than one synthesized with Design Compiler.
- [Nirmalraj et al. 2023](https://doi.org/10.1007/s00034-022-02287-x), *Circuits Syst. Signal Process.* 42(6):
  10-transistor full adder (4-transistor PTL XOR, two GDI multiplexers), built in ten technologies including
  0.18 µm. At 90 nm: 1.843 µW and 0.605 ns. Extended to a 4-bit adder/subtractor.
- [Sharma, Jhamb 2024](https://doi.org/10.2298/FUEE2402301S), *Facta Universitatis, Electronics and Energetics*
  37(2): XOR–XNOR cells in CMOS, FinFET, CNTFET and FGMOS compared under supply and temperature variation. CNTFET
  gives the lowest delay at small nodes and FGMOS the best power efficiency.

## ALU implementations

- [Subbulakshmi et al. 2023](https://doi.org/10.1016/j.measen.2023.100842), *Measurement: Sensors* 28, 100842:
  ALU-based sliced processor for a filter bank, GDI and modified GDI, 65 nm. GDI uses 91.4 % less power and 65 %
  less area than CMOS; modified GDI saves 77.5 % area.
- [Jyothi, Reddy, Jhamb 2024](https://doi.org/10.1109/ICECSP61809.2024.10698278), ICECSP 2024: ALU in ECRL adiabatic
  logic, total ALU power 3.693 nW at 1.8 V.
- [Kannan Nithin et al. 2024](https://doi.org/10.4108/ew.6035), *EAI Endorsed Trans. Energy Web* 11: 32-bit ALU in
  Cadence gpdk 180 nm. The arithmetic unit is built from 4:1 and 2:1 multiplexers and full adders, and the logic
  unit from a 4:1 multiplexer and gates.
- [Karapothula et al. 2026](https://doi.org/10.1007/978-981-95-1058-0_2), ICSDP 2024, LNEE 1470: transistor-level
  ALU in Cadence, compared at 180, 90 and 45 nm. At 45 nm: 13.29 ps, 0.257 µW.

## Transistor sizing and standard-cell libraries

- [Chen, Nie, Jiao 2022](https://doi.org/10.1109/TVLSI.2022.3151500), *IEEE TVLSI* 30(5): ultralow-voltage
  standard-cell library in 65 nm LP CMOS. Transistor sizes are optimized by threshold-voltage tuning and technology
  feature exploration.
- [Lim et al. 2023](https://doi.org/10.1109/ACCESS.2022.3230897), *IEEE Access* 11: P/N ratio sizing with a
  full-diffusion layout and cell-height tuning for near-threshold operation, 110 nm test chip. The 14-track library
  is up to 4.5 % faster and the 7-track library saves 55 % energy (AHB controller). An 8051 runs at 0.6 V with
  4.3× lower energy than at 1.2 V.
- [Cao, Guo 2024](https://doi.org/10.3390/electronics13224477), *Electronics* 13(22), 4477: optimal P/N width ratio
  derived analytically for minimum worst-case delay under process variation (sub-threshold). At cell level,
  worst-case delay improves by ≥ 8.6 % and EDP by ≥ 7.4 %, at 3.2 % extra energy.

## Cell layout, characterization and open-source flows

- [Ren, Fojtik 2021](https://doi.org/10.1109/DAC18074.2021.9586188), DAC 2021: NVCell, a cell-layout generator
  with reinforcement learning. It gives equal or smaller area for more than 90 % of the single-row cells of an
  industrial library.
- [Lee et al. 2021](https://doi.org/10.1109/TCAD.2020.3037885), *IEEE TCAD* 40(10): SP&R, simultaneous SMT-based
  place and route for cell synthesis, with a complete 7 nm library. Against sequential P&R, metal-2 track usage
  falls about 53 % and total resistance about 12 %.
- [Nishizawa, Nakura 2023](https://doi.org/10.1587/transfun.2022VLP0007), *IEICE Trans. Fundamentals* E106.A(3):
  Libretto, an open-source cell characterizer that generates timing and power models.
- [Edwards, Shalan, Kassem 2021](https://doi.org/10.1109/MDAT.2021.3050000), *IEEE Design & Test* 38(2): a complete
  open-source flow (OpenLane on OpenROAD) produces industrial-quality digital designs, shown on a RISC-V based SoC.
