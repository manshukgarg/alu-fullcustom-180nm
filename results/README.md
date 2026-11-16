# Stored results

Results of project scripts kept with the repository, one folder per run.

## ngspice46_2026-11-16

Run of 16 November 2026 with Ngspice 46 outside the lab (built from the Ngspice 46
sources; the Step 1 inverter gives 95.04 ps there against 95.0 ps in the lab).
These files are the source of the cell sizes in `step4_layout/library.json`,
`step5_library/library.json` and `step3_cells/alu_cells.json` and of the tables in
STATUS.md and in the LTspice package. The lab runs of the same scripts are the
reference for the paper; their summaries should reproduce these files.

| File | Script | Content |
| --- | --- | --- |
| `step3b_sweep_summary.txt`, `step3b_sweep_1800mV.csv` | `step3_cells/run_sweep.sh` | sizing sweep, 21 candidates x 40 sizes |
| `step3c_alu_cells_summary.txt`, `step3c_alu_cells.csv` | `step3_cells/run_alu_cells.sh` | the two ALU-specific cells: sizing and comparison |
| `step6_summary.txt`, `step6_<design>.json` | `step6_alu_schematic/run.sh` | the five 4-bit ALUs at transistor level |
