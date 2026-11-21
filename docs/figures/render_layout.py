#!/usr/bin/env python3
"""Presentation figure of a cell layout from its Magic file (needs matplotlib; outside the lab).

  python3 docs/figures/render_layout.py mag/pl_fb4.mag docs/figures/presentation/layout_pl_fb4.png
Layers in the usual Magic colours on a white background, contacts and vias with a cross,
pin labels, the cell outline, a 1 um scale bar and a layer legend.
"""
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

LAMBDA_UM = 0.1
# Magic layer: (label, fill colour, alpha, z-order, kind)
STYLE = {
    "nwell": ("n-well", "#efe3b0", 0.55, 0, "fill"),
    "ndiffusion": ("n-diffusion", "#3f9f4f", 0.85, 1, "fill"),
    "pdiffusion": ("p-diffusion", "#c58a3b", 0.85, 1, "fill"),
    "ntransistor": ("gate", "#c62f2f", 1.0, 2, "fill"),
    "ptransistor": ("gate", "#c62f2f", 1.0, 2, "fill"),
    "polysilicon": ("polysilicon", "#e04848", 0.92, 2, "fill"),
    "ndcontact": ("contact", "#2b2b2b", 1.0, 3, "contact"),
    "pdcontact": ("contact", "#2b2b2b", 1.0, 3, "contact"),
    "polycontact": ("contact", "#2b2b2b", 1.0, 3, "contact"),
    "psubstratepcontact": ("contact", "#2b2b2b", 1.0, 3, "contact"),
    "nsubstratencontact": ("contact", "#2b2b2b", 1.0, 3, "contact"),
    "metal1": ("metal1", "#3d6fe0", 0.42, 4, "fill"),
    "m2contact": ("via (metal1-metal2)", "#111111", 1.0, 5, "via"),
    "metal2": ("metal2", "#9b4fc6", 0.45, 6, "fill"),
}


def read_mag(path):
    rects, labels, bbox, cur = [], [], None, None
    for line in open(path):
        line = line.strip()
        m = re.match(r"<< (\S+) >>", line)
        if m:
            cur = m.group(1)
            continue
        f = line.split()
        if f[:1] == ["rect"] and cur in STYLE:
            rects.append((cur,) + tuple(int(v) for v in f[1:5]))
        elif f[:1] == ["rlabel"]:
            labels.append((f[1], tuple(int(v) for v in f[3:7]), f[-1]))
        elif f[:2] == ["string", "FIXED_BBOX"]:
            bbox = tuple(int(v) for v in f[2:6])
    return rects, labels, bbox


def render(mag, out, width_in=None, legend=True, dpi=220):
    rects, labels, bbox = read_mag(mag)
    xs = [r[1] for r in rects] + [r[3] for r in rects]
    ys = [r[2] for r in rects] + [r[4] for r in rects]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W = x1 - x0 + 18
    H = y1 - y0 + (22 if legend else 12)
    width_in = width_in or W * 0.075
    fig = plt.figure(figsize=(width_in, width_in * H / W), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0 - 14, x1 + 4)
    ax.set_ylim(y0 - (18 if legend else 8), y1 + 4)
    ax.set_aspect("equal")
    ax.axis("off")
    pt = width_in * 72.0 / W                      # points per lambda
    for layer, a, b, c, d in sorted(rects, key=lambda r: STYLE[r[0]][3]):
        name, col, alpha, z, kind = STYLE[layer]
        if kind == "fill":
            ax.add_patch(Rectangle((a, b), c - a, d - b, facecolor=col, alpha=alpha, edgecolor="none",
                                   zorder=z))
        else:
            ax.add_patch(Rectangle((a, b), c - a, d - b, facecolor="#ffffff" if kind == "contact" else "#e8e8e8",
                                   edgecolor=col, linewidth=0.6 * pt, zorder=z))
            ax.plot([a + 0.4, c - 0.4], [b + 0.4, d - 0.4], color=col, lw=0.45 * pt, zorder=z + 0.1)
            ax.plot([a + 0.4, c - 0.4], [d - 0.4, b + 0.4], color=col, lw=0.45 * pt, zorder=z + 0.1)
    if bbox:
        ax.add_patch(Rectangle((bbox[0], bbox[1]), bbox[2] - bbox[0], bbox[3] - bbox[1], fill=False,
                               edgecolor="#555555", linestyle=(0, (4, 3)), linewidth=0.25 * pt, zorder=8))
    for layer, (a, b, c, d), text in labels:
        cx, cy = (a + c) / 2, (b + d) / 2
        if text in ("vdd", "gnd"):
            ax.text(x0 - 1, cy, text, ha="right", va="center", fontsize=3.2 * pt, fontweight="bold",
                    color="#333333", zorder=9)
            continue
        ax.text(cx, cy, text, ha="center", va="center", fontsize=3.4 * pt, fontweight="bold", color="#000000",
                zorder=9, bbox=dict(boxstyle="round,pad=0.15", facecolor="#ffffff", edgecolor="none", alpha=0.85))
    # scale bar: 1 um
    sx, sy = x1 - 10, y0 - 7
    ax.plot([sx, sx + 1 / LAMBDA_UM], [sy, sy], color="#000000", lw=0.6 * pt, solid_capstyle="butt", zorder=9)
    ax.text(sx + 0.5 / LAMBDA_UM, sy - 1.2, "1 um", ha="center", va="top", fontsize=2.6 * pt, zorder=9)
    if bbox:
        ax.text(x0, y0 - 7, "%.1f um x %.1f um" % ((bbox[2] - bbox[0]) * LAMBDA_UM, (bbox[3] - bbox[1]) * LAMBDA_UM),
                ha="left", va="center", fontsize=2.8 * pt, color="#333333", zorder=9)
    if legend:
        items = [("n-well", "#efe3b0", 0.8), ("n-diffusion", "#3f9f4f", 0.85), ("p-diffusion", "#c58a3b", 0.85),
                 ("polysilicon", "#e04848", 0.92), ("metal1", "#3d6fe0", 0.42), ("metal2", "#9b4fc6", 0.45)]
        handles = [Patch(facecolor=c, alpha=a, label=n) for n, c, a in items]
        handles.append(Patch(facecolor="#ffffff", edgecolor="#2b2b2b", label="contact / via"))
        ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=len(handles),
                  frameon=False, fontsize=2.6 * pt, handlelength=1.2, columnspacing=1.0)
    fig.savefig(out, dpi=dpi, facecolor="#ffffff")
    plt.close(fig)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
    print("wrote", sys.argv[2])
