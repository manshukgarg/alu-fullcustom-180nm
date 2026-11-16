#!/usr/bin/env python3
"""Step 6 summary: the 4-bit ALU built from each cell style, transistor level before layout.

Reads out/<design>.json (written by sim/alutb.py) and netlists/index.json; writes
out/step6_results.json.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DESIGNS = ("gate", "conv", "opt", "pl", "fb")
OPS = ("ADD", "SUB", "INC", "DEC", "AND", "OR", "XOR", "NOT")
W = 79


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def f(x, fmt="%.1f"):
    return "n/a" if x is None else fmt % x


def main():
    index = load(os.path.join(HERE, "netlists", "index.json"))
    res = {d: load(os.path.join(OUT, d + ".json")) for d in DESIGNS}
    ok = {d: res[d].get("status") == "ok" for d in DESIGNS}
    print("=" * W)
    print("STEP 6 SUMMARY  4-bit ALU at transistor level from each cell style (pre-layout)")
    print("=" * W)
    for d in DESIGNS:
        print("  %-5s %s" % (d, index.get(d, {}).get("note", "")[:W - 8]))
    row = "%-29s" + " %-9s" * len(DESIGNS)
    print("-" * W)
    print(row % (("Ngspice, 1.8 V, 27 C, FO4",) + DESIGNS))
    print(row % (("cells / transistors",) + tuple(
        "%s / %s" % (index.get(d, {}).get("cells", "?"), index.get(d, {}).get("transistors", "?"))
        for d in DESIGNS)))
    print(row % (("logic check (2048 vectors)",) + tuple(index.get(d, {}).get("check", "n/a")[:9]
                                                           for d in DESIGNS)))

    def line(text, fn):
        print(row % ((text,) + tuple(fn(res[d]) if ok[d] else "-" for d in DESIGNS)))
    line("cycles correct", lambda c: "%d/%d" % (c["transitions"] - c["wrong_cycles"], c["transitions"]))
    line("weak output levels", lambda c: "%d" % c.get("weak_levels", 0))
    line("worst delay (ps)", lambda c: f(c.get("t_max_ps")))
    line("  full carry ripples (ps)", lambda c: f(c.get("t_crit_max_ps")))
    line("  random operand changes", lambda c: f(c.get("t_rand_max_ps")))
    line("mean delay (ps)", lambda c: f(c.get("t_avg_ps")))
    line("energy per operation (fJ)", lambda c: f(c.get("e_avg_fJ")))
    line("input-driver energy (fJ)", lambda c: f(c.get("e_drv_avg_fJ")))
    line("leakage power (nW)", lambda c: f(c.get("p_leak_nW"), "%.2f"))
    line("energy x delay (fJ ns)", lambda c: f(c.get("edp_fJns")))
    ref = res["conv"] if ok["conv"] else None
    if ref and ref.get("t_max_ps") and ref.get("e_avg_fJ"):
        print("-" * W)
        print(row % (("Against conv",) + DESIGNS))
        for text, key in (("worst delay", "t_max_ps"), ("energy per operation", "e_avg_fJ"),
                          ("energy x worst delay", "edp_fJns"), ("leakage power", "p_leak_nW")):
            print(row % (("  " + text,) + tuple(
                "%+.0f %%" % (100 * (res[d][key] / ref[key] - 1))
                if ok[d] and res[d].get(key) and ref.get(key) else "-" for d in DESIGNS)))
    print("-" * W)
    print("%-10s" % "E (fJ)" + "".join("%8s" % o for o in OPS))
    for d in DESIGNS:
        e = res[d].get("e_op_fJ") or {}
        print("  %-8s" % d + "".join("%8s" % f(e.get(o), "%.0f") for o in OPS))
    for d in DESIGNS:
        wst = res[d].get("worst")
        if wst:
            print("  worst %-5s %s -> %s, last output %s" % (d, wst["from"], wst["to"], wst["last_output"]))
    msgs = []
    for d in DESIGNS:
        c = res[d]
        if not ok[d]:
            msgs.append("%s: %s" % (d, c.get("status", "no result (see out/%s.out)" % d)))
        msgs += ["%s: %s" % (d, e) for e in c.get("errors", [])[:3]]
        msgs += ["%s note: %s" % (d, e) for e in c.get("notes", [])[:2]]
        if c.get("warning"):
            msgs.append("%s: %s" % (d, c["warning"]))
        if ok[d] and (c["wrong_cycles"] or c["missing_references"]):
            msgs.append("%s: %d wrong cycles, %d missing references (see out/%s_transitions.csv)"
                        % (d, c["wrong_cycles"], c["missing_references"], d))
    if msgs:
        print("-" * W)
        for m in msgs[:12]:
            print("  " + m[:W - 2])
    with open(os.path.join(OUT, "step6_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
