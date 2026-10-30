"""Generate the Step 1 inverter layout (mag/inv.mag) and its reference netlist.

Run from the repository root:  python3 layout/gen_step1.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

from cells import inv, INV_REF   # noqa: E402

cell = inv()
errors = cell.check()
if errors:
    print("Rule check FAILED for %s:" % cell.name)
    for err in errors:
        print("  " + err)
    sys.exit(1)
cell.write(os.path.join(ROOT, "mag", "inv.mag"))
with open(os.path.join(ROOT, "step1_flowcheck", "inv_ref.spice"), "w") as f:
    f.write(INV_REF)
print("inv: rule check clean, wrote mag/inv.mag and step1_flowcheck/inv_ref.spice")
