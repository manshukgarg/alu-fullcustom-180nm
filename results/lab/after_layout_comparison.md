# ALUs after layout: D3 (OSU018), D4 (pl018) and the proposed ALU P

Netlists extracted from the routed layouts (every transistor and parasitic capacitance),
simulated with `sim/alutb.py` (Ngspice, 1.8 V, 27 C, FO4 loads, 229 transitions, all
correct in every design). Written by `results/compare_after_layout.py` from
`results/lab/step2_2026-11-22.json` and `results/lab/step5_final_2026-11-22.json`.

| Design | Library | Netlist cells | Cells placed | Die (um) | Die area (um2) | Transistors | C (fF) | Worst delay (ps) | Mean delay (ps) | Energy per op (fJ) | Leakage (nW) | Energy x delay (fJ ns) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D3 beh | OSU018 | 122 | 147 | 97.6 x 56.0 | 5466 | 793 | 875 | 1812.0 | 1353.2 | 4898.7 | 3.10 | 8876.4 |
| D3 slice | OSU018 | 74 | 104 | 84.0 x 46.0 | 3864 | 525 | 563 | 2144.4 | 1204.7 | 3333.0 | 2.21 | 7147.1 |
| D3 map | OSU018 | 55 | 63 | 76.0 x 46.0 | 3496 | 534 | 455 | 3476.1 | 1564.8 | 3807.1 | 2.18 | 13233.7 |
| D4 beh | pl018 | 146 | 198 | 84.0 x 54.0 | 4536 | 716 | 655 | 1874.0 | 1274.6 | 2798.5 | 1.98 | 5244.4 |
| D4 slice | pl018 | 87 | 110 | 78.4 x 38.0 | 2979 | 454 | 429 | 2257.1 | 1259.4 | 2140.4 | 1.22 | 4831.1 |
| D4 map | pl018 | 60 | 94 | 69.6 x 46.0 | 3202 | 484 | 528 | 3220.6 | 1498.5 | 2077.3 | 1.04 | 6690.1 |
| P fb | pl018 | 27 | 55 | 57.6 x 38.0 | 2189 | 316 | 324 | 2615.4 | 1340.1 | 1453.0 | 0.69 | 3800.1 |

## D4 against D3 (same description, other cell library)

| Description | Cells placed | Die area | Worst delay | Energy per op | Leakage | Energy x delay |
| --- | --- | --- | --- | --- | --- | --- |
| beh | +35 % | -17 % | +3.4 % | -42.9 % | -36.1 % | -40.9 % |
| slice | +6 % | -23 % | +5.3 % | -35.8 % | -44.8 % | -32.4 % |
| map | +49 % | -8 % | -7.4 % | -45.4 % | -52.3 % | -49.4 % |

## Proposed ALU P against every other laid-out design

| Reference | Die area | Transistors | Worst delay | Energy per op | Leakage | Energy x delay |
| --- | --- | --- | --- | --- | --- | --- |
| D3 beh | -60 % | -60 % | +44.3 % | -70.3 % | -77.7 % | -57.2 % |
| D3 slice | -43 % | -40 % | +22.0 % | -56.4 % | -68.8 % | -46.8 % |
| D3 map | -37 % | -41 % | -24.8 % | -61.8 % | -68.3 % | -71.3 % |
| D4 beh | -52 % | -56 % | +39.6 % | -48.1 % | -65.2 % | -27.5 % |
| D4 slice | -27 % | -30 % | +15.9 % | -32.1 % | -43.4 % | -21.3 % |
| D4 map | -32 % | -35 % | -18.8 % | -30.1 % | -33.7 % | -43.2 % |

## Energy per operation after layout (fJ)

| Design | ADD | SUB | INC | DEC | AND | OR | XOR | NOT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D3 beh | 5397 | 5520 | 3947 | 5445 | 4934 | 4413 | 4778 | 4755 |
| D3 slice | 4304 | 3780 | 2616 | 3535 | 3495 | 3067 | 3006 | 2860 |
| D3 map | 4865 | 4741 | 2820 | 4529 | 3913 | 3638 | 2792 | 3160 |
| D4 beh | 3209 | 3228 | 2304 | 2906 | 2764 | 2439 | 2725 | 2813 |
| D4 slice | 2519 | 2962 | 1621 | 2282 | 2129 | 2044 | 1734 | 1833 |
| D4 map | 3119 | 2762 | 1705 | 2293 | 2026 | 1629 | 1460 | 1626 |
| P fb | 1807 | 1857 | 1610 | 1953 | 1104 | 967 | 1138 | 1188 |

Best value of each quantity: die area P fb, transistors P fb, worst delay D3 beh, energy P fb, leakage P fb, energy x delay P fb.
