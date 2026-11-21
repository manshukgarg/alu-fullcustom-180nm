#!/usr/bin/env python3
"""Result charts for the slides and the paper (needs matplotlib; run outside the lab).

  python3 docs/figures/make_charts.py        writes docs/figures/presentation/chart_*.png

Data: the stored Ngspice results (results/ngspice46_2026-11-16/) and the lab results
transcribed in results/lab/*.json.
"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "presentation")
RES = os.path.join(ROOT, "results", "ngspice46_2026-11-16")
LAB = os.path.join(ROOT, "results", "lab")

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
BASE, MID, PROPOSED = "#aeaca5", "#86b6ef", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK})


def style(ax, horizontal=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left" if not horizontal else "bottom"].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x" if horizontal else "y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def round_bars(ax, bars, horizontal=False, radius_px=4.0):
    """Replace matplotlib bars by bars with a rounded data end and a square base."""
    fig = ax.figure
    fig.canvas.draw()
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform((0, 0)), inv.transform((radius_px, radius_px))
    rx, ry = abs(x1 - x0), abs(y1 - y0)
    for b in bars:
        x, y, w, h = b.get_x(), b.get_y(), b.get_width(), b.get_height()
        col = b.get_facecolor()
        b.set_visible(False)
        if horizontal:
            r = min(rx, w / 2)
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%g" % r,
                                        mutation_aspect=ry / rx, facecolor=col, edgecolor="none", zorder=3,
                                        snap=False))
            ax.add_patch(Rectangle((x, y), w - r, h, facecolor=col, edgecolor="none", zorder=3, snap=False))
        else:
            r = min(ry, h / 2) if h > 0 else 0
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%g" % rx,
                                        mutation_aspect=ry / rx, facecolor=col, edgecolor="none", zorder=3,
                                        snap=False))
            ax.add_patch(Rectangle((x, y), w, max(h - r, 0), facecolor=col, edgecolor="none", zorder=3,
                                   snap=False))


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


# ---------------------------------------------------------------------- cells (Step 3b)
def cells_chart():
    rows = list(csv.DictReader(open(os.path.join(RES, "step3b_sweep_1800mV.csv"))))
    valid = [r for r in rows if r["wrong_levels"] == "0" and r["weak_levels"] == "0" and r["missing_delays"] == "0"]
    static = {"INV": "inv_cmos", "NAND2": "nand2_cmos", "NOR2": "nor2_cmos", "XOR2": "xor_cmos12",
              "MUX2": "mux_cmos12", "MUX2I": "muxi_cmos10", "FA": "fa_cmos28"}
    fams = list(static)
    best, ref = {}, {}
    for f in fams:
        cand = [r for r in valid if r["family"] == f]
        best[f] = min(cand, key=lambda r: float(r["pdp_fJ"]))
        ref[f] = next(r for r in rows if r["cell"] == static[f] and float(r["k"]) == 1 and float(r["r"]) == 2)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    w = 0.34
    for ax, key, title in ((axes[0], "pdp_fJ", "Power-delay product (fJ)"),
                           (axes[1], "t_max_ps", "Worst delay (ps)")):
        xs = range(len(fams))
        b1 = ax.bar([x - w / 2 - 0.02 for x in xs], [float(ref[f][key]) for f in fams], w, color=BASE)
        b2 = ax.bar([x + w / 2 + 0.02 for x in xs], [float(best[f][key]) for f in fams], w, color=PROPOSED)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(fams)
        ax.set_title(title, loc="left", fontsize=12, color=INK, pad=10)
        style(ax)
        top = max(float(ref[f][key]) for f in fams)
        ax.set_ylim(0, top * 1.18)
        for x, f in zip(xs, fams):
            a, b = float(ref[f][key]), float(best[f][key])
            ax.text(x + w / 2 + 0.02, b + top * 0.02, "%+.0f%%" % (100 * (b / a - 1)), ha="center", va="bottom",
                    fontsize=9, color=INK2, zorder=6,
                    bbox=dict(boxstyle="square,pad=0.1", facecolor=SURFACE, edgecolor="none"))
        round_bars(ax, list(b1) + list(b2))
    axes[0].legend(handles=[Patch(color=BASE, label="static CMOS, reference size (k = 1, r = 2)"),
                            Patch(color=PROPOSED, label="best topology at its minimum-PDP size")],
                   loc="upper left", frameon=False, fontsize=9.5)
    save(fig, "chart_cells_pdp_delay.png")
    return best, ref


# ---------------------------------------------------------------------- ALU-specific cells (Step 3c)
def alu_cells_chart():
    # step3c_alu_cells_summary.txt (identical lab run of 16 Nov)
    data = {"FB4": {"static CMOS: 3 x MUX2": (688.7, 70.78, 36), "library cells: 3 x MUX2I": (433.6, 21.58, 24),
                    "proposed FB4 cell": (450.2, 18.95, 20)},
            "CS": {"static CMOS: MUX2 + XOR2 + MUX2": (614.6, 93.84, 36),
                   "library cells: MUX2 + XOR2 + MUX2": (510.0, 41.08, 30), "proposed CS cell": (458.6, 33.64, 24)}}
    cols = [BASE, MID, PROPOSED]
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.0))
    w = 0.25
    for ax, idx, title in ((axes[0], 1, "Power-delay product (fJ)"), (axes[1], 0, "Worst delay (ps)"),
                           (axes[2], 2, "Transistors")):
        bars = []
        for g, cell in enumerate(("FB4", "CS")):
            vals = list(data[cell].values())
            for s in range(3):
                b = ax.bar(g + (s - 1) * (w + 0.02), vals[s][idx], w, color=cols[s])
                bars += list(b)
                if s == 2:
                    ax.text(g + (w + 0.02), vals[s][idx], "%g" % vals[s][idx] if idx == 2 else "%.1f" % vals[s][idx]
                            if idx == 1 else "%.0f" % vals[s][idx],
                            ha="center", va="bottom", fontsize=9, color=INK, zorder=6)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["FB4", "CS"])
        ax.set_title(title, loc="left", fontsize=12, pad=10)
        style(ax)
        ax.set_ylim(0, max(v[idx] for d in data.values() for v in d.values()) * 1.15)
        round_bars(ax, bars)
    fig.legend(handles=[Patch(color=BASE, label="same function from static CMOS gates"),
                        Patch(color=MID, label="same function from the library's TG cells"),
                        Patch(color=PROPOSED, label="proposed ALU-specific cell")],
               loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.06))
    save(fig, "chart_alu_cells.png")


# ---------------------------------------------------------------------- ALUs at transistor level (Step 6)
def alu_chart():
    lab = json.load(open(os.path.join(LAB, "step6_2026-11-16.json")))
    order = ["conv", "gate", "pl", "opt", "fb"]
    names = {"conv": "Static CMOS cells (D1)", "gate": "Gate-level cells (NAND based)",
             "pl": "Library pl018 cells", "opt": "Minimum-PDP cells (D2)", "fb": "Proposed: FB4 + CS per bit"}
    metrics = [("transistors", "Transistors", "%d"), ("t_max_ps", "Worst delay (ps)", "%.0f"),
               ("e_avg_fJ", "Energy per operation (fJ)", "%.0f"), ("p_leak_nW", "Leakage (nW)", "%.2f")]
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.6), sharey=True)
    ys = list(range(len(order)))[::-1]
    for ax, (key, title, fmt) in zip(axes, metrics):
        vals = [lab["designs"][d][key] for d in order]
        bars = ax.barh(ys, vals, 0.55, color=[PROPOSED if d == "fb" else BASE for d in order])
        for y, v in zip(ys, vals):
            ax.text(v * 1.02, y, fmt % v, va="center", ha="left", fontsize=9, color=INK, zorder=6)
        ax.set_xlim(0, max(vals) * 1.28)
        ax.set_title(title, loc="left", fontsize=11.5, pad=8)
        style(ax, horizontal=True)
        ax.set_xticks([])
        round_bars(ax, list(bars), horizontal=True)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([names[d] for d in order])
    save(fig, "chart_alu_transistor_level.png")


if __name__ == "__main__":
    cells_chart()
    alu_cells_chart()
    alu_chart()
