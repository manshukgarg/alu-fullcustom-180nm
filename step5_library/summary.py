#!/usr/bin/env python3
"""Step 5 summary: library checks, the automated ALU with the library (D4), and D4 against D3.

Reuses the log parsers of step2_rtl_baseline/summary.py on this step's files and
reads Step 2's results (step2_rtl_baseline/out/step2_results.json) for the comparison.
Writes out/step5_results.json.
"""
import importlib.util
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
_spec = importlib.util.spec_from_file_location("s2", os.path.join(ROOT, "step2_rtl_baseline", "summary.py"))
s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s2)
s2.HERE, s2.OUT = HERE, OUT            # the parsers read this step's logs
f = s2.f
DESIGNS = (("beh", "beh", "behavioural RTL, synthesized (rtl/alu4.v)"),
           ("slice", "slice", "bit-sliced RTL, synthesized (rtl/alu4_slice.v)"),
           ("map", "map", "hand-mapped netlist with pl_fa full adders (rtl/alu4_map_pl018.v)"),
           ("fb", "fb", "hand-mapped function-block slice, pl_fb4 + pl_cs (rtl/alu4_fb_pl018.v)"))
W = 79


def read(path):
    try:
        with open(path, errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def lvs_result(cell):
    text = read(os.path.join(OUT, "cells", cell + "_lvs.out")) + read(os.path.join(OUT, "cells", cell + "_netgen.log"))
    low = text.lower()
    if not text:
        return "n/a"
    if "do not match" in low or "failed matching" in low:
        return "FAIL"
    if "failed pin matching" in low or "port errors" in low:
        return "pins"
    if "property errors" in low or "missing properties" in low:
        return "prop"
    if "match uniquely" in low or "circuits match with" in low or "match correctly" in low:
        return "match"
    return "?"


def library():
    cells = json.load(open(os.path.join(HERE, "cells.json")))["cells"]
    mag = read(os.path.join(OUT, "cells", "magic.log"))
    drc = {m.group(1): int(m.group(2)) for m in re.finditer(r"^DRC_ERRORS (\S+) (\d+)", mag, re.M)}
    try:
        char = json.load(open(os.path.join(OUT, "characterization.json")))
    except (OSError, ValueError):
        char = {}
    rows = []
    for c in cells:
        r = char.get(c["name"], {})
        caps = [v["mean"] for v in r.get("cap_pF", {}).values()]
        i, j = 2, 1
        dr = [a["cell_rise"][i][j] for a in r.get("arcs", {}).values() if a.get("cell_rise")]
        df = [a["cell_fall"][i][j] for a in r.get("arcs", {}).values() if a.get("cell_fall")]
        rows.append({"name": c["name"], "sites": int(round(c["width_um"] / 0.8)), "area_um2": c["area_um2"],
                     "transistors": c["transistors"], "drc": drc.get(c["name"]),
                     "lvs": "-" if not c["outputs"] else lvs_result(c["name"]),
                     "cin_max_fF": max(caps) * 1e3 if caps else None,
                     "tpd_rise_ps": max(dr) * 1e3 if dr else None, "tpd_fall_ps": max(df) * 1e3 if df else None,
                     "leak_nW": r.get("leakage_nW"), "missing": r.get("missing"),
                     "netlist": "pex" if "extracted" in r.get("source", "") else ("drawn" if r else "-"),
                     "provisional": c.get("provisional", False)})
    errors = [l.strip() for l in mag.splitlines() if l.startswith(("ERROR", "DRC: "))][:6]
    checks = [l.strip()[7:] for l in read(os.path.join(OUT, "characterization.txt")).splitlines()
              if l.strip().startswith("check:")][:6]
    return rows, errors, checks


def num(v):
    if v >= 100 or float(v).is_integer():
        return "%.0f" % v
    return "%.1f" % v if v >= 10 else "%.2f" % v


def change(a, b):
    """Value of this step with its change against Step 2, e.g. '1234 (-18%)'."""
    if a is None:
        return "n/a"
    if b is None or not b:
        return num(a)
    return "%s (%+.0f%%)" % (num(a), 100 * (a / b - 1))


def main():
    lib, lib_err, char_checks = library()
    designs = [d for d, _, _ in DESIGNS]
    titles = [t for _, t, _ in DESIGNS]
    res = s2.collect(designs)
    print("=" * W)
    print("STEP 5 SUMMARY  project cell library pl018 and the automated ALU with it (D4)")
    print("=" * W)
    print("cell       sites  area  T  DRC  LVS    Cin max  tpd rise/fall*  leak    netlist")
    for r in lib:
        if r["netlist"] == "-":
            print("%-10s %4d %6.1f %2d %4s  %s" % (r["name"], r["sites"], r["area_um2"], r["transistors"],
                                                 f(r["drc"], "%d"), "filler"))
            continue
        print("%-10s %4d %6.1f %2d %4s  %-6s %6s   %5s/%-5s   %6s  %s" % (
            r["name"], r["sites"], r["area_um2"], r["transistors"],
            f(r["drc"], "%d"), r["lvs"], f(r["cin_max_fF"], "%.1f"), f(r["tpd_rise_ps"], "%.0f"),
            f(r["tpd_fall_ps"], "%.0f"), f(r["leak_nW"], "%.3f"), r["netlist"]))
    print("* fF, ps, nW; worst arc at 16 fF load and 80 ps input slope")
    print("-" * W)
    for d, _, note in DESIGNS:
        print("  %-5s %s" % (d, note[:W - 8]))
    s2.print_flow(res, designs, titles)
    print("-" * W)
    s2.print_sim(res, designs, titles)
    # comparison with Step 2 (same designs with the OSU018 cells)
    try:
        d3 = json.load(open(os.path.join(ROOT, "step2_rtl_baseline", "out", "step2_results.json")))
    except (OSError, ValueError):
        d3 = None
    print("-" * W)
    if d3:
        row = s2.flow_row(len(designs))
        print(row % (("D4 after layout (vs D3)",) + tuple(titles)))
        for text, key in (("cells placed", ("layout", "cells")), ("worst delay (ps)", ("post", "t_max_ps")),
                          ("energy per operation (fJ)", ("post", "e_avg_fJ")),
                          ("leakage power (nW)", ("post", "p_leak_nW")),
                          ("energy x delay (fJ ns)", ("post", "edp_fJns"))):
            print(row % (("  " + text,) + tuple(
                change(res[d][key[0]].get(key[1]), d3.get(d, {}).get(key[0], {}).get(key[1]))
                for d in designs)))
        areas = []
        for d in designs:
            da, db = res[d]["layout"]["die_um"], d3.get(d, {}).get("layout", {}).get("die_um")
            areas.append(change(da[0] * da[1] if da else None, db[0] * db[1] if db else None))
        print(row % (("  die area (um2)",) + tuple(areas)))
    else:
        print("D3 results not found: run step2_rtl_baseline/run.sh for the comparison")
    msgs = ["library: " + e for e in lib_err] + ["characterization: " + e for e in char_checks]
    msgs += s2.messages(res, designs)
    if msgs:
        print("-" * W)
        for m in msgs[:14]:
            print("  " + m[:W - 2])
    res["library"] = lib
    with open(os.path.join(OUT, "step5_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
