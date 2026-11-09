#!/usr/bin/env python3
"""Step 2 summary: one screen for both RTL descriptions, and out/step2_results.json.

Reads the logs of run.sh (iverilog, Yosys, OpenSTA, Qflow, Magic) and the results of
the transistor-level simulations (out/sim/*.json, written by sim/alutb.py).
"""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DESIGNS = (("beh", "behavioural RTL"), ("slice", "bit-sliced RTL"))
OPS = ("ADD", "SUB", "INC", "DEC", "AND", "OR", "XOR", "NOT")


def read(path):
    try:
        with open(path, errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def tests(name):
    m = re.search(r"TESTS (\d+) ERRORS (\d+)", read(os.path.join(OUT, name + ".log")))
    return {"tests": int(m.group(1)), "errors": int(m.group(2))} if m else None


def fmt_tests(r):
    if r is None:
        return "no result"
    return "%d/%d pass" % (r["tests"] - r["errors"], r["tests"])


def yosys(d):
    text = read(os.path.join(OUT, "yosys_%s.log" % d))
    if "=== alu4 ===" in text:
        text = text[text.rindex("=== alu4 ==="):]
    cells = area = None
    types = Counter()
    for ln in text.splitlines():
        m = re.match(r"^\s*(\d+)\s+[\d.]+\s+cells\s*$", ln) or re.search(r"Number of cells:\s*(\d+)", ln)
        if m:
            cells = int(m.group(1))
        m = re.search(r"Chip area for .*?:\s*([\d.]+)", ln)
        if m:
            area = float(m.group(1))
        m = re.match(r"^\s*(\d+)\s+[\d.]+\s+([A-Z][A-Z0-9_]*)\s*$", ln)
        if m:
            types[m.group(2)] = int(m.group(1))
            continue
        m = re.match(r"^\s+([A-Z][A-Z0-9_]*)\s+(\d+)\s*$", ln)
        if m:
            types[m.group(1)] = int(m.group(2))
    return {"cells": cells, "area_um2": area, "types": dict(types)}


def sta(d):
    text = read(os.path.join(OUT, "sta_%s.log" % d))
    m = re.search(r"^\s*([\d.]+)\s+data arrival time", text, re.M)
    sp = re.search(r"Startpoint:\s*(\S+)", text)
    ep = re.search(r"Endpoint:\s*(\S+)", text)
    return {"delay_ns": float(m.group(1)) if m else None,
            "path": "%s->%s" % (sp.group(1), ep.group(1)) if sp and ep else ""}


def layout(d):
    q = os.path.join(HERE, "qflow_" + d)
    text = read(os.path.join(q, "layout", "alu4.def"))
    res = {"cells": None, "fill": None, "die_um": None}
    u = re.search(r"UNITS\s+DISTANCE\s+MICRONS\s+(\d+)", text)
    die = re.search(r"DIEAREA\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)", text)
    if u and die:
        k = float(u.group(1))
        x0, y0, x1, y1 = (int(die.group(i)) for i in range(1, 5))
        res["die_um"] = [round((x1 - x0) / k, 2), round((y1 - y0) / k, 2)]
    comps = re.search(r"COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS", text, re.S)
    if comps:
        types = Counter(m.group(2) for m in re.finditer(r"-\s+(\S+)\s+(\S+)", comps.group(1)))
        res["fill"] = sum(v for t, v in types.items() if t.upper().startswith("FILL"))
        res["cells"] = sum(types.values()) - res["fill"]
    route = [l.split("Final:", 1)[1].strip() for l in read(os.path.join(q, "log", "route.log")).splitlines()
             if "Final:" in l]
    res["route"] = route[-1] if route else "n/a"
    lvs = [l.strip() for l in read(os.path.join(q, "log", "lvs.log")).splitlines()
           if re.search(r"circuits match|netlists match|do not match|mismatch|final result", l, re.I)]
    res["lvs"] = lvs[-1] if lvs else "n/a"
    mag = read(os.path.join(OUT, "magic_%s.log" % d))
    m = re.search(r"^DRC_ERRORS (\d+)", mag, re.M)
    res["drc_errors"] = int(m.group(1)) if m else None
    res["drc_types"] = [l[5:] for l in mag.splitlines() if l.startswith("DRC: ")][:6]
    res["extracted"] = "EXTRACTED" in mag
    res["magic_errors"] = [l.strip() for l in mag.splitlines() if l.startswith("ERROR")][:3]
    res["qflow_errors"] = [l.strip() for l in read(os.path.join(OUT, "qflow_%s.log" % d)).splitlines()
                           if re.search(r"\berror\b", l, re.I)][:3]
    return res


def sim(label):
    try:
        with open(os.path.join(OUT, "sim", label + ".json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"status": "no result (see out/sim/%s.out)" % label}


def f(x, fmt="%.1f"):
    return "n/a" if x is None else fmt % x


def short_lvs(text):
    low = text.lower()
    if "do not match" in low or "mismatch" in low:
        return "MISMATCH"
    if "match" in low:
        return "match"
    return text[:12] or "n/a"


def main():
    res = {}
    for d, _ in DESIGNS:
        res[d] = {"rtl": tests("sim_" + d), "gate": tests("sim_gate_" + d), "yosys": yosys(d),
                  "sta": sta(d), "layout": layout(d), "pre": sim(d + "_pre"), "post": sim(d + "_post")}
    W = 79
    print("=" * W)
    print("STEP 2 SUMMARY  4-bit ALU, automated OSU018 implementation (design D3)")
    print("=" * W)
    row = "%-33s %-22s %-22s"
    print(row % ("", DESIGNS[0][1], DESIGNS[1][1]))
    b, s = res["beh"], res["slice"]
    print(row % ("RTL simulation, exhaustive", fmt_tests(b["rtl"]), fmt_tests(s["rtl"])))
    print(row % ("Gate-level simulation, exhaustive", fmt_tests(b["gate"]), fmt_tests(s["gate"])))
    print(row % ("Yosys: cells, area (um2)",
                 "%s, %s" % (f(b["yosys"]["cells"], "%d"), f(b["yosys"]["area_um2"])),
                 "%s, %s" % (f(s["yosys"]["cells"], "%d"), f(s["yosys"]["area_um2"]))))
    print(row % ("OpenSTA worst delay (ns), path",
                 "%s %s" % (f(b["sta"]["delay_ns"], "%.3f"), b["sta"]["path"]),
                 "%s %s" % (f(s["sta"]["delay_ns"], "%.3f"), s["sta"]["path"])))

    def die(r):
        dm = r["layout"]["die_um"]
        return "%s, %s" % (f(r["layout"]["cells"], "%d"), "%.1f x %.1f um" % tuple(dm) if dm else "n/a")
    print(row % ("Qflow: cells placed, die size", die(b), die(s)))
    print(row % ("Qflow routing", b["layout"]["route"][:22], s["layout"]["route"][:22]))
    print(row % ("Qflow LVS (cell level)", short_lvs(b["layout"]["lvs"]), short_lvs(s["layout"]["lvs"])))
    print(row % ("Magic DRC with real cell layouts", f(b["layout"]["drc_errors"], "%d errors"),
                 f(s["layout"]["drc_errors"], "%d errors")))

    def ext(r):
        p = r["post"]
        if "transistors" not in p:
            return "n/a"
        return "%d T, %d C (%.0f fF)" % (p["transistors"], p.get("capacitors", 0), p.get("cap_total_fF", 0))
    print(row % ("Extracted layout netlist", ext(b), ext(s)))

    ref = next((r[k] for r in (b, s) for k in ("post", "pre") if r[k].get("status") == "ok"), {})
    print("-" * W)
    print("Ngspice, %s V, %s C, FO4 loads: %s transitions, %s full carry ripples"
          % (ref.get("vdd", "1.8"), f(ref.get("temp"), "%g"), ref.get("transitions", "n/a"),
             ref.get("critical_transitions", "n/a")))
    row4 = "%-31s %-11s %-11s %-11s %-11s"
    print(row4 % ("", "beh pre", "beh post", "slice pre", "slice post"))
    cols = [b["pre"], b["post"], s["pre"], s["post"]]

    def line(text, fn):
        print(row4 % ((text,) + tuple(fn(c) if c.get("status") == "ok" else "-" for c in cols)))
    line("cycles correct", lambda c: "%d/%d" % (c["transitions"] - c["wrong_cycles"], c["transitions"]))
    line("worst delay (ps)", lambda c: f(c.get("t_max_ps")))
    line("mean delay (ps)", lambda c: f(c.get("t_avg_ps")))
    line("energy per operation (fJ)", lambda c: f(c.get("e_avg_fJ")))
    line("input-driver energy (fJ)", lambda c: f(c.get("e_drv_avg_fJ")))
    line("leakage power (nW)", lambda c: f(c.get("p_leak_nW"), "%.2f"))
    line("energy x worst delay (fJ ns)", lambda c: f(c.get("edp_fJns")))
    for d, name in DESIGNS:
        pre, post = res[d]["pre"], res[d]["post"]
        if pre.get("status") == "ok" and post.get("status") == "ok" and pre.get("t_max_ps") and pre.get("e_avg_fJ"):
            print("  %-5s after layout: worst delay %+.1f %%, energy %+.1f %%" % (
                d, 100 * (post["t_max_ps"] / pre["t_max_ps"] - 1),
                100 * (post["e_avg_fJ"] / pre["e_avg_fJ"] - 1)))
    print("%-24s" % "Post-layout energy (fJ)" + "".join("%6s" % o for o in OPS))
    for d, name in DESIGNS:
        e = res[d]["post"].get("e_op_fJ") or {}
        print("  %-22s" % name + "".join("%6s" % f(e.get(o), "%.0f") for o in OPS))
    for d, name in DESIGNS:
        wst = res[d]["post"].get("worst")
        if wst:
            print("  worst %-5s %s -> %s, last output %s" % (
                d, wst["from"], wst["to"], wst["last_output"]))
    # anything that needs a look
    msgs = []
    for d, name in DESIGNS:
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
            msgs += ["%s_%s: %s" % (d, k, e) for e in c.get("errors", [])[:3]]
            msgs += ["%s_%s note: %s" % (d, k, e) for e in c.get("notes", [])[:3]]
            if c.get("warning"):
                msgs.append("%s_%s: %s" % (d, k, c["warning"]))
            if c.get("status") == "ok" and (c["wrong_cycles"] or c["weak_levels"] or c["missing_references"]):
                msgs.append("%s_%s: %d wrong cycles, %d weak levels, %d missing references (see CSV)" % (
                    d, k, c["wrong_cycles"], c["weak_levels"], c["missing_references"]))
    if msgs:
        print("-" * W)
        for m in msgs[:14]:
            print("  " + m[:W - 2])
    with open(os.path.join(OUT, "step2_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
