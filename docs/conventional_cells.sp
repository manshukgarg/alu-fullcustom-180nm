* Conventional static-CMOS reference cells of the project (k = 1, P/N ratio 2)
* TSMC 0.18 um models: .include tsmc018_t14b.lib (models nfet, pfet); L = 0.2 um; VDD = 1.8 V
* Junction areas estimated for a 0.5 um diffusion. Generated from step3_cells/cellnet.py.
* Pin order of every subcircuit: inputs, outputs, vdd, gnd. Functions:
*   inv_cmos     INV        2 transistors, static CMOS; truth (A > Y): 0>1 1>0
*   nand2_cmos   NAND2      4 transistors, static CMOS; truth (A,B > Y): 00>1 01>1 10>1 11>0
*   nor2_cmos    NOR2       4 transistors, static CMOS; truth (A,B > Y): 00>1 01>0 10>0 11>0
*   xor_cmos12   XOR2       12 transistors, static CMOS, input inverters; truth (A,B > Y): 00>0 01>1 10>1 11>0
*   mux_cmos12   MUX2       12 transistors, static CMOS, AOI22 + inverter; truth (A,B,S > Y): 000>0 001>0 010>0 011>1 100>1 101>0 110>1 111>1
*   muxi_cmos10  MUX2I      10 transistors, static CMOS AOI22; truth (A,B,S > Y): 000>1 001>1 010>1 011>0 100>0 101>1 110>0 111>0
*   fa_cmos28    FA         28 transistors, mirror adder (static CMOS); truth (A,B,C > S,CO): 000>00 001>10 010>10 011>01 100>10 101>01 110>01 111>11

.subckt inv_cmos A Y vdd gnd
M0 Y A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends inv_cmos

.subckt nand2_cmos A B Y vdd gnd
M0 Y A x gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M1 x B gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M2 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M3 Y B vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends nand2_cmos

.subckt nor2_cmos A B Y vdd gnd
M0 Y A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y B gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M2 Y A x vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M3 x B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
.ends nor2_cmos

.subckt xor_cmos12 A B Y vdd gnd
M0 An A gnd gnd nfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M1 An A vdd vdd pfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M2 Bn B gnd gnd nfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M3 Bn B vdd vdd pfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M4 Y A n1 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M5 n1 B gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M6 Y An n2 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M7 n2 Bn gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M8 Y An p1 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M9 p1 B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M10 Y A p2 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M11 p2 Bn vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
.ends xor_cmos12

.subckt mux_cmos12 A B S Y vdd gnd
M0 Sn S gnd gnd nfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M1 Sn S vdd vdd pfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M2 Yb A n1 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M3 n1 Sn gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M4 Yb B n2 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M5 n2 S gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M6 Yb A p1 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M7 Yb Sn p1 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M8 p1 B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M9 p1 S vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M10 Y Yb gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M11 Y Yb vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends mux_cmos12

.subckt muxi_cmos10 A B S Y vdd gnd
M0 Sn S gnd gnd nfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M1 Sn S vdd vdd pfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M2 Y A n1 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M3 n1 Sn gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M4 Y B n2 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M5 n2 S gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M6 Y A p1 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M7 Y Sn p1 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M8 p1 B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M9 p1 S vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
.ends muxi_cmos10

.subckt fa_cmos28 A B C S CO vdd gnd
M0 COn A n1 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M1 n1 B gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M2 COn C n2 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M3 n2 A gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M4 n2 B gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M5 COn A p1 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M6 p1 B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M7 COn C p2 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M8 p2 A vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M9 p2 B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M10 Sn A n3 gnd nfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
M11 n3 B n4 gnd nfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
M12 n4 C gnd gnd nfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
M13 Sn COn n5 gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M14 n5 A gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M15 n5 B gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M16 n5 C gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M17 Sn A p3 vdd pfet w=6u l=0.2u ad=3p as=3p pd=13u ps=13u
M18 p3 B p4 vdd pfet w=6u l=0.2u ad=3p as=3p pd=13u ps=13u
M19 p4 C vdd vdd pfet w=6u l=0.2u ad=3p as=3p pd=13u ps=13u
M20 Sn COn p5 vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M21 p5 A vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M22 p5 B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M23 p5 C vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M24 CO COn gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M25 CO COn vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M26 S Sn gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M27 S Sn vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends fa_cmos28
