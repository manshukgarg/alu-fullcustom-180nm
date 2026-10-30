"""Cell layouts for the custom standard-cell library (lambda units)."""

from maglib import Layout
from template import H, YN0, YP1, EDGE, rails, taps, ports_power


def inv(name="inv", wn=10, wp=20):
    """Static CMOS inverter. Default Wn = 1.0 um, Wp = 2.0 um, L = 0.2 um.

    Columns (x): source contact 2..6 | gate 7..9 | drain contact 10..14.
    Input A on a poly contact in the well gap; output Y on a metal1 strip
    joining the two drains.
    """
    W = 16
    L = Layout(name, bbox=(0, 0, W, H))
    rails(L, W)
    taps(L, [6])

    yn1 = YN0 + wn            # NMOS diffusion top
    yp0 = YP1 - wp            # PMOS diffusion bottom

    # diffusions: contact | 1 lambda | gate | 1 lambda | contact
    L.paint("ndc", 2, YN0, 6, yn1)
    L.paint("ndiff", 6, YN0, 10, yn1)
    L.paint("ndc", 10, YN0, 14, yn1)
    L.paint("pdc", 2, yp0, 6, YP1)
    L.paint("pdiff", 6, yp0, 10, YP1)
    L.paint("pdc", 10, yp0, 14, YP1)

    # gate poly, 2 lambda beyond each diffusion; poly contact for input A
    L.paint("poly", 7, YN0 - 2, 9, YP1 + 2)
    L.paint("pc", 4, 32, 8, 36)

    # metal1: sources to rails, drains joined (output), input pin
    L.paint("m1", 2, -3, 6, YN0)
    L.paint("m1", 2, YP1, 6, H + 3)
    L.paint("m1", 11, YN0, 14, YP1)
    L.paint("m1", 4, 36, 8, 40)

    L.label("m1", 4, 37, 8, 40, "A", "signal", "input")
    L.label("m1", 11, 40, 14, 44, "Y", "signal", "output")
    ports_power(L, W)
    return L


INV_REF = """* Inverter reference netlist (LVS)
.subckt inv A Y vdd gnd
M1 Y A vdd vdd pfet w=2u l=0.2u
M2 Y A gnd gnd nfet w=1u l=0.2u
.ends inv
"""
