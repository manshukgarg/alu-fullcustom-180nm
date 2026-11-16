* 4-bit ALU, transistor level: minimum-PDP cells of Step 3 (step4_layout/library.json)
* slice architecture: plain; generated and checked by sim/gen_alu.py (all 2048 vectors)
* models: models/tsmc018_t14b.lib (nfet, pfet); pins of alu4: inputs, outputs, vdd, gnd

.subckt xor_tg8 A B Y vdd gnd
M0 An A gnd gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M1 An A vdd vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
M2 Bn B gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 Bn B vdd vdd pfet w=0.9u l=0.2u ad=0.45p as=0.45p pd=2.8u ps=2.8u
M4 A Bn Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M5 A B Y vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
M6 An B Y gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M7 An Bn Y vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
.ends xor_tg8

.subckt buf_cmos A Y vdd gnd
M0 Yn A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Yn A vdd vdd pfet w=2.5u l=0.2u ad=1.25p as=1.25p pd=6u ps=6u
M2 Y Yn gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M3 Y Yn vdd vdd pfet w=5u l=0.2u ad=2.5p as=2.5p pd=11u ps=11u
.ends buf_cmos

.subckt mux_tg6 A B S Y vdd gnd
M0 Sn S gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 Sn S vdd vdd pfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M2 A Sn Y gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 A S Y vdd pfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M4 B S Y gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 B Sn Y vdd pfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
.ends mux_tg6

.subckt fa_tgab24 A B C S CO vdd gnd
M0 An A gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M1 An A vdd vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M2 Bn B gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M3 Bn B vdd vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M4 A Bn P gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M5 A B P vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M6 An B P gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M7 An Bn P vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M8 Pn P gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M9 Pn P vdd vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M10 Cn C gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M11 Cn C vdd vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M12 C P Sx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M13 C Pn Sx vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M14 Cn Pn Sx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M15 Cn P Sx vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M16 S Sx gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M17 S Sx vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M18 Cn P COx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M19 Cn Pn COx vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M20 An Pn COx gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M21 An P COx vdd pfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M22 CO COx gnd gnd nfet w=0.4u l=0.2u ad=0.2p as=0.2p pd=1.8u ps=1.8u
M23 CO COx vdd vdd pfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
.ends fa_tgab24

.subckt nand2_cmos A B Y vdd gnd
M0 Y A x gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M1 x B gnd gnd nfet w=1.2u l=0.2u ad=0.6p as=0.6p pd=3.4u ps=3.4u
M2 Y A vdd vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
M3 Y B vdd vdd pfet w=1.8u l=0.2u ad=0.9p as=0.9p pd=4.6u ps=4.6u
.ends nand2_cmos

.subckt inv_cmos A Y vdd gnd
M0 Y A gnd gnd nfet w=0.8u l=0.2u ad=0.4p as=0.4p pd=2.6u ps=2.6u
M1 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends inv_cmos

.subckt nor2_cmos A B Y vdd gnd
M0 Y A gnd gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M1 Y B gnd gnd nfet w=0.6u l=0.2u ad=0.3p as=0.3p pd=2.2u ps=2.2u
M2 Y A x vdd pfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
M3 x B vdd vdd pfet w=3u l=0.2u ad=1.5p as=1.5p pd=7u ps=7u
.ends nor2_cmos

.subckt alu4 a_0 a_1 a_2 a_3 b_0 b_1 b_2 b_3 s_0 s_1 s_2 y_0 y_1 y_2 y_3 c v z n vdd gnd
Xu_xor21 s_1 s_0 cy_0 vdd gnd xor_tg8
Xu_buf1 s_2 s2b vdd gnd buf_cmos
Xu_buf2 s_0 s0b_0 vdd gnd buf_cmos
Xu_buf3 s_0 s0b_1 vdd gnd buf_cmos
Xu_buf4 s_1 s1b_0 vdd gnd buf_cmos
Xu_buf5 s_1 s1b_1 vdd gnd buf_cmos
Xu_xor22 b_0 s0b_0 bxs_0 vdd gnd xor_tg8
Xu_mux21 bxs_0 s0b_0 s1b_0 bx_0 vdd gnd mux_tg6
Xu_fa1 a_0 bx_0 cy_0 sum_0 cy_1 vdd gnd fa_tgab24
Xu_nand21 a_0 b_0 land_0_n vdd gnd nand2_cmos
Xu_inv1 land_0_n land_0 vdd gnd inv_cmos
Xu_nor21 a_0 b_0 lor_0_n vdd gnd nor2_cmos
Xu_inv2 lor_0_n lor_0 vdd gnd inv_cmos
Xu_xor23 a_0 b_0 lxor_0 vdd gnd xor_tg8
Xu_inv3 a_0 lnot_0 vdd gnd inv_cmos
Xu_mux22 land_0 lor_0 s0b_0 m0_0 vdd gnd mux_tg6
Xu_mux23 lxor_0 lnot_0 s0b_0 m1_0 vdd gnd mux_tg6
Xu_mux24 m0_0 m1_0 s1b_0 lg_0 vdd gnd mux_tg6
Xu_mux25 sum_0 lg_0 s2b y_0 vdd gnd mux_tg6
Xu_xor24 b_1 s0b_0 bxs_1 vdd gnd xor_tg8
Xu_mux26 bxs_1 s0b_0 s1b_0 bx_1 vdd gnd mux_tg6
Xu_fa2 a_1 bx_1 cy_1 sum_1 cy_2 vdd gnd fa_tgab24
Xu_nand22 a_1 b_1 land_1_n vdd gnd nand2_cmos
Xu_inv4 land_1_n land_1 vdd gnd inv_cmos
Xu_nor22 a_1 b_1 lor_1_n vdd gnd nor2_cmos
Xu_inv5 lor_1_n lor_1 vdd gnd inv_cmos
Xu_xor25 a_1 b_1 lxor_1 vdd gnd xor_tg8
Xu_inv6 a_1 lnot_1 vdd gnd inv_cmos
Xu_mux27 land_1 lor_1 s0b_0 m0_1 vdd gnd mux_tg6
Xu_mux28 lxor_1 lnot_1 s0b_0 m1_1 vdd gnd mux_tg6
Xu_mux29 m0_1 m1_1 s1b_0 lg_1 vdd gnd mux_tg6
Xu_mux210 sum_1 lg_1 s2b y_1 vdd gnd mux_tg6
Xu_xor26 b_2 s0b_1 bxs_2 vdd gnd xor_tg8
Xu_mux211 bxs_2 s0b_1 s1b_1 bx_2 vdd gnd mux_tg6
Xu_fa3 a_2 bx_2 cy_2 sum_2 cy_3 vdd gnd fa_tgab24
Xu_nand23 a_2 b_2 land_2_n vdd gnd nand2_cmos
Xu_inv7 land_2_n land_2 vdd gnd inv_cmos
Xu_nor23 a_2 b_2 lor_2_n vdd gnd nor2_cmos
Xu_inv8 lor_2_n lor_2 vdd gnd inv_cmos
Xu_xor27 a_2 b_2 lxor_2 vdd gnd xor_tg8
Xu_inv9 a_2 lnot_2 vdd gnd inv_cmos
Xu_mux212 land_2 lor_2 s0b_1 m0_2 vdd gnd mux_tg6
Xu_mux213 lxor_2 lnot_2 s0b_1 m1_2 vdd gnd mux_tg6
Xu_mux214 m0_2 m1_2 s1b_1 lg_2 vdd gnd mux_tg6
Xu_mux215 sum_2 lg_2 s2b y_2 vdd gnd mux_tg6
Xu_xor28 b_3 s0b_1 bxs_3 vdd gnd xor_tg8
Xu_mux216 bxs_3 s0b_1 s1b_1 bx_3 vdd gnd mux_tg6
Xu_fa4 a_3 bx_3 cy_3 sum_3 cy_4 vdd gnd fa_tgab24
Xu_nand24 a_3 b_3 land_3_n vdd gnd nand2_cmos
Xu_inv10 land_3_n land_3 vdd gnd inv_cmos
Xu_nor24 a_3 b_3 lor_3_n vdd gnd nor2_cmos
Xu_inv11 lor_3_n lor_3 vdd gnd inv_cmos
Xu_xor29 a_3 b_3 lxor_3 vdd gnd xor_tg8
Xu_inv12 a_3 lnot_3 vdd gnd inv_cmos
Xu_mux217 land_3 lor_3 s0b_1 m0_3 vdd gnd mux_tg6
Xu_mux218 lxor_3 lnot_3 s0b_1 m1_3 vdd gnd mux_tg6
Xu_mux219 m0_3 m1_3 s1b_1 lg_3 vdd gnd mux_tg6
Xu_mux220 sum_3 lg_3 s2b y_3 vdd gnd mux_tg6
Xu_inv13 cy_4 cyn vdd gnd inv_cmos
Xu_nor25 s2b cyn c vdd gnd nor2_cmos
Xu_xor210 cy_3 cy_4 vxn_n vdd gnd xor_tg8
Xu_inv14 vxn_n vxn vdd gnd inv_cmos
Xu_nor26 s2b vxn v vdd gnd nor2_cmos
Xu_nor27 y_0 y_1 zn_0 vdd gnd nor2_cmos
Xu_nor28 y_2 y_3 zn_1 vdd gnd nor2_cmos
Xu_nand25 zn_0 zn_1 z_n vdd gnd nand2_cmos
Xu_inv15 z_n z vdd gnd inv_cmos
Xu_inv16 y_3 nn vdd gnd inv_cmos
Xu_inv17 nn n vdd gnd inv_cmos
.ends alu4
