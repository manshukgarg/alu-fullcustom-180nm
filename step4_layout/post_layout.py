#!/usr/bin/env python3
"""Step 4 summary: DRC and LVS results, and every cell simulated before and after layout.

Run by run.sh after Magic and Netgen. Each cell is simulated twice with the
Step 3 testbench (FO4 load, every input transition, delay including the input
driver): once as its transistor netlist with estimated junctions (pre-layout)
and once as the netlist Magic extracted from the layout, with all parasitic
capacitances (post-layout). Writes out/cells_post_layout.csv.
"""
import csv
import json
import multiprocessing as mp
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, os.path.join(HERE, "..", "step3_cells"))
import cellnet  # noqa: E402
import run_cells  # noqa: E402

VDD, PERIOD = 1.8, 2e-9


def read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def drc_counts():
    counts, errors = {}, []
    for line in read(os.path.join(OUT, "magic.log")).splitlines():
        m = re.match(r"DRC_ERRORS (\S+) (\d+)", line)
        if m:
            counts[m.group(1)] = int(m.group(2))
        elif line.startswith("DRC: ") or line.startswith("ERROR"):
            errors.append(line)
    return counts, errors


def lvs_result(name):
    """Netgen verdict for one cell: match, prop (property errors), pins, FAIL or n/a."""
    text = read(os.path.join(OUT, name + "_lvs.out")) + read(os.path.join(OUT, name + "_netgen.log"))
    if not text:
        return "n/a"
    low = text.lower()
    if "do not match" in low or "failed matching" in low:
        return "FAIL"
    if "failed pin matching" in low or "port errors" in low:
        return "pins"
    if "property errors" in low or "missing properties" in low:
        return "prop"
    if "match uniquely" in low or "circuits match with" in low or "match correctly" in low:
        return "match"
    return "?"


def wrapped_extract(name, ports):
    """Extracted subcircuit renamed, plus a wrapper with the testbench pin order."""
    text = read(os.path.join(OUT, name + "_pex.spice"))
    if ".subckt" not in text.lower():
        return None
    lines, joined = text.splitlines(), []
    for ln in lines:
        if ln.startswith("+") and joined:
            joined[-1] += " " + ln[1:]
        else:
            joined.append(ln)
    body, got = [], None
    for ln in joined:
        low = ln.strip().lower()
        if low == ".end":
            continue
        if low.startswith(".subckt"):
            parts = ln.split()
            got = parts[2:]
            ln = " ".join([parts[0], name + "_x"] + got)
        body.append(ln)
    conn = []
    for p in got:
        if p in ports:
            conn.append(p)
        elif "sub" in p.lower() or p.lower() in ("gnd!", "0"):
            conn.append("gnd")
        elif p.lower().startswith("w_") or p.lower() == "vdd!":
            conn.append("vdd")
        else:
            conn.append(p)
    wrap = [".subckt %s %s" % (name, " ".join(ports)),
            "Xpex %s %s_x" % (" ".join(conn), name), ".ends %s" % name]
    return "\n".join(body) + "\n" + "\n".join(wrap) + "\n"


def job(args):
    c, which = args
    cell = getattr(cellnet, c["cell"])(c["k"], c["r"])
    cell.name = c["name"]
    if which == "pre":
        return c["name"], which, run_cells.evaluate(cell, VDD, PERIOD, OUT, c["k"], c["r"], tag="_pre")
    ports = cell.inputs + cell.outputs + ["vdd", "gnd"]
    dut = wrapped_extract(c["name"], ports)
    if dut is None:
        return c["name"], which, None
    return c["name"], which, run_cells.evaluate(cell, VDD, PERIOD, OUT, c["k"], c["r"],
                                                dut_text=dut, tag="_pex")


def ok(row):
    return row is not None and row["wrong_levels"] == 0 and row["missing_delays"] == 0


def main():
    cells = json.load(open(os.path.join(HERE, "cells.json")))["cells"]
    counts, drc_lines = drc_counts()
    jobs = [(c, w) for c in cells for w in ("pre", "post")]
    res = {}
    with mp.Pool(max(1, min(8, os.cpu_count() or 2))) as pool:
        for name, which, row in pool.imap_unordered(job, jobs):
            res[(name, which)] = row

    print()
    print("STEP 4 SUMMARY  full-custom cell libraries, %.2f V, 27 C, FO4 load" % VDD)
    print("delay = worst transition incl. input driver; PDP = power x delay; post = extracted layout")
    hdr = "%-11s %3s %5s %6s %4s %6s %13s %13s %7s" % (
        "cell", "T", "W(um)", "A(um2)", "DRC", "LVS", "tmax pre/post", "PDP pre/post", "layout")
    print(hdr)
    rows = []
    lib = None
    for c in cells:
        if c["lib"] != lib:
            lib = c["lib"]
            print("-" * len(hdr) + "  " + lib)
        pre, post = res.get((c["name"], "pre")), res.get((c["name"], "post"))
        drc = counts.get(c["name"])
        lvs = lvs_result(c["name"])
        t = "%6.1f/%6.1f" % (pre["t_max_ps"] if pre else float("nan"),
                             post["t_max_ps"] if post else float("nan"))
        p = "%6.2f/%6.2f" % (pre["pdp_fJ"] if pre else float("nan"),
                             post["pdp_fJ"] if post else float("nan"))
        if ok(pre) and ok(post):
            d = "%+6.1f%%" % (100 * (post["pdp_fJ"] / pre["pdp_fJ"] - 1))
        else:
            d = "  check"
        print("%-11s %3d %5.1f %6.1f %4s %6s %13s %13s %7s" % (
            c["name"], c["transistors"], c["width_um"], c["area_um2"],
            "n/a" if drc is None else drc, lvs, t, p, d))
        rows.append({"name": c["name"], "lib": c["lib"], "family": c["family"], "cell": c["cell"],
                     "k": c["k"], "r": c["r"], "transistors": c["transistors"],
                     "width_um": c["width_um"], "area_um2": c["area_um2"], "drc_errors": drc,
                     "lvs": lvs,
                     "pre_tmax_ps": pre and pre["t_max_ps"], "post_tmax_ps": post and post["t_max_ps"],
                     "pre_ptot_uW": pre and pre["p_total_uW"], "post_ptot_uW": post and post["p_total_uW"],
                     "pre_pdp_fJ": pre and pre["pdp_fJ"], "post_pdp_fJ": post and post["pdp_fJ"],
                     "post_ok": ok(post)})
    print("-" * len(hdr))
    by = {(r["lib"], r["family"]): r for r in rows}
    fams = [r["family"] for r in rows if r["lib"] == "optimized"]
    print("after layout, optimized vs conventional:  PDP change, delay change, area change")
    line = []
    for f in fams:
        o, cv = by.get(("optimized", f)), by.get(("conventional", f))
        if not o or not cv or not (o["post_ok"] and cv["post_ok"]):
            line.append("%s n/a" % f)
            continue
        line.append("%s %+.0f/%+.0f/%+.0f%%" % (
            f, 100 * (o["post_pdp_fJ"] / cv["post_pdp_fJ"] - 1),
            100 * (o["post_tmax_ps"] / cv["post_tmax_ps"] - 1),
            100 * (o["area_um2"] / cv["area_um2"] - 1)))
    for i in range(0, len(line), 4):
        print("  " + "   ".join(line[i:i + 4]))
    if drc_lines:
        print("---- DRC messages (first 8) ----")
        for ln in drc_lines[:8]:
            print("  " + ln)
    for (name, which), row in sorted(res.items()):
        if row is not None and not ok(row):
            print("check %s %s: %d wrong levels, %d missing delays" % (
                name, which, row["wrong_levels"], row["missing_delays"]))
        if row is None:
            print("check %s %s: no extracted netlist (see out/magic.log)" % (name, which))
    with open(os.path.join(OUT, "cells_post_layout.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
