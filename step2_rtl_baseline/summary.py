#!/usr/bin/env python3
"""Step 2 summary: one screen for the three designs, and out/step2_results.json.

Reads the logs of run.sh (iverilog, Yosys, OpenSTA, Qflow, Magic) and the results of
the transistor-level simulations (out/sim/*.json, written by sim/alutb.py).
"""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
# key, column title, description
DESIGNS = (("beh", "beh", "behavioural RTL, synthesized (rtl/alu4.v)"),
           ("slice", "slice", "bit-sliced RTL, synthesized (rtl/alu4_slice.v)"),
           ("map", "map", "hand-mapped netlist with FAX1 full adders (rtl/alu4_map_osu018.v)"))
W = 79
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


def fmt_tests(r, short=False):
    if r is None:
        return "no result"
    if short:
        return "all %d" % r["tests"] if not r["errors"] else "%d fail" % r["errors"]
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


def short_route(text):
    low = text.lower()
    if "no failed routes" in low:
        return "complete"
    m = re.search(r"(\d+)", text)
    if "fail" in low and m:
        return "%s failed" % m.group(1)
    return text[:14] or "n/a"


def collect(designs):
    res = {}
    for d in designs:
        res[d] = {"rtl": tests("sim_" + d), "gate": tests("sim_gate_" + d), "yosys": yosys(d),
                  "sta": sta(d), "layout": layout(d), "pre": sim(d + "_pre"), "post": sim(d + "_post")}
    return res


def is_ok(c):
    return c.get("status") == "ok"


def flow_row(n):
    """Row format of the flow tables: label and one column per design, at most 79 columns."""
    return ("%-33s" + " %-14s" * n) if n <= 3 else ("%-30s" + " %-11s" * n)


def print_flow(res, designs, titles):
    """Synthesis and layout rows, one column per design."""
    row = flow_row(len(designs))
    cols = [res[d] for d in designs]
    print(row % (("",) + tuple(titles)))
    short = len(designs) > 3
    print(row % (("Netlist simulation, exhaustive",) + tuple(fmt_tests(r["rtl"], short) for r in cols)))
    print(row % (("Gate-level simulation",) + tuple(fmt_tests(r["gate"], short) for r in cols)))
    print(row % (("Yosys: cells, area (um2)",) + tuple(
        "%s, %s" % (f(r["yosys"]["cells"], "%d"), f(r["yosys"]["area_um2"])) for r in cols)))
    print(row % (("OpenSTA worst delay (ns)",) + tuple(f(r["sta"]["delay_ns"], "%.3f") for r in cols)))
    print(row % (("Qflow: cells placed",) + tuple(f(r["layout"]["cells"], "%d") for r in cols)))
    print(row % (("Qflow: die size (um)",) + tuple(
        "%.1f x %.1f" % tuple(r["layout"]["die_um"]) if r["layout"]["die_um"] else "n/a" for r in cols)))
    print(row % (("Qflow routing",) + tuple(short_route(r["layout"]["route"]) for r in cols)))
    print(row % (("Qflow LVS (cell level)",) + tuple(short_lvs(r["layout"]["lvs"]) for r in cols)))
    print(row % (("Magic DRC, real cell layouts",) + tuple(
        f(r["layout"]["drc_errors"], "%d errors") for r in cols)))
    print(row % (("Extracted: transistors, C (fF)",) + tuple(
        "%d, %.0f" % (r["post"]["transistors"], r["post"].get("cap_total_fF", 0))
        if "transistors" in r["post"] else "n/a" for r in cols)))


def print_sim(res, designs, titles):
    """Transistor-level rows: before and after layout for every design."""
    ref = next((res[d][k] for d in designs for k in ("post", "pre") if is_ok(res[d][k])), {})
    print("Ngspice, %s V, %s C, FO4 loads: %s transitions, %s full carry ripples"
          % (ref.get("vdd", "1.8"), f(ref.get("temp"), "%g"), ref.get("transitions", "n/a"),
             ref.get("critical_transitions", "n/a")))
    wide = len(designs) <= 3
    row = ("%-24s" + " %8s" * (2 * len(designs))) if wide else ("%-22s" + " %6s" * (2 * len(designs)))
    heads = []
    for t in titles:
        heads += ["%s pre" % t[:3], "%s post" % t[:3]] if wide else [t[:5], "post"]
    print(row % (("" if wide else "before | after layout",) + tuple(heads)))
    cols = [res[d][k] for d in designs for k in ("pre", "post")]

    def line(text, fn):
        print(row % ((text,) + tuple(fn(c) if is_ok(c) else "-" for c in cols)))

    def num(x, fmt="%.1f"):
        """A value in at most six characters in the narrow table."""
        if x is None:
            return "n/a"
        return fmt % x if wide or len(fmt % x) <= 6 else "%.0f" % x

    def cycles(c):
        good = c["transitions"] - c["wrong_cycles"]
        if wide:
            return "%d/%d" % (good, c["transitions"])
        return "all" if not c["wrong_cycles"] else "%d bad" % c["wrong_cycles"]
    line("cycles correct", cycles)
    line("worst delay (ps)", lambda c: num(c.get("t_max_ps")))
    line("mean delay (ps)", lambda c: num(c.get("t_avg_ps")))
    line("energy per op (fJ)", lambda c: num(c.get("e_avg_fJ")))
    line("driver energy (fJ)", lambda c: num(c.get("e_drv_avg_fJ")))
    line("leakage power (nW)", lambda c: num(c.get("p_leak_nW"), "%.2f"))
    line("energy x delay (fJ ns)", lambda c: num(c.get("edp_fJns")))
    for d in designs:
        pre, post = res[d]["pre"], res[d]["post"]
        if is_ok(pre) and is_ok(post) and pre.get("t_max_ps") and pre.get("e_avg_fJ"):
            print("  %-5s after layout: worst delay %+.1f %%, energy %+.1f %%" % (
                d, 100 * (post["t_max_ps"] / pre["t_max_ps"] - 1),
                100 * (post["e_avg_fJ"] / pre["e_avg_fJ"] - 1)))
    print("%-24s" % "Post-layout energy (fJ)" + "".join("%6s" % o for o in OPS))
    for d in designs:
        e = res[d]["post"].get("e_op_fJ") or {}
        print("  %-22s" % d + "".join("%6s" % f(e.get(o), "%.0f") for o in OPS))
    for d in designs:
        wst = res[d]["post"].get("worst")
        if wst:
            print("  worst %-5s %s -> %s, last output %s" % (d, wst["from"], wst["to"], wst["last_output"]))


def messages(res, designs):
    """Lines for anything that needs a look, then the notes of the netlist preparation."""
    msgs, notes = [], []
    for d in designs:
        r = res[d]
        for k in ("rtl", "gate"):
            if r[k] is None or r[k]["errors"]:
                msgs.append("%s %s simulation: %s" % (d, k, fmt_tests(r[k])))
        msgs += ["%s qflow: %s" % (d, e) for e in r["layout"]["qflow_errors"]]
        msgs += ["%s magic: %s" % (d, e) for e in r["layout"]["magic_errors"]]
        msgs += ["%s DRC: %s" % (d, e) for e in r["layout"]["drc_types"]]
        for k in ("pre", "post"):
            c = r[k]
            if not is_ok(c):
                msgs.append("%s_%s: %s" % (d, k, c.get("status")))
            msgs += ["%s_%s: %s" % (d, k, e) for e in c.get("errors", [])[:3]]
            for e in c.get("notes", [])[:3]:
                text = "%s-layout netlists: %s" % (k, e)
                if text not in notes:
                    notes.append(text)
            if c.get("warning"):
                msgs.append("%s_%s: %s" % (d, k, c["warning"]))
            if is_ok(c) and (c["wrong_cycles"] or c["weak_levels"] or c["missing_references"]):
                msgs.append("%s_%s: %d wrong cycles, %d weak levels, %d missing references (see CSV)" % (
                    d, k, c["wrong_cycles"], c["weak_levels"], c["missing_references"]))
    return msgs + notes


def main():
    designs = [d for d, _, _ in DESIGNS]
    titles = [t for _, t, _ in DESIGNS]
    res = collect(designs)
    print("=" * W)
    print("STEP 2 SUMMARY  4-bit ALU, automated OSU018 implementation (design D3)")
    print("=" * W)
    for d, _, note in DESIGNS:
        print("  %-5s %s" % (d, note[:W - 8]))
    print_flow(res, designs, titles)
    print("-" * W)
    print_sim(res, designs, titles)
    msgs = messages(res, designs)
    if msgs:
        print("-" * W)
        for m in msgs[:14]:
            print("  " + m[:W - 2])
    with open(os.path.join(OUT, "step2_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
