#!/usr/bin/env python3
"""Circuit figures of the report from the project drawings (white background).

  fig_inv_tg.png    CMOS inverter and transmission gate         (docs/report/figures/ref_inv_tg.png)
  fig_xor_mux.png   (a) TG XOR2, (b) TG MUX2, side by side       (ref_xor_tg8.png, ref_mux_tg6.png)
  fig_fb4.png       transistor schematic of FB4                  (docs/figures/presentation/schematic_pl_fb4.png)
  fig_cs.png        transistor schematic of CS                   (docs/figures/presentation/schematic_pl_cs.png)

The title lines drawn inside the source images are cut off (the report caption replaces them).

  python3 docs/report/prepare_circuit_figures.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIGS = os.path.join(HERE, "figures")
PRES = os.path.join(ROOT, "docs", "figures", "presentation")


def rows_with_ink(im):
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    return [any(px[x, y] < 200 for x in range(0, w, 2)) for y in range(h)]


def cut_title(im, min_gap):
    """Remove the text block at the top: everything above the first white gap of min_gap rows
    that follows the first inked row."""
    ink = rows_with_ink(im)
    y = ink.index(True)
    run = 0
    while y < len(ink):
        run = run + 1 if not ink[y] else 0
        if run >= min_gap:
            return im.crop((0, y, im.size[0], im.size[1]))
        y += 1
    raise ValueError("no gap below the title")


def trim(im, pad=20):
    g = im.convert("L").point(lambda v: 255 if v > 245 else 0).convert("1")
    inv = Image.eval(g.convert("L"), lambda v: 255 - v)
    x0, y0, x1, y1 = inv.getbbox()
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.size[0], x1 + pad), min(im.size[1], y1 + pad)))


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def side_by_side(a, b, gap=80):
    h = max(a.size[1], b.size[1]) + 90
    out = Image.new("RGB", (a.size[0] + gap + b.size[0], h), "white")
    out.paste(a, (0, (h - 90 - a.size[1]) // 2))
    out.paste(b, (a.size[0] + gap, (h - 90 - b.size[1]) // 2))
    d = ImageDraw.Draw(out)
    f = font(44)
    for x0, w, t in ((0, a.size[0], "(a)"), (a.size[0] + gap, b.size[0], "(b)")):
        tw = d.textlength(t, font=f)
        d.text((x0 + (w - tw) / 2, h - 70), t, fill="black", font=f)
    return out


def main():
    rgb = lambda p: Image.open(p).convert("RGB")
    inv_tg = trim(rgb(os.path.join(FIGS, "ref_inv_tg.png")))
    inv_tg.save(os.path.join(FIGS, "fig_inv_tg.png"))
    xor = trim(cut_title(rgb(os.path.join(FIGS, "ref_xor_tg8.png")), 25))
    mux = trim(cut_title(rgb(os.path.join(FIGS, "ref_mux_tg6.png")), 25))
    side_by_side(xor, mux).save(os.path.join(FIGS, "fig_xor_mux.png"))
    for cell in ("fb4", "cs"):
        im = rgb(os.path.join(PRES, "schematic_pl_%s.png" % cell))
        trim(cut_title(im, 40)).save(os.path.join(FIGS, "fig_%s.png" % cell))
    for f in ("fig_inv_tg", "fig_xor_mux", "fig_fb4", "fig_cs"):
        print(f, Image.open(os.path.join(FIGS, f + ".png")).size)


if __name__ == "__main__":
    main()
