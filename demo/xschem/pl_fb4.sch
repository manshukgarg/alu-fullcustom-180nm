v {xschem version=3.0.0 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {pl_fb4   function block FB4:  P = C[2A+B]} -20 -150 0 0 0.45 0.45 {}
T {4:1 transmission-gate multiplexer selected by A and B, input inverters, output buffer} -20 -112 0 0 0.28 0.28 {}
T {20 transistors; device labels W/L, the sizes of the layout mag/pl_fb4.mag} -20 -92 0 0 0.28 0.28 {}
N 80 0 170 0 {lab=C0}
N 80 120 170 120 {lab=C1}
N 80 280 170 280 {lab=C2}
N 80 400 170 400 {lab=C3}
N 230 0 310 0 {lab=u0}
N 310 0 310 60 {lab=u0}
N 230 120 310 120 {lab=u0}
N 310 120 310 60 {lab=u0}
N 310 60 360 60 {lab=u0}
N 360 60 370 60 {lab=u0}
N 230 280 310 280 {lab=u1}
N 310 280 310 340 {lab=u1}
N 230 400 310 400 {lab=u1}
N 310 400 310 340 {lab=u1}
N 310 340 360 340 {lab=u1}
N 360 340 370 340 {lab=u1}
N 430 60 510 60 {lab=x}
N 510 60 510 200 {lab=x}
N 430 340 510 340 {lab=x}
N 510 340 510 200 {lab=x}
N 510 200 570 200 {lab=x}
N 570 200 580 200 {lab=x}
N 580 160 580 200 {lab=x}
N 580 200 580 240 {lab=x}
N 620 190 620 200 {lab=Pn}
N 620 200 620 210 {lab=Pn}
N 620 200 710 200 {lab=Pn}
N 710 200 720 200 {lab=Pn}
N 720 160 720 200 {lab=Pn}
N 720 200 720 240 {lab=Pn}
N 760 190 760 200 {lab=P}
N 760 200 760 210 {lab=P}
N 760 200 840 200 {lab=P}
N 60 600 140 600 {lab=A}
N 140 560 140 600 {lab=A}
N 140 600 140 640 {lab=A}
N 180 590 180 600 {lab=An}
N 180 600 180 610 {lab=An}
N 180 600 260 600 {lab=An}
N 340 600 420 600 {lab=B}
N 420 560 420 600 {lab=B}
N 420 600 420 640 {lab=B}
N 460 590 460 600 {lab=Bn}
N 460 600 460 610 {lab=Bn}
N 460 600 540 600 {lab=Bn}
C {pl018_pfet_h.sym} 200 0 0 0 {name=M3 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 0 0 0 {name=M2 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 -40 0 0 {name=l1 lab=B}
C {lab_pin.sym} 200 40 0 0 {name=l2 lab=Bn}
C {ipin.sym} 80 0 0 0 {name=p1 lab=C0}
C {pl018_pfet_h.sym} 200 120 0 0 {name=M1 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 120 0 0 {name=M0 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 80 0 0 {name=l3 lab=Bn}
C {lab_pin.sym} 200 160 0 0 {name=l4 lab=B}
C {ipin.sym} 80 120 0 0 {name=p2 lab=C1}
C {pl018_pfet_h.sym} 200 280 0 0 {name=M5 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 280 0 0 {name=M4 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 240 0 0 {name=l5 lab=B}
C {lab_pin.sym} 200 320 0 0 {name=l6 lab=Bn}
C {ipin.sym} 80 280 0 0 {name=p3 lab=C2}
C {pl018_pfet_h.sym} 200 400 0 0 {name=M7 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 400 0 0 {name=M6 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 360 0 0 {name=l7 lab=Bn}
C {lab_pin.sym} 200 440 0 0 {name=l8 lab=B}
C {ipin.sym} 80 400 0 0 {name=p4 lab=C3}
C {pl018_label.sym} 360 60 0 0 {name=l9 lab=u0}
C {pl018_label.sym} 360 340 0 0 {name=l10 lab=u1}
C {pl018_pfet_h.sym} 400 60 0 0 {name=M9 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet_h.sym} 400 60 0 0 {name=M8 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 400 20 0 0 {name=l11 lab=A}
C {lab_pin.sym} 400 100 0 0 {name=l12 lab=An}
C {pl018_pfet_h.sym} 400 340 0 0 {name=M11 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet_h.sym} 400 340 0 0 {name=M10 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 400 300 0 0 {name=l13 lab=An}
C {lab_pin.sym} 400 380 0 0 {name=l14 lab=A}
C {pl018_label.sym} 570 200 0 0 {name=l15 lab=x}
C {pl018_pfet.sym} 600 160 0 0 {name=M17 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet.sym} 600 240 0 0 {name=M16 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 620 130 0 0 {name=l16 lab=vdd}
C {gnd.sym} 620 270 0 0 {name=l17 lab=gnd}
C {pl018_label.sym} 710 200 0 0 {name=l18 lab=Pn}
C {pl018_pfet.sym} 740 160 0 0 {name=M19 model=pfet body=vdd w=1u l=0.2u m=1}
C {pl018_nfet.sym} 740 240 0 0 {name=M18 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 760 130 0 0 {name=l19 lab=vdd}
C {gnd.sym} 760 270 0 0 {name=l20 lab=gnd}
C {opin.sym} 840 200 0 0 {name=p5 lab=P}
C {ipin.sym} 60 600 0 0 {name=p6 lab=A}
C {pl018_pfet.sym} 160 560 0 0 {name=M13 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet.sym} 160 640 0 0 {name=M12 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 180 530 0 0 {name=l21 lab=vdd}
C {gnd.sym} 180 670 0 0 {name=l22 lab=gnd}
C {lab_pin.sym} 260 600 0 1 {name=l23 lab=An}
C {ipin.sym} 340 600 0 0 {name=p7 lab=B}
C {pl018_pfet.sym} 440 560 0 0 {name=M15 model=pfet body=vdd w=0.5u l=0.2u m=1}
C {pl018_nfet.sym} 440 640 0 0 {name=M14 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 460 530 0 0 {name=l24 lab=vdd}
C {gnd.sym} 460 670 0 0 {name=l25 lab=gnd}
C {lab_pin.sym} 540 600 0 1 {name=l26 lab=Bn}
C {iopin.sym} 680 570 0 0 {name=p8 lab=vdd}
C {iopin.sym} 680 610 0 0 {name=p9 lab=gnd}
