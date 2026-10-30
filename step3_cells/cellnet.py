"""Transistor-level netlists of the candidate library cells (180 nm, L = 0.2 um).

Every candidate is written as a SPICE subcircuit with pins: inputs, outputs,
vdd, gnd. Widths are in um and scale with the factor k (k = 1 is the reference
sizing: each stage about as strong as the X1 inverter, Wn 1.0 / Wp 2.0 um).
Source/drain junctions are estimated for a 0.5 um diffusion length, the same
convention as the inverter of Step 1, so pre-layout numbers stay comparable.
"""

L = 0.2          # drawn channel length, um
DIFF = 0.5       # source/drain diffusion length used for junction estimates, um


class Cell:
    def __init__(self, name, inputs, outputs, func, family, note=""):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.func = func            # function: dict(input -> 0/1) -> dict(output -> 0/1)
        self.family = family
        self.note = note
        self.devs = []

    def n(self, d, g, s, w):
        self.devs.append(("nfet", d, g, s, "gnd", w))

    def p(self, d, g, s, w):
        self.devs.append(("pfet", d, g, s, "vdd", w))

    def inv(self, a, y, wn, wp):
        self.n(y, a, "gnd", wn)
        self.p(y, a, "vdd", wp)

    def tg(self, a, b, gn, gp, wn, wp):
        """Transmission gate between a and b; on when gn = 1 (gp = 0)."""
        self.n(a, gn, b, wn)
        self.p(a, gp, b, wp)

    @property
    def count(self):
        return len(self.devs)

    def spice(self):
        pins = " ".join(self.inputs + self.outputs + ["vdd", "gnd"])
        out = [".subckt %s %s" % (self.name, pins)]
        for i, (m, d, g, s, b, w) in enumerate(self.devs):
            ad = w * DIFF
            pd = 2 * (w + DIFF)
            out.append("M%d %s %s %s %s %s w=%.3gu l=%.3gu ad=%.4gp as=%.4gp pd=%.4gu ps=%.4gu"
                       % (i, d, g, s, b, m, w, L, ad, ad, pd, pd))
        out.append(".ends %s" % self.name)
        return "\n".join(out) + "\n"


def X(a, b):
    return a ^ b


# --------------------------------------------------------------------------
# reference inverter used as driver and load (same sizes as OSU018 INVX1)
# --------------------------------------------------------------------------
def inv_x1():
    c = Cell("inv_x1", ["A"], ["Y"], lambda v: {"Y": 1 - v["A"]}, "INV")
    c.inv("A", "Y", 1.0, 2.0)
    return c


# --------------------------------------------------------------------------
# basic gates
# --------------------------------------------------------------------------
def inv_cmos(k=1.0):
    c = Cell("inv_cmos", ["A"], ["Y"], lambda v: {"Y": 1 - v["A"]}, "INV", "static CMOS")
    c.inv("A", "Y", 1.0 * k, 2.0 * k)
    return c


def nand2_cmos(k=1.0):
    c = Cell("nand2_cmos", ["A", "B"], ["Y"], lambda v: {"Y": 1 - (v["A"] & v["B"])},
             "NAND2", "static CMOS")
    c.n("Y", "A", "x", 2.0 * k)
    c.n("x", "B", "gnd", 2.0 * k)
    c.p("Y", "A", "vdd", 2.0 * k)
    c.p("Y", "B", "vdd", 2.0 * k)
    return c


def nor2_cmos(k=1.0):
    c = Cell("nor2_cmos", ["A", "B"], ["Y"], lambda v: {"Y": 1 - (v["A"] | v["B"])},
             "NOR2", "static CMOS")
    c.n("Y", "A", "gnd", 1.0 * k)
    c.n("Y", "B", "gnd", 1.0 * k)
    c.p("Y", "A", "x", 4.0 * k)
    c.p("x", "B", "vdd", 4.0 * k)
    return c


# --------------------------------------------------------------------------
# XOR2: Y = A xor B
# --------------------------------------------------------------------------
def fxor(v):
    return {"Y": X(v["A"], v["B"])}


def xor_cmos12(k=1.0):
    c = Cell("xor_cmos12", ["A", "B"], ["Y"], fxor, "XOR2", "static CMOS, input inverters")
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.n("Y", "A", "n1", 2.0 * k)
    c.n("n1", "B", "gnd", 2.0 * k)
    c.n("Y", "An", "n2", 2.0 * k)
    c.n("n2", "Bn", "gnd", 2.0 * k)
    c.p("Y", "An", "p1", 4.0 * k)
    c.p("p1", "B", "vdd", 4.0 * k)
    c.p("Y", "A", "p2", 4.0 * k)
    c.p("p2", "Bn", "vdd", 4.0 * k)
    return c


def xor_tg8(k=1.0):
    c = Cell("xor_tg8", ["A", "B"], ["Y"], fxor, "XOR2", "transmission gate, unbuffered")
    c.inv("A", "An", 1.0 * k, 2.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("A", "Y", "Bn", "B", 1.0 * k, 2.0 * k)
    c.tg("An", "Y", "B", "Bn", 1.0 * k, 2.0 * k)
    return c


def xor_tgb10(k=1.0):
    c = Cell("xor_tgb10", ["A", "B"], ["Y"], fxor, "XOR2", "transmission gate + output inverter")
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("An", "Xn", "Bn", "B", 0.5 * k, 1.0 * k)      # Xn = A xnor B
    c.tg("A", "Xn", "B", "Bn", 0.5 * k, 1.0 * k)
    c.inv("Xn", "Y", 1.0 * k, 2.0 * k)
    return c


def xor_cpl14(k=1.0):
    c = Cell("xor_cpl14", ["A", "B"], ["Y"], fxor, "XOR2", "CPL, NMOS pass + restoring inverters")
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.n("A", "Bn", "Yi", 1.0 * k)          # Yi  = A xor B  (NMOS pass)
    c.n("An", "B", "Yi", 1.0 * k)
    c.n("An", "Bn", "Yni", 1.0 * k)        # Yni = A xnor B
    c.n("A", "B", "Yni", 1.0 * k)
    c.inv("Yni", "Y", 1.0 * k, 2.0 * k)
    c.inv("Yi", "Yn", 0.5 * k, 1.0 * k)
    c.p("Yni", "Y", "vdd", 0.4)            # weak level restorers
    c.p("Yi", "Yn", "vdd", 0.4)
    return c


# --------------------------------------------------------------------------
# MUX2: Y = S ? B : A   (inverting variants: Y = not(S ? B : A))
# --------------------------------------------------------------------------
def fmux(v):
    return {"Y": v["B"] if v["S"] else v["A"]}


def fmuxi(v):
    return {"Y": 1 - (v["B"] if v["S"] else v["A"])}


def mux_cmos12(k=1.0):
    c = Cell("mux_cmos12", ["A", "B", "S"], ["Y"], fmux, "MUX2", "static CMOS, AOI22 + inverter")
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.n("Yb", "A", "n1", 2.0 * k)
    c.n("n1", "Sn", "gnd", 2.0 * k)
    c.n("Yb", "B", "n2", 2.0 * k)
    c.n("n2", "S", "gnd", 2.0 * k)
    c.p("Yb", "A", "p1", 4.0 * k)
    c.p("Yb", "Sn", "p1", 4.0 * k)
    c.p("p1", "B", "vdd", 4.0 * k)
    c.p("p1", "S", "vdd", 4.0 * k)
    c.inv("Yb", "Y", 1.0 * k, 2.0 * k)
    return c


def mux_tg6(k=1.0):
    c = Cell("mux_tg6", ["A", "B", "S"], ["Y"], fmux, "MUX2", "transmission gate, unbuffered")
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.tg("A", "Y", "Sn", "S", 1.0 * k, 2.0 * k)
    c.tg("B", "Y", "S", "Sn", 1.0 * k, 2.0 * k)
    return c


def mux_tgb10(k=1.0):
    c = Cell("mux_tgb10", ["A", "B", "S"], ["Y"], fmux, "MUX2", "transmission gate + two inverters")
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.tg("A", "M", "Sn", "S", 0.5 * k, 1.0 * k)
    c.tg("B", "M", "S", "Sn", 0.5 * k, 1.0 * k)
    c.inv("M", "Mn", 0.5 * k, 1.0 * k)
    c.inv("Mn", "Y", 1.0 * k, 2.0 * k)
    return c


def muxi_cmos10(k=1.0):
    c = Cell("muxi_cmos10", ["A", "B", "S"], ["Y"], fmuxi, "MUX2I", "static CMOS AOI22")
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.n("Y", "A", "n1", 2.0 * k)
    c.n("n1", "Sn", "gnd", 2.0 * k)
    c.n("Y", "B", "n2", 2.0 * k)
    c.n("n2", "S", "gnd", 2.0 * k)
    c.p("Y", "A", "p1", 4.0 * k)
    c.p("Y", "Sn", "p1", 4.0 * k)
    c.p("p1", "B", "vdd", 4.0 * k)
    c.p("p1", "S", "vdd", 4.0 * k)
    return c


def muxi_tg8(k=1.0):
    c = Cell("muxi_tg8", ["A", "B", "S"], ["Y"], fmuxi, "MUX2I", "transmission gate + output inverter")
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.tg("A", "M", "Sn", "S", 0.5 * k, 1.0 * k)
    c.tg("B", "M", "S", "Sn", 0.5 * k, 1.0 * k)
    c.inv("M", "Y", 1.0 * k, 2.0 * k)
    return c


def muxi_npt7(k=1.0):
    c = Cell("muxi_npt7", ["A", "B", "S"], ["Y"], fmuxi, "MUX2I",
             "NMOS pass + level restorer + inverter")
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.n("A", "Sn", "M", 1.0 * k)
    c.n("B", "S", "M", 1.0 * k)
    c.inv("M", "Y", 1.0 * k, 2.0 * k)
    c.p("M", "Y", "vdd", 0.4)              # weak restorer pulls M to full VDD
    return c


# --------------------------------------------------------------------------
# full adder: S = A xor B xor C, CO = majority(A, B, C)
# --------------------------------------------------------------------------
def ffa(v):
    a, b, c = v["A"], v["B"], v["C"]
    return {"S": a ^ b ^ c, "CO": (a & b) | (c & (a | b))}


def fa_cmos28(k=1.0):
    c = Cell("fa_cmos28", ["A", "B", "C"], ["S", "CO"], ffa, "FA", "mirror adder (static CMOS)")
    # carry stage: COn = not(AB + C(A + B)), identical pull-up and pull-down topology
    c.n("COn", "A", "n1", 2.0 * k); c.n("n1", "B", "gnd", 2.0 * k)
    c.n("COn", "C", "n2", 2.0 * k); c.n("n2", "A", "gnd", 2.0 * k); c.n("n2", "B", "gnd", 2.0 * k)
    c.p("COn", "A", "p1", 4.0 * k); c.p("p1", "B", "vdd", 4.0 * k)
    c.p("COn", "C", "p2", 4.0 * k); c.p("p2", "A", "vdd", 4.0 * k); c.p("p2", "B", "vdd", 4.0 * k)
    # sum stage: Sn = not(ABC + COn(A + B + C))
    c.n("Sn", "A", "n3", 3.0 * k); c.n("n3", "B", "n4", 3.0 * k); c.n("n4", "C", "gnd", 3.0 * k)
    c.n("Sn", "COn", "n5", 2.0 * k)
    c.n("n5", "A", "gnd", 2.0 * k); c.n("n5", "B", "gnd", 2.0 * k); c.n("n5", "C", "gnd", 2.0 * k)
    c.p("Sn", "A", "p3", 6.0 * k); c.p("p3", "B", "p4", 6.0 * k); c.p("p4", "C", "vdd", 6.0 * k)
    c.p("Sn", "COn", "p5", 4.0 * k)
    c.p("p5", "A", "vdd", 4.0 * k); c.p("p5", "B", "vdd", 4.0 * k); c.p("p5", "C", "vdd", 4.0 * k)
    c.inv("COn", "CO", 1.0 * k, 2.0 * k)
    c.inv("Sn", "S", 1.0 * k, 2.0 * k)
    return c


def fa_tga20(k=1.0):
    c = Cell("fa_tga20", ["A", "B", "C"], ["S", "CO"], ffa, "FA", "transmission-gate adder, unbuffered")
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("A", "P", "Bn", "B", 0.5 * k, 1.0 * k)       # P = A xor B
    c.tg("An", "P", "B", "Bn", 0.5 * k, 1.0 * k)
    c.inv("P", "Pn", 0.5 * k, 1.0 * k)
    c.inv("C", "Cn", 1.0 * k, 2.0 * k)
    c.tg("Cn", "S", "P", "Pn", 1.0 * k, 2.0 * k)      # S = P ? Cn : C
    c.tg("C", "S", "Pn", "P", 1.0 * k, 2.0 * k)
    c.tg("C", "CO", "P", "Pn", 1.0 * k, 2.0 * k)      # CO = P ? C : A
    c.tg("A", "CO", "Pn", "P", 1.0 * k, 2.0 * k)
    return c


def fa_tgab24(k=1.0):
    c = Cell("fa_tgab24", ["A", "B", "C"], ["S", "CO"], ffa, "FA",
             "transmission-gate adder, inverted internals, buffered outputs")
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("A", "P", "Bn", "B", 0.5 * k, 1.0 * k)       # P = A xor B
    c.tg("An", "P", "B", "Bn", 0.5 * k, 1.0 * k)
    c.inv("P", "Pn", 0.5 * k, 1.0 * k)
    c.inv("C", "Cn", 0.5 * k, 1.0 * k)
    c.tg("C", "Sx", "P", "Pn", 0.5 * k, 1.0 * k)      # Sx = P ? C : Cn  = not S
    c.tg("Cn", "Sx", "Pn", "P", 0.5 * k, 1.0 * k)
    c.inv("Sx", "S", 1.0 * k, 2.0 * k)
    c.tg("Cn", "COx", "P", "Pn", 0.5 * k, 1.0 * k)    # COx = P ? Cn : An = not CO
    c.tg("An", "COx", "Pn", "P", 0.5 * k, 1.0 * k)
    c.inv("COx", "CO", 1.0 * k, 2.0 * k)
    return c


CANDIDATES = [inv_cmos, nand2_cmos, nor2_cmos,
              xor_cmos12, xor_tg8, xor_tgb10, xor_cpl14,
              mux_cmos12, mux_tg6, mux_tgb10, muxi_cmos10, muxi_tg8, muxi_npt7,
              fa_cmos28, fa_tga20, fa_tgab24]
