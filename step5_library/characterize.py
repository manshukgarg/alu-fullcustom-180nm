#!/usr/bin/env python3
"""Liberty characterization of the project cell library pl018 with Ngspice (lab).

Conventions follow the OSU018 library used by the automated baseline: times in ns,
capacitances in pF, leakage in nW; delays between 50 % points; transitions between
20 % and 80 %; 5 x 5 tables indexed by output load (index_1) and input transition
(index_2).

For every cell of step5_library/cells.json the netlist extracted from its layout
(out/cells/<name>_pex.spice, written by run.sh; the drawn devices of
tech/pl018/pl018_cells.sp when no extraction exists) is simulated:
  * timing: for every input, every state of the other inputs that makes an output
    depend on it; the input is driven by an ideal ramp (rise, then fall) and every
    output carries the load capacitor; 25 copies of the cell (5 loads x 5 input
    transitions) run in one simulation. A timing arc keeps the worst case over the
    sensitizing states: positive or negative unate when all states agree, non_unate
    otherwise (XOR inputs, multiplexer select, adder inputs);
  * input capacitance: charge drawn from an ideal source driving the pin, unloaded
    outputs, mean over the sensitizing states and both edges;
  * leakage: DC supply current, mean over all input states.
Outputs: tech/pl018/pl018_cells.lib and out/characterization.json, and a summary.

Usage:  python3 characterize.py [--vdd 1.8] [--temp 27] [--jobs N] [--only name,name]
"""
import argparse
import itertools
import json
import multiprocessing as mp
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models", "tsmc018_t14b.lib")
TECHDIR = os.path.join(ROOT, "tech", "pl018")
OUT = os.path.join(HERE, "out")
WORK = os.path.join(OUT, "char")

LOADS = [0.002, 0.006, 0.016, 0.04, 0.1]         # pF   (index_1)
SLEWS = [0.03, 0.08, 0.2, 0.5, 1.2]              # ns, 20-80 %   (index_2)
LO, HI = 0.2, 0.8                                # transition thresholds
T1 = 2.0                                         # ns: 50 % point of the rising input edge
HALF = 10.0                                      # ns between the two input edges
CAP_SLEW = 0.1                                   # ns: input edge for the capacitance runs
REF = (2, 1)                                     # summary point: 0.016 pF, 0.08 ns
MEAS_RE = re.compile(r"^\s*(\w+)\s*=\s*([-+]?[0-9.]+(?:[eE][-+]?[0-9]+)?)")


# ----------------------------------------------------------------------------
# netlists
# ----------------------------------------------------------------------------
def logical(text):
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


def library_subckt(name):
    """The drawn-device subcircuit of a cell from tech/pl018/pl018_cells.sp."""
    lines = logical(open(os.path.join(TECHDIR, "pl018_cells.sp")).read())
    out, on = [], False
    for ln in lines:
        low = ln.lower()
        if low.startswith(".subckt") and ln.split()[1] == name:
            on = True
        if on:
            out.append(ln)
            if low.startswith(".ends"):
                break
    return "\n".join(out) + "\n" if out else None


def extracted_subckt(cell):
    """Magic extraction of the cell, renamed and wrapped with the pin order
    inputs, outputs, vdd, gnd (substrate and well ports joined to the rails)."""
    name = cell["name"]
    path = os.path.join(OUT, "cells", name + "_pex.spice")
    if not os.path.isfile(path):
        return None
    lines = logical(open(path).read())
    body, ports = [], None
    for ln in lines:
        low = ln.lower()
        if low.startswith(".end") and not low.startswith(".ends"):
            continue
        if low.startswith(".subckt"):
            parts = ln.split()
            ports = [p for p in parts[2:] if "=" not in p]
            ln = " ".join([parts[0], name + "_x"] + ports)
        body.append(ln)
    if ports is None:
        return None
    pins = cell["inputs"] + cell["outputs"] + ["vdd", "gnd"]
    conn = []
    for p in ports:
        lp = p.lower()
        if p in pins:
            conn.append(p)
        elif lp in ("vdd!", "vdd") or lp.startswith("w_"):
            conn.append("vdd")
        elif "sub" in lp or lp in ("gnd!", "0", "gnd"):
            conn.append("gnd")
        else:
            conn.append(p)
    wrap = [".subckt %s %s" % (name, " ".join(pins)), "Xpex %s %s_x" % (" ".join(conn), name),
            ".ends %s" % name]
    return "\n".join(body) + "\n" + "\n".join(wrap) + "\n"


def dut_text(cell):
    t = extracted_subckt(cell)
    if t:
        return t, "extracted layout"
    return library_subckt(cell["name"]), "drawn devices (no extraction found)"


# ----------------------------------------------------------------------------
# arcs
# ----------------------------------------------------------------------------
def states(cell, pin):
    """Sensitizing states of the other inputs: list of (state dict, {output: sense})."""
    ins = cell["inputs"]
    others = [p for p in ins if p != pin]
    res = []
    for bits in itertools.product((0, 1), repeat=len(others)):
        st = dict(zip(others, bits))
        sens = {}
        for o in cell["outputs"]:
            vals = []
            for v in (0, 1):
                full = dict(st)
                full[pin] = v
                idx = int("".join(str(full[p]) for p in ins), 2)
                vals.append(cell["truth"][o][idx])
            if vals[0] != vals[1]:
                sens[o] = "positive" if vals[1] == 1 else "negative"
        if sens:
            res.append((st, sens))
    return res


def ramp(t50, rising, slew, vdd):
    """PWL points of an ideal edge with the given 20-80 % transition, 50 % at t50 (ns)."""
    full = slew / (HI - LO)
    a, b = (0.0, vdd) if rising else (vdd, 0.0)
    return [(t50 - full / 2, a), (t50 + full / 2, b)]


def pwl(points):
    return "PWL(" + " ".join("%.6gn %.6g" % (t, v) for t, v in points) + ")"


def timing_deck(cell, dut, pin, st, sens, vdd, temp, path):
    L = ["* %s: timing of %s, other inputs %s" % (cell["name"], pin, st), ".include %s" % MODELS,
         dut, ".temp %g" % temp, "Vdd vdd 0 %g" % vdd]
    for p, v in st.items():
        L.append("V_%s s_%s 0 %g" % (p, p, vdd * v))
    t2 = T1 + HALF
    meas = []
    for i, cl in enumerate(LOADS):
        for j, sl in enumerate(SLEWS):
            c = "%d_%d" % (i, j)
            pts = [(0, 0.0)] + ramp(T1, True, sl, vdd) + ramp(t2, False, sl, vdd)
            L.append("Vin_%s in_%s 0 %s" % (c, c, pwl(pts)))
            conn = []
            for p in cell["inputs"] + cell["outputs"]:
                if p == pin:
                    conn.append("in_" + c)
                elif p in st:
                    conn.append("s_" + p)
                else:
                    conn.append("o_%s_%s" % (p, c))
            L.append("X%s %s vdd 0 %s" % (c, " ".join(conn), cell["name"]))
            for o in cell["outputs"]:
                L.append("C_%s_%s o_%s_%s 0 %gp" % (o, c, o, c, cl))
            for o, sense in sens.items():
                node = "o_%s_%s" % (o, c)
                for edge, inrise in (("r", True), ("f", False)):
                    out_rise = inrise if sense == "positive" else not inrise
                    ind, outd = ("rise" if inrise else "fall"), ("rise" if out_rise else "fall")
                    tag = "%s_%s_%s" % (o, edge, c)
                    meas.append(".meas tran d_%s trig v(in_%s) val=%g %s=1 targ v(%s) val=%g %s=1"
                                % (tag, c, vdd / 2, ind, node, vdd / 2, outd))
                    a, b = (LO, HI) if out_rise else (HI, LO)
                    meas.append(".meas tran t_%s trig v(%s) val=%g %s=1 targ v(%s) val=%g %s=1"
                                % (tag, node, vdd * a, outd, node, vdd * b, outd))
    L += meas
    L += [".tran 2p %gn" % (t2 + HALF), ".end"]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def cap_deck(cell, dut, vdd, temp, path):
    """Input charge of every pin in every sensitizing state (one copy each)."""
    L = ["* %s: input capacitance" % cell["name"], ".include %s" % MODELS, dut, ".temp %g" % temp,
         "Vdd vdd 0 %g" % vdd]
    t2 = T1 + 4.0
    keys = []
    for pin in cell["inputs"]:
        sts = [s for s, _ in states(cell, pin)] or [{p: 0 for p in cell["inputs"] if p != pin}]
        for k, st in enumerate(sts):
            c = "%s_%d" % (pin, k)
            pts = [(0, 0.0)] + ramp(T1, True, CAP_SLEW, vdd) + ramp(t2, False, CAP_SLEW, vdd)
            L.append("Vin_%s in_%s 0 %s" % (c, c, pwl(pts)))
            conn = []
            for p in cell["inputs"] + cell["outputs"]:
                if p == pin:
                    conn.append("in_" + c)
                elif p in st:
                    conn.append("s_%s_%s" % (p, c))
                    L.append("V_%s_%s s_%s_%s 0 %g" % (p, c, p, c, vdd * st[p]))
                else:
                    conn.append("o_%s_%s" % (p, c))
            L.append("X%s %s vdd 0 %s" % (c, " ".join(conn), cell["name"]))
            L.append(".meas tran qr_%s integ i(Vin_%s) from=%gn to=%gn" % (c, c, T1 - 0.5, T1 + 3.0))
            L.append(".meas tran qf_%s integ i(Vin_%s) from=%gn to=%gn" % (c, c, t2 - 0.5, t2 + 3.0))
            keys.append((pin, c))
    L += [".tran 2p %gn" % (t2 + 3.5), ".end"]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return keys


def leak_deck(cell, dut, vdd, temp, path):
    n = len(cell["inputs"])
    L = ["* %s: leakage in every input state" % cell["name"], ".include %s" % MODELS, dut,
         ".temp %g" % temp, ".options gmin=1e-15"]
    for k in range(1 << n):
        bits = [(k >> (n - 1 - i)) & 1 for i in range(n)]
        conn = []
        for p, b in zip(cell["inputs"], bits):
            L.append("V_%s_%d s_%s_%d 0 %g" % (p, k, p, k, vdd * b))
            conn.append("s_%s_%d" % (p, k))
        conn += ["o_%s_%d" % (o, k) for o in cell["outputs"]]
        L.append("Vdd_%d vdd_%d 0 %g" % (k, k, vdd))
        L.append("X%d %s vdd_%d 0 %s" % (k, " ".join(conn), k, cell["name"]))
        L.append(".meas dc il_%d find i(Vdd_%d) at=0" % (k, k))
    L += ["Vdum dum 0 0", "Rdum dum 0 1k", ".dc Vdum 0 1 1", ".end"]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return 1 << n


def run(path):
    try:
        r = subprocess.run(["ngspice", "-b", os.path.basename(path)], cwd=os.path.dirname(path),
                           capture_output=True, text=True, timeout=1800)
        log = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        log = "TIMEOUT"
    with open(path[:-3] + ".log", "w") as f:
        f.write(log)
    vals = {}
    for line in log.splitlines():
        m = MEAS_RE.match(line)
        if m:
            vals[m.group(1).lower()] = float(m.group(2))
    return path, vals


# ----------------------------------------------------------------------------
# Liberty
# ----------------------------------------------------------------------------
def table(name, values):
    rows = ", \\\n          ".join('"%s"' % ", ".join("%.6g" % v for v in row) for row in values)
    return ["      %s(delay_template_5x5) {" % name,
            '        index_1 ("%s");' % ", ".join("%g" % v for v in LOADS),
            '        index_2 ("%s");' % ", ".join("%g" % v for v in SLEWS),
            "        values ( \\", "          %s);" % rows, "      }"]


def write_liberty(lib, res, vdd, temp, path):
    L = ["/* Project cell library %s: characterized with Ngspice by step5_library/characterize.py */"
         % lib["library"],
         "/* TSMC 0.18 um BSIM3v3.1 models (MOSIS T14B), %.2f V, %g C, from the extracted layouts */"
         % (vdd, temp),
         "library(%s) {" % lib["library"], "  delay_model : table_lookup;",
         '  time_unit : "1ns";', '  voltage_unit : "1V";', '  current_unit : "1uA";',
         '  pulling_resistance_unit : "1kohm";', '  leakage_power_unit : "1nW";',
         "  capacitive_load_unit (1,pf);",
         "  slew_upper_threshold_pct_rise : 80;", "  slew_lower_threshold_pct_rise : 20;",
         "  slew_upper_threshold_pct_fall : 80;", "  slew_lower_threshold_pct_fall : 20;",
         "  input_threshold_pct_rise : 50;", "  input_threshold_pct_fall : 50;",
         "  output_threshold_pct_rise : 50;", "  output_threshold_pct_fall : 50;",
         "  nom_process : 1;", "  nom_voltage : %g;" % vdd, "  nom_temperature : %g;" % temp,
         "  operating_conditions ( typical ) {", "     process : 1;", "     voltage : %g;" % vdd,
         "     temperature : %g;" % temp, "  }", "  default_operating_conditions : typical;",
         "  lu_table_template(delay_template_5x5) {", "    variable_1 : total_output_net_capacitance;",
         "    variable_2 : input_net_transition;",
         '    index_1 ("1000.0, 1001.0, 1002.0, 1003.0, 1004.0");',
         '    index_2 ("1000.0, 1001.0, 1002.0, 1003.0, 1004.0");', "  }"]
    for cell in lib["cells"]:
        r = res.get(cell["name"])
        if not r or not cell["outputs"]:
            continue
        L += ["", "cell (%s) {" % cell["name"], "  area : %g;" % cell["area_um2"],
              "  cell_leakage_power : %.6g;" % r["leakage_nW"]]
        for p in cell["inputs"]:
            c = r["cap_pF"].get(p, {})
            L += ["  pin(%s) {" % p, "    direction : input;",
                  "    capacitance : %.6g;" % c.get("mean", 0.0),
                  "    rise_capacitance : %.6g;" % c.get("rise", 0.0),
                  "    fall_capacitance : %.6g;" % c.get("fall", 0.0), "  }"]
        for o in cell["outputs"]:
            L += ["  pin(%s) {" % o, "    direction : output;", "    capacitance : 0;",
                  "    max_capacitance : %g;" % LOADS[-1],
                  '    function : "%s";' % cell["function"][o]]
            for p in cell["inputs"]:
                arc = r["arcs"].get("%s>%s" % (p, o))
                if not arc:
                    continue
                L += ["    timing() {", '      related_pin : "%s";' % p,
                      "      timing_sense : %s;" % arc["sense"]]
                for key in ("cell_rise", "rise_transition", "cell_fall", "fall_transition"):
                    if arc.get(key):
                        L += table(key, arc[key])
                L.append("    }")
            L.append("  }")
        L.append("}")
    L.append("}")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vdd", type=float, default=1.8)
    ap.add_argument("--temp", type=float, default=27.0)
    ap.add_argument("--jobs", type=int, default=max(1, min(8, os.cpu_count() or 2)))
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    vdd = args.vdd
    lib = json.load(open(os.path.join(HERE, "cells.json")))
    only = [s for s in args.only.split(",") if s]
    cells = [c for c in lib["cells"] if c["outputs"] and (not only or c["name"] in only)]
    os.makedirs(WORK, exist_ok=True)
    jobs, plan, source = [], {}, {}
    for cell in cells:
        dut, src = dut_text(cell)
        source[cell["name"]] = src
        if dut is None:
            continue
        p = os.path.join(WORK, "%s_cap.sp" % cell["name"])
        plan[p] = ("cap", cell, cap_deck(cell, dut, vdd, args.temp, p))
        jobs.append(p)
        p = os.path.join(WORK, "%s_leak.sp" % cell["name"])
        plan[p] = ("leak", cell, leak_deck(cell, dut, vdd, args.temp, p))
        jobs.append(p)
        for pin in cell["inputs"]:
            for k, (st, sens) in enumerate(states(cell, pin)):
                p = os.path.join(WORK, "%s_%s_%d.sp" % (cell["name"], pin, k))
                timing_deck(cell, dut, pin, st, sens, vdd, args.temp, p)
                plan[p] = ("timing", cell, (pin, st, sens))
                jobs.append(p)
    print("characterizing %d cells: %d simulations on %d cores" % (len(cells), len(jobs), args.jobs),
          flush=True)
    results = {}
    with mp.Pool(args.jobs) as pool:
        for path, vals in pool.imap_unordered(run, jobs):
            results[path] = vals

    res, problems = {}, []
    for cell in cells:
        name = cell["name"]
        r = {"source": source[name], "arcs": {}, "cap_pF": {}, "leakage_nW": 0.0, "missing": 0}
        res[name] = r
        if source[name] is None or library_subckt(name) is None and "extracted" not in source[name]:
            problems.append("%s: no netlist" % name)
            continue
        for path, (kind, c, info) in plan.items():
            if c is not cell:
                continue
            v = results.get(path, {})
            if kind == "leak":
                il = [v.get("il_%d" % k) for k in range(info)]
                good = [-x * vdd * 1e9 for x in il if x is not None]
                r["leakage_nW"] = sum(good) / len(good) if good else 0.0
                if len(good) < info:
                    problems.append("%s: %d leakage states missing" % (name, info - len(good)))
            elif kind == "cap":
                acc = {}
                for pin, c_ in info:
                    qr, qf = v.get("qr_%s" % c_.lower()), v.get("qf_%s" % c_.lower())
                    if qr is None or qf is None:
                        r["missing"] += 1
                        continue
                    acc.setdefault(pin, []).append((abs(qr) / vdd * 1e12, abs(qf) / vdd * 1e12))
                for pin, lst in acc.items():
                    rise = sum(a for a, _ in lst) / len(lst)
                    fall = sum(b for _, b in lst) / len(lst)
                    r["cap_pF"][pin] = {"rise": rise, "fall": fall, "mean": (rise + fall) / 2}
        # timing: worst case over the sensitizing states, per arc and output edge
        for pin in cell["inputs"]:
            for o in cell["outputs"]:
                senses = set()
                tabs = {k: [[None] * len(SLEWS) for _ in LOADS]
                        for k in ("cell_rise", "rise_transition", "cell_fall", "fall_transition")}
                for path, (kind, c, info) in plan.items():
                    if c is not cell or kind != "timing" or info[0] != pin or o not in info[2]:
                        continue
                    sense = info[2][o]
                    senses.add(sense)
                    v = results.get(path, {})
                    for i in range(len(LOADS)):
                        for j in range(len(SLEWS)):
                            for edge, inrise in (("r", True), ("f", False)):
                                out_rise = inrise if sense == "positive" else not inrise
                                tag = "%s_%s_%d_%d" % (o.lower(), edge, i, j)
                                d, t = v.get("d_" + tag), v.get("t_" + tag)
                                if d is None or t is None:
                                    r["missing"] += 1
                                    continue
                                kd, kt = (("cell_rise", "rise_transition") if out_rise
                                          else ("cell_fall", "fall_transition"))
                                d, t = d * 1e9, t * 1e9
                                tabs[kd][i][j] = d if tabs[kd][i][j] is None else max(tabs[kd][i][j], d)
                                tabs[kt][i][j] = t if tabs[kt][i][j] is None else max(tabs[kt][i][j], t)
                if not senses:
                    continue
                arc = {"sense": ("positive_unate" if senses == {"positive"} else
                                 "negative_unate" if senses == {"negative"} else "non_unate")}
                for k, tab in tabs.items():
                    if all(x is not None for row in tab for x in row):
                        arc[k] = [[max(x, 1e-4) for x in row] for row in tab]
                    elif any(x is not None for row in tab for x in row):
                        problems.append("%s %s>%s: %s incomplete" % (name, pin, o, k))
                r["arcs"]["%s>%s" % (pin, o)] = arc
        if r["missing"]:
            problems.append("%s: %d measurements missing (see out/char/%s_*.log)" % (name, r["missing"], name))

    write_liberty(lib, res, vdd, args.temp, os.path.join(TECHDIR, "pl018_cells.lib"))
    with open(os.path.join(OUT, "characterization.json"), "w") as f:
        json.dump(res, f)

    i, j = REF
    print("pl018 Liberty: %.2f V, %g C; delay and transition at %g pF load, %g ns input transition"
          % (vdd, args.temp, LOADS[i], SLEWS[j]))
    print("%-9s %6s %7s  %-24s %-26s %s" % ("cell", "area", "leak", "input cap (fF)",
                                           "worst delay rise/fall (ps)", "netlist"))
    for cell in cells:
        r = res[cell["name"]]
        caps = " ".join("%s %.1f" % (p, r["cap_pF"][p]["mean"] * 1e3) for p in cell["inputs"]
                        if p in r["cap_pF"])
        dr = [a["cell_rise"][i][j] for a in r["arcs"].values() if a.get("cell_rise")]
        df = [a["cell_fall"][i][j] for a in r["arcs"].values() if a.get("cell_fall")]
        dl = "%5.0f / %5.0f" % (max(dr) * 1e3 if dr else float("nan"), max(df) * 1e3 if df else float("nan"))
        print("%-9s %6.1f %7.3f  %-24s %-26s %s" % (cell["name"], cell["area_um2"], r["leakage_nW"],
                                                    caps, dl, "pex" if "extracted" in r["source"] else "drawn"))
    for p in problems[:10]:
        print("  check: " + p)


if __name__ == "__main__":
    main()
