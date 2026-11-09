"""Boolean helpers for the cell library: minimized expressions from truth tables.

A truth table is a list of output bits indexed by the input combination, with
the first input as the most significant bit (the order used by cells.json).
Expressions are written for Liberty ("!", "&", "|", "^") or Verilog ("~", "&", "|", "^").
"""
import itertools


def minterms(table):
    return [i for i, v in enumerate(table) if v]


def _combine(a, b):
    """Merge two implicants (value, mask) that differ in exactly one unmasked bit."""
    (va, ma), (vb, mb) = a, b
    if ma != mb:
        return None
    d = (va ^ vb) & ~ma
    if d and not d & (d - 1):
        return (va & ~d, ma | d)
    return None


def prime_implicants(ones, n):
    terms = {(m, 0) for m in ones}
    primes = set()
    while terms:
        used, nxt = set(), set()
        tl = sorted(terms)
        for a, b in itertools.combinations(tl, 2):
            c = _combine(a, b)
            if c is not None:
                nxt.add(c)
                used.add(a)
                used.add(b)
        primes |= terms - used
        terms = nxt
    return primes


def covers(imp, m):
    v, mask = imp
    return (m & ~mask) == (v & ~mask)


def minimal_cover(ones, n):
    """Smallest set of prime implicants covering the minterms (exact for small n)."""
    if not ones:
        return []
    primes = sorted(prime_implicants(ones, n), key=lambda p: (bin(p[1]).count("1"), p), reverse=True)
    for size in range(1, len(primes) + 1):
        best = None
        for combo in itertools.combinations(primes, size):
            if all(any(covers(p, m) for p in combo) for m in ones):
                lits = sum(n - bin(p[1]).count("1") for p in combo)
                if best is None or lits < best[0]:
                    best = (lits, combo)
        if best:
            return list(best[1])
    return primes


def _term(imp, names, style):
    v, mask = imp
    n = len(names)
    lits = []
    for i, nm in enumerate(names):
        bit = 1 << (n - 1 - i)
        if mask & bit:
            continue
        neg = "!" if style == "liberty" else "~"
        lits.append(nm if v & bit else neg + nm)
    if not lits:
        return "1" if style == "liberty" else "1'b1"
    return lits[0] if len(lits) == 1 else "(" + "&".join(lits) + ")"


def sop(table, names, style):
    n = len(names)
    cover = minimal_cover(minterms(table), n)
    if not cover:
        return "0" if style == "liberty" else "1'b0"
    terms = [_term(p, names, style) for p in cover]
    return terms[0] if len(terms) == 1 else "(" + "|".join(terms) + ")"


def parity_form(table, names, style):
    """'A^B^C' (or its complement) if the function is a parity of some inputs."""
    n = len(names)
    for k in range(2, n + 1):
        for sub in itertools.combinations(range(n), k):
            for inv in (0, 1):
                ok = all(table[i] == (sum((i >> (n - 1 - j)) & 1 for j in sub) + inv) % 2
                         for i in range(1 << n))
                if ok:
                    e = "(" + "^".join(names[j] for j in sub) + ")"
                    return ("!" if style == "liberty" else "~") + e if inv else e
    return None


def expression(table, names, style="liberty"):
    """Compact expression of one output: parity form, SOP of f, or complement of SOP of !f."""
    p = parity_form(table, names, style)
    if p:
        return p
    f = sop(table, names, style)
    g = sop([1 - v for v in table], names, style)
    neg = "!" if style == "liberty" else "~"
    if g.count("&") + g.count("|") + 1 < f.count("&") + f.count("|"):
        return neg + (g if g.startswith("(") else "(" + g + ")")
    return f


def evaluate(expr, values, style="liberty"):
    """Value of an expression written by expression() for {name: bit} (self-check).

    Recursive descent with | lowest, then ^, then &, then unary ! or ~; the
    expressions written here are fully parenthesized, so precedence never decides."""
    text = expr.replace("1'b1", "1").replace("1'b0", "0")
    toks, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch in "()&|^!~":
            toks.append(ch)
            i += 1
        else:
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            if j == i:
                raise ValueError("bad character %r in %s" % (ch, expr))
            toks.append(text[i:j])
            i = j
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        pos[0] += 1
        return toks[pos[0] - 1]

    def unary():
        t = take()
        if t in ("!", "~"):
            return 1 - unary()
        if t == "(":
            v = orx()
            if take() != ")":
                raise ValueError("unbalanced parentheses in %s" % expr)
            return v
        if t in ("0", "1"):
            return int(t)
        return int(values[t])

    def andx():
        v = unary()
        while peek() == "&":
            take()
            v &= unary()
        return v

    def xorx():
        v = andx()
        while peek() == "^":
            take()
            v ^= andx()
        return v

    def orx():
        v = xorx()
        while peek() == "|":
            take()
            v |= xorx()
        return v

    v = orx()
    if pos[0] != len(toks):
        raise ValueError("trailing tokens in %s" % expr)
    return v


def check(table, names, expr, style="liberty"):
    n = len(names)
    for i in range(1 << n):
        vals = {nm: (i >> (n - 1 - j)) & 1 for j, nm in enumerate(names)}
        if evaluate(expr, vals, style) != table[i]:
            return False
    return True
