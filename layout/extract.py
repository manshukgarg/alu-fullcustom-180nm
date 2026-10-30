"""Connectivity extraction of a maglib.Layout and an LVS-style comparison.

Nodes are the connected regions of polysilicon (gates included), diffusion
(cut by the gates), metal1 and metal2, joined through diffusion contacts, poly
contacts and vias exactly as Magic composes them. Every transistor region
becomes a device with its gate node, its two diffusion nodes and its drawn W
and L. Node names come from the net annotation that the generator attached to
each shape; a node carrying two names is a short, a name spread over two nodes
is an open. The device list is then compared with the intended netlist.
"""
from collections import Counter

import numpy as np

from drc import Grid, ACT, MET1, MET2, components


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        p = self.p
        p.setdefault(a, a)
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def extract(L):
    """Return (devices, node_of, grid): devices are (model, g, s, d, W, L) with node ids."""
    g = Grid(L)
    act, m1, m2 = g.act, g.m1, g.m2
    polyset = np.isin(act, [ACT[t] for t in ("poly", "pc", "ntr", "ptr")])
    diffset = np.isin(act, [ACT[t] for t in ("ndiff", "pdiff", "ndc", "pdc")])
    tapset = np.isin(act, [ACT["psc"], ACT["nsc"]])
    lp, _ = components(polyset)
    ld, _ = components(diffset)
    lt, _ = components(tapset)
    l1, _ = components(m1 > 0)
    l2, _ = components(m2 > 0)
    uf = UF()

    def tie(maskA, labA, ka, labB, kb):
        for x, y in np.argwhere(maskA):
            uf.union((ka, int(labA[x, y])), (kb, int(labB[x, y])))

    tie(np.isin(act, [ACT["ndc"], ACT["pdc"]]), ld, "d", l1, "1")
    tie(act == ACT["pc"], lp, "p", l1, "1")
    tie(tapset, lt, "t", l1, "1")
    tie(m1 == MET1["m2c"], l1, "1", l2, "2")

    def node(kind, lab, x, y):
        return uf.find((kind, int(lab[x, y])))

    # devices
    trans = np.isin(act, [ACT["ntr"], ACT["ptr"]])
    lt_, nt = components(trans)
    devices = []
    for k in range(1, nt + 1):
        cells = np.argwhere(lt_ == k)
        x, y = cells[0]
        model = "nfet" if act[x, y] == ACT["ntr"] else "pfet"
        gate = node("p", lp, x, y)
        sides = {"x": set(), "y": set()}
        for cx, cy in cells:
            for dx, dy, ax in ((1, 0, "x"), (-1, 0, "x"), (0, 1, "y"), (0, -1, "y")):
                nx_, ny_ = cx + dx, cy + dy
                if diffset[nx_, ny_]:
                    sides[ax].add(node("d", ld, nx_, ny_))
        xs, ys = cells[:, 0], cells[:, 1]
        wx, wy = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if sides["x"] and not sides["y"]:
            sd, W, Lc = sides["x"], int(wy), int(wx)
        elif sides["y"] and not sides["x"]:
            sd, W, Lc = sides["y"], int(wx), int(wy)
        else:
            sd, W, Lc = sides["x"] | sides["y"], -1, -1
        sd = sorted(sd, key=str)
        if len(sd) == 1:
            sd = sd * 2
        devices.append((model, gate, tuple(sd), W, Lc))
    nodes = {"p": lp, "d": ld, "1": l1, "2": l2, "t": lt}
    return devices, nodes, uf, g


def lvs(L, shapes, fingers, pins):
    """Compare the layout with the intended devices. Returns a list of problems."""
    devices, nodes, uf, g = extract(L)
    act = g.act
    problems = []
    names = {}                      # extracted node -> set of intended names

    def note(kind, x, y, net):
        lab = nodes[kind]
        xi, yi = x - g.x0, y - g.y0
        if lab[xi, yi]:
            names.setdefault(uf.find((kind, int(lab[xi, yi]))), set()).add(net)

    for layer, x1, y1, x2, y2, net in shapes:
        if not net:
            continue
        kinds = {"poly": "p", "pc": "p", "ndiff": "d", "pdiff": "d", "ndc": "d", "pdc": "d",
                 "m1": "1", "m2": "2", "m2c": "2", "psc": "t", "nsc": "t"}.get(layer)
        if kinds is None:
            continue
        for x in range(x1, x2):
            for y in range(y1, y2):
                xi, yi = x - g.x0, y - g.y0
                # diffusion under a gate is the transistor, not a node
                if kinds == "d" and act[xi, yi] in (ACT["ntr"], ACT["ptr"]):
                    continue
                if kinds == "p" and act[xi, yi] not in (ACT["poly"], ACT["pc"], ACT["ntr"], ACT["ptr"]):
                    continue
                note(kinds, x, y, net)
    for n, s in names.items():
        if len(s) > 1:
            problems.append("short between %s" % ", ".join(sorted(s)))
    where = {}
    for n, s in names.items():
        for net in s:
            where.setdefault(net, set()).add(n)
    for net, ns in where.items():
        if len(ns) > 1:
            problems.append("open: net %s is split into %d pieces" % (net, len(ns)))

    def nm(n):
        s = names.get(n)
        return sorted(s)[0] if s else "?%s" % (n,)

    got = Counter()
    for model, gate, sd, W, Lc in devices:
        a, b = sorted((nm(sd[0]), nm(sd[1])))
        got[(model, nm(gate), a, b, W, Lc)] += 1
    want = Counter()
    for model, d, gg, s, w in fingers:
        a, b = sorted((d, s))
        want[(model, gg, a, b, w, 2)] += 1
    if got != want:
        extra = got - want
        miss = want - got
        if extra:
            problems.append("layout has unexpected devices: %s" % dict(extra))
        if miss:
            problems.append("layout lacks devices: %s" % dict(miss))
    # pin labels sit on metal1 of their own net
    for layer, (x1, y1, x2, y2), text, use, cls in L.labels:
        if text not in pins:
            continue
        xi, yi = x1 - g.x0, y1 - g.y0
        kind = "1" if layer == "m1" else "2"
        lab = nodes[kind][xi, yi]
        if not lab:
            problems.append("pin %s label is not on its metal" % text)
            continue
        n = uf.find((kind, int(lab)))
        if text not in names.get(n, set()):
            problems.append("pin %s label is on net %s" % (text, sorted(names.get(n, {"?"}))))
    return problems, len(devices)
