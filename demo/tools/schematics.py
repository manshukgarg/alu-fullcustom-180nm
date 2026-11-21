#!/usr/bin/env python3
"""Xschem schematics of the two ALU-specific cells: demo/xschem/pl_fb4.sch and pl_cs.sch.

The drawings are described below (device positions, wires and labels). Before a file is
written, its connectivity is extracted the way Xschem forms nets (wire end points, pins at
the same point, labels of the same name) and every device is compared with the cell
netlist tech/pl018/pl018_cells.sp, the netlist the cell layouts are checked against
(type, gate, drain and source, body, W and L). In the lab, demo/show.sh netlists the
schematics with Xschem and compares them with the layout extraction (Netgen).

  python3 demo/tools/schematics.py        write and check both schematics
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
XDIR = os.path.join(ROOT, "demo", "xschem")
CELLS_SP = os.path.join(ROOT, "tech", "pl018", "pl018_cells.sp")

# pin positions of the symbols used (symbol coordinates; y grows downwards as in Xschem)
PINS = {
    "pl018_nfet.sym": [("d", 20, -30), ("g", -20, 0), ("s", 20, 30)],
    "pl018_pfet.sym": [("d", 20, 30), ("g", -20, 0), ("s", 20, -30)],
    "pl018_nfet_h.sym": [("d", -30, 0), ("g", 0, 40), ("s", 30, 0)],
    "pl018_pfet_h.sym": [("d", -30, 0), ("g", 0, -40), ("s", 30, 0)],
}
LABELS = ("lab_pin.sym", "pl018_label.sym", "ipin.sym", "opin.sym", "iopin.sym", "vdd.sym", "gnd.sym")
for _s in LABELS:
    PINS[_s] = [("p", 0, 0)]


def transform(px, py, x, y, rot, flip):
    """Absolute position of symbol point (px, py) for an instance at (x, y) (Xschem ROTATION)."""
    if flip:
        px = -px
    if rot == 1:
        px, py = -py, px
    elif rot == 2:
        px, py = -px, -py
    elif rot == 3:
        px, py = py, -px
    return (x + px, y + py)


class Drawing:
    def __init__(self, name, title, lines):
        self.name, self.title, self.lines = name, title, lines
        self.inst, self.segs, self.counts = [], [], {}

    def place(self, sym, x, y, rot=0, flip=0, **props):
        if "name" not in props:
            prefix = {"ipin.sym": "p", "opin.sym": "p", "iopin.sym": "p"}.get(sym, "l")
            self.counts[prefix] = self.counts.get(prefix, 0) + 1
            props = dict(name="%s%d" % (prefix, self.counts[prefix]), **props)
        self.inst.append((sym, x, y, rot, flip, props))
        return {p: transform(px, py, x, y, rot, flip) for p, px, py in PINS[sym]}

    def wire(self, *pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if x1 != x2 and y1 != y2:
                raise ValueError("%s: diagonal wire %s" % (self.name, ((x1, y1), (x2, y2))))
            self.segs.append((x1, y1, x2, y2))

    def label(self, lab, x, y, right=False):
        """Net label at a wire end: text left of the point, or right of it (right=True)."""
        self.place("lab_pin.sym", x, y, 0, 1 if right else 0, lab=lab)

    def wire_label(self, lab, x, y):
        """Net label on a wire: text above the wire, ending at the point."""
        self.place("pl018_label.sym", x, y, lab=lab)

    def port(self, kind, lab, x, y):
        self.place(kind + ".sym", x, y, lab=lab)

    def tg(self, x, y, nname, pname, ngate, pgate, wn, wp):
        """Transmission gate: pfet above, nfet below, terminals at (x -/+ 30, y)."""
        self.place("pl018_pfet_h.sym", x, y, name=pname, model="pfet", body="vdd", w=wp, l="0.2u", m=1)
        self.place("pl018_nfet_h.sym", x, y, name=nname, model="nfet", body="gnd", w=wn, l="0.2u", m=1)
        self.label(pgate, x, y - 40)
        self.label(ngate, x, y + 40)
        return (x - 30, y), (x + 30, y)

    def inverter(self, gx, gy, nname, pname, wn, wp):
        """Static CMOS inverter with its input junction at (gx, gy); returns the output point."""
        p = self.place("pl018_pfet.sym", gx + 20, gy - 40, name=pname, model="pfet", body="vdd",
                       w=wp, l="0.2u", m=1)
        n = self.place("pl018_nfet.sym", gx + 20, gy + 40, name=nname, model="nfet", body="gnd",
                       w=wn, l="0.2u", m=1)
        self.wire(p["g"], (gx, gy), n["g"])
        self.wire(p["d"], (gx + 40, gy), n["d"])
        self.place("vdd.sym", p["s"][0], p["s"][1], lab="vdd")
        self.place("gnd.sym", n["s"][0], n["s"][1], lab="gnd")
        return (gx + 40, gy)

    # ------------------------------------------------------------------ connectivity
    def pin_points(self):
        pts = []
        for k, (sym, x, y, rot, flip, props) in enumerate(self.inst):
            for p, px, py in PINS[sym]:
                pts.append((transform(px, py, x, y, rot, flip), k, p))
        return pts

    def split_wires(self):
        """Split every wire at the pins and wire ends that lie inside it (Xschem connects
        them anyway; split wires make every connection an end point)."""
        points = {pt for pt, _, _ in self.pin_points()}
        for x1, y1, x2, y2 in self.segs:
            points.add((x1, y1))
            points.add((x2, y2))
        out = []
        for x1, y1, x2, y2 in self.segs:
            inner = sorted(p for p in points if inside(p, (x1, y1, x2, y2)))
            if (x1, y1) > (x2, y2):
                inner.reverse()
            chain = [(x1, y1)] + inner + [(x2, y2)]
            out += [(a[0], a[1], b[0], b[1]) for a, b in zip(chain, chain[1:])]
        self.segs = out

    def connectivity(self):
        """Net name of every point (pins and wire ends), and the problems found."""
        parent = {}

        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        pins = self.pin_points()
        for pt, _, _ in pins:
            find(pt)
        for x1, y1, x2, y2 in self.segs:
            union((x1, y1), (x2, y2))
        allpts = list(parent)
        for s in self.segs:                      # Xschem also connects points inside a wire
            for p in allpts:
                if inside(p, s):
                    union(p, (s[0], s[1]))
        names, problems = {}, []
        for pt, k, _ in pins:
            if self.inst[k][0] in LABELS:
                names.setdefault(find(pt), set()).add(self.inst[k][5]["lab"])
        for labs in names.values():
            if len(labs) > 1:
                problems.append("short between nets %s" % ", ".join(sorted(labs)))
        used = {props["body"] for sym, x, y, rot, flip, props in self.inst if "body" in props}
        for pt, k, _ in pins:
            if self.inst[k][0] not in LABELS and find(pt) in names:
                used |= names[find(pt)]
        for r in {find(p) for p in allpts}:
            if r not in names:
                problems.append("unnamed net at %s" % (r,))
            elif not names[r] & used:
                problems.append("net %s connects no device" % sorted(names[r])[0])
        point_net = {p: sorted(names[find(p)])[0] for p in allpts if find(p) in names}
        return point_net, problems

    def nets(self):
        """(net of every device pin, problems)"""
        point_net, problems = self.connectivity()
        net_of = {}
        for pt, k, p in self.pin_points():
            if self.inst[k][0] not in LABELS and pt in point_net:
                net_of[(self.inst[k][5]["name"], p)] = point_net[pt]
        return net_of, problems

    def devices(self):
        net_of, problems = self.nets()
        devs = {}
        for sym, x, y, rot, flip, props in self.inst:
            if sym in LABELS:
                continue
            nm = props["name"]
            devs[nm] = {"model": props["model"], "g": net_of.get((nm, "g")),
                        "ds": sorted([net_of.get((nm, "d")) or "?", net_of.get((nm, "s")) or "?"]),
                        "b": props["body"], "w": props["w"], "l": props["l"]}
        return devs, problems

    # ------------------------------------------------------------------ file
    def sch_text(self):
        L = ["v {xschem version=3.0.0 file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        L.append("T {%s} -20 -150 0 0 0.45 0.45 {}" % self.title)
        for i, ln in enumerate(self.lines):
            L.append("T {%s} -20 %d 0 0 0.28 0.28 {}" % (ln, -112 + 20 * i))
        point_net, _ = self.connectivity()
        for x1, y1, x2, y2 in self.segs:
            lab = point_net.get((x1, y1))
            L.append("N %g %g %g %g {%s}" % (x1, y1, x2, y2, "lab=%s" % lab if lab else ""))
        for sym, x, y, rot, flip, props in self.inst:
            attrs = " ".join("%s=%s" % (k, v) for k, v in props.items())
            L.append("C {%s} %g %g %d %d {%s}" % (sym, x, y, rot, flip, attrs))
        return "\n".join(L) + "\n"


def inside(p, seg):
    """True when point p lies on segment seg strictly between its end points."""
    x1, y1, x2, y2 = seg
    x, y = p
    if x1 == x2 == x:
        return min(y1, y2) < y < max(y1, y2)
    if y1 == y2 == y:
        return min(x1, x2) < x < max(x1, x2)
    return False


# ---------------------------------------------------------------------- the cells
def fb4():
    d = Drawing("pl_fb4", "pl_fb4   function block FB4:  P = C[2A+B]",
                ["4:1 transmission-gate multiplexer selected by A and B, input inverters, output buffer",
                 "20 transistors; device labels W/L, the sizes of the layout mag/pl_fb4.mag"])
    rows = [(0, "C0", "M2", "M3", "Bn", "B"), (120, "C1", "M0", "M1", "B", "Bn"),
            (280, "C2", "M4", "M5", "Bn", "B"), (400, "C3", "M6", "M7", "B", "Bn")]
    right = {}
    for y, c, mn, mp, ng, pg in rows:
        left, right[c] = d.tg(200, y, mn, mp, ng, pg, "0.4u", "0.5u")
        d.port("ipin", c, 80, y)
        d.wire((80, y), left)
    # first level: u0 = B ? C1 : C0, u1 = B ? C3 : C2
    d.wire(right["C0"], (310, 0), (310, 60))
    d.wire(right["C1"], (310, 120), (310, 60))
    d.wire((310, 60), (370, 60))
    d.wire_label("u0", 360, 60)
    d.wire(right["C2"], (310, 280), (310, 340))
    d.wire(right["C3"], (310, 400), (310, 340))
    d.wire((310, 340), (370, 340))
    d.wire_label("u1", 360, 340)
    # second level: x = A ? u1 : u0
    _, r4 = d.tg(400, 60, "M8", "M9", "An", "A", "0.4u", "0.5u")
    _, r5 = d.tg(400, 340, "M10", "M11", "A", "An", "0.4u", "0.5u")
    d.wire(r4, (510, 60), (510, 200))
    d.wire(r5, (510, 340), (510, 200))
    d.wire((510, 200), (580, 200))
    d.wire_label("x", 570, 200)
    # output buffer: Pn = not x, P = not Pn
    o1 = d.inverter(580, 200, "M16", "M17", "0.4u", "0.5u")
    d.wire(o1, (720, 200))
    d.wire_label("Pn", 710, 200)
    o2 = d.inverter(720, 200, "M18", "M19", "0.4u", "1u")
    d.wire(o2, (840, 200))
    d.port("opin", "P", 840, 200)
    # input inverters: An = not A, Bn = not B
    for x0, inp, mn, mp, out in ((60, "A", "M12", "M13", "An"), (340, "B", "M14", "M15", "Bn")):
        d.port("ipin", inp, x0, 600)
        d.wire((x0, 600), (x0 + 80, 600))
        o = d.inverter(x0 + 80, 600, mn, mp, "0.4u", "0.5u")
        d.wire(o, (o[0] + 80, 600))
        d.label(out, o[0] + 80, 600, right=True)
    d.port("iopin", "vdd", 680, 570)
    d.port("iopin", "gnd", 680, 610)
    return d


def cs():
    d = Drawing("pl_cs", "pl_cs   carry-sum cell CS:  CO = P ? CI : A,   Y = K ? P : (P xor CI)",
                ["carry multiplexer, XOR and K multiplexer as transmission gates; inverters, output buffers",
                 "24 transistors; device labels W/L, the sizes of the layout mag/pl_cs.mag"])
    # carry: cx = P ? CI : A, CO = buffered cx
    la, ra = d.tg(200, 0, "M0", "M1", "Pn", "P", "0.4u", "0.6u")
    lb, rb = d.tg(200, 120, "M2", "M3", "P", "Pn", "0.4u", "0.6u")
    d.port("ipin", "A", 80, 0)
    d.wire((80, 0), la)
    d.port("ipin", "CI", 80, 120)
    d.wire((80, 120), lb)
    d.wire(ra, (310, 0), (310, 60))
    d.wire(rb, (310, 120), (310, 60))
    d.wire((310, 60), (380, 60))
    d.wire_label("cx", 370, 60)
    o = d.inverter(380, 60, "M18", "M19", "0.4u", "0.6u")
    d.wire(o, (520, 60))
    d.wire_label("COn", 510, 60)
    o = d.inverter(520, 60, "M20", "M21", "0.8u", "1.2u")
    d.wire(o, (640, 60))
    d.port("opin", "CO", 640, 60)
    # propagate XOR: xn = P ? CI : CIn  (= not (P xor CI))
    lc, rc = d.tg(200, 300, "M4", "M5", "P", "Pn", "0.4u", "0.6u")
    ld, rd = d.tg(200, 420, "M6", "M7", "Pn", "P", "0.4u", "0.6u")
    d.label("CI", 120, 300)
    d.wire((120, 300), lc)
    d.label("CIn", 120, 420)
    d.wire((120, 420), ld)
    d.wire(rc, (310, 300), (310, 360))
    d.wire(rd, (310, 420), (310, 360))
    d.wire((310, 360), (370, 360))
    d.wire_label("xn", 360, 360)
    # logic or arithmetic: yn = K ? Pn : xn, Y = not yn
    le, re_ = d.tg(400, 240, "M12", "M13", "K", "Kn", "0.4u", "0.6u")
    _, rf = d.tg(400, 360, "M14", "M15", "Kn", "K", "0.4u", "0.6u")
    d.label("Pn", 320, 240)
    d.wire((320, 240), le)
    d.wire(re_, (510, 240), (510, 300))
    d.wire(rf, (510, 360), (510, 300))
    d.wire((510, 300), (580, 300))
    d.wire_label("yn", 570, 300)
    o = d.inverter(580, 300, "M22", "M23", "0.8u", "1.2u")
    d.wire(o, (700, 300))
    d.port("opin", "Y", 700, 300)
    # input inverters: Pn, CIn, Kn
    for x0, inp, mn, mp, out, port in ((60, "P", "M10", "M11", "Pn", True), (340, "CI", "M8", "M9", "CIn", False),
                                       (620, "K", "M16", "M17", "Kn", True)):
        if port:
            d.port("ipin", inp, x0, 600)
        else:
            d.label(inp, x0, 600)
        d.wire((x0, 600), (x0 + 80, 600))
        o = d.inverter(x0 + 80, 600, mn, mp, "0.4u", "0.6u")
        d.wire(o, (o[0] + 80, 600))
        d.label(out, o[0] + 80, 600, right=True)
    d.port("iopin", "vdd", 780, 150)
    d.port("iopin", "gnd", 780, 190)
    return d


# ---------------------------------------------------------------------- reference
def reference(cell):
    """Devices of a cell in tech/pl018/pl018_cells.sp, in the form of Drawing.devices()."""
    devs, on = {}, False
    for ln in open(CELLS_SP):
        t = ln.split()
        if not t:
            continue
        if t[0].lower() == ".subckt":
            on = t[1] == cell
            continue
        if on and t[0].lower().startswith(".ends"):
            break
        if on and t[0][0].lower() == "m":
            kv = dict(x.split("=", 1) for x in t[6:] if "=" in x)
            devs[t[0]] = {"model": t[5], "g": t[2], "ds": sorted([t[1], t[3]]), "b": t[4],
                          "w": kv.get("w"), "l": kv.get("l")}
    return devs


def check(d):
    got, problems = d.devices()
    ref = reference(d.name)
    for nm in sorted(set(ref) | set(got)):
        if nm not in got:
            problems.append("%s missing in the drawing" % nm)
        elif nm not in ref:
            problems.append("%s not in %s" % (nm, os.path.relpath(CELLS_SP, ROOT)))
        elif got[nm] != ref[nm]:
            problems.append("%s: drawing %s, netlist %s" % (nm, got[nm], ref[nm]))
    return got, ref, problems


def main():
    ok = True
    for make in (fb4, cs):
        d = make()
        d.split_wires()
        got, ref, problems = check(d)
        nets = sorted({n for v in got.values() for n in [v["g"]] + v["ds"] + [v["b"]]})
        if problems:
            ok = False
            print("%s: %d problems" % (d.name, len(problems)))
            for p in problems:
                print("  " + p)
            continue
        path = os.path.join(XDIR, d.name + ".sch")
        with open(path, "w") as f:
            f.write(d.sch_text())
        print("%s: %d devices and %d nets as in %s; %d wires, %d labels -> %s" % (
            d.name, len(got), len(nets), os.path.relpath(CELLS_SP, ROOT), len(d.segs),
            sum(1 for i in d.inst if i[0] in LABELS), os.path.relpath(path, ROOT)))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
