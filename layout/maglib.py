"""Layout builder for Magic in the SCN6M_SUBM.10 technology (OSU018 kit).

All coordinates are in lambda (1 lambda = 0.1 um). Geometry is painted on a
unit grid, one grid per Magic plane, with the same composition Magic applies
(polysilicon over diffusion forms a transistor; a contact occupies both the
active and the metal1 plane). The result is written as a Magic .mag file made
of disjoint rectangles, and a rule check covering the MOSIS SCMOS rules used
by the cell library is run before the file is written.
"""

from collections import defaultdict, deque
import math

# --------------------------------------------------------------------------
# Layer table: short name -> (Magic type name, planes it occupies)
# --------------------------------------------------------------------------
TYPES = {
    "nwell": ("nwell", ("well",)),
    "ndiff": ("ndiffusion", ("active",)),
    "pdiff": ("pdiffusion", ("active",)),
    "poly":  ("polysilicon", ("active",)),
    "ntr":   ("ntransistor", ("active",)),
    "ptr":   ("ptransistor", ("active",)),
    "ndc":   ("ndcontact", ("active", "metal1")),
    "pdc":   ("pdcontact", ("active", "metal1")),
    "pc":    ("polycontact", ("active", "metal1")),
    "psc":   ("psubstratepcontact", ("active", "metal1")),
    "nsc":   ("nsubstratencontact", ("active", "metal1")),
    "m1":    ("metal1", ("metal1",)),
    "m2c":   ("m2contact", ("metal1", "metal2")),
    "m2":    ("metal2", ("metal2",)),
}
CONTACTS = {"ndc", "pdc", "pc", "psc", "nsc", "m2c"}
DIFF = {"ndiff", "pdiff", "ntr", "ptr", "ndc", "pdc", "psc", "nsc"}
NDIFF = {"ndiff", "ntr", "ndc"}
PDIFF = {"pdiff", "ptr", "pdc"}
POLYG = {"poly", "ntr", "ptr", "pc"}
TRANS = {"ntr", "ptr"}
M1G = {"m1", "ndc", "pdc", "pc", "psc", "nsc", "m2c"}
M2G = {"m2", "m2c"}

WRITE_ORDER = ["nwell", "ndiff", "pdiff", "poly", "ntr", "ptr", "ndc", "pdc",
               "pc", "psc", "nsc", "m1", "m2c", "m2"]


class Layout:
    def __init__(self, name, bbox=None):
        self.name = name
        self.planes = {p: {} for p in ("well", "active", "metal1", "metal2")}
        self.labels = []          # (layer, rect, text, use, cls)
        self.bbox = bbox          # abutment box (x1, y1, x2, y2)
        self.errors = []

    # ------------------------------------------------------------------
    # painting
    # ------------------------------------------------------------------
    def paint(self, layer, x1, y1, x2, y2):
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        if layer not in TYPES:
            raise ValueError("unknown layer " + layer)
        for x in range(x1, x2):
            for y in range(y1, y2):
                self._paint_cell(layer, (x, y))

    def _paint_cell(self, layer, c):
        act, m1, m2, well = (self.planes[p] for p in ("active", "metal1", "metal2", "well"))
        if layer == "nwell":
            well[c] = "nwell"
        elif layer in ("ndiff", "pdiff"):
            cur = act.get(c)
            if cur is None or cur == layer:
                act[c] = layer
            elif cur == "poly":
                act[c] = "ntr" if layer == "ndiff" else "ptr"
            elif cur in CONTACTS or cur in TRANS:
                pass
            else:
                raise ValueError("%s over %s at %s in %s" % (layer, cur, c, self.name))
        elif layer == "poly":
            cur = act.get(c)
            if cur is None or cur == "poly":
                act[c] = "poly"
            elif cur == "ndiff":
                act[c] = "ntr"
            elif cur == "pdiff":
                act[c] = "ptr"
            elif cur in CONTACTS or cur in TRANS:
                pass
            else:
                raise ValueError("poly over %s at %s in %s" % (cur, c, self.name))
        elif layer in ("ndc", "pdc", "pc", "psc", "nsc"):
            act[c] = layer
            m1[c] = layer
        elif layer == "m1":
            cur = m1.get(c)
            if cur is None or cur == "m1":
                m1[c] = "m1"
        elif layer == "m2c":
            if m1.get(c) not in (None, "m1", "m2c"):
                raise ValueError("via over contact at %s in %s" % (c, self.name))
            m1[c] = "m2c"
            m2[c] = "m2c"
        elif layer == "m2":
            if m2.get(c) is None:
                m2[c] = "m2"

    def label(self, layer, x1, y1, x2, y2, text, use="signal", cls="bidirectional"):
        self.labels.append((layer, (x1, y1, x2, y2), text, use, cls))

    # ------------------------------------------------------------------
    # output
    # ------------------------------------------------------------------
    def cells_of(self, t):
        home = TYPES[t][1][0]
        return [c for c, v in self.planes[home].items() if v == t]

    @staticmethod
    def rects(cells):
        """Merge unit cells into disjoint rectangles (row runs, then merged downward)."""
        rows = defaultdict(list)
        for x, y in cells:
            rows[y].append(x)
        runs = defaultdict(list)          # y -> list of (x1, x2)
        for y, xs in rows.items():
            xs.sort()
            start = prev = xs[0]
            for x in xs[1:]:
                if x != prev + 1:
                    runs[y].append((start, prev + 1))
                    start = x
                prev = x
            runs[y].append((start, prev + 1))
        out = []
        open_rects = {}                   # (x1, x2) -> y1
        for y in sorted(runs) + [None]:
            cur = set(runs[y]) if y is not None else set()
            for key in list(open_rects):
                y1, ylast = open_rects[key]
                if key not in cur or y != ylast + 1:
                    out.append((key[0], y1, key[1], ylast + 1))
                    del open_rects[key]
            for key in cur:
                if key in open_rects:
                    open_rects[key] = (open_rects[key][0], y)
                else:
                    open_rects[key] = (y, y)
        return sorted(out, key=lambda r: (r[1], r[0]))

    def mag_text(self):
        lines = ["magic", "tech scmos", "timestamp 1730000000"]   # name declared inside SCN6M_SUBM.10.tech
        for t in WRITE_ORDER:
            cells = self.cells_of(t)
            if not cells:
                continue
            lines.append("<< %s >>" % TYPES[t][0])
            for r in self.rects(cells):
                lines.append("rect %d %d %d %d" % r)
        if self.labels:
            lines.append("<< labels >>")
            for i, (layer, r, text, use, cls) in enumerate(self.labels, 1):
                # rlabel layer sticky xbot ybot xtop ytop position(0 = centre) text
                lines.append("rlabel %s s %d %d %d %d 0 %s"
                             % ((TYPES[layer][0],) + tuple(r) + (text,)))
                lines.append("port %d nsew %s %s" % (i, use, cls))
        if self.bbox:
            lines.append("<< properties >>")
            lines.append("string FIXED_BBOX %d %d %d %d" % self.bbox)
        lines.append("<< end >>")
        return "\n".join(lines) + "\n"

    def write(self, path):
        with open(path, "w") as f:
            f.write(self.mag_text())

    # ------------------------------------------------------------------
    # rule check (subset of SCN6M_SUBM.10 rules, lambda units)
    # ------------------------------------------------------------------
    def check(self):
        e = self.errors = []
        act, m1, m2, well = (self.planes[p] for p in ("active", "metal1", "metal2", "well"))

        def cells(plane, group):
            return {c for c, v in plane.items() if v in group}

        nw = set(well)
        diff, poly = cells(act, DIFF), cells(act, POLYG)
        nd, pd = cells(act, NDIFF), cells(act, PDIFF)
        trans = cells(act, TRANS)
        dcont = cells(act, {"ndc", "pdc", "psc", "nsc"})
        pcont = cells(act, {"pc"})
        psc, nsc = cells(act, {"psc"}), cells(act, {"nsc"})
        purepoly = cells(act, {"poly"})
        puredif = cells(act, {"ndiff", "pdiff"})
        metal1, metal2 = set(m1), set(m2)

        self._width(e, nw, 12, "nwell width < 12")
        self._width(e, diff, 3, "diffusion width < 3")
        self._width(e, poly, 2, "poly width < 2")
        self._width(e, metal1, 3, "metal1 width < 3")
        self._width(e, metal2, 3, "metal2 width < 3")
        for t in ("ndc", "pdc", "pc", "psc", "nsc", "m2c"):
            self._width(e, set(self.cells_of(t)), 4, "%s width < 4" % t)

        self._space_same(e, diff, 3, "diffusion spacing < 3")
        self._space_same(e, poly, 3, "poly spacing < 3")
        self._space_same(e, metal1, 3, "metal1 spacing < 3")
        self._space_same(e, metal2, 3, "metal2 spacing < 3")
        self._space(e, nd, pd, 12, "ndiff to pdiff < 12")
        self._space(e, nd, nw, 6, "nwell to ndiff < 6")
        self._space(e, psc, nw, 3, "nwell to p-substrate contact < 3")
        self._space(e, nd - psc, psc, 4, "ndiff to p-substrate contact < 4", touching_ok=True)
        self._space(e, pd, nsc, 4, "pdiff to n-well contact < 4", touching_ok=True)
        self._space(e, trans, psc | nsc, 3, "transistor to substrate contact < 3")
        self._space(e, trans, dcont, 1, "gate to diffusion contact < 1")
        self._space(e, pcont, diff, 1, "diffusion to poly contact < 1")
        self._space(e, pcont, dcont, 2, "poly contact to diffusion contact < 2")
        self._space(e, purepoly, puredif | dcont, 1, "poly to diffusion < 1", edge_only=True)
        self._space(e, puredif | trans, dcont, 4,
                    "diffusion to unrelated diffusion contact < 4", touching_ok=True)
        self._enclose(e, pd, nw, 6, "nwell overlap of pdiff < 6")
        self._enclose(e, nsc, nw, 3, "nwell overlap of n-well contact < 3")
        self._gate_rules(e, act)
        return e

    @staticmethod
    def _width(e, region, w, msg):
        """Every cell of the region must lie inside a w x w square fully in the region."""
        if not region:
            return
        xs = [c[0] for c in region]
        ys = [c[1] for c in region]
        x0, y0 = min(xs), min(ys)
        nx, ny = max(xs) - x0 + 1, max(ys) - y0 + 1
        # prefix sums of occupancy
        ps = [[0] * (ny + 1) for _ in range(nx + 1)]
        for i in range(nx):
            col, prev = ps[i + 1], ps[i]
            run = 0
            for j in range(ny):
                run += (x0 + i, y0 + j) in region
                col[j + 1] = prev[j + 1] + run
        # mark cells covered by fully occupied w x w squares (2-D difference array)
        mark = [[0] * (ny + 2) for _ in range(nx + 2)]
        for i in range(nx - w + 1):
            for j in range(ny - w + 1):
                tot = ps[i + w][j + w] - ps[i][j + w] - ps[i + w][j] + ps[i][j]
                if tot == w * w:
                    mark[i][j] += 1
                    mark[i + w][j] -= 1
                    mark[i][j + w] -= 1
                    mark[i + w][j + w] += 1
        for i in range(nx + 1):
            for j in range(ny + 1):
                if i:
                    mark[i][j] += mark[i - 1][j]
                if j:
                    mark[i][j] += mark[i][j - 1]
                if i and j:
                    mark[i][j] -= mark[i - 1][j - 1]
        bad = [(x0 + i, y0 + j) for i in range(nx) for j in range(ny)
               if (x0 + i, y0 + j) in region and mark[i][j] <= 0]
        if bad:
            e.append("%s near %s (%d cells)" % (msg, min(bad), len(bad)))

    @staticmethod
    def _components(region):
        comp, n = {}, 0
        for c in region:
            if c in comp:
                continue
            n += 1
            q = deque([c])
            comp[c] = n
            while q:
                x, y = q.popleft()
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (x + d[0], y + d[1])
                    if nb in region and nb not in comp:
                        comp[nb] = n
                        q.append(nb)
        return comp

    @staticmethod
    def _dist(a, b):
        gx = max(0, abs(a[0] - b[0]) - 1)
        gy = max(0, abs(a[1] - b[1]) - 1)
        return math.hypot(gx, gy)

    def _space_same(self, e, region, s, msg):
        comp = self._components(region)
        bad = None
        r = int(math.ceil(s)) + 1
        for c in region:
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nb = (c[0] + dx, c[1] + dy)
                    if nb in region and comp[nb] != comp[c] and self._dist(c, nb) < s:
                        bad = (c, nb)
                        break
                if bad:
                    break
            if bad:
                break
        if bad:
            e.append("%s between %s and %s" % (msg, bad[0], bad[1]))

    def _space(self, e, a, b, s, msg, touching_ok=False, edge_only=False):
        r = int(math.ceil(s)) + 1
        if touching_ok:
            comp = self._components(a | b)
        for c in a:
            nbrs = ((1, 0), (-1, 0), (0, 1), (0, -1)) if edge_only else \
                   [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)]
            for dx, dy in nbrs:
                nb = (c[0] + dx, c[1] + dy)
                if nb == c or nb not in b or nb in a:
                    continue
                if touching_ok and comp[nb] == comp[c]:
                    continue
                if edge_only or self._dist(c, nb) < s:
                    e.append("%s between %s and %s" % (msg, c, nb))
                    return

    @staticmethod
    def _enclose(e, inner, outer, s, msg):
        for (x, y) in inner:
            for dx in range(-s, s + 1):
                for dy in range(-s, s + 1):
                    if (x + dx, y + dy) not in outer:
                        e.append("%s near %s" % (msg, (x, y)))
                        return

    @staticmethod
    def _gate_rules(e, act):
        """Poly must extend 2 beyond each gate, diffusion 3 beyond each gate."""
        for c, v in act.items():
            if v not in TRANS:
                continue
            x, y = c
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = act.get((x + d[0], y + d[1]))
                if nb in TRANS:
                    continue
                if nb == "poly":      # poly side: need 2 cells of poly
                    if act.get((x + 2 * d[0], y + 2 * d[1])) not in ("poly", "pc"):
                        e.append("poly overhang of gate < 2 near %s" % (c,))
                        return
                elif nb in DIFF:      # diffusion side: need 3 cells of diffusion
                    for k in (2, 3):
                        if act.get((x + k * d[0], y + k * d[1])) not in DIFF:
                            e.append("diffusion overhang of gate < 3 near %s" % (c,))
                            return
                else:
                    e.append("gate edge touches %s near %s" % (nb, c))
                    return
