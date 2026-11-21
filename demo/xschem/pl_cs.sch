v {xschem version=3.0.0 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {pl_cs   carry-sum cell CS:  CO = P ? CI : A,   Y = K ? P : (P xor CI)} -20 -150 0 0 0.45 0.45 {}
T {carry multiplexer, XOR and K multiplexer as transmission gates; inverters, output buffers} -20 -112 0 0 0.28 0.28 {}
T {24 transistors; device labels W/L, the sizes of the layout mag/pl_cs.mag} -20 -92 0 0 0.28 0.28 {}
N 80 0 170 0 {lab=A}
N 80 120 170 120 {lab=CI}
N 230 0 310 0 {lab=cx}
N 310 0 310 60 {lab=cx}
N 230 120 310 120 {lab=cx}
N 310 120 310 60 {lab=cx}
N 310 60 370 60 {lab=cx}
N 370 60 380 60 {lab=cx}
N 380 20 380 60 {lab=cx}
N 380 60 380 100 {lab=cx}
N 420 50 420 60 {lab=COn}
N 420 60 420 70 {lab=COn}
N 420 60 510 60 {lab=COn}
N 510 60 520 60 {lab=COn}
N 520 20 520 60 {lab=COn}
N 520 60 520 100 {lab=COn}
N 560 50 560 60 {lab=CO}
N 560 60 560 70 {lab=CO}
N 560 60 640 60 {lab=CO}
N 120 300 170 300 {lab=CI}
N 120 420 170 420 {lab=CIn}
N 230 300 310 300 {lab=xn}
N 310 300 310 360 {lab=xn}
N 230 420 310 420 {lab=xn}
N 310 420 310 360 {lab=xn}
N 310 360 360 360 {lab=xn}
N 360 360 370 360 {lab=xn}
N 320 240 370 240 {lab=Pn}
N 430 240 510 240 {lab=yn}
N 510 240 510 300 {lab=yn}
N 430 360 510 360 {lab=yn}
N 510 360 510 300 {lab=yn}
N 510 300 570 300 {lab=yn}
N 570 300 580 300 {lab=yn}
N 580 260 580 300 {lab=yn}
N 580 300 580 340 {lab=yn}
N 620 290 620 300 {lab=Y}
N 620 300 620 310 {lab=Y}
N 620 300 700 300 {lab=Y}
N 60 600 140 600 {lab=P}
N 140 560 140 600 {lab=P}
N 140 600 140 640 {lab=P}
N 180 590 180 600 {lab=Pn}
N 180 600 180 610 {lab=Pn}
N 180 600 260 600 {lab=Pn}
N 340 600 420 600 {lab=CI}
N 420 560 420 600 {lab=CI}
N 420 600 420 640 {lab=CI}
N 460 590 460 600 {lab=CIn}
N 460 600 460 610 {lab=CIn}
N 460 600 540 600 {lab=CIn}
N 620 600 700 600 {lab=K}
N 700 560 700 600 {lab=K}
N 700 600 700 640 {lab=K}
N 740 590 740 600 {lab=Kn}
N 740 600 740 610 {lab=Kn}
N 740 600 820 600 {lab=Kn}
C {pl018_pfet_h.sym} 200 0 0 0 {name=M1 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 0 0 0 {name=M0 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 -40 0 0 {name=l1 lab=P}
C {lab_pin.sym} 200 40 0 0 {name=l2 lab=Pn}
C {pl018_pfet_h.sym} 200 120 0 0 {name=M3 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 120 0 0 {name=M2 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 80 0 0 {name=l3 lab=Pn}
C {lab_pin.sym} 200 160 0 0 {name=l4 lab=P}
C {ipin.sym} 80 0 0 0 {name=p1 lab=A}
C {ipin.sym} 80 120 0 0 {name=p2 lab=CI}
C {pl018_label.sym} 370 60 0 0 {name=l5 lab=cx}
C {pl018_pfet.sym} 400 20 0 0 {name=M19 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet.sym} 400 100 0 0 {name=M18 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 420 -10 0 0 {name=l6 lab=vdd}
C {gnd.sym} 420 130 0 0 {name=l7 lab=gnd}
C {pl018_label.sym} 510 60 0 0 {name=l8 lab=COn}
C {pl018_pfet.sym} 540 20 0 0 {name=M21 model=pfet body=vdd w=1.2u l=0.2u m=1}
C {pl018_nfet.sym} 540 100 0 0 {name=M20 model=nfet body=gnd w=0.8u l=0.2u m=1}
C {vdd.sym} 560 -10 0 0 {name=l9 lab=vdd}
C {gnd.sym} 560 130 0 0 {name=l10 lab=gnd}
C {opin.sym} 640 60 0 0 {name=p3 lab=CO}
C {pl018_pfet_h.sym} 200 300 0 0 {name=M5 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 300 0 0 {name=M4 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 260 0 0 {name=l11 lab=Pn}
C {lab_pin.sym} 200 340 0 0 {name=l12 lab=P}
C {pl018_pfet_h.sym} 200 420 0 0 {name=M7 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet_h.sym} 200 420 0 0 {name=M6 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 200 380 0 0 {name=l13 lab=P}
C {lab_pin.sym} 200 460 0 0 {name=l14 lab=Pn}
C {lab_pin.sym} 120 300 0 0 {name=l15 lab=CI}
C {lab_pin.sym} 120 420 0 0 {name=l16 lab=CIn}
C {pl018_label.sym} 360 360 0 0 {name=l17 lab=xn}
C {pl018_pfet_h.sym} 400 240 0 0 {name=M13 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet_h.sym} 400 240 0 0 {name=M12 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 400 200 0 0 {name=l18 lab=Kn}
C {lab_pin.sym} 400 280 0 0 {name=l19 lab=K}
C {pl018_pfet_h.sym} 400 360 0 0 {name=M15 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet_h.sym} 400 360 0 0 {name=M14 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {lab_pin.sym} 400 320 0 0 {name=l20 lab=K}
C {lab_pin.sym} 400 400 0 0 {name=l21 lab=Kn}
C {lab_pin.sym} 320 240 0 0 {name=l22 lab=Pn}
C {pl018_label.sym} 570 300 0 0 {name=l23 lab=yn}
C {pl018_pfet.sym} 600 260 0 0 {name=M23 model=pfet body=vdd w=1.2u l=0.2u m=1}
C {pl018_nfet.sym} 600 340 0 0 {name=M22 model=nfet body=gnd w=0.8u l=0.2u m=1}
C {vdd.sym} 620 230 0 0 {name=l24 lab=vdd}
C {gnd.sym} 620 370 0 0 {name=l25 lab=gnd}
C {opin.sym} 700 300 0 0 {name=p4 lab=Y}
C {ipin.sym} 60 600 0 0 {name=p5 lab=P}
C {pl018_pfet.sym} 160 560 0 0 {name=M11 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet.sym} 160 640 0 0 {name=M10 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 180 530 0 0 {name=l26 lab=vdd}
C {gnd.sym} 180 670 0 0 {name=l27 lab=gnd}
C {lab_pin.sym} 260 600 0 1 {name=l28 lab=Pn}
C {lab_pin.sym} 340 600 0 0 {name=l29 lab=CI}
C {pl018_pfet.sym} 440 560 0 0 {name=M9 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet.sym} 440 640 0 0 {name=M8 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 460 530 0 0 {name=l30 lab=vdd}
C {gnd.sym} 460 670 0 0 {name=l31 lab=gnd}
C {lab_pin.sym} 540 600 0 1 {name=l32 lab=CIn}
C {ipin.sym} 620 600 0 0 {name=p6 lab=K}
C {pl018_pfet.sym} 720 560 0 0 {name=M17 model=pfet body=vdd w=0.6u l=0.2u m=1}
C {pl018_nfet.sym} 720 640 0 0 {name=M16 model=nfet body=gnd w=0.4u l=0.2u m=1}
C {vdd.sym} 740 530 0 0 {name=l33 lab=vdd}
C {gnd.sym} 740 670 0 0 {name=l34 lab=gnd}
C {lab_pin.sym} 820 600 0 1 {name=l35 lab=Kn}
C {iopin.sym} 780 150 0 0 {name=p7 lab=vdd}
C {iopin.sym} 780 190 0 0 {name=p8 lab=gnd}
