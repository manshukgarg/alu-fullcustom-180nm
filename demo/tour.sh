#!/bin/bash
# Guided tour of the project: the demonstration views one after the other.
#
#   bash demo/tour.sh            all views in order; close each window to go on
#   bash demo/tour.sh 4          start at view 4
#   bash demo/tour.sh --list     the list of views only
#
# Each view is a command of demo/show.sh. Before it opens, the terminal shows what the view
# is; press Enter to open it, s to skip it, q to stop.
DEMO=$(cd "$(dirname "$0")" && pwd)

STEPS=(
  "schematic fb4|Function block FB4: 20 transistors. A and B select one of the four code lines C0..C3 through two levels of transmission gates; two inverters restore the output."
  "cell-sim fb4|FB4 in Ngspice with the ALU's function codes: the output P follows the code, every row checked, delays with a fan-out-of-four load."
  "layout fb4|Layout of FB4 in Magic: fresh DRC (0 errors), extraction, and LVS of the layout against the schematic."
  "schematic cs|Carry-sum cell CS: carry out = CI if P = 1, else A (no generate signal); Y = P for logic operations, P xor CI for arithmetic."
  "layout cs|Layout of CS: DRC and LVS like FB4."
  "alu-sim fb|The 4-bit ALU built from FB4 and CS at transistor level: 32 vectors, all eight operations, results and flags checked."
  "chip fb|The ALU placed and routed by Qflow with our cell library pl018, opened in KLayout with the real cell layouts."
  "chip-sim fb|The netlist extracted from that routed layout (every transistor and parasitic capacitance) simulated again: still correct."
  "results|Result tables: cells, the five transistor-level ALUs and the seven routed ALUs."
)

if [ "$1" = "--list" ]; then
  for i in "${!STEPS[@]}"; do
    printf "%d  %-15s %s\n" $((i + 1)) "${STEPS[$i]%%|*}" "${STEPS[$i]#*|}"
  done
  exit 0
fi

start=${1:-1}
n=${#STEPS[@]}
for ((i = start - 1; i < n; i++)); do
  view=${STEPS[$i]%%|*}
  text=${STEPS[$i]#*|}
  echo
  echo "=== $((i + 1))/$n  bash demo/show.sh $view"
  echo "$text" | fold -s -w 90
  read -r -p "Enter = open, s = skip, q = quit: " key
  case "$key" in
    q|Q) exit 0 ;;
    s|S) continue ;;
  esac
  bash "$DEMO/show.sh" $view
done
echo
echo "End of the tour."
