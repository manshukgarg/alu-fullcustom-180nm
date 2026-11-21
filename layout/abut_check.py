"""Abutment check of the pl018 library cells.

Builds four placement rows of abutted cells (normal and mirrored, alternate rows flipped
so that they share their rails, as in a placed design) and checks the flattened result
with the project rule check plus Magic's exact-overlap rule for contacts of different
cells (contacts of two subcells may coincide but may not touch or partially overlap).
This is where the well and substrate taps of neighbouring rows meet.

Usage:  python3 layout/abut_check.py [mag directory]
"""
import os, sys, re, itertools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "layout"))
import verify_mag, drc
from maglib import Layout

H = 80
names = ["pl_inv", "pl_buf", "pl_nand2", "pl_nor2", "pl_and2", "pl_or2", "pl_xor2", "pl_mux2",
         "pl_mux2i", "pl_fa", "pl_fb4", "pl_cs", "pl_fill"]
magdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "mag")
cells = {}
for n in names:
    L = verify_mag.read_mag(os.path.join(magdir, n + ".mag"))
    m = re.search(r"FIXED_BBOX (-?\d+) (-?\d+) (-?\d+) (-?\d+)", open(os.path.join(magdir, n + ".mag")).read())
    bb = tuple(int(v) for v in m.groups())
    taps = []
    cur = None
    for line in open(os.path.join(magdir, n + ".mag")):
        line = line.strip()
        mm = re.match(r"<< (\S+) >>", line)
        if mm:
            cur = mm.group(1)
            continue
        if line.startswith("rect") and cur in ("psubstratepcontact", "nsubstratencontact", "ndcontact", "pdcontact", "polycontact"):
            taps.append((cur, tuple(int(v) for v in line.split()[1:5])))
    cells[n] = (L, bb, taps)

def place(rows):
    """rows: list of lists of (name, mirror_x); row k flipped when k odd."""
    C = Layout("composite")
    contacts = []
    for k, row in enumerate(rows):
        x0 = 0
        for idx, (n, mx) in enumerate(row):
            L, bb, taps = cells[n]
            W = bb[2] - bb[0]
            flip = k % 2 == 1
            def tx(x):
                return x0 + (W - 1 - x if mx else x)
            def ty(y):
                return (k + 1) * H - 1 - y if flip else k * H + y
            for pl, P in L.planes.items():
                Q = C.planes[pl]
                for (x, y), t in P.items():
                    Q[(tx(x), ty(y))] = t
            for t, (x1, y1, x2, y2) in taps:
                xs = sorted([tx(x1), tx(x2 - 1)])
                ys = sorted([ty(y1), ty(y2 - 1)])
                contacts.append((t, (k, idx), (xs[0], ys[0], xs[1] + 1, ys[1] + 1)))
            x0 += W
    return C, contacts

def exact_overlap_errors(contacts):
    errs = 0
    by = {}
    for t, inst, r in contacts:
        by.setdefault(t, []).append((inst, r))
    for t, lst in by.items():
        for (i1, a), (i2, b) in itertools.combinations(lst, 2):
            if i1 == i2:
                continue
            touch = a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]
            if touch and a != b:
                errs += 1
    return errs

order = names[:-1]
rows = [
    [(n, False) for n in order],
    [("pl_fill", False)] + [(n, True) for n in reversed(order)],
    [("pl_fill", False), ("pl_fill", False)] + [(n, i % 2 == 0) for i, n in enumerate(order[3:] + order[:3])],
    [(n, i % 3 == 0) for i, n in enumerate(order[6:] + order[:6])],
]
C, contacts = place(rows)
errs = drc.check(C)
print("composite: %d instances, DRC findings %d" % (sum(len(r) for r in rows), len(errs)))
from collections import Counter
cnt = Counter(re.sub(r" near .*", "", e) for e in errs)
for k, v in cnt.most_common():
    print("  %4d  %s" % (v, k))
nx = exact_overlap_errors(contacts)
print("contacts of different cells touching without exact overlap: %d" % nx)
sys.exit(1 if errs or nx else 0)
