#!/usr/bin/env python3
"""Router blockers for a placed Qflow layout of the pl018 library (run by run.sh between
Qflow's place and route steps).

Reads the placed DEF (layout/alu4.def) and the cell blockers of
tech/pl018/pl018_blockers.json (routing-grid points next to signal-pin metal, see
gen_library.pin_blockers), places every blocker with its cell (position and orientation)
and adds them as obstructions to the router configuration (layout/alu4.cfg), ahead of its
read_def line. The LEF stays free of them, so Qflow's abstract-view LVS sees only the
cells' metal.

  python3 add_blockers.py <qflow layout directory> [design name, default alu4]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKERS = os.path.join(os.path.dirname(HERE), "tech", "pl018", "pl018_blockers.json")


def main():
    lay = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "alu4"
    blk = json.load(open(BLOCKERS))["cells"]
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "layout"))
    import find_shorts as F                     # DEF reader and orientation transforms
    text = open(os.path.join(lay, name + ".def")).read()
    sec = F.sections(F.def_tokens(text))
    k = sec["UNITS"]
    sizes = {}
    lef = F.Lef()
    lef.read(os.path.join(os.path.dirname(HERE), "tech", "pl018", "pl018_cells.lef"))
    for m, rec in lef.macros.items():
        sizes[m] = rec["size"]
    lines, cells = [], 0
    for st in sec.get("COMPONENTS", []):
        if st[0] != "-" or st[2] not in blk:
            continue
        for key in ("PLACED", "FIXED"):
            if key in st:
                j = st.index(key)
                x, y, orient = float(st[j + 2]) / k, float(st[j + 3]) / k, st[j + 5]
                break
        else:
            continue
        w, h = sizes[st[2]]
        tf = F.orient_tf(orient, x, y, w, h)
        cells += 1
        for layer, rects in blk[st[2]].items():
            for r in rects:
                x1, y1, x2, y2 = F.rect_tf(tf, r)
                lines.append("obstruction %.3f %.3f %.3f %.3f %s" % (x1, y1, x2, y2, layer))
    cfg = os.path.join(lay, name + ".cfg")
    old = open(cfg).read().splitlines()
    marker = "# router blockers next to signal-pin metal (step5_library/add_blockers.py)"
    if marker in old:                              # already added (rerun): replace
        i = old.index(marker)
        j = i + 1
        while j < len(old) and old[j].startswith("obstruction "):
            j += 1
        old = old[:i] + old[j:]
    at = next((i for i, l in enumerate(old) if l.strip().startswith("read_def")), len(old))
    new = old[:at] + [marker] + lines + old[at:]
    with open(cfg, "w") as f:
        f.write("\n".join(new) + "\n")
    print("add_blockers: %d obstructions for %d placed cells in %s" % (len(lines), cells, cfg))


if __name__ == "__main__":
    main()
