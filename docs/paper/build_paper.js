// Research paper in the IEEE conference layout (US Letter, two columns, Times 10 pt), built with docx.
//
//   python3 docs/paper/make_paper_figures.py      (figures)
//   node docs/paper/build_paper.js                (writes docs/paper/ALU4_180nm_paper.docx)
//
// Every number is a lab result from results/lab/ (Steps 2, 5, 6) or results/ngspice46_2026-11-16/
// (Steps 3b, 3c; the lab runs of 16 and 21 Nov 2026 give identical values).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, SectionType, HeadingLevel, TabStopType, Tab, VerticalAlign,
} = require("docx");

const HERE = __dirname;
const ROOT = path.resolve(HERE, "..", "..");
const FIG = path.join(HERE, "figures");
const PRES = path.join(ROOT, "docs", "presentation", "assets");
const FIGS = path.join(ROOT, "docs", "figures", "presentation");
const OUT = path.join(HERE, "ALU4_180nm_paper.docx");

const FONT = "Times New Roman";
const COL = 5040; // column width, DXA (3.5 in)
const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1440, left: 900, right: 900 } };

// ---------------------------------------------------------------- text helpers
// markup: *italic*, _{subscript}, ^{superscript}
function runs(str, base = {}) {
  const out = [];
  let italic = false, buf = "";
  const mk = (text, extra = {}) => new TextRun(Object.assign({ text, font: base.font || FONT, size: base.size,
    bold: base.bold, italics: italic || base.italics, smallCaps: base.smallCaps }, extra));
  const flush = () => { if (buf) { out.push(mk(buf)); buf = ""; } };
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (ch === "*") { flush(); italic = !italic; continue; }
    if ((ch === "_" || ch === "^") && str[i + 1] === "{") {
      flush();
      const j = str.indexOf("}", i);
      out.push(mk(str.slice(i + 2, j), ch === "_" ? { subScript: true } : { superScript: true }));
      i = j;
      continue;
    }
    if (ch === "⊕") { flush(); out.push(mk("⊕", { font: "Cambria Math" })); continue; }
    buf += ch;
  }
  flush();
  return out;
}
function P(str, opt = {}) {
  return new Paragraph({ alignment: opt.align || AlignmentType.JUSTIFIED, indent: opt.noIndent ? undefined : { firstLine: 202 },
    spacing: { before: opt.before || 0, after: opt.after || 0 }, keepNext: opt.keepNext, children: runs(str, opt.run || {}) });
}
function H1(num, title) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: `${num}. ${title}`, font: FONT, smallCaps: true })] });
}
function H2(letter, title) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(`${letter}. ${title}`, { italics: true }) });
}
function item(label, str) {
  return new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { left: 288, hanging: 288 },
    children: [new TextRun({ text: label, font: FONT }), new TextRun({ children: [new Tab()] }), ...runs(str)],
    tabStops: [{ type: TabStopType.LEFT, position: 288 }] });
}
function equation(str, num) {
  return new Paragraph({ spacing: { before: 60, after: 60 },
    tabStops: [{ type: TabStopType.CENTER, position: COL / 2 }, { type: TabStopType.RIGHT, position: COL }],
    children: [new TextRun({ children: [new Tab()] }), ...runs(str), new TextRun({ children: [new Tab(), `(${num})`], font: FONT })] });
}
function pngSize(p) { const b = fs.readFileSync(p); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
let figNo = 0;
function figure(file, caption, widthIn = 3.4) {
  figNo += 1;
  const sz = pngSize(file);
  const w = Math.round(widthIn * 96), h = Math.round((widthIn * 96 * sz.h) / sz.w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: w, height: h },
        altText: { title: `Fig. ${figNo}`, description: caption, name: `fig${figNo}` } })] }),
    new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 },
      children: [new TextRun({ text: `Fig. ${figNo}. `, font: FONT, size: 16 }), ...runs(caption, { size: 16 })] }),
  ];
}
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
let tabNo = 0;
const RULE = { style: BorderStyle.SINGLE, size: 6, color: "000000" };
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function table(title, header, rows, widths, opt = {}) {
  tabNo += 1;
  const align = opt.align || header.map((_, i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER));
  const cell = (text, i, o = {}) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, columnSpan: o.span, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 15, bottom: 15, left: 50, right: 50 },
    borders: { top: o.top ? RULE : NONE, bottom: o.bottom ? RULE : NONE, left: NONE, right: NONE },
    children: [new Paragraph({ alignment: o.align || align[i], children: runs(String(text), { size: 16, bold: o.bold,
      italics: o.italics }) })],
  });
  const trs = [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, { top: true, bottom: true })) })];
  rows.forEach((r, k) => {
    const last = k === rows.length - 1;
    if (r.group) {
      trs.push(new TableRow({ children: [cell(r.group, 0, { span: widths.length, italics: true, bottom: last,
        align: AlignmentType.LEFT })] }));
      return;
    }
    const cells = r.cells || r;
    trs.push(new TableRow({ children: cells.map((c, i) => cell(c, i, { bottom: last, bold: !!r.bold })) }));
  });
  const out = [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160 }, keepNext: true,
      children: [new TextRun({ text: `TABLE ${ROMAN[tabNo - 1]}`, font: FONT, size: 16 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, keepNext: true,
      children: [new TextRun({ text: title, font: FONT, size: 16, smallCaps: true })] }),
    new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
      alignment: AlignmentType.CENTER,
      borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
      rows: trs }),
  ];
  if (opt.note) {
    out.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { before: 40, after: 160 },
      children: runs(opt.note, { size: 14 }) }));
  } else {
    out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  }
  return out;
}

// ---------------------------------------------------------------- front matter (one column)
const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({
    text: "Design and Performance Analysis of a 4-Bit ALU Using Optimized Full-Custom Standard Cells and ALU-Specific Cells in 180 nm CMOS",
    font: FONT, size: 48 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({
    text: "Manshuk Garg, Aditya Kumar, Gourangi Tyagi, Kashish Goyal", font: FONT, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({
    text: "Department of Electronics and Communication Engineering", font: FONT, size: 20, italics: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 280 }, children: [new TextRun({
    text: "Thapar Institute of Engineering and Technology, Patiala, India", font: FONT, size: 20, italics: true })] }),
];

// ---------------------------------------------------------------- body (two columns)
const B = [];
const push = (...x) => x.flat().forEach((e) => B.push(e));

push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, children: [
  new TextRun({ text: "Abstract", font: FONT, size: 18, bold: true, italics: true }),
  new TextRun({ text: "—", font: FONT, size: 18, bold: true }),
  ...runs("This paper presents the design and post-layout evaluation of a 4-bit arithmetic logic unit (ALU) in 180 nm CMOS " +
    "built from a full-custom standard-cell library optimized for minimum power-delay product (PDP). Twenty-one candidate " +
    "circuits for nine functions were sized over 40 width and P/N-ratio combinations under a fan-out-of-four load; " +
    "transmission-gate circuits reduce the PDP of XOR2, MUX2 and the full adder by 53 %, 65 % and 60 % against static " +
    "CMOS. Two ALU-specific cells are proposed: a function block FB4 (20 transistors), a transmission-gate 4:1 multiplexer " +
    "in which the operand bits select one of four operation-code lines, and a carry-sum cell CS (24 transistors) that " +
    "forms the carry without a generate signal and selects the sum or the logic result. One ALU bit thus needs 44 " +
    "transistors. The cells were laid out by a cell generator, verified by DRC and LVS, characterized into a Liberty " +
    "library and used in an open-source Yosys and Qflow flow. Seven ALUs were placed, routed, extracted and simulated " +
    "with one transistor-level test bench. The proposed ALU occupies 2189 µm² and consumes 1453 fJ per operation and " +
    "0.69 nW of leakage: 37 % less area, 56 % less energy and 68 % less leakage than the best ALU built from the OSU " +
    "0.18 µm library, at a worst-case delay of 2.62 ns, 44 % above the fastest synthesized design.", { size: 18, bold: true }),
] }));
push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { before: 120, after: 120 }, children: [
  new TextRun({ text: "Index Terms", font: FONT, size: 18, bold: true, italics: true }),
  new TextRun({ text: "—", font: FONT, size: 18, bold: true }),
  new TextRun({ text: "Arithmetic logic unit, standard cells, transmission gate, power-delay product, low-power design, " +
    "physical design, open-source EDA.", font: FONT, size: 18, bold: true }),
] }));

// I. Introduction
push(H1("I", "Introduction"));
push(P("The arithmetic logic unit (ALU) lies on the datapath of every processor. In a cell-based design its area, delay " +
  "and energy are bounded by the standard-cell library: by the circuit style and size of each cell and by the number of " +
  "cells needed per bit. Logic styles and full-adder circuits have been compared extensively [4]–[8]. Transmission-gate " +
  "(TG) and hybrid circuits reduce the power-delay product (PDP) of XOR functions and full adders [5]–[7], and " +
  "minimum-PDP sizing in a realistic loading environment has been proposed at 0.18 µm [8]. These studies evaluate " +
  "single cells, and [4] shows that conclusions drawn from particular cells can change under realistic circuit " +
  "arrangements and cell-based design. Whether the gains of optimized cells survive in a complete datapath after " +
  "automatic placement, routing and parasitic extraction is rarely reported."));
push(P("A second way to reduce an ALU is to merge the logic of a bit into fewer cells. The OM-2 data path [1] uses " +
  "function blocks: multiplexers whose select inputs are the operand bits and whose data inputs are control lines shared " +
  "by all bits, so that one block computes any Boolean function of two variables. FPGA carry chains steer the carry with " +
  "a multiplexer controlled by the propagate signal [9]. This work implements both principles as restoring static CMOS " +
  "TG standard cells and evaluates them in a complete 4-bit ALU. The contributions are:"));
push(item("1)", "minimum-PDP sizing of 21 candidate circuits for nine functions under identical driver and fan-out-of-four " +
  "(FO4) conditions, and a 12-cell library (pl018) with generated layouts, design-rule check (DRC), layout-versus-schematic " +
  "(LVS) verification and Liberty characterization;"));
push(item("2)", "two ALU-specific cells, the function block FB4 and the carry-sum cell CS, which form an ALU bit with 44 " +
  "transistors;"));
push(item("3)", "a comparison of seven placed-and-routed 4-bit ALUs, built from the OSU 0.18 µm library and from pl018, " +
  "by one transistor-level test bench applied to the netlists extracted from the layouts."));
push(P("Section II describes the technology and the measurements, Section III the cell optimization, Section IV the " +
  "proposed cells, Section V the ALU, Section VI the physical implementation and Section VII the results."));

// II. Method
push(H1("II", "Technology and Evaluation Method"));
push(H2("A", "Technology and Tools"));
push(P("All circuits use the TSMC 0.18 µm process with the MOSIS BSIM3v3.1 parameters of run T14B at *V*_{DD} = 1.8 V " +
  "and 27 °C. The layouts follow the MOSIS SCMOS SCN6M_SUBM rules (λ = 0.1 µm, drawn channel length 0.2 µm) [14] of the " +
  "Qflow OSU018 kit. Circuits are simulated with Ngspice 46 [13]; layouts are drawn and extracted with Magic [10] and " +
  "compared with Netgen; the ALUs are synthesized with Yosys [12], placed and routed with Qflow [11] (GrayWolf, Qrouter) " +
  "and timed with OpenSTA. All flows run in the NIELIT ChipCraft virtual laboratory."));
push(H2("B", "Cell Measurement"));
push(P("Every cell input is driven through two X1 inverters, which gives it a realistic slope, and the output drives four " +
  "X1 inverters (FO4). The input sequence applies every change of one input in every state of the other inputs. The " +
  "delay *t*_{max} is the worst 50 %–50 % delay over all transitions, measured from the input of the last driver " +
  "inverter; *P*_{tot} is the average supply power including the drivers, and PDP = *P*_{tot} · *t*_{max}. A size is " +
  "accepted only if every transition gives the correct output level with full swing."));
push(H2("C", "ALU Measurement"));
push(P("All ALUs are measured with one test bench under the same driver and load conditions. It applies 229 " +
  "transitions: the 18 full-length carry ripples of ADD, SUB, INC and DEC, started at bit 0 or at the select inputs in " +
  "both directions, with their setup vectors, and for each of the eight operations one switch and 24 random operand " +
  "changes, one vector every 5 ns. Every output is checked at the end of each cycle. The delay of a transition is " +
  "measured from the input of the last driver inverter to the last 50 % crossing of any output, so it includes " +
  "glitches. The energy per operation *E*_{op} is the charge drawn from the ALU supply times *V*_{DD}, without the " +
  "drivers; the leakage *P*_{leak} is the mean over 16 static input states. The same bench is applied to the " +
  "transistor-level netlists and to the netlists extracted from the routed layouts. In addition, every netlist is " +
  "checked at switch level against all 2048 input combinations."));

// III. Cell optimization
push(H1("III", "Standard-Cell Optimization"));
push(P("Twenty-one candidate circuits were evaluated for nine functions: static CMOS for every function; gate-level " +
  "(NAND-based) XOR2, MUX2 and full adder (FA); TG XOR2 with and without output buffer and a complementary " +
  "pass-transistor (CPL) XOR2; TG MUX2 with and without output buffer; a TG inverting multiplexer (MUX2I) and one with " +
  "NMOS pass transistors; and two TG full adders [5], [6]. Each candidate was simulated at 40 sizes: eight width scales " +
  "*k* between 0.3 and 2 relative to its reference size and five PMOS-to-NMOS width ratios *r* between 1 and 3, 840 " +
  "Ngspice runs in all. Table I lists the minimum-PDP size of the best circuit of each function."));
push(table("Minimum-PDP Cells (FO4 Load, Drivers Included)",
  ["Function", "Circuit", "T", "*k* / *r*", "*t*_{max} (ps)", "PDP (fJ)", "ΔPDP"],
  [["INV", "static CMOS", "2", "0.8 / 2.5", "149.0", "9.65", "−3 %"],
    ["NAND2", "static CMOS", "4", "0.6 / 3", "184.9", "10.62", "−14 %"],
    ["NOR2", "static CMOS", "4", "0.6 / 2.5", "222.6", "13.36", "−3 %"],
    ["XOR2", "TG", "8", "0.6 / 3", "260.3", "20.11", "−53 %"],
    ["MUX2", "TG", "6", "0.4 / 3", "250.0", "16.28", "−65 %"],
    ["MUX2I", "TG + inverter", "8", "0.6 / 2.5", "282.1", "19.38", "−47 %"],
    ["FA", "TG adder", "24", "0.3 / 2.5", "589.6", "63.95", "−60 %"]],
  [760, 1240, 400, 760, 680, 600, 600],
  { note: "T: transistors. ΔPDP against the static CMOS circuit of the same function at *k* = 1, *r* = 2." }));
push(P("For the inverter and NOR2 the optimum lies close to the reference size (−3 %), and NAND2 gains 14 %. The TG " +
  "circuits reduce the PDP of XOR2, MUX2, MUX2I and FA by 47 %–65 %: they need fewer transistors in series and switch " +
  "less capacitance. The CPL XOR2 (43.59 fJ) and the NMOS-pass MUX2I (29.04 fJ) lose against the TG circuits, because an " +
  "NMOS transistor passes a degraded high level, which slows the next stage and causes static current in it. For the " +
  "library of the automated flow, XOR2 and MUX2 are used in their buffered versions (10 transistors, 21.94 and 22.98 fJ), " +
  "since a placed cell may drive any load and its timing model must not depend on the cell that drives it."));

// IV. ALU-specific cells
push(H1("IV", "Proposed ALU-Specific Cells"));
push(H2("A", "Function Block FB4"));
push(P("FB4 computes *P* = *C*[2*A* + *B*]: the operand bits *A* and *B* select one of four code lines *C*_{0}–*C*_{3} " +
  "(Fig. 1). The code lines are driven by the operation decoder and shared by all bits, so *P* can be any Boolean " +
  "function of *A* and *B*, chosen per operation. The cell is a 4:1 multiplexer of two TG levels, controlled by *B* and " +
  "then by *A*, with two input inverters for the complements and two output inverters that restore the level and isolate " +
  "the output: 20 transistors in all. At minimum PDP (*k* = 0.4, *r* = 2.5) its worst delay is 450.2 ps and its PDP " +
  "18.95 fJ."));
push(figure(path.join(PRES, "schematic_fb4.png"), "Transistor schematic of the function block FB4 (20 transistors; " +
  "device sizes of the layout)."));
push(H2("B", "Carry-Sum Cell CS"));
push(P("CS computes the carry and the result of a bit (Fig. 2):", { keepNext: true }));
push(equation("*C*_{O} = *C*_{I} if *P* = 1, else *A*,", 1));
push(equation("*Y* = *P* if *K* = 1, else *P* ⊕ *C*_{I}.", 2));
push(P("With *P* = *A* ⊕ *B*_{x} the propagate of the two operand bits, *P* = 0 means *A* = *B*_{x}: either both bits " +
  "are 1 and a carry is generated, or both are 0 and it is killed. In both cases the carry out equals *A*, so no " +
  "generate signal is needed and the carry logic reduces to one 2:1 TG multiplexer per bit. *K* selects the logic result " +
  "*P* instead of the sum. The cell has 24 transistors, and the carry passes one TG and two inverters per bit. At minimum " +
  "PDP (*k* = 0.8, *r* = 1.5) the worst delay is 458.6 ps and the PDP 33.64 fJ."));
push(figure(path.join(PRES, "schematic_cs.png"), "Transistor schematic of the carry-sum cell CS (24 transistors)."));
push(H2("C", "Comparison With Composed Cells"));
push(P("Table II compares the two cells with the same functions built from other cells, measured with the same bench " +
  "(384 transitions for FB4 and 64 for CS). Against static CMOS the PDP falls by 73 % and 64 %. Against the optimized " +
  "library cells, FB4 lowers the PDP by 12 % with four transistors fewer at a 4 % longer delay, and CS lowers the PDP by " +
  "18 % and the delay by 10 %. All 40 sizes of both cells pass every functional check."));
push(table("ALU-Specific Cells Against Composed Implementations", ["Implementation", "T", "*t*_{max} (ps)", "PDP (fJ)"],
  [{ group: "Function of FB4: *P* = *C*[2*A* + *B*]" },
    ["3 × MUX2, static CMOS", "36", "688.7", "70.78"],
    ["3 × MUX2I, pl018", "24", "433.6", "21.58"],
    { bold: true, cells: ["FB4 (proposed)", "20", "450.2", "18.95"] },
    { group: "Function of CS: carry and result" },
    ["MUX2 + XOR2 + MUX2, static CMOS", "36", "614.6", "93.84"],
    ["MUX2 + XOR2 + MUX2, pl018", "30", "510.0", "41.08"],
    { bold: true, cells: ["CS (proposed)", "24", "458.6", "33.64"] }],
  [2640, 600, 900, 900]));

// V. ALU organization
push(H1("V", "ALU Organization"));
push(P("Each bit of the ALU consists of one FB4 and one CS (Fig. 3). A decoder of nine library cells derives from the " +
  "operation code *s*_{2}*s*_{1}*s*_{0} the code lines *C*_{0}–*C*_{3}, shared by all bits, the carry into bit 0, " +
  "*c*_{0} = *s*_{1} ⊕ *s*_{0}, and *K* = *s*_{2} (Table III). ADD uses *P* = *A* ⊕ *B*. SUB uses *P* = *A* XNOR *B* " +
  "= *A* ⊕ ¬*B* with *c*_{0} = 1, so that the bit computes *A* + ¬*B* + 1 without an XOR gate on the second operand. " +
  "INC uses *P* = *A* with *c*_{0} = 1, and DEC uses *P* = ¬*A* with *c*_{0} = 0, which adds 1111. For the logic " +
  "operations *K* = 1 and FB4 forms the result directly. Ten further cells form the flags: *C* = *c*_{4} · ¬*s*_{2}, " +
  "*V* = (*c*_{3} ⊕ *c*_{4}) · ¬*s*_{2}, *Z* = 1 when all result bits are 0, and *N* = *y*_{3}. At transistor level the " +
  "ALU has 272 transistors, including one buffer on *s*_{2}."));
push(figure(path.join(FIG, "fig_alu_org.png"), "Organization of the proposed 4-bit ALU: one FB4 and one CS per bit, " +
  "the code lines *C*_{0}–*C*_{3} and *K* shared by all bits, the decoder and the flag logic."));
push(table("Operation Codes", ["Op.", "*s*_{2}*s*_{1}*s*_{0}", "*P*", "*C*_{3}..*C*_{0}", "*c*_{0}", "*K*"],
  [["ADD", "000", "*A* ⊕ *B*", "0110", "0", "0"], ["SUB", "001", "*A* XNOR *B*", "1001", "1", "0"],
    ["INC", "010", "*A*", "1100", "1", "0"], ["DEC", "011", "¬*A*", "0011", "0", "0"],
    ["AND", "100", "*A* · *B*", "1000", "–", "1"], ["OR", "101", "*A* + *B*", "1110", "–", "1"],
    ["XOR", "110", "*A* ⊕ *B*", "0110", "–", "1"], ["NOT", "111", "¬*A*", "0011", "–", "1"]],
  [720, 860, 1340, 1000, 560, 560]));

// VI. Physical implementation
push(H1("VI", "Physical Implementation"));
push(H2("A", "Cell Library pl018"));
push(P("The cell layouts are produced by a generator from the transistor netlist and a column order of the devices " +
  "along shared diffusion. The generator places the devices on an 8.0 µm row (0.8 µm sites, shared 0.6 µm power rails " +
  "with substrate and well taps, n-well over the full cell width), folds wide transistors (NMOS up to 2.4 µm and PMOS up " +
  "to 3.2 µm per finger) and routes every net on poly, metal1 and metal2 with a maze router. Every pin pad lies on a " +
  "crossing of the routing tracks (metal2 every 0.8 µm, metal1 every 1.0 µm), so that the router reaches it in any " +
  "placement orientation (Fig. 4). The OSU018 cells use 10.0 µm rows."));
push(figure(path.join(FIGS, "layout_pl_fb4.png"), "Generated layout of the cell pl_fb4 (14.4 × 8.0 µm)."));
push(P("The library pl018 contains 12 cells (INV, BUF, NAND2, NOR2, AND2, OR2, XOR2, MUX2, MUX2I, FA, FB4, CS) and a " +
  "filler; all pass Magic DRC and Netgen LVS. Each cell is extracted and characterized with Ngspice at five loads " +
  "(2–100 fF) and five input slopes (30–1200 ps) into the non-linear delay tables of a Liberty file. At 16 fF and 80 ps " +
  "the worst-arc delays range from 84 ps (INV) to 633 ps (FA), with 378/456 ps (rise/fall) for FB4 and 395/400 ps for " +
  "CS. The LEF view takes the complete metal of each pin net as pin geometry and the internal nets as obstructions."));
push(H2("B", "Automated Implementation"));
push(P("Three descriptions of the ALU were implemented with both libraries: behavioural RTL (beh), bit-sliced RTL " +
  "(slice), and a hand-mapped netlist of full adders and inverting multiplexers (map). Design D3 uses the OSU018 cells " +
  "and design D4 the pl018 cells; the proposed ALU P is the hand-mapped FB4/CS netlist of Section V (27 cells) with " +
  "pl018. Yosys maps each description onto the library; Qflow buffers high-fanout nets, places the cells and routes " +
  "them; Netgen compares the routed layout with the netlist; Magic checks DRC with the real cell layouts and extracts a " +
  "flat netlist with all transistors and parasitic capacitances, which is simulated with the ALU bench. Wire " +
  "resistance is not extracted. To make the generated cells routable, keep-out areas next to the signal-pin metal are " +
  "passed to the router as obstructions. All seven ALUs route completely, match in LVS, have no DRC errors and give " +
  "correct results on all 229 transitions after extraction. Fig. 5 shows the routed proposed ALU (57.6 × 38.0 µm, 55 " +
  "placed cells)."));
push(figure(path.join(FIG, "fig_chip.png"), "Routed proposed ALU (57.6 × 38.0 µm) with the pl018 cell layouts, " +
  "viewed in KLayout."));

// VII. Results
push(H1("VII", "Results and Discussion"));
push(H2("A", "Transistor Level"));
push(P("Table IV compares the ALU built from five cell sets at transistor level, before layout. With the minimum-PDP " +
  "cells (D2) the energy per operation is 69 % lower than with static CMOS cells (D1). The FB4/CS ALU (P) needs 272 " +
  "transistors, 2076.2 ps and 870.6 fJ per operation: against D1, 53 % fewer transistors, 30 % less delay, 75 % less " +
  "energy, 76 % less leakage and an 83 % lower energy-delay product (EDP); against D2, 32 % fewer transistors, 9 % less " +
  "delay and 21 % less energy."));
push(table("4-Bit ALUs at Transistor Level (Before Layout)",
  ["Cell set", "T", "*t*_{max} (ps)", "*E*_{op} (fJ)", "*P*_{leak} (nW)", "EDP (fJ·ns)"],
  [["Gate-level cells", "842", "2925.4", "2039.6", "1.41", "5966.6"],
    ["D1: static CMOS", "578", "2979.3", "3509.8", "2.02", "10456.7"],
    ["D2: minimum-PDP", "402", "2270.8", "1102.1", "0.81", "2502.6"],
    ["pl018, mapped slice", "458", "2310.4", "1312.8", "0.93", "3033.1"],
    { bold: true, cells: ["P: FB4 + CS", "272", "2076.2", "870.6", "0.47", "1807.5"] }],
  [1500, 520, 760, 760, 740, 760]));
push(H2("B", "After Layout"));
push(P("Table V and Fig. 6 summarize the seven routed ALUs. With the same description, the pl018 library reduces the " +
  "energy by 36 %–45 %, the leakage by 36 %–52 %, the EDP by 32 %–49 % and the die area by 8 %–23 % against OSU018, " +
  "at a delay change between −7 % and +5 %. The proposed ALU has the smallest die (2189 µm²), the fewest transistors " +
  "(316) and the lowest energy (1453.0 fJ), leakage (0.69 nW) and EDP (3800.1 fJ·ns) of all seven designs. Against the " +
  "best OSU018 design for each quantity, this is 37 % less area (D3 map), 40 % fewer transistors and 56 % less energy " +
  "(D3 slice), 68 % less leakage (D3 map) and a 47 % lower EDP (D3 slice). The logic operations cost only 967–1188 fJ, " +
  "against 1460–4934 fJ in the other designs, since FB4 forms their result directly."));
push(table("Routed 4-Bit ALUs (Extracted Netlists)",
  ["Design", "Area (µm²)", "T", "*C* (fF)", "*t*_{max} (ps)", "*E*_{op} (fJ)", "*P*_{leak} (nW)", "EDP"],
  [["D3 beh", "5466", "793", "875", "1812.0", "4898.7", "3.10", "8876.4"],
    ["D3 slice", "3864", "525", "563", "2144.4", "3333.0", "2.21", "7147.1"],
    ["D3 map", "3496", "534", "455", "3476.1", "3807.1", "2.18", "13233.7"],
    ["D4 beh", "4536", "716", "655", "1874.0", "2798.5", "1.98", "5244.4"],
    ["D4 slice", "2979", "454", "429", "2257.1", "2140.4", "1.22", "4831.1"],
    ["D4 map", "3202", "484", "528", "3220.6", "2077.3", "1.04", "6690.1"],
    { bold: true, cells: ["P", "2189", "316", "324", "2615.4", "1453.0", "0.69", "3800.1"] }],
  [720, 640, 460, 520, 680, 680, 620, 720],
  { note: "D3: OSU018 cells; D4: pl018 cells; P: proposed FB4/CS ALU with pl018. *C*: extracted parasitic capacitance. EDP in fJ·ns." }));
push(figure(path.join(FIG, "fig_after_layout.png"), "Energy per operation and worst-case delay of the seven routed " +
  "ALUs (extracted netlists; light grey: OSU018 cells, dark grey: pl018 cells, black: proposed)."));
push(P("The proposed ALU is not the fastest. Its worst transition, a change from ADD to SUB, propagates from the select " +
  "inputs through the decoder and the buffered code lines into every FB4 and then along the 4-bit carry chain to the " +
  "overflow flag: 2615.4 ps. The behavioural description restructured by Yosys and ABC with the OSU018 cells reaches " +
  "1812.0 ps (D3 beh), 31 % less, with 147 placed cells and 793 transistors; P is 25 % faster than the hand-mapped D3 " +
  "map. Layout increases the delay of P by 22.6 % and its energy by 16.6 % over its netlist before layout, against 4 %–9 % " +
  "in delay for D3. The pl018 cells have smaller input and internal capacitances, so the wiring is a larger share of " +
  "each load, and the library has a single drive strength, which leads Qflow to place 55 cells for the 27-cell netlist."));
push(H2("C", "Limitations"));
push(P("The results hold for the typical corner at 1.8 V and 27 °C. Supply, temperature and Monte Carlo analysis, " +
  "wire-resistance extraction and drive strengths beyond X1 remain to be added. For wider ALUs the linear carry path of " +
  "the bit slice will need lookahead or skip logic."));

// VIII. Conclusion
push(H1("VIII", "Conclusion"));
push(P("A 4-bit ALU was designed in 180 nm CMOS from a full-custom library of minimum-PDP cells and two ALU-specific " +
  "cells. TG circuits at their minimum-PDP size reduce the PDP of XOR2, MUX2 and the full adder by 53 %–65 %. The " +
  "function block FB4 and the carry-sum cell CS form an ALU bit with 44 transistors and lower the PDP of their functions " +
  "by 12 % and 18 % against composed library cells. Implemented with Yosys and Qflow and evaluated on extracted layouts, " +
  "the proposed ALU needs 37 % less area, 56 % less energy and 68 % less leakage than the best ALU from the OSU 0.18 µm " +
  "library, at a worst-case delay 44 % above the fastest synthesized design. Future work will shorten the carry path " +
  "with alternating carry polarity and stronger drivers, add corner and Monte Carlo analysis, and extend the design to " +
  "8 and 16 bits."));

// Acknowledgment
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true,
  children: [new TextRun({ text: "Acknowledgment", font: FONT, smallCaps: true })] }));
push(P("The authors thank NIELIT for access to the ChipCraft virtual laboratory. In accordance with the IEEE policy on " +
  "AI-generated content, the authors disclose that Claude (Anthropic), an AI system, was used to write the scripts that " +
  "generate, lay out, characterize and simulate the cells and ALUs, and to draft all sections, figures and tables of " +
  "this paper. All flows were run by the authors in the ChipCraft laboratory, and the authors are responsible for the " +
  "content."));

// References
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true,
  children: [new TextRun({ text: "References", font: FONT, smallCaps: true })] }));
const REFS = [
  "C. Mead and L. Conway, *Introduction to VLSI Systems*. Reading, MA, USA: Addison-Wesley, 1980.",
  "N. H. E. Weste and D. M. Harris, *CMOS VLSI Design: A Circuits and Systems Perspective*, 4th ed. Boston, MA, USA: Addison-Wesley, 2011.",
  "J. M. Rabaey, A. Chandrakasan, and B. Nikolić, *Digital Integrated Circuits: A Design Perspective*, 2nd ed. Upper Saddle River, NJ, USA: Prentice Hall, 2003.",
  "R. Zimmermann and W. Fichtner, “Low-power logic styles: CMOS versus pass-transistor logic,” *IEEE J. Solid-State Circuits*, vol. 32, no. 7, pp. 1079–1090, Jul. 1997.",
  "N. Zhuang and H. Wu, “A new design of the CMOS full adder,” *IEEE J. Solid-State Circuits*, vol. 27, no. 5, pp. 840–844, May 1992.",
  "A. M. Shams, T. K. Darwish, and M. A. Bayoumi, “Performance analysis of low-power 1-bit CMOS full adder cells,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 10, no. 1, pp. 20–29, Feb. 2002.",
  "S. Goel, A. Kumar, and M. A. Bayoumi, “Design of robust, energy-efficient full adders for deep-submicrometer design using hybrid-CMOS logic style,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 14, no. 12, pp. 1309–1321, Dec. 2006.",
  "C.-H. Chang, J. Gu, and M. Zhang, “A review of 0.18-µm full adder performances for tree structured arithmetic circuits,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 13, no. 6, pp. 686–695, Jun. 2005.",
  "Xilinx, “7 Series FPGAs configurable logic block user guide,” UG474.",
  "J. K. Ousterhout, G. T. Hamachi, R. N. Mayo, W. S. Scott, and G. S. Taylor, “Magic: A VLSI layout system,” in *Proc. 21st Design Automation Conf.*, 1984, pp. 152–159.",
  "R. T. Edwards, “Qflow: An open-source digital synthesis flow,” Open Circuit Design. [Online]. Available: http://opencircuitdesign.com/qflow/",
  "C. Wolf, “Yosys Open SYnthesis Suite.” [Online]. Available: https://yosyshq.net/yosys/",
  "“Ngspice: Open source mixed-signal circuit simulator.” [Online]. Available: https://ngspice.sourceforge.io/",
  "MOSIS, “MOSIS scalable CMOS (SCMOS) design rules,” rev. 8.",
];
REFS.forEach((r, i) => push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { left: 400, hanging: 400 },
  tabStops: [{ type: TabStopType.LEFT, position: 400 }], spacing: { after: 20 },
  children: [new TextRun({ text: `[${i + 1}]`, font: FONT, size: 16 }), new TextRun({ children: [new Tab()], size: 16 }),
    ...runs(r, { size: 16 })] })));

// ---------------------------------------------------------------- document
const doc = new Document({
  creator: "Manshuk Garg",
  title: "Design and Performance Analysis of a 4-Bit ALU Using Optimized Full-Custom Standard Cells and ALU-Specific Cells in 180 nm CMOS",
  styles: {
    default: { document: { run: { font: FONT, size: 20 }, paragraph: { spacing: { line: 240 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 20, smallCaps: true },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 20, italics: true },
        paragraph: { spacing: { before: 100, after: 60 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  sections: [
    { properties: { page: PAGE }, children: front },
    { properties: { type: SectionType.CONTINUOUS, page: PAGE, column: { space: 360, count: 2, equalWidth: true } }, children: B },
  ],
});
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("wrote " + path.relative(ROOT, OUT));
});
