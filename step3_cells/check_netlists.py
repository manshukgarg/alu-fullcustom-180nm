#!/usr/bin/env python3
"""Switch-level check of every transistor netlist of the project against its truth table.

No simulator is needed (see sim/switchsim.py). Checked:
  * every candidate cell of cellnet.py and the two ALU-specific cells,
  * the cells of the automated-flow library as laid out (tech/pl018/pl018_cells.sp),
  * the conventional reference cells handed to the LTspice designers (docs/conventional_cells.sp).
Usage:  python3 step3_cells/check_netlists.py        (exit status 1 if any netlist fails)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "sim"))
import cellnet  # noqa: E402
import switchsim  # noqa: E402


def main():
    bad = 0
    print("%-14s %-22s %3s  %s" % ("cell", "source", "T", "result"))

    def report(name, source, ntr, problems):
        nonlocal bad
        bad += bool(problems)
        print("%-14s %-22s %3d  %s" % (name, source, ntr, "ok" if not problems else "; ".join(problems)))

    for fn in cellnet.CANDIDATES + [cellnet.buf_cmos] + cellnet.ALU_CELLS:
        c = fn(1.0, 2.0)
        ntr, problems = switchsim.check_subckt(c.spice(), c.name, c.inputs, c.outputs, c.func)
        report(c.name, "cellnet.py", ntr, problems)

    lib = os.path.join(ROOT, "tech", "pl018", "pl018_cells.sp")
    index = os.path.join(ROOT, "step5_library", "cells.json")
    if os.path.isfile(lib) and os.path.isfile(index):
        text = open(lib).read()
        for c in json.load(open(index))["cells"]:
            if not c["outputs"]:
                continue
            ins, outs, truth = c["inputs"], c["outputs"], c["truth"]

            def func(v, ins=ins, outs=outs, truth=truth):
                idx = int("".join(str(v[p]) for p in ins), 2)
                return {o: truth[o][idx] for o in outs}
            ntr, problems = switchsim.check_subckt(text, c["name"], ins, outs, func)
            report(c["name"], "pl018_cells.sp", ntr, problems)

    ref = os.path.join(ROOT, "docs", "conventional_cells.sp")
    if os.path.isfile(ref):
        text = open(ref).read()
        for fn in (cellnet.inv_cmos, cellnet.nand2_cmos, cellnet.nor2_cmos, cellnet.xor_cmos12,
                   cellnet.mux_cmos12, cellnet.muxi_cmos10, cellnet.fa_cmos28):
            c = fn()
            ntr, problems = switchsim.check_subckt(text, c.name, c.inputs, c.outputs, c.func)
            report(c.name, "conventional_cells.sp", ntr, problems)
    print("netlists with problems: %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
