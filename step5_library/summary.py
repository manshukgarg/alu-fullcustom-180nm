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
f, fmt_tests, short_lvs = s2.f, s2.fmt_tests, s2.short_lvs
DESIGNS = s2.DESIGNS
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
    return "%.0f" % v if v >= 100 or float(v).is_integer() else "%.1f" % v


def change(a, b):
    if a is None or b is None or not b:
        return "n/a"
    return "%s / %s (%+.0f%%)" % (num(a), num(b), 100 * (a / b - 1))


def main():
    lib, lib_err, char_checks = library()
    res = {"library": lib}
    for d, _ in DESIGNS:
        res[d] = {"rtl": s2.tests("sim_" + d), "gate": s2.tests("sim_gate_" + d), "yosys": s2.yosys(d),
                  "sta": s2.sta(d), "layout": s2.layout(d), "pre": s2.sim(d + "_pre"), "post": s2.sim(d + "_post")}
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
            r["name"] + ("+" if r["provisional"] else ""), r["sites"], r["area_um2"], r["transistors"],
            f(r["drc"], "%d"), r["lvs"], f(r["cin_max_fF"], "%.1f"), f(r["tpd_rise_ps"], "%.0f"),
            f(r["tpd_fall_ps"], "%.0f"), f(r["leak_nW"], "%.3f"), r["netlist"]))
    print("* fF, ps, nW; worst arc at 16 fF load and 80 ps input slope; + provisional size")
    b, s = res["beh"], res["slice"]
    row = "%-33s %-22s %-22s"
    print("-" * W)
    print(row % ("", DESIGNS[0][1], DESIGNS[1][1]))
    print(row % ("RTL simulation, exhaustive", fmt_tests(b["rtl"]), fmt_tests(s["rtl"])))
    print(row % ("Gate-level simulation, exhaustive", fmt_tests(b["gate"]), fmt_tests(s["gate"])))
    print(row % ("Yosys: cells, area (um2)",
                 "%s, %s" % (f(b["yosys"]["cells"], "%d"), f(b["yosys"]["area_um2"])),
                 "%s, %s" % (f(s["yosys"]["cells"], "%d"), f(s["yosys"]["area_um2"]))))
    print(row % ("OpenSTA worst delay (ns)", f(b["sta"]["delay_ns"], "%.3f"), f(s["sta"]["delay_ns"], "%.3f")))

    def die(r):
        dm = r["layout"]["die_um"]
        return "%s, %s" % (f(r["layout"]["cells"], "%d"), "%.1f x %.1f um" % tuple(dm) if dm else "n/a")
    print(row % ("Qflow: cells placed, die size", die(b), die(s)))
    print(row % ("Qflow routing", b["layout"]["route"][:22], s["layout"]["route"][:22]))
    print(row % ("Qflow LVS / DRC with real cells",
                 "%s / %s" % (short_lvs(b["layout"]["lvs"]), f(b["layout"]["drc_errors"], "%d")),
                 "%s / %s" % (short_lvs(s["layout"]["lvs"]), f(s["layout"]["drc_errors"], "%d"))))
    print("-" * W)
    row4 = "%-31s %-11s %-11s %-11s %-11s"
    print(row4 % ("Ngspice, 1.8 V, 27 C, FO4 loads", "beh pre", "beh post", "slice pre", "slice post"))
    cols = [b["pre"], b["post"], s["pre"], s["post"]]

    def line(text, fn):
        print(row4 % ((text,) + tuple(fn(c) if c.get("status") == "ok" else "-" for c in cols)))
    line("cycles correct", lambda c: "%d/%d" % (c["transitions"] - c["wrong_cycles"], c["transitions"]))
    line("worst delay (ps)", lambda c: f(c.get("t_max_ps")))
    line("energy per operation (fJ)", lambda c: f(c.get("e_avg_fJ")))
    line("leakage power (nW)", lambda c: f(c.get("p_leak_nW"), "%.2f"))
    line("energy x worst delay (fJ ns)", lambda c: f(c.get("edp_fJns")))
    # comparison with Step 2
    try:
        d3 = json.load(open(os.path.join(ROOT, "step2_rtl_baseline", "out", "step2_results.json")))
    except (OSError, ValueError):
        d3 = None
    print("-" * W)
    if d3:
        print(row % ("After layout: D4 / D3 (change)", DESIGNS[0][1], DESIGNS[1][1]))
        for text, key in (("cells placed", ("layout", "cells")), ("worst delay (ps)", ("post", "t_max_ps")),
                          ("energy per operation (fJ)", ("post", "e_avg_fJ")),
                          ("leakage power (nW)", ("post", "p_leak_nW")),
                          ("energy x worst delay (fJ ns)", ("post", "edp_fJns"))):
            vals = []
            for d, _ in DESIGNS:
                a = res[d][key[0]].get(key[1]) if isinstance(res[d][key[0]], dict) else None
                c3 = d3.get(d, {}).get(key[0], {}).get(key[1])
                vals.append(change(a, c3))
            print(row % ("  " + text, vals[0], vals[1]))
        for d, _ in DESIGNS:
            da, d3a = res[d]["layout"]["die_um"], d3.get(d, {}).get("layout", {}).get("die_um")
            if da and d3a:
                print("  die area %-5s %.0f um2 / %.0f um2 (%+.0f%%)" % (
                    d, da[0] * da[1], d3a[0] * d3a[1], 100 * (da[0] * da[1] / (d3a[0] * d3a[1]) - 1)))
    else:
        print("D3 results not found: run step2_rtl_baseline/run.sh for the comparison")
    msgs = ["library: " + e for e in lib_err] + ["characterization: " + e for e in char_checks]
    for d, _ in DESIGNS:
        r = res[d]
        for k in ("rtl", "gate"):
            if r[k] is None or r[k]["errors"]:
                msgs.append("%s %s simulation: %s" % (d, k, fmt_tests(r[k])))
        msgs += ["%s qflow: %s" % (d, e) for e in r["layout"]["qflow_errors"]]
        msgs += ["%s magic: %s" % (d, e) for e in r["layout"]["magic_errors"]]
        msgs += ["%s DRC: %s" % (d, e) for e in r["layout"]["drc_types"]]
        for k in ("pre", "post"):
            c = r[k]
            if c.get("status") != "ok":
                msgs.append("%s_%s: %s" % (d, k, c.get("status")))
            msgs += ["%s_%s: %s" % (d, k, e) for e in c.get("errors", [])[:2]]
            if c.get("warning"):
                msgs.append("%s_%s: %s" % (d, k, c["warning"]))
    if msgs:
        print("-" * W)
        for m in msgs[:12]:
            print("  " + m[:W - 2])
    with open(os.path.join(OUT, "step5_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
