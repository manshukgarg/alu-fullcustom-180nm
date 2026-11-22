#!/usr/bin/env python3
"""Figures used by the presentation (needs matplotlib and Pillow; run outside the lab).

  python3 docs/presentation/prepare_assets.py
Writes docs/presentation/assets/: the schematics of FB4 and CS without their header text
(the slide carries the title), and the layout of pl_fb4 without the layer legend for the
title slide; and the lab screenshots of docs/presentation/screens/ without the desktop
task bar. The other figures are used as they are from docs/figures/presentation/.
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


SCREENS = {  # screenshot: (output, crop box left, top, right, bottom)
    "klayout_fb_full.png": ("scr_klayout_fb.png", (0, 26, 1917, 973)),
    "ngspice_chip_fb.png": ("scr_ngspice_chip_fb.png", (0, 31, 1426, 581)),
    "xschem_fb4.png": ("scr_xschem_fb4.png", (0, 37, 1320, 860)),
    "magic_fb4.png": ("scr_magic_fb4.png", (0, 38, 1430, 930)),
    "ngspice_fb4.png": ("scr_ngspice_fb4.png", (0, 26, 1917, 973)),
}


def screens():
    src = os.path.join(HERE, "screens")
    for name, (out, box) in SCREENS.items():
        path = os.path.join(src, name)
        if not os.path.isfile(path):
            print("missing", os.path.relpath(path, ROOT))
            continue
        im = Image.open(path).convert("RGB")
        box = (box[0], box[1], min(box[2], im.size[0]), min(box[3], im.size[1]))
        im.crop(box).save(os.path.join(OUT, out))
        print("wrote", os.path.relpath(os.path.join(OUT, out), ROOT), box)


def main():
    os.makedirs(OUT, exist_ok=True)
    screens()
    crop_header(os.path.join(FIG, "schematic_pl_fb4.png"), os.path.join(OUT, "schematic_fb4.png"), 250)
    crop_header(os.path.join(FIG, "schematic_pl_cs.png"), os.path.join(OUT, "schematic_cs.png"), 250)
    dst = os.path.join(OUT, "layout_fb4_plain.png")
    render_layout.render(os.path.join(ROOT, "mag", "pl_fb4.mag"), dst, legend=False)
    print("wrote", os.path.relpath(dst, ROOT))


if __name__ == "__main__":
    main()
