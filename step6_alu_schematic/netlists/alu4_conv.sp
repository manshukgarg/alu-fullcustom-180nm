* 4-bit ALU, transistor level: conventional static CMOS cells at the reference size (k = 1, r = 2)
* slice architecture: plain; generated and checked by sim/gen_alu.py (all 2048 vectors)
* models: models/tsmc018_t14b.lib (nfet, pfet); pins of alu4: inputs, outputs, vdd, gnd

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

.subckt and2_cmos A B Y vdd gnd
M0 Yn A x gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M1 x B gnd gnd nfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M2 Yn A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M3 Yn B vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
M4 Y Yn gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M5 Y Yn vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends and2_cmos

.subckt or2_cmos A B Y vdd gnd
M0 Yn A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Yn B gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M2 Yn A x vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M3 x B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M4 Y Yn gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M5 Y Yn vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends or2_cmos

.subckt inv_cmos A Y vdd gnd
M0 Y A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends inv_cmos

.subckt nor2_cmos A B Y vdd gnd
M0 Y A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y B gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M2 Y A x vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
M3 x B vdd vdd pfet w=4u l=0.2u ad=2p as=2p pd=9u ps=9u
.ends nor2_cmos

.subckt alu4 a_0 a_1 a_2 a_3 b_0 b_1 b_2 b_3 s_0 s_1 s_2 y_0 y_1 y_2 y_3 c v z n vdd gnd
Xu_xor21 s_1 s_0 cy_0 vdd gnd xor_cmos12
Xu_xor22 b_0 s_0 bxs_0 vdd gnd xor_cmos12
Xu_mux21 bxs_0 s_0 s_1 bx_0 vdd gnd mux_cmos12
Xu_fa1 a_0 bx_0 cy_0 sum_0 cy_1 vdd gnd fa_cmos28
Xu_and21 a_0 b_0 land_0 vdd gnd and2_cmos
Xu_or21 a_0 b_0 lor_0 vdd gnd or2_cmos
Xu_xor23 a_0 b_0 lxor_0 vdd gnd xor_cmos12
Xu_inv1 a_0 lnot_0 vdd gnd inv_cmos
Xu_mux22 land_0 lor_0 s_0 m0_0 vdd gnd mux_cmos12
Xu_mux23 lxor_0 lnot_0 s_0 m1_0 vdd gnd mux_cmos12
Xu_mux24 m0_0 m1_0 s_1 lg_0 vdd gnd mux_cmos12
Xu_mux25 sum_0 lg_0 s_2 y_0 vdd gnd mux_cmos12
Xu_xor24 b_1 s_0 bxs_1 vdd gnd xor_cmos12
Xu_mux26 bxs_1 s_0 s_1 bx_1 vdd gnd mux_cmos12
Xu_fa2 a_1 bx_1 cy_1 sum_1 cy_2 vdd gnd fa_cmos28
Xu_and22 a_1 b_1 land_1 vdd gnd and2_cmos
Xu_or22 a_1 b_1 lor_1 vdd gnd or2_cmos
Xu_xor25 a_1 b_1 lxor_1 vdd gnd xor_cmos12
Xu_inv2 a_1 lnot_1 vdd gnd inv_cmos
Xu_mux27 land_1 lor_1 s_0 m0_1 vdd gnd mux_cmos12
Xu_mux28 lxor_1 lnot_1 s_0 m1_1 vdd gnd mux_cmos12
Xu_mux29 m0_1 m1_1 s_1 lg_1 vdd gnd mux_cmos12
Xu_mux210 sum_1 lg_1 s_2 y_1 vdd gnd mux_cmos12
Xu_xor26 b_2 s_0 bxs_2 vdd gnd xor_cmos12
Xu_mux211 bxs_2 s_0 s_1 bx_2 vdd gnd mux_cmos12
Xu_fa3 a_2 bx_2 cy_2 sum_2 cy_3 vdd gnd fa_cmos28
Xu_and23 a_2 b_2 land_2 vdd gnd and2_cmos
Xu_or23 a_2 b_2 lor_2 vdd gnd or2_cmos
Xu_xor27 a_2 b_2 lxor_2 vdd gnd xor_cmos12
Xu_inv3 a_2 lnot_2 vdd gnd inv_cmos
Xu_mux212 land_2 lor_2 s_0 m0_2 vdd gnd mux_cmos12
Xu_mux213 lxor_2 lnot_2 s_0 m1_2 vdd gnd mux_cmos12
Xu_mux214 m0_2 m1_2 s_1 lg_2 vdd gnd mux_cmos12
Xu_mux215 sum_2 lg_2 s_2 y_2 vdd gnd mux_cmos12
Xu_xor28 b_3 s_0 bxs_3 vdd gnd xor_cmos12
Xu_mux216 bxs_3 s_0 s_1 bx_3 vdd gnd mux_cmos12
Xu_fa4 a_3 bx_3 cy_3 sum_3 cy_4 vdd gnd fa_cmos28
Xu_and24 a_3 b_3 land_3 vdd gnd and2_cmos
Xu_or24 a_3 b_3 lor_3 vdd gnd or2_cmos
Xu_xor29 a_3 b_3 lxor_3 vdd gnd xor_cmos12
Xu_inv4 a_3 lnot_3 vdd gnd inv_cmos
Xu_mux217 land_3 lor_3 s_0 m0_3 vdd gnd mux_cmos12
Xu_mux218 lxor_3 lnot_3 s_0 m1_3 vdd gnd mux_cmos12
Xu_mux219 m0_3 m1_3 s_1 lg_3 vdd gnd mux_cmos12
Xu_mux220 sum_3 lg_3 s_2 y_3 vdd gnd mux_cmos12
Xu_inv5 cy_4 cyn vdd gnd inv_cmos
Xu_nor21 s_2 cyn c vdd gnd nor2_cmos
Xu_xor210 cy_3 cy_4 vxn_n vdd gnd xor_cmos12
Xu_inv6 vxn_n vxn vdd gnd inv_cmos
Xu_nor22 s_2 vxn v vdd gnd nor2_cmos
Xu_nor23 y_0 y_1 zn_0 vdd gnd nor2_cmos
Xu_nor24 y_2 y_3 zn_1 vdd gnd nor2_cmos
Xu_and25 zn_0 zn_1 z vdd gnd and2_cmos
Xu_inv7 y_3 nn vdd gnd inv_cmos
Xu_inv8 nn n vdd gnd inv_cmos
.ends alu4
