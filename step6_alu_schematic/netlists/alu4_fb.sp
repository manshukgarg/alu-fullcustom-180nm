* 4-bit ALU, transistor level: function-block slice: FB4 and CS cells per bit, pl018 cells for decoder and flags
* slice architecture: fb; generated and checked by sim/gen_alu.py (all 2048 vectors)
* models: models/tsmc018_t14b.lib (nfet, pfet); pins of alu4: inputs, outputs, vdd, gnd

.subckt pl_xor2 A B Y vdd gnd
M0 A B Xn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 A Bn Xn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M2 Xn Bn An gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 Xn B An vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M4 An A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 An A vdd vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M6 gnd B Bn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 vdd B Bn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M8 Y Xn gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M9 Y Xn vdd vdd pfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
.ends pl_xor2

.subckt pl_buf A Y vdd gnd
M0 Yn A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Yn A vdd vdd pfet w=2.5u l=0.2u ad=1.25p as=1.25p pd=6u ps=6u
M2 gnd Yn Y gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M3 Y Yn gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M4 vdd Yn Y vdd pfet w=2.5u l=0.2u ad=1.25p as=1.25p pd=6u ps=6u
M5 Y Yn vdd vdd pfet w=2.5u l=0.2u ad=1.25p as=1.25p pd=6u ps=6u
.ends pl_buf

.subckt pl_inv A Y vdd gnd
M0 gnd A Y gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M1 vdd A Y vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends pl_inv

.subckt pl_nand2 A B Y vdd gnd
M0 gnd B x gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M1 vdd B Y vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
M2 x A Y gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M3 Y A vdd vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
.ends pl_nand2

.subckt pl_and2 A B Y vdd gnd
M0 Yn A x gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M1 vdd A Yn vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
M2 x B gnd gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M3 Yn B vdd vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
M4 gnd Yn Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M5 vdd Yn Y vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
.ends pl_and2

.subckt pl_nor2 A B Y vdd gnd
M0 gnd A Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M1 Y A x vdd pfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
M2 Y B gnd gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M3 x B vdd vdd pfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
.ends pl_nor2

.subckt pl_mux2i A B S Y vdd gnd
M0 Sn S gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Sn S vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M2 gnd M Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M3 vdd M Y vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
M4 A Sn M gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 A S M vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M6 M S B gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 M Sn B vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends pl_mux2i

.subckt pl_fb4 A B C0 C1 C2 C3 P vdd gnd
M0 C1 B u0 gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 C1 Bn u0 vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M2 u0 Bn C0 gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 u0 B C0 vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M4 C2 Bn u1 gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 C2 B u1 vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M6 u1 B C3 gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 u1 Bn C3 vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M8 u0 An x gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M9 u0 A x vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M10 x A u1 gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M11 x An u1 vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M12 An A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M13 An A vdd vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M14 gnd B Bn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M15 vdd B Bn vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M16 Pn x gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M17 Pn x vdd vdd pfet w=0.5u l=0.2u ad=0.25p as=0.25p pd=2u ps=2u
M18 gnd Pn P gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M19 vdd Pn P vdd pfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
.ends pl_fb4

.subckt pl_cs P A CI K CO Y vdd gnd
M0 A Pn cx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 A P cx vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M2 cx P CI gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 cx Pn CI vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M4 CI P xn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 CI Pn xn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M6 xn Pn CIn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 xn P CIn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M8 CIn CI gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M9 CIn CI vdd vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M10 gnd P Pn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M11 vdd P Pn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M12 Pn K yn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M13 Pn Kn yn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M14 yn Kn xn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M15 yn K xn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M16 Kn K gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M17 Kn K vdd vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M18 gnd cx COn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M19 vdd cx COn vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M20 CO COn gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M21 CO COn vdd vdd pfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M22 gnd yn Y gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M23 vdd yn Y vdd pfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
.ends pl_cs

.subckt alu4 a_0 a_1 a_2 a_3 b_0 b_1 b_2 b_3 s_0 s_1 s_2 y_0 y_1 y_2 y_3 c v z n vdd gnd
Xu_xor21 s_1 s_0 cy_0 vdd gnd pl_xor2
Xu_buf1 s_2 s2b vdd gnd pl_buf
Xu_inv1 cy_0 xn vdd gnd pl_inv
Xu_inv2 s_1 s1n vdd gnd pl_inv
Xu_nand21 s2b s1n dt vdd gnd pl_nand2
Xu_and21 s_0 dt fc0 vdd gnd pl_and2
Xu_nor21 s_1 s_0 dnor vdd gnd pl_nor2
Xu_mux2i1 cy_0 dnor s2b fc1 vdd gnd pl_mux2i
Xu_mux2i2 s_0 xn s2b fc2 vdd gnd pl_mux2i
Xu_mux2i3 xn s_1 s2b fc3 vdd gnd pl_mux2i
Xu_fb41 a_0 b_0 fc0 fc1 fc2 fc3 p_0 vdd gnd pl_fb4
Xu_cs1 p_0 a_0 cy_0 s2b cy_1 y_0 vdd gnd pl_cs
Xu_fb42 a_1 b_1 fc0 fc1 fc2 fc3 p_1 vdd gnd pl_fb4
Xu_cs2 p_1 a_1 cy_1 s2b cy_2 y_1 vdd gnd pl_cs
Xu_fb43 a_2 b_2 fc0 fc1 fc2 fc3 p_2 vdd gnd pl_fb4
Xu_cs3 p_2 a_2 cy_2 s2b cy_3 y_2 vdd gnd pl_cs
Xu_fb44 a_3 b_3 fc0 fc1 fc2 fc3 p_3 vdd gnd pl_fb4
Xu_cs4 p_3 a_3 cy_3 s2b cy_4 y_3 vdd gnd pl_cs
Xu_inv3 cy_4 cyn vdd gnd pl_inv
Xu_nor22 s2b cyn c vdd gnd pl_nor2
Xu_xor22 cy_3 cy_4 vxn_n vdd gnd pl_xor2
Xu_inv4 vxn_n vxn vdd gnd pl_inv
Xu_nor23 s2b vxn v vdd gnd pl_nor2
Xu_nor24 y_0 y_1 zn_0 vdd gnd pl_nor2
Xu_nor25 y_2 y_3 zn_1 vdd gnd pl_nor2
Xu_and22 zn_0 zn_1 z vdd gnd pl_and2
Xu_inv5 y_3 nn vdd gnd pl_inv
Xu_inv6 nn n vdd gnd pl_inv
.ends alu4
