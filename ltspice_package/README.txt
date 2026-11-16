4-bit ALU in 180 nm CMOS: cells, ALU netlists and test decks for LTspice
========================================================================
Project: Design and Performance Analysis of a Full-Custom 4-bit ALU Using Optimized
Standard Cells. Package of 16 November 2026.

The package holds the transistor-level circuits of the project in a form that runs
directly in LTspice: five cell sets, the 4-bit ALU built from each of them, and a test
deck with expected results for every cell and every ALU.

1. Files
--------
  tsmc018.lib                 transistor models (TSMC 0.18 um, BSIM3v3, devices nfet, pfet)
  cells_gate.lib              gate-level cells: XOR, multiplexer and full adder from NAND2,
                              NOR2 and inverters (the cell set of the LTspice deliverable
                              of 14 November, re-entered with the 180 nm models)
  cells_conv.lib              conventional static CMOS cells, reference size
  cells_opt.lib               minimum-PDP cells of the sizing sweep (transmission-gate
                              XOR, multiplexers and full adder)
  cells_pl.lib                cells of the project standard-cell library pl018 as laid out
  cells_alu.lib               the two ALU-specific cells: function block pl_fb4 and
                              carry-sum cell pl_cs (section 6)
  alu4_<design>.lib           the 4-bit ALU, one file per design (section 5)
  tb_<cell>.cir               test deck of one cell (38 decks)
  tb_alu4_<design>_function.cir   function test, 32 vectors, results as decimal words
  tb_alu4_<design>_delay.cir      slowest transition of the design
  tb_alu4_<design>_energy.cir     energy per operation (192 random operand changes)
  expected_results.txt        measured values of every deck (Ngspice 46)
  results_cells.csv, results_alu.csv   the tables of sections 4 and 5

2. Technology and conventions
-----------------------------
  Supply 1.8 V, 27 C. Channel length 0.2 um for every transistor. Model names nfet and
  pfet; the model file uses LEVEL = 8, the BSIM3v3 level of LTspice and Ngspice.
  Every source and drain carries the junction of a 0.5 um long diffusion (ad, as, pd, ps).
  Cell pins: inputs, outputs, vdd, vss. Sizes: k scales all widths of a cell (k = 1:
  inverter with Wn = 1.0 um), r is the ratio Wp / Wn; widths are rounded to 0.1 um and
  not smaller than 0.4 um.
  Test conditions of every deck: each input is driven through two inverters of the
  reference size (X1: Wn 1.0 um, Wp 2.0 um), each output drives four X1 inverters (FO4).
  Delays are measured between 50 % points, from the input of the last driver inverter,
  so the loading of the driver by the cell input is part of the delay; the power of a
  cell deck includes the two driver inverters of every input.

3. Running a deck in LTspice
----------------------------
  1. Extract the zip and keep all files in one folder (the decks include the other
     files by name).
  2. LTspice: File > Open, file type 'Netlists', select a tb_*.cir file.
  3. Simulate > Run.
  4. Waveforms: Plot Settings > Add Trace. Node names: cell pins as in the cell file
     (A, B, Y, ...), ALU pins a_0 .. a_3, b_0 .. b_3, s_0 .. s_2, y_0 .. y_3, c, v, z, n.
     The ALU decks also provide the words V(aw), V(bw), V(sw), V(yw), V(fw): operands,
     operation, result and flags as decimal numbers (1 V = 1).
  5. Measured values: View > SPICE Error Log. The header of every deck explains its
     measurements and states the expected values; expected_results.txt lists them all.
  The numbers of this package were obtained with Ngspice 46, the simulator of the
  project's layout flow; every deck was run there and agrees with the project scripts.
  The decks contain only statements common to LTspice and Ngspice. LTspice evaluates
  BSIM3 at version 3.3 and has its own time-step control, so its values can differ
  from expected_results.txt by a few percent; the first LTspice run of a deck should be
  compared with that file.

4. Cells
--------
  Worst delay over all input transitions, average power including the input drivers,
  PDP = power x worst delay (values of the cell decks). T: transistors.

  cells_gate.lib
  cell          T     k    r  delay (ps)  power (uW)  PDP (fJ)  circuit
  gate_inv      2   0.4    2       240.8       57.22     13.78  static CMOS
  gate_buf      4   0.4    2       218.5       68.56     14.98  static CMOS, two inverters
  gate_nand2    4   0.4    2       281.2       50.39     14.17  static CMOS
  gate_nor2     4   0.4    2       293.6       52.13     15.31  static CMOS
  gate_and2     6   0.4    2       308.7       53.15     16.41  static CMOS, NAND2 + inverter
  gate_or2      6   0.4    2       338.0       54.91     18.56  static CMOS, NOR2 + inverter
  gate_xor2    16   0.4    2       460.5       84.18     38.77  gate level, four NAND2
  gate_mux2    20   0.4    2       498.3       86.37     43.04  gate level, inverter + two AND2 + OR2
  gate_fa      44   0.4    2       769.3      173.68    133.61  gate level, eleven NAND2

  cells_conv.lib
  cell          T     k    r  delay (ps)  power (uW)  PDP (fJ)  circuit
  conv_inv      2     1    2       152.2       65.82     10.01  static CMOS
  conv_buf      4     1    2       188.6       92.95     17.53  static CMOS, two inverters
  conv_nand2    4     1    2       196.2       62.72     12.31  static CMOS
  conv_nor2     4     1    2       205.8       67.04     13.80  static CMOS
  conv_and2     6     1    2       236.3       69.41     16.40  static CMOS, NAND2 + inverter
  conv_or2      6     1    2       271.5       73.76     20.02  static CMOS, NOR2 + inverter
  conv_xor2    12     1    2       365.9      116.93     42.78  static CMOS, input inverters
  conv_mux2    12     1    2       402.1      116.12     46.69  static CMOS, AOI22 + inverter
  conv_fa      28     1    2       651.1      245.04    159.56  mirror adder (static CMOS)

  cells_opt.lib
  cell          T     k    r  delay (ps)  power (uW)  PDP (fJ)  circuit
  opt_inv       2   0.8  2.5       149.2       64.86      9.68  static CMOS
  opt_buf       4     1  2.5       194.2       99.47     19.32  static CMOS, two inverters
  opt_nand2     4   0.6    3       184.9       57.53     10.64  static CMOS
  opt_nor2      4   0.6  2.5       222.9       60.13     13.40  static CMOS
  opt_xor2      8   0.6    3       260.5       77.38     20.16  transmission gate, unbuffered
  opt_mux2      6   0.4    3       250.3       65.24     16.33  transmission gate, unbuffered
  opt_mux2i     8   0.6  2.5       282.5       68.82     19.44  transmission gate + output inverter
  opt_fa       24   0.3  2.5       589.8      108.60     64.06  transmission-gate adder, inverted internals, buffered outputs

  cells_pl.lib
  cell          T     k    r  delay (ps)  power (uW)  PDP (fJ)  circuit
  pl_inv        2   0.8  2.5       149.2       64.86      9.68  static CMOS
  pl_buf        4     1  2.5       194.0       99.78     19.36  static CMOS, two inverters
  pl_nand2      4   0.6    3       184.9       57.53     10.64  static CMOS
  pl_nor2       4   0.6  2.5       222.9       60.13     13.40  static CMOS
  pl_and2       6   0.6  2.5       247.8       60.77     15.06  static CMOS, NAND2 + inverter
  pl_or2        6   0.8  1.5       284.4       62.79     17.86  static CMOS, NOR2 + inverter
  pl_xor2      10   0.8  1.5       322.3       68.26     22.00  transmission gate + output inverter
  pl_mux2      10   0.6    2       334.3       69.04     23.08  transmission gate + two inverters
  pl_mux2i      8   0.6  2.5       282.5       68.82     19.44  transmission gate + output inverter
  pl_fa        24   0.3  2.5       589.8      108.60     64.06  transmission-gate adder, inverted internals, buffered outputs

  cells_alu.lib
  cell          T     k    r  delay (ps)  power (uW)  PDP (fJ)  circuit
  pl_fb4       20   0.4  2.5       450.2       42.08     18.95  function block: 4:1 TG tree selected by the operands, restored output
  pl_cs        24   0.8  1.5       458.6       73.36     33.64  carry-sum cell: TG carry multiplexer and TG sum/result selection, restored outputs

  pl_fb4 and pl_cs have six and four inputs; their decks apply every change of one input
  in every state of the other inputs (384 and 64 transitions). The other decks apply
  every transition between two input states.

5. The 4-bit ALU
----------------
  Inputs a_3..a_0, b_3..b_0, operation select s_2 s_1 s_0; outputs y_3..y_0 and the flags
  c, v, z, n.
    s = 000 ADD  y = a + b        100 AND  y = a and b
        001 SUB  y = a - b        101 OR   y = a or b
        010 INC  y = a + 1        110 XOR  y = a xor b
        011 DEC  y = a - 1        111 NOT  y = not a
  c: carry out (1 = no borrow for SUB and DEC); v: signed overflow; z: y = 0; n: y_3.
  c and v are 0 for the logic operations.

  Designs (subcircuit alu4_<design> in alu4_<design>.lib):
    gate  cells_gate.lib. Per bit: XOR and multiplexer for the second operand, full
          adder, AND, OR, XOR, NOT, and four 2:1 multiplexers selecting the result.
    conv  cells_conv.lib, same structure.
    opt   cells_opt.lib, same structure.
    pl    cells_pl.lib; same function with inverting multiplexers, which need no output
          inverter (NAND, NOR and XNOR in place of AND, OR and XOR).
    fb    proposed design: per bit one function block pl_fb4 and one carry-sum cell
          pl_cs (section 6); a decoder of ten library cells, shared by the four bits,
          and the flag logic use cells_pl.lib.
  In every design the select lines are buffered inside the ALU.

  Results (project test: 229 transitions; all outputs correct in every design)
  design   cells  transistors  delay (ps)  energy (fJ) leak (nW)      E x D
  gate        60          842      2925.4       2039.6      1.41     5966.7
  conv        60          578      2979.6       3509.8      2.02    10457.9
  opt         69          402      2267.5       1102.1      0.81     2499.1
  pl          66          458      2310.7       1312.8      0.93     3033.6
  fb          28          272      2076.2        870.6      0.47     1807.5

  Against the conventional design (conv):
  design   transistors       delay       energy   leakage      E x D
  gate           +46 %        -2 %        -42 %     -30 %      -43 %
  opt            -30 %       -24 %        -69 %     -60 %      -76 %
  pl             -21 %       -22 %        -63 %     -54 %      -71 %
  fb             -53 %       -30 %        -75 %     -76 %      -83 %

  delay    largest settling delay over the 229 transitions of the test (18 full-length
           carry propagations, 24 random operand changes per operation and the changes
           between them): from the input of the last driver inverter to the last 50 %
           crossing of any output, glitches included. tb_alu4_<design>_delay.cir repeats
           this transition from a settled state and agrees within 0.5 %.
  energy   energy drawn from the ALU supply per operation, mean over the 192 random
           operand changes (tb_alu4_<design>_energy.cir).
  leak     static power, mean over 16 input states.
  E x D    energy x delay in fJ ns.

6. The two ALU-specific cells
-----------------------------
  pl_fb4 (function block, 20 transistors). P = C0, C1, C2 or C3 for (A, B) = 00, 01, 10,
  11: the operand bits select one of four function-code lines through a tree of six
  transmission gates, followed by two inverters that restore the level. The code lines
  are common to all bits and set by the operation, so P is any function of a and b:
      operation    P            C0 C1 C2 C3   carry in   K
      ADD          a xor b       0  1  1  0       0      0
      SUB          a xnor b      1  0  0  1       1      0
      INC          a             0  0  1  1       1      0
      DEC          not a         1  1  0  0       0      0
      AND          a and b       0  0  0  1       -      1
      OR           a or b        0  1  1  1       -      1
      XOR          a xor b       0  1  1  0       -      1
      NOT          not a         1  1  0  0       -      1
  pl_cs (carry-sum cell, 24 transistors). CO = CI if P = 1, else A; Y = P if K = 1, else
  P xor CI. For the arithmetic operations P is the propagate signal; when it is 0 the
  carry out equals the operand bit a, so no generate signal is needed. K = s_2 selects
  the logic result P or the sum.
  One pl_fb4 and one pl_cs form a complete ALU bit (44 transistors) in place of the
  operand logic, full adder, logic gates and result multiplexers of the other designs.

  Against the same functions composed of library cells (FO4, single-input changes):
  circuit                                        T  delay (ps)  power (uW)  PDP (fJ)
  pl_fb4                                        20       450.2       42.08     18.95
  same function, 3 x MUX2, static CMOS          36       688.7      102.77     70.78
  same function, 3 x MUX2I of pl018             24       433.6       49.77     21.58
  pl_cs                                         24       458.6       73.36     33.64
  same function, MUX2+XOR2+MUX2, static         36       614.6      152.67     93.84
  same function, MUX2+XOR2+MUX2 of pl018        30       510.0       80.54     41.08

  Origin of the ideas: a function block steered by four code lines is the ALU principle
  of the OM-2 data path of Mead and Conway (Introduction to VLSI Systems, 1980), there
  in nMOS pass-transistor logic with a precharged carry chain; a carry multiplexer
  steered by the propagate signal with the operand as its second input, followed by an
  XOR for the sum, is the carry logic of FPGA logic cells. The work of this project is
  their combination into two restoring transmission-gate standard cells for a static
  CMOS cell flow, the sizing and layout of these cells in 180 nm, and the measured
  comparison with the conventional cell-based ALU.

