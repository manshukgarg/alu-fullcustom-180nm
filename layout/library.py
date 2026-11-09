"""Cell plans of the custom library: device order in the NMOS and PMOS rows.

Each plan lists the columns of a cell left to right (see cellgen.py). Widths
come from the transistor netlists of step3_cells/cellnet.py at the chosen
width scale k and P/N ratio r, so the same plans serve the optimized library
(selected k, r) and the conventional library (k = 1, r = 2).

Strips whose transistors are wider than the row allows (NMOS 2.4 um, PMOS
3.2 um on the 8 um template) are folded: the strip is mirrored, every device
of 0.8 um or more becomes two fingers of half width, and series stacks become
two parallel stacks with their own internal nodes.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "step3_cells"))

import cellnet  # noqa: E402
from cellgen import CellBuilder  # noqa: E402
from template import WN_MAX, WP_MAX  # noqa: E402


def D(n, p):
    return ("D", n, p)


def G(n, p=None, same=True):
    return ("G", n, n if (p is None and same) else p)


BRK = ("B",)

# ---------------------------------------------------------------------------
# column plans (unfolded)
# ---------------------------------------------------------------------------
PLANS = {
    "inv_cmos": [D("gnd", "vdd"), G("A"), D("Y", "Y")],
    # two inverters sharing the supply column; the output stage folds when wide
    "buf_cmos": [D("Yn", "Yn"), G("A"), D("gnd", "vdd"), BRK, D("gnd", "vdd"), G("Yn"), D("Y", "Y")],

    "nand2_cmos": [D("gnd", "vdd"), G("B"), D("x", "Y"), G("A"), D("Y", "vdd")],

    "nor2_cmos": [D("gnd", "Y"), G("A"), D("Y", "x"), G("B"), D("gnd", "vdd")],

    # A xor B: two transmission gates fed by A and An, inverters for An and Bn
    "xor_tg8": [D("A", "A"), G("Bn", "B"), D("Y", "Y"), G("B", "Bn"), D("An", "An"),
                G("A"), D("gnd", "vdd"), G("B"), D("Bn", "Bn")],

    "xor_tgb10": [D("A", "A"), G("B", "Bn"), D("Xn", "Xn"), G("Bn", "B"), D("An", "An"),
                  G("A"), D("gnd", "vdd"), G("B"), D("Bn", "Bn"), BRK,
                  D("Y", "Y"), G("Xn"), D("gnd", "vdd")],

    # each series-stack pair is its own strip, so folding mirrors it around Y;
    # neighbouring strips that meet on a rail are joined after folding
    "xor_cmos12": [D("An", "An"), G("A"), D("gnd", "vdd"), BRK,
                   D("gnd", "vdd"), G("B", "Bn"), D("n1", "p2"), G("A"), D("Y", "Y"), BRK,
                   D("gnd", "vdd"), G("Bn", "B"), D("n2", "p1"), G("An"), D("Y", "Y"), BRK,
                   D("gnd", "vdd"), G("B"), D("Bn", "Bn")],

    "mux_tg6": [D("gnd", "vdd"), G("S"), D("Sn", "Sn"), BRK,
                D("A", "A"), G("Sn", "S"), D("Y", "Y"), G("S", "Sn"), D("B", "B")],

    "mux_tgb10": [D("Sn", "Sn"), G("S"), D("gnd", "vdd"), G("M"), D("Mn", "Mn"), BRK,
                  D("A", "A"), G("Sn", "S"), D("M", "M"), G("S", "Sn"), D("B", "B"), BRK,
                  D("Y", "Y"), G("Mn"), D("gnd", "vdd")],

    "muxi_tg8": [D("Sn", "Sn"), G("S"), D("gnd", "vdd"), G("M"), D("Y", "Y"), BRK,
                 D("A", "A"), G("Sn", "S"), D("M", "M"), G("S", "Sn"), D("B", "B")],

    "mux_cmos12": [D("Sn", "Sn"), G("S"), D("gnd", "vdd"), G("Yb"), D("Y", "Y"), BRK,
                   D("gnd", "vdd"), G("Sn", "B"), D("n1", "p1"), G("A"), D("Yb", "Yb"),
                   G("B", "Sn"), D("n2", "p1"), G("S"), D("gnd", "vdd")],

    "muxi_cmos10": [D("Sn", "Sn"), G("S"), D("gnd", "vdd"), BRK,
                    D("gnd", "vdd"), G("Sn", "B"), D("n1", "p1"), G("A"), D("Y", "Y"),
                    G("B", "Sn"), D("n2", "p1"), G("S"), D("gnd", "vdd")],

    # buffered TG full adder: P = A xor B; Sx = not S; COx = not CO
    "fa_tgab24": [D("A", "A"), G("Bn", "B"), D("P", "P"), G("B", "Bn"), D("An", "An"), BRK,
                  D("Bn", "Bn"), G("B"), D("gnd", "vdd"), G("A"), D("An", "An"),
                  G("Pn", "P"), D("COx", "COx"), G("P", "Pn"), D("Cn", "Cn"),
                  G("Pn", "P"), D("Sx", "Sx"), G("P", "Pn"), D("C", "C"), BRK,
                  D("Cn", "Cn"), G("C"), D("gnd", "vdd"), G("P"), D("Pn", "Pn"), BRK,
                  D("S", "S"), G("Sx"), D("gnd", "vdd"), G("COx"), D("CO", "CO")],

    "fa_tga20": [D("A", "A"), G("Bn", "B"), D("P", "P"), G("B", "Bn"), D("An", "An"),
                 G("A"), D("gnd", "vdd"), G("B"), D("Bn", "Bn"), BRK,
                 D("Pn", "Pn"), G("P"), D("gnd", "vdd"), G("C"), D("Cn", "Cn"),
                 G("P", "Pn"), D("S", "S"), G("Pn", "P"), D("C", "C"),
                 G("P", "Pn"), D("CO", "CO"), G("Pn", "P"), D("A", "A")],

    # mirror adder: carry network folded in two, sum network folded in three (taller channel),
    # output inverters joined to the carry strip through the shared rails
    "fa_cmos28": [D("CO", "CO"), G("COn"), D("gnd", "vdd"), BRK,
                  D("gnd", "vdd"), G("B"), D("n1", "p1"), G("A"), D("COn", "COn"), G("C"),
                  D("n2", "p2"), G("A"), D("gnd", "vdd"), G("B"), D("n2", "p2"), BRK,
                  D("gnd", "vdd"), G("Sn"), D("S", "S"), BRK,
                  ("F", 3), D("Sn", "Sn"), G("A"), D("n3", "p3"), G("B"), D("n4", "p4"), G("C"),
                  D("gnd", "vdd"), G("A"), D("n5", "p5"), G("B"), D("gnd", "vdd"), G("C"),
                  D("n5", "p5"), G("COn"), D("Sn", "Sn")],
}


# ---------------------------------------------------------------------------
# folding
# ---------------------------------------------------------------------------
def _strips(plan):
    out, cur = [], []
    for col in plan:
        if col[0] == "B" and len(col) == 1:
            out.append(cur)
            cur = []
        else:
            cur.append(col)
    out.append(cur)
    return [s for s in out if s]


def _gate_width(cell, strip, i, row):
    """Width (lambda) of the device at gate column i of a strip."""
    col = strip[i]
    g = col[1 + row]
    left, right = strip[i - 1][1 + row], strip[i + 1][1 + row]
    model = "nfet" if row == 0 else "pfet"
    for m, d, gg, s, b, w in cell.devs:
        if m == model and gg == g.split("#")[0] and {d, s} == {left.split("#")[0], right.split("#")[0]}:
            return int(round(w * 10))
    raise KeyError((cell.name, g, left, right))


def fold(cell, plan, pins):
    """Fold strips holding a transistor wider than its row allows.

    The strip is repeated nf times, every other copy mirrored, so neighbouring
    copies share their end node. A device of width W gets min(nf, W // 4)
    fingers of equal width; series stacks become parallel stacks with their own
    internal nodes (x#1, x#2, ...). A strip may force nf with a leading ("F", nf).
    """
    gates = {c[1 + r] for c in plan if c[0] == "G" for r in (0, 1) if c[1 + r]}
    count = {}
    for c in plan:
        if c[0] == "D":
            for r in (0, 1):
                if c[1 + r]:
                    count[c[1 + r]] = count.get(c[1 + r], 0) + 1
    internal = {n for n, k in count.items()
                if k == 1 and n not in gates and n not in pins and n not in ("gnd", "vdd")}
    out = []
    for strip in _strips(plan):
        forced = 1
        if strip and strip[0][0] == "F":
            forced = strip[0][1]
            strip = strip[1:]
        nf = forced
        width = {}
        for i, col in enumerate(strip):
            if col[0] == "G":
                for row in (0, 1):
                    if col[1 + row]:
                        w = _gate_width(cell, strip, i, row)
                        width[(i, row)] = w
                        lim = (WN_MAX, WP_MAX)[row]
                        nf = max(nf, -(-w // lim))
        if nf == 1:
            out.extend(strip + [BRK])
            continue

        def copy(k):
            idx = list(range(len(strip)))
            if k % 2 == 0:                       # mirrored copy, shares the previous end
                idx = list(reversed(idx[:-1]))
            elif k > 1:
                idx = idx[1:]
            cols = []
            for i in idx:
                c = strip[i]
                if c[0] == "D":
                    cols.append(("D",) + tuple(n + "#%d" % k if n in internal else n
                                               for n in c[1:]))
                else:
                    g_ = []
                    for row in (0, 1):
                        w = width.get((i, row))
                        fingers = min(nf, w // 4) if w else 0
                        g_.append(c[1 + row] if w and k <= fingers else None)
                    cols.append(("G", g_[0], g_[1]))
            return cols
        full = []
        for k in range(1, nf + 1):
            full.extend(copy(k))
        # remove diffusion nodes left without a transistor, then empty columns
        for j, col in enumerate(full):
            if col[0] != "D":
                continue
            vals = list(col[1:])
            for row in (0, 1):
                left = full[j - 1][1 + row] if j > 0 else None
                right = full[j + 1][1 + row] if j + 1 < len(full) else None
                if not left and not right:
                    vals[row] = None
            full[j] = ("D", vals[0], vals[1])
        for col in full:
            if col[1] is None and col[2] is None:
                if out and out[-1] != BRK:
                    out.append(BRK)
                continue
            out.append(col)
        out.append(BRK)
    while out and out[-1] == BRK:
        out.pop()
    final = []
    for col in out:
        if col == BRK and (not final or final[-1] == BRK):
            continue
        final.append(col)
    return join_strips(final)


def join_strips(plan):
    """Remove a break between two diffusion columns with the same nets (shared node)."""
    out = []
    i = 0
    while i < len(plan):
        col = plan[i]
        if (col == BRK and out and i + 1 < len(plan) and out[-1][0] == "D"
                and plan[i + 1][0] == "D" and out[-1][1:] == plan[i + 1][1:]
                and all(n is not None for n in out[-1][1:])):
            i += 2                       # drop the break and the duplicate column
            continue
        out.append(col)
        i += 1
    return out


def make_cell(fname, k, r, name=None, grid=False):
    """Netlist cell (step3_cells/cellnet.py) and its CellBuilder.

    grid=True builds a cell for automatic place and route (site-multiple width,
    pin pads on routing-track crossings, see cellgen.py)."""
    cell = getattr(cellnet, fname)(k, r)
    devs = [(m, d, g, s, int(round(w * 10))) for m, d, g, s, b, w in cell.devs]
    plan = join_strips(fold(cell, PLANS[fname], cell.inputs + cell.outputs))
    b = CellBuilder(name or fname, devs, plan, cell.inputs, cell.outputs, grid=grid)
    return cell, b


def fill_cell(name, sites=1):
    """Filler cell for placement rows: rails, n-well and power ports only."""
    from maglib import Layout
    from template import H, RAIL, NW_Y0, NW_Y1, EDGE
    from cellgen import SITE
    w = SITE * sites
    L = Layout(name, bbox=(0, 0, w, H))
    L.paint("m1", 0, -RAIL, w, RAIL)
    L.paint("m1", 0, H - RAIL, w, H + RAIL)
    L.paint("nwell", -6, NW_Y0, w + 6, NW_Y1)
    L.label("m1", 0, H - RAIL, EDGE, H + RAIL, "vdd", "power", "bidirectional")
    L.label("m1", 0, -RAIL, EDGE, RAIL, "gnd", "ground", "bidirectional")
    shapes = [("m1", 0, -RAIL, w, RAIL, "gnd"), ("m1", 0, H - RAIL, w, H + RAIL, "vdd")]
    return L, shapes
