"""Transistor-level netlists of the candidate library cells (180 nm, L = 0.2 um).

Every candidate is written as a SPICE subcircuit with pins: inputs, outputs,
vdd, gnd. Widths are in um and scale with the factor k (k = 1 is the reference
sizing: each stage about as strong as the X1 inverter, Wn 1.0 / Wp 2.0 um).
Source/drain junctions are estimated for a 0.5 um diffusion length, the same
convention as the inverter of Step 1, so pre-layout numbers stay comparable.
"""

L = 0.2          # drawn channel length, um
DIFF = 0.5       # source/drain diffusion length used for junction estimates, um
WMIN = 0.4       # minimum contacted transistor width (4 lambda), um


class Cell:
    def __init__(self, name, inputs, outputs, func, family, note="", r=2.0):
        self.name = name
        self.pscale = r / 2.0       # PMOS widths in the code assume a P/N ratio of 2
        self.inputs = inputs
        self.outputs = outputs
        self.func = func            # function: dict(input -> 0/1) -> dict(output -> 0/1)
        self.family = family
        self.note = note
        self.devs = []

    @staticmethod
    def _grid(w):
        """Round to the 0.1 um layout grid; 0.4 um is the minimum contacted width."""
        return max(WMIN, round(w * 10) / 10)

    def n(self, d, g, s, w):
        self.devs.append(("nfet", d, g, s, "gnd", self._grid(w)))

    def p(self, d, g, s, w, fixed=False):
        w = w if fixed else w * self.pscale
        self.devs.append(("pfet", d, g, s, "vdd", self._grid(w)))

    def inv(self, a, y, wn, wp):
        self.n(y, a, "gnd", wn)
        self.p(y, a, "vdd", wp)

    def tg(self, a, b, gn, gp, wn, wp):
        """Transmission gate between a and b; on when gn = 1 (gp = 0)."""
        self.n(a, gn, b, wn)
        self.p(a, gp, b, wp)

    def _node(self, prefix):
        """A new internal node name (gate-level cells composed of several gates)."""
        self._nodes = getattr(self, "_nodes", 0) + 1
        return "%s%d" % (prefix, self._nodes)

    def nand2(self, a, b, y, k):
        """Static NAND2 with the proportions of nand2_cmos."""
        x = self._node("x")
        self.n(y, a, x, 2.0 * k)
        self.n(x, b, "gnd", 2.0 * k)
        self.p(y, a, "vdd", 2.0 * k)
        self.p(y, b, "vdd", 2.0 * k)

    def nor2(self, a, b, y, k):
        """Static NOR2 with the proportions of nor2_cmos."""
        x = self._node("x")
        self.n(y, a, "gnd", 1.0 * k)
        self.n(y, b, "gnd", 1.0 * k)
        self.p(y, a, x, 4.0 * k)
        self.p(x, b, "vdd", 4.0 * k)

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


# output buffer of the automated-flow library (not a sizing candidate):
# X1 input stage driving an X2 output stage, like OSU018 BUFX2
def buf_cmos(k=1.0, r=2.0):
    c = Cell("buf_cmos", ["A"], ["Y"], lambda v: {"Y": v["A"]}, "BUF", "static CMOS, two inverters", r=r)
    c.inv("A", "Yn", 1.0 * k, 2.0 * k)
    c.inv("Yn", "Y", 2.0 * k, 4.0 * k)
    return c


# --------------------------------------------------------------------------
# basic gates
# --------------------------------------------------------------------------
def inv_cmos(k=1.0, r=2.0):
    c = Cell("inv_cmos", ["A"], ["Y"], lambda v: {"Y": 1 - v["A"]}, "INV", "static CMOS", r=r)
    c.inv("A", "Y", 1.0 * k, 2.0 * k)
    return c


def nand2_cmos(k=1.0, r=2.0):
    c = Cell("nand2_cmos", ["A", "B"], ["Y"], lambda v: {"Y": 1 - (v["A"] & v["B"])},
             "NAND2", "static CMOS", r=r)
    c.n("Y", "A", "x", 2.0 * k)
    c.n("x", "B", "gnd", 2.0 * k)
    c.p("Y", "A", "vdd", 2.0 * k)
    c.p("Y", "B", "vdd", 2.0 * k)
    return c


def nor2_cmos(k=1.0, r=2.0):
    c = Cell("nor2_cmos", ["A", "B"], ["Y"], lambda v: {"Y": 1 - (v["A"] | v["B"])},
             "NOR2", "static CMOS", r=r)
    c.n("Y", "A", "gnd", 1.0 * k)
    c.n("Y", "B", "gnd", 1.0 * k)
    c.p("Y", "A", "x", 4.0 * k)
    c.p("x", "B", "vdd", 4.0 * k)
    return c


def and2_cmos(k=1.0, r=2.0):
    c = Cell("and2_cmos", ["A", "B"], ["Y"], lambda v: {"Y": v["A"] & v["B"]},
             "AND2", "static CMOS, NAND2 + inverter", r=r)
    c.n("Yn", "A", "x", 2.0 * k)
    c.n("x", "B", "gnd", 2.0 * k)
    c.p("Yn", "A", "vdd", 2.0 * k)
    c.p("Yn", "B", "vdd", 2.0 * k)
    c.inv("Yn", "Y", 1.0 * k, 2.0 * k)
    return c


def or2_cmos(k=1.0, r=2.0):
    c = Cell("or2_cmos", ["A", "B"], ["Y"], lambda v: {"Y": v["A"] | v["B"]},
             "OR2", "static CMOS, NOR2 + inverter", r=r)
    c.n("Yn", "A", "gnd", 1.0 * k)
    c.n("Yn", "B", "gnd", 1.0 * k)
    c.p("Yn", "A", "x", 4.0 * k)
    c.p("x", "B", "vdd", 4.0 * k)
    c.inv("Yn", "Y", 1.0 * k, 2.0 * k)
    return c


# --------------------------------------------------------------------------
# XOR2: Y = A xor B
# --------------------------------------------------------------------------
def fxor(v):
    return {"Y": X(v["A"], v["B"])}


def xor_cmos12(k=1.0, r=2.0):
    c = Cell("xor_cmos12", ["A", "B"], ["Y"], fxor, "XOR2", "static CMOS, input inverters", r=r)
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


def xor_nand16(k=1.0, r=2.0):
    """Gate-level XOR of the LTspice cell set: four NAND2 gates."""
    c = Cell("xor_nand16", ["A", "B"], ["Y"], fxor, "XOR2", "gate level, four NAND2", r=r)
    c.nand2("A", "B", "n1", k)
    c.nand2("A", "n1", "n2", k)
    c.nand2("B", "n1", "n3", k)
    c.nand2("n2", "n3", "Y", k)
    return c


def xor_tg8(k=1.0, r=2.0):
    c = Cell("xor_tg8", ["A", "B"], ["Y"], fxor, "XOR2", "transmission gate, unbuffered", r=r)
    c.inv("A", "An", 1.0 * k, 2.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("A", "Y", "Bn", "B", 1.0 * k, 2.0 * k)
    c.tg("An", "Y", "B", "Bn", 1.0 * k, 2.0 * k)
    return c


def xor_tgb10(k=1.0, r=2.0):
    c = Cell("xor_tgb10", ["A", "B"], ["Y"], fxor, "XOR2", "transmission gate + output inverter", r=r)
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("An", "Xn", "Bn", "B", 0.5 * k, 1.0 * k)      # Xn = A xnor B
    c.tg("A", "Xn", "B", "Bn", 0.5 * k, 1.0 * k)
    c.inv("Xn", "Y", 1.0 * k, 2.0 * k)
    return c


def xor_cpl14(k=1.0, r=2.0):
    c = Cell("xor_cpl14", ["A", "B"], ["Y"], fxor, "XOR2", "CPL, NMOS pass + restoring inverters", r=r)
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.n("A", "Bn", "Yi", 1.0 * k)          # Yi  = A xor B  (NMOS pass)
    c.n("An", "B", "Yi", 1.0 * k)
    c.n("An", "Bn", "Yni", 1.0 * k)        # Yni = A xnor B
    c.n("A", "B", "Yni", 1.0 * k)
    c.inv("Yni", "Y", 1.0 * k, 2.0 * k)
    c.inv("Yi", "Yn", 0.5 * k, 1.0 * k)
    c.p("Yni", "Y", "vdd", 0.4, fixed=True)   # weak level restorers
    c.p("Yi", "Yn", "vdd", 0.4, fixed=True)
    return c


# --------------------------------------------------------------------------
# MUX2: Y = S ? B : A   (inverting variants: Y = not(S ? B : A))
# --------------------------------------------------------------------------
def fmux(v):
    return {"Y": v["B"] if v["S"] else v["A"]}


def fmuxi(v):
    return {"Y": 1 - (v["B"] if v["S"] else v["A"])}


def mux_cmos12(k=1.0, r=2.0):
    c = Cell("mux_cmos12", ["A", "B", "S"], ["Y"], fmux, "MUX2", "static CMOS, AOI22 + inverter", r=r)
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


def mux_gate20(k=1.0, r=2.0):
    """Gate-level multiplexer of the LTspice cell set: inverter, two AND2, OR2."""
    c = Cell("mux_gate20", ["A", "B", "S"], ["Y"], fmux, "MUX2",
             "gate level, inverter + two AND2 + OR2", r=r)
    c.inv("S", "Sn", 1.0 * k, 2.0 * k)
    c.nand2("A", "Sn", "m1n", k)
    c.inv("m1n", "m1", 1.0 * k, 2.0 * k)
    c.nand2("B", "S", "m2n", k)
    c.inv("m2n", "m2", 1.0 * k, 2.0 * k)
    c.nor2("m1", "m2", "Yn", k)
    c.inv("Yn", "Y", 1.0 * k, 2.0 * k)
    return c


def mux_tg6(k=1.0, r=2.0):
    c = Cell("mux_tg6", ["A", "B", "S"], ["Y"], fmux, "MUX2", "transmission gate, unbuffered", r=r)
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.tg("A", "Y", "Sn", "S", 1.0 * k, 2.0 * k)
    c.tg("B", "Y", "S", "Sn", 1.0 * k, 2.0 * k)
    return c


def mux_tgb10(k=1.0, r=2.0):
    c = Cell("mux_tgb10", ["A", "B", "S"], ["Y"], fmux, "MUX2", "transmission gate + two inverters", r=r)
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.tg("A", "M", "Sn", "S", 0.5 * k, 1.0 * k)
    c.tg("B", "M", "S", "Sn", 0.5 * k, 1.0 * k)
    c.inv("M", "Mn", 0.5 * k, 1.0 * k)
    c.inv("Mn", "Y", 1.0 * k, 2.0 * k)
    return c


def muxi_cmos10(k=1.0, r=2.0):
    c = Cell("muxi_cmos10", ["A", "B", "S"], ["Y"], fmuxi, "MUX2I", "static CMOS AOI22", r=r)
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


def muxi_tg8(k=1.0, r=2.0):
    c = Cell("muxi_tg8", ["A", "B", "S"], ["Y"], fmuxi, "MUX2I", "transmission gate + output inverter", r=r)
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.tg("A", "M", "Sn", "S", 0.5 * k, 1.0 * k)
    c.tg("B", "M", "S", "Sn", 0.5 * k, 1.0 * k)
    c.inv("M", "Y", 1.0 * k, 2.0 * k)
    return c


def muxi_npt7(k=1.0, r=2.0):
    c = Cell("muxi_npt7", ["A", "B", "S"], ["Y"], fmuxi, "MUX2I",
             "NMOS pass + level restorer + inverter", r=r)
    c.inv("S", "Sn", 0.5 * k, 1.0 * k)
    c.n("A", "Sn", "M", 1.0 * k)
    c.n("B", "S", "M", 1.0 * k)
    c.inv("M", "Y", 1.0 * k, 2.0 * k)
    c.p("M", "Y", "vdd", 0.4, fixed=True)    # weak restorer pulls M to full VDD
    return c


# --------------------------------------------------------------------------
# full adder: S = A xor B xor C, CO = majority(A, B, C)
# --------------------------------------------------------------------------
def ffa(v):
    a, b, c = v["A"], v["B"], v["C"]
    return {"S": a ^ b ^ c, "CO": (a & b) | (c & (a | b))}


def fa_cmos28(k=1.0, r=2.0):
    c = Cell("fa_cmos28", ["A", "B", "C"], ["S", "CO"], ffa, "FA", "mirror adder (static CMOS)", r=r)
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


def fa_nand44(k=1.0, r=2.0):
    """Gate-level full adder of the LTspice cell set: two NAND-based XORs and three NAND2."""
    c = Cell("fa_nand44", ["A", "B", "C"], ["S", "CO"], ffa, "FA",
             "gate level, eleven NAND2", r=r)
    c.nand2("A", "B", "a1", k)            # P = A xor B
    c.nand2("A", "a1", "a2", k)
    c.nand2("B", "a1", "a3", k)
    c.nand2("a2", "a3", "P", k)
    c.nand2("P", "C", "b1", k)            # S = P xor C
    c.nand2("P", "b1", "b2", k)
    c.nand2("C", "b1", "b3", k)
    c.nand2("b2", "b3", "S", k)
    c.nand2("A", "B", "g", k)             # CO = AB + PC
    c.nand2("P", "C", "h", k)
    c.nand2("g", "h", "CO", k)
    return c


def fa_tga20(k=1.0, r=2.0):
    c = Cell("fa_tga20", ["A", "B", "C"], ["S", "CO"], ffa, "FA", "transmission-gate adder, unbuffered", r=r)
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


def fa_tgab24(k=1.0, r=2.0):
    c = Cell("fa_tgab24", ["A", "B", "C"], ["S", "CO"], ffa, "FA",
             "transmission-gate adder, inverted internals, buffered outputs", r=r)
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


# --------------------------------------------------------------------------
# ALU-specific cells: function block and carry-sum cell
# --------------------------------------------------------------------------
# The two operand bits select one of four function-code lines (the function block of
# Mead and Conway's OM-2 data path, here as a restoring transmission-gate cell). With
# the code lines set by the operation, P is the adder's propagate signal for ADD, SUB,
# INC and DEC, and the result itself for AND, OR, XOR and NOT:
#     P = C[2A + B]      codes (C0 C1 C2 C3):  ADD 0110  SUB 1001  INC 0011  DEC 1100
#                                              AND 0001  OR  0111  XOR 0110  NOT 1100
# The carry-sum cell completes the bit: CO = P ? CI : A (when P is 0 the two adder
# operands are equal, so the generate term equals A) and Y = K ? P : P xor CI, where K
# is 1 for the logic operations.
def ffb4(v):
    return {"P": v["C%d" % (2 * v["A"] + v["B"])]}


def fcs(v):
    return {"CO": v["CI"] if v["P"] else v["A"], "Y": v["P"] if v["K"] else v["P"] ^ v["CI"]}


def fb4_tg20(k=1.0, r=2.0):
    c = Cell("fb4_tg20", ["A", "B", "C0", "C1", "C2", "C3"], ["P"], ffb4, "FB4",
             "function block: 4:1 TG tree selected by the operands, restored output", r=r)
    c.inv("A", "An", 0.5 * k, 1.0 * k)
    c.inv("B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("C0", "u0", "Bn", "B", 0.5 * k, 1.0 * k)          # u0 = B ? C1 : C0
    c.tg("C1", "u0", "B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("C2", "u1", "Bn", "B", 0.5 * k, 1.0 * k)          # u1 = B ? C3 : C2
    c.tg("C3", "u1", "B", "Bn", 0.5 * k, 1.0 * k)
    c.tg("u0", "x", "An", "A", 0.5 * k, 1.0 * k)           # x = A ? u1 : u0
    c.tg("u1", "x", "A", "An", 0.5 * k, 1.0 * k)
    c.inv("x", "Pn", 0.5 * k, 1.0 * k)
    c.inv("Pn", "P", 1.0 * k, 2.0 * k)
    return c


def cs_tg24(k=1.0, r=2.0):
    c = Cell("cs_tg24", ["P", "A", "CI", "K"], ["CO", "Y"], fcs, "CS",
             "carry-sum cell: TG carry multiplexer and TG sum/result selection, restored outputs", r=r)
    c.inv("P", "Pn", 0.5 * k, 1.0 * k)
    c.inv("K", "Kn", 0.5 * k, 1.0 * k)
    c.inv("CI", "CIn", 0.5 * k, 1.0 * k)
    c.tg("CI", "cx", "P", "Pn", 0.5 * k, 1.0 * k)          # cx = P ? CI : A
    c.tg("A", "cx", "Pn", "P", 0.5 * k, 1.0 * k)
    c.inv("cx", "COn", 0.5 * k, 1.0 * k)
    c.inv("COn", "CO", 1.0 * k, 2.0 * k)
    c.tg("CI", "xn", "P", "Pn", 0.5 * k, 1.0 * k)          # xn = not (P xor CI)
    c.tg("CIn", "xn", "Pn", "P", 0.5 * k, 1.0 * k)
    c.tg("xn", "yn", "Kn", "K", 0.5 * k, 1.0 * k)          # yn = K ? not P : xn
    c.tg("Pn", "yn", "K", "Kn", 0.5 * k, 1.0 * k)
    c.inv("yn", "Y", 1.0 * k, 2.0 * k)
    return c


# gate-level cells of the LTspice cell set (compositions of NAND2, NOR2 and inverters):
# reference style of the comparison, not laid out as library cells
GATE_LEVEL = ("xor_nand16", "mux_gate20", "fa_nand44")
GATE_LEVEL_K, GATE_LEVEL_R = 0.4, 2.0   # sizes of that set: Wn 0.4 um, Wp 0.8 um inverter

CANDIDATES = [inv_cmos, nand2_cmos, nor2_cmos, and2_cmos, or2_cmos,
              xor_cmos12, xor_nand16, xor_tg8, xor_tgb10, xor_cpl14,
              mux_cmos12, mux_gate20, mux_tg6, mux_tgb10, muxi_cmos10, muxi_tg8, muxi_npt7,
              fa_cmos28, fa_nand44, fa_tga20, fa_tgab24]

# ALU-specific cells: measured with their own step (many inputs), not part of the family sweep
ALU_CELLS = [fb4_tg20, cs_tg24]
