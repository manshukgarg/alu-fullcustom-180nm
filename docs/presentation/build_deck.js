// Presentation of the project (PowerPoint), built with pptxgenjs.
//
//   python3 docs/presentation/prepare_assets.py      (figures and screenshot crops)
//   node docs/presentation/build_deck.js             (writes docs/presentation/ALU4_180nm_presentation.pptx)
//
// All numbers are the lab results stored in results/lab/ (Steps 2, 5 and 6) and the cell results in
// results/ngspice46_2026-11-16/ (Steps 3b and 3c).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const ROOT = path.resolve(HERE, "..", "..");
const ASSETS = path.join(HERE, "assets");
const FIGS = path.join(ROOT, "docs", "figures", "presentation");
const OUT = path.join(HERE, "ALU4_180nm_presentation.pptx");
const THEME_JS = process.env.PPTX_THEME_JS ||
  "/root/.claude/skills/synced/d3da237c-03b5-4263-bf34-d2c5f853f719_f4efced4-22eb-4efd-8301-06827ebf0ae6/pptx/scripts/apply_theme.js";

const THEME = {
  name: "ALU 180nm",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "15181C", lt1: "FFFFFF", dk2: "1F242B", lt2: "F2F3F5",
    accent1: "2A78D6",  // proposed design, emphasis
    accent2: "A8A69F",  // context series in charts
    accent3: "5F6368",  // secondary text
    accent4: "E8F1FC",  // tint of the emphasis colour
    accent5: "D5D8DD",  // rules and borders
    accent6: "8FB9EC",  // emphasis colour on dark slides
    hlink: "2A78D6", folHlink: "5F6368",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Manshuk Garg";
pres.company = "Thapar Institute of Engineering and Technology";
pres.title = "Design and Performance Analysis of a Full-Custom ALU Using Optimized Standard Cells";
pres.subject = "4-bit ALU in 180 nm CMOS";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const INK = C.text1, MUTED = C.accent3, BLUE = C.accent1, TINT = C.accent4, RULE = C.accent5, CARD = C.background2;

const W = 13.333, MX = 0.6, CW = W - 2 * MX, TOP = 1.9;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE",
  background: { color: HEX.dk2 },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.36, w: CW, h: 0.66, fontSize: 32, bold: true,
      color: INK, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "msg", type: "body", x: MX, y: 1.04, w: CW, h: 0.66, fontSize: 18, color: MUTED,
      valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Full-custom 4-bit ALU in 180 nm CMOS", options: { x: MX, y: 7.03, w: 6, h: 0.28, fontSize: 10,
      color: MUTED, margin: 0, valign: "middle" } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.03, w: 0.6, h: 0.28, fontSize: 10, color: MUTED, align: "right", margin: 0 },
});

// ---------------------------------------------------------------- helpers
function pngSize(p) {
  const b = fs.readFileSync(p);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function content(section, title, msg) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (msg) s.addText(msg, { placeholder: "msg" });
  return s;
}
function txt(s, runs, o) {
  s.addText(runs, Object.assign({ isTextBox: true, margin: 0, fontSize: 16, color: INK, valign: "top" }, o));
}
// image fitted into a box (x, y, w, h), aligned left/top unless centred
function img(s, file, x, y, w, h, o = {}) {
  const sz = pngSize(file);
  let iw = w, ih = (w * sz.h) / sz.w;
  if (ih > h) { ih = h; iw = (h * sz.w) / sz.h; }
  const ix = o.center ? x + (w - iw) / 2 : x, iy = o.middle ? y + (h - ih) / 2 : y;
  s.addImage({ path: file, x: ix, y: iy, w: iw, h: ih, altText: o.alt || "", objectName: o.name });
  if (o.frame) {
    s.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: iw, h: ih, fill: { type: "none" },
      line: { color: RULE, width: 0.75 } });
  }
  return { x: ix, y: iy, w: iw, h: ih };
}
function caption(s, text, x, y, w, o = {}) {
  txt(s, text, Object.assign({ x, y, w, h: 0.3, fontSize: 12, color: MUTED }, o));
}
// rounded box with text
function box(s, x, y, w, h, runs, o = {}) {
  s.addText(runs, Object.assign({ shape: pres.shapes.ROUNDED_RECTANGLE, x, y, w, h, rectRadius: 0.07,
    fill: { color: o.fill || CARD }, line: { color: o.line || RULE, width: o.lineWidth || 0.75 },
    margin: [8, 8, 6, 6], fontSize: 13, color: INK, valign: o.valign || "middle", align: o.align || "center" },
  o.extra || {}));
}
function arrow(s, x1, y1, x2, y2, o = {}) {
  const opts = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    line: { color: o.color || "6B7075", width: o.width || 1.5, endArrowType: o.noHead ? undefined : "triangle" } };
  if (x2 < x1) opts.flipH = true;
  if (y2 < y1) opts.flipV = true;
  s.addShape(pres.shapes.LINE, opts);
}
// table with horizontal rules only; rows: arrays of strings or {text, options}
function table(s, header, rows, o) {
  const fs_ = o.fontSize || 14;
  const hdr = header.map((h, i) => ({ text: h, options: { bold: true, color: INK, fill: { color: HEX.lt2 },
    align: (o.align && o.align[i]) || "left", valign: "middle",
    border: [{ type: "none" }, { type: "none" }, { pt: 1, color: HEX.accent5 }, { type: "none" }] } }));
  const body = rows.map((r) => {
    const hi = r.highlight;
    const cells = hi ? r.cells : r;
    return cells.map((c, i) => {
      const cell = typeof c === "object" && c !== null && c.text !== undefined ? c : { text: String(c) };
      return { text: cell.text, options: Object.assign({ color: INK, align: (o.align && o.align[i]) || "left",
        valign: "middle", bold: !!hi, fill: hi ? { color: HEX.accent4 } : undefined,
        border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: HEX.accent5 }, { type: "none" }] },
      cell.options || {}) };
    });
  });
  s.addTable([hdr, ...body], { x: o.x, y: o.y, w: o.w, colW: o.colW, fontSize: fs_, fontFace: THEME.bodyFontFace,
    rowH: o.rowH || 0.34, margin: [0.03, 0.08, 0.03, 0.08], autoPage: false });
}
// big number with a label underneath
function stat(s, x, y, w, value, label, o = {}) {
  txt(s, value, { x, y, w, h: 0.62, fontSize: o.size || 36, bold: true, color: o.color || BLUE });
  txt(s, label, { x, y: y + 0.66, w, h: 0.62, fontSize: 13, color: MUTED });
}
const AXIS = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt" };
function hbar(s, x, y, w, h, labels, values, colors, o = {}) {
  s.addChart(pres.charts.BAR, [{ name: o.name || "value", labels, values }], Object.assign({}, AXIS, {
    x, y, w, h, barDir: "bar", catAxisOrientation: "maxMin", chartColors: colors,
    catAxisLabelFontSize: o.labelSize || 12, catAxisLabelColor: "3C4043", catAxisLineShow: true,
    catAxisLineColor: "C9CCD1", catGridLine: { style: "none" }, valGridLine: { style: "none" },
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: o.max,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: o.labelSize || 12, dataLabelColor: HEX.dk1,
    dataLabelFormatCode: o.fmt || "0", barGapWidthPct: o.gap || 45, showLegend: false,
    objectName: o.objectName,
  }));
}
const GRAY = HEX.accent2, EMPH = HEX.accent1;

// ======================================================================== 1 title
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  txt(s, "M.Tech VLSI Design  |  Project presentation", { x: MX, y: 0.62, w: 7.2, h: 0.35, fontSize: 14,
    color: C.accent6, bold: true });
  txt(s, "Design and Performance Analysis of a Full-Custom ALU Using Optimized Standard Cells",
    { x: MX, y: 1.25, w: 6.9, h: 2.3, fontSize: 36, bold: true, color: C.background1, fontFace: THEME.headFontFace });
  txt(s, "4-bit ALU in 180 nm CMOS: minimum-PDP cell library, two ALU-specific cells, and placed-and-routed " +
    "implementations compared after layout", { x: MX, y: 3.7, w: 6.6, h: 1.0, fontSize: 17, color: "C9CED6" });
  txt(s, [
    { text: "Manshuk Garg, Aditya Kumar, Gourangi Tyagi, Kashish Goyal", options: { breakLine: true, bold: true } },
    { text: "Thapar Institute of Engineering and Technology, Patiala", options: { breakLine: true } },
    { text: "28 November 2026" },
  ], { x: MX, y: 5.35, w: 7.0, h: 1.2, fontSize: 15, color: "E6E9EE", paraSpaceAfter: 4 });
  // layout of the function-block cell on a white card
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.75, y: 1.35, w: 5.0, h: 3.35, rectRadius: 0.08,
    fill: { color: HEX.lt1 }, line: { color: HEX.lt1, width: 0 }, objectName: "Layout card" });
  img(s, path.join(ASSETS, "layout_fb4_plain.png"), 7.95, 1.5, 4.6, 3.05, { center: true, middle: true,
    alt: "Layout of the function-block cell pl_fb4", name: "Layout pl_fb4" });
  txt(s, "Function-block cell pl_fb4: 20 transistors, 14.4 × 8.0 µm, generated layout",
    { x: 7.75, y: 4.82, w: 5.0, h: 0.5, fontSize: 12, color: "AEB4BD" });
  s.addNotes("Project: a 4-bit ALU in 180 nm CMOS built from our own optimized standard cells, plus two cells " +
    "designed specifically for the ALU bit slice. The same ALU is compared in several versions, at transistor level " +
    "and after automatic place and route, with one common measurement. Everything shown was run in the NIELIT " +
    "ChipCraft lab with open-source tools; a live demonstration follows the slides.");
}

// ======================================================================== 2 objectives
{
  const s = content("Introduction", "Objectives",
    "Evaluate optimized and ALU-specific standard cells in one 4-bit ALU, before and after layout");
  const items = [
    ["Optimize the cells of the ALU", "XOR2, MUX2, full adder and gates in 180 nm CMOS: circuit topology and transistor sizing for minimum power-delay product"],
    ["Design cells for the ALU bit slice", "Function block FB4 and carry-sum cell CS: one ALU bit from two cells"],
    ["Build a standard-cell library", "Layout, DRC and LVS, characterization (Liberty), views for Yosys and Qflow"],
    ["Compare complete ALUs", "One transistor-level test for every design, at schematic level and on the netlist extracted from the routed layout"],
  ];
  items.forEach(([h, d], i) => {
    const y = TOP + 0.05 + i * 1.18;
    txt(s, String(i + 1).padStart(2, "0"), { x: MX, y, w: 0.6, h: 0.5, fontSize: 24, bold: true, color: BLUE });
    txt(s, [{ text: h, options: { bold: true, breakLine: true } }, { text: d, options: { color: MUTED, fontSize: 14 } }],
      { x: MX + 0.75, y: y + 0.02, w: 5.35, h: 1.05, fontSize: 16 });
  });
  txt(s, "Designs compared", { x: 7.15, y: TOP + 0.05, w: 5.5, h: 0.4, fontSize: 16, bold: true });
  table(s, ["Design", "Cells", "Evaluated"], [
    ["D1", "conventional static CMOS cells", "transistor level"],
    ["D2", "minimum-PDP cells (this work)", "transistor level"],
    ["D3", "OSU 0.18 µm library, Yosys and Qflow", "after layout"],
    ["D4", "project library pl018, Yosys and Qflow", "after layout"],
    { highlight: true, cells: ["P", "FB4 and CS cells (proposed)", "both"] },
  ], { x: 7.15, y: TOP + 0.55, w: 5.58, colW: [0.8, 3.18, 1.6], fontSize: 14, rowH: 0.42 });
  txt(s, "Also at transistor level: an ALU from gate-level cells (NAND-based XOR, multiplexer and adder) and one from " +
    "the pl018 cells in the hand-mapped slice.", { x: 7.15, y: 5.25, w: 5.58, h: 0.9, fontSize: 13, color: MUTED });
  s.addNotes("Four objectives. The point of the comparison is that every design is measured the same way: the same " +
    "test bench, the same input sequence and the same loads, first on the transistor netlist and then on the netlist " +
    "extracted from the routed layout. D3 and D4 use the same RTL and differ only in the cell library, which isolates " +
    "the effect of our library inside a standard automated flow.");
}

// ======================================================================== 3 specification
{
  const s = content("Introduction", "ALU specification and technology",
    "Four bits, eight operations, four flags; TSMC 0.18 µm CMOS at 1.8 V");
  table(s, ["s2 s1 s0", "Operation", "Result y"], [
    ["0 0 0", "ADD", "a + b"], ["0 0 1", "SUB", "a − b"], ["0 1 0", "INC", "a + 1"], ["0 1 1", "DEC", "a − 1"],
    ["1 0 0", "AND", "a and b"], ["1 0 1", "OR", "a or b"], ["1 1 0", "XOR", "a xor b"], ["1 1 1", "NOT", "not a"],
  ], { x: MX, y: TOP, w: 5.2, colW: [1.35, 1.6, 2.25], fontSize: 14, rowH: 0.36 });
  txt(s, [
    { text: "Flags: ", options: { bold: true } },
    { text: "C carry out (1 = no borrow for SUB and DEC), V signed overflow, Z zero, N negative; C and V are 0 for the logic operations." },
  ], { x: MX, y: 5.35, w: 5.2, h: 1.0, fontSize: 14 });
  table(s, ["Item", "Choice"], [
    ["Process", "TSMC 0.18 µm CMOS, VDD = 1.8 V, 27 °C"],
    ["Transistor models", "MOSIS BSIM3v3.1 parameters, run T14B"],
    ["Layout rules", "SCMOS SCN6M_SUBM, λ = 0.1 µm, L = 0.2 µm"],
    ["Circuit simulation", "Ngspice 46"],
    ["Schematic, layout, checks", "Xschem, Magic 8.3, Netgen, KLayout"],
    ["Synthesis, place and route", "Yosys, Qflow (GrayWolf, Qrouter), OpenSTA"],
    ["Environment", "NIELIT ChipCraft Virtual Lab"],
  ], { x: 6.35, y: TOP, w: 6.38, colW: [2.45, 3.93], fontSize: 14, rowH: 0.4 });
  txt(s, "Functional reference for every netlist: all 2048 input combinations (16 × 16 × 8).",
    { x: 6.35, y: 5.45, w: 6.38, h: 0.6, fontSize: 14, color: MUTED });
  s.addNotes("Eight operations selected by s2..s0: four arithmetic, four logic, with carry, overflow, zero and " +
    "negative flags. The carry flag follows the usual convention that 1 means no borrow for subtraction. Technology is " +
    "TSMC 0.18 micron with the MOSIS BSIM3 models and the SCMOS SUBM rules of the Qflow OSU018 kit, so the layouts can " +
    "be checked with Magic and Netgen and used by Qflow. Every netlist, from RTL to transistor level, is checked against " +
    "all 2048 input combinations.");
}

// ======================================================================== 4 flow
{
  const s = content("Introduction", "Design flow",
    "Cells and ALUs are measured with one transistor-level test, from schematic to extracted layout");
  const bw = 1.78, gap = 0.29, y = 3.0, bh = 1.45;
  const steps = [
    ["Cell circuits", "21 candidates for 9 functions; FB4 and CS"],
    ["Sizing", "8 widths × 5 P/N ratios; minimum PDP at FO4"],
    ["Cell layout", "generated; Magic DRC, Netgen LVS"],
    ["Library pl018", "Liberty from extracted layouts; LEF, SPICE, Verilog"],
    ["Synthesis, place and route", "Yosys, Qflow, OpenSTA"],
    ["Layout sign-off", "LVS; DRC with real cells; extraction"],
  ];
  const xs = steps.map((_, i) => MX + i * (bw + gap));
  steps.forEach(([h, d], i) => {
    const prop = i === 1 || i === 3;
    box(s, xs[i], y, bw, bh, [{ text: h, options: { bold: true, fontSize: 14, breakLine: true } },
      { text: d, options: { fontSize: 12, color: MUTED } }], { fill: prop ? TINT : CARD, line: prop ? BLUE : RULE,
      extra: { objectName: "Flow step " + (i + 1) } });
    if (i < steps.length - 1) arrow(s, xs[i] + bw + 0.03, y + bh / 2, xs[i + 1] - 0.03, y + bh / 2);
  });
  // feeder into synthesis
  box(s, xs[4] - 0.35, TOP, bw + 0.7, 0.68, [{ text: "ALU netlists: RTL, hand-mapped; OSU 0.18 µm cells for D3",
    options: { fontSize: 12 } }], { extra: { objectName: "ALU netlists" } });
  arrow(s, xs[4] + bw / 2, TOP + 0.7, xs[4] + bw / 2, y - 0.03);
  // bottom: transistor-level ALUs and the common test
  const yb = 5.25, hb = 0.9;
  box(s, xs[1], yb, bw * 2 + gap, hb, [{ text: "ALU from each cell set at transistor level", options: { bold: true,
    fontSize: 13, breakLine: true } }, { text: "D1, D2, P and two more, before layout", options: { fontSize: 12,
    color: MUTED } }], { extra: { objectName: "Transistor-level ALUs" } });
  arrow(s, xs[1] + bw / 2, y + bh + 0.03, xs[1] + bw / 2, yb - 0.03);
  box(s, xs[4], yb, bw * 2 + gap, hb, [{ text: "One ALU test bench (Ngspice)", options: { bold: true, fontSize: 13,
    breakLine: true } }, { text: "229 transitions; delay, energy, leakage", options: { fontSize: 12, color: MUTED } }],
  { fill: TINT, line: BLUE, extra: { objectName: "ALU test bench" } });
  arrow(s, xs[5] + bw / 2, y + bh + 0.03, xs[5] + bw / 2, yb - 0.03);
  arrow(s, xs[1] + 2 * bw + gap + 0.03, yb + hb / 2, xs[4] - 0.03, yb + hb / 2);
  caption(s, "before layout", xs[1] + 2 * bw + gap + 0.03, yb + hb / 2 - 0.34, xs[4] - (xs[1] + 2 * bw + gap) - 0.06,
    { align: "center" });
  caption(s, "after layout", xs[5] + bw / 2 + 0.08, yb - 0.62, 1.4);
  txt(s, "Inputs through two X1 inverters, FO4 loads on every output; 18 full carry ripples and 24 random operand " +
    "changes per operation, 5 ns per vector; energy from the ALU supply; leakage from 16 DC states.",
  { x: MX, y: 6.33, w: CW, h: 0.55, fontSize: 13, color: MUTED });
  s.addNotes("Top row is the cell flow: candidate circuits, sizing sweep, layout generation with DRC and LVS in Magic " +
    "and Netgen, characterization into a Liberty library. The library and the ALU netlists go through Yosys and Qflow; " +
    "the routed layout is checked and extracted with every transistor and parasitic capacitance. The bottom row is " +
    "the key point: the transistor-level ALUs and the extracted layouts run through the same Ngspice test bench, so " +
    "numbers before and after layout are directly comparable.");
}

// ======================================================================== 5 cell optimization
pres.addSection({ title: "Cell design" });
{
  const s = content("Cell design", "Standard-cell optimization",
    "Transmission-gate circuits at their minimum-PDP size: PDP −53 % (XOR2), −65 % (MUX2), −60 % (full adder)");
  table(s, ["Function", "Selected circuit", "k / r", "PDP (fJ)", "vs static"], [
    ["INV", "static CMOS", "0.8 / 2.5", "9.65", "−3 %"],
    ["NAND2", "static CMOS", "0.6 / 3", "10.62", "−14 %"],
    ["NOR2", "static CMOS", "0.6 / 2.5", "13.36", "−3 %"],
    { highlight: true, cells: ["XOR2", "transmission gate, 8 T", "0.6 / 3", "20.11", "−53 %"] },
    { highlight: true, cells: ["MUX2", "transmission gate, 6 T", "0.4 / 3", "16.28", "−65 %"] },
    { highlight: true, cells: ["MUX2I", "TG + inverter, 8 T", "0.6 / 2.5", "19.38", "−47 %"] },
    { highlight: true, cells: ["FA", "TG adder, 24 T", "0.3 / 2.5", "63.95", "−60 %"] },
  ], { x: MX, y: TOP, w: 6.2, colW: [0.95, 2.2, 1.05, 1.0, 1.0], fontSize: 14, rowH: 0.42,
    align: ["left", "left", "left", "right", "right"] });
  txt(s, "PDP (fJ): static CMOS at reference size (k 1, r 2) and the selected circuit", { x: 7.1, y: TOP,
    w: 5.63, h: 0.35, fontSize: 13, color: MUTED });
  s.addChart(pres.charts.BAR, [
    { name: "static CMOS", labels: ["INV", "NAND2", "NOR2", "XOR2", "MUX2", "MUX2I", "FA"], values: [9.99, 12.28, 13.77, 42.69, 46.60, 36.49, 159.44] },
    { name: "selected circuit", labels: ["INV", "NAND2", "NOR2", "XOR2", "MUX2", "MUX2I", "FA"], values: [9.65, 10.62, 13.36, 20.11, 16.28, 19.38, 63.95] },
  ], Object.assign({}, AXIS, { x: 7.0, y: TOP + 0.4, w: 5.73, h: 3.1, barDir: "col", chartColors: [GRAY, EMPH],
    catAxisLabelFontSize: 12, catAxisLabelColor: "3C4043", catAxisLineColor: "C9CCD1", catGridLine: { style: "none" },
    valGridLine: { style: "none" }, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 185,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: HEX.dk1, dataLabelFormatCode: "0",
    barGapWidthPct: 55, showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: "3C4043",
    objectName: "Cell PDP chart" }));
  txt(s, "21 candidate circuits × 40 sizes (width scale k = 0.3–2, P/N ratio r = 1–3). Each cell is driven by two X1 " +
    "inverters and loaded with four (FO4); every input transition is applied; the worst delay and the power including " +
    "the drivers give the PDP. Selected: minimum PDP with full output swing.",
  { x: MX, y: 5.75, w: CW, h: 0.95, fontSize: 13, color: MUTED });
  s.addNotes("Each function had several candidate circuits: static CMOS, gate-level, transmission-gate, buffered " +
    "transmission-gate, CPL and pass-transistor variants, 21 in all. Each was simulated at 40 sizes and the size with the " +
    "minimum power-delay product and full swing was kept. Gains are small for simple gates and large for XOR, " +
    "multiplexer and full adder, where transmission gates replace stacked static CMOS. For the automated-flow library " +
    "the restoring versions (with an output inverter) are used, because the synthesis tool connects cells freely.");
}

// ======================================================================== 6 FB4
{
  const s = content("Cell design", "Function block FB4 (20 transistors)",
    "The operand bits A and B select one of four code lines, so P can be any function of A and B");
  const im = img(s, path.join(ASSETS, "schematic_fb4.png"), MX, TOP - 0.05, 6.2, 4.55,
    { alt: "Transistor schematic of FB4", name: "FB4 schematic" });
  caption(s, "Schematic (Xschem), device sizes of the layout", MX, im.y + im.h + 0.02, im.w);
  const x2 = 7.15, w2 = 5.58;
  table(s, ["A", "B", "P"], [["0", "0", "C0"], ["0", "1", "C1"], ["1", "0", "C2"], ["1", "1", "C3"]],
    { x: x2, y: TOP, w: 2.4, colW: [0.7, 0.7, 1.0], fontSize: 14, rowH: 0.36, align: ["center", "center", "center"] });
  txt(s, [
    { text: "Example", options: { bold: true, breakLine: true } },
    { text: "ADD: C3..C0 = 0110 gives P = A xor B (propagate)", options: { breakLine: true } },
    { text: "AND: C3..C0 = 1000 gives P = A and B" },
  ], { x: x2 + 2.7, y: TOP + 0.05, w: 2.88, h: 1.6, fontSize: 14 });
  txt(s, [
    { text: "Two levels of transmission gates (B, then A) and two inverters that restore the level: a normal static " +
      "cell for the place-and-route flow.", options: { bullet: true, breakLine: true } },
    { text: "Sized for minimum PDP: k 0.4, r 2.5; 450 ps worst delay and 18.95 fJ PDP at FO4.",
      options: { bullet: true, breakLine: true } },
    { text: "Layout 14.4 × 8.0 µm (18 sites); Magic DRC 0, Netgen LVS match.", options: { bullet: true, breakLine: true } },
    { text: "Principle: the function block of the OM-2 data path (Mead and Conway, 1980), here as a restoring CMOS " +
      "transmission-gate cell.", options: { bullet: true } },
  ], { x: x2, y: 3.95, w: w2, h: 2.7, fontSize: 14, paraSpaceAfter: 7 });
  s.addNotes("FB4 is a 4-to-1 multiplexer whose data inputs are the four code lines and whose select inputs are the " +
    "operand bits. With the right code, its output is any Boolean function of a and b: the propagate signal for the " +
    "arithmetic operations, or directly the result for AND, OR, XOR and NOT. The code lines are shared by all four " +
    "bits. Every path passes two transmission gates, then two inverters restore the level, so it behaves like any " +
    "static library cell. The idea goes back to the OM-2 data path of Mead and Conway; our contribution is the " +
    "restoring CMOS cell, its sizing and layout, and its use in the ALU.");
}

// ======================================================================== 7 CS
{
  const s = content("Cell design", "Carry-sum cell CS (24 transistors)",
    "A carry multiplexer without a generate signal, and the choice between sum and logic result");
  const im = img(s, path.join(ASSETS, "schematic_cs.png"), MX, TOP - 0.05, 6.2, 4.55,
    { alt: "Transistor schematic of CS", name: "CS schematic" });
  caption(s, "Schematic (Xschem), device sizes of the layout", MX, im.y + im.h + 0.02, im.w);
  const x2 = 7.15, w2 = 5.58;
  box(s, x2, TOP, w2, 1.2, [
    { text: "CO = CI if P = 1, else A", options: { breakLine: true } },
    { text: "Y = P if K = 1, else P xor CI" },
  ], { fill: TINT, line: BLUE, align: "left", extra: { fontSize: 18, bold: true, margin: [14, 10, 8, 8],
    objectName: "CS function" } });
  txt(s, [
    { text: "P = 0 means the operand bits are equal, so the carry out is A: no generate signal is needed.",
      options: { bullet: true, breakLine: true } },
    { text: "K = s2 selects the logic result (P) or the sum (P xor CI).", options: { bullet: true, breakLine: true } },
    { text: "Carry path per bit: one transmission gate and two inverters.", options: { bullet: true, breakLine: true } },
    { text: "Sized for minimum PDP: k 0.8, r 1.5; 459 ps, 33.64 fJ at FO4. Layout 13.6 × 8.0 µm (17 sites); DRC 0, " +
      "LVS match.", options: { bullet: true, breakLine: true } },
    { text: "The propagate-steered carry multiplexer is also used in FPGA carry chains.", options: { bullet: true } },
  ], { x: x2, y: TOP + 1.45, w: w2, h: 3.5, fontSize: 15, paraSpaceAfter: 8 });
  s.addNotes("CS takes P from FB4. When P is 1 the carry propagates, so the carry out is the carry in; when P is 0 " +
    "the two operand bits are equal, so the carry out is simply A, either both ones (generate) or both zeros (kill). " +
    "That removes the separate generate signal. The same cell forms the sum P xor CI and selects with K between the " +
    "sum and the logic result. The carry ripples through one transmission gate and two inverters per bit.");
}

// ======================================================================== 8 cell comparison
{
  const s = content("Cell design", "FB4 and CS against composed cells",
    "Lower PDP than the same functions built from library cells (−12 %, −18 %) and from static CMOS (−73 %, −64 %)");
  txt(s, "PDP of the FB4 function (fJ)", { x: MX, y: TOP, w: 5.9, h: 0.32, fontSize: 14, bold: true });
  hbar(s, MX, TOP + 0.3, 5.9, 1.75, ["3 × MUX2, static CMOS", "3 × MUX2I, pl018", "FB4 cell"],
    [70.78, 21.58, 18.95], [GRAY, GRAY, EMPH], { max: 85, fmt: "0.00", objectName: "FB4 PDP chart" });
  txt(s, "PDP of the CS function (fJ)", { x: MX, y: 4.2, w: 5.9, h: 0.32, fontSize: 14, bold: true });
  hbar(s, MX, 4.5, 5.9, 1.75, ["MUX2 + XOR2 + MUX2, static", "MUX2 + XOR2 + MUX2, pl018", "CS cell"],
    [93.84, 41.08, 33.64], [GRAY, GRAY, EMPH], { max: 112, fmt: "0.00", objectName: "CS PDP chart" });
  table(s, ["Implementation", "T", "Delay (ps)", "PDP (fJ)"], [
    [{ text: "FB4 function", options: { bold: true, color: MUTED } }, "", "", ""],
    ["3 × MUX2, static CMOS", "36", "688.7", "70.78"],
    ["3 × MUX2I, pl018", "24", "433.6", "21.58"],
    { highlight: true, cells: ["FB4", "20", "450.2", "18.95"] },
    [{ text: "CS function", options: { bold: true, color: MUTED } }, "", "", ""],
    ["MUX2 + XOR2 + MUX2, static", "36", "614.6", "93.84"],
    ["MUX2 + XOR2 + MUX2, pl018", "30", "510.0", "41.08"],
    { highlight: true, cells: ["CS", "24", "458.6", "33.64"] },
  ], { x: 6.95, y: TOP, w: 5.78, colW: [2.9, 0.6, 1.14, 1.14], fontSize: 14, rowH: 0.4,
    align: ["left", "right", "right", "right"] });
  txt(s, "Every change of one input in every state of the others (384 transitions for FB4, 64 for CS), FO4 load, " +
    "drivers included. FB4 is 4 % slower than three MUX2I cells but 12 % lower in PDP with 4 transistors fewer.",
  { x: 6.95, y: 5.75, w: 5.78, h: 1.0, fontSize: 13, color: MUTED });
  s.addNotes("Fair comparison: the same function built from our own optimized library cells, and from static CMOS " +
    "cells. Against the optimized library the merged cells save 12 and 18 percent PDP and 4 and 6 transistors; against " +
    "static CMOS 73 and 64 percent. FB4 is slightly slower than three inverting multiplexers, which is stated openly; " +
    "the main gain appears at ALU level, where the two cells replace the whole conventional bit slice.");
}

// ======================================================================== 9 architecture
pres.addSection({ title: "ALU" });
{
  const s = content("ALU", "ALU bit slice",
    "One FB4 and one CS per bit (44 transistors); a shared decoder of nine library cells sets the code lines");
  // bit slice
  const fx = 2.05, fy = 2.75, fw = 1.55, fh = 1.0, cx = 4.75, cy = 2.75, cw = 1.55, ch = 2.15;
  box(s, fx, fy, fw, fh, [{ text: "FB4", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "20 T", options: { fontSize: 12, color: MUTED } }], { fill: TINT, line: BLUE, lineWidth: 1.25,
    extra: { objectName: "FB4 block" } });
  box(s, cx, cy, cw, ch, [{ text: "CS", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "24 T", options: { fontSize: 12, color: MUTED } }], { fill: TINT, line: BLUE, lineWidth: 1.25,
    extra: { objectName: "CS block" } });
  const sub = (a, b) => [{ text: a }, { text: b, options: { subscript: true } }];
  // code lines from the top
  txt(s, "C0..C3 from the decoder (all bits)", { x: 1.2, y: TOP + 0.02, w: 3.3, h: 0.3, fontSize: 13, color: MUTED });
  arrow(s, fx + fw / 2, TOP + 0.36, fx + fw / 2, fy - 0.03);
  // inputs
  const inY = [fy + 0.28, fy + 0.72];
  [["a", "i"], ["b", "i"]].forEach(([n, i], k) => {
    txt(s, sub(n, i), { x: 0.75, y: inY[k] - 0.16, w: 0.5, h: 0.32, fontSize: 15 });
    arrow(s, 1.15, inY[k], fx - 0.03, inY[k]);
  });
  // P
  arrow(s, fx + fw + 0.03, fy + fh / 2, cx - 0.03, fy + fh / 2);
  txt(s, sub("P", "i"), { x: 3.95, y: fy + fh / 2 - 0.36, w: 0.5, h: 0.32, fontSize: 15 });
  // a, carry in and K into CS
  const csIn = [[cy + 1.3, ["a", "i"]], [cy + 1.65, ["c", "i"]], [cy + 1.98, ["K = s", "2"]]];
  csIn.forEach(([yy, lab]) => {
    arrow(s, 1.15, yy, cx - 0.03, yy);
    txt(s, sub(lab[0], lab[1]), { x: 0.6, y: yy - 0.16, w: 0.9, h: 0.32, fontSize: 15 });
  });
  caption(s, "carry in", 1.45, cy + 1.65 - 0.3, 1.2);
  // outputs
  [[cy + 0.5, ["y", "i"], "result"], [cy + 1.65, ["c", "i+1"], "carry out"]].forEach(([yy, lab, what]) => {
    arrow(s, cx + cw + 0.03, yy, 7.0, yy);
    txt(s, sub(lab[0], lab[1]), { x: 7.08, y: yy - 0.16, w: 0.6, h: 0.32, fontSize: 15 });
    caption(s, what, cx + cw + 0.12, yy - 0.32, 1.2);
  });
  // chain of the 4-bit ALU
  const chainY = 5.55, chH = 0.78;
  const blocks = [["Decoder", "9 cells"], ["bit 0", "FB4 + CS"], ["bit 1", "FB4 + CS"], ["bit 2", "FB4 + CS"],
    ["bit 3", "FB4 + CS"], ["Flags", "C V Z N"]];
  const bwid = 0.98, bgap = 0.22;
  blocks.forEach(([h, d], i) => {
    const xx = MX + i * (bwid + bgap);
    const bit = i > 0 && i < 5;
    box(s, xx, chainY, bwid, chH, [{ text: h, options: { bold: true, fontSize: 13, breakLine: true } },
      { text: d, options: { fontSize: 11, color: MUTED } }], { fill: bit ? TINT : CARD, line: bit ? BLUE : RULE,
      extra: { objectName: "Chain " + h } });
    if (i < blocks.length - 1) arrow(s, xx + bwid + 0.02, chainY + chH / 2, xx + bwid + bgap - 0.02, chainY + chH / 2);
  });
  caption(s, "4-bit ALU at transistor level: 272 transistors, including one buffer on s2", MX, chainY + chH + 0.08, 7.0);
  // operation table
  table(s, ["Op", "P", "C3..C0", "c0", "K"], [
    ["ADD", "a xor b", "0110", "0", "0"], ["SUB", "a xnor b", "1001", "1", "0"], ["INC", "a", "1100", "1", "0"],
    ["DEC", "not a", "0011", "0", "0"], ["AND", "a and b", "1000", "–", "1"], ["OR", "a or b", "1110", "–", "1"],
    ["XOR", "a xor b", "0110", "–", "1"], ["NOT", "not a", "0011", "–", "1"],
  ], { x: 7.95, y: TOP, w: 4.78, colW: [0.8, 1.35, 1.13, 0.75, 0.75], fontSize: 14, rowH: 0.4,
    align: ["left", "left", "center", "center", "center"] });
  txt(s, "c0 = s1 xor s0 is the carry into bit 0. For SUB and DEC the operand b is complemented or replaced " +
    "through the code, not by an extra XOR per bit.", { x: 7.95, y: 5.65, w: 4.78, h: 1.0, fontSize: 13, color: MUTED });
  s.addNotes("One bit is FB4 plus CS. The decoder turns the operation code into the four code lines, the carry into " +
    "bit 0 and K. For ADD the code 0110 makes P = a xor b; for SUB the code 1001 gives a xnor b, which is a xor (not b), " +
    "and the carry in is 1, so no XOR gate per bit is needed to complement b. INC uses P = a with carry in 1; DEC uses " +
    "P = not a with carry in 0. For the logic operations K = 1 and P itself is the result. The flags take ten more " +
    "library cells. Code columns are written C3 C2 C1 C0.");
}

// ======================================================================== 10 layouts
{
  const s = content("ALU", "Cell layouts",
    "Generated on an 8.0 µm row with every pin on a routing-track crossing; all 12 cells DRC-clean and LVS-matched");
  const h = 3.78;
  const a = img(s, path.join(FIGS, "layout_pl_fb4.png"), MX, TOP, 6.3, h, { alt: "Layout of pl_fb4", name: "Layout pl_fb4" });
  const b = img(s, path.join(FIGS, "layout_pl_cs.png"), a.x + a.w + 0.3, TOP, 6.0, h, { alt: "Layout of pl_cs",
    name: "Layout pl_cs" });
  caption(s, "pl_fb4: function block, 20 transistors", a.x + 0.15, a.y + a.h + 0.05, a.w);
  caption(s, "pl_cs: carry-sum cell, 24 transistors", b.x + 0.15, b.y + b.h + 0.05, b.w);
  const facts = [["8.0 µm", "row height, shared rails"], ["0.8 µm", "site width"],
    ["0.8 / 1.0 µm", "metal2 / metal1 track pitch"], ["12 cells", "Magic DRC 0, Netgen LVS match"]];
  facts.forEach(([v, l], i) => {
    const xx = MX + i * 3.08;
    txt(s, v, { x: xx, y: 6.0, w: 2.9, h: 0.45, fontSize: 22, bold: true, color: BLUE });
    txt(s, l, { x: xx, y: 6.45, w: 2.9, h: 0.35, fontSize: 13, color: MUTED });
  });
  s.addNotes("The layouts are produced by our cell generator from the transistor netlists: transistors are ordered " +
    "along shared diffusion, wide devices are folded, and a maze router connects poly, metal1 and metal2. NMOS sits on " +
    "the ground side, PMOS in a full-width n-well, substrate and well taps under the rails. Every pin pad is centred " +
    "on a crossing of the OSU018 routing tracks, so Qrouter can reach it in any placement orientation. All 12 cells " +
    "pass Magic DRC and Netgen LVS in the lab.");
}

// ======================================================================== 11 library
{
  const s = content("ALU", "Cell library pl018",
    "12 restoring cells and a filler, characterized with Ngspice from their extracted layouts");
  const rows = [
    ["pl_inv", "INV", "3", "2", "84 / 80", "9.5", "7"], ["pl_buf", "BUF", "4", "4", "131 / 136", "12.0", "28"],
    ["pl_nand2", "NAND2", "3", "4", "107 / 90", "10.4", "10"], ["pl_nor2", "NOR2", "3", "4", "117 / 130", "12.0", "9"],
    ["pl_and2", "AND2", "4", "6", "153 / 180", "9.6", "15"], ["pl_or2", "OR2", "4", "6", "178 / 177", "10.9", "15"],
    ["pl_xor2", "XOR2", "7", "10", "269 / 264", "13.9", "16"], ["pl_mux2", "MUX2", "9", "10", "279 / 323", "15.0", "12"],
    ["pl_mux2i", "MUX2I", "6", "8", "225 / 210", "18.0", "9"], ["pl_fa", "FA", "17", "24", "545 / 633", "14.0", "29"],
    { highlight: true, cells: ["pl_fb4", "FB4", "18", "20", "378 / 456", "21.7", "14"] },
    { highlight: true, cells: ["pl_cs", "CS", "17", "24", "395 / 400", "26.0", "30"] },
  ];
  table(s, ["Cell", "Function", "Sites", "T", "Delay r / f (ps)", "Cin (fF)", "Leak (pW)"], rows,
    { x: MX, y: TOP - 0.05, w: 7.7, colW: [1.25, 1.05, 0.8, 0.6, 1.75, 1.05, 1.2], fontSize: 13, rowH: 0.34,
      align: ["left", "left", "right", "right", "right", "right", "right"] });
  caption(s, "Worst arc at 16 fF load and 80 ps input slope; every cell DRC 0 and LVS match (lab, 22 Nov 2026)",
    MX, 6.48, 7.7);
  const x2 = 8.75, w2 = 3.98;
  const views = [
    ["Liberty", "NLDM 5 × 5 tables of delay and output slope against load and input slope; input capacitance; leakage"],
    ["LEF", "OSU018 technology section; pins are the complete metal of the pin net, internal nets are obstructions"],
    ["SPICE, Verilog", "for LVS, gate-level simulation and the transistor-level ALU test"],
  ];
  views.forEach(([h, d], i) => {
    box(s, x2, TOP + i * 1.5, w2, 1.32, [{ text: h, options: { bold: true, fontSize: 15, breakLine: true } },
      { text: d, options: { fontSize: 13, color: MUTED } }], { align: "left", valign: "top",
      extra: { margin: [10, 8, 8, 8], objectName: "View " + h } });
  });
  s.addNotes("Only restoring cells go into the automated library, because synthesis may connect any output to any " +
    "load. Every cell is extracted from its layout and characterized with Ngspice into a 5 by 5 table, the same " +
    "format as the OSU018 library, so Yosys, OpenSTA and Qflow use it unchanged. Delays are the worst arc at 16 fF and " +
    "80 ps input slope. FB4 and CS are ordinary cells of this library.");
}

// ======================================================================== 12 transistor level
{
  const s = content("ALU", "The ALU from each cell set (before layout)",
    "With FB4 and CS the ALU needs 53 % fewer transistors and 75 % less energy than with static CMOS cells");
  table(s, ["Cell set", "Cells", "Transistors", "Worst delay (ps)", "Energy / op (fJ)", "Leakage (nW)", "Energy × delay (fJ ns)"], [
    ["Gate-level cells (NAND-based)", "60", "842", "2925.4", "2039.6", "1.41", "5966.6"],
    ["D1: static CMOS", "60", "578", "2979.3", "3509.8", "2.02", "10456.7"],
    ["D2: minimum-PDP cells", "69", "402", "2270.8", "1102.1", "0.81", "2502.6"],
    ["pl018 cells, hand-mapped slice", "66", "458", "2310.4", "1312.8", "0.93", "3033.1"],
    { highlight: true, cells: ["P: FB4 + CS per bit", "28", "272", "2076.2", "870.6", "0.47", "1807.5"] },
  ], { x: MX, y: TOP, w: CW, colW: [3.45, 0.9, 1.3, 1.65, 1.6, 1.38, 1.85], fontSize: 14, rowH: 0.42,
    align: ["left", "right", "right", "right", "right", "right", "right"] });
  caption(s, "Ngspice 46, 1.8 V, 27 °C, FO4 loads; 229 transitions, all correct in every design; lab run of 16 Nov 2026",
    MX, 4.5, CW);
  txt(s, "P against D1 (static CMOS)", { x: MX, y: 5.0, w: 6, h: 0.32, fontSize: 14, bold: true });
  [["−53 %", "transistors"], ["−30 %", "worst delay"], ["−75 %", "energy per operation"], ["−76 %", "leakage"],
    ["−83 %", "energy × delay"]].forEach(([v, l], i) => stat(s, MX + i * 2.45, 5.38, 2.3, v, l));
  s.addNotes("The same 4-bit ALU composed from five cell sets and simulated at transistor level. Optimized cells " +
    "alone (D2) already cut energy by two thirds against static CMOS. The FB4/CS slice goes further: 272 transistors, " +
    "the shortest worst-case delay of the five and 871 femtojoule per operation. Against D2 it still saves 32 percent " +
    "of the transistors, 9 percent delay and 21 percent energy.");
}

// ======================================================================== 13 automated implementation
pres.addSection({ title: "Implementation and results" });
{
  const s = content("Implementation and results", "Automated implementation with Yosys and Qflow",
    "Seven routed ALUs: complete routing, LVS match, Magic DRC 0, all 229 transitions correct after extraction");
  const flow = ["Yosys", "gate-level test", "OpenSTA", "Qflow place, route", "Netgen LVS", "Magic DRC, real cells",
    "flat extraction", "Ngspice test"];
  const fw = 1.36, fg = 0.175;
  flow.forEach((f, i) => {
    const xx = MX + i * (fw + fg);
    box(s, xx, TOP, fw, 0.62, [{ text: f, options: { fontSize: 12 } }], { extra: { objectName: "Impl step " + (i + 1) } });
    if (i < flow.length - 1) arrow(s, xx + fw + 0.02, TOP + 0.31, xx + fw + fg - 0.02, TOP + 0.31, { width: 1.25 });
  });
  table(s, ["Design", "Library", "Netlist cells", "Placed cells", "Die (µm)", "Area (µm²)", "Transistors", "C (fF)"], [
    ["D3 beh", "OSU018", "122", "147", "97.6 × 56.0", "5466", "793", "875"],
    ["D3 slice", "OSU018", "74", "104", "84.0 × 46.0", "3864", "525", "563"],
    ["D3 map", "OSU018", "55", "63", "76.0 × 46.0", "3496", "534", "455"],
    ["D4 beh", "pl018", "146", "198", "84.0 × 54.0", "4536", "716", "655"],
    ["D4 slice", "pl018", "87", "110", "78.4 × 38.0", "2979", "454", "429"],
    ["D4 map", "pl018", "60", "94", "69.6 × 46.0", "3202", "484", "528"],
    { highlight: true, cells: ["P fb", "pl018", "27", "55", "57.6 × 38.0", "2189", "316", "324"] },
  ], { x: MX, y: 2.85, w: CW, colW: [1.35, 1.25, 1.5, 1.5, 1.95, 1.5, 1.6, 1.483], fontSize: 14, rowH: 0.38,
    align: ["left", "left", "right", "right", "right", "right", "right", "right"] });
  txt(s, "beh: behavioural RTL; slice: bit-sliced RTL; map: hand-mapped netlist with full adders and inverting " +
    "multiplexers; fb: hand-mapped FB4/CS netlist. Placed cells include the buffers inserted by Qflow; transistors " +
    "and C from the extracted layout.", { x: MX, y: 6.0, w: CW, h: 0.8, fontSize: 13, color: MUTED });
  s.addNotes("Three descriptions of the ALU go through the complete open-source flow, once with the OSU 0.18 micron " +
    "library (D3) and once with our library (D4); the proposed ALU is the hand-mapped FB4/CS netlist with our library. " +
    "All seven designs route completely, match LVS, have zero Magic DRC errors with the real cell layouts, and the " +
    "extracted netlists pass all 229 transitions. The proposed ALU is the smallest: 2189 square micron and 316 " +
    "transistors.");
}

// ======================================================================== 14 routed layout
{
  const s = content("Implementation and results", "Routed layout of the proposed ALU",
    "Placed and routed by Qflow with the pl018 cells; the extracted netlist passes the full ALU test");
  const a = img(s, path.join(ASSETS, "scr_klayout_fb.png"), MX, TOP, 8.1, 4.6, { frame: true,
    alt: "KLayout view of the routed proposed ALU", name: "KLayout screenshot" });
  caption(s, "KLayout: alu4_full.gds written by Magic, with the cell layouts and the routing", MX, a.y + a.h + 0.05, a.w);
  const x2 = a.x + a.w + 0.35, w2 = W - MX - x2;
  txt(s, [
    { text: "55 placed cells: 27 netlist cells and the buffers inserted by Qflow", options: { bullet: true, breakLine: true } },
    { text: "Die 57.6 × 38.0 µm (2189 µm²)", options: { bullet: true, breakLine: true } },
    { text: "Routing complete; Qflow LVS match; Magic DRC 0 with the real cells", options: { bullet: true, breakLine: true } },
    { text: "Extracted: 316 transistors and 324 fF of parasitic capacitance", options: { bullet: true } },
  ], { x: x2, y: TOP, w: w2, h: 2.4, fontSize: 15, paraSpaceAfter: 6 });
  const b = img(s, path.join(ASSETS, "scr_ngspice_chip_fb.png"), x2, 4.45, w2, 1.9, { frame: true,
    alt: "Ngspice simulation of the extracted layout", name: "Ngspice screenshot" });
  caption(s, "Ngspice: extracted layout, 32 vectors, all correct", x2, b.y + b.h + 0.05, w2);
  s.addNotes("This is the routed proposed ALU in KLayout, from the GDS that Magic writes with the real cell layouts. " +
    "Qflow added buffers on the high-fanout nets, mainly the code lines and the select inputs. The layout is " +
    "extracted with every transistor and capacitance, and the extracted netlist is simulated: on the right the 32-vector " +
    "function test of all eight operations, which I will also run live.");
}

// ======================================================================== 15 after layout
{
  const s = content("Implementation and results", "Performance after layout",
    "The proposed ALU has the lowest energy, leakage and energy-delay product of the seven routed ALUs");
  const labels = ["D3 beh", "D3 slice", "D3 map", "D4 beh", "D4 slice", "D4 map", "P fb"];
  const cols = [GRAY, GRAY, GRAY, GRAY, GRAY, GRAY, EMPH];
  txt(s, "Energy per operation (fJ)", { x: MX, y: TOP, w: 5.9, h: 0.32, fontSize: 14, bold: true });
  hbar(s, MX, TOP + 0.3, 5.9, 3.0, labels, [4898.7, 3333.0, 3807.1, 2798.5, 2140.4, 2077.3, 1453.0], cols,
    { max: 5900, objectName: "Energy after layout chart" });
  txt(s, "Worst-case delay (ps)", { x: 6.83, y: TOP, w: 5.9, h: 0.32, fontSize: 14, bold: true });
  hbar(s, 6.83, TOP + 0.3, 5.9, 3.0, labels, [1812.0, 2144.4, 3476.1, 1874.0, 2257.1, 3220.6, 2615.4], cols,
    { max: 4200, objectName: "Delay after layout chart" });
  txt(s, "P against the best D3 value of each quantity", { x: MX, y: 5.35, w: 8, h: 0.32, fontSize: 14, bold: true });
  [["−56 %", "energy per operation"], ["−68 %", "leakage (0.69 nW)"], ["−47 %", "energy × delay"],
    ["−37 %", "die area"]].forEach(([v, l], i) => stat(s, MX + i * 2.35, 5.68, 2.2, v, l, { size: 32 }));
  box(s, 10.15, 5.4, 2.58, 1.35, [{ text: "Worst delay +44 % against D3 beh (synthesized, 147 cells); −25 % " +
    "against D3 map", options: { fontSize: 12 } }], { align: "left", valign: "middle",
    extra: { margin: [8, 8, 6, 6], objectName: "Delay note" } });
  s.addNotes("After layout, same test on the extracted netlists. Our library alone (D4 against D3, same RTL) saves 36 " +
    "to 45 percent energy. The proposed ALU is lowest in energy, leakage, energy-delay product and area. It is not " +
    "the fastest: the synthesized behavioural design of D3 uses a faster carry structure with many more cells, and the " +
    "worst path of the proposed ALU is a select change that goes through the decoder, the code-line buffers and the " +
    "four-bit carry chain to the overflow flag. Comparisons with D3 use the best D3 value of each quantity: energy and " +
    "energy-delay against D3 slice, leakage and area against D3 map.");
}

// ======================================================================== 16 demo
pres.addSection({ title: "Demonstration" });
{
  const s = content("Demonstration", "Live demonstration in the lab",
    "The design data in the tools that produced and checked it: one command per view");
  const steps = [
    ["schematic fb4", "Xschem: transistor schematic of FB4"],
    ["cell-sim fb4", "Ngspice: FB4 with the ALU function codes, checked"],
    ["layout fb4", "Magic and Netgen: DRC, extraction, LVS"],
    ["chip fb", "KLayout: the routed proposed ALU"],
    ["chip-sim fb", "Ngspice: the extracted layout, eight operations"],
    ["results", "result tables of the lab runs"],
  ];
  steps.forEach(([cmd, d], i) => {
    const yy = TOP + i * 0.78;
    txt(s, String(i + 1), { x: MX, y: yy, w: 0.35, h: 0.4, fontSize: 18, bold: true, color: BLUE });
    txt(s, [{ text: "bash demo/show.sh " + cmd, options: { fontFace: "Courier New", fontSize: 13, bold: true,
      breakLine: true } }, { text: d, options: { fontSize: 13, color: MUTED } }],
    { x: MX + 0.42, y: yy, w: 4.6, h: 0.7 });
  });
  const shots = [["scr_xschem_fb4.png", "Xschem"], ["scr_magic_fb4.png", "Magic"],
    ["scr_ngspice_fb4.png", "Ngspice"], ["scr_klayout_fb.png", "KLayout"]];
  const gx = 5.85, gw = 3.35, gh = 2.05, ggx = 0.18, ggy = 0.45;
  shots.forEach(([f, cap], i) => {
    const xx = gx + (i % 2) * (gw + ggx), yy = TOP + Math.floor(i / 2) * (gh + ggy);
    const r = img(s, path.join(ASSETS, f), xx, yy, gw, gh, { frame: true, center: true,
      alt: cap + " screenshot", name: cap + " screenshot" });
    caption(s, cap, xx, r.y + r.h + 0.04, gw, { align: "center" });
  });
  s.addNotes("Order of the demonstration, about ten minutes: the FB4 schematic in Xschem, its simulation with the " +
    "function codes of the ALU, the layout in Magic with a fresh DRC and LVS against the schematic, the routed ALU in " +
    "KLayout (press * to show the cell contents and F2 to fit), the simulation of the extracted layout, and the result " +
    "tables. Every view starts from the files in the repository and the outputs of the last lab run.");
}

// ======================================================================== 17 conclusions
pres.addSection({ title: "Conclusion" });
{
  const s = content("Conclusion", "Conclusions and future work", null);
  const res = [
    ["Cells", "Transmission-gate circuits at minimum PDP: −53 to −65 % PDP for XOR2, MUX2 and the full adder against static CMOS."],
    ["ALU-specific cells", "FB4 and CS form one ALU bit with 44 transistors; at transistor level the ALU needs 272 transistors and 871 fJ per operation (−53 % and −75 % against static CMOS)."],
    ["Library in a standard flow", "pl018 (12 cells, DRC and LVS clean, characterized) works in Yosys and Qflow; for the same netlists it uses 36–45 % less energy than the OSU 0.18 µm cells."],
    ["After layout", "The proposed ALU has the smallest die (2189 µm²) and the lowest energy (1453 fJ), leakage (0.69 nW) and energy × delay of the seven routed ALUs; its worst delay (2.62 ns) is above the synthesized designs."],
  ];
  res.forEach(([h, d], i) => {
    const yy = 1.15 + i * 1.3;
    txt(s, [{ text: h, options: { bold: true, breakLine: true, color: BLUE } }, { text: d }],
      { x: MX, y: yy, w: 7.3, h: 1.2, fontSize: 15 });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 1.15, w: 4.33, h: 5.45, rectRadius: 0.08,
    fill: { color: HEX.lt2 }, line: { color: HEX.lt2, width: 0 }, objectName: "Future work card" });
  txt(s, [
    { text: "Future work", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "Faster carry path: alternating carry polarity (one inverter less per bit), carry-lookahead variant",
      options: { bullet: true, breakLine: true } },
    { text: "Drive strengths X2 and X4 in pl018 to reduce the buffers Qflow inserts", options: { bullet: true, breakLine: true } },
    { text: "Supply, temperature and Monte Carlo analysis of the transmission-gate paths", options: { bullet: true, breakLine: true } },
    { text: "8-bit version (the width is a parameter of the RTL and the generators)", options: { bullet: true } },
  ], { x: 8.65, y: 1.4, w: 3.85, h: 5.0, fontSize: 15, paraSpaceAfter: 10 });
  s.addNotes("Four results: optimized cells, the two ALU cells, a working library in the standard open-source flow, " +
    "and the after-layout comparison, where the proposed ALU wins on area, energy, leakage and energy-delay but not on " +
    "raw delay. The future work addresses exactly that delay: a carry path with alternating polarity and stronger " +
    "drivers, plus corner and Monte Carlo analysis.");
}

// ======================================================================== 18 references
{
  const s = content("Conclusion", "References", null);
  const refs = [
    "C. Mead and L. Conway, Introduction to VLSI Systems. Reading, MA: Addison-Wesley, 1980.",
    "N. H. E. Weste and D. M. Harris, CMOS VLSI Design: A Circuits and Systems Perspective, 4th ed. Boston: Addison-Wesley, 2011.",
    "J. M. Rabaey, A. Chandrakasan and B. Nikolić, Digital Integrated Circuits: A Design Perspective, 2nd ed. Upper Saddle River, NJ: Prentice Hall, 2003.",
    "R. Zimmermann and W. Fichtner, “Low-power logic styles: CMOS versus pass-transistor logic,” IEEE J. Solid-State Circuits, vol. 32, no. 7, pp. 1079–1090, Jul. 1997.",
    "Xilinx, 7 Series FPGAs Configurable Logic Block User Guide, UG474 (carry logic).",
    "MOSIS, Scalable CMOS (SCMOS) Design Rules, revision 8.",
    "R. T. Edwards, Qflow, Magic, Netgen and Qrouter, Open Circuit Design; C. Wolf, Yosys Open SYnthesis Suite; Ngspice; KLayout; Xschem.",
  ];
  txt(s, refs.map((r, i) => ({ text: r, options: { bullet: { type: "number" }, breakLine: i < refs.length - 1 } })),
    { x: MX, y: 1.2, w: CW, h: 5.5, fontSize: 15, paraSpaceAfter: 10 });
  s.addNotes("Mead and Conway for the function-block principle, the FPGA user guide for the propagate-steered carry " +
    "multiplexer, the standard textbooks for cell design, and Zimmermann and Fichtner for the comparison of logic styles.");
}

// ======================================================================== backup
pres.addSection({ title: "Backup" });
{
  const s = content("Backup", "Project library against the OSU 0.18 µm cells",
    "Same netlists, other cells (D4 against D3): energy −36 to −45 %, leakage −36 to −52 %, delay within ±7 %");
  s.addChart(pres.charts.BAR, [
    { name: "D3, OSU018", labels: ["beh", "slice", "map"], values: [4898.7, 3333.0, 3807.1] },
    { name: "D4, pl018", labels: ["beh", "slice", "map"], values: [2798.5, 2140.4, 2077.3] },
  ], Object.assign({}, AXIS, { x: MX, y: TOP + 0.35, w: 5.6, h: 3.9, barDir: "col", chartColors: [GRAY, EMPH],
    catAxisLabelFontSize: 13, catAxisLabelColor: "3C4043", catAxisLineColor: "C9CCD1", catGridLine: { style: "none" },
    valGridLine: { style: "none" }, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 5600, showValue: true,
    dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFormatCode: "0",
    barGapWidthPct: 60, showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: "3C4043",
    objectName: "D3 D4 energy chart" }));
  txt(s, "Energy per operation after layout (fJ)", { x: MX, y: TOP, w: 5.6, h: 0.32, fontSize: 14, bold: true });
  table(s, ["D4 against D3", "beh", "slice", "map"], [
    ["Placed cells", "+35 %", "+6 %", "+49 %"], ["Die area", "−17 %", "−23 %", "−8 %"],
    ["Worst delay", "+3.4 %", "+5.3 %", "−7.4 %"], ["Energy per operation", "−42.9 %", "−35.8 %", "−45.4 %"],
    ["Leakage", "−36.1 %", "−44.8 %", "−52.3 %"], ["Energy × delay", "−40.9 %", "−32.4 %", "−49.4 %"],
  ], { x: 6.75, y: TOP, w: 5.98, colW: [2.45, 1.18, 1.18, 1.17], fontSize: 14, rowH: 0.44,
    align: ["left", "right", "right", "right"] });
  txt(s, "More placed cells with pl018: a single drive strength, so Qflow inserts more buffers. The smaller cells " +
    "still give a smaller die.", { x: 6.75, y: 5.3, w: 5.98, h: 0.9, fontSize: 13, color: MUTED });
  s.addNotes("Backup for questions about the library alone. Same RTL, same flow settings; only the cell library " +
    "differs.");
}
{
  const s = content("Backup", "Energy per operation after layout",
    "The proposed ALU is lowest in every operation; the logic operations gain most (967–1188 fJ)");
  const ops = ["ADD", "SUB", "INC", "DEC", "AND", "OR", "XOR", "NOT"];
  const data = [
    ["D3 beh", [5397, 5520, 3947, 5445, 4934, 4413, 4778, 4755]],
    ["D3 slice", [4304, 3780, 2616, 3535, 3495, 3067, 3006, 2860]],
    ["D3 map", [4865, 4741, 2820, 4529, 3913, 3638, 2792, 3160]],
    ["D4 beh", [3209, 3228, 2304, 2906, 2764, 2439, 2725, 2813]],
    ["D4 slice", [2519, 2962, 1621, 2282, 2129, 2044, 1734, 1833]],
    ["D4 map", [3119, 2762, 1705, 2293, 2026, 1629, 1460, 1626]],
  ];
  const rows = data.map(([n, v]) => [n, ...v.map(String)]);
  rows.push({ highlight: true, cells: ["P fb", "1807", "1857", "1610", "1953", "1104", "967", "1138", "1188"] });
  table(s, ["Design (fJ)", ...ops], rows, { x: MX, y: TOP, w: CW, colW: [1.733, ...Array(8).fill(1.3)], fontSize: 14,
    rowH: 0.44, align: ["left", ...Array(8).fill("right")] });
  txt(s, "Mean over 24 random operand changes per operation, energy drawn from the ALU supply (drivers excluded), " +
    "netlists extracted from the routed layouts.", { x: MX, y: 5.6, w: CW, h: 0.6, fontSize: 13, color: MUTED });
  s.addNotes("Backup: energy per operation for every routed design. The proposed ALU computes the logic operations " +
    "directly in FB4, without passing through an adder, which is why AND, OR, XOR and NOT cost about 1 pJ.");
}
{
  const s = content("Backup", "Verification at transistor level",
    "Function test of the proposed ALU before layout: 32 vectors, eight operations, every result and flag as expected");
  const a = img(s, path.join(FIGS, "wave_alu_fb.png"), MX, TOP, 8.1, 4.4, { alt: "ALU waveforms", name: "ALU waveforms" });
  caption(s, "Ngspice: operands, result y and flags (8c + 4v + 2z + n); circles: expected values", MX, a.y + a.h + 0.05, a.w);
  table(s, ["Level", "Check"], [
    ["RTL, gate level", "2048 vectors (iverilog)"], ["Transistor netlists", "2048 vectors, switch level"],
    ["Transistor level", "229 transitions (Ngspice)"], ["Cell layouts", "Magic DRC, Netgen LVS"],
    ["Routed layouts", "LVS, DRC, 229 transitions"],
  ], { x: 9.0, y: TOP, w: 3.73, colW: [1.75, 1.98], fontSize: 13, rowH: 0.5 });
  s.addNotes("Backup: the verification levels. Every generated netlist is evaluated at switch level on all 2048 " +
    "input combinations before it is committed, and every simulated design is checked cycle by cycle against the " +
    "reference model.");
}

// ---------------------------------------------------------------- write
(async () => {
  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(THEME_JS);
  await applyTheme(OUT, THEME);
  console.log("wrote " + path.relative(ROOT, OUT));
})().catch((e) => { console.error(e); process.exit(1); });
