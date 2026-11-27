#!/usr/bin/env python3
"""Figures of the paper (column width 3.4 in, grey scale), from the lab results.

  python3 docs/paper/make_paper_figures.py
Writes docs/paper/figures/: fig_alu_org.png (ALU organization), fig_after_layout.png
(energy and delay of the seven routed ALUs, results/lab/after_layout_comparison.md),
fig_chip.png (routed proposed ALU, crop of the KLayout screenshot of 22 Nov 2026).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "figures")
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "font.size": 7, "axes.linewidth": 0.6, "mathtext.fontset": "stix"})
INK = "#111111"


def box(ax, x, y, w, h, text, fill="#ffffff", lw=0.8, size=7, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8", fc=fill, ec=INK, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            fontweight="bold" if bold else "normal", color=INK, linespacing=1.1)


def arrow(ax, x1, y1, x2, y2, lw=0.7):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", lw=lw, color=INK, shrinkA=0, shrinkB=0, mutation_scale=6))


def line(ax, xs, ys, lw=0.7):
    ax.plot(xs, ys, color=INK, lw=lw, solid_capstyle="butt")


def alu_org(path):
    fig, ax = plt.subplots(figsize=(3.4, 2.3), dpi=600)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 69)
    ax.axis("off")
    centres = [21, 40, 59, 78]  # bit 3 .. bit 0
    # decoder and select inputs
    box(ax, 86, 52, 13.5, 10, "Decoder", fill="#eeeeee", size=6.5)
    ax.text(92.75, 67.2, "$s_2\\,s_1\\,s_0$", ha="center", va="center", fontsize=6.5)
    arrow(ax, 92.75, 65.6, 92.75, 62)
    # code-line bus C0..C3
    line(ax, [14, 86], [57.5, 57.5], lw=1.6)
    ax.text(15, 60.2, "$C_0$–$C_3$ (common to all bits)", ha="left", va="center", fontsize=6.5)
    # K bus
    line(ax, [14, 89.5], [30, 30])
    line(ax, [89.5, 89.5], [30, 52])
    ax.text(50, 32.0, "$K = s_2$", ha="center", va="center", fontsize=6.5)
    # carry into bit 0
    line(ax, [96, 96], [52, 21])
    arrow(ax, 96, 21, 85, 21)
    ax.text(97.2, 24.0, "$c_0$", ha="left", va="center", fontsize=6.5)
    for i, c in enumerate(centres):
        bit = 3 - i
        box(ax, c - 7, 39, 14, 11, "FB4", fill="#dddddd", bold=True)
        box(ax, c - 7, 15, 14, 12, "CS", fill="#dddddd", bold=True)
        arrow(ax, c - 3, 57.5, c - 3, 50)
        ax.text(c + 3.6, 53.6, "$a_{%d}\\,b_{%d}$" % (bit, bit), ha="center", va="center", fontsize=6)
        arrow(ax, c + 3.2, 51.8, c + 3.2, 50)
        arrow(ax, c + 2, 39, c + 2, 27)
        ax.text(c + 3.0, 35.5, "$P_{%d}$" % bit, ha="left", va="center", fontsize=6)
        arrow(ax, c - 4, 30, c - 4, 27)
        arrow(ax, c, 15, c, 9.5)
        ax.text(c, 7.4, "$y_{%d}$" % bit, ha="center", va="center", fontsize=6.5)
        ax.text(c, 2.0, "bit %d" % bit, ha="center", va="center", fontsize=6, color="#444444")
        if i < 3:
            arrow(ax, centres[i + 1] - 7, 21, c + 7, 21)
            ax.text((c + 7 + centres[i + 1] - 7) / 2, 23.4, "$c_{%d}$" % bit, ha="center", va="center", fontsize=6)
    # flags
    box(ax, 0.4, 14, 10.2, 14, "Flags\nC V\nZ N", fill="#eeeeee", size=6)
    arrow(ax, 14, 21, 10.6, 21)
    ax.text(12.3, 23.4, "$c_4$", ha="center", va="center", fontsize=6)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def after_layout(path):
    labels = ["D3 beh", "D3 slice", "D3 map", "D4 beh", "D4 slice", "D4 map", "P"]
    energy = [4898.7, 3333.0, 3807.1, 2798.5, 2140.4, 2077.3, 1453.0]
    delay = [1812.0, 2144.4, 3476.1, 1874.0, 2257.1, 3220.6, 2615.4]
    colours = ["#cfcfcf"] * 3 + ["#8f8f8f"] * 3 + ["#1a1a1a"]
    fig, axs = plt.subplots(1, 2, figsize=(3.4, 1.9), dpi=600, sharey=True)
    for ax, vals, title, top in ((axs[0], energy, "Energy per operation (fJ)", 6300),
                                 (axs[1], delay, "Worst-case delay (ps)", 4450)):
        y = list(range(len(labels)))
        ax.barh(y, vals, color=colours, edgecolor=INK, linewidth=0.4, height=0.68)
        for yi, v in zip(y, vals):
            ax.text(v + top * 0.015, yi, "%.0f" % v, va="center", ha="left", fontsize=6)
        ax.set_xlim(0, top)
        ax.set_title(title, fontsize=7, pad=3)
        ax.tick_params(axis="x", labelsize=6, length=2, width=0.5)
        ax.tick_params(axis="y", labelsize=6.5, length=0)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.xaxis.set_major_locator(plt.MaxNLocator(3))
    axs[0].set_yticks(range(len(labels)))
    axs[0].set_yticklabels(labels)
    axs[0].invert_yaxis()  # shared y axis: once
    fig.tight_layout(w_pad=0.6)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def chip(path):
    src = os.path.join(ROOT, "docs", "presentation", "screens", "klayout_fb_full.png")
    im = Image.open(src).convert("RGB")
    im.crop((430, 172, 1566, 930)).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    alu_org(os.path.join(OUT, "fig_alu_org.png"))
    after_layout(os.path.join(OUT, "fig_after_layout.png"))
    chip(os.path.join(OUT, "fig_chip.png"))
    for f in sorted(os.listdir(OUT)):
        print("wrote", os.path.join("docs/paper/figures", f), Image.open(os.path.join(OUT, f)).size)


if __name__ == "__main__":
    main()
