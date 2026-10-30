"""Render a Layout to PNG (review aid; needs matplotlib, not used in the lab flow)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

STYLE = {   # type: (face colour, alpha, hatch, z-order)
    "nwell": ("#e8d98a", 0.35, "", 0),
    "ndiff": ("#3fa34d", 0.85, "", 1),
    "pdiff": ("#b5803c", 0.85, "", 1),
    "ntr":   ("#c0392b", 0.95, "xx", 2),
    "ptr":   ("#c0392b", 0.95, "xx", 2),
    "poly":  ("#d9473f", 0.90, "", 2),
    "ndc":   ("#1f1f1f", 0.90, "", 3),
    "pdc":   ("#1f1f1f", 0.90, "", 3),
    "pc":    ("#1f1f1f", 0.90, "", 3),
    "psc":   ("#555555", 0.90, "", 3),
    "nsc":   ("#555555", 0.90, "", 3),
    "m1":    ("#3b6fd6", 0.45, "", 4),
    "m2c":   ("#000000", 0.95, "++", 5),
    "m2":    ("#9b59b6", 0.40, "", 6),
}
PLANE_OF = {"nwell": "well", "m1": "metal1", "m2": "metal2", "m2c": "metal1"}


def render(L, path, scale=0.12):
    xs, ys = [], []
    for plane in L.planes.values():
        for (x, y) in plane:
            xs.append(x)
            ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    fig, ax = plt.subplots(figsize=(max(3, (x1 - x0) * scale), max(3, (y1 - y0) * scale)))
    for t, (fc, a, hatch, z) in STYLE.items():
        plane = PLANE_OF.get(t, "active")
        cells = [c for c, v in L.planes[plane].items() if v == t]
        for (rx1, ry1, rx2, ry2) in L.rects(cells):
            ax.add_patch(Rectangle((rx1, ry1), rx2 - rx1, ry2 - ry1, facecolor=fc,
                                   alpha=a, hatch=hatch, edgecolor="none", zorder=z))
    # metal1 over contacts drawn as outline so contacts stay visible
    for t in ("ndc", "pdc", "pc", "psc", "nsc"):
        cells = [c for c, v in L.planes["active"].items() if v == t]
        for (rx1, ry1, rx2, ry2) in L.rects(cells):
            ax.add_patch(Rectangle((rx1 + 1, ry1 + 1), rx2 - rx1 - 2, ry2 - ry1 - 2,
                                   facecolor="white", edgecolor="none", alpha=0.9, zorder=3.5))
    for layer, (lx1, ly1, lx2, ly2), text, use, cls in L.labels:
        ax.text((lx1 + lx2) / 2, (ly1 + ly2) / 2, text, ha="center", va="center",
                fontsize=8, fontweight="bold", color="black", zorder=10)
    if L.bbox:
        bx1, by1, bx2, by2 = L.bbox
        ax.add_patch(Rectangle((bx1, by1), bx2 - bx1, by2 - by1, fill=False,
                               edgecolor="black", linestyle="--", linewidth=0.8, zorder=11))
    ax.set_xlim(x0 - 2, x1 + 2)
    ax.set_ylim(y0 - 2, y1 + 2)
    ax.set_aspect("equal")
    ax.set_xticks(range((x0 // 4) * 4, x1 + 4, 4))
    ax.set_yticks(range((y0 // 4) * 4, y1 + 4, 4))
    ax.tick_params(labelsize=5)
    ax.grid(True, linewidth=0.2, alpha=0.5)
    ax.set_title("%s (lambda grid, 1 lambda = 0.1 um)" % L.name, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
