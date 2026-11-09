#!/usr/bin/env python3
"""Cell-level comparison of candidate circuit styles (Ngspice, 180 nm).

For every candidate cell:
  * inputs are driven through two X1 inverters from ideal sources (realistic edges),
  * every output drives four X1 inverters (fan-out of four),
  * the input sequence is an Eulerian circuit over all input states, so every
    possible input transition occurs exactly once (12 for two inputs, 56 for three),
  * two delays are measured for each transition, to the output 50 % crossing:
      - from the cell input (latest 50 % crossing of the inputs that changed), and
      - from the input of the last driver inverter, which adds the driver delay and
        so includes the cost of the cell's input loading (pass-transistor inputs
        that drive the output load through the cell are not hidden);
    the worst case over all transitions is reported and the second one is used
    for PDP and EDP,
  * energy is integrated separately for the cell supply and the input drivers;
    power includes the drivers,
  * the settled output level is sampled before every input change to check
    logic correctness and full voltage swing.

Usage:  python3 run_cells.py [--vdd 1.8] [--period 2e-9] [--only name,name] [--k 1] [--r 2]
        python3 run_cells.py --sweep            (size every candidate on the k x r grid)
        python3 run_cells.py --report           (reprint the sweep summary from out/)
Writes out/*.csv and prints a table.
"""
import argparse
import csv
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


def build_tb(cell, vdd, period, dut_text=None):
    """Testbench text plus the bookkeeping needed to evaluate it.

    dut_text replaces the cell's own subcircuit (used for extracted layouts);
    it must define a subcircuit with the same name and pin order.
    """
    states = euler_states(len(cell.inputs))
    vecs = [bits(s, cell.inputs) for s in states]
    tstop = len(vecs) * period
    lines = ["* testbench for %s at %.2f V" % (cell.name, vdd),
             ".include %s" % MODELS,
             cellnet.inv_x1().spice(),
             dut_text if dut_text is not None else cell.spice(),
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
    meta = []           # (vector index, changed inputs with direction, changed outputs with direction)
    for k in range(1, len(vecs)):
        t = k * period
        prev_o, cur_o = cell.func(vecs[k - 1]), cell.func(vecs[k])
        ins = [(nm, "rise" if vecs[k][nm] else "fall")
               for nm in cell.inputs if vecs[k][nm] != vecs[k - 1][nm]]
        outs = [(o, "rise" if cur_o[o] else "fall")
                for o in cell.outputs if cur_o[o] != prev_o[o]]
        for nm, d in ins:
            lines.append(".meas tran ti_%d_%s when v(%s)=%g td=%.6g %s=1" % (k, nm, nm, half, t, d))
            # the driver input moves the opposite way
            dd = "fall" if d == "rise" else "rise"
            lines.append(".meas tran tq_%d_%s when v(d_%s)=%g td=%.6g %s=1" % (k, nm, nm, half, t, dd))
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


def evaluate(cell, vdd, period, workdir, k=1.0, r=2.0, dut_text=None, tag=""):
    """Simulate one cell and return its figures of merit as a dict."""
    tb, meta, levels, twin = build_tb(cell, vdd, period, dut_text)
    path = os.path.join(workdir, "tb_%s%s_%dmV_k%g_r%g.sp"
                        % (cell.name, tag, round(vdd * 1000), k, r))
    with open(path, "w") as f:
        f.write(tb)
    res = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                         cwd=workdir, timeout=1800)
    log = res.stdout + res.stderr
    with open(path.replace(".sp", ".log"), "w") as f:
        f.write(log)
    v = parse_meas(log)

    d_in, d_drv, missing = [], [], 0
    for idx, ins, outs in meta:
        tin = [v.get("ti_%d_%s" % (idx, nm.lower())) for nm, _ in ins]
        tq = [v.get("tq_%d_%s" % (idx, nm.lower())) for nm, _ in ins]
        if None in tin or None in tq:
            missing += len(outs)
            continue
        for o, _ in outs:
            to = v.get("to_%d_%s" % (idx, o.lower()))
            if to is None:
                missing += 1
            else:
                d_in.append(to - max(tin))
                d_drv.append(to - max(tq))
    wrong, weak, vmin_hi, vmax_lo = 0, 0, vdd, 0.0
    for idx, o, expect in levels:
        lv = v.get("lv_%d_%s" % (idx, o.lower()))
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
    nan = float("nan")
    ecut, edrv = v.get("ecut"), v.get("edrv")
    p_cut = -ecut * vdd / twin if ecut is not None else nan
    p_drv = -edrv * vdd / twin if edrv is not None else nan
    tmax = max(d_drv) if d_drv else nan
    tavg = sum(d_drv) / len(d_drv) if d_drv else nan
    tmax_in = max(d_in) if d_in else nan
    p_tot = p_cut + p_drv
    return {
        "cell": cell.name, "family": cell.family, "note": cell.note,
        "transistors": cell.count, "vdd": vdd, "k": k, "r": r,
        "t_max_ps": tmax * 1e12, "t_avg_ps": tavg * 1e12, "t_in_max_ps": tmax_in * 1e12,
        "p_cell_uW": p_cut * 1e6, "p_total_uW": p_tot * 1e6,
        "pdp_fJ": p_tot * tmax * 1e15,
        "edp_fJps": p_tot * tmax * tmax * 1e27,
        "width_um": round(sum(d[5] for d in cell.devs), 2),
        "vout_hi_min": vmin_hi, "vout_lo_max": vmax_lo,
        "wrong_levels": wrong, "weak_levels": weak, "missing_delays": missing,
        "transitions": len(meta),
    }


# candidates whose output is not restored by an inverter or a static gate: kept out of the
# library for automatic place and route (step5_library), allowed in the full-custom slice
UNBUFFERED = {"xor_tg8", "mux_tg6", "fa_tga20"}
NO_LAYOUT_PLAN = {"xor_cpl14", "muxi_npt7"}      # layout/library.py has no column plan yet
CONVENTIONAL = {"INV": "inv_cmos", "NAND2": "nand2_cmos", "NOR2": "nor2_cmos",
                "XOR2": "xor_cmos12", "MUX2": "mux_cmos12", "MUX2I": "muxi_cmos10",
                "FA": "fa_cmos28"}
K_LIST = [0.3, 0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0]
R_LIST = [1.0, 1.5, 2.0, 2.5, 3.0]
NUMERIC = ("transistors", "vdd", "k", "r", "t_max_ps", "t_avg_ps", "t_in_max_ps", "p_cell_uW",
           "p_total_uW", "pdp_fJ", "edp_fJps", "width_um", "vout_hi_min", "vout_lo_max",
           "wrong_levels", "weak_levels", "missing_delays", "transitions")


def _job(job):
    name, k, r, vdd, period, workdir = job
    fn = getattr(cellnet, name)
    return evaluate(fn(k, r), vdd, period, workdir, k, r)


def good(row):
    return row["wrong_levels"] == 0 and row["missing_delays"] == 0 and row["weak_levels"] == 0 \
        and row["pdp_fJ"] == row["pdp_fJ"]


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            for key in NUMERIC:
                if key in row:
                    row[key] = float(row[key])
            rows.append(row)
    return rows


def summarize(rows, names, vdd, workdir):
    """Print the per-family table and write out/selected.csv."""
    print()
    print("Best size of every candidate: minimum PDP, full swing, every transition correct")
    print("%.2f V, 27 C, FO4 load; delay includes the input driver; %d k x %d r sizes"
          % (vdd, len({r["k"] for r in rows}), len({r["r"] for r in rows})))
    hdr = "  %-12s %3s %5s %4s %7s %8s %7s %7s %6s" % (
        "cell", "T", "k", "r", "tmax", "Ptot", "PDP", "EDP", "W")
    print(hdr + "   (ps, uW, fJ, fJ*ns, um)")
    families = []
    for n in names:
        fam = getattr(cellnet, n)().family
        if fam not in families:
            families.append(fam)
    selected = []
    for fam in families:
        conv = [r for r in rows if r["cell"] == CONVENTIONAL.get(fam)
                and r["k"] == 1.0 and r["r"] == 2.0]
        c = conv[0] if conv else None
        head = "%-6s" % fam
        if c:
            head += " conventional %s k 1 r 2: tmax %.1f ps, PDP %.2f fJ" % (
                c["cell"], c["t_max_ps"], c["pdp_fJ"])
        print("-" * len(hdr))
        print(head)
        best_fam = None
        lines = []
        for n in names:
            cand = [r for r in rows if r["cell"] == n and r["family"] == fam and good(r)]
            if not cand:
                if any(r["cell"] == n and r["family"] == fam for r in rows):
                    lines.append((n, "  %-12s no size passes all checks" % n))
                continue
            b = min(cand, key=lambda r: r["pdp_fJ"])
            lines.append((n, "  %-12s %3d %5g %4g %7.1f %8.2f %7.2f %7.1f %6.1f" % (
                b["cell"], b["transistors"], b["k"], b["r"], b["t_max_ps"], b["p_total_uW"],
                b["pdp_fJ"], b["edp_fJps"] / 1000.0, b["width_um"])))
            if best_fam is None or b["pdp_fJ"] < best_fam["pdp_fJ"]:
                best_fam = b
        for n, text in lines:
            if best_fam and n == best_fam["cell"]:
                if c:
                    text += "  <= PDP %+.0f %%" % (100 * (best_fam["pdp_fJ"] / c["pdp_fJ"] - 1))
                else:
                    text += "  <="
            print(text)
        if best_fam:
            row = dict(best_fam)
            if c:
                row["conv_t_max_ps"] = c["t_max_ps"]
                row["conv_pdp_fJ"] = c["pdp_fJ"]
            selected.append(row)
    print("-" * len(hdr))
    print("<= selected for the optimized library (PDP change against the conventional cell)")
    # library for automatic place and route: best restoring candidate of every function
    auto = []
    for fam in families:
        best = None
        for n in names:
            if n in UNBUFFERED or n in NO_LAYOUT_PLAN:
                continue
            cand = [r for r in rows if r["cell"] == n and r["family"] == fam and good(r)]
            if cand:
                b = min(cand, key=lambda r: r["pdp_fJ"])
                if best is None or b["pdp_fJ"] < best["pdp_fJ"]:
                    best = b
        if best:
            auto.append(best)
    if auto:
        print("Automated-flow library (restoring outputs, cells with a layout plan):")
        for r in auto:
            print("  %-6s %-12s k %-5g r %-4g tmax %6.1f ps  PDP %6.2f fJ"
                  % (r["family"], r["cell"], r["k"], r["r"], r["t_max_ps"], r["pdp_fJ"]))
        with open(os.path.join(workdir, "selected_auto.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(auto[0].keys()))
            w.writeheader()
            w.writerows(auto)
    if selected:
        keys = []
        for row in selected:
            for key in row:
                if key not in keys:
                    keys.append(key)
        with open(os.path.join(workdir, "selected.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(selected)
    return selected


def sweep(args, workdir):
    import multiprocessing as mp
    names = [fn.__name__ for fn in cellnet.CANDIDATES]
    if args.only:
        names = [n for n in names if n in args.only.split(",")]
    jobs = [(n, k, r, args.vdd, args.period, workdir) for n in names for k in K_LIST for r in R_LIST]
    workers = max(1, min(8, os.cpu_count() or 2))
    print("sizing sweep: %d candidates x %d sizes = %d simulations on %d cores"
          % (len(names), len(K_LIST) * len(R_LIST), len(jobs), workers), flush=True)
    rows = []
    step = max(1, len(jobs) // 16)
    with mp.Pool(workers) as pool:
        for i, row in enumerate(pool.imap_unordered(_job, jobs), 1):
            rows.append(row)
            if i % step == 0 or i == len(jobs):
                print("  %d / %d done" % (i, len(jobs)), flush=True)
    rows.sort(key=lambda r: (names.index(r["cell"]), r["k"], r["r"]))
    write_csv(os.path.join(workdir, "sweep_%dmV.csv" % round(args.vdd * 1000)), rows)
    summarize(rows, names, args.vdd, workdir)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vdd", type=float, default=1.8)
    ap.add_argument("--period", type=float, default=2e-9)
    ap.add_argument("--only", default="")
    ap.add_argument("--k", type=float, default=1.0, help="width scale factor")
    ap.add_argument("--r", type=float, default=2.0, help="P/N width ratio")
    ap.add_argument("--tag", default="")
    ap.add_argument("--sweep", action="store_true", help="size every candidate (k x r grid)")
    ap.add_argument("--report", action="store_true", help="reprint the sweep summary from out/")
    args = ap.parse_args()

    workdir = os.path.join(HERE, "out")
    os.makedirs(workdir, exist_ok=True)
    if args.report:
        rows = read_csv(os.path.join(workdir, "sweep_%dmV.csv" % round(args.vdd * 1000)))
        names = [fn.__name__ for fn in cellnet.CANDIDATES if fn.__name__ in {r["cell"] for r in rows}]
        summarize(rows, names, args.vdd, workdir)
        return
    if args.sweep:
        sweep(args, workdir)
        return
    only = [s for s in args.only.split(",") if s]
    rows = []
    for fn in cellnet.CANDIDATES:
        cell = fn(args.k, args.r)
        if only and cell.name not in only:
            continue
        print("  simulating %-12s (%2d transistors) ..." % (cell.name, cell.count), flush=True)
        rows.append(evaluate(cell, args.vdd, args.period, workdir, args.k, args.r))

    tag = args.tag or "cells_%dmV_k%g_r%g" % (round(args.vdd * 1000), args.k, args.r)
    write_csv(os.path.join(workdir, tag + ".csv"), rows)

    print()
    print("Cell comparison at %.2f V, 27 C, FO4 load, width scale k = %g, P/N ratio r = %g"
          % (args.vdd, args.k, args.r))
    print("tmax: worst delay including the input driver; tin: worst delay from the cell input")
    hdr = "%-12s %3s %8s %8s %9s %9s %7s  %s" % ("cell", "T", "tmax(ps)", "tin(ps)",
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
        print("%-12s %3d %8.1f %8.1f %9.2f %9.2f %7s  %s" % (
            r["cell"], r["transistors"], r["t_max_ps"], r["t_in_max_ps"], r["p_total_uW"],
            r["pdp_fJ"], swing, ok))


if __name__ == "__main__":
    main()
