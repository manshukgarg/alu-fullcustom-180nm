#!/usr/bin/env python3
"""Live simulation views: a cell or an ALU is simulated with Ngspice, the result is checked
against its function and printed as a table, and the waveforms are opened in Ngspice's
plot windows.

  python3 demo/tools/wave.py cell fb4|cs          the two ALU-specific cells
  python3 demo/tools/wave.py alu-test [design]    32-vector function test of a 4-bit ALU
  python3 demo/tools/wave.py alu-delay [design]   the slowest transition of a 4-bit ALU
  designs: gate conv opt pl fb (default fb, the proposed ALU)
  python3 demo/tools/wave.py chip-test [layout]   32-vector test of a routed ALU: the netlist
                                                  extracted from its layout by Magic
  layouts: fb beh slice map (Step 5), osu-beh osu-slice osu-map (Step 2); default fb
  --no-plot    table only

Cells: the extracted layout netlist of Step 5 (step5_library/out/cells) when it exists,
otherwise the netlist of the drawn layout (tech/pl018/pl018_cells.sp). ALUs: the netlists
and decks of ltspice_package/ (the 4-bit ALU from each cell set). Routed ALUs: the flat
netlist with every transistor and parasitic capacitance (qflow_<layout>/layout/alu4_pex.spice)
of the last lab run. Every input is driven through two inverters of the reference size and
every output drives four of them.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.dirname(HERE)
ROOT = os.path.dirname(DEMO)
OUT = os.path.join(DEMO, "out")
PKG = os.path.join(ROOT, "ltspice_package")
sys.path.insert(0, os.path.join(ROOT, "sim"))

import alutb  # noqa: E402

VDD, HALF = 1.8, 0.9
EDGE = 50e-12
MODELS = os.path.join(ROOT, "models", "tsmc018_t14b.lib")
INV_X1 = """.subckt inv_x1 A Y vdd gnd
M0 Y A gnd gnd nfet w=1u l=0.2u ad=0.5p as=0.5p pd=3u ps=3u
M1 Y A vdd vdd pfet w=2u l=0.2u ad=1p as=1p pd=5u ps=5u
.ends inv_x1"""
DESIGNS = {"gate": "gate-level cells (NAND-based XOR, multiplexer and full adder)",
           "conv": "conventional static CMOS cells",
           "opt": "minimum-PDP cells, conventional slice",
           "pl": "library pl018, inverting-multiplexer slice",
           "fb": "proposed: function block FB4 and carry-sum cell CS per bit"}
W = 4


def ngspice_batch(deck, raw, cwd):
    if os.path.exists(raw):
        os.remove(raw)
    t0 = time.time()
    r = subprocess.run(["ngspice", "-b", "-r", raw, deck], cwd=cwd, capture_output=True, text=True)
    log = r.stdout + r.stderr
    with open(os.path.splitext(raw)[0] + ".log", "w") as f:
        f.write(log)
    if not os.path.isfile(raw):
        sys.exit("Ngspice did not finish; see %s" % os.path.splitext(raw)[0] + ".log")
    return time.time() - t0


def open_plots(raw, lets, plots):
    """Ngspice in interactive mode: load the waveforms and open one window per plot."""
    ctl = os.path.splitext(raw)[0] + "_plot.sp"
    # white background, black grid and text; dark trace colours that stay readable on a projector
    # (Ngspice's defaults include khaki and pink); the first trace of a plot is red
    colours = ["red", "blue", "darkgreen", "darkorange", "purple", "brown", "black", "magenta"]
    L = ["* waveform view (demo/tools/wave.py)", ".control", "set color0=white", "set color1=black"]
    L += ["set color%d=%s" % (k + 2, c) for k, c in enumerate(colours)]
    L += ["set xbrushwidth=2", "load %s" % raw]
    L += ["let %s = %s" % (n, e) for n, e in lets]
    L += ["plot %s title \"%s\"" % (" ".join(vs), title) for title, vs in plots]
    L += ["echo", "echo \"Plot windows are open. Type quit to leave Ngspice.\"", ".endc", ".end"]
    with open(ctl, "w") as f:
        f.write("\n".join(L) + "\n")
    print("\nOpening the waveforms in Ngspice (type quit in the terminal to close) ...")
    sys.stdout.flush()
    os.execvp("ngspice", ["ngspice", ctl])


def pwl(name, node, levels, period):
    pts = ["0 %g" % (VDD * levels[0])]
    for k in range(1, len(levels)):
        if levels[k] != levels[k - 1]:
            t = k * period
            pts.append("%.9gn %g" % (t * 1e9, VDD * levels[k - 1]))
            pts.append("%.9gn %g" % ((t + EDGE) * 1e9, VDD * levels[k]))
    return "%s %s 0 PWL(%s)" % (name, node, " ".join(pts))


# ----------------------------------------------------------------------------
# cells
# ----------------------------------------------------------------------------
def logical(text):
    out = []
    for ln in text.splitlines():
        ln = ln.rstrip()
        if ln.startswith("+") and out:
            out[-1] += " " + ln[1:].strip()
        elif ln.strip() and not ln.startswith("*"):
            out.append(ln)
    return out


def cell_netlist(name, inputs, outputs):
    """(subcircuit text, source) of a library cell: the Magic extraction of Step 5 when it
    exists, wrapped to the pin order inputs, outputs, vdd, gnd; else the drawn devices."""
    pex = os.path.join(ROOT, "step5_library", "out", "cells", name + "_pex.spice")
    pins = inputs + outputs + ["vdd", "gnd"]
    if os.path.isfile(pex):
        body, ports = [], None
        for ln in logical(open(pex).read()):
            low = ln.lower()
            if low.startswith(".end") and not low.startswith(".ends"):
                continue
            if low.startswith(".subckt"):
                parts = ln.split()
                ports = [p for p in parts[2:] if "=" not in p]
                ln = " ".join([parts[0], name + "_x"] + ports)
            body.append(ln)
        if ports:
            conn = []
            for p in ports:
                lp = p.lower()
                if p in pins:
                    conn.append(p)
                elif lp in ("vdd!", "vdd") or lp.startswith("w_"):
                    conn.append("vdd")
                elif "sub" in lp or lp in ("gnd!", "0", "gnd"):
                    conn.append("gnd")
                else:
                    conn.append(p)
            text = "\n".join(body) + "\n.subckt %s %s\nXpex %s %s_x\n.ends %s\n" % (
                name, " ".join(pins), " ".join(conn), name, name)
            return text, "layout extracted by Magic (Step 5), parasitic capacitances included"
    out, on = [], False
    for ln in logical(open(os.path.join(ROOT, "tech", "pl018", "pl018_cells.sp")).read()):
        low = ln.lower()
        if low.startswith(".subckt") and ln.split()[1] == name:
            on = True
        if on:
            out.append(ln)
            if low.startswith(".ends"):
                break
    return "\n".join(out) + "\n", "devices of the drawn layout (run Step 5 for the extracted netlist)"


FB4_FUNCS = [("ADD   a xor b", (0, 1, 1, 0)), ("SUB   a xnor b", (1, 0, 0, 1)), ("INC   a", (0, 0, 1, 1)),
             ("DEC   not a", (1, 1, 0, 0)), ("AND   a and b", (0, 0, 0, 1)), ("OR    a or b", (0, 1, 1, 1))]


def cell_demo(which, plot):
    period = 2e-9
    if which == "fb4":
        name, inputs, outputs = "pl_fb4", ["A", "B", "C0", "C1", "C2", "C3"], ["P"]
        states, groups = [], []
        for label, code in FB4_FUNCS:
            groups.append((label, code, len(states)))
            for a, b in ((0, 0), (0, 1), (1, 0), (1, 1)):
                states.append({"A": a, "B": b, "C0": code[0], "C1": code[1], "C2": code[2], "C3": code[3]})

        def func(v):
            return {"P": v["C%d" % (2 * v["A"] + v["B"])]}
    else:
        name, inputs, outputs = "pl_cs", ["P", "A", "CI", "K"], ["CO", "Y"]
        states = [{"K": k, "P": p, "A": a, "CI": ci} for k in (0, 1) for p in (0, 1)
                  for a in (0, 1) for ci in (0, 1)]

        def func(v):
            return {"CO": v["CI"] if v["P"] else v["A"],
                    "Y": v["P"] if v["K"] else v["P"] ^ v["CI"]}
    states = [states[0]] + states          # a settled start state
    text, source = cell_netlist(name, inputs, outputs)
    ntr = sum(1 for ln in text.splitlines() if ln[:1].lower() == "m")
    os.makedirs(OUT, exist_ok=True)
    deck = os.path.join(OUT, "%s_demo.sp" % name)
    raw = os.path.join(OUT, "%s_demo.raw" % name)
    L = ["* %s: every function, Ngspice demonstration" % name, ".include %s" % MODELS, INV_X1, text,
         "Vdd vdd 0 %g" % VDD]
    for p in inputs:
        L.append(pwl("Vs_" + p, "s_" + p, [s[p] for s in states], period))
        L.append("Xd1_%s s_%s d_%s vdd 0 inv_x1" % (p, p, p))
        L.append("Xd2_%s d_%s %s vdd 0 inv_x1" % (p, p, p))
    L.append("Xcell %s vdd 0 %s" % (" ".join(inputs + outputs), name))
    for o in outputs:
        L += ["Xl_%s_%d %s ld_%s_%d vdd 0 inv_x1" % (o, j, o, o, j) for j in range(4)]
    L.append(".save " + " ".join(["v(%s)" % p for p in inputs + outputs] + ["v(d_%s)" % p for p in inputs]))
    L += [".tran 2p %.9gn" % (len(states) * period * 1e9), ".end"]
    with open(deck, "w") as f:
        f.write("\n".join(L) + "\n")
    print("=" * 79)
    print("%s, %d transistors: Ngspice transient, 1.8 V, 27 C" % (name, ntr))
    print("netlist: %s" % source)
    sys.stdout.flush()
    dt = ngspice_batch(deck, raw, OUT)
    cols = alutb.read_raw(raw)
    t = cols["time"]
    got, delays = [], []
    for k, s in enumerate(states):
        te = (k + 1) * period - 0.05 * period
        got.append({o: int(alutb.interp(t, cols[o.lower()], te) > HALF) for o in outputs})
        if k == 0:
            continue
        i0 = alutb.bisect.bisect_left(t, k * period)
        i1 = alutb.bisect.bisect_left(t, (k + 1) * period)
        changed = [p for p in inputs if s[p] != states[k - 1][p]]
        ref = [alutb.first_cross(t, cols["d_" + p.lower()], i0, i1, HALF) for p in changed]
        for o in outputs:
            if func(s)[o] != func(states[k - 1])[o] and None not in ref:
                tc = alutb.first_cross(t, cols[o.lower()], i0, i1, HALF)
                if tc is not None:
                    delays.append(tc - max(ref))
    bad = sum(got[k] != func(s) for k, s in enumerate(states))
    print("simulated %d states in %.1f s" % (len(states) - 1, dt))
    print("-" * 79)
    if which == "fb4":
        print("  operation          code C0..C3   P for (a, b) = 00 01 10 11   expected   check")
        for label, code, k0 in groups:
            sim = [got[1 + k0 + j]["P"] for j in range(4)]
            exp = list(code)
            print("  %-18s %s       %s              %s    %s" % (
                label, " ".join(map(str, code)), "  ".join(map(str, sim)), " ".join(map(str, exp)),
                "ok" if sim == exp else "WRONG"))
    else:
        print("   K  P  A  CI |  CO  Y | expected CO Y | check")
        for k in range(1, len(states)):
            s, e = states[k], func(states[k])
            if k in (1, 9):
                print("  %s" % ("arithmetic (K = 0): CO = P ? CI : A,  Y = P xor CI" if s["K"] == 0
                                else "logic (K = 1): Y = P"))
            print("   %d  %d  %d  %d  |  %d   %d |   %d  %d        | %s" % (
                s["K"], s["P"], s["A"], s["CI"], got[k]["CO"], got[k]["Y"], e["CO"], e["Y"],
                "ok" if got[k] == e else "WRONG"))
    print("-" * 79)
    print("%s: %d of %d states correct; output changes %d, slowest %.0f ps, mean %.0f ps" % (
        name, len(states) - 1 - bad, len(states) - 1, len(delays),
        max(delays) * 1e12 if delays else float("nan"),
        sum(delays) / len(delays) * 1e12 if delays else float("nan")))
    print("(delay from the input of the inverter driving the changed input to the output, FO4 load)")
    if plot:
        n = len(inputs) + len(outputs)
        lets, names = [], []
        for i, p in enumerate(inputs + outputs):
            nm = p.lower() + ("_out" if p in outputs else "_in")
            lets.append((nm, "v(%s)+%d" % (p.lower(), 2 * (n - 1 - i))))
            names.append(nm)
        # outputs first, so that they get the first trace colours
        order = names[len(inputs):] + names[:len(inputs)]
        open_plots(raw, lets, [("%s: inputs (top) and outputs (bottom), offset 2 V each" % name, order)])


# ----------------------------------------------------------------------------
# ALUs
# ----------------------------------------------------------------------------
def alu_raw(design, kind):
    deck = "tb_alu4_%s_%s.cir" % (design, kind)
    if not os.path.isfile(os.path.join(PKG, deck)):
        sys.exit("%s not found in ltspice_package/" % deck)
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(OUT, "alu4_%s_%s.raw" % (design, kind))
    ntr = int(open(os.path.join(PKG, "alu4_%s.lib" % design)).read().split(" transistors")[0].split()[-1])
    print("=" * 79)
    print("4-bit ALU '%s' (%s), %d transistors" % (design, DESIGNS[design], ntr))
    print("Ngspice transient, 1.8 V, 27 C; deck ltspice_package/%s" % deck)
    sys.stdout.flush()
    dt = ngspice_batch(deck, raw, PKG)
    return alutb.read_raw(raw), raw, dt


def flags_of(a, b, s):
    y, c, v, z, n = alutb.alu_ref(a, b, s, W)
    return y, c, v, z, n


def alu_test(design, plot):
    cols, raw, dt = alu_raw(design, "function")
    pairs = [(5, 3), (3, 12), (15, 1), (8, 8)]
    vecs = [(0, 0, 0)] + [(a, b, s) for s in range(8) for a, b in pairs]
    period = 5e-9
    t = cols["time"]
    print("simulated %d vectors (%d ns) in %.1f s" % (len(vecs) - 1, len(vecs) * 5, dt))
    print("-" * 79)
    print("  vec  op     a   b |  y   c v z n | expected y  c v z n | check")
    good = 0
    for k in range(1, len(vecs)):
        a, b, s = vecs[k]
        te = (k + 1) * period - 0.05 * period
        y = round(alutb.interp(t, cols["yw"], te))
        fw = round(alutb.interp(t, cols["fw"], te))
        got = (y, fw >> 3 & 1, fw >> 2 & 1, fw >> 1 & 1, fw & 1)
        exp = flags_of(a, b, s)
        good += got == exp
        print("  %3d  %-4s %3d %3d | %2d   %d %d %d %d |          %2d  %d %d %d %d | %s" % (
            k, alutb.OPS[s], a, b, got[0], got[1], got[2], got[3], got[4],
            exp[0], exp[1], exp[2], exp[3], exp[4], "ok" if got == exp else "WRONG"))
    print("-" * 79)
    print("%d of %d vectors correct (c = carry out, 1 = no borrow; v overflow; z zero; n negative)" % (
        good, len(vecs) - 1))
    if plot:
        lets = [("a_operand", "v(aw)+40"), ("b_operand", "v(bw)+20"), ("operation", "v(sw)"),
                ("result_y", "v(yw)+20"), ("flags_cvzn", "v(fw)")]
        open_plots(raw, lets, [
            ("ALU %s inputs: a (+40), b (+20), operation s (0 ADD ... 7 NOT)" % design,
             ["a_operand", "b_operand", "operation"]),
            ("ALU %s outputs: result y (+20), flags 8c+4v+2z+n" % design, ["result_y", "flags_cvzn"])])


def alu_delay(design, plot):
    cols, raw, dt = alu_raw(design, "delay")
    deck = open(os.path.join(PKG, "tb_alu4_%s_delay.cir" % design)).read()
    t = cols["time"]
    period = 5e-9
    i0, i1 = alutb.bisect.bisect_left(t, period), len(t)
    drv = sorted(k[2:] for k in cols if k.startswith("d_"))
    tin = {p: alutb.first_cross(t, cols["d_" + p], i0, i1, HALF) for p in drv}
    tin = {p: v for p, v in tin.items() if v is not None}
    outs = alutb.out_pins(W)
    tout = {o: alutb.last_cross(t, cols[o], i0, i1, HALF) for o in outs}
    ref = max(tin.values())
    head = [ln[2:] for ln in deck.splitlines()[4:6]]
    print("simulated in %.1f s" % dt)
    print("-" * 79)
    print("  " + head[0].strip())
    print("  " + head[1].strip())
    print("  changed inputs: %s" % " ".join(drv))
    print("  output  last 50 % crossing after the latest input (ps)")
    for o in outs:
        print("  %-6s  %s" % (o, "%.1f" % ((tout[o] - ref) * 1e12) if tout[o] is not None else "no change"))
    last = max((o for o in outs if tout[o] is not None), key=lambda o: tout[o])
    print("-" * 79)
    print("worst delay %.1f ps, last output %s (delay from the input of the inverter driving the input)"
          % ((tout[last] - ref) * 1e12, last))
    if plot:
        n = len(drv) + len(outs)
        lets, names = [], []
        for i, p in enumerate(drv + outs):
            nm = ("in_" + p) if p in drv else ("out_" + p)
            node = ("d_" + p) if p in drv else p
            lets.append((nm, "v(%s)+%d" % (node, 2 * (n - 1 - i))))
            names.append(nm)
        open_plots(raw, lets, [("ALU %s slowest transition: driver inputs (top, inverted) and outputs" % design,
                                names)])


def chip_test(name, plot):
    osu = name.startswith("osu-")
    d = name[4:] if osu else name
    step = "step2_rtl_baseline" if osu else "step5_library"
    path = os.path.join(ROOT, step, "qflow_" + d, "layout", "alu4_pex.spice")
    if not os.path.isfile(path):
        sys.exit("%s not found: run bash %s/run.sh first" % (os.path.relpath(path, ROOT), step))
    text, rep = alutb.prepare_netlist(path, "alu4", W)
    if rep["errors"]:
        sys.exit("netlist problem: %s" % "; ".join(rep["errors"]))
    os.makedirs(OUT, exist_ok=True)
    dut = os.path.join(OUT, "chip_%s_dut.sp" % name)
    with open(dut, "w") as f:
        f.write(text)
    pairs = [(5, 3), (3, 12), (15, 1), (8, 8)]
    vecs = [(0, 0, 0)] + [(a, b, s) for s in range(8) for a, b in pairs]
    period = 5e-9
    deck = os.path.join(OUT, "chip_%s_test.sp" % name)
    alutb.write_tran_tb(deck, dut, vecs, W, VDD, 27.0, period)
    print("=" * 79)
    print("routed 4-bit ALU '%s' (%s/qflow_%s), netlist extracted from the layout by Magic:" % (name, step, d))
    print("  %d transistors, %d parasitic capacitors (%.0f fF in total)" % (
        rep["transistors"], rep["capacitors"], rep["cap_total_fF"]))
    print("Ngspice transient, 1.8 V, 27 C, %d vectors of 5 ns" % (len(vecs) - 1))
    sys.stdout.flush()
    raw = os.path.join(OUT, "chip_%s_test.raw" % name)
    dt = ngspice_batch(deck, raw, OUT)
    cols = alutb.read_raw(raw)
    t = cols["time"]
    outs = alutb.out_pins(W)
    print("simulated in %.1f s" % dt)
    print("-" * 79)
    print("  vec  op     a   b |  y   c v z n | expected y  c v z n | check")
    good = 0
    for k in range(1, len(vecs)):
        a, b, s = vecs[k]
        te = (k + 1) * period - 0.05 * period
        bit = {o: int(alutb.interp(t, cols[o], te) > HALF) for o in outs}
        y = sum(bit["y_%d" % i] << i for i in range(W))
        got = (y, bit["c"], bit["v"], bit["z"], bit["n"])
        exp = flags_of(a, b, s)
        good += got == exp
        print("  %3d  %-4s %3d %3d | %2d   %d %d %d %d |          %2d  %d %d %d %d | %s" % (
            k, alutb.OPS[s], a, b, got[0], got[1], got[2], got[3], got[4],
            exp[0], exp[1], exp[2], exp[3], exp[4], "ok" if got == exp else "WRONG"))
    print("-" * 79)
    print("%d of %d vectors correct after layout (c = carry out, 1 = no borrow; v overflow; z zero;"
          " n negative)" % (good, len(vecs) - 1))
    if plot:
        word = lambda p: "(%s)/%g" % ("+".join("%d*v(%s_%d)" % (1 << i, p, i) for i in range(W)), VDD)
        lets = [("a_operand", word("a") + "+40"), ("b_operand", word("b") + "+20"),
                ("operation", "(v(s_0)+2*v(s_1)+4*v(s_2))/%g" % VDD),
                ("result_y", word("y") + "+20"),
                ("flags_cvzn", "(8*v(c)+4*v(v)+2*v(z)+v(n))/%g" % VDD)]
        open_plots(raw, lets, [
            ("routed ALU %s inputs: a (+40), b (+20), operation s (0 ADD ... 7 NOT)" % name,
             ["a_operand", "b_operand", "operation"]),
            ("routed ALU %s outputs: result y (+20), flags 8c+4v+2z+n" % name, ["result_y", "flags_cvzn"])])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("view", choices=["cell", "alu-test", "alu-delay", "chip-test"])
    ap.add_argument("name", nargs="?", default=None)
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()
    plot = not args.no_plot
    if args.view == "cell":
        which = (args.name or "fb4").lower().replace("pl_", "")
        if which not in ("fb4", "cs"):
            sys.exit("cell views: fb4, cs")
        cell_demo(which, plot)
    elif args.view == "chip-test":
        chip_test(args.name or "fb", plot)
    else:
        design = args.name or "fb"
        if design not in DESIGNS:
            sys.exit("designs: %s" % " ".join(DESIGNS))
        (alu_test if args.view == "alu-test" else alu_delay)(design, plot)


if __name__ == "__main__":
    main()
