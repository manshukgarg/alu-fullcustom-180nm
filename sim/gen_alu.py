#!/usr/bin/env python3
"""Structural 4-bit ALU built from a cell set: transistor-level SPICE and cell-level Verilog.

The same ALU (rtl/alu4.v: ADD, SUB, INC, DEC, AND, OR, XOR, NOT, flags C V Z N) is
composed from the cells of one set, so the cell styles can be compared at ALU level
with the same structure, and so a hand-mapped netlist can go through place and route.

Two slice architectures:
  plain   follows rtl/alu4_slice.v: XOR2 and MUX2 for the operand, full adder, AND/OR/XOR/NOT,
          a 4:1 and a 2:1 output multiplexer built from non-inverting MUX2 cells;
  inv     the same function with inverting multiplexers only: the multiplexer inputs are
          supplied in the complemented polarity (NAND and NOR in place of AND and OR, XNOR
          in place of XOR, the complemented sum), so no multiplexer needs an output inverter.
  fb      function-block slice with the two ALU-specific cells: per bit one FB4 cell (the
          operand bits select one of four function-code lines) and one CS cell (carry
          multiplexer and result); a small decoder shared by all bits sets the code lines
          from the operation select.

Cell sets (SPICE, written to step6_alu_schematic/netlists/):
  gate    gate-level cells of the LTspice cell set (XOR from four NAND2, AND/OR multiplexer,
          eleven-NAND full adder), Wn 0.4 / Wp 0.8 um inverter sizing, plain
  conv    conventional static CMOS cells at the reference size, plain
  opt     minimum-PDP cells of Step 3 (step4_layout/library.json), plain
  pl      automated-flow library pl018 as laid out (tech/pl018/pl018_cells.sp), inv
  fb      FB4 and CS cells at the sizes of Step 3c (step3_cells/alu_cells.json), with
          pl018 cells for the decoder and the flags, fb
Verilog (hand-mapped netlists for place and route, written to rtl/):
  alu4_map_pl018.v    pl018 cells, inv
  alu4_fb_pl018.v     pl018 cells with pl_fb4 and pl_cs, fb
  alu4_map_osu018.v   OSU018 cells, inv

Every written netlist is read back and checked against the reference model for all
2048 input vectors: the SPICE files at switch level (sim/switchsim.py), the Verilog
files with the cell functions.

Usage:  python3 sim/gen_alu.py            write and check all netlists
        python3 sim/gen_alu.py --check    only check the netlists on disk
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "step3_cells"))

import alutb  # noqa: E402
import cellnet  # noqa: E402
import switchsim  # noqa: E402

W = 4
SPICE_DIR = os.path.join(ROOT, "step6_alu_schematic", "netlists")
RTL_DIR = os.path.join(ROOT, "rtl")

# generic cell families: input pins, output pins, function on bit masks (m = all ones)
FAMILIES = {
    "INV":   (["A"], ["Y"], lambda m, a: [~a & m]),
    "BUF":   (["A"], ["Y"], lambda m, a: [a]),
    "NAND2": (["A", "B"], ["Y"], lambda m, a, b: [~(a & b) & m]),
    "NOR2":  (["A", "B"], ["Y"], lambda m, a, b: [~(a | b) & m]),
    "AND2":  (["A", "B"], ["Y"], lambda m, a, b: [a & b]),
    "OR2":   (["A", "B"], ["Y"], lambda m, a, b: [a | b]),
    "XOR2":  (["A", "B"], ["Y"], lambda m, a, b: [a ^ b]),
    "XNOR2": (["A", "B"], ["Y"], lambda m, a, b: [~(a ^ b) & m]),
    "MUX2":  (["A", "B", "S"], ["Y"], lambda m, a, b, s: [(b & s) | (a & ~s & m)]),
    "MUX2I": (["A", "B", "S"], ["Y"], lambda m, a, b, s: [~((b & s) | (a & ~s)) & m]),
    "FA":    (["A", "B", "C"], ["S", "CO"], lambda m, a, b, c: [a ^ b ^ c, (a & b) | (c & (a | b))]),
    # ALU-specific cells: P = C[2A + B];  CO = P ? CI : A,  Y = K ? P : P xor CI
    "FB4":   (["A", "B", "C0", "C1", "C2", "C3"], ["P"],
              lambda m, a, b, c0, c1, c2, c3: [(~a & ~b & c0 | ~a & b & c1 | a & ~b & c2 | a & b & c3) & m]),
    "CS":    (["P", "A", "CI", "K"], ["CO", "Y"],
              lambda m, p, a, ci, k: [(p & ci) | (~p & a & m), (k & p) | (~k & (p ^ ci) & m)]),
}


# ----------------------------------------------------------------------------
# structure
# ----------------------------------------------------------------------------
class Builder:
    """Collects cell instances (family, name, nets in the family's pin order)."""

    def __init__(self, avail):
        self.avail = set(avail)
        self.inst = []
        self.count = {}

    def cell(self, fam, ins, outs):
        if fam not in self.avail:
            raise ValueError("cell set has no %s" % fam)
        self.count[fam] = self.count.get(fam, 0) + 1
        self.inst.append((fam, "u_%s%d" % (fam.lower(), self.count[fam]), list(ins) + list(outs)))
        return outs[0] if len(outs) == 1 else outs

    def inv(self, a, y):
        return self.cell("INV", [a], [y])

    def and2(self, a, b, y):
        if "AND2" in self.avail:
            return self.cell("AND2", [a, b], [y])
        self.cell("NAND2", [a, b], [y + "_n"])
        return self.inv(y + "_n", y)

    def or2(self, a, b, y):
        if "OR2" in self.avail:
            return self.cell("OR2", [a, b], [y])
        self.cell("NOR2", [a, b], [y + "_n"])
        return self.inv(y + "_n", y)

    def mux2(self, a, b, s, y):
        if "MUX2" in self.avail:
            return self.cell("MUX2", [a, b, s], [y])
        self.cell("MUX2I", [a, b, s], [y + "_n"])
        return self.inv(y + "_n", y)

    def xnor2(self, a, b, y):
        if "XNOR2" in self.avail:
            return self.cell("XNOR2", [a, b], [y])
        self.cell("XOR2", [a, b], [y + "_n"])
        return self.inv(y + "_n", y)


def build(arch, avail, width=W, selbuf=False):
    """Instance list of the ALU for one architecture and the available cell families.

    selbuf: buffer the operation-select lines inside the ALU (one buffer per two bits for
    a line that goes to every slice), as a designer would; the netlists for place and
    route leave this to the tool's fan-out buffering.
    """
    b = Builder(avail)
    s0, s1, s2 = "s_0", "s_1", "s_2"
    cy = ["cy_%d" % i for i in range(width + 1)]
    b.cell("XOR2", [s1, s0], [cy[0]])
    ngroup = (width + 1) // 2
    s0g, s1g, s2b = [s0] * ngroup, [s1] * ngroup, s2
    if selbuf:
        s2b = b.cell("BUF", [s2], ["s2b"])
        if arch in ("plain", "inv"):
            s0g = [b.cell("BUF", [s0], ["s0b_%d" % g]) for g in range(ngroup)]
            s1g = [b.cell("BUF", [s1], ["s1b_%d" % g]) for g in range(ngroup)]
    if arch == "inv":
        if selbuf:
            s0ng = [b.inv(s0g[g], "s0n_%d" % g) for g in range(ngroup)]
        else:
            s0ng = [b.inv(s0, "s0n")] * ngroup
    if arch == "fb":
        # function codes C[2a + b] of P for the eight operations (s2 s1 s0), x = s1 xor s0:
        #   C0 = s0 and not (s2 and not s1)      C1 = s2 ? s1 or s0 : not x
        #   C2 = s2 ? x : not s0                 C3 = s2 ? not s1 : x
        b.inv(cy[0], "xn")
        b.inv(s1, "s1n")
        b.cell("NAND2", [s2b, "s1n"], ["dt"])
        b.and2(s0, "dt", "fc0")
        b.cell("NOR2", [s1, s0], ["dnor"])
        b.cell("MUX2I", [cy[0], "dnor", s2b], ["fc1"])
        b.cell("MUX2I", [s0, "xn", s2b], ["fc2"])
        b.cell("MUX2I", ["xn", s1, s2b], ["fc3"])
    for i in range(width):
        a, bb, y = "a_%d" % i, "b_%d" % i, "y_%d" % i
        t = lambda name: "%s_%d" % (name, i)        # noqa: E731
        s0, s1, s2 = s0g[i // 2], s1g[i // 2], s2b
        if arch == "plain":
            b.cell("XOR2", [bb, s0], [t("bxs")])
            b.mux2(t("bxs"), s0, s1, t("bx"))
            b.cell("FA", [a, t("bx"), cy[i]], [t("sum"), cy[i + 1]])
            b.and2(a, bb, t("land"))
            b.or2(a, bb, t("lor"))
            b.cell("XOR2", [a, bb], [t("lxor")])
            b.inv(a, t("lnot"))
            b.mux2(t("land"), t("lor"), s0, t("m0"))
            b.mux2(t("lxor"), t("lnot"), s0, t("m1"))
            b.mux2(t("m0"), t("m1"), s1, t("lg"))
            b.mux2(t("sum"), t("lg"), s2, y)
        elif arch == "inv":
            if "XNOR2" in b.avail:
                b.cell("XNOR2", [bb, s0], [t("bxsn")])
                b.cell("XNOR2", [a, bb], [t("lxn")])
            else:
                b.inv(bb, t("bn"))
                b.cell("XOR2", [t("bn"), s0], [t("bxsn")])
                b.cell("XOR2", [a, t("bn")], [t("lxn")])
            b.cell("MUX2I", [t("bxsn"), s0ng[i // 2], s1], [t("bx")])
            b.cell("FA", [a, t("bx"), cy[i]], [t("sum"), cy[i + 1]])
            b.cell("NAND2", [a, bb], [t("lnand")])
            b.cell("NOR2", [a, bb], [t("lnor")])
            b.cell("MUX2I", [t("lnand"), t("lnor"), s0], [t("m0")])     # s0 ? a|b : a&b
            b.cell("MUX2I", [t("lxn"), a, s0], [t("m1")])               # s0 ? ~a : a^b
            b.cell("MUX2I", [t("m0"), t("m1"), s1], [t("lgn")])
            b.inv(t("sum"), t("sumn"))
            b.cell("MUX2I", [t("sumn"), t("lgn"), s2], [y])
        elif arch == "fb":
            b.cell("FB4", [a, bb, "fc0", "fc1", "fc2", "fc3"], [t("p")])
            b.cell("CS", [t("p"), a, cy[i], s2], [cy[i + 1], y])
        else:
            raise ValueError("unknown architecture %s" % arch)
    # flags: c and v only for the arithmetic operations (s2 = 0)
    b.inv(cy[width], "cyn")
    b.cell("NOR2", [s2b, "cyn"], ["c"])
    b.xnor2(cy[width - 1], cy[width], "vxn")
    b.cell("NOR2", [s2b, "vxn"], ["v"])
    terms = []
    for i in range(0, width, 2):
        terms.append(b.cell("NOR2", ["y_%d" % i, "y_%d" % (i + 1)], ["zn_%d" % (i // 2)]))
    while len(terms) > 2:
        nxt = []
        for i in range(0, len(terms), 2):
            nxt.append(b.and2(terms[i], terms[i + 1], "za_%d_%d" % (len(terms), i // 2)))
        terms = nxt
    b.and2(terms[0], terms[1], "z")
    b.inv("y_%d" % (width - 1), "nn")
    b.inv("nn", "n")
    return b.inst


# ----------------------------------------------------------------------------
# cell sets
# ----------------------------------------------------------------------------
def cellnet_set(spec):
    """spec: {family: (cellnet function name, k, r)} -> {family: (subckt name, pins, text, transistors)}."""
    out = {}
    for fam, (fname, k, r) in spec.items():
        c = getattr(cellnet, fname)(k, r)
        out[fam] = (c.name, c.inputs + c.outputs, c.spice(), c.count)
    return out


def spec_gate():
    k, r = cellnet.GATE_LEVEL_K, cellnet.GATE_LEVEL_R
    return {"INV": ("inv_cmos", k, r), "NAND2": ("nand2_cmos", k, r),
            "NOR2": ("nor2_cmos", k, r), "AND2": ("and2_cmos", k, r),
            "OR2": ("or2_cmos", k, r), "XOR2": ("xor_nand16", k, r),
            "MUX2": ("mux_gate20", k, r), "FA": ("fa_nand44", k, r),
            "BUF": ("buf_cmos", k, r)}


def spec_conv():
    return {"INV": ("inv_cmos", 1, 2), "NAND2": ("nand2_cmos", 1, 2),
            "NOR2": ("nor2_cmos", 1, 2), "AND2": ("and2_cmos", 1, 2),
            "OR2": ("or2_cmos", 1, 2), "XOR2": ("xor_cmos12", 1, 2),
            "MUX2": ("mux_cmos12", 1, 2), "FA": ("fa_cmos28", 1, 2),
            "BUF": ("buf_cmos", 1, 2)}


def spec_opt():
    lib = json.load(open(os.path.join(ROOT, "step4_layout", "library.json")))["optimized"]
    spec = {fam: (c["cell"], c["k"], c["r"]) for fam, c in lib.items() if fam in FAMILIES}
    spec["BUF"] = ("buf_cmos", 1.0, 2.5)        # the output buffer of the pl018 library
    return spec


def spec_alu_cells():
    """Sizes of the two ALU-specific cells, selected by Step 3c (step3_cells/alu_cells.json)."""
    sel = json.load(open(os.path.join(ROOT, "step3_cells", "alu_cells.json")))["cells"]
    return {fam: (sel[fam]["cell"], sel[fam]["k"], sel[fam]["r"]) for fam in ("FB4", "CS")}


def set_gate():
    return cellnet_set(spec_gate())


def set_conv():
    return cellnet_set(spec_conv())


def set_opt():
    return cellnet_set(spec_opt())


def set_pl():
    index = json.load(open(os.path.join(ROOT, "step5_library", "cells.json")))["cells"]
    text = open(os.path.join(ROOT, "tech", "pl018", "pl018_cells.sp")).read()
    out = {}
    for c in index:
        if c["family"] in FAMILIES and c["outputs"]:
            m = re.search(r"^\.subckt %s .*?^\.ends %s$" % (c["name"], c["name"]), text, re.S | re.M)
            out[c["family"]] = (c["name"], c["inputs"] + c["outputs"], m.group(0) + "\n", c["transistors"])
    return out


def set_fb():
    """pl018 with its laid-out FB4 and CS cells; the netlists of cellnet.py at the Step 3c
    sizes stand in when the library has not been generated with them."""
    cells = set_pl()
    for fam, c in cellnet_set(spec_alu_cells()).items():
        cells.setdefault(fam, c)
    return cells


SPICE_DESIGNS = [
    ("gate", "plain", set_gate, "gate-level cells of the LTspice cell set (NAND-based), k = 0.4, r = 2"),
    ("conv", "plain", set_conv, "conventional static CMOS cells at the reference size (k = 1, r = 2)"),
    ("opt", "plain", set_opt, "minimum-PDP cells of Step 3 (step4_layout/library.json)"),
    ("pl", "inv", set_pl, "automated-flow library pl018 as laid out, inverting-multiplexer slice"),
    ("fb", "fb", set_fb, "function-block slice: FB4 and CS cells per bit, pl018 cells for decoder and flags"),
]

# Verilog targets: cell name and pin names per family (generic pin -> library pin)
PL018 = {
    "INV": ("pl_inv", {}), "NAND2": ("pl_nand2", {}), "NOR2": ("pl_nor2", {}),
    "AND2": ("pl_and2", {}), "OR2": ("pl_or2", {}), "XOR2": ("pl_xor2", {}),
    "MUX2": ("pl_mux2", {}), "MUX2I": ("pl_mux2i", {}), "FA": ("pl_fa", {}),
    "FB4": ("pl_fb4", {}), "CS": ("pl_cs", {}),
}
# OSU018: MUX2X1 is Y = !(S ? A : B), so the data pins are exchanged; FAX1 names its outputs YS, YC
OSU018 = {
    "INV": ("INVX1", {}), "NAND2": ("NAND2X1", {}), "NOR2": ("NOR2X1", {}),
    "AND2": ("AND2X2", {}), "OR2": ("OR2X2", {}), "XOR2": ("XOR2X1", {}), "XNOR2": ("XNOR2X1", {}),
    "MUX2I": ("MUX2X1", {"A": "B", "B": "A"}), "FA": ("FAX1", {"S": "YS", "CO": "YC"}),
}
# functions of the OSU018 cells used, from osu018_stdcells.lib (pins in the order given)
OSU018_FUNC = {
    "INVX1": (["A"], ["Y"], lambda m, a: [~a & m]),
    "NAND2X1": (["A", "B"], ["Y"], lambda m, a, b: [~(a & b) & m]),
    "NOR2X1": (["A", "B"], ["Y"], lambda m, a, b: [~(a | b) & m]),
    "AND2X2": (["A", "B"], ["Y"], lambda m, a, b: [a & b]),
    "OR2X2": (["A", "B"], ["Y"], lambda m, a, b: [a | b]),
    "XOR2X1": (["A", "B"], ["Y"], lambda m, a, b: [a ^ b]),
    "XNOR2X1": (["A", "B"], ["Y"], lambda m, a, b: [~(a ^ b) & m]),
    "MUX2X1": (["A", "B", "S"], ["Y"], lambda m, a, b, s: [~((s & a) | (~s & b)) & m]),
    "FAX1": (["A", "B", "C"], ["YC", "YS"], lambda m, a, b, c: [(a & b) | (b & c) | (c & a), a ^ b ^ c]),
}
VERILOG_DESIGNS = [
    ("alu4_map_pl018.v", "inv", PL018, "project library pl018"),
    ("alu4_fb_pl018.v", "fb", PL018, "project library pl018"),
    ("alu4_map_osu018.v", "inv", OSU018, "OSU018 standard cells"),
]


# ----------------------------------------------------------------------------
# writers
# ----------------------------------------------------------------------------
def top_pins(width=W):
    return alutb.in_pins(width) + alutb.out_pins(width)


def write_spice(path, name, arch, cells, note, inst):
    used = []
    for fam, _, _ in inst:
        if fam not in used:
            used.append(fam)
    ntr = 0
    L = ["* 4-bit ALU, transistor level: %s" % note,
         "* slice architecture: %s; generated and checked by sim/gen_alu.py (all 2048 vectors)" % arch,
         "* models: models/tsmc018_t14b.lib (nfet, pfet); pins of alu4: inputs, outputs, vdd, gnd", ""]
    for fam in used:
        if cells[fam][1] != FAMILIES[fam][0] + FAMILIES[fam][1]:
            raise ValueError("pin order of %s differs from the %s family" % (cells[fam][0], fam))
        L.append(cells[fam][2].rstrip())
        L.append("")
    L.append(".subckt alu4 %s vdd gnd" % " ".join(top_pins()))
    for fam, iname, nets in inst:
        L.append("X%s %s vdd gnd %s" % (iname, " ".join(nets), cells[fam][0]))
        ntr += cells[fam][2].count("\nM")
    L.append(".ends alu4")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return ntr


def vnet(net):
    m = re.match(r"^([abys])_(\d+)$", net)
    return "%s[%s]" % (m.group(1), m.group(2)) if m else net


def write_verilog(path, arch, target, note, inst):
    ports = set(top_pins())
    wires = []
    for fam, _, nets in inst:
        for n in nets:
            if n not in ports and n not in wires:
                wires.append(n)
    slice_note = {"inv": "slice with inverting multiplexers",
                  "fb": "function-block slice: one FB4 and one CS cell per bit"}[arch]
    L = ["// 4-bit ALU, hand-mapped onto the %s (%s)." % (note, slice_note),
         "// Function as rtl/alu4.v. Generated and checked by sim/gen_alu.py (all 2048 vectors);",
         "// source of the hand-mapped place-and-route run.",
         "module alu4 (a, b, s, y, c, v, z, n);",
         "    input  [%d:0] a;" % (W - 1), "    input  [%d:0] b;" % (W - 1), "    input  [2:0] s;",
         "    output [%d:0] y;" % (W - 1), "    output c;", "    output v;", "    output z;", "    output n;"]
    for i in range(0, len(wires), 8):
        L.append("    wire %s;" % ", ".join(wires[i:i + 8]))
    for fam, iname, nets in inst:
        cname, pinmap = target[fam]
        pins = FAMILIES[fam][0] + FAMILIES[fam][1]
        conn = ", ".join(".%s(%s)" % (pinmap.get(p, p), vnet(n)) for p, n in zip(pins, nets))
        L.append("    %s %s (%s);" % (cname, iname, conn))
    L.append("endmodule")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


# ----------------------------------------------------------------------------
# checks
# ----------------------------------------------------------------------------
def vectors(width=W):
    """Bit masks of the input pins and the expected output pins over all vectors {s, a, b}."""
    nvec = 8 << (2 * width)
    ins = {p: 0 for p in alutb.in_pins(width)}
    outs = {p: 0 for p in alutb.out_pins(width)}
    for i in range(nvec):
        b, a, s = i & ((1 << width) - 1), (i >> width) & ((1 << width) - 1), i >> (2 * width)
        for p, bit in alutb.pin_bits((a, b, s), width).items():
            if bit:
                ins[p] |= 1 << i
        for p, bit in alutb.out_bits((a, b, s), width).items():
            if bit:
                outs[p] |= 1 << i
    return nvec, ins, outs


def compare(values, expect, nvec):
    bad = []
    for p, e in expect.items():
        if p not in values:
            bad.append("%s missing" % p)
        elif values[p] != e:
            bad.append("%s wrong in %d vectors" % (p, bin(values[p] ^ e).count("1")))
    return bad


def check_spice(path):
    nvec, ins, expect = vectors()
    subs, _ = switchsim.parse_spice(open(path).read())
    try:
        pins, devs, shorts = switchsim.flatten(subs, "alu4")
    except (KeyError, ValueError) as exc:
        return 0, [str(exc)]
    fixed = dict(ins)
    fixed["vdd"] = (1 << nvec) - 1
    fixed["gnd"] = 0
    is1, is0 = switchsim.solve(devs, shorts, fixed, nvec)
    full = (1 << nvec) - 1
    bad = []
    fights = [n for n in is1 if is1[n] & is0[n]]
    if fights:
        bad.append("%d nodes driven to 0 and 1 together, e.g. %s" % (len(fights), fights[0]))
    for p, e in expect.items():
        if p not in is1:
            bad.append("%s missing" % p)
            continue
        und = full & ~(is1[p] | is0[p])
        if und:
            bad.append("%s undriven in %d vectors" % (p, bin(und).count("1")))
        wrong = (is1[p] ^ e) & ~und & full
        if wrong:
            bad.append("%s wrong in %d vectors" % (p, bin(wrong).count("1")))
    return len(devs), bad


INST_RE = re.compile(r"^\s*(\w+)\s+(\w+)\s*\((.*)\);\s*$")
CONN_RE = re.compile(r"\.(\w+)\(([^)]*)\)")


def check_verilog(path, funcs):
    """Evaluate a structural netlist with the cell functions; funcs: {cell: (ins, outs, f)}."""
    nvec, ins, expect = vectors()
    m = (1 << nvec) - 1
    val = {vnet(p): v for p, v in ins.items()}
    todo = []
    for ln in open(path).read().splitlines():
        mt = INST_RE.match(ln)
        if mt and mt.group(1) not in ("module", "input", "output", "wire"):
            if mt.group(1) not in funcs:
                return 0, ["cell %s unknown" % mt.group(1)]
            todo.append((mt.group(1), dict(CONN_RE.findall(mt.group(3)))))
    ncell = len(todo)
    while todo:
        rest = []
        for cname, conn in todo:
            cin, cout, f = funcs[cname]
            if set(conn) != set(cin + cout):
                return ncell, ["%s: pins %s do not match the cell" % (cname, sorted(conn))]
            if all(conn[p] in val for p in cin):
                for p, v in zip(cout, f(m, *[val[conn[p]] for p in cin])):
                    val[conn[p]] = v
            else:
                rest.append((cname, conn))
        if len(rest) == len(todo):
            return ncell, ["%d cells have undriven inputs" % len(rest)]
        todo = rest
    return ncell, compare({p: val.get(vnet(p)) for p in expect}, expect, nvec)


def pl018_funcs():
    out = {}
    for c in json.load(open(os.path.join(ROOT, "step5_library", "cells.json")))["cells"]:
        if not c["outputs"]:
            continue
        ins, outs, truth = c["inputs"], c["outputs"], c["truth"]

        def f(m, *args, ins=ins, outs=outs, truth=truth):
            res = [0] * len(outs)
            for idx in range(1 << len(ins)):
                sel = m
                for j, a in enumerate(args):
                    sel &= a if (idx >> (len(ins) - 1 - j)) & 1 else ~a & m
                for k, o in enumerate(outs):
                    if truth[o][idx]:
                        res[k] |= sel
            return res
        out[c["name"]] = (ins, outs, f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only check the netlists on disk")
    args = ap.parse_args()
    os.makedirs(SPICE_DIR, exist_ok=True)
    bad_total = 0
    print("%-22s %-6s %6s %5s  %s" % ("netlist", "slice", "cells", "T", "all 2048 vectors"))
    print("(T: transistors of the circuit; wide transistors drawn as several fingers count once)")
    index = {}
    for name, arch, make, note in SPICE_DESIGNS:
        path = os.path.join(SPICE_DIR, "alu4_%s.sp" % name)
        cells = make()
        inst = build(arch, cells.keys(), selbuf=True)
        if not args.check:
            write_spice(path, name, arch, cells, note, inst)
        ntr, bad = check_spice(path) if os.path.isfile(path) else (0, ["file missing"])
        bad_total += bool(bad)
        logical = sum(cells[fam][3] for fam, _, _ in inst)
        index[name] = {"file": os.path.relpath(path, ROOT), "slice": arch, "cells": len(inst),
                       "transistors": logical, "devices_drawn": ntr, "note": note,
                       "check": "ok" if not bad else "; ".join(bad)}
        print("%-22s %-6s %6d %5d  %s" % ("alu4_%s.sp" % name, arch, len(inst), logical,
                                         "correct (switch level)" if not bad else "; ".join(bad)))
    funcs = {"alu4_map_pl018.v": pl018_funcs(), "alu4_fb_pl018.v": pl018_funcs(),
             "alu4_map_osu018.v": OSU018_FUNC}
    for fname, arch, target, note in VERILOG_DESIGNS:
        path = os.path.join(RTL_DIR, fname)
        inst = build(arch, target.keys())
        if not args.check:
            write_verilog(path, arch, target, note, inst)
        ncell, bad = check_verilog(path, funcs[fname]) if os.path.isfile(path) else (0, ["file missing"])
        bad_total += bool(bad)
        print("%-22s %-6s %6d %5s  %s" % (fname, arch, ncell, "-",
                                         "correct (cell functions)" if not bad else "; ".join(bad)))
    if not args.check:
        with open(os.path.join(SPICE_DIR, "index.json"), "w") as f:
            json.dump(index, f, indent=1)
    return 1 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
