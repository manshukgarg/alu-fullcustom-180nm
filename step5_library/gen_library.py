#!/usr/bin/env python3
"""Generate the project cell library for automatic place and route (Step 5).

Runs outside the lab (the layout generator needs numpy); the lab verifies the
cells and characterizes them.

Every cell of step5_library/library.json is laid out by layout/cellgen.py in grid
mode (width in 0.8 um placement sites, pin pads centred on routing-track
crossings), checked with the project's rule checker and extractor, and written
as mag/<name>.mag. The geometry of every net is kept in
step5_library/build/<name>.json, from which the library views are written:
    tech/pl018/pl018_cells.lef   OSU018 technology section, the 0.8 x 8.0 um site, cell macros
    tech/pl018/pl018_cells.sp    transistor netlists, devices as laid out (LVS and simulation)
    tech/pl018/pl018_cells.v     Verilog models (gate-level simulation)
    step5_library/cells.json     pins, functions, truth tables and sizes (lab scripts)

Usage:  python3 step5_library/gen_library.py [--only name,name] [--views] [--preview] [--jobs N]
        --views rewrites the views from the cached geometry without new layouts;
        --preview renders docs/figures/cells/<name>.png with the routing-track crossings.
"""
import argparse
import itertools
import json
import multiprocessing as mp
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "layout"))
sys.path.insert(0, os.path.join(ROOT, "step3_cells"))
sys.path.insert(0, HERE)

import logic  # noqa: E402

TECHDIR = os.path.join(ROOT, "tech", "pl018")
BUILD = os.path.join(HERE, "build")
M1_LAYERS = {"m1", "ndc", "pdc", "pc", "psc", "nsc", "m2c"}
M2_LAYERS = {"m2", "m2c"}
DIFF_UM = 0.5            # diffusion length of the junction estimates, as in step3_cells/cellnet.py
H = 80                   # cell height in lambda (layout/template.py)
SITE_NAME = "plcore"


def truth_tables(cell):
    tabs = {o: [] for o in cell.outputs}
    for bits in itertools.product((0, 1), repeat=len(cell.inputs)):
        out = cell.func(dict(zip(cell.inputs, bits)))
        for o in cell.outputs:
            tabs[o].append(int(out[o]))
    return tabs


def build(job):
    family, spec = job
    import library
    t0 = time.time()
    try:
        cell, b = library.make_cell(spec["cell"], spec["k"], spec["r"], name=spec["name"], grid=True)
        L = b.build()
    except Exception as exc:                      # routing or plan failure
        return {"name": spec["name"], "failed": str(exc), "seconds": round(time.time() - t0, 1)}
    errors, problems, ndev = b.verify(L)
    L.write(os.path.join(ROOT, "mag", spec["name"] + ".mag"))
    geo = {"name": spec["name"], "family": family, "cell": spec["cell"], "k": spec["k"],
           "r": spec["r"], "provisional": bool(spec.get("provisional")),
           "width_lambda": b.width, "height_lambda": H,
           "inputs": cell.inputs, "outputs": cell.outputs, "transistors": cell.count,
           "truth": truth_tables(cell), "fingers": [list(f) for f in b.fingers],
           "pads": {p: list(v) for p, v in b.pads.items()},
           "shapes": [list(s_) for s_ in b.all_shapes() if s_[0] in M1_LAYERS | M2_LAYERS],
           "drc_errors": errors, "lvs_problems": problems, "devices_drawn": ndev,
           "seconds": round(time.time() - t0, 1)}
    with open(os.path.join(BUILD, spec["name"] + ".json"), "w") as f:
        json.dump(geo, f)
    return geo


def build_fill(spec):
    import library
    L, shapes = library.fill_cell(spec["name"], spec.get("sites", 1))
    L.write(os.path.join(ROOT, "mag", spec["name"] + ".mag"))
    w = L.bbox[2] - L.bbox[0]
    geo = {"name": spec["name"], "family": "FILL", "cell": None, "width_lambda": w,
           "height_lambda": H, "inputs": [], "outputs": [], "transistors": 0, "truth": {},
           "fingers": [], "pads": {}, "shapes": [list(s_) for s_ in shapes],
           "drc_errors": [], "lvs_problems": [], "provisional": False}
    with open(os.path.join(BUILD, spec["name"] + ".json"), "w") as f:
        json.dump(geo, f)
    return geo


# ----------------------------------------------------------------------------
# views
# ----------------------------------------------------------------------------
def rect_cover(boxes):
    """Exact cover of the union of (x1, y1, x2, y2) boxes by rectangles (lambda grid)."""
    filled = set()
    for x1, y1, x2, y2 in boxes:
        for x in range(min(x1, x2), max(x1, x2)):
            for y in range(min(y1, y2), max(y1, y2)):
                filled.add((x, y))
    rows = {}
    for x, y in filled:
        rows.setdefault(y, []).append(x)
    runs = {}
    for y, xs in rows.items():
        xs.sort()
        out, s0, p = [], xs[0], xs[0]
        for x in xs[1:]:
            if x == p + 1:
                p = x
            else:
                out.append((s0, p + 1))
                s0 = p = x
        out.append((s0, p + 1))
        runs[y] = out
    result, active, prev = [], {}, None
    for y in sorted(runs):
        cur = set(runs[y])
        contiguous = prev is not None and y == prev + 1
        for key in list(active):
            if not contiguous or key not in cur:
                result.append((key[0], active.pop(key), key[1], prev + 1))
        for key in cur:
            if key not in active:
                active[key] = y
        prev = y
    for key, y0 in active.items():
        result.append((key[0], y0, key[1], prev + 1))
    return sorted(result, key=lambda r: (r[1], r[0]))


def um(v):
    return "%.3f" % (v / 10.0)


def lef_rects(rects, indent):
    return ["%sRECT %s %s %s %s ;" % (indent, um(x1), um(y1), um(x2), um(y2)) for x1, y1, x2, y2 in rects]


def base(net):
    return net.split("#")[0] if net else net


def lef_macro(g):
    by = {}
    for layer, x1, y1, x2, y2, net in g["shapes"]:
        n = base(net) or "-"
        if layer in M1_LAYERS:
            by.setdefault((n, "metal1"), []).append((x1, y1, x2, y2))
        if layer in M2_LAYERS:
            by.setdefault((n, "metal2"), []).append((x1, y1, x2, y2))
    pins = g["inputs"] + g["outputs"]
    L = ["MACRO %s" % g["name"], "  CLASS CORE ;", "  FOREIGN %s 0.000 0.000 ;" % g["name"],
         "  ORIGIN 0.000 0.000 ;", "  SIZE %s BY %s ;" % (um(g["width_lambda"]), um(g["height_lambda"])),
         "  SYMMETRY X Y ;", "  SITE %s ;" % SITE_NAME]
    for p in pins + ["vdd", "gnd"]:
        L.append("  PIN %s" % p)
        if p in g["inputs"]:
            L.append("    DIRECTION INPUT ;")
        elif p in g["outputs"]:
            L.append("    DIRECTION OUTPUT ;")
        else:
            L += ["    DIRECTION INOUT ;", "    USE %s ;" % ("POWER" if p == "vdd" else "GROUND"),
                  "    SHAPE ABUTMENT ;"]
        L.append("    PORT")
        pad = g["pads"].get(p)
        for layer in ("metal1", "metal2"):
            boxes = by.get((p, layer))
            if boxes:
                L.append("      LAYER %s ;" % layer)
                # the access pad first and whole (centred on a track crossing), then the net
                if pad and {"m1": "metal1", "m2": "metal2"}[pad[0]] == layer:
                    L += lef_rects([tuple(pad[1:5])], "        ")
                L += lef_rects(rect_cover(boxes), "        ")
        L += ["    END", "  END %s" % p]
    obs = []
    for layer in ("metal1", "metal2"):
        boxes = [b for (n, ly), bs in by.items() if ly == layer and n not in pins + ["vdd", "gnd"]
                 for b in bs]
        if boxes:
            obs.append("    LAYER %s ;" % layer)
            obs += lef_rects(rect_cover(boxes), "      ")
    if obs:
        L += ["  OBS"] + obs + ["  END"]
    L.append("END %s" % g["name"])
    return L


def write_lef(cells, path):
    head = [l for l in open(os.path.join(HERE, "lef_tech_osu018.txt")).read().splitlines()]
    L = ["# LEF of the project cell library pl018 (generated by step5_library/gen_library.py)"]
    L += head
    L += ["", "SITE  %s" % SITE_NAME, "    CLASS\tCORE ;", "    SYMMETRY\tY ;",
          "    SIZE\t0.800 BY %s ;" % um(H), "END  %s" % SITE_NAME, ""]
    for g in cells:
        L += lef_macro(g) + [""]
    L.append("END LIBRARY")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def write_spice(cells, path):
    L = ["* Transistor netlists of the project cell library pl018, devices as laid out",
         "* (generated by step5_library/gen_library.py; junctions estimated for a %.1f um diffusion)"
         % DIFF_UM]
    for g in cells:
        pins = g["inputs"] + g["outputs"] + ["vdd", "gnd"]
        L.append(".subckt %s %s" % (g["name"], " ".join(pins)))
        for i, (model, d, gate, s, w) in enumerate(g["fingers"]):
            wu = w / 10.0
            body = "gnd" if model == "nfet" else "vdd"
            ad, pd = wu * DIFF_UM, 2 * (wu + DIFF_UM)
            L.append("M%d %s %s %s %s %s w=%gu l=0.2u ad=%.4gp as=%.4gp pd=%.4gu ps=%.4gu"
                     % (i, d, gate, s, body, model, wu, ad, ad, pd, pd))
        L.append(".ends %s" % g["name"])
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def write_verilog(cells, path):
    L = ["// Verilog models of the project cell library pl018 (generated by step5_library/gen_library.py)",
         "`timescale 1ns/10ps"]
    for g in cells:
        if not g["outputs"]:
            continue
        ports = g["inputs"] + g["outputs"]
        L.append("module %s (%s);" % (g["name"], ", ".join(ports)))
        L.append("    input %s;" % ", ".join(g["inputs"]))
        L.append("    output %s;" % ", ".join(g["outputs"]))
        for o in g["outputs"]:
            L.append("    assign %s = %s;" % (o, logic.expression(g["truth"][o], g["inputs"], "verilog")))
        L.append("endmodule")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def write_index(cells, lib, path):
    out = []
    for g in cells:
        funcs, vfuncs = {}, {}
        for o in g["outputs"]:
            funcs[o] = logic.expression(g["truth"][o], g["inputs"], "liberty")
            vfuncs[o] = logic.expression(g["truth"][o], g["inputs"], "verilog")
            assert logic.check(g["truth"][o], g["inputs"], funcs[o], "liberty"), (g["name"], o)
        w, h = g["width_lambda"] / 10.0, g["height_lambda"] / 10.0
        out.append({"name": g["name"], "family": g["family"], "cell": g["cell"], "k": g.get("k"),
                    "r": g.get("r"), "provisional": g.get("provisional", False),
                    "inputs": g["inputs"], "outputs": g["outputs"], "transistors": g["transistors"],
                    "truth": g["truth"], "function": funcs, "verilog": vfuncs,
                    "width_um": w, "height_um": h, "area_um2": round(w * h, 2),
                    "pads_um": {p: [v[0]] + [c / 10.0 for c in v[1:]] for p, v in g["pads"].items()}})
    with open(path, "w") as f:
        json.dump({"library": lib["name"], "note": "generated by step5_library/gen_library.py",
                   "site_um": lib["site_um"], "cells": out}, f, indent=1)


def write_views(lib):
    order = [spec["name"] for spec in lib["cells"].values()] + [lib["fill"]["name"]]
    cells = []
    for name in order:
        p = os.path.join(BUILD, name + ".json")
        if not os.path.exists(p):
            print("no geometry for %s (lay it out first)" % name)
            continue
        cells.append(json.load(open(p)))
    os.makedirs(TECHDIR, exist_ok=True)
    write_lef(cells, os.path.join(TECHDIR, "pl018_cells.lef"))
    write_spice(cells, os.path.join(TECHDIR, "pl018_cells.sp"))
    write_verilog(cells, os.path.join(TECHDIR, "pl018_cells.v"))
    write_index(cells, lib, os.path.join(HERE, "cells.json"))
    print("views written for %d cells: %s" % (len(cells), ", ".join(c["name"] for c in cells)))


def previews(lib):
    """docs/figures/cells/<name>.png from the Magic files, routing-track crossings marked."""
    import re
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import preview
    import verify_mag
    out = os.path.join(ROOT, "docs", "figures", "cells")
    os.makedirs(out, exist_ok=True)
    names = [spec["name"] for spec in lib["cells"].values()]
    real_savefig = plt.Figure.savefig

    def savefig(fig, path, **kw):            # add the track crossings before saving
        ax = fig.axes[0]
        x1, x2 = ax.get_xlim()
        xs = [x for x in range(4, int(x2), 8) if x >= x1]
        ys = [y for y in range(5, 80, 10)]
        ax.scatter([x for x in xs for _ in ys], [y for _ in xs for y in ys], s=4, c="black",
                   marker="+", linewidths=0.5, zorder=12)
        real_savefig(fig, path, **kw)
    plt.Figure.savefig = savefig
    try:
        for name in names:
            path = os.path.join(ROOT, "mag", name + ".mag")
            L = verify_mag.read_mag(path)
            L.name = name
            m = re.search(r"FIXED_BBOX (-?\d+) (-?\d+) (-?\d+) (-?\d+)", open(path).read())
            if m:
                L.bbox = tuple(int(v) for v in m.groups())
            preview.render(L, os.path.join(out, name + ".png"), scale=0.12)
    finally:
        plt.Figure.savefig = real_savefig
    print("previews: %s (+ marks routing-track crossings)" % ", ".join(names))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--views", action="store_true", help="only rewrite the views from build/")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--preview", action="store_true", help="also render docs/figures/cells/*.png")
    args = ap.parse_args()
    lib = json.load(open(os.path.join(HERE, "library.json")))
    os.makedirs(BUILD, exist_ok=True)
    if not args.views:
        only = [s for s in args.only.split(",") if s]
        jobs = [(fam, spec) for fam, spec in lib["cells"].items() if not only or spec["name"] in only]
        import library
        jobs.sort(key=lambda j: -len(library.PLANS[j[1]["cell"]]))      # slowest first
        bad = []
        with mp.Pool(max(1, min(args.jobs, len(jobs)))) as pool:
            for r in pool.imap_unordered(build, jobs):
                if "failed" in r:
                    print("%-9s FAILED after %.0f s: %s" % (r["name"], r["seconds"], r["failed"]), flush=True)
                    bad.append(r["name"])
                    continue
                ok = "clean" if not r["drc_errors"] and not r["lvs_problems"] else "PROBLEM"
                if ok != "clean":
                    bad.append(r["name"])
                print("%-9s %5.1f x %.1f um (%2d sites)  %2d T  %6.1f s  %s %s" % (
                    r["name"], r["width_lambda"] / 10.0, H / 10.0, r["width_lambda"] // 8,
                    r["transistors"], r["seconds"], ok, (r["drc_errors"] + r["lvs_problems"])[:3]),
                    flush=True)
        if not only or lib["fill"]["name"] in only:
            build_fill(lib["fill"])
        if bad:
            print("cells with problems:", ", ".join(bad))
    write_views(lib)
    if args.preview:
        previews(lib)


if __name__ == "__main__":
    main()
