#!/usr/bin/env python3
"""Figures used by the presentation (needs matplotlib and Pillow; run outside the lab).

  python3 docs/presentation/prepare_assets.py
Writes docs/presentation/assets/: the schematics of FB4 and CS without their header text
(the slide carries the title), and the layout of pl_fb4 without the layer legend for the
title slide. The other figures are used as they are from docs/figures/presentation/.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIG = os.path.join(ROOT, "docs", "figures", "presentation")
OUT = os.path.join(HERE, "assets")
sys.path.insert(0, os.path.join(ROOT, "docs", "figures"))
import render_layout  # noqa: E402


def crop_header(src, dst, top):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    im = im.crop((0, top, w, h))
    # trim the white margin left after the crop
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = Image.eval(Image.composite(im, bg, Image.new("L", im.size, 255)), lambda v: v)
    box = Image.eval(diff, lambda v: 255 - v).getbbox()
    if box:
        pad = 30
        im = im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, w), min(box[3] + pad, im.size[1])))
    im.save(dst)
    print("wrote", os.path.relpath(dst, ROOT), im.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    crop_header(os.path.join(FIG, "schematic_pl_fb4.png"), os.path.join(OUT, "schematic_fb4.png"), 250)
    crop_header(os.path.join(FIG, "schematic_pl_cs.png"), os.path.join(OUT, "schematic_cs.png"), 250)
    dst = os.path.join(OUT, "layout_fb4_plain.png")
    render_layout.render(os.path.join(ROOT, "mag", "pl_fb4.mag"), dst, legend=False)
    print("wrote", os.path.relpath(dst, ROOT))


if __name__ == "__main__":
    main()
