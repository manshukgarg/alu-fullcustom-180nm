"""Parametric standard-cell layout generator (SCN6M_SUBM.10, lambda units).

A cell is described by its transistor netlist and a column plan:

    ("D", nnet, pnet)    diffusion node column (NMOS row net, PMOS row net; None = empty)
    ("G", ngate, pgate)  gate column (gate signal in each row; None = no transistor)
    ("B",)               diffusion break between strips

Nets written as "x#1", "x#2" are separate nodes that the netlist calls "x"
(used when a series stack is folded into two parallel stacks).

The generator places the devices on the cell template of template.py, draws
rails, taps and gate stubs, routes every signal net with a maze router on the
lambda grid (polysilicon, metal1 and metal2, with poly contacts and vias), and
returns a maglib.Layout together with the device list it intended to build.
Every net that is a cell pin gets a 4 x 4 lambda metal1 pad on which a via can
land, so the cell can be connected from metal2 above.
"""

import heapq
import itertools
import math

import numpy as np

from maglib import Layout
from template import H, RAIL, YN0, YP1, NW_Y0, NW_Y1, WN_MAX, WP_MAX, EDGE

# routing grid in y covers the whole cell including the rails
Y0, Y1 = -6, H + 6
POLY, M1, M2 = 0, 1, 2
WIRE = {POLY: 2, M1: 3, M2: 3}               # wire widths
STEP_COST = {POLY: 1.5, M1: 1.0, M2: 1.6}     # cost per lambda of wire
PC_COST, V1_COST, BEND_COST = 18, 14, 3
SPACE = {POLY: 3, M1: 3, M2: 3}               # same-layer spacing


def base(net):
    return net.split("#")[0] if net else net


def spice_name(net):
    return net.replace("#", "_")


class PlanError(Exception):
    pass


class RouteError(Exception):
    pass


def _shift(m, dx, dy):
    """out[x, y] = m[x + dx, y + dy] (False outside)."""
    out = np.zeros_like(m)
    nx, ny = m.shape
    xs, xd = (slice(dx, nx), slice(0, nx - dx)) if dx >= 0 else (slice(0, nx + dx), slice(-dx, nx))
    ys, yd = (slice(dy, ny), slice(0, ny - dy)) if dy >= 0 else (slice(0, ny + dy), slice(-dy, ny))
    out[xd, yd] = m[xs, ys]
    return out


def notch_cells(m, s=3):
    """Empty cells that sit in a gap narrower than s between parts of mask m."""
    fill = np.zeros_like(m)
    e = ~m
    for dx, dy in ((1, 0), (0, 1)):
        a1, b1 = _shift(m, -dx, -dy), _shift(m, dx, dy)
        a2, b2 = _shift(m, -2 * dx, -2 * dy), _shift(m, 2 * dx, 2 * dy)
        fill |= e & a1 & b1                                   # gap of one cell
        fill |= e & a1 & ~b1 & b2                             # first cell of a two-cell gap
        fill |= e & ~a1 & a2 & b1                             # second cell of a two-cell gap
    for sx in (1, -1):
        for sy in (1, -1):
            corner = m & ~_shift(m, sx, 0) & ~_shift(m, 0, sy)
            if not corner.any():
                continue
            for i in range(1, s + 1):
                for j in range(1, s + 1):
                    if math.hypot(i - 1, j - 1) >= s:
                        continue
                    hit = corner & _shift(m, i * sx, j * sy)
                    for cx, cy in np.argwhere(hit):
                        xa, xb = sorted((cx, cx + i * sx))
                        ya, yb = sorted((cy, cy + j * sy))
                        fill[xa:xb + 1, ya:yb + 1] = True
    return fill & e


# ----------------------------------------------------------------------------
# integral-image helpers
# ----------------------------------------------------------------------------
def window_any(mask, a, b, c, d):
    """out[x, y] = any(mask[x+a : x+b, y+c : y+d]); cells outside the array count as empty."""
    nx, ny = mask.shape
    S = np.zeros((nx + 1, ny + 1), dtype=np.int32)
    S[1:, 1:] = mask.astype(np.int32).cumsum(0).cumsum(1)
    xs, ys = np.arange(nx), np.arange(ny)
    X1, X2 = np.clip(xs + a, 0, nx), np.clip(xs + b, 0, nx)
    Y1_, Y2_ = np.clip(ys + c, 0, ny), np.clip(ys + d, 0, ny)
    tot = S[np.ix_(X2, Y2_)] - S[np.ix_(X1, Y2_)] - S[np.ix_(X2, Y1_)] + S[np.ix_(X1, Y1_)]
    return tot > 0


# ----------------------------------------------------------------------------
# cell builder
# ----------------------------------------------------------------------------
class CellBuilder:
    def __init__(self, name, devices, plan, inputs, outputs, extra_space=0, spread=0):
        """devices: list of (model, drain, gate, source, width_lambda)."""
        self.name = name
        self.devices = devices
        self.plan = plan
        self.inputs = inputs
        self.outputs = outputs
        self.pins = inputs + outputs
        self.extra_space = extra_space
        self.spread = spread
        self.shapes = []               # (layer, x1, y1, x2, y2, net)
        self.labels = []               # (x1, y1, x2, y2, text, use, cls)
        self.fingers = []              # devices as laid out: (model, d, g, s, w)
        self.terms = {}                # net -> list of terminals
        self.pads = {}                 # pin -> (x1, y1, x2, y2) metal1 pad for a via
        self._lf_cache = {}
        self.patience = 10
        self.reserve = []              # (layer, x1, y1, x2, y2, net): terminal access kept free
        self.routed = set()
        self.width = None

    # -------------------------------------------------------------- placement
    def _match_devices(self):
        """Assign a netlist device (and finger width) to every gate in the plan."""
        cols = self.plan
        slots = []                     # (column index, row, gate, left net, right net)
        for i, col in enumerate(cols):
            if col[0] != "G":
                continue
            for row in (0, 1):
                g = col[1 + row]
                if g is None:
                    continue
                left = cols[i - 1][1 + row] if i > 0 and cols[i - 1][0] == "D" else None
                right = cols[i + 1][1 + row] if i + 1 < len(cols) and cols[i + 1][0] == "D" else None
                if left is None or right is None:
                    raise PlanError("%s: gate %s in column %d lacks a diffusion node on both sides"
                                    % (self.name, g, i))
                slots.append((i, row, g, left, right))
        users = {}
        for s in slots:
            i, row, g, left, right = s
            model = "nfet" if row == 0 else "pfet"
            cand = [k for k, d in enumerate(self.devices)
                    if d[0] == model and d[2] == base(g)
                    and {d[1], d[3]} == {base(left), base(right)}]
            if not cand:
                raise PlanError("%s: no %s with gate %s between %s and %s"
                                % (self.name, model, g, left, right))
            users.setdefault(cand[0], []).append(s)
        missing = [d for k, d in enumerate(self.devices) if k not in users]
        if missing:
            raise PlanError("%s: devices not placed: %s" % (self.name, missing))
        self.gate_w = {}               # (column, row) -> width
        for k, ss in users.items():
            model, d, g, s, w = self.devices[k]
            nf = len(ss)
            ws = [w // nf + (1 if j < w % nf else 0) for j in range(nf)]
            for (i, row, gg, left, right), wf in zip(ss, ws):
                lim = WN_MAX if row == 0 else WP_MAX
                if wf > lim:
                    raise PlanError("%s: finger %s of width %d exceeds the row limit %d"
                                    % (self.name, gg, wf, lim))
                if wf < 4:
                    raise PlanError("%s: finger %s of width %d below 4" % (self.name, gg, wf))
                self.gate_w[(i, row)] = wf
                self.fingers.append((model, spice_name(left), spice_name(gg), spice_name(right), wf))

    def _contacted(self):
        """A diffusion node needs a contact unless it only joins two gates of one strip."""
        count = {}
        for col in self.plan:
            if col[0] == "D":
                for row in (0, 1):
                    if col[1 + row] is not None:
                        count[col[1 + row]] = count.get(col[1 + row], 0) + 1
        gates = {c[1 + r] for c in self.plan if c[0] == "G" for r in (0, 1)}
        gates = {base(g) for g in gates if g}
        cont = {}
        for i, col in enumerate(self.plan):
            if col[0] != "D":
                continue
            for row in (0, 1):
                net = col[1 + row]
                if net is None:
                    continue
                between = (0 < i < len(self.plan) - 1 and self.plan[i - 1][0] == "G"
                           and self.plan[i + 1][0] == "G"
                           and self.plan[i - 1][1 + row] is not None
                           and self.plan[i + 1][1 + row] is not None)
                internal = (count[net] == 1 and between and base(net) not in gates
                            and base(net) not in self.pins and base(net) not in ("vdd", "gnd"))
                cont[(i, row)] = not internal
        return cont

    def _place(self):
        self._match_devices()
        cont = self._contacted()
        x = EDGE + self.extra_space
        self.colx = {}
        self.gap = {}                  # gate column -> (left gap, right gap) of diffusion
        prev = None
        n = len(self.plan)

        def wide(j):
            c = self.plan[j]
            return c[0] == "G" and c[1] and c[2] and c[1] != c[2]
        for i, col in enumerate(self.plan):
            kind = col[0]
            if kind == "B":
                x += 4
                prev = "B"
                continue
            if kind == "D":
                anyc = any(cont.get((i, r)) for r in (0, 1))
                if prev == "G" and anyc:
                    x += 1 + (self.spread if wide(i - 1) else 0)
                w = 4 if anyc else 3
                self.colx[i] = (x, x + w, anyc)
                x += w
            else:
                lg = 0
                if prev == "D" and self.colx[i - 1][2]:
                    lg = 1 + (self.spread if wide(i) else 0)
                x += lg
                rg = 0
                if i + 1 < n and self.plan[i + 1][0] == "D":
                    rg = 1 + (self.spread if wide(i) else 0)
                self.gap[i] = (lg, rg)
                self.colx[i] = (x, x + 2, False)
                x += 2
            prev = kind
        self.width = x + EDGE + self.extra_space
        self.cont = cont

    def _row_extent(self, row, w):
        """(y1, y2) of a diffusion of width w in the given row."""
        return (YN0, YN0 + w) if row == 0 else (YP1 - w, YP1)

    def _draw_devices(self):
        S = self.shapes
        diff = ("ndiff", "pdiff")
        dc = ("ndc", "pdc")
        n = len(self.plan)
        for i, col in enumerate(self.plan):
            if col[0] == "G":
                x1, x2, _ = self.colx[i]
                for row in (0, 1):
                    g = col[1 + row]
                    if g is None:
                        continue
                    w = self.gate_w[(i, row)]
                    y1, y2 = self._row_extent(row, w)
                    S.append((diff[row], x1, y1, x2, y2, None))
                    # gaps between the gate and contacted neighbours: diffusion of the gate's width
                    lg, rg = self.gap.get(i, (1, 1))
                    if 0 <= i - 1 and self.plan[i - 1][0] == "D" and self.colx[i - 1][2]:
                        S.append((diff[row], x1 - lg, y1, x1, y2, None))
                    if i + 1 < n and self.plan[i + 1][0] == "D" and self.colx[i + 1][2]:
                        S.append((diff[row], x2, y1, x2 + rg, y2, None))
                    # gate stub: 2 beyond the diffusion on both sides
                    S.append(("poly", x1, y1 - 2, x2, y2 + 2, base(g)))
                    if row == 0:
                        self.terms.setdefault(base(g), []).append(("gate", x1, y2 + 1, 0))
                        self.reserve.append(("poly", x1, y2 + 1, x2, y2 + 6, base(g)))
                    else:
                        self.terms.setdefault(base(g), []).append(("gate", x1, y1 - 3, 1))
                        self.reserve.append(("poly", x1, y1 - 7, x2, y1 - 1, base(g)))
            elif col[0] == "D":
                x1, x2, anyc = self.colx[i]
                for row in (0, 1):
                    net = col[1 + row]
                    if net is None:
                        continue
                    ws = [self.gate_w[(j, row)] for j in (i - 1, i + 1)
                          if 0 <= j < n and self.plan[j][0] == "G" and (j, row) in self.gate_w]
                    if not ws:
                        raise PlanError("%s: diffusion node %s in column %d has no transistor"
                                        % (self.name, net, i))
                    wmax, wmin = max(ws), min(ws)
                    if not self.cont[(i, row)]:
                        if wmax != wmin:
                            raise PlanError("%s: uncontacted node %s joins widths %d and %d"
                                            % (self.name, net, wmin, wmax))
                        y1, y2 = self._row_extent(row, wmax)
                        S.append((diff[row], x1, y1, x2, y2, spice_name(net)))
                        continue
                    # diffusion as tall as the widest neighbour, contact as tall as the narrowest
                    y1, y2 = self._row_extent(row, wmax)
                    S.append((diff[row], x1, y1, x2, y2, spice_name(net)))
                    cy1, cy2 = self._row_extent(row, wmin)
                    S.append((dc[row], x1, cy1, x2, cy2, spice_name(net)))
                    b = spice_name(net)
                    if b == "gnd" and row == 0:
                        S.append(("m1", x1, RAIL, x2, cy1, "gnd"))
                    elif b == "vdd" and row == 1:
                        S.append(("m1", x1, cy2, x2, H - RAIL, "vdd"))
                    elif b in ("gnd", "vdd"):
                        raise PlanError("%s: %s in the wrong row" % (self.name, b))
                    else:
                        self.terms.setdefault(b, []).append(("cont", x1, cy1, x2, cy2))
                        if row == 0:
                            self.reserve.append(("m1", x1, cy2, x2, cy2 + 5, b))
                        else:
                            self.reserve.append(("m1", x1, cy1 - 5, x2, cy1, b))

    def _draw_frame(self):
        S, W = self.shapes, self.width
        S.append(("m1", 0, -RAIL, W, RAIL, "gnd"))
        S.append(("m1", 0, H - RAIL, W, H + RAIL, "vdd"))
        S.append(("nwell", -6, NW_Y0, W + 6, NW_Y1, None))
        x = 3
        while x + 4 <= W - 3:
            S.append(("psc", x, -2, x + 4, 2, "gnd"))
            S.append(("nsc", x, H - 2, x + 4, H + 2, "vdd"))
            x += 12
        self.labels.append((0, H - RAIL, EDGE, H + RAIL, "vdd", "power", "bidirectional"))
        self.labels.append((0, -RAIL, EDGE, RAIL, "gnd", "ground", "bidirectional"))

    # -------------------------------------------------------------- routing maps
    def _raster(self, shapes):
        """Arrays of the routing grid: net id per cell for poly, metal1, metal2; masks for the rest."""
        W = self.width
        ny = Y1 - Y0
        mp = dict(poly=np.zeros((W, ny), dtype=np.int32), m1=np.zeros((W, ny), dtype=np.int32),
                  m2=np.zeros((W, ny), dtype=np.int32), act=np.zeros((W, ny), dtype=bool),
                  dcont=np.zeros((W, ny), dtype=bool), cut1=np.zeros((W, ny), dtype=bool),
                  via1=np.zeros((W, ny), dtype=bool))
        for layer, x1, y1, x2, y2, net in shapes:
            xa, xb = max(0, x1), min(W, x2)
            ya, yb = max(0, y1 - Y0), min(ny, y2 - Y0)
            if xa >= xb or ya >= yb:
                continue
            nid = self.netid.get(net, -1) if net else -1
            sl = (slice(xa, xb), slice(ya, yb))
            if layer in ("poly", "pc"):
                mp["poly"][sl] = nid
            if layer in ("ndiff", "pdiff", "ndc", "pdc", "psc", "nsc"):
                mp["act"][sl] = True
            if layer in ("ndc", "pdc", "psc", "nsc"):
                mp["dcont"][sl] = True
            if layer in ("m1", "ndc", "pdc", "pc", "psc", "nsc", "m2c"):
                mp["m1"][sl] = nid
            if layer in ("m2", "m2c"):
                mp["m2"][sl] = nid
            if layer in ("ndc", "pdc", "pc", "psc", "nsc"):
                mp["cut1"][sl] = True
            if layer == "m2c":
                mp["via1"][sl] = True
        return mp

    def _maps(self):
        self.mp = self._raster(self.all_shapes())

    def all_shapes(self):
        out = list(self.shapes)
        for net, shp in self.routes.items():
            out.extend(x for x in shp if x[0] != "m2k")
        return out

    def _inside(self, w):
        W = self.width
        xs = np.arange(W)[:, None]
        ys = np.arange(Y1 - Y0)[None, :] + Y0
        return (xs >= EDGE) & (xs + w <= W - EDGE) & (ys >= -RAIL) & (ys + w <= H + RAIL)

    def _legal_fixed(self, nid):
        """Hard legality against the fixed geometry (devices, stubs, rails, taps)."""
        cache = self.__dict__.setdefault("_lf_cache", {})
        if nid in cache:
            return cache[nid]
        cache[nid] = self._legal_fixed_compute(nid)
        return cache[nid]

    def _legal_fixed_compute(self, nid):
        mp = self.fx
        fp = (mp["poly"] != 0) & (mp["poly"] != nid)
        f1 = (mp["m1"] != 0) & (mp["m1"] != nid)
        f2 = (mp["m2"] != 0) & (mp["m2"] != nid)
        L = {}
        L[POLY] = (~window_any(fp, -3, 5, -3, 5) & ~window_any(mp["act"], -1, 3, -1, 3)
                   & self._inside(2))
        L[M1] = ~window_any(f1, -3, 6, -3, 6) & self._inside(3)
        L[M2] = ~window_any(f2, -3, 6, -3, 6) & self._inside(3)
        L["pc"] = (~window_any(fp, -3, 7, -3, 7) & ~window_any(mp["act"], -1, 5, -1, 5)
                   & ~window_any(mp["dcont"], -2, 6, -2, 6) & ~window_any(f1, -3, 7, -3, 7)
                   & self._inside(4))
        L["v1"] = (~window_any(f1, -3, 7, -3, 7) & ~window_any(f2, -3, 7, -3, 7)
                   & ~window_any(mp["cut1"], 0, 4, 0, 4) & self._inside(4))
        return L

    def _route_masks(self, shapes):
        """Boolean masks (poly, m1, m2, cut) of a route; pads keep metal2 free as well."""
        W, ny = self.width, Y1 - Y0
        m = {k: np.zeros((W, ny), dtype=bool) for k in ("poly", "m1", "m2", "cut")}
        for layer, x1, y1, x2, y2, net in shapes:
            xa, xb = max(0, x1), min(W, x2)
            ya, yb = max(0, y1 - Y0), min(ny, y2 - Y0)
            if xa >= xb or ya >= yb:
                continue
            sl = (slice(xa, xb), slice(ya, yb))
            if layer in ("poly", "pc"):
                m["poly"][sl] = True
            if layer in ("m1", "pc", "m2c"):
                m["m1"][sl] = True
            if layer in ("m2", "m2c", "m2k"):
                m["m2"][sl] = True
            if layer in ("pc", "m2c"):
                m["cut"][sl] = True
        return m

    def _set_route(self, net, shapes):
        old = self.rmask.get(net)
        if old is not None:
            for k in self.rtotal:
                self.rtotal[k] -= old[k]
        self.routes[net] = shapes
        new = self._route_masks(shapes)
        self.rmask[net] = new
        for k in self.rtotal:
            self.rtotal[k] += new[k]

    def _soft(self, net, hist, pres):
        """Congestion costs from the routes of the other nets (plus history)."""
        own = self.rmask.get(net)
        tot = self.rtotal
        if own is not None:
            op = (tot["poly"] - own["poly"]) > 0
            o1 = (tot["m1"] - own["m1"]) > 0
            o2 = (tot["m2"] - own["m2"]) > 0
            cut = (tot["cut"] - own["cut"]) > 0
        else:
            op, o1, o2, cut = tot["poly"] > 0, tot["m1"] > 0, tot["m2"] > 0, tot["cut"] > 0
        C = {}
        C[POLY] = pres * window_any(op, -3, 5, -3, 5) + hist[POLY]
        C[M1] = pres * window_any(o1, -3, 6, -3, 6) + hist[M1]
        C[M2] = pres * window_any(o2, -3, 6, -3, 6) + hist[M2]
        C["pc"] = pres * (window_any(op, -3, 7, -3, 7) + window_any(o1, -3, 7, -3, 7)
                          + window_any(cut, 0, 4, 0, 4))
        C["v1"] = pres * (window_any(o1, -3, 7, -3, 7) + window_any(o2, -3, 7, -3, 7)
                          + window_any(cut, 0, 4, 0, 4))
        return C

    # -------------------------------------------------------------- router
    def _terminal_states(self, t):
        """Grid states (layer, x, y) from which a wire touches terminal t."""
        if t[0] == "cont":
            _, x1, y1, x2, y2 = t
            return [(M1, x, y) for x in range(x1, x2 - 2) for y in range(y1, y2 - 2)]
        _, gx, y, row = t
        return [(POLY, gx, y)]

    def _search(self, L, C, sources, targets, groups=None, accept=None, limit=2000000, own_vias=(),
                pad=None):
        """A* from any source state to any target state; returns the path (list of states)."""
        W = self.width
        if pad is not None:
            pad_ok, pad_cost = pad
            targets = [(3, int(c[0]), int(c[1]) + Y0) for c in np.argwhere(pad_ok)]
        tset = set(targets)
        if not tset:
            raise RouteError("no target")
        boxes = []
        for grp in (groups or [targets]):
            boxes.append((min(t[1] for t in grp), max(t[1] for t in grp),
                          min(t[2] for t in grp), max(t[2] for t in grp)))

        def h(x, y):
            best = 1 << 30
            for bx1, bx2, by1, by2 in boxes:
                dx = bx1 - x if x < bx1 else (x - bx2 if x > bx2 else 0)
                dy = by1 - y if y < by1 else (y - by2 if y > by2 else 0)
                if dx + dy < best:
                    best = dx + dy
            return best

        Lp, L1, L2, Lpc, Lv = L[POLY], L[M1], L[M2], L["pc"], L["v1"]
        layer_ok = {POLY: Lp, M1: L1, M2: L2}
        Cl = {POLY: C[POLY], M1: C[M1], M2: C[M2]}
        Cpc, Cv = C["pc"], C["v1"]
        heap, g, parent, vias = [], {}, {}, {}
        cnt = itertools.count()
        own = tuple(own_vias)
        for s_ in sources:
            key = (s_[0], s_[1], s_[2], 4)
            if key in g:
                continue
            g[key] = 0.0
            parent[key] = None
            vias[key] = own
            heapq.heappush(heap, (h(s_[1], s_[2]), next(cnt), 0.0, key))
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
        found, expanded = None, 0
        while heap:
            f, _, gc, key = heapq.heappop(heap)
            if g.get(key, 1e18) < gc:
                continue
            layer, x, y, d = key
            if (layer, x, y) in tset and (accept is None or accept(key, vias[key])):
                found = key
                break
            if layer == 3:
                continue
            expanded += 1
            if expanded > limit:
                break
            ok, cl, sc = layer_ok[layer], Cl[layer], STEP_COST[layer]
            kv = vias[key]
            for k, (dx, dy) in enumerate(dirs):
                nx_, ny_ = x + dx, y + dy
                if not (0 <= nx_ < W and Y0 <= ny_ < Y1) or not ok[nx_, ny_ - Y0]:
                    continue
                cost = gc + sc + cl[nx_, ny_ - Y0] + (BEND_COST if d not in (4, k) else 0)
                nk = (layer, nx_, ny_, k)
                if cost < g.get(nk, 1e18):
                    g[nk] = cost
                    parent[nk] = key
                    vias[nk] = kv
                    heapq.heappush(heap, (cost + h(nx_, ny_), next(cnt), cost, nk))

            def clear(ax, ay):
                return all(abs(ax - rx) >= 4 or abs(ay - ry) >= 4 for rx, ry in kv)
            moves = []
            if layer == POLY:
                ax, ay = x - 1, y - 1
                if (0 <= ax < W and Y0 <= ay < Y1 and Lpc[ax, ay - Y0] and L1[ax, ay - Y0]
                        and clear(ax, ay)):
                    moves.append(((M1, ax, ay, 4), PC_COST + Cpc[ax, ay - Y0], (ax, ay)))
            elif layer == M1:
                if pad is not None and pad_ok[x, y - Y0] and clear(x, y):
                    moves.append(((3, x, y, 4), 2.0 + pad_cost[x, y - Y0], None))
                if (Lpc[x, y - Y0] and x + 1 < W and y + 1 < Y1 and Lp[x + 1, y + 1 - Y0]
                        and clear(x, y)):
                    moves.append(((POLY, x + 1, y + 1, 4), PC_COST + Cpc[x, y - Y0], (x, y)))
                if Lv[x, y - Y0] and L2[x, y - Y0] and clear(x, y):
                    moves.append(((M2, x, y, 4), V1_COST + Cv[x, y - Y0], (x, y)))
            else:
                if Lv[x, y - Y0] and L1[x, y - Y0] and clear(x, y):
                    moves.append(((M1, x, y, 4), V1_COST + Cv[x, y - Y0], (x, y)))
            for nk, c, anchor in moves:
                cost = gc + c
                if cost < g.get(nk, 1e18):
                    g[nk] = cost
                    parent[nk] = key
                    vias[nk] = kv + (anchor,) if anchor is not None else kv
                    heapq.heappush(heap, (cost + h(nk[1], nk[2]), next(cnt), cost, nk))
        if found is None:
            raise RouteError("no path")
        path = []
        k = found
        while k is not None:
            path.append(k[:3])
            k = parent[k]
        return path[::-1]

    def _path_shapes(self, path, net):
        out = []
        for i, (layer, x, y) in enumerate(path):
            if layer == 3:
                continue
            w = WIRE[layer]
            out.append((("poly", "m1", "m2")[layer], x, y, x + w, y + w, net))
            if i:
                pl, px, py = path[i - 1]
                if {pl, layer} == {POLY, M1}:
                    ax, ay = (px, py) if pl == M1 else (x, y)
                    out.append(("pc", ax, ay, ax + 4, ay + 4, net))
                    out.append(("poly", ax, ay, ax + 4, ay + 4, net))
                elif {pl, layer} == {M1, M2}:
                    out.append(("m2c", x, y, x + 4, y + 4, net))
        return out

    @staticmethod
    def _via_anchors(shapes):
        return [(x[1], x[2]) for x in shapes if x[0] in ("pc", "m2c")]

    def _route_one(self, net, hist, pres):
        """Route one net against the fixed geometry, paying for overlap with other routes."""
        nid = self.netid[net]
        L = self._legal_fixed(nid)
        C = self._soft(net, hist, pres)
        groups = [self._terminal_states(t) for t in self.terms.get(net, [])]
        shapes = []
        if not groups:
            return shapes
        tree = list(groups[0])
        todo = groups[1:]
        while todo:
            targets = [s_ for grp in todo for s_ in grp]
            path = self._search(L, C, tree, targets, groups=todo,
                                own_vias=self._via_anchors(shapes))
            end = path[-1]
            for grp in [g_ for g_ in todo if end in g_]:
                tree.extend(grp)
            todo = [grp for grp in todo if end not in grp]
            shapes.extend(self._path_shapes(path, net))
            tree.extend(path)
        self.trees[net] = tree
        if net in self.pins:
            fx = self.fx
            pad_ok = (L["v1"] & L[M1] & ~window_any(fx["cut1"], 0, 4, 0, 4))
            tot, own = self.rtotal, self.rmask.get(net)
            o1 = (tot["m1"] - (own["m1"] if own is not None else 0)) > 0
            o2 = (tot["m2"] - (own["m2"] if own is not None else 0)) > 0
            ys = np.arange(Y1 - Y0)[None, :] + Y0
            pad_cost = (pres * (window_any(o1, -3, 7, -3, 7) + window_any(o2, -3, 7, -3, 7))
                        + 0.05 * np.abs(ys - (NW_Y0 - 3)) + np.zeros((self.width, 1)))
            path = self._search(L, C, tree, [], own_vias=self._via_anchors(shapes),
                                pad=(pad_ok, pad_cost))
            _, x, y = path[-1]
            shapes.extend(self._path_shapes(path[:-1], net))
            shapes.append(("m1", x, y, x + 4, y + 4, net))
            shapes.append(("m2k", x, y, x + 4, y + 4, net))
            self.pads[net] = ("m1", x, y, x + 4, y + 4)
        return shapes

    def _legal_all(self, nid):
        """Hard legality against every shape already in the cell (used after negotiation)."""
        mp = self._raster(self.all_shapes())
        fp = (mp["poly"] != 0) & (mp["poly"] != nid)
        f1 = (mp["m1"] != 0) & (mp["m1"] != nid)
        f2 = (mp["m2"] != 0) & (mp["m2"] != nid)
        L = {}
        L[POLY] = (~window_any(fp, -3, 5, -3, 5) & ~window_any(mp["act"], -1, 3, -1, 3)
                   & self._inside(2))
        L[M1] = ~window_any(f1, -3, 6, -3, 6) & self._inside(3)
        L[M2] = ~window_any(f2, -3, 6, -3, 6) & self._inside(3)
        L["pc"] = (~window_any(fp, -3, 7, -3, 7) & ~window_any(mp["act"], -1, 5, -1, 5)
                   & ~window_any(mp["dcont"], -2, 6, -2, 6) & ~window_any(f1, -3, 7, -3, 7)
                   & ~window_any(mp["via1"], 0, 4, 0, 4) & self._inside(4))
        L["v1"] = (~window_any(f1, -3, 7, -3, 7) & ~window_any(f2, -3, 7, -3, 7)
                   & ~window_any(mp["cut1"], 0, 4, 0, 4) & self._inside(4))
        return L, mp

    def _pads(self):
        """Give every pin a 4 x 4 access pad: plain metal1 that can take a via, or metal2."""
        for net in self.pins:
            if net in self.pads:
                continue
            nid = self.netid[net]
            for attempt in range(3):
                L, mp = self._legal_all(nid)
                o1 = mp["m1"] == nid
                o2 = mp["m2"] == nid
                cut = mp["cut1"] | mp["via1"]
                full1 = ~window_any(~o1, 0, 4, 0, 4)
                touch = window_any(o1, -1, 5, 0, 4) | window_any(o1, 0, 4, -1, 5)
                c1 = np.argwhere(L["v1"] & touch & ~window_any(cut, 0, 4, 0, 4))
                mid = (NW_Y0 - 3) - Y0
                if len(c1):
                    i = min(range(len(c1)), key=lambda i: (not full1[c1[i][0], c1[i][1]],
                                                           abs(int(c1[i][1]) - mid), int(c1[i][0])))
                    x, y = int(c1[i][0]), int(c1[i][1]) + Y0
                    self._set_route(net, self.routes[net] + [("m1", x, y, x + 4, y + 4, net)])
                    self.pads[net] = ("m1", x, y, x + 4, y + 4)
                    break
                full2 = ~window_any(~o2, 0, 4, 0, 4) & self._inside(4)
                c2 = np.argwhere(full2)
                if len(c2):
                    i = min(range(len(c2)), key=lambda i: (abs(int(c2[i][1]) - mid), int(c2[i][0])))
                    x, y = int(c2[i][0]), int(c2[i][1]) + Y0
                    self.pads[net] = ("m2", x, y, x + 4, y + 4)
                    break
                # extend the net with a short wire into free space (metal1 pad, else metal2 pad)
                targets = [(M1, int(c[0]), int(c[1]) + Y0)
                           for c in np.argwhere(L["v1"] & L[M1] & ~window_any(cut, 0, 4, 0, 4))]
                if not targets:
                    f2 = (mp["m2"] != 0) & (mp["m2"] != nid)
                    ok2 = ~window_any(f2, -3, 7, -3, 7) & self._inside(4) & L[M2]
                    targets = [(M2, int(c[0]), int(c[1]) + Y0) for c in np.argwhere(ok2)]
                zero = {k: np.zeros_like(v, dtype=float) for k, v in L.items()}
                vias = self._via_anchors(self.routes[net])
                tree = self.trees.get(net) or [st for t in self.terms[net]
                                                for st in self._terminal_states(t)]

                def accept(key, pv):
                    _, ax, ay, _ = key
                    return all(abs(ax - vx) >= 4 or abs(ay - vy) >= 4 for vx, vy in pv)
                path = self._search(L, zero, tree, targets, accept=accept, own_vias=vias)
                extra = self._path_shapes(path, net)
                lay, px, py = path[-1]
                if lay == M2:
                    extra.append(("m2", px, py, px + 4, py + 4, net))
                self._set_route(net, self.routes[net] + extra)
            else:
                raise RouteError("no pin pad for %s" % net)
        self._maps()

    def _conflicts(self):
        """Cells of routed wires that break spacing to another net. Returns {layer: mask}."""
        out = {}
        for layer, key in ((POLY, "poly"), (M1, "m1"), (M2, "m2")):
            fcnt, fm = self.fcount[key], self.fmask
            bad = np.zeros((self.width, Y1 - Y0), dtype=bool)
            for n, rm in self.rmask.items():
                own_f = fm.get(n, {}).get(key)
                foreign = (fcnt - (own_f if own_f is not None else 0)) + (self.rtotal[key] - rm[key])
                near = window_any(foreign > 0, -3, 4, -3, 4)
                bad |= rm[key] & near
                if not rm[key].any():
                    continue
                own = rm[key] | (own_f.astype(bool) if own_f is not None else False)
                notch = notch_cells(own)
                stuck = notch & near
                if key == "poly":
                    stuck |= notch & window_any(self.fx["act"], -1, 2, -1, 2)
                if stuck.any():
                    bad |= rm[key] & window_any(stuck, -2, 3, -2, 3)
            out[layer] = bad
        return out

    def route(self, order, max_iter=40):
        for p in self.pins:
            if p not in self.terms:
                raise PlanError("%s: pin %s has no terminal" % (self.name, p))
        shape = (self.width, Y1 - Y0)
        hist = {POLY: np.zeros(shape), M1: np.zeros(shape), M2: np.zeros(shape)}
        pres = 4.0
        best = (1 << 30, 0)
        for n in order:
            self._set_route(n, [])
        for it in range(max_iter):
            for net in order:
                self._set_route(net, [])
                self.pads.pop(net, None)
                try:
                    self._set_route(net, self._route_one(net, hist, pres))
                except RouteError as err:
                    raise RouteError("%s: %s" % (net, err))
            bad = self._conflicts()
            nbad = sum(int(m.sum()) for m in bad.values())
            self.iterations = it + 1
            if nbad == 0:
                break
            if nbad < best[0]:
                best = (nbad, it)
            elif it - best[1] >= self.patience:
                raise RouteError("congestion stuck at %d cells after %d passes" % (nbad, it + 1))
            for layer, m in bad.items():
                hist[layer] += 3.0 * m
            pres = min(pres * 1.5, 60.0)
        else:
            raise RouteError("congestion not resolved after %d passes" % max_iter)
        self._maps()
        self._pads()
        for _ in range(3):
            if not self._fill_notches():
                break

    def _fill_notches(self):
        """Fill gaps narrower than the spacing rule between shapes of the same net."""
        added = []
        for layer, key in (("m1", "m1"), ("m2", "m2"), ("poly", "poly")):
            arr = self.mp[key]
            for nid in set(np.unique(arr)) - {0, -1}:
                mask = arr == nid
                fill = notch_cells(mask)
                if not fill.any():
                    continue
                foreign = (arr != 0) & (arr != nid)
                bad = window_any(foreign, -3, 4, -3, 4)
                if key == "poly":
                    bad |= window_any(self.mp["act"], -1, 2, -1, 2)
                fill &= ~bad
                for x, yy in np.argwhere(fill):
                    added.append((layer, int(x), int(yy) + Y0, int(x) + 1, int(yy) + Y0 + 1,
                                  self.netid_rev[nid]))
        if added:
            per = {}
            for a in added:
                per.setdefault(a[5], []).append(a)
            for n, extra in per.items():
                self._set_route(n, self.routes.get(n, []) + extra)
            self._maps()
        return len(added)

    def default_order(self):
        nets = [n for n in self.terms if n not in ("gnd", "vdd")]

        def key(n):
            t = self.terms[n]
            gates = sum(1 for x in t if x[0] == "gate")
            xs = [x[1] for x in t]
            return (-gates, -len(t), -(max(xs) - min(xs)), n)
        return sorted(nets, key=key)

    def _reset(self, extra, spread=0):
        self.__init__(self.name, self.devices, self.plan, self.inputs, self.outputs, extra, spread)
        self._place()
        self._draw_frame()
        self._draw_devices()
        nets = sorted({s_[5] for s_ in self.shapes if s_[5]} | set(self.terms))
        self.netid = {n: i + 1 for i, n in enumerate(nets)}
        self.netid_rev = {v: k for k, v in self.netid.items()}
        self.routes = {}
        self.trees = {}
        self.fx = self._raster(self.shapes)
        shp = (self.width, Y1 - Y0)
        self.rmask = {}
        self.rtotal = {k: np.zeros(shp, dtype=np.int32) for k in ("poly", "m1", "m2", "cut")}
        self.fmask = {}
        self.fcount = {k: np.zeros(shp, dtype=np.int32) for k in ("poly", "m1", "m2")}
        groups = {}
        for x in self.shapes:
            groups.setdefault(x[5] or "-", []).append(x)
        for n, g_ in groups.items():
            m = self._route_masks([(("m1" if t[0] in ("ndc", "pdc", "psc", "nsc") else t[0]),)
                                   + t[1:] for t in g_ if t[0] in ("poly", "m1", "m2", "ndc", "pdc",
                                                                    "psc", "nsc", "pc", "m2c")])
            self.fmask[n] = m
            for k in self.fcount:
                self.fcount[k] += m[k]
        self._maps()

    CONFIGS = [(0, 0), (0, 1), (2, 0), (0, 2), (2, 1), (4, 0), (0, 3), (4, 2), (6, 0), (6, 3), (10, 0)]

    def build(self, verbose=False, max_iter=40):
        """Place and route; try wider placements until congestion can be resolved.

        Configurations (edge margin, gap added beside transmission-gate columns) are
        tried from the narrowest resulting cell upwards; the first one that routes is kept.
        """
        trials = []
        for extra, spread in self.CONFIGS:
            self._reset(extra, spread)
            trials.append((self.width, extra, spread))
        trials = sorted(set(trials))
        last = None
        for width, extra, spread in trials:
            self._reset(extra, spread)
            try:
                self.route(self.default_order(), max_iter=max_iter)
                if verbose:
                    print("  routed at width %d (margin %d, spread %d) in %d passes"
                          % (self.width, extra, spread, self.iterations))
                return self.layout()
            except RouteError as err:
                last = err
                if verbose:
                    print("  width %d (margin %d, spread %d): %s" % (width, extra, spread, err))
        raise RouteError("%s: routing failed (%s)" % (self.name, last))

    def layout(self):
        L = Layout(self.name, bbox=(0, 0, self.width, H))
        order = ["nwell", "ndiff", "pdiff", "poly", "ndc", "pdc", "psc", "nsc", "pc", "m1", "m2c", "m2"]
        allsh = self.all_shapes()
        for layer in order:
            for s_ in allsh:
                if s_[0] == layer:
                    L.paint(layer, s_[1], s_[2], s_[3], s_[4])
        for p in self.pins:
            layer, x1, y1, x2, y2 = self.pads[p]
            use = "input" if p in self.inputs else "output"
            L.label(layer, x1, y1, x2, y2, p, "signal", use)
        for x1, y1, x2, y2, text, use, cls in self.labels:
            L.label("m1", x1, y1, x2, y2, text, use, cls)
        L.net_shapes = allsh
        return L

    def verify(self, L):
        """Design-rule check and LVS-style comparison of the generated layout."""
        import drc
        import extract
        errors = drc.check(L)
        problems, ndev = extract.lvs(L, self.all_shapes(), self.fingers, self.pins)
        return errors, problems, ndev

    def reference_netlist(self):
        """LVS reference: the devices exactly as laid out (folded fingers listed one by one)."""
        pins = self.inputs + self.outputs + ["vdd", "gnd"]
        out = [".subckt %s %s" % (self.name, " ".join(pins))]
        for i, (model, d, g, s, w) in enumerate(self.fingers):
            body = "gnd" if model == "nfet" else "vdd"
            out.append("M%d %s %s %s %s %s w=%gu l=0.2u" % (i, d, g, s, body, model, w / 10.0))
        out.append(".ends %s" % self.name)
        return "\n".join(out) + "\n"
