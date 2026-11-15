#!/usr/bin/env python3
"""Switch-level logic check of transistor netlists (pure Python, no simulator).

Every transistor is a switch: an NMOS conducts when its gate is 1, a PMOS when its
gate is 0. Starting from the supplies and the input pins, values spread through
conducting transistors until nothing changes. All input vectors are evaluated at
once (one bit per vector in Python integers), so a 4-bit ALU with its 2048
vectors takes well under a second.

The check finds wiring and logic errors in a netlist before any circuit
simulation: wrong function, outputs left undriven, and nodes driven to 0 and 1
at the same time. It does not see voltage levels, delays or weak drive.

Used by step3_cells/check_netlists.py (cells) and sim/gen_alu.py (ALUs).
"""


def logical_lines(text):
    out = []
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("*"):
            continue
        if ln.startswith("+") and out:
            out[-1] += " " + ln[1:].strip()
        else:
            out.append(ln)
    return out


def parse_spice(text):
    """{subckt name (lower case): (pins, element lines)} and the top-level element lines."""
    subs, top, cur = {}, [], None
    for ln in logical_lines(text):
        low = ln.lower()
        if low.startswith(".subckt"):
            parts = ln.split()
            cur = (parts[1].lower(), [p for p in parts[2:] if "=" not in p], [])
        elif low.startswith(".ends"):
            if cur:
                subs[cur[0]] = (cur[1], cur[2])
            cur = None
        elif low.startswith("."):
            continue
        elif cur:
            cur[2].append(ln)
        else:
            top.append(ln)
    return subs, top


def flatten(subs, name):
    """Transistors and shorts of subcircuit `name`, flattened.

    Returns (pins, devices, shorts): devices are (kind, drain, gate, source) with kind
    'n' or 'p'; shorts are node pairs joined by resistors. Internal nodes of
    instances are named <instance>/<node>.
    """
    pins, _ = subs[name.lower()]
    devs, shorts = [], []

    def walk(sub, prefix, bind):
        _, lines = subs[sub]

        def node(n):
            return bind.get(n, prefix + n)

        for ln in lines:
            tok = ln.split()
            kind = tok[0][0].lower()
            if kind == "m":
                model = tok[5].lower()
                devs.append(("n" if model.startswith("n") else "p", node(tok[1]), node(tok[2]), node(tok[3])))
            elif kind == "r":
                shorts.append((node(tok[1]), node(tok[2])))
            elif kind == "x":
                plain = [t for t in tok if "=" not in t]
                child = plain[-1].lower()
                if child not in subs:
                    raise ValueError("subcircuit %s is not defined (instance %s)" % (plain[-1], tok[0]))
                cpins = subs[child][0]
                nodes = plain[1:-1]
                if len(nodes) != len(cpins):
                    raise ValueError("instance %s gives %d nodes to %s, which has %d pins"
                                     % (tok[0], len(nodes), plain[-1], len(cpins)))
                walk(child, prefix + tok[0] + "/", {p: node(n) for p, n in zip(cpins, nodes)})

    walk(name.lower(), "", {p: p for p in pins})
    return pins, devs, shorts


def solve(devs, shorts, fixed, nvec):
    """Steady-state node values for all vectors at once.

    fixed: {node: bitmask of the vectors in which the node is 1}; fixed nodes are the
    inputs and the supplies. Returns (is1, is0): bitmasks per node.
    """
    full = (1 << nvec) - 1
    is1, is0 = {}, {}
    for n, m in fixed.items():
        is1[n] = m & full
        is0[n] = ~m & full
    for kind, d, g, s in devs:
        for n in (d, g, s):
            is1.setdefault(n, 0)
            is0.setdefault(n, 0)
    for a, b in shorts:
        for n in (a, b):
            is1.setdefault(n, 0)
            is0.setdefault(n, 0)
    changed = True
    while changed:
        changed = False
        for kind, d, g, s in devs:
            on = is1[g] if kind == "n" else is0[g]
            if not on:
                continue
            for a, b in ((d, s), (s, d)):
                v1, v0 = is1[a] | (is1[b] & on), is0[a] | (is0[b] & on)
                if v1 != is1[a] or v0 != is0[a]:
                    is1[a], is0[a] = v1, v0
                    changed = True
        for a, b in shorts:
            v1, v0 = is1[a] | is1[b], is0[a] | is0[b]
            if v1 != is1[a] or v0 != is0[a] or v1 != is1[b] or v0 != is0[b]:
                is1[a] = is1[b] = v1
                is0[a] = is0[b] = v0
                changed = True
    return is1, is0


def check(devs, shorts, inputs, outputs, func, supplies=("vdd", "gnd")):
    """Compare a flattened netlist with func over all input vectors.

    func(dict input -> 0/1) -> dict output -> 0/1. Returns a list of problems (empty if clean).
    """
    n = len(inputs)
    nvec = 1 << n
    full = (1 << nvec) - 1
    fixed = {supplies[0]: full, supplies[1]: 0}
    for i, nm in enumerate(inputs):
        mask = 0
        for v in range(nvec):
            if (v >> (n - 1 - i)) & 1:
                mask |= 1 << v
        fixed[nm] = mask
    is1, is0 = solve(devs, shorts, fixed, nvec)
    expect = {o: 0 for o in outputs}
    for v in range(nvec):
        out = func({nm: (v >> (n - 1 - i)) & 1 for i, nm in enumerate(inputs)})
        for o in outputs:
            if out[o]:
                expect[o] |= 1 << v
    problems = []
    fight = [nd for nd in is1 if is1[nd] & is0[nd]]
    if fight:
        problems.append("%d node(s) driven to 0 and 1 together, e.g. %s" % (len(fight), fight[0]))
    for o in outputs:
        if o not in is1:
            problems.append("output %s is not connected" % o)
            continue
        undriven = full & ~(is1[o] | is0[o])
        wrong = (is1[o] ^ expect[o]) & ~undriven & full
        if undriven:
            problems.append("output %s undriven in %d of %d vectors" % (o, bin(undriven).count("1"), nvec))
        if wrong:
            v = (wrong & -wrong).bit_length() - 1
            problems.append("output %s wrong in %d of %d vectors, first at %s"
                            % (o, bin(wrong).count("1"), nvec,
                               " ".join("%s=%d" % (nm, (v >> (n - 1 - i)) & 1) for i, nm in enumerate(inputs))))
    return problems


def check_subckt(text, name, inputs, outputs, func):
    """Parse SPICE text, flatten subcircuit `name` and check it. Returns (transistors, problems)."""
    subs, _ = parse_spice(text)
    if name.lower() not in subs:
        return 0, ["subcircuit %s not found" % name]
    try:
        pins, devs, shorts = flatten(subs, name)
    except ValueError as exc:
        return 0, [str(exc)]
    low = {p.lower(): p for p in pins}
    missing = [p for p in inputs + outputs + ["vdd", "gnd"] if p.lower() not in low]
    if missing:
        return len(devs), ["pins missing: %s" % " ".join(missing)]
    ren = {low[p.lower()]: p for p in inputs + outputs + ["vdd", "gnd"]}
    devs = [(k, ren.get(d, d), ren.get(g, g), ren.get(s, s)) for k, d, g, s in devs]
    shorts = [(ren.get(a, a), ren.get(b, b)) for a, b in shorts]
    return len(devs), check(devs, shorts, inputs, outputs, func)
