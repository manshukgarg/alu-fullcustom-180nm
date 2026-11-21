#!/usr/bin/env python3
"""Facts of a routed ALU from the logs and results of the last lab run, printed before the
layout is opened (demo/show.sh chip and chip-magic).

  python3 demo/tools/facts.py fb | beh | slice | map | osu-beh | osu-slice | osu-map
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TITLES = {"beh": "behavioural RTL, synthesized", "slice": "bit-sliced RTL, synthesized",
          "map": "hand-mapped netlist with full-adder cells",
          "fb": "proposed: hand-mapped function-block slice, one FB4 and one CS cell per bit"}


def step2_parsers(step_dir):
    spec = importlib.util.spec_from_file_location("s2", os.path.join(ROOT, "step2_rtl_baseline", "summary.py"))
    s2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s2)
    s2.HERE, s2.OUT = step_dir, os.path.join(step_dir, "out")
    return s2


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "fb"
    osu = name.startswith("osu-")
    d = name[4:] if osu else name
    step_dir = os.path.join(ROOT, "step2_rtl_baseline" if osu else "step5_library")
    lib = "OSU018 cells (design D3)" if osu else ("library pl018" if d == "fb" else "library pl018 (design D4)")
    print("Routed 4-bit ALU '%s': %s, %s" % (name, TITLES.get(d, d), lib))
    try:
        lay = step2_parsers(step_dir).layout(d)
    except Exception as exc:                      # the logs of an interrupted run
        print("  (layout logs not readable: %s)" % exc)
        return
    die = lay.get("die_um")
    if lay.get("cells") is None:
        print("  no layout logs of this design (run its step in the lab first)")
        return
    print("  placement and routing (Qflow): %s cells, die %s um; routing: %s" % (
        lay.get("cells"), "%.1f x %.1f" % tuple(die) if die else "n/a", lay.get("route")))
    print("  checks: Magic DRC with the cell layouts %s errors; Qflow LVS %s" % (
        lay.get("drc_errors"), lay.get("lvs")))
    try:
        r = json.load(open(os.path.join(step_dir, "out", "sim", "%s_post.json" % d)))
    except (OSError, ValueError):
        print("  transistor-level simulation after layout: no result")
        return
    if r.get("status") != "ok":
        print("  transistor-level simulation after layout: %s" % r.get("status"))
        return
    good = r["transitions"] - r["wrong_cycles"]
    print("  extraction (Magic): %d transistors, %d parasitic capacitors (%.0f fF in total)" % (
        r["transistors"], r["capacitors"], r["cap_total_fF"]))
    print("  after layout (Ngspice): %d of %d transitions correct, worst delay %.0f ps, "
          "%.0f fJ per operation, leakage %.2f nW" % (
              good, r["transitions"], r["t_max_ps"], r["e_avg_fJ"], r.get("p_leak_nW") or float("nan")))


if __name__ == "__main__":
    main()
