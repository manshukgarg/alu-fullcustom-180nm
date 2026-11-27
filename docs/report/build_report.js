// Project report (Word, A4) built with docx from report_content.js.
//
//   bash docs/report/build.sh        two passes: the second fills in the page numbers of the
//                                    contents and lists, found in the PDF of the first
//
// Text markup in report_content.js: **bold**, *italic*, _{subscript}, ^{superscript},
// {c:key,key} citations (numbered in order of first use), {f:label} figure and {t:label} table
// references, {e:label} equation references.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, SectionType, TabStopType, LeaderType, Footer, PageNumber, NumberFormat, LevelFormat, ShadingType,
  VerticalAlign, HeightRule, LineRuleType, PageBreak,
} = require("docx");
const C = require("./report_content.js");

const HERE = __dirname;
const ROOT = path.resolve(HERE, "..", "..");
const OUT = path.join(HERE, "ALU_project_report.docx");
const PAGES = path.join(HERE, "pages.json");
const pages = fs.existsSync(PAGES) ? JSON.parse(fs.readFileSync(PAGES, "utf8")) : {};

const FONT = "Times New Roman";
const MONO = "Courier New";
const TW = 8306;                     // text width, DXA (A4 minus 1.5 in left and 1 in right margin)
const PAGE = { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 2160, right: 1440, footer: 708 } };
const BODY = { line: 360, lineRule: LineRuleType.AUTO };
const GREY = "808080";

// ------------------------------------------------------------------ numbering pass
const cite = [];                     // citation keys in order of first use
const fig = {}, tab = {}, eqn = {};  // label -> number string
const toc = [];                      // {id, level, text}
const lof = [], lot = [];
(function number() {
  let chap = "", nf = 0, nt = 0, ne = 0;
  const scan = (s) => {
    if (typeof s !== "string") return;
    for (const m of s.matchAll(/\{c:([^}]+)\}/g)) {
      for (const k of m[1].split(",").map((x) => x.trim())) {
        if (!C.refs[k]) throw new Error("unknown reference " + k);
        if (!cite.includes(k)) cite.push(k);
      }
    }
  };
  for (const b of C.body) {
    if (b.k === "chapter" || b.k === "appendix") {
      chap = b.n; nf = 0; nt = 0; ne = 0;
      toc.push({ id: "ch:" + b.n, level: 1, text: (b.k === "chapter" ? b.n + "  " : "Appendix " + b.n + "  ") + b.title });
    }
    if (b.k === "refs") toc.push({ id: "refs", level: 1, text: "References" });
    if (b.k === "h2") toc.push({ id: "h2:" + b.n, level: 2, text: b.n + "  " + b.title });
    if (b.k === "fig" || b.k === "hand") { nf += 1; fig[b.label] = chap + "." + nf; lof.push({ id: "fig:" + fig[b.label], text: `Fig. ${fig[b.label]}  ${plain(b.caption)}` }); }
    if (b.k === "table") { nt += 1; tab[b.label] = chap + "." + nt; lot.push({ id: "tab:" + tab[b.label], text: `Table ${tab[b.label]}  ${plain(b.caption)}` }); }
    if (b.k === "eq" && b.label !== undefined) { ne += 1; eqn[b.label] = chap + "." + ne; }
    for (const key of ["t", "caption", "note", "title"]) scan(b[key]);
    for (const it of b.items || []) scan(it);
    for (const row of b.rows || []) {
      if (row.group) { scan(row.group); continue; }
      for (const c of (row.cells || row)) scan(c);
    }
  }
})();
function plain(s) { return resolve(s).replace(/\*\*|\*/g, "").replace(/[_^]\{([^}]*)\}/g, "$1"); }
function resolve(s) {
  return String(s)
    .replace(/\{c:([^}]+)\}/g, (_, ks) => citeText(ks.split(",").map((x) => cite.indexOf(x.trim()) + 1)))
    .replace(/\{f:([^}]+)\}/g, (_, l) => { if (!fig[l]) throw new Error("figure " + l); return "Fig. " + fig[l]; })
    .replace(/\{t:([^}]+)\}/g, (_, l) => { if (!tab[l]) throw new Error("table " + l); return "Table " + tab[l]; })
    .replace(/\{e:([^}]+)\}/g, (_, l) => { if (!eqn[l]) throw new Error("equation " + l); return "(" + eqn[l] + ")"; });
}
function citeText(ns) {
  ns = [...new Set(ns)].sort((a, b) => a - b);
  const parts = [];
  for (let i = 0; i < ns.length; i++) {
    let j = i;
    while (j + 1 < ns.length && ns[j + 1] === ns[j] + 1) j++;
    if (j - i >= 2) parts.push(`[${ns[i]}]–[${ns[j]}]`);
    else for (let k = i; k <= j; k++) parts.push(`[${ns[k]}]`);
    i = j;
  }
  return parts.join(", ");
}

// ------------------------------------------------------------------ text runs
function runs(str, base = {}) {
  str = resolve(str);
  const out = [];
  let bold = !!base.bold, ital = !!base.italics, buf = "";
  const mk = (text, extra = {}) => new TextRun(Object.assign({ text, font: base.font || FONT, size: base.size, color: base.color,
    bold, italics: ital }, extra));
  const flush = () => { if (buf) { out.push(mk(buf)); buf = ""; } };
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (ch === "*" && str[i + 1] === "*") { flush(); bold = !bold; i++; continue; }
    if (ch === "*") { flush(); ital = !ital; continue; }
    if ((ch === "_" || ch === "^") && str[i + 1] === "{") {
      flush();
      const j = str.indexOf("}", i);
      out.push(mk(str.slice(i + 2, j), ch === "_" ? { subScript: true } : { superScript: true }));
      i = j; continue;
    }
    if (ch === "\n") { flush(); out.push(new TextRun({ break: 1 })); continue; }
    buf += ch;
  }
  flush();
  return out;
}
const P = (str, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED, spacing: Object.assign({ before: 0, after: 120 }, BODY, o.spacing || {}),
  indent: o.indent, keepNext: o.keepNext, keepLines: o.keepLines, pageBreakBefore: o.pageBreakBefore,
  children: runs(str, o.run || {}),
});

// ------------------------------------------------------------------ blocks
function pngSize(p) { const b = fs.readFileSync(p); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function caption(prefix, num, text) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 240, line: 276, lineRule: LineRuleType.AUTO },
    children: [new TextRun({ text: `${prefix} ${num}: `, font: FONT, size: 22, bold: true }), ...runs(text, { size: 22 })] });
}
function figure(b) {
  const file = path.join(ROOT, b.file);
  const sz = pngSize(file);
  const wIn = Math.min(b.width || 5.6, TW / 1440);
  const w = Math.round(wIn * 96), h = Math.round(wIn * 96 * sz.h / sz.w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 0 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: w, height: h },
        altText: { title: "Fig. " + fig[b.label], description: plain(b.caption), name: b.label } })] }),
    caption("Fig.", fig[b.label], b.caption),
  ];
}
function handFig(b) {
  const dash = { style: BorderStyle.DASHED, size: 8, color: "7F7F7F" };
  const box = new Table({
    width: { size: b.width || TW, type: WidthType.DXA }, columnWidths: [b.width || TW], alignment: AlignmentType.CENTER,
    rows: [new TableRow({ height: { value: Math.round(b.height * 1440), rule: HeightRule.ATLEAST }, cantSplit: true, children: [new TableCell({
      width: { size: b.width || TW, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
      borders: { top: dash, bottom: dash, left: dash, right: dash },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Paste the photograph of the hand-drawn circuit here", font: FONT, size: 24, bold: true, color: "7F7F7F" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new TextRun({ text: `Reference sheet ${b.ref}: ${b.sheet}`, font: FONT, size: 22, italics: true, color: "7F7F7F" })] }),
      ] })] })],
  });
  return [new Paragraph({ spacing: { before: 120, after: 0 }, keepNext: true, children: [] }), box, caption("Fig.", fig[b.label], b.caption)];
}
const thin = { style: BorderStyle.SINGLE, size: 4, color: GREY };
function table(b) {
  const widths = b.widths;
  const total = widths.reduce((a, x) => a + x, 0);
  if (total > TW) throw new Error(`table ${b.label} too wide: ${total}`);
  const size = b.size || 20;
  const align = b.align || b.header.map((_, i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER));
  const cell = (text, i, o = {}) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, columnSpan: o.span, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    shading: o.head ? { type: ShadingType.CLEAR, fill: "D9D9D9", color: "auto" } : (o.group ? { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" } : undefined),
    borders: { top: thin, bottom: thin, left: thin, right: thin },
    children: String(text).split("|").map((line) => new Paragraph({ alignment: o.align || align[i], spacing: { line: 240, lineRule: LineRuleType.AUTO }, keepNext: !!o.keep,
      children: runs(line, { size, bold: o.head || o.bold, italics: o.italics }) })),
  });
  const keepAll = b.rows.length <= 14, last = b.rows[b.rows.length - 1];
  const rows = [new TableRow({ tableHeader: true, cantSplit: true, children: b.header.map((h, i) => cell(h, i, { head: true, align: AlignmentType.CENTER, keep: true })) })];
  for (const r of b.rows) {
    if (r.group) { rows.push(new TableRow({ cantSplit: true, children: [cell(r.group, 0, { span: widths.length, group: true, italics: true, align: AlignmentType.LEFT, keep: keepAll })] })); continue; }
    const cells = r.cells || r;
    rows.push(new TableRow({ cantSplit: true, children: cells.map((c, i) => cell(c, i, { bold: !!r.bold, keep: keepAll && r !== last })) }));
  }
  const out = [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100, line: 276, lineRule: LineRuleType.AUTO }, keepNext: true,
      children: [new TextRun({ text: `Table ${tab[b.label]}: `, font: FONT, size: 22, bold: true }), ...runs(b.caption, { size: 22 })] }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER, rows }),
  ];
  out.push(b.note
    ? new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 60, after: 240, line: 240, lineRule: LineRuleType.AUTO }, children: runs(b.note, { size: 18 }) })
    : new Paragraph({ spacing: { before: 0, after: 160 }, children: [] }));
  return out;
}
function equation(b) {
  const num = b.label !== undefined ? `(${eqn[b.label]})` : "";
  return new Paragraph({ spacing: { before: 60, after: 120, line: 300, lineRule: LineRuleType.AUTO }, keepNext: b.keepNext,
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(TW / 2) }, { type: TabStopType.RIGHT, position: TW }],
    children: [new TextRun({ children: ["\t"], font: FONT }), ...runs(b.t), new TextRun({ children: ["\t" + num], font: FONT })] });
}
function code(b) {
  const lines = b.lines || fs.readFileSync(path.join(ROOT, b.file), "utf8").split("\n");
  const box = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 4 };
  return lines.map((l, i) => new Paragraph({
    spacing: { before: 0, after: 0, line: 220, lineRule: LineRuleType.AUTO }, keepLines: true, keepNext: i < lines.length - 1,
    shading: { type: ShadingType.CLEAR, fill: "F5F5F5", color: "auto" },
    border: { left: box, right: box, top: i === 0 ? box : undefined, bottom: i === lines.length - 1 ? box : undefined },
    children: [new TextRun({ text: l.length ? l : " ", font: MONO, size: b.size || 15 })],
  })).concat([new Paragraph({ spacing: { after: 160 }, children: [] })]);
}
function list(b) {
  const instance = b.numbered ? (list.n = (list.n || 0) + 1) : undefined;
  return b.items.map((it) => new Paragraph({
    numbering: { reference: b.numbered ? "numbers" : "bullets", level: 0, instance },
    alignment: AlignmentType.JUSTIFIED, spacing: Object.assign({ before: 0, after: 80 }, BODY), children: runs(it) }));
}
function tocLine(text, page, level, id) {
  return new Paragraph({
    spacing: { before: level === 1 ? 120 : 0, after: 40, line: 276, lineRule: LineRuleType.AUTO },
    indent: { left: level === 2 ? 480 : 0, hanging: level === 2 ? 0 : 0 },
    tabStops: [{ type: TabStopType.RIGHT, position: TW, leader: LeaderType.DOT }],
    children: [...runs(text, { bold: level === 1 && !/^Fig|^Table/.test(text) }), new TextRun({ children: ["\t" + (pages[id] || "00")], font: FONT })],
  });
}
const heading = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.CENTER, pageBreakBefore: o.pageBreakBefore,
  spacing: { before: o.before || 0, after: o.after || 360, line: 276, lineRule: LineRuleType.AUTO }, keepNext: true,
  children: runs(text, { bold: true, size: o.size || 32 }),
});

// ------------------------------------------------------------------ front matter
const front1 = C.titlePage(runs);       // title page: own section, no page number
const front2 = [];
for (const s of C.frontPages) {
  front2.push(heading(s.title, { pageBreakBefore: front2.length > 0, size: 28 }));
  for (const b of s.blocks) front2.push(...render(b));
}
front2.push(heading("CONTENTS", { pageBreakBefore: true, size: 28 }));
for (const s of C.frontPages.filter((x) => x.toc)) front2.push(tocLine(s.title.replace(/^\w/, (c) => c) , null, 1, "front:" + s.id));
for (const id of ["lof", "lot", "abbr"]) front2.push(tocLine({ lof: "LIST OF FIGURES", lot: "LIST OF TABLES", abbr: "LIST OF ABBREVIATIONS" }[id], null, 1, "front:" + id));
for (const e of toc) front2.push(tocLine(e.text, null, e.level, e.id));
front2.push(heading("LIST OF FIGURES", { pageBreakBefore: true, size: 28 }));
for (const e of lof) front2.push(tocLine(e.text, null, 2.5, e.id));
front2.push(heading("LIST OF TABLES", { pageBreakBefore: true, size: 28 }));
for (const e of lot) front2.push(tocLine(e.text, null, 2.5, e.id));
front2.push(heading("LIST OF ABBREVIATIONS", { pageBreakBefore: true, size: 28 }));
front2.push(...table(Object.assign({ label: "__abbr" }, C.abbreviations)).slice(1));

// ------------------------------------------------------------------ body
function render(b) {
  switch (b.k) {
    case "p": return [P(b.t, b)];
    case "chapter": return [new Paragraph({ alignment: AlignmentType.CENTER, pageBreakBefore: true, spacing: { before: 0, after: 120 }, keepNext: true,
      children: [new TextRun({ text: "CHAPTER " + b.n, font: FONT, size: 28, bold: true })] }), heading(b.title.toUpperCase(), { size: 32, after: 480 })];
    case "appendix": return [new Paragraph({ alignment: AlignmentType.CENTER, pageBreakBefore: true, spacing: { before: 0, after: 120 }, keepNext: true,
      children: [new TextRun({ text: "APPENDIX " + b.n, font: FONT, size: 28, bold: true })] }), heading(b.title.toUpperCase(), { size: 32, after: 480 })];
    case "refs": {
      const out = [heading("REFERENCES", { pageBreakBefore: true, size: 32, after: 360 })];
      cite.forEach((k, i) => out.push(new Paragraph({
        alignment: AlignmentType.LEFT, spacing: { before: 0, after: 100, line: 276, lineRule: LineRuleType.AUTO },
        indent: { left: 600, hanging: 600 }, tabStops: [{ type: TabStopType.LEFT, position: 600 }],
        children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 22 }), ...runs(C.refs[k], { size: 22 })] })));
      return out;
    }
    case "h2": return [new Paragraph({ spacing: { before: 280, after: 120, line: 276, lineRule: LineRuleType.AUTO }, keepNext: true,
      children: runs(b.n + "  " + b.title, { bold: true, size: 28 }) })];
    case "h3": return [new Paragraph({ spacing: { before: 200, after: 80, line: 276, lineRule: LineRuleType.AUTO }, keepNext: true,
      children: runs(b.title, { bold: true, italics: true, size: 24 }) })];
    case "eq": return [equation(b)];
    case "fig": return figure(b);
    case "hand": return handFig(b);
    case "table": return table(b);
    case "code": return [...(b.title ? [P(b.title, { keepNext: true, run: { bold: true } })] : []), ...code(b)];
    case "list": return list(b);
    case "pagebreak": return [new Paragraph({ children: [new PageBreak()] })];
    default: throw new Error("block " + b.k);
  }
}
const body = [];
for (const b of C.body) body.push(...render(b));

// ------------------------------------------------------------------ document
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] });
const doc = new Document({
  creator: "Manshuk Garg", title: C.title,
  styles: { default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 360, lineRule: LineRuleType.AUTO } } } } },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 480, hanging: 300 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 480, hanging: 360 } } } }] },
  ] },
  sections: [
    { properties: { page: PAGE }, children: front1 },
    { properties: { type: SectionType.NEXT_PAGE, page: Object.assign({}, PAGE, { pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } }) },
      footers: { default: footer }, children: front2 },
    { properties: { type: SectionType.NEXT_PAGE, page: Object.assign({}, PAGE, { pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } }) },
      footers: { default: footer }, children: body },
  ],
});
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  // what the page finder looks for: id -> text at the start of a line in the PDF
  const find = {};
  for (const s of C.frontPages.filter((x) => x.toc)) find["front:" + s.id] = s.title;
  Object.assign(find, { "front:lof": "LIST OF FIGURES", "front:lot": "LIST OF TABLES", "front:abbr": "LIST OF ABBREVIATIONS", refs: "REFERENCES" });
  for (const b of C.body) {
    if (b.k === "chapter") find["ch:" + b.n] = "CHAPTER " + b.n;
    if (b.k === "appendix") find["ch:" + b.n] = "APPENDIX " + b.n;
    if (b.k === "h2") find["h2:" + b.n] = b.n + "  " + plain(b.title);
  }
  for (const [l, n] of Object.entries(fig)) find["fig:" + n] = `Fig. ${n}:`;
  for (const [l, n] of Object.entries(tab)) find["tab:" + n] = `Table ${n}:`;
  fs.writeFileSync(path.join(HERE, "find.json"), JSON.stringify(find, null, 1));
  console.log(`wrote ${path.relative(ROOT, OUT)}: ${cite.length} references, ${Object.keys(fig).length} figures, ${Object.keys(tab).length} tables`);
});
