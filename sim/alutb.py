#!/usr/bin/env python3
"""Transistor-level evaluation of an ALU netlist with Ngspice (180 nm).

One harness measures every ALU implementation of the project (the automated
standard-cell layout and the full-custom layouts), before or after layout, so
that all designs are compared with the same stimulus, load and definitions:

  * every input is driven through two X1 inverters from an ideal source (50 ps
    edges); every output drives four X1 inverters (fan-out of four),
  * the vector sequence contains every full-length carry propagation of ADD,
    SUB, INC and DEC that starts at bit 0 (a0 or b0) or at the operation select
    (s0, s1), in both directions, followed by NRAND random operand changes for
    each of the eight operations,
  * delay of a transition = time from the input of the last driver inverter of
    the latest changing input to the last 50 % crossing of any output in that
    cycle (settling time, glitches included); it is also reported from the ALU
    input pins,
  * energy of a transition = charge drawn from the ALU supply in that cycle x VDD;
    the energy of the input drivers is reported separately,
  * output levels are checked at the end of every cycle (logic value and swing
    within 10 % of the rails),
  * leakage power = mean of DC operating points at NLEAK static input states.

Netlists: a Magic extraction (flat or hierarchical, with parasitic capacitances)
or a cell-level netlist that includes its cell library. The top subcircuit is
unwrapped, bus names a[0] become a_0, supply and substrate nodes are joined to
the measured supplies, and cell libraries with other model names or a scale
option are normalized to the project models (nfet, pfet).

Usage:
  python3 alutb.py NETLIST --top alu4 --width 4 --label NAME --out DIR
         [--vdd 1.8] [--temp 27] [--period 5e-9] [--nrand 24] [--nleak 16] [--seed 1]
         [--lib CELLS.sp] [--prepare-only]
Writes DIR/NAME.json (figures of merit), DIR/NAME_transitions.csv, the testbench
and the logs, and prints one result line.
"""
import argparse
import bisect
import csv
import json
import multiprocessing as mp
import os
import random
import re
import subprocess
import sys
import time
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models", "tsmc018_t14b.lib")
EDGE = 50e-12                 # ideal source rise/fall time
FANOUT = 4
OPS = ("ADD", "SUB", "INC", "DEC", "AND", "OR", "XOR", "NOT")

# reference inverter used as driver and load (same as step3_cells/cellnet.py inv_x1:
# Wn 1.0 um, Wp 2.0 um, L 0.2 um, junctions for a 0.5 um diffusion length)
INV_X1 = """.subckt inv_x1 A Y vdd gnd
M0 Y A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends inv_x1
"""


# ----------------------------------------------------------------------------
# ALU reference model and vectors
# ----------------------------------------------------------------------------
def alu_ref(a, b, s, W):
    """(y, c, v, z, n) of rtl/alu4.v for operands a, b and select s."""
    m, msb = (1 << W) - 1, 1 << (W - 1)
    c = v = 0
    if s == 0:
        t = a + b
        y, c = t & m, t >> W
        v = int((a & msb) == (b & msb) and (y & msb) != (a & msb))
    elif s == 1:
        t = a + (~b & m) + 1
        y, c = t & m, t >> W
        v = int((a & msb) != (b & msb) and (y & msb) != (a & msb))
    elif s == 2:
        t = a + 1
        y, c = t & m, t >> W
        v = int(a == msb - 1)
    elif s == 3:
        t = a + m
        y, c = t & m, t >> W
        v = int(a == msb)
    elif s == 4:
        y = a & b
    elif s == 5:
        y = a | b
    elif s == 6:
        y = a ^ b
    else:
        y = ~a & m
    return y, c, v, int(y == 0), (y >> (W - 1)) & 1


def carries(vec, W):
    """Carry chain cy[0..W] of the bit-sliced ALU (rtl/alu4_slice.v)."""
    a, b, s = vec
    s0, s1 = s & 1, (s >> 1) & 1
    cy = [s1 ^ s0]
    for i in range(W):
        ai, bi = (a >> i) & 1, (b >> i) & 1
        bx = s0 if s1 else bi ^ s0
        p = ai ^ bx
        cy.append((ai & bx) | (cy[i] & p))
    return cy


def in_pins(W):
    return ["a_%d" % i for i in range(W)] + ["b_%d" % i for i in range(W)] + ["s_0", "s_1", "s_2"]


def out_pins(W):
    return ["y_%d" % i for i in range(W)] + ["c", "v", "z", "n"]


def pin_bits(vec, W):
    a, b, s = vec
    d = {}
    for i in range(W):
        d["a_%d" % i] = (a >> i) & 1
        d["b_%d" % i] = (b >> i) & 1
    for i in range(3):
        d["s_%d" % i] = (s >> i) & 1
    return d


def out_bits(vec, W):
    y, c, v, z, n = alu_ref(vec[0], vec[1], vec[2], W)
    d = {"y_%d" % i: (y >> i) & 1 for i in range(W)}
    d.update({"c": c, "v": v, "z": z, "n": n})
    return d


def flip(vec, pin):
    a, b, s = vec
    name, idx = pin.split("_")
    bit = 1 << int(idx)
    if name == "a":
        a ^= bit
    elif name == "b":
        b ^= bit
    else:
        s ^= bit
    return (a, b, s)


def critical_pairs(W):
    """Single-input changes that toggle every carry cy[1..W] (full-length propagation).

    One transition is kept for every (changed input, operation before, operation
    after, direction); among the candidates the one that changes most outputs.
    """
    best = {}
    for s in range(4):
        for a in range(1 << W):
            for b in range(1 << W):
                u = (a, b, s)
                cu, ou = carries(u, W), out_bits(u, W)
                for pin in ("a_0", "b_0", "s_0", "s_1"):
                    v = flip(u, pin)
                    cv = carries(v, W)
                    if any(cu[i] == cv[i] for i in range(1, W + 1)):
                        continue
                    ov = out_bits(v, W)
                    score = (sum(ou[k] != ov[k] for k in ou), -a, -b)
                    key = (pin, s, v[2], pin_bits(v, W)[pin])
                    if key not in best or score > best[key][0]:
                        best[key] = (score, u, v)
    return [(u, v) for _, (_, u, v) in sorted(best.items())]


def make_sequence(W, nrand, seed):
    """Vector list and a tag per vector: init, setup, crit, switch or op:NAME."""
    rnd = random.Random(seed)
    vecs, tags = [(0, 0, 0)], ["init"]
    for u, v in critical_pairs(W):
        if vecs[-1] != u:
            vecs.append(u)
            tags.append("setup")
        vecs.append(v)
        tags.append("crit")
    m = 1 << W
    for op in range(8):
        for j in range(nrand + 1):
            while True:
                vec = (rnd.randrange(m), rnd.randrange(m), op)
                if vec != vecs[-1]:
                    break
            vecs.append(vec)
            tags.append("switch" if j == 0 else "op:" + OPS[op])
    return vecs, tags


def leak_states(W, nleak, seed):
    rnd = random.Random(seed + 1000)
    m = 1 << W
    return [(rnd.randrange(m), rnd.randrange(m), i % 8) for i in range(nleak)]


# ----------------------------------------------------------------------------
# netlist preparation
# ----------------------------------------------------------------------------
SUPPLY = {"vdd", "vcc", "vpwr", "vdda", "vddd"}
GROUND = {"gnd", "vss", "vgnd", "gnda", "gndd", "vsubs", "vsub", "sub", "substrate", "_sub"}
SUFFIX = {"t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9,
          "p": 1e-12, "f": 1e-15, "a": 1e-18}
NUM_RE = re.compile(r"^([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)([a-zA-Z]*)$")


def spice_value(text):
    """Number of a SPICE value such as 1.2fF, 0.4u, 3meg; None if not numeric."""
    m = NUM_RE.match(text.strip())
    if not m:
        return None
    val, suf = float(m.group(1)), m.group(2).lower()
    if suf.startswith("meg"):
        return val * 1e6
    if suf and suf[0] in SUFFIX:
        return val * SUFFIX[suf[0]]
    return val


def sanitize(line):
    line = line.replace("\\", "")
    line = re.sub(r"(?<=\s)\$", "_", line)       # "$SUB": Ngspice may read " $" as a comment
    line = re.sub(r"\[(\d+)\]", r"_\1", line)
    return re.sub(r"<(\d+)>", r"_\1", line)


def logical_lines(text):
    out = []
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("*"):
            continue
        if ln.startswith("+"):
            if out:
                out[-1] += " " + ln[1:].strip()
            continue
        out.append(ln)
    return out


def node_slots(tokens):
    """Indices of the node tokens of an element line."""
    kind = tokens[0][0].lower()
    if kind == "m":
        return list(range(1, min(5, len(tokens))))
    if kind in "crldvi":
        return list(range(1, min(3, len(tokens))))
    if kind == "q":
        return list(range(1, min(4, len(tokens))))
    if kind == "x":
        plain = [i for i, t in enumerate(tokens) if "=" not in t]
        return list(range(1, plain[-1])) if len(plain) > 2 else []
    return []


def base_name(node):
    return node.split("/")[-1].lower().rstrip("!")


def normalize_devices(lines, notes, where):
    """Map other model names to nfet/pfet and apply a scale option to geometries."""
    scale = None
    kept = []
    for ln in lines:
        low = ln.lower()
        if low.startswith(".option"):
            m = re.search(r"scale\s*=\s*(\S+)", ln, re.I)
            if m:
                scale = spice_value(m.group(1))
                notes.append("%s: scale option %s applied to device sizes" % (where, m.group(1)))
                rest = re.sub(r"scale\s*=\s*\S+", "", ln, flags=re.I).split()
                if len(rest) > 1:
                    kept.append(" ".join(rest))
                continue
        kept.append(ln)
    out, renamed = [], {}
    for ln in kept:
        tok = ln.split()
        if tok and tok[0][0].lower() == "m" and len(tok) >= 6 and not tok[0].startswith("."):
            model = tok[5]
            if model.lower() not in ("nfet", "pfet"):
                new = "nfet" if model.lower().startswith("n") else "pfet" if model.lower().startswith("p") else model
                renamed[model] = new
                tok[5] = new
            if scale:
                for i in range(6, len(tok)):
                    if "=" not in tok[i]:
                        continue
                    key, val = tok[i].split("=", 1)
                    num = spice_value(val)
                    if num is None:
                        continue
                    k = key.lower()
                    if k in ("w", "l", "pd", "ps"):
                        tok[i] = "%s=%.6gu" % (key, num * scale * 1e6)
                    elif k in ("ad", "as"):
                        tok[i] = "%s=%.6gp" % (key, num * scale * scale * 1e12)
            ln = " ".join(tok)
        out.append(ln)
    for old, new in sorted(renamed.items()):
        notes.append("%s: model %s simulated as %s" % (where, old, new))
    return out


def parse_blocks(lines):
    """Split logical lines into subcircuits [name, ports, body] and top-level lines."""
    subckts, top, cur = [], [], None
    for ln in lines:
        low = ln.lower()
        if low.startswith(".subckt"):
            parts = ln.split()
            cur = [parts[1], [p for p in parts[2:] if "=" not in p], []]
            continue
        if low.startswith(".ends"):
            if cur is not None:
                subckts.append(cur)
            cur = None
            continue
        if low.startswith(".end"):
            continue
        if cur is not None:
            cur[2].append(ln)
        else:
            top.append(ln)
    return subckts, top


def is_element(ln):
    return bool(ln) and ln[0].isalpha()


def read_library(path, notes):
    """Logical lines of a cell library: .model lines dropped, devices normalized."""
    lines = [sanitize(x) for x in logical_lines(open(path).read())]
    nmodel = sum(1 for x in lines if x.lower().startswith(".model"))
    lines = [x for x in lines if not x.lower().startswith(".model") and x.lower() != ".end"]
    if nmodel:
        notes.append("library %s: %d .model lines dropped (project models used)"
                     % (os.path.basename(path), nmodel))
    return normalize_devices(lines, notes, os.path.basename(path))


def prepare_netlist(path, top, W, libs=()):
    """Prepared DUT text (top level unwrapped, supplies joined) and a report dict."""
    notes, errors = [], []
    text = open(path).read()
    base_dir = os.path.dirname(os.path.abspath(path))
    lines = [sanitize(ln) for ln in logical_lines(text)]
    expanded = []
    for lib in libs:
        if os.path.isfile(lib):
            expanded.extend(read_library(lib, notes))
        else:
            errors.append("cell library not found: %s" % lib)
    # inline included cell libraries, keep other includes with absolute paths
    for ln in lines:
        if ln.lower().startswith((".include", ".inc ", ".lib ")):
            parts = ln.split(None, 1)
            inc = parts[1].strip().strip("'\"") if len(parts) > 1 else ""
            inc_path = inc if os.path.isabs(inc) else os.path.join(base_dir, inc)
            if not os.path.isfile(inc_path):
                errors.append("include not found: %s" % inc)
                continue
            if any(os.path.samefile(inc_path, l) for l in libs if os.path.isfile(l)):
                continue
            head = open(inc_path).read()
            if re.search(r"^\s*\.subckt", head, re.I | re.M):
                expanded.extend(read_library(inc_path, notes))
            else:
                expanded.append(".include %s" % inc_path)
            continue
        expanded.append(ln)
    expanded = normalize_devices(expanded, notes, os.path.basename(path))
    subckts, top_lines = parse_blocks(expanded)

    blk = next((sc for sc in subckts if sc[0].lower() == top.lower()), None)
    if blk is None and len(subckts) == 1 and not any(is_element(l) for l in top_lines):
        blk = subckts[0]
        notes.append("top subcircuit is %s (expected %s)" % (blk[0], top))
    ports = blk[1] if blk else []
    body = blk[2] if blk else []
    others = [sc for sc in subckts if sc is not blk]
    directives = [l for l in top_lines if not is_element(l)]
    elements = [l for l in top_lines if is_element(l)] + body
    if blk is None:
        notes.append("no subcircuit %s: top-level elements used" % top)

    # supply, ground and floating-well nodes of the top level
    nodes = set()
    for ln in elements:
        tok = ln.split()
        for i in node_slots(tok):
            nodes.add(tok[i])
    nodes |= set(ports)
    rename, sup, gnd = {}, [], []
    for n in sorted(nodes):
        b = base_name(n)
        if b in SUPPLY:
            rename[n] = "vdd_dut"
            sup.append(n)
        elif b in GROUND:
            rename[n] = "gnd_dut"
            gnd.append(n)
    wells = set()
    for ln in elements:
        tok = ln.split()
        if tok[0][0].lower() == "m" and len(tok) >= 6 and tok[5].lower() == "pfet":
            bulk = tok[4]
            if bulk not in rename and base_name(bulk).startswith("w_"):
                wells.add(bulk)
    for w in sorted(wells):
        rename[w] = "vdd_dut"
    if wells:
        notes.append("%d unlabeled n-well node(s) joined to the supply" % len(wells))
    if not sup:
        errors.append("no supply node (vdd) found")
    if not gnd:
        notes.append("no ground node found by name; device bulks may use node 0")
    if len(sup) > 1:
        notes.append("%d supply node names joined: %s" % (len(sup), " ".join(sup[:4])))
    if len(gnd) > 1:
        notes.append("%d ground/substrate node names joined: %s" % (len(gnd), " ".join(gnd[:4])))

    out_el = []
    for ln in elements:
        tok = ln.split()
        for i in node_slots(tok):
            tok[i] = rename.get(tok[i], tok[i])
        out_el.append(" ".join(tok))
    ties = []
    for ln in directives:
        if ln.lower().startswith(".global"):
            for g in ln.split()[1:]:
                b = base_name(g)
                if b in SUPPLY:
                    ties.append("Vtie_%d %s vdd_dut 0" % (len(ties), g))
                elif b in GROUND:
                    ties.append("Vtie_%d %s gnd_dut 0" % (len(ties), g))

    lower = {n.lower() for n in nodes}
    missing = [p for p in in_pins(W) + out_pins(W) if p not in lower]
    if missing:
        errors.append("pins not found in the netlist: %s" % " ".join(missing))

    # device statistics (hierarchical count through subcircuit instances)
    defs = {sc[0].lower(): sc[2] for sc in others}
    memo = {}

    def count(lines_, depth=0):
        n = 0
        for ln in lines_:
            tok = ln.split()
            k = tok[0][0].lower()
            if k == "m":
                n += 1
            elif k == "x" and depth < 20:
                plain = [t for t in tok if "=" not in t]
                name = plain[-1].lower()
                if name in defs:
                    if name not in memo:
                        memo[name] = count(defs[name], depth + 1)
                    n += memo[name]
        return n

    ncap, ctot = 0, 0.0
    for ln in out_el:
        tok = ln.split()
        if tok[0][0].lower() == "c" and len(tok) >= 4:
            val = spice_value(tok[3])
            if val is not None:
                ncap += 1
                ctot += val
    ntr = count(out_el)
    if ntr < 4 * len(in_pins(W) + out_pins(W)):
        errors.append("only %d transistors in the netlist: cell layouts not extracted?" % ntr)
    report = {
        "netlist": os.path.abspath(path), "top_found": blk is not None,
        "transistors": ntr, "cell_instances": sum(1 for l in out_el if l[0].lower() == "x"),
        "capacitors": ncap, "cap_total_fF": round(ctot * 1e15, 2),
        "supply_nodes": sup, "ground_nodes": gnd, "notes": notes, "errors": errors,
    }
    parts = ["* prepared from %s by sim/alutb.py" % os.path.abspath(path)]
    for name, prt, bd in others:
        parts.append(".subckt %s %s" % (name, " ".join(prt)))
        parts.extend(bd)
        parts.append(".ends %s" % name)
    parts.extend(directives)
    parts.extend(out_el)
    parts.extend(ties)
    return "\n".join(parts) + "\n", report


# ----------------------------------------------------------------------------
# testbenches
# ----------------------------------------------------------------------------
def wrap(items, first, per=8):
    lines, cur = [], first
    for i, it in enumerate(items):
        if i and i % per == 0:
            lines.append(cur)
            cur = "+"
        cur += " " + it
    lines.append(cur)
    return lines


def write_tran_tb(path, dut_path, vecs, W, vdd, temp, period):
    pins, outs = in_pins(W), out_pins(W)
    bits = [pin_bits(v, W) for v in vecs]
    tstop = len(vecs) * period
    L = ["* transistor-level ALU testbench: %d vectors, %.3g ns per vector, %.2f V, %g C"
         % (len(vecs), period * 1e9, vdd, temp),
         ".include %s" % MODELS, INV_X1.strip(), ".include %s" % dut_path,
         ".temp %g" % temp,
         "Vdut vdd_dut 0 %g" % vdd, "Vgnd gnd_dut 0 0",
         "Vdrv tb_vdrv 0 %g" % vdd, "Vld tb_vld 0 %g" % vdd]
    for p in pins:
        pts = ["0", "%g" % (vdd * bits[0][p])]
        for k in range(1, len(vecs)):
            if bits[k][p] != bits[k - 1][p]:
                t = k * period
                pts += ["%.9g" % t, "%g" % (vdd * bits[k - 1][p]),
                        "%.9g" % (t + EDGE), "%g" % (vdd * bits[k][p])]
        L.extend(wrap(pts, "Vs_%s tb_s_%s 0 PWL(" % (p, p), per=12))
        L[-1] += " )"
        L.append("Xd1_%s tb_s_%s tb_d_%s tb_vdrv 0 inv_x1" % (p, p, p))
        L.append("Xd2_%s tb_d_%s %s tb_vdrv 0 inv_x1" % (p, p, p))
    for o in outs:
        for j in range(FANOUT):
            L.append("Xl_%s_%d %s tb_l_%s_%d tb_vld 0 inv_x1" % (o, j, o, o, j))
    saves = ["v(%s)" % p for p in pins] + ["v(tb_d_%s)" % p for p in pins] + \
            ["v(%s)" % o for o in outs] + ["i(vdut)", "i(vdrv)"]
    L.extend(wrap(saves, ".save"))
    L.append(".tran 10p %.9g 0 20p" % tstop)
    L.append(".end")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return tstop


def write_leak_tb(path, dut_path, vec, W, vdd, temp):
    bits = pin_bits(vec, W)
    L = ["* leakage at a=%d b=%d s=%d (%s), %.2f V, %g C" % (vec[0], vec[1], vec[2], OPS[vec[2]], vdd, temp),
         ".include %s" % MODELS, ".include %s" % dut_path, ".temp %g" % temp,
         ".options gmin=1e-15",
         "Vdut vdd_dut 0 %g" % vdd, "Vgnd gnd_dut 0 0"]
    for p in in_pins(W):
        L.append("V_%s %s 0 %g" % (p, p, vdd * bits[p]))
    # the dummy sweep only gives a DC analysis to measure in; the circuit does not depend on it
    L += ["Vdum tb_dum 0 0", "Rdum tb_dum 0 1k", ".dc Vdum 0 1 1",
          ".meas dc ileak find i(vdut) at=0", ".end"]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


# ----------------------------------------------------------------------------
# Ngspice output
# ----------------------------------------------------------------------------
MEAS_RE = re.compile(r"^\s*(\w+)\s*=\s*([-+]?[0-9.]+(?:[eE][-+]?[0-9]+)?)")


def norm_name(name):
    n = name.strip().lower()
    m = re.match(r"^v\((.*)\)$", n)
    if m:
        return m.group(1)
    if n.endswith("#branch"):
        return "i(%s)" % n[:-7]
    return n


def read_raw(path):
    """Columns of an Ngspice raw file (binary or ASCII, real data) by normalized name."""
    with open(path, "rb") as f:
        data = f.read()
    pos, binary = data.find(b"Binary:\n"), True
    if pos < 0:
        pos, binary = data.find(b"Values:\n"), False
    if pos < 0:
        raise ValueError("no data section in %s" % path)
    header = data[:pos].decode("latin-1")
    nvars = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    m = re.search(r"No\. Points:\s*(\d+)", header)
    npts_hdr = int(m.group(1)) if m else 0
    flags = (re.search(r"Flags:\s*(.*)", header) or re.search("()", "")).group(1).lower()
    if "complex" in flags:
        raise ValueError("complex data in %s" % path)
    names, in_vars = [], False
    for ln in header.splitlines():
        if ln.startswith("Variables:"):
            in_vars = True
            continue
        if in_vars:
            parts = ln.split()
            if len(parts) >= 2 and parts[0].isdigit():
                names.append(parts[1])
    names = names[:nvars]
    body = data[pos + 8:]
    if binary:
        npts = len(body) // (8 * nvars)
        if npts_hdr:
            npts = min(npts, npts_hdr)
        arr = array("d")
        arr.frombytes(body[:npts * nvars * 8])
        if sys.byteorder != "little":
            arr.byteswap()
    else:
        nums = body.decode("latin-1").split()
        vals, i = [], 0
        while i < len(nums):
            i += 1                      # point index
            for _ in range(nvars):
                vals.append(float(nums[i].split(",")[0]))
                i += 1
        arr = array("d", vals)
        npts = len(arr) // nvars
    return {norm_name(names[j]): arr[j::nvars][:npts] for j in range(nvars)}


def interp(t, y, x):
    i = bisect.bisect_left(t, x)
    if i <= 0:
        return y[0]
    if i >= len(t):
        return y[-1]
    t0, t1 = t[i - 1], t[i]
    return y[i - 1] + (y[i] - y[i - 1]) * (x - t0) / (t1 - t0) if t1 > t0 else y[i]


def integrate(t, y, ta, tb):
    ia, ib = bisect.bisect_right(t, ta), bisect.bisect_left(t, tb)
    pt, py, tot = ta, interp(t, y, ta), 0.0
    for i in range(ia, ib):
        tot += 0.5 * (y[i] + py) * (t[i] - pt)
        pt, py = t[i], y[i]
    return tot + 0.5 * (interp(t, y, tb) + py) * (tb - pt)


def first_cross(t, y, i0, i1, lev):
    for i in range(max(i0, 1), i1):
        y0, y1 = y[i - 1] - lev, y[i] - lev
        if (y0 < 0) != (y1 < 0):
            return t[i - 1] + (t[i] - t[i - 1]) * (-y0) / (y1 - y0)
    return None


def last_cross(t, y, i0, i1, lev):
    for i in range(i1 - 1, max(i0, 1) - 1, -1):
        y0, y1 = y[i - 1] - lev, y[i] - lev
        if (y0 < 0) != (y1 < 0):
            return t[i - 1] + (t[i] - t[i - 1]) * (-y0) / (y1 - y0)
    return None


def analyze(cols, vecs, tags, W, vdd, period):
    """Per-transition records and the summary figures of merit."""
    t = cols["time"]
    pins, outs = in_pins(W), out_pins(W)
    need = pins + ["tb_d_" + p for p in pins] + outs + ["i(vdut)", "i(vdrv)"]
    absent = [n for n in need if n not in cols]
    if absent:
        raise ValueError("vectors missing in the raw file: %s" % " ".join(absent[:6]))
    half = vdd / 2
    tstop = len(vecs) * period
    if t[-1] < tstop - 0.5 * period:
        raise ValueError("transient stopped at %.1f ns of %.1f ns" % (t[-1] * 1e9, tstop * 1e9))
    idut, idrv = cols["i(vdut)"], cols["i(vdrv)"]
    rows = []
    wrong = weak = missing = 0
    for k in range(1, len(vecs)):
        tk, te = k * period, min((k + 1) * period, tstop)
        i0, i1 = bisect.bisect_left(t, tk), bisect.bisect_left(t, te)
        prev, cur = pin_bits(vecs[k - 1], W), pin_bits(vecs[k], W)
        changed = [p for p in pins if prev[p] != cur[p]]
        ref_drv, ref_in = [], []
        for p in changed:
            ref_drv.append(first_cross(t, cols["tb_d_" + p], i0, i1, half))
            ref_in.append(first_cross(t, cols[p], i0, i1, half))
        last, last_out = None, ""
        for o in outs:
            tc = last_cross(t, cols[o], i0, i1, half)
            if tc is not None and (last is None or tc > last):
                last, last_out = tc, o
        exp = out_bits(vecs[k], W)
        bad = []
        for o in outs:
            lv = interp(t, cols[o], te - 0.05 * period)
            if (lv > half) != bool(exp[o]):
                bad.append(o)
            elif (exp[o] and lv < 0.9 * vdd) or (not exp[o] and lv > 0.1 * vdd):
                weak += 1
        wrong += bool(bad)
        d_drv = d_in = None
        if last is not None:
            if None in ref_drv or None in ref_in:
                missing += 1
            else:
                d_drv, d_in = last - max(ref_drv), last - max(ref_in)
        e_dut = -vdd * integrate(t, idut, tk, te)
        e_drv = -vdd * integrate(t, idrv, tk, te)
        a0, b0, s0 = vecs[k - 1]
        a1, b1, s1 = vecs[k]
        rows.append({
            "k": k, "tag": tags[k], "from": "%s a=%d b=%d" % (OPS[s0], a0, b0),
            "to": "%s a=%d b=%d" % (OPS[s1], a1, b1), "changed": " ".join(changed),
            "last_output": last_out if last is not None else "",
            "delay_ps": None if d_drv is None else round(d_drv * 1e12, 2),
            "delay_in_ps": None if d_in is None else round(d_in * 1e12, 2),
            "e_dut_fJ": round(e_dut * 1e15, 3), "e_drv_fJ": round(e_drv * 1e15, 3),
            "wrong_outputs": " ".join(bad),
        })
    timed = [r for r in rows if r["delay_ps"] is not None]
    worst = max(timed, key=lambda r: r["delay_ps"]) if timed else None
    res = {
        "transitions": len(rows), "timed_transitions": len(timed),
        "wrong_cycles": wrong, "weak_levels": weak, "missing_references": missing,
        "t_max_ps": worst["delay_ps"] if worst else None,
        "t_avg_ps": round(sum(r["delay_ps"] for r in timed) / len(timed), 2) if timed else None,
        "t_max_in_ps": max(r["delay_in_ps"] for r in timed) if timed else None,
        "t_crit_max_ps": max([r["delay_ps"] for r in timed if r["tag"] == "crit"] or [None],
                             key=lambda x: -1 if x is None else x),
        "t_rand_max_ps": max([r["delay_ps"] for r in timed if r["tag"].startswith("op:")] or [None],
                             key=lambda x: -1 if x is None else x),
        "worst": worst,
        "period_ps": period * 1e12,
    }
    e_op, e_drv_op = {}, {}
    for name in OPS:
        sel = [r for r in rows if r["tag"] == "op:" + name]
        if sel:
            e_op[name] = round(sum(r["e_dut_fJ"] for r in sel) / len(sel), 2)
            e_drv_op[name] = round(sum(r["e_drv_fJ"] for r in sel) / len(sel), 2)
    res["e_op_fJ"] = e_op
    res["e_drv_op_fJ"] = e_drv_op
    res["e_avg_fJ"] = round(sum(e_op.values()) / len(e_op), 2) if e_op else None
    res["e_drv_avg_fJ"] = round(sum(e_drv_op.values()) / len(e_drv_op), 2) if e_drv_op else None
    if res["e_avg_fJ"] is not None and res["t_max_ps"] is not None:
        res["edp_fJns"] = round(res["e_avg_fJ"] * res["t_max_ps"] * 1e-3, 2)
    if res["t_max_ps"] is not None and res["t_max_ps"] > 0.8 * period * 1e12:
        res["warning"] = "worst delay exceeds 80 % of the vector period; rerun with a longer --period"
    return rows, res


# ----------------------------------------------------------------------------
# running
# ----------------------------------------------------------------------------
def run_ngspice(args, cwd, timeout):
    t0 = time.time()
    try:
        r = subprocess.run(["ngspice", "-b"] + args, cwd=cwd, capture_output=True,
                           text=True, timeout=timeout)
        log = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        log = "TIMEOUT after %d s" % timeout
    except FileNotFoundError:
        log = "ngspice not found"
    return log, time.time() - t0


def _leak_job(job):
    path, cwd, vdd = job
    log, _ = run_ngspice([os.path.basename(path)], cwd, 600)
    with open(path[:-3] + ".log", "w") as f:
        f.write(log)
    for line in log.splitlines():
        m = MEAS_RE.match(line)
        if m and m.group(1).lower() == "ileak":
            return -float(m.group(2)) * vdd
    return None


def error_lines(log, n=5):
    keep = [l.strip() for l in log.splitlines()
            if re.search(r"error|fatal|singular|not found|unknown|timestep too small", l, re.I)]
    return keep[:n]


def main():
    ap = argparse.ArgumentParser(description="transistor-level ALU evaluation (Ngspice)")
    ap.add_argument("netlist")
    ap.add_argument("--top", default="alu4")
    ap.add_argument("--width", type=int, default=4)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vdd", type=float, default=1.8)
    ap.add_argument("--temp", type=float, default=27.0)
    ap.add_argument("--period", type=float, default=5e-9)
    ap.add_argument("--nrand", type=int, default=24)
    ap.add_argument("--nleak", type=int, default=16)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--lib", action="append", default=[],
                    help="cell library to include (for cell-level netlists), repeatable")
    ap.add_argument("--prepare-only", action="store_true")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    W, label = args.width, args.label
    res = {"label": label, "top": args.top, "width": W, "vdd": args.vdd, "temp": args.temp}
    json_path = os.path.join(out, label + ".json")

    def finish(status):
        res["status"] = status
        with open(json_path, "w") as f:
            json.dump(res, f, indent=1)
        line = "%-12s %s" % (label, status)
        if status == "ok":
            line += ": %d/%d cycles correct, tmax %.1f ps, E %.1f fJ/op, leak %.2f nW" % (
                res["transitions"] - res["wrong_cycles"], res["transitions"],
                res["t_max_ps"] or float("nan"), res["e_avg_fJ"] or float("nan"),
                res.get("p_leak_nW") or float("nan"))
        print(line, flush=True)

    if not os.path.isfile(args.netlist):
        res["errors"] = ["netlist not found: %s" % args.netlist]
        finish("no netlist")
        return
    text, rep = prepare_netlist(args.netlist, args.top, W, args.lib)
    res.update(rep)
    dut_path = os.path.join(out, label + "_dut.spice")
    with open(dut_path, "w") as f:
        f.write(text)
    if rep["errors"]:
        finish("netlist error")
        return
    vecs, tags = make_sequence(W, args.nrand, args.seed)
    tb = os.path.join(out, label + "_tb.sp")
    tstop = write_tran_tb(tb, dut_path, vecs, W, args.vdd, args.temp, args.period)
    states = leak_states(W, args.nleak, args.seed)
    leak_tbs = []
    for i, st in enumerate(states):
        p = os.path.join(out, "%s_leak%02d.sp" % (label, i))
        write_leak_tb(p, dut_path, st, W, args.vdd, args.temp)
        leak_tbs.append(p)
    res.update({"vectors": len(vecs), "period": args.period, "tstop": tstop,
                "critical_transitions": tags.count("crit")})
    if args.prepare_only:
        finish("prepared")
        return

    raw = os.path.join(out, label + ".raw")
    if os.path.exists(raw):
        os.remove(raw)
    pool = mp.Pool(max(1, args.jobs))
    leak_async = pool.map_async(_leak_job, [(p, out, args.vdd) for p in leak_tbs])
    log, secs = run_ngspice(["-r", os.path.basename(raw), os.path.basename(tb)], out, 7200)
    with open(tb[:-3] + ".log", "w") as f:
        f.write(log)
    res["sim_seconds"] = round(secs, 1)
    leaks = [x for x in leak_async.get() if x is not None]
    pool.close()
    pool.join()
    if leaks:
        res["p_leak_nW"] = round(sum(leaks) / len(leaks) * 1e9, 3)
        res["p_leak_max_nW"] = round(max(leaks) * 1e9, 3)
        res["leak_states"] = len(leaks)
    if not os.path.isfile(raw) or os.path.getsize(raw) < 1000:
        res["errors"] = error_lines(log) or ["no raw file written; see %s" % (tb[:-3] + ".log")]
        finish("simulation failed")
        return
    try:
        cols = read_raw(raw)
        rows, summary = analyze(cols, vecs, tags, W, args.vdd, args.period)
    except (ValueError, KeyError, IndexError) as exc:
        res["errors"] = [str(exc)] + error_lines(log)
        finish("analysis failed")
        return
    res.update(summary)
    with open(os.path.join(out, label + "_transitions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    try:
        os.remove(raw)          # large; the CSV and JSON keep the results
    except OSError:
        pass
    finish("ok")


if __name__ == "__main__":
    main()
