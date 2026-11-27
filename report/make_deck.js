/* Final report deck (12 slides, projector-friendly, evidence-led):
 * "Customer Follow-up in Online Retail".
 * Every evidence slide = EDA/result picture + "what the data says"
 * + "how this keeps customers". Figures come from make_figures.py,
 * numbers from ../outputs/*.  Berry & cream theme, Bookman + Calibri. */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "outputs");
const ASSETS = path.join(__dirname, "assets");
const S = JSON.parse(fs.readFileSync(path.join(OUT, "eda_summary.json"), "utf8"));
const latest = fs.readFileSync(path.join(OUT, "latest_scores.csv"), "utf8")
  .trim().split(/\r?\n/).slice(1).map((l) => l.split(","));
const latestHigh = latest.filter((r) => r[2] === "High");
const latestHighSpend = latestHigh.reduce((a, r) => a + Number(r[6]), 0);
const latestDate = new Date(latest[0][latest[0].length - 1])
  .toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

/* ---------- theme ---------- */
const THEME = {
  name: "Berry Ledger",
  headFontFace: "Bookman Old Style",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "33202C", lt1: "FFFFFF", dk2: "6D2E46", lt2: "F6EEF2",
    accent1: "C0507C", accent2: "C98A2D", accent3: "50808E",
    accent4: "8A8A93", accent5: "421A30", accent6: "D9A0B4",
    hlink: "C0507C", folHlink: "6D2E46",
  },
};
const INK = THEME.colors.dk1, BERRY = THEME.colors.dk2, BLUSH = THEME.colors.lt2;
const RASP = THEME.colors.accent1, AMBER = THEME.colors.accent2;
const GRAY = THEME.colors.accent4, WINE = THEME.colors.accent5;
const CREAM = "ECE2D0", MUTED = "716572", PINK = "D9A0B4";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Final-year data science project";
pres.title = "Customer Follow-up in Online Retail";

const W = 13.33, M = 0.65, CW = W - 2 * M;
const pct = (x, d = 0) => (100 * x).toFixed(d) + "%";
const gbpK = (x) => "GBP " + (Math.round(x / 100) / 10).toFixed(1) + "k";

/* ---------- layouts ---------- */
pres.defineSlideMaster({ title: "DARK", background: { color: WINE }, objects: [] });
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: {
        options: { name: "kicker", type: "body", x: M, y: 0.38, w: CW, h: 0.34,
          fontSize: 13, bold: true, charSpacing: 3, color: RASP, margin: 0 },
        text: "SECTION" } },
    { placeholder: {
        options: { name: "title", type: "title", x: M, y: 0.72, w: CW, h: 0.8,
          fontSize: 32, bold: true, color: BERRY, align: "left", margin: 0 },
        text: "Title" } },
    { text: {
        text: "Customer Follow-up in Online Retail  ·  UCI Online Retail data (Dec 2010 - Dec 2011)",
        options: { x: M, y: 7.1, w: 9.5, h: 0.3, fontSize: 10, color: GRAY,
          margin: 0, isTextBox: true } } },
    { slideNumber: { x: 12.4, y: 7.1, w: 0.55, h: 0.3, fontSize: 10, color: GRAY } },
  ],
});

/* ---------- helpers ---------- */
function contentSlide(section, kicker, title) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  return s;
}
function card(s, x, y, w, h, fill) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill || BLUSH },
    rectRadius: 0.09, line: { type: "none" } });
}
function numDot(s, x, y, n, color, txt) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: 0.46, h: 0.46,
    fill: { color: color || RASP }, line: { type: "none" } });
  s.addText(String(n), { x, y: y - 0.014, w: 0.46, h: 0.49, align: "center",
    valign: "middle", fontSize: 17, bold: true, color: txt || "FFFFFF",
    fontFace: THEME.headFontFace, margin: 0, isTextBox: true });
}

/* The evidence-slide pattern: picture left, finding + action right. */
const IMG = { x: M, y: 1.75, w: 7.36, h: 4.6 };
const RX = IMG.x + IMG.w + 0.35, RW = W - M - RX;
function evidenceSlide({ section, kicker, title, img, caption, big, bigSize,
                         finding, action, statKicker }) {
  const s = contentSlide(section, kicker, title);
  s.addImage({ path: path.join(ASSETS, img), ...IMG });
  s.addText(caption, { x: IMG.x, y: IMG.y + IMG.h + 0.08, w: IMG.w, h: 0.38,
    fontSize: 13, italic: true, color: MUTED, margin: 0, isTextBox: true });
  // finding card
  const fy = 1.75, fh = 2.3;
  card(s, RX, fy, RW, fh);
  s.addText(statKicker || "WHAT THE DATA SAYS", { x: RX + 0.3, y: fy + 0.2,
    w: RW - 0.6, h: 0.3, fontSize: 12, bold: true, charSpacing: 2, color: RASP,
    margin: 0, isTextBox: true });
  s.addText(big, { x: RX + 0.3, y: fy + 0.48, w: RW - 0.6, h: 0.8,
    fontFace: THEME.headFontFace, fontSize: bigSize || 42, bold: true,
    color: RASP, margin: 0, isTextBox: true, valign: "middle" });
  s.addText(finding, { x: RX + 0.3, y: fy + 1.3, w: RW - 0.6, h: fh - 1.38,
    fontSize: 15, color: INK, margin: 0, isTextBox: true, valign: "top" });
  // action card
  const ay = fy + fh + 0.22, ah = 6.81 - ay;
  card(s, RX, ay, RW, ah, WINE);
  s.addText("HOW THIS KEEPS CUSTOMERS", { x: RX + 0.3, y: ay + 0.22,
    w: RW - 0.6, h: 0.3, fontSize: 12, bold: true, charSpacing: 2, color: AMBER,
    margin: 0, isTextBox: true });
  s.addText(action, { x: RX + 0.3, y: ay + 0.6, w: RW - 0.6, h: ah - 0.75,
    fontSize: 16, color: CREAM, margin: 0, isTextBox: true, valign: "top" });
  return s;
}

/* =====================================================================
 * 1. TITLE
 * =================================================================== */
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
  [RASP, AMBER, CREAM].forEach((c, i) =>
    s.addShape(pres.ShapeType.ellipse, { x: M + i * 0.36, y: 1.45, w: 0.21,
      h: 0.21, fill: { color: c }, line: { type: "none" } }));
  s.addText("Keeping the Customers\nYou Already Won", {
    x: M, y: 1.95, w: 12, h: 2.4, fontFace: THEME.headFontFace, fontSize: 52,
    bold: true, color: CREAM, margin: 0, isTextBox: true, lineSpacing: 60 });
  s.addText("What one year of sales data says about who stops buying - and what to do about it", {
    x: M, y: 4.5, w: 11.8, h: 0.9, fontSize: 21, color: PINK, margin: 0,
    isTextBox: true });
  s.addText("Customer follow-up in online retail  ·  final project report  ·  November 2026", {
    x: M, y: 6.55, w: 11, h: 0.45, fontSize: 14, color: "A98FA0", margin: 0,
    isTextBox: true });
}

/* =====================================================================
 * 2. THE PROBLEM AND THE APPROACH
 * =================================================================== */
{
  const s = contentSlide("Opening", "The problem", "Regular customers leave in silence");
  s.addText("Which regular customers may stop buying in the next 60 days?", {
    x: M, y: 1.85, w: 7.3, h: 1.0, fontSize: 23, bold: true, color: BERRY,
    margin: 0, isTextBox: true, valign: "top" });
  const steps = [
    ["Study", "Explore one year of sales to find who leaves and why."],
    ["Score", "Give every regular a risk score from their last 90 days."],
    ["Act", "Hand the team a short list of the riskiest 10% each week."],
  ];
  steps.forEach(([t, d], i) => {
    const y = 3.15 + i * 1.12;
    numDot(s, M, y, i + 1, i === 2 ? AMBER : RASP);
    s.addText([{ text: t + "   ", options: { bold: true, color: BERRY } },
      { text: d, options: { color: INK } }],
      { x: M + 0.7, y: y - 0.06, w: 6.6, h: 0.9, fontSize: 18, margin: 0,
        isTextBox: true, valign: "top" });
  });
  const bx = 8.35, bw = 4.33;
  card(s, bx, 1.85, bw, 4.95);
  s.addText("THE COST OF SILENCE", { x: bx + 0.35, y: 2.15, w: bw - 0.7, h: 0.3,
    fontSize: 12, bold: true, charSpacing: 2, color: RASP, margin: 0, isTextBox: true });
  s.addText("~12%", { x: bx + 0.35, y: 2.5, w: bw - 0.7, h: 1.0,
    fontFace: THEME.headFontFace, fontSize: 54, bold: true, color: RASP,
    margin: 0, isTextBox: true });
  s.addText("of regular, recent buyers make no purchase at all in the next 60 days.", {
    x: bx + 0.35, y: 3.6, w: bw - 0.7, h: 1.0, fontSize: 16, bold: true,
    color: INK, margin: 0, isTextBox: true, valign: "top" });
  s.addText("Nobody cancels in retail. The revenue is gone before anyone notices, and the team cannot call all 4,334 customers.", {
    x: bx + 0.35, y: 4.7, w: bw - 0.7, h: 1.9, fontSize: 15, color: MUTED,
    margin: 0, isTextBox: true, valign: "top" });
}

/* =====================================================================
 * 3-8. EXPLORATION: WHERE THE BUSINESS IS AT RISK
 * =================================================================== */
const EDA = "What the data shows";
pres.addSection({ title: EDA });

const ma = S.monthly_active;
const nov = ma.find((m) => m.month === "Nov 11").n, aug = ma.find((m) => m.month === "Aug 11").n;
evidenceSlide({
  section: EDA, kicker: "1 · Business rhythm",
  title: "One year of sales, peaking every autumn",
  img: "fig_seasonality.png",
  caption: "Customers with at least one order per month, Dec 2010 - Nov 2011. Clean data: 391,153 sales lines, 4,334 customers.",
  big: "+" + pct(nov / aug - 1),
  finding: `more active customers in November (${nov.toLocaleString("en-GB")}) than in August (${aug}). Sep-Nov is the season that pays the year.`,
  action: "Start retention work in late summer. A regular kept in September is still buying in the peak months, instead of being lost right before them.",
});

const rc = S.revenue_concentration;
evidenceSlide({
  section: EDA, kicker: "2 · Where the money is",
  title: "A tenth of customers bring " + pct(rc.top10pct_share) + " of revenue",
  img: "fig_revenue_concentration.png",
  caption: "Cumulative share of yearly revenue, customers sorted from biggest spender down.",
  big: pct(rc.top10pct_share),
  finding: `of yearly revenue comes from the top 10% of customers (${Math.round(rc.customers / 10)} accounts). The top 20% bring ${pct(rc.top20pct_share)}.`,
  action: "Treat big spenders as key accounts. When one of them appears on the risk list, call them first: losing one costs as much as losing dozens of small buyers.",
});

const nv = S.new_vs_returning;
evidenceSlide({
  section: EDA, kicker: "3 · Who pays the bills",
  title: "Returning customers pay " + pct(nv.returning_share_of_revenue) + " of the bills",
  img: "fig_new_vs_returning.png",
  caption: "Monthly revenue split by first-time and returning customers, Jan - Nov 2011.",
  big: pct(nv.returning_share_of_revenue),
  finding: `of revenue comes from customers on a repeat visit, yet ${pct(S.one_time_buyer_share)} of all customers buy only once.`,
  action: "Put retention money before acquisition money. Every regular who stays protects income that new customers cannot replace quickly.",
});

evidenceSlide({
  section: EDA, kicker: "4 · Retention",
  title: "Most new customers never come back",
  img: "fig_cohort.png",
  caption: "Share of each month's new customers who ordered again 1-6 months later.",
  big: "15-30%",
  finding: "of each month's new customers order again in any later month. The rest drift away after the first purchase.",
  action: "Follow up every first-time buyer within 30 days: a thank-you note and a clear reason to place the second order. The second order starts the habit.",
});

const f = S.risk_by_frequency;
evidenceSlide({
  section: EDA, kicker: "5 · Who leaves",
  title: "Shallow buying habits break first",
  img: "fig_risk_habit.png",
  caption: "Regular, recent buyers at four cutoff dates (1,087 customer snapshots).",
  big: pct(f["3"].rate),
  finding: `of regulars with only 3 order days in 90 days stop buying, against ${pct(f["9+"].rate)} of those with 9 or more.`,
  action: "Grow the habit. Reorder reminders and small loyalty rewards that move a 3-order customer to a 4th order cut their risk by more than half.",
});

const r = S.risk_by_recency;
evidenceSlide({
  section: EDA, kicker: "6 · Who leaves",
  title: "Three quiet weeks is a warning sign",
  img: "fig_risk_silence.png",
  caption: "Same 1,087 snapshots, grouped by days since the last order at the cutoff.",
  big: pct(r["22-30 d"].rate),
  finding: `stop buying after 22-30 quiet days, against ${pct(r["0-7 d"].rate)} for regulars who ordered this week.`,
  action: "Set an automatic trigger: when a regular passes three weeks without an order, send a personal check-in before the silence becomes a loss.",
});

/* =====================================================================
 * 9-11. THE MODEL AND THE PROOF
 * =================================================================== */
const MOD = "The model and the proof";
pres.addSection({ title: MOD });

evidenceSlide({
  section: MOD, kicker: "7 · How the score works",
  title: "What the risk score looks at",
  img: "fig_model_drivers.png",
  caption: "Logistic regression weights (standardized). Quiet days act through the lateness measure, which contains them.",
  big: "Habit depth", bigSize: 32,
  finding: "Few order days and low spend are the strongest warnings. An irregular or slow buying rhythm adds risk.",
  action: "Every name on the list comes with its reasons, so staff know what to say: a reorder nudge for a shallow habit, a check-in for a late customer.",
});

const v = S.validation, t = S.final_test;
evidenceSlide({
  section: MOD, kicker: "8 · Does it work?",
  title: "Proven on data the model never saw",
  img: "fig_bakeoff.png",
  caption: `Validation, 1 Aug 2011: share of each top-10% list (32 of 311) that really stopped buying.`,
  statKicker: "LOCKED TEST, 1 OCT 2011",
  big: t.lift.toFixed(1) + "x",
  finding: `better than random. ${t.hits} of ${t.k} flagged customers really stopped (${pct(t.precision)}), against ${pct(t.base_rate)} by chance.`,
  action: "Each hour of follow-up now reaches twice as many real at-risk customers as untargeted calls. The test was opened once, after the model was frozen.",
});

evidenceSlide({
  section: MOD, kicker: "9 · Choosing the list size",
  title: "Contact a third, reach half the leavers",
  img: "fig_gains.png",
  caption: "Locked test, 1 Oct 2011: share of real leavers found as more customers are contacted.",
  big: "52%",
  finding: "of real leavers are reached by contacting the riskiest 30% of regulars. The top 10% alone reaches 21%.",
  action: `Size the list to your team. On the latest data (${latestDate}) the top 10% is ${latestHigh.length} regulars holding ${gbpK(latestHighSpend)} of recent spend. Start there.`,
});

/* =====================================================================
 * 12. CLOSING: THE ROUTINE
 * =================================================================== */
pres.addSection({ title: "Using it" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Using it" });
  s.addText("Twice the right conversations,\nhalf the wasted effort.", {
    x: M, y: 0.75, w: 12, h: 1.9, fontFace: THEME.headFontFace, fontSize: 40,
    bold: true, color: CREAM, margin: 0, isTextBox: true, lineSpacing: 48 });
  const steps = [
    ["Score", "Run the pipeline weekly. Every regular gets a fresh risk score."],
    ["Shortlist", "Open the dashboard and take the top 10% with their reasons."],
    ["Reach out", "Check-in, reorder nudge or loyalty offer, matched to the reason."],
    ["Measure", "Track who buys again and keep what works."],
  ];
  const w = 2.92, gap = 0.17, y = 3.05;
  steps.forEach(([tt, d], i) => {
    const x = M + i * (w + gap);
    card(s, x, y, w, 2.5, "55253F");
    numDot(s, x + 0.28, y + 0.3, i + 1, i === 3 ? AMBER : RASP);
    s.addText(tt, { x: x + 0.88, y: y + 0.3, w: w - 1.05, h: 0.5, fontSize: 18,
      bold: true, color: CREAM, fontFace: THEME.headFontFace, margin: 0,
      isTextBox: true });
    s.addText(d, { x: x + 0.28, y: y + 1.0, w: w - 0.56, h: 1.4, fontSize: 15,
      color: PINK, margin: 0, isTextBox: true, valign: "top" });
  });
  s.addText("Dashboard for the shop owner:  streamlit run dashboard/app.py", {
    x: M, y: 5.95, w: CW, h: 0.45, fontSize: 17, bold: true, color: AMBER,
    margin: 0, isTextBox: true });
  s.addText("Code, pipeline and figures: online_retail_churn repository  ·  python run_all.py", {
    x: M, y: 6.6, w: 11, h: 0.4, fontSize: 13, color: "A98FA0", margin: 0,
    isTextBox: true });
}

/* ---------- write + theme ---------- */
const OUTFILE = path.join(__dirname,
  process.env.DECK_NAME || "Online_Retail_Final_Report_v2.pptx");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");
pres.writeFile({ fileName: OUTFILE })
  .then(() => applyTheme(OUTFILE, THEME))
  .then(() => console.log("Wrote " + OUTFILE))
  .catch((e) => { console.error(e); process.exit(1); });
