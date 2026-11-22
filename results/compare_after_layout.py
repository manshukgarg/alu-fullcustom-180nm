#!/usr/bin/env python3
"""Comparison of every placed-and-routed ALU after layout (Step 7).

  python3 results/compare_after_layout.py
Reads the lab results of Step 2 (D3, OSU018 cells) and Step 5 (D4, project library pl018,
and the proposed ALU P) from results/lab/ and writes results/lab/after_layout_comparison.md.
All values are from the same transistor-level test (sim/alutb.py) of the netlist extracted
from the routed layout.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(HERE, "lab")
OPS = ["ADD", "SUB", "INC", "DEC", "AND", "OR", "XOR", "NOT"]


def load():
    d3 = json.load(open(os.path.join(LAB, "step2_2026-11-22.json")))
    d5 = json.load(open(os.path.join(LAB, "step5_final_2026-11-22.json")))
    rows = []
    for key in ("beh", "slice", "map"):
        g, p = d3["designs"][key], d3["post"][key]
        rows.append(dict(name="D3 " + key, lib="OSU018", **_row(g, p, g["yosys_cells"])))
    for key in ("beh", "slice", "map", "fb"):
        g, p = d5["designs"][key], d5["designs"][key]["post"]
        cells = d5["pre_layout"][key]["yosys_cells"]
        rows.append(dict(name=("P fb" if key == "fb" else "D4 " + key), lib="pl018", **_row(g, p, cells)))
    return rows


def _row(g, p, cells):
    w, h = g["die_um"]
    return dict(cells=cells, placed=g["placed"], die=w * h, die_wh=(w, h), T=g["extracted_T"],
                C=g["extracted_C_fF"], t=p["t_max_ps"], tm=p["t_mean_ps"], e=p["e_avg_fJ"],
                leak=p["p_leak_nW"], edp=p["edp"], ops=p["energy_by_op_fJ"])


def pct(new, old):
    return 100.0 * (new - old) / old


def main():
    rows = load()
    by = {r["name"]: r for r in rows}
    out = ["# ALUs after layout: D3 (OSU018), D4 (pl018) and the proposed ALU P", "",
           "Netlists extracted from the routed layouts (every transistor and parasitic capacitance),",
           "simulated with `sim/alutb.py` (Ngspice, 1.8 V, 27 C, FO4 loads, 229 transitions, all",
           "correct in every design). Written by `results/compare_after_layout.py` from",
           "`results/lab/step2_2026-11-22.json` and `results/lab/step5_final_2026-11-22.json`.", "",
           "| Design | Library | Netlist cells | Cells placed | Die (um) | Die area (um2) | Transistors | C (fF) "
           "| Worst delay (ps) | Mean delay (ps) | Energy per op (fJ) | Leakage (nW) | Energy x delay (fJ ns) |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        out.append("| %s | %s | %d | %d | %.1f x %.1f | %.0f | %d | %d | %.1f | %.1f | %.1f | %.2f | %.1f |" % (
            r["name"], r["lib"], r["cells"], r["placed"], r["die_wh"][0], r["die_wh"][1], r["die"], r["T"], r["C"],
            r["t"], r["tm"], r["e"], r["leak"], r["edp"]))
    out += ["", "## D4 against D3 (same description, other cell library)", "",
            "| Description | Cells placed | Die area | Worst delay | Energy per op | Leakage | Energy x delay |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for key in ("beh", "slice", "map"):
        a, b = by["D3 " + key], by["D4 " + key]
        out.append("| %s | %+.0f %% | %+.0f %% | %+.1f %% | %+.1f %% | %+.1f %% | %+.1f %% |" % (
            key, pct(b["placed"], a["placed"]), pct(b["die"], a["die"]), pct(b["t"], a["t"]), pct(b["e"], a["e"]),
            pct(b["leak"], a["leak"]), pct(b["edp"], a["edp"])))
    p = by["P fb"]
    out += ["", "## Proposed ALU P against every other laid-out design", "",
            "| Reference | Die area | Transistors | Worst delay | Energy per op | Leakage | Energy x delay |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if r is p:
            continue
        out.append("| %s | %+.0f %% | %+.0f %% | %+.1f %% | %+.1f %% | %+.1f %% | %+.1f %% |" % (
            r["name"], pct(p["die"], r["die"]), pct(p["T"], r["T"]), pct(p["t"], r["t"]), pct(p["e"], r["e"]),
            pct(p["leak"], r["leak"]), pct(p["edp"], r["edp"])))
    out += ["", "## Energy per operation after layout (fJ)", "",
            "| Design | " + " | ".join(OPS) + " |", "| --- |" + " --- |" * len(OPS)]
    for r in rows:
        out.append("| %s | %s |" % (r["name"], " | ".join("%d" % v for v in r["ops"])))
    best = {k: min(rows, key=lambda r: r[k])["name"] for k in ("die", "T", "t", "e", "leak", "edp")}
    out += ["", "Best value of each quantity: die area %s, transistors %s, worst delay %s, energy %s, "
            "leakage %s, energy x delay %s." % (best["die"], best["T"], best["t"], best["e"], best["leak"],
                                                best["edp"]), ""]
    path = os.path.join(LAB, "after_layout_comparison.md")
    open(path, "w").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
