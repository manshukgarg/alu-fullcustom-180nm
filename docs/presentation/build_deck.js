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
  background: { color: HEX.lt1 },
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
    { text: { text: "Full-Custom ALU Using Optimized Standard Cells", options: { x: MX, y: 7.03, w: 6, h: 0.28, fontSize: 10,
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
// short version (9 slides): the flow, waveform and reference slides are kept in the code but not built
const FULL = false;

// ======================================================================== 1 title
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  // logo of the institute (supplied by the team), centred at the top
  const logo = path.join(ROOT, "docs", "figures", "logo", "thapar_logo.png");
  const lh = 1.7, lsz = pngSize(logo), lw = lh * lsz.w / lsz.h;
  s.addImage({ path: logo, x: (W - lw) / 2, y: 0.5, w: lw, h: lh, altText: "Thapar Institute of Engineering and Technology",
    objectName: "Thapar logo" });
  txt(s, "Design and Performance Analysis of a Full-Custom ALU Using Optimized Standard Cells",
    { x: 1.0, y: 2.4, w: W - 2.0, h: 1.2, fontSize: 32, bold: true, color: INK, align: "center", valign: "middle",
      fontFace: THEME.headFontFace, objectName: "Project title" });
  s.addShape(pres.shapes.LINE, { x: (W - 1.6) / 2, y: 3.85, w: 1.6, h: 0, line: { color: BLUE, width: 2 },
    objectName: "Title rule" });
  // submitted by: names and roll numbers in two aligned columns
  const team = [["Aditya Kumar", "6026620002"], ["Gourangi Tyagi", "6026620016"], ["Kashish Goyal", "6026620019"],
    ["Manshuk Garg", "6026620022"]];
  const lx = 1.75, cy = 4.3;
  txt(s, "Submitted by", { x: lx, y: cy, w: 4.6, h: 0.4, fontSize: 18, bold: true, color: BLUE });
  const none = { type: "none" };
  s.addTable(team.map(([n, r]) => [
    { text: n, options: { color: INK, border: [none, none, none, none] } },
    { text: r, options: { color: INK, border: [none, none, none, none] } }]),
  { x: lx, y: cy + 0.5, w: 4.6, colW: [2.5, 2.1], fontSize: 18, fontFace: THEME.bodyFontFace, rowH: 0.42,
    margin: [0, 0, 0, 0], valign: "middle", autoPage: false, objectName: "Team" });
  // submitted to
  const rx = 7.55;
  txt(s, "Submitted to", { x: rx, y: cy, w: 4.6, h: 0.4, fontSize: 18, bold: true, color: BLUE });
  txt(s, [
    { text: "Dr. Arun Kumar Chatterjee", options: { bold: true, breakLine: true } },
    { text: "Assistant Professor", options: { breakLine: true } },
    { text: "Department of Electronics and Communication Engineering" },
  ], { x: rx, y: cy + 0.5, w: 4.6, h: 1.6, fontSize: 18, color: INK, paraSpaceAfter: 6 });
  s.addNotes("Our project is the design and performance analysis of a full-custom ALU using optimized standard " +
    "cells: a 4-bit ALU in 180 nm CMOS built from our own optimized cell library, plus two cells designed " +
    "specifically for the ALU bit. The same ALU is compared in several versions, at transistor level and after " +
    "automatic place and route, with one common measurement. Everything was run in the NIELIT ChipCraft lab with " +
    "open-source tools; a live demonstration follows the slides.");
}

// ======================================================================== 2 objectives and specification
{
  const s = content("Introduction", "Objectives and specification",
    "A 4-bit ALU in 180 nm CMOS from minimum-PDP cells and two ALU-specific cells, compared before and after layout");
  const items = [
    ["Optimize the cells", "Topology and sizing of XOR2, MUX2, full adder and gates for minimum power-delay product"],
    ["Design cells for the ALU bit", "Function block FB4 and carry-sum cell CS: one ALU bit from two cells"],
    ["Build and use a cell library", "Layout, DRC and LVS, characterization; automatic place and route with Yosys and Qflow"],
    ["Compare complete ALUs", "One transistor-level test for every design, before layout and on the extracted layout"],
  ];
  items.forEach(([h, d], i) => {
    const y = TOP + 0.05 + i * 1.05;
    txt(s, String(i + 1).padStart(2, "0"), { x: MX, y, w: 0.6, h: 0.5, fontSize: 24, bold: true, color: BLUE });
    txt(s, [{ text: h, options: { bold: true, breakLine: true } }, { text: d, options: { color: MUTED, fontSize: 14 } }],
      { x: MX + 0.75, y: y + 0.02, w: 5.55, h: 0.95, fontSize: 16 });
  });
  table(s, ["s2 s1 s0", "Operation", "Result y"], [
    ["0 0 0", "ADD", "a + b"], ["0 0 1", "SUB", "a − b"], ["0 1 0", "INC", "a + 1"], ["0 1 1", "DEC", "a − 1"],
    ["1 0 0", "AND", "a and b"], ["1 0 1", "OR", "a or b"], ["1 1 0", "XOR", "a xor b"], ["1 1 1", "NOT", "not a"],
  ], { x: 7.35, y: TOP, w: 5.38, colW: [1.4, 1.6, 2.38], fontSize: 14, rowH: 0.35 });
  txt(s, "Flags: C carry (1 = no borrow), V overflow, Z zero, N negative.",
    { x: 7.35, y: 5.25, w: 5.38, h: 0.6, fontSize: 14 });
  txt(s, "TSMC 0.18 µm CMOS, 1.8 V, 27 °C; SCMOS SCN6M_SUBM rules [22], λ = 0.1 µm. Ngspice 46 [24], Xschem, " +
    "Magic [23], Netgen, Yosys [25], Qflow [26], OpenSTA, KLayout in the NIELIT ChipCraft lab.", { x: MX, y: 6.3, w: CW, h: 0.55, fontSize: 13, color: MUTED });
  s.addNotes("Four objectives: optimized cells, two cells made for the ALU bit, a library that the standard open-source " +
    "flow can use, and a fair comparison of complete ALUs. The ALU has eight operations selected by s2 to s0 and four " +
    "flags. Technology: TSMC 0.18 micron at 1.8 volt with the SCMOS rules of the Qflow kit; every tool runs in the " +
    "ChipCraft lab.");
}

// ======================================================================== 3 literature survey
{
  const s = content("Introduction", "Literature survey (2021–2026)",
    "Recent work improves single cells or the logic style of a whole ALU; few designs are compared after place and route");
  const cols = [
    ["Arithmetic cells", [
      ["Hussain et al. 2022 [1]", "18T hybrid FA: PDP \u221267\u00a0%"],
      ["Sadeghi et al. 2022 [2]", "TG FA with full-swing carry"],
      ["Arul, Kathirvelu 2024 [3]", "20T hybrid FA, 45\u00a0nm"],
      ["Yin et al. 2023 [4]", "PTL FA: \u221213.8\u00a0% power"],
      ["Nirmalraj et al. 2023 [5]", "10T GDI FA, ten nodes"],
      ["Sharma, Jhamb 2024 [6]", "XOR\u2013XNOR cells compared"]]],
    ["ALU designs", [
      ["Subbulakshmi et al. 2023 [7]", "GDI ALU, 65\u00a0nm: \u221291\u00a0% power"],
      ["Jyothi et al. 2024 [8]", "adiabatic (ECRL) ALU"],
      ["Kannan Nithin et al. 2024 [9]", "32-bit MUX-based ALU, 180\u00a0nm"],
      ["Karapothula et al. 2026 [10]", "ALU at 180, 90 and 45\u00a0nm"]]],
    ["Cell sizing and libraries", [
      ["Chen et al. 2022 [11]", "65\u00a0nm ultralow-voltage library"],
      ["Lim et al. 2023 [12]", "P/N ratio, cell height: \u221255\u00a0% energy"],
      ["Cao, Guo 2024 [13]", "optimal P/N ratio under variation"]]],
    ["Cell layout and open flows", [
      ["Ren, Fojtik 2021 [14]", "NVCell: cell layout by learning"],
      ["Lee et al. 2021 [15]", "SMT cell place and route, 7\u00a0nm"],
      ["Nishizawa, Nakura 2023 [16]", "Libretto cell characterizer"],
      ["Edwards et al. 2021 [17]", "OpenLane: RISC-V SoC, open flow"]]],
  ];
  const gw = 0.18, cw = (CW - 3 * gw) / 4, chh = 3.72;
  cols.forEach(([head, items], i) => {
    const x = MX + i * (cw + gw);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: TOP, w: cw, h: chh, rectRadius: 0.06, fill: { color: CARD },
      line: { color: RULE, width: 0.75 }, objectName: "Survey: " + head });
    txt(s, head, { x: x + 0.15, y: TOP + 0.14, w: cw - 0.3, h: 0.42, fontSize: 16, bold: true, color: BLUE });
    const runs = [];
    items.forEach(([a, b], j) => {
      runs.push({ text: a, options: { bold: true, breakLine: true } });
      runs.push({ text: b, options: { color: MUTED, breakLine: j < items.length - 1 } });
    });
    txt(s, runs, { x: x + 0.15, y: TOP + 0.62, w: cw - 0.3, h: chh - 0.72, fontSize: 12, paraSpaceAfter: 3 });
  });
  box(s, MX, TOP + chh + 0.18, CW, 0.86, [
    { text: "Gaps addressed here:  ", options: { bold: true, color: BLUE } },
    { text: "cells evaluated alone, not in a routed datapath  ·  ALU logic and arithmetic in separate units  ·  open " +
      "flows used only with the libraries of a process kit  →  FB4 and CS cells, the pl018 library, seven ALUs " +
      "compared after layout" }],
  { fill: TINT, line: BLUE, align: "left", extra: { fontSize: 14, objectName: "Research gaps" } });
  s.addNotes("Seventeen papers from 2021 to 2026, in four groups; the numbers refer to the reference slides at the end. " +
    "Hybrid and transmission-gate adders keep improving the power-delay product of single cells, but at different " +
    "nodes and loads, and mostly without layout. Recent ALUs use GDI, adiabatic or multiplexer-based logic, with " +
    "arithmetic and logic in separate units. Library papers size the P/N ratio per cell, and layout generators and " +
    "open characterizers now make a custom library usable in an open flow. Three gaps follow, and our three " +
    "contributions answer them.");
}

// ======================================================================== 4 flow
if (FULL) {
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
    "the drivers give the PDP. Selected: minimum PDP with full output swing. Logic styles and metrics: [19]\u2013[21].",
  { x: MX, y: 5.75, w: CW, h: 0.95, fontSize: 13, color: MUTED });
  s.addNotes("Each function had several candidate circuits: static CMOS, gate-level, transmission-gate, buffered " +
    "transmission-gate, CPL and pass-transistor variants, 21 in all. Each was simulated at 40 sizes and the size with the " +
    "minimum power-delay product and full swing was kept. Gains are small for simple gates and large for XOR, " +
    "multiplexer and full adder, where transmission gates replace stacked static CMOS. For the automated-flow library " +
    "the restoring versions (with an output inverter) are used, because the synthesis tool connects cells freely.");
}

// ======================================================================== 5 proposed cells
{
  const s = content("Cell design", "Proposed cells FB4 and CS",
    "One ALU bit from two cells (44 transistors); PDP −12 % and −18 % against the same functions built from library cells");
  const cw = 5.9, gap = 0.33;
  const a = img(s, path.join(ASSETS, "schematic_fb4.png"), MX, TOP - 0.05, cw, 2.95,
    { center: true, alt: "Transistor schematic of FB4", name: "FB4 schematic" });
  const b = img(s, path.join(ASSETS, "schematic_cs.png"), MX + cw + gap, TOP - 0.05, cw, 2.95,
    { center: true, alt: "Transistor schematic of CS", name: "CS schematic" });
  const yb = TOP + 3.05;
  box(s, MX, yb, cw, 0.62, [{ text: "FB4 (20 T):  P = C[2A + B]", options: { bold: true, fontSize: 16 } }],
    { fill: TINT, line: BLUE, align: "left", extra: { objectName: "FB4 function", margin: [12, 8, 4, 4] } });
  box(s, MX + cw + gap, yb, cw, 0.62, [{ text: "CS (24 T):  CO = P ? CI : A;   Y = K ? P : P xor CI",
    options: { bold: true, fontSize: 16 } }], { fill: TINT, line: BLUE, align: "left",
    extra: { objectName: "CS function", margin: [12, 8, 4, 4] } });
  txt(s, [
    { text: "A and B select one of the four code lines C0..C3, so P can be any function of A and B (function-block principle [18]).",
      options: { bullet: true, breakLine: true } },
    { text: "450 ps, PDP 18.95 fJ; three MUX2I cells 21.58 fJ, static CMOS 70.78 fJ.", options: { bullet: true } },
  ], { x: MX, y: yb + 0.78, w: cw, h: 1.2, fontSize: 14, paraSpaceAfter: 4 });
  txt(s, [
    { text: "P = 0 means A equals the second operand bit, so the carry out is A: no generate signal.",
      options: { bullet: true, breakLine: true } },
    { text: "459 ps, PDP 33.64 fJ; library cells 41.08 fJ, static CMOS 93.84 fJ.", options: { bullet: true } },
  ], { x: MX + cw + gap, y: yb + 0.78, w: cw, h: 1.2, fontSize: 14, paraSpaceAfter: 4 });
  s.addNotes("FB4 is a 4-to-1 transmission-gate multiplexer: the operand bits select one of four code lines, so with " +
    "the right code its output is any function of a and b, the propagate signal for arithmetic or the result itself " +
    "for logic. The principle is the function block of the OM-2 data path of Mead and Conway; our part is the " +
    "restoring CMOS cell, its sizing, layout and use. CS is the carry multiplexer: when P is 0 the two bits are equal, " +
    "so the carry out is simply A, which removes the generate signal; K selects sum or logic result. Against the same " +
    "functions built from our optimized library cells they save 12 and 18 percent PDP, against static CMOS 73 and 64 " +
    "percent.");
}

// ======================================================================== 9 architecture
pres.addSection({ title: "ALU" });
{
  const s = content("ALU", "ALU bit slice",
    "One FB4 and one CS per bit (44 transistors); a shared decoder of ten library cells sets the code lines");
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
  const blocks = [["Decoder", "10 cells"], ["bit 0", "FB4 + CS"], ["bit 1", "FB4 + CS"], ["bit 2", "FB4 + CS"],
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

// ======================================================================== waveforms
if (FULL) {
  const s = content("ALU", "Simulation waveforms",
    "FB4 forms every function of A and B from its code lines; the ALU matches the reference model on all 32 vectors");
  const L1 = img(s, path.join(ASSETS, "wave_fb4_slide.png"), MX, TOP, 5.9, 4.25, { center: true,
    alt: "Ngspice waveforms of the FB4 cell for six operation codes", name: "FB4 waveforms" });
  caption(s, "FB4 cell: code lines set for six operations; A and B step through 00, 01, 10, 11 in each window",
    MX, L1.y + L1.h + 0.1, 5.9, { h: 0.5, align: "center" });
  const R1 = img(s, path.join(ASSETS, "wave_alu_slide.png"), MX + 6.23, TOP, 5.9, 4.25, { center: true,
    alt: "Ngspice function test of the proposed ALU: result and flags against expected values", name: "ALU waveforms" });
  caption(s, "Proposed ALU, 32-vector function test: lines simulated, circles expected; flags = 8C + 4V + 2Z + N",
    MX + 6.23, R1.y + R1.h + 0.1, 5.9, { h: 0.5, align: "center" });
  s.addNotes("Ngspice transient simulations at 1.8 volt with the same drivers and FO4 loads as all measurements. " +
    "Left: the FB4 cell; for each operation the four code lines are set, and P follows the code bit selected by A " +
    "and B, for example A xor B for ADD and A and B for AND. Right: the complete proposed ALU at transistor level; " +
    "for every one of the 32 vectors the simulated result and flags reach the expected value. The report appendix " +
    "has these waveforms with the CS cell and the slowest transition, and the netlists.");
}

// ======================================================================== 7 layout
pres.addSection({ title: "Implementation and results" });
// ---------------------------------------------------------------- Verilog to layout
{
  const s = content("Implementation and results", "From Verilog to layout",
    "Seven ALUs from three Verilog descriptions and the proposed netlist, through one open-source flow");
  table(s, ["Design", "Verilog description", "Cells", "Placed cells"], [
    ["D3 beh", "behavioural (alu4.v)", "OSU018", "147"],
    ["D3 slice", "bit-sliced (alu4_slice.v)", "OSU018", "104"],
    ["D3 map", "hand-mapped netlist", "OSU018", "63"],
    ["D4 beh", "behavioural (alu4.v)", "pl018", "198"],
    ["D4 slice", "bit-sliced (alu4_slice.v)", "pl018", "110"],
    ["D4 map", "hand-mapped netlist", "pl018", "94"],
    { highlight: true, cells: ["P (proposed)", "FB4/CS netlist, 27 cells", "pl018", "55"] },
  ], { x: MX, y: TOP, w: 5.9, colW: [1.35, 2.55, 0.95, 1.05], fontSize: 14, rowH: 0.4,
    align: ["left", "left", "left", "center"] });
  txt(s, [
    { text: "beh: ", options: { bold: true } }, { text: "Yosys chooses the structure.", options: { breakLine: true } },
    { text: "slice: ", options: { bold: true } }, { text: "one bit described and repeated four times.", options: { breakLine: true } },
    { text: "map: ", options: { bold: true } }, { text: "library cells placed by hand (Yosys cannot infer the two-output full adder)." },
  ], { x: MX, y: 5.35, w: 5.9, h: 1.1, fontSize: 13, color: MUTED });
  const fx = 6.95, fw = W - MX - fx, fh = 0.62, fg = 0.16;
  const steps = [
    ["1  RTL check", "Icarus Verilog, self-checking bench: all 2048 input combinations"],
    ["2  Synthesis", "Yosys maps the design onto the Liberty library (pl018 or OSU018)"],
    ["3  Gate-level check", "the same bench on the synthesized netlist"],
    ["4  Place and route", "Qflow: GrayWolf placement, Qrouter routing"],
    ["5  Sign-off", "Netgen LVS, Magic DRC with the real cells, extraction"],
    ["6  Post-layout test", "Ngspice: 229 transitions on the extracted netlist"],
  ];
  steps.forEach(([h, d], i) => {
    const y = TOP + i * (fh + fg);
    box(s, fx, y, fw, fh, [{ text: h, options: { bold: true, fontSize: 14, breakLine: true } },
      { text: d, options: { fontSize: 12, color: MUTED } }], { align: "left", fill: i === 5 ? TINT : CARD,
      line: i === 5 ? BLUE : RULE, extra: { objectName: "Flow step " + (i + 1) } });
    if (i < steps.length - 1) arrow(s, fx + 0.35, y + fh + 0.01, fx + 0.35, y + fh + fg - 0.01, { width: 1.25 });
  });
  txt(s, "All seven: routed, LVS match, DRC 0, 229/229 correct after extraction",
    { x: fx, y: TOP + 6 * (fh + fg) + 0.02, w: fw, h: 0.32, fontSize: 13, bold: true, color: BLUE });
  s.addNotes("This is the automated part. We wrote the ALU in Verilog three ways: a behavioural description where " +
    "Yosys decides the structure, a bit-sliced description, and a hand-mapped netlist that instantiates library " +
    "cells directly. Each was implemented twice, with the OSU 0.18 micron cells of the Qflow kit (D3) and with our " +
    "own library pl018 (D4); the proposed ALU P is a structural netlist of our cells. Every design first passes " +
    "an exhaustive self-checking Verilog test bench with Icarus Verilog, all 2048 input combinations, before and " +
    "after synthesis. Qflow then places and routes it, Netgen and Magic check LVS and DRC, Magic extracts every " +
    "transistor and parasitic capacitance, and the extracted netlist is simulated in Ngspice with the same 229-" +
    "transition bench as the transistor-level ALUs. All seven designs pass every step.");
}

{
  const s = content("Implementation and results", "Layout: cells and routed ALU",
    "Generated cells, DRC-clean and LVS-matched; the proposed ALU placed and routed by Qflow with these cells");
  const a = img(s, path.join(FIGS, "layout_pl_fb4.png"), MX, TOP, 4.65, 3.6, { alt: "Layout of pl_fb4", name: "Layout pl_fb4" });
  caption(s, "Cell pl_fb4, 14.4 × 8.0 µm", MX + 0.1, a.y + a.h + 0.04, a.w);
  const bx = MX + 4.95;
  const b = img(s, path.join(ASSETS, "scr_klayout_fb.png"), bx, TOP, W - MX - bx, 3.75, { frame: true,
    alt: "KLayout view of the routed proposed ALU", name: "KLayout screenshot" });
  caption(s, "Routed proposed ALU in KLayout (GDS written by Magic with the cell layouts)", bx, b.y + b.h + 0.04, b.w);
  const facts = [["12 cells", "row 8.0 µm, site 0.8 µm; DRC 0, LVS match"], ["2189 µm²", "proposed ALU: 57.6 × 38.0 µm, 55 placed cells"],
    ["7 ALUs", "routed; LVS match, DRC 0, 229/229 correct after extraction"], ["316 T", "extracted, with 324 fF of parasitic capacitance"]];
  facts.forEach(([v, l], i) => {
    const xx = MX + i * 3.08;
    txt(s, v, { x: xx, y: 5.95, w: 2.95, h: 0.45, fontSize: 22, bold: true, color: BLUE });
    txt(s, l, { x: xx, y: 6.4, w: 2.95, h: 0.5, fontSize: 12, color: MUTED });
  });
  s.addNotes("The cell layouts come from our generator: devices along shared diffusion, wide ones folded, a maze router " +
    "on poly, metal1 and metal2; every pin on a routing-track crossing. All twelve cells pass Magic DRC and Netgen LVS. " +
    "The library is characterized into Liberty tables, so Yosys and Qflow use it like the OSU library. On the right is " +
    "the routed proposed ALU in KLayout; seven ALUs were routed in total, all with LVS match, zero DRC errors and correct " +
    "results after extraction.");
}

// ======================================================================== 8 results
{
  const s = content("Implementation and results", "Results",
    "The proposed ALU has the lowest energy, leakage and area of the seven routed ALUs; it is not the fastest");
  const labels = ["D3 beh", "D3 slice", "D3 map", "D4 beh", "D4 slice", "D4 map", "P fb"];
  const cols = [GRAY, GRAY, GRAY, GRAY, GRAY, GRAY, EMPH];
  txt(s, "Energy per operation after layout (fJ)", { x: MX, y: TOP, w: 5.9, h: 0.32, fontSize: 14, bold: true });
  hbar(s, MX, TOP + 0.3, 5.9, 2.75, labels, [4898.7, 3333.0, 3807.1, 2798.5, 2140.4, 2077.3, 1453.0], cols,
    { max: 5900, objectName: "Energy after layout chart" });
  txt(s, "Worst-case delay after layout (ps)", { x: 6.83, y: TOP, w: 5.9, h: 0.32, fontSize: 14, bold: true });
  hbar(s, 6.83, TOP + 0.3, 5.9, 2.75, labels, [1812.0, 2144.4, 3476.1, 1874.0, 2257.1, 3220.6, 2615.4], cols,
    { max: 4200, objectName: "Delay after layout chart" });
  caption(s, "D3: OSU 0.18 µm cells; D4: project library pl018; P: FB4 + CS. beh, slice, map: behavioural, bit-sliced and " +
    "hand-mapped descriptions.", MX, 5.0, CW);
  txt(s, "Before layout, against static CMOS", { x: MX, y: 5.4, w: 4.6, h: 0.32, fontSize: 14, bold: true });
  [["−53 %", "transistors (272)"], ["−75 %", "energy per operation"]].forEach(([v, l], i) =>
    stat(s, MX + i * 2.35, 5.72, 2.2, v, l, { size: 30 }));
  txt(s, "After layout, against the best OSU018 design", { x: 5.6, y: 5.4, w: 7.1, h: 0.32, fontSize: 14, bold: true });
  [["−56 %", "energy (1453 fJ)"], ["−68 %", "leakage (0.69 nW)"], ["−37 %", "die area (2189 µm²)"]].forEach(([v, l], i) =>
    stat(s, 5.6 + i * 2.4, 5.72, 2.25, v, l, { size: 30 }));
  s.addNotes("Every design is measured with the same Ngspice test bench: two X1 inverters drive every input, FO4 loads, " +
    "229 transitions including the full carry ripples, all results checked. At transistor level the FB4/CS ALU needs " +
    "272 transistors and 871 fJ per operation, 53 and 75 percent below the static-CMOS ALU. After layout the proposed " +
    "ALU uses 1453 fJ per operation, 56 percent less than the best OSU018 design, with 68 percent less leakage and 37 " +
    "percent less area. It is not the fastest: the synthesized behavioural design reaches 1812 ps against our 2615 ps, " +
    "because our worst path runs from the select inputs through the decoder and the four-bit carry chain. " +
    "Live demonstration follows this slide (bash demo/tour.sh).");
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

// ======================================================================== references
{
  // IEEE references as in the project report: the 17 papers of the literature survey, then the background
  const R = require(path.join(ROOT, "docs", "report", "report_content.js")).refs;
  const keys = ["hussain2022", "sadeghi2022", "arul2023", "yin2023", "gdi10t2023", "sharma2024", "subbulakshmi2023",
    "jyothi2024", "eai2024", "karapothula2026", "chen2022", "lim2023", "sizing2024", "ren2021", "lee2021",
    "nishizawa2023", "edwards2021", "meadconway1980", "weste2011", "rabaey2003", "zimmermann1997", "mosis",
    "ousterhout1984", "ngspice", "yosys", "qflow"];
  // "*...*" in the report strings marks italics
  const rich = (str) => str.split("*").map((t, k) => ({ text: t, options: k % 2 ? { italic: true } : {} }))
    .filter((r) => r.text.length);
  const none = { type: "none" };
  const parts = [[0, 12], [12, keys.length]];
  parts.forEach(([a, b], pi) => {
    const s = content("Conclusion", "References (" + (pi + 1) + "/" + parts.length + ")", null);
    const rows = keys.slice(a, b).map((k, i) => {
      if (!R[k]) throw new Error("reference " + k);
      return [
        { text: "[" + (a + i + 1) + "]", options: { color: INK, valign: "top", border: [none, none, none, none] } },
        { text: rich(R[k]), options: { color: INK, valign: "top", border: [none, none, none, none] } }];
    });
    s.addTable(rows, { x: MX, y: 1.2, w: CW, colW: [0.55, CW - 0.55], fontSize: 11, fontFace: THEME.bodyFontFace,
      margin: [0.02, 0.04, 0.05, 0.02], autoPage: false, objectName: "References " + (pi + 1) });
    s.addNotes(pi === 0 ? "References [1] to [17] are the seventeen papers of the literature survey (2021 to 2026), " +
      "numbered as on slide 3." : "Background references: the function-block principle (Mead and Conway), the " +
      "standard texts on CMOS circuits, the comparison of logic styles, the design rules and the open-source tools.");
  });
}

// ---------------------------------------------------------------- write
(async () => {
  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(THEME_JS);
  await applyTheme(OUT, THEME);
  console.log("wrote " + path.relative(ROOT, OUT));
})().catch((e) => { console.error(e); process.exit(1); });
