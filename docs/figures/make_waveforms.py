#!/usr/bin/env python3
"""Waveform figures for the slides (needs matplotlib and Ngspice; run outside the lab).

  python3 docs/figures/make_waveforms.py
Runs the simulations of demo/tools/wave.py when their results are missing and writes
docs/figures/presentation/wave_pl_fb4.png and wave_alu_fb.png.
"""
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "presentation")
DEMO_OUT = os.path.join(ROOT, "demo", "out")
sys.path.insert(0, os.path.join(ROOT, "sim"))
import alutb  # noqa: E402

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
IN_COL, OUT_COL = "#7d7b74", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "text.color": INK})


def raw(name, args):
    path = os.path.join(DEMO_OUT, name)
    if not os.path.isfile(path):
        subprocess.run([sys.executable, os.path.join(ROOT, "demo", "tools", "wave.py")] + args + ["--no-plot"],
                       check=True, stdout=subprocess.DEVNULL)
    return alutb.read_raw(path)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), dpi=200, facecolor="#ffffff", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("wrote docs/figures/presentation/" + name)


def fb4():
    cols = raw("pl_fb4_demo.raw", ["cell", "fb4"])
    t = [v * 1e9 for v in cols["time"]]
    sigs = ["a", "b", "c0", "c1", "c2", "c3", "p"]
    names = ["A", "B", "C0", "C1", "C2", "C3", "P"]
    fig, ax = plt.subplots(figsize=(12, 4.6))
    n = len(sigs)
    for i, (s, nm) in enumerate(zip(sigs, names)):
        off = (n - 1 - i) * 2.4 + (0 if s == "p" else 0.9)
        y = [v + off for v in cols[s]]
        ax.plot(t, y, color=OUT_COL if s == "p" else IN_COL, lw=1.8 if s == "p" else 1.3)
        ax.text(-0.6, off + 0.9, nm, ha="right", va="center", fontsize=11, fontweight="bold" if s == "p" else None,
                color=INK)
    period = 2.0
    ops = ["ADD", "SUB", "INC", "DEC", "AND", "OR"]
    codes = ["0110", "1001", "0011", "1100", "0001", "0111"]
    top = (n - 1) * 2.4 + 0.9 + 2.3
    for k, (op, code) in enumerate(zip(ops, codes)):
        x0 = period * (1 + 4 * k)
        ax.axvline(x0, color=GRID, lw=0.8, zorder=0)
        ax.text(x0 + 4 * period / 2, top, "%s   C = %s" % (op, code), ha="center", va="bottom", fontsize=10,
                color=INK2)
    ax.axvline(period * 25, color=GRID, lw=0.8, zorder=0)
    ax.set_xlim(-0.2, t[-1])
    ax.set_ylim(-0.3, top + 0.9)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.set_xlabel("time (ns)", color=INK2)
    ax.tick_params(colors=INK2, length=0)
    save(fig, "wave_pl_fb4.png")


def alu():
    cols = raw("alu4_fb_function.raw", ["alu-test", "fb"])
    t = [v * 1e9 for v in cols["time"]]
    pairs = [(5, 3), (3, 12), (15, 1), (8, 8)]
    vecs = [(0, 0, 0)] + [(a, b, s) for s in range(8) for a, b in pairs]
    period = 5.0
    fig, axes = plt.subplots(3, 1, figsize=(12, 5.2), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1.25, 1.25], "hspace": 0.12})
    word = lambda key: [v for v in cols[key]]
    ax = axes[0]
    ax.plot(t, word("aw"), color=IN_COL, lw=1.4, label="operand a")
    ax.plot(t, [v for v in word("bw")], color="#c9c7c0", lw=1.4, label="operand b")
    ax.set_ylabel("a (dark)\nb (light)", color=INK2)
    ax = axes[1]
    ax.plot(t, word("yw"), color=OUT_COL, lw=1.8, label="simulated result y")
    ex = [(k + 0.85) * period for k in range(1, len(vecs))]
    ey = [alutb.alu_ref(a, b, s, 4)[0] for a, b, s in vecs[1:]]
    ax.scatter(ex, ey, s=22, color="#ffffff", edgecolor=INK, linewidth=1.0, zorder=5, label="expected value")
    ax.set_ylabel("result y", color=INK2)
    ax.legend(loc="upper left", frameon=False, fontsize=9.5, ncol=2, bbox_to_anchor=(0, 1.18))
    ax = axes[2]
    ax.plot(t, word("fw"), color=OUT_COL, lw=1.6)
    fe = []
    for a, b, s in vecs[1:]:
        y, c, v, z, n = alutb.alu_ref(a, b, s, 4)
        fe.append(8 * c + 4 * v + 2 * z + n)
    ax.scatter(ex, fe, s=22, color="#ffffff", edgecolor=INK, linewidth=1.0, zorder=5)
    ax.set_ylabel("flags 8c+4v+2z+n", color=INK2)
    ax.set_xlabel("time (ns)", color=INK2)
    for ax in axes:
        for k in range(1, 9):
            ax.axvline(period * (1 + 4 * (k - 1)), color=GRID, lw=0.8, zorder=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color("#c3c2b7")
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors=INK2, length=0)
        ax.set_ylim(-1, 16.5)
        ax.set_yticks([0, 5, 10, 15])
        ax.grid(axis="y", color=GRID, lw=0.6)
    for k, op in enumerate(alutb.OPS):
        axes[0].text(period * (1 + 4 * k) + 2 * period, 17.2, op, ha="center", va="bottom", fontsize=10, color=INK2)

    axes[2].set_xlim(0, t[-1])
    save(fig, "wave_alu_fb.png")


if __name__ == "__main__":
    fb4()
    alu()
