#!/usr/bin/env python3
"""Cell-level comparison of candidate circuit styles (Ngspice, 180 nm).

For every candidate cell:
  * inputs are driven through two X1 inverters from ideal sources (realistic edges),
  * every output drives four X1 inverters (fan-out of four),
  * the input sequence is an Eulerian circuit over all input states, so every
    possible input transition occurs exactly once (12 for two inputs, 56 for three),
  * delay of each transition = output 50 % crossing minus the latest 50 % crossing
    of the inputs that changed; the worst case over all transitions is reported,
  * energy is integrated separately for the cell supply and the input drivers;
    power includes the drivers so that heavily loaded inputs are not hidden,
  * the settled output level is sampled before every input change to check
    logic correctness and full voltage swing.

Usage:  python3 run_cells.py [--vdd 1.8] [--period 2e-9] [--only name,name]
Writes out/<run>.csv and prints a table.
"""
import argparse
import csv
import itertools
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cellnet  # noqa: E402

MODELS = os.path.join(HERE, "..", "models", "tsmc018_t14b.lib")
EDGE = 50e-12          # ideal source rise/fall time
FANOUT = 4


def euler_states(nbits):
    """Sequence of input states in which every ordered pair (u -> v, u != v) occurs once."""
    n = 1 << nbits
    remaining = {u: [v for v in range(n) if v != u] for u in range(n)}
    stack, path = [0], []
    while stack:
        u = stack[-1]
        if remaining[u]:
            stack.append(remaining[u].pop())
        else:
            path.append(stack.pop())
    return path[::-1]


def bits(state, names):
    """State integer -> {name: bit}; the first name is the most significant bit."""
    n = len(names)
    return {nm: (state >> (n - 1 - i)) & 1 for i, nm in enumerate(names)}


def build_tb(cell, vdd, period):
    states = euler_states(len(cell.inputs))
    vecs = [bits(s, cell.inputs) for s in states]
    tstop = len(vecs) * period
    lines = ["* testbench for %s at %.2f V" % (cell.name, vdd),
             ".include %s" % MODELS,
             cellnet.inv_x1().spice(),
             cell.spice(),
             "Vcut vcut 0 %g" % vdd,
             "Vdrv vdrv 0 %g" % vdd,
             "Vld  vld  0 %g" % vdd]
    # ideal sources -> two X1 inverters -> cell input
    for nm in cell.inputs:
        pts = ["0 %g" % (vdd * vecs[0][nm])]
        for k in range(1, len(vecs)):
            if vecs[k][nm] != vecs[k - 1][nm]:
                t = k * period
                pts.append("%.6g %g" % (t, vdd * vecs[k - 1][nm]))
                pts.append("%.6g %g" % (t + EDGE, vdd * vecs[k][nm]))
        lines.append("Vs_%s s_%s 0 PWL(%s)" % (nm, nm, " ".join(pts)))
        lines.append("Xd1_%s s_%s d_%s vdrv 0 inv_x1" % (nm, nm, nm))
        lines.append("Xd2_%s d_%s %s vdrv 0 inv_x1" % (nm, nm, nm))
    pins = " ".join(cell.inputs + cell.outputs)
    lines.append("Xcut %s vcut 0 %s" % (pins, cell.name))
    for out in cell.outputs:
        for j in range(FANOUT):
            lines.append("Xl_%s_%d %s ld_%s_%d vld 0 inv_x1" % (out, j, out, out, j))
    lines.append(".tran 1p %.6g" % tstop)

    half = vdd / 2
    meta = []           # (k, changed inputs with direction, changed outputs with direction)
    for k in range(1, len(vecs)):
        t = k * period
        prev_o, cur_o = cell.func(vecs[k - 1]), cell.func(vecs[k])
        ins = [(nm, "rise" if vecs[k][nm] else "fall")
               for nm in cell.inputs if vecs[k][nm] != vecs[k - 1][nm]]
        outs = [(o, "rise" if cur_o[o] else "fall")
                for o in cell.outputs if cur_o[o] != prev_o[o]]
        for nm, d in ins:
            lines.append(".meas tran ti_%d_%s when v(%s)=%g td=%.6g %s=1" % (k, nm, nm, half, t, d))
        for o, d in outs:
            lines.append(".meas tran to_%d_%s when v(%s)=%g td=%.6g %s=1" % (k, o, o, half, t, d))
        meta.append((k, ins, outs))
    # settled output levels just before every change (and at the end)
    levels = []
    for k in range(len(vecs)):
        ts = (k + 1) * period - 0.05 * period
        for o in cell.outputs:
            lines.append(".meas tran lv_%d_%s find v(%s) at=%.6g" % (k, o, o, ts))
            levels.append((k, o, cell.func(vecs[k])[o]))
    t0 = period
    lines.append(".meas tran ecut integ i(Vcut) from=%.6g to=%.6g" % (t0, tstop))
    lines.append(".meas tran edrv integ i(Vdrv) from=%.6g to=%.6g" % (t0, tstop))
    lines.append(".end")
    return "\n".join(lines) + "\n", meta, levels, tstop - t0


MEAS_RE = re.compile(r"^\s*(\w+)\s*=\s*([-+]?[0-9.]+(?:[eE][-+]?[0-9]+)?)")


def parse_meas(text):
    vals = {}
    for line in text.splitlines():
        m = MEAS_RE.match(line)
        if m:
            vals[m.group(1).lower()] = float(m.group(2))
    return vals


def evaluate(cell, vdd, period, workdir):
    tb, meta, levels, twin = build_tb(cell, vdd, period)
    path = os.path.join(workdir, "tb_%s_%dmV.sp" % (cell.name, round(vdd * 1000)))
    with open(path, "w") as f:
        f.write(tb)
    res = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                         cwd=workdir, timeout=900)
    log = res.stdout + res.stderr
    with open(path.replace(".sp", ".log"), "w") as f:
        f.write(log)
    v = parse_meas(log)

    delays, missing = [], 0
    for k, ins, outs in meta:
        tin = [v.get("ti_%d_%s" % (k, nm.lower())) for nm, _ in ins]
        if None in tin:
            missing += len(outs)
            continue
        for o, _ in outs:
            to = v.get("to_%d_%s" % (k, o.lower()))
            if to is None:
                missing += 1
            else:
                delays.append(to - max(tin))
    wrong, weak, vmin_hi, vmax_lo = 0, 0, vdd, 0.0
    for k, o, expect in levels:
        lv = v.get("lv_%d_%s" % (k, o.lower()))
        if lv is None:
            wrong += 1
            continue
        if (lv > vdd / 2) != bool(expect):
            wrong += 1
        elif expect:
            vmin_hi = min(vmin_hi, lv)
            weak += lv < 0.9 * vdd
        else:
            vmax_lo = max(vmax_lo, lv)
            weak += lv > 0.1 * vdd
    ecut, edrv = v.get("ecut"), v.get("edrv")
    p_cut = -ecut * vdd / twin if ecut is not None else float("nan")
    p_drv = -edrv * vdd / twin if edrv is not None else float("nan")
    tmax = max(delays) if delays else float("nan")
    tavg = sum(delays) / len(delays) if delays else float("nan")
    p_tot = p_cut + p_drv
    return {
        "cell": cell.name, "family": cell.family, "note": cell.note,
        "transistors": cell.count, "vdd": vdd,
        "t_max_ps": tmax * 1e12, "t_avg_ps": tavg * 1e12,
        "p_cell_uW": p_cut * 1e6, "p_total_uW": p_tot * 1e6,
        "pdp_fJ": p_tot * tmax * 1e15,
        "vout_hi_min": vmin_hi, "vout_lo_max": vmax_lo,
        "wrong_levels": wrong, "weak_levels": weak, "missing_delays": missing,
        "transitions": len(meta),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vdd", type=float, default=1.8)
    ap.add_argument("--period", type=float, default=2e-9)
    ap.add_argument("--only", default="")
    ap.add_argument("--k", type=float, default=1.0, help="width scale factor")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    workdir = os.path.join(HERE, "out")
    os.makedirs(workdir, exist_ok=True)
    only = [s for s in args.only.split(",") if s]
    rows = []
    for fn in cellnet.CANDIDATES:
        cell = fn(args.k)
        if only and cell.name not in only:
            continue
        print("  simulating %-12s (%2d transistors) ..." % (cell.name, cell.count), flush=True)
        rows.append(evaluate(cell, args.vdd, args.period, workdir))

    tag = args.tag or "cells_%dmV_k%g" % (round(args.vdd * 1000), args.k)
    with open(os.path.join(workdir, tag + ".csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print()
    print("Cell comparison at %.2f V, 27 C, FO4 load, width scale k = %g" % (args.vdd, args.k))
    hdr = "%-12s %3s %9s %9s %10s %9s %7s  %s" % ("cell", "T", "tmax(ps)", "tavg(ps)",
                                               "Ptot(uW)", "PDP(fJ)", "swing", "check")
    print(hdr)
    fam = None
    for r in rows:
        if r["family"] != fam:
            fam = r["family"]
            print("-" * len(hdr))
        ok = "ok" if r["wrong_levels"] == 0 and r["missing_delays"] == 0 else \
            "FAIL(%d wrong, %d missing)" % (r["wrong_levels"], r["missing_delays"])
        swing = "full" if r["weak_levels"] == 0 else "weak%d" % r["weak_levels"]
        print("%-12s %3d %9.1f %9.1f %10.2f %9.2f %7s  %s" % (
            r["cell"], r["transistors"], r["t_max_ps"], r["t_avg_ps"], r["p_total_uW"],
            r["pdp_fJ"], swing, ok))


if __name__ == "__main__":
    main()
