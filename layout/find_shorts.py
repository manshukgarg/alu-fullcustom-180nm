#!/usr/bin/env python3
"""Shorts and spacing faults of a routed Qflow layout, located from its DEF and LEF files.

Rebuilds the layout from the routed DEF (Qflow moves the router output to
layout/alu4.def) and the abstract views of the cells (LEF pins and obstructions):
every wire with its layer width and half-width end extensions, every via, every
I/O pin and every cell pin and obstruction. Shapes on the same layer that overlap
or touch along an edge are connected in the real layout, so

  * two shapes of different nets that touch       -> short (the nets are merged),
  * a wire on a cell obstruction (internal metal)  -> short with an internal net,
  * shapes of different nets closer than the
    layer spacing                                  -> spacing fault (Magic DRC error).

Pins, obstructions and abutment of the cells themselves are not reported (checked
by the cell DRC/LVS and layout/abut_check.py).

Usage (from the repository root, in the lab after a run of Step 5 or Step 2):
  python3 layout/find_shorts.py                    all designs of Steps 5 and 2 found
  python3 layout/find_shorts.py beh slice osu-map  selected designs
  python3 layout/find_shorts.py --def F.def --lef A.lef [--lef B.lef]
"""
import argparse
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OSU_LEF = "/apps/vlsi/share/qflow/tech/osu018/osu018_stdcells.lef"
POWER_NAMES = {"vdd", "gnd", "vss", "vcc", "vdd!", "gnd!"}


# ---------------------------------------------------------------------- LEF
class Lef:
    def __init__(self):
        self.width, self.spacing, self.routing = {}, {}, set()
        self.vias = {}        # name -> [(layer, x1, y1, x2, y2)] in microns
        self.macros = {}      # name -> dict(size, origin, pins {name: [(layer, rect)]}, use {}, obs [])

    def read(self, path):
        lines = open(path, errors="replace").read().splitlines()
        i, n = 0, len(lines)
        while i < n:
            t = lines[i].split()
            if not t or t[0].startswith("#"):
                i += 1
                continue
            if t[0] == "LAYER" and len(t) > 1:
                name = t[1]
                i += 1
                while i < n and not re.match(r"\s*END\s+%s\s*$" % re.escape(name), lines[i]):
                    u = lines[i].replace(";", " ").split()
                    if u[:1] == ["WIDTH"]:
                        self.width[name] = float(u[1])
                    elif u[:1] == ["SPACING"] and name not in self.spacing:
                        self.spacing[name] = float(u[1])
                    elif u[:2] == ["TYPE", "ROUTING"]:
                        self.routing.add(name)
                    i += 1
            elif t[0] == "VIA" and len(t) > 1:
                name, layer, rects = t[1], None, []
                i += 1
                while i < n and not re.match(r"\s*END\s+%s\s*$" % re.escape(name), lines[i]):
                    u = lines[i].replace(";", " ").split()
                    if u[:1] == ["LAYER"]:
                        layer = u[1]
                    elif u[:1] == ["RECT"]:
                        rects.append((layer,) + tuple(float(v) for v in u[1:5]))
                    i += 1
                self.vias[name] = rects
            elif t[0] == "VIARULE":
                name = t[1]
                i += 1
                while i < n and not re.match(r"\s*END\s+%s\s*$" % re.escape(name), lines[i]):
                    i += 1
            elif t[0] == "MACRO" and len(t) > 1:
                i = self._macro(lines, i, t[1])
            i += 1

    def _macro(self, lines, i, name):
        m = {"size": (0.0, 0.0), "origin": (0.0, 0.0), "pins": defaultdict(list), "use": {}, "obs": []}
        i += 1
        n = len(lines)
        while i < n and not re.match(r"\s*END\s+%s\s*$" % re.escape(name), lines[i]):
            u = lines[i].replace(";", " ").split()
            if u[:1] == ["SIZE"]:
                m["size"] = (float(u[1]), float(u[3]))
            elif u[:1] == ["ORIGIN"]:
                m["origin"] = (float(u[1]), float(u[2]))
            elif u[:1] == ["PIN"]:
                pin, layer = u[1], None
                i += 1
                while i < n and not re.match(r"\s*END\s+%s\s*$" % re.escape(pin), lines[i]):
                    v = lines[i].replace(";", " ").split()
                    if v[:1] == ["USE"]:
                        m["use"][pin] = v[1].upper()
                    elif v[:1] == ["LAYER"]:
                        layer = v[1]
                    elif v[:1] == ["RECT"]:
                        vals = [x for x in v[1:] if x != "MASK"]
                        m["pins"][pin].append((layer,) + tuple(float(x) for x in vals[-4:]))
                    i += 1
            elif u[:1] == ["OBS"]:
                layer = None
                i += 1
                while i < n and lines[i].split()[:1] != ["END"]:
                    v = lines[i].replace(";", " ").split()
                    if v[:1] == ["LAYER"]:
                        layer = v[1]
                    elif v[:1] == ["RECT"]:
                        vals = [x for x in v[1:] if x != "MASK"]
                        m["obs"].append((layer,) + tuple(float(x) for x in vals[-4:]))
                    i += 1
            i += 1
        self.macros[name] = m
        return i


# ---------------------------------------------------------------------- DEF
def def_tokens(text):
    text = re.sub(r"#[^\n]*", " ", text)
    return text.replace("(", " ( ").replace(")", " ) ").replace(";", " ; ").split()


def sections(tokens):
    """{section name: list of statements (token lists)} for VIAS, COMPONENTS, PINS, NETS,
    SPECIALNETS; plus UNITS and DIEAREA."""
    out = {"UNITS": 100.0, "DIEAREA": None}
    i, n = 0, len(tokens)
    while i < n:
        t = tokens[i]
        if t == "UNITS" and tokens[i + 1:i + 3] == ["DISTANCE", "MICRONS"]:
            out["UNITS"] = float(tokens[i + 3])
            i += 4
        elif t == "DIEAREA":
            j = tokens.index(";", i)
            nums = [float(x) for x in tokens[i + 1:j] if x not in "()"]
            out["DIEAREA"] = nums[:4]
            i = j + 1
        elif t in ("VIAS", "COMPONENTS", "PINS", "NETS", "SPECIALNETS") and i + 2 < n and tokens[i + 2] == ";":
            j = i + 3
            stmts, cur = [], []
            while j < n and not (tokens[j] == "END" and j + 1 < n and tokens[j + 1] == t):
                if tokens[j] == ";":
                    if cur:
                        stmts.append(cur)
                    cur = []
                else:
                    cur.append(tokens[j])
                j += 1
            out[t] = stmts
            i = j + 2
        else:
            i += 1
    return out


def orient_tf(orient, x, y, w, h):
    if orient == "N":
        return lambda px, py: (x + px, y + py)
    if orient == "S":
        return lambda px, py: (x + w - px, y + h - py)
    if orient == "FN":
        return lambda px, py: (x + w - px, y + py)
    if orient == "FS":
        return lambda px, py: (x + px, y + h - py)
    if orient == "W":
        return lambda px, py: (x + h - py, y + px)
    if orient == "E":
        return lambda px, py: (x + py, y + w - px)
    if orient == "FW":
        return lambda px, py: (x + h - py, y + w - px)
    if orient == "FE":
        return lambda px, py: (x + py, y + px)
    raise ValueError("orientation %s" % orient)


def rect_tf(tf, r):
    (ax, ay), (bx, by) = tf(r[0], r[1]), tf(r[2], r[3])
    return (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))


class Shape:
    __slots__ = ("layer", "x1", "y1", "x2", "y2", "net", "what", "inst")

    def __init__(self, layer, r, net, what, inst=None):
        self.layer, (self.x1, self.y1, self.x2, self.y2) = layer, r
        self.net, self.what, self.inst = net, what, inst


def build(def_path, lef):
    sec = sections(def_tokens(open(def_path, errors="replace").read()))
    k = sec["UNITS"]
    shapes, notes = [], []
    vias = {name: list(rects) for name, rects in lef.vias.items()}
    for st in sec.get("VIAS", []):                 # generated vias: - name + RECT layer ( ) ( ) ...
        if st[0] != "-":
            continue
        rects, j = [], 2
        while j < len(st):
            if st[j] == "RECT":
                vals = [float(v) / k for v in st[j + 2:j + 10] if v not in "()"][:4]
                rects.append((st[j + 1],) + tuple(vals))
                j += 8
            j += 1
        vias[st[1]] = rects
    # nets of the component pins
    pin_net = {}
    for st in sec.get("NETS", []):
        if st[0] != "-":
            continue
        net = st[1]
        j = 2
        while j < len(st) and st[j] != "+":
            if st[j] == "(" and j + 3 < len(st) and st[j + 3] == ")":
                pin_net[(st[j + 1], st[j + 2])] = net
                j += 4
            else:
                j += 1
    comps = {}
    for st in sec.get("COMPONENTS", []):
        if st[0] != "-":
            continue
        inst, macro = st[1], st[2]
        for key in ("PLACED", "FIXED", "COVER"):
            if key in st:
                j = st.index(key)
                x, y, orient = float(st[j + 2]) / k, float(st[j + 3]) / k, st[j + 5]
                break
        else:
            continue
        m = lef.macros.get(macro)
        if m is None:
            notes.append("macro %s of %s not in the LEF" % (macro, inst))
            continue
        comps[inst] = macro
        w, h = m["size"]
        ox, oy = m["origin"]
        tf = orient_tf(orient, x, y, w, h)
        for pin, rects in m["pins"].items():
            use = m["use"].get(pin, "")
            if use in ("POWER", "GROUND") or pin.lower() in POWER_NAMES:
                net = "gnd" if use == "GROUND" or pin.lower().startswith(("gnd", "vss")) else "vdd"
            else:
                net = pin_net.get((inst, pin), "%s/%s (unconnected)" % (inst, pin))
            for layer, x1, y1, x2, y2 in rects:
                shapes.append(Shape(layer, rect_tf(tf, (x1 + ox, y1 + oy, x2 + ox, y2 + oy)), net,
                                    "pin %s of %s (%s)" % (pin, inst, macro), inst))
        for layer, x1, y1, x2, y2 in m["obs"]:
            shapes.append(Shape(layer, rect_tf(tf, (x1 + ox, y1 + oy, x2 + ox, y2 + oy)), "OBS " + inst,
                                "obstruction of %s (%s)" % (inst, macro), inst))
    # I/O pins
    for st in sec.get("PINS", []):
        if st[0] != "-":
            continue
        name = st[1]
        net = st[st.index("NET") + 1] if "NET" in st else name
        layer = rect = place = None
        j = 2
        while j < len(st):
            if st[j] == "LAYER":
                nums = [float(v) / k for v in st[j + 2:j + 10] if v not in "()"][:4]
                layer, rect = st[j + 1], nums
                j += 8
            elif st[j] in ("PLACED", "FIXED"):
                place = (float(st[j + 2]) / k, float(st[j + 3]) / k, st[j + 5])
                j += 6
            j += 1
        if layer and rect and place:
            rel = {"N": lambda px, py: (px, py), "S": lambda px, py: (-px, -py),
                   "W": lambda px, py: (-py, px), "E": lambda px, py: (py, -px),
                   "FN": lambda px, py: (-px, py), "FS": lambda px, py: (px, -py),
                   "FW": lambda px, py: (-py, -px), "FE": lambda px, py: (py, px)}[place[2]]
            (ax, ay), (bx, by) = rel(rect[0], rect[1]), rel(rect[2], rect[3])
            r = (place[0] + min(ax, bx), place[1] + min(ay, by), place[0] + max(ax, bx), place[1] + max(ay, by))
            shapes.append(Shape(layer, r, net, "I/O pin %s" % name))
    # wiring
    nroute = 0
    for kind in ("NETS", "SPECIALNETS"):
        for st in sec.get(kind, []):
            if st[0] != "-":
                continue
            net = st[1]
            j = 2
            while j < len(st):
                if st[j] in ("ROUTED", "FIXED", "COVER", "NOSHIELD") or st[j] == "NEW":
                    j, added = wire(st, j + 1, net, kind == "SPECIALNETS", lef, vias, k, shapes, notes)
                    nroute += added
                else:
                    j += 1
    return shapes, comps, nroute, notes


def wire(st, j, net, special, lef, vias, k, shapes, notes):
    """Parse one path (layer [width] points and vias) starting at st[j]; return the next index."""
    layer = st[j]
    j += 1
    width = None
    if special and j < len(st) and re.match(r"^\d+$", st[j]):
        width = float(st[j]) / k
        j += 1
    while j < len(st) and st[j] in ("TAPER", "STYLE", "TAPERRULE", "SHAPE", "MASK"):
        j += 2 if st[j] != "TAPER" else 1
    w = width if width is not None else lef.width.get(layer, 0.3)
    ext = 0.0 if special else w / 2
    last, added = None, 0
    while j < len(st) and st[j] not in ("NEW", "+"):
        if st[j] == "(":
            e = st.index(")", j)
            vals = st[j + 1:e]
            x = last[0] if vals[0] == "*" else float(vals[0]) / k
            y = last[1] if vals[1] == "*" else float(vals[1]) / k
            if last is not None and (x, y) != last:
                x1, x2 = sorted((last[0], x))
                y1, y2 = sorted((last[1], y))
                if y1 == y2:
                    r = (x1 - ext, y1 - w / 2, x2 + ext, y1 + w / 2)
                else:
                    r = (x1 - w / 2, y1 - ext, x1 + w / 2, y2 + ext)
                shapes.append(Shape(layer, r, net, "wire of %s" % net))
                added += 1
            last = (x, y)
            j = e + 1
        elif st[j] == "RECT":
            j += 6
        elif st[j] == "VIRTUAL":
            j += 4
        else:
            name = st[j]
            if last is not None and name in vias:
                for lay, x1, y1, x2, y2 in vias[name]:
                    shapes.append(Shape(lay, (last[0] + x1, last[1] + y1, last[0] + x2, last[1] + y2), net,
                                        "via %s of %s" % (name, net)))
                added += 1
                # a path continues on the other metal layer of the via
                metals = [r[0] for r in vias[name] if r[0] in lef.routing]
                if layer in metals and len(metals) == 2:
                    layer = metals[1] if metals[0] == layer else metals[0]
                    w = lef.width.get(layer, w) if width is None else w
                    ext = 0.0 if special else w / 2
            elif last is not None:
                notes.append("unknown via or keyword %s in net %s" % (name, net))
            j += 1
    return j, added


# ---------------------------------------------------------------------- checks
def touching(a, b, eps=1e-6):
    """'overlap' / 'edge' (touch along an edge) / None."""
    ox = min(a.x2, b.x2) - max(a.x1, b.x1)
    oy = min(a.y2, b.y2) - max(a.y1, b.y1)
    if ox > eps and oy > eps:
        return "overlap"
    if (abs(ox) <= eps and oy > eps) or (abs(oy) <= eps and ox > eps):
        return "edge"
    return None


def distance(a, b):
    dx = max(a.x1 - b.x2, b.x1 - a.x2, 0.0)
    dy = max(a.y1 - b.y2, b.y1 - a.y2, 0.0)
    return (dx * dx + dy * dy) ** 0.5


def check(shapes, lef):
    shorts, spacing = [], []
    by_layer = defaultdict(list)
    for s in shapes:
        by_layer[s.layer].append(s)
    for layer, lst in by_layer.items():
        sp = lef.spacing.get(layer, 0.0)
        lst.sort(key=lambda s: s.x1)
        active = []
        for s in lst:
            active = [a for a in active if a.x2 + sp >= s.x1 - 1e-9]
            for a in active:
                if a.net == s.net:
                    continue
                if a.inst is not None and a.inst == s.inst:
                    continue                    # inside one cell: cell DRC/LVS
                if a.inst is not None and s.inst is not None:
                    continue                    # two cells: abutment, layout/abut_check.py
                t = touching(a, s)
                if t:
                    shorts.append((layer, a, s, t))
                elif layer in lef.routing and sp > 0 and distance(a, s) < sp - 1e-6:
                    spacing.append((layer, a, s, distance(a, s)))
            active.append(s)
    return shorts, spacing


def where(a, b):
    x = (max(a.x1, b.x1) + min(a.x2, b.x2)) / 2
    y = (max(a.y1, b.y1) + min(a.y2, b.y2)) / 2
    return "(%.2f, %.2f)" % (x, y)


def report(label, def_path, lefs):
    lef = Lef()
    for p in lefs:
        lef.read(p)
    shapes, comps, nroute, notes = build(def_path, lef)
    shorts, spacing = check(shapes, lef)
    nets = {s.net for s in shapes if not s.net.startswith("OBS ")}
    print("%s: %s" % (label, os.path.relpath(def_path, ROOT) if def_path.startswith(ROOT) else def_path))
    print("  %d cells, %d nets, %d wires and vias" % (len(comps), len(nets), nroute))
    for n in sorted(set(notes))[:5]:
        print("  note: " + n)
    if not shorts:
        print("  no shorts")
    groups = defaultdict(list)
    for layer, a, b, t in shorts:
        key = tuple(sorted((a.net, b.net)))
        groups[key].append((layer, a, b, t))
    items = sorted(groups.items())
    for (n1, n2), lst in items[:6]:
        kind = "short with a cell's internal metal" if n1.startswith("OBS ") or n2.startswith("OBS ") \
            else "short between nets"
        print("  %s %s / %s: %d place%s" % (kind, n1, n2, len(lst), "" if len(lst) == 1 else "s"))
        for layer, a, b, t in lst[:2]:
            print("    %s %s at %s um: %s / %s" % (layer, t, where(a, b), a.what, b.what))
    if len(items) > 6:
        print("  ... %d more pairs of shorted nets" % (len(items) - 6))
    if spacing:
        cnt = defaultdict(int)
        for layer, a, b, d in spacing:
            cnt[layer] += 1
        print("  spacing below the rule between different nets: %s" % ", ".join(
            "%s %d" % kv for kv in sorted(cnt.items())))
        for layer, a, b, d in spacing[:4]:
            print("    %s %.2f um at %s: %s / %s" % (layer, d, where(a, b), a.what, b.what))
    return len(shorts), len(spacing)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("designs", nargs="*")
    ap.add_argument("--def", dest="def_path")
    ap.add_argument("--lef", action="append", default=[])
    args = ap.parse_args()
    if args.def_path:
        report("design", args.def_path, args.lef)
        return
    designs = args.designs or ["beh", "slice", "map", "fb", "osu-beh", "osu-slice", "osu-map"]
    found = 0
    for d in designs:
        if d.startswith("osu-"):
            q, lefs = os.path.join(ROOT, "step2_rtl_baseline", "qflow_" + d[4:]), [OSU_LEF]
        else:
            q, lefs = os.path.join(ROOT, "step5_library", "qflow_" + d), \
                [os.path.join(ROOT, "tech", "pl018", "pl018_cells.lef")]
        path = os.path.join(q, "layout", "alu4.def")
        if not os.path.isfile(path):
            if args.designs:
                print("%s: %s not found" % (d, os.path.relpath(path, ROOT)))
            continue
        found += 1
        report(d, path, lefs)
    if not found:
        print("no routed layouts found (run Step 5 or Step 2 first)")


if __name__ == "__main__":
    main()
