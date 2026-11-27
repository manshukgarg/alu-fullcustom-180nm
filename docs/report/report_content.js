// Content of the project report. Every number is a result in results/lab/ (Steps 2, 5, 6) or
// results/ngspice46_2026-11-16/ (Steps 3b, 3c; the lab runs give the same values).
const { Paragraph, TextRun, AlignmentType, LineRuleType } = require("docx");

const title = "Design and Performance Analysis of a Full-Custom ALU Using Optimized Standard Cells";
const team = ["Manshuk Garg", "Aditya Kumar", "Gourangi Tyagi", "Kashish Goyal"];
const BLANK = "____________";

function titlePage() {
  const T = (text, size, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER,
    spacing: { before: o.before || 0, after: o.after || 0, line: o.line || 276, lineRule: LineRuleType.AUTO },
    children: [new TextRun({ text, font: "Times New Roman", size, bold: o.bold, italics: o.italics, allCaps: o.caps })] });
  return [
    T(title.toUpperCase(), 32, { bold: true, before: 1200, after: 360, line: 360 }),
    T("A 4-bit ALU in 180 nm CMOS with PDP-optimized and ALU-specific standard cells", 24, { italics: true, after: 1300 }),
    T("Project Report", 28, { bold: true, after: 120 }),
    T("submitted in partial fulfilment of the requirements for the degree of", 24, { after: 60 }),
    T("Master of Technology in VLSI Design", 26, { bold: true, after: 1100 }),
    T("Submitted by", 24, { italics: true, after: 160 }),
    ...team.map((n, i) => T(`${n}   (Roll No. ${BLANK})`, 24, { after: i === team.length - 1 ? 900 : 120 })),
    T("Under the supervision of", 24, { italics: true, after: 160 }),
    T(`${BLANK}${BLANK}`, 24, { after: 60 }),
    T("(Name and designation of the supervisor)", 20, { italics: true, after: 1500 }),
    T("Department of Electronics and Communication Engineering", 26, { bold: true, after: 80 }),
    T("Thapar Institute of Engineering and Technology", 26, { bold: true, after: 80 }),
    T("Patiala 147004, Punjab, India", 24, { after: 240 }),
    T("November 2026", 24, { bold: true }),
  ];
}

const frontPages = [
  { id: "cert", title: "CERTIFICATE", toc: true, blocks: [
    { k: "p", t: `This is to certify that the project report entitled “${title}” submitted by ${team[0]} (Roll No. ${BLANK}), ${team[1]} (Roll No. ${BLANK}), ${team[2]} (Roll No. ${BLANK}) and ${team[3]} (Roll No. ${BLANK}) to the Department of Electronics and Communication Engineering, Thapar Institute of Engineering and Technology, Patiala, is a record of the project work carried out by them under my supervision.` },
    { k: "p", t: "\n\n\n", align: AlignmentType.LEFT },
    { k: "p", t: `Signature: ${BLANK}\nName: ${BLANK}${BLANK}\nDesignation: ${BLANK}\nDepartment of Electronics and Communication Engineering\nThapar Institute of Engineering and Technology, Patiala\nDate: ${BLANK}`, align: AlignmentType.LEFT },
  ] },
  { id: "decl", title: "DECLARATION", toc: true, blocks: [
    { k: "p", t: `We hereby declare that the project report entitled “${title}” is a record of the project carried out by us in the Department of Electronics and Communication Engineering, Thapar Institute of Engineering and Technology, Patiala. The simulations and implementations reported here were run by us. This report has not been submitted elsewhere for any other degree or diploma.` },
    { k: "p", t: "\n\n", align: AlignmentType.LEFT },
    ...team.map((n) => ({ k: "p", t: `${n}   Roll No. ${BLANK}   Signature: ${BLANK}`, align: AlignmentType.LEFT, spacing: { after: 360 } })),
    { k: "p", t: `Place: Patiala\nDate: ${BLANK}`, align: AlignmentType.LEFT },
  ] },
  { id: "ack", title: "ACKNOWLEDGEMENT", toc: true, blocks: [
    { k: "p", t: `We express our sincere gratitude to our supervisor, ${BLANK}${BLANK}, Department of Electronics and Communication Engineering, for guidance and encouragement throughout this project. We thank the Department for its facilities, and NIELIT for access to the ChipCraft virtual laboratory, in which the design flows of this project were run. We also acknowledge the developers of the open-source tools used in this work: Ngspice, Xschem, Magic, Netgen, Yosys, Qflow, OpenSTA and KLayout.` },
    { k: "p", t: "\n" + team.join("\n"), align: AlignmentType.RIGHT },
  ] },
  { id: "abs", title: "ABSTRACT", toc: true, blocks: [
    { k: "p", t: "The arithmetic logic unit (ALU) is a central block of every processor datapath, and in a cell-based design its area, delay and energy are set by the standard cells from which it is built. This project designs a 4-bit ALU in 180 nm CMOS (TSMC 0.18 µm, 1.8 V) from a full-custom standard-cell library optimized for minimum power-delay product (PDP) and evaluates it after layout against ALUs built from the OSU 0.18 µm standard-cell library." },
    { k: "p", t: "Twenty-one candidate circuits for nine logic functions were simulated with Ngspice at 40 combinations of transistor width and PMOS-to-NMOS ratio under a fan-out-of-four load, 840 simulations in all. Transmission-gate (TG) circuits at their minimum-PDP size reduce the PDP of the XOR2, MUX2 and full-adder cells by 53 %, 65 % and 60 % compared with static CMOS cells of reference size. Two ALU-specific cells are proposed: a function block FB4 (20 transistors), a TG 4:1 multiplexer whose select inputs are the operand bits and whose data inputs are four operation-code lines, and a carry-sum cell CS (24 transistors) that forms the carry without a generate signal and selects either the sum or the logic result. One ALU bit therefore needs 44 transistors and the complete ALU 272." },
    { k: "p", t: "The cell layouts were produced by a layout generator, verified by design-rule check and layout-versus-schematic comparison, characterized into a Liberty library (pl018) and used in an open-source Yosys and Qflow flow. Seven ALUs were synthesized, placed, routed, extracted and simulated with one transistor-level test bench of 229 transitions. The proposed ALU occupies 2189 µm² and needs 1453 fJ per operation and 0.69 nW of leakage power: 37 % less area, 56 % less energy and 68 % less leakage than the best ALU built from the OSU 0.18 µm cells. Its worst-case delay of 2.62 ns is 44 % longer than that of the fastest synthesized design." },
    { k: "p", t: "**Keywords:** arithmetic logic unit, standard-cell library, transmission gate, power-delay product, full-custom layout, Qflow, Ngspice." },
  ] },
];

const abbreviations = {
  header: ["Abbreviation", "Meaning"], widths: [2000, 6300], size: 22, align: [AlignmentType.LEFT, AlignmentType.LEFT],
  rows: [["ALU", "Arithmetic logic unit"], ["CMOS", "Complementary metal-oxide-semiconductor"], ["CPL", "Complementary pass-transistor logic"],
    ["CS", "Carry-sum cell (proposed)"], ["DRC", "Design-rule check"], ["EDP", "Energy-delay product"], ["FA", "Full adder"],
    ["FB4", "Function block with four code inputs (proposed)"], ["FO4", "Fan-out of four (load of four X1 inverters)"], ["GDI", "Gate diffusion input"],
    ["LEF", "Library exchange format (abstract cell view for placement and routing)"], ["LVS", "Layout versus schematic"],
    ["MUX2, MUX2I", "2:1 multiplexer, inverting 2:1 multiplexer"], ["NLDM", "Non-linear delay model"], ["PDP", "Power-delay product"],
    ["PTL", "Pass-transistor logic"], ["RTL", "Register-transfer level"], ["STA", "Static timing analysis"], ["TG", "Transmission gate"],
    ["V_{DD}", "Supply voltage"]],
};

// ------------------------------------------------------------------ references (IEEE style)
const refs = {
  weste2011: "N. H. E. Weste and D. M. Harris, *CMOS VLSI Design: A Circuits and Systems Perspective*, 4th ed. Boston, MA, USA: Addison-Wesley, 2011.",
  rabaey2003: "J. M. Rabaey, A. Chandrakasan, and B. Nikolić, *Digital Integrated Circuits: A Design Perspective*, 2nd ed. Upper Saddle River, NJ, USA: Prentice Hall, 2003.",
  zimmermann1997: "R. Zimmermann and W. Fichtner, “Low-power logic styles: CMOS versus pass-transistor logic,” *IEEE J. Solid-State Circuits*, vol. 32, no. 7, pp. 1079–1090, Jul. 1997, doi: 10.1109/4.597298.",
  zhuang1992: "N. Zhuang and H. Wu, “A new design of the CMOS full adder,” *IEEE J. Solid-State Circuits*, vol. 27, no. 5, pp. 840–844, May 1992, doi: 10.1109/4.133177.",
  shams2002: "A. M. Shams, T. K. Darwish, and M. A. Bayoumi, “Performance analysis of low-power 1-bit CMOS full adder cells,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 10, no. 1, pp. 20–29, Feb. 2002, doi: 10.1109/92.988727.",
  goel2006: "S. Goel, A. Kumar, and M. A. Bayoumi, “Design of robust, energy-efficient full adders for deep-submicrometer design using hybrid-CMOS logic style,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 14, no. 12, pp. 1309–1321, Dec. 2006, doi: 10.1109/TVLSI.2006.887807.",
  chang2005: "C.-H. Chang, J. Gu, and M. Zhang, “A review of 0.18-µm full adder performances for tree structured arithmetic circuits,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 13, no. 6, pp. 686–695, Jun. 2005, doi: 10.1109/TVLSI.2005.848806.",
  meadconway1980: "C. Mead and L. Conway, *Introduction to VLSI Systems*. Reading, MA, USA: Addison-Wesley, 1980.",
  xilinx: "Xilinx, “7 Series FPGAs configurable logic block user guide,” UG474.",
  hussain2022: "S. Hussain, M. Hasan, G. Agrawal, and M. Hasan, “A high-performance full swing 1-bit hybrid full adder cell,” *IET Circuits, Devices & Systems*, vol. 16, no. 3, pp. 210–217, 2022, doi: 10.1049/cds2.12097.",
  sadeghi2022: "A. Sadeghi, N. Shiri, and M. Rafiee, “High-performance 1-bit full adder with excellent driving capability for multistage structures,” *IEEE Embedded Systems Letters*, vol. 14, no. 1, pp. 47–50, Mar. 2022, doi: 10.1109/LES.2021.3108474.",
  arul2023: "A. Arul and M. Kathirvelu, “Design a novel 1-bit full adder with hybrid logic for full-swing, area-efficiency and high-speed,” *Analog Integrated Circuits and Signal Processing*, vol. 119, no. 1, pp. 111–130, Apr. 2024, doi: 10.1007/s10470-023-02217-0.",
  yin2023: "N. Yin, W. Pan, Y. Yu, C. Tang, and Z. Yu, “Low-power pass-transistor logic-based full adder and 8-bit multiplier,” *Electronics*, vol. 12, no. 15, Art. no. 3209, Jul. 2023, doi: 10.3390/electronics12153209.",
  gdi10t2023: "T. Nirmalraj, S. Pandiyan, R. Karan, R. Sivaraman, and R. Amirtharajan, “Design of low-power 10-transistor full adder using GDI technique for energy-efficient arithmetic applications,” *Circuits, Systems, and Signal Processing*, vol. 42, no. 6, pp. 3649–3667, Jun. 2023, doi: 10.1007/s00034-022-02287-x.",
  sharma2024: "U. Sharma and M. Jhamb, “Exploring supply voltage and temperature variation on XOR-XNOR cells with conventional/non-conventional techniques,” *Facta Universitatis, Series: Electronics and Energetics*, vol. 37, no. 2, pp. 301–316, 2024, doi: 10.2298/FUEE2402301S.",
  subbulakshmi2023: "N. Subbulakshmi, R. Sravanthi, M. S. Stalin, T. Swapna, T. Rajesh, and Y. Greeshma, “ALUSGDI: Low power arithmetic logic unit based sliced processor using GDI and MGDI,” *Measurement: Sensors*, vol. 28, Art. no. 100842, Aug. 2023, doi: 10.1016/j.measen.2023.100842.",
  jyothi2024: "B. Jyothi, B. V. R. Reddy, and M. Jhamb, “Design of arithmetic logic unit using energy charge recovery adiabatic logic technique,” in *Proc. 1st Int. Conf. Electronics, Communication and Signal Processing (ICECSP)*, 2024, pp. 1–6, doi: 10.1109/ICECSP61809.2024.10698278.",
  eai2024: "K. V. Kannan Nithin, V. R. Balaji, V. Mani, V. Priya, S. S. Sivaraju, and A. N. Duraivel, “ASIC design and implementation of 32 bit arithmetic and logic unit,” *EAI Endorsed Transactions on Energy Web*, vol. 11, Aug. 2024, doi: 10.4108/ew.6035.",
  karapothula2026: "R. G. Karapothula, J. Motheesh, T. Deekshith, M. Madhushankara, and R. Mathew, “Delay and power analysis of ALU with 180, 90, and 45 nm technologies,” in *Proc. 4th Int. Conf. Signal and Data Processing (ICSDP 2024)*, Lecture Notes in Electrical Engineering, vol. 1470. Singapore: Springer, 2026, pp. 13–21, doi: 10.1007/978-981-95-1058-0_2.",
  chen2022: "Y. Chen, Y. Nie, and H. Jiao, “An ultralow-power 65-nm standard cell library for near/subthreshold digital circuits,” *IEEE Trans. Very Large Scale Integr. (VLSI) Syst.*, vol. 30, no. 5, pp. 676–680, May 2022, doi: 10.1109/TVLSI.2022.3151500.",
  lim2023: "Y. W. Lim, N. A. Kamsani, R. M. Sidek, S. J. Hashim, and F. Z. Rokhani, “Energy-performance optimization via P/N ratio sizing with full diffusion layout structure and standard cell height tuning in near-threshold voltage operation,” *IEEE Access*, vol. 11, pp. 12536–12546, 2023, doi: 10.1109/ACCESS.2022.3230897.",
  sizing2024: "P. Cao and J. Guo, “Standard cell sizing for worst-case performance optimization considering process variation in subthreshold region,” *Electronics*, vol. 13, no. 22, Art. no. 4477, Nov. 2024, doi: 10.3390/electronics13224477.",
  ren2021: "H. Ren and M. Fojtik, “NVCell: Standard cell layout in advanced technology nodes with reinforcement learning,” in *Proc. 58th ACM/IEEE Design Automation Conf. (DAC)*, 2021, pp. 1291–1294, doi: 10.1109/DAC18074.2021.9586188.",
  lee2021: "D. Lee et al., “SP&R: SMT-based simultaneous place-and-route for standard cell synthesis of advanced nodes,” *IEEE Trans. Comput.-Aided Design Integr. Circuits Syst.*, vol. 40, no. 10, pp. 2142–2155, Oct. 2021, doi: 10.1109/TCAD.2020.3037885.",
  nishizawa2023: "S. Nishizawa and T. Nakura, “Libretto: An open cell timing characterizer for open source VLSI design,” *IEICE Trans. Fundamentals of Electronics, Communications and Computer Sciences*, vol. E106.A, no. 3, pp. 551–559, Mar. 2023, doi: 10.1587/transfun.2022VLP0007.",
  edwards2021: "R. T. Edwards, M. Shalan, and M. Kassem, “Real silicon using open-source EDA,” *IEEE Design & Test*, vol. 38, no. 2, pp. 38–44, Apr. 2021, doi: 10.1109/MDAT.2021.3050000.",
  mosis: "MOSIS, “MOSIS scalable CMOS (SCMOS) design rules,” rev. 8.",
  ngspice: "“Ngspice: Open source mixed-signal circuit simulator.” [Online]. Available: https://ngspice.sourceforge.io/",
  ousterhout1984: "J. K. Ousterhout, G. T. Hamachi, R. N. Mayo, W. S. Scott, and G. S. Taylor, “Magic: A VLSI layout system,” in *Proc. 21st Design Automation Conf.*, 1984, pp. 152–159, doi: 10.1109/DAC.1984.1585789.",
  yosys: "C. Wolf, “Yosys Open SYnthesis Suite.” [Online]. Available: https://yosyshq.net/yosys/",
  qflow: "R. T. Edwards, “Qflow: An open-source digital synthesis flow,” Open Circuit Design. [Online]. Available: http://opencircuitdesign.com/qflow/",
};

// ------------------------------------------------------------------ helpers for the body
const ch = (n, title) => ({ k: "chapter", n, title });
const h2 = (n, title) => ({ k: "h2", n, title });
const p = (t, o = {}) => Object.assign({ k: "p", t }, o);
const eq = (t, label) => ({ k: "eq", t, label });
const L = (items, numbered) => ({ k: "list", items, numbered });
const F = (label, file, caption, width) => ({ k: "fig", label, file, caption, width });
const H = (label, ref, sheet, caption, height) => ({ k: "hand", label, ref, sheet, caption, height });
const T = (label, caption, header, rows, widths, o = {}) => Object.assign({ k: "table", label, caption, header, rows, widths }, o);
const AL = (n) => Array(n).fill(1);
const FIGS = "docs/report/figures";

function subckt(file, name) {
  const fs = require("fs"), path = require("path");
  const lines = fs.readFileSync(path.resolve(__dirname, "..", "..", file), "utf8").split("\n");
  const i = lines.findIndex((l) => l.toLowerCase().startsWith(".subckt " + name.toLowerCase() + " "));
  const j = lines.findIndex((l, k) => k > i && l.toLowerCase().startsWith(".ends"));
  if (i < 0 || j < 0) throw new Error("subckt " + name + " in " + file);
  return lines.slice(i, j + 1);
}

// ------------------------------------------------------------------ body
const body = [
  // ============================================================== 1
  ch("1", "Introduction"),
  h2("1.1", "Background"),
  p("The arithmetic logic unit (ALU) performs the arithmetic and logic operations of a processor and lies on the critical path of its datapath. In a cell-based design flow, synthesis and place-and-route tools build the ALU from a fixed library of standard cells, so the circuit style, the transistor sizes and the layout of these cells bound the area, delay and energy of the ALU {c:weste2011,rabaey2003}."),
  p("Transmission-gate (TG) and pass-transistor circuits implement multiplexers, XOR gates and full adders with fewer transistors and less switched capacitance than static CMOS {c:zimmermann1997,zhuang1992,shams2002,goel2006}, and recent work continues to improve hybrid full adders and XOR–XNOR cells {c:hussain2022,sadeghi2022,arul2023,yin2023}. Most of these studies, however, compare single cells under the authors’ own load conditions; whether the gains survive in a complete datapath after placement, routing and extraction is examined far less often. A second way to reduce an ALU is to merge the logic of one bit into fewer cells: the OM-2 data path of Mead and Conway {c:meadconway1980} computes any Boolean function of two operand bits with one multiplexer driven by shared control lines. This project implements both ideas as restoring CMOS standard cells and measures their effect on a complete ALU."),
  h2("1.2", "Problem Statement and Objectives"),
  p("The problem is to design a 4-bit ALU in 180 nm CMOS whose standard cells are optimized at transistor level for minimum power-delay product (PDP), to add cells specific to the ALU where they reduce the transistor count of a bit, to implement the ALU with an automated open-source physical design flow, and to compare it after layout with ALUs built from an existing standard-cell library. The objectives are:", { keepNext: true }),
  L(["To select, for each basic function (INV, NAND2, NOR2, AND2, OR2, XOR2, MUX2, MUX2I and full adder), the circuit and transistor size with the minimum PDP under a fan-out-of-four load.",
    "To design two ALU-specific cells, a function block (FB4) and a carry-sum cell (CS), and to compare them with the same functions built from library cells.",
    "To lay out the cells, verify them by design-rule check (DRC) and layout-versus-schematic (LVS) comparison, and characterize them into a Liberty library (pl018).",
    "To implement 4-bit ALUs with Yosys and Qflow from the new library and from the OSU 0.18 µm library, and to compare the area, delay, energy and leakage of the extracted layouts."], true),
  h2("1.3", "Specifications"),
  T("spec", "Specifications of the ALU and of the design environment", ["Parameter", "Value"], [
    ["Data width", "4 bits: operands a, b; result y"],
    ["Operations", "8, selected by s_{2}s_{1}s_{0}: ADD, SUB, INC, DEC, AND, OR, XOR, NOT"],
    ["Status flags", "C (carry), V (overflow), Z (zero), N (negative)"],
    ["Technology", "TSMC 0.18 µm CMOS, BSIM3v3.1 models (MOSIS run T14B)"],
    ["Supply voltage, temperature", "1.8 V, 27 °C"],
    ["Design rules", "MOSIS SCMOS SCN6M_SUBM, λ = 0.1 µm, drawn L = 0.2 µm"],
    ["Cell library", "pl018: 12 cells and a filler, row height 8.0 µm"],
    ["Reference library", "OSU018 (Qflow kit), row height 10.0 µm"],
    ["Tools", "Ngspice 46, Xschem, Magic 8.3, Netgen, Icarus Verilog, Yosys, Qflow (GrayWolf, Qrouter), OpenSTA, KLayout"]],
    [2600, 5700], { align: [0, 0].map(() => AlignmentType.LEFT) }),

  // ============================================================== 2
  ch("2", "Literature Survey"),
  h2("2.1", "Scope of the Survey"),
  p("The survey covers papers published between 2021 and 2026 in four areas that bear directly on this project: logic styles for arithmetic cells, transistor-level ALU implementations, transistor sizing and standard-cell library design, and automated cell layout, characterization and open-source physical design. The papers were identified by keyword searches of publisher databases and scholarly indexes and selected for relevance; seventeen are discussed below and summarized in {t:lit}."),
  h2("2.2", "Logic Styles for Arithmetic Cells"),
  p("Hybrid circuits that combine transmission gates, pass transistors and static CMOS continue to give the lowest power-delay products for full adders and XOR–XNOR cells. Hussain et al. {c:hussain2022} proposed an 18-transistor full-swing hybrid full adder in which an XOR–XNOR stage is followed by pass transistors and inverters; in HSPICE simulations at the 16 nm node it improved the delay, average power and PDP of the conventional CMOS mirror adder by 34.8 %, 48.8 % and 66.6 % at 0.8 V. Arul and Kathirvelu {c:arul2023} built a 20-transistor hybrid full adder around a 12-transistor XOR–XNOR circuit made of 2:1 multiplexers, pass transistors and inverters; in a 45 nm process it occupied 14.16 µm² and dissipated 3.58 µW with a delay of 72.7 ps, and it was cascaded into ripple-carry adders of up to 64 bits. Yin et al. {c:yin2023} proposed an 18-transistor pass-transistor full adder whose post-layout power was 13.8 % lower than that of a conventional CMOS full adder, and used it in an 8-bit signed multiplier that needed 8 % less power than a multiplier produced by a commercial synthesis tool."),
  p("Output swing and driving capability are the second recurring theme. Sadeghi et al. {c:sadeghi2022} designed a TG-based full adder with a separate module that generates a full-swing carry, so that both outputs keep a strong drive when the cell is cascaded in ripple-carry adders, compressors and multipliers. Nirmalraj et al. {c:gdi10t2023} reduced a full adder to 10 transistors by combining a 4-transistor pass-transistor XOR gate with two gate-diffusion-input (GDI) multiplexers, evaluated it in ten technologies between 1.2 µm and 50 nm, including 0.18 µm, and extended it to a 4-bit adder/subtractor. Sharma and Jhamb {c:sharma2024} compared XOR–XNOR cells in conventional and non-conventional technologies; carbon-nanotube transistors gave the lowest delay at small nodes and floating-gate MOS circuits the best power efficiency."),
  p("These studies agree that the XOR–XNOR stage dominates the power and delay of a full adder and that full-swing outputs with adequate drive are a requirement. They differ in technology node, supply voltage and load, so their percentages cannot be compared directly, a point made earlier by Zimmermann and Fichtner, who showed that the ranking of logic styles depends on the circuit environment {c:zimmermann1997}. Yin et al. are among the few who carry the cell into a larger block and report post-layout results. This project therefore measures all candidate circuits with the same drivers and load and then carries the selected cells through layout and automatic place-and-route."),
  h2("2.3", "ALU Implementations"),
  p("Recent ALU designs pursue low power mainly through the logic style of the whole unit. Subbulakshmi et al. {c:subbulakshmi2023} built an ALU-based sliced processor for a filter bank in 65 nm CMOS from GDI and modified GDI cells, together with a recursive parallel self-timed adder; GDI logic used 91.4 % less power and 65 % less area than CMOS. Jyothi et al. {c:jyothi2024} designed an ALU in energy-recovery (ECRL) adiabatic logic and reported a total power of 3.69 nW at 1.8 V. Such styles save energy, but GDI gates lose output swing unless they are modified and buffered, and adiabatic logic needs a multiphase power clock, so neither fits directly into a conventional static standard-cell flow."),
  p("Designs in conventional CMOS organize the ALU as an arithmetic unit and a logic unit whose results are selected by multiplexers. The 32-bit ALU of Kannan Nithin et al. {c:eai2024}, designed in a 180 nm process with Cadence tools, builds the arithmetic unit from 4:1 and 2:1 multiplexers and full adders, and the logic unit from a 4:1 multiplexer and logic gates. Karapothula et al. {c:karapothula2026} compared the delay and power of a transistor-level ALU in 180 nm, 90 nm and 45 nm technologies, reporting 13.29 ps and 0.257 µW for the 45 nm version. In this organization the operands drive both units, so every operation switches both, and the final selection adds a multiplexer to every bit. As far as their abstracts state, none of the surveyed works compares the same ALU built from different standard-cell libraries after place-and-route."),
  h2("2.4", "Transistor Sizing and Standard-Cell Libraries"),
  p("Recent library work treats the transistor width and the PMOS-to-NMOS width ratio of each cell as the main design parameters. Chen et al. {c:chen2022} designed a standard-cell library for near- and sub-threshold operation in 65 nm CMOS, sizing the transistors by threshold-voltage tuning to improve switching and area efficiency. Lim et al. {c:lim2023} jointly optimized the P/N ratio and the cell height for near-threshold operation: in a 110 nm test chip a 7-track library saved 55 % of the energy of a bus controller, and an 8051 microcontroller built from it operated down to 0.6 V. Cao and Guo {c:sizing2024} derived the optimal P/N width ratio analytically for minimum worst-case delay under process variation in the sub-threshold region, improving the worst-case delay and the energy-delay product of the cells by at least 8.6 % and 7.4 %. Like these works, this project sizes each cell individually; at the nominal 1.8 V of the 180 nm process the optimum is set mainly by the load and the input slope, so the cells are swept in width and P/N ratio under fixed drivers and a fan-out-of-four load (Chapter 4)."),
  h2("2.5", "Cell Layout, Characterization and Open-Source Flows"),
  p("Ren and Fojtik {c:ren2021} introduced NVCell, a layout generator that uses reinforcement learning to fix design-rule violations during routing; it produced layouts of equal or smaller area for more than 90 % of the single-row cells of an industrial library. Lee et al. {c:lee2021} formulated the placement and routing of a cell as one satisfiability-modulo-theories (SMT) problem with dynamic pin allocation and generated a complete 7 nm library, reducing the metal-2 track usage by about 53 %. Nishizawa and Nakura {c:nishizawa2023} presented Libretto, an open-source characterizer that generates the timing and power models of a user’s standard cells, and Edwards, Shalan and Kassem {c:edwards2021} showed that a complete open-source flow, OpenLane built on OpenROAD, can produce industrial-quality designs. The 180 nm rules of this project allow a simpler deterministic generator with a maze router (Chapter 6); the requirement it shares with these generators, that every pin be reachable by the block-level router, decided the routability of the new library."),
  h2("2.6", "Summary of the Surveyed Papers"),
  T("lit", "Summary of the surveyed literature (2021–2026)", ["Ref.", "Year", "Circuit or topic", "Technology / tool", "Main reported result"], [
    ["{c:hussain2022}", "2022", "18T full-swing hybrid full adder", "16 nm, HSPICE", "PDP −66.6 % vs CMOS mirror adder at 0.8 V"],
    ["{c:sadeghi2022}", "2022", "TG full adder with full-swing carry module", "–", "strong Sum and Carry drive in multistage adders"],
    ["{c:arul2023}", "2024", "20T hybrid full adder, 12T XOR–XNOR", "45 nm, Cadence", "3.58 µW, 72.7 ps; adders up to 64 bits"],
    ["{c:yin2023}", "2023", "18T PTL full adder, 8-bit multiplier", "post-layout", "full adder −13.8 %, multiplier −8 % power"],
    ["{c:gdi10t2023}", "2023", "10T GDI/PTL full adder, 4-bit adder/subtractor", "ten nodes incl. 0.18 µm", "−13 % power vs a low-power adder"],
    ["{c:sharma2024}", "2024", "XOR–XNOR cells, comparative study", "CMOS, FinFET, CNTFET, FGMOS", "CNTFET fastest, FGMOS most power-efficient"],
    ["{c:subbulakshmi2023}", "2023", "GDI / modified GDI ALU for a filter bank", "65 nm", "−91.4 % power, −65 % area vs CMOS"],
    ["{c:jyothi2024}", "2024", "Adiabatic (ECRL) ALU", "1.8 V", "ALU power 3.69 nW"],
    ["{c:eai2024}", "2024", "32-bit ALU, multiplexer-based units", "180 nm, Cadence", "delay and power of a 32-bit ALU"],
    ["{c:karapothula2026}", "2026", "Transistor-level ALU in three nodes", "180, 90, 45 nm", "45 nm: 13.29 ps, 0.257 µW"],
    ["{c:chen2022}", "2022", "Ultralow-voltage standard-cell library", "65 nm LP", "sizing by threshold-voltage tuning"],
    ["{c:lim2023}", "2023", "P/N ratio and cell-height tuning", "110 nm test chip", "7-track library: −55 % energy"],
    ["{c:sizing2024}", "2024", "Optimal P/N ratio under variation", "sub-threshold", "≥ 8.6 % lower worst-case delay"],
    ["{c:ren2021}", "2021", "NVCell: cell layout by reinforcement learning", "advanced node", "equal or smaller area for > 90 % of cells"],
    ["{c:lee2021}", "2021", "SP&R: SMT-based cell place-and-route", "7 nm", "−53 % metal-2 tracks vs sequential P&R"],
    ["{c:nishizawa2023}", "2023", "Libretto: open cell characterizer", "open source", "timing and power models of custom cells"],
    ["{c:edwards2021}", "2021", "Open-source RTL-to-GDS flow", "OpenLane / OpenROAD", "complete RISC-V based SoC"]],
    [720, 620, 2520, 1900, 2540], { size: 18, keep: true, align: [AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT] }),
  h2("2.7", "Research Gaps and Contribution"),
  p("The survey points to three gaps that this project addresses:", { keepNext: true }),
  L(["Cell-level comparisons dominate: most low-power arithmetic cells are evaluated alone, in different technologies and under different loads, and few are measured in a complete datapath after placement, routing and extraction.",
    "ALUs are organized as separate arithmetic and logic units; a function block that computes the logic result and the propagate signal of a bit in one cell was not found among the surveyed designs.",
    "Open-source flows are used with the libraries supplied with a process kit; a custom, PDP-optimized library laid out, verified and characterized for an open flow and compared with an existing library on the same designs is uncommon."], true),
  p("Accordingly, the contributions of this project are (i) a minimum-PDP sizing of 21 candidate circuits under identical conditions and a 12-cell library, pl018, with generated layouts, DRC and LVS verification and Liberty characterization; (ii) two ALU-specific cells, FB4 and CS, which form an ALU bit with 44 transistors; and (iii) a comparison of seven placed-and-routed 4-bit ALUs by one transistor-level test bench applied to the netlists extracted from their layouts."),

  // ============================================================== 3
  ch("3", "Background and Design Methodology"),
  h2("3.1", "CMOS Logic Styles"),
  p("A static CMOS gate connects its output either to V_{DD} through a pull-up network of PMOS transistors or to ground through a complementary pull-down network of NMOS transistors, so the output always reaches the full supply levels and restores the signal for the next stage {c:weste2011}; the inverter of {f:invtg}(a) is the simplest case. A transmission gate, {f:invtg}(b), places an NMOS and a PMOS transistor in parallel with complementary gate signals: the PMOS passes the high level and the NMOS the low level, so the output follows the input over the full swing when S = 1 and is isolated when S = 0 {c:rabaey2003}."),
  F("invtg", `${FIGS}/fig_inv_tg.png`, "(a) CMOS inverter and (b) CMOS transmission gate", 4.8),
  p("Multiplexers and XOR gates map naturally onto transmission gates: a 2:1 multiplexer needs two TGs and one inverter, six transistors against twelve in static CMOS. A TG does not restore the signal, however, so restoring inverters are placed after one or two TG levels, and pass-transistor styles do not always win once such buffering and realistic loads are included {c:zimmermann1997}. Hybrid full adders compute A ⊕ B with an XOR–XNOR stage and select the sum and carry with TGs controlled by it {c:zhuang1992,shams2002,goel2006}."),
  h2("3.2", "Performance Metrics and ALU Basics"),
  p("The propagation delay is measured between the 50 % points of the input and output transitions. Because power can be traded for delay, circuits are compared by the power-delay product, the energy of a switching event, and by the energy-delay product,", { keepNext: true }),
  eq("PDP = P_{avg} · t_{max},      EDP = E_{op} · t_{max}", "pdp"),
  p("where t_{max} is the worst-case delay over all input transitions, P_{avg} the average supply power and E_{op} the energy per ALU operation. In a ripple-carry adder with the propagate signal P_{i} = A_{i} ⊕ B_{i}, each bit computes", { keepNext: true }),
  eq("C_{i+1} = A_{i} · B_{i} + P_{i} · C_{i},      S_{i} = P_{i} ⊕ C_{i}", "carry"),
  p("Subtraction uses the two’s complement, A − B = A + ¬B + 1; increment and decrement add 1 or 1111 (−1). The flags are the carry C = C_{4}, the overflow V = C_{3} ⊕ C_{4}, the zero flag Z and the negative flag N = y_{3}."),
  h2("3.3", "Technology, Tools and Design Flow"),
  p("All circuits use the TSMC 0.18 µm CMOS process with the MOSIS BSIM3v3.1 parameters of run T14B at 1.8 V and 27 °C; the layouts follow the MOSIS SCMOS rules SCN6M_SUBM {c:mosis}, the rules of the Qflow OSU018 kit. The reference inverter X1 has an NMOS of 1.0/0.2 µm and a PMOS of 2.0/0.2 µm. Only open-source tools are used: Ngspice {c:ngspice} for simulation, Xschem for schematics, Magic {c:ousterhout1984} and Netgen for layout, DRC, extraction and LVS, Icarus Verilog for RTL simulation, Yosys {c:yosys} for synthesis, Qflow {c:qflow} with GrayWolf and Qrouter for placement and routing, and KLayout for viewing. All flows were run in the NIELIT ChipCraft virtual laboratory."),
  p("The work proceeds at two levels ({f:flow}). At cell level, candidate circuits are simulated over a grid of transistor sizes, the best circuit and size of each function is selected, and the selected cells and the two ALU-specific cells are laid out, verified and characterized into the library pl018. At ALU level, several descriptions of the ALU are synthesized onto pl018 and onto the OSU018 library, placed and routed with Qflow, verified, extracted and simulated with one test bench."),
  F("flow", `${FIGS}/flow.png`, "Design flow: cell-level design (top) and ALU-level implementation and evaluation (bottom)", 5.0),
  h2("3.4", "Test Benches and Sizing Sweep"),
  p("**Cell bench.** Every cell input is driven through two X1 inverters and every output drives four X1 inverters (FO4). The input sequence applies every change of a single input in every state of the other inputs. The worst delay t_{max} is measured from the input of the last driver inverter, the power P_{tot} includes the drivers, so a cell with a large input capacitance is charged for the energy its driver spends, and a size is accepted only if every transition gives the correct level with full swing."),
  p("**Sizing sweep.** Each candidate is simulated at 40 sizes: eight width factors k = 0.3–2, which scale all widths relative to the reference size, combined with five PMOS-to-NMOS ratios r = 1–3. The reference size k = 1, r = 2 corresponds to conventional X1 sizing. The 21 candidates give 840 simulations; for each function the candidate and size with the lowest PDP is selected."),
  p("**ALU bench.** All ALUs are measured under the same driver and load conditions with 229 transitions, one every 5 ns: the 18 full-length carry ripples of ADD, SUB, INC and DEC, and for each of the eight operations one change of operation and 24 random operand changes. The delay of a transition ends at the last 50 % crossing of any output, so glitches are included; E_{op} is the charge drawn from the ALU supply times V_{DD}, averaged over the transitions, and the leakage P_{leak} the mean over 16 static states. The bench is applied to the transistor-level netlists and to the netlists extracted from the routed layouts."),

  // ============================================================== 4
  ch("4", "Standard-Cell Optimization"),
  h2("4.1", "Candidate Circuits"),
  p("Twenty-one candidate circuits were evaluated for nine functions ({t:cand}). Besides a static CMOS circuit for every function, they include gate-level circuits, TG circuits with and without output buffering, among them two TG full adders {c:zhuang1992,shams2002}, and two pass-transistor circuits."),
  T("cand", "Candidate circuits at their minimum-PDP size", ["Function", "Candidate", "Circuit style", "T", "k / r", "t_{max} (ps)", "P_{tot} (µW)", "PDP (fJ)"], [
    { bold: true, cells: ["INV", "inv_cmos", "static CMOS", "2", "0.8 / 2.5", "149.0", "64.77", "9.65"] },
    { bold: true, cells: ["NAND2", "nand2_cmos", "static CMOS", "4", "0.6 / 3", "184.9", "57.43", "10.62"] },
    { bold: true, cells: ["NOR2", "nor2_cmos", "static CMOS", "4", "0.6 / 2.5", "222.6", "60.03", "13.36"] },
    { bold: true, cells: ["AND2", "and2_cmos", "NAND2 + inverter", "6", "0.6 / 2.5", "247.6", "60.66", "15.02"] },
    { bold: true, cells: ["OR2", "or2_cmos", "NOR2 + inverter", "6", "0.8 / 1.5", "283.8", "62.68", "17.79"] },
    ["XOR2", "xor_cmos12", "static CMOS, input inverters", "12", "0.3 / 2.5", "390.1", "73.73", "28.76"],
    ["XOR2", "xor_nand16", "gate level, four NAND2", "16", "0.3 / 3", "427.6", "81.43", "34.82"],
    { bold: true, cells: ["XOR2", "xor_tg8", "TG, unbuffered", "8", "0.6 / 3", "260.3", "77.27", "20.11"] },
    ["XOR2", "xor_tgb10", "TG + output inverter", "10", "0.8 / 1.5", "322.0", "68.15", "21.94"],
    ["XOR2", "xor_cpl14", "CPL + restoring inverters", "14", "1 / 1", "475.8", "91.62", "43.59"],
    ["MUX2", "mux_cmos12", "static CMOS, AOI22 + inverter", "12", "0.3 / 2.5", "465.2", "75.53", "35.14"],
    ["MUX2", "mux_gate20", "gate level, AND2/OR2", "20", "0.3 / 2.5", "498.1", "83.90", "41.79"],
    { bold: true, cells: ["MUX2", "mux_tg6", "TG, unbuffered", "6", "0.4 / 3", "250.0", "65.12", "16.28"] },
    ["MUX2", "mux_tgb10", "TG + two inverters", "10", "0.6 / 2", "333.5", "68.91", "22.98"],
    ["MUX2I", "muxi_cmos10", "static CMOS AOI22", "10", "0.4 / 2.5", "334.9", "78.74", "26.37"],
    { bold: true, cells: ["MUX2I", "muxi_tg8", "TG + output inverter", "8", "0.6 / 2.5", "282.1", "68.69", "19.38"] },
    ["MUX2I", "muxi_npt7", "NMOS pass + level restorer", "7", "1.5 / 1", "361.1", "80.41", "29.04"],
    ["FA", "fa_cmos28", "mirror adder (static CMOS)", "28", "0.3 / 2", "703.3", "123.89", "87.13"],
    ["FA", "fa_nand44", "gate level, eleven NAND2", "44", "0.3 / 2", "803.0", "149.00", "119.65"],
    ["FA", "fa_tga20", "TG adder, unbuffered", "20", "0.4 / 3", "625.4", "119.30", "74.61"],
    { bold: true, cells: ["FA", "fa_tgab24", "TG adder, buffered outputs", "24", "0.3 / 2.5", "589.6", "108.46", "63.95"] }],
    [950, 1250, 2150, 420, 900, 880, 880, 850],
    { size: 18, align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT, ...AL(5).map(() => AlignmentType.CENTER)],
      note: "T: transistors. 1.8 V, 27 °C, FO4 load, drivers included; best accepted size of each candidate. Bold: selected for the optimized cell set." }),
  h2("4.2", "Transmission-Gate XOR2 and MUX2"),
  p("The TG XOR2 ({f:xormux}a) forms ¬A and ¬B with two inverters; the TG controlled by B passes A when B = 0 and the other TG passes ¬A when B = 1, so Y = A ⊕ B with 8 transistors instead of 12. The TG MUX2 ({f:xormux}b) passes A when S = 0 and B when S = 1, with one inverter for ¬S: six transistors instead of twelve. At their minimum-PDP sizes the worst delays are 260.3 ps and 250.0 ps and the PDPs 20.11 fJ and 16.28 fJ."),
  F("xormux", `${FIGS}/fig_xor_mux.png`, "(a) Transmission-gate XOR2, 8 transistors, and (b) transmission-gate 2:1 multiplexer, 6 transistors, at their minimum-PDP sizes (W/L in µm)", 5.6),
  h2("4.3", "Results of the Sizing Sweep"),
  p("{t:sel} compares the selected circuit of each function with the static CMOS circuit at the reference size (k = 1, r = 2)."),
  T("sel", "Selected cells against static CMOS cells of reference size", ["Function", "Selected circuit", "T", "k / r", "t_{max} (ps)", "PDP (fJ)", "Reference t_{max} (ps)", "Reference PDP (fJ)", "ΔPDP"], [
    ["INV", "inv_cmos", "2", "0.8 / 2.5", "149.0", "9.65", "152.0", "9.99", "−3 %"],
    ["NAND2", "nand2_cmos", "4", "0.6 / 3", "184.9", "10.62", "196.1", "12.28", "−14 %"],
    ["NOR2", "nor2_cmos", "4", "0.6 / 2.5", "222.6", "13.36", "205.7", "13.77", "−3 %"],
    ["XOR2", "xor_tg8", "8", "0.6 / 3", "260.3", "20.11", "365.5", "42.69", "−53 %"],
    ["MUX2", "mux_tg6", "6", "0.4 / 3", "250.0", "16.28", "401.8", "46.60", "−65 %"],
    ["MUX2I", "muxi_tg8", "8", "0.6 / 2.5", "282.1", "19.38", "337.4", "36.49", "−47 %"],
    ["FA", "fa_tgab24", "24", "0.3 / 2.5", "589.6", "63.95", "651.0", "159.44", "−60 %"]],
    [950, 1150, 420, 950, 850, 800, 1050, 1050, 900], { size: 19, note: "Reference: static CMOS circuit of the same function (xor_cmos12, mux_cmos12, muxi_cmos10, fa_cmos28) at k = 1, r = 2." }),
  p("For the inverter and NOR2 the optimum lies close to the reference size and the PDP falls by only 3 %; NAND2 gains 14 %. For the functions with a TG alternative the gain is much larger and has two parts: sizing the static CMOS circuit alone reduces its PDP by 25 %–45 % (42.69 to 28.76 fJ for XOR2), and the TG topology removes a further 27 %–54 % (28.76 to 20.11 fJ). The TG circuits also switch less capacitance, so their delay falls by 9 %–38 %. In the library of the automated flow, XOR2 and MUX2 are used in their buffered versions (xor_tgb10, mux_tgb10), whose delay does not depend on the driving cell."),

  // ============================================================== 5
  ch("5", "Proposed Cells and ALU Architecture"),
  h2("5.1", "Function Block FB4"),
  p("In a conventional ALU bit, the logic functions and the propagate signal of the adder are computed by separate gates and then selected by a multiplexer. The function block FB4 replaces all of them by one cell:", { keepNext: true }),
  eq("P = C[2A + B]", "fb4"),
  p("The operand bits A and B select one of the four code lines C_{0}–C_{3}, which are driven by the operation decoder and shared by all bits. Because the four code bits form the truth table of P, FB4 can produce any of the 16 Boolean functions of two variables; {t:fb4codes} lists the six that the ALU uses."),
  T("fb4codes", "Functions of FB4 used by the ALU", ["Function P", "P for AB = 00, 01, 10, 11", "Code C_{3}C_{2}C_{1}C_{0}", "Used for"], [
    ["A ⊕ B", "0  1  1  0", "0110", "ADD, XOR"], ["A XNOR B = A ⊕ ¬B", "1  0  0  1", "1001", "SUB"], ["A", "0  0  1  1", "1100", "INC"],
    ["¬A", "1  1  0  0", "0011", "DEC, NOT"], ["A · B", "0  0  0  1", "1000", "AND"], ["A + B", "0  1  1  1", "1110", "OR"]],
    [2400, 2400, 1900, 1600]),
  p("The circuit ({f:fb4}) is a 4:1 multiplexer of two TG levels: the first level, controlled by B, selects between C_{0} and C_{1} (node u0) and between C_{2} and C_{3} (node u1); the second, controlled by A, selects u0 or u1. Two input inverters form ¬A and ¬B, and two output inverters restore the level. The cell has 20 transistors; at its minimum-PDP size (k = 0.4, r = 2.5) the worst delay is 450.2 ps and the PDP 18.95 fJ."),
  F("fb4", `${FIGS}/fig_fb4.png`, "Transistor schematic of the function block FB4, 20 transistors (W/L as in the layout; netlist in Appendix B)", 5.4),
  h2("5.2", "Carry-Sum Cell CS"),
  p("The carry-sum cell forms the carry out and the result of one bit:", { keepNext: true }),
  eq("C_{O} = P ? C_{I} : A,      Y = K ? P : P ⊕ C_{I}", "cs"),
  p("For the arithmetic operations P = A ⊕ B_{x} is the propagate signal, where B_{x} is B, ¬B or a constant. P = 0 means A = B_{x}: both inputs are 1 and a carry is generated, or both are 0 and it is killed; in both cases the carry out equals A, so no generate signal is needed and the carry logic reduces to one TG multiplexer controlled by P. For the logic operations K = 1 selects P as the result ({t:csmodes})."),
  T("csmodes", "Modes of the carry-sum cell", ["K", "P", "C_{O}", "Y", "Meaning"], [
    ["0", "0", "A", "C_{I}", "generate (A = 1) or kill (A = 0); sum = C_{I}"], ["0", "1", "C_{I}", "¬C_{I}", "propagate; sum = ¬C_{I}"],
    ["1", "0", "A", "0", "logic result 0"], ["1", "1", "C_{I}", "1", "logic result 1"]],
    [700, 700, 1000, 1000, 4900], { align: [1, 1, 1, 1, 0].map((x) => (x ? AlignmentType.CENTER : AlignmentType.LEFT)) }),
  p("In the circuit ({f:cs}) two TGs controlled by P form the carry multiplexer; two TGs with an inverter for C_{I} form ¬(P ⊕ C_{I}); two TGs controlled by K select between this signal and ¬P; and output inverters restore C_{O} and Y. The cell has 24 transistors, and the carry passes through one TG and two inverters per bit. At its minimum-PDP size (k = 0.8, r = 1.5) the worst delay is 458.6 ps and the PDP 33.64 fJ."),
  F("cs", `${FIGS}/fig_cs.png`, "Transistor schematic of the carry-sum cell CS, 24 transistors (W/L as in the layout; netlist in Appendix B)", 5.4),
  h2("5.3", "Comparison with Composed Cells"),
  p("{t:cellcmp} compares the two cells with the same functions built from other cells, measured with the same bench. Against static CMOS the PDP falls by 73 % (FB4) and 64 % (CS) and the transistor count by 44 % and 33 %. Against the optimized library cells, FB4 lowers the PDP by 12 % with 17 % fewer transistors at a 4 % longer delay, and CS lowers the PDP by 18 %, the delay by 10 % and the transistor count by 20 %."),
  T("cellcmp", "FB4 and CS against composed implementations", ["Implementation", "T", "k / r", "t_{max} (ps)", "P_{tot} (µW)", "PDP (fJ)", "W_{total} (µm)"], [
    { group: "Function of FB4: P = C[2A + B]" },
    ["3 × MUX2, static CMOS", "36", "–", "688.7", "102.77", "70.78", "85.5"],
    ["3 × MUX2I of pl018", "24", "–", "433.6", "49.77", "21.58", "17.1"],
    ["FB4, reference size", "20", "1 / 2", "437.9", "50.19", "21.98", "16.5"],
    { bold: true, cells: ["FB4, minimum PDP (selected)", "20", "0.4 / 2.5", "450.2", "42.08", "18.95", "9.5"] },
    { group: "Function of CS: carry and result" },
    ["MUX2 + XOR2 + MUX2, static CMOS", "36", "–", "614.6", "152.67", "93.84", "84.0"],
    ["MUX2 + XOR2 + MUX2 of pl018", "30", "–", "510.0", "80.54", "41.08", "17.6"],
    ["CS, reference size", "24", "1 / 2", "439.5", "85.13", "37.41", "21.0"],
    { bold: true, cells: ["CS, minimum PDP (selected)", "24", "0.8 / 1.5", "458.6", "73.36", "33.64", "14.0"] }],
    [2900, 500, 1000, 950, 1000, 900, 1000], { size: 19 }),
  h2("5.4", "ALU Organization and Operation Codes"),
  p("One bit of the ALU is one FB4 and one CS, 44 transistors: the FB4 output P drives the P input of the CS, and the carry passes from C_{O} of one bit to C_{I} of the next. The ALU ({f:aluorg}) has four such bit slices, an operation decoder and the flag logic. The decoder converts s_{2}s_{1}s_{0} into the code lines C_{0}–C_{3}, the carry into bit 0, c_{0}, and the control K = s_{2}."),
  F("aluorg", "docs/paper/figures/fig_alu_org.png", "Block diagram of the proposed 4-bit ALU: four FB4/CS bit slices with a ripple carry, the operation decoder and the flag logic", 4.8),
  p("{t:opcodes} shows the mapping. SUB uses P = A XNOR B with c_{0} = 1, so each bit computes A + ¬B + 1 without an extra inverter or XOR gate on the second operand; INC uses P = A with c_{0} = 1 and DEC P = ¬A with c_{0} = 0, which adds 1111 (−1). For the logic operations K = 1 and the result is the FB4 output itself."),
  T("opcodes", "Operation codes and their mapping onto the bit slice", ["Operation", "s_{2}s_{1}s_{0}", "P (FB4)", "C_{3}C_{2}C_{1}C_{0}", "c_{0}", "K", "Result y"], [
    ["ADD", "000", "A ⊕ B", "0110", "0", "0", "a + b"], ["SUB", "001", "A XNOR B", "1001", "1", "0", "a − b"],
    ["INC", "010", "A", "1100", "1", "0", "a + 1"], ["DEC", "011", "¬A", "0011", "0", "0", "a − 1"],
    ["AND", "100", "A · B", "1000", "–", "1", "a · b"], ["OR", "101", "A + B", "1110", "–", "1", "a + b (bitwise OR)"],
    ["XOR", "110", "A ⊕ B", "0110", "–", "1", "a ⊕ b"], ["NOT", "111", "¬A", "0011", "–", "1", "¬a"]],
    [1100, 1000, 1300, 1300, 600, 600, 2300], { note: "–: the carry chain is not used for the logic operations." }),
  h2("5.5", "Operation Decoder and Status Flags"),
  p("The decoder is built from ten pl018 cells (XOR2, BUF, two INV, NAND2, AND2, NOR2 and three MUX2I). With x ? y : z denoting a 2:1 multiplexer, its outputs are", { keepNext: true }),
  eq("c_{0} = s_{1} ⊕ s_{0},      K = s_{2},      C_{0} = s_{0} · (¬s_{2} + s_{1})", "dec0"),
  eq("C_{1} = s_{2} ? (s_{1} + s_{0}) : ¬(s_{1} ⊕ s_{0}),      C_{2} = s_{2} ? (s_{1} ⊕ s_{0}) : ¬s_{0}", "dec1"),
  eq("C_{3} = s_{2} ? ¬s_{1} : (s_{1} ⊕ s_{0})", "dec2"),
  p("and evaluating them for all eight codes reproduces the code column of {t:opcodes}. Ten further cells form the flags", { keepNext: true }),
  eq("C = c_{4} · ¬s_{2},      V = (c_{3} ⊕ c_{4}) · ¬s_{2}", "flags1"),
  eq("Z = ¬(y_{0} + y_{1}) · ¬(y_{2} + y_{3}),      N = y_{3}", "flags2"),
  p("so C and V are 0 for the logic operations, and for SUB and DEC C = 1 means that no borrow occurred. {t:count} lists the cells of the complete ALU."),
  T("count", "Cells and transistors of the proposed ALU", ["Block", "Cells", "Number of cells", "Transistors"], [
    ["Bit slices", "4 × FB4, 4 × CS", "8", "176"],
    ["Operation decoder", "XOR2, BUF, 2 × INV, NAND2, AND2, NOR2, 3 × MUX2I", "10", "56"],
    ["Flag logic", "XOR2, 4 × NOR2, AND2, 4 × INV", "10", "40"],
    { bold: true, cells: ["Total", "", "28", "272"] }],
    [1900, 4100, 1200, 1100], { align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER] }),

  // ============================================================== 6
  ch("6", "Physical Implementation and Results"),
  h2("6.1", "Cell Layout and the pl018 Library"),
  p("The cell layouts are produced by a generator from the transistor netlist and a column order of the devices along shared diffusion. It places the devices on an 8.0 µm row with 0.8 µm sites and shared power rails, folds wide transistors, and routes every net on polysilicon, metal1 and metal2 with a maze router. Every pin pad lies on a crossing of the routing tracks of the block router, so that the router can reach it in any orientation. {f:layoutfb4} shows the layout of FB4."),
  F("layoutfb4", "docs/figures/presentation/layout_pl_fb4.png", "Generated layout of the cell pl_fb4, 14.4 µm × 8.0 µm", 4.6),
  p("The library contains twelve cells and a filler ({t:lib}); all pass the Magic DRC and match their netlists in Netgen LVS. Each cell is extracted and simulated with Ngspice at five loads (2–100 fF) and five input slopes (30–1200 ps), which fill the 5 × 5 delay tables of a Liberty file read by Yosys and OpenSTA; the LEF view for the router takes the metal of each pin net as pin geometry."),
  T("lib", "Cells of the pl018 library", ["Cell", "Sites", "Area (µm²)", "T", "C_{in,max} (fF)", "Delay rise / fall (ps)", "Leakage (nW)"], [
    ["pl_inv", "3", "19.2", "2", "9.5", "84 / 80", "0.007"], ["pl_buf", "4", "25.6", "4", "12.0", "131 / 136", "0.028"],
    ["pl_nand2", "3", "19.2", "4", "10.4", "107 / 90", "0.010"], ["pl_nor2", "3", "19.2", "4", "12.0", "117 / 130", "0.009"],
    ["pl_and2", "4", "25.6", "6", "9.6", "153 / 180", "0.015"], ["pl_or2", "4", "25.6", "6", "10.9", "178 / 177", "0.015"],
    ["pl_xor2", "7", "44.8", "10", "13.9", "269 / 264", "0.016"], ["pl_mux2", "9", "57.6", "10", "15.0", "279 / 323", "0.012"],
    ["pl_mux2i", "6", "38.4", "8", "18.0", "225 / 210", "0.009"], ["pl_fa", "17", "108.8", "24", "14.0", "545 / 633", "0.029"],
    { bold: true, cells: ["pl_fb4", "18", "115.2", "20", "21.7", "378 / 456", "0.014"] }, { bold: true, cells: ["pl_cs", "17", "108.8", "24", "26.0", "395 / 400", "0.030"] }],
    [1300, 800, 1200, 600, 1350, 1700, 1300], { size: 19, note: "Site width 0.8 µm, row height 8.0 µm. Delay: worst timing arc at 16 fF load and 80 ps input slope, from the Liberty tables." }),
  h2("6.2", "Automated Implementation from Verilog"),
  p("Three Verilog descriptions of the ALU were implemented with both libraries. The behavioural description (beh) states each operation with Verilog operators in one case statement and leaves the structure to Yosys; the bit-sliced description (slice) describes one bit with operand conditioning, full adder, logic unit and output multiplexers; and the hand-mapped netlist (map) instantiates the library’s full adders and inverting multiplexers, which synthesis cannot use because the full adder has two outputs. Design D3 uses the OSU018 cells and D4 the pl018 cells. The proposed ALU P is a structural Verilog netlist of the 28 pl018 cells of Chapter 5."),
  p("Every description is first simulated with Icarus Verilog against a self-checking test bench that applies all 2048 combinations of the eleven inputs and computes the expected outputs independently. Yosys then maps it onto the library, and the gate-level netlist is simulated again with the same bench. Qflow buffers high-fanout nets, places the cells with GrayWolf and routes them with Qrouter; Netgen compares the routed layout with the netlist, and Magic checks the design rules with the real cell layouts and extracts a flat netlist with all transistors and parasitic capacitances, which is simulated with the ALU bench of Section 3.4. Routing the generated cells required pin pads on the track crossings and keep-out areas next to the signal-pin metal; with them all seven ALUs route completely, match in LVS, have no DRC errors and give correct results on all 229 transitions after extraction. {f:chip} shows the routed proposed ALU."),
  F("chip", "docs/paper/figures/fig_chip.png", "Routed proposed ALU, 57.6 µm × 38.0 µm with 55 placed cells, viewed in KLayout", 4.2),
  h2("6.3", "Transistor-Level Comparison"),
  p("{t:tl} compares the ALU built from five cell sets before layout. The ALU from minimum-PDP cells (D2) needs 69 % less energy than the ALU from static CMOS cells of reference size (D1). The proposed ALU P needs 272 transistors, 2076.2 ps and 870.6 fJ per operation: compared with D1, 53 % fewer transistors, 30 % less delay, 75 % less energy and an 83 % lower energy-delay product; compared with D2, 32 % fewer transistors, 9 % less delay and 21 % less energy."),
  T("tl", "4-bit ALUs at transistor level, before layout", ["Cell set", "Cells", "T", "t_{max} (ps)", "E_{op} (fJ)", "P_{leak} (nW)", "EDP (fJ·ns)"], [
    ["Gate-level cells (k = 0.4, r = 2)", "60", "842", "2925.4", "2039.6", "1.41", "5966.6"],
    ["D1: static CMOS, reference size", "60", "578", "2979.3", "3509.8", "2.02", "10456.7"],
    ["D2: minimum-PDP cells", "69", "402", "2270.8", "1102.1", "0.81", "2502.6"],
    ["pl018 cells, MUX2I slice", "66", "458", "2310.4", "1312.8", "0.93", "3033.1"],
    { bold: true, cells: ["P: FB4 + CS (proposed)", "28", "272", "2076.2", "870.6", "0.47", "1807.5"] }],
    [2900, 700, 700, 1000, 1000, 1000, 1000], { size: 19 }),
  h2("6.4", "Comparison after Layout"),
  p("{t:al} and {f:alfig} summarize the seven routed ALUs, simulated from their extracted netlists. With the same description, replacing the OSU018 cells by the pl018 cells reduces the energy per operation by 36 %–45 %, the leakage by 36 %–52 % and the die area by 8 %–23 %, while the delay changes by −7 % to +5 %. The proposed ALU has the smallest die (2189 µm²), the fewest transistors and the lowest energy (1453.0 fJ), leakage (0.69 nW) and energy-delay product of all seven: against the best OSU018 design for each quantity, 37 % less area, 56 % less energy, 68 % less leakage and a 47 % lower energy-delay product."),
  T("al", "Routed 4-bit ALUs, extracted netlists", ["Design", "Area (µm²)", "T", "C (fF)", "t_{max} (ps)", "t_{mean} (ps)", "E_{op} (fJ)", "P_{leak} (nW)", "EDP (fJ·ns)"], [
    ["D3 beh", "5466", "793", "875", "1812.0", "1353.2", "4898.7", "3.10", "8876.4"], ["D3 slice", "3864", "525", "563", "2144.4", "1204.7", "3333.0", "2.21", "7147.1"],
    ["D3 map", "3496", "534", "455", "3476.1", "1564.8", "3807.1", "2.18", "13233.7"], ["D4 beh", "4536", "716", "655", "1874.0", "1274.6", "2798.5", "1.98", "5244.4"],
    ["D4 slice", "2979", "454", "429", "2257.1", "1259.4", "2140.4", "1.22", "4831.1"], ["D4 map", "3202", "484", "528", "3220.6", "1498.5", "2077.3", "1.04", "6690.1"],
    { bold: true, cells: ["P", "2189", "316", "324", "2615.4", "1340.1", "1453.0", "0.69", "3800.1"] }],
    [950, 900, 600, 750, 950, 950, 950, 950, 1000], { size: 19, note: "D3: OSU018 cells; D4: pl018 cells; P: proposed FB4/CS ALU with pl018 cells. T and C: transistors and parasitic capacitance of the extracted netlist." }),
  F("alfig", "docs/paper/figures/fig_after_layout.png", "Energy per operation and worst-case delay of the seven routed ALUs (light grey: OSU018 cells; dark grey: pl018 cells; black: proposed)", 4.8),
  h2("6.5", "Energy per Operation and Delay"),
  p("{t:ops} breaks the energy down by operation. The proposed ALU needs 967–1188 fJ for the logic operations, against 1460–4934 fJ in the other designs, because the FB4 forms the logic result directly, and its arithmetic operations are also the lowest of all designs."),
  T("ops", "Energy per operation of the routed ALUs (fJ)", ["Design", "ADD", "SUB", "INC", "DEC", "AND", "OR", "XOR", "NOT"], [
    ["D3 beh", "5397", "5520", "3947", "5445", "4934", "4413", "4778", "4755"], ["D3 slice", "4304", "3780", "2616", "3535", "3495", "3067", "3006", "2860"],
    ["D3 map", "4865", "4741", "2820", "4529", "3913", "3638", "2792", "3160"], ["D4 beh", "3209", "3228", "2304", "2906", "2764", "2439", "2725", "2813"],
    ["D4 slice", "2519", "2962", "1621", "2282", "2129", "2044", "1734", "1833"], ["D4 map", "3119", "2762", "1705", "2293", "2026", "1629", "1460", "1626"],
    { bold: true, cells: ["P", "1807", "1857", "1610", "1953", "1104", "967", "1138", "1188"] }],
    [1100, 900, 900, 900, 900, 900, 900, 900, 900], { size: 19 }),
  p("The proposed ALU is not the fastest. Its slowest transition, a change from ADD to SUB, propagates from the select inputs through the decoder and the buffered code lines into every FB4 and then along the carry chain to the overflow flag: 2615.4 ps. The behavioural design restructured by Yosys with the OSU018 cells (D3 beh) reaches 1812.0 ps, but needs 793 transistors and 3.4 times the energy. Layout increases the delay of P by 22.6 % and its energy by 16.6 %, against 4 %–9 % and 3 %–8 % for the D3 designs: the pl018 cells have smaller capacitances, so the wiring is a larger share of each load, and a single drive strength leaves long nets to buffers inserted by the flow."),
  h2("6.6", "Limitations"),
  p("The results hold for the typical process corner at 1.8 V and 27 °C; corner and Monte Carlo analysis, wire-resistance extraction and cells with more than one drive strength are not included. The ripple carry is adequate for four bits, but wider ALUs will need carry lookahead or carry skip. The OSU 0.18 µm library serves as the reference because it is the library of the Qflow kit for the same process; a commercial library may perform differently."),

  // ============================================================== 7
  ch("7", "Conclusion and Future Scope"),
  h2("7.1", "Conclusion"),
  p("A 4-bit ALU was designed in 180 nm CMOS from a full-custom library of minimum-PDP standard cells and two ALU-specific cells, and was compared after layout with ALUs built from the OSU 0.18 µm library. The main results are:", { keepNext: true }),
  L(["Transmission-gate circuits at their minimum-PDP size reduce the PDP of XOR2, MUX2, MUX2I and the full adder by 47 %–65 % against static CMOS cells of reference size.",
    "The function block FB4 and the carry-sum cell CS form an ALU bit with 44 transistors and lower the PDP of their functions by 12 % and 18 % against the same functions built from library cells.",
    "The pl018 library alone, used for the same Verilog descriptions, reduces the energy per operation by 36 %–45 % and the leakage by 36 %–52 % against the OSU018 library.",
    "After layout, the proposed ALU needs 37 % less area, 56 % less energy and 68 % less leakage than the best ALU from the OSU 0.18 µm library, at a worst-case delay of 2.62 ns, 44 % above that of the fastest synthesized design."]),
  h2("7.2", "Future Scope"),
  L(["Shorten the carry path by alternating the carry polarity between bits and by strengthening the carry driver.",
    "Add X2 and X4 drive strengths and wire-aware sizing to reduce the delay added by layout.",
    "Extend the analysis to process corners and Monte Carlo variation, and extract wire resistance.",
    "Scale the design to 8 and 16 bits with carry lookahead or carry skip, and fabricate a test chip."]),

  { k: "refs" },

  // ============================================================== A
  { k: "appendix", n: "A", title: "Simulation Waveforms" },
  p("All waveforms are Ngspice 46 transient simulations with the TSMC 0.18 µm BSIM3v3.1 models at 1.8 V and 27 °C. Every input is driven through two X1 inverters and every output drives four X1 inverters. Inputs are drawn in grey and outputs in blue; each logic trace spans 0 to 1.8 V."),
  F("wavefb4", `${FIGS}/wave_fb4.png`, "FB4 with the code lines C_{3}–C_{0} set to the codes of six operations in turn; in each 8 ns window A and B step through 00, 01, 10 and 11, and P follows the code bit C[2A + B]", 5.2),
  F("wavecs", `${FIGS}/wave_cs.png`, "CS in its four modes; in each 8 ns window A and C_{I} step through 00, 01, 10 and 11", 5.2),
  F("wavefunc", `${FIGS}/wave_alu_function.png`, "Function test of the proposed ALU at transistor level: 32 vectors, four operand pairs for each operation. Lines: simulated operands, result and flags (8C + 4V + 2Z + N); circles: expected values of the reference model, which agree for all 32 vectors", 5.0),
  F("wavedelay", `${FIGS}/wave_alu_delay.png`, "Slowest transition of the proposed ALU at transistor level, before layout: ADD to SUB with a = b = 0, measured from the input of the last s_{0} driver inverter to the last 50 % crossing of an output (Z): 2076.2 ps", 5.2),

  // ============================================================== B
  { k: "appendix", n: "B", title: "Netlists" },
  p("The netlists are written for Ngspice. nfet and pfet are the NMOS and PMOS transistors of the TSMC 0.18 µm BSIM3v3.1 model set; all channel lengths are 0.2 µm, and ad, as, pd and ps are the drain and source areas and perimeters of the layout."),
  { k: "code", title: "Function block FB4 (pl_fb4)", lines: subckt("tech/pl018/pl018_cells.sp", "pl_fb4") },
  { k: "code", title: "Carry-sum cell CS (pl_cs)", lines: subckt("tech/pl018/pl018_cells.sp", "pl_cs") },
  { k: "code", title: "Proposed 4-bit ALU (alu4_fb)", lines: ["* 4-bit ALU: FB4 and CS cell per bit, pl018 cells for decoder and flags",
    "* operation select s_2 s_1 s_0: 000 ADD  001 SUB  010 INC  011 DEC",
    "*                               100 AND  101 OR   110 XOR  111 NOT (of a)",
    "* 28 cell instances, 272 transistors",
    ...subckt("ltspice_package/alu4_fb.lib", "alu4_fb")] },
];

module.exports = { title, titlePage, frontPages, abbreviations, refs, body };
