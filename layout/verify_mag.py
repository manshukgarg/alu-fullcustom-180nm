#!/usr/bin/env python3
"""Independent check of written Magic files: rules, and layout-versus-netlist by graph matching.

Each .mag file is read back from disk (no information from the generator is
used), checked with drc.py, and its transistors and nets are extracted from the
geometry. The pin labels name their nets; everything else is matched against
the reference netlist by graph isomorphism (devices with model, W and L; gate
and source/drain connections, source and drain interchangeable).

Usage:  python3 layout/verify_mag.py mag/opt_fa.mag step4_layout/ref/opt_fa.spice [...pairs]
"""
import re
import sys

import networkx as nx
from networkx.algorithms import isomorphism

import drc
import extract
from maglib import Layout, TYPES

NAME_TO_SHORT = {v[0]: k for k, v in TYPES.items()}
PLANE = {"well": "well", "active": "active", "metal1": "metal1", "metal2": "metal2"}


def read_mag(path):
    L = Layout(path)
    cur = None
    for line in open(path):
        line = line.strip()
        m = re.match(r"<< (\S+) >>", line)
        if m:
            cur = NAME_TO_SHORT.get(m.group(1))
            continue
        if line.startswith("rect") and cur:
            x1, y1, x2, y2 = (int(v) for v in line.split()[1:5])
            for plane in TYPES[cur][1]:
                P = L.planes[PLANE[plane]]
                for x in range(x1, x2):
                    for y in range(y1, y2):
                        P[(x, y)] = cur
        elif line.startswith("rlabel"):
            f = line.split()
            L.labels.append((NAME_TO_SHORT.get(f[1], f[1]),
                             tuple(int(v) for v in f[3:7]), f[-1], "", ""))
    return L


def layout_graph(L):
    devices, nodes, uf, g = extract.extract(L)
    G = nx.Graph()
    pins = {}
    for layer, (x1, y1, x2, y2), text, use, cls in L.labels:
        kind = "1" if layer == "m1" else "2"
        lab = nodes[kind][x1 - g.x0, y1 - g.y0]
        if lab:
            pins[uf.find((kind, int(lab)))] = text
    for i, (model, gate, sd, W, Lc) in enumerate(devices):
        d = ("dev", i)
        G.add_node(d, kind="dev", model=model, w=W, l=Lc)
        for n, role in ((gate, "g"), (sd[0], "sd"), (sd[1], "sd")):
            G.add_node(("net", n), kind="net", pin=pins.get(n))
            if G.has_edge(d, ("net", n)):
                G[d][("net", n)]["role"] += "+" + role
            else:
                G.add_edge(d, ("net", n), role=role)
    return G, len(devices)


def netlist_graph(path):
    G = nx.Graph()
    pins, n = set(), 0
    for line in open(path):
        f = line.split()
        if not f:
            continue
        if f[0].lower() == ".subckt":
            pins = set(f[2:])
        elif f[0][0] in "Mm":
            dd, gg, ss, model = f[1], f[2], f[3], f[5]
            w = next(float(x.split("=")[1].rstrip("u")) for x in f if x.startswith("w="))
            l_ = next(float(x.split("=")[1].rstrip("u")) for x in f if x.startswith("l="))
            d = ("dev", n)
            n += 1
            G.add_node(d, kind="dev", model=model, w=round(w * 10), l=round(l_ * 10))
            for net, role in ((gg, "g"), (dd, "sd"), (ss, "sd")):
                G.add_node(("net", net), kind="net", pin=net if net in pins else None)
                if G.has_edge(d, ("net", net)):
                    G[d][("net", net)]["role"] += "+" + role
                else:
                    G.add_edge(d, ("net", net), role=role)
    return G, n


def roles(r):
    return "+".join(sorted(r.split("+")))


def compare(mag, ref):
    L = read_mag(mag)
    errors = drc.check(L)
    GL, nl = layout_graph(L)
    GR, nr = netlist_graph(ref)
    nm = lambda a, b: (a["kind"] == b["kind"] and a.get("model") == b.get("model")
                       and a.get("w") == b.get("w") and a.get("l") == b.get("l")
                       and a.get("pin") == b.get("pin"))
    em = lambda a, b: roles(a["role"]) == roles(b["role"])
    match = isomorphism.GraphMatcher(GL, GR, node_match=nm, edge_match=em).is_isomorphic()
    return errors, match, nl, nr


def main(args):
    ok = True
    for mag, ref in zip(args[0::2], args[1::2]):
        errors, match, nl, nr = compare(mag, ref)
        print("%-28s DRC %-6s  devices %3d / %3d  netlist %s" % (
            mag, "clean" if not errors else "%d err" % len(errors), nl, nr,
            "match" if match else "MISMATCH"))
        for e in errors[:5]:
            print("    " + e)
        ok &= not errors and match
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
