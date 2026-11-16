* 4-bit ALU, transistor level: gate-level cells of the LTspice cell set (NAND-based), k = 0.4, r = 2
* slice architecture: plain; generated and checked by sim/gen_alu.py (all 2048 vectors)
* models: models/tsmc018_t14b.lib (nfet, pfet); pins of alu4: inputs, outputs, vdd, gnd

.subckt xor_nand16 A B Y vdd gnd
M0 n1 A x1 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M1 x1 B gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M2 n1 A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M3 n1 B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M4 n2 A x2 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M5 x2 n1 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M6 n2 A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M7 n2 n1 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M8 n3 B x3 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M9 x3 n1 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M10 n3 B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M11 n3 n1 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M12 Y n2 x4 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M13 x4 n3 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M14 Y n2 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M15 Y n3 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends xor_nand16

.subckt buf_cmos A Y vdd gnd
M0 Yn A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Yn A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M2 Y Yn gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M3 Y Yn vdd vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
.ends buf_cmos

.subckt mux_gate20 A B S Y vdd gnd
M0 Sn S gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Sn S vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M2 m1n A x1 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M3 x1 Sn gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M4 m1n A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M5 m1n Sn vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M6 m1 m1n gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 m1 m1n vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M8 m2n B x2 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M9 x2 S gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M10 m2n B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M11 m2n S vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M12 m2 m2n gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M13 m2 m2n vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M14 Yn m1 gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M15 Yn m2 gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M16 Yn m1 x3 vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
M17 x3 m2 vdd vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
M18 Y Yn gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M19 Y Yn vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends mux_gate20

.subckt fa_nand44 A B C S CO vdd gnd
M0 a1 A x1 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M1 x1 B gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M2 a1 A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M3 a1 B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M4 a2 A x2 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M5 x2 a1 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M6 a2 A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M7 a2 a1 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M8 a3 B x3 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M9 x3 a1 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M10 a3 B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M11 a3 a1 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M12 P a2 x4 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M13 x4 a3 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M14 P a2 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M15 P a3 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M16 b1 P x5 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M17 x5 C gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M18 b1 P vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M19 b1 C vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M20 b2 P x6 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M21 x6 b1 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M22 b2 P vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M23 b2 b1 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M24 b3 C x7 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M25 x7 b1 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M26 b3 C vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M27 b3 b1 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M28 S b2 x8 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M29 x8 b3 gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M30 S b2 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M31 S b3 vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M32 g A x9 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M33 x9 B gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M34 g A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M35 g B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M36 h P x10 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M37 x10 C gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M38 h P vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M39 h C vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M40 CO g x11 gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M41 x11 h gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M42 CO g vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M43 CO h vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends fa_nand44

.subckt and2_cmos A B Y vdd gnd
M0 Yn A x gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M1 x B gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M2 Yn A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M3 Yn B vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M4 Y Yn gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 Y Yn vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends and2_cmos

.subckt or2_cmos A B Y vdd gnd
M0 Yn A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Yn B gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M2 Yn A x vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
M3 x B vdd vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
M4 Y Yn gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 Y Yn vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends or2_cmos

.subckt inv_cmos A Y vdd gnd
M0 Y A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Y A vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends inv_cmos

.subckt nor2_cmos A B Y vdd gnd
M0 Y A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Y B gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M2 Y A x vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
M3 x B vdd vdd pfet w=1.6u l=0.2u ad=0.8p as=0.8p pd=4.2u ps=4.2u
.ends nor2_cmos

.subckt alu4 a_0 a_1 a_2 a_3 b_0 b_1 b_2 b_3 s_0 s_1 s_2 y_0 y_1 y_2 y_3 c v z n vdd gnd
Xu_xor21 s_1 s_0 cy_0 vdd gnd xor_nand16
Xu_buf1 s_2 s2b vdd gnd buf_cmos
Xu_buf2 s_0 s0b_0 vdd gnd buf_cmos
Xu_buf3 s_0 s0b_1 vdd gnd buf_cmos
Xu_buf4 s_1 s1b_0 vdd gnd buf_cmos
Xu_buf5 s_1 s1b_1 vdd gnd buf_cmos
Xu_xor22 b_0 s0b_0 bxs_0 vdd gnd xor_nand16
Xu_mux21 bxs_0 s0b_0 s1b_0 bx_0 vdd gnd mux_gate20
Xu_fa1 a_0 bx_0 cy_0 sum_0 cy_1 vdd gnd fa_nand44
Xu_and21 a_0 b_0 land_0 vdd gnd and2_cmos
Xu_or21 a_0 b_0 lor_0 vdd gnd or2_cmos
Xu_xor23 a_0 b_0 lxor_0 vdd gnd xor_nand16
Xu_inv1 a_0 lnot_0 vdd gnd inv_cmos
Xu_mux22 land_0 lor_0 s0b_0 m0_0 vdd gnd mux_gate20
Xu_mux23 lxor_0 lnot_0 s0b_0 m1_0 vdd gnd mux_gate20
Xu_mux24 m0_0 m1_0 s1b_0 lg_0 vdd gnd mux_gate20
Xu_mux25 sum_0 lg_0 s2b y_0 vdd gnd mux_gate20
Xu_xor24 b_1 s0b_0 bxs_1 vdd gnd xor_nand16
Xu_mux26 bxs_1 s0b_0 s1b_0 bx_1 vdd gnd mux_gate20
Xu_fa2 a_1 bx_1 cy_1 sum_1 cy_2 vdd gnd fa_nand44
Xu_and22 a_1 b_1 land_1 vdd gnd and2_cmos
Xu_or22 a_1 b_1 lor_1 vdd gnd or2_cmos
Xu_xor25 a_1 b_1 lxor_1 vdd gnd xor_nand16
Xu_inv2 a_1 lnot_1 vdd gnd inv_cmos
Xu_mux27 land_1 lor_1 s0b_0 m0_1 vdd gnd mux_gate20
Xu_mux28 lxor_1 lnot_1 s0b_0 m1_1 vdd gnd mux_gate20
Xu_mux29 m0_1 m1_1 s1b_0 lg_1 vdd gnd mux_gate20
Xu_mux210 sum_1 lg_1 s2b y_1 vdd gnd mux_gate20
Xu_xor26 b_2 s0b_1 bxs_2 vdd gnd xor_nand16
Xu_mux211 bxs_2 s0b_1 s1b_1 bx_2 vdd gnd mux_gate20
Xu_fa3 a_2 bx_2 cy_2 sum_2 cy_3 vdd gnd fa_nand44
Xu_and23 a_2 b_2 land_2 vdd gnd and2_cmos
Xu_or23 a_2 b_2 lor_2 vdd gnd or2_cmos
Xu_xor27 a_2 b_2 lxor_2 vdd gnd xor_nand16
Xu_inv3 a_2 lnot_2 vdd gnd inv_cmos
Xu_mux212 land_2 lor_2 s0b_1 m0_2 vdd gnd mux_gate20
Xu_mux213 lxor_2 lnot_2 s0b_1 m1_2 vdd gnd mux_gate20
Xu_mux214 m0_2 m1_2 s1b_1 lg_2 vdd gnd mux_gate20
Xu_mux215 sum_2 lg_2 s2b y_2 vdd gnd mux_gate20
Xu_xor28 b_3 s0b_1 bxs_3 vdd gnd xor_nand16
Xu_mux216 bxs_3 s0b_1 s1b_1 bx_3 vdd gnd mux_gate20
Xu_fa4 a_3 bx_3 cy_3 sum_3 cy_4 vdd gnd fa_nand44
Xu_and24 a_3 b_3 land_3 vdd gnd and2_cmos
Xu_or24 a_3 b_3 lor_3 vdd gnd or2_cmos
Xu_xor29 a_3 b_3 lxor_3 vdd gnd xor_nand16
Xu_inv4 a_3 lnot_3 vdd gnd inv_cmos
Xu_mux217 land_3 lor_3 s0b_1 m0_3 vdd gnd mux_gate20
Xu_mux218 lxor_3 lnot_3 s0b_1 m1_3 vdd gnd mux_gate20
Xu_mux219 m0_3 m1_3 s1b_1 lg_3 vdd gnd mux_gate20
Xu_mux220 sum_3 lg_3 s2b y_3 vdd gnd mux_gate20
Xu_inv5 cy_4 cyn vdd gnd inv_cmos
Xu_nor21 s2b cyn c vdd gnd nor2_cmos
Xu_xor210 cy_3 cy_4 vxn_n vdd gnd xor_nand16
Xu_inv6 vxn_n vxn vdd gnd inv_cmos
Xu_nor22 s2b vxn v vdd gnd nor2_cmos
Xu_nor23 y_0 y_1 zn_0 vdd gnd nor2_cmos
Xu_nor24 y_2 y_3 zn_1 vdd gnd nor2_cmos
Xu_and25 zn_0 zn_1 z vdd gnd and2_cmos
Xu_inv7 y_3 nn vdd gnd inv_cmos
Xu_inv8 nn n vdd gnd inv_cmos
.ends alu4
