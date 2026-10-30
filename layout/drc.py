"""Design-rule check of a maglib.Layout against the SCN6M_SUBM.10 rules used by the
cell library (MOSIS SCMOS SUBM, lambda units), following Magic's edge semantics.

Covers width, spacing (same type and between types, with Euclidean corners),
enclosure by the n-well, transistor overhangs, poly-to-diffusion spacing,
contact spacing and the minimum-area rules for metal1, metal2 and taps.
It is a pre-check: the authoritative DRC is Magic in the lab.
"""
import math

import numpy as np

ACT = {"ndiff": 1, "pdiff": 2, "poly": 3, "ntr": 4, "ptr": 5, "ndc": 6, "pdc": 7,
       "pc": 8, "psc": 9, "nsc": 10}
MET1 = {"m1": 1, "ndc": 2, "pdc": 3, "pc": 4, "psc": 5, "nsc": 6, "m2c": 7}
MET2 = {"m2": 1, "m2c": 2}

DIFF_ALL = ["ndiff", "pdiff", "ntr", "ptr", "ndc", "pdc", "psc", "nsc"]
POLY_ALL = ["poly", "pc", "ntr", "ptr"]
ND = ["ndiff", "ntr", "ndc"]
PD = ["pdiff", "ptr", "pdc"]
DC = ["ndc", "pdc", "psc", "nsc"]
TRANS = ["ntr", "ptr"]


class Grid:
    def __init__(self, L, margin=16):
        cells = [c for p in L.planes.values() for c in p]
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        self.x0, self.y0 = min(xs) - margin, min(ys) - margin
        nx, ny = max(xs) - self.x0 + margin + 1, max(ys) - self.y0 + margin + 1
        self.act = np.zeros((nx, ny), dtype=np.int8)
        self.m1 = np.zeros((nx, ny), dtype=np.int8)
        self.m2 = np.zeros((nx, ny), dtype=np.int8)
        self.well = np.zeros((nx, ny), dtype=bool)
        for (x, y), t in L.planes["active"].items():
            self.act[x - self.x0, y - self.y0] = ACT[t]
        for (x, y), t in L.planes["metal1"].items():
            self.m1[x - self.x0, y - self.y0] = MET1[t]
        for (x, y), t in L.planes["metal2"].items():
            self.m2[x - self.x0, y - self.y0] = MET2[t]
        for (x, y) in L.planes["well"]:
            self.well[x - self.x0, y - self.y0] = True

    def a(self, names):
        return np.isin(self.act, [ACT[n] for n in names])

    def pos(self, ij):
        return (int(ij[0]) + self.x0, int(ij[1]) + self.y0)


def shift(m, dx, dy):
    """out[x, y] = m[x + dx, y + dy] (False outside)."""
    out = np.zeros_like(m)
    nx, ny = m.shape
    xs, xd = (slice(dx, nx), slice(0, nx - dx)) if dx >= 0 else (slice(0, nx + dx), slice(-dx, nx))
    ys, yd = (slice(dy, ny), slice(0, ny - dy)) if dy >= 0 else (slice(0, ny + dy), slice(-dy, ny))
    out[xd, yd] = m[xs, ys]
    return out


def disk(d):
    """Offsets whose cell-to-cell Euclidean gap is below d (cells closer than d)."""
    r = int(math.ceil(d)) + 1
    out = []
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            gx, gy = max(0, abs(dx) - 1), max(0, abs(dy) - 1)
            if math.hypot(gx, gy) < d:
                out.append((dx, dy))
    return out


def dilate(m, d):
    out = np.zeros_like(m)
    for dx, dy in disk(d):
        out |= shift(m, dx, dy)
    return out


def components(m):
    """4-connected component labels (0 = background)."""
    lab = np.zeros(m.shape, dtype=np.int32)
    n = 0
    nx, ny = m.shape
    for x, y in np.argwhere(m):
        if lab[x, y]:
            continue
        n += 1
        stack = [(x, y)]
        lab[x, y] = n
        while stack:
            cx, cy = stack.pop()
            for ax, ay in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= ax < nx and 0 <= ay < ny and m[ax, ay] and not lab[ax, ay]:
                    lab[ax, ay] = n
                    stack.append((ax, ay))
    return lab, n


class Checker:
    def __init__(self, L):
        self.g = Grid(L)
        self.errors = []

    def err(self, msg, where):
        if len(where):
            self.errors.append("%s near %s (%d cells)" % (msg, self.g.pos(where[0]), len(where)))

    # ---------------------------------------------------------------- rule kinds
    def width(self, m, w, msg):
        if not m.any():
            return
        nx, ny = m.shape
        S = np.zeros((nx + 1, ny + 1), dtype=np.int32)
        S[1:, 1:] = m.astype(np.int32).cumsum(0).cumsum(1)
        full = np.zeros_like(m)
        tot = S[w:, w:] - S[:-w, w:] - S[w:, :-w] + S[:-w, :-w]
        full[: nx - w + 1, : ny - w + 1] = tot == w * w
        cover = np.zeros_like(m)
        for dx in range(w):
            for dy in range(w):
                cover |= shift(full, -dx, -dy)
        self.err(msg, np.argwhere(m & ~cover))

    def spacing(self, A, B, d, msg, touching_ok=True):
        """Magic spacing rule between type sets A and B (A may equal B)."""
        if not A.any() or not B.any():
            return
        if not touching_ok:
            self.err(msg, np.argwhere(A & dilate(B, d)))
            return
        same = np.array_equal(A, B)
        pairs = [(A, B)] if same else [(A, B), (B, A)]
        for P, Q in pairs:
            R = ~P & ~Q
            bad = np.zeros_like(P)
            dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
            for dx, dy in dirs:
                edge = P & shift(R, dx, dy)
                if not edge.any():
                    continue
                hit = np.zeros_like(P)
                for k in range(2, int(math.ceil(d)) + 1):
                    hit |= shift(Q, k * dx, k * dy)
                bad |= edge & hit
            # convex corners: Euclidean check into the diagonal quadrant
            for sx in (1, -1):
                for sy in (1, -1):
                    corner = P & shift(R, sx, 0) & shift(R, 0, sy)
                    if not corner.any():
                        continue
                    hit = np.zeros_like(P)
                    r = int(math.ceil(d)) + 1
                    for i in range(1, r + 1):
                        for j in range(1, r + 1):
                            if math.hypot(i - 1, j - 1) < d:
                                hit |= shift(Q, i * sx, j * sy)
                    bad |= corner & hit
            self.err(msg, np.argwhere(bad))

    def enclose(self, inner, outer, d, msg):
        self.err(msg, np.argwhere(inner & dilate(~outer, d)))

    def area(self, m, amin, msg):
        lab, n = components(m)
        if n:
            sizes = np.bincount(lab.ravel())
            for k in range(1, n + 1):
                if sizes[k] < amin:
                    self.err(msg, np.argwhere(lab == k))

    # ---------------------------------------------------------------- all rules
    def run(self):
        g = self.g
        a = g.a
        diff, poly = a(DIFF_ALL), a(POLY_ALL)
        nd, pd = a(ND), a(PD)
        trans, dc = a(TRANS), a(DC)
        psc, nsc, pc = a(["psc"]), a(["nsc"]), a(["pc"])
        m1, m2 = g.m1 > 0, g.m2 > 0
        nw = g.well

        self.width(nw, 12, "N-well width < 12")
        self.width(diff, 3, "Diffusion width < 3")
        self.width(poly, 2, "Poly width < 2")
        self.width(m1, 3, "Metal1 width < 3")
        self.width(m2, 3, "Metal2 width < 3")
        for t in ("ndc", "pdc", "pc", "psc", "nsc", "m2c"):
            self.width(g.m1 == MET1[t], 4, "%s width < 4" % t)

        self.spacing(nw, nw, 6, "N-well spacing < 6")
        self.spacing(diff, diff, 3, "Diffusion spacing < 3")
        self.spacing(nw, nd, 6, "N-well spacing to N-Diffusion < 6", touching_ok=False)
        self.spacing(nd, pd, 12, "N-Diffusion spacing to P-Diffusion < 12", touching_ok=False)
        self.enclose(pd, nw, 6, "N-well overlap of P-Diffusion < 6")
        self.enclose(nsc, nw, 3, "N-well overlap of N-Ohmic < 3")
        self.spacing(a(["ndiff", "ndc"]), nsc, 9, "N-Diffusion spacing to N-Ohmic < 9", False)
        self.spacing(a(["pdiff", "pdc"]), psc, 9, "P-Diffusion spacing to P-Ohmic < 9", False)
        self.spacing(nw, psc, 3, "N-well spacing to P-Ohmic < 3", touching_ok=False)
        self.spacing(nsc, psc, 6, "N-Ohmic spacing to P-Ohmic < 6", touching_ok=False)
        self.spacing(nd, psc, 4, "N-Diffusion spacing to P-Ohmic < 4")
        self.spacing(pd, nsc, 4, "P-Diffusion spacing to N-Ohmic < 4")
        self.spacing(poly, poly, 3, "Poly spacing < 3")
        self._gate_rules()
        self._poly_diff()
        self._tran_ohmic()
        self.area(psc | nsc, 16, "Ohmic-Diffusion area < 16")
        self.spacing(a(["psc"]), a(["ndc"]), 1, "psc spacing to ndc < 1", touching_ok=False)
        self.spacing(a(["nsc"]), a(["pdc"]), 1, "nsc spacing to pdc < 1", touching_ok=False)
        self.spacing(trans, dc, 1, "Transistor spacing to Diffusion contact < 1", touching_ok=False)
        self.spacing(diff, pc, 1, "Diffusion spacing to Poly contact < 1", touching_ok=False)
        self.spacing(diff, dc, 4, "Diffusion spacing to Diffusion contact < 4")
        self.spacing(pc, dc, 2, "Poly contact spacing to Diffusion contact < 2", touching_ok=False)
        self.spacing(m1, m1, 3, "Metal1 spacing < 3")
        self.area(m1, 20, "Metal1 area < 20")
        self.spacing(m2, m2, 3, "Metal2 spacing < 3")
        self.area(m2, 20, "Metal2 area < 20")
        stacked = (g.m1 == MET1["m2c"]) & np.isin(g.act, [ACT[t] for t in ("ndc", "pdc", "pc", "psc", "nsc")])
        self.err("m2c stacked on a contact", np.argwhere(stacked))
        return self.errors

    def _gate_rules(self):
        g = self.g
        act = g.act
        trans = np.isin(act, [ACT["ntr"], ACT["ptr"]])
        polyt = np.isin(act, [ACT["poly"], ACT["pc"]])
        difft = np.isin(act, [ACT[t] for t in ("ndiff", "pdiff", "ndc", "pdc")])
        space = act == 0
        bad_p = np.zeros_like(trans)
        bad_d = np.zeros_like(trans)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = shift(act, dx, dy)
            nb_poly_or_space = shift(polyt | space, dx, dy)
            nb_diff_or_space = shift(difft | space, dx, dy)
            # poly side: two cells of poly beyond the transistor
            need_p = trans & nb_poly_or_space
            okp = shift(polyt, dx, dy) & shift(polyt | trans, 2 * dx, 2 * dy)
            bad_p |= need_p & ~okp
            # diffusion side: three cells of diffusion beyond the transistor
            need_d = trans & nb_diff_or_space
            dif_or_t = difft | trans
            okd = shift(dif_or_t, dx, dy) & shift(dif_or_t, 2 * dx, 2 * dy) & shift(dif_or_t, 3 * dx, 3 * dy)
            bad_d |= need_d & ~okd
            del nb
        self.err("Poly overhang of Transistor < 2", np.argwhere(bad_p))
        self.err("Diffusion overhang of Transistor < 3", np.argwhere(bad_d))

    def _poly_diff(self):
        """Field poly (and poly contacts) must keep 1 lambda of space to other active types."""
        act = self.g.act
        polyt = np.isin(act, [ACT["poly"], ACT["pc"]])
        okn = np.isin(act, [0, ACT["poly"], ACT["pc"], ACT["ntr"], ACT["ptr"]])
        space = act == 0
        bad = np.zeros_like(polyt)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bad |= polyt & ~shift(okn, dx, dy)
        for sx in (1, -1):
            for sy in (1, -1):
                corner = polyt & shift(space, sx, 0) & shift(space, 0, sy)
                bad |= corner & ~shift(okn, sx, sy)
        self.err("Poly spacing to Diffusion < 1", np.argwhere(bad))

    def _tran_ohmic(self):
        act = self.g.act
        for t, o, msg in (("ntr", "psc", "N-Transistor space to P-Ohmic < 3"),
                          ("ptr", "nsc", "P-Transistor space to N-Ohmic < 3")):
            T = act == ACT[t]
            O = act == ACT[o]
            self.err(msg, np.argwhere(T & dilate(O, 3)))


def check(L):
    return Checker(L).run()
