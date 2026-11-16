#!/usr/bin/env python3
"""LTspice package: the project cells and the five 4-bit ALUs as netlists and test decks.

Writes the folder ltspice_package/ (flat, so that every .include is a plain file name):
  tsmc018.lib            transistor models (BSIM3, LEVEL 8 for LTspice and Ngspice)
  cells_<set>.lib        cell subcircuits of one cell set (gate, conv, opt, pl, alu)
  alu4_<design>.lib      the 4-bit ALU built from one cell set (subcircuit alu4_<design>)
  tb_<cell>.cir          test deck of one cell (FO4, every input transition)
  tb_alu4_<d>_function.cir   32 vectors, results as decimal words
  tb_alu4_<d>_delay.cir      the slowest transition of the design
  tb_alu4_<d>_energy.cir     192 random operand changes, energy per operation
  results_cells.csv, results_alu.csv, expected_results.txt, README.txt
and the zip file ALU4_180nm_LTspice.zip beside it.

The decks use only statements that LTspice and Ngspice share. Every deck is run here
with Ngspice and its measurements are compared with the project flow (sim/cellbench.py,
sim/alutb.py); the values found are written into the deck headers and expected_results.txt.

Inputs: the cell sizes in the repository (step4_layout/library.json, step5_library,
step3_cells/alu_cells.json) and the ALU results of step6_alu_schematic/out (run
step6_alu_schematic/run.sh first).

Usage:  python3 sim/make_ltspice_package.py [--alu-results DIR] [--zip FILE] [--no-zip]
"""
import argparse
import csv
import datetime
import hashlib
import json
import multiprocessing as mp
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "step3_cells"))

import alutb  # noqa: E402
import cellbench  # noqa: E402
import cellnet  # noqa: E402
import gen_alu  # noqa: E402

PKG = os.path.join(ROOT, "ltspice_package")
WORK = os.path.join(PKG, "_work")
ZIP_NAME = "ALU4_180nm_LTspice"
VDD, HALF = 1.8, 0.9
CELL_PERIOD, ALU_PERIOD = 2e-9, 5e-9
EDGE = 50e-12
W = 4
OPS = alutb.OPS

FUNC_TEXT = {
    "INV": "Y = not A", "BUF": "Y = A", "NAND2": "Y = not (A and B)", "NOR2": "Y = not (A or B)",
    "AND2": "Y = A and B", "OR2": "Y = A or B", "XOR2": "Y = A xor B",
    "MUX2": "Y = B if S = 1, else A", "MUX2I": "Y = not (B if S = 1, else A)",
    "FA": "S = A xor B xor C, CO = carry of A + B + C",
    "FB4": "P = C0, C1, C2, C3 for (A, B) = 00, 01, 10, 11",
    "CS": "CO = CI if P = 1, else A;  Y = P if K = 1, else P xor CI",
}
SETS = [
    ("gate", "cells_gate.lib", "gate-level cells of the LTspice cell set of 14 November, re-entered with "
     "the project models: every function composed of NAND2, NOR2 and inverters, inverter Wn 0.4 / Wp 0.8 um"),
    ("conv", "cells_conv.lib", "conventional static CMOS cells at the reference size (inverter Wn 1.0 / "
     "Wp 2.0 um)"),
    ("opt", "cells_opt.lib", "minimum-PDP cells of the sizing sweep: transmission-gate XOR, multiplexers and "
     "full adder, static NAND, NOR and inverter"),
    ("pl", "cells_pl.lib", "cells of the project standard-cell library pl018 (automated flow) as laid out: "
     "every output restored by an inverter or a static gate; wide transistors appear as parallel fingers"),
    ("alu", "cells_alu.lib", "the two ALU-specific cells of the project, as laid out for the library pl018: "
     "function block FB4 (pl_fb4) and carry-sum cell CS (pl_cs)"),
]
DESIGNS = [   # name, slice architecture, cell sets included, description
    ("gate", "plain", ["gate"], "gate-level cells (NAND-based XOR, multiplexer and full adder)"),
    ("conv", "plain", ["conv"], "conventional static CMOS cells"),
    ("opt", "plain", ["opt"], "minimum-PDP cells (transmission-gate XOR, multiplexer, full adder)"),
    ("pl", "inv", ["pl"], "library pl018, slice with inverting multiplexers"),
    ("fb", "fb", ["pl", "alu"], "proposed: FB4 and CS cell per bit, pl018 cells for decoder and flags"),
]
FUNC_PAIRS = [(5, 3), (3, 12), (15, 1), (8, 8)]

INV_X1 = """.subckt inv_x1 A Y vdd vss
M0 Y A vss vss nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends inv_x1"""


def to_vss(text):
    return re.sub(r"\bgnd\b", "vss", text)


# ----------------------------------------------------------------------------
# cells
# ----------------------------------------------------------------------------
class PkgCell:
    def __init__(self, cset, family, name, cell, text, k, r, source):
        self.set, self.family, self.name = cset, family, name
        self.cell = cell                  # cellnet.Cell carrying the package name
        self.text = text                  # subcircuit, ground pin named vss
        self.k, self.r, self.source = k, r, source
        self.transistors = cell.count
        self.res = None                   # reference figures (cellbench)


def collect_cells():
    """{set: [PkgCell]} in a fixed family order."""
    order = ["INV", "BUF", "NAND2", "NOR2", "AND2", "OR2", "XOR2", "MUX2", "MUX2I", "FA", "FB4", "CS"]
    out = {}

    def from_spec(cset, spec, names):
        cells = []
        for fam in order:
            if fam not in spec:
                continue
            fname, k, r = spec[fam]
            c = getattr(cellnet, fname)(k, r)
            c.name = names(fam, fname)
            cells.append(PkgCell(cset, fam, c.name, c, to_vss(c.spice()), k, r, fname))
        out[cset] = cells
    from_spec("gate", gen_alu.spec_gate(), lambda fam, fn: "gate_" + fam.lower())
    from_spec("conv", gen_alu.spec_conv(), lambda fam, fn: "conv_" + fam.lower())
    from_spec("opt", gen_alu.spec_opt(), lambda fam, fn: "opt_" + fam.lower())
    # pl018: the netlists of the laid-out cells (fingers), functions and sizes from library.json;
    # its two ALU-specific cells go into their own file
    lib = json.load(open(os.path.join(ROOT, "step5_library", "library.json")))["cells"]
    laid = gen_alu.set_pl()
    out["pl"], out["alu"] = [], []
    for fam in order:
        if fam not in lib or fam not in laid:
            continue
        e = lib[fam]
        c = getattr(cellnet, e["cell"])(e["k"], e["r"])
        name, pins, text, ntr = laid[fam]
        if pins != c.inputs + c.outputs:
            raise ValueError("pin order of %s differs from %s" % (name, e["cell"]))
        c.name = name
        cset = "alu" if fam in ("FB4", "CS") else "pl"
        out[cset].append(PkgCell(cset, fam, name, c, to_vss(text), e["k"], e["r"], e["cell"]))
    if len(out["alu"]) != 2:
        raise ValueError("the library pl018 has no FB4 and CS cells (step5_library/gen_library.py)")
    return out


def write_cell_lib(path, title, cells):
    L = ["* %s" % os.path.basename(path)]
    for ln in wrap_comment(title[0].upper() + title[1:] + "."):
        L.append("* " + ln)
    L += ["* 180 nm (TSMC 0.18 um BSIM3 models in tsmc018.lib, devices nfet and pfet), L = 0.2 um.",
          "* Pin order of every cell: inputs, outputs, vdd, vss.",
          "*", "* %-10s %-3s  %s" % ("cell", "T", "function / circuit")]
    for pc in cells:
        L.append("* %-10s %-3d  %s" % (pc.name, pc.transistors, FUNC_TEXT[pc.family]))
        L.append("* %-10s %-3s  %s; width scale k = %g, P/N ratio r = %g" % ("", "", pc.cell.note, pc.k, pc.r))
    L.append("")
    for pc in cells:
        L.append(pc.text.rstrip())
        L.append("")
    with open(path, "w") as f:
        f.write("\n".join(L))


def wrap_comment(text, width=92):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


ALLCELLS = []          # set before the worker pool starts (cells hold functions, not picklable)


def cell_reference(index):
    """Figures of merit and output events of one cell with the project flow (cellbench)."""
    pc = ALLCELLS[index]
    seq = "single" if len(pc.cell.inputs) > 3 else "all"
    r = cellbench.evaluate(pc.cell, VDD, CELL_PERIOD, WORK, pc.k, pc.r, sequence=seq,
                           dut_text=pc.text, tag="_ref", detail=True)
    return pc.name, r


def tn(t):
    """A time in SPICE notation, in ns (2.05n)."""
    return "%.9gn" % (t * 1e9)


def pwl(points):
    """PWL argument lines from [(t, v)], wrapped with + continuation."""
    items = ["%s %g" % (tn(t), v) for t, v in points]
    lines, cur = [], ""
    for it in items:
        if cur and len(cur) + 1 + len(it) > 100:
            lines.append(cur)
            cur = it
        else:
            cur = (cur + " " + it).strip()
    lines.append(cur)
    return lines


def source(name, node, levels, period):
    """PWL source lines for a list of 0/1 levels, one per period."""
    pts = [(0, VDD * levels[0])]
    for k in range(1, len(levels)):
        if levels[k] != levels[k - 1]:
            pts.append((k * period, VDD * levels[k - 1]))
            pts.append((k * period + EDGE, VDD * levels[k]))
    ls = pwl(pts)
    out = ["%s %s 0 PWL(%s" % (name, node, ls[0])]
    out += ["+ " + x for x in ls[1:]]
    out[-1] += ")"
    return out


def write_cell_deck(pc, libfile):
    c, r = pc.cell, pc.res
    states = r["states"]
    vecs = [cellbench.bits(s, c.inputs) for s in states]
    tstop = len(vecs) * CELL_PERIOD
    digits = len(str(len(vecs)))
    seq_text = "every input transition once" if r["sequence"] == "all" else \
        "every change of one input in every state of the other inputs"
    worst = max(r["events"], key=lambda e: e["delay_ps"])
    wname = "d%0*d_%s" % (digits, worst["k"], worst["out"])
    L = ["* tb_%s.cir  test of cell %s (%s, %d transistors)" % (pc.name, pc.name, pc.family, pc.transistors),
         "* Function: %s" % FUNC_TEXT[pc.family],
         "* 1.8 V, 27 C. Every input is driven through two X1 inverters, every output drives four",
         "* X1 inverters. Sequence: %s (%d transitions)," % (seq_text, len(vecs) - 1),
         "* %g ns per state; data are saved from the first transition (%g ns)." % (
             CELL_PERIOD * 1e9, CELL_PERIOD * 1e9),
         "* Measurements (LTspice: View > SPICE Error Log):",
         "*   dNN_<output>  delay of the output change in step NN, from the input of the last driver",
         "*                 inverter (node d_<input>) to the 50 % point of the output",
         "*   p_uW          average power in uW, cell and input drivers",
         "*   worst delay = largest dNN value;  PDP = p_uW x worst delay",
         "* Ngspice 46:  worst delay %.1f ps (%s),  power %.2f uW,  PDP %.2f fJ" % (
             r["t_max_ps"], wname, r["p_total_uW"], r["pdp_fJ"]),
         ".include tsmc018.lib", ".include %s" % libfile, ".options plotwinsize=0",
         INV_X1,
         "Vcut vcut 0 %g" % VDD, "Vdrv vdrv 0 %g" % VDD, "Vld vld 0 %g" % VDD]
    if len(c.inputs) <= 3:
        L.insert(5, "* States (%s): %s" % (" ".join(c.inputs), " ".join(
            "".join(str(v[n]) for n in c.inputs) for v in vecs)))
    for nm in c.inputs:
        L += source("Vs_%s" % nm, "s_%s" % nm, [v[nm] for v in vecs], CELL_PERIOD)
        L.append("Xd1_%s s_%s d_%s vdrv 0 inv_x1" % (nm, nm, nm))
        L.append("Xd2_%s d_%s %s vdrv 0 inv_x1" % (nm, nm, nm))
    L.append("Xcut %s vcut 0 %s" % (" ".join(c.inputs + c.outputs), pc.name))
    for o in c.outputs:
        for j in range(4):
            L.append("Xl_%s_%d %s ld_%s_%d vld 0 inv_x1" % (o, j, o, o, j))
    L.append("Bpw pw 0 V=-(I(Vcut)+I(Vdrv))*%g" % (VDD * 1e6))
    L.append(".tran 1p %s %s 10p" % (tn(tstop), tn(CELL_PERIOD)))
    names = []
    for e in r["events"]:
        td = tn(e["k"] * CELL_PERIOD)
        name = "d%0*d_%s" % (digits, e["k"], e["out"])
        names.append(name)
        L.append(".meas tran %s TRIG V(d_%s) VAL=%g TD=%s %s=1 TARG V(%s) VAL=%g TD=%s %s=1" % (
            name, e["pin"], HALF, td, e["pin_dir"].upper(), e["out"], HALF, td, e["out_dir"].upper()))
    L.append(".meas tran p_uW AVG V(pw)")
    L.append(".end")
    path = os.path.join(PKG, "tb_%s.cir" % pc.name)
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return os.path.basename(path), names


# ----------------------------------------------------------------------------
# ALU netlists and decks
# ----------------------------------------------------------------------------
def design_cells(cells, sets):
    """{family: PkgCell} of a design; the later set wins (alu over pl)."""
    out = {}
    for s in sets:
        for pc in cells[s]:
            out[pc.family] = pc
    return out


def write_alu_lib(name, arch, sets, note, cells):
    fam = design_cells(cells, sets)
    inst = gen_alu.build(arch, fam.keys(), selbuf=True)
    used = []
    for f_, _, _ in inst:
        if f_ not in used:
            used.append(f_)
    ntr = sum(fam[f_].transistors for f_, _, _ in inst)
    pins = alutb.in_pins(W) + alutb.out_pins(W)
    L = ["* alu4_%s.lib  4-bit ALU, transistor level: %s" % (name, note),
         "* Subcircuit alu4_%s; pins: a_0..a_3, b_0..b_3, s_0..s_2, y_0..y_3, c, v, z, n, vdd, vss" % name,
         "* (index 0 is the least significant bit). Operation select s_2 s_1 s_0:",
         "*   000 ADD   001 SUB   010 INC   011 DEC   100 AND   101 OR   110 XOR   111 NOT (of a)",
         "* Flags: c carry out (1 = no borrow for SUB and DEC), v signed overflow, z result zero,",
         "* n result negative; c and v are 0 for the logic operations.",
         "* %d cell instances, %d transistors. Cells used (%s):" % (
             len(inst), ntr, ", ".join("cells_%s.lib" % s for s in sets)),
         "*   " + ", ".join("%s x %d" % (fam[f_].name, sum(1 for i in inst if i[0] == f_)) for f_ in used),
         "* Requires: .include tsmc018.lib and the cell files named above.", "",
         ".subckt alu4_%s %s vdd vss" % (name, " ".join(pins))]
    for f_, iname, nets in inst:
        L.append("X%s %s vdd vss %s" % (iname, " ".join(nets), fam[f_].name))
    L.append(".ends alu4_%s" % name)
    with open(os.path.join(PKG, "alu4_%s.lib" % name), "w") as f:
        f.write("\n".join(L) + "\n")
    return len(inst), ntr


def alu_bench(name, sets, vecs, period):
    """Common part of the ALU decks: includes, supplies, input drivers, ALU, loads, word nodes."""
    bits = [alutb.pin_bits(v, W) for v in vecs]
    L = [".include tsmc018.lib"] + [".include cells_%s.lib" % s for s in sets]
    L += [".include alu4_%s.lib" % name, ".options plotwinsize=0", INV_X1,
          "Vdut vdd_dut 0 %g" % VDD, "Vdrv vdrv 0 %g" % VDD, "Vld vld 0 %g" % VDD]
    for p in alutb.in_pins(W):
        L += source("Vs_%s" % p, "s_%s" % p, [b[p] for b in bits], period)
        L.append("Xd1_%s s_%s d_%s vdrv 0 inv_x1" % (p, p, p))
        L.append("Xd2_%s d_%s %s vdrv 0 inv_x1" % (p, p, p))
    L.append("Xalu %s vdd_dut 0 alu4_%s" % (" ".join(alutb.in_pins(W) + alutb.out_pins(W)), name))
    for o in alutb.out_pins(W):
        for j in range(4):
            L.append("Xl_%s_%d %s ld_%s_%d vld 0 inv_x1" % (o, j, o, o, j))
    word = lambda pre: "+".join("%d*V(%s_%d)" % (1 << i, pre, i) for i in range(W))   # noqa: E731
    L += ["* decimal words for plotting and measuring: operands, operation, result, flags (8c+4v+2z+n)",
          "Baw aw 0 V=(%s)/%g" % (word("a"), VDD), "Bbw bw 0 V=(%s)/%g" % (word("b"), VDD),
          "Bsw sw 0 V=(V(s_0)+2*V(s_1)+4*V(s_2))/%g" % VDD,
          "Byw yw 0 V=(%s)/%g" % (word("y"), VDD),
          "Bfw fw 0 V=(8*V(c)+4*V(v)+2*V(z)+V(n))/%g" % VDD]
    return L


def save_lines(extra):
    items = ["V(aw)", "V(bw)", "V(sw)", "V(yw)", "V(fw)"] + \
            ["V(%s)" % p for p in alutb.in_pins(W) + alutb.out_pins(W)] + extra
    lines, cur = [], ".save"
    for it in items:
        if len(cur) + 1 + len(it) > 100:
            lines.append(cur)
            cur = "+"
        cur += " " + it
    lines.append(cur)
    return lines


def flags_word(vec):
    y, c, v, z, n = alutb.alu_ref(vec[0], vec[1], vec[2], W)
    return y, 8 * c + 4 * v + 2 * z + n, "%d%d%d%d" % (c, v, z, n)


def write_function_deck(name, sets, note):
    vecs = [(0, 0, 0)] + [(a, b, op) for op in range(8) for a, b in FUNC_PAIRS]
    tstop = len(vecs) * ALU_PERIOD
    L = ["* tb_alu4_%s_function.cir  function test of the 4-bit ALU, %s" % (name, note),
         "* 32 vectors (8 operations x 4 operand pairs), %g ns each, after one start vector." % (ALU_PERIOD * 1e9),
         "* Inputs through two X1 inverters, every output loaded with four X1 inverters.",
         "* Plot V(yw) (result as a decimal word), V(fw) (flags, 8c + 4v + 2z + n), V(aw), V(bw), V(sw).",
         "* Measurements yNN, fNN: result and flag words 0.25 ns before the end of vector NN;",
         "* they must equal the columns y and fw of this table:",
         "*   NN  time (ns)   op    a   b  |   y  cvzn  fw"]
    for k in range(1, len(vecs)):
        a, b, s = vecs[k]
        y, fw, ftxt = flags_word(vecs[k])
        L.append("*   %02d  %3d - %3d  %-4s %3d %3d  |  %2d  %s  %2d" % (
            k, k * ALU_PERIOD * 1e9, (k + 1) * ALU_PERIOD * 1e9, OPS[s], a, b, y, ftxt, fw))
    L += alu_bench(name, sets, vecs, ALU_PERIOD)
    L += save_lines(["I(Vdut)"])
    L.append(".tran 10p %s 0 20p" % tn(tstop))
    expect = {}
    for k in range(1, len(vecs)):
        t = tn((k + 1) * ALU_PERIOD - 0.05 * ALU_PERIOD)
        L.append(".meas tran y%02d FIND V(yw) AT=%s" % (k, t))
        L.append(".meas tran f%02d FIND V(fw) AT=%s" % (k, t))
        y, fw, _ = flags_word(vecs[k])
        expect["y%02d" % k], expect["f%02d" % k] = y, fw
    L.append(".end")
    fname = "tb_alu4_%s_function.cir" % name
    with open(os.path.join(PKG, fname), "w") as f:
        f.write("\n".join(L) + "\n")
    return fname, expect


def op_text(vec):
    return "%s a=%d b=%d" % (OPS[vec[2]], vec[0], vec[1])


def write_delay_deck(name, sets, note, res, outs_cross=None):
    """The slowest transition of the design in the project test (sim/alutb.py)."""
    vecs, _ = alutb.make_sequence(W, 24, 1)
    k = res["worst"]["k"]
    u, v = vecs[k - 1], vecs[k]
    bu, bv = alutb.pin_bits(u, W), alutb.pin_bits(v, W)
    changed = [p for p in alutb.in_pins(W) if bu[p] != bv[p]]
    outs = outs_cross if outs_cross is not None else alutb.out_pins(W)
    yu, fu, tu = flags_word(u)
    yv, fv, tv = flags_word(v)
    L = ["* tb_alu4_%s_delay.cir  slowest transition of the 4-bit ALU, %s" % (name, note),
         "* The transition with the largest settling delay among the 229 transitions of the project",
         "* test: 18 full-length carry propagations, 24 random operand changes per operation and the",
         "* changes between them.",
         "*   before: %-16s y = %2d, flags cvzn = %s" % (op_text(u), yu, tu),
         "*   after:  %-16s y = %2d, flags cvzn = %s   (inputs change at %g ns)" % (
             op_text(v), yv, tv, ALU_PERIOD * 1e9),
         "* Data are saved from %g ns. Measurements:" % (ALU_PERIOD * 1e9),
         "*   tin_<input>   time at which the input of the last driver inverter crosses 50 %",
         "*   t_<output>    time of the last 50 % crossing of an output (glitches included)",
         "*   e_fJ          energy drawn by the ALU for this transition, in fJ",
         "*   delay = latest t_<output> - latest tin_<input>",
         "* Ngspice 46 (project flow): delay %.1f ps, last output %s, energy %.0f fJ" % (
             res["worst"]["delay_ps"], res["worst"]["last_output"], res["worst"]["e_dut_fJ"])]
    L += alu_bench(name, sets, [u, v], ALU_PERIOD)
    L.append("Befj efj 0 V=-I(Vdut)*%g" % (VDD * ALU_PERIOD * 1e15))
    L += save_lines(["V(d_%s)" % p for p in changed] + ["V(efj)", "I(Vdut)"])
    L.append(".tran 10p %s %s 20p" % (tn(2 * ALU_PERIOD), tn(ALU_PERIOD)))
    for p in changed:
        L.append(".meas tran tin_%s WHEN V(d_%s)=%g %s=1" % (p, p, HALF, "FALL" if bv[p] else "RISE"))
    for o in outs:
        L.append(".meas tran t_%s WHEN V(%s)=%g CROSS=LAST" % (o, o, HALF))
    L.append(".meas tran e_fJ AVG V(efj)")
    L.append(".end")
    fname = "tb_alu4_%s_delay.cir" % name
    with open(os.path.join(PKG, fname), "w") as f:
        f.write("\n".join(L) + "\n")
    return fname, changed


def write_energy_deck(name, sets, note, res):
    """The 192 random operand changes of the project test; energy per operation."""
    vecs, tags = alutb.make_sequence(W, 24, 1)
    i0 = tags.index("switch")
    seq, stags = vecs[i0 - 1:], ["start"] + tags[i0:]
    nop = sum(t.startswith("op:") for t in stags)
    tstop = len(seq) * ALU_PERIOD
    pts, lvl = [(0, 0)], 0
    for k in range(1, len(seq)):
        new = 1 if stags[k].startswith("op:") else 0
        if new != lvl:
            pts += [(k * ALU_PERIOD - 1e-12, lvl), (k * ALU_PERIOD, new)]
            lvl = new
    ls = pwl(pts)
    scale = VDD * (tstop - ALU_PERIOD) / nop * 1e15
    L = ["* tb_alu4_%s_energy.cir  energy per operation of the 4-bit ALU, %s" % (name, note),
         "* %d vectors of %g ns: for each of the 8 operations one change to the operation and then" % (
             len(seq) - 1, ALU_PERIOD * 1e9),
         "* 24 random operand changes. V(win) is 1 during the %d random operand changes; the energy" % nop,
         "* drawn from the ALU supply during them, divided by %d, is the energy per operation." % nop,
         "* Data are saved from %g ns. Measurement:" % (ALU_PERIOD * 1e9),
         "*   e_op_fJ   energy per operation in fJ (average over the 8 operations)",
         "* Ngspice 46 (project flow): %.1f fJ" % res["e_avg_fJ"]]
    L += alu_bench(name, sets, seq, ALU_PERIOD)
    L.append("Vwin win 0 PWL(%s" % ls[0])
    L += ["+ " + x for x in ls[1:]]
    L[-1] += ")"
    L.append("Befj efj 0 V=-I(Vdut)*V(win)*%.9g" % scale)
    L += save_lines(["V(win)", "V(efj)", "I(Vdut)"])
    L.append(".tran 10p %s %s 20p" % (tn(tstop), tn(ALU_PERIOD)))
    L.append(".meas tran e_op_fJ AVG V(efj)")
    L.append(".end")
    fname = "tb_alu4_%s_energy.cir" % name
    with open(os.path.join(PKG, fname), "w") as f:
        f.write("\n".join(L) + "\n")
    return fname


# ----------------------------------------------------------------------------
# guide
# ----------------------------------------------------------------------------
def alu_cell_comparison():
    """Lines comparing FB4 and CS with the same functions composed of library cells (Step 3c)."""
    path = os.path.join(ROOT, "step3_cells", "out", "alu_cells.csv")
    if not os.path.isfile(path):
        return []
    rows = list(csv.DictReader(open(path)))
    sel = json.load(open(os.path.join(ROOT, "step3_cells", "alu_cells.json")))["cells"]
    L = ["  %-44s %3s %11s %11s %9s" % ("circuit", "T", "delay (ps)", "power (uW)", "PDP (fJ)")]
    for fam, label in (("FB4", "pl_fb4"), ("CS", "pl_cs")):
        own = [r for r in rows if r["family"] == fam and r["version"] == "size"
               and float(r["k"]) == sel[fam]["k"] and float(r["r"]) == sel[fam]["r"]]
        refs = [r for r in rows if r["family"] == fam and r["version"] != "size"]
        for r, name in [(own[0], label)] + [(r, "same function, " + r["version"]) for r in refs]:
            L.append("  %-44s %3d %11.1f %11.2f %9.2f" % (
                name[:44], float(r["transistors"]), float(r["t_max_ps"]), float(r["p_total_uW"]),
                float(r["pdp_fJ"])))
    return L


def write_readme(cells, cell_rows, alu_rows, date):
    by = {r["cell"]: r for r in cell_rows}
    ref = [r for r in alu_rows if r["design"] == "conv"][0]
    T = []
    T += ["4-bit ALU in 180 nm CMOS: cells, ALU netlists and test decks for LTspice",
          "=" * 72,
          "Project: Design and Performance Analysis of a Full-Custom 4-bit ALU Using Optimized",
          "Standard Cells. Package of %s." % date, "",
          "The package holds the transistor-level circuits of the project in a form that runs",
          "directly in LTspice: five cell sets, the 4-bit ALU built from each of them, and a test",
          "deck with expected results for every cell and every ALU.", "",
          "1. Files", "--------",
          "  tsmc018.lib                 transistor models (TSMC 0.18 um, BSIM3v3, devices nfet, pfet)",
          "  cells_gate.lib              gate-level cells: XOR, multiplexer and full adder from NAND2,",
          "                              NOR2 and inverters (the cell set of the LTspice deliverable",
          "                              of 14 November, re-entered with the 180 nm models)",
          "  cells_conv.lib              conventional static CMOS cells, reference size",
          "  cells_opt.lib               minimum-PDP cells of the sizing sweep (transmission-gate",
          "                              XOR, multiplexers and full adder)",
          "  cells_pl.lib                cells of the project standard-cell library pl018 as laid out",
          "  cells_alu.lib               the two ALU-specific cells: function block pl_fb4 and",
          "                              carry-sum cell pl_cs (section 6)",
          "  alu4_<design>.lib           the 4-bit ALU, one file per design (section 5)",
          "  tb_<cell>.cir               test deck of one cell (%d decks)" % len(cell_rows),
          "  tb_alu4_<design>_function.cir   function test, 32 vectors, results as decimal words",
          "  tb_alu4_<design>_delay.cir      slowest transition of the design",
          "  tb_alu4_<design>_energy.cir     energy per operation (192 random operand changes)",
          "  expected_results.txt        measured values of every deck (Ngspice 46)",
          "  results_cells.csv, results_alu.csv   the tables of sections 4 and 5", "",
          "2. Technology and conventions", "-----------------------------",
          "  Supply 1.8 V, 27 C. Channel length 0.2 um for every transistor. Model names nfet and",
          "  pfet; the model file uses LEVEL = 8, the BSIM3v3 level of LTspice and Ngspice.",
          "  Every source and drain carries the junction of a 0.5 um long diffusion (ad, as, pd, ps).",
          "  Cell pins: inputs, outputs, vdd, vss. Sizes: k scales all widths of a cell (k = 1:",
          "  inverter with Wn = 1.0 um), r is the ratio Wp / Wn; widths are rounded to 0.1 um and",
          "  not smaller than 0.4 um.",
          "  Test conditions of every deck: each input is driven through two inverters of the",
          "  reference size (X1: Wn 1.0 um, Wp 2.0 um), each output drives four X1 inverters (FO4).",
          "  Delays are measured between 50 % points, from the input of the last driver inverter,",
          "  so the loading of the driver by the cell input is part of the delay; the power of a",
          "  cell deck includes the two driver inverters of every input.", "",
          "3. Running a deck in LTspice", "----------------------------",
          "  1. Extract the zip and keep all files in one folder (the decks include the other",
          "     files by name).",
          "  2. LTspice: File > Open, file type 'Netlists', select a tb_*.cir file.",
          "  3. Simulate > Run.",
          "  4. Waveforms: Plot Settings > Add Trace. Node names: cell pins as in the cell file",
          "     (A, B, Y, ...), ALU pins a_0 .. a_3, b_0 .. b_3, s_0 .. s_2, y_0 .. y_3, c, v, z, n.",
          "     The ALU decks also provide the words V(aw), V(bw), V(sw), V(yw), V(fw): operands,",
          "     operation, result and flags as decimal numbers (1 V = 1).",
          "  5. Measured values: View > SPICE Error Log. The header of every deck explains its",
          "     measurements and states the expected values; expected_results.txt lists them all.",
          "  The numbers of this package were obtained with Ngspice 46, the simulator of the",
          "  project's layout flow; every deck was run there and agrees with the project scripts.",
          "  The decks contain only statements common to LTspice and Ngspice. LTspice evaluates",
          "  BSIM3 at version 3.3 and has its own time-step control, so its values can differ",
          "  from expected_results.txt by a few percent; the first LTspice run of a deck should be",
          "  compared with that file.", "",
          "4. Cells", "--------",
          "  Worst delay over all input transitions, average power including the input drivers,",
          "  PDP = power x worst delay (values of the cell decks). T: transistors.", ""]
    for cset, fname, title in SETS:
        T.append("  %s" % fname)
        T.append("  %-11s %3s %5s %4s %11s %11s %9s  %s" % (
            "cell", "T", "k", "r", "delay (ps)", "power (uW)", "PDP (fJ)", "circuit"))
        for pc in cells[cset]:
            r = by.get(pc.name)
            if r:
                T.append("  %-11s %3d %5g %4g %11.1f %11.2f %9.2f  %s" % (
                    pc.name, pc.transistors, pc.k, pc.r, r["worst_delay_ps"], r["power_uW"],
                    r["pdp_fJ"], pc.cell.note))
        T.append("")
    T += ["  pl_fb4 and pl_cs have six and four inputs; their decks apply every change of one input",
          "  in every state of the other inputs (384 and 64 transitions). The other decks apply",
          "  every transition between two input states.", "",
          "5. The 4-bit ALU", "----------------",
          "  Inputs a_3..a_0, b_3..b_0, operation select s_2 s_1 s_0; outputs y_3..y_0 and the flags",
          "  c, v, z, n.",
          "    s = 000 ADD  y = a + b        100 AND  y = a and b",
          "        001 SUB  y = a - b        101 OR   y = a or b",
          "        010 INC  y = a + 1        110 XOR  y = a xor b",
          "        011 DEC  y = a - 1        111 NOT  y = not a",
          "  c: carry out (1 = no borrow for SUB and DEC); v: signed overflow; z: y = 0; n: y_3.",
          "  c and v are 0 for the logic operations.", "",
          "  Designs (subcircuit alu4_<design> in alu4_<design>.lib):",
          "    gate  cells_gate.lib. Per bit: XOR and multiplexer for the second operand, full",
          "          adder, AND, OR, XOR, NOT, and four 2:1 multiplexers selecting the result.",
          "    conv  cells_conv.lib, same structure.",
          "    opt   cells_opt.lib, same structure.",
          "    pl    cells_pl.lib; same function with inverting multiplexers, which need no output",
          "          inverter (NAND, NOR and XNOR in place of AND, OR and XOR).",
          "    fb    proposed design: per bit one function block pl_fb4 and one carry-sum cell",
          "          pl_cs (section 6); a decoder of ten library cells, shared by the four bits,",
          "          and the flag logic use cells_pl.lib.",
          "  In every design the select lines are buffered inside the ALU.", "",
          "  Results (project test: 229 transitions; all outputs correct in every design)",
          "  %-7s %6s %12s %11s %12s %9s %10s" % (
              "design", "cells", "transistors", "delay (ps)", "energy (fJ)", "leak (nW)", "E x D"),
          ]
    for r in alu_rows:
        T.append("  %-7s %6d %12d %11.1f %12.1f %9.2f %10.1f" % (
            r["design"], r["cell_instances"], r["transistors"], r["worst_delay_ps"],
            r["energy_per_operation_fJ"], r["leakage_nW"], r["energy_x_delay_fJns"]))
    T += ["", "  Against the conventional design (conv):",
          "  %-7s %12s %11s %12s %9s %10s" % ("design", "transistors", "delay", "energy", "leakage", "E x D")]
    pct = lambda a, b: "%+.0f %%" % (100.0 * (a / b - 1))        # noqa: E731
    for r in alu_rows:
        if r["design"] == "conv":
            continue
        T.append("  %-7s %12s %11s %12s %9s %10s" % (
            r["design"], pct(r["transistors"], ref["transistors"]),
            pct(r["worst_delay_ps"], ref["worst_delay_ps"]),
            pct(r["energy_per_operation_fJ"], ref["energy_per_operation_fJ"]),
            pct(r["leakage_nW"], ref["leakage_nW"]),
            pct(r["energy_x_delay_fJns"], ref["energy_x_delay_fJns"])))
    T += ["",
          "  delay    largest settling delay over the 229 transitions of the test (18 full-length",
          "           carry propagations, 24 random operand changes per operation and the changes",
          "           between them): from the input of the last driver inverter to the last 50 %",
          "           crossing of any output, glitches included. tb_alu4_<design>_delay.cir repeats",
          "           this transition from a settled state and agrees within 0.5 %.",
          "  energy   energy drawn from the ALU supply per operation, mean over the 192 random",
          "           operand changes (tb_alu4_<design>_energy.cir).",
          "  leak     static power, mean over 16 input states.",
          "  E x D    energy x delay in fJ ns.", "",
          "6. The two ALU-specific cells", "-----------------------------",
          "  pl_fb4 (function block, 20 transistors). P = C0, C1, C2 or C3 for (A, B) = 00, 01, 10,",
          "  11: the operand bits select one of four function-code lines through a tree of six",
          "  transmission gates, followed by two inverters that restore the level. The code lines",
          "  are common to all bits and set by the operation, so P is any function of a and b:",
          "      operation    P            C0 C1 C2 C3   carry in   K",
          "      ADD          a xor b       0  1  1  0       0      0",
          "      SUB          a xnor b      1  0  0  1       1      0",
          "      INC          a             0  0  1  1       1      0",
          "      DEC          not a         1  1  0  0       0      0",
          "      AND          a and b       0  0  0  1       -      1",
          "      OR           a or b        0  1  1  1       -      1",
          "      XOR          a xor b       0  1  1  0       -      1",
          "      NOT          not a         1  1  0  0       -      1",
          "  pl_cs (carry-sum cell, 24 transistors). CO = CI if P = 1, else A; Y = P if K = 1, else",
          "  P xor CI. For the arithmetic operations P is the propagate signal; when it is 0 the",
          "  carry out equals the operand bit a, so no generate signal is needed. K = s_2 selects",
          "  the logic result P or the sum.",
          "  One pl_fb4 and one pl_cs form a complete ALU bit (44 transistors) in place of the",
          "  operand logic, full adder, logic gates and result multiplexers of the other designs.", ""]
    cmp_lines = alu_cell_comparison()
    if cmp_lines:
        T += ["  Against the same functions composed of library cells (FO4, single-input changes):"]
        T += cmp_lines + [""]
    T += ["  Origin of the ideas: a function block steered by four code lines is the ALU principle",
          "  of the OM-2 data path of Mead and Conway (Introduction to VLSI Systems, 1980), there",
          "  in nMOS pass-transistor logic with a precharged carry chain; a carry multiplexer",
          "  steered by the propagate signal with the operand as its second input, followed by an",
          "  XOR for the sum, is the carry logic of FPGA logic cells. The work of this project is",
          "  their combination into two restoring transmission-gate standard cells for a static",
          "  CMOS cell flow, the sizing and layout of these cells in 180 nm, and the measured",
          "  comparison with the conventional cell-based ALU.", ""]
    with open(os.path.join(PKG, "README.txt"), "w") as f:
        f.write("\n".join(T) + "\n")


def write_zip(path):
    names = sorted(n for n in os.listdir(PKG) if not n.startswith("_") and os.path.isfile(os.path.join(PKG, n)))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(PKG, n), "%s/%s" % (ZIP_NAME, n))
    return len(names)


# ----------------------------------------------------------------------------
# running the decks with Ngspice
# ----------------------------------------------------------------------------
MEAS_RE = re.compile(r"^\s*([a-z]\w*)\s*=\s*([-+]?[0-9.]+(?:[eE][-+]?[0-9]+)?)(?:\s|$)", re.M)


CACHE = None


def deck_key(fname):
    text = open(os.path.join(PKG, fname)).read()
    h = hashlib.sha1(text.encode())
    for inc in re.findall(r"^\.include\s+(\S+)", text, re.M):
        h.update(open(os.path.join(PKG, inc)).read().encode())
    return h.hexdigest()


def run_deck(fname):
    cpath = os.path.join(CACHE, deck_key(fname) + ".json") if CACHE else None
    if cpath and os.path.isfile(cpath):
        d = json.load(open(cpath))
        return fname, d["vals"], d["err"]
    fname, vals, err = _run_deck(fname)
    if cpath and vals:
        with open(cpath + ".tmp", "w") as f:
            json.dump({"deck": fname, "vals": vals, "err": err}, f)
        os.replace(cpath + ".tmp", cpath)
    return fname, vals, err


def _run_deck(fname):
    try:
        r = subprocess.run(["ngspice", "-b", fname], cwd=PKG, capture_output=True, text=True, timeout=7200)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return fname, {}, str(exc)
    text = r.stdout + r.stderr
    vals = {m.group(1).lower(): float(m.group(2)) for m in MEAS_RE.finditer(text)}
    errs = [ln for ln in text.splitlines() if re.search(r"\berror\b|failed|unknown subckt|singular", ln, re.I)]
    return fname, vals, "; ".join(errs[:3])


def run_all(decks, jobs):
    with mp.Pool(jobs) as pool:
        return {f: (vals, err) for f, vals, err in pool.imap_unordered(run_deck, decks)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alu-results", default=os.path.join(ROOT, "step6_alu_schematic", "out"))
    ap.add_argument("--jobs", type=int, default=max(1, min(8, os.cpu_count() or 2)))
    ap.add_argument("--zip", default=os.path.join(ROOT, ZIP_NAME + ".zip"), help="zip file to write")
    ap.add_argument("--no-zip", action="store_true")
    ap.add_argument("--date", default=datetime.date.today().strftime("%d %B %Y").lstrip("0"))
    ap.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "alu_ltspice_cache"),
                    help="finished Ngspice runs are kept here, so an interrupted run continues")
    args = ap.parse_args()
    global CACHE
    CACHE = args.cache
    os.makedirs(CACHE, exist_ok=True)

    alu_res = {}
    for name, _, _, _ in DESIGNS:
        p = os.path.join(args.alu_results, name + ".json")
        alu_res[name] = json.load(open(p)) if os.path.isfile(p) else {}
        if alu_res[name].get("status") != "ok":
            sys.exit("no ALU result for '%s' in %s (run step6_alu_schematic/run.sh first)" % (
                name, args.alu_results))
    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    os.makedirs(WORK)
    problems = []

    # models: LEVEL 8 is BSIM3v3 in LTspice and in Ngspice (49 is the HSPICE number)
    text = open(os.path.join(ROOT, "models", "tsmc018_t14b.lib")).read()
    text, nsub = re.subn(r"LEVEL\s*=\s*49", "LEVEL   = 8 ", text)
    if nsub != 2:
        sys.exit("model file: expected two LEVEL = 49 entries")
    text = text.replace("* SPICE level 49 (HSPICE) / level 8 or 49 (ngspice); VDD = 1.8 V",
                        "* LEVEL = 8 (BSIM3v3 in LTspice and Ngspice; HSPICE uses 49); VDD = 1.8 V")
    with open(os.path.join(PKG, "tsmc018.lib"), "w") as f:
        f.write(text)

    cells = collect_cells()
    for cset, fname, title in SETS:
        write_cell_lib(os.path.join(PKG, fname), title, cells[cset])
    libfile = {cset: fname for cset, fname, _ in SETS}
    allcells = [pc for cset, _, _ in SETS for pc in cells[cset]]

    print("cells: reference figures of %d cells (cellbench)" % len(allcells), flush=True)
    ALLCELLS[:] = allcells
    with mp.Pool(args.jobs) as pool:
        ref = dict(pool.imap_unordered(cell_reference, range(len(allcells))))
    cell_decks = {}
    for pc in allcells:
        pc.res = ref[pc.name]
        if pc.res["wrong_levels"] or pc.res["missing_delays"] or pc.res["weak_levels"]:
            problems.append("%s: reference run has %d wrong, %d weak levels, %d missing delays" % (
                pc.name, pc.res["wrong_levels"], pc.res["weak_levels"], pc.res["missing_delays"]))
        cell_decks[pc.name] = write_cell_deck(pc, libfile[pc.set])

    design_info = {}
    func_expect, delay_inputs = {}, {}
    for name, arch, sets, note in DESIGNS:
        ninst, ntr = write_alu_lib(name, arch, sets, note, cells)
        design_info[name] = {"cells": ninst, "transistors": ntr, "note": note, "sets": sets}
        fn, func_expect[name] = write_function_deck(name, sets, note)
        _, delay_inputs[name] = write_delay_deck(name, sets, note, alu_res[name])
        write_energy_deck(name, sets, note, alu_res[name])

    # ---- run every deck with Ngspice and compare with the project flow ----
    decks = [d for d, _ in cell_decks.values()]
    decks += ["tb_alu4_%s_%s.cir" % (n, kind) for n, _, _, _ in DESIGNS for kind in ("function", "delay")]
    print("ngspice: %d cell, function and delay decks" % len(decks), flush=True)
    out = run_all(decks, args.jobs)
    # delay decks: keep the measurements of the outputs that cross, then run them again
    for name, arch, sets, note in DESIGNS:
        vals, err = out["tb_alu4_%s_delay.cir" % name]
        crossing = [o for o in alutb.out_pins(W) if "t_" + o in vals]
        write_delay_deck(name, sets, note, alu_res[name], crossing)
    decks2 = ["tb_alu4_%s_delay.cir" % n for n, _, _, _ in DESIGNS]
    decks2 += ["tb_alu4_%s_energy.cir" % n for n, _, _, _ in DESIGNS]
    print("ngspice: %d delay and energy decks" % len(decks2), flush=True)
    out.update(run_all(decks2, args.jobs))

    E = ["Expected results of the test decks (Ngspice 46, 1.8 V, 27 C)", "=" * 60, "",
         "Cell decks: worst delay = largest dNN value, power = p_uW, PDP = power x worst delay", "",
         "%-22s %10s %-10s %9s %8s" % ("deck", "delay (ps)", "measure", "p_uW", "PDP (fJ)")]
    cell_rows = []
    for cset, _, _ in SETS:
        for pc in cells[cset]:
            deck, names = cell_decks[pc.name]
            vals, err = out[deck]
            r = pc.res
            got = {n: vals.get(n.lower()) for n in names}
            if err or None in got.values() or "p_uw" not in vals:
                problems.append("%s: %s" % (deck, err or "%d measurements missing" % (
                    sum(v is None for v in got.values()) + ("p_uw" not in vals))))
                continue
            wn = max(got, key=lambda n: got[n])
            tmax, pw = got[wn] * 1e12, vals["p_uw"]
            if abs(tmax - r["t_max_ps"]) > max(1.0, 0.005 * r["t_max_ps"]):
                problems.append("%s: worst delay %.1f ps, project flow %.1f ps" % (deck, tmax, r["t_max_ps"]))
            if abs(pw - r["p_total_uW"]) > 0.01 * r["p_total_uW"]:
                problems.append("%s: power %.2f uW, project flow %.2f uW" % (deck, pw, r["p_total_uW"]))
            E.append("%-22s %10.1f %-10s %9.2f %8.2f" % (deck, tmax, wn, pw, pw * tmax * 1e-3))
            cell_rows.append({
                "set": cset, "cell": pc.name, "function": FUNC_TEXT[pc.family], "circuit": pc.cell.note,
                "transistors": pc.transistors, "k": pc.k, "r": pc.r,
                "worst_delay_ps": round(tmax, 1), "power_uW": round(pw, 2),
                "pdp_fJ": round(pw * tmax * 1e-3, 2), "transitions": r["transitions"],
                "sequence": "all input transitions" if r["sequence"] == "all" else "single-input changes",
                "deck": deck})
    E += ["", "ALU decks", "",
          "%-28s %s" % ("deck", "result")]
    alu_rows = []
    for name, arch, sets, note in DESIGNS:
        res = alu_res[name]
        deck = "tb_alu4_%s_function.cir" % name
        vals, err = out[deck]
        bad = [k for k, e in func_expect[name].items() if k not in vals or abs(vals[k] - e) > 0.05]
        if err or bad:
            problems.append("%s: %s" % (deck, err or "%d words differ, e.g. %s" % (len(bad), bad[0])))
        E.append("%-28s %d of %d words as in the table of the deck" % (
            deck, len(func_expect[name]) - len(bad), len(func_expect[name])))
        deck = "tb_alu4_%s_delay.cir" % name
        vals, err = out[deck]
        tins = [vals.get("tin_" + p) for p in delay_inputs[name]]
        touts = {o: vals["t_" + o] for o in alutb.out_pins(W) if "t_" + o in vals}
        if err or None in tins or not touts or "e_fj" not in vals:
            problems.append("%s: %s" % (deck, err or "measurements missing"))
            delay = float("nan")
        else:
            last = max(touts, key=lambda o: touts[o])
            delay = (touts[last] - max(tins)) * 1e12
            if abs(delay - res["worst"]["delay_ps"]) > max(2.0, 0.005 * res["worst"]["delay_ps"]):
                problems.append("%s: delay %.1f ps, project flow %.1f ps" % (deck, delay, res["worst"]["delay_ps"]))
            E.append("%-28s delay %.1f ps = t_%s (%.4f ns) - latest tin (%.4f ns); e_fJ %.0f" % (
                deck, delay, last, touts[last] * 1e9, max(tins) * 1e9, vals["e_fj"]))
        deck = "tb_alu4_%s_energy.cir" % name
        vals, err = out[deck]
        e_op = vals.get("e_op_fj")
        if err or e_op is None:
            problems.append("%s: %s" % (deck, err or "measurement missing"))
        else:
            if abs(e_op - res["e_avg_fJ"]) > 0.01 * res["e_avg_fJ"]:
                problems.append("%s: %.1f fJ, project flow %.1f fJ" % (deck, e_op, res["e_avg_fJ"]))
            E.append("%-28s e_op_fJ %.1f" % (deck, e_op))
        info = design_info[name]
        alu_rows.append({
            "design": name, "cells_used": note, "cell_instances": info["cells"],
            "transistors": info["transistors"], "cycles_correct": "%d/%d" % (
                res["transitions"] - res["wrong_cycles"], res["transitions"]),
            "worst_delay_ps": round(res["t_max_ps"], 1), "mean_delay_ps": round(res["t_avg_ps"], 1),
            "energy_per_operation_fJ": round(res["e_avg_fJ"], 1),
            "energy_x_delay_fJns": round(res["e_avg_fJ"] * res["t_max_ps"] * 1e-3, 1),
            "leakage_nW": res.get("p_leak_nW")})
    with open(os.path.join(PKG, "expected_results.txt"), "w") as f:
        f.write("\n".join(E) + "\n")
    for fname, rows in (("results_cells.csv", cell_rows), ("results_alu.csv", alu_rows)):
        if rows:
            with open(os.path.join(PKG, fname), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    shutil.rmtree(WORK, ignore_errors=True)
    for fn in os.listdir(PKG):
        if fn.endswith(".log") or fn.endswith(".raw"):
            os.remove(os.path.join(PKG, fn))

    write_readme(cells, cell_rows, alu_rows, args.date)
    if not args.no_zip and not problems:
        n = write_zip(args.zip)
        print("zip: %s (%d files)" % (args.zip, n))
    print("package: %d files in %s" % (len(os.listdir(PKG)), os.path.relpath(PKG, ROOT)))
    print("decks checked with Ngspice: %d cell decks, %d ALU decks" % (len(cell_decks), 3 * len(DESIGNS)))
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  " + p)
        return 1
    print("every deck agrees with the project flow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
