#!/usr/bin/env python3
"""Step 3c: the two ALU-specific cells, sized and compared with the same function
composed of library cells (Ngspice, 180 nm).

  FB4  fb4_tg20   P = C[2A + B]: the operand bits select one of four function-code lines
  CS   cs_tg24    CO = P ? CI : A,  Y = K ? P : P xor CI

Test conditions and definitions are those of the cell sweep (run_cells.py): inputs through
two X1 inverters, FO4 loads, delay from the input of the last driver inverter, power
including the drivers, PDP = power x worst delay. The cells have six and four inputs, so
the input sequence is every change of one input in every state of the other inputs, both
directions (384 and 64 transitions), evaluated from the waveforms (sim/cellbench.py).

Each cell is simulated on the k x r grid of the sweep; the minimum-PDP size with full swing
and every transition correct is selected. References, measured in the same way:
  * the same function composed of the cells of the automated-flow library pl018
    (step5_library/library.json): FB4 from three MUX2I, CS from MUX2 + XOR2 + MUX2;
  * the same composition in conventional static CMOS at the reference size.

Usage:  python3 run_alu_cells.py             simulate and print the summary
        python3 run_alu_cells.py --report    reprint the summary from out/
        python3 run_alu_cells.py --select    also write the selected sizes to alu_cells.json
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "sim"))

import cellbench  # noqa: E402
import cellnet  # noqa: E402
from run_cells import K_LIST, R_LIST  # noqa: E402

OUT = os.path.join(HERE, "out")
SELECTION = os.path.join(HERE, "alu_cells.json")
VDD, PERIOD = 1.8, 2e-9
W = 79
NUMERIC = ("transistors", "k", "r", "t_max_ps", "t_in_max_ps", "p_total_uW", "pdp_fJ",
           "edp_fJps", "width_um", "wrong_levels", "weak_levels", "missing_delays",
           "transitions", "vout_hi_min", "vout_lo_max", "p_cell_uW", "t_avg_ps", "vdd")


def composed(name, like, parts, wiring, note):
    """A cell made of library cells: parts {subckt: Cell}, wiring [(subckt, nets)].

    Returns (Cell with the pins and function of 'like', SPICE text of the composition)."""
    c = cellnet.Cell(name, like.inputs, like.outputs, like.func, like.family, note)
    text = "".join(p.spice() for p in parts.values())
    text += ".subckt %s %s vdd gnd\n" % (name, " ".join(like.inputs + like.outputs))
    for i, (sub, nets) in enumerate(wiring):
        text += "X%d %s vdd gnd %s\n" % (i, " ".join(nets), sub)
        c.devs += parts[sub].devs
    text += ".ends %s\n" % name
    return c, text


def references():
    """[(family, label, Cell, SPICE text)]: the two functions composed of library cells."""
    lib = json.load(open(os.path.join(ROOT, "step5_library", "library.json")))["cells"]

    def pl(fam):
        e = lib[fam]
        return getattr(cellnet, e["cell"])(e["k"], e["r"])
    fb, cs = cellnet.fb4_tg20(), cellnet.cs_tg24()
    out = []
    # FB4 = MUX2I(MUX2I(C0, C1, B), MUX2I(C2, C3, B), A);  MUX2I: Y = not (S ? B : A)
    m = pl("MUX2I")
    out.append(("FB4", "3 x MUX2I of pl018") + composed(
        "fb4_pl", fb, {m.name: m},
        [(m.name, ["C0", "C1", "B", "m0"]), (m.name, ["C2", "C3", "B", "m1"]),
         (m.name, ["m0", "m1", "A", "P"])], "three inverting multiplexers of pl018"))
    m = cellnet.mux_cmos12(1.0, 2.0)
    out.append(("FB4", "3 x MUX2, static CMOS") + composed(
        "fb4_conv", fb, {m.name: m},
        [(m.name, ["C0", "C1", "B", "m0"]), (m.name, ["C2", "C3", "B", "m1"]),
         (m.name, ["m0", "m1", "A", "P"])], "three static CMOS multiplexers, k 1, r 2"))
    # CS: CO = MUX2(A, CI, P);  Y = MUX2(XOR2(P, CI), P, K);  MUX2: Y = S ? B : A
    m, x = pl("MUX2"), pl("XOR2")
    out.append(("CS", "MUX2+XOR2+MUX2 of pl018") + composed(
        "cs_pl", cs, {m.name: m, x.name: x},
        [(m.name, ["A", "CI", "P", "CO"]), (x.name, ["P", "CI", "px"]),
         (m.name, ["px", "P", "K", "Y"])], "two multiplexers and an XOR of pl018"))
    m, x = cellnet.mux_cmos12(1.0, 2.0), cellnet.xor_cmos12(1.0, 2.0)
    out.append(("CS", "MUX2+XOR2+MUX2, static") + composed(
        "cs_conv", cs, {m.name: m, x.name: x},
        [(m.name, ["A", "CI", "P", "CO"]), (x.name, ["P", "CI", "px"]),
         (m.name, ["px", "P", "K", "Y"])], "static CMOS multiplexers and XOR, k 1, r 2"))
    return out


def _job(job):
    kind, name, k, r = job
    if kind == "cell":
        row = cellbench.evaluate(getattr(cellnet, name)(k, r), VDD, PERIOD, OUT, k, r)
        row["version"] = "size"
    else:
        fam, label, cell, text = [x for x in references() if x[2].name == name][0]
        row = cellbench.evaluate(cell, VDD, PERIOD, OUT, 0, 0, dut_text=text)
        row["version"] = label
    return row


def good(row):
    return row["wrong_levels"] == 0 and row["missing_delays"] == 0 and row["weak_levels"] == 0 \
        and row["pdp_fJ"] == row["pdp_fJ"]


def simulate():
    import multiprocessing as mp
    jobs = [("ref", x[2].name, 0, 0) for x in references()]
    jobs += [("cell", fn.__name__, k, r) for fn in cellnet.ALU_CELLS for k in K_LIST for r in R_LIST]
    workers = max(1, min(8, os.cpu_count() or 2))
    print("ALU-specific cells: %d simulations on %d cores" % (len(jobs), workers), flush=True)
    rows, step = [], max(1, len(jobs) // 8)
    with mp.Pool(workers) as pool:
        for i, row in enumerate(pool.imap_unordered(_job, jobs), 1):
            rows.append(row)
            if i % step == 0 or i == len(jobs):
                print("  %d / %d done" % (i, len(jobs)), flush=True)
    rows.sort(key=lambda r: (r["family"], r["version"] != "size", r["cell"], r["k"], r["r"]))
    keys = []
    for row in rows:
        keys += [k for k in row if k not in keys]
    with open(os.path.join(OUT, "alu_cells.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    return rows


def read_rows():
    rows = []
    with open(os.path.join(OUT, "alu_cells.csv")) as f:
        for row in csv.DictReader(f):
            for key in NUMERIC:
                if row.get(key) not in (None, ""):
                    row[key] = float(row[key])
            rows.append(row)
    return rows


def summarize(rows, select):
    print("=" * W)
    print("STEP 3c SUMMARY  ALU-specific cells: function block FB4 and carry-sum cell CS")
    print("=" * W)
    print("%.2f V, 27 C, FO4 loads; every change of one input in every state of the others" % VDD)
    print("tmax (ps): worst delay incl. the input driver; Ptot (uW) incl. the drivers;")
    print("PDP (fJ) = Ptot x tmax; W (um): total transistor width")
    print("  %-26s %3s %5s %4s %7s %7s %7s %6s  %s" % (
        "version", "T", "k", "r", "tmax", "Ptot", "PDP", "W", "check"))
    chosen = {}
    titles = {"FB4": "FB4   P = C[2A + B]   (function codes C0..C3 from the operation decoder)",
              "CS": "CS    CO = P ? CI : A,   Y = K ? P : P xor CI"}

    def line(label, r, k="", mark=""):
        chk = "ok" if good(r) else "%d wrong, %d weak, %d missing" % (
            r["wrong_levels"], r["weak_levels"], r["missing_delays"])
        ks = ("%5g %4g" % (r["k"], r["r"])) if k == "" else "%5s %4s" % ("-", "-")
        print("  %-26s %3d %s %7.1f %7.2f %7.2f %6.1f  %s%s" % (
            label, r["transistors"], ks, r["t_max_ps"], r["p_total_uW"], r["pdp_fJ"],
            r["width_um"], chk, mark))
    for fam in ("FB4", "CS"):
        print("-" * W)
        print(titles[fam])
        sized = [r for r in rows if r["family"] == fam and r["version"] == "size"]
        refs = [r for r in rows if r["family"] == fam and r["version"] != "size"]
        if not sized:
            print("  no result")
            continue
        name = sized[0]["cell"]
        ref_size = [r for r in sized if r["k"] == 1.0 and r["r"] == 2.0]
        if ref_size:
            line("%s, reference size" % name, ref_size[0])
        ok = [r for r in sized if good(r)]
        best = min(ok, key=lambda r: r["pdp_fJ"]) if ok else None
        if best:
            line("%s, minimum PDP" % name, best, mark="  <=")
            fast = min(ok, key=lambda r: r["t_max_ps"])
            line("%s, fastest" % name, fast)
            chosen[fam] = {"cell": name, "k": best["k"], "r": best["r"],
                           "t_max_ps": round(best["t_max_ps"], 1), "pdp_fJ": round(best["pdp_fJ"], 2)}
        else:
            print("  %s: no size passes all checks" % name)
        for r in refs:
            line(r["version"], r, k="-")
        if best:
            for r in refs:
                if good(r):
                    print("    against %-24s PDP %+4.0f %%, delay %+4.0f %%, T %+4.0f %%" % (
                        r["version"] + ":", 100 * (best["pdp_fJ"] / r["pdp_fJ"] - 1),
                        100 * (best["t_max_ps"] / r["t_max_ps"] - 1),
                        100 * (best["transistors"] / r["transistors"] - 1)))
        print("    %d of %d sizes pass all checks" % (len(ok), len(sized)))
    print("-" * W)
    cur = json.load(open(SELECTION))["cells"] if os.path.isfile(SELECTION) else {}
    for fam in ("FB4", "CS"):
        if fam in chosen:
            c, u = chosen[fam], cur.get(fam, {})
            same = u.get("k") == c["k"] and u.get("r") == c["r"]
            print("  <= selected %-3s %s k %g r %g   (alu_cells.json: %s)" % (
                fam, c["cell"], c["k"], c["r"],
                "same" if same else "k %s r %s" % (u.get("k", "?"), u.get("r", "?"))))
    if select and len(chosen) == 2:
        with open(SELECTION, "w") as f:
            json.dump({"note": "Sizes of the ALU-specific cells: minimum PDP of Step 3c "
                               "(step3_cells/run_alu_cells.py). Read by sim/gen_alu.py.",
                       "cells": chosen}, f, indent=1)
            f.write("\n")
        print("  written to step3_cells/alu_cells.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="reprint the summary from out/")
    ap.add_argument("--select", action="store_true", help="write the selected sizes to alu_cells.json")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rows = read_rows() if args.report else simulate()
    summarize(rows, args.select)


if __name__ == "__main__":
    main()
