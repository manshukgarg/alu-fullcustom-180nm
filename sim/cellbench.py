#!/usr/bin/env python3
"""Cell characterization from the waveforms (Ngspice raw file), for cells with many inputs.

Same test conditions and definitions as step3_cells/run_cells.py: every input is driven
through two X1 inverters, every output is loaded with four X1 inverters, the delay of
an output change runs from the input of the last driver inverter (also reported from
the cell input), power includes the input drivers, and PDP = average power x worst delay.

run_cells.py measures with one .meas line per event, which stops scaling beyond three or
four inputs; here the waveforms are saved and evaluated in Python. Two input sequences:
  all      every ordered pair of input states once (as run_cells.py)
  single   every change of one input in every state of the other inputs, both directions
           (n * 2^n transitions; used for the ALU-specific cells with 4 and 6 inputs)
"""
import bisect
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "step3_cells"))

import alutb  # noqa: E402
import cellnet  # noqa: E402

MODELS = os.path.join(ROOT, "models", "tsmc018_t14b.lib")
EDGE = 50e-12
FANOUT = 4


def all_pairs(nbits):
    """States in which every ordered pair (u -> v, u != v) occurs once (as run_cells.py)."""
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


def single_changes(nbits):
    """States in which every single-input change (u -> u xor 2^i) occurs once: an Eulerian
    circuit of the directed hypercube."""
    remaining = {u: [u ^ (1 << i) for i in range(nbits)] for u in range(1 << nbits)}
    stack, path = [0], []
    while stack:
        u = stack[-1]
        if remaining[u]:
            stack.append(remaining[u].pop())
        else:
            path.append(stack.pop())
    return path[::-1]


def bits(state, names):
    n = len(names)
    return {nm: (state >> (n - 1 - i)) & 1 for i, nm in enumerate(names)}


def build_tb(cell, vdd, period, states, dut_text=None):
    vecs = [bits(s, cell.inputs) for s in states]
    tstop = len(vecs) * period
    L = ["* testbench for %s at %.2f V (waveform evaluation)" % (cell.name, vdd),
         ".include %s" % MODELS, cellnet.inv_x1().spice(),
         dut_text if dut_text is not None else cell.spice(),
         "Vcut vcut 0 %g" % vdd, "Vdrv vdrv 0 %g" % vdd, "Vld  vld  0 %g" % vdd]
    for nm in cell.inputs:
        pts = ["0 %g" % (vdd * vecs[0][nm])]
        for k in range(1, len(vecs)):
            if vecs[k][nm] != vecs[k - 1][nm]:
                t = k * period
                pts.append("%.9g %g" % (t, vdd * vecs[k - 1][nm]))
                pts.append("%.9g %g" % (t + EDGE, vdd * vecs[k][nm]))
        L.append("Vs_%s s_%s 0 PWL(%s)" % (nm, nm, " ".join(pts)))
        L.append("Xd1_%s s_%s d_%s vdrv 0 inv_x1" % (nm, nm, nm))
        L.append("Xd2_%s d_%s %s vdrv 0 inv_x1" % (nm, nm, nm))
    L.append("Xcut %s vcut 0 %s" % (" ".join(cell.inputs + cell.outputs), cell.name))
    for out in cell.outputs:
        for j in range(FANOUT):
            L.append("Xl_%s_%d %s ld_%s_%d vld 0 inv_x1" % (out, j, out, out, j))
    saves = ["v(%s)" % p for p in cell.inputs] + ["v(d_%s)" % p for p in cell.inputs] + \
            ["v(%s)" % o for o in cell.outputs] + ["i(vcut)", "i(vdrv)"]
    L.append(".save " + " ".join(saves))
    L.append(".tran 1p %.9g 0 10p" % tstop)
    L.append(".end")
    return "\n".join(L) + "\n", vecs, tstop


def directed_cross(t, y, i0, i1, lev, rising):
    """First crossing of lev in the given direction between sample indices i0 and i1."""
    for i in range(max(i0, 1), i1):
        a, b = y[i - 1] - lev, y[i] - lev
        if (a < 0 <= b) if rising else (a > 0 >= b):
            return t[i - 1] + (t[i] - t[i - 1]) * (-a) / (b - a) if b != a else t[i]
    return None


def sequence_states(cell, sequence):
    return single_changes(len(cell.inputs)) if sequence == "single" else all_pairs(len(cell.inputs))


def evaluate(cell, vdd, period, workdir, k=1.0, r=2.0, sequence="single", dut_text=None, tag="",
             detail=False):
    """Simulate one cell and return its figures of merit (keys as run_cells.evaluate).

    detail: also return the list "events", one entry per output change: vector index,
    the changed input whose driver input crosses last (the delay reference) and its
    direction at the driver input, the output and its direction, the delay."""
    states = sequence_states(cell, sequence)
    tb, vecs, tstop = build_tb(cell, vdd, period, states, dut_text)
    base = "wb_%s%s_%dmV_k%g_r%g" % (cell.name, tag, round(vdd * 1000), k, r)
    path, raw = os.path.join(workdir, base + ".sp"), os.path.join(workdir, base + ".raw")
    with open(path, "w") as f:
        f.write(tb)
    if os.path.exists(raw):
        os.remove(raw)
    res = subprocess.run(["ngspice", "-b", "-r", base + ".raw", base + ".sp"], capture_output=True,
                         text=True, cwd=workdir, timeout=3600)
    with open(os.path.join(workdir, base + ".log"), "w") as f:
        f.write(res.stdout + res.stderr)
    nan = float("nan")
    out = {"cell": cell.name, "family": cell.family, "note": cell.note, "transistors": cell.count,
           "vdd": vdd, "k": k, "r": r, "sequence": sequence, "transitions": len(vecs) - 1,
           "width_um": round(sum(d[5] for d in cell.devs), 2)}
    if not os.path.isfile(raw):
        out.update({"t_max_ps": nan, "pdp_fJ": nan, "wrong_levels": len(vecs), "weak_levels": 0,
                    "missing_delays": len(vecs), "error": "no raw file"})
        return out
    cols = alutb.read_raw(raw)
    os.remove(raw)
    t = cols["time"]
    half = vdd / 2
    d_in, d_drv, missing, wrong, weak = [], [], 0, 0, 0
    events = []
    vmin_hi, vmax_lo = vdd, 0.0
    worst = None
    for kk in range(len(vecs)):
        tk, te = kk * period, min((kk + 1) * period, tstop)
        i0, i1 = bisect.bisect_left(t, tk), bisect.bisect_left(t, te)
        cur_o = cell.func(vecs[kk])
        for o in cell.outputs:                                   # settled level
            lv = alutb.interp(t, cols[o.lower()], te - 0.05 * period)
            if (lv > half) != bool(cur_o[o]):
                wrong += 1
            elif cur_o[o]:
                vmin_hi = min(vmin_hi, lv)
                weak += lv < 0.9 * vdd
            else:
                vmax_lo = max(vmax_lo, lv)
                weak += lv > 0.1 * vdd
        if kk == 0:
            continue
        prev_o = cell.func(vecs[kk - 1])
        ins = [(nm, vecs[kk][nm]) for nm in cell.inputs if vecs[kk][nm] != vecs[kk - 1][nm]]
        outs = [(o, cur_o[o]) for o in cell.outputs if cur_o[o] != prev_o[o]]
        tin = [directed_cross(t, cols[nm.lower()], i0, i1, half, bool(v)) for nm, v in ins]
        tq = [directed_cross(t, cols["d_" + nm.lower()], i0, i1, half, not v) for nm, v in ins]
        if None in tin or None in tq:
            missing += len(outs)
            continue
        for o, v in outs:
            to = directed_cross(t, cols[o.lower()], i0, i1, half, bool(v))
            if to is None:
                missing += 1
                continue
            d_in.append(to - max(tin))
            d_drv.append(to - max(tq))
            ref = max(range(len(tq)), key=lambda j: tq[j])
            events.append({"k": kk, "pin": ins[ref][0], "pin_dir": "fall" if ins[ref][1] else "rise",
                           "out": o, "out_dir": "rise" if v else "fall",
                           "delay_ps": round(d_drv[-1] * 1e12, 2)})
            if worst is None or d_drv[-1] > worst[0]:
                worst = (d_drv[-1], "%s -> %s, output %s" % (
                    "".join(str(vecs[kk - 1][n]) for n in cell.inputs),
                    "".join(str(vecs[kk][n]) for n in cell.inputs), o))
    twin = tstop - period
    p_cut = -alutb.integrate(t, cols["i(vcut)"], period, tstop) * vdd / twin
    p_drv = -alutb.integrate(t, cols["i(vdrv)"], period, tstop) * vdd / twin
    tmax = max(d_drv) if d_drv else nan
    p_tot = p_cut + p_drv
    out.update({
        "t_max_ps": tmax * 1e12, "t_avg_ps": (sum(d_drv) / len(d_drv) if d_drv else nan) * 1e12,
        "t_in_max_ps": (max(d_in) if d_in else nan) * 1e12,
        "p_cell_uW": p_cut * 1e6, "p_total_uW": p_tot * 1e6, "pdp_fJ": p_tot * tmax * 1e15,
        "edp_fJps": p_tot * tmax * tmax * 1e27, "vout_hi_min": vmin_hi, "vout_lo_max": vmax_lo,
        "wrong_levels": wrong, "weak_levels": weak, "missing_delays": missing,
        "worst": worst[1] if worst else "", "inputs_order": "".join(cell.inputs),
    })
    if detail:
        out["events"] = events
        out["states"] = states
    return out
