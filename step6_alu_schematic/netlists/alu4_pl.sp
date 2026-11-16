* 4-bit ALU, transistor level: automated-flow library pl018 as laid out, inverting-multiplexer slice
* slice architecture: inv; generated and checked by sim/gen_alu.py (all 2048 vectors)
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

.subckt pl_fa A B C S CO vdd gnd
M0 A Bn P gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 A B P vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M2 P B An gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 P Bn An vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M4 Bn B gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 Bn B vdd vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M6 gnd A An gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 vdd A An vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M8 An Pn COx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M9 An P COx vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M10 COx P Cn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M11 COx Pn Cn vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M12 Cn Pn Sx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M13 Cn P Sx vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M14 Sx P C gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M15 Sx Pn C vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M16 Cn C gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M17 Cn C vdd vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M18 gnd P Pn gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M19 vdd P Pn vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M20 S Sx gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M21 S Sx vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M22 gnd COx CO gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M23 vdd COx CO vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends pl_fa

.subckt pl_nand2 A B Y vdd gnd
M0 gnd B x gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M1 vdd B Y vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
M2 x A Y gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M3 Y A vdd vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
.ends pl_nand2

.subckt pl_nor2 A B Y vdd gnd
M0 gnd A Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M1 Y A x vdd pfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
M2 Y B gnd gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M3 x B vdd vdd pfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
.ends pl_nor2

.subckt pl_and2 A B Y vdd gnd
M0 Yn A x gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M1 vdd A Yn vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
M2 x B gnd gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M3 Yn B vdd vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
M4 gnd Yn Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M5 vdd Yn Y vdd pfet w=1.5u l=0.2u ad=0.75p as=0.75p pd=4u ps=4u
.ends pl_and2

.subckt alu4 a_0 a_1 a_2 a_3 b_0 b_1 b_2 b_3 s_0 s_1 s_2 y_0 y_1 y_2 y_3 c v z n vdd gnd
Xu_xor21 s_1 s_0 cy_0 vdd gnd pl_xor2
Xu_buf1 s_2 s2b vdd gnd pl_buf
Xu_buf2 s_0 s0b_0 vdd gnd pl_buf
Xu_buf3 s_0 s0b_1 vdd gnd pl_buf
Xu_buf4 s_1 s1b_0 vdd gnd pl_buf
Xu_buf5 s_1 s1b_1 vdd gnd pl_buf
Xu_inv1 s0b_0 s0n_0 vdd gnd pl_inv
Xu_inv2 s0b_1 s0n_1 vdd gnd pl_inv
Xu_inv3 b_0 bn_0 vdd gnd pl_inv
Xu_xor22 bn_0 s0b_0 bxsn_0 vdd gnd pl_xor2
Xu_xor23 a_0 bn_0 lxn_0 vdd gnd pl_xor2
Xu_mux2i1 bxsn_0 s0n_0 s1b_0 bx_0 vdd gnd pl_mux2i
Xu_fa1 a_0 bx_0 cy_0 sum_0 cy_1 vdd gnd pl_fa
Xu_nand21 a_0 b_0 lnand_0 vdd gnd pl_nand2
Xu_nor21 a_0 b_0 lnor_0 vdd gnd pl_nor2
Xu_mux2i2 lnand_0 lnor_0 s0b_0 m0_0 vdd gnd pl_mux2i
Xu_mux2i3 lxn_0 a_0 s0b_0 m1_0 vdd gnd pl_mux2i
Xu_mux2i4 m0_0 m1_0 s1b_0 lgn_0 vdd gnd pl_mux2i
Xu_inv4 sum_0 sumn_0 vdd gnd pl_inv
Xu_mux2i5 sumn_0 lgn_0 s2b y_0 vdd gnd pl_mux2i
Xu_inv5 b_1 bn_1 vdd gnd pl_inv
Xu_xor24 bn_1 s0b_0 bxsn_1 vdd gnd pl_xor2
Xu_xor25 a_1 bn_1 lxn_1 vdd gnd pl_xor2
Xu_mux2i6 bxsn_1 s0n_0 s1b_0 bx_1 vdd gnd pl_mux2i
Xu_fa2 a_1 bx_1 cy_1 sum_1 cy_2 vdd gnd pl_fa
Xu_nand22 a_1 b_1 lnand_1 vdd gnd pl_nand2
Xu_nor22 a_1 b_1 lnor_1 vdd gnd pl_nor2
Xu_mux2i7 lnand_1 lnor_1 s0b_0 m0_1 vdd gnd pl_mux2i
Xu_mux2i8 lxn_1 a_1 s0b_0 m1_1 vdd gnd pl_mux2i
Xu_mux2i9 m0_1 m1_1 s1b_0 lgn_1 vdd gnd pl_mux2i
Xu_inv6 sum_1 sumn_1 vdd gnd pl_inv
Xu_mux2i10 sumn_1 lgn_1 s2b y_1 vdd gnd pl_mux2i
Xu_inv7 b_2 bn_2 vdd gnd pl_inv
Xu_xor26 bn_2 s0b_1 bxsn_2 vdd gnd pl_xor2
Xu_xor27 a_2 bn_2 lxn_2 vdd gnd pl_xor2
Xu_mux2i11 bxsn_2 s0n_1 s1b_1 bx_2 vdd gnd pl_mux2i
Xu_fa3 a_2 bx_2 cy_2 sum_2 cy_3 vdd gnd pl_fa
Xu_nand23 a_2 b_2 lnand_2 vdd gnd pl_nand2
Xu_nor23 a_2 b_2 lnor_2 vdd gnd pl_nor2
Xu_mux2i12 lnand_2 lnor_2 s0b_1 m0_2 vdd gnd pl_mux2i
Xu_mux2i13 lxn_2 a_2 s0b_1 m1_2 vdd gnd pl_mux2i
Xu_mux2i14 m0_2 m1_2 s1b_1 lgn_2 vdd gnd pl_mux2i
Xu_inv8 sum_2 sumn_2 vdd gnd pl_inv
Xu_mux2i15 sumn_2 lgn_2 s2b y_2 vdd gnd pl_mux2i
Xu_inv9 b_3 bn_3 vdd gnd pl_inv
Xu_xor28 bn_3 s0b_1 bxsn_3 vdd gnd pl_xor2
Xu_xor29 a_3 bn_3 lxn_3 vdd gnd pl_xor2
Xu_mux2i16 bxsn_3 s0n_1 s1b_1 bx_3 vdd gnd pl_mux2i
Xu_fa4 a_3 bx_3 cy_3 sum_3 cy_4 vdd gnd pl_fa
Xu_nand24 a_3 b_3 lnand_3 vdd gnd pl_nand2
Xu_nor24 a_3 b_3 lnor_3 vdd gnd pl_nor2
Xu_mux2i17 lnand_3 lnor_3 s0b_1 m0_3 vdd gnd pl_mux2i
Xu_mux2i18 lxn_3 a_3 s0b_1 m1_3 vdd gnd pl_mux2i
Xu_mux2i19 m0_3 m1_3 s1b_1 lgn_3 vdd gnd pl_mux2i
Xu_inv10 sum_3 sumn_3 vdd gnd pl_inv
Xu_mux2i20 sumn_3 lgn_3 s2b y_3 vdd gnd pl_mux2i
Xu_inv11 cy_4 cyn vdd gnd pl_inv
Xu_nor25 s2b cyn c vdd gnd pl_nor2
Xu_xor210 cy_3 cy_4 vxn_n vdd gnd pl_xor2
Xu_inv12 vxn_n vxn vdd gnd pl_inv
Xu_nor26 s2b vxn v vdd gnd pl_nor2
Xu_nor27 y_0 y_1 zn_0 vdd gnd pl_nor2
Xu_nor28 y_2 y_3 zn_1 vdd gnd pl_nor2
Xu_and21 zn_0 zn_1 z vdd gnd pl_and2
Xu_inv13 y_3 nn vdd gnd pl_inv
Xu_inv14 nn n vdd gnd pl_inv
.ends alu4
